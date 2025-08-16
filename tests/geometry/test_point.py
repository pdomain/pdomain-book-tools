import pytest
from pd_book_tools.geometry.point import Point
from shapely.geometry import Point as ShapelyPoint  # type: ignore

# Construction & basic access -------------------------------------------------


def test_direct_construction_and_to_x_y():
    p = Point(0.5, 0.5)
    assert p.to_x_y() == (0.5, 0.5)


def test_numeric_validation():
    # Numeric strings now accepted
    p = Point("1", 2)  # type: ignore
    assert p.x == 1.0 or p.x == 1  # Depending on dataclass storage
    p2 = Point(1, "2")  # type: ignore
    assert p2.y == 2.0 or p2.y == 2
    # Non-numeric strings still rejected
    with pytest.raises(ValueError):
        Point("abc", 2)  # type: ignore
    with pytest.raises(ValueError):
        Point(1, "two")  # type: ignore


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


def test_ordering_lexicographic():
    a = Point(0.2, 0.9)
    b = Point(0.3, 0.1)
    c = Point(0.3, 0.5)
    # a < b because x smaller
    assert a < b
    # b < c because x equal, y smaller
    assert b < c
    # c > b
    assert c > b
    # equality requires both coords and normalization
    assert not (b == c)

def test_ordering_mismatch_normalization_raises():
    norm = Point(0.5, 0.4)              # normalized
    pix = Point(50, 40)                 # pixel
    with pytest.raises(TypeError):
        _ = norm < pix
    with pytest.raises(TypeError):
        _ = pix > norm


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
    assert d == {"x": 0.5, "y": 0.5, "is_normalized": True}
    # Legacy construction from dict fields
    p2 = Point(d["x"], d["y"], is_normalized=d["is_normalized"])
    assert p2 == p
    # New from_dict helper
    p3 = Point.from_dict(d)
    assert p3 == p


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
