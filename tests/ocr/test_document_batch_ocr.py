"""Tests for Document.from_images_ocr_via_doctr (batch OCR entry point)."""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pytest

from pdomain_book_tools.ocr.document import Document


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

    export_pages = [{"dimensions": (8, 8), "blocks": []} for _ in range(n_pages)]
    result.export = MagicMock(return_value={"pages": export_pages})
    return result


class TestFromImagesOcrViaDoctr:
    def test_predictor_called_once_with_list(self):
        img_a = _make_rgb_image()
        img_b = _make_rgb_image()

        fake_result = _fake_doctr_result(2)
        call_args: list[object] = []

        def stub_predictor(images):
            call_args.append(images)
            assert len(images) == 2, "predictor must receive both images in one call"
            return fake_result

        doc = Document.from_images_ocr_via_doctr(
            [img_a, img_b],
            source_identifiers=["a", "b"],
            predictor=stub_predictor,
        )

        assert len(call_args) == 1, "predictor must be called exactly once"
        assert doc is not None

    def test_returns_document_with_correct_page_count(self):
        img_a = _make_rgb_image()
        img_b = _make_rgb_image()

        fake_result = _fake_doctr_result(2)

        def stub_predictor(images):
            return fake_result

        doc = Document.from_images_ocr_via_doctr(
            [img_a, img_b],
            source_identifiers=["a", "b"],
            predictor=stub_predictor,
        )

        assert len(doc.pages) == 2

    def test_source_identifiers_preserved_in_order(self):
        img_a = _make_rgb_image()
        img_b = _make_rgb_image()

        fake_result = _fake_doctr_result(2)

        def stub_predictor(images):
            return fake_result

        doc = Document.from_images_ocr_via_doctr(
            [img_a, img_b],
            source_identifiers=["alpha", "beta"],
            predictor=stub_predictor,
        )

        pages = doc.pages
        assert pages[0].page_index == 0
        assert pages[1].page_index == 1

    def test_single_image_list_works(self):
        img = _make_rgb_image()
        fake_result = _fake_doctr_result(1)

        def stub_predictor(images):
            assert len(images) == 1
            return fake_result

        doc = Document.from_images_ocr_via_doctr(
            [img],
            source_identifiers=["only"],
            predictor=stub_predictor,
        )

        assert len(doc.pages) == 1

    def test_empty_list_raises(self):
        with pytest.raises((ValueError, IndexError)):
            Document.from_images_ocr_via_doctr(
                [],
                source_identifiers=[],
                predictor=MagicMock(),
            )

    def test_mismatched_identifiers_raises(self):
        img = _make_rgb_image()
        with pytest.raises((ValueError, TypeError)):
            Document.from_images_ocr_via_doctr(
                [img],
                source_identifiers=["a", "extra"],
                predictor=MagicMock(),
            )
