import pytest
import numpy as np

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.word import Word


###############################################################################
# Fixtures (shared test data)
###############################################################################


@pytest.fixture
def pixel_bbox():
    """Pixel-space bounding box used for simple word construction."""
    return BoundingBox.from_ltrb(0, 0, 10, 10)


@pytest.fixture
def normalized_bbox():
    """Normalized bounding box (0-1) for scale tests."""
    return BoundingBox.from_ltrb(0.1, 0.2, 0.3, 0.4)


@pytest.fixture
def hello_word(pixel_bbox):
    """Word whose ground truth matches exactly (true path)."""
    return Word(text="Hello", bounding_box=pixel_bbox, ground_truth_text="Hello")


@pytest.fixture
def hello_world_words():
    """Pair of adjacent words (left, right) used for merge (left->right) tests."""
    return (
        Word(
            text="hello",
            bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10),
            ocr_confidence=0.9,
            ground_truth_text="HELLO",
        ),
        Word(
            text="world",
            bounding_box=BoundingBox.from_ltrb(10, 0, 20, 10),
            ocr_confidence=0.7,
            ground_truth_text="WORLD",
        ),
    )


###############################################################################
# Serialization (to_dict / from_dict)
###############################################################################


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


@pytest.fixture
def word_from_dict_case():
    bbox_dict = {
        "top_left": {"x": 0, "y": 0, "is_normalized": False},
        "bottom_right": {"x": 10, "y": 10, "is_normalized": False},
        "is_normalized": False,
    }
    w = Word.from_dict(
        {
            "type": "Word",
            "text": "test",
            "bounding_box": bbox_dict,
            "ocr_confidence": 0.99,
            "word_labels": ["label1"],
        }
    )
    return w, bbox_dict


def test_word_from_dict_text(word_from_dict_case):
    w, _ = word_from_dict_case
    assert w.text == "test"


def test_word_from_dict_bbox(word_from_dict_case):
    w, bbox_dict = word_from_dict_case
    assert w.bounding_box.to_ltrb() == BoundingBox.from_dict(bbox_dict).to_ltrb()


def test_word_from_dict_confidence(word_from_dict_case):
    w, _ = word_from_dict_case
    assert w.ocr_confidence == pytest.approx(0.99)


def test_word_from_dict_labels(word_from_dict_case):
    w, _ = word_from_dict_case
    assert w.word_labels == ["label1"]


###############################################################################
# Ground truth exact match flag
###############################################################################


def test_ground_truth_exact_match_true(hello_word):
    assert hello_word.ground_truth_exact_match is True


def test_ground_truth_exact_match_false(pixel_bbox):
    w = Word(text="Hello", bounding_box=pixel_bbox, ground_truth_text="World")
    assert w.ground_truth_exact_match is False


###############################################################################
# Scaling (normalized -> pixel, pixel no-op, deep copy semantics)
###############################################################################


@pytest.fixture
def scaled_word_case(normalized_bbox):
    """Original normalized word and its scaled pixel copy."""
    w = Word(text="hi", bounding_box=normalized_bbox, ocr_confidence=0.5)
    return w, w.scale(100, 200)


def test_scale_returns_scaled_word_scaled_bbox(scaled_word_case):
    _, scaled = scaled_word_case
    assert scaled.bounding_box.to_ltrb() == (10, 40, 30, 80)


def test_scale_returns_scaled_word_original_preserved(scaled_word_case):
    original, _ = scaled_word_case
    assert original.bounding_box.to_ltrb() == (0.1, 0.2, 0.3, 0.4)


@pytest.fixture
def scale_pixel_noop_case(caplog):
    """Pixel-space word; scaling should be a no-op copy with log message."""
    w = Word(
        text="pix",
        bounding_box=BoundingBox.from_ltrb(0, 0, 50, 20),
        ocr_confidence=0.7,
        ground_truth_text="PIX",
    )
    with caplog.at_level("INFO"):
        scaled = w.scale(200, 400)
    return w, scaled, caplog.records


def test_scale_noop_when_pixel_bbox(scale_pixel_noop_case):
    _, scaled, _ = scale_pixel_noop_case
    assert scaled.bounding_box.to_ltrb() == (0, 0, 50, 20)


