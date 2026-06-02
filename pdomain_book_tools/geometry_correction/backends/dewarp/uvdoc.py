"""UVDoc dewarp backend: predicts a backward grid, applied via cv2.remap."""

from __future__ import annotations

from typing import TYPE_CHECKING

import cv2

from pdomain_book_tools.geometry_correction.protocols import DewarpResult
from pdomain_book_tools.geometry_correction.transforms import GeometryTransform

from ._uvdoc_model import grid_to_remap, resolve_model_path, run_uvdoc

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

    import numpy as np

    from pdomain_book_tools.geometry_correction.protocols import BBox, GutterEdge


class UVDocDewarp:
    """UVDoc (ONNX) dewarp: predicts a backward grid, applied via cv2.remap.

    ``runner`` is injectable for testing; in production it defaults to ONNX inference
    against the model at ``model_path`` / ``$PD_UVDOC_ONNX``.
    """

    name = "uvdoc"

    def __init__(
        self,
        *,
        model_path: str | Path | None = None,
        runner: Callable[[np.ndarray], np.ndarray] | None = None,
    ) -> None:
        """Initialise with an optional model path or injectable runner."""
        self._model_path = model_path
        self._runner = runner

    def _grid(self, image_rgb: np.ndarray) -> np.ndarray:
        if self._runner is not None:
            return self._runner(image_rgb)
        return run_uvdoc(image_rgb, resolve_model_path(self._model_path))

    def estimate(
        self,
        image: np.ndarray,
        *,
        gutter_edge: GutterEdge | None = None,
        text_lines: Sequence[BBox] | None = None,
    ) -> DewarpResult:
        """Estimate a dewarp correction grid and return a corrective transform."""
        rgb = image if image.ndim == 3 else cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        grid = self._grid(rgb)
        h, w = image.shape[:2]
        map_x, map_y = grid_to_remap(grid, (h, w))
        return DewarpResult(
            transform=GeometryTransform.grid(map_x, map_y, (h, w)),
            confidence=1.0,
            method=self.name,
        )
