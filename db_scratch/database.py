"""Top-level database facade.

Wires the storage engine, WAL, transaction manager, B+tree, and SQL pipeline
into a single `execute(sql)` entry point. Does not contain business logic —
each subsystem owns its own invariants (see README.md).
"""

from __future__ import annotations

from pathlib import Path

from db_scratch.btree.btree import BTree
from db_scratch.sql.executor import Executor
from db_scratch.sql.parser import parse
from db_scratch.sql.planner import Planner
from db_scratch.storage.buffer_pool import BufferPool
from db_scratch.storage.file_manager import FileManager
from db_scratch.txn.transaction import TransactionManager
from db_scratch.wal.wal import WriteAheadLog


class Database:
    """Disk-backed database: buffer pool, B+tree, WAL, MVCC, and SQL execution.

    Wiring is done for you — implement each phase's TODOs, then un-skip tests.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.file_manager = FileManager(path)
        self.buffer_pool = BufferPool(self.file_manager)
        self.wal = WriteAheadLog(path.with_suffix(".wal"))
        self.txn_manager = TransactionManager(self.wal)
        self.btree = BTree(self.buffer_pool, self.txn_manager)
        self.planner = Planner()
        self.executor = Executor(self.btree, self.txn_manager)

    def execute(self, sql: str) -> list[dict[str, object]]:
        """Parse, plan, and run a SQL statement."""
        statement = parse(sql)
        plan = self.planner.plan(statement)
        return self.executor.execute(plan)

    def close(self) -> None:
        """Flush dirty pages, sync WAL, and close files."""
        self.buffer_pool.flush_all()
        self.wal.sync()
        self.wal.close()
        self.file_manager.close()

    @classmethod
    def create(cls, path: Path, *, page_size: int = 4096) -> Database:
        """Create a new database file on disk."""
        FileManager.create(path, page_size=page_size)
        return cls(path)
