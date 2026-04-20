import itertools
import pathlib
from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from json import dump as json_dump
from json import load as json_load
from logging import getLogger
from typing import Any, Callable, Collection, Dict, List, Optional, Tuple

# from cv2 import IMWRITE_JPEG_QUALITY as cv2_IMWRITE_JPEG_QUALITY
from cv2 import COLOR_BGR2RGB as cv2_COLOR_BGR2RGB
from cv2 import FONT_HERSHEY_SIMPLEX as cv2_FONT_HERSHEY_SIMPLEX
from cv2 import IMWRITE_PNG_COMPRESSION as cv2_IMWRITE_PNG_COMPRESSION
from cv2 import cvtColor as cv2_cvtColor
from cv2 import imwrite as cv2_imwrite
from cv2 import putText as cv2_putText
from cv2 import rectangle as cv2_rectangle
from numpy import mean as np_mean
from numpy import median as np_median
from numpy import ndarray
from numpy import std as np_std

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.block import Block, BlockCategory
from pd_book_tools.ocr.ground_truth_matching import update_page_with_ground_truth_text
from pd_book_tools.ocr.provenance import OCRProvenance
from pd_book_tools.ocr.word import Word

# Configure logging
logger = getLogger(__name__)


class BBoxColors(Enum):
    """Enum for different colors used to draw bounding boxes"""

    PAGE = (255, 0, 255)  # Magenta
    BLOCK = (0, 255, 0)  # Green
    PARAGRAPH = (255, 0, 0)  # Red
    LINE = (0, 0, 255)  # Blue
    WORD = (0, 128, 0)  # Dark Green
    GROUND_TRUTH = (0, 255, 255)  # Cyan
    BLACK = (0, 0, 0)  # Black
    DARK_YELLOW = (0, 225, 225)  # Darker Yellow


