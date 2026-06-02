import cv2
import numpy as np

from pdomain_book_tools.geometry_correction.detectors.textline import (
    MorphCentroidDetector,
    TextlineDetector,
)
from pdomain_book_tools.image_processing.textline_types import LineSamples


def _lined_page(h=900, w=700, n_lines=14, top=90, gap=55):
    img = np.zeros((h, w), np.uint8)
    for i in range(n_lines):
        y = top + i * gap
        for x0 in range(60, w - 60, 70):
            cv2.rectangle(img, (x0, y), (x0 + 50, y + 10), 255, -1)
    return img


class _FakeDetector:
    name = "fake"

    def detect(self, binary, *, page_width):
        return [
            LineSamples(
                xs=np.arange(page_width, dtype=np.float64), ys=np.full(page_width, 5.0)
            )
        ]


def test_fake_detector_satisfies_protocol():
    det = _FakeDetector()
    assert isinstance(det, TextlineDetector)  # runtime_checkable Protocol
    out = det.detect(np.zeros((10, 20), np.uint8), page_width=20)
    assert len(out) == 1
    assert out[0].ys.mean() == 5.0


def test_morph_centroid_detector_recovers_lines():
    det = MorphCentroidDetector()
    assert det.name == "morph_centroid"
    page = _lined_page()
    lines = det.detect(page, page_width=page.shape[1])
    assert 12 <= len(lines) <= 14
