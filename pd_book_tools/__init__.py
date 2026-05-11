"""pd-book-tools: tools for working with public domain book scans.

Public API
----------

The top-level package re-exports the canonical types most consumers
need. These names are the supported public API; submodule paths
(e.g. ``pd_book_tools.ocr.page``) are not part of the supported API
and may relocate in future versions. See ``docs/public-api.md``.

Importing this package eagerly imports the OCR / layout / geometry
stack (``cv2``, ``numpy``, DocTR, transformers). If you need a
lightweight import surface for a tool that only touches geometry,
import the specific submodule directly (``from pd_book_tools.geometry
import BoundingBox``) — but be aware that even that path imports
``cv2`` today.
"""

# Version is generated at build time by hatch-vcs into _version.py.
# In an editable / source-tree checkout where _version.py hasn't been
# generated yet, fall back to importlib.metadata (works once installed).
try:
    from pd_book_tools._version import __version__, version
except ImportError:  # pragma: no cover - fallback for unbuilt source trees
    try:
        from importlib.metadata import PackageNotFoundError
        from importlib.metadata import version as _pkg_version

        try:
            __version__ = _pkg_version("pd-book-tools")
        except PackageNotFoundError:
            __version__ = "0.0.0+unknown"
    except ImportError:
        __version__ = "0.0.0+unknown"
    version = __version__

# Public API re-exports. See docs/public-api.md.
from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.geometry.point import Point
from pd_book_tools.layout.types import RegionType
from pd_book_tools.ocr.block import Block, BlockCategory
from pd_book_tools.ocr.page import Page
from pd_book_tools.ocr.word import Word
from pd_book_tools.pgdp.pgdp_results import PGDPExport, PGDPResults

__all__ = [
    "Block",
    "BlockCategory",
    "BoundingBox",
    "PGDPExport",
    "PGDPResults",
    "Page",
    "Point",
    "RegionType",
    "Word",
    "__version__",
    "version",
]
