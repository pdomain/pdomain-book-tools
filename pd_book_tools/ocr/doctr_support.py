from os import PathLike
from pathlib import Path
from typing import Mapping


def _read_arch_sidecar(pt_file: PathLike) -> str | None:
    """Return the architecture name written in a ``<stem>.arch`` sidecar, if any.

    The trainer writes a one-line text file alongside each ``.pt`` checkpoint
    containing the doctr architecture name (e.g. ``crnn_vgg16_bn``, ``parseq``,
    ``db_resnet50``). When present, callers should prefer it over heuristic
    detection because it is authoritative.
    """
    try:
        sidecar = Path(pt_file).with_suffix(".arch")
        if sidecar.is_file():
            value = sidecar.read_text(encoding="utf-8").strip()
            return value or None
    except Exception:
        return None
    return None


def _detect_recognition_arch(state_dict: Mapping[str, object]) -> str:
    """Best-effort guess at the recognition architecture from a state_dict.

    Falls back to ``crnn_vgg16_bn`` when nothing distinctive is found so that
    legacy checkpoints (and the empty dicts used in unit tests) continue to
    work as before. Prefer ``_read_arch_sidecar`` when an ``.arch`` sidecar is
    available.
    """
    keys = set(state_dict.keys()) if state_dict else set()
    if not keys:
        return "crnn_vgg16_bn"

    # PARSeq: permuted autoregressive transformer recognizer.
    if "pos_queries" in keys and any(
        k.startswith("decoder.cross_attention") for k in keys
    ):
        return "parseq"

    # CRNN family — distinguish by feature extractor key prefix.
    has_crnn_decoder = any(k.startswith("decoder.weight_ih_l") for k in keys)
    if has_crnn_decoder and "linear.weight" in keys:
        if any(k.startswith("feat_extractor.features.") for k in keys):
            # MobileNet variants share the same key structure; default to small
            # and let the caller fall back to large on shape mismatch.
            return "crnn_mobilenet_v3_small"
        return "crnn_vgg16_bn"

    # ViTSTR family.
    if "cls_token" in keys and "pos_embed" in keys:
        return "vitstr_small"

    # SAR.
    if any(k.startswith("decoder.lstm_decoder") for k in keys):
        return "sar_resnet31"

    # MASTER (transformer encoder/decoder without PARSeq's pos_queries).
    if any(k.startswith("decoder.layers.") and ".cross_attn." in k for k in keys):
        return "master"

    return "crnn_vgg16_bn"


def _detect_detection_arch(state_dict: Mapping[str, object]) -> str:
    """Best-effort guess at the detection architecture from a state_dict.

    Defaults to ``db_resnet50`` (the historical hardcoded choice).
    """
    keys = set(state_dict.keys()) if state_dict else set()
    if not keys:
        return "db_resnet50"

    if any(k.startswith("feat_extractor.features.") for k in keys):
        # MobileNet-backed detection (DBNet / LinkNet variants).
        if any("linknet" in k.lower() for k in keys):
            return "linknet_resnet18"
        return "db_mobilenet_v3_large"
    if any(k.startswith("feat_extractor.layer") for k in keys):
        # ResNet-backed; default to db_resnet50.
        return "db_resnet50"
    return "db_resnet50"


def get_default_doctr_predictor():
    """
    Get the pre-trained OCR predictor from the doctr library.
    :return: The OCR predictor.
    """
    try:
        from doctr.models import (
            crnn_vgg16_bn,
            db_resnet50,
            ocr_predictor,
        )
    except ImportError as e:
        raise ImportError(
            "The docTR library is required for OCR. Please install it (PyPi: python-doctr)"
        ) from e

    return ocr_predictor(
        det_arch=db_resnet50(pretrained=True),
        reco_arch=crnn_vgg16_bn(pretrained=True, pretrained_backbone=True),
        pretrained=True,
        assume_straight_pages=True,
        disable_crop_orientation=True,
    )


