"""On-disk page representation and serialization.

Phase 1 — start here.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import IntEnum

PAGE_HEADER_FORMAT = "!BBHIH6x"  # type, flags, page_id, lsn, free_space
PAGE_HEADER_SIZE = struct.calcsize(PAGE_HEADER_FORMAT)
DEFAULT_PAGE_SIZE = 4096


class PageType(IntEnum):
    FREE = 0
    META = 1
    BTREE_INTERNAL = 2
    BTREE_LEAF = 3
    OVERFLOW = 4


@dataclass
class PageHeader:
    page_type: PageType
    flags: int
    page_id: int
    lsn: int
    free_space: int

    def pack(self) -> bytes:
        return struct.pack(
            PAGE_HEADER_FORMAT,
            int(self.page_type),
            self.flags,
            self.page_id,
            self.lsn,
            self.free_space,
        )

    @classmethod
    def unpack(cls, data: memoryview) -> PageHeader:
        if len(data) < PAGE_HEADER_SIZE:
            raise ValueError("truncated page header")
        page_type, flags, page_id, lsn, free_space = struct.unpack(
            PAGE_HEADER_FORMAT, data[:PAGE_HEADER_SIZE]
        )
        return cls(
            page_type=PageType(page_type),
            flags=flags,
            page_id=page_id,
            lsn=lsn,
            free_space=free_space,
        )


class Page:
    """Fixed-size page with header and byte payload."""

    def __init__(self, page_id: int, page_size: int = DEFAULT_PAGE_SIZE) -> None:
        self.page_id = page_id
        self.page_size = page_size
        self.header = PageHeader(
            page_type=PageType.FREE,
            flags=0,
            page_id=page_id,
            lsn=0,
            free_space=page_size - PAGE_HEADER_SIZE,
        )
        self._data = bytearray(page_size)

    @property
    def payload(self) -> memoryview:
        return memoryview(self._data)[PAGE_HEADER_SIZE:]

    def to_bytes(self) -> bytes:
        self._data[:PAGE_HEADER_SIZE] = self.header.pack()
        return bytes(self._data)

    def load_bytes(self, raw: bytes) -> None:
        if len(raw) != self.page_size:
            raise ValueError("Invalid page size")
        self._data[:] = raw
        self.header = PageHeader.unpack(memoryview(self._data[:PAGE_HEADER_SIZE]))

    @classmethod
    def from_bytes(cls, page_id: int, raw: bytes) -> Page:
        page = cls(page_id, page_size=len(raw))
        page.load_bytes(raw)
        return page
