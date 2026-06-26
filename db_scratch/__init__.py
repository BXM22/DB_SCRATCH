"""DB_SCRATCH — disk-backed RDBMS built from first principles.

Public API:
    Database  — facade over storage, WAL, transactions, and SQL execution

Implementation follows a strict layered architecture (see README.md):
  storage → btree → wal → txn → sql

Work through TODOS.txt in phase order; un-skip tests as each layer passes.
"""

from db_scratch.database import Database

__all__ = ["Database"]
__version__ = "0.1.0"
