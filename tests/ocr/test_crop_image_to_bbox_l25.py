"""L-25 regression: ``crop_image_to_bbox`` previously caught bare
``Exception`` and silently returned ``None``, hiding genuine bugs.
The fix narrows the catch to expected types
(ValueError / AttributeError / TypeError / IndexError); anything else
must propagate.
"""

from __future__ import annotations

import logging

import numpy as np
import pytest

from pdomain_book_tools.geometry.bounding_box import BoundingBox
from pdomain_book_tools.geometry.point import Point
from pdomain_book_tools.ocr.image_utilities import crop_image_to_bbox


class _BBoxStub:
    def __init__(self, exc: BaseException) -> None:
        self._exc = exc

    def crop_image(self, image: np.ndarray) -> None:
        raise self._exc


class _Element:
    def __init__(self, bbox: object) -> None:
        self.bounding_box = bbox


def test_unexpected_exception_propagates() -> None:
    """Real bugs (e.g. RuntimeError from a corrupted internal state)
    must NOT be swallowed."""
    page = np.zeros((100, 100, 3), dtype=np.uint8)
    el = _Element(_BBoxStub(RuntimeError("upstream invariant violated")))
    with pytest.raises(RuntimeError, match="upstream invariant violated"):
        crop_image_to_bbox(el, page, label="test")


def test_keyboard_interrupt_propagates() -> None:
    """KeyboardInterrupt is a BaseException (not Exception), but
    historically a bare 'except Exception' would already let it through.
    Pin the post-fix behavior so a future widening to BaseException
    catch is caught."""
    page = np.zeros((100, 100, 3), dtype=np.uint8)
    el = _Element(_BBoxStub(KeyboardInterrupt()))
    with pytest.raises(KeyboardInterrupt):
        crop_image_to_bbox(el, page, label="test")


@pytest.mark.parametrize(
    "exc_type",
    [ValueError, AttributeError, TypeError, IndexError],
)
def test_expected_exception_types_still_swallowed(
    caplog: pytest.LogCaptureFixture, exc_type: type[Exception]
) -> None:
    """Expected failure modes (bad coords, missing .shape, slicing) keep
    returning None and only debug-log."""
    page = np.zeros((100, 100, 3), dtype=np.uint8)
    el = _Element(_BBoxStub(exc_type("boom")))
    with caplog.at_level(
        logging.DEBUG, logger="pdomain_book_tools.ocr.image_utilities"
    ):
        result = crop_image_to_bbox(el, page, label="test")
    assert result is None
    assert any("Error cropping image for test" in rec.message for rec in caplog.records)


def test_happy_path_still_returns_array() -> None:
    """The narrowed catch must not change happy-path behavior."""
    page = np.full((100, 100, 3), 7, dtype=np.uint8)
    bbox = BoundingBox(
        Point(0.1, 0.1, is_normalized=True),
        Point(0.5, 0.5, is_normalized=True),
        is_normalized=True,
    )
    el = _Element(bbox)
    out = crop_image_to_bbox(el, page, label="ok")
    assert isinstance(out, np.ndarray)
    assert out.shape == (40, 40, 3)
    assert (out == 7).all()


def test_none_element_or_image_short_circuits_to_none() -> None:
    """Pre-try guards unaffected by the narrowed catch."""
    page = np.zeros((10, 10, 3), dtype=np.uint8)
    assert crop_image_to_bbox(None, page, label="x") is None
    bbox = BoundingBox(
        Point(0.1, 0.1, is_normalized=True),
        Point(0.5, 0.5, is_normalized=True),
        is_normalized=True,
    )
    assert crop_image_to_bbox(_Element(bbox), None, label="x") is None
    assert crop_image_to_bbox(_Element(None), page, label="x") is None
