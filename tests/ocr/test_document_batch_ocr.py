"""Tests for Document.from_images_ocr_via_doctr (batch OCR entry point)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import numpy as np
import pytest

from pdomain_book_tools.ocr.document import Document

if TYPE_CHECKING:
    from collections.abc import Sequence


def _make_rgb_image(h: int = 8, w: int = 8) -> np.ndarray:
    """Return a tiny synthetic RGB uint8 ndarray."""
    rng = np.random.default_rng(0)
    return rng.integers(0, 256, (h, w, 3), dtype=np.uint8)


def _fake_doctr_result(n_pages: int) -> MagicMock:
    """Return a stub DocTR result with *n_pages* empty pages."""
    page_render = MagicMock(return_value="")
    fake_page = MagicMock()
    fake_page.render = page_render

    result = MagicMock()
    result.pages = [MagicMock() for _ in range(n_pages)]
    for p in result.pages:
        p.render = MagicMock(return_value="")

    export_pages: list[dict[str, object]] = [
        {"dimensions": (8, 8), "blocks": []} for _ in range(n_pages)
    ]
    result.export = MagicMock(return_value={"pages": export_pages})
    return result


def _fake_doctr_result_with_words(
    n_pages: int, confidences_per_page: list[list[float]]
) -> MagicMock:
    """Return a stub DocTR result with pages that have words with given confidences.

    ``confidences_per_page`` is a list-of-lists - one inner list per page.
    """
    result = MagicMock()
    result.pages = [MagicMock() for _ in range(n_pages)]
    for p in result.pages:
        p.render = MagicMock(return_value="")

    export_pages: list[dict[str, object]] = []
    for i in range(n_pages):
        page_confs = confidences_per_page[i] if i < len(confidences_per_page) else []
        words = [
            {"value": f"word{j}", "geometry": [[0, 0], [0.1, 0.1]], "confidence": c}
            for j, c in enumerate(page_confs)
        ]
        line = {"geometry": [[0, 0], [0.5, 0.5]], "words": words}
        block = {"geometry": [[0, 0], [1.0, 1.0]], "lines": [line], "artefacts": []}
        export_pages.append({"dimensions": (8, 8), "blocks": [block]})

    result.export = MagicMock(return_value={"pages": export_pages})
    return result


class TestFromImagesOcrViaDoctr:
    def test_predictor_called_once_with_list(self) -> None:
        img_a = _make_rgb_image()
        img_b = _make_rgb_image()

        fake_result = _fake_doctr_result(2)
        call_args: list[object] = []

        def stub_predictor(images: Sequence[np.ndarray]) -> MagicMock:
            call_args.append(images)
            assert len(images) == 2, "predictor must receive both images in one call"
            return fake_result

        doc, _degrees = Document.from_images_ocr_via_doctr(
            [img_a, img_b],
            source_identifiers=["a", "b"],
            predictor=stub_predictor,
            auto_rotate=False,  # empty pages have 0 confidence; skip rotation to test batch mechanics
        )

        assert len(call_args) == 1, "predictor must be called exactly once"
        assert doc is not None

    def test_returns_document_with_correct_page_count(self) -> None:
        img_a = _make_rgb_image()
        img_b = _make_rgb_image()

        fake_result = _fake_doctr_result(2)

        def stub_predictor(images: Sequence[np.ndarray]) -> MagicMock:
            return fake_result

        doc, _degrees = Document.from_images_ocr_via_doctr(
            [img_a, img_b],
            source_identifiers=["a", "b"],
            predictor=stub_predictor,
            auto_rotate=False,
        )

        assert len(doc.pages) == 2

    def test_source_identifiers_preserved_in_order(self) -> None:
        img_a = _make_rgb_image()
        img_b = _make_rgb_image()

        fake_result = _fake_doctr_result(2)

        def stub_predictor(images: Sequence[np.ndarray]) -> MagicMock:
            return fake_result

        doc, _degrees = Document.from_images_ocr_via_doctr(
            [img_a, img_b],
            source_identifiers=["alpha", "beta"],
            predictor=stub_predictor,
            auto_rotate=False,
        )

        pages = doc.pages
        assert pages[0].page_index == 0
        assert pages[1].page_index == 1

    def test_single_image_list_works(self) -> None:
        img = _make_rgb_image()
        fake_result = _fake_doctr_result(1)

        def stub_predictor(images: Sequence[np.ndarray]) -> MagicMock:
            assert len(images) == 1
            return fake_result

        doc, _degrees = Document.from_images_ocr_via_doctr(
            [img],
            source_identifiers=["only"],
            predictor=stub_predictor,
            auto_rotate=False,
        )

        assert len(doc.pages) == 1

    def test_empty_list_raises(self) -> None:
        with pytest.raises((ValueError, IndexError)):
            Document.from_images_ocr_via_doctr(
                [],
                source_identifiers=[],
                predictor=MagicMock(),
            )

    def test_mismatched_identifiers_raises(self) -> None:
        img = _make_rgb_image()
        with pytest.raises((ValueError, TypeError)):
            Document.from_images_ocr_via_doctr(
                [img],
                source_identifiers=["a", "extra"],
                predictor=MagicMock(),
            )


class TestFromImagesOcrViaDoctrAutoRotate:
    """Tests for auto_rotate parameter on the batch OCR method."""

    def test_auto_rotate_false_skips_rotation(self) -> None:
        """With auto_rotate=False the predictor is called exactly once."""
        img_a = _make_rgb_image(8, 8)
        img_b = _make_rgb_image(8, 8)

        call_count = {"n": 0}
        fake_result = _fake_doctr_result(2)

        def predictor(images: Sequence[np.ndarray]) -> MagicMock:
            call_count["n"] += 1
            return fake_result

        doc, _degrees = Document.from_images_ocr_via_doctr(
            [img_a, img_b],
            source_identifiers=["a", "b"],
            predictor=predictor,
            auto_rotate=False,
        )

        assert call_count["n"] == 1, (
            "predictor called exactly once with auto_rotate=False"
        )
        assert len(doc.pages) == 2

    def test_auto_rotate_true_is_default(self) -> None:
        """Calling without auto_rotate keyword should behave like auto_rotate=True."""
        img = _make_rgb_image(8, 8)
        # High-confidence result so no rotation probes needed
        fake_result = _fake_doctr_result_with_words(1, [[0.95, 0.92]])

        call_count = {"n": 0}

        def predictor(images: Sequence[np.ndarray]) -> MagicMock:
            call_count["n"] += 1
            return fake_result

        doc, _degrees = Document.from_images_ocr_via_doctr(
            [img],
            predictor=predictor,
        )
        # High confidence: only the initial batch call
        assert call_count["n"] == 1
        assert len(doc.pages) == 1

    def test_high_confidence_upright_no_extra_calls(self) -> None:
        """High-confidence pages should NOT trigger additional predictor calls."""
        img_a = _make_rgb_image(8, 8)
        img_b = _make_rgb_image(8, 8)

        call_count = {"n": 0}
        fake_result = _fake_doctr_result_with_words(2, [[0.95, 0.9], [0.88, 0.91]])

        def predictor(images: Sequence[np.ndarray]) -> MagicMock:
            call_count["n"] += 1
            return fake_result

        doc, _degrees = Document.from_images_ocr_via_doctr(
            [img_a, img_b],
            source_identifiers=["a", "b"],
            predictor=predictor,
            auto_rotate=True,
        )

        assert call_count["n"] == 1, "no re-OCR needed when confidence is high"
        assert len(doc.pages) == 2

    def test_low_confidence_page_triggers_rotation_recovery(self) -> None:
        """A page with mean confidence below threshold should be re-OCR'd after rotation."""
        # Image A: 8x8 upright - high confidence (no re-OCR needed)
        # Image B: 8x12 upright - low confidence (needs rotation recovery)
        img_a = _make_rgb_image(8, 8)
        img_b = _make_rgb_image(8, 12)

        call_record: list[int] = []

        def predictor(images: Sequence[np.ndarray]) -> MagicMock:
            call_record.append(len(images))
            if len(images) == 2:
                # Initial batch: img_a high confidence, img_b low confidence
                return _fake_doctr_result_with_words(2, [[0.95, 0.9], [0.1, 0.15]])
            # Re-OCR for img_b rotation recovery - high confidence
            return _fake_doctr_result_with_words(1, [[0.9, 0.88]])

        doc, _degrees = Document.from_images_ocr_via_doctr(
            [img_a, img_b],
            source_identifiers=["a", "b"],
            predictor=predictor,
            auto_rotate=True,
        )

        # First call was the batch, subsequent calls were single-image re-OCR probes
        assert call_record[0] == 2, "first call must be the 2-image batch"
        assert len(call_record) > 1, "low-confidence page must trigger re-OCR probes"
        assert len(doc.pages) == 2
        # Both pages must survive in order
        assert doc.pages[0].page_index == 0
        assert doc.pages[1].page_index == 1

    def test_rotated_page_image_stashed_on_page(self) -> None:
        """After rotation recovery the page's cv2_numpy_page_image must be set."""
        img = _make_rgb_image(4, 8)  # non-square so rotation changes dims

        call_count = {"n": 0}

        def predictor(images: Sequence[np.ndarray]) -> MagicMock:
            call_count["n"] += 1
            if call_count["n"] == 1:
                # Batch: low confidence -> trigger rotation recovery
                return _fake_doctr_result_with_words(1, [[0.1]])
            # Re-OCR at rotated orientation: high confidence
            return _fake_doctr_result_with_words(1, [[0.9, 0.85]])

        doc, _degrees = Document.from_images_ocr_via_doctr(
            [img],
            predictor=predictor,
            auto_rotate=True,
        )

        assert len(doc.pages) == 1
        page = doc.pages[0]
        # cv2_numpy_page_image should be set (not None) after rotation stash
        assert page.cv2_numpy_page_image is not None

    def test_upright_page_image_stashed_when_confident(self) -> None:
        """When upright confidence is already high, page image must still be stashed."""
        img = _make_rgb_image(8, 8)

        def predictor(images: Sequence[np.ndarray]) -> MagicMock:
            return _fake_doctr_result_with_words(1, [[0.95, 0.9]])

        doc, _degrees = Document.from_images_ocr_via_doctr(
            [img],
            predictor=predictor,
            auto_rotate=True,
        )

        assert len(doc.pages) == 1
        page = doc.pages[0]
        assert page.cv2_numpy_page_image is not None

    def test_auto_rotate_false_page_image_still_stashed(self) -> None:
        """With auto_rotate=False the page image should also be stashed."""
        img = _make_rgb_image(8, 8)

        def predictor(images: Sequence[np.ndarray]) -> MagicMock:
            return _fake_doctr_result_with_words(1, [[0.5]])

        doc, _degrees = Document.from_images_ocr_via_doctr(
            [img],
            predictor=predictor,
            auto_rotate=False,
        )

        assert len(doc.pages) == 1
        page = doc.pages[0]
        assert page.cv2_numpy_page_image is not None

    def test_page_order_preserved_after_rotation(self) -> None:
        """Document pages must maintain correct order after partial rotation recovery."""
        img_a = _make_rgb_image(8, 8)
        img_b = _make_rgb_image(8, 8)
        img_c = _make_rgb_image(8, 8)

        call_count = {"n": 0}

        def predictor(images: Sequence[np.ndarray]) -> MagicMock:
            call_count["n"] += 1
            if call_count["n"] == 1:
                # Batch: page 1 (index 1) low confidence; others high
                return _fake_doctr_result_with_words(
                    3, [[0.9, 0.88], [0.1, 0.12], [0.92, 0.87]]
                )
            # Re-OCR for the low-confidence page: return high confidence
            return _fake_doctr_result_with_words(1, [[0.9]])

        doc, _degrees = Document.from_images_ocr_via_doctr(
            [img_a, img_b, img_c],
            source_identifiers=["a", "b", "c"],
            predictor=predictor,
            auto_rotate=True,
        )

        assert len(doc.pages) == 3
        pages = doc.pages
        assert pages[0].page_index == 0
        assert pages[1].page_index == 1
        assert pages[2].page_index == 2

    def test_custom_threshold_respected(self) -> None:
        """Setting auto_rotate_threshold=0.0 means any confidence passes upright."""
        img = _make_rgb_image(8, 8)
        call_count = {"n": 0}

        def predictor(images: Sequence[np.ndarray]) -> MagicMock:
            call_count["n"] += 1
            # Even very low confidence result
            return _fake_doctr_result_with_words(1, [[0.05, 0.1]])

        doc, _degrees = Document.from_images_ocr_via_doctr(
            [img],
            predictor=predictor,
            auto_rotate=True,
            auto_rotate_threshold=0.0,
        )

        # With threshold=0.0 even confidence=0.0 passes -> single batch call only
        assert call_count["n"] == 1
        assert len(doc.pages) == 1

    def test_returns_document_and_one_degree_per_page(self) -> None:
        """Each page reports the chosen angle, in page order.

        An empty upright page stays at 0. The return is not a single
        batch-wide ``tuple[Document, int]``.
        """
        img_a = _make_rgb_image()
        img_b = _make_rgb_image()
        fake_result = _fake_doctr_result(2)

        def predictor(images: Sequence[np.ndarray]) -> MagicMock:
            return fake_result

        doc, degrees = Document.from_images_ocr_via_doctr(
            [img_a, img_b],
            predictor=predictor,
            auto_rotate=False,
        )
        assert isinstance(doc, Document)
        assert degrees == [0, 0]

    def test_reports_the_chosen_degree_for_each_page(self) -> None:
        """A confident page stays at 0. A recovered page reports 90.

        The first fallback that beats the upright pass is 90 degrees.
        """
        img_a = _make_rgb_image(8, 8)
        img_b = _make_rgb_image(8, 12)

        def predictor(images: Sequence[np.ndarray]) -> MagicMock:
            if len(images) == 2:
                return _fake_doctr_result_with_words(2, [[0.95, 0.9], [0.1, 0.15]])
            return _fake_doctr_result_with_words(1, [[0.9, 0.88]])

        doc, degrees = Document.from_images_ocr_via_doctr(
            [img_a, img_b],
            predictor=predictor,
            auto_rotate=True,
        )

        assert [page.page_index for page in doc.pages] == [0, 1]
        assert degrees == [0, 90]
        assert not hasattr(doc.pages[1], "rotation_applied")

    def test_unbeaten_upright_page_reports_zero(self) -> None:
        """Probes that lose to the upright pass still report 0."""
        img = _make_rgb_image(4, 8)
        calls = {"n": 0}

        def predictor(images: Sequence[np.ndarray]) -> MagicMock:
            calls["n"] += 1
            if calls["n"] == 1:
                return _fake_doctr_result_with_words(1, [[0.2]])
            return _fake_doctr_result_with_words(1, [[0.05]])

        _doc, degrees = Document.from_images_ocr_via_doctr(
            [img],
            predictor=predictor,
            auto_rotate=True,
        )

        assert calls["n"] > 1
        assert degrees == [0]

    def test_all_pages_low_confidence_all_recover(self) -> None:
        """Regression: a fully rotated batch must not produce empty output.

        This tests the canonical failure mode from the bug report:
        a 90deg-rotated page OCRs to empty output without auto-rotation.
        """
        # All pages start with near-zero confidence (simulating 90deg-rotated input).
        # After rotation probes, subsequent single-image re-OCR yields high confidence.
        img_a = _make_rgb_image(4, 8)  # non-square so rotation changes dims
        img_b = _make_rgb_image(4, 8)

        probe_count = {"n": 0}

        def predictor(images: Sequence[np.ndarray]) -> MagicMock:
            probe_count["n"] += 1
            n = len(images)
            if probe_count["n"] == 1:
                # Initial batch: all low confidence
                return _fake_doctr_result_with_words(n, [[0.05]] * n)
            # All subsequent single-image re-OCR probes:
            # return high confidence to simulate correct orientation found
            return _fake_doctr_result_with_words(1, [[0.95, 0.9]])

        doc, _degrees = Document.from_images_ocr_via_doctr(
            [img_a, img_b],
            source_identifiers=["rotated_a", "rotated_b"],
            predictor=predictor,
            auto_rotate=True,
        )

        assert len(doc.pages) == 2
        # Pages must have correct indices
        indices = [p.page_index for p in doc.pages]
        assert sorted(indices) == [0, 1]
        # Both pages must have OCR words (recovered from rotation)
        for page in doc.pages:
            assert len(page.words) > 0, (
                f"Page {page.page_index} must have words after rotation recovery"
            )
