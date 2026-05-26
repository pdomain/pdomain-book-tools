import json
from pathlib import Path

import pytest
from pandas import DataFrame

from pdomain_book_tools.ocr.document import Document
from pdomain_book_tools.ocr.page import Page
from pdomain_book_tools.ocr.provenance import OCRModelProvenance, OCRProvenance


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
    print(df)  # debug helper — visible when fixture is regenerated
    return df


def test_document_to_dict():
    doc = Document(source_lib="test_lib", source_path=Path("test_path"), pages=[])
    page = Page(page_index=0, width=800, height=1000, blocks=[])
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
    page = Page(page_index=0, width=800, height=1000, blocks=[])
    doc._pages.append(page)
    file_path = tmp_path / "test.json"
    doc.to_json_file(file_path)
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
    assert data["source_lib"] == "test_lib"
    assert data["source_path"] == "test_path"
    assert len(data["pages"]) == 1


def test_document_from_doctr_word_missing_confidence_is_none():
    """L-19: a DocTR word with no ``confidence`` key must surface as
    ``ocr_confidence=None`` (\"unknown\"), not ``0.0`` (\"near certainty
    of error\"). Pre-fix the adapter did
    ``word_data.get(\"confidence\", 0.0)``, conflating the two semantics
    so confidence-based filters and quality reports were silently
    polluted with phantom 0.0-score words.
    """
    doctr_output = {
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
                                        # No "confidence" key — must read None.
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
    }
    doc = Document.from_doctr_output(doctr_output)
    word = doc.pages[0].items[0].items[0].items[0].items[0]
    assert word.text == "Hello"
    assert word.ocr_confidence is None


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


def test_document_from_doctr_output_matches_tesseract_nesting_depth(
    sample_doctr_output, sample_tesseract_output
):
    """Regression test for M-14.

    The DocTR adapter previously produced ``Page -> Block(PARAGRAPH) ->
    Block(LINE) -> Word`` (3 levels) while the Tesseract adapter produced
    ``Page -> Block(BLOCK) -> Block(PARAGRAPH) -> Block(LINE) -> Word``
    (4 levels). Consumers iterating ``page.items[0]`` and expecting a
    ``BLOCK``-category item silently failed on DocTR output.

    Both adapters must produce the same canonical depth and category
    sequence so consumers can iterate uniformly.
    """
    from pdomain_book_tools.ocr.block import BlockCategory

    doctr_doc = Document.from_doctr_output(sample_doctr_output)
    tess_doc = Document.from_tesseract(sample_tesseract_output)

    def category_path(page):
        # Walk leftmost child until a non-Block (Word) is reached, collecting
        # block categories. Returns a tuple like
        # (BLOCK, PARAGRAPH, LINE).
        path = []
        node = page.items[0]
        while hasattr(node, "block_category") and node.block_category is not None:
            path.append(node.block_category)
            if not node.items:
                break
            node = node.items[0]
        return tuple(path)

    doctr_path = category_path(doctr_doc.pages[0])
    tess_path = category_path(tess_doc.pages[0])

    expected = (BlockCategory.BLOCK, BlockCategory.PARAGRAPH, BlockCategory.LINE)
    assert tess_path == expected, (
        f"Tesseract baseline changed unexpectedly: {tess_path}"
    )
    assert doctr_path == expected, (
        f"DocTR adapter must match Tesseract depth/categories. "
        f"Got {doctr_path}, expected {expected}."
    )

    # And the leaf words must still be reachable; the wrap should not lose
    # any OCR words (memory rule: never silently drop OCR words).
    doctr_words = list(doctr_doc.pages[0].words)
    assert [w.text for w in doctr_words] == ["Hello"]


