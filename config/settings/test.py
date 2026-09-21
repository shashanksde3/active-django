from .base import *  # noqa: F403

DEBUG = False

SECRET_KEY = "django-insecure-test-only"

ALLOWED_HOSTS = ["testserver"]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Tests never run collectstatic; autorefresh stops WhiteNoise expecting STATIC_ROOT to exist.
WHITENOISE_AUTOREFRESH = True
