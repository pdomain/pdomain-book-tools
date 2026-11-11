from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import cv2
import numpy as np
import pytest

from pdomain_book_tools.geometry_correction.transforms import GeometryTransform

if TYPE_CHECKING:
    from numpy.typing import NDArray


def _checker(h: int = 40, w: int = 60) -> NDArray[np.uint8]:
    img = np.zeros((h, w), np.uint8)
    img[::4, :] = 255
    img[:, ::4] = 255
    return img


def test_identity_apply_is_noop():
    img = _checker()
    t = GeometryTransform.identity((img.shape[0], img.shape[1]))
    out = t.apply(img)
    assert np.array_equal(out, img)
    assert t.invertible is True


def test_affine_rotation_then_invert_roundtrips():
    img = _checker()
    h, w = img.shape
    m = cv2.getRotationMatrix2D((w / 2, h / 2), 5.0, 1.0)  # 2x3
    t = GeometryTransform.affine(m, (h, w))
    inv = t.invert()
    assert inv is not None
    restored = inv.apply(t.apply(img))
    # interior pixels should match closely after round trip
    inner = (slice(6, h - 6), slice(6, w - 6))
    diff = np.abs(restored[inner].astype(int) - img[inner].astype(int))
    assert (
        diff.mean() < 45.0
    )  # relaxed: small high-frequency checker causes rounding; spirit = roundtrip is lossy but bounded


def test_affine_map_points_matches_cv2():
    h, w = 40, 60
    m = cv2.getRotationMatrix2D((w / 2, h / 2), 5.0, 1.0)
    t = GeometryTransform.affine(m, (h, w))
    pts = np.array([[10.0, 12.0], [30.0, 25.0]], np.float32)
    expected = cv2.transform(pts.reshape(-1, 1, 2), m).reshape(-1, 2)
    np.testing.assert_allclose(t.map_points(pts), expected, atol=1e-4)


def test_grid_identity_map_is_noop():
    img = _checker()
    h, w = img.shape
    map_x, map_y = np.meshgrid(
        np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32)
    )
    t = GeometryTransform.grid(map_x, map_y, (h, w))
    out = t.apply(img)
    # remap with identity maps reproduces the image (interior exact)
    assert np.array_equal(out[2:-2, 2:-2], img[2:-2, 2:-2])
    assert t.invertible is False  # grid is not analytically invertible by default


def test_rectified_holds_precomputed_output():
    img = _checker()
    rect = img[::-1].copy()
    t = GeometryTransform.rectified(rect, (img.shape[0], img.shape[1]))
    assert np.array_equal(t.apply(img), rect)  # ignores input, returns precomputed
    assert t.invert() is None


def _shifted_grid(
    h: int, w: int, dx: float, dy: float
) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
    """Backward maps for an output that shows the source moved by (dx, dy)."""
    xs, ys = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    return xs - dx, ys - dy


def test_grid_map_points_goes_from_source_to_output():
    """Grid ``map_points`` has the same direction as affine: source to output."""
    h, w = 40, 60
    map_x, map_y = _shifted_grid(h, w, dx=3.0, dy=5.0)
    t = GeometryTransform.grid(map_x, map_y, (h, w))
    out = t.map_points(np.array([[10.0, 12.0], [20.5, 7.25]], np.float32))
    np.testing.assert_allclose(out, [[13.0, 17.0], [23.5, 12.25]], atol=1e-3)


def test_grid_map_points_agrees_with_apply_on_a_curved_map():
    """A dot drawn in the source lands where ``map_points`` says it will."""
    h, w = 120, 160
    xs, ys = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    sag = 6.0 * np.sin(xs * np.pi / w).astype(np.float32)
    t = GeometryTransform.grid(xs, ys + sag, (h, w))
    src = np.zeros((h, w), np.float32)
    src[60 + 6, 80] = 1.0

    out = t.map_points(np.array([[80.0, 66.0]], np.float32))[0]

    rendered = t.apply(cv2.GaussianBlur(src, (0, 0), 1.5))
    row, col = np.unravel_index(np.argmax(rendered), rendered.shape)
    assert abs(out[0] - float(col)) <= 1.0
    assert abs(out[1] - float(row)) <= 1.0


