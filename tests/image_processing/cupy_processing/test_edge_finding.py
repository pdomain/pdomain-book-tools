"""Tests for cupy_processing.edge_finding module."""

import numpy as np
import pytest


@pytest.mark.gpu
@pytest.mark.cupy
class TestFindEdgesGpu:
    def test_blank_image_returns_full_extents(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.edge_finding import (
            find_edges_gpu,
        )

        img = cp.zeros((100, 100), dtype=cp.uint8)
        minX, maxX, minY, maxY = find_edges_gpu(img)
        assert minX == 0
        assert maxX == 100
        assert minY == 0
        assert maxY == 100

    def test_central_block_detected(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.edge_finding import (
            find_edges_gpu,
        )

        img = cp.zeros((200, 200), dtype=cp.uint8)
        img[50:150, 60:140] = 255
        minX, maxX, minY, maxY = find_edges_gpu(
            img, fuzzy_pct=0, pixel_count_columns=1, pixel_count_rows=1
        )
        assert minX <= 60
        assert maxX >= 139
        assert minY <= 50
        assert maxY >= 149

    def test_returns_python_ints(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.edge_finding import (
            find_edges_gpu,
        )

        img = cp.zeros((100, 100), dtype=cp.uint8)
        img[20:80, 20:80] = 200
        result = find_edges_gpu(
            img, fuzzy_pct=0, pixel_count_columns=1, pixel_count_rows=1
        )
        assert all(isinstance(v, int) for v in result)

    def test_threshold_uses_255_not_256(self, cupy_module):
        """Regression for M-02: threshold multiplier must be `* 255`, not `* 256`.

        A column with exactly `pixel_count_columns` fully-bright (255) pixels
        sums to `N * 255`. With the pre-fix `* 256` multiplier the column fell
        strictly below threshold and was missed; post-fix `* 255` it is
        detected.
        """
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.edge_finding import (
            find_edges_gpu,
        )

        img = cp.zeros((200, 200), dtype=cp.uint8)
        img[10, 100] = 255
        img[11, 100] = 255
        img[100, 10] = 255
        img[100, 11] = 255
        minX, maxX, minY, maxY = find_edges_gpu(
            img,
            fuzzy_pct=0,
            pixel_count_columns=2,
            pixel_count_rows=2,
            fuzzy_px_w_override=0,
            fuzzy_px_h_override=0,
        )
        assert minX == 100, f"expected minX=100 (column detected), got {minX}"
        assert maxX == 100, f"expected maxX=100 (column detected), got {maxX}"
        assert minY == 100, f"expected minY=100 (row detected), got {minY}"
        assert maxY == 100, f"expected maxY=100 (row detected), got {maxY}"

    def test_fuzzy_px_override_zero(self, cupy_module):
        """fuzzy_px_w_override=0 should be respected (not treated as falsy)."""
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.edge_finding import (
            find_edges_gpu,
        )

        img = cp.zeros((100, 100), dtype=cp.uint8)
        img[40:60, 40:60] = 255
        minX, maxX, _minY, _maxY = find_edges_gpu(
            img,
            pixel_count_columns=1,
            pixel_count_rows=1,
            fuzzy_px_w_override=0,
            fuzzy_px_h_override=0,
        )
        assert minX <= 40
        assert maxX >= 59

    def test_matches_cpu_reference(self, cupy_module):
        """GPU result must be within ±2 pixels of the CPU reference on the same image."""
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.edge_finding import (
            find_edges_gpu,
        )
        from pd_book_tools.image_processing.cv2_processing.edge_finding import (
            find_edges,
        )

        rng = np.random.default_rng(42)
        img_np = np.zeros((300, 200), dtype=np.uint8)
        img_np[40:260, 30:170] = rng.integers(100, 256, (220, 140), dtype=np.uint8)

        kwargs = {"fuzzy_pct": 0, "pixel_count_columns": 1, "pixel_count_rows": 1}
        cpu = find_edges(img_np, **kwargs)
        gpu = find_edges_gpu(cp.asarray(img_np), **kwargs)

        for cpu_val, gpu_val in zip(cpu, gpu, strict=False):
            assert abs(cpu_val - gpu_val) <= 2, f"CPU={cpu} GPU={gpu}"

    def test_np_uint8_find_edges_wrapper(self, cupy_module):
        from pd_book_tools.image_processing.cupy_processing.edge_finding import (
            np_uint8_find_edges,
        )

        img = np.zeros((100, 100), dtype=np.uint8)
        img[20:80, 20:80] = 200
        minX, maxX, minY, maxY = np_uint8_find_edges(
            img, fuzzy_pct=0, pixel_count_columns=1, pixel_count_rows=1
        )
        assert all(isinstance(v, int) for v in (minX, maxX, minY, maxY))
        assert minX <= 20
        assert maxX >= 79
        assert minY <= 20
        assert maxY >= 79
