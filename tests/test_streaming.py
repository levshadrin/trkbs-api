# SPDX-FileCopyrightText: 2025-present Lev Shadrin <lev.shadrin@uibk.ac.at>
#
# SPDX-License-Identifier: MIT
"""Offline tests for count_tag_by_page and run_stream, using a mock client."""
import pytest
import requests

from trkbs_api import count_tag_by_page
from trkbs_api._streaming import iter_pages, run_stream


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
        self.num_pages_calls = 0

    def get_num_pages(self, coll, doc):
        self.num_pages_calls += 1
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


def test_iter_pages_resolves_page_end_without_extra_request():
    """page_end=None is resolved once, not once here and again in the stream."""
    client = MockClient({1: '<a/>', 2: '<a/>', 3: '<a/>'})
    pages = list(iter_pages(client, 'c', 'd', 1, None, progress=False))
    assert [n for n, _ in pages] == [1, 2, 3]
    assert client.num_pages_calls == 1


def test_iter_pages_progress_flag_controls_output(capsys):
    """progress=False silences the bar; the default still draws one."""
    client = MockClient({1: '<a/>', 2: '<a/>'})

    list(iter_pages(client, 'c', 'd', 1, 2, desc='Quiet', progress=False))
    assert capsys.readouterr().err == ''

    list(iter_pages(client, 'c', 'd', 1, 2, desc='Loud', progress=True))
    assert 'Loud' in capsys.readouterr().err


def test_iter_pages_bar_knows_its_total(capsys):
    """The bar shows a percentage, not a bare 'Npage [..]' counter."""
    client = MockClient({1: '<a/>', 2: '<a/>', 3: '<a/>', 4: '<a/>'})
    list(iter_pages(client, 'c', 'd', 1, None, desc='Counting', progress=True))
    err = capsys.readouterr().err
    assert '4/4' in err and '100%' in err


def test_count_tag_by_page_accepts_page_end_none():
    client = MockClient({
        1: _page([_line('structure {type:regesta;}')]),
        2: _page([_line('readingOrder {index:0;}')]),
    })
    counts = count_tag_by_page(client, 'c', 'd', 1, None, 'regesta', progress=False)
    assert counts == {'Page_1': 1, 'Page_2': 0}


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
