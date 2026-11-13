set shell := ["bash", "-eu", "-o", "pipefail", "-c"]
set positional-arguments

# Copy this wrapper and install-hooks with the shell setting to sibling justfiles.
[private]
_ai +args:
    #!/usr/bin/env bash
    set -euo pipefail
    if env AI= just --quiet "$@" > .ci-ai.log 2>&1; then
        printf 'PASS: %s\n' "$*"
    else
        result=$?
        printf 'FAIL: %s (exit %s)\n' "$*" "$result"
        if [[ -f scripts/ai_filter_log.py ]]; then
            uv run python scripts/ai_filter_log.py .ci-ai.log
        else
            tail -50 .ci-ai.log
        fi
        exit "$result"
    fi

install-hooks:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai install-hooks; fi
    if [[ -f .git ]]; then
        echo "hooks: worktree checkout - the canonical repo owns them, skipping"
    elif [[ -n "$(git config --get core.hooksPath || true)" ]]; then
        echo "hooks: core.hooksPath is set - leaving it alone, skipping"
    else
        uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
    fi


# A failed probe means CPU-only, including when CI is absent.
gpu_extra := `bash -c 'if [ -z "${CI:-}" ] && command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then echo --extra gpu; fi'`
coverage_config := if gpu_extra == "" { ".coveragerc.cpu" } else { "pyproject.toml" }

help:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai help; fi
    just --list

setup:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai setup; fi
    uv sync --locked --group dev {{gpu_extra}}
    just --quiet install-hooks

reset-venv:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai reset-venv; fi
    just --quiet reset

remove-venv:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai remove-venv; fi
    echo "🗑️  Removing existing virtual environment..."
    rm -rf "${UV_PROJECT_ENVIRONMENT:-.venv}"
    echo "✅ Virtual environment removed!"

reset:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai reset; fi
    just --quiet clean
    just --quiet remove-venv
    just --quiet setup
    echo "✅ Environment Reset!"

reset-full:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai reset-full; fi
    echo "🔄 FULL RESET: Clearing all caches and virtual environment..."
    just --quiet clean
    just --quiet remove-venv
    echo "🧹 Clearing UV cache..."
    uv cache clean
    echo "⬇️ Dependencies should download fresh now."
    just --quiet setup
    echo "💥 Full reset complete! Everything is fresh!"

test:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai test; fi
    just --quiet sync-gpu
    echo "🧪 Running tests (parallelized, slow tests excluded)..."
    uv run pytest --cov-config={{coverage_config}} -n auto -v -ra

test-slow:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai test-slow; fi
    just --quiet sync-gpu
    echo "🧪 Running tests including slow model-download smoke tests..."
    uv run pytest --cov-config={{coverage_config}} -n auto -v -ra -m "slow or not slow"

test-verbose:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai test-verbose; fi
    just --quiet sync-gpu
    echo "🧪 Running tests (verbose mode, parallelized)..."
    uv run pytest --cov-config={{coverage_config}} -n auto -v -ra

test-single:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai test-single; fi
    just --quiet sync-gpu
    if [ -z "${TEST:-}" ]; then
        echo "❌ Missing TEST parameter."
        echo "   Example: TEST='tests/ocr/test_word.py::TestWord::test_word_scale' just test-single"
        exit 1
    fi
    echo "🧪 Running single test (parallelized): ${TEST:-}"
    uv run pytest --cov-config={{coverage_config}} -n auto "${TEST:-}"

test-k:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai test-k; fi
    just --quiet sync-gpu
    if [ -z "${K:-}" ]; then
        echo "❌ Missing K parameter."
        echo "   Example: K='test_word_scale' just test-k"
        exit 1
    fi
    echo "🧪 Running tests with -k (parallelized): ${K:-}"
    uv run pytest --cov-config={{coverage_config}} -n auto -k "${K:-}"

coverage:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai coverage; fi
    just --quiet sync-gpu
    echo "🧪 Running tests with coverage (parallelized)..."
    uv run pytest --cov-config={{coverage_config}} --cov=pdomain_book_tools --cov-report=html --cov-report=xml -n auto -v -ra
    echo "📊 Coverage report generated in htmlcov/index.html"
    uv run python scripts/coverage_reporter.py

sync-gpu:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai sync-gpu; fi
    uv sync --locked --group dev {{gpu_extra}}

