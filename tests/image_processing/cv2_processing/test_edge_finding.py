"""Tests for cv2_processing.edge_finding module."""

import numpy as np

from pd_book_tools.image_processing.cv2_processing.edge_finding import find_edges


class TestFindEdges:
    def test_blank_image_returns_full_extents(self):
        img = np.zeros((100, 100), dtype=np.uint8)
        minX, maxX, minY, maxY = find_edges(img)
        # No content -> default to image extents
        assert minX == 0
        assert maxX == 100
        assert minY == 0
        assert maxY == 100

    def test_central_block(self):
        img = np.zeros((200, 200), dtype=np.uint8)
        # A solid block of full white pixels in the center
        img[50:150, 60:140] = 255
        minX, maxX, minY, maxY = find_edges(
            img,
            fuzzy_pct=0,
            pixel_count_columns=1,
            pixel_count_rows=1,
        )
        # Detected bounds should include the bright region (allow off-by-one)
        assert minX <= 60
        assert maxX >= 139
        assert minY <= 50
        assert maxY >= 149

    def test_fuzzy_overrides_apply(self):
        img = np.zeros((100, 100), dtype=np.uint8)
        img[40:60, 40:60] = 255
        minX, maxX, minY, maxY = find_edges(
            img,
            pixel_count_columns=1,
            pixel_count_rows=1,
            fuzzy_px_w_override=0,
            fuzzy_px_h_override=0,
        )
        # With zero fuzz, bounds should still tightly enclose content
        assert 0 <= minX <= 40
        assert 59 <= maxX <= 99
