import re

from bs4 import BeautifulSoup as bsp

from ._streaming import run_stream
from ._tags import has_structure_type, structure_tag

MONTH_NAMES_FR = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
]


## refactor with less restrictive data structure
def get_headings_by_page(df, page_nr):
    row = df.loc[df['page_nr'] == page_nr]
    if not row.empty:
        return [row['header_1'].values[0], row['header_2'].values[0]]
    else:
        return []


def find_months_in_text(text, months=MONTH_NAMES_FR, ignore_case=True):
    flags = re.IGNORECASE if ignore_case else 0
    return [m for m in months if re.search(r'\b' + re.escape(m) + r'\b', text, flags)]


## v 0.2
def header_string_lookup(df, string):
    return bool(df['text'].str.fullmatch(re.escape(string)).any())  # re.escape() to deal with escape chars


def tag_heading(df_header, xml, heading_tag='heading', regesta_tag='regesta'):
    soup = bsp(xml, 'xml')
    snippet = structure_tag(heading_tag)
    modified = False
    lines_tagged = []
    for unicode in soup.select('TextLine > TextEquiv > Unicode'):
        string = unicode.string
        if string and header_string_lookup(df_header, string):
            text_line = unicode.find_parent('TextLine')
            custom_attr = text_line.get('custom')
            if not has_structure_type(custom_attr, heading_tag) and \
                    not has_structure_type(custom_attr, regesta_tag):
                text_line['custom'] = custom_attr + snippet
                lines_tagged.append({'textline': string})
                modified = True
        else:
            continue
    output_xml = str(soup)

    return (output_xml, lines_tagged) if modified else (xml, [])


def tag_heading_stream(client, coll_id, doc_id, df_header, output_log_path,
                       page_start=1, page_end=None, heading_tag='heading',
                       regesta_tag='regesta', continue_on_error=False):
    return run_stream(
        client, coll_id, doc_id, page_start, page_end,
        transform=lambda xml: tag_heading(df_header, xml, heading_tag, regesta_tag),
        fieldnames=['page', 'textline'],
        output_log_path=output_log_path,
        continue_on_error=continue_on_error,
    )
