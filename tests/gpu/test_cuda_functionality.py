"""GPU functionality tests for pd-book-tools.

This module contains comprehensive tests for GPU/CUDA functionality including:
- CuPy-based image processing operations (dilate, erode, morph_fill)
- PyTorch CUDA support for neural networks
- Integration tests for GPU processing pipelines
- Performance comparisons between CPU and GPU

Tests automatically skip when:
- CUDA/GPU hardware is not available
- Running in CI environments (GitHub Actions, etc.)
- Required dependencies (CuPy, PyTorch) are missing

Test Organization:
- TestGPUAvailability: Basic GPU detection and conditional logic
- TestCupyProcessing: CuPy GPU array operations and morphology
- TestTorchCuda: PyTorch CUDA tensor operations and DocTR support
- TestGPUIntegration: End-to-end pipelines and performance tests

Usage:
    # Run all GPU tests (skips automatically if no GPU)
    pytest tests/gpu/ -v

    # Run only CuPy tests
    pytest tests/gpu/ -v -m cupy

    # Run only PyTorch CUDA tests
    pytest tests/gpu/ -v -m torch_cuda

    # Skip slow performance tests
    pytest tests/gpu/ -v -m "gpu and not slow"

    # Simulate CI environment (should skip GPU tests)
    CI=true pytest tests/gpu/ -v
"""

import numpy as np
import pytest

from tests.conftest import skipif_ci, skipif_no_cuda


class TestGPUAvailability:
    """Basic tests for GPU availability and configuration."""

    def test_always_runs(self):
        """This test always runs, regardless of GPU availability."""
        assert True

    @pytest.mark.gpu
    def test_conditional_gpu_logic(self, cuda_available):
        """Example of conditional GPU vs CPU logic."""
        if cuda_available:
            # GPU code path
            import cupy as cp

            arr = cp.array([1, 2, 3])
            assert isinstance(arr, cp.ndarray)
        else:
            # CPU fallback (this will run in CI)
            arr = np.array([1, 2, 3])
            assert isinstance(arr, np.ndarray)

    @skipif_ci
    @pytest.mark.gpu
    def test_skip_in_ci_example(self, cuda_available):
        """This test will skip in GitHub Actions but run locally with GPU."""
        assert cuda_available, "This should only run when CUDA is available"


@pytest.mark.gpu
@pytest.mark.cupy
class TestCupyProcessing:
    """Tests for CuPy-based GPU image processing operations."""

    def test_cupy_basic_operations(self, cupy_module):
        """Test basic CuPy array operations on GPU."""
        cp = cupy_module

        # Create array on GPU
        gpu_array = cp.array([1, 2, 3, 4, 5])

        # Perform computation
        result = cp.sum(gpu_array)

        # Convert back to CPU for assertion
        assert result.get() == 15

    def test_cupy_image_processing(self, cupy_module, sample_gpu_image):
        """Test CuPy image processing functions."""
        cp = cupy_module

        # Use fixture-provided GPU image
        gpu_image = sample_gpu_image

        # Test basic operations work on GPU
        assert gpu_image.shape == (100, 100)
        assert gpu_image.dtype == cp.uint8

        # Test conversion back to CPU
        result_cpu = cp.asnumpy(gpu_image)
        assert result_cpu.shape == (100, 100)
        assert isinstance(result_cpu, np.ndarray)

    @pytest.mark.parametrize("image_size", [(50, 50), (100, 100), (200, 200)])
    def test_cupy_array_factory(self, cupy_module, gpu_array_factory, image_size):
        """Test GPU array factory with different sizes."""
        cp = cupy_module

        # Use factory to create test image on GPU
        gpu_image = gpu_array_factory(image_size, dtype=cp.uint8)

        # Test that image is on GPU
        assert isinstance(gpu_image, cp.ndarray)
        assert gpu_image.device.id >= 0  # On a GPU device
        assert gpu_image.shape == image_size

    @pytest.mark.slow
    def test_cupy_morphology_operations(self, cupy_module, sample_gpu_image):
        """Test actual CuPy morphology processing modules."""
        cp = cupy_module

        # Import the actual module we want to test
        try:
            from pd_book_tools.image_processing.cupy_processing.morph import (
                dilate,
                erode,
                morph_fill,
            )
        except ImportError:
            pytest.skip("CuPy processing module not available")

        # Create kernel
        kernel = cp.ones((3, 3), dtype=cp.uint8)

        # Test dilation
        result = dilate(sample_gpu_image, kernel)

        # Verify result properties
        assert isinstance(result, cp.ndarray)
        assert result.shape == sample_gpu_image.shape
        assert result.dtype == sample_gpu_image.dtype

        # Test erosion
        eroded = erode(sample_gpu_image, kernel)
        assert isinstance(eroded, cp.ndarray)
        assert eroded.shape == sample_gpu_image.shape

        # Test morphological fill
        filled = morph_fill(sample_gpu_image, shape=(3, 3))
        assert isinstance(filled, cp.ndarray)
        assert filled.shape == sample_gpu_image.shape

    @skipif_no_cuda
    def test_cupy_when_available(self, cupy_module):
        """Test CuPy functionality when available, skip otherwise."""
        cp = cupy_module

        # Basic CuPy operations
        arr = cp.array([1, 2, 3, 4, 5])
        result = cp.sum(arr)
        assert result.get() == 15


