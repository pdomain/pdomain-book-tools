---
Status: active
Owner: CT
Created: 2026-07-13
Last verified: 2026-07-13
Kind: context
---

# Intent Map

## Agent Index

- **Kind:** context
- **Status:** active
- **Read when:** deciding whether proposed work is active, deferred, rejected, blocked, or awaiting an owner decision.
- **Search terms:** intent, deferred, rejected, blocked, legacy sweep.

## Active bets

- Complete the active designs in specs 06a–06c, 09, 10, page-order detection,
  scannos, and hyphen n-grams.
- Continue the residual work in docs/plans/roadmap.md.

## Deferred work

- Add a dirty flag for Page.items and Block.items sorting only if profiling
  shows repeated reads are material. Preserve the mutation-site coverage in
  tests/ocr/test_items_resort_l23.py. Evidence: retired review item L-23 in Git
  history for docs/archive/research/older/bugs-low.md.
- Decide whether a non-canonical DocTR Git URL should activate local-dev mode
  when a concrete fork-pin workflow needs it. Evidence: docs/plans/roadmap.md.

## Rejected directions

- Do not maintain a documentation archive tree. Promote durable truth, update
  inbound links, and rely on Git history for retired prose.

## Blocked (waiting on)

None.

## Needs owner decision

- Choose architecture destinations for implemented specs 01–05, 07, and the
  layout-debug auto-cleanup spec and plan before formal retirement.

## Legacy-unverified sweep

- **Can retire:** every file formerly under docs/archive/; the completed deep
  code/security review; Git history preserves their evidence.
- **Still active:** docs/plans/roadmap.md, docs/process/lint-deviations.md,
  docs/process/writing-style.md, active specs 06a–06c, 09, 10, hyphen n-grams,
  page-order detection, scannos, and the specs index.
- **Still active pending architecture promotion:** implemented specs 01–05, 07,
  layout-debug auto-cleanup, and its implementation plan.
- **Superseded:** the original word-reference-lines parent spec, replaced by
  specs 06a, 06b, and 06c.
- **Needs owner review:** none beyond the architecture destinations above.
