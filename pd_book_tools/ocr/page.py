import itertools
from dataclasses import dataclass, field
from typing import Any, Collection, Dict, List, Optional

from numpy import ndarray, mean as np_mean, median as np_median, std as np_std
from sortedcontainers import SortedList

from ..geometry import BoundingBox
from .block import Block, BlockCategory
from .word import Word


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
    cv2_numpy_page_image: Optional[ndarray] = None

    unmatched_ground_truth_lines: list[(int, str)] = field(default_factory=list)
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
        self.cv2_numpy_page_image = cv2_numpy_page_image

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

    @property
    def words(self) -> List[Word]:
        """Get flat list of all words in the block"""
        return list(itertools.chain.from_iterable([item.words for item in self.items]))

    @property
    def lines(self) -> List["Block"]:
        """Get flat list of all 'lines' in the page"""
        return list(itertools.chain.from_iterable([item.lines for item in self.items]))

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
            bounding_box=self.bounding_box.scale(width, height),
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

    def reorganize_page(self):
        """
        Reogranize the page into paragraphs and blocks.
        This is a post-processing step to ensure that the text is
        organized into logical sections for text generated output.
        """
        row_blocks = self.compute_text_row_blocks(self.lines)
        reset_paragraph_blocks = []
        for b in list(row_blocks.items):
            paragraphs = self.compute_text_paragraph_blocks(b.lines)
            reset_paragraph_blocks.append(paragraphs)
        self.items = reset_paragraph_blocks

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
    def compute_text_row_blocks(cls, lines: List[Block], tolerance=None):
        """
        Use dynamic vertical spacing to group lines into "blocks" of text.

        This generally splits a page into logical sections
        like headers, body, blockquotes, and footers.

        After finding blocks, we can compute columns within each block.
        """
        # Single Line Block
        if len(lines) < 2:
            return [lines]

        # Tolerance is 20% of average line height by default
        if tolerance is None:
            tolerance = 0.2 * np_mean([line.bounding_box.height for line in lines])

        # Sort lines by their Y position
        lines.sort(key=lambda line: line.bounding_box.minY)

        # Compute spacing after each line
        min_y_positions = [line.bounding_box.minY for line in lines]
        max_y_positions = [line.bounding_box.maxY for line in lines]

        # Compute difference between the max Y of the previous line and the min Y of the current line
        line_spacings = [
            max(0, min_y_positions[i] - max_y_positions[i - 1])
            for i in range(1, len(lines))
        ]

        # This gives us the spacing between lines, which we can use to determine
        # if they are part of the same block or not. "blocks" will be separated by
        # vertical gaps larger than the norm.

        # Use 1/4 of the standard deviation, or 10% of the avarage line height
        # as the tolerance for line spacing
        median_line_height_spacing = (
            np_median([line.bounding_box.height for line in lines]) * 0.10
        )
        std_line_height_spacing = np_std(line_spacings) * 0.25

        tolerance_spacing = tolerance + max(
            std_line_height_spacing, (median_line_height_spacing * 0.10)
        )

        blocks = []
        current_block = [lines[0]]
        for i in range(1, len(lines)):
            prev_line_space_after = line_spacings[i - 1]
            if prev_line_space_after > 0 and prev_line_space_after > tolerance_spacing:
                b = Block(items=current_block, block_category=BlockCategory.PARAGRAPH)
                blocks.append(b)
                current_block = [lines[i]]
            else:
                current_block.append(lines[i])

        # Final Block
        if current_block:
            b = Block(items=current_block, block_category=BlockCategory.PARAGRAPH)
            blocks.append(b)

        new_block = Block(items=blocks, block_category=BlockCategory.BLOCK)
        return new_block

    @classmethod
    def compute_text_paragraph_blocks(cls, lines: List[Block]):
        min_x_positions = [line.bounding_box.minX for line in lines]
        max_x_positions = [line.bounding_box.maxX for line in lines]

        median_line_length = np_median([line.bounding_box.width for line in lines])

        median_left_indent = np_median(min_x_positions)
        median_right_indent = np_median(max_x_positions)

        left_tolerance = 0.02 * median_line_length  # np.std(min_x_positions) * 2
        right_tolerance = 0.02 * median_line_length  # np.std(max_x_positions) * 2

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
        for i in range(1, len(lines)):
            # If previous line right indent is < median,
            #   previous line is end of paragraph
            # If current line left indent is > median, start of paragraph

            prev_x_end_paragraph = max_x_positions[i - 1] <= right_min
            current_x_start_paragraph = min_x_positions[i] >= left_max

            if (prev_x_end_paragraph) or (current_x_start_paragraph):
                b = Block(items=current_block, block_category=BlockCategory.PARAGRAPH)
                blocks.append(b)
                current_block = [lines[i]]
            else:
                current_block.append(lines[i])

        # Final Block
        if current_block:
            b = Block(items=current_block, block_category=BlockCategory.PARAGRAPH)
            blocks.append(b)

        new_block = Block(items=blocks, block_category=BlockCategory.BLOCK)
        return new_block

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