def test_scale_noop_when_pixel_new_instance(scale_pixel_noop_case):
    w, scaled, _ = scale_pixel_noop_case
    assert scaled is not w


def test_scale_noop_when_pixel_ground_truth(scale_pixel_noop_case):
    _, scaled, _ = scale_pixel_noop_case
    assert scaled.ground_truth_text == "PIX"


def test_scale_noop_when_pixel_logs(scale_pixel_noop_case):
    _, _, records = scale_pixel_noop_case
    assert any("pixel-space bounding box" in r.message for r in records)


@pytest.fixture
def scale_pixel_copy_case():
    """Pixel-space deep copy independence test case."""
    w = Word(
        text="abc",
        bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10),
        ocr_confidence=0.5,
        word_labels=["L"],
    )
    scaled = w.scale(100, 200)
    w.text = "changed"
    w.word_labels.append("M")
    return w, scaled


def test_scale_pixel_deep_copy_text(scale_pixel_copy_case):
    _, scaled = scale_pixel_copy_case
    assert scaled.text == "abc"


def test_scale_pixel_deep_copy_labels(scale_pixel_copy_case):
    _, scaled = scale_pixel_copy_case
    assert scaled.word_labels == ["L"]


def test_fuzz_score_against_identical_single_assert():
    assert (
        Word(text="test", bounding_box=BoundingBox.from_ltrb(0, 0, 1, 1)).fuzz_score_against("test")
    ) == 100


###############################################################################
# Splitting (word -> two words) & related flags
###############################################################################


@pytest.fixture
def split_basic_case():
    """Split a word in the middle for width/text ground truth validation."""
    w = Word(
        text="hello",
        bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10),
        ground_truth_text="hello",
    )
    return w.split(bbox_split_offset=4, character_split_index=2)


def test_split_basic_left_text(split_basic_case):
    left, _ = split_basic_case
    assert left.text == "he"


def test_split_basic_right_text(split_basic_case):
    _, right = split_basic_case
    assert right.text == "llo"


def test_split_basic_left_width(split_basic_case):
    left, _ = split_basic_case
    assert left.bounding_box.width == 4


def test_split_basic_right_width(split_basic_case):
    _, right = split_basic_case
    assert right.bounding_box.width == 6


def test_split_basic_left_gt(split_basic_case):
    left, _ = split_basic_case
    assert left.ground_truth_text == "he"


def test_split_basic_right_gt(split_basic_case):
    _, right = split_basic_case
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


@pytest.fixture
def split_flags_case():
    """Split capturing split flag propagation & label copying."""
    w = Word(
        text="abcd",
        bounding_box=BoundingBox.from_ltrb(0, 0, 8, 8),
        word_labels=["x", "y"],
    )
    return w.split(bbox_split_offset=3, character_split_index=2)


def test_split_sets_split_flag_left(split_flags_case):
    left, _ = split_flags_case
    assert left.ground_truth_match_keys.get("split") is True


def test_split_sets_split_flag_right(split_flags_case):
    _, right = split_flags_case
    assert right.ground_truth_match_keys.get("split") is True


def test_split_labels_left(split_flags_case):
    left, _ = split_flags_case
    assert set(left.word_labels) == {"x", "y"}


def test_split_labels_right(split_flags_case):
    _, right = split_flags_case
    assert set(right.word_labels) == {"x", "y"}


###############################################################################
# Merging (concatenation of adjacent words) – order, confidence, labels
###############################################################################


@pytest.fixture
def merge_reversed_case():
    """Merge where 'self' starts to the right, exercising reversed order path."""
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
    return right


def test_merge_reversed_text(merge_reversed_case):
    assert merge_reversed_case.text == "helloworld"


def test_merge_reversed_ground_truth(merge_reversed_case):
    assert merge_reversed_case.ground_truth_text == "HELLOWORLD"


def test_merge_reversed_confidence(merge_reversed_case):
    assert merge_reversed_case.ocr_confidence == pytest.approx((0.8 + 0.6) / 2)


