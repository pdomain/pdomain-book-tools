---
Status: active
Owner: maintainers
Created: 2026-08-08
Last verified: 2026-08-08
Kind: issue
Level: I1
---

# OCR entry points report no progress, so callers can only show a spinner

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-08-08
- **Resolution:** Open
- **Severity:** Medium — a caller cannot distinguish model load from inference, or working from stuck
- **Affected version:** `pdomain-book-tools` 0.21.0, tree at commit `8e90c8f`
- **Read when:** adding progress or staging output to the doctr OCR path, or responding to a consumer that needs to show OCR status.
- **Search terms:** progress callback, from_image_ocr_via_doctr, get_default_doctr_predictor, model load, loading screen, OCR staging, doctr predictor.
- **Relates to:** `pdomain-ocr-labeler-spa` `docs/specs/2026-08-08-page-load-progress-design.md`

## Summary

`Document.from_image_ocr_via_doctr` and the default predictor construction behind
`get_default_doctr_predictor` accept no progress callback. A caller running either one
has no way to tell a user which stage is in flight.

This surfaced in `pdomain-ocr-labeler-spa`, where opening a page can block for about 33
seconds with nothing on screen but a spinner. That consumer is speccing a loading screen
that names the current stage, and two of its five stages need information only this
library has.

## Impact

- A caller cannot distinguish model load from inference, or working from stuck.
- `pdomain-ocr-labeler-spa` blocks for about 33 seconds on page open with only a
  spinner on screen.
- Two of the five stages in that consumer's planned loading screen cannot be
  built at all, because only this library knows when they start and end.
- The one signal available today is doctr's root-logger output, so any consumer
  wanting progress has to scrape log lines.

## Environment / versions

```text
pdomain-book-tools 0.21.0, tree at commit 8e90c8f
consumer: pdomain-ocr-labeler-spa
device:   cuda:0 (NVIDIA GeForce RTX 3070 Ti Laptop GPU)
measured: 2026-08-07 and 2026-08-08
```

## Outcome / acceptance criteria

- A caller can observe stage transitions during model construction and during an OCR pass,
  without parsing log lines.
- The addition is optional. A caller that passes nothing sees today's behavior unchanged.
- The labeler can distinguish "loading the detection model" from "loading the recognition
  model" from "running OCR" while the work is happening.

## Evidence

`from_image_ocr_via_doctr` takes an image, a source identifier, an optional predictor, and
two rotation arguments. There is no callback parameter
(`pdomain_book_tools/ocr/document.py:174-181`). When `predictor` is `None` it calls
`get_default_doctr_predictor()`, which is where model loading happens, and that call
reports nothing either.

The only signal available today is doctr's own root-logger output, which the consumer sees
as lines like `Using downloaded & verified file: .../db_resnet50-79bd7d70.pt`. Scraping
those is not a contract either side should depend on.

Costs measured by the consumer on 2026-08-07 and 2026-08-08, on the machine
named under Environment / versions above:

```text
build the predictor                  26.22s   once per predictor-cache key
one page's OCR pass, predictor warm   3-17s   per page, per store miss
```

The predictor build is a load, not a download. Both weight files were already on
disk when that 26.22s was measured, at 102 MB for `db_resnet50` and 63 MB for
`crnn_vgg16_bn` under `~/.cache/doctr/models`. Importing torch accounted for
3.59s of it and initialising the CUDA context for 0.28s. The rest is
deserialising the weights, building the graph, and moving it to the device.

Warm per-page cost varies widely on identical inputs. Five consecutive uncached
pages measured 22.17s, 3.08s, 3.76s, 9.98s, and 9.91s, where the first includes
the predictor build. An earlier run on the same machine and book gave 30.18s,
17.06s, and 13.26s. The consumer did not chase the roughly threefold spread.
Treat these as orders of magnitude, not benchmarks.

Note for scoping: the consumer passes `auto_rotate=False`, so these numbers are a single
OCR pass and not the 90/180/270 rotation probes. Any progress contract should still account
for the multi-probe path, since `auto_rotate` defaults to `True` for other callers.

## Root-cause hypotheses

1. **(Most likely) The API predates any consumer that needed staged progress.**
   Both entry points were designed to return a finished result, so there is no
   seam to report from. This is a missing capability rather than a regression;
   nothing broke, the need is new.
2. **Model loading is hidden behind predictor construction.** The expensive
   steps happen inside `get_default_doctr_predictor()`, which
   `from_image_ocr_via_doctr` calls only when `predictor` is `None`. Even a
   callback on the outer function would not see those stages unless the hook is
   threaded through predictor construction too.

## Defects to fix

1. **`from_image_ocr_via_doctr` has no progress parameter.** Its signature takes
   an image, a source identifier, an optional predictor, and two rotation
   arguments, and nothing else. (Primary)
2. **`get_default_doctr_predictor` reports nothing during model load.** This is
   where the 26.22s predictor build is paid.
3. **Log scraping is the only current workaround**, and neither side should
   depend on doctr's root-logger format as a contract.

## Dependencies

None. This is additive and can land before the consumer's loading screen.

## Next steps

1. Decide the shape with the consumer: an optional callback argument, or structured events
   the caller subscribes to. This is the open question in the consumer's spec, and it sets
   how fine the stage granularity can be.
2. Identify the stage boundaries worth reporting. The consumer's ask is: weights resolved,
   detection model ready, recognition model ready, OCR pass starting, OCR pass complete.
3. Thread the hook through `from_image_ocr_via_doctr` and the default predictor path.

## Resolution

_Open._
