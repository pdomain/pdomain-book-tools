# pd-book-tools

Python tools for working with public domain book scans.

## Installation

Install Nvidia CUDA toolkit if you want to use GPU functions.
https://developer.nvidia.com/cuda-toolkit

Install the 'uv' tooling to manage project dependencies:

https://docs.astral.sh/uv/getting-started/installation/

I used: `pipx install uv` (you will need pipx to do this), upgrade with `pipx upgrade uv`

Then run `uv venv` to create a venv.

Deactivate any current venv (`deactivate`), then activate the venv `source .venv/bin/activate`

Install dependencies:
`uv sync --extra dev`

This installs both runtime and development dependencies (including pre-commit, pytest, ruff).

Also, if you want to use tesseract, you have to install it on your system.
https://tesseract-ocr.github.io/tessdoc/Installation.html

Try to build
`uv build`

Try to test
`uv run pytest`

Set up pre-commit hooks (required for all contributors):
`uv run pre-commit install`

Check pre-commit manually:
`uv run pre-commit run --all-files`

## Usage

TODO

## License

See LICENSE file.