def test_document_from_doctr_output_preserves_artefacts_as_role_tagged_blocks():
    """Regression test for M-15.

    DocTR's block export carries both ``"lines"`` (text) and ``"artefacts"``
    (non-text regions: stamps, barcodes, QR codes, figures). The adapter
    previously iterated only ``"lines"``, silently discarding artefacts.

    pdomain-book-tools' invariant is that OCR-derived content is never silently
    dropped — even non-text regions must be preserved with a role label so
    consumers can choose to keep, render, or strip them.

    Strategy: each artefact becomes a top-level ``Block`` on the page,
    ``block_category=BLOCK``, ``child_type=WORDS``, ``items=[]``,
    ``block_role_labels=["artefact"]``. DocTR's per-artefact ``type`` and
    ``confidence`` are preserved in ``additional_block_attributes`` so the
    artefact's classification (e.g. ``"barcode"``) is not lost.
    """
    from pdomain_book_tools.ocr.block import BlockCategory, BlockChildType

    doctr_output = {
        "metadata": {},
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
                        "artefacts": [
                            {
                                "geometry": [[0.6, 0.6], [0.9, 0.9]],
                                "type": "barcode",
                                "confidence": 0.88,
                            },
                            {
                                "geometry": [[0.05, 0.7], [0.15, 0.8]],
                                "type": "qr_code",
                                "confidence": 0.42,
                            },
                        ],
                    }
                ],
            }
        ],
    }

    doc = Document.from_doctr_output(doctr_output)
    page = doc.pages[0]

    # The text Word must still flow through unchanged.
    assert [w.text for w in page.words] == ["Hello"]

    # Both artefacts must be preserved as top-level Blocks on the page,
    # tagged with the "artefact" role label so consumers can filter them.
    artefact_blocks = [
        item for item in page.items if "artefact" in item.block_role_labels
    ]
    assert len(artefact_blocks) == 2, (
        f"Expected 2 artefact blocks; got {len(artefact_blocks)}. "
        f"Pre-fix bug: artefacts were silently dropped."
    )

    # Match the canonical Block shape so they don't break consumers walking
    # page.items: BLOCK category, WORDS child type, empty items list.
    for art in artefact_blocks:
        assert art.block_category == BlockCategory.BLOCK
        assert art.child_type == BlockChildType.WORDS
        assert list(art.items) == []
        assert art.bounding_box is not None

    # DocTR's classification (type) and confidence must be preserved so the
    # artefact's identity is not lost.
    types = sorted(
        a.additional_block_attributes.get("artefact_type") for a in artefact_blocks
    )
    assert types == ["barcode", "qr_code"]
    confidences = sorted(
        a.additional_block_attributes.get("artefact_confidence")
        for a in artefact_blocks
    )
    assert confidences == [0.42, 0.88]

    # Artefact blocks contribute zero words to ``page.words`` — they are
    # geometry-only placeholders, not OCR text.
    assert len(page.words) == 1


def test_document_from_doctr_output_tolerates_missing_word_geometry():
    """Regression test for M-16.

    The DocTR adapter previously accessed ``word_data["geometry"]`` with
    a hard key, raising ``KeyError`` on partial data, while block and
    line geometry already used guarded ``.get("geometry")``. A word with
    no geometry should not be silently dropped (project invariant: never
    drop OCR-derived content) — it must be emitted as a ``Word`` with
    ``bounding_box=None``, consistent with the existing None-bbox
    handling at the block / line / artefact levels.
    """
    doctr_output = {
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
                                    },
                                    {
                                        # No "geometry" key — partial DocTR
                                        # output. Pre-fix: KeyError on the
                                        # whole document construction.
                                        "value": "world",
                                        "confidence": 0.40,
                                    },
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
    }

    # Pre-fix this raised KeyError at word_data["geometry"].
    doc = Document.from_doctr_output(doctr_output)
    page = doc.pages[0]

    # Both words must survive — no silent drop. Order is not asserted
    # because None-bbox sorting is implementation-defined; the
    # invariant tested here is the no-drop guarantee.
    words = list(page.words)
    by_text = {w.text: w for w in words}
    assert set(by_text) == {"Hello", "world"}

    # The geometry-bearing word keeps its bbox; the partial word has
    # bounding_box=None (consistent with how block/line/artefact handle
    # missing geometry).
    assert by_text["Hello"].bounding_box is not None
    assert by_text["world"].bounding_box is None

    # Confidence still flows through for the partial word.
    assert by_text["world"].ocr_confidence == 0.40


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
    print(doc.to_dict())  # debug helper for test inspection
    assert doc.pages[0].width == 100
    assert doc.pages[0].height == 200
    assert doc.pages[0].ocr_provenance is not None
    assert doc.pages[0].ocr_provenance.engine == "tesseract"
    # L-15: tuple, not list. L-18: default ``lang="eng"`` is now recorded
    # in the provenance so two language packs produce distinguishable
    # records.
    assert isinstance(doc.pages[0].ocr_provenance.models, tuple)
    assert [m.name for m in doc.pages[0].ocr_provenance.models] == ["eng"]
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
    from pdomain_book_tools.ocr.rotation import _mean_confidence

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


