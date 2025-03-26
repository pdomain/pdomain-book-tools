from dataclasses import dataclass, field
import itertools
from typing import Any, Collection, Dict, List, Optional

from sortedcontainers import SortedList

from ..geometry import BoundingBox
from ._block import Block
from ._word import Word


@dataclass
class Page:
    """Represents a page (single or multiple "blocks") of OCR results"""

    width: int
    height: int
    page_index: int
    bounding_box: Optional[BoundingBox] = None
    _items: SortedList[Block] = field(
        default_factory=lambda: SortedList(
            key=lambda item: item.bounding_box.top_left.y if item.bounding_box else 0
        )
    )
    page_labels: Optional[list[str]] = None

    def __init__(
        self,
        width: int,
        height: int,
        page_index: int,
        items: Collection,
        bounding_box: Optional[BoundingBox] = None,
        page_labels: Optional[list[str]] = None,
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

    @property
    def items(self) -> SortedList:
        return self._items

    @items.setter
    def items(self, values):
        if isinstance(values, SortedList):
            self._items = values
            return
        if not isinstance(values, Collection):
            raise TypeError("items must be a collection")
        for block in values:
            if not isinstance(block, Block):
                raise TypeError("Each item in items must be of type Block")
        self._items = SortedList(
            values, key=lambda block: block.bounding_box.top_left.y
        )

    @property
    def text(self) -> str:
        """
        Get the full text of the page, separating each top-level block
        by double carriage returns and one final carraige return
        """
        return "\n\n".join(block.text for block in self.items) + "\n"

    def words(self) -> List[Word]:
        """Get flat list of all words in the block"""
        return list(
            itertools.chain.from_iterable([item.words() for item in self.items])
        )

    def lines(self) -> List["Block"]:
        """Get flat list of all 'lines' in the block"""
        return list(
            itertools.chain.from_iterable([item.lines() for item in self.items])
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
