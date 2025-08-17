from shapely.geometry import Point as ShapelyPoint  # type: ignore


class Point:
    """2D point backed by a Shapely ``Point`` with an inferred or overridable
    ``is_normalized`` flag describing coordinate semantics.

    Classification:
        * Normalized (``is_normalized=True``): both coordinates lie in [0,1].
        * Pixel (``is_normalized=False``): any other non‑negative coordinates.

    The flag is inferred on construction and after x/y mutation, unless explicitly
    overridden via the constructor argument or the ``is_normalized`` property.

    Ordering (>, <, >=, <=) is lexicographic on the tuple (x, y) and only permitted
    when both points share the same normalization state; otherwise a TypeError is
    raised. Equality likewise requires matching normalization; attempting to compare
    points whose normalization flags differ raises TypeError. Equality is otherwise
    exact on (x, y). Use a helper for approximate comparison if needed.

    Serialization: ``to_dict()`` / ``from_dict()`` round‑trip x, y and
    ``is_normalized`` (older dicts without the flag still infer it).
    """

    __slots__ = ("_geom", "_is_normalized")

    def __init__(
        self, x: float | int, y: float | int, is_normalized: bool | None = None
    ):
        """Create a point backed directly by a Shapely Point.

        Args:
            x: X coordinate (int/float or numeric string)
            y: Y coordinate (int/float or numeric string)
            is_normalized: Optional explicit override of the inferred normalized flag.
        """
        fx, fy = self._coerce_number(x), self._coerce_number(y)
        self._geom = ShapelyPoint(float(fx), float(fy))
        self._classify()
        if is_normalized is not None:
            if is_normalized and not (self._within_unit(fx) and self._within_unit(fy)):
                raise ValueError(
                    "Cannot mark as normalized: coordinates must lie within [0,1]"
                )
            self._is_normalized = bool(is_normalized)

    # Internal -----------------------------------------------------------
    def _coerce_number(self, value: float | int | str) -> float | int:
        try:
            f = float(value)
        except (TypeError, ValueError):
            raise ValueError(
                "Point coordinates must be able to be coerced to real numbers"
            )
        # Preserve int type when exact
        return int(f) if f.is_integer() else f

    def _classify(self) -> None:
        fx = float(self._geom.x)
        fy = float(self._geom.y)
        EPS = 1e-9
        if -EPS <= fx <= 1 + EPS and -EPS <= fy <= 1 + EPS:
            if fx < 0 or fy < 0:
                raise ValueError("Pixel point coordinates must be non-negative")
            self._is_normalized = True
        else:
            if fx < 0 or fy < 0:
                raise ValueError("Pixel point coordinates must be non-negative")
            self._is_normalized = False

    def _within_unit(self, v: float | int) -> bool:
        EPS = 1e-9
        fv = float(v)
        return -EPS <= fv <= 1 + EPS and fv >= 0

    # Properties ---------------------------------------------------------
    @property
    def x(self) -> float | int:
        # Return int when representable exactly
        return int(self._geom.x) if float(self._geom.x).is_integer() else self._geom.x

    @property
    def y(self) -> float | int:
        return int(self._geom.y) if float(self._geom.y).is_integer() else self._geom.y

    @property
    def is_normalized(self) -> bool:
        return self._is_normalized

    @is_normalized.setter
    def is_normalized(self, value: bool) -> None:  # pragma: no cover - defensive
        raise AttributeError(
            "Point is immutable; use factory methods instead of mutating is_normalized"
        )

    def __getattr__(self, item):
        return getattr(self._geom, item)

    def __repr__(self) -> str:  # pragma: no cover - trivial representation
        return f"Point(x={self.x}, y={self.y}, normalized={self.is_normalized})"

    # (to_x_y removed; use (p.x, p.y) directly)

    def scale(self, width: int, height: int) -> "Point":
        """
        Scale the point to pixel coordinates based on the given width and height.
        """
        if not self.is_normalized:
            raise ValueError("scale() expected a normalized point (values in [0,1])")
        return Point.pixel(int(round(self.x * width)), int(round(self.y * height)))

    def normalize(self, width: int, height: int) -> "Point":
        """
        Normalize the point to [0,1] unit square coordinates based on the given width and height.
        """
        if self.is_normalized:
            raise ValueError("normalize() expected a pixel point (non-normalized)")
        if not (self._is_int_like(self.x) and self._is_int_like(self.y)):
            raise ValueError(
                "normalize() requires integer-like pixel coordinates (e.g., 10 or 10.0)"
            )
        return Point.normalized(
            float(self.x) / float(width), float(self.y) / float(height)
        )

    # (with_* helpers removed; construct new instances directly)

    # Alternative constructors --------------------------------------------
    @classmethod
    def normalized(cls, x: float | int, y: float | int) -> "Point":
        return cls(x, y, is_normalized=True)

    @classmethod
    def pixel(cls, x: float | int, y: float | int) -> "Point":
        return cls(x, y, is_normalized=False)

    def to_dict(self) -> dict:
        # Include normalization state for round‑trip serialization
        return {"x": self.x, "y": self.y, "is_normalized": self.is_normalized}

    @classmethod
    def from_dict(cls, data: dict) -> "Point":
        """Create a Point from a dict produced by ``to_dict``.

        Accepts legacy dicts without ``is_normalized`` (falls back to inference).
        """
        x = data["x"]
        y = data["y"]
        is_norm = data.get("is_normalized")
        return cls(x, y, is_normalized=is_norm)

    def as_shapely(self) -> "ShapelyPoint":
        return self._geom  # type: ignore

    def distance_to(self, other: "Point") -> float:
        return float(self._geom.distance(other.as_shapely()))

    # Helpers ----------------------------------------------------------
    def _is_int_like(self, value: float | int) -> bool:
        return isinstance(value, int) or (
            isinstance(value, float) and float(value).is_integer()
        )

    # Comparisons ------------------------------------------------------
    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return NotImplemented  # type: ignore[return-value]
        if self.is_normalized != other.is_normalized:
            raise TypeError("Cannot compare points with different normalization state")
        return (self.x, self.y) > (other.x, other.y)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return NotImplemented  # type: ignore[return-value]
        if self.is_normalized != other.is_normalized:
            raise TypeError("Cannot compare points with different normalization state")
        return (self.x, self.y) < (other.x, other.y)

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return NotImplemented  # type: ignore[return-value]
        if self.is_normalized != other.is_normalized:
            raise TypeError("Cannot compare points with different normalization state")
        return (self.x, self.y) >= (other.x, other.y)

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return NotImplemented  # type: ignore[return-value]
        if self.is_normalized != other.is_normalized:
            raise TypeError("Cannot compare points with different normalization state")
        return (self.x, self.y) <= (other.x, other.y)

    def __eq__(self, other: object) -> bool:  # type: ignore[override]
        if not isinstance(other, Point):
            return NotImplemented  # type: ignore[return-value]
        if self.is_normalized != other.is_normalized:
            raise TypeError("Cannot compare points with different normalization state")
        return (self.x, self.y) == (other.x, other.y)

    def __hash__(self) -> int:  # Allow use in sets / dicts
        return hash((float(self.x), float(self.y), self.is_normalized))
