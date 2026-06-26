"""Tokenize SQL source text.

Phase 5a — SQL layer. Start with the lexer.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TokenType(Enum):
    KEYWORD = "keyword"
    IDENT = "ident"
    NUMBER = "number"
    STRING = "string"
    SYMBOL = "symbol"
    EOF = "eof"


@dataclass
class Token:
    type: TokenType
    value: str
    pos: int


# Hints for your lexer — keywords to recognize (case-insensitive):
# CREATE TABLE INSERT INTO VALUES SELECT FROM WHERE UPDATE SET JOIN ON EXPLAIN AND OR
#
# Symbols: , ( ) = != <= >= < > *
# Skip whitespace. Strings are single-quoted ('hello', ''escaped'').


def lex(sql: str) -> list[Token]:
    """Return a flat token stream for a SQL string."""
    # TODO(phase-5a): tokenize sql into a list[Token], append EOF at the end
    raise NotImplementedError
