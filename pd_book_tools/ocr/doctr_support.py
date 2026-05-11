from collections.abc import Mapping
from logging import getLogger
from os import PathLike
from pathlib import Path

logger = getLogger(__name__)

# Default vocabulary used when training and loading models.
# Trainers and predictors should both reference these so the vocab stays in sync.
DEFAULT_VOCAB_LIBRARY: list[str] = ["multilingual", "currency"]
DEFAULT_VOCAB_EXTRA_CHARS: str = "⸺¡¿—\u2018\u2019“”\u2032″\u2044"  # LEFT/RIGHT SINGLE QUOTATION MARK, PRIME, FRACTION SLASH


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


def _read_vocab_sidecar(pt_file: PathLike) -> str | None:
    """Return the vocab string written in a ``<stem>.vocab`` sidecar, if any."""
    try:
        sidecar = Path(pt_file).with_suffix(".vocab")
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


def _select_torch_device() -> tuple[str, str]:
    """Pick a torch device, preferring CUDA, then Apple MPS, else CPU.

    Returns a ``(device, device_nbr)`` pair where ``device`` is the
    short name used by ``model.to(...)`` and ``device_nbr`` is the
    longer form used by ``torch.load(..., map_location=...)``. Lifted
    out of :func:`get_finetuned_torch_doctr_predictor` as part of the
    R-15 finishing extraction so device selection is independently
    testable.
    """
    import torch as _torch
    from torch.cuda import is_available as torch_cuda_is_available

    if torch_cuda_is_available():
        return "cuda", "cuda:0"
    if getattr(_torch.backends, "mps", None) and _torch.backends.mps.is_available():
        return "mps", "mps"
    return "cpu", "cpu"


def _build_doctr_arch(arch_name: str, doctr_models, **kwargs):
    """Resolve a DocTR model factory by name with a safe fallback.

    Looks up ``arch_name`` on the (possibly mocked) ``doctr.models``
    module passed in as ``doctr_models``. When the name is unknown,
    falls back to the historical defaults so older checkpoints and
    tests with mocked modules keep working: ``db_resnet50`` for
    detection-flavored names, ``crnn_vgg16_bn`` for recognition.

    Lifted from a closure inside
    :func:`get_finetuned_torch_doctr_predictor` as part of the R-15
    finishing extraction so the fallback policy is independently
    testable.
    """
    from doctr.models import (
        crnn_vgg16_bn,
        db_resnet50,
    )

    factory = getattr(doctr_models, arch_name, None) if doctr_models else None
    if factory is None:
        fallback = (
            "db_resnet50"
            if "resnet" in arch_name
            or "linknet" in arch_name
            or arch_name.startswith("db_")
            else "crnn_vgg16_bn"
        )
        factory = (
            getattr(doctr_models, fallback)
            if doctr_models
            else (db_resnet50 if fallback == "db_resnet50" else crnn_vgg16_bn)
        )
    return factory(**kwargs)


def _assemble_doctr_predictor(det_model, reco_model, *, pretrained: bool):
    """Wrap loaded det/reco models into a DocTR ``OCRPredictor``.

    Builds the full ``ocr_predictor`` plus the standalone
    ``detection_predictor`` and ``recognition_predictor`` and attaches
    the latter two onto the full predictor — matching the historical
    contract that callers can reach into ``predictor.det_predictor`` /
    ``predictor.reco_predictor``. Extracted from
    :func:`get_finetuned_torch_doctr_predictor` as the final R-15
    helper so predictor assembly is independent of model loading.
    """
    from doctr.models import (
        detection_predictor,
        ocr_predictor,
        recognition_predictor,
    )

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


def _load_det_model(
    *,
    det_path: Path,
    torch_load,
    device: str,
    device_nbr: str,
    build_arch,
):
    """Load and return a DocTR detection model from ``det_path``.

    Architecture is read from the ``.arch`` sidecar when present and falls
    back to heuristic detection over the state_dict keys. The model is
    constructed with ``pretrained=False`` because the immediately
    following ``load_state_dict`` call overwrites all weights — passing
    ``pretrained=True`` would download doctr-hosted weights from the
    internet just to discard them (M-24). Mismatch failures are wrapped
    so the offending file and detected arch surface in the message
    instead of a bare framework error (M-23).
    """
    det_params = torch_load(det_path, map_location=device_nbr)
    det_arch_name = _read_arch_sidecar(det_path) or _detect_detection_arch(det_params)
    det_model = build_arch(det_arch_name, pretrained=False).to(device)
    try:
        det_model.load_state_dict(det_params)
    except (RuntimeError, KeyError) as e:
        raise RuntimeError(
            f"Failed to load DocTR detection checkpoint {det_path} into "
            f"architecture {det_arch_name!r}: {e}"
        ) from e
    return det_model


