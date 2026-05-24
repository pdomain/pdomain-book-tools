# Spec: Scannos Rule and Candidate Module

> **Status**: Draft
> **Last updated**: 2026-05-24
> **Spec-Issue**: ConcaveTrillion/pd-book-tools#209

Own the data model, storage, and API for the scannos (scanner
error corrections) subsystem used across `pd-prep-for-pgdp` and future
pd-* tools. This module gates all Stage 13 slices (`S13-A` through `S13-D`)
in the `pd-prep-for-pgdp` design-handoff plan. The UI components it backs are
designed in
`pd-ui/docs/templates/design_handoff_pd_ui/wf05b/scanno-configure.jsx`
and `wf05b/scanno-promote.jsx`; the domain model and design rationale appear
in `wf05b/DISCUSSION.md`.

Related specs:

- `Spec: 01-page-model` — the `Page` / `Block` / `Word` types whose text
  is scanned for scanno candidates.
- `Spec: 03-reorganize-pipeline` — the upstream pipeline that produces the
  word-level text this module reads.

---

## 1. TL;DR

Add `pd_book_tools.scannos` owning:

1. `ScannoRule` — a rule in the global library (e.g. "tbe" → "the").
2. `ScannoCandidate` — a per-book occurrence flagged by a rule or by OCR
   confidence heuristics.
3. Storage: **SQLite** for the global rule library (relational queries on
   hit counts, book counts, contributor history), **JSON sidecar** for
   per-book candidates (matches the existing pd-* sidecar convention).
4. API: load/save/query rules; load/save/promote candidates; promotion flow
   that records an evidence trail when a candidate is promoted to a rule.

---

## 2. Context

### 2.1 What scannos are

A "scanno" is a word whose appearance in an OCR'd text is likely a scanner
error rather than an authorial choice — "tbe" instead of "the", "rn" instead
of "m", "liis" instead of "his". Two categories exist:

- **Rule-driven**: a global library entry that applies across many books.
  A rule carries statistics (how many books it has fired in, how many total
  hits) that inform confidence.
- **Book-specific candidates**: tokens flagged for a particular scan that may
  be genuine (OCR noise) or may be valid archaic forms. A human reviewer
  accepts or dismisses each candidate; accepted ones can be promoted to the
  global library.

### 2.2 Design handoff context

The `wf05b` prototype shows three surfaces:

- **Pipeline panel** (`S13-A`): per-page density bar showing scanno hit
  density; a "Re-scan all pages" trigger.
- **Capture** (`S13-B`): inline token popover in the PageWorkbench where the
  user accepts, dismisses, or promotes a suspicion on a specific word.
- **Promote** (`S13-C`): a candidate triage table where accepted candidates
  are reviewed before promotion to the global library.
