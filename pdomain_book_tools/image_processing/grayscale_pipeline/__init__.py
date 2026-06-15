"""Composable grayscale pipeline: flatten → converter → CLAHE."""

from pdomain_book_tools.image_processing.grayscale_pipeline.config import (
    ClaheConfig,
    Color2GrayParams,
    Converter,
    FlattenConfig,
    GrayscaleConfig,
)

__all__ = [
    "ClaheConfig",
    "Color2GrayParams",
    "Converter",
    "FlattenConfig",
    "GrayscaleConfig",
]
