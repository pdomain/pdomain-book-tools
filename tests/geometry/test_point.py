import pytest
from pd_book_tools.geometry.point import Point
from shapely.geometry import Point as ShapelyPoint  # type: ignore

# Construction & basic access -------------------------------------------------


def test_direct_construction_coords(point_factory):
    p = point_factory(0.5, 0.5)
    assert (p.x, p.y) == (0.5, 0.5)


def test_numeric_string_x(point_factory):
    p = point_factory("1", 2)  # type: ignore
    assert p.x in (1, 1.0)


def test_numeric_string_y(point_factory):
    p = point_factory(1, "2")  # type: ignore
    assert p.y in (2, 2.0)


def test_non_numeric_string_x_raises(point_factory):
    with pytest.raises(ValueError):
        point_factory("abc", 2)  # type: ignore


def test_non_numeric_string_y_raises(point_factory):
    with pytest.raises(ValueError):
        point_factory(1, "two")  # type: ignore


# Scaling / normalization -----------------------------------------------------


def test_scale_happy_path(point_factory):
    p = point_factory(0.5, 0.5)
    assert p.scale(200, 100) == Point(100, 50)


def test_scale_invalid_out_of_range_negative_x():
    with pytest.raises(ValueError):
        Point(-0.1, 0.2).scale(100, 200)


def test_scale_invalid_out_of_range_y_gt_one():
    with pytest.raises(ValueError):
        Point(0.2, 1.1).scale(50, 60)


def test_scale_boundary_zero(point_factory):
    assert point_factory(0.0, 0.0).scale(100, 200) == point_factory(0, 0, is_normalized=False)


def test_scale_boundary_one(point_factory):
    assert point_factory(1.0, 1.0).scale(100, 200) == point_factory(100, 200)


def test_scale_zero_zero_int(point_factory):
    # Explicit integer (0,0) behaves same as float form; inferred normalized
    p = point_factory(0, 0)
    scaled = p.scale(50, 80)
    assert scaled == point_factory(0, 0, is_normalized=False)


def test_scale_zero_zero_override_pixel_raises(point_factory):
    # Forcing pixel semantics on (0,0) should make scale invalid
    p = point_factory(0, 0, is_normalized=False)
    with pytest.raises(ValueError):
        p.scale(10, 20)


def test_scale_one_one_int(point_factory):
    p = point_factory(1, 1)
    scaled = p.scale(30, 40)
    assert scaled == point_factory(30, 40)


def test_scale_one_one_override_pixel_raises(point_factory):
    p = point_factory(1, 1, is_normalized=False)  # force pixel semantics
    with pytest.raises(ValueError):
        p.scale(30, 40)


def test_scale_edge_right(point_factory):
    p = point_factory(1, 0)
    scaled = p.scale(64, 128)
    assert scaled == point_factory(64, 0)


def test_scale_edge_top(point_factory):
    p = point_factory(0, 1)
    scaled = p.scale(64, 128)
    assert scaled == point_factory(0, 128)


def test_normalize_with_ints_x(point_factory):
    n = point_factory(10, 20).normalize(100, 200)
    assert pytest.approx(n.x) == 0.1


def test_normalize_with_ints_y(point_factory):
    n = point_factory(10, 20).normalize(100, 200)
    assert pytest.approx(n.y) == 0.1


def test_normalize_with_non_ints_raises_x():
    with pytest.raises(ValueError):
        Point(10.5, 20).normalize(100, 200)


def test_normalize_with_non_ints_raises_y():
    with pytest.raises(ValueError):
        Point(10, 20.1).normalize(100, 200)


def test_normalize_intlike_floats_x():
    n = Point(10.0, 20.0).normalize(100, 200)
    assert pytest.approx(n.x) == 0.1


def test_normalize_intlike_floats_y():
    n = Point(10.0, 20.0).normalize(100, 200)
    assert pytest.approx(n.y) == 0.1


# Comparison / helpers -------------------------------------------------------


def test_ordering_a_less_b(point_factory):
    a = point_factory(0.2, 0.9)
    b = point_factory(0.3, 0.1)
    assert a < b


def test_ordering_b_less_c(point_factory):
    b = point_factory(0.3, 0.1)
    c = point_factory(0.3, 0.5)
    assert b < c


def test_ordering_c_greater_b(point_factory):
    b = point_factory(0.3, 0.1)
    c = point_factory(0.3, 0.5)
    assert c > b


def test_ordering_b_not_equal_c(point_factory):
    b = point_factory(0.3, 0.1)
    c = point_factory(0.3, 0.5)
    assert not (b == c)

def test_ordering_mismatch_normalization_raises(point_factory):
    norm = point_factory(0.5, 0.4)
    pix = point_factory(50, 40)
    with pytest.raises(TypeError):
        _ = norm < pix
    with pytest.raises(TypeError):
        _ = pix > norm

def test_equality_mismatch_normalization_raises(point_factory):
    norm = point_factory(0.2, 0.3)
    pix = point_factory(20, 30)
    with pytest.raises(TypeError):
        _ = (norm == pix)


