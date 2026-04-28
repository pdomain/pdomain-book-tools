"""Tests for ocr.doctr_support module.

These tests focus on import-error handling and code paths that don't actually
require the docTR / PyTorch dependencies to be installed. The heavy-weight
predictor builders are exercised with mocks.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest


class TestGetDefaultDoctrPredictor:
    """Cover the import-error branch of get_default_doctr_predictor."""

    def test_import_error_raises_helpful_error(self, monkeypatch):
        """When doctr.models is unavailable, the helper should raise ImportError."""
        # Ensure the import inside the function fails by removing doctr.models
        monkeypatch.setitem(sys.modules, "doctr.models", None)

        from pd_book_tools.ocr.doctr_support import get_default_doctr_predictor

        with pytest.raises(ImportError, match="docTR library is required"):
            get_default_doctr_predictor()

    def test_returns_predictor_when_doctr_available(self):
        """When doctr is mocked-in, get_default_doctr_predictor should return its result."""
        fake_predictor = MagicMock(name="fake_predictor")
        fake_module = MagicMock()
        fake_module.crnn_vgg16_bn = MagicMock(return_value="reco_arch")
        fake_module.db_resnet50 = MagicMock(return_value="det_arch")
        fake_module.ocr_predictor = MagicMock(return_value=fake_predictor)

        with patch.dict(sys.modules, {"doctr.models": fake_module}):
            from pd_book_tools.ocr.doctr_support import get_default_doctr_predictor

            result = get_default_doctr_predictor()

        assert result is fake_predictor
        fake_module.ocr_predictor.assert_called_once()
        kwargs = fake_module.ocr_predictor.call_args.kwargs
        assert kwargs["assume_straight_pages"] is True
        assert kwargs["disable_crop_orientation"] is True
        assert kwargs["pretrained"] is True


class TestGetFinetunedTorchDoctrPredictor:
    """Cover the import-error branch of get_finetuned_torch_doctr_predictor."""

    def test_import_error_when_torch_missing(self, monkeypatch, tmp_path):
        # Force the inline `from torch import load` to fail
        monkeypatch.setitem(sys.modules, "torch", None)

        from pd_book_tools.ocr.doctr_support import (
            get_finetuned_torch_doctr_predictor,
        )

        with pytest.raises(ImportError, match="PyTorch is not available"):
            get_finetuned_torch_doctr_predictor(
                dectection_pt_file=tmp_path / "det.pt",
                recognition_pt_file=tmp_path / "reco.pt",
            )

    def test_missing_files_returns_none(self, monkeypatch, tmp_path):
        """When the model files don't exist on disk, the helper should return None."""
        # Provide a stub torch module so the import succeeds
        fake_torch = MagicMock()
        fake_torch.load = MagicMock()
        fake_torch.cuda = MagicMock()
        fake_torch.cuda.is_available = MagicMock(return_value=False)

        # Provide stub doctr modules
        fake_vocabs = MagicMock()
        fake_vocabs.VOCABS = {"multilingual": "abc", "currency": "$"}
        fake_models = MagicMock()
        fake_models.crnn_vgg16_bn = MagicMock()
        fake_models.db_resnet50 = MagicMock()
        fake_models.detection_predictor = MagicMock()
        fake_models.ocr_predictor = MagicMock()
        fake_models.recognition_predictor = MagicMock()

        monkeypatch.setitem(sys.modules, "torch", fake_torch)
        monkeypatch.setitem(sys.modules, "torch.cuda", fake_torch.cuda)
        monkeypatch.setitem(sys.modules, "doctr.datasets.vocabs", fake_vocabs)
        monkeypatch.setitem(sys.modules, "doctr.models", fake_models)

        from pd_book_tools.ocr.doctr_support import (
            get_finetuned_torch_doctr_predictor,
        )

        result = get_finetuned_torch_doctr_predictor(
            dectection_pt_file=tmp_path / "missing_det.pt",
            recognition_pt_file=tmp_path / "missing_reco.pt",
        )
        # Files do not exist, so the helper falls through and returns None
        assert result is None
