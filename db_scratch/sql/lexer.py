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


KEYWORDS = {
    "CREATE",
    "TABLE",
    "INSERT",
    "INTO",
    "VALUES",
    "SELECT",
    "FROM",
    "WHERE",
    "UPDATE",
    "SET",
    "JOIN",
    "ON",
    "EXPLAIN",
    "AND",
    "OR",
    "INT",
    "TEXT",
}

SYMBOLS = {
    ",",
    "(",
    ")",
    "=",
    "!=",
    "<=",
    ">=",
    "<",
    ">",
    "*",
}


def lex(sql: str) -> list[Token]:
    """Return a flat token stream for a SQL string."""
    tokens: list[Token] = []
    pos = 0
    length = len(sql)

    while pos < length:
        if sql[pos].isspace():
            pos += 1
            continue

        start = pos

        if sql[pos] == "'":
            pos += 1
            chars: list[str] = []
            while pos < length:
                if sql[pos] == "'":
                    if pos + 1 < length and sql[pos + 1] == "'":
                        chars.append("'")
                        pos += 2
                        continue
                    pos += 1
                    break
                chars.append(sql[pos])
                pos += 1
            tokens.append(Token(TokenType.STRING, "".join(chars), start))
            continue

        if sql[pos].isdigit():
            while pos < length and (sql[pos].isdigit() or sql[pos] == "."):
                pos += 1
            tokens.append(Token(TokenType.NUMBER, sql[start:pos], start))
            continue

        if sql[pos].isalpha() or sql[pos] == "_":
            while pos < length and (sql[pos].isalnum() or sql[pos] == "_"):
                pos += 1
            word = sql[start:pos]
            upper = word.upper()
            if upper in KEYWORDS:
                tokens.append(Token(TokenType.KEYWORD, upper, start))
            else:
                tokens.append(Token(TokenType.IDENT, word, start))
            continue

        matched = False
        for sym in ("!=", "<=", ">=", ",", "(", ")", "=", "<", ">", "*"):
            if sql.startswith(sym, pos):
                tokens.append(Token(TokenType.SYMBOL, sym, start))
                pos += len(sym)
                matched = True
                break
        if matched:
            continue

        raise ValueError(f"unexpected character at position {pos}: {sql[pos]!r}")

    tokens.append(Token(TokenType.EOF, "", pos))
    return tokens
