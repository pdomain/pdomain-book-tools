from __future__ import annotations

# Configure logging
import logging
import pathlib

import cv2
import numpy as np
from PIL import Image

# Importing formats registers the pillow-heif / pillow-avif-plugin openers
# with Pillow, which read_image's fallback below relies on.
from pdomain_book_tools.image_processing import formats as _formats

logger = logging.getLogger(__name__)

# Reference the module so the import above is not flagged as unused by
# linters/type checkers; its purpose is the plugin-registration side effect
# that runs at import time, not any attribute access here.
_ = _formats


def _read_image_via_pillow(resolved: str) -> np.ndarray | None:
    """Fall back to Pillow for formats cv2 cannot decode (HEIF/AVIF).

    Pillow decodes to RGB; cv2's convention (and every writer/reader pair in
    this module) is BGR, so the channel order is reversed before returning.
    Returns ``None`` on any Pillow failure so the caller can raise a single,
    unified error naming the path.
    """
    try:
        with Image.open(resolved) as pil_img:
            rgb = np.array(pil_img.convert("RGB"))
    except (OSError, ValueError):
        # OSError covers PIL.UnidentifiedImageError (unrecognised/corrupt
        # data, missing HEIF/AVIF plugin) and truncated-file errors; ValueError
        # covers malformed images Pillow's decoders reject outright.
        return None
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def read_image(src: pathlib.Path) -> np.ndarray:
    """Read an image file, raising on failure.

    Tries ``cv2.imread`` first. cv2.imread silently returns None for
    missing files, unsupported formats, permission errors, and
    truncated/corrupt images. For formats cv2 cannot decode at all (HEIF,
    AVIF), falls back to Pillow via the ``pillow-heif`` / ``pillow-avif-plugin``
    openers registered by :mod:`pdomain_book_tools.image_processing.formats`.
    Propagating a silent None leads to confusing AttributeErrors deep in
    callers (e.g. ``rescale_image`` doing ``img.shape[:2]``); both paths
    convert failure into an explicit, path-naming exception so callers fail
    fast.

    Raises:
        FileNotFoundError: if ``src`` does not exist.
        ValueError: if the file exists but neither cv2.imread nor the
            Pillow fallback can decode it (unsupported format, corrupt
            file, or permission error).
    """
    resolved = str(src.resolve())
    if not pathlib.Path(resolved).exists():
        raise FileNotFoundError(f"read_image: file not found: {resolved}")
    img = cv2.imread(filename=resolved)
    if img is None:
        img = _read_image_via_pillow(resolved)
    if img is None:
        raise ValueError(
            f"read_image: failed to decode image at {resolved} "
            + "(unsupported format, corrupt file, or permission error)"
        )
    return img


def write_jpg(img: np.ndarray, f: pathlib.Path, quality: int = 100) -> None:
    """Write a numpy BGR image to disk as a JPEG with the given quality.

    Raises:
        ValueError: if cv2.imwrite reports failure (e.g. a full disk,
            a read-only directory, or a path whose parent directory does
            not exist). cv2.imwrite returns False rather than raising, so
            without this check the caller would be told the write
            succeeded when nothing was written to disk.
    """
    fpathstr = str(f.resolve())
    ok = cv2.imwrite(fpathstr, img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise ValueError(f"write_jpg: cv2.imwrite failed to write image to {fpathstr}")


def write_png(img: np.ndarray, f: pathlib.Path) -> None:
    """Write a numpy BGR image to disk as a PNG with maximum compression.

    Raises:
        ValueError: if cv2.imwrite reports failure (e.g. a full disk,
            a read-only directory, or a path whose parent directory does
            not exist). cv2.imwrite returns False rather than raising, so
            without this check the caller would be told the write
            succeeded when nothing was written to disk.
    """
    fpathstr = str(f.resolve())
    ok = cv2.imwrite(fpathstr, img, [int(cv2.IMWRITE_PNG_COMPRESSION), 9])
    if not ok:
        raise ValueError(f"write_png: cv2.imwrite failed to write image to {fpathstr}")
