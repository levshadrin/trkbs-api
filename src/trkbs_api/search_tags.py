"""Find and inspect Transkribus semantic tags in PAGE XML.

Main scenario: `find_tags_by_page(client, coll_id, doc_id, tag='person', text=r'Μ[ιί]λλ[εέ]ρ.+')` —
"has Μίλλερ been tagged as person everywhere it occurs in this document?"

Secondary: `count_tags(xml)` / `count_tags_by_page(...)` — editorial validation, e.g.
"expected 2 person tags on this page, found only 1".
"""

import re
from dataclasses import dataclass
from collections import Counter

from bs4 import BeautifulSoup as bsp
from tqdm import tqdm

from ._custom import iter_blocks


@dataclass(frozen=True)
class TagInstance:
    """A single resolved tag instance from a TextLine's custom attribute.

    L1 = transcription text (in source language, e.g. Greek)
    L2 = tag annotation (name + offset/length anchor)
    L3 = normalised/authority properties (opaque at this revision)
    """
    tag: str              # L2 block name (e.g. 'person', 'place')
    offset: int | None    # None for unanchored (readingOrder, structure)
    length: int | None
    text: str | None      # L1 resolved token; None if unanchored or no Unicode
    properties_raw: str   # L3 opaque
    line_id: str | None   # <TextLine id="...">
    page: int | None      # stamped by document-level driver
    custom: str           # full custom attribute, for context


def find_tags(xml: str, tag: str | None = None, text: str | None = None, flags: int = 0) -> list[TagInstance]:
    """Find tag instances on a single page.

    Args:
        xml: PAGE XML string of one page.
        tag: exact tag name to match (e.g. 'person'), or None for all tags.
        text: regex pattern to match against resolved L1 tokens (ignored if tag has no offset/length).
        flags: re.IGNORECASE etc., passed to re.compile.

    Returns:
        List of TagInstance, one per matched block.
        Instances without resolvable text (unanchored or no Unicode) have text=None.
    """
    soup = bsp(xml, 'xml')
    instances = []

    for textline in soup.find_all('TextLine'):
        custom_attr = textline.get('custom')
        line_id = textline.get('id')
        unicode_elem = textline.select_one('TextEquiv > Unicode')
        unicode_text = unicode_elem.get_text() if unicode_elem else None

        for block in iter_blocks(custom_attr):
            # Filter by tag name if specified
            if tag is not None and block.name != tag:
                continue

            # Resolve the L1 token
            resolved_text = None
            if block.offset is not None and block.length is not None and unicode_text is not None:
                resolved_text = unicode_text[block.offset:block.offset + block.length]

            # Filter by text pattern if specified (skip unanchored)
            if text is not None:
                if resolved_text is None:
                    continue
                if not re.search(text, resolved_text, flags):
                    continue

            instances.append(TagInstance(
                tag=block.name,
                offset=block.offset,
                length=block.length,
                text=resolved_text,
                properties_raw=block.properties_raw,
                line_id=line_id,
                page=None,  # stamped by find_tags_by_page
                custom=custom_attr or ''
            ))

    return instances


def find_tags_by_page(client, coll_id: int, doc_id: int, tag: str | None = None,
                      text: str | None = None, page_start: int = 1, page_end: int | None = None,
                      flags: int = 0) -> list[TagInstance]:
    """Find tag instances across a page range.

    Args:
        client: authenticated TrkbsClient.
        coll_id, doc_id: Transkribus collection and document IDs.
        tag, text, flags: as find_tags.
        page_start, page_end: inclusive page range; page_end=None streams to end of document.

    Returns:
        List of TagInstance with page stamped.
    """
    instances = []

    for page_nr, page_xml in tqdm(
        client.get_pages_stream(coll_id, doc_id, page_start, page_end),
        desc=f"Searching {coll_id}/{doc_id}",
        unit="page"
    ):
        for inst in find_tags(page_xml, tag=tag, text=text, flags=flags):
            instances.append(TagInstance(
                tag=inst.tag,
                offset=inst.offset,
                length=inst.length,
                text=inst.text,
                properties_raw=inst.properties_raw,
                line_id=inst.line_id,
                page=page_nr,
                custom=inst.custom
            ))

    return instances


def count_tags(xml: str) -> dict[str, int]:
    """Count tag instances by name on a single page.

    Returns a dict mapping tag names to counts. Used for editorial validation:
    "expected 2 person tags on this page, found only 1?"

    Does not distinguish unanchored tags (readingOrder) from anchored ones.
    """
    return dict(Counter(inst.tag for inst in find_tags(xml)))


def count_tags_by_page(client, coll_id: int, doc_id: int, page_start: int = 1,
                       page_end: int | None = None) -> dict[int, dict[str, int]]:
    """Count tag instances by name across a page range.

    Returns a dict mapping page number to count dict. Used for editorial validation
    across a batch, e.g. to spot under-tagged pages.
    """
    counts = {}

    for page_nr, page_xml in tqdm(
        client.get_pages_stream(coll_id, doc_id, page_start, page_end),
        desc=f"Counting {coll_id}/{doc_id}",
        unit="page"
    ):
        counts[page_nr] = count_tags(page_xml)

    return counts
