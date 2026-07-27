# Changelog

All notable changes to this project are documented here.

## [0.5.0] - 2026-07-27

### Removed
- **Python 3.9 support — the package now requires Python 3.10 or newer.**
  `requires-python` is `>=3.10`, the 3.9 classifier is dropped, and CI tests
  3.10/3.11/3.12. 3.9 reached end of life in October 2025, and the tag model
  added in 0.4.0 uses PEP 604 type syntax (`int | None`) that 3.9 cannot
  evaluate at runtime. Users on 3.9 should stay on 0.3.1.
- **`tag_sub.py`** — backward-compatibility re-export of the tag-mutation module,
  no longer needed. All functions are exported from the top-level `trkbs_api`
  namespace.

### Changed
- **Public module renames for clarity** — module names now use `<verb>_<object>`
  pattern:
  - `export.py` → `export_text.py` — explicit about text extraction + formatting
  - `search.py` → `search_tags.py` — explicit about tag queries
  - `edit.py` → `edit_tags.py` — explicit about tag mutations
  - `validate.py` → `count_structure.py` — explicit about structural tag counting

  **No impact on public API** — all functions exported from `trkbs_api` namespace
  unchanged. Direct submodule imports (e.g., `from trkbs_api.search_tags import
  find_tags`) work but are unnecessary; use the flat namespace:
  `from trkbs_api import find_tags`.

## [0.4.0] - 2026-07-27

### Added
- **Query and find semantic tags: `find_tags(xml, tag=..., text=...)`** — the main
  scenario. Find all instances of a tag by name, optionally filtered by a regex
  pattern over the transcribed text (L1), and inspect the resolved token and
  line ID. E.g. `find_tags(xml, tag='person', text=r'Μ[ιί]λλ[εέ]ρ.+')` answers
  "has Μίλλερ been tagged as person everywhere it occurs?"
- **Document-wide tag queries: `find_tags_by_page(client, coll, doc, ...)`** —
  stream `find_tags` across a page range, stamping each result with its page number.
- **Editorial validation: `count_tags(xml)` / `count_tags_by_page(...)`** — count
  tag instances by name on a page or range, for validation checks like "expected
  2 `person` tags, found only 1".
- **Safe tag rename: `replace_tag_name(xml, old, new)`** — operates on the parsed
  tag model so the tag name is matched exactly, not as a substring. Unlike
  `replace_tag`, it does not corrupt property keys (§2 of the analysis).
- **Backward-compatible module alias** — `tag_sub.py` renamed to `edit.py` for
  clarity (search vs edit). `tag_sub` is preserved as a re-export alias.
- **Three-layer data model:** `TagInstance` dataclass that separates L1 (text),
  L2 (tag name + anchor), and L3 (opaque properties), enabling correct queries
  and edits. The model is the foundation for future L3 operations (property
  normalisation, enrichment, etc.).

### Changed
- **`replace_tag` and `replace_attr` are now documented as unsafe** for tag/property
  name changes. They remain as an escape hatch for edge cases, but new code should
  use `replace_tag_name` and operations on the tag model instead.
- **Round-trip safety:** `replace_tag` and `tag_empty_lines` now return the input
  XML unchanged if no matches are found (S3 guard), preventing silent mutation of
  pages that were unchanged.

### Fixed
- **Data corruption on zero-match runs** — `replace_tag` would always re-serialize
  even when nothing matched, causing `&#10;` (encoded newlines) in `custom` values
  to collapse to spaces on the next parse. Now returns input unchanged when no
  matches are found.

### Deprecated
- **`count_tag_by_page` is limited to structural tags** and should not be used for
  general tag audits. Use `count_tags_by_page` (new, pluralised, covers all 17 tag
  names) instead. `count_tag_by_page` is kept for backward compatibility.

## [0.3.1] - 2026-07-23

### Added
- **`get_text` text cleanup.** Two new opt-in flags, both off by default (so
  `get_text(xml)` is unchanged):
  - `cleanup=False` — rejoins words hyphenated across line breaks (the `¬`
    continuation sign) and collapses runs of spaces/tabs.
  - `flatten=False` — folds line breaks into single spaces for one continuous
    line; leave off to keep one line per `<TextLine>`.

## [0.3.0] - 2026-07-16

First minor release: new API, a rename, and behaviour changes. Includes the
`format_page_xml` pretty-printer added earlier. Being pre-1.0, this release makes
a few clean breaks (no back-compat aliases).

### Added
- **`format_page_xml(xml)`** and **`get_page(..., pretty=True)`** — indented,
  human-readable PAGE XML for viewing (Transkribus now serves it compact).
- **`count_tag_by_page(client, coll, doc, start, end, tag)`** — counts
  `structure {type:<tag>}` lines per page, **including zero-count pages** (which
  the old `validate_*` dropped). Replaces `validate_headings` / `validate_regesta`.
- **Configurable structural tag names.** `tag_heading`, `tag_marginalia`,
  `tag_empty_lines`, `add_regesta`, and `get_text` take `heading_tag` /
  `regesta_tag` / `marginalia_tag` arguments (defaulting to the Transkribus/LAGOOS
  names) so other projects can use their own vocabulary.
