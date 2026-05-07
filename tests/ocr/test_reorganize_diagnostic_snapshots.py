"""Tests for the diagnostic snapshots captured by ``Page.reorganize_page``.

The reorganize pipeline stashes two ``Page`` clones for CLI / debugging
consumption:

* ``Page.diagnostic_pure_ocr`` — captured at the very top of
  ``reorganize_page``, before any layout tagging or noise removal. The
  literal OCR engine output as it entered the pipeline.

* ``Page.diagnostic_post_noise_removal`` — captured at the same point
  as the internal ``pre_reorg_words`` reference list, after Step
  Layout-2b (``drop_figure_internal_words``) and Step B2
  (``drop_heuristic_figure_noise``) but before reorg-proper begins.

Both are diagnostic-only outputs intended for CLI consumption, not used
by any production logic.
"""

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.geometry.point import Point
from pd_book_tools.layout.types import LayoutRegion, PageLayout, RegionType
from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pd_book_tools.ocr.page import Page
from pd_book_tools.ocr.word import Word

PAGE_W = 1000
PAGE_H = 1500


def _word(text, L, T, R, B):
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
    return Page(width=PAGE_W, height=PAGE_H, page_index=0, blocks=blocks)


# ---------------------------------------------------------------------------
# Pre-reorganize state of the diagnostic attributes.
# ---------------------------------------------------------------------------


def test_diagnostic_attributes_default_to_none():
    """A freshly-built page has no diagnostic snapshots until reorganize runs."""
    page = _make_page(
        [_paragraph_block([_line_block([_word("hello", 100, 100, 200, 130)])])]
    )
    assert page.diagnostic_pure_ocr is None
    assert page.diagnostic_post_noise_removal is None


def test_capture_diagnostics_false_keeps_attributes_none():
    """The opt-out kwarg disables snapshot capture without affecting reorg."""
    page = _make_page(
        [_paragraph_block([_line_block([_word("hello", 100, 100, 200, 130)])])]
    )
    page.reorganize_page(capture_diagnostics=False)
    assert page.diagnostic_pure_ocr is None
    assert page.diagnostic_post_noise_removal is None


# ---------------------------------------------------------------------------
# Pure-OCR snapshot — captured before any pipeline mutation.
# ---------------------------------------------------------------------------


def test_pure_ocr_snapshot_has_no_layout_tags():
    """The pure-OCR snapshot is captured *before* ``tag_words_with_layout``,
    so its words must carry no ``layout:*`` entries even when the live
    page has them stamped after reorganize."""
    body_words = [
        _word("body", 100, 500, 200, 530),
        _word("text", 210, 500, 350, 530),
    ]
    page = _make_page([_paragraph_block([_line_block(body_words)])])
    layout = PageLayout(
        regions=[
            LayoutRegion(
                type=RegionType.text,
                L=0,
                R=PAGE_W,
                T=400,
                B=600,
                confidence=0.95,
            )
        ],
        image_width=PAGE_W,
        image_height=PAGE_H,
        detector="test",
    )
    page.reorganize_page(layout=layout)

    # Live page words must have layout tags after reorganize.
    for word in page.words:
        if word.text in {"body", "text"}:
            assert "layout:text" in word.word_labels

    # Snapshot must NOT — it pre-dates ``tag_words_with_layout``.
    snap = page.diagnostic_pure_ocr
    assert snap is not None
    assert isinstance(snap, Page)
    snap_texts = [w.text for w in snap.words]
    assert sorted(snap_texts) == sorted(["body", "text"])
    for word in snap.words:
        for label in word.word_labels:
            assert not label.startswith("layout:"), (
                f"pure-OCR snapshot leaked layout label {label!r} on {word.text!r}"
            )


def test_pure_ocr_snapshot_word_count_matches_input():
    """The pure-OCR snapshot preserves *every* OCR word, regardless of
    what the rest of the pipeline subsequently drops."""
    # Body line + a footnote-band line. With ``drop_layout_words=True`` the
    # heuristic pipeline can drop figure-internal noise; the pure-OCR
    # snapshot must still hold both lines unmodified.
    body_words = [
        _word("body", 100, 500, 200, 530),
        _word("text", 210, 500, 350, 530),
    ]
    fn_words = [
        _word("FN", 100, 1300, 150, 1330),
        _word("note", 160, 1300, 280, 1330),
    ]
    page = _make_page(
        [
            _paragraph_block([_line_block(body_words)]),
            _paragraph_block([_line_block(fn_words)]),
        ]
    )
    pre_count = len(page.words)
    page.reorganize_page(drop_layout_words=True)

    snap = page.diagnostic_pure_ocr
    assert snap is not None
    assert len(snap.words) == pre_count
    assert {w.text for w in snap.words} == {"body", "text", "FN", "note"}


