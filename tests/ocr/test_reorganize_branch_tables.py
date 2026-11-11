"""Branch tables for high-risk reorganize heuristics (plan item B4).

These cover plate-noise edges, the two column-split strategies, and floated
flow with a caption prefix. Early return, soft recover, and multiset
preservation are in ``test_reorganize_early_return_and_soft_recover.py``.

Geometry is written in pixels on a 1000-wide page. ``SCALES`` reruns a case in
normalized coordinates where the heuristic is meant to handle both.
"""

from __future__ import annotations

from collections import Counter
from typing import NamedTuple

import pytest

from pdomain_book_tools.geometry.bounding_box import BoundingBox
from pdomain_book_tools.geometry.point import Point
from pdomain_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pdomain_book_tools.ocr.page import Page
from pdomain_book_tools.ocr.reorganize_page_utils import (
    StepHDecision,
    _detect_column_split,
    _detect_floated_flow_span,
    _is_gibberish_line,
    _is_weak_noise_line,
    _split_caption_like_prefix,
    absorb_caption_tails_into_caption,
    compute_page_metrics,
    drop_heuristic_figure_noise,
    expand_floated_flow_row_block,
)
from pdomain_book_tools.ocr.word import Word

PAGE_WIDTH = 1000
PAGE_HEIGHT = 2000
LINE_H = 20
PIXEL = 1.0
NORMALIZED = 1.0 / PAGE_WIDTH
SCALES = [
    pytest.param(PIXEL, id="pixel"),
    pytest.param(NORMALIZED, id="normalized"),
]
CAPTION = "Frontispiece engraving by the author"


def _box(
    left: float, top: float, right: float, bottom: float, scale: float
) -> BoundingBox:
    normalized = scale != PIXEL
    return BoundingBox(
        top_left=Point(left * scale, top * scale, is_normalized=normalized),
        bottom_right=Point(right * scale, bottom * scale, is_normalized=normalized),
        is_normalized=normalized,
    )


def _word(
    text: str,
    left: float,
    top: float,
    right: float,
    height: float = LINE_H,
    scale: float = PIXEL,
) -> Word:
    return Word(
        text=text,
        bounding_box=_box(left, top, right, top + height, scale),
        ocr_confidence=0.95,
    )


def _line_of(words: list[Word]) -> Block:
    return Block(
        items=words,
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )


def _line(
    text: str,
    left: float,
    top: float,
    right: float,
    height: float = LINE_H,
    scale: float = PIXEL,
) -> Block:
    """Return a LINE whose words share the box evenly."""
    parts = text.split()
    step = (right - left) / len(parts)
    return _line_of(
        [
            _word(part, left + i * step, top, left + (i + 1) * step, height, scale)
            for i, part in enumerate(parts)
        ]
    )


def _para(lines: list[Block]) -> Block:
    return Block(
        items=lines,
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.PARAGRAPH,
    )


def _page(lines: list[Block]) -> Page:
    return Page(
        width=PAGE_WIDTH, height=PAGE_HEIGHT, page_index=0, blocks=[_para(lines)]
    )


def _text(lines: list[Block]) -> list[str]:
    return [line.text.strip() for line in lines]


# ── Plate noise ──────────────────────────────────────────────────────────────


class NoiseCase(NamedTuple):
    weak: list[tuple[str, int]]
    strong_tops: list[int]
    removed: int


NOISE_CASES = {
    "two-weak-lines-form-a-cluster": NoiseCase(
        [("i", 100), ("a", 150)], [800], removed=2
    ),
    "solo-punctuation-far-from-text": NoiseCase([("-", 100)], [800], removed=1),
    "solo-punctuation-beside-caption": NoiseCase([("-", 775)], [800], removed=0),
    "solo-digit-may-be-a-page-number": NoiseCase([("5", 100)], [800], removed=0),
    "solo-letter-far-from-text": NoiseCase([("x", 100)], [800], removed=1),
    "solo-letter-beside-caption": NoiseCase([("x", 775)], [800], removed=0),
    "gibberish-joins-a-weak-cluster": NoiseCase(
        [("i", 50), ("BCD", 100), ("II1s1", 150)], [800], removed=3
    ),
    "gibberish-alone-does-not-trigger-the-pass": NoiseCase(
        [("BCD", 100), ("II1s1", 150)], [800], removed=0
    ),
    "six-strong-lines-is-not-a-plate": NoiseCase(
        [("i", 100), ("a", 150)], [400, 440, 480, 520, 560, 600], removed=0
    ),
    "three-strong-groups-is-not-a-plate": NoiseCase(
        [("i", 450), ("a", 500)], [100, 400, 800], removed=0
    ),
    "page-with-no-strong-line-is-left-alone": NoiseCase(
        [("i", 100), ("a", 150)], [], removed=0
    ),
}


