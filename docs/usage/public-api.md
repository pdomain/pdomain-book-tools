---
Status: active
Owner: CT
Created: 2026-05-07
Last verified: 2026-11-07
Kind: usage
---

# Public API

This page lists the **supported public API** of `pdomain-book-tools`.
Every import path shown on this page is supported, including the deeper paths
that `README.md` teaches, such as `pdomain_book_tools.ocr.document`. Any path
not shown here, such as `pdomain_book_tools.ocr.page`, is internal and may move
without notice. For `Page`, `Block`, `Word`, and `BlockCategory`, prefer the
top-level import.

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
    TypographyCorrection,
    TypographyTaxonomy,
    WordTypography,
)
```

`BoundingBox`, `Point`, `RegionType`, `PGDPResults`, `PGDPExport`,
`TypographyCorrection`, `TypographyTaxonomy`, and `WordTypography` are
pure-Python contracts that now live in `pdomain-book-contracts`; importing
the top-level package or any of these five names costs no more than that
package. (`BoundingBox` and `Point` pull in `numpy` as shapely's own
transitive dependency, not this package's — `pdomain-book-contracts`
documents that as a declared exception, not a defect.) `Page`, `Block`,
`BlockCategory`, and `Word` still reach cv2 directly and are resolved
lazily on first access through the package's `__getattr__` — importing
`pdomain_book_tools` does not by itself load cv2. Consumers who want the
pure-Python contracts without cv2 can depend on `pdomain-book-contracts`
directly.

## Geometry — `pdomain_book_tools.geometry`

```python
from pdomain_book_tools.geometry import BoundingBox, Point
```

`BoundingBox` exposes the image-processing helper methods `refine`, `crop_top`,
and `crop_bottom` for backward compatibility. Their canonical implementation
lives in `pdomain_book_tools.geometry.image_ops`. Call those free functions
directly in new code.

## OCR a page — `pdomain_book_tools.ocr.document`

```python
from pdomain_book_tools.ocr.document import Document

doc, rotation_degrees = Document.from_image_ocr_via_doctr("page.png")
```

`Document.from_image_ocr_via_doctr` runs DocTR on one image. It returns the
`Document` and the rotation in degrees that it chose. See the README and
[page orientation](../architecture/ocr-page-orientation.md) for the options.

## OCR data model — `pdomain_book_tools.ocr`

```python
from pdomain_book_tools.ocr import (
    BlobStoreProtocol,
    GtOrphans,
    TypographyAnnotations,
    apply_text_normalizations,
    normalize_curly_quotes,
    normalize_em_dash,
)
from pdomain_book_tools.ocr.word import Word  # as taught in README.md
```

`Page`, `Block`, `BlockCategory`, and `Word` are supported from the top-level
package. The README also teaches `pdomain_book_tools.ocr.word.Word`, so that
path is supported too. Other OCR submodules are not part of the API.

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

## Geometry correction — `pdomain_book_tools.geometry_correction`

```python
from pdomain_book_tools.geometry_correction import (
    GeometryTransform,
    PageSide,
    TextlineDisparityDewarp,
)
from pdomain_book_tools.geometry_correction.defaults import (
    default_pipeline,
    scanned_pipeline,
)
from pdomain_book_tools.geometry_correction.pipeline import GeometryPipeline
from pdomain_book_tools.geometry_correction.registry import (
    get_deskew,
    register_deskew,
)
```

The package `__all__` lists the protocols, result types, detectors, and regime
helpers. The `defaults`, `pipeline`, and `registry` paths above are supported
as well. See [geometry correction](geometry-correction.md) for usage.

## Hugging Face model helpers — `pdomain_book_tools.hf`

```python
from pdomain_book_tools.hf import (
    hf_download,
    prefetch_layout_files,
    resolve_layout_source,
    resolve_ocr_models,
    short_revision,
    silence_transformers_load_chatter,
    suppress_hf_unauth_warning,
)
```

The package `__all__` also lists the constants `DEFAULT_DET_FILENAME`,
`DEFAULT_HF_REPO`, `DEFAULT_RECO_FILENAME`, `LAYOUT_MODEL_FILES`, and
`OCR_MODEL_SIDECARS`. Import all of these from `pdomain_book_tools.hf`, not
from its `download` or `models` submodules.

## JSON Schema emission — `pdomain_book_tools.schemas.emit`

```sh
uv run python -m pdomain_book_tools.schemas.emit > schemas.json
```

```python
from pdomain_book_tools.schemas.emit import (
    PUBLIC_MODELS,
    emit_schema_manifest,
    emit_schemas,
)
```

`PUBLIC_MODELS` is the set of models that the schema output covers.

## Typography and matching

`pdomain_book_tools.typography` and `pdomain_book_tools.matching` define an
`__all__` and are public packages. Import from the package, not its submodules.
This page does not list their names. Read each package's `__all__`.

## Utility — `pdomain_book_tools.utility`

```python
from pdomain_book_tools.utility import timing, ipynb_widgets
```

## Stability

The imports listed here are part of the supported API. Removing or moving
one is a deliberate breaking change that will be called out in the release
notes. Internal submodule paths, meaning anything not listed here, may change
without notice. These guarantees cover this package only. They do not claim
stability for any other `pdomain-*` project.

`tests/test_public_api.py` pins this page. It checks the top-level, geometry,
pgdp, utility, `ocr`, `layout`, `hf`, and `geometry_correction` names, the
supported deeper paths, and that the README imports only paths listed here.
`tests/test_schemas_emit.py` covers `schemas.emit`.
