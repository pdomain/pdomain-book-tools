"""Regression tests for M-30:

`rescale_image_gpu` previously called `cupyx.scipy.ndimage.zoom(..., order=1)`
(bare bilinear) regardless of scale factor. cv2's reference implementation uses
`INTER_AREA` for downscaling, which performs pixel-area averaging and is
alias-free; bare bilinear aliases hard on high-frequency content (book scan
edges, hairline rules) and visibly degrades OCR accuracy on 4x reductions.

Fix adds a `uniform_filter` (box average) pre-pass sized to the source-pixels-
per-output-pixel ratio whenever the zoom factor is less than 1 on either axis.
This approximates `INTER_AREA`'s anti-aliasing without requiring a
cv2-equivalent on the GPU side.
"""

import pytest


@pytest.mark.gpu
@pytest.mark.cupy
class TestRescaleImageGpuAntialias:
    def test_4x_downscale_alternating_columns_no_aliasing(self, cupy_module):
        """Bare-bilinear baseline produced std~74 on this fixture
        (mean 127, full 0/255 alternation). The fix must collapse
        the alternating signal to ~mid-gray (the area average), so std
        must be small even though the source is high-frequency."""
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing.rescale import (
            rescale_image_gpu,
        )

        img = cp.zeros((800, 800), dtype=cp.uint8)
        img[:, ::2] = 255

        out = cp.asnumpy(rescale_image_gpu(img, target_short_side=200))

        assert out.shape == (200, 200)
        # Mean must remain mid-gray (the true area average).
        assert 120 <= out.mean() <= 135
        # Bare bilinear yielded std ~74; area-averaged output must be
        # well below half of that.
        assert out.std() < 30.0

    def test_uniform_field_preserved_under_downscale(self, cupy_module):
        """A constant-valued source must remain (essentially) constant
        after rescaling — the anti-alias pre-filter must not introduce
        bias. Tolerance covers float32 round-trip + uint8 quantization."""
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing.rescale import (
            rescale_image_gpu,
        )

        img = cp.full((400, 200), 100, dtype=cp.uint8)
        out = cp.asnumpy(rescale_image_gpu(img, target_short_side=50))

        assert out.shape == (100, 50)
        assert abs(out.mean() - 100.0) < 1.0
        assert out.std() < 1.0

    def test_upscale_path_unchanged(self, cupy_module):
        """When zoom > 1 on both axes the pre-filter must not engage —
        upscaling synthesizes; box-filtering an upscaled image would just
        blur it. Verify a constant-valued input survives unchanged
        (float32/uint8 round-trip aside) and shape grows correctly."""
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing.rescale import (
            rescale_image_gpu,
        )

        img = cp.full((100, 100), 200, dtype=cp.uint8)
        out = cp.asnumpy(rescale_image_gpu(img, target_short_side=400))

        assert out.shape == (400, 400)
        assert abs(out.mean() - 200.0) < 1.0

    def test_horizontal_lines_survive_downscale(self, cupy_module):
        """A small set of widely-spaced horizontal lines (typical
        book-page rule lines) must remain detectable post-downscale.
        This guards against the pre-filter being so aggressive that it
        erases foreground content — the no-silent-data-loss invariant
        applied to image content."""
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing.rescale import (
            rescale_image_gpu,
        )

        img = cp.full((400, 400), 255, dtype=cp.uint8)
        # 4 horizontal black lines, well separated.
        for y in (50, 150, 250, 350):
            img[y, :] = 0

        out = cp.asnumpy(rescale_image_gpu(img, target_short_side=200))
        # The lines must darken some rows below the bright background;
        # the dimmest row must be visibly lower than the brightest.
        row_means = out.mean(axis=1)
        assert row_means.max() - row_means.min() > 30.0

    def test_color_image_anti_alias_per_channel(self, cupy_module):
        """3-channel input still gets per-spatial-axis anti-aliasing
        without cross-channel mixing."""
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing.rescale import (
            rescale_image_gpu,
        )

        img = cp.zeros((400, 400, 3), dtype=cp.uint8)
        # Red-only alternating columns: green/blue planes are fully zero,
        # red plane has 0/255 alternation.
        img[:, ::2, 0] = 255

        out = cp.asnumpy(rescale_image_gpu(img, target_short_side=100))
        assert out.shape == (100, 100, 3)
        # Green and blue channels stay near zero (no leakage from anti-alias).
        assert out[:, :, 1].max() <= 1
        assert out[:, :, 2].max() <= 1
        # Red channel area-averaged to mid-range (no aliasing).
        assert 120 <= out[:, :, 0].mean() <= 135
        assert out[:, :, 0].std() < 30.0
