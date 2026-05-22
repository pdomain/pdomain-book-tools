"""Adapter registry — :func:`get_detector` returns a memoised instance.

Memoisation key is ``(adapter_key, device, confidence, checkpoint_path)``.
Switching any of these returns a fresh instance; calling with the same args
returns the cached one. This matters because the model adapter loads a
~132 MB checkpoint and we do not want to reload it per-page.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from logging import getLogger
from typing import TYPE_CHECKING, Any

from pd_book_tools.layout.detector import (
    ContourDetector,
    LayoutDetector,
    NullDetector,
)

if TYPE_CHECKING:
    from pd_book_tools.layout.types import PageLayout

logger = getLogger(__name__)

# Built-in adapter keys — reserved against shadowing by user registrations.
_BUILTIN_KEYS = frozenset({"none", "contour", "pp-doclayout-plus-l"})

# User-registered factory functions, populated by ``register_detector``.
# A factory receives ``(device, confidence, checkpoint_path, **extra_kwargs)``
# and returns a ``LayoutDetector``; the registry wraps the result in
# ``_TimingDetector`` and memoises the same way it does for built-ins.
_DetectorFactory = Callable[..., LayoutDetector]
_USER_DETECTORS: dict[str, _DetectorFactory] = {}


# A tuple whose first elements are (key, device, confidence, checkpoint_path)
# for model adapters; the contour detector encodes its tunable kwargs as
# additional sorted (name, value) pairs at the end so different tunings
# memoise to different instances. Kept as ``tuple`` rather than a strict
# named alias because the trailing kwargs portion is variable-length.
_CacheKey = tuple[Any, ...]
_DETECTOR_CACHE: dict[_CacheKey, LayoutDetector] = {}
# Guards _DETECTOR_CACHE under concurrent access. Without this, two threads
# can both miss the cache and both call _build(); for PPDocLayoutPlusLDetector
# that triggers a double model download (~132 MB) and double VRAM allocation,
# potentially OOMing on smaller GPUs.
_CACHE_LOCK = threading.Lock()


class _TimingDetector:
    """Wrapper that fills ``inference_ms`` on the returned PageLayout."""

    def __init__(self, inner: LayoutDetector) -> None:
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
    checkpoint_path: str | None,
    extra_kwargs: dict[str, Any],
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
    factory = _USER_DETECTORS.get(key)
    if factory is not None:
        return factory(
            device=device,
            confidence=confidence,
            checkpoint_path=checkpoint_path,
            **extra_kwargs,
        )
    raise ValueError(f"Unknown layout detector: {key!r}")


def get_detector(
    key: str,
    device: str = "cpu",
    confidence: float = 0.5,
    checkpoint_path: str | None = None,
    on_error: str = "raise",
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

    ``on_error`` controls how build failures are surfaced. The default
    ``"raise"`` re-raises the underlying exception (network error,
    missing weights, OOM during model load, unknown key) — appropriate
    for CLI flows that should fail fast. ``"log_and_null"`` instead
    logs a single warning and returns a memoised :class:`NullDetector`
    so batch callers (e.g. ``pd-prep-for-pgdp``) can survive transient
    failures and fall back to the geometric reorg path.
    """
    if on_error not in ("raise", "log_and_null"):
        raise ValueError(
            f"get_detector: on_error must be 'raise' or 'log_and_null', "
            f"got {on_error!r}"
        )
    if key == "contour":
        # confidence / checkpoint_path are meaningless for the rule-based
        # contour detector — collapse them to fixed values in the cache
        # key so distinct confidence values don't create distinct cache
        # entries for behaviorally identical instances. The detector's
        # own tunables are what matter, so include them.
        cache_key = (key, device, 0.0, None, *tuple(sorted(detector_kwargs.items())))
    elif key in _USER_DETECTORS:
        # User-registered detectors may take extra kwargs; fold them into
        # the cache key the same way ``contour`` does so distinct tunings
        # memoise to distinct instances.
        cache_key = (
            key,
            device,
            confidence,
            checkpoint_path,
            *tuple(sorted(detector_kwargs.items())),
        )
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
        try:
            inner = _build(key, device, confidence, checkpoint_path, detector_kwargs)
        except Exception as exc:
            if on_error == "log_and_null":
                logger.warning(
                    "get_detector: build failed for key=%r (%s: %s); "
                    "falling back to NullDetector.",
                    key,
                    type(exc).__name__,
                    exc,
                )
                wrapped = _TimingDetector(NullDetector())
                _DETECTOR_CACHE[cache_key] = wrapped
                return wrapped
            raise
        wrapped = _TimingDetector(inner)
        _DETECTOR_CACHE[cache_key] = wrapped
        return wrapped


def clear_detector_cache() -> None:
    """Drop all memoised adapters. Mainly useful in tests."""
    with _CACHE_LOCK:
        _DETECTOR_CACHE.clear()


def register_detector(key: str, factory: _DetectorFactory) -> None:
    """Register a custom layout-detector adapter under ``key``.

    The ``factory`` is called as
    ``factory(device=..., confidence=..., checkpoint_path=..., **extra_kwargs)``
    when :func:`get_detector` first sees a previously-uncached cache key.
    The returned :class:`LayoutDetector` is wrapped in the same timing
    wrapper as built-in adapters and memoised on
    ``(key, device, confidence, checkpoint_path, sorted(extra_kwargs))``.

    Built-in keys (``"none"``, ``"contour"``, ``"pp-doclayout-plus-l"``)
    cannot be shadowed. Registering ``key`` always evicts any cached
    detector entries for that key — whether they came from a previous
    user factory or from an earlier ``get_detector(key,
    on_error="log_and_null")`` fallback — so the next
    :func:`get_detector` call rebuilds with the new factory.

    Intended for downstream projects (e.g. ``pd-ocr-trainer``) that
    produce custom fine-tuned checkpoints needing their own adapter
    keys without modifying this registry's hard-coded chain.
    """
    if not isinstance(key, str) or not key:
        raise ValueError("register_detector: key must be a non-empty string")
    if key in _BUILTIN_KEYS:
        raise ValueError(
            f"register_detector: {key!r} is a built-in detector key and "
            "cannot be overridden"
        )
    if not callable(factory):
        raise TypeError("register_detector: factory must be callable")
    with _CACHE_LOCK:
        _USER_DETECTORS[key] = factory
        # Always evict cached entries for ``key``, regardless of whether a
        # previous factory existed. A prior ``get_detector(key,
        # on_error="log_and_null")`` call could have cached a NullDetector
        # fallback for this (then-unknown) key; if that stale entry is left
        # in place, the newly registered factory would never be used (#168).
        stale = [k for k in _DETECTOR_CACHE if k and k[0] == key]
        for k in stale:
            _DETECTOR_CACHE.pop(k, None)


def unregister_detector(key: str) -> None:
    """Remove a previously-registered custom adapter.

    Built-in keys cannot be unregistered. Unknown keys are silently
    ignored so this is safe to call from test teardown.
    """
    if key in _BUILTIN_KEYS:
        raise ValueError(
            f"unregister_detector: {key!r} is a built-in detector key and "
            "cannot be removed"
        )
    with _CACHE_LOCK:
        if _USER_DETECTORS.pop(key, None) is not None:
            stale = [k for k in _DETECTOR_CACHE if k and k[0] == key]
            for k in stale:
                _DETECTOR_CACHE.pop(k, None)


__all__ = [
    "clear_detector_cache",
    "get_detector",
    "register_detector",
    "unregister_detector",
]
