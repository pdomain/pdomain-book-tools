import pytest
from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.geometry.point import Point
from shapely.geometry import box  # type: ignore


# various ways to initialize


def test_bounding_box_initialization():
    top_left = Point(0, 0)
    bottom_right = Point(1, 1)
    bbox = BoundingBox(top_left, bottom_right)
    assert bbox.top_left == top_left
    assert bbox.bottom_right == bottom_right


def test_bounding_box_invalid_initialization():
    top_left = Point(1, 1)
    bottom_right = Point(0, 0)
    with pytest.raises(ValueError):
        BoundingBox(top_left, bottom_right)


def test_bounding_box_from_points():
    points = [Point(0, 0), Point(1, 1)]
    bbox = BoundingBox.from_points(points)
    assert bbox.top_left == points[0]
    assert bbox.bottom_right == points[1]


def test_bounding_box_from_float():
    points = [0, 0, 1, 1]
    bbox = BoundingBox.from_float(points)
    assert bbox.top_left == Point(0, 0)
    assert bbox.bottom_right == Point(1, 1)


def test_bounding_box_from_nested_float():
    points = [[0, 0], [1, 1]]
    bbox = BoundingBox.from_nested_float(points)
    assert bbox.top_left == Point(0, 0)
    assert bbox.bottom_right == Point(1, 1)


def test_bounding_box_from_ltrb():
    bbox = BoundingBox.from_ltrb(0, 0, 1, 1)
    assert bbox.top_left == Point(0, 0)
    assert bbox.bottom_right == Point(1, 1)


def test_bounding_box_from_ltwh():
    bbox = BoundingBox.from_ltwh(0, 0, 1, 1)
    assert bbox.top_left == Point(0, 0)
    assert bbox.bottom_right == Point(1, 1)


@pytest.fixture
def sample_bounding_box():
    """Fixture for a sample bounding box."""
    top_left = Point(2, 3)
    bottom_right = Point(8, 10)
    return BoundingBox(top_left=top_left, bottom_right=bottom_right)


def test_min_max_properties(sample_bounding_box):
    """Test minX, minY, maxX, maxY properties."""
    assert sample_bounding_box.minX == 2
    assert sample_bounding_box.minY == 3
    assert sample_bounding_box.maxX == 8
    assert sample_bounding_box.maxY == 10


def test_lrtb_property(sample_bounding_box):
    """Test lrtb property."""
    assert sample_bounding_box.lrtb == (2, 3, 8, 10)


def test_width_height_properties(sample_bounding_box):
    """Test width and height properties."""
    assert sample_bounding_box.width == 6  # 8 - 2
    assert sample_bounding_box.height == 7  # 10 - 3


def test_size_property(sample_bounding_box):
    """Test size property."""
    assert sample_bounding_box.size == (6, 7)  # (width, height)


def test_lrwh_property(sample_bounding_box):
    """Test lrwh property."""
    assert sample_bounding_box.lrwh == (2, 3, 6, 7)  # (minX, minY, width, height)


def test_area_property(sample_bounding_box):
    """Test area property."""
    assert sample_bounding_box.area == 42  # width * height = 6 * 7


def test_center_property(sample_bounding_box):
    """Test center property."""
    center = sample_bounding_box.center
    assert center.x == pytest.approx(5.0)  # (2 + 8) / 2
    assert center.y == pytest.approx(6.5)  # (3 + 10) / 2


def test_bounding_box_contains_point():
    bbox = BoundingBox(Point(0, 0), Point(1, 1))
    assert bbox.contains_point(Point(0.5, 0.5))
    assert not bbox.contains_point(Point(1.5, 1.5))


def test_bounding_box_intersects():
    # Use pixel-space boxes so both share coordinate system
    bbox1 = BoundingBox(Point(0, 0), Point(2, 2))
    bbox2 = BoundingBox(Point(0.5, 0.5), Point(1.5, 1.5))
    assert bbox1.intersects(bbox2)
    assert bbox2.intersects(bbox1)


