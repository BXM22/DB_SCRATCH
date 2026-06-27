"""Learning checklist — un-skip each test as you complete a phase."""

from pathlib import Path

import pytest

from db_scratch.sql.lexer import TokenType, lex
from db_scratch.sql.parser import ParseError, parse
from db_scratch.sql.planner import Planner
from db_scratch.storage.buffer_pool import BufferPool
from db_scratch.storage.file_manager import FileManager
from db_scratch.storage.page import PAGE_HEADER_SIZE, Page, PageHeader, PageType
from db_scratch.txn.mvcc import Snapshot
from db_scratch.txn.transaction import TransactionManager
from db_scratch.wal.recovery import recover
from db_scratch.wal.wal import LogRecord, LogRecordType, WriteAheadLog


# ── Phase 1: storage ──────────────────────────────────────────────────────────


def test_page_header_round_trip() -> None:
    header = PageHeader(PageType.BTREE_LEAF, 0, 1, 42, 4000)
    packed = header.pack()
    assert len(packed) == PAGE_HEADER_SIZE
    restored = PageHeader.unpack(memoryview(packed))
    assert restored.page_type == PageType.BTREE_LEAF
    assert restored.page_id == 1
    assert restored.lsn == 42
    assert restored.free_space == 4000


def test_page_round_trip() -> None:
    page = Page(page_id=1)
    page.header.page_type = PageType.BTREE_LEAF
    raw = page.to_bytes()
    restored = Page.from_bytes(1, raw)
    assert restored.header.page_type == PageType.BTREE_LEAF
    assert len(raw) == page.page_size
    assert PAGE_HEADER_SIZE < page.page_size


def test_file_manager_page_io(tmp_path: Path) -> None:
    path = tmp_path / "test.db"
    fm = FileManager.create(path)
    page = Page(1)
    page.header.page_type = PageType.BTREE_LEAF
    data = page.to_bytes()
    new_id = fm.allocate_page()
    fm.write_page(new_id, data)
    assert fm.read_page(new_id) == data
    fm.close()


def test_buffer_pool_caches_pages(tmp_path: Path) -> None:
    path = tmp_path / "test.db"
    fm = FileManager.create(path)
    pool = BufferPool(fm, capacity=2)
    page = pool.new_page()
    page.header.page_type = PageType.BTREE_LEAF
    pool.mark_dirty(page.page_id)
    pool.flush_page(page.page_id)

    fetched = pool.fetch_page(page.page_id)
    assert fetched.header.page_type == PageType.BTREE_LEAF

    p2 = pool.new_page()
    p3 = pool.new_page()
    assert p2.page_id != p3.page_id
    fm.close()


# ── Phase 2: B+tree ───────────────────────────────────────────────────────────


def test_btree_node_serialization() -> None:
    from db_scratch.btree.node import LeafNode, node_from_page, node_to_page

    page = Page(1)
    leaf = LeafNode(1, [b"a", b"b"], [b"1", b"2"], next_leaf=2)
    node_to_page(leaf, page)
    restored = node_from_page(page)
    assert isinstance(restored, LeafNode)
    assert restored.keys == [b"a", b"b"]
    assert restored.values == [b"1", b"2"]
    assert restored.next_leaf == 2


def test_btree_insert_and_lookup(tmp_path: Path) -> None:
    from db_scratch.btree.btree import BTree

    path = tmp_path / "test.db"
    fm = FileManager.create(path)
    pool = BufferPool(fm)
    wal = WriteAheadLog(path.with_suffix(".wal"))
    txn_mgr = TransactionManager(wal)
    tree = BTree(pool, txn_mgr)

    tree.insert(b"key1", b"val1")
    tree.insert(b"key2", b"val2")
    assert tree.get(b"key1") == b"val1"
    assert tree.get(b"key2") == b"val2"
    assert tree.get(b"missing") is None

    results = list(tree.scan())
    assert results == [(b"key1", b"val1"), (b"key2", b"val2")]

    wal.close()
    fm.close()


# ── Phase 3: WAL ──────────────────────────────────────────────────────────────


def test_wal_record_round_trip() -> None:
    record = LogRecord(LogRecordType.PAGE_WRITE, 1, 3, b"page-bytes")
    encoded = record.encode()
    decoded = LogRecord.decode(encoded)
    assert decoded.record_type == LogRecordType.PAGE_WRITE
    assert decoded.txn_id == 1
    assert decoded.page_id == 3
    assert decoded.payload == b"page-bytes"


