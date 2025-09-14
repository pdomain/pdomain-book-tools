# GPU Testing Strategy

This document explains how GPU/CUDA functionality is tested in pd-book-tools while remaining compatible with CI environments like GitHub Actions that don't have GPU access.

## Overview

The project includes GPU acceleration through:
- **CuPy**: GPU arrays and operations (`cupy_processing/` modules)
- **PyTorch CUDA**: Neural network acceleration (DocTR integration)
- **OpenCV CUDA**: GPU-accelerated computer vision

However, CI environments typically don't have GPUs, so tests must gracefully skip when GPU is unavailable.

## Testing Strategy

### 1. **Fixtures for GPU Detection**

Located in `tests/conftest.py`:

```python
@pytest.fixture(scope="session")
def cuda_available():
    """Check if CUDA is available."""
    return _is_cuda_available()

@pytest.fixture
def cupy_module():
    """Import cupy or skip if unavailable."""
    cupy = pytest.importorskip("cupy")
    if not cupy.cuda.is_available():
        pytest.skip("CUDA not available")
    return cupy
```

### 2. **Skip Conditions**

```python
# Skip GPU tests in CI environments
skipif_ci = pytest.mark.skipif(
    _is_ci_environment(),
    reason="Skipping GPU tests in CI environment"
)

# Skip when CUDA not available
skipif_no_cuda = pytest.mark.skipif(
    not _is_cuda_available(),
    reason="CUDA not available"
)
```

### 3. **Test Patterns**

#### **Pattern 1: Skip in CI**
```python
@skipif_ci
@pytest.mark.gpu
def test_gpu_functionality(cupy_module):
    """Runs locally with GPU, skips in GitHub Actions."""
    cp = cupy_module
    arr = cp.array([1, 2, 3])
    assert cp.sum(arr).get() == 6
```

#### **Pattern 2: Conditional Logic**
```python
@pytest.mark.gpu
def test_conditional_gpu(cuda_available):
    """Adapts behavior based on GPU availability."""
    if cuda_available:
        import cupy as cp
        # GPU code path
    else:
        import numpy as np
        # CPU fallback - runs in CI
```

#### **Pattern 3: Automatic Skip**
```python
@skipif_no_cuda
@pytest.mark.cupy
def test_cupy_required(cupy_module):
    """Only runs when CuPy/CUDA available."""
    # This automatically skips in CI
    pass
```

## Running Tests

### **Local Development (with GPU)**
```bash
# Run all tests (GPU tests will run)
uv run pytest

# Run only GPU tests
uv run pytest -m gpu

# Run specific GPU modules
uv run pytest tests/gpu/ -v

# Skip slow GPU tests
uv run pytest -m "gpu and not slow"
```

### **CI Environment (GitHub Actions)**
```bash
# GPU tests automatically skip
uv run pytest

# Explicitly skip GPU tests
uv run pytest -m "not gpu"
```

### **Force Skip GPU Tests**
```bash
# Simulate CI environment
CI=true uv run pytest

# Use markers to skip
uv run pytest -m "not gpu"
```

## Markers

- `@pytest.mark.gpu` - General GPU functionality
- `@pytest.mark.cupy` - Requires CuPy library
- `@pytest.mark.torch_cuda` - Requires PyTorch CUDA
- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.integration` - Integration tests

## CI Behavior

### **GitHub Actions**
- Environment variable: `GITHUB_ACTIONS=true`
- GPU tests automatically skip
- Only CPU code paths tested
- Tesseract tests run (system binary installed)

### **Local Development**
- GPU tests run if CUDA available
- Provides full test coverage
- Can test GPU performance

## File Organization

```
tests/
├── conftest.py              # GPU fixtures and skip conditions
├── gpu/                     # GPU-specific tests
│   ├── test_examples.py     # Usage patterns
│   └── test_cuda_functionality.py  # Actual GPU tests
├── ocr/                     # Regular tests (run in CI)
├── geometry/               # Regular tests (run in CI)
└── pgdp/                   # Regular tests (run in CI)
```

## Best Practices

### **DO:**
- Use fixtures for GPU imports (`cupy_module`, `torch_cuda`)
- Mark GPU tests with appropriate markers
- Provide CPU fallbacks where possible
- Skip gracefully in CI environments

### **DON'T:**
- Import GPU libraries at module level
- Assume GPU is always available
- Write tests that fail hard without GPU
- Block CI pipeline on GPU unavailability

## Example Test

```python
@pytest.mark.gpu
@pytest.mark.cupy
class TestCupyMorphology:
    """Test GPU morphological operations."""

    def test_dilate_image(self, cupy_module, sample_gpu_image):
        """Test dilation on GPU."""
        cp = cupy_module

        # Import actual module to test
        from pd_book_tools.image_processing.cupy_processing.morph import dilate_image

        # Create kernel
        kernel = cp.ones((3, 3), dtype=cp.uint8)

        # Test operation
        result = dilate_image(sample_gpu_image, kernel)

        # Verify result
        assert isinstance(result, cp.ndarray)
        assert result.shape == sample_gpu_image.shape
```

This approach ensures:
- ✅ **CI passes** without GPU hardware
- ✅ **Local development** gets full GPU test coverage
- ✅ **Graceful degradation** when GPU unavailable
- ✅ **Clear test organization** with markers and fixtures
