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

    def test_threshold_uses_255_not_256(self):
        """Regression for M-02: threshold multiplier must be `* 255`, not `* 256`.

        A column with exactly `pixel_count_columns` fully-bright (255) pixels
        sums to `N * 255`. With the pre-fix `* 256` multiplier, the threshold
        was `N * 256` and such a column fell strictly below — the function
        missed content that exactly satisfied the documented contract. With
        the corrected `* 255` multiplier, sum equals threshold and the column
        is detected.
        """
        # 200x200 black image; place 2 fully-bright pixels in a single column.
        img = np.zeros((200, 200), dtype=np.uint8)
        img[10, 100] = 255
        img[11, 100] = 255
        # Add the same in a single row so row detection has content too,
        # otherwise minY/maxY default to 0/h and we can't distinguish.
        img[100, 10] = 255
        img[100, 11] = 255
        minX, maxX, minY, maxY = find_edges(
            img,
            fuzzy_pct=0,
            pixel_count_columns=2,
            pixel_count_rows=2,
            fuzzy_px_w_override=0,
            fuzzy_px_h_override=0,
        )
        # Column 100 has sum = 2 * 255 = 510. Pre-fix threshold = 2 * 256 = 512.
        # 510 < 512 -> column not detected -> x_indices empty -> defaults
        # minX=0, maxX=w(=200). Post-fix threshold = 510 -> column detected.
        assert minX == 100, f"expected minX=100 (column detected), got {minX}"
        assert maxX == 100, f"expected maxX=100 (column detected), got {maxX}"
        assert minY == 100, f"expected minY=100 (row detected), got {minY}"
        assert maxY == 100, f"expected maxY=100 (row detected), got {maxY}"

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