# ---------------------------------------------------------------------------
# R-16: per-level DocTR helper functions
#
# ``from_doctr_output`` now delegates to small per-level helpers so that
# adapters can be reused (e.g. by tests, downstream tools, or future formats)
# and reasoned about in isolation. These tests pin the helper contracts
# directly — the high-level integration is covered by the ``sample_doctr_output``
# tests above.
# ---------------------------------------------------------------------------


def test_word_from_doctr_preserves_confidence_and_geometry():
    word = Document._word_from_doctr(
        {
            "value": "Hello",
            "geometry": [[0.1, 0.2], [0.3, 0.4]],
            "confidence": 0.87,
        }
    )
    assert word.text == "Hello"
    assert word.ocr_confidence == 0.87
    assert word.bounding_box is not None


def test_word_from_doctr_missing_geometry_yields_none_bbox():
    # M-16: missing geometry must NOT raise; the word survives with bbox=None
    word = Document._word_from_doctr({"value": "x", "confidence": 0.5})
    assert word.text == "x"
    assert word.bounding_box is None


def test_word_from_doctr_missing_confidence_is_none_not_zero():
    # L-19: missing confidence is "unknown", not "0% confident"
    word = Document._word_from_doctr({"value": "x"})
    assert word.ocr_confidence is None


def test_line_from_doctr_builds_line_block_with_words():
    line = Document._line_from_doctr(
        {
            "geometry": [[0.1, 0.1], [0.5, 0.2]],
            "words": [
                {"value": "a", "geometry": [[0.1, 0.1], [0.2, 0.2]], "confidence": 0.9},
                {"value": "b", "geometry": [[0.3, 0.1], [0.4, 0.2]], "confidence": 0.8},
            ],
        }
    )
    assert [w.text for w in line.items] == ["a", "b"]
    assert line.bounding_box is not None


def test_block_from_doctr_wraps_in_block_paragraph_line_and_yields_artefact_siblings():
    blocks = Document._block_from_doctr(
        {
            "geometry": [[0.1, 0.1], [0.5, 0.5]],
            "lines": [
                {
                    "geometry": [[0.1, 0.1], [0.5, 0.2]],
                    "words": [{"value": "hi", "geometry": [[0.1, 0.1], [0.2, 0.2]]}],
                }
            ],
            "artefacts": [
                {
                    "geometry": [[0.6, 0.6], [0.7, 0.7]],
                    "type": "barcode",
                    "confidence": 0.4,
                }
            ],
        }
    )
    # Canonical block + 1 artefact sibling.
    assert len(blocks) == 2
    canonical, artefact = blocks

    # Canonical: BLOCK -> PARAGRAPH -> LINE -> Word
    assert canonical.block_category.name == "BLOCK"
    paragraph = canonical.items[0]
    assert paragraph.block_category.name == "PARAGRAPH"
    line = paragraph.items[0]
    assert line.block_category.name == "LINE"
    assert [w.text for w in line.items] == ["hi"]

    # Artefact: empty items, role-labelled, attrs preserved
    assert artefact.items == []
    assert artefact.block_role_labels == ["artefact"]
    assert artefact.additional_block_attributes is not None
    assert artefact.additional_block_attributes["artefact_type"] == "barcode"
    assert artefact.additional_block_attributes["artefact_confidence"] == 0.4


