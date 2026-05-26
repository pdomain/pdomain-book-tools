"""Tests for cv2_processing.io module."""

import pathlib

import numpy as np
import pytest

pytest.importorskip("cv2")

from pdomain_book_tools.image_processing.cv2_processing.io import (
    read_image,
    write_jpg,
    write_png,
)


class TestReadWritePng:
    def test_write_then_read_png(self, tmp_path):
        # Build a simple BGR image
        img = np.zeros((10, 12, 3), dtype=np.uint8)
        img[2:8, 2:10] = [40, 80, 120]
        out_path = pathlib.Path(tmp_path / "test.png")

        write_png(img, out_path)
        assert out_path.exists()
        assert out_path.stat().st_size > 0

        loaded = read_image(out_path)
        assert loaded is not None
        assert loaded.shape == img.shape
        np.testing.assert_array_equal(loaded, img)


class TestReadImageFailures:
    """Regression coverage for M-05.

    Pre-fix ``read_image`` returned ``cv2.imread``'s ``None`` sentinel
    silently, so downstream code (e.g. ``rescale_image`` doing
    ``img.shape[:2]``) crashed with a confusing ``AttributeError`` that
    didn't name the offending path. Post-fix it raises an explicit,
    path-naming exception.
    """

    def test_missing_file_raises_file_not_found(self, tmp_path):
        missing = pathlib.Path(tmp_path / "does_not_exist.png")
        with pytest.raises(FileNotFoundError, match=str(missing.resolve())):
            read_image(missing)

    def test_corrupt_file_raises_value_error(self, tmp_path):
        # An existing but undecodeable file: cv2.imread returns None, not raises.
        corrupt = pathlib.Path(tmp_path / "corrupt.png")
        corrupt.write_bytes(b"this is not a valid PNG payload")
        with pytest.raises(ValueError, match=str(corrupt.resolve())):
            read_image(corrupt)


class TestWriteJpg:
    def test_write_jpg_creates_file(self, tmp_path):
        img = np.zeros((20, 20, 3), dtype=np.uint8)
        img[:, :] = [120, 80, 40]
        out_path = pathlib.Path(tmp_path / "test.jpg")

        write_jpg(img, out_path, quality=80)
        assert out_path.exists()
        assert out_path.stat().st_size > 0

        loaded = read_image(out_path)
        assert loaded is not None
        assert loaded.shape == img.shape
