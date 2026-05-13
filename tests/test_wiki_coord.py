from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
_COORD = _REPO / "scripts" / "wiki_coord.py"
_REG = _REPO / "schema" / "wiki_family_registry.v1.json"


def _minimal_manager_tree(dest: Path) -> Path:
    (dest / "schema").mkdir(parents=True)
    (dest / "scripts").mkdir(parents=True)
    shutil.copy(_REG, dest / "schema" / _REG.name)
    shutil.copy(_COORD, dest / "scripts" / _COORD.name)
    return dest


def _run_coord(root: Path, args: list[str], env: dict | None = None):
    merged = dict(os.environ)
    if env:
        merged.update(env)
    return subprocess.run(
        [sys.executable, str(_COORD)] + ["--repo-root", str(root)] + args,
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )


@pytest.fixture()
def fake_manager(tmp_path: Path) -> Path:
    return _minimal_manager_tree(tmp_path / "mgr")


def test_snapshot_json_shape_without_optional_env(monkeypatch, fake_manager: Path):
    monkeypatch.delenv("WIKI_MANAGER_COMPARE_ROOT", raising=False)
    monkeypatch.delenv("WIKI_MANAGER_CHILD_SHAOLIN", raising=False)
    monkeypatch.delenv("WIKI_MANAGER_CHILD_TAI_PAN", raising=False)
    cp = _run_coord(fake_manager, ["snapshot", "--json"])
    assert cp.returncode == 0, cp.stderr
    data = json.loads(cp.stdout)
    assert data["v"] == 1
    assert "generated_at_utc" in data
    assert data["warning_codes"] == data["family_snapshot_warning_codes"] == []
    assert data["llm_wiki_base_model"]["path_resolved_from_env"] is False
    for ch in data["managed_children"]:
        assert ch.get("path") is None


def test_compare_root_collision_warns(monkeypatch, fake_manager: Path):
    mgr = fake_manager.resolve()
    env = {"WIKI_MANAGER_COMPARE_ROOT": str(mgr)}
    cp = _run_coord(fake_manager, ["snapshot", "--json"], env=env)
    assert cp.returncode == 0
    data = json.loads(cp.stdout)
    assert "compare_root_is_manager" in data["warning_codes"]
    assert "compare_root_is_manager" in data["family_snapshot_warning_codes"]
    assert data["warning_codes"] == data["family_snapshot_warning_codes"]


def test_duplicate_child_path_warns(tmp_path: Path, monkeypatch, fake_manager: Path):
    same = tmp_path / "same_child_dir"
    same.mkdir(parents=True)
    env = {
        "WIKI_MANAGER_CHILD_SHAOLIN": str(same),
        "WIKI_MANAGER_CHILD_TAI_PAN": str(same),
    }
    cp = _run_coord(fake_manager, ["snapshot", "--json"], env=env)
    assert cp.returncode == 0
    data = json.loads(cp.stdout)
    assert "duplicate_child_path" in data["warning_codes"]
    assert data["warning_codes"].count("duplicate_child_path") == 1


def test_compare_root_equals_managed_child_warns(tmp_path: Path, monkeypatch, fake_manager: Path):
    child = tmp_path / "fork_a"
    child.mkdir(parents=True)
    env = {
        "WIKI_MANAGER_COMPARE_ROOT": str(child),
        "WIKI_MANAGER_CHILD_SHAOLIN": str(child),
    }
    cp = _run_coord(fake_manager, ["snapshot", "--json"], env=env)
    assert cp.returncode == 0
    data = json.loads(cp.stdout)
    assert "compare_root_equals_managed_child" in data["warning_codes"]
    assert (
        data["warning_codes"].count("compare_root_equals_managed_child") == 1
    )


def test_status_writes_rollup(tmp_path: Path, monkeypatch, fake_manager: Path):
    out = tmp_path / "out" / "sync.json"
    monkeypatch.delenv("WIKI_MANAGER_COMPARE_ROOT", raising=False)
    cp = subprocess.run(
        [
            sys.executable,
            str(_COORD),
            "--repo-root",
            str(fake_manager),
            "status",
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
        check=False,
        env=os.environ.copy(),
    )
    assert cp.returncode == 0, cp.stderr
    assert out.is_file()
    rollup = json.loads(out.read_text(encoding="utf-8"))
    fs = rollup["family_snapshot"]
    assert isinstance(fs["family_snapshot_warning_codes"], list)


def _run_ci_smoke_on_stdin(blob: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_COORD), "ci-smoke-check-stdin"],
        input=blob,
        text=True,
        capture_output=True,
        check=False,
        cwd=str(_REPO),
        env=os.environ.copy(),
    )


def test_ci_smoke_rejects_empty_stdin():
    cp = _run_ci_smoke_on_stdin("")
    assert cp.returncode != 0
    assert "expects JSON" in (cp.stderr or "")


