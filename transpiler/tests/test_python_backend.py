"""Tests for Python backend."""

from src.backend.python import PythonBackend
from tests.fixture import make_fixture

EXPECTED = """\
\"\"\"Generated Python code.\"\"\"

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

EOF: int = -1


class Scanner(Protocol):
    def peek(self) -> int: ...
    def advance(self) -> None: ...


@dataclass
class Token:
    kind: str
    text: str
    pos: int

    def is_word(self) -> bool:
        return self.kind == "word"


@dataclass
class Lexer:
    source: str
    pos: int
    current: Token | None

    def peek(self) -> int:
        if self.pos >= len(self.source):
            return EOF
        return self.source[self.pos]

    def advance(self) -> None:
        self.pos += 1

    def scan_word(self) -> tuple[Token, bool]:
        start: int = self.pos
        while self.peek() != EOF and not is_space(self.peek()):
            self.advance()
        if self.pos == start:
            return (Token(), False)
        text: str = self.source[start:self.pos]
        return (Token(kind="word", text=text, pos=start), True)


def is_space(ch: int) -> bool:
    return ch == 32 or ch == 10


def tokenize(source: str) -> list[Token]:
    lx: Lexer = Lexer(source=source, pos=0, current=None)
    tokens: list[Token] = []
    while lx.peek() != EOF:
        ch: int = lx.peek()
        if is_space(ch):
            lx.advance()
            continue
        result: tuple[Token, bool] = lx.scan_word()
        tok: Token = result[0]
        ok: bool = result[1]
        if not ok:
            raise ParseError("unexpected character", lx.pos)
        tokens.append(tok)
    return tokens


def count_words(tokens: list[Token]) -> int:
    count: int = 0
    for tok in tokens:
        if tok.kind == "word":
            count += 1
    return count


def format_token(tok: Token) -> str:
    return tok.kind + ":" + tok.text


def find_token(tokens: list[Token], kind: str) -> Token | None:
    for tok in tokens:
        if tok.kind == kind:
            return tok
    return None


def example_nil_check(tokens: list[Token]) -> str:
    tok: Token | None = find_token(tokens, "word")
    if tok is None:
        return ""
    return tok.text


def sum_positions(tokens: list[Token]) -> int:
    sum_: int = 0
    for i in range(len(tokens)):
        sum_ += tokens[i].pos
    return sum_


def first_word_pos(tokens: list[Token]) -> int:
    pos: int = -1
    for tok in tokens:
        if tok.kind == "word":
            pos = tok.pos
            break
    return pos


def max_int(a: int, b: int) -> int:
    return a if a > b else b


def default_kinds() -> dict[str, int]:
    return {"word": 1, "num": 2, "op": 3}


def scoped_work(x: int) -> int:
    result: int = 0
    temp: int = x * 2
    result = temp + 1
    return result


def kind_priority(kind: str) -> int:
    match kind:
        case "word":
            return 1
        case "num" | "float":
            return 2
        case "op":
            return 3
        case _:
            return 0


def safe_tokenize(source: str) -> list[Token]:
    tokens: list[Token] = []
    try:
        tokens = tokenize(source)
    except Exception as e:
        tokens = []
    return tokens


def pi() -> float:
    return 3.14159


def describe_token(tok: Token) -> str:
    return f"Token({tok.kind}, {tok.text}, {tok.pos})"


def set_first_kind(tokens: list[Token], kind: str) -> None:
    if len(tokens) > 0:
        tokens[0] = Token(kind=kind, text="", pos=0)


def make_int_slice(n: int) -> list[int]:
    return [0] * n


def int_to_float(n: int) -> float:
    return n


def known_kinds() -> set[str]:
    return {"word", "num", "op"}


def call_static() -> Token:
    return Token.empty()


def new_kind_map() -> dict[str, int]:
    return {}


def get_array_first(arr: list[int]) -> int:
    return arr[0]


def maybe_get(tokens: list[Token], idx: int) -> Token | None:
    if idx >= len(tokens):
        return None
    return tokens[idx]


def set_via_ptr(ptr: int, val: int) -> None:
    ptr = val


def identity_str(s: str) -> str:
    return s


def accept_union(obj: Token | Lexer) -> bool:
    return True"""


def test_fixture_emits_correct_python() -> None:
    module = make_fixture()
    backend = PythonBackend()
    output = backend.emit(module)
    assert output == EXPECTED
