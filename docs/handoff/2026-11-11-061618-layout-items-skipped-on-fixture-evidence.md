---
kind: handoff
status: "active"
created: "2026-11-11"
created_at: "2026-11-11T06:16:18Z"
owner: "CT"
branch: "feat/layout-no-owner-items"
scope: "layout-no-owner-items"
worktree: "/mnt/work/projects/pdomain/pdomain-book-tools/.claude/worktrees/layout-no-owner-items"
base_commit: "0a918f8b44e7d3b4bc7f0060307ca819e665b7c1"
supersedes: "2026-11-11-051125-roadmap-items-caption-bug-left-open.md"
handoff_reason: "stopping"
host: "claude-code"
---

# Layout items: all three skipped, the fixtures do not support them

## Goal

Build three layout items from `docs/plans/roadmap.md` that need no owner decision, no training and no GPU, one commit each, test-first with layout fixtures: drop-cap Iteration C, sidenote-aware row-block expansion (gh-006, gh-049), and sidenote x-height projection (gh-004, gh-047).

## Done

- No code changed. All three items were checked and skipped. The only commit on this branch is this handoff.
- Found why no real page gets sidenote tags. `detect_geometric_sidenotes` in `pdomain_book_tools/ocr/layout_aware_reorg.py` takes the body's right and left edges from the median of all word edges, which falls mid-page. This bug has no issue record yet.

## Not done

**Drop-cap Iteration C is skipped because it needs owner decisions.**

- The acceptance test cannot pass by a heading check. `footnotes-stacked-with-anchor` has no heading above "A BELIEF". Its only heading is the running header "358 CREDULITIES PAST AND PRESENT." The word "omens" appears zero times in its OCR and proofread text, and the page image shows no such title. The issues' "A BELIEF IN OMENS" example does not match this page.
- Of 31 fixtures, the only other `drop cap unrecovered` tags are "AIOCKO" and "The" on `inline-figure-with-greek-labels`. I did not investigate that page. No fixture was found where a heading restates an ambiguous cap.
- Rendering "A BELIEF" needs a new tag. `Block.text` fuses every `drop cap` word to the next word, which would give "ABELIEF". The tag list lives in `pdomain_book_contracts/text/label_normalization.py`, outside this repo.

**Sidenote-aware row blocks (gh-006, gh-049) are skipped because their prerequisite is an open decision.**

- gh-006 says it must not start before the sidenote tuning slice ships. gh-003, the keep-`None`-or-`0.85` decision, is still open. The plan says this waits until fixtures need it.
- Fixtures do not need it yet. Across 31 fixtures run with layout, at both `None` and `0.85`, no word received a sidenote label. Both `sidenote-*` fixtures have no column split at all, so the spurious third column does not reproduce. The sidenote text is merged into body lines by OCR, for example "Valen- The in-".

**Sidenote x-height projection (gh-004, gh-047) is skipped because its prerequisite is not met.**

- The issue requires a fixture that bbox height misclassifies and projection corrects. No fixture reaches the height gate, because the detector rejects every cluster first.
- A scratch measurement found no sign that projection would help. Sidenote words were picked by hand-set x-ranges, and x-height was one crude method, the rows at or above 50% of the peak.

| Fixture | Median word right edge | Bbox height ratio | Projection x-height ratio |
|---|---|---|---|
| `sidenote-right-with-footnotes` | 0.454 | 0.857 | 1.000 |
| `sidenote-left-with-footnotes` | 0.581 | 0.975 | 1.050 |
| `decorative-headpiece-list-of-illus` | 0.418 | 0.971 | 0.944 |

All three bbox ratios are above `0.85`, so flipping the default to `0.85` would reject all three real sidenotes once the detector can find them. This is evidence for gh-003.

## Failed approaches

- A heading check limited to fused matches, such as "HERE" resolved by a title "THERE WAS", needs no contract change. I did not build it, because no fixture exercises it and it would not close the item.

## Decisions

Needed from the owner:

- Drop-cap C: drop the `BELIEF` flip from the acceptance criteria, or pick a method that does not use a heading, such as recognizing the cap glyph. If whole-word caps should render with a space, approve a new tag in `pdomain-book-contracts`.
- Sidenotes: my recommendation is to fix the detector's body-edge calculation first, as its own issue, then rerun the gh-003 sweep. gh-004 and gh-006 both depend on real tags. The fix changes output on pages with layout, so it needs baseline review.

Carried over from the retired handoff:

- B3: `plate-rio-harbour-photo` and `plate-service-on-board` want opposite results from nearly the same geometry, so at least one needs a dated accept.
- Floated caption: scan the remaining 579 candidates when memory is free, or accept a synthetic fixture.
- The provenance home, and overriding the D1 and C4 defaults.

## State

Worktree clean at `0a918f8` before this handoff, and identical in code to `fix/roadmap-no-owner-items`. Both gate runs had `CUDA_VISIBLE_DEVICES` empty and `TMPDIR` under `/mnt/work/pdt/tools2`, and both statuses are real `make` statuses, not pipe statuses.

- `make ci AI=1` exited 2: 11 failed, 2825 passed, 207 skipped, 5 xfailed, coverage 85.66% against the 87% floor. All 11 failures need a GPU: 10 are `cudaErrorNoDevice` and 1 is the assertion "This should only run when CUDA is available". `make setup` sees `nvidia-smi` succeed and installs `[gpu]`, so tests that see `cupy` run with the card hidden. This is the failure the retired handoff recorded.
- `CI=1 make ci AI=1` exited 0: 2821 passed, 222 skipped, 5 xfailed, coverage 90.29%. The GPU-marked tests did not run.

Nothing was pushed, merged, tagged, released or deployed. No live service changed. No GPU job ran. No reviewer was dispatched, because no code changed. The scratch scripts are in `/mnt/work/pdt/tools2/claude-1000/-mnt-work-projects-pdomain-pdomain-book-tools/33c496ab-8cd4-4cbd-9df9-99dfa2ad1029/scratchpad/`, which is not durable.

## Pointers

- `docs/plans/roadmap.md`
- `docs/issues/2026-07-21-dropcap-iteration-c-heading-crosscheck.md`
- `docs/issues/2026-05-10-gh-005-drop-cap-heading-cross-check.md`
- `docs/issues/2026-05-10-gh-003-sidenote-height-ratio-default.md`
- `docs/issues/2026-05-10-gh-004-sidenote-projection-x-height.md`
- `docs/issues/2026-05-10-gh-006-sidenote-aware-row-blocks.md`
- `pdomain_book_tools/ocr/layout_aware_reorg.py`
- `pdomain_book_tools/ocr/dropcap.py`

## Resume steps

1. Get the owner decisions above.
2. If the detector fix is approved, file an issue, write a failing test on `sidenote-right-with-footnotes`, fix the body-edge calculation, and review the baseline changes.
3. Rerun the `None` versus `0.85` sweep for gh-003 on the fixed detector.
4. Reassess gh-004 and gh-006 against the real tags.
