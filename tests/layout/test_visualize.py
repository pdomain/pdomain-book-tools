"""Tests for ``pd_book_tools.layout.visualize.draw_layout_overlay``."""

import numpy as np
import pytest

from pd_book_tools.layout.types import LayoutRegion, PageLayout, RegionType
from pd_book_tools.layout.visualize import draw_layout_overlay


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
    with pytest.raises(OSError, match="cv2.imwrite failed"):
        draw_layout_overlay(src, _layout_one_text_region(), dest)
