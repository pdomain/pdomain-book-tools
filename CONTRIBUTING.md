# Contributing to pd-book-tools

Thank you for your interest in contributing to pd-book-tools!

## Development Setup

1. **Install UV package manager**: Follow the [UV installation guide](https://docs.astral.sh/uv/getting-started/installation/)

2. **Clone and set up the project**:
   ```bash
   git clone https://github.com/ConcaveTrillion/pd-book-tools.git
   cd pd-book-tools
   make install  # This installs deps + sets up pre-commit
   ```

   **Or manually**:
   ```bash
   uv sync --extra dev
   uv run pre-commit install
   ```

3. **🎯 Verify setup**:
   ```bash
   make help              # Should show all available commands
   make pre-commit-check  # Should run successfully
   ```

   This ensures code quality checks run automatically before each commit. **All contributions must pass these checks.**

## Code Quality

### Pre-commit Hooks
- **Automatically runs** on every `git commit`
- Includes: Ruff linting/formatting, trailing whitespace removal, YAML/JSON validation
- **Manual run**: `uv run pre-commit run --all-files`
- **If hooks fail**: Fix the issues and commit again

### Development Commands

We provide a comprehensive Makefile for all development tasks. Run `make help` to see all available commands:

#### **📦 Setup & Installation**
```bash
make install           # Install dependencies and setup pre-commit hooks
make setup             # Alias for install
```

#### **🔧 Environment Management**
```bash
make clean             # Clean cache files (keeps venv and UV cache)
make remove-venv       # Remove virtual environment only
make reset             # Clean rebuild (venv + cache, keeps UV cache)
make reset-full        # Nuclear option: clear everything and redownload
make reinstall         # Alias for reset (backward compatibility)
```

#### **🧪 Development & Testing**
```bash
make test              # Run test suite with coverage
make lint              # Run linting checks (with auto-fix)
make format            # Format code with Ruff
make pre-commit-check  # Run pre-commit on all files
```

#### **📋 Help**
```bash
make help              # Show all available commands with descriptions
```

**💡 Pro tip**: Use `make reset` for most environment issues, `make reset-full` only when everything is broken!

### Testing
- **Run tests**: `make test` (includes coverage reporting)
- **Coverage reports** are generated in `htmlcov/` directory
- **Ensure all tests pass** before submitting PR
- **Add tests** for new functionality

### Code Style & Quality
- **Ruff** for linting and formatting (enforced by pre-commit)
- **Import sorting** with Ruff (replaces isort)
- **Automatic fixes** where possible (`make lint` auto-fixes issues)
- **Pre-commit hooks** ensure consistency across all commits
- Follow existing code patterns and conventions

## Troubleshooting Environment Issues

If you encounter problems, try these commands in order:

```bash
# Light cleanup - removes cache files only
make clean

# Medium reset - rebuilds environment (keeps UV cache for speed)
make reset

# Nuclear option - clears everything including UV cache (slow but thorough)
make reset-full
```

## Submitting Changes

1. **Create a feature branch**: `git checkout -b feature-name`
2. **Make your changes**
3. **Test your changes**: `make test`
4. **Check code quality**: `make lint` and `make format`
5. **Run pre-commit**: `make pre-commit-check`
6. **Commit your changes** (hooks will run automatically)
7. **Push and create a Pull Request**

### Quick Quality Check
```bash
# Run this before submitting PR
make format && make lint && make test
```

## Questions?

Open an issue or reach out to the maintainers!
