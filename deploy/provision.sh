#!/usr/bin/env bash
set -euo pipefail

APP_USER=active
APP_HOME=/srv/active
APP_DIR=$APP_HOME/app
ENV_DIR=/etc/active
ENV_FILE=$ENV_DIR/active.env
STATE_FILE=$ENV_DIR/provision.conf
GITHUB_ED25519_FINGERPRINT="SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU"

REPO=git@github.com:shashanksde3/active-django.git
BRANCH=main
DOMAINS=()
EMAIL=""

usage() {
  cat <<'EOF'
Provision a fresh Ubuntu 24.04 server (e.g. a DigitalOcean Droplet) for the Active site.

Usage (as root on the server):
  bash provision.sh [--domain example.com]... [--email you@example.com] [--repo URL] [--branch main]

  --domain   Domain pointing at this server (repeatable, e.g. example.com and www.example.com).
             With --email, HTTPS is set up with Let's Encrypt.
  --email    Email for Let's Encrypt expiry notices.
  --repo     Git URL to deploy (default: git@github.com:shashanksde3/active-django.git).
  --branch   Branch to deploy (default: main).

Safe to re-run. Domains and email are remembered in /etc/active/provision.conf.
The first run stops after printing a deploy key: add it to the GitHub repo
(Settings > Deploy keys, read-only), then run the script again.
EOF
}

log() { printf '\n\033[1;32m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m!!  %s\033[0m\n' "$*" >&2; }
die() { printf '\033[1;31mxx  %s\033[0m\n' "$*" >&2; exit 1; }
as_app() { sudo -u "$APP_USER" -H "$@"; }

parse_args() {
  local domains_given=false
  while [[ $# -gt 0 ]]; do
    case $1 in
      --domain) DOMAINS+=("${2:?--domain needs a value}"); domains_given=true; shift 2 ;;
      --email) EMAIL=${2:?--email needs a value}; shift 2 ;;
      --repo) REPO=${2:?--repo needs a value}; shift 2 ;;
      --branch) BRANCH=${2:?--branch needs a value}; shift 2 ;;
      -h | --help) usage; exit 0 ;;
      *) usage; die "Unknown option: $1" ;;
    esac
  done
  if [[ -f $STATE_FILE ]]; then
    # shellcheck source=/dev/null
    source "$STATE_FILE"
    if ! $domains_given && [[ -n ${SAVED_DOMAINS:-} ]]; then read -r -a DOMAINS <<<"$SAVED_DOMAINS"; fi
    EMAIL=${EMAIL:-${SAVED_EMAIL:-}}
  fi
}

check_system() {
  [[ $EUID -eq 0 ]] || die "Run as root (e.g. sudo bash provision.sh)."
  # shellcheck source=/dev/null
  source /etc/os-release
  [[ ${ID:-} == ubuntu && ${VERSION_ID:-} == 24.04 ]] || warn "Tested on Ubuntu 24.04; this is ${PRETTY_NAME:-unknown}."
}

public_ip() {
  curl -fsS --max-time 2 http://169.254.169.254/metadata/v1/interfaces/public/0/ipv4/address 2>/dev/null \
    || hostname -I | awk '{print $1}'
}

install_packages() {
  log "Installing system packages"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -q
  apt-get upgrade -yq
  apt-get install -yq python3-venv git nginx ufw fail2ban unattended-upgrades \
    certbot python3-certbot-nginx
}

add_swap() {
  swapon --show | grep -q . && return 0
  log "Adding 1 GB swap (small Droplets run out of memory during pip installs)"
  fallocate -l 1G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile >/dev/null
  swapon /swapfile
  grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >>/etc/fstab
}

secure_server() {
  log "Firewall, automatic security updates, fail2ban"
  ufw allow OpenSSH >/dev/null
  ufw allow 'Nginx Full' >/dev/null
  ufw --force enable >/dev/null
  printf 'APT::Periodic::Update-Package-Lists "1";\nAPT::Periodic::Unattended-Upgrade "1";\n' \
    >/etc/apt/apt.conf.d/20auto-upgrades
  systemctl enable --now fail2ban >/dev/null

  if [[ -s /root/.ssh/authorized_keys ]]; then
    # sshd keeps the first value it reads, so this must sort before cloud-init's 50-cloud-init.conf.
    cat >/etc/ssh/sshd_config.d/00-active-hardening.conf <<'EOF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin prohibit-password
EOF
    sshd -t
    systemctl try-reload-or-restart ssh.service
  else
    warn "root has no SSH key, so password login stays enabled to avoid locking you out."
  fi
}

create_app_user() {
  log "Creating the '$APP_USER' user and $APP_HOME"
  id "$APP_USER" &>/dev/null || adduser --system --group --home "$APP_HOME" --shell /bin/bash "$APP_USER"
  install -d -m 750 -o "$APP_USER" -g "$APP_USER" "$APP_HOME"
  install -d -m 700 -o "$APP_USER" -g "$APP_USER" "$APP_HOME/.ssh"
  # nginx serves staticfiles straight from the app directory, so it needs to traverse the home dir.
  usermod -aG "$APP_USER" www-data
}

