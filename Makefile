AI ?=
LOG := .ci-ai.log

ifdef AI
_goals := $(or $(MAKECMDGOALS),ci)
.PHONY: $(_goals)
$(_goals):
	@rm -f $(LOG)
	@$(MAKE) --no-print-directory AI= $@ > $(LOG) 2>&1 \
		&& echo "✅ $@ passed (log: $(LOG))" \
		|| (echo "❌ $@ failed:"; uv run scripts/ai_filter_log.py $(LOG); echo "(full log: $(LOG))"; exit 1)

else

.PHONY: setup remove-venv reset reset-venv reset-full upgrade-deps sync-gpu test test-slow test-verbose test-single test-k coverage lint lint-check format-check typecheck format pre-commit-check build clean clean-logs clean-debug ci ci-slow release-patch release-minor release-major _do-release layout-fork-info layout-fork-update layout-fork-pin layout-fixtures-regenerate help local-dev local-check local-upgrade-deps dev-local check-dev-local upgrade-deps-local

# Layout-detector fork sync (see pdomain_book_tools/layout/adapters/pp_doclayout.py)
HF_LAYOUT_UPSTREAM ?= PaddlePaddle/PP-DocLayout_plus-L_safetensors
HF_LAYOUT_FORK     ?= CT2534/PP-DocLayout_plus-L
HF_LAYOUT_MIRROR   ?= /tmp/pp-doclayout-mirror
HF_LAYOUT_ADAPTER  := pdomain_book_tools/layout/adapters/pp_doclayout.py

# Auto-detect a usable NVIDIA GPU (nvidia-smi present and succeeds) and not in CI.
# When detected, GPU_EXTRA expands to "--extra gpu"; otherwise it is empty.
GPU_EXTRA := $(shell [ -z "$$CI" ] && command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1 && echo --extra gpu)
COVERAGE_CONFIG := $(if $(strip $(GPU_EXTRA)),pyproject.toml,.coveragerc.cpu)

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Set up development environment (auto-detects [gpu] extra)
	@echo "📦 Installing dependencies..."
ifeq ($(strip $(GPU_EXTRA)),)
	@echo "ℹ️  No usable NVIDIA GPU detected (or CI=$$CI); installing CPU-only."
else
	@echo "🚀 NVIDIA GPU detected; installing with [gpu] extra (CuPy)."
endif
	uv sync --group dev $(GPU_EXTRA)
	@echo "🪝 Setting up pre-commit hooks..."
	@[ -f .git/hooks/pre-commit ] || [ -f .git ] || [ -n "$$(git config --get core.hooksPath 2>/dev/null)" ] || uv run pre-commit install
	@echo "✅ Setup complete!"

reset-venv: reset ## Alias for reset

remove-venv: ## Remove the virtual environment
	@echo "🗑️  Removing existing virtual environment..."
	rm -rf .venv
	@echo "✅ Virtual environment removed!"

reset: ## Rebuild virtual environment (keeps UV cache)
	@$(MAKE) --no-print-directory clean
	@$(MAKE) --no-print-directory remove-venv
	@$(MAKE) --no-print-directory setup
	@echo "✅ Environment Reset!"

reset-full: ## Nuclear option: clear everything and redownload
	@echo "🔄 FULL RESET: Clearing all caches and virtual environment..."
	@$(MAKE) --no-print-directory clean
	@$(MAKE) --no-print-directory remove-venv
	@echo "🧹 Clearing UV cache..."
	uv cache clean
	@echo "⬇️ Dependencies should download fresh now."
	@$(MAKE) --no-print-directory setup
	@echo "💥 Full reset complete! Everything is fresh!"

test: sync-gpu ## Run tests with parallelization (slow model-download tests excluded by default)
	@echo "🧪 Running tests (parallelized, slow tests excluded)..."
	uv run pytest --cov-config=$(COVERAGE_CONFIG) -n auto -v -ra

test-slow: sync-gpu ## Run ALL tests including slow model-download smoke tests (needs network + disk space)
	@echo "🧪 Running tests including slow model-download smoke tests..."
	uv run pytest --cov-config=$(COVERAGE_CONFIG) -n auto -v -ra -m "slow or not slow"

test-verbose: sync-gpu ## Run tests with verbose output and parallelization
	@echo "🧪 Running tests (verbose mode, parallelized)..."
	uv run pytest --cov-config=$(COVERAGE_CONFIG) -n auto -v -ra

