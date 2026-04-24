# pd-book-tools

Python tools for working with public domain book scans.

## Installation

### Prerequisites

1. **Install UV package manager** (required):
   https://docs.astral.sh/uv/getting-started/installation/

2. **Install Tesseract OCR** (optional, for OCR functionality):
   https://tesseract-ocr.github.io/tessdoc/Installation.html

3. **Install Nvidia CUDA toolkit** (optional but highly recommended, for GPU functions):
   https://developer.nvidia.com/cuda-toolkit

   Note, if you are using a containerized dev env, you also need Nvidia container tools.
   https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

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

## License

See LICENSE file.
