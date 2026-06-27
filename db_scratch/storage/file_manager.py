"""Database file creation, growth, and mmap-backed reads/writes.

Phase 1 — after page.py.
"""

from __future__ import annotations

import mmap
import os
from pathlib import Path

from db_scratch.storage.page import DEFAULT_PAGE_SIZE


class FileManager:
    """Owns the primary database file and page-sized I/O."""

    def __init__(self, path: Path, *, page_size: int = DEFAULT_PAGE_SIZE) -> None:
        self.path = path
        self.page_size = page_size
        self._fd = os.open(str(path), os.O_RDWR)
        self._mmap = mmap.mmap(self._fd, 0, access=mmap.ACCESS_WRITE)

    @classmethod
    def create(cls, path: Path, *, page_size: int = DEFAULT_PAGE_SIZE) -> FileManager:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(b"\x00" * page_size)
        return cls(path, page_size=page_size)

    def read_page(self, page_id: int) -> bytes:
        offset = page_id * self.page_size
        return bytes(self._mmap[offset : offset + self.page_size])

    def write_page(self, page_id: int, data: bytes) -> None:
        if len(data) != self.page_size:
            raise ValueError(f"expected {self.page_size} bytes, got {len(data)}")
        offset = page_id * self.page_size
        self._mmap[offset : offset + self.page_size] = data

    def allocate_page(self) -> int:
        new_id = self.num_pages()
        new_size = (new_id + 1) * self.page_size
        os.ftruncate(self._fd, new_size)
        self._mmap.close()
        self._mmap = mmap.mmap(self._fd, 0, access=mmap.ACCESS_WRITE)
        return new_id

    def num_pages(self) -> int:
        return len(self._mmap) // self.page_size

    def sync(self) -> None:
        self._mmap.flush()
        os.fsync(self._fd)

    def close(self) -> None:
        self._mmap.close()
        os.close(self._fd)
