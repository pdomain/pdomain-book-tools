"""Regression test for Python 3.11 compat: bounding_box.py must import cleanly
on Python < 3.12 (typing.override was added in 3.12; we fall back to
typing_extensions.override on older interpreters).

This test exercises the import path that triggered the ImportError in
pd-ocr-ops when it bumped to pd-book-tools v0.14.0 on Python 3.11.
"""

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.geometry.point import Point


def test_bounding_box_importable_on_all_python_versions():
    """BoundingBox can be imported and instantiated regardless of Python version."""
    bb = BoundingBox(Point(0.0, 0.0), Point(1.0, 1.0))
    assert bb.minX == 0.0
    assert bb.minY == 0.0
    assert bb.maxX == 1.0
    assert bb.maxY == 1.0


def test_bounding_box_repr_uses_override():
    """@override decorator on __repr__ must work on Python 3.11 and 3.12+."""
    bb = BoundingBox(Point(0.1, 0.2), Point(0.8, 0.9))
    assert repr(bb) == "BoundingBox.from_ltrb(0.1, 0.2, 0.8, 0.9)"
