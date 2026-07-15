"""Tests for ``Document.make_doctr_ocr_fn`` and the orientation-detection
input contract (labeler-spa live parity audit 2026-06-12, sweep row C29).

The production crash: a consumer built ``ocr_fn`` for
:func:`~pdomain_book_tools.ocr.rotation.detect_best_rotation` by calling the
raw DocTR predictor with a bare ndarray (``predictor(image)`` instead of
``predictor([image])``). DocTR iterates its ``pages`` argument, so a bare
HxWx3 array decomposes into H row-slices of shape (W, 3) and DocTR raises
``ValueError: incorrect input shape: all pages are expected to be
multi-channel 2D images.``

``Document.make_doctr_ocr_fn`` is the supported way to build a correct
``ocr_fn`` from a predictor: it wraps the image in a list, normalizes
channels (grayscale / BGR / BGRA / binarized-bool all become HxWx3 RGB),
and converts the DocTR result into a :class:`Document`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from pdomain_book_tools.ocr.document import Document
from pdomain_book_tools.ocr.rotation import detect_best_rotation
from tests.ocr.test_document_batch_ocr import _fake_doctr_result_with_words

if TYPE_CHECKING:
    from collections.abc import Iterable
    from unittest.mock import MagicMock

_DOCTR_SHAPE_ERROR = (
    "incorrect input shape: all pages are expected to be multi-channel 2D images."
)


class StrictFakePredictor:
    """Stub predictor enforcing the real DocTR input contract.

    Mirrors ``doctr/models/predictor/pytorch.py``: iterates ``pages`` and
    raises the exact production ValueError when any element is not a
    3-dimensional array. Records the pages it accepted so tests can assert
    on the shapes that reached the model.
    """

    def __init__(self, confidences: list[float] | None = None) -> None:
        self.received: list[np.ndarray] = []
        self._confidences = confidences if confidences is not None else [0.9, 0.95]

    def __call__(self, images: Iterable[np.ndarray]) -> MagicMock:
        pages_list = list(images)
        if any(getattr(page, "ndim", 0) != 3 for page in pages_list):
            raise ValueError(_DOCTR_SHAPE_ERROR)
        self.received.extend(pages_list)
        return _fake_doctr_result_with_words(len(pages_list), [self._confidences])


def _bgr_image(h: int = 8, w: int = 8) -> np.ndarray:
    rng = np.random.default_rng(0)
    return rng.integers(0, 256, (h, w, 3), dtype=np.uint8)


class TestC29Reproduction:
    """Pin the production failure mode so it stays documented."""

    def test_bare_predictor_as_ocr_fn_raises_doctr_shape_error(self):
        # A raw DocTR predictor used directly as ocr_fn receives a bare
        # ndarray and iterates it into 2D row-slices -> production crash.
        predictor = StrictFakePredictor()
        with pytest.raises(ValueError, match="multi-channel 2D images"):
            detect_best_rotation(_bgr_image(), ocr_fn=predictor)

    def test_make_doctr_ocr_fn_fixes_the_crash(self):
        predictor = StrictFakePredictor()
        ocr_fn = Document.make_doctr_ocr_fn(predictor)
        chosen, doc, probes = detect_best_rotation(_bgr_image(), ocr_fn=ocr_fn)
        assert chosen == 0  # high stub confidence -> upright fast path
        assert len(doc.pages) == 1
        assert probes[0].word_count == 2


class TestMakeDoctrOcrFnChannelMatrix:
    """Every supported input layout must reach the predictor as [HxWx3]."""

    @pytest.mark.parametrize(
        ("name", "image"),
        [
            ("bgr_3ch", np.zeros((8, 6, 3), dtype=np.uint8)),
            ("grayscale_2d", np.zeros((8, 6), dtype=np.uint8)),
            ("single_channel_3d", np.zeros((8, 6, 1), dtype=np.uint8)),
            ("bgra_4ch", np.zeros((8, 6, 4), dtype=np.uint8)),
            ("binarized_bool", np.ones((8, 6), dtype=bool)),
        ],
    )
    def test_predictor_receives_list_of_hxwx3(self, name: str, image: np.ndarray):
        predictor = StrictFakePredictor()
        ocr_fn = Document.make_doctr_ocr_fn(predictor)
        doc = ocr_fn(image)
        assert len(predictor.received) == 1, name
        assert predictor.received[0].shape == (8, 6, 3), name
        assert predictor.received[0].dtype == np.uint8, name
        assert isinstance(doc, Document), name

    def test_unsupported_channel_count_raises_value_error(self):
        predictor = StrictFakePredictor()
        ocr_fn = Document.make_doctr_ocr_fn(predictor)
        with pytest.raises(ValueError, match=r"[Uu]nsupported"):
            ocr_fn(np.zeros((8, 6, 5), dtype=np.uint8))

    def test_returns_document_with_word_confidences(self):
        predictor = StrictFakePredictor(confidences=[0.7, 0.8])
        ocr_fn = Document.make_doctr_ocr_fn(predictor)
        doc = ocr_fn(_bgr_image())
        confs = [w.ocr_confidence for w in doc.pages[0].words]
        assert confs == [0.7, 0.8]


class TestDetectBestRotationReturnContract:
    """A non-Document ocr_fn return must fail with actionable guidance."""

    def test_raw_doctr_result_return_raises_type_error(self):
        # Second latent consumer bug: ocr_fn returning the raw DocTR result
        # (whose pages have .blocks but no .words) used to AttributeError
        # deep inside _mean_confidence. It must now raise a TypeError
        # pointing at make_doctr_ocr_fn. Faithful stand-in for a real DocTR
        # Page: attribute access on .words raises AttributeError.
        class _RawDoctrPage:
            blocks: tuple[object, ...] = ()

            def render(self) -> str:
                return ""

        class _RawDoctrResult:
            pages = (_RawDoctrPage(),)

        def bad_ocr_fn(image: np.ndarray):
            return _RawDoctrResult()  # raw doctr-style result, not Document

        with pytest.raises(TypeError, match="make_doctr_ocr_fn"):
            detect_best_rotation(_bgr_image(), ocr_fn=bad_ocr_fn)  # type: ignore[arg-type]


@pytest.mark.slow
class TestOrientationDetectionRealModel:
    """End-to-end sanity: detection must actually DETECT, not just not crash.

    Uses the real (pretrained, cached) DocTR predictor on CPU. Marked slow;
    run via ``make test-slow`` or ``-m slow``.
    """

    @staticmethod
    def _render_text_page() -> np.ndarray:
        import cv2

        img = np.full((400, 600, 3), 255, dtype=np.uint8)
        lines = ["The quick brown fox", "jumps over the lazy dog", "0123456789"]
        for i, line in enumerate(lines):
            cv2.putText(
                img,
                line,
                (30, 80 + 90 * i),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (0, 0, 0),
                2,
            )
        return img

    def test_upright_and_rotated_pages_detected(self):
        from pdomain_book_tools.ocr.doctr_support import get_default_doctr_predictor
        from pdomain_book_tools.ocr.rotation import rotate_image

        predictor = get_default_doctr_predictor()
        ocr_fn = Document.make_doctr_ocr_fn(predictor)
        upright = self._render_text_page()

        # Plain RGB upright page: confident at 0 degrees (this is the exact
        # input class that crashed in the labeler's auto-rotate-all, C29).
        chosen, _doc, probes = detect_best_rotation(upright, ocr_fn=ocr_fn)
        assert chosen == 0
        assert probes[0].word_count >= 5
        assert probes[0].mean_confidence > 0.6

        # Page rotated 90 degrees clockwise: the probe must pick 270 (the
        # rotation that restores upright text).
        sideways = rotate_image(upright, 90)
        chosen_rot, doc_rot, _probes_rot = detect_best_rotation(sideways, ocr_fn=ocr_fn)
        assert chosen_rot == 270
        assert len(doc_rot.pages[0].words) >= 5
