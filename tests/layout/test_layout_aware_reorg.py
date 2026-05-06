"""Tests for the layout-aware reorganize_page integration.

Covers:
  - ``reorganize_page(layout=None)`` is a no-op on layout (parity with
    pre-layout behaviour).
  - ``drop_layout_regions`` removes words inside high-confidence header
    regions and leaves low-confidence regions alone.
  - ``associate_captions`` builds a tagged caption block under each
    figure region.
"""

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.geometry.point import Point
from pd_book_tools.layout.types import LayoutRegion, PageLayout, RegionType
from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pd_book_tools.ocr.layout_aware_reorg import (
    _LEFT_SIDENOTE_SORT_ORDER,
    _RIGHT_SIDENOTE_SORT_ORDER,
    associate_captions,
    bubble_block_roles_from_layout,
    detect_geometric_sidenotes,
    drop_figure_internal_words,
    drop_layout_regions,
    emit_caption_block,
    route_sidenote_reading_order,
    tag_words_with_layout,
    word_layout_tags,
    words_inside,
)
from pd_book_tools.ocr.page import Page
from pd_book_tools.ocr.word import Word

PAGE_W = 1000
PAGE_H = 1500


def _word(text, L, T, R, B, *, normalized=False):
    if normalized:
        bbox = BoundingBox(
            top_left=Point(L, T, is_normalized=True),
            bottom_right=Point(R, B, is_normalized=True),
            is_normalized=True,
        )
    else:
        bbox = BoundingBox(
            top_left=Point(L, T, is_normalized=False),
            bottom_right=Point(R, B, is_normalized=False),
            is_normalized=False,
        )
    return Word(text=text, bounding_box=bbox, ocr_confidence=0.9)


def _line_block(words):
    return Block(
        items=words,
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )


def _paragraph_block(line_blocks):
    return Block(
        items=line_blocks,
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.PARAGRAPH,
    )


def _make_page(blocks):
    return Page(width=PAGE_W, height=PAGE_H, page_index=0, items=blocks)


class TestWordsInside:
    def test_pixel_word_inside_pixel_region(self):
        w = _word("hi", 100, 100, 200, 130)
        region = LayoutRegion(
            type=RegionType.text, L=0, R=300, T=50, B=200, confidence=1.0
        )
        assert words_inside(region, [w], PAGE_W, PAGE_H, PAGE_W, PAGE_H) == [w]

    def test_pixel_word_outside_region(self):
        w = _word("hi", 800, 800, 850, 830)
        region = LayoutRegion(
            type=RegionType.text, L=0, R=300, T=50, B=200, confidence=1.0
        )
        assert words_inside(region, [w], PAGE_W, PAGE_H, PAGE_W, PAGE_H) == []

    def test_normalized_word(self):
        # Word centered at (0.15, 0.1) in normalized coords → page-pixel (150, 150)
        w = _word("hi", 0.1, 0.05, 0.2, 0.15, normalized=True)
        region = LayoutRegion(
            type=RegionType.text, L=0, R=400, T=0, B=300, confidence=1.0
        )
        assert words_inside(region, [w], PAGE_W, PAGE_H, PAGE_W, PAGE_H) == [w]


class TestDropLayoutRegions:
    def _page_with_header_and_body(self):
        header_words = [
            _word("PAGE", 100, 30, 200, 60),
            _word("TITLE", 210, 30, 350, 60),
        ]
        body_words = [
            _word("body", 100, 500, 200, 530),
            _word("text", 210, 500, 350, 530),
        ]
        return _make_page(
            [
                _paragraph_block([_line_block(header_words)]),
                _paragraph_block([_line_block(body_words)]),
            ]
        )

    def test_drops_high_confidence_header(self):
        page = self._page_with_header_and_body()
        layout = PageLayout(
            regions=[
                LayoutRegion(
                    type=RegionType.header,
                    L=0,
                    R=PAGE_W,
                    T=0,
                    B=100,
                    confidence=0.95,
                )
            ],
            image_width=PAGE_W,
            image_height=PAGE_H,
            detector="test",
        )
        removed = drop_layout_regions(page, layout, drop_types={RegionType.header})
        assert removed == 2
        # Only body words remain.
        remaining_text = [w.text for w in page.words]
        assert remaining_text == ["body", "text"]

    def test_low_confidence_header_kept(self):
        page = self._page_with_header_and_body()
        layout = PageLayout(
            regions=[
                LayoutRegion(
                    type=RegionType.header,
                    L=0,
                    R=PAGE_W,
                    T=0,
                    B=100,
                    confidence=0.3,
                )
            ],
            image_width=PAGE_W,
            image_height=PAGE_H,
            detector="test",
        )
        removed = drop_layout_regions(page, layout, drop_types={RegionType.header})
        assert removed == 0
        assert {w.text for w in page.words} == {"PAGE", "TITLE", "body", "text"}

    def test_only_listed_drop_types_removed(self):
        page = self._page_with_header_and_body()
        layout = PageLayout(
            regions=[
                LayoutRegion(
                    type=RegionType.header,
                    L=0,
                    R=PAGE_W,
                    T=0,
                    B=100,
                    confidence=0.95,
                )
            ],
            image_width=PAGE_W,
            image_height=PAGE_H,
            detector="test",
        )
        removed = drop_layout_regions(page, layout, drop_types={RegionType.footer})
        assert removed == 0


