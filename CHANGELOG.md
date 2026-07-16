# Changelog

All notable changes to this project are documented here.

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
