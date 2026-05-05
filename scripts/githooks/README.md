# Optional Git hooks

These hooks are **not** enabled by default. Install once per clone when you want local verification before **`git push`** instead of relying on memory or long pasted LLM preambles.

## Install

From the repository root:

```bash
git config core.hooksPath scripts/githooks
```

**Line endings.** The extensionless **`pre-push`** file is stored with **LF** endings (**`.gitattributes`**, **`scripts/githooks/pre-push text eol=lf`**) so the **`#!/bin/sh`** shebang stays reliable after checkout on all platforms.

To use the default hooks path again:

```bash
git config --unset core.hooksPath
```

## `pre-push`

Runs **`make`** gates before the push proceeds. Control behavior with **`WIKI_PRE_PUSH`**:

| Value | Behavior |
|-------|----------|
| **`off`**, **`0`**, **`skip`** | No-op (exit 0). |
| **`check`** (default) | **`make wiki-check`** — Markdown-focused gates after **`wiki-compile`**. |
| **`ci`** | **`make wiki-ci`** then **`make wiki-quality-gate`** — matches the wiki leg of **`.github/workflows/ci.yml`** after **`wiki-test`**. |
| **`all`** | **`make wiki-all`** — **`wiki-test`** (pytest + restore **`ai/runtime/`**) then **`wiki-ci`** then **`wiki-quality-gate`** then **`wiki-restore-runtime`** again (local clean tree; Actions keeps step outputs). |

Examples:

```bash
WIKI_PRE_PUSH=all git push
WIKI_PRE_PUSH=off git push
```

**Note.** Hooks run in your shell environment. If forks use **`VALIDATE_WIKI_ARGS`**, export it before **`git push`** when you need the same **`validate_wiki.py`** flags as local **`make`**.

**`make wiki-test` invocation.** **`WIKI_PRE_PUSH=all`** runs **`make wiki-all`**, which chains **`make wiki-test`**. Do not use **`make wiki-test -q`** (**`-q`** is not a **`pytest`** flag there. It becomes a stray **`make`** goal). Run **`pytest -q`** inside your venv instead (**README.md** Pre-push and **Assistant preamble → repo mechanics** table, **`proposed/README.md`**, **`schema/wiki-quickstart.md`** **Pytest and CI**, **`schema/karpathy-llm-wiki-bridge.md`** **Pytest leg**, **`schema/AGENTS.md`** githooks bullet, **`Makefile`** top comments, **`make help`**, **`tests/test_githooks_wiring.py`**, **`tests/test_pipeline_step_order.py`**, **`tests/conftest.py`**, **`tests/test_makeflags_inheritance.py`**, **`tests/test_make_wiki_all_recipe.py`**, **`tests/test_karpathy_bridge_docs.py`**). Tests that spawn Python via **`subprocess.run`** with **`cwd`** outside the checkout should pass **`tests/_resolved_python.py`** **`RESOLVED_PYTHON`** when **`sys.executable`** might be relative (**`schema/AGENTS.md`** **Pytest subprocess hygiene**, **`tests/test_build_hub_links.py`**, plus the note in that section that **`tests/conftest.py`** and **`tests/_resolved_python.py`** module docstrings cross-link **`MAKEFLAGS`** and **`RESOLVED_PYTHON`**).

## Multi-repo coordination (optional, not in the hook)

**LLM Wiki Manager** can register sibling checkouts via **`WIKI_MANAGER_*`** env vars (**`schema/wiki-manager.md`**). Registry **`compare_root_env`** names the Base Model path env when it differs from the default **`WIKI_MANAGER_COMPARE_ROOT`**. Run **`make wiki-manager-refresh-dry`**, **`make wiki-manager-snapshot`**, or **`make wiki-manager-sync-status`** manually when you want path inventory, a **`sync_status.min.json`** rollup (**`family_snapshot_warning_codes`** surfaces compare-root structural issues), or dry-run fork-delta steps before a push. Those targets do **not** run inside **`pre-push`** by default.
