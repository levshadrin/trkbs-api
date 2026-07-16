import logging
import re

from bs4 import BeautifulSoup as bsp

from ._streaming import run_stream

logger = logging.getLogger(__name__)


def replace_tag(xml, tag, repl):
    """Replace occurrences of ``tag`` with ``repl`` in every line's ``custom``.

    Note:
        ``tag`` is compiled as a **regular expression** for substitution, but a
        line is selected via a literal substring test (``tag in custom``). So a
        ``tag`` containing regex metacharacters — including the braces in
        Transkribus tags like ``{type:heading;}`` — behaves as a regex during the
        replace. Pass a regex-escaped pattern if you mean it literally. (A
        ``literal=True`` mode is planned for 0.3.)
    """
    soup = bsp(xml, 'xml')
    regex = re.compile(tag)
    for textline in soup.find_all('TextLine'):
        custom_attr = textline.get('custom')
        if tag in custom_attr:
            textline['custom'] = re.sub(regex, repl, textline['custom'])
            logger.debug('replace_tag: %s', textline['custom'])

    output_xml = str(soup)
    return output_xml


def _replace_tag_transform(xml, tag, replacement):
    """Return ``(updated_xml, diffs)`` for a single page's tag replacement."""
    soup = bsp(xml, 'xml')
    regex = re.compile(tag)
    diffs = []

    for textline in soup.find_all('TextLine'):
        if 'custom' not in textline.attrs:
            continue

        old_value = textline['custom']
        if tag not in old_value:
            continue

        new_value = re.sub(regex, replacement, old_value)
        if old_value != new_value:
            textline['custom'] = new_value
            unicode_tag = textline.select_one('TextEquiv > Unicode')
            unicode_text = unicode_tag.text if unicode_tag else None
            diffs.append({
                'textline_id': textline.get('id', 'N/A'),
                'old_value': old_value,
                'new_value': new_value,
                'unicode_text': unicode_text,
            })

    return (str(soup), diffs) if diffs else (xml, [])


def replace_tag_stream(client, coll_id, doc_id, tag, replacement, output_log_path, page_start, page_end):
    return run_stream(
        client, coll_id, doc_id, page_start, page_end,
        transform=lambda xml: _replace_tag_transform(xml, tag, replacement),
        fieldnames=['page', 'textline_id', 'old_value', 'new_value', 'unicode_text'],
        output_log_path=output_log_path,
    )


def replace_attr(xml, tag_name, attr_name, old_value, new_value):
    soup = bsp(xml, 'xml')
    tag_attr_pattern = re.compile(
        rf'({re.escape(tag_name)}\s*\{{[^}}]*{re.escape(attr_name)}:{re.escape(old_value)}[^}}]*\}})'
    )
    attr_value_pattern = re.compile(
        rf'({re.escape(attr_name)}:){re.escape(old_value)}'
    )

    modified_any = False
    diffs = []

    for textline in soup.find_all('TextLine'):
        custom = textline.get('custom')
        if not custom or tag_name not in custom or attr_name not in custom:
            continue

        if tag_attr_pattern.search(custom):
            old_custom = custom
            new_custom = attr_value_pattern.sub(rf'\1{new_value}', old_custom)
            if old_custom != new_custom:
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


def replace_attr_stream(client, coll_id, doc_id, tag_name, attr_name, old_value, new_value, output_log_path, page_start, page_end):
    return run_stream(
        client, coll_id, doc_id, page_start, page_end,
        transform=lambda xml: replace_attr(xml, tag_name, attr_name, old_value, new_value),
        fieldnames=['page', 'textline_id', 'old_custom', 'new_custom', 'unicode_text'],
        output_log_path=output_log_path,
    )
