# LLM Wiki Manager coordination

This checkout is **LLM Wiki Manager**: a coordination layer on the same Karpathy-style wiki toolchain as **LLM Wiki Base Model**, with explicit registration of domain child wikis and repeatable **fork-delta** bundles per child.

## Machine-first repository (LLM Wiki Manager)

- **No human-facing wiki requirement.** Nothing in **`wiki/`** is obligated to read like a public encyclopedia for people. Optional **`wiki/`** pages exist to give **LLMs and agents** a **dense** map of the four related checkouts and how gates run.
- **Optimize for LLM use.** Prefer **tables**, **short bullets**, **stable `##` anchors**, and **cross-refs** over narrative padding. **Lower token count** beats polite exposition. Repeat facts only when it reduces ambiguity for automation.
- **Gates are not reader polish.** **`validate_human_text.py`** on **`MD_GLOBS`** paths keeps **ASCII-safe** predictable Markdown for **parsers and CI**. That is **machine-parseable hygiene**, not a goal of human readability on **Manager**.
- **Narrow wiki typography.** **`MD_GLOBS`** in **`scripts/validate_human_text.py`** includes **`wiki/main.md`**, **`wiki/_templates/`**, **`wiki/sources/`**, and **`wiki/synthesis/`** only. Stub subtrees such as **`wiki/entities/`** stay out of that pass so **LLM** pages are not forced through reader-centric typography gates. **`validate_wiki.py`** still validates narrative fixtures when you run **`wiki-check`**.

## Canonical development hub

- **Default development root.** Treat **this repository** as the **canonical checkout for ongoing shared work** across the family: **`scripts/`**, **`tests/`**, **`Makefile`**, **`.github/workflows/`**, topic-neutral **`schema/`** Markdown, **`ai/schema/`** JSON policies, **`.cursor/rules/`**, and coordination prose on **this** page. Implement new automation, CI gates, and cross-repo contracts **here first**.
- **LLM Wiki Base Model** remains the **neutral sibling template** used as the diff left side when you export the Base Model checkout path (registry **`compare_root_env`**, default **`WIKI_MANAGER_COMPARE_ROOT`**) or run **`make fork-delta … COMPARE=`**. It should receive **cherry-picked** or otherwise reviewed **backports** of **domain-neutral** tooling and policy deltas from **Manager** on whatever cadence your maintainers define. It is **not** an automatic mirror of **Manager**.
- **Domain children** (for example paths in **`ai/schema/wiki_manager_registry.v1.json`**) keep **domain-specific** **`wiki/`** narrative local. They align shared files through **subsystem diffs** and **cherry-picks** per **`schema/fork-sync.md`**, not by merging whole child trees into **Manager**.
- **Lineage versus role.** **Manager** may have been created **after** **Base Model** and still hosts a **`wiki/`** tree. That history does **not** change the **role** above: **Manager** owns integration and shared development. **Base Model** stays the neutral **reference** checkout for compare-root workflows.
- **Operator wiki.** **`wiki/`** under **LLM Wiki Manager** is **machine-first** documentation for **all four** related checkouts (paths, env vars, governance). Canonical page: **`wiki/synthesis/llm-wiki-family-repositories.md`**. That scope is **intentional** and is **not** the same as the **domain-neutral human reader** **`wiki/`** posture expected on **LLM Wiki Base Model** when it acts as the neutral parent template for domain-only child narrative.

## What this is not

- **Not** an unattended merge of `wiki/**/*.md` from the base into forks. Domain narrative stays in each child. See **`schema/fork-sync.md`** and **`schema/human-wiki-automation-boundary.md`**.
- **Not** a replacement for Git remotes. Point environment variables at local checkouts (or bind-mounted CI workspaces) you intend to compare.

## Registry

- **Machine list:** **`ai/schema/wiki_manager_registry.v1.json`** (`managed_children[].id`, `label`, `path_env`). **`v`** must be **1**. Each **`id`** must match lowercase letters, digits, and single hyphens between segments (safe directory name under **`ai/runtime/manager/`**). Each **`path_env`** names an environment variable whose value is an absolute path to that child checkout.
- **Upstream (diff left side):** defaults to this **Manager** checkout when you want **Manager** compared to a child. Export the Base Model path using the env var named in registry **`compare_root_env`** (default **`WIKI_MANAGER_COMPARE_ROOT`**) so the diff left side is a **neutral** **sibling LLM Wiki Base Model** tree while policy and JSON outputs stay in **Manager**. A child checkout path must **not** be the same directory as **`compare_root`** (resolved). Policy JSON for fork-delta still loads from **this** checkout when compare-root differs, so classification stays aligned with the **`ai/schema/fork_delta_policy.v1.json`** file in this checkout.

## Commands

