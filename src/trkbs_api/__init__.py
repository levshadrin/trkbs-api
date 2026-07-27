from .client import TrkbsClient
from .headings import (
    get_headings_by_page,
    find_months_in_text,
    header_string_lookup,
    tag_heading,
    tag_heading_stream,
)
from .edit_tags import (
    replace_tag,
    replace_tag_stream,
    replace_tag_name,
    replace_tag_name_stream,
    replace_attr,
    replace_attr_stream,
)
from .regesta import (
    tag_empty_lines,
    add_regesta,
)
from .marginalia import tag_marginalia, tag_marginalia_stream
from .export_text import get_text, format_page_xml
from .count_structure import count_tag_by_page
from .search_tags import (
    TagInstance,
    find_tags,
    find_tags_by_page,
    count_tags,
    count_tags_by_page,
)

__all__ = [
    "TrkbsClient",
    "get_headings_by_page",
    "find_months_in_text",
    "header_string_lookup",
    "tag_heading",
    "tag_heading_stream",
    "replace_tag",
    "replace_tag_stream",
    "replace_tag_name",
    "replace_tag_name_stream",
    "replace_attr",
    "replace_attr_stream",
    "tag_empty_lines",
    "add_regesta",
    "tag_marginalia",
    "tag_marginalia_stream",
    "get_text",
    "format_page_xml",
    "count_tag_by_page",
    "TagInstance",
    "find_tags",
    "find_tags_by_page",
    "count_tags",
    "count_tags_by_page",
]
