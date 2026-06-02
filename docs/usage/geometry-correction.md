# Geometry Correction (Deskew / Dewarp)

> **Spec:** [`docs/specs/2026-06-02-geometry-correction-design.md`](../specs/2026-06-02-geometry-correction-design.md)

The `pdomain_book_tools.geometry_correction` package provides swappable
`Deskew`, `Dewarp`, `PageSideDetector`, and `CurvatureDetector` protocol
backends that return a composable `GeometryTransform`. Consumers orchestrate
ordering through a thin `GeometryPipeline` helper or build their own sequence.

## Quick start

```python
import cv2
from pdomain_book_tools.geometry_correction.defaults import default_pipeline

img = cv2.imread("page.tif", cv2.IMREAD_GRAYSCALE)
result = default_pipeline().run(img)
corrected = result.image
```

`default_pipeline()` runs:

1. `GutterShadowPageSide` — detect the binding edge from a dark shadow band.
2. `ImageBasedCurvature` — gate: is the page flat enough for deskew-only?
3. `ProjectionDeskew` — rotate to align text rows.

Dewarp (UVDoc) is opt-in; see below.

## Protocols

All backends satisfy one of the four protocols. Downstream code should type against
the protocol, not the concrete class.

| Protocol | Key method | What it returns |
|---|---|---|
| `Deskew` | `estimate(image, ...)` | `DeskewResult` (angle, transform) |
| `Dewarp` | `estimate(image, ...)` | `DewarpResult` (grid transform) |
| `PageSideDetector` | `detect(image, ...)` | `PageSideResult` (LEFT/RIGHT/SINGLE, gutter edge) |
| `CurvatureDetector` | `score(image, ...)` | `CurvatureReport` (flatness, "none"/"deskew_only"/"dewarp") |

## Built-in backends

| Kind | Name | Notes |
|---|---|---|
| deskew | `projection` | Projection-profile variance (Postl). Default. |
| deskew | `sbrunner` | Hough-transform via `deskew` PyPI package. |
| curvature | `image_based` | Text-row bow measurement. Gate for dewarp. |
| page_side | `supplied` | Trust a caller-supplied LEFT/RIGHT hint. |
| page_side | `gutter_shadow` | Dark binding-shadow detection. Default. |
| dewarp | `uvdoc` | UVDoc ONNX backward-map. Requires extra + model. |

## UVDoc dewarp (`[dewarp-dl]` extra)

Install the extra:

```sh
pip install 'pdomain-book-tools[dewarp-dl]'
```

Obtain the ONNX model via [FahNos/UVDoc_onnx](https://github.com/FahNos/UVDoc_onnx)
(`make_onnx.py`) and set the path:

```sh
export PD_UVDOC_ONNX=/path/to/uvdoc.onnx
```

Enable it in the pipeline:

```python
result = default_pipeline(with_dewarp=True).run(img)
```

> **License note:** Verify the UVDoc model weight license before hosting or
> redistributing alongside our Unlicense code.

## Page-side hint (split-upstream contract)

When your upstream split stage knows which page of the spread this is, pass it:

```python
from pdomain_book_tools.geometry_correction import PageSide

result = default_pipeline().run(img, page_side_hint=PageSide.LEFT)
```

The `SuppliedPageSide` backend in the pipeline will use the hint directly,
giving `gutter_edge="right"` for a left page (binding is on the right of a
left-hand page).

## Custom backends

Register and retrieve backends by name:

```python
from pdomain_book_tools.geometry_correction.registry import register_deskew, get_deskew

register_deskew("my_backend", MyDeskewClass)
deskew = get_deskew("my_backend")
```

Swap into the pipeline:

```python
from pdomain_book_tools.geometry_correction.pipeline import GeometryPipeline

pipe = GeometryPipeline(
    page_side=my_page_side,
    curvature=my_curvature,
    deskew=deskew,
)
result = pipe.run(img)
```

## `GeometryTransform`

All backends return a `GeometryTransform` (identity / affine / grid / rectified).

```python
transform = result.deskew.transform
corrected = transform.apply(img)          # apply to image
pts_out = transform.map_points(pts)       # propagate keypoints
inv = transform.invert()                  # invert (affine only)
```

Grid transforms (`kind="grid"`) are non-invertible — they come from dense
backward-map dewarpers. Affine transforms invert exactly.

## Textline-disparity dewarp (scanned-page workhorse)

> **Spec:** [`docs/specs/2026-06-02-textline-disparity-dewarp-design.md`](../specs/2026-06-02-textline-disparity-dewarp-design.md)

`TextlineDisparityDewarp` is a clean-room reimplementation of Leptonica's
textline-disparity model: morph-consolidate text lines, fit order-2 baselines
(vertical disparity), and optionally straighten the reference margin (horizontal
disparity, even/odd-aware). No neural-network weights required.

### Regime routing (flat / flat_curl / oblique)

`RegimeDetector` classifies a page by two signals:

- **baseline_sag** — mean `|c2|` of detected baselines, scaled to a
  dimensionless page-sag. Flat pages have sag near 0; curl pages have sag ≥ 0.04
  (default).
- **edge_convergence** — angle between the left/right content edges. Oblique
  photos show convergence ≥ 0.10 rad (default).

| Regime | Signal | Routed to |
|---|---|---|
| `flat` | low sag, low convergence | deskew only |
| `flat_curl` | high sag, low convergence | `textline_disparity` |
| `oblique` | high convergence | UVDoc (when available) |

Use `scanned_pipeline()` for the regime-aware default:

```python
from pdomain_book_tools.geometry_correction.defaults import scanned_pipeline

pipe = scanned_pipeline()
result = pipe.run(img, page_side_hint=PageSide.LEFT)
```

### Even/odd (gutter_edge) contract

- **Verso (LEFT page, gutter on right):** reference the LEFT line-ends; target =
  minimum left end across lines.
- **Recto (RIGHT page, gutter on left):** reference the RIGHT line-ends; target =
  maximum right end across lines.

Pass `gutter_edge="right"` for verso, `"left"` for recto. The `GutterShadowPageSide`
backend sets `gutter_edge` automatically from the detected binding side.

### Sparse-page fallback

When fewer than `min_textlines=15` (Leptonica `DefaultMinLines`) text lines survive
the short-line cull, `TextlineDisparityDewarp.estimate()` returns an identity
transform with `confidence=0.0`. The regime gate / caller can then defer to UVDoc
or skip dewarp entirely.

### GPU acceleration (`[gpu]` extra)

Pass `prefer_gpu=True` to use the CuPy mirror for morphology and the dense resample:

```python
TextlineDisparityDewarp(prefer_gpu=True)
```

CuPy is the `[gpu]` optional extra. On CPU-only installs the flag is silently
ignored and the NumPy path is used.
