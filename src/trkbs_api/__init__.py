from .client import TrkbsClient
from .headings import (
    get_headings_by_page,
    find_months_in_text,
    validate_headings,
    header_string_lookup,
    tag_heading,
    tag_heading_stream,
)
from .tag_sub import (
    replace_tag,
    replace_tag_stream,
    replace_attr,
    replace_attr_stream,
)
from .regesta import (
    tag_empty_lines,
    add_regesta,
    validate_regesta,
    remove_regesta,
)
from .marginalia import tag_marginalia, tag_marginalia_stream
from .export import get_text

__all__ = [
    "TrkbsClient",
    "get_headings_by_page",
    "find_months_in_text",
    "validate_headings",
    "header_string_lookup",
    "tag_heading",
    "tag_heading_stream",
    "replace_tag",
    "replace_tag_stream",
    "replace_attr",
    "replace_attr_stream",
    "tag_empty_lines",
    "add_regesta",
    "validate_regesta",
    "remove_regesta",
    "tag_marginalia",
    "tag_marginalia_stream",
    "get_text",
]
