"""Tests for cv2_processing.rescale module."""

import inspect

import numpy as np
import pytest

pytest.importorskip("cv2")

from pd_book_tools.image_processing.cv2_processing.rescale import (
    rescale_image,
)


class TestRescaleImage:
    def test_portrait_image(self):
        img = np.zeros((400, 200), dtype=np.uint8)
        out = rescale_image(img, target_short_side=100)
        # Width is the short side, so it should equal target_short_side
        assert out.shape[1] == 100
        # The long side should scale by short_side / orig_short = 100/200 = 0.5
        assert out.shape[0] == 200

    def test_landscape_image(self):
        img = np.zeros((200, 400), dtype=np.uint8)
        out = rescale_image(img, target_short_side=100)
        # Height is the short side, so it should equal target_short_side
        assert out.shape[0] == 100
        assert out.shape[1] == 200

    def test_color_image_preserves_channels(self):
        img = np.zeros((300, 200, 3), dtype=np.uint8)
        out = rescale_image(img, target_short_side=100)
        assert out.ndim == 3
        assert out.shape[2] == 3

    def test_signature_has_no_aspect_ratio_param(self):
        # The deprecated `aspect_ratio` parameter was removed entirely.
        # Aspect-shape control is applied downstream via
        # `map_content_onto_scaled_canvas` (in pd-prep-for-pgdp), not at
        # rescale time. Any future re-introduction must use a new name
        # (e.g. `long_side_clamp`) — see ROADMAP "Done" entry.
        params = inspect.signature(rescale_image).parameters
        assert "aspect_ratio" not in params

    def test_aspect_ratio_kwarg_now_raises_typeerror(self):
        # Defensive: passing the removed kwarg should fail cleanly with
        # TypeError rather than silently no-op as it did pre-R-24.
        img = np.zeros((400, 200), dtype=np.uint8)
        with pytest.raises(TypeError):
            rescale_image(img, aspect_ratio=1.65, target_short_side=100)  # type: ignore[call-arg]
