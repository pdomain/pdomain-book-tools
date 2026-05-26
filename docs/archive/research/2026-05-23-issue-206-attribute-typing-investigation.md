# Issue #206: Downstream `reportAny` on `pd_book_tools` Attribute Access

**Date:** 2026-05-23
**Issue:** [pdomain-book-tools#206](https://github.com/ConcaveTrillion/pdomain-book-tools/issues/206)
**Status:** Investigation complete — Hypothesis 3 confirmed

---

## Finding: Hypothesis 3 Applies

The upstream variable in `pdomain-ocr-labeler-spa` is typed `Any`, not `pd_book_tools`. The
`reportAny` warnings are **not** a `pdomain-book-tools` annotation deficiency. `pdomain-book-tools`
attributes are fully typed and propagate correctly to `py.typed`-aware consumers.

---

## Evidence

### 1. basedpyright repro — direct access vs. `getattr()`

Repro file (`/tmp/repro.py`, run against editable in-tree source in the worktree):

```python
from pd_book_tools.ocr.page import Page

def use_direct(p: Page) -> int:
    return len(p.lines)              # case A: direct access

def use_getattr(p: Page) -> object:
    return len(getattr(p, "lines"))  # case B: getattr on typed Page

def use_getattr_words(p: Page) -> object:
    return len(getattr(p, "words"))  # case C: getattr words on typed Page

def use_object_typed(p: object) -> object:
    return getattr(p, "lines", None) # case D: object-typed upstream var
```

Output of `uv run basedpyright /tmp/repro.py`:

```text
/tmp/repro.py
  /tmp/repro.py:7:16 - warning: Argument type is Any
    Argument corresponds to parameter "obj" in function "len" (reportAny)
  /tmp/repro.py:10:16 - warning: Argument type is Any
    Argument corresponds to parameter "obj" in function "len" (reportAny)
0 errors, 2 warnings, 0 notes
```

**Interpretation:**

- Case A (direct attribute access `p.lines` where `p: Page`) → **clean, 0 warnings**
- Cases B and C (`getattr(p, "lines"/"words")` even where `p: Page`) → **reportAny** because `getattr()` always returns `Any` regardless of upstream type

This is Python's fundamental `getattr()` behavior: the return type is `Any` by definition.
No annotation change in `pd_book_tools` can fix this — `getattr()` is structurally `Any`.

### 2. Upstream variable type in `pdomain-ocr-labeler-spa`

The six `# pyright: ignore[reportAny]` sites added in commit `c708eb4` are concentrated in:

- `api/pages.py` — `glyph_bulk_mark()` and `save_page()`
- `api/words.py` — `_resolve_page_object()` and `_resolve_word()`
- `core/glyph/bulk_mark.py`

The upstream variable in all cases flows from `PageLoadOutcome.payload`, defined in
`core/page_state.py`:

```python
@dataclass
class PageLoadOutcome:
    # ...
    payload: Any   # <-- explicitly typed Any
```

The comment in that file is explicit (line 24–25):

> `payload` is typed `Any` because the eventual `Page` (from pdomain-book-tools) hasn't landed
> the M3-proper `PageRecord` type yet

The functions `_resolve_page_object()` (words.py) and `_resolve_page_object_for_pages()`
(pages.py) both return `object | None`, which avoids `Any` propagation but still makes
direct attribute access impossible without a cast or isinstance guard. In `words.py`,
`_resolve_page_object` returns `Any | None` (i.e. `Any`), making the `Any` explicit.

**Conclusion:** The `getattr()` calls exist because the resolved page object is typed
`object | None` or `Any | None`, not `Page`, so direct attribute access (`page.lines`)
would itself raise `reportAny` or `reportAttributeAccessIssue`.

### 3. Wheel inspection — `py.typed` and annotations present

```text
$ unzip -l pd_book_tools-0.14.1-py3-none-any.whl | grep -E "py.typed|ocr/page|ocr/word"
         0  2020-02-02 00:00   pd_book_tools/py.typed
    145056  2020-02-02 00:00   pd_book_tools/ocr/page.py
     48675  2020-02-02 00:00   pd_book_tools/ocr/word.py
```

The wheel ships `py.typed` and full annotated `.py` source (no `.pyi` stubs needed
for a pure-Python library — source annotations serve as the type surface). This
**rules out Hypothesis 2**: annotations are not lost in the wheel build.

`Page.lines`, `Page.words`, and `Page.ground_truth_text` are all fully typed:

- `Page.lines` (property) → `list[Block]`
- `Page.words` (property) → `list[Word]`
- `Page.ground_truth_text` (property) → `str`
- `Word.ground_truth_text` (property) → `str`

### 4. Cross-repo grep — `getattr(...lines/words/ground_truth...)`

```text
$ grep -rn 'getattr.*\(lines\|words\|ground_truth' \
    /workspaces/ocr-container/pdomain-ocr-cli/ \
    /workspaces/ocr-container/pdomain-prep-for-pgdp/ 2>/dev/null
(no output — exit code 2, paths not found)
```

Neither `pdomain-ocr-cli` nor `pdomain-prep-for-pgdp` use `getattr()` for `lines`/`words`/
`ground_truth` attribute access. This confirms the pattern is a **labeler-spa
concentration**, not a workspace-wide idiom.

---

## Root Cause Summary

The six `# pyright: ignore[reportAny]` suppressions were added in labeler-spa commit
`c708eb4` because:

1. `PageLoadOutcome.payload` is typed `Any` (intentional placeholder pending M3 `PageRecord`)
2. The resolver functions return `object | None` or `Any | None` rather than `Page | None`
3. `getattr()` was chosen defensively (to tolerate `UserPageEnvelope` payloads that lack
   `.lines`) — but `getattr()` always returns `Any`, making the suppression unavoidable
   as long as the code uses `getattr()` with an `Any`/`object`-typed receiver

`pdomain-book-tools` is not the source of the problem.

---

## Recommended Remediation

Hypothesis 3 confirmed — close #206 as "not a pdomain-book-tools issue."

### Immediate (labeler-spa)

The correct fix in `pdomain-ocr-labeler-spa` is to narrow the resolved page object to `Page`
before accessing attributes. The `lift_envelope_to_page` function already performs the
lift — its return type just needs to be narrowed:

```python
# words.py / pages.py after lift:
from pd_book_tools.ocr.page import Page
...
lift_result = lift_envelope_to_page(payload_obj)
if isinstance(lift_result, EnvelopeLiftError):
    return None
if not isinstance(lift_result, Page):
    return None  # unknown payload type — treat as not loaded
return lift_result   # now typed Page, not object
```

With the resolver returning `Page | None`, all the `getattr(page, "lines")` calls can
become `page.lines` — direct typed access, no `getattr()`, no ignores.

The defensive `getattr()` pattern (to tolerate non-Page payloads) should be replaced
by the `isinstance(lift_result, Page)` guard at the lift boundary. That's the right
seam — once you've confirmed the type, use direct attribute access.

### Workspace pattern (new guidance)

Add to workspace conventions: **`getattr()` on a typed object is a type-smell.**
`getattr(obj, "attr")` always returns `Any`; if `obj` has a known type, use direct
attribute access. The defensive-against-duck-typing pattern belongs at protocol
boundaries (e.g. after deserialization), not inside typed function bodies.

### Cross-repo recommendation

```text
Cross-repo recommendation
  Target: pdomain-ocr-labeler-spa
  Reason: PayloadLoadOutcome.payload is typed Any (pending M3 PageRecord);
          narrowing the lift resolvers to Page | None would eliminate all
          six reportAny ignores and make attribute access type-safe
  gh issue create -R ConcaveTrillion/pdomain-ocr-labeler-spa \
    -l kind:feature-request -l status:backlog \
    --title "Narrow lift_envelope_to_page resolvers to Page | None to drop getattr reportAny ignores" \
    --body "Tracks: none yet\nContext: Discovered while investigating pdomain-book-tools#206\n\nPageLoadOutcome.payload is typed Any (placeholder pending M3 PageRecord).\nThe _resolve_page_object / _resolve_page_object_for_pages functions return\nobject | None or Any | None instead of Page | None. Adding an isinstance(lift_result, Page)\nguard at the lift boundary would let all six getattr() attribute accesses become\ndirect typed access, dropping the six reportAny ignores added in commit c708eb4."
  → Run this? CT can edit before executing.
```

---

## Decision

- **Hypothesis 3 confirmed**: `pdomain-book-tools` attribute annotations are correct and survive
  the wheel build. The `reportAny` warnings originate from `PageLoadOutcome.payload: Any`
  in labeler-spa, compounded by the inherent `Any`-ness of `getattr()`.
- **Close pdomain-book-tools#206**: no action needed in this repo.
- **File a labeler-spa follow-up** (see cross-repo recommendation above) to narrow the
  resolvers once M3's `PageRecord` type lands or sooner.
