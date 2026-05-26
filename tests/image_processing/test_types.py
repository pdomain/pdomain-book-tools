"""Tests for backend-neutral image_processing types (M-27).

Both cv2_processing and cupy_processing canvas modules historically used
the `Alignment` enum from `cv2_processing.canvas`, which forced
`cupy_processing.canvas` to import the cv2 backend at module load. This
defeated backend independence: importing the cupy canvas pulled cv2 in.

The fix moves `Alignment` to `pdomain_book_tools.image_processing.types`. The
cv2 module re-exports `Alignment` from there for backward compatibility,
and the cupy module imports it directly from the neutral location.
"""

import importlib
import sys


def test_alignment_canonical_location():
    """`Alignment` is defined in the backend-neutral types module."""
    from pdomain_book_tools.image_processing.types import Alignment

    assert Alignment.TOP.value == "top"
    assert Alignment.CENTER.value == "center"
    assert Alignment.BOTTOM.value == "bottom"
    assert Alignment.DEFAULT.value == "default"


def test_alignment_re_exported_from_cv2_canvas_for_back_compat():
    """Existing callers of the cv2 module's `Alignment` keep working —
    same identity object, no shadow class."""
    from pdomain_book_tools.image_processing.cv2_processing.canvas import (
        Alignment as Alignment_cv2,
    )
    from pdomain_book_tools.image_processing.types import Alignment as Alignment_neutral

    assert Alignment_cv2 is Alignment_neutral


def test_cupy_canvas_does_not_import_cv2_backend():
    """Importing cupy_processing.canvas must NOT load cv2_processing.canvas
    (the M-27 cross-backend coupling)."""
    # Drop both modules from cache so we observe a fresh import graph.
    for mod_name in list(sys.modules):
        if mod_name in {
            "pdomain_book_tools.image_processing.cupy_processing.canvas",
            "pdomain_book_tools.image_processing.cv2_processing.canvas",
        }:
            del sys.modules[mod_name]

    # Skip if cupy is unavailable in this environment — the import-graph
    # invariant is what we care about, and that can only be observed when
    # the cupy module successfully loads.
    try:
        importlib.import_module(
            "pdomain_book_tools.image_processing.cupy_processing.canvas"
        )
    except ImportError:
        import pytest

        pytest.skip("cupy not available in this environment")

    assert (
        "pdomain_book_tools.image_processing.cv2_processing.canvas" not in sys.modules
    ), (
        "cupy_processing.canvas should not transitively import "
        "cv2_processing.canvas (M-27)."
    )


def test_alignment_same_identity_across_backends():
    """The cupy backend's `Alignment` reference is the same object as the
    cv2 backend's and the neutral types module's — guards against a future
    refactor accidentally re-defining the enum in one of the backends."""
    from pdomain_book_tools.image_processing.cupy_processing import (
        canvas as cupy_canvas,
    )
    from pdomain_book_tools.image_processing.cv2_processing import canvas as cv2_canvas
    from pdomain_book_tools.image_processing.types import Alignment as Alignment_neutral

    assert cupy_canvas.Alignment is Alignment_neutral
    assert cv2_canvas.Alignment is Alignment_neutral
