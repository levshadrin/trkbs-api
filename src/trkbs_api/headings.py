import re

from bs4 import BeautifulSoup as bsp
from tqdm import tqdm

from ._streaming import run_stream

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


def find_months_in_text(text, months=MONTH_NAMES_FR):
    return [m for m in months if re.search(r'\b' + re.escape(m) + r'\b', text)]


def validate_headings(client, coll, doc, page_start, page_end):
    heading_dict = {}
    for i in tqdm(range(page_start, page_end + 1)):
        xml = client.get_page(coll, doc, i)
        soup = bsp(xml, 'xml')
        heading_counter = 0
        for unicode in soup.select('TextLine > TextEquiv > Unicode'):
            text_line = unicode.find_parent('TextLine')
            custom_attr = text_line.get('custom')
            if 'heading' in custom_attr:
                heading_counter += 1
                heading_dict.update({f'Page_{i}': f'{heading_counter}'})

    return heading_dict


## v 0.2
def header_string_lookup(df, string):
    return bool(df['text'].str.fullmatch(re.escape(string)).any())  # re.escape() to deal with escape chars


def tag_heading(df_header, xml):
    soup = bsp(xml, 'xml')
    modified = False
    lines_tagged = []
    for unicode in soup.select('TextLine > TextEquiv > Unicode'):
        string = unicode.string
        if string and header_string_lookup(df_header, string):
            text_line = unicode.find_parent('TextLine')
            custom_attr = text_line.get('custom')
            if 'type:heading' not in custom_attr and 'type:regesta' not in custom_attr:
                text_line['custom'] = custom_attr + ' structure {type:heading;}'
                lines_tagged.append({'textline': string})
                modified = True
        else:
            continue
    output_xml = str(soup)

    return (output_xml, lines_tagged) if modified else (xml, [])


def tag_heading_stream(client, coll_id, doc_id, df_header, output_log_path, page_start, page_end):
    return run_stream(
        client, coll_id, doc_id, page_start, page_end,
        transform=lambda xml: tag_heading(df_header, xml),
        fieldnames=['page', 'textline'],
        output_log_path=output_log_path,
    )
