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


def test_scale_noop_when_pixel(caplog):
    bbox = BoundingBox.from_ltrb(0, 0, 50, 20)  # pixel box (not normalized)
    w = Word(text="pix", bounding_box=bbox, ocr_confidence=0.7, ground_truth_text="PIX")
    with caplog.at_level("INFO"):
        scaled = w.scale(200, 400)
    # Bounding box unchanged
    assert scaled.bounding_box.to_ltrb() == (0, 0, 50, 20)
    # Object is new instance (copy) not the same
    assert scaled is not w
    # Ground truth carried over
    assert scaled.ground_truth_text == "PIX"
    # Log message emitted
    assert any("pixel-space bounding box" in rec.message for rec in caplog.records)


def test_scale_pixel_deep_copy_independence():
    bbox = BoundingBox.from_ltrb(0, 0, 10, 10)
    w = Word(
        text="abc", bounding_box=bbox, ocr_confidence=0.5, word_labels=["L"]
    )  # pixel
    scaled = w.scale(100, 200)
    # mutate original after scaling
    w.text = "changed"
    w.word_labels.append("M")
    # scaled copy should remain unchanged
    assert scaled.text == "abc"
    assert scaled.word_labels == ["L"]


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
    [
        (-1, 2, ValueError),
        (2, -1, ValueError),
        (5, 10, IndexError),
        (11, 2, ValueError),
    ],
)
def test_split_errors(bbox_split_offset, character_split_index, exc):
    w = Word(text="hello", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10))
    with pytest.raises(exc):
        w.split(
            bbox_split_offset=bbox_split_offset,
            character_split_index=character_split_index,
        )


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
    a = Word(
        text="a", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10), ocr_confidence=None
    )
    b = Word(
        text="b", bounding_box=BoundingBox.from_ltrb(10, 0, 20, 10), ocr_confidence=None
    )
    a.merge(b)
    assert a.ocr_confidence is None

    # self None, other has value
    c = Word(
        text="c", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10), ocr_confidence=None
    )
    d = Word(
        text="d", bounding_box=BoundingBox.from_ltrb(10, 0, 20, 10), ocr_confidence=0.4
    )
    c.merge(d)
    assert c.ocr_confidence == pytest.approx(0.4)

    # self has value, other None
    e = Word(
        text="e", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10), ocr_confidence=0.7
    )
    f = Word(
        text="f", bounding_box=BoundingBox.from_ltrb(10, 0, 20, 10), ocr_confidence=None
    )
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


def test_scale_normalized_keeps_ground_truth_and_keys_deep_copy():
    bbox = BoundingBox.from_ltrb(0.1, 0.2, 0.4, 0.5)  # normalized
    gt_bbox = BoundingBox.from_ltrb(0.15, 0.25, 0.35, 0.45)  # normalized
    w = Word(
        text="abc",
        bounding_box=bbox,
        ocr_confidence=0.8,
        word_labels=["L1"],
        ground_truth_text="abc",
        ground_truth_bounding_box=gt_bbox,
        ground_truth_match_keys={"k": 1},
    )
    scaled = w.scale(200, 100)  # width, height
    # scaled bbox should now be pixel (0.1*200=20, etc.)
    assert scaled.bounding_box.to_ltrb() == (20, 20, 80, 50)
    assert scaled.bounding_box.is_normalized is False
    # ground truth bbox unchanged & still normalized
    assert scaled.ground_truth_bounding_box.to_ltrb() == pytest.approx(
        (0.15, 0.25, 0.35, 0.45)
    )
    assert scaled.ground_truth_bounding_box.is_normalized is True
    # deep copy: mutate original
    w.text = "changed"
    w.word_labels.append("L2")
    w.ground_truth_match_keys["k2"] = 2
    assert scaled.text == "abc"
    assert scaled.word_labels == ["L1"]
    assert scaled.ground_truth_match_keys == {"k": 1}


