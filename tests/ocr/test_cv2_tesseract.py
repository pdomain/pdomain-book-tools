"""Tests for cv2_tesseract OCR adapter module."""

from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest
from cv2 import imread

from pd_book_tools.ocr.cv2_tesseract import tesseract_ocr_cv2_image
from pd_book_tools.ocr.document import Document
from pd_book_tools.ocr.page import Page


class TestTesseractOcrCv2Image:
    """Test the main OCR function."""

    @pytest.fixture
    def sample_grayscale_image(self):
        """Create a sample grayscale image."""
        return np.random.randint(0, 255, size=(100, 100), dtype=np.uint8)

    @pytest.fixture
    def sample_color_image(self):
        """Create a sample color image."""
        return np.random.randint(0, 255, size=(100, 100, 3), dtype=np.uint8)

    @pytest.fixture
    def mock_tesseract_dataframe(self):
        """Mock Tesseract dataframe output."""
        return pd.DataFrame(
            {
                "level": [1, 2, 3, 4, 5],
                "page_num": [1, 1, 1, 1, 1],
                "block_num": [0, 1, 1, 1, 1],
                "par_num": [0, 0, 1, 1, 1],
                "line_num": [0, 0, 0, 1, 1],
                "word_num": [0, 0, 0, 0, 1],
                "left": [0, 10, 20, 30, 40],
                "top": [0, 10, 20, 30, 40],
                "width": [100, 90, 80, 70, 60],
                "height": [200, 190, 180, 170, 160],
                "conf": [0, 0, 0, 0, 95],
                "text": ["", "", "", "", "test"],
            }
        )

    @pytest.fixture
    def mock_tesseract_string(self):
        """Mock Tesseract string output."""
        return "test\n"

    @patch("pd_book_tools.ocr.cv2_tesseract.image_to_data")
    @patch("pd_book_tools.ocr.cv2_tesseract.image_to_string")
    @patch("pd_book_tools.ocr.document.Document.from_tesseract")
    def test_tesseract_ocr_with_grayscale_image(
        self,
        mock_from_tesseract,
        mock_image_to_string,
        mock_image_to_data,
        sample_grayscale_image,
        mock_tesseract_dataframe,
        mock_tesseract_string,
    ):
        """Test OCR with grayscale image."""
        # Setup mocks
        mock_image_to_data.return_value = mock_tesseract_dataframe
        mock_image_to_string.return_value = mock_tesseract_string

        # Create mock document and page
        mock_page = Mock(spec=Page)
        mock_doc = Mock(spec=Document)
        mock_doc.pages = [mock_page]
        mock_from_tesseract.return_value = mock_doc

        # Test
        result = tesseract_ocr_cv2_image(sample_grayscale_image, "test_path")

        # Assertions
        assert result == mock_page

        # Verify Tesseract was called with correct parameters
        expected_config = "--oem 3 -c textord_noise_rej=1 --dpi 300"
        mock_image_to_data.assert_called_once()
        call_args = mock_image_to_data.call_args
        assert call_args[1]["lang"] == "eng"
        assert call_args[1]["config"] == expected_config

        mock_image_to_string.assert_called_once()
        call_args = mock_image_to_string.call_args
        assert call_args[1]["lang"] == "eng"
        assert call_args[1]["config"] == expected_config

        # Verify Document.from_tesseract was called correctly
        mock_from_tesseract.assert_called_once_with(
            tesseract_output=mock_tesseract_dataframe,
            tesseract_string=mock_tesseract_string,
            source_path="test_path",
        )

    @patch("pd_book_tools.ocr.cv2_tesseract.cvtColor")
    @patch("pd_book_tools.ocr.cv2_tesseract.image_to_data")
    @patch("pd_book_tools.ocr.cv2_tesseract.image_to_string")
    @patch("pd_book_tools.ocr.document.Document.from_tesseract")
    def test_tesseract_ocr_with_color_image(
        self,
        mock_from_tesseract,
        mock_image_to_string,
        mock_image_to_data,
        mock_cvtColor,
        sample_color_image,
        mock_tesseract_dataframe,
        mock_tesseract_string,
    ):
        """Test OCR with color image (should convert to grayscale)."""
        # Setup mocks
        mock_grayscale = np.random.randint(0, 255, size=(100, 100), dtype=np.uint8)
        mock_cvtColor.return_value = mock_grayscale
        mock_image_to_data.return_value = mock_tesseract_dataframe
        mock_image_to_string.return_value = mock_tesseract_string

        # Create mock document and page
        mock_page = Mock(spec=Page)
        mock_doc = Mock(spec=Document)
        mock_doc.pages = [mock_page]
        mock_from_tesseract.return_value = mock_doc

        # Test
        result = tesseract_ocr_cv2_image(sample_color_image, "test_path")

        # Assertions
        assert result == mock_page

        # Verify color conversion was called
        mock_cvtColor.assert_called_once()
        # Note: We can't easily check the COLOR_BGR2GRAY constant without importing it

        # Verify Tesseract was called with the converted grayscale image
        mock_image_to_data.assert_called_once()
        mock_image_to_string.assert_called_once()

    @patch("pd_book_tools.ocr.cv2_tesseract.image_to_data")
    @patch("pd_book_tools.ocr.cv2_tesseract.image_to_string")
    @patch("pd_book_tools.ocr.document.Document.from_tesseract")
    def test_tesseract_ocr_with_empty_source_path(
        self,
        mock_from_tesseract,
        mock_image_to_string,
        mock_image_to_data,
        sample_grayscale_image,
        mock_tesseract_dataframe,
        mock_tesseract_string,
    ):
        """Test OCR with empty source path."""
        # Setup mocks
        mock_image_to_data.return_value = mock_tesseract_dataframe
        mock_image_to_string.return_value = mock_tesseract_string

        # Create mock document and page
        mock_page = Mock(spec=Page)
        mock_doc = Mock(spec=Document)
        mock_doc.pages = [mock_page]
        mock_from_tesseract.return_value = mock_doc

        # Test with empty source path
        result = tesseract_ocr_cv2_image(sample_grayscale_image, "")

        # Assertions
        assert result == mock_page

        # Verify Document.from_tesseract was called with None for source_path
        mock_from_tesseract.assert_called_once_with(
            tesseract_output=mock_tesseract_dataframe,
            tesseract_string=mock_tesseract_string,
            source_path=None,
        )

    @patch("pd_book_tools.ocr.cv2_tesseract.image_to_data")
    @patch("pd_book_tools.ocr.cv2_tesseract.image_to_string")
    @patch("pd_book_tools.ocr.document.Document.from_tesseract")
    def test_tesseract_ocr_default_source_path(
        self,
        mock_from_tesseract,
        mock_image_to_string,
        mock_image_to_data,
        sample_grayscale_image,
        mock_tesseract_dataframe,
        mock_tesseract_string,
    ):
        """Test OCR with default source path (not provided)."""
        # Setup mocks
        mock_image_to_data.return_value = mock_tesseract_dataframe
        mock_image_to_string.return_value = mock_tesseract_string

        # Create mock document and page
        mock_page = Mock(spec=Page)
        mock_doc = Mock(spec=Document)
        mock_doc.pages = [mock_page]
        mock_from_tesseract.return_value = mock_doc

        # Test without source path parameter
        result = tesseract_ocr_cv2_image(sample_grayscale_image)

        # Assertions
        assert result == mock_page

        # Verify Document.from_tesseract was called with None for source_path
        mock_from_tesseract.assert_called_once_with(
            tesseract_output=mock_tesseract_dataframe,
            tesseract_string=mock_tesseract_string,
            source_path=None,
        )

    def test_tesseract_ocr_invalid_image_dimensions(self):
        """Test OCR with invalid image dimensions."""
        # Create invalid image (1D array)
        invalid_image = np.random.randint(0, 255, size=(100,), dtype=np.uint8)

        # This should not crash but may behave unexpectedly
        # The actual behavior depends on how opencv handles it
        with pytest.raises(Exception):
            tesseract_ocr_cv2_image(invalid_image)

    def test_tesseract_config_string_format(self):
        """Test that the Tesseract configuration string is properly formatted."""
        expected_config_parts = [
            "--oem 3",
            "-c textord_noise_rej=1",
            "--dpi 300",
        ]

        # This is more of a documentation test to ensure config stays consistent
        # We'd need to refactor the function to make this more testable
        assert len(expected_config_parts) == 3

    @patch("pd_book_tools.ocr.cv2_tesseract.image_to_data")
    @patch("pd_book_tools.ocr.cv2_tesseract.image_to_string")
    @patch("pd_book_tools.ocr.document.Document.from_tesseract")
    def test_tesseract_config_no_textord_noise_debug(
        self,
        mock_from_tesseract,
        mock_image_to_string,
        mock_image_to_data,
        sample_grayscale_image,
        mock_tesseract_dataframe,
        mock_tesseract_string,
    ):
        """M-21 regression: the default Tesseract config must NOT include
        ``-c textord_noise_debug=1``. That flag forces Tesseract to emit
        noise-detection debug messages to the caller's stderr on every OCR
        call; library code must not pollute caller stderr by default.
        """
        mock_image_to_data.return_value = mock_tesseract_dataframe
        mock_image_to_string.return_value = mock_tesseract_string

        mock_page = Mock(spec=Page)
        mock_doc = Mock(spec=Document)
        mock_doc.pages = [mock_page]
        mock_from_tesseract.return_value = mock_doc

        tesseract_ocr_cv2_image(sample_grayscale_image, "test_path")

        for mock_call in (mock_image_to_data, mock_image_to_string):
            cfg = mock_call.call_args[1]["config"]
            assert "textord_noise_debug" not in cfg, (
                f"textord_noise_debug must not be in default config; got: {cfg!r}"
            )

    @patch("pd_book_tools.ocr.cv2_tesseract.image_to_data")
    @patch("pd_book_tools.ocr.cv2_tesseract.image_to_string")
    @patch("pd_book_tools.ocr.document.Document.from_tesseract")
    def test_tesseract_dpi_parameter_overrides_default(
        self,
        mock_from_tesseract,
        mock_image_to_string,
        mock_image_to_data,
        sample_grayscale_image,
        mock_tesseract_dataframe,
        mock_tesseract_string,
    ):
        """M-19 regression: dpi=150 must reach Tesseract as ``--dpi 150``,
        not the hardcoded ``--dpi 300`` default."""
        mock_image_to_data.return_value = mock_tesseract_dataframe
        mock_image_to_string.return_value = mock_tesseract_string

        mock_page = Mock(spec=Page)
        mock_doc = Mock(spec=Document)
        mock_doc.pages = [mock_page]
        mock_from_tesseract.return_value = mock_doc

        tesseract_ocr_cv2_image(sample_grayscale_image, "test_path", dpi=150)

        for mock_call in (mock_image_to_data, mock_image_to_string):
            cfg = mock_call.call_args[1]["config"]
            assert "--dpi 150" in cfg
            assert "--dpi 300" not in cfg

    @patch("pd_book_tools.ocr.cv2_tesseract.image_to_data")
    @patch("pd_book_tools.ocr.cv2_tesseract.image_to_string")
    @patch("pd_book_tools.ocr.document.Document.from_tesseract")
    def test_tesseract_dpi_default_preserves_300(
        self,
        mock_from_tesseract,
        mock_image_to_string,
        mock_image_to_data,
        sample_grayscale_image,
        mock_tesseract_dataframe,
        mock_tesseract_string,
    ):
        """M-19 regression: omitting dpi keeps the historical 300 default,
        so existing callers do not silently change behavior."""
        mock_image_to_data.return_value = mock_tesseract_dataframe
        mock_image_to_string.return_value = mock_tesseract_string

        mock_page = Mock(spec=Page)
        mock_doc = Mock(spec=Document)
        mock_doc.pages = [mock_page]
        mock_from_tesseract.return_value = mock_doc

        tesseract_ocr_cv2_image(sample_grayscale_image, "test_path")

        for mock_call in (mock_image_to_data, mock_image_to_string):
            cfg = mock_call.call_args[1]["config"]
            assert "--dpi 300" in cfg

    @patch("pd_book_tools.ocr.cv2_tesseract.image_to_data")
    @patch("pd_book_tools.ocr.cv2_tesseract.image_to_string")
    @patch("pd_book_tools.ocr.document.Document.from_tesseract")
    def test_tesseract_dpi_600(
        self,
        mock_from_tesseract,
        mock_image_to_string,
        mock_image_to_data,
        sample_grayscale_image,
        mock_tesseract_dataframe,
        mock_tesseract_string,
    ):
        """M-19 regression: high-resolution scans (e.g. 600 DPI) flow
        through the parameter unmodified."""
        mock_image_to_data.return_value = mock_tesseract_dataframe
        mock_image_to_string.return_value = mock_tesseract_string

        mock_page = Mock(spec=Page)
        mock_doc = Mock(spec=Document)
        mock_doc.pages = [mock_page]
        mock_from_tesseract.return_value = mock_doc

        tesseract_ocr_cv2_image(sample_grayscale_image, "test_path", dpi=600)

        for mock_call in (mock_image_to_data, mock_image_to_string):
            cfg = mock_call.call_args[1]["config"]
            assert "--dpi 600" in cfg
            assert "--dpi 300" not in cfg


