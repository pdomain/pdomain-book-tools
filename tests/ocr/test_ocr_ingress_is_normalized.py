"""OCR engines state their coordinate system at ingress (plan item C1).

DocTR geometry is always normalized and Tesseract geometry is always pixels.
Neither adapter may leave the choice to ``BoundingBox`` range inference, which
labels a pixel box that fits inside the unit square as normalized.
"""

from __future__ import annotations

import pytest
from pandas import DataFrame

from pdomain_book_tools.ocr.document import Document


def _doctr_output(geometry: list[list[float]]) -> dict[str, object]:
    return {
        "pages": [
            {
                "page_idx": 0,
                "dimensions": [100, 100],
                "blocks": [
                    {
                        "geometry": geometry,
                        "lines": [
                            {
                                "geometry": geometry,
                                "words": [
                                    {
                                        "value": "word",
                                        "confidence": 0.9,
                                        "geometry": geometry,
                                    }
                                ],
                            }
                        ],
                        "artefacts": [],
                    }
                ],
            }
        ]
    }


def _tesseract_output(left: int, top: int, width: int, height: int) -> DataFrame:
    return DataFrame(
        {
            "level": [1, 2, 3, 4, 5],
            "page_num": [1, 1, 1, 1, 1],
            "block_num": [0, 1, 1, 1, 1],
            "par_num": [0, 0, 1, 1, 1],
            "line_num": [0, 0, 0, 1, 1],
            "left": [left] * 5,
            "top": [top] * 5,
            "width": [width] * 5,
            "height": [height] * 5,
            "text": ["", "", "", "", "word"],
            "conf": [0, 0, 0, 0, 90],
        }
    )


def test_tesseract_unit_square_pixel_box_stays_pixel() -> None:
    """A one-pixel box at the origin must not be inferred as normalized."""
    page = Document.from_tesseract(_tesseract_output(0, 0, 1, 1)).pages[0]

    word = page.words[0]

    assert word.bounding_box is not None
    assert word.bounding_box.is_normalized is False


def test_tesseract_page_box_is_pixel() -> None:
    page = Document.from_tesseract(_tesseract_output(0, 0, 1, 1)).pages[0]

    assert page.bounding_box is not None
    assert page.bounding_box.is_normalized is False


def test_doctr_box_is_normalized() -> None:
    doc = Document.from_doctr_output(_doctr_output([[0.1, 0.1], [0.5, 0.2]]))

    word = doc.pages[0].words[0]

    assert word.bounding_box is not None
    assert word.bounding_box.is_normalized is True


def test_doctr_out_of_range_geometry_raises() -> None:
    """Out-of-range DocTR output is an error, not a silent switch to pixels."""
    with pytest.raises(ValueError, match="normalized"):
        Document.from_doctr_output(_doctr_output([[0.1, 0.1], [1.5, 1.5]]))
