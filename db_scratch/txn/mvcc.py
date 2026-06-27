"""MVCC snapshot visibility rules.

Phase 4 — after WAL.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Snapshot:
    """Read snapshot for snapshot isolation."""

    txn_id: int
    active_txns: frozenset[int]

    def is_visible(self, creator_txn_id: int, committed: bool) -> bool:
        if creator_txn_id == self.txn_id:
            return True
        if not committed:
            return False
        if creator_txn_id in self.active_txns:
            return False
        return True
