"""Tests for Swift backend."""

from src.backend.swift import SwiftBackend
from tests.fixture import make_fixture

EXPECTED = """\
import Foundation

enum Constants {
    static let EOF: Int = -1
}

protocol Scanner {
    func peek() -> Int
    func advance()
}

class Token {
    var kind: String
    var text: String
    var pos: Int

    init(kind: String, text: String, pos: Int) {
        self.kind = kind
        self.text = text
        self.pos = pos
    }

    func isWord() -> Bool {
        return (self.kind == "word")
    }
}

class Lexer {
    var source: String
    var pos: Int
    var current: Token?

    init(source: String, pos: Int, current: Token?) {
        self.source = source
        self.pos = pos
        self.current = current
    }

    func peek() -> Int {
        if (self.pos >= self.source.count) {
            return Constants.EOF
        }
        return self.source[self.pos]
    }

    func advance() {
        self.pos += 1
    }

    func scanWord() -> (Token, Bool) {
        let start: Int = self.pos
        while ((self.peek() != Constants.EOF) && !isSpace(self.peek())) {
            self.advance()
        }
        if (self.pos == start) {
            return (Token(), false)
        }
        let text: String = String(self.source[self.source.index(self.source.startIndex, offsetBy: start)..<self.source.index(self.source.startIndex, offsetBy: self.pos)])
        return (Token(kind: "word", text: text, pos: start), true)
    }
}

func isSpace(_ ch: Int) -> Bool {
    return ((ch == 32) || (ch == 10))
}

func tokenize(_ source: String) -> [Token] {
    var lx: Lexer = Lexer(source: source, pos: 0, current: nil)
    var tokens: [Token] = [Token]()
    while (lx.peek() != Constants.EOF) {
        let ch: Int = lx.peek()
        if isSpace(ch) {
            lx.advance()
            continue
        }
        let result: (Token, Bool) = lx.scanWord()
        let tok: Token = result.0
        let ok: Bool = result.1
        if !ok {
            fatalError("unexpected character")
        }
        tokens.append(tok)
    }
    return tokens
}

func countWords(_ tokens: [Token]) -> Int {
    var count: Int = 0
    for tok in tokens {
        if (tok.kind == "word") {
            count += 1
        }
    }
    return count
}

func formatToken(_ tok: Token) -> String {
    return tok.kind + ":" + tok.text
}

func findToken(_ tokens: [Token], _ kind: String) -> Token? {
    for tok in tokens {
        if (tok.kind == kind) {
            return tok
        }
    }
    return nil
}

func exampleNilCheck(_ tokens: [Token]) -> String {
    let tok: Token? = findToken(tokens, "word")
    if (tok == nil) {
        return ""
    }
    return tok!.text
}

func sumPositions(_ tokens: [Token]) -> Int {
    var sum: Int = 0
    var i: Int = 0
    while (i < tokens.count) {
        sum = (sum + tokens[i].pos)
        i = (i + 1)
    }
    return sum
}

func firstWordPos(_ tokens: [Token]) -> Int {
    var pos: Int = -1
    for tok in tokens {
        if (tok.kind == "word") {
            pos = tok.pos
            break
        }
    }
    return pos
}

func maxInt(_ a: Int, _ b: Int) -> Int {
    return ((a > b) ? a : b)
}

func defaultKinds() -> [String: Int] {
    return ["word": 1, "num": 2, "op": 3]
}

func scopedWork(_ x: Int) -> Int {
    var result: Int = 0
    do {
        let temp: Int = (x * 2)
        result = (temp + 1)
    }
    return result
}

func kindPriority(_ kind: String) -> Int {
    switch kind {
    case "word":
        return 1
    case "num", "float":
        return 2
    case "op":
        return 3
    default:
        return 0
    }
}

func safeTokenize(_ source: String) -> [Token] {
    var tokens: [Token] = [Token]()
    do {
        tokens = tokenize(source)
    } catch let e {
        tokens = [Token]()
    }
    return tokens
}

func pi() -> Double {
    return 3.14159
}

func describeToken(_ tok: Token) -> String {
    return "Token(\\(tok.kind), \\(tok.text), \\(tok.pos))"
}

func setFirstKind(_ tokens: [Token], _ kind: String) {
    if (tokens.count > 0) {
        tokens[0] = Token(kind: kind, text: "", pos: 0)
    }
}

func makeIntSlice(_ n: Int) -> [Int] {
    return [Int]()
}

func intToFloat(_ n: Int) -> Double {
    return Double(n)
}

func knownKinds() -> Set<String> {
    return Set(["word", "num", "op"])
}

func callStatic() -> Token {
    return Token.empty()
}

func newKindMap() -> [String: Int] {
    return [String: Int]()
}

func getArrayFirst(_ arr: [Int]) -> Int {
    return arr[0]
}

func maybeGet(_ tokens: [Token], _ idx: Int) -> Token? {
    if (idx >= tokens.count) {
        return nil
    }
    return tokens[idx]
}

func setViaPtr(_ ptr: Int, _ val: Int) {
    ptr = val
}

func identityStr(_ s: String) -> String {
    return s
}

func acceptUnion(_ obj: Any) -> Bool {
    return true
}
"""


def test_fixture_emits_correct_swift() -> None:
    module = make_fixture()
    backend = SwiftBackend()
    output = backend.emit(module)
    assert output == EXPECTED
