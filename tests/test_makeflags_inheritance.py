"""Guard-rail: nested ``make`` subprocess tests under GNU make question mode."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
def test_nested_make_help_exits_nonzero_under_makeflags_question_mode() -> None:
    """When ``MAKEFLAGS`` carries question mode, nested ``make`` does not run recipes.

    ``tests/conftest.py`` clears inherited ``MAKEFLAGS`` per test so shell-out smoke
    tests stay reliable if a driver accidentally passed ``-q`` into the pytest child
    (for example the invalid ``make wiki-test -q`` pattern documented in the Makefile).
    """
    env = dict(os.environ)
    env["MAKEFLAGS"] = "q"
    r = subprocess.run(
        ["make", "help"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert r.returncode != 0, "expected GNU make question mode to avoid running the help recipe"
