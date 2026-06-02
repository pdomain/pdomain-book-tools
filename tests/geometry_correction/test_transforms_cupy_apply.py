import numpy as np
import pytest


@pytest.mark.gpu
@pytest.mark.cupy
class TestGeometryTransformCuPyApply:
    def test_cupy_grid_apply_matches_cv2_remap(self, cupy_module):
        cp = cupy_module
        from pdomain_book_tools.geometry_correction.transforms import GeometryTransform

        rng = np.random.default_rng(3)
        img = rng.integers(0, 255, (64, 96), dtype=np.uint8)
        h, w = img.shape
        # a mild smooth backward map
        xs = np.arange(w, dtype=np.float32)
        ys = np.arange(h, dtype=np.float32)
        gx, gy = np.meshgrid(xs, ys)
        map_x = (gx + 1.5 * np.sin(gy / 12.0)).astype(np.float32)
        map_y = (gy + 1.5 * np.cos(gx / 14.0)).astype(np.float32)

        cpu = GeometryTransform.grid(map_x, map_y, (h, w)).apply(img)

        gpu_t = GeometryTransform.grid(cp.asarray(map_x), cp.asarray(map_y), (h, w))
        gpu = cp.asnumpy(gpu_t.apply(cp.asarray(img)))

        # cv2.remap (cubic) vs map_coordinates (cubic) agree within a few levels
        # Tolerance relaxed to 8.0 since cv2 uses different cubic kernel than scipy
        assert np.abs(gpu.astype(int) - cpu.astype(int)).mean() < 8.0
