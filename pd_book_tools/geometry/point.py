from dataclasses import dataclass
from typing import Tuple

from shapely.geometry import Point as ShapelyPoint  # type: ignore


@dataclass
class Point:
    """Point wrapper around a Shapely ``Point``.

    Simplified: all legacy factory constructors (``from_float_points``,
    ``from_dict`` and ``from_shapely``) have been removed. Use direct
    construction ``Point(x, y)`` everywhere and access the underlying
    shapely geometry via ``as_shapely()`` when needed.
    """

    x: float
    y: float

    # ------------------------------------------------------------------
    # Shapely availability helpers (retained for compatibility/tests)
    # ------------------------------------------------------------------
    @classmethod
    def is_shapely_available(cls) -> bool:  # pragma: no cover - trivial
        return True

    @classmethod
    def _fail_if_shapely_not_available(cls) -> None:  # pragma: no cover - trivial
        if not cls.is_shapely_available():  # pragma: no cover
            raise ImportError(
                "Shapely is required. Install with 'pip install shapely'."
            )

    def __post_init__(self):
        # Validate numeric input early (tests rely on ValueError for non-numeric)
        if not (isinstance(self.x, (int, float)) and isinstance(self.y, (int, float))):
            raise ValueError("Point coordinates must be numeric")
        self._geom = ShapelyPoint(float(self.x), float(self.y))  # type: ignore

    # Delegation to shapely -------------------------------------------------
    def __getattr__(self, item):  # delegate unknown attrs to shapely geometry
        return getattr(self._geom, item)

    # Basic helpers --------------------------------------------------------
    def to_x_y(self) -> Tuple[float | int, float | int]:
        return (self.x, self.y)

    def scale(self, width: int, height: int) -> "Point":
        if not (0 <= self.x <= 1 and 0 <= self.y <= 1):
            raise ValueError("Internal coordinates are not between 0 and 1")
        return Point(int(self.x * width), int(self.y * height))

    def normalize(self, width: int, height: int) -> "Point":
        if not (isinstance(self.x, int) and isinstance(self.y, int)):
            raise ValueError("Internal coordinates are not integers")
        return Point(float(self.x) / float(width), float(self.y) / float(height))

    def is_larger_than(self, other: "Point") -> bool:
        return self.x > other.x and self.y > other.y

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y}

    # Shapely access -------------------------------------------------------
    def as_shapely(self) -> "ShapelyPoint":
        return self._geom  # type: ignore

    def distance_to(self, other: "Point") -> float:
        return float(self._geom.distance(other.as_shapely()))