def get_finetuned_torch_doctr_predictor(
    dectection_pt_file: PathLike,
    recognition_pt_file: PathLike,
    vocab: str = "",
    pretrained: bool = True,
    pretrained_backbone: bool = True,
):
    full_predictor = None

    try:
        from torch import load as torch_load
        from torch.cuda import is_available as torch_cuda_is_available
    except ImportError:
        raise ImportError("PyTorch is not available in this environment.")

    import sys as _sys

    from doctr.datasets.vocabs import VOCABS
    from doctr.models import (
        crnn_vgg16_bn,  # noqa: F401  (kept for back-compat / external imports)
        db_resnet50,  # noqa: F401
        detection_predictor,
        ocr_predictor,
        recognition_predictor,
    )

    _doctr_models = _sys.modules.get("doctr.models")

    def _build_arch(arch_name: str, **kwargs):
        """Resolve a doctr model factory by name with a safe fallback."""
        factory = getattr(_doctr_models, arch_name, None) if _doctr_models else None
        if factory is None:
            # Unknown name — fall back to the historical defaults so that older
            # checkpoints / tests with mocked modules keep working.
            fallback = (
                "db_resnet50"
                if "resnet" in arch_name
                or "linknet" in arch_name
                or arch_name.startswith("db_")
                else "crnn_vgg16_bn"
            )
            factory = (
                getattr(_doctr_models, fallback)
                if _doctr_models
                else (db_resnet50 if fallback == "db_resnet50" else crnn_vgg16_bn)
            )
        return factory(**kwargs)

    # check if file exists
    if Path.exists(dectection_pt_file) and Path.exists(recognition_pt_file):
        print("Loading pre-trained OCR models...")
        # Check if CUDA is available
        device, device_nbr = (
            ("cuda", "cuda:0") if torch_cuda_is_available() else ("cpu", "cpu")
        )

        # ---- Detection model -------------------------------------------------
        det_params = torch_load(dectection_pt_file, map_location=device_nbr)
        det_arch_name = _read_arch_sidecar(
            dectection_pt_file
        ) or _detect_detection_arch(det_params)
        det_model = _build_arch(det_arch_name, pretrained=True).to(device)
        det_model.load_state_dict(det_params)

        if not vocab:
            # assume the model was fine-tuned on mostly english book data with some additional unicode characters
            # (⁄ is the "fraction" character not forward slash)
            vocab = "".join(
                sorted(
                    dict.fromkeys(
                        VOCABS["multilingual"] + "⸺¡¿—‘’“”′″⁄" + VOCABS["currency"]
                    )
                )
            )

        # ---- Recognition model ----------------------------------------------
        reco_params = torch_load(recognition_pt_file, map_location=device_nbr)
        reco_arch_name = _read_arch_sidecar(
            recognition_pt_file
        ) or _detect_recognition_arch(reco_params)
        reco_kwargs = dict(
            pretrained=pretrained,
            pretrained_backbone=pretrained_backbone,
            vocab=vocab,
        )
        try:
            reco_model = _build_arch(reco_arch_name, **reco_kwargs).to(device)
        except TypeError:
            # Some archs (e.g. parseq) do not accept ``pretrained_backbone``.
            reco_kwargs.pop("pretrained_backbone", None)
            reco_model = _build_arch(reco_arch_name, **reco_kwargs).to(device)
        reco_model.load_state_dict(reco_params)

        full_predictor = ocr_predictor(
            det_arch=det_model,
            reco_arch=reco_model,
            pretrained=pretrained,
            assume_straight_pages=True,
            disable_crop_orientation=True,
        )

        det_predictor = detection_predictor(
            arch=det_model,
            pretrained=pretrained,
            assume_straight_pages=True,
        )

        reco_predictor = recognition_predictor(
            arch=reco_model,
            pretrained=pretrained,
        )

        full_predictor.det_predictor = det_predictor
        full_predictor.reco_predictor = reco_predictor

        return full_predictor
