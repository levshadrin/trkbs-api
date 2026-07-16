import re

from bs4 import BeautifulSoup as bsp

from ._tags import has_structure_type, structure_tag

def tag_empty_lines(xml, regesta_tag='regesta'):
    soup = bsp(xml, 'xml')
    snippet = structure_tag(regesta_tag)
    dup_re = re.compile(r'(' + re.escape(snippet) + r'){2,}')
    for unicode in soup.select('TextLine > TextEquiv > Unicode'):
        if not unicode.contents:
            text_line = unicode.find_parent('TextLine')
            custom_attr = text_line.get('custom')
            if not has_structure_type(custom_attr, regesta_tag):
                text_line['custom'] = custom_attr + snippet
            else:
                # Collapse any run of repeated regesta tags back to a single one.
                text_line['custom'] = dup_re.sub(snippet, custom_attr)
    output_xml = str(soup)

    return output_xml

def add_regesta(xml, regesta_text, regesta_tag='regesta'):
    soup = bsp(xml, 'xml')
    for unicode in soup.select('TextLine > TextEquiv > Unicode'):
        text_line = unicode.find_parent('TextLine')
        custom_attr = text_line.get('custom')
        if has_structure_type(custom_attr, regesta_tag) and not unicode.contents:
            unicode.string = regesta_text
    output_xml = str(soup)

    return output_xml