from __future__ import annotations

from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from os import PathLike

    from doctr.models.predictor import OCRPredictor

    class _DoctrModel(Protocol):
        """Structural contract for a loaded/loadable DocTR det/reco model.

        Matches only the ``torch.nn.Module`` surface this module actually
        calls (``.to()`` / ``.load_state_dict()``); ``unittest.mock.MagicMock``
        (used throughout the test suite) satisfies this structurally via its
        typed ``__getattr__``.
        """

        def to(self, device: str) -> _DoctrModel: ...
        def load_state_dict(self, state_dict: Mapping[str, object]) -> object: ...

    class _DoctrModelsModule(Protocol):
        """Structural contract for the (possibly mocked) ``doctr.models`` module.

        Only ``getattr(doctr_models, arch_name)`` is used, so any object
        exposing arbitrary architecture-factory attributes satisfies this —
        including a real module (``types.ModuleType``, whose ``__getattr__``
        typeshed stub is equally permissive) and ``unittest.mock.MagicMock``.
        """

        def __getattr__(self, name: str, /) -> Callable[..., _DoctrModel]: ...

    TorchLoadFn = Callable[..., object]
    BuildArchFn = Callable[..., _DoctrModel]

logger = getLogger(__name__)

# Default vocabulary used when training and loading models.
# Trainers and predictors should both reference these so the vocab stays in sync.
DEFAULT_VOCAB_LIBRARY: list[str] = ["multilingual", "currency"]
DEFAULT_VOCAB_EXTRA_CHARS: str = "⸺¡¿—\u2018\u2019“”\u2032″\u2044"  # LEFT/RIGHT SINGLE QUOTATION MARK, PRIME, FRACTION SLASH


def _read_arch_sidecar(pt_file: str | PathLike[str]) -> str | None:
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


def _read_vocab_sidecar(pt_file: str | PathLike[str]) -> str | None:
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
    keys = set(state_dict.keys()) if state_dict else set[str]()
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
    keys = set(state_dict.keys()) if state_dict else set[str]()
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


def get_default_doctr_predictor(
    det_bs: int = 2,
    reco_bs: int = 128,
) -> OCRPredictor:
    """Get the pre-trained OCR predictor from the doctr library."""
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
        det_bs=det_bs,
        reco_bs=reco_bs,
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


def _build_doctr_arch(
    arch_name: str, doctr_models: _DoctrModelsModule | None, **kwargs: object
) -> _DoctrModel:
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

    # getattr's non-literal-name overload always resolves to Any; cast to the
    # honest declared factory type instead of letting the Any propagate into
    # (and confuse the narrowing of) the ``factory`` variable below.
    factory: Callable[..., _DoctrModel] | None = (
        cast(
            "Callable[..., _DoctrModel] | None", getattr(doctr_models, arch_name, None)
        )
        if doctr_models
        else None
    )
    if factory is None:
        fallback = (
            "db_resnet50"
            if "resnet" in arch_name
            or "linknet" in arch_name
            or arch_name.startswith("db_")
            else "crnn_vgg16_bn"
        )
        factory = (
            cast("Callable[..., _DoctrModel]", getattr(doctr_models, fallback))
            if doctr_models
            else cast(
                "Callable[..., _DoctrModel]",
                db_resnet50 if fallback == "db_resnet50" else crnn_vgg16_bn,
            )
        )
    return factory(**kwargs)


