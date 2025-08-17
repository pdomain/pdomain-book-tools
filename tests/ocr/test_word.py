import pytest
import numpy as np

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.word import Word


def test_word_to_dict(sample_word1):
    word_dict = sample_word1.to_dict()

    assert word_dict == {
        "type": "Word",
        "text": "word1",
        "bounding_box": {
            "top_left": {"x": 0, "y": 0, "is_normalized": False},
            "bottom_right": {"x": 10, "y": 10, "is_normalized": False},
            "is_normalized": False,
        },
        "ocr_confidence": pytest.approx(0.9),
        "word_labels": [],
        "ground_truth_text": None,
        "ground_truth_bounding_box": None,
        "ground_truth_match_keys": {},
    }


def test_word_from_dict(sample_word1):
    bounding_box_dict = {
    "top_left": {"x": 0, "y": 0, "is_normalized": False},
    "bottom_right": {"x": 10, "y": 10, "is_normalized": False},
    "is_normalized": False,
    }
    word_dict = {
        "type": "Word",
        "text": "test",
        "bounding_box": bounding_box_dict,
        "ocr_confidence": 0.99,
        "word_labels": ["label1"],
    }
    word = Word.from_dict(word_dict)

    assert word.text == "test"
    assert word.bounding_box == BoundingBox.from_dict(bounding_box_dict)
    assert word.ocr_confidence == pytest.approx(0.99)
    assert word.word_labels == ["label1"]


def test_ground_truth_exact_match():
    w = Word(
        text="Hello",
        bounding_box=BoundingBox.from_ltrb(0, 0, 1, 1),
        ground_truth_text="Hello",
    )
    assert w.ground_truth_exact_match is True
    w.ground_truth_text = "World"
    assert w.ground_truth_exact_match is False


def test_scale_returns_scaled_word():
    # bounding box with normalized coordinates
    bbox = BoundingBox.from_ltrb(0.1, 0.2, 0.3, 0.4)
    w = Word(text="hi", bounding_box=bbox, ocr_confidence=0.5)
    scaled = w.scale(100, 200)
    # Expect pixel coordinates (int) after scaling
    assert scaled.bounding_box.to_ltrb() == (10, 40, 30, 80)
    # Original unchanged
    assert w.bounding_box.to_ltrb() == (0.1, 0.2, 0.3, 0.4)


def test_fuzz_score_against_identical():
    w = Word(text="test", bounding_box=BoundingBox.from_ltrb(0, 0, 1, 1))
    assert w.fuzz_score_against("test") == 100


def test_split_basic():
    w = Word(
        text="hello",
        bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10),
        ground_truth_text="hello",
    )
    left, right = w.split(bbox_split_offset=4, character_split_index=2)
    assert left.text == "he"
    assert right.text == "llo"
    # bounding box widths reflect the split offset
    assert left.bounding_box.width == 4
    assert right.bounding_box.width == 6
    # ground truth texts also split
    assert left.ground_truth_text == "he"
    assert right.ground_truth_text == "llo"


@pytest.mark.parametrize(
    "bbox_split_offset,character_split_index,exc",
    [(-1, 2, ValueError), (2, -1, ValueError), (5, 10, IndexError), (11, 2, ValueError)],
)
def test_split_errors(bbox_split_offset, character_split_index, exc):
    w = Word(text="hello", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10))
    with pytest.raises(exc):
        w.split(bbox_split_offset=bbox_split_offset, character_split_index=character_split_index)


def test_split_sets_split_flag_and_labels():
    w = Word(
        text="abcd",
        bounding_box=BoundingBox.from_ltrb(0, 0, 8, 8),
        word_labels=["x", "y"],
    )
    left, right = w.split(bbox_split_offset=3, character_split_index=2)
    assert left.ground_truth_match_keys.get("split") is True
    assert right.ground_truth_match_keys.get("split") is True
    # Labels copied (not necessarily deep-copied, but contents preserved)
    assert set(left.word_labels) == {"x", "y"}
    assert set(right.word_labels) == {"x", "y"}


def test_merge_reversed_order_and_confidence_and_labels():
    # self is to the right of the other; should prepend other's text
    right = Word(
        text="world",
        bounding_box=BoundingBox.from_ltrb(10, 0, 20, 10),
        ocr_confidence=0.8,
        word_labels=["bar"],
        ground_truth_text="WORLD",
    )
    left = Word(
        text="hello",
        bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10),
        ocr_confidence=0.6,
        word_labels=["foo", "bar"],
        ground_truth_text="HELLO",
    )
    right.merge(left)
    # Text & ground truth concatenated in left->right reading order
    assert right.text == "helloworld"
    assert right.ground_truth_text == "HELLOWORLD"
    # Confidence averaged
    assert right.ocr_confidence == pytest.approx((0.8 + 0.6) / 2)
    # Labels deduped (order not guaranteed due to set usage)
    assert set(right.word_labels) == {"foo", "bar"}
    # Bounding box spans both
    assert right.bounding_box.to_ltrb() == (0, 0, 20, 10)


