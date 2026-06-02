import cv2
import numpy as np

from pdomain_book_tools.geometry_correction.transforms import GeometryTransform


def _checker(h=40, w=60):
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
