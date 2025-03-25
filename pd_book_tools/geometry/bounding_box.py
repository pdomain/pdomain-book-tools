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

    def scale(self, width: int, height: int) -> Tuple["Point", "Point"]:
        """Convert normalized coordinates to absolute pixel coordinates"""
        return (
            Point(self.top_left.x * width, self.top_left.y * height),
            Point(self.bottom_right.x * width, self.bottom_right.y * height),
        )

    def contains_point(self, point: Point) -> bool:
        """Check if the bounding box contains the given point"""
        return (
            self.top_left.x <= point.x <= self.bottom_right.x
            and self.top_left.y <= point.y <= self.bottom_right.y
        )

    def intersects(self, other: "BoundingBox") -> bool:
        """Check if this bounding box intersects with another"""
        return (
            self.top_left.x <= other.bottom_right.x
            and self.bottom_right.x >= other.top_left.x
            and self.top_left.y <= other.bottom_right.y
            and self.bottom_right.y >= other.top_left.y
        )

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
