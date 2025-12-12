from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
from .lexer import Lexer, Token
from .errors import ConfigError


@dataclass
class ASTConstRef:
    name: str
    token: Token


class Parser:
    def __init__(self, text: str):
        self.lexer = Lexer(text)
        self.cur = self.lexer.next_token()

    def _eat(self, kind: str) -> Token:
        if self.cur.kind != kind:
            raise ConfigError(
                f"Expected {kind}, got {self.cur.kind}",
                self.cur.line,
                self.cur.col,
            )
        tok = self.cur
        self.cur = self.lexer.next_token()
        return tok

    def parse_program(self) -> List[Tuple[str, Any]]:
        """
        program := (def_stmt)* EOF
        def_stmt := 'def' IDENT ':=' value
        """
        items: List[Tuple[str, Any]] = []
        while self.cur.kind != "EOF":
            self._eat("DEF")
            name_tok = self._eat("IDENT")
            self._eat("ASSIGN")
            val = self.parse_value()
            items.append((name_tok.value, val))
        return items

    def parse_value(self) -> Any:
        """
        value := NUMBER | STRING | list_expr | CONSTREF
        list_expr := '(' 'list' value* ')'
        """
        if self.cur.kind == "NUMBER":
            tok = self._eat("NUMBER")
            return int(tok.value)  # целые
        if self.cur.kind == "STRING":
            tok = self._eat("STRING")
            return tok.value
        if self.cur.kind == "CONSTREF":
            tok = self._eat("CONSTREF")
            return ASTConstRef(tok.value, tok)
        if self.cur.kind == "LPAREN":
            self._eat("LPAREN")
            self._eat("LIST")
            arr = []
            while self.cur.kind != "RPAREN":
                if self.cur.kind == "EOF":
                    raise ConfigError("Unterminated list: expected ')'", self.cur.line, self.cur.col)
                arr.append(self.parse_value())
            self._eat("RPAREN")
            return arr

        raise ConfigError(
            f"Expected value, got {self.cur.kind}",
            self.cur.line,
            self.cur.col,
        )


def evaluate(program: List[Tuple[str, Any]]) -> Dict[str, Any]:
    """
    Однопроходная трансляция:
    - def NAME := value
    - #{NAME} должно ссылаться на уже определённую константу (иначе ошибка)
    """
    env: Dict[str, Any] = {}

    def eval_value(v: Any) -> Any:
        if isinstance(v, ASTConstRef):
            if v.name not in env:
                raise ConfigError(f"Undefined constant: {v.name}", v.token.line, v.token.col)
            return env[v.name]
        if isinstance(v, list):
            return [eval_value(x) for x in v]
        return v

    for name, raw in program:
        env[name] = eval_value(raw)
    return env
