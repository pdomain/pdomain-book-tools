from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import cv2
import numpy as np

TransformKind = Literal["identity", "affine", "homography", "grid", "rectified"]

# Grid inversion: seed from a coarse sample, then refine with Newton steps.
_GRID_SEED_CELLS = 128
_GRID_NEWTON_STEPS = 25
_GRID_CONVERGED_PX = 1e-3
_GRID_MIN_DETERMINANT = 1e-9
# A point further than this from every output pixel's source is off the page.
_GRID_MAX_RESIDUAL_PX = 0.5


def _is_cupy(arr: object) -> bool:
    """True if ``arr`` is a cupy ndarray, without importing cupy on CPU-only installs."""
    return arr is not None and type(arr).__module__.split(".")[0] == "cupy"


def _as_numpy(arr: np.ndarray) -> np.ndarray:
    """Return *arr* as a NumPy array, copying it off the GPU if it is a cupy array."""
    if _is_cupy(arr):
        import cupy as cp

        return cp.asnumpy(arr)
    return np.asarray(arr)


def _bilinear_with_gradient(
    field: np.ndarray, xy: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return *field* at the (N, 2) positions *xy*, with its d/dx and d/dy there."""
    h, w = field.shape[:2]
    col = np.minimum(xy[:, 0].astype(np.intp), w - 2)
    row = np.minimum(xy[:, 1].astype(np.intp), h - 2)
    u = xy[:, 0] - col
    v = xy[:, 1] - row
    f00 = field[row, col]
    f01 = field[row, col + 1]
    f10 = field[row + 1, col]
    f11 = field[row + 1, col + 1]
    value = (1 - v) * ((1 - u) * f00 + u * f01) + v * ((1 - u) * f10 + u * f11)
    d_dx = (1 - v) * (f01 - f00) + v * (f11 - f10)
    d_dy = (1 - u) * (f10 - f00) + u * (f11 - f01)
    return value, d_dx, d_dy


def _invert_grid_points(
    map_x: np.ndarray, map_y: np.ndarray, source_pts: np.ndarray
) -> np.ndarray:
    """Return the output position of each source point under dense backward maps.

    The maps give, for each output pixel, the source position it shows, so a
    source point needs the inverse: the output position whose maps land on it.
    Each point starts at the nearest of a coarse sample of the maps and is
    refined with Newton steps on the bilinear surface. A point that no output
    position reaches, because the warp moved it off the page, comes back as NaN.
    """
    h, w = map_x.shape[:2]
    if h < 2 or w < 2:
        raise ValueError("grid map_points needs maps of at least 2x2 pixels")
    fx = map_x.astype(np.float64)
    fy = map_y.astype(np.float64)
    source = source_pts.astype(np.float64)

    stride = max(1, max(h, w) // _GRID_SEED_CELLS)
    seed_x = fx[::stride, ::stride]
    seed_y = fy[::stride, ::stride]
    solved = np.empty_like(source)
    for i, (px, py) in enumerate(source):
        nearest = np.argmin((seed_x - px) ** 2 + (seed_y - py) ** 2)
        row, col = np.unravel_index(nearest, seed_x.shape)
        solved[i] = (float(col) * stride, float(row) * stride)

    max_xy = np.array([w - 1, h - 1], np.float64)
    for _ in range(_GRID_NEWTON_STEPS):
        x_at, dx_dx, dx_dy = _bilinear_with_gradient(fx, solved)
        y_at, dy_dx, dy_dy = _bilinear_with_gradient(fy, solved)
        err_x = x_at - source[:, 0]
        err_y = y_at - source[:, 1]
        if np.all(np.hypot(err_x, err_y) <= _GRID_CONVERGED_PX):
            break
        det = dx_dx * dy_dy - dx_dy * dy_dx
        usable = np.abs(det) > _GRID_MIN_DETERMINANT
        safe_det = np.where(usable, det, 1.0)
        step_x = np.where(usable, (dy_dy * err_x - dx_dy * err_y) / safe_det, 0.0)
        step_y = np.where(usable, (dx_dx * err_y - dy_dx * err_x) / safe_det, 0.0)
        solved = np.clip(solved - np.column_stack([step_x, step_y]), 0.0, max_xy)

    x_at, _, _ = _bilinear_with_gradient(fx, solved)
    y_at, _, _ = _bilinear_with_gradient(fy, solved)
    distance = np.hypot(x_at - source[:, 0], y_at - source[:, 1])
    # Written as "not within" so a NaN distance also counts as unreachable.
    solved[~(distance <= _GRID_MAX_RESIDUAL_PX)] = np.nan
    return solved.astype(np.float32)


@dataclass(frozen=True)
class GeometryTransform:
    """A page-geometry correction expressed as a reusable, (usually) invertible map.

    - affine/homography keep a `matrix` and invert exactly.
    - grid keeps dense backward maps (`map_x`/`map_y`) for cv2.remap.
    - rectified holds a precomputed output image from a black-box backend
      (non-invertible).
    """

    kind: TransformKind
    size: tuple[int, int]  # (height, width) of the target/output
    matrix: np.ndarray | None = None
    map_x: np.ndarray | None = None
    map_y: np.ndarray | None = None
    output: np.ndarray | None = None
    invertible: bool = True

    @classmethod
    def identity(cls, size: tuple[int, int]) -> GeometryTransform:
        """Return an identity (no-op) transform for the given (height, width) size."""
        return cls(kind="identity", size=size, invertible=True)

    @classmethod
    def affine(cls, matrix: np.ndarray, size: tuple[int, int]) -> GeometryTransform:
        """Return an affine transform (2x3 matrix) for the given (height, width) size."""
        return cls(
            kind="affine",
            size=size,
            matrix=np.asarray(matrix, np.float64),
            invertible=True,
        )

    @classmethod
    def grid(
        cls, map_x: np.ndarray, map_y: np.ndarray, size: tuple[int, int]
    ) -> GeometryTransform:
        """Return a dense backward-map (grid) transform for cv2.remap or cupy map_coordinates."""
        if _is_cupy(map_x):
            import cupy as cp

            return cls(
                kind="grid",
                size=size,
                map_x=cp.asarray(map_x, cp.float32),
                map_y=cp.asarray(map_y, cp.float32),
                invertible=False,
            )
        return cls(
            kind="grid",
            size=size,
            map_x=np.asarray(map_x, np.float32),
            map_y=np.asarray(map_y, np.float32),
            invertible=False,
        )

    @classmethod
    def rectified(cls, output: np.ndarray, size: tuple[int, int]) -> GeometryTransform:
        """Return a rectified transform holding a precomputed output image."""
        return cls(
            kind="rectified", size=size, output=np.asarray(output), invertible=False
        )

    def apply(self, image: np.ndarray) -> np.ndarray:
        """Apply this transform to *image* and return the result."""
        h, w = self.size
        if self.kind == "identity":
            return image.copy()
        if self.kind == "affine":
            if self.matrix is None:  # pragma: no cover
                raise ValueError("affine transform has no matrix")
            return cv2.warpAffine(
                image,
                self.matrix,
                (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE,
            )
        if self.kind == "homography":
            if self.matrix is None:  # pragma: no cover
                raise ValueError("homography transform has no matrix")
            return cv2.warpPerspective(
                image,
                self.matrix,
                (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE,
            )
        if self.kind == "grid":
            if self.map_x is None or self.map_y is None:  # pragma: no cover
                raise ValueError("grid transform has no maps")
            if _is_cupy(self.map_x):
                import importlib

                import cupy as cp

                _cupyx_ndimage = importlib.import_module("cupyx.scipy.ndimage")
                map_coordinates = _cupyx_ndimage.map_coordinates
                coords = cp.stack([self.map_y, self.map_x])  # (row, col) order
                src = image if _is_cupy(image) else cp.asarray(image)
                return map_coordinates(src, coords, order=3, mode="nearest")
            return cv2.remap(
                image,
                self.map_x,
                self.map_y,
                interpolation=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE,
            )
        if self.kind == "rectified":
            if self.output is None:  # pragma: no cover
                raise ValueError("rectified transform has no output")
            return self.output.copy()
        raise NotImplementedError(self.kind)

    def invert(self) -> GeometryTransform | None:
        """Return the inverse transform, or None if not invertible."""
        if not self.invertible:
            return None
        if self.kind == "identity":
            return self
        if self.kind == "affine":
            if self.matrix is None:  # pragma: no cover
                raise ValueError("affine transform has no matrix")
            full = np.vstack([self.matrix, np.array([[0.0, 0.0, 1.0]])])
            inv = np.linalg.inv(full)[:2, :]
            return GeometryTransform.affine(inv, self.size)
        if self.kind == "homography":
            if self.matrix is None:  # pragma: no cover
                raise ValueError("homography transform has no matrix")
            return GeometryTransform(
                kind="homography",
                size=self.size,
                matrix=np.linalg.inv(self.matrix),
                invertible=True,
            )
        return None

    def map_points(self, pts: np.ndarray) -> np.ndarray:
        """Map source *pts* (N, 2) to their output positions and return (N, 2).

        For a grid transform, a point the warp moved off the page comes back as
        NaN, so check the result with ``np.isnan``. A rectified transform has no
        point mapping and raises ``NotImplementedError``.
        """
        pts = np.asarray(pts, np.float32).reshape(-1, 1, 2)
        if self.kind == "affine":
            if self.matrix is None:  # pragma: no cover
                raise ValueError("affine transform has no matrix")
            return cv2.transform(pts, self.matrix).reshape(-1, 2)
        if self.kind == "homography":
            if self.matrix is None:  # pragma: no cover
                raise ValueError("homography transform has no matrix")
            return cv2.perspectiveTransform(pts, self.matrix).reshape(-1, 2)
        if self.kind == "identity":
            return pts.reshape(-1, 2)
        if self.kind == "grid":
            if self.map_x is None or self.map_y is None:  # pragma: no cover
                raise ValueError("grid transform has no maps")
            return _invert_grid_points(
                _as_numpy(self.map_x), _as_numpy(self.map_y), pts.reshape(-1, 2)
            )
        raise NotImplementedError(self.kind)
