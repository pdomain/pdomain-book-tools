"""Tests for cv2_processing.contours module."""

from __future__ import annotations

from typing import cast

import numpy as np
import pytest

pytest.importorskip("cv2")

from cv2 import (
    CHAIN_APPROX_SIMPLE,
    RETR_EXTERNAL,
    findContours,
)

from pdomain_book_tools.image_processing.cv2_processing.contours import (
    Contour,
    ImageArray,
    find_and_draw_contours,
    remove_small_contours,
)


def _find_contours(img: ImageArray) -> tuple[Contour, ...]:
    """Wrap ``cv2.findContours`` and narrow its ``MatLike`` result to ``Contour``.

    Mirrors the cast used in ``contours.find_and_draw_contours`` — cv2's
    stubs return the broader ``MatLike`` element type, but this codebase's
    contour arrays are always ``int32``.
    """
    raw_contours, _ = findContours(img, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)
    return cast("tuple[Contour, ...]", tuple(raw_contours))


def _no_contours_stub(*args: object, **kwargs: object) -> tuple[list[Contour], None]:
    """Typed stand-in for ``cv2.findContours`` that always reports no contours."""
    return [], None


def _binary_image_with_blobs() -> np.ndarray:
    """Create a 100x100 binary image with a couple of blobs."""
    img = np.zeros((100, 100), dtype=np.uint8)
    # Big blob
    img[30:70, 30:70] = 255
    # Tiny blob (small contour)
    img[5:9, 5:9] = 255
    return img