upgrade-deps:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai upgrade-deps; fi
    if ! uv run python scripts/check_dev_local.py --quiet 2> /dev/null; then
        echo "" >&2
        echo "❌ local-dev venv detected (GPU extras, editable siblings, or marker)." >&2
        echo "   Running 'uv sync' here would revert the venv to the canonical baseline." >&2
        echo "   Use:  just local-upgrade-deps   (lock + sync + restore GPU extras)" >&2
        echo "" >&2
        exit 1
    fi
    if [ -f "${UV_PROJECT_ENVIRONMENT:-.venv}/.pdomain-local-mode" ]; then
        echo "" >&2
        echo "❌ local-dev marker (${UV_PROJECT_ENVIRONMENT:-.venv}/.pdomain-local-mode) detected." >&2
        echo "   Use:  just local-upgrade-deps" >&2
        echo "" >&2
        exit 1
    fi
    echo "⬆️ Upgrading dependency lockfile..."
    uv lock --upgrade
    echo "📦 Syncing upgraded dependencies..."
    uv sync --group dev
    just --quiet update-hooks
    echo "✅ Dependencies upgraded and environment synced!"

local-dev:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai local-dev; fi
    ./scripts/local-dev.sh

local-check:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai local-check; fi
    ./scripts/local-check.sh

local-upgrade-deps:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai local-upgrade-deps; fi
    ./scripts/local-upgrade-deps.sh

dev-local:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai dev-local; fi
    echo "warning: 'dev-local' is deprecated; use 'local-dev'"
    just --quiet local-dev

check-dev-local:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai check-dev-local; fi
    echo "warning: 'check-dev-local' is deprecated; use 'local-check'"
    just --quiet local-check

upgrade-deps-local:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai upgrade-deps-local; fi
    echo "warning: 'upgrade-deps-local' is deprecated; use 'local-upgrade-deps'"
    just --quiet local-upgrade-deps

lint:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai lint; fi
    echo "🔍 Running linting checks..."
    uv run ruff check --select I --fix
    uv run ruff check --fix

fast-check:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai fast-check; fi
    just --quiet lint

format:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai format; fi
    uv run ruff format

pre-commit-check:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai pre-commit-check; fi
    SKIP="basedpyright${SKIP:+,$SKIP}" uv run pre-commit run --all-files

update-hooks:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai update-hooks; fi
    echo "⬆️  Updating pre-commit hook revisions (frozen to commit SHAs)..."
    uv run pre-commit autoupdate --freeze
    echo "✅ Hook revisions updated — review upstream release notes and the .pre-commit-config.yaml diff."

lint-check:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai lint-check; fi
    echo "🔍 Checking format and lint (read-only, full repo)..."
    uv run ruff format --check .
    uv run ruff check .

format-check:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai format-check; fi
    uv run ruff format --check .

typecheck:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai typecheck; fi
    echo "🔬 Running basedpyright type check..."
    uv run basedpyright

build:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai build; fi
    echo "🔨 Building project..."
    uv build

[default]
ci:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai ci; fi
    just --quiet setup pre-commit-check lint-check typecheck test build layout-fork-info
    docgraph check --strict

ci-slow:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai ci-slow; fi
    just --quiet ci

clean:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai clean; fi
    echo "🧹 Cleaning Python cache files..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2> /dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2> /dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2> /dev/null || true
    find . -type d -name ".ruff_cache" -exec rm -rf {} + 2> /dev/null || true
    echo "🧹 Cleaning coverage files..."
    rm -rf htmlcov/ 2> /dev/null || true
    rm -f coverage.xml 2> /dev/null || true
    echo "🧹 Cleaning build artifacts..."
    rm -rf dist/ 2> /dev/null || true
    echo "✅ Cache cleanup complete!"

clean-logs:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai clean-logs; fi
    echo "🧹 Cleaning logs..."
    find logs -type f -name "*.log" -delete 2> /dev/null || true
    echo "✅ Log cleanup complete!"

clean-debug:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai clean-debug; fi
    echo "🧹 Removing timestamped debug runs (test-* and regen-*)..."
    DEBUG=tests/fixtures/layout_regression/debug
    if [ -d "$DEBUG" ]; then
        COUNT=$(find "$DEBUG" -maxdepth 1 -type d \( -name 'test-*' -o -name 'regen-*' \) | wc -l)
        find "$DEBUG" -maxdepth 1 -type d \( -name 'test-*' -o -name 'regen-*' \) -exec rm -rf {} +
        echo "✅ Removed $COUNT timestamped run(s)."
    else
        echo "ℹ️  $DEBUG does not exist; nothing to clean."
    fi

release-patch:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai release-patch; fi
    BUMP=patch ./scripts/do-release.sh

release-minor:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai release-minor; fi
    BUMP=minor ./scripts/do-release.sh

release-major:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai release-major; fi
    BUMP=major ./scripts/do-release.sh

layout-fork-info:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai layout-fork-info; fi
    uv run python scripts/check_layout_fork.py

