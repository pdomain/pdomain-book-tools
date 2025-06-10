from base64 import b64encode

from numpy import ndarray

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.image_processing.cv2_processing import encode_bgr_image_as_png
from pd_book_tools.ocr.block import Block
from pd_book_tools.ocr.word import Word


def get_encoded_image(
    img: ndarray,
) -> tuple[ndarray, str, str]:
    # Encode the image as PNG
    encoded_img = encode_bgr_image_as_png(img)
    b64_encoded_string = b64encode(encoded_img).decode("utf-8")
    data_src_string = f"data:image/png;base64,{b64_encoded_string}"
    return encoded_img, b64_encoded_string, data_src_string


def get_cropped_encoded_image_scaled_bbox(
    img: ndarray, bounding_box_scaled: BoundingBox
) -> tuple[ndarray, ndarray, str, str]:
    # Get the bounding box of the word
    x1, y1, x2, y2 = bounding_box_scaled.to_ltrb()
    # Crop the image to the bounding box
    cropped_img = img[y1:y2, x1:x2]
    # Encode the cropped image as PNG
    return cropped_img, *get_encoded_image(cropped_img)


def get_cropped_encoded_image(
    img: ndarray, bounding_box: BoundingBox
) -> tuple[ndarray, ndarray, str, str]:
    h, w = img.shape[:2]
    # Get the bounding box of the word
    x1, y1, x2, y2 = bounding_box.scale(w, h).to_ltrb()
    # Crop the image to the bounding box
    cropped_img = img[y1:y2, x1:x2]
    # Encode the cropped image as PNG
    return cropped_img, *get_encoded_image(cropped_img)


def get_cropped_word_image(
    img: ndarray, word: Word
) -> tuple[ndarray, ndarray, str, str]:
    return get_cropped_encoded_image(img, word.bounding_box)


def get_cropped_block_image(
    img: ndarray, line: Block
) -> tuple[ndarray, ndarray, str, str]:
    if not line.bounding_box:
        raise ValueError("Line bounding box is not defined.")
    return get_cropped_encoded_image(img, line.bounding_box)