def test_artefact_from_doctr_with_no_metadata_has_empty_attrs():
    # ``Block`` normalizes ``additional_block_attributes`` to ``{}`` even
    # when ``None`` is passed in, so what we pin here is that no spurious
    # type/confidence keys leak in when DocTR didn't supply any.
    block = Document._artefact_from_doctr({"geometry": [[0.0, 0.0], [0.1, 0.1]]})
    assert block.block_role_labels == ["artefact"]
    assert not block.additional_block_attributes


def test_page_from_doctr_uses_dimensions_and_threads_original_text():
    provenance = OCRProvenance(engine="doctr", models=[], engine_version="x")
    page = Document._page_from_doctr(
        page_data={
            "dimensions": [1000, 800],
            "blocks": [
                {
                    "geometry": [[0.1, 0.1], [0.5, 0.5]],
                    "lines": [
                        {
                            "geometry": [[0.1, 0.1], [0.5, 0.2]],
                            "words": [
                                {
                                    "value": "Hi",
                                    "geometry": [[0.1, 0.1], [0.2, 0.2]],
                                }
                            ],
                        }
                    ],
                }
            ],
        },
        page_idx=0,
        ocr_provenance=provenance,
        original_text=["original"],
    )
    assert page.height == 1000
    assert page.width == 800
    assert page.original_ocr_tool_text == "original"
    assert [w.text for w in page.words] == ["Hi"]


# ---------------------------------------------------------------------------
# R-16: per-level Tesseract helper functions
#
# Tesseract's adapter is DataFrame-driven, so each level's helper takes the
# full DataFrame plus the parent row's ``block_num`` / ``par_num`` /
# ``line_num`` to filter children — H-18: Tesseract numbers are NOT
# guaranteed contiguous, so the helpers must use the row's actual ids.
# ---------------------------------------------------------------------------


def _tesseract_minimal_df():
    return DataFrame(
        [
            # Page (level 1)
            {
                "level": 1,
                "page_num": 1,
                "block_num": 0,
                "par_num": 0,
                "line_num": 0,
                "word_num": 0,
                "left": 0,
                "top": 0,
                "width": 800,
                "height": 1000,
                "conf": -1,
                "text": "",
            },
            # Block (level 2)
            {
                "level": 2,
                "page_num": 1,
                "block_num": 1,
                "par_num": 0,
                "line_num": 0,
                "word_num": 0,
                "left": 10,
                "top": 10,
                "width": 300,
                "height": 50,
                "conf": -1,
                "text": "",
            },
            # Paragraph (level 3)
            {
                "level": 3,
                "page_num": 1,
                "block_num": 1,
                "par_num": 1,
                "line_num": 0,
                "word_num": 0,
                "left": 10,
                "top": 10,
                "width": 300,
                "height": 50,
                "conf": -1,
                "text": "",
            },
            # Line (level 4)
            {
                "level": 4,
                "page_num": 1,
                "block_num": 1,
                "par_num": 1,
                "line_num": 1,
                "word_num": 0,
                "left": 10,
                "top": 10,
                "width": 300,
                "height": 25,
                "conf": -1,
                "text": "",
            },
            # Word (level 5)
            {
                "level": 5,
                "page_num": 1,
                "block_num": 1,
                "par_num": 1,
                "line_num": 1,
                "word_num": 1,
                "left": 10,
                "top": 10,
                "width": 80,
                "height": 20,
                "conf": 88,
                "text": "Hello",
            },
        ]
    )


