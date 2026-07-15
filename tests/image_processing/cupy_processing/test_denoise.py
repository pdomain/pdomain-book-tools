"""Tests for cupy_processing.denoise module.

GPU tests (marked ``@pytest.mark.gpu`` + ``@pytest.mark.cupy``) require the
``cupy_module`` fixture, which skips automatically when CUDA is unavailable.

CPU-equivalence tests assert array-equal results between the CuPy mirror and
the cv2 reference implementation on binary images — component filtering is
deterministic, so exact equality is the correct bar.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

if TYPE_CHECKING:
    from types import ModuleType

    import numpy.typing as npt

# ---------------------------------------------------------------------------
# Shared fixture helpers (same synthetic images as cv2 test_denoise.py)
# ---------------------------------------------------------------------------


def _synthetic_page_with_speckle() -> npt.NDArray[np.uint8]:
    """Binary page image (text=0, background=255) with text strokes + speckle."""
    img = np.full((300, 200), 255, dtype=np.uint8)
    img[50:65, 20:180] = 0  # horizontal text line
    img[30:80, 80:90] = 0  # vertical letter stem
    img[150:155, 50:55] = 0  # period-sized dot (5x5 = 25 px²)
    speckle_coords = [
        (10, 10),
        (20, 150),
        (90, 170),
        (200, 30),
        (250, 100),
        (5, 5),
        (280, 190),
        (100, 100),
        (60, 10),
        (60, 195),
    ]
    for r, c in speckle_coords:
        img[r, c] = 0
    img[180:182, 180:182] = 0  # 2x2 cluster speckle (area=4)
    return img


# ---------------------------------------------------------------------------
# Import guard — module must load without cupy installed
# ---------------------------------------------------------------------------


def test_denoise_module_imports_without_cupy() -> None:
    """The denoise module must be importable without cupy at module-load time."""
    import importlib

    importlib.import_module(
        "pdomain_book_tools.image_processing.cupy_processing.denoise"
    )


# ---------------------------------------------------------------------------
# GPU tests — require cupy_module fixture (auto-skips without CUDA)
# ---------------------------------------------------------------------------


@pytest.mark.gpu
@pytest.mark.cupy
class TestDenoiseBinaryGpuBasic:
    def test_returns_cupy_array(self, cupy_module: ModuleType) -> None:
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing.denoise import (
            denoise_binary_gpu,
        )

        img = cp.full((50, 50), 255, dtype=cp.uint8)
        out = denoise_binary_gpu(img)
        assert isinstance(out, cp.ndarray)

    def test_shape_preserved(self, cupy_module: ModuleType) -> None:
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing.denoise import (
            denoise_binary_gpu,
        )

        img = cp.asarray(_synthetic_page_with_speckle())
        out = denoise_binary_gpu(img)
        assert out.shape == img.shape

    def test_dtype_preserved(self, cupy_module: ModuleType) -> None:
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing.denoise import (
            denoise_binary_gpu,
        )

        img = cp.asarray(_synthetic_page_with_speckle())
        out = denoise_binary_gpu(img)
        assert out.dtype == cp.uint8

    def test_output_is_binary_values_only(self, cupy_module: ModuleType) -> None:
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing.denoise import (
            denoise_binary_gpu,
        )

        img = cp.asarray(_synthetic_page_with_speckle())
        out = denoise_binary_gpu(img)
        unique = set(cp.asnumpy(cp.unique(out)).tolist())
        assert unique.issubset({0, 255})

    def test_all_white_returns_all_white(self, cupy_module: ModuleType) -> None:
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing.denoise import (
            denoise_binary_gpu,
        )

        img = cp.full((50, 50), 255, dtype=cp.uint8)
        out = denoise_binary_gpu(img)
        assert bool(cp.all(out == 255))

    def test_all_black_returns_all_black(self, cupy_module: ModuleType) -> None:
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing.denoise import (
            denoise_binary_gpu,
        )

        img = cp.zeros((50, 50), dtype=cp.uint8)
        out = denoise_binary_gpu(img)
        assert bool(cp.all(out == 0))

    def test_single_pixel_speckle_removed(self, cupy_module: ModuleType) -> None:
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing.denoise import (
            denoise_binary_gpu,
        )

        img_np = _synthetic_page_with_speckle()
        img = cp.asarray(img_np)
        out = denoise_binary_gpu(img)
        assert int(cp.asnumpy(out)[10, 10]) == 255, (
            "single-pixel speckle must be removed"
        )

    def test_text_stroke_preserved(self, cupy_module: ModuleType) -> None:
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing.denoise import (
            denoise_binary_gpu,
        )

        img_np = _synthetic_page_with_speckle()
        img = cp.asarray(img_np)
        out = denoise_binary_gpu(img)
        assert int(cp.asnumpy(out)[57, 100]) == 0, "text stroke must be preserved"

    def test_period_dot_preserved(self, cupy_module: ModuleType) -> None:
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing.denoise import (
            denoise_binary_gpu,
        )

        img_np = _synthetic_page_with_speckle()
        img = cp.asarray(img_np)
        out = denoise_binary_gpu(img)
        assert int(cp.asnumpy(out)[152, 52]) == 0, (
            "period dot (25 px) must be preserved"
        )


@pytest.mark.gpu
@pytest.mark.cupy
class TestDenoiseBinaryGpuEquivalence:
    """Exact CPU↔GPU equivalence — component filtering is deterministic."""

    def test_array_equal_to_cpu_no_median(self, cupy_module: ModuleType) -> None:
        """GPU output must be array-equal to cv2 CPU output on binary images."""
        cp = cupy_module
        pytest.importorskip("cv2")
        from pdomain_book_tools.image_processing.cupy_processing.denoise import (
            denoise_binary_gpu,
        )
        from pdomain_book_tools.image_processing.cv2_processing.denoise import (
            denoise_binary as cpu_denoise,
        )

        img_np = _synthetic_page_with_speckle()
        cpu_out = cpu_denoise(img_np)
        gpu_out = cp.asnumpy(denoise_binary_gpu(cp.asarray(img_np)))
        np.testing.assert_array_equal(cpu_out, gpu_out)

    def test_array_equal_to_cpu_with_median(self, cupy_module: ModuleType) -> None:
        """GPU + median pre-pass must match cv2 + median pre-pass exactly."""
        cp = cupy_module
        pytest.importorskip("cv2")
        from pdomain_book_tools.image_processing.cupy_processing.denoise import (
            denoise_binary_gpu,
        )
        from pdomain_book_tools.image_processing.cv2_processing.denoise import (
            denoise_binary as cpu_denoise,
        )

        img_np = _synthetic_page_with_speckle()
        cpu_out = cpu_denoise(img_np, median_kernel_size=3)
        gpu_out = cp.asnumpy(
            denoise_binary_gpu(cp.asarray(img_np), median_kernel_size=3)
        )
        np.testing.assert_array_equal(cpu_out, gpu_out)

    def test_array_equal_custom_min_component_area(
        self, cupy_module: ModuleType
    ) -> None:
        """Custom min_component_area matches CPU exactly."""
        cp = cupy_module
        pytest.importorskip("cv2")
        from pdomain_book_tools.image_processing.cupy_processing.denoise import (
            denoise_binary_gpu,
        )
        from pdomain_book_tools.image_processing.cv2_processing.denoise import (
            denoise_binary as cpu_denoise,
        )

        img_np = _synthetic_page_with_speckle()
        cpu_out = cpu_denoise(img_np, min_component_area=30)
        gpu_out = cp.asnumpy(
            denoise_binary_gpu(cp.asarray(img_np), min_component_area=30)
        )
        np.testing.assert_array_equal(cpu_out, gpu_out)

    def test_all_white_array_equal(self, cupy_module: ModuleType) -> None:
        """All-white images: GPU matches CPU."""
        cp = cupy_module
        pytest.importorskip("cv2")
        from pdomain_book_tools.image_processing.cupy_processing.denoise import (
            denoise_binary_gpu,
        )
        from pdomain_book_tools.image_processing.cv2_processing.denoise import (
            denoise_binary as cpu_denoise,
        )

        img_np = np.full((80, 80), 255, dtype=np.uint8)
        cpu_out = cpu_denoise(img_np)
        gpu_out = cp.asnumpy(denoise_binary_gpu(cp.asarray(img_np)))
        np.testing.assert_array_equal(cpu_out, gpu_out)


# ---------------------------------------------------------------------------
# np_uint8_denoise_binary wrapper tests
# ---------------------------------------------------------------------------


@pytest.mark.gpu
@pytest.mark.cupy
class TestNpUint8DenoiseBinaryWrapper:
    def test_returns_numpy_ndarray(self, cupy_module: ModuleType) -> None:
        from pdomain_book_tools.image_processing.cupy_processing.denoise import (
            np_uint8_denoise_binary,
        )

        img = np.zeros((50, 50), dtype=np.uint8)
        result = np_uint8_denoise_binary(img)
        assert isinstance(result, np.ndarray)
        assert result.ndim == 2

    def test_array_equal_to_direct_gpu(self, cupy_module: ModuleType) -> None:
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing.denoise import (
            denoise_binary_gpu,
            np_uint8_denoise_binary,
        )

        img_np = _synthetic_page_with_speckle()
        wrapper_out = np_uint8_denoise_binary(img_np)
        direct_out = cp.asnumpy(denoise_binary_gpu(cp.asarray(img_np)))
        np.testing.assert_array_equal(wrapper_out, direct_out)


# ---------------------------------------------------------------------------
# Input validation (mirrors cv2 validation: same error messages)
# ---------------------------------------------------------------------------


@pytest.mark.gpu
@pytest.mark.cupy
class TestDenoiseBinaryGpuValidation:
    def test_invalid_ndim_raises(self, cupy_module: ModuleType) -> None:
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing.denoise import (
            denoise_binary_gpu,
        )

        img_3d = cp.zeros((10, 10, 3), dtype=cp.uint8)
        with pytest.raises(ValueError, match="2-D"):
            denoise_binary_gpu(img_3d)

    def test_invalid_dtype_raises(self, cupy_module: ModuleType) -> None:
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing.denoise import (
            denoise_binary_gpu,
        )

        img_float = cp.zeros((10, 10), dtype=cp.float32)
        with pytest.raises(ValueError, match="uint8"):
            denoise_binary_gpu(img_float)

    def test_invalid_even_median_kernel_raises(self, cupy_module: ModuleType) -> None:
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing.denoise import (
            denoise_binary_gpu,
        )

        img = cp.zeros((10, 10), dtype=cp.uint8)
        with pytest.raises(ValueError, match="odd"):
            denoise_binary_gpu(img, median_kernel_size=4)

    def test_invalid_negative_median_kernel_raises(
        self, cupy_module: ModuleType
    ) -> None:
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing.denoise import (
            denoise_binary_gpu,
        )

        img = cp.zeros((10, 10), dtype=cp.uint8)
        with pytest.raises(ValueError, match="odd"):
            denoise_binary_gpu(img, median_kernel_size=-1)
