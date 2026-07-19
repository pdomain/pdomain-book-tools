---
Status: built
Owner: CT
Created: 2026-07-19
Last verified: 2026-07-19
Kind: architecture
---

# PP-DocLayout requires explicit trust for custom remote model repositories

## Agent Index

- **Kind:** architecture
- **Status:** built
- **Read when:** loading PP-DocLayout models, changing `checkpoint_path`,
  revisions, offline behavior, or remote-model trust policy.
- **Search terms:** PP-DocLayout, checkpoint_path, Hugging Face,
  trust_remote_checkpoint, local_files_only, model trust boundary.

## The built-in model source is pinned

`PPDocLayoutPlusLDetector` defaults to the repository
`CT2534/PP-DocLayout_plus-L` at revision
`32d3ea36944213ce46f157e9255852620e30eeca`. The adapter passes that revision
to both processor and model `from_pretrained()` calls.

The built-in source needs no trust flag. A caller-supplied `checkpoint_path`
does not inherit the built-in revision. Callers may pass their own `revision`;
otherwise a custom source is unpinned.

## Custom remote repositories require acknowledgment

The adapter classifies path-like values as local and other values as remote
Hugging Face repository IDs. A custom remote repository raises `ValueError`
unless the caller passes `trust_remote_checkpoint=True`. This flag records an
explicit trust decision; it does not validate the repository or its artifacts.

Local directories need no trust flag. Passing `local_files_only=True` forwards
that option to both `from_pretrained()` calls and prevents network access.
Local files remain caller-trusted input.

The adapter does not pass or enable `trust_remote_code`; it relies on the
installed Transformers default. That default reduces one remote-code path, but
model configuration, weights, artifact size, and inference resource use still
cross a trust boundary.

## Residual safeguards are not implemented

The adapter does not enforce a repository allowlist, require immutable
revisions for custom sources, cap artifact sizes, or verify checksums. It also
does not inspect a local directory for hostile or malformed model artifacts.
Applications that expose custom model selection must apply any stronger source,
size, integrity, and resource policies outside this adapter.

This boundary is distinct from the
[DocTR checkpoint-loading boundary](checkpoint-loading-trust-boundary.md).
DocTR loads caller-provided `.pt` state dictionaries through `torch.load` and
validates their object shape. PP-DocLayout delegates model and processor loading
to Hugging Face `from_pretrained()`.

## Evidence

- **Code:** `pdomain_book_tools/layout/adapters/pp_doclayout.py` — pinned
  defaults, local-path classification, remote opt-in, revision selection, and
  offline forwarding.
- **Tests:** `tests/layout/test_pp_doclayout.py` — local offline loading, remote
  rejection, remote opt-in, and built-in default behavior.
- **Commit:** `c5ca010`, merged in `bad42d3`.
- **Verified:** 2026-07-19 against the current adapter and tests.
