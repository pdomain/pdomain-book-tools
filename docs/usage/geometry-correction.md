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
