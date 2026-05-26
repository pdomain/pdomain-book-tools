import logging
from base64 import b64encode
from typing import TYPE_CHECKING, Protocol, cast, runtime_checkable

from numpy import ndarray

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.image_processing.cv2_processing import encode_bgr_image_as_png
from pd_book_tools.ocr.block import Block
from pd_book_tools.ocr.word import Word

if TYPE_CHECKING:
    from pd_book_tools.ocr.character import Character


@runtime_checkable
class _HasRefineBoundingBoxes(Protocol):
    """Minimal protocol for Page objects that expose ``refine_bounding_boxes``."""

    def refine_bounding_boxes(
        self, image: ndarray | None = None, padding_px: int = 0
    ) -> None: ...


@runtime_checkable
class _HasCropBottom(Protocol):
    """Minimal protocol for Word objects that expose ``crop_bottom``."""

    def crop_bottom(self, image: ndarray) -> None: ...


logger = logging.getLogger(__name__)


def crop_image_to_bbox(
    element: object,
    page_image: ndarray | None,
    label: str = "element",
) -> ndarray | None:
    """Crop a region from *page_image* using the bounding box of *element*.

    Args:
        element: Any object with a ``bounding_box`` attribute.
        page_image: The full page image as a NumPy array.
        label: Human-readable label used in debug logging.

    Returns:
        Cropped image array, or ``None`` when cropping is impossible.
    """
    if element is None or page_image is None:
        logger.debug("No element or page_image for %s", label)
        return None

    raw_bbox = getattr(element, "bounding_box", None)
    if not raw_bbox:
        logger.debug("No bounding_box found for %s", label)
        return None
    bbox = cast("BoundingBox", raw_bbox)

    # Only swallow exceptions that genuinely mean "this bbox/image pair
    # cannot produce a crop" — bad coords (ValueError), bad image type or
    # missing .shape (AttributeError, TypeError), out-of-range slicing
    # before clamping (IndexError). Everything else is a real bug and
    # must propagate so the caller sees it instead of getting a silent
    # None that masks the failure mode (L-25).
    try:
        cropped: ndarray | None = bbox.crop_image(page_image)
        if cropped is None:
            logger.debug("Empty crop for %s", label)
        return cropped
    except (ValueError, AttributeError, TypeError, IndexError) as e:
        logger.debug("Error cropping image for %s: %s", label, e)
        return None


def get_encoded_image(
    img: ndarray,
) -> tuple[ndarray, str, str]:
    # Encode the image as PNG
    encoded_img = encode_bgr_image_as_png(img)
    b64_encoded_string = b64encode(memoryview(encoded_img)).decode("utf-8")
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
    h, w = cast("tuple[int, int]", img.shape[:2])
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


# ---------------------------------------------------------------------------
# R-01 / R-03 free-function image ops
#
# Canonical surface for image operations on Word / Block / Page. The
# corresponding methods on Word / Block / Page remain in place as thin
# wrappers preserving backward compatibility (downstream repos call
# them directly). New code should call these free functions.
#
# For simple ops (refine, crop_top, crop_bottom) the implementation
# lives here and the method delegates. For the more complex ops
# (split_into_characters_from_whitespace, estimate_baseline_from_image)  # noqa: ERA001  # function name references, not dead code
# the implementation continues to live on the method to limit blast
# radius; these free-function entry points delegate to the method.
# Callers see a uniform "free-function = canonical" surface either
# way.
# ---------------------------------------------------------------------------


def refine_word_bbox(word: Word, image: ndarray | None, padding_px: int = 1) -> bool:
    """Refine ``word.bounding_box`` against ``image``. Mutates ``word`` in place.

    Wraps the existing logic on :meth:`Word.refine_bbox` (BoundingBox.refine
    primary path with ``crop_bottom`` fallback). Returns ``True`` on
    successful refinement, ``False`` otherwise.
    """
    bbox = word.bounding_box
    if image is None:
        return False

    try:
        refined_bbox = bbox.refine(
            image, padding_px=padding_px, expand_beyond_original=False
        )
        # Defensive None check: BoundingBox.refine is typed to return
        # BoundingBox (non-optional), but test monkey-patches may return None.
        if refined_bbox is None:  # pyright: ignore[reportUnnecessaryComparison]
            return False
        word.bounding_box = refined_bbox
        return True
    except Exception:
        logger.debug(
            "Bounding-box refine failed during word refine; falling back",
            exc_info=True,
        )

    try:
        # Call the method (not the free function) so that downstream
        # tests / call sites that monkey-patch ``word.crop_bottom``
        # continue to work. The method itself thin-wraps the free
        # function ``crop_word_bottom`` in production.
        # Use a typed structural view so the unannotated method signature
        # doesn't leak into callers.
        cast("_HasCropBottom", cast("object", word)).crop_bottom(image)
        return True
    except Exception:
        logger.debug(
            "crop_bottom failed during word refine",
            exc_info=True,
        )

    return False


