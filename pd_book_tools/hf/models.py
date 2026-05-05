"""Model resolution helpers for OCR + layout artifacts on Hugging Face Hub.

Builds on :mod:`pd_book_tools.hf.download` to translate "what model do I want"
into "where is the cached file path." Intended consumers: pd-ocr-cli,
pd-ocr-labeler, pd-prep-for-pgdp.
"""

from __future__ import annotations

from pathlib import Path

from .download import hf_download

DEFAULT_HF_REPO = "CT2534/pd-ocr-models"
DEFAULT_DET_FILENAME = "detection/pd-all-detection-model-finetuned.pt"
DEFAULT_RECO_FILENAME = "recognition/pd-all-recognition-model-finetuned.pt"

OCR_MODEL_SIDECARS: tuple[str, ...] = (".arch", ".vocab")

LAYOUT_MODEL_FILES: tuple[str, ...] = (
    "config.json",
    "preprocessor_config.json",
    "model.safetensors",
)


def short_revision(rev: str | None) -> str:
    """Return ``rev[:8]`` or ``"latest"`` for display."""
    if not rev:
        return "latest"
    return rev[:8] if len(rev) > 8 else rev


# ─── OCR detection + recognition ─────────────────────────────────────────────


def resolve_ocr_models(
    *,
    repo: str = DEFAULT_HF_REPO,
    revision: str | None = None,
    det_filename: str = DEFAULT_DET_FILENAME,
    reco_filename: str = DEFAULT_RECO_FILENAME,
    detection_path: Path | None = None,
    recognition_path: Path | None = None,
) -> tuple[Path, Path]:
    """Return ``(det_path, reco_path)`` from local paths or HF Hub.

    Either both ``detection_path`` and ``recognition_path`` are provided
    (local files; both must exist), or both are ``None`` (HF Hub fetch).
    Mixed input raises :class:`ValueError`.
    """
    if bool(detection_path) != bool(recognition_path):
        raise ValueError(
            "detection_path and recognition_path must both be set or both omitted"
        )
    if detection_path and recognition_path:
        if not detection_path.is_file():
            raise FileNotFoundError(f"detection model not found: {detection_path}")
        if not recognition_path.is_file():
            raise FileNotFoundError(f"recognition model not found: {recognition_path}")
        return detection_path, recognition_path

    det = hf_download(repo, det_filename, revision, sidecars=OCR_MODEL_SIDECARS)
    reco = hf_download(repo, reco_filename, revision, sidecars=OCR_MODEL_SIDECARS)
    return det, reco


# ─── Layout model ────────────────────────────────────────────────────────────


def resolve_layout_source(
    layout_model: str,
    layout_checkpoint: str | None = None,
) -> tuple[str | None, str | None, str]:
    """Translate a layout backend name into ``(repo, revision, descriptor)``.

    ``repo`` and ``revision`` are ``None`` for backends that don't fetch from
    HF Hub (``"none"``, ``"contour"``, or a local checkpoint path). The
    descriptor is a human-readable label suitable for a "Loaded …" line.
    """
    if layout_model == "none":
        return (None, None, "")
    if layout_model == "contour":
        return (None, None, "contour (built-in)")

    if layout_checkpoint:
        ckpt = Path(layout_checkpoint)
        if ckpt.exists():
            return (None, None, str(ckpt))
        return (layout_checkpoint, None, f"{layout_checkpoint}@latest")

    from pd_book_tools.layout.adapters.pp_doclayout import PPDocLayoutPlusLDetector

    return (
        PPDocLayoutPlusLDetector.HF_REPO,
        PPDocLayoutPlusLDetector.HF_REVISION,
        f"{PPDocLayoutPlusLDetector.HF_REPO}@{short_revision(PPDocLayoutPlusLDetector.HF_REVISION)}",
    )


def prefetch_layout_files(repo: str, revision: str | None) -> None:
    """Pre-download the HF transformers files for a layout model.

    Ensures the later ``from_pretrained()`` call inside the adapter is a cache
    hit, so the only progress bar the user sees is HF Hub's per-file download
    bar — not transformers' in-memory weight-loading bar.
    """
    for fname in LAYOUT_MODEL_FILES:
        hf_download(repo, fname, revision)


def silence_transformers_load_chatter() -> None:
    """Disable ``transformers`` verbose logging + in-memory progress bar.

    No-op when ``transformers`` is not installed.
    """
    try:
        from transformers.utils import logging as _hf_logging

        _hf_logging.set_verbosity_error()
        _hf_logging.disable_progress_bar()
    except Exception:
        pass


__all__ = [
    "DEFAULT_DET_FILENAME",
    "DEFAULT_HF_REPO",
    "DEFAULT_RECO_FILENAME",
    "LAYOUT_MODEL_FILES",
    "OCR_MODEL_SIDECARS",
    "prefetch_layout_files",
    "resolve_layout_source",
    "resolve_ocr_models",
    "short_revision",
    "silence_transformers_load_chatter",
]