- **`continue_on_error` flag** on every `*_stream` helper: log-and-continue past a
  failed page instead of the default fail-fast abort.
- **`replace_tag(..., literal=True)`** to match a tag verbatim (`re.escape`),
  correct for Transkribus tags containing braces.

### Changed
- **`get_page_nr` → `get_num_pages`** (rename, no alias).
- **`get_pages_stream(coll, doc, page_start=1, page_end=None)`** — `page_start`
  now defaults to 1, and `page_end=None` streams to the end of the document
  (derived via `get_num_pages`). All `*_stream` helpers inherit these defaults.
- Structural tag matching now tests the exact `type:<name>` token instead of a
  bare substring, so a tag name is no longer confused with a longer one
  (`heading` vs `subheading`). `*_stream` runs log a one-line summary
  (pages/lines changed, failures) on completion.

### Removed
- **`remove_regesta`** — deprecated in 0.2.1; destructive (`decompose()` deletes
  whole lines). Use `get_text(xml, regesta=False)` to exclude regesta
  non-destructively.
- **`validate_headings`, `validate_regesta`** — superseded by `count_tag_by_page`.

## [0.2.1] - 2026-07-16

Patch release: correctness fixes and safe internal cleanups from a functional
review of the `src/trkbs_api/` modules. No public-API changes.

### Fixed
- **`tag_marginalia` no longer crashes on unindexed headings.** A `heading`-tagged
  line without a `readingOrder {index:…}` token made `_get_reading_index` call
  `.group(1)` on a `None` match (`AttributeError`). It now returns `None` on
  no-match; `_first_heading_index` and the main loop skip such lines (removing a
  broad `try/except` that also masked unrelated errors).
- **Read methods now check HTTP status.** `get_col_ids`, `get_doc_ids`,
  `get_page`, `get_page_transcript_ids`, and `get_metadata` now call
  `raise_for_status()`. Previously an error response (e.g. an expired session)
  was parsed as data — `get_page` handed error HTML to BeautifulSoup, silently
  yielding empty results and silently-skipped stream pages.
- **`header_string_lookup` always returns a `bool`.** It previously returned
  `True` or an implicit `None`.

### Changed
- `remove_regesta` is **deprecated** (emits `DeprecationWarning`); use
  `get_text(xml, regesta=False)` to exclude regesta non-destructively. It stays
  exported for now and is scheduled for removal in 0.3.
- Batch changelog CSVs are now named `changelog_%Y%m%d_%H%M%S.csv` (was
  `%d-%m_%H%M%S`, which omitted the year).
- `run_stream` no longer mutates caller-supplied diff dicts (writes a copy with
  the `page` field instead).
- Simplified the repeated-regesta-tag collapse in `tag_empty_lines`; removed a
  dead comment; renamed copy-pasted `reg_*` locals in `validate_headings`.
- Documented the stream helpers' fail-fast behaviour and `page_start` resume
  (README), and `replace_tag`'s regex-vs-literal `tag` semantics (docstring).

## [0.2.0] - 2026-07-14

First public GitHub release. Focus: correctness, security, and a lighter install.

### Fixed
- **`post_page` no longer crashes on errors.** The previous bare `except:`
  referenced an unassigned `response` (raising `UnboundLocalError`) and never
  checked the HTTP status. It now calls `raise_for_status()` and returns the
  response, so failed uploads surface instead of passing silently.
- **Session cookie no longer sent in cleartext.** `get_col_ids`,
  `get_page_transcript_ids`, and `get_metadata` used `http://`, which the
  server 301-redirects to HTTPS — leaking the `JSESSIONID` cookie on the first
  hop. All endpoints now use `https://`.
- **`find_months_in_text` now matches.** The word-boundary regex was
  double-escaped (`\\b`), so French month detection never matched; fixed to `\b`.
- **Malformed query strings.** Optional `param` was appended as `/?{param}`
  (stray leading slash); now `?{param}`.

### Added
- Request `timeout` (default 30s) on every HTTP call to prevent indefinite hangs.
- `BASE_URL` constant and a configurable `timeout` argument on `TrkbsClient`.
- Explicit `__all__` in the package namespace.

### Changed
- **Removed the experimental `ner.py` module** and its `torch` / `transformers`
  dependencies — dropping a multi-gigabyte install for functionality that was
  deprecated. Added the previously-undeclared `lxml` dependency (required by the
  `BeautifulSoup(..., "xml")` parser used throughout).
- Deduplicated the four `*_stream` batch drivers into a shared
  `_streaming.run_stream` helper.
- Replaced library `print()` calls with the standard `logging` module.
- `replace_tag` now emits `str(soup)` instead of `soup.prettify()`, consistent
  with the other transforms (prettify reflows whitespace and can corrupt PAGE XML).
- Rewrote the README to match the actual API (`TrkbsClient`, real function names,
  `TRANSKRIBUS_USERNAME` / `TRANSKRIBUS_PASSWORD`).
- Filled in the license/author placeholders and populated `[project.urls]`.
