from dataclasses import dataclass
import itertools
from typing import Collection, List, Optional, Union

from sortedcontainers import SortedList

from ..geometry import BoundingBox
from ._word import Word

from enum import Enum


class BlockChildType(Enum):
    WORDS = "WORDS"
    BLOCKS = "BLOCKS"


class BlockCategory(Enum):
    BLOCK = "BLOCK"
    PARAGRAPH = "PARAGRAPH"
    LINE = "LINE"


@dataclass
class Block:
    """
    Represents a block of text as detected and split by OCR.

    A "block" can be a line of text, a paragraph, or a larger "block" or "region" of text.
    Inside it, there can either be child blocks or individual words (a "line" of text)

    Some OCR tools may not distinguish between blocks, paragraphs, or lines.
    Some may have blocks with no words at all.
    """

    _items: SortedList[Union["Word", "Block"]]
    bounding_box: Optional[BoundingBox] = None
    child_type: Optional[BlockChildType] = BlockChildType.BLOCKS
    block_category: Optional[BlockCategory] = BlockCategory.BLOCK
    block_labels: Optional[list[str]] = None

    def __init__(
        self,
        items: Collection,
        bounding_box: Optional[BoundingBox] = None,
        child_type: Optional[BlockChildType] = BlockChildType.BLOCKS,
        block_category: Optional[BlockCategory] = BlockCategory.BLOCK,
        block_labels: Optional[list[str]] = None,
    ):
        self.items = items  # Use the setter for validation or processing
        if bounding_box:
            self.bounding_box = bounding_box
        elif self.items:
            self.bounding_box = BoundingBox.union(
                [item.bounding_box for item in self.items]
            )
        self.child_type = child_type
        self.block_category = block_category
        self.block_labels = block_labels

    @property
    def items(self) -> SortedList:
        return self._items

    @items.setter
    def items(self, value):
        if isinstance(value, SortedList):
            self._items = value
            return
        if not isinstance(value, Collection):
            raise TypeError(
                "items must be a collection (e.g., list, tuple, set) or SortedList"
            )
        for item in value:
            if not hasattr(item, "bounding_box") or not isinstance(
                item.bounding_box, BoundingBox
            ):
                raise TypeError(
                    "Each item in items must have a bounding_box attribute of type BoundingBox"
                )
            if not isinstance(item, (Word, Block)):
                raise TypeError("Each item in items must be of type Word or Block")
        # Sort by x then y-coordinate
        self._items = SortedList(
            value,
            key=lambda item: (
                item.bounding_box.top_left.x,
                item.bounding_box.top_left.y,
            ),
        )

    @property
    def text(self) -> str:
        """Get the full text of the block.
        If child type is words, join text by spaces.
        Otherwise join text by carriage returns.
        This automatically adds additional CRs between blocks/paragraphs.
        """
        if self.child_type == BlockChildType.WORDS:
            return " ".join(item.text for item in self.items)
        elif self.block_category == BlockCategory.PARAGRAPH:
            return "\n".join(item.text for item in self.items)
        else:
            return "\n\n".join(item.text for item in self.items)

    def words(self) -> list[Word]:
        """Get flat list of all words in the block"""
        if self.child_type == BlockChildType.WORDS:
            return list(self.items)
        else:
            return list(
                itertools.chain.from_iterable([item.words() for item in self.items])
            )

    def lines(self) -> List["Block"]:
        """Get flat list of all 'lines' in the block"""
        if self.child_type == BlockChildType.WORDS:
            return [self]
        else:
            return list(
                itertools.chain.from_iterable([item.lines() for item in self.items])
            )

    def ocr_confidence_scores(self) -> list[float]:
        """Get a list of the OCR confidence scores of all nested words"""
        if not self.items:
            return []
        if self.child_type == BlockChildType.WORDS:
            return [item.ocr_confidence for item in self.items]
        else:
            return list(
                itertools.chain.from_iterable(
                    [item.ocr_confidence_scores() for item in self.items]
                )
            )

    def mean_ocr_confidence(self) -> float:
        """Get the mean of the OCR confidence score of all items"""
        scores = self.ocr_confidence_scores()
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary"""
        return {
            "type": "Block",
            "child_type": self.child_type.value,
            "block_category": self.block_category.value,
            "block_labels": self.block_labels,
            "bounding_box": self.bounding_box.to_dict() if self.bounding_box else None,
            "items": [item.to_dict() for item in self.items] if self.items else [],
        }

    def from_dict(dict) -> "Block":
        """Create OCRBlock from dictionary"""
        if dict.get("child_type"):
            child_type = BlockChildType(dict["child_type"])
        else:
            child_type = BlockChildType.WORDS

        if child_type == BlockChildType.WORDS:
            items = [Word.from_dict(item) for item in dict["items"]]
        else:
            items = [Block.from_dict(item) for item in dict["items"]]

        return Block(
            items=SortedList(
                items,
                key=lambda item: item.bounding_box.top_left.y,
            ),
            bounding_box=BoundingBox.from_dict(dict["bounding_box"]),
            child_type=child_type,
            block_category=BlockCategory(dict.get("block_category")),
            block_labels=dict.get("block_labels", []),
        )
