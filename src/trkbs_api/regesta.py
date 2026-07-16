import re
import warnings

from bs4 import BeautifulSoup as bsp
from tqdm import tqdm

REGESTA_DUP_RE = re.compile(r'(\sstructure {type:regesta;}){2,}')

def tag_empty_lines(xml):
    soup = bsp(xml, 'xml')
    for unicode in soup.select('TextLine > TextEquiv > Unicode'):
        if not unicode.contents:
            text_line = unicode.find_parent('TextLine')
            custom_attr = text_line.get('custom')
            if 'type:regesta' not in text_line['custom']:
                text_line['custom'] =  custom_attr + ' structure {type:regesta;}'
            else:
                # Collapse any run of repeated regesta tags back to a single one.
                text_line['custom'] = REGESTA_DUP_RE.sub(
                    ' structure {type:regesta;}', text_line['custom']
                )
    output_xml = str(soup)

    return output_xml

def remove_regesta(xml):
    """Delete every ``<TextLine>`` tagged ``regesta`` from the page.

    .. deprecated::
        Destructive: ``decompose()`` removes the whole line (geometry + text),
        not just the tag, and damages reading order. Use
        ``get_text(xml, regesta=False)`` (``export.py``) to exclude regesta from
        a transcription non-destructively. Scheduled for removal in 0.3.
    """
    warnings.warn(
        'remove_regesta is deprecated and will be removed in 0.3; '
        'use get_text(xml, regesta=False) to exclude regesta non-destructively.',
        DeprecationWarning,
        stacklevel=2,
    )
    soup = bsp(xml, 'xml')
    for unicode in soup.select('TextLine > TextEquiv > Unicode'):
        text_line = unicode.find_parent('TextLine')
        custom_attr = text_line.get('custom')
        if 'regesta' in custom_attr:
            text_line.decompose()
    output_xml = str(soup)
        
    return output_xml

def add_regesta(xml, regesta_text):
    soup = bsp(xml, 'xml')
    for unicode in soup.select('TextLine > TextEquiv > Unicode'):
        text_line = unicode.find_parent('TextLine')
        custom_attr = text_line.get('custom')
        if 'regesta' in custom_attr and not unicode.contents:
            unicode.string = regesta_text
    output_xml = str(soup)
            
    return output_xml

def validate_regesta(client, coll, doc, page_start, page_end):
    reg_dict = {}
    for i in tqdm(range(page_start, page_end + 1)):
        xml = client.get_page(coll, doc, i)
        soup = bsp(xml, 'xml')
        reg_counter = 0
        for unicode in soup.select('TextLine > TextEquiv > Unicode'):
            text_line = unicode.find_parent('TextLine')
            custom_attr = text_line.get('custom')
            if 'regesta' in custom_attr:
                reg_counter += 1
                reg_dict.update({f'Page_{i}': f'{reg_counter}'})
    
    return reg_dict