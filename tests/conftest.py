"""Pytest boot: allow ``import wiki_paths`` (and sibling script modules) from ``tests/``."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _ROOT / "scripts"
if _SCRIPTS.exists() and str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))


@pytest.fixture(autouse=True)
def _drop_makeflags_for_subprocess_make(monkeypatch: pytest.MonkeyPatch) -> None:
    """GNU make exports ``MAKEFLAGS`` to recipe subprocesses.

    If the outer driver used ``-q`` / ``--question`` (including the invalid
    ``make wiki-test -q`` pattern), nested ``subprocess.run(['make', ...])``
    inherits question mode: recipes are not run, exit code is ``1``, and
    stdout/stderr are often empty. Many tests shell out to ``make``; drop
    ``MAKEFLAGS`` for each test so those invocations stay non-interactive
    without inheriting question mode.
    """
    monkeypatch.delenv("MAKEFLAGS", raising=False)