- **Configure** (`S13-D`): the global rule library browser (search, filter by
  scope/auto/conflict, edit a rule's `sug` / `note` / `auto` flag).

`wf05b/DISCUSSION.md` records the key domain decision: candidates and rules
are separate entities with an explicit promotion step, rather than a single
mutable record. This spec adopts that model.

### 2.3 Why pd-book-tools owns the schema

The rule library and candidate store are consumed by:

- `pd-prep-for-pgdp` (Stage 13 slices)
- Potentially `pd-ocr-cli` (automatic scanno flagging in plain-text output)
- Potentially `pd-ocr-labeler-spa` (inline token highlights during review)

Centralising the schema and storage layer in pd-book-tools prevents each
downstream tool from independently inventing its own format and migration path.

---

## 3. Goals / Non-Goals

### Goals

- Define `ScannoRule` and `ScannoCandidate` as Python dataclasses with a
  stable `to_dict` / `from_dict` round-trip.
- Implement SQLite-backed `RuleLibrary` for the global rule store with CRUD,
  search, and statistics queries.
- Implement JSON-sidecar-backed `CandidateStore` for per-book candidates,
  following the existing sidecar naming convention used elsewhere in pd-*.
- Implement a `promote(candidate, library)` operation that creates or updates
  a `ScannoRule`, records provenance (which book, which user, timestamp), and
  marks the candidate as `'promoted'`.
- Provide a `scan_page(page: Page, library: RuleLibrary) -> list[ScannoCandidate]`
  function for literal and word-final pattern matching against a page's words.
- Expose a default global library path via `platformdirs` so the library is
  shared across tools without each tool hard-coding its location.
- Ship an empty default library (empty SQLite file) bundled with the package
  so first-run works without a separate download step.

### Non-Goals

- Populating the global library with rules — that is a data task (seeding from
  PGDP community lists, dpscannos, etc.), not a code task. The spec only
  defines the schema and storage layer.
- Regex scanning in V1 (`match: 'regex'`) — the schema defines it for
  forward compatibility, but the `scan_page` implementation in V1 supports
  only `'literal'` and `'word-final'`. Regex support is a V2 item.
- The UI (FastAPI routes, React components) — those belong to `pd-prep-for-pgdp`
  slices `S13-A` through `S13-D`.
- Multi-user collaboration or online sync of the global library.

---

## 4. Constraints

- The global SQLite library must be readable by multiple pd-* processes
  concurrently (read-heavy; WAL mode required).
- JSON sidecars must use UTF-8 and be human-readable (indented) so developers
  can inspect them without tooling.
- `ScannoRule.id` and `ScannoCandidate.id` must be stable, human-readable
  strings (not auto-increment integers) so that JSON exports and git diffs
  are meaningful. Recommended format: slug of `pattern`, e.g. `tbe_the_v1`.
- The `promote` function must be atomic with respect to the SQLite write
  (use a transaction) and idempotent (re-promoting the same candidate updates
  evidence rather than creating a duplicate rule).
- `platformdirs` is already a dependency of the pd-* stack; no new mandatory
  dep needed for the default path resolution.

---

## 5. Options Considered

### O-A: Single SQLite database for both rules and candidates

Simple from a query perspective; candidates could be JOINed to rules in one
query. Rejected: per-book candidate stores would accumulate in the global
database, making it hard to share the rule library independently of any one
book's working state. Also breaks the existing pd-* convention of book-level
sidecars that travel with the book's output directory.

### O-B: Two JSON files (global rules + per-book candidates)

Pure JSON matches the pd-* sidecar convention everywhere. Rejected for the
global library: querying hit counts, filtering by contributor, and pagination
over thousands of rules is significantly harder on JSON than on SQLite. The
global library is write-once-read-many from a single-user perspective, so
SQLite's locking model is not a concern.

### O-C: SQLite for global library, JSON sidecar for per-book candidates (chosen)

Combines the query power of SQLite for the shared library with the portability
and git-friendliness of JSON for per-book state. Each book's output directory
carries `<book-id>-scanno-candidates.json`; the global library lives at the
`platformdirs` user-data path. This matches the rationale in `wf05b/DISCUSSION.md`.

---

## 6. Decision

Implement O-C. Module layout:

```text
pd_book_tools/
  scannos/
    __init__.py           # re-exports ScannoRule, ScannoCandidate, RuleLibrary,
                          # CandidateStore, scan_page, promote
    _models.py            # dataclasses ScannoRule + ScannoCandidate
    _library.py           # RuleLibrary (SQLite CRUD + search)
    _candidate_store.py   # CandidateStore (JSON sidecar CRUD)
    _scanner.py           # scan_page()  literal + word-final matching
    _promote.py           # promote()    candidate → rule evidence trail
    _paths.py             # default_library_path() via platformdirs
```

### 6.1 ScannoRule schema

```python
@dataclass
class ScannoRule:
    id: str                          # slug, e.g. "tbe_the_v1"
    pattern: str                     # the error form, e.g. "tbe"
    sug: str                         # the suggested correction, e.g. "the"
    match: Literal['literal', 'word-final', 'regex']
    scope: Literal['global', 'project', 'book']
    auto: bool                       # safe to auto-apply without review
    hits: int                        # total occurrences across all indexed books
    books: int                       # number of distinct books this rule has fired in
    contributors: list[str]          # user IDs who have confirmed this rule
    added: str                       # ISO 8601 datetime
    updated: str                     # ISO 8601 datetime
    conflict: str | None = None      # id of a conflicting rule, if any
    note: str | None = None          # free-text annotation
```

### 6.2 ScannoCandidate schema

```python
@dataclass
class ScannoCandidate:
    id: str                          # slug, e.g. "liis_his_p042_w007"
    token: str                       # the word as it appears in the scan
    sug: str                         # suggested correction
    src: Literal['ocr', 'rule', 'manual']
    hits: int                        # occurrences in this book
    pages: list[int]                 # page indices where token appears
    conf: float                      # [0.0, 1.0] confidence (OCR conf or rule-match score)
    status: Literal['pending', 'accepted-local', 'promoted', 'dismissed']
    first_seen: str                  # ISO 8601 datetime
    note: str | None = None
```

### 6.3 Key API surface

```python
# RuleLibrary
library = RuleLibrary(path)           # opens or creates the SQLite file
library.add(rule: ScannoRule)
library.get(rule_id: str) -> ScannoRule | None
library.search(q: str, *, scope=None, auto=None, limit=50) -> list[ScannoRule]
library.update(rule: ScannoRule)
library.delete(rule_id: str)
library.stats() -> dict[str, int]     # total_rules, total_hits, total_books

# CandidateStore
store = CandidateStore(path)          # opens or creates the JSON sidecar
store.add(candidate: ScannoCandidate)
store.get(candidate_id: str) -> ScannoCandidate | None
store.list(*, status=None) -> list[ScannoCandidate]
store.update(candidate: ScannoCandidate)
store.save()                          # flush to disk (explicit; no auto-save)

# Scanner
candidates = scan_page(
    page: Page,
    library: RuleLibrary,
    *,
    min_conf: float = 0.0,
) -> list[ScannoCandidate]

# Promoter
promote(
    candidate: ScannoCandidate,
    store: CandidateStore,
    library: RuleLibrary,
    *,
    contributor: str,
    auto: bool = False,
) -> ScannoRule

# Default path
from pd_book_tools.scannos import default_library_path
path: Path = default_library_path()
# → ~/.local/share/pd-suite/scannos/rules.db  (or platform equivalent)
```

### 6.4 SQLite schema

```sql
CREATE TABLE rules (
    id          TEXT PRIMARY KEY,
    pattern     TEXT NOT NULL,
    sug         TEXT NOT NULL,
    match       TEXT NOT NULL CHECK(match IN ('literal','word-final','regex')),
    scope       TEXT NOT NULL CHECK(scope IN ('global','project','book')),
    auto        INTEGER NOT NULL DEFAULT 0,
    hits        INTEGER NOT NULL DEFAULT 0,
    books       INTEGER NOT NULL DEFAULT 0,
    contributors TEXT NOT NULL DEFAULT '[]',  -- JSON array of strings
    added       TEXT NOT NULL,
    updated     TEXT NOT NULL,
    conflict    TEXT REFERENCES rules(id),
    note        TEXT
);
CREATE INDEX rules_pattern ON rules(pattern);
CREATE INDEX rules_scope   ON rules(scope);
CREATE INDEX rules_auto    ON rules(auto);
```

WAL mode is enabled at `PRAGMA journal_mode=WAL` on first open.

---

## 7. Implementation Plan

1. Write `_models.py` with `ScannoRule` and `ScannoCandidate` dataclasses
   plus `to_dict` / `from_dict` round-trip.
2. Write `_library.py` implementing `RuleLibrary` with the SQLite schema
   above; include migration scaffolding (a `schema_version` table) even though
   V1 has only one version.
3. Write `_candidate_store.py` implementing `CandidateStore` backed by a
   single JSON array file. File is read fully on open and written fully on
   `save()` — acceptable because per-book candidate counts are expected to be
   in the low hundreds.
4. Write `_scanner.py` with `scan_page` for `literal` and `word-final` match
   types. `literal` = exact string match of `Word.text.lower()`. `word-final` =
   word ends with the pattern (e.g. pattern `"m"`, word `"tliern"` → hit).
5. Write `_promote.py` implementing `promote()`:
   - If no rule exists for `(pattern, sug)`, create one with `hits=candidate.hits`,
     `books=1`, `contributors=[contributor]`.
   - If a rule already exists, increment `hits` and `books` (if not already
     counted for this book's contributor run), append `contributor` if not
     already listed, update `updated`.
   - In both cases, update `candidate.status = 'promoted'` and `store.save()`.
6. Write `_paths.py` with `default_library_path()`.
7. Write `__init__.py` re-exporting the public surface.
8. Bundle an empty `rules.db` under `pd_book_tools/scannos/data/empty_rules.db`
   for first-run initialisation (copy-on-first-open to the user data dir).

---

## 8. Test Plan

| Test | Location | What it checks |
|---|---|---|
| `test_rule_round_trip` | `tests/test_scannos.py` | `ScannoRule.to_dict` / `from_dict` identity |
| `test_candidate_round_trip` | same | `ScannoCandidate.to_dict` / `from_dict` identity |
| `test_library_add_get` | same | Add a rule, retrieve by id |
| `test_library_search` | same | Search by pattern substring; filter by `auto` |
| `test_library_wal_mode` | same | SQLite file uses WAL journal mode |
| `test_candidate_store_persist` | same | Add candidate, `save()`, re-open, list → present |
| `test_scan_page_literal` | same | Page with word "tbe" and rule `tbe→the` → one candidate |
| `test_scan_page_word_final` | same | Page with word "rn" suffix rule → hit |
| `test_scan_page_no_rules` | same | Empty library → empty candidate list |
| `test_promote_creates_rule` | same | Promote candidate → rule created with correct hits |
| `test_promote_idempotent` | same | Promote same candidate twice → rule updated, not duplicated |
| `test_promote_updates_candidate_status` | same | After promote, candidate.status == 'promoted' |
| `test_default_library_path` | same | Returns a `Path` under a user-data dir, never None |

---

## 9. Open Questions

- **Q-SC-1**: Should `CandidateStore` use a JSON array file or a directory of
  per-candidate JSON files? Array file is simpler and covers expected scale; a
  directory would enable partial writes. Leaning array-file for V1.
- **Q-SC-2**: The `wf05b/DISCUSSION.md` mentions a potential future where the
  rule library is shared as a community-maintained dataset file (like a dpscannos
  update feed). The `scope: 'global'` field anticipates this but the update
  mechanism is unspecified. No action in V1; note for V2.
- **Q-SC-3**: `ScannoRule.contributors` is stored as a JSON-serialised list in
  SQLite rather than a junction table. This is sufficient for V1 (single-user,
  no query over contributors needed). If contributor-based filtering is added
  later, a migration to a junction table will be needed.
- **Q-SC-4**: The `scan_page` function operates on a single `Page`. A
  `scan_document(pages, library)` convenience wrapper scanning all pages at
  once and de-duplicating candidates by `(token, sug)` would be useful.
  Defer to V1 implementation feedback.
