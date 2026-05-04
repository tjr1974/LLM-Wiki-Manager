"""Absolute ``sys.executable`` for subprocess tests.

``subprocess.run(..., cwd=other_dir)`` resolves argv[0] relative to ``cwd`` when
it is not absolute; a venv often yields a relative ``.venv/bin/python3``.

Operator contract: ``schema/AGENTS.md`` (``## Pytest subprocess hygiene``).
Reference subprocess test: ``tests/test_build_hub_links.py``. Cross-link:
``tests/conftest.py`` documents nested ``make`` and inherited ``MAKEFLAGS``.
"""

from __future__ import annotations

import sys
from pathlib import Path

RESOLVED_PYTHON = str(Path(sys.executable).resolve())
