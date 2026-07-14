import re

from bs4 import BeautifulSoup as bsp

from ._streaming import run_stream

IDX_RE = re.compile(r'readingOrder\s*\{[^}]*index:(\d+)\b', re.IGNORECASE) #reading order regex

MARGINALIA_SNIPPET = ' structure {type:marginalia;}' #append payload for PAGE xml

def _get_reading_index(textline):
    custom = textline['custom']
    return int(IDX_RE.search(custom).group(1))

def _first_heading_index(soup):
    lines = soup.find_all('TextLine')
    heading_indices = [
        _get_reading_index(l)
        for l in lines
        if 'custom' in l.attrs and 'heading' in l['custom'].lower()
    ]
    return min(heading_indices) if heading_indices else None

def _append_marginalia(custom_value):
    # Append snippet once; keep spacing consistent
    if MARGINALIA_SNIPPET in custom_value:
        return custom_value  # already tagged
    return (custom_value.rstrip() + MARGINALIA_SNIPPET)


def tag_marginalia(xml):
    soup = bsp(xml, 'xml')

    first_heading_idx = _first_heading_index(soup)
    if first_heading_idx is None:
        return (xml, [])

    diffs = []
    modified_any = False

    for textline in soup.find_all('TextLine'):
        if 'custom' not in textline.attrs:
            continue

        try:
            idx = _get_reading_index(textline)
        except Exception:
            continue

        if idx < first_heading_idx:
            old_custom = textline['custom']
            new_custom = _append_marginalia(old_custom)

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
    page_start,
    page_end
):
    return run_stream(
        client, coll_id, doc_id, page_start, page_end,
        transform=tag_marginalia,
        fieldnames=['page', 'textline_id', 'old_custom', 'new_custom', 'unicode_text'],
        output_log_path=output_log_path,
    )