# Agent hints

Single entrypoint **`scripts/wiki_coord.py`**: **`list`**, **`snapshot`** (`--json`), **`status`** (**`runtime/sync_status.min.json`**, `--json`), **`ci-smoke-check-stdin`** (stderr + exit **1** on bad JSON/shape / **`warning_codes`** mismatch vs **`family_snapshot_warning_codes`**).

Register children in **`schema/wiki_family_registry.v1.json`** and mirror **`path_env`** in **`.env.example`**. **`load_registry`** rejects malformed JSON (**`invalid registry JSON`**), **`managed_children`** that are **not** a **`list`**, malformed sibling rows (**not** objects, empty **`id`** or **`path_env`**, or duplicate **`path_env`** identifiers), and bogus **`compare_root_env`**. **`wiki_coord`** rejects **`--repo-root`** directories that **do not exist**. **`schema/wiki-manager.md`** defines **`warning_codes`**, rollup shape, **`coord-*`**. **`make coord-ci-smoke`** snapshots **`status`** JSON via **tempfile** (POSIX **`make`** / **`sh`** without **`pipefail`** otherwise masks LHS failures); CI runs **`make test`** then **`make coord-ci-smoke`**.

Do not rely on **`runtime/`** in prompts; regenerate with **`make coord-status`** locally.

**Lineage vs practice:** **LLM Wiki Base Model** is the **conceptual parent** and default **compare-root**; **Shaolin Monastery Research System** is often where **implementation is proven first**. Neutral improvements are then **backported** into Base Model (and/or **Manager** for coordination-only changes). **`schema/wiki-manager.md`** spells this out for assistants. **Fork-delta** and optional **child path layout** JSON (**`CHILD_PATH_OVERRIDES`**, **`wiki_manager_registry`**) are documented and run from the **Base Model** checkout — see that repo’s **`schema/fork-sync.md`** and **`schema/wiki-manager.md`**.
