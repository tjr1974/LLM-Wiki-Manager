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


def test_wiki_manager_sync_status_json_shape(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    reg = {
        "v": 1,
        "managed_children": [
            {"id": "sync-test-wiki", "label": "Sync", "path_env": "WIKI_MANAGER_ITEST_SYNC_CHILD"},
        ],
    }
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(json.dumps(reg), encoding="utf-8")
    child = tmp_path / "child"
    child.mkdir()
    monkeypatch.setenv("WIKI_MANAGER_ITEST_SYNC_CHILD", str(child))
    out_rel = "sync_status.min.json"
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "wiki_manager_sync_status.py"),
            "--repo-root",
            str(tmp_path),
            "--registry",
            "registry.json",
            "--out",
            out_rel,
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    out = tmp_path / out_rel
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data.get("v") == 1
    assert data.get("drift_compare_mode") == "manager-vs-child"
    assert "drift_warnings" in data and isinstance(data["drift_warnings"], list)
    snap = data.get("family_snapshot")
    assert isinstance(snap, dict) and snap.get("v") == 1
    kids = data.get("managed_children")
    assert isinstance(kids, list) and len(kids) == 1
    assert kids[0].get("id") == "sync-test-wiki"
    assert kids[0].get("fork_delta_report") is None


def test_wiki_manager_sync_status_digests_report_when_present(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mgr = tmp_path / "mgr"
    mgr.mkdir()
    reg = {
        "v": 1,
        "managed_children": [
            {"id": "digest-wiki", "label": "Digest", "path_env": "WIKI_MANAGER_ITEST_DIGEST_CHILD"},
        ],
    }
    reg_path = mgr / "registry.json"
    reg_path.write_text(json.dumps(reg), encoding="utf-8")
    child = tmp_path / "child2"
    child.mkdir()
    monkeypatch.setenv("WIKI_MANAGER_ITEST_DIGEST_CHILD", str(child))
    base = tmp_path / "base-model"
    base.mkdir()
    monkeypatch.setenv("WIKI_MANAGER_COMPARE_ROOT", str(base))

    report_dir = mgr / "ai/runtime/manager/digest-wiki"
    report_dir.mkdir(parents=True)
    report_dir.joinpath("fork_delta_report.min.json").write_text(
        json.dumps(
            {
                "high_priority_upstream_paths": ["a.py", "b.py"],
                "candidate_upstream_paths": ["a.py"],
                "review_queue": [{"path": "a.py"}],
            }
        ),
        encoding="utf-8",
    )
    report_dir.joinpath("fork_delta_summary.min.json").write_text(
        json.dumps({"recommendation": "review_safe_paths_first"}),
        encoding="utf-8",
    )

    out = mgr / "out/sync.json"
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "wiki_manager_sync_status.py"),
            "--repo-root",
            str(mgr),
            "--registry",
            "registry.json",
            "--out",
            "out/sync.json",
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["drift_compare_mode"] == "base-model-vs-child"
    row = data["managed_children"][0]["fork_delta_report"]
    assert row is not None
    assert row["high_priority_upstream_paths"] == 2
    assert row["candidate_upstream_paths"] == 1
    assert row["review_queue"] == 1
    summ = data["managed_children"][0]["fork_delta_summary"]
    assert summ and summ.get("recommendation") == "review_safe_paths_first"


def test_make_wiki_manager_sync_status_json_runs() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "wiki-manager-sync-status-json:" in makefile
    r = subprocess.run(["make", "-C", str(ROOT), "wiki-manager-sync-status-json"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr + r.stdout
    combined = r.stdout + r.stderr
    start = combined.index("{")
    end = combined.rindex("}") + 1
    data = json.loads(combined[start:end])
    assert data.get("v") == 1
    assert "drift_compare_mode" in data
