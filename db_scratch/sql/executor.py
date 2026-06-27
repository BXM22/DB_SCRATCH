"""Volcano-style plan execution.

Phase 5d — after planner. Run plans against storage + transactions.
"""

from __future__ import annotations

from db_scratch.btree.btree import BTree
from db_scratch.sql import ast
from db_scratch.sql.planner import (
    CreateTablePlan,
    Filter,
    InsertPlan,
    NestedLoopJoin,
    Plan,
    Planner,
    PlanNode,
    SeqScan,
    UpdatePlan,
)
from db_scratch.txn.transaction import TransactionManager


class Executor:
    """Run plans against the storage engine."""

    def __init__(self, btree: BTree, txn_manager: TransactionManager) -> None:
        self.btree = btree
        self.txn_manager = txn_manager
        self._catalog: dict[str, list[ast.ColumnDef]] = {}
        self._tables: dict[str, list[dict[str, object]]] = {}
        self._planner = Planner()

    def execute(self, plan: Plan) -> list[dict[str, object]]:
        if plan.explain_only:
            return [{"plan": self._planner.explain(plan)}]
        txn = self.txn_manager.begin()
        try:
            result = self._execute_node(plan.root, txn.txn_id)
            self.txn_manager.commit(txn)
            return result
        except Exception:
            self.txn_manager.abort(txn)
            raise

    def _execute_node(self, node: PlanNode, txn_id: int) -> list[dict[str, object]]:
        if isinstance(node, CreateTablePlan):
            self._catalog[node.table_name] = node.columns
            self._tables[node.table_name] = []
            return []

        if isinstance(node, InsertPlan):
            if node.table_name not in self._tables:
                raise ValueError(f"table not found: {node.table_name}")
            row = dict(zip(node.columns, node.values, strict=True))
            self._tables[node.table_name].append(row)
            return []

        if isinstance(node, SeqScan):
            if node.table_name not in self._tables:
                raise ValueError(f"table not found: {node.table_name}")
            return [dict(row) for row in self._tables[node.table_name]]

        if isinstance(node, Filter):
            rows = self._execute_node(node.child, txn_id)
            return [row for row in rows if self._eval_expr(node.predicate, row)]

        if isinstance(node, NestedLoopJoin):
            left_rows = self._execute_node(node.left, txn_id)
            right_rows = self._execute_node(node.right, txn_id)
            result: list[dict[str, object]] = []
            for left in left_rows:
                for right in right_rows:
                    combined = {**left, **right}
                    if self._eval_expr(node.on, combined):
                        result.append(combined)
            return result

        if isinstance(node, UpdatePlan):
            rows = self._execute_node(node.child, txn_id)
            table = self._tables[node.table_name]
            updated: list[dict[str, object]] = []
            for row in table:
                if node.where is None or self._eval_expr(node.where, row):
                    for col, val in node.assignments.items():
                        row[col] = val
                    updated.append(dict(row))
            return updated

        raise TypeError(f"unsupported plan node: {type(node)}")

    def _eval_expr(self, expr: ast.Expr, row: dict[str, object]) -> bool:
        if isinstance(expr, ast.BinaryExpr):
            if expr.op in ("AND", "OR"):
                left = self._eval_expr(expr.left, row)
                right = self._eval_expr(expr.right, row)
                return left and right if expr.op == "AND" else left or right
            left = self._value(expr.left, row)
            right = self._value(expr.right, row)
            if expr.op == "=":
                return left == right
            if expr.op == "!=":
                return left != right
            if expr.op == "<":
                return left < right  # type: ignore[operator]
            if expr.op == "<=":
                return left <= right  # type: ignore[operator]
            if expr.op == ">":
                return left > right  # type: ignore[operator]
            if expr.op == ">=":
                return left >= right  # type: ignore[operator]
        if isinstance(expr, ast.Literal):
            return bool(expr.value)
        if isinstance(expr, ast.ColumnRef):
            return bool(row.get(expr.name))
        raise TypeError(f"unsupported expression: {type(expr)}")

    def _value(self, expr: ast.Expr, row: dict[str, object]) -> object:
        if isinstance(expr, ast.Literal):
            return expr.value
        if isinstance(expr, ast.ColumnRef):
            return row.get(expr.name)
        if isinstance(expr, ast.BinaryExpr):
            raise TypeError("nested binary expressions belong in _eval_expr")
        raise TypeError(f"unsupported value expression: {type(expr)}")