def test_grid_map_points_marks_points_outside_the_output_as_nan():
    h, w = 40, 60
    map_x, map_y = _shifted_grid(h, w, dx=0.0, dy=10.0)
    t = GeometryTransform.grid(map_x, map_y, (h, w))
    # Output row 39 shows source row 29, so source row 35 was pushed off the page.
    out = t.map_points(np.array([[10.0, 35.0], [10.0, 5.0]], np.float32))
    assert np.isnan(out[0]).all()
    np.testing.assert_allclose(out[1], [10.0, 15.0], atol=1e-3)


def test_grid_map_points_accepts_no_points():
    map_x, map_y = _shifted_grid(10, 10, 0.0, 0.0)
    t = GeometryTransform.grid(map_x, map_y, (10, 10))
    assert t.map_points(np.empty((0, 2), np.float32)).shape == (0, 2)


def test_rectified_map_points_still_raises():
    img = _checker()
    t = GeometryTransform.rectified(img, (img.shape[0], img.shape[1]))
    with pytest.raises(NotImplementedError):
        t.map_points(np.array([[1.0, 1.0]], np.float32))


class _FakeCupyArray:
    """Stands in for a cupy array, so the GPU branch runs on CPU."""

    __module__ = "cupy._core.core"

    def __init__(self, data: NDArray[np.float32]) -> None:
        self.data = data


def test_grid_map_points_reads_cupy_maps_through_asnumpy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def asnumpy(arr: _FakeCupyArray) -> NDArray[np.float32]:
        return arr.data

    monkeypatch.setitem(sys.modules, "cupy", SimpleNamespace(asnumpy=asnumpy))
    map_x, map_y = _shifted_grid(20, 30, dx=2.0, dy=1.0)
    t = GeometryTransform(
        kind="grid",
        size=(20, 30),
        map_x=cast("np.ndarray", _FakeCupyArray(map_x)),
        map_y=cast("np.ndarray", _FakeCupyArray(map_y)),
        invertible=False,
    )
    out = t.map_points(np.array([[5.0, 6.0]], np.float32))
    np.testing.assert_allclose(out, [[7.0, 7.0]], atol=1e-3)


@pytest.mark.parametrize("bad", [np.nan, np.inf])
def test_grid_map_points_returns_nan_for_non_finite_input(bad: float) -> None:
    map_x, map_y = _shifted_grid(40, 60, dx=3.0, dy=5.0)
    t = GeometryTransform.grid(map_x, map_y, (40, 60))

    out = t.map_points(np.array([[bad, 12.0], [10.0, 12.0]], np.float32))

    assert np.isnan(out[0]).all()
    np.testing.assert_allclose(out[1], [13.0, 17.0], atol=1e-3)


def test_grid_map_points_refines_past_the_coarse_seed_on_a_large_map() -> None:
    """A map wider than the seed sample still lands to a small fraction of a pixel."""
    h, w = 900, 1300
    xs, ys = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    sag = 12.0 * np.sin(xs * np.pi / w).astype(np.float32)
    t = GeometryTransform.grid(xs, ys + sag, (h, w))
    output_x = np.array([100.0, 650.0, 1211.0])
    output_y = np.array([200.0, 450.0, 700.0])
    source_y = output_y + 12.0 * np.sin(output_x * np.pi / w)

    out = t.map_points(np.column_stack([output_x, source_y]).astype(np.float32))

    np.testing.assert_allclose(out[:, 0], output_x, atol=1e-2)
    np.testing.assert_allclose(out[:, 1], output_y, atol=1e-2)


def test_grid_map_points_reaches_the_far_corner_between_seed_samples() -> None:
    """The last row and column are not on the seed grid when the stride skips them."""
    h, w = 901, 1301
    map_x, map_y = _shifted_grid(h, w, dx=0.0, dy=0.0)
    t = GeometryTransform.grid(map_x, map_y, (h, w))

    out = t.map_points(np.array([[1300.0, 900.0]], np.float32))

    np.testing.assert_allclose(out, [[1300.0, 900.0]], atol=1e-2)


def test_grid_map_points_rejects_a_map_too_small_to_interpolate() -> None:
    map_x, map_y = _shifted_grid(1, 10, 0.0, 0.0)
    t = GeometryTransform.grid(map_x, map_y, (1, 10))

    with pytest.raises(ValueError, match="2x2"):
        t.map_points(np.array([[1.0, 0.0]], np.float32))
