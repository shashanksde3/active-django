import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_production_settings_pass_the_deploy_checks() -> None:
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "config.settings.prod",
        "DJANGO_SECRET_KEY": "x7!qZ9#mP2" * 6,
        "RENDER_EXTERNAL_HOSTNAME": "active-d.onrender.com",
    }

    result = subprocess.run(
        [sys.executable, "manage.py", "check", "--deploy", "--fail-level", "WARNING"],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
