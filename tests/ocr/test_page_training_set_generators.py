"""Coverage tests for page.py training-set generator helpers (lines ~2810-3234)."""

import json

import numpy as np
import pytest

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pd_book_tools.ocr.page import Page
from pd_book_tools.ocr.word import Word


def _make_word(
    text: str,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    ground_truth: str | None = None,
    is_normalized: bool = True,
) -> Word:
    """Create a Word with optional ground truth."""
    word = Word(
        text=text,
        bounding_box=BoundingBox.from_ltrb(x1, y1, x2, y2, is_normalized=is_normalized),
        ocr_confidence=0.9,
    )
    if ground_truth:
        word.ground_truth_text = ground_truth
    return word


def _make_line(words):
    """Create a LINE block from words."""
    return Block(
        items=list(words),
        block_category=BlockCategory.LINE,
        child_type=BlockChildType.WORDS,
    )


def _make_paragraph(lines):
    """Create a PARAGRAPH block from lines."""
    return Block(
        items=list(lines),
        block_category=BlockCategory.PARAGRAPH,
        child_type=BlockChildType.BLOCKS,
    )


def _make_test_image(height: int = 100, width: int = 100) -> np.ndarray:
    """Create a simple BGR test image."""
    return np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)


def _make_page_with_words(
    words_list: list[str], image=None, normalized: bool = True
) -> Page:
    """Create a page with words positioned horizontally."""
    words = []
    if normalized:
        # Normalized coordinates: distribute words across [0.0, 1.0] range
        spacing = 0.2
        x_offset = 0.05
        for _i, text in enumerate(words_list):
            word = _make_word(
                text,
                x_offset,
                0.1,
                x_offset + 0.15,
                0.3,
                ground_truth=text,
                is_normalized=True,
            )
            words.append(word)
            x_offset += spacing
    else:
        # Pixel coordinates for backwards compatibility
        x_offset = 0
        for _i, text in enumerate(words_list):
            word = _make_word(
                text,
                x_offset,
                10,
                x_offset + 20,
                30,
                ground_truth=text,
                is_normalized=False,
            )
            words.append(word)
            x_offset += 25

    line = _make_line(words)
    para = _make_paragraph([line])
    page = Page(width=200, height=100, page_index=0, blocks=[para])

    if image is None:
        image = _make_test_image(100, 200)
    page.cv2_numpy_page_image = image

    return page


