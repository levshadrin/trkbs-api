# SPDX-FileCopyrightText: 2025-present Lev Shadrin <lev.shadrin@uibk.ac.at>
#
# SPDX-License-Identifier: MIT
"""Offline test for the read-method HTTP status check (0.2.1 bugfix).

Builds a TrkbsClient without running __init__ (which would log in over the
network) and swaps in a fake session, so we can assert that an error response
now raises instead of being parsed as data.
"""
import pytest
import requests

from trkbs_api import TrkbsClient


class _FakeResponse:
    def __init__(self, status_code, text='', json_data=None):
        self.status_code = status_code
        self.text = text
        self._json = json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f'{self.status_code} Error')

    def json(self):
        return self._json


class _FakeSession:
    def __init__(self, response):
        self._response = response

    def get(self, url, timeout=None):
        return self._response


def test_get_num_pages_reads_metadata():
    client = _client_with_response(_FakeResponse(200, json_data={'nrOfPages': 7}))
    assert client.get_num_pages('coll', 'doc') == 7


def test_get_pages_stream_whole_document_when_page_end_none():
    # One fake response serves both get_num_pages (.json) and get_page (.text).
    client = _client_with_response(
        _FakeResponse(200, text='<PcGts/>', json_data={'nrOfPages': 3})
    )
    pages = [n for n, _ in client.get_pages_stream('coll', 'doc')]
    assert pages == [1, 2, 3]                 # page_start=1, page_end derived


def _client_with_response(response):
    client = TrkbsClient.__new__(TrkbsClient)  # skip __init__/login
    client.timeout = 30
    client.session = _FakeSession(response)
    return client


def test_get_page_raises_on_error_status():
    client = _client_with_response(
        _FakeResponse(401, text='<html>Session expired</html>')
    )
    # Before the fix this returned the error HTML unchanged.
    with pytest.raises(requests.HTTPError):
        client.get_page('coll', 'doc', 1)


def test_get_page_returns_text_on_success():
    client = _client_with_response(_FakeResponse(200, text='<PcGts/>'))
    assert client.get_page('coll', 'doc', 1) == '<PcGts/>'


def test_get_page_pretty_indents_only_when_requested():
    compact = '<a><b>text</b></a>'
    client = _client_with_response(_FakeResponse(200, text=compact))
    # Default: raw server bytes, unchanged (the write path relies on this).
    assert client.get_page('coll', 'doc', 1) == compact
    # Opt-in: indented for reading.
    pretty = client.get_page('coll', 'doc', 1, pretty=True)
    assert '\n' in pretty and '  <b>text</b>' in pretty
