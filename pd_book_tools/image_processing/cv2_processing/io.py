# Configure logging
import logging
import pathlib

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def read_image(src: pathlib.Path) -> np.ndarray:
    """Read an image file with cv2.imread, raising on failure.

    cv2.imread silently returns None for missing files, unsupported formats,
    permission errors, and truncated/corrupt images. Propagating that None
    leads to confusing AttributeErrors deep in callers (e.g.
    ``rescale_image`` doing ``img.shape[:2]``). Convert the silent failure
    into an explicit, path-naming exception so callers fail fast.

    Raises:
        FileNotFoundError: if ``src`` does not exist.
        ValueError: if the file exists but cv2.imread cannot decode it
            (unsupported format, corrupt, permission error).
    """
    resolved = str(src.resolve())
    if not pathlib.Path(resolved).exists():
        raise FileNotFoundError(f"read_image: file not found: {resolved}")
    img = cv2.imread(filename=resolved)
    if img is None:
        raise ValueError(
            f"read_image: cv2.imread failed to decode image at {resolved} "
            "(unsupported format, corrupt file, or permission error)"
        )
    return img


def write_jpg(img: np.ndarray, f: pathlib.Path, quality: int = 100) -> None:
    """Write a numpy BGR image to disk as a JPEG with the given quality."""
    fpathstr = str(f.resolve())
    cv2.imwrite(fpathstr, img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])


def write_png(img: np.ndarray, f: pathlib.Path) -> None:
    """Write a numpy BGR image to disk as a PNG with maximum compression."""
    fpathstr = str(f.resolve())
    cv2.imwrite(fpathstr, img, [int(cv2.IMWRITE_PNG_COMPRESSION), 9])
