from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from _resolved_python import RESOLVED_PYTHON

ROOT = Path(__file__).resolve().parents[1]


def test_resolved_python_is_absolute_existing_file() -> None:
    p = Path(RESOLVED_PYTHON)
    assert p.is_absolute()
    assert p.is_file()


def test_resolved_python_module_docstring_lists_operator_anchors() -> None:
    text = (ROOT / "tests" / "_resolved_python.py").read_text(encoding="utf-8")
    assert "schema/AGENTS.md" in text
    assert "## Pytest subprocess hygiene" in text
    assert "test_build_hub_links.py" in text
    assert "tests/conftest.py" in text
    assert "MAKEFLAGS" in text
    assert "Cross-link:" in text


@pytest.mark.skipif(not (ROOT / ".git").exists(), reason="not a git checkout")
def test_resolved_python_tracked_in_git_index() -> None:
    """Regression: subprocess tests import this module. Untracked file breaks fresh clones and CI."""
    r = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "tests/_resolved_python.py"],
        cwd=ROOT,
        capture_output=True,
    )
    assert r.returncode == 0, (
        "tests/_resolved_python.py must be tracked (git add tests/_resolved_python.py) "
        "so clones and CI match schema/AGENTS.md Pytest subprocess hygiene"
    )


def test_build_hub_links_tmp_repo(tmp_path: Path) -> None:
    wiki = tmp_path / "wiki"
    (wiki / "entities").mkdir(parents=True)
    (wiki / "synthesis").mkdir(parents=True)
    (wiki / "entities" / "e1.md").write_text("# e\n", encoding="utf-8")
    (wiki / "main.md").write_text("# m\n", encoding="utf-8")

    r = subprocess.run(
        [
            RESOLVED_PYTHON,
            str(ROOT / "scripts" / "build_hub_links.py"),
            "--repo-root",
            str(tmp_path),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    out = tmp_path / "wiki" / "synthesis" / "hub-index.md"
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "[[entities/e1]]" in text
    assert "[[main]]" in text
    assert "[[synthesis/hub-index]]" not in text
