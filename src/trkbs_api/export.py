from bs4 import BeautifulSoup as bsp
from lxml import etree
import re

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
def get_text(xml, cleanup=False, flatten=True, regesta=False, regesta_tag='regesta'):
    """Extract the reading text from a PAGE-XML string.

    ``cleanup`` rejoins words hyphenated across line breaks (the ``¬``
    continuation sign) and collapses runs of spaces/tabs. ``flatten`` (on by
    default) folds the remaining line breaks into single spaces, yielding one
    continuous line; set it to ``False`` to keep one line per ``<TextLine>``.
    ``regesta`` includes lines tagged ``structure {type:<regesta_tag>;}``,
    which are dropped by default.
    """
    soup = bsp(xml, 'xml')
    line_list = []
    for unicode in soup.select('TextLine > TextEquiv > Unicode'):
        string = unicode.string
        if string is None:
            continue
        custom_attr = unicode.find_parent('TextLine').get('custom')
        if regesta or not has_structure_type(custom_attr, regesta_tag):
            line_list.append(string)

    text = '\n'.join(line_list)

    replacements = []
    if cleanup:
        replacements.append((r'¬\s*', ''))     # rejoin words split across lines
    if flatten:
        replacements.append((r'\n', ' '))       # fold line breaks into spaces
    if cleanup:
        replacements.append((r'[ \t]+', ' '))   # collapse runs of spaces/tabs
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)

    return text