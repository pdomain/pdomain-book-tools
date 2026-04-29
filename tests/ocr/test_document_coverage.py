"""Coverage-focused tests for Document (init paths, scaling, image OCR, etc.)."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from pd_book_tools.ocr.document import Document
from pd_book_tools.ocr.page import Page
from pd_book_tools.ocr.provenance import OCRModelProvenance


@pytest.fixture
def empty_doc():
    return Document(source_lib="lib", source_path=Path("img.png"), pages=[])


@pytest.fixture
def doc_with_pages():
    doc = Document(source_lib="lib", source_path=Path("img.png"), pages=[])
    for idx in (2, 0, 1):
        doc._pages.append(Page(page_index=idx, width=10, height=10, items=[]))
    return doc


class TestInit:
    def test_string_source_path_is_converted(self):
        doc = Document(source_lib="lib", source_path="some/path.png", pages=[])
        assert isinstance(doc.source_path, Path)
        assert doc.source_path == Path("some/path.png")

    def test_none_source_path(self):
        doc = Document(source_lib="lib", source_path=None, pages=[])
        assert doc.source_path is None

    def test_pages_setter_rejects_non_collection(self):
        with pytest.raises(TypeError, match="must be a collection"):
            Document(source_lib="lib", source_path=None, pages=42)

    def test_pages_setter_rejects_invalid_page(self):
        # An object missing page_index should raise
        class NotAPage:
            pass

        with pytest.raises(TypeError, match="page_index"):
            Document(source_lib="lib", source_path=None, pages=[NotAPage()])


class TestPagesProperty:
    def test_pages_sorted(self, doc_with_pages):
        assert [p.page_index for p in doc_with_pages.pages] == [0, 1, 2]

    def test_pages_returns_copy(self, doc_with_pages):
        copy = doc_with_pages.pages
        copy.clear()
        assert len(doc_with_pages.pages) == 3


class TestScale:
    def test_scale_calls_each_page(self):
        doc = Document(source_lib="lib", source_path=Path("p.png"), pages=[])
        page = MagicMock()
        page.page_index = 0
        scaled_page = MagicMock()
        scaled_page.page_index = 0
        page.scale.return_value = scaled_page
        doc._pages.append(page)

        new = doc.scale(100, 200)
        assert isinstance(new, Document)
        page.scale.assert_called_once_with(100, 200)
        assert new.source_lib == "lib"


class TestToFromJsonFile:
    def test_round_trip(self, tmp_path):
        doc = Document(source_lib="my_lib", source_path=Path("p.png"), pages=[])
        doc._pages.append(Page(page_index=0, width=10, height=20, items=[]))

        out_path = tmp_path / "out.json"
        doc.to_json_file(out_path)
        loaded = Document.from_json_file(out_path)

        assert loaded.source_lib == "my_lib"
        assert loaded.source_path == Path("p.png")
        assert len(loaded.pages) == 1


class TestSafeFloat:
    def test_none_returns_zero(self):
        assert Document.safe_float(None) == 0.0

    def test_with_item_method(self):
        # numpy scalars expose .item()
        scalar = np.float32(3.14)
        assert abs(Document.safe_float(scalar) - 3.14) < 1e-3

    def test_invalid_returns_zero(self):
        assert Document.safe_float("not-a-number") == 0.0

    def test_string_number(self):
        assert Document.safe_float("3.14") == 3.14


class TestSafePackageVersion:
    def test_unknown_package_returns_unknown(self):
        assert (
            Document._safe_package_version("definitely-not-a-package-xyz") == "unknown"
        )

    def test_known_package_returns_version_string(self):
        # numpy is a transitive dep
        v = Document._safe_package_version("numpy")
        assert isinstance(v, str)


class TestDetectTesseractEngineVersion:
    def test_returns_string(self):
        # When pytesseract is installed but tesseract binary is missing,
        # the helper should swallow the error and return "unknown".
        out = Document._detect_tesseract_engine_version()
        assert isinstance(out, str)

    def test_pytesseract_missing_returns_unknown(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "pytesseract", None)
        assert Document._detect_tesseract_engine_version() == "unknown"


class TestNormalizeOcrModels:
    def test_non_list_returns_empty(self):
        assert Document._normalize_ocr_models("not a list") == []

    def test_strings_become_models(self):
        models = Document._normalize_ocr_models(["alpha", "beta"])
        assert models == [
            OCRModelProvenance(name="alpha"),
            OCRModelProvenance(name="beta"),
        ]

    def test_dict_with_name_only(self):
        models = Document._normalize_ocr_models([{"name": "ocr_v1"}])
        assert models == [OCRModelProvenance(name="ocr_v1")]

    def test_dict_with_full_metadata(self):
        models = Document._normalize_ocr_models(
            [
                {
                    "model": "alpha",
                    "version": 12,
                    "weights_id": 7,
                }
            ]
        )
        assert models == [
            OCRModelProvenance(name="alpha", version="12", weights_id="7"),
        ]

    def test_empty_string_skipped(self):
        models = Document._normalize_ocr_models(["", {"name": ""}])
        assert models == []

    def test_dict_without_name_skipped(self):
        models = Document._normalize_ocr_models([{"foo": "bar"}])
        assert models == []


class TestBuildOcrProvenance:
    def test_explicit_fingerprint(self):
        prov = Document._build_ocr_provenance(
            engine="x",
            metadata={"config_fingerprint": 1234, "engine_version": "1.0"},
        )
        assert prov.config_fingerprint == "1234"

    def test_constructed_fingerprint_from_source_lib(self):
        prov = Document._build_ocr_provenance(
            engine="x",
            metadata={
                "source_lib": "src",
                "models": ["a", "b"],
            },
        )
        # Constructed from source_lib + sorted model names
        assert prov.config_fingerprint == "src|a|b"

    def test_no_fingerprint_when_no_parts(self):
        prov = Document._build_ocr_provenance(engine="x", metadata={})
        assert prov.config_fingerprint is None


class TestFromImageOcrViaDoctr:
    def test_with_ndarray(self):
        # Patch out the predictor and the doctr-output-conversion entirely
        fake_predictor = MagicMock()
        # Mock doctr_result with .render() and .export()
        doctr_result = MagicMock()
        doctr_result.render.return_value = ["rendered"]
        doctr_result.export.return_value = {
            "metadata": {},
            "pages": [{"dimensions": [100, 100], "blocks": []}],
        }
        fake_predictor.return_value = doctr_result

        img = np.zeros((50, 50, 3), dtype=np.uint8)
        doc = Document.from_image_ocr_via_doctr(img, predictor=fake_predictor)
        assert isinstance(doc, Document)
        assert doc.pages[0].cv2_numpy_page_image is img
        fake_predictor.assert_called_once()

    def test_with_grayscale_ndarray(self):
        fake_predictor = MagicMock()
        doctr_result = MagicMock()
        doctr_result.render.return_value = ["rendered"]
        doctr_result.export.return_value = {
            "metadata": {},
            "pages": [{"dimensions": [50, 50], "blocks": []}],
        }
        fake_predictor.return_value = doctr_result

        gray = np.zeros((50, 50), dtype=np.uint8)
        doc = Document.from_image_ocr_via_doctr(gray, predictor=fake_predictor)
        assert isinstance(doc, Document)

    def test_with_single_channel_3d_ndarray(self):
        fake_predictor = MagicMock()
        doctr_result = MagicMock()
        doctr_result.render.return_value = ["rendered"]
        doctr_result.export.return_value = {
            "metadata": {},
            "pages": [{"dimensions": [50, 50], "blocks": []}],
        }
        fake_predictor.return_value = doctr_result

        img = np.zeros((50, 50, 1), dtype=np.uint8)
        doc = Document.from_image_ocr_via_doctr(img, predictor=fake_predictor)
        assert isinstance(doc, Document)

    def test_with_path_loads_via_imread(self, tmp_path):
        # Create an actual PNG file
        import cv2

        img_path = tmp_path / "img.png"
        cv2.imwrite(str(img_path), np.zeros((20, 20, 3), dtype=np.uint8))

        fake_predictor = MagicMock()
        doctr_result = MagicMock()
        doctr_result.render.return_value = ["rendered"]
        doctr_result.export.return_value = {
            "metadata": {},
            "pages": [{"dimensions": [20, 20], "blocks": []}],
        }
        fake_predictor.return_value = doctr_result

        doc = Document.from_image_ocr_via_doctr(str(img_path), predictor=fake_predictor)
        assert isinstance(doc, Document)
        assert doc.source_path == Path(str(img_path))

    def test_invalid_path_raises_value_error(self):
        fake_predictor = MagicMock()
        with pytest.raises(ValueError, match="Failed to load image"):
            Document.from_image_ocr_via_doctr(
                "/path/that/does/not/exist.png", predictor=fake_predictor
            )

    def test_with_pil_image(self):
        try:
            from PIL import Image as PILImageModule
        except ImportError:
            pytest.skip("PIL not installed")

        pil_image = PILImageModule.fromarray(
            np.zeros((20, 20, 3), dtype=np.uint8), mode="RGB"
        )

        fake_predictor = MagicMock()
        doctr_result = MagicMock()
        doctr_result.render.return_value = ["rendered"]
        doctr_result.export.return_value = {
            "metadata": {},
            "pages": [{"dimensions": [20, 20], "blocks": []}],
        }
        fake_predictor.return_value = doctr_result

        doc = Document.from_image_ocr_via_doctr(pil_image, predictor=fake_predictor)
        assert isinstance(doc, Document)

    def test_default_predictor_invokes_get_default_doctr_predictor(self):
        # Patch get_default_doctr_predictor inside document module
        fake_predictor = MagicMock()
        doctr_result = MagicMock()
        doctr_result.render.return_value = []
        doctr_result.export.return_value = {
            "metadata": {},
            "pages": [{"dimensions": [10, 10], "blocks": []}],
        }
        fake_predictor.return_value = doctr_result

        with patch(
            "pd_book_tools.ocr.document.get_default_doctr_predictor",
            return_value=fake_predictor,
        ) as mock_get_default:
            img = np.zeros((10, 10, 3), dtype=np.uint8)
            Document.from_image_ocr_via_doctr(img)
            mock_get_default.assert_called_once()


class TestFromDoctrOutputEdgeCases:
    def test_geometry_missing_for_block_and_line(self):
        doctr_output = {
            "metadata": {},
            "pages": [
                {
                    "dimensions": [100, 100],
                    "blocks": [
                        {
                            # No geometry
                            "lines": [
                                {
                                    # No geometry on line either
                                    "words": [
                                        {
                                            "value": "abc",
                                            "geometry": [[0.1, 0.1], [0.2, 0.2]],
                                            "confidence": 0.9,
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        doc = Document.from_doctr_output(doctr_output)
        assert isinstance(doc, Document)
        assert len(doc.pages) == 1

    def test_string_source_path_converted(self):
        doc = Document.from_doctr_output(
            {"metadata": {}, "pages": []}, source_path="some_path.png"
        )
        assert isinstance(doc.source_path, Path)

    def test_metadata_not_dict_treated_as_empty(self):
        doctr_output = {
            "metadata": "not a dict",
            "pages": [{"dimensions": [10, 10], "blocks": []}],
        }
        doc = Document.from_doctr_output(doctr_output)
        assert doc.pages[0].ocr_provenance is not None

    def test_with_original_text_assigned_per_page(self):
        doctr_output = {
            "metadata": {},
            "pages": [{"dimensions": [10, 10], "blocks": []}],
        }
        doc = Document.from_doctr_output(
            doctr_output,
            original_text=["hello"],
        )
        assert doc.pages[0].original_ocr_tool_text == "hello"


class TestFromTesseractMissingPandas:
    def test_missing_pandas_raises_import_error(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "pandas", None)

        with pytest.raises(ImportError, match="pandas"):
            Document.from_tesseract(MagicMock())


class TestFromTesseractStringFirstPage:
    def test_tesseract_string_assigned(self):
        from pandas import DataFrame

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
        doc = Document.from_tesseract(df, tesseract_string="full text")
        assert doc.pages[0].original_ocr_tool_text == "full text"


class TestToFromDictEmptyPages:
    def test_to_dict_empty_pages(self):
        doc = Document(source_lib="x", source_path=None, pages=[])
        out = doc.to_dict()
        assert out["pages"] == []

    def test_from_dict_default_paths(self):
        doc = Document.from_dict({})
        assert doc.source_lib == ""
        assert doc.source_path is None
        assert doc.pages == []
