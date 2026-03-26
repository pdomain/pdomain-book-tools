import pytest

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.character import Character


def test_character_to_dict_round_trip():
    c = Character(
        text="x",
        bounding_box=BoundingBox.from_ltrb(1, 2, 3, 4),
        ocr_confidence=0.8,
        text_style_labels=["bold"],
        word_components=["superscript"],
    )

    d = c.to_dict()
    rehydrated = Character.from_dict(d)

    assert d["type"] == "Character"
    assert rehydrated.text == "x"
    assert rehydrated.bounding_box.to_ltrb() == (1, 2, 3, 4)
    assert rehydrated.ocr_confidence == pytest.approx(0.8)
    assert rehydrated.text_style_labels == ["bold"]
    assert rehydrated.word_components == ["superscript"]


def test_character_component_normalizes_compact_form():
    c = Character(
        text="*",
        bounding_box=BoundingBox.from_ltrb(1, 2, 3, 4),
        word_components=["footnote-marker"],
    )

    assert c.word_components == ["footnote marker"]


def test_character_from_dict_legacy_footnote_flag_maps_to_component_list():
    rehydrated = Character.from_dict(
        {
            "type": "Character",
            "text": "*",
            "bounding_box": BoundingBox.from_ltrb(1, 2, 3, 4).to_dict(),
            "is_footnote_marker": True,
        }
    )

    assert rehydrated.word_components == ["footnote marker"]


def test_character_text_style_labels_reuse_word_normalization():
    c = Character(
        text="x",
        bounding_box=BoundingBox.from_ltrb(1, 2, 3, 4),
        text_style_labels=["Bold", "italics", "small_caps"],
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
