# Copilot Project Instructions: pd-book-tools

Copilot-specific adapter for this repository.

## Canonical baseline

- Cross-agent instructions live in `AGENTS.md` at repository root.
- Treat `AGENTS.md` as canonical for workflow, architecture, validation, and documentation policy.
- Keep this file limited to Copilot/VS Code-specific notes only.

## Copilot in VS Code

- In VS Code, prefer task-based execution when suitable tasks exist.
- For tests in VS Code, prefer the built-in VS Code test runner when available.
- Use terminal commands only when no suitable task exists.
- When a task and a Make command are equivalent in VS Code, either is acceptable.

## Project-specific Copilot note

- For code generation, setup/configuration, and library/API references, use Context7 MCP tools.

## Documentation hygiene for this adapter

- Do not restate shared project rules here; add or update those in `AGENTS.md`.
- Update this file only for Copilot/VS Code-specific behavior.
