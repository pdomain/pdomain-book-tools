from pd_book_tools.geometry import BoundingBox, Point


def test_bounding_box_repr_format():
    """repr(BoundingBox) returns BoundingBox.from_ltrb(x0, y0, x1, y1) form."""
    bb = BoundingBox(Point(0, 0), Point(10, 10))
    assert repr(bb) == "BoundingBox.from_ltrb(0, 0, 10, 10)"


def test_bounding_box_repr_eval_safe():
    """eval(repr(bb)) == bb for bb constructed without is_normalized."""
    bb = BoundingBox(Point(0, 0), Point(10, 10))
    restored = eval(repr(bb))
    assert restored == bb


def test_point_repr():
    """repr(Point) returns Point(x, y) form."""
    assert repr(Point(3, 7)) == "Point(3, 7)"
    assert repr(Point(0.5, 0.5)) == "Point(0.5, 0.5)"
