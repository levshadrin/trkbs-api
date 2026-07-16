# SPDX-FileCopyrightText: 2025-present Lev Shadrin <lev.shadrin@uibk.ac.at>
#
# SPDX-License-Identifier: MIT
"""Offline tests for count_tag_by_page and run_stream, using a mock client."""
import pytest
import requests

from trkbs_api import count_tag_by_page
from trkbs_api._streaming import run_stream


def _page(textlines):
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<PcGts><Page><TextRegion>' + ''.join(textlines) + '</TextRegion></Page></PcGts>'
    )


def _line(custom, text=''):
    return (
        f'<TextLine id="l" custom="{custom}">'
        f'<TextEquiv><Unicode>{text}</Unicode></TextEquiv></TextLine>'
    )


class MockClient:
    def __init__(self, pages, fail_pages=()):
        self.pages = pages                 # {page_nr: xml}
        self.fail_pages = set(fail_pages)
        self.posted = []

    def get_num_pages(self, coll, doc):
        return len(self.pages)

    def get_page(self, coll, doc, page_nr):
        return self.pages[page_nr]

    def get_pages_stream(self, coll, doc, page_start=1, page_end=None):
        if page_end is None:
            page_end = self.get_num_pages(coll, doc)
        for n in range(page_start, page_end + 1):
            yield n, self.get_page(coll, doc, n)

    def post_page(self, xml, coll, doc, page_nr):
        if page_nr in self.fail_pages:
            raise requests.HTTPError(f'page {page_nr} failed')
        self.posted.append(page_nr)


def test_count_tag_by_page_includes_zero_pages():
    client = MockClient({
        1: _page([_line('structure {type:regesta;}'), _line('structure {type:regesta;}')]),
        2: _page([_line('readingOrder {index:0;}')]),   # no regesta
    })
    counts = count_tag_by_page(client, 'c', 'd', 1, 2, 'regesta')
    assert counts == {'Page_1': 2, 'Page_2': 0}         # zero-count page present


def _one_diff_per_page(xml):
    # Every page "changes": one diff row, so post_page is always attempted.
    return xml, [{'val': 'x'}]


def test_run_stream_fail_fast_aborts(tmp_path):
    client = MockClient({1: '<a/>', 2: '<a/>', 3: '<a/>'}, fail_pages={2})
    with pytest.raises(requests.HTTPError):
        run_stream(client, 'c', 'd', 1, 3, _one_diff_per_page,
                   ['page', 'val'], str(tmp_path))
    assert client.posted == [1]                          # stopped at the failure


def test_run_stream_continue_on_error_skips_and_returns_path(tmp_path):
    client = MockClient({1: '<a/>', 2: '<a/>', 3: '<a/>'}, fail_pages={2})
    result = run_stream(client, 'c', 'd', 1, 3, _one_diff_per_page,
                        ['page', 'val'], str(tmp_path), continue_on_error=True)
    assert isinstance(result, str) and result.endswith('.csv')  # still returns a path
    assert client.posted == [1, 3]                       # page 2 skipped, run continued
