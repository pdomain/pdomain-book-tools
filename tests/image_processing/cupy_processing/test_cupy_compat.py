"""Tests for the ``_cupy_compat`` opt-in import shim.

Regression for L-40: ``cupy-cuda12x`` is in ``[project.optional-dependencies]``
under the ``gpu`` extra, so a CPU-only install must be able to:

  1. Import ``pd_book_tools.image_processing.cupy_processing`` and every
     submodule under it without raising ``ImportError`` at module load time.
  2. Get a clear, actionable ``ImportError`` (mentioning ``pip install
     pd-book-tools[gpu]``) when calling any GPU function without cupy
     installed.

These tests simulate the "cupy not installed" state by forcing the import
machinery to raise ``ImportError`` for the ``cupy`` and ``cupyx`` packages,
then re-importing the cupy_processing modules from a clean ``sys.modules``
state. We do NOT touch the live cupy install — both the simulated and real
states must coexist in this test environment so the rest of the GPU test
suite (gated by the ``cupy`` marker) keeps working.
"""

from __future__ import annotations

import builtins
import importlib
import sys

import pytest

# Module names to scrub from sys.modules between simulations so each reload
# re-runs the top-level import code with the current ``import cupy`` shim.
_CUPY_PROCESSING_MODULES = [
    "pd_book_tools.image_processing.cupy_processing",
    "pd_book_tools.image_processing.cupy_processing._cupy_compat",
    "pd_book_tools.image_processing.cupy_processing.canvas",
    "pd_book_tools.image_processing.cupy_processing.colors",
    "pd_book_tools.image_processing.cupy_processing.colorToGray",
    "pd_book_tools.image_processing.cupy_processing.contours",
    "pd_book_tools.image_processing.cupy_processing.crop",
    "pd_book_tools.image_processing.cupy_processing.deskew",
    "pd_book_tools.image_processing.cupy_processing.edge_finding",
    "pd_book_tools.image_processing.cupy_processing.filters",
    "pd_book_tools.image_processing.cupy_processing.invert",
    "pd_book_tools.image_processing.cupy_processing.morph",
    "pd_book_tools.image_processing.cupy_processing.rescale",
    "pd_book_tools.image_processing.cupy_processing.rotate",
    "pd_book_tools.image_processing.cupy_processing.split",
    "pd_book_tools.image_processing.cupy_processing.threshold",
    "pd_book_tools.image_processing.cupy_processing.whitespace",
]


@pytest.fixture
def cupy_unavailable(monkeypatch):
    """Simulate a CPU-only install where ``import cupy`` fails.

    Patches ``builtins.__import__`` to raise ``ImportError`` for any
    ``cupy``-rooted import, and clears the cupy_processing modules from
    ``sys.modules`` so they get re-imported under the simulated state.
    Restores the original sys.modules entries on teardown so the live
    cupy install remains usable for other tests.
    """
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "cupy" or name.startswith("cupy.") or name.startswith("cupyx"):
            raise ImportError(f"simulated: {name} not installed")
        return real_import(name, globals, locals, fromlist, level)

    # Save and remove any pre-imported cupy_processing modules + cupy itself
    # so the next import re-runs their top-level code under the patched import.
    saved: dict[str, object] = {}
    for mod_name in list(sys.modules.keys()):
        if mod_name in _CUPY_PROCESSING_MODULES or mod_name.startswith(
            ("cupy", "cupyx")
        ):
            saved[mod_name] = sys.modules.pop(mod_name)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    yield

    # Teardown: monkeypatch unwinds __import__; restore real cupy modules so
    # subsequent GPU tests in the same session don't see an empty cupy.
    for mod_name in list(sys.modules.keys()):
        if mod_name in _CUPY_PROCESSING_MODULES or mod_name.startswith(
            ("cupy", "cupyx")
        ):
            del sys.modules[mod_name]
    sys.modules.update(saved)


def test_cupy_compat_imports_without_cupy(cupy_unavailable):
    """``_cupy_compat`` itself must import cleanly with cupy missing."""
    compat = importlib.import_module(
        "pd_book_tools.image_processing.cupy_processing._cupy_compat"
    )
    assert compat.cp is None
    assert compat.cupy_available() is False


def test_require_cupy_raises_with_install_hint(cupy_unavailable):
    """``require_cupy()`` must raise ImportError mentioning the gpu extra."""
    compat = importlib.import_module(
        "pd_book_tools.image_processing.cupy_processing._cupy_compat"
    )
    with pytest.raises(ImportError) as excinfo:
        compat.require_cupy()
    msg = str(excinfo.value)
    assert "pd-book-tools[gpu]" in msg
    assert "CuPy" in msg or "cupy" in msg.lower()


@pytest.mark.parametrize("mod_name", _CUPY_PROCESSING_MODULES)
def test_cupy_processing_submodule_imports_without_cupy(cupy_unavailable, mod_name):
    """Every cupy_processing submodule must import cleanly with cupy missing.

    This is the L-40 contract: putting ``cupy-cuda12x`` behind the ``gpu``
    extra is only useful if the package itself can still be imported on
    CPU-only installs. If any submodule has an unguarded top-level
    ``import cupy`` (or top-level use of ``cp.<something>`` that evaluates
    at import time despite ``from __future__ import annotations``), this
    parametrized test will catch it.
    """
    importlib.import_module(mod_name)


def test_calling_gpu_function_without_cupy_raises_install_hint(cupy_unavailable):
    """Calling any public GPU function without cupy must raise the hint.

    Uses ``np_uint8_auto_deskew`` as a representative end-user entry point
    — it goes through the ``require_cupy()`` guard before touching cupy.
    """
    import numpy as np

    deskew = importlib.import_module(
        "pd_book_tools.image_processing.cupy_processing.deskew"
    )
    img = np.zeros((10, 10), dtype=np.uint8)
    with pytest.raises(ImportError) as excinfo:
        deskew.np_uint8_auto_deskew(img)
    assert "pd-book-tools[gpu]" in str(excinfo.value)
