"""Tests for ocr.image_utilities module."""

import base64
from unittest.mock import patch

import numpy as np
import pytest

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pd_book_tools.ocr.image_utilities import (
    get_cropped_block_image,
    get_cropped_encoded_image,
    get_cropped_encoded_image_scaled_bbox,
    get_cropped_word_image,
    get_encoded_image,
)
from pd_book_tools.ocr.word import Word


class TestGetEncodedImage:
    """Test the get_encoded_image function."""

    @pytest.fixture
    def sample_image(self):
        """Create a sample BGR image for testing."""
        # Create a 10x10 BGR image with distinct RGB values
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        img[:, :] = [50, 100, 150]  # BGR format (B=50, G=100, R=150)
        return img

    @pytest.fixture
    def mock_encoded_png(self):
        """Mock PNG encoded data."""
        return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\n"

    @patch("pd_book_tools.ocr.image_utilities.encode_bgr_image_as_png")
    def test_get_encoded_image_success(
        self, mock_encode, sample_image, mock_encoded_png
    ):
        """Test successful image encoding."""
        # Setup mock
        mock_encode.return_value = mock_encoded_png

        # Test
        encoded_img, b64_string, data_src = get_encoded_image(sample_image)

        # Assertions
        assert encoded_img == mock_encoded_png

        # Verify base64 encoding
        expected_b64 = base64.b64encode(mock_encoded_png).decode("utf-8")
        assert b64_string == expected_b64

        # Verify data source string format
        expected_data_src = f"data:image/png;base64,{expected_b64}"
        assert data_src == expected_data_src

        # Verify encode function was called correctly
        mock_encode.assert_called_once_with(sample_image)

    @patch("pd_book_tools.ocr.image_utilities.encode_bgr_image_as_png")
    def test_get_encoded_image_grayscale(self, mock_encode, mock_encoded_png):
        """Test encoding with grayscale image."""
        # Create grayscale image
        gray_img = np.random.randint(0, 255, (20, 20), dtype=np.uint8)
        mock_encode.return_value = mock_encoded_png

        # Test
        encoded_img, b64_string, data_src = get_encoded_image(gray_img)

        # Assertions
        assert encoded_img == mock_encoded_png
        assert isinstance(b64_string, str)
        assert data_src.startswith("data:image/png;base64,")
        mock_encode.assert_called_once_with(gray_img)

    @patch("pd_book_tools.ocr.image_utilities.encode_bgr_image_as_png")
    def test_get_encoded_image_empty_encoding(self, mock_encode, sample_image):
        """Test handling of empty encoded data."""
        # Setup mock to return empty bytes
        mock_encode.return_value = b""

        # Test
        encoded_img, b64_string, data_src = get_encoded_image(sample_image)

        # Assertions
        assert encoded_img == b""
        assert b64_string == ""
        assert data_src == "data:image/png;base64,"

    def test_base64_encoding_correctness(self):
        """Test that base64 encoding is correct."""
        # Use actual encoding function to ensure correctness
        test_bytes = b"test_data_12345"
        expected_b64 = base64.b64encode(test_bytes).decode("utf-8")

        with patch(
            "pd_book_tools.ocr.image_utilities.encode_bgr_image_as_png"
        ) as mock_encode:
            mock_encode.return_value = test_bytes
            sample_img = np.zeros((5, 5, 3), dtype=np.uint8)

            _, b64_string, data_src = get_encoded_image(sample_img)

            assert b64_string == expected_b64
            assert data_src == f"data:image/png;base64,{expected_b64}"


