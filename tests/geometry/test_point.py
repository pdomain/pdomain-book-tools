import pytest
from pd_book_tools.geometry.point import Point
from shapely.geometry import Point as ShapelyPoint  # type: ignore

# Construction & basic access -------------------------------------------------

def test_direct_construction_and_to_x_y():
    p = Point(0.5, 0.5)
    assert p.to_x_y() == (0.5, 0.5)


def test_numeric_validation():
    with pytest.raises(ValueError):
        Point("1", 2)  # type: ignore
    with pytest.raises(ValueError):
        Point(1, "2")  # type: ignore

# Scaling / normalization -----------------------------------------------------

def test_scale_happy_path():
    p = Point(0.5, 0.5)
    assert p.scale(200, 100) == Point(100, 50)


def test_scale_invalid_out_of_range():
    with pytest.raises(ValueError):
        Point(-0.1, 0.2).scale(100, 200)
    with pytest.raises(ValueError):
        Point(0.2, 1.1).scale(50, 60)


def test_scale_boundary_values():
    assert Point(0.0, 0.0).scale(100, 200) == Point(0, 0)
    assert Point(1.0, 1.0).scale(100, 200) == Point(100, 200)


def test_normalize_with_ints():
    p = Point(10, 20)
    n = p.normalize(100, 200)
    assert pytest.approx(n.x) == 0.1
    assert pytest.approx(n.y) == 0.1


def test_normalize_with_non_ints_raises():
    with pytest.raises(ValueError):
        Point(10.5, 20).normalize(100, 200)
    with pytest.raises(ValueError):
        Point(10, 20.1).normalize(100, 200)

# Comparison / helpers -------------------------------------------------------

def test_is_larger_than():
    p1 = Point(0.6, 0.6)
    p2 = Point(0.5, 0.5)
    assert p1.is_larger_than(p2)
    assert not p2.is_larger_than(p1)


def test_distance_to():
    a = Point(0, 0)
    b = Point(3, 4)
    assert a.distance_to(b) == pytest.approx(5.0)
    # symmetry
    assert b.distance_to(a) == pytest.approx(5.0)

# Serialization --------------------------------------------------------------

def test_to_dict_round_trip():
    p = Point(0.5, 0.5)
    d = p.to_dict()
    assert d == {"x": 0.5, "y": 0.5}
    p2 = Point(d["x"], d["y"])
    assert p2 == p

# Shapely integration --------------------------------------------------------

def test_point_wraps_shapely():
    p = Point(1, 2)
    sp = p.as_shapely()
    assert isinstance(sp, ShapelyPoint)
    assert (sp.x, sp.y) == (1, 2)


def test_shapely_round_trip():
    sp = ShapelyPoint(3.3, 4.4)  # type: ignore
    p = Point(sp.x, sp.y)
    assert p.x == pytest.approx(3.3)
    assert p.y == pytest.approx(4.4)
    sp2 = p.as_shapely()  # type: ignore
    assert sp2.x == pytest.approx(3.3)
    assert sp2.y == pytest.approx(4.4)

