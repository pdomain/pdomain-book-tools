import cv2
import numpy as np
import pytest

from pdomain_book_tools.geometry_correction import DewarpResult
from pdomain_book_tools.geometry_correction.backends.dewarp._uvdoc_model import (
    grid_to_remap,
)
from pdomain_book_tools.geometry_correction.backends.dewarp.uvdoc import UVDocDewarp


def test_identity_grid_yields_identity_maps():
    h, w, gh, gw = 20, 30, 5, 7
    # identity grid in [-1,1] over (gh, gw)
    ys = np.linspace(-1, 1, gh, dtype=np.float32)
    xs = np.linspace(-1, 1, gw, dtype=np.float32)
    gx, gy = np.meshgrid(xs, ys)
    grid = np.stack([gx, gy])[None]  # (1, 2, gh, gw)
    map_x, map_y = grid_to_remap(grid, (h, w))
    assert map_x.shape == (h, w)
    assert map_y.shape == (h, w)
    # corners map to image corners
    assert abs(map_x[0, 0] - 0) < 1.0
    assert abs(map_y[0, 0] - 0) < 1.0
    assert abs(map_x[-1, -1] - (w - 1)) < 1.0
    assert abs(map_y[-1, -1] - (h - 1)) < 1.0
    # applying identity maps to an image is ~no-op (use full-res grid for low error)
    # Low-res gh*gw->h*w upsample creates interpolation bands; use full-res grid here.
    hf, wf = 20, 30
    ysf = np.linspace(-1, 1, hf, dtype=np.float32)
    xsf = np.linspace(-1, 1, wf, dtype=np.float32)
    gxf, gyf = np.meshgrid(xsf, ysf)
    gridf = np.stack([gxf, gyf])[None]
    mx, my = grid_to_remap(gridf, (hf, wf))
    img = np.random.default_rng(0).integers(0, 255, (hf, wf), dtype=np.uint8)
    out = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    assert np.abs(out.astype(int) - img.astype(int)).mean() < 5.0


def _identity_grid(gh: int = 40, gw: int = 60) -> np.ndarray:
    """Build an identity grid in [-1,1] at (gh, gw) resolution."""
    ys = np.linspace(-1, 1, gh, dtype=np.float32)
    xs = np.linspace(-1, 1, gw, dtype=np.float32)
    gx, gy = np.meshgrid(xs, ys)
    return np.stack([gx, gy])[None]


def test_backend_builds_grid_transform_from_injected_runner():
    img = np.random.default_rng(1).integers(0, 255, (40, 60, 3), dtype=np.uint8)
    # Full-res identity grid to avoid coarse-upsample banding artifacts
    backend = UVDocDewarp(runner=lambda rgb: _identity_grid(40, 60))
    res = backend.estimate(img)
    assert isinstance(res, DewarpResult)
    assert res.transform.kind == "grid"
    assert res.transform.map_x is not None
    assert res.transform.map_x.shape == (40, 60)
    out = res.transform.apply(img)
    assert np.abs(out.astype(int) - img.astype(int)).mean() < 6.0  # identity ~ no-op


def test_missing_model_raises_helpful_error():
    backend = UVDocDewarp()  # no runner, no model env set
    with pytest.raises(FileNotFoundError):
        backend.estimate(np.zeros((20, 20, 3), np.uint8))