class TestGetCroppedEncodedImageScaledBbox:
    """Test the get_cropped_encoded_image_scaled_bbox function."""

    @pytest.fixture
    def sample_image(self):
        """Create a sample image for cropping tests."""
        # Create a 20x20 image with gradient values for easy verification
        img = np.zeros((20, 20, 3), dtype=np.uint8)
        for i in range(20):
            for j in range(20):
                img[i, j] = [i * 10, j * 10, (i + j) * 5]
        return img

    @pytest.fixture
    def scaled_bbox(self):
        """Create a scaled (pixel) bounding box."""
        return BoundingBox.from_ltrb(5, 5, 15, 15, is_normalized=False)

    @patch("pd_book_tools.ocr.image_utilities.get_encoded_image")
    def test_cropping_with_scaled_bbox(
        self, mock_get_encoded, sample_image, scaled_bbox
    ):
        """Test cropping with scaled (pixel) bounding box."""
        # Setup mock
        mock_encoded = (b"mock_png", "mock_b64", "mock_data_src")
        mock_get_encoded.return_value = mock_encoded

        # Test
        cropped_img, encoded_img, b64_string, data_src = (
            get_cropped_encoded_image_scaled_bbox(sample_image, scaled_bbox)
        )

        # Verify cropping dimensions
        assert cropped_img.shape == (10, 10, 3)  # 15-5 = 10 for both dimensions

        # Verify that the cropped region is correct
        # Should be sample_image[5:15, 5:15]
        expected_crop = sample_image[5:15, 5:15]
        np.testing.assert_array_equal(cropped_img, expected_crop)

        # Verify encoding was called with cropped image
        mock_get_encoded.assert_called_once()
        call_args = mock_get_encoded.call_args[0]
        np.testing.assert_array_equal(call_args[0], expected_crop)

        # Verify return values
        assert encoded_img == b"mock_png"
        assert b64_string == "mock_b64"
        assert data_src == "mock_data_src"

    @patch("pd_book_tools.ocr.image_utilities.get_encoded_image")
    def test_cropping_edge_bbox(self, mock_get_encoded, sample_image):
        """Test cropping with bounding box at image edges."""
        # Bbox that covers the entire image
        edge_bbox = BoundingBox.from_ltrb(0, 0, 20, 20, is_normalized=False)

        mock_encoded = (b"edge_png", "edge_b64", "edge_data_src")
        mock_get_encoded.return_value = mock_encoded

        # Test
        cropped_img, _, _, _ = get_cropped_encoded_image_scaled_bbox(
            sample_image, edge_bbox
        )

        # Should return the entire image
        np.testing.assert_array_equal(cropped_img, sample_image)

    @patch("pd_book_tools.ocr.image_utilities.get_encoded_image")
    def test_cropping_single_pixel_bbox(self, mock_get_encoded):
        """Test cropping with single pixel bounding box."""
        img = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)
        single_pixel_bbox = BoundingBox.from_ltrb(5, 5, 6, 6, is_normalized=False)

        mock_encoded = (b"pixel_png", "pixel_b64", "pixel_data_src")
        mock_get_encoded.return_value = mock_encoded

        # Test
        cropped_img, _, _, _ = get_cropped_encoded_image_scaled_bbox(
            img, single_pixel_bbox
        )

        # Should be 1x1 image
        assert cropped_img.shape == (1, 1, 3)
        np.testing.assert_array_equal(cropped_img, img[5:6, 5:6])


