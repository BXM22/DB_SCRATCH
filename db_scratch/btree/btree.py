"""B+tree operations: point lookups, inserts, deletes, and range scans.

Phase 2 — after node (de)serialization.
"""

from __future__ import annotations

import bisect

from db_scratch.btree.node import MAX_KEYS, BTreeNode, LeafNode, node_from_page, node_to_page
from db_scratch.storage.buffer_pool import BufferPool
from db_scratch.txn.transaction import TransactionManager


class BTree:
    """Ordered index backed by on-disk pages."""

    def __init__(self, buffer_pool: BufferPool, txn_manager: TransactionManager) -> None:
        self.buffer_pool = buffer_pool
        self.txn_manager = txn_manager
        self.root_page_id: int | None = None

    def get(self, key: bytes, txn_id: int | None = None) -> bytes | None:
        leaf = self._find_leaf(key)
        idx = bisect.bisect_left(leaf.keys, key)
        if idx < len(leaf.keys) and leaf.keys[idx] == key:
            return leaf.values[idx]
        return None

    def insert(self, key: bytes, value: bytes, txn_id: int | None = None) -> None:
        if self.root_page_id is None:
            page = self.buffer_pool.new_page()
            self.root_page_id = page.page_id
            leaf = LeafNode(page.page_id, [key], [value])
            node_to_page(leaf, page)
            self.buffer_pool.mark_dirty(page.page_id)
            return

        leaf = self._find_leaf(key)
        idx = bisect.bisect_left(leaf.keys, key)
        if idx < len(leaf.keys) and leaf.keys[idx] == key:
            leaf.values[idx] = value
        else:
            leaf.keys.insert(idx, key)
            leaf.values.insert(idx, value)

        page = self.buffer_pool.fetch_page(leaf.page_id)
        node_to_page(leaf, page)
        self.buffer_pool.mark_dirty(leaf.page_id)

        if len(leaf.keys) > MAX_KEYS:
            self._split_leaf(leaf)

    def delete(self, key: bytes, txn_id: int | None = None) -> bool:
        if self.root_page_id is None:
            return False
        leaf = self._find_leaf(key)
        idx = bisect.bisect_left(leaf.keys, key)
        if idx >= len(leaf.keys) or leaf.keys[idx] != key:
            return False
        leaf.keys.pop(idx)
        leaf.values.pop(idx)
        page = self.buffer_pool.fetch_page(leaf.page_id)
        node_to_page(leaf, page)
        self.buffer_pool.mark_dirty(leaf.page_id)
        return True

    def scan(self, start: bytes | None = None, end: bytes | None = None):
        """Yield (key, value) pairs in key order."""
        if self.root_page_id is None:
            return

        leaf = self._leftmost_leaf()
        while leaf is not None:
            for key, value in zip(leaf.keys, leaf.values, strict=True):
                if start is not None and key < start:
                    continue
                if end is not None and key > end:
                    return
                yield key, value
            if leaf.next_leaf is None:
                break
            page = self.buffer_pool.fetch_page(leaf.next_leaf)
            leaf = node_from_page(page)
            if not isinstance(leaf, LeafNode):
                raise ValueError("leaf chain points to non-leaf page")

    def _find_leaf(self, key: bytes) -> LeafNode:
        if self.root_page_id is None:
            raise ValueError("empty btree")
        page = self.buffer_pool.fetch_page(self.root_page_id)
        node = node_from_page(page)
        while not isinstance(node, LeafNode):
            assert isinstance(node, BTreeNode)
            idx = bisect.bisect_right(node.keys, key)
            child_id = node.children[idx]
            page = self.buffer_pool.fetch_page(child_id)
            node = node_from_page(page)
        return node

    def _leftmost_leaf(self) -> LeafNode | None:
        if self.root_page_id is None:
            return None
        page = self.buffer_pool.fetch_page(self.root_page_id)
        node = node_from_page(page)
        while not isinstance(node, LeafNode):
            assert isinstance(node, BTreeNode)
            page = self.buffer_pool.fetch_page(node.children[0])
            node = node_from_page(page)
        return node

    def _find_parent(self, child_page_id: int) -> tuple[BTreeNode, int] | None:
        if self.root_page_id is None or child_page_id == self.root_page_id:
            return None

        def search(page_id: int) -> tuple[BTreeNode, int] | None:
            page = self.buffer_pool.fetch_page(page_id)
            node = node_from_page(page)
            if isinstance(node, LeafNode):
                return None
            for idx, child_id in enumerate(node.children):
                if child_id == child_page_id:
                    return node, idx
                found = search(child_id)
                if found is not None:
                    return found
            return None

        return search(self.root_page_id)

    def _create_new_root(self, key: bytes, left_id: int, right_id: int) -> None:
        new_root_page = self.buffer_pool.new_page()
        new_root = BTreeNode(new_root_page.page_id, [key], [left_id, right_id])
        node_to_page(new_root, new_root_page)
        self.buffer_pool.mark_dirty(new_root_page.page_id)
        self.root_page_id = new_root_page.page_id

    def _split_leaf(self, leaf: LeafNode) -> None:
        mid = len(leaf.keys) // 2
        right_page = self.buffer_pool.new_page()
        right = LeafNode(
            right_page.page_id,
            leaf.keys[mid:],
            leaf.values[mid:],
            leaf.next_leaf,
        )
        leaf.keys = leaf.keys[:mid]
        leaf.values = leaf.values[:mid]
        leaf.next_leaf = right_page.page_id

        left_page = self.buffer_pool.fetch_page(leaf.page_id)
        node_to_page(leaf, left_page)
        node_to_page(right, right_page)
        self.buffer_pool.mark_dirty(leaf.page_id)
        self.buffer_pool.mark_dirty(right_page.page_id)

        separator = right.keys[0]
        if leaf.page_id == self.root_page_id:
            self._create_new_root(separator, leaf.page_id, right_page.page_id)
            return

        parent_info = self._find_parent(leaf.page_id)
        if parent_info is None:
            self._create_new_root(separator, leaf.page_id, right_page.page_id)
            return
        parent, child_idx = parent_info
        self._insert_into_internal(parent, separator, right_page.page_id, child_idx)

    def _insert_into_internal(
        self, node: BTreeNode, key: bytes, right_child_id: int, child_idx: int
    ) -> None:
        node.keys.insert(child_idx, key)
        node.children.insert(child_idx + 1, right_child_id)

        page = self.buffer_pool.fetch_page(node.page_id)
        node_to_page(node, page)
        self.buffer_pool.mark_dirty(node.page_id)

        if len(node.keys) <= MAX_KEYS:
            return

        mid = len(node.keys) // 2
        promote_key = node.keys[mid]
        right_page = self.buffer_pool.new_page()
        right = BTreeNode(
            right_page.page_id,
            node.keys[mid + 1 :],
            node.children[mid + 1 :],
        )
        node.keys = node.keys[:mid]
        node.children = node.children[: mid + 1]

        left_page = self.buffer_pool.fetch_page(node.page_id)
        node_to_page(node, left_page)
        node_to_page(right, right_page)
        self.buffer_pool.mark_dirty(node.page_id)
        self.buffer_pool.mark_dirty(right_page.page_id)

        if node.page_id == self.root_page_id:
            self._create_new_root(promote_key, node.page_id, right_page.page_id)
            return

        parent_info = self._find_parent(node.page_id)
        if parent_info is None:
            self._create_new_root(promote_key, node.page_id, right_page.page_id)
            return
        parent, idx = parent_info
        self._insert_into_internal(parent, promote_key, right_page.page_id, idx)
