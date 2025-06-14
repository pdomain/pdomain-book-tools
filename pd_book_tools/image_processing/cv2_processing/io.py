# Configure logging
import logging
import pathlib

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def read_image(src: pathlib.Path) -> np.ndarray:
    return cv2.imread(filename=src.resolve())


def write_jpg(img: np.ndarray, f: pathlib.Path, quality: int = 100):
    fpathstr = str(f.resolve())
    cv2.imwrite(fpathstr, img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])


def write_png(img: np.ndarray, f: pathlib.Path):
    fpathstr = str(f.resolve())
    cv2.imwrite(fpathstr, img, [int(cv2.IMWRITE_PNG_COMPRESSION), 9])
