---
Status: active
Owner: CT
Created: 2026-06-02
Last verified: 2026-07-13
Kind: usage
---

# Correct Page Geometry with Deskew and Dewarp

> **Design history:** preserved in Git history.

The `pdomain_book_tools.geometry_correction` package corrects page geometry with
swappable backends. Its `Deskew`, `Dewarp`, `PageSideDetector`, and
`CurvatureDetector` protocols return a composable `GeometryTransform`. Use the
thin `GeometryPipeline` helper to control their order, or build your own
sequence.

## Run the default correction pipeline

```python
import cv2
from pdomain_book_tools.geometry_correction.defaults import default_pipeline

img = cv2.imread("page.tif", cv2.IMREAD_GRAYSCALE)
result = default_pipeline().run(img)
corrected = result.image
```

`default_pipeline()` runs these steps in order:

1. `GutterShadowPageSide` — detect the binding edge from a dark shadow band.
2. `ImageBasedCurvature` — gate: is the page flat enough for deskew-only?
3. `ProjectionDeskew` — rotate to align text rows.

UVDoc dewarp is opt-in; see below.

## Type against backend protocols

Every backend implements one of four protocols. Downstream code should use the
protocol as its type, not the concrete class.

| Protocol | Key method | What it returns |
|---|---|---|
| `Deskew` | `estimate(image, ...)` | `DeskewResult` (angle, transform) |
| `Dewarp` | `estimate(image, ...)` | `DewarpResult` (grid transform) |
| `PageSideDetector` | `detect(image, ...)` | `PageSideResult` (LEFT/RIGHT/SINGLE, gutter edge) |
| `CurvatureDetector` | `score(image, ...)` | `CurvatureReport` (flatness, "none"/"deskew_only"/"dewarp") |

## Choose a built-in backend

| Kind | Name | Notes |
|---|---|---|
| deskew | `projection` | Projection-profile variance (Postl). Default. |
| deskew | `sbrunner` | Hough-transform via `deskew` PyPI package. |
| curvature | `image_based` | Text-row bow measurement. Gate for dewarp. |
| page_side | `supplied` | Trust a caller-supplied LEFT/RIGHT hint. |
| page_side | `gutter_shadow` | Dark binding-shadow detection. Default. |
| dewarp | `uvdoc` | UVDoc ONNX backward-map. Requires extra + model. |

## Use UVDoc dewarp (`[dewarp-dl]` extra)

Install the extra:

```sh
pip install 'pdomain-book-tools[dewarp-dl]'
```

Use `make_onnx.py` from
[FahNos/UVDoc_onnx](https://github.com/FahNos/UVDoc_onnx) to obtain the ONNX
model. Then set its path:

```sh
export PD_UVDOC_ONNX=/path/to/uvdoc.onnx
```

Enable it in the pipeline:

```python
result = default_pipeline(with_dewarp=True).run(img)
```

> **License note:** Verify the UVDoc model weight license before hosting or
> redistributing alongside our Unlicense code.

## Pass a page-side hint from an upstream split

Pass a hint when your upstream split stage knows which page of the spread this
is:

```python
from pdomain_book_tools.geometry_correction import PageSide

result = default_pipeline().run(img, page_side_hint=PageSide.LEFT)
```

The pipeline's `SuppliedPageSide` backend uses the hint directly. For a left
page, it gives `gutter_edge="right"` because the binding is on the right of a
left-hand page.

## Register and use custom backends

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

## Apply a `GeometryTransform`

Every backend returns an identity, affine, grid, or rectified
`GeometryTransform`.

```python
transform = result.deskew.transform
corrected = transform.apply(img)          # apply to image
pts_out = transform.map_points(pts)       # propagate keypoints
inv = transform.invert()                  # invert (affine only)
```

Grid transforms with `kind="grid"` are non-invertible because they come from
dense backward-map dewarpers. Affine transforms invert exactly.

## Dewarp scanned pages with textline disparity

> **Design history:** preserved in Git history.

`TextlineDisparityDewarp` is a clean-room reimplementation of Leptonica's
textline-disparity model. It consolidates text lines with morphology and fits
order-2 baselines for vertical disparity. It can also straighten the reference
margin for horizontal disparity while accounting for even and odd pages. It
requires no neural-network weights.

### Route flat, curled, and oblique pages

`RegimeDetector` uses two signals to classify a page:

- **baseline_sag** — the mean `|c2|` of detected baselines, scaled to a
  dimensionless page sag. Flat pages have sag near 0. Curl pages have sag ≥ 0.04
  by default.
- **edge_convergence** — the angle between the left and right content edges.
  Oblique photos show convergence ≥ 0.10 rad by default.

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

### Set `gutter_edge` for even and odd pages

- **Verso (LEFT page, gutter on right):** reference the LEFT line-ends; target =
  minimum left end across lines.
- **Recto (RIGHT page, gutter on left):** reference the RIGHT line-ends; target =
  maximum right end across lines.

Pass `gutter_edge="right"` for verso and `"left"` for recto. The
`GutterShadowPageSide` backend sets `gutter_edge` automatically from the
detected binding side.

### Fall back when a page has too few text lines

When fewer than `min_textlines=15` text lines survive the short-line cull,
`TextlineDisparityDewarp.estimate()` returns an identity transform with
`confidence=0.0`. This threshold is Leptonica's `DefaultMinLines`. The regime
gate or caller can then defer to UVDoc or skip dewarp entirely.

### GPU acceleration (`[gpu]` extra)

Pass `prefer_gpu=True` to use the CuPy mirror for morphology and the dense resample:

```python
TextlineDisparityDewarp(prefer_gpu=True)
```

CuPy is the `[gpu]` optional extra. On CPU-only installs, the flag is silently
ignored and the NumPy path is used.
