from cv2 import imencode
from numpy import ndarray


def encode_bgr_image_as_png(bgr_image: ndarray) -> ndarray:
    """Encodes a BGR image as a PNG buffer.

    cv2.imencode expects BGR input and writes correct RGB PNGs. No channel
    swap is needed before encoding.
    """
    ok, buffer = imencode(".png", bgr_image)
    if not ok:
        raise ValueError(
            "encode_bgr_image_as_png: cv2.imencode failed to encode the image"
        )
    return buffer