class TestEmitCaptionBlock:
    def test_returns_none_for_empty(self):
        assert emit_caption_block([]) is None

    def test_role_label_set(self):
        words = [_word("Fig.", 100, 100, 150, 130), _word("1", 160, 100, 180, 130)]
        block = emit_caption_block(words)
        assert block is not None
        assert "caption" in block.block_role_labels


class TestReorganizeAcceptsLayoutKwarg:
    def test_signature_accepts_layout_keyword(self):
        # Tiny page: a single line block with two words. Goal here is just
        # to verify reorganize_page(layout=None) is a no-op vs the no-arg
        # call shape (the rest of the reorg tests in tests/ocr/ exercise
        # behaviour under typical pages).
        words = [_word("Hello", 100, 100, 200, 130), _word("world", 210, 100, 350, 130)]
        page = _make_page([_paragraph_block([_line_block(words)])])
        # No layout supplied — should not raise.
        page.reorganize_page(layout=None)
        # Words preserved.
        assert "Hello" in page.text
        assert "world" in page.text


class TestReorganizeDropLayoutWordsFlag:
    """Regression: footnote / header / footer / abandoned words must
    NEVER be silently dropped by ``Page.reorganize_page``, regardless
    of the experimental ``drop_layout_words`` flag. Pre-fix, a real
    page (``225.png`` from ``projectID66c62fca99a93``) lost its
    footnotes entirely because ``reorganize_page`` called
    ``drop_layout_regions`` unconditionally when a layout was supplied.

    With the corrected policy:
      * Default mode (``drop_layout_words=False``) — no layout-region
        drops, no Step Layout-2b drops, no Step B2 drops. Every OCR
        word survives.
      * Experimental mode (``drop_layout_words=True``) — Step Layout-2b
        (figure-internal only words) and Step B2 (geometric figure
        noise) both fire. Footnote / header / footer / abandoned words
        still survive.

    This class exercises both modes through the full
    ``Page.reorganize_page`` entry point with a synthetic page.
    """

    def _page_with_body_and_footnote(self):
        # Body paragraph in the upper two-thirds, footnote paragraph
        # near the bottom — wide enough x-extents that geometric heuristics
        # treat the body line as real content.
        body_words = [
            _word("body", 100, 500, 200, 530),
            _word("text", 210, 500, 350, 530),
        ]
        footnote_words = [
            _word("FN", 100, 1300, 150, 1330),
            _word("note", 160, 1300, 280, 1330),
        ]
        return _make_page(
            [
                _paragraph_block([_line_block(body_words)]),
                _paragraph_block([_line_block(footnote_words)]),
            ]
        )

    def _layout_with_footnote_band(self):
        # High-confidence footnote region covering the footnote band, plus
        # a body text region so the body line keeps its layout:text tag.
        return PageLayout(
            regions=[
                LayoutRegion(
                    type=RegionType.text,
                    L=0,
                    R=PAGE_W,
                    T=400,
                    B=600,
                    confidence=0.95,
                ),
                LayoutRegion(
                    type=RegionType.footnote,
                    L=0,
                    R=PAGE_W,
                    T=1250,
                    B=1400,
                    confidence=0.95,
                ),
            ],
            image_width=PAGE_W,
            image_height=PAGE_H,
            detector="test",
        )

    def test_default_preserves_footnote_words(self):
        page = self._page_with_body_and_footnote()
        layout = self._layout_with_footnote_band()
        page.reorganize_page(layout=layout)
        # Footnote words must survive into the post-reorganize output —
        # this is the whole point of the policy.
        remaining_text = {w.text for w in page.words}
        assert "FN" in remaining_text
        assert "note" in remaining_text
        # Body words obviously also survive.
        assert {"body", "text"}.issubset(remaining_text)

    def test_opt_in_still_preserves_footnote_words(self):
        # Even with ``drop_layout_words=True`` (the experimental
        # opt-in), footnote / header / footer / abandoned regions are
        # NEVER dropped — that flag now governs only the two
        # figure-internal word-deletion paths (Step Layout-2b and the
        # geometric Step B2 sweep), neither of which fires on a
        # footnote-band line.
        page = self._page_with_body_and_footnote()
        layout = self._layout_with_footnote_band()
        page.reorganize_page(layout=layout, drop_layout_words=True)
        remaining_text = {w.text for w in page.words}
        assert "FN" in remaining_text
        assert "note" in remaining_text
        assert {"body", "text"}.issubset(remaining_text)

    def test_footnote_words_keep_layout_tag(self):
        # Per-word ``layout:footnote`` tags are stamped by
        # ``tag_words_with_layout`` and survive the rest of the
        # pipeline, so consumers can still dispatch on the per-word
        # tag (or the bubbled block role, where Step E doesn't
        # relabel the band) instead of relying on word deletion.
        page = self._page_with_body_and_footnote()
        layout = self._layout_with_footnote_band()
        page.reorganize_page(layout=layout)
        for word in page.words:
            if word.text in {"FN", "note"}:
                assert "layout:footnote" in word.word_labels
            elif word.text in {"body", "text"}:
                assert "layout:text" in word.word_labels


