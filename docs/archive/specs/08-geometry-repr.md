# Geometry Types `__repr__` Contract

> **Status**: Shipped — archived 2026-05-22
> **Last updated**: 2026-05-22
> **Spec-Issue**: ConcaveTrillion/pd-book-tools#36 (closed)

## TL;DR

Add a self-evaluating `__repr__` to `BoundingBox` and a consistent
`__repr__` to `Point`, so that pytest assertion diffs show readable
coordinate values instead of `<BoundingBox object at 0x...>`.

## Context

`BoundingBox` is a `@dataclass` holding two `Point` corners
(`top_left`, `bottom_right`) and an optional `is_normalized` flag.
`Point` is a hand-written class backed by a Shapely `Point`. Neither
class currently defines `__repr__`, so the inherited repr is a useless
memory address when debugging layout-regression failures.

The feature request (#35) was filed after pytest assertion diffs became
opaque in the `04-layout-regression-fixtures` test suite.

## Constraints

- `BoundingBox` uses `@dataclass` — Python already auto-generates a
  `__repr__` for dataclasses, but it exposes the internal `Point`
  objects rather than the four scalars callers work with (minX, minY,
  maxX, maxY). The auto-generated repr reads
  `BoundingBox(top_left=Point(...), bottom_right=Point(...), is_normalized=None)`
  which is long and requires knowing the internal model.
- The repr must be safe to read in test output on 80-character terminals.
- `eval(repr(x)) == x` is desirable but not mandatory; the priority is
  readability over round-trippability.
- Do NOT break existing tests that rely on the current repr (check
  `tests/` for `repr(` usages first; none are expected).

## Decision

1. **`BoundingBox.__repr__`**: return an eval-safe form using the
   existing `from_ltrb` helper constructor:

   ```text
   BoundingBox.from_ltrb(x0, y0, x1, y1)
   ```

   where `x0 = minX`, `y0 = minY`, `x1 = maxX`, `y1 = maxY`.
   Override the dataclass default by defining `__repr__` explicitly.
   `eval(repr(bb)) == bb` holds (modulo `is_normalized` — see open
   question below). `is_normalized` is omitted from the repr to keep
   the output compact; `from_ltrb` defaults it to `None` which matches
   the common case.

2. **`Point.__repr__`**: return:

   ```text
   Point(x, y)
   ```

   Simple positional form. `is_normalized` omitted for the same reason.

3. No other geometry types (`image_ops.py`) need `__repr__` changes in
   this slice — they are not primitive value types.

4. The repr uses `from_ltrb` rather than the primary constructor
   (`BoundingBox(top_left, bottom_right)`) because `from_ltrb` accepts
   the four scalar values that callers actually work with at debug
   time. This keeps `eval(repr(bb))` a single, readable expression.

## Contract / Acceptance

- `repr(BoundingBox(Point(0, 0), Point(10, 10)))` returns
  `"BoundingBox.from_ltrb(0, 0, 10, 10)"`.
- `eval(repr(bb)) == bb` for any `bb` constructed without
  `is_normalized` (default None case).
- `repr(Point(3, 7))` returns `"Point(3, 7)"`.
- `repr(Point(0.5, 0.5))` returns `"Point(0.5, 0.5)"`.
- Unit tests in `tests/test_geometry_repr.py` assert all four forms.
- No existing tests break (run `uv run pytest tests/ -x` before filing the PR).

## Trade-offs considered

| Option | Pro | Con |
|---|---|---|
| Let `@dataclass` auto-repr (current) | Zero code | Exposes internals; verbose |
| `BoundingBox.from_ltrb(x0, y0, x1, y1)` form | Eval-clean; matches existing constructor helper; readable | Slightly longer than bare `BoundingBox(...)` |
| Bare positional `BoundingBox(x0, y0, x1, y1)` | Most compact | Misleading — primary constructor doesn't accept four scalars; can't be eval'd |
| Named-arg form `BoundingBox(x0=0, y0=0, x1=10, y1=10)` | Self-documenting | Long (40+ chars per box); terminal wrap risk |
| Add `__repr__` to all geometry types | Consistency | Out-of-scope for a one-chore slice |

Decision: `from_ltrb` form for `BoundingBox` (eval-clean) + positional form for `Point` (its primary constructor already accepts two scalars); other geometry types left for a follow-on chore.

## Consequences

- Pytest diffs become immediately readable for layout-regression failures.
- Any snapshot tests that captured the old `<BoundingBox object at ...>` form
  must be updated (expected: none in the current test suite).
- `Point.__repr__` change may surface differences in any downstream
  tool that relied on implicit string conversion (check `pd-ocr-cli`,
  `pd-ocr-labeler`).

## Open questions

- Should `BoundingBox.__repr__` include `is_normalized` when it is not
  `None`? Decision deferred: omit for now; revisit if callers ask for it.

## References

- `pd_book_tools/geometry/bounding_box.py` — `BoundingBox` class
- `pd_book_tools/geometry/point.py` — `Point` class
- Issue #35 (feature-request parent)
- Issue #36 (this spec)
