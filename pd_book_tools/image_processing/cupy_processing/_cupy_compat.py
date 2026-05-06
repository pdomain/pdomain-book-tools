"""Guarded CuPy import helper.

CuPy is an opt-in dependency (see the ``gpu`` extra in ``pyproject.toml``).
Importing any module under ``pd_book_tools.image_processing.cupy_processing``
on a CPU-only install must not crash at import time, but calling a GPU
function without the GPU extra installed should raise a clear, actionable
``ImportError``.

Pattern, used by every module in this package:

    from __future__ import annotations  # so cp.ndarray annotations don't evaluate

    from ._cupy_compat import cp, require_cupy

    def my_gpu_fn(img_cp: cp.ndarray) -> cp.ndarray:
        require_cupy()
        ...

If CuPy is installed, ``cp`` is the real ``cupy`` module. If not, ``cp`` is
``None`` and ``require_cupy()`` raises with install instructions.
"""

from __future__ import annotations

GPU_EXTRA_INSTALL_HINT = (
    "CuPy/CUDA is required for pd_book_tools GPU functionality. "
    "Install with: pip install 'pd-book-tools[gpu]' "
    "(requires CUDA 12 toolkit and a compatible NVIDIA GPU)."
)

try:
    import cupy as cp  # type: ignore[import-not-found]

    _CUPY_AVAILABLE = True
    _CUPY_IMPORT_ERROR: ImportError | None = None
except ImportError as _exc:  # pragma: no cover - exercised only on CPU-only installs
    cp = None  # type: ignore[assignment]
    _CUPY_AVAILABLE = False
    _CUPY_IMPORT_ERROR = _exc


def require_cupy() -> None:
    """Raise a clear ImportError if CuPy is not installed.

    Call from the top of any function that needs CuPy at runtime. Cheap when
    CuPy is available (one boolean check); informative when it isn't.
    """
    if not _CUPY_AVAILABLE:
        raise ImportError(GPU_EXTRA_INSTALL_HINT) from _CUPY_IMPORT_ERROR


def cupy_available() -> bool:
    """Whether CuPy was successfully imported. Useful for runtime branching."""
    return _CUPY_AVAILABLE


__all__ = ["cp", "require_cupy", "cupy_available", "GPU_EXTRA_INSTALL_HINT"]
