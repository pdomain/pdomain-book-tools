import itertools
from collections.abc import Collection
from enum import Enum
from logging import getLogger
from typing import ClassVar

import numpy as np
from numpy import ndarray
from thefuzz.fuzz import ratio as fuzz_ratio

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.word import Word

# Configure logging
logger = getLogger(__name__)


class BlockChildType(Enum):
    WORDS = "WORDS"
    BLOCKS = "BLOCKS"


class BlockCategory(Enum):
    BLOCK = "BLOCK"
    PARAGRAPH = "PARAGRAPH"
    LINE = "LINE"


class Block:
    """
    Represents a block of text as detected and split by OCR.

    A "block" can be a line of text, a paragraph, or a larger "block" or "region" of text.
    Inside it, there can either be child blocks or individual words (a "line" of text)

    Some OCR tools may not distinguish between blocks, paragraphs, or lines.
    Some may have blocks with no words at all.
    """

    ALLOWED_BLOCK_ROLE_LABELS: ClassVar[frozenset[str]] = frozenset(
        {
            "paragraph",
            "sidenote",
            "page header",
            "page footer",
            "page number",
            "printers mark",
            "blockquote",
            "poetry",
        }
    )

    ALLOWED_BLOCK_POSITION_LABELS: ClassVar[frozenset[str]] = frozenset(
        {
            "top",
            "bottom",
            "left",
            "right",
            "center",
            "margin left",
            "margin right",
        }
    )

    ALLOWED_LINE_ROLE_LABELS: ClassVar[frozenset[str]] = frozenset(
        {
            "body line",
            "heading line",
            "verse line",
            "blockquote line",
            "header line",
            "footer line",
            "footnote line",
            "caption line",
            "page number line",
        }
    )

    ALLOWED_LINE_POSITION_LABELS: ClassVar[frozenset[str]] = frozenset(
        {
            "top",
            "bottom",
            "left",
            "right",
            "center",
            "column left",
            "column right",
        }
    )

    BLOCK_ROLE_LABEL_ALIASES: ClassVar[dict[str, str]] = {
        "block quote": "blockquote",
        "pageheader": "page header",
        "pagefooter": "page footer",
        "pagenumber": "page number",
        "printer's mark": "printers mark",
        "printersmark": "printers mark",
        "poem": "poetry",
    }

    LINE_ROLE_LABEL_ALIASES: ClassVar[dict[str, str]] = {
        "body": "body line",
        "heading": "heading line",
        "verse": "verse line",
        "blockquote": "blockquote line",
        "header": "header line",
        "footer": "footer line",
        "footnote": "footnote line",
        "caption": "caption line",
        "page number": "page number line",
        "pagenumber": "page number line",
    }

    # NOTE: Previously a dataclass; converted to manual class to avoid misleading auto-generated
    # equality semantics (identity comparisons are intended) and because a custom __init__ already
    # existed. Behavior retained.
    # _items: internal storage list; use items property for external access (sorted copy)

    def __init__(
        self,
        items: Collection,
        bounding_box: BoundingBox | None = None,
        child_type: BlockChildType | None = BlockChildType.BLOCKS,
        block_category: BlockCategory | None = BlockCategory.BLOCK,
        block_labels: list[str] | None = None,
        block_role_labels: list[str] | None = None,
        block_position_labels: list[str] | None = None,
        line_role_labels: list[str] | None = None,
        line_position_labels: list[str] | None = None,
        baseline: dict[str, float | str] | None = None,
        override_page_sort_order: int | None = None,
        unmatched_ground_truth_words: list[tuple[int, str]] | None = None,
        additional_block_attributes: dict | None = None,
        base_ground_truth_text: str | None = None,
    ):
        self.child_type: BlockChildType | None = child_type
        self.block_category: BlockCategory | None = block_category
        self.block_labels: list[str] | None = block_labels
        self.block_role_labels: list[str] = self._normalize_labels(
            block_role_labels,
            self.ALLOWED_BLOCK_ROLE_LABELS,
            self.BLOCK_ROLE_LABEL_ALIASES,
            "block role",
        )
        self.block_position_labels: list[str] = self._normalize_labels(
            block_position_labels,
            self.ALLOWED_BLOCK_POSITION_LABELS,
            {},
            "block position",
        )
        self.line_role_labels: list[str] = self._normalize_labels(
            line_role_labels,
            self.ALLOWED_LINE_ROLE_LABELS,
            self.LINE_ROLE_LABEL_ALIASES,
            "line role",
        )
        self.line_position_labels: list[str] = self._normalize_labels(
            line_position_labels,
            self.ALLOWED_LINE_POSITION_LABELS,
            {},
            "line position",
        )
        self.baseline: dict[str, float | str] | None = (
            baseline.copy() if baseline else None
        )
        self.override_page_sort_order: int | None = override_page_sort_order
        self.base_ground_truth_text: str | None = base_ground_truth_text
        # containers
        self.additional_block_attributes: dict = (
            additional_block_attributes
            if additional_block_attributes is not None
            else {}
        )
        self.unmatched_ground_truth_words: list[tuple[int, str]] = (
            list(unmatched_ground_truth_words)
            if unmatched_ground_truth_words is not None
            else []
        )
        logger.debug(
            "unmatched_ground_truth_words: %s", str(self.unmatched_ground_truth_words)
        )
        # Initialize bounding box attribute so it's always present (may be None for empty blocks)
        self.bounding_box: BoundingBox | None = None
        # Will set self._items and compute bounding box
        self.items = items  # type: ignore[assignment]
        # If explicit bbox passed, override computed one
        if bounding_box is not None:
            self.bounding_box = bounding_box

    def __repr__(self) -> str:  # pragma: no cover (representation convenience)
        cls = self.__class__.__name__
        n_items = len(getattr(self, "_items", []))
        bbox = (
            None
            if getattr(self, "bounding_box", None) is None
            else f"{self.bounding_box.to_ltrb()}"
        )
        return (
            f"{cls}(items={n_items}, child_type={self.child_type}, "
            f"block_category={self.block_category}, bbox={bbox}, "
            f"labels={self.block_labels}, override_sort={self.override_page_sort_order})"
        )

    @classmethod
    def _normalize_label(
        cls,
        label: str,
        allowed: frozenset[str],
        aliases: dict[str, str],
        label_kind: str,
    ) -> str:
        normalized = " ".join(
            label.strip().lower().replace("_", " ").replace("-", " ").split()
        )
        normalized = aliases.get(normalized, normalized)

        if normalized not in allowed:
            compact = normalized.replace(" ", "")
            for allowed_label in allowed:
                if compact == allowed_label.replace(" ", ""):
                    normalized = allowed_label
                    break

            if normalized not in allowed:
                for alias, canonical in aliases.items():
                    if compact == alias.replace(" ", ""):
                        normalized = canonical
                        break

        if normalized not in allowed:
            allowed_str = ", ".join(sorted(allowed))
            raise ValueError(
                f"Invalid {label_kind} label '{label}'. Allowed labels: {allowed_str}"
            )
        return normalized

    @classmethod
    def _normalize_labels(
        cls,
        labels: list[str] | None,
        allowed: frozenset[str],
        aliases: dict[str, str],
        label_kind: str,
    ) -> list[str]:
        if not labels:
            return []
        normalized = [
            cls._normalize_label(label, allowed, aliases, label_kind)
            for label in labels
        ]
        return list(dict.fromkeys(normalized))

    def _sort_items(self):
        # TODO: Implement a more robust sorting mechanism.

        # Blocks should be sorted:
        # Header & Page Number
        # Left Sidenotes
        # Body Text
        #    Within Body Text, sort by:
        #    Blocks, top to bottom
        #      Blocks within Blocks (Columns), left to right
        #      Within Columns, sort by Paragraphs, top to bottom
        #        Within Paragraphs, sort by Lines, top to bottom
        #          Within Lines, sort by Words, left to right

        # Right Sidenotes
        if self.child_type == BlockChildType.WORDS:
            self._items.sort(
                key=lambda item: (
                    item.bounding_box.top_left.x
                    if item.bounding_box and item.bounding_box.top_left
                    else 0,
                    item.bounding_box.top_left.y
                    if item.bounding_box and item.bounding_box.top_left
                    else 0,
                ),
            )
        else:
            self._items.sort(
                key=lambda item: (
                    item.bounding_box.top_left.y
                    if item.bounding_box and item.bounding_box.top_left
                    else 0,
                    item.bounding_box.top_left.x
                    if item.bounding_box and item.bounding_box.top_left
                    else 0,
                ),
            )

    @property
    def items(self) -> list:
        """Returns a copy of the item list in this block."""
        return self._items.copy()

    def recompute_bounding_box(self) -> None:
        """Recompute the bounding box of the block based on its items."""
        if not self._items:
            self.bounding_box = None
            return
        self.bounding_box = BoundingBox.union(
            [item.bounding_box for item in self._items]
        )

    def add_item(self, item):
        """Add an item to the block"""
        if self.child_type == BlockChildType.WORDS:
            if not isinstance(item, Word):
                raise TypeError("Item must be of type Word")
            # Enforce uniform coordinate system among word bounding boxes
            if self._items:
                first_bbox = self._items[0].bounding_box
                if (
                    first_bbox is not None
                    and item.bounding_box is not None
                    and first_bbox.is_normalized != item.bounding_box.is_normalized
                ):
                    raise ValueError(
                        "All word bounding boxes in a WORDS block must share the same coordinate system (normalized or pixel)."
                    )
        else:
            if not isinstance(item, Block):
                raise TypeError("Item must be of type Block")
        self._items.append(item)
        self._sort_items()
        self.recompute_bounding_box()

    def remove_item(self, item) -> None:
        """Remove an item from the block."""
        if item in self._items:
            self._items.remove(item)
            self._sort_items()
            self.recompute_bounding_box()
            logger.debug("Item removed from block")
        else:
            raise ValueError("Item not found in block")

    def remove_ground_truth(self) -> None:
        """Remove the ground truth text from the block."""
        if self.unmatched_ground_truth_words:
            self.unmatched_ground_truth_words.clear()
        else:
            self.unmatched_ground_truth_words = []
        if self.child_type == BlockChildType.WORDS:
            for word in self._items:
                word.ground_truth_text = ""
                word.ground_truth_bounding_box = None
        else:
            for block in self._items:
                block.remove_ground_truth()
        logger.debug("Ground truth text removed from block")

    def remove_line_if_exists(self, line) -> bool:
        """Remove a line from the page if it exists."""
        if self.child_type == BlockChildType.WORDS:
            return False

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
            logger.debug("Line removed from block")
        else:
            logger.debug("Line not found in block")

        return removed

    @property
    def is_empty(self) -> bool:
        """Return True when this block has no child items."""
        return not self._items

    def remove_empty_items(self) -> None:
        """Remove empty child blocks from the block."""
        if not self._items:
            return
        if self.child_type != BlockChildType.WORDS:
            for item in self._items:
                item.remove_empty_items()
            before = len(self._items)
            self._items = [item for item in self._items if item._items]
            if len(self._items) != before:
                self._sort_items()
                self.recompute_bounding_box()
                logger.debug("Empty blocks removed")
        # Empty words are directly removed with remove_item, do not need to be handled here

    @items.setter
    def items(self, value):
        if not isinstance(value, Collection):
            raise TypeError("items must be a collection (e.g., list, tuple, set)")
        for item in value:
            if not hasattr(item, "bounding_box") or not isinstance(
                item.bounding_box, BoundingBox
            ):
                raise TypeError(
                    "Each item in items must have a bounding_box attribute of type BoundingBox"
                )
            if not isinstance(item, (Word, Block)):
                raise TypeError("Each item in items must be of type Word or Block")
        # Enforce coordinate system uniformity for WORDS blocks
        if value and self.child_type == BlockChildType.WORDS:
            is_norm_set = {
                getattr(it.bounding_box, "is_normalized", False)
                for it in value
                if it.bounding_box is not None
            }
            if len(is_norm_set) > 1:
                raise ValueError(
                    "All word bounding boxes in a WORDS block must share the same coordinate system (normalized or pixel)."
                )
        self._items = list(value)
        self._sort_items()
        self.recompute_bounding_box()

    @property
    def text(self) -> str:
        """Get the full text of the block.
        If child type is words, join text by spaces.
        Otherwise join text by carriage returns.
        This automatically adds additional CRs between blocks/paragraphs.
        """
        if self.child_type == BlockChildType.WORDS:
            return " ".join(item.text for item in self._items)
        elif self.block_category == BlockCategory.PARAGRAPH:
            return "\n".join(item.text for item in self._items)
        else:
            return "\n\n".join(item.text for item in self._items)

    @property
    def ground_truth_text(self) -> str:
        """Get the ground truth text of the words in the block.
        If child type is words, join text by spaces.
        Otherwise join text by carriage returns.
        This automatically adds additional CRs between blocks/paragraphs.
        """
        if self.child_type == BlockChildType.WORDS:
            # If the block is a line, use the ground truth text of the words
            matched_words = []
            for word in self._items:
                matched_words.append(word.ground_truth_text or "")

            # Also, add unmatched ground truth words to the text
            if self.unmatched_ground_truth_words:
                for unmatched_gt_word_idx, unmatched_gt_word in reversed(
                    self.unmatched_ground_truth_words
                ):
                    logger.debug(
                        "Adding unmatched ground truth word '%s' at index %s",
                        unmatched_gt_word,
                        unmatched_gt_word_idx,
                    )
                    matched_words.insert(unmatched_gt_word_idx + 1, unmatched_gt_word)
                logger.debug(
                    "Matched words after adding unmatched ground truth words: %s",
                    matched_words,
                )
            return " ".join(matched_words)
        elif self.block_category == BlockCategory.PARAGRAPH:
            return "\n".join(item.ground_truth_text for item in self._items)
        else:
            return "\n\n".join(item.ground_truth_text for item in self._items)

    @property
    def ground_truth_text_only_ocr(self) -> str:
        """Get the ground truth text of the words in the block.
        Only include words that have associated OCR text.
        If child type is words, join text by spaces.
        Otherwise join text by carriage returns.
        This automatically adds additional CRs between blocks/paragraphs.
        """
        if self.child_type == BlockChildType.WORDS:
            return " ".join(
                s
                for s in (item.ground_truth_text_only_ocr for item in self._items)
                if s
            )
        elif self.block_category == BlockCategory.PARAGRAPH:
            return "\n".join(
                s
                for s in (item.ground_truth_text_only_ocr for item in self._items)
                if s
            )
        else:
            return "\n\n".join(
                s
                for s in (item.ground_truth_text_only_ocr for item in self._items)
                if s
            )

    @property
    def ground_truth_exact_match(self) -> bool:
        """Check if the ground truth text of the block matches the text."""
        return all(item.ground_truth_exact_match for item in self._items)

    def validate_line_consistency(self) -> dict:
        """Validate consistency of OCR vs ground truth for this line.

        Returns a dict with word counts, match counts, mismatch details,
        and an overall accuracy score.
        """
        words = self.words
        if not words:
            return {
                "valid": True,
                "words": 0,
                "with_gt": 0,
                "matches": 0,
                "mismatches": 0,
            }

        total_words = len(words)
        words_with_gt = 0
        exact_matches = 0
        mismatches = []

        for word_idx, word in enumerate(words):
            ocr_text = word.text
            gt_text = word.ground_truth_text

            if gt_text:
                words_with_gt += 1
                if ocr_text == gt_text:
                    exact_matches += 1
                else:
                    mismatches.append(
                        {
                            "word_index": word_idx,
                            "ocr_text": ocr_text,
                            "gt_text": gt_text,
                        }
                    )

        return {
            "valid": True,
            "words": total_words,
            "with_gt": words_with_gt,
            "matches": exact_matches,
            "mismatches": len(mismatches),
            "mismatch_details": mismatches,
            "accuracy": exact_matches / words_with_gt if words_with_gt > 0 else 1.0,
        }

    def copy_ocr_to_ground_truth(self) -> bool:
        """Copy OCR text to ground truth for all words in this block."""
        return any([word.copy_ocr_to_ground_truth() for word in self.words])

    def copy_ground_truth_to_ocr(self) -> bool:
        """Copy ground truth text to OCR text for all words in this block."""
        return any([word.copy_ground_truth_to_ocr() for word in self.words])

    def clear_ground_truth(self) -> bool:
        """Clear ground truth text from all words in this block."""
        return any([word.clear_ground_truth() for word in self.words])

    @property
    def word_list(self) -> list[str]:
        """Get list of words in the block."""
        if self.child_type == BlockChildType.WORDS:
            return [item.text for item in self._items]
        else:
            return list(
                itertools.chain.from_iterable(item.word_list for item in self._items)
            )

    @property
    def words(self) -> list[Word]:
        """Get flat list of all words in the block."""
        if self.child_type == BlockChildType.WORDS:
            return list(self._items)
        else:
            return list(
                itertools.chain.from_iterable(item.words for item in self._items)
            )

    @property
    def lines(self) -> list["Block"]:
        """Flat list of all 'lines' in the block."""
        if self.child_type == BlockChildType.WORDS:
            return [self]
        else:
            return list(
                itertools.chain.from_iterable(item.lines for item in self._items)
            )

    @property
    def paragraphs(self) -> list["Block"]:
        """Flat list of all 'paragraphs' in the block."""
        if self.block_category == BlockCategory.PARAGRAPH:
            return [self]
        else:
            return list(
                itertools.chain.from_iterable(item.paragraphs for item in self._items)
            )

    def split_word(
        self,
        split_word_index: int,
        bbox_split_offset: float,
        character_split_index: int,
    ) -> None:
        """Split a word in the line into two parts and replace it with the new words."""
        logger.debug(
            "Splitting word at index %s with bbox_split_offset %s and character_split_index %s",
            split_word_index,
            bbox_split_offset,
            character_split_index,
        )

        if self.child_type != BlockChildType.WORDS:
            raise ValueError("Cannot split a word in a block of blocks")
        if split_word_index < 0 or split_word_index >= len(self._items):
            raise IndexError("Index out of range")
        word = self._items[split_word_index]
        if not isinstance(word, Word):
            raise TypeError("Item must be of type Word")

        word_1, word_2 = word.split(
            bbox_split_offset=bbox_split_offset,
            character_split_index=character_split_index,
        )
        logger.debug("Word Split. New words: %s, %s", word_1.text, word_2.text)
        self._items.remove(word)
        self._items.append(word_1)
        self._items.append(word_2)
        self._sort_items()
        self.recompute_bounding_box()
        logger.debug("Line after split: %s", self.text)

    def merge_adjacent_words(self, word_index: int, direction: str) -> bool:
        """Merge adjacent words within this line block.

        Args:
            word_index: Zero-based index of the selected word.
            direction: ``"left"`` merges into the preceding word,
                ``"right"`` merges the following word into the selected one.

        Returns:
            True if the merge succeeded, False otherwise.
        """
        words = list(self.words)
        if len(words) < 2:
            logger.warning("Word merge requires at least two words in line")
            return False

        if word_index < 0 or word_index >= len(words):
            logger.warning(
                "Word merge index %s out of range (0-%s)",
                word_index,
                len(words) - 1,
            )
            return False

        if direction == "left":
            if word_index == 0:
                logger.warning("Cannot merge first word to the left")
                return False
            keep_index = word_index - 1
            remove_index = word_index
        elif direction == "right":
            if word_index >= len(words) - 1:
                logger.warning("Cannot merge last word to the right")
                return False
            keep_index = word_index
            remove_index = word_index + 1
        else:
            logger.warning("Unsupported word merge direction: %s", direction)
            return False

        words[keep_index].merge(words[remove_index])
        self.remove_item(words[remove_index])

        for word in self.words:
            word.ground_truth_text = ""

        return True

    def merge_word_left(self, word_index: int) -> bool:
        """Merge the word at *word_index* into its immediate left neighbor."""
        return self.merge_adjacent_words(word_index, "left")

    def merge_word_right(self, word_index: int) -> bool:
        """Merge the word at *word_index* with its immediate right neighbor."""
        return self.merge_adjacent_words(word_index, "right")

    def split_word_at_fraction(self, word_index: int, split_fraction: float) -> bool:
        """Split the word at *word_index* at a relative horizontal position.

        Calculates the character and bbox split points from *split_fraction*
        and delegates to :meth:`split_word`.  Clears ground-truth text for all
        words in the line after the split.

        Args:
            word_index: Zero-based index of the word to split.
            split_fraction: Relative split position in the range (0, 1).

        Returns:
            True if the split succeeded, False otherwise.
        """
        if split_fraction <= 0.0 or split_fraction >= 1.0:
            logger.warning(
                "Word split fraction must be between 0 and 1 (exclusive), got %s",
                split_fraction,
            )
            return False

        words = list(self.words)
        if word_index < 0 or word_index >= len(words):
            logger.warning(
                "Word split index %s out of range (0-%s)",
                word_index,
                len(words) - 1,
            )
            return False

        word = words[word_index]
        word_text = str(word.text or "")
        if len(word_text) < 2:
            logger.warning(
                "Word split requires at least two characters (word=%s)",
                word_index,
            )
            return False

        bbox = word.bounding_box
        bbox_width = float(bbox.width if bbox else 0.0)
        if bbox is None or bbox_width <= 0.0:
            logger.warning(
                "Word split requires a valid non-zero bounding box (word=%s)",
                word_index,
            )
            return False

        character_split_index = int(round(len(word_text) * split_fraction))
        character_split_index = max(1, min(len(word_text) - 1, character_split_index))

        epsilon = min(1e-6, bbox_width / 10) if bbox_width > 0 else 0.0
        bbox_split_offset = bbox_width * split_fraction
        bbox_split_offset = max(epsilon, min(bbox_width - epsilon, bbox_split_offset))

        self.split_word(
            split_word_index=word_index,
            bbox_split_offset=bbox_split_offset,
            character_split_index=character_split_index,
        )

        for w in self.words:
            w.ground_truth_text = ""

        logger.info(
            "Split word index=%d fraction=%.3f char_index=%d",
            word_index,
            split_fraction,
            character_split_index,
        )
        return True

    @staticmethod
    def _is_geometry_normalization_error(error: Exception) -> bool:
        """Return True for known malformed-bbox normalization failures."""
        return BoundingBox.is_geometry_normalization_error(error)

    def merge_fallback(self, other: "Block") -> bool:
        """Fallback merge that concatenates items when :meth:`merge` fails
        on malformed bbox metadata."""
        try:
            self._items = [*self._items, *other.items]
            self._sort_items()

            try:
                self.recompute_bounding_box()
            except Exception as recompute_error:
                if not self._is_geometry_normalization_error(recompute_error):
                    raise
                logger.warning(
                    "Fallback merge skipped bbox recompute due to "
                    "malformed geometry: %s",
                    recompute_error,
                )

            return True
        except Exception as fallback_error:
            logger.exception("Fallback merge failed: %s", fallback_error)
            return False

    def refine_word_bboxes(self, page_image: "ndarray | None") -> bool:
        """Refine all word bounding boxes using the page image and recompute
        this block's bbox.

        Args:
            page_image: The page's cv2 numpy image (passed down since Block
                doesn't own the image).

        Returns:
            True if any word was refined.
        """
        refined_any = False
        for word in self.words:
            refined_any = word.refine_bbox(page_image) or refined_any
        self.recompute_bounding_box()
        return refined_any

    def merge(self, block_to_merge: "Block") -> None:
        """Merge another block into this one."""
        if self.child_type != block_to_merge.child_type:
            raise ValueError("Cannot merge blocks with different child types")
        if self.block_category != block_to_merge.block_category:
            raise ValueError("Cannot merge blocks with different block categories")
        self._items.extend(block_to_merge.items)
        self._sort_items()
        if (
            self.unmatched_ground_truth_words
            and block_to_merge.unmatched_ground_truth_words
        ):
            self.unmatched_ground_truth_words.extend(
                block_to_merge.unmatched_ground_truth_words
            )
        if self.block_labels is None:
            self.block_labels = block_to_merge.block_labels
        else:
            if block_to_merge.block_labels is not None:
                self.block_labels = list(
                    set(self.block_labels).union(block_to_merge.block_labels)
                )
        self.block_role_labels = list(
            dict.fromkeys(self.block_role_labels + block_to_merge.block_role_labels)
        )
        self.block_position_labels = list(
            dict.fromkeys(
                self.block_position_labels + block_to_merge.block_position_labels
            )
        )
        self.line_role_labels = list(
            dict.fromkeys(self.line_role_labels + block_to_merge.line_role_labels)
        )
        self.line_position_labels = list(
            dict.fromkeys(
                self.line_position_labels + block_to_merge.line_position_labels
            )
        )
        self.recompute_bounding_box()

    def ocr_confidence_scores(self) -> list[float]:
        """Get a list of the OCR confidence scores of all nested words."""
        if not self._items:
            return []
        if self.child_type == BlockChildType.WORDS:
            return [item.ocr_confidence for item in self._items]
        else:
            return list(
                itertools.chain.from_iterable(
                    item.ocr_confidence_scores() for item in self._items
                )
            )

    def mean_ocr_confidence(self) -> float:
        """Get the mean of the OCR confidence score of all items"""
        scores = self.ocr_confidence_scores()
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def scale(self, width: int, height: int) -> "Block":
        """
        Return new block with scaled bounding box
        and scaled children to absolute pixel coordinates
        """
        return Block(
            items=[item.scale(width, height) for item in self._items],
            bounding_box=self.bounding_box.scale(width, height)
            if self.bounding_box
            else None,
            child_type=self.child_type,
            block_category=self.block_category,
            block_labels=self.block_labels,
            block_role_labels=self.block_role_labels,
            block_position_labels=self.block_position_labels,
            line_role_labels=self.line_role_labels,
            line_position_labels=self.line_position_labels,
            baseline=self.baseline,
        )

    def fuzz_score_against(self, ground_truth_text):
        """Scores a string as "matching" against a ground truth string

        TODO: Perhaps add loose scoring for curly quotes against straight quotes, and em-dashes against hyphens to count these as "closer" to gt

        Args:
            ground_truth_text (_type_): 'correct' text
        """
        return fuzz_ratio(self.text, ground_truth_text)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "type": "Block",
            "child_type": self.child_type.value if self.child_type else None,
            "block_category": self.block_category.value
            if self.block_category
            else None,
            "block_labels": self.block_labels,
            "block_role_labels": self.block_role_labels,
            "block_position_labels": self.block_position_labels,
            "line_role_labels": self.line_role_labels,
            "line_position_labels": self.line_position_labels,
            "baseline": self.baseline,
            "bounding_box": self.bounding_box.to_dict() if self.bounding_box else None,
            "items": [item.to_dict() for item in self._items],
            "override_page_sort_order": self.override_page_sort_order,
            "unmatched_ground_truth_words": self.unmatched_ground_truth_words or [],
            "additional_block_attributes": self.additional_block_attributes or {},
            "base_ground_truth_text": self.base_ground_truth_text or "",
        }

    @classmethod
    def from_dict(cls, data) -> "Block":
        """Create OCRBlock from dictionary"""
        if data.get("child_type"):
            child_type = BlockChildType(data["child_type"])
        else:
            child_type = BlockChildType.WORDS

        if child_type == BlockChildType.WORDS:
            items = [Word.from_dict(item) for item in data["items"]]
        else:
            items = [Block.from_dict(item) for item in data["items"]]

        return cls(
            items=items,
            bounding_box=BoundingBox.from_dict(data["bounding_box"]),
            child_type=child_type,
            block_category=BlockCategory(data["block_category"])
            if data.get("block_category")
            else BlockCategory.BLOCK,
            block_labels=data.get("block_labels", []),
            block_role_labels=data.get("block_role_labels", []),
            block_position_labels=data.get("block_position_labels", []),
            line_role_labels=data.get("line_role_labels", []),
            line_position_labels=data.get("line_position_labels", []),
            baseline=data.get("baseline"),
            override_page_sort_order=data.get("override_page_sort_order", None),
            unmatched_ground_truth_words=data.get("unmatched_ground_truth_words", []),
            additional_block_attributes=data.get("additional_block_attributes", {}),
            base_ground_truth_text=data.get("base_ground_truth_text", None),
        )

    def estimate_baseline_from_image(
        self, image: ndarray | None
    ) -> dict[str, float | str] | None:
        """Estimate a line baseline y = m*x + b in pixel coordinates.

        This only applies to line blocks containing words.
        """
        if image is None:
            self.baseline = None
            return None
        if (
            self.child_type != BlockChildType.WORDS
            or self.block_category != BlockCategory.LINE
        ):
            self.baseline = None
            return None

        descender_chars = {"p", "g", "j", "q", "Q"}
        x_points: list[float] = []
        y_points: list[float] = []
        weights: list[float] = []

        for item in self._items:
            if not isinstance(item, Word):
                continue
            chars = item.split_into_characters_from_whitespace(image)
            if not chars:
                continue
            item.estimate_baseline_from_image(image)
            for ch in chars:
                x_points.append(
                    float((ch.bounding_box.minX + ch.bounding_box.maxX) / 2)
                )
                y_points.append(float(ch.bounding_box.maxY))
                weights.append(0.35 if ch.text in descender_chars else 1.0)

        if len(x_points) < 2:
            self.baseline = None
            return None

        x_arr = np.array(x_points, dtype=float)
        y_arr = np.array(y_points, dtype=float)
        w_arr = np.array(weights, dtype=float)

        slope, intercept = np.polyfit(x_arr, y_arr, deg=1, w=w_arr)
        predicted = slope * x_arr + intercept
        residual = y_arr - predicted
        weighted_var = float(np.average(residual * residual, weights=w_arr))
        weighted_std = float(np.sqrt(weighted_var))
        y_span = float(max(1.0, np.max(y_arr) - np.min(y_arr)))
        confidence = max(0.0, 1.0 - (weighted_std / y_span))

        self.baseline = {
            "type": "linear",
            "slope": float(slope),
            "intercept": float(intercept),
            "confidence": confidence,
            "coordinate_space": "pixel",
        }
        return self.baseline

    def refine_bounding_boxes(self, image: ndarray | None, padding_px: int = 0) -> None:
        logger.debug(
            "Refining bounding boxes for block with %s items", len(self._items)
        )
        if not self._items:
            self.bounding_box = None
            return
        if self.child_type == BlockChildType.WORDS:
            logger.debug(
                "Refining bounding boxes for %s words in block", len(self._items)
            )
            for item in self._items:
                item.refine_bounding_box(image, padding_px=padding_px)
        else:
            logger.debug(
                "Refining bounding boxes for %s blocks in block", len(self._items)
            )
            for item in self._items:
                item.refine_bounding_boxes(image, padding_px=padding_px)
        self.recompute_bounding_box()
