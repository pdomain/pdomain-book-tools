"""PP-DocLayout adapter tests.

The smoke test downloads ~132 MB of weights on first run; mark the slow
test with ``pytest.mark.slow`` so ``-m 'not slow'`` skips it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from pdomain_book_tools.layout._mappings import PP_DOCLAYOUT_TO_PGDP
from pdomain_book_tools.layout.types import LayoutRegion, RegionType

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from unittest.mock import MagicMock

    from pdomain_book_tools.layout.adapters.pp_doclayout import (
        PPDocLayoutPlusLDetector,
    )


def test_mapping_targets_are_known_region_types() -> None:
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

    def _import_helper(self) -> Callable[..., tuple[float, float, float, float]]:
        from pdomain_book_tools.layout.adapters.pp_doclayout import _clip_box_to_bounds

        return _clip_box_to_bounds

    def test_in_bounds_box_unchanged(self) -> None:
        """A box that fits within (800, 1200) is returned unchanged."""
        clip = self._import_helper()
        x1, y1, x2, y2 = clip(10.0, 20.0, 100.0, 200.0, img_width=800, img_height=1200)
        assert (x1, y1, x2, y2) == (10.0, 20.0, 100.0, 200.0)

    def test_right_edge_clipped(self) -> None:
        """x2 beyond image width is clamped to image width."""
        clip = self._import_helper()
        x1, _y1, x2, _y2 = clip(
            10.0, 20.0, 900.0, 200.0, img_width=800, img_height=1200
        )
        assert x2 == 800.0
        assert x1 == 10.0

    def test_bottom_edge_clipped(self) -> None:
        """y2 beyond image height is clamped to image height."""
        clip = self._import_helper()
        _x1, y1, _x2, y2 = clip(
            10.0, 20.0, 100.0, 1500.0, img_width=800, img_height=1200
        )
        assert y2 == 1200.0
        assert y1 == 20.0

    def test_negative_left_edge_clamped(self) -> None:
        """x1 < 0 is clamped to 0."""
        clip = self._import_helper()
        x1, _y1, _x2, _y2 = clip(
            -5.0, 0.0, 100.0, 100.0, img_width=800, img_height=1200
        )
        assert x1 == 0.0

    def test_negative_top_edge_clamped(self) -> None:
        """y1 < 0 is clamped to 0."""
        clip = self._import_helper()
        _x1, y1, _x2, _y2 = clip(
            0.0, -10.0, 100.0, 100.0, img_width=800, img_height=1200
        )
        assert y1 == 0.0

    def test_fully_out_of_bounds_produces_degenerate(self) -> None:
        """A box entirely outside the image clips to a degenerate (zero-area) box."""
        clip = self._import_helper()
        x1, y1, x2, y2 = clip(
            900.0, 1300.0, 950.0, 1400.0, img_width=800, img_height=1200
        )
        # After clamping, x1==x2==800 and y1==y2==1200 — degenerate but valid
        assert x1 >= x2 or y1 >= y2  # at least one axis is degenerate


class TestAdapterClipsOutOfBoundsBoxes:
    """Integration test: the detect() method must clip boxes before constructing LayoutRegion."""

    def test_build_region_clips_right_and_bottom(self) -> None:
        """LayoutRegion constructed from clipped coords stays within image bounds."""
        # Simulate what the adapter produces after clipping: x2 > image_width
        # should become image_width after clip.
        img_width, img_height = 800, 1200

        # Directly simulate the clip-and-build logic
        from pdomain_book_tools.layout.adapters.pp_doclayout import _clip_box_to_bounds

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
def test_smoke_load_and_infer_blank_page() -> None:
    """End-to-end: load model, run on a blank synthetic page.

    Marked slow because the first call downloads ~132 MB; skip with
    ``-m 'not slow'``.
    """
    from pdomain_book_tools.layout.adapters.pp_doclayout import (
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


# ---------------------------------------------------------------------------
# #190: custom layout checkpoint loading is an untrusted-model boundary
# ---------------------------------------------------------------------------


class TestCheckpointTrustBoundary:
    """Tests for the checkpoint loading trust boundary (issue #190).

    The adapter must:
    - Accept ``local_files_only=True`` and forward it to from_pretrained so
      callers can guarantee no network access (high-security mode).
    - Raise ``ValueError`` when a custom ``checkpoint_path`` looks like a
      remote HF repo ID and ``local_files_only`` is not explicitly set,
      unless the caller also passes ``trust_remote_checkpoint=True``.

    These tests mock from_pretrained so they never actually download weights.
    """

    def _get_cls(self) -> type[PPDocLayoutPlusLDetector]:
        from pdomain_book_tools.layout.adapters.pp_doclayout import (
            PPDocLayoutPlusLDetector,
        )

        return PPDocLayoutPlusLDetector

    def test_local_path_with_local_files_only_accepted(self, tmp_path: Path) -> None:
        """A local directory checkpoint with local_files_only=True is accepted
        without raising and passes local_files_only to from_pretrained."""
        from unittest import mock

        from pdomain_book_tools.layout.adapters.pp_doclayout import (
            PPDocLayoutPlusLDetector,
        )

        class _FakeFromPretrained:
            """Records the kwargs it was last called with, for assertion."""

            def __init__(self) -> None:
                self.last_kwargs: dict[str, object] = {}

            def __call__(self, repo_id: str, **kwargs: object) -> MagicMock:
                self.last_kwargs = dict(kwargs)
                m = mock.MagicMock()
                m.to.return_value = m
                m.eval.return_value = m
                m.config.id2label = {}
                return m

        fake_from_pretrained = _FakeFromPretrained()

        with (
            mock.patch(
                "pdomain_book_tools.layout.adapters.pp_doclayout.RTDetrImageProcessor.from_pretrained",
                side_effect=fake_from_pretrained,
            ),
            mock.patch(
                "pdomain_book_tools.layout.adapters.pp_doclayout.RTDetrForObjectDetection.from_pretrained",
                side_effect=fake_from_pretrained,
            ),
        ):
            local_dir = str(tmp_path)
            # Must not raise even though checkpoint_path is supplied.
            PPDocLayoutPlusLDetector(
                checkpoint_path=local_dir,
                local_files_only=True,
            )
        # from_pretrained must have received local_files_only=True
        assert fake_from_pretrained.last_kwargs.get("local_files_only") is True

    def test_remote_custom_repo_without_opt_in_raises(self) -> None:
        """Passing a remote HF repo ID as checkpoint_path (non-local path)
        without ``trust_remote_checkpoint=True`` must raise ValueError."""
        from pdomain_book_tools.layout.adapters.pp_doclayout import (
            PPDocLayoutPlusLDetector,
        )

        # HF repo IDs look like "owner/repo" — no leading "/" or "."
        with pytest.raises(ValueError, match="trust_remote_checkpoint"):
            PPDocLayoutPlusLDetector(checkpoint_path="some-org/custom-model")

    def test_remote_custom_repo_with_opt_in_accepted(self, tmp_path: Path) -> None:
        """With trust_remote_checkpoint=True, a remote HF repo ID is allowed."""
        from unittest import mock

        from pdomain_book_tools.layout.adapters.pp_doclayout import (
            PPDocLayoutPlusLDetector,
        )

        def fake_from_pretrained(repo_id: str, **kwargs: object) -> MagicMock:
            m = mock.MagicMock()
            m.to.return_value = m
            m.eval.return_value = m
            m.config.id2label = {}
            return m

        with (
            mock.patch(
                "pdomain_book_tools.layout.adapters.pp_doclayout.RTDetrImageProcessor.from_pretrained",
                side_effect=fake_from_pretrained,
            ),
            mock.patch(
                "pdomain_book_tools.layout.adapters.pp_doclayout.RTDetrForObjectDetection.from_pretrained",
                side_effect=fake_from_pretrained,
            ),
        ):
            # Must not raise when the caller explicitly opts in
            PPDocLayoutPlusLDetector(
                checkpoint_path="some-org/custom-model",
                trust_remote_checkpoint=True,
            )

    def test_default_repo_does_not_require_opt_in(self, tmp_path: Path) -> None:
        """The built-in pinned fork (HF_REPO) never requires trust_remote_checkpoint.
        The default constructor must not raise even without any special flags."""
        from unittest import mock

        from pdomain_book_tools.layout.adapters.pp_doclayout import (
            PPDocLayoutPlusLDetector,
        )

        def fake_from_pretrained(repo_id: str, **kwargs: object) -> MagicMock:
            m = mock.MagicMock()
            m.to.return_value = m
            m.eval.return_value = m
            m.config.id2label = {}
            return m

        with (
            mock.patch(
                "pdomain_book_tools.layout.adapters.pp_doclayout.RTDetrImageProcessor.from_pretrained",
                side_effect=fake_from_pretrained,
            ),
            mock.patch(
                "pdomain_book_tools.layout.adapters.pp_doclayout.RTDetrForObjectDetection.from_pretrained",
                side_effect=fake_from_pretrained,
            ),
        ):
            # Must not raise — no checkpoint_path means the default fork
            PPDocLayoutPlusLDetector()
