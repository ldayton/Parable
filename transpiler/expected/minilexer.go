package minilexer

import (
	"fmt"
	"reflect"
	"strconv"
	"strings"
	"unicode"
	"unicode/utf8"
)

var _ = strings.Compare // ensure import is used

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

// _intPtr converts a sentinel int (-1 = nil) to *int
func _intPtr(val int) *int {
	if val == -1 {
		return nil
	}
	return &val
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

// _mapGet returns the value for key from map m, or defaultVal if not found
func _mapGet[K comparable, V any](m map[K]V, key K, defaultVal V) V {
	if v, ok := m[key]; ok {
		return v
	}
	return defaultVal
}

// _intToStr converts an integer to its string representation
func _intToStr(n int) string {
	return strconv.Itoa(n)
}

// _isNilInterface checks if an interface value is nil.
// In Go, an interface is nil only when both type and value are nil.
// This handles the case where interface contains a typed nil pointer.
func _isNilInterface(i interface{}) bool {
	if i == nil {
		return true
	}
	v := reflect.ValueOf(i)
	return v.Kind() == reflect.Ptr && v.IsNil()
}

// _runeAt returns the character (as string) at rune index i in string s.
// Python s[i] on a string returns the i-th character, not byte.
func _runeAt(s string, i int) string {
	runes := []rune(s)
	if i < 0 || i >= len(runes) {
		return ""
	}
	return string(runes[i])
}

// _runeLen returns the number of runes (characters) in string s.
// Python len(s) on a string returns character count, not byte count.
func _runeLen(s string) int {
	return utf8.RuneCountInString(s)
}

// _Substring returns s[start:end] using rune (character) indices.
// Python s[start:end] uses character indices, not byte indices.
func _Substring(s string, start int, end int) string {
	runes := []rune(s)
	if start < 0 {
		start = 0
	}
	if end > len(runes) {
		end = len(runes)
	}
	if start >= end {
		return ""
	}
	return string(runes[start:end])
}

const (
	EOF = -1
)

type Scanner interface {
	peek() int
	advance()
}

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
	if lx.Pos >= _runeLen(lx.Source) {
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
		return Token{}, false
	}
	text := _Substring(lx.Source, start, lx.Pos)
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
			panic(NewParseError("unexpected character", lx.Pos, 0))
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

