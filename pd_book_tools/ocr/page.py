import itertools
import pathlib
from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from json import dump as json_dump
from json import load as json_load
from logging import getLogger
from typing import Any, Collection, Dict, List, Optional, Tuple

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
    RED = (0, 0, 255)  # Red
    DARK_YELLOW = (0, 225, 225)  # Darker Yellow
    DARK_GREEN = (0, 128, 0)  # Dark Green
    MAGENTA = (255, 0, 255)  # Magenta


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
        if line in self.lines:
            if line in self._items:
                self.remove_item(line)
                logger.debug(f"Line {line.text[0:10]}... removed from page")
            else:
                for block in self._items:
                    block.remove_line_if_exists(line)
        else:
            logger.debug(f"Line {line.text[0:10]}... not found in page")

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
        self._items = sorted(values, key=lambda block: block.bounding_box.top_left.y if block.bounding_box else 0)

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
            lambda x: isinstance(x, Block)
            and x.block_category == BlockCategory.PARAGRAPH,
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
        self._add_ocr_text_recurse(
            self.items,
            self._cv2_numpy_page_image_word_with_bboxes_and_ocr_text,
        )

        self._cv2_numpy_page_image_word_with_bboxes_and_gt_text = (
            self._cv2_numpy_page_image.copy()
        )
        self._add_rect_recurse(
            self.items,
            self._cv2_numpy_page_image_word_with_bboxes_and_gt_text,
            lambda x: isinstance(x, Word),
        )
        self._add_gt_text_recurse(
            self.items,
            self._cv2_numpy_page_image_word_with_bboxes_and_gt_text,
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
                color = BBoxColors.RED.value
            elif w.ground_truth_match_keys["match_score"] >= 90:
                color = BBoxColors.DARK_GREEN.value
            elif w.ground_truth_match_keys["match_score"] >= 70:
                color = BBoxColors.DARK_GREEN.value
            else:
                color = BBoxColors.MAGENTA.value
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

    def _add_ocr_text_recurse(self, items, image):
        if image is None:
            return
        for item in items:
            if isinstance(item, Word):
                self._add_ocr_text(image, item)
            elif hasattr(item, "items") and item.items:
                self._add_ocr_text_recurse(item.items, image)

    @classmethod
    def _add_ocr_text(cls, image, item, color=None):
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
            item.text or "",
            (x1, y1 - 5),
            cv2_FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1,
        )

    @classmethod
    def _add_gt_text(cls, image, item, color=None):
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
            item.ground_truth_text or "",
            (x1, y1 - 5),
            cv2_FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1,
        )

    def _add_gt_text_recurse(self, items, image):
        if image is None:
            return
        for item in items:
            if isinstance(item, Word):
                self._add_gt_text(image, item)
            elif hasattr(item, "items") and item.items:
                self._add_gt_text_recurse(item.items, image)

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
            bounding_box=self.bounding_box.scale(width, height) if self.bounding_box else None,
            page_labels=self.page_labels,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary"""
        return {
            "type": "Page",
            "width": self.width,
            "height": self.height,
            "page_index": self.page_index,
            "bounding_box": self.bounding_box.to_dict() if self.bounding_box else None,
            "items": [item.to_dict() for item in self.items] if self.items else [],
        }

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

    @classmethod
    def from_dict(cls, dict: Dict[str, Any]) -> "Page":
        """Create OCRPage from dictionary"""
        return cls(
            items=[Block.from_dict(block) for block in dict["items"]],
            width=dict["width"],
            height=dict["height"],
            page_index=dict["page_index"],
            bounding_box=(
                BoundingBox.from_dict(dict["bounding_box"])
                if dict.get("bounding_box")
                else None
            ),
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
                        
        median_line_width = np_median([line.bounding_box.width if line.bounding_box else 0 for line in lines])

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
            tolerance = 0.2 * np_mean([line.bounding_box.height if line.bounding_box else 0 for line in lines])

        logger.debug("Tolerance: " + str(tolerance))

        # Sort lines by their Y position
        lines.sort(key=lambda line: line.bounding_box.minY if line.bounding_box else 0)

        # Compute spacing after each line
        min_y_positions = [line.bounding_box.minY if line.bounding_box else 0 for line in lines]
        max_y_positions = [line.bounding_box.maxY if line.bounding_box else 0 for line in lines]

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
            np_median([line.bounding_box.height if line.bounding_box else 0 for line in lines]) * 0.10
        )
        logger.debug("Median Line Height Spacing: " + str(median_line_height_spacing))

        std_line_height_spacing = np_std(line_spacings) * 0.75
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

        min_x_positions = [line.bounding_box.minX if line.bounding_box else 0 for line in lines]
        max_x_positions = [line.bounding_box.maxX if line.bounding_box else 0 for line in lines]

        median_line_length = np_median([line.bounding_box.width if line.bounding_box else 0 for line in lines])

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
        self: "Page", output_path: pathlib.Path, prefix: str = ""
    ) -> None:
        """
        Create a DocTR text detection training or validation set from a page image (matched_ocr data) and image bounding boxes
        Result:
            Files:
            ├── detection
              ├── images
                ├──── <prefix>_<page_index>.png (image)
                └──── ...
              ├── labels.json

           Detection labels.json:
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

        detection_labels[image_name] = {
            "img_dimensions": (img_width, img_height),
            "img_hash": image_hash,
            "polygons": [
                word.bounding_box.get_four_point_scaled_polygon_list(
                    img_width, img_height
                )
                for word in self.words
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
        self: "Page", output_path: pathlib.Path, prefix: str = ""
    ) -> None:
        """
        Create a text recognition training or validation set from a page image (matched_ocr data) and image bounding boxes
        Result:
            Files:
            ├── recognition
              ├── images
                ├──── <prefix>_<page_index>_x1_x2_y1_y2.jpg (cropped image, x1, y1, x2, y2 are the scaled coordinates of the bounding box)
                └──── ...
              ├── labels.json

            Recognition labels.json:
            {
                "image_path_1": "<gt value>",
            }


        Args:
            self (Page): _description_
            output_path (pathlib.Path): _description_
            prefix (str, optional): _description_. Defaults to "".
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

        # Delete any existing images that match the prefix + page index in the output directory
        for file in recognition_image_path.glob(f"{prefix}_{self.page_index}_*"):
            if file.is_file():
                logger.debug("Deleting existing image: " + str(file))
                file.unlink()

        recognition_labels = {}

        for word in self.words:
            if not word.ground_truth_text:
                logger.critical(
                    "Word does not have ground truth text. Please set it before calling this method. Word: "
                    + word.text
                )
                raise ValueError(
                    "Word does not have ground truth text. Please set it before calling this method. Word: "
                    + word.text
                )
                # raise ValueError(
                #     "Word does not have ground truth text. Please set it before calling this method. Word: "
                #     + word.text
                # )
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
                # [int(cv2_IMWRITE_JPEG_QUALITY), 100],
            )
            label = word.ground_truth_text
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
        self: "Page", output_path: pathlib.Path, prefix: str = ""
    ) -> None:
        """
        Create a recognition and detection training sets from a page image (matched_ocr data) and image bounding boxes
        """
        self.generate_doctr_detection_training_set(
            output_path=output_path, prefix=prefix
        )
        self.generate_doctr_recognition_training_set(
            output_path=output_path, prefix=prefix
        )

    # def compute_text_columns(lines: List[Block], tolerance=None):
    #     """
    #     Compute the number of columns in a given block of OCR lines.
    #     This is done by grouping lines based on their x-coordinates.

    #     :param lines: List of blocks representing a line of OCR words.
    #     :param tolerance: Tolerance for grouping similar x-coordinates
    #     (in same coordinates as line bounding boxes).
    #     :return: dictionary of columns
    #     """

    #     # A given page may have multiple sets of columns, broken apart horizontally
    #     # E.G. 1-column header, 2-column body, 1-column footer
    #     # or single column, but 3 blocks, because of a blockquote

    #     # Default tolerance is 10% of the average line width
    #     if tolerance is None:
    #         tolerance = 0.10 * np.mean([line.bounding_box.width for line in lines])

    #     left_positions = [line.bounding_box.minX for line in lines]
    #     right_positions = [line.bounding_box.maxX for line in lines]
    #     central_positions = [
    #         (left + right) / 2 for left, right in zip(left_positions, right_positions)
    #     ]

    #     # Helper function to group positions into clusters
    #     def cluster_positions(positions, tolerance):
    #         clusters = []
    #         for pos in sorted(positions):
    #             if not clusters or abs(pos - clusters[-1][-1]) > tolerance:
    #                 clusters.append([pos])
    #             else:
    #                 clusters[-1].append(pos)
    #         return [np.mean(cluster) for cluster in clusters]

    #     # Cluster central positions instead of left or right positions
    #     central_clusters = cluster_positions(central_positions, tolerance)

    #     # Group lines into columns based on left and right clusters
    #     columns = defaultdict(list)
    #     for line in lines:
    #         left = line["geometry"][0][0]
    #         right = line["geometry"][1][0]

    #         # Find the closest cluster for the left and right margins
    #         left_column = min(left_clusters, key=lambda x: abs(x - left))
    #         right_column = min(right_clusters, key=lambda x: abs(x - right))

    #         # Use a tuple of (left_column, right_column) as the column key
    #         columns[(left_column, right_column)].append(line)

    #     return columns

    # def _compute_dynamic_horizontal_spacing_threshold(self, lines, std_multiplier):
    #     """
    #     Compute a dynamic spacing threshold based on the vertical spacing between lines.
    #     This is used to detect block/paragraph/thought breaks in OCR text.

    #     The threshold is calculated as the mean spacing,
    #     plus a multiple of the standard deviation to account
    #     for minor variations in line spacing.

    #     :param lines: List of line dictionaries
    #     :return: Dynamic spacing threshold based on mean and standard deviation
    #     """
    #     if len(lines) < 2:
    #         return 0
    #         # Extract Y positions and compute spacing statistics
    #     y_positions = [line["geometry"][0][1] for line in lines]

    #     # Get differences between consecutive lines
    #     line_spacings = np.diff(y_positions)
    #     mean_spacing = np.mean(line_spacings)
    #     std_spacing = np.std(line_spacings)
    #     dynamic_horizontal_spacing_threshold = mean_spacing + (
    #         std_spacing * std_multiplier
    #     )
    #     return dynamic_horizontal_spacing_threshold

    # def reprocess_column_block(self, lines: List[Block]):

    #     # First, reorganize the lines into blocks based on their vertical spacing
    #     # This will group lines separate vertical blocks (e.g. Header, Body, Blockquotes, Footer, etc)

    #     # Compute dynamic spacing threshold for block breaks
    #     dynamic_horizontal_spacing_threshold = (
    #         self._compute_dynamic_horizontal_spacing_threshold(
    #             lines, std_multiplier=1.3
    #         )
    #     )

    #     blocks = []
    #     current_block = []
    #     last_y = lines[0]["geometry"][0][1]

    #     for i, line in enumerate(lines):
    #         words = line.items
    #         if words:
    #             line_text = line.text
    #             indent = words[0].bounding_box.minX  # X-coordinate for indentation
    #             y_position = line.bounding_box.minY

    #             # Paragraph break detection
    #             is_paragraph_break = False

    #             # "Block" break detection
    #             is_block_break = False

    #             # First line: Always add it normally (don't check breaks)
    #             if i == 0:
    #                 processed_text.append(line_text)
    #                 continue  # Skip to next line

    #             # Second line: Check if it's unusually spaced compared to the first
    #             # Poetry, of course, makes this worse

    #             elif i == 1:
    #                 first_spacing = abs(y_position - lines[0]["geometry"][0][1])
    #                 if first_spacing > dynamic_spacing_threshold:
    #                     is_paragraph_break = True

    #             # For other lines, detect spacing-based paragraph breaks dynamically
    #             elif i < len(lines) - 1:  # Ensure next line exists
    #                 next_y = lines[i + 1]["geometry"][0][1]
    #                 line_spacing = abs(next_y - y_position)

    #                 if line_spacing > dynamic_spacing_threshold:
    #                     is_paragraph_break = True  # Large vertical gap detected

    #             # Detect indentation-based paragraph breaks using global median threshold
    #             if abs(indent - median_indent) > dynamic_indent_threshold:
    #                 is_paragraph_break = True

    #             # Insert exactly two line breaks for paragraph separation
    #             if is_paragraph_break and not last_was_paragraph_break:
    #                 processed_text.append("")  # Adds one extra blank line
    #                 last_was_paragraph_break = True
    #             else:
    #                 last_was_paragraph_break = False  # Reset flag

    #             processed_text.append(line_text)

    # def reprocess_blocks(self, std_multiplier=1.3, indent_multiplier=0.015):
    #     """
    #     Reprocesses an OCR page dictionary.
    #     This is post-processing logic built primarily for Book Pages.

    #     Starts with all lines, and recalculates blocks and
    #     paragraph breaks based on dynamically computed vertical spacing
    #     and a median-based global indentation threshold.

    #     :param std_multiplier: How many standard deviations above the mean spacing qualifies as a block break.
    #     :param indent_multiplier: Factor to apply to median line length for dynamic indentation threshold. (for paragraphs)
    #     :return: New Page object with reprocessed paragraphs.
    #     """
    #     processed_text = []
    #     last_was_paragraph_break = False  # Tracks last break state

    #     lines = self.lines
    #     if len(lines) < 2:
    #         return self  # Not enough lines to compute spacing, don't change the text

    #     dynamic_horizontal_spacing_threshold = (
    #         self._compute_dynamic_horizontal_spacing_threshold(lines, std_multiplier)
    #     )

    #     # Compute right-aligned median x value for dynamic indentation threshold
    #     all_right_indents = [line["geometry"][1][0] for line in lines]

    #     # Determine if there are several different common median right-aligned x values.
    #     # If so, this means there are multiple columns of text on the page.
    #     # We should split these apart and generate separate paragraphs for each column.

    #     median_right_indent = np.median(all_right_indents)

    #     # Compute global median indentation of each line
    #     all_left_indents = [line["geometry"][0][0] for line in lines]
    #     median_left_indent = np.median(all_left_indents)

    #     # Compute median line length for dynamic indentation threshold
    #     line_lengths = [
    #         line["geometry"][1][0] - line["geometry"][0][0] for line in lines
    #     ]
    #     median_line_length = np.median(line_lengths)
    #     dynamic_indent_threshold = median_line_length * indent_multiplier

    #     return "\n".join(processed_text)
