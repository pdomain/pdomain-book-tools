"""Adapter registry — :func:`get_detector` returns a memoised instance.

Memoisation key is ``(adapter_key, device, confidence, checkpoint_path)``.
Switching any of these returns a fresh instance; calling with the same args
returns the cached one. This matters because the model adapter loads a
~132 MB checkpoint and we do not want to reload it per-page.
"""

import threading
import time
from logging import getLogger
from typing import Any, Optional, Tuple

from pd_book_tools.layout.detector import (
    ContourDetector,
    LayoutDetector,
    NullDetector,
)
from pd_book_tools.layout.types import PageLayout

logger = getLogger(__name__)


# A tuple whose first elements are (key, device, confidence, checkpoint_path)
# for model adapters; the contour detector encodes its tunable kwargs as
# additional sorted (name, value) pairs at the end so different tunings
# memoise to different instances. Kept as ``tuple`` rather than a strict
# named alias because the trailing kwargs portion is variable-length.
_CacheKey = Tuple[Any, ...]
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


_CONTOUR_DETECTOR_KWARGS = (
    "min_area_frac",
    "max_area_frac",
    "min_aspect",
    "max_aspect",
    "close_kernel_px",
)


def _build(
    key: str,
    device: str,
    confidence: float,
    checkpoint_path: Optional[str],
    extra_kwargs: dict,
) -> LayoutDetector:
    if key == "none":
        return NullDetector()
    if key == "contour":
        contour_kwargs = {
            k: v for k, v in extra_kwargs.items() if k in _CONTOUR_DETECTOR_KWARGS
        }
        unknown = set(extra_kwargs) - set(_CONTOUR_DETECTOR_KWARGS)
        if unknown:
            raise TypeError(
                f"ContourDetector got unexpected keyword arguments: {sorted(unknown)}"
            )
        return ContourDetector(**contour_kwargs)
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
    **detector_kwargs,
) -> LayoutDetector:
    """Return a memoised detector instance for ``key``.

    Available keys: ``"none"``, ``"contour"``, ``"pp-doclayout-plus-l"``.
    The model adapter pulls in ``transformers>=4.45``, which ships as a
    core dependency (no install extra needed).

    For ``"contour"``, ``confidence`` and ``checkpoint_path`` are unused
    and intentionally do not participate in the cache key (so callers
    that vary them by mistake don't churn the cache with behaviorally
    identical instances). Tuning kwargs (``min_area_frac``,
    ``max_area_frac``, ``min_aspect``, ``max_aspect``, ``close_kernel_px``)
    are forwarded to ``ContourDetector`` and *do* participate in the
    cache key.
    """
    if key == "contour":
        # confidence / checkpoint_path are meaningless for the rule-based
        # contour detector — collapse them to fixed values in the cache
        # key so distinct confidence values don't create distinct cache
        # entries for behaviorally identical instances. The detector's
        # own tunables are what matter, so include them.
        cache_key = (
            key,
            device,
            0.0,
            None,
        ) + tuple(sorted(detector_kwargs.items()))
    else:
        if detector_kwargs:
            raise TypeError(
                f"get_detector({key!r}, ...) does not accept extra "
                f"keyword arguments: {sorted(detector_kwargs)}"
            )
        cache_key = (key, device, confidence, checkpoint_path)
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
        inner = _build(key, device, confidence, checkpoint_path, detector_kwargs)
        wrapped = _TimingDetector(inner)
        _DETECTOR_CACHE[cache_key] = wrapped
        return wrapped


def clear_detector_cache() -> None:
    """Drop all memoised adapters. Mainly useful in tests."""
    with _CACHE_LOCK:
        _DETECTOR_CACHE.clear()


__all__ = ["clear_detector_cache", "get_detector"]
