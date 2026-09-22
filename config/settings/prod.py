from .base import *  # noqa: F403
from .base import STORAGES, env

DEBUG = False

SECRET_KEY = env("DJANGO_SECRET_KEY")

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

# Safe only because nginx always overwrites this header (see deploy/nginx/active.conf).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Off while a new server is reachable only by IP over plain HTTP; on once certbot has issued a cert.
HTTPS = env.bool("DJANGO_HTTPS", default=True)
SECURE_SSL_REDIRECT = HTTPS
# Also secures the messages cookie: CookieStorage reuses the session cookie flags.
SESSION_COOKIE_SECURE = HTTPS
CSRF_COOKIE_SECURE = HTTPS

# Start low; raise to 31536000 once HTTPS is confirmed on the client's final domain.
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=3600) if HTTPS else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# HSTS preload is a per-domain commitment the client must opt into explicitly.
SILENCED_SYSTEM_CHECKS = ["security.W021"]

STORAGES = {
    **STORAGES,
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
