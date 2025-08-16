from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple, Union

import cv2

from pd_book_tools.geometry.point import Point
from shapely.geometry import Point as ShapelyPoint
from shapely.geometry import Polygon as ShapelyPolygon
from shapely.geometry import box as shapely_box
from shapely.ops import unary_union

from logging import getLogger

from cv2 import (
    COLOR_BGR2GRAY,
    THRESH_BINARY,
    THRESH_OTSU,
    cvtColor,
    findNonZero,
    threshold,
)
from numpy import ndarray

# Configure logging
logger = getLogger(__name__)


@dataclass
class BoundingBox:
    """Axis-aligned bounding box.

    Internally represented with two corner points (top-left & bottom-right)
    to stay consistent with earlier code. Optional integration with shapely
    provides more powerful spatial operations when installed while falling
    back to minimal manual implementations otherwise.
    """

    top_left: Point
    bottom_right: Point

    @property
    def minX(self) -> float:
        return self.top_left.x

    @property
    def minY(self) -> float:
        return self.top_left.y

    @property
    def maxX(self) -> float:
        return self.bottom_right.x

    @property
    def maxY(self) -> float:
        return self.bottom_right.y

    @property
    def lrtb(self) -> Tuple[float, float, float, float]:
        return self.minX, self.minY, self.maxX, self.maxY

    @property
    def width(self) -> float:
        """Get width of the box"""
        return self.bottom_right.x - self.top_left.x

    @property
    def height(self) -> float:
        """Get height of the box"""
        return self.bottom_right.y - self.top_left.y

    @property
    def size(self) -> Tuple[float, float]:
        """Get (width, height) of the box"""
        return self.width, self.height

    @property
    def lrwh(self) -> Tuple[float, float, float, float]:
        return self.minX, self.minY, self.width, self.height

    def get_four_point_scaled_polygon_list(
        self, width: int, height: int
    ) -> List[List[float]]:
        """Get four points of the box"""
        return [
            [int(self.minX * width), int(self.minY * height)],
            [int(self.maxX * width), int(self.minY * height)],
            [int(self.maxX * width), int(self.maxY * height)],
            [int(self.minX * width), int(self.maxY * height)],
        ]

    @property
    def area(self) -> float:
        """Area of the bounding box."""
        return float(self.as_shapely().area)  # type: ignore

    @property
    def center(self) -> Point:
        """Get center point of the box"""
        return Point(
            (self.top_left.x + self.bottom_right.x) / 2,
            (self.top_left.y + self.bottom_right.y) / 2,
        )

    def split_x_offset(self, x_offset: float) -> Tuple["BoundingBox", "BoundingBox"]:
        """Split the bounding box into two boxes using the given x offset"""
        if x_offset < 0 or x_offset > self.width:
            raise ValueError("x_offset is out of range for bounding box")

        left_box = BoundingBox(
            top_left=self.top_left,
            bottom_right=Point(self.top_left.x + x_offset, self.bottom_right.y),
        )
        right_box = BoundingBox(
            top_left=Point(self.top_left.x + x_offset, self.top_left.y),
            bottom_right=self.bottom_right,
        )
        return left_box, right_box

    def split_x_absolute(
        self, x_absolute: float
    ) -> Tuple["BoundingBox", "BoundingBox"]:
        """Split the bounding box into two boxes at the given x index"""
        if x_absolute < self.top_left.x or x_absolute > self.bottom_right.x:
            raise ValueError("index is out of range for bounding box")

        left_box = BoundingBox(
            top_left=self.top_left,
            bottom_right=Point(x_absolute, self.bottom_right.y),
        )
        right_box = BoundingBox(
            top_left=Point(x_absolute, self.top_left.y),
            bottom_right=self.bottom_right,
        )
        return left_box, right_box

    # Initialization Checks
    def __post_init__(self):
        """Validate the bounding box coordinates"""
        if (
            self.top_left.x > self.bottom_right.x
            or self.top_left.y > self.bottom_right.y
        ):
            raise ValueError(
                "Invalid bounding box coordinates: x_min must be <= x_max and y_min must be <= y_max"
            )


    @classmethod
    def from_points(
        cls,
        points: Sequence[Union[dict, "Point", "ShapelyPoint", Sequence[float]]],
    ):
        """Create from a sequence of two Point instances, Shapely points, dicts with "x" and "y" keys, or sequences of 2 floats"""
        if len(points) != 2:
            raise ValueError("Bounding box should have exactly 2 points")

        converted_points = []
        for p in points:
            if isinstance(p, dict):
                if "x" not in p or "y" not in p:
                    raise ValueError("Dictionary should have 'x' and 'y' keys")
                converted_points.append(Point(p["x"], p["y"]))
            elif isinstance(p, ShapelyPoint):  # type: ignore
                if hasattr(p, "x") and hasattr(p, "y"):
                    converted_points.append(Point(p.x, p.y))  # type: ignore
                else:
                    raise ValueError("ShapelyPoint should have 'x' and 'y' attributes")
            elif isinstance(p, Point):
                converted_points.append(p)
            elif len(p) == 2:  # type: ignore
                converted_points.append(Point(p[0], p[1]))  # type: ignore

        if not (
            converted_points[1].x > converted_points[0].x
            and converted_points[1].y > converted_points[0].y
        ):
            raise ValueError(
                "Second point should have larger x and y coordinates than the first point"
            )
        return cls(converted_points[0], converted_points[1])

    @classmethod
    def from_float(cls, points: Sequence[float]):
        """Create from [x_min, y_min, x_max, y_max] format"""
        if len(points) != 4:
            raise ValueError(
                "Bounding box should have exactly 4 coordinates: x_min, y_min, x_max, y_max"
            )
        if points[0] > points[2] or points[1] > points[3]:
            raise ValueError(
                "Bounding box coordinates are not in correct order. x_min < x_max and y_min < y_max"
            )
        return cls(Point(points[0], points[1]), Point(points[2], points[3]))

    @classmethod
    def from_nested_float(cls, points: Sequence[Sequence[float]]):
        """Create from [[x_min, y_min], [x_max, y_max]] format"""
        if len(points) != 2:
            raise ValueError("Bounding box should have exactly 2 points")
        if len(points[0]) != 2 or len(points[1]) != 2:
            raise ValueError("Each point should have exactly 2 coordinates: x, y")
        if points[0][0] > points[1][0] or points[0][1] > points[1][1]:
            raise ValueError(
                "Bounding box coordinates are not in correct order. x_min < x_max and y_min < y_max"
            )
        return cls(Point(points[0][0], points[0][1]), Point(points[1][0], points[1][1]))

    @classmethod
    def from_ltrb(cls, left: float, top: float, right: float, bottom: float):
        """Create from left, top, right, bottom format"""
        if left > right or top > bottom:
            raise ValueError(
                "Bounding box coordinates are not in correct order. left < right and top < bottom"
            )
        return cls(Point(left, top), Point(right, bottom))

    @classmethod
    def from_ltwh(cls, left: float, top: float, width: float, height: float):
        """Create from left, top, width, height format"""
        if width < 0 or height < 0:
            raise ValueError("Bounding box width and height must be non-negative")
        return cls(Point(left, top), Point(left + width, top + height))

    def to_points(self) -> Tuple["Point", "Point"]:
        """Convert to (Point,Point) format (top left point, bottom right point)"""
        return (self.top_left, self.bottom_right)

    def to_ltrb(self) -> Tuple[float, float, float, float]:
        """Convert to (left, top, right, bottom) format"""
        return (
            self.top_left.x,
            self.top_left.y,
            self.bottom_right.x,
            self.bottom_right.y,
        )

    def to_ltwh(self) -> Tuple[float, float, float, float]:
        """Convert to (left, top, width, height) format"""
        return (
            self.top_left.x,
            self.top_left.y,
            self.bottom_right.x - self.top_left.x,
            self.bottom_right.y - self.top_left.y,
        )

    def to_scaled_ltwh(
        self, width: int, height: int
    ) -> Tuple[float, float, float, float]:
        """Convert to (left, top, width, height) format with absolute pixel coordinates"""
        scaled: BoundingBox = self.scale(width, height)
        return scaled.to_ltwh()

    def scale(self, width: int, height: int) -> "BoundingBox":
        """
        Return new BoundingBox, with normalized coordinates converted
        to absolute pixel coordinates
        """
        return BoundingBox(
            top_left=self.top_left.scale(width, height),
            bottom_right=self.bottom_right.scale(width, height),
        )

    def normalize(self, width: int, height: int) -> "BoundingBox":
        """
        Return new BoundingBox, with absolute coordinates converted
        to normalized pixel coordinates
        """
        return BoundingBox(
            top_left=self.top_left.normalize(width, height),
            bottom_right=self.bottom_right.normalize(width, height),
        )

    def contains_point(self, point: Point) -> bool:
        """Check if the bounding box contains the given point"""
        return (
            self.top_left.x <= point.x <= self.bottom_right.x
            and self.top_left.y <= point.y <= self.bottom_right.y
        )

    def intersects(self, other: "BoundingBox") -> bool:
        """Return True if this bounding box intersects with another."""
        return self.as_shapely().intersects(other.as_shapely())  # type: ignore

    def intersection(self, other: "BoundingBox") -> Optional["BoundingBox"]:
        """Return the geometric intersection or None."""
        inter = self.as_shapely().intersection(other.as_shapely())  # type: ignore
        if inter.is_empty:  # type: ignore
            return None
        minx, miny, maxx, maxy = inter.bounds  # type: ignore
        if minx == maxx or miny == maxy:
            return None
        return BoundingBox(Point(minx, miny), Point(maxx, maxy))

    def overlap_y_amount(self, other: "BoundingBox"):
        """Return the amount of overlap on the y-axis (even if it doesn't directly intersect)"""
        overlap_top = max(self.minY, other.minY)
        overlap_bottom = min(self.maxY, other.maxY)

        return max(overlap_bottom - overlap_top, 0)

    def overlap_x_amount(self, other: "BoundingBox"):
        """Return the amount of overlap on the x-axis (even if it doesn't directly intersect)"""
        overlap_left = max(self.minX, other.minX)
        overlap_right = min(self.maxX, other.maxX)

        return max(overlap_right - overlap_left, 0)

    @classmethod
    def union(cls, bounding_boxes: Sequence["BoundingBox"]) -> "BoundingBox":
        """Return the minimal box covering all provided boxes.

        When shapely is available we leverage unary_union to support future
        extension (e.g., rotated boxes). For current axis-aligned rectangles
        this reduces to bounds of all boxes.
        """
        if not bounding_boxes:
            raise ValueError("Bounding box list is empty")
        geom = unary_union([b.as_shapely() for b in bounding_boxes])  # type: ignore
        minx, miny, maxx, maxy = geom.bounds  # type: ignore
        return cls(Point(minx, miny), Point(maxx, maxy))

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary"""
        return {
            "top_left": self.top_left.to_dict(),
            "bottom_right": self.bottom_right.to_dict(),
        }

    @classmethod
    def from_dict(cls, dict: Dict) -> "BoundingBox":
        """Create BoundingBox from dictionary"""
        tl = dict["top_left"]
        br = dict["bottom_right"]
        return BoundingBox(
            top_left=Point(tl["x"], tl["y"]),
            bottom_right=Point(br["x"], br["y"]),
        )

    def refine(self, image: ndarray, padding_px: int = 0) -> "BoundingBox":
        """
        Returns a new bounding box to better fit the text within the given OpenCV image.

        Args:
            image (numpy.ndarray): The OpenCV image containing the text.

        Returns:
            BoundingBox: A new bounding box that tightly fits the detected text.
        """
        # Extract the region of interest (ROI) from the image
        img_h, img_w = image.shape[:2]
        x1, y1, x2, y2 = (self.scale(width=img_w, height=img_h)).to_ltrb()

        logger.debug(f"Region of Interest: ({x1}, {y1}, {x2}, {y2})")

        roi = image[y1:y2, x1:x2]

        # Convert to grayscale if the image is not already
        if len(roi.shape) == 3:
            roi_gray = cvtColor(roi, COLOR_BGR2GRAY)
        else:
            roi_gray = roi

        inverted_image = cv2.bitwise_not(roi_gray)

        # Apply thresholding to isolate text from inverted image
        _, thresh = threshold(inverted_image, 0, 255, THRESH_BINARY + THRESH_OTSU)

        # Find non-zero pixels in the thresholded image
        non_zero_coords = findNonZero(thresh)

        if non_zero_coords is None:
            logger.debug("No non-zero pixels found")
            # return a copy of self via serialization
            return self.from_dict(self.to_dict())

        x, y, w, h = cv2.boundingRect(non_zero_coords)
        logger.debug(f"Bounding Rect: ({x}, {y}, {w}, {h})")

        # Restore location of bounding box from ROI
        x_min = x1 + x
        y_min = y1 + y
        x_max = x1 + x + w + 1  # +1 to include the right edge
        y_max = y1 + y + h + 1  # +1 to include the bottom edge

        # Apply padding to the bounding box
        x_min = max(0, x_min - padding_px)
        y_min = max(0, y_min - padding_px)
        x_max = min(img_w, x_max + padding_px)
        y_max = min(img_h, y_max + padding_px)

        # Return a new bounding box
        bbox = BoundingBox.from_ltrb(
            x_min,
            y_min,
            x_max,
            y_max,
        )
        logger.debug(f"New bbox: ({x_min}, {y_min}, {x_max}, {y_max})")

        bbox = bbox.normalize(width=img_w, height=img_h)
        logger.debug(f"Normalized Bbox:\n{bbox.to_dict()}")
        return bbox

    def expand_to_content(
        self, image: ndarray, recurse_depth: int = 0
    ) -> "BoundingBox":
        """
        Expand the bounding box to include additional pixels connected to the text within the given OpenCV image.
        Args:
            image (numpy.ndarray): The OpenCV image containing the text.
        Returns:
            BoundingBox: A new bounding box that includes the pixels that are connected to the existing pixels of the bounding box.
        """
        # iterate over the bounding box X and Y coordinates, checking for non-zero pixels

        img_h, img_w = image.shape[:2]
        x1, y1, x2, y2 = (self.scale(width=img_w, height=img_h)).to_ltrb()

        logger.debug(f"Expanding bounding box: ({x1}, {y1}, {x2}, {y2})")

        # Extract ROI
        roi = image[y1:y2, x1:x2]

        # Convert the ROI to grayscale if needed
        if len(roi.shape) == 3:
            roi_gray = cvtColor(roi, COLOR_BGR2GRAY)
        else:
            roi_gray = roi

        if len(image.shape) == 3:
            image = cvtColor(image, COLOR_BGR2GRAY)
        else:
            image = image

        image = cv2.bitwise_not(image)
        _, image = threshold(image, 0, 255, THRESH_BINARY + THRESH_OTSU)

        # Invert and threshold
        inverted_roi = cv2.bitwise_not(roi_gray)
        _, thresh = threshold(inverted_roi, 0, 255, THRESH_BINARY + THRESH_OTSU)

        # Find nonzero pixels in ROI
        non_zero_coords = findNonZero(thresh)
        if non_zero_coords is None:
            logger.debug("No non-zero pixels found")
            return BoundingBox.from_dict(self.to_dict())

        non_zero_coords = non_zero_coords.reshape(-1, 2)  # (N, 2)

        roi_h, roi_w = thresh.shape

        # Check edges of ROI
        top_edge = non_zero_coords[non_zero_coords[:, 1] == 0]
        bottom_edge = non_zero_coords[non_zero_coords[:, 1] == roi_h - 1]
        left_edge = non_zero_coords[non_zero_coords[:, 0] == 0]
        right_edge = non_zero_coords[non_zero_coords[:, 0] == roi_w - 1]

        # Expand bbox in image coordinates
        expand_top = False
        if y1 > 0:
            for x, y in top_edge:
                if image[int(y1 - 1), int(x1 + x)] > 0:
                    expand_top = True
                    logger.debug(
                        f"found non-zero pixel above top edge at {x1 + x}, {y1 - 1}"
                    )
                    break

        expand_bottom = False
        if y2 < img_h:
            for x, y in bottom_edge:
                if image[int(y2), int(x1 + x)] > 0:
                    expand_bottom = True
                    logger.debug(
                        f"found non-zero pixel below bottom edge at {x1 + x}, {y2}"
                    )
                    break

        expand_left = False
        if x1 > 0:
            for x, y in left_edge:
                if image[int(y1 + y), int(x1 - 1)] > 0:
                    expand_left = True
                    logger.debug(
                        f"found non-zero pixel left of left edge at {x1 - 1}, {y1 + y}"
                    )
                    break

        expand_right = False
        if x2 < img_w:
            for x, y in right_edge:
                if image[int(y1 + y), int(x2)] > 0:
                    expand_right = True
                    logger.debug(
                        f"found non-zero pixel right of right edge at {x2}, {y1 + y}"
                    )
                    break

        if expand_top:
            y1 = max(0, y1 - 1)
        if expand_bottom:
            y2 = min(img_h, y2 + 1)
        if expand_left:
            x1 = max(0, x1 - 1)
        if expand_right:
            x2 = min(img_w, x2 + 1)
        ox1, oy1, ox2, oy2 = self.scale(width=img_w, height=img_h).to_ltrb()

        logger.debug(f"Expanded bbox: ({x1}, {y1}, {x2}, {y2})")
        logger.debug(f"Original bbox: ({ox1}, {oy1}, {ox2}, {oy2})")

        # if the bounding box has not changed, return a copy of self
        if (x1, y1, x2, y2) == (ox1, oy1, ox2, oy2):
            logger.debug("Bounding box has not changed, returning a copy of self")
            return BoundingBox.from_dict(self.to_dict())

        # Return a new bounding box
        bbox = BoundingBox.from_ltrb(
            x1,
            y1,
            x2,
            y2,
        ).normalize(width=img_w, height=img_h)

        logger.debug("BBox expanded. Recursing to check next iteration")

        # recursively call expand to ensure all connected pixels are included
        recurse_depth = recurse_depth + 1
        if recurse_depth < 10:
            # Only go up to 10 pixels. Any worse and it's probably a bad bbox
            bbox = bbox.expand_to_content(image, recurse_depth=recurse_depth)
        else:
            logger.debug("Max recursion depth reached, returning bounding box")

        return bbox

    def crop_bottom(self, image: ndarray) -> "BoundingBox":
        """
        Crop the bounding box to only include text (nonzero pixels) that are vertically
        contiguous with pixels that can be reached below the center row of the bounding box.
        This method starts from the center row of the bounding box, checks for non-zero pixels,
        and for each row below, only keeps pixels that are directly below at least one pixel
        from the previous row. This effectively crops the bounding box to the vertically-connected
        center character(s) in the image.

        Unfortunately, this method is not useful for text that is not vertically connected below in some scripts.
        But for english text, it works well to crop the bottom of the bounding box.

        Args:
            image (numpy.ndarray): The OpenCV image containing the text.

        Returns:
            BoundingBox: A new bounding box with bottom cropped.
        """

        logger.debug("Cropping bottom of bounding box to vertically connected text")

        img_h, img_w = image.shape[:2]
        x1, y1, x2, y2 = (self.scale(width=img_w, height=img_h)).to_ltrb()

        # Extract ROI
        roi = image[y1:y2, x1:x2]

        # Convert ROI to grayscale if needed
        if len(roi.shape) == 3:
            roi_gray = cvtColor(roi, COLOR_BGR2GRAY)
        else:
            roi_gray = roi

        # Invert and threshold to get text as white on black
        inverted_roi = cv2.bitwise_not(roi_gray)
        _, thresh = threshold(inverted_roi, 0, 255, THRESH_BINARY + THRESH_OTSU)

        roi_h, roi_w = thresh.shape

        # Find nonzero pixels in ROI
        non_zero_coords = findNonZero(thresh)
        if non_zero_coords is None:
            logger.debug("No non-zero pixels found")
            return BoundingBox.from_dict(self.to_dict())

        non_zero_coords = non_zero_coords.reshape(-1, 2)  # (N, 2)

        center_y = roi_h // 2

        # drop all pixels above the center row
        non_zero_coords = non_zero_coords[non_zero_coords[:, 1] >= center_y]
        if non_zero_coords.size == 0:
            logger.debug("No non-zero pixels found below the center row")
            return BoundingBox.from_dict(self.to_dict())

        logger.debug(
            f"Center row: {center_y}, non-zero pixels below center: {non_zero_coords.shape[0]}"
        )

        # itearate over the rows below the center row
        for y in range(center_y + 1, roi_h):
            logger.debug("Checking row with pixels for non-zero pixels")

            current_row_x = set(non_zero_coords[non_zero_coords[:, 1] == y][:, 0])
            prev_row_x = set(non_zero_coords[non_zero_coords[:, 1] == y - 1][:, 0])
            if not prev_row_x and current_row_x:
                logger.debug(
                    "Prev Row has no pixels, current row has at least one pixel, continuing search"
                )
                continue
            # Check if any x in current_row_x is also in prev_row_x
            if current_row_x & prev_row_x:
                logger.debug(f"Row {y} has matching pixel, continuing search")
                continue
            # No connectivity, crop here
            y2 = y1 + y
            logger.debug(f"New bottom y-coordinate: {y2}")
            break

            # # get all pixels in the current row
            # current_row_coords = non_zero_coords[non_zero_coords[:, 1] == y]
            # logger.debug(f"Row {y} has {current_row_coords.shape[0]} pixels")
            # # get all pixels in the previous row
            # previous_row_coords = non_zero_coords[non_zero_coords[:, 1] == y - 1]

            # if previous_row_coords.size == 0:
            #     continue
            # # check each pixel in the current row, compare to the pixel directly above it
            # # if any pixel in the current row is directly below a pixel in the previous row, keep it
            # match = False
            # if not (current_row_coords.size == 0):
            #     for cx, cy in current_row_coords:
            #         # check if there is a pixel directly above the current pixel in the previous row
            #         for px, py in previous_row_coords:
            #             if px == cx and py == cy - 1:
            #                 # we have a match, keep the current row
            #                 logger.debug(
            #                     f"Row {cy} has pixel ({cx}, {cy}) directly below row {cy - 1} pixel ({px}, {py}), keeping current row"
            #                 )
            #                 match = True
            #                 break
            #         if match:
            #             break
            #         # keep the current row
            # if match:
            #     logger.debug(f"Row {y} has matching pixel, continuing search")
            #     continue

            # # this means there are no pixels directly below the previous row, so we stop
            # logger.debug(f"No pixels found below row {y - 1}, stopping crop")
            # y2 = y1 + y
            # logger.debug(f"New bottom y-coordinate: {y2}")
            # break

        bbox = BoundingBox.from_ltrb(
            x1,
            y1,
            x2,
            y2,
        ).normalize(width=img_w, height=img_h)

        logger.debug(f"Cropped bounding box: ({x1}, {y1}, {x2}, {y2})")

        return bbox

    def crop_top(self, image: ndarray) -> "BoundingBox":
        """
        Crop the bounding box to only include text (nonzero pixels) that are vertically
        contiguous with pixels that can be reached above the center row of the bounding box.
        This method starts from the center row of the bounding box, checks for non-zero pixels,
        and for each row above, only keeps pixels that are directly above at least one pixel
        from the previous row. This effectively crops the bounding box to the vertically-connected
        center character(s) in the image.

        Unfortunately, this method is not useful for text that is not vertically connected above in some scripts.
        But for english text, it works well to crop the top of the bounding box, except for "i", "j", and any characters with diacritics.

        Args:
            image (numpy.ndarray): The OpenCV image containing the text.

        Returns:
            BoundingBox: A new bounding box with top cropped.
        """

        logger.debug("Cropping top of bounding box to vertically connected text")

        img_h, img_w = image.shape[:2]
        x1, y1, x2, y2 = (self.scale(width=img_w, height=img_h)).to_ltrb()

        # Extract ROI
        roi = image[y1:y2, x1:x2]

        # Convert ROI to grayscale if needed
        if len(roi.shape) == 3:
            roi_gray = cvtColor(roi, COLOR_BGR2GRAY)
        else:
            roi_gray = roi

        # Invert and threshold to get text as white on black
        inverted_roi = cv2.bitwise_not(roi_gray)
        _, thresh = threshold(inverted_roi, 0, 255, THRESH_BINARY + THRESH_OTSU)

        roi_h, roi_w = thresh.shape

        # Find nonzero pixels in ROI
        non_zero_coords = findNonZero(thresh)
        if non_zero_coords is None:
            logger.debug("No non-zero pixels found")
            return BoundingBox.from_dict(self.to_dict())

        non_zero_coords = non_zero_coords.reshape(-1, 2)

        center_y = roi_h // 2
        # drop all pixels below the center row
        non_zero_coords = non_zero_coords[non_zero_coords[:, 1] <= center_y]
        if non_zero_coords.size == 0:
            logger.debug("No non-zero pixels found above the center row")
            return BoundingBox.from_dict(self.to_dict())
        logger.debug(
            f"Center row: {center_y}, non-zero pixels above center: {non_zero_coords.shape[0]}"
        )
        # iterate over the rows above the center row
        for y in range(center_y - 1, -1, -1):
            logger.debug("Checking row with pixels for non-zero pixels")

            current_row_x = set(non_zero_coords[non_zero_coords[:, 1] == y][:, 0])
            prev_row_x = set(non_zero_coords[non_zero_coords[:, 1] == y + 1][:, 0])
            if not prev_row_x and current_row_x:
                logger.debug(
                    "Prev Row has no pixels, current row has at least one pixel, continuing search"
                )
                continue
            if current_row_x & prev_row_x:
                logger.debug(f"Row {y} has matching pixel, continuing search")
                continue
            logger.debug(f"No pixels found above row {y + 1}, stopping crop")
            y1 = y1 + y
            logger.debug(f"New top y-coordinate: {y1}")
            break

        bbox = BoundingBox.from_ltrb(
            x1,
            y1,
            x2,
            y2,
        ).normalize(width=img_w, height=img_h)

        logger.debug(f"Cropped bounding box: ({x1}, {y1}, {x2}, {y2})")

        return bbox

    # Shapely integration methods
    @classmethod
    def from_shapely(cls, shapely_box: "ShapelyPolygon") -> "BoundingBox":
        """
        Create a BoundingBox from a Shapely geometry.

        Args:
            shapely_box: Any Shapely geometry with a bounds property

        Returns:
            BoundingBox instance

        Raises:
            ImportError: If shapely is not installed
            ValueError: If input is not a valid Shapely geometry
        """
        try:
            minx, miny, maxx, maxy = shapely_box.bounds
            return cls(Point(minx, miny), Point(maxx, maxy))
        except AttributeError:
            raise ValueError(
                "Input must be a valid Shapely geometry with a bounds property"
            )

    def as_shapely(self) -> "ShapelyPolygon":
        """Return a shapely geometry for the box.

        Raises ImportError if shapely is missing.
        """
        return shapely_box(  # type: ignore
            self.top_left.x, self.top_left.y, self.bottom_right.x, self.bottom_right.y
        )

    @property
    def shapely(self) -> "ShapelyPolygon":
        return self.as_shapely()

    # Additional shapely-powered helpers ---------------------------------
    def union_with(self, other: "BoundingBox") -> "BoundingBox":
        """Return the minimal box containing this and other."""
        return self.union([self, other])

    def iou(self, other: "BoundingBox") -> float:
        """Intersection over Union metric.

        Returns 0.0 when there's no overlap.
        """
        inter = self.intersection(other)
        if not inter:
            return 0.0
        union_area = self.area + other.area - inter.area
        if union_area == 0:
            return 0.0
        return inter.area / union_area

    def expand(self, dx: float = 0.0, dy: float = 0.0) -> "BoundingBox":
        """Uniformly expand (or shrink) the box by deltas in both directions.

        Negative values shrink the box. Values are applied to each side.
        """
        return BoundingBox.from_ltrb(
            self.minX - dx, self.minY - dy, self.maxX + dx, self.maxY + dy
        )
