# Spec: Per-Character Bounding-Box Extraction

> **Status**: Draft
> **Last updated**: 2026-05-16
> **Spec-Issue**: (to be filed)

Extract per-character bounding boxes from a word image crop and the
associated OCR text string. The primary consumer is the
`pdomain-ocr-labeler-spa` CharFixer feature, which lets a human reviewer
drag individual character boxes into their correct positions before
saving a correction. The extracted boxes are also useful for training-
data pipelines in `pdomain-ocr-synth` and `pd-ocr-trainer` that need
character-level alignment signals.

This spec relates to:

- `Spec: 05-glyph-annotations` — the parallel side-channel annotation
  model for ligatures and long-s. Where glyph-annotations records
  *what* ligature is present, char-bbox extraction records *where*
  each rendered component sits on the image.
- `Spec: 01-page-model` — the `Word` / `Character` / `BoundingBox`
  types that this spec builds on.
- `Spec: 06b-word-reference-lines-api` — baseline / x-height geometry used
  to classify diacritic blobs vs. base-letter blobs (see also the
  parent index at `Spec: 06-word-reference-lines` (archived)).

---

## 1. Problem Statement

Word-level OCR is well-solved; character-level spatial alignment is
not. Three categories of difficulty dominate real-world book scans:

**Disconnected strokes.** Many characters consist of two or more
ink blobs that are not connected at the pixel level. Common cases:

- "i" and "j" — tittle (dot) is a separate connected component from
  the stem.
- "!" and "?" — dot separated from bar/hook.
- Diacritics: "ä ö ü é è ê ë â à á ã ì í î ï ñ ý ÿ ç" — the
  combining mark (umlaut, acute, grave, circumflex, cedilla, …) sits
  above or below the base letter as a distinct blob.
- Split ascenders/descenders — especially at low resolution or on
  worn type, the top of "f", "t", or "h" may detach.

A naive connected-component-per-character assignment will produce one
blob for the tittle and one for the stem of "i", misaligning every
subsequent character.

**Ligatures.** Typographers set "fi", "fl", "ff", "ffi", "ffl" (and
early-modern "ct", "st", "ſt", "ſs") as a single fused glyph. Two
competing needs arise:

- The OCR engine may recognize the ligature and emit it as one or two
  characters (e.g. "fi" as two chars, or as the Unicode ligature U+FB01).
- The labeler may want to show one merged bounding box labelled "fi"
  or two sub-boxes labelled "f" and "i" separately.

The spec resolves this with an explicit policy (see §4.4).

**Long-s (ſ).** The long-s ascender is nearly as tall as an "f" and
frequently merges with descenders ("p", "g", "y", "j") from the line
above when working on a full page image. This spec operates on the
word-level crop already isolated by the upstream pipeline, so
cross-line merging is avoided; however the ascender-to-line-above risk
remains when the crop is loose.

**Drop-caps.** The drop-cap pipeline (see `pdomain_book_tools/ocr/dropcap.py`)
already isolates the initial letter into its own `Word` with
`word_components = ["drop cap"]`. When the input `Word` is a drop cap,
the extraction must not attempt connected-component decomposition across
the body text that surrounds it; the word crop already contains only
the drop-cap letter, so standard extraction applies unchanged.

---

## 2. Input / Output Contract

### 2.1 Input

```python
def extract_char_bboxes(
    word_image: np.ndarray,        # word image crop; grayscale (H, W) or RGB (H, W, 3)
    word_text: str,                # OCR text for the word; no leading/trailing spaces
    word_bbox: BoundingBox,        # word's position in the page image (pixel-space)
    config: CharExtractionConfig | None = None,
) -> CharExtractionResult:
    ...
```

`word_image` is a crop already extracted by the caller. It MUST be in
pixel coordinates (not normalized). The dtype may be `uint8` or
`float32`; the extractor normalises internally.