class TestAssociateCaptions:
    def test_caption_attached_to_figure(self):
        # Body paragraph
        body = _paragraph_block([_line_block([_word("body", 100, 200, 200, 230)])])
        # Caption words at y=720..760, just below the figure's bottom (700)
        caption_words = [
            _word("Fig.", 100, 720, 150, 750),
            _word("1.", 160, 720, 200, 750),
            _word("Demo.", 210, 720, 350, 750),
        ]
        caption_para = _paragraph_block([_line_block(caption_words)])
        page = _make_page([body, caption_para])

        layout = PageLayout(
            regions=[
                LayoutRegion(
                    type=RegionType.figure,
                    L=100,
                    R=400,
                    T=300,
                    B=700,
                    confidence=0.9,
                ),
                LayoutRegion(
                    type=RegionType.caption,
                    L=100,
                    R=400,
                    T=710,
                    B=770,
                    confidence=0.8,
                ),
            ],
            image_width=PAGE_W,
            image_height=PAGE_H,
            detector="test",
        )

        attached = associate_captions(page, layout)
        assert attached == 1

        # Find the caption block and the illustration block.
        caption_blocks = [b for b in page.items if "caption" in b.block_role_labels]
        illustration_blocks = [
            b for b in page.items if "illustration" in b.block_role_labels
        ]
        assert len(caption_blocks) == 1
        assert len(illustration_blocks) == 1

        caption_block = caption_blocks[0]
        # Caption block should now hold the caption words.
        words_in_caption = caption_block.words
        assert {w.text for w in words_in_caption} == {"Fig.", "1.", "Demo."}

    def test_low_confidence_figure_skipped(self):
        body = _paragraph_block([_line_block([_word("body", 100, 200, 200, 230)])])
        page = _make_page([body])

        layout = PageLayout(
            regions=[
                LayoutRegion(
                    type=RegionType.figure,
                    L=100,
                    R=400,
                    T=300,
                    B=700,
                    confidence=0.2,  # below default 0.5
                )
            ],
            image_width=PAGE_W,
            image_height=PAGE_H,
            detector="test",
        )
        assert associate_captions(page, layout) == 0
        assert not any("illustration" in b.block_role_labels for b in page.items)