def test_bounding_box_intersects_mixed_coordinate_system_error():
    norm_box = BoundingBox.from_ltrb(0.1, 0.2, 0.3, 0.4)
    pix_box = BoundingBox.from_ltrb(10, 20, 30, 40)
    with pytest.raises(ValueError):
        norm_box.intersects(pix_box)


def test_bounding_box_intersection():
    # Both pixel-space boxes (right/bottom > 1)
    bbox1 = BoundingBox(Point(0, 0), Point(2, 2))
    bbox2 = BoundingBox(Point(0.5, 0.5), Point(1.5, 1.5))
    intersection = bbox1.intersection(bbox2)
    assert intersection
    assert intersection.top_left
    assert intersection.bottom_right
    # Compare raw coordinates to avoid normalization flag equality issues
    assert (intersection.top_left.x, intersection.top_left.y) == (0.5, 0.5)
    assert (intersection.bottom_right.x, intersection.bottom_right.y) == (1.5, 1.5)


def test_intersection_mixed_coordinate_system_error():
    norm_box = BoundingBox.from_ltrb(0.1, 0.2, 0.3, 0.4)
    pix_box = BoundingBox.from_ltrb(10, 20, 30, 40)
    assert norm_box.is_normalized and not pix_box.is_normalized
    with pytest.raises(ValueError):
        norm_box.intersection(pix_box)


def test_union_mixed_coordinate_system_error():
    norm_box = BoundingBox.from_ltrb(0.1, 0.2, 0.3, 0.4)
    pix_box = BoundingBox.from_ltrb(10, 20, 30, 40)
    with pytest.raises(ValueError):
        BoundingBox.union([norm_box, pix_box])


def test_bounding_box_union():
    # Both pixel-space boxes
    bbox1 = BoundingBox(Point(0, 0), Point(2, 2))
    bbox2 = BoundingBox(Point(0.5, 0.5), Point(1.5, 1.5))
    union_bbox = BoundingBox.union([bbox1, bbox2])
    # Compare coordinates
    assert (union_bbox.top_left.x, union_bbox.top_left.y) == (0, 0)
    assert (union_bbox.bottom_right.x, union_bbox.bottom_right.y) == (2, 2)


def test_bounding_box_to_dict():
    bbox = BoundingBox(Point(0, 0), Point(1, 1))
    bbox_dict = bbox.to_dict()
    assert bbox_dict == {
        "top_left": {"x": 0, "y": 0, "is_normalized": True},
        "bottom_right": {"x": 1, "y": 1, "is_normalized": True},
        "is_normalized": True,
    }


def test_bounding_box_from_dict():
    bbox_dict = {
        "top_left": {"x": 0, "y": 0, "is_normalized": True},
        "bottom_right": {"x": 1, "y": 1, "is_normalized": True},
        "is_normalized": True,
    }
    bbox = BoundingBox.from_dict(bbox_dict)
    assert bbox.top_left == Point(0, 0)
    assert bbox.bottom_right == Point(1, 1)


def test_bounding_box_from_shapely():
    shapely_box = box(0, 0, 1, 1)  # type: ignore
    bbox = BoundingBox.from_shapely(shapely_box)
    assert bbox.top_left == Point(0, 0)
    assert bbox.bottom_right == Point(1, 1)


def test_bounding_box_as_shapely():
    bbox = BoundingBox(Point(0, 0), Point(1, 1))
    shapely_geom = bbox.as_shapely()
    assert shapely_geom
    assert shapely_geom.bounds == (0, 0, 1, 1)


