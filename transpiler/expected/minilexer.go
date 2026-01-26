package minilexer

import (
	"fmt"
	"strconv"
	"strings"
	"unicode"
)

var _ = strings.Compare // ensure import is used

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

// Range generates a slice of integers similar to Python's range()
// Range(end) -> [0, 1, ..., end-1]
// Range(start, end) -> [start, start+1, ..., end-1]
// Range(start, end, step) -> [start, start+step, ..., last < end]
func Range(args ...int) []int {
	var start, end, step int
	switch len(args) {
	case 1:
		start, end, step = 0, args[0], 1
	case 2:
		start, end, step = args[0], args[1], 1
	case 3:
		start, end, step = args[0], args[1], args[2]
	default:
		return nil
	}
	if step == 0 {
		return nil
	}
	var result []int
	if step > 0 {
		for i := start; i < end; i += step {
			result = append(result, i)
		}
	} else {
		for i := start; i > end; i += step {
			result = append(result, i)
		}
	}
	return result
}

func _parseInt(s string, base int) int {
	n, _ := strconv.ParseInt(s, base, 64)
	return int(n)
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
	return int(lx.Source[lx.Pos])
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
		return Token{}, false
	}
	text := lx.Source[start:lx.Pos]
	return Token{Kind: "word", Text: text, Pos: start}, true
}

func IsSpace(ch int) bool {
	return ch == 32 || ch == 10
}

func Tokenize(source string) []Token {
	lx := Lexer{Source: source, Pos: 0, Current: nil}
	tokens := []Token{}
	for lx.Peek() != EOF {
		ch := lx.Peek()
		if IsSpace(ch) {
			lx.Advance()
			continue
		}
		var result struct{ F0 Token; F1 bool } = func() struct{ F0 Token; F1 bool } { _t0, _t1 := lx.ScanWord(); return struct{ F0 Token; F1 bool }{_t0, _t1} }()
		tok := result.F0
		ok := result.F1
		if !ok {
			panic(fmt.Sprintf("%s at position %d", "unexpected character", lx.Pos))
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
			return &tok
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
		tokens[0] = Token{Kind: kind, Text: "", Pos: 0}
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
	return &tokens[idx]
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

