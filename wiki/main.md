---
type: synthesis
title: Wiki home
updated: 2026-05-04
lang_primary: en
---

# Wiki home

**LLM Wiki Manager** uses this **`wiki/`** tree as **machine-first LLM context** for the **four related repositories** (Manager, **LLM Wiki Base Model**, **Shaolin Monastery Research System**, **Tai-Pan Wiki**). **Human reader polish is out of scope.** Default paths and env wiring live in [[synthesis/llm-wiki-family-repositories]]. Coordination **`make`** targets (**`make wiki-manager-refresh-dry`**, **`make wiki-manager-fork-delta-from-base`**, **`make wiki-manager-sync-status`**, **`schema/wiki-manager.md`**) only print inventories, fork-delta bundles, and the **`sync_status.min.json`** rollup. **README.md** documents **GitHub Actions** **`wiki_manager_sync_status.py`** smoke after **`make wiki-test`**. That smoke requires **`family_snapshot_warning_codes`** in the JSON. They do **not** merge **`wiki/`** prose into sibling repos. Policies and machine contracts still live under **`schema/`**. Forks add domain evidence under **`normalized/`** and their own narrative **`wiki/`** outside this checkout.

## See also

- See also [[synthesis/llm-wiki-family-repositories]] (paths, roles, **`WIKI_MANAGER_*`** wiring for all four checkouts)
- See also **`schema/wiki-manager.md`** (**`make wiki-manager-*`**, registry **`ai/schema/wiki_manager_registry.v1.json`**)
- See also [[entities/example-entity]] (minimal example encyclopedia-style page)
- See also [[synthesis/sources]] (alphabetical index of all source pages under `wiki/sources/`)
- See also [[synthesis/activity-log]] (optional chronological log paired with compiler output under **`index/`**. **`make wiki-log-tail`** prints recent gist-style dated headings from the shell)
- See also [[disputes/example-dispute-stub]] (illustrative dispute layout and citation pattern)
- See also **`schema/karpathy-llm-wiki-bridge.md`** maps the Karpathy LLM Wiki gist to **`make`** targets and **`ai/runtime/`**
- See also maintainer orientation in **`schema/wiki-quickstart.md`** at the repository root
- See also [[synthesis/disclaimer-and-license]] (reader-facing waiver and licence posture for this scaffold)
