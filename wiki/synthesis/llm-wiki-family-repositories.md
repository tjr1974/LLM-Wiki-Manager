---
type: synthesis
title: "LLM Wiki family repositories"
updated: 2026-05-04
lang_primary: en
categories:
  - Meta
notes: "Authoritative maintainer map for the four related LLM Wiki checkouts on this machine. Paths are defaults under /home/admn/Downloads. Adjust if your layout differs."
---

# LLM Wiki family repositories

**LLM Wiki Manager** uses this **`wiki/`** tree as **machine-first LLM context** for the whole family. **Human readability is not a goal.** Keep this page **dense** (tables, bullets, stable headings) so agents burn fewer tokens for the same facts. Update paths and env vars when checkouts move.

## Default checkout paths (this machine)

| Repository | Role | Default absolute path |
|------------|------|------------------------|
| **LLM Wiki Manager** | Canonical development hub, coordination, fork-delta policy owner, this **`wiki/`** | `/home/admn/Downloads/LLM Wiki Manager` |
| **LLM Wiki Base Model** | Neutral sibling template, **`COMPARE=`** / **`WIKI_MANAGER_COMPARE_ROOT`** diff left side, cherry-pick target for shared tooling | `/home/admn/Downloads/LLM Wiki Base Model` |
| **Shaolin Monastery Research System** | Domain child wiki (registered in **`ai/schema/wiki_manager_registry.v1.json`**) | `/home/admn/Downloads/Shaolin Monastery Research System` |
| **Tai-Pan Wiki** | Domain child wiki (registered in **`ai/schema/wiki_manager_registry.v1.json`**) | `/home/admn/Downloads/Tai-Pan Wiki` |

## Public HTTPS remotes

| Repository | Typical **`git clone`** URL |
|------------|-----------------------------|
| **LLM Wiki Manager** | `https://github.com/tjr1974/LLM-Wiki-Manager.git` |
| **LLM Wiki Base Model** | `https://github.com/tjr1974/LLM-Wiki-Base-Model.git` |

On a **Manager** checkout, keep **`origin`** → Manager and add **`base-model`** → Base Model when you need **`fetch`** or **cherry-picks** from the sibling template. On a **Base Model** checkout, keep **`origin`** → Base Model and add **`manager`** → Manager when you need the same toward **Manager**. Root **`README.md`** (**Git remotes**) spells out both layouts.

## How paths enter automation

| Variable or command | Operator note |
|---------------------|----------------|
| **`WIKI_MANAGER_COMPARE_ROOT`** | Point at **LLM Wiki Base Model** when fork-delta should diff that tree against each child while policy JSON stays in **Manager**. |
| **`WIKI_MANAGER_CHILD_SHAOLIN`**, **`WIKI_MANAGER_CHILD_TAI_PAN`** | Point at the two domain checkouts. See **`.env.example`** and **`schema/wiki-manager.md`**. |
| **`make fork-delta CHILD='…' COMPARE='…'`** | Same compare semantics without the registry (single child). |
| **GitHub Actions (default `ci` workflow)** | After **`make wiki-test`**, runs **`python3 scripts/wiki_manager_sync_status.py --json`** pipe smoke (**`.github/workflows/ci.yml`**). Full fork-delta bundles stay local (needs **`WIKI_MANAGER_*`** paths). |

## Governance in one glance

| Topic | Rule |
|-------|------|
| **Shared tooling and CI** | Land in **LLM Wiki Manager** first per **`schema/wiki-manager.md`** **Canonical development hub**. |
| **LLM Wiki Base Model** | **Cherry-picked** neutral backports only. **Not** an unattended mirror of **Manager**. |
| **Shaolin**, **Tai-Pan** | Keep **domain narrative** in their own **`wiki/`** trees. **Manager** **`wiki/`** here documents relations and how operators run **`make wiki-manager-*`**, **`make fork-delta`**, and gates. It does **not** replace their encyclopedic mission pages. |

## When the Base Model checkout changes (operator playbook)

Scripts do **not** merge **`wiki/`** prose into children unattended. Use **Manager** to **measure** drift then **cherry-pick** by subsystem per **`schema/fork-sync.md`**.

| Step | Command or action |
|------|-------------------|
| 0 | Optional smoke without writing fork-delta artifacts: **`make wiki-manager-refresh-dry`**. |
| 1 | Export **`WIKI_MANAGER_COMPARE_ROOT`**, **`WIKI_MANAGER_CHILD_SHAOLIN`**, **`WIKI_MANAGER_CHILD_TAI_PAN`** (see **`.env.example`**). |
| 2 | **`make wiki-manager-snapshot`** or **`make wiki-manager-snapshot-json`** to confirm paths and Git dirty state. |
| 3 | **`make wiki-manager-base-vs-manager-report`** then inspect **`ai/runtime/manager/base-vs-manager/fork_delta_report.min.json`** for shared files that moved in **Base Model** but not yet in **Manager**. Port neutral changes into **Manager** first. |
| 4 | Prefer **`make wiki-manager-fork-delta-from-base`** (same as **`wiki-manager-fork-delta-full`** but **fails fast** if **`WIKI_MANAGER_COMPARE_ROOT`** is unset or points at this manager tree). Each child bundle diffs **Base Model** (left) versus that child (right). Use **`fork_delta_backlog.md`** under each **`ai/runtime/manager/<id>/`** for cherry-pick order. |
| 4b | **`make wiki-manager-sync-status`** (after step 4 or **`make wiki-manager-report-from-base`**) writes **`ai/runtime/manager/sync_status.min.json`**: one JSON rollup of Git heads, dirty counts, **`drift_compare_mode`**, and per-child **`fork_delta_report`** counts. |
| 5 | In each child repo run **`make wiki-all`** (or their documented merge gate) after ports. |

**LLM Wiki Manager local parity.** **`make wiki-all`** chains **`wiki-test`** (which already restores **`ai/runtime/`**), then **`wiki-ci`**, **`wiki-quality-gate`**, and **`wiki-restore-runtime`** again so **`wiki-ci`** timestamps do not leave **`ai/runtime/`** dirty. Domain children may use different documented gates. Pytest shell-outs to nested **`make`** inherit GNU make **`MAKEFLAGS`** unless **`tests/conftest.py`** clears it (**`schema/karpathy-llm-wiki-bridge.md`** **Pytest leg**, **`tests/test_makeflags_inheritance.py`**).

## See also

- See also [[main]] (hub)
- See also **`schema/wiki-manager.md`** (registry, **`## Regression tests`**, **Canonical development hub**)
- See also **`schema/fork-sync.md`** (upstreaming and **LLM Wiki Manager as canonical toolchain home**)
- See also **`scripts/githooks/README.md`** (optional **`pre-push`** versus manual **`make wiki-manager-*`** coordination)
- See also **`README.md`** **Governance** at the repository root