def crop_word_bottom(word: Word, image: ndarray | None) -> None:
    """Crop ``word.bounding_box`` to its bottom half. Mutates ``word``."""
    if word.bounding_box is None:  # pyright: ignore[reportUnnecessaryComparison]
        raise ValueError("Bounding box is None, cannot crop bottom")  # pyright: ignore[reportUnreachable]
    if image is None:
        raise ValueError("Image ndarray is None, cannot crop bottom")

    cropped_bbox = word.bounding_box.crop_bottom(image)
    # Defensive None check: BoundingBox.crop_bottom is typed BoundingBox→BoundingBox
    # but test stubs may return None; preserve existing bbox rather than overwrite with None.
    if cropped_bbox is None:  # pyright: ignore[reportUnnecessaryComparison]
        logger.warning(
            "Cropped bounding box is None, cannot crop bottom; preserving existing bounding_box"
        )
        return
    word.bounding_box = cropped_bbox


def crop_word_top(word: Word, image: ndarray | None) -> None:
    """Crop ``word.bounding_box`` to its top half. Mutates ``word``."""
    if word.bounding_box is None:  # pyright: ignore[reportUnnecessaryComparison]
        raise ValueError("Bounding box is None, cannot crop top")  # pyright: ignore[reportUnreachable]
    if image is None:
        raise ValueError("Image ndarray is None, cannot crop top")

    cropped_bbox = word.bounding_box.crop_top(image)
    # Defensive None check: BoundingBox.crop_top is typed BoundingBox→BoundingBox
    # but test stubs may return None; preserve existing bbox rather than overwrite with None.
    if cropped_bbox is None:  # pyright: ignore[reportUnnecessaryComparison]
        logger.warning(
            "Cropped bounding box is None, cannot crop top; preserving existing bounding_box"
        )
        return
    word.bounding_box = cropped_bbox


def split_word_into_characters(
    word: Word, image: ndarray | None, min_ink_pixels_per_column: int = 1
) -> list["Character"]:
    """Split a :class:`Word` into :class:`Character` objects via vertical-whitespace gaps.

    Free-function delegate of :meth:`Word.split_into_characters_from_whitespace`.
    The complex implementation continues to live on the method for now;
    new code should still prefer this free-function entry point so that
    a future iteration can flip the directionality without touching
    callers.
    """
    return word.split_into_characters_from_whitespace(
        image, min_ink_pixels_per_column=min_ink_pixels_per_column
    )


def estimate_word_baseline(
    word: Word, image: ndarray | None
) -> dict[str, float | str] | None:
    """Estimate a horizontal baseline for ``word``. Mutates ``word.baseline``.

    Free-function delegate of :meth:`Word.estimate_baseline_from_image`.
    """
    return word.estimate_baseline_from_image(image)


def estimate_block_baseline(
    block: Block, image: ndarray | None
) -> dict[str, float | str] | None:
    """Estimate a linear baseline for a line block. Mutates ``block.baseline``.

    Free-function delegate of :meth:`Block.estimate_baseline_from_image`.
    """
    return block.estimate_baseline_from_image(image)


def refine_block_bounding_boxes(
    block: Block, image: ndarray | None, padding_px: int = 0
) -> None:
    """Recursively refine ``block`` and its descendants' bboxes against ``image``.

    Free-function delegate of :meth:`Block.refine_bounding_boxes`.
    """
    block.refine_bounding_boxes(image, padding_px=padding_px)


def refine_page_bounding_boxes(
    page: _HasRefineBoundingBoxes, image: ndarray | None = None, padding_px: int = 0
) -> None:
    """Refine all bboxes on a :class:`Page` against ``image``.

    Free-function delegate of :meth:`Page.refine_bounding_boxes`. The ``page``
    parameter uses the ``_HasRefineBoundingBoxes`` protocol instead of ``Page``
    to avoid a circular import (image_utilities lives inside the OCR package;
    importing ``Page`` would create an import cycle).
    """
    page.refine_bounding_boxes(image=image, padding_px=padding_px)
