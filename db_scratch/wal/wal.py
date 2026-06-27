"""Append-only WAL for durable transaction and page changes.

Phase 3 — after B+tree basics.
"""

from __future__ import annotations

import os
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
        header = struct.pack(
            LOG_RECORD_HEADER,
            int(self.record_type),
            self.txn_id,
            self.page_id,
        )
        return header + struct.pack("!I", len(self.payload)) + self.payload

    @classmethod
    def decode(cls, data: bytes) -> LogRecord:
        min_size = LOG_RECORD_HEADER_SIZE + 4
        if len(data) < min_size:
            raise ValueError("truncated log record")
        record_type, txn_id, page_id = struct.unpack(LOG_RECORD_HEADER, data[:LOG_RECORD_HEADER_SIZE])
        payload_len = struct.unpack("!I", data[LOG_RECORD_HEADER_SIZE : LOG_RECORD_HEADER_SIZE + 4])[0]
        end = LOG_RECORD_HEADER_SIZE + 4 + payload_len
        if len(data) < end:
            raise ValueError("truncated log record payload")
        payload = data[LOG_RECORD_HEADER_SIZE + 4 : end]
        return cls(LogRecordType(record_type), txn_id, page_id, payload)


class WriteAheadLog:
    """Append log records and fsync for durability."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._fd = os.open(str(path), os.O_RDWR | os.O_CREAT, 0o644)
        self._offset = os.lseek(self._fd, 0, os.SEEK_END)

    def append(self, record: LogRecord) -> int:
        data = record.encode()
        lsn = self._offset
        os.write(self._fd, data)
        self._offset += len(data)
        return lsn

    def sync(self) -> None:
        os.fsync(self._fd)

    def iter_records(self):
        fd = os.open(str(self.path), os.O_RDONLY)
        try:
            offset = 0
            buf = b""
            while True:
                chunk = os.read(fd, 4096)
                if not chunk:
                    break
                buf += chunk
                while True:
                    min_size = LOG_RECORD_HEADER_SIZE + 4
                    if len(buf) < min_size:
                        break
                    payload_len = struct.unpack("!I", buf[LOG_RECORD_HEADER_SIZE : min_size])[0]
                    total = min_size + payload_len
                    if len(buf) < total:
                        break
                    record = LogRecord.decode(buf[:total])
                    yield offset, record
                    offset += total
                    buf = buf[total:]
        finally:
            os.close(fd)

    def close(self) -> None:
        os.close(self._fd)
