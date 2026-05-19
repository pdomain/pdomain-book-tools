# pd-book-tools — Documentation

Detailed documentation for the `pd-book-tools` Python library. Quick-start
information for users (installation, dependencies, basic usage) lives in the
top-level [`README.md`](../README.md); this directory holds the long-form
reference material.

## Layout

```text
docs/
├── README.md                          ← you are here
├── ROADMAP.md                         ← curated narrative of open work
├── ROADMAP-shipped.md                 ← what landed (and where to find it)
├── specs/                             ← architecture & planning specs
│   ├── README.md                      ← spec index (start here)
│   └── 0X-*.md                        ← numbered specs, see specs/README.md
└── review/                            ← human review notes (bugs, refactors)
```

When you reach for documentation, expect:

- **`specs/`** — durable architectural decisions and planning specs:
  pipeline diagrams, per-step heuristics, data-flow notes, the rationale
  behind specific thresholds, and the fixture-driven failures that shaped
  them. Read these when you need to *change* the behaviour of a subsystem
  and want to know what each knob does. Numbered prefixes are stable
  pointers — issues and code comments can refer to `Spec: 03-reorganize-pipeline`
  without breaking when neighbours are added.

Future top-level sections (add as needed):

- `guides/` — task-oriented walkthroughs (e.g. "how to add a new OCR fixture"
  or "how to fine-tune a DocTR model").
- `reference/` — generated or curated API references.

## Conventions

- Spec docs use a numbered or labelled pipeline outline at the top so the
  reader can map module functions to documented steps quickly. Each step
  has its own `### Step <name>` heading with the actual function names that
  implement it.
- When a heuristic threshold appears in code, mention it by name (e.g.
  `band_factor`) so a reader can grep both directions: docs ↔ code.
- Keep "what shaped this" sections at the bottom of architectural specs
  that list the specific fixtures or incidents that drove non-obvious
  decisions. Future maintainers should be able to see *why* a constant
  has its current value, not just *what* the constant is.
- New specs follow the workspace 9-section template (see
  `/workspaces/ocr-container/scripts/lint-spec.py`); existing specs are
  allowlisted as `legacy` in `specs/.specrc` and are migrated incrementally.
