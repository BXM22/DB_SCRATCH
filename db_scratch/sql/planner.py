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
        if isinstance(statement, ast.Explain):
            inner = self.plan(statement.statement)
            return Plan(inner.root, explain_only=True)
        if isinstance(statement, ast.CreateTable):
            return Plan(CreateTablePlan(statement.table_name, statement.columns))
        if isinstance(statement, ast.Insert):
            return Plan(InsertPlan(statement.table_name, statement.columns, statement.values))
        if isinstance(statement, ast.Select):
            root: PlanNode = SeqScan(statement.table_name)
            if statement.where is not None:
                root = Filter(statement.where, root)
            for join in statement.joins:
                right = SeqScan(join.table_name)
                root = NestedLoopJoin(root, right, join.on)
            return Plan(root)
        if isinstance(statement, ast.Update):
            scan: PlanNode = SeqScan(statement.table_name)
            if statement.where is not None:
                scan = Filter(statement.where, scan)
            return Plan(
                UpdatePlan(statement.table_name, statement.assignments, statement.where, scan)
            )
        raise TypeError(f"unsupported statement type: {type(statement)}")

    def explain(self, plan: Plan) -> str:
        lines: list[str] = []

        def walk(node: PlanNode, depth: int) -> None:
            indent = "  " * depth
            name = type(node).__name__
            if isinstance(node, SeqScan):
                lines.append(f"{indent}{name}({node.table_name})")
            elif isinstance(node, IndexScan):
                lines.append(f"{indent}{name}({node.table_name}, {node.index_name})")
            elif isinstance(node, Filter):
                lines.append(f"{indent}{name}")
                walk(node.child, depth + 1)
            elif isinstance(node, NestedLoopJoin):
                lines.append(f"{indent}{name}")
                walk(node.left, depth + 1)
                walk(node.right, depth + 1)
            elif isinstance(node, InsertPlan):
                lines.append(f"{indent}{name}({node.table_name})")
            elif isinstance(node, CreateTablePlan):
                lines.append(f"{indent}{name}({node.table_name})")
            elif isinstance(node, UpdatePlan):
                lines.append(f"{indent}{name}({node.table_name})")
                walk(node.child, depth + 1)

        walk(plan.root, 0)
        return "\n".join(lines)
