"""Equivalence tests for auto_detect_illustrations_from_array.

Verifies that passing an ndarray directly to auto_detect_illustrations_from_array
yields identical results to passing the same image via a file path
(after saving to disk), confirming no encode/decode round-trip loss.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import cv2

if TYPE_CHECKING:
    from pathlib import Path
import numpy as np
import numpy.typing as npt

from pdomain_book_tools.layout.detector import ContourDetector, NullDetector
from pdomain_book_tools.layout.ndarray_detection import (
    auto_detect_illustrations_from_array,
)
from pdomain_book_tools.layout.types import PageLayout, RegionType

ImageArray = npt.NDArray[np.uint8]


# ─── Fixture helpers ──────────────────────────────────────────────────────────


def _blank_page(width: int = 800, height: int = 1200) -> ImageArray:
    return np.full((height, width, 3), 255, dtype=np.uint8)


def _page_with_figure(
    width: int = 800,
    height: int = 1200,
    rect: tuple[int, int, int, int] = (200, 300, 600, 900),
) -> ImageArray:
    """Page with a solid dark rectangle that ContourDetector will find as a figure."""
    img = _blank_page(width, height)
    l, t, r, b = rect
    img[t:b, l:r] = 0
    return img


# ─── Core behaviour tests ─────────────────────────────────────────────────────


class TestAutoDetectIllustrationsFromArray:
    def test_blank_page_returns_empty(self) -> None:
        result = auto_detect_illustrations_from_array(
            _blank_page(), layout_detector=ContourDetector(), confidence_threshold=0.5
        )
        assert result.regions == []

    def test_page_with_figure_returns_regions(self) -> None:
        result = auto_detect_illustrations_from_array(
            _page_with_figure(),
            layout_detector=ContourDetector(),
            confidence_threshold=0.5,
        )
        assert len(result.regions) >= 1

    def test_none_detector_returns_empty(self) -> None:
        result = auto_detect_illustrations_from_array(
            _page_with_figure(), layout_detector=None, confidence_threshold=0.5
        )
        assert result.regions == []

    def test_null_detector_returns_empty(self) -> None:
        result = auto_detect_illustrations_from_array(
            _page_with_figure(),
            layout_detector=NullDetector(),
            confidence_threshold=0.5,
        )
        assert result.regions == []

    def test_confidence_threshold_filters_low_confidence(self) -> None:
        """Regions whose confidence is below the threshold are excluded."""

        class _LowConfidenceDetector:
            def detect(self, source: object) -> PageLayout:
                from pdomain_book_tools.layout.types import LayoutRegion

                return PageLayout(
                    regions=[
                        LayoutRegion(
                            type=RegionType.figure,
                            L=100,
                            T=100,
                            R=400,
                            B=600,
                            confidence=0.3,
                            raw_label="test",
                        )
                    ],
                    image_width=800,
                    image_height=1200,
                    detector="test",
                )

        result = auto_detect_illustrations_from_array(
            _blank_page(),
            layout_detector=_LowConfidenceDetector(),
            confidence_threshold=0.5,
        )
        assert result.regions == []

    def test_confidence_threshold_keeps_high_confidence(self) -> None:
        """Regions whose confidence meets or exceeds the threshold are kept."""

        class _HighConfidenceDetector:
            def detect(self, source: object) -> PageLayout:
                from pdomain_book_tools.layout.types import LayoutRegion

                return PageLayout(
                    regions=[
                        LayoutRegion(
                            type=RegionType.figure,
                            L=100,
                            T=100,
                            R=400,
                            B=600,
                            confidence=0.8,
                            raw_label="test",
                        )
                    ],
                    image_width=800,
                    image_height=1200,
                    detector="test",
                )

        result = auto_detect_illustrations_from_array(
            _blank_page(),
            layout_detector=_HighConfidenceDetector(),
            confidence_threshold=0.5,
        )
        assert len(result.regions) == 1

    def test_returns_page_layout(self) -> None:
        result = auto_detect_illustrations_from_array(
            _blank_page(), layout_detector=ContourDetector(), confidence_threshold=0.5
        )
        assert isinstance(result, PageLayout)

    def test_text_regions_excluded(self) -> None:
        """Regions of type 'text' must not appear in the output."""

        class _TextDetector:
            def detect(self, source: object) -> PageLayout:
                from pdomain_book_tools.layout.types import LayoutRegion

                return PageLayout(
                    regions=[
                        LayoutRegion(
                            type=RegionType.text,
                            L=10,
                            T=10,
                            R=100,
                            B=200,
                            confidence=1.0,
                            raw_label="text",
                        )
                    ],
                    image_width=800,
                    image_height=1200,
                    detector="test",
                )

        result = auto_detect_illustrations_from_array(
            _blank_page(),
            layout_detector=_TextDetector(),
            confidence_threshold=0.0,
        )
        assert result.regions == []


# ─── Equivalence tests (path == array) ───────────────────────────────────────


class TestPathArrayEquivalence:
    """Prove that calling via a saved file path and via an ndarray give identical output."""

    def test_blank_page_path_vs_array(self, tmp_path: Path) -> None:
        img = _blank_page()
        img_file = tmp_path / "blank.png"
        cv2.imwrite(str(img_file), img)

        detector = ContourDetector()
        from_path = detector.detect(img_file)
        from_array_layout = auto_detect_illustrations_from_array(
            img, layout_detector=detector, confidence_threshold=0.0
        )

        assert len(from_path.regions) == len(from_array_layout.regions)

    def test_figure_page_path_vs_array(self, tmp_path: Path) -> None:
        img = _page_with_figure()
        img_file = tmp_path / "figure.png"
        cv2.imwrite(str(img_file), img)

        detector = ContourDetector()
        from_path = detector.detect(img_file)
        from_array_layout = auto_detect_illustrations_from_array(
            img, layout_detector=detector, confidence_threshold=0.0
        )

        # Same number of regions detected.
        assert len(from_path.regions) == len(from_array_layout.regions)

        # Bounding boxes are identical (both paths avoid any encode/decode loss).
        for path_region, array_region in zip(
            from_path.regions, from_array_layout.regions, strict=True
        ):
            assert path_region.L == array_region.L
            assert path_region.T == array_region.T
            assert path_region.R == array_region.R
            assert path_region.B == array_region.B
            assert path_region.type == array_region.type