`word_bbox` MUST be a pixel-space `BoundingBox` (`is_normalized=False`).
The extractor uses it only to translate relative word-image coordinates
back to page-image coordinates in the output.

`word_text` is the OCR string. It may contain:

- ASCII printable characters.
- Unicode letters with diacritics in precomposed NFC form (e.g. "ä"
  U+00E4, not "a" + U+0308).
- Ligature characters from the Alphabetic Presentation Forms block
  (U+FB00–U+FB06) when the OCR engine emits them.
- Long-s (U+017F).

It MUST NOT contain whitespace (words have no spaces; call this function
once per `Word`).

### 2.2 Output types

```python
@dataclass
class CharBbox:
    char: str                      # single character (may be precomposed, ligature, or long-s)
    bbox: BoundingBox              # tight box in PAGE pixel coordinates (is_normalized=False)
    confidence: float              # 0.0–1.0; 0.1 signals uniform-fallback
    components: list[BoundingBox]  # per-blob boxes in PAGE pixel coords; len >= 1
    is_joined: bool                # True when this char's ink merges with an adjacent char's ink

@dataclass
class CharExtractionResult:
    chars: list[CharBbox]          # len == len(word_text) after Unicode normalization
    word_text: str                 # NFC-normalized copy of the input word_text
    coverage: float                # fraction of foreground pixels claimed by any CharBbox
    method: str                    # "component", "doctr_ctc", "morphology", or "uniform"
```

`CharBbox.bbox` is always the union of all entries in `CharBbox.components`.

`CharBbox.components` has at least one entry. For a simple connected
character it has exactly one entry equal to `bbox`. For "i" with a
separated tittle it has two.

`is_joined` is `True` when the rightmost pixel column of `bbox` touches
or overlaps the leftmost pixel column of the next character's `bbox`,
or when the leftmost column of `bbox` touches the previous character's
rightmost column. Equivalently: adjacent `bbox` ranges overlap
horizontally. This flag helps the labeler UI decide whether to draw
a visible gap between boxes.

---

## 3. Algorithm

### 3.1 Pre-processing

1. Convert `word_image` to 8-bit grayscale if not already.
2. Binarize with Otsu's method (`cv2.threshold` +
   `cv2.THRESH_BINARY + cv2.THRESH_OTSU`). Store both the foreground
   mask (ink = 255) and background mask.
3. If the image is very dark (median pixel < `config.dark_page_threshold`)
   invert so ink is always bright — this handles scans where white
   paper was digitized with inverted polarity.

### 3.2 Connected Component Analysis

Run `cv2.connectedComponentsWithStats` on the binarized foreground
mask. Discard components whose pixel area is below
`config.min_component_area` (dust / JPEG artefacts).

Each surviving component is a candidate glyph blob with:

- Centroid `(cx, cy)` in word-image coordinates.
- Bounding rectangle `(x, y, w, h)`.
- Pixel area.

### 3.3 Diacritic / Tittle Detection

Classify each blob as a *diacritic candidate* when ALL of the
following hold:

1. `height < config.diacritic_height_ratio * word_image.height`
2. `area < config.diacritic_area_ratio * median_blob_area`
3. `cy < config.diacritic_y_ratio * word_image.height`
   (blob centroid is in the upper portion of the word image)

Classify as a *cedilla/descending diacritic* candidate when (1) and (2)
hold AND `cy > (1 - config.diacritic_y_ratio) * word_image.height`.

Diacritic candidates are tagged but not independently assigned to
characters in the sweepline; they are reassigned in §3.5.

### 3.4 Character-to-Blob Assignment (Sweepline)

Sort non-diacritic blobs left-to-right by centroid x.

The text is traversed in Unicode code-point order (left-to-right for
all scripts in scope; right-to-left support is out of scope, see §7).
For each character position `i` in `word_text`, assign the blob(s)
whose centroid falls within the horizontal span allocated to position
`i`.

Allocation is computed greedily:

1. For `N` characters and `M` non-diacritic blobs, compute a target
   x-width per character: `target_width = word_image.width / N`.
2. Walk blobs left-to-right, accumulating into the current character
   slot until the accumulated width exceeds `target_width`. Then
   advance the slot.
3. Empty slots (no blobs) get a synthetic zero-area placeholder at
   the expected position for subsequent diacritic merging.

This approach tolerates moderate mismatch (M ≠ N) without requiring a
global optimisation pass.

### 3.5 Diacritic / Tittle Reassignment

After the sweepline, reassign each diacritic-candidate blob to the
non-diacritic character that has the maximum horizontal overlap with
the diacritic blob's x-range. Ties are broken by proximity of centroids.

"Horizontal overlap" = length of intersection of the two x-intervals.

Characters in the alphabet whose diacritic reassignment MUST succeed:

| Precomposed char | Diacritic component | Component position |
|---|---|---|
| ä ö ü Ä Ö Ü | umlaut (two dots) | above |
| é É à á â ê è ë | accent / circumflex | above |
| ñ | tilde | above |
| ç Ç | cedilla | below |
| ì í î ï | accent / diaeresis | above |
| ý ÿ | acute / diaeresis | above |
| i (ASCII) | tittle | above |
| j (ASCII) | tittle | above |

Characters that look like they might have a diacritic but whose
diacritic is part of a single connected blob in normal printing (and
therefore do NOT trigger diacritic reassignment):

- "t" — crossbar connects to stem.
- "f" — the hook is part of the glyph.
- "!" "?" — dot may be separate; treat like "i" tittle.

### 3.6 Ligature Policy

This spec adopts the following policy, which aligns with
`Spec: 05-glyph-annotations §1.1`:

- If `word_text` contains a Unicode ligature codepoint (U+FB00–U+FB06),
  the extractor treats it as a **single character**. The resulting
  `CharBbox` has `char = "<ligature>"` (the codepoint) and
  `components` contains the blob(s) that make up the combined glyph.
- If `word_text` spells out the ligature as two ASCII chars (e.g. "fi")
  and the two chars share a merged blob (no gap between them), set
  `is_joined = True` on both. The bbox for "f" is the left portion
  of the merged blob (split at the estimated junction), and for "i"
  the right portion.
- The optional `CharExtractionConfig.split_ligature_blobs` flag
  (default `False`) controls whether to attempt to sub-divide the
  merged blob into per-letter boxes (useful for the CharFixer UI).
  When `False`, both "f" and "i" receive the full merged bbox and
  `is_joined = True`.

Rationale: The labeler's primary job is positioning correction, not
ligature decomposition (that is glyph-annotations territory). Keeping
the merged bbox available as a fallback avoids misleading sub-bboxes
when the split heuristic is wrong.

### 3.7 Long-s Handling

Long-s (U+017F, rendered as "ſ") has a tall ascender that may merge
with the line above in loose crops. Within the word crop:

- Treat long-s as a normal tall character; no special blob logic.
- If the crop includes pixels from the line above (detected by a blob
  that touches the top edge of the word image AND extends further
  than 1.5× the estimated x-height), clip that blob at the top
  by `config.long_s_top_clip_ratio * word_image.height` before
  assigning it.

Long-s text (`word_text` contains U+017F) is allowed. The extractor
does not convert it to "f" — that is `glyph_annotations` territory.

### 3.8 DocTR CTC Alignment (Optional Enhancement)

DocTR recognition models decode characters via CTC. The CTC alignment
matrix maps each output character to a range of horizontal column
positions in the feature map (which corresponds, approximately, to
column positions in the word image after accounting for the CNN
receptive field).

When `config.use_doctr_char_positions = True` and the caller passes
`doctr_char_cols: list[tuple[int, int]] | None` (a list of
`(col_start, col_end)` pairs in word-image x-coordinates, one per
character in `word_text`), the extractor substitutes those column
ranges for the sweepline allocation in §3.4, then runs §3.5
(diacritic reassignment) as normal.

