"""Layout-aware helpers folded into the reorganize_page pipeline.

The integration model is:

  1. **Early** (after :meth:`Page.refine_bounding_boxes`):
     :func:`tag_words_with_layout` annotates every Word with
     ``layout:<region_type>`` tags for each region the word's center falls
     in. From this point on, the rest of the reorg pipeline can treat layout
     as data attached to words — no need to thread a ``layout`` argument
     through every step.

  2. **Drop** (still early): :func:`drop_layout_regions` removes words tagged
     with high-confidence header / footer / footnote / abandoned region
     types so the geometric pipeline sees a cleaner page.

  3. **Late** (after the existing pipeline emits final blocks):
     :func:`bubble_block_roles_from_layout` looks at the dominant
     ``layout:*`` tag inside each top-level block and stamps it onto
     ``block_role_labels``. This is how a block of body text gets its
     ``"page header"`` / ``"caption"`` / ``"section"`` /``"title"`` role
     without the geometric heuristics having to figure it out from scratch.

  4. **Caption association**: :func:`associate_captions` emits a placeholder
     illustration block + caption block per high-confidence figure region.

Layout is treated as a *hint* throughout — low-confidence regions are
ignored and the geometric heuristics remain the safety net. Goal is
monotonic improvement: never let a noisy model prediction make output
worse than current behaviour.
"""

from __future__ import annotations

from collections import Counter
from logging import getLogger
from typing import TYPE_CHECKING, cast

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.geometry.point import Point
from pd_book_tools.layout.geometry import caption_for_figure
from pd_book_tools.layout.types import LayoutRegion, PageLayout, RegionType
from pd_book_tools.ocr.block import (
    Block,
    BlockCategory,
    BlockChildType,
    purge_words_from_blocks,
)
from pd_book_tools.ocr.word import Word

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from pd_book_tools.ocr.page import Page

logger = getLogger(__name__)


# Default minimum confidence for *trusting* a region as authoritative
# enough to act on (drop words, force a role label). Below this, the tag
# is still attached for downstream consumers but reorg ignores it.
DEFAULT_TAG_CONFIDENCE = 0.5
DEFAULT_DROP_CONFIDENCE = 0.7

# Per-type minimum confidence overrides for callers passing a
# ``dict[RegionType, float]`` to ``drop_layout_regions`` /
# ``drop_figure_internal_words``. Tuned on the observation that figures
# are detected confidently (we can trust them at 0.5) while headers
# are the noisiest class (require ≥0.7 before dropping their words).
# Types not listed fall back to ``DEFAULT_DROP_CONFIDENCE``.
DEFAULT_DROP_CONFIDENCE_BY_TYPE: dict[RegionType, float] = {
    RegionType.figure: 0.50,
    RegionType.header: 0.70,
    RegionType.footer: 0.65,
    RegionType.footnote: 0.65,
    RegionType.abandoned: 0.70,
}


def _resolve_confidence_threshold(
    threshold: float | dict[RegionType, float],
    region_type: RegionType,
) -> float:
    """Pick the minimum confidence for ``region_type``.

    Accepts either a single ``float`` (legacy single-bar policy) or a
    ``dict[RegionType, float]`` (per-type policy). For dict input,
    types not present fall back to ``DEFAULT_DROP_CONFIDENCE``.
    """
    if isinstance(threshold, dict):
        return float(threshold.get(region_type, DEFAULT_DROP_CONFIDENCE))
    return float(threshold)


# Prefix used for the ``word_labels`` entries. Kept short to match the
# free-form pattern already used for OCR-confidence / debug labels.
LAYOUT_LABEL_PREFIX = "layout:"

# Map a dominant layout RegionType → the block role label that the
# downstream PGDP serialiser (or any consumer reading
# ``block_role_labels``) will dispatch on.
_REGION_TO_BLOCK_ROLE: dict[RegionType, str] = {
    RegionType.text: "paragraph",
    RegionType.title: "title",
    RegionType.section: "section",
    RegionType.list: "list",
    RegionType.table: "table",
    RegionType.figure: "figure",
    RegionType.decoration: "decoration",
    RegionType.caption: "caption",
    RegionType.header: "page header",
    RegionType.footer: "page footer",
    RegionType.footnote: "footnote",
    RegionType.formula: "formula",
    RegionType.sidenote: "sidenote",
}


# ---------------------------------------------------------------------------
# Coordinate helpers


