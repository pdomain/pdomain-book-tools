# Copilot Project Instructions: pd-book-tools

Concise, project-specific guidance for AI coding agents contributing to this repo.

## 1. Core Domain & Architecture
- Purpose: Tools for processing public domain book scans: OCR ingestion, geometric normalization, refinement, labeling, and ground-truth alignment.
- Key layers:
  - `pd_book_tools/geometry/`: Primitive spatial types (`Point`, `BoundingBox`) with normalization semantics (normalized vs pixel). All downstream logic relies on correct `is_normalized` flags.
  - `pd_book_tools/ocr/`: OCR result object model (`Word`, `Block`, `Page`) plus matching (`ground_truth_matching.py`), external OCR/tool adapters (`cv2_tesseract.py`, `doctr_support.py`), and utilities.
  - `pd_book_tools/image_processing/`: CV + (optional) GPU variants (cupy / opencv-cuda) for transformations (color, crop, morph, threshold, etc.). Many files are thin wrappers—keep them small & focused.
- Data flow (typical): raw OCR tool output -> `Word`s (normalized or pixel bboxes) -> grouped into `Block`s (hierarchy Lines / Paragraphs / Blocks) -> aggregated into `Page` -> refined (bbox refine/crop) -> ground truth match augmentation.

## 2. Coordinate System Conventions (Critical!)
- `BoundingBox` & `Point` track `is_normalized` (True => values in [0,1]; False => pixel space). Inference happens on construction if unspecified.
- Cross-box operations (union, intersection, IoU, merge/split in `Word`) REQUIRE matching coordinate systems; code raises `ValueError` when mismatched.
- Scaling APIs:
  - `BoundingBox.scale(width, height)`: ONLY for normalized -> pixel.
  - `BoundingBox.normalize(width, height)`: ONLY for pixel -> normalized.
  - `Word.scale(width, height)`: deep-copies; if already pixel-space returns unchanged deep copy (logs info); if normalized, scales bbox to pixel, leaves ground-truth bbox untouched.
- When adding new APIs manipulating multiple boxes, enforce coordinate uniformity early.

## 3. Object Model Highlights
- `Word`:
  - Deep copy pattern relies on `to_dict` / `from_dict` for safety (lists/dicts cloned). Follow this when creating variant instances.
  - `merge` & `split` add provenance flags (`ground_truth_match_keys['split']`). Preserve existing flags when extending.
  - On merges: label dedup happens via set + order-stable dict trick; replicate pattern if extending label logic.
- `Block`:
  - Hierarchical: contains either `Word`s or child `Block`s (see `child_type`). Sorting is positional (top-left y then x); advanced multi-column sorting is TODO—don’t over-engineer new ordering heuristics without tests.
  - Bounding box auto-computed via `BoundingBox.union` if not provided.
- `Page`:
  - Similar aggregation pattern; recompute page bbox after structural edits.
  - Rendering/debug functions (drawing bboxes) rely on consistent pixel coordinates—ensure you normalize or scale before drawing.

## 4. Image Refinement Pipeline
- `BoundingBox.refine` / `crop_top` / `crop_bottom` temporarily scale to pixel space if normalized, run thresholding (OTSU, inverted), compute tight rectangle, then (if originally normalized) renormalize—preserve this round-trip.
- When adding new refinement routines use `_extract_roi` & `_threshold_inverted` helpers to stay consistent and reduce duplication.

## 5. Testing & Coverage
- Tests live under `tests/ocr/` and cover: serialization, coordinate scaling, merge/split invariants, deep copy semantics, mismatch error raising, refinement.
- New features touching coordinate logic must introduce tests for: success path + coordinate mismatch error.
- **ALWAYS** run tests using `uv run pytest` (coverage auto-configured via `pyproject.toml`). **NEVER** use direct python/pytest commands - UV manages dependencies and environment properly.
- Keep public behavior stable; many assertions depend on exact bbox tuples and concatenated text ordering.

## 6. Dependency & Tooling Workflow
- **MANDATORY**: Use `uv` for ALL dependency and environment management (see README). **ALWAYS** use `uv add <pkg>` for new deps; ensure version constraints remain compatible with Python >=3.10.
- Build: `uv build` (hatchling backend).
- **CRITICAL**: All tooling commands MUST be run through UV: `uv run pytest`, `uv run ruff format`, `uv run ruff check`, etc. **NEVER** run tools directly without UV prefix.
- Lint/format/test quality tools present: `ruff`, `pytest`, `pre-commit`, `pylint`, `isort`. Favor `ruff` for quick lint fixes; keep changes minimal in unrelated lines.
- **ALWAYS** run `uv run ruff format` after making changes.
- GPU optional: cupy / opencv-cuda; guard GPU-specific code paths if adding runtime checks.

## 7. Performance & Safety Notes
- Prefer arithmetic over Shapely when simple (already adopted in horizontal splits). Only use Shapely for geometry unions / more complex intersection logic.
- Avoid mutating existing bbox instances in place when semantics require provenance (create new via factories); this keeps normalization inference reliable.
- Large images: keep ROI extraction localized; do not copy entire image unless necessary.

## 8. Serialization & Backward Compatibility
- `BoundingBox.to_dict` includes `is_normalized`. `from_dict` tolerates legacy dicts missing the flag (infers). Preserve this loose ingestion behavior when extending schema.
- If adding new fields to serialized objects (Word/Block/Page), make them optional with sensible defaults to avoid breaking old JSON.

## 9. Patterns to Emulate
- Validation early, explicit error messages (e.g., mismatched coordinate systems).
- Use helper factory methods (`from_ltrb`, `from_ltwh`, `from_points`) rather than constructing raw dataclasses directly when outside current module.
- Deep copy via `to_dict`/`from_dict` when returning transformed versions of entities (scale, refine, etc.).

## 10. Adding New Functionality (Example)
- Need a horizontal expansion of a `Word` bbox by N pixels:
  1. Verify bbox is pixel-space; if normalized, either raise or scale then expand.
  2. Use `BoundingBox.expand(dx,0)` producing new bbox (preserving `is_normalized`).
  3. Return deep-copied new `Word` instance (`data = deepcopy(word.to_dict()); data['bounding_box']=new_bbox.to_dict(); Word.from_dict(data)`).
  4. Add tests for pixel & normalized inputs (normalized path should log or convert intentionally).

## 11. Ground Truth Integration
- Matching flow occurs in `ground_truth_matching.py` (large, currently sparsely covered). When interacting with it, focus on incremental improvements and add targeted tests for new pathways.
- Preserve existing `ground_truth_match_keys` structure; merge dictionaries rather than replacing.

## 12. What NOT to Do
- Do not silently coerce between normalized/pixel in merge/split/union—explicit failures are protective.
- Do not mutate `Point.is_normalized`; create new `Point` instead (immutable contract).
- Avoid adding hidden global state; pass width/height explicitly for normalization/scaling.

## 13. Adding new test cases
- Add tests cases in similar folder structure (tests/<submodule>/<class>.py). Don't create multiple files for adding tests.

---
Feedback welcome: identify unclear areas (e.g., multi-column layout handling, ground-truth matching internals) to refine these instructions.
