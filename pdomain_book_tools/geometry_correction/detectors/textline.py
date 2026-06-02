"""TextlineDetector seam + the default Leptonica-faithful morph-centroid detector.

The seam leaves structural room for future StripProjectionDetector /
MLBaselineDetector drop-ins (YAGNI: not built now). The default delegates to the
device-parallel cv2 / cupy ``textline_dewarp.detect_textlines``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from pdomain_book_tools.image_processing.cv2_processing import (
    textline_dewarp as _cv2_td,
)

if TYPE_CHECKING:
    from pdomain_book_tools.image_processing.textline_types import LineSamples


@runtime_checkable
class TextlineDetector(Protocol):
    """Protocol for textline detector backends (runtime-checkable)."""

    name: str

    def detect(self, binary: Any, *, page_width: int) -> list[LineSamples]:
        """Detect text lines and return per-column vertical centroids."""
        ...


class MorphCentroidDetector:
    """Default detector: morph-consolidate -> per-column centroid (Leptonica-faithful).

    ``prefer_gpu`` selects the CuPy module when CuPy is importable; otherwise the
    NumPy path is used. The module is resolved lazily so a CPU-only install never
    imports cupy.
    """

    name = "morph_centroid"

    def __init__(self, *, prefer_gpu: bool = False) -> None:
        """Initialise the detector, optionally preferring the GPU path."""
        self.prefer_gpu = prefer_gpu

    def _module(self) -> Any:
        """Return the appropriate textline_dewarp module (cv2 or cupy)."""
        if self.prefer_gpu:
            from pdomain_book_tools.image_processing.cupy_processing._cupy_compat import (
                cupy_available,
            )

            if cupy_available():
                import importlib

                return importlib.import_module(
                    "pdomain_book_tools.image_processing.cupy_processing.textline_dewarp"
                )
        return _cv2_td

    def detect(self, binary: Any, *, page_width: int) -> list[LineSamples]:
        """Detect text lines as per-column vertical centroids."""
        return self._module().detect_textlines(binary, page_width=page_width)  # type: ignore[no-any-return]
