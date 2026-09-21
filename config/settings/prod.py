from .base import *  # noqa: F403
from .base import STORAGES, env

DEBUG = False

SECRET_KEY = env("DJANGO_SECRET_KEY")

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])
if render_hostname := env("RENDER_EXTERNAL_HOSTNAME", default=None):
    ALLOWED_HOSTS.append(render_hostname)

CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
# Also secures the messages cookie: CookieStorage reuses the session cookie flags.
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Start low; raise to 31536000 once HTTPS is confirmed on the client's final domain.
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=3600)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# HSTS preload is a per-domain commitment the client must opt into explicitly.
SILENCED_SYSTEM_CHECKS = ["security.W021"]

STORAGES = {
    **STORAGES,
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
