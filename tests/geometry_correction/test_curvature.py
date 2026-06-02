import cv2
import numpy as np

from pdomain_book_tools.geometry_correction.backends.curvature.image_based import (
    ImageBasedCurvature,
)


def _flat_text(h=300, w=400):
    img = np.full((h, w), 255, np.uint8)
    for y in range(40, h - 40, 18):
        cv2.rectangle(img, (40, y), (w - 40, y + 5), 0, -1)
    return img


def _curved_text(h=300, w=400, amp=14):
    img = np.full((h, w), 255, np.uint8)
    xs = np.arange(w)
    for y0 in range(40, h - 40, 18):
        ys = (y0 + amp * np.sin(np.pi * xs / w)).astype(int)  # bow the rows
        for x, y in zip(xs[40 : w - 40], ys[40 : w - 40], strict=False):
            img[y : y + 5, x] = 0
    return img


def test_flat_page_recommends_no_dewarp():
    rep = ImageBasedCurvature().score(_flat_text())
    assert rep.recommended in ("none", "deskew_only")
    assert rep.flatness < 0.3


def test_curved_page_recommends_dewarp():
    rep = ImageBasedCurvature().score(_curved_text())
    assert rep.recommended == "dewarp"
    assert rep.flatness > 0.5