def _word_bbox_in_layout_frame(
    word: Word, page_w: float, page_h: float, layout_w: float, layout_h: float
) -> tuple[float, float, float, float] | None:
    """Return ``(L, T, R, B)`` for ``word`` in the layout image's pixel frame.

    Handles both normalized and pixel-space word bounding boxes. Falls back
    to ``None`` if the word has no bounding box.
    """
    bbox = cast("BoundingBox | None", word.bounding_box)
    if bbox is None:
        return None
    if bbox.is_normalized:
        return (
            float(bbox.minX) * layout_w,
            float(bbox.minY) * layout_h,
            float(bbox.maxX) * layout_w,
            float(bbox.maxY) * layout_h,
        )
    if (
        page_w > 0
        and page_h > 0
        and (abs(page_w - layout_w) > 1 or abs(page_h - layout_h) > 1)
    ):
        sx = layout_w / page_w
        sy = layout_h / page_h
        return (
            float(bbox.minX) * sx,
            float(bbox.minY) * sy,
            float(bbox.maxX) * sx,
            float(bbox.maxY) * sy,
        )
    return (float(bbox.minX), float(bbox.minY), float(bbox.maxX), float(bbox.maxY))


def _word_center_in_region(
    word: Word,
    region: LayoutRegion,
    page_w: float,
    page_h: float,
    layout_w: float,
    layout_h: float,
) -> bool:
    coords = _word_bbox_in_layout_frame(word, page_w, page_h, layout_w, layout_h)
    if coords is None:
        return False
    L, T, R, B = coords
    cx = (L + R) / 2.0
    cy = (T + B) / 2.0
    return region.contains_point(cx, cy)


def words_inside(
    region: LayoutRegion,
    words: Iterable[Word],
    page_width: float,
    page_height: float,
    layout_width: float,
    layout_height: float,
) -> list[Word]:
    return [
        w
        for w in words
        if _word_center_in_region(
            w, region, page_width, page_height, layout_width, layout_height
        )
    ]


def _resolve_dimensions(page: Page) -> tuple[float, float]:
    w = float(page.width or 0.0)
    h = float(page.height or 0.0)
    if w > 0 and h > 0:
        return w, h
    base_image = page.cv2_numpy_page_image
    if base_image is not None:
        ih = int(cast("int", base_image.shape[0]))
        iw = int(cast("int", base_image.shape[1]))
        return float(iw), float(ih)
    return 0.0, 0.0


# ---------------------------------------------------------------------------
# Word tagging — Step 1 of the integration


def _layout_label(region_type: RegionType) -> str:
    return f"{LAYOUT_LABEL_PREFIX}{region_type.value}"


def tag_words_with_layout(
    page: Page,
    layout: PageLayout | None,
    confidence_threshold: float = DEFAULT_TAG_CONFIDENCE,
) -> int:
    """Annotate each Word's ``word_labels`` with the layout regions it sits in.

    Tag format: ``"layout:<region_type>"`` (e.g. ``"layout:caption"``).
    Words can be inside more than one region (caption nested inside a
    figure column, etc.), in which case multiple tags are added.

    Returns the number of (word, region) pairs tagged. Idempotent — running
    twice with the same layout yields the same tags (duplicates skipped).
    """
    if layout is None or not layout.regions:
        return 0
    page_w, page_h = _resolve_dimensions(page)
    if page_w <= 0 or page_h <= 0:
        logger.debug("tag_words_with_layout: page dims unknown; skipping")
        return 0
    layout_w = float(layout.image_width or page_w)
    layout_h = float(layout.image_height or page_h)

    relevant = [r for r in layout.regions if r.confidence >= confidence_threshold]
    if not relevant:
        return 0

    tagged = 0
    for word in page.words:
        for region in relevant:
            if not _word_center_in_region(
                word, region, page_w, page_h, layout_w, layout_h
            ):
                continue
            label = _layout_label(region.type)
            if label not in word.word_labels:
                word.word_labels.append(label)
                tagged += 1
    return tagged


def word_layout_tags(word: Word) -> list[str]:
    """Return just the ``layout:*`` slice of ``word.word_labels``."""
    return [
        lbl[len(LAYOUT_LABEL_PREFIX) :]
        for lbl in word.word_labels
        if lbl.startswith(LAYOUT_LABEL_PREFIX)
    ]