test-single: sync-gpu ## Run one pytest node id (usage: make test-single TEST='tests/...::test_name')
	@if [ -z "$(TEST)" ]; then \
		echo "❌ Missing TEST parameter."; \
		echo "   Example: make test-single TEST='tests/ocr/test_word.py::TestWord::test_word_scale'"; \
		exit 1; \
	fi
	@echo "🧪 Running single test (parallelized): $(TEST)"
	uv run pytest --cov-config=$(COVERAGE_CONFIG) -n auto "$(TEST)"

test-k: sync-gpu ## Run tests by pytest -k expression (usage: make test-k K='pattern')
	@if [ -z "$(K)" ]; then \
		echo "❌ Missing K parameter."; \
		echo "   Example: make test-k K='test_word_scale'"; \
		exit 1; \
	fi
	@echo "🧪 Running tests with -k (parallelized): $(K)"
	uv run pytest --cov-config=$(COVERAGE_CONFIG) -n auto -k "$(K)"

coverage: sync-gpu ## Run tests with coverage report (parallelized)
	@echo "🧪 Running tests with coverage (parallelized)..."
	uv run pytest --cov-config=$(COVERAGE_CONFIG) --cov=pdomain_book_tools --cov-report=html --cov-report=xml -n auto -v -ra
	@echo "📊 Coverage report generated in htmlcov/index.html"
	@uv run python scripts/coverage_reporter.py

sync-gpu: ## Sync the [gpu] extra (CuPy) when an NVIDIA GPU is auto-detected; no-op otherwise / in CI
	@if [ -z "$(strip $(GPU_EXTRA))" ]; then \
	  echo "ℹ️  No usable NVIDIA GPU detected (or CI=$$CI); syncing without [gpu] extra."; \
	  uv sync --group dev; \
	else \
	  echo "📦 Syncing [gpu] extra (CuPy) for local GPU tests..."; \
	  uv sync --group dev --extra gpu; \
	fi


upgrade-deps: ## Upgrade dependencies and sync local environment (refuses if local-dev — see local-upgrade-deps)
	@# Two-tier dev-local detection (spec #200 / pdomain-ocr-cli canonical pattern):
	@#   1. check_dev_local.py — probes editable installs, [gpu] extras, env var,
	@#      and the .pdomain-dev-local marker written by write_dev_local_marker.py.
	@#   2. Fast marker fallback — also check .venv/.pdomain-local-mode (written by
	@#      local-dev.sh for back-compat with shell-side scripts).
	@# Either probe firing causes the recipe to refuse rather than clobber.
	@if ! uv run python scripts/check_dev_local.py --quiet 2>/dev/null; then \
	  echo "" >&2; \
	  echo "❌ local-dev venv detected (GPU extras, editable siblings, or marker)." >&2; \
	  echo "   Running 'uv sync' here would revert the venv to the canonical baseline." >&2; \
	  echo "   Use:  make local-upgrade-deps   (lock + sync + restore GPU extras)" >&2; \
	  echo "   Or:   PDOMAIN_DEV_LOCAL=0 make upgrade-deps   (intentional clobber)" >&2; \
	  echo "" >&2; \
	  exit 1; \
	fi
	@if [ -f .venv/.pdomain-local-mode ]; then \
	  echo "" >&2; \
	  echo "❌ local-dev marker (.venv/.pdomain-local-mode) detected." >&2; \
	  echo "   Use:  make local-upgrade-deps" >&2; \
	  echo "" >&2; \
	  exit 1; \
	fi
	@echo "⬆️ Upgrading dependency lockfile..."
	uv lock --upgrade
	@echo "📦 Syncing upgraded dependencies..."
	uv sync --group dev
	@echo "✅ Dependencies upgraded and environment synced!"

# ─── local-dev workflow (spec #362) ─────────────────────────────────────────

local-dev: ## Switch to local-dev mode (GPU extras active + marker)
	@./scripts/local-dev.sh

local-check: ## Print local-dev (GPU extras) status
	@./scripts/local-check.sh

local-upgrade-deps: ## Upgrade deps + re-sync GPU extras (local-mode only)
	@./scripts/local-upgrade-deps.sh

# Back-compat aliases for legacy target names (deprecated since #362)
dev-local: ## DEPRECATED: use local-dev
	@echo "warning: 'dev-local' is deprecated; use 'local-dev'"
	@$(MAKE) local-dev

check-dev-local: ## DEPRECATED: use local-check
	@echo "warning: 'check-dev-local' is deprecated; use 'local-check'"
	@$(MAKE) local-check

upgrade-deps-local: ## DEPRECATED: use local-upgrade-deps
	@echo "warning: 'upgrade-deps-local' is deprecated; use 'local-upgrade-deps'"
	@$(MAKE) local-upgrade-deps