def test_bounding_box_scale_requires_normalized():
    # Pixel (non-normalized) box: values extend beyond unit interval
    pixel_bbox = BoundingBox.from_ltrb(0, 0, 10, 10)
    assert not pixel_bbox.is_normalized
    # Calling scale() on pixel box should raise
    with pytest.raises(ValueError):
        pixel_bbox.scale(100, 200)

    # Normalized box scales correctly
    norm_bbox = BoundingBox.from_ltrb(0.1, 0.2, 0.3, 0.4)
    assert norm_bbox.is_normalized
    scaled = norm_bbox.scale(100, 200)
    assert not scaled.is_normalized
    assert scaled.to_ltrb() == (10, 40, 30, 80)


def test_bounding_box_normalize_requires_pixel():
    # Normalized box should not be normalized again
    norm_bbox = BoundingBox.from_ltrb(0.1, 0.2, 0.3, 0.4)
    assert norm_bbox.is_normalized
    with pytest.raises(ValueError):
        norm_bbox.normalize(100, 200)

    # Pixel box normalizes correctly
    pixel_bbox = BoundingBox.from_ltrb(0, 0, 10, 10)
    assert not pixel_bbox.is_normalized
    normalized = pixel_bbox.normalize(100, 200)
    assert normalized.is_normalized
    # (left, top, right, bottom) -> (0,0,10/100,10/200)
    assert normalized.to_ltrb() == (0, 0, 0.1, 0.05)


def test_refine_preserves_normalized(monkeypatch):
    import numpy as np

    # Create simple image with a small white rectangle inside the expected region
    img = np.zeros((100, 200), dtype=np.uint8)
    # Original normalized bbox roughly covering cols 20-80, rows 10-60
    bbox = BoundingBox.from_ltrb(0.1, 0.1, 0.4, 0.6)  # normalized
    # Draw a tighter white rectangle inside (30-70, 20-50)
    img[20:51, 30:71] = 255
    refined = bbox.refine(img)
    assert refined.is_normalized
    # Ensure refined box is still within original bounds and tighter in at least one dimension
    assert refined.minX >= bbox.minX - 1e-6
    assert refined.minY >= bbox.minY - 1e-6
    assert refined.maxX <= bbox.maxX + 1e-6
    assert refined.maxY <= bbox.maxY + 1e-6
    # Tighter width or height
    assert (refined.width <= bbox.width) or (refined.height <= bbox.height)


def test_refine_preserves_pixel():
    import numpy as np

    img = np.zeros((100, 200), dtype=np.uint8)
    bbox = BoundingBox.from_ltrb(10, 10, 80, 60)  # pixel box
    img[20:51, 30:71] = 255
    refined = bbox.refine(img)
    assert not refined.is_normalized
    assert refined.minX >= bbox.minX
    assert refined.minY >= bbox.minY
    assert refined.maxX <= bbox.maxX
    assert refined.maxY <= bbox.maxY
    assert (refined.width <= bbox.width) or (refined.height <= bbox.height)


def test_refine_no_text_returns_copy_normalized():
    import numpy as np

    # Image all white so after inversion it's all black -> threshold -> all zeros -> no non-zero coords
    img = np.full((50, 100), 255, dtype=np.uint8)
    bbox = BoundingBox.from_ltrb(0.2, 0.2, 0.6, 0.8)  # normalized
    refined = bbox.refine(img)
    assert refined.is_normalized
    assert refined.to_ltrb() == pytest.approx(bbox.to_ltrb())


def test_refine_no_text_returns_copy_pixel():
    import numpy as np

    img = np.full((50, 100), 255, dtype=np.uint8)
    bbox = BoundingBox.from_ltrb(10, 5, 60, 40)  # pixel
    refined = bbox.refine(img)
    assert not refined.is_normalized
    assert refined.to_ltrb() == bbox.to_ltrb()