| Command | Purpose |
|--------|---------|
| **`make wiki-manager-list`** | Print resolved `compare_root` and each child path (from env). |
| **`make wiki-manager-report`** | **`fork_delta_report.py` only** per child (fast path inventory under **`ai/runtime/manager/<id>/fork_delta_report.min.json`**). |
| **`make wiki-manager-fork-delta-full`** | For each child with a resolvable directory, run the same pipeline as **`make fork-delta-full`**, writing under **`ai/runtime/manager/<child-id>/`** so runs do not overwrite **`ai/runtime/fork_delta_*.min.json`**. |
| **`make wiki-manager-fork-delta-from-base`** | Same as **`wiki-manager-fork-delta-full`** but **`--require-base-compare`**: exits **2** unless the compare-root env (registry **`compare_root_env`**, default **`WIKI_MANAGER_COMPARE_ROOT`**) resolves to a directory **other than** this manager checkout (forces **LLM Wiki Base Model** as diff left side). |
| **`make wiki-manager-report-from-base`** | **`fork_delta_report.py` only** per child with **`--require-base-compare`** (same fail-fast guard as above). |
| **`make wiki-manager-sync-status`** | Writes **`ai/runtime/manager/sync_status.min.json`**: embeds **`wiki_family_snapshot`** output plus per-child counts from existing **`fork_delta_report.min.json`** / **`fork_delta_summary.min.json`** when present (run **`wiki-manager-report`** or **`wiki-manager-fork-delta-full`** first). **`drift_warnings`** lists **`family_snapshot.warnings`** first, then drift-mode hints. Root **`family_snapshot_warning_codes`** mirrors **`family_snapshot.warning_codes`**. |
| **`make wiki-manager-sync-status-json`** | Same with **`--json`** on stdout for piping. |
| **`.github/workflows/ci.yml` (default)** | After **`make wiki-test`**, runs **`python3 scripts/wiki_manager_sync_status.py --json`** as import smoke. Does not require **`WIKI_MANAGER_*`**. Step order is guarded by **`tests/test_pipeline_step_order.py`** **`test_ci_yml_wiki_manager_sync_smoke_follows_wiki_test_before_wiki_ci`**. |
| **`make wiki-manager-snapshot`** | Print (or **`--json`**) resolved paths plus optional Git **`HEAD`** short hash and dirty file counts for **Manager**, **Base Model** (when compare-root env from **`compare_root_env`** is set and resolves), and each registry child. Emits **`warning [code]:`** lines (or JSON **`warnings`** with parallel **`warning_codes`**) when compare-root equals the manager path or a managed child path so fork-delta misconfiguration is visible before running diffs. |
| **`make wiki-manager-base-vs-manager-report`** | **`fork_delta_report.py`** only with **upstream = Base Model** (compare-root path from that env) and **downstream = this Manager checkout**. Writes **`ai/runtime/manager/base-vs-manager/fork_delta_report.min.json`**. Use after **Base Model** tooling moves to see what to port into **Manager** before refreshing children. |
| **`make wiki-manager-base-vs-manager-full`** | Same full fork-delta pipeline as **`make fork-delta-full`**, but **child** is **Manager** and **compare** is **Base Model**. Optional **`WIKI_MANAGER_ARGS='--dry-run'`** prints paths only. **`base-vs-manager-full --dry-run`** exits **0** and prints **skip** when compare-root env is unset so **`make wiki-manager-refresh-dry`** works on partial setups. |
| **`make wiki-manager-snapshot-json`** | Same as **`make wiki-manager-snapshot`** with **`--json`** on stdout (machine inventory). |
| **`make wiki-manager-refresh-dry`** | **`wiki-manager-list`**, **`wiki-manager-snapshot`**, **`base-vs-manager-full --dry-run`**, then **`wiki_manager_fork_delta.py full --dry-run`**. Safe default smoke when child env paths are not set yet. |
| Optional **`WIKI_MANAGER_ARGS`** | Example: **`WIKI_MANAGER_ARGS='--child tai-pan-wiki'`** targets one id on **`report`** / **`full`**. **`--dry-run`** lists work only. **`--require-all`** fails if any registered env path is missing. |

Single-child **`make`** parity: **`make fork-delta CHILD='…' COMPARE='…'`** and **`make fork-delta-full`** with the same variables pass **`--compare-root`** into **`fork_delta_report.py`** while keeping default outputs under **`ai/runtime/fork_delta_*.min.json`**.

## Local full gate (Manager)

- **`make wiki-all`** runs **`make wiki-test`** (pytest plus **`wiki-restore-runtime`**), then **`make wiki-ci`**, then **`make wiki-quality-gate`**, then **`wiki-restore-runtime`** again. The final restore keeps **`ai/runtime/`** clean when **`wiki-ci`** refreshes timestamps. **GitHub Actions** keeps separate workflow steps instead of one chained **`make`** target. **`tests/test_make_wiki_all_recipe.py`** pins the **`Makefile`** **`wiki-all`** recipe. **`tests/test_pipeline_step_order.py`** covers related **`Makefile`** step order where it applies. Operator-facing prose also appears under **`wiki/synthesis/llm-wiki-family-repositories.md`** **LLM Wiki Manager local parity**.
- Optional **`pre-push`**: **`WIKI_PRE_PUSH=all`** runs **`make wiki-all`**. See **`scripts/githooks/README.md`**.

