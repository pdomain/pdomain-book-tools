import pytest
from pd_book_tools.geometry.point import Point

# Try to import shapely, but don't fail if not installed
try:
    from shapely.geometry import Point as ShapelyPoint

    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False


def test_from_float_points():
    point = Point.from_float_points([0.5, 0.5])
    assert point.x == 0.5
    assert point.y == 0.5


def test_to_points():
    point = Point(0.5, 0.5)
    assert point.to_points() == (0.5, 0.5)


def test_scale():
    point = Point(0.5, 0.5)
    assert point.scale(200, 100) == (100, 50)


def test_is_larger_than():
    point1 = Point(0.6, 0.6)
    point2 = Point(0.5, 0.5)
    assert point1.is_larger_than(point2)
    assert not point2.is_larger_than(point1)


def test_to_dict():
    point = Point(0.5, 0.5)
    assert point.to_dict() == {"x": 0.5, "y": 0.5}


def test_from_dict():
    point_dict = {"x": 0.5, "y": 0.5}
    point = Point.from_dict(point_dict)
    assert point.x == 0.5
    assert point.y == 0.5


def test_shapely_not_available(monkeypatch):

    monkeypatch.setattr(Point, "is_shapely_available", lambda: False)

    with pytest.raises(ImportError):
        Point._fail_if_shapely_not_available()

    with pytest.raises(ImportError):
        Point.from_shapely(Point(0, 0))

    point = Point(0, 0)

    with pytest.raises(ImportError):
        point.as_shapely()


def test_shapely_methods():
    if not SHAPELY_AVAILABLE:
        pytest.skip(
            "Shapely is required for this test. Install it with 'pip install shapely'."
        )

    point = Point(0.5, 0.5)
    shapely_point = point.as_shapely()
    assert shapely_point.x == 0.5
    assert shapely_point.y == 0.5

    point2 = Point.from_shapely(ShapelyPoint(0.5, 0.5))
    assert point2.x == 0.5
    assert point2.y == 0.5
