"""Tests for cv2_processing.invert module."""

import numpy as np

from pd_book_tools.image_processing.cv2_processing.invert import invert_image


class TestInvertImage:
    def test_uint8_inversion(self):
        img = np.array([[0, 1, 127, 254, 255]], dtype=np.uint8)
        out = invert_image(img)
        np.testing.assert_array_equal(
            out, np.array([[255, 254, 128, 1, 0]], dtype=np.uint8)
        )

    def test_inverting_twice_returns_original(self):
        img = np.random.randint(0, 256, (8, 8), dtype=np.uint8)
        np.testing.assert_array_equal(invert_image(invert_image(img)), img)

    def test_color_image(self):
        img = np.zeros((4, 4, 3), dtype=np.uint8)
        out = invert_image(img)
        assert out.shape == img.shape
        assert (out == 255).all()
