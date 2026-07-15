from __future__ import annotations

from typing import TYPE_CHECKING

import cv2
import numpy as np

from pdomain_book_tools.geometry_correction.backends.deskew.projection import (
    ProjectionDeskew,
)

if TYPE_CHECKING:
    from cv2.typing import MatLike


def _text_page(angle_deg: float, h: int = 300, w: int = 400) -> MatLike:
    img = np.full((h, w), 255, np.uint8)
    for y in range(40, h - 40, 18):  # horizontal "text" bars
        cv2.rectangle(img, (40, y), (w - 40, y + 6), 0, -1)
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle_deg, 1.0)
    return cv2.warpAffine(img, m, (w, h), borderValue=255)


def test_recovers_known_skew() -> None:
    skewed = _text_page(4.0)
    res = ProjectionDeskew().estimate(skewed)
    assert abs(res.angle_degrees - 4.0) < 0.75  # estimated angle ~= applied
    deskewed = res.transform.apply(skewed)

    # variance of row-sum profile is higher when text rows are axis-aligned
    def row_var(im: MatLike) -> float:
        return float(np.var(np.sum(255 - im, axis=1)))

    assert row_var(deskewed) > row_var(skewed)


def test_flat_page_near_zero_angle() -> None:
    res = ProjectionDeskew().estimate(_text_page(0.0))
    assert abs(res.angle_degrees) < 0.75
