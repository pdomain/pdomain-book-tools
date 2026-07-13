---
Status: implemented
Owner: CT
Created: 2026-05-04
Last verified: 2026-07-13
Kind: spec
---

# Page-Orientation Detection

> **Status**: Implemented
> **Last updated**: 2026-05-10
> **Spec-Issue**: pdomain/pdomain-book-tools#26

How `pdomain-book-tools` decides whether a page image needs to be rotated before
OCR, and what the resulting `Page` records about that decision.

The implementation lives in
`pdomain_book_tools/ocr/rotation.py`.
`Document.from_image_ocr_via_doctr` consumes it as the default code path
(opt out with `auto_rotate=False`).

## Why this exists

Real public-domain scans include sideways foldout plates, upside-down
covers, and 90°-rotated maps. The Peutinger map fixture
`tests/fixtures/layout_regression/inputs/rotated-peutinger-map.png`
is the canonical example: a full-page map printed sideways, with the page
number `42` running vertically up the gutter.

DocTR (and any downstream layout detector) assumes upright input. Fed a
sideways page, it doesn't error — it silently produces garbage: low
recognition confidence, corrupted layout boxes, and an
indistinguishable-from-a-broken-page result downstream. Detecting this at
the OCR boundary keeps the layout module, the reorganize pipeline, and
the labeler UI honest: they can trust that whatever pixels they see were
the orientation the OCR pass was confident about.

## Pipeline

```text
   image (BGR/RGB/grayscale numpy array)
        │
        ▼
   ┌───────────────────────────────────────────────┐
   │ 1. OCR upright (0°)                           │
   │    record mean per-word confidence            │
   └───────────────────────────────────────────────┘
        │
        ▼
   confidence ≥ threshold? ──── yes ──→ done; rotation_applied = 0
        │
        no
        ▼
   ┌───────────────────────────────────────────────┐
   │ 2. OCR at 90°, 180°, 270°                     │
   │    record mean per-word confidence each       │
   └───────────────────────────────────────────────┘
        │
        ▼
   pick rotation with highest mean confidence
   (ties keep the earliest rotation tried)
        │
        ▼
   rotation_applied = chosen
   page.cv2_numpy_page_image = rotate_image(image, chosen)
```

### Step 1 — Upright probe

`detect_best_rotation` always runs OCR at 0° first. For the overwhelming
majority of correctly-oriented pages this is the only pass that runs; the
3 fallback rotations are only tried when the upright pass fails the
threshold.

The fast path returns the original image array unchanged (`rotate_image`
returns its input by reference at 0°), so confident pages pay no extra
allocation.

### Step 2 — Fallback probes

Triggered when mean upright confidence is below
`DEFAULT_CONFIDENCE_THRESHOLD = 0.6`. The image is rotated 90°, 180°,
and 270° clockwise (in that order); each rotation is OCR'd and the run
with the highest mean per-word confidence wins.

Ties keep the earliest rotation tried, so the upright pass is preferred
when nothing strictly beats it. This matters for nearly-blank or
illustration-heavy pages where every rotation produces the same low
confidence — we don't want to flip a page just because three rotations
of noise compute the same mean.

### Step 3 — Frame convention

The chosen rotation is applied to the source image array, and the
*rotated* array becomes `page.cv2_numpy_page_image`. Every coordinate
the OCR returned (and any layout/reorganize result that follows) is
already in the rotated frame, so downstream consumers can use the bbox
coordinates directly to crop or annotate the image without an extra
inverse rotation.

The original orientation is **not** preserved. Callers that need the
original image keep their own copy; the OCR frame is the source of
truth from this point forward.

## Threshold rationale

`DEFAULT_CONFIDENCE_THRESHOLD = 0.6` is calibrated against the fixture
corpus:

| Fixture class | Typical mean conf at 0° | Notes |
|---|---|---|
| Body / chapter-head / front-matter pages | 0.75 – 0.95 | well above threshold; fast-pathed |
| Plate caption + rich figure (engraving, photo) | 0.60 – 0.75 | sometimes hovers right at threshold; cost of one extra fallback round on borderline cases is acceptable |
| Decoration-heavy pages with little text | 0.40 – 0.65 | model hallucinates letters out of stripes; fallbacks correctly find nothing better, so we keep 0° |
| Sideways/upside-down scans | 0.10 – 0.55 | upright pass fails; fallback finds the right orientation |

The threshold is exposed as an argument
(`auto_rotate_threshold` on `Document.from_image_ocr_via_doctr`,
`confidence_threshold` on `detect_best_rotation`) so a downstream caller
that knows their corpus can tune it without forking the module.

## Cost model

