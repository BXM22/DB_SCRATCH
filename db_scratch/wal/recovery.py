"""ARIES-lite crash recovery: redo page writes from the WAL.

Phase 3 — after WriteAheadLog.iter_records works.
"""

from __future__ import annotations

from db_scratch.storage.buffer_pool import BufferPool
from db_scratch.wal.wal import LogRecordType, WriteAheadLog


def recover(wal: WriteAheadLog, buffer_pool: BufferPool) -> None:
    """Replay PAGE_WRITE records with LSN >= each page's on-disk LSN."""
    # TODO(phase-3): iterate wal records
    # TODO(phase-3): for PAGE_WRITE, load payload into page if record LSN is newer
    # TODO(phase-3): mark pages dirty and flush_all at the end
    raise NotImplementedError
