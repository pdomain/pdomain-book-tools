"""Array-accepting layout detection helpers.

Provides :func:`auto_detect_illustrations_from_array`, which accepts a BGR
``uint8`` ndarray instead of a file path.  Pipeline stages that already hold
a decoded image can call this directly, skipping the temp-file write that the
path-accepting variant would require.

The returned :class:`~pdomain_book_tools.layout.types.PageLayout` contains
only regions whose :attr:`~pdomain_book_tools.layout.types.LayoutRegion.type`
belongs to ``{figure, table, decoration}`` and whose confidence meets
``confidence_threshold``.  Consumers that need all region types (including
``text``, ``header``, etc.) should call ``layout_detector.detect(img)``
directly.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt

from pdomain_book_tools.layout.types import LayoutRegion, PageLayout, RegionType

ImageArray = npt.NDArray[np.uint8]

_ILLUSTRATION_TYPES = frozenset(
    {RegionType.figure, RegionType.table, RegionType.decoration}
)


def auto_detect_illustrations_from_array(
    img: ImageArray,
    *,
    layout_detector: Any,
    confidence_threshold: float = 0.5,
) -> PageLayout:
    """Run the layout detector on a BGR ndarray and return illustration regions.

    Accepts an ndarray directly, so callers that already have a decoded image
    in memory avoid the encode-to-disk / read-from-disk round-trip that a
    path-based API would require.

    Only regions of type ``figure``, ``table``, or ``decoration`` that meet
    ``confidence_threshold`` are included in the returned
    :class:`~pdomain_book_tools.layout.types.PageLayout`.  The
    :attr:`~pdomain_book_tools.layout.types.PageLayout.image_width` and
    :attr:`~pdomain_book_tools.layout.types.PageLayout.image_height` reflect the
    dimensions of the supplied array; the
    :attr:`~pdomain_book_tools.layout.types.PageLayout.detector` field is
    propagated from the underlying detector.

    Args:
        img: BGR ``uint8`` ndarray (H, W, 3).
        layout_detector: Any object with a ``detect(source) -> PageLayout``
            method (i.e. anything satisfying
            :class:`~pdomain_book_tools.layout.detector.LayoutDetector`).
            ``None`` is accepted and treated as "no detector available",
            returning an empty layout.
        confidence_threshold: Regions with
            :attr:`~pdomain_book_tools.layout.types.LayoutRegion.confidence`
            strictly below this value are excluded.  Default ``0.5``.

    Returns:
        A :class:`~pdomain_book_tools.layout.types.PageLayout` whose
        :attr:`~pdomain_book_tools.layout.types.PageLayout.regions` list
        contains only illustration-type regions above the confidence threshold.
    """
    h, w = img.shape[:2]

    if layout_detector is None:
        return PageLayout(
            regions=[],
            image_width=int(w),
            image_height=int(h),
            detector="none",
        )

    full_layout: PageLayout = layout_detector.detect(img)

    filtered: list[LayoutRegion] = [
        r
        for r in full_layout.regions
        if isinstance(r, LayoutRegion)
        and r.type in _ILLUSTRATION_TYPES
        and r.confidence >= confidence_threshold
    ]

    return PageLayout(
        regions=filtered,
        image_width=full_layout.image_width,
        image_height=full_layout.image_height,
        detector=full_layout.detector,
        inference_ms=full_layout.inference_ms,
    )