def test_distance_to_value(point_factory):
    a = point_factory(0, 0)
    b = point_factory(3, 4)
    assert a.distance_to(b) == pytest.approx(5.0)


def test_distance_to_symmetry(point_factory):
    a = point_factory(0, 0)
    b = point_factory(3, 4)
    assert b.distance_to(a) == pytest.approx(5.0)


# Serialization --------------------------------------------------------------


def test_to_dict_values(point_factory):
    p = point_factory(0.5, 0.5)
    d = p.to_dict()
    assert d == {"x": 0.5, "y": 0.5, "is_normalized": True}


def test_from_dict_round_trip(point_factory):
    p = point_factory(0.5, 0.5)
    d = p.to_dict()
    assert Point.from_dict(d) == p


def test_manual_constructor_round_trip(point_factory):
    p = point_factory(0.5, 0.5)
    d = p.to_dict()
    p2 = Point(d["x"], d["y"], is_normalized=d["is_normalized"])
    assert p2 == p


# Shapely integration --------------------------------------------------------


def test_point_wraps_shapely_type_and_coords(point_factory):
    p = point_factory(1, 2)
    sp = p.as_shapely()
    assert isinstance(sp, ShapelyPoint)
    assert (sp.x, sp.y) == (1, 2)


def test_shapely_round_trip_value_x(point_factory):
    sp = ShapelyPoint(3.3, 4.4)  # type: ignore
    p = point_factory(sp.x, sp.y)
    assert p.x == pytest.approx(3.3)


def test_shapely_round_trip_value_y(point_factory):
    sp = ShapelyPoint(3.3, 4.4)  # type: ignore
    p = point_factory(sp.x, sp.y)
    assert p.y == pytest.approx(4.4)


def test_shapely_round_trip_sp2_x(point_factory):
    sp = ShapelyPoint(3.3, 4.4)  # type: ignore
    p = point_factory(sp.x, sp.y)
    sp2 = p.as_shapely()  # type: ignore
    assert sp2.x == pytest.approx(3.3)


def test_shapely_round_trip_sp2_y(point_factory):
    sp = ShapelyPoint(3.3, 4.4)  # type: ignore
    p = point_factory(sp.x, sp.y)
    sp2 = p.as_shapely()  # type: ignore
    assert sp2.y == pytest.approx(4.4)


# Additional coverage for edge / branch paths ---------------------------------


def test_small_negative_within_eps_raises(point_factory):
    # Triggers inner negative check inside normalized range (line 57->58)
    with pytest.raises(ValueError):
        point_factory(-5e-10, 0.5)


def test_setter_x_out_of_range_on_normalized_raises(point_factory):
    p = point_factory(0.5, 0.5)
    with pytest.raises(AttributeError):
        p.x = 2  # immutability


def test_setter_y_out_of_range_on_normalized_raises(point_factory):
    p = point_factory(0.5, 0.5)
    with pytest.raises(AttributeError):
        p.y = 3


def test_setter_x_inside_unit_still_normalized(point_factory):
    p = point_factory(0.5, 0.5)
    p2 = Point.normalized(0.75, p.y)
    assert p2.is_normalized is True


def test_setter_y_inside_unit_still_normalized(point_factory):
    p = point_factory(0.5, 0.5)
    p2 = Point.normalized(p.x, 0.25)
    assert p2.is_normalized is True


def test_manual_is_normalized_override_initial_state(point_factory):
    p = point_factory(10, 20)
    assert p.is_normalized is False


def test_manual_is_normalized_override_after_setting(point_factory):
    p = point_factory(10, 20)
    with pytest.raises(AttributeError):
        p.is_normalized = True


def test_dunder_getattr_delegation_has_area(point_factory):
    p = point_factory(1, 2)
    assert hasattr(p, "area")


def test_dunder_getattr_delegation_area_value(point_factory):
    p = point_factory(1, 2)
    assert p.area == 0.0


def test_dunder_getattr_delegation_bounds(point_factory):
    p = point_factory(1, 2)
    assert p.bounds == (1.0, 2.0, 1.0, 2.0)


def test_comparison_gt_non_point_typeerror(point_factory):
    p = point_factory(0.2, 0.3)
    with pytest.raises(TypeError):
        _ = p > 5


def test_comparison_lt_non_point_typeerror(point_factory):
    p = point_factory(0.2, 0.3)
    with pytest.raises(TypeError):
        _ = p < 5


def test_comparison_ge_non_point_typeerror(point_factory):
    p = point_factory(0.2, 0.3)
    with pytest.raises(TypeError):
        _ = p >= 5


def test_comparison_le_non_point_typeerror(point_factory):
    p = point_factory(0.2, 0.3)
    with pytest.raises(TypeError):
        _ = p <= 5


def test_comparison_eq_non_point_false(point_factory):
    p = point_factory(0.2, 0.3)
    assert (p == 5) is False