layout-fork-update:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai layout-fork-update; fi
    [[ ${HF_LAYOUT_UPSTREAM:-PaddlePaddle/PP-DocLayout_plus-L_safetensors} =~ ^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$ ]] || {
        echo "Invalid HF_LAYOUT_UPSTREAM: ${HF_LAYOUT_UPSTREAM:-}" >&2
        exit 1
    }
    [[ ${HF_LAYOUT_FORK:-CT2534/PP-DocLayout_plus-L} =~ ^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$ ]] || {
        echo "Invalid HF_LAYOUT_FORK: ${HF_LAYOUT_FORK:-}" >&2
        exit 1
    }
    [[ ${HF_LAYOUT_MIRROR:-/tmp/pp-doclayout-mirror} =~ ^[A-Za-z0-9._/-]+$ ]] || {
        echo "Invalid HF_LAYOUT_MIRROR: ${HF_LAYOUT_MIRROR:-}" >&2
        exit 1
    }
    command -v hf > /dev/null 2>&1 || {
        echo "ERROR: 'hf' CLI not found. uv add huggingface_hub or pip install -U huggingface_hub"
        exit 1
    }
    echo "🔁 Re-downloading ${HF_LAYOUT_UPSTREAM:-PaddlePaddle/PP-DocLayout_plus-L_safetensors} → ${HF_LAYOUT_MIRROR:-/tmp/pp-doclayout-mirror} ..."
    rm -rf "${HF_LAYOUT_MIRROR:-/tmp/pp-doclayout-mirror}"
    hf download "${HF_LAYOUT_UPSTREAM:-PaddlePaddle/PP-DocLayout_plus-L_safetensors}" --local-dir "${HF_LAYOUT_MIRROR:-/tmp/pp-doclayout-mirror}" > /dev/null
    echo "⬆️  Uploading mirror → ${HF_LAYOUT_FORK:-CT2534/PP-DocLayout_plus-L} ..."
    hf upload "${HF_LAYOUT_FORK:-CT2534/PP-DocLayout_plus-L}" "${HF_LAYOUT_MIRROR:-/tmp/pp-doclayout-mirror}" . \
        --commit-message "Re-sync from ${HF_LAYOUT_UPSTREAM:-PaddlePaddle/PP-DocLayout_plus-L_safetensors} ($(date -u +%Y-%m-%dT%H:%M:%SZ))" > /dev/null
    SHA=$(git ls-remote "https://huggingface.co/${HF_LAYOUT_FORK:-CT2534/PP-DocLayout_plus-L}" HEAD | cut -f1)
    echo "✅ Fork now at $SHA"
    echo "   Pin it with: SHA=$SHA just layout-fork-pin"

layout-fixtures-regenerate:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai layout-fixtures-regenerate; fi
    echo "🔁 Regenerating layout JSON fixtures (downloads ~132 MB model on first run)..."
    uv run python tests/fixtures/layout_regression/regenerate_layouts.py
    echo "✅ Layout fixtures regenerated. Inspect diffs and commit if intended."

layout-fork-pin:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai layout-fork-pin; fi
    [[ ${SHA:-} =~ ^[0-9a-f]{7,40}$ ]] || {
        echo "Invalid SHA: ${SHA:-}" >&2
        exit 1
    }
    if [ -z "${SHA:-}" ]; then
        echo "❌ Missing SHA. Usage: SHA=<commit> just layout-fork-pin"
        exit 1
    fi
    if ! [ -f "${HF_LAYOUT_ADAPTER:-pdomain_book_tools/layout/adapters/pp_doclayout.py}" ]; then
        echo "❌ Adapter not found at ${HF_LAYOUT_ADAPTER:-pdomain_book_tools/layout/adapters/pp_doclayout.py}"
        exit 1
    fi
    adapter=${HF_LAYOUT_ADAPTER:-pdomain_book_tools/layout/adapters/pp_doclayout.py}
    OLD=$(grep '^_DEFAULT_REVISION' "$adapter" | sed -E 's/.*"([^"]+)".*/\1/')
    if [ "$OLD" = "${SHA:-}" ]; then
        echo "ℹ️  ${HF_LAYOUT_ADAPTER:-pdomain_book_tools/layout/adapters/pp_doclayout.py} is already pinned at $OLD"
        exit 0
    fi
    sed -i.bak -E "s|^(_DEFAULT_REVISION = \").*(\")|\1${SHA:-}\2|" "$adapter"
    rm -f "$adapter.bak"
    echo "📌 Pinned ${HF_LAYOUT_ADAPTER:-pdomain_book_tools/layout/adapters/pp_doclayout.py}: $OLD → ${SHA:-}"

[private]
_do-release:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai _do-release; fi
    BUMP="${BUMP:-minor}" ./scripts/do-release.sh

update-pdomain-deps:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${AI:-}" ]]; then exec just --quiet _ai update-pdomain-deps; fi
    if ! uv run python scripts/check_dev_local.py --quiet 2> /dev/null || [[ -f "${UV_PROJECT_ENVIRONMENT:-.venv}/.pdomain-local-mode" ]]; then
        echo "Refusing dependency upgrades in local-dev mode" >&2
        exit 1
    fi
    uv lock --upgrade-package pdomain-book-contracts
    uv sync --group dev {{gpu_extra}}
