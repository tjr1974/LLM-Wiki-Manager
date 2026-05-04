from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _isolate_wiki_manager_compare_root(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WIKI_MANAGER_COMPARE_ROOT", raising=False)


def test_wiki_family_snapshot_json_shape() -> None:
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "wiki_family_snapshot.py"), "--repo-root", str(ROOT), "--json"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    data = json.loads(r.stdout)
    assert data.get("v") == 1
    assert data.get("manager_root") == str(ROOT.resolve())
    repos = data.get("repos")
    assert isinstance(repos, list)
    assert any(x.get("role") == "llm-wiki-manager" for x in repos)
    base_rows = [x for x in repos if x.get("role") == "llm-wiki-base-model"]
    assert len(base_rows) == 1
    assert base_rows[0].get("path_resolved") is False


def test_make_wiki_manager_snapshot_json_runs() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "wiki-manager-snapshot-json:" in makefile
    assert "wiki_family_snapshot.py --json" in makefile
    r = subprocess.run(["make", "-C", str(ROOT), "wiki-manager-snapshot-json"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr + r.stdout
    combined = r.stdout + r.stderr
    start = combined.index("{")
    end = combined.rindex("}") + 1
    data = json.loads(combined[start:end])
    assert data.get("v") == 1
    assert data.get("manager_root") == str(ROOT.resolve())


def test_wiki_family_snapshot_text_includes_manager_root() -> None:
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "wiki_family_snapshot.py"), "--repo-root", str(ROOT)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    assert "manager_root:" in r.stdout
    assert str(ROOT.resolve()) in r.stdout