def test_dunder_gt_returns_notimplemented(point_factory):
    p = point_factory(0.1, 0.1)
    assert p.__gt__(5) is NotImplemented


def test_dunder_lt_returns_notimplemented(point_factory):
    p = point_factory(0.1, 0.1)
    assert p.__lt__(5) is NotImplemented


def test_dunder_ge_returns_notimplemented(point_factory):
    p = point_factory(0.1, 0.1)
    assert p.__ge__(5) is NotImplemented


def test_dunder_le_returns_notimplemented(point_factory):
    p = point_factory(0.1, 0.1)
    assert p.__le__(5) is NotImplemented


def test_dunder_eq_returns_notimplemented(point_factory):
    p = point_factory(0.1, 0.1)
    # Equality returns NotImplemented; Python wrapper would then coerce to False
    assert p.__eq__(5) is NotImplemented


def test_comparison_ge_equal(point_factory):
    a = point_factory(0.4, 0.4)
    b = point_factory(0.4, 0.4)
    assert a >= b


def test_comparison_le_equal(point_factory):
    a = point_factory(0.4, 0.4)
    b = point_factory(0.4, 0.4)
    assert a <= b


def test_comparison_c_ge_a(point_factory):
    a = point_factory(0.4, 0.4)
    c = point_factory(0.4, 0.5)
    assert c >= a


def test_comparison_a_le_c(point_factory):
    a = point_factory(0.4, 0.4)
    c = point_factory(0.4, 0.5)
    assert a <= c


def test_comparison_ge_mismatch_typeerror(point_factory):
    norm = point_factory(0.2, 0.2)
    pix = point_factory(2, 2)
    with pytest.raises(TypeError):
        _ = norm >= pix


def test_comparison_le_mismatch_typeerror(point_factory):
    norm = point_factory(0.2, 0.2)
    pix = point_factory(2, 2)
    with pytest.raises(TypeError):
        _ = pix <= norm


def test_normalize_already_normalized_raises(point_factory):
    p = point_factory(0.6, 0.4)
    with pytest.raises(ValueError):
        p.normalize(100, 100)


def test_setters_do_not_auto_upgrade_pixel_point(point_factory):
    p = point_factory(5, 5)  # pixel
    assert p.is_normalized is False
    p2 = Point.pixel(0.25, 0.75)
    assert p2.is_normalized is False


def test_is_normalized_setter_rejects_out_of_range(point_factory):
    p = point_factory(5, 5)  # pixel
    with pytest.raises(AttributeError):
        p.is_normalized = True


def test_is_normalized_setter_accepts_in_range_after_mutation(point_factory):
    # start from pixel semantics
    p2 = Point.pixel(0.1, 0.2)
    # Still pixel semantics (immutable new object)
    assert p2.is_normalized is False
    # create a normalized instance explicitly
    p3 = Point.normalized(0.1, 0.2)
    assert p3.is_normalized is True


# Corner / boundary / rounding cases -----------------------------------------


def test_eps_boundary_still_normalized(point_factory):
    # Slightly over 1 within EPS should still be treated as normalized
    p = point_factory(1 + 5e-10, 1 - 5e-10)
    assert p.is_normalized is True


def test_eps_exceeded_becomes_pixel(point_factory):
    p = point_factory(1 + 2e-9, 0.5)
    assert p.is_normalized is False


def test_normalize_after_manual_pixel_override_origin(point_factory):
    p = point_factory(0, 0, is_normalized=False)
    n = p.normalize(100, 200)
    assert n.is_normalized is True
    assert (n.x, n.y) == (0.0, 0.0)


def test_constructor_rejects_invalid_forced_normalized(point_factory):
    with pytest.raises(ValueError):
        point_factory(5, 5, is_normalized=True)


def test_scale_requires_normalized_state(point_factory):
    p = point_factory(5, 5)  # pixel
    with pytest.raises(ValueError):
        p.scale(10, 10)


def test_scale_rounding_half_even_value(point_factory):
    p = point_factory(0.5, 0.5)
    scaled = p.scale(3, 3)
    assert (scaled.x, scaled.y) == (2, 2)


def test_scale_rounding_generic_value(point_factory):
    p = point_factory(1/3, 2/3)
    scaled = p.scale(3, 3)
    assert (scaled.x, scaled.y) == (1, 2)


def test_setter_moves_point_out_of_normalized_range_initial(point_factory):
    p = point_factory(0.9, 0.9)
    assert p.is_normalized is True


def test_setter_moves_point_out_of_normalized_range_after_raises(point_factory):
    p = point_factory(0.9, 0.9)
    with pytest.raises(AttributeError):
        p.x = 2


# Hashing --------------------------------------------------------------------

def test_hash_membership_normalized():
    p = Point.normalized(0.1, 0.2)
    s = {p}
    assert Point.normalized(0.1, 0.2) in s


def test_hash_dict_key_pixel():
    k = Point.pixel(5, 6)
    d = {k: "value"}
    assert d[Point.pixel(5, 6)] == "value"