# ---------------------------------------------------------------------------
# Drop pass — uses the tags now


def _purge_word_from_blocks(blocks: list[Block], targets: set[int]) -> None:
    """R-05: thin module-private alias around ``block.purge_words_from_blocks``.

    Kept so the four in-module call sites read at the original level of
    abstraction; the implementation lives in ``ocr.block`` so the
    geometry pipeline can share it without depending on layout types.
    """
    purge_words_from_blocks(blocks, targets)


def drop_layout_regions(
    page: Page,
    layout: PageLayout | None,
    drop_types: set[RegionType],
    confidence_threshold: float | dict[RegionType, float] = DEFAULT_DROP_CONFIDENCE,
) -> int:
    """Remove words whose centers fall in high-confidence drop-type regions.

    Mutates ``page`` in place; returns the number of words removed. Reads
    high-confidence regions directly from ``layout`` (does NOT depend on
    :func:`tag_words_with_layout` having been called first — although in
    the standard pipeline that's the order).

    ``confidence_threshold`` accepts either a single ``float`` (single
    blanket bar — legacy behaviour) or a ``dict[RegionType, float]`` for
    a per-type policy. With a dict, region types not listed fall back to
    :data:`DEFAULT_DROP_CONFIDENCE`. See
    :data:`DEFAULT_DROP_CONFIDENCE_BY_TYPE` for a sensible default
    per-type policy.
    """
    if not drop_types or layout is None or not layout.regions:
        return 0
    page_w, page_h = _resolve_dimensions(page)
    if page_w <= 0 or page_h <= 0:
        return 0
    layout_w = float(layout.image_width or page_w)
    layout_h = float(layout.image_height or page_h)

    relevant = [
        r
        for r in layout.regions
        if r.type in drop_types
        and r.confidence >= _resolve_confidence_threshold(confidence_threshold, r.type)
    ]
    if not relevant:
        return 0

    targets: set[int] = set()
    for word in page.words:
        for region in relevant:
            if _word_center_in_region(word, region, page_w, page_h, layout_w, layout_h):
                targets.add(id(word))
                break

    if not targets:
        return 0
    _purge_word_from_blocks(page.items, targets)
    page.remove_empty_items()
    page.recompute_bounding_box()
    logger.debug(
        "drop_layout_regions: removed %d words across %d regions",
        len(targets),
        len(relevant),
    )
    return len(targets)


# ---------------------------------------------------------------------------
# Figure-internal-noise drop — a per-line, tag-aware sweep


def _iter_line_blocks(blocks: Iterable[Block]) -> Iterable[Block]:
    """Yield every BlockCategory.LINE block in the tree."""
    for b in blocks:
        if b.child_type == BlockChildType.WORDS:
            yield b
        else:
            yield from _iter_line_blocks(
                [item for item in b.items if isinstance(item, Block)]
            )


def _word_has_only_layout_tag(word: Word, tag: str) -> bool:
    """True if the word carries ``tag`` and no other ``layout:*`` tag.

    A word with both ``layout:figure`` and ``layout:text`` is wrap-around
    body, not figure-internal noise — this returns False. A word with no
    layout tags at all also returns False (we don't drop unknown words).
    """
    layout_tags = [t for t in word.word_labels if t.startswith(LAYOUT_LABEL_PREFIX)]
    if not layout_tags:
        return False
    return layout_tags == [tag]


def drop_figure_internal_words(
    page: Page,
    layout: PageLayout | None,
    confidence_threshold: float | dict[RegionType, float] = DEFAULT_DROP_CONFIDENCE,
) -> int:
    """Drop OCR lines that exist *only* inside a high-confidence figure region.

    This is the safer cousin of ``drop_layout_regions`` for figures: instead
    of deleting every word whose center lands in a figure bbox (which would
    eat body text wrapping around the figure), we only drop a line when
    *every* word in it carries solely the ``layout:figure`` tag — meaning
    the OCR engine produced characters from inside the engraving and the
    model also believed it was a figure with no text overlay there.

    Body text that wraps around a figure is preserved because PP-DocLayout
    emits a separate ``text`` region for the wrap zone, so those words
    carry a ``layout:text`` tag too. Caption words are similarly
    preserved (``layout:caption``).

    Returns the number of words removed. Requires
    :func:`tag_words_with_layout` to have run first; if called without
    tagging, returns 0 because no word has any ``layout:*`` tag.
    """
    if layout is None or not layout.regions:
        return 0
    figure_threshold = _resolve_confidence_threshold(
        confidence_threshold, RegionType.figure
    )
    has_figure = any(
        r.type == RegionType.figure and r.confidence >= figure_threshold
        for r in layout.regions
    )
    if not has_figure:
        return 0

    targets: set[int] = set()
    for line_block in _iter_line_blocks(page.items):
        words = [item for item in line_block.items if isinstance(item, Word)]
        if not words:
            continue
        # Drop only when EVERY word in the line is purely figure-tagged.
        if all(
            _word_has_only_layout_tag(w, _layout_label(RegionType.figure))
            for w in words
        ):
            for w in words:
                targets.add(id(w))

    if not targets:
        return 0
    _purge_word_from_blocks(page.items, targets)
    page.remove_empty_items()
    page.recompute_bounding_box()
    logger.debug("drop_figure_internal_words: removed %d words", len(targets))
    return len(targets)


