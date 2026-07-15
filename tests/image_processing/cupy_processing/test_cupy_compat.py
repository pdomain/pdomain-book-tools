"""Tests for the ``_cupy_compat`` opt-in import shim.

Regression for L-40: ``cupy-cuda12x`` is in ``[project.optional-dependencies]``
under the ``gpu`` extra, so a CPU-only install must be able to:

  1. Import ``pdomain_book_tools.image_processing.cupy_processing`` and every
     submodule under it without raising ``ImportError`` at module load time.
  2. Get a clear, actionable ``ImportError`` (mentioning ``pip install
     pdomain-book-tools[gpu]``) when calling any GPU function without cupy
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
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator, Mapping, Sequence
    from types import ModuleType

# Module names to scrub from sys.modules between simulations so each reload
# re-runs the top-level import code with the current ``import cupy`` shim.
_CUPY_PROCESSING_MODULES = [
    "pdomain_book_tools.image_processing.cupy_processing",
    "pdomain_book_tools.image_processing.cupy_processing._cupy_compat",
    "pdomain_book_tools.image_processing.cupy_processing.canvas",
    "pdomain_book_tools.image_processing.cupy_processing.colors",
    "pdomain_book_tools.image_processing.cupy_processing.color_to_gray",
    "pdomain_book_tools.image_processing.cupy_processing.contours",
    "pdomain_book_tools.image_processing.cupy_processing.crop",
    "pdomain_book_tools.image_processing.cupy_processing.deskew",
    "pdomain_book_tools.image_processing.cupy_processing.denoise",
    "pdomain_book_tools.image_processing.cupy_processing.edge_finding",
    "pdomain_book_tools.image_processing.cupy_processing.filters",
    "pdomain_book_tools.image_processing.cupy_processing.invert",
    "pdomain_book_tools.image_processing.cupy_processing.morph",
    "pdomain_book_tools.image_processing.cupy_processing.rescale",
    "pdomain_book_tools.image_processing.cupy_processing.rotate",
    "pdomain_book_tools.image_processing.cupy_processing.split",
    "pdomain_book_tools.image_processing.cupy_processing.threshold",
    "pdomain_book_tools.image_processing.cupy_processing.whitespace",
]


@pytest.fixture
def cupy_unavailable(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    """Simulate a CPU-only install where ``import cupy`` fails.

    Patches ``builtins.__import__`` to raise ``ImportError`` for any
    ``cupy``-rooted import, and clears the cupy_processing modules from
    ``sys.modules`` so they get re-imported under the simulated state.
    Restores the original sys.modules entries on teardown so the live
    cupy install remains usable for other tests.
    """
    real_import = builtins.__import__

    def fake_import(
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] | None = (),
        level: int = 0,
    ) -> ModuleType:
        if name == "cupy" or name.startswith("cupy.") or name.startswith("cupyx"):
            raise ImportError(f"simulated: {name} not installed")
        return real_import(name, globals, locals, fromlist, level)

    # Save and remove any pre-imported cupy_processing modules + cupy itself
    # so the next import re-runs their top-level code under the patched import.
    saved: dict[str, ModuleType] = {}
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


def test_cupy_compat_imports_without_cupy(cupy_unavailable: None) -> None:
    """``_cupy_compat`` itself must import cleanly with cupy missing."""
    compat = importlib.import_module(
        "pdomain_book_tools.image_processing.cupy_processing._cupy_compat"
    )
    assert compat.cp is None
    assert compat.cupy_available() is False


def test_require_cupy_raises_with_install_hint(cupy_unavailable: None) -> None:
    """``require_cupy()`` must raise ImportError mentioning the gpu extra."""
    compat = importlib.import_module(
        "pdomain_book_tools.image_processing.cupy_processing._cupy_compat"
    )
    with pytest.raises(ImportError) as excinfo:
        compat.require_cupy()
    msg = str(excinfo.value)
    assert "pdomain-book-tools[gpu]" in msg
    assert "CuPy" in msg or "cupy" in msg.lower()


@pytest.mark.parametrize("mod_name", _CUPY_PROCESSING_MODULES)
def test_cupy_processing_submodule_imports_without_cupy(
    cupy_unavailable: None, mod_name: str
) -> None:
    """Every cupy_processing submodule must import cleanly with cupy missing.

    This is the L-40 contract: putting ``cupy-cuda12x`` behind the ``gpu``
    extra is only useful if the package itself can still be imported on
    CPU-only installs. If any submodule has an unguarded top-level
    ``import cupy`` (or top-level use of ``cp.<something>`` that evaluates
    at import time despite ``from __future__ import annotations``), this
    parametrized test will catch it.
    """
    importlib.import_module(mod_name)


def test_calling_gpu_function_without_cupy_raises_install_hint(
    cupy_unavailable: None,
) -> None:
    """Calling any public GPU function without cupy must raise the hint.

    Uses ``np_uint8_auto_deskew`` as a representative end-user entry point
    — it goes through the ``require_cupy()`` guard before touching cupy.
    """
    import numpy as np

    deskew = importlib.import_module(
        "pdomain_book_tools.image_processing.cupy_processing.deskew"
    )
    img = np.zeros((10, 10), dtype=np.uint8)
    with pytest.raises(ImportError) as excinfo:
        deskew.np_uint8_auto_deskew(img)
    assert "pdomain-book-tools[gpu]" in str(excinfo.value)
