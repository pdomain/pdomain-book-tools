---
kind: handoff
status: "active"
created: "2026-11-11"
created_at: "2026-11-11T05:11:25Z"
owner: "CT"
branch: "fix/roadmap-no-owner-items"
scope: "roadmap-no-owner-items"
worktree: "/mnt/work/projects/pdomain/pdomain-book-tools/.claude/worktrees/roadmap-no-owner-items"
base_commit: "17dc9fdc5bc01f35b741e59fb961561eee248457"
supersedes: "2026-11-11-032239-roadmap-items-without-owner-decisions-ready-for-review.md"
handoff_reason: "stopping"
host: "claude-code"
---

# Roadmap items: caption bug left open, B3 needs an owner accept

## Goal

Fix the floated-caption split against a real DocTR fixture, then finish the roadmap items that need no owner decision and no GPU, stopping after B3 and the `opencv-cuda` part of C5.

## Done

- C5 `opencv-cuda`: removed from `[gpu]` and the lock file. The dead `cv2cuda_processing` coverage omits are gone. `scripts/check_dev_local.py` now recognizes `cupy-cuda13x` (`b868a2a`).
- B3 record: the five strict xfail reasons now name the real reading-order failures. No output changed (`70b7c91`).
- Floated-caption fixture search recorded in the issue (`17dc9fd`).

## Not done

- The floated-caption bug stays open and its code is unchanged. No real page proves the fix. Of 154 real DocTR pages, 31 from the corpus and 123 scanned on CPU, the split ran on 6 and correct scaling found a caption prefix on none.
- The scan covered 123 of 702 candidates. Claude Code stopped it when the machine ran low on memory, and it was not restarted.
- B3 stays open. No xfail closed.
- C5 stays open for one item: `encode_bgr_image_as_png` still discards the `cv2.imencode` success flag. This was outside the requested `opencv-cuda` item.
- C3 was skipped because the fix belongs in `pdomain-book-contracts`.
- The branch is not merged.

## Failed approaches

- Packing each printed caption line into its own LINE, tried in memory at `emit_caption_block`, closes none of the five xfails and changes 6 other locked baselines. It makes those 6 readable, so it is a lead, but it needs case-by-case baseline promotion.
- `make ci AI=1` with the GPU hidden and no `CI=1` exits 2. `make setup` sees `nvidia-smi` succeed and installs `[gpu]`. Then 11 tests that treat an importable `cupy` as a usable device fail with `cudaErrorNoDevice`, and coverage is 85.7%, below the 87% gate.

## Decisions

Needed from the owner:

- B3: `plate-rio-harbour-photo` and `plate-service-on-board` want opposite results from nearly the same geometry, so at least one needs a dated accept. The table is in the xfail issue.
- Floated caption: scan the remaining 579 candidates when memory is free, or accept a synthetic fixture. Printed captions usually sit under the figure, so a proving real page may be rare.

Still open from earlier: the provenance home, and overriding the D1 and C4 defaults.

## State

Worktree clean at the commit before this handoff. `CI=1 CUDA_VISIBLE_DEVICES= make ci AI=1` exited 0 on the trees of all three commits, each with 2821 passed, 222 skipped and 5 xfailed. Those are real `make` statuses, not pipe statuses. One earlier run for `70b7c91` exited 2 because `ruff format` rewrapped a new test string, and the rerun passed. The GPU-marked tests did not run. No reviewer was dispatched for `b868a2a`, because its Python change is one constant. Nothing was pushed, merged, tagged, released or deployed. No live service changed. The scan log and the six saved pages are in `/mnt/work/pdt/tools/claude-1000/-mnt-work-projects-pdomain-pdomain-book-tools/b6fa2ce4-45c9-44a2-a92b-b01f2064c220/scratchpad/scan/`, which is not durable. `pdomain-ocr-cli` and `pdomain-ocr-simple-gui` still name `opencv-cuda`, but only in comments and docstrings.

## Pointers

- `docs/issues/2026-11-10-floated-caption-thresholds-ignore-normalized-coords.md`
- `docs/issues/2026-07-21-reorganize-known-failing-baselines-xfail.md`
- `docs/issues/2026-07-21-image-io-heif-write-failures.md`
- `docs/plans/roadmap.md`

## Resume steps

1. Review `git log master..HEAD`.
2. Run the GPU-marked tests on a free card before merging.
3. Get the two owner decisions above.
4. Once a proving page exists, write the failing tests listed in the floated-caption issue, then fix both functions together.
