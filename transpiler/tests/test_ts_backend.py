"""Tests for TypeScript backend."""

from src.backend.ts import TsBackend
from tests.fixture import make_fixture

EXPECTED = """\
const EOF: number = -1;

interface Scanner {
  peek(): number;
  advance(): void;
}

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
      return [new Token(), false];
    }
    let text: string = this.source.slice(start, this.pos);
    return [new Token("word", text, start), true];
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
    let result: [Token, boolean] = lx.scanWord();
    let tok: Token = result[0];
    let ok: boolean = result[1];
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
}

function sumPositions(tokens: Token[]): number {
  let sum: number = 0;
  for (let i: number = 0; (i < tokens.length); i = (i + 1)) {
    sum = (sum + tokens[i].pos);
  }
  return sum;
}

function firstWordPos(tokens: Token[]): number {
  let pos: number = -1;
  for (const tok of tokens) {
    if ((tok.kind === "word")) {
      pos = tok.pos;
      break;
    }
  }
  return pos;
}

function maxInt(a: number, b: number): number {
  return ((a > b) ? a : b);
}

function defaultKinds(): Map<string, number> {
  return new Map([["word", 1], ["num", 2], ["op", 3]]);
}

function scopedWork(x: number): number {
  let result: number = 0;
  {
    let temp: number = (x * 2);
    result = (temp + 1);
  }
  return result;
}

function kindPriority(kind: string): number {
  switch (kind) {
    case "word":
      return 1;
      break;
    case "num":
    case "float":
      return 2;
      break;
    case "op":
      return 3;
      break;
    default:
      return 0;
  }
}

function safeTokenize(source: string): Token[] {
  let tokens: Token[] = [];
  try {
    tokens = tokenize(source);
  } catch (e) {
    tokens = [];
  }
  return tokens;
}

function pi(): number {
  return 3.14159;
}"""


def test_fixture_emits_correct_typescript() -> None:
    module = make_fixture()
    backend = TsBackend()
    output = backend.emit(module)
    assert output == EXPECTED
