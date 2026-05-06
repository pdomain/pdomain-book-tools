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
    dpi: int = 300,
) -> Page:
    """Run Tesseract OCR over a cv2 image array and return a Page.

    Args:
        image: 2D grayscale or 3D BGR cv2/numpy image array.
        source_path: Optional source path to record on the produced Document.
        dpi: Scan resolution in dots-per-inch passed to Tesseract via
            ``--dpi``. Tesseract uses this to size its character-classifier
            heuristics; on 150 / 600 DPI scans the default of 300 mis-estimates
            character sizes and degrades OCR. Callers that know the actual
            image DPI (e.g. from PIL ``Image.info["dpi"]`` or scanner metadata)
            should pass it through. Defaults to 300 to preserve historical
            behavior.
    """
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
        f"--dpi {int(dpi)}",
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
