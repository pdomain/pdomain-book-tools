---
Status: built
Owner: CT
Created: 2026-07-13
Last verified: 2026-07-13
Kind: architecture
---

# OCR page orientation

## Agent Index

- **Kind:** architecture
- **Status:** built
- **Read when:** changing DocTR ingestion, quarter-turn probing, confidence thresholds, or the image coordinate frame used after OCR.
- **Search terms:** auto rotate, detect_best_rotation, RotationProbe, rotated frame, DocTR orientation, rotation degrees.

## Current behavior

DocTR ingestion enables quarter-turn orientation probing by default. `detect_best_rotation()` evaluates the image at 0 degrees first. It computes mean confidence from Words whose `ocr_confidence` is not `None`; when no such words exist, the result is zero confidence and zero words.

If the upright confidence meets `DEFAULT_CONFIDENCE_THRESHOLD` (`0.6`), the helper returns the upright OCR result without fallback probes. Otherwise it tries the remaining configured rotations in order. The default sequence is 0, 90, 180, and 270 degrees clockwise. A candidate replaces the current best only when its confidence is strictly greater, so ties retain the earliest rotation. The `rotations` argument must start with zero.

`rotate_image()` returns the original array for zero degrees and uses lossless NumPy quarter turns for 90, 180, and 270 degrees. Other angles raise `ValueError`.

`detect_best_rotation()` returns the chosen degrees, the Document produced at that orientation, and a `RotationProbe` for every attempted orientation. Each probe carries the rotation, mean confidence, and contributing word count. An `upright_result` can supply an existing zero-degree OCR result and avoid repeating that call.

## Document integration

`Document.from_image_ocr_via_doctr()` returns `(document, rotation_degrees)`. With automatic rotation enabled, it calls the detector and attaches the source image rotated by the chosen degrees to the OCR Page. With automatic rotation disabled, it performs one OCR call, attaches the unrotated image, and returns zero degrees. Bounding boxes in the returned OCR tree therefore address the attached image frame.

`Document.from_images_ocr_via_doctr()` performs the initial upright OCR as a batch. Pages at or above the threshold retain their upright result. Each lower-confidence page reuses its existing upright result and probes only the fallback orientations. When a fallback wins, its Page replaces the upright Page while retaining the batch page index. The method attaches the chosen image frame to every Page and returns a Document. It does not return per-page rotation degrees or probes.

## Audit boundary

`Page` has no `rotation_applied` field. Page construction rejects that keyword, and Page serialization does not store a rotation angle. The singular ingestion method exposes the chosen angle only in its return tuple. Both singular and batch ingestion discard the probe list after choosing an image. Durable rotation audit events and persisted diagnostics are not part of the current architecture.

## Evidence

- `pdomain_book_tools/ocr/rotation.py`: `DEFAULT_ROTATIONS`, `DEFAULT_CONFIDENCE_THRESHOLD`, `RotationProbe`, `rotate_image`, `_mean_confidence`, and `detect_best_rotation`.
- `pdomain_book_tools/ocr/document.py`: `Document.from_image_ocr_via_doctr`, `Document.from_images_ocr_via_doctr`, and `Document.make_doctr_ocr_fn`.
- `pdomain_book_tools/ocr/page.py`: current Page fields and serialization, which contain no rotation field.
- `tests/ocr/test_rotation.py`: quarter-turn image behavior, fallback selection, tie handling, empty OCR results, threshold override, rotation-sequence validation, upright-result reuse, and absence of `Page.rotation_applied`.
- `tests/ocr/test_document_coverage.py`: DocTR ingestion input and automatic-rotation call paths.
- `tests/test_page_model_doc.py`: explicit exclusion of `rotation_applied` from serialized Page data.

## Residual intent

The decision whether rotation probes need a durable audit or event surface, and reproducible calibration for threshold and timing claims, remains deferred in `docs/context/intent-map.md`. This document does not repeat historical fixture confidence ranges, timing measurements, or a persisted Page rotation contract because current tests and serialization do not establish them.
