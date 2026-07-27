"""Validation helpers that page through a document counting structural tags."""
from bs4 import BeautifulSoup as bsp

from ._streaming import iter_pages
from ._tags import has_structure_type


def count_tag_by_page(client, coll_id, doc_id, page_start, page_end, tag,
                      progress=True):
    """Count lines carrying ``structure {type:<tag>}`` on each page in a range.

    **This function counts structural tags only** (``structure {type:heading}``, etc.).
    For a general tag inventory across all 17 tag names, use ``count_tags`` or
    ``count_tags_by_page`` from the search module instead.

    Returns a dict ``{'Page_<n>': count}`` covering **every** page in
    ``[page_start, page_end]``, including pages with a count of ``0`` (the old
    ``validate_headings`` / ``validate_regesta`` omitted zero-count pages).
    ``page_end=None`` runs to the end of the document.

    ``tag`` is the structural tag name to count, e.g. ``'heading'`` or
    ``'regesta'``. ``progress`` set False suppresses the progress bar.
    """
    counts = {}
    for page_nr, xml in iter_pages(client, coll_id, doc_id, page_start, page_end,
                                   desc=f'Counting {tag}', progress=progress):
        soup = bsp(xml, 'xml')
        n = sum(
            1
            for unicode in soup.select('TextLine > TextEquiv > Unicode')
            if has_structure_type(
                unicode.find_parent('TextLine').get('custom'), tag
            )
        )
        counts[f'Page_{page_nr}'] = n
    return counts
