"""Fixture-based tests — exercise the layout consumers without the model.

These tests load cached :class:`PageLayout` JSON from
``tests/fixtures/layout_regression/layout_outputs/`` (regenerated via
``make layout-fixtures-regenerate``). The model itself is never invoked
here, so the suite stays fast and offline.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pd_book_tools.layout._mappings import PP_DOCLAYOUT_TO_PGDP
from pd_book_tools.layout.geometry import caption_for_figure
from pd_book_tools.layout.types import PageLayout, RegionType

FIXTURES_DIR = (
    Path(__file__).resolve().parents[1] / "fixtures" / "layout_regression" / "inputs"
)


def _cases() -> list[tuple[str, Path]]:
    if not FIXTURES_DIR.exists():
        return []
    return [
        (p.stem.replace(".layout", ""), p)
        for p in sorted(FIXTURES_DIR.glob("*.layout.json"))
    ]


CASES = _cases()


@pytest.mark.skipif(
    not CASES,
    reason="no layout fixtures present — run `make layout-fixtures-regenerate`",
)
class TestFixtureLayouts:
    @pytest.mark.parametrize("case,path", CASES, ids=[c for c, _ in CASES])
    def test_round_trip(self, case: str, path: Path):
        data = json.loads(path.read_text())
        layout = PageLayout.from_dict(data)
        assert layout.image_width > 0
        assert layout.image_height > 0
        assert layout.detector == "pp-doclayout-plus-l"
        # Every region type is one we know how to consume.
        valid = {rt.value for rt in RegionType}
        assert all(r.type.value in valid for r in layout.regions)

    @pytest.mark.parametrize("case,path", CASES, ids=[c for c, _ in CASES])
    def test_regions_inside_image_bounds(self, case: str, path: Path):
        layout = PageLayout.from_dict(json.loads(path.read_text()))
        for r in layout.regions:
            assert 0 <= r.L < r.R <= layout.image_width, (
                f"{case}: region {r.type.value} L={r.L} R={r.R} outside [0,{layout.image_width}]"
            )
            assert 0 <= r.T < r.B <= layout.image_height, (
                f"{case}: region {r.type.value} T={r.T} B={r.B} outside [0,{layout.image_height}]"
            )

    def test_caption_associates_with_figure_in_side_by_side(self):
        # The figures-side-by-side-with-captions fixture has two figures
        # (FIG. 72 and FIG. 73), each with a caption stacked below; the
        # geometry helper should pair at least one. This is the integration
        # test that justifies the caption_for_figure heuristic on real
        # model output.
        path = FIXTURES_DIR / "figures-side-by-side-with-captions.layout.json"
        if not path.exists():
            pytest.skip("figures-side-by-side-with-captions fixture missing")
        layout = PageLayout.from_dict(json.loads(path.read_text()))
        figures = layout.of_type(RegionType.figure)
        assert figures, "fixture should have at least one figure region"

        # Allow a generous gap because publishing white-space sits between
        # the figure and its caption in this fixture.
        paired = 0
        for fig in figures:
            cap = caption_for_figure(fig, layout.regions, max_gap_px=200)
            if cap is not None:
                paired += 1
        assert paired >= 1, (
            "expected at least one figure→caption pairing in "
            "figures-side-by-side-with-captions.layout.json"
        )


def test_corpus_exercises_key_region_types():
    """The fixture corpus, taken together, should cover the region types
    that drive layout-aware reorg behaviour. If this fails after a
    fixture regeneration, the corpus has lost coverage and needs a
    new fixture image with the missing type.
    """
    if not CASES:
        pytest.skip("no fixtures present")
    seen: set[str] = set()
    for _, path in CASES:
        data = json.loads(path.read_text())
        seen.update(r["type"] for r in data["regions"])
    expected = {"text", "figure", "caption", "header"}
    missing = expected - seen
    assert not missing, (
        f"fixture corpus missing region types: {missing}. "
        "Add a fixture image that exercises them."
    )


def test_mapping_targets_match_region_enum():
    """Sanity: every non-None mapping target must resolve to a RegionType.
    Lives here too (in addition to test_pp_doclayout.py) so it runs even
    if transformers regresses and the model adapter test gets skipped.
    """
    valid = {rt.value for rt in RegionType}
    for native, mapped in PP_DOCLAYOUT_TO_PGDP.items():
        if mapped is None:
            continue
        assert mapped in valid, (
            f"PP-DocLayout label {native!r} → {mapped!r} (not a RegionType)"
        )