def test_merge_coordinate_mismatch_raises():
    a = Word(text="a", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10))  # pixel
    b = Word(
        text="b", bounding_box=BoundingBox.from_ltrb(0.1, 0.1, 0.2, 0.2)
    )  # normalized
    with pytest.raises(ValueError):
        a.merge(b)


def test_merge_ground_truth_coordinate_mismatch_raises():
    w1 = Word(
        text="a",
        bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10),  # pixel
        ground_truth_text="A",
        ground_truth_bounding_box=BoundingBox.from_ltrb(0, 0, 5, 5),  # pixel
    )
    w2 = Word(
        text="b",
        bounding_box=BoundingBox.from_ltrb(20, 0, 30, 10),  # pixel
        ground_truth_text="B",
        ground_truth_bounding_box=BoundingBox.from_ltrb(
            0.1, 0.1, 0.2, 0.2
        ),  # normalized
    )
    with pytest.raises(ValueError):
        w1.merge(w2)


def test_merge_word_ground_truth_vs_main_mismatch_raises():
    w_bad = Word(
        text="x",
        bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10),  # pixel
        ground_truth_bounding_box=BoundingBox.from_ltrb(
            0.1, 0.1, 0.2, 0.2
        ),  # normalized (mismatch)
    )
    w_other = Word(
        text="y",
        bounding_box=BoundingBox.from_ltrb(10, 0, 20, 10),  # pixel
    )
    with pytest.raises(ValueError):
        w_bad.merge(w_other)


def test_merge_with_both_ground_truth_matching_system_success():
    # Both words have pixel-space main and ground-truth bboxes (matching systems) -> no raise
    w1 = Word(
        text="A",
        bounding_box=BoundingBox.from_ltrb(0, 0, 5, 5),
        ground_truth_text="A",
        ground_truth_bounding_box=BoundingBox.from_ltrb(0, 0, 5, 5),
        word_labels=["l1"],
    )
    w2 = Word(
        text="B",
        bounding_box=BoundingBox.from_ltrb(5, 0, 10, 5),
        ground_truth_text="B",
        ground_truth_bounding_box=BoundingBox.from_ltrb(5, 0, 10, 5),
        word_labels=["l2"],
    )
    w1.merge(w2)
    assert w1.text == "AB"
    assert w1.ground_truth_text == "AB"
    assert w1.bounding_box.to_ltrb() == (0, 0, 10, 5)
    # labels combined & deduped
    assert set(w1.word_labels) == {"l1", "l2"}


def test_split_ground_truth_coordinate_mismatch_raises():
    w = Word(
        text="hello",
        bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10),  # pixel
        ground_truth_text="hello",
        ground_truth_bounding_box=BoundingBox.from_ltrb(
            0.1, 0.1, 0.9, 0.9
        ),  # normalized mismatch
    )
    with pytest.raises(ValueError):
        w.split(bbox_split_offset=5, character_split_index=2)


def test_split_with_ground_truth_same_category():
    w = Word(
        text="hello",
        bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10),
        ground_truth_text="hello",
        ground_truth_bounding_box=BoundingBox.from_ltrb(2, 2, 8, 8),  # pixel
    )
    left, right = w.split(bbox_split_offset=4, character_split_index=2)
    assert left.text == "he"
    assert right.text == "llo"
    # original ground truth text unaffected
    assert w.ground_truth_text == "hello"


def test_split_ground_truth_coordinate_mismatch_reversed():
    # Here main bbox is normalized but ground truth bbox is pixel -> mismatch
    w = Word(
        text="hello",
        bounding_box=BoundingBox.from_ltrb(0.0, 0.0, 1.0, 1.0),  # normalized
        ground_truth_text="hello",
        ground_truth_bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10),  # pixel
    )
    with pytest.raises(ValueError):
        w.split(bbox_split_offset=0.5, character_split_index=2)


