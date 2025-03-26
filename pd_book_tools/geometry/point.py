from dataclasses import dataclass
from typing import Sequence, Tuple

# Try to import shapely, but don't fail if not installed
try:
    from shapely.geometry import Point as ShapelyPoint

    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False


@dataclass
class Point:
    """Point class to represent a Normalized 2D point in format [x, y]"""

    x: float
    y: float

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
    def from_float_points(cls, points: Sequence[float]):
        return cls(points[0], points[1])

    # Standard Instance methods

    def to_x_y(self) -> Tuple[float]:
        return (self.x, self.y)

    def scale(self, width: int, height: int) -> Tuple[int, int]:
        """
        Return a copy of this point, with normalized
        coordinates converted to absolute pixel coordinates
        """
        if self.x < 0 or self.x > 1 or self.y < 0 or self.y > 1:
            raise ValueError("Internal coordinates are not between 0 and 1")
        return Point(int(self.x * width), int(self.y * height))

    def is_larger_than(self, other: "Point") -> bool:
        """Check if both x and y coordinates are larger than those of another point"""
        return self.x > other.x and self.y > other.y

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary"""
        return {"x": self.x, "y": self.y}

    def from_dict(dict) -> "Point":
        """Create Point from dictionary"""
        return Point(x=dict["x"], y=dict["y"])

    # Shapely Methods

    @classmethod
    def from_shapely(
        cls,
        shapely_pixel_point: "ShapelyPoint",
    ) -> "Point":
        """
        Create a Point from a Shapely Point.

        Args:
            shapely_point: Shapely Point geometry

        Returns:
            Point instance

        Raises:
            ImportError: If shapely is not installed
            ValueError: If input is not a valid Shapely Point
        """
        cls._fail_if_shapely_not_available()
        try:
            return cls(shapely_pixel_point.x, shapely_pixel_point.y)
        except AttributeError:
            raise ValueError(
                "Input must be a valid Shapely Point with x and y attributes"
            )

    def as_shapely(self) -> "ShapelyPoint":
        """
        Convert to Shapely Point geometry.

        Returns:
            Shapely Point if shapely is installed, otherwise None

        Raises:
            ImportError: If shapely is not installed
        """
        self._fail_if_shapely_not_available()
        return ShapelyPoint(self.x, self.y)
