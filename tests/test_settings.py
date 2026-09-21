import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PRODUCTION_ENV = {
    "DJANGO_SETTINGS_MODULE": "config.settings.prod",
    "DJANGO_SECRET_KEY": "x7!qZ9#mP2" * 6,
    "RENDER_EXTERNAL_HOSTNAME": "active-d.onrender.com",
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


def test_production_settings_pass_the_deploy_checks() -> None:
    result = run_manage("check", "--deploy", "--fail-level", "WARNING")

    assert result.returncode == 0, result.stderr


def test_blank_contact_email_falls_back_to_the_default() -> None:
    result = run_manage(
        "shell",
        "--verbosity",
        "0",
        "-c",
        "from django.conf import settings; print(settings.CONTACT_EMAIL)",
        CONTACT_EMAIL="",
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "contact@example.com"