@pytest.mark.parametrize("case", NOISE_CASES.values(), ids=NOISE_CASES.keys())
def test_drop_heuristic_figure_noise_table(case: NoiseCase) -> None:
    lines = [_line(text, 400, top, 440) for text, top in case.weak]
    lines += [_line(CAPTION, 100, top, 900) for top in case.strong_tops]
    page = _page(lines)
    before = len(page.words)

    removed = drop_heuristic_figure_noise(page)

    assert removed == case.removed
    assert len(page.words) == before - case.removed


def test_noise_pass_keeps_the_caption_text() -> None:
    page = _page(
        [
            _line("i", 400, 100, 440),
            _line("a", 400, 150, 440),
            _line(CAPTION, 100, 800, 900),
        ]
    )

    drop_heuristic_figure_noise(page)

    assert _text(list(page.lines)) == [CAPTION]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param("a", True, id="one-letter"),
        pytest.param("a b", True, id="two-one-letter-words"),
        pytest.param("abc", False, id="three-alphanumerics"),
        pytest.param("a b c", False, id="three-words"),
        pytest.param("-", True, id="punctuation-only"),
    ],
)
def test_is_weak_noise_line_table(text: str, expected: bool) -> None:
    line = _line(text, 100, 100, 200)
    metrics = compute_page_metrics(_page([line, _line(CAPTION, 100, 800, 900)]))

    assert _is_weak_noise_line(line, metrics) is expected


@pytest.mark.parametrize(
    ("protect", "expected"),
    [pytest.param(True, False, id="protected"), pytest.param(False, True, id="open")],
)
def test_tall_initial_is_protected_only_when_asked(
    protect: bool, expected: bool
) -> None:
    initial = _line("T", 100, 100, 160, height=3 * LINE_H)
    metrics = compute_page_metrics(_page([initial, _line(CAPTION, 100, 800, 900)]))

    assert _is_weak_noise_line(initial, metrics, protect_drop_caps=protect) is expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param("BCD", True, id="no-vowels"),
        pytest.param("II1s1", True, id="letters-and-digits"),
        pytest.param("TEor", True, id="odd-capitals"),
        pytest.param("The", False, id="title-case-word"),
        pytest.param("THE", False, id="upper-case-word"),
        pytest.param("the", False, id="lower-case-word"),
        pytest.param("123", False, id="digits-only"),
        pytest.param("ab", False, id="too-short"),
        pytest.param("abcdef", False, id="too-long"),
        pytest.param("a-b", False, id="not-alphanumeric"),
    ],
)
def test_is_gibberish_line_table(text: str, expected: bool) -> None:
    assert _is_gibberish_line(_line(text, 100, 100, 200)) is expected


# ── Column split: strategy 1 clusters lines, strategy 2 finds a word gutter ──


@pytest.mark.parametrize("scale", SCALES)
def test_strategy_one_splits_lines_by_left_edge(scale: float) -> None:
    lines = [
        _line("right low", 600, 130, 900, scale=scale),
        _line("left low", 100, 130, 400, scale=scale),
        _line("right high", 600, 100, 900, scale=scale),
        _line("left high", 100, 100, 400, scale=scale),
    ]

    result = _detect_column_split(lines, PAGE_WIDTH)

    assert result is not None
    left, right = result
    assert _text(left) == ["left high", "left low"]
    assert _text(right) == ["right high", "right low"]


@pytest.mark.parametrize("scale", SCALES)
def test_strategy_two_splits_lines_stitched_across_the_gutter(scale: float) -> None:
    lines = [
        _line_of(
            [
                _word(f"left{top}", 100, top, 400, scale=scale),
                _word(f"right{top}", 600, top, 900, scale=scale),
            ]
        )
        for top in (100, 130, 160, 190)
    ]

    result = _detect_column_split(lines, PAGE_WIDTH)

    assert result is not None
    left, right = result
    assert _text(left) == ["left100", "left130", "left160", "left190"]
    assert _text(right) == ["right100", "right130", "right160", "right190"]


