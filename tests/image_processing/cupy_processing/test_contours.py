"""Tests for cupy_processing.contours module."""

import numpy as np
import pytest


@pytest.mark.gpu
@pytest.mark.cupy
class TestRemoveSmallContoursGpu:
    def test_blank_image_returns_zeros(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.contours import (
            remove_small_contours_gpu,
        )

        img = cp.zeros((50, 50), dtype=cp.uint8)
        out = remove_small_contours_gpu(img)
        assert cp.all(out == 0)

    def test_output_shape_matches_input(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.contours import (
            remove_small_contours_gpu,
        )

        img = cp.zeros((100, 100), dtype=cp.uint8)
        img[40:60, 40:60] = 255
        out = remove_small_contours_gpu(img)
        assert out.shape == img.shape

    def test_tiny_isolated_pixel_is_removed(self, cupy_module):
        """A single white pixel on a large blank canvas should be removed."""
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.contours import (
            remove_small_contours_gpu,
        )

        img = cp.zeros((100, 100), dtype=cp.uint8)
        img[50, 50] = 255
        out = remove_small_contours_gpu(img)
        assert int(out[50, 50]) == 0

    def test_large_blob_is_preserved(self, cupy_module):
        """A blob larger than the size thresholds should not be removed."""
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.contours import (
            remove_small_contours_gpu,
        )

        img = cp.zeros((200, 200), dtype=cp.uint8)
        img[50:150, 50:150] = 255  # 100×100 blob — far above any threshold
        out = remove_small_contours_gpu(img)
        assert int(out[100, 100]) == 255

    def test_small_blob_near_large_blob_is_kept(self, cupy_module):
        """A small component whose search area overlaps a large blob should survive."""
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.contours import (
            remove_small_contours_gpu,
        )

        # 200×200 image: pixels_w=max(8,5)=8, pixels_h=max(6,5)=6
        img = cp.zeros((200, 200), dtype=cp.uint8)
        img[50:150, 50:150] = 255  # large blob (rows 50-149)
        # 5×5 contour one row below the blob (row 151).
        # Search area rows: [max(0,151-3):min(200,151+5+3)] = [148:159]
        # Rows 148-149 are inside the blob → search_sum >> threshold → kept.
        img[151:156, 98:103] = 255

        out = remove_small_contours_gpu(img)
        assert int(out[153, 100]) == 255

    def test_small_isolated_blob_is_removed(self, cupy_module):
        """A small component with no neighbours should be removed."""
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.contours import (
            remove_small_contours_gpu,
        )

        img = cp.zeros((200, 200), dtype=cp.uint8)
        img[100:105, 100:105] = 255  # 5×5 blob, totally isolated
        out = remove_small_contours_gpu(img)
        assert int(out[102, 102]) == 0

    def test_input_is_not_mutated(self, cupy_module):
        """remove_small_contours_gpu should return a copy, not modify in-place."""
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.contours import (
            remove_small_contours_gpu,
        )

        img = cp.zeros((60, 60), dtype=cp.uint8)
        img[30, 30] = 255
        original = img.copy()
        remove_small_contours_gpu(img)
        assert cp.array_equal(img, original)

    def test_np_wrapper_returns_numpy(self, cupy_module):
        from pd_book_tools.image_processing.cupy_processing.contours import (
            np_uint8_remove_small_contours,
        )

        img = np.zeros((60, 60), dtype=np.uint8)
        img[30, 30] = 255
        out = np_uint8_remove_small_contours(img)
        assert isinstance(out, np.ndarray)
        assert out.dtype == np.uint8
        assert out[30, 30] == 0


@pytest.mark.gpu
@pytest.mark.cupy
class TestContourSizeStatsGpu:
    def test_blank_image_returns_zero_count(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.contours import (
            contour_size_stats_gpu,
        )

        img = cp.zeros((100, 100), dtype=cp.uint8)
        stats = contour_size_stats_gpu(img)
        assert stats["count"] == 0

    def test_single_blob_stats(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.contours import (
            contour_size_stats_gpu,
        )

        img = cp.zeros((100, 100), dtype=cp.uint8)
        img[20:30, 30:45] = 255  # 10h × 15w blob
        stats = contour_size_stats_gpu(img)
        assert stats["count"] == 1
        assert stats["median_w"] == 15.0
        assert stats["median_h"] == 10.0

    def test_median_dominated_by_majority_size(self, cupy_module):
        """Median should reflect the common component size, not outliers."""
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.contours import (
            contour_size_stats_gpu,
        )

        img = cp.zeros((200, 200), dtype=cp.uint8)
        # 9 medium blobs (10×8) spread across the image
        positions = [
            (10, 10),
            (10, 40),
            (10, 70),
            (50, 10),
            (50, 40),
            (50, 70),
            (90, 10),
            (90, 40),
            (90, 70),
        ]
        for r, c in positions:
            img[r : r + 8, c : c + 10] = 255
        # 1 large outlier blob — should not pull median up
        img[150:180, 150:180] = 255

        stats = contour_size_stats_gpu(img)
        assert stats["median_w"] == pytest.approx(10.0, abs=1)
        assert stats["median_h"] == pytest.approx(8.0, abs=1)

    def test_returns_all_expected_keys(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.contours import (
            contour_size_stats_gpu,
        )

        img = cp.zeros((50, 50), dtype=cp.uint8)
        img[10:15, 10:15] = 255
        stats = contour_size_stats_gpu(img)
        for key in (
            "count",
            "median_w",
            "median_h",
            "mean_w",
            "mean_h",
            "p10_w",
            "p10_h",
        ):
            assert key in stats


@pytest.mark.gpu
@pytest.mark.cupy
class TestRemoveSmallContoursAdaptiveGpu:
    def _make_text_page(self, cp):
        """20 character-sized (8×6) blobs + 5 noise dots (1×1)."""
        img = cp.zeros((200, 200), dtype=cp.uint8)
        positions = [
            (10, 10),
            (10, 30),
            (10, 50),
            (10, 70),
            (10, 90),
            (30, 10),
            (30, 30),
            (30, 50),
            (30, 70),
            (30, 90),
            (50, 10),
            (50, 30),
            (50, 50),
            (50, 70),
            (50, 90),
            (70, 10),
            (70, 30),
            (70, 50),
            (70, 70),
            (70, 90),
        ]
        for r, c in positions:
            img[r : r + 6, c : c + 8] = 255
        # Isolated noise dots
        for r, c in [(150, 150), (155, 160), (160, 170), (165, 140), (170, 155)]:
            img[r, c] = 255
        return img

    def test_noise_dots_are_removed(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.contours import (
            remove_small_contours_adaptive_gpu,
        )

        img = self._make_text_page(cp)
        out = remove_small_contours_adaptive_gpu(img)
        # All isolated noise dots should be gone
        for r, c in [(150, 150), (155, 160), (160, 170), (165, 140), (170, 155)]:
            assert int(out[r, c]) == 0

    def test_character_blobs_are_preserved(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.contours import (
            remove_small_contours_adaptive_gpu,
        )

        img = self._make_text_page(cp)
        out = remove_small_contours_adaptive_gpu(img)
        # Centres of character blobs must survive
        for r, c in [(13, 14), (33, 34), (53, 54)]:
            assert int(out[r, c]) == 255

    def test_page_number_same_size_as_body_text_is_kept(self, cupy_module):
        """Components matching body-text character size must never be removed."""
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.contours import (
            remove_small_contours_adaptive_gpu,
        )

        img = cp.zeros((200, 200), dtype=cp.uint8)
        # Body text — 12 character blobs
        for r in range(20, 100, 20):
            for c in range(10, 100, 20):
                img[r : r + 6, c : c + 8] = 255
        # Page number in the corner — same character size, isolated
        img[180:186, 90:98] = 255

        out = remove_small_contours_adaptive_gpu(img)
        assert int(out[183, 94]) == 255

    def test_toc_leader_dots_are_preserved(self, cupy_module):
        """
        Leader dots in a table of contents (". . . . . 50") must not be removed.
        Each dot is isolated from its immediate neighbours but they form a row;
        the search area must be wide enough to span the inter-dot gap.
        """
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.contours import (
            remove_small_contours_adaptive_gpu,
        )

        img = cp.zeros((200, 200), dtype=cp.uint8)
        # Body text: 12 character blobs (8×6) — establishes the median
        for r in range(20, 80, 20):
            for c in range(10, 100, 20):
                img[r : r + 6, c : c + 8] = 255
        # TOC leader row: 6 dots (2×2) spaced 12px apart — isolated but in a row
        dot_cols = [10, 22, 34, 46, 58, 70]
        for c in dot_cols:
            img[110:112, c : c + 2] = 255

        out = remove_small_contours_adaptive_gpu(img)
        # Every leader dot should survive because neighbours are within search area
        for c in dot_cols:
            assert int(out[110, c]) == 255, (
                f"Leader dot at col {c} was incorrectly removed"
            )

    def test_np_wrapper_returns_numpy(self, cupy_module):
        from pd_book_tools.image_processing.cupy_processing.contours import (
            np_uint8_remove_small_contours_adaptive,
        )

        img = np.zeros((100, 100), dtype=np.uint8)
        img[50, 50] = 255
        out = np_uint8_remove_small_contours_adaptive(img)
        assert isinstance(out, np.ndarray)
        assert out.dtype == np.uint8
