from numpy import ndarray
from cv2 import cvtColor, COLOR_BGR2RGB, COLOR_BGR2GRAY
from pd_book_tools.ocr.document import Document
from .page import Page
from pytesseract import image_to_data, image_to_string, Output as pytesseract_Output


def tesseract_ocr_cv2_image(
    image: ndarray,
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

    ocr_doc = Document.from_tesseract(tesseract_output=dataframe, source_path=None)
    
    ocr_page: Page = ocr_doc.pages[0]

    return ocr_page


def get_default_doctr_predictor():
    """
    Get the pre-trained OCR predictor from the doctr library.
    :return: The OCR predictor.
    """
    from doctr.models import ocr_predictor, db_resnet50, crnn_vgg16_bn

    return ocr_predictor(
        det_arch=db_resnet50(pretrained=True),
        reco_arch=crnn_vgg16_bn(pretrained=True, pretrained_backbone=True),
        pretrained=True,
        assume_straight_pages=True,
        disable_crop_orientation=True,
    )


def doctr_ocr_cv2_image(
    image: ndarray,
    predictor=None,
) -> Page:
    """
    Perform OCR on a cv2 image using the doctr library.
    :param image: The input image in cv2 format.
    :param predictor: The OCR predictor to use. If None, it will use the default pre-trained model.
    :return: A tuple containing the recognized text and the OCR results.
    """
    if predictor is None:
        predictor = get_default_doctr_predictor()

    source_image = "out.png"

    # convert to cv2 image to RGB format
    image_list = [cvtColor(image, COLOR_BGR2RGB)]

    doctr_result = predictor(image_list)
    docTR_output = doctr_result.export()

    ocr_doc = Document.from_doctr_output(docTR_output, source_image)
    # Always 1 page per OCR in this case
    ocr_page: Page = ocr_doc.pages[0]
    ocr_page.cv2_numpy_page_image = image

    # ocr_page.refine_bounding_boxes()
    # ocr_page.reorganize_page()

    return ocr_page


full_predictor = None
# check if file exists
if os.path.exists(
    "../train_pgdp_ocr/ml-models/detection-model-finetuned.pt"
) and os.path.exists("../train_pgdp_ocr/ml-models/recognition-model-finetuned.pt"):
    print("Loading pre-trained OCR models...")
    # Check if GPU is available
    device, device_nbr = (
        ("cuda", "cuda:0") if torch.cuda.is_available() else ("cpu", "cpu")
    )

    finetuned_detection = "../train_pgdp_ocr/ml-models/detection-model-finetuned.pt"
    finetuned_recognition = "../train_pgdp_ocr/ml-models/recognition-model-finetuned.pt"

    det_model = db_resnet50(pretrained=True).to(device)
    det_params = torch_load(finetuned_detection, map_location=device_nbr)
    det_model.load_state_dict(det_params)

    vocab = "".join(
        sorted(
            dict.fromkeys(VOCABS["multilingual"] + "⸺¡¿—‘’“”′″⁄" + VOCABS["currency"])
        )
    )

    reco_model = crnn_vgg16_bn(
        pretrained=True,
        pretrained_backbone=True,
        vocab=vocab,  # model was fine-tuned on multilingual data with some additional unicode characters
    ).to(device)
    reco_params = torch_load(finetuned_recognition, map_location=device_nbr)
    reco_model.load_state_dict(reco_params)

    full_predictor = ocr_predictor(
        det_arch=det_model,
        reco_arch=reco_model,
        pretrained=True,
        assume_straight_pages=True,
        disable_crop_orientation=True,
    )

    det_predictor = detection_predictor(
        arch=det_model,
        pretrained=True,
        assume_straight_pages=True,
    )

    reco_predictor = recognition_predictor(
        arch=reco_model,
        pretrained=True,
    )

    full_predictor.det_predictor = det_predictor
    full_predictor.reco_predictor = reco_predictor
