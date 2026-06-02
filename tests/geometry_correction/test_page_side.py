import cv2
import numpy as np

from pdomain_book_tools.geometry_correction import PageSide
from pdomain_book_tools.geometry_correction.backends.page_side.gutter_shadow import (
    GutterShadowPageSide,
)
from pdomain_book_tools.geometry_correction.backends.page_side.supplied import (
    SuppliedPageSide,
)


def test_passes_hint_through_with_gutter_edge():
    res = SuppliedPageSide().detect(np.zeros((10, 10), np.uint8), hint=PageSide.LEFT)
    assert res.side is PageSide.LEFT
    assert res.gutter_edge == "right"  # left page -> gutter on the right
    res2 = SuppliedPageSide().detect(np.zeros((10, 10), np.uint8), hint=PageSide.RIGHT)
    assert res2.gutter_edge == "left"


def test_no_hint_is_unknown_none_gutter():
    res = SuppliedPageSide().detect(np.zeros((10, 10), np.uint8))
    assert res.side is PageSide.UNKNOWN
    assert res.gutter_edge == "none"


# --- Task 10: gutter-shadow ---


def _page_with_dark_edge(side: str) -> np.ndarray:
    img = np.full((200, 300), 230, np.uint8)
    for y in range(30, 170, 14):  # some text
        cv2.rectangle(img, (40, y), (260, y + 4), 60, -1)
    if side == "right":
        img[:, 285:] = 25  # dark binding band on the right
    else:
        img[:, :15] = 25  # dark binding band on the left
    return img


def test_detects_gutter_on_right_means_left_page():
    res = GutterShadowPageSide().detect(_page_with_dark_edge("right"))
    assert res.gutter_edge == "right"
    assert res.side is PageSide.LEFT


def test_detects_gutter_on_left_means_right_page():
    res = GutterShadowPageSide().detect(_page_with_dark_edge("left"))
    assert res.gutter_edge == "left"
    assert res.side is PageSide.RIGHT


def test_hint_wins_over_weak_detection():
    blank = np.full((200, 300), 230, np.uint8)  # no clear gutter
    res = GutterShadowPageSide().detect(blank, hint=PageSide.LEFT)
    assert res.side is PageSide.LEFT
