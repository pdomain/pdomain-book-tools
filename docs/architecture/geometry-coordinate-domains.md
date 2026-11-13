---
Status: built
Owner: CT
Created: 2026-11-13
Last verified: 2026-11-13
Kind: architecture
---

# Geometry coordinate domains

## Agent Index

- **Kind:** architecture
- **Status:** built
- **Last verified:** 2026-11-13
- **Read when:** constructing geometry, checking containment, or changing OCR ingress flags.
- **Search terms:** is_normalized, center, contains_point, contracts, unit-square pixel, ingress.

Geometry carries an explicit coordinate-domain flag. OCR ingress sets that flag, and operations that combine incompatible domains fail rather than silently converting them.

## Shared primitives and containment

`pdomain_book_tools.geometry.point.Point` and `geometry.bounding_box.BoundingBox` re-export the contracts implementations. This repository requires `pdomain-book-contracts >=0.3.1`; its lockfile and inspected worktree environment select 0.3.1.

In that version, `BoundingBox.center` passes the box's `is_normalized` flag into the returned Point. A pixel box inside the unit square therefore retains a pixel center. `contains_point` raises `ValueError` when point and box domains differ, in either direction. Same-domain containment includes edges. Callers constructing pixel points inside the unit square must specify the pixel domain rather than rely on coordinate-range inference.

Image refinement remains in this library. The re-exported box's compatibility wrappers require the registered image-operations provider; importing `geometry.image_ops` registers it.

## OCR ingress states its domain

DocTR ingress explicitly constructs normalized boxes with `is_normalized=True`. Out-of-range normalized geometry raises instead of becoming pixels. Tesseract ingress explicitly uses `is_normalized=False`, including one-pixel boxes at the origin. These are implemented behavior from `04da801`.

## Remaining helper audit

The center and containment defects are resolved in the consumed contracts version. The broader scale and four-point helper audit remains unverified. This document does not claim that audit is complete. Its remaining work stays in [roadmap C3](../plans/roadmap.md) and [the continued-work plan](../plans/2026-07-21-continued-work-from-deep-review.md#c3-geometry-primitive-flag-hygiene).

## Evidence

- **Code:** `pdomain_book_tools/geometry/point.py`, `bounding_box.py`, `image_ops.py`, and `pdomain_book_tools/ocr/document.py`; installed contracts 0.3.1 `geometry/bounding_box.py`, `center` and `contains_point`.
- **Tests inspected:** `tests/geometry/test_bounding_box.py` covers same-domain containment and edges. `tests/ocr/test_ocr_ingress_is_normalized.py` covers unit-square pixel ingress, explicit domains, and rejected out-of-range DocTR geometry.
- **Dependency evidence:** `pyproject.toml`, `uv.lock`, and the worktree's installed contracts metadata select the repaired dependency.
- **Verification:** source inspected on 2026-11-13 at `50fcb0e`. The migration coordinator separately checked installed 0.3.1: pixel-center preservation, both containment mismatch directions, and same-domain containment passed. This is a local consumption check, not a claim that upstream contracts tests ran.
