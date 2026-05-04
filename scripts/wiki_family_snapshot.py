#!/usr/bin/env python3
"""Machine-readable inventory of the four-repo LLM Wiki family on this host.

Resolves **LLM Wiki Manager** root, optional **WIKI_MANAGER_COMPARE_ROOT** (Base
Model), and registered child paths from **ai/schema/wiki_manager_registry.v1.json**.
For each directory that exists, records whether it is a Git checkout, short
**HEAD**, and a dirty file count (**git status --porcelain**).

See **schema/wiki-manager.md** and **wiki/synthesis/llm-wiki-family-repositories.md**.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from wiki_paths import resolve_repo_root  # noqa: E402

DEFAULT_REGISTRY_REL = "ai/schema/wiki_manager_registry.v1.json"


def _load_registry(manager_root: Path, registry_rel: str) -> dict:
    path = (manager_root / registry_rel).resolve()
    if not path.is_file():
        print(f"missing registry: {path}", file=sys.stderr)
        raise SystemExit(2)
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        print("registry root must be a JSON object", file=sys.stderr)
        raise SystemExit(2)
    return raw


def load_wiki_manager_registry(manager_root: Path, registry_rel: str = DEFAULT_REGISTRY_REL) -> dict:
    """Load **ai/schema/wiki_manager_registry.v1.json** (or a test registry path). Shared with sibling manager scripts."""
    return _load_registry(manager_root, registry_rel)


def _compare_root_env_key(registry: dict) -> str:
    k = registry.get("compare_root_env", "WIKI_MANAGER_COMPARE_ROOT")
    if not isinstance(k, str) or not k.strip():
        return "WIKI_MANAGER_COMPARE_ROOT"
    return k


def _compare_root_path(registry: dict, manager_root: Path) -> Path | None:
    env_key = _compare_root_env_key(registry)
    raw = os.environ.get(env_key, "").strip()
    if not raw:
        return None
    p = Path(raw).expanduser().resolve()
    if not p.is_dir():
        return None
    return p


def _managed_children(registry: dict) -> list[dict]:
    rows = registry.get("managed_children")
    if not isinstance(rows, list):
        return []
    out: list[dict] = []
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("id"), str) and isinstance(row.get("path_env"), str):
            out.append(row)
    return out


def _child_path(row: dict) -> Path | None:
    raw = os.environ.get(row["path_env"], "").strip()
    if not raw:
        return None
    return Path(raw).expanduser().resolve()


def _git_field(path: Path) -> dict:
    if not path.is_dir():
        return {"present": False}
    try:
        r = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {"present": True, "git": False}
    if r.returncode != 0 or r.stdout.strip() != "true":
        return {"present": True, "git": False}
    head = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    st = subprocess.run(
        ["git", "-C", str(path), "status", "--porcelain"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    dirty = 0
    if st.returncode == 0 and st.stdout.strip():
        dirty = len([ln for ln in st.stdout.splitlines() if ln.strip()])
    short = head.stdout.strip() if head.returncode == 0 else ""
    return {"present": True, "git": True, "head": short, "dirty_files": dirty}


def build_snapshot(manager_root: Path, registry: dict) -> dict:
    mr = manager_root.resolve()
    env_key = _compare_root_env_key(registry)
    base = _compare_root_path(registry, manager_root)
    rows: list[dict] = [
        {
            "role": "llm-wiki-manager",
            "label": "LLM Wiki Manager",
            "path": str(mr),
            "path_resolved": True,
            **_git_field(mr),
        }
    ]
    if base is not None:
        rows.append(
            {
                "role": "llm-wiki-base-model",
                "label": "LLM Wiki Base Model",
                "path": str(base),
                "path_env": env_key,
                "path_resolved": True,
                **_git_field(base),
            }
        )
    else:
        rows.append(
            {
                "role": "llm-wiki-base-model",
                "label": "LLM Wiki Base Model",
                "path": None,
                "path_env": env_key,
                "path_resolved": False,
                "hint": f"set {env_key} to the Base Model checkout for fork-delta left side and base-vs-manager reports",
            }
        )

    for child in _managed_children(registry):
        cid = child["id"]
        label = child.get("label", cid)
        pe = child["path_env"]
        cp = _child_path(child)
        if cp is None:
            rows.append(
                {
                    "role": "managed-child",
                    "id": cid,
                    "label": label,
                    "path": None,
                    "path_env": pe,
                    "path_resolved": False,
                }
            )
        elif not cp.is_dir():
            rows.append(
                {
                    "role": "managed-child",
                    "id": cid,
                    "label": label,
                    "path": str(cp),
                    "path_env": pe,
                    "path_resolved": False,
                    "missing": True,
                }
            )
        else:
            rows.append(
                {
                    "role": "managed-child",
                    "id": cid,
                    "label": label,
                    "path": str(cp),
                    "path_env": pe,
                    "path_resolved": True,
                    **_git_field(cp),
                }
            )

    return {"v": 1, "manager_root": str(mr), "repos": rows}


def _print_text(snapshot: dict) -> None:
    print(f"manager_root: {snapshot['manager_root']}")
    for r in snapshot["repos"]:
        role = r.get("role", "")
        label = r.get("label", r.get("id", ""))
        path = r.get("path")
        if path is None:
            env = r.get("path_env", "")
            print(f"- {label} ({role})")
            if env:
                print(f"    {env}: (unset or invalid path)")
            if "hint" in r:
                print(f"    hint: {r['hint']}")
            continue
        print(f"- {label} ({role})")
        print(f"    path: {path}")
        if r.get("missing"):
            print("    ERROR: path is not a directory")
            continue
        if not r.get("present", True):
            continue
        if not r.get("git"):
            print("    git: (not a git checkout)")
            continue
        head = r.get("head", "")
        dirty = r.get("dirty_files", 0)
        print(f"    git head: {head or '(unknown)'}  dirty_files: {dirty}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default="", help="LLM Wiki Manager checkout root.")
    ap.add_argument(
        "--registry",
        default=DEFAULT_REGISTRY_REL,
        help="Registry JSON path relative to repo root.",
    )
    ap.add_argument("--json", action="store_true", help="Emit one JSON object on stdout.")
    args = ap.parse_args()
    manager_root = resolve_repo_root(args.repo_root)
    registry = load_wiki_manager_registry(manager_root, args.registry)
    snap = build_snapshot(manager_root, registry)
    if args.json:
        print(json.dumps(snap, ensure_ascii=False, indent=2))
    else:
        _print_text(snap)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
