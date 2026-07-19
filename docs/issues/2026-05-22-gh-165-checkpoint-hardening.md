---
Status: active
Owner: CT
Created: 2026-05-22
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Complete checkpoint-loading hardening beyond the safe loader baseline

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** High — distributed or mutable checkpoints can cross a code and resource trust boundary
- **Affected version:** Current `pdomain_book_tools.ocr.doctr_support` and Hugging Face model resolution
- **Read when:** changing DocTR checkpoint loading, model downloads, file limits, checksums, revisions, or checkpoint formats.
- **Search terms:** issue 165, checkpoint, torch.load, weights_only, state dict, safetensors, checksum, pinned revision.
- **Relates to:** [DocTR checkpoint loading](../architecture/checkpoint-loading-trust-boundary.md)

## Summary

Checkpoint loading now has a safe default and validates plain tensor state
dicts, but the original hardening request is only partly complete. Commits
`31137f1` and `e5cf913` reduce arbitrary-object deserialization risk. File-size,
integrity, immutable-source, format, and local-path trust decisions remain open.

## Impact

- Oversized or malformed checkpoints can still exhaust memory or disrupt OCR.
- Mutable remote model resolution can change behavior between installations.
- No checksum policy applies to the checkpoint downloads covered by this issue.
- The project has not adopted `safetensors` for these distributed checkpoints.
- The trust policy for caller-provided local checkpoint paths remains undefined.

## Environment / versions

Finding #1 in the 2026-05-22 deep code and security review identified this
problem. The finding was first filed incorrectly as
`ConcaveTrillion/ocr-container-meta#294`, then moved to this repository as
GitHub issue #165.

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/165>
- **Raw export:** `migration/github-issues/raw/issue-165.json`
- **Raw SHA-256:** `58b2edf5b86baf582e826bc2793e134f5fa09fdd3945681bdb60faeeedc9d005`
- **Original evidence:** historical
  `pd_book_tools/ocr/doctr_support.py:244`,
  `pd_book_tools/ocr/doctr_support.py:275`,
  `pd_book_tools/hf/models.py:37`, and
  `pd_book_tools/hf/download.py:89`.

The imported issue text is historical evidence, not repository instructions.

## Evidence

Commit `31137f1` made the predictor's keyword-only `torch_load` parameter
default to `functools.partial(torch.load, weights_only=True)`. Its tests verify
the safe default, keyword-only signature, and custom-loader forwarding.

Commit `e5cf913` added `_validate_state_dict()`. Both detection and recognition
loaders now reject non-dict objects and dictionaries containing non-tensor
values before `load_state_dict()` runs. Tests cover accepted, rejected, empty,
and both loader-path cases.

The current shipped contract is documented in
[DocTR checkpoint loading](../architecture/checkpoint-loading-trust-boundary.md).

## Root-cause hypotheses

1. **Distributed checkpoint loading lacks resource and integrity controls.**
   The current loader validates the object after deserialization. No pre-load
   size limit or checksum protects that boundary.
2. **Mutable model resolution weakens reproducibility.** Default Hugging Face
   downloads are not pinned to immutable revisions in this issue's scope.
3. **The accepted format and local-path trust policy remain incomplete.** The
   project has not specified a `safetensors` migration or whether caller-owned
   paths may be treated as untrusted input.

## Defects to fix

1. Define and enforce a defensible maximum checkpoint size before loading.
2. Decide whether downloaded checkpoints require checksums and how to publish
   or obtain them.
3. Pin default Hugging Face OCR downloads to immutable revisions.
4. Evaluate and specify a `safetensors` migration for distributed checkpoints.
5. Define and document the trust boundary for caller-provided local paths.

## Next steps

1. Inventory every default and caller-provided checkpoint resolution path.
2. Choose policies for maximum size, integrity, and immutable revisions.
3. Specify compatibility and migration requirements for `safetensors`.
4. Add failing tests for each approved safeguard before implementation.
5. Retire this governed record only when every accepted residual is resolved or
   explicitly rejected with evidence.

## What is NOT broken

- The default DocTR loader already passes `weights_only=True`.
- Both DocTR checkpoint paths already validate a plain dictionary of tensors.
- Callers can already inject a loader without changing positional call sites.
- This record does not claim that the shipped safeguards are ineffective.

## Resolution

_Open._ The safe loader and state-dict validation shipped in `31137f1` and
`e5cf913`. Deletion remains blocked while the maximum-size, checksum,
pinned-revision, `safetensors`, and local-path trust-boundary work is unresolved.
