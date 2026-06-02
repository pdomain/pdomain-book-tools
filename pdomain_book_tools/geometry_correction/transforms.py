from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import cv2
import numpy as np

TransformKind = Literal["identity", "affine", "homography", "grid", "rectified"]


def _is_cupy(arr: object) -> bool:
    """True if ``arr`` is a cupy ndarray, without importing cupy on CPU-only installs."""
    return arr is not None and type(arr).__module__.split(".")[0] == "cupy"


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
            import cupy as cp  # pyright: ignore[reportMissingImports]

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

                import cupy as cp  # pyright: ignore[reportMissingImports]

                _cupyx_ndimage = importlib.import_module("cupyx.scipy.ndimage")
                map_coordinates = _cupyx_ndimage.map_coordinates
                coords = cp.stack([self.map_y, self.map_x])  # (row, col) order
                src = image if _is_cupy(image) else cp.asarray(image)
                return map_coordinates(src, coords, order=3, mode="nearest")  # type: ignore[return-value]
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
        """Map *pts* (N, 2) through this transform and return (N, 2)."""
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
        raise NotImplementedError(self.kind)
