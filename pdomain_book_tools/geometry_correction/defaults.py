"""Factory helpers for the reference geometry-correction pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from pdomain_book_tools.geometry_correction.pipeline import GeometryPipeline

from . import registry

if TYPE_CHECKING:
    from pdomain_book_tools.geometry_correction.protocols import (
        CurvatureDetector,
        Deskew,
        Dewarp,
        PageSideDetector,
    )


def default_pipeline(*, with_dewarp: bool = False) -> GeometryPipeline:
    """Return the reference pipeline with built-in backends.

    Dewarp is opt-in (requires the ``[dewarp-dl]`` extra and a UVDoc ONNX model;
    see ``$PD_UVDOC_ONNX``). The default runs gutter-shadow page-side detection,
    image-based curvature gate, and projection-profile deskew.
    """
    registry.ensure_defaults()
    dewarp = cast("Dewarp", registry.get_dewarp("uvdoc")) if with_dewarp else None
    return GeometryPipeline(
        page_side=cast("PageSideDetector", registry.get_page_side("gutter_shadow")),
        curvature=cast("CurvatureDetector", registry.get_curvature("image_based")),
        deskew=cast("Deskew", registry.get_deskew("projection")),
        dewarp=dewarp,
    )
