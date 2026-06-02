import cv2
import numpy as np

from pdomain_book_tools.geometry_correction.backends.deskew.projection import (
    ProjectionDeskew,
)


def _text_page(angle_deg, h=300, w=400):
    img = np.full((h, w), 255, np.uint8)
    for y in range(40, h - 40, 18):  # horizontal "text" bars
        cv2.rectangle(img, (40, y), (w - 40, y + 6), 0, -1)
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle_deg, 1.0)
    return cv2.warpAffine(img, m, (w, h), borderValue=255)


def test_recovers_known_skew():
    skewed = _text_page(4.0)
    res = ProjectionDeskew().estimate(skewed)
    assert abs(res.angle_degrees - 4.0) < 0.75  # estimated angle ~= applied
    deskewed = res.transform.apply(skewed)

    # variance of row-sum profile is higher when text rows are axis-aligned
    def row_var(im):
        return float(np.var(np.sum(255 - im, axis=1)))

    assert row_var(deskewed) > row_var(skewed)


def test_flat_page_near_zero_angle():
    res = ProjectionDeskew().estimate(_text_page(0.0))
    assert abs(res.angle_degrees) < 0.75
