"""Tests for the no-model detectors and the registry.

The PP-DocLayout adapter is exercised by ``test_pp_doclayout.py``; the
end-to-end smoke test there is gated behind ``pytest.mark.slow`` because
the first run downloads ~132 MB of weights.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

import numpy as np
import pytest

from pdomain_book_tools.layout.detector import ContourDetector, NullDetector
from pdomain_book_tools.layout.registry import (
    clear_detector_cache,
    get_detector,
    register_detector,
    unregister_detector,
)
from pdomain_book_tools.layout.types import PageLayout, RegionType

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from typing import NoReturn

    from numpy.typing import NDArray

    from pdomain_book_tools.layout.detector import ImageSource, LayoutDetector


@pytest.fixture(autouse=True)
def reset_registry() -> Iterator[None]:
    clear_detector_cache()
    yield
    clear_detector_cache()


def _blank_page(width: int = 1000, height: int = 1500) -> NDArray[np.uint8]:
    return np.full((height, width, 3), 255, dtype=np.uint8)


def _page_with_filled_rect(
    width: int = 1000,
    height: int = 1500,
    rect: tuple[int, int, int, int] = (200, 300, 700, 900),
) -> NDArray[np.uint8]:
    img = _blank_page(width, height)
    L, T, R, B = rect
    img[T:B, L:R] = 0  # solid black block — looks like an engraving
    return img


class TestNullDetector:
    def test_returns_empty_layout_with_image_dims(self) -> None:
        det = NullDetector()
        layout = det.detect(_blank_page(800, 1200))
        assert layout.regions == []
        assert layout.image_width == 800
        assert layout.image_height == 1200
        assert layout.detector == "none"


class TestContourDetector:
    def test_finds_solid_rect(self) -> None:
        img = _page_with_filled_rect(rect=(200, 300, 700, 900))
        det = ContourDetector()
        layout = det.detect(img)
        assert len(layout.regions) >= 1
        # All regions tagged figure by this adapter.
        assert all(r.type is RegionType.figure for r in layout.regions)
        # The biggest region should roughly match the seeded rectangle.
        biggest = max(layout.regions, key=lambda r: r.area)
        assert 150 <= biggest.L <= 250
        assert 250 <= biggest.T <= 350
        assert 650 <= biggest.R <= 750
        assert 850 <= biggest.B <= 950

    def test_blank_page_no_regions(self) -> None:
        det = ContourDetector()
        layout = det.detect(_blank_page())
        assert layout.regions == []
        assert layout.detector == "contour"

    def test_min_area_filter(self) -> None:
        img = _blank_page()
        # Tiny 10x10 dot — well under min_area_frac=0.005
        img[100:110, 100:110] = 0
        det = ContourDetector(min_area_frac=0.005)
        layout = det.detect(img)
        assert layout.regions == []


class TestRegistry:
    def test_known_keys(self) -> None:
        assert isinstance(get_detector("none"), object)
        assert isinstance(get_detector("contour"), object)

    def test_unknown_key_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown layout detector"):
            get_detector("not-a-real-detector")

    def test_memoised(self) -> None:
        a = get_detector("contour")
        b = get_detector("contour")
        assert a is b

    def test_distinct_args_distinct_instances(self) -> None:
        # ``device`` is a real cache-key participant for any detector — the
        # underlying instance binds itself to a specific device. (We use the
        # contour detector here because it has no model load; it ignores
        # ``device`` itself, but the registry still keys on it.)
        a = get_detector("contour", device="cpu")
        b = get_detector("contour", device="cuda")
        assert a is not b

    def test_inference_ms_filled_by_wrapper(self) -> None:
        det = get_detector("contour")
        layout = det.detect(_page_with_filled_rect())
        assert layout.inference_ms >= 0

    def test_contour_kwargs_forwarded(self) -> None:
        # L-34: ContourDetector tunables (min_area_frac, etc.) were
        # silently dropped by _build, leaving callers stuck with the
        # defaults regardless of what they passed.
        from pdomain_book_tools.layout.registry import _TimingDetector

        det = get_detector("contour", min_area_frac=0.123, close_kernel_px=15)
        # Unwrap the _TimingDetector to inspect the inner detector.
        assert isinstance(det, _TimingDetector)
        inner = det._inner
        assert isinstance(inner, ContourDetector)
        assert inner.min_area_frac == 0.123
        assert inner.close_kernel_px == 15

    def test_contour_distinct_kwargs_distinct_instances(self) -> None:
        # Different tunings must memoise as distinct instances.
        a = get_detector("contour", min_area_frac=0.001)
        b = get_detector("contour", min_area_frac=0.5)
        assert a is not b
        # Same tuning hits the cache.
        c = get_detector("contour", min_area_frac=0.001)
        assert a is c

    def test_contour_confidence_irrelevant_to_cache_key(self) -> None:
        # confidence/checkpoint_path are meaningless for the rule-based
        # contour detector; varying them must not churn the cache.
        a = get_detector("contour", confidence=0.5)
        b = get_detector("contour", confidence=0.9)
        assert a is b

    def test_unknown_kwargs_for_model_detector_rejected(self) -> None:
        # Don't silently swallow typos for non-contour detectors.
        with pytest.raises(TypeError, match="extra keyword arguments"):
            get_detector("none", min_area_frac=0.01)

    def test_concurrent_get_detector_builds_once(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # L-33: under concurrent first-time access, two threads could both
        # see a cache miss and both call _build. For the model adapter this
        # means a double 132 MB download and double VRAM allocation. The
        # double-checked-lock fix should funnel concurrent first calls
        # through a single _build invocation.
        import threading

        from pdomain_book_tools.layout import registry as registry_mod

        clear_detector_cache()
        build_calls = {"n": 0}
        build_started = threading.Event()
        release_build = threading.Event()
        original_build = registry_mod._build

        def slow_build(
            key: str,
            device: str,
            confidence: float,
            checkpoint_path: str | None,
            extra_kwargs: dict[str, object],
        ) -> LayoutDetector:
            build_calls["n"] += 1
            build_started.set()
            # Hold the lock long enough for other threads to pile up on it.
            release_build.wait(timeout=5.0)
            return original_build(
                key, device, confidence, checkpoint_path, extra_kwargs
            )

        monkeypatch.setattr(registry_mod, "_build", slow_build)

        results: list[LayoutDetector] = []

        def caller() -> None:
            results.append(get_detector("contour"))

        threads = [threading.Thread(target=caller) for _ in range(8)]
        for t in threads:
            t.start()
        # Wait for the first thread to enter _build, then let it finish.
        assert build_started.wait(timeout=5.0)
        release_build.set()
        for t in threads:
            t.join(timeout=5.0)

        assert build_calls["n"] == 1
        assert len(results) == 8
        # All callers receive the same memoised instance.
        assert all(r is results[0] for r in results)


class TestDetectorFailureHardening:
    """Detector failure hardening (ROADMAP `Detector failure hardening`).

    ``get_detector(..., on_error=...)`` lets batch callers (e.g.
    ``pdomain-prep-for-pgdp``) survive transient build failures (network,
    OOM, missing weights) by falling back to a ``NullDetector`` instead
    of aborting a long-running run. Default stays ``"raise"`` so the
    CLI's existing fail-fast behaviour is preserved.
    """

    def teardown_method(self, method: Callable[..., object]) -> None:
        for key in ("failing-x", "never-registered-key"):
            with contextlib.suppress(ValueError):
                unregister_detector(key)

    def _failing_factory(self) -> Callable[..., NoReturn]:
        def factory(
            *,
            device: str,
            confidence: float,
            checkpoint_path: str | None,
            **kwargs: object,
        ) -> NoReturn:
            raise RuntimeError("boom — model load failed")

        return factory

    def test_default_on_error_raises(self) -> None:
        register_detector("failing-x", self._failing_factory())
        with pytest.raises(RuntimeError, match="boom"):
            get_detector("failing-x")

    def test_explicit_on_error_raise(self) -> None:
        register_detector("failing-x", self._failing_factory())
        with pytest.raises(RuntimeError, match="boom"):
            get_detector("failing-x", on_error="raise")

    def test_on_error_log_and_null_returns_null_detector(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging

        register_detector("failing-x", self._failing_factory())
        with caplog.at_level(
            logging.WARNING, logger="pdomain_book_tools.layout.registry"
        ):
            det = get_detector("failing-x", on_error="log_and_null")
        # Wrapped in _TimingDetector but exposes a NullDetector inner.
        assert det is not None
        layout = det.detect(_blank_page(100, 200))
        assert layout.regions == []
        assert layout.image_width == 100
        assert layout.image_height == 200
        # Logged once.
        assert any("failing-x" in rec.message for rec in caplog.records)

    def test_on_error_log_and_null_does_not_cache_fallback(self) -> None:
        # Remediation (a): fallback NullDetectors must NOT be stored in the
        # cache so a later on_error="raise" call for the same key is not
        # silently poisoned (#167).  Two successive log_and_null calls will
        # each retry the build (and fail again), returning independent
        # NullDetector wrappers rather than one cached instance.
        register_detector("failing-x", self._failing_factory())
        det_a = get_detector("failing-x", on_error="log_and_null")
        det_b = get_detector("failing-x", on_error="log_and_null")
        # Not cached — distinct objects (each is a fresh _TimingDetector).
        assert det_a is not det_b

    def test_failure_then_raise_gets_exception_not_cached_null(self) -> None:
        """Cache-poisoning regression: a prior log_and_null call must not
        silently feed a NullDetector to a later on_error='raise' call (#167).
        """
        register_detector("failing-x", self._failing_factory())
        # First call: soft failure, logs and returns NullDetector.
        _ = get_detector("failing-x", on_error="log_and_null")
        # Second call with same key + on_error="raise" must NOT return the
        # cached NullDetector — it must propagate the build error.
        with pytest.raises(RuntimeError, match="boom"):
            get_detector("failing-x", on_error="raise")

    def test_unknown_key_log_and_null_then_raise_gets_exception(self) -> None:
        """Unknown-key fallback must not poison a later raise call (#167).

        Before the fix, get_detector(unknown, on_error='log_and_null') cached
        a NullDetector, and get_detector(unknown, on_error='raise') silently
        returned it instead of raising ValueError.
        """
        # First call: unknown key, soft fallback.
        _ = get_detector("never-registered-key", on_error="log_and_null")
        # Second call: same unknown key, strict — must raise, not return null.
        with pytest.raises(ValueError, match="Unknown layout detector"):
            get_detector("never-registered-key", on_error="raise")

    def test_on_error_invalid_value_raises(self) -> None:
        with pytest.raises(ValueError, match="on_error"):
            get_detector("contour", on_error="silent")

    def test_unknown_key_with_log_and_null_still_falls_back(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging

        with caplog.at_level(
            logging.WARNING, logger="pdomain_book_tools.layout.registry"
        ):
            det = get_detector("nonexistent-detector", on_error="log_and_null")
        layout = det.detect(_blank_page(50, 80))
        assert layout.regions == []
        assert layout.image_width == 50

    def test_register_after_fallback_evicts_stale_null_detector(self) -> None:
        """Registering a detector after a cached ``log_and_null`` fallback
        must evict the stale ``NullDetector`` so the new factory is used.

        Regression for #168: ``register_detector`` previously only evicted
        cached entries when *replacing* a prior user factory. A first-time
        registration left a fallback cached by an earlier
        ``get_detector(key, on_error="log_and_null")`` call in place.
        """
        # No factory registered yet — fallback to NullDetector and cache it.
        fallback = get_detector("failing-x", on_error="log_and_null")
        layout = fallback.detect(_blank_page(10, 10))
        assert layout.regions == []  # NullDetector returns no regions

        # Now register a real factory for the same key for the first time.
        sentinel = object()

        class _RealDetector:
            marker = sentinel

            def detect(self, source: ImageSource) -> PageLayout:
                return PageLayout(regions=[], image_width=1, image_height=1)

        def factory(
            *,
            device: str,
            confidence: float,
            checkpoint_path: str | None,
            **kwargs: object,
        ) -> _RealDetector:
            return _RealDetector()

        register_detector("failing-x", factory)

        # The next get_detector must build with the new factory, not return
        # the stale cached NullDetector.
        from pdomain_book_tools.layout.registry import _TimingDetector

        det = get_detector("failing-x")
        assert isinstance(det, _TimingDetector)
        assert getattr(det._inner, "marker", None) is sentinel

    def test_timing_detector_per_page_failure_routes_through_caller(self) -> None:
        """Per-page detect() failures are not swallowed inside the registry —
        callers (``_TimingDetector`` wrapping the user inner) propagate so
        the consumer can decide whether to swallow per-page exceptions.
        """
        from pdomain_book_tools.layout.registry import _TimingDetector

        class _Boom:
            def detect(self, source: ImageSource) -> NoReturn:
                raise RuntimeError("OOM mid-batch")

        wrapped = _TimingDetector(_Boom())
        with pytest.raises(RuntimeError, match="OOM"):
            wrapped.detect(_blank_page(10, 10))


class TestRegisterDetector:
    """R-25: ``register_detector`` allows downstream projects (e.g.
    ``pdomain-ocr-training``) to plug in custom adapter keys without modifying
    the registry's hard-coded chain."""

    def teardown_method(self, method: Callable[..., object]) -> None:
        # Each test registers its own keys; clean up so they don't leak.
        for key in ("custom-x", "custom-y"):
            with contextlib.suppress(ValueError):
                unregister_detector(key)

    def _make_factory(
        self, calls: list[tuple[str, float, str | None, dict[str, object]]]
    ) -> Callable[..., LayoutDetector]:
        def factory(
            *,
            device: str,
            confidence: float,
            checkpoint_path: str | None,
            **kwargs: object,
        ) -> LayoutDetector:
            calls.append((device, confidence, checkpoint_path, dict(kwargs)))

            class _Stub:
                def detect(self, source: ImageSource) -> PageLayout:
                    return PageLayout(
                        regions=[],
                        image_width=10,
                        image_height=10,
                        detector="custom-x",
                    )

            return _Stub()

        return factory

    def test_register_then_get(self) -> None:
        calls: list[tuple[str, float, str | None, dict[str, object]]] = []
        register_detector("custom-x", self._make_factory(calls))
        det = get_detector("custom-x", device="cpu", confidence=0.7)
        assert det is not None
        # Factory invoked once with the forwarded args.
        assert calls == [("cpu", 0.7, None, {})]

    def test_register_memoises_per_kwargs(self) -> None:
        calls: list[tuple[str, float, str | None, dict[str, object]]] = []
        register_detector("custom-x", self._make_factory(calls))
        a = get_detector("custom-x", scale=1)
        b = get_detector("custom-x", scale=1)
        c = get_detector("custom-x", scale=2)
        assert a is b
        assert a is not c
        assert len(calls) == 2

    def test_register_rejects_builtin_keys(self) -> None:
        def _unused_factory(**_: object) -> LayoutDetector:
            return NullDetector()

        for key in ("none", "contour", "pp-doclayout-plus-l"):
            with pytest.raises(ValueError, match="built-in"):
                register_detector(key, _unused_factory)

    def test_non_hashable_kwargs_raise_type_error(self) -> None:
        # #179: passing a dict or list as a kwarg value for a user-registered
        # detector used to raise a confusing TypeError deep inside
        # _DETECTOR_CACHE.get() because the cache key tuple was unhashable.
        # Should now raise TypeError with a clear message before touching
        # the cache.
        register_detector("custom-x", self._make_factory([]))
        with pytest.raises(TypeError, match="hashable"):
            get_detector("custom-x", filters={"a": 1})
        with pytest.raises(TypeError, match="hashable"):
            get_detector("custom-x", items=[1, 2, 3])

    def test_register_requires_callable(self) -> None:
        with pytest.raises(TypeError, match="callable"):
            register_detector("custom-x", "not-callable")  # type: ignore[arg-type]

    def test_register_requires_nonempty_key(self) -> None:
        def _unused_factory(**_: object) -> LayoutDetector:
            return NullDetector()

        with pytest.raises(ValueError, match="non-empty"):
            register_detector("", _unused_factory)

    def test_re_register_replaces_and_clears_cache(self) -> None:
        calls_a: list[tuple[str, float, str | None, dict[str, object]]] = []
        calls_b: list[tuple[str, float, str | None, dict[str, object]]] = []
        register_detector("custom-x", self._make_factory(calls_a))
        get_detector("custom-x")
        # Replace factory; previously-cached instance must be evicted so
        # the next call goes through the new factory.
        register_detector("custom-x", self._make_factory(calls_b))
        get_detector("custom-x")
        assert len(calls_a) == 1
        assert len(calls_b) == 1

    def test_unregister_drops_cache_and_makes_key_unknown(self) -> None:
        register_detector("custom-x", self._make_factory([]))
        get_detector("custom-x")
        unregister_detector("custom-x")
        with pytest.raises(ValueError, match="Unknown layout detector"):
            get_detector("custom-x")

    def test_unregister_unknown_key_is_noop(self) -> None:
        # Safe to call from teardown without tracking what was registered.
        unregister_detector("never-registered")

    def test_unregister_rejects_builtin(self) -> None:
        with pytest.raises(ValueError, match="built-in"):
            unregister_detector("contour")
