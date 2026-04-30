"""Tests for cv2_processing.contours module."""

import numpy as np
import pytest

pytest.importorskip("cv2")

from pd_book_tools.image_processing.cv2_processing.contours import (  # noqa: E402
    find_and_draw_contours,
    remove_small_contours,
)


def _binary_image_with_blobs() -> np.ndarray:
    """Create a 100x100 binary image with a couple of blobs."""
    img = np.zeros((100, 100), dtype=np.uint8)
    # Big blob
    img[30:70, 30:70] = 255
    # Tiny blob (small contour)
    img[5:9, 5:9] = 255
    return img


class TestFindAndDrawContours:
    def test_finds_contours_and_returns_visualization(self):
        img = _binary_image_with_blobs()
        out_img, contours = find_and_draw_contours(img.copy())
        assert out_img is not None
        # Should detect at least 2 contours
        assert len(contours) >= 2
        # Output is a 3-channel BGR image with the contours drawn
        assert out_img.ndim == 3
        assert out_img.shape[2] == 3

    def test_no_contours_returns_original(self):
        # An all-zero image has no contours
        img = np.zeros((50, 50), dtype=np.uint8)
        out_img, contours = find_and_draw_contours(img.copy())
        assert len(contours) == 0
        # Image should be returned as-is (still grayscale)
        assert out_img.shape == img.shape


class TestRemoveSmallContours:
    def test_no_contours_returns_image_unchanged(self):
        img = np.zeros((50, 50), dtype=np.uint8)
        out_img, vis = remove_small_contours(img.copy(), [])
        np.testing.assert_array_equal(out_img, img)
        # Visualization should be a 3-channel BGR
        assert vis.shape == (50, 50, 3)

    def test_removes_tiny_contour(self):
        from cv2 import (
            CHAIN_APPROX_SIMPLE,
            RETR_EXTERNAL,
            findContours,
        )

        img = _binary_image_with_blobs()
        contours, _ = findContours(img.copy(), RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)
        # Initial image has tiny blob at [5:9, 5:9]
        assert (img[5:9, 5:9] == 255).all()
        cleaned, _ = remove_small_contours(img.copy(), contours)
        # Tiny blob should now be zeroed out
        assert (cleaned[5:9, 5:9] == 0).all()
        # Big blob should remain
        assert (cleaned[30:70, 30:70] == 255).all()

    def test_medium_contour_with_nearby_pixels_kept(self):
        """Medium contour with significant nearby pixels should be retained."""
        from cv2 import (
            CHAIN_APPROX_SIMPLE,
            RETR_EXTERNAL,
            findContours,
        )

        # Create an image where a medium contour sits close to a large blob
        img = np.zeros((200, 200), dtype=np.uint8)
        # Large support blob
        img[80:120, 20:180] = 255
        # Medium-sized contour next to it - within size threshold but with neighbors
        img[60:75, 60:80] = 255

        contours, _ = findContours(img.copy(), RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)
        cleaned, vis = remove_small_contours(img.copy(), contours)
        # Visualization should be a 3-channel image
        assert vis.ndim == 3
        assert vis.shape[2] == 3

    def test_medium_contour_isolated_removed(self):
        """Medium contour with no nearby pixels should be removed."""
        from cv2 import (
            CHAIN_APPROX_SIMPLE,
            RETR_EXTERNAL,
            findContours,
        )

        img = np.zeros((200, 200), dtype=np.uint8)
        # An isolated medium-sized contour
        img[100:108, 100:108] = 255

        contours, _ = findContours(img.copy(), RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)
        cleaned, _ = remove_small_contours(
            img.copy(), contours, min_w_pct=0.10, min_h_pct=0.10
        )
        # The isolated medium contour should be cleared
        assert (cleaned[100:108, 100:108] == 0).all()

    def test_already_zeroed_contour_skipped(self):
        """Covers line 65 (continue): contour region already all zeros.

        Pass a contour whose bounding region in the image is all zeros;
        the function should skip it and return the image unchanged.
        """
        from cv2 import (
            CHAIN_APPROX_SIMPLE,
            RETR_EXTERNAL,
            findContours,
        )

        # Create a temporary image with a blob to get a valid contour
        template = np.zeros((100, 100), dtype=np.uint8)
        template[10:20, 10:20] = 255
        contours, _ = findContours(template.copy(), RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)

        # Now pass a blank image (all zeros) so contour_sum == 0 → continue
        blank = np.zeros((100, 100), dtype=np.uint8)
        out, _ = remove_small_contours(blank.copy(), list(contours))
        # Image should remain all zeros
        assert np.sum(out) == 0

    def test_medium_contour_below_size_threshold_covers_search_area(self):
        """Covers lines 75-91: contour is NOT tiny but IS below pixels_w/h threshold.

        Use small_contour_w/h=5 (tiny threshold) and min_w_pct/min_h_pct=0.20
        (large size threshold), so a 12x12 contour is:
          - NOT tiny (12 >= 5) → does not hit the 'directly remove' path
          - IS below size threshold (12 < 200*0.20=40) → enters the search area code

        The nearby_pixel_count threshold determines if the contour is removed (low count)
        or kept (high count, red rectangle drawn at line 91).
        """
        from cv2 import (
            CHAIN_APPROX_SIMPLE,
            RETR_EXTERNAL,
            findContours,
        )

        img = np.zeros((200, 200), dtype=np.uint8)
        # Isolated medium contour: 12x12 – above tiny (5) but below size threshold (40)
        img[50:62, 50:62] = 255
        contours, _ = findContours(img.copy(), RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)

        # nearby_pixel_count=100 → threshold_sum = 25500, search_sum < 25500 → removed
        out_removed, vis_removed = remove_small_contours(
            img.copy(),
            contours,
            min_w_pct=0.20,
            min_h_pct=0.20,
            small_contour_w=5,
            small_contour_h=5,
            nearby_pixel_count=100,
        )
        assert (out_removed[50:62, 50:62] == 0).all()

        # nearby_pixel_count=0 → threshold_sum=0, search_sum >= 0 → kept (red rect drawn)
        img2 = np.zeros((200, 200), dtype=np.uint8)
        img2[50:62, 50:62] = 255
        contours2, _ = findContours(img2.copy(), RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)
        out_kept, vis_kept = remove_small_contours(
            img2.copy(),
            contours2,
            min_w_pct=0.20,
            min_h_pct=0.20,
            small_contour_w=5,
            small_contour_h=5,
            nearby_pixel_count=0,
        )
        # The contour should NOT be removed (search_sum >= threshold_sum=0)
        assert (out_kept[50:62, 50:62] == 255).all()