def _load_reco_model(
    *,
    reco_path: Path,
    vocab: str,
    torch_load,
    device: str,
    device_nbr: str,
    build_arch,
):
    """Load and return a DocTR recognition model from ``reco_path``.

    Same ``pretrained=False`` reasoning as :func:`_load_det_model`: the
    immediately-following ``load_state_dict`` overwrites every weight, so
    network-fetching pretrained weights at construction time is pure
    waste (M-24). Some archs (e.g. ``parseq``) do not accept the
    ``pretrained_backbone`` kwarg, so a ``TypeError`` triggers a retry
    without it. Load failures are wrapped (M-23).
    """
    reco_params = torch_load(reco_path, map_location=device_nbr)
    reco_arch_name = _read_arch_sidecar(reco_path) or _detect_recognition_arch(
        reco_params
    )
    reco_kwargs = dict(
        pretrained=False,
        pretrained_backbone=False,
        vocab=vocab,
    )
    try:
        reco_model = build_arch(reco_arch_name, **reco_kwargs).to(device)
    except TypeError:
        reco_kwargs.pop("pretrained_backbone", None)
        reco_model = build_arch(reco_arch_name, **reco_kwargs).to(device)
    try:
        reco_model.load_state_dict(reco_params)
    except (RuntimeError, KeyError) as e:
        raise RuntimeError(
            f"Failed to load DocTR recognition checkpoint {reco_path} into "
            f"architecture {reco_arch_name!r}: {e}"
        ) from e
    return reco_model


def get_finetuned_torch_doctr_predictor(
    dectection_pt_file: PathLike,
    recognition_pt_file: PathLike,
    vocab: str = "",
    pretrained: bool = True,
    pretrained_backbone: bool = True,
    device: str | None = None,
):
    try:
        from torch import load as torch_load
    except ImportError as err:
        raise ImportError("PyTorch is not available in this environment.") from err

    import sys as _sys

    from doctr.datasets.vocabs import VOCABS
    from doctr.models import (  # imported to ensure doctr.models is loaded before _doctr_models lookup
        crnn_vgg16_bn,
        db_resnet50,
    )

    _doctr_models = _sys.modules.get("doctr.models")

    def _build_arch(arch_name: str, **kwargs):
        """Closure adapter: bind ``_doctr_models`` to the module-level helper."""
        return _build_doctr_arch(arch_name, _doctr_models, **kwargs)

    # check if file exists — raise loudly on absence so callers don't get a
    # silent ``None`` and crash later with a confusing AttributeError on first
    # use of the predictor (M-22).
    det_path = Path(dectection_pt_file)
    reco_path = Path(recognition_pt_file)
    if not det_path.exists():
        raise FileNotFoundError(f"DocTR detection checkpoint not found: {det_path}")
    if not reco_path.exists():
        raise FileNotFoundError(f"DocTR recognition checkpoint not found: {reco_path}")

    logger.info("Loading pre-trained OCR models...")
    # Select compute device: CUDA > MPS (Apple Silicon) > CPU, unless the
    # caller has pinned a specific device (e.g. "cpu" for reproducible tests).
    device, device_nbr = _select_torch_device() if device is None else (device, device)
    logger.info("Using device: %s", device)

    # ---- Detection model -------------------------------------------------
    det_model = _load_det_model(
        det_path=det_path,
        torch_load=torch_load,
        device=device,
        device_nbr=device_nbr,
        build_arch=_build_arch,
    )

    if not vocab:
        vocab = _read_vocab_sidecar(recognition_pt_file) or "".join(
            sorted(
                dict.fromkeys(
                    "".join(
                        VOCABS[name] for name in DEFAULT_VOCAB_LIBRARY if name in VOCABS
                    )
                    + DEFAULT_VOCAB_EXTRA_CHARS
                )
            )
        )

    # ---- Recognition model ----------------------------------------------
    reco_model = _load_reco_model(
        reco_path=reco_path,
        vocab=vocab,
        torch_load=torch_load,
        device=device,
        device_nbr=device_nbr,
        build_arch=_build_arch,
    )

    return _assemble_doctr_predictor(det_model, reco_model, pretrained=pretrained)
