---
Status: active
Owner: CT
Created: 2026-09-18
Last verified: 2026-09-18
Kind: issue
Level: I1
---

# Merging two words clears every word's ground truth in the line

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-09-18
- **Resolution:** Open
- **Severity:** High. A caller merging two words loses the ground-truth text of
  every other word in that line, with no warning and no way to recover it.
- **Affected version:** `9dc73cf`
- **Read when:** touching `Block.merge_adjacent_words`, `merge_word_left`,
  `merge_word_right`, or `split_word_at_fraction`.
- **Search terms:** merge_adjacent_words, merge_word_left, merge_word_right,
  ground_truth_text cleared, word merge data loss.

## What happens

`Block.merge_adjacent_words` in `pdomain_book_tools/ocr/block.py` merges the two
words as asked, then runs:

```python
for word in self.words:
    word.ground_truth_text = ""
```

That loop touches every word in the line, not the merged pair. A line of ten
words where somebody merges words 3 and 4 loses the transcribed ground truth of
all nine surviving words.

`merge_word_left` and `merge_word_right` both delegate here, so both carry it.

## Why this looks deliberate, and why it is still wrong

`split_word_at_fraction`'s docstring says plainly that it "clears ground-truth
text for all words in the line after the split", so the pattern is intentional
somewhere. The rationale holds for a split: one word becomes two, and which part
of the old ground truth belongs to which half is genuinely ambiguous.

It does not hold for a merge. The merged word's ground truth is the
concatenation of the two, which `Word.merge` already produces. No other word in
the line changes position, text or box. Clearing them discards work that the
merge did not invalidate.

`merge_adjacent_words` also has no docstring line warning about this, unlike the
split, so a caller reading the signature has no way to know.

## How it was found

On 2026-09-18, while building word merge in `pdomain-ocr-labeler-spa`. That
repository's right-panel "merge with previous/next" buttons call these helpers
and are live today, so the loss is reachable by a real person in a shipped
product. The new toolbar merge route was built on `Word.merge` directly to avoid
this, and both of that repository's merge routes now share that path. See its
`docs/context/decisions.md`, the 2026-09-18 entry "Retired: word merge had
nowhere to live".

That repository no longer depends on the behaviour, so nothing here is urgent
for it. Any other caller of these three helpers still is affected.

## What to decide

1. **Clear only the merged word's neighbours if anything at all.** The narrow
   reading: `Word.merge` already produces the concatenated ground truth, so
   clear nothing. This is what the labeler now does and it loses no data.
2. **Keep the clear but scope it to the merged word**, if the concatenated
   ground truth is considered untrustworthy after a structural edit.
3. **Keep the current behaviour and document it**, if some caller depends on a
   line-wide reset. Then `merge_adjacent_words` needs the same explicit docstring
   warning `split_word_at_fraction` carries, because today it is silent.

Option 1 is the recommendation. A merge is the one structural edit whose ground
truth is unambiguous.

## What is NOT broken

The merge itself is correct: the right two words combine, the survivor keeps the
merged text and box, and the removed word leaves the line. `Word.merge` is
sound. This is only about the loop that runs afterwards.
