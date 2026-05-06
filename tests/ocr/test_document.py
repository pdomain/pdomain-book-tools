import json
from pathlib import Path

import pytest
from pandas import DataFrame

from pd_book_tools.ocr.document import Document
from pd_book_tools.ocr.page import Page
from pd_book_tools.ocr.provenance import OCRModelProvenance, OCRProvenance


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
    doc._pages.append(page)
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


def test_document_source_path_none_round_trips_as_none():
    """Regression test for M-07.

    `Document.to_dict` previously did `str(self.source_path)`, which yields
    the literal string ``"None"`` when ``source_path`` is ``None``. The
    matching ``from_dict`` then saw a truthy non-empty string and produced
    ``Path("None")`` (a path literally named ``None`` in the cwd), breaking
    the round-trip. Serialize ``None`` as JSON ``null`` instead.
    """
    doc = Document(source_lib="test_lib", source_path=None, pages=[])
    doc_dict = doc.to_dict()
    # Must not be the literal string "None" — that's the bug.
    assert doc_dict["source_path"] != "None"
    assert doc_dict["source_path"] is None

    restored = Document.from_dict(doc_dict)
    assert restored.source_path is None
    # And specifically not a path literally named "None".
    assert restored.source_path != Path("None")


def test_document_from_dict_tolerates_legacy_none_string():
    """Backward-compat: legacy JSON files written before M-07 contain the
    literal string ``"None"`` for missing source paths. ``from_dict`` should
    treat that as ``None`` rather than ``Path("None")``."""
    doc_dict = {
        "source_lib": "test_lib",
        "source_path": "None",
        "pages": [],
    }
    doc = Document.from_dict(doc_dict)
    assert doc.source_path is None


