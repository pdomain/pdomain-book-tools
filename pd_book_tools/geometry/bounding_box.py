from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple, Union

import cv2
from shapely.geometry import (
    Point as ShapelyPoint,
    Polygon as ShapelyPolygon,
    box as shapely_box,
)  # removed LineString import
from shapely.ops import unary_union  # removed split import

from pd_book_tools.geometry.point import Point
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

    Internally represented with two corner points (top-left & bottom-right).
    Shapely is leveraged for certain spatial combinations (intersection/union),
    but core scalar properties (area, overlaps, splits) use inexpensive arithmetic.
    """

    top_left: Point
    bottom_right: Point
    is_normalized: bool | None = None  # explicit override; inferred when None

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
        """Area of the bounding box (width * height)."""
        return float(self.width * self.height)

    @property
    def center(self) -> Point:
        """Get center point of the box"""
        return Point(
            (self.top_left.x + self.bottom_right.x) / 2,
            (self.top_left.y + self.bottom_right.y) / 2,
        )

    @staticmethod
    def _split_at_x(
        box: "BoundingBox", x_value: float
    ) -> tuple["BoundingBox", "BoundingBox"]:
        """Internal helper to split at absolute x coordinate (may coincide with an edge)."""
        if x_value < box.minX or x_value > box.maxX:
            raise ValueError("split x is out of range for bounding box")
        left = BoundingBox._build(
            box.minX, box.minY, x_value, box.maxY, box.is_normalized
        )
        right = BoundingBox._build(
            x_value, box.minY, box.maxX, box.maxY, box.is_normalized
        )
        return left, right

    def split_x_offset(self, x_offset: float) -> Tuple["BoundingBox", "BoundingBox"]:
        """Split the bounding box into two boxes using the given x offset from left edge.

        Pure arithmetic implementation replaces earlier Shapely-based version
        (performance + determinism). Maintains previous semantics allowing
        zero-width side when offset is 0 or width.
        """
        if x_offset < 0 or x_offset > self.width:
            raise ValueError("x_offset is out of range for bounding box")
        x_abs = self.minX + x_offset
        return self._split_at_x(self, x_abs)

    def split_x_absolute(
        self, x_absolute: float
    ) -> Tuple["BoundingBox", "BoundingBox"]:
        """Split the bounding box into two boxes at absolute x coordinate.

        Arithmetic-only implementation (no Shapely).
        """
        return self._split_at_x(self, x_absolute)

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
        coords = [
            float(self.top_left.x),
            float(self.top_left.y),
            float(self.bottom_right.x),
            float(self.bottom_right.y),
        ]
        inferred = all(0 <= c <= 1 for c in coords)
        if self.is_normalized is None:
            self.is_normalized = inferred
        else:
            if self.is_normalized and not inferred:
                raise ValueError(
                    "Cannot mark bounding box as normalized: coordinates must lie within [0,1]"
                )
        # Rebuild points if their flags differ from box-level flag
        if (
            self.top_left.is_normalized != self.is_normalized
            or self.bottom_right.is_normalized != self.is_normalized
        ):
            self.top_left = Point(
                self.top_left.x, self.top_left.y, is_normalized=self.is_normalized
            )
            self.bottom_right = Point(
                self.bottom_right.x,
                self.bottom_right.y,
                is_normalized=self.is_normalized,
            )

    @classmethod
    def from_points(
        cls,
        points: Sequence[Union[dict, "Point", "ShapelyPoint", Sequence[float]]],
        is_normalized: bool | None = None,
    ):
        """Create from a sequence of two Point instances, Shapely points, dicts with "x" and "y" keys, or sequences of 2 floats"""
        if len(points) != 2:
            raise ValueError("Bounding box should have exactly 2 points")
        converted_points: list[Point] = []
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
            elif isinstance(p, Sequence) and len(p) == 2:  # type: ignore
                converted_points.append(Point(p[0], p[1]))  # type: ignore
            else:
                raise TypeError("Unsupported point specification in from_points")
        if not (
            converted_points[1].x > converted_points[0].x
            and converted_points[1].y > converted_points[0].y
        ):
            raise ValueError(
                "Second point should have larger x and y coordinates than the first point"
            )
        return cls._build(
            converted_points[0].x,
            converted_points[0].y,
            converted_points[1].x,
            converted_points[1].y,
            is_normalized,
        )

    @classmethod
    def from_float(cls, points: Sequence[float], is_normalized: bool | None = None):
        """Create from [x_min, y_min, x_max, y_max] format"""
        if len(points) != 4:
            raise ValueError(
                "Bounding box should have exactly 4 coordinates: x_min, y_min, x_max, y_max"
            )
        if points[0] > points[2] or points[1] > points[3]:
            raise ValueError(
                "Bounding box coordinates are not in correct order. x_min < x_max and y_min < y_max"
            )
        return cls._build(points[0], points[1], points[2], points[3], is_normalized)

    @classmethod
    def from_nested_float(
        cls, points: Sequence[Sequence[float]], is_normalized: bool | None = None
    ):
        """Create from [[x_min, y_min], [x_max, y_max]] format"""
        if len(points) != 2:
            raise ValueError("Bounding box should have exactly 2 points")
        if len(points[0]) != 2 or len(points[1]) != 2:
            raise ValueError("Each point should have exactly 2 coordinates: x, y")
        if points[0][0] > points[1][0] or points[0][1] > points[1][1]:
            raise ValueError(
                "Bounding box coordinates are not in correct order. x_min < x_max and y_min < y_max"
            )
        return cls._build(
            points[0][0], points[0][1], points[1][0], points[1][1], is_normalized
        )

    @classmethod
    def from_ltrb(
        cls,
        left: float,
        top: float,
        right: float,
        bottom: float,
        is_normalized: bool | None = None,
    ):
        """Create from left, top, right, bottom format"""
        return cls._build(left, top, right, bottom, is_normalized)

    @classmethod
    def from_ltwh(
        cls,
        left: float,
        top: float,
        width: float,
        height: float,
        is_normalized: bool | None = None,
    ):
        """Create from left, top, width, height format"""
        if width < 0 or height < 0:
            raise ValueError("Bounding box width and height must be non-negative")
        right = left + width
        bottom = top + height
        return cls._build(left, top, right, bottom, is_normalized)

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
        Return a new BoundingBox with normalized coordinates converted
        to absolute pixel coordinates.

        Requires this box to be normalized. Raises ValueError if the box
        is already in pixel space (``is_normalized`` is False).
        """
        if not self.is_normalized:
            raise ValueError(
                "scale() expected a normalized bounding box (values in [0,1]); this box is pixel coordinates"
            )
        return BoundingBox(
            top_left=self.top_left.scale(width, height),
            bottom_right=self.bottom_right.scale(width, height),
            is_normalized=False,
        )

    def normalize(self, width: int, height: int) -> "BoundingBox":
        """
        Return a new BoundingBox with absolute (pixel) coordinates converted
        to normalized coordinates in the unit square.

        Requires this box to be in pixel space. Raises ValueError if the box
        is already normalized.
        """
        if self.is_normalized:
            raise ValueError(
                "normalize() expected a pixel bounding box (non-normalized); this box is already normalized"
            )
        return BoundingBox(
            top_left=self.top_left.normalize(width, height),
            bottom_right=self.bottom_right.normalize(width, height),
            is_normalized=True,
        )

    def contains_point(self, point: Point) -> bool:
        """Check if the bounding box covers the given point (inclusive of edges)."""
        return self.as_shapely().covers(ShapelyPoint(point.x, point.y))  # type: ignore

    @staticmethod
    def _require_same_coords(fn):  # type: ignore
        def wrapper(self, other, *args, **kwargs):  # type: ignore
            if self.is_normalized != other.is_normalized:
                raise ValueError(
                    "Bounding boxes must share coordinate system (both normalized or both pixel)"
                )
            return fn(self, other, *args, **kwargs)  # type: ignore

        return wrapper

    @_require_same_coords
    def intersects(self, other: "BoundingBox") -> bool:  # type: ignore
        return self.as_shapely().intersects(other.as_shapely())  # type: ignore

    @_require_same_coords
    def intersection(self, other: "BoundingBox") -> Optional["BoundingBox"]:  # type: ignore
        inter = self.as_shapely().intersection(other.as_shapely())  # type: ignore
        if inter.is_empty:  # type: ignore
            return None
        minx, miny, maxx, maxy = inter.bounds  # type: ignore
        if minx == maxx or miny == maxy:
            return None
        is_norm = self.is_normalized and all(
            0 <= c <= 1 for c in (minx, miny, maxx, maxy)
        )
        return BoundingBox.from_ltrb(minx, miny, maxx, maxy, is_normalized=is_norm)

    @_require_same_coords  # type: ignore
    def overlap_y_amount(self, other: "BoundingBox"):
        """Return the amount of overlap on the y-axis (projection overlap)."""
        return self._interval_overlap(self.minY, self.maxY, other.minY, other.maxY)

    @_require_same_coords  # type: ignore
    def overlap_x_amount(self, other: "BoundingBox"):
        """Return the amount of overlap on the x-axis (projection overlap)."""
        return self._interval_overlap(self.minX, self.maxX, other.minX, other.maxX)

    @classmethod
    def union(cls, bounding_boxes: Sequence["BoundingBox"]) -> "BoundingBox":
        """Return the minimal box covering all provided boxes.

        When shapely is available we leverage unary_union to support future
        extension (e.g., rotated boxes). For current axis-aligned rectangles
        this reduces to bounds of all boxes.
        """
        if not bounding_boxes:
            raise ValueError("Bounding box list is empty")
        first_norm = bounding_boxes[0].is_normalized
        if any(b.is_normalized != first_norm for b in bounding_boxes[1:]):
            raise ValueError(
                "All bounding boxes must share coordinate system (all normalized or all pixel) for union"
            )
        geom = unary_union([b.as_shapely() for b in bounding_boxes])  # type: ignore
        minx, miny, maxx, maxy = geom.bounds  # type: ignore
        coords = [minx, miny, maxx, maxy]
        # Normalized only if all source boxes are normalized AND bounds lie in [0,1]
        is_norm = all(
            b.top_left.is_normalized and b.bottom_right.is_normalized
            for b in bounding_boxes
        ) and all(0 <= c <= 1 for c in coords)
        return cls(
            Point(minx, miny, is_normalized=is_norm),
            Point(maxx, maxy, is_normalized=is_norm),
            is_normalized=is_norm,
        )

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary.

        Includes each corner point's normalization state (``is_normalized``) so
        consumers can distinguish whether the coordinates are unit-normalized
        (in [0,1]) or absolute pixel values. Older serialized forms omitted this
        flag; :meth:`from_dict` remains backward compatible and will infer the
        state when the flag is absent.
        """
        tl = {
            "x": self.top_left.x,
            "y": self.top_left.y,
            "is_normalized": self.top_left.is_normalized,
        }
        br = {
            "x": self.bottom_right.x,
            "y": self.bottom_right.y,
            "is_normalized": self.bottom_right.is_normalized,
        }
        return {"top_left": tl, "bottom_right": br, "is_normalized": self.is_normalized}

    @classmethod
    def from_dict(cls, dict: Dict) -> "BoundingBox":
        """Create BoundingBox from dictionary"""
        tl = dict["top_left"]
        br = dict["bottom_right"]
        box_norm = dict.get("is_normalized")
        return BoundingBox(
            top_left=Point(tl["x"], tl["y"], is_normalized=tl.get("is_normalized")),
            bottom_right=Point(br["x"], br["y"], is_normalized=br.get("is_normalized")),
            is_normalized=box_norm,
        )

    def _extract_roi(self, image: ndarray):
        """Internal: return (roi, x1,y1,x2,y2, img_w,img_h, original_is_normalized).
        Scales to pixel space if normalized.
        """
        img_h, img_w = image.shape[:2]
        original_is_normalized = bool(self.is_normalized)
        box = self.scale(img_w, img_h) if original_is_normalized else self
        x1, y1, x2, y2 = box.to_ltrb()
        roi = image[y1:y2, x1:x2]
        return roi, x1, y1, x2, y2, img_w, img_h, original_is_normalized

    @staticmethod
    def _tight_bbox_from_thresh(thresh: ndarray):
        non_zero = findNonZero(thresh)
        if non_zero is None:
            return None
        x, y, w, h = cv2.boundingRect(non_zero)
        return x, y, w, h

    def _finalize_pixel_bbox(
        self,
        x_min: float,
        y_min: float,
        x_max: float,
        y_max: float,
        img_w: int,
        img_h: int,
        original_is_normalized: bool,
    ) -> "BoundingBox":
        bbox = BoundingBox.from_ltrb(x_min, y_min, x_max, y_max)
        if original_is_normalized:
            # round before renormalizing (existing behavior)
            bbox = BoundingBox.from_ltrb(
                int(round(x_min)),
                int(round(y_min)),
                int(round(x_max)),
                int(round(y_max)),
            ).normalize(img_w, img_h)
        return bbox

    def refine(
        self,
        image: ndarray,
        padding_px: int = 0,
        expand_beyond_original: bool = False,
    ) -> "BoundingBox":
        roi, x1, y1, x2, y2, img_w, img_h, original_is_normalized = self._extract_roi(
            image
        )
        orig_x1, orig_y1, orig_x2, orig_y2 = x1, y1, x2, y2
        thresh, _ = self._threshold_inverted(roi)
        tight = self._tight_bbox_from_thresh(thresh)
        if tight is None:
            return BoundingBox.from_dict(self.to_dict())
        x, y, w, h = tight
        x_min = x1 + x
        y_min = y1 + y
        x_max = x1 + x + w
        y_max = y1 + y + h
        tight_width = x_max - x_min
        tight_height = y_max - y_min
        if expand_beyond_original:
            slack_w = max(0.0, (orig_x2 - orig_x1) - tight_width)
            slack_h = max(0.0, (orig_y2 - orig_y1) - tight_height)
            extra_w = padding_px + slack_w / 2.0
            extra_h = padding_px + slack_h / 2.0
            x_min = max(0.0, x_min - extra_w)
            y_min = max(0.0, y_min - extra_h)
            x_max = min(float(img_w), x_max + extra_w)
            y_max = min(float(img_h), y_max + extra_h)
        else:
            x_min = max(orig_x1, max(0.0, x_min - padding_px))
            y_min = max(orig_y1, max(0.0, y_min - padding_px))
            x_max = min(orig_x2, min(float(img_w), x_max + padding_px))
            y_max = min(orig_y2, min(float(img_h), y_max + padding_px))
        return self._finalize_pixel_bbox(
            x_min, y_min, x_max, y_max, img_w, img_h, original_is_normalized
        )

    def _vertical_crop(self, image: ndarray, keep: str) -> "BoundingBox":
        """Shared implementation for crop_top (keep='bottom') and crop_bottom (keep='top')."""
        roi, x1, y1, x2, y2, img_w, img_h, _ = self._extract_roi(image)
        thresh, _ = self._threshold_inverted(roi)
        non_zero = findNonZero(thresh)
        if non_zero is None:
            return BoundingBox.from_dict(self.to_dict())
        coords = non_zero.reshape(-1, 2)
        roi_h, _ = thresh.shape
        center_y = roi_h // 2
        if keep == "top":
            # discard below center
            coords = coords[coords[:, 1] <= center_y]
            if coords.size == 0:
                return BoundingBox.from_dict(self.to_dict())
            for y in range(center_y - 1, -1, -1):
                current = set(coords[coords[:, 1] == y][:, 0])
                prev = set(coords[coords[:, 1] == y + 1][:, 0])
                if not prev and current:
                    continue
                if current & prev:
                    continue
                y1 = y1 + y
                break
        else:  # keep == bottom
            coords = coords[coords[:, 1] >= center_y]
            if coords.size == 0:
                return BoundingBox.from_dict(self.to_dict())
            roi_h = thresh.shape[0]
            for y in range(center_y + 1, roi_h):
                current = set(coords[coords[:, 1] == y][:, 0])
                prev = set(coords[coords[:, 1] == y - 1][:, 0])
                if not prev and current:
                    continue
                if current & prev:
                    continue
                y2 = y1 + (y - 0)  # adjust y2 based on offset
                break
        bbox = BoundingBox.from_ltrb(x1, y1, x2, y2).normalize(img_w, img_h)
        return bbox

    def crop_bottom(self, image: ndarray) -> "BoundingBox":
        return self._vertical_crop(image, keep="bottom")

    def crop_top(self, image: ndarray) -> "BoundingBox":
        return self._vertical_crop(image, keep="top")

    def clamp_to_image(self, width: int, height: int) -> "BoundingBox":
        """Return new box clamped to [0,width]x[0,height] in pixel or [0,1] if normalized.

        If normalized, simply clamps to [0,1].
        """
        if self.is_normalized:
            return BoundingBox.from_ltrb(
                max(0.0, min(1.0, self.minX)),
                max(0.0, min(1.0, self.minY)),
                max(0.0, min(1.0, self.maxX)),
                max(0.0, min(1.0, self.maxY)),
                is_normalized=True,
            )
        return BoundingBox.from_ltrb(
            max(0.0, min(width, self.minX)),
            max(0.0, min(height, self.minY)),
            max(0.0, min(width, self.maxX)),
            max(0.0, min(height, self.maxY)),
            is_normalized=False,
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
        try:
            minx, miny, maxx, maxy = shapely_box.bounds
            coords = [minx, miny, maxx, maxy]
            is_norm = all(0 <= c <= 1 for c in coords)
            return cls(
                Point(minx, miny, is_normalized=is_norm),
                Point(maxx, maxy, is_normalized=is_norm),
                is_normalized=is_norm,
            )
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

    @_require_same_coords
    def iou(self, other: "BoundingBox") -> float:  # type: ignore
        a = self.as_shapely()
        b = other.as_shapely()
        inter = a.intersection(b)  # type: ignore
        if inter.is_empty:  # type: ignore
            return 0.0
        union_area = a.union(b).area  # type: ignore
        if union_area == 0:
            return 0.0
        return float(inter.area / union_area)  # type: ignore

    def expand(self, dx: float = 0.0, dy: float = 0.0) -> "BoundingBox":
        """Expand (or shrink) the box by dx, dy on each side.

        Uniform case (dx == dy) uses Shapely buffer with square corners.
        Anisotropic case computes new rectangle about the center.
        Negative deltas shrink; resulting dimensions must remain non-negative.
        """
        if dx == dy:
            if dx == 0:
                return BoundingBox.from_ltrb(
                    self.minX,
                    self.minY,
                    self.maxX,
                    self.maxY,
                    is_normalized=self.is_normalized,
                )
            g = self.as_shapely().buffer(dx, join_style=2)  # type: ignore
            minx, miny, maxx, maxy = g.bounds  # type: ignore
            return BoundingBox.from_ltrb(
                minx, miny, maxx, maxy, is_normalized=self.is_normalized
            )
        cx = (self.minX + self.maxX) / 2.0
        cy = (self.minY + self.maxY) / 2.0
        half_w = (self.width / 2.0) + dx
        half_h = (self.height / 2.0) + dy
        if half_w < 0 or half_h < 0:
            raise ValueError("Expansion deltas collapse box to negative size")
        minx = cx - half_w
        maxx = cx + half_w
        miny = cy - half_h
        maxy = cy + half_h
        return BoundingBox.from_ltrb(
            minx, miny, maxx, maxy, is_normalized=self.is_normalized
        )

    @staticmethod
    def _build(
        left: float, top: float, right: float, bottom: float, is_normalized: bool | None
    ):
        """Internal helper to construct a BoundingBox with shared validation & normalization inference.

        Mirrors the previous logic in individual factory constructors so behavior remains unchanged.
        """
        if left > right or top > bottom:
            raise ValueError(
                "Bounding box coordinates are not in correct order. left < right and top < bottom"
            )
        vals = [left, top, right, bottom]
        inferred = all(0 <= v <= 1 for v in vals)
        norm = inferred if is_normalized is None else is_normalized
        return BoundingBox(
            Point(left, top, is_normalized=norm),
            Point(right, bottom, is_normalized=norm),
            is_normalized=norm,
        )

    @staticmethod
    def _interval_overlap(a0: float, a1: float, b0: float, b1: float) -> float:
        """Return 1D interval overlap length (>=0)."""
        return max(0.0, min(a1, b1) - max(a0, b0))

    @staticmethod
    def _threshold_inverted(roi: ndarray) -> tuple[ndarray, ndarray]:
        """Convert ROI to grayscale (if needed), invert, OTSU threshold.

        Returns (thresh, grayscale_roi). Extracted to reduce duplication across
        refine/crop/expand_to_content routines.
        """
        if len(roi.shape) == 3:
            roi_gray = cvtColor(roi, COLOR_BGR2GRAY)
        else:
            roi_gray = roi
        inverted = cv2.bitwise_not(roi_gray)
        _, thresh = threshold(inverted, 0, 255, THRESH_BINARY + THRESH_OTSU)
        return thresh, roi_gray

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, s: str) -> "BoundingBox":
        import json

        return cls.from_dict(json.loads(s))
