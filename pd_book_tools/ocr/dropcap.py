"""Cursive / decorative drop-cap recognition fallback.

Iteration A. Runs after the geometric block-cap stitcher
(``reorganize_page_utils.stitch_drop_caps``) has had its turn. The
block-cap path catches plain Roman caps the OCR model already
recognised; this module catches the cases where OCR mis-read or
skipped the oversized initial glyph entirely — typical for serif /
italic / decorative caps the recogniser hasn't been trained on.

See the ROADMAP entry "Drop-cap glyph recognition for cursive /
decorative caps" for the full Q1-Q7 design rationale; this module is
the iteration-A implementation of that spec.

Public surface:

    detect_and_stitch_cursive_dropcaps(blocks, image, metrics) -> list[Block]

Signature mirrors :func:`reorganize_page_utils.stitch_drop_caps` so it
slots in as a fallback. Returns the (possibly modified) ``blocks``
list. On any internal failure the original list comes back unchanged
plus a ``logger.warning`` and a ``"drop cap unrecovered"`` tag on the
closest body word — never silent, never raises.
"""

from __future__ import annotations

import string
from dataclasses import dataclass
from logging import getLogger
from typing import TYPE_CHECKING, Optional

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr._dropcap_lexicon import WORDS as _LEXICON
from pd_book_tools.ocr.block import Block, BlockCategory
from pd_book_tools.ocr.word import Word

if TYPE_CHECKING:
    import numpy as np

    from pd_book_tools.ocr.reorganize_page_utils import PageMetrics


logger = getLogger(__name__)


# Roles that the block-cap stitcher already skips. The cursive fallback
# applies the same skip list — drop caps only appear in body text.
_SKIP_ROLES: frozenset[str] = frozenset(
    {
        "page header",
        "page footer",
        "sidenote",
        "poetry",
        "blockquote",
        "recovered",
        "page number",
        "printers mark",
    }
)


# Geometric-trigger thresholds. Tuned against the three known
# regression fixtures (chapter-head-credulities, chapter-head-filial-duty,
# footnotes-stacked-with-anchor). All values are in normalised coordinate
# space (page width = 1.0).
#
# A real drop-cap-induced indent is ~2-3 cap-glyph widths of blank
# space to the left of the first body word, vs. a regular paragraph
# indent of ~1-2 em. We guard against false positives with a
# multi-line check (lines 2-3 of the same paragraph must also be
# indented vs. the page's body-left margin).
_MIN_INDENT_DELTA = 0.025  # body word's minX must exceed body-left by this
_MAX_INDENT_DELTA = 0.10  # body word's minX must NOT exceed body-left by more
# than this (centered chapter titles can sit ≥0.20 past body-left; not a cap)
_MULTI_LINE_INDENT_TOLERANCE = 0.02  # lines 2-3 indented within this of cap line
_CAP_HEIGHT_RATIO_MIN = 1.5  # cap CC's height ≥ this × median_word_h


@dataclass(frozen=True)
class _IndentSignature:
    """Per-page paragraph-indent statistics.

    ``body_left`` is the median minX across body lines (the "page left
    margin"). ``standard_indent`` is the median *first-line indent*
    relative to ``body_left`` for normal paragraphs — used as the
    upper bound of "this is just a regular indent, not a drop-cap
    gap".
    """

    body_left: float
    standard_indent: float


@dataclass(frozen=True)
class _GapCandidate:
    """A first-line that looks like a drop-cap indent.

    Captures everything a CC scan needs to confirm: the body word
    abutting the gap, the y-band (top/bottom of the body line), and
    the x-range of the gap itself.
    """

    block: Block
    paragraph: Block
    target_line: Block
    first_body_word: Word
    gap_minX: float
    gap_maxX: float
    line_minY: float
    line_maxY: float
    body_line_height: float


def _block_role_skipped(block: Block) -> bool:
    roles = block.block_role_labels or []
    return any(r in _SKIP_ROLES for r in roles)