def test_tesseract_filter_level_applies_equality_filters():
    df = _tesseract_minimal_df()
    rows = Document._tesseract_filter_level(df, level=5.0, page_num=1, block_num=1)
    assert len(rows) == 1
    word = rows.iloc[0]
    assert word["text"] == "Hello"


def test_word_from_tesseract_drops_negative_conf_sentinel():
    df = _tesseract_minimal_df()
    word_row = next(Document._tesseract_filter_level(df, level=5.0).itertuples())
    word = Document._word_from_tesseract(word_row)
    assert word.text == "Hello"
    # conf=88 > 0, so this is preserved (the sentinel-drop test is in
    # ``_tesseract_confidence`` coverage; here we just pin that real
    # confidences pass through and that the bbox/text plumbing works.)
    assert word.ocr_confidence == 88.0


def test_tesseract_confidence_treats_nan_as_none():
    """A NaN ``conf`` cell must be excluded from aggregation, not averaged in.

    Tesseract can emit a ``NaN`` confidence for rejected/empty rows. ``NaN``
    is the sentinel for "no confidence available"; it must map to ``None`` so
    it is left out of mean-confidence math rather than corrupting it.
    """
    import math

    assert Document._tesseract_confidence(math.nan) is None
    assert Document._tesseract_confidence(float("nan")) is None
    # Real confidences still pass through unchanged.
    assert Document._tesseract_confidence(95) == 95.0
    # Non-positive sentinel and non-numeric values stay None.
    assert Document._tesseract_confidence(-1) is None
    assert Document._tesseract_confidence("garbage") is None


def test_tesseract_text_treats_nan_as_empty_string():
    """A NaN ``text`` cell must render as ``""``, never the string ``'nan'``."""
    import math

    assert Document._tesseract_text(math.nan) == ""
    assert Document._tesseract_text(float("nan")) == ""
    assert Document._tesseract_text("Hello") == "Hello"
    assert Document._tesseract_text(None) == ""


def test_block_from_tesseract_handles_non_contiguous_ids():
    """H-18 regression: filtering must use the row's actual ids."""
    df = DataFrame(
        [
            {
                "level": 1,
                "page_num": 1,
                "block_num": 0,
                "par_num": 0,
                "line_num": 0,
                "word_num": 0,
                "left": 0,
                "top": 0,
                "width": 100,
                "height": 100,
                "conf": -1,
                "text": "",
            },
            # block 1, then block 5 (skipping 2-4)
            {
                "level": 2,
                "page_num": 1,
                "block_num": 5,
                "par_num": 0,
                "line_num": 0,
                "word_num": 0,
                "left": 0,
                "top": 0,
                "width": 100,
                "height": 50,
                "conf": -1,
                "text": "",
            },
            {
                "level": 3,
                "page_num": 1,
                "block_num": 5,
                "par_num": 7,
                "line_num": 0,
                "word_num": 0,
                "left": 0,
                "top": 0,
                "width": 100,
                "height": 50,
                "conf": -1,
                "text": "",
            },
            {
                "level": 4,
                "page_num": 1,
                "block_num": 5,
                "par_num": 7,
                "line_num": 3,
                "word_num": 0,
                "left": 0,
                "top": 0,
                "width": 100,
                "height": 25,
                "conf": -1,
                "text": "",
            },
            {
                "level": 5,
                "page_num": 1,
                "block_num": 5,
                "par_num": 7,
                "line_num": 3,
                "word_num": 1,
                "left": 0,
                "top": 0,
                "width": 50,
                "height": 20,
                "conf": 90,
                "text": "non-contig",
            },
        ]
    )
    block_row = next(Document._tesseract_filter_level(df, level=2.0).itertuples())
    block = Document._block_from_tesseract(block_row, df=df, page_num=1)
    word_texts = [w.text for w in block.words]
    assert word_texts == ["non-contig"]
