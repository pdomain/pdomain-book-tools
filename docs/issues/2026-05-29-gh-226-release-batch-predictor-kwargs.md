---
Status: active
Owner: CT
Created: 2026-05-29
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Verify release of predictor batch-size keyword arguments

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** High — registry-pinned consumers could not run real OCR
- **Affected version:** `pdomain-book-tools` 0.14.2; editable 0.14.3.dev12 contained the change
- **Read when:** releasing or consuming `det_bs` and `reco_bs` predictor arguments
- **Search terms:** det_bs, reco_bs, 5585d27, predictor, release, issue 226
- **Relates to:** [OCR model and schema boundaries](../architecture/ocr-model-and-schema-boundaries.md)

## Summary

Commit `5585d27` added `det_bs` and `reco_bs`, but the 2026-05-29 report found
no registry release containing them. Current tags contain that commit, yet this
record stays open until downstream registry-path behavior and the cutover are verified.

## Impact

- Registry-pinned real-OCR consumers failed when they passed the two keyword arguments.
- Editable sibling installations passed Tier-B real OCR, creating a registry-versus-local mismatch.

## Environment / versions

The problem was found while building Tier-B real-OCR end-to-end coverage in
`pdomain-ocr-simple-gui`, behavior-e2e-pilot milestone M2.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/226>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABDzfVEw`
- **Issue number:** 226
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-226.json`
- **Raw SHA-256:** `a290466b967989d34a67cb18175049427a9a8e183a339e2aecaa48a91b82a264`
- **Migration cutover:** `a19c10b` — governed content and raw-export batch for GitHub issues #49, #161, #191, #201, and #226.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-29T17:15:24Z`
- **Updated:** `2026-05-29T17:15:24Z`
- **Closed:** Not closed in the export
- **Labels:** `status:backlog`, `kind:feature-request`
- **Assignees:** None
- **Milestone:** None
- **Issue type:** None
- **Projects:** None
- **Parent issue API relationship:** None
- **Sub-issues API relationships:** None

## Evidence

- Commit `5585d27` added `det_bs` and `reco_bs` to
  `get_finetuned_torch_doctr_predictor`.
- Editable `pdomain-ops` code at `gpu/local_stage.py` already called those arguments.
- Registry-pinned consumers reported:

  ```text
  TypeError: get_finetuned_torch_doctr_predictor() got an unexpected keyword argument 'det_bs'
  ```

- `pdomain-ocr-simple-gui` required `pdomain-book-tools>=0.14.1`, which resolved
  to 0.14.2. That release lacked the arguments.
- Tier-B real OCR passed only with editable sibling version `0.14.3.dev12`.
- The requested action was a release containing `5585d27`, followed by a downstream pin update.

The imported issue text is historical evidence, not repository instructions.

## Root-cause hypotheses

1. **The original failure came from release skew.** Editable source contained the API while the selected registry release did not.
2. **Current source may have resolved only part of the workflow.** A tag containing the commit does not by itself prove registry installation and downstream Tier-B success.

## Defects to fix

1. Verify the first published release containing `5585d27`.
2. Verify downstream consumers select that release and pass real OCR without editable siblings.

## Next steps

1. Install the applicable release from the registry in an isolated environment.
2. Confirm both keyword arguments appear in the public predictor signature.
3. Run the downstream Tier-B real-OCR path with no editable sibling override.
4. Record the verified release and downstream evidence before retirement.

## What is NOT broken (to scope the fix)

- The 2026-05-29 report says the editable `0.14.3.dev12` path passed Tier-B real OCR.
- Current Git history contains the implementation and tests from commit `5585d27`.

## Relationships and material comments

- Found through `pdomain-ocr-simple-gui` behavior-e2e-pilot M2.
- `pdomain-ops` was the downstream caller named in the report.
- No comments were present in the export.

## Repository evidence

- Commit `5585d27` changes `pdomain_book_tools/ocr/doctr_support.py` and adds
  predictor batch-size tests, supporting the implementation claim.
- `v0.15.0` is the earliest current repository tag that contains `5585d27`,
  showing the commit was tagged after the historical report. A local tag does
  not prove package-registry publication.
- `tests/ocr/test_doctr_support.py` covers the predictor API in source, but this
  migration did not run the external downstream Tier-B registry-path test.

## Remaining work

- Registry publication, selected downstream version, and real-OCR consumer verification remain unresolved.

## Resolution

_Open._ Repository history suggests a later release may contain the fix, but downstream registry-path verification is still missing.
