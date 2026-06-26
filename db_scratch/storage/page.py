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
        # TODO(phase-1): use struct.pack with PAGE_HEADER_FORMAT
        
        raise NotImplementedError

    @classmethod
    def unpack(cls, data: memoryview) -> PageHeader:
        # TODO(phase-1): read PAGE_HEADER_SIZE bytes and return a PageHeader
        raise NotImplementedError


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
        return memoryview(self._data[PAGE_HEADER_SIZE:])
    

    def to_bytes(self) -> bytes:
        self._data[:PAGE_HEADER_SIZE] = self.header.pack()
        return bytes(self._data)

    def load_bytes(self, raw: bytes) -> None:
        # TODO(phase-1): validate length, copy into _data, refresh header
        if len(raw) != self.page_size:
            raise ValueError("Invalid page size")
        self._data[:] = raw
        self.header = PageHeader.unpack(memoryview(self._data[:PAGE_HEADER_SIZE]))

    @classmethod
    def from_bytes(cls, page_id: int, raw: bytes) -> Page:
        # TODO(phase-1): construct Page and call load_bytes
        page = cls(page_id)
        page.load_bytes(raw)
        return page
        
