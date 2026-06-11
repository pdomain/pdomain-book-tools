"""Equivalence tests for detect_page_attributes / detect_page_attributes_from_array.

Verifies that the bytes-accepting and ndarray-accepting entry points return
identical results on the same synthetic fixture image, and that the core
heuristics behave correctly for blank, colour, narrow-content, and normal pages.
"""

from __future__ import annotations

import cv2
import numpy as np
import numpy.typing as npt
import pytest

from pdomain_book_tools.image_processing.page_attributes import (
    PageCharacteristics,
    detect_page_attributes,
    detect_page_attributes_from_array,
)

ImageArray = npt.NDArray[np.uint8]


# ─── Fixture helpers ──────────────────────────────────────────────────────────


def _to_png_bytes(img: ImageArray) -> bytes:
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return bytes(buf.tobytes())


def _blank_page(width: int = 800, height: int = 1200) -> ImageArray:
    """Solid white BGR page — should trigger blank detection."""
    return np.full((height, width, 3), 255, dtype=np.uint8)


def _color_page(width: int = 800, height: int = 1200) -> ImageArray:
    """Page with strong color content — should trigger plate_p detection."""
    img = np.full((height, width, 3), 200, dtype=np.uint8)
    # Fill a large region with highly saturated red to exceed COLOR_SATURATION_FRACTION
    h, w = height, width
    img[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4, 2] = 220  # strong red channel
    img[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4, 0] = 20  # low blue
    img[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4, 1] = 20  # low green
    return img


def _normal_page(width: int = 800, height: int = 1200) -> ImageArray:
    """Page with dark text spanning full width — should be normal/default."""
    img = np.full((height, width, 3), 240, dtype=np.uint8)
    # Add dark horizontal text-like stripes spanning the full width
    for row_start in range(100, height - 100, 60):
        img[row_start : row_start + 8, 50 : width - 50] = 30
    return img


def _narrow_content_page(width: int = 800, height: int = 1200) -> ImageArray:
    """Page where content occupies < 50% of the width — triggers center alignment."""
    img = np.full((height, width, 3), 240, dtype=np.uint8)
    center_x = width // 2
    narrow_half = int(width * 0.2)  # 40% total width — under NARROW_CONTENT_FRACTION
    for row_start in range(100, height - 100, 60):
        img[
            row_start : row_start + 8, center_x - narrow_half : center_x + narrow_half
        ] = 30
    return img


# ─── Core heuristic tests ─────────────────────────────────────────────────────


class TestDetectPageAttributesFromArray:
    def test_blank_page_suggested_type(self) -> None:
        result = detect_page_attributes_from_array(_blank_page())
        assert result.suggested_type == "blank"

    def test_blank_page_confidence_nonzero(self) -> None:
        result = detect_page_attributes_from_array(_blank_page())
        assert result.confidence > 0.0

    def test_color_page_suggested_type(self) -> None:
        result = detect_page_attributes_from_array(_color_page())
        assert result.suggested_type == "plate_p"

    def test_normal_page_suggested_type(self) -> None:
        result = detect_page_attributes_from_array(_normal_page())
        assert result.suggested_type == "normal"

    def test_normal_page_default_alignment(self) -> None:
        result = detect_page_attributes_from_array(_normal_page())
        assert result.suggested_alignment == "default"

    def test_narrow_content_triggers_center_alignment(self) -> None:
        result = detect_page_attributes_from_array(_narrow_content_page())
        assert result.suggested_alignment == "center"
        assert result.suggested_type == "normal"

    def test_returns_page_characteristics_instance(self) -> None:
        result = detect_page_attributes_from_array(_blank_page())
        assert isinstance(result, PageCharacteristics)

    def test_confidence_is_float(self) -> None:
        result = detect_page_attributes_from_array(_normal_page())
        assert isinstance(result.confidence, float)


# ─── Bytes variant tests ──────────────────────────────────────────────────────


class TestDetectPageAttributesBytes:
    def test_bytes_blank_page(self) -> None:
        result = detect_page_attributes(_to_png_bytes(_blank_page()))
        assert result.suggested_type == "blank"

    def test_bytes_color_page(self) -> None:
        result = detect_page_attributes(_to_png_bytes(_color_page()))
        assert result.suggested_type == "plate_p"

    def test_bytes_normal_page(self) -> None:
        result = detect_page_attributes(_to_png_bytes(_normal_page()))
        assert result.suggested_type == "normal"

    def test_invalid_bytes_returns_normal(self) -> None:
        result = detect_page_attributes(b"not an image")
        assert result.suggested_type == "normal"
        assert result.suggested_alignment == "default"

    def test_empty_bytes_returns_normal(self) -> None:
        result = detect_page_attributes(b"")
        assert result.suggested_type == "normal"


# ─── Equivalence tests (bytes path == array path) ────────────────────────────


class TestEquivalence:
    """Prove that the bytes and array entry points produce identical results."""

    @pytest.mark.parametrize(
        "fixture_fn",
        [_blank_page, _color_page, _normal_page, _narrow_content_page],
        ids=["blank", "color", "normal", "narrow"],
    )
    def test_bytes_and_array_match(
        self,
        fixture_fn: type,
    ) -> None:
        img = fixture_fn()
        from_bytes = detect_page_attributes(_to_png_bytes(img))
        from_array = detect_page_attributes_from_array(img)
        assert from_bytes.suggested_type == from_array.suggested_type
        assert from_bytes.suggested_alignment == from_array.suggested_alignment
        assert abs(from_bytes.confidence - from_array.confidence) < 1e-9
