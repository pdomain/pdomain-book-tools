"""Targeted tests for Word coverage gaps (refine, expand, ground_truth helpers)."""

from unittest.mock import MagicMock

import numpy as np
import pytest

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.word import Word


@pytest.fixture
def pixel_word():
    return Word(
        text="abc",
        bounding_box=BoundingBox.from_ltrb(10, 10, 30, 20, is_normalized=False),
        ocr_confidence=0.9,
    )


@pytest.fixture
def normalized_word():
    return Word(
        text="abc",
        bounding_box=BoundingBox.from_ltrb(0.1, 0.1, 0.3, 0.2, is_normalized=True),
        ocr_confidence=0.9,
    )


class TestGroundTruthHelpers:
    def test_copy_ocr_to_ground_truth_empty_text(self, pixel_word):
        pixel_word.text = ""
        assert pixel_word.copy_ocr_to_ground_truth() is False

    def test_copy_ocr_to_ground_truth(self, pixel_word):
        pixel_word.ground_truth_text = ""
        assert pixel_word.copy_ocr_to_ground_truth() is True
        assert pixel_word.ground_truth_text == pixel_word.text

    def test_copy_ground_truth_to_ocr_empty(self, pixel_word):
        pixel_word.ground_truth_text = ""
        assert pixel_word.copy_ground_truth_to_ocr() is False

    def test_copy_ground_truth_to_ocr(self, pixel_word):
        pixel_word.ground_truth_text = "GT"
        assert pixel_word.copy_ground_truth_to_ocr() is True
        assert pixel_word.text == "GT"

    def test_clear_ground_truth_empty(self, pixel_word):
        pixel_word.ground_truth_text = ""
        assert pixel_word.clear_ground_truth() is False

    def test_clear_ground_truth(self, pixel_word):
        pixel_word.ground_truth_text = "GT"
        assert pixel_word.clear_ground_truth() is True
        assert pixel_word.ground_truth_text == ""

    def test_is_empty(self, pixel_word):
        assert pixel_word.is_empty is False
        pixel_word.text = ""
        assert pixel_word.is_empty is True

    def test_ground_truth_text_only_ocr_empty_text(self, pixel_word):
        pixel_word.text = ""
        pixel_word.ground_truth_text = "something"
        assert pixel_word.ground_truth_text_only_ocr == ""

    def test_ground_truth_text_only_ocr_with_gt(self, pixel_word):
        pixel_word.ground_truth_text = "GT"
        assert pixel_word.ground_truth_text_only_ocr == "GT"


class TestApplyStyleScope:
    def test_apply_style_scope_adds_new_label(self, pixel_word):
        # No existing italics label, but apply scope to italics
        pixel_word.apply_style_scope("italics", "whole")
        assert "italics" in pixel_word.text_style_labels
        assert pixel_word.text_style_label_scopes.get("italics") == "whole"

    def test_apply_style_scope_with_existing_label(self, pixel_word):
        pixel_word.text_style_labels = ["italics"]
        pixel_word.apply_style_scope("italics", "part")
        assert pixel_word.text_style_label_scopes.get("italics") == "part"


class TestApplyComponent:
    def test_apply_component_enable(self, pixel_word):
        pixel_word.apply_component("footnote marker", enabled=True)
        assert "footnote marker" in pixel_word.word_components

    def test_apply_component_disable(self, pixel_word):
        pixel_word.word_components = ["footnote marker"]
        pixel_word.apply_component("footnote marker", enabled=False)
        assert "footnote marker" not in pixel_word.word_components


class TestClearAllScopes:
    def test_clear_all_scopes_no_styles(self, pixel_word):
        # Default text style labels are ["regular"]; should return False
        assert pixel_word.clear_all_scopes() is False

    def test_clear_all_scopes_with_scoped_styles(self, pixel_word):
        pixel_word.text_style_labels = ["italics"]
        pixel_word.text_style_label_scopes = {"italics": "part"}
        assert pixel_word.clear_all_scopes() is True
        assert pixel_word.text_style_label_scopes == {}

    def test_clear_all_scopes_no_scope_to_clear(self, pixel_word):
        pixel_word.text_style_labels = ["italics"]
        pixel_word.text_style_label_scopes = {}
        assert pixel_word.clear_all_scopes() is False


