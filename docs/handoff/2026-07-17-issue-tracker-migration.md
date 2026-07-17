---
kind: handoff
status: "active"
created: "2026-07-17"
created_at: "2026-07-17T09:18:02Z"
owner: CT
branch: master
scope: issue-tracker-migration
worktree: /workspaces/pdomain/pdomain-book-tools
base_commit: 131f9589be43ad3b6ef89128ea1a6798f1a0f411
supersedes: ""
---

# Issue tracker migration — pdomain-book-tools

## Agent Index

- Kind: handoff
- Status: active
- Read when: picking up the issue-tracker migration for this repo
- Search terms: issue tracker migration, roadmap, closed issues archive, gh
  issue delete, docs/roadmap.md, docs/decisions archive

## Goal

Clear this repo's GitHub issue tracker: migrate the open backlog into
`docs/roadmap.md`, archive every in-scope issue's full text into Git history,
then delete the issues from GitHub. This is the same proven pattern already
run on `pdomain-ocr-cli` (50 issues) and `pdomain-ocr-simple-gui` (37 issues,
roadmap-first).

## Current state

Open issues: 33. Closed issues: 181. `docs/decisions/` exists (currently
empty except `.gitkeep`). `docs/roadmap.md` does not exist yet. `docs/handoff/`
did not exist before this doc. Docgraph is present (`DOCGRAPH.md` at repo
root). Admin access on the repo is confirmed
(`gh api repos/pdomain/pdomain-book-tools` reports `admin: true`).

Label breakdown across the 33 open issues:

- `kind:*` — 17 `kind:feature`, 8 `kind:spec`, 7 `kind:feature-request`, 1
  `kind:chore`.
- `status:*` — 27 `status:backlog`, 1 `status:blocked` (issue #7; the
  remaining 5 have no `status:*` label, being pending-spec feature requests).
- `priority:*` — 1 `priority:medium` (thin coverage; do not read priority
  absence as "no priority").
- `area:*` — 1 `area:deps`, 1 `area:ci`.
- Also present: `effort:*` (23), `model:*` / `model-effort:*` (21 each),
  `triage:*` (15, e.g. `triage:approved`, `triage:needs-spec`,
  `triage:proposed-by-agent`).

Representative titles (full list of all 33 is in the raw `gh issue list`
output; pull it fresh per Resume steps below):

- #226 — Release det_bs/reco_bs predictor kwargs (5585d27) for downstream
  real-OCR consumers (`kind:feature-request`, `status:backlog`)
- #225–#221 — `hyphen-ngrams:` five-issue implementation cluster (extraction
  pipeline, download-on-first-use, JsonApiClient, SQLite schema,
  Protocol/dataclass) (`kind:feature`, `status:backlog`)
- #220–#216 — `scannos:` five-issue implementation cluster (promotion-flow
  tests, scan/promote API, JSON CandidateStore, SQLite RuleLibrary, dataclasses)
  (`kind:feature`, `status:backlog`)
- #215–#211 — `page-order:` five-issue implementation cluster (voting
  aggregation, visual-similarity signal, OCR page-number signal,
  filename-sequence signal, module skeleton) (`kind:feature`, `status:backlog`)
- #210, #209, #208 — companion specs for the three clusters above
  (`kind:spec`, `status:backlog`)
- #201 — chore(ci): add advisory static-testing scanner targets
  (`kind:chore`, `area:ci`)
- #191 — image validation accepts allowlisted extensions even when magic
  sniff fails; filed from the 2026-05-22 deep code/security review
  (`kind:feature-request`)
- #161 — make torch/DocTR an optional extra so consumers can import
  torch-free; blocks a torch-free FastAPI process in `pd-ocr-trainer-spa`
  (`kind:feature-request`, `area:deps`)
- #49–#45 — `kind:spec` companions to #2–#6 below, same titles prefixed
  "Spec:" (`triage:proposed-by-agent`)
- #7 — dev-local detector: doctr-from-git (fork-pin) signal (`kind:feature`,
  `status:blocked`)
- #6–#2 — layout heuristics backlog (multi-column body detection, drop-cap
  recognition, sidenote detection x2, decoration-vs-figure classification)
  (`kind:feature-request`, `triage:approved`, `triage:needs-spec`)

Read on the backlog: this is genuine, well-triaged pending work, not stale
noise. Every open issue carries a `kind:*` label and nearly all carry
`status:backlog` or `status:blocked`. Several form explicit spec-then-feature
pairs (e.g. #208 spec / #211–#215 page-order features; #45–#49 specs / #2–#6
feature requests) — the spec issue is meant to land before its paired feature
work starts. This backlog is worth carrying into `docs/roadmap.md` rather than
silently dropped.

