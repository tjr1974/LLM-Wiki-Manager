from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_wiki_family_snapshot():
    path = ROOT / "scripts" / "wiki_family_snapshot.py"
    spec = importlib.util.spec_from_file_location("wiki_family_snapshot_under_test", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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
    assert data.get("warnings") == []
    assert data.get("warning_codes") == []
    assert len(data.get("warnings") or []) == len(data.get("warning_codes") or [])


def test_wiki_family_snapshot_warns_compare_root_same_as_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mod = _load_wiki_family_snapshot()
    mgr = tmp_path / "mgr"
    mgr.mkdir()
    shared = tmp_path / "shared-checkout"
    shared.mkdir()
    reg = {
        "v": 1,
        "managed_children": [{"id": "dup-child", "label": "Dup", "path_env": "E_CHILD_PATH"}],
    }
    (mgr / "registry.json").write_text(json.dumps(reg), encoding="utf-8")
    monkeypatch.setenv("E_CHILD_PATH", str(shared))
    monkeypatch.setenv("WIKI_MANAGER_COMPARE_ROOT", str(shared))
    registry = mod.load_wiki_manager_registry(mgr, "registry.json")
    snap = mod.build_snapshot(mgr, registry)
    ws = snap.get("warnings") or []
    codes = snap.get("warning_codes") or []
    assert len(ws) == len(codes)
    assert mod.WARNING_COMPARE_ROOT_EQUALS_MANAGED_CHILD in codes
    assert any("same directory as managed child" in w for w in ws), ws


def test_wiki_family_snapshot_warns_compare_root_is_manager(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mod = _load_wiki_family_snapshot()
    mgr = tmp_path / "mgr"
    mgr.mkdir()
    reg = {"v": 1, "managed_children": []}
    (mgr / "registry.json").write_text(json.dumps(reg), encoding="utf-8")
    monkeypatch.setenv("WIKI_MANAGER_COMPARE_ROOT", str(mgr.resolve()))
    registry = mod.load_wiki_manager_registry(mgr, "registry.json")
    snap = mod.build_snapshot(mgr, registry)
    ws = snap.get("warnings") or []
    codes = snap.get("warning_codes") or []
    assert len(ws) == len(codes)
    assert codes == [mod.WARNING_COMPARE_ROOT_IS_MANAGER]
    assert any("points at this manager checkout" in w for w in ws), ws


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


def test_compare_root_env_key_defaults_and_registry_override() -> None:
    mod = _load_wiki_family_snapshot()
    assert mod.compare_root_env_key({"v": 1}) == "WIKI_MANAGER_COMPARE_ROOT"
    assert mod.compare_root_env_key({"v": 1, "compare_root_env": "MY_BASE"}) == "MY_BASE"
    assert mod.compare_root_env_key({"v": 1, "compare_root_env": "  "}) == "WIKI_MANAGER_COMPARE_ROOT"
    assert mod.compare_root_env_key({"v": 1, "compare_root_env": 99}) == "WIKI_MANAGER_COMPARE_ROOT"


def test_wiki_family_snapshot_text_includes_manager_root() -> None:
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "wiki_family_snapshot.py"), "--repo-root", str(ROOT)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    assert "manager_root:" in r.stdout
    assert str(ROOT.resolve()) in r.stdout


def test_wiki_family_snapshot_text_prefixes_warning_with_code(tmp_path: Path) -> None:
    mgr = tmp_path / "mgr"
    mgr.mkdir()
    (mgr / "registry.json").write_text(json.dumps({"v": 1, "managed_children": []}), encoding="utf-8")
    env = dict(os.environ)
    env["WIKI_MANAGER_COMPARE_ROOT"] = str(mgr.resolve())
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "wiki_family_snapshot.py"),
            "--repo-root",
            str(mgr),
            "--registry",
            "registry.json",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    assert "warning [compare_root_is_manager]:" in r.stdout