def test_merge_reversed_labels(merge_reversed_case):
    assert set(merge_reversed_case.word_labels) == {"foo", "bar"}


def test_merge_reversed_bbox(merge_reversed_case):
    assert merge_reversed_case.bounding_box.to_ltrb() == (0, 0, 20, 10)


@pytest.fixture
def merge_left_to_right_case(hello_world_words):
    """Standard left->right merge path case."""
    left, right = hello_world_words
    left.merge(right)
    return left


def test_merge_left_to_right_text(merge_left_to_right_case):
    assert merge_left_to_right_case.text == "helloworld"


def test_merge_left_to_right_ground_truth(merge_left_to_right_case):
    assert merge_left_to_right_case.ground_truth_text == "HELLOWORLD"


def test_merge_left_to_right_confidence(merge_left_to_right_case):
    assert merge_left_to_right_case.ocr_confidence == pytest.approx((0.9 + 0.7) / 2)


def test_merge_left_to_right_bbox(merge_left_to_right_case):
    assert merge_left_to_right_case.bounding_box.to_ltrb() == (0, 0, 20, 10)


def test_merge_confidence_both_none():
    a = Word(text="a", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10), ocr_confidence=None)
    b = Word(text="b", bounding_box=BoundingBox.from_ltrb(10, 0, 20, 10), ocr_confidence=None)
    a.merge(b)
    assert a.ocr_confidence is None


def test_merge_confidence_self_none_other_value():
    c = Word(text="c", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10), ocr_confidence=None)
    d = Word(text="d", bounding_box=BoundingBox.from_ltrb(10, 0, 20, 10), ocr_confidence=0.4)
    c.merge(d)
    assert c.ocr_confidence == pytest.approx(0.4)


def test_merge_confidence_other_none():
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


###############################################################################
# Bounding box refinement (content-driven shrink) & cropping
###############################################################################


@pytest.fixture
def refine_bbox_case():
    """Word covering full normalized image refined to tight content rectangle."""
    w = Word(text="x", bounding_box=BoundingBox.from_ltrb(0, 0, 1, 1))
    image = np.full((40, 80), 255, dtype=np.uint8)
    image[5:15, 10:30] = 0
    w.refine_bounding_box(image)
    return w


def test_refine_bounding_box_left(refine_bbox_case):
    left, _, _, _ = refine_bbox_case.bounding_box.to_ltrb()
    assert left == pytest.approx(10 / 80, rel=1e-3)


def test_refine_bounding_box_top(refine_bbox_case):
    _, top, _, _ = refine_bbox_case.bounding_box.to_ltrb()
    assert top == pytest.approx(5 / 40, rel=1e-3)


def test_refine_bounding_box_right(refine_bbox_case):
    _, _, right, _ = refine_bbox_case.bounding_box.to_ltrb()
    assert right == pytest.approx(30 / 80, rel=1e-3)


def test_refine_bounding_box_bottom(refine_bbox_case):
    _, _, _, bottom = refine_bbox_case.bounding_box.to_ltrb()
    assert bottom == pytest.approx(15 / 40, rel=1e-3)


def test_crop_bottom_none_image_error():
    w = Word(text="x", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10))
    with pytest.raises(ValueError):
        w.crop_bottom(None)


def test_crop_top_none_image_error():
    w = Word(text="x", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10))
    with pytest.raises(ValueError):
        w.crop_top(None)


def test_ground_truth_exact_match_no_gt_single_assert():
    assert Word(text="abc", bounding_box=BoundingBox.from_ltrb(0, 0, 1, 1)).ground_truth_exact_match is False


@pytest.fixture
def to_from_dict_gt_case():
    """Serialized + deserialized word including ground truth box & keys."""
    gt_bbox = BoundingBox.from_ltrb(0.1, 0.1, 0.2, 0.2)
    w = Word(
        text="abc",
        bounding_box=BoundingBox.from_ltrb(0, 0, 1, 1),
        ocr_confidence=0.5,
        word_labels=["l1"],
        ground_truth_text="abc",
        ground_truth_bounding_box=gt_bbox,
        ground_truth_match_keys={"k": 1},
    )
    d = w.to_dict()
    round_trip = Word.from_dict(d)
    return d, round_trip


