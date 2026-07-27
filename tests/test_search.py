"""Tests for the search module (find_tags, count_tags, etc.)."""

import pytest
from bs4 import BeautifulSoup as bsp

from trkbs_api import TagInstance, find_tags, count_tags


@pytest.fixture
def ref_page():
    """Reference page: 56612907.xml line 45 (Karlsruhe / Heunisch).

    Unicode text: τοῦ ἐκ τοῦ Καρλσροῦε Χεύνισχ, θέλοντος ἔχειν τὰ ὑπ' ἐμοῦ ὑπη¬
    """
    # The ¬ character (U+00AC, not-sign) is at the end, representing a line break marker
    xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15">
    <Page>
        <TextRegion id="tr_1">
            <TextLine id="tl_1768563062" custom="readingOrder {index:4;} place {offset:11; length:9;placeName:Karlsruhe;} person {offset:21; length:7;notice:https://de.wikipedia.org/wiki/Karl_Friedrich_Heunisch; dateofbirth:1806; firstname: Karl Friedrich ; dateofdeath:1860; lastname:Heunisch;}">
                <TextEquiv><Unicode>τοῦ ἐκ τοῦ Καρλσροῦε Χεύνισχ, θέλοντος ἔχειν τὰ ὑπ' ἐμοῦ ὑπη¬</Unicode></TextEquiv>
            </TextLine>
        </TextRegion>
    </Page>
</PcGts>'''
    return xml


@pytest.fixture
def page_no_custom():
    """Page with a TextLine lacking custom attribute."""
    xml = '''<?xml version="1.0"?>
<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15">
    <Page>
        <TextRegion>
            <TextLine id="l1">
                <TextEquiv><Unicode>some text</Unicode></TextEquiv>
            </TextLine>
        </TextRegion>
    </Page>
</PcGts>'''
    return xml


@pytest.fixture
def page_no_unicode():
    """Page with a TextLine lacking TextEquiv/Unicode."""
    xml = '''<?xml version="1.0"?>
<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15">
    <Page>
        <TextRegion>
            <TextLine id="l1" custom="readingOrder {index:0;}">
            </TextLine>
        </TextRegion>
    </Page>
