import os

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


def get_finetuned_torch_doctr_predictor(
    dectection_pt_file,
    recognition_pt_file,
    vocab: str = "",
    pretrained: bool = True,
    pretrained_backbone: bool = True,
):
    full_predictor = None
    # check if file exists
    if os.path.exists(dectection_pt_file) and os.path.exists(recognition_pt_file):
        print("Loading pre-trained OCR models...")
        # Check if GPU is available
        device, device_nbr = (
            ("cuda", "cuda:0") if torch_cuda_is_available() else ("cpu", "cpu")
        )

        det_model = db_resnet50(pretrained=True).to(device)
        det_params = torch_load(dectection_pt_file, map_location=device_nbr)
        det_model.load_state_dict(det_params)

        if not vocab:
            # assume model was fine-tuned on mostly english book data with some additional unicode characters (⁄ is the "fraction" character not forward slash)
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
