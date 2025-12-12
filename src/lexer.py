from dataclasses import dataclass
from typing import Optional
from .errors import ConfigError


@dataclass(frozen=True)
class Token:
    kind: str
    value: Optional[str]
    line: int
    col: int


class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.i = 0
        self.line = 1
        self.col = 1

    def _peek(self, n: int = 0) -> str:
        j = self.i + n
        return self.text[j] if j < len(self.text) else ""

    def _advance(self, n: int = 1) -> None:
        for _ in range(n):
            if self.i >= len(self.text):
                return
            ch = self.text[self.i]
            self.i += 1
            if ch == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1

    def _error(self, msg: str) -> ConfigError:
        # короткий сниппет строки
        start = self.i
        while start > 0 and self.text[start - 1] != "\n":
            start -= 1
        end = self.i
        while end < len(self.text) and self.text[end] != "\n":
            end += 1
        line_text = self.text[start:end]
        caret_pos = max(0, self.col - 1)
        snippet = line_text + "\n" + (" " * caret_pos) + "^"
        return ConfigError(msg, self.line, self.col, snippet)

    def _skip_ws_and_comments(self) -> None:
        while True:
            ch = self._peek()
            # whitespace
            if ch and ch.isspace():
                self._advance()
                continue

            # single-line comment: % ... \n
            if ch == "%":
                while self._peek() and self._peek() != "\n":
                    self._advance()
                continue

            # multi-line comment: {{!-- ... --}}
            if self._peek() == "{" and self._peek(1) == "{" and self._peek(2) == "!" and self._peek(3) == "-" and self._peek(4) == "-":
                self._advance(5)  # consume {{!--
                while True:
                    if not self._peek():
                        raise self._error("Unterminated multiline comment")
                    if self._peek() == "-" and self._peek(1) == "-" and self._peek(2) == "}" and self._peek(3) == "}":
                        self._advance(4)  # consume --}}
                        break
                    self._advance()
                continue

            break

    def next_token(self) -> Token:
        self._skip_ws_and_comments()

        if self.i >= len(self.text):
            return Token("EOF", None, self.line, self.col)

        ch = self._peek()
        line, col = self.line, self.col

        # symbols / operators
        if ch == "(":
            self._advance()
            return Token("LPAREN", "(", line, col)
        if ch == ")":
            self._advance()
            return Token("RPAREN", ")", line, col)
        if ch == ":" and self._peek(1) == "=":
            self._advance(2)
            return Token("ASSIGN", ":=", line, col)

        # constref: #{NAME}
        if ch == "#" and self._peek(1) == "{":
            self._advance(2)
            name = self._read_ident()
            if self._peek() != "}":
                raise self._error("Expected '}' after constant name")
            self._advance()
            return Token("CONSTREF", name, line, col)

        # string: @"...."
        if ch == "@" and self._peek(1) == "\"":
            self._advance(2)  # consume @"
            s = []
            while True:
                if not self._peek():
                    raise self._error("Unterminated string literal")
                c = self._peek()
                if c == "\"":
                    self._advance()
                    break
                # простой вариант без экранирования в исходном языке
                if c == "\n":
                    raise self._error("Newline inside string literal")
                s.append(c)
                self._advance()
            return Token("STRING", "".join(s), line, col)

        # number: [+-]?([1-9][0-9]*|0)
        if ch in "+-" or ch.isdigit():
            # чтобы не спутать + как часть чего-то ещё — тут ок, других операций нет
            num = self._read_number()
            return Token("NUMBER", num, line, col)

        # keywords / identifiers
        if ch.isalpha():
            word = self._read_word()
            if word == "def":
                return Token("DEF", word, line, col)
            if word == "list":
                return Token("LIST", word, line, col)
            # IDENT: [A-Z]+
            if not word.isupper():
                raise self._error("Identifier must match [A-Z]+")
            return Token("IDENT", word, line, col)

        raise self._error(f"Unexpected character: {repr(ch)}")

    def _read_word(self) -> str:
        out = []
        while self._peek() and (self._peek().isalpha()):
            out.append(self._peek())
            self._advance()
        return "".join(out)

    def _read_ident(self) -> str:
        out = []
        while self._peek() and self._peek().isalpha():
            out.append(self._peek())
            self._advance()
        name = "".join(out)
        if not name or not name.isupper():
            raise self._error("Constant name must match [A-Z]+")
        return name

    def _read_number(self) -> str:
        out = []
        if self._peek() in "+-":
            out.append(self._peek())
            self._advance()
        if not self._peek().isdigit():
            raise self._error("Expected digit after sign")
        # read digits
        if self._peek() == "0":
            out.append("0")
            self._advance()
        else:
            if self._peek() < "1" or self._peek() > "9":
                raise self._error("Invalid number")
            while self._peek() and self._peek().isdigit():
                out.append(self._peek())
                self._advance()
        # запрет на ведущие нули типа 01
        if len(out) >= 2 and out[-2] in "+-" and out[-1] == "0":
            # +0 / -0 допустим по regex? regex допускает 0, да, значит +0/-0 тоже допустим.
            pass
        if self._peek() and self._peek().isdigit():
            # если было 0 и дальше цифра — это 01
            raise self._error("Leading zeros are not allowed")
        return "".join(out)
