"""Edit Transkribus semantic tags in PAGE XML.

This module handles tag-level mutations (rename) and low-level string edits.
Read-only queries are in search.py.

IMPORTANT: The raw-regex functions (replace_tag, replace_attr) are unsafe for
renaming tags or properties—use replace_tag_name instead. They are kept as an
escape hatch for cases where the parsing model is insufficient.
"""

import logging
import re

from bs4 import BeautifulSoup as bsp

from ._streaming import run_stream
from ._custom import iter_blocks

logger = logging.getLogger(__name__)


def replace_tag(xml, tag, repl, literal=False):
    """Replace occurrences of ``tag`` with ``repl`` in every line's ``custom``.

    **UNSAFE for tag name replacement.** Use replace_tag_name() instead.
    This function is an unscoped regex over the entire custom attribute, so the
    tag name can match inside property keys, e.g. ``place`` → ``placeName`` will
    also rewrite ``placeName:value`` to ``placeNameName:value``.

    ``tag`` is treated as a **regular expression** by default. Pass
    ``literal=True`` to match ``tag`` verbatim (it is ``re.escape``-d), which is
    what you want for Transkribus tags containing braces, e.g. ``{type:heading;}``.

    Returns the original XML unchanged if nothing matched (S3 round-trip guard).
    """
    soup = bsp(xml, 'xml')
    regex = re.compile(re.escape(tag) if literal else tag)
    modified_any = False

    for textline in soup.find_all('TextLine'):
        custom_attr = textline.get('custom')
        if custom_attr and regex.search(custom_attr):
            textline['custom'] = regex.sub(repl, custom_attr)
            logger.debug('replace_tag: %s', textline['custom'])
            modified_any = True

    if not modified_any:
        return xml

    output_xml = str(soup)
    return output_xml


def _replace_tag_transform(xml, tag, replacement, literal=False):
    """Return ``(updated_xml, diffs)`` for a single page's tag replacement.

    Note: still unsafe for tag names; this is internal to replace_tag_stream.
    """
    soup = bsp(xml, 'xml')
    regex = re.compile(re.escape(tag) if literal else tag)
    diffs = []

    for textline in soup.find_all('TextLine'):
        if 'custom' not in textline.attrs:
            continue

        old_value = textline['custom']
        if not regex.search(old_value):
            continue

        new_value = regex.sub(replacement, old_value)
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


def replace_tag_stream(client, coll_id, doc_id, tag, replacement, output_log_path,
                       page_start=1, page_end=None, literal=False, continue_on_error=False):
    """Apply replace_tag across a page range, logging changes to a CSV.

    **UNSAFE for tag name replacement.** Use replace_tag_name_stream instead.
    """
    return run_stream(
        client, coll_id, doc_id, page_start, page_end,
        transform=lambda xml: _replace_tag_transform(xml, tag, replacement, literal),
        fieldnames=['page', 'textline_id', 'old_value', 'new_value', 'unicode_text'],
        output_log_path=output_log_path,
        continue_on_error=continue_on_error,
    )


def replace_tag_name(xml, old_name, new_name):
    """Safely rename a tag name across all blocks in a page.

    Unlike replace_tag, this operates on the parsed tag model, so 'place' will
    rename only the tag block name, not substring matches in property keys like
    'placeName:Karlsruhe'.

    Returns ``(updated_xml, diffs)`` where diffs is a list of changed line records.
    Returns the original XML unchanged if nothing matched (S3 round-trip guard).
    """
    soup = bsp(xml, 'xml')
    diffs = []

    for textline in soup.find_all('TextLine'):
        custom_attr = textline.get('custom')
        if not custom_attr:
            continue

        blocks = iter_blocks(custom_attr)
        new_blocks = []
        any_changed = False

        for block in blocks:
            if block.name == old_name:
                new_blocks.append(f'{new_name} {{{block.properties_raw}}}')
                any_changed = True
            else:
                new_blocks.append(f'{block.name} {{{block.properties_raw}}}')

        if any_changed:
            old_custom = custom_attr
            new_custom = ' '.join(new_blocks)
            textline['custom'] = new_custom

            unicode_tag = textline.select_one('TextEquiv > Unicode')
            unicode_text = unicode_tag.text if unicode_tag else None

            diffs.append({
                'textline_id': textline.get('id', 'N/A'),
                'old_custom': old_custom,
                'new_custom': new_custom,
                'unicode_text': unicode_text,
            })

    if not diffs:
        return (xml, [])

    output_xml = str(soup)
    return (output_xml, diffs)


def replace_tag_name_stream(client, coll_id, doc_id, old_name, new_name, output_log_path,
                            page_start=1, page_end=None, continue_on_error=False):
    """Apply replace_tag_name across a page range, logging changes to a CSV."""
    return run_stream(
        client, coll_id, doc_id, page_start, page_end,
        transform=lambda xml: replace_tag_name(xml, old_name, new_name),
        fieldnames=['page', 'textline_id', 'old_custom', 'new_custom', 'unicode_text'],
        output_log_path=output_log_path,
        continue_on_error=continue_on_error,
    )


def replace_attr(xml, tag_name, attr_name, old_value, new_value):
    """Replace a property value within a specific tag block.

    **UNSAFE.** The substitution is still unscoped to the target block—it rewrites
    all occurrences of the value everywhere in the custom attribute. Use with caution.

    Returns ``(updated_xml, diffs)`` or (original xml, []) if nothing matched (S3 guard).
    """
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


def replace_attr_stream(client, coll_id, doc_id, tag_name, attr_name, old_value, new_value,
                        output_log_path, page_start=1, page_end=None, continue_on_error=False):
    """Apply replace_attr across a page range, logging changes to a CSV."""
    return run_stream(
        client, coll_id, doc_id, page_start, page_end,
        transform=lambda xml: replace_attr(xml, tag_name, attr_name, old_value, new_value),
        fieldnames=['page', 'textline_id', 'old_custom', 'new_custom', 'unicode_text'],
        output_log_path=output_log_path,
        continue_on_error=continue_on_error,
    )
