"""B+tree operations: point lookups, inserts, deletes, and range scans.

Phase 2 — after node (de)serialization.
"""

from __future__ import annotations

from db_scratch.btree.node import LeafNode
from db_scratch.storage.buffer_pool import BufferPool
from db_scratch.txn.transaction import TransactionManager


class BTree:
    """Ordered index backed by on-disk pages."""

    def __init__(self, buffer_pool: BufferPool, txn_manager: TransactionManager) -> None:
        self.buffer_pool = buffer_pool
        self.txn_manager = txn_manager
        self.root_page_id = 0

    def get(self, key: bytes, txn_id: int | None = None) -> bytes | None:
        # TODO(phase-2): find leaf, scan keys for match, return value or None
        raise NotImplementedError

    def insert(self, key: bytes, value: bytes, txn_id: int | None = None) -> None:
        # TODO(phase-2): insert into leaf; split on overflow; propagate separators up
        raise NotImplementedError

    def delete(self, key: bytes, txn_id: int | None = None) -> bool:
        # TODO(phase-2): remove from leaf; merge or redistribute when underfull
        raise NotImplementedError

    def scan(self, start: bytes | None = None, end: bytes | None = None):
        """Yield (key, value) pairs in key order."""
        # TODO(phase-2): walk leaf chain via next_leaf pointers
        raise NotImplementedError
        yield  # pragma: no cover — makes this a generator stub

    def _find_leaf(self, key: bytes) -> LeafNode:
        # TODO(phase-2): descend from root using separator keys until you hit a leaf
        raise NotImplementedError