def test_pure_ocr_snapshot_is_independent_of_live_page():
    """Mutating the live page's words after reorganize must not affect the
    snapshot, since the snapshot is a deep clone."""
    page = _make_page(
        [
            _paragraph_block(
                [
                    _line_block(
                        [
                            _word("alpha", 100, 100, 200, 130),
                            _word("beta", 210, 100, 350, 130),
                        ]
                    )
                ]
            )
        ]
    )
    page.reorganize_page()
    snap = page.diagnostic_pure_ocr
    assert snap is not None

    # Tag a word on the live page.
    page.words[0].word_labels.append("post-reorg-mutation")

    snap_word = next(w for w in snap.words if w.text == "alpha")
    assert "post-reorg-mutation" not in snap_word.word_labels


# ---------------------------------------------------------------------------
# Post-noise-removal snapshot — captured after Step Layout-2b / Step B2.
# ---------------------------------------------------------------------------


def test_post_noise_snapshot_equals_pure_ocr_when_no_drops():
    """When neither noise-removal step is triggered, the post-noise
    snapshot should hold the same words as the pure-OCR snapshot.

    Default-flag reorganize without a layout has nothing to drop:
    Step Layout-2b is skipped (no layout) and Step B2 is gated behind
    the experimental ``drop_layout_words`` opt-in."""
    page = _make_page(
        [
            _paragraph_block(
                [
                    _line_block(
                        [
                            _word("hello", 100, 100, 200, 130),
                            _word("world", 210, 100, 350, 130),
                        ]
                    )
                ]
            )
        ]
    )
    page.reorganize_page()

    pure = page.diagnostic_pure_ocr
    post = page.diagnostic_post_noise_removal
    assert pure is not None
    assert post is not None
    assert {w.text for w in pure.words} == {w.text for w in post.words}


def test_post_noise_snapshot_drops_figure_internal_words():
    """When the layout-aware figure-internal drop fires (Step Layout-2b),
    the post-noise snapshot should reflect the post-drop state, while
    the pure-OCR snapshot still holds every input word."""
    fig_words = [
        _word("BALI", 100, 200, 140, 230),
        _word("KANE", 160, 200, 200, 230),
        _word("WU", 220, 200, 260, 230),
    ]
    body_words = [
        _word("body", 100, 1000, 200, 1030),
        _word("text", 210, 1000, 350, 1030),
    ]
    page = _make_page(
        [
            _paragraph_block([_line_block(fig_words)]),
            _paragraph_block([_line_block(body_words)]),
        ]
    )
    layout = PageLayout(
        regions=[
            LayoutRegion(
                type=RegionType.figure,
                L=50,
                R=400,
                T=150,
                B=300,
                confidence=0.95,
            ),
            LayoutRegion(
                type=RegionType.text,
                L=50,
                R=400,
                T=950,
                B=1100,
                confidence=0.95,
            ),
        ],
        image_width=PAGE_W,
        image_height=PAGE_H,
        detector="test",
    )
    page.reorganize_page(
        layout=layout,
        drop_figure_internal_text=True,
        drop_layout_words=True,
    )

    pure = page.diagnostic_pure_ocr
    post = page.diagnostic_post_noise_removal
    assert pure is not None
    assert post is not None

    pure_texts = {w.text for w in pure.words}
    post_texts = {w.text for w in post.words}

    # The pure snapshot keeps every input word.
    assert pure_texts == {"BALI", "KANE", "WU", "body", "text"}
    # The post-noise snapshot has the figure-internal words removed.
    assert post_texts == {"body", "text"}


def test_post_noise_snapshot_is_independent_of_live_page():
    """Reorganize-proper continues to mutate self.words after the
    post-noise capture point. The snapshot must hold an independent
    deep copy so its words still reflect the captured state."""
    page = _make_page(
        [
            _paragraph_block(
                [
                    _line_block(
                        [
                            _word("alpha", 100, 100, 200, 130),
                            _word("beta", 210, 100, 350, 130),
                        ]
                    )
                ]
            )
        ]
    )
    page.reorganize_page()
    post = page.diagnostic_post_noise_removal
    assert post is not None

    # Whichever changes happen during the rest of reorganize, the
    # snapshot should not see them — confirm by mutating the live page.
    for w in page.words:
        w.word_labels.append("post-snapshot-tag")

    for w in post.words:
        assert "post-snapshot-tag" not in w.word_labels


