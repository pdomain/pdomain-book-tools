"""Tests for cupy_processing.split module."""

import numpy as np
import pytest


@pytest.mark.gpu
@pytest.mark.cupy
class TestSplitXColumnsGpu:
    def test_shapes_sum_to_original_width(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.split import (
            split_x_columns_gpu,
        )

        img = cp.ones((20, 30), dtype=cp.uint8)
        left, right = split_x_columns_gpu(img, 10)
        assert left.shape == (20, 10)
        assert right.shape == (20, 20)

    def test_values_are_correct_slice(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.split import (
            split_x_columns_gpu,
        )

        img = cp.zeros((10, 20), dtype=cp.uint8)
        img[:, 10:] = 255
        left, right = split_x_columns_gpu(img, 10)
        assert cp.all(left == 0)
        assert cp.all(right == 255)

    def test_split_at_zero_gives_empty_left(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.split import (
            split_x_columns_gpu,
        )

        img = cp.ones((5, 10), dtype=cp.uint8)
        left, right = split_x_columns_gpu(img, 0)
        assert left.shape[1] == 0
        assert right.shape[1] == 10

    def test_split_at_width_gives_empty_right(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.split import (
            split_x_columns_gpu,
        )

        img = cp.ones((5, 10), dtype=cp.uint8)
        left, right = split_x_columns_gpu(img, 10)
        assert left.shape[1] == 10
        assert right.shape[1] == 0

    def test_out_of_bounds_raises(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.split import (
            split_x_columns_gpu,
        )

        img = cp.ones((5, 10), dtype=cp.uint8)
        with pytest.raises(ValueError):
            split_x_columns_gpu(img, 11)

    def test_color_image(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.split import (
            split_x_columns_gpu,
        )

        img = cp.ones((10, 20, 3), dtype=cp.uint8)
        left, right = split_x_columns_gpu(img, 8)
        assert left.shape == (10, 8, 3)
        assert right.shape == (10, 12, 3)

    def test_np_wrapper_returns_numpy(self, cupy_module):
        from pd_book_tools.image_processing.cupy_processing.split import (
            np_uint8_split_x_columns,
        )

        img = np.ones((10, 20), dtype=np.uint8)
        left, right = np_uint8_split_x_columns(img, 5)
        assert isinstance(left, np.ndarray)
        assert isinstance(right, np.ndarray)
        assert left.shape == (10, 5)


@pytest.mark.gpu
@pytest.mark.cupy
class TestSplitYRowsGpu:
    def test_shapes_sum_to_original_height(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.split import (
            split_y_rows_gpu,
        )

        img = cp.ones((30, 20), dtype=cp.uint8)
        top, bottom = split_y_rows_gpu(img, 10)
        assert top.shape == (10, 20)
        assert bottom.shape == (20, 20)

    def test_values_are_correct_slice(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.split import (
            split_y_rows_gpu,
        )

        img = cp.zeros((20, 10), dtype=cp.uint8)
        img[10:, :] = 255
        top, bottom = split_y_rows_gpu(img, 10)
        assert cp.all(top == 0)
        assert cp.all(bottom == 255)

    def test_out_of_bounds_raises(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.split import (
            split_y_rows_gpu,
        )

        img = cp.ones((10, 5), dtype=cp.uint8)
        with pytest.raises(ValueError):
            split_y_rows_gpu(img, 11)

    def test_np_wrapper_returns_numpy(self, cupy_module):
        from pd_book_tools.image_processing.cupy_processing.split import (
            np_uint8_split_y_rows,
        )

        img = np.ones((20, 10), dtype=np.uint8)
        top, bottom = np_uint8_split_y_rows(img, 8)
        assert isinstance(top, np.ndarray)
        assert isinstance(bottom, np.ndarray)
        assert top.shape == (8, 10)
