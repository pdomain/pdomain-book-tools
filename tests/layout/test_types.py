"""Round-trip + accessor tests for ``LayoutRegion`` / ``PageLayout``.

These types are pure data — the goal is just to lock the public shape and
the to_dict/from_dict round-trip in place so the consuming apps can rely
on them as a serialization contract.
"""

import pytest

from pd_book_tools.layout.types import LayoutRegion, PageLayout, RegionType


def _region(**kwargs) -> LayoutRegion:
    defaults = dict(
        type=RegionType.figure,
        L=10,
        R=110,
        T=20,
        B=220,
        confidence=0.9,
        raw_label="image",
    )
    defaults.update(kwargs)
    return LayoutRegion(**defaults)


class TestLayoutRegion:
    def test_dimensions(self):
        r = _region(L=10, R=110, T=20, B=220)
        assert r.width == 100
        assert r.height == 200
        assert r.area == 20000
        assert r.center == (60.0, 120.0)

    def test_degenerate_area_is_zero(self):
        assert _region(L=10, R=10, T=20, B=220).area == 0
        assert _region(L=10, R=110, T=20, B=20).area == 0
        assert _region(L=110, R=10, T=20, B=220).area == 0

    def test_contains_point(self):
        r = _region(L=10, R=110, T=20, B=220)
        assert r.contains_point(50, 50)
        assert r.contains_point(10, 20)  # corner inclusive
        assert r.contains_point(110, 220)
        assert not r.contains_point(9, 50)
        assert not r.contains_point(50, 19)

    def test_round_trip(self):
        r = _region(type=RegionType.caption, raw_label="figure_title")
        roundtripped = LayoutRegion.from_dict(r.to_dict())
        assert roundtripped == r
        assert roundtripped.type is RegionType.caption

    def test_from_dict_unknown_type_raises(self):
        with pytest.raises(ValueError):
            LayoutRegion.from_dict(
                {"type": "not_a_region", "L": 0, "R": 1, "T": 0, "B": 1}
            )


class TestPageLayout:
    def test_iter_and_len(self):
        layout = PageLayout(
            regions=[_region(), _region(type=RegionType.caption)],
            image_width=2000,
            image_height=3000,
            detector="contour",
        )
        assert len(layout) == 2
        assert [r.type for r in layout] == [RegionType.figure, RegionType.caption]

    def test_of_type(self):
        layout = PageLayout(
            regions=[
                _region(type=RegionType.figure),
                _region(type=RegionType.caption),
                _region(type=RegionType.text),
            ],
        )
        assert len(layout.of_type(RegionType.figure)) == 1
        assert len(layout.of_type(RegionType.figure, RegionType.caption)) == 2
        assert len(layout.of_type(RegionType.header)) == 0

    def test_round_trip(self):
        layout = PageLayout(
            regions=[_region(), _region(type=RegionType.header, T=0, B=50)],
            image_width=2000,
            image_height=3000,
            detector="pp-doclayout-plus-l",
            inference_ms=42,
        )
        roundtripped = PageLayout.from_dict(layout.to_dict())
        assert roundtripped.image_width == 2000
        assert roundtripped.image_height == 3000
        assert roundtripped.detector == "pp-doclayout-plus-l"
        assert roundtripped.inference_ms == 42
        assert len(roundtripped.regions) == 2
        assert roundtripped.regions[1].type is RegionType.header