def test_to_from_dict_gt_text(to_from_dict_gt_case):
    d, _ = to_from_dict_gt_case
    assert d["ground_truth_text"] == "abc"


def test_to_from_dict_gt_bbox_x(to_from_dict_gt_case):
    d, _ = to_from_dict_gt_case
    assert d["ground_truth_bounding_box"]["top_left"]["x"] == pytest.approx(0.1)


def test_to_from_dict_gt_keys(to_from_dict_gt_case):
    d, _ = to_from_dict_gt_case
    assert d["ground_truth_match_keys"] == {"k": 1}


def test_to_from_dict_round_trip_text(to_from_dict_gt_case):
    _, rt = to_from_dict_gt_case
    assert rt.text == "abc"


def test_to_from_dict_round_trip_gt_text(to_from_dict_gt_case):
    _, rt = to_from_dict_gt_case
    assert rt.ground_truth_text == "abc"


def test_to_from_dict_round_trip_keys(to_from_dict_gt_case):
    _, rt = to_from_dict_gt_case
    assert rt.ground_truth_match_keys == {"k": 1}


@pytest.fixture
def scale_normalized_case():
    """Scaling normalized word: main bbox -> pixel; GT bbox stays normalized (deep copy)."""
    w = Word(
        text="abc",
        bounding_box=BoundingBox.from_ltrb(0.1, 0.2, 0.4, 0.5),
        ocr_confidence=0.8,
        word_labels=["L1"],
        ground_truth_text="abc",
        ground_truth_bounding_box=BoundingBox.from_ltrb(0.15, 0.25, 0.35, 0.45),
        ground_truth_match_keys={"k": 1},
    )
    scaled = w.scale(200, 100)
    w.text = "changed"
    w.word_labels.append("L2")
    w.ground_truth_match_keys["k2"] = 2
    return scaled


def test_scale_normalized_bbox(scale_normalized_case):
    assert scale_normalized_case.bounding_box.to_ltrb() == (20, 20, 80, 50)


def test_scale_normalized_bbox_category(scale_normalized_case):
    assert scale_normalized_case.bounding_box.is_normalized is False


def test_scale_normalized_gt_bbox(scale_normalized_case):
    assert scale_normalized_case.ground_truth_bounding_box.to_ltrb() == pytest.approx((0.15, 0.25, 0.35, 0.45))


def test_scale_normalized_gt_bbox_category(scale_normalized_case):
    assert scale_normalized_case.ground_truth_bounding_box.is_normalized is True


def test_scale_normalized_text(scale_normalized_case):
    assert scale_normalized_case.text == "abc"


def test_scale_normalized_labels(scale_normalized_case):
    assert scale_normalized_case.word_labels == ["L1"]


def test_scale_normalized_keys(scale_normalized_case):
    assert scale_normalized_case.ground_truth_match_keys == {"k": 1}


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


@pytest.fixture
def merge_with_gt_case():
    """Merge two words each with aligned main + GT bounding boxes."""
    w1 = Word(text="A", bounding_box=BoundingBox.from_ltrb(0, 0, 5, 5), ground_truth_text="A", ground_truth_bounding_box=BoundingBox.from_ltrb(0, 0, 5, 5), word_labels=["l1"])
    w2 = Word(text="B", bounding_box=BoundingBox.from_ltrb(5, 0, 10, 5), ground_truth_text="B", ground_truth_bounding_box=BoundingBox.from_ltrb(5, 0, 10, 5), word_labels=["l2"])
    w1.merge(w2)
    return w1


def test_merge_with_gt_text(merge_with_gt_case):
    assert merge_with_gt_case.text == "AB"


def test_merge_with_gt_gt_text(merge_with_gt_case):
    assert merge_with_gt_case.ground_truth_text == "AB"


def test_merge_with_gt_bbox(merge_with_gt_case):
    assert merge_with_gt_case.bounding_box.to_ltrb() == (0, 0, 10, 5)


def test_merge_with_gt_labels(merge_with_gt_case):
    assert set(merge_with_gt_case.word_labels) == {"l1", "l2"}


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


