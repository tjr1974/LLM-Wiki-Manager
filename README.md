# LLM Wiki Manager

Coordinator for the **LLM Wiki** family:

- **`LLM Wiki Base Model`** — topic-neutral scaffold (upstream template / lineage reference; default **compare-root** for fork-delta and coordination).
- **Domain repos** registered in **`schema/wiki_family_registry.v1.json`** (for example **Shaolin Monastery Research System**, **Tai-Pan Wiki**, and additional children later).

Exports machine-readable **snapshots** of “what is checked out where and at which revision” across those trees. Outputs under **`runtime/`** are gitignored because they mirror your local paths.

### Lineage versus day-to-day workflow (assistants and maintainers)

**Conceptually and in git history,** **LLM Wiki Base Model** is the **parent** of domain children such as **Shaolin Monastery Research System** (neutral template → fork).

**In day-to-day practice for this family,** **Shaolin Monastery Research System** is often where **active implementation** happens first (new validators, export behavior, dashboards, corpus-scale lessons). **Deriving** or **refreshing** **LLM Wiki Base Model** then means **cherry-picking or porting the topic-neutral subset** (scripts, tests, schema, CI, shared policies) back into the parent so it stays domain-neutral — not an automatic mirror and not “only edit Base Model in isolation.” **LLM Wiki Manager** does not merge trees; it makes **paths, HEADs, and warnings** visible so that backport work stays intentional. See **`schema/wiki-manager.md`** (**Lineage and derivation**) and **LLM Wiki Base Model** **`schema/fork-sync.md`** (**`## Human-facing wiki backlog (Shaolin Monastery Research System → this base)`** for **`CHILD_PATH_OVERRIDES`**, **`make fork-delta-scan`**, and **Suggested port phases** **0–4**) plus **`schema/human-wiki-universal-backlog.md`** (tabular checklist of what should be universal on the human wiki surface). **`make coord-fork-delta-help`** prints the **`fork-delta-full`** one-liner and a lighter **Phase 0** reminder.

**Runtime:** Python **≥ 3.10**. GitHub Actions pins **3.12** (**`.github/workflows/ci.yml`**).

## Quickstart

Install test deps:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Point at your clones (examples):

```bash
export WIKI_MANAGER_COMPARE_ROOT="/absolute/path/to/LLM Wiki Base Model"
export WIKI_MANAGER_CHILD_SHAOLIN="/absolute/path/to/Shaolin Monastery Research System"
make coord-list
make coord-snapshot-json
```

Write the rollup artifact:

```bash
make coord-status
# → runtime/sync_status.min.json
```

Documentation: **`schema/wiki-manager.md`**. Environment template: **`.env.example`**. Human-wiki backport diff recipe (run from Base Model): **`make coord-fork-delta-help`**.

### Fork-delta and child directory layout (run from Base Model)

**`wiki_coord`** in this repo does **not** diff `scripts/` trees. To compare **LLM Wiki Base Model** to a child whose layout differs (for example **Shaolin** with **`platform/scripts/`** instead of **`scripts/`**), use the **Base Model** checkout: **`make fork-delta`** or **`make fork-delta-full`**, optional **`CHILD_PATH_OVERRIDES=`** (see that repo’s **`schema/fork-sync.md`** and **`ai/schema/fork_delta_child_path_overrides.shaolin-monastery-research-system.v1.json`**), or **`make wiki-manager-report`** / **`wiki_manager_fork_delta.py`** with **`ai/schema/wiki_manager_registry.v1.json`** there. Copy-paste **`WIKI_MANAGER_*`** env commands for backlog + verify live under **`schema/wiki-manager.md`** (**Human-facing wiki universalization**). This Manager repo documents the split under **`schema/wiki-manager.md`** (**Fork-delta and child directory layout**).

### Troubleshooting

Early **`SystemExit`** messages from **`wiki_coord`** usually narrow the fix: **`missing registry`** (wrong **`--repo-root`** or deleted **`schema/wiki_family_registry.v1.json`**), **`registry v must be 1`**, **`invalid registry JSON`**, **`managed_children`** row shape (**`must be an object`** / **`must be a list`**), **`id must be a non-empty string`** / **`path_env must be a non-empty string`** (including JSON **`null`** or non-string types), **`duplicate managed_children[].path_env`**, bad **`compare_root_env`**, or **`--repo-root is not an existing directory`** (typo/absent checkout path).

### What this repo does *not* do

- No encyclopedia authoring surface, **`wiki/`** corpus compilation, ingest pipeline, or static human-site export.
- No **`fork_delta_report.py`**, **`make fork-delta*`**, or **`wiki_manager_fork_delta.py`** in this checkout — run those from **LLM Wiki Base Model**; **`make coord-fork-delta-help`** here only prints a suggested **`fork-delta-full`** shell line (see **`schema/wiki-manager.md`**).
- No **`make wiki-manager-fork-delta-full`** / per-child **`ai/runtime/manager/<id>/`** fork-delta bundles — those **`Makefile`** targets and **`scripts/wiki_manager_fork_delta.py`** live in **LLM Wiki Base Model** (see that repo’s **`schema/wiki-manager.md`**). Here, names like **`make wiki-manager-list`** are **aliases** for **`coord-list`** / snapshots only.
- No unattended merges into sibling checkouts — only snapshots and tooling that make misconfiguration visible.

Those belong in **`LLM Wiki Base Model`** and each registered domain child.

### CI parity

On every push / PR GitHub Actions runs **`make test`** then **`make coord-ci-smoke`** — **`coord-ci-smoke`** captures **`status --json`** stdout to a tempfile, then **`ci-smoke-check-stdin`** verifies shape (**rollup JSON; **`family_snapshot.warning_codes`** matches **`family_snapshot_warning_codes`**), so **`status`** failures propagate under POSIX **`make`**. Wiki build / corpus gates live in Base Model / child repos, not here.