def test_ci_smoke_rejects_invalid_json():
    cp = _run_ci_smoke_on_stdin("not json")
    assert cp.returncode != 0
    assert "invalid JSON" in (cp.stderr or "")


def test_ci_smoke_rejects_missing_warning_codes_list():
    bad = {"v": 1, "generated_at_utc": "dummy", "family_snapshot": {"family_snapshot_warning_codes": []}}
    cp = _run_ci_smoke_on_stdin(json.dumps(bad))
    assert cp.returncode != 0
    assert "warning_codes" in (cp.stderr or "")


def test_ci_smoke_rejects_family_snapshot_must_be_json_object():
    for payload in (
        {"v": 1},
        {"v": 1, "family_snapshot": None},
        {"v": 1, "family_snapshot": ["x"]},
    ):
        cp = _run_ci_smoke_on_stdin(json.dumps(payload))
        assert cp.returncode != 0, payload
        assert "JSON object" in (cp.stderr or "")


def test_ci_smoke_rejects_when_family_snapshot_warning_codes_missing():
    bad = {
        "v": 1,
        "generated_at_utc": "dummy",
        "family_snapshot": {"warning_codes": []},
    }
    cp = _run_ci_smoke_on_stdin(json.dumps(bad))
    assert cp.returncode != 0
    assert "family_snapshot_warning_codes" in (cp.stderr or "")


def test_ci_smoke_accepts_rollup_when_warnings_present(monkeypatch, fake_manager: Path):
    mgr = str(fake_manager.resolve())
    monkeypatch.delenv("WIKI_MANAGER_CHILD_SHAOLIN", raising=False)
    monkeypatch.delenv("WIKI_MANAGER_CHILD_TAI_PAN", raising=False)
    proc_status = subprocess.run(
        [
            sys.executable,
            str(_COORD),
            "--repo-root",
            str(fake_manager),
            "status",
            "--json",
            "--out",
            str(fake_manager / "runtime" / "warnings.json"),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "WIKI_MANAGER_COMPARE_ROOT": mgr},
    )
    assert proc_status.returncode == 0
    snap = json.loads(proc_status.stdout)["family_snapshot"]
    assert "compare_root_is_manager" in snap["warning_codes"]
    proc_smoke = _run_ci_smoke_on_stdin(proc_status.stdout)
    assert proc_smoke.returncode == 0, proc_smoke.stderr


def test_registry_invalid_json_exits(fake_manager: Path):
    (fake_manager / "schema" / "wiki_family_registry.v1.json").write_text("{", encoding="utf-8")
    cp = _run_coord(fake_manager, ["list"])
    assert cp.returncode != 0
    assert "invalid registry JSON" in cp.stderr


def test_registry_compare_root_env_must_be_nonempty_string(fake_manager: Path):
    data = json.loads((_REPO / "schema" / "wiki_family_registry.v1.json").read_text(encoding="utf-8"))
    data["compare_root_env"] = "   "
    (fake_manager / "schema" / "wiki_family_registry.v1.json").write_text(
        json.dumps(data),
        encoding="utf-8",
    )
    cp = _run_coord(fake_manager, ["list"])
    assert cp.returncode != 0
    assert "compare_root_env" in cp.stderr


def test_registry_compare_root_env_must_be_string_type(fake_manager: Path):
    data = json.loads((_REPO / "schema" / "wiki_family_registry.v1.json").read_text(encoding="utf-8"))
    data["compare_root_env"] = 1
    (fake_manager / "schema" / "wiki_family_registry.v1.json").write_text(
        json.dumps(data),
        encoding="utf-8",
    )
    cp = _run_coord(fake_manager, ["list"])
    assert cp.returncode != 0
    assert "compare_root_env" in cp.stderr


def test_ci_smoke_rejects_mismatched_duplicate_lists():
    bad = {
        "v": 1,
        "generated_at_utc": "dummy",
        "family_snapshot": {
            "warning_codes": ["a"],
            "family_snapshot_warning_codes": [],
        },
    }
    cp = _run_ci_smoke_on_stdin(json.dumps(bad))
    assert cp.returncode != 0
    assert "match" in (cp.stderr or "").lower()


def test_ci_smoke_accepts_rollout_stdin(monkeypatch, fake_manager: Path):
    monkeypatch.delenv("WIKI_MANAGER_COMPARE_ROOT", raising=False)
    proc_status = subprocess.run(
        [
            sys.executable,
            str(_COORD),
            "--repo-root",
            str(fake_manager),
            "status",
            "--json",
            "--out",
            str(fake_manager / "runtime" / "ignored.json"),
        ],
        capture_output=True,
        text=True,
        check=False,
        env=os.environ.copy(),
    )
    assert proc_status.returncode == 0
    proc_smoke = _run_ci_smoke_on_stdin(proc_status.stdout)
    assert proc_smoke.returncode == 0, proc_smoke.stderr