class TestTagWordsWithLayout:
    def test_word_in_caption_region_gets_tag(self):
        words = [_word("Fig.", 100, 100, 200, 130), _word("body", 100, 600, 200, 630)]
        page = _make_page([_paragraph_block([_line_block(words)])])
        layout = PageLayout(
            regions=[
                LayoutRegion(
                    type=RegionType.caption,
                    L=0,
                    R=400,
                    T=80,
                    B=160,
                    confidence=0.9,
                ),
                LayoutRegion(
                    type=RegionType.text,
                    L=0,
                    R=400,
                    T=500,
                    B=700,
                    confidence=0.9,
                ),
            ],
            image_width=PAGE_W,
            image_height=PAGE_H,
            detector="test",
        )
        n = tag_words_with_layout(page, layout)
        assert n == 2
        assert word_layout_tags(words[0]) == ["caption"]
        assert word_layout_tags(words[1]) == ["text"]

    def test_low_confidence_region_ignored(self):
        words = [_word("hi", 100, 100, 200, 130)]
        page = _make_page([_paragraph_block([_line_block(words)])])
        layout = PageLayout(
            regions=[
                LayoutRegion(
                    type=RegionType.caption,
                    L=0,
                    R=400,
                    T=80,
                    B=160,
                    confidence=0.2,
                ),
            ],
            image_width=PAGE_W,
            image_height=PAGE_H,
            detector="test",
        )
        assert tag_words_with_layout(page, layout) == 0
        assert word_layout_tags(words[0]) == []

    def test_idempotent(self):
        words = [_word("hi", 100, 100, 200, 130)]
        page = _make_page([_paragraph_block([_line_block(words)])])
        layout = PageLayout(
            regions=[
                LayoutRegion(
                    type=RegionType.caption,
                    L=0,
                    R=400,
                    T=80,
                    B=160,
                    confidence=0.9,
                ),
            ],
            image_width=PAGE_W,
            image_height=PAGE_H,
            detector="test",
        )
        tag_words_with_layout(page, layout)
        tag_words_with_layout(page, layout)
        assert words[0].word_labels.count("layout:caption") == 1


class TestDropFigureInternalWords:
    def _layout_with_figure(self, fig_box, extra_regions=()):
        return PageLayout(
            regions=[
                LayoutRegion(
                    type=RegionType.figure,
                    L=fig_box[0],
                    R=fig_box[2],
                    T=fig_box[1],
                    B=fig_box[3],
                    confidence=0.95,
                ),
                *extra_regions,
            ],
            image_width=PAGE_W,
            image_height=PAGE_H,
            detector="test",
        )

    def test_drops_pure_figure_only_line(self):
        # Single line, all words inside the figure region only — drop.
        words = [
            _word(t, 100 + 50 * i, 200, 140 + 50 * i, 230)
            for i, t in enumerate(["BALI", "KANE", "WU"])
        ]
        page = _make_page([_paragraph_block([_line_block(words)])])
        layout = self._layout_with_figure((50, 50, 700, 800))
        tag_words_with_layout(page, layout)
        n = drop_figure_internal_words(page, layout)
        assert n == 3
        assert page.words == []

    def test_preserves_wrap_around_body(self):
        # Two words: one inside the figure (would be tagged figure-only) and
        # one inside an adjacent text region (tagged text-only). They are
        # in DIFFERENT lines — only the figure-only line should drop.
        fig_word = _word("noise", 100, 200, 140, 230)
        body_word = _word("real", 800, 200, 870, 230)
        page = _make_page(
            [
                _paragraph_block([_line_block([fig_word])]),
                _paragraph_block([_line_block([body_word])]),
            ]
        )
        layout = self._layout_with_figure(
            (50, 50, 500, 800),
            extra_regions=(
                LayoutRegion(
                    type=RegionType.text,
                    L=600,
                    R=950,
                    T=50,
                    B=800,
                    confidence=0.9,
                ),
            ),
        )
        tag_words_with_layout(page, layout)
        n = drop_figure_internal_words(page, layout)
        assert n == 1
        assert {w.text for w in page.words} == {"real"}

    def test_keeps_line_with_mixed_tags(self):
        # A single line where one word is inside both a figure AND a text
        # region (multi-tagged) should NOT be dropped — that's the wrap-around
        # signal we care about preserving.
        words = [
            _word("wrap", 480, 200, 540, 230),  # at the boundary
            _word("text", 700, 200, 760, 230),  # outside figure
        ]
        page = _make_page([_paragraph_block([_line_block(words)])])
        layout = self._layout_with_figure(
            (50, 50, 600, 800),  # boundary at x=600
            extra_regions=(
                LayoutRegion(
                    type=RegionType.text,
                    L=400,
                    R=950,
                    T=50,
                    B=800,
                    confidence=0.9,
                ),
            ),
        )
        tag_words_with_layout(page, layout)
        n = drop_figure_internal_words(page, layout)
        assert n == 0
        assert {w.text for w in page.words} == {"wrap", "text"}

    def test_keeps_caption_words_inside_figure_bbox(self):
        # If a caption region overlaps a figure region, caption words have
        # both layout:figure and layout:caption tags — they must NOT be
        # treated as figure-internal noise.
        words = [_word("Fig.", 100, 200, 200, 230), _word("1.", 220, 200, 260, 230)]
        page = _make_page([_paragraph_block([_line_block(words)])])
        layout = self._layout_with_figure(
            (50, 50, 600, 800),
            extra_regions=(
                LayoutRegion(
                    type=RegionType.caption,
                    L=80,
                    R=400,
                    T=180,
                    B=260,
                    confidence=0.9,
                ),
            ),
        )
        tag_words_with_layout(page, layout)
        n = drop_figure_internal_words(page, layout)
        assert n == 0
        assert {w.text for w in page.words} == {"Fig.", "1."}

    def test_no_op_without_tagging(self):
        # If tag_words_with_layout never ran, words have no layout tags →
        # the helper drops nothing (we only act on positive evidence).
        words = [_word("a", 100, 200, 140, 230)]
        page = _make_page([_paragraph_block([_line_block(words)])])
        layout = self._layout_with_figure((50, 50, 700, 800))
        n = drop_figure_internal_words(page, layout)
        assert n == 0


