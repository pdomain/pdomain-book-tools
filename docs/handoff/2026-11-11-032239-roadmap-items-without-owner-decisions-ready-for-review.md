---
kind: handoff
status: "active"
created: "2026-11-11"
created_at: "2026-11-11T03:22:38Z"
owner: "CT"
branch: "fix/roadmap-no-owner-items"
scope: "roadmap-no-owner-items"
worktree: "/mnt/work/projects/pdomain/pdomain-book-tools/.claude/worktrees/roadmap-no-owner-items"
base_commit: "029d05dd3b63f6d0f7ab4b613d42baffac70ba88"
supersedes: ""
handoff_reason: "user_requested"
host: "claude-code"
---

# Roadmap items without owner decisions ready for review

## Goal

Work through the roadmap items that need no owner decision: C1, C3, C4, D1, D2 and B4.

## Done

- C1: DocTR boxes are stated as normalized and Tesseract boxes as pixels (`04da801`).
- C4: grid `map_points` works and `PipelineResult.dewarp_outcome` separates not recommended, no backend, identity no-op and applied (`a094ed7`, `39cdd9a`).
- D1: all documented names are pinned, and the README moved off three internal import paths (`eb4df23`).
- D2: the architecture doc says who owns provenance (`e2c9a79`).
- B4: plate noise, both column strategies, floated flow and captions have tables. Using `tests/ocr` alone, the module went from 81.0% to 87.1% (`eeb9a82`).
- Five issue records are retired and current-state, the roadmap and the issue index are updated (`d23a23a`, `029d05d`).

## Not done

- C3 stays open. `BoundingBox` lives in `pdomain-book-contracts`, and the bug is in both the installed 0.2.0 and that repo's source. This repo has no callers of the two methods.
- A new bug is filed but not fixed: the floated-caption split never fires on normalized pages, which from the code includes DocTR pages. It was found with a synthetic probe, not a real DocTR page, and the fix changes output with no fixture to check it.
- The branch is not merged.

## Failed approaches

- One `make build` failed with a disk quota error on `/mnt/work` and passed on retry.

## Decisions

- DocTR coordinates outside 0 to 1 now raise instead of silently becoming pixels. A reviewer worried this could abort a page, but DocTR clips its boxes and both predictors assume straight pages.
- Grid `map_points` returns NaN for a point the warp moved off the page, because raising would lose the whole batch.
- Still open for the owner: the provenance home, and overriding the D1 and C4 defaults.

## State

Worktree clean. GPU tests were skipped, and the cupy path in grid `map_points` ran only against a fake array. The session left `fix/caption-reading-order` alone. The owner paused this work on 2026-11-10 and the session's herdr tab is closed. Nothing was pushed, merged, tagged, released or deployed. All work ran on CPU with the GPU hidden. The session's last terminal output is saved in `/mnt/work/projects/pdomain/.artifacts/handoff-20261110/session-output/`. `/tmp` is a shared tmpfs that ran out of quota several times on 2026-11-10 while ten sessions ran gates. If a gate fails with a quota error, point `TMPDIR` at the work drive and rerun before suspecting the code.

## Pointers

- `docs/issues/2026-11-10-floated-caption-thresholds-ignore-normalized-coords.md`
- `docs/plans/roadmap.md`
- `docs/issues/2026-07-21-owner-decision-pack-greenfield.md`

## Resume steps

1. Review `git log master..HEAD`.
2. Run the GPU-marked tests on a free card before merging.
3. Decide how to fix the floated-caption bug and what fixture proves it.
