"""PP-DocLayout_plus-L adapter (RT-DETR via Hugging Face ``transformers``).

The model is loaded from
``PaddlePaddle/PP-DocLayout_plus-L_safetensors`` (Apache 2.0). A custom
fine-tuned checkpoint can be passed in via ``checkpoint_path`` — anything
that ``RTDetrForObjectDetection.from_pretrained`` accepts (a HF repo id or a
local directory).

Native labels are mapped to :class:`pd_book_tools.layout.types.RegionType`
via :data:`pd_book_tools.layout._mappings.PP_DOCLAYOUT_TO_PGDP`. Labels that
map to ``None`` are dropped.

"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, cast

import numpy as np
import torch
from PIL import Image
from transformers import RTDetrForObjectDetection, RTDetrImageProcessor

from pd_book_tools.layout._mappings import PP_DOCLAYOUT_TO_PGDP
from pd_book_tools.layout.types import LayoutRegion, PageLayout, RegionType

if TYPE_CHECKING:
    from pathlib import Path

logger = getLogger(__name__)


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
    pages (see :func:`pd_book_tools.layout.registry.get_detector` for the
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
    ) -> None:
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
        load_kwargs = {"revision": rev} if rev else {}
        self._processor = RTDetrImageProcessor.from_pretrained(repo, **load_kwargs)  # pyright: ignore[reportArgumentType]  # transformers stubs don't match **kwargs spread
        _loaded_model = RTDetrForObjectDetection.from_pretrained(repo, **load_kwargs)  # pyright: ignore[reportArgumentType]  # transformers stubs don't match **kwargs spread
        self._model = _loaded_model.to(device)  # pyright: ignore[reportArgumentType]  # from_pretrained stubs type result as str | RTDetrForObjectDetection; .to() is valid at runtime
        _ = self._model.eval()
        self._device = device
        self._conf = float(confidence)

    @torch.inference_mode()
    def detect(self, source: str | Path | np.ndarray) -> PageLayout:
        img = self._to_pil(source)
        inputs = self._processor(images=img, return_tensors="pt").to(self._device)
        outputs = self._model(**inputs)
        target = torch.tensor([img.size[::-1]]).to(self._device)  # pyright: ignore[reportPrivateImportUsage]  # torch.tensor is public API; stubs mark it private
        raw_results = self._processor.post_process_object_detection(
            outputs,
            target_sizes=target,  # pyright: ignore[reportArgumentType]  # transformers stubs require TensorType; torch.Tensor is accepted at runtime
            threshold=self._conf,
        )
        results = cast("list[dict[str, torch.Tensor]]", raw_results)[0]

        regions: list[LayoutRegion] = []
        id2label = self._model.config.id2label
        for score, label, box in zip(
            results["scores"], results["labels"], results["boxes"], strict=False
        ):
            raw_label = id2label[int(label.item())]  # pyright: ignore[reportOptionalSubscript]  # id2label is always populated for object detection models
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
            x1, y1, x2, y2 = (float(v) for v in box.detach().cpu().tolist())
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
