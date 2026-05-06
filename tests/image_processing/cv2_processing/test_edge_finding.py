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

    def test_fuzzy_override_zero_is_honored(self):
        """Regression for M-03: `fuzzy_px_w_override=0` / `fuzzy_px_h_override=0`
        must be respected as "no fuzzy window", not silently treated as falsy
        and replaced with `int(w * fuzzy_pct)` / `int(h * fuzzy_pct)`.

        Pre-fix: `if fuzzy_px_w_override:` evaluates 0 as False, so the default
        `int(w * fuzzy_pct)` is applied, smearing content across the convolution
        kernel. Post-fix mirrors the cupy backend: `is not None` check, so
        explicit 0 disables fuzzing.

        The cupy backend already uses `is not None`.
        """
        # 100x100 black image with a single isolated 1-pixel-wide bright column
        # at x=50 and a single isolated 1-pixel-wide bright row at y=50, each
        # exactly meeting the pixel_count threshold.
        img = np.zeros((100, 100), dtype=np.uint8)
        img[10:13, 50] = 255  # 3 bright pixels in column x=50
        img[50, 10:13] = 255  # 3 bright pixels in row y=50

        # fuzzy_pct=0.10 so the buggy default fuzz_w/h = int(100 * 0.10) = 10,
        # producing a convolution kernel of size 21 that smears the bright
        # column across columns [40..60] (similarly for the row). With the
        # override honored as 0, the kernel is size 1 (identity) and only
        # the actual bright column/row indices are detected.
        minX, maxX, minY, maxY = find_edges(
            img,
            fuzzy_pct=0.10,
            pixel_count_columns=3,
            pixel_count_rows=3,
            fuzzy_px_w_override=0,
            fuzzy_px_h_override=0,
        )
        # Post-fix: only x=50, y=50 satisfy threshold (no fuzzing).
        assert minX == 50, (
            f"expected minX=50 with override=0 honored; got {minX} "
            "(pre-fix: 0 falsy, default fuzz_w=10 smears column to ~40)"
        )
        assert maxX == 50, (
            f"expected maxX=50 with override=0 honored; got {maxX} "
            "(pre-fix: 0 falsy, default fuzz_w=10 smears column to ~60)"
        )
        assert minY == 50, (
            f"expected minY=50 with override=0 honored; got {minY} "
            "(pre-fix: 0 falsy, default fuzz_h=10 smears row to ~40)"
        )
        assert maxY == 50, (
            f"expected maxY=50 with override=0 honored; got {maxY} "
            "(pre-fix: 0 falsy, default fuzz_h=10 smears row to ~60)"
        )
