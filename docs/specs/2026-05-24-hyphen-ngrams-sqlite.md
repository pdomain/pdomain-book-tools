---
Status: active
Owner: CT
Created: 2026-05-24
Last verified: 2026-07-13
Kind: spec
---

# Spec: Hyphen N-Grams SQLite Migration

> **Status**: Draft
> **Last updated**: 2026-05-24
> **Spec-Issue**: pdomain/pdomain-book-tools#210

Replace the unofficial Google Books JSON n-gram endpoint with a
pre-indexed, locally-resident SQLite database of hyphen-pair frequency data
extracted from the Google Books Ngrams corpus. The adapter interface
(`HyphenNgramsClient`) is already named in the `pdomain-prep-for-pgdp` design
handoff spec; Stage 15 slices (`S15-A` through `S15-F`) ship JSON-first via
that interface and migrate to SQLite once this spec lands.

Background reading: `pdomain-ui/docs/templates/design_handoff_pdomain_ui/wf05/NOTES.md`
documents both paths (live API and pre-indexed SQLite) and the rationale for
preferring local indexing.

Related specs:

- `Spec: 01-page-model` — the `Word` type whose text is the query key.
- `Spec: 2026-05-24-scannos-module` — the parallel local-data module for
  scannos rules; follows the same `platformdirs` + opt-in-download convention.

---

## 1. TL;DR

Add `pdomain_book_tools.hyphen_ngrams` exposing a `HyphenNgramsClient` protocol
and two implementations:

- `JsonApiClient` — the existing fallback that calls the unofficial
  Google Books JSON endpoint (V0, ships first, already in
  `pdomain-prep-for-pgdp`).
- `SqliteClient` — the new local implementation that queries a
  pre-indexed ~50 MB SQLite file derived from the raw Google Books Ngrams
  corpus dump (V1, this spec).

Both implementations expose the same `HyphenNgramsClient` protocol so
callers switch by construction only.

---

## 2. Context

### 2.1 The hyphen-join problem

When a book is scanned and OCR'd, end-of-line hyphens appear throughout.
Some hyphens are grammatical (compound words: "well-known") and some are
purely typographic line-break artefacts (the word "re-" / "turn" spans two
lines). The `pdomain-prep-for-pgdp` Stage 15 Hyphen Join workbench helps the
user decide, for each hyphenated pair `(word_a, word_b)`, whether to join
the words, keep the hyphen, or leave them separate.

The key signal is historical frequency: how often do `word_a-word_b` (with
hyphen) and `word_aword_b` (joined) appear in period-contemporary text? A
high joined-form frequency suggests the hyphen is a line-break artefact; a
high hyphenated-form frequency suggests the hyphen should be preserved.

### 2.2 Current state: unofficial JSON endpoint

The Google Books Ngrams v2 JSON API (`books.google.com/ngrams/json`) provides
frequency time-series for arbitrary phrases. It is unofficial, rate-limited,
subject to removal without notice, and requires internet access at query time.
The `wf05/NOTES.md` design note explicitly flags this fragility and recommends
pre-indexing.

### 2.3 Why pre-index into SQLite

The Google Books Ngrams corpus data files are available for download at
`storage.googleapis.com/books/ngrams/books/datasetsv3.html`. The
hyphen-pair data (bigrams where the 1-gram contains a hyphen) is a small
fraction of the full corpus. A pre-extraction pipeline can:

1. Download only the relevant bigram files.
2. Filter to records where `ngram` contains a hyphen.
3. Aggregate by decade bucket (1700–2020).
4. Store the result as a single ~50 MB SQLite file shipped as a
   downloadable data artifact.

This removes the runtime internet dependency and enables sub-millisecond
local lookups.

### 2.4 Adapter interface in pdomain-prep-for-pgdp

The `pdomain-prep-for-pgdp` plan introduces `HyphenNgramsClient` as a
structural protocol (duck-typed, no `abc.ABC`). Stage 15 ships with
`JsonApiClient` satisfying that protocol; this spec adds `SqliteClient`
as a drop-in replacement.

---

## 3. Goals / Non-Goals

### Goals