class TestRemoveStyleLabel:
    def test_remove_style_label(self, pixel_word):
        pixel_word.text_style_labels = ["italics", "small caps"]
        pixel_word.text_style_label_scopes = {"italics": "whole", "small caps": "part"}
        assert pixel_word.remove_style_label("italics") is True
        assert "italics" not in pixel_word.text_style_labels

    def test_remove_only_style_label_falls_back_to_regular(self, pixel_word):
        pixel_word.text_style_labels = ["italics"]
        pixel_word.text_style_label_scopes = {"italics": "whole"}
        pixel_word.remove_style_label("italics")
        assert pixel_word.text_style_labels == ["regular"]


class TestUpdateStyleAttributes:
    def test_no_change_returns_true(self, pixel_word):
        # Already in default state. Setting all to False should keep it stable.
        result = pixel_word.update_style_attributes(
            italic=False,
            small_caps=False,
            blackletter=False,
            left_footnote=False,
            right_footnote=False,
        )
        assert result is True

    def test_set_italic_true(self, pixel_word):
        pixel_word.update_style_attributes(
            italic=True,
            small_caps=False,
            blackletter=False,
            left_footnote=False,
            right_footnote=False,
        )
        assert "italics" in pixel_word.text_style_labels
        assert pixel_word.read_style_attribute("italic") is True

    def test_set_footnote_true(self, pixel_word):
        pixel_word.update_style_attributes(
            italic=False,
            small_caps=False,
            blackletter=False,
            left_footnote=True,
            right_footnote=False,
        )
        assert "footnote marker" in pixel_word.word_components

    def test_set_all_styles(self, pixel_word):
        pixel_word.update_style_attributes(
            italic=True,
            small_caps=True,
            blackletter=True,
            left_footnote=True,
            right_footnote=True,
        )
        assert "italics" in pixel_word.text_style_labels
        assert "small caps" in pixel_word.text_style_labels
        assert "blackletter" in pixel_word.text_style_labels
        assert "footnote marker" in pixel_word.word_components

    def test_unset_all_styles(self, pixel_word):
        pixel_word.text_style_labels = ["italics"]
        pixel_word.update_style_attributes(
            italic=False,
            small_caps=False,
            blackletter=False,
            left_footnote=False,
            right_footnote=False,
        )
        # When all unset, should fall back to "regular"
        assert "regular" in pixel_word.text_style_labels


class TestReadStyleAttribute:
    def test_unknown_attribute(self, pixel_word):
        # Returns False for unknown attributes
        assert pixel_word.read_style_attribute("unknown_attr") is False

    def test_style_attribute_alias(self, pixel_word):
        pixel_word.text_style_labels = ["italics"]
        # is_italic is an alias
        assert pixel_word.read_style_attribute("is_italic") is True

    def test_component_attribute(self, pixel_word):
        pixel_word.word_components = ["footnote marker"]
        assert pixel_word.read_style_attribute("footnote") is True


class TestBboxSignature:
    def test_bbox_signature(self, pixel_word):
        sig = pixel_word.bbox_signature
        assert sig is not None
        assert sig[4] is False  # is_normalized

    def test_bbox_signature_none_when_no_bbox(self, pixel_word):
        pixel_word.bounding_box = None
        assert pixel_word.bbox_signature is None


class TestRefineBbox:
    def test_refine_bbox_no_image(self, pixel_word):
        assert pixel_word.refine_bbox(None) is False

    def test_refine_bbox_no_bbox(self, pixel_word):
        pixel_word.bounding_box = None
        assert pixel_word.refine_bbox(np.zeros((20, 20), dtype=np.uint8)) is False

    def test_refine_bbox_uses_refine_when_succeeds(self, pixel_word, monkeypatch):
        new_bbox = BoundingBox.from_ltrb(0, 0, 5, 5, is_normalized=False)

        def fake_refine(self, page_image, padding_px=1, expand_beyond_original=False):
            return new_bbox

        monkeypatch.setattr(BoundingBox, "refine", fake_refine)
        img = np.zeros((50, 50), dtype=np.uint8)
        assert pixel_word.refine_bbox(img) is True
        assert pixel_word.bounding_box is new_bbox

    def test_refine_bbox_falls_back_to_crop_bottom(self, pixel_word, monkeypatch):
        # refine raises -> falls back to crop_bottom
        def raising_refine(self, *a, **kw):
            raise RuntimeError("nope")

        monkeypatch.setattr(BoundingBox, "refine", raising_refine)

        called = {"count": 0}

        def fake_crop_bottom(img):
            called["count"] += 1

        # Replace crop_bottom on the word instance
        pixel_word.crop_bottom = fake_crop_bottom
        img = np.zeros((50, 50), dtype=np.uint8)
        assert pixel_word.refine_bbox(img) is True
        assert called["count"] == 1

    def test_refine_bbox_returns_false_when_all_fail(self, pixel_word, monkeypatch):
        def raising_refine(self, *a, **kw):
            raise RuntimeError("nope")

        def raising_crop_bottom(img):
            raise RuntimeError("nope2")

        monkeypatch.setattr(BoundingBox, "refine", raising_refine)
        pixel_word.crop_bottom = raising_crop_bottom
        img = np.zeros((50, 50), dtype=np.uint8)
        assert pixel_word.refine_bbox(img) is False

    def test_refine_bbox_returns_false_when_refine_returns_none(
        self, pixel_word, monkeypatch
    ):
        def fake_refine(self, *a, **kw):
            return None

        monkeypatch.setattr(BoundingBox, "refine", fake_refine)
        pixel_word.crop_bottom = MagicMock(side_effect=RuntimeError("no"))
        img = np.zeros((50, 50), dtype=np.uint8)
        assert pixel_word.refine_bbox(img) is False


