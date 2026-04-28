"""Tests for cv2_processing.encoding module."""

import numpy as np
import pytest

pytest.importorskip("cv2")

from pd_book_tools.image_processing.cv2_processing.encoding import (  # noqa: E402
    encode_bgr_image_as_png,
)


class TestEncodeBgrImageAsPng:
    def test_returns_png_buffer(self):
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        img[:, :] = [50, 100, 150]
        buf = encode_bgr_image_as_png(img)
        # Should be an ndarray buffer that starts with PNG signature
        data = bytes(buf)
        assert data.startswith(b"\x89PNG\r\n\x1a\n")

    def test_grayscale_input(self):
        img = np.full((5, 5, 3), 255, dtype=np.uint8)
        buf = encode_bgr_image_as_png(img)
        data = bytes(buf)
        assert data.startswith(b"\x89PNG\r\n\x1a\n")
