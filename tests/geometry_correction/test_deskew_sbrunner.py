import cv2
import numpy as np

from pdomain_book_tools.geometry_correction.backends.deskew.sbrunner import (
    SbrunnerDeskew,
)


def _text_page(angle_deg, h=300, w=400):
    img = np.full((h, w), 255, np.uint8)
    for y in range(40, h - 40, 18):
        cv2.rectangle(img, (40, y), (w - 40, y + 6), 0, -1)
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle_deg, 1.0)
    return cv2.warpAffine(img, m, (w, h), borderValue=255)


def test_recovers_known_skew():
    res = SbrunnerDeskew().estimate(_text_page(3.0))
    assert abs(res.angle_degrees - 3.0) < 0.75
    assert res.method == "sbrunner"