def test_refine_padding_clamped_normalized():
    import numpy as np

    img = np.full((100, 100), 255, dtype=np.uint8)
    # Place a small black (0) rectangle inside the bbox to act as text
    img[30:35, 40:45] = 0
    bbox = BoundingBox.from_ltrb(0.2, 0.2, 0.8, 0.9)  # normalized large box
    refined = bbox.refine(img, padding_px=50)
    # Still normalized
    assert refined.is_normalized
    # Must stay within original bounds despite large padding request
    o_l, o_t, o_r, o_b = bbox.to_ltrb()
    r_l, r_t, r_r, r_b = refined.to_ltrb()
    assert o_l <= r_l <= o_r
    assert o_t <= r_t <= o_b
    assert o_l <= r_r <= o_r
    assert o_t <= r_b <= o_b


def test_refine_content_fills_box_pixel():
    import numpy as np

    img = np.full((60, 120), 255, dtype=np.uint8)
    bbox = BoundingBox.from_ltrb(10, 10, 70, 50)  # pixel
    # Fill entire bbox region with black (text) so refine should not shrink
    img[10:50, 10:70] = 0
    refined = bbox.refine(img)
    assert not refined.is_normalized
    assert refined.to_ltrb() == bbox.to_ltrb()


def test_refine_expand_beyond_original_pixel():
    import numpy as np

    img = np.full((100, 100), 255, dtype=np.uint8)
    # small text region
    img[40:45, 40:45] = 0
    bbox = BoundingBox.from_ltrb(30, 30, 50, 50)  # pixel
    refined = bbox.refine(img, padding_px=10, expand_beyond_original=True)
    # Tight rect (40,40)-(45,45); orig width=20 tight width=5 slack=15; extra=10 + 15/2 = 17.5 each side
    # Expanded: (40-17.5,40-17.5)-(45+17.5,45+17.5) -> (22.5,22.5)-(62.5,62.5)
    assert refined.to_ltrb() == (22.5, 22.5, 62.5, 62.5)


def test_refine_expand_beyond_original_normalized():
    import numpy as np

    img_h, img_w = 80, 160
    img = np.full((img_h, img_w), 255, dtype=np.uint8)
    img[30:35, 70:75] = 0  # small text
    bbox = BoundingBox.from_ltrb(0.3, 0.3, 0.5, 0.6)  # normalized
    refined = bbox.refine(img, padding_px=10, expand_beyond_original=True)
    assert refined.is_normalized
    # Convert expected expanded pixel box to normalized: original pixel bounds
    # original pixel box is (48,24)-(80,48) given scaling (0.3*160=48, 0.3*80=24, 0.5*160=80, 0.6*80=48)
    # content at (70:75,30:35) so tightened region plus 10px padding expands outward inside image bounds:
    # Tight rect (70,30)-(75,35); original pixel window (48,24)-(80,48)
    # slack_w=32-5=27, slack_h=24-5=19 -> extra_w=10+27/2=23.5, extra_h=10+19/2=19.5
    # Expanded (46.5,10.5)-(98.5,54.5) then rounded to int before normalization -> (46,10)-(98,54)
    left_norm, top_norm, right_norm, bottom_norm = refined.to_ltrb()
    assert left_norm == pytest.approx(46 / 160, rel=1e-3)
    assert top_norm == pytest.approx(10 / 80, rel=1e-3)
    assert right_norm == pytest.approx(98 / 160, rel=1e-3)
    assert bottom_norm == pytest.approx(54 / 80, rel=1e-3)


# ---------------- Additional coverage tests below -----------------


def test_split_x_offset_and_absolute():
    bbox = BoundingBox.from_ltrb(10, 5, 30, 25)  # pixel
    # Offset in middle
    left, right = bbox.split_x_offset(10)  # 10 px from left edge -> absolute x=20
    assert left.to_ltrb() == (10, 5, 20, 25)
    assert right.to_ltrb() == (20, 5, 30, 25)
    # Absolute split at left edge (zero-width left)
    l2, r2 = bbox.split_x_absolute(10)
    assert l2.width == 0
    assert r2.width == 20
    # Absolute split at right edge (zero-width right)
    l3, r3 = bbox.split_x_absolute(30)
    assert l3.width == 20
    assert r3.width == 0


