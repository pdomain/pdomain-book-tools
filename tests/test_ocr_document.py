import json
import pytest
from pathlib import Path
from pandas import DataFrame
from pd_book_tools.ocr._document import Document
from pd_book_tools.ocr._page import Page


@pytest.fixture
def sample_doctr_output():
    return {
        "pages": [
            {
                "dimensions": [1000, 800],
                "blocks": [
                    {
                        "geometry": [[0.1, 0.1], [0.5, 0.5]],
                        "lines": [
                            {
                                "geometry": [[0.1, 0.1], [0.5, 0.2]],
                                "words": [
                                    {
                                        "value": "Hello",
                                        "geometry": [[0.1, 0.1], [0.2, 0.2]],
                                        "confidence": 0.95,
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
    }


@pytest.fixture
def sample_tesseract_output():
    df = DataFrame(
        {
            "level": [1, 2, 3, 4, 5],
            "page_num": [1, 1, 1, 1, 1],
            "block_num": [0, 1, 1, 1, 1],
            "par_num": [0, 0, 1, 1, 1],
            "line_num": [0, 0, 0, 1, 1],
            "left": [0, 10, 20, 30, 40],
            "top": [0, 10, 20, 30, 40],
            "width": [100, 90, 80, 70, 60],
            "height": [200, 190, 180, 170, 160],
            "text": ["", "", "", "", "Hello"],
            "conf": [0, 0, 0, 0, 95],
        }
    )
    print(df)
    return df


def test_document_to_dict():
    doc = Document(source_lib="test_lib", source_path=Path("test_path"), pages=[])
    page = Page(page_index=0, width=800, height=1000, items=[])
    doc.pages.add(page)
    doc_dict = doc.to_dict()
    assert doc_dict["source_lib"] == "test_lib"
    assert doc_dict["source_path"] == "test_path"
    assert len(doc_dict["pages"]) == 1


def test_document_from_dict():
    doc_dict = {
        "source_lib": "test_lib",
        "source_path": "test_path",
        "pages": [{"page_index": 0, "width": 800, "height": 1000, "items": []}],
    }
    doc = Document.from_dict(doc_dict)
    assert doc.source_lib == "test_lib"
    assert doc.source_path == Path("test_path")
    assert len(doc.pages) == 1


def test_document_save_json(tmp_path):
    doc = Document(source_lib="test_lib", source_path=Path("test_path"), pages=[])
    page = Page(page_index=0, width=800, height=1000, items=[])
    doc.pages.add(page)
    file_path = tmp_path / "test.json"
    doc.save_json(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["source_lib"] == "test_lib"
    assert data["source_path"] == "test_path"
    assert len(data["pages"]) == 1


def test_document_from_doctr_output(sample_doctr_output):
    doc = Document.from_doctr_output(sample_doctr_output, "test_path")
    assert doc.source_lib == "doctr"
    assert doc.source_path == Path("test_path")
    assert len(doc.pages) == 1
    assert doc.pages[0].width == 800
    assert doc.pages[0].height == 1000


def test_document_from_tesseract(sample_tesseract_output):
    doc = Document.from_tesseract(sample_tesseract_output, "test_path")
    assert doc.source_lib == "tesseract"
    assert doc.source_path == Path("test_path")
    assert len(doc.pages) == 1
    print(doc.to_dict())
    assert doc.pages[0].width == 100
    assert doc.pages[0].height == 200