def test_document_to_json_file(tmp_path):
    doc = Document(source_lib="test_lib", source_path=Path("test_path"), pages=[])
    page = Page(page_index=0, width=800, height=1000, items=[])
    doc._pages.append(page)
    file_path = tmp_path / "test.json"
    doc.to_json_file(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["source_lib"] == "test_lib"
    assert data["source_path"] == "test_path"
    assert len(data["pages"]) == 1


def test_document_from_doctr_output(sample_doctr_output):
    doc = Document.from_doctr_output(sample_doctr_output, source_path="test_path")
    assert doc.source_lib == "doctr"
    assert doc.source_path == Path("test_path")
    assert len(doc.pages) == 1
    assert doc.pages[0].width == 800
    assert doc.pages[0].height == 1000
    assert doc.pages[0].ocr_provenance is not None
    assert doc.pages[0].ocr_provenance == OCRProvenance(
        engine="doctr",
        models=[],
        engine_version="unknown",
    )


def test_document_from_doctr_output_normalizes_model_provenance():
    doctr_output = {
        "metadata": {
            "source_lib": "doctr-custom",
            "engine_version": "0.12.1",
            "models": [
                "db_resnet50",
                {"name": "crnn_vgg16", "version": "2", "weights_id": 123},
            ],
        },
        "pages": [
            {
                "dimensions": [100, 100],
                "blocks": [],
            }
        ],
    }

    doc = Document.from_doctr_output(doctr_output)

    assert doc.pages[0].ocr_provenance == OCRProvenance(
        engine="doctr",
        engine_version="0.12.1",
        models=[
            OCRModelProvenance(name="db_resnet50"),
            OCRModelProvenance(name="crnn_vgg16", version="2", weights_id="123"),
        ],
        config_fingerprint="doctr-custom|crnn_vgg16|db_resnet50",
    )


def test_document_from_tesseract(sample_tesseract_output):
    doc = Document.from_tesseract(sample_tesseract_output, source_path="test_path")
    assert doc.source_lib == "tesseract"
    assert doc.source_path == Path("test_path")
    assert len(doc.pages) == 1
    print(doc.to_dict())
    assert doc.pages[0].width == 100
    assert doc.pages[0].height == 200
    assert doc.pages[0].ocr_provenance is not None
    assert doc.pages[0].ocr_provenance.engine == "tesseract"
    assert doc.pages[0].ocr_provenance.models == []
    assert isinstance(doc.pages[0].ocr_provenance.engine_version, str)


def test_document_from_tesseract_treats_conf_minus_one_as_none():
    """Regression test for H-10.

    Tesseract returns ``conf == -1`` for rejected/empty words. That sentinel
    must not be stored as a real confidence (``-1.0``); it has to surface as
    ``None`` so downstream code (rotation detection's mean-confidence guard,
    ``Block.mean_ocr_confidence``, confidence-based filtering) skips it
    instead of treating it as a near-zero confidence and dragging the mean
    below thresholds like ``0.6``.
    """
    df = DataFrame(
        {
            "level": [1, 2, 3, 4, 5, 5],
            "page_num": [1, 1, 1, 1, 1, 1],
            "block_num": [0, 1, 1, 1, 1, 1],
            "par_num": [0, 0, 1, 1, 1, 1],
            "line_num": [0, 0, 0, 1, 1, 1],
            "left": [0, 10, 20, 30, 40, 110],
            "top": [0, 10, 20, 30, 40, 40],
            "width": [200, 190, 180, 170, 60, 60],
            "height": [200, 190, 180, 170, 160, 160],
            "text": ["", "", "", "", "Hello", ""],
            # Last word is a rejected/empty Tesseract entry: conf == -1.
            "conf": [0, 0, 0, 0, 95, -1],
        }
    )
    doc = Document.from_tesseract(df)

    words = list(doc.pages[0].words)
    assert len(words) == 2
    confidences = [w.ocr_confidence for w in words]
    assert 95.0 in confidences
    # The -1 sentinel must NOT be stored as -1.0; it must be None.
    assert None in confidences, (
        f"Tesseract conf == -1 sentinel should map to None, got {confidences}"
    )
    assert -1.0 not in confidences

    # And the rotation-detection style mean-confidence aggregation must
    # exclude the sentinel rather than averaging it in.
    from pd_book_tools.ocr.rotation import _mean_confidence

    mean_conf, count = _mean_confidence(doc)
    assert count == 1
    assert mean_conf == 95.0


def test_document_from_tesseract_skips_nan_text_rows():
    """Regression test for H-11.

    Tesseract emits rejected/empty rows where the ``text`` cell is a pandas
    ``NaN``. Calling ``str(NaN)`` yields the literal string ``'nan'``, so the
    naive ``Word(text=str(word_row.text), ...)`` ingest creates a ghost Word
    with text ``'nan'`` that propagates as real OCR output into ground-truth
    matching and final text. The fix must keep the row's geometry around (we
    do not silently drop OCR rows) while ensuring its text is empty rather
    than the string ``'nan'``.
    """
    import math

    df = DataFrame(
        {
            "level": [1, 2, 3, 4, 5, 5],
            "page_num": [1, 1, 1, 1, 1, 1],
            "block_num": [0, 1, 1, 1, 1, 1],
            "par_num": [0, 0, 1, 1, 1, 1],
            "line_num": [0, 0, 0, 1, 1, 1],
            "left": [0, 10, 20, 30, 40, 110],
            "top": [0, 10, 20, 30, 40, 40],
            "width": [200, 190, 180, 170, 60, 60],
            "height": [200, 190, 180, 170, 160, 160],
            # Second word row's text is a real NaN — Tesseract's
            # rejected/empty-text sentinel for that column.
            "text": ["", "", "", "", "Hello", math.nan],
            "conf": [0, 0, 0, 0, 95, -1],
        }
    )
    doc = Document.from_tesseract(df)

    word_texts = [w.text for w in doc.pages[0].words]
    # The literal string 'nan' must NEVER leak through as OCR output.
    assert "nan" not in word_texts, (
        f"NaN text cell produced ghost 'nan' word: {word_texts}"
    )
    # The Hello word is preserved as-is.
    assert "Hello" in word_texts


def test_document_from_tesseract_handles_noncontiguous_block_numbers():
    """Regression test for H-18.

    Tesseract's hierarchy fields (``block_num``, ``par_num``, ``line_num``)
    are *not* guaranteed to be a contiguous 1..N sequence. Tesseract may
    skip numbers when intermediate regions are empty, dropped as noise, or
    filtered out earlier in the pipeline. The reconstruction in
    ``Document.from_tesseract`` must use the actual ``block_num`` /
    ``par_num`` / ``line_num`` values from the DataFrame rows, not the
    positional ``enumerate`` index, otherwise child rows are filtered
    against the wrong parent and entire branches of the hierarchy vanish.

    This test exercises the worst case: blocks ``1`` and ``3`` (no block
    ``2``), with the second block's paragraph numbered ``5`` (not ``1``)
    and that paragraph's line numbered ``2`` (not ``1``). The pre-fix
    positional code finds block ``1``'s "Hello" but loses block ``3``'s
    "World" entirely because the inner filters look for ``block_num == 2``,
    ``par_num == 1``, ``line_num == 1`` — none of which exist.
    """
    df = DataFrame(
        {
            # Page row, two block rows (1 and 3 — no 2!), paragraph rows
            # within each block (par 1 in block 1, par 5 in block 3),
            # line rows (line 1 in block 1/par 1; line 2 in block 3/par 5),
            # word rows ("Hello" in block 1; "World" in block 3).
            "level": [1, 2, 2, 3, 3, 4, 4, 5, 5],
            "page_num": [1, 1, 1, 1, 1, 1, 1, 1, 1],
            "block_num": [0, 1, 3, 1, 3, 1, 3, 1, 3],
            "par_num": [0, 0, 0, 1, 5, 1, 5, 1, 5],
            "line_num": [0, 0, 0, 0, 0, 1, 2, 1, 2],
            "left": [0, 10, 200, 20, 210, 30, 220, 40, 230],
            "top": [0, 10, 10, 20, 20, 30, 30, 40, 40],
            "width": [400, 90, 90, 80, 80, 70, 70, 60, 60],
            "height": [200, 190, 190, 180, 180, 170, 170, 160, 160],
            "text": ["", "", "", "", "", "", "", "Hello", "World"],
            "conf": [0, 0, 0, 0, 0, 0, 0, 95, 90],
        }
    )

    doc = Document.from_tesseract(df)

    # Both words must be ingested — neither branch of the hierarchy may
    # be silently dropped because of non-contiguous numbering.
    word_texts = sorted(w.text for w in doc.pages[0].words)
    assert word_texts == ["Hello", "World"], (
        f"Non-contiguous block_num/par_num/line_num caused word loss: got {word_texts}"
    )

    # And the hierarchy must be correctly partitioned: two blocks, each
    # with exactly one word.
    page = doc.pages[0]
    assert len(page.items) == 2, (
        f"Expected 2 blocks (block_num 1 and 3), got {len(page.items)}"
    )
    block_word_counts = [len(list(b.words)) for b in page.items]
    assert block_word_counts == [1, 1], (
        f"Words mis-grouped across blocks: per-block counts {block_word_counts}"
    )
