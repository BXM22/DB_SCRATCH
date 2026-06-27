"""B+tree node layout and (de)serialization from pages.

Phase 2 — after storage layer works.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field

from db_scratch.storage.page import Page, PageType

MAX_KEYS = 64


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


def _read_length_prefixed(mv: memoryview, offset: int) -> tuple[bytes, int]:
    length = struct.unpack_from("!H", mv, offset)[0]
    offset += 2
    data = bytes(mv[offset : offset + length])
    return data, offset + length


def _write_length_prefixed(buf: bytearray, data: bytes) -> None:
    buf.extend(struct.pack("!H", len(data)))
    buf.extend(data)


def node_from_page(page: Page) -> BTreeNode | LeafNode:
    mv = page.payload
    if page.header.page_type == PageType.BTREE_LEAF:
        offset = 0
        num_keys = struct.unpack_from("!H", mv, offset)[0]
        offset += 2
        next_raw = struct.unpack_from("!I", mv, offset)[0]
        offset += 4
        next_leaf = None if next_raw == 0 else next_raw
        keys: list[bytes] = []
        values: list[bytes] = []
        for _ in range(num_keys):
            key, offset = _read_length_prefixed(mv, offset)
            value, offset = _read_length_prefixed(mv, offset)
            keys.append(key)
            values.append(value)
        return LeafNode(page.page_id, keys, values, next_leaf)

    if page.header.page_type == PageType.BTREE_INTERNAL:
        offset = 0
        num_keys = struct.unpack_from("!H", mv, offset)[0]
        offset += 2
        keys: list[bytes] = []
        for _ in range(num_keys):
            key, offset = _read_length_prefixed(mv, offset)
            keys.append(key)
        num_children = struct.unpack_from("!H", mv, offset)[0]
        offset += 2
        children: list[int] = []
        for _ in range(num_children):
            child_id = struct.unpack_from("!I", mv, offset)[0]
            offset += 4
            children.append(child_id)
        return BTreeNode(page.page_id, keys, children)

    raise ValueError(f"unsupported page type for btree node: {page.header.page_type}")


def node_to_page(node: BTreeNode | LeafNode, page: Page) -> None:
    buf = bytearray()
    if isinstance(node, LeafNode):
        page.header.page_type = PageType.BTREE_LEAF
        buf.extend(struct.pack("!H", len(node.keys)))
        next_raw = 0 if node.next_leaf is None else node.next_leaf
        buf.extend(struct.pack("!I", next_raw))
        for key, value in zip(node.keys, node.values, strict=True):
            _write_length_prefixed(buf, key)
            _write_length_prefixed(buf, value)
    else:
        page.header.page_type = PageType.BTREE_INTERNAL
        buf.extend(struct.pack("!H", len(node.keys)))
        for key in node.keys:
            _write_length_prefixed(buf, key)
        buf.extend(struct.pack("!H", len(node.children)))
        for child_id in node.children:
            buf.extend(struct.pack("!I", child_id))

    payload = page.payload
    raw = bytes(buf)
    payload[: len(raw)] = raw
    if len(raw) < len(payload):
        payload[len(raw) :] = b"\x00" * (len(payload) - len(raw))
    page.header.free_space = len(payload) - len(raw)
