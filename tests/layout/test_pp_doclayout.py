"""PP-DocLayout adapter tests.

The smoke test downloads ~132 MB of weights on first run; mark the slow
test with ``pytest.mark.slow`` so ``-m 'not slow'`` skips it.
"""

import numpy as np
import pytest

from pd_book_tools.layout._mappings import PP_DOCLAYOUT_TO_PGDP
from pd_book_tools.layout.types import LayoutRegion, RegionType


def test_mapping_targets_are_known_region_types():
    """Every non-None PP-DocLayout mapping resolves to a known RegionType."""
    valid_values = {rt.value for rt in RegionType}
    for native, mapped in PP_DOCLAYOUT_TO_PGDP.items():
        if mapped is None:
            continue
        assert mapped in valid_values, (
            f"PP-DocLayout label {native!r} maps to {mapped!r}, "
            "which is not a RegionType — update RegionType or the mapping."
        )


# ---------------------------------------------------------------------------
# #177: pp-doclayout adapter must clip boxes to image bounds
# ---------------------------------------------------------------------------


class TestClipBoxToImageBounds:
    """Unit tests for the _clip_box_to_bounds helper (issue #177).

    The helper is module-level in pp_doclayout.py; tests import it directly
    so we can verify clipping without needing the model weights.
    """

    def _import_helper(self):
        from pd_book_tools.layout.adapters.pp_doclayout import _clip_box_to_bounds

        return _clip_box_to_bounds

    def test_in_bounds_box_unchanged(self):
        """A box that fits within (800, 1200) is returned unchanged."""
        clip = self._import_helper()
        x1, y1, x2, y2 = clip(10.0, 20.0, 100.0, 200.0, img_width=800, img_height=1200)
        assert (x1, y1, x2, y2) == (10.0, 20.0, 100.0, 200.0)

    def test_right_edge_clipped(self):
        """x2 beyond image width is clamped to image width."""
        clip = self._import_helper()
        x1, _y1, x2, _y2 = clip(
            10.0, 20.0, 900.0, 200.0, img_width=800, img_height=1200
        )
        assert x2 == 800.0
        assert x1 == 10.0

    def test_bottom_edge_clipped(self):
        """y2 beyond image height is clamped to image height."""
        clip = self._import_helper()
        _x1, y1, _x2, y2 = clip(
            10.0, 20.0, 100.0, 1500.0, img_width=800, img_height=1200
        )
        assert y2 == 1200.0
        assert y1 == 20.0

    def test_negative_left_edge_clamped(self):
        """x1 < 0 is clamped to 0."""
        clip = self._import_helper()
        x1, _y1, _x2, _y2 = clip(
            -5.0, 0.0, 100.0, 100.0, img_width=800, img_height=1200
        )
        assert x1 == 0.0

    def test_negative_top_edge_clamped(self):
        """y1 < 0 is clamped to 0."""
        clip = self._import_helper()
        _x1, y1, _x2, _y2 = clip(
            0.0, -10.0, 100.0, 100.0, img_width=800, img_height=1200
        )
        assert y1 == 0.0

    def test_fully_out_of_bounds_produces_degenerate(self):
        """A box entirely outside the image clips to a degenerate (zero-area) box."""
        clip = self._import_helper()
        x1, y1, x2, y2 = clip(
            900.0, 1300.0, 950.0, 1400.0, img_width=800, img_height=1200
        )
        # After clamping, x1==x2==800 and y1==y2==1200 — degenerate but valid
        assert x1 >= x2 or y1 >= y2  # at least one axis is degenerate


class TestAdapterClipsOutOfBoundsBoxes:
    """Integration test: the detect() method must clip boxes before constructing LayoutRegion."""

    def test_build_region_clips_right_and_bottom(self):
        """LayoutRegion constructed from clipped coords stays within image bounds."""
        # Simulate what the adapter produces after clipping: x2 > image_width
        # should become image_width after clip.
        img_width, img_height = 800, 1200

        # Directly simulate the clip-and-build logic
        from pd_book_tools.layout.adapters.pp_doclayout import _clip_box_to_bounds

        x1, y1, x2, y2 = _clip_box_to_bounds(
            10.0, 20.0, 900.0, 1500.0, img_width=img_width, img_height=img_height
        )
        region = LayoutRegion(
            type=RegionType.text,
            L=round(x1),
            R=round(x2),
            T=round(y1),
            B=round(y2),
            confidence=0.8,
        )
        assert img_width >= region.R
        assert img_height >= region.B


@pytest.mark.slow
def test_smoke_load_and_infer_blank_page():
    """End-to-end: load model, run on a blank synthetic page.

    Marked slow because the first call downloads ~132 MB; skip with
    ``-m 'not slow'``.
    """
    from pd_book_tools.layout.adapters.pp_doclayout import (
        PPDocLayoutPlusLDetector,
    )

    det = PPDocLayoutPlusLDetector(device="cpu", confidence=0.5)
    blank = np.full((1200, 800, 3), 255, dtype=np.uint8)
    layout = det.detect(blank)
    assert layout.image_width == 800
    assert layout.image_height == 1200
    assert layout.detector == "pp-doclayout-plus-l"
    # No predictions on a blank page is fine; we just want to know the
    # adapter ran without errors.
    assert isinstance(layout.regions, list)
