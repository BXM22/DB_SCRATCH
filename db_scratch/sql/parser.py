"""Recursive-descent parser for the supported SQL subset.

Phase 5b — after lexer. Build AST nodes defined in ast.py.
"""

from __future__ import annotations

from db_scratch.sql import ast
from db_scratch.sql.lexer import Token, TokenType, lex


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, sql: str) -> None:
        self.tokens = lex(sql)
        self.pos = 0

    def parse(self) -> ast.Statement:
        if self._peek_keyword("EXPLAIN"):
            return self._parse_explain()
        if self._peek_keyword("CREATE"):
            return self._parse_create_table()
        if self._peek_keyword("INSERT"):
            return self._parse_insert()
        if self._peek_keyword("SELECT"):
            return self._parse_select()
        if self._peek_keyword("UPDATE"):
            return self._parse_update()
        raise ParseError(f"unexpected token: {self._current().value!r}")

    def _parse_explain(self) -> ast.Explain:
        self._consume_keyword("EXPLAIN")
        inner = Parser.from_tokens(self.tokens[self.pos :]).parse()
        return ast.Explain(inner)

    def _parse_create_table(self) -> ast.CreateTable:
        self._consume_keyword("CREATE")
        self._consume_keyword("TABLE")
        table_name = self._consume_ident()
        self._consume_symbol("(")
        columns = self._parse_column_defs()
        self._consume_symbol(")")
        return ast.CreateTable(table_name, columns)

    def _parse_column_defs(self) -> list[ast.ColumnDef]:
        columns: list[ast.ColumnDef] = []
        while True:
            name = self._consume_ident()
            type_name = self._consume_type_name()
            columns.append(ast.ColumnDef(name, type_name))
            if self._peek_symbol(","):
                self._consume_symbol(",")
                continue
            break
        return columns

    def _parse_insert(self) -> ast.Insert:
        self._consume_keyword("INSERT")
        self._consume_keyword("INTO")
        table_name = self._consume_ident()
        self._consume_symbol("(")
        columns = self._parse_ident_list()
        self._consume_symbol(")")
        self._consume_keyword("VALUES")
        self._consume_symbol("(")
        values = self._parse_value_list()
        self._consume_symbol(")")
        return ast.Insert(table_name, columns, values)

    def _parse_select(self) -> ast.Select:
        self._consume_keyword("SELECT")
        columns = self._parse_select_columns()
        self._consume_keyword("FROM")
        table_name = self._consume_ident()
        joins: list[ast.Join] = []
        while self._peek_keyword("JOIN"):
            self._consume_keyword("JOIN")
            join_table = self._consume_ident()
            self._consume_keyword("ON")
            on_expr = self._parse_expr()
            joins.append(ast.Join(join_table, on_expr))
        where = self._parse_optional_where()
        return ast.Select(columns, table_name, where, joins)

    def _parse_update(self) -> ast.Update:
        self._consume_keyword("UPDATE")
        table_name = self._consume_ident()
        self._consume_keyword("SET")
        assignments = self._parse_assignments()
        where = self._parse_optional_where()
        return ast.Update(table_name, assignments, where)

    def _parse_select_columns(self) -> list[str]:
        if self._peek_symbol("*"):
            self._consume_symbol("*")
            return ["*"]
        return self._parse_ident_list()

    def _parse_ident_list(self) -> list[str]:
        names = [self._consume_ident()]
        while self._peek_symbol(","):
            self._consume_symbol(",")
            names.append(self._consume_ident())
        return names

    def _parse_value_list(self) -> list[object]:
        values = [self._consume_literal()]
        while self._peek_symbol(","):
            self._consume_symbol(",")
            values.append(self._consume_literal())
        return values

    def _parse_assignments(self) -> dict[str, object]:
        assignments: dict[str, object] = {}
        while True:
            col = self._consume_ident()
            self._consume_symbol("=")
            assignments[col] = self._consume_literal()
            if self._peek_symbol(","):
                self._consume_symbol(",")
                continue
            break
        return assignments

    def _parse_optional_where(self) -> ast.Expr | None:
        if not self._peek_keyword("WHERE"):
            return None
        self._consume_keyword("WHERE")
        return self._parse_expr()

    def _parse_expr(self) -> ast.Expr:
        return self._parse_or_expr()

    def _parse_or_expr(self) -> ast.Expr:
        left = self._parse_and_expr()
        while self._peek_keyword("OR"):
            self._consume_keyword("OR")
            right = self._parse_and_expr()
            left = ast.BinaryExpr("OR", left, right)
        return left

    def _parse_and_expr(self) -> ast.Expr:
        left = self._parse_comparison()
        while self._peek_keyword("AND"):
            self._consume_keyword("AND")
            right = self._parse_comparison()
            left = ast.BinaryExpr("AND", left, right)
        return left

    def _parse_comparison(self) -> ast.Expr:
        left = self._parse_primary()
        if self._current().type == TokenType.SYMBOL and self._current().value in {
            "=",
            "!=",
            "<",
            "<=",
            ">",
            ">=",
        }:
            op = self._current().value
            self.pos += 1
            right = self._parse_primary()
            return ast.BinaryExpr(op, left, right)  # type: ignore[arg-type]
        return left

    def _parse_primary(self) -> ast.Expr:
        token = self._current()
        if token.type == TokenType.NUMBER:
            self.pos += 1
            if "." in token.value:
                return ast.Literal(float(token.value))
            return ast.Literal(int(token.value))
        if token.type == TokenType.STRING:
            self.pos += 1
            return ast.Literal(token.value)
        if token.type == TokenType.IDENT:
            name = self._consume_ident()
            return ast.ColumnRef(name)
        raise ParseError(f"unexpected token in expression: {token.value!r}")

    def _consume_keyword(self, keyword: str) -> None:
        token = self._current()
        if token.type != TokenType.KEYWORD or token.value != keyword:
            raise ParseError(f"expected keyword {keyword}, got {token.value!r}")
        self.pos += 1

    def _consume_type_name(self) -> str:
        token = self._current()
        if token.type in (TokenType.IDENT, TokenType.KEYWORD):
            self.pos += 1
            return token.value.upper()
        raise ParseError(f"expected type name, got {token.value!r}")

    def _consume_ident(self) -> str:
        token = self._current()
        if token.type != TokenType.IDENT:
            raise ParseError(f"expected identifier, got {token.value!r}")
        self.pos += 1
        return token.value

    def _consume_symbol(self, symbol: str) -> None:
        token = self._current()
        if token.type != TokenType.SYMBOL or token.value != symbol:
            raise ParseError(f"expected symbol {symbol!r}, got {token.value!r}")
        self.pos += 1

    def _consume_literal(self) -> object:
        token = self._current()
        if token.type == TokenType.NUMBER:
            self.pos += 1
            return int(token.value) if "." not in token.value else float(token.value)
        if token.type == TokenType.STRING:
            self.pos += 1
            return token.value
        raise ParseError(f"expected literal, got {token.value!r}")

    def _peek_keyword(self, keyword: str) -> bool:
        token = self._current()
        return token.type == TokenType.KEYWORD and token.value == keyword

    def _peek_symbol(self, symbol: str) -> bool:
        token = self._current()
        return token.type == TokenType.SYMBOL and token.value == symbol

    def _current(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos]

    @classmethod
    def from_tokens(cls, tokens: list[Token]) -> Parser:
        parser = cls.__new__(cls)
        parser.tokens = tokens
        parser.pos = 0
        return parser


def parse(sql: str) -> ast.Statement:
    return Parser(sql).parse()
