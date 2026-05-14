.PHONY: install setup reinstall remove-venv reset reset-venv reset-full upgrade-deps upgrade-deps-local check-dev-local dev-local sync-gpu test test-verbose test-single test-k coverage lint lint-check format pre-commit-check build clean clean-logs clean-debug ci ci-slow release-patch release-minor release-major _do-release layout-fork-info layout-fork-update layout-fork-pin layout-fixtures-regenerate help

# Layout-detector fork sync (see pd_book_tools/layout/adapters/pp_doclayout.py)
HF_LAYOUT_UPSTREAM ?= PaddlePaddle/PP-DocLayout_plus-L_safetensors
HF_LAYOUT_FORK     ?= CT2534/PP-DocLayout_plus-L
HF_LAYOUT_MIRROR   ?= /tmp/pp-doclayout-mirror
HF_LAYOUT_ADAPTER  := pd_book_tools/layout/adapters/pp_doclayout.py

# Auto-detect a usable NVIDIA GPU (nvidia-smi present and succeeds) and not in CI.
# When detected, GPU_EXTRA expands to "--extra gpu"; otherwise it is empty.
GPU_EXTRA := $(shell [ -z "$$CI" ] && command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1 && echo --extra gpu)

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
	@[ -f .git/hooks/pre-commit ] || [ -f .git ] || uv run pre-commit install
	@echo "✅ Setup complete!"

install: setup ## Alias for setup (library — no CLI to install)

reinstall: reset-venv ## Alias for reset-venv (backward compatibility)

reset-venv: reset ## Alias for reset

remove-venv: ## Remove the virtual environment
	@echo "🗑️  Removing existing virtual environment..."
	rm -rf .venv
	@echo "✅ Virtual environment removed!"

reset: ## Rebuild virtual environment (keeps UV cache)
	@$(MAKE) --no-print-directory clean
	@$(MAKE) --no-print-directory remove-venv
	@$(MAKE) --no-print-directory install
	@echo "✅ Environment Reset!"

reset-full: ## Nuclear option: clear everything and redownload
	@echo "🔄 FULL RESET: Clearing all caches and virtual environment..."
	@$(MAKE) --no-print-directory clean
	@$(MAKE) --no-print-directory remove-venv
	@echo "🧹 Clearing UV cache..."
	uv cache clean
	@echo "⬇️ Dependencies should download fresh now."
	@$(MAKE) --no-print-directory install
	@echo "💥 Full reset complete! Everything is fresh!"

test: sync-gpu ## Run tests with parallelization
	@echo "🧪 Running tests (parallelized)..."
	uv run pytest -n auto -v -ra

test-verbose: sync-gpu ## Run tests with verbose output and parallelization
	@echo "🧪 Running tests (verbose mode, parallelized)..."
	uv run pytest -n auto -v -ra

test-single: sync-gpu ## Run one pytest node id (usage: make test-single TEST='tests/...::test_name')
	@if [ -z "$(TEST)" ]; then \
		echo "❌ Missing TEST parameter."; \
		echo "   Example: make test-single TEST='tests/ocr/test_word.py::TestWord::test_word_scale'"; \
		exit 1; \
	fi
	@echo "🧪 Running single test (parallelized): $(TEST)"
	uv run pytest -n auto "$(TEST)"

test-k: sync-gpu ## Run tests by pytest -k expression (usage: make test-k K='pattern')
	@if [ -z "$(K)" ]; then \
		echo "❌ Missing K parameter."; \
		echo "   Example: make test-k K='test_word_scale'"; \
		exit 1; \
	fi
	@echo "🧪 Running tests with -k (parallelized): $(K)"
	uv run pytest -n auto -k "$(K)"

coverage: sync-gpu ## Run tests with coverage report (parallelized)
	@echo "🧪 Running tests with coverage (parallelized)..."
	uv run pytest --cov=pd_book_tools --cov-report=html --cov-report=xml -n auto -v -ra
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


check-dev-local: ## Print whether the venv is in dev-local mode (exit 1 if so, 0 if canonical)
	@uv run python scripts/check_dev_local.py

dev-local: ## Enter dev-local mode: sync [gpu] extra (if GPU detected) + write .venv/.pd-dev-local marker
	@if [ ! -d .venv ]; then \
	  echo "❌ .venv not found. Run 'make install' first to create the venv." >&2; \
	  exit 1; \
	fi
	@$(MAKE) --no-print-directory sync-gpu
	@uv run python scripts/write_dev_local_marker.py --venv .venv
	@echo "✅ Venv is now in dev-local mode. 'make upgrade-deps' will refuse;"
	@echo "   use 'make upgrade-deps-local' to refresh dependencies."

upgrade-deps: ## Upgrade dependencies and sync local environment (refuses if dev-local — see upgrade-deps-local)
	@if ! uv run python scripts/check_dev_local.py --quiet; then \
	  uv run python scripts/check_dev_local.py >&2 || true; \
	  echo "" >&2; \
	  echo "❌ Refusing to clobber dev-local overrides. Run 'make upgrade-deps-local' instead." >&2; \
	  exit 1; \
	fi
	@echo "⬆️ Upgrading dependency lockfile..."
	uv lock --upgrade
	@echo "📦 Syncing upgraded dependencies..."
	uv sync --group dev
	@echo "✅ Dependencies upgraded and environment synced!"

upgrade-deps-local: ## Upgrade dependencies, then restore dev-local overrides ([gpu] extra if GPU detected)
	@echo "⬆️ Upgrading dependency lockfile (dev-local mode)..."
	uv lock --upgrade
	@echo "📦 Syncing canonical baseline first..."
	uv sync --group dev
	@echo "🔁 Restoring dev-local overrides..."
	@$(MAKE) --no-print-directory sync-gpu
	@echo "✅ Dependencies upgraded; dev-local overrides restored."

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
	uv run pre-commit run --all-files

lint-check: ## Read-only ruff format+check on all files (no auto-fix; matches GitHub CI exactly)
	@echo "🔍 Checking format and lint (read-only, full repo)..."
	uv run ruff format --check .
	uv run ruff check .

build: ## Build the project (hatchling/uv build)
	@echo "🔨 Building project..."
	uv build

ci: ## Run complete CI pipeline (setup [idempotent], pre-commit, lint-check, test, build, layout-fork-info)
	@echo "🚀 Running complete CI pipeline..."
	@$(MAKE) --no-print-directory setup
	@$(MAKE) --no-print-directory pre-commit-check
	@$(MAKE) --no-print-directory lint-check
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

layout-fork-update: ## Re-sync layout-detector fork from upstream and print the new SHA
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
# Pass SKIP_PUSH=1 to create the tag locally without pushing (dry-run).
# Pass RELEASE_BRANCH=main if/when the default branch is renamed.
_do-release:
	@BUMP=$(or $(BUMP),minor) ./scripts/do-release.sh
