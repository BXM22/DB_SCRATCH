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
        # TODO(phase-4): implement snapshot isolation visibility rules
        #   - your own uncommitted writes are visible
        #   - uncommitted writes from others are not
        #   - committed writes from active txns at snapshot time are not
        raise NotImplementedError