def test_wal_append_and_replay(tmp_path: Path) -> None:
    path = tmp_path / "test.wal"
    wal = WriteAheadLog(path)
    r1 = LogRecord(LogRecordType.BEGIN, 1)
    r2 = LogRecord(LogRecordType.PAGE_WRITE, 1, 2, b"x" * 4096)
    lsn1 = wal.append(r1)
    lsn2 = wal.append(r2)
    assert lsn1 == 0
    assert lsn2 > lsn1
    wal.close()

    wal2 = WriteAheadLog(path)
    records = list(wal2.iter_records())
    assert len(records) == 2
    assert records[0][1].record_type == LogRecordType.BEGIN
    assert records[1][1].record_type == LogRecordType.PAGE_WRITE
    wal2.close()


def test_crash_recovery(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    wal_path = tmp_path / "test.wal"
    fm = FileManager.create(db_path)
    pool = BufferPool(fm)
    wal = WriteAheadLog(wal_path)
    txn_mgr = TransactionManager(wal)

    page = pool.new_page()
    page.header.page_type = PageType.BTREE_LEAF
    page_bytes = page.to_bytes()
    txn = txn_mgr.begin()
    lsn = txn_mgr.log_page_write(txn, page.page_id, page_bytes)
    page.header.lsn = lsn
    pool.mark_dirty(page.page_id)
    txn_mgr.commit(txn)
    wal.close()

    fm2 = FileManager(db_path)
    pool2 = BufferPool(fm2)
    wal2 = WriteAheadLog(wal_path)
    recover(wal2, pool2)
    restored = pool2.fetch_page(page.page_id)
    assert restored.header.page_type == PageType.BTREE_LEAF
    wal2.close()
    fm2.close()


# ── Phase 4: transactions ─────────────────────────────────────────────────────


def test_mvcc_visibility() -> None:
    snap = Snapshot(txn_id=5, active_txns=frozenset({2, 3}))
    assert snap.is_visible(5, committed=False)
    assert not snap.is_visible(2, committed=False)
    assert not snap.is_visible(2, committed=True)
    assert snap.is_visible(10, committed=True)


def test_transaction_lifecycle(tmp_path: Path) -> None:
    wal_path = tmp_path / "test.wal"
    wal = WriteAheadLog(wal_path)
    mgr = TransactionManager(wal)

    txn = mgr.begin()
    assert txn.txn_id == 1
    assert txn.active
    assert 1 in mgr._active

    mgr.commit(txn)
    assert not txn.active
    assert 1 not in mgr._active

    txn2 = mgr.begin()
    mgr.abort(txn2)
    assert not txn2.active

    wal.close()


# ── Phase 5: SQL ──────────────────────────────────────────────────────────────


def test_lexer_tokenizes_keywords() -> None:
    tokens = lex("CREATE TABLE users (id INT)")
    values = [t.value for t in tokens if t.type != TokenType.EOF]
    assert values == ["CREATE", "TABLE", "users", "(", "id", "INT", ")"]


def test_parse_create_table() -> None:
    stmt = parse("CREATE TABLE users (id INT, name TEXT)")
    assert stmt.table_name == "users"
    assert [c.name for c in stmt.columns] == ["id", "name"]


def test_parse_select_with_where() -> None:
    stmt = parse("SELECT id, name FROM users WHERE id = 1")
    assert stmt.table_name == "users"
    assert stmt.where is not None


def test_parse_invalid_sql_raises() -> None:
    with pytest.raises(ParseError):
        parse("NOT VALID SQL")


def test_planner_builds_seq_scan() -> None:
    stmt = parse("SELECT id FROM users WHERE id = 1")
    plan = Planner().plan(stmt)
    from db_scratch.sql.planner import Filter, SeqScan

    assert isinstance(plan.root, Filter)
    assert isinstance(plan.root.child, SeqScan)
    assert plan.root.child.table_name == "users"


def test_execute_create_and_insert(tmp_path: Path) -> None:
    from db_scratch.btree.btree import BTree
    from db_scratch.database import Database

    db_path = tmp_path / "test.db"
    db = Database.create(db_path)
    db.execute("CREATE TABLE users (id INT, name TEXT)")
    db.execute("INSERT INTO users (id, name) VALUES (1, 'alice')")
    rows = db.execute("SELECT id, name FROM users WHERE id = 1")
    assert rows == [{"id": 1, "name": "alice"}]
    db.close()


# ── Integration ───────────────────────────────────────────────────────────────


def test_database_create_and_close(tmp_path: Path) -> None:
    from db_scratch.database import Database

    db_path = tmp_path / "test.db"
    db = Database.create(db_path)
    db.close()
    assert db_path.exists()