def test_merge_left_to_right():
    left = Word(
        text="hello",
        bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10),
        ocr_confidence=0.9,
        ground_truth_text="HELLO",
    )
    right = Word(
        text="world",
        bounding_box=BoundingBox.from_ltrb(10, 0, 20, 10),
        ocr_confidence=0.7,
        ground_truth_text="WORLD",
    )
    left.merge(right)
    assert left.text == "helloworld"
    assert left.ground_truth_text == "HELLOWORLD"
    assert left.ocr_confidence == pytest.approx((0.9 + 0.7) / 2)
    assert left.bounding_box.to_ltrb() == (0, 0, 20, 10)


def test_merge_confidence_cases():
    # both None
    a = Word(text="a", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10), ocr_confidence=None)
    b = Word(text="b", bounding_box=BoundingBox.from_ltrb(10, 0, 20, 10), ocr_confidence=None)
    a.merge(b)
    assert a.ocr_confidence is None

    # self None, other has value
    c = Word(text="c", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10), ocr_confidence=None)
    d = Word(text="d", bounding_box=BoundingBox.from_ltrb(10, 0, 20, 10), ocr_confidence=0.4)
    c.merge(d)
    assert c.ocr_confidence == pytest.approx(0.4)

    # self has value, other None
    e = Word(text="e", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10), ocr_confidence=0.7)
    f = Word(text="f", bounding_box=BoundingBox.from_ltrb(10, 0, 20, 10), ocr_confidence=None)
    e.merge(f)
    assert e.ocr_confidence == pytest.approx(0.7)


def test_merge_type_error():
    w = Word(text="a", bounding_box=BoundingBox.from_ltrb(0, 0, 1, 1))
    with pytest.raises(TypeError):
        w.merge("not-a-word")  # type: ignore[arg-type]


def test_refine_bounding_box_none_image_no_change():
    bbox = BoundingBox.from_ltrb(0, 0, 10, 10)
    w = Word(text="x", bounding_box=bbox)
    w.refine_bounding_box(None)  # should warn & leave bbox unchanged
    assert w.bounding_box.to_ltrb() == (0, 0, 10, 10)


def test_refine_bounding_box_shrinks_to_content():
    # Full-image bounding box normalized
    w = Word(text="x", bounding_box=BoundingBox.from_ltrb(0, 0, 1, 1))
    img_h, img_w = 40, 80
    # White background (255), black rectangle (0) to represent text before inversion
    image = np.full((img_h, img_w), 255, dtype=np.uint8)
    image[5:15, 10:30] = 0
    w.refine_bounding_box(image)
    # Expect normalized bbox approx (10/80,5/40,30/80,15/40) after refine (no +1 expansion, clamped)
    left_, t, r, b = w.bounding_box.to_ltrb()
    assert left_ == pytest.approx(10 / 80, rel=1e-3)
    assert t == pytest.approx(5 / 40, rel=1e-3)
    assert r == pytest.approx(30 / 80, rel=1e-3)
    assert b == pytest.approx(15 / 40, rel=1e-3)


def test_crop_bottom_none_image_error():
    w = Word(text="x", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10))
    with pytest.raises(ValueError):
        w.crop_bottom(None)


def test_crop_top_none_image_error():
    w = Word(text="x", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10))
    with pytest.raises(ValueError):
        w.crop_top(None)


def test_ground_truth_exact_match_no_gt():
    w = Word(text="abc", bounding_box=BoundingBox.from_ltrb(0, 0, 1, 1))
    assert w.ground_truth_exact_match is False


def test_to_from_dict_with_ground_truth_and_keys():
    bbox = BoundingBox.from_ltrb(0, 0, 1, 1)
    gt_bbox = BoundingBox.from_ltrb(0.1, 0.1, 0.2, 0.2)
    w = Word(
        text="abc",
        bounding_box=bbox,
        ocr_confidence=0.5,
        word_labels=["l1"],
        ground_truth_text="abc",
        ground_truth_bounding_box=gt_bbox,
        ground_truth_match_keys={"k": 1},
    )
    d = w.to_dict()
    assert d["ground_truth_text"] == "abc"
    assert d["ground_truth_bounding_box"]["top_left"]["x"] == pytest.approx(0.1)
    assert d["ground_truth_match_keys"] == {"k": 1}
    round_trip = Word.from_dict(d)
    assert round_trip.text == "abc"
    assert round_trip.ground_truth_text == "abc"
    assert round_trip.ground_truth_match_keys == {"k": 1}
