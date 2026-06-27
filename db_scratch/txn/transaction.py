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
        txn_id = self._next_txn_id
        self._next_txn_id += 1
        snapshot = Snapshot(txn_id, frozenset(self._active.keys()))
        txn = Transaction(txn_id, snapshot)
        self._active[txn_id] = txn
        self.wal.append(LogRecord(LogRecordType.BEGIN, txn_id))
        return txn

    def commit(self, txn: Transaction) -> None:
        self.wal.append(LogRecord(LogRecordType.COMMIT, txn.txn_id))
        self.wal.sync()
        txn.active = False
        del self._active[txn.txn_id]

    def abort(self, txn: Transaction) -> None:
        self.wal.append(LogRecord(LogRecordType.ABORT, txn.txn_id))
        txn.active = False
        del self._active[txn.txn_id]

    def log_page_write(self, txn: Transaction, page_id: int, page_bytes: bytes) -> int:
        lsn = self.wal.append(
            LogRecord(LogRecordType.PAGE_WRITE, txn.txn_id, page_id, page_bytes)
        )
        txn.write_set.add(page_id)
        return lsn
