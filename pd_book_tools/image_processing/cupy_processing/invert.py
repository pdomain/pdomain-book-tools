# pyright: reportUnknownMemberType=false
# Configure logging
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ._cupy_compat import require_cupy

if TYPE_CHECKING:
    import numpy as np
    import numpy.typing as npt

    CuPyArray = npt.NDArray[np.generic]
else:
    CuPyArray = object

logger = logging.getLogger(__name__)


def invert_image(img: CuPyArray) -> CuPyArray:
    """Invert a uint8 CuPy image (255 - pixel value for each element)."""
    require_cupy()
    return 255 - img  # pyright: ignore[reportOperatorIssue]  # CuPy arithmetic on NDArray-like alias