- Define `HyphenNgramsClient` as a Python `typing.Protocol` in
  `pdomain_book_tools.hyphen_ngrams` so both implementations are type-safe.
- Implement `SqliteClient` querying a locally-cached SQLite file.
- Implement an extraction pipeline (`scripts/build_hyphen_ngrams_db.py`)
  that downloads the relevant Google Books Ngrams bigram files and
  produces the SQLite database.
- Define the SQLite schema: `(word_a, word_b, joined_freq[year_bucket],
  hyphen_freq[year_bucket])` where `year_bucket` is decade-granularity
  covering 1700–2020.
- Choose and document a packaging strategy for the SQLite file (see §5).
- Keep `JsonApiClient` as a fallback for users who cannot or do not want
  to download the SQLite file.
- Expose a CLI entry point `pdomain-book-tools build-hyphen-db` that runs the
  extraction pipeline.

### Non-Goals

- Full Google Books Ngrams download (we only extract hyphen bigrams, not
  the full corpus).
- The `pdomain-prep-for-pgdp` FastAPI routes that call this client — those belong
  to the S15-* slices.
- Diacritic normalisation or lemmatisation of the corpus entries — V1 does
  exact-match lookup only.
- Offline corpus updates (V1 database is built once from a specific corpus
  snapshot, identified by date in the database metadata table).

---

## 4. Constraints

- `SqliteClient` must have no mandatory runtime dependencies beyond the
  Python standard library (`sqlite3`) and `platformdirs`.
- The extraction pipeline (`build_hyphen_ngrams_db.py`) may use `requests`
  (already a pdomain-* dep) and standard-library `gzip`; no heavy ML/data deps.
- The SQLite file must be usable by multiple read-only processes
  concurrently; WAL mode is required.
- The protocol must be satisfiable by a lightweight test double (a dict
  lookup) so Stage 15 tests never require the 50 MB file.
- The packaged database, once distributed, must remain stable and
  re-downloadable from a versioned URL (not a mutable `latest.db` link)
  so that reproducible builds are possible.

---

## 5. Options Considered

### O-A: Keep the unofficial JSON API as sole source (rejected)

Fragile, rate-limited, internet-dependent. Rejected as a long-term
strategy; retained only as a fallback.

### O-B: Embed the SQLite file in the pdomain-book-tools wheel

A 50 MB file inside the wheel means every pip-install of pdomain-book-tools
downloads it, even for users who never use the Hyphen Join feature. The wheel
would exceed PyPI's 100 MB soft limit. Rejected.

### O-C: Separate optional data wheel (`pdomain-book-tools-hyphen-data`)

Publish a companion wheel containing only the SQLite file. Installs on
demand via `pip install pdomain-book-tools[hyphen-data]`. Clean separation of
code and data; wheel can be re-published when the corpus snapshot is
refreshed. Complicates the pdomain-index release pipeline (two wheels to
publish per release instead of one). Viable; see §6 decision.

### O-D: Download-on-first-use from a GitHub Release asset

`SqliteClient` lazily downloads the database on first query and caches it
at `platformdirs` user-data path. No new wheel or pip extra needed. User
sees a one-time download delay (~50 MB). The download URL is versioned (a
GitHub Release asset URL pinned in the pdomain-book-tools source). This matches
the pattern used by `spacy` and `stanza` for language models. Selected as
the primary mechanism for V1.

### O-E: Require user to run `pdomain-book-tools build-hyphen-db` manually

Power-user path only; not user-friendly for the `pdomain-prep-for-pgdp`
desktop audience. Retained as an advanced option alongside O-D.

---

## 6. Decision

Implement **O-D** (download-on-first-use) as the primary mechanism, with
**O-E** (manual build) as an advanced option and **O-A** (`JsonApiClient`)
as a fallback when neither is available.

Module layout:

```text
pdomain_book_tools/
  hyphen_ngrams/
    __init__.py        # re-exports HyphenNgramsClient, SqliteClient,
                       # JsonApiClient, default_db_path, ensure_db
    _protocol.py       # HyphenNgramsClient Protocol + FreqResult dataclass
    _sqlite_client.py  # SqliteClient
    _json_api_client.py # JsonApiClient (moved from pdomain-prep-for-pgdp)
    _paths.py          # default_db_path() via platformdirs
    _downloader.py     # ensure_db(force=False) — lazy download logic

scripts/
  build_hyphen_ngrams_db.py   # corpus download + extraction pipeline
```

