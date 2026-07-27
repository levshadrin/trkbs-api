"""Parser for Transkribus custom-attribute tag blocks.

The custom attribute contains a sequence of blocks: `name {key:value; …}`.
This module extracts and parses those blocks into structured form.
"""

import re
from typing import NamedTuple

BLOCK_RE = re.compile(r'(\w+)\s*\{([^{}]*)\}')
OFFSET_RE = re.compile(r'\boffset:\s*(\d+)')
LENGTH_RE = re.compile(r'\blength:\s*(\d+)')


class Block(NamedTuple):
    """A single block from a custom attribute."""
    name: str          # e.g. 'person', 'place', 'readingOrder'
    offset: int | None # None for unanchored blocks like readingOrder/structure
    length: int | None
    properties_raw: str  # opaque L3 string (e.g. "offset:21; length:7; notice:...")


def iter_blocks(custom: str | None) -> list[Block]:
    """Parse a custom attribute into blocks.

    Returns a list of Block instances in document order. If custom is None or
    empty, returns an empty list.
    """
    if not custom:
        return []

    blocks = []
    for match in BLOCK_RE.finditer(custom):
        name = match.group(1)
        body = match.group(2)

        # Try to extract offset and length
        offset_match = OFFSET_RE.search(body)
        length_match = LENGTH_RE.search(body)

        offset = int(offset_match.group(1)) if offset_match else None
        length = int(length_match.group(1)) if length_match else None

        blocks.append(Block(
            name=name,
            offset=offset,
            length=length,
            properties_raw=body
        ))

    return blocks
