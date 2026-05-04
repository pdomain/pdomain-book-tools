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
        a = get_detector("contour", confidence=0.5)
        b = get_detector("contour", confidence=0.7)
        assert a is not b

    def test_inference_ms_filled_by_wrapper(self):
        det = get_detector("contour")
        layout = det.detect(_page_with_filled_rect())
        assert layout.inference_ms >= 0