# ---------------------------------------------------------------------------
# Geometric sidenote detection — a margin-column heuristic


def _percentile(sorted_values: Sequence[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    idx = max(0, min(len(sorted_values) - 1, round(pct * (len(sorted_values) - 1))))
    return float(sorted_values[idx])


def detect_geometric_sidenotes(
    page: Page,
    *,
    min_cluster_words: int = 4,
    min_gap_ratio: float = 0.04,
    max_column_width_ratio: float = 0.22,
    max_height_ratio: float | None = None,
) -> int:
    """Tag words in a left- or right-margin sidenote column with ``layout:sidenote``.

    Used as a fallback when the layout model lumps a marginal column into
    the body's wide ``text`` region (which PP-DocLayout currently does on
    PGDP-style pages with one-or-two-word marginalia). The heuristic is
    conservative — it only tags when there is clear geometric evidence of
    a separate column:

      * The body's right edge (10th-percentile of word right-edges, from
        the right) is the body's effective right margin. A sidenote
        candidate sits **at least** ``min_gap_ratio * page_width`` to the
        right of that edge.
      * The candidate cluster spans a horizontal range no wider than
        ``max_column_width_ratio * page_width`` — a real sidenote is
        narrow, not full-width.
      * The cluster has at least ``min_cluster_words`` words.

    Same logic mirrored on the left side. Returns the number of words
    tagged.

    Optional glyph-size filter (``max_height_ratio``): real sidenotes are
    typically rendered in a smaller font than body text. When this kwarg
    is set (e.g. ``0.8``), a candidate cluster is rejected unless its
    median bbox height is ``<= max_height_ratio * body_median_height``.
    Default ``None`` preserves legacy x-position-only behaviour. Helps
    distinguish a true sidenote column from a narrow body protrusion or
    a hanging-indent line that happens to land in the margin x-range.

    The tag is the same shape model-emitted tags use
    (``layout:sidenote``), so :func:`bubble_block_roles_from_layout`
    promotes the containing block to ``block_role_labels=["sidenote"]``
    automatically.
    """
    word_bboxes: list[tuple[Word, BoundingBox]] = []
    for word in page.words:
        bbox = cast("BoundingBox | None", word.bounding_box)
        if bbox is not None:
            word_bboxes.append((word, bbox))

    if len(word_bboxes) < min_cluster_words * 2:
        return 0

    # Resolve the page's horizontal extent. Word coords might be in pixel
    # or normalized space; treat is_normalized words against [0,1].
    is_norm = word_bboxes[0][1].is_normalized
    if is_norm:
        page_w = 1.0
    else:
        page_w, _ = _resolve_dimensions(page)
        if page_w <= 0:
            page_w = max(float(bbox.maxX) for _, bbox in word_bboxes)

    extents: list[tuple[tuple[float, float, float], Word]] = [
        (
            (
                float(bbox.minX),
                float(bbox.maxX),
                (float(bbox.minX) + float(bbox.maxX)) / 2.0,
            ),
            word,
        )
        for word, bbox in word_bboxes
    ]
    bbox_by_id = {id(word): bbox for word, bbox in word_bboxes}

    rights = sorted(e[1] for e, _ in extents)
    lefts = sorted(e[0] for e, _ in extents)

    # Body right / left edge: the *median* of word right / left edges.
    # Median is robust to a sidenote-column cluster making up 20-30% of
    # words on the page, where percentile-based bounds would be biased.
    body_right = _percentile(rights, 0.50)
    body_left = _percentile(lefts, 0.50)

    gap = max(min_gap_ratio * page_w, 1.0)
    max_col_w = max_column_width_ratio * page_w

    right_candidates: list[Word] = []
    left_candidates: list[Word] = []
    for (_l, _r, cx), w in extents:
        if cx > body_right + gap:
            right_candidates.append(w)
        elif cx < body_left - gap:
            left_candidates.append(w)

    # Body median glyph height — only computed if the caller opted into the
    # glyph-size filter. Uses words *not* in either margin cluster as the
    # body sample so a tall sidenote cluster can't pull the median up.
    body_median_height = 0.0
    if max_height_ratio is not None:
        margin_ids = {id(w) for w in right_candidates} | {
            id(w) for w in left_candidates
        }
        body_heights = sorted(
            float(bbox.maxY) - float(bbox.minY)
            for word, bbox in word_bboxes
            if id(word) not in margin_ids
        )
        if body_heights:
            body_median_height = _percentile(body_heights, 0.50)

    tagged = 0
    for cluster_label, cluster in [
        ("right", right_candidates),
        ("left", left_candidates),
    ]:
        if len(cluster) < min_cluster_words:
            continue
        # Reject if the cluster spans most of the page horizontally — that's
        # not a margin column, that's noise across the whole page.
        cluster_left = min(float(bbox_by_id[id(w)].minX) for w in cluster)
        cluster_right = max(float(bbox_by_id[id(w)].maxX) for w in cluster)
        if (cluster_right - cluster_left) > max_col_w:
            continue
        # Optional glyph-size gate: real sidenotes use a smaller font than
        # the body. Reject the cluster if its median bbox height isn't at
        # least max_height_ratio times shorter than the body median.
        if max_height_ratio is not None and body_median_height > 0:
            cluster_heights = sorted(
                float(bbox_by_id[id(w)].maxY) - float(bbox_by_id[id(w)].minY)
                for w in cluster
            )
            cluster_median_height = _percentile(cluster_heights, 0.50)
            if cluster_median_height > max_height_ratio * body_median_height:
                logger.debug(
                    "detect_geometric_sidenotes: rejecting %s cluster on glyph-size (median=%.1f, body=%.1f, ratio_bar=%.2f)",
                    cluster_label,
                    cluster_median_height,
                    body_median_height,
                    max_height_ratio,
                )
                continue
        for w in cluster:
            label = _layout_label(RegionType.sidenote)
            if label not in w.word_labels:
                w.word_labels.append(label)
                tagged += 1
        logger.debug(
            "detect_geometric_sidenotes: tagged %d %s-margin words",
            len(cluster),
            cluster_label,
        )
    return tagged


# ---------------------------------------------------------------------------
# Block-role bubble-up — the late step


def _all_words_in_block(block: Block) -> list[Word]:
    if block.child_type == BlockChildType.WORDS:
        return [item for item in block.items if isinstance(item, Word)]
    out: list[Word] = []
    for child in block.items:
        if isinstance(child, Block):
            out.extend(_all_words_in_block(child))
    return out


def _dominant_layout_info(
    words: Sequence[Word],
) -> tuple[RegionType, int, int] | None:
    """Return ``(winning_type, winner_count, pool_size)`` or ``None``.

    The pool excludes ``RegionType.text`` whenever any non-text tag is
    present — captions and headings are typically nested inside a parent
    ``text`` region and should not be drowned out by it. With no non-text
    tags, the full pool (including ``text``) is used.
    """
    if not words:
        return None
    counter: Counter[str] = Counter()
    for w in words:
        for tag in word_layout_tags(w):
            counter[tag] += 1
    if not counter:
        return None
    non_text = {k: v for k, v in counter.items() if k != RegionType.text.value}
    if non_text:
        pool = sum(non_text.values())
        winner_tag, winner_count = max(non_text.items(), key=lambda kv: kv[1])
    else:
        pool = sum(counter.values())
        winner_tag, winner_count = max(counter.items(), key=lambda kv: kv[1])
    try:
        return RegionType(winner_tag), winner_count, pool
    except ValueError:
        return None


# Layout-derived block roles that should NOT be overwritten by a later
# bubble-up pass. Includes the role names emitted by associate_captions
# (``illustration`` for figures, ``decoration`` for seals).
_LAYOUT_DERIVED_BLOCK_ROLES: frozenset[str] = frozenset(
    set(_REGION_TO_BLOCK_ROLE.values()) | {"illustration"}
) - {"paragraph"}


def bubble_block_roles_from_layout(
    blocks: Iterable[Block],
    dominance: float = 0.5,
) -> int:
    """Stamp ``block_role_labels`` based on the dominant layout tag inside.

    For each top-level block, count the ``layout:*`` tags across its words
    and — when one type accounts for at least ``dominance`` of all tagged
    words — set the corresponding block role label (idempotent; existing
    labels are kept unless they conflict).

    Returns the number of blocks whose role was updated.
    """
    updated = 0
    for block in blocks:
        # Don't overwrite a layout-derived role someone already set
        # (e.g. associate_captions stamps "illustration" / "caption").
        if any(r in _LAYOUT_DERIVED_BLOCK_ROLES for r in block.block_role_labels):
            continue

        words = _all_words_in_block(block)
        if not words:
            continue
        info = _dominant_layout_info(words)
        if info is None:
            continue
        dom_type, winner_count, pool_size = info
        if winner_count / max(pool_size, 1) < dominance:
            continue

        role = _REGION_TO_BLOCK_ROLE.get(dom_type)
        if not role or role == "paragraph":
            # Body text is the default — don't pollute labels with it.
            continue
        if role not in block.block_role_labels:
            block.block_role_labels.append(role)
            updated += 1
    return updated


# ---------------------------------------------------------------------------
# Sidenote reading-order routing — left → top, right → bottom


# Sentinel sort-order values pushing sidenote blocks to the very top / very
# bottom of the page, well outside the body's [0..N] range and the
# illustration/caption sort-offset (1_000_000+) used by associate_captions.
_LEFT_SIDENOTE_SORT_ORDER = -1_000_000
_RIGHT_SIDENOTE_SORT_ORDER = 2_000_000


def _block_x_center(block: Block, fallback: float) -> float:
    bb = block.bounding_box
    if bb is None:
        return fallback
    return (float(bb.minX) + float(bb.maxX)) / 2.0


def route_sidenote_reading_order(page: Page) -> int:
    """Stamp ``override_page_sort_order`` on sidenote blocks so left-margin
    notes emit before the body and right-margin notes emit after.

    Determines left vs right by comparing each sidenote block's bounding-box
    center to the page's mid-line. Blocks without a ``"sidenote"`` role
    label are untouched. Returns the number of blocks routed.

    Run after :func:`bubble_block_roles_from_layout` so the sidenote role
    is already attached.
    """
    page_w, _ = _resolve_dimensions(page)
    if page_w <= 0:
        # Try to recover from the actual block bboxes.
        all_xs: list[float] = []
        for b in page.items:
            if b.bounding_box is not None:
                all_xs.append(float(b.bounding_box.minX))
                all_xs.append(float(b.bounding_box.maxX))
        if not all_xs:
            return 0
        page_w = max(all_xs)
    midline = page_w / 2.0

    routed = 0
    # Build separate index counters so multiple left / right sidenotes
    # preserve their top-to-bottom order (by bbox top edge).
    left_blocks: list[Block] = []
    right_blocks: list[Block] = []
    for block in page.items:
        if "sidenote" not in block.block_role_labels:
            continue
        cx = _block_x_center(block, fallback=midline)
        if cx < midline:
            left_blocks.append(block)
        else:
            right_blocks.append(block)

    def _top_of(b: Block) -> float:
        return float(b.bounding_box.minY) if b.bounding_box else 0.0

    for i, b in enumerate(sorted(left_blocks, key=_top_of)):
        b.override_page_sort_order = _LEFT_SIDENOTE_SORT_ORDER + i
        routed += 1
    for i, b in enumerate(sorted(right_blocks, key=_top_of)):
        b.override_page_sort_order = _RIGHT_SIDENOTE_SORT_ORDER + i
        routed += 1

    if routed:
        page.items = page.items
    return routed


# ---------------------------------------------------------------------------
# Caption association — placeholder illustration block + caption block


def emit_caption_block(
    words: Sequence[Word],
    region_type: RegionType = RegionType.figure,
) -> Block | None:
    _ = region_type
    if not words:
        return None
    line = Block(
        items=list(words),
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
        line_role_labels=["caption line"],
    )
    return Block(
        items=[line],
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.PARAGRAPH,
        block_role_labels=["caption"],
    )


def _empty_illustration_block(
    region: LayoutRegion,
    page_w: float,
    page_h: float,
    layout_w: float,
    layout_h: float,
    is_normalized: bool,
) -> Block:
    role = "decoration" if region.type == RegionType.decoration else "illustration"
    if is_normalized:
        l = region.L / layout_w
        t = region.T / layout_h
        r = region.R / layout_w
        b = region.B / layout_h
    else:
        sx = page_w / layout_w if page_w > 0 else 1.0
        sy = page_h / layout_h if page_h > 0 else 1.0
        l = region.L * sx
        t = region.T * sy
        r = region.R * sx
        b = region.B * sy
    bbox = BoundingBox(
        top_left=Point(l, t, is_normalized=is_normalized),
        bottom_right=Point(r, b, is_normalized=is_normalized),
        is_normalized=is_normalized,
    )
    return Block(
        items=[],
        bounding_box=bbox,
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.BLOCK,
        block_role_labels=[role],
    )


def associate_captions(
    page: Page,
    layout: PageLayout | None,
    confidence_threshold: float = 0.5,
    max_gap_px: int = 80,
    emit_placeholders: bool = True,
) -> int:
    """Attach caption blocks to figure / decoration / table regions.

    When ``emit_placeholders`` is ``True`` (default), each high-confidence
    figure / decoration / table region also emits a geometry-only
    placeholder ``Block`` tagged ``illustration`` (or ``decoration``) so
    PGDP-bound consumers can serialise it as ``[Illustration: ...]``.
    Set ``emit_placeholders=False`` to skip that emission — useful for
    plain-text consumers (e.g. ``pd-ocr-cli``'s ``.txt`` output) that
    have no rendering for an empty illustration block. Caption *words*
    are still relocated into a new caption-roled block in either mode,
    so opting out never silently drops OCR words.
    """
    if layout is None or not layout.regions:
        return 0
    page_w, page_h = _resolve_dimensions(page)
    if page_w <= 0 or page_h <= 0:
        return 0
    layout_w = float(layout.image_width or page_w)
    layout_h = float(layout.image_height or page_h)
    is_normalized = page.is_content_normalized

    illustration_types = {
        RegionType.figure,
        RegionType.decoration,
        RegionType.table,
    }

    plan: list[tuple[LayoutRegion, list[Word]]] = []
    for region in layout.regions:
        if region.type not in illustration_types:
            continue
        if region.confidence < confidence_threshold:
            continue
        caption_region = caption_for_figure(
            region, layout.regions, max_gap_px=max_gap_px
        )
        caption_words: list[Word] = []
        if caption_region is not None:
            caption_words = words_inside(
                caption_region, page.words, page_w, page_h, layout_w, layout_h
            )
        plan.append((region, caption_words))

    if not plan:
        return 0

    target_ids: set[int] = set()
    for _, words in plan:
        for w in words:
            target_ids.add(id(w))
    if target_ids:
        _purge_word_from_blocks(page.items, target_ids)
        page.remove_empty_items()

    captions_attached = 0
    sort_offset = 1_000_000
    for region, caption_words in plan:
        if emit_placeholders:
            illustration = _empty_illustration_block(
                region, page_w, page_h, layout_w, layout_h, is_normalized
            )
            illustration.override_page_sort_order = sort_offset
            sort_offset += 1
            page.add_item(illustration)
        if not caption_words:
            continue
        caption_block = emit_caption_block(caption_words, region_type=region.type)
        if caption_block is None:
            continue
        caption_block.override_page_sort_order = sort_offset
        sort_offset += 1
        page.add_item(caption_block)
        captions_attached += 1

    page.items = page.items
    page.recompute_bounding_box()
    return captions_attached


__all__ = [
    "DEFAULT_DROP_CONFIDENCE",
    "DEFAULT_DROP_CONFIDENCE_BY_TYPE",
    "DEFAULT_TAG_CONFIDENCE",
    "LAYOUT_LABEL_PREFIX",
    "associate_captions",
    "bubble_block_roles_from_layout",
    "detect_geometric_sidenotes",
    "drop_figure_internal_words",
    "drop_layout_regions",
    "emit_caption_block",
    "route_sidenote_reading_order",
    "tag_words_with_layout",
    "word_layout_tags",
    "words_inside",
]
