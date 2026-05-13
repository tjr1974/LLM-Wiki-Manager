# LLM Wiki Manager (coordination)

This repository owns **registration and snapshots** so you can keep **LLM Wiki Base Model** (neutral parent scaffold) aligned with domain children (paths live in **`schema/wiki_family_registry.v1.json`**) during manual cherry-picks and reviews.

This is **not** an unattended merge robot. Domain narrative stays in each child checkout.

## Lineage and derivation (for LLM coding assistants)

- **Lineage (theory / git):** **LLM Wiki Base Model** is the **parent template**; repos like **Shaolin Monastery Research System** are **domain children** forked from that idea. The parent must stay **topic-neutral** in bundled examples and shared contracts.
- **Practice (where work often lands first):** **Shaolin Monastery Research System** is frequently the **live laboratory** — new tooling, gates, and operational patterns are proven there against a real corpus and layout (`knowledge/wiki/`, `platform/scripts/`, `state/ai/`, and so on). **Refreshing Base Model** means **extracting domain-neutral changes** from the child (or from **LLM Wiki Manager** when shared tooling lives there) via **reviewed cherry-picks**, not wholesale merges or a one-way assumption that “all development starts in Base Model.”
- **This coordinator’s role:** **`wiki_coord`** only records **resolved paths**, **git HEAD**, **dirty counts**, and **warning codes** across the registered trees. It helps humans and assistants **not** confuse “compare-root path” with “the only place edits are allowed.”

## Registry

Machine list: **`schema/wiki_family_registry.v1.json`** (`managed_children[].id`, `label`, `path_env`). Each **`id`** / **`path_env`** must be a **JSON string** and **non-empty** after whitespace trim (otherwise **`must be a non-empty string`**). JSON **`null`**, numbers, or objects for those keys are rejected the same way. Each **`path_env`** names an environment variable whose value must be an **absolute path** to that checkout when set.

Top-level **`v`** must equal **`1`**. Wrong version fails with **`registry v must be 1`** (**non-zero** exit). If **`--repo-root`** is wrong or the file is absent, **`load_registry`** exits with **`missing registry:`** `<path>`.

**`managed_children[]` rows cannot reuse the same `path_env` name:** after trimming, duplicates fail with **`duplicate managed_children[].path_env`** — each child binds a distinct environment variable.

Malformed registry JSON fails fast with **`SystemExit`** and message **`invalid registry JSON (`…`)`** (**non-zero** exit) before **`list`** / **`snapshot`** / **`status`** run.

If JSON field **`compare_root_env`** is present, it **must be a non-empty string** naming the **`WIKI_MANAGER_*`** environment variable for the compare-root (**Base Model**) checkout path. Omit **`compare_root_env`** to rely on **`WIKI_MANAGER_COMPARE_ROOT`** (**code default**; the bundled registry manifests it explicitly today).

## Commands

| Make target | Meaning |
|-------------|---------|
| **`make coord-list`** | Resolved manager root, compare root env, child env vars. |
| **`make coord-snapshot`** | Git **HEAD** and dirty file counts where paths exist and are git repos. |
| **`make coord-snapshot-json`** | Same as JSON on stdout. |
| **`make coord-status`** | Writes **`runtime/sync_status.min.json`** with a **`family_snapshot`** object (**gitignored**, may embed paths). The file is replaced **atomically** (temp file in the same directory then **`os.replace`**) so concurrent readers never see a truncated JSON object. |
| **`make coord-status-json`** | Status file plus rollup JSON echoed to stdout. |
| **`make coord-ci-smoke`** | Temp rollup from **`wiki_coord`** **`status --json`** into a tempfile, then **`wiki_coord`** **`ci-smoke-check-stdin`** reads it (POSIX **`make` / **`sh`** without **`pipefail`** hides left-hand **`status`** failures when using only a **`|`** pipe — this recipe does **not** do that). **`ci.yml`**: **`make test`** then **`make coord-ci-smoke`**; mirror locally. |
| **`make coord-fork-delta-help`** | Prints the **Base Model** **`make fork-delta-full`** shell line ( **`WIKI_MANAGER_COMPARE_ROOT`**, **`CHILD_PATH_OVERRIDES`**, **`WIKI_MANAGER_CHILD_*`** ) plus a **Phase 0** (**`fork-delta`** + **`fork-delta-scan`**) pointer. Does **not** run fork-delta from this repo. |