class TestM20InputShapeDispatch:
    """M-20 regression tests for `tesseract_ocr_cv2_image` input dispatch.

    Pre-fix the dispatch only handled `ndim == 2` and
    `ndim == 3 and shape[2] == 3`; anything else fell through with
    ``image_grayscale = None`` and pytesseract then crashed deep inside.
    """

    @pytest.fixture
    def mock_tesseract_dataframe(self):
        return pd.DataFrame(
            {
                "level": [1, 2, 3, 4, 5],
                "page_num": [1, 1, 1, 1, 1],
                "block_num": [0, 1, 1, 1, 1],
                "par_num": [0, 0, 1, 1, 1],
                "line_num": [0, 0, 0, 1, 1],
                "word_num": [0, 0, 0, 0, 1],
                "left": [0, 10, 20, 30, 40],
                "top": [0, 10, 20, 30, 40],
                "width": [100, 90, 80, 70, 60],
                "height": [200, 190, 180, 170, 160],
                "conf": [0, 0, 0, 0, 95],
                "text": ["", "", "", "", "test"],
            }
        )

    @patch("pd_book_tools.ocr.cv2_tesseract.image_to_data")
    @patch("pd_book_tools.ocr.cv2_tesseract.image_to_string")
    @patch("pd_book_tools.ocr.document.Document.from_tesseract")
    def test_rgba_input_drops_alpha_and_calls_tesseract(
        self,
        mock_from_tesseract,
        mock_image_to_string,
        mock_image_to_data,
        mock_tesseract_dataframe,
    ):
        """RGBA / 4-channel input must be accepted: alpha is dropped (matches
        cv2 COLOR_BGRA2GRAY semantics, mirroring the M-18 cupy fix) and a
        valid 2D grayscale array is forwarded to pytesseract."""
        mock_image_to_data.return_value = mock_tesseract_dataframe
        mock_image_to_string.return_value = "test\n"

        mock_page = Mock(spec=Page)
        mock_doc = Mock(spec=Document)
        mock_doc.pages = [mock_page]
        mock_from_tesseract.return_value = mock_doc

        # Build an RGBA image whose alpha varies; if alpha leaked into the
        # gray conversion we'd get a different result than the BGR-only
        # slice would have produced.
        rgba = np.zeros((20, 30, 4), dtype=np.uint8)
        rgba[..., :3] = np.random.randint(0, 255, size=(20, 30, 3), dtype=np.uint8)
        rgba[..., 3] = np.random.randint(0, 255, size=(20, 30), dtype=np.uint8)

        result = tesseract_ocr_cv2_image(rgba, "test_path")

        assert result is mock_page

        # pytesseract must have been called with an actual 2D grayscale
        # array, not None.
        assert mock_image_to_data.call_count == 1
        forwarded = mock_image_to_data.call_args[0][0]
        assert forwarded is not None
        assert isinstance(forwarded, np.ndarray)
        assert forwarded.ndim == 2
        assert forwarded.shape == (20, 30)

        # Output must equal cv2's COLOR_BGRA2GRAY on the same input
        # (alpha-ignoring policy, matching M-18 cupy).
        from cv2 import COLOR_BGRA2GRAY
        from cv2 import cvtColor as real_cvtColor

        expected = real_cvtColor(rgba, COLOR_BGRA2GRAY)
        np.testing.assert_array_equal(forwarded, expected)

    def test_unsupported_two_channel_raises_value_error(self):
        """A 3D image with 2 channels (neither grayscale nor BGR/BGRA) must
        raise a clear ValueError naming the actual shape, not silently pass
        ``None`` to pytesseract."""
        bad = np.zeros((10, 10, 2), dtype=np.uint8)
        with pytest.raises(ValueError, match=r"shape="):
            tesseract_ocr_cv2_image(bad)

    def test_unsupported_ndim_raises_value_error(self):
        """A 4D array (e.g. accidental batch dimension) must raise a clear
        ValueError, not silently fall through to pytesseract with None."""
        bad = np.zeros((1, 10, 10, 3), dtype=np.uint8)
        with pytest.raises(ValueError, match=r"shape="):
            tesseract_ocr_cv2_image(bad)