class TestExpandBbox:
    def test_expand_bbox_no_bbox(self, pixel_word):
        pixel_word.bounding_box = None
        assert pixel_word.expand_bbox(5.0, 100, 100) is False

    def test_expand_bbox_pixel_space(self, pixel_word):
        # pixel_word: 10,10 -> 30,20 in 100x100 page
        result = pixel_word.expand_bbox(2.0, 100, 100)
        assert result is True
        # Padding of 2 should expand bbox in both directions
        assert pixel_word.bounding_box.minX < 10
        assert pixel_word.bounding_box.maxX > 30

    def test_expand_bbox_normalized_space(self, normalized_word):
        result = normalized_word.expand_bbox(5.0, 100, 100)
        assert result is True
        # Result should remain normalized
        assert normalized_word.bounding_box.is_normalized is True

    def test_expand_bbox_normalized_zero_dimensions_returns_false(
        self, normalized_word
    ):
        assert normalized_word.expand_bbox(5.0, 0, 100) is False
        assert normalized_word.expand_bbox(5.0, 100, 0) is False

    def test_expand_bbox_invalid_returns_false(self, pixel_word):
        # Negative padding so large that maxX <= minX
        # Hard to construct with negative padding directly since it's added.
        # Use a tiny image to clamp away the new bbox.
        # Set bbox right at the edges: 0,0 -> 1,1, padding -2 -> 2,2 outside
        pixel_word.bounding_box = BoundingBox.from_ltrb(0, 0, 1, 1, is_normalized=False)
        # Padding -2 then clamping to 0 / image size -> nx2 <= nx1
        result = pixel_word.expand_bbox(-2.0, 100, 100)
        assert result is False

    def test_expand_bbox_pixel_zero_page_width(self, pixel_word):
        """Covers 519->521 False branch: pixel word, page_width=0 → no min-clamp on nx2."""
        # pixel_word: 10,10 -> 30,20; page_width=0, page_height=50
        result = pixel_word.expand_bbox(2.0, 0, 50)
        assert result is True  # nx2 = 32 (no clamping), ny2 = min(22, 50)

    def test_expand_bbox_pixel_zero_page_height(self, pixel_word):
        """Covers 521->524 False branch: pixel word, page_height=0 → no min-clamp on ny2."""
        result = pixel_word.expand_bbox(2.0, 100, 0)
        assert result is True  # nx2 = min(32, 100), ny2 = 22 (no clamping)


class TestExpandThenRefineBbox:
    def test_expand_then_refine_no_image(self, pixel_word):
        result = pixel_word.expand_then_refine_bbox(None)
        assert result is False

    def test_expand_then_refine_succeeds_with_refine(self, pixel_word, monkeypatch):
        new_bbox = BoundingBox.from_ltrb(0, 0, 50, 30, is_normalized=False)

        call_count = {"n": 0}

        def fake_refine(self, *a, **kw):
            call_count["n"] += 1
            return new_bbox

        monkeypatch.setattr(BoundingBox, "refine", fake_refine)
        img = np.zeros((50, 50), dtype=np.uint8)
        result = pixel_word.expand_then_refine_bbox(img)
        assert result is True

    def test_expand_then_refine_refine_fails_falls_back(self, pixel_word, monkeypatch):
        def raising_refine(self, *a, **kw):
            raise RuntimeError("nope")

        monkeypatch.setattr(BoundingBox, "refine", raising_refine)

        crop_calls = {"n": 0}

        def fake_crop_bottom(img):
            crop_calls["n"] += 1

        pixel_word.crop_bottom = fake_crop_bottom
        img = np.zeros((50, 50), dtype=np.uint8)
        result = pixel_word.expand_then_refine_bbox(img)
        assert result is True
        assert crop_calls["n"] >= 1