class TestGenerateDoctrChecks:
    """Test the generate_doctr_checks helper method."""

    def test_checks_creates_output_parent_if_exists(self, tmp_path):
        """generate_doctr_checks validates output path exists."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = _make_page_with_words(["hello", "world"])
        page.generate_doctr_checks(output_path)

    def test_checks_raises_on_nonexistent_parent(self, tmp_path):
        """generate_doctr_checks raises ValueError when parent doesn't exist."""
        output_path = tmp_path / "nonexistent" / "training_set"

        page = _make_page_with_words(["hello", "world"])
        with pytest.raises(ValueError, match="Output path does not exist"):
            page.generate_doctr_checks(output_path)

    def test_checks_with_no_items(self, tmp_path):
        """generate_doctr_checks handles page with no items."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = Page(width=100, height=100, page_index=0, blocks=[])
        page.cv2_numpy_page_image = _make_test_image()

        page.generate_doctr_checks(output_path)


class TestGenerateDoctrDetectionTrainingSet:
    """Test detection training set generation."""

    def test_detection_creates_directory_structure(self, tmp_path):
        """Detection export creates detection/images/ and labels.json."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = _make_page_with_words(["hello", "world"])
        page.generate_doctr_detection_training_set(
            output_path=output_path, prefix="test"
        )

        detection_path = output_path / "detection"
        assert detection_path.exists()
        assert (detection_path / "images").exists()
        assert (detection_path / "labels.json").exists()

    def test_detection_writes_image_file(self, tmp_path):
        """Detection export writes PNG image to detection/images/."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = _make_page_with_words(["hello", "world"])
        page.generate_doctr_detection_training_set(
            output_path=output_path, prefix="test"
        )

        image_files = list((output_path / "detection" / "images").glob("*.png"))
        assert len(image_files) == 1
        assert image_files[0].name == "test_0.png"

    def test_detection_labels_json_structure(self, tmp_path):
        """Detection labels.json has correct structure."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = _make_page_with_words(["hello", "world"])
        page.generate_doctr_detection_training_set(
            output_path=output_path, prefix="test"
        )

        with open(output_path / "detection" / "labels.json") as f:
            labels = json.load(f)

        assert "test_0.png" in labels
        assert "img_dimensions" in labels["test_0.png"]
        assert "img_hash" in labels["test_0.png"]
        assert "polygons" in labels["test_0.png"]
        assert len(labels["test_0.png"]["polygons"]) == 2

    def test_detection_image_hash_in_labels(self, tmp_path):
        """Detection labels include sha256 hash of image."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = _make_page_with_words(["hello", "world"])
        page.generate_doctr_detection_training_set(
            output_path=output_path, prefix="test"
        )

        with open(output_path / "detection" / "labels.json") as f:
            labels = json.load(f)

        img_hash = labels["test_0.png"]["img_hash"]
        assert len(img_hash) == 64
        assert all(c in "0123456789abcdef" for c in img_hash)

    def test_detection_with_word_filter(self, tmp_path):
        """Detection export respects word_filter predicate."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = _make_page_with_words(["hello", "world"])

        # Filter to only include words starting with 'w'
        def word_filter(w: Word) -> bool:
            return w.text.startswith("w")

        page.generate_doctr_detection_training_set(
            output_path=output_path, prefix="test", word_filter=word_filter
        )

        with open(output_path / "detection" / "labels.json") as f:
            labels = json.load(f)

        assert len(labels["test_0.png"]["polygons"]) == 1

    def test_detection_empty_page(self, tmp_path):
        """Detection export handles page with no words."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = Page(width=100, height=100, page_index=0, blocks=[])
        page.cv2_numpy_page_image = _make_test_image()

        page.generate_doctr_detection_training_set(
            output_path=output_path, prefix="test"
        )

        with open(output_path / "detection" / "labels.json") as f:
            labels = json.load(f)

        assert "test_0.png" in labels
        assert len(labels["test_0.png"]["polygons"]) == 0

    def test_detection_overwrites_existing_page_labels(self, tmp_path):
        """Detection export overwrites labels for same prefix+page_index."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page1 = _make_page_with_words(["hello", "world"])
        page1.generate_doctr_detection_training_set(
            output_path=output_path, prefix="test"
        )

        with open(output_path / "detection" / "labels.json") as f:
            labels_v1 = json.load(f)
        assert len(labels_v1["test_0.png"]["polygons"]) == 2

        page2 = _make_page_with_words(["foo"])
        page2.generate_doctr_detection_training_set(
            output_path=output_path, prefix="test"
        )

        with open(output_path / "detection" / "labels.json") as f:
            labels_v2 = json.load(f)

        assert len(labels_v2["test_0.png"]["polygons"]) == 1

    def test_detection_multiple_pages_accumulate(self, tmp_path):
        """Detection export preserves labels from other pages."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page0 = _make_page_with_words(["hello"])
        page0.generate_doctr_detection_training_set(
            output_path=output_path, prefix="test"
        )

        page1 = _make_page_with_words(["world"])
        page1.page_index = 1
        page1.generate_doctr_detection_training_set(
            output_path=output_path, prefix="test"
        )

        with open(output_path / "detection" / "labels.json") as f:
            labels = json.load(f)

        assert "test_0.png" in labels
        assert "test_1.png" in labels


class TestGenerateDoctrRecognitionTrainingSet:
    """Test recognition training set generation."""

    def test_recognition_creates_directory_structure(self, tmp_path):
        """Recognition export creates recognition/images/ and labels.json."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = _make_page_with_words(["hello", "world"])
        page.generate_doctr_recognition_training_set(
            output_path=output_path, prefix="test"
        )

        recognition_path = output_path / "recognition"
        assert recognition_path.exists()
        assert (recognition_path / "images").exists()
        assert (recognition_path / "labels.json").exists()

    def test_recognition_cropped_images_written(self, tmp_path):
        """Recognition export writes cropped word images."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = _make_page_with_words(["hello", "world"])
        page.generate_doctr_recognition_training_set(
            output_path=output_path, prefix="test"
        )

        image_files = list((output_path / "recognition" / "images").glob("*.png"))
        assert len(image_files) == 2

    def test_recognition_labels_json_structure(self, tmp_path):
        """Recognition labels.json maps image names to ground truth text."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = _make_page_with_words(["hello", "world"])
        page.generate_doctr_recognition_training_set(
            output_path=output_path, prefix="test"
        )

        with open(output_path / "recognition" / "labels.json") as f:
            labels = json.load(f)

        assert len(labels) == 2

        label_values = list(labels.values())
        assert "hello" in label_values
        assert "world" in label_values

    def test_recognition_with_word_filter(self, tmp_path):
        """Recognition export respects word_filter predicate."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = _make_page_with_words(["hello", "world"])

        def word_filter(w: Word) -> bool:
            return w.text.startswith("w")

        page.generate_doctr_recognition_training_set(
            output_path=output_path, prefix="test", word_filter=word_filter
        )

        with open(output_path / "recognition" / "labels.json") as f:
            labels = json.load(f)

        assert len(labels) == 1
        assert "world" in labels.values()

    def test_recognition_with_label_formatter(self, tmp_path):
        """Recognition export uses custom label_formatter if provided."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = _make_page_with_words(["hello", "world"])

        def label_formatter(w: Word) -> str:
            return w.text.upper()

        page.generate_doctr_recognition_training_set(
            output_path=output_path, prefix="test", label_formatter=label_formatter
        )

        with open(output_path / "recognition" / "labels.json") as f:
            labels = json.load(f)

        label_values = list(labels.values())
        assert "HELLO" in label_values
        assert "WORLD" in label_values

    def test_recognition_skips_words_without_ground_truth(self, tmp_path):
        """Recognition export skips words without ground_truth_text (no formatter)."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        # Create page with one word that has ground truth, one without
        word1 = _make_word(
            "hello", 0.1, 0.1, 0.25, 0.3, ground_truth="hello", is_normalized=True
        )
        word2 = Word(
            text="world",
            bounding_box=BoundingBox.from_ltrb(0.3, 0.1, 0.45, 0.3, is_normalized=True),
            ocr_confidence=0.9,
        )
        # word2 has no ground_truth_text

        line = _make_line([word1, word2])
        para = _make_paragraph([line])
        page = Page(width=100, height=100, page_index=0, blocks=[para])
        page.cv2_numpy_page_image = _make_test_image(100, 100)

        page.generate_doctr_recognition_training_set(
            output_path=output_path, prefix="test"
        )

        with open(output_path / "recognition" / "labels.json") as f:
            labels = json.load(f)

        assert len(labels) == 1
        assert "hello" in labels.values()

    def test_recognition_cleans_old_images(self, tmp_path):
        """Recognition export deletes old cropped images for same prefix+page_index."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page1 = _make_page_with_words(["hello", "world"])
        page1.generate_doctr_recognition_training_set(
            output_path=output_path, prefix="test"
        )

        image_files_v1 = list((output_path / "recognition" / "images").glob("*.png"))
        assert len(image_files_v1) == 2

        page2 = _make_page_with_words(["foo"])
        page2.generate_doctr_recognition_training_set(
            output_path=output_path, prefix="test"
        )

        image_files_v2 = list((output_path / "recognition" / "images").glob("*.png"))
        assert len(image_files_v2) == 1

    def test_recognition_accumulates_across_pages(self, tmp_path):
        """Recognition export preserves labels from other pages."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page0 = _make_page_with_words(["hello"])
        page0.generate_doctr_recognition_training_set(
            output_path=output_path, prefix="test"
        )

        page1 = _make_page_with_words(["world"])
        page1.page_index = 1
        page1.generate_doctr_recognition_training_set(
            output_path=output_path, prefix="test"
        )

        with open(output_path / "recognition" / "labels.json") as f:
            labels = json.load(f)

        assert len(labels) == 2


class TestConvertToTrainingSet:
    """Test the unified convert_to_training_set method."""

    def test_convert_creates_both_datasets(self, tmp_path):
        """convert_to_training_set creates both detection and recognition sets."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = _make_page_with_words(["hello", "world"])
        page.convert_to_training_set(output_path=output_path, prefix="test")

        assert (output_path / "detection").exists()
        assert (output_path / "detection" / "images").exists()
        assert (output_path / "detection" / "labels.json").exists()

        assert (output_path / "recognition").exists()
        assert (output_path / "recognition" / "images").exists()
        assert (output_path / "recognition" / "labels.json").exists()

    def test_convert_with_word_filter(self, tmp_path):
        """convert_to_training_set applies word_filter to both datasets."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = _make_page_with_words(["hello", "world"])

        def word_filter(w: Word) -> bool:
            return w.text.startswith("h")

        page.convert_to_training_set(
            output_path=output_path, prefix="test", word_filter=word_filter
        )

        with open(output_path / "detection" / "labels.json") as f:
            detection_labels = json.load(f)
        assert len(detection_labels["test_0.png"]["polygons"]) == 1

        with open(output_path / "recognition" / "labels.json") as f:
            recognition_labels = json.load(f)
        assert len(recognition_labels) == 1
        assert "hello" in recognition_labels.values()

    def test_convert_empty_page(self, tmp_path):
        """convert_to_training_set handles page with no words."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = Page(width=100, height=100, page_index=0, blocks=[])
        page.cv2_numpy_page_image = _make_test_image()

        page.convert_to_training_set(output_path=output_path, prefix="test")

        assert (output_path / "detection" / "labels.json").exists()
        assert (output_path / "recognition" / "labels.json").exists()