@pytest.fixture
def split_with_gt_case():
    """Split where main & ground-truth bboxes share coordinate category (pixel)."""
    w = Word(text="hello", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10), ground_truth_text="hello", ground_truth_bounding_box=BoundingBox.from_ltrb(2, 2, 8, 8))
    return w.split(bbox_split_offset=4, character_split_index=2), w


def test_split_with_gt_left_text(split_with_gt_case):
    (left, _), _ = split_with_gt_case
    assert left.text == "he"


def test_split_with_gt_right_text(split_with_gt_case):
    (_, right), _ = split_with_gt_case
    assert right.text == "llo"


def test_split_with_gt_original_gt_text(split_with_gt_case):
    _, w = split_with_gt_case
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


@pytest.fixture
def split_zero_case():
    """Split at offset/index zero producing empty left word."""
    w = Word(text="hello", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10))
    return w.split(bbox_split_offset=0, character_split_index=0)


def test_split_zero_left_text(split_zero_case):
    left, _ = split_zero_case
    assert left.text == ""


def test_split_zero_right_text(split_zero_case):
    _, right = split_zero_case
    assert right.text == "hello"


def test_split_zero_left_width(split_zero_case):
    left, _ = split_zero_case
    assert left.bounding_box.width == 0


def test_split_zero_right_width(split_zero_case):
    _, right = split_zero_case
    assert right.bounding_box.width == 10


@pytest.fixture
def split_full_width_case():
    """Split with offset equal to full width -> right side zero width."""
    w = Word(text="hello", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10))
    return w.split(bbox_split_offset=10, character_split_index=2)


def test_split_full_width_left_text(split_full_width_case):
    left, _ = split_full_width_case
    assert left.text == "he"


def test_split_full_width_right_text(split_full_width_case):
    _, right = split_full_width_case
    assert right.text == "llo"


def test_split_full_width_left_width(split_full_width_case):
    left, _ = split_full_width_case
    assert left.bounding_box.width == 10


def test_split_full_width_right_width(split_full_width_case):
    _, right = split_full_width_case
    assert right.bounding_box.width == 0


@pytest.fixture
def merge_keys_case():
    """Merge combining distinct ground-truth match key dictionaries."""
    a = Word(text="a", bounding_box=BoundingBox.from_ltrb(0, 0, 5, 5), ground_truth_match_keys={"k1": True})
    b = Word(text="b", bounding_box=BoundingBox.from_ltrb(5, 0, 10, 5), ground_truth_match_keys={"k2": True})
    a.merge(b)
    return a


def test_merge_inherits_ground_truth_keys_k1(merge_keys_case):
    assert merge_keys_case.ground_truth_match_keys.get("k1") is True


def test_merge_inherits_ground_truth_keys_k2(merge_keys_case):
    assert merge_keys_case.ground_truth_match_keys.get("k2") is True


@pytest.fixture
def merge_one_gt_case():
    """Merge where only first word has ground-truth bbox/Text."""
    a = Word(text="hi", bounding_box=BoundingBox.from_ltrb(0, 0, 5, 5), ground_truth_bounding_box=BoundingBox.from_ltrb(0, 0, 5, 5))
    b = Word(text="there", bounding_box=BoundingBox.from_ltrb(5, 0, 12, 5))
    a.merge(b)
    return a


def test_merge_one_gt_text(merge_one_gt_case):
    assert merge_one_gt_case.text == "hithere"


def test_merge_one_gt_bbox(merge_one_gt_case):
    assert merge_one_gt_case.bounding_box.to_ltrb() == (0, 0, 12, 5)


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


def test_merge_only_other_has_ground_truth_left_to_right_single_assert():
    left = Word(text="ab", bounding_box=BoundingBox.from_ltrb(0, 0, 5, 5))
    right = Word(text="cd", bounding_box=BoundingBox.from_ltrb(5, 0, 10, 5), ground_truth_text="CD")
    left.merge(right)
    assert (left.text, left.ground_truth_text) == ("abcd", "CD")


