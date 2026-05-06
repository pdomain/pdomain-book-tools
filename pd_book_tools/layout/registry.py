"""Adapter registry — :func:`get_detector` returns a memoised instance.

Memoisation key is ``(adapter_key, device, confidence, checkpoint_path)``.
Switching any of these returns a fresh instance; calling with the same args
returns the cached one. This matters because the model adapter loads a
~132 MB checkpoint and we do not want to reload it per-page.
"""

import threading
import time
from logging import getLogger
from typing import Optional, Tuple

from pd_book_tools.layout.detector import (
    ContourDetector,
    LayoutDetector,
    NullDetector,
)
from pd_book_tools.layout.types import PageLayout

logger = getLogger(__name__)


_CacheKey = Tuple[str, str, float, Optional[str]]
_DETECTOR_CACHE: dict[_CacheKey, LayoutDetector] = {}
# Guards _DETECTOR_CACHE under concurrent access. Without this, two threads
# can both miss the cache and both call _build(); for PPDocLayoutPlusLDetector
# that triggers a double model download (~132 MB) and double VRAM allocation,
# potentially OOMing on smaller GPUs.
_CACHE_LOCK = threading.Lock()


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
    The model adapter pulls in ``transformers>=4.45``, which ships as a
    core dependency (no install extra needed).
    """
    cache_key: _CacheKey = (key, device, confidence, checkpoint_path)
    # Fast path: lock-free read for the common warm-cache case. dict.get is
    # atomic under the GIL, so this is safe.
    cached = _DETECTOR_CACHE.get(cache_key)
    if cached is not None:
        return cached
    # Slow path: serialize the build so concurrent first-time callers don't
    # race into _build(). Re-check under the lock (double-checked locking).
    with _CACHE_LOCK:
        cached = _DETECTOR_CACHE.get(cache_key)
        if cached is not None:
            return cached
        inner = _build(key, device, confidence, checkpoint_path)
        wrapped = _TimingDetector(inner)
        _DETECTOR_CACHE[cache_key] = wrapped
        return wrapped


def clear_detector_cache() -> None:
    """Drop all memoised adapters. Mainly useful in tests."""
    with _CACHE_LOCK:
        _DETECTOR_CACHE.clear()


__all__ = ["clear_detector_cache", "get_detector"]