def test_split_zero_offset_and_index_zero():
    w = Word(text="hello", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10))
    left, right = w.split(bbox_split_offset=0, character_split_index=0)
    assert left.text == ""
    assert right.text == "hello"
    assert left.bounding_box.width == 0
    assert right.bounding_box.width == 10


def test_split_offset_equals_width():
    w = Word(text="hello", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10))
    left, right = w.split(bbox_split_offset=10, character_split_index=2)
    # Entire geometry assigned to left, right gets zero-width geometry
    assert left.text == "he"
    assert right.text == "llo"
    assert left.bounding_box.width == 10
    assert right.bounding_box.width == 0


def test_merge_inherits_ground_truth_keys():
    a = Word(
        text="a",
        bounding_box=BoundingBox.from_ltrb(0, 0, 5, 5),
        ground_truth_match_keys={"k1": True},
    )
    b = Word(
        text="b",
        bounding_box=BoundingBox.from_ltrb(5, 0, 10, 5),
        ground_truth_match_keys={"k2": True},
    )
    a.merge(b)
    assert a.ground_truth_match_keys.get("k1") is True
    assert a.ground_truth_match_keys.get("k2") is True


def test_merge_one_has_ground_truth_bbox():
    a = Word(
        text="hi",
        bounding_box=BoundingBox.from_ltrb(0, 0, 5, 5),
        ground_truth_bounding_box=BoundingBox.from_ltrb(0, 0, 5, 5),  # pixel
    )
    b = Word(
        text="there",
        bounding_box=BoundingBox.from_ltrb(5, 0, 12, 5),
        # no ground truth bbox
    )
    a.merge(b)
    assert a.text == "hithere"
    assert a.bounding_box.to_ltrb() == (0, 0, 12, 5)


def test_refine_bounding_box_no_content_returns_same():
    # Create a pixel-space word whose ROI has no foreground (after inversion+threshold)
    w = Word(text="x", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10))
    image = np.full(
        (20, 20), 255, dtype=np.uint8
    )  # all white -> inverted all black -> no non-zero
    before = w.bounding_box.to_ltrb()
    w.refine_bounding_box(image)
    assert w.bounding_box.to_ltrb() == before


def test_merge_other_word_ground_truth_vs_main_mismatch_raises():
    good = Word(
        text="ok",
        bounding_box=BoundingBox.from_ltrb(0, 0, 5, 5),
    )
    bad = Word(
        text="bad",
        bounding_box=BoundingBox.from_ltrb(5, 0, 10, 5),  # pixel
        ground_truth_bounding_box=BoundingBox.from_ltrb(0.1, 0.1, 0.2, 0.2),  # normalized mismatch
    )
    with pytest.raises(ValueError):
        good.merge(bad)


def test_merge_only_other_has_ground_truth_left_to_right():
    left = Word(
        text="ab",
        bounding_box=BoundingBox.from_ltrb(0, 0, 5, 5),
    )
    right = Word(
        text="cd",
        bounding_box=BoundingBox.from_ltrb(5, 0, 10, 5),
        ground_truth_text="CD",
    )
    left.merge(right)
    assert left.text == "abcd"
    # ground truth text should now be just the other's since self had none
    assert left.ground_truth_text == "CD"


def test_merge_only_other_has_ground_truth_reversed_order():
    right = Word(
        text="XY",
        bounding_box=BoundingBox.from_ltrb(10, 0, 15, 5),
    )
    left = Word(
        text="Z",
        bounding_box=BoundingBox.from_ltrb(0, 0, 10, 5),
        ground_truth_text="Z",
    )
    right.merge(left)  # right is to the right -> reversed order merge path
    assert right.text == "ZXY"
    assert right.ground_truth_text == "Z"  # only left contributed


