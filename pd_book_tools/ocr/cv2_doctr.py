from cv2 import COLOR_BGR2RGB, cvtColor
from doctr.models import (
    crnn_vgg16_bn,
    db_resnet50,
    ocr_predictor,
)
from numpy import ndarray

from pd_book_tools.ocr.document import Document
from pd_book_tools.ocr.page import Page


def get_default_doctr_predictor():
    """
    Get the pre-trained OCR predictor from the doctr library.
    :return: The OCR predictor.
    """
    return ocr_predictor(
        det_arch=db_resnet50(pretrained=True),
        reco_arch=crnn_vgg16_bn(pretrained=True, pretrained_backbone=True),
        pretrained=True,
        assume_straight_pages=True,
        disable_crop_orientation=True,
    )


def doctr_ocr_cv2_image(
    image: ndarray,
    source_image: str = "",
    predictor=None,
) -> Page:
    """
    Perform OCR on a cv2 image using the doctr library.
    :param image: The input image in cv2 format.
    :param source_image: The source image path or identifier for the OCR results.
    :param predictor: The OCR predictor to use. If None, it will use the default pre-trained model.
    :return: A tuple containing the recognized text and the OCR results.
    """
    if predictor is None:
        predictor = get_default_doctr_predictor()

    # convert to cv2 image to RGB format
    image_list = [cvtColor(image, COLOR_BGR2RGB)]

    doctr_result = predictor(image_list)
    ocr_doc = Document.from_doctr_result(doctr_result, source_image)

    # Always 1 page per OCR in this case
    ocr_page: Page = ocr_doc.pages[0]
    ocr_page.cv2_numpy_page_image = image

    return ocr_page
