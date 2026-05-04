"""Adapter registry — :func:`get_detector` returns a memoised instance.

Memoisation key is ``(adapter_key, device, confidence, checkpoint_path)``.
Switching any of these returns a fresh instance; calling with the same args
returns the cached one. This matters because the model adapter loads a
~132 MB checkpoint and we do not want to reload it per-page.
"""

import time
from logging import getLogger
from typing import Optional, Tuple

from pd_book_tools.layout.detector import (
    ContourDetector,
    LayoutDetector,
    NullDetector,
    _load_image,
)
from pd_book_tools.layout.types import PageLayout

logger = getLogger(__name__)


_CacheKey = Tuple[str, str, float, Optional[str]]
_DETECTOR_CACHE: dict[_CacheKey, LayoutDetector] = {}


class _TimingDetector:
    """Wrapper that fills ``inference_ms`` on the returned PageLayout."""

    def __init__(self, inner: LayoutDetector):
        self._inner = inner

    def detect(self, source) -> PageLayout:
        start = time.monotonic()
        layout = self._inner.detect(source)
        elapsed_ms = int((time.monotonic() - start) * 1000)
        if layout.inference_ms == 0:
            layout.inference_ms = elapsed_ms
        return layout


def _build(
    key: str,
    device: str,
    confidence: float,
    checkpoint_path: Optional[str],
) -> LayoutDetector:
    if key == "none":
        return NullDetector()
    if key == "contour":
        return ContourDetector()
    if key == "pp-doclayout-plus-l":
        from pd_book_tools.layout.adapters.pp_doclayout import (
            PPDocLayoutPlusLDetector,
        )

        return PPDocLayoutPlusLDetector(
            device=device,
            confidence=confidence,
            checkpoint_path=checkpoint_path,
        )
    raise ValueError(f"Unknown layout detector: {key!r}")


def get_detector(
    key: str,
    device: str = "cpu",
    confidence: float = 0.5,
    checkpoint_path: Optional[str] = None,
) -> LayoutDetector:
    """Return a memoised detector instance for ``key``.

    Available keys: ``"none"``, ``"contour"``, ``"pp-doclayout-plus-l"``.
    The model adapter requires the ``[layout]`` extra (``transformers>=4.45``).
    """
    cache_key: _CacheKey = (key, device, confidence, checkpoint_path)
    cached = _DETECTOR_CACHE.get(cache_key)
    if cached is not None:
        return cached
    inner = _build(key, device, confidence, checkpoint_path)
    wrapped = _TimingDetector(inner)
    _DETECTOR_CACHE[cache_key] = wrapped
    return wrapped


def clear_detector_cache() -> None:
    """Drop all memoised adapters. Mainly useful in tests."""
    _DETECTOR_CACHE.clear()


__all__ = ["clear_detector_cache", "get_detector"]


# Re-exported so adapters can share the helper without importing _detector_internal.
_ = _load_image
