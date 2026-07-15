"""Tests for cv2_processing.encoding module."""

import numpy as np
import pytest

pytest.importorskip("cv2")

from pdomain_book_tools.image_processing.cv2_processing.encoding import (
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

    def test_preserves_bgr_channels_round_trip(self):
        """Regression for H-01: encoding a BGR image then decoding must
        round-trip the same BGR pixel values. Previously the function did
        an extra BGR->RGB swap before imencode, so PNG decode (which
        returns BGR) returned channel-swapped values."""
        import cv2

        # Use a clearly asymmetric pixel so a swap is unambiguous.
        # BGR = (50, 100, 200): blue=50, green=100, red=200.
        bgr = np.zeros((4, 4, 3), dtype=np.uint8)
        bgr[:, :] = [50, 100, 200]

        buf = encode_bgr_image_as_png(bgr)
        decoded = cv2.imdecode(np.asarray(buf), cv2.IMREAD_COLOR)
        assert decoded is not None
        # cv2.imdecode returns BGR; should match the input BGR exactly.
        assert decoded.shape == bgr.shape
        # Check the pixel value at (0,0): with the bug, channels are swapped
        # to (200, 100, 50).
        np.testing.assert_array_equal(
            decoded[0, 0], np.array([50, 100, 200], dtype=np.uint8)
        )
        np.testing.assert_array_equal(decoded, bgr)