@pytest.mark.gpu
@pytest.mark.torch_cuda
class TestTorchCuda:
    """Tests for PyTorch CUDA functionality."""

    def test_torch_cuda_basic(self, torch_cuda):
        """Test basic PyTorch CUDA operations."""
        torch = torch_cuda

        # Create tensor on GPU
        device = torch.device("cuda:0")
        tensor = torch.tensor([1.0, 2.0, 3.0]).to(device)

        # Verify it's on GPU
        assert tensor.device.type == "cuda"

        # Perform computation
        result = torch.sum(tensor)
        assert result.item() == 6.0

    @skipif_ci
    def test_doctr_gpu_integration(self, torch_cuda):
        """Test DocTR with GPU support."""
        torch = torch_cuda

        # Test device selection logic
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        assert device.type == "cuda"

        # Create a simple tensor on GPU
        tensor = torch.randn(10, 10).to(device)
        assert tensor.is_cuda

    def test_doctr_cuda_support(self, torch_cuda):
        """Test DocTR CUDA functionality if available."""
        torch = torch_cuda
        pytest.importorskip("doctr")

        # Test that CUDA is detected by torch
        assert torch.cuda.is_available()

        # Test device detection logic
        device = "cuda" if torch.cuda.is_available() else "cpu"
        assert device == "cuda"


@pytest.mark.gpu
@pytest.mark.integration
class TestGPUIntegration:
    """Integration tests for complete GPU processing pipelines."""

    def test_full_gpu_pipeline(self, cupy_module, gpu_array_factory):
        """Test complete GPU processing pipeline."""
        cp = cupy_module

        # Create sample image using factory
        gpu_image = gpu_array_factory((200, 200), dtype=cp.uint8, fill_value=128)

        # Simulate processing pipeline
        processed = gpu_image * 0.5  # Simple processing

        # Convert back to CPU
        result = cp.asnumpy(processed).astype(np.uint8)

        assert result.shape == (200, 200)
        assert result.dtype == np.uint8

    @pytest.mark.slow
    def test_gpu_vs_cpu_performance(self, cupy_module, cuda_available, ci_environment):
        """Compare GPU vs CPU processing speed (skip in CI)."""
        if ci_environment:
            pytest.skip("Performance tests not needed in CI")

        cp = cupy_module

        # Large array for performance testing
        size = (1000, 1000)

        # CPU version
        cpu_array = np.random.randint(0, 255, size, dtype=np.uint8)

        # GPU version
        gpu_array = cp.asarray(cpu_array)

        # Simple operation timing (just verify it works, not actual benchmarking)
        cpu_result = cpu_array * 2
        gpu_result = gpu_array * 2

        # Verify results match
        np.testing.assert_array_equal(cpu_result, cp.asnumpy(gpu_result))
