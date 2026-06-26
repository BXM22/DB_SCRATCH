"""In-memory buffer pool with pin counts and LRU eviction.

Phase 1 — after file_manager.py.
"""

from __future__ import annotations

from collections import OrderedDict

from db_scratch.storage.file_manager import FileManager
from db_scratch.storage.page import Page


class BufferPool:
    """Cache pages in memory; write dirty pages back on flush or eviction."""

    def __init__(self, file_manager: FileManager, *, capacity: int = 128) -> None:
        self.file_manager = file_manager
        self.capacity = capacity
        self._cache: OrderedDict[int, Page] = OrderedDict()
        self._pin_counts: dict[int, int] = {}
        self._dirty: set[int] = set()

    def fetch_page(self, page_id: int) -> Page:
        # TODO(phase-1): return cached page or read from disk via file_manager
        raise NotImplementedError

    def new_page(self) -> Page:
        # TODO(phase-1): allocate_page(), create Page, add to cache
        raise NotImplementedError

    def mark_dirty(self, page_id: int) -> None:
        # TODO(phase-1): add page_id to self._dirty
        raise NotImplementedError

    def pin(self, page_id: int) -> None:
        # TODO(phase-1): increment pin count for page_id
        raise NotImplementedError

    def unpin(self, page_id: int) -> None:
        # TODO(phase-1): decrement pin count; remove entry when it hits zero
        raise NotImplementedError

    def flush_page(self, page_id: int) -> None:
        # TODO(phase-1): if dirty, write page.to_bytes() to disk and clear dirty bit
        raise NotImplementedError

    def flush_all(self) -> None:
        # TODO(phase-1): flush every cached page, then file_manager.sync()
        raise NotImplementedError

    def _put_page(self, page_id: int, page: Page) -> None:
        # TODO(phase-1): evict if at capacity, then insert into OrderedDict
        raise NotImplementedError

    def _evict_one(self) -> None:
        # TODO(phase-1): LRU-evict an unpinned page (flush first if dirty)
        raise NotImplementedError
