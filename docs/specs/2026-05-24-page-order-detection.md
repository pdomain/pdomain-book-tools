---
Status: active
Owner: CT
Created: 2026-05-24
Last verified: 2026-07-13
Kind: spec
---

# Spec: Page-Order Detection

> **Status**: Draft
> **Last updated**: 2026-05-24
> **Spec-Issue**: pdomain/pdomain-book-tools#208

Detect pages that are out of sequence in a scanned book. Propose confident
swap pairs for the user to review. The primary consumer is the
`pdomain-prep-for-pgdp` Stage 11 (`/projects/:id/page-order`) introduced in the
`pdomain-ui` design handoff. The UI component that renders each detected swap is
`SwapRow` at `pdomain-ui/docs/templates/design_handoff_pdomain_ui/wf09/pages-tab.jsx:414-487`.

Related specs:

- [Page serialization](../architecture/page-serialization.md) — the `Page`
  type whose metadata this module reads.
- [Page reorganization](../architecture/reorganize-page-pipeline.md) — the
  upstream pipeline whose output provides
  OCR text from which page numbers may be extracted.

---

## 1. TL;DR

Add `pdomain_book_tools.page_order` exposing:

```python
from pdomain_book_tools.page_order import detect_out_of_order_pages, SwapProposal

proposals: list[SwapProposal] = detect_out_of_order_pages(pages)
```

A `SwapProposal` identifies two pages that are likely swapped. Its `confidence`
tier (`'high'` / `'medium'` / `'low'`) comes from agreement across up to three
independent signals: filename sequence number, OCR-extracted page number, and
perceptual-hash visual similarity.

---

## 2. Context

### 2.1 Why page-order detection belongs in pdomain-book-tools

Page reordering is a common artifact of physical scanning workflows. Scanners
mis-feed, operators grab pages in the wrong order, and older digitisation
batches have known sorting errors. Every pdomain-* consumer that works with
multi-page documents needs the same logic. Centralising it in the
foundation library avoids duplication across `pdomain-prep-for-pgdp`,
`pdomain-ocr-cli`, and future tools.

### 2.2 What the design handoff specifies

The `wf09/pages-tab.jsx` prototype shows:

- An "Auto-detect" banner that triggers a backend scan and surfaces
  `SwapRow` cards for each detected pair.
- Each `SwapRow` shows thumbnails for page A and page B, a confidence badge
  (`high` / `medium` / `low`), and signal chips summarising why the swap was
  proposed (e.g. "filename seq", "page number", "visual sim").
- Accept / Skip controls per row; an "Apply all high-confidence" shortcut.

The backend that powers `SwapRow` is the new
`GET /projects/:id/page-order/proposals` route in `pdomain-prep-for-pgdp`. That route calls
`detect_out_of_order_pages` and serialises the result. This spec owns the
detection side; `pdomain-prep-for-pgdp` owns the route and serialisation.

### 2.3 Signals available

| Signal | Source | Availability |
|---|---|---|
| Filename sequence number | `Page.source_path` basename, digit-run extraction | Always (if files have numeric names) |
| OCR page number | `Page.blocks` — footer/header containing a bare integer | Only when page has been OCR'd and reorganised |
| Visual similarity hash | Page thumbnail (derived from `Page.image_array` or a cached thumbnail) | Always (requires image access) |

---

## 3. Goals / Non-Goals

### Goals

- Expose a single pure function `detect_out_of_order_pages(pages)` with a
  documented, stable return type.
- Implement all three signals (filename, OCR page number, visual hash).
- Produce a three-tier confidence label backed by signal-agreement logic with
  clear, documented thresholds.
- Support pages with no image (image-array is `None`) gracefully — degrade to
  filename + OCR signals only.
- Support pages with no OCR (no `Page.blocks`) — degrade to filename + visual
  signals only.
- Be callable from a FastAPI endpoint without blocking the event loop (the
  heavy work is perceptual hashing; it should run in a thread pool or accept a
  pre-computed hash map).

### Non-Goals

- Auto-applying swaps — that is the UI's responsibility.
- Multi-page cycle detection (A→B→C misorderings involving three or more
  pages) — V1 targets pairwise swaps only.