def _all_lines(block: Block) -> list[tuple[Block, Block]]:
    """Flatten BLOCK → PARAGRAPH → LINE; return ``(paragraph, line)`` pairs.

    The pairing is needed so the gap-candidate logic can recompute the
    enclosing paragraph's bbox after stitching.
    """
    out: list[tuple[Block, Block]] = []
    for paragraph in block.items:
        if not isinstance(paragraph, Block):
            continue
        if paragraph.block_category != BlockCategory.PARAGRAPH:
            continue
        for child in paragraph.items:
            if not isinstance(child, Block):
                continue
            if child.block_category == BlockCategory.LINE:
                out.append((paragraph, child))
    return out


def _compute_indent_signature(blocks: list[Block]) -> Optional[_IndentSignature]:
    """Compute the page's body-left margin + typical paragraph indent.

    ``body_left`` = modal minX across non-skipped body lines (the
    page's left margin). ``standard_indent`` = median first-line
    indent measured ONLY in multi-line paragraphs whose continuation
    lines hug ``body_left`` (i.e. real body paragraphs, not chapter
    heads or centered titles whose minX swings wildly).

    Returns ``None`` if there isn't enough body geometry.
    """
    body_lefts: list[float] = []
    multi_line_paragraphs: list[list[Block]] = []

    for block in blocks:
        if _block_role_skipped(block):
            continue
        for paragraph in block.items:
            if not isinstance(paragraph, Block):
                continue
            if paragraph.block_category != BlockCategory.PARAGRAPH:
                continue
            line_children = [
                c
                for c in paragraph.items
                if isinstance(c, Block) and c.block_category == BlockCategory.LINE
            ]
            if not line_children:
                continue
            for line in line_children:
                if line.bounding_box is None:
                    continue
                body_lefts.append(line.bounding_box.minX)
            if len(line_children) >= 2:
                multi_line_paragraphs.append(line_children)

    if not body_lefts:
        return None

    # Modal-ish body-left: take the lowest decile-of-the-distribution
    # to avoid centered titles dragging the median rightward.
    body_lefts.sort()
    cutoff = max(1, int(0.30 * len(body_lefts)))
    body_left = sorted(body_lefts[:cutoff])[len(body_lefts[:cutoff]) // 2]

    indents: list[float] = []
    body_left_tolerance = 0.02
    for line_children in multi_line_paragraphs:
        first = line_children[0]
        rest = line_children[1:]
        rest_minX = [l.bounding_box.minX for l in rest if l.bounding_box is not None]
        if first.bounding_box is None or not rest_minX:
            continue
        rest_minX.sort()
        rest_median = rest_minX[len(rest_minX) // 2]
        # Only use this paragraph's indent measurement if its
        # continuation lines hug the body-left margin (real body
        # paragraph, not a centered or right-margined block).
        if abs(rest_median - body_left) > body_left_tolerance:
            continue
        indent = first.bounding_box.minX - rest_median
        if indent > 0:
            indents.append(indent)

    if indents:
        indents.sort()
        standard_indent = indents[len(indents) // 2]
    else:
        # No usable body paragraphs to compare against. Pick a small
        # default — typical print indent ~0.025-0.04 of page width.
        standard_indent = 0.03

    return _IndentSignature(body_left=body_left, standard_indent=standard_indent)


def _geometric_gap_candidates(
    blocks: list[Block], indent: _IndentSignature
) -> list[_GapCandidate]:
    """Find body lines whose minX is abnormally indented, with the
    *next line below* (in reading order, even if it's in a different
    paragraph) also indented.

    A real drop-cap gap is *much* larger than a normal paragraph
    indent. We require the body-word minX to be at least
    ``_MIN_INDENT_DELTA`` past the standard-indent boundary. To
    suppress false positives on a regular indent that happens to be
    wide (small-format printings), we require the immediate next line
    in reading order to share the indent (the drop-cap glyph wraps 2
    body lines around itself, and the paragraph splitter often puts
    those lines into different paragraphs because of the indent
    discontinuity).
    """
    candidates: list[_GapCandidate] = []
    indent_threshold = indent.body_left + indent.standard_indent + _MIN_INDENT_DELTA

    for block in blocks:
        if _block_role_skipped(block):
            continue
        all_lines = _all_lines(block)
        # Sort by minY so we walk in reading order regardless of how
        # the paragraph splitter assigned each line.
        all_lines.sort(
            key=lambda pl: (
                pl[1].bounding_box.minY if pl[1].bounding_box is not None else 0.0
            )
        )
        for idx, (paragraph, line) in enumerate(all_lines):
            if line.bounding_box is None:
                continue
            words = [w for w in line.words if (w.text or "").strip()]
            if not words:
                continue
            words_sorted = sorted(
                words, key=lambda w: w.bounding_box.minX if w.bounding_box else 0.0
            )
            # The "first body word" for trigger purposes is the first
            # word that looks like real text. OCR sometimes returns a
            # short artifact (single dash, stray glyph, punctuation
            # only) at the cap location; those are precisely what the
            # cap CC will eventually replace. Skip such tokens when
            # measuring the gap. Real short words like "to" / "of" /
            # "is" are kept (they're alphabetic).
            first_body_word: Optional[Word] = None
            for w in words_sorted:
                if w.bounding_box is None:
                    continue
                t = (w.text or "").strip()
                if not t:
                    continue
                # Skip artifacts: single-character non-alphabetic
                # tokens (e.g. "-", ")", ">"), or any token that has
                # no alphabetic characters at all.
                if not any(ch.isalpha() for ch in t):
                    continue
                first_body_word = w
                break
            if first_body_word is None:
                continue
            # Geometric trigger: body word starts well to the right of
            # the page's body-left margin, but NOT so far right that
            # this is obviously a centered chapter title.
            if first_body_word.bounding_box.minX < indent_threshold:
                continue
            if first_body_word.bounding_box.minX > indent.body_left + _MAX_INDENT_DELTA:
                continue

            # Look at the next line in reading order. It must exist and
            # also be indented past the body-left (drop-cap wrap), AND
            # it must sit close to the candidate line vertically (within
            # ~2 line heights — eliminates "next paragraph indent" false
            # positives at the bottom of a paragraph).
            if idx + 1 >= len(all_lines):
                continue
            next_para, next_line = all_lines[idx + 1]
            if next_line.bounding_box is None:
                continue
            line_h = line.bounding_box.height
            if next_line.bounding_box.minY > line.bounding_box.maxY + 2 * line_h:
                continue
            # Either the next line is indented, OR it's a *very*
            # short single-token line that is itself the OCR's stab at
            # the cap glyph (the "-" line beneath "NCE" in
            # chapter-head-filial-duty). Both are signals.
            next_indented = (
                next_line.bounding_box.minX
                >= indent.body_left
                + indent.standard_indent
                - _MULTI_LINE_INDENT_TOLERANCE
            )
            next_token_count = sum(1 for w in next_line.words if (w.text or "").strip())
            next_short_artifact = (
                next_token_count <= 1
                and next_line.bounding_box.width <= 2 * line.bounding_box.height
            )
            if not (next_indented or next_short_artifact):
                continue

            # The gap to scan is from the body-left margin (minus a
            # whisker) to just left of the first body word's bbox.
            gap_minX = max(0.0, indent.body_left - 0.005)
            gap_maxX = first_body_word.bounding_box.minX
            line_minY = line.bounding_box.minY
            line_maxY = line.bounding_box.maxY
            body_line_height = line.bounding_box.height

            candidates.append(
                _GapCandidate(
                    block=block,
                    paragraph=paragraph,
                    target_line=line,
                    first_body_word=first_body_word,
                    gap_minX=gap_minX,
                    gap_maxX=gap_maxX,
                    line_minY=line_minY,
                    line_maxY=line_maxY,
                    body_line_height=body_line_height,
                )
            )
    return candidates


def _scan_dropcap_cc(
    image,
    candidate: _GapCandidate,
    metrics: "PageMetrics",
) -> Optional[BoundingBox]:
    """Connected-components scan in the gap region; return the cap CC bbox.

    Threshold the page image, run ``cv2.connectedComponentsWithStats``
    on the cropped gap region, pick the CC that's:

    * at least ``_CAP_HEIGHT_RATIO_MIN × median_word_h`` tall (drop
      caps are 2-3× body height; we set the floor low to admit smaller
      decorated caps),
    * spans more vertical extent than the body line itself (so we
      don't pick up the body word's ascender),
    * sits left of the first body word.

    Returns the cap's bbox in normalised page coordinates, or ``None``.
    """
    if image is None:
        return None
    try:
        import cv2
    except Exception:  # pragma: no cover — cv2 is a hard dep
        return None

    H, W = image.shape[:2]
    if H == 0 or W == 0:
        return None

    # Expand the search band vertically by ~1.5 body-line heights above
    # the body line so we capture the cap's top half (drop caps extend
    # upwards from the body baseline). And by 0.5 body-line heights
    # below to capture the descender area.
    pad_y = max(1.5 * candidate.body_line_height, 0.02)
    band_top = max(0.0, candidate.line_minY - pad_y)
    band_bot = min(1.0, candidate.line_maxY + 0.5 * candidate.body_line_height)

    x1 = int(candidate.gap_minX * W)
    x2 = int(candidate.gap_maxX * W)
    y1 = int(band_top * H)
    y2 = int(band_bot * H)
    # Margin the crop to make sure we don't slice through the glyph.
    if x2 <= x1 + 4 or y2 <= y1 + 4:
        return None
    sub = image[y1:y2, x1:x2]
    if sub.size == 0:
        return None

    if sub.ndim == 3:
        gray = cv2.cvtColor(sub, cv2.COLOR_BGR2GRAY)
    else:
        gray = sub
    # Otsu threshold with inversion so glyph pixels are foreground.
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    n_labels, _, stats, _ = cv2.connectedComponentsWithStats(bw, connectivity=8)

    median_word_h = max(metrics.median_word_h, 1e-6)
    median_h_px = median_word_h * H if metrics.coord_h <= 2.0 else median_word_h
    min_cap_h_px = _CAP_HEIGHT_RATIO_MIN * median_h_px

    best: Optional[tuple[int, int, int, int, int]] = None  # (x, y, w, h, area)
    for i in range(1, n_labels):
        x, y, w, h, area = (
            stats[i, cv2.CC_STAT_LEFT],
            stats[i, cv2.CC_STAT_TOP],
            stats[i, cv2.CC_STAT_WIDTH],
            stats[i, cv2.CC_STAT_HEIGHT],
            stats[i, cv2.CC_STAT_AREA],
        )
        if h < min_cap_h_px:
            continue
        # Reject CCs that are taller than the gap allows (the page
        # margin or a stray decoration).
        if h > 6 * median_h_px:
            continue
        # Reject ultra-thin CCs (vertical rules, page-edge artifacts).
        if w < 0.3 * h:
            continue
        # Reject CCs that touch the left edge of the crop — almost
        # certainly the page margin or a binding artefact, not the
        # decorative cap (which sits inset from the body-left margin).
        if x <= 1:
            continue
        if best is None or area > best[4]:
            best = (x, y, w, h, area)

    if best is None:
        return None
    bx, by, bw, bh, _area = best
    abs_x1 = (x1 + bx) / W
    abs_y1 = (y1 + by) / H
    abs_x2 = (x1 + bx + bw) / W
    abs_y2 = (y1 + by + bh) / H
    # Guard against rounding pushing maxX past the body word's minX
    # (would make Block.recompute_bounding_box reorder the words).
    if abs_x2 > candidate.first_body_word.bounding_box.maxX:
        abs_x2 = min(abs_x2, candidate.first_body_word.bounding_box.minX)
    if abs_x1 >= abs_x2 or abs_y1 >= abs_y2:
        return None
    return BoundingBox.from_ltrb(abs_x1, abs_y1, abs_x2, abs_y2, is_normalized=True)


def _resolve_cap_letter(body_word_text: str) -> Optional[str]:
    """Try every uppercase ASCII letter as a prefix; accept unique match.

    The body word is uppercased before lookup so the function works on
    fixtures where the OCR text is title-cased (``"Tudies"``) or all
    caps (``"UPERSTITIONS"``). Returns the inferred cap letter, or
    ``None`` when 0 or >1 candidates match the lexicon.
    """
    body_upper = (body_word_text or "").strip().upper()
    if not body_upper:
        return None
    # Strip trailing punctuation that OCR may have grabbed onto the
    # body word (commas, full stops, semicolons). The lexicon stores
    # bare words.
    while body_upper and body_upper[-1] in ".,;:!?'\"-)":
        body_upper = body_upper[:-1]
    if not body_upper:
        return None

    matches = [c for c in string.ascii_uppercase if (c + body_upper) in _LEXICON]
    if len(matches) == 1:
        return matches[0]
    return None


def _bboxes_overlap(a: BoundingBox, b: BoundingBox) -> bool:
    """Axis-aligned overlap test."""
    if a.maxX < b.minX or b.maxX < a.minX:
        return False
    if a.maxY < b.minY or b.maxY < a.minY:
        return False
    return True


def _is_cc_overlapping_word(cc_bbox: BoundingBox, word: Word) -> bool:
    """True when ``word``'s bbox overlaps the CC bbox (any overlap)."""
    if word.bounding_box is None:
        return False
    wb = word.bounding_box
    if wb.maxX < cc_bbox.minX or wb.minX > cc_bbox.maxX:
        return False
    if wb.maxY < cc_bbox.minY or wb.minY > cc_bbox.maxY:
        return False
    return True


def _find_existing_cap_word(
    candidate: _GapCandidate, cc_bbox: BoundingBox
) -> Optional[Word]:
    """Return the OCR word that the recogniser placed at the cap CC, if any.

    Matches "single visible character" tokens whose bbox sits within /
    overlaps the CC bbox AND is to the left of the first body word.
    Used to handle the OCR-state branching: gibberish ``"-"`` next to
    the cap should be replaced with the inferred letter.
    """
    line_words = list(candidate.target_line.words)
    for w in line_words:
        if w is candidate.first_body_word:
            continue
        if not (w.text or "").strip():
            continue
        if w.bounding_box is None:
            continue
        # Tiny tokens only — a real cap glyph would be 1-2 chars.
        text = (w.text or "").strip()
        if len(text) > 2:
            continue
        if w.bounding_box.minX >= candidate.first_body_word.bounding_box.minX:
            continue
        if _is_cc_overlapping_word(cc_bbox, w):
            return w
    return None


def _make_cap_word(letter: str, bbox: BoundingBox) -> Word:
    """Synthesise a Word to stand in for the un-OCR'd cap glyph.

    Carries both the ``"drop cap"`` tag (so ``Block.text`` joins it to
    the next word with no separator, matching the block-cap stitcher's
    contract) and ``"drop cap inferred"`` so labelers / training
    pipelines can flag the synthetic origin.
    """
    return Word(
        text=letter,
        bounding_box=bbox,
        ocr_confidence=None,
        word_components=["drop cap", "drop cap inferred"],
    )


def _tag_unrecovered(candidate: _GapCandidate) -> None:
    """Failure path: tag the body word ``"drop cap unrecovered"``."""
    body = candidate.first_body_word
    components = list(body.word_components or [])
    if "drop cap unrecovered" not in components:
        components.append("drop cap unrecovered")
        body.word_components = components


def _attach_cap_to_line(
    cap_word: Word,
    candidate: _GapCandidate,
) -> None:
    """Prepend ``cap_word`` to the target line + recompute bboxes upward."""
    line = candidate.target_line
    line.items = [cap_word] + list(line.items)
    line.recompute_bounding_box()
    candidate.paragraph.recompute_bounding_box()
    candidate.block.recompute_bounding_box()


def detect_and_stitch_cursive_dropcaps(
    blocks: list[Block],
    image: "Optional[np.ndarray]",
    metrics: "PageMetrics",
) -> list[Block]:
    """Iteration-A cursive-cap fallback. See module docstring for design.

    Parameters
    ----------
    blocks
        The body-block list as returned by ``stitch_drop_caps`` (i.e.
        after the geometric block-cap pass). Mutated in place; the
        same list is also returned for chainable use.
    image
        The page image as a ``numpy.ndarray`` (``cv2`` BGR or grayscale).
        If ``None``, the function is a no-op (CC scan needs pixels).
    metrics
        Per-page geometric statistics (``PageMetrics``).

    Returns
    -------
    list[Block]
        ``blocks``, possibly with cap words prepended to first body
        lines. On any failure the list is returned unchanged plus a
        ``logger.warning`` and a ``"drop cap unrecovered"`` tag on the
        body word closest to the failure.
    """
    if image is None:
        return blocks
    indent = _compute_indent_signature(blocks)
    if indent is None:
        return blocks

    candidates = _geometric_gap_candidates(blocks, indent)
    if not candidates:
        return blocks

    # Track CC bboxes that have been claimed by a successful stitch.
    # When two consecutive lines wrap around the same drop-cap glyph
    # the paragraph splitter often fires the geometric trigger on
    # both — but they're the same physical cap, so we de-dup.
    claimed_cc_bboxes: list[BoundingBox] = []

    for candidate in candidates:
        # Skip if this paragraph's first line ALREADY hosts a drop cap
        # (block-cap stitcher claimed it on a previous step).
        if any(
            "drop cap" in (w.word_components or []) for w in candidate.target_line.words
        ):
            continue

        cc_bbox = _scan_dropcap_cc(image, candidate, metrics)
        if cc_bbox is None:
            logger.warning(
                "Drop-cap geometric trigger fired but no CC found near body "
                "word %r at y=[%.4f,%.4f]; tagging unrecovered.",
                candidate.first_body_word.text,
                candidate.line_minY,
                candidate.line_maxY,
            )
            _tag_unrecovered(candidate)
            continue

        # De-dup: when two adjacent body lines wrap around the same
        # cap glyph (typical 2-line drop cap), the geometric trigger
        # fires on both. The CC scan finds the same physical cap for
        # the second candidate; skip it silently.
        if any(_bboxes_overlap(cc_bbox, prev) for prev in claimed_cc_bboxes):
            continue

        letter = _resolve_cap_letter(candidate.first_body_word.text or "")
        if letter is None:
            logger.warning(
                "Drop-cap CC found near body word %r but letter inference "
                "ambiguous (no unique single-letter prepend matches the "
                "lexicon); tagging unrecovered.",
                candidate.first_body_word.text,
            )
            _tag_unrecovered(candidate)
            continue

        existing = _find_existing_cap_word(candidate, cc_bbox)
        if existing is not None:
            existing_text = (existing.text or "").strip().upper()
            if existing_text == letter:
                # OCR returned the right letter — keep its confidence
                # and just tag it.
                components = list(existing.word_components or [])
                if "drop cap" not in components:
                    components.append("drop cap")
                if "drop cap inferred" not in components:
                    components.append("drop cap inferred")
                existing.word_components = components
                # Move it to the front of the line if it's not already.
                if list(candidate.target_line.words)[0] is not existing:
                    line_items = [existing] + [
                        w for w in candidate.target_line.items if w is not existing
                    ]
                    candidate.target_line.items = line_items
                    candidate.target_line.recompute_bounding_box()
                    candidate.paragraph.recompute_bounding_box()
                    candidate.block.recompute_bounding_box()
            else:
                # OCR returned wrong/gibberish text — discard the
                # OCR letter, replace with the inferred one. Keep the
                # bbox (it's where the cap glyph actually lives) but
                # union it with the CC bbox for safety.
                cap_bbox = BoundingBox.from_ltrb(
                    min(existing.bounding_box.minX, cc_bbox.minX),
                    min(existing.bounding_box.minY, cc_bbox.minY),
                    max(existing.bounding_box.maxX, cc_bbox.maxX),
                    max(existing.bounding_box.maxY, cc_bbox.maxY),
                    is_normalized=True,
                )
                existing.text = letter
                existing.bounding_box = cap_bbox
                existing.ocr_confidence = None
                components = list(existing.word_components or [])
                if "drop cap" not in components:
                    components.append("drop cap")
                if "drop cap inferred" not in components:
                    components.append("drop cap inferred")
                existing.word_components = components
                if list(candidate.target_line.words)[0] is not existing:
                    line_items = [existing] + [
                        w for w in candidate.target_line.items if w is not existing
                    ]
                    candidate.target_line.items = line_items
                candidate.target_line.recompute_bounding_box()
                candidate.paragraph.recompute_bounding_box()
                candidate.block.recompute_bounding_box()
        else:
            # OCR skipped the glyph — synthesise a new Word.
            cap_word = _make_cap_word(letter, cc_bbox)
            _attach_cap_to_line(cap_word, candidate)

        claimed_cc_bboxes.append(cc_bbox)

    return blocks
