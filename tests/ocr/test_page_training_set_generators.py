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
    """Create a Word with optional ground truth.

    By default uses normalized coordinates (0.0-1.0) for compatibility with
    recognition training set methods that use scale().
    """
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
    """Create a page with words positioned horizontally.

    Words are created with normalized coordinates (0.0-1.0) by default for
    compatibility with training set methods. Use normalized=False for pixel coords.
    """
    words = []
    if normalized:
        # Normalized coordinates: distribute words across [0.0, 1.0] range
        spacing = 0.2
        x_offset = 0.05
        for i, text in enumerate(words_list):
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
        for i, text in enumerate(words_list):
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
        # Should not raise an error
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
        # Should complete without error


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

        # Verify directory structure
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

        # Check that image file exists
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

        # Should have 2 polygons (2 words)
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
        # Hash should be a valid hex string of length 64 (SHA256)
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

        # Should have 1 polygon (only "world")
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

        # First export
        page1 = _make_page_with_words(["hello", "world"])
        page1.generate_doctr_detection_training_set(
            output_path=output_path, prefix="test"
        )

        with open(output_path / "detection" / "labels.json") as f:
            labels_v1 = json.load(f)
        assert len(labels_v1["test_0.png"]["polygons"]) == 2

        # Second export with same prefix+page_index but different words
        page2 = _make_page_with_words(["foo"])
        page2.generate_doctr_detection_training_set(
            output_path=output_path, prefix="test"
        )

        with open(output_path / "detection" / "labels.json") as f:
            labels_v2 = json.load(f)

        # Should have overwritten: now only 1 polygon
        assert len(labels_v2["test_0.png"]["polygons"]) == 1

    def test_detection_multiple_pages_accumulate(self, tmp_path):
        """Detection export preserves labels from other pages."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        # Page 0
        page0 = _make_page_with_words(["hello"])
        page0.generate_doctr_detection_training_set(
            output_path=output_path, prefix="test"
        )

        # Page 1
        page1 = _make_page_with_words(["world"])
        page1.page_index = 1
        page1.generate_doctr_detection_training_set(
            output_path=output_path, prefix="test"
        )

        with open(output_path / "detection" / "labels.json") as f:
            labels = json.load(f)

        # Should have both test_0.png and test_1.png
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

        # Verify directory structure
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

        # Check that cropped images exist
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

        # Should have 2 entries (2 words with ground truth)
        assert len(labels) == 2

        # Check that labels contain the ground truth text
        label_values = list(labels.values())
        assert "hello" in label_values
        assert "world" in label_values

    def test_recognition_with_word_filter(self, tmp_path):
        """Recognition export respects word_filter predicate."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = _make_page_with_words(["hello", "world"])

        # Filter to only include words starting with 'w'
        def word_filter(w: Word) -> bool:
            return w.text.startswith("w")

        page.generate_doctr_recognition_training_set(
            output_path=output_path, prefix="test", word_filter=word_filter
        )

        with open(output_path / "recognition" / "labels.json") as f:
            labels = json.load(f)

        # Should have 1 entry (only "world")
        assert len(labels) == 1
        assert "world" in labels.values()

    def test_recognition_with_label_formatter(self, tmp_path):
        """Recognition export uses custom label_formatter if provided."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = _make_page_with_words(["hello", "world"])

        # Custom formatter: uppercase the text
        def label_formatter(w: Word) -> str:
            return w.text.upper()

        page.generate_doctr_recognition_training_set(
            output_path=output_path, prefix="test", label_formatter=label_formatter
        )

        with open(output_path / "recognition" / "labels.json") as f:
            labels = json.load(f)

        # Labels should be uppercase
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

        # Should only have 1 entry
        assert len(labels) == 1
        assert "hello" in labels.values()

    def test_recognition_cleans_old_images(self, tmp_path):
        """Recognition export deletes old cropped images for same prefix+page_index."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        # First export with 2 words
        page1 = _make_page_with_words(["hello", "world"])
        page1.generate_doctr_recognition_training_set(
            output_path=output_path, prefix="test"
        )

        image_files_v1 = list((output_path / "recognition" / "images").glob("*.png"))
        assert len(image_files_v1) == 2

        # Second export with 1 word
        page2 = _make_page_with_words(["foo"])
        page2.generate_doctr_recognition_training_set(
            output_path=output_path, prefix="test"
        )

        image_files_v2 = list((output_path / "recognition" / "images").glob("*.png"))
        # Should have only 1 image (old ones deleted)
        assert len(image_files_v2) == 1

    def test_recognition_accumulates_across_pages(self, tmp_path):
        """Recognition export preserves labels from other pages."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        # Page 0
        page0 = _make_page_with_words(["hello"])
        page0.generate_doctr_recognition_training_set(
            output_path=output_path, prefix="test"
        )

        # Page 1
        page1 = _make_page_with_words(["world"])
        page1.page_index = 1
        page1.generate_doctr_recognition_training_set(
            output_path=output_path, prefix="test"
        )

        with open(output_path / "recognition" / "labels.json") as f:
            labels = json.load(f)

        # Should have 2 total entries
        assert len(labels) == 2


class TestConvertToTrainingSet:
    """Test the unified convert_to_training_set method."""

    def test_convert_creates_both_datasets(self, tmp_path):
        """convert_to_training_set creates both detection and recognition sets."""
        output_path = tmp_path / "training_set"
        output_path.mkdir(parents=True, exist_ok=True)

        page = _make_page_with_words(["hello", "world"])
        page.convert_to_training_set(output_path=output_path, prefix="test")

        # Verify both subdirectories exist
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

        # Filter to only include words starting with 'h'
        def word_filter(w: Word) -> bool:
            return w.text.startswith("h")

        page.convert_to_training_set(
            output_path=output_path, prefix="test", word_filter=word_filter
        )

        # Check detection labels
        with open(output_path / "detection" / "labels.json") as f:
            detection_labels = json.load(f)
        assert len(detection_labels["test_0.png"]["polygons"]) == 1

        # Check recognition labels
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

        # Both should exist even with empty page
        assert (output_path / "detection" / "labels.json").exists()
        assert (output_path / "recognition" / "labels.json").exists()


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
