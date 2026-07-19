---
Status: built
Owner: CT
Created: 2026-07-19
Last verified: 2026-07-19
Kind: architecture
---

# DocTR checkpoint loading rejects unsafe object shapes by default

## Agent Index

- **Kind:** architecture
- **Status:** built
- **Read when:** loading finetuned DocTR checkpoints, changing the checkpoint
  loader, or evaluating checkpoint trust and validation.
- **Search terms:** checkpoint, torch.load, weights_only, state dict,
  get_finetuned_torch_doctr_predictor, trust boundary.

## The default loader accepts weights without general pickle objects

`get_finetuned_torch_doctr_predictor()` loads detection and recognition
checkpoints through an injected `torch_load` callable. Its default callable is
`functools.partial(torch.load, weights_only=True)`. The package requires a
PyTorch version that supports this explicit safe default.

Callers may inject another loader for testing or integration. The parameter is
keyword-only, so existing positional calls keep their meaning. An injected
loader crosses the default loading boundary and is responsible for its own
deserialization policy.

## Every loaded value must be a plain tensor state dict

Both checkpoint paths validate the loaded object before calling
`load_state_dict()`. The validator accepts a `dict` only when every value is a
`torch.Tensor`. It rejects non-dict objects and dictionaries with any
non-tensor value. An empty dictionary remains valid for unit tests and
fresh-model paths.

This structural check is defense in depth. It still applies when a caller
injects a loader that does not enforce `weights_only=True`.

## The remaining trust work is still open

These shipped checks do not limit checkpoint file size, verify a checksum, pin
default Hugging Face downloads to immutable revisions, or use `safetensors`.
They also do not establish that arbitrary local checkpoint paths are untrusted
input. The active [checkpoint-hardening issue](../issues/2026-05-22-gh-165-checkpoint-hardening.md)
tracks those unresolved decisions and safeguards.

## Evidence

- **Code:** `pdomain_book_tools/ocr/doctr_support.py` — keyword-only loader
  injection, the `weights_only=True` default, `_validate_state_dict()`, and
  validation in both model-loading paths.
- **Tests:** `tests/ocr/test_doctr_support.py` — default-loader, injected-loader,
  signature, accepted-state-dict, rejected-object, and rejected-value cases.
- **Commits:** `31137f1` added the safe default and injection boundary;
  `e5cf913` added state-dict validation.
- **Verified:** 2026-07-19 against the current code and focused tests.