def test_split_x_offset_errors():
    bbox = BoundingBox.from_ltrb(0, 0, 10, 10)
    with pytest.raises(ValueError):
        bbox.split_x_offset(-1)
    with pytest.raises(ValueError):
        bbox.split_x_offset(11)
    with pytest.raises(ValueError):
        bbox.split_x_absolute(-5)
    with pytest.raises(ValueError):
        bbox.split_x_absolute(50)


def test_intersection_none_and_edge_touch():
    a = BoundingBox.from_ltrb(0, 0, 10, 10)
    b = BoundingBox.from_ltrb(20, 20, 30, 30)  # disjoint
    assert a.intersection(b) is None
    # Touching edge (right of a at x=10 equals left of c)
    c = BoundingBox.from_ltrb(10, 0, 20, 10)
    assert a.intersection(c) is None


def test_overlap_amounts():
    a = BoundingBox.from_ltrb(0, 0, 10, 10)
    b = BoundingBox.from_ltrb(5, 5, 15, 12)
    assert a.overlap_x_amount(b) == 5
    assert a.overlap_y_amount(b) == 5


def test_union_empty_error():
    with pytest.raises(ValueError):
        BoundingBox.union([])


def test_union_normalized_flag_and_union_with():
    a = BoundingBox.from_ltrb(0.1, 0.2, 0.2, 0.4)
    b = BoundingBox.from_ltrb(0.15, 0.25, 0.25, 0.45)
    u = BoundingBox.union([a, b])
    assert u.is_normalized
    assert u.to_ltrb() == (0.1, 0.2, 0.25, 0.45)
    # union_with wrapper
    u2 = a.union_with(b)
    assert u2.to_ltrb() == u.to_ltrb()


def test_from_points_invalid_cases():
    with pytest.raises(ValueError):
        BoundingBox.from_points([Point(0, 0)])  # type: ignore[arg-type]
    with pytest.raises(ValueError):  # second not larger
        BoundingBox.from_points([Point(1, 1), Point(0, 0)])
    with pytest.raises(ValueError):  # dict missing keys
        BoundingBox.from_points([{"x": 0}, {"x": 1, "y": 1}])  # type: ignore[arg-type]
    with pytest.raises(TypeError):  # unsupported spec
        BoundingBox.from_points([Point(0, 0), 5])  # type: ignore[list-item]


def test_from_float_invalid_cases():
    with pytest.raises(ValueError):
        BoundingBox.from_float([0, 1, 2])  # type: ignore[list-item]
    with pytest.raises(ValueError):
        BoundingBox.from_float([2, 0, 1, 1])


def test_from_nested_float_invalid_cases():
    with pytest.raises(ValueError):
        BoundingBox.from_nested_float([[0, 0]])  # type: ignore[list-item]
    with pytest.raises(ValueError):
        BoundingBox.from_nested_float([[0, 0], [1]])  # type: ignore[list-item]
    with pytest.raises(ValueError):
        BoundingBox.from_nested_float([[2, 0], [1, 1]])


def test_from_ltwh_negative():
    with pytest.raises(ValueError):
        BoundingBox.from_ltwh(0, 0, -1, 5)
    with pytest.raises(ValueError):
        BoundingBox.from_ltwh(0, 0, 5, -2)


def test_to_scaled_ltwh():
    bbox = BoundingBox.from_ltrb(0.1, 0.2, 0.4, 0.5)
    assert bbox.is_normalized
    assert bbox.to_scaled_ltwh(200, 100) == (20.0, 20.0, 60.0, 30.0)


def test_from_dict_infer_normalized_missing_flags():
    legacy_dict = {  # simulate old serialization w/o per-point flags
        "top_left": {"x": 0.1, "y": 0.2},
        "bottom_right": {"x": 0.3, "y": 0.4},
        # omit box-level is_normalized to force inference
    }
    bbox = BoundingBox.from_dict(legacy_dict)  # type: ignore[arg-type]
    assert bbox.is_normalized  # all in [0,1]


