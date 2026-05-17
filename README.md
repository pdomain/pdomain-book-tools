# pd-book-tools

Python tools for working with public domain book scans.

## Installation

### Prerequisites

1. **Install UV package manager** (required):
   <https://docs.astral.sh/uv/getting-started/installation/>

2. **Install Tesseract OCR** (optional, for OCR functionality):
   <https://tesseract-ocr.github.io/tessdoc/Installation.html>

3. **Install Nvidia CUDA toolkit** (optional, for the GPU extra):
   <https://developer.nvidia.com/cuda-toolkit>

   Required only when installing with the `[gpu]` extra (see below).
   If you are using a containerized dev env, you also need Nvidia
   container tools.
   <https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html>

### CPU-only vs GPU installs

The default install is CPU-only and works on Linux (CPU), macOS, and CI:

```bash
pip install pd-book-tools
```

For the optional CuPy/CUDA-12 acceleration (Linux + NVIDIA GPU only),
install with the `gpu` extra:

```bash
pip install 'pd-book-tools[gpu]'
```

This pulls in `cupy-cuda12x` and `opencv-cuda`, which require a
CUDA 12 toolkit and a compatible NVIDIA driver. The CPU pipeline
(`pd_book_tools.image_processing.cv2_processing.*`) remains the
fallback when the extra is not installed; calling any
`pd_book_tools.image_processing.cupy_processing.*` function without
the extra raises a clear `ImportError` pointing back at the install
command above.

### Quick Setup

The project includes a Makefile with convenient commands. For a complete setup:

```bash
make install
```

This will:

- Create a virtual environment
- Install all dependencies (runtime + development)
- Set up pre-commit hooks

### Available Make Commands

Run `make help` to see all available commands:

- `make install` - Install dependencies and set up development environment
- `make test` - Run tests
- `make lint` - Run linting checks
- `make format` - Format code
- `make build` - Build the project
- `make ci` - Run complete CI pipeline
- `make clean` - Clean up cache and temporary files
- `make reset` - Rebuild virtual environment
- `make reset-full` - Nuclear option: clear everything and redownload

### Manual Setup (Alternative)

If you prefer manual setup instead of using make:

```bash
# Install dependencies
uv sync --group dev

# Set up pre-commit hooks
uv run pre-commit install

# Test the installation
uv run pytest -n auto -v -ra

# Build the project
uv build
```

## Development Workflow

### Running Tests

```bash
make test
```

### Code Quality

```bash
make lint    # Check and auto-fix linting issues
make format  # Format code with ruff
```

### Coverage Testing

The project maintains test coverage thresholds to ensure code quality:

```bash
make coverage  # Run tests with coverage report (generates htmlcov/index.html)
```

**Coverage Thresholds:**

- **Hard threshold:** 80% — CI fails if coverage drops below this level
- **Soft target:** 88% — Goal for maintainability and code reliability

The coverage report includes a threshold summary with the current coverage
percentage and how it compares to the soft target.

### Pre-commit Checks

```bash
make pre-commit-check  # Run all pre-commit hooks
```

### Building

```bash
make build
```

### Complete CI Pipeline

```bash
make ci  # Runs install, pre-commit-check, test, and build
```

### Troubleshooting

If you encounter dependency issues:

```bash
make reset       # Rebuild environment (keeps cache)
make reset-full  # Nuclear option: clear everything
```

## Usage

### Geometry primitives

```python
from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.geometry.point import Point

bbox = BoundingBox(top_left=Point(10, 20), bottom_right=Point(110, 70))
print(bbox.width, bbox.height, bbox.area)
```

### OCR word model

```python
from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.geometry.point import Point
from pd_book_tools.ocr.word import Word

word = Word(
   text="Example",
   bounding_box=BoundingBox(Point(0, 0), Point(100, 20)),
   ocr_confidence=0.98,
)
word.ground_truth_text = "Example"
print(word.text, word.ground_truth_text)
```

### PGDP preprocessing

```python
from pd_book_tools.pgdp.pgdp_results import PGDPResults

results = PGDPResults("001.png", "Some -- raw [*proof note*] text")
print(results.processed_page_text)
```

### OCR a page (with auto-rotate)

```python
from pd_book_tools.ocr.document import Document

doc = Document.from_image_ocr_via_doctr("page.png")
page = doc.pages[0]

# `auto_rotate=True` is the default. If the upright OCR pass had mean
# per-word confidence below the threshold (0.6 by default), DocTR is
# re-run at 90°/180°/270° and the highest-confidence orientation wins.
# `page.rotation_applied` records the chosen rotation in degrees clockwise
# (one of 0/90/180/270). Bbox coordinates are in the rotated frame.
print(f"OCR ran at {page.rotation_applied}° rotation")

# Opt out (skip the fallback probes; pay only one OCR pass).
doc = Document.from_image_ocr_via_doctr("page.png", auto_rotate=False)

# Loosen the threshold (more pages take the fast path; fewer fallbacks).
doc = Document.from_image_ocr_via_doctr(
    "page.png", auto_rotate_threshold=0.4
)
```

See [`docs/specs/02-rotation.md`](docs/specs/02-rotation.md) for
the threshold rationale, the rotated-frame coordinate convention, and
what this is *not* (no arbitrary deskew, no separate orientation
classifier).

### Layout-regression fixture corpus

`tests/fixtures/layout_regression/` holds 30 hand-picked public-domain
pages plus their OCR / layout / reorganize artifacts; it's the contract
that pins the layout pipeline to known-good output. Workflow for adding
a fixture and regenerating after a pipeline change is in
[`docs/specs/04-layout-regression-fixtures.md`](docs/specs/04-layout-regression-fixtures.md).

## Emitting JSON Schema for downstream codegen

```sh
uv run python -m pd_book_tools.schemas.emit > schemas.json
```

The output is a single JSON document, keyed by public model class name
(`ReviewMetadata`, ...), whose values are JSON-Schema documents produced
by `pydantic.TypeAdapter`. Downstream consumers (`pd-ocr-ops`, `pd-ui`
codegen) re-run this command against a pinned wheel and feed the output
to `openapi-typescript` or equivalent to keep TypeScript types in sync
with the Python source of truth.

The set of public models lives in
`pd_book_tools/schemas/emit.py::PUBLIC_MODELS`. Add new models there.

## License

See LICENSE file.
