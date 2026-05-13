# LLM Wiki Manager (coordination)

This repository owns **registration and snapshots** so you can keep **LLM Wiki Base Model** (neutral parent scaffold) aligned with domain children (paths live in **`schema/wiki_family_registry.v1.json`**) during manual cherry-picks and reviews.

This is **not** an unattended merge robot. Domain narrative stays in each child checkout.

## Lineage and derivation (for LLM coding assistants)

- **Lineage (theory / git):** **LLM Wiki Base Model** is the **parent template**; repos like **Shaolin Monastery Research System** are **domain children** forked from that idea. The parent must stay **topic-neutral** in bundled examples and shared contracts.
- **Practice (where work often lands first):** **Shaolin Monastery Research System** is frequently the **live laboratory** — new tooling, gates, and operational patterns are proven there against a real corpus and layout (`knowledge/wiki/`, `platform/scripts/`, `state/ai/`, and so on). **Refreshing Base Model** means **extracting domain-neutral changes** from the child (or from **LLM Wiki Manager** when shared tooling lives there) via **reviewed cherry-picks**, not wholesale merges or a one-way assumption that “all development starts in Base Model.”
- **This coordinator’s role:** **`wiki_coord`** only records **resolved paths**, **git HEAD**, **dirty counts**, and **warning codes** across the registered trees. It helps humans and assistants **not** confuse “compare-root path” with “the only place edits are allowed.”

## Registry

Machine list: **`schema/wiki_family_registry.v1.json`** (`managed_children[].id`, `label`, `path_env`). Each **`id`** / **`path_env`** must be a **non-empty string** after whitespace trim. Each **`path_env`** names an environment variable whose value must be an **absolute path** to that checkout when set.

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

**This coordinator does not run** **`fork_delta_report.py`**, **`make fork-delta`**, or **`make wiki-manager-*`**. Those live in **LLM Wiki Base Model** (see that repo’s **`schema/wiki-manager.md`**, **`schema/fork-sync.md`**, and **`Makefile`**).

When you compare **Base Model** (`scripts/`, `human/`, …) to a child that uses a different top-level layout (for example **Shaolin** with **`platform/scripts/`** and **`web/human/`**), run fork-delta **from the Base Model tree** (or any checkout that vendors the same scripts) and use:

- **`make fork-delta … CHILD_PATH_OVERRIDES=…`** — points at JSON mapping subsystem roots (see **`ai/schema/fork_delta_child_path_overrides.shaolin-monastery-research-system.v1.json`** in Base Model), or
- **`wiki_manager_fork_delta.py`** with **`ai/schema/wiki_manager_registry.v1.json`** — optional per-child **`fork_delta_child_path_overrides_rel`** so **`make wiki-manager-report`** passes the same JSON automatically for registered children.

**`wiki_coord`** snapshots here do not read those JSON files; they only record **`path_env`** paths and git state.

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

Regression coverage lives under **`tests/test_wiki_coord.py`**.

Fork-delta, **`CHILD_PATH_OVERRIDES`**, and **`wiki_manager_fork_delta`** registry wiring are tested in **LLM Wiki Base Model** (**`tests/test_fork_delta_*.py`**, **`tests/test_wiki_manager_fork_delta.py`**).
