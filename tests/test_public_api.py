"""Public API surface tests for ``pd_book_tools``.

These tests pin the documented re-exports listed in
``docs/public-api.md``. Submodule paths are not part of the supported
public API and may relocate in future versions.

The presence (and identity) of these re-exports is what downstream
repos rely on. If a re-export ever needs to be removed or relocated,
that is a deliberate breaking change and these tests should be updated
in the same commit.
"""

from __future__ import annotations


def test_top_level_reexports():
    from pd_book_tools import (
        Block,
        BlockCategory,
        BoundingBox,
        Page,
        PGDPExport,
        PGDPResults,
        Point,
        RegionType,
        Word,
    )

    # Identity check: the top-level name must be the same object as the
    # canonical class in its submodule.
    from pd_book_tools.geometry.bounding_box import BoundingBox as _BB
    from pd_book_tools.geometry.point import Point as _Point
    from pd_book_tools.layout.types import RegionType as _RegionType
    from pd_book_tools.ocr.block import Block as _Block
    from pd_book_tools.ocr.block import BlockCategory as _BlockCategory
    from pd_book_tools.ocr.page import Page as _Page
    from pd_book_tools.ocr.word import Word as _Word
    from pd_book_tools.pgdp.pgdp_results import PGDPExport as _PGDPExport
    from pd_book_tools.pgdp.pgdp_results import PGDPResults as _PGDPResults

    assert BoundingBox is _BB
    assert Point is _Point
    assert Page is _Page
    assert Block is _Block
    assert Word is _Word
    assert RegionType is _RegionType
    assert BlockCategory is _BlockCategory
    assert PGDPResults is _PGDPResults
    assert PGDPExport is _PGDPExport


def test_geometry_reexports():
    from pd_book_tools.geometry import BoundingBox, Point
    from pd_book_tools.geometry.bounding_box import BoundingBox as _BB
    from pd_book_tools.geometry.point import Point as _Point

    assert BoundingBox is _BB
    assert Point is _Point


def test_pgdp_reexports():
    from pd_book_tools.pgdp import PGDPExport, PGDPResults
    from pd_book_tools.pgdp.pgdp_results import PGDPExport as _PGDPExport
    from pd_book_tools.pgdp.pgdp_results import PGDPResults as _PGDPResults

    assert PGDPResults is _PGDPResults
    assert PGDPExport is _PGDPExport


def test_utility_reexports():
    # utility/ previously had no __init__.py at all — the package itself
    # is part of the new public surface.
    import pd_book_tools.utility as utility
    from pd_book_tools.utility import ipynb_widgets, timing

    assert utility.timing is timing
    assert utility.ipynb_widgets is ipynb_widgets


def test_layout_reexports():
    # The layout package already had a populated __init__.py; R-08 adds
    # draw_layout_overlay, clear_detector_cache, and the geometry helpers.
    from pd_book_tools.layout import (
        caption_for_figure,
        clear_detector_cache,
        contains,
        draw_layout_overlay,
        horizontal_overlap_ratio,
        iou,
        region_reading_order,
    )
    from pd_book_tools.layout.geometry import caption_for_figure as _caption
    from pd_book_tools.layout.geometry import contains as _contains
    from pd_book_tools.layout.geometry import (
        horizontal_overlap_ratio as _hor,
    )
    from pd_book_tools.layout.geometry import iou as _iou
    from pd_book_tools.layout.geometry import (
        region_reading_order as _reading_order,
    )
    from pd_book_tools.layout.registry import (
        clear_detector_cache as _clear_cache,
    )
    from pd_book_tools.layout.visualize import draw_layout_overlay as _draw

    assert draw_layout_overlay is _draw
    assert clear_detector_cache is _clear_cache
    assert caption_for_figure is _caption
    assert iou is _iou
    assert contains is _contains
    assert horizontal_overlap_ratio is _hor
    assert region_reading_order is _reading_order
