import pytest

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.geometry.point import Point
from shapely import Polygon

# Try to import shapely, but don't fail if not installed
try:
    from shapely.geometry import box

    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False


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
    bbox1 = BoundingBox(Point(0, 0), Point(1, 1))
    bbox2 = BoundingBox(Point(0.5, 0.5), Point(1.5, 1.5))
    assert bbox1.intersects(bbox2)
    assert bbox2.intersects(bbox1)


def test_bounding_box_intersection():
    bbox1 = BoundingBox(Point(0, 0), Point(1, 1))
    bbox2 = BoundingBox(Point(0.5, 0.5), Point(1.5, 1.5))
    intersection = bbox1.intersection(bbox2)
    assert intersection
    assert intersection.top_left
    assert intersection.bottom_right
    assert intersection.top_left == Point(0.5, 0.5)
    assert intersection.bottom_right == Point(1, 1)


def test_bounding_box_union():
    bbox1 = BoundingBox(Point(0, 0), Point(1, 1))
    bbox2 = BoundingBox(Point(0.5, 0.5), Point(1.5, 1.5))
    union_bbox = BoundingBox.union([bbox1, bbox2])
    assert union_bbox.top_left == Point(0, 0)
    assert union_bbox.bottom_right == Point(1.5, 1.5)


def test_bounding_box_to_dict():
    bbox = BoundingBox(Point(0, 0), Point(1, 1))
    bbox_dict = bbox.to_dict()
    assert bbox_dict == {
        "top_left": {"x": 0, "y": 0},
        "bottom_right": {"x": 1, "y": 1},
    }


def test_bounding_box_from_dict():
    bbox_dict = {
        "top_left": {"x": 0, "y": 0},
        "bottom_right": {"x": 1, "y": 1},
    }
    bbox = BoundingBox.from_dict(bbox_dict)
    assert bbox.top_left == Point(0, 0)
    assert bbox.bottom_right == Point(1, 1)


def test_bounding_box_shapely_not_available(monkeypatch):
    monkeypatch.setattr(BoundingBox, "is_shapely_available", lambda: False)

    with pytest.raises(ImportError):
        BoundingBox._fail_if_shapely_not_available()

    with pytest.raises(ImportError):
        BoundingBox.from_shapely(Polygon(shell=[(0, 0), (1, 0), (1, 1), (0, 1)]))

    bbox = BoundingBox(Point(0, 0), Point(1, 1))

    with pytest.raises(ImportError):
        bbox.as_shapely()


def test_bounding_box_from_shapely():
    if not SHAPELY_AVAILABLE:
        raise ImportError(
            "Shapely is required for this test. Install it to the environment."
        )
    shapely_box = box(0, 0, 1, 1)  # type: ignore
    bbox = BoundingBox.from_shapely(shapely_box)
    assert bbox.top_left == Point(0, 0)
    assert bbox.bottom_right == Point(1, 1)


def test_bounding_box_as_shapely():
    if not SHAPELY_AVAILABLE:
        raise ImportError(
            "Shapely is required for this test. Install it to the environment."
        )
    bbox = BoundingBox(Point(0, 0), Point(1, 1))
    shapely_box = bbox.as_shapely()
    assert shapely_box
    assert shapely_box.bounds == (0, 0, 1, 1)
