from os import PathLike
from pathlib import Path


def get_default_doctr_predictor():
    """
    Get the pre-trained OCR predictor from the doctr library.
    :return: The OCR predictor.
    """
    try:
        from doctr.models import (
            crnn_vgg16_bn,
            db_resnet50,
            ocr_predictor,
        )
    except ImportError as e:
        raise ImportError(
            "The docTR library is required for OCR. Please install it (PyPi: python-doctr)"
        ) from e

    return ocr_predictor(
        det_arch=db_resnet50(pretrained=True),
        reco_arch=crnn_vgg16_bn(pretrained=True, pretrained_backbone=True),
        pretrained=True,
        assume_straight_pages=True,
        disable_crop_orientation=True,
    )


def get_finetuned_torch_doctr_predictor(
    dectection_pt_file: PathLike,
    recognition_pt_file: PathLike,
    vocab: str = "",
    pretrained: bool = True,
    pretrained_backbone: bool = True,
):
    full_predictor = None

    try:
        from torch import load as torch_load
        from torch.cuda import is_available as torch_cuda_is_available
    except ImportError:
        raise ImportError("PyTorch is not available in this environment.")

    from doctr.datasets.vocabs import VOCABS
    from doctr.models import (
        crnn_vgg16_bn,
        db_resnet50,
        detection_predictor,
        ocr_predictor,
        recognition_predictor,
    )

    # check if file exists
    if Path.exists(dectection_pt_file) and Path.exists(recognition_pt_file):
        print("Loading pre-trained OCR models...")
        # Check if CUDA is available
        device, device_nbr = (
            ("cuda", "cuda:0") if torch_cuda_is_available() else ("cpu", "cpu")
        )

        det_model = db_resnet50(pretrained=True).to(device)
        det_params = torch_load(dectection_pt_file, map_location=device_nbr)
        det_model.load_state_dict(det_params)

        if not vocab:
            # assume the model was fine-tuned on mostly english book data with some additional unicode characters
            # (⁄ is the "fraction" character not forward slash)
            vocab = "".join(
                sorted(
                    dict.fromkeys(
                        VOCABS["multilingual"] + "⸺¡¿—‘’“”′″⁄" + VOCABS["currency"]
                    )
                )
            )

        reco_model = crnn_vgg16_bn(
            pretrained=pretrained,
            pretrained_backbone=pretrained_backbone,
            vocab=vocab,
        ).to(device)
        reco_params = torch_load(recognition_pt_file, map_location=device_nbr)
        reco_model.load_state_dict(reco_params)

        full_predictor = ocr_predictor(
            det_arch=det_model,
            reco_arch=reco_model,
            pretrained=pretrained,
            assume_straight_pages=True,
            disable_crop_orientation=True,
        )

        det_predictor = detection_predictor(
            arch=det_model,
            pretrained=pretrained,
            assume_straight_pages=True,
        )

        reco_predictor = recognition_predictor(
            arch=reco_model,
            pretrained=pretrained,
        )

        full_predictor.det_predictor = det_predictor
        full_predictor.reco_predictor = reco_predictor

        return full_predictor
