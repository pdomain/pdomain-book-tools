"""Pipeline-step implementations for ``Page.reorganize_page``.

This module owns the heavy lifting of turning OCR output into reading-order
blocks: header/footer band detection, row-block grouping, column / floated-
figure expansion, paragraph splitting, special-block classification, and the
per-step debug PNG writers used by the layout regression test.

See ``docs/architecture/reorganize_pipeline.md`` for the per-step heuristic
specs, debug-PNG semantics, the rationale behind every threshold, and the
fixture-driven decisions that shaped the pipeline.
"""

import itertools
import os
import pathlib
from dataclasses import dataclass
from logging import getLogger
from typing import List, Tuple

from cv2 import FONT_HERSHEY_SIMPLEX as cv2_FONT_HERSHEY_SIMPLEX
from cv2 import addWeighted as cv2_addWeighted
from cv2 import imwrite as cv2_imwrite
from cv2 import putText as cv2_putText
from cv2 import rectangle as cv2_rectangle
from numpy import mean as np_mean
from numpy import median as np_median
from numpy import std as np_std

from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pd_book_tools.ocr.word import Word

logger = getLogger(__name__)


@dataclass(frozen=True)
class PageMetrics:
    """Per-page geometric statistics used by every pipeline step.

    Computed once at the start of ``reorganize_page`` so individual steps can
    use consistent, robust thresholds without re-deriving them.
    """

    coord_w: float
    coord_h: float
    median_word_w: float
    median_word_h: float
    median_line_h: float
    top_word_min_y: float
    bottom_word_max_y: float
    word_count: int


def _coord_dims_from_words(
    words: List[Word], page_w: float, page_h: float
) -> Tuple[float, float]:
    """Return the coordinate-domain (normalized vs pixel) page width/height.

    OCR pipelines may emit either normalized [0, 1] boxes or pixel boxes while
    keeping ``page.width``/``page.height`` in pixels. We pick the matching unit
    by inspecting the largest observed coordinate.
    """
    valid = [w for w in words if w.bounding_box]
    if not valid:
        return float(page_w or 1.0), float(page_h or 1.0)
    bbox_max_x = max(w.bounding_box.maxX for w in valid)
    bbox_max_y = max(w.bounding_box.maxY for w in valid)
    coord_w = 1.0 if bbox_max_x <= 2.0 else float(page_w or bbox_max_x)
    coord_h = 1.0 if bbox_max_y <= 2.0 else float(page_h or bbox_max_y)
    return coord_w, coord_h