def test_merge_label_dedup_multiple_duplicates():
    a = Word(
        text="a",
        bounding_box=BoundingBox.from_ltrb(0, 0, 5, 5),
        word_labels=["l1", "l2", "l2"],
    )
    b = Word(
        text="b",
        bounding_box=BoundingBox.from_ltrb(5, 0, 10, 5),
        word_labels=["l2", "l3", "l1", "l3"],
    )
    a.merge(b)
    assert set(a.word_labels) == {"l1", "l2", "l3"}


def test_crop_bottom_success():
    # Create normalized word covering whole image; add content only in lower half
    img_h, img_w = 40, 80
    image = np.full((img_h, img_w), 255, dtype=np.uint8)
    image[25:35, 10:70] = 0  # simulate text (black)
    w = Word(text="foo", bounding_box=BoundingBox.from_ltrb(0, 0, 1, 1))
    before = w.bounding_box.to_ltrb()
    w.crop_bottom(image)
    after = w.bounding_box.to_ltrb()
    # Should still be normalized coords; y2 possibly adjusted upward
    assert w.bounding_box.is_normalized is True
    assert after[0] == pytest.approx(before[0])  # left unchanged
    assert after[1] == pytest.approx(before[1])  # top unchanged
    assert after[2] == pytest.approx(before[2])  # right unchanged
    # bottom should not exceed 1
    assert 0 < after[3] <= 1


def test_crop_top_success():
    img_h, img_w = 40, 80
    image = np.full((img_h, img_w), 255, dtype=np.uint8)
    image[5:15, 5:70] = 0  # content near top half
    w = Word(text="bar", bounding_box=BoundingBox.from_ltrb(0, 0, 1, 1))
    before = w.bounding_box.to_ltrb()
    w.crop_top(image)
    after = w.bounding_box.to_ltrb()
    assert w.bounding_box.is_normalized is True
    assert after[0] == pytest.approx(before[0])
    # bottom should be >= previous bottom (still 1) or maybe slightly less after crop
    assert 0 < after[3] <= 1


def test_crop_bottom_missing_bbox_error():
    w = Word(text="x", bounding_box=BoundingBox.from_ltrb(0, 0, 1, 1))
    # Force invalid state
    w.bounding_box = None  # type: ignore
    with pytest.raises(ValueError):
        w.crop_bottom(np.zeros((10, 10), dtype=np.uint8))


def test_crop_top_missing_bbox_error():
    w = Word(text="x", bounding_box=BoundingBox.from_ltrb(0, 0, 1, 1))
    w.bounding_box = None  # type: ignore
    with pytest.raises(ValueError):
        w.crop_top(np.zeros((10, 10), dtype=np.uint8))


def test_crop_bottom_warns_when_internal_returns_none(caplog):
    # Force crop_bottom to return None to hit warning branch (line ~298)
    w = Word(text="x", bounding_box=BoundingBox.from_ltrb(0, 0, 1, 1))

    class DummyBBox:
        def crop_bottom(self, image):  # type: ignore[no-untyped-def]
            return None

    w.bounding_box = DummyBBox()  # type: ignore[assignment]
    with caplog.at_level("WARNING"):
        w.crop_bottom(np.zeros((4, 4), dtype=np.uint8))
    assert any("Cropped bounding box is None" in r.message for r in caplog.records)
    assert w.bounding_box is None  # now set to None


def test_crop_top_warns_when_internal_returns_none(caplog):
    # Force crop_top to return None to hit warning branch (line ~313)
    w = Word(text="y", bounding_box=BoundingBox.from_ltrb(0, 0, 1, 1))

    class DummyBBox:
        def crop_top(self, image):  # type: ignore[no-untyped-def]
            return None

    w.bounding_box = DummyBBox()  # type: ignore[assignment]
    with caplog.at_level("WARNING"):
        w.crop_top(np.zeros((4, 4), dtype=np.uint8))
    assert any("Cropped bounding box is None" in r.message for r in caplog.records)
    assert w.bounding_box is None