# ---------------------------------------------------------------------------
# Snapshot rendering / serialization — verify the standard exporters work.
# ---------------------------------------------------------------------------


def test_snapshot_text_renders_words():
    """The snapshot is a real Page so ``snapshot.text`` works the same
    way as on the live page."""
    page = _make_page(
        [
            _paragraph_block(
                [
                    _line_block(
                        [
                            _word("Hello", 100, 100, 200, 130),
                            _word("world", 210, 100, 350, 130),
                        ]
                    )
                ]
            )
        ]
    )
    page.reorganize_page()

    pure = page.diagnostic_pure_ocr
    post = page.diagnostic_post_noise_removal
    assert pure is not None and post is not None

    pure_text = pure.text
    post_text = post.text

    assert "Hello" in pure_text
    assert "world" in pure_text
    assert "Hello" in post_text
    assert "world" in post_text


def test_snapshot_to_dict_round_trips():
    """The snapshot serializes via ``to_dict`` to the same shape the live
    page does, and ``from_dict`` rebuilds it without loss."""
    page = _make_page(
        [
            _paragraph_block(
                [
                    _line_block(
                        [
                            _word("Hello", 100, 100, 200, 130),
                            _word("world", 210, 100, 350, 130),
                        ]
                    )
                ]
            )
        ]
    )
    page.reorganize_page()

    pure = page.diagnostic_pure_ocr
    assert pure is not None

    payload = pure.to_dict()
    assert payload["type"] == "Page"
    assert payload["width"] == PAGE_W
    assert payload["height"] == PAGE_H
    assert isinstance(payload["items"], list)

    rebuilt = Page.from_dict(payload)
    rebuilt_texts = {w.text for w in rebuilt.words}
    assert rebuilt_texts == {"Hello", "world"}


def test_snapshots_not_persisted_by_to_dict():
    """Diagnostic snapshots are runtime-only and must NOT bleed into the
    serialized Page payload — otherwise round-tripping a reorganized
    page would re-emit the snapshots and double the on-disk footprint."""
    page = _make_page(
        [_paragraph_block([_line_block([_word("hello", 100, 100, 200, 130)])])]
    )
    page.reorganize_page()
    payload = page.to_dict()
    assert "diagnostic_pure_ocr" not in payload
    assert "diagnostic_post_noise_removal" not in payload


def test_snapshots_not_persisted_by_copy():
    """``Page.copy()`` round-trips through ``to_dict`` / ``from_dict``,
    so the diagnostic snapshots must not survive a copy. Ensures the
    snapshots stay scoped to the originating reorganize call."""
    page = _make_page(
        [_paragraph_block([_line_block([_word("hello", 100, 100, 200, 130)])])]
    )
    page.reorganize_page()
    cloned = page.copy()
    assert cloned.diagnostic_pure_ocr is None
    assert cloned.diagnostic_post_noise_removal is None


# ---------------------------------------------------------------------------
# Noise-drop diagnostics — list/count of words removed between snapshots.
# ---------------------------------------------------------------------------


def test_noise_drop_diagnostics_default_empty():
    """A freshly-built page has no noise-drop diagnostics until reorganize
    runs."""
    page = _make_page(
        [_paragraph_block([_line_block([_word("hello", 100, 100, 200, 130)])])]
    )
    assert page.diagnostic_noise_dropped_words == []
    assert page.diagnostic_noise_dropped_count == 0


def test_noise_drop_diagnostics_zero_when_no_noise_step_fires():
    """Default reorganize without a layout has nothing to drop:
    Step Layout-2b is skipped (no layout) and Step B2 is gated behind
    the experimental ``drop_layout_words`` opt-in. The drop count
    should be zero and the dropped-words list empty."""
    page = _make_page(
        [
            _paragraph_block(
                [
                    _line_block(
                        [
                            _word("hello", 100, 100, 200, 130),
                            _word("world", 210, 100, 350, 130),
                        ]
                    )
                ]
            )
        ]
    )
    page.reorganize_page()
    assert page.diagnostic_noise_dropped_count == 0
    assert page.diagnostic_noise_dropped_words == []