def test_strategy_two_handles_a_lopsided_column() -> None:
    """One right-hand line fails strategy 1's two-per-side rule."""
    lines = [
        _line("left one", 100, 100, 400),
        _line("left two", 100, 130, 400),
        _line("left three", 100, 160, 400),
        _line("right one", 600, 100, 900),
    ]

    result = _detect_column_split(lines, PAGE_WIDTH)

    assert result is not None
    left, right = result
    assert _text(left) == ["left one", "left two", "left three"]
    assert _text(right) == ["right one"]


def _stitched(left_box: tuple[int, int], right_box: tuple[int, int]) -> list[Block]:
    return [
        _line_of(
            [
                _word("a", left_box[0], top, left_box[1]),
                _word("b", right_box[0], top, right_box[1]),
            ]
        )
        for top in (100, 130, 160, 190)
    ]


NO_SPLIT_CASES = {
    "fewer-than-four-lines": [
        _line("left", 100, 100, 400),
        _line("right", 600, 100, 900),
        _line("left again", 100, 130, 400),
    ],
    "columns-overlap": [
        _line("alpha", 100, 100, 650),
        _line("beta", 100, 130, 650),
        _line("gamma", 600, 100, 900),
        _line("delta", 600, 130, 900),
    ],
    "word-gap-too-small": _stitched((100, 480), (520, 900)),
    "gutter-too-near-the-left-edge": _stitched((20, 60), (300, 980)),
    "gutter-too-near-the-right-edge": _stitched((20, 700), (940, 980)),
}


@pytest.mark.parametrize("lines", NO_SPLIT_CASES.values(), ids=NO_SPLIT_CASES.keys())
def test_detect_column_split_declines(lines: list[Block]) -> None:
    assert _detect_column_split(lines, PAGE_WIDTH) is None


# ── Floated flow ─────────────────────────────────────────────────────────────

FLOW_TOPS = (200, 230, 260, 290)
BODY_TOPS_ABOVE = (60, 90, 120, 140)
BODY_TOPS_BELOW = (400, 430, 460, 490)


def _body(top: int, scale: float = PIXEL) -> Block:
    return _line(f"body {top}", 100, top, 900, scale=scale)


def _floated_lines(
    *,
    left_x: int = 200,
    right_x: int = 600,
    flow_width: int = 300,
    scale: float = PIXEL,
) -> list[Block]:
    body = [_body(top, scale) for top in BODY_TOPS_ABOVE + BODY_TOPS_BELOW]
    left = [
        _line(f"left {top}", left_x, top, left_x + flow_width, scale=scale)
        for top in FLOW_TOPS
    ]
    right = [
        _line(f"right {top}", right_x, top, right_x + flow_width, scale=scale)
        for top in FLOW_TOPS
    ]
    return body + left + right


@pytest.mark.parametrize("scale", SCALES)
def test_floated_flow_sorts_lines_into_their_bands(scale: float) -> None:
    result = _detect_floated_flow_span(_floated_lines(scale=scale), PAGE_WIDTH)

    assert result is not None
    pre, left, right, band_body, post = result
    assert _text(pre) == [f"body {top}" for top in BODY_TOPS_ABOVE]
    assert _text(left) == [f"left {top}" for top in FLOW_TOPS]
    assert _text(right) == [f"right {top}" for top in FLOW_TOPS]
    assert band_body == []
    assert _text(post) == [f"body {top}" for top in BODY_TOPS_BELOW]


def test_floated_flow_keeps_a_full_width_band_line_in_the_body() -> None:
    lines = [*_floated_lines(), _line("body inside", 100, 275, 900)]

    result = _detect_floated_flow_span(lines, PAGE_WIDTH)

    assert result is not None
    assert _text(result[3]) == ["body inside"]


NO_FLOAT_CASES = {
    "fewer-than-eight-lines": [_body(top) for top in (100, 130, 160)],
    "no-squeezed-lines": [_body(top) for top in range(100, 500, 40)],
    "only-one-squeezed-cluster": _floated_lines(left_x=200, right_x=210),
    "left-flow-sits-on-the-body-margin": _floated_lines(left_x=100),
}


@pytest.mark.parametrize("lines", NO_FLOAT_CASES.values(), ids=NO_FLOAT_CASES.keys())
def test_detect_floated_flow_declines(lines: list[Block]) -> None:
    assert _detect_floated_flow_span(lines, PAGE_WIDTH) is None


