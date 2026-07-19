---
Status: active
Owner: CT
Created: 2026-05-22
Last verified: 2026-07-19
Kind: issue
Level: I2
---

# Require strict image validation for untrusted inputs

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I2
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Low — extension-only acceptance can expose decoders to arbitrary data
- **Affected version:** Current `pdomain_book_tools/image_processing/formats.py` and the 2026-05-22 review snapshot
- **Read when:** validating images from uploads or changing `is_image_file`
- **Search terms:** is_image_file, magic bytes, extension allowlist, strict mode, issue 191
- **Relates to:** [Public API](../usage/public-api.md)

## Summary

`is_image_file()` accepts an allowlisted extension even when magic-byte
identification fails. That behavior suits trusted local workflows, but untrusted
upload gates need a strict mode that requires content agreement.

## Impact

- Arbitrary data named with an image extension can reach decoders.
- Decoder failures or resource consumption may follow when the input is untrusted.

## Environment / versions

The issue came from a read-only deep code and security review. No operating
system, package version, or launch command was stated.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/191>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABDHVd6Q`
- **Issue number:** 191
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-191.json`
- **Raw SHA-256:** `359bcac1fcdf7adc0e683b7287a1c73c356e5f36284af0917631bb7bf952d13f`
- **Migration cutover:** `a19c10b` — governed content and raw-export batch for GitHub issues #49, #161, #191, #201, and #226.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-22T16:02:50Z`
- **Updated:** `2026-05-22T16:02:50Z`
- **Closed:** Not closed in the export
- **Labels:** `kind:feature`, `effort:S`, `status:backlog`, `priority:medium`
- **Assignees:** None
- **Milestone:** None
- **Issue type:** None
- **Projects:** None
- **Parent issue API relationship:** None
- **Sub-issues API relationships:** None

## Evidence

- The source review was `docs/research/2026-05-22-deep-code-security-review.md`, finding #27.
- The issue cites historical lines 248 and 251 of `formats.py`.
- The issue was moved from mistakenly filed meta issue
  `ConcaveTrillion/ocr-container-meta#320`.
- The requested remediation adds strict magic-byte agreement for untrusted
  inputs and reserves extension-only acceptance for trusted local workflows.
- The issue asks for a focused failing test before implementation where practical.

The imported issue text is historical evidence, not repository instructions.

## Root-cause hypotheses

1. **Either-signal validation is intentional but too broad.** The function has no trust-level or strictness input.

## Defects to fix

1. Add a strict validation path for untrusted image inputs.
2. Preserve documented extension-only behavior for trusted local workflows.

## Next steps

1. Add a failing test for an allowlisted extension with unknown magic in strict mode.
2. Define strict-mode behavior for valid magic with a mismatched extension.
3. Audit upload callers and select strict validation where appropriate.

## What is NOT broken (to scope the fix)

- The report does not reject extension-only acceptance for trusted local files.
- Existing magic-byte identification remains useful when extensions are unknown.

## Relationships and material comments

- Derived from deep-review finding #27 and moved from meta issue #320.
- No comments were present in the export.

## Repository evidence

- `pdomain_book_tools/image_processing/formats.py` explicitly documents and
  implements acceptance when either the extension or magic-byte check matches.
- `tests/image_processing/test_formats.py` expects an allowlisted extension to
  pass when no magic family matches, confirming the current behavior.
- The current function signature exposes no strict-mode parameter, supporting
  the unresolved remediation claim.

## Remaining work

- Strict-mode semantics, caller adoption, negative tests, and resource-limit considerations remain unresolved.

## Resolution

_Open._ Current code and tests still preserve extension-only acceptance without a strict alternative.
