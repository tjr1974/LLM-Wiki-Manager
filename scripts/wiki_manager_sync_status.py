#!/usr/bin/env python3
"""Roll up family Git snapshot plus optional fork-delta report metrics.

Writes **ai/runtime/manager/sync_status.min.json** (gitignored) so agents and
dashboards can read one file after **make wiki-manager-report** or
**make wiki-manager-fork-delta-full**. Does **not** run diffs itself.

See **schema/wiki-manager.md** (**make wiki-manager-sync-status**).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from wiki_family_snapshot import build_snapshot, load_wiki_manager_registry  # noqa: E402
from wiki_paths import resolve_repo_root, utc_now_iso  # noqa: E402

DEFAULT_OUT_REL = "ai/runtime/manager/sync_status.min.json"
DEFAULT_REGISTRY_REL = "ai/schema/wiki_manager_registry.v1.json"


def _digest_fork_delta_report(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"error": "invalid_json", "path": str(path)}
    if not isinstance(data, dict):
        return {"error": "not_object", "path": str(path)}
    hp = data.get("high_priority_upstream_paths") or []
    cand = data.get("candidate_upstream_paths") or []
    rq = data.get("review_queue") or []
    if not isinstance(hp, list):
        hp = []
    if not isinstance(cand, list):
        cand = []
    if not isinstance(rq, list):
        rq = []
    return {
        "path": str(path),
        "high_priority_upstream_paths": len(hp),
        "candidate_upstream_paths": len(cand),
        "review_queue": len(rq),
    }


def _digest_fork_delta_summary(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"error": "invalid_json", "path": str(path)}
    if not isinstance(data, dict):
        return {"error": "not_object", "path": str(path)}
    rec = data.get("recommendation")
    if isinstance(rec, str):
        return {"path": str(path), "recommendation": rec}
    return {"path": str(path)}


def build_sync_status(manager_root: Path, registry_rel: str) -> dict:
    registry = load_wiki_manager_registry(manager_root, registry_rel)
    snap = build_snapshot(manager_root, registry)
    mr = manager_root.resolve()
    warnings: list[str] = []

    base_path: str | None = None
    for r in snap.get("repos", []):
        if r.get("role") == "llm-wiki-base-model" and r.get("path_resolved") and r.get("path"):
            base_path = str(r["path"])
            break

    if base_path is None:
        drift_mode = "manager-vs-child"
        warnings.append(
            "WIKI_MANAGER_COMPARE_ROOT unset or invalid: fork-delta left side defaults to this "
            "manager checkout (not LLM Wiki Base Model). Export compare root before measuring "
            "parent-to-child tooling drift."
        )
    elif Path(base_path).resolve() == mr.resolve():
        drift_mode = "manager-vs-child"
        warnings.append("compare_root resolves to manager_root; same as unset for fork-delta purposes.")
    else:
        drift_mode = "base-model-vs-child"

    children: list[dict] = []
    for r in snap.get("repos", []):
        if r.get("role") != "managed-child":
            continue
        cid = r.get("id", "")
        prefix = manager_root / "ai/runtime/manager" / cid
        report = prefix / "fork_delta_report.min.json"
        summary = prefix / "fork_delta_summary.min.json"
        row: dict = {
            "id": cid,
            "label": r.get("label", cid),
            "path_env": r.get("path_env", ""),
            "path_resolved": bool(r.get("path_resolved")),
            "path": r.get("path"),
            "fork_delta_report": _digest_fork_delta_report(report),
            "fork_delta_summary": _digest_fork_delta_summary(summary),
        }
        children.append(row)

    return {
        "v": 1,
        "generated_at": utc_now_iso(),
        "drift_compare_mode": drift_mode,
        "drift_warnings": warnings,
        "family_snapshot": snap,
        "managed_children": children,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default="", help="LLM Wiki Manager checkout root.")
    ap.add_argument(
        "--registry",
        default=DEFAULT_REGISTRY_REL,
        help="Registry JSON path relative to repo root.",
    )
    ap.add_argument(
        "--out",
        default=DEFAULT_OUT_REL,
        help="Output path relative to repo root (default: ai/runtime/manager/sync_status.min.json).",
    )
    ap.add_argument("--json", action="store_true", help="Print JSON to stdout (still writes --out).")
    args = ap.parse_args()
    manager_root = resolve_repo_root(args.repo_root)
    payload = build_sync_status(manager_root, args.registry)
    out_path = (manager_root / str(args.out).strip()).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"wrote {out_path}")
        print(f"drift_compare_mode: {payload['drift_compare_mode']}")
        for w in payload["drift_warnings"]:
            print(f"warning: {w}")
        for ch in payload["managed_children"]:
            rid = ch.get("id", "")
            rep = ch.get("fork_delta_report")
            if rep is None:
                print(f"- {rid}: (no fork_delta_report yet; run make wiki-manager-report)")
            elif "error" in rep:
                print(f"- {rid}: report {rep.get('error')}")
            else:
                hp = rep.get("high_priority_upstream_paths", 0)
                print(f"- {rid}: high_priority_upstream_paths={hp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
