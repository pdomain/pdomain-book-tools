from pdomain_book_tools.geometry import BoundingBox, Point


def test_bounding_box_repr_format():
    bb = BoundingBox(Point(0, 0), Point(10, 10))
    assert repr(bb) == "BoundingBox.from_ltrb(0, 0, 10, 10)"


def test_bounding_box_repr_eval_safe():
    bb = BoundingBox(Point(0, 0), Point(10, 10))
    restored = eval(repr(bb))  # noqa: S307  # test verifies repr() is eval-safe by design
    assert restored == bb


def test_point_repr():
    assert repr(Point(3, 7)) == "Point(3, 7)"
    assert repr(Point(0.5, 0.5)) == "Point(0.5, 0.5)"
