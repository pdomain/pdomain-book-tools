"""UVDoc ONNX model utilities: grid-to-remap conversion and model loading."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, cast

import cv2
import numpy as np
import numpy.typing as npt

# UVDoc inference image size (W, H) — from upstream utils.IMG_SIZE = [488, 712]
UVDOC_INPUT_WH = (488, 712)
# Pre-exported ONNX produced via FahNos/UVDoc_onnx make_onnx.py (opset 11).
# Provided/hosted separately; path overridable for tests and ops.
UVDOC_MODEL_ENV = "PD_UVDOC_ONNX"


def grid_to_remap(
    grid: npt.NDArray[np.float32], size: tuple[int, int]
) -> tuple[npt.NDArray[np.float32], npt.NDArray[np.float32]]:
    """Convert a UVDoc grid (1,2,Gh,Gw) in [-1,1] to full-res cv2.remap maps."""
    h, w = size
    g = grid[0]  # (2, Gh, Gw): channel 0 = x, 1 = y
    gx = cast(
        "npt.NDArray[np.float32]",
        cv2.resize(g[0], (w, h), interpolation=cv2.INTER_LINEAR),
    )
    gy = cast(
        "npt.NDArray[np.float32]",
        cv2.resize(g[1], (w, h), interpolation=cv2.INTER_LINEAR),
    )
    map_x = ((gx + 1.0) * (w - 1) / 2.0).astype(np.float32)
    map_y = ((gy + 1.0) * (h - 1) / 2.0).astype(np.float32)
    return map_x, map_y


def resolve_model_path(explicit: str | os.PathLike[str] | None = None) -> Path:
    """Return the path to the UVDoc ONNX model, or raise FileNotFoundError."""
    path = explicit or os.environ.get(UVDOC_MODEL_ENV)
    if not path:
        raise FileNotFoundError(
            "UVDoc ONNX model not found. Set PD_UVDOC_ONNX or pass model_path. "
            "Produce it via FahNos/UVDoc_onnx make_onnx.py."
        )
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"UVDoc ONNX model not found at {p}")
    return p


def run_uvdoc(image_rgb: np.ndarray, model_path: Path) -> np.ndarray:
    """Run UVDoc ONNX, returning the grid (1,2,Gh,Gw)."""
    import onnxruntime as ort  # pyright: ignore[reportMissingImports]  # lazy: only when the extra is installed

    # onnxruntime ships no stub this repo can pin (heavy optional dep, not
    # covered by typings/); wrap the boundary once as Any rather than let
    # Unknown spread through every attribute access below.
    ort_any = cast("Any", ort)

    inp = cv2.resize(image_rgb.astype(np.float32) / 255.0, UVDOC_INPUT_WH)
    inp = inp.transpose(2, 0, 1)[None]  # (1,3,H,W)
    sess: Any = ort_any.InferenceSession(
        str(model_path), providers=["CPUExecutionProvider"]
    )
    out: Any = sess.run(None, {sess.get_inputs()[0].name: inp.astype(np.float32)})
    return np.asarray(out[0])  # point_positions2D