| Page condition | Predictor calls | Wall time on devcontainer GPU |
|---|---|---|
| Fast path (upright confident) | 1 | ~1–4 s/page |
| Fallback path (one orientation strictly best) | 4 | ~6–9 s/page |
| Fallback path (all rotations equally bad) | 4 | ~6–9 s/page; chosen = 0 |

The peutinger-map fixture concretely measured: upright 0.568 → fallback
chose 90° at 0.687, total wall time 8.4 s vs 3.4 s with `auto_rotate=False`.

## Page surface area

The chosen rotation is recorded on `Page.rotation_applied: int`. Allowed
values are `{0, 90, 180, 270}`; the constructor validates and rejects
anything else. The field round-trips through `to_dict` / `from_dict`,
but the default `0` is **omitted from serialized JSON** so existing
fixtures (and any pre-rotation OCR JSONs in the wild) deserialize
unchanged.

```python
doc = Document.from_image_ocr_via_doctr("rotated-page.png")
page = doc.pages[0]
if page.rotation_applied:
    print(f"OCR rotated this page {page.rotation_applied}° before recognition")
```

Consumers that want to reason about the original (pre-rotation) image —
e.g. a labeler UI displaying "this page was scanned upside-down; OCR
fixed it" — can do so by examining `rotation_applied` and applying the
inverse rotation to bbox coordinates if they need to project back onto
the source image.

## What this is *not*

- **Not arbitrary deskew.** Only quarter turns are tried. Pages scanned
  with a 3° tilt are corrected at the OCR-detection layer (DocTR's
  detection model handles small rotations natively), not here.
- **Not orientation classification.** We deliberately don't load a
  separate "is this page upside down" classifier. Re-running OCR is the
  truth signal — if a rotation produces better text, it's better. This
  uses the OCR predictor we already have rather than maintaining a
  second model with its own training data.
- **Not multi-page-aware.** Each page is rotated independently. A book
  with mixed-orientation pages (foldout map between two upright leaves)
  works fine; a book where every page is upside-down still pays the
  fallback cost on every page.

## What shaped this

- **Peutinger-map fixture** (`rotated-peutinger-map.png`) — a real PGDP
  page where DocTR returned 0.568 mean confidence upright. Without
  rotation detection, the reorganize baseline for this page is
  literally "RiL C / Le / RUIG Cs / S / 2 / se. / a / use / ie- pant"
  — visible in the regression baseline before this change.
- **Mock-based input-handling tests** (`test_document_coverage.py`) —
  predictors that return zero words get treated as zero confidence,
  triggering 4 OCR calls on what looks like a one-call test. Tests
  that are exercising input-type handling rather than rotation logic
  pass `auto_rotate=False` to keep the call shape deterministic.
- **`DEFAULT_CONFIDENCE_THRESHOLD = 0.6`** — chosen to accept noisy-
  but-readable plate captions while rejecting the hallucinate-letters-
  out-of-stripes failure mode on heavily-decorated pages. Should be
  re-tuned if a fixture lands that's borderline.

## TL;DR

Not yet captured during the B3 mechanical migration.

## Context

Not yet captured during the B3 mechanical migration.

## Constraints

Not yet captured during the B3 mechanical migration.

## Decision

Not yet captured during the B3 mechanical migration.

## Contract / Acceptance

Not yet captured during the B3 mechanical migration.

## Trade-offs considered

Not yet captured during the B3 mechanical migration.

## Consequences

Not yet captured during the B3 mechanical migration.

## Open questions

Not yet captured during the B3 mechanical migration.

## References

Not yet captured during the B3 mechanical migration.

## Adversarial Review

- **Stage:** Migration/post-implementation review dated 2026-07-13; no earlier live adversarial exercise is asserted.
- **Source:** Full spec compared with `ocr/rotation.py`, `Document.from_image_ocr_via_doctr`, batch ingestion, and `tests/ocr/test_rotation.py`.
- **Accepted findings:** Quarter-turn probing, threshold fallback, tie behavior, and rotated-frame image attachment are implemented and tested. The Page audit contract is not: current tests explicitly require `rotation_applied` to be absent from Page construction and serialization. Fold this in by separating the implemented detection behavior from the removed persistence design and marking any replacement audit/event path `needs_owner_decision`.
- **Disposition:** Accepted corrections and unresolved ideas are preserved in `docs/context/intent-map.md` as deferred work or owner decisions; the source body remains unchanged pending its next evidence-backed revision.
- **Residual risks:** Threshold and timing claims are historical measurements without a checked benchmark; probe diagnostics are discarded by ingestion; consumers cannot reconstruct the chosen rotation from serialized Page data.
