# Public API

This page lists the **supported public API** of `pdomain-book-tools`.
Submodule paths (e.g. `pdomain_book_tools.ocr.page`) are not part of the
supported API and may relocate in future versions — import the names
below from the documented entry points.

## Top-level package — `pdomain_book_tools`

```python
from pdomain_book_tools import (
    BoundingBox,
    Point,
    Page,
    Block,
    BlockCategory,
    Word,
    RegionType,
    PGDPResults,
    PGDPExport,
)
```

Importing the top-level package eagerly imports the OCR / layout /
geometry stack (`cv2`, `numpy`, DocTR, transformers). If you need a
lighter import surface, import the specific subpackage below.

## Geometry — `pdomain_book_tools.geometry`

```python
from pdomain_book_tools.geometry import BoundingBox, Point
```

Note: `BoundingBox` exposes image-processing helper methods
(`refine`, `crop_top`, `crop_bottom`) for backward compatibility.
Their canonical implementation lives in
`pdomain_book_tools.geometry.image_ops` — call those free functions
directly in new code.

## OCR data model — `pdomain_book_tools.ocr.*`

The OCR submodule layout is intentionally not pinned as public API
beyond the re-exports above. New code should prefer the top-level
imports.

Image-processing helpers for `Word` and `Block` live as free
functions in `pdomain_book_tools.ocr.image_utilities` (e.g.
`refine_word_bbox(word, image)`); the corresponding methods on
`Word` / `Block` are thin wrappers preserved for backward
compatibility.

## Layout — `pdomain_book_tools.layout`

```python
from pdomain_book_tools.layout import (
    RegionType,
    LayoutRegion,
    PageLayout,
    LayoutDetector,
    ContourDetector,
    NullDetector,
    get_detector,
    clear_detector_cache,
    draw_layout_overlay,
    iou,
    contains,
    horizontal_overlap_ratio,
    caption_for_figure,
    region_reading_order,
)
```

## PGDP — `pdomain_book_tools.pgdp`

```python
from pdomain_book_tools.pgdp import PGDPResults, PGDPExport
```

## Utility — `pdomain_book_tools.utility`

```python
from pdomain_book_tools.utility import timing, ipynb_widgets
```

## Stability

Re-exports listed here are part of the supported API. Removal or
relocation is a deliberate breaking change and will be called out in
the release notes. Internal submodule paths (anything not listed
here) are subject to change without notice.