class TestPixelSpaceExport:
    """Tests for pixel-space (is_normalized=False) bounding box handling in export.

    Regression tests for #166: detection and recognition export paths were
    unconditionally scaling coordinates, corrupting pixel-space training data.
    """

    def _make_pixel_word(
        self,
        text: str,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        ground_truth: str | None = None,
    ) -> Word:
        """Create a Word with pixel-space (non-normalized) bounding box."""
        word = Word(
            text=text,
            bounding_box=BoundingBox.from_ltrb(
                float(x1), float(y1), float(x2), float(y2), is_normalized=False
            ),
            ocr_confidence=0.9,
        )
        if ground_truth:
            word.ground_truth_text = ground_truth
        return word

    def _make_pixel_page(self, img_h: int = 100, img_w: int = 200) -> Page:
        """Create a 200x100 page with pixel-space words that stay within image bounds."""
        # Words at pixel coords: (10,10)-(30,40) and (50,10)-(80,40)
        # On a 200x100 image these are completely valid, in-bounds coords.
        w1 = self._make_pixel_word("hello", 10, 10, 30, 40, ground_truth="hello")
        w2 = self._make_pixel_word("world", 50, 10, 80, 40, ground_truth="world")
        line = Block(
            items=[w1, w2],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )
        para = Block(
            items=[line],
            block_category=BlockCategory.PARAGRAPH,
            child_type=BlockChildType.BLOCKS,
        )
        page = Page(width=img_w, height=img_h, page_index=0, blocks=[para])
        page.cv2_numpy_page_image = np.random.randint(
            0, 256, (img_h, img_w, 3), dtype=np.uint8
        )
        return page

    # ------------------------------------------------------------------
    # Detection export — pixel-space
    # ------------------------------------------------------------------

    def test_detection_pixel_space_polygon_coords_are_in_bounds(self, tmp_path):
        """Detection export with pixel-space boxes must NOT multiply coords by image dims.

        Before fix: word at (10,10)-(30,40) on a 200x100 image was scaled to
        (2000,1000)-(6000,4000) — completely out of bounds.
        After fix: coords pass through unchanged (clamped/int-cast only).
        """
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = self._make_pixel_page(img_h=100, img_w=200)
        page.generate_doctr_detection_training_set(
            output_path=output_path, prefix="test"
        )

        with open(output_path / "detection" / "labels.json") as f:
            labels = json.load(f)

        polygons = labels["test_0.png"]["polygons"]
        assert len(polygons) == 2

        # All polygon coordinates must be within the image dimensions
        img_w, img_h = labels["test_0.png"]["img_dimensions"]
        for poly in polygons:
            for x, y in poly:
                assert 0 <= x <= img_w, (
                    f"x={x} out of bounds [0, {img_w}]; pixel-space coords were wrongly scaled"
                )
                assert 0 <= y <= img_h, (
                    f"y={y} out of bounds [0, {img_h}]; pixel-space coords were wrongly scaled"
                )

    def test_detection_pixel_space_polygon_values_are_correct(self, tmp_path):
        """Detection export must produce the original pixel coordinates, not scaled ones."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = self._make_pixel_page(img_h=100, img_w=200)
        page.generate_doctr_detection_training_set(
            output_path=output_path, prefix="test"
        )

        with open(output_path / "detection" / "labels.json") as f:
            labels = json.load(f)

        polygons = labels["test_0.png"]["polygons"]
        first_poly = polygons[0]
        xs = [pt[0] for pt in first_poly]
        ys = [pt[1] for pt in first_poly]
        assert min(xs) == 10, (
            f"x min {min(xs)} != 10; pixel-space coords were wrongly scaled"
        )
        assert max(xs) == 30, (
            f"x max {max(xs)} != 30; pixel-space coords were wrongly scaled"
        )
        assert min(ys) == 10, (
            f"y min {min(ys)} != 10; pixel-space coords were wrongly scaled"
        )
        assert max(ys) == 40, (
            f"y max {max(ys)} != 40; pixel-space coords were wrongly scaled"
        )

    # ------------------------------------------------------------------
    # Recognition export — pixel-space
    # ------------------------------------------------------------------

    def test_recognition_pixel_space_does_not_raise(self, tmp_path):
        """Recognition export with pixel-space boxes must not raise ValueError.

        Before fix: bbox.scale() was called unconditionally and raised
        'ValueError: scale() expected a normalized bounding box'.
        """
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = self._make_pixel_page(img_h=100, img_w=200)
        # Should not raise — pixel-space boxes must pass through
        page.generate_doctr_recognition_training_set(
            output_path=output_path, prefix="test"
        )

    def test_recognition_pixel_space_writes_correct_crops(self, tmp_path):
        """Recognition export with pixel-space boxes writes non-empty crops."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = self._make_pixel_page(img_h=100, img_w=200)
        page.generate_doctr_recognition_training_set(
            output_path=output_path, prefix="test"
        )

        image_files = list((output_path / "recognition" / "images").glob("*.png"))
        assert len(image_files) == 2

        with open(output_path / "recognition" / "labels.json") as f:
            labels = json.load(f)

        label_values = list(labels.values())
        assert "hello" in label_values
        assert "world" in label_values

    def test_recognition_pixel_space_crop_filename_uses_pixel_coords(self, tmp_path):
        """Recognition export uses the original pixel coords in the crop filename."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = self._make_pixel_page(img_h=100, img_w=200)
        page.generate_doctr_recognition_training_set(
            output_path=output_path, prefix="test"
        )

        image_files = sorted((output_path / "recognition" / "images").glob("*.png"))
        # Filenames encode minX, maxX, minY, maxY — all must be <= image dims
        img_w, img_h = 200, 100
        for f in image_files:
            parts = f.stem.split("_")
            x1, x2, y1, y2 = (
                int(parts[-4]),
                int(parts[-3]),
                int(parts[-2]),
                int(parts[-1]),
            )
            assert 0 <= x1 <= img_w, f"x1={x1} out of bounds in filename {f.name}"
            assert 0 <= x2 <= img_w, f"x2={x2} out of bounds in filename {f.name}"
            assert 0 <= y1 <= img_h, f"y1={y1} out of bounds in filename {f.name}"
            assert 0 <= y2 <= img_h, f"y2={y2} out of bounds in filename {f.name}"

    # ------------------------------------------------------------------
    # Normalized parity — confirm existing normalized behavior unchanged
    # ------------------------------------------------------------------

    def test_detection_normalized_parity(self, tmp_path):
        """Normalized-space detection export still produces scaled-up polygon coords."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        # Word at normalized (0.1, 0.1)-(0.3, 0.4) on 200x100 image
        # Expected pixel polygon: x in [20,60], y in [10,40]
        word = Word(
            text="hello",
            bounding_box=BoundingBox.from_ltrb(0.1, 0.1, 0.3, 0.4, is_normalized=True),
            ocr_confidence=0.9,
        )
        word.ground_truth_text = "hello"
        line = Block(
            items=[word],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )
        para = Block(
            items=[line],
            block_category=BlockCategory.PARAGRAPH,
            child_type=BlockChildType.BLOCKS,
        )
        page = Page(width=200, height=100, page_index=0, blocks=[para])
        page.cv2_numpy_page_image = np.zeros((100, 200, 3), dtype=np.uint8)

        page.generate_doctr_detection_training_set(
            output_path=output_path, prefix="test"
        )

        with open(output_path / "detection" / "labels.json") as f:
            labels = json.load(f)

        poly = labels["test_0.png"]["polygons"][0]
        xs = [pt[0] for pt in poly]
        ys = [pt[1] for pt in poly]
        # 0.1 * 200 = 20, 0.3 * 200 = 60; 0.1 * 100 = 10, 0.4 * 100 = 40
        assert min(xs) == 20
        assert max(xs) == 60
        assert min(ys) == 10
        assert max(ys) == 40

    def test_recognition_normalized_parity(self, tmp_path):
        """Normalized-space recognition export still produces correct crops."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = _make_page_with_words(["hello"], normalized=True)
        page.generate_doctr_recognition_training_set(
            output_path=output_path, prefix="test"
        )

        image_files = list((output_path / "recognition" / "images").glob("*.png"))
        assert len(image_files) == 1

        with open(output_path / "recognition" / "labels.json") as f:
            labels = json.load(f)
        assert "hello" in labels.values()


class TestTrainingSetGeneratorErrorHandling:
    """Test error handling in training set generators."""

    def test_detection_raises_without_image(self, tmp_path):
        """generate_doctr_detection_training_set raises when no image is set."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = _make_page_with_words(["hello", "world"])
        page.cv2_numpy_page_image = None

        with pytest.raises(ValueError, match="cv2_numpy_page_image is not set"):
            page.generate_doctr_detection_training_set(
                output_path=output_path, prefix="test"
            )

    def test_recognition_raises_without_image(self, tmp_path):
        """generate_doctr_recognition_training_set raises when no image is set."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = _make_page_with_words(["hello", "world"])
        page.cv2_numpy_page_image = None

        with pytest.raises(ValueError, match="cv2_numpy_page_image is not set"):
            page.generate_doctr_recognition_training_set(
                output_path=output_path, prefix="test"
            )

    def test_detection_raises_nonexistent_parent(self, tmp_path):
        """generate_doctr_detection_training_set raises on nonexistent parent."""
        output_path = tmp_path / "nonexistent" / "training_set"

        page = _make_page_with_words(["hello", "world"])

        with pytest.raises(ValueError, match="Output path does not exist"):
            page.generate_doctr_detection_training_set(
                output_path=output_path, prefix="test"
            )

    def test_recognition_raises_nonexistent_parent(self, tmp_path):
        """generate_doctr_recognition_training_set raises on nonexistent parent."""
        output_path = tmp_path / "nonexistent" / "training_set"

        page = _make_page_with_words(["hello", "world"])

        with pytest.raises(ValueError, match="Output path does not exist"):
            page.generate_doctr_recognition_training_set(
                output_path=output_path, prefix="test"
            )
