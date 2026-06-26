"""Database file creation, growth, and mmap-backed reads/writes.

Phase 1 — after page.py.
"""

from __future__ import annotations

from pathlib import Path

from db_scratch.storage.page import DEFAULT_PAGE_SIZE


class FileManager:
    """Owns the primary database file and page-sized I/O."""

    def __init__(self, path: Path, *, page_size: int = DEFAULT_PAGE_SIZE) -> None:
        self.path = path
        self.page_size = page_size
        # TODO(phase-1): open file with os.open, mmap the file into self._mmap
        raise NotImplementedError

    @classmethod
    def create(cls, path: Path, *, page_size: int = DEFAULT_PAGE_SIZE) -> FileManager:
        # TODO(phase-1): create parent dirs, write one zeroed page (meta page 0)
        raise NotImplementedError

    def read_page(self, page_id: int) -> bytes:
        # TODO(phase-1): seek to page_id * page_size, read exactly page_size bytes
        raise NotImplementedError

    def write_page(self, page_id: int, data: bytes) -> None:
        # TODO(phase-1): validate len(data) == page_size, write at correct offset
        raise NotImplementedError

    def allocate_page(self) -> int:
        # TODO(phase-1): extend mmap, return new page id
        raise NotImplementedError

    def num_pages(self) -> int:
        # TODO(phase-1): return len(mmap) // page_size
        raise NotImplementedError

    def sync(self) -> None:
        # TODO(phase-1): mmap.flush() + os.fsync(fd)
        raise NotImplementedError

    def close(self) -> None:
        # TODO(phase-1): close mmap and file descriptor
        raise NotImplementedError
