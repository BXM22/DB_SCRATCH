"""Typer CLI: init, sql, and explain commands."""

from __future__ import annotations

from pathlib import Path

import typer

from db_scratch.database import Database

app = typer.Typer(help="DB_SCRATCH — a database built from scratch in Python.")


@app.command()
def init(
    path: Path = typer.Argument(..., help="Path to the database file to create."),
    page_size: int = typer.Option(4096, help="Page size in bytes."),
) -> None:
    """Create a new empty database file."""
    Database.create(path, page_size=page_size)
    typer.echo(f"created database at {path}")


@app.command()
def sql(
    path: Path = typer.Argument(..., help="Path to the database file."),
    statement: str = typer.Argument(..., help="SQL statement to execute."),
) -> None:
    """Execute a single SQL statement."""
    db = Database(path)
    try:
        rows = db.execute(statement)
        for row in rows:
            typer.echo(row)
    finally:
        db.close()


@app.command(name="explain")
def explain_cmd(
    path: Path = typer.Argument(..., help="Path to the database file."),
    statement: str = typer.Argument(..., help="SQL statement to explain."),
) -> None:
    """Print the query plan for a SQL statement."""
    db = Database(path)
    try:
        rows = db.execute(f"EXPLAIN {statement}")
        for row in rows:
            typer.echo(row.get("plan", row))
    finally:
        db.close()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
