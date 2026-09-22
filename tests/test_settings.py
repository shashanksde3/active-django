import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PRODUCTION_ENV = {
    "DJANGO_SETTINGS_MODULE": "config.settings.prod",
    "DJANGO_SECRET_KEY": "x7!qZ9#mP2" * 6,
    "DJANGO_ALLOWED_HOSTS": "203.0.113.10,example.com",
}


def run_manage(*args: str, **env: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "manage.py", *args],
        cwd=PROJECT_ROOT,
        env={**os.environ, **PRODUCTION_ENV, **env},
        capture_output=True,
        text=True,
        check=False,
    )


def production_settings(*names: str, **env: str) -> list[str]:
    code = f"from django.conf import settings; print(*[getattr(settings, n) for n in {names!r}])"
    result = run_manage("shell", "--verbosity", "0", "-c", code, **env)
    assert result.returncode == 0, result.stderr
    return result.stdout.split()


def test_production_settings_pass_the_deploy_checks() -> None:
    result = run_manage("check", "--deploy", "--fail-level", "WARNING")

    assert result.returncode == 0, result.stderr


def test_https_is_enforced_by_default() -> None:
    values = production_settings(
        "SECURE_SSL_REDIRECT", "SESSION_COOKIE_SECURE", "CSRF_COOKIE_SECURE", "SECURE_HSTS_SECONDS"
    )

    assert values == ["True", "True", "True", "3600"]


def test_http_only_server_can_turn_https_enforcement_off() -> None:
    values = production_settings(
        "SECURE_SSL_REDIRECT",
        "SESSION_COOKIE_SECURE",
        "CSRF_COOKIE_SECURE",
        "SECURE_HSTS_SECONDS",
        DJANGO_HTTPS="False",
    )

    assert values == ["False", "False", "False", "0"]


def test_blank_contact_email_falls_back_to_the_default() -> None:
    assert production_settings("CONTACT_EMAIL", CONTACT_EMAIL="") == ["contact@example.com"]
