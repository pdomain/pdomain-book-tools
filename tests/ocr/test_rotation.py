"""Unit tests for :mod:`pd_book_tools.ocr.rotation`.

These tests exercise the orientation-detection logic with stub OCR
callables, so they're fast and don't require the DocTR predictor.
"""

from __future__ import annotations

from typing import Callable
from unittest.mock import MagicMock

import numpy as np
import pytest

from pd_book_tools.ocr.rotation import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    detect_best_rotation,
    rotate_image,
)


def _make_image(width: int = 6, height: int = 4) -> np.ndarray:
    """Distinct values per pixel so rotations are visually verifiable."""
    return np.arange(height * width, dtype=np.uint8).reshape(height, width)


def _stub_doc_with_confidences(*confidences: float):
    """Return a stand-in Document whose pages.words.ocr_confidence read back."""
    words = [MagicMock(ocr_confidence=c) for c in confidences]
    page = MagicMock()
    page.words = words
    doc = MagicMock()
    doc.pages = [page]
    return doc


class TestRotateImage:
    def test_zero_returns_same_object(self):
        img = _make_image()
        # 0° should return the original array (no copy) — callers rely on
        # this to avoid an allocation on the common upright path.
        assert rotate_image(img, 0) is img

    def test_90_180_270_match_numpy_rot90(self):
        img = _make_image()
        # Clockwise rotations match np.rot90 with negative-k convention.
        np.testing.assert_array_equal(rotate_image(img, 90), np.rot90(img, k=-1))
        np.testing.assert_array_equal(rotate_image(img, 180), np.rot90(img, k=2))
        np.testing.assert_array_equal(rotate_image(img, 270), np.rot90(img, k=1))

    def test_90_swaps_dimensions(self):
        img = _make_image(width=6, height=4)
        rotated = rotate_image(img, 90)
        assert rotated.shape == (6, 4)

    def test_invalid_degrees_raises(self):
        with pytest.raises(ValueError, match="0/90/180/270"):
            rotate_image(_make_image(), 45)


class TestDetectBestRotation:
    def test_fast_path_at_zero(self):
        # 0° passes the threshold: should NOT call OCR for any other rotation.
        ocr_fn: Callable = MagicMock(
            return_value=_stub_doc_with_confidences(0.9, 0.8, 0.95)
        )
        chosen, doc, probes = detect_best_rotation(_make_image(), ocr_fn=ocr_fn)
        assert chosen == 0
        assert ocr_fn.call_count == 1
        assert len(probes) == 1
        assert probes[0].rotation == 0
        assert probes[0].mean_confidence == pytest.approx((0.9 + 0.8 + 0.95) / 3)
        assert probes[0].word_count == 3
        assert doc is ocr_fn.return_value

    def test_falls_back_when_zero_below_threshold(self):
        # Confidence ramps with rotation; 270° is best.
        confidences_per_call = [
            (0.1, 0.2),  # 0°  → 0.15
            (0.3,),  # 90° → 0.30
            (0.4,),  # 180° → 0.40
            (0.9, 0.7),  # 270° → 0.80
        ]
        docs_returned = [_stub_doc_with_confidences(*c) for c in confidences_per_call]
        call_count = {"n": 0}

        def ocr_fn(_img):
            doc = docs_returned[call_count["n"]]
            call_count["n"] += 1
            return doc

        chosen, doc, probes = detect_best_rotation(_make_image(), ocr_fn=ocr_fn)
        assert chosen == 270
        assert call_count["n"] == 4  # tried all rotations
        assert [p.rotation for p in probes] == [0, 90, 180, 270]
        assert probes[-1].mean_confidence == pytest.approx(0.8)
        # Returned doc is the one from the 270° run.
        assert doc is docs_returned[3]

    def test_tie_keeps_earliest_rotation(self):
        # All probes return identical low confidence. The fast path doesn't
        # fire (below threshold), but no fallback strictly beats 0°, so
        # 0° should win.
        ocr_fn = MagicMock(return_value=_stub_doc_with_confidences(0.4))
        chosen, _, probes = detect_best_rotation(_make_image(), ocr_fn=ocr_fn)
        assert chosen == 0
        assert ocr_fn.call_count == 4
        assert all(p.mean_confidence == pytest.approx(0.4) for p in probes)

    def test_no_words_treated_as_zero_confidence(self):
        # Empty pages have no words; mean_confidence is 0.0 (not NaN), so
        # the fallback path is exercised cleanly.
        ocr_fn = MagicMock(return_value=_stub_doc_with_confidences())
        chosen, _, probes = detect_best_rotation(_make_image(), ocr_fn=ocr_fn)
        assert chosen == 0  # nothing beats 0.0 strictly
        assert ocr_fn.call_count == 4  # threshold not met → tried all
        assert all(p.mean_confidence == 0.0 for p in probes)
        assert all(p.word_count == 0 for p in probes)

    def test_threshold_override_skips_fallbacks(self):
        # Setting threshold=0 makes any non-empty 0° pass acceptable.
        ocr_fn = MagicMock(return_value=_stub_doc_with_confidences(0.05))
        chosen, _, probes = detect_best_rotation(
            _make_image(), ocr_fn=ocr_fn, confidence_threshold=0.0
        )
        assert chosen == 0
        assert ocr_fn.call_count == 1
        assert len(probes) == 1

    def test_rotations_must_start_with_zero(self):
        ocr_fn = MagicMock(return_value=_stub_doc_with_confidences(0.9))
        with pytest.raises(ValueError, match="must start with 0"):
            detect_best_rotation(_make_image(), ocr_fn=ocr_fn, rotations=(90, 180, 270))

    def test_default_threshold_is_documented_constant(self):
        # Sanity: catching accidental drift between the doc constant and
        # the default arg value.
        ocr_fn = MagicMock(
            return_value=_stub_doc_with_confidences(DEFAULT_CONFIDENCE_THRESHOLD - 0.01)
        )
        chosen, _, _ = detect_best_rotation(_make_image(), ocr_fn=ocr_fn)
        # Just below threshold → fallbacks attempted.
        assert ocr_fn.call_count > 1
        assert chosen == 0


class TestPageRotationAppliedField:
    def test_default_zero(self):
        from pd_book_tools.ocr.page import Page

        page = Page(width=10, height=10, page_index=0, items=[])
        assert page.rotation_applied == 0

    def test_invalid_value_rejected(self):
        from pd_book_tools.ocr.page import Page

        with pytest.raises(ValueError, match="rotation_applied"):
            Page(
                width=10,
                height=10,
                page_index=0,
                items=[],
                rotation_applied=45,
            )

    def test_round_trip_through_dict(self):
        from pd_book_tools.ocr.page import Page

        page = Page(
            width=10,
            height=10,
            page_index=0,
            items=[],
            rotation_applied=90,
        )
        data = page.to_dict()
        assert data["rotation_applied"] == 90
        restored = Page.from_dict(data)
        assert restored.rotation_applied == 90

    def test_zero_omitted_from_dict(self):
        # Default 0 isn't serialized, keeping existing JSONs unchanged.
        from pd_book_tools.ocr.page import Page

        page = Page(width=10, height=10, page_index=0, items=[])
        assert "rotation_applied" not in page.to_dict()