class TestDetectGeometricSidenotes:
    def _body_word(self, text, idx, *, x_left=80, x_right=600):
        # 12 body words stacked vertically — wide x-range establishes
        # the "body column" in the histogram.
        y = 100 + idx * 40
        return _word(text, x_left, y, x_right, y + 30)

    def _make_body(self):
        words = [self._body_word(f"body{i}", i) for i in range(12)]
        return words, _make_page([_paragraph_block([_line_block(words)])])

    def test_right_margin_cluster_tagged(self):
        body_words, page = self._make_body()
        # Add a sidenote: 5 words in a tight column at x=820..900,
        # comfortably beyond the body's right edge of 600 (with page width 1000).
        sidenote_words = [
            _word(f"side{i}", 820, 110 + i * 50, 900, 140 + i * 50) for i in range(5)
        ]
        page._items.append(_paragraph_block([_line_block(sidenote_words)]))

        n = detect_geometric_sidenotes(page)
        assert n == 5
        assert all("layout:sidenote" in w.word_labels for w in sidenote_words)
        # Body words must NOT pick up the sidenote tag.
        assert not any("layout:sidenote" in w.word_labels for w in body_words)

    def test_left_margin_cluster_tagged(self):
        # Body shifted right so x_left=300; sidenote at x=20..100.
        body_words = [
            _word(f"body{i}", 300, 100 + i * 40, 800, 130 + i * 40) for i in range(12)
        ]
        page = _make_page([_paragraph_block([_line_block(body_words)])])

        sidenote_words = [
            _word(f"L{i}", 20, 110 + i * 50, 100, 140 + i * 50) for i in range(5)
        ]
        page._items.append(_paragraph_block([_line_block(sidenote_words)]))

        n = detect_geometric_sidenotes(page)
        assert n == 5
        assert all("layout:sidenote" in w.word_labels for w in sidenote_words)

    def test_below_min_cluster_size_ignored(self):
        body_words, page = self._make_body()
        # Only 2 words in the right margin — below default min_cluster_words=4.
        stray = [
            _word("a", 820, 110, 900, 140),
            _word("b", 820, 200, 900, 230),
        ]
        page._items.append(_paragraph_block([_line_block(stray)]))
        n = detect_geometric_sidenotes(page)
        assert n == 0
        assert not any("layout:sidenote" in w.word_labels for w in stray)

    def test_wide_cluster_rejected(self):
        # A "cluster" that spans most of the page width is not a sidenote
        # column — it's noise across the whole page (or a full-width line).
        body_words, page = self._make_body()
        wide = [
            _word("x", 100 + i * 100, 1200 + i * 30, 200 + i * 100, 1230 + i * 30)
            for i in range(8)
        ]
        page._items.append(_paragraph_block([_line_block(wide)]))
        n = detect_geometric_sidenotes(page)
        # The wide spread is well beyond the max_column_width_ratio cap.
        assert n == 0


