import os

import pytest

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.geometry.point import Point
from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pd_book_tools.ocr.page import Page
from pd_book_tools.ocr.word import Word

# GPU/CUDA Testing Configuration =============================================


def _is_cuda_available():
    """Check if CUDA is available for testing."""
    try:
        import cupy

        return cupy.cuda.is_available()
    except (ImportError, RuntimeError):
        # ImportError: cupy not installed
        # RuntimeError: CUDA driver/runtime issues (e.g., insufficient driver version)
        return False


def _is_torch_cuda_available():
    """Check if PyTorch CUDA is available."""
    try:
        import torch

        return torch.cuda.is_available()
    except ImportError:
        return False


def _is_ci_environment():
    """Check if running in CI environment (GitHub Actions, GitLab CI, etc.)."""
    ci_indicators = [
        "CI",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "JENKINS_URL",
        "BUILDKITE",
        "CIRCLECI",
        "TRAVIS",
    ]
    return any(os.getenv(indicator) for indicator in ci_indicators)


# Pytest markers for GPU tests
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "gpu: mark test as requiring GPU/CUDA functionality"
    )
    config.addinivalue_line("markers", "cupy: mark test as requiring CuPy library")
    config.addinivalue_line(
        "markers", "torch_cuda: mark test as requiring PyTorch CUDA"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (skip with -m 'not slow')"
    )


# GPU Fixtures ================================================================


@pytest.fixture(scope="session")
def cuda_available():
    """Session-scoped fixture that checks CUDA availability."""
    return _is_cuda_available()


@pytest.fixture(scope="session")
def torch_cuda_available():
    """Session-scoped fixture that checks PyTorch CUDA availability."""
    return _is_torch_cuda_available()


@pytest.fixture(scope="session")
def ci_environment():
    """Session-scoped fixture that detects CI environment."""
    return _is_ci_environment()


@pytest.fixture
def cupy_module():
    """Fixture that imports and returns cupy module, or skips if unavailable."""
    cupy = pytest.importorskip("cupy", reason="CuPy not available")
    try:
        if not cupy.cuda.is_available():
            pytest.skip("CUDA not available for CuPy")
    except RuntimeError as e:
        pytest.skip(f"CUDA runtime error: {e}")
    return cupy


@pytest.fixture
def torch_cuda():
    """Fixture that imports torch and checks CUDA, or skips if unavailable."""
    torch = pytest.importorskip("torch", reason="PyTorch not available")
    if not torch.cuda.is_available():
        pytest.skip("CUDA not available for PyTorch")
    return torch


@pytest.fixture
def gpu_array_factory(cupy_module):
    """Factory fixture for creating GPU arrays with CuPy."""

    def _create_array(shape, dtype=None, fill_value=None):
        if fill_value is not None:
            return cupy_module.full(shape, fill_value, dtype=dtype)
        return cupy_module.random.randint(
            0, 255, shape, dtype=dtype or cupy_module.uint8
        )

    return _create_array


@pytest.fixture
def sample_gpu_image(cupy_module):
    """Create a sample grayscale image on GPU."""
    return cupy_module.random.randint(0, 255, (100, 100), dtype=cupy_module.uint8)


@pytest.fixture
def sample_gpu_color_image(cupy_module):
    """Create a sample color image on GPU."""
    return cupy_module.random.randint(0, 255, (100, 100, 3), dtype=cupy_module.uint8)


# Skip conditions for GPU tests ==============================================

skipif_no_cuda = pytest.mark.skipif(
    not _is_cuda_available() or _is_ci_environment(),
    reason="CUDA not available or running in CI environment",
)

skipif_no_cupy = pytest.mark.skipif(
    not _is_cuda_available(), reason="CuPy/CUDA not available"
)

skipif_no_torch_cuda = pytest.mark.skipif(
    not _is_torch_cuda_available(), reason="PyTorch CUDA not available"
)

skipif_ci = pytest.mark.skipif(
    _is_ci_environment(), reason="Skipping GPU tests in CI environment"
)


@pytest.fixture
def sample_word1():
    return Word(
        text="word1",
        bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10),
        ocr_confidence=0.9,
    )


@pytest.fixture
def sample_word2():
    return Word(
        text="word2",
        bounding_box=BoundingBox.from_ltrb(10, 0, 20, 10),
        ocr_confidence=0.8,
        word_labels=["label_word2"],
    )


@pytest.fixture
def sample_line1(sample_word1, sample_word2):
    return [
        sample_word1,
        sample_word2,
    ]


@pytest.fixture
def sample_line2():
    return [
        Word(
            text="word3",
            bounding_box=BoundingBox.from_ltrb(0, 10, 10, 20),
            ocr_confidence=0.9,
        ),
        Word(
            text="word4",
            bounding_box=BoundingBox.from_ltrb(10, 10, 20, 20),
            ocr_confidence=0.8,
        ),
    ]


@pytest.fixture
def sample_line3():
    return [
        Word(
            text="word5",
            bounding_box=BoundingBox.from_ltrb(0, 20, 10, 30),
            ocr_confidence=0.9,
        ),
        Word(
            text="word6",
            bounding_box=BoundingBox.from_ltrb(0, 20, 20, 30),
            ocr_confidence=0.8,
        ),
    ]


@pytest.fixture
def sample_line4():
    return [
        Word(
            text="word7",
            bounding_box=BoundingBox.from_ltrb(0, 30, 10, 40),
            ocr_confidence=0.9,
        ),
        Word(
            text="word8",
            bounding_box=BoundingBox.from_ltrb(0, 30, 20, 40),
            ocr_confidence=0.8,
        ),
    ]


@pytest.fixture
def sample_block1(sample_line1):
    return Block(
        items=sample_line1,
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
        block_labels=["labelline1"],
    )


@pytest.fixture
def sample_block2(sample_line2):
    return Block(
        items=sample_line2,
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
        block_labels=["labelline2"],
    )


@pytest.fixture
def sample_block3(sample_line3):
    return Block(
        items=sample_line3,
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
        block_labels=["labelline3"],
    )


@pytest.fixture
def sample_block4(sample_line4):
    return Block(
        items=sample_line4,
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
        block_labels=["labelline4"],
    )


@pytest.fixture
def sample_paragraph_block1(sample_block1, sample_block2, sample_block3):
    # initialize with out-of-order list to test sorting
    return Block(
        items=[sample_block1, sample_block3, sample_block2],
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.PARAGRAPH,
        block_labels=["labelparagraph1"],
    )


@pytest.fixture
def sample_two_paragraph_block1(sample_block1, sample_block2, sample_block3):
    block1 = Block(
        items=[sample_block2, sample_block1],
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.PARAGRAPH,
        block_labels=["labelparagraph1-1"],
    )
    block2 = Block(
        items=[sample_block3],
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.PARAGRAPH,
        block_labels=["labelparagraph1-2"],
    )
    return Block(
        items=[block2, block1],
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.BLOCK,
        block_labels=["labelparagraph2"],
    )


@pytest.fixture
def sample_page(sample_two_paragraph_block1, sample_block4):
    return Page(
        width=100,
        height=200,
        page_index=1,
        items=[sample_two_paragraph_block1, sample_block4],
        page_labels=["labelpage1"],
    )


# Geometry fixtures -----------------------------------------------------------


@pytest.fixture
def norm_point():
    return Point(0.5, 0.5)


@pytest.fixture
def pixel_point():
    return Point(10, 20)


@pytest.fixture
def point_factory():
    def _make(x: float | int, y: float | int, is_normalized: bool | None = None):
        return Point(x, y, is_normalized=is_normalized)

    return _make
