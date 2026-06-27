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
        if page_id in self._cache:
            self._cache.move_to_end(page_id)
            return self._cache[page_id]
        raw = self.file_manager.read_page(page_id)
        page = Page.from_bytes(page_id, raw)
        self._put_page(page_id, page)
        return page

    def new_page(self) -> Page:
        page_id = self.file_manager.allocate_page()
        page = Page(page_id, page_size=self.file_manager.page_size)
        page.header.page_id = page_id
        self._put_page(page_id, page)
        self.mark_dirty(page_id)
        return page

    def mark_dirty(self, page_id: int) -> None:
        self._dirty.add(page_id)

    def pin(self, page_id: int) -> None:
        self._pin_counts[page_id] = self._pin_counts.get(page_id, 0) + 1

    def unpin(self, page_id: int) -> None:
        count = self._pin_counts.get(page_id, 0)
        if count <= 1:
            self._pin_counts.pop(page_id, None)
        else:
            self._pin_counts[page_id] = count - 1

    def flush_page(self, page_id: int) -> None:
        if page_id not in self._dirty:
            return
        page = self._cache[page_id]
        self.file_manager.write_page(page_id, page.to_bytes())
        self._dirty.discard(page_id)

    def flush_all(self) -> None:
        for page_id in list(self._dirty):
            self.flush_page(page_id)
        self.file_manager.sync()

    def _put_page(self, page_id: int, page: Page) -> None:
        if page_id not in self._cache and len(self._cache) >= self.capacity:
            self._evict_one()
        self._cache[page_id] = page
        self._cache.move_to_end(page_id)

    def _evict_one(self) -> None:
        for page_id in self._cache:
            if self._pin_counts.get(page_id, 0) == 0:
                if page_id in self._dirty:
                    self.flush_page(page_id)
                del self._cache[page_id]
                return
        raise RuntimeError("all pages are pinned")
