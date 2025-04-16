# Configure logging
import logging
import pathlib

from .io import read_image, write_jpg
from .rescale import rescale_image

logger = logging.getLogger(__name__)


def create_file_thumbnail(
    source_file_path: pathlib.Path,
    target_file_path: pathlib.Path,
    jpeg_quality=50,
    max_dimension: int = 300,
):
    img = read_image(source_file_path)
    thumb = rescale_image(img, target_short_side=max_dimension)

    if target_file_path.suffix == ".png":
        raise NotImplementedError("PNG not yet implemented")
        # quant = quantize(thumb, 4)
        # write_png(img=quant, f=target_file_path)
        # return
    elif target_file_path.suffix == ".jpg":
        write_jpg(
            img=thumb,
            f=target_file_path,
            quality=jpeg_quality,
        )
        return
    else:
        raise ValueError("file suffix must be '.jpg' or '.png'")
