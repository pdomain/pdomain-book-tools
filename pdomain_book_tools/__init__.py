"""pdomain-book-tools: tools for working with public domain book scans.

Public API
----------

The top-level package re-exports the canonical types most consumers
need. These names are the supported public API; submodule paths
(e.g. ``pdomain_book_tools.ocr.page``) are not part of the supported API
and may relocate in future versions. See ``docs/usage/public-api.md``.

Most of these re-exports are pure-Python value types that now live in
``pdomain-book-contracts``: ``BoundingBox``, ``Point``, ``RegionType``,
``PGDPExport``, ``PGDPResults``, ``TypographyCorrection``,
``TypographyTaxonomy``, and ``WordTypography``. Importing
``pdomain_book_tools`` or any of those names costs no more than
``pdomain-book-contracts`` itself — consumers who want the contracts
without the OCR imaging stack can depend on that package directly instead.
(``BoundingBox`` and ``Point`` do pull in ``numpy``, as a transitive import
of shapely rather than of this package; ``pdomain-book-contracts`` treats
that as a declared exception, not a defect — see its own
``tests/test_torch_free_import.py``.)

``Block``, ``BlockCategory``, ``Page``, and ``Word`` still reach cv2
directly, so they are resolved lazily through a module-level
``__getattr__``: ``from pdomain_book_tools import Page`` and
``pdomain_book_tools.Page`` both work, but cv2 loads only on first access
to one of these four names, not on package import.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# Version is generated at build time by hatch-vcs into _version.py.
# In an editable / source-tree checkout where _version.py hasn't been
# generated yet, fall back to importlib.metadata (works once installed).
try:
    from pdomain_book_tools._version import __version__, version
except ImportError:  # pragma: no cover - fallback for unbuilt source trees
    try:
        from importlib.metadata import PackageNotFoundError
        from importlib.metadata import version as _pkg_version

        try:
            __version__ = _pkg_version("pdomain-book-tools")
        except PackageNotFoundError:
            __version__ = "0.0.0+unknown"
    except ImportError:
        __version__ = "0.0.0+unknown"
    version = __version__

# Public API re-exports. See docs/usage/public-api.md.
#
# ``RegionType`` is sourced straight from ``pdomain_book_contracts`` rather
# than through ``pdomain_book_tools.layout.types`` (which re-exports the
# same object). Importing a submodule requires initialising its parent
# package first, and ``pdomain_book_tools.layout``'s own ``__init__.py``
# eagerly imports the cv2-based layout detectors for unrelated reasons —
# going through it here would tax this light re-export with the imaging
# stack it does not need.
from pdomain_book_contracts.layout.types import RegionType

from pdomain_book_tools.geometry.bounding_box import BoundingBox
from pdomain_book_tools.geometry.point import Point
from pdomain_book_tools.pgdp.pgdp_results import PGDPExport, PGDPResults
from pdomain_book_tools.typography.review import (
    TypographyCorrection,
    TypographyTaxonomy,
    WordTypography,
)

if TYPE_CHECKING:
    # Deferred at runtime (see __getattr__ below) because these pull in
    # cv2; kept here so static analysis and IDE completion still see them.
    from pdomain_book_tools.ocr.block import Block, BlockCategory
    from pdomain_book_tools.ocr.page import Page
    from pdomain_book_tools.ocr.word import Word

__all__ = [
    "Block",
    "BlockCategory",
    "BoundingBox",
    "PGDPExport",
    "PGDPResults",
    "Page",
    "Point",
    "RegionType",
    "TypographyCorrection",
    "TypographyTaxonomy",
    "Word",
    "WordTypography",
    "__version__",
    "version",
]


def __getattr__(name: str) -> object:
    """Lazily resolve names that reach cv2.

    ``Block``, ``BlockCategory``, ``Page``, and ``Word`` import
    ``pdomain_book_tools.ocr.block`` / ``.page`` / ``.word``. ``Page`` and
    ``Word`` import cv2 directly; ``Block``/``BlockCategory`` import
    ``Word`` at module level and so reach cv2 the same way. Resolving them
    here on first access keeps ``import pdomain_book_tools`` — and
    importing any of the pure-Python contracts above — free of cv2.
    """
    if name in ("Block", "BlockCategory"):
        from pdomain_book_tools.ocr.block import Block, BlockCategory

        return Block if name == "Block" else BlockCategory
    if name == "Page":
        from pdomain_book_tools.ocr.page import Page

        return Page
    if name == "Word":
        from pdomain_book_tools.ocr.word import Word

        return Word
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
