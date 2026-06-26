"""Recursive-descent parser for the supported SQL subset.

Phase 5b — after lexer. Build AST nodes defined in ast.py.
"""

from __future__ import annotations

from db_scratch.sql import ast
from db_scratch.sql.lexer import Token, lex


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, sql: str) -> None:
        self.tokens = lex(sql)
        self.pos = 0

    def parse(self) -> ast.Statement:
        # TODO(phase-5b): dispatch on first keyword — EXPLAIN, CREATE, INSERT, SELECT, UPDATE
        raise NotImplementedError

    # TODO(phase-5b): implement helper methods:
    #   _parse_explain, _parse_create_table, _parse_insert, _parse_select, _parse_update
    #   _parse_expr, _parse_optional_where, _parse_column_list
    #   _consume_keyword, _consume_ident, _consume_symbol, _consume_literal
    #   _peek_keyword, _peek_symbol, _current

    @classmethod
    def from_tokens(cls, tokens: list[Token]) -> Parser:
        parser = cls.__new__(cls)
        parser.tokens = tokens
        parser.pos = 0
        return parser


def parse(sql: str) -> ast.Statement:
    return Parser(sql).parse()
