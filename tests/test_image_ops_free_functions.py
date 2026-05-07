"""Free-function image-op tests (R-01 / R-03).

The R-01/R-03 deprecation-overlap shape: free functions in
``pd_book_tools.geometry.image_ops`` (BoundingBox-level) and
``pd_book_tools.ocr.image_utilities`` (Word/Block/Page-level) are the
canonical surface; the corresponding methods are preserved as thin
wrappers for backward compatibility.

These tests assert:

1. The free functions produce the same results as the methods on the
   same input (parity).
2. Mutate-in-place semantics are preserved by the free functions
   (``crop_word_bottom`` mutates ``word.bounding_box`` etc.).
"""

from __future__ import annotations

import numpy as np
import pytest

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.geometry.image_ops import (
    crop_bottom_bbox,
    crop_top_bbox,
    refine_bbox,
)
from pd_book_tools.ocr.image_utilities import (
    crop_word_bottom,
    crop_word_top,
    refine_word_bbox,
)
from pd_book_tools.ocr.word import Word


def _make_text_image() -> np.ndarray:
    """Build a 50x50 image with a black rectangle of "ink" near the bottom."""
    img = np.full((50, 50), 255, dtype=np.uint8)
    img[20:35, 5:45] = 0
    return img


def _make_word(bbox: BoundingBox, text: str = "hello") -> Word:
    return Word(text=text, bounding_box=bbox, ocr_confidence=0.9)


# ---------------------------------------------------------------------------
# BoundingBox image_ops parity
# ---------------------------------------------------------------------------


def test_refine_bbox_free_function_matches_method():
    img = _make_text_image()
    bbox = BoundingBox.from_ltrb(0, 0, 50, 50)

    method_result = bbox.refine(img, padding_px=1)
    free_result = refine_bbox(bbox, img, padding_px=1)

    assert method_result.to_ltrb() == free_result.to_ltrb()


def test_crop_top_bbox_free_function_matches_method():
    img = _make_text_image()
    bbox = BoundingBox.from_ltrb(0, 0, 50, 50)

    method_result = bbox.crop_top(img)
    free_result = crop_top_bbox(bbox, img)

    assert method_result.to_ltrb() == free_result.to_ltrb()


def test_crop_bottom_bbox_free_function_matches_method():
    img = _make_text_image()
    bbox = BoundingBox.from_ltrb(0, 0, 50, 50)

    method_result = bbox.crop_bottom(img)
    free_result = crop_bottom_bbox(bbox, img)

    assert method_result.to_ltrb() == free_result.to_ltrb()


def test_refine_bbox_returns_new_object_not_mutating_input():
    img = _make_text_image()
    bbox = BoundingBox.from_ltrb(0, 0, 50, 50)
    original_ltrb = bbox.to_ltrb()

    refine_bbox(bbox, img)

    assert bbox.to_ltrb() == original_ltrb


# ---------------------------------------------------------------------------
# Word image_utilities parity / mutation semantics
# ---------------------------------------------------------------------------


def test_crop_word_bottom_mutates_word_bbox_like_method():
    img = _make_text_image()
    bbox1 = BoundingBox.from_ltrb(0, 0, 50, 50)
    bbox2 = BoundingBox.from_ltrb(0, 0, 50, 50)

    word_method = _make_word(bbox1)
    word_free = _make_word(bbox2)

    word_method.crop_bottom(img)
    crop_word_bottom(word_free, img)

    assert word_method.bounding_box.to_ltrb() == word_free.bounding_box.to_ltrb()


def test_crop_word_top_mutates_word_bbox_like_method():
    img = _make_text_image()
    bbox1 = BoundingBox.from_ltrb(0, 0, 50, 50)
    bbox2 = BoundingBox.from_ltrb(0, 0, 50, 50)

    word_method = _make_word(bbox1)
    word_free = _make_word(bbox2)

    word_method.crop_top(img)
    crop_word_top(word_free, img)

    assert word_method.bounding_box.to_ltrb() == word_free.bounding_box.to_ltrb()


def test_refine_word_bbox_returns_bool_and_mutates():
    img = _make_text_image()
    bbox = BoundingBox.from_ltrb(0, 0, 50, 50)
    word = _make_word(bbox)
    original = word.bounding_box.to_ltrb()

    result = refine_word_bbox(word, img)

    assert result is True
    # Refinement should have tightened the bbox; new ltrb is not the
    # original full image.
    assert word.bounding_box.to_ltrb() != original


def test_refine_word_bbox_no_image_returns_false():
    bbox = BoundingBox.from_ltrb(0, 0, 50, 50)
    word = _make_word(bbox)
    assert refine_word_bbox(word, None) is False


def test_crop_word_bottom_no_image_raises():
    bbox = BoundingBox.from_ltrb(0, 0, 50, 50)
    word = _make_word(bbox)
    with pytest.raises(ValueError, match="Image"):
        crop_word_bottom(word, None)


def test_crop_word_top_no_image_raises():
    bbox = BoundingBox.from_ltrb(0, 0, 50, 50)
    word = _make_word(bbox)
    with pytest.raises(ValueError, match="Image"):
        crop_word_top(word, None)


def test_crop_word_bottom_no_bbox_raises():
    word = Word(text="foo", bounding_box=None, ocr_confidence=0.9)
    img = _make_text_image()
    with pytest.raises(ValueError, match="Bounding box"):
        crop_word_bottom(word, img)