class TestCropTop:
    def test_crop_top_no_bbox(self):
        word = Word(text="x", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10))
        word.bounding_box = None
        with pytest.raises(ValueError, match="Bounding box is None"):
            word.crop_top(np.zeros((20, 20), dtype=np.uint8))

    def test_crop_top_no_image(self, pixel_word):
        with pytest.raises(ValueError, match="Image ndarray is None"):
            pixel_word.crop_top(None)

    def test_crop_top_invokes_bbox_method(self, pixel_word, monkeypatch):
        result_bbox = BoundingBox.from_ltrb(10, 12, 30, 20, is_normalized=False)

        def fake_crop_top(self, img):
            return result_bbox

        monkeypatch.setattr(BoundingBox, "crop_top", fake_crop_top)
        pixel_word.crop_top(np.zeros((50, 50), dtype=np.uint8))
        assert pixel_word.bounding_box is result_bbox


class TestCropBottom:
    def test_crop_bottom_no_bbox(self):
        word = Word(text="x", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10))
        word.bounding_box = None
        with pytest.raises(ValueError, match="Bounding box is None"):
            word.crop_bottom(np.zeros((20, 20), dtype=np.uint8))

    def test_crop_bottom_no_image(self, pixel_word):
        with pytest.raises(ValueError, match="Image ndarray is None"):
            pixel_word.crop_bottom(None)


class TestRefineBoundingBox:
    def test_refine_bounding_box_no_image(self, pixel_word):
        # refine_bounding_box returns None when image is None
        assert pixel_word.refine_bounding_box(None) is None

    def test_refine_bounding_box_with_image(self, pixel_word, monkeypatch):
        new_bbox = BoundingBox.from_ltrb(0, 0, 5, 5, is_normalized=False)

        def fake_refine(self, image, padding_px=0):
            return new_bbox

        monkeypatch.setattr(BoundingBox, "refine", fake_refine)
        pixel_word.refine_bounding_box(np.zeros((20, 20), dtype=np.uint8))
        assert pixel_word.bounding_box is new_bbox


class TestNormalizationHelpers:
    def test_normalize_text_style_label_classmethod(self):
        # _normalize_text_style_label is a classmethod that delegates
        normalized = Word._normalize_text_style_label("italics")
        assert isinstance(normalized, str)

    def test_normalize_word_component_classmethod(self):
        normalized = Word._normalize_word_component("footnote marker")
        assert isinstance(normalized, str)

    def test_normalized_style_labels_filters_invalid(self, pixel_word):
        pixel_word.text_style_labels = ["italics", "definitely-bogus-label"]
        labels = pixel_word._normalized_style_labels()
        assert "italics" in labels

    def test_normalized_style_scopes_filters_invalid(self, pixel_word):
        pixel_word.text_style_label_scopes = {
            "italics": "whole",
            "definitely-bogus-label": "part",
        }
        scopes = pixel_word._normalized_style_scopes()
        assert "italics" in scopes

    def test_normalized_components_filters_invalid(self, pixel_word):
        pixel_word.word_components = [
            "footnote marker",
            "definitely-bogus-component",
        ]
        components = pixel_word._normalized_components()
        assert "footnote marker" in components


class TestSplitIntoCharactersFromWhitespace:
    def test_no_image_raises(self, pixel_word):
        with pytest.raises(ValueError, match="Image is None"):
            pixel_word.split_into_characters_from_whitespace(None)

    def test_no_text_returns_empty(self, pixel_word):
        pixel_word.text = ""
        img = np.zeros((50, 50, 3), dtype=np.uint8)
        result = pixel_word.split_into_characters_from_whitespace(img)
        assert result == []


class TestEstimateBaselineFromImage:
    def test_no_image_returns_none(self, pixel_word):
        result = pixel_word.estimate_baseline_from_image(None)
        assert result is None
        assert pixel_word.baseline is None

    def test_no_text_returns_none(self, pixel_word):
        pixel_word.text = ""
        img = np.zeros((50, 50, 3), dtype=np.uint8)
        result = pixel_word.estimate_baseline_from_image(img)
        assert result is None