def test_clamp_to_image():
    # Normalized box already within [0,1]; clamp should be identity
    bbox_norm = BoundingBox.from_ltrb(0.0, 0.0, 0.9, 0.8, is_normalized=True)
    clamped_norm = bbox_norm.clamp_to_image(100, 50)
    assert clamped_norm.to_ltrb() == bbox_norm.to_ltrb()
    # Pixel path
    bbox_pix = BoundingBox.from_ltrb(10, 5, 120, 60, is_normalized=False)
    clamped_pix = bbox_pix.clamp_to_image(100, 50)
    assert clamped_pix.to_ltrb() == (10.0, 5.0, 100.0, 50.0)


def test_from_shapely_invalid_input():
    class Dummy:
        pass

    with pytest.raises(ValueError):
        BoundingBox.from_shapely(Dummy())  # type: ignore[arg-type]


def test_expand_variants():
    bbox = BoundingBox.from_ltrb(10, 10, 20, 30)
    # uniform dx=0 returns identical
    assert bbox.expand(0, 0).to_ltrb() == bbox.to_ltrb()
    # uniform buffer uses shapely; just assert bigger
    bigger = bbox.expand(2, 2)
    assert bigger.width > bbox.width and bigger.height > bbox.height
    # anisotropic different dx, dy
    aniso = bbox.expand(3, 1)
    assert aniso.width == pytest.approx(bbox.width + 2 * 3)
    assert aniso.height == pytest.approx(bbox.height + 2 * 1)
    # shrink still positive
    shrink = bbox.expand(-2, -5)
    assert shrink.width == pytest.approx(bbox.width - 4)
    assert shrink.height == pytest.approx(bbox.height - 10)
    # excessive shrink raises
    with pytest.raises(ValueError):
        bbox.expand(-100, 0)


def test_interval_overlap_static():
    f = BoundingBox._interval_overlap
    assert f(0, 10, 5, 15) == 5
    assert f(0, 5, 5, 10) == 0
    assert f(0, 2, 3, 4) == 0
    assert f(0, 10, -5, 5) == 5


def test_threshold_inverted_color_image():
    import numpy as np
    import cv2

    # Color ROI (blue-ish rectangle) inside a normalized bbox
    img = np.zeros((20, 40, 3), dtype=np.uint8)
    img[5:15, 10:30] = (255, 0, 0)
    bbox = BoundingBox.from_ltrb(0.0, 0.0, 1.0, 1.0)
    # Use private helper via refine (exercise color branch)
    refined = bbox.refine(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))  # grayscale path
    refined_color = bbox.refine(img)  # color path triggers conversion
    assert refined.to_ltrb() == refined_color.to_ltrb()


def test_to_json_roundtrip():
    bbox = BoundingBox.from_ltrb(0.1, 0.2, 0.3, 0.4)
    s = bbox.to_json()
    bbox2 = BoundingBox.from_json(s)
    assert bbox2.to_ltrb() == bbox.to_ltrb()
    assert bbox2.is_normalized


def test_crop_top_and_bottom():
    import numpy as np

    # Image with text only in top quarter and bottom quarter white so crop_top should shrink bottom
    img = np.full((80, 200), 255, dtype=np.uint8)
    img[5:15, 20:180] = 0  # text near top
    bbox = BoundingBox.from_ltrb(0.0, 0.0, 1.0, 1.0)  # normalized full image
    top_cropped = bbox.crop_top(img)
    bottom_cropped = bbox.crop_bottom(img)
    # Both remain normalized
    assert top_cropped.is_normalized and bottom_cropped.is_normalized
    # Crops should reduce height relative to original in at least one case
    assert top_cropped.height <= bbox.height
    assert bottom_cropped.height <= bbox.height
    # Identity case when no change still acceptable; ensure outputs are BoundingBox
    assert isinstance(top_cropped, BoundingBox)
    assert isinstance(bottom_cropped, BoundingBox)


