#!/usr/bin/env bash
set -euo pipefail

APP_USER=active
APP_DIR=/srv/active/app
ENV_FILE=/etc/active/active.env
SOCKET=/run/gunicorn-active.sock
BRANCH=main

usage() {
  cat <<'EOF'
Deploy the latest code for the Active site on a server set up by provision.sh.

Usage (as root on the server):
  sudo /srv/active/app/deploy/deploy.sh [--branch main]

From your own machine:
  ssh root@SERVER_IP /srv/active/app/deploy/deploy.sh

Pulls the branch (fast-forward only), installs requirements, runs Django's deploy
checks, collects static files, gracefully reloads gunicorn and smoke-tests the app.
EOF
}

log() { printf '\n\033[1;32m==> %s\033[0m\n' "$*"; }
die() { printf '\033[1;31mxx  %s\033[0m\n' "$*" >&2; exit 1; }
as_app() { sudo -u "$APP_USER" -H "$@"; }

manage() {
  # shellcheck disable=SC2016
  as_app bash -c 'set -a; . "$1"; set +a; shift; exec .venv/bin/python manage.py "$@"' _ "$ENV_FILE" "$@"
}

smoke_test() {
  local host code
  host=$(sed -n 's/^DJANGO_ALLOWED_HOSTS=\([^,]*\).*/\1/p' "$ENV_FILE")
  code=$(curl -s -o /dev/null -w '%{http_code}' --unix-socket "$SOCKET" \
    -H "Host: $host" -H "X-Forwarded-Proto: https" http://localhost/)
  [[ $code == 200 ]] || die "Smoke test failed (HTTP $code). Check: journalctl -u gunicorn-active -n 50"
  log "Smoke test passed: the home page returns HTTP 200"
}

main() {
  while [[ $# -gt 0 ]]; do
    case $1 in
      --branch) BRANCH=${2:?--branch needs a value}; shift 2 ;;
      -h | --help) usage; exit 0 ;;
      *) usage; die "Unknown option: $1" ;;
    esac
  done
  [[ $EUID -eq 0 ]] || die "Run as root: sudo $0"
  cd "$APP_DIR"

  log "Updating code ($BRANCH)"
  as_app git fetch --quiet origin "$BRANCH"
  as_app git checkout --quiet "$BRANCH"
  as_app git merge --quiet --ff-only "origin/$BRANCH"
  as_app git log -1 --format='    %h %s'

  log "Installing Python dependencies"
  [[ -d .venv ]] || as_app python3 -m venv .venv
  as_app .venv/bin/pip install --quiet --upgrade pip
  as_app .venv/bin/pip install --quiet -r requirements/prod.txt

  log "Running deploy checks and collecting static files"
  manage check --deploy
  manage collectstatic --no-input --verbosity 0

  log "Reloading gunicorn"
  systemctl try-reload-or-restart gunicorn-active.service
  smoke_test
}

# Bash reads scripts lazily and git may rewrite this file mid-run, so everything runs from main().
main "$@"
exit