def test_noise_drop_diagnostics_populated_when_layout_2b_fires():
    """When Step Layout-2b drops figure-internal words (only fires under
    the experimental ``drop_layout_words=True`` opt-in), the noise-drop
    diagnostics should list every dropped word with original text +
    bbox preserved."""
    fig_words = [
        _word("BALI", 100, 200, 140, 230),
        _word("KANE", 160, 200, 200, 230),
        _word("WU", 220, 200, 260, 230),
    ]
    body_words = [
        _word("body", 100, 1000, 200, 1030),
        _word("text", 210, 1000, 350, 1030),
    ]
    page = _make_page(
        [
            _paragraph_block([_line_block(fig_words)]),
            _paragraph_block([_line_block(body_words)]),
        ]
    )
    layout = PageLayout(
        regions=[
            LayoutRegion(
                type=RegionType.figure,
                L=50,
                R=400,
                T=150,
                B=300,
                confidence=0.95,
            ),
            LayoutRegion(
                type=RegionType.text,
                L=50,
                R=400,
                T=950,
                B=1100,
                confidence=0.95,
            ),
        ],
        image_width=PAGE_W,
        image_height=PAGE_H,
        detector="test",
    )
    page.reorganize_page(
        layout=layout,
        drop_figure_internal_text=True,
        drop_layout_words=True,
    )

    # All three figure-internal words should have been dropped.
    assert page.diagnostic_noise_dropped_count == 3
    dropped_texts = sorted(w.text for w in page.diagnostic_noise_dropped_words)
    assert dropped_texts == sorted(["BALI", "KANE", "WU"])

    # Each dropped Word should preserve its text + bbox so the CLI can
    # format a useful warning.
    for word in page.diagnostic_noise_dropped_words:
        assert word.text in {"BALI", "KANE", "WU"}
        assert word.bounding_box is not None


def test_noise_drop_zero_with_drop_layout_words_false_on_figure_page():
    """Default reorganize (``drop_layout_words=False``) must not drop
    any words even on a figure-bearing page where Step Layout-2b *would*
    fire under the opt-in. The hard rule is: the default pipeline never
    silently deletes OCR words — every OCR token survives, with its
    ``layout:figure`` tag attached for downstream consumers to filter
    on if they wish."""
    fig_words = [
        _word("BALI", 100, 200, 140, 230),
        _word("KANE", 160, 200, 200, 230),
        _word("WU", 220, 200, 260, 230),
    ]
    body_words = [
        _word("body", 100, 1000, 200, 1030),
        _word("text", 210, 1000, 350, 1030),
    ]
    page = _make_page(
        [
            _paragraph_block([_line_block(fig_words)]),
            _paragraph_block([_line_block(body_words)]),
        ]
    )
    layout = PageLayout(
        regions=[
            LayoutRegion(
                type=RegionType.figure,
                L=50,
                R=400,
                T=150,
                B=300,
                confidence=0.95,
            ),
            LayoutRegion(
                type=RegionType.text,
                L=50,
                R=400,
                T=950,
                B=1100,
                confidence=0.95,
            ),
        ],
        image_width=PAGE_W,
        image_height=PAGE_H,
        detector="test",
    )
    # Default: drop_layout_words=False. Step Layout-2b is gated, Step B2
    # is gated. No OCR words should be dropped.
    page.reorganize_page(layout=layout)

    assert page.diagnostic_noise_dropped_count == 0
    assert page.diagnostic_noise_dropped_words == []

    # Every OCR word still on the page.
    live_texts = {w.text for w in page.words}
    assert live_texts == {"BALI", "KANE", "WU", "body", "text"}


def test_noise_drop_diagnostics_count_matches_pure_minus_post():
    """Sanity check: the dropped-count must equal the difference between
    pure-OCR snapshot word count and post-noise snapshot word count.
    Layout-2b is gated on ``drop_layout_words=True`` so we opt in here."""
    fig_words = [
        _word("BALI", 100, 200, 140, 230),
        _word("KANE", 160, 200, 200, 230),
    ]
    body_words = [
        _word("body", 100, 1000, 200, 1030),
        _word("text", 210, 1000, 350, 1030),
    ]
    page = _make_page(
        [
            _paragraph_block([_line_block(fig_words)]),
            _paragraph_block([_line_block(body_words)]),
        ]
    )
    layout = PageLayout(
        regions=[
            LayoutRegion(
                type=RegionType.figure,
                L=50,
                R=400,
                T=150,
                B=300,
                confidence=0.95,
            ),
            LayoutRegion(
                type=RegionType.text,
                L=50,
                R=400,
                T=950,
                B=1100,
                confidence=0.95,
            ),
        ],
        image_width=PAGE_W,
        image_height=PAGE_H,
        detector="test",
    )
    page.reorganize_page(
        layout=layout,
        drop_figure_internal_text=True,
        drop_layout_words=True,
    )

    pure_n = len(page.diagnostic_pure_ocr.words)
    post_n = len(page.diagnostic_post_noise_removal.words)
    assert page.diagnostic_noise_dropped_count == pure_n - post_n


