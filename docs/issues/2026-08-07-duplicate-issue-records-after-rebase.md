---
Status: active
Owner: CT
Created: 2026-08-07
Last verified: 2026-08-07
Kind: issue
Level: I1
---

# docs/issues/ carries two record sets that describe the same work twice

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-08-07
- **Resolution:** Open
- **Severity:** Medium — a reader can close one record and leave its twin open
- **Affected version:** pdomain-book-tools 0.21.x-dev @ 6b8e610
- **Read when:** filing a new issue report, closing one, or counting open work in this repo
- **Search terms:** duplicate issues, gh-NNN records, deep review issues, rebase, issue index
- **Relates to:** [issues index](./README.md),
  [continued-work plan](../plans/2026-07-21-continued-work-from-deep-review.md),
  [migration ledger](../context/github-issues-migration-ledger.md)

## Summary

`docs/issues/` now holds two independent record sets that cover overlapping
work. Twenty-four of the 43 migrated `gh-NNN` records describe the same six
work clusters as four open deep-review reports and two deferred plan items.

Two sessions built issue conventions in the same folder without seeing each
other, because local `master` had diverged from `origin/master` for three
weeks. The rebase on 2026-08-07 brought both sets into one tree.

Nothing was lost, and no record is wrong on its own. The risk is arithmetic:
the index reports 43 active records plus 19 open issues, which overstates the
real backlog. Closing one record also leaves its twin open.

## Impact

- Anyone counting open work in this repo counts the six overlapping clusters
  twice.
- Closing a `gh-NNN` record does not close its deep-review counterpart, or the
  reverse. A resolved problem can stay listed as open.
- A new report filed against one naming scheme will not surface when someone
  searches the other.

## Environment / versions

```text
pdomain-book-tools 0.21.x-dev
branch master @ 6b8e610 (10 commits ahead of origin/master 28c9e02)
docs/issues/: 72 files — 43 gh-NNN records, 27 deep-review reports, README, TEMPLATE
```

## Evidence

### 1. Both sets index from the same README

`docs/issues/README.md` lists 43 records under **Active issue files** and 19
under **Open issues**. The two lists share no filenames, so no tool reports a
collision.

### 2. Six clusters appear in both sets

Each row below names the same work twice. The plan item is the deep-review
side.

| Work | Migrated records | Deep-review side |
|---|---|---|
| Drop-cap heading cross-check | #5, #48 | `dropcap-iteration-c-heading-crosscheck` (F1) |
| Sidenote height-ratio default | #3, #46 | plan item F2 (no file) |
| Decoration vs figure post-classification | #2, #45 | plan item F3 (no file) |
| Page-order detection | #208, #211–#215 | `page-order-module-unbuilt` (G1) |
| Scannos module | #209, #216–#220 | `scannos-module-unbuilt` (G2) |
| Hyphen n-grams | #210, #221–#225 | `hyphen-ngrams-unbuilt` (G3) |

That is 24 migrated records against four issue files and two deferred plan
items.

### 3. The divergence explains the split

Local `master` and `origin/master` shared no commits after `a7bff12` on
2026-07-17. Origin ran the GitHub issue migration through PRs #234–#240 and
produced the `gh-NNN` records. Local ran the 2026-07-21 deep review and
produced the dated reports. Neither session could see the other's folder.

The handoff at `docs/handoff/2026-07-19-issue-tracker-migration.md` names only
PRs #234–#236, because it was written before the last four merged. Confirm the
full range against GitHub:

```text
gh pr view 240 --repo pdomain/pdomain-book-tools --json number,title,state,mergedAt
```

## Root-cause hypotheses

1. **(Most likely) Parallel work on an unpushed branch.** Ten local commits sat
   unpushed for three weeks while 86 landed on origin. Both efforts chose
   `docs/issues/` independently, which is the convention this repo documents.
   No further cause is needed to produce the duplication.
2. **Missing convention for migrated provenance.** The issues README defined
   one filename pattern, `YYYY-MM-DD-short-slug.md`. The migration added a
   second, `YYYY-MM-DD-gh-NNN-slug.md`, without recording how the two relate.
   This would have caused confusion even without the divergence.

## Defects to fix

1. **The index double-counts open work.** README reports 43 + 19 without
   stating that 24 of the 43 overlap. (Primary)
2. **No record links to its twin.** Neither set carries a cross-reference, so
   closing one gives no signal about the other.
3. **F2 and F3 have no issue file.** Their migrated counterparts (#3, #46, #2,
   #45) do, so the deferred plan items are the weaker record of the two.

## Next steps

1. Pick one record per cluster as authoritative. The `gh-NNN` records carry
   original issue provenance; the deep-review reports carry current evidence
   and plan mapping. Merging evidence into the `gh-NNN` record preserves both.
2. Retire the losing record of each pair through `doc-retirer`, citing its twin
   in `## Resolution`.
3. State the reconciled open count in the README once, and drop the
   "Two record sets live here" note when it no longer applies.
4. Cross-check the remaining 19 migrated records against the roadmap and the
   deep-review issues. Only the six clusters above were compared.

## What is NOT broken

- No record content was lost or altered by the rebase. Both sets are intact.
- No filename collides, and `docgraph check` reports no dangling link from the
  merged README.
- The eight resolved deep-review issues are correctly marked and are not part
  of this overlap.
- The migration itself is complete and verified. The ledger at
  `docs/context/github-issues-migration-ledger.md` and the journaled deletion
  commits on origin cover all 214 source issues.

## Resolution

*Open.* When this is fixed:

1. Set frontmatter and Agent Index `Status: retired`.
2. Add the resolving commit link here.
3. Move the README pointer to "Resolved".
4. Route the retirement through `doc-retirer`.