### 6.1 Protocol definition

```python
@dataclass
class FreqResult:
    word_a: str
    word_b: str
    hyphen_freq: dict[int, float]   # decade → relative frequency, e.g. {1900: 0.000412}
    joined_freq: dict[int, float]   # decade → relative frequency

class HyphenNgramsClient(Protocol):
    def query(
        self,
        word_a: str,
        word_b: str,
        *,
        start_year: int = 1800,
        end_year: int = 2000,
    ) -> FreqResult | None: ...
```

### 6.2 SQLite schema

```sql
CREATE TABLE metadata (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
-- Populated at build time:
-- key='corpus_snapshot_date', value='2023-01-01'
-- key='schema_version', value='1'

CREATE TABLE hyphen_pairs (
    word_a      TEXT NOT NULL,
    word_b      TEXT NOT NULL,
    decade      INTEGER NOT NULL,   -- e.g. 1900 for the 1900s
    hyphen_freq REAL NOT NULL DEFAULT 0.0,
    joined_freq REAL NOT NULL DEFAULT 0.0,
    PRIMARY KEY (word_a, word_b, decade)
);
CREATE INDEX hp_lookup ON hyphen_pairs(word_a, word_b);
```

WAL mode enabled at PRAGMA `journal_mode=WAL`.

Frequencies are stored as relative frequency (count / total_tokens_that_decade)
rather than raw counts, so the values are stable across corpus size variations
and comparable across decades.

### 6.3 Download URL convention

The SQLite file is published as a GitHub Release asset on the
`pdomain/pdomain-book-tools` repository under the tag
`hyphen-data-v{YYYYMMDD}` (independent of the code release tag). The URL
template:

```text
https://github.com/pdomain/pdomain-book-tools/releases/download/
    hyphen-data-{snapshot_date}/hyphen_ngrams_{snapshot_date}.db
```

The URL is hard-coded in `_downloader.py` as a module constant
`HYPHEN_DB_URL` so it can be updated without touching the API surface.
`ensure_db()` checks `~/.local/share/pdomain-suite/hyphen-ngrams/<snapshot_date>.db`
before downloading; if found, returns the cached path immediately.

### 6.4 Extraction pipeline overview

`scripts/build_hyphen_ngrams_db.py`:

1. Download the Google Books Ngrams 2-gram files for the `eng-all` corpus
   (20 split files, gzipped TSV).
2. Stream-parse each file, filtering to records where `ngram` matches
   `word_a-word_b` (contains a hyphen and consists of exactly two
   alphabet-only tokens around the hyphen) or `word_aword_b` (the joined
   form of a known hyphen pair discovered in the same scan).
3. Aggregate by `(word_a, word_b, decade)`, computing relative frequency as
   `match_count / total_tokens_that_decade` (total token counts are in
   the totalcounts file).
4. Write to SQLite with the schema above.
5. Record `corpus_snapshot_date` in `metadata`.

The pipeline is idempotent (re-running with `--overwrite` replaces the db);
it is expected to take 30–60 minutes on a single core with adequate disk.

---

## 7. Implementation Plan

1. Write `_protocol.py` with `FreqResult` and `HyphenNgramsClient`.
2. Write `_paths.py` with `default_db_path()`.
3. Write `_downloader.py` with `ensure_db(force=False)` and `HYPHEN_DB_URL`.
4. Write `_sqlite_client.py` implementing `SqliteClient`.
   - `__init__(db_path: Path | None = None)` — defaults to
     `ensure_db()` result.
   - `query(word_a, word_b, *, start_year, end_year)` — returns
     `FreqResult | None` from a single parameterised SELECT.
5. Write `_json_api_client.py` — migrate the existing V0 implementation
   from `pdomain-prep-for-pgdp`. The `pdomain-prep-for-pgdp` import becomes an alias
   pointing at pdomain-book-tools once this ships.
