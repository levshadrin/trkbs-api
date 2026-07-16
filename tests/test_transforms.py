# SPDX-FileCopyrightText: 2025-present Lev Shadrin <lev.shadrin@uibk.ac.at>
#
# SPDX-License-Identifier: MIT
"""Offline unit tests for the pure XML/DataFrame transforms.

These exercise the 0.2.1 fixes without any Transkribus credentials or network:
every function under test operates on PAGE-XML strings or DataFrames in memory.
"""
import warnings

import pandas as pd
import pytest

from trkbs_api import (
    tag_marginalia,
    tag_empty_lines,
    header_string_lookup,
    remove_regesta,
)


def _page(textlines):
    """Wrap TextLine XML fragments in a minimal PAGE document."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<PcGts><Page><TextRegion>'
        + ''.join(textlines)
        + '</TextRegion></Page></PcGts>'
    )


def _line(custom, text=''):
    return (
        f'<TextLine id="l1" custom="{custom}">'
        f'<TextEquiv><Unicode>{text}</Unicode></TextEquiv>'
        f'</TextLine>'
    )


# --- Bugfix 1: marginalia crash on a heading line without a reading index ----

def test_tag_marginalia_heading_without_reading_index_does_not_crash():
    # 'heading' present in custom but no `readingOrder {index:...}` token.
    xml = _page([_line('structure {type:heading;}', 'Chapitre I')])
    # Before the fix this raised AttributeError inside _first_heading_index.
    out_xml, diffs = tag_marginalia(xml)
    assert diffs == []
    assert out_xml == xml  # unchanged: no usable heading index -> nothing tagged


def test_tag_marginalia_tags_lines_before_first_heading():
    xml = _page([
        _line('readingOrder {index:0;}', 'note in the margin'),
        _line('readingOrder {index:1;} structure {type:heading;}', 'Chapitre I'),
        _line('readingOrder {index:2;}', 'body text'),
    ])
    out_xml, diffs = tag_marginalia(xml)
    assert len(diffs) == 1
    assert 'type:marginalia' in diffs[0]['new_custom']
    assert 'type:marginalia' in out_xml


# --- Bugfix 3: header_string_lookup returns a real bool -----------------------

def test_header_string_lookup_returns_bool():
    df = pd.DataFrame({'text': ['Janvier', 'Février']})
    assert header_string_lookup(df, 'Janvier') is True
    # Previously returned None (falsy) rather than False on no match.
    assert header_string_lookup(df, 'Mars') is False


# --- Tweak: regesta dedup collapses a repeated tag run ------------------------

def test_tag_empty_lines_collapses_duplicate_regesta_tags():
    doubled = ('base structure {type:regesta;} '
               'structure {type:regesta;} structure {type:regesta;}')
    xml = _page([_line(doubled, '')])  # empty Unicode -> hits the dedup branch
    out_xml = tag_empty_lines(xml)
    assert out_xml.count('structure {type:regesta;}') == 1


# --- Tweak: remove_regesta warns (deprecated) --------------------------------

def test_remove_regesta_emits_deprecation_warning():
    xml = _page([_line('structure {type:regesta;}', 'x')])
    with pytest.warns(DeprecationWarning):
        remove_regesta(xml)
