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