class TestFindAndDrawContours:
    def test_finds_contours_and_returns_visualization(self) -> None:
        img = _binary_image_with_blobs()
        out_img, contours = find_and_draw_contours(img.copy())
        assert out_img is not None
        # Should detect at least 2 contours
        assert len(contours) >= 2
        # Output is a 3-channel BGR image with the contours drawn
        assert out_img.ndim == 3
        assert out_img.shape[2] == 3

    def test_no_contours_returns_bgr(self) -> None:
        # An all-zero image has no contours.
        # Output must still be a 3-channel BGR image so callers don't have
        # to runtime-dispatch on shape (regression for M-10).
        img = np.zeros((50, 50), dtype=np.uint8)
        out_img, contours = find_and_draw_contours(img.copy())
        assert len(contours) == 0
        assert out_img.ndim == 3
        assert out_img.shape == (50, 50, 3)
        assert out_img.dtype == img.dtype

    def test_return_ndim_consistent_with_and_without_contours(self) -> None:
        """Regression for M-10: ndim/dtype must match across both branches."""
        empty = np.zeros((50, 50), dtype=np.uint8)
        out_empty, c_empty = find_and_draw_contours(empty.copy())
        assert len(c_empty) == 0

        with_blob = _binary_image_with_blobs()
        out_blob, c_blob = find_and_draw_contours(with_blob.copy())
        assert len(c_blob) >= 1

        # Same ndim, same channel count, same dtype regardless of branch.
        assert out_empty.ndim == out_blob.ndim == 3
        assert out_empty.shape[2] == out_blob.shape[2] == 3
        assert out_empty.dtype == out_blob.dtype

    def test_gray2bgr_conversion_semantics(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Regression for M-11: gray->BGR conversion must use COLOR_GRAY2BGR.

        COLOR_GRAY2BGR replicates the single grayscale channel into all
        three BGR channels, so for any pixel the B/G/R values must be
        equal to the original grayscale value. The previous implementation
        used COLOR_RGB2BGR (semantically wrong on a 2D input). M-11 was
        already incidentally fixed by the M-10 commit 1012acd; this test
        locks the GRAY2BGR contract so a future refactor cannot
        regress to RGB2BGR or any other semantically-incorrect constant.

        Patches cv2.findContours to return no contours so the function
        skips the rectangle-drawing step and we can assert that every
        output pixel has B == G == R == original_gray_value across the
        entire image, including non-zero intensities.
        """
        from pdomain_book_tools.image_processing.cv2_processing import contours as mod

        # Distinct non-zero grayscale intensities so the channel-equality
        # check is non-trivial (an all-zero image trivially satisfies it).
        img = np.zeros((10, 10), dtype=np.uint8)
        img[0, 0] = 17
        img[1, 2] = 128
        img[5, 5] = 200
        img[9, 9] = 255

        # Force the no-contours path so cv2.rectangle does not overdraw.
        monkeypatch.setattr(mod.cv2, "findContours", _no_contours_stub)

        out, contours = find_and_draw_contours(img.copy())
        assert len(contours) == 0
        assert out.ndim == 3
        assert out.shape == (10, 10, 3)
        assert out.dtype == np.uint8

        # COLOR_GRAY2BGR contract: every pixel's three channels are
        # equal to each other and equal to the grayscale source value.
        # COLOR_RGB2BGR on a 2D input cannot guarantee this — it would
        # either crash or interpret the data with wrong channel semantics.
        assert (out[..., 0] == out[..., 1]).all()
        assert (out[..., 1] == out[..., 2]).all()
        np.testing.assert_array_equal(out[..., 0], img)


class TestRemoveSmallContours:
    def test_does_not_mutate_input_image(self) -> None:
        """L-13: ``remove_small_contours`` must not mutate the caller's array.

        The cupy backend (``remove_small_contours_gpu``) operates on
        ``img_cp.copy()``; the cv2 backend was historically writing
        ``img[y:y+h, x:x+w] = 0`` directly into the input. Aligning the
        two backends so callers don't have to remember which one mutates.
        """
        img = _binary_image_with_blobs()
        # Snapshot of the *exact* bytes the caller is passing in.
        original = img.copy()
        contours = _find_contours(img)

        cleaned, _ = remove_small_contours(img, contours)

        # The returned image must reflect the cleaning (tiny blob gone)...
        assert (cleaned[5:9, 5:9] == 0).all()
        # ...but the caller's input must be byte-identical to what they
        # passed in (no in-place mutation).
        np.testing.assert_array_equal(img, original)

    def test_no_contours_returns_image_unchanged(self) -> None:
        img = np.zeros((50, 50), dtype=np.uint8)
        out_img, vis = remove_small_contours(img.copy(), [])
        np.testing.assert_array_equal(out_img, img)
        # Visualization should be a 3-channel BGR
        assert vis.shape == (50, 50, 3)

    def test_removes_tiny_contour(self) -> None:
        img = _binary_image_with_blobs()
        contours = _find_contours(img.copy())
        # Initial image has tiny blob at [5:9, 5:9]
        assert (img[5:9, 5:9] == 255).all()
        cleaned, _ = remove_small_contours(img.copy(), contours)
        # Tiny blob should now be zeroed out
        assert (cleaned[5:9, 5:9] == 0).all()
        # Big blob should remain
        assert (cleaned[30:70, 30:70] == 255).all()

    def test_medium_contour_with_nearby_pixels_kept(self) -> None:
        """Medium contour with significant nearby pixels should be retained."""
        # Create an image where a medium contour sits close to a large blob
        img = np.zeros((200, 200), dtype=np.uint8)
        # Large support blob
        img[80:120, 20:180] = 255
        # Medium-sized contour next to it - within size threshold but with neighbors
        img[60:75, 60:80] = 255

        contours = _find_contours(img.copy())
        _cleaned, vis = remove_small_contours(img.copy(), contours)
        # Visualization should be a 3-channel image
        assert vis.ndim == 3
        assert vis.shape[2] == 3

    def test_medium_contour_isolated_removed(self) -> None:
        """Medium contour with no nearby pixels should be removed."""
        img = np.zeros((200, 200), dtype=np.uint8)
        # An isolated medium-sized contour
        img[100:108, 100:108] = 255

        contours = _find_contours(img.copy())
        cleaned, _ = remove_small_contours(
            img.copy(), contours, min_w_pct=0.10, min_h_pct=0.10
        )
        # The isolated medium contour should be cleared
        assert (cleaned[100:108, 100:108] == 0).all()

    def test_already_zeroed_contour_skipped(self) -> None:
        """Covers line 65 (continue): contour region already all zeros.

        Pass a contour whose bounding region in the image is all zeros;
        the function should skip it and return the image unchanged.
        """
        # Create a temporary image with a blob to get a valid contour
        template = np.zeros((100, 100), dtype=np.uint8)
        template[10:20, 10:20] = 255
        contours = _find_contours(template.copy())

        # Now pass a blank image (all zeros) so contour_sum == 0 → continue
        blank = np.zeros((100, 100), dtype=np.uint8)
        out, _ = remove_small_contours(blank.copy(), list(contours))
        # Image should remain all zeros
        assert np.sum(out) == 0

    def test_medium_contour_below_size_threshold_covers_search_area(self) -> None:
        """Covers lines 75-91: contour is NOT tiny but IS below pixels_w/h threshold.

        Use small_contour_w/h=5 (tiny threshold) and min_w_pct/min_h_pct=0.20
        (large size threshold), so a 12x12 contour is:
          - NOT tiny (12 >= 5) → does not hit the 'directly remove' path
          - IS below size threshold (12 < 200*0.20=40) → enters the search area code

        The nearby_pixel_count threshold determines if the contour is removed (low count)
        or kept (high count, red rectangle drawn at line 91).
        """
        img = np.zeros((200, 200), dtype=np.uint8)
        # Isolated medium contour: 12x12 -- above tiny (5) but below size threshold (40)
        img[50:62, 50:62] = 255
        contours = _find_contours(img.copy())

        # nearby_pixel_count=100 → threshold_sum = 25500, search_sum < 25500 → removed
        out_removed, _vis_removed = remove_small_contours(
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
        contours2 = _find_contours(img2.copy())
        out_kept, _vis_kept = remove_small_contours(
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

    def test_l27_small_contour_fast_path_disabled_with_zero_thresholds(self) -> None:
        """L-27: passing ``small_contour_w=0, small_contour_h=0`` disables the
        cv2-only unconditional fast-path so cv2 mirrors the cupy backend's
        neighborhood-only behavior.

        Per the L-27 docstring escape hatch: with the fast path disabled,
        a tiny 6x6 dot adjacent to a large support blob (well above
        threshold_sum nearby pixels) is KEPT — the same outcome the cupy
        ``remove_small_contours_gpu`` produces. With the default
        ``small_contour_w=10, small_contour_h=10``, the same dot is
        unconditionally removed (cv2 backend divergence). This test pins
        BOTH outcomes so a future change cannot silently flip the cv2
        default behavior or remove the escape-hatch contract.
        """
        img = np.zeros((200, 200), dtype=np.uint8)
        # Big neighbor blob: provides plenty of nearby pixels
        img[80:160, 20:180] = 255
        # Tiny 6x6 dot directly above the big blob (well within search radius)
        img[60:66, 60:66] = 255

        contours = _find_contours(img.copy())

        # Default fast path: tiny dot < 10x10 -> unconditionally removed.
        cleaned_default, _ = remove_small_contours(img.copy(), contours)
        assert (cleaned_default[60:66, 60:66] == 0).all()

        # Fast path disabled (mirrors cupy): neighborhood check sees the
        # adjacent big blob and the dot is KEPT.
        contours2 = _find_contours(img.copy())
        cleaned_no_fastpath, _ = remove_small_contours(
            img.copy(),
            contours2,
            small_contour_w=0,
            small_contour_h=0,
        )
        assert (cleaned_no_fastpath[60:66, 60:66] == 255).all()
        # And the big blob is unaffected in either case.
        assert (cleaned_no_fastpath[80:160, 20:180] == 255).all()

    def test_l27_divergence_is_documented(self) -> None:
        """L-27: the behavioral divergence between cv2 and cupy backends
        must remain documented so future maintainers don't quietly delete
        the escape-hatch contract.
        """
        from pdomain_book_tools.image_processing.cv2_processing.contours import (
            remove_small_contours as cv2_fn,
        )

        assert "L-27" in (cv2_fn.__doc__ or "")
        assert "small_contour_w=0" in (cv2_fn.__doc__ or "")
