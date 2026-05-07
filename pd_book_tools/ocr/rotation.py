"""Page-orientation detection for OCR.

Real-world scans include sideways foldout plates, upside-down cover pages,
and 90°-rotated maps (the Peutinger map in *From Magic to Science*, fixture
``rotated-peutinger-map.png``, is the canonical example). DocTR — and any
downstream layout detector — assumes upright input and silently produces
garbage when fed a rotated page.

Strategy is intentionally cheap: run OCR at the page's current orientation
first, and only fall back to trying 90°/180°/270° when mean per-word
confidence indicates the upright run was no good. We pick whichever
rotation yields the highest mean confidence.

This module deliberately knows nothing about the OCR engine internals — it
operates on (image, predictor) and on the resulting :class:`Document` only.
That keeps it composable with non-DocTR OCR backends down the line.
"""

from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from typing import TYPE_CHECKING, Callable, Sequence

import numpy as np
from numpy import ndarray

if TYPE_CHECKING:
    from pd_book_tools.ocr.document import Document

logger = getLogger(__name__)

# Rotations we try, in degrees clockwise. 0 is always tried first; the
# remaining values are the OpenCV-supported quarter turns.
DEFAULT_ROTATIONS: tuple[int, ...] = (0, 90, 180, 270)

# If mean per-word confidence at 0° meets or exceeds this, we trust the
# upright run and skip the other rotations entirely. Picked empirically as
# a value that's high enough to reject pages where DocTR is hallucinating
# letters out of stripes/decoration but low enough to accept legitimate
# OCR with some noisy words.
DEFAULT_CONFIDENCE_THRESHOLD: float = 0.6


@dataclass(frozen=True)
class RotationProbe:
    """Outcome of trying one rotation."""

    rotation: int  # degrees clockwise; one of {0, 90, 180, 270}
    mean_confidence: float
    word_count: int

    @property
    def has_words(self) -> bool:
        return self.word_count > 0


def rotate_image(image: ndarray, degrees: int) -> ndarray:
    """Rotate ``image`` by ``degrees`` clockwise (one of 0/90/180/270).

    Uses ``np.rot90`` so this is allocation-cheap and lossless. We accept
    only quarter turns because that's all our OCR fallback path needs;
    arbitrary-angle deskew is a different (and harder) problem out of
    scope here.
    """
    if degrees == 0:
        return image
    if degrees == 90:
        return np.rot90(image, k=-1).copy()
    if degrees == 180:
        return np.rot90(image, k=2).copy()
    if degrees == 270:
        return np.rot90(image, k=1).copy()
    raise ValueError(f"degrees must be one of 0/90/180/270, got {degrees}")


def _mean_confidence(doc: "Document") -> tuple[float, int]:
    """Mean per-word confidence across every page in ``doc``.

    Returns ``(mean_confidence, word_count)``. ``mean_confidence`` is 0.0
    when no words have a confidence value (so the empty-page case is
    treated as "no signal" rather than NaN-poisoning the comparison).
    """
    confidences: list[float] = []
    for page in doc.pages:
        for word in page.words:
            if word.ocr_confidence is not None:
                confidences.append(float(word.ocr_confidence))
    if not confidences:
        return 0.0, 0
    return float(np.mean(confidences)), len(confidences)


def detect_best_rotation(
    image: ndarray,
    *,
    ocr_fn: Callable[[ndarray], "Document"],
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    rotations: Sequence[int] = DEFAULT_ROTATIONS,
    upright_result: "Document | None" = None,
) -> tuple[int, "Document", list[RotationProbe]]:
    """Find the rotation that maximises OCR confidence on ``image``.

    Tries 0° first (fast path: returns immediately if confidence is at or
    above ``confidence_threshold``). Otherwise probes every rotation in
    ``rotations`` and picks the one with the highest mean confidence,
    returning the OCR output for that rotation directly so callers don't
    re-run OCR.

    Parameters
    ----------
    image
        Source image as a numpy array (BGR / RGB / grayscale).
    ocr_fn
        Callable that takes an image array and returns a :class:`Document`.
        Typically a partially-applied ``Document.from_image_ocr_via_doctr``;
        kept abstract so this module isn't bound to DocTR.
    confidence_threshold
        Mean per-word confidence at which the 0° pass is considered good
        enough to skip the fallback rotations. Default 0.6.
    rotations
        Rotations to try, in order. Must start with 0; subsequent values
        are tried only if the 0° pass fails the threshold.
    upright_result
        Optional pre-computed :class:`Document` for the 0° pass. When
        provided, the upright OCR call is skipped and this result is used
        directly — useful for callers that already have OCR output for
        the upright orientation and want to avoid a redundant pass. When
        ``None`` (default), the upright pass runs as before.

    Returns
    -------
    chosen_rotation
        Degrees of rotation applied to the source image to produce the
        best OCR. 0 means the original orientation was best.
    document
        The :class:`Document` produced by OCR at ``chosen_rotation``.
        Its bounding boxes are already in the rotated frame — i.e., they
        index into ``rotate_image(image, chosen_rotation)``, *not* into
        the original ``image``.
    probes
        Per-rotation diagnostics. Useful for callers that want to log or
        surface the decision (e.g. the labeler UI).
    """
    if not rotations or rotations[0] != 0:
        raise ValueError("rotations must start with 0 (the upright pass)")

    probes: list[RotationProbe] = []

    # Fast path: try the page upright first. If the caller already has
    # the upright OCR result, skip the redundant call.
    doc_upright = upright_result if upright_result is not None else ocr_fn(image)
    conf_upright, count_upright = _mean_confidence(doc_upright)
    probes.append(RotationProbe(0, conf_upright, count_upright))
    if conf_upright >= confidence_threshold:
        logger.debug(
            "rotation: upright pass confident enough (%.3f >= %.3f), skipping fallbacks",
            conf_upright,
            confidence_threshold,
        )
        return 0, doc_upright, probes

    logger.info(
        "rotation: upright confidence %.3f below threshold %.3f; trying fallbacks",
        conf_upright,
        confidence_threshold,
    )

    best_rotation = 0
    best_doc = doc_upright
    best_conf = conf_upright

    for deg in rotations[1:]:
        rotated = rotate_image(image, deg)
        doc = ocr_fn(rotated)
        conf, count = _mean_confidence(doc)
        probes.append(RotationProbe(deg, conf, count))
        logger.debug("rotation: %d° -> mean conf %.3f over %d words", deg, conf, count)
        if conf > best_conf:
            best_rotation = deg
            best_doc = doc
            best_conf = conf

    if best_rotation != 0:
        logger.info(
            "rotation: chose %d° (conf %.3f) over upright (conf %.3f)",
            best_rotation,
            best_conf,
            conf_upright,
        )
    return best_rotation, best_doc, probes