@dataclass
class Page:
    """Represents a page (single or multiple "blocks") of OCR results"""

    width: int
    height: int
    page_index: int
    bounding_box: Optional[BoundingBox] = None
    _items: List[Block] = field(
        default_factory=list, init=False, repr=False, compare=False
    )
    page_labels: Optional[list[str]] = None
    _cv2_numpy_page_image: Optional[ndarray] = None
    _cv2_numpy_page_image_page_with_bbox: Optional[ndarray] = None
    _cv2_numpy_page_image_blocks_with_bboxes: Optional[ndarray] = None
    _cv2_numpy_page_image_paragraph_with_bboxes: Optional[ndarray] = None
    _cv2_numpy_page_image_line_with_bboxes: Optional[ndarray] = None
    _cv2_numpy_page_image_word_with_bboxes: Optional[ndarray] = None
    _cv2_numpy_page_image_word_with_bboxes_and_ocr_text: Optional[ndarray] = None
    _cv2_numpy_page_image_word_with_bboxes_and_gt_text: Optional[ndarray] = None
    _cv2_numpy_page_image_matched_word_with_colors: Optional[ndarray] = None

    unmatched_ground_truth_lines: Optional[List] = None
    "List of Ground Truth Lines and the line they were found on before an OCR match"

    original_ocr_tool_text: Optional[str] = ""
    original_ground_truth_text: Optional[str] = ""
    ocr_provenance: OCRProvenance | None = None

    def __init__(
        self,
        width: int,
        height: int,
        page_index: int,
        items: Collection,
        bounding_box: Optional[BoundingBox] = None,
        page_labels: Optional[list[str]] = None,
        cv2_numpy_page_image: Optional[ndarray] = None,
        unmatched_ground_truth_lines: Optional[List[Tuple[int, str]]] = None,
        original_ocr_tool_text: Optional[str] = "",
        original_ground_truth_text: Optional[str] = "",
        ocr_provenance: OCRProvenance | Dict[str, Any] | None = None,
        image_path: pathlib.Path | str | None = None,
        name: str | None = None,
        source: str = "ocr",
        ocr_failed: bool = False,
        provenance_live_ocr: Dict[str, Any] | None = None,
        provenance_saved_ocr: Dict[str, Any] | None = None,
        provenance_saved: Dict[str, Any] | None = None,
    ):
        self.width = width
        self.height = height
        self.page_index = page_index
        self.items = items  # Use the setter for validation or processing
        if bounding_box:
            self.bounding_box = bounding_box
        elif self.items:
            self.bounding_box = BoundingBox.union(
                [item.bounding_box for item in self.items]
            )
        self.page_labels = page_labels

        if cv2_numpy_page_image is not None:
            if not isinstance(cv2_numpy_page_image, ndarray):
                raise TypeError("cv2_numpy_page_image must be a numpy ndarray")

            self.cv2_numpy_page_image = (
                cv2_numpy_page_image  # Use the setter for validation or processing
            )

        if unmatched_ground_truth_lines:
            self.unmatched_ground_truth_lines = unmatched_ground_truth_lines
        else:
            self.unmatched_ground_truth_lines = []

        self.original_ocr_tool_text = original_ocr_tool_text
        self.original_ground_truth_text = original_ground_truth_text
        self.ocr_provenance = OCRProvenance.coerce(ocr_provenance)

        # Page metadata fields
        self.image_path: pathlib.Path | str | None = image_path
        self.name: str | None = name
        self.source: str = source
        self.ocr_failed: bool = ocr_failed
        self.provenance_live_ocr: Dict[str, Any] | None = provenance_live_ocr
        self.provenance_saved_ocr: Dict[str, Any] | None = provenance_saved_ocr
        self.provenance_saved: Dict[str, Any] | None = provenance_saved

    @property
    def index(self) -> int:
        """Compatibility alias for ``page_index``."""
        return self.page_index

    @index.setter
    def index(self, value: int) -> None:
        self.page_index = int(value)

    @property
    def page_source(self) -> str:
        """Compatibility alias for ``source``."""
        return self.source

    @page_source.setter
    def page_source(self, value: str) -> None:
        self.source = value

    def _sort_items(self):
        self._items.sort(
            key=lambda item: (
                item.bounding_box.top_left.y if item.bounding_box else 0,
                item.bounding_box.top_left.x if item.bounding_box else 0,
            ),
        )

    @property
    def items(self) -> List[Block]:
        """Returns a copy of the item list in this page"""
        self._sort_items()
        return self._items.copy()

    def add_item(self, item):
        """Add an item to the page"""
        if not isinstance(item, Block):
            raise TypeError("Item must be of type Block")
        self._items.append(item)
        self._sort_items()
        self.recompute_bounding_box()

    def remove_item(self, item):
        """Remove a block from the page"""
        if item in self._items:
            self._items.remove(item)
            self._sort_items()
            self.recompute_bounding_box()
        else:
            raise ValueError("Item not found in page")

    def remove_line_if_exists(self, line):
        """Remove a line from the page if it exists"""
        removed = False

        if line in self._items:
            self.remove_item(line)
            removed = True
        else:
            for block in self._items:
                if block.remove_line_if_exists(line):
                    removed = True
                    break

        if removed:
            logger.debug(f"Line {line.text[0:10]}... removed from page")
        else:
            logger.debug(f"Line {line.text[0:10]}... not found in page")

        return removed

    def remove_empty_items(self):
        """Remove empty child blocks from the page."""
        if not self.items:
            return
        item: Block
        for item in self.items:
            item.remove_empty_items()
            if not item.items:
                logger.debug("Empty block removed")
                self.remove_item(item)

    @items.setter
    def items(self, values):
        if not isinstance(values, Collection):
            raise TypeError("items must be a collection")
        for block in values:
            if not isinstance(block, Block):
                raise TypeError("Each item in items must be of type Block")
        self._items = sorted(
            values,
            key=lambda block: (
                block.bounding_box.top_left.y if block.bounding_box else 0,
                block.bounding_box.top_left.x if block.bounding_box else 0,
            ),
        )

    @property
    def cv2_numpy_page_image(self) -> ndarray | None:
        return self._cv2_numpy_page_image

    @cv2_numpy_page_image.setter
    def cv2_numpy_page_image(self, value: ndarray):
        if value is not None and not isinstance(value, ndarray):
            raise TypeError("cv2_numpy_page_image must be a numpy ndarray")
        self._cv2_numpy_page_image = value

        self.refresh_page_images()

    @property
    def cv2_numpy_page_image_page_with_bbox(self) -> ndarray | None:
        return self._cv2_numpy_page_image_page_with_bbox

    @property
    def cv2_numpy_page_image_blocks_with_bboxes(self) -> ndarray | None:
        return self._cv2_numpy_page_image_blocks_with_bboxes

    @property
    def cv2_numpy_page_image_paragraph_with_bboxes(self) -> ndarray | None:
        return self._cv2_numpy_page_image_paragraph_with_bboxes

    @property
    def cv2_numpy_page_image_line_with_bboxes(self) -> ndarray | None:
        return self._cv2_numpy_page_image_line_with_bboxes

    @property
    def cv2_numpy_page_image_word_with_bboxes(self) -> ndarray | None:
        return self._cv2_numpy_page_image_word_with_bboxes

    @property
    def cv2_numpy_page_image_word_with_bboxes_and_ocr_text(self) -> ndarray | None:
        return self._cv2_numpy_page_image_word_with_bboxes_and_ocr_text

    @property
    def cv2_numpy_page_image_word_with_bboxes_and_gt_text(self) -> ndarray | None:
        return self._cv2_numpy_page_image_word_with_bboxes_and_gt_text

    @property
    def cv2_numpy_page_image_matched_word_with_colors(self) -> ndarray | None:
        return self._cv2_numpy_page_image_matched_word_with_colors

    def refresh_page_images(self):
        if self._cv2_numpy_page_image is None:
            return

        # Rebuild all images with drawn bboxes on them
        self._cv2_numpy_page_image_page_with_bbox = self._cv2_numpy_page_image.copy()
        self._add_rect(self._cv2_numpy_page_image_page_with_bbox, self)

        self._cv2_numpy_page_image_blocks_with_bboxes = (
            self._cv2_numpy_page_image.copy()
        )
        self._add_rect_recurse(
            self.items,
            self._cv2_numpy_page_image_blocks_with_bboxes,
            lambda x: isinstance(x, Block) and x.block_category == BlockCategory.BLOCK,
        )

        self._cv2_numpy_page_image_paragraph_with_bboxes = (
            self._cv2_numpy_page_image.copy()
        )

        self._add_rect_recurse(
            self.items,
            self._cv2_numpy_page_image_paragraph_with_bboxes,
            lambda x: (
                isinstance(x, Block) and x.block_category == BlockCategory.PARAGRAPH
            ),
        )

        self._cv2_numpy_page_image_line_with_bboxes = self._cv2_numpy_page_image.copy()
        self._add_rect_recurse(
            self.items,
            self._cv2_numpy_page_image_line_with_bboxes,
            lambda x: isinstance(x, Block) and x.block_category == BlockCategory.LINE,
        )

        self._cv2_numpy_page_image_word_with_bboxes = self._cv2_numpy_page_image.copy()
        self._add_rect_recurse(
            self.items,
            self._cv2_numpy_page_image_word_with_bboxes,
            lambda x: isinstance(x, Word),
        )

        self._cv2_numpy_page_image_word_with_bboxes_and_ocr_text = (
            self._cv2_numpy_page_image.copy()
        )
        self._add_rect_recurse(
            self.items,
            self._cv2_numpy_page_image_word_with_bboxes_and_ocr_text,
            lambda x: isinstance(x, Word),
        )
        self._add_text_recurse(
            self.items,
            self._cv2_numpy_page_image_word_with_bboxes_and_ocr_text,
            text_attr="text",
        )

        self._cv2_numpy_page_image_word_with_bboxes_and_gt_text = (
            self._cv2_numpy_page_image.copy()
        )
        self._add_rect_recurse(
            self.items,
            self._cv2_numpy_page_image_word_with_bboxes_and_gt_text,
            lambda x: isinstance(x, Word),
        )
        self._add_text_recurse(
            self.items,
            self._cv2_numpy_page_image_word_with_bboxes_and_gt_text,
            text_attr="ground_truth_text",
        )

        self._cv2_numpy_page_image_matched_word_with_colors = (
            self._cv2_numpy_page_image.copy()
        )
        for w in self.words:
            if (
                "match_score" in w.ground_truth_match_keys
                and w.ground_truth_match_keys["match_score"] == 100
            ):
                continue  # Don't display a box for matched words

            if (
                not w.ground_truth_text
                or not w.ground_truth_match_keys
                or "match_score" not in w.ground_truth_match_keys
            ):
                logger.debug("No ground truth match/match score for word " + w.text)
                color = BBoxColors.LINE.value
            elif w.ground_truth_match_keys["match_score"] >= 90:
                color = BBoxColors.WORD.value
            elif w.ground_truth_match_keys["match_score"] >= 70:
                color = BBoxColors.DARK_YELLOW.value
            else:
                color = BBoxColors.PAGE.value
            self._add_rect(
                self._cv2_numpy_page_image_matched_word_with_colors, w, color
            )

    def _add_rect_recurse(self, items, image, item_add_lambda):
        if image is None:
            return
        for item in items:
            if item_add_lambda(item):
                self._add_rect(image, item)
            if hasattr(item, "items") and item.items:
                self._add_rect_recurse(item.items, image, item_add_lambda)

    @classmethod
    def _add_rect(cls, image, item, box_color=None):
        w, h = image.shape[1], image.shape[0]
        if not box_color:
            if isinstance(item, Page):
                box_color = BBoxColors.PAGE.value
            elif isinstance(item, Word):
                box_color = BBoxColors.WORD.value
            elif isinstance(item, Block):
                if item.block_category == BlockCategory.LINE:
                    box_color = BBoxColors.LINE.value
                elif item.block_category == BlockCategory.PARAGRAPH:
                    box_color = BBoxColors.PARAGRAPH.value
                else:
                    box_color = BBoxColors.BLOCK.value
            else:
                box_color = BBoxColors.BLACK.value

        bbox = item.bounding_box
        # If scaled coordinates
        if item and item.bounding_box:
            if item.bounding_box.width < 1 or item.bounding_box.height < 1:
                bbox = item.bounding_box.scale(width=w, height=h)

            if bbox is not None:
                cv2_rectangle(
                    img=image,
                    pt1=(int(bbox.top_left.x), int(bbox.top_left.y)),
                    pt2=(int(bbox.bottom_right.x), int(bbox.bottom_right.y)),
                    color=box_color,
                    thickness=2,
                )

    def _add_text_recurse(self, items, image, text_attr="text"):
        if image is None:
            return
        for item in items:
            if isinstance(item, Word):
                self._add_text_label(image, item, text_attr=text_attr)
            elif hasattr(item, "items") and item.items:
                self._add_text_recurse(item.items, image, text_attr=text_attr)

    @classmethod
    def _add_text_label(cls, image, item, text_attr="text", color=None):
        if not isinstance(item, Word):
            raise TypeError("item must be of type Word")
        w, h = image.shape[1], image.shape[0]
        if not color:
            color = (255, 0, 0)  # Blue

        bbox = item.bounding_box
        # If scaled coordinates
        if item.bounding_box.width < 1 or item.bounding_box.height < 1:
            bbox = item.bounding_box.scale(width=w, height=h)

        x1 = int(bbox.top_left.x)
        y1 = max(int(bbox.top_left.y), 0)
        cv2_putText(
            image,
            getattr(item, text_attr, None) or "",
            (x1, y1 - 5),
            cv2_FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1,
        )

    @property
    def text(self) -> str:
        """
        Get the full text of the page, separating each top-level block
        by double carriage returns and one final carraige return
        """
        return "\n\n".join(block.text for block in self.items) + "\n"

    @property
    def ground_truth_text(self) -> str:
        """
        Get the full ground truth text of the page, separating each top-level block
        by double carriage returns and one final carraige return
        """
        return "\n\n".join(block.ground_truth_text for block in self.items) + "\n"

    @property
    def ground_truth_exact_match(self) -> bool:
        """Check if the ground truth text of the block matches the text"""
        return all(item.ground_truth_exact_match for item in self.items)

    @property
    def words(self) -> List[Word]:
        """Get flat list of all words in the page"""
        return list(itertools.chain.from_iterable([item.words for item in self.items]))

    @property
    def lines(self) -> List["Block"]:
        """Get flat list of all 'lines' in the page"""
        return list(itertools.chain.from_iterable([item.lines for item in self.items]))

    @property
    def paragraphs(self) -> List["Block"]:
        """Get flat list of all 'paragraphs' in the page"""
        return list(
            itertools.chain.from_iterable([item.paragraphs for item in self.items])
        )

    @property
    def is_content_normalized(self) -> bool:
        """Return True if existing word bboxes on the page are normalized."""
        for line in self.lines:
            for word in line.words:
                if word.bounding_box is not None:
                    return word.bounding_box.is_normalized
        return False

    @property
    def resolved_dimensions(self) -> tuple[float, float]:
        """Return page dimensions in pixels (width, height).

        Falls back to page image dimensions if width/height are not set.
        """
        w = float(self.width or 0.0)
        h = float(self.height or 0.0)
        if w > 0.0 and h > 0.0:
            return w, h

        base_image = self.cv2_numpy_page_image
        if base_image is not None:
            image_height, image_width = base_image.shape[:2]
            return float(image_width), float(image_height)

        return 0.0, 0.0

    # ------------------------------------------------------------------
    # Structural helpers
    # ------------------------------------------------------------------

    def validated_line_words(self, line_index: int) -> list[Word] | None:
        """Validate line index and return line words list, or None if invalid."""
        lines = list(self.lines)
        if line_index < 0 or line_index >= len(lines):
            logger.warning(
                "Line index %s out of range (0-%s)",
                line_index,
                len(lines) - 1,
            )
            return None
        return list(lines[line_index].words)

    @staticmethod
    def move_word_between_lines(
        source_line: Block,
        target_line: Block,
        word: Word,
    ) -> bool:
        """Move a word object from source line to target line."""
        if source_line is target_line:
            return True

        source_line.remove_item(word)
        try:
            target_line.add_item(word)
        except Exception:
            source_line.add_item(word)
            return False
        return True

    # ------------------------------------------------------------------
    # Spatial line-search helpers
    # ------------------------------------------------------------------

    @staticmethod
    def closest_line_by_y_range_then_x(
        lines: list[Block],
        center_x: float,
        center_y: float,
        fallback_line: Block,
    ) -> Block:
        """Choose the best line for a point at (center_x, center_y).

        Strategy:
        1. Collect all lines whose Y range contains center_y.
        2. Among those, pick the one closest horizontally.
        3. Fall back to closest vertical midpoint.
        """
        y_candidates: list[Block] = []
        for line in lines:
            bbox = line.bounding_box
            if bbox is None or not bbox.has_usable_coordinates:
                continue
            if bbox.minY <= center_y <= bbox.maxY:
                y_candidates.append(line)

        if y_candidates:
            best_line = y_candidates[0]
            best_x_dist = float("inf")
            for line in y_candidates:
                bbox = line.bounding_box
                if bbox is None:
                    continue
                x_dist = abs(bbox.horizontal_midpoint - center_x)
                if x_dist < best_x_dist:
                    best_x_dist = x_dist
                    best_line = line
            return best_line

        return Page.closest_line_by_midpoint(lines, center_y, fallback_line)

    @staticmethod
    def closest_line_by_midpoint(
        lines: list[Block],
        midpoint_y: float | None,
        fallback_line: Block,
    ) -> Block:
        """Choose the line whose vertical midpoint is closest to *midpoint_y*."""
        if midpoint_y is None:
            return fallback_line

        closest_line = fallback_line
        closest_distance = float("inf")
        for line in lines:
            bbox = line.bounding_box
            if bbox is None or not bbox.has_usable_coordinates:
                continue
            distance = abs(bbox.vertical_midpoint - midpoint_y)
            if distance < closest_distance:
                closest_distance = distance
                closest_line = line

        return closest_line

    # ------------------------------------------------------------------
    # Page finalization and block tree manipulation
    # ------------------------------------------------------------------

    @staticmethod
    def _is_geometry_normalization_error(error: Exception) -> bool:
        """Return True for known malformed-bbox normalization failures."""
        return BoundingBox.is_geometry_normalization_error(error)

    def finalize_page_structure(self) -> None:
        """Run cleanup/recompute hooks after structural edits.

        Prunes empty items and recomputes nested bounding boxes.
        """
        self._remove_empty_items_safely()

        try:
            Page._recompute_nested_bounding_boxes(self)
        except Exception as recompute_error:
            if not self._is_geometry_normalization_error(recompute_error):
                raise
            logger.warning(
                "Skipped nested bbox recompute due to malformed geometry: %s",
                recompute_error,
            )
            self._recompute_paragraph_bboxes()

        try:
            self.recompute_bounding_box()
        except Exception as recompute_error:
            if not self._is_geometry_normalization_error(recompute_error):
                raise
            logger.warning(
                "Skipped page bbox recompute due to malformed geometry: %s",
                recompute_error,
            )

    @staticmethod
    def _recompute_nested_bounding_boxes(
        container: "Page | Block",
    ) -> None:
        """Recursively recompute bounding boxes bottom-up for nested blocks."""
        for child in container.items:
            if isinstance(child, Block):
                Page._recompute_nested_bounding_boxes(child)
        container.recompute_bounding_box()

    def find_parent_block(
        self,
        target: Block,
    ) -> "Page | Block | None":
        """Find parent block/page that directly contains target in its child items."""
        return Page._find_parent_block_recursive(self, target)

    @staticmethod
    def _find_parent_block_recursive(
        container: "Page | Block",
        target: Block,
    ) -> "Page | Block | None":
        if target in container.items:
            return container
        for child in container.items:
            if isinstance(child, Block):
                parent = Page._find_parent_block_recursive(child, target)
                if parent is not None:
                    return parent
        return None

    def remove_nested_block(self, target: Block) -> bool:
        """Remove target from nested page/block hierarchy if present."""
        return Page._remove_nested_block_recursive(self, target)

    @classmethod
    def _remove_nested_block_recursive(
        cls,
        container: "Page | Block",
        target: Block,
    ) -> bool:
        if target in container.items:
            try:
                container.remove_item(target)
                return True
            except Exception as removal_error:
                if not cls._is_geometry_normalization_error(removal_error):
                    raise
                logger.warning(
                    "remove_item fallback for malformed geometry on %s: %s",
                    type(container).__name__,
                    removal_error,
                )
                return Page._remove_item_without_recompute(container, target)

        for child in list(container.items):
            if isinstance(child, Block) and cls._remove_nested_block_recursive(
                child, target
            ):
                return True
        return False

    @staticmethod
    def _remove_item_without_recompute(
        container: "Page | Block",
        target: "Block | Word",
    ) -> bool:
        """Best-effort item removal when remove_item triggers malformed bbox
        recompute errors."""
        items = list(container.items)
        if target not in items:
            return False
        updated_items = [item for item in items if item is not target]
        container._items = updated_items
        return True

    def _remove_empty_items_safely(self) -> None:
        """Best-effort empty-item pruning that tolerates malformed geometry
        recompute errors."""
        try:
            self.remove_empty_items()
        except Exception as error:
            if not self._is_geometry_normalization_error(error):
                raise
            logger.warning(
                "Skipped remove_empty_items due to malformed geometry: %s",
                error,
            )

        Page._prune_empty_blocks_fallback(self)

    @staticmethod
    def _prune_empty_blocks_fallback(
        container: "Page | Block",
    ) -> None:
        """Recursively remove empty line/paragraph blocks from nested items
        lists."""
        child_items = list(container.items)
        if not child_items:
            return

        kept_items: list["Block | Word"] = []
        changed = False
        for child in child_items:
            if isinstance(child, Block):
                Page._prune_empty_blocks_fallback(child)

            if child.is_empty:
                changed = True
                continue

            kept_items.append(child)

        if not changed:
            return

        container._items = kept_items

    def replace_block_with_split_paragraphs(
        self,
        paragraph: Block,
        paragraph_lines: list[Block],
    ) -> bool:
        """Replace a paragraph with one paragraph per line."""
        parent = self.find_parent_block(paragraph)
        if parent is None:
            return False
        parent.remove_item(paragraph)
        for line in paragraph_lines:
            new_paragraph = Block(
                items=[line],
                block_category=BlockCategory.PARAGRAPH,
            )
            parent.add_item(new_paragraph)
        return True

    def _recompute_paragraph_bboxes(self) -> None:
        """Best-effort paragraph bbox recompute."""
        try:
            paragraphs = self.paragraphs
        except (AttributeError, TypeError):
            return
        for paragraph in paragraphs:
            try:
                paragraph.recompute_bounding_box()
            except Exception:
                logger.debug(
                    "Paragraph bbox recompute fallback skipped for %s",
                    type(paragraph).__name__,
                    exc_info=True,
                )

    @staticmethod
    def first_usable_bbox(
        bbox_candidates: list[BoundingBox | None],
    ) -> BoundingBox | None:
        """Return first bbox candidate that can be rendered in overlays."""
        for bbox in bbox_candidates:
            if bbox is not None and bbox.has_usable_coordinates:
                return bbox
        return None

    # ------------------------------------------------------------------
    # Paragraph operations
    # ------------------------------------------------------------------

    def merge_paragraphs(self, paragraph_indices: list[int]) -> bool:
        """Merge selected paragraphs into the first selected paragraph."""
        try:
            paragraphs = list(self.paragraphs)
            paragraph_count_before = len(paragraphs)

            logger.debug(
                "merge_paragraphs start: page_type=%s, paragraph_count=%d, "
                "requested=%s",
                type(self).__name__,
                paragraph_count_before,
                paragraph_indices,
            )

            unique_indices = sorted(set(paragraph_indices or []))
            if len(unique_indices) < 2:
                logger.warning(
                    "Paragraph merge requires selecting at least two paragraphs"
                )
                return False

            for index in unique_indices:
                if index < 0 or index >= paragraph_count_before:
                    logger.warning(
                        "Paragraph index %s out of range (0-%s)",
                        index,
                        paragraph_count_before - 1,
                    )
                    return False

            primary_index = unique_indices[0]
            primary_paragraph = paragraphs[primary_index]

            for index in unique_indices[1:]:
                primary_paragraph.merge(paragraphs[index])

            for index in reversed(unique_indices[1:]):
                if not self.remove_nested_block(paragraphs[index]):
                    logger.warning(
                        "Failed to remove merged paragraph at index %s", index
                    )
                    return False

            self.remove_empty_items()
            self.recompute_bounding_box()

            paragraph_count_after = len(self.paragraphs)
            logger.info(
                "Merged %d paragraphs into paragraph %d (paragraph_count %d -> %d)",
                len(unique_indices),
                primary_index,
                paragraph_count_before,
                paragraph_count_after,
            )
            return True

        except Exception as e:
            logger.exception("Error merging paragraphs %s: %s", paragraph_indices, e)
            return False

    def delete_paragraphs(self, paragraph_indices: list[int]) -> bool:
        """Delete selected paragraphs from the page."""
        try:
            paragraphs = list(self.paragraphs)
            paragraph_count_before = len(paragraphs)

            unique_indices = sorted(set(paragraph_indices or []))
            if not unique_indices:
                logger.warning("Paragraph deletion requires selecting at least one")
                return False

            for index in unique_indices:
                if index < 0 or index >= paragraph_count_before:
                    logger.warning(
                        "Paragraph index %s out of range (0-%s)",
                        index,
                        paragraph_count_before - 1,
                    )
                    return False

            for index in reversed(unique_indices):
                if not self.remove_nested_block(paragraphs[index]):
                    logger.warning(
                        "Failed to remove paragraph at index %s during deletion",
                        index,
                    )
                    return False

            self.remove_empty_items()
            self.recompute_bounding_box()

            paragraph_count_after = len(self.paragraphs)
            logger.info(
                "Deleted %d paragraphs (paragraph_count %d -> %d)",
                len(unique_indices),
                paragraph_count_before,
                paragraph_count_after,
            )
            return True

        except Exception as e:
            logger.exception("Error deleting paragraphs %s: %s", paragraph_indices, e)
            return False

    def split_paragraphs(self, paragraph_indices: list[int]) -> bool:
        """Split selected paragraphs into one paragraph per line."""
        try:
            paragraphs = list(self.paragraphs)
            paragraph_count_before = len(paragraphs)

            logger.debug(
                "split_paragraphs start: page_type=%s, paragraph_count=%d, "
                "requested=%s",
                type(self).__name__,
                paragraph_count_before,
                paragraph_indices,
            )

            unique_indices = sorted(set(paragraph_indices or []))
            if not unique_indices:
                logger.warning(
                    "Paragraph split requires selecting at least one paragraph"
                )
                return False

            for index in unique_indices:
                if index < 0 or index >= paragraph_count_before:
                    logger.warning(
                        "Paragraph index %s out of range (0-%s)",
                        index,
                        paragraph_count_before - 1,
                    )
                    return False

            changed = False
            for index in reversed(unique_indices):
                paragraph = paragraphs[index]
                paragraph_lines = list(paragraph.lines)
                if len(paragraph_lines) < 2:
                    logger.debug(
                        "Skipping paragraph %s split; requires at least 2 lines",
                        index,
                    )
                    continue

                if not self.replace_block_with_split_paragraphs(
                    paragraph,
                    paragraph_lines,
                ):
                    logger.warning("Unable to split paragraph index %s", index)
                    continue
                changed = True

            if not changed:
                logger.info("No selected paragraphs were split")
                return False

            self.remove_empty_items()
            self.recompute_bounding_box()

            paragraph_count_after = len(self.paragraphs)
            logger.info(
                "Split selected paragraphs (paragraph_count %d -> %d)",
                paragraph_count_before,
                paragraph_count_after,
            )
            return True

        except Exception as e:
            logger.exception("Error splitting paragraphs %s: %s", paragraph_indices, e)
            return False

    def split_paragraph_after_line(self, line_index: int) -> bool:
        """Split the containing paragraph immediately after the selected
        line."""
        try:
            lines = list(self.lines)
            if line_index < 0 or line_index >= len(lines):
                logger.warning(
                    "Line index %s out of range for paragraph split (0-%s)",
                    line_index,
                    len(lines) - 1,
                )
                return False

            selected_line = lines[line_index]
            paragraphs = list(self.paragraphs)
            target_paragraph = None
            target_paragraph_lines: list[Block] = []

            for paragraph in paragraphs:
                paragraph_lines = list(paragraph.lines)
                if selected_line in paragraph_lines:
                    target_paragraph = paragraph
                    target_paragraph_lines = paragraph_lines
                    break

            if target_paragraph is None:
                logger.warning(
                    "Unable to find paragraph containing line index %s",
                    line_index,
                )
                return False

            split_offset = target_paragraph_lines.index(selected_line)
            if split_offset >= len(target_paragraph_lines) - 1:
                logger.warning(
                    "Cannot split paragraph after last line (line index %s)",
                    line_index,
                )
                return False

            first_lines = target_paragraph_lines[: split_offset + 1]
            second_lines = target_paragraph_lines[split_offset + 1 :]
            if not first_lines or not second_lines:
                logger.warning(
                    "Paragraph split produced empty segment(s) for line index %s",
                    line_index,
                )
                return False

            parent = self.find_parent_block(target_paragraph)
            if parent is None:
                logger.warning(
                    "Unable to locate parent block for paragraph split after line %s",
                    line_index,
                )
                return False

            current_items = list(parent.items)
            if target_paragraph not in current_items:
                logger.warning(
                    "Target paragraph not found in parent items for line index %s",
                    line_index,
                )
                return False

            paragraph_idx = current_items.index(target_paragraph)
            replacement = [
                Block(
                    items=first_lines,
                    block_category=BlockCategory.PARAGRAPH,
                ),
                Block(
                    items=second_lines,
                    block_category=BlockCategory.PARAGRAPH,
                ),
            ]
            parent.items = (
                current_items[:paragraph_idx]
                + replacement
                + current_items[paragraph_idx + 1 :]
            )

            self.remove_empty_items()
            self.recompute_bounding_box()

            logger.info("Split paragraph after line index %s", line_index)
            return True

        except Exception as e:
            logger.exception(
                "Error splitting paragraph after line index %s: %s",
                line_index,
                e,
            )
            return False

    def split_paragraph_with_selected_lines(
        self,
        line_indices: list[int],
    ) -> bool:
        """Split a paragraph into selected lines and unselected lines."""
        try:
            lines = list(self.lines)
            unique_indices = sorted(set(line_indices or []))
            if not unique_indices:
                logger.warning(
                    "Split-by-selected-lines requires at least one selected line"
                )
                return False

            for line_index in unique_indices:
                if line_index < 0 or line_index >= len(lines):
                    logger.warning(
                        "Line index %s out of range for split-by-selected-lines (0-%s)",
                        line_index,
                        len(lines) - 1,
                    )
                    return False

            selected_lines = [lines[line_index] for line_index in unique_indices]
            paragraphs = list(self.paragraphs)
            target_paragraph = None
            target_paragraph_lines: list[Block] = []

            for paragraph in paragraphs:
                paragraph_lines = list(paragraph.lines)
                if any(line in paragraph_lines for line in selected_lines):
                    target_paragraph = paragraph
                    target_paragraph_lines = paragraph_lines
                    break

            if target_paragraph is None:
                logger.warning(
                    "Unable to find paragraph containing selected lines %s",
                    unique_indices,
                )
                return False

            if not all(line in target_paragraph_lines for line in selected_lines):
                logger.warning(
                    "Selected lines %s span multiple paragraphs; "
                    "split requires one paragraph",
                    unique_indices,
                )
                return False

            selected_line_set = set(selected_lines)
            selected_paragraph_lines = [
                line for line in target_paragraph_lines if line in selected_line_set
            ]
            unselected_paragraph_lines = [
                line for line in target_paragraph_lines if line not in selected_line_set
            ]

            if not selected_paragraph_lines or not unselected_paragraph_lines:
                logger.warning(
                    "Split-by-selected-lines requires selecting a "
                    "strict subset of a paragraph"
                )
                return False

            parent = self.find_parent_block(target_paragraph)
            if parent is None:
                logger.warning(
                    "Unable to locate parent block for split-by-selected-lines %s",
                    unique_indices,
                )
                return False

            current_items = list(parent.items)
            if target_paragraph not in current_items:
                logger.warning(
                    "Target paragraph missing in parent items for selected lines %s",
                    unique_indices,
                )
                return False

            paragraph_idx = current_items.index(target_paragraph)
            replacement = [
                Block(
                    items=selected_paragraph_lines,
                    block_category=BlockCategory.PARAGRAPH,
                ),
                Block(
                    items=unselected_paragraph_lines,
                    block_category=BlockCategory.PARAGRAPH,
                ),
            ]
            parent.items = (
                current_items[:paragraph_idx]
                + replacement
                + current_items[paragraph_idx + 1 :]
            )

            self.remove_empty_items()
            self.recompute_bounding_box()

            logger.info(
                "Split paragraph by selected lines %s into selected/unselected groups",
                unique_indices,
            )
            return True

        except Exception as e:
            logger.exception(
                "Error splitting paragraph with selected lines %s: %s",
                line_indices,
                e,
            )
            return False

    def group_selected_words_into_new_paragraph(
        self,
        word_keys: list[tuple[int, int]],
    ) -> bool:
        """Move selected words into a newly created paragraph.

        For each affected source line, selected words are moved to one
        new line in the new paragraph while unselected words remain in
        the original line.
        """
        from pd_book_tools.ocr.block import BlockChildType

        unique_keys = sorted(set(word_keys or []))
        if not unique_keys:
            logger.warning("Group-selected-words requires at least one selected word")
            return False

        try:
            lines = list(self.lines)
            paragraphs = list(self.paragraphs)

            line_to_selected_word_indices: dict[int, set[int]] = {}
            for line_index, word_index in unique_keys:
                if line_index < 0 or line_index >= len(lines):
                    logger.warning(
                        "Word key (%s, %s) line index out of range (0-%s)",
                        line_index,
                        word_index,
                        len(lines) - 1,
                    )
                    return False
                line_to_selected_word_indices.setdefault(line_index, set()).add(
                    word_index
                )

            target_lines = [
                lines[line_index]
                for line_index in sorted(line_to_selected_word_indices)
            ]

            paragraph_for_line: dict[Block, Block] = {}
            for line in target_lines:
                containing_paragraph = None
                for paragraph in paragraphs:
                    paragraph_lines = list(paragraph.lines)
                    if line in paragraph_lines:
                        containing_paragraph = paragraph
                        break
                if containing_paragraph is None:
                    logger.warning(
                        "Unable to find paragraph containing selected words %s",
                        unique_keys,
                    )
                    return False
                paragraph_for_line[line] = containing_paragraph

            affected_paragraphs: list[Block] = []
            for paragraph in paragraphs:
                if any(
                    paragraph_for_line.get(line) is paragraph for line in target_lines
                ):
                    affected_paragraphs.append(paragraph)

            if not affected_paragraphs:
                logger.warning(
                    "Unable to determine affected paragraphs for selected words %s",
                    unique_keys,
                )
                return False

            selected_lines_for_new_paragraph: list[Block] = []
            selected_line_bbox_fallbacks: list[object] = []
            for line_index in sorted(line_to_selected_word_indices):
                selected_word_indices = line_to_selected_word_indices[line_index]
                source_line = lines[line_index]
                line_words = list(source_line.words)
                source_line_original_bbox = source_line.bounding_box

                for wi in selected_word_indices:
                    if wi < 0 or wi >= len(line_words):
                        logger.warning(
                            "Word index %s out of range for line %s (0-%s)",
                            wi,
                            line_index,
                            len(line_words) - 1,
                        )
                        return False

                selected_words = [
                    line_words[wi]
                    for wi in range(len(line_words))
                    if wi in selected_word_indices
                ]
                unselected_words = [
                    line_words[wi]
                    for wi in range(len(line_words))
                    if wi not in selected_word_indices
                ]

                if not selected_words:
                    logger.warning(
                        "Grouping requires at least one selected word for line %s",
                        line_index,
                    )
                    return False

                source_line.items = unselected_words
                source_line.unmatched_ground_truth_words = []
                try:
                    source_line.recompute_bounding_box()
                except Exception as recompute_error:
                    if not self._is_geometry_normalization_error(recompute_error):
                        raise
                    logger.warning(
                        "Skipped source line bbox recompute due to "
                        "malformed geometry on line %s: %s",
                        line_index,
                        recompute_error,
                    )

                if (
                    unselected_words
                    and not (
                        source_line.bounding_box is not None
                        and source_line.bounding_box.has_usable_coordinates
                    )
                    and (
                        source_line_original_bbox is not None
                        and source_line_original_bbox.has_usable_coordinates
                    )
                ):
                    source_line.bounding_box = source_line_original_bbox

                selected_line = Block(
                    items=selected_words,
                    bounding_box=source_line_original_bbox,
                    child_type=BlockChildType.WORDS,
                    block_category=BlockCategory.LINE,
                )
                try:
                    selected_line.recompute_bounding_box()
                except Exception as recompute_error:
                    if not self._is_geometry_normalization_error(recompute_error):
                        raise
                    logger.warning(
                        "Skipped selected line bbox recompute due to "
                        "malformed geometry on line %s: %s",
                        line_index,
                        recompute_error,
                    )

                if (
                    selected_line.bounding_box is not None
                    and selected_line.bounding_box.has_usable_coordinates
                ):
                    selected_line_bbox_fallbacks.append(selected_line.bounding_box)
                elif (
                    source_line_original_bbox is not None
                    and source_line_original_bbox.has_usable_coordinates
                ):
                    selected_line.bounding_box = source_line_original_bbox
                    selected_line_bbox_fallbacks.append(source_line_original_bbox)
                selected_lines_for_new_paragraph.append(selected_line)

            if not selected_lines_for_new_paragraph:
                logger.warning("No selected words available to group into paragraph")
                return False

            new_paragraph = Block(
                items=selected_lines_for_new_paragraph,
                bounding_box=Page.first_usable_bbox(
                    selected_line_bbox_fallbacks
                    + [paragraph.bounding_box for paragraph in affected_paragraphs]
                ),
                child_type=BlockChildType.BLOCKS,
                block_category=BlockCategory.PARAGRAPH,
            )

            page_items = list(self.items)
            self.items = page_items + [new_paragraph]

            self.finalize_page_structure()

            if not (
                new_paragraph.bounding_box is not None
                and new_paragraph.bounding_box.has_usable_coordinates
            ):
                fallback_bbox = Page.first_usable_bbox(
                    selected_line_bbox_fallbacks
                    + [paragraph.bounding_box for paragraph in affected_paragraphs]
                )
                if fallback_bbox is not None:
                    new_paragraph.bounding_box = fallback_bbox

            logger.info(
                "Grouped selected words %s into new paragraph with %d line(s)",
                unique_keys,
                len(selected_lines_for_new_paragraph),
            )
            return True
        except Exception as e:
            logger.exception(
                "Error grouping selected words %s into paragraph: %s",
                unique_keys,
                e,
            )
            return False

    # ------------------------------------------------------------------
    # Bbox operations – shared helpers
    # ------------------------------------------------------------------

    def _apply_to_word_keys(
        self,
        word_keys: list[tuple[int, int]],
        operation: Callable[[Word], bool],
        label: str,
    ) -> bool:
        """Validate word keys and apply *operation* to each word."""
        unique_keys = sorted(set(word_keys or []))
        if not unique_keys:
            logger.warning("%s requires selecting at least one word", label)
            return False
        try:
            changed = False
            for line_index, word_index in unique_keys:
                line_words = self.validated_line_words(line_index)
                if line_words is None:
                    return False
                if word_index < 0 or word_index >= len(line_words):
                    logger.warning(
                        "%s word index %s out of range for line %s (0-%s)",
                        label,
                        word_index,
                        line_index,
                        len(line_words) - 1,
                    )
                    return False
                changed = operation(line_words[word_index]) or changed
            if not changed:
                logger.warning("Selected words could not be processed (%s)", label)
                return False
            self.finalize_page_structure()
            logger.info("%s %d selected words", label, len(unique_keys))
            return True
        except Exception as e:
            logger.exception("Error in %s for words %s: %s", label, word_keys, e)
            return False

    def _apply_to_line_indices(
        self,
        line_indices: list[int],
        operation: Callable[[Block], bool],
        label: str,
    ) -> bool:
        """Validate line indices and apply *operation* to each line."""
        unique_indices = sorted(set(line_indices or []))
        if not unique_indices:
            logger.warning("%s requires selecting at least one line", label)
            return False
        try:
            lines = list(self.lines)
            changed = False
            for line_index in unique_indices:
                if line_index < 0 or line_index >= len(lines):
                    logger.warning(
                        "%s line index %s out of range (0-%s)",
                        label,
                        line_index,
                        len(lines) - 1,
                    )
                    return False
                changed = operation(lines[line_index]) or changed
            if not changed:
                logger.warning("Selected lines could not be processed (%s)", label)
                return False
            self.finalize_page_structure()
            logger.info("%s %d selected lines", label, len(unique_indices))
            return True
        except Exception as e:
            logger.exception("Error in %s for lines %s: %s", label, line_indices, e)
            return False

    def _apply_to_paragraph_indices(
        self,
        paragraph_indices: list[int],
        operation: Callable[[Block], bool],
        label: str,
    ) -> bool:
        """Validate paragraph indices and apply *operation* to each paragraph."""
        unique_indices = sorted(set(paragraph_indices or []))
        if not unique_indices:
            logger.warning("%s requires selecting at least one paragraph", label)
            return False
        try:
            paragraphs = list(self.paragraphs)
            if not paragraphs:
                logger.warning("Page has no paragraphs (%s)", label)
                return False
            changed = False
            for paragraph_index in unique_indices:
                if paragraph_index < 0 or paragraph_index >= len(paragraphs):
                    logger.warning(
                        "%s paragraph index %s out of range (0-%s)",
                        label,
                        paragraph_index,
                        len(paragraphs) - 1,
                    )
                    return False
                changed = operation(paragraphs[paragraph_index]) or changed
            if not changed:
                logger.warning("Selected paragraphs could not be processed (%s)", label)
                return False
            self.finalize_page_structure()
            logger.info("%s %d selected paragraphs", label, len(unique_indices))
            return True
        except Exception as e:
            logger.exception(
                "Error in %s for paragraphs %s: %s", label, paragraph_indices, e
            )
            return False

    # ------------------------------------------------------------------
    # Bbox operations – word level
    # ------------------------------------------------------------------

    def refine_words(self, word_keys: list[tuple[int, int]]) -> bool:
        """Refine selected word bounding boxes."""
        return self._apply_to_word_keys(
            word_keys,
            lambda w: w.refine_bbox(self.cv2_numpy_page_image),
            "Refined",
        )

    def expand_then_refine_words(self, word_keys: list[tuple[int, int]]) -> bool:
        """Expand then refine selected word bounding boxes."""
        return self._apply_to_word_keys(
            word_keys,
            lambda w: w.expand_then_refine_bbox(self.cv2_numpy_page_image),
            "Expand-then-refined",
        )

    def expand_word_bboxes(
        self, word_keys: list[tuple[int, int]], padding_px: float = 2.0
    ) -> bool:
        """Expand selected word bounding boxes by uniform pixel padding."""
        page_width, page_height = self.resolved_dimensions
        return self._apply_to_word_keys(
            word_keys,
            lambda w: w.expand_bbox(padding_px, page_width, page_height),
            "Expanded bboxes for",
        )

    # ------------------------------------------------------------------
    # Bbox operations – line level
    # ------------------------------------------------------------------

    def refine_lines(self, line_indices: list[int]) -> bool:
        """Refine all words/bboxes in selected lines."""
        return self._apply_to_line_indices(
            line_indices,
            lambda line: line.refine_word_bboxes(self.cv2_numpy_page_image),
            "Refined",
        )

    def expand_then_refine_lines(self, line_indices: list[int]) -> bool:
        """Expand then refine all words/bboxes in selected lines."""

        def _op(line: Block) -> bool:
            changed = False
            for word in line.words:
                changed = (
                    word.expand_then_refine_bbox(self.cv2_numpy_page_image) or changed
                )
            line.recompute_bounding_box()
            return changed

        return self._apply_to_line_indices(line_indices, _op, "Expand-then-refined")

    def expand_line_bboxes(
        self, line_indices: list[int], padding_px: float = 2.0
    ) -> bool:
        """Expand all word bboxes in selected lines by uniform pixel padding."""
        page_width, page_height = self.resolved_dimensions

        def _op(line: Block) -> bool:
            changed = False
            for word in line.words:
                changed = (
                    word.expand_bbox(padding_px, page_width, page_height) or changed
                )
            line.recompute_bounding_box()
            return changed

        return self._apply_to_line_indices(line_indices, _op, "Expanded bboxes in")

    # ------------------------------------------------------------------
    # Bbox operations – paragraph level
    # ------------------------------------------------------------------

    def refine_paragraphs(self, paragraph_indices: list[int]) -> bool:
        """Refine all words/bboxes in selected paragraphs."""

        def _op(paragraph: Block) -> bool:
            changed = False
            for line in paragraph.lines:
                changed = line.refine_word_bboxes(self.cv2_numpy_page_image) or changed
            paragraph.recompute_bounding_box()
            return changed

        return self._apply_to_paragraph_indices(paragraph_indices, _op, "Refined")

    def expand_then_refine_paragraphs(self, paragraph_indices: list[int]) -> bool:
        """Expand then refine all words/bboxes in selected paragraphs."""

        def _op(paragraph: Block) -> bool:
            changed = False
            for line in paragraph.lines:
                for word in line.words:
                    changed = (
                        word.expand_then_refine_bbox(self.cv2_numpy_page_image)
                        or changed
                    )
                line.recompute_bounding_box()
            paragraph.recompute_bounding_box()
            return changed

        return self._apply_to_paragraph_indices(
            paragraph_indices, _op, "Expand-then-refined"
        )

    def expand_paragraph_bboxes(
        self, paragraph_indices: list[int], padding_px: float = 2.0
    ) -> bool:
        """Expand all word bboxes in selected paragraphs by uniform pixel padding."""
        page_width, page_height = self.resolved_dimensions

        def _op(paragraph: Block) -> bool:
            changed = False
            for line in paragraph.lines:
                for word in line.words:
                    changed = (
                        word.expand_bbox(padding_px, page_width, page_height) or changed
                    )
                line.recompute_bounding_box()
            paragraph.recompute_bounding_box()
            return changed

        return self._apply_to_paragraph_indices(
            paragraph_indices, _op, "Expanded bboxes in"
        )

    def scale(self, width: int, height: int) -> "Page":
        """
        Return new page with scaled bounding box
        to absolute pixel coordinates
        """
        return Page(
            width=width,
            height=height,
            page_index=self.page_index,
            items=[item.scale(width, height) for item in self.items],
            bounding_box=self.bounding_box.scale(width, height)
            if self.bounding_box
            else None,
            page_labels=self.page_labels,
            ocr_provenance=self.ocr_provenance,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary"""
        result: Dict[str, Any] = {
            "type": "Page",
            "width": self.width,
            "height": self.height,
            "page_index": self.page_index,
            "bounding_box": self.bounding_box.to_dict() if self.bounding_box else None,
            "items": [item.to_dict() for item in self.items] if self.items else [],
            "ocr_provenance": (
                self.ocr_provenance.to_dict()
                if self.ocr_provenance is not None
                else None
            ),
        }
        # Include metadata fields when set (omit defaults for compact output)
        if self.image_path is not None:
            result["image_path"] = str(self.image_path)
        if self.name is not None:
            result["name"] = self.name
        if self.source != "ocr":
            result["source"] = self.source
        if self.ocr_failed:
            result["ocr_failed"] = self.ocr_failed
        if self.provenance_live_ocr is not None:
            result["provenance_live_ocr"] = self.provenance_live_ocr
        if self.provenance_saved_ocr is not None:
            result["provenance_saved_ocr"] = self.provenance_saved_ocr
        if self.provenance_saved is not None:
            result["provenance_saved"] = self.provenance_saved
        return result

    def copy(self) -> "Page":
        # Copy the page to a new object via serialization/deserialization
        return self.from_dict(self.to_dict())

    def reorganize_page(self):
        """
        Reogranize the page into paragraphs and blocks.
        This is a post-processing step to ensure that the text is
        organized into logical sections for text generated output.
        """
        logger.debug("Reorganizing Page")

        # Merge lines for each block if they didn't get recognzied together
        for block in self.items:
            self.reorganize_lines(block)

        row_blocks = self.compute_text_row_blocks(self.lines)

        # TODO: Add logic to detect and handle multiple columns of text

        if not row_blocks or len(row_blocks.items) == 0:
            logger.debug("No blocks to reorganize")
            return

        # Recompute lines within blocks
        for block in row_blocks.items:
            # Recompute lines for each paragraph block
            self.reorganize_lines(block)

        reset_paragraph_blocks = []

        # Reoragnize into paragraph blocks
        for b in list(row_blocks.items):
            paragraph_blocks = self.compute_text_paragraph_blocks(b.lines)
            reset_paragraph_blocks.append(paragraph_blocks)
        self.items = reset_paragraph_blocks

        paragraph_blocks = self.paragraphs

        logger.debug(
            "Page Block Count after adding paragraphs:" + str(len(paragraph_blocks))
        )
        self.refresh_page_images()

    def add_ground_truth(self, text: str):
        update_page_with_ground_truth_text(self, text)
        self.refresh_page_images()

    def remove_ground_truth(self):
        """Remove ground truth text from the page"""
        for item in self.items:
            item.remove_ground_truth()
        if self.unmatched_ground_truth_lines:
            self.unmatched_ground_truth_lines.clear()
        else:
            self.unmatched_ground_truth_lines = []
        self.refresh_page_images()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Page":
        """Create OCRPage from dictionary"""
        # Resolve source from either "source" or legacy "page_source" key
        source = data.get("source", data.get("page_source", "ocr"))
        return cls(
            items=[Block.from_dict(block) for block in data["items"]],
            width=data["width"],
            height=data["height"],
            page_index=data["page_index"],
            bounding_box=(
                BoundingBox.from_dict(data["bounding_box"])
                if data.get("bounding_box")
                else None
            ),
            ocr_provenance=data.get("ocr_provenance"),
            image_path=data.get("image_path"),
            name=data.get("name"),
            source=source,
            ocr_failed=data.get("ocr_failed", False),
            provenance_live_ocr=data.get("provenance_live_ocr"),
            provenance_saved_ocr=data.get("provenance_saved_ocr"),
            provenance_saved=data.get("provenance_saved"),
        )

    @classmethod
    def _reorganize_lines_log_debug_lines(cls, message, line1text, line2text):
        logger.debug(
            message
            + "\nFirst line: "
            + str(line1text[0:10] + ("..." if len(line1text) > 10 else ""))
            + "\nSecond line: "
            + str(line2text[0:10] + ("..." if len(line2text) > 10 else ""))
        )

    @classmethod
    def _reorganize_lines_check_overlap(cls, line: Block, next_line: Block):
        # TODO move this to the Block class

        if not line.bounding_box:
            cls._reorganize_lines_log_debug_lines(
                "First Line has no bounding box.",
                line.text,
                next_line.text,
            )
            return False
        if not next_line.bounding_box:
            cls._reorganize_lines_log_debug_lines(
                "Second Line has no bounding box.",
                line.text,
                next_line.text,
            )
            return False

        y_overlap_h = line.bounding_box.overlap_y_amount(next_line.bounding_box)
        x_overlap_w = line.bounding_box.overlap_x_amount(next_line.bounding_box)

        overlap_not_ok = False
        if y_overlap_h < (
            0.4 * (np_mean([line.bounding_box.height, next_line.bounding_box.height]))
        ):
            cls._reorganize_lines_log_debug_lines(
                f"Lines not overlapping on Y axis enough. Overlap is {y_overlap_h}",
                line.text,
                next_line.text,
            )
            overlap_not_ok = True

        if x_overlap_w > (0.1 * line.bounding_box.width):
            cls._reorganize_lines_log_debug_lines(
                f"Lines overlapping on X axis too much. Overlap is {x_overlap_w}",
                line.text,
                next_line.text,
            )
            overlap_not_ok = True
        return overlap_not_ok

    @classmethod
    def reorganize_lines(cls, block: Block):
        """
        # TODO move this to the Block class

        Reorganizes the lines of text in a given paragraph.
        In some cases the OCR accidently creates two lines
        in a single block for a single line of text

        This is not for multi-column layouts where lines are clearly delineated
        with a margin of space along all lines

        Use hueristics of surrounding text to determine if two lines really should be one
        """
        if not block.items:
            return
        lines: List[Block] = block.items
        if not all(hasattr(line, "block_category") for line in lines) and not all(
            line.block_category == BlockCategory.LINE for line in lines
        ):
            raise TypeError("All items in lines must have a block_category of LINE")

        logger.debug("Recomputing lines for block " + str(block.text[0:10] + "..."))

        # Iterate through each line, finding "nearly adjacent" lines on X axis
        if len(lines) < 2:
            # If only one line, no need to recompute
            return

        median_line_width = np_median(
            [line.bounding_box.width if line.bounding_box else 0 for line in lines]
        )

        i = -1
        while True:
            i = i + 1
            # this is being mutated, get it each time through the loop
            lines: List[Block] = block.items

            if i >= len(lines) - 1:
                break

            line: Block = lines[i]
            next_line: Block = lines[i + 1]

            if cls._reorganize_lines_check_overlap(line, next_line):
                continue

            if not line.bounding_box or not next_line.bounding_box:
                continue

            # Only check lines that are "approximately" the same height (to account for drop-caps)
            # use a 10% height tolerance
            logger.debug("line.bounding_box.height: " + str(line.bounding_box.height))
            logger.debug(
                "next_line.bounding_box.height: " + str(next_line.bounding_box.height)
            )
            logger.debug(
                "Height difference: "
                + str(abs(line.bounding_box.height - next_line.bounding_box.height))
            )
            logger.debug("Tolerance: " + str(0.50 * line.bounding_box.height))
            if abs(line.bounding_box.height - next_line.bounding_box.height) > (
                0.50 * line.bounding_box.height
            ):
                cls._reorganize_lines_log_debug_lines(
                    "Line height difference too large.", line.text, next_line.text
                )
                continue

            # Figure out which line should come "first" and reorder them
            if line.bounding_box.minX > next_line.bounding_box.minX:
                line, next_line = next_line, line

            if not line.bounding_box or not next_line.bounding_box:
                continue

            # Compute X space between lines
            x_space_between = max(
                next_line.bounding_box.minX - line.bounding_box.maxX, 0
            )

            # Compute 10% of line length of all lines in block
            ten_percent_median_line_length = median_line_width * 0.10
            if x_space_between < ten_percent_median_line_length:
                # Merge the two lines into one. Subtract 1 from the index
                # So that we can continue merging if there's more than two broken up lines
                cls._reorganize_lines_log_debug_lines(
                    "Merging Lines.", line.text, next_line.text
                )
                line.merge(next_line)
                block.remove_item(next_line)
                i = i - 1
                continue
            else:
                cls._reorganize_lines_log_debug_lines(
                    "Lines not split on X axis enough.", line.text, next_line.text
                )
                continue

    @classmethod
    def compute_text_row_blocks(cls, lines: List[Block], tolerance=None):
        """
        Use dynamic vertical spacing to group lines into "blocks" of text.

        This generally splits a page into logical sections
        like headers, body, blockquotes, and footers.

        After finding blocks, we can compute columns within each block.
        """
        logger.debug("Computing text row blocks")
        # Single Line Block
        if len(lines) == 0:
            return None
        # if len(lines) == 1:
        #     logger.debug("Only one line, no blocks to compute")
        #     b = Block(items=lines, block_category=BlockCategory.PARAGRAPH)
        #     new_block = Block(items=[b], block_category=BlockCategory.BLOCK)
        #     return new_block

        # Tolerance is 20% of average line height by default
        if tolerance is None:
            tolerance = 0.2 * np_mean(
                [line.bounding_box.height if line.bounding_box else 0 for line in lines]
            )

        logger.debug("Tolerance: " + str(tolerance))

        # Sort lines by their Y position
        lines.sort(key=lambda line: line.bounding_box.minY if line.bounding_box else 0)

        # Compute spacing after each line
        min_y_positions = [
            line.bounding_box.minY if line.bounding_box else 0 for line in lines
        ]
        max_y_positions = [
            line.bounding_box.maxY if line.bounding_box else 0 for line in lines
        ]

        # Compute difference between the max Y of the previous line and the min Y of the current line
        line_spacings = [
            max(0, min_y_positions[i] - max_y_positions[i - 1])
            for i in range(1, len(lines))
        ]

        # This gives us the spacing between lines, which we can use to determine
        # if they are part of the same block or not. "blocks" will be separated by
        # vertical gaps larger than the norm.

        # Use 1/2 of the standard deviation, or 15% of the avarage line height
        # as the tolerance for line spacing
        median_line_height_spacing = float(
            np_median(
                [line.bounding_box.height if line.bounding_box else 0 for line in lines]
            )
            * 0.10
        )
        logger.debug("Median Line Height Spacing: " + str(median_line_height_spacing))

        std_line_height_spacing = (
            float(np_std(line_spacings)) * 0.75 if line_spacings else 0.0
        )
        logger.debug(
            "Standard Deviation Line Height Spacing: " + str(std_line_height_spacing)
        )

        tolerance_spacing = tolerance + max(
            float(std_line_height_spacing), (median_line_height_spacing * 0.25)
        )
        logger.debug("Tolerance Spacing: " + str(tolerance_spacing))

        blocks = []
        current_block = [lines[0]]
        logger.debug("Starting Block: " + str(current_block[0].text[0:25] + "..."))
        for i in range(1, len(lines)):
            prev_line_space_after = max(line_spacings[i - 1], 0)
            logger.debug("Line: " + str(lines[i].text[0:25] + "..."))
            logger.debug("Previous line space after: " + str(prev_line_space_after))
            if prev_line_space_after >= 0 and prev_line_space_after > tolerance_spacing:
                b = Block(items=current_block, block_category=BlockCategory.PARAGRAPH)
                logger.debug("New Block: " + str(b.text[0:25] + "..."))
                blocks.append(b)
                current_block = [lines[i]]
            else:
                current_block.append(lines[i])

        # Final Block
        if current_block:
            b = Block(items=current_block, block_category=BlockCategory.PARAGRAPH)
            blocks.append(b)

        logger.debug("Block Count: " + str(len(blocks)))

        for block in blocks:
            logger.debug("Block: " + str(block.text[0:10] + "..."))

        new_block = Block(items=blocks, block_category=BlockCategory.BLOCK)
        return new_block

    @classmethod
    def compute_text_paragraph_blocks(cls, lines: List[Block]):
        logger.debug("Computing Paragraph Blocks")

        min_x_positions = [
            line.bounding_box.minX if line.bounding_box else 0 for line in lines
        ]
        max_x_positions = [
            line.bounding_box.maxX if line.bounding_box else 0 for line in lines
        ]

        median_line_length = np_median(
            [line.bounding_box.width if line.bounding_box else 0 for line in lines]
        )

        median_left_indent = np_median(min_x_positions)
        median_right_indent = np_median(max_x_positions)

        left_tolerance = 0.02 * median_line_length  # np.std(min_x_positions) * 2
        right_tolerance = 0.15 * median_line_length  # np.std(max_x_positions) * 2

        left_max = median_left_indent + left_tolerance
        right_min = median_right_indent - right_tolerance

        # def cluster_numbers(numbers, threshold):
        #     numbers.sort()
        #     clusters = [[numbers[0]]]

        #     for number in numbers[1:]:
        #         if abs(number - clusters[-1][-1]) <= threshold:
        #             clusters[-1].append(number)
        #         else:
        #             clusters.append([number])

        #     return clusters

        # TODO - Dramas & pages with lots of dialog are unique in that they
        # have many one-line indented paragraphs,
        # and as such often will have MORE lines that are indented than not.
        # Add clustering logic to detect this and handle it. Look for two similar
        # sets of left-aligned locations that are fairly close to each other
        # compared to the page width, and have multiple lines that match each.

        # Perform Clustering
        # left_clusters = cluster_numbers(min_x_positions, left_tolerance)

        blocks = []
        current_block = [lines[0]]
        logger.debug("First Paragraph" + str(current_block[0].text[0:10] + "..."))
        for i in range(1, len(lines)):
            # If previous line right indent is < median,
            #   previous line *might* be end of paragraph
            # If current line left indent is > median, start of paragraph

            prev_x_end_paragraph = max_x_positions[i - 1] <= right_min
            current_x_start_paragraph = min_x_positions[i] >= left_max

            if (prev_x_end_paragraph) or (current_x_start_paragraph):
                b = Block(items=current_block, block_category=BlockCategory.PARAGRAPH)
                logger.debug("New Paragraph: " + str(b.text[0:10] + "..."))
                blocks.append(b)
                current_block = [lines[i]]
            else:
                current_block.append(lines[i])

        # Final Block
        if current_block:
            b = Block(items=current_block, block_category=BlockCategory.PARAGRAPH)
            blocks.append(b)

        new_block = Block(items=blocks, block_category=BlockCategory.BLOCK)
        logger.debug("New Block Paragraph Count: " + str(len(new_block.items)))
        logger.debug("New Block Line Count: " + str(len(new_block.lines)))
        return new_block

    def recompute_bounding_box(self):
        """Recompute the bounding box of the page based on its items"""
        if not self.items:
            self.bounding_box = None
            logger.debug("No items in page to recompute bounding box")
            return
        self.bounding_box = BoundingBox.union(
            [item.bounding_box for item in self.items if item.bounding_box]
        )

    def refine_bounding_boxes(self, image: ndarray | None = None, padding_px: int = 0):
        if image is None:
            if hasattr(self, "cv2_numpy_page_image"):
                image = self.cv2_numpy_page_image
            else:
                raise ValueError(
                    "Image not provided and cv2_numpy_page_image is not set."
                )
        for item in self.items:
            item.refine_bounding_boxes(image, padding_px=padding_px)
        self.recompute_bounding_box()

    def generate_doctr_checks(self, output_path: pathlib.Path):
        if self.cv2_numpy_page_image is None:
            raise ValueError(
                "cv2_numpy_page_image is not set. Please set it before calling this method."
            )
        if not self.items:
            logger.info("No items in the page to process.")
            return

        if not output_path.parent.exists():
            raise ValueError(
                "Output path does not exist. Please create the parent directory first."
            )
        output_path.mkdir(parents=True, exist_ok=True)

    def generate_doctr_detection_training_set(
        self: "Page",
        output_path: pathlib.Path,
        prefix: str = "",
        word_filter: Optional[Callable[["Word"], bool]] = None,
    ) -> None:
        """
        Create a DocTR text detection training or validation set from a page
        image (matched_ocr data) and image bounding boxes.

        Parameters
        ----------
        output_path : pathlib.Path
            Root output directory.  A ``detection/`` subdirectory is created.
        prefix : str
            Prefix for exported image filenames.
        word_filter : callable, optional
            ``(Word) -> bool`` predicate. When provided, only words that
            return ``True`` contribute polygons to the detection labels.

        Result::

            Files:
            ├── detection
              ├── images
                ├──── <prefix>_<page_index>.png (image)
                └──── ...
              ├── labels.json

           Detection labels.json::

            {
                "image_path_1": {
                    'img_dimensions': (x, y),
                    'img_hash': "theimagedumpmyhash",
                    'polygons': [[[x10, y10], [x20, y20], [x30, y30], [x40, y40]], ...]
                }
            }
        """
        self.generate_doctr_checks(output_path)

        # Create the detection directory
        detection_path = pathlib.Path(output_path, "detection")
        detection_path.mkdir(parents=True, exist_ok=True)
        detection_image_path = pathlib.Path(detection_path, "images")
        detection_image_path.mkdir(parents=True, exist_ok=True)

        if self.cv2_numpy_page_image is None:
            raise ValueError(
                "cv2_numpy_page_image is not set. Please set it before calling this method."
            )
        image = cv2_cvtColor(self.cv2_numpy_page_image, cv2_COLOR_BGR2RGB)
        img_height, img_width, _ = image.shape

        detection_labels = {}

        image_name = "{}_{}.png".format(prefix, self.page_index)
        logger.debug("Writing image: " + str(image_name))
        cv2_imwrite(
            str(pathlib.Path(detection_image_path, image_name).resolve()),
            image,
            [int(cv2_IMWRITE_PNG_COMPRESSION), 9],
        )

        # compute sha-256 hash of the image file
        # read the image file back in as bytes
        with open(pathlib.Path(detection_image_path, image_name), "rb") as f:
            image_buffer = f.read()
            image_hash = sha256(image_buffer).hexdigest()

        words = self.words
        if word_filter is not None:
            words = [w for w in words if word_filter(w)]

        detection_labels[image_name] = {
            "img_dimensions": (img_width, img_height),
            "img_hash": image_hash,
            "polygons": [
                word.bounding_box.get_four_point_scaled_polygon_list(
                    img_width, img_height
                )
                for word in words
            ],
        }

        # Read in the JSON file and add the new labels
        try:
            with open(pathlib.Path(detection_path, "labels.json"), "r") as f:
                existing_detection_labels = json_load(f)
        except FileNotFoundError:
            # If the file doesn't exist, create an empty dictionary
            existing_detection_labels = {}

        # remove existing labels that have prefix + page index
        existing_detection_labels = {
            k: v
            for k, v in existing_detection_labels.items()
            if not k.startswith(f"{prefix}_{self.page_index}")
        }

        # Add the new labels to the existing labels
        detection_labels = {**existing_detection_labels, **detection_labels}

        # Write the labels to the JSON file
        with open(pathlib.Path(detection_path, "labels.json"), "w") as f:
            json_dump(detection_labels, f, indent=4, ensure_ascii=False)

    def generate_doctr_recognition_training_set(
        self: "Page",
        output_path: pathlib.Path,
        prefix: str = "",
        word_filter: Optional[Callable[["Word"], bool]] = None,
        label_formatter: Optional[Callable[["Word"], Any]] = None,
    ) -> None:
        """
        Create a text recognition training or validation set from a page
        image (matched_ocr data) and image bounding boxes.

        Parameters
        ----------
        output_path : pathlib.Path
            Root output directory.  A ``recognition/`` subdirectory is created.
        prefix : str
            Prefix for exported image filenames.
        word_filter : callable, optional
            ``(Word) -> bool`` predicate.  When provided, only words that
            return ``True`` are exported as recognition crops.
        label_formatter : callable, optional
            ``(Word) -> Any`` — custom label builder.  When provided, each
            word's label in ``labels.json`` is the return value of
            ``label_formatter(word)`` instead of ``word.ground_truth_text``.
            Words without ``ground_truth_text`` are still skipped unless a
            *label_formatter* is supplied.

        Result::

            Files:
            ├── recognition
              ├── images
                ├──── <prefix>_<page_index>_x1_x2_y1_y2.png
                └──── ...
              ├── labels.json

            Recognition labels.json::

            {
                "image_path_1": "<gt value>",
            }
        """
        self.generate_doctr_checks(output_path)

        # Create the recognition directory
        recognition_path = pathlib.Path(output_path, "recognition")
        recognition_path.mkdir(parents=True, exist_ok=True)
        recognition_image_path = pathlib.Path(recognition_path, "images")
        recognition_image_path.mkdir(parents=True, exist_ok=True)

        if self.cv2_numpy_page_image is None:
            raise ValueError(
                "cv2_numpy_page_image is not set. Please set it before calling this method."
            )
        image = cv2_cvtColor(self.cv2_numpy_page_image, cv2_COLOR_BGR2RGB)
        img_height, img_width, _ = image.shape

        words = self.words
        if word_filter is not None:
            words = [w for w in words if word_filter(w)]

        # Delete any existing images that match the prefix + page index in the output directory
        for file in recognition_image_path.glob(f"{prefix}_{self.page_index}_*"):
            if file.is_file():
                logger.debug("Deleting existing image: " + str(file))
                file.unlink()

        recognition_labels = {}

        for word in words:
            if label_formatter is not None:
                label = label_formatter(word)
            elif word.ground_truth_text:
                label = word.ground_truth_text
            else:
                logger.warning("Skipping word without ground truth text: %s", word.text)
                continue

            bb = word.bounding_box.scale(width=img_width, height=img_height)
            cropped_image = image[bb.minY : bb.maxY, bb.minX : bb.maxX]
            cropped_image_name = "{}_{}_{}_{}_{}_{}.png".format(
                prefix,
                self.page_index,
                bb.minX,
                bb.maxX,
                bb.minY,
                bb.maxY,
            )
            logger.debug("Writing image: " + str(cropped_image_name))
            cv2_imwrite(
                str(pathlib.Path(recognition_image_path, cropped_image_name).resolve()),
                cropped_image,
                [int(cv2_IMWRITE_PNG_COMPRESSION), 9],
            )
            recognition_labels[cropped_image_name] = label

        # Read in the JSON file and add the new labels
        try:
            with open(pathlib.Path(recognition_path, "labels.json"), "r") as f:
                existing_labels = json_load(f)
        except FileNotFoundError:
            # If the file doesn't exist, create an empty dictionary
            existing_labels = {}

        # remove existing labels that have prefix + page index
        existing_labels = {
            k: v
            for k, v in existing_labels.items()
            if not k.startswith(f"{prefix}_{self.page_index}_")
        }

        # Add the new labels to the existing labels
        recognition_labels = {**existing_labels, **recognition_labels}

        # Write the updated labels to the JSON file
        with open(pathlib.Path(recognition_path, "labels.json"), "w") as f:
            json_dump(recognition_labels, f, indent=4, ensure_ascii=False)

    def convert_to_training_set(
        self: "Page",
        output_path: pathlib.Path,
        prefix: str = "",
        word_filter: Optional[Callable[["Word"], bool]] = None,
    ) -> None:
        """
        Create recognition and detection training sets from a page image
        (matched_ocr data) and image bounding boxes.

        Parameters
        ----------
        output_path : pathlib.Path
            Root output directory.
        prefix : str
            Prefix for exported image filenames.
        word_filter : callable, optional
            ``(Word) -> bool`` predicate forwarded to both detection and
            recognition export methods.
        """
        self.generate_doctr_detection_training_set(
            output_path=output_path, prefix=prefix, word_filter=word_filter
        )
        self.generate_doctr_recognition_training_set(
            output_path=output_path, prefix=prefix, word_filter=word_filter
        )