def test_missing_registry_file_exits(fake_manager: Path):
    reg_path = fake_manager / "schema" / "wiki_family_registry.v1.json"
    reg_path.unlink()
    cp = _run_coord(fake_manager, ["list"])
    assert cp.returncode != 0
    assert "missing registry:" in cp.stderr


def test_registry_v_must_be_one(fake_manager: Path):
    p = fake_manager / "schema" / "wiki_family_registry.v1.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    data["v"] = 2
    p.write_text(json.dumps(data), encoding="utf-8")
    cp = _run_coord(fake_manager, ["list"])
    assert cp.returncode != 0
    assert "registry v must be 1" in cp.stderr


def test_repo_root_must_be_existing_directory(fake_manager: Path):
    missing = fake_manager.parent / "nope-this-manager-checkout"
    cp = subprocess.run(
        [
            sys.executable,
            str(_COORD),
            "--repo-root",
            str(missing),
            "list",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=os.environ.copy(),
    )
    assert cp.returncode != 0
    assert "not an existing directory" in cp.stderr


def test_registry_managed_children_row_must_be_object(fake_manager: Path):
    data = json.loads((_REPO / "schema" / "wiki_family_registry.v1.json").read_text(encoding="utf-8"))
    data["managed_children"][1] = "not-an-object"
    (fake_manager / "schema" / "wiki_family_registry.v1.json").write_text(
        json.dumps(data),
        encoding="utf-8",
    )
    cp = _run_coord(fake_manager, ["list"])
    assert cp.returncode != 0
    assert "must be an object" in cp.stderr


def test_registry_managed_children_must_be_list(fake_manager: Path):
    data = json.loads((_REPO / "schema" / "wiki_family_registry.v1.json").read_text(encoding="utf-8"))
    data["managed_children"] = None
    (fake_manager / "schema" / "wiki_family_registry.v1.json").write_text(
        json.dumps(data),
        encoding="utf-8",
    )
    cp = _run_coord(fake_manager, ["list"])
    assert cp.returncode != 0
    assert "managed_children must be a list" in cp.stderr


def test_registry_rejects_duplicate_path_env_rows(fake_manager: Path):
    data = json.loads((_REPO / "schema" / "wiki_family_registry.v1.json").read_text(encoding="utf-8"))
    kid_a = dict(data["managed_children"][0])
    kid_b = dict(data["managed_children"][1])
    kid_b["path_env"] = kid_a["path_env"]
    kid_b["id"] = "other-id-duplicated-env"
    kid_b["label"] = "Other Child"
    data["managed_children"] = [kid_a, kid_b]
    (fake_manager / "schema" / "wiki_family_registry.v1.json").write_text(
        json.dumps(data),
        encoding="utf-8",
    )
    cp = _run_coord(fake_manager, ["list"])
    assert cp.returncode != 0
    assert "duplicate managed_children[].path_env" in cp.stderr


def test_ci_smoke_rejects_when_family_snapshot_warning_codes_not_list():
    bad = {
        "v": 1,
        "generated_at_utc": "dummy",
        "family_snapshot": {
            "warning_codes": [],
            "family_snapshot_warning_codes": "not-list",
        },
    }
    cp = _run_ci_smoke_on_stdin(json.dumps(bad))
    assert cp.returncode != 0
    assert "must be a list" in (cp.stderr or "")


def test_ci_smoke_rejects_invalid_family_snapshot_v_when_lists_aligned():
    bad = {
        "v": 1,
        "generated_at_utc": "2020-01-01T00:00:00Z",
        "family_snapshot": {
            "v": 0,
            "manager_root": "/tmp/mgr",
            "llm_wiki_base_model": {},
            "managed_children": [],
            "warnings": [],
            "warning_codes": [],
            "family_snapshot_warning_codes": [],
        },
    }
    cp = _run_ci_smoke_on_stdin(json.dumps(bad))
    assert cp.returncode != 0
    assert "family_snapshot v must be 1" in (cp.stderr or "")


def test_ci_smoke_rejects_invalid_rollout_v_when_snapshot_valid():
    bad = {
        "v": 2,
        "generated_at_utc": "2020-01-01T00:00:00Z",
        "family_snapshot": {
            "v": 1,
            "manager_root": "/tmp/mgr",
            "llm_wiki_base_model": {},
            "managed_children": [],
            "warnings": [],
            "warning_codes": [],
            "family_snapshot_warning_codes": [],
        },
    }
    cp = _run_ci_smoke_on_stdin(json.dumps(bad))
    assert cp.returncode != 0
    assert "rollup v must be 1" in (cp.stderr or "")


def test_ci_smoke_rejects_missing_manager_root_when_lists_aligned():
    bad = {
        "v": 1,
        "generated_at_utc": "2020-01-01T00:00:00Z",
        "family_snapshot": {
            "v": 1,
            "llm_wiki_base_model": {},
            "managed_children": [],
            "warnings": [],
            "warning_codes": [],
            "family_snapshot_warning_codes": [],
        },
    }
    cp = _run_ci_smoke_on_stdin(json.dumps(bad))
    assert cp.returncode != 0
    assert "manager_root" in (cp.stderr or "")


def test_registry_managed_child_id_must_be_nonempty(fake_manager: Path):
    corrupt = json.loads((_REPO / "schema" / "wiki_family_registry.v1.json").read_text(encoding="utf-8"))
    corrupt["managed_children"][0]["id"] = "   "
    (fake_manager / "schema" / "wiki_family_registry.v1.json").write_text(
        json.dumps(corrupt),
        encoding="utf-8",
    )
    cp = _run_coord(fake_manager, ["list"])
    assert cp.returncode != 0
    assert ".id must be a non-empty string" in cp.stderr


def test_registry_managed_child_id_rejects_json_null(fake_manager: Path):
    corrupt = json.loads((_REPO / "schema" / "wiki_family_registry.v1.json").read_text(encoding="utf-8"))
    corrupt["managed_children"][0]["id"] = None
    (fake_manager / "schema" / "wiki_family_registry.v1.json").write_text(
        json.dumps(corrupt),
        encoding="utf-8",
    )
    cp = _run_coord(fake_manager, ["list"])
    assert cp.returncode != 0
    assert ".id must be a non-empty string" in cp.stderr


def test_registry_managed_child_path_env_rejects_json_null(fake_manager: Path):
    corrupt = json.loads((_REPO / "schema" / "wiki_family_registry.v1.json").read_text(encoding="utf-8"))
    corrupt["managed_children"][0]["path_env"] = None
    (fake_manager / "schema" / "wiki_family_registry.v1.json").write_text(
        json.dumps(corrupt),
        encoding="utf-8",
    )
    cp = _run_coord(fake_manager, ["list"])
    assert cp.returncode != 0
    assert ".path_env must be a non-empty string" in cp.stderr


def test_registry_managed_child_must_have_path_env(fake_manager: Path):
    corrupt = json.loads((_REPO / "schema" / "wiki_family_registry.v1.json").read_text(encoding="utf-8"))
    corrupt["managed_children"][0].pop("path_env", None)
    (fake_manager / "schema" / "wiki_family_registry.v1.json").write_text(
        json.dumps(corrupt),
        encoding="utf-8",
    )
    cp = _run_coord(fake_manager, ["list"])
    assert cp.returncode != 0
    assert "path_env" in cp.stderr


def test_list_line_output(fake_manager: Path, monkeypatch):
    monkeypatch.delenv("WIKI_MANAGER_COMPARE_ROOT", raising=False)
    cp = _run_coord(fake_manager, ["list"])
    assert cp.returncode == 0
    assert "manager_root" in cp.stdout
    assert "WIKI_MANAGER_COMPARE_ROOT" in cp.stdout


@pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
def test_make_coord_ci_smoke_exits_zero():
    """Integration guard: POSIX make recipe must propagate status failures (tempfile capture)."""
    cp = subprocess.run(
        ["make", "-C", str(_REPO), "coord-ci-smoke"],
        capture_output=True,
        text=True,
        check=False,
        env=os.environ.copy(),
        timeout=120,
    )
    assert cp.returncode == 0, cp.stdout + cp.stderr


def test_wiki_coord_help_epilog_mentions_fork_delta_help():
    cp = subprocess.run(
        [sys.executable, str(_COORD), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert cp.returncode == 0, cp.stderr
    # argparse may wrap the epilog across lines (e.g. "coord-\nfork-delta-help").
    out = (cp.stdout + cp.stderr).replace("\n", "")
    assert "coord-fork-delta-help" in out
    assert "fork-sync" in out.lower() or "fork-delta" in out.lower()


@pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
def test_make_help_lists_coord_fork_delta_help():
    cp = subprocess.run(
        ["make", "-C", str(_REPO), "help"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert cp.returncode == 0, cp.stderr
    assert "coord-fork-delta-help" in cp.stdout + cp.stderr


@pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
def test_make_coord_fork_delta_help_prints_base_model_recipe():
    cp = subprocess.run(
        ["make", "-C", str(_REPO), "coord-fork-delta-help"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert cp.returncode == 0, cp.stderr
    out = cp.stdout + cp.stderr
    assert "fork-delta-full" in out
    assert "WIKI_MANAGER_COMPARE_ROOT" in out
    assert "CHILD_PATH_OVERRIDES" in out or "fork_delta_child_path_overrides" in out
    assert "fork-delta-scan" in out
    assert "human-wiki-universal-backlog" in out
