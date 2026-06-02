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


def scanned_pipeline(
    *, with_uvdoc: bool = False, dewarp_override: str | None = None
) -> GeometryPipeline:
    """Reference pipeline for scanned books: regime routes flat_curl -> textline_disparity.

    Oblique pages route to UVDoc when ``with_uvdoc`` and the ``[dewarp-dl]`` extra
    are available. Callers may force a specific backend via ``dewarp_override``.
    """
    from pdomain_book_tools.geometry_correction.regime import RegimeDetector

    registry.ensure_defaults()
    backends = {"textline_disparity": registry.get_dewarp("textline_disparity")}
    if with_uvdoc:
        backends["uvdoc"] = registry.get_dewarp("uvdoc")
    return GeometryPipeline(
        page_side=cast("PageSideDetector", registry.get_page_side("gutter_shadow")),
        curvature=cast("CurvatureDetector", registry.get_curvature("image_based")),
        deskew=cast("Deskew", registry.get_deskew("projection")),
        dewarp_backends=backends,
        regime=RegimeDetector(),
        dewarp_override=dewarp_override,
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
