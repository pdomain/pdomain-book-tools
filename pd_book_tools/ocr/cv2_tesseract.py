import logging

from cv2 import COLOR_BGR2GRAY, COLOR_BGRA2GRAY, cvtColor
from numpy import ndarray

from pd_book_tools.ocr.document import Document
from pd_book_tools.ocr.page import Page

try:
    from pytesseract import Output as pytesseract_Output
    from pytesseract import image_to_data, image_to_string

    _pytesseract_available = True
except ImportError:
    _pytesseract_available = False
    pytesseract_Output = None  # type: ignore[assignment]  # mirrors the pytesseract module attribute name; None when not installed
    image_to_data = None  # type: ignore[assignment]  # None when pytesseract is not installed
    image_to_string = None  # type: ignore[assignment]  # None when pytesseract is not installed

logger = logging.getLogger(__name__)

_RGBA_NOTICE_LOGGED = False


def tesseract_ocr_cv2_image(
    image: ndarray,
    source_path: str = "",
    dpi: int = 300,
    lang: str = "eng",
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
        lang: Tesseract language pack name (e.g. ``"eng"``, ``"deu"``,
            ``"eng+deu"``). Recorded into the Document's OCR provenance so
            two runs with different language packs produce distinguishable
            provenance records (L-18). Defaults to ``"eng"`` to preserve
            historical behavior.
    """
    if not _pytesseract_available:
        raise ImportError(
            "pytesseract is not installed. Please install extra dependency [tesseract]"
        )

    if image.ndim == 2:
        # If the image is already grayscale, no need to convert
        image_grayscale = image
    elif image.ndim == 3 and image.shape[2] == 3:
        # If the image is in color, convert it to grayscale
        image_grayscale = cvtColor(image, COLOR_BGR2GRAY)
    elif image.ndim == 3 and image.shape[2] == 4:
        # 4-channel BGRA / RGBA input: drop alpha (matches the
        # cv2 COLOR_BGRA2GRAY policy of ignoring the alpha channel
        # rather than alpha-blending). Mirrors the M-18 cupy
        # `cupy_color_to_gray` fix so both backends behave identically.
        global _RGBA_NOTICE_LOGGED
        if not _RGBA_NOTICE_LOGGED:
            logger.info(
                "tesseract_ocr_cv2_image received 4-channel input; dropping "
                "alpha channel (matches cv2 COLOR_BGRA2GRAY semantics). "
                "This notice is logged once per process."
            )
            _RGBA_NOTICE_LOGGED = True
        image_grayscale = cvtColor(image, COLOR_BGRA2GRAY)
    else:
        raise ValueError(
            "tesseract_ocr_cv2_image expected a 2D grayscale, 3-channel "
            "BGR, or 4-channel BGRA image; got shape="
            f"{tuple(image.shape)} (ndim={image.ndim})."
        )

    config = [
        "--oem 3",  # Use LSTM OCR engine
        "-c textord_noise_rej=1",
        # `-c textord_noise_debug=1` was previously hardcoded here, which
        # forced Tesseract to emit noise-detection debug messages to the
        # caller's stderr on every OCR call. Library code should not
        # pollute the caller's stderr; removed (M-21). If a future caller
        # legitimately needs the noise-detection trace, expose it as an
        # opt-in `extra_config` parameter at that time (YAGNI for now).
        f"--dpi {int(dpi)}",
    ]
    config_str = " ".join(config)

    dataframe = image_to_data(  # type: ignore[reportOptionalCall]  # guarded by _pytesseract_available check above
        image_grayscale,
        lang=lang,
        config=config_str,
        output_type=pytesseract_Output.DATAFRAME,  # type: ignore[reportOptionalMemberAccess]  # guarded by _pytesseract_available
    )
    result_string = image_to_string(  # type: ignore[reportOptionalCall]  # guarded by _pytesseract_available check above
        image_grayscale,
        lang=lang,
        config=config_str,
        output_type=pytesseract_Output.STRING,  # type: ignore[reportOptionalMemberAccess]  # guarded by _pytesseract_available
    )

    ocr_doc = Document.from_tesseract(
        tesseract_output=dataframe,
        tesseract_string=result_string,
        source_path=source_path if source_path else None,
        lang=lang,
        tesseract_config=config_str,
    )
    ocr_page: Page = ocr_doc.pages[0]

    return ocr_page
