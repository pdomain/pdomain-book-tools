"""Tests for cv2_processing.rescale module."""

import numpy as np
import pytest

pytest.importorskip("cv2")

from pd_book_tools.image_processing.cv2_processing.rescale import (  # noqa: E402
    rescale_image,
)


class TestRescaleImage:
    def test_portrait_image(self):
        img = np.zeros((400, 200), dtype=np.uint8)
        out = rescale_image(img, aspect_ratio=1.65, target_short_side=100)
        # Width is the short side, so it should equal target_short_side
        assert out.shape[1] == 100
        # The long side should scale by short_side / orig_short = 100/200 = 0.5
        assert out.shape[0] == 200

    def test_landscape_image(self):
        img = np.zeros((200, 400), dtype=np.uint8)
        out = rescale_image(img, aspect_ratio=1.65, target_short_side=100)
        # Height is the short side, so it should equal target_short_side
        assert out.shape[0] == 100
        assert out.shape[1] == 200

    def test_color_image_preserves_channels(self):
        img = np.zeros((300, 200, 3), dtype=np.uint8)
        out = rescale_image(img, target_short_side=100)
        assert out.ndim == 3
        assert out.shape[2] == 3
