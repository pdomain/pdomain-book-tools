from cv2 import COLOR_BGR2GRAY, cvtColor
from numpy import ndarray

from pd_book_tools.ocr.document import Document
from pd_book_tools.ocr.page import Page

try:
    from pytesseract import Output as pytesseract_Output
    from pytesseract import image_to_data, image_to_string
except ImportError:
    raise ImportError(
        "pytesseract is not installed. Please install extra dependency [tesseract]"
    )


def tesseract_ocr_cv2_image(
    image: ndarray,
    source_path: str = "",
) -> Page:
    image_grayscale = None

    if image.ndim == 2:
        # If the image is already grayscale, no need to convert
        image_grayscale = image
    elif image.ndim == 3 and image.shape[2] == 3:
        # If the image is in color, convert it to grayscale
        image_grayscale = cvtColor(image, COLOR_BGR2GRAY)

    config = [
        "--oem 3",  # Use LSTM OCR engine
        "-c textord_noise_rej=1",
        "-c textord_noise_debug=1",
        "--dpi 300",
    ]
    config_str = " ".join(config)

    dataframe = image_to_data(
        image_grayscale,
        lang="eng",
        config=config_str,
        output_type=pytesseract_Output.DATAFRAME,
    )
    result_string = image_to_string(
        image_grayscale,
        lang="eng",
        config=config_str,
        output_type=pytesseract_Output.STRING,
    )

    ocr_doc = Document.from_tesseract(
        tesseract_output=dataframe,
        tesseract_string=result_string,
        source_path=source_path if source_path else None,
    )
    ocr_page: Page = ocr_doc.pages[0]

    return ocr_page
