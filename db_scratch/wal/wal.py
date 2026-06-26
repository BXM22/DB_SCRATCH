"""Append-only WAL for durable transaction and page changes.

Phase 3 — after B+tree basics.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path


class LogRecordType(IntEnum):
    BEGIN = 1
    COMMIT = 2
    ABORT = 3
    PAGE_WRITE = 4
    CHECKPOINT = 5


LOG_RECORD_HEADER = "!BII"  # type, txn_id, page_id (when applicable)
LOG_RECORD_HEADER_SIZE = struct.calcsize(LOG_RECORD_HEADER)


@dataclass
class LogRecord:
    record_type: LogRecordType
    txn_id: int
    page_id: int = 0
    payload: bytes = b""

    def encode(self) -> bytes:
        # TODO(phase-3): pack header + 4-byte payload length + payload
        raise NotImplementedError

    @classmethod
    def decode(cls, data: bytes) -> LogRecord:
        # TODO(phase-3): unpack header, read payload length, slice payload
        raise NotImplementedError


class WriteAheadLog:
    """Append log records and fsync for durability."""

    def __init__(self, path: Path) -> None:
        self.path = path
        # TODO(phase-3): open/create wal file, track append offset as self._offset
        raise NotImplementedError

    def append(self, record: LogRecord) -> int:
        # TODO(phase-3): encode record, os.write, return LSN (offset before write)
        raise NotImplementedError

    def sync(self) -> None:
        # TODO(phase-3): fsync the wal file descriptor
        raise NotImplementedError

    def iter_records(self):
        # TODO(phase-3): read from start of file, yield decoded LogRecords
        raise NotImplementedError
        yield  # pragma: no cover

    def close(self) -> None:
        # TODO(phase-3): close file descriptor
        raise NotImplementedError