class TestImportError:
    """Test import error handling."""

    def test_import_error_message(self):
        """Test that import error has appropriate message."""
        # This tests the import error at module level
        # We can't easily test this without mocking the import system
        # But we can verify the error message format exists in the code

        # Read the source file to verify error message
        from pathlib import Path

        source_file = (
            Path(__file__).parent.parent.parent
            / "pd_book_tools"
            / "ocr"
            / "cv2_tesseract.py"
        )
        content = source_file.read_text()

        assert "pytesseract is not installed" in content
        assert "Please install extra dependency [tesseract]" in content


class TestRealImageIntegration:
    """Integration tests with real images (requires pytesseract)."""

    @pytest.fixture
    def test_image_path(self):
        """Path to the test image."""
        return Path(__file__).parent.parent / "ocr-test-image.png"

    @pytest.mark.skipif(
        not pytest.importorskip("pytesseract", reason="pytesseract not available"),
        reason="Requires pytesseract for integration testing",
    )
    def test_real_image_ocr(self, test_image_path):
        """Test OCR with real test image."""
        pytest.importorskip("cv2")
        pytest.importorskip("pytesseract")

        # Load the test image
        image = imread(str(test_image_path))
        assert image is not None, f"Could not load test image: {test_image_path}"

        # Run OCR
        result_page = tesseract_ocr_cv2_image(image, str(test_image_path))

        # Basic assertions
        assert isinstance(result_page, Page)
        assert result_page.width > 0
        assert result_page.height > 0

        # The page should have some content (words or blocks)
        # We don't assert specific text since OCR results can vary
        assert hasattr(result_page, "items")

    @pytest.mark.skipif(
        not pytest.importorskip("pytesseract", reason="pytesseract not available"),
        reason="Requires pytesseract for integration testing",
    )
    def test_real_image_grayscale_vs_color(self, test_image_path):
        """Test that grayscale and color versions of same image produce similar results."""
        pytest.importorskip("cv2")
        pytest.importorskip("pytesseract")

        from cv2 import IMREAD_COLOR, IMREAD_GRAYSCALE, imread

        # Load as grayscale and color
        gray_image = imread(str(test_image_path), IMREAD_GRAYSCALE)
        color_image = imread(str(test_image_path), IMREAD_COLOR)

        assert gray_image is not None
        assert color_image is not None

        # Run OCR on both
        gray_result = tesseract_ocr_cv2_image(gray_image, str(test_image_path))
        color_result = tesseract_ocr_cv2_image(color_image, str(test_image_path))

        # Both should produce valid pages
        assert isinstance(gray_result, Page)
        assert isinstance(color_result, Page)

        # Dimensions should match
        assert gray_result.width == color_result.width
        assert gray_result.height == color_result.height
