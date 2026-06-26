"""Learning checklist — un-skip each test as you complete a phase."""

from pathlib import Path

import pytest

from db_scratch.sql.parser import ParseError, parse
from db_scratch.storage.page import PAGE_HEADER_SIZE, Page, PageType


# ── Phase 1: storage ──────────────────────────────────────────────────────────


@pytest.mark.skip(reason="TODO(phase-1): implement PageHeader.pack / unpack")
def test_page_header_round_trip() -> None:
    ...


@pytest.mark.skip(reason="TODO(phase-1): implement Page.to_bytes / from_bytes")
def test_page_round_trip() -> None:
    page = Page(page_id=1)
    page.header.page_type = PageType.BTREE_LEAF
    raw = page.to_bytes()
    restored = Page.from_bytes(1, raw)
    assert restored.header.page_type == PageType.BTREE_LEAF
    assert len(raw) == page.page_size
    assert PAGE_HEADER_SIZE < page.page_size


@pytest.mark.skip(reason="TODO(phase-1): implement FileManager.create / read_page / write_page")
def test_file_manager_page_io(tmp_path: Path) -> None:
    ...


@pytest.mark.skip(reason="TODO(phase-1): implement BufferPool fetch / flush / eviction")
def test_buffer_pool_caches_pages(tmp_path: Path) -> None:
    ...


# ── Phase 2: B+tree ───────────────────────────────────────────────────────────


@pytest.mark.skip(reason="TODO(phase-2): implement node_to_page / node_from_page")
def test_btree_node_serialization() -> None:
    ...


@pytest.mark.skip(reason="TODO(phase-2): implement BTree.insert / get / scan")
def test_btree_insert_and_lookup(tmp_path: Path) -> None:
    ...


# ── Phase 3: WAL ──────────────────────────────────────────────────────────────


@pytest.mark.skip(reason="TODO(phase-3): implement LogRecord.encode / decode")
def test_wal_record_round_trip() -> None:
    ...


@pytest.mark.skip(reason="TODO(phase-3): implement WriteAheadLog.append / iter_records")
def test_wal_append_and_replay(tmp_path: Path) -> None:
    ...


@pytest.mark.skip(reason="TODO(phase-3): implement recover()")
def test_crash_recovery(tmp_path: Path) -> None:
    ...


# ── Phase 4: transactions ─────────────────────────────────────────────────────


@pytest.mark.skip(reason="TODO(phase-4): implement Snapshot.is_visible")
def test_mvcc_visibility() -> None:
    ...


@pytest.mark.skip(reason="TODO(phase-4): implement TransactionManager begin/commit/abort")
def test_transaction_lifecycle(tmp_path: Path) -> None:
    ...


# ── Phase 5: SQL ──────────────────────────────────────────────────────────────


@pytest.mark.skip(reason="TODO(phase-5a): implement lex()")
def test_lexer_tokenizes_keywords() -> None:
    ...


@pytest.mark.skip(reason="TODO(phase-5b): implement Parser.parse for CREATE TABLE")
def test_parse_create_table() -> None:
    stmt = parse("CREATE TABLE users (id INT, name TEXT)")
    assert stmt.table_name == "users"
    assert [c.name for c in stmt.columns] == ["id", "name"]


@pytest.mark.skip(reason="TODO(phase-5b): implement Parser.parse for SELECT ... WHERE")
def test_parse_select_with_where() -> None:
    stmt = parse("SELECT id, name FROM users WHERE id = 1")
    assert stmt.table_name == "users"
    assert stmt.where is not None


@pytest.mark.skip(reason="TODO(phase-5b): raise ParseError on invalid input")
def test_parse_invalid_sql_raises() -> None:
    with pytest.raises(ParseError):
        parse("NOT VALID SQL")


@pytest.mark.skip(reason="TODO(phase-5c): implement Planner.plan")
def test_planner_builds_seq_scan() -> None:
    ...


@pytest.mark.skip(reason="TODO(phase-5d): implement Executor.execute end-to-end")
def test_execute_create_and_insert(tmp_path: Path) -> None:
    ...


# ── Integration ───────────────────────────────────────────────────────────────


@pytest.mark.skip(reason="TODO: all phases — Database.create / close")
def test_database_create_and_close(tmp_path: Path) -> None:
    from db_scratch.database import Database

    db_path = tmp_path / "test.db"
    db = Database.create(db_path)
    db.close()
    assert db_path.exists()
