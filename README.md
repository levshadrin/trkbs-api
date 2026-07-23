# trkbs_api

A Python package for exporting, parsing, editing, and uploading Transkribus PAGE XML via the Transkribus REST API.

Developed by Lev Shadrin (<lev.shadrin@uibk.ac.at>) as part of the LAGOOS project (<https://lagoos.org>).

---

## Features

- **API Client**: Log in and interact with Transkribus via a simple `TrkbsClient` class.
- **Collection, document, page navigation**: Use `.get_col_ids()`, `.get_doc_ids()`, and `.get_page()` methods to navigate the standard Transkribus document structure.
- **Semantic tagging**: Tag PAGE-XML `<TextLine>` elements as Transkribus strucutral tags (e.g. `heading`, `regesta`, or `marginalia`) via the `custom` attribute.
- **Batch streaming**: Page through a document, apply a transform, write a CSV changelog, and post changes back.
- **Easy integration**: Use as a standalone tool or import in any notebook or script.

---

## Contents

- [Installation](#installation)
- [Credentials & Environment](#credentials--environment)
- [Usage Examples](#usage-examples)
- [Log output](#log-output)
- [Functions & Classes](#main-functions--classes)

## Installation

### Requirements

```
python >= 3.9
```

First, clone or copy this repository to your local machine.

Then from the project root directory (where `pyproject.toml` is):

```bash
pip install -e .
```

If using Hatch environments:
```bash
hatch env create
hatch run pip install -e .
```

If using Colab:
```
!pip install -q git+https://github.com/levshadrin/trkbs-api
```

---

## Credentials & Environment

### **Best Practice: Use a `.env` File**

Create a `.env` file in your project root (this is **not** committed to git):

```
TRANSKRIBUS_USERNAME=your_transkribus_username
TRANSKRIBUS_PASSWORD=your_transkribus_password
```

Or export them as environment variables in your shell:

```bash
export TRANSKRIBUS_USERNAME="your_transkribus_username"
export TRANSKRIBUS_PASSWORD="your_transkribus_password"
```

`TrkbsClient()` reads these automatically. 

You can also pass credentials directly: `TrkbsClient(user="...", pw="...")`, but this is not recommended.

### Running in Google.Colab

Set `TRANSKRIBUS_USERNAME` and `TRANSKRIBUS_PASSWORD` as Colab secrets, then run:

```python
from google.colab import userdata
from trkbs_api import TrkbsClient

client = TrkbsClient(
    user=userdata.get('TRANSKRIBUS_USERNAME'),
    pw=userdata.get('TRANSKRIBUS_PASSWORD'),
)
```

---

## Usage Examples

### General use cases

```python
from trkbs_api import TrkbsClient, tag_heading, get_headings_by_page, find_months_in_text, get_text
from bs4 import BeautifulSoup

# Initialize client (uses env vars / .env if no args)
client = TrkbsClient()

# List collections -> {colName: colId}
collections = client.get_col_ids()
print(collections)

# List documents in a collection -> {title: docId}
docs = client.get_doc_ids(coll_id)

# Fetch one page of PAGE XML
page_xml = client.get_page(coll_id, doc_id, page_nr)
```

> **Readable output.** Transkribus serves PAGE XML compact (single-line). For a
> human-readable, indented view, pass `pretty=True` (or call `format_page_xml`
> on any PAGE-XML string):
>
> ```python
> print(client.get_page(coll_id, doc_id, page_nr, pretty=True))
> ```
>
> This is **view-only** — pretty-printing adds whitespace, so never pass a
> prettified string to `post_page`. Use the default (raw) output for edits and
> uploads; the batch/tagging helpers already do.

```python
# Export the reading text from PAGE XML
text = get_text(page_xml)
print(text)
```

Two flags control formatting:

- `cleanup` (default `False`): rejoins words hyphenated across line breaks (the
  `¬` continuation sign) and collapses runs of spaces/tabs.
- `flatten` (default `False`): folds line breaks into single spaces to yield one
  continuous line. Leave as-is to keep one line per `<TextLine>`.

```python
get_text(page_xml, cleanup=True)                 # de-hyphenated, one line per TextLine
get_text(page_xml, cleanup=True, flatten=True)   # de-hyphenated, folded to one flat line
get_text(page_xml, regesta=True)                 # also include regesta-tagged lines
```

### LAGOOS-specific use cases

```python
# Detect French month names in the page text
soup = BeautifulSoup(page_xml, "xml")
months = find_months_in_text(soup.get_text())
print(months)

# Tag headings on a single page (df_header holds the reference strings)
updated_xml, lines_tagged = tag_heading(df_header, page_xml)
if lines_tagged:
    client.post_page(updated_xml, coll_id, doc_id, page_nr)
```

### Batch processing

For batch processing across a page range, use the `*_stream` helpers
(`tag_heading_stream`, `replace_tag_stream`, `replace_attr_stream`,
`tag_marginalia_stream`), which write a timestamped CSV changelog and post
modified pages back automatically.

These helpers are **fail-fast**: if a page fails to upload, the run stops there.
Pages processed before the failure are already saved to Transkribus and recorded
in the CSV changelog. Fix the cause (e.g. an expired session) and resume by
re-running with `page_start` set to the page that failed.

---

## Log output

The package logs through Python's standard `logging` module under the
`trkbs_api` logger — it never `print()`s. By default `logging` shows only
warnings and errors, so informational messages (like login confirmation) are
hidden until you opt in. Add this once in your script or notebook:

```python
import logging
logging.basicConfig(level=logging.INFO)

from trkbs_api import TrkbsClient
client = TrkbsClient()
# INFO:trkbs_api.client:Transkribus login successful (status 200)
```

Use `level=logging.DEBUG` instead to also see per-line change details from the
tagging/streaming functions. To adjust only this package (leaving other
libraries quiet), target its logger directly:

```python
logging.getLogger('trkbs_api').setLevel(logging.DEBUG)
```

---

## Main Functions & Classes

### **TrkbsClient**
- Handles Transkribus login and API calls over HTTPS.
- Reads credentials from arguments, environment variables, or a `.env` file.
- Methods:
  - `get_col_ids()`: List all collections (`{colName: colId}`).
  - `get_doc_ids(coll_id)`: List all documents in a collection (`{title: docId}`).
  - `get_page(coll_id, doc_id, page_nr, pretty=False)`: Fetch PAGE XML for a page (`pretty=True` for an indented view).
  - `get_pages_stream(coll_id, doc_id, page_start=1, page_end=None)`: Yield `(page_nr, xml)` over a range; `page_end=None` streams the whole document.
  - `post_page(xml, coll_id, doc_id, page_nr)`: Upload modified PAGE XML (raises on HTTP error).
  - `get_metadata` / `get_num_pages` / `get_page_transcript_ids`: Document/page metadata helpers.

### **Tagging**
- `tag_heading(df_header, xml)` / `tag_heading_stream(...)`: Tag heading lines.
- `tag_empty_lines(xml)`, `add_regesta`: Regesta handling.
- `tag_marginalia(xml)` / `tag_marginalia_stream(...)`: Tag marginalia lines.
- `replace_tag` / `replace_tag_stream`, `replace_attr` / `replace_attr_stream`: Substitute custom-attribute tags/values.

The tagging functions take structural-tag-name arguments (`heading_tag`, `regesta_tag`,
`marginalia_tag`) defaulting to the Transkribus/LAGOOS names — override them to match a
different vocabulary. The `*_stream` helpers accept `continue_on_error=True` to log and skip
a failed page instead of aborting the run.

### **Helpers**
- `find_months_in_text(text, ignore_case=True)`: Detect French month names in a string.
- `get_headings_by_page(df, page_nr)`: Look up reference headers for a page.
- `get_text(xml, cleanup=False, flatten=False, regesta=False)`: Export plain text from PAGE XML (`cleanup` de-hyphenates and normalizes whitespace; `flatten` folds line breaks into spaces).
- `format_page_xml(xml)`: Return an indented, human-readable copy of PAGE XML (view-only).
- `count_tag_by_page(client, coll, doc, start, end, tag)`: Count `type:<tag>` lines per page (includes zero-count pages).

---

## License

MIT

---

## Author

*Lev Shadrin* — lev.shadrin@uibk.ac.at

---

*Happy coding!*