Direct Python (**`--repo-root`** must resolve to an **existing manager checkout directory**):

```bash
python3 scripts/wiki_coord.py --repo-root /abs/path/to/manager-checkout list
python3 scripts/wiki_coord.py list
python3 scripts/wiki_coord.py snapshot --json
python3 scripts/wiki_coord.py status --json --out runtime/sync_status.min.json
```

## Warnings (`warning_codes`)

- **`compare_root_is_manager`** — The configured compare-root env (registry field `compare_root_env`, default **`WIKI_MANAGER_COMPARE_ROOT`**) resolves to **this** manager checkout.
- **`compare_root_equals_managed_child`** — The compare-root path resolves to the same directory as a registered child (**misconfiguration for fork-delta style comparisons).
- **`duplicate_child_path`** — Two **`path_env`** values resolve to the same directory.

The snapshot includes **`family_snapshot_warning_codes`** (same codes as **`warning_codes`**) for shallow JSON consumers such as **`ci-smoke-check-stdin`**.

## Fork-delta and child directory layout (Base Model checkout)

**This coordinator does not run** **`fork_delta_report.py`** or **LLM Wiki Base Model**'s **`wiki_manager_fork_delta.py`** / **`make fork-delta*`** / **`make wiki-manager-report`** / **`make wiki-manager-fork-delta-full`**; see that repo's **`schema/wiki-manager.md`**, **`schema/fork-sync.md`**, and **`Makefile`**. Use **`make coord-fork-delta-help`** here only to print the suggested **`fork-delta-full`** shell line.

When you compare **Base Model** (`scripts/`, `human/`, …) to a child that uses a different top-level layout (for example **Shaolin** with **`platform/scripts/`** and **`web/human/`**), run fork-delta **from the Base Model tree** (or any checkout that vendors the same scripts) and use:

- **`make fork-delta … CHILD_PATH_OVERRIDES=…`** — points at JSON mapping subsystem roots (see **`ai/schema/fork_delta_child_path_overrides.shaolin-monastery-research-system.v1.json`** in Base Model), or
- **`wiki_manager_fork_delta.py`** with **`ai/schema/wiki_manager_registry.v1.json`** — optional per-child **`fork_delta_child_path_overrides_rel`** so **`make wiki-manager-report`** passes the same JSON automatically for registered children.

**`wiki_coord`** snapshots here do not read those JSON files; they only record **`path_env`** paths and git state.

### Human-facing wiki universalization (operator recipe)

Use this when you want a **machine-backed backlog** of what to port from a mature child (for example **Shaolin Monastery Research System**) into **LLM Wiki Base Model**—category hubs, bake/clone/verbatim stacks, exposure validators, baked-shell **`page-*`** alignment (**`validate_wiki_site_page_class.py`**, **`make wiki-site-page-class`**, ordered before **`wiki-wiki-rel`** inside **`make wiki-static-export-check`**), and related tests. The compare work always runs **from the Base Model checkout**, not from this Manager repo.

1. Export paths (same variables as **`.env.example`** / **`make coord-list`**): **`WIKI_MANAGER_COMPARE_ROOT`**, and the **`path_env`** for the child you compare (for example **`WIKI_MANAGER_CHILD_SHAOLIN`**). **`CHILD_PATH_OVERRIDES`** is required when the child’s layout skews from Base Model (**`platform/scripts`** vs **`scripts`**, and so on); the bundled Shaolin map is **`ai/schema/fork_delta_child_path_overrides.shaolin-monastery-research-system.v1.json`**. A child whose tree already matches Base Model can omit **`CHILD_PATH_OVERRIDES=`** on **`make fork-delta-full`**.
2. From **`$WIKI_MANAGER_COMPARE_ROOT`** — use **`make fork-delta-full`** so **`fork_delta_summary.min.json`**, portability audit, next-batch, **`fork-delta-verify`**, and **`fork-delta-status`** all have their inputs (**`fork-delta-status`** alone will fail without the summary artifact):

```bash
cd "$WIKI_MANAGER_COMPARE_ROOT"
OV="$WIKI_MANAGER_COMPARE_ROOT/ai/schema/fork_delta_child_path_overrides.shaolin-monastery-research-system.v1.json"
make fork-delta-full CHILD="$WIKI_MANAGER_CHILD_SHAOLIN" CHILD_PATH_OVERRIDES="$OV"
```

