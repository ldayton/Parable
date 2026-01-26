"""Tests for Go backend."""

from src.backend.go import GoBackend
from tests.fixture import make_fixture

EXPECTED = """\
package fixture

import (
	"fmt"
	"strings"
	"unicode"
)

// quoteStackEntry holds pushed quote state (single, double)
type quoteStackEntry struct {
	Single bool
	Double bool
}

func _strIsAlnum(s string) bool {
	for _, r := range s {
		if !unicode.IsLetter(r) && !unicode.IsDigit(r) {
			return false
		}
	}
	return len(s) > 0
}

func _strIsAlpha(s string) bool {
	for _, r := range s {
		if !unicode.IsLetter(r) {
			return false
		}
	}
	return len(s) > 0
}

func _strIsDigit(s string) bool {
	for _, r := range s {
		if !unicode.IsDigit(r) {
			return false
		}
	}
	return len(s) > 0
}

func _strIsSpace(s string) bool {
	for _, r := range s {
		if !unicode.IsSpace(r) {
			return false
		}
	}
	return len(s) > 0
}

func _strIsUpper(s string) bool {
	for _, r := range s {
		if !unicode.IsUpper(r) {
			return false
		}
	}
	return len(s) > 0
}

func _strIsLower(s string) bool {
	for _, r := range s {
		if !unicode.IsLower(r) {
			return false
		}
	}
	return len(s) > 0
}

const (
	EOF = -1
)

type Token struct {
	Kind string
	Text string
	Pos int
}

func (t *Token) IsWord() bool {
	return t.Kind == "word"
}

type Lexer struct {
	Source string
	Pos int
	Current *Token
}

func (lx *Lexer) Peek() int {
	if lx.Pos >= len(lx.Source) {
		return EOF
	}
	return lx.Source[lx.Pos]
}

func (lx *Lexer) Advance()  {
	lx.Pos++
}

func (lx *Lexer) ScanWord() (Token, bool) {
	start := lx.Pos
	for lx.Peek() != EOF && !IsSpace(lx.Peek()) {
		lx.Advance()
	}
	if lx.Pos == start {
		return &Token{}, false
	}
	text := lx.Source[start:lx.Pos]
	return &Token{Kind: "word", Text: text, Pos: start}, true
}

func IsSpace(ch int) bool {
	return ch == 32 || ch == 10
}

func Tokenize(source string) []Token {
	lx := &Lexer{Source: source, Pos: 0, Current: nil}
	tokens := []Token{}
	for lx.Peek() != EOF {
		ch := lx.Peek()
		if IsSpace(ch) {
			lx.Advance()
			continue
		}
		var result struct{ F0 Token, F1 bool } = lx.ScanWord()
		tok := result.F0
		ok := result.F1
		if !ok {
			panic("unexpected character")
		}
		tokens = append(tokens, tok)
	}
	return tokens
}

func CountWords(tokens []Token) int {
	count := 0
	for _, tok := range tokens {
		if tok.Kind == "word" {
			count++
		}
	}
	return count
}

func FormatToken(tok Token) string {
	return tok.Kind + ":" + tok.Text
}

func FindToken(tokens []Token, kind string) *Token {
	for _, tok := range tokens {
		if tok.Kind == kind {
			return tok
		}
	}
	return nil
}

func ExampleNilCheck(tokens []Token) string {
	tok := FindToken(tokens, "word")
	if tok == nil {
		return ""
	}
	return tok.Text
}

func SumPositions(tokens []Token) int {
	sum := 0
	for i := 0; i < len(tokens); i++ {
		sum += tokens[i].Pos
	}
	return sum
}

func FirstWordPos(tokens []Token) int {
	pos := -1
	for _, tok := range tokens {
		if tok.Kind == "word" {
			pos = tok.Pos
			break
		}
	}
	return pos
}

func MaxInt(a int, b int) int {
	if a > b {
		return a
	}
	return b
}

func DefaultKinds() map[string]int {
	return map[string]int{"word": 1, "num": 2, "op": 3}
}

func ScopedWork(x int) int {
	result := 0
	{
		temp := x * 2
		result = temp + 1
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
	tokens := []Token{}
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
	if len(tokens) > 0 {
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
	if idx >= len(tokens) {
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
