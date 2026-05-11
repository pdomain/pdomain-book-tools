"""Tests for ``pd_book_tools.layout.visualize.draw_layout_overlay``."""

import inspect

import numpy as np
import pytest

from pd_book_tools.layout import visualize as visualize_module
from pd_book_tools.layout.types import LayoutRegion, PageLayout, RegionType
from pd_book_tools.layout.visualize import draw_layout_overlay


def test_text_color_comment_does_not_claim_cyan():
    """L-10: BGR (200, 200, 60) is yellow-green, not cyan-ish (cyan in BGR is
    (255, 255, 0)). The original comment was misleading; this test prevents
    a future edit from re-introducing the wrong claim."""
    src = inspect.getsource(visualize_module)
    text_lines = [
        line for line in src.splitlines() if line.strip().startswith('"text":')
    ]
    assert text_lines, 'expected a "text" entry in _COLORS_BGR'
    for line in text_lines:
        # Strip out the "pre-L-10" historical breadcrumb so the regression
        # only fires on a *new* claim of cyan.
        before_l10 = line.split("L-10")[0]
        assert "cyan" not in before_l10.lower(), (
            f"misleading 'cyan' description present in: {line}"
        )


def _write_dummy_png(path):
    """Write a small valid PNG so cv2.imread succeeds."""
    import cv2

    img = np.full((400, 600, 3), 200, dtype=np.uint8)
    assert cv2.imwrite(str(path), img)


def _layout_one_text_region():
    region = LayoutRegion(type=RegionType.text, L=10, T=10, R=200, B=80, confidence=0.9)
    return PageLayout(image_width=600, image_height=400, regions=[region])


def test_draw_layout_overlay_happy_path(tmp_path):
    src = tmp_path / "src.png"
    dest = tmp_path / "out.png"
    _write_dummy_png(src)
    result = draw_layout_overlay(src, _layout_one_text_region(), dest)
    assert result == dest
    assert dest.exists()
    assert dest.stat().st_size > 0


def test_draw_layout_overlay_missing_source_returns_none(tmp_path):
    src = tmp_path / "missing.png"
    dest = tmp_path / "out.png"
    assert draw_layout_overlay(src, _layout_one_text_region(), dest) is None


def test_label_x_clamped_to_image_width(tmp_path, monkeypatch):
    """L-09: a region near the right edge previously had its label rectangle
    and text painted off-image. Now the label x-start is clamped so the
    label fits inside the image."""
    import cv2

    src = tmp_path / "src.png"
    dest = tmp_path / "out.png"
    _write_dummy_png(src)

    # Region whose L is at the very right edge of the 600-wide image.
    region = LayoutRegion(
        type=RegionType.text, L=590, T=100, R=599, B=130, confidence=0.9
    )
    layout = PageLayout(image_width=600, image_height=400, regions=[region])

    captured: list[tuple[int, int]] = []
    real_rectangle = cv2.rectangle

    def spy_rectangle(img, pt1, pt2, color, thickness=1, *args, **kwargs):
        # We only care about the filled label rectangle (thickness=-1).
        if thickness == -1:
            captured.append((pt1[0], pt2[0]))
        return real_rectangle(img, pt1, pt2, color, thickness, *args, **kwargs)

    monkeypatch.setattr(cv2, "rectangle", spy_rectangle)

    draw_layout_overlay(src, layout, dest)

    assert captured, "expected at least one label rectangle to be drawn"
    for lx_start, lx_end in captured:
        assert lx_start >= 0
        assert lx_end <= 600, (
            f"label rectangle right edge {lx_end} exceeds image width 600"
        )


def test_draw_layout_overlay_raises_oserror_on_write_failure(tmp_path, monkeypatch):
    """L-08: cv2.imwrite returning False used to be silently ignored — the
    function returned `dest_path` so callers' `is not None` check claimed
    success even when nothing was written. Now raises OSError so the
    failure surfaces."""
    import cv2

    src = tmp_path / "src.png"
    dest = tmp_path / "out.png"
    _write_dummy_png(src)

    monkeypatch.setattr(cv2, "imwrite", lambda _path, _img: False)
    with pytest.raises(OSError, match=r"cv2.imwrite failed"):
        draw_layout_overlay(src, _layout_one_text_region(), dest)
