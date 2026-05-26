"""Hugging Face Hub helpers for OCR + layout model resolution.

Canonical home for the model-resolution code shared by pdomain-ocr-cli,
pd-ocr-labeler, and pdomain-prep-for-pgdp. Each downstream app uses
``pdomain-book-tools`` for inference; this package factors out the
"how do we find / fetch the .pt files" layer so they don't drift.

Subpackage layout:

- :mod:`pdomain_book_tools.hf.download` — low-level :func:`hf_download` primitive
  and the :func:`suppress_hf_unauth_warning` context manager.
- :mod:`pdomain_book_tools.hf.models` — registry constants and the
  ``resolve_*`` / ``prefetch_*`` helpers built on top of the primitive.

All public names are re-exported here so callers can write
``from pdomain_book_tools.hf import hf_download`` and stay decoupled from the
internal split.
"""

from .download import hf_download, suppress_hf_unauth_warning
from .models import (
    DEFAULT_DET_FILENAME,
    DEFAULT_HF_REPO,
    DEFAULT_RECO_FILENAME,
    LAYOUT_MODEL_FILES,
    OCR_MODEL_SIDECARS,
    prefetch_layout_files,
    resolve_layout_source,
    resolve_ocr_models,
    short_revision,
    silence_transformers_load_chatter,
)

__all__ = [
    "DEFAULT_DET_FILENAME",
    "DEFAULT_HF_REPO",
    "DEFAULT_RECO_FILENAME",
    "LAYOUT_MODEL_FILES",
    "OCR_MODEL_SIDECARS",
    "hf_download",
    "prefetch_layout_files",
    "resolve_layout_source",
    "resolve_ocr_models",
    "short_revision",
    "silence_transformers_load_chatter",
    "suppress_hf_unauth_warning",
]
