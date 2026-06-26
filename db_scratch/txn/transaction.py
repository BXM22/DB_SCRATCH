"""Transaction lifecycle: begin, commit, abort, and WAL integration.

Phase 4 — after WAL.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from db_scratch.txn.mvcc import Snapshot
from db_scratch.wal.wal import LogRecord, LogRecordType, WriteAheadLog


@dataclass
class Transaction:
    txn_id: int
    snapshot: Snapshot
    active: bool = True
    write_set: set[int] = field(default_factory=set)


class TransactionManager:
    """Assign txn ids, track active transactions, and log commit/abort."""

    def __init__(self, wal: WriteAheadLog) -> None:
        self.wal = wal
        self._next_txn_id = 1
        self._active: dict[int, Transaction] = {}

    def begin(self) -> Transaction:
        # TODO(phase-4): assign txn id, build Snapshot from active txns, log BEGIN
        raise NotImplementedError

    def commit(self, txn: Transaction) -> None:
        # TODO(phase-4): log COMMIT, fsync wal, mark txn inactive, remove from _active
        raise NotImplementedError

    def abort(self, txn: Transaction) -> None:
        # TODO(phase-4): log ABORT, mark txn inactive, remove from _active
        raise NotImplementedError

    def log_page_write(self, txn: Transaction, page_id: int, page_bytes: bytes) -> int:
        # TODO(phase-4): append PAGE_WRITE record, add page_id to txn.write_set
        raise NotImplementedError
