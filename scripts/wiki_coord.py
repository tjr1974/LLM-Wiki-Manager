#!/usr/bin/env python3
"""LLM Wiki Manager — enumerate registered family checkouts and emit sync snapshots."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REGISTRY_REL = Path("schema") / "wiki_family_registry.v1.json"
DEFAULT_STATUS_OUT = Path("runtime") / "sync_status.min.json"


def utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )


def manager_root(cli: str | None) -> Path:
    if cli:
        here = Path(cli).expanduser().resolve()
        if not here.is_dir():
            raise SystemExit(f"--repo-root is not an existing directory: {here}")
        return here
    here = Path(__file__).resolve().parent.parent
    return here


def load_registry(root: Path) -> dict[str, Any]:
    path = root / REGISTRY_REL
    if not path.is_file():
        raise SystemExit(f"missing registry: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid registry JSON ({path}, {exc})") from None
    if data.get("v") != 1:
        raise SystemExit("registry v must be 1")
    cre = data.get("compare_root_env")
    if cre is not None and (not isinstance(cre, str) or not cre.strip()):
        raise SystemExit("registry compare_root_env must be omitted or a non-empty string")
    children = data.get("managed_children")
    if not isinstance(children, list):
        raise SystemExit("registry managed_children must be a list")
    seen_pen: set[str] = set()
    for i, row in enumerate(children):
        if not isinstance(row, dict):
            raise SystemExit(f"registry managed_children[{i}] must be an object")
        raw_id = row.get("id")
        if not isinstance(raw_id, str) or not raw_id.strip():
            raise SystemExit(f"registry managed_children[{i}].id must be a non-empty string")
        cid = raw_id.strip()
        raw_penv = row.get("path_env")
        if not isinstance(raw_penv, str) or not raw_penv.strip():
            raise SystemExit(
                f"registry managed_children[{i}].path_env must be a non-empty string"
            )
        penv = raw_penv.strip()
        if penv in seen_pen:
            raise SystemExit(f"duplicate managed_children[].path_env after strip: {penv}")
        seen_pen.add(penv)
    return data


def env_path(name: str) -> str | None:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return None
    return str(raw).strip()


def git_head(path: Path) -> tuple[str | None, str | None]:
    if not path.is_dir():
        return None, "not_a_directory"
    try:
        cp = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if cp.returncode != 0:
            return None, "not_git_repo"
        out = cp.stdout.strip()
        return out or None, None
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, repr(exc)


def git_dirty_count(path: Path) -> int | None:
    if not path.is_dir():
        return None
    try:
        cp = subprocess.run(
            ["git", "-C", str(path), "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if cp.returncode != 0:
            return None
        return sum(1 for ln in cp.stdout.splitlines() if ln.strip())
    except (OSError, subprocess.TimeoutExpired):
        return None


def path_entry(tree: Path) -> dict[str, Any]:
    exists = tree.is_dir()
    head, err = git_head(tree) if exists else (None, None)
    dirty = git_dirty_count(tree) if exists else None
    row: dict[str, Any] = {
        "path": str(tree.resolve()) if exists else None,
        "exists": exists,
        "git_head_short": head,
        "dirty_files": dirty,
    }
    if exists and head is None and err:
        row["git_error"] = err
    return row


def build_family_snapshot(manager: Path, reg: dict[str, Any]) -> dict[str, Any]:
    cr_key = reg.get("compare_root_env") or "WIKI_MANAGER_COMPARE_ROOT"
    cr_raw = env_path(cr_key)
    warnings: list[str] = []
    codes: list[str] = []

    compare_path = Path(cr_raw).expanduser().resolve() if cr_raw else None

    if compare_path:
        base_block = {**path_entry(compare_path), "path_env": cr_key, "path_resolved_from_env": True}
    else:
        base_block = {
            "path": None,
            "exists": False,
            "git_head_short": None,
            "dirty_files": None,
            "path_env": cr_key,
            "path_resolved_from_env": False,
        }

    if compare_path and compare_path.resolve() == manager.resolve():
        warnings.append(
            f"warning [compare_root_is_manager]: {cr_key} points at this manager checkout."
        )
        codes.append("compare_root_is_manager")

    children_out: list[dict[str, Any]] = []
    seen_paths: dict[str, str] = {}
    for child in reg.get("managed_children", []):
        cid = str(child["id"])
        penv = str(child["path_env"])
        raw_c = env_path(penv)
        cpath = Path(raw_c).expanduser().resolve() if raw_c else None

        row: dict[str, Any] = {
            "id": cid,
            "label": str(child.get("label", cid)),
            "path_env": penv,
        }
        if cpath:
            key = str(cpath.resolve())
            if key in seen_paths:
                other = seen_paths[key]
                msg = (
                    f"warning [duplicate_child_path]: {penv} resolves to same path as child {other}."
                )
                warnings.append(msg)
                if "duplicate_child_path" not in codes:
                    codes.append("duplicate_child_path")
            seen_paths.setdefault(key, cid)
            row.update(path_entry(cpath))
            if compare_path and cpath.resolve() == compare_path.resolve():
                warnings.append(
                    f"warning [compare_root_equals_managed_child]: "
                    f"{cr_key} equals child {cid} path."
                )
                if "compare_root_equals_managed_child" not in codes:
                    codes.append("compare_root_equals_managed_child")
        else:
            row.update(
                {
                    "path": None,
                    "exists": False,
                    "git_head_short": None,
                    "dirty_files": None,
                }
            )
        children_out.append(row)

    return {
        "v": 1,
        "generated_at_utc": utc_now_iso(),
        "manager_root": str(manager.resolve()),
        "compare_root_env": cr_key,
        "llm_wiki_base_model": base_block,
        "managed_children": children_out,
        "warnings": warnings,
        "warning_codes": codes,
        "family_snapshot_warning_codes": codes,
    }


def cmd_list(manager: Path, reg: dict[str, Any]) -> None:
    cr_key = reg.get("compare_root_env") or "WIKI_MANAGER_COMPARE_ROOT"
    print(f"manager_root\t{manager.resolve()}")
    print(f"{cr_key}\t{env_path(cr_key) or '(unset)'}")
    for child in reg.get("managed_children", []):
        penv = str(child["path_env"])
        print(f"{penv}\t{env_path(penv) or '(unset)'}\t# {child['id']}")


def cmd_snapshot(manager: Path, reg: dict[str, Any], *, as_json: bool) -> None:
    snap = build_family_snapshot(manager, reg)
    if as_json:
        print(json.dumps(snap, indent=2))
        return
    print(f"# snapshot {snap['generated_at_utc']} manager={snap['manager_root']}")
    br = snap["llm_wiki_base_model"]
    print(f"base_model exists={br.get('exists')} path={br.get('path')} head={br.get('git_head_short')}")
    for ch in snap["managed_children"]:
        print(
            f"child[{ch['id']}] exists={ch.get('exists')} "
            f"head={ch.get('git_head_short')} dirty={ch.get('dirty_files')}"
        )
    for w in snap["warnings"]:
        print(w)


def _atomic_write_text(path: Path, text: str, *, encoding: str = "utf-8") -> None:
    """Write ``path`` atomically so readers never observe a partial JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
        text=True,
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as fp:
            fp.write(text)
            fp.flush()
            os.fsync(fp.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        with contextlib.suppress(OSError):
            tmp_path.unlink(missing_ok=True)
        raise


def cmd_status(
    manager: Path,
    reg: dict[str, Any],
    *,
    outfile: Path,
    stdout_json: bool,
) -> None:
    snap = build_family_snapshot(manager, reg)
    rollup = {"v": 1, "generated_at_utc": snap["generated_at_utc"], "family_snapshot": snap}
    text = json.dumps(rollup, indent=2) + "\n"

    _atomic_write_text(outfile, text)

    if stdout_json:
        sys.stdout.write(text)


def _fail_ci_smoke(msg: str) -> None:
    print(f"ci-smoke-check-stdin: {msg}", file=sys.stderr)
    raise SystemExit(1)


def ci_smoke_check_stdin() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        _fail_ci_smoke("expects JSON on stdin")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        _fail_ci_smoke(f"invalid JSON ({exc})")
    if not isinstance(data, dict):
        _fail_ci_smoke("rollup must be a JSON object")
    fs = data.get("family_snapshot")
    if not isinstance(fs, dict):
        _fail_ci_smoke("family_snapshot must be a JSON object")
    if "family_snapshot_warning_codes" not in fs:
        _fail_ci_smoke("family_snapshot.family_snapshot_warning_codes missing")
    if not isinstance(fs["family_snapshot_warning_codes"], list):
        _fail_ci_smoke("family_snapshot_warning_codes must be a list")
    wc = fs.get("warning_codes")
    if wc is None or not isinstance(wc, list):
        _fail_ci_smoke("family_snapshot.warning_codes must be a list")
    if wc != fs["family_snapshot_warning_codes"]:
        _fail_ci_smoke("warning_codes must match family_snapshot_warning_codes")

    if data.get("v") != 1:
        _fail_ci_smoke("rollup v must be 1")
    gat = data.get("generated_at_utc")
    if not isinstance(gat, str) or not gat.strip():
        _fail_ci_smoke("rollup generated_at_utc must be a non-empty string")
    if fs.get("v") != 1:
        _fail_ci_smoke("family_snapshot v must be 1")
    mr = fs.get("manager_root")
    if not isinstance(mr, str) or not mr.strip():
        _fail_ci_smoke("family_snapshot.manager_root must be a non-empty string")
    if not isinstance(fs.get("llm_wiki_base_model"), dict):
        _fail_ci_smoke("family_snapshot.llm_wiki_base_model must be a JSON object")
    if not isinstance(fs.get("managed_children"), list):
        _fail_ci_smoke("family_snapshot.managed_children must be a JSON array")
    if not isinstance(fs.get("warnings"), list):
        _fail_ci_smoke("family_snapshot.warnings must be a JSON array")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="LLM Wiki Manager coordination CLI.",
        epilog=(
            "Fork-delta and script-tree diffs run from the LLM Wiki Base Model checkout "
            "(see that repo's schema/fork-sync.md). From this manager repo: make coord-fork-delta-help"
        ),
    )
    ap.add_argument(
        "--repo-root",
        default=None,
        help="Manager checkout root (default: checkout containing this file).",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="Print resolved env paths for registry entries")

    p_snap = sub.add_parser("snapshot", help="Describe manager, compare root, and children")
    p_snap.add_argument("--json", action="store_true")

    p_st = sub.add_parser("status", help=f"Write {DEFAULT_STATUS_OUT} and optional stdout JSON")
    p_st.add_argument("--json", action="store_true", help="Echo rollup JSON after writing")
    p_st.add_argument(
        "--out",
        default=str(DEFAULT_STATUS_OUT),
        help="Output path relative to repo root unless absolute.",
    )

    sub.add_parser("ci-smoke-check-stdin", help="Verify rollup JSON on stdin has required fields")

    args = ap.parse_args()
    root = manager_root(args.repo_root)

    if args.cmd == "ci-smoke-check-stdin":
        ci_smoke_check_stdin()
        return 0

    reg = load_registry(root)
    if args.cmd == "list":
        cmd_list(root, reg)
    elif args.cmd == "snapshot":
        cmd_snapshot(root, reg, as_json=args.json)
    elif args.cmd == "status":
        out = Path(args.out)
        if not out.is_absolute():
            out = (root / out).resolve()
        cmd_status(root, reg, outfile=out, stdout_json=args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