setup_repo_access() {
  local key=$APP_HOME/.ssh/id_ed25519 known_hosts=$APP_HOME/.ssh/known_hosts scanned
  [[ -f $key ]] || as_app ssh-keygen -q -t ed25519 -N "" -C "$APP_USER@$(hostname)" -f "$key"

  if ! grep -q '^github.com ssh-ed25519 ' "$known_hosts" 2>/dev/null; then
    scanned=$(ssh-keyscan -t ed25519 github.com 2>/dev/null)
    [[ $(ssh-keygen -lf - <<<"$scanned" | awk '{print $2}') == "$GITHUB_ED25519_FINGERPRINT" ]] \
      || die "github.com host key doesn't match GitHub's published fingerprint; refusing to trust it."
    echo "$scanned" | as_app tee -a "$known_hosts" >/dev/null
  fi

  if ! as_app git ls-remote "$REPO" &>/dev/null; then
    log "Action needed: give this server read access to the repo"
    echo "Add this key in GitHub > repo > Settings > Deploy keys (leave 'Allow write access' off):"
    echo
    cat "$key.pub"
    echo
    echo "Then run this script again."
    exit 2
  fi
}

fetch_code() {
  if [[ -d $APP_DIR/.git ]]; then return 0; fi
  log "Cloning $REPO ($BRANCH)"
  as_app git clone --quiet --branch "$BRANCH" "$REPO" "$APP_DIR"
}

set_env() {
  local name=$1 value=$2
  if grep -q "^$name=" "$ENV_FILE"; then
    sed -i "s|^$name=.*|$name=$value|" "$ENV_FILE"
  else
    echo "$name=$value" >>"$ENV_FILE"
  fi
}

write_env_file() {
  log "Writing $ENV_FILE"
  install -d -m 750 -o root -g "$APP_USER" "$ENV_DIR"
  if [[ ! -f $ENV_FILE ]]; then
    install -m 640 -o root -g "$APP_USER" /dev/null "$ENV_FILE"
    cat >"$ENV_FILE" <<EOF
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
DJANGO_HTTPS=False
CONTACT_EMAIL=
EOF
  fi
  local hosts
  hosts=$(IFS=,; echo "$(public_ip)${DOMAINS[*]:+,${DOMAINS[*]}}")
  set_env DJANGO_ALLOWED_HOSTS "$hosts"
  printf 'SAVED_DOMAINS="%s"\nSAVED_EMAIL="%s"\n' "${DOMAINS[*]}" "$EMAIL" >"$STATE_FILE"
  chmod 600 "$STATE_FILE"
}

install_services() {
  log "Installing gunicorn systemd units and the nginx site"
  install -m 644 "$APP_DIR/deploy/systemd/gunicorn-active.socket" /etc/systemd/system/
  install -m 644 "$APP_DIR/deploy/systemd/gunicorn-active.service" /etc/systemd/system/
  systemctl daemon-reload
  systemctl enable --now gunicorn-active.socket >/dev/null

  local server_names
  server_names="$(public_ip) ${DOMAINS[*]}"
  sed "s|__SERVER_NAMES__|${server_names% }|" "$APP_DIR/deploy/nginx/active.conf" \
    >/etc/nginx/sites-available/active
  ln -sf /etc/nginx/sites-available/active /etc/nginx/sites-enabled/active
  rm -f /etc/nginx/sites-enabled/default
  nginx -t
  # A restart (not reload) so nginx workers pick up www-data's new group membership.
  systemctl restart nginx
}

enable_https() {
  [[ ${#DOMAINS[@]} -gt 0 ]] || return 0
  [[ -n $EMAIL ]] || { warn "Skipping HTTPS: --email is required with --domain."; return 0; }
  log "Setting up HTTPS for ${DOMAINS[*]}"
  local domain domain_args=()
  for domain in "${DOMAINS[@]}"; do domain_args+=(-d "$domain"); done
  if ! certbot --nginx --non-interactive --agree-tos --redirect --keep-until-expiring \
    -m "$EMAIL" "${domain_args[@]}"; then
    warn "certbot failed. Check each domain's DNS A record points at $(public_ip), then re-run."
    return 0
  fi
  set_env DJANGO_HTTPS True
  systemctl try-reload-or-restart gunicorn-active.service
}

summary() {
  local url
  url="http://$(public_ip)/"
  grep -q '^DJANGO_HTTPS=True' "$ENV_FILE" && url="https://${DOMAINS[0]}/"
  log "Done. The site is live at $url"
  cat <<EOF
  App code:     $APP_DIR
  Settings:     $ENV_FILE  (set CONTACT_EMAIL here, then: systemctl reload gunicorn-active)
  App logs:     journalctl -u gunicorn-active -f
  nginx logs:   /var/log/nginx/
  Deploy again: sudo $APP_DIR/deploy/deploy.sh
EOF
}

main() {
  parse_args "$@"
  check_system
  install_packages
  add_swap
  secure_server
  create_app_user
  setup_repo_access
  fetch_code
  write_env_file
  install_services
  "$APP_DIR/deploy/deploy.sh" --branch "$BRANCH"
  enable_https
  summary
}

main "$@"
exit
