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


def test_morph_centroid_detector_default_binarization_is_otsu():
    det = MorphCentroidDetector()
    assert det.binarization == "otsu"
    assert det.binarization_params is None


def test_morph_centroid_detector_binarization_param_threaded():
    """binarization kwarg is stored and forwarded (smoke test — no GPU needed)."""
    det = MorphCentroidDetector(binarization="sauvola", binarization_params={"k": 0.3})
    assert det.binarization == "sauvola"
    assert det.binarization_params == {"k": 0.3}
    # Verify it can actually run on a gradient page (dark text on uneven background)
    bg = np.linspace(240, 120, 700, dtype=np.float32)
    img = np.tile(bg, (900, 1)).astype(np.uint8)
    for i in range(14):
        y = 90 + i * 55
        for x0 in range(60, 700 - 60, 70):
            img[y : y + 10, x0 : x0 + 50] = 30
    lines = det.detect(img, page_width=img.shape[1])
    assert len(lines) >= 6  # recovers most lines under illumination gradient
