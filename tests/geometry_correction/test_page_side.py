import numpy as np

from pdomain_book_tools.geometry_correction import PageSide
from pdomain_book_tools.geometry_correction.backends.page_side.supplied import (
    SuppliedPageSide,
)


def test_passes_hint_through_with_gutter_edge():
    res = SuppliedPageSide().detect(np.zeros((10, 10), np.uint8), hint=PageSide.LEFT)
    assert res.side is PageSide.LEFT
    assert res.gutter_edge == "right"  # left page -> gutter on the right
    res2 = SuppliedPageSide().detect(np.zeros((10, 10), np.uint8), hint=PageSide.RIGHT)
    assert res2.gutter_edge == "left"


def test_no_hint_is_unknown_none_gutter():
    res = SuppliedPageSide().detect(np.zeros((10, 10), np.uint8))
    assert res.side is PageSide.UNKNOWN
    assert res.gutter_edge == "none"
