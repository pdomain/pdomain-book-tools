"""GPU tests for pd-book-tools.

This module contains tests for GPU/CUDA functionality that automatically skip
when GPU hardware or dependencies are not available, making them CI-friendly.

Test organization:
- TestGPUAvailability: Basic GPU detection and conditional logic
- TestCupyProcessing: CuPy-based GPU array operations and image processing
- TestTorchCuda: PyTorch CUDA support for neural networks
- TestGPUIntegration: End-to-end GPU processing pipelines and performance

Usage:
    pytest tests/gpu/ -v               # All GPU tests (auto-skip if no GPU)
    pytest tests/gpu/ -v -m cupy       # Only CuPy tests
    pytest tests/gpu/ -v -m torch_cuda # Only PyTorch CUDA tests
    pytest tests/gpu/ -v -m "not slow" # Skip slow performance tests
"""
