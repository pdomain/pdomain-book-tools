---
Status: active
Owner: CT
Created: 2026-11-10
Last verified: 2026-11-11
Kind: issue
Level: I2
---

# Floated-caption split never fires on pages with normalized coordinates

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I2
- **Last verified:** 2026-11-11
- **Resolution:** Open — no real page proves the fix yet
- **Severity:** Medium — captions stay in the body text with no error
- **Affected version:** pdomain-book-tools master @ f1f0ecb
- **Read when:** changing floated-flow handling or coordinate thresholds in reorganize_page_utils
- **Search terms:** _split_caption_like_prefix, absorb_caption_tails_into_caption, page.width, coord_width, normalized, floated caption
- **Relates to:** [issue index](README.md)

## Summary

On a page with normalized coordinates, a caption at the top of a floated left flow is never split out. The two caption functions in `pdomain_book_tools/ocr/reorganize_page_utils.py` compare normalized distances with thresholds scaled by the page width in pixels. The neighboring detectors avoid this by computing a `coord_width` of `1.0` for normalized boxes. The branch tables for plan item B4 led to this finding.

## Impact

- DocTR ingress keeps normalized boxes and sets `Page.width` in pixels, so the code path applies to DocTR pages. This comes from reading the code and from the probe below. No real DocTR page has shown the fault yet. See evidence 4.
- A floated caption stays in the main paragraph instead of becoming a `sidenote` block with the label `margin left`.
- Nothing warns the caller. The words are kept, so the dropped-word checks pass.

## Environment / versions

```text
pdomain-book-tools master @ f1f0ecb
Found 2026-11-10 on branch fix/roadmap-no-owner-items, on CPU
```

## Evidence

### 1. The same geometry splits in pixels and does not split when normalized

Five one-word lines were passed to `_split_caption_like_prefix` with `page_width=1000`. Each spans x 200 to 500 and is 20 high. Their tops are 100, 125, 200, 225, and 250. The normalized run divides every coordinate by 1000 and sets `is_normalized=True`. The `_flow` helper in `tests/ocr/test_reorganize_branch_tables.py` builds the same pixel lines.

```text
pixel prefix lines: 2 rest lines: 3
normalized prefix lines: 0 rest lines: 5
```

### 2. The thresholds use the pixel width

`_split_caption_like_prefix` sets `coord_width = float(page_width)`. Its gap threshold is `max(1.8 * avg_h, 0.008 * coord_width)`, which is 8 on a 1000-wide page. No gap between normalized boxes can exceed 8, so the function always returns an empty prefix. Its left-alignment test, `np_std(prefix_xs) > 0.035 * coord_width`, is scaled the same way and would accept any prefix.

`absorb_caption_tails_into_caption` has the same fault. It uses `0.30 * page.width` for the horizontal distance to the caption, and `0.04 * page.width` and `0.07 * page.width` for the alignment of lines below. On a normalized page those three tests always pass, with two opposite effects. Any line near the caption band counts as horizontally close, so too many tails join the caption. Any two lines below count as aligned, so a real tail can look like justified text and stay in the flow. The fallback `[page.width]` for `block_median_w` is in pixels too.

This second fault stays hidden for now. The function runs only after a prefix is found, so the fault cannot show until the first one is fixed.

### 3. The neighboring detectors handle both coordinate systems

`_detect_column_split`, `_detect_mixed_column_split`, and `_detect_floated_flow_span` all set `coord_width = 1.0 if bbox_max_x <= 2.0 else float(page_width)`.

### 4. No real DocTR page reaches a caption prefix, in pixels or normalized

**A search of 154 real DocTR pages on 2026-11-10 found none where correct scaling would split a caption, so no regression fixture exists yet.** The check wrapped `_split_caption_like_prefix` in memory and compared the current result with the result using a width of `1.0`.

| Source | Pages | `_detect_floated_flow_span` fired | Split would find a prefix |
|---|---|---|---|
| Layout regression corpus, three `reorganize_page` modes | 31 | 0 of 84 calls, without a layout | 0 |
| PGDP page images, DocTR run on CPU | 123 | 6 pages | 0 of 6 |

The scan covered 123 of 702 candidate pages. Claude Code stopped it when the machine ran low on memory, so 579 candidates were not run. Candidates were pages whose F2 text has an `[Illustration: ...]` of at least 8 characters and at least 14 lines longer than 20 characters, at most 8 per book.

The six flows are `projectID68da24895dde5/b026`, `projectID638209f0dd6c0/563`, `projectID68a86e26d4714/068`, `projectID69027d8333570/276`, `projectID68e337f925d55/002`, and `projectID69c2fb9ce6d62/p009`. Each has no compact prefix followed by a clear gap, so the fix leaves all six unchanged.

## Root-cause hypotheses

1. **(Most likely) These two functions were not covered by the coordinate-domain threshold work in plan item A1.** This comes from reading the code. No commit history was checked to show whether it was deliberate. Coverage before B4 shows `tests/ocr` never ran the body of `_split_caption_like_prefix`.

## Defects to fix

1. `_split_caption_like_prefix`: scale its gap and left-alignment thresholds to the coordinate system of the line boxes.
2. `absorb_caption_tails_into_caption`: do the same for its three distance tests and the `block_median_w` fallback.

## Next steps

1. Write failing tests that run the caption-prefix and caption-tail cases in `tests/ocr/test_reorganize_branch_tables.py` in normalized coordinates, including the misaligned-prefix, too-far-across, and justified-text cases.
2. Fix both functions together. Compute the width the way the neighboring detectors do, with `coord_width = 1.0 if bbox_max_x <= 2.0 else float(page_width)`, or use `_coord_dims_for_block`, which prefers the `is_normalized` flag.
3. Check the layout regression fixtures for changed output.

This was left unfixed on purpose. The fix changes the output for normalized pages, and evidence 4 found no real page to check it against. A proving fixture is a real DocTR page whose floated left flow starts with at least 2 lines, followed by a gap larger than `max(1.8 * avg_h, 0.008)`. Scanning the remaining 579 candidates needs free memory. Printed figure captions usually sit under the figure, so such a page may be rare, and the owner may prefer to accept a synthetic fixture.

## What is NOT broken

- Pixel pages split captions correctly. `tests/ocr/test_reorganize_branch_tables.py` covers that path.
- `_detect_floated_flow_span` finds floated flows in both coordinate systems.
- No words are lost. The caption lines stay in the main block.

## Resolution

*Open.*
