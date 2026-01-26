"""Tests for Go backend."""

from src.backend.go import GoBackend
from tests.fixture import make_fixture

EXPECTED = """\
package fixture

import (
	"fmt"
	"strings"
)

// quoteStackEntry holds pushed quote state (single, double)
type quoteStackEntry struct {
	Single bool
	Double bool
}

const (
	Eof = -1
)

type Token struct {
	Kind string
	Text string
	Pos int
}

func (t *Token) IsWord() bool {
	return (t.Kind == "word")
}

type Lexer struct {
	Source string
	Pos int
	Current *Token
}

func (l *Lexer) Peek() int {
	if (lx.Pos >= len(lx.Source)) {
		return Eof
	}
	return lx.Source[lx.Pos]
}

func (l *Lexer) Advance()  {
	lx.Pos += 1
}

func (l *Lexer) ScanWord() struct{ F0 Token, F1 bool } {
	var start int = lx.Pos
	for ((lx.Peek() != Eof) && !IsSpace(lx.Peek())) {
		lx.Advance()
	}
	if (lx.Pos == start) {
		return &Token{}, false
	}
	var text string = lx.Source[start:lx.Pos]
	return &Token{Kind: "word", Text: text, Pos: start}, true
}

func IsSpace(ch int) bool {
	return ((ch == 32) || (ch == 10))
}

func Tokenize(source string) []Token {
	var lx Lexer = &Lexer{Source: source, Pos: 0, Current: nil}
	var tokens []Token = []Token{}
	for (lx.Peek() != Eof) {
		var ch int = lx.Peek()
		if IsSpace(ch) {
			lx.Advance()
			continue
		}
		var result struct{ F0 Token, F1 bool } = lx.ScanWord()
		var tok Token = result[0]
		var ok bool = result[1]
		if !ok {
			panic("unexpected character")
		}
		tokens = append(tokens, tok)
	}
	return tokens
}

func CountWords(tokens []Token) int {
	var count int = 0
	for _, tok := range tokens {
		if (tok.Kind == "word") {
			count += 1
		}
	}
	return count
}

func FormatToken(tok Token) string {
	return (tok.Kind + ":" + tok.Text)
}

func FindToken(tokens []Token, kind string) *Token {
	for _, tok := range tokens {
		if (tok.Kind == kind) {
			return tok
		}
	}
	return nil
}

func ExampleNilCheck(tokens []Token) string {
	var tok *Token = FindToken(tokens, "word")
	if tok == nil {
		return ""
	}
	return tok.Text
}

func SumPositions(tokens []Token) int {
	var sum int = 0
	for i := 0; (i < len(tokens)); i = (i + 1) {
		sum = (sum + tokens[i].Pos)
	}
	return sum
}

func FirstWordPos(tokens []Token) int {
	var pos int = -1
	for _, tok := range tokens {
		if (tok.Kind == "word") {
			pos = tok.Pos
			break
		}
	}
	return pos
}

func MaxInt(a int, b int) int {
	return func() int { if (a > b) { return a } else { return b } }()
}

func DefaultKinds() map[string]int {
	return map[string]int{"word": 1, "num": 2, "op": 3}
}

func ScopedWork(x int) int {
	var result int = 0
	{
		var temp int = (x * 2)
		result = (temp + 1)
	}
	return result
}

func KindPriority(kind string) int {
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

func SafeTokenize(source string) []Token {
	var tokens []Token = []Token{}
	func() {
		defer func() {
			if e := recover(); e != nil {
				tokens = []Token{}
			}
		}()
		tokens = Tokenize(source)
	}()
	return tokens
}

func Pi() float64 {
	return 3.14159
}

func DescribeToken(tok Token) string {
	return fmt.Sprintf("Token(%v, %v, %v)", tok.Kind, tok.Text, tok.Pos)
}

func SetFirstKind(tokens []Token, kind string) {
	if (len(tokens) > 0) {
		tokens[0] = &Token{Kind: kind, Text: "", Pos: 0}
	}
}

func MakeIntSlice(n int) []int {
	return make([]int, n)
}

func IntToFloat(n int) float64 {
	return float64(n)
}

func KnownKinds() map[string]struct{} {
	return map[string]struct{}{"word": {}, "num": {}, "op": {}}
}

func CallStatic() Token {
	return Token.Empty()
}

func NewKindMap() map[string]int {
	return make(map[string]int)
}

func GetArrayFirst(arr [10]int) int {
	return arr[0]
}

func MaybeGet(tokens []Token, idx int) *Token {
	if (idx >= len(tokens)) {
		return nil
	}
	return tokens[idx]
}

func SetViaPtr(ptr *int, val int) {
	*ptr = val
}

func IdentityStr(s string) string {
	return s
}

func AcceptUnion(obj interface{}) bool {
	return true
}
"""


def test_fixture_emits_correct_go() -> None:
    module = make_fixture()
    backend = GoBackend()
    output = backend.emit(module)
    assert output == EXPECTED
