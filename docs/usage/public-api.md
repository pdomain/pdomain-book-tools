---
Status: active
Owner: CT
Created: 2026-05-07
Last verified: 2026-07-13
Kind: usage
---

# Public API

This page lists the **supported public API** of `pdomain-book-tools`.
Import the names below from the documented entry points. Submodule paths,
such as `pdomain_book_tools.ocr.page`, are not part of the supported API and
may move in future versions.

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

Importing the top-level package eagerly imports the OCR, layout, and geometry
stack: `cv2`, `numpy`, DocTR, and transformers. For a lighter import surface,
import the specific subpackage below.

## Geometry — `pdomain_book_tools.geometry`

```python
from pdomain_book_tools.geometry import BoundingBox, Point
```

`BoundingBox` exposes the image-processing helper methods `refine`, `crop_top`,
and `crop_bottom` for backward compatibility. Their canonical implementation
lives in `pdomain_book_tools.geometry.image_ops`. Call those free functions
directly in new code.

## OCR data model — `pdomain_book_tools.ocr.*`

Only the re-exports above are pinned as public API. The OCR submodule layout is
intentionally not pinned. Prefer top-level imports in new code.

Image-processing helpers for `Word` and `Block` are free functions in
`pdomain_book_tools.ocr.image_utilities`, such as
`refine_word_bbox(word, image)`. The corresponding methods on `Word` and
`Block` are thin wrappers preserved for backward compatibility.

## Layout — `pdomain_book_tools.layout`

```python
from pdomain_book_tools.layout import (
    RegionType,
    LayoutRegion,
    LayoutRegionDict,
    PageLayout,
    PageLayoutDict,
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
    auto_detect_illustrations_from_array,
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

The re-exports listed here are part of the supported API. Removing or moving
one is a deliberate breaking change that will be called out in the release
notes. Internal submodule paths, meaning anything not listed here, may change
without notice.