class TestGetCroppedEncodedImage:
    """Test the get_cropped_encoded_image function."""

    @pytest.fixture
    def sample_image(self):
        """Create a sample image for testing."""
        return np.random.randint(0, 255, (100, 200, 3), dtype=np.uint8)

    @pytest.fixture
    def normalized_bbox(self):
        """Create a normalized bounding box."""
        return BoundingBox.from_ltrb(0.1, 0.2, 0.9, 0.8, is_normalized=True)

    @pytest.fixture
    def pixel_bbox(self):
        """Create a pixel bounding box."""
        return BoundingBox.from_ltrb(20, 40, 180, 160, is_normalized=False)

    def test_pixel_coordinates_with_scaled_bbox_function(self):
        """Test that pixel coordinates work correctly with get_cropped_encoded_image_scaled_bbox."""
        img = np.random.randint(0, 255, (100, 200, 3), dtype=np.uint8)
        pixel_bbox = BoundingBox.from_ltrb(20, 40, 180, 160, is_normalized=False)

        with patch(
            "pd_book_tools.ocr.image_utilities.encode_bgr_image_as_png"
        ) as mock_encode:
            mock_encode.return_value = b"pixel_png_data"

            # This function is designed for pixel coordinates
            cropped_img, encoded_img, b64_string, data_src = (
                get_cropped_encoded_image_scaled_bbox(img, pixel_bbox)
            )

            # Verify dimensions and cropping
            assert cropped_img.shape == (
                60,
                160,
                3,
            )  # (100-40, 180-20, 3) - constrained by image size
            expected_crop = img[
                40:100, 20:180
            ]  # [y1:y2, x1:x2] - y goes from 40 to image height (100)
            np.testing.assert_array_equal(cropped_img, expected_crop)

            # Verify encoding
            assert encoded_img == b"pixel_png_data"
            assert isinstance(b64_string, str)
            assert data_src.startswith("data:image/png;base64,")

    @patch("pd_book_tools.ocr.image_utilities.get_encoded_image")
    def test_cropping_with_normalized_bbox(
        self, mock_get_encoded, sample_image, normalized_bbox
    ):
        """Test cropping with normalized bounding box."""
        h, w = sample_image.shape[:2]  # h=100, w=200

        mock_encoded = (b"norm_png", "norm_b64", "norm_data_src")
        mock_get_encoded.return_value = mock_encoded

        # Test
        cropped_img, encoded_img, b64_string, data_src = get_cropped_encoded_image(
            sample_image, normalized_bbox
        )

        # Verify the bbox was scaled correctly
        # Expected scaled coordinates: x1=20 (0.1*200), y1=20 (0.2*100),
        # x2=180 (0.9*200), y2=80 (0.8*100)
        expected_crop = sample_image[20:80, 20:180]  # Note: [y1:y2, x1:x2] for numpy

        assert cropped_img.shape == expected_crop.shape
        np.testing.assert_array_equal(cropped_img, expected_crop)

        # Verify encoding was called
        mock_get_encoded.assert_called_once()
        call_args = mock_get_encoded.call_args[0]
        np.testing.assert_array_equal(call_args[0], expected_crop)

        # Verify return values
        assert encoded_img == b"norm_png"
        assert b64_string == "norm_b64"
        assert data_src == "norm_data_src"

    def test_cropping_with_pixel_bbox_error(self, sample_image, pixel_bbox):
        """Test that pixel bounding box raises error in get_cropped_encoded_image."""
        # get_cropped_encoded_image expects normalized coordinates and calls scale()
        # Using pixel coordinates should raise ValueError
        with pytest.raises(
            ValueError, match="scale\\(\\) expected a normalized bounding box"
        ):
            get_cropped_encoded_image(sample_image, pixel_bbox)

    def test_coordinate_system_inference(self):
        """Test that coordinate systems are inferred correctly."""
        # Test with values that should be inferred as normalized
        norm_inferred_bbox = BoundingBox.from_ltrb(0.0, 0.0, 1.0, 1.0)
        assert norm_inferred_bbox.is_normalized is True

        # Test with values that should be inferred as pixel
        pixel_inferred_bbox = BoundingBox.from_ltrb(0, 0, 100, 50)
        assert pixel_inferred_bbox.is_normalized is False


class TestGetCroppedWordImage:
    """Test the get_cropped_word_image function."""

    @pytest.fixture
    def sample_word(self):
        """Create a sample Word with bounding box."""
        bbox = BoundingBox.from_ltrb(0.2, 0.3, 0.8, 0.7, is_normalized=True)
        return Word(text="test_word", bounding_box=bbox, ocr_confidence=0.95)

    @patch("pd_book_tools.ocr.image_utilities.get_cropped_encoded_image")
    def test_get_cropped_word_image(self, mock_get_cropped, sample_word):
        """Test cropping image for a Word."""
        img = np.random.randint(0, 255, (100, 200, 3), dtype=np.uint8)

        mock_result = (
            np.zeros((40, 120, 3), dtype=np.uint8),  # cropped image
            b"word_png",
            "word_b64",
            "word_data_src",
        )
        mock_get_cropped.return_value = mock_result

        # Test
        result = get_cropped_word_image(img, sample_word)

        # Verify get_cropped_encoded_image was called with correct parameters
        mock_get_cropped.assert_called_once_with(img, sample_word.bounding_box)

        # Verify result is passed through correctly
        assert result == mock_result

    def test_word_with_pixel_bbox_error(self):
        """Test with Word that has pixel coordinates - should error."""
        pixel_bbox = BoundingBox.from_ltrb(10, 20, 50, 60, is_normalized=False)
        word = Word(text="pixel_word", bounding_box=pixel_bbox, ocr_confidence=0.8)

        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # get_cropped_word_image uses get_cropped_encoded_image which expects normalized coords
        with pytest.raises(
            ValueError, match="scale\\(\\) expected a normalized bounding box"
        ):
            get_cropped_word_image(img, word)


