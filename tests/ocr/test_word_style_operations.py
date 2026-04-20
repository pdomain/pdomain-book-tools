"""Tests for Word style methods."""

import pytest

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.word import Word


@pytest.fixture
def plain_word():
    return Word(
        text="hello",
        bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10),
    )


@pytest.fixture
def italic_word():
    return Word(
        text="emphasis",
        bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10),
        text_style_labels=["italics"],
    )


class TestReadWordAttribute:
    def test_italic_present(self, italic_word):
        assert italic_word.read_style_attribute("italic") is True

    def test_italic_missing(self, plain_word):
        assert plain_word.read_style_attribute("italic") is False

    def test_small_caps_missing(self, plain_word):
        assert plain_word.read_style_attribute("small_caps") is False

    def test_unknown_attribute(self, plain_word):
        assert plain_word.read_style_attribute("nonexistent") is False

    def test_blackletter_via_alias(self):
        word = Word(
            text="frak",
            bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10),
            text_style_labels=["blackletter"],
        )
        assert word.read_style_attribute("is_blackletter") is True


class TestUpdateWordAttributes:
    def test_set_italic(self, plain_word):
        plain_word.update_style_attributes(
            italic=True,
            small_caps=False,
            blackletter=False,
            left_footnote=False,
            right_footnote=False,
        )
        assert "italics" in plain_word.text_style_labels
        assert "regular" not in plain_word.text_style_labels

    def test_set_small_caps(self, plain_word):
        plain_word.update_style_attributes(
            italic=False,
            small_caps=True,
            blackletter=False,
            left_footnote=False,
            right_footnote=False,
        )
        assert "small caps" in plain_word.text_style_labels

    def test_clear_all_styles_reverts_to_regular(self, italic_word):
        italic_word.update_style_attributes(
            italic=False,
            small_caps=False,
            blackletter=False,
            left_footnote=False,
            right_footnote=False,
        )
        assert italic_word.text_style_labels == ["regular"]

    def test_set_footnote_component(self, plain_word):
        plain_word.update_style_attributes(
            italic=False,
            small_caps=False,
            blackletter=False,
            left_footnote=True,
            right_footnote=False,
        )
        assert "footnote marker" in plain_word.word_components

    def test_noop_returns_true(self, plain_word):
        result = plain_word.update_style_attributes(
            italic=False,
            small_caps=False,
            blackletter=False,
            left_footnote=False,
            right_footnote=False,
        )
        assert result is True


class TestApplyStyleScope:
    def test_set_whole_scope(self, italic_word):
        italic_word.apply_style_scope("italics", "whole")
        assert italic_word.text_style_label_scopes.get("italics") == "whole"

    def test_set_part_scope(self, italic_word):
        italic_word.apply_style_scope("italics", "part")
        assert italic_word.text_style_label_scopes.get("italics") == "part"

    def test_adds_missing_style(self, plain_word):
        plain_word.apply_style_scope("italics", "whole")
        assert "italics" in plain_word.text_style_labels
        assert plain_word.text_style_label_scopes.get("italics") == "whole"


class TestRemoveTextStyleLabel:
    def test_remove_existing_label(self, italic_word):
        italic_word.remove_style_label("italics")
        assert "italics" not in italic_word.text_style_labels
        assert "regular" in italic_word.text_style_labels

    def test_remove_nonexistent_label(self, plain_word):
        result = plain_word.remove_style_label("blackletter")
        assert result is True
        assert "regular" in plain_word.text_style_labels

    def test_remove_preserves_other_labels(self):
        word = Word(
            text="styled",
            bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10),
            text_style_labels=["italics", "small caps"],
        )
        word.remove_style_label("italics")
        assert "italics" not in word.text_style_labels
        assert "small caps" in word.text_style_labels
