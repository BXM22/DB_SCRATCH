"""Shared helpers for CLI output."""

from __future__ import annotations

import typer


def print_result(rows: list[dict[str, object]]) -> None:
    if not rows:
        typer.echo("(ok)")
        return

    if len(rows) == 1 and set(rows[0].keys()) == {"plan"}:
        typer.echo(str(rows[0]["plan"]))
        return

    columns = list(rows[0].keys())
    widths = {col: len(col) for col in columns}
    for row in rows:
        for col in columns:
            widths[col] = max(widths[col], len(str(row.get(col, ""))))

    header = " | ".join(col.ljust(widths[col]) for col in columns)
    divider = "-+-".join("-" * widths[col] for col in columns)
    typer.echo(header)
    typer.echo(divider)
    for row in rows:
        typer.echo(" | ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns))
