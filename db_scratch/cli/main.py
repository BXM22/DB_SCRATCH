"""Typer CLI: init, sql, shell, explain, and demo commands."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import typer

from db_scratch.cli.demo import default_db_path, run_demo
from db_scratch.cli.formatting import print_result
from db_scratch.database import Database
from db_scratch.sql.parser import ParseError

_SHELL_HELP = """\
Shell commands (start with a dot):
  .help    show this message
  .demo    load sample users table and rows
  .quit    exit

SQL examples (type these directly — not CLI commands like init/sql):
  CREATE TABLE users (id INT, name TEXT)
  INSERT INTO users (id, name) VALUES (1, 'alice')
  SELECT id, name FROM users
  EXPLAIN SELECT id FROM users WHERE id = 1
"""

_CLI_ALIASES = frozenset({"init", "sql", "explain", "shell", "demo", "test"})


def _print_shell_help() -> None:
    typer.echo(_SHELL_HELP)


def _shell_error_hint(line: str) -> str | None:
    first = line.split(maxsplit=1)[0].lower()
    if first in _CLI_ALIASES:
        return (
            f"'{first}' is a terminal CLI command, not SQL. "
            "In the shell, type SQL directly (see .help). "
            "Exit and run e.g. `db-scratch init ./data/app.db` from your shell."
        )
    if first == "path":
        return "Replace PATH with a real file path outside this shell, e.g. `db-scratch init ./data/app.db`."
    if line.upper() == "SQL":
        return "Type a SQL statement, not the word SQL. Try: CREATE TABLE users (id INT, name TEXT)"
    return None

app = typer.Typer(
    help="DB_SCRATCH — a disk-backed database built from scratch in Python.",
    no_args_is_help=True,
)


@app.command()
def init(
    path: Path = typer.Argument(..., help="Path to the database file to create."),
    page_size: int = typer.Option(4096, help="Page size in bytes."),
) -> None:
    """Create a new empty database file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    Database.create(path, page_size=page_size)
    typer.secho(f"created database at {path}", fg=typer.colors.GREEN)


@app.command()
def sql(
    path: Path = typer.Argument(..., help="Path to the database file."),
    statement: str = typer.Argument(..., help="SQL statement to execute."),
) -> None:
    """Execute a single SQL statement."""
    db = _open_database(path)
    try:
        print_result(db.execute(statement))
    finally:
        db.close()


@app.command(name="explain")
def explain_cmd(
    path: Path = typer.Argument(..., help="Path to the database file."),
    statement: str = typer.Argument(..., help="SQL statement to explain."),
) -> None:
    """Print the query plan for a SQL statement."""
    db = _open_database(path)
    try:
        print_result(db.execute(f"EXPLAIN {statement}"))
    finally:
        db.close()


@app.command()
def shell(
    path: Path = typer.Argument(
        default_db_path(),
        help="Path to the database file (created if missing).",
    ),
) -> None:
    """Open an interactive SQL shell."""
    typer.echo(f"Connected to {path}" if path.exists() else f"Creating database at {path}")
    if not path.exists():
        db = Database.create(path)
    else:
        db = Database(path)

    typer.secho("DB_SCRATCH SQL shell — type SQL statements, not CLI commands.", bold=True)
    typer.echo("Type .help for examples, .demo to load sample data, .quit to exit.\n")

    try:
        while True:
            try:
                line = input("db> ").strip()
            except (EOFError, KeyboardInterrupt):
                typer.echo()
                break

            if not line:
                continue

            if line in {".quit", ".exit", "quit", "exit"}:
                break

            if line == ".help":
                _print_shell_help()
                continue

            if line == ".demo":
                for sql in (
                    "CREATE TABLE users (id INT, name TEXT)",
                    "INSERT INTO users (id, name) VALUES (1, 'alice')",
                    "INSERT INTO users (id, name) VALUES (2, 'bob')",
                ):
                    typer.secho(f"> {sql}", fg=typer.colors.CYAN)
                    print_result(db.execute(sql))
                typer.echo("Sample data loaded. Try: SELECT id, name FROM users")
                continue

            if line.startswith("."):
                typer.secho(f"unknown command: {line} (type .help)", fg=typer.colors.RED)
                continue

            hint = _shell_error_hint(line)
            if hint:
                typer.secho(f"hint: {hint}", fg=typer.colors.YELLOW)
                continue

            try:
                print_result(db.execute(line))
            except ParseError as exc:
                typer.secho(f"SQL parse error: {exc}", fg=typer.colors.RED)
                typer.echo("Type .help for valid statement examples.")
            except Exception as exc:
                typer.secho(f"error: {exc}", fg=typer.colors.RED)
    finally:
        db.close()
        typer.echo("bye")


@app.command()
def demo(
    db: Path = typer.Option(
        default_db_path(),
        "--db",
        help="Database file path.",
    ),
    fresh: bool = typer.Option(False, "--fresh", help="Delete existing database first."),
) -> None:
    """Run a sample CREATE / INSERT / SELECT / EXPLAIN workflow."""
    run_demo(db, fresh=fresh)


@app.command()
def test() -> None:
    """Run the pytest suite."""
    root = Path(__file__).resolve().parents[2]
    typer.echo("Running tests...\n")
    subprocess.run([sys.executable, "-m", "pytest", "-v"], cwd=root, check=True)


def _open_database(path: Path) -> Database:
    if not path.exists():
        raise typer.BadParameter(f"database not found: {path} (run `init` first)")
    return Database(path)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