- Duplex / recto-verso detection.
- Integration with the pdomain-prep-for-pgdp FastAPI router — that is owned by the
  downstream slice `S11-B`.

---

## 4. Constraints

- Must run on CPU; no GPU dependency.
- `detect_out_of_order_pages` must be pure (no side effects, no I/O) when
  called with a list of `Page` objects that already carry image arrays. An
  optional `thumbnail_cache: dict[str, bytes]` parameter allows callers
  (e.g. the FastAPI route) to pre-load thumbnails from disk without baking
  I/O into the function.
- The perceptual hash algorithm must be deterministic and stable across Python
  versions so that stored proposals can be compared to re-runs.
- Public API (`SwapProposal` fields, function signature) must be stable once
  shipped — `pdomain-prep-for-pgdp` serialises the return directly.

---

## 5. Options Considered

### O-A: Single-signal (filename only)

This option is fast to implement and useful when files have names such as
`IMG_0042.jpg`. It was rejected because it misses renamed out-of-order scans
and produces no confidence distinction.

### O-B: Two signals (filename + page number)

This option is reliable when OCR is available. It was rejected as the sole
approach because OCR may not have run yet at Stage 11. The filename signal
alone also gives no visual confirmation.

### O-C: Three signals with weighted agreement (chosen)

Each signal votes for or against a swap proposal independently. Confidence
tier is determined by how many signals agree:

- `high` — 3/3 signals agree, or 2/2 signals agree where the third is
  unavailable.
- `medium` — 2/3 signals agree (one disagrees or is unavailable).
- `low` — only 1 signal available and it flags an anomaly (no corroboration).

This approach is extensible. New signals, such as chapter-heading detection,
can add votes without changing the tier logic.

---

## 6. Decision

Implement O-C. The module is `pdomain_book_tools/page_order.py`. The public
surface is:

```python
@dataclass
class SwapProposal:
    id_a: str          # Page.page_id of the first page
    id_b: str          # Page.page_id of the second page
    confidence: Literal['high', 'medium', 'low']
    signals: dict[str, object]
    # signals keys (present only when signal was evaluated):
    #   'filename_seq': {'expected_a': int, 'expected_b': int,
    #                    'actual_a': int | None, 'actual_b': int | None}
    #   'ocr_page_num': {'expected_a': int, 'expected_b': int,
    #                    'actual_a': int | None, 'actual_b': int | None}
    #   'visual_sim':   {'hash_a': str, 'hash_b': str,
    #                    'similarity': float,
    #                    'verdict': 'similar' | 'dissimilar' | 'unknown'}


def detect_out_of_order_pages(
    pages: list[Page],
    *,
    thumbnail_cache: dict[str, bytes] | None = None,
    hash_size: int = 8,
    sim_threshold: float = 0.85,
) -> list[SwapProposal]:
    ...
```

The `signals` dict is intentionally untyped at the value level: its values are
`object`. This keeps the `SwapProposal` dataclass serialisable without adding
discriminated-union machinery. Callers that need typed signal
access can use typed helpers in the same module.

---

## 7. Implementation Plan

### 7.1 File layout

```text
pdomain_book_tools/
  page_order.py          # public module
  _page_order_impl/
    __init__.py
    filename_signal.py   # digit-run extraction from page source paths
    ocr_page_num.py      # OCR text scanning for bare integers in footers/headers
    visual_hash.py       # perceptual hash (average hash, then dHash fallback)
    voting.py            # signal aggregation + confidence tier logic
```

### 7.2 Signal implementations

**filename_signal.py** — Extract the last continuous digit run from the
basename of `Page.source_path`. For `IMG_0042.jpg`, that is `42`. Sort all
pages by their extracted digit. Flag pairs where the sorted position differs
from the list position by more than a configurable tolerance, which defaults
to 2 positions. Return proposed swap pairs.

**ocr_page_num.py** — Scan `Page.blocks` for blocks with
`block_role_labels` containing `footer` or `header`. Within those blocks,
find `Word` text that parses as a bare integer in a plausible range (1 to
`len(pages) * 2`). Cross-reference against the page's list index. Return
`(page_id, detected_num)` pairs; caller drives the voting.

