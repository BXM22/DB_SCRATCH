"""SQL AST node definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ColumnDef:
    name: str
    type_name: str


@dataclass
class CreateTable:
    table_name: str
    columns: list[ColumnDef]


@dataclass
class Insert:
    table_name: str
    columns: list[str]
    values: list[object]


@dataclass
class Select:
    columns: list[str]
    table_name: str
    where: "Expr | None" = None
    joins: list["Join"] = field(default_factory=list)


@dataclass
class Update:
    table_name: str
    assignments: dict[str, object]
    where: "Expr | None" = None


@dataclass
class Explain:
    statement: "Statement"


@dataclass
class Join:
    table_name: str
    on: "Expr"


@dataclass
class BinaryExpr:
    op: Literal["=", "!=", "<", "<=", ">", ">=", "AND", "OR"]
    left: "Expr"
    right: "Expr"


@dataclass
class ColumnRef:
    name: str
    table: str | None = None


@dataclass
class Literal:
    value: object


Expr = BinaryExpr | ColumnRef | Literal
Statement = CreateTable | Insert | Select | Update | Explain