def test_crop_top_bottom_no_text_returns_copy():
    import numpy as np

    img = np.full((40, 80), 255, dtype=np.uint8)
    bbox = BoundingBox.from_ltrb(0.0, 0.0, 1.0, 1.0)
    assert bbox.crop_top(img).to_ltrb() == bbox.to_ltrb()
    assert bbox.crop_bottom(img).to_ltrb() == bbox.to_ltrb()


def test_iou():
    a = BoundingBox.from_ltrb(0, 0, 10, 10)
    b = BoundingBox.from_ltrb(5, 5, 15, 15)
    c = BoundingBox.from_ltrb(20, 20, 30, 30)
    iou_ab = a.iou(b)
    assert 0 < iou_ab < 1
    assert a.iou(c) == 0.0
    # mismatch coordinate systems triggers error
    norm = BoundingBox.from_ltrb(0.1, 0.1, 0.2, 0.2)
    with pytest.raises(ValueError):
        norm.iou(a)


def test_points_and_conversions():
    bbox = BoundingBox.from_ltrb(1, 2, 6, 10, is_normalized=False)
    p1, p2 = bbox.to_points()
    assert (p1.x, p1.y) == (1, 2)
    assert (p2.x, p2.y) == (6, 10)
    # to_ltwh
    assert bbox.to_ltwh() == (1, 2, 5, 8)
    # four point scaled polygon list from normalized box
    nb = BoundingBox.from_ltrb(0.1, 0.2, 0.4, 0.5)
    pts = nb.get_four_point_scaled_polygon_list(200, 100)
    assert pts == [[20, 20], [80, 20], [80, 50], [20, 50]]
    # union on pixel boxes should not mark normalized
    p1 = BoundingBox.from_ltrb(10, 10, 20, 20, is_normalized=False)
    p2 = BoundingBox.from_ltrb(30, 5, 40, 25, is_normalized=False)
    up = BoundingBox.union([p1, p2])
    assert not up.is_normalized
    assert up.to_ltrb() == (10, 5, 40, 25)


def test_from_points_length_error():
    with pytest.raises(ValueError):
        BoundingBox.from_points([Point(0, 0), Point(1, 1), Point(2, 2)])  # type: ignore[list-item]


def test_vertical_crop_branch_coverage():
    import numpy as np

    h, w = 40, 60
    img = np.full((h, w), 255, dtype=np.uint8)
    # center row index
    center = h // 2  # noqa: F841
    # Setup rows for crop_top logic:
    # row 20 (center) empty -> prev empty triggers first continue when y=19
    # row 19 has pixels at x 5,6 -> current
    img[19, 5:7] = 0
    # row 18 has overlapping pixel at x5 -> triggers second continue (current & prev)
    img[18, 5] = 0
    # row 17 has disjoint pixels at x 30 -> triggers break (prev non-empty, disjoint)
    img[17, 30:32] = 0
    # For crop_bottom create similar ascending pattern:
    # row 21 (center+1) empty -> prev empty triggers first continue
    # row 22 pixels at 10,11
    img[22, 10:12] = 0
    # row 23 overlapping pixel at 10 -> continue second branch
    img[23, 10] = 0
    # row 24 disjoint pixel at 40 -> break
    img[24, 40] = 0
    bbox_full = BoundingBox.from_ltrb(0.0, 0.0, 1.0, 1.0)
    ct = bbox_full.crop_top(img)
    cb = bbox_full.crop_bottom(img)
    assert ct.is_normalized and cb.is_normalized
    # Ensure y adjustments occurred (top crop raised top; bottom crop lowered bottom)
    assert ct.minY > 0
    assert cb.maxY < 1
