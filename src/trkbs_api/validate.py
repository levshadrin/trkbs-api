"""Validation helpers that page through a document counting structural tags."""
from bs4 import BeautifulSoup as bsp
from tqdm import tqdm

from ._tags import has_structure_type


def count_tag_by_page(client, coll_id, doc_id, page_start, page_end, tag):
    """Count lines carrying ``structure {type:<tag>}`` on each page in a range.

    Returns a dict ``{'Page_<n>': count}`` covering **every** page in
    ``[page_start, page_end]``, including pages with a count of ``0`` (the old
    ``validate_headings`` / ``validate_regesta`` omitted zero-count pages).

    ``tag`` is the structural tag name to count, e.g. ``'heading'`` or
    ``'regesta'``.
    """
    counts = {}
    for i in tqdm(range(page_start, page_end + 1)):
        soup = bsp(client.get_page(coll_id, doc_id, i), 'xml')
        n = sum(
            1
            for unicode in soup.select('TextLine > TextEquiv > Unicode')
            if has_structure_type(
                unicode.find_parent('TextLine').get('custom'), tag
            )
        )
        counts[f'Page_{i}'] = n
    return counts
