"""ARIES-lite crash recovery: redo page writes from the WAL.

Phase 3 — after WriteAheadLog.iter_records works.
"""

from __future__ import annotations

from db_scratch.storage.buffer_pool import BufferPool
from db_scratch.storage.page import Page
from db_scratch.wal.wal import LogRecordType, WriteAheadLog


def recover(wal: WriteAheadLog, buffer_pool: BufferPool) -> None:
    """Replay PAGE_WRITE records with LSN >= each page's on-disk LSN."""
    for lsn, record in wal.iter_records():
        if record.record_type != LogRecordType.PAGE_WRITE:
            continue
        page_id = record.page_id
        page = buffer_pool.fetch_page(page_id)
        if lsn > page.header.lsn:
            page.load_bytes(record.payload)
            page.header.lsn = lsn
            buffer_pool.mark_dirty(page_id)
    buffer_pool.flush_all()
