from cv2 import imencode
from numpy import ndarray


def encode_bgr_image_as_png(bgr_image: ndarray):
    """Encodes a BGR image as a PNG buffer.

    cv2.imencode expects BGR input and writes correct RGB PNGs. No channel
    swap is needed before encoding.
    """
    _, buffer = imencode(".png", bgr_image)
    return buffer