lint: ## Run linting checks
	@echo "🔍 Running linting checks..."
	uv run ruff check --select I --fix
	uv run ruff check --fix

fast-check: lint ## Quick lint check used by style-review-apply.py to verify auto-fix patches

format: ## Format code
	@echo "✨ Formatting code..."
	uv run ruff format
	@$(MAKE) --no-print-directory lint

pre-commit-check: ## Run pre-commit on all files
	@echo "🪝 Running pre-commit on all files..."
	SKIP=basedpyright uv run pre-commit run --all-files

lint-check: ## Read-only ruff format+check on all files (no auto-fix; matches GitHub CI exactly)
	@echo "🔍 Checking format and lint (read-only, full repo)..."
	uv run ruff format --check .
	uv run ruff check .

format-check: lint-check ## Alias for lint-check (workspace canonical name for read-only format+lint check)

typecheck: ## Run basedpyright at recommended mode (workspace canonical)
	@echo "🔬 Running basedpyright type check..."
	uv run basedpyright pdomain_book_tools --level error

build: ## Build the project (hatchling/uv build)
	@echo "🔨 Building project..."
	uv build

ci: ## Run complete CI pipeline (setup [idempotent], pre-commit, lint-check, format-check, typecheck, test, build, layout-fork-info)
	@echo "🚀 Running complete CI pipeline..."
	@$(MAKE) --no-print-directory setup
	@$(MAKE) --no-print-directory pre-commit-check
	@$(MAKE) --no-print-directory lint-check
	@$(MAKE) --no-print-directory format-check
	@$(MAKE) --no-print-directory typecheck
	@$(MAKE) --no-print-directory test
	@$(MAKE) --no-print-directory build
	@echo ""
	@echo "🔎 Layout-detector fork drift check..."
	@$(MAKE) --no-print-directory layout-fork-info
	@echo "✅ CI pipeline complete!"

ci-slow: ci ## Full pre-flight for releases (alias of ci today; reserved for slower checks if added later)

clean: ## Clean up cache and temporary files (keeps venv and UV cache)
	@echo "🧹 Cleaning Python cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "🧹 Cleaning coverage files..."
	rm -rf htmlcov/ 2>/dev/null || true
	rm -f coverage.xml 2>/dev/null || true
	@echo "🧹 Cleaning build artifacts..."
	rm -rf dist/ 2>/dev/null || true
	@echo "✅ Cache cleanup complete!"

clean-logs: ## Remove log files from logs/ if present
	@echo "🧹 Cleaning logs..."
	find logs -type f -name "*.log" -delete 2>/dev/null || true
	@echo "✅ Log cleanup complete!"

clean-debug: ## Remove all timestamped debug runs from layout_regression/debug/
	@echo "🧹 Removing timestamped debug runs (test-* and regen-*)..."
	@DEBUG=tests/fixtures/layout_regression/debug; \
	if [ -d "$$DEBUG" ]; then \
	  COUNT=$$(find "$$DEBUG" -maxdepth 1 -type d \( -name 'test-*' -o -name 'regen-*' \) | wc -l); \
	  find "$$DEBUG" -maxdepth 1 -type d \( -name 'test-*' -o -name 'regen-*' \) -exec rm -rf {} +; \
	  echo "✅ Removed $$COUNT timestamped run(s)."; \
	else \
	  echo "ℹ️  $$DEBUG does not exist; nothing to clean."; \
	fi

release-patch: ## Release: bump patch, run ci-slow, tag, push (fires GitHub Release workflow; e.g. v0.10.0 → v0.10.1)
	@$(MAKE) --no-print-directory _do-release BUMP=patch

release-minor: ## Release: bump minor, run ci-slow, tag, push (fires GitHub Release workflow; e.g. v0.10.0 → v0.11.0)
	@$(MAKE) --no-print-directory _do-release BUMP=minor

release-major: ## Release: bump major, run ci-slow, tag, push (fires GitHub Release workflow; e.g. v0.10.0 → v1.0.0)
	@$(MAKE) --no-print-directory _do-release BUMP=major

layout-fork-info: ## Show pinned layout SHA + upstream / fork latest SHAs (warns on real file drift; never fails)
	@uv run python scripts/check_layout_fork.py