## Decisions the next session must make

- **Scope.** Migrate the 33 OPEN issues (recommended). The 181 CLOSED issues
  are completed history; archiving and deleting those too is OPTIONAL — only
  do it for a full tracker wipe. Recommend focusing on OPEN unless a full wipe
  is explicitly wanted.
- **Roadmap-first is REQUIRED** here: the open issues are unfinished backlog
  (`status:backlog` / `status:blocked` / pending-spec feature requests).
  Never delete an issue without first carrying its content into
  `docs/roadmap.md`.

## The proven procedure

1. Pull every issue in scope, full:
   `gh issue view N --repo pdomain/pdomain-book-tools --json number,title,author,createdAt,closedAt,state,stateReason,labels,body,comments,url`
   Save each to a scratch dir and `sha256sum` the batch as a backup before
   touching anything else.
2. Author `docs/roadmap.md`, mirroring `../pdomain-ocr-cli/docs/roadmap.md`
   (frontmatter, Agent Index, Goal/Architecture/Tech Stack/Global Constraints,
   Work clusters, Now/Next/Later grouped by theme). Group the
   `hyphen-ngrams:`, `scannos:`, and `page-order:` five-issue clusters as
   single work-cluster entries rather than one roadmap line per issue. Tag
   every roadmap item with its originating `#NNN` so provenance survives.
3. Render one consolidated
   `docs/decisions/2026-07-17-closed-issues-archive.md` (adjust the date to
   the day you actually run this): docgraph frontmatter (`Kind: decision`,
   `Status: retired`) + Agent Index + Context/Decision/Consequences/
   Supersedes, then one `## #N — title` section per issue with a metadata
   line, labels, url, full body verbatim, and all comments verbatim. Add
   `<!-- markdownlint-disable -->` immediately after the frontmatter — issue
   bodies carry their own `##` headings and code fences that otherwise fail
   markdownlint.
4. Commit the roadmap and the archive together. Then `git rm` the archive in
   a SECOND commit whose message cites the add-commit SHA and the
   `git show <sha>:<path>` retrieval command. Git history is the tombstone
   (per `docs/README.md`'s convention) — the roadmap is what stays live and
   readable.
5. Only after the archive commit exists: `gh issue delete N --repo
   pdomain/pdomain-book-tools --yes` for each in-scope issue. This is
   PERMANENT with no undo — get an explicit human "go" before running any
   delete.

## Gotchas

- The `pre-commit-update` hook auto-bumps `.pre-commit-config.yaml` and
  aborts the commit. Revert it (`git checkout -- .pre-commit-config.yaml`)
  and commit with `SKIP=pre-commit-update git commit ...`; every other gate
  still runs normally.
- Validate docs before committing:
  `uv run pre-commit run markdownlint-cli2 --files <doc>` and the docgraph
  check MCP tool. An "orphan / no inbound links" advisory on the archive or
  handoff doc is acceptable and non-blocking.
- Preserve every word from each issue when archiving — roles may change
  (issue text becomes archive prose), but words may not disappear.
- The working tree has an untracked `tmp/` directory. Ignore it; never stage
  it as part of this work.

## Pointers

- `docs/roadmap.md` — migration target, to be created.
- `docs/decisions/` — archive target (currently empty but for `.gitkeep`).
- `DOCGRAPH.md` — repo docgraph conventions.
- `../pdomain-ocr-cli/docs/roadmap.md` — reference roadmap to mirror.
- `../pdomain-ocr-simple-gui/docs/roadmap.md` — reference roadmap-first
  example (37 issues).

## Reference worked examples

- `pdomain-ocr-cli`: closed-issues archive commit `9498407`, then a follow-up
  removal commit (local to that repo).
- `pdomain-ocr-simple-gui`: roadmap+archive commit `ec3979f`, then removal
  commit `7f3be6b` (local to that repo).
- Full repeatable steps are also saved in agent memory under
  `closed-issue-archive-pattern`.

## Resume steps

1. `gh issue list --repo pdomain/pdomain-book-tools --state open --limit 300 --json number,title,labels` — re-confirm the open count and label mix haven't drifted since 2026-07-17.
2. `mkdir -p /workspaces/pdomain/pdomain-book-tools/tmp/issue-migration-scratch` (or an equivalent scratch dir outside `docs/`) to hold the raw `gh issue view` pulls and their checksums.
3. Start pulling issues in scope: loop `gh issue view N --repo pdomain/pdomain-book-tools --json number,title,author,createdAt,closedAt,state,stateReason,labels,body,comments,url` over the 33 open issue numbers (or re-derive the current list from step 1) into that scratch dir, then `sha256sum` the batch.
