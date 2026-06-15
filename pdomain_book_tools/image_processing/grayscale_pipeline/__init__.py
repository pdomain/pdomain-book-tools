"""Composable grayscale pipeline: flatten → converter → CLAHE."""

from pdomain_book_tools.image_processing.grayscale_pipeline.config import (
    ClaheConfig,
    Color2GrayParams,
    Converter,
    FlattenConfig,
    GrayscaleConfig,
)
from pdomain_book_tools.image_processing.grayscale_pipeline.pipeline import (
    run_grayscale_pipeline,
)

__all__ = [
    "ClaheConfig",
    "Color2GrayParams",
    "Converter",
    "FlattenConfig",
    "GrayscaleConfig",
    "run_grayscale_pipeline",
]