def test_merge_only_other_has_ground_truth_reversed_order_single_assert():
    right = Word(text="XY", bounding_box=BoundingBox.from_ltrb(10, 0, 15, 5))
    left = Word(text="Z", bounding_box=BoundingBox.from_ltrb(0, 0, 10, 5), ground_truth_text="Z")
    right.merge(left)
    assert (right.text, right.ground_truth_text) == ("ZXY", "Z")


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


@pytest.fixture
def crop_bottom_case():
    """Cropping bottom of a full-coverage normalized word to content region."""
    image = np.full((40, 80), 255, dtype=np.uint8)
    image[25:35, 10:70] = 0
    w = Word(text="foo", bounding_box=BoundingBox.from_ltrb(0, 0, 1, 1))
    before = w.bounding_box.to_ltrb()
    w.crop_bottom(image)
    after = w.bounding_box.to_ltrb()
    return w, before, after


def test_crop_bottom_is_normalized(crop_bottom_case):
    w, _, _ = crop_bottom_case
    assert w.bounding_box.is_normalized is True


def test_crop_bottom_left_preserved(crop_bottom_case):
    w, before, after = crop_bottom_case
    assert pytest.approx(before[0]) == after[0]


def test_crop_bottom_top_preserved(crop_bottom_case):
    w, before, after = crop_bottom_case
    assert pytest.approx(before[1]) == after[1]


def test_crop_bottom_right_preserved(crop_bottom_case):
    w, before, after = crop_bottom_case
    assert pytest.approx(before[2]) == after[2]


def test_crop_bottom_bottom_within_bounds(crop_bottom_case):
    w, _, after = crop_bottom_case
    assert 0 < after[3] <= 1


@pytest.fixture
def crop_top_case():
    """Cropping top of a normalized word to remove whitespace."""
    image = np.full((40, 80), 255, dtype=np.uint8)
    image[5:15, 5:70] = 0
    w = Word(text="bar", bounding_box=BoundingBox.from_ltrb(0, 0, 1, 1))
    before = w.bounding_box.to_ltrb()
    w.crop_top(image)
    after = w.bounding_box.to_ltrb()
    return w, before, after


def test_crop_top_is_normalized(crop_top_case):
    w, _, _ = crop_top_case
    assert w.bounding_box.is_normalized is True


def test_crop_top_left_preserved(crop_top_case):
    w, before, after = crop_top_case
    assert pytest.approx(before[0]) == after[0]


def test_crop_top_bottom_within_bounds(crop_top_case):
    w, _, after = crop_top_case
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


@pytest.fixture
def crop_bottom_warn_case(caplog):
    """Force crop_bottom internal call to return None to exercise warning path."""
    w = Word(text="x", bounding_box=BoundingBox.from_ltrb(0, 0, 1, 1))
    class DummyBBox:
        def crop_bottom(self, image):  # type: ignore[no-untyped-def]
            return None
    w.bounding_box = DummyBBox()  # type: ignore[assignment]
    with caplog.at_level("WARNING"):
        w.crop_bottom(np.zeros((4, 4), dtype=np.uint8))
    return w, caplog.records


def test_crop_bottom_warns_logged(crop_bottom_warn_case):
    _, records = crop_bottom_warn_case
    assert any("Cropped bounding box is None" in r.message for r in records)


def test_crop_bottom_warns_sets_none(crop_bottom_warn_case):
    w, _ = crop_bottom_warn_case
    assert w.bounding_box is None


@pytest.fixture
def crop_top_warn_case(caplog):
    """Force crop_top internal call to return None to exercise warning path."""
    w = Word(text="y", bounding_box=BoundingBox.from_ltrb(0, 0, 1, 1))
    class DummyBBox:
        def crop_top(self, image):  # type: ignore[no-untyped-def]
            return None
    w.bounding_box = DummyBBox()  # type: ignore[assignment]
    with caplog.at_level("WARNING"):
        w.crop_top(np.zeros((4, 4), dtype=np.uint8))
    return w, caplog.records


def test_crop_top_warns_logged(crop_top_warn_case):
    _, records = crop_top_warn_case
    assert any("Cropped bounding box is None" in r.message for r in records)


def test_crop_top_warns_sets_none(crop_top_warn_case):
    w, _ = crop_top_warn_case
    assert w.bounding_box is None
