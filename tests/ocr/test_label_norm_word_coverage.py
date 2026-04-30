"""Coverage tests for label_normalization.py and word.py edge cases."""

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.label_normalization import (
    normalize_text_style_label_scope,
    normalize_text_style_label_scopes,
)
from pd_book_tools.ocr.word import Word


def _make_word(text, x=0, y=0, w=60, h=20):
    return Word(
        text=text,
        bounding_box=BoundingBox.from_ltrb(x, y, x + w, y + h, is_normalized=False),
        ocr_confidence=0.9,
    )


# ---------------------------------------------------------------------------
# label_normalization.py missing lines
# ---------------------------------------------------------------------------


class TestLabelNormalizationCoverage:
    def test_normalize_scope_none_returns_whole(self):
        """normalize_text_style_label_scope(None) → 'whole' (line 62)."""
        result = normalize_text_style_label_scope(None)
        assert result == "whole"

    def test_normalize_scopes_empty_labels_none_scopes(self):
        """normalize_text_style_label_scopes with empty labels returns regular entry (line 79)."""
        result = normalize_text_style_label_scopes([], None)
        assert result == {"regular": "whole"}

    def test_normalize_scopes_empty_labels_empty_scopes(self):
        """normalize_text_style_label_scopes([], {}) also returns regular entry."""
        result = normalize_text_style_label_scopes([], {})
        assert result == {"regular": "whole"}


# ---------------------------------------------------------------------------
# word.py – apply_style_scope with new style
# ---------------------------------------------------------------------------


class TestWordApplyStyleScope:
    def test_apply_scope_adds_new_style(self):
        """apply_style_scope adds the style if not already present (line 286)."""
        word = _make_word("hello")
        word.text_style_labels = ["regular"]
        result = word.apply_style_scope("italics", "part")
        assert result is True
        assert "italics" in word.text_style_labels
        assert word.text_style_label_scopes.get("italics") == "part"

    def test_apply_scope_updates_existing_style(self):
        """apply_style_scope updates scope for an existing style."""
        word = _make_word("hello")
        word.text_style_labels = ["italics"]
        word.text_style_label_scopes = {"italics": "whole"}
        result = word.apply_style_scope("italics", "part")
        assert result is True
        assert word.text_style_label_scopes.get("italics") == "part"


# ---------------------------------------------------------------------------
# word.py – _normalized_style_labels with invalid label (line 365)
# ---------------------------------------------------------------------------


class TestWordNormalizedStyleLabels:
    def test_ignores_invalid_label_returns_regular(self):
        """_normalized_style_labels with only invalid labels returns ['regular'] (line 365)."""
        word = _make_word("hello")
        word.text_style_labels = ["not_a_real_style_xyz_abc"]
        result = word._normalized_style_labels()
        assert result == ["regular"]

    def test_preserves_valid_labels(self):
        """_normalized_style_labels preserves valid labels."""
        word = _make_word("hello")
        word.text_style_labels = ["italics"]
        result = word._normalized_style_labels()
        assert "italics" in result


# ---------------------------------------------------------------------------
# word.py – _resolve_style_label alias loop (lines 404-406)
# ---------------------------------------------------------------------------


class TestWordResolveStyleLabelAliasLoop:
    def test_alias_resolves_primary_name(self):
        """_resolve_style_label returns from STYLE_LABEL_BY_ATTR for primary name."""
        result = Word._resolve_style_label("italic", ())
        assert result == "italics"

    def test_alias_loop_returns_via_alias(self):
        """_resolve_style_label finds via alias when primary is not found (lines 404-406)."""
        # 'italic' maps to 'italics' in STYLE_LABEL_BY_ATTR
        result = Word._resolve_style_label("nonexistent_primary", ("italic",))
        assert result == "italics"

    def test_returns_none_for_unknown(self):
        """_resolve_style_label returns None when neither primary nor aliases match."""
        result = Word._resolve_style_label("unknown_xyz", ("also_unknown",))
        assert result is None


# ---------------------------------------------------------------------------
# word.py – _resolve_word_component alias loop (lines 420-422)
# ---------------------------------------------------------------------------


class TestWordResolveWordComponentAliasLoop:
    def test_component_resolves_primary_name(self):
        """_resolve_word_component returns from WORD_COMPONENT_BY_ATTR for primary."""
        result = Word._resolve_word_component("left_footnote", ())
        assert result is not None

    def test_component_via_alias(self):
        """_resolve_word_component finds via alias when primary is not found (lines 420-422)."""
        result = Word._resolve_word_component("nonexistent_xyz", ("left_footnote",))
        assert result is not None

    def test_returns_none_for_unknown(self):
        """_resolve_word_component returns None when nothing matches."""
        result = Word._resolve_word_component("unknown_xyz", ("also_unknown",))
        assert result is None


# ---------------------------------------------------------------------------
# word.py – expand_bbox branches (lines 519->521, 521->524)
# ---------------------------------------------------------------------------


class TestWordExpandBbox:
    def test_expand_bbox_pixel_coords(self):
        """expand_bbox with pixel coords uses the else branch (lines 521->524)."""
        word = _make_word("hello", x=10, y=10, w=60, h=20)
        assert not word.bounding_box.is_normalized
        result = word.expand_bbox(
            padding_px=5.0,
            page_width=1000.0,
            page_height=500.0,
        )
        assert result is True
        assert word.bounding_box.minX <= 10.0

    def test_expand_bbox_normalized_coords(self):
        """expand_bbox with normalized coords uses the normalized branch (lines 519->521)."""
        word = Word(
            text="hello",
            bounding_box=BoundingBox.from_ltrb(0.1, 0.1, 0.2, 0.15, is_normalized=True),
            ocr_confidence=0.9,
        )
        assert word.bounding_box.is_normalized
        result = word.expand_bbox(
            padding_px=5.0,
            page_width=1000.0,
            page_height=500.0,
        )
        assert result is True
        assert word.bounding_box.is_normalized

    def test_expand_bbox_no_bbox_returns_false(self):
        """expand_bbox returns False when bbox is None."""
        word = _make_word("hello")
        word.bounding_box = None
        result = word.expand_bbox(padding_px=5.0, page_width=1000.0, page_height=500.0)
        assert result is False

    def test_expand_bbox_normalized_no_page_dims_returns_false(self):
        """expand_bbox with normalized bbox and zero page dims returns False."""
        word = Word(
            text="hello",
            bounding_box=BoundingBox.from_ltrb(0.1, 0.1, 0.2, 0.15, is_normalized=True),
            ocr_confidence=0.9,
        )
        result = word.expand_bbox(padding_px=5.0, page_width=0.0, page_height=0.0)
        assert result is False