class TestGetCroppedBlockImage:
    """Test the get_cropped_block_image function."""

    @pytest.fixture
    def sample_block_with_bbox(self):
        """Create a sample Block with bounding box."""
        bbox = BoundingBox.from_ltrb(0.1, 0.1, 0.9, 0.5, is_normalized=True)
        words = [
            Word(
                text="word1",
                bounding_box=BoundingBox.from_ltrb(0.1, 0.1, 0.3, 0.3),
                ocr_confidence=0.9,
            ),
            Word(
                text="word2",
                bounding_box=BoundingBox.from_ltrb(0.4, 0.1, 0.6, 0.3),
                ocr_confidence=0.8,
            ),
        ]
        return Block(
            items=words,
            child_type=BlockChildType.WORDS,
            block_category=BlockCategory.LINE,
            bounding_box=bbox,
        )

    @pytest.fixture
    def block_without_bbox(self):
        """Create a Block without items (so no computed bounding box)."""
        # Create empty block - no items means no computed bounding box
        return Block(
            items=[],
            child_type=BlockChildType.WORDS,
            block_category=BlockCategory.LINE,
            # No bounding_box provided, and no items to compute one from
        )

    @patch("pd_book_tools.ocr.image_utilities.get_cropped_encoded_image")
    def test_get_cropped_block_image_success(
        self, mock_get_cropped, sample_block_with_bbox
    ):
        """Test successful cropping of block image."""
        img = np.random.randint(0, 255, (200, 300, 3), dtype=np.uint8)

        mock_result = (
            np.zeros((80, 240, 3), dtype=np.uint8),  # cropped image
            b"block_png",
            "block_b64",
            "block_data_src",
        )
        mock_get_cropped.return_value = mock_result

        # Test
        result = get_cropped_block_image(img, sample_block_with_bbox)

        # Verify get_cropped_encoded_image was called with correct parameters
        mock_get_cropped.assert_called_once_with(
            img, sample_block_with_bbox.bounding_box
        )

        # Verify result is passed through correctly
        assert result == mock_result

    def test_get_cropped_block_image_no_bbox_error(self, block_without_bbox):
        """Test error when block has no bounding box."""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # Test
        with pytest.raises(ValueError, match="Line bounding box is not defined"):
            get_cropped_block_image(img, block_without_bbox)

    def test_block_with_pixel_bbox_error(self):
        """Test with Block that has pixel coordinates - should error."""
        pixel_bbox = BoundingBox.from_ltrb(20, 30, 100, 80, is_normalized=False)
        words = [
            Word(
                text="test",
                bounding_box=BoundingBox.from_ltrb(25, 35, 50, 45, is_normalized=False),
                ocr_confidence=0.9,
            )
        ]
        block = Block(
            items=words,
            child_type=BlockChildType.WORDS,
            block_category=BlockCategory.PARAGRAPH,
            bounding_box=pixel_bbox,
        )

        img = np.random.randint(0, 255, (150, 150, 3), dtype=np.uint8)

        # get_cropped_block_image uses get_cropped_encoded_image which expects normalized coords
        with pytest.raises(
            ValueError, match="scale\\(\\) expected a normalized bounding box"
        ):
            get_cropped_block_image(img, block)

    def test_block_with_none_bounding_box(self):
        """Test Block where bounding_box is forced to None after construction."""
        words = [
            Word(
                text="test",
                bounding_box=BoundingBox.from_ltrb(0.1, 0.1, 0.3, 0.3),
                ocr_confidence=0.9,
            )
        ]
        block = Block(
            items=words,
            child_type=BlockChildType.WORDS,
            block_category=BlockCategory.LINE,
        )
        # Force the bounding box to None after construction
        block.bounding_box = None

        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        with pytest.raises(ValueError, match="Line bounding box is not defined"):
            get_cropped_block_image(img, block)


