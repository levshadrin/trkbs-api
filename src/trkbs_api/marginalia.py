import re

from bs4 import BeautifulSoup as bsp

from ._streaming import run_stream
from ._tags import has_structure_type, structure_tag

IDX_RE = re.compile(r'readingOrder\s*\{[^}]*index:(\d+)\b', re.IGNORECASE) #reading order regex

def _get_reading_index(textline):
    m = IDX_RE.search(textline.get('custom', ''))
    return int(m.group(1)) if m else None

def _first_heading_index(soup, heading_tag):
    lines = soup.find_all('TextLine')
    heading_indices = [
        idx
        for l in lines
        if has_structure_type(l.get('custom'), heading_tag)
        for idx in (_get_reading_index(l),)
        if idx is not None
    ]
    return min(heading_indices) if heading_indices else None

def _append_marginalia(custom_value, snippet):
    # Append snippet once; keep spacing consistent
    if snippet in custom_value:
        return custom_value  # already tagged
    return (custom_value.rstrip() + snippet)


def tag_marginalia(xml, heading_tag='heading', marginalia_tag='marginalia'):
    soup = bsp(xml, 'xml')
    snippet = structure_tag(marginalia_tag)

    first_heading_idx = _first_heading_index(soup, heading_tag)
    if first_heading_idx is None:
        return (xml, [])

    diffs = []
    modified_any = False

    for textline in soup.find_all('TextLine'):
        if 'custom' not in textline.attrs:
            continue

        idx = _get_reading_index(textline)
        if idx is None:
            continue

        if idx < first_heading_idx:
            old_custom = textline['custom']
            new_custom = _append_marginalia(old_custom, snippet)

            if new_custom != old_custom:
                textline['custom'] = new_custom
                unicode_tag = textline.select_one('TextEquiv > Unicode')
                unicode_text = unicode_tag.text if unicode_tag else None
                line_id = textline.get('id', 'N/A')

                diffs.append({
                    'textline_id': line_id,
                    'old_custom': old_custom,
                    'new_custom': new_custom,
                    'unicode_text': unicode_text
                })
                modified_any = True

    return (str(soup), diffs) if modified_any else (xml, [])


def tag_marginalia_stream(
    client,
    coll_id,
    doc_id,
    output_log_path,
    page_start=1,
    page_end=None,
    heading_tag='heading',
    marginalia_tag='marginalia',
    continue_on_error=False,
):
    return run_stream(
        client, coll_id, doc_id, page_start, page_end,
        transform=lambda xml: tag_marginalia(xml, heading_tag, marginalia_tag),
        fieldnames=['page', 'textline_id', 'old_custom', 'new_custom', 'unicode_text'],
        output_log_path=output_log_path,
        continue_on_error=continue_on_error,
    )