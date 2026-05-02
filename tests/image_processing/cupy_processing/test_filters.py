"""Tests for cupy_processing.filters module."""

import numpy as np
import pytest


@pytest.mark.gpu
@pytest.mark.cupy
class TestGaussianFilterGpu:
    def test_output_shape_and_dtype_grayscale(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.filters import (
            gaussian_filter_gpu,
        )

        img = cp.full((50, 50), 128, dtype=cp.uint8)
        out = gaussian_filter_gpu(img, sigma=1.0)
        assert out.shape == img.shape
        assert out.dtype == cp.uint8

    def test_output_shape_and_dtype_color(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.filters import (
            gaussian_filter_gpu,
        )

        img = cp.full((50, 50, 3), 128, dtype=cp.uint8)
        out = gaussian_filter_gpu(img, sigma=1.0)
        assert out.shape == img.shape
        assert out.dtype == cp.uint8

    def test_uniform_image_unchanged(self, cupy_module):
        """Blurring a constant image should return the same constant value."""
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.filters import (
            gaussian_filter_gpu,
        )

        img = cp.full((30, 30), 200, dtype=cp.uint8)
        out = gaussian_filter_gpu(img, sigma=2.0)
        assert cp.all(out == 200)

    def test_blur_reduces_sharp_edge(self, cupy_module):
        """A hard edge should become softer after Gaussian blur."""
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.filters import (
            gaussian_filter_gpu,
        )

        img = cp.zeros((30, 30), dtype=cp.uint8)
        img[:, 15:] = 255
        out = gaussian_filter_gpu(img, sigma=2.0)
        # Pixels just left of the edge should be > 0 after blur
        assert int(out[15, 13]) > 0

    def test_channels_filtered_independently(self, cupy_module):
        """Each colour channel should be blurred without bleeding into others."""
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.filters import (
            gaussian_filter_gpu,
        )

        img = cp.zeros((30, 30, 3), dtype=cp.uint8)
        img[:, :, 0] = 255  # only B channel is non-zero
        out = gaussian_filter_gpu(img, sigma=1.0)
        # G and R channels should stay zero
        assert cp.all(out[:, :, 1] == 0)
        assert cp.all(out[:, :, 2] == 0)

    def test_np_wrapper_returns_numpy(self, cupy_module):
        from pd_book_tools.image_processing.cupy_processing.filters import (
            np_uint8_gaussian_filter,
        )

        img = np.full((20, 20), 100, dtype=np.uint8)
        out = np_uint8_gaussian_filter(img, sigma=1.0)
        assert isinstance(out, np.ndarray)
        assert out.dtype == np.uint8
        assert out.shape == img.shape


@pytest.mark.gpu
@pytest.mark.cupy
class TestMedianFilterGpu:
    def test_output_shape_and_dtype(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.filters import (
            median_filter_gpu,
        )

        img = cp.full((30, 30), 128, dtype=cp.uint8)
        out = median_filter_gpu(img, size=3)
        assert out.shape == img.shape
        assert out.dtype == cp.uint8

    def test_removes_single_bright_pixel(self, cupy_module):
        """Median filter should suppress a single salt pixel."""
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.filters import (
            median_filter_gpu,
        )

        img = cp.zeros((20, 20), dtype=cp.uint8)
        img[10, 10] = 255  # single salt pixel
        out = median_filter_gpu(img, size=3)
        assert int(out[10, 10]) == 0

    def test_uniform_image_unchanged(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.filters import (
            median_filter_gpu,
        )

        img = cp.full((20, 20), 77, dtype=cp.uint8)
        out = median_filter_gpu(img)
        assert cp.all(out == 77)

    def test_color_image_per_channel(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.filters import (
            median_filter_gpu,
        )

        img = cp.zeros((20, 20, 3), dtype=cp.uint8)
        img[10, 10, 1] = 255  # salt in G channel only
        out = median_filter_gpu(img, size=3)
        assert int(out[10, 10, 1]) == 0  # removed
        assert int(out[10, 10, 0]) == 0  # B unaffected
        assert int(out[10, 10, 2]) == 0  # R unaffected

    def test_np_wrapper_returns_numpy(self, cupy_module):
        from pd_book_tools.image_processing.cupy_processing.filters import (
            np_uint8_median_filter,
        )

        img = np.zeros((20, 20), dtype=np.uint8)
        img[10, 10] = 255
        out = np_uint8_median_filter(img, size=3)
        assert isinstance(out, np.ndarray)
        assert out[10, 10] == 0


@pytest.mark.gpu
@pytest.mark.cupy
class TestUniformFilterGpu:
    def test_output_shape_and_dtype(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.filters import (
            uniform_filter_gpu,
        )

        img = cp.full((30, 30), 128, dtype=cp.uint8)
        out = uniform_filter_gpu(img, size=3)
        assert out.shape == img.shape
        assert out.dtype == cp.uint8

    def test_uniform_image_unchanged(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.filters import (
            uniform_filter_gpu,
        )

        img = cp.full((20, 20), 50, dtype=cp.uint8)
        out = uniform_filter_gpu(img)
        assert cp.all(out == 50)

    def test_averages_neighbourhood(self, cupy_module):
        """A 3×3 box filter over a step edge should produce intermediate values."""
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.filters import (
            uniform_filter_gpu,
        )

        img = cp.zeros((10, 10), dtype=cp.uint8)
        img[:, 5:] = 255
        out = uniform_filter_gpu(img, size=3)
        # Pixel right on the edge gets a mix of 0 and 255
        mid = int(out[5, 5])
        assert 0 < mid < 255

    def test_color_image_per_channel(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.filters import (
            uniform_filter_gpu,
        )

        img = cp.zeros((20, 20, 3), dtype=cp.uint8)
        img[:, :, 0] = 60
        img[:, :, 1] = 120
        img[:, :, 2] = 180
        out = uniform_filter_gpu(img)
        # Uniform image: filter should leave values unchanged
        assert int(out[10, 10, 0]) == 60
        assert int(out[10, 10, 1]) == 120
        assert int(out[10, 10, 2]) == 180

    def test_np_wrapper_returns_numpy(self, cupy_module):
        from pd_book_tools.image_processing.cupy_processing.filters import (
            np_uint8_uniform_filter,
        )

        img = np.full((20, 20), 200, dtype=np.uint8)
        out = np_uint8_uniform_filter(img)
        assert isinstance(out, np.ndarray)
        assert out.dtype == np.uint8
        assert (out == 200).all()
