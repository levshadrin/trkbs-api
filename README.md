# trkbs_api

A Python package for working with Transkribus PAGE XML via the Transkribus REST API.

Developed by Lev Shadrin as part of the LAGOOS project.

---

## Features

- **API Client**: Log in and interact with Transkribus via a simple `TrkbsClient` class.
- **Semantic tagging**: Tag PAGE-XML `<TextLine>` elements as headings, regesta, or marginalia via the `custom` attribute.
- **Batch streaming**: Page through a document, apply a transform, write a CSV changelog, and post changes back.
- **Easy integration**: Use as a standalone tool or import in any notebook or script.

---

## Installation

First, clone or copy this repository to your local machine.

Then from the project root directory (where `pyproject.toml` is):

```bash
pip install -e .
```

*(If using Hatch environments:*
```bash
hatch env create
hatch run pip install -e .
```
*)*

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

`TrkbsClient()` reads these automatically. You can also pass credentials
directly: `TrkbsClient(user="...", pw="...")`.

---

## Usage Example

```python
from trkbs_api import TrkbsClient, tag_heading, get_headings_by_page, find_months_in_text
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

# Detect French month names in the page text
soup = BeautifulSoup(page_xml, "xml")
months = find_months_in_text(soup.get_text())
print(months)

# Tag headings on a single page (df_header holds the reference strings)
updated_xml, lines_tagged = tag_heading(df_header, page_xml)
if lines_tagged:
    client.post_page(updated_xml, coll_id, doc_id, page_nr)
```

For batch processing across a page range, use the `*_stream` helpers
(`tag_heading_stream`, `replace_tag_stream`, `replace_attr_stream`,
`tag_marginalia_stream`), which write a timestamped CSV changelog and post
modified pages back automatically.

---

## Main Functions & Classes

### **TrkbsClient**
- Handles Transkribus login and API calls over HTTPS.
- Reads credentials from arguments, environment variables, or a `.env` file.
- Methods:
  - `get_col_ids()`: List all collections (`{colName: colId}`).
  - `get_doc_ids(coll_id)`: List all documents in a collection (`{title: docId}`).
  - `get_page(coll_id, doc_id, page_nr)`: Fetch PAGE XML for a page.
  - `get_pages_stream(coll_id, doc_id, page_start, page_end)`: Yield `(page_nr, xml)` over a range.
  - `post_page(xml, coll_id, doc_id, page_nr)`: Upload modified PAGE XML (raises on HTTP error).
  - `get_metadata` / `get_page_nr` / `get_page_transcript_ids`: Document/page metadata helpers.

### **Tagging**
- `tag_heading(df_header, xml)` / `tag_heading_stream(...)`: Tag heading lines.
- `tag_empty_lines(xml)`, `add_regesta`, `remove_regesta`, `validate_regesta`: Regesta handling.
- `tag_marginalia(xml)` / `tag_marginalia_stream(...)`: Tag marginalia lines.
- `replace_tag` / `replace_tag_stream`, `replace_attr` / `replace_attr_stream`: Substitute custom-attribute tags/values.

### **Helpers**
- `find_months_in_text(text)`: Detect French month names in a string.
- `get_headings_by_page(df, page_nr)`: Look up reference headers for a page.
- `get_text(xml, regesta=False)`: Export plain text from PAGE XML.

---

## Development Notes

- Source code is in `src/trkbs_api/`.
- Add your own scripts/notebooks to process new documents as needed.
- Tests belong in the `tests/` folder (currently a stub).

---

## License

MIT

---

## Author

*Lev Shadrin* — lev.shadrin@uibk.ac.at

---

*Happy coding!*