def test_noise_drop_diagnostics_independent_of_live_page():
    """The captured dropped-words list must be independent of the live
    page — mutating the live page must not change the captured words."""
    fig_words = [
        _word("BALI", 100, 200, 140, 230),
    ]
    body_words = [
        _word("body", 100, 1000, 200, 1030),
    ]
    page = _make_page(
        [
            _paragraph_block([_line_block(fig_words)]),
            _paragraph_block([_line_block(body_words)]),
        ]
    )
    layout = PageLayout(
        regions=[
            LayoutRegion(
                type=RegionType.figure,
                L=50,
                R=400,
                T=150,
                B=300,
                confidence=0.95,
            ),
            LayoutRegion(
                type=RegionType.text,
                L=50,
                R=400,
                T=950,
                B=1100,
                confidence=0.95,
            ),
        ],
        image_width=PAGE_W,
        image_height=PAGE_H,
        detector="test",
    )
    page.reorganize_page(
        layout=layout,
        drop_figure_internal_text=True,
        drop_layout_words=True,
    )
    assert page.diagnostic_noise_dropped_count == 1
    captured = page.diagnostic_noise_dropped_words[0]

    # Mutate the live page's surviving words. The captured dropped
    # word must remain intact.
    for w in page.words:
        w.word_labels.append("post-mutation")

    assert "post-mutation" not in captured.word_labels


def test_noise_drop_diagnostics_reset_on_subsequent_reorganize():
    """A second reorganize_page call must not accumulate dropped words
    from the previous pass — the attributes should reset cleanly."""
    fig_words = [
        _word("BALI", 100, 200, 140, 230),
    ]
    body_words = [
        _word("body", 100, 1000, 200, 1030),
    ]
    page = _make_page(
        [
            _paragraph_block([_line_block(fig_words)]),
            _paragraph_block([_line_block(body_words)]),
        ]
    )
    layout = PageLayout(
        regions=[
            LayoutRegion(
                type=RegionType.figure,
                L=50,
                R=400,
                T=150,
                B=300,
                confidence=0.95,
            ),
            LayoutRegion(
                type=RegionType.text,
                L=50,
                R=400,
                T=950,
                B=1100,
                confidence=0.95,
            ),
        ],
        image_width=PAGE_W,
        image_height=PAGE_H,
        detector="test",
    )
    page.reorganize_page(
        layout=layout,
        drop_figure_internal_text=True,
        drop_layout_words=True,
    )
    assert page.diagnostic_noise_dropped_count == 1

    # Second call: this time pass no layout so no noise removal fires.
    page.reorganize_page()
    assert page.diagnostic_noise_dropped_count == 0
    assert page.diagnostic_noise_dropped_words == []


def test_noise_drop_diagnostics_populated_with_capture_diagnostics_false():
    """The noise-drop accumulators are scalar-cheap and always populated,
    independent of ``capture_diagnostics``. The CLI uses them as the
    trigger for its "likely noise" warning, so they must be available
    even when the heavier Page snapshots are skipped."""
    fig_words = [
        _word("BALI", 100, 200, 140, 230),
    ]
    body_words = [
        _word("body", 100, 1000, 200, 1030),
    ]
    page = _make_page(
        [
            _paragraph_block([_line_block(fig_words)]),
            _paragraph_block([_line_block(body_words)]),
        ]
    )
    layout = PageLayout(
        regions=[
            LayoutRegion(
                type=RegionType.figure,
                L=50,
                R=400,
                T=150,
                B=300,
                confidence=0.95,
            ),
            LayoutRegion(
                type=RegionType.text,
                L=50,
                R=400,
                T=950,
                B=1100,
                confidence=0.95,
            ),
        ],
        image_width=PAGE_W,
        image_height=PAGE_H,
        detector="test",
    )
    page.reorganize_page(
        layout=layout,
        drop_figure_internal_text=True,
        drop_layout_words=True,
        capture_diagnostics=False,
    )
    # Page snapshots skipped.
    assert page.diagnostic_pure_ocr is None
    assert page.diagnostic_post_noise_removal is None
    # ...but the dropped-word list and count are still populated.
    assert page.diagnostic_noise_dropped_count == 1
    assert page.diagnostic_noise_dropped_words[0].text == "BALI"
