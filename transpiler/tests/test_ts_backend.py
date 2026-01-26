"""Tests for TypeScript backend."""

from src.backend.ts import TsBackend
from tests.fixture import make_fixture

EXPECTED = """\
const EOF: number = -1;

class Token {
  kind: string;
  text: string;
  pos: number;

  constructor(kind: string, text: string, pos: number) {
    this.kind = kind;
    this.text = text;
    this.pos = pos;
  }

  isWord(): boolean {
    return (this.kind === "word");
  }
}

class Lexer {
  source: string;
  pos: number;
  current: Token | null;

  constructor(source: string, pos: number, current: Token | null) {
    this.source = source;
    this.pos = pos;
    this.current = current;
  }

  peek(): number {
    if ((this.pos >= this.source.length)) {
      return EOF;
    }
    return this.source[this.pos];
  }

  advance(): void {
    this.pos += 1;
  }

  scanWord(): [Token, boolean] {
    let start: number = this.pos;
    while (((this.peek() !== EOF) && !isSpace(this.peek()))) {
      this.advance();
    }
    if ((this.pos === start)) {
      return new Token();
    }
    let text: string = this.source.slice(start, this.pos);
    return new Token("word", text, start);
  }
}

function isSpace(ch: number): boolean {
  return ((ch === 32) || (ch === 10));
}

function tokenize(source: string): Token[] {
  let lx: Lexer = new Lexer(source, 0, null);
  let tokens: Token[] = [];
  while ((lx.peek() !== EOF)) {
    let ch: number = lx.peek();
    if (isSpace(ch)) {
      lx.advance();
      continue;
    }
    let tok: Token;
    let ok: boolean;
    if (!ok) {
      throw new ParseError("unexpected character", lx.pos);
    }
    tokens.push(tok);
  }
  return tokens;
}

function countWords(tokens: Token[]): number {
  let count: number = 0;
  for (const tok of tokens) {
    if ((tok.kind === "word")) {
      count += 1;
    }
  }
  return count;
}

function formatToken(tok: Token): string {
  return tok.kind + ":" + tok.text;
}

function findToken(tokens: Token[], kind: string): Token | null {
  for (const tok of tokens) {
    if ((tok.kind === kind)) {
      return tok;
    }
  }
  return null;
}

function exampleNilCheck(tokens: Token[]): string {
  let tok: Token | null = findToken(tokens, "word");
  if ((tok === null)) {
    return "";
  }
  return tok.text;
}"""


def test_fixture_emits_correct_typescript() -> None:
    module = make_fixture()
    backend = TsBackend()
    output = backend.emit(module)
    assert output == EXPECTED
