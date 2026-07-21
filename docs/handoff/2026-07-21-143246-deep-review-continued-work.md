---
kind: handoff
status: "active"
created: "2026-07-21"
created_at: "2026-07-21T14:32:46Z"
owner: CT
branch: master
scope: deep-review-continued-work
worktree: /workspaces/pdomain/pdomain-book-tools
base_commit: e49d60601eac8cbb419164f130a0bd417235ca61
supersedes: ""
---

# Deep review continued work — pdomain-book-tools

## Agent Index

- Kind: handoff
- Status: active
- Read when: resuming implementation from the 2026-07-21 deep code review
- Search terms: deep review, continued work, docs/issues, reorganize A1, layout harness

## Goal

Execute the continued-work plan from the 2026-07-21 deep code review: close
confirmed P0 correctness and CI-truth gaps first, then layout test debt and
dual-path hardening, using the governed issue trackers as the work queue.

## Done this session

- Full-repo deep audit: 9 specialist agents + adversarial challenge passes.
- Wrote `docs/research/2026-07-21-deep-code-review-findings.md`.
- Wrote `docs/plans/2026-07-21-continued-work-from-deep-review.md` (Themes A–J, S0–S12+).
- Installed `docs/issues/` convention (README + TEMPLATE).
- Filed 27 issue reports mapped to plan items; two adversarial review passes on
  issues; post-commit adversarial pass aligned plan/findings with issue wording.
- Linked high-priority open issues from `docs/context/intent-map.md`.
- Commits on master:
  - `15405e3` docs: deep-review findings, continued-work plan, and issues
  - `e49d606` docs: align plan and findings with post-commit issue review
- No product code fixes landed (docs-only session).

## Not done

- No Theme A–D code implementation (S0–S9).
- No drop-cap Iteration C (F1 / S10).
- Theme E owner decision workshop not run.
- Greenfield modules (G–I) still blocked on Theme E.
- Issue-tracker migration handoff (`scope: issue-tracker-migration`) still
  active and separate; #208–#225 absorb into roadmap is tracked as issue D3
  but not executed.

## Failed approaches

- First commit attempt failed pre-commit markdownlint (MD040 bare fences, MD012
  double blanks, MD049/MD050 underscore emphasis). Fixed by language tags on
  fences, blank collapse, `*Open.*` / `` `__all__` ``, then re-committed.

## Decisions

- Work items live in `docs/issues/` (not only the plan prose).
- Soft-recover empty-bbox is filter documentation, not a permanent-loss product path.
- Geometry-correction conf=0 is identity no-op; missing backend is omit — not both “skip”.
- D1 public-API expand defaults to README-taught surface; do not claim monorepo/`hf`
  stability without a cite.
- F2/F3/Theme J deferred without dedicated issue files (noted in issues README).
- Plan A1 dual-domain matrix must be green before B1/B2 baseline rewrites.

## State

- Branch: `master` at `e49d606` (confirm with `git rev-parse HEAD`).
- Working tree clean except untracked `tmp/` (ignore).
- Primary index: `docs/issues/README.md` (27 open issues).
- Start implementation at S0 then S1–S3 (Theme A P0s).

## Pointers

- `docs/research/2026-07-21-deep-code-review-findings.md`
- `docs/plans/2026-07-21-continued-work-from-deep-review.md`
- `docs/issues/README.md`
- `docs/issues/2026-07-21-reorganize-coord-domain-thresholds.md` (A1)
- `docs/issues/2026-07-21-reorganize-early-return-skips-reconcile.md` (A2)
- `docs/issues/2026-07-21-reorganize-soft-recover-untested.md` (A3)
- `docs/issues/2026-07-21-gpu-textline-foreground-polarity.md` (A4)
- `docs/issues/2026-07-21-layout-regression-harness-without-layout.md` (B1)
- `docs/context/intent-map.md` (Open issues section)
- `docs/handoff/2026-07-17-issue-tracker-migration.md` (separate scope; still open)

## Resume steps

1. `git status` and `git log -3 --oneline` on master; confirm HEAD includes
   `e49d606` (or later) docs commits.
2. Read `docs/issues/README.md` High list, then plan Themes A–B.
3. Implement S0 (cheap docs): README orientation examples; public-api path;
   intent-map spec-07 stale line; roadmap #208–#225 absorb language — see issues
   A5, D2 path item, D3.
4. Implement S1 (A1): dual-domain unit tests that fail first; fix
   `_classify_row_block` / absolute thresholds in `reorganize_page_utils.py`.
5. Implement S2 (A2+A3): reconcile on early return; non-strict recover tests.
6. Implement S3 (A4): GPU `_ensure_foreground` mean gate + parity tests.
7. Do not re-baseline layout text until A1 matrix is green (B1 prerequisite).
8. Do not start G/H/I modules until Theme E decision pack is answered.
9. When closing an issue: set Resolution, retire via doc-retirer, move README
   pointer to Resolved.

## Pickup prompt

After `/clear`, send:

Use the docgraph:pickup-handoff skill for scope "deep-review-continued-work" in worktree "/workspaces/pdomain/pdomain-book-tools".
