"""Tests for cv2_processing.thumbnails module."""

import pathlib

import numpy as np
import pytest

pytest.importorskip("cv2")

from pdomain_book_tools.image_processing.cv2_processing.io import (
    read_image,
    write_jpg,
)
from pdomain_book_tools.image_processing.cv2_processing.thumbnails import (
    create_file_thumbnail,
)


class TestCreateFileThumbnail:
    def _make_source(self, tmp_path: pathlib.Path) -> pathlib.Path:
        img = np.zeros((600, 400, 3), dtype=np.uint8)
        img[:, :] = [120, 80, 40]
        src = pathlib.Path(tmp_path / "source.jpg")
        write_jpg(img, src, quality=95)
        return src

    def test_create_jpg_thumbnail(self, tmp_path):
        src = self._make_source(tmp_path)
        target = pathlib.Path(tmp_path / "thumb.jpg")
        create_file_thumbnail(src, target, jpeg_quality=50, max_dimension=100)
        assert target.exists()
        thumb = read_image(target)
        # Short side of thumbnail should match max_dimension
        h, w = thumb.shape[:2]
        assert min(h, w) == 100

    def test_png_target_raises_not_implemented(self, tmp_path):
        src = self._make_source(tmp_path)
        target = pathlib.Path(tmp_path / "thumb.png")
        with pytest.raises(NotImplementedError):
            create_file_thumbnail(src, target)

    def test_unknown_suffix_raises_value_error(self, tmp_path):
        src = self._make_source(tmp_path)
        target = pathlib.Path(tmp_path / "thumb.bmp")
        with pytest.raises(ValueError, match="suffix"):
            create_file_thumbnail(src, target)

    def test_missing_source_raises_file_not_found(self, tmp_path):
        # M-05: a missing source previously surfaced as
        # ``AttributeError: 'NoneType' object has no attribute 'shape'``
        # from ``rescale_image``. It must now name the offending path.
        src = pathlib.Path(tmp_path / "does_not_exist.jpg")
        target = pathlib.Path(tmp_path / "thumb.jpg")
        with pytest.raises(FileNotFoundError, match=str(src.resolve())):
            create_file_thumbnail(src, target)