`doctr_char_cols` is an optional parallel argument:

```python
def extract_char_bboxes(
    word_image: np.ndarray,
    word_text: str,
    word_bbox: BoundingBox,
    config: CharExtractionConfig | None = None,
    *,
    doctr_char_cols: list[tuple[int, int]] | None = None,
) -> CharExtractionResult:
```

When provided: `len(doctr_char_cols) == len(word_text)` (after NFC
normalization) is a precondition. If violated, the extractor logs a
warning and falls back to the sweepline.

How to obtain `doctr_char_cols` from the current pipeline is addressed
in §7 (Open Questions Q2).

### 3.9 Fallback: Uniform Division

When none of the above strategies produces `len(chars) == len(word_text)`,
or when `word_text` is a single character, divide the word width into
`N` equal vertical slices and assign one slice per character. Report:

- `confidence = 0.1` on every `CharBbox`.
- `method = "uniform"` on `CharExtractionResult`.

---

## 4. Edge Cases

| Situation | Behaviour |
|---|---|
| Single-character word | One `CharBbox`; confidence from component analysis or 1.0 if clean blob |
| More blobs than chars | Merge smallest orphan blobs into the nearest char (by centroid distance) |
| Fewer blobs than chars | Split largest blobs using a vertical cut at the expected character boundary |
| All chars fused into one blob | Uniform division fallback |
| Ligature codepoint in `word_text` | Single `CharBbox`; components = per-blob sub-boxes if separable |
| Ligature as ASCII pair with merged blob | Both chars get `is_joined=True`; split if `config.split_ligature_blobs` |
| Long-s (U+017F) | Clip ascender bleeding if it touches top of crop; treat as tall char |
| Drop-cap word | Standard extraction (crop is already isolated by dropcap pipeline) |
| Zero-width / combining codepoints | Should not appear in `word_text` (pre-NFC normalizes them away); if present, assign to preceding base character with zero-width bbox |
| Blank word_text | Return `CharExtractionResult(chars=[], word_text="", coverage=0.0, method="uniform")` |
| word_image smaller than 2×2 pixels | Return empty result with method="uniform" |

---

## 5. Configuration

```python
@dataclass
class CharExtractionConfig:
    # Binarization
    binarization_threshold: int = 0       # 0 → Otsu auto-threshold
    dark_page_threshold: int = 64         # median pixel below this → invert image

    # Component filtering
    min_component_area: int = 4           # discard dust blobs below this area (px)

    # Diacritic detection
    diacritic_height_ratio: float = 0.35  # blob height fraction of word height
    diacritic_area_ratio: float = 0.20    # blob area fraction of median blob area
    diacritic_y_ratio: float = 0.40       # centroid y fraction; above → diacritic zone

    # Long-s clipping
    long_s_top_clip_ratio: float = 0.15   # clip ascender bleed above this y fraction

    # Ligature sub-division
    split_ligature_blobs: bool = False    # attempt to split fused ligature blobs

    # DocTR CTC
    use_doctr_char_positions: bool = True  # prefer doctr_char_cols when provided
```

All thresholds are tunable. The defaults are calibrated for 300 DPI
greyscale scans of 19th-century English printed text at typical
font sizes (9–14 pt body copy).

---

## 6. Module Location and API

New file: `pdomain_book_tools/ocr/char_extraction.py`

Public surface (importable from `pdomain_book_tools.ocr`):

```python
from pdomain_book_tools.ocr.char_extraction import (
    CharBbox,
    CharExtractionConfig,
    CharExtractionResult,
    extract_char_bboxes,
)
```

`CharBbox` and `CharExtractionResult` follow the `to_dict` / `from_dict`
convention used by `Word` and `Character`:

