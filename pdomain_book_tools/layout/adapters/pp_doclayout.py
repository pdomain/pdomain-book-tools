"""PP-DocLayout_plus-L adapter (RT-DETR via Hugging Face ``transformers``).

The model is loaded from
``PaddlePaddle/PP-DocLayout_plus-L_safetensors`` (Apache 2.0). A custom
fine-tuned checkpoint can be passed in via ``checkpoint_path`` — anything
that ``RTDetrForObjectDetection.from_pretrained`` accepts (a HF repo id or a
local directory).

Native labels are mapped to :class:`pdomain_book_tools.layout.types.RegionType`
via :data:`pdomain_book_tools.layout._mappings.PP_DOCLAYOUT_TO_PGDP`. Labels that
map to ``None`` are dropped.

Trust boundary
--------------
``checkpoint_path`` is a trust boundary.  Loading weights from an arbitrary
remote Hugging Face repo or untrusted local directory can execute code at
``from_pretrained`` time (``trust_remote_code`` is always ``False`` here,
which helps) and grants the model full access to inference compute.

Safe-use rules enforced at construction time:

* The **default pinned fork** (``CT2534/PP-DocLayout_plus-L`` at a fixed
  revision) is always allowed.
* A **local directory path** (any path starting with ``/``, ``.``, ``~``,
  or a Windows drive letter) is allowed with no extra flags.  Pass
  ``local_files_only=True`` to guarantee no network access.
* A **remote custom repo ID** (an ``owner/repo`` string not starting with a
  path-separator or drive letter) requires the caller to explicitly pass
  ``trust_remote_checkpoint=True``.  This is intentional friction: callers
  must acknowledge the trust boundary.

"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, Any, cast

import numpy as np
import torch
from PIL import Image
from transformers import RTDetrForObjectDetection, RTDetrImageProcessor

from pdomain_book_tools.layout._mappings import PP_DOCLAYOUT_TO_PGDP
from pdomain_book_tools.layout.types import LayoutRegion, PageLayout, RegionType

if TYPE_CHECKING:
    from pathlib import Path

logger = getLogger(__name__)


def _clip_box_to_bounds(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    img_width: int,
    img_height: int,
) -> tuple[float, float, float, float]:
    """Clip a model-predicted box to the image pixel frame.

    RT-DETR (and similar) can emit coordinates outside the image boundary when
    the predicted box partially extends beyond the edge. ``LayoutRegion`` already
    clamps negative coordinates to 0, but it does **not** clamp R/B to the image
    dimensions — that requires knowledge of the image size, which the adapter
    holds.

    Parameters
    ----------
    x1, y1:
        Top-left corner of the predicted box (may be negative).
    x2, y2:
        Bottom-right corner of the predicted box (may exceed image bounds).
    img_width, img_height:
        Pixel dimensions of the source image.

    Returns
    -------
    tuple[float, float, float, float]
        Clipped ``(x1, y1, x2, y2)`` with each coordinate in the valid range.
        If the clipped box is degenerate (x1 >= x2 or y1 >= y2) the caller
        should drop it.
    """
    x1 = max(0.0, x1)
    y1 = max(0.0, y1)
    x2 = min(float(img_width), x2)
    y2 = min(float(img_height), y2)
    return x1, y1, x2, y2


def _is_local_path(path: str) -> bool:
    """Return True if *path* looks like a local filesystem path.

    Local paths start with ``/`` (Unix absolute), ``.`` (relative), ``~``
    (home-dir expansion), or a Windows drive letter (``C:\\``).  Anything
    else is treated as a Hugging Face repo ID (``owner/repo``).
    """
    if path.startswith(("/", ".", "~")):
        return True
    # Windows drive letter: "C:\..." or "C:/..."
    if len(path) >= 3 and path[1] == ":" and path[2] in ("\\/"):  # noqa: SIM103
        return True
    return False


_ADAPTER_KEY = "pp-doclayout-plus-l"

# Repository hosting the weights. We ship a fork (Apache-2.0; identical bytes
# to PaddlePaddle/PP-DocLayout_plus-L_safetensors at the time of pinning) so a
# rename or deletion upstream cannot break installs. The Makefile target
# `layout-fork-update` re-syncs this fork from upstream and prints the new
# SHA to pin below.
_DEFAULT_REPO = "CT2534/PP-DocLayout_plus-L"
_DEFAULT_REVISION = "32d3ea36944213ce46f157e9255852620e30eeca"


class PPDocLayoutPlusLDetector:
    """Adapter around PP-DocLayout_plus-L.

    The model + processor are loaded once at construction and reused across
    pages (see :func:`pdomain_book_tools.layout.registry.get_detector` for the
    memoisation layer). On a fresh install, the first call downloads ~132 MB
    to ``$HF_HOME``; subsequent calls are local.

    The default repo is a pinned fork (``CT2534/PP-DocLayout_plus-L``); the
    revision is also pinned so installs are reproducible and immune to
    upstream removal. Override either via ``checkpoint_path`` (which can be
    a local directory or a different HF repo id).
    """

    HF_REPO: str = _DEFAULT_REPO
    HF_REVISION: str = _DEFAULT_REVISION
    KEY: str = _ADAPTER_KEY

    _processor: RTDetrImageProcessor
    _model: RTDetrForObjectDetection
    _device: str
    _conf: float

    def __init__(
        self,
        device: str = "cpu",
        confidence: float = 0.5,
        checkpoint_path: str | None = None,
        revision: str | None = None,
        *,
        local_files_only: bool = False,
        trust_remote_checkpoint: bool = False,
    ) -> None:
        """Initialise the PP-DocLayout_plus-L detector.

        Parameters
        ----------
        device:
            Torch device string (``"cpu"``, ``"cuda"``, etc.).
        confidence:
            Minimum detection confidence threshold (0-1).
        checkpoint_path:
            Override the default pinned HF fork.  May be a local directory
            path or a Hugging Face repo ID.

            **Trust boundary:** if this is a remote HF repo ID (not a local
            path), you must also pass ``trust_remote_checkpoint=True`` to
            acknowledge that you are loading weights from an external source.
            See the module docstring for the full security rationale.
        revision:
            Git revision (branch, tag, or SHA) to load from the HF repo.
            Ignored for local directory checkpoints.
        local_files_only:
            When ``True``, pass ``local_files_only=True`` to
            ``from_pretrained``.  This prevents any network access and raises
            ``OSError`` if the weights are not already cached.  Useful in
            air-gapped or high-security environments.
        trust_remote_checkpoint:
            Must be ``True`` when ``checkpoint_path`` is a remote HF repo ID
            (not a local path).  This is explicit opt-in friction: callers
            must acknowledge that they are trusting an external model source.
            Has no effect for local paths or the built-in default fork.
        """
        # ── trust-boundary enforcement ───────────────────────────────────────
        if (
            checkpoint_path is not None
            and not _is_local_path(checkpoint_path)
            and not trust_remote_checkpoint
        ):
            raise ValueError(
                f"checkpoint_path={checkpoint_path!r} looks like a remote "
                "Hugging Face repo ID, which is an untrusted model boundary. "
                "Pass trust_remote_checkpoint=True to explicitly opt in to "
                "loading from this source.  See the module docstring for the "
                "security rationale."
            )
        # ─────────────────────────────────────────────────────────────────────

        repo = checkpoint_path or self.HF_REPO
        # When the user supplies their own ``checkpoint_path``, don't force
        # our pinned revision onto it.
        rev = (
            revision
            if revision is not None
            else (None if checkpoint_path is not None else self.HF_REVISION)
        )
        logger.info(
            "Loading PP-DocLayout_plus-L from %s%s on %s",
            repo,
            f"@{rev}" if rev else "",
            device,
        )
        load_kwargs: dict[str, Any] = {}
        if rev:
            load_kwargs["revision"] = rev
        if local_files_only:
            load_kwargs["local_files_only"] = True
        processor_cls = cast("Any", RTDetrImageProcessor)
        model_cls = cast("Any", RTDetrForObjectDetection)
        self._processor = processor_cls.from_pretrained(repo, **load_kwargs)
        _loaded_model = model_cls.from_pretrained(repo, **load_kwargs)
        self._model = cast("RTDetrForObjectDetection", _loaded_model.to(device))
        _ = self._model.eval()
        self._device = device
        self._conf = float(confidence)

    @torch.inference_mode()
    def detect(self, source: str | Path | np.ndarray) -> PageLayout:
        img = self._to_pil(source)
        inputs = cast("Any", self._processor(images=img, return_tensors="pt")).to(
            self._device
        )
        outputs: Any = self._model(**inputs)
        target = torch.tensor([img.size[::-1]]).to(self._device)
        processor = cast("Any", self._processor)
        raw_results = cast(
            "list[dict[str, torch.Tensor]]",
            processor.post_process_object_detection(
                outputs,
                target_sizes=target,
                threshold=self._conf,
            ),
        )
        results = raw_results[0]
        regions: list[LayoutRegion] = []
        id2label = cast("dict[int, str]", self._model.config.id2label)
        for score, label, box in zip(
            results["scores"], results["labels"], results["boxes"], strict=False
        ):
            raw_label = id2label[int(label.item())]
            mapped = PP_DOCLAYOUT_TO_PGDP.get(raw_label)
            if mapped is None:
                continue
            try:
                region_type = RegionType(mapped)
            except ValueError:
                logger.debug(
                    "Mapped label %r → %r is not a known RegionType; dropping",
                    raw_label,
                    mapped,
                )
                continue
            coords_any = cast("Any", box.detach().cpu())
            coords = cast("list[float]", coords_any.tolist())
            x1, y1, x2, y2 = coords
            x1, y1, x2, y2 = _clip_box_to_bounds(
                x1, y1, x2, y2, img_width=int(img.width), img_height=int(img.height)
            )
            # Drop degenerate boxes that became zero-area after clipping.
            if x1 >= x2 or y1 >= y2:
                logger.debug(
                    "Dropping degenerate box after clipping: (%s, %s, %s, %s)",
                    x1,
                    y1,
                    x2,
                    y2,
                )
                continue
            regions.append(
                LayoutRegion(
                    type=region_type,
                    L=round(x1),
                    R=round(x2),
                    T=round(y1),
                    B=round(y2),
                    confidence=float(score.item()),
                    raw_label=raw_label,
                )
            )

        return PageLayout(
            regions=regions,
            image_width=int(img.width),
            image_height=int(img.height),
            detector=self.KEY,
            inference_ms=0,  # filled by the registry's timing wrapper
        )

    @staticmethod
    def _to_pil(source: str | Path | np.ndarray) -> Image.Image:
        if isinstance(source, np.ndarray):
            arr = source
            if arr.ndim == 2:
                return Image.fromarray(arr).convert("RGB")
            # Assume cv2 BGR → convert to RGB for PIL.
            return Image.fromarray(arr[:, :, ::-1].copy()).convert("RGB")
        return Image.open(source).convert("RGB")
