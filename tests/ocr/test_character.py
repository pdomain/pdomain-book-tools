import pytest

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.character import Character


def test_character_to_dict_round_trip():
    c = Character(
        text="x",
        bounding_box=BoundingBox.from_ltrb(1, 2, 3, 4),
        ocr_confidence=0.8,
        text_style_labels=["bold"],
        word_components=["has superscript"],
        is_superscript=True,
        is_subscript=False,
    )

    d = c.to_dict()
    rehydrated = Character.from_dict(d)

    assert d["type"] == "Character"
    assert rehydrated.text == "x"
    assert rehydrated.bounding_box.to_ltrb() == (1, 2, 3, 4)
    assert rehydrated.ocr_confidence == pytest.approx(0.8)
    assert rehydrated.text_style_labels == ["bold"]
    assert rehydrated.word_components == ["has superscript"]
    assert rehydrated.is_superscript is True
    assert rehydrated.is_subscript is False


def test_character_text_style_labels_reuse_word_normalization():
    c = Character(
        text="x",
        bounding_box=BoundingBox.from_ltrb(1, 2, 3, 4),
        text_style_labels=["Bold", "italic", "small_caps"],
    )

    assert c.text_style_labels == ["bold", "italics", "small caps"]


def test_character_text_style_labels_default_to_regular():
    c = Character(
        text="x",
        bounding_box=BoundingBox.from_ltrb(1, 2, 3, 4),
    )

    assert c.text_style_labels == ["regular"]


def test_character_text_style_invalid_raises():
    with pytest.raises(ValueError):
        Character(
            text="x",
            bounding_box=BoundingBox.from_ltrb(1, 2, 3, 4),
            text_style_labels=["totally unknown style"],
        )
