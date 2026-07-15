"""Round-trip + accessor tests for ``LayoutRegion`` / ``PageLayout``.

These types are pure data — the goal is just to lock the public shape and
the to_dict/from_dict round-trip in place so the consuming apps can rely
on them as a serialization contract.
"""

from __future__ import annotations

from typing import TypedDict, Unpack

import pytest

from pdomain_book_tools.layout.types import LayoutRegion, PageLayout, RegionType


class _RegionOverrides(TypedDict, total=False):
    """Keyword overrides accepted by :func:`_region`, mirroring the
    ``LayoutRegion`` constructor fields."""

    type: RegionType
    L: int
    R: int
    T: int
    B: int
    confidence: float
    raw_label: str


def _region(**overrides: Unpack[_RegionOverrides]) -> LayoutRegion:
    return LayoutRegion(
        type=overrides.get("type", RegionType.figure),
        L=overrides.get("L", 10),
        R=overrides.get("R", 110),
        T=overrides.get("T", 20),
        B=overrides.get("B", 220),
        confidence=overrides.get("confidence", 0.9),
        raw_label=overrides.get("raw_label", "image"),
    )


class TestLayoutRegion:
    def test_dimensions(self) -> None:
        r = _region(L=10, R=110, T=20, B=220)
        assert r.width == 100
        assert r.height == 200
        assert r.area == 20000
        assert r.center == (60.0, 120.0)

    def test_degenerate_area_is_zero(self) -> None:
        # Zero-width / zero-height (L == R or T == B) are accepted; only the
        # area is zero. Inverted coordinates (L > R, T > B) are rejected at
        # construction — see test_inverted_coordinates_rejected.
        assert _region(L=10, R=10, T=20, B=220).area == 0
        assert _region(L=10, R=110, T=20, B=20).area == 0

    def test_inverted_coordinates_rejected(self) -> None:
        # L-31: silently accepting L > R / T > B caused width to go negative
        # and contains_point to return wrong results.
        with pytest.raises(ValueError, match=r"L .* R"):
            _region(L=110, R=10, T=20, B=220)
        with pytest.raises(ValueError, match=r"T .* B"):
            _region(L=10, R=110, T=220, B=20)

    def test_contains_point(self) -> None:
        r = _region(L=10, R=110, T=20, B=220)
        assert r.contains_point(50, 50)
        assert r.contains_point(10, 20)  # corner inclusive
        assert r.contains_point(110, 220)
        assert not r.contains_point(9, 50)
        assert not r.contains_point(50, 19)

    def test_round_trip(self) -> None:
        r = _region(type=RegionType.caption, raw_label="figure_title")
        roundtripped = LayoutRegion.from_dict(r.to_dict())
        assert roundtripped == r
        assert roundtripped.type is RegionType.caption

    def test_hashable(self) -> None:
        # L-32: regions need to be usable in sets / dict keys so callers
        # don't have to fall back to identity-based ``r is figure`` checks
        # (see ``caption_for_figure`` for the historical workaround).
        r1 = _region(L=10, R=110, T=20, B=220, type=RegionType.figure)
        r2 = _region(L=10, R=110, T=20, B=220, type=RegionType.figure)
        r3 = _region(L=10, R=110, T=20, B=220, type=RegionType.caption)
        assert hash(r1) == hash(r2)
        assert {r1, r2, r3} == {r1, r3}

    def test_from_dict_unknown_type_raises(self) -> None:
        with pytest.raises(ValueError):
            LayoutRegion.from_dict(
                {"type": "not_a_region", "L": 0, "R": 1, "T": 0, "B": 1}
            )

    def test_string_type_coerced_to_enum(self) -> None:
        # #176: direct construction with type="text" (string) used to succeed
        # but then crash in to_dict() when self.type.value was called on a str.
        r = LayoutRegion(type="text", L=0, R=10, T=0, B=10)  # type: ignore[arg-type]
        # Must survive to_dict() — self.type must be a RegionType, not a str.
        d = r.to_dict()
        assert d["type"] == "text"
        assert r.type is RegionType.text

    def test_invalid_string_type_raises(self) -> None:
        # #176: unknown string must raise ValueError, not silently set type to
        # a string and defer the crash to to_dict().
        with pytest.raises(ValueError):
            LayoutRegion(type="not_a_real_type", L=0, R=10, T=0, B=10)  # type: ignore[arg-type]

    def test_non_finite_confidence_rejected(self) -> None:
        # #176: NaN/infinity confidence produces non-standard JSON and breaks
        # sorting — reject at construction.

        with pytest.raises(ValueError, match="confidence"):
            LayoutRegion(
                type=RegionType.text, L=0, R=10, T=0, B=10, confidence=float("nan")
            )
        with pytest.raises(ValueError, match="confidence"):
            LayoutRegion(
                type=RegionType.text, L=0, R=10, T=0, B=10, confidence=float("inf")
            )
        with pytest.raises(ValueError, match="confidence"):
            LayoutRegion(type=RegionType.text, L=0, R=10, T=0, B=10, confidence=-0.1)
        with pytest.raises(ValueError, match="confidence"):
            LayoutRegion(type=RegionType.text, L=0, R=10, T=0, B=10, confidence=1.1)

    def test_confidence_boundary_values_accepted(self) -> None:
        # 0.0 and 1.0 are valid confidence values.
        r0 = LayoutRegion(type=RegionType.text, L=0, R=10, T=0, B=10, confidence=0.0)
        r1 = LayoutRegion(type=RegionType.text, L=0, R=10, T=0, B=10, confidence=1.0)
        assert r0.confidence == 0.0
        assert r1.confidence == 1.0


class TestPageLayout:
    def test_iter_and_len(self) -> None:
        layout = PageLayout(
            regions=[_region(), _region(type=RegionType.caption)],
            image_width=2000,
            image_height=3000,
            detector="contour",
        )
        assert len(layout) == 2
        assert [r.type for r in layout] == [RegionType.figure, RegionType.caption]

    def test_of_type(self) -> None:
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

    def test_of_type_no_args_raises(self) -> None:
        """R-26: ``of_type()`` with no arguments used to silently return
        ``[]`` (because ``r.type in set()`` is always False), looking like
        "no regions found" rather than "all regions." Now raises ValueError."""
        layout = PageLayout(regions=[_region(type=RegionType.figure)])
        with pytest.raises(ValueError, match="at least one RegionType"):
            layout.of_type()

    def test_round_trip(self) -> None:
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
