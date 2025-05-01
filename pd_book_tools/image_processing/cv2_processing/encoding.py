from cv2 import COLOR_BGR2RGB, cvtColor, imencode
from numpy import ndarray


def encode_bgr_image_as_png(bgr_image: ndarray):
    """Encodes a BGR image as a PNG buffer."""
    # Convert BGR to RGB
    rgb_image = cvtColor(bgr_image, COLOR_BGR2RGB)
    _, buffer = imencode(".png", rgb_image)
    return buffer
