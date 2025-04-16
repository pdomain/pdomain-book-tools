from dataclasses import dataclass
from typing import Optional, Sequence, Tuple, Union

from .point import Point

# Try to import shapely, but don't fail if not installed
try:
    from shapely.geometry import Point as ShapelyPoint
    from shapely.geometry import Polygon as ShapelyPolygon
    from shapely.geometry import box as shapely_box

    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False

from logging import getLogger

from cv2 import (
    CHAIN_APPROX_SIMPLE,
    COLOR_BGR2GRAY,
    RETR_EXTERNAL,
    THRESH_BINARY,
    THRESH_OTSU,
    cvtColor,
    findContours,
    threshold,
)
from numpy import max as np_max
from numpy import min as np_min
from numpy import ndarray
from numpy import vstack as np_vstack

# Configure logging
logger = getLogger(__name__)


@dataclass
class BoundingBox:
    """2D bounding box coordinates (x_min, y_min, x_max, y_max)"""

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

    @property
    def area(self) -> float:
        """Get area of the box"""
        return self.width * self.height

    @property
    def center(self) -> Point:
        """Get center point of the box"""
        return Point(
            (self.top_left.x + self.bottom_right.x) / 2,
            (self.top_left.y + self.bottom_right.y) / 2,
        )

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
    def is_shapely_available(cls):
        return SHAPELY_AVAILABLE

    @classmethod
    def _fail_if_shapely_not_available(cls):
        if not cls.is_shapely_available():
            raise ImportError(
                "Shapely is required for this operation. "
                "Install it with 'pip install shapely'."
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
            elif cls.is_shapely_available() and isinstance(p, ShapelyPoint):
                converted_points.append(Point(p.x, p.y))
            elif isinstance(p, Point):
                converted_points.append(p)
            elif len(p) == 2:
                converted_points.append(Point(p[0], p[1]))

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

    def to_ltwh(self) -> Tuple["Point", float, float]:
        """Convert to ((left, top), width, height) format"""
        return (
            self.top_left,
            self.bottom_right.x - self.top_left.x,
            self.bottom_right.y - self.top_left.y,
        )

    def to_scaled_ltwh(
        self, width: int, height: int
    ) -> Tuple[float, float, float, float]:
        """Convert to (left, top, width, height) format with absolute pixel coordinates"""
        lt, width, height = self.to_ltwh()
        return lt.scale(width, height) + (width * width, height * height)

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
        """Check if this bounding box intersects with another"""
        intersects_on_x_axis = self.minX <= other.maxX and self.maxX >= other.minX
        intersects_on_y_axis = self.minY <= other.maxY and self.maxY >= other.minY
        return intersects_on_x_axis and intersects_on_y_axis

    def intersection(self, other: "BoundingBox") -> Optional["BoundingBox"]:
        """Get the intersection of this bounding box with another"""
        if not self.intersects(other):
            return None

        return BoundingBox(
            Point(
                max(self.top_left.x, other.top_left.x),
                max(self.top_left.y, other.top_left.y),
            ),
            Point(
                min(self.bottom_right.x, other.bottom_right.x),
                min(self.bottom_right.y, other.bottom_right.y),
            ),
        )

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
        """Get the union BoundingBox from a sequence of bounding boxes"""
        if not bounding_boxes:
            raise ValueError("Bounding box list is empty")

        top_left = Point(float("inf"), float("inf"))
        bottom_right = Point(float("-inf"), float("-inf"))
        for bbox in bounding_boxes:
            top_left = Point(
                min(top_left.x, bbox.top_left.x),
                min(top_left.y, bbox.top_left.y),
            )
            bottom_right = Point(
                max(bottom_right.x, bbox.bottom_right.x),
                max(bottom_right.y, bbox.bottom_right.y),
            )
        return cls(top_left, bottom_right)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary"""
        return {
            "top_left": self.top_left.to_dict(),
            "bottom_right": self.bottom_right.to_dict(),
        }

    def from_dict(dict) -> "BoundingBox":
        """Create BoundingBox from dictionary"""
        return BoundingBox(
            top_left=Point.from_dict(dict["top_left"]),
            bottom_right=Point.from_dict(dict["bottom_right"]),
        )

    def refine(self, image: ndarray) -> "BoundingBox":
        """
        Returns a new bounding box to better fit the text within the given OpenCV image.

        Args:
            image (numpy.ndarray): The OpenCV image containing the text.

        Returns:
            BoundingBox: A new bounding box that tightly fits the detected text.
        """
        # Extract the region of interest (ROI) from the image
        h, w = image.shape[:2]
        x1, y1, x2, y2 = (self.scale(width=w, height=h)).to_ltrb()

        logger.debug(f"Region of Interest: ({x1}, {y1}, {x2}, {y2})")

        roi = image[y1:y2, x1:x2]

        # Convert to grayscale if the image is not already
        if len(roi.shape) == 3:
            roi_gray = cvtColor(roi, COLOR_BGR2GRAY)
        else:
            roi_gray = roi

        # Apply thresholding to isolate text
        _, thresh = threshold(roi_gray, 0, 255, THRESH_BINARY + THRESH_OTSU)

        # Find contours in the thresholded image
        contours, _ = findContours(thresh, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)

        # If no contours are found, return the original bounding box
        if not contours:
            logger.debug("No Contours Found")
            bbox = BoundingBox.from_ltrb(self.minX, self.minY, self.maxX, self.maxY)
        else:
            logger.debug("Computing Min/Max for all contours")
            # Concatenate all contours into a single array
            # Shape is (N, 1, 2 [0=x,1=y])
            #   N is total number of points across all countours
            all_points = np_vstack(contours)

            # Calculate the bounding box using NumPy
            x_min = np_min(all_points[:, 0, 0])
            y_min = np_min(all_points[:, 0, 1])
            x_max = np_max(all_points[:, 0, 0])
            y_max = np_max(all_points[:, 0, 1])

            # Restore location of bounding box from ROI
            x_min += x1
            y_min += y1
            x_max += x1
            y_max += y1

            # Return a new bounding Box
            bbox = BoundingBox.from_ltrb(
                x_min,
                y_min,
                x_max,
                y_max,
            )
            logger.debug(f"New bbox: ({x_min}, {y_min}, {x_max}, {y_max})")

        bbox = bbox.normalize(width=w, height=h)
        logger.debug(f"Normalized Bbox:\n{bbox.to_dict()}")
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
        cls._fail_if_shapely_not_available()

        try:
            minx, miny, maxx, maxy = shapely_box.bounds
            return cls(Point(minx, miny), Point(maxx, maxy))
        except AttributeError:
            raise ValueError(
                "Input must be a valid Shapely geometry with a bounds property"
            )

    def as_shapely(self) -> Union["ShapelyPolygon", None]:
        """
        Convert to Shapely box geometry.

        Returns:
            Shapely box if shapely is installed, otherwise throw error

        Raises:
            ImportError: If shapely is not installed
        """
        self._fail_if_shapely_not_available()

        return shapely_box(
            self.top_left.x,
            self.top_left.y,
            self.bottom_right.x,
            self.bottom_right.y,
        )
