"""Demo workflow for CLI and run script."""

from __future__ import annotations

import os
from pathlib import Path

import typer

from db_scratch.cli.formatting import print_result
from db_scratch.database import Database

DEFAULT_DB = Path("./data/demo.db")


def default_db_path() -> Path:
    return Path(os.environ.get("DB_PATH", DEFAULT_DB))


def run_demo(db_path: Path, *, fresh: bool) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if fresh and db_path.exists():
        db_path.unlink()
        wal_path = db_path.with_suffix(".wal")
        if wal_path.exists():
            wal_path.unlink()

    if db_path.exists():
        typer.echo(f"Opening database at {db_path}")
        db = Database(db_path)
    else:
        typer.echo(f"Creating database at {db_path}")
        db = Database.create(db_path)

    statements = [
        "CREATE TABLE users (id INT, name TEXT)",
        "INSERT INTO users (id, name) VALUES (1, 'alice')",
        "INSERT INTO users (id, name) VALUES (2, 'bob')",
        "SELECT id, name FROM users WHERE id = 1",
        "SELECT id, name FROM users",
        "EXPLAIN SELECT id FROM users WHERE id = 1",
    ]

    try:
        for sql in statements:
            typer.secho(f"\n> {sql}", fg=typer.colors.CYAN)
            rows = db.execute(sql)
            print_result(rows)
    finally:
        db.close()

    typer.secho(
        f"\nDone. Database files: {db_path} and {db_path.with_suffix('.wal')}",
        fg=typer.colors.GREEN,
    )
