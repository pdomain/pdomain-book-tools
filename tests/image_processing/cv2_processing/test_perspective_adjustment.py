"""Tests for cv2_processing.perspective_adjustment module."""

import numpy as np
import pytest

pytest.importorskip("cv2")

from pd_book_tools.image_processing.cv2_processing.perspective_adjustment import (  # noqa: E402
    auto_deskew,
)


class TestAutoDeskew:
    def test_blank_image_returns_tuple_unchanged(self):
        img = np.zeros((100, 100), dtype=np.uint8)
        result = auto_deskew(img)
        # Blank image: still falls through and returns the original via the
        # "do nothing 2" branch (top/bottom columns are equal -> dist_b == dist_c).
        assert isinstance(result, tuple)
        new_img, top_of_img, bottom_of_img = result
        np.testing.assert_array_equal(new_img, img)
        assert isinstance(top_of_img, np.ndarray)
        assert isinstance(bottom_of_img, np.ndarray)

    def test_zero_pct_returns_three_tuple(self):
        """Regression test for M-04.

        The early-exit path (``h_percent == 0`` or ``w_ten_percent == 0``)
        previously returned a bare ``np.ndarray``, while every other path
        in ``auto_deskew`` and *all* paths in the cupy ``auto_deskew_gpu``
        return a 3-tuple ``(image, top_slice, bottom_slice)``. Callers
        therefore had to do ``isinstance(out, tuple)`` runtime dispatch
        to switch backends. Unify the early-exit return to a 3-tuple
        with empty-array placeholders, mirroring ``auto_deskew_gpu``'s
        ``cp.empty((0, 0), dtype=img_cp.dtype)`` contract.
        """
        img = np.zeros((100, 100), dtype=np.uint8)
        # pct=0 -> h_percent==0 -> early-exit branch
        out = auto_deskew(img, pct=0.0)
        assert isinstance(out, tuple)
        assert len(out) == 3
        new_img, top_of_img, bottom_of_img = out
        np.testing.assert_array_equal(new_img, img)
        # Mirror cupy: empty placeholders with the input dtype.
        assert isinstance(top_of_img, np.ndarray)
        assert isinstance(bottom_of_img, np.ndarray)
        assert top_of_img.shape == (0, 0)
        assert bottom_of_img.shape == (0, 0)
        assert top_of_img.dtype == img.dtype
        assert bottom_of_img.dtype == img.dtype

    def test_straight_block_no_skew(self):
        img = np.zeros((200, 200), dtype=np.uint8)
        img[40:160, 40:160] = 255
        result = auto_deskew(img)
        # Always returns a 3-tuple post-M-04.
        assert isinstance(result, tuple)
        new_img, top_of_img, bottom_of_img = result
        assert isinstance(new_img, np.ndarray)
        assert isinstance(top_of_img, np.ndarray)
        assert isinstance(bottom_of_img, np.ndarray)

    def test_skewed_block_clockwise(self):
        # Image where bottom-left starts further right than top-left
        # (positive slope) -> auto_deskew should rotate clockwise
        img = np.zeros((200, 200), dtype=np.uint8)
        for row, start_col in zip(range(40, 160), range(40, 160)):
            img[row, start_col : start_col + 100] = 255
        result = auto_deskew(img)
        assert isinstance(result, tuple)
        new_img = result[0]
        assert isinstance(new_img, np.ndarray)

    def test_skewed_block_counter_clockwise(self):
        # Image where bottom-left starts further left than top-left
        # (negative slope) -> auto_deskew should rotate counter-clockwise
        img = np.zeros((200, 200), dtype=np.uint8)
        for row, start_col in zip(range(40, 160), range(160, 40, -1)):
            img[row, start_col : start_col + 30] = 255
        result = auto_deskew(img)
        assert isinstance(result, tuple)
        new_img = result[0]
        assert isinstance(new_img, np.ndarray)

    def test_noise_above_text_block_does_not_corrupt_skew(self):
        """Regression test for M-01.

        The top-strip column-sum in auto_deskew must start at ``minY`` (the
        detected content top edge), not at row 0. Otherwise stray noise
        pixels above the text block bias ``top_left_column`` toward the
        noise's column, making auto_deskew detect a phantom skew on a
        perfectly straight (non-skewed) block.

        Construction:
            * 200x200 zero image
            * Un-skewed solid text block at rows [80, 160), cols [60, 160).
              Vertical left edge at column 60 -> truth: zero skew.
            * A single near-bright noise pixel high above the block at
              (row 10, col 20) with value 254. Sub-threshold for
              ``find_edges`` (single pixel sums to 254 < pixel_count_rows*255
              with the M-02 fix), so ``minY`` still resolves to the block's
              top edge ~80, and the bug under test is purely in the
              top-strip column scan that follows. Note: post-M-02 the
              find_edges threshold is exactly N*255, so a value-255 noise
              pixel would cross the threshold and shift ``minY`` to row 10;
              we use 254 to keep the noise sub-threshold while still being
              visible to the column-sum band scan that ``Y1=0`` would
              include.

        Pre-fix (Y1=0): the band img[0:minY+h_percent, :] includes the
        noise at column 20 (any non-zero pixel in the band makes
        ``columns[20] > 0``), so ``top_left_column`` becomes 20 while
        ``bottom_left_column`` is 60 -> auto_deskew rotates by ~27°.

        Post-fix (Y1=minY): noise is excluded from the band, so
        ``top_left_column`` correctly equals 60, matches
        ``bottom_left_column``, and auto_deskew returns the original
        image unchanged via the "do nothing" branch.
        """
        img = np.zeros((200, 200), dtype=np.uint8)
        # Un-skewed text block: vertical left edge at column 60.
        img[80:160, 60:160] = 255
        # Single high-up noise pixel, column 20. Value 254 keeps it
        # sub-threshold for find_edges (pixel_count_rows=1 -> threshold 255
        # post-M-02) so minY still snaps to the block top.
        img[10, 20] = 254

        result = auto_deskew(img)
        assert isinstance(result, tuple)
        new_img = result[0]

        # Post-fix: zero skew detected, image returned unchanged.
        # Pre-fix: image is rotated by ~27° and differs substantially.
        np.testing.assert_array_equal(new_img, img)