# Strict validators for variables interpolated into shell recipes below.
# These developer-only targets accept Make variables on the command line;
# a malicious value (e.g. SHA='x; rm -rf ~') would otherwise be a
# command-injection surface. Each guard rejects anything outside a tight
# allowlist regex before the value reaches a shell recipe.
#
# Hugging Face repo id: "owner/name", each segment [A-Za-z0-9._-].
HF_REPO_ID_RE := ^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$$
# Filesystem path: no shell metacharacters.
HF_PATH_RE := ^[A-Za-z0-9._/-]+$$
# Git commit SHA: 7-40 lowercase hex digits.
SHA_RE := ^[0-9a-f]{7,40}$$

define _check_var
	@printf '%s' "$(2)" | grep -Eq '$(3)' || { \
	  echo "❌ Invalid $(1): '$(2)' (must match $(3))"; exit 1; }
endef

layout-fork-update: ## Re-sync layout-detector fork from upstream and print the new SHA
	$(call _check_var,HF_LAYOUT_UPSTREAM,$(HF_LAYOUT_UPSTREAM),$(HF_REPO_ID_RE))
	$(call _check_var,HF_LAYOUT_FORK,$(HF_LAYOUT_FORK),$(HF_REPO_ID_RE))
	$(call _check_var,HF_LAYOUT_MIRROR,$(HF_LAYOUT_MIRROR),$(HF_PATH_RE))
	@command -v hf >/dev/null 2>&1 || { echo "ERROR: 'hf' CLI not found. uv add huggingface_hub or pip install -U huggingface_hub"; exit 1; }
	@echo "🔁 Re-downloading $(HF_LAYOUT_UPSTREAM) → $(HF_LAYOUT_MIRROR) ..."
	@rm -rf "$(HF_LAYOUT_MIRROR)"
	@hf download "$(HF_LAYOUT_UPSTREAM)" --local-dir "$(HF_LAYOUT_MIRROR)" >/dev/null
	@echo "⬆️  Uploading mirror → $(HF_LAYOUT_FORK) ..."
	@hf upload "$(HF_LAYOUT_FORK)" "$(HF_LAYOUT_MIRROR)" . \
	  --commit-message "Re-sync from $(HF_LAYOUT_UPSTREAM) ($$(date -u +%Y-%m-%dT%H:%M:%SZ))" >/dev/null
	@SHA=$$(git ls-remote https://huggingface.co/$(HF_LAYOUT_FORK) HEAD | cut -f1); \
	echo "✅ Fork now at $$SHA"; \
	echo "   Pin it with: make layout-fork-pin SHA=$$SHA"

layout-fixtures-regenerate: ## Re-run the layout model on tests/fixtures/.../inputs/*.png and cache JSON
	@echo "🔁 Regenerating layout JSON fixtures (downloads ~132 MB model on first run)..."
	@uv run python tests/fixtures/layout_regression/regenerate_layouts.py
	@echo "✅ Layout fixtures regenerated. Inspect diffs and commit if intended."

layout-fork-pin: ## Pin a SHA into pp_doclayout.py (usage: make layout-fork-pin SHA=<commit>)
	@if [ -z "$(SHA)" ]; then \
	  echo "❌ Missing SHA. Usage: make layout-fork-pin SHA=<commit>"; \
	  exit 1; \
	fi
	$(call _check_var,SHA,$(SHA),$(SHA_RE))
	@if ! [ -f "$(HF_LAYOUT_ADAPTER)" ]; then \
	  echo "❌ Adapter not found at $(HF_LAYOUT_ADAPTER)"; exit 1; \
	fi
	@OLD=$$(grep '^_DEFAULT_REVISION' $(HF_LAYOUT_ADAPTER) | sed -E 's/.*"([^"]+)".*/\1/'); \
	if [ "$$OLD" = "$(SHA)" ]; then \
	  echo "ℹ️  $(HF_LAYOUT_ADAPTER) is already pinned at $$OLD"; \
	  exit 0; \
	fi; \
	sed -i.bak -E 's|^(_DEFAULT_REVISION = ").*(")|\1$(SHA)\2|' $(HF_LAYOUT_ADAPTER); \
	rm -f $(HF_LAYOUT_ADAPTER).bak; \
	echo "📌 Pinned $(HF_LAYOUT_ADAPTER): $$OLD → $(SHA)"

# scripts/do-release.sh handles repo-state guards, runs the ci-slow
# pre-flight, computes the next three-component tag from the latest v*
# tag, creates the annotated tag, and pushes the release branch + tag
# (which fires .github/workflows/release.yml).
# Pass FORCE=1 to skip the repo-state guards (pre-flight still runs).
# Pass SKIP_PUSH=1 to create the tag locally without pushing.
# Pass RELEASE_BRANCH=main if/when the default branch is renamed.
_do-release:
	@BUMP=$(or $(BUMP),minor) ./scripts/do-release.sh

endif
