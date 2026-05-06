"""Region-adjacency helpers used by reorg and the illustration extractor.

These are deliberately decoupled from :class:`pd_book_tools.geometry.BoundingBox`
because layout regions live in pixel space and don't participate in
normalize/scale operations. Keeping them here avoids cross-coupling and makes
the helpers easy to reason about.
"""

from typing import Iterable, Optional

from pd_book_tools.layout.types import LayoutRegion, RegionType


def iou(a: LayoutRegion, b: LayoutRegion) -> float:
    """Intersection-over-union for two regions.

    Returns 0.0 if either input is degenerate (zero width or zero height),
    *including the case where two identical zero-area boxes are compared*.

    The mathematical IoU of two identical sets is 1.0 even when they have
    zero measure, but layout code here uses IoU as a "do these rectangles
    meaningfully overlap" signal — and a pair of zero-area boxes carries no
    spatial coverage to overlap on. Treating them as non-overlapping
    (returning 0.0) is the intentional convention for this module so
    deduplication / cluster passes don't collapse degenerate point-regions
    against each other. Callers that need exact-equality detection on
    layout regions should compare coordinates directly, not via IoU.

    The 0.0 floor is enforced two ways: the intersection-area early
    return (`if inter <= 0`) catches mismatched zero-area inputs; the
    union-area early return (`if union <= 0`) catches the matched case,
    where both inputs collapse to the same point/line.
    """
    inter_l = max(a.L, b.L)
    inter_t = max(a.T, b.T)
    inter_r = min(a.R, b.R)
    inter_b = min(a.B, b.B)
    iw = max(0, inter_r - inter_l)
    ih = max(0, inter_b - inter_t)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    union = a.area + b.area - inter
    if union <= 0:
        # Both inputs are zero-area and coincident. By module convention
        # (see docstring) this is not a meaningful overlap signal.
        return 0.0
    return inter / union


def contains(outer: LayoutRegion, inner: LayoutRegion, tol: int = 0) -> bool:
    """``inner`` is fully inside ``outer`` (with optional pixel tolerance)."""
    return (
        outer.L - tol <= inner.L
        and outer.T - tol <= inner.T
        and outer.R + tol >= inner.R
        and outer.B + tol >= inner.B
    )


def horizontal_overlap_ratio(a: LayoutRegion, b: LayoutRegion) -> float:
    """Width of horizontal overlap divided by the smaller of the two widths.

    Used to decide "is this caption directly under that figure" — they should
    share most of their horizontal extent.
    """
    inter_l = max(a.L, b.L)
    inter_r = min(a.R, b.R)
    inter_w = max(0, inter_r - inter_l)
    if inter_w == 0:
        return 0.0
    smaller = min(a.width, b.width)
    if smaller <= 0:
        return 0.0
    return inter_w / smaller


def caption_for_figure(
    figure: LayoutRegion,
    regions: Iterable[LayoutRegion],
    max_gap_px: int = 80,
    min_horizontal_overlap: float = 0.3,
) -> Optional[LayoutRegion]:
    """Return the caption/text region directly below ``figure``, if any.

    Heuristic per the plan's "Caption association distance" question — choose
    the closest region of type :attr:`RegionType.caption` (preferred) or
    :attr:`RegionType.text` (fallback) whose top edge is within ``max_gap_px``
    of the figure's bottom and whose horizontal overlap with the figure is at
    least ``min_horizontal_overlap`` of the smaller width.
    """
    best: Optional[LayoutRegion] = None
    best_gap = max_gap_px + 1
    best_is_caption = False
    for r in regions:
        if r is figure:
            continue
        if r.type not in (RegionType.caption, RegionType.text):
            continue
        gap = r.T - figure.B
        if gap < 0 or gap > max_gap_px:
            continue
        if horizontal_overlap_ratio(figure, r) < min_horizontal_overlap:
            continue
        is_caption = r.type == RegionType.caption
        # Prefer explicit captions over generic text; among same type, prefer
        # the smaller gap.
        if best is None:
            best, best_gap, best_is_caption = r, gap, is_caption
            continue
        if is_caption and not best_is_caption:
            best, best_gap, best_is_caption = r, gap, is_caption
            continue
        if is_caption == best_is_caption and gap < best_gap:
            best, best_gap = r, gap
    return best


def region_reading_order(regions: Iterable[LayoutRegion]) -> list[LayoutRegion]:
    """Stable left-right-top-down sort.

    Sorts primarily by top edge, secondarily by left edge. The plan flags
    multi-column reading order as an open design question — this is a sensible
    default for single-column books and a starting point for the column-aware
    sort to come.
    """
    return sorted(regions, key=lambda r: (r.T, r.L))


__all__ = [
    "caption_for_figure",
    "contains",
    "horizontal_overlap_ratio",
    "iou",
    "region_reading_order",
]
