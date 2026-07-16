"""Helpers for reading and writing Transkribus ``custom``-attribute structural tags.

A structural tag looks like ``structure {type:heading;}`` inside a ``<TextLine>``'s
``custom`` attribute. Matching on the exact ``type`` token (rather than a bare
substring) keeps a tag name from being confused with a longer one — ``heading``
must not match ``subheading`` — while still letting callers use their own
vocabulary via a configurable name.
"""
import re


def has_structure_type(custom, type_name):
    """Return True if ``custom`` carries a ``structure {type:<type_name>;}`` tag.

    The ``type`` token must be terminated by ``;`` or ``}``, so ``'heading'``
    does not match ``'subheading'`` or ``'heading2'``. ``custom`` may be ``None``.
    """
    if not custom:
        return False
    return re.search(r'\btype:' + re.escape(type_name) + r'\s*[;}]', custom) is not None


def structure_tag(type_name):
    """Return the ``custom`` snippet (with leading space) that tags a line."""
    return f' structure {{type:{type_name};}}'
