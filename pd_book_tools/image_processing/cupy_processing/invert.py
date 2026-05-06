# Configure logging
from __future__ import annotations

import logging

from ._cupy_compat import cp, require_cupy

logger = logging.getLogger(__name__)


def invert_image(img: cp.ndarray) -> cp.ndarray:
    require_cupy()
    return 255 - img