**visual_hash.py** — Compute an 8x8 average hash (`imagehash.average_hash`
or a pure-numpy equivalent to avoid the `imagehash` dependency). For any
pair of candidate pages, compute hash Hamming distance normalised to
`[0.0, 1.0]`. A high-similarity pair (> `sim_threshold`) that appears in
the wrong position reinforces a swap proposal; dissimilar pair weakens it.

**voting.py** — Given per-page signal outputs, enumerate adjacent and
near-adjacent page pairs that any signal flagged. Run the three-signal voting
logic. Return `list[SwapProposal]` sorted first by descending confidence and
then by the list index of the first page.

### 7.3 `__init__` exports

```python
# pdomain_book_tools/__init__.py — add to public re-exports
from pdomain_book_tools.page_order import (
    SwapProposal,
    detect_out_of_order_pages,
)
```

### 7.4 Dependency notes

Perceptual hashing requires either `imagehash`, as a new optional dep, or a
~20-line pure-numpy implementation. Prefer the pure-numpy path first. Add
`imagehash` as an optional dep only if the accuracy delta is
significant enough to justify it.

---

## 8. Test Plan

| Test | Location | What it checks |
|---|---|---|
| `test_filename_signal_ordered` | `tests/test_page_order.py` | Ordered pages → no proposals |
| `test_filename_signal_one_swap` | same | Two swapped pages → one proposal |
| `test_filename_signal_no_digits` | same | Pages with non-numeric names → signal absent, no crash |
| `test_ocr_page_num_detects_swap` | same | Page with footer "42" at list index 43 → flagged |
| `test_ocr_page_num_no_blocks` | same | Pages without OCR → signal absent, no crash |
| `test_visual_hash_similar` | same | Two near-identical images → `similarity > sim_threshold` |
| `test_visual_hash_dissimilar` | same | Blank page vs. text page → `similarity` below threshold |
| `test_confidence_high_three_agree` | same | All three signals agree on a swap → `'high'` |
| `test_confidence_medium_two_agree` | same | Two signals agree, one absent → `'medium'` |
| `test_confidence_low_one_signal` | same | Only filename signal available → `'low'` |
| `test_no_image_array` | same | Pages with `image_array=None` → only filename+OCR signals run |
| `test_round_trip_serialisable` | same | `SwapProposal` is JSON-serialisable via `dataclasses.asdict` |

---

## 9. Open Questions

- **Q-PO-1**: Should `detect_out_of_order_pages` accept a pre-built
  `list[SwapProposal]` to merge with (e.g. for incremental re-runs after
  new pages are appended)? Decision deferred to implementation.
- **Q-PO-2**: Should `imagehash` be added as a mandatory dep, an optional
  dep under a `[page-order]` extra, or replaced entirely with a
  pure-numpy implementation? The pure-numpy path is preferred unless
  accuracy testing shows a significant gap.
- **Q-PO-3**: The `wf09` design shows a thumbnail image per `SwapRow`. The
  thumbnail generation (resize + encode to JPEG bytes) is straightforward but
  not specified here. Should `SwapProposal` carry an optional
  `thumbnail_a_b64: str` field, or should the FastAPI route build thumbnails
  independently from `Page.image_array`? Leaning toward route-owns-thumbnails
  to keep `SwapProposal` data-only, but needs alignment with the
  `pdomain-prep-for-pgdp` slice owner.

## Adversarial Review

- **Stage:** Migration/design review performed 2026-07-13; no implementation was found.
- **Source:** Full spec and current `Page`, block-role normalization, image-cache, and test code.
- **Accepted findings (and how folded in):** Align the API with `Page.name`, `page_index`, and UUID `page_id`; use the normalized page-role labels; remove visual pair similarity as a swap vote unless a validated positional model is supplied; reconcile confidence tiers; and define numbering gaps/front matter before proposing swaps. Keep thread offloading in the downstream caller or expose a clearly separate async wrapper.
- **Disposition:** Accepted corrections and unresolved ideas are preserved in `docs/context/intent-map.md` as deferred work or owner decisions; the source body remains unchanged pending its next evidence-backed revision.
- **Residual risks:** Pairwise proposals cannot model cycles or arbitrary moves, and no labelled corpus establishes precision, recall, thresholds, or safe high-confidence auto-application.
