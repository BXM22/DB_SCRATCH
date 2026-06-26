"""Build physical plans from SQL AST nodes.

Phase 5c — after parser. Keep plan node types; implement planning logic.
"""

from __future__ import annotations

from dataclasses import dataclass

from db_scratch.sql import ast


@dataclass
class SeqScan:
    table_name: str


@dataclass
class IndexScan:
    table_name: str
    index_name: str


@dataclass
class Filter:
    predicate: ast.Expr
    child: "PlanNode"


@dataclass
class NestedLoopJoin:
    left: "PlanNode"
    right: "PlanNode"
    on: ast.Expr


@dataclass
class InsertPlan:
    table_name: str
    columns: list[str]
    values: list[object]


@dataclass
class CreateTablePlan:
    table_name: str
    columns: list[ast.ColumnDef]


@dataclass
class UpdatePlan:
    table_name: str
    assignments: dict[str, object]
    where: ast.Expr | None
    child: "PlanNode"


PlanNode = SeqScan | IndexScan | Filter | NestedLoopJoin | InsertPlan | CreateTablePlan | UpdatePlan


@dataclass
class Plan:
    root: PlanNode
    explain_only: bool = False


class Planner:
    """Translate AST statements into volcano-style plan trees."""

    def plan(self, statement: ast.Statement) -> Plan:
        # TODO(phase-5c): map each AST type to a plan tree
        #   CREATE  -> CreateTablePlan
        #   INSERT  -> InsertPlan
        #   SELECT  -> SeqScan + optional Filter + NestedLoopJoin per JOIN
        #   UPDATE  -> UpdatePlan wrapping Filter(SeqScan)
        #   EXPLAIN -> plan inner statement with explain_only=True
        raise NotImplementedError

    def explain(self, plan: Plan) -> str:
        # TODO(phase-5c): walk plan tree, indent by depth, return node type names
        raise NotImplementedError