def compute_page_metrics(page) -> PageMetrics:
    """Compute robust per-page geometric statistics."""
    words = [w for w in page.words if w.bounding_box]
    page_w, page_h = page.resolved_dimensions
    coord_w, coord_h = _coord_dims_from_words(words, page_w, page_h)

    if not words:
        return PageMetrics(
            coord_w=coord_w,
            coord_h=coord_h,
            median_word_w=0.02 * coord_w,
            median_word_h=0.02 * coord_h,
            median_line_h=0.02 * coord_h,
            top_word_min_y=0.0,
            bottom_word_max_y=coord_h,
            word_count=0,
        )

    median_word_h = float(np_median([w.bounding_box.height for w in words]))
    median_word_w = float(np_median([w.bounding_box.width for w in words]))
    lines = [l for l in page.lines if l.bounding_box]
    median_line_h = float(
        np_median([l.bounding_box.height for l in lines] or [median_word_h])
    )

    top_word_min_y = min(w.bounding_box.minY for w in words)
    bottom_word_max_y = max(w.bounding_box.maxY for w in words)

    return PageMetrics(
        coord_w=coord_w,
        coord_h=coord_h,
        median_word_w=median_word_w,
        median_word_h=median_word_h,
        median_line_h=median_line_h,
        top_word_min_y=top_word_min_y,
        bottom_word_max_y=bottom_word_max_y,
        word_count=len(words),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline Step E — page header / page footer band extraction
# ─────────────────────────────────────────────────────────────────────────────
#
# Many printed book pages have a running header (chapter title or section name,
# usually centered) and a page number on the same baseline. Some pages put the
# page number on the left and the header on the right, or vice-versa. The
# horizontal gap between them can be many word-widths wide, which defeats
# generic word-clustering thresholds tuned for body text.
#
# This step uses pure geometry: any line whose bounding box sits inside a thin
# band at the very top of the OCR content (and that band is followed by a
# clear vertical gap) is part of the page header. The same logic, mirrored,
# applies to the footer band.


def extract_top_header_lines(
    lines: List[Block],
    metrics: PageMetrics,
    *,
    band_factor: float = 1.5,
    near_top_factor: float = 0.12,
    min_gap_factor: float = 0.7,
) -> Tuple[List[Block], List[Block]]:
    """Peel the topmost band of lines off as page-header lines.

    Returns ``(header_lines, body_lines)`` preserving original ordering inside
    the body partition. Returns ``([], lines)`` when no clear header band can
    be identified.

    A line qualifies as a page header when:

    1. The topmost line's ``minY`` is within ``near_top_factor * coord_h`` of
       the top of the page (body text is generally at least one full margin
       below this threshold).
    2. The line's bbox fits inside a band of height ``band_factor *
       median_word_h`` starting at the topmost line's ``minY``.
    3. The vertical gap from the band's bottom to the next non-header line is
       at least ``min_gap_factor * median_word_h`` — confirming a *visible*
       blank line separates the header from the body.
    """
    valid = [l for l in lines if l.bounding_box]
    if len(valid) < 1:
        return [], list(lines)

    valid_sorted = sorted(valid, key=lambda l: l.bounding_box.minY)
    top_min_y = valid_sorted[0].bounding_box.minY
    if top_min_y > near_top_factor * metrics.coord_h:
        return [], list(lines)

    band_bottom = top_min_y + band_factor * metrics.median_word_h
    slack = 0.5 * metrics.median_word_h

    header_lines = [
        l
        for l in valid_sorted
        if l.bounding_box.minY <= band_bottom
        and l.bounding_box.maxY <= band_bottom + slack
    ]
    if not header_lines:
        return [], list(lines)

    header_ids = {id(l) for l in header_lines}
    remaining = [l for l in valid_sorted if id(l) not in header_ids]
    if remaining:
        header_max_y = max(l.bounding_box.maxY for l in header_lines)
        next_min_y = min(l.bounding_box.minY for l in remaining)
        gap = next_min_y - header_max_y
        if gap < min_gap_factor * metrics.median_word_h:
            return [], list(lines)

    body_lines = [l for l in lines if id(l) not in header_ids]
    return header_lines, body_lines


def extract_bottom_footer_lines(
    lines: List[Block],
    metrics: PageMetrics,
    *,
    band_factor: float = 1.5,
    near_bottom_factor: float = 0.12,
    min_gap_factor: float = 0.7,
) -> Tuple[List[Block], List[Block]]:
    """Peel the bottommost band of lines off as page-footer lines.

    Mirror of :func:`extract_top_header_lines`. ``near_bottom_factor`` is the
    distance from the bottom of the page that the bottommost line must lie
    within.
    """
    valid = [l for l in lines if l.bounding_box]
    if len(valid) < 1:
        return [], list(lines)

    valid_sorted = sorted(valid, key=lambda l: l.bounding_box.maxY, reverse=True)
    bottom_max_y = valid_sorted[0].bounding_box.maxY
    if bottom_max_y < (1.0 - near_bottom_factor) * metrics.coord_h:
        return [], list(lines)

    band_top = bottom_max_y - band_factor * metrics.median_word_h
    slack = 0.5 * metrics.median_word_h

    footer_lines = [
        l
        for l in valid_sorted
        if l.bounding_box.maxY >= band_top and l.bounding_box.minY >= band_top - slack
    ]
    if not footer_lines:
        return [], list(lines)

    footer_ids = {id(l) for l in footer_lines}
    remaining = [l for l in valid_sorted if id(l) not in footer_ids]
    if remaining:
        footer_min_y = min(l.bounding_box.minY for l in footer_lines)
        prev_max_y = max(l.bounding_box.maxY for l in remaining)
        gap = footer_min_y - prev_max_y
        if gap < min_gap_factor * metrics.median_word_h:
            return [], list(lines)

    body_lines = [l for l in lines if id(l) not in footer_ids]
    return footer_lines, body_lines


def _build_band_block(
    band_lines: List[Block],
    *,
    role: str,
    position: str,
) -> Block | None:
    """Collapse a list of band lines into a single page-header/footer block.

    All words across the band are sorted by ``minX`` and packed into a single
    LINE so the final emitted text is, e.g., ``"EARLY HERBALS 177"`` even when
    OCR placed the heading and page number in separate paragraph siblings.
    """
    if not band_lines:
        return None

    all_words: List[Word] = []
    for line in band_lines:
        all_words.extend(line.words)
    all_words = [w for w in all_words if w.bounding_box]
    if not all_words:
        return None

    all_words.sort(key=lambda w: w.bounding_box.minX)

    new_line = Block(
        items=all_words,
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
        block_role_labels=[role],
        block_position_labels=[position],
    )
    paragraph = Block(
        items=[new_line],
        block_category=BlockCategory.PARAGRAPH,
        block_role_labels=[role],
        block_position_labels=[position],
    )
    outer = Block(
        items=[paragraph],
        block_category=BlockCategory.BLOCK,
        block_role_labels=[role],
        block_position_labels=[position],
    )
    return outer


def build_page_header_block(header_lines: List[Block]) -> Block | None:
    return _build_band_block(header_lines, role="page header", position="top")


def build_page_footer_block(footer_lines: List[Block]) -> Block | None:
    return _build_band_block(footer_lines, role="page footer", position="bottom")


# Pipeline Step L — wrap a row block's lines in a paragraph + outer block with
# the appropriate role and position labels.
_SPECIAL_BLOCK_LABELS = {
    "page header": ("page header", "top"),
    "page footer": ("page footer", "bottom"),
    "sidenote left": ("sidenote", "margin left"),
    "sidenote right": ("sidenote", "margin right"),
}


def emit_step_h_debug(
    page,
    debug_sections: List[tuple],
    debug_squeezed_lines: List[str],
    step_h_decisions: List[dict],
) -> None:
    """Append the Step H summary section (and its overlay PNG) to debug_sections."""
    if not layout_debug_enabled():
        return
    debug_sections.append(
        (
            "Step 2",
            debug_squeezed_lines
            or [
                "No squeezed side-flow candidates found (or all were single-line/ignored)."
            ],
        )
    )
    step_h_summary = ["Step H: column / float decisions per row block"]
    for entry in step_h_decisions:
        step_h_summary.append(
            f"  RB{entry['row_idx']:02d}: kind={entry['kind']} "
            f"left={len(entry.get('left', []))} "
            f"right={len(entry.get('right', []))} "
            f"spanning={len(entry.get('spanning', []))}"
        )
    png_h = write_step_h_debug_overlay_png(page, step_h_decisions)
    if png_h is not None:
        step_h_summary.append(f"Overlay PNG: {png_h}")
    debug_sections.append(("Step H", step_h_summary))


def emit_step_k_debug(
    page,
    debug_sections: List[tuple],
    final_blocks: List[Block],
) -> None:
    """Append the Step K (paragraph splits) overlay to debug_sections."""
    if not layout_debug_enabled():
        return
    paragraph_count = sum(len(b.items) for b in final_blocks)
    step_k_summary = [
        "Step K: paragraph splits within body blocks",
        f"Total paragraphs (across all blocks): {paragraph_count}",
    ]
    png_k = write_step_k_debug_overlay_png(page, final_blocks)
    if png_k is not None:
        step_k_summary.append(f"Overlay PNG: {png_k}")
    debug_sections.append(("Step K", step_k_summary))


def emit_step_l_debug(
    page,
    debug_sections: List[tuple],
    final_blocks: List[Block],
) -> None:
    """Append the Step L summary section (and its overlay PNG) to debug_sections."""
    if not layout_debug_enabled():
        return
    step_l_summary = ["Step L: final classified blocks (reading order)"]
    for idx, block in enumerate(final_blocks, start=1):
        roles = block.block_role_labels or []
        role = roles[0] if roles else "paragraph"
        step_l_summary.append(f"  B{idx:02d}: role={role} lines={len(block.lines)}")
    png_l = write_step_l_debug_overlay_png(page, final_blocks)
    if png_l is not None:
        step_l_summary.append(f"Overlay PNG: {png_l}")
    debug_sections.append(("Step L", step_l_summary))


def _meaningful_words(words: List[Word]) -> List[Word]:
    """Filter to words with non-empty text and a bounding box.

    The pipeline intentionally discards empty-text artifact words (e.g. an
    OCR'd dot-stem with ``text=""``); those should not show up as "dropped"
    in the validator since their loss is by design.
    """
    return [w for w in words if w.bounding_box and (w.text or "").strip()]


def collect_word_signatures(
    words: List[Word],
) -> List[tuple[str, float, float, float, float]]:
    """Return a sorted list of (text, minX, minY, maxX, maxY) for every word.

    Used by ``validate_word_preservation`` to compare a page's word set
    before vs after the reorganize pipeline. Bounding-box coordinates are
    rounded to 4 decimal places so float equality is robust.

    Empty-text and bbox-less words are filtered via :func:`_meaningful_words`
    — those are routinely dropped by intent and shouldn't trigger validator
    warnings.
    """
    sigs: List[tuple[str, float, float, float, float]] = []
    for w in _meaningful_words(words):
        bb = w.bounding_box
        sigs.append(
            (
                (w.text or ""),
                round(float(bb.minX), 4),
                round(float(bb.minY), 4),
                round(float(bb.maxX), 4),
                round(float(bb.maxY), 4),
            )
        )
    sigs.sort()
    return sigs


def validate_word_preservation(
    pre_words: List[Word],
    post_words: List[Word],
) -> List[str]:
    """Report words present in ``pre_words`` but missing from ``post_words``.

    The reorganize pipeline must never *drop* OCR words — it may move them
    between blocks, merge OCR-fragmented lines, or reclassify them, but the
    raw word multiset must round-trip. This helper diffs the two word sets by
    (text, bbox) signature and returns a list of human-readable error lines
    describing any drops. An empty list means the post set is a superset of
    the pre set (extra words allowed; missing words are not).

    Caller is expected to log the messages and either fail loudly or continue
    with the post set, depending on policy.
    """
    pre_sigs = collect_word_signatures(pre_words)
    post_sig_set = set(collect_word_signatures(post_words))
    errors: List[str] = []
    for sig in pre_sigs:
        if sig not in post_sig_set:
            text, x0, y0, x1, y1 = sig
            errors.append(
                f"reorganize dropped word: text={text!r} bbox=({x0:.4f},{y0:.4f})-({x1:.4f},{y1:.4f})"
            )
    return errors


def find_dropped_words(
    pre_words: List[Word],
    post_words: List[Word],
) -> List[Word]:
    """Return ``Word`` objects that appear in ``pre_words`` but not in
    ``post_words`` (compared by text + bbox signature).

    Sister to :func:`validate_word_preservation` — same diff, but returns the
    actual ``Word`` instances so callers can splice them back into the output.
    """
    post_sig_set = set(collect_word_signatures(post_words))
    dropped: List[Word] = []
    for w in _meaningful_words(pre_words):
        bb = w.bounding_box
        sig = (
            (w.text or ""),
            round(float(bb.minX), 4),
            round(float(bb.minY), 4),
            round(float(bb.maxX), 4),
            round(float(bb.maxY), 4),
        )
        if sig not in post_sig_set:
            dropped.append(w)
    return dropped


def reorganize_strict_mode_enabled() -> bool:
    """Return True when ``PD_OCR_REORGANIZE_STRICT`` is set to a truthy value.

    Strict mode flips the recovery behaviour: instead of re-adding dropped
    words to the page and warning, ``Page.reorganize_page`` raises a
    ``ReorganizeDroppedWordsError``. Useful for CI / tests so any future
    pipeline change that drops a word fails loudly rather than silently
    self-healing.
    """
    return os.environ.get("PD_OCR_REORGANIZE_STRICT", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


class ReorganizeDroppedWordsError(RuntimeError):
    """Raised in strict mode when reorganize_page drops one or more words."""

    def __init__(self, dropped: List[Word], errors: List[str]):
        super().__init__(
            f"reorganize_page dropped {len(dropped)} word(s); "
            f"first: {errors[0] if errors else '(none)'}"
        )
        self.dropped = dropped
        self.errors = errors


def build_recovered_words_block(dropped: List[Word]) -> "Block | None":
    """Wrap dropped-but-rescued words in a tagged BLOCK so they survive in
    the final ``page.text`` output.

    Each dropped word becomes a single-word LINE so its original geometry is
    preserved in the tree. Lines are sorted by (Y, X). The wrapping BLOCK
    carries ``block_role_labels=["recovered"]`` so consumers can flag /
    inspect / strip these post-hoc.
    """
    valid = [w for w in dropped if w.bounding_box]
    if not valid:
        return None
    valid.sort(key=lambda w: (w.bounding_box.minY, w.bounding_box.minX))
    line_blocks: List[Block] = []
    for word in valid:
        line_blocks.append(
            Block(
                items=[word],
                child_type=BlockChildType.WORDS,
                block_category=BlockCategory.LINE,
                block_role_labels=["recovered"],
            )
        )
    paragraph = Block(
        items=line_blocks,
        block_category=BlockCategory.PARAGRAPH,
        block_role_labels=["recovered"],
    )
    return Block(
        items=[paragraph],
        block_category=BlockCategory.BLOCK,
        block_role_labels=["recovered"],
    )


def _format_big_warning(banner: str, lines: List[str]) -> str:
    rule = "=" * max(60, len(banner) + 4)
    body = "\n".join(f"  {line}" for line in lines)
    return f"\n{rule}\n  {banner}\n{rule}\n{body}\n{rule}\n"


def reconcile_dropped_words(
    page,
    pre_words: List[Word],
    final_blocks: List[Block],
) -> List[Block]:
    """Detect words dropped by the pipeline and re-attach them.

    Strategy:

    1. Diff ``pre_words`` against the words currently reachable from
       ``final_blocks``.
    2. If nothing is missing, return ``final_blocks`` unchanged.
    3. Otherwise:
       * If ``PD_OCR_REORGANIZE_STRICT`` is set, raise
         :class:`ReorganizeDroppedWordsError` so the failure is loud. Tests
         and CI should set this env var.
       * Otherwise, log a big stderr warning naming every dropped word and
         append a ``block_role_labels=["recovered"]`` block to
         ``final_blocks`` containing them. The recovered block sorts to the
         end via ``override_page_sort_order`` so it doesn't interleave with
         the rest of the reading order — its primary purpose is to keep the
         word multiset round-tripping while making the loss obvious.
    """
    import sys  # local import: avoids polluting module top-level

    post_words = [
        w
        for outer in final_blocks
        for paragraph in outer.items
        for line in paragraph.items
        for w in (line.words if hasattr(line, "words") else [])
    ]
    errors = validate_word_preservation(pre_words, post_words)
    if not errors:
        return final_blocks

    dropped = find_dropped_words(pre_words, post_words)
    if reorganize_strict_mode_enabled():
        raise ReorganizeDroppedWordsError(dropped, errors)

    page_label = (
        getattr(page, "name", None) or f"page-{getattr(page, 'page_index', 0) + 1}"
    )
    banner = f"WARNING: reorganize dropped {len(dropped)} word(s) on {page_label}; recovering."
    sys.stderr.write(
        _format_big_warning(
            banner,
            errors[:20]
            + ([f"... ({len(errors) - 20} more)"] if len(errors) > 20 else []),
        )
    )
    sys.stderr.flush()

    recovered = build_recovered_words_block(dropped)
    if recovered is None:
        return final_blocks
    return list(final_blocks) + [recovered]


def assemble_final_blocks(
    page_header_block: Block | None,
    body_blocks: List[Block],
    page_footer_block: Block | None,
) -> List[Block]:
    """Pipeline assembly — weave header/footer bands around body blocks and
    stamp ``override_page_sort_order`` so re-sorts keep the order stable.
    """
    final_blocks: List[Block] = []
    if page_header_block is not None:
        final_blocks.append(page_header_block)
    final_blocks.extend(body_blocks)
    if page_footer_block is not None:
        final_blocks.append(page_footer_block)
    for block_idx, block in enumerate(final_blocks):
        block.override_page_sort_order = block_idx
    return final_blocks


def wrap_special_role_block(lines: List[Block], block_type: str) -> Block:
    """Wrap classified lines in PARAGRAPH+BLOCK with role/position labels.

    Replaces repetitive boilerplate for the page-header, page-footer,
    sidenote-left, sidenote-right, poetry and blockquote special types.
    """
    labels = _SPECIAL_BLOCK_LABELS.get(block_type)
    if labels is not None:
        role, position = labels
        position_labels = [position]
    else:
        # poetry / blockquote / any other named role: no position metadata
        role = block_type
        position_labels = None

    paragraph = Block(
        items=lines,
        block_category=BlockCategory.PARAGRAPH,
        block_role_labels=[role],
        block_position_labels=position_labels,
    )
    outer = Block(
        items=[paragraph],
        block_category=BlockCategory.BLOCK,
        block_role_labels=[role],
        block_position_labels=position_labels,
    )
    return outer


@dataclass(frozen=True)
class _LooseBBox:
    """Tiny bbox-like adapter for ad-hoc rectangles passed to ``_bbox_to_px_rect``.

    The real ``BoundingBox`` carries far more metadata than the projection
    helper needs — only minX/minY/maxX/maxY plus width/height are used. This
    adapter keeps the helper's contract narrow.
    """

    minX: float
    minY: float
    maxX: float
    maxY: float

    @property
    def width(self) -> float:
        return self.maxX - self.minX

    @property
    def height(self) -> float:
        return self.maxY - self.minY


def _bbox_to_px_rect(bb, image_w: int, image_h: int):
    """Project a bounding box (normalized or pixel) onto an image grid."""
    if bb is None:
        return None
    if bb.width < 1.0 or bb.height < 1.0:
        min_x = int(bb.minX * image_w)
        max_x = int(bb.maxX * image_w)
        min_y = int(bb.minY * image_h)
        max_y = int(bb.maxY * image_h)
    else:
        min_x = int(bb.minX)
        max_x = int(bb.maxX)
        min_y = int(bb.minY)
        max_y = int(bb.maxY)
    min_x = max(0, min(min_x, image_w - 1))
    max_x = max(0, min(max_x, image_w - 1))
    min_y = max(0, min(min_y, image_h - 1))
    max_y = max(0, min(max_y, image_h - 1))
    if max_x <= min_x or max_y <= min_y:
        return None
    return min_x, min_y, max_x, max_y


# ─────────────────────────────────────────────────────────────────────────────
# Per-step debug PNG writers — render each pipeline stage's output as an
# overlay on the page image. All wrap _bbox_to_px_rect for projection.
# ─────────────────────────────────────────────────────────────────────────────


def write_step_e_debug_overlay_png(
    page,
    header_lines: List[Block],
    footer_lines: List[Block],
    suffix: str = "stepE",
) -> "pathlib.Path | None":
    """Write a debug PNG showing the detected page-header / page-footer bands.

    Header lines are framed in orange; footer lines in purple. Other detected
    lines are framed in light gray so the band selection is visually obvious.
    """
    base_image = page.cv2_numpy_page_image
    if base_image is None:
        return None

    overlay = base_image.copy()
    image_h, image_w = overlay.shape[:2]
    header_ids = {id(l) for l in header_lines}
    footer_ids = {id(l) for l in footer_lines}

    for line in page.lines:
        rect = _bbox_to_px_rect(line.bounding_box, image_w, image_h)
        if rect is None:
            continue
        x0, y0, x1, y1 = rect
        if id(line) in header_ids:
            color = (0, 140, 255)  # orange (BGR)
            label = "HEADER"
        elif id(line) in footer_ids:
            color = (180, 60, 180)  # purple (BGR)
            label = "FOOTER"
        else:
            color = (160, 160, 160)
            label = ""
        cv2_rectangle(overlay, (x0, y0), (x1, y1), color, 2)
        if label:
            cv2_putText(
                overlay,
                label,
                (x0 + 4, max(12, y0 - 4)),
                cv2_FONT_HERSHEY_SIMPLEX,
                0.45,
                color,
                1,
            )

    debug_txt_path = layout_debug_output_path(page)
    png_path = debug_txt_path.with_name(debug_txt_path.stem + f".{suffix}.png")
    cv2_imwrite(str(png_path), overlay)
    return png_path


def write_step_row_blocks_debug_overlay_png(
    page,
    row_blocks_block,
    suffix: str,
) -> "pathlib.Path | None":
    """Write a debug PNG framing each row block in a distinct color.

    Row blocks are the output of vertical region grouping (Step F/G). Each
    block gets a unique color and a numeric label showing reading order.
    """
    base_image = page.cv2_numpy_page_image
    if base_image is None or row_blocks_block is None:
        return None

    overlay = base_image.copy()
    image_h, image_w = overlay.shape[:2]

    palette = [
        (40, 200, 40),
        (40, 120, 220),
        (220, 40, 200),
        (220, 120, 40),
        (40, 220, 200),
        (220, 200, 40),
    ]

    for idx, rb in enumerate(row_blocks_block.items, start=1):
        rect = _bbox_to_px_rect(rb.bounding_box, image_w, image_h)
        if rect is None:
            continue
        x0, y0, x1, y1 = rect
        color = palette[(idx - 1) % len(palette)]
        cv2_rectangle(overlay, (x0, y0), (x1, y1), color, 2)
        cv2_putText(
            overlay,
            f"RB{idx} ({len(rb.lines)} lines)",
            (x0 + 4, max(14, y0 - 6)),
            cv2_FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
        )

    debug_txt_path = layout_debug_output_path(page)
    png_path = debug_txt_path.with_name(debug_txt_path.stem + f".{suffix}.png")
    cv2_imwrite(str(png_path), overlay)
    return png_path


def write_step_d_debug_overlay_png(
    page,
    pre_split_paragraphs: List[Block],
    post_split_paragraphs: List[Block],
    suffix: str = "stepD",
) -> "pathlib.Path | None":
    """Write a debug PNG showing the result of mixed-content line splitting.

    Lines that already existed before Step D are framed in light gray. Lines
    that came out of Step D's gap-and-height split are framed in red so the
    newly-introduced boundaries jump out.
    """
    base_image = page.cv2_numpy_page_image
    if base_image is None:
        return None

    overlay = base_image.copy()
    image_h, image_w = overlay.shape[:2]

    pre_line_ids = {
        id(line)
        for paragraph in pre_split_paragraphs
        for line in paragraph.items
        if line.block_category == BlockCategory.LINE
    }

    post_lines: List[Block] = []
    for paragraph in post_split_paragraphs:
        for item in paragraph.items:
            if item.block_category == BlockCategory.LINE:
                post_lines.append(item)

    for line in post_lines:
        rect = _bbox_to_px_rect(line.bounding_box, image_w, image_h)
        if rect is None:
            continue
        x0, y0, x1, y1 = rect
        if id(line) in pre_line_ids:
            color = (160, 160, 160)
            thickness = 1
        else:
            color = (40, 40, 220)  # red (BGR)
            thickness = 2
            cv2_putText(
                overlay,
                "SPLIT",
                (x0 + 4, max(12, y0 - 4)),
                cv2_FONT_HERSHEY_SIMPLEX,
                0.45,
                color,
                1,
            )
        cv2_rectangle(overlay, (x0, y0), (x1, y1), color, thickness)

    debug_txt_path = layout_debug_output_path(page)
    png_path = debug_txt_path.with_name(debug_txt_path.stem + f".{suffix}.png")
    cv2_imwrite(str(png_path), overlay)
    return png_path


def write_step_h_debug_overlay_png(
    page,
    row_block_decisions: List[dict],
    suffix: str = "stepH",
) -> "pathlib.Path | None":
    """Write a debug PNG showing column-split decisions per row block.

    Each entry in ``row_block_decisions`` describes one row block:
    ``{"row_idx": int, "kind": str, "left": [Block], "right": [Block],
       "spanning": [Block]}``. ``kind`` is one of ``"single"``, ``"two_column"``,
    ``"mixed_column"``, ``"floated_flow"``, or ``"multi_column"``.

    Lines are colored:
      * left column → green
      * right column → blue
      * spanning / single column → light gray
      * extra columns (multi-column case) → cycled palette
    """
    base_image = page.cv2_numpy_page_image
    if base_image is None or not row_block_decisions:
        return None

    overlay = base_image.copy()
    image_h, image_w = overlay.shape[:2]

    palette = [
        (40, 200, 40),
        (220, 120, 40),
        (40, 120, 220),
        (220, 40, 200),
        (40, 220, 200),
        (220, 200, 40),
    ]

    for entry in row_block_decisions:
        row_idx = entry.get("row_idx", 0)
        kind = entry.get("kind", "single")
        left = entry.get("left", [])
        right = entry.get("right", [])
        spanning = entry.get("spanning", [])
        extra_columns = entry.get("extra_columns", [])

        for line in left:
            rect = _bbox_to_px_rect(line.bounding_box, image_w, image_h)
            if rect is None:
                continue
            x0, y0, x1, y1 = rect
            cv2_rectangle(overlay, (x0, y0), (x1, y1), (40, 200, 40), 2)
        for line in right:
            rect = _bbox_to_px_rect(line.bounding_box, image_w, image_h)
            if rect is None:
                continue
            x0, y0, x1, y1 = rect
            cv2_rectangle(overlay, (x0, y0), (x1, y1), (220, 120, 40), 2)
        for line in spanning:
            rect = _bbox_to_px_rect(line.bounding_box, image_w, image_h)
            if rect is None:
                continue
            x0, y0, x1, y1 = rect
            cv2_rectangle(overlay, (x0, y0), (x1, y1), (160, 160, 160), 1)
        for col_idx, col_lines in enumerate(extra_columns):
            color = palette[(col_idx + 3) % len(palette)]
            for line in col_lines:
                rect = _bbox_to_px_rect(line.bounding_box, image_w, image_h)
                if rect is None:
                    continue
                x0, y0, x1, y1 = rect
                cv2_rectangle(overlay, (x0, y0), (x1, y1), color, 2)

        # Label the row block once at the topmost line.
        all_lines = left + right + spanning
        for cl in extra_columns:
            all_lines.extend(cl)
        if all_lines:
            top_line = min(
                (l for l in all_lines if l.bounding_box),
                key=lambda l: l.bounding_box.minY,
                default=None,
            )
            if top_line is not None:
                rect = _bbox_to_px_rect(top_line.bounding_box, image_w, image_h)
                if rect is not None:
                    x0, y0, _, _ = rect
                    cv2_putText(
                        overlay,
                        f"RB{row_idx}: {kind}",
                        (x0 + 2, max(14, y0 - 6)),
                        cv2_FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (0, 0, 0),
                        2,
                    )

    debug_txt_path = layout_debug_output_path(page)
    png_path = debug_txt_path.with_name(debug_txt_path.stem + f".{suffix}.png")
    cv2_imwrite(str(png_path), overlay)
    return png_path


_FINAL_BLOCK_COLOR = {
    "page header": (0, 140, 255),
    "page footer": (180, 60, 180),
    "sidenote": (60, 180, 220),
    "poetry": (200, 60, 100),
    "blockquote": (200, 100, 60),
    "paragraph": (60, 200, 80),
    "body": (60, 200, 80),
}


def write_step_k_debug_overlay_png(
    page,
    body_paragraph_blocks: List[Block],
    suffix: str = "stepK",
) -> "pathlib.Path | None":
    """Write a debug PNG showing paragraph splits within body blocks.

    Each paragraph inside a body BLOCK is framed in a unique color from a
    rotating palette, and labeled ``P<idx>`` so the paragraph boundaries
    chosen by ``compute_text_paragraph_blocks`` (Step K) are visible.
    Special-role blocks (page header/footer, sidenote, poetry, blockquote)
    are framed in light gray since they are emitted as a single paragraph.
    """
    base_image = page.cv2_numpy_page_image
    if base_image is None or not body_paragraph_blocks:
        return None

    overlay = base_image.copy()
    image_h, image_w = overlay.shape[:2]
    palette = [
        (60, 200, 80),
        (220, 120, 40),
        (40, 120, 220),
        (220, 40, 200),
        (40, 220, 200),
        (220, 200, 40),
    ]

    p_idx = 0
    for outer in body_paragraph_blocks:
        # Outer is BLOCK — its items are PARAGRAPH blocks (or a single PARAGRAPH
        # for special roles wrapped via wrap_special_role_block).
        roles = outer.block_role_labels or []
        is_special = any(
            r in {"page header", "page footer", "sidenote", "poetry", "blockquote"}
            for r in roles
        )
        for paragraph in outer.items:
            rect = _bbox_to_px_rect(paragraph.bounding_box, image_w, image_h)
            if rect is None:
                continue
            x0, y0, x1, y1 = rect
            if is_special:
                color = (160, 160, 160)
            else:
                p_idx += 1
                color = palette[(p_idx - 1) % len(palette)]
            cv2_rectangle(overlay, (x0, y0), (x1, y1), color, 2)
            label = (
                f"P{p_idx}" if not is_special else (roles[0] if roles else "special")
            )
            cv2_putText(
                overlay,
                label,
                (x0 + 4, max(14, y0 - 6)),
                cv2_FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
            )

    debug_txt_path = layout_debug_output_path(page)
    png_path = debug_txt_path.with_name(debug_txt_path.stem + f".{suffix}.png")
    cv2_imwrite(str(png_path), overlay)
    return png_path


def write_step_l_debug_overlay_png(
    page,
    final_blocks: List[Block],
    suffix: str = "stepL",
) -> "pathlib.Path | None":
    """Write a debug PNG showing the final classified blocks in reading order.

    Each top-level emitted block is framed by its role color and labeled
    ``B<idx>: <role>`` so the reading order baked into ``page.text`` is
    visually obvious.
    """
    base_image = page.cv2_numpy_page_image
    if base_image is None or not final_blocks:
        return None

    overlay = base_image.copy()
    image_h, image_w = overlay.shape[:2]

    for idx, block in enumerate(final_blocks, start=1):
        rect = _bbox_to_px_rect(block.bounding_box, image_w, image_h)
        if rect is None:
            continue
        x0, y0, x1, y1 = rect
        roles = block.block_role_labels or []
        role = roles[0] if roles else "paragraph"
        color = _FINAL_BLOCK_COLOR.get(role, (60, 200, 80))
        cv2_rectangle(overlay, (x0, y0), (x1, y1), color, 3)
        cv2_putText(
            overlay,
            f"B{idx}: {role}",
            (x0 + 4, max(16, y0 - 8)),
            cv2_FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
        )

    debug_txt_path = layout_debug_output_path(page)
    png_path = debug_txt_path.with_name(debug_txt_path.stem + f".{suffix}.png")
    cv2_imwrite(str(png_path), overlay)
    return png_path


# ─────────────────────────────────────────────────────────────────────────────
# Layout-debug enablement and output paths.
# ─────────────────────────────────────────────────────────────────────────────


def layout_debug_enabled() -> bool:
    return os.environ.get("PD_OCR_LAYOUT_DEBUG", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def layout_debug_output_path(page) -> pathlib.Path:
    explicit_file = os.environ.get("PD_OCR_LAYOUT_DEBUG_FILE", "").strip()
    if explicit_file:
        out_path = pathlib.Path(explicit_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        return out_path

    base_dir = os.environ.get("PD_OCR_LAYOUT_DEBUG_DIR", "").strip() or "."
    out_dir = pathlib.Path(base_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = (
        page.name
        or (pathlib.Path(page.image_path).stem if page.image_path else None)
        or f"page-{page.page_index + 1}"
    )
    safe_stem = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in stem)
    return out_dir / f"{safe_stem}.layout-debug.txt"


# ─────────────────────────────────────────────────────────────────────────────
# Geometry primitives — pure, no Page state. interval_gap, line_vertical_gaps,
# gaps_are_consistent and similar small helpers used by every step.
# ─────────────────────────────────────────────────────────────────────────────


def line_vertical_gaps(lines: List[Block]) -> List[float]:
    sorted_lines = sorted(
        [l for l in lines if l.bounding_box],
        key=lambda l: (l.bounding_box.minY, l.bounding_box.minX),
    )
    if len(sorted_lines) < 2:
        return []
    gaps: List[float] = []
    for i in range(len(sorted_lines) - 1):
        curr = sorted_lines[i].bounding_box
        nxt = sorted_lines[i + 1].bounding_box
        if curr is None or nxt is None:
            continue
        gaps.append(max(0.0, nxt.minY - curr.maxY))
    return gaps


def gaps_are_consistent(gaps: List[float]) -> bool:
    if len(gaps) < 2:
        return False
    med = float(np_median(gaps))
    std = float(np_std(gaps)) if len(gaps) > 1 else 0.0
    return med >= 0.0 and std <= max(1.0, 0.65 * max(med, 1.0))


def _word_interval_gap(min1: float, max1: float, min2: float, max2: float) -> float:
    return max(0.0, max(min1, min2) - min(max1, max2))


def _line_bands_from_group_words(words: List[Word], y_tol: float) -> List[List[Word]]:
    sorted_words = sorted(
        [w for w in words if w.bounding_box],
        key=lambda w: (
            w.bounding_box.vertical_midpoint if w.bounding_box else 0,
            w.bounding_box.minX if w.bounding_box else 0,
        ),
    )
    if not sorted_words:
        return []

    bands: List[List[Word]] = [[sorted_words[0]]]
    band_centers: List[float] = [
        sorted_words[0].bounding_box.vertical_midpoint
        if sorted_words[0].bounding_box
        else 0.0
    ]

    for word in sorted_words[1:]:
        y_mid = word.bounding_box.vertical_midpoint if word.bounding_box else 0.0
        best_idx = -1
        best_dist = float("inf")
        for idx, center in enumerate(band_centers):
            dist = abs(y_mid - center)
            if dist <= y_tol and dist < best_dist:
                best_idx = idx
                best_dist = dist
        if best_idx == -1:
            bands.append([word])
            band_centers.append(y_mid)
        else:
            bands[best_idx].append(word)
            members = [
                w.bounding_box.vertical_midpoint
                for w in bands[best_idx]
                if w.bounding_box
            ]
            band_centers[best_idx] = (
                float(np_mean(members)) if members else band_centers[best_idx]
            )

    for band in bands:
        band.sort(key=lambda w: w.bounding_box.minX if w.bounding_box else 0)
    bands.sort(
        key=lambda b: min((w.bounding_box.minY for w in b if w.bounding_box), default=0)
    )
    return bands


def _split_group_second_pass(words: List[Word], coord_width: float) -> List[List[Word]]:
    if len(words) < 12:
        return [words]

    median_h = float(
        np_median([w.bounding_box.height for w in words if w.bounding_box] or [0.01])
    )
    bands = _line_bands_from_group_words(words, y_tol=max(0.55 * median_h, 1e-6))
    if len(bands) < 3:
        return [words]

    band_boxes = []
    for band in bands:
        min_x = min((w.bounding_box.minX for w in band if w.bounding_box), default=0.0)
        max_x = max((w.bounding_box.maxX for w in band if w.bounding_box), default=0.0)
        min_y = min((w.bounding_box.minY for w in band if w.bounding_box), default=0.0)
        max_y = max((w.bounding_box.maxY for w in band if w.bounding_box), default=0.0)
        band_boxes.append((min_x, max_x, min_y, max_y))

    gaps = [
        max(0.0, band_boxes[i + 1][2] - band_boxes[i][3]) for i in range(len(bands) - 1)
    ]
    gap_mean = float(np_mean(gaps)) if gaps else 0.0
    gap_std = float(np_std(gaps)) if len(gaps) > 1 else 0.0
    gap_trigger = max(1.2 * median_h, gap_mean + 1.25 * gap_std)

    group_min_x = min((bb[0] for bb in band_boxes), default=0.0)
    group_max_x = max((bb[1] for bb in band_boxes), default=0.0)
    group_w = max(1e-6, group_max_x - group_min_x)

    split_indices: List[int] = []
    for i in range(len(bands) - 1):
        gap = gaps[i]

        prev_band_words = [w for w in bands[i] if w.bounding_box]
        next_band_words = [w for w in bands[i + 1] if w.bounding_box]

        left_boundary_x = group_min_x + 0.40 * group_w
        right_boundary_x = group_min_x + 0.60 * group_w

        prev_left = [
            w
            for w in prev_band_words
            if w.bounding_box and w.bounding_box.horizontal_midpoint <= left_boundary_x
        ]
        next_left = [
            w
            for w in next_band_words
            if w.bounding_box and w.bounding_box.horizontal_midpoint <= left_boundary_x
        ]
        prev_right = [
            w
            for w in prev_band_words
            if w.bounding_box and w.bounding_box.horizontal_midpoint >= right_boundary_x
        ]
        next_right = [
            w
            for w in next_band_words
            if w.bounding_box and w.bounding_box.horizontal_midpoint >= right_boundary_x
        ]

        def side_continuous(prev_side: List[Word], next_side: List[Word]) -> bool:
            if not prev_side or not next_side:
                return False

            prev_min_x = min(
                (w.bounding_box.minX for w in prev_side if w.bounding_box), default=0.0
            )
            prev_max_x = max(
                (w.bounding_box.maxX for w in prev_side if w.bounding_box), default=0.0
            )
            next_min_x = min(
                (w.bounding_box.minX for w in next_side if w.bounding_box), default=0.0
            )
            next_max_x = max(
                (w.bounding_box.maxX for w in next_side if w.bounding_box), default=0.0
            )
            prev_max_y = max(
                (w.bounding_box.maxY for w in prev_side if w.bounding_box), default=0.0
            )
            next_min_y = min(
                (w.bounding_box.minY for w in next_side if w.bounding_box), default=0.0
            )

            side_w_prev = max(1e-6, prev_max_x - prev_min_x)
            side_w_next = max(1e-6, next_max_x - next_min_x)
            side_overlap = max(
                0.0, min(prev_max_x, next_max_x) - max(prev_min_x, next_min_x)
            )
            side_overlap_ratio = side_overlap / max(1e-6, min(side_w_prev, side_w_next))
            side_y_gap = max(0.0, next_min_y - prev_max_y)

            return side_overlap_ratio >= 0.30 and side_y_gap <= max(
                0.85 * median_h, 0.006 * coord_width
            )

        left_continuous = side_continuous(prev_left, next_left)
        right_continuous = side_continuous(prev_right, next_right)

        hard_gap_split = gap >= gap_trigger

        # Do not split a continuous full-width body stream into top/bottom just
        # because of one large vertical void (e.g., figure area in the middle).
        if hard_gap_split:
            upper_bands = bands[: i + 1]
            lower_bands = bands[i + 1 :]

            upper_words = [w for band in upper_bands for w in band if w.bounding_box]
            lower_words = [w for band in lower_bands for w in band if w.bounding_box]

            upper_count = len(upper_words)
            lower_count = len(lower_words)
            total_count = max(1, len(words))

            upper_min_x = min(
                (w.bounding_box.minX for w in upper_words if w.bounding_box),
                default=0.0,
            )
            upper_max_x = max(
                (w.bounding_box.maxX for w in upper_words if w.bounding_box),
                default=0.0,
            )
            lower_min_x = min(
                (w.bounding_box.minX for w in lower_words if w.bounding_box),
                default=0.0,
            )
            lower_max_x = max(
                (w.bounding_box.maxX for w in lower_words if w.bounding_box),
                default=0.0,
            )
            upper_w = max(1e-6, upper_max_x - upper_min_x)
            lower_w = max(1e-6, lower_max_x - lower_min_x)

            both_large = upper_count >= int(0.25 * total_count) and lower_count >= int(
                0.25 * total_count
            )
            both_body_like = upper_w >= 0.70 * group_w and lower_w >= 0.70 * group_w
            similar_margins = (
                abs(upper_min_x - lower_min_x) <= 0.05 * coord_width
                and abs(upper_max_x - lower_max_x) <= 0.05 * coord_width
            )

            if both_large and both_body_like and similar_margins:
                hard_gap_split = False

        if hard_gap_split:
            # Require evidence of a true boundary across the text flow.
            # If right side remains continuous while only left side breaks,
            # keep the group intact (common around figure/caption intrusions).
            if right_continuous and not left_continuous:
                hard_gap_split = False

        if hard_gap_split:
            split_indices.append(i)

    if not split_indices:
        return [words]

    segments: List[List[Word]] = []
    start = 0
    for idx in split_indices:
        segment_bands = bands[start : idx + 1]
        segment_words = [w for band in segment_bands for w in band]
        if segment_words:
            segments.append(segment_words)
        start = idx + 1

    tail_words = [w for band in bands[start:] for w in band]
    if tail_words:
        segments.append(tail_words)

    return segments if len(segments) > 1 else [words]


def _split_group_horizontal_pass(
    words: List[Word], coord_width: float
) -> List[List[Word]]:
    """Split groups that contain a strong left/right gap across line bands."""
    if len(words) < 10:
        return [words]

    median_h = float(
        np_median([w.bounding_box.height for w in words if w.bounding_box] or [0.01])
    )
    bands = _line_bands_from_group_words(words, y_tol=max(0.55 * median_h, 1e-6))
    if not bands:
        return [words]

    all_gaps: List[float] = []
    candidate_split_mids: List[float] = []
    for band in bands:
        band_words = sorted(
            [w for w in band if w.bounding_box],
            key=lambda w: w.bounding_box.minX if w.bounding_box else 0,
        )
        if len(band_words) < 2:
            continue
        band_gaps: List[tuple[float, float]] = []
        for i in range(len(band_words) - 1):
            a = band_words[i].bounding_box
            b = band_words[i + 1].bounding_box
            if a is None or b is None:
                continue
            gap = max(0.0, b.minX - a.maxX)
            mid = (a.maxX + b.minX) / 2.0
            if gap > 0:
                all_gaps.append(gap)
                band_gaps.append((gap, mid))

        if not band_gaps:
            continue
        # Use only the dominant gap from each band to reduce noise.
        max_gap, max_mid = max(band_gaps, key=lambda t: t[0])
        candidate_split_mids.append(max_mid)

    if not all_gaps or not candidate_split_mids:
        return [words]

    med_gap = float(np_median(all_gaps)) if all_gaps else 0.0
    abs_gap_threshold = max(0.04 * coord_width, 3.0 * med_gap)

    strong_band_mids: List[float] = []
    for band in bands:
        band_words = sorted(
            [w for w in band if w.bounding_box],
            key=lambda w: w.bounding_box.minX if w.bounding_box else 0,
        )
        if len(band_words) < 2:
            continue
        band_gaps: List[tuple[float, float]] = []
        for i in range(len(band_words) - 1):
            a = band_words[i].bounding_box
            b = band_words[i + 1].bounding_box
            if a is None or b is None:
                continue
            gap = max(0.0, b.minX - a.maxX)
            mid = (a.maxX + b.minX) / 2.0
            band_gaps.append((gap, mid))
        if not band_gaps:
            continue
        gap, mid = max(band_gaps, key=lambda t: t[0])
        if gap >= abs_gap_threshold:
            strong_band_mids.append(mid)

    # Need support from multiple bands (or one very large band split) to avoid
    # breaking normal paragraph lines.
    if not strong_band_mids:
        return [words]
    if len(strong_band_mids) == 1 and len(words) > 20:
        # Allow single-band split only when gap is very pronounced.
        lone_mid = strong_band_mids[0]
        split_x = lone_mid
    else:
        split_x = float(np_median(strong_band_mids))

    left = [
        w
        for w in words
        if w.bounding_box and w.bounding_box.horizontal_midpoint <= split_x
    ]
    right = [
        w
        for w in words
        if w.bounding_box and w.bounding_box.horizontal_midpoint > split_x
    ]
    if len(left) < 3 or len(right) < 3:
        return [words]

    left_max_x = max((w.bounding_box.maxX for w in left if w.bounding_box), default=0.0)
    right_min_x = min(
        (w.bounding_box.minX for w in right if w.bounding_box), default=1.0
    )
    if right_min_x - left_max_x < 0.02 * coord_width:
        return [words]

    return [left, right]


def _legacy_magic_wand_subgroups(
    words: List[Word],
    coord_width: float,
    coord_height: float,
) -> List[List[Word]]:
    """Original lightweight adjacency grouping, reused for small groups."""
    words_with_bbox = [w for w in words if w.bounding_box]
    if len(words_with_bbox) < 2:
        return [words]

    median_h = float(
        np_median(
            [w.bounding_box.height for w in words_with_bbox if w.bounding_box] or [0.01]
        )
    )
    same_row_y_tol = max(0.50 * median_h, 0.004 * coord_height)
    same_row_x_gap = max(1.8 * median_h, 0.028 * coord_width)
    next_row_y_gap = max(1.1 * median_h, 0.006 * coord_height)

    n = len(words_with_bbox)
    visited = [False] * n
    groups: List[List[Word]] = []

    def are_adjacent(i: int, j: int) -> bool:
        a = words_with_bbox[i].bounding_box
        b = words_with_bbox[j].bounding_box
        if a is None or b is None:
            return False

        y_mid_delta = abs(a.vertical_midpoint - b.vertical_midpoint)
        x_gap = _word_interval_gap(a.minX, a.maxX, b.minX, b.maxX)
        y_gap = _word_interval_gap(a.minY, a.maxY, b.minY, b.maxY)
        x_overlap = max(0.0, min(a.maxX, b.maxX) - max(a.minX, b.minX))
        min_w = max(min(a.width, b.width), 1e-6)
        overlap_ratio = x_overlap / min_w

        if y_mid_delta <= same_row_y_tol and x_gap <= same_row_x_gap:
            return True
        if y_gap <= next_row_y_gap and overlap_ratio >= 0.22:
            return True
        return False

    for i in range(n):
        if visited[i]:
            continue
        stack = [i]
        visited[i] = True
        comp: List[int] = []
        while stack:
            idx = stack.pop()
            comp.append(idx)
            for j in range(n):
                if visited[j]:
                    continue
                if are_adjacent(idx, j):
                    visited[j] = True
                    stack.append(j)
        groups.append([words_with_bbox[k] for k in comp])

    if len(groups) <= 1:
        return [words]

    # Preserve original order by top-left position.
    groups.sort(
        key=lambda g: (
            min((w.bounding_box.minY for w in g if w.bounding_box), default=0.0),
            min((w.bounding_box.minX for w in g if w.bounding_box), default=0.0),
        )
    )
    return groups


def compute_next_word_space_stats(
    words: List[Word],
) -> tuple[float, float, float, float, float, float, float, float]:
    """Return nearest-gap stats:

    (mean_x, std_x, mean_y, std_y, median_x, median_y, p90_x, p90_y)

    For each word, we compute the nearest positive X gap to another word on
    roughly the same row, and nearest positive Y gap to another word on roughly
    the same column. We then take the max of those nearest gaps.
    """
    words_with_bbox = [w for w in words if w.bounding_box]
    if len(words_with_bbox) < 2:
        return 0.0, 0.0

    median_h = float(
        np_median(
            [w.bounding_box.height for w in words_with_bbox if w.bounding_box] or [1]
        )
    )
    median_w = float(
        np_median(
            [w.bounding_box.width for w in words_with_bbox if w.bounding_box] or [1]
        )
    )

    same_row_tol = max(0.60 * median_h, 1e-6)
    same_col_tol = max(0.60 * median_w, 1e-6)

    nearest_x_gaps: List[float] = []
    nearest_y_gaps: List[float] = []

    for w in words_with_bbox:
        bb = w.bounding_box
        if bb is None:
            continue
        nearest_x = None
        nearest_y = None

        for other in words_with_bbox:
            if other is w or other.bounding_box is None:
                continue
            ob = other.bounding_box

            y_mid_delta = abs(ob.vertical_midpoint - bb.vertical_midpoint)
            if y_mid_delta <= same_row_tol:
                x_gap = _word_interval_gap(bb.minX, bb.maxX, ob.minX, ob.maxX)
                if x_gap > 0:
                    nearest_x = x_gap if nearest_x is None else min(nearest_x, x_gap)

            x_mid_delta = abs(ob.horizontal_midpoint - bb.horizontal_midpoint)
            if x_mid_delta <= same_col_tol:
                y_gap = _word_interval_gap(bb.minY, bb.maxY, ob.minY, ob.maxY)
                if y_gap > 0:
                    nearest_y = y_gap if nearest_y is None else min(nearest_y, y_gap)

        if nearest_x is not None:
            nearest_x_gaps.append(nearest_x)
        if nearest_y is not None:
            nearest_y_gaps.append(nearest_y)

    mean_x = float(np_mean(nearest_x_gaps)) if nearest_x_gaps else 0.0
    std_x = float(np_std(nearest_x_gaps)) if len(nearest_x_gaps) > 1 else 0.0
    mean_y = float(np_mean(nearest_y_gaps)) if nearest_y_gaps else 0.0
    std_y = float(np_std(nearest_y_gaps)) if len(nearest_y_gaps) > 1 else 0.0

    med_x = float(np_median(nearest_x_gaps)) if nearest_x_gaps else 0.0
    med_y = float(np_median(nearest_y_gaps)) if nearest_y_gaps else 0.0

    if nearest_x_gaps:
        x_sorted = sorted(nearest_x_gaps)
        idx = min(len(x_sorted) - 1, max(0, int(0.9 * (len(x_sorted) - 1))))
        p90_x = float(x_sorted[idx])
    else:
        p90_x = 0.0

    if nearest_y_gaps:
        y_sorted = sorted(nearest_y_gaps)
        idx = min(len(y_sorted) - 1, max(0, int(0.9 * (len(y_sorted) - 1))))
        p90_y = float(y_sorted[idx])
    else:
        p90_y = 0.0

    return mean_x, std_x, mean_y, std_y, med_x, med_y, p90_x, p90_y


def _group_sort_key(group: List[Word]) -> tuple[float, float]:
    min_y = min((w.bounding_box.minY for w in group if w.bounding_box), default=0.0)
    min_x = min((w.bounding_box.minX for w in group if w.bounding_box), default=0.0)
    return (min_y, min_x)


def _detect_word_groups_internal(
    page,
) -> tuple[List[List[Word]], List[List[Word]], List[List[Word]], List[List[Word]]]:
    """Return grouped words for each sub-pass:

    (seed_groups, vertical_split_groups, horizontal_split_groups, final_groups)
    """
    words = [w for w in page.words if w.bounding_box and (w.text or "").strip()]
    if not words:
        return ([], [], [], [])

    page_w, page_h = page.resolved_dimensions

    bbox_max_x = max(
        (w.bounding_box.maxX for w in words if w.bounding_box), default=1.0
    )
    bbox_max_y = max(
        (w.bounding_box.maxY for w in words if w.bounding_box), default=1.0
    )
    # Use coordinate-domain dimensions (normalized vs pixel) for thresholds.
    coord_width = (
        1.0 if bbox_max_x <= 2.0 else float(page_w or page.width or bbox_max_x)
    )
    coord_height = (
        1.0 if bbox_max_y <= 2.0 else float(page_h or page.height or bbox_max_y)
    )

    median_h = float(
        np_median([w.bounding_box.height for w in words if w.bounding_box] or [1])
    )
    avg_word_gap = estimate_average_word_distance(words, page.width)
    (
        mean_next_x_space,
        std_next_x_space,
        mean_next_y_space,
        std_next_y_space,
        med_next_x_space,
        med_next_y_space,
        p90_next_x_space,
        p90_next_y_space,
    ) = compute_next_word_space_stats(words)

    # Dynamic thresholds (with global floors) used during group growth.
    same_row_y_tol_floor = max(0.55 * median_h, 0.004 * coord_height)
    same_row_x_tol_floor = max(2.4 * avg_word_gap, 0.012 * coord_width)
    stack_x_tol_floor = max(1.2 * avg_word_gap, 0.010 * coord_width)
    stack_y_tol_floor = max(1.8 * median_h, 0.010 * coord_height)
    # Use median nearest spacing as the primary cap and p90 as a robust upper
    # ceiling so single large outliers don't connect distant regions.
    row_link_x_cap = max(
        1.0 * avg_word_gap,
        1.15 * (mean_next_x_space + 2.0 * std_next_x_space),
        1.10 * med_next_x_space,
    )
    if p90_next_x_space > 0:
        row_link_x_cap = min(row_link_x_cap, 1.10 * p90_next_x_space)

    stack_link_y_cap = max(
        0.90 * median_h,
        1.15 * (mean_next_y_space + 2.0 * std_next_y_space),
        1.10 * med_next_y_space,
    )
    if p90_next_y_space > 0:
        stack_link_y_cap = min(stack_link_y_cap, 1.10 * p90_next_y_space)

    x_std_eps = max(std_next_x_space, 1e-6)
    y_std_eps = max(std_next_y_space, 1e-6)

    unassigned = set(range(len(words)))
    seed_groups: List[List[Word]] = []
    global_min_y = min(
        (w.bounding_box.minY for w in words if w.bounding_box), default=0.0
    )
    top_guard_band_end = global_min_y + max(3.0 * median_h, 0.02 * coord_height)

    while unassigned:
        seed_idx = min(
            unassigned,
            key=lambda i: (
                words[i].bounding_box.minY if words[i].bounding_box else 0,
                words[i].bounding_box.minX if words[i].bounding_box else 0,
            ),
        )
        group_indices = {seed_idx}
        unassigned.remove(seed_idx)

        changed = True
        while changed and unassigned:
            changed = False

            g_words = [words[i] for i in group_indices if words[i].bounding_box]
            if not g_words:
                break

            g_med_x_mid = float(
                np_median(
                    [
                        w.bounding_box.horizontal_midpoint
                        for w in g_words
                        if w.bounding_box
                    ]
                )
            )
            g_med_y_mid = float(
                np_median(
                    [
                        w.bounding_box.vertical_midpoint
                        for w in g_words
                        if w.bounding_box
                    ]
                )
            )
            g_min_y = min(
                (w.bounding_box.minY for w in g_words if w.bounding_box), default=0.0
            )
            g_med_h = float(
                np_median(
                    [w.bounding_box.height for w in g_words if w.bounding_box]
                    or [median_h]
                )
            )
            g_med_w = float(
                np_median(
                    [w.bounding_box.width for w in g_words if w.bounding_box]
                    or [0.02 * coord_width]
                )
            )

            same_row_y_tol = max(0.55 * g_med_h, same_row_y_tol_floor)
            same_row_x_tol = max(0.75 * g_med_w, same_row_x_tol_floor)
            stack_x_tol = max(0.35 * g_med_w, stack_x_tol_floor)
            stack_y_tol = max(1.6 * g_med_h, stack_y_tol_floor)
            # Keep early vertical growth strict only in the top guard band
            # (page number/running header area). Else allow captions/blocks to
            # grow vertically from small seeds.
            in_top_guard_band = g_min_y <= top_guard_band_end
            allow_vertical_links = (len(group_indices) >= 6) or (not in_top_guard_band)

            to_add: List[int] = []
            for idx in list(unassigned):
                bb = words[idx].bounding_box
                if bb is None:
                    continue

                x_mid_dist = abs(bb.horizontal_midpoint - g_med_x_mid)
                y_mid_dist = abs(bb.vertical_midpoint - g_med_y_mid)

                # Nearest relation to current group (prevents broad transitive grabs).
                nearest_x_gap = float("inf")
                nearest_y_gap = float("inf")
                nearest_y_mid = float("inf")
                nearest_x_mid = float("inf")
                nearest_y_overlap_ratio = 0.0
                nearest_x_overlap_ratio = 0.0
                for gw in g_words:
                    gbb = gw.bounding_box
                    if gbb is None:
                        continue
                    nearest_x_gap = min(
                        nearest_x_gap,
                        _word_interval_gap(gbb.minX, gbb.maxX, bb.minX, bb.maxX),
                    )
                    nearest_y_gap = min(
                        nearest_y_gap,
                        _word_interval_gap(gbb.minY, gbb.maxY, bb.minY, bb.maxY),
                    )
                    nearest_y_mid = min(
                        nearest_y_mid,
                        abs(gbb.vertical_midpoint - bb.vertical_midpoint),
                    )
                    nearest_x_mid = min(
                        nearest_x_mid,
                        abs(gbb.horizontal_midpoint - bb.horizontal_midpoint),
                    )

                    y_overlap = max(
                        0.0, min(gbb.maxY, bb.maxY) - max(gbb.minY, bb.minY)
                    )
                    x_overlap = max(
                        0.0, min(gbb.maxX, bb.maxX) - max(gbb.minX, bb.minX)
                    )
                    min_h = max(min(gbb.height, bb.height), 1e-6)
                    min_w = max(min(gbb.width, bb.width), 1e-6)
                    nearest_y_overlap_ratio = max(
                        nearest_y_overlap_ratio, y_overlap / min_h
                    )
                    nearest_x_overlap_ratio = max(
                        nearest_x_overlap_ratio, x_overlap / min_w
                    )

                x_z = (nearest_x_gap - mean_next_x_space) / x_std_eps
                y_z = (nearest_y_gap - mean_next_y_space) / y_std_eps

                same_row_like = (
                    min(y_mid_dist, nearest_y_mid) <= same_row_y_tol
                    and nearest_x_gap <= min(same_row_x_tol, row_link_x_cap)
                    and x_z <= 1.9
                    and nearest_y_overlap_ratio >= 0.42
                )
                stacked_like = (
                    (
                        min(x_mid_dist, nearest_x_mid) <= stack_x_tol
                        and nearest_y_gap <= min(stack_y_tol, stack_link_y_cap)
                        and y_z <= 1.9
                        and nearest_x_overlap_ratio >= 0.24
                    )
                    if allow_vertical_links
                    else False
                )
                touching_like = (
                    (
                        nearest_x_gap <= 0.60 * min(same_row_x_tol, row_link_x_cap)
                        and nearest_y_gap <= 0.70 * min(stack_y_tol, stack_link_y_cap)
                        and x_z <= 1.3
                        and y_z <= 1.3
                    )
                    if allow_vertical_links
                    else False
                )

                if same_row_like or stacked_like or touching_like:
                    to_add.append(idx)

            if to_add:
                for idx in to_add:
                    if idx in unassigned:
                        unassigned.remove(idx)
                        group_indices.add(idx)
                changed = True

        seed_groups.append([words[i] for i in sorted(group_indices)])

    # Second pass: split broad groups at strong inter-line boundaries.
    vertical_split_groups: List[List[Word]] = []
    for group in seed_groups:
        vertical_split_groups.extend(_split_group_second_pass(group, coord_width))

    horizontal_split_groups: List[List[Word]] = []
    for group in vertical_split_groups:
        horizontal_split_groups.extend(_split_group_horizontal_pass(group, coord_width))

    # Reuse the original lightweight magic-wand logic for small groups.
    # This helps avoid overfitting of strict global rules in compact regions.
    legacy_refined: List[List[Word]] = []
    for group in horizontal_split_groups:
        if 2 <= len(group) <= 36:
            legacy_refined.extend(
                _legacy_magic_wand_subgroups(
                    group,
                    coord_width=coord_width,
                    coord_height=coord_height,
                )
            )
        else:
            legacy_refined.append(group)
    final_groups = legacy_refined

    # Stable top-to-bottom, then left-to-right ordering.
    seed_groups.sort(key=_group_sort_key)
    vertical_split_groups.sort(key=_group_sort_key)
    horizontal_split_groups.sort(key=_group_sort_key)
    final_groups.sort(key=_group_sort_key)
    return (seed_groups, vertical_split_groups, horizontal_split_groups, final_groups)


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — word-level region grouping. Three sub-passes (1a seed growth,
# 1b vertical hard-gap split, 1c horizontal split + legacy small-group
# refinement) feed into ``detect_word_groups``.
# ─────────────────────────────────────────────────────────────────────────────


def detect_word_groups(page) -> List[List[Word]]:
    """Detect disconnected word groups via staged geometry refinement."""
    _, _, _, final_groups = _detect_word_groups_internal(page)
    return final_groups


def _group_summary_lines(groups: List[List[Word]]) -> List[str]:
    out: List[str] = []
    out.append(f"Word group count: {len(groups)}")
    for idx, group in enumerate(groups, start=1):
        min_x = min((w.bounding_box.minX for w in group if w.bounding_box), default=0.0)
        min_y = min((w.bounding_box.minY for w in group if w.bounding_box), default=0.0)
        max_x = max((w.bounding_box.maxX for w in group if w.bounding_box), default=0.0)
        max_y = max((w.bounding_box.maxY for w in group if w.bounding_box), default=0.0)
        sample = " ".join((w.text or "").strip() for w in group[:6]).strip()
        out.append(
            f"  group-{idx:02d}: words={len(group)} bbox=({min_x:.4f},{min_y:.4f})-({max_x:.4f},{max_y:.4f})"
        )
        if sample:
            out.append(f"    sample: {sample}")
    return out


def _base_step1_geometry_lines(page) -> List[str]:
    words = [w for w in page.words if w.bounding_box and (w.text or "").strip()]
    paragraphs = [p for p in page.paragraphs if p.bounding_box]
    lines = [l for l in page.lines if l.bounding_box]

    if not words:
        return ["Step 1: no words available."]

    out: List[str] = []
    page_w, page_h = page.resolved_dimensions
    max_word_x = max(
        (w.bounding_box.maxX for w in words if w.bounding_box), default=0.0
    )
    max_word_y = max(
        (w.bounding_box.maxY for w in words if w.bounding_box), default=0.0
    )
    (
        mean_next_x_space,
        std_next_x_space,
        mean_next_y_space,
        std_next_y_space,
        med_next_x_space,
        med_next_y_space,
        p90_next_x_space,
        p90_next_y_space,
    ) = compute_next_word_space_stats(words)
    out.append(f"Max X/Y (words): {max_word_x:.4f}, {max_word_y:.4f}")
    out.append(f"Max X/Y (page resolved): {float(page_w):.4f}, {float(page_h):.4f}")
    out.append(
        f"Median X/Y space to next word: {med_next_x_space:.4f}, {med_next_y_space:.4f}"
    )
    out.append(
        f"Mean+Std X/Y space to next word: {mean_next_x_space:.4f}+{std_next_x_space:.4f}, {mean_next_y_space:.4f}+{std_next_y_space:.4f}"
    )
    out.append(
        f"P90 X/Y space to next word: {p90_next_x_space:.4f}, {p90_next_y_space:.4f}"
    )
    out.append(f"Word count: {len(words)}")
    out.append(f"Line count: {len(lines)}")
    out.append(f"Paragraph count: {len(paragraphs)}")

    widths = [w.bounding_box.width for w in words if w.bounding_box]
    heights = [w.bounding_box.height for w in words if w.bounding_box]
    if widths:
        out.append(f"Median word width: {float(np_median(widths)):.4f}")
    if heights:
        out.append(f"Median word height: {float(np_median(heights)):.4f}")
    out.append("Overlay: paragraphs=green@25%, words=blue@15%")
    return out


def debug_step1_subgroup_sections(page) -> List[tuple[str, List[str]]]:
    """Return explicit Step 1a/1b/1c sections for sub-group passes."""
    seed_groups, vertical_groups, horizontal_groups, final_groups = (
        _detect_word_groups_internal(page)
    )

    step1a = ["Step 1a: seed region growth (raw magic-wand connectivity)"]
    step1a.extend(_base_step1_geometry_lines(page))
    step1a.extend(_group_summary_lines(seed_groups))
    png_1a = write_step_groups_debug_overlay_png(page, seed_groups, "step1a")
    if png_1a is not None:
        step1a.append(f"Overlay PNG: {png_1a}")

    step1b = ["Step 1b: vertical hard-gap split pass"]
    step1b.append(f"Input groups from 1a: {len(seed_groups)}")
    step1b.extend(_group_summary_lines(vertical_groups))
    png_1b = write_step_groups_debug_overlay_png(page, vertical_groups, "step1b")
    if png_1b is not None:
        step1b.append(f"Overlay PNG: {png_1b}")

    step1c = ["Step 1c: horizontal split + legacy small-group refinement"]
    step1c.append(f"Input groups from 1b: {len(vertical_groups)}")
    step1c.append(f"Post-horizontal group count: {len(horizontal_groups)}")
    step1c.extend(_group_summary_lines(final_groups))
    png_1c = write_step_groups_debug_overlay_png(page, final_groups, "step1c")
    if png_1c is not None:
        step1c.append(f"Overlay PNG: {png_1c}")

    return [("Step 1a", step1a), ("Step 1b", step1b), ("Step 1c", step1c)]


def write_step_groups_debug_overlay_png(
    page,
    groups: List[List[Word]],
    suffix: str,
) -> pathlib.Path | None:
    """Write a debug PNG with overlays and supplied group boundaries."""
    base_image = page.cv2_numpy_page_image
    if base_image is None:
        return None

    words = [w for w in page.words if w.bounding_box and (w.text or "").strip()]
    if not words:
        return None

    overlay = base_image.copy()
    image_h, image_w = overlay.shape[:2]

    paragraph_layer = overlay.copy()
    for paragraph in page.paragraphs:
        bb = paragraph.bounding_box
        rect = _bbox_to_px_rect(bb, image_w, image_h)
        if rect is None:
            continue
        min_x, min_y, max_x, max_y = rect
        cv2_rectangle(
            paragraph_layer,
            (min_x, min_y),
            (max_x, max_y),
            (0, 180, 0),  # green in BGR
            -1,
        )
    overlay = cv2_addWeighted(paragraph_layer, 0.25, overlay, 0.75, 0.0)

    word_layer = overlay.copy()
    for word in words:
        bb = word.bounding_box
        rect = _bbox_to_px_rect(bb, image_w, image_h)
        if rect is None:
            continue
        min_x, min_y, max_x, max_y = rect
        cv2_rectangle(
            word_layer,
            (min_x, min_y),
            (max_x, max_y),
            (220, 90, 40),  # blue-toned in BGR
            -1,
        )
    overlay = cv2_addWeighted(word_layer, 0.15, overlay, 0.85, 0.0)

    # Thin outlines keep boxes legible on dense regions.
    for paragraph in page.paragraphs:
        bb = paragraph.bounding_box
        rect = _bbox_to_px_rect(bb, image_w, image_h)
        if rect is None:
            continue
        min_x, min_y, max_x, max_y = rect
        cv2_rectangle(
            overlay,
            (min_x, min_y),
            (max_x, max_y),
            (0, 140, 0),
            1,
        )
    for word in words:
        bb = word.bounding_box
        rect = _bbox_to_px_rect(bb, image_w, image_h)
        if rect is None:
            continue
        min_x, min_y, max_x, max_y = rect
        cv2_rectangle(
            overlay,
            (min_x, min_y),
            (max_x, max_y),
            (255, 120, 60),
            1,
        )

    # Add thin group-level outlines to visualize disconnected components.
    group_colors = [
        (20, 20, 220),
        (220, 120, 20),
        (180, 20, 180),
        (20, 160, 220),
        (220, 220, 20),
        (20, 220, 120),
    ]
    for group_idx, group in enumerate(groups, start=1):
        min_x = min((w.bounding_box.minX for w in group if w.bounding_box), default=0.0)
        min_y = min((w.bounding_box.minY for w in group if w.bounding_box), default=0.0)
        max_x = max((w.bounding_box.maxX for w in group if w.bounding_box), default=0.0)
        max_y = max((w.bounding_box.maxY for w in group if w.bounding_box), default=0.0)

        rect = _bbox_to_px_rect(
            _LooseBBox(min_x, min_y, max_x, max_y), image_w, image_h
        )
        if rect is None:
            continue
        gx0, gy0, gx1, gy1 = rect
        group_color = group_colors[(group_idx - 1) % len(group_colors)]
        cv2_rectangle(
            overlay,
            (gx0, gy0),
            (gx1, gy1),
            group_color,
            2,
        )
        label = f"G{group_idx} ({len(group)})"
        label_y = max(12, gy0 - 4)
        cv2_putText(
            overlay,
            label,
            (gx0 + 2, label_y),
            cv2_FONT_HERSHEY_SIMPLEX,
            0.45,
            group_color,
            1,
        )

    debug_txt_path = layout_debug_output_path(page)
    png_path = debug_txt_path.with_name(debug_txt_path.stem + f".{suffix}.png")
    cv2_imwrite(str(png_path), overlay)
    return png_path


def write_layout_debug_report(
    page, step_sections: List[tuple[str, List[str]]]
) -> pathlib.Path:
    report_lines: List[str] = []
    report_lines.append(
        f"Layout debug for page_index={page.page_index}, name={page.name or 'n/a'}"
    )
    report_lines.append("")
    for title, lines in step_sections:
        report_lines.append(title)
        report_lines.append("-" * len(title))
        report_lines.extend(lines or ["(no data)"])
        report_lines.append("")

    out_path = layout_debug_output_path(page)
    out_path.write_text("\n".join(report_lines).rstrip() + "\n", encoding="utf-8")
    write_layout_debug_index_html(page, out_path)
    return out_path


def write_layout_debug_index_html(
    page, debug_txt_path: pathlib.Path
) -> pathlib.Path | None:
    """Write a small index.html alongside the debug PNGs for quick review.

    The index walks the directory and embeds every ``*.step*.png`` and
    ``*.layout-debug.*.png`` it finds, in lexical order, so a reviewer can
    scroll through the entire pipeline state for the page in a browser.
    """
    out_dir = debug_txt_path.parent
    page_stem = debug_txt_path.stem  # e.g. "test1.layout-debug" or "layout-debug"
    pngs = sorted(out_dir.glob(f"{page_stem}.*.png"))
    if not pngs:
        return None

    index_path = out_dir / "index.html"
    page_label = page.name or f"page-{page.page_index + 1}"
    parts: List[str] = [
        "<!doctype html>",
        '<html><head><meta charset="utf-8">',
        f"<title>Layout debug — {page_label}</title>",
        "<style>",
        "body{font-family:system-ui,sans-serif;max-width:1200px;margin:1.5em auto;padding:0 1em;}",
        "h1{font-size:1.4em;}h2{font-size:1.1em;border-top:1px solid #ddd;padding-top:1em;}",
        "img{max-width:100%;border:1px solid #ccc;}",
        ".step{margin-bottom:2em;}",
        ".meta{color:#666;font-size:0.85em;}",
        "</style></head><body>",
        f"<h1>Layout debug — {page_label}</h1>",
        f'<p class="meta">Generated from {debug_txt_path.name}. Read top-to-bottom in pipeline order.</p>',
    ]
    for png in pngs:
        # Pull "stepX" out of the filename "<stem>.stepX.png".
        suffix = png.stem.rsplit(".", 1)[-1]
        parts.append('<div class="step">')
        parts.append(f"<h2>{suffix}</h2>")
        parts.append(f'<img src="{png.name}" alt="{suffix}">')
        parts.append("</div>")
    parts.append("</body></html>")
    index_path.write_text("\n".join(parts), encoding="utf-8")
    return index_path


def interval_gap(min1: float, max1: float, min2: float, max2: float) -> float:
    """Return distance between two 1D intervals (0 when overlapping)."""
    return max(0.0, max(min1, min2) - min(max1, max2))


def estimate_average_word_distance(words: List[Word], page_width: int) -> float:
    """Estimate average local word spacing for neighborhood growth."""
    words_with_bbox = [w for w in words if w.bounding_box]
    if len(words_with_bbox) < 2:
        return 0.02 * float(page_width)

    bbox_max_x = max(
        (w.bounding_box.maxX for w in words_with_bbox if w.bounding_box),
        default=float(page_width),
    )
    coord_width = 1.0 if bbox_max_x <= 2.0 else float(page_width)
    max_horizontal_gap = 0.08 * coord_width

    gaps: list[float] = []
    for word in words_with_bbox:
        bb = word.bounding_box
        if not bb:
            continue
        nearest_gap = None
        for other_word in words_with_bbox:
            if other_word is word or not other_word.bounding_box:
                continue
            other = other_word.bounding_box
            if other.minX < bb.minX:
                continue
            max_h = max(bb.height, other.height)
            if abs(other.vertical_midpoint - bb.vertical_midpoint) > 1.5 * max_h:
                continue
            gap = max(0.0, other.minX - bb.maxX)
            if gap <= max_horizontal_gap:
                nearest_gap = gap if nearest_gap is None else min(nearest_gap, gap)
        if nearest_gap is not None:
            gaps.append(nearest_gap)

    if not gaps:
        return 0.02 * coord_width
    return max(float(np_median(gaps)), 0.005 * coord_width)


def build_word_seeded_row_blocks(
    words: List[Word],
    page_width: int,
    page_height: int,
    source_lines: List[Block] | None = None,
) -> Block | None:
    """Build full text blocks by expanding from words, then split to lines."""
    words_with_bbox = [w for w in words if w.bounding_box]
    if len(words_with_bbox) < 10:
        return None

    bbox_max_x = max(
        (w.bounding_box.maxX for w in words_with_bbox if w.bounding_box),
        default=float(page_width),
    )
    bbox_max_y = max(
        (w.bounding_box.maxY for w in words_with_bbox if w.bounding_box),
        default=float(page_height),
    )
    coord_width = 1.0 if bbox_max_x <= 2.0 else float(page_width)
    coord_height = 1.0 if bbox_max_y <= 2.0 else float(page_height)

    avg_word_gap = estimate_average_word_distance(words_with_bbox, page_width)
    median_word_height = float(
        np_median(
            [w.bounding_box.height for w in words_with_bbox if w.bounding_box]
            or [0.02 * coord_height]
        )
    )

    x_expand = max(2.0 * avg_word_gap, 0.015 * coord_width)
    y_expand = max(1.25 * median_word_height, 0.01 * coord_height)

    n = len(words_with_bbox)
    visited = [False] * n
    components: List[List[Word]] = []

    for i in range(n):
        if visited[i]:
            continue

        stack = [i]
        visited[i] = True
        comp_indices: List[int] = []

        while stack:
            idx = stack.pop()
            comp_indices.append(idx)
            bb = words_with_bbox[idx].bounding_box
            if not bb:
                continue

            for j in range(n):
                if visited[j]:
                    continue
                other_bb = words_with_bbox[j].bounding_box
                if not other_bb:
                    continue
                x_gap = interval_gap(
                    bb.minX,
                    bb.maxX,
                    other_bb.minX,
                    other_bb.maxX,
                )
                y_gap = interval_gap(
                    bb.minY,
                    bb.maxY,
                    other_bb.minY,
                    other_bb.maxY,
                )
                if x_gap <= x_expand and y_gap <= y_expand:
                    visited[j] = True
                    stack.append(j)

        components.append([words_with_bbox[k] for k in comp_indices])

    # Single-word components must NOT be dropped — that loses real content
    # like a centered chapter heading ("PREFACE.") which sits in its own
    # vertical band far from any other text. Drop only truly empty components.
    components = [comp for comp in components if len(comp) >= 1]
    if not components:
        return None

    row_blocks: List[Block] = []
    assigned_line_ids: set[int] = set()
    line_y_tolerance = max(0.8 * median_word_height, 0.006 * coord_height)

    for component in components:
        component.sort(
            key=lambda w: (
                w.bounding_box.vertical_midpoint if w.bounding_box else 0,
                w.bounding_box.minX if w.bounding_box else 0,
            )
        )

        component_word_ids = {id(w) for w in component}
        if source_lines:
            component_lines = [
                line
                for line in source_lines
                if id(line) not in assigned_line_ids
                and any(id(word) in component_word_ids for word in line.words)
            ]
            component_lines.sort(
                key=lambda l: (
                    l.bounding_box.minY if l.bounding_box else 0,
                    l.bounding_box.minX if l.bounding_box else 0,
                )
            )
            if component_lines:
                assigned_line_ids.update(id(line) for line in component_lines)
                row_blocks.append(
                    Block(items=component_lines, block_category=BlockCategory.PARAGRAPH)
                )
                continue

        line_buckets: List[List[Word]] = []
        line_centers: List[float] = []

        for word in component:
            bb = word.bounding_box
            if not bb:
                continue
            y_mid = bb.vertical_midpoint
            best_bucket_idx = -1
            best_distance = float("inf")

            for bucket_idx, center_y in enumerate(line_centers):
                distance = abs(y_mid - center_y)
                if distance <= line_y_tolerance and distance < best_distance:
                    best_bucket_idx = bucket_idx
                    best_distance = distance

            if best_bucket_idx == -1:
                line_buckets.append([word])
                line_centers.append(y_mid)
            else:
                line_buckets[best_bucket_idx].append(word)
                bucket = line_buckets[best_bucket_idx]
                line_centers[best_bucket_idx] = float(
                    np_mean(
                        [
                            w.bounding_box.vertical_midpoint
                            for w in bucket
                            if w.bounding_box
                        ]
                    )
                )

        line_blocks: List[Block] = []
        for bucket in line_buckets:
            bucket.sort(key=lambda w: w.bounding_box.minX if w.bounding_box else 0)
            line_blocks.append(
                Block(
                    items=bucket,
                    child_type=BlockChildType.WORDS,
                    block_category=BlockCategory.LINE,
                )
            )

        if line_blocks:
            line_blocks.sort(key=lambda l: l.bounding_box.minY if l.bounding_box else 0)
            row_blocks.append(
                Block(items=line_blocks, block_category=BlockCategory.PARAGRAPH)
            )

    if not row_blocks:
        return None

    y_bucket = max(2.5 * median_word_height, 0.02 * coord_height)

    row_blocks.sort(
        key=lambda b: (
            int((b.bounding_box.minY if b.bounding_box else 0) / y_bucket),
            b.bounding_box.minX if b.bounding_box else 0,
            b.bounding_box.minY if b.bounding_box else 0,
        )
    )
    return Block(items=row_blocks, block_category=BlockCategory.BLOCK)


def row_block_quality(row_blocks: Block | None) -> float:
    """Lower score indicates cleaner, more reliable row block structure."""
    if row_blocks is None:
        return float("inf")

    lines = row_blocks.lines
    if not lines:
        return float("inf")

    short_text_lines = 0
    sparse_word_lines = 0
    total_words = 0
    y_backtracks = 0
    median_line_height = float(
        np_median(
            [line.bounding_box.height for line in lines if line.bounding_box] or [0.0]
        )
    )
    backtrack_tolerance = max(0.5 * median_line_height, 1e-6)
    prev_y = None
    for line in lines:
        text = (line.text or "").strip()
        word_count = len(line.words)
        total_words += word_count
        if len(text) <= 2:
            short_text_lines += 1
        if word_count <= 1:
            sparse_word_lines += 1
        if line.bounding_box is not None:
            y = line.bounding_box.minY
            if prev_y is not None and y < (prev_y - backtrack_tolerance):
                y_backtracks += 1
            prev_y = y

    avg_words_per_line = total_words / max(len(lines), 1)
    return (
        (6.0 * short_text_lines)
        + (2.5 * sparse_word_lines)
        + (15.0 * y_backtracks)
        + (3.0 if avg_words_per_line < 2.0 else 0.0)
    )


# ─────────────────────────────────────────────────────────────────────────────
# Step D — split mixed-content (caption + body) OCR lines by gap + height shift.
# ─────────────────────────────────────────────────────────────────────────────


def split_line_by_gap_and_word_height(
    line: Block,
    page_width: int,
    preferred_split_x: float | None = None,
) -> tuple[Block, Block] | None:
    """Split a mixed-content OCR line using gap + average word-height shift."""
    words = [w for w in line.words if w.bounding_box]
    if len(words) < 4:
        return None

    words.sort(key=lambda w: w.bounding_box.minX if w.bounding_box else 0)

    bbox_max_x = max(
        (w.bounding_box.maxX for w in words if w.bounding_box),
        default=float(page_width),
    )
    coord_width = 1.0 if bbox_max_x <= 2.0 else float(page_width)

    gaps: list[tuple[float, int, float]] = []
    for i in range(len(words) - 1):
        left_bb = words[i].bounding_box
        right_bb = words[i + 1].bounding_box
        if not left_bb or not right_bb:
            continue
        gap = max(0.0, right_bb.minX - left_bb.maxX)
        gap_mid = (left_bb.maxX + right_bb.minX) / 2.0
        gaps.append((gap, i, gap_mid))

    if not gaps:
        return None

    split_gap = None
    split_idx = None
    preferred_is_close = False
    if preferred_split_x is not None:
        nearest_gap, nearest_idx, nearest_mid = min(
            gaps,
            key=lambda g: abs(g[2] - preferred_split_x),
        )
        if (
            abs(nearest_mid - preferred_split_x) <= 0.06 * coord_width
            and nearest_gap >= 0.014 * coord_width
        ):
            split_gap, split_idx = nearest_gap, nearest_idx
            preferred_is_close = True

    if split_idx is None:
        max_gap, max_gap_idx, _ = max(gaps, key=lambda g: g[0])
        split_gap, split_idx = max_gap, max_gap_idx

    if split_gap < 0.022 * coord_width and not preferred_is_close:
        return None

    left_words = words[: split_idx + 1]
    right_words = words[split_idx + 1 :]
    if len(left_words) < 2 or len(right_words) < 2:
        return None

    left_h = float(
        np_mean([w.bounding_box.height for w in left_words if w.bounding_box] or [0])
    )
    right_h = float(
        np_mean([w.bounding_box.height for w in right_words if w.bounding_box] or [0])
    )
    if left_h <= 0 or right_h <= 0:
        return None

    h_ratio = max(left_h, right_h) / min(left_h, right_h)
    if preferred_is_close:
        if h_ratio < 1.02:
            return None
    elif h_ratio < 1.20:
        return None

    left_text = " ".join(w.text for w in left_words).rstrip()
    right_text = " ".join(w.text for w in right_words).lstrip()
    if left_text and right_text:
        right_starts_lower = right_text[0].isalpha() and right_text[0].islower()
        left_looks_continuation = left_text.endswith("-") or left_text.endswith(",")
        if not preferred_is_close and not (
            right_starts_lower or left_looks_continuation
        ):
            return None

    left_line = Block(
        items=left_words,
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )
    right_line = Block(
        items=right_words,
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )

    if (
        left_line.bounding_box
        and right_line.bounding_box
        and left_line.bounding_box.maxX > right_line.bounding_box.minX
    ):
        return None

    return left_line, right_line


def split_mixed_content_lines(paragraphs: List[Block], page_width: int) -> None:
    """Split OCR lines that merge figure-caption and body fragments."""
    for paragraph in paragraphs:
        candidate_lines = [
            line
            for line in paragraph.items
            if line.block_category == BlockCategory.LINE
        ]
        if not candidate_lines:
            continue

        line_widths = [
            line.bounding_box.width if line.bounding_box else 0
            for line in candidate_lines
        ]
        median_line_width = float(np_median(line_widths)) if line_widths else 0.0
        narrow_neighbor_threshold = (
            0.82 * median_line_width if median_line_width else 0.0
        )

        new_lines: list[Block] = []
        changed = False
        preferred_split_x = None
        last_split_y = None
        for i, line in enumerate(candidate_lines):
            neighbor_widths = []
            for j in range(max(0, i - 2), min(len(candidate_lines), i + 3)):
                bb = candidate_lines[j].bounding_box
                if bb is not None:
                    neighbor_widths.append(bb.width)
            has_narrow_neighbor = any(
                w <= narrow_neighbor_threshold for w in neighbor_widths
            )
            if not has_narrow_neighbor:
                new_lines.append(line)
                preferred_split_x = None
                last_split_y = None
                continue

            if (
                preferred_split_x is not None
                and last_split_y is not None
                and line.bounding_box is not None
                and (line.bounding_box.minY - last_split_y) > 0.08
            ):
                preferred_split_x = None
                last_split_y = None

            split = split_line_by_gap_and_word_height(
                line,
                page_width,
                preferred_split_x=preferred_split_x,
            )
            if split is None:
                new_lines.append(line)
                continue
            left_line, right_line = split
            new_lines.append(left_line)
            new_lines.append(right_line)
            changed = True
            if left_line.bounding_box and right_line.bounding_box:
                preferred_split_x = (
                    left_line.bounding_box.maxX + right_line.bounding_box.minX
                ) / 2.0
            if line.bounding_box is not None:
                last_split_y = line.bounding_box.minY

        if changed:
            new_lines.sort(
                key=lambda l: (
                    l.bounding_box.minY if l.bounding_box else 0,
                    l.bounding_box.minX if l.bounding_box else 0,
                )
            )
            paragraph.items = new_lines
            paragraph.recompute_bounding_box()


# ─────────────────────────────────────────────────────────────────────────────
# Step K — split a row block's lines into paragraphs using indent / narrow-line
# / wrapped-line rules.
# ─────────────────────────────────────────────────────────────────────────────


def compute_text_paragraph_blocks(lines: List[Block]) -> Block:
    logger.debug("Computing Paragraph Blocks")

    # Drop lines with no text content (empty OCR artifacts) so they don't
    # create spurious empty paragraphs that add extra blank lines to output.
    lines = [l for l in lines if (l.text or "").strip()]

    if not lines:
        return Block(items=[], block_category=BlockCategory.BLOCK)

    min_x_positions = [
        line.bounding_box.minX if line.bounding_box else 0 for line in lines
    ]
    max_x_positions = [
        line.bounding_box.maxX if line.bounding_box else 0 for line in lines
    ]
    min_y_positions = [
        line.bounding_box.minY if line.bounding_box else 0 for line in lines
    ]
    max_y_positions = [
        line.bounding_box.maxY if line.bounding_box else 0 for line in lines
    ]
    line_widths = [
        line.bounding_box.width if line.bounding_box else 0 for line in lines
    ]
    line_heights = [
        line.bounding_box.height if line.bounding_box else 0 for line in lines
    ]

    median_line_length = float(np_median(line_widths))
    median_line_height = float(np_median(line_heights)) if line_heights else 0.0

    median_left_indent = np_median(min_x_positions)
    median_right_indent = np_median(max_x_positions)

    left_tolerance = 0.02 * median_line_length
    right_tolerance = 0.15 * median_line_length

    left_max = median_left_indent + left_tolerance
    right_min = median_right_indent - right_tolerance

    narrow_line_threshold = 0.78 * median_line_length if median_line_length else 0.0
    same_band_tolerance = max(2.0 * left_tolerance, 0.01 * median_line_length)
    tight_vertical_gap = 0.75 * median_line_height if median_line_height else 0.0

    blocks = []
    current_block = [lines[0]]
    logger.debug("First Paragraph" + str(current_block[0].text[0:10] + "..."))
    for i in range(1, len(lines)):
        prev_x_end_paragraph = max_x_positions[i - 1] <= right_min
        current_x_start_paragraph = min_x_positions[i] >= left_max

        prev_width = line_widths[i - 1]
        curr_width = line_widths[i]
        prev_is_narrow = prev_width <= narrow_line_threshold
        curr_is_narrow = curr_width <= narrow_line_threshold
        same_left_band = (
            abs(min_x_positions[i] - min_x_positions[i - 1]) <= same_band_tolerance
        )
        line_gap = max(0.0, min_y_positions[i] - max_y_positions[i - 1])
        is_tightly_wrapped = line_gap <= tight_vertical_gap

        if prev_is_narrow and curr_is_narrow and same_left_band and is_tightly_wrapped:
            current_block.append(lines[i])
            continue

        returns_to_main_left = abs(min_x_positions[i] - median_left_indent) <= max(
            same_band_tolerance, 1.5 * left_tolerance
        )
        current_is_wideish = curr_width >= 0.85 * median_line_length
        previous_is_wrapped = prev_is_narrow and min_x_positions[
            i - 1
        ] > median_left_indent + (0.5 * same_band_tolerance)
        if (
            previous_is_wrapped
            and returns_to_main_left
            and current_is_wideish
            and line_gap <= max(tight_vertical_gap, 0.8 * median_line_height)
        ):
            current_block.append(lines[i])
            continue

        prev_text = (lines[i - 1].text or "").rstrip()
        curr_text = (lines[i].text or "").lstrip()
        if prev_text and curr_text:
            prev_last_char = prev_text[-1]
            curr_first_char = curr_text[0]
            if (
                curr_first_char.isalpha()
                and curr_first_char.islower()
                and prev_last_char not in ".!?;:"
                and line_gap <= max(tight_vertical_gap, 0.5 * median_line_height)
                and not current_x_start_paragraph  # indented starts override continuation
            ):
                current_block.append(lines[i])
                continue

        if prev_x_end_paragraph or current_x_start_paragraph:
            b = Block(items=current_block, block_category=BlockCategory.PARAGRAPH)
            logger.debug("New Paragraph: " + str(b.text[0:10] + "..."))
            blocks.append(b)
            current_block = [lines[i]]
        else:
            current_block.append(lines[i])

    if current_block:
        b = Block(items=current_block, block_category=BlockCategory.PARAGRAPH)
        blocks.append(b)

    new_block = Block(items=blocks, block_category=BlockCategory.BLOCK)
    logger.debug("New Block Paragraph Count: " + str(len(new_block.items)))
    logger.debug("New Block Line Count: " + str(len(new_block.lines)))
    return new_block


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline orchestration helpers — consume a Page and produce structured
# intermediates. Page only needs to call these in order; all the heavy lifting
# lives here. Full per-step heuristic specs in
# docs/architecture/reorganize_pipeline.md.
# ─────────────────────────────────────────────────────────────────────────────


def _yx_sort_key(line: Block):
    """Sort lines by minY then minX. Stable across normalized/pixel coords."""
    return (
        line.bounding_box.minY if line.bounding_box else 0,
        line.bounding_box.minX if line.bounding_box else 0,
    )


def record_floated_flow_debug_squeezed(
    row_idx: int,
    pre_lines: List[Block],
    left_flow: List[Block],
    right_flow: List[Block],
    band_body: List[Block],
    post_lines: List[Block],
    debug_squeezed_lines: List[str],
) -> None:
    """Append per-side gap-consistency info for the layout debug report."""
    body_gaps = line_vertical_gaps(band_body)
    body_med_gap = float(np_median(body_gaps)) if body_gaps else 0.0
    body_consistent = gaps_are_consistent(body_gaps)
    debug_squeezed_lines.append(
        f"row-{row_idx:03d}: pre={len(pre_lines)} left={len(left_flow)} "
        f"right={len(right_flow)} body={len(band_body)} post={len(post_lines)}"
    )
    for side_name, side_lines in (("left", left_flow), ("right", right_flow)):
        side_gaps = line_vertical_gaps(side_lines)
        side_med_gap = float(np_median(side_gaps)) if side_gaps else 0.0
        side_consistent = gaps_are_consistent(side_gaps)
        spacing_unchanged = (
            bool(side_gaps)
            and bool(body_gaps)
            and abs(side_med_gap - body_med_gap)
            <= max(1.0, 0.9 * max(body_med_gap, 1.0))
        )
        candidate = (
            len(side_lines) >= 2
            and side_consistent
            and spacing_unchanged
            and body_consistent
        )
        debug_squeezed_lines.append(
            f"  {side_name}: lines={len(side_lines)} med_gap={side_med_gap:.2f} "
            f"consistent={side_consistent} unchanged_vs_body={spacing_unchanged} "
            f"candidate={candidate}"
        )


def absorb_caption_tails_into_caption(
    page,
    row_block: Block,
    flow_rest: List[Block],
    caption_target: List[Block],
    caption_seed: List[Block],
) -> List[Block]:
    """Move trailing flow lines that look like caption continuation back into
    the caption. Geometry-only: works off the caption seed bbox + the
    surrounding row block's median line width.
    """
    seed_bbox_lines = [l for l in caption_seed if l.bounding_box]
    if not seed_bbox_lines:
        return flow_rest

    seed_x = float(np_median([l.bounding_box.minX for l in seed_bbox_lines]))
    seed_y0 = min(l.bounding_box.minY for l in seed_bbox_lines)
    seed_y1 = max(l.bounding_box.maxY for l in seed_bbox_lines)
    seed_h = float(np_mean([l.bounding_box.height for l in seed_bbox_lines] or [1]))
    block_median_w = float(
        np_median(
            [l.bounding_box.width for l in row_block.lines if l.bounding_box]
            or [page.width]
        )
    )

    sorted_flow = sorted(flow_rest, key=_yx_sort_key)

    def has_justified_continuation_below(idx: int, candidate: Block) -> bool:
        bb = candidate.bounding_box
        if not bb:
            return False
        anchor_left = bb.minX
        anchor_right = bb.maxX
        anchor_h = max(bb.height, 1.0)
        continuation_count = 0
        for next_line in sorted_flow[idx + 1 :]:
            nb = next_line.bounding_box
            if not nb:
                continue
            if nb.minY - bb.maxY > 3.0 * anchor_h:
                break
            left_aligned = abs(nb.minX - anchor_left) <= 0.04 * page.width
            right_aligned = abs(nb.maxX - anchor_right) <= 0.07 * page.width
            if left_aligned and right_aligned:
                continuation_count += 1
                if continuation_count >= 2:
                    return True
        return False

    kept: List[Block] = []
    for idx, line in enumerate(sorted_flow):
        bb = line.bounding_box
        if not bb:
            kept.append(line)
            continue
        y_mid = bb.vertical_midpoint
        near_caption_band = (
            (seed_y0 - 0.3 * seed_h) <= y_mid <= (seed_y1 + 0.9 * seed_h)
        )
        near_caption_x = abs(bb.minX - seed_x) <= 0.30 * page.width
        narrow_like_caption = bb.width <= 0.82 * block_median_w
        continuation_below = has_justified_continuation_below(idx, line)
        if (
            near_caption_band
            and near_caption_x
            and narrow_like_caption
            and not continuation_below
        ):
            caption_target.append(line)
        else:
            kept.append(line)
    return kept


def expand_floated_flow_row_block(
    page,
    b: Block,
    floated_flow,
    row_idx: int,
    debug_squeezed_lines: List[str],
    step_h_decisions: List[dict],
) -> List[Block]:
    """Pipeline Step I — expand a row block that contains a floated figure."""
    pre_lines, left_flow, right_flow, band_body, post_lines = floated_flow

    step_h_decisions.append(
        {
            "row_idx": row_idx,
            "kind": "floated_flow",
            "left": list(left_flow),
            "right": list(right_flow),
            "spanning": list(pre_lines) + list(band_body) + list(post_lines),
        }
    )
    logger.debug(
        "Detected floated span; pre=%d left=%d right=%d band_body=%d post=%d",
        len(pre_lines),
        len(left_flow),
        len(right_flow),
        len(band_body),
        len(post_lines),
    )
    if layout_debug_enabled():
        record_floated_flow_debug_squeezed(
            row_idx,
            pre_lines,
            left_flow,
            right_flow,
            band_body,
            post_lines,
            debug_squeezed_lines,
        )

    left_caption, left_flow_rest = _split_caption_like_prefix(left_flow, page.width)
    right_caption: List[Block] = []
    right_flow_rest = list(right_flow)

    if left_caption + right_caption:
        left_flow_rest = absorb_caption_tails_into_caption(
            page,
            b,
            left_flow_rest,
            left_caption,
            left_caption + right_caption,
        )

    new_blocks: List[Block] = []
    merged_main_lines = sorted(
        pre_lines + band_body + left_flow_rest + right_flow_rest + post_lines,
        key=_yx_sort_key,
    )
    if merged_main_lines:
        new_blocks.append(
            Block(items=merged_main_lines, block_category=BlockCategory.PARAGRAPH)
        )
    if left_caption:
        new_blocks.append(
            Block(
                items=left_caption,
                block_category=BlockCategory.PARAGRAPH,
                block_role_labels=["sidenote"],
                block_position_labels=["margin left"],
            )
        )
    if right_caption:
        new_blocks.append(
            Block(
                items=right_caption,
                block_category=BlockCategory.PARAGRAPH,
                block_role_labels=["sidenote"],
                block_position_labels=["margin right"],
            )
        )
    return new_blocks


def expand_mixed_column_row_block(
    mixed_col_split,
    row_idx: int,
    step_h_decisions: List[dict],
) -> List[Block]:
    """Pipeline Step H — expand a row block whose lines split into two narrow
    columns plus optional spanning lines."""
    left_lines, right_lines, spanning_lines = mixed_col_split
    left_median_x = float(
        np_median([l.bounding_box.minX for l in left_lines if l.bounding_box])
    )
    right_median_x = float(
        np_median([l.bounding_box.minX for l in right_lines if l.bounding_box])
    )
    if left_median_x > right_median_x:
        left_lines, right_lines = right_lines, left_lines
    logger.debug(
        "Detected mixed two-column+body row block; splitting into "
        "left (%d lines), right (%d lines), trailing body (%d lines)",
        len(left_lines),
        len(right_lines),
        len(spanning_lines),
    )
    step_h_decisions.append(
        {
            "row_idx": row_idx,
            "kind": "mixed_column",
            "left": list(left_lines),
            "right": list(right_lines),
            "spanning": list(spanning_lines),
        }
    )

    col_min_y_ff = min(
        l.bounding_box.minY for l in left_lines + right_lines if l.bounding_box
    )
    avg_h_ff = float(
        np_mean(
            [l.bounding_box.height for l in left_lines + right_lines if l.bounding_box]
            or [1]
        )
    )
    span_min_y_ff = (
        min(l.bounding_box.minY for l in spanning_lines if l.bounding_box)
        if spanning_lines
        else col_min_y_ff
    )
    if spanning_lines and span_min_y_ff < col_min_y_ff - avg_h_ff:
        return _emit_floated_mixed_column_blocks(
            left_lines, right_lines, spanning_lines, col_min_y_ff
        )
    return _emit_side_by_side_caption_blocks(left_lines, right_lines, spanning_lines)


def _emit_floated_mixed_column_blocks(
    left_lines: List[Block],
    right_lines: List[Block],
    spanning_lines: List[Block],
    col_min_y_ff: float,
) -> List[Block]:
    """Emit blocks for a floated-figure layout: body wraps around the figure."""
    spanning_before = [
        l
        for l in spanning_lines
        if l.bounding_box and l.bounding_box.minY < col_min_y_ff
    ]
    spanning_after = [
        l
        for l in spanning_lines
        if l.bounding_box and l.bounding_box.minY >= col_min_y_ff
    ]
    new_blocks: List[Block] = []
    body_main = sorted(spanning_before + right_lines, key=_yx_sort_key)
    if body_main:
        new_blocks.append(
            Block(items=body_main, block_category=BlockCategory.PARAGRAPH)
        )
    caption_sorted = sorted(left_lines, key=_yx_sort_key)
    if caption_sorted:
        new_blocks.append(
            Block(
                items=caption_sorted,
                block_category=BlockCategory.PARAGRAPH,
                block_role_labels=["sidenote"],
                block_position_labels=["margin left"],
            )
        )
    if spanning_after:
        new_blocks.append(
            Block(
                items=sorted(spanning_after, key=_yx_sort_key),
                block_category=BlockCategory.PARAGRAPH,
            )
        )
    return new_blocks


def _emit_side_by_side_caption_blocks(
    left_lines: List[Block],
    right_lines: List[Block],
    spanning_lines: List[Block],
) -> List[Block]:
    """Emit blocks for side-by-side captions plus optional trailing body."""
    caption_groups = [left_lines, right_lines]
    caption_groups.sort(
        key=lambda g: float(
            np_median([l.bounding_box.minX for l in g if l.bounding_box] or [0])
        )
    )
    new_blocks: List[Block] = []
    for group in caption_groups:
        new_blocks.append(
            Block(
                items=sorted(group, key=_yx_sort_key),
                block_category=BlockCategory.PARAGRAPH,
                block_role_labels=["paragraph"],
            )
        )
    if spanning_lines:
        new_blocks.append(
            Block(items=spanning_lines, block_category=BlockCategory.PARAGRAPH)
        )
    return new_blocks


def expand_multi_column_row_block(
    page,
    multi_col_split,
    row_idx: int,
    step_h_decisions: List[dict],
) -> Block:
    """Pipeline Step H — collapse a multi-column row block into a single flow."""
    column_groups, spanning_lines = multi_col_split
    logger.debug(
        "Detected multi-column row block; splitting into %d column groups and %d spanning lines",
        len(column_groups),
        len(spanning_lines),
    )
    step_h_decisions.append(
        {
            "row_idx": row_idx,
            "kind": "multi_column",
            "left": list(column_groups[0]) if column_groups else [],
            "right": list(column_groups[1]) if len(column_groups) > 1 else [],
            "spanning": list(spanning_lines),
            "extra_columns": [list(g) for g in column_groups[2:]],
        }
    )
    merged_flow_lines = _merge_isolated_columns_into_flow(column_groups, spanning_lines)
    return Block(items=merged_flow_lines, block_category=BlockCategory.PARAGRAPH)


def expand_simple_two_column_row_block(
    page,
    col_split,
    row_idx: int,
    step_h_decisions: List[dict],
) -> Block:
    """Pipeline Step H — collapse a simple two-column row block into a single
    flow paragraph (left then right)."""
    left_lines, right_lines = col_split
    left_median_x = float(
        np_median([l.bounding_box.minX for l in left_lines if l.bounding_box])
    )
    right_median_x = float(
        np_median([l.bounding_box.minX for l in right_lines if l.bounding_box])
    )
    if left_median_x > right_median_x:
        left_lines, right_lines = right_lines, left_lines
    logger.debug(
        "Detected two-column row block; splitting into left (%d lines) and "
        "right (%d lines) sub-blocks",
        len(left_lines),
        len(right_lines),
    )
    step_h_decisions.append(
        {
            "row_idx": row_idx,
            "kind": "two_column",
            "left": list(left_lines),
            "right": list(right_lines),
            "spanning": [],
        }
    )
    merged_flow_lines = _merge_isolated_columns_into_flow([left_lines, right_lines], [])
    return Block(items=merged_flow_lines, block_category=BlockCategory.PARAGRAPH)


def expand_row_blocks(
    page,
    row_blocks: Block,
    debug_squeezed_lines: List[str],
) -> Tuple[List[Block], List[dict]]:
    """Pipeline Step H/I — dispatch each row block to the right expander."""
    expanded_row_blocks: List[Block] = []
    step_h_decisions: List[dict] = []
    for row_idx, b in enumerate(row_blocks.items, start=1):
        floated_flow = _detect_floated_flow_span(b.lines, page.width)
        if floated_flow is not None:
            expanded_row_blocks.extend(
                expand_floated_flow_row_block(
                    page,
                    b,
                    floated_flow,
                    row_idx,
                    debug_squeezed_lines,
                    step_h_decisions,
                )
            )
            continue

        mixed_col_split = _detect_mixed_column_split(b.lines, page.width)
        if mixed_col_split is not None:
            expanded_row_blocks.extend(
                expand_mixed_column_row_block(
                    mixed_col_split, row_idx, step_h_decisions
                )
            )
            continue

        multi_col_split = _detect_multi_column_split(b.lines, page.width)
        if multi_col_split is not None:
            expanded_row_blocks.append(
                expand_multi_column_row_block(
                    page, multi_col_split, row_idx, step_h_decisions
                )
            )
            continue

        col_split = _detect_column_split(b.lines, page.width)
        if col_split is not None:
            expanded_row_blocks.append(
                expand_simple_two_column_row_block(
                    page, col_split, row_idx, step_h_decisions
                )
            )
        else:
            step_h_decisions.append(
                {
                    "row_idx": row_idx,
                    "kind": "single",
                    "left": [],
                    "right": [],
                    "spanning": list(b.lines),
                }
            )
            expanded_row_blocks.append(b)
    return expanded_row_blocks, step_h_decisions


SPECIAL_BLOCK_TYPES = frozenset(
    {
        "page header",
        "page footer",
        "sidenote left",
        "sidenote right",
        "poetry",
        "blockquote",
    }
)


def classify_and_paragraphize_blocks(
    page,
    expanded_row_blocks: List[Block],
) -> List[Block]:
    """Pipeline Step L — classify each row block (page header/footer, sidenote,
    poetry, blockquote, body) and paragraphize body blocks via Step K."""
    all_lines = list(
        itertools.chain.from_iterable([b.lines for b in expanded_row_blocks])
    )
    page_median_line_width = float(
        np_median(
            [l.bounding_box.width for l in all_lines if l.bounding_box] or [page.width]
        )
    )
    avg_line_height = float(
        np_mean([l.bounding_box.height for l in all_lines if l.bounding_box] or [1])
    )
    body_minX, body_maxX = _compute_body_x_extent(expanded_row_blocks, page.width)
    ocr_minY = float(
        min(b.bounding_box.minY for b in expanded_row_blocks if b.bounding_box)
    )
    ocr_maxY = float(
        max(b.bounding_box.maxY for b in expanded_row_blocks if b.bounding_box)
    )

    result: List[Block] = []
    for b in expanded_row_blocks:
        block_type = _classify_row_block(
            b,
            page.width,
            page.height,
            body_minX,
            body_maxX,
            page_median_line_width,
            ocr_minY,
            ocr_maxY,
            avg_line_height,
        )
        logger.debug("Row block classified as: %s", str(block_type))
        if block_type in SPECIAL_BLOCK_TYPES:
            result.append(wrap_special_role_block(b.lines, block_type))
        else:
            result.append(compute_text_paragraph_blocks(b.lines))
    return result


def _reorganize_lines_log_debug(message: str, line1text: str, line2text: str) -> None:
    logger.debug(
        message
        + "\nFirst line: "
        + str(line1text[0:10] + ("..." if len(line1text) > 10 else ""))
        + "\nSecond line: "
        + str(line2text[0:10] + ("..." if len(line2text) > 10 else ""))
    )


def _reorganize_lines_check_overlap(line: Block, next_line: Block) -> bool:
    """Return True when the two lines should NOT be merged (overlap heuristic)."""
    if not line.bounding_box:
        _reorganize_lines_log_debug(
            "First Line has no bounding box.", line.text, next_line.text
        )
        return False
    if not next_line.bounding_box:
        _reorganize_lines_log_debug(
            "Second Line has no bounding box.", line.text, next_line.text
        )
        return False

    y_overlap_h = line.bounding_box.overlap_y_amount(next_line.bounding_box)
    x_overlap_w = line.bounding_box.overlap_x_amount(next_line.bounding_box)

    overlap_not_ok = False
    if y_overlap_h < (
        0.4 * (np_mean([line.bounding_box.height, next_line.bounding_box.height]))
    ):
        _reorganize_lines_log_debug(
            f"Lines not overlapping on Y axis enough. Overlap is {y_overlap_h}",
            line.text,
            next_line.text,
        )
        overlap_not_ok = True

    if x_overlap_w > (0.1 * line.bounding_box.width):
        _reorganize_lines_log_debug(
            f"Lines overlapping on X axis too much. Overlap is {x_overlap_w}",
            line.text,
            next_line.text,
        )
        overlap_not_ok = True
    return overlap_not_ok


# ─────────────────────────────────────────────────────────────────────────────
# Step B — re-merge OCR-fragmented lines inside a block.
# ─────────────────────────────────────────────────────────────────────────────


def reorganize_lines(block: Block) -> None:
    """Step B — re-merge OCR-fragmented lines inside ``block``."""
    if not block.items:
        return
    lines: List[Block] = block.items
    if not all(hasattr(line, "block_category") for line in lines) and not all(
        line.block_category == BlockCategory.LINE for line in lines
    ):
        raise TypeError("All items in lines must have a block_category of LINE")

    logger.debug("Recomputing lines for block " + str(block.text[0:10] + "..."))
    if len(lines) < 2:
        return

    median_line_width = np_median(
        [line.bounding_box.width if line.bounding_box else 0 for line in lines]
    )

    i = -1
    while True:
        i = i + 1
        lines = block.items
        if i >= len(lines) - 1:
            break

        line: Block = lines[i]
        next_line: Block = lines[i + 1]

        if _reorganize_lines_check_overlap(line, next_line):
            continue
        if not line.bounding_box or not next_line.bounding_box:
            continue
        if abs(line.bounding_box.height - next_line.bounding_box.height) > (
            0.50 * line.bounding_box.height
        ):
            _reorganize_lines_log_debug(
                "Line height difference too large.", line.text, next_line.text
            )
            continue

        if line.bounding_box.minX > next_line.bounding_box.minX:
            line, next_line = next_line, line
        if not line.bounding_box or not next_line.bounding_box:
            continue

        x_space_between = max(next_line.bounding_box.minX - line.bounding_box.maxX, 0)

        # Style-shift guard: don't merge across a clear glyph-height shift.
        line_word_heights = [
            w.bounding_box.height for w in line.words if w.bounding_box
        ]
        next_word_heights = [
            w.bounding_box.height for w in next_line.words if w.bounding_box
        ]
        if line_word_heights and next_word_heights:
            line_avg_h = float(np_mean(line_word_heights))
            next_avg_h = float(np_mean(next_word_heights))
            height_ratio = max(line_avg_h, next_avg_h) / max(
                min(line_avg_h, next_avg_h), 1e-6
            )
            bbox_max_x = max(line.bounding_box.maxX, next_line.bounding_box.maxX)
            coord_width = 1.0 if bbox_max_x <= 2.0 else float(bbox_max_x)
            if height_ratio >= 1.20 and x_space_between >= 0.02 * coord_width:
                _reorganize_lines_log_debug(
                    "Keeping lines split due to height/style shift.",
                    line.text,
                    next_line.text,
                )
                continue

        ten_percent_median_line_length = median_line_width * 0.10
        if x_space_between < ten_percent_median_line_length:
            _reorganize_lines_log_debug("Merging Lines.", line.text, next_line.text)
            line.merge(next_line)
            block.remove_item(next_line)
            i = i - 1
            continue
        else:
            _reorganize_lines_log_debug(
                "Lines not split on X axis enough.", line.text, next_line.text
            )
            continue


# ─────────────────────────────────────────────────────────────────────────────
# Step F — group lines into row blocks by dynamic vertical spacing.
# ─────────────────────────────────────────────────────────────────────────────


def compute_text_row_blocks(lines: List[Block], tolerance=None) -> "Block | None":
    """Step F — group lines into row blocks by dynamic vertical spacing.

    Does not mutate the caller's ``lines`` list — sorts a local copy.
    """
    logger.debug("Computing text row blocks")
    if len(lines) == 0:
        return None

    if tolerance is None:
        tolerance = 0.2 * np_mean(
            [line.bounding_box.height if line.bounding_box else 0 for line in lines]
        )

    logger.debug("Tolerance: " + str(tolerance))

    lines = sorted(
        lines, key=lambda line: line.bounding_box.minY if line.bounding_box else 0
    )

    min_y_positions = [
        line.bounding_box.minY if line.bounding_box else 0 for line in lines
    ]
    max_y_positions = [
        line.bounding_box.maxY if line.bounding_box else 0 for line in lines
    ]
    line_spacings = [
        max(0, min_y_positions[i] - max_y_positions[i - 1])
        for i in range(1, len(lines))
    ]

    median_line_height_spacing = float(
        np_median(
            [line.bounding_box.height if line.bounding_box else 0 for line in lines]
        )
        * 0.10
    )
    logger.debug("Median Line Height Spacing: " + str(median_line_height_spacing))

    std_line_height_spacing = (
        float(np_std(line_spacings)) * 0.75 if line_spacings else 0.0
    )
    logger.debug(
        "Standard Deviation Line Height Spacing: " + str(std_line_height_spacing)
    )

    tolerance_spacing = tolerance + max(
        float(std_line_height_spacing), (median_line_height_spacing * 0.25)
    )
    logger.debug("Tolerance Spacing: " + str(tolerance_spacing))

    blocks: List[Block] = []
    current_block = [lines[0]]
    logger.debug("Starting Block: " + str(current_block[0].text[0:25] + "..."))
    for i in range(1, len(lines)):
        prev_line_space_after = max(line_spacings[i - 1], 0)
        logger.debug("Line: " + str(lines[i].text[0:25] + "..."))
        logger.debug("Previous line space after: " + str(prev_line_space_after))
        if prev_line_space_after >= 0 and prev_line_space_after > tolerance_spacing:
            prev_bb = lines[i - 1].bounding_box
            curr_bb = lines[i].bounding_box
            if prev_bb and curr_bb and prev_bb.overlap_x_amount(curr_bb) <= 0:
                logger.debug(
                    "Lines have no X overlap — side-by-side columns, "
                    "suppressing paragraph break"
                )
                current_block.append(lines[i])
            else:
                b = Block(items=current_block, block_category=BlockCategory.PARAGRAPH)
                logger.debug("New Block: " + str(b.text[0:25] + "..."))
                blocks.append(b)
                current_block = [lines[i]]
        else:
            current_block.append(lines[i])

    if current_block:
        b = Block(items=current_block, block_category=BlockCategory.PARAGRAPH)
        blocks.append(b)

    logger.debug("Block Count: " + str(len(blocks)))
    for block in blocks:
        logger.debug("Block: " + str(block.text[0:10] + "..."))

    return Block(items=blocks, block_category=BlockCategory.BLOCK)


def emit_band_only_blocks(
    page,
    page_header_block: Block | None,
    page_footer_block: Block | None,
) -> None:
    """Assemble the page even when no body content remains so headerless pages
    stay consistent."""
    band_only_blocks: List[Block] = []
    if page_header_block is not None:
        band_only_blocks.append(page_header_block)
    if page_footer_block is not None:
        band_only_blocks.append(page_footer_block)
    if not band_only_blocks:
        return
    for block_idx, block in enumerate(band_only_blocks):
        block.override_page_sort_order = block_idx
    page.items = band_only_blocks
    page.refresh_page_images()


def run_step_d_split_mixed_content(
    page,
    debug_sections: List[tuple],
) -> None:
    """Step D — split OCR-merged caption/body lines and emit debug PNG."""
    debug = layout_debug_enabled()
    pre_split_line_ids: set[int] = set()
    if debug:
        pre_split_line_ids = {id(line) for line in page.lines}
        pre_split_line_count = len(pre_split_line_ids)

    split_mixed_content_lines(page.paragraphs, page.width)

    if not debug:
        return
    post_split_paragraphs = list(page.paragraphs)
    post_split_lines = list(page.lines)
    new_line_count = sum(
        1 for line in post_split_lines if id(line) not in pre_split_line_ids
    )
    step_d_lines = [
        "Step D: split mixed-content OCR lines",
        f"Pre-split line count: {pre_split_line_count}",
        f"Post-split line count: {len(post_split_lines)}",
        f"Lines added by gap+height split: {new_line_count}",
    ]
    faux_pre = [
        Block(
            items=[l for l in post_split_lines if id(l) in pre_split_line_ids],
            block_category=BlockCategory.PARAGRAPH,
        )
    ]
    png_d = write_step_d_debug_overlay_png(page, faux_pre, post_split_paragraphs)
    if png_d is not None:
        step_d_lines.append(f"Overlay PNG: {png_d}")
    debug_sections.append(("Step D", step_d_lines))


def run_step_e_extract_header_footer(
    page,
    debug_sections: List[tuple],
):
    """Step E — peel page header/footer bands and split body words."""
    page_metrics = compute_page_metrics(page)
    all_lines = list(page.lines)
    header_lines, after_header_lines = extract_top_header_lines(all_lines, page_metrics)
    footer_lines, body_lines = extract_bottom_footer_lines(
        after_header_lines, page_metrics
    )
    page_header_block = build_page_header_block(header_lines)
    page_footer_block = build_page_footer_block(footer_lines)

    if layout_debug_enabled():
        step_e_lines = [
            "Step E: page header / footer band extraction",
            f"Header lines: {len(header_lines)}",
            f"Footer lines: {len(footer_lines)}",
            f"Body lines remaining: {len(body_lines)}",
            f"Median word h (coord): {page_metrics.median_word_h:.4f}",
            f"Coord (w,h): {page_metrics.coord_w:.2f},{page_metrics.coord_h:.2f}",
        ]
        png_e = write_step_e_debug_overlay_png(page, header_lines, footer_lines)
        if png_e is not None:
            step_e_lines.append(f"Overlay PNG: {png_e}")
        debug_sections.append(("Step E", step_e_lines))

    excluded_word_ids = {
        id(w)
        for line in (header_lines + footer_lines)
        for w in line.words
        if w.bounding_box
    }
    body_words = [
        w for w in page.words if w.bounding_box and id(w) not in excluded_word_ids
    ]
    return (
        header_lines,
        footer_lines,
        body_lines,
        body_words,
        page_header_block,
        page_footer_block,
    )


def run_step_fg_row_blocks(
    page,
    body_lines: List[Block],
    body_words: List[Word],
    debug_sections: List[tuple],
) -> Block | None:
    """Step F/G — pick between legacy and seeded row-block grouping."""
    legacy_row_blocks = compute_text_row_blocks(body_lines)
    seeded_row_blocks = build_word_seeded_row_blocks(
        body_words, page.width, page.height, source_lines=body_lines
    )
    if seeded_row_blocks is not None and (
        row_block_quality(seeded_row_blocks) <= row_block_quality(legacy_row_blocks)
    ):
        row_blocks = seeded_row_blocks
        row_blocks_source = "seeded"
    else:
        row_blocks = legacy_row_blocks
        row_blocks_source = "legacy"

    if layout_debug_enabled():
        step_rb_lines = [
            "Step F/G: vertical row block grouping",
            f"Source picked: {row_blocks_source}",
            f"Row block count: {len(row_blocks.items) if row_blocks else 0}",
            f"Legacy quality: {row_block_quality(legacy_row_blocks):.2f}",
        ]
        if seeded_row_blocks is not None:
            step_rb_lines.append(
                f"Seeded quality: {row_block_quality(seeded_row_blocks):.2f}"
            )
        png_rb = write_step_row_blocks_debug_overlay_png(page, row_blocks, "stepFG")
        if png_rb is not None:
            step_rb_lines.append(f"Overlay PNG: {png_rb}")
        debug_sections.append(("Step F/G", step_rb_lines))
    return row_blocks


# ─────────────────────────────────────────────────────────────────────────────
# Layout detection primitives — pure functions, no Page state. Each takes the
# row block lines and the page coordinate width / height where needed.
# Migrated from Page class methods.
# ─────────────────────────────────────────────────────────────────────────────


def _compute_body_x_extent(blocks: List[Block], page_width: int) -> tuple[float, float]:
    """Estimate main body text X extent from row blocks using median positions."""
    min_xs = [b.bounding_box.minX for b in blocks if b.bounding_box]
    max_xs = [b.bounding_box.maxX for b in blocks if b.bounding_box]
    if not min_xs:
        return 0.0, float(page_width)
    return float(np_median(min_xs)), float(np_median(max_xs))


def _detect_column_split(
    lines: List[Block], page_width: int
) -> tuple[List[Block], List[Block]] | None:
    """
    Detect whether a set of lines represents a two-column layout.

    Returns (left_lines, right_lines) sorted by Y if two distinct columns are
    found, or None for a single-column block.

    Two strategies are tried in order:

    **Strategy 1 — line-level minX clustering**: in a two-column layout the left
    edges of lines cluster around two distinct values separated by the gutter.
    Works when the OCR engine correctly assigns each line to one column.

    **Strategy 2 — word-level gap detection** (fallback): some OCR engines scan
    left-to-right across the full page and stitch words from both columns into a
    single "line". In that case all lines share roughly the same minX and
    strategy 1 sees no gap. Instead we collect all words, sort by center X, and
    look for the largest inter-word gap. Lines that span the gutter are split into
    two new LINE blocks reconstructed from their word subsets.
    """
    if len(lines) < 4:
        return None

    bbox_max_x = max(
        (l.bounding_box.maxX for l in lines if l.bounding_box),
        default=float(page_width),
    )
    # OCR pipelines may provide normalized [0,1] coordinates while keeping
    # page_width in pixels. Use the coordinate system of the line boxes for
    # all gap/width thresholds.
    coord_width = 1.0 if bbox_max_x <= 2.0 else float(page_width)

    # ── Strategy 1: line-level minX clustering ─────────────────────────
    bbox_lines = [(l.bounding_box.minX, l) for l in lines if l.bounding_box]
    if len(bbox_lines) >= 4:
        bbox_lines.sort(key=lambda t: t[0])
        xs = [t[0] for t in bbox_lines]
        gaps = [(xs[i + 1] - xs[i], i) for i in range(len(xs) - 1)]
        max_gap, split_idx = max(gaps, key=lambda g: g[0])

        if max_gap >= 0.10 * coord_width:
            left_count = split_idx + 1
            right_count = len(xs) - left_count
            if left_count >= 2 and right_count >= 2:
                left_std = float(np_std(xs[:left_count]))
                right_std = float(np_std(xs[left_count:]))
                if left_std <= 0.08 * coord_width and right_std <= 0.08 * coord_width:
                    split_x = (xs[split_idx] + xs[split_idx + 1]) / 2.0
                    left_lines = sorted(
                        [
                            l
                            for l in lines
                            if l.bounding_box and l.bounding_box.minX <= split_x
                        ],
                        key=lambda l: l.bounding_box.minY if l.bounding_box else 0,
                    )
                    right_lines = sorted(
                        [
                            l
                            for l in lines
                            if l.bounding_box and l.bounding_box.minX > split_x
                        ],
                        key=lambda l: l.bounding_box.minY if l.bounding_box else 0,
                    )
                    if left_lines and right_lines:
                        left_max_x = max(
                            l.bounding_box.maxX for l in left_lines if l.bounding_box
                        )
                        right_min_x = min(
                            l.bounding_box.minX for l in right_lines if l.bounding_box
                        )
                        if left_max_x < right_min_x:
                            return left_lines, right_lines

    # ── Strategy 2: word-level gap detection ───────────────────────────
    # Collect all words and sort by horizontal centre.
    all_words = list(itertools.chain.from_iterable(l.words for l in lines))
    if len(all_words) < 4:
        return None

    all_words.sort(
        key=lambda w: (
            (w.bounding_box.minX + w.bounding_box.maxX) / 2.0 if w.bounding_box else 0.0
        )
    )

    # Find the largest inter-word gap (space between adjacent word edges).
    best_gap = 0.0
    gutter_x = 0.0
    for i in range(len(all_words) - 1):
        wb_cur = all_words[i].bounding_box
        wb_next = all_words[i + 1].bounding_box
        if wb_cur and wb_next:
            gap = wb_next.minX - wb_cur.maxX
            mid = (wb_cur.maxX + wb_next.minX) / 2.0
            if gap > best_gap:
                best_gap = gap
                gutter_x = mid

    if best_gap < 0.10 * coord_width:
        return None

    # Gutter must sit in the middle 60 % of the page to avoid confusing a
    # large left indent or a right-margin space with a column boundary.
    if gutter_x < 0.20 * coord_width or gutter_x > 0.80 * coord_width:
        return None

    # Reconstruct per-column lines from the word groups.  Lines that span the
    # gutter (OCR merged both columns into one line) are split into two new
    # LINE blocks constructed from their word subsets.
    from pd_book_tools.ocr.block import BlockChildType

    left_lines_out: List[Block] = []
    right_lines_out: List[Block] = []

    for line in lines:
        left_words = [
            w for w in line.words if w.bounding_box and w.bounding_box.minX <= gutter_x
        ]
        right_words = [
            w for w in line.words if w.bounding_box and w.bounding_box.minX > gutter_x
        ]

        if left_words and right_words:
            # Line straddles the gutter — create two new LINE blocks.
            left_lines_out.append(
                Block(
                    items=left_words,
                    child_type=BlockChildType.WORDS,
                    block_category=BlockCategory.LINE,
                )
            )
            right_lines_out.append(
                Block(
                    items=right_words,
                    child_type=BlockChildType.WORDS,
                    block_category=BlockCategory.LINE,
                )
            )
        elif left_words:
            left_lines_out.append(line)
        elif right_words:
            right_lines_out.append(line)

    if not left_lines_out or not right_lines_out:
        return None

    left_lines_out.sort(key=lambda l: l.bounding_box.minY if l.bounding_box else 0)
    right_lines_out.sort(key=lambda l: l.bounding_box.minY if l.bounding_box else 0)

    return left_lines_out, right_lines_out


def _detect_mixed_column_split(
    lines: List[Block], page_width: int
) -> tuple[List[Block], List[Block], List[Block]] | None:
    """Detect a two-column region followed by full-width lines in one row block.

    Some pages contain side-by-side figure captions and then resume normal
    body text immediately below. When all of these lines land in a single
    row block, strict two-column splitting fails because full-width lines
    overlap both columns. This helper extracts:

    - left column lines
    - right column lines
    - trailing full-width (gutter-spanning) lines
    """
    bbox_lines = [l for l in lines if l.bounding_box]
    if len(bbox_lines) < 6:
        return None

    bbox_max_x = max(
        (l.bounding_box.maxX for l in bbox_lines if l.bounding_box),
        default=float(page_width),
    )
    coord_width = 1.0 if bbox_max_x <= 2.0 else float(page_width)

    # Ignore tiny OCR artifacts and full-width body lines when discovering
    # caption columns. Artifacts can create false split points and wide
    # lines can dominate minX statistics.
    candidate_lines = [
        l
        for l in bbox_lines
        if l.bounding_box
        and l.bounding_box.width >= 0.15 * coord_width
        and l.bounding_box.width <= 0.75 * coord_width
        and len((l.text or "").strip()) >= 3
    ]
    if len(candidate_lines) < 4:
        return None

    xs = sorted(l.bounding_box.minX for l in candidate_lines if l.bounding_box)
    if len(xs) < 4:
        return None

    gaps = [(xs[i + 1] - xs[i], i) for i in range(len(xs) - 1)]
    max_gap, split_idx = max(gaps, key=lambda g: g[0])
    if max_gap < 0.10 * coord_width:
        return None

    split_x = (xs[split_idx] + xs[split_idx + 1]) / 2.0
    if split_x < 0.20 * coord_width or split_x > 0.80 * coord_width:
        return None

    widths = sorted(l.bounding_box.width for l in candidate_lines if l.bounding_box)
    if not widths:
        return None

    avg_h = float(
        np_mean([l.bounding_box.height for l in bbox_lines if l.bounding_box] or [1])
    )

    # Separate narrow caption lines from wide full-width body lines.
    # Keep a high floor so long caption lines are not misclassified as
    # full-width body text.
    if len(widths) >= 2:
        width_gaps = [(widths[i + 1] - widths[i], i) for i in range(len(widths) - 1)]
        max_w_gap, max_w_idx = max(width_gaps, key=lambda t: t[0])
        adaptive_wide_threshold = (
            (widths[max_w_idx] + widths[max_w_idx + 1]) / 2.0
            if max_w_gap >= 0.10 * coord_width
            else 0.75 * coord_width
        )
    else:
        adaptive_wide_threshold = 0.75 * coord_width

    wide_threshold = max(0.75 * coord_width, adaptive_wide_threshold)

    # Identify the vertical band where both left and right narrow flows are
    # present. This captures float/caption regions and avoids classifying
    # unrelated lines above/below as part of a side-flow layout.
    left_flow_candidates = [
        l
        for l in candidate_lines
        if l.bounding_box and l.bounding_box.horizontal_midpoint <= split_x
    ]
    right_flow_candidates = [
        l
        for l in candidate_lines
        if l.bounding_box and l.bounding_box.horizontal_midpoint > split_x
    ]
    if len(left_flow_candidates) < 2 or len(right_flow_candidates) < 2:
        return None

    left_min_y = min(
        l.bounding_box.minY for l in left_flow_candidates if l.bounding_box
    )
    left_max_y = max(
        l.bounding_box.maxY for l in left_flow_candidates if l.bounding_box
    )
    right_min_y = min(
        l.bounding_box.minY for l in right_flow_candidates if l.bounding_box
    )
    right_max_y = max(
        l.bounding_box.maxY for l in right_flow_candidates if l.bounding_box
    )

    y_pad = max(1.5 * avg_h, 0.005 * coord_width)
    flow_band_start = max(left_min_y, right_min_y) - y_pad
    flow_band_end = min(left_max_y, right_max_y) + y_pad
    if flow_band_end <= flow_band_start:
        return None

    left_lines: List[Block] = []
    right_lines: List[Block] = []
    spanning_lines: List[Block] = []
    min_column_line_width = 0.12 * coord_width

    for line in lines:
        bb = line.bounding_box
        if not bb:
            spanning_lines.append(line)
            continue

        text = (line.text or "").strip()
        is_tiny_artifact = bb.width < min_column_line_width and len(text) < 3
        very_wide = bb.width >= wide_threshold
        in_flow_band = flow_band_start <= bb.vertical_midpoint <= flow_band_end

        if not in_flow_band:
            spanning_lines.append(line)
        elif very_wide or is_tiny_artifact:
            spanning_lines.append(line)
        elif bb.width < min_column_line_width:
            spanning_lines.append(line)
        elif bb.horizontal_midpoint <= split_x:
            left_lines.append(line)
        elif bb.horizontal_midpoint > split_x:
            right_lines.append(line)
        else:
            spanning_lines.append(line)

    if len(left_lines) < 2 or len(right_lines) < 2 or not spanning_lines:
        return None

    left_lines.sort(key=lambda l: l.bounding_box.minY if l.bounding_box else 0)
    right_lines.sort(key=lambda l: l.bounding_box.minY if l.bounding_box else 0)
    spanning_lines.sort(key=lambda l: l.bounding_box.minY if l.bounding_box else 0)

    # Reject when spanning lines start far above the columns AND actually span
    # both column regions.  When all early spanning lines are confined to one
    # column side (e.g. right-column body text flowing around a left figure),
    # the layout is a valid floated-figure pattern and we should not reject.
    col_min_y = min(
        [l.bounding_box.minY for l in left_lines + right_lines if l.bounding_box]
    )
    span_min_y = min(l.bounding_box.minY for l in spanning_lines if l.bounding_box)
    if span_min_y < col_min_y - (0.50 * avg_h):
        early_span = [
            l
            for l in spanning_lines
            if l.bounding_box and l.bounding_box.minY < col_min_y
        ]
        if not early_span:
            return None
        early_mids = [
            l.bounding_box.horizontal_midpoint for l in early_span if l.bounding_box
        ]
        all_one_side = all(x > split_x for x in early_mids) or all(
            x <= split_x for x in early_mids
        )
        if not all_one_side:
            return None

    # Ensure deterministic left/right assignment even if split_x is noisy.
    left_median_x = float(np_median([l.bounding_box.minX for l in left_lines]))
    right_median_x = float(np_median([l.bounding_box.minX for l in right_lines]))
    if left_median_x > right_median_x:
        left_lines, right_lines = right_lines, left_lines

    return left_lines, right_lines, spanning_lines


def _detect_floated_flow_span(
    lines: List[Block],
    page_width: int,
) -> tuple[List[Block], List[Block], List[Block], List[Block], List[Block]] | None:
    """Detect a floated-content span by geometric left/right flow overlap.

    Returns (pre_lines, left_flow, right_flow, band_body_lines, post_lines)
    when a vertical band contains concurrent left/right text flows.
    """
    bbox_lines = [l for l in lines if l.bounding_box]
    if len(bbox_lines) < 8:
        return None

    bbox_max_x = max(
        (l.bounding_box.maxX for l in bbox_lines if l.bounding_box),
        default=float(page_width),
    )
    coord_width = 1.0 if bbox_max_x <= 2.0 else float(page_width)

    widths = [l.bounding_box.width for l in bbox_lines if l.bounding_box]
    median_w = float(np_median(widths)) if widths else 0.0
    avg_h = float(
        np_mean([l.bounding_box.height for l in bbox_lines if l.bounding_box] or [1])
    )
    if median_w <= 0:
        return None

    body_like = [
        l
        for l in bbox_lines
        if l.bounding_box and l.bounding_box.width >= 0.92 * median_w
    ]
    if body_like:
        body_left = float(
            np_median([l.bounding_box.minX for l in body_like if l.bounding_box])
        )
        body_right = float(
            np_median([l.bounding_box.maxX for l in body_like if l.bounding_box])
        )
    else:
        body_left = float(
            np_median([l.bounding_box.minX for l in bbox_lines if l.bounding_box])
        )
        body_right = float(
            np_median([l.bounding_box.maxX for l in bbox_lines if l.bounding_box])
        )

    squeezed = [
        l
        for l in bbox_lines
        if l.bounding_box and l.bounding_box.width <= 0.86 * median_w
    ]
    if len(squeezed) < 6:
        return None

    squeezed_sorted = sorted(
        squeezed,
        key=lambda l: l.bounding_box.minX if l.bounding_box else 0,
    )
    x_gap = 0.12 * coord_width
    clusters: List[List[Block]] = []
    current: List[Block] = []
    prev_x = None
    for line in squeezed_sorted:
        x = line.bounding_box.minX if line.bounding_box else 0
        if prev_x is None or (x - prev_x) < x_gap:
            current.append(line)
        else:
            clusters.append(current)
            current = [line]
        prev_x = x
    if current:
        clusters.append(current)

    clusters = [
        c
        for c in clusters
        if len(c) >= 3
        and float(np_std([l.bounding_box.minX for l in c if l.bounding_box]))
        <= 0.09 * coord_width
    ]
    if len(clusters) < 2:
        return None

    clusters = sorted(
        clusters,
        key=lambda c: float(
            np_median([l.bounding_box.minX for l in c if l.bounding_box])
        ),
    )[:2]
    left_cluster, right_cluster = clusters[0], clusters[1]

    left_center = float(
        np_median([l.bounding_box.minX for l in left_cluster if l.bounding_box])
    )
    right_center = float(
        np_median([l.bounding_box.minX for l in right_cluster if l.bounding_box])
    )
    if (right_center - left_center) < 0.14 * coord_width:
        return None

    isolate_left = abs(left_center - body_left) > 0.07 * coord_width
    isolate_right = (
        abs(right_center - body_right) > 0.07 * coord_width
        or right_center > body_left + 0.10 * coord_width
    )

    right_y0 = min(l.bounding_box.minY for l in right_cluster if l.bounding_box)
    right_y1 = max(l.bounding_box.maxY for l in right_cluster if l.bounding_box)

    y_pad = max(1.2 * avg_h, 0.004 * coord_width)
    # Anchor floated span to the shifted/right flow range, then require
    # left-flow presence within that range.
    band_start = right_y0 - y_pad
    band_end = right_y1 + y_pad
    if band_end <= band_start:
        return None
    if (band_end - band_start) < 3.0 * avg_h:
        return None

    left_in_band = [
        l
        for l in left_cluster
        if l.bounding_box and band_start <= l.bounding_box.vertical_midpoint <= band_end
    ]
    if len(left_in_band) < 2:
        return None

    pre_lines: List[Block] = []
    left_flow: List[Block] = []
    right_flow: List[Block] = []
    band_body: List[Block] = []
    post_lines: List[Block] = []

    for line in lines:
        bb = line.bounding_box
        if not bb:
            band_body.append(line)
            continue

        y_mid = bb.vertical_midpoint
        if y_mid < band_start:
            pre_lines.append(line)
            continue
        if y_mid > band_end:
            post_lines.append(line)
            continue

        # Keep lines that follow normal body margins out of float assignment.
        is_body_baseline = abs(
            bb.minX - body_left
        ) <= 0.06 * coord_width and bb.maxX >= body_right - (0.08 * coord_width)
        if is_body_baseline:
            band_body.append(line)
            continue

        d_left = abs(bb.minX - left_center)
        d_right = abs(bb.minX - right_center)
        if d_left <= 0.14 * coord_width and d_left < d_right:
            if isolate_left:
                left_flow.append(line)
            else:
                band_body.append(line)
        elif d_right <= 0.14 * coord_width and d_right < d_left:
            if isolate_right:
                right_flow.append(line)
            else:
                band_body.append(line)
        else:
            band_body.append(line)

    isolated_flow_count = (1 if len(left_flow) >= 2 else 0) + (
        1 if len(right_flow) >= 2 else 0
    )
    if isolated_flow_count < 2:
        # Require both flows to be non-trivial so that two-column caption blocks
        # (where one cluster sits at the body left margin, making isolate_left=False
        # and left_flow empty) fall through to _detect_mixed_column_split instead.
        return None

    pre_lines.sort(key=_yx_sort_key)
    left_flow.sort(key=_yx_sort_key)
    right_flow.sort(key=_yx_sort_key)
    band_body.sort(key=_yx_sort_key)
    post_lines.sort(key=_yx_sort_key)

    return pre_lines, left_flow, right_flow, band_body, post_lines


def _detect_multi_column_split(
    lines: List[Block], page_width: int
) -> tuple[List[List[Block]], List[Block]] | None:
    """Detect and isolate multi-column regions (2-3 columns) plus spanning lines."""
    bbox_lines = [l for l in lines if l.bounding_box]
    if len(bbox_lines) < 6:
        return None

    bbox_max_x = max(
        (l.bounding_box.maxX for l in bbox_lines if l.bounding_box),
        default=float(page_width),
    )
    coord_width = 1.0 if bbox_max_x <= 2.0 else float(page_width)

    candidate_lines = [
        l
        for l in bbox_lines
        if l.bounding_box
        and l.bounding_box.width >= 0.12 * coord_width
        and l.bounding_box.width <= 0.72 * coord_width
        and len((l.text or "").strip()) >= 3
    ]
    if len(candidate_lines) < 4:
        return None

    sorted_candidates = sorted(
        candidate_lines,
        key=lambda l: l.bounding_box.minX if l.bounding_box else 0,
    )
    gap_threshold = 0.09 * coord_width

    clusters: List[List[Block]] = []
    current_cluster: List[Block] = []
    prev_x = None
    for line in sorted_candidates:
        x = line.bounding_box.minX if line.bounding_box else 0
        if prev_x is None or (x - prev_x) < gap_threshold:
            current_cluster.append(line)
        else:
            clusters.append(current_cluster)
            current_cluster = [line]
        prev_x = x
    if current_cluster:
        clusters.append(current_cluster)

    # Keep well-formed clusters; cap at three columns for stability.
    valid_clusters = [
        c
        for c in clusters
        if len(c) >= 3
        and float(np_std([l.bounding_box.minX for l in c if l.bounding_box]))
        <= 0.08 * coord_width
    ]
    if len(valid_clusters) < 2:
        return None
    if len(valid_clusters) > 3:
        valid_clusters = sorted(valid_clusters, key=len, reverse=True)[:3]

    centers = [
        float(np_median([l.bounding_box.minX for l in c if l.bounding_box]))
        for c in valid_clusters
    ]
    center_pairs = sorted(zip(centers, valid_clusters), key=lambda t: t[0])
    centers = [c for c, _ in center_pairs]

    # Require at least one clearly separated anchor gap; if all centers are
    # too close, this is likely a single flow with indentation noise.
    center_gaps = [centers[i + 1] - centers[i] for i in range(len(centers) - 1)]
    if not center_gaps or max(center_gaps) < 0.10 * coord_width:
        return None

    widths = [l.bounding_box.width for l in candidate_lines if l.bounding_box]
    median_w = float(np_median(widths)) if widths else 0.0
    wide_threshold = max(0.78 * coord_width, 1.30 * median_w)

    column_lines: List[List[Block]] = [[] for _ in centers]
    spanning_lines: List[Block] = []

    for line in lines:
        bb = line.bounding_box
        if not bb:
            spanning_lines.append(line)
            continue

        if bb.width >= wide_threshold:
            spanning_lines.append(line)
            continue

        line_mid = bb.horizontal_midpoint
        distances = sorted(
            [(abs(line_mid - centers[i]), i) for i in range(len(centers))],
            key=lambda t: t[0],
        )
        nearest_dist, nearest_idx = distances[0]
        second_dist = distances[1][0] if len(distances) > 1 else float("inf")

        # If line is far from any anchor or nearly equidistant between two
        # anchors, do not force it into a column (partial-separation case).
        ambiguous_assignment = (
            second_dist < float("inf")
            and (nearest_dist / max(second_dist, 1e-6)) > 0.72
        )
        if nearest_dist > 0.18 * coord_width or ambiguous_assignment:
            spanning_lines.append(line)
            continue
        column_lines[nearest_idx].append(line)

    # Require at least two non-trivial columns to classify as multi-column.
    column_lines = [c for c in column_lines if len(c) >= 2]
    if len(column_lines) < 2:
        return None

    # Validate that detected columns are part of the same vertical region.
    # If Y ranges barely overlap, this is likely a false split across unrelated
    # sections rather than a true multi-column segment.
    col_ranges = [
        (
            min(l.bounding_box.minY for l in c if l.bounding_box),
            max(l.bounding_box.maxY for l in c if l.bounding_box),
        )
        for c in column_lines
        if any(l.bounding_box for l in c)
    ]
    if len(col_ranges) >= 2:
        global_min = min(r[0] for r in col_ranges)
        global_max = max(r[1] for r in col_ranges)
        overlap_top = max(r[0] for r in col_ranges)
        overlap_bottom = min(r[1] for r in col_ranges)
        overlap_h = max(0.0, overlap_bottom - overlap_top)
        global_h = max(1e-6, global_max - global_min)
        if overlap_h < 0.20 * global_h:
            return None

    # If spanning content begins far above detected columns, do not split:
    # this usually means we accidentally mixed normal body flow with a small
    # later narrow-run rather than identifying a true column region.
    if spanning_lines and col_ranges:
        span_min_y = min(l.bounding_box.minY for l in spanning_lines if l.bounding_box)
        col_min_y = min(r[0] for r in col_ranges)
        avg_h = float(
            np_mean(
                [l.bounding_box.height for l in bbox_lines if l.bounding_box] or [1]
            )
        )
        if span_min_y < col_min_y - (2.0 * avg_h):
            return None

    for c in column_lines:
        c.sort(key=lambda l: l.bounding_box.minY if l.bounding_box else 0)
    spanning_lines.sort(key=lambda l: l.bounding_box.minY if l.bounding_box else 0)

    return column_lines, spanning_lines


def _merge_isolated_columns_into_flow(
    column_groups: List[List[Block]],
    spanning_lines: List[Block] | None = None,
) -> List[Block]:
    """Merge isolated column groups back into a single standard reading flow."""
    if not column_groups:
        return sorted(
            spanning_lines or [],
            key=lambda l: (
                l.bounding_box.minY if l.bounding_box else 0,
                l.bounding_box.minX if l.bounding_box else 0,
            ),
        )

    ordered_groups = sorted(
        column_groups,
        key=lambda g: float(
            np_median([l.bounding_box.minX for l in g if l.bounding_box] or [0])
        ),
    )

    merged_lines: List[Block] = []
    for group in ordered_groups:
        merged_lines.extend(
            sorted(
                group,
                key=lambda l: (
                    l.bounding_box.minY if l.bounding_box else 0,
                    l.bounding_box.minX if l.bounding_box else 0,
                ),
            )
        )

    if spanning_lines:
        merged_lines.extend(
            sorted(
                spanning_lines,
                key=lambda l: (
                    l.bounding_box.minY if l.bounding_box else 0,
                    l.bounding_box.minX if l.bounding_box else 0,
                ),
            )
        )

    return merged_lines


def _split_caption_like_prefix(
    flow_lines: List[Block],
    page_width: int,
) -> tuple[List[Block], List[Block]]:
    """Split a compact top prefix from a flow as caption-like content.

    Uses only geometric cues: a dense run of lines at the top of a side flow
    followed by a clear vertical gap.
    """
    if len(flow_lines) < 3:
        return [], list(flow_lines)

    sorted_lines = sorted(
        flow_lines,
        key=lambda l: (
            l.bounding_box.minY if l.bounding_box else 0,
            l.bounding_box.minX if l.bounding_box else 0,
        ),
    )
    bbox_lines = [l for l in sorted_lines if l.bounding_box]
    if len(bbox_lines) < 3:
        return [], sorted_lines

    avg_h = float(
        np_mean([l.bounding_box.height for l in bbox_lines if l.bounding_box] or [1])
    )
    coord_width = float(page_width)
    gap_threshold = max(1.8 * avg_h, 0.008 * coord_width)

    split_idx = None
    for idx in range(len(sorted_lines) - 1):
        a = sorted_lines[idx].bounding_box
        b = sorted_lines[idx + 1].bounding_box
        if not a or not b:
            continue
        gap = b.minY - a.maxY
        if gap > gap_threshold:
            split_idx = idx
            break

    if split_idx is None:
        return [], sorted_lines

    prefix = sorted_lines[: split_idx + 1]
    suffix = sorted_lines[split_idx + 1 :]
    if len(prefix) < 2 or not suffix:
        return [], sorted_lines

    prefix_xs = [l.bounding_box.minX for l in prefix if l.bounding_box]
    if len(prefix_xs) >= 2 and float(np_std(prefix_xs)) > 0.035 * coord_width:
        return [], sorted_lines

    return prefix, suffix


# ─────────────────────────────────────────────────────────────────────────────
# Step L — classify a row block as page header / footer / sidenote / poetry /
# blockquote / body. Geometry-first; falls back on no-classification (body).
# ─────────────────────────────────────────────────────────────────────────────


def _classify_row_block(
    block: Block,
    page_width: int,
    page_height: int,
    body_minX: float,
    body_maxX: float,
    page_median_line_width: float,
    ocr_minY: float,
    ocr_maxY: float,
    avg_line_height: float,
) -> str | None:
    """
    Classify a row block for special handling.

    Returns one of: 'page header', 'page footer', 'sidenote left',
    'sidenote right', 'poetry', 'blockquote', or None (normal body text).
    """
    if not block.bounding_box:
        return None
    lines = block.lines
    if not lines:
        return None

    # Page header: must be near the top of BOTH the image and the OCR content.
    # Checking both prevents chapter headings and title-page text from being
    # misidentified — those are near the top of the OCR extent but not always
    # near the top of the image, or vice-versa.
    near_top_of_image = block.bounding_box.minY < 0.12 * page_height
    near_top_of_ocr = block.bounding_box.minY <= ocr_minY + 1.5 * avg_line_height
    if near_top_of_image and near_top_of_ocr and len(lines) <= 3:
        return "page header"

    # Page footer: same dual check against image bottom and OCR content bottom.
    near_bottom_of_image = block.bounding_box.maxY > 0.88 * page_height
    near_bottom_of_ocr = block.bounding_box.maxY >= ocr_maxY - 1.5 * avg_line_height
    if near_bottom_of_image and near_bottom_of_ocr and len(lines) <= 3:
        return "page footer"

    # Sidenotes: block X extent lies entirely outside the main body region
    margin = 0.02 * page_width
    if block.bounding_box.maxX < body_minX - margin:
        return "sidenote left"
    if block.bounding_box.minX > body_maxX + margin:
        return "sidenote right"

    # Poetry / blockquote: lines significantly narrower than body and left-indented
    if page_median_line_width > 0 and len(lines) >= 2:
        line_widths = [l.bounding_box.width for l in lines if l.bounding_box]
        if line_widths:
            block_median_width = float(np_median(line_widths))
            if block_median_width < 0.75 * page_median_line_width:
                line_min_xs = [l.bounding_box.minX for l in lines if l.bounding_box]
                block_left = float(np_median(line_min_xs)) if line_min_xs else body_minX
                if block_left > body_minX + 0.03 * page_width:
                    # Poetry: right edges vary a lot (lines of different lengths)
                    line_max_xs = [l.bounding_box.maxX for l in lines if l.bounding_box]
                    right_std = (
                        float(np_std(line_max_xs)) if len(line_max_xs) > 1 else 0.0
                    )
                    if right_std > 0.05 * page_width:
                        return "poetry"
                    return "blockquote"

    return None
