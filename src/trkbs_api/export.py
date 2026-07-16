from bs4 import BeautifulSoup as bsp
from lxml import etree

from ._tags import has_structure_type


def format_page_xml(xml):
    """Return an indented, human-readable copy of a PAGE-XML string.

    Transkribus serves PAGE XML compact (single-line) as of platform 2.47.0; this
    re-indents it for reading. Uses lxml (the same parser backing
    ``BeautifulSoup(..., 'xml')`` elsewhere): structural elements are indented
    while text-bearing elements such as ``<Unicode>`` stay intact on one line.

    View-only. Re-serialization adds inter-element whitespace, so **never** feed
    the result to ``post_page`` — round-trip the raw ``get_page`` output for
    writes instead.
    """
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(xml.encode('utf-8'), parser)
    return etree.tostring(
        root, pretty_print=True, xml_declaration=True, encoding='UTF-8'
    ).decode('utf-8')


# basic text export with 'regesta' flag (dependant on TRKBS structural tagging)
def get_text(xml, regesta=False, regesta_tag='regesta'):
    soup = bsp(xml, 'xml')
    line_list = []
    for unicode in soup.select('TextLine > TextEquiv > Unicode'):
        string = unicode.string
        text_line = unicode.find_parent('TextLine')
        custom_attr = text_line.get('custom')
        if regesta == False:
            if not has_structure_type(custom_attr, regesta_tag):
                line_list.append(string)
        else:
            line_list.append(string)

    line_list = [x for x in line_list if x is not None]        

    return '\n'.join(line_list)