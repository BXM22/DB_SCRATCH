"""Volcano-style plan execution.

Phase 5d — after planner. Run plans against storage + transactions.
"""

from __future__ import annotations

from db_scratch.btree.btree import BTree
from db_scratch.sql import ast
from db_scratch.sql.planner import Plan, PlanNode
from db_scratch.txn.transaction import TransactionManager


class Executor:
    """Run plans against the storage engine."""

    def __init__(self, btree: BTree, txn_manager: TransactionManager) -> None:
        self.btree = btree
        self.txn_manager = txn_manager
        self._catalog: dict[str, list[ast.ColumnDef]] = {}
        self._tables: dict[str, list[dict[str, object]]] = {}

    def execute(self, plan: Plan) -> list[dict[str, object]]:
        # TODO(phase-5d): if explain_only, return plan text
        # TODO(phase-5d): otherwise begin txn, run _execute_node, commit/abort
        raise NotImplementedError

    def _execute_node(self, node: PlanNode, txn_id: int) -> list[dict[str, object]]:
        # TODO(phase-5d): dispatch on plan node type (SeqScan, Filter, Join, DML, ...)
        raise NotImplementedError

    def _eval_expr(self, expr: ast.Expr, row: dict[str, object]) -> bool:
        # TODO(phase-5d): evaluate WHERE / JOIN predicates against a row
        raise NotImplementedError

    def _value(self, expr: ast.Expr, row: dict[str, object]) -> object:
        # TODO(phase-5d): resolve Literal and ColumnRef to Python values
        raise NotImplementedError
