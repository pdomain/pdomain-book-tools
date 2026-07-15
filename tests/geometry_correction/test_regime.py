from __future__ import annotations

from typing import TYPE_CHECKING

import cv2
import numpy as np

from pdomain_book_tools.geometry_correction.regime import RegimeDetector, RegimeReport

if TYPE_CHECKING:
    from cv2.typing import MatLike
    from numpy.typing import NDArray


def _flat_page(h: int = 900, w: int = 700) -> NDArray[np.uint8]:
    img = np.full((h, w), 255, np.uint8)
    for y in range(90, h - 90, 55):
        for x0 in range(60, w - 60, 70):
            cv2.rectangle(img, (x0, y), (x0 + 50, y + 10), 0, -1)
    return img


def _curled_page(h: int = 900, w: int = 700, amp: int = 26) -> NDArray[np.uint8]:
    img = np.full((h, w), 255, np.uint8)
    xs = np.arange(w)
    for y0 in range(110, h - 110, 60):
        ys = (y0 + amp * (1 - ((xs - w / 2) / (w / 2)) ** 2)).astype(int)
        for x in range(60, w - 60):
            img[ys[x] : ys[x] + 10, x] = 0
    return img


def _oblique_page(h: int = 900, w: int = 700) -> MatLike:
    """Flat baselines but strongly converging left/right page borders (keystone)."""
    flat = _flat_page(h, w)
    src = np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype=np.float32)
    dst = np.array(
        [[120, 0], [w - 120, 0], [w, h], [0, h]], dtype=np.float32
    )  # top edge pinched in
    mat = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(flat, mat, (w, h), borderValue=255)


def test_flat_page_is_flat() -> None:
    assert RegimeDetector().classify(_flat_page()).regime == "flat"


def test_curled_page_is_flat_curl() -> None:
    rep = RegimeDetector().classify(_curled_page())
    assert isinstance(rep, RegimeReport)
    assert rep.regime == "flat_curl"


def test_oblique_page_is_oblique() -> None:
    assert RegimeDetector().classify(_oblique_page()).regime == "oblique"
