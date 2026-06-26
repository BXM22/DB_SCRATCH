"""B+tree node layout and (de)serialization from pages.

Phase 2 — after storage layer works.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from db_scratch.storage.page import Page


@dataclass
class BTreeNode:
    """Internal node: separator keys and child page ids."""

    page_id: int
    keys: list[bytes] = field(default_factory=list)
    children: list[int] = field(default_factory=list)

    def is_leaf(self) -> bool:
        return False


@dataclass
class LeafNode:
    """Leaf node: ordered keys and row payloads."""

    page_id: int
    keys: list[bytes] = field(default_factory=list)
    values: list[bytes] = field(default_factory=list)
    next_leaf: int | None = None

    def is_leaf(self) -> bool:
        return True


def node_from_page(page: Page) -> BTreeNode | LeafNode:
    # TODO(phase-2): inspect page.header.page_type, parse payload into keys/children/values
    raise NotImplementedError


def node_to_page(node: BTreeNode | LeafNode, page: Page) -> None:
    # TODO(phase-2): set page_type, serialize keys/children/values into page.payload
    raise NotImplementedError
