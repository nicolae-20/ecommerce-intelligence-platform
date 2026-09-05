import os
from pathlib import Path
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _run_clean_import(module_name: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)

    return subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            f"import {module_name}",
        ],
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_bookkeeping_router_import_does_not_depend_on_import_order():
    result = _run_clean_import("api.routers.bookkeeping")

    assert result.returncode == 0, (
        "Direct bookkeeping router import failed without PYTHONPATH:\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_api_main_import_does_not_depend_on_import_order():
    result = _run_clean_import("api.main")

    assert result.returncode == 0, (
        "Direct api.main import failed without PYTHONPATH:\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