# ── Caption prefix inside a floated flow ─────────────────────────────────────


def _flow(tops: list[int], lefts: list[int] | None = None) -> list[Block]:
    xs = lefts if lefts is not None else [200] * len(tops)
    return [
        _line(f"line {top}", x, top, x + 300) for top, x in zip(tops, xs, strict=True)
    ]


def test_caption_prefix_splits_at_the_first_clear_gap() -> None:
    prefix, rest = _split_caption_like_prefix(
        _flow([100, 125, 200, 225, 250]), PAGE_WIDTH
    )

    assert _text(prefix) == ["line 100", "line 125"]
    assert _text(rest) == ["line 200", "line 225", "line 250"]


CAPTION_DECLINED = {
    "too-few-lines": _flow([100, 200]),
    "no-clear-gap": _flow([100, 125, 150, 175]),
    "gap-leaves-a-one-line-prefix": _flow([100, 200, 225, 250]),
    "prefix-is-not-left-aligned": _flow([100, 125, 200, 225], [200, 300, 200, 200]),
}


@pytest.mark.parametrize("flow", CAPTION_DECLINED.values(), ids=CAPTION_DECLINED.keys())
def test_caption_prefix_declines(flow: list[Block]) -> None:
    prefix, rest = _split_caption_like_prefix(flow, PAGE_WIDTH)

    assert prefix == []
    assert len(rest) == len(flow)


def _row_block() -> Block:
    return _para([_body(top) for top in (500, 530, 560)])


def _absorb(flow: list[Block]) -> tuple[list[str], list[str]]:
    seed = [_line("seed", 200, 100, 500)]
    caption = list(seed)
    kept = absorb_caption_tails_into_caption(
        _page([*seed, *flow]), _row_block(), flow, caption, seed
    )
    return _text(kept), _text(caption)


def test_caption_tail_next_to_the_seed_joins_the_caption() -> None:
    kept, caption = _absorb([_line("tail", 200, 125, 500)])

    assert kept == []
    assert caption == ["seed", "tail"]


@pytest.mark.parametrize(
    "tail",
    [
        pytest.param(_line("tail", 200, 300, 500), id="too-far-below"),
        pytest.param(_line("tail", 200, 125, 900), id="too-wide"),
        pytest.param(_line("tail", 700, 125, 950), id="too-far-across"),
    ],
)
def test_caption_tail_stays_in_the_flow(tail: Block) -> None:
    kept, caption = _absorb([tail])

    assert kept == ["tail"]
    assert caption == ["seed"]


def test_line_with_justified_text_below_stays_in_the_flow() -> None:
    kept, caption = _absorb(
        [
            _line("tail", 200, 125, 500),
            _line("next", 200, 150, 500),
            _line("last", 200, 175, 500),
        ]
    )

    assert kept == ["tail", "next", "last"]
    assert caption == ["seed"]


def _expand(left: list[Block], right: list[Block]) -> list[Block]:
    decisions: list[StepHDecision] = []
    blocks = expand_floated_flow_row_block(
        _page([*left, *right]),
        _row_block(),
        ([], left, right, [], []),
        row_idx=1,
        debug_squeezed_lines=[],
        step_h_decisions=decisions,
    )
    assert decisions[0]["kind"] == "floated_flow"
    return blocks


def _word_counts(lines: list[Block]) -> Counter[str]:
    return Counter(word.text for line in lines for word in line.words)


def test_floated_caption_prefix_becomes_a_left_sidenote() -> None:
    left = _flow([100, 125, 300, 330, 360])
    right = _flow([300, 330], [600, 600])

    blocks = _expand(left, right)

    assert len(blocks) == 2
    main, sidenote = blocks
    assert _text(list(sidenote.lines)) == ["line 100", "line 125"]
    assert sidenote.block_role_labels == ["sidenote"]
    assert sidenote.block_position_labels == ["margin left"]
    assert _word_counts([*main.lines, *sidenote.lines]) == _word_counts([*left, *right])


def test_floated_flow_without_a_caption_is_one_block() -> None:
    left = _flow([300, 330, 360])
    right = _flow([300, 330], [600, 600])

    blocks = _expand(left, right)

    assert len(blocks) == 1
    assert _word_counts(list(blocks[0].lines)) == _word_counts([*left, *right])