6. Write `__init__.py` re-exporting the public surface.
7. Write `scripts/build_hyphen_ngrams_db.py` with streaming TSV parser.
8. Build the first database snapshot and publish as a GitHub Release asset
   (a manual step; not part of the normal release pipeline).

---

## 8. Test Plan

| Test | Location | What it checks |
|---|---|---|
| `test_freq_result_round_trip` | `tests/test_hyphen_ngrams.py` | `FreqResult` is a dataclass with expected fields |
| `test_sqlite_client_query_hit` | same | SQLite client returns `FreqResult` for a known pair |
| `test_sqlite_client_query_miss` | same | Unknown pair → `None` |
| `test_sqlite_client_year_range` | same | `start_year`/`end_year` filters decades correctly |
| `test_sqlite_client_wal_mode` | same | Opens in WAL mode |
| `test_json_api_client_interface` | same | `JsonApiClient` satisfies `HyphenNgramsClient` Protocol |
| `test_protocol_structural` | same | A plain dict-based test double satisfies the Protocol |
| `test_default_db_path_returns_path` | same | Returns a `Path`; does not require the file to exist |
| `test_ensure_db_cached` | same (monkeypatch) | If file present at path, no download attempted |
| `test_build_pipeline_smoke` | `tests/test_hyphen_ngrams_build.py` | Script produces a valid SQLite with correct schema on a 10-row fixture TSV |

The `test_sqlite_client_*` tests use a tiny fixture SQLite (3–5 rows)
created at test time via `pytest` `tmp_path`; they do not require the full
50 MB database to be present.

---

## 9. Open Questions

- **Q-HN-1**: Should `ensure_db` block the calling thread during download
  (synchronous `requests.get`) or be an `async def` that the FastAPI route
  can `await`? For V1, synchronous is simpler; the `pdomain-prep-for-pgdp`
  router can call it in a startup lifespan event or offload to a thread.
- **Q-HN-2**: The Google Books Ngrams 2-gram files are large (~20 GB
  compressed). The extraction pipeline streams and filters rather than
  materialising the full corpus, but the initial run still requires
  substantial disk and time. Should the pipeline accept a pre-filtered
  TSV to allow partial rebuilds? Useful if the corpus snapshot needs to be
  refreshed for a specific language or date range.
- **Q-HN-3**: `wf05/NOTES.md` mentions the possibility of a community-
  maintained hyphen-pair list (analogous to dpscannos for scannos) as a
  supplement to the Google Books frequencies. This is out of scope for V1
  but the `metadata` table should reserve a key for `community_list_version`
  to support it later.
- **Q-HN-4**: The `JsonApiClient` is currently implemented inside
  `pdomain-prep-for-pgdp`. Migration to pdomain-book-tools requires a deprecation shim
  in `pdomain-prep-for-pgdp` (re-export from the new location). The timing of
  that shim relative to the S15-A slice needs coordination.
- **Q-HN-5**: Frequency normalisation: relative frequency (chosen above) vs.
  raw count vs. Zipf score. The `wf05/NOTES.md` prototype renders the values
  as a small bar chart, suggesting relative frequency is the right unit (scale
  is human-meaningful). Confirm before building the extraction pipeline.

## Adversarial Review

- **Stage:** Migration/design review performed 2026-07-13; no implementation or data artifact was found.
- **Source:** Full spec, current package/CLI/dependency layout, and repository tests.
- **Accepted findings (and how folded in):** Redesign extraction as an explicit two-pass or indexed process; pin the corpus edition and exact normalization/counting rules; add checksum verification, locking, atomic download, retry/timeout, and corruption recovery; and define read-only SQLite behavior instead of assuming WAL is always safe. Treat size, duration, and latency figures as estimates until a reproducible build manifest and benchmark exist.
- **Disposition:** Accepted corrections and unresolved ideas are preserved in `docs/context/intent-map.md` as deferred work or owner decisions; the source body remains unchanged pending its next evidence-backed revision.
- **Residual risks:** Corpus licensing/redistribution, GitHub asset durability, initial build resource cost, API fallback drift, and cross-process first-use races remain unproven.
