# LLM Wiki Manager — coordination makefile (no bundled wiki toolchain).
PYTHON ?= python3
COORD := $(PYTHON) scripts/wiki_coord.py

.PHONY: help coord-list coord-snapshot coord-snapshot-json coord-status coord-status-json coord-ci-smoke \
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
	@echo "  make test                 # pytest"
	@echo "(Aliases: wiki-manager-list, wiki-manager-snapshot[-json], wiki-manager-sync-status[-json])"

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