```python
# CharBbox.to_dict() shape:
{
    "type": "CharBbox",
    "char": "ä",
    "bbox": { ... },            # BoundingBox.to_dict()
    "confidence": 0.85,
    "components": [ { ... } ],  # list of BoundingBox.to_dict()
    "is_joined": false
}
```

`CharExtractionConfig` does NOT need `to_dict` / `from_dict` — it is
a transient call-site parameter, not persisted in OCR snapshots.

### Relationship to `Word.split_into_characters_from_whitespace`

`Word.split_into_characters_from_whitespace` (introduced earlier in
`word.py`) uses a column-whitespace segmentation approach that works
well for widely-spaced characters but fails silently for touching or
diacritic-bearing characters. The new `extract_char_bboxes` function:

- Supersedes it for all production uses in `pdomain-ocr-labeler-spa`.
- Does NOT replace it in `word.py` immediately; the old method remains
  as a lower-dependency fallback (it has no cv2 connected-component
  dependency beyond what is already imported).
- `estimate_baseline_from_image` can stay on `Word`; it may optionally
  call `extract_char_bboxes` internally in a future refactor.

---

## 7. Tests

**Unit tests** (`tests/ocr/test_char_extraction.py`):

- Single ASCII character → one `CharBbox`, coverage near 1.0.
- Two clearly-separated ASCII characters → two `CharBbox`, correct order.
- "i" with a synthetic tittle blob above the stem → two components in
  one `CharBbox`; `char == "i"`.
- Precomposed "ä" (umlaut above "a") → two components; correct assignment.
- Ligature "fi" as merged blob with `split_ligature_blobs=False` →
  both chars `is_joined=True`, both receive the merged bbox.
- Uniform fallback triggered when single-blob word has 3-char text.
- Empty `word_text` → empty result.
- `word_image` 1×1 → empty result.

**Integration tests** (require test fixtures):

- Known word crops from `tests/fixtures/` with manually verified
  per-character bbox ground truth (add as part of the implementation
  slice, not this spec).

**Golden tests** (future):

- Real scanned word images from `tests/fixtures/layout_regression/`
  with per-char bbox annotations stored as JSON sidecars. Regeneration
  is explicit (not automatic) via a `make regen-char-bbox-fixtures` target.

---

## 8. Open Questions

**Q1 — Ligature sub-division UX.** Should `pdomain-ocr-labeler-spa` CharFixer
show ligature characters as one merged box or two sub-boxes? The policy
in §3.6 (`split_ligature_blobs=False` default) favours a merged box, but
the labeler could override this per session. This needs a UX decision
from the labeler spec owner before the CharFixer implementation lands.

**Q2 — DocTR CTC alignment access.** The current `run_page_ocr` pipeline
in `pdomain_book_tools/ocr/doctr_support.py` does not expose per-character
column positions. Accessing the CTC alignment requires either:

  (a) Patching the doctr fork to return logit-level alignment alongside
      the decoded string (preferred; adds ~10 lines to the recognition
      model forward pass).
  (b) Re-running recognition on each word crop with a modified model
      wrapper that captures intermediate outputs (expensive).
  (c) Accepting that `doctr_char_cols` will be `None` in v1 and falling
      back to the sweepline; add CTC integration as a follow-on.

Option (c) is the default plan for v1. Q2 stays open until the doctr
fork maintainer is consulted.

**Q3 — Right-to-left scripts.** Arabic, Hebrew, and other RTL scripts
require the sweepline to run right-to-left and the "left portion of
merged blob = f, right portion = i" logic to invert. Out of scope for
v1; all use cases are Latin / extended-Latin historical texts.

**Q4 — Coordinate normalization.** Should `CharBbox.bbox` support
normalized coordinates (0–1 relative to page) in addition to pixel
coordinates? The current design outputs pixel-space only (matching
`word_bbox` input). If the labeler API needs normalized coordinates,
the caller can scale with `BoundingBox.scale(w, h)` and reconstruct;
no spec change needed.
