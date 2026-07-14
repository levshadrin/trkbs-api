# Changelog

All notable changes to this project are documented here.

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
