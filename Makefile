# LLM Wiki Manager — coordination makefile (no bundled wiki toolchain).
PYTHON ?= python3
COORD := $(PYTHON) scripts/wiki_coord.py

.PHONY: help coord-list coord-snapshot coord-snapshot-json coord-status coord-status-json coord-ci-smoke \
	coord-fork-delta-help \
	wiki-manager-list wiki-manager-snapshot wiki-manager-snapshot-json wiki-manager-sync-status \
	wiki-manager-sync-status-json

help:
	@echo "Targets:"
	@echo "  make coord-list           # TAB-separated paths from registry + env"
	@echo "  make coord-snapshot       # human-readable snapshot"
	@echo "  make coord-snapshot-json  # JSON snapshot (stdout)"
	@echo "  make coord-status         # write runtime/sync_status.min.json"
	@echo "  make coord-status-json    # same + JSON on stdout"
	@echo "  make coord-ci-smoke       # capture status JSON then run ci-smoke-check-stdin (CI parity)"
	@echo "  make coord-fork-delta-help  # where to run fork-delta-full (Base Model; see schema/wiki-manager.md)"
	@echo "  make test                 # pytest"
	@echo "(Aliases: wiki-manager-list, wiki-manager-snapshot[-json], wiki-manager-sync-status[-json])"

# Fork-delta never runs in this repo; this target only prints the operator one-liner (Base Model checkout).
coord-fork-delta-help:
	@echo "Fork-delta: run from LLM Wiki Base Model (not this repo). Full recipe: schema/wiki-manager.md → Human-facing wiki universalization."
	@echo "Export WIKI_MANAGER_COMPARE_ROOT and the child path_env you compare (e.g. WIKI_MANAGER_CHILD_SHAOLIN; see .env.example), then:"
	@echo '  cd "$$WIKI_MANAGER_COMPARE_ROOT" && OV="$$WIKI_MANAGER_COMPARE_ROOT/ai/schema/fork_delta_child_path_overrides.shaolin-monastery-research-system.v1.json" && make fork-delta-full CHILD="$$WIKI_MANAGER_CHILD_SHAOLIN" CHILD_PATH_OVERRIDES="$$OV"'
	@echo "Lighter Phase-0 triage (same checkout): make fork-delta … CHILD_PATH_OVERRIDES=… ; make fork-delta-scan CHILD=… (scan needs CHILD only; then read ai/runtime/fork_delta_*.min.json). Phases 0–4: Base Model schema/human-wiki-universal-backlog.md + schema/fork-sync.md."

coord-list:
	@$(COORD) list

coord-snapshot:
	@$(COORD) snapshot

coord-snapshot-json:
	@$(COORD) snapshot --json

coord-status:
	@$(COORD) status

coord-status-json:
	@$(COORD) status --json

# CI helper: capture rollup before smoke so `status --json` failures are not masked by plain `|`.
coord-ci-smoke:
	@rollup=$$(mktemp); \
	$(COORD) status --json >"$$rollup"; \
	sts=$$?; \
	if [ $$sts -ne 0 ]; then rm -f "$$rollup"; exit $$sts; fi; \
	$(COORD) ci-smoke-check-stdin <"$$rollup"; \
	rc=$$?; rm -f "$$rollup"; exit $$rc

test:
	@$(PYTHON) -m pytest -q

# Backwards-friendly names (thin aliases for older docs / muscle memory).
wiki-manager-list: coord-list
wiki-manager-snapshot: coord-snapshot
wiki-manager-snapshot-json: coord-snapshot-json
wiki-manager-sync-status: coord-status
wiki-manager-sync-status-json: coord-status-json
