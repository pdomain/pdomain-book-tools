"""Tests for the no-model detectors and the registry.

The PP-DocLayout adapter is exercised by ``test_pp_doclayout.py``; the
end-to-end smoke test there is gated behind ``pytest.mark.slow`` because
the first run downloads ~132 MB of weights.
"""

import numpy as np
import pytest

from pd_book_tools.layout.detector import ContourDetector, NullDetector
from pd_book_tools.layout.registry import (
    clear_detector_cache,
    get_detector,
)
from pd_book_tools.layout.types import RegionType


@pytest.fixture(autouse=True)
def _reset_registry():
    clear_detector_cache()
    yield
    clear_detector_cache()


def _blank_page(width=1000, height=1500) -> np.ndarray:
    return np.full((height, width, 3), 255, dtype=np.uint8)


def _page_with_filled_rect(
    width=1000,
    height=1500,
    rect=(200, 300, 700, 900),
) -> np.ndarray:
    img = _blank_page(width, height)
    L, T, R, B = rect
    img[T:B, L:R] = 0  # solid black block — looks like an engraving
    return img


class TestNullDetector:
    def test_returns_empty_layout_with_image_dims(self):
        det = NullDetector()
        layout = det.detect(_blank_page(800, 1200))
        assert layout.regions == []
        assert layout.image_width == 800
        assert layout.image_height == 1200
        assert layout.detector == "none"


class TestContourDetector:
    def test_finds_solid_rect(self):
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

    def test_blank_page_no_regions(self):
        det = ContourDetector()
        layout = det.detect(_blank_page())
        assert layout.regions == []
        assert layout.detector == "contour"

    def test_min_area_filter(self):
        img = _blank_page()
        # Tiny 10x10 dot — well under min_area_frac=0.005
        img[100:110, 100:110] = 0
        det = ContourDetector(min_area_frac=0.005)
        layout = det.detect(img)
        assert layout.regions == []


class TestRegistry:
    def test_known_keys(self):
        assert isinstance(get_detector("none"), object)
        assert isinstance(get_detector("contour"), object)

    def test_unknown_key_raises(self):
        with pytest.raises(ValueError, match="Unknown layout detector"):
            get_detector("not-a-real-detector")

    def test_memoised(self):
        a = get_detector("contour")
        b = get_detector("contour")
        assert a is b

    def test_distinct_args_distinct_instances(self):
        # ``device`` is a real cache-key participant for any detector — the
        # underlying instance binds itself to a specific device. (We use the
        # contour detector here because it has no model load; it ignores
        # ``device`` itself, but the registry still keys on it.)
        a = get_detector("contour", device="cpu")
        b = get_detector("contour", device="cuda")
        assert a is not b

    def test_inference_ms_filled_by_wrapper(self):
        det = get_detector("contour")
        layout = det.detect(_page_with_filled_rect())
        assert layout.inference_ms >= 0

    def test_contour_kwargs_forwarded(self):
        # L-34: ContourDetector tunables (min_area_frac, etc.) were
        # silently dropped by _build, leaving callers stuck with the
        # defaults regardless of what they passed.
        det = get_detector("contour", min_area_frac=0.123, close_kernel_px=15)
        # Unwrap the _TimingDetector to inspect the inner detector.
        inner = det._inner
        assert inner.min_area_frac == 0.123
        assert inner.close_kernel_px == 15

    def test_contour_distinct_kwargs_distinct_instances(self):
        # Different tunings must memoise as distinct instances.
        a = get_detector("contour", min_area_frac=0.001)
        b = get_detector("contour", min_area_frac=0.5)
        assert a is not b
        # Same tuning hits the cache.
        c = get_detector("contour", min_area_frac=0.001)
        assert a is c

    def test_contour_confidence_irrelevant_to_cache_key(self):
        # confidence/checkpoint_path are meaningless for the rule-based
        # contour detector; varying them must not churn the cache.
        a = get_detector("contour", confidence=0.5)
        b = get_detector("contour", confidence=0.9)
        assert a is b

    def test_unknown_kwargs_for_model_detector_rejected(self):
        # Don't silently swallow typos for non-contour detectors.
        with pytest.raises(TypeError, match="extra keyword arguments"):
            get_detector("none", min_area_frac=0.01)

    def test_concurrent_get_detector_builds_once(self, monkeypatch):
        # L-33: under concurrent first-time access, two threads could both
        # see a cache miss and both call _build. For the model adapter this
        # means a double 132 MB download and double VRAM allocation. The
        # double-checked-lock fix should funnel concurrent first calls
        # through a single _build invocation.
        import threading

        from pd_book_tools.layout import registry as registry_mod

        clear_detector_cache()
        build_calls = {"n": 0}
        build_started = threading.Event()
        release_build = threading.Event()
        original_build = registry_mod._build

        def slow_build(*args, **kwargs):
            build_calls["n"] += 1
            build_started.set()
            # Hold the lock long enough for other threads to pile up on it.
            release_build.wait(timeout=5.0)
            return original_build(*args, **kwargs)

        monkeypatch.setattr(registry_mod, "_build", slow_build)

        results: list = []

        def caller():
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