Writes gitignored artifacts under **`ai/runtime/`**, including **`fork_delta_backlog.md`**, **`fork_delta_shortlist.min.json`**, **`fork_delta_summary.min.json`**, and **`fork_delta_next_batch.min.json`**. From **this** coordinator checkout you can print the same shell line without opening the doc: **`make coord-fork-delta-help`**.

3. Lighter path (**report + scan + backlog only**, no **`fork-delta-status`** / **`fork-delta-verify`**): **`make fork-delta`** with **`CHILD_PATH_OVERRIDES=`** when the child layout skews, then **`make fork-delta-scan`** with the same **`CHILD=`** (scan does not take overrides; it reads the report from **`fork-delta`**). Then **`make fork-delta-remediation`** and **`make fork-delta-backlog`** (same **`CHILD=`** where the **`Makefile`** requires it). Do not run **`make fork-delta-status`** until **`fork_delta_summary.min.json`** exists (normally via **`make fork-delta-full`** or **`python3 scripts/fork_delta_summary.py`** after portability audit — see Base Model **`Makefile`** **`fork-delta-full`** ordering).

4. **Phase 0 triage:** read **`ai/runtime/fork_delta_report.min.json`** (**`counts`**) and **`ai/runtime/fork_delta_scan.min.json`** next to **`schema/human-wiki-universal-backlog.md`** (**Fork-delta triage**). Then read **`schema/fork-sync.md`** (**Human-facing wiki backlog** and **Suggested port phases** **0–4**) and the backlog table next to **`ai/runtime/fork_delta_shortlist.min.json`** (**`safe_paths`**) and **`fork_delta_backlog.md`** when you ran the full remediation chain.

Counts in those JSON files change whenever either tree changes; they are **not** stored by **`wiki_coord`**.

## Rollup JSON shape (`status`)

Top-level rollup object (**`scripts/wiki_coord.py status`**, default **`runtime/sync_status.min.json`**):

- **`v`**: **`1`**.
- **`generated_at_utc`**: RFC 3339 UTC (second precision).
- **`family_snapshot`**: object described below (**this is what `ci-smoke-check-stdin` inspects).

**`family_snapshot`** required fields:

- **`v`**: **`1`**.
- **`generated_at_utc`** (mirrors rollup).
- **`manager_root`**: absolute path string to this coordinator checkout.
- **`compare_root_env`**: string name of the compare-root **`path_env`** (from registry field **`compare_root_env`**, default **`WIKI_MANAGER_COMPARE_ROOT`**) naming **LLM Wiki Base Model**.
- **`llm_wiki_base_model`**: compare-root resolution block (`path`, `exists`, `git_head_short`, `dirty_files`, optional `git_error`; `path_env`; `path_resolved_from_env` boolean).
- **`managed_children`**: array — each `{ id, label, path_env, path?, exists, git_head_short?, dirty_files?, git_error? }` per registry row.
- **`warnings`**: array of human-readable warning strings when misconfigured paths collide or duplicate.
- **`warning_codes`** and **`family_snapshot_warning_codes`**: duplicate lists (**same ordering and contents** — each distinct issue code appears at most once per snapshot). **`ci-smoke-check-stdin`** validates the **rollup** envelope (**`v`**, **`generated_at_utc`**, and **`family_snapshot`** typed fields including **`manager_root`**, **`llm_wiki_base_model`**, **`managed_children`**, **`warnings`**) then rejects a missing / wrongly typed **`family_snapshot`** (needs a JSON **object**), rejects missing / non-list **`family_snapshot_warning_codes`**, rejects non-list **`warning_codes`**, and rejects lists that **differ** from each other (**exit non-zero**, message on **`stderr`**).

## Tests

Regression coverage lives under **`tests/test_wiki_coord.py`** (including **`make coord-ci-smoke`** and **`make coord-fork-delta-help`** guards when **`make`** is on **`PATH`**).

Fork-delta, **`CHILD_PATH_OVERRIDES`**, and **`wiki_manager_fork_delta`** registry wiring are tested in **LLM Wiki Base Model** (**`tests/test_fork_delta_*.py`**, **`tests/test_wiki_manager_fork_delta.py`**).
