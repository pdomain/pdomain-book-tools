# pd-book-tools — Documentation

Detailed documentation for the `pd-book-tools` Python library. Quick-start
information for users (installation, dependencies, basic usage) lives in the
top-level [`README.md`](../README.md); this directory holds the long-form
reference material.

## Layout

```text
docs/
├── README.md                          ← you are here
└── architecture/                      ← how the pieces fit together: data
    │                                    models, algorithms, pipelines
    ├── reorganize_pipeline.md         ← Page.reorganize_page step-by-step
    ├── rotation.md                    ← OCR-time orientation detection
    └── layout_regression_fixtures.md  ← fixture corpus + regen workflow
```

When you reach for documentation, expect:

- **`architecture/`** — explains *how a subsystem works*: pipeline diagrams,
  per-step heuristics, data-flow notes, the rationale behind specific
  thresholds, and the fixture-driven failures that shaped them. Read these
  when you need to *change* the behaviour of a subsystem and want to know
  what each knob does.

Future top-level sections (add as needed):

- `guides/` — task-oriented walkthroughs (e.g. "how to add a new OCR fixture"
  or "how to fine-tune a DocTR model").
- `reference/` — generated or curated API references.

## Conventions

- Architecture docs use a numbered or labelled pipeline outline at the top so
  the reader can map module functions to documented steps quickly. Each step
  has its own `### Step <name>` heading with the actual function names that
  implement it.
- When a heuristic threshold appears in code, mention it by name (e.g.
  `band_factor`) so a reader can grep both directions: docs ↔ code.
- Keep "what shaped this" sections at the bottom of architecture docs that
  list the specific fixtures or incidents that drove non-obvious decisions.
  Future maintainers should be able to see *why* a constant has its current
  value, not just *what* the constant is.
