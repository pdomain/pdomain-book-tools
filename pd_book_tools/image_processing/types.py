"""Backend-neutral types shared by cv2_processing and cupy_processing.

These types must not depend on either backend implementation, so that
either backend can be imported without dragging the other in. Re-exports
from `cv2_processing.canvas` (and other backend modules that historically
defined these types) are preserved for backward compatibility — callers
that import e.g. `Alignment` from the cv2 module continue to work.
"""

from enum import Enum


class Alignment(Enum):
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"
    DEFAULT = "default"