def _assemble_doctr_predictor(
    det_model: _DoctrModel,
    reco_model: _DoctrModel,
    *,
    pretrained: bool,
    det_bs: int = 2,
    reco_bs: int = 128,
) -> OCRPredictor:
    """Wrap loaded det/reco models into a DocTR ``OCRPredictor``.

    Builds the full ``ocr_predictor`` plus the standalone
    ``detection_predictor`` and ``recognition_predictor`` and attaches
    the latter two onto the full predictor — matching the historical
    contract that callers can reach into ``predictor.det_predictor`` /
    ``predictor.reco_predictor``. Extracted from
    :func:`get_finetuned_torch_doctr_predictor` as the final R-15
    helper so predictor assembly is independent of model loading.

    ``det_bs`` / ``reco_bs`` are passed through to DocTR's public factory
    kwargs (``det_bs`` / ``reco_bs`` on ``ocr_predictor``; ``batch_size`` on the
    standalone predictors). Defaults match DocTR's own defaults (2 / 128).
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
        det_bs=det_bs,
        reco_bs=reco_bs,
    )
    det_predictor = detection_predictor(
        arch=det_model,
        pretrained=pretrained,
        assume_straight_pages=True,
        batch_size=det_bs,
    )
    reco_predictor = recognition_predictor(
        arch=reco_model,
        pretrained=pretrained,
        batch_size=reco_bs,
    )
    full_predictor.det_predictor = det_predictor
    full_predictor.reco_predictor = reco_predictor
    return full_predictor


def _validate_state_dict(obj: object, *, path: str) -> None:
    """Validate that *obj* looks like a PyTorch state dict.

    Raises :class:`ValueError` when:

    - *obj* is not a :class:`dict` (e.g. a pickled model instance).
    - Any value in the dict is not a :class:`torch.Tensor` (catches checkpoints
      that smuggled an arbitrary Python object as a weight tensor).

    An empty dict is accepted (used in unit tests and for fresh models).

    Called immediately after every ``torch.load`` call so that a maliciously or
    accidentally mis-pickled checkpoint is caught before any code acts on it.
    Requires PyTorch >= 2.4 (this repo pins >= 2.6) for the complementary
    ``weights_only=True`` loader defence.
    """
    import torch as _torch

    if not isinstance(obj, dict):
        raise ValueError(
            f"Checkpoint {path!r} is not a dict (state dict); "
            f"got {type(obj).__name__!r}. "
            "Only plain dict state dicts are accepted. "
            "Ensure the checkpoint was saved with model.state_dict() "
            "and comes from a trusted source."
        )
    # isinstance against the unparameterized dict erases the key/value types
    # to Unknown; the cast restores the honest key/value types this function
    # actually validates (str keys, arbitrary values checked below).
    obj_dict = cast("dict[str, object]", obj)
    for key, value in obj_dict.items():
        if not isinstance(value, _torch.Tensor):
            raise ValueError(
                f"Checkpoint {path!r}: value for key {key!r} is not a "
                f"torch.Tensor (got {type(value).__name__!r}). "
                "Only plain dict state dicts with Tensor values are accepted."
            )


def _load_det_model(
    *,
    det_path: Path,
    torch_load: TorchLoadFn,
    device: str,
    device_nbr: str,
    build_arch: BuildArchFn,
) -> _DoctrModel:
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
    _validate_state_dict(det_params, path=str(det_path))
    # _validate_state_dict raises unless obj is a dict; safe to treat as a
    # state_dict-shaped mapping from here on.
    det_state = cast("Mapping[str, object]", det_params)
    det_arch_name = _read_arch_sidecar(det_path) or _detect_detection_arch(det_state)
    det_model = build_arch(det_arch_name, pretrained=False).to(device)
    try:
        det_model.load_state_dict(det_state)
    except (RuntimeError, KeyError) as e:
        raise RuntimeError(
            f"Failed to load DocTR detection checkpoint {det_path} into architecture {det_arch_name!r}: {e}"
        ) from e
    return det_model


def _load_reco_model(
    *,
    reco_path: Path,
    vocab: str,
    torch_load: TorchLoadFn,
    device: str,
    device_nbr: str,
    build_arch: BuildArchFn,
) -> _DoctrModel:
    """Load and return a DocTR recognition model from ``reco_path``.

    Same ``pretrained=False`` reasoning as :func:`_load_det_model`: the
    immediately-following ``load_state_dict`` overwrites every weight, so
    network-fetching pretrained weights at construction time is pure
    waste (M-24). Some archs (e.g. ``parseq``) do not accept the
    ``pretrained_backbone`` kwarg, so a ``TypeError`` triggers a retry
    without it. Load failures are wrapped (M-23).
    """
    reco_params = torch_load(reco_path, map_location=device_nbr)
    _validate_state_dict(reco_params, path=str(reco_path))
    # _validate_state_dict raises unless obj is a dict; safe to treat as a
    # state_dict-shaped mapping from here on.
    reco_state = cast("Mapping[str, object]", reco_params)
    reco_arch_name = _read_arch_sidecar(reco_path) or _detect_recognition_arch(
        reco_state
    )
    reco_kwargs: dict[str, object] = {
        "pretrained": False,
        "pretrained_backbone": False,
        "vocab": vocab,
    }
    try:
        reco_model = build_arch(reco_arch_name, **reco_kwargs).to(device)
    except TypeError:
        _ = reco_kwargs.pop("pretrained_backbone", None)
        reco_model = build_arch(reco_arch_name, **reco_kwargs).to(device)
    try:
        reco_model.load_state_dict(reco_state)
    except (RuntimeError, KeyError) as e:
        raise RuntimeError(
            f"Failed to load DocTR recognition checkpoint {reco_path} into architecture {reco_arch_name!r}: {e}"
        ) from e
    return reco_model


def get_finetuned_torch_doctr_predictor(
    dectection_pt_file: str | PathLike[str],
    recognition_pt_file: str | PathLike[str],
    vocab: str = "",
    pretrained: bool = True,
    pretrained_backbone: bool = True,  # public API; _load_reco_model hardcodes pretrained_backbone=False
    device: str | None = None,
    *,
    det_bs: int = 2,
    reco_bs: int = 128,
    torch_load: TorchLoadFn | None = None,
) -> OCRPredictor:
    """Load a fine-tuned DocTR OCR predictor from local ``.pt`` checkpoint files.

    Parameters
    ----------
    dectection_pt_file:
        Path to the detection model checkpoint (``.pt``).
    recognition_pt_file:
        Path to the recognition model checkpoint (``.pt``).
    vocab:
        Character vocabulary string. Inferred from the ``.vocab`` sidecar when
        omitted.
    pretrained:
        Passed to the DocTR ``ocr_predictor`` constructor. Does *not* trigger
        a network download for the detection / recognition weights — those are
        always loaded from the local ``.pt`` files.
    pretrained_backbone:
        Public API parameter; kept for call-site compatibility. The inner
        loader always passes ``pretrained_backbone=False`` because
        ``load_state_dict`` immediately overwrites every weight.
    device:
        Torch device string (e.g. ``"cpu"``, ``"cuda"``). Defaults to
        automatic selection (CUDA > MPS > CPU).
    torch_load:
        Callable used to deserialize the ``.pt`` checkpoints. Defaults to
        ``functools.partial(torch.load, weights_only=True)``, which prevents
        arbitrary code execution via pickle. Requires PyTorch >= 2.4; this
        repo pins >= 2.6 so the default is always safe.

        Pass a custom callable only when you have a specific need (e.g.
        injecting a test stub or loading a checkpoint saved with an older
        format). In that case you are responsible for the security of the
        deserialization.
    """
    try:
        from torch import load as _torch_load_fn
    except ImportError as err:
        raise ImportError("PyTorch is not available in this environment.") from err

    if torch_load is None:
        from functools import partial as _partial

        torch_load = _partial(_torch_load_fn, weights_only=True)

    import sys as _sys

    from doctr.datasets.vocabs import VOCABS
    from doctr.models import (
        crnn_vgg16_bn,
        db_resnet50,
    )

    # Touching these names is intentional: it ensures doctr.models is fully
    # registered in sys.modules before _doctr_models lookup below (side-effect import).
    _ = (crnn_vgg16_bn, db_resnet50)
    _doctr_models = _sys.modules.get("doctr.models")

    def _build_arch(arch_name: str, **kwargs: object) -> _DoctrModel:
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

    return _assemble_doctr_predictor(
        det_model, reco_model, pretrained=pretrained, det_bs=det_bs, reco_bs=reco_bs
    )