class TestImageUtilitiesIntegration:
    """Integration tests for image utilities."""

    def test_full_pipeline_normalized_coordinates(self):
        """Test the full pipeline with normalized coordinates."""
        # Create test image
        img = np.random.randint(0, 255, (100, 200, 3), dtype=np.uint8)

        # Create Word with normalized bbox
        word = Word(
            text="integration_test",
            bounding_box=BoundingBox.from_ltrb(
                0.25, 0.25, 0.75, 0.75, is_normalized=True
            ),
            ocr_confidence=0.95,
        )

        # This should work without mocking to test the actual integration
        with patch(
            "pd_book_tools.ocr.image_utilities.encode_bgr_image_as_png"
        ) as mock_encode:
            mock_encode.return_value = b"test_png_data"

            cropped_img, encoded_img, b64_string, data_src = get_cropped_word_image(
                img, word
            )

            # Verify dimensions - should be 50x100 (0.5*100, 0.5*200)
            assert cropped_img.shape == (50, 100, 3)

            # Verify cropped region
            expected_crop = img[25:75, 50:150]  # [y1:y2, x1:x2] in pixel coords
            np.testing.assert_array_equal(cropped_img, expected_crop)

            # Verify encoding
            assert encoded_img == b"test_png_data"
            assert isinstance(b64_string, str)
            assert data_src.startswith("data:image/png;base64,")

    def test_full_pipeline_pixel_coordinates_error(self):
        """Test that pixel coordinates cause appropriate error."""
        # Create test image
        img = np.random.randint(0, 255, (100, 200, 3), dtype=np.uint8)

        # Create Block with pixel bbox - this should cause error in get_cropped_encoded_image
        bbox = BoundingBox.from_ltrb(10, 20, 60, 80, is_normalized=False)
        words = [
            Word(
                text="test",
                bounding_box=BoundingBox.from_ltrb(15, 25, 35, 45, is_normalized=False),
                ocr_confidence=0.9,
            )
        ]
        block = Block(
            items=words,
            child_type=BlockChildType.WORDS,
            block_category=BlockCategory.LINE,
            bounding_box=bbox,
        )

        # get_cropped_block_image calls get_cropped_encoded_image which expects normalized coordinates
        with pytest.raises(
            ValueError, match="scale\\(\\) expected a normalized bounding box"
        ):
            get_cropped_block_image(img, block)

    def test_error_handling_empty_image(self):
        """Test handling of edge case with tiny image and normalized coordinates."""
        # Test with minimum valid image and normalized coordinates
        tiny_img = np.zeros((1, 1, 3), dtype=np.uint8)
        word = Word(
            text="tiny",
            bounding_box=BoundingBox.from_ltrb(0.0, 0.0, 1.0, 1.0, is_normalized=True),
            ocr_confidence=0.5,
        )

        with patch(
            "pd_book_tools.ocr.image_utilities.encode_bgr_image_as_png"
        ) as mock_encode:
            mock_encode.return_value = b"tiny_png"

            cropped_img, _, _, _ = get_cropped_word_image(tiny_img, word)

            # Should handle this gracefully
            assert cropped_img.shape == (1, 1, 3)
            np.testing.assert_array_equal(cropped_img, tiny_img)

    def test_coordinate_system_consistency(self):
        """Test that normalized coordinates work and pixel coordinates error appropriately."""
        img = np.random.randint(0, 255, (50, 100, 3), dtype=np.uint8)

        # Test normalized coordinates
        norm_bbox = BoundingBox.from_ltrb(0.2, 0.4, 0.8, 0.8, is_normalized=True)

        with patch(
            "pd_book_tools.ocr.image_utilities.encode_bgr_image_as_png"
        ) as mock_encode:
            mock_encode.return_value = b"consistent_png"

            # Normalized coordinates should work fine with get_cropped_encoded_image
            norm_crop, _, _, _ = get_cropped_encoded_image(img, norm_bbox)

            # Should produce reasonable cropped region
            # 0.2*100=20, 0.4*50=20, 0.8*100=80, 0.8*50=40
            # So crop should be img[20:40, 20:80] -> shape (20, 60, 3)
            assert norm_crop.shape == (20, 60, 3)

            # Test pixel coordinates should raise error
            pixel_bbox = BoundingBox.from_ltrb(20, 20, 80, 40, is_normalized=False)
            with pytest.raises(
                ValueError, match="scale\\(\\) expected a normalized bounding box"
            ):
                get_cropped_encoded_image(img, pixel_bbox)
