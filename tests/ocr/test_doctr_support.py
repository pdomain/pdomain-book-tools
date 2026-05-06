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

    def test_missing_files_raises_file_not_found(self, monkeypatch, tmp_path):
        """Regression for M-22: missing checkpoint files must raise FileNotFoundError.

        Pre-fix, the function silently returned ``None`` and callers crashed
        later with confusing ``TypeError`` / ``AttributeError`` at first use.
        Post-fix, the helper raises ``FileNotFoundError`` naming the offending
        path so the failure mode is loud and immediate.
        """
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

        missing_det = tmp_path / "missing_det.pt"
        missing_reco = tmp_path / "missing_reco.pt"
        with pytest.raises(FileNotFoundError) as exc_info:
            get_finetuned_torch_doctr_predictor(
                dectection_pt_file=missing_det,
                recognition_pt_file=missing_reco,
            )
        # The error must name at least one of the offending paths so the
        # caller can act on it without re-deriving which file was missing.
        msg = str(exc_info.value)
        assert "missing_det.pt" in msg or "missing_reco.pt" in msg

    def test_missing_one_file_raises_file_not_found(self, monkeypatch, tmp_path):
        """When only one of the two checkpoints is missing, still raise."""
        # Detection file exists, recognition file does not.
        det_path = tmp_path / "det.pt"
        det_path.write_bytes(b"fake")
        missing_reco = tmp_path / "missing_reco.pt"

        fake_torch = MagicMock()
        fake_torch.load = MagicMock()
        fake_torch.cuda = MagicMock()
        fake_torch.cuda.is_available = MagicMock(return_value=False)

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

        with pytest.raises(FileNotFoundError) as exc_info:
            get_finetuned_torch_doctr_predictor(
                dectection_pt_file=det_path,
                recognition_pt_file=missing_reco,
            )
        assert "missing_reco.pt" in str(exc_info.value)

    def test_missing_files_with_str_paths_raises(self, monkeypatch, tmp_path):
        """Regression for H-13 + M-22: ``str`` paths must hit the same branch.

        H-13 fixed ``Path.exists(x)`` (which raised ``AttributeError`` on
        ``str`` arguments) to ``Path(x).exists()``. M-22 then converts the
        missing-files fall-through from a silent ``return None`` into an
        explicit ``FileNotFoundError``. Both flavors of input must surface the
        same loud failure.
        """
        fake_torch = MagicMock()
        fake_torch.load = MagicMock()
        fake_torch.cuda = MagicMock()
        fake_torch.cuda.is_available = MagicMock(return_value=False)

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

        # str paths, not Path objects.
        with pytest.raises(FileNotFoundError):
            get_finetuned_torch_doctr_predictor(
                dectection_pt_file=str(tmp_path / "missing_det.pt"),
                recognition_pt_file=str(tmp_path / "missing_reco.pt"),
            )

    def test_happy_path_with_existing_files(self, monkeypatch, tmp_path):
        """With pretrained files present, the helper should construct a predictor."""
        det_path = tmp_path / "det.pt"
        reco_path = tmp_path / "reco.pt"
        det_path.write_bytes(b"fake")
        reco_path.write_bytes(b"fake")

        # Stub torch
        fake_torch = MagicMock()
        fake_torch.load = MagicMock(return_value={})
        fake_torch.cuda = MagicMock()
        fake_torch.cuda.is_available = MagicMock(return_value=False)

        # Stub doctr modules
        fake_vocabs = MagicMock()
        fake_vocabs.VOCABS = {"multilingual": "abc", "currency": "$"}

        fake_det_model = MagicMock()
        fake_det_model.to = MagicMock(return_value=fake_det_model)
        fake_reco_model = MagicMock()
        fake_reco_model.to = MagicMock(return_value=fake_reco_model)
        fake_predictor = MagicMock()
        fake_det_predictor = MagicMock()
        fake_reco_predictor = MagicMock()

        fake_models = MagicMock()
        fake_models.crnn_vgg16_bn = MagicMock(return_value=fake_reco_model)
        fake_models.db_resnet50 = MagicMock(return_value=fake_det_model)
        fake_models.detection_predictor = MagicMock(return_value=fake_det_predictor)
        fake_models.ocr_predictor = MagicMock(return_value=fake_predictor)
        fake_models.recognition_predictor = MagicMock(return_value=fake_reco_predictor)

        monkeypatch.setitem(sys.modules, "torch", fake_torch)
        monkeypatch.setitem(sys.modules, "torch.cuda", fake_torch.cuda)
        monkeypatch.setitem(sys.modules, "doctr.datasets.vocabs", fake_vocabs)
        monkeypatch.setitem(sys.modules, "doctr.models", fake_models)

        from pd_book_tools.ocr.doctr_support import (
            get_finetuned_torch_doctr_predictor,
        )

        result = get_finetuned_torch_doctr_predictor(
            dectection_pt_file=det_path,
            recognition_pt_file=reco_path,
        )
        assert result is fake_predictor
        # Verify det/reco predictors got attached
        assert fake_predictor.det_predictor is fake_det_predictor
        assert fake_predictor.reco_predictor is fake_reco_predictor

    def test_happy_path_with_custom_vocab(self, monkeypatch, tmp_path):
        """If vocab is provided explicitly, it should be passed through."""
        det_path = tmp_path / "det.pt"
        reco_path = tmp_path / "reco.pt"
        det_path.write_bytes(b"fake")
        reco_path.write_bytes(b"fake")

        fake_torch = MagicMock()
        fake_torch.load = MagicMock(return_value={})
        fake_torch.cuda = MagicMock()
        fake_torch.cuda.is_available = MagicMock(return_value=False)

        fake_vocabs = MagicMock()
        fake_vocabs.VOCABS = {"multilingual": "abc", "currency": "$"}

        fake_det_model = MagicMock()
        fake_det_model.to = MagicMock(return_value=fake_det_model)
        fake_reco_model = MagicMock()
        fake_reco_model.to = MagicMock(return_value=fake_reco_model)

        fake_models = MagicMock()
        fake_models.crnn_vgg16_bn = MagicMock(return_value=fake_reco_model)
        fake_models.db_resnet50 = MagicMock(return_value=fake_det_model)
        fake_models.detection_predictor = MagicMock(return_value=MagicMock())
        fake_models.ocr_predictor = MagicMock(return_value=MagicMock())
        fake_models.recognition_predictor = MagicMock(return_value=MagicMock())

        monkeypatch.setitem(sys.modules, "torch", fake_torch)
        monkeypatch.setitem(sys.modules, "torch.cuda", fake_torch.cuda)
        monkeypatch.setitem(sys.modules, "doctr.datasets.vocabs", fake_vocabs)
        monkeypatch.setitem(sys.modules, "doctr.models", fake_models)

        from pd_book_tools.ocr.doctr_support import (
            get_finetuned_torch_doctr_predictor,
        )

        get_finetuned_torch_doctr_predictor(
            dectection_pt_file=det_path,
            recognition_pt_file=reco_path,
            vocab="custom_vocab",
        )
        kwargs = fake_models.crnn_vgg16_bn.call_args.kwargs
        assert kwargs["vocab"] == "custom_vocab"

    def test_det_load_state_dict_failure_names_checkpoint_and_arch(
        self, monkeypatch, tmp_path
    ):
        """Regression for M-23: a detection-model load_state_dict failure must
        re-raise with the offending checkpoint path and detected architecture
        name in the message.

        Pre-fix, a torch ``RuntimeError("size mismatch ...")`` propagated as-is
        from deep inside torch with no indication of which file or which arch
        caused it. Post-fix, the helper wraps the call and re-raises with both
        identifiers, preserving the original via ``raise ... from e``.
        """
        det_path = tmp_path / "bad_det.pt"
        reco_path = tmp_path / "reco.pt"
        det_path.write_bytes(b"fake")
        reco_path.write_bytes(b"fake")

        fake_torch = MagicMock()
        fake_torch.load = MagicMock(return_value={})
        fake_torch.cuda = MagicMock()
        fake_torch.cuda.is_available = MagicMock(return_value=False)

        fake_vocabs = MagicMock()
        fake_vocabs.VOCABS = {"multilingual": "abc", "currency": "$"}

        fake_det_model = MagicMock()
        fake_det_model.to = MagicMock(return_value=fake_det_model)
        fake_det_model.load_state_dict = MagicMock(
            side_effect=RuntimeError("size mismatch for some.weight: ...")
        )
        fake_reco_model = MagicMock()
        fake_reco_model.to = MagicMock(return_value=fake_reco_model)

        fake_models = MagicMock()
        fake_models.crnn_vgg16_bn = MagicMock(return_value=fake_reco_model)
        fake_models.db_resnet50 = MagicMock(return_value=fake_det_model)
        fake_models.detection_predictor = MagicMock(return_value=MagicMock())
        fake_models.ocr_predictor = MagicMock(return_value=MagicMock())
        fake_models.recognition_predictor = MagicMock(return_value=MagicMock())

        monkeypatch.setitem(sys.modules, "torch", fake_torch)
        monkeypatch.setitem(sys.modules, "torch.cuda", fake_torch.cuda)
        monkeypatch.setitem(sys.modules, "doctr.datasets.vocabs", fake_vocabs)
        monkeypatch.setitem(sys.modules, "doctr.models", fake_models)

        from pd_book_tools.ocr.doctr_support import (
            get_finetuned_torch_doctr_predictor,
        )

        with pytest.raises(RuntimeError) as exc_info:
            get_finetuned_torch_doctr_predictor(
                dectection_pt_file=det_path,
                recognition_pt_file=reco_path,
            )

        msg = str(exc_info.value)
        # Checkpoint path must be named so the user knows which file is wrong.
        assert "bad_det.pt" in msg
        # Detected arch name must be named so the user can correct or override.
        # ``db_resnet50`` is the default detection arch for an empty state_dict.
        assert "db_resnet50" in msg
        # Original exception preserved via ``raise ... from e``.
        assert isinstance(exc_info.value.__cause__, RuntimeError)
        assert "size mismatch" in str(exc_info.value.__cause__)

    def test_reco_load_state_dict_failure_names_checkpoint_and_arch(
        self, monkeypatch, tmp_path
    ):
        """Regression for M-23: same contract for the recognition model.

        A ``KeyError`` (missing key) raised by torch deep inside
        ``reco_model.load_state_dict`` must be wrapped to name the recognition
        checkpoint path and the detected reco arch.
        """
        det_path = tmp_path / "det.pt"
        reco_path = tmp_path / "bad_reco.pt"
        det_path.write_bytes(b"fake")
        reco_path.write_bytes(b"fake")

        fake_torch = MagicMock()
        fake_torch.load = MagicMock(return_value={})
        fake_torch.cuda = MagicMock()
        fake_torch.cuda.is_available = MagicMock(return_value=False)

        fake_vocabs = MagicMock()
        fake_vocabs.VOCABS = {"multilingual": "abc", "currency": "$"}

        fake_det_model = MagicMock()
        fake_det_model.to = MagicMock(return_value=fake_det_model)
        fake_reco_model = MagicMock()
        fake_reco_model.to = MagicMock(return_value=fake_reco_model)
        fake_reco_model.load_state_dict = MagicMock(
            side_effect=KeyError("missing.key.in.state_dict")
        )

        fake_models = MagicMock()
        fake_models.crnn_vgg16_bn = MagicMock(return_value=fake_reco_model)
        fake_models.db_resnet50 = MagicMock(return_value=fake_det_model)
        fake_models.detection_predictor = MagicMock(return_value=MagicMock())
        fake_models.ocr_predictor = MagicMock(return_value=MagicMock())
        fake_models.recognition_predictor = MagicMock(return_value=MagicMock())

        monkeypatch.setitem(sys.modules, "torch", fake_torch)
        monkeypatch.setitem(sys.modules, "torch.cuda", fake_torch.cuda)
        monkeypatch.setitem(sys.modules, "doctr.datasets.vocabs", fake_vocabs)
        monkeypatch.setitem(sys.modules, "doctr.models", fake_models)

        from pd_book_tools.ocr.doctr_support import (
            get_finetuned_torch_doctr_predictor,
        )

        with pytest.raises(RuntimeError) as exc_info:
            get_finetuned_torch_doctr_predictor(
                dectection_pt_file=det_path,
                recognition_pt_file=reco_path,
            )

        msg = str(exc_info.value)
        assert "bad_reco.pt" in msg
        # Default recognition arch for an empty state_dict is crnn_vgg16_bn.
        assert "crnn_vgg16_bn" in msg
        # Original cause preserved.
        assert isinstance(exc_info.value.__cause__, KeyError)

    def test_arch_construction_skips_pretrained_download(self, monkeypatch, tmp_path):
        """Regression for M-24: arch construction must pass ``pretrained=False``.

        The next statement after each ``_build_arch`` call is
        ``load_state_dict(...)``, which overwrites every weight. Constructing
        the arch with ``pretrained=True`` (or letting it default to True via
        the public ``pretrained``/``pretrained_backbone`` kwargs) downloads
        weights from the internet only to immediately discard them — pure
        network waste plus an unwanted runtime dependency.
        """
        det_path = tmp_path / "det.pt"
        reco_path = tmp_path / "reco.pt"
        det_path.write_bytes(b"fake")
        reco_path.write_bytes(b"fake")

        fake_torch = MagicMock()
        fake_torch.load = MagicMock(return_value={})
        fake_torch.cuda = MagicMock()
        fake_torch.cuda.is_available = MagicMock(return_value=False)

        fake_vocabs = MagicMock()
        fake_vocabs.VOCABS = {"multilingual": "abc", "currency": "$"}

        fake_det_model = MagicMock()
        fake_det_model.to = MagicMock(return_value=fake_det_model)
        fake_reco_model = MagicMock()
        fake_reco_model.to = MagicMock(return_value=fake_reco_model)

        fake_models = MagicMock()
        fake_models.crnn_vgg16_bn = MagicMock(return_value=fake_reco_model)
        fake_models.db_resnet50 = MagicMock(return_value=fake_det_model)
        fake_models.detection_predictor = MagicMock(return_value=MagicMock())
        fake_models.ocr_predictor = MagicMock(return_value=MagicMock())
        fake_models.recognition_predictor = MagicMock(return_value=MagicMock())

        monkeypatch.setitem(sys.modules, "torch", fake_torch)
        monkeypatch.setitem(sys.modules, "torch.cuda", fake_torch.cuda)
        monkeypatch.setitem(sys.modules, "doctr.datasets.vocabs", fake_vocabs)
        monkeypatch.setitem(sys.modules, "doctr.models", fake_models)

        from pd_book_tools.ocr.doctr_support import (
            get_finetuned_torch_doctr_predictor,
        )

        # Even when callers pass the default ``pretrained=True`` /
        # ``pretrained_backbone=True``, the arch builders must be invoked with
        # ``pretrained=False`` because their weights are about to be
        # overwritten by ``load_state_dict``.
        get_finetuned_torch_doctr_predictor(
            dectection_pt_file=det_path,
            recognition_pt_file=reco_path,
            pretrained=True,
            pretrained_backbone=True,
        )

        # Detection arch (db_resnet50 default for empty state_dict) was
        # constructed with pretrained=False.
        det_kwargs = fake_models.db_resnet50.call_args.kwargs
        assert det_kwargs.get("pretrained") is False, (
            f"detection arch constructor received pretrained={det_kwargs.get('pretrained')!r} "
            "but should be False — load_state_dict immediately overwrites"
        )

        # Recognition arch (crnn_vgg16_bn default for empty state_dict) was
        # constructed with pretrained=False AND pretrained_backbone=False.
        reco_kwargs = fake_models.crnn_vgg16_bn.call_args.kwargs
        assert reco_kwargs.get("pretrained") is False, (
            f"recognition arch constructor received pretrained={reco_kwargs.get('pretrained')!r} "
            "but should be False — load_state_dict immediately overwrites"
        )
        assert reco_kwargs.get("pretrained_backbone") is False, (
            f"recognition arch constructor received "
            f"pretrained_backbone={reco_kwargs.get('pretrained_backbone')!r} "
            "but should be False — load_state_dict overwrites the entire model"
        )

    def test_happy_path_with_cuda_available(self, monkeypatch, tmp_path):
        """When CUDA is available, the helper should use the cuda device strings."""
        det_path = tmp_path / "det.pt"
        reco_path = tmp_path / "reco.pt"
        det_path.write_bytes(b"fake")
        reco_path.write_bytes(b"fake")

        fake_torch = MagicMock()
        fake_torch.load = MagicMock(return_value={})
        fake_torch.cuda = MagicMock()
        fake_torch.cuda.is_available = MagicMock(return_value=True)

        fake_vocabs = MagicMock()
        fake_vocabs.VOCABS = {"multilingual": "abc", "currency": "$"}

        fake_det_model = MagicMock()
        fake_det_model.to = MagicMock(return_value=fake_det_model)
        fake_reco_model = MagicMock()
        fake_reco_model.to = MagicMock(return_value=fake_reco_model)

        fake_models = MagicMock()
        fake_models.crnn_vgg16_bn = MagicMock(return_value=fake_reco_model)
        fake_models.db_resnet50 = MagicMock(return_value=fake_det_model)
        fake_models.detection_predictor = MagicMock(return_value=MagicMock())
        fake_models.ocr_predictor = MagicMock(return_value=MagicMock())
        fake_models.recognition_predictor = MagicMock(return_value=MagicMock())

        monkeypatch.setitem(sys.modules, "torch", fake_torch)
        monkeypatch.setitem(sys.modules, "torch.cuda", fake_torch.cuda)
        monkeypatch.setitem(sys.modules, "doctr.datasets.vocabs", fake_vocabs)
        monkeypatch.setitem(sys.modules, "doctr.models", fake_models)

        from pd_book_tools.ocr.doctr_support import (
            get_finetuned_torch_doctr_predictor,
        )

        get_finetuned_torch_doctr_predictor(
            dectection_pt_file=det_path,
            recognition_pt_file=reco_path,
        )
        # torch_load should have been called with map_location="cuda:0"
        load_kwargs = fake_torch.load.call_args.kwargs
        assert load_kwargs["map_location"] == "cuda:0"