class TestRouteSidenoteReadingOrder:
    def _sidenote_block(self, text, *, x_left, x_right, y_top=300, y_bot=500):
        words = [_word(text, x_left, y_top, x_right, y_bot)]
        block = _paragraph_block([_line_block(words)])
        block.block_role_labels = ["sidenote"]
        return block

    def test_right_sidenote_pushed_to_bottom(self):
        body_block = _paragraph_block(
            [_line_block([_word("body", 100, 100, 800, 130)])]
        )
        right_sn = self._sidenote_block("right", x_left=820, x_right=950)
        page = _make_page([body_block, right_sn])

        n = route_sidenote_reading_order(page)
        assert n == 1
        assert right_sn.override_page_sort_order >= _RIGHT_SIDENOTE_SORT_ORDER

    def test_left_sidenote_pushed_to_top(self):
        body_block = _paragraph_block(
            [_line_block([_word("body", 200, 100, 800, 130)])]
        )
        left_sn = self._sidenote_block("left", x_left=20, x_right=120)
        page = _make_page([body_block, left_sn])

        n = route_sidenote_reading_order(page)
        assert n == 1
        assert left_sn.override_page_sort_order <= _LEFT_SIDENOTE_SORT_ORDER + 100

    def test_multiple_left_sidenotes_preserve_top_to_bottom(self):
        sn_top = self._sidenote_block(
            "top", x_left=20, x_right=120, y_top=200, y_bot=240
        )
        sn_bot = self._sidenote_block(
            "bot", x_left=20, x_right=120, y_top=900, y_bot=940
        )
        body = _paragraph_block([_line_block([_word("body", 200, 500, 800, 530)])])
        page = _make_page([body, sn_bot, sn_top])

        route_sidenote_reading_order(page)
        # Top block should come first (lower override_page_sort_order)
        assert sn_top.override_page_sort_order < sn_bot.override_page_sort_order

    def test_non_sidenote_blocks_untouched(self):
        body = _paragraph_block([_line_block([_word("body", 100, 100, 800, 130)])])
        body.override_page_sort_order = 5
        page = _make_page([body])
        n = route_sidenote_reading_order(page)
        assert n == 0
        assert body.override_page_sort_order == 5


class TestBubbleBlockRolesFromLayout:
    def test_dominant_caption_words_set_caption_role(self):
        words = [
            _word("Fig.", 100, 100, 200, 130),
            _word("1.", 210, 100, 240, 130),
            _word("Demo.", 250, 100, 350, 130),
        ]
        block = _paragraph_block([_line_block(words)])
        for w in words:
            w.word_labels.append("layout:caption")
        n = bubble_block_roles_from_layout([block])
        assert n == 1
        assert "caption" in block.block_role_labels

    def test_paragraph_role_not_added(self):
        # Pure body text should NOT add "paragraph" — it's the default role
        # and adding it pollutes labels.
        words = [_word("hello", 100, 100, 200, 130)]
        block = _paragraph_block([_line_block(words)])
        words[0].word_labels.append("layout:text")
        bubble_block_roles_from_layout([block])
        assert "paragraph" not in block.block_role_labels

    def test_no_tags_no_change(self):
        block = _paragraph_block([_line_block([_word("a", 100, 100, 200, 130)])])
        before = list(block.block_role_labels)
        bubble_block_roles_from_layout([block])
        assert block.block_role_labels == before

    def test_skip_block_already_layout_tagged(self):
        words = [_word("a", 100, 100, 200, 130)]
        block = _paragraph_block([_line_block(words)])
        words[0].word_labels.append("layout:caption")
        block.block_role_labels.append("illustration")  # someone already set it
        n = bubble_block_roles_from_layout([block])
        assert n == 0
        assert "caption" not in block.block_role_labels

    def test_non_text_dominates_text(self):
        # Mixed: 2 caption-tagged + 5 text-tagged → should still pick caption,
        # because "text" is a parent region the model often emits around
        # nested caption / heading regions.
        words = [_word(f"w{i}", 100 + 50 * i, 100, 140 + 50 * i, 130) for i in range(7)]
        block = _paragraph_block([_line_block(words)])
        for w in words[:2]:
            w.word_labels.append("layout:caption")
        for w in words[2:]:
            w.word_labels.append("layout:text")
        n = bubble_block_roles_from_layout([block])
        assert n == 1
        assert "caption" in block.block_role_labels
        body = _paragraph_block([_line_block([_word("body", 100, 200, 200, 230)])])
        page = _make_page([body])

        layout = PageLayout(
            regions=[
                LayoutRegion(
                    type=RegionType.figure,
                    L=100,
                    R=400,
                    T=300,
                    B=700,
                    confidence=0.2,  # below default 0.5
                )
            ],
            image_width=PAGE_W,
            image_height=PAGE_H,
            detector="test",
        )
        assert associate_captions(page, layout) == 0
        assert not any("illustration" in b.block_role_labels for b in page.items)