</PcGts>'''
    return xml


class TestFindTags:
    """Tests for find_tags (single-page queries)."""

    def test_parse_coverage(self, ref_page):
        """All blocks on the reference page should parse."""
        all_tags = find_tags(ref_page)
        tag_names = [t.tag for t in all_tags]
        assert 'readingOrder' in tag_names
        assert 'place' in tag_names
        assert 'person' in tag_names
        assert len(all_tags) == 3

    def test_offset_invariant(self, ref_page):
        """Offset + length should never exceed text length."""
        soup = bsp(ref_page, 'xml')
        unicode_elem = soup.select_one('TextEquiv > Unicode')
        unicode_text = unicode_elem.get_text()

        for inst in find_tags(ref_page):
            if inst.offset is not None and inst.length is not None and inst.text is not None:
                expected = unicode_text[inst.offset:inst.offset + inst.length]
                assert inst.text == expected

    def test_m2_resolution(self, ref_page):
        """M2: resolve L1 token correctly."""
        place_inst = next((t for t in find_tags(ref_page) if t.tag == 'place'), None)
        assert place_inst is not None
        assert place_inst.text == 'Καρλσροῦε'

        person_inst = next((t for t in find_tags(ref_page) if t.tag == 'person'), None)
        assert person_inst is not None
        assert person_inst.text == 'Χεύνισχ'

    def test_m3_exactness_place(self, ref_page):
        """M3: tag name matching is exact, not substring."""
        results = find_tags(ref_page, tag='place')
        assert len(results) == 1
        assert results[0].tag == 'place'
        assert results[0].text == 'Καρλσροῦε'

    def test_m3_exactness_person(self, ref_page):
        """M3: 'person' should not match 'personName' or similar."""
        results = find_tags(ref_page, tag='person')
        assert len(results) == 1
        assert results[0].tag == 'person'

    def test_m3_no_match(self, ref_page):
        """M3: nonexistent tag returns empty list."""
        results = find_tags(ref_page, tag='nonexistent')
        assert results == []

    def test_m4_regex_literal(self, ref_page):
        """M4: regex search over L1 text."""
        results = find_tags(ref_page, tag='person', text='Χεύνισχ')
        assert len(results) == 1

    def test_m4_regex_pattern(self, ref_page):
        """M4: regex pattern should work."""
        results = find_tags(ref_page, tag='place', text=r'Κα.*ρ')
        assert len(results) == 1
        assert results[0].text == 'Καρλσροῦε'

    def test_m4_no_match_with_text_filter(self, ref_page):
        """M4: text filter that doesn't match returns empty."""
        results = find_tags(ref_page, tag='person', text='Miller')
        assert results == []

    def test_unanchored_readingorder(self, ref_page):
        """Unanchored tags (readingOrder) should have offset=None, length=None."""
        ro = next((t for t in find_tags(ref_page) if t.tag == 'readingOrder'), None)
        assert ro is not None
        assert ro.offset is None
        assert ro.length is None
        assert ro.text is None

    def test_text_filter_skips_unanchored(self, ref_page):
        """Text filter should skip unanchored tags (readingOrder)."""
        results = find_tags(ref_page, text='index')
        assert results == []

    def test_edge_case_no_custom(self, page_no_custom):
        """Line without custom attribute should return no tags."""
        results = find_tags(page_no_custom)
        assert results == []

    def test_edge_case_no_unicode(self, page_no_unicode):
        """Line without TextEquiv should return unanchored tag with text=None."""
        results = find_tags(page_no_unicode)
        assert len(results) == 1
        ro = results[0]
        assert ro.tag == 'readingOrder'
        assert ro.text is None
        assert ro.offset is None

    def test_properties_raw_opaque(self, ref_page):
        """Properties should be kept raw, not parsed."""
        person = next((t for t in find_tags(ref_page) if t.tag == 'person'), None)
        assert 'notice:' in person.properties_raw
        assert 'lastname:Heunisch' in person.properties_raw

    def test_line_id_preserved(self, ref_page):
        """Line ID should be captured."""
        person = next((t for t in find_tags(ref_page) if t.tag == 'person'), None)
        assert person.line_id == 'tl_1768563062'

    def test_page_initially_none(self, ref_page):
        """Page field should be None before stamping by find_tags_by_page."""
        results = find_tags(ref_page)
        for inst in results:
            assert inst.page is None


class TestCountTags:
    """Tests for count_tags (editorial validation)."""

    def test_count_tags_single_page(self, ref_page):
        """count_tags should return a dict of tag_name -> count."""
        counts = count_tags(ref_page)
        assert counts == {
            'readingOrder': 1,
            'place': 1,
            'person': 1,
        }

    def test_count_tags_empty_page(self, page_no_custom):
        """Empty page should return empty dict."""
        counts = count_tags(page_no_custom)
        assert counts == {}

    def test_count_tags_unanchored(self, page_no_unicode):
        """Unanchored tags should still be counted."""
        counts = count_tags(page_no_unicode)
        assert 'readingOrder' in counts
        assert counts['readingOrder'] == 1


class TestInstanceDataclass:
    """Tests for TagInstance dataclass."""

    def test_instance_frozen(self, ref_page):
        """TagInstance should be frozen (immutable)."""
        person = next((t for t in find_tags(ref_page) if t.tag == 'person'), None)
        with pytest.raises(AttributeError):
            person.tag = 'place'

    def test_instance_repr(self, ref_page):
        """TagInstance should have a readable repr."""
        person = next((t for t in find_tags(ref_page) if t.tag == 'person'), None)
        r = repr(person)
        assert 'TagInstance' in r
        assert 'person' in r
        assert 'Χεύνισχ' in r
