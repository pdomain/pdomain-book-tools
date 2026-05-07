"""Geometry primitives — :class:`BoundingBox` and :class:`Point`.

These are the canonical value types used throughout the rest of the
library. Both are re-exported from :mod:`pd_book_tools` itself.

Note: :class:`BoundingBox` currently exposes image-processing helper
methods (``refine``, ``crop_top``, ``crop_bottom``) that are thin
wrappers around the canonical free functions in
:mod:`pd_book_tools.geometry.image_ops`. The wrappers are preserved
for backward compatibility; new code should call the free functions
directly.
"""

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.geometry.point import Point

__all__ = ["BoundingBox", "Point"]