Direct invocation:

```bash
python3 scripts/wiki_manager_fork_delta.py list
python3 scripts/wiki_manager_fork_delta.py report --dry-run
python3 scripts/wiki_manager_fork_delta.py report --require-base-compare --dry-run
python3 scripts/wiki_manager_fork_delta.py full --dry-run
python3 scripts/wiki_manager_fork_delta.py full --require-base-compare --dry-run
python3 scripts/wiki_manager_fork_delta.py full --child shaolin-monastery-research-system
python3 scripts/wiki_family_snapshot.py
python3 scripts/wiki_family_snapshot.py --json
python3 scripts/wiki_manager_sync_status.py
python3 scripts/wiki_manager_sync_status.py --json
python3 scripts/wiki_manager_fork_delta.py base-vs-manager-report
python3 scripts/wiki_manager_fork_delta.py base-vs-manager-full --dry-run
make wiki-manager-refresh-dry
make wiki-manager-snapshot-json
```

## Environment variables

Documented in **`.env.example`**. Typical layout on one machine:

- **`WIKI_MANAGER_COMPARE_ROOT`**: absolute path to **LLM Wiki Base Model** (optional). Registry field **`compare_root_env`** overrides the env var name when forks need a different export (default remains **`WIKI_MANAGER_COMPARE_ROOT`**). **`scripts/wiki_family_snapshot.py`** **`compare_root_env_key`** is shared by manager CLIs.
- **`WIKI_MANAGER_CHILD_SHAOLIN`**: absolute path to **Shaolin Monastery Research System**.
- **`WIKI_MANAGER_CHILD_TAI_PAN`**: absolute path to **Tai-Pan Wiki**.

## Artifacts

Outputs live under **`ai/runtime/manager/<id>/`** (gitignored). Each **managed child** bundle uses that child's registry **`id`**. The **Base Model versus Manager** bundle uses the fixed id **`base-vs-manager`**. Each full bundle includes **`fork_delta_summary.min.json`**, **`fork_delta_backlog.md`**, and the same artifact names as the single-child **`make fork-delta-full`** flow.

## Regression tests

Use **`tests/test_wiki_manager_fork_delta.py`** for **`wiki_manager_fork_delta.py`** and registry edge cases. Use **`tests/test_wiki_family_snapshot.py`** for **`wiki_family_snapshot.py`**. Use **`tests/test_wiki_manager_sync_status.py`** for **`wiki_manager_sync_status.py`**. Use **`tests/test_pipeline_step_order.py`** for **`Makefile`** and **`.github/workflows/ci.yml`** ordering (**`test_ci_yml_wiki_manager_sync_smoke_follows_wiki_test_before_wiki_ci`** covers **`wiki_manager_sync_status.py`** smoke placement after **`wiki-test`**). Use **`tests/test_fork_delta_report.py`** for **`--compare-root`** and split-root policy layout. Use **`tests/test_make_fork_delta_compare.py`** for **`Makefile`** **`fork-delta`** targets with **`COMPARE=`**. **`tests/conftest.py`** and **`tests/test_makeflags_inheritance.py`** guard nested **`make`** subprocess smoke tests when GNU make would otherwise inherit question-mode **`MAKEFLAGS`**. **`tests/_resolved_python.py`** and **`tests/test_build_hub_links.py`** document **`RESOLVED_PYTHON`** for **`subprocess.run`** calls that set **`cwd`** outside the repo checkout (**`schema/AGENTS.md`** **Pytest subprocess hygiene**, plus the note in that section that **`tests/conftest.py`** and **`tests/_resolved_python.py`** module docstrings cross-link **`MAKEFLAGS`** and **`RESOLVED_PYTHON`**).

## Low-level compare flag

**`scripts/fork_delta_report.py`** accepts **`--compare-root`** when **`--repo-root`** is the manager checkout: file comparison uses **compare-root** versus **child-root**, while outputs and policy resolution use **repo-root**. Legacy invocations omit **`--compare-root`** so behavior matches older **`make fork-delta`** usage. **compare-root** and **child-root** must resolve to different paths (including **`make fork-delta CHILD='…' COMPARE='…'`** when both are set).

## See also

- **`schema/fork-sync.md`** (upstreaming and **LLM Wiki Manager** as canonical toolchain home)
- **`schema/human-wiki-automation-boundary.md`** (coordination outputs are read-only. No silent sibling **`wiki/`** merges)
- **`scripts/githooks/README.md`** (optional **`pre-push`** modes. **`make wiki-manager-*`** targets are manual unless you extend the hook locally)
- **`wiki/synthesis/llm-wiki-family-repositories.md`** (default paths and maintainer playbook for all four checkouts)
