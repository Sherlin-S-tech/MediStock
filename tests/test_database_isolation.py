import os
import subprocess
import sys
from pathlib import Path


def test_test_client_uses_per_test_temporary_database(app, tmp_path):
    database_path = Path(app.config["DATABASE"])
    assert database_path == tmp_path / "isolated-test.db"
    assert database_path.exists()


def test_importing_app_does_not_initialize_configured_database(tmp_path):
    database_path = tmp_path / "must-not-be-created.db"
    env = os.environ.copy()
    env["DATABASE_PATH"] = str(database_path)
    env["SEED_DEMO_DATA"] = "true"
    project_root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [sys.executable, "-c", "import app"],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert not database_path.exists()
