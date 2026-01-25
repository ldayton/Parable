// Package parable is a recursive descent parser for bash.
//
// MIT License - https://github.com/ldayton/Parable
//
//	import "parable"
//	ast, err := parable.Parse("ps aux | grep python")
package parable

import (
	"fmt"
	"reflect"
	"strconv"
	"strings"
	"unicode"
	"unicode/utf8"
)

var (
	_ = fmt.Sprintf
	_ = strings.Contains
	_ = strconv.Atoi
	_ = unicode.IsLetter
	_ = utf8.RuneCountInString
)

// ParseError is raised when parsing fails.
type ParseError struct {
	Message string
	Pos     int
	Line    int
}

func (e *ParseError) Error() string {
	if e.Line != 0 && e.Pos != 0 {
		return fmt.Sprintf("Parse error at line %d, position %d: %s", e.Line, e.Pos, e.Message)
	}
	if e.Pos != 0 {
		return fmt.Sprintf("Parse error at position %d: %s", e.Pos, e.Message)
	}
	return fmt.Sprintf("Parse error: %s", e.Message)
}

func NewParseError(message string, pos int, line int) *ParseError {
	return &ParseError{Message: message, Pos: pos, Line: line}
}

// MatchedPairError is raised when a matched pair is unclosed at EOF.
type MatchedPairError struct {
	ParseError
}

func NewMatchedPairError(message string, pos int, line int) *MatchedPairError {
	return &MatchedPairError{ParseError{Message: message, Pos: pos, Line: line}}
}

// Node is the base interface for all AST nodes.
type Node interface {
	Kind() string
	ToSexp() string
}

// ANSICEscapes maps ANSI-C escape characters to byte values
var ANSICEscapes = map[rune]int{
	'a': 0x07, 'b': 0x08, 'e': 0x1B, 'E': 0x1B,
	'f': 0x0C, 'n': 0x0A, 'r': 0x0D, 't': 0x09,
	'v': 0x0B, '\\': 0x5C, '"': 0x22, '?': 0x3F,
}

func _mapGet[K comparable, V any](m map[K]V, key K, def V) V {
	if v, ok := m[key]; ok {
		return v
	}
	return def
}

func _ternary[T any](cond bool, a, b T) T {
	if cond {
		return a
	}
	return b
}

func _isNilNode(n Node) bool {
	if n == nil {
		return true
	}
	v := reflect.ValueOf(n)
	return v.Kind() == reflect.Ptr && v.IsNil()
}

func _runeAt(s string, i int) string {
	runes := []rune(s)
	if i < 0 || i >= len(runes) {
		return ""
	}
	return string(runes[i])
}

func _runeLen(s string) int {
	return utf8.RuneCountInString(s)
}

func _strToRune(s string) rune {
	for _, r := range s {
		return r
	}
	return 0
}

func _runeFromChar(c interface{}) rune {
	switch v := c.(type) {
	case rune:
		return v
	case byte:
		return rune(v)
	case string:
		for _, r := range v {
			return r
		}
	}
	return 0
}

func _contains[T comparable](slice []T, val T) bool {
	for _, v := range slice {
		if v == val {
			return true
		}
	}
	return false
}

func _containsAny(slice []interface{}, val interface{}) bool {
	for _, v := range slice {
		if v == val {
			return true
		}
	}
	return false
}

func _parseInt(s string, base int) int {
	v, err := strconv.ParseInt(s, base, 64)
	if err != nil {
		return 0
	}
	return int(v)
}

func _max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func _min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func _mustAtoi(s string) int {
	v, err := strconv.Atoi(s)
	if err != nil {
		return 0
	}
	return v
}

func _strIsDigits(s string) bool {
	if len(s) == 0 {
		return false
	}
	for _, r := range s {
		if !unicode.IsDigit(r) {
			return false
		}
	}
	return true
}

func _getattr(obj interface{}, attr string, def interface{}) interface{} {
	if obj == nil {
		return def
	}
	v := reflect.ValueOf(obj)
	if v.Kind() == reflect.Ptr {
		v = v.Elem()
	}
	if v.Kind() != reflect.Struct {
		return def
	}
	// Convert snake_case to PascalCase
	fieldName := _snakeToPascal(attr)
	f := v.FieldByName(fieldName)
	if !f.IsValid() {
		// Try lowercase 'kind' field
		if attr == "kind" {
			f = v.FieldByName("kind")
			if f.IsValid() {
				return f.Interface()
			}
		}
		return def
	}
	return f.Interface()
}

func _FormatArithVal(s string) string {
	w := NewWord(s, []Node{})
	val := w._ExpandAllAnsiCQuotes(s)
	val = w._StripLocaleStringDollars(val)
	val = w._FormatCommandSubstitutions(val, false)
	val = strings.ReplaceAll(strings.ReplaceAll(val, "\\", "\\\\"), "\"", "\\\"")
	val = strings.ReplaceAll(strings.ReplaceAll(val, "\n", "\\n"), "\t", "\\t")
	return val
}

func _snakeToPascal(s string) string {
	parts := strings.Split(s, "_")
	for i, p := range parts {
		if len(p) > 0 {
			parts[i] = strings.ToUpper(p[:1]) + p[1:]
		}
	}
	return strings.Join(parts, "")
}

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

func _pop[T any](s *[]T) T {
	last := (*s)[len(*s)-1]
	*s = (*s)[:len(*s)-1]
	return last
}

// Module-level constants
const (
	SmpLiteral    = 1
	SmpPastOpen   = 2
	WordCtxNormal = 0
	WordCtxCond   = 1
	WordCtxRegex  = 2
)

var ReservedWords = map[string]bool{
	"case":     true,
	"coproc":   true,
	"do":       true,
	"done":     true,
	"elif":     true,
	"else":     true,
	"esac":     true,
	"fi":       true,
	"for":      true,
	"function": true,
	"if":       true,
	"in":       true,
	"select":   true,
	"then":     true,
	"until":    true,
	"while":    true,
}

var CondUnaryOps = map[string]bool{
	"-G": true,
	"-L": true,
	"-N": true,
	"-O": true,
	"-R": true,
	"-S": true,
	"-a": true,
	"-b": true,
	"-c": true,
	"-d": true,
	"-e": true,
	"-f": true,
	"-g": true,
	"-h": true,
	"-k": true,
	"-n": true,
	"-o": true,
	"-p": true,
	"-r": true,
	"-s": true,
	"-t": true,
	"-u": true,
	"-v": true,
	"-w": true,
	"-x": true,
	"-z": true,
}

var CondBinaryOps = map[string]bool{
	"!=":  true,
	"-ef": true,
	"-eq": true,
	"-ge": true,
	"-gt": true,
	"-le": true,
	"-lt": true,
	"-ne": true,
	"-nt": true,
	"-ot": true,
	"<":   true,
	"=":   true,
	"==":  true,
	"=~":  true,
	">":   true,
}

var CompoundKeywords = map[string]bool{
	"case":   true,
	"for":    true,
	"if":     true,
	"select": true,
	"until":  true,
	"while":  true,
}

var AssignmentBuiltins = map[string]bool{
	"alias":    true,
	"declare":  true,
	"eval":     true,
	"export":   true,
	"let":      true,
	"local":    true,
	"readonly": true,
	"typeset":  true,
}

// quoteStackEntry holds pushed quote state (single, double)
type quoteStackEntry struct {
	single bool
	double bool
}

// TokenType constants
const (
	TokenType_EOF                 = 0
	TokenType_WORD                = 1
	TokenType_NEWLINE             = 2
	TokenType_SEMI                = 10
	TokenType_PIPE                = 0x0B
	TokenType_AMP                 = 0x0C
	TokenType_LPAREN              = 0x0D
	TokenType_RPAREN              = 0x0E
	TokenType_LBRACE              = 0x0F
	TokenType_RBRACE              = 0x10
	TokenType_LESS                = 0x11
	TokenType_GREATER             = 0x12
	TokenType_AND_AND             = 0x1E
	TokenType_OR_OR               = 0x1F
	TokenType_SEMI_SEMI           = 0x20
	TokenType_SEMI_AMP            = 0x21
	TokenType_SEMI_SEMI_AMP       = 0x22
	TokenType_LESS_LESS           = 0x23
	TokenType_GREATER_GREATER     = 0x24
	TokenType_LESS_AMP            = 0x25
	TokenType_GREATER_AMP         = 0x26
	TokenType_LESS_GREATER        = 0x27
	TokenType_GREATER_PIPE        = 0x28
	TokenType_LESS_LESS_MINUS     = 0x29
	TokenType_LESS_LESS_LESS      = 0x2A
	TokenType_AMP_GREATER         = 0x2B
	TokenType_AMP_GREATER_GREATER = 0x2C
	TokenType_PIPE_AMP            = 0x2D
	TokenType_IF                  = 0x32
	TokenType_THEN                = 0x33
	TokenType_ELSE                = 0x34
	TokenType_ELIF                = 0x35
	TokenType_FI                  = 0x36
	TokenType_CASE                = 0x37
	TokenType_ESAC                = 0x38
	TokenType_FOR                 = 0x39
	TokenType_WHILE               = 0x3A
	TokenType_UNTIL               = 0x3B
	TokenType_DO                  = 0x3C
	TokenType_DONE                = 0x3D
	TokenType_IN                  = 0x3E
	TokenType_FUNCTION            = 0x3F
	TokenType_SELECT              = 0x40
	TokenType_COPROC              = 0x41
	TokenType_TIME                = 0x42
	TokenType_BANG                = 0x43
	TokenType_LBRACKET_LBRACKET   = 0x44
	TokenType_RBRACKET_RBRACKET   = 0x45
	TokenType_ASSIGNMENT_WORD     = 0x50
	TokenType_NUMBER              = 0x51
)

type Token struct {
	Type  int
	Value string
	Pos   int
	Parts []Node
	Word  Node
}

// ParserStateFlags constants
const (
	ParserStateFlags_NONE           = 0
	ParserStateFlags_PST_CASEPAT    = 1
	ParserStateFlags_PST_CMDSUBST   = 2
	ParserStateFlags_PST_CASESTMT   = 4
	ParserStateFlags_PST_CONDEXPR   = 8
	ParserStateFlags_PST_COMPASSIGN = 0x10
	ParserStateFlags_PST_ARITH      = 0x20
	ParserStateFlags_PST_HEREDOC    = 0x40
	ParserStateFlags_PST_REGEXP     = 0x80
	ParserStateFlags_PST_EXTPAT     = 0x100
	ParserStateFlags_PST_SUBSHELL   = 0x200
	ParserStateFlags_PST_REDIRLIST  = 0x400
	ParserStateFlags_PST_COMMENT    = 0x800
	ParserStateFlags_PST_EOFTOKEN   = 0x1000
)

// DolbraceState constants
const (
	DolbraceState_NONE   = 0
	DolbraceState_PARAM  = 1
	DolbraceState_OP     = 2
	DolbraceState_WORD   = 4
	DolbraceState_QUOTE  = 0x40
	DolbraceState_QUOTE2 = 0x80
)

// MatchedPairFlags constants
const (
	MatchedPairFlags_NONE       = 0
	MatchedPairFlags_DQUOTE     = 1
	MatchedPairFlags_DOLBRACE   = 2
	MatchedPairFlags_COMMAND    = 4
	MatchedPairFlags_ARITH      = 8
	MatchedPairFlags_ALLOWESC   = 0x10
	MatchedPairFlags_EXTGLOB    = 0x20
	MatchedPairFlags_FIRSTCLOSE = 0x40
	MatchedPairFlags_ARRAYSUB   = 0x80
	MatchedPairFlags_BACKQUOTE  = 0x100
)

type SavedParserState struct {
	Parser_state     int
	Dolbrace_state   int
	Pending_heredocs []Node
	Ctx_stack        []*ParseContext
	Eof_token        string
	Token_history    []*Token
}

type QuoteState struct {
	Single bool
	Double bool
	_Stack []quoteStackEntry
}

// ParseContext constants
const (
	ParseContext_NORMAL          = 0
	ParseContext_COMMAND_SUB     = 1
	ParseContext_ARITHMETIC      = 2
	ParseContext_CASE_PATTERN    = 3
	ParseContext_BRACE_EXPANSION = 4
)

type ParseContext struct {
	Kind              int
	Paren_depth       int
	Brace_depth       int
	Bracket_depth     int
	Case_depth        int
	Arith_depth       int
	Arith_paren_depth int
	Quote             *QuoteState
}

type ContextStack struct {
	_Stack []*ParseContext
}

type Lexer struct {
	RESERVED_WORDS            map[string]int
	Source                    string
	Pos                       int
	Length                    int
	Quote                     *QuoteState
	_Token_cache              *Token
	_Parser_state             int
	_Dolbrace_state           int
	_Pending_heredocs         []Node
	_Extglob                  bool
	_Parser                   *Parser
	_Eof_token                string
	_Last_read_token          *Token
	_Word_context             int
	_At_command_start         bool
	_In_array_literal         bool
	_In_assign_builtin        bool
	_Post_read_pos            int
	_Cached_word_context      int
	_Cached_at_command_start  bool
	_Cached_in_array_literal  bool
	_Cached_in_assign_builtin bool
	Source_runes              []rune
}

type Word struct {
	Value string
	Parts []Node
	kind  string
}

func (w *Word) Kind() string {
	return w.kind
}

type Command struct {
	Words     []Node
	Redirects []Node
	kind      string
}

func (c *Command) Kind() string {
	return c.kind
}

type Pipeline struct {
	Commands []Node
	kind     string
}

func (p *Pipeline) Kind() string {
	return p.kind
}

type List struct {
	Parts []Node
	kind  string
}

func (l *List) Kind() string {
	return l.kind
}

type Operator struct {
	Op   string
	kind string
}

func (o *Operator) Kind() string {
	return o.kind
}

type PipeBoth struct {
	kind string
}

func (p *PipeBoth) Kind() string {
	return p.kind
}

type Empty struct {
	kind string
}

func (e *Empty) Kind() string {
	return e.kind
}

type Comment struct {
	Text string
	kind string
}

func (c *Comment) Kind() string {
	return c.kind
}

type Redirect struct {
	Op     string
	Target Node
	Fd     int
	kind   string
}

func (r *Redirect) Kind() string {
	return r.kind
}

type HereDoc struct {
	Delimiter  string
	Content    string
	Strip_tabs bool
	Quoted     bool
	Fd         int
	Complete   bool
	_Start_pos int
	kind       string
}

func (h *HereDoc) Kind() string {
	return h.kind
}

type Subshell struct {
	Body      Node
	Redirects []Node
	kind      string
}

func (s *Subshell) Kind() string {
	return s.kind
}

type BraceGroup struct {
	Body      Node
	Redirects []Node
	kind      string
}

func (b *BraceGroup) Kind() string {
	return b.kind
}

type If struct {
	Condition Node
	Then_body Node
	Else_body Node
	Redirects []Node
	kind      string
}

func (i *If) Kind() string {
	return i.kind
}

type While struct {
	Condition Node
	Body      Node
	Redirects []Node
	kind      string
}

func (w *While) Kind() string {
	return w.kind
}

type Until struct {
	Condition Node
	Body      Node
	Redirects []Node
	kind      string
}

func (u *Until) Kind() string {
	return u.kind
}

type For struct {
	Var       string
	Words     []Node
	Body      Node
	Redirects []Node
	kind      string
}

func (f *For) Kind() string {
	return f.kind
}

type ForArith struct {
	Init      string
	Cond      string
	Incr      string
	Body      Node
	Redirects []Node
	kind      string
}

func (f *ForArith) Kind() string {
	return f.kind
}

type Select struct {
	Var       string
	Words     []Node
	Body      Node
	Redirects []Node
	kind      string
}

func (s *Select) Kind() string {
	return s.kind
}

type Case struct {
	Word      Node
	Patterns  []Node
	Redirects []Node
	kind      string
}

func (c *Case) Kind() string {
	return c.kind
}

type CasePattern struct {
	Pattern    string
	Body       Node
	Terminator string
	kind       string
}

func (c *CasePattern) Kind() string {
	return c.kind
}

type Function struct {
	Name string
	Body Node
	kind string
}

func (f *Function) Kind() string {
	return f.kind
}

type ParamExpansion struct {
	Param string
	Op    string
	Arg   string
	kind  string
}

func (p *ParamExpansion) Kind() string {
	return p.kind
}

type ParamLength struct {
	Param string
	kind  string
}

func (p *ParamLength) Kind() string {
	return p.kind
}

type ParamIndirect struct {
	Param string
	Op    string
	Arg   string
	kind  string
}

func (p *ParamIndirect) Kind() string {
	return p.kind
}

type CommandSubstitution struct {
	Command Node
	Brace   bool
	kind    string
}

func (c *CommandSubstitution) Kind() string {
	return c.kind
}

type ArithmeticExpansion struct {
	Expression Node
	kind       string
}

func (a *ArithmeticExpansion) Kind() string {
	return a.kind
}

type ArithmeticCommand struct {
	Expression  Node
	Redirects   []Node
	Raw_content string
	kind        string
}

func (a *ArithmeticCommand) Kind() string {
	return a.kind
}

type ArithNumber struct {
	Value string
	kind  string
}

func (a *ArithNumber) Kind() string {
	return a.kind
}

type ArithEmpty struct {
	kind string
}

func (a *ArithEmpty) Kind() string {
	return a.kind
}

type ArithVar struct {
	Name string
	kind string
}

func (a *ArithVar) Kind() string {
	return a.kind
}

type ArithBinaryOp struct {
	Op    string
	Left  Node
	Right Node
	kind  string
}

func (a *ArithBinaryOp) Kind() string {
	return a.kind
}

type ArithUnaryOp struct {
	Op      string
	Operand Node
	kind    string
}

func (a *ArithUnaryOp) Kind() string {
	return a.kind
}

type ArithPreIncr struct {
	Operand Node
	kind    string
}

func (a *ArithPreIncr) Kind() string {
	return a.kind
}

type ArithPostIncr struct {
	Operand Node
	kind    string
}

func (a *ArithPostIncr) Kind() string {
	return a.kind
}

type ArithPreDecr struct {
	Operand Node
	kind    string
}

func (a *ArithPreDecr) Kind() string {
	return a.kind
}

type ArithPostDecr struct {
	Operand Node
	kind    string
}

func (a *ArithPostDecr) Kind() string {
	return a.kind
}

type ArithAssign struct {
	Op     string
	Target Node
	Value  Node
	kind   string
}

func (a *ArithAssign) Kind() string {
	return a.kind
}

type ArithTernary struct {
	Condition Node
	If_true   Node
	If_false  Node
	kind      string
}

func (a *ArithTernary) Kind() string {
	return a.kind
}

type ArithComma struct {
	Left  Node
	Right Node
	kind  string
}

func (a *ArithComma) Kind() string {
	return a.kind
}

type ArithSubscript struct {
	Array string
	Index Node
	kind  string
}

func (a *ArithSubscript) Kind() string {
	return a.kind
}

type ArithEscape struct {
	Char string
	kind string
}

func (a *ArithEscape) Kind() string {
	return a.kind
}

type ArithDeprecated struct {
	Expression string
	kind       string
}

func (a *ArithDeprecated) Kind() string {
	return a.kind
}

type ArithConcat struct {
	Parts []Node
	kind  string
}

func (a *ArithConcat) Kind() string {
	return a.kind
}

type AnsiCQuote struct {
	Content string
	kind    string
}

func (a *AnsiCQuote) Kind() string {
	return a.kind
}

type LocaleString struct {
	Content string
	kind    string
}

func (l *LocaleString) Kind() string {
	return l.kind
}

type ProcessSubstitution struct {
	Direction string
	Command   Node
	kind      string
}

func (p *ProcessSubstitution) Kind() string {
	return p.kind
}

type Negation struct {
	Pipeline Node
	kind     string
}

func (n *Negation) Kind() string {
	return n.kind
}

type Time struct {
	Pipeline Node
	Posix    bool
	kind     string
}

func (t *Time) Kind() string {
	return t.kind
}

type ConditionalExpr struct {
	Body      interface{}
	Redirects []Node
	kind      string
}

func (c *ConditionalExpr) Kind() string {
	return c.kind
}

type UnaryTest struct {
	Op      string
	Operand Node
	kind    string
}

func (u *UnaryTest) Kind() string {
	return u.kind
}

type BinaryTest struct {
	Op    string
	Left  Node
	Right Node
	kind  string
}

func (b *BinaryTest) Kind() string {
	return b.kind
}

type CondAnd struct {
	Left  Node
	Right Node
	kind  string
}

func (c *CondAnd) Kind() string {
	return c.kind
}

type CondOr struct {
	Left  Node
	Right Node
	kind  string
}

func (c *CondOr) Kind() string {
	return c.kind
}

type CondNot struct {
	Operand Node
	kind    string
}

func (c *CondNot) Kind() string {
	return c.kind
}

type CondParen struct {
	Inner Node
	kind  string
}

func (c *CondParen) Kind() string {
	return c.kind
}

type Array struct {
	Elements []Node
	kind     string
}

func (a *Array) Kind() string {
	return a.kind
}

type Coproc struct {
	Command Node
	Name    string
	kind    string
}

func (c *Coproc) Kind() string {
	return c.kind
}

type Parser struct {
	Source                       string
	Pos                          int
	Length                       int
	_Pending_heredocs            []Node
	_Cmdsub_heredoc_end          int
	_Saw_newline_in_single_quote bool
	_In_process_sub              bool
	_Extglob                     bool
	_Ctx                         *ContextStack
	_Lexer                       *Lexer
	_Token_history               []*Token
	_Parser_state                int
	_Dolbrace_state              int
	_Eof_token                   string
	_Word_context                int
	_At_command_start            bool
	_In_array_literal            bool
	_In_assign_builtin           bool
	_Arith_src                   string
	_Arith_pos                   int
	_Arith_len                   int
	Source_runes                 []rune
}

func _IsHexDigit(c string) bool {
	return c >= "0" && c <= "9" || c >= "a" && c <= "f" || c >= "A" && c <= "F"
}

func _IsOctalDigit(c string) bool {
	return c >= "0" && c <= "7"
}

func _GetAnsiEscape(c string) int {
	return _mapGet(ANSICEscapes, _strToRune(c), -1)
}

func _IsWhitespace(c string) bool {
	return c == " " || c == "\t" || c == "\n"
}

func _IsWhitespaceNoNewline(c string) bool {
	return c == " " || c == "\t"
}

func _StartsWithAt(s string, pos int, prefix string) bool {
	return strings.HasPrefix(s, prefix)
}

func _CountConsecutiveDollarsBefore(s string, pos int) int {
	var bsCount int
	var j int
	count := 0
	k := pos - 1
	for k >= 0 && _runeAt(s, k) == "$" {
		bsCount = 0
		j = k - 1
		for j >= 0 && _runeAt(s, j) == "\\" {
			bsCount += 1
			j -= 1
		}
		if bsCount%2 == 1 {
			break
		}
		count += 1
		k -= 1
	}
	return count
}

func _IsExpansionStart(s string, pos int, delimiter string) bool {
	if !(strings.HasPrefix(s[pos:], delimiter)) {
		return false
	}
	return _CountConsecutiveDollarsBefore(s, pos)%2 == 0
}

func _Sublist(lst []Node, start int, end int) []Node {
	return lst[start:end]
}

func _RepeatStr(s string, n int) string {
	result := []string{}
	i := 0
	for i < n {
		result = append(result, s)
		i += 1
	}
	return strings.Join(result, "")
}

func _StripLineContinuationsCommentAware(text string) string {
	var inComment bool
	var c string
	var numPrecedingBackslashes int
	var j int
	result := []string{}
	i := 0
	inComment = false
	quote := NewQuoteState()
	for i < _runeLen(text) {
		c = _runeAt(text, i)
		if c == "\\" && i+1 < _runeLen(text) && _runeAt(text, i+1) == "\n" {
			numPrecedingBackslashes = 0
			j = i - 1
			for j >= 0 && _runeAt(text, j) == "\\" {
				numPrecedingBackslashes += 1
				j -= 1
			}
			if numPrecedingBackslashes%2 == 0 {
				if inComment {
					result = append(result, "\n")
				}
				i += 2
				inComment = false
				continue
			}
		}
		if c == "\n" {
			inComment = false
			result = append(result, c)
			i += 1
			continue
		}
		if c == "'" && !(quote.Double) && !(inComment) {
			quote.Single = !(quote.Single)
		} else if c == "\"" && !(quote.Single) && !(inComment) {
			quote.Double = !(quote.Double)
		} else if c == "#" && !(quote.Single) && !(inComment) {
			inComment = true
		}
		result = append(result, c)
		i += 1
	}
	return strings.Join(result, "")
}

func _AppendRedirects(base string, redirects []Node) string {
	var parts []string
	if len(redirects) > 0 {
		parts = []string{}
		for _, r := range redirects {
			parts = append(parts, r.ToSexp())
		}
		return base + " " + strings.Join(parts, " ")
	}
	return base
}

func _ConsumeSingleQuote(s string, start int) (int, []string) {
	chars := []string{"'"}
	i := start + 1
	for i < _runeLen(s) && _runeAt(s, i) != "'" {
		chars = append(chars, _runeAt(s, i))
		i += 1
	}
	if i < _runeLen(s) {
		chars = append(chars, _runeAt(s, i))
		i += 1
	}
	return i, chars
}

func _ConsumeDoubleQuote(s string, start int) (int, []string) {
	chars := []string{"\""}
	i := start + 1
	for i < _runeLen(s) && _runeAt(s, i) != "\"" {
		if _runeAt(s, i) == "\\" && i+1 < _runeLen(s) {
			chars = append(chars, _runeAt(s, i))
			i += 1
		}
		chars = append(chars, _runeAt(s, i))
		i += 1
	}
	if i < _runeLen(s) {
		chars = append(chars, _runeAt(s, i))
		i += 1
	}
	return i, chars
}

func _HasBracketClose(s string, start int, depth int) bool {
	i := start
	for i < _runeLen(s) {
		if _runeAt(s, i) == "]" {
			return true
		}
		if (_runeAt(s, i) == "|" || _runeAt(s, i) == ")") && depth == 0 {
			return false
		}
		i += 1
	}
	return false
}

func _ConsumeBracketClass(s string, start int, depth int) (int, []string, bool) {
	var isBracket bool
	scanPos := start + 1
	if scanPos < _runeLen(s) && (_runeAt(s, scanPos) == "!" || _runeAt(s, scanPos) == "^") {
		scanPos += 1
	}
	if scanPos < _runeLen(s) && _runeAt(s, scanPos) == "]" {
		if _HasBracketClose(s, scanPos+1, depth) {
			scanPos += 1
		}
	}
	isBracket = false
	for scanPos < _runeLen(s) {
		if _runeAt(s, scanPos) == "]" {
			isBracket = true
			break
		}
		if _runeAt(s, scanPos) == ")" && depth == 0 {
			break
		}
		if _runeAt(s, scanPos) == "|" && depth == 0 {
			break
		}
		scanPos += 1
	}
	if !(isBracket) {
		return start + 1, []string{"["}, false
	}
	chars := []string{"["}
	i := start + 1
	if i < _runeLen(s) && (_runeAt(s, i) == "!" || _runeAt(s, i) == "^") {
		chars = append(chars, _runeAt(s, i))
		i += 1
	}
	if i < _runeLen(s) && _runeAt(s, i) == "]" {
		if _HasBracketClose(s, i+1, depth) {
			chars = append(chars, _runeAt(s, i))
			i += 1
		}
	}
	for i < _runeLen(s) && _runeAt(s, i) != "]" {
		chars = append(chars, _runeAt(s, i))
		i += 1
	}
	if i < _runeLen(s) {
		chars = append(chars, _runeAt(s, i))
		i += 1
	}
	return i, chars, true
}

func _FormatCondBody(node Node) string {
	kind := node.Kind()
	if kind == "unary-test" {
		ut := node.(*UnaryTest)
		operandVal := ut.Operand.(*Word).GetCondFormattedValue()
		return ut.Op + " " + operandVal
	}
	if kind == "binary-test" {
		bt := node.(*BinaryTest)
		leftVal := bt.Left.(*Word).GetCondFormattedValue()
		rightVal := bt.Right.(*Word).GetCondFormattedValue()
		return leftVal + " " + bt.Op + " " + rightVal
	}
	if kind == "cond-and" {
		ca := node.(*CondAnd)
		return _FormatCondBody(ca.Left) + " && " + _FormatCondBody(ca.Right)
	}
	if kind == "cond-or" {
		co := node.(*CondOr)
		return _FormatCondBody(co.Left) + " || " + _FormatCondBody(co.Right)
	}
	if kind == "cond-not" {
		cn := node.(*CondNot)
		return "! " + _FormatCondBody(cn.Operand)
	}
	if kind == "cond-paren" {
		cp := node.(*CondParen)
		return "( " + _FormatCondBody(cp.Inner) + " )"
	}
	return ""
}

func _StartsWithSubshell(node Node) bool {
	if node.Kind() == "subshell" {
		return true
	}
	if node.Kind() == "list" {
		list := node.(*List)
		for _, p := range list.Parts {
			if p.Kind() != "operator" {
				return _StartsWithSubshell(p)
			}
		}
		return false
	}
	if node.Kind() == "pipeline" {
		pipeline := node.(*Pipeline)
		if len(pipeline.Commands) > 0 {
			return _StartsWithSubshell(pipeline.Commands[0])
		}
		return false
	}
	return false
}

func _FormatCmdsubNode(node Node, indent int, inProcsub bool, compactRedirects bool, procsubFirst bool) string {
	if _isNilNode(node) {
		return ""
	}
	sp := _RepeatStr(" ", indent)
	innerSp := _RepeatStr(" ", indent+4)
	switch node.Kind() {
	case "empty":
		return ""
	case "command":
		cmd := node.(*Command)
		parts := []string{}
		for _, wn := range cmd.Words {
			w := wn.(*Word)
			val := w._ExpandAllAnsiCQuotes(w.Value)
			val = w._StripLocaleStringDollars(val)
			val = w._NormalizeArrayWhitespace(val)
			val = w._FormatCommandSubstitutions(val, false)
			parts = append(parts, val)
		}
		heredocs := []Node{}
		for _, r := range cmd.Redirects {
			if r.Kind() == "heredoc" {
				heredocs = append(heredocs, r)
			}
		}
		for _, r := range cmd.Redirects {
			parts = append(parts, _FormatRedirect(r, compactRedirects, true))
		}
		var result string
		if compactRedirects && len(cmd.Words) > 0 && len(cmd.Redirects) > 0 {
			wordParts := strings.Join(parts[:len(cmd.Words)], " ")
			redirectParts := strings.Join(parts[len(cmd.Words):], "")
			result = wordParts + redirectParts
		} else {
			result = strings.Join(parts, " ")
		}
		for _, h := range heredocs {
			result = result + _FormatHeredocBody(h)
		}
		return result
	case "pipeline":
		pipeline := node.(*Pipeline)
		type cmdPair struct {
			cmd           Node
			needsRedirect bool
		}
		cmds := []cmdPair{}
		i := 0
		for i < len(pipeline.Commands) {
			c := pipeline.Commands[i]
			if c.Kind() == "pipe-both" {
				i++
				continue
			}
			needsRedirect := i+1 < len(pipeline.Commands) && pipeline.Commands[i+1].Kind() == "pipe-both"
			cmds = append(cmds, cmdPair{c, needsRedirect})
			i++
		}
		resultParts := []string{}
		for idx, pair := range cmds {
			formatted := _FormatCmdsubNode(pair.cmd, indent, inProcsub, false, procsubFirst && idx == 0)
			isLast := idx == len(cmds)-1
			hasHeredoc := false
			if pair.cmd.Kind() == "command" {
				c := pair.cmd.(*Command)
				for _, r := range c.Redirects {
					if r.Kind() == "heredoc" {
						hasHeredoc = true
						break
					}
				}
			}
			if pair.needsRedirect {
				if hasHeredoc {
					firstNl := strings.Index(formatted, "\n")
					if firstNl != -1 {
						formatted = _Substring(formatted, 0, firstNl) + " 2>&1" + _Substring(formatted, firstNl, len(formatted))
					} else {
						formatted = formatted + " 2>&1"
					}
				} else {
					formatted = formatted + " 2>&1"
				}
			}
			if !isLast && hasHeredoc {
				firstNl := strings.Index(formatted, "\n")
				if firstNl != -1 {
					formatted = _Substring(formatted, 0, firstNl) + " |" + _Substring(formatted, firstNl, len(formatted))
				}
			}
			resultParts = append(resultParts, formatted)
		}
		compactPipe := inProcsub && len(cmds) > 0 && cmds[0].cmd.Kind() == "subshell"
		result := ""
		for idx, part := range resultParts {
			if idx > 0 {
				if strings.HasSuffix(result, "\n") {
					result = result + "  " + part
				} else if compactPipe {
					result = result + "|" + part
				} else {
					result = result + " | " + part
				}
			} else {
				result = part
			}
		}
		return result
	case "list":
		list := node.(*List)
		hasHeredoc := false
		for _, p := range list.Parts {
			if p.Kind() == "command" {
				c := p.(*Command)
				for _, r := range c.Redirects {
					if r.Kind() == "heredoc" {
						hasHeredoc = true
						break
					}
				}
			} else if p.Kind() == "pipeline" {
				pl := p.(*Pipeline)
				for _, c := range pl.Commands {
					if c.Kind() == "command" {
						cmd := c.(*Command)
						for _, r := range cmd.Redirects {
							if r.Kind() == "heredoc" {
								hasHeredoc = true
								break
							}
						}
					}
					if hasHeredoc {
						break
					}
				}
			}
		}
		resultList := []string{}
		skippedSemi := false
		cmdCount := 0
		for _, p := range list.Parts {
			if p.Kind() == "operator" {
				op := p.(*Operator)
				if op.Op == ";" {
					if len(resultList) > 0 && strings.HasSuffix(resultList[len(resultList)-1], "\n") {
						skippedSemi = true
						continue
					}
					if len(resultList) >= 3 && resultList[len(resultList)-2] == "\n" && strings.HasSuffix(resultList[len(resultList)-3], "\n") {
						skippedSemi = true
						continue
					}
					resultList = append(resultList, ";")
					skippedSemi = false
				} else if op.Op == "\n" {
					if len(resultList) > 0 && resultList[len(resultList)-1] == ";" {
						skippedSemi = false
						continue
					}
					if len(resultList) > 0 && strings.HasSuffix(resultList[len(resultList)-1], "\n") {
						if skippedSemi {
							resultList = append(resultList, " ")
						} else {
							resultList = append(resultList, "\n")
						}
						skippedSemi = false
						continue
					}
					resultList = append(resultList, "\n")
					skippedSemi = false
				} else if op.Op == "&" {
					if len(resultList) > 0 && strings.Contains(resultList[len(resultList)-1], "<<") && strings.Contains(resultList[len(resultList)-1], "\n") {
						last := resultList[len(resultList)-1]
						if strings.Contains(last, " |") || strings.HasPrefix(last, "|") {
							resultList[len(resultList)-1] = last + " &"
						} else {
							firstNl := strings.Index(last, "\n")
							resultList[len(resultList)-1] = _Substring(last, 0, firstNl) + " &" + _Substring(last, firstNl, len(last))
						}
					} else {
						resultList = append(resultList, " &")
					}
				} else {
					if len(resultList) > 0 && strings.Contains(resultList[len(resultList)-1], "<<") && strings.Contains(resultList[len(resultList)-1], "\n") {
						last := resultList[len(resultList)-1]
						firstNl := strings.Index(last, "\n")
						resultList[len(resultList)-1] = _Substring(last, 0, firstNl) + " " + op.Op + " " + _Substring(last, firstNl, len(last))
					} else {
						resultList = append(resultList, " "+op.Op)
					}
				}
			} else {
				if len(resultList) > 0 && !strings.HasSuffix(resultList[len(resultList)-1], " ") && !strings.HasSuffix(resultList[len(resultList)-1], "\n") {
					resultList = append(resultList, " ")
				}
				formattedCmd := _FormatCmdsubNode(p, indent, inProcsub, compactRedirects, procsubFirst && cmdCount == 0)
				if len(resultList) > 0 {
					last := resultList[len(resultList)-1]
					if strings.Contains(last, " || \n") || strings.Contains(last, " && \n") {
						formattedCmd = " " + formattedCmd
					}
				}
				if skippedSemi {
					formattedCmd = " " + formattedCmd
					skippedSemi = false
				}
				resultList = append(resultList, formattedCmd)
				cmdCount++
			}
		}
		s := strings.Join(resultList, "")
		if strings.Contains(s, " &\n") && strings.HasSuffix(s, "\n") {
			return s + " "
		}
		for strings.HasSuffix(s, ";") {
			s = _Substring(s, 0, len(s)-1)
		}
		if !hasHeredoc {
			for strings.HasSuffix(s, "\n") {
				s = _Substring(s, 0, len(s)-1)
			}
		}
		return s
	case "if":
		ifNode := node.(*If)
		cond := _FormatCmdsubNode(ifNode.Condition, indent, false, false, false)
		thenBody := _FormatCmdsubNode(ifNode.Then_body, indent+4, false, false, false)
		result := "if " + cond + "; then\n" + innerSp + thenBody + ";"
		if ifNode.Else_body != nil {
			elseBody := _FormatCmdsubNode(ifNode.Else_body, indent+4, false, false, false)
			result = result + "\n" + sp + "else\n" + innerSp + elseBody + ";"
		}
		result = result + "\n" + sp + "fi"
		return result
	case "while":
		whileNode := node.(*While)
		cond := _FormatCmdsubNode(whileNode.Condition, indent, false, false, false)
		body := _FormatCmdsubNode(whileNode.Body, indent+4, false, false, false)
		result := "while " + cond + "; do\n" + innerSp + body + ";\n" + sp + "done"
		for _, r := range whileNode.Redirects {
			result = result + " " + _FormatRedirect(r, false, false)
		}
		return result
	case "until":
		untilNode := node.(*Until)
		cond := _FormatCmdsubNode(untilNode.Condition, indent, false, false, false)
		body := _FormatCmdsubNode(untilNode.Body, indent+4, false, false, false)
		result := "until " + cond + "; do\n" + innerSp + body + ";\n" + sp + "done"
		for _, r := range untilNode.Redirects {
			result = result + " " + _FormatRedirect(r, false, false)
		}
		return result
	case "for":
		forNode := node.(*For)
		varName := forNode.Var
		body := _FormatCmdsubNode(forNode.Body, indent+4, false, false, false)
		var result string
		if forNode.Words != nil {
			wordVals := []string{}
			for _, wn := range forNode.Words {
				wordVals = append(wordVals, wn.(*Word).Value)
			}
			words := strings.Join(wordVals, " ")
			if words != "" {
				result = "for " + varName + " in " + words + ";\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done"
			} else {
				result = "for " + varName + " in ;\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done"
			}
		} else {
			result = "for " + varName + " in \"$@\";\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done"
		}
		for _, r := range forNode.Redirects {
			result = result + " " + _FormatRedirect(r, false, false)
		}
		return result
	case "for-arith":
		forArith := node.(*ForArith)
		body := _FormatCmdsubNode(forArith.Body, indent+4, false, false, false)
		result := "for ((" + forArith.Init + "; " + forArith.Cond + "; " + forArith.Incr + "))\ndo\n" + innerSp + body + ";\n" + sp + "done"
		for _, r := range forArith.Redirects {
			result = result + " " + _FormatRedirect(r, false, false)
		}
		return result
	case "case":
		caseNode := node.(*Case)
		word := caseNode.Word.(*Word).Value
		patterns := []string{}
		for i, pn := range caseNode.Patterns {
			p := pn.(*CasePattern)
			pat := strings.ReplaceAll(p.Pattern, "|", " | ")
			var body string
			if p.Body != nil {
				body = _FormatCmdsubNode(p.Body, indent+8, false, false, false)
			} else {
				body = ""
			}
			term := p.Terminator
			patIndent := _RepeatStr(" ", indent+8)
			termIndent := _RepeatStr(" ", indent+4)
			var bodyPart string
			if body != "" {
				bodyPart = patIndent + body + "\n"
			} else {
				bodyPart = "\n"
			}
			if i == 0 {
				patterns = append(patterns, " "+pat+")\n"+bodyPart+termIndent+term)
			} else {
				patterns = append(patterns, pat+")\n"+bodyPart+termIndent+term)
			}
		}
		patternStr := strings.Join(patterns, "\n"+_RepeatStr(" ", indent+4))
		redirects := ""
		if len(caseNode.Redirects) > 0 {
			redirectParts := []string{}
			for _, r := range caseNode.Redirects {
				redirectParts = append(redirectParts, _FormatRedirect(r, false, false))
			}
			redirects = " " + strings.Join(redirectParts, " ")
		}
		return "case " + word + " in" + patternStr + "\n" + sp + "esac" + redirects
	case "function":
		funcNode := node.(*Function)
		name := funcNode.Name
		var innerBody Node
		if funcNode.Body.Kind() == "brace-group" {
			bg := funcNode.Body.(*BraceGroup)
			innerBody = bg.Body
		} else {
			innerBody = funcNode.Body
		}
		body := _FormatCmdsubNode(innerBody, indent+4, false, false, false)
		body = strings.TrimSuffix(body, ";")
		return "function " + name + " () \n{ \n" + innerSp + body + "\n}"
	case "subshell":
		subshell := node.(*Subshell)
		body := _FormatCmdsubNode(subshell.Body, indent, inProcsub, compactRedirects, false)
		redirects := ""
		if len(subshell.Redirects) > 0 {
			redirectParts := []string{}
			for _, r := range subshell.Redirects {
				redirectParts = append(redirectParts, _FormatRedirect(r, false, false))
			}
			redirects = strings.Join(redirectParts, " ")
		}
		if procsubFirst {
			if redirects != "" {
				return "(" + body + ") " + redirects
			}
			return "(" + body + ")"
		}
		if redirects != "" {
			return "( " + body + " ) " + redirects
		}
		return "( " + body + " )"
	case "brace-group":
		bg := node.(*BraceGroup)
		body := _FormatCmdsubNode(bg.Body, indent, false, false, false)
		body = strings.TrimSuffix(body, ";")
		var terminator string
		if strings.HasSuffix(body, " &") {
			terminator = " }"
		} else {
			terminator = "; }"
		}
		redirects := ""
		if len(bg.Redirects) > 0 {
			redirectParts := []string{}
			for _, r := range bg.Redirects {
				redirectParts = append(redirectParts, _FormatRedirect(r, false, false))
			}
			redirects = strings.Join(redirectParts, " ")
		}
		if redirects != "" {
			return "{ " + body + terminator + " " + redirects
		}
		return "{ " + body + terminator
	case "arith-cmd":
		arith := node.(*ArithmeticCommand)
		return "((" + arith.Raw_content + "))"
	case "cond-expr":
		condExpr := node.(*ConditionalExpr)
		body := _FormatCondBody(condExpr.Body.(Node))
		return "[[ " + body + " ]]"
	case "negation":
		neg := node.(*Negation)
		if neg.Pipeline != nil {
			return "! " + _FormatCmdsubNode(neg.Pipeline, indent, false, false, false)
		}
		return "! "
	case "time":
		timeNode := node.(*Time)
		var prefix string
		if timeNode.Posix {
			prefix = "time -p "
		} else {
			prefix = "time "
		}
		if timeNode.Pipeline != nil {
			return prefix + _FormatCmdsubNode(timeNode.Pipeline, indent, false, false, false)
		}
		return prefix
	}
	return ""
}

func _FormatRedirect(r Node, compact bool, heredocOpOnly bool) string {
	if r.Kind() == "heredoc" {
		h := r.(*HereDoc)
		var op string
		if h.Strip_tabs {
			op = "<<-"
		} else {
			op = "<<"
		}
		if h.Fd > 0 {
			op = strconv.Itoa(h.Fd) + op
		}
		var delim string
		if h.Quoted {
			delim = "'" + h.Delimiter + "'"
		} else {
			delim = h.Delimiter
		}
		if heredocOpOnly {
			return op + delim
		}
		return op + delim + "\n" + h.Content + h.Delimiter + "\n"
	}
	rd := r.(*Redirect)
	op := rd.Op
	if op == "1>" {
		op = ">"
	} else if op == "0<" {
		op = "<"
	}
	targetWord := rd.Target.(*Word)
	target := targetWord.Value
	target = targetWord._ExpandAllAnsiCQuotes(target)
	target = targetWord._StripLocaleStringDollars(target)
	target = targetWord._FormatCommandSubstitutions(target, false)
	if strings.HasPrefix(target, "&") {
		wasInputClose := false
		if target == "&-" && strings.HasSuffix(op, "<") {
			wasInputClose = true
			op = _Substring(op, 0, len(op)-1) + ">"
		}
		afterAmp := _Substring(target, 1, len(target))
		isLiteralFd := afterAmp == "-" || (len(afterAmp) > 0 && afterAmp[0] >= '0' && afterAmp[0] <= '9')
		if isLiteralFd {
			if op == ">" || op == ">&" {
				if wasInputClose {
					op = "0>"
				} else {
					op = "1>"
				}
			} else if op == "<" || op == "<&" {
				op = "0<"
			}
		} else {
			if op == "1>" {
				op = ">"
			} else if op == "0<" {
				op = "<"
			}
		}
		return op + target
	}
	if strings.HasSuffix(op, "&") {
		return op + target
	}
	if compact {
		return op + target
	}
	return op + " " + target
}

func _FormatHeredocBody(r Node) string {
	h := r.(*HereDoc)
	return "\n" + h.Content + h.Delimiter + "\n"
}

func _LookaheadForEsac(value string, start int, caseDepth int) bool {
	var c string
	i := start
	depth := caseDepth
	quote := NewQuoteState()
	for i < _runeLen(value) {
		c = _runeAt(value, i)
		if c == "\\" && i+1 < _runeLen(value) && quote.Double {
			i += 2
			continue
		}
		if c == "'" && !(quote.Double) {
			quote.Single = !(quote.Single)
			i += 1
			continue
		}
		if c == "\"" && !(quote.Single) {
			quote.Double = !(quote.Double)
			i += 1
			continue
		}
		if quote.Single || quote.Double {
			i += 1
			continue
		}
		if strings.HasPrefix(value[i:], "case") && _IsWordBoundary(value, i, 4) {
			depth += 1
			i += 4
		} else if strings.HasPrefix(value[i:], "esac") && _IsWordBoundary(value, i, 4) {
			depth -= 1
			if depth == 0 {
				return true
			}
			i += 4
		} else if c == "(" {
			i += 1
		} else if c == ")" {
			if depth > 0 {
				i += 1
			} else {
				break
			}
		} else {
			i += 1
		}
	}
	return false
}

func _SkipBacktick(value string, start int) int {
	i := start + 1
	for i < _runeLen(value) && _runeAt(value, i) != "`" {
		if _runeAt(value, i) == "\\" && i+1 < _runeLen(value) {
			i += 2
		} else {
			i += 1
		}
	}
	if i < _runeLen(value) {
		i += 1
	}
	return i
}

func _SkipSingleQuoted(s string, start int) int {
	i := start
	for i < _runeLen(s) && _runeAt(s, i) != "'" {
		i += 1
	}
	return _ternary(i < _runeLen(s), i+1, i)
}

func _SkipDoubleQuoted(s string, start int) int {
	var passNext bool
	var backq bool
	var c string
	var i int
	i, n := start, _runeLen(s)
	passNext = false
	backq = false
	for i < n {
		c = _runeAt(s, i)
		if passNext {
			passNext = false
			i += 1
			continue
		}
		if c == "\\" {
			passNext = true
			i += 1
			continue
		}
		if backq {
			if c == "`" {
				backq = false
			}
			i += 1
			continue
		}
		if c == "`" {
			backq = true
			i += 1
			continue
		}
		if c == "$" && i+1 < n {
			if _runeAt(s, i+1) == "(" {
				i = _FindCmdsubEnd(s, i+2)
				continue
			}
			if _runeAt(s, i+1) == "{" {
				i = _FindBracedParamEnd(s, i+2)
				continue
			}
		}
		if c == "\"" {
			return i + 1
		}
		i += 1
	}
	return i
}

func _IsValidArithmeticStart(value string, start int) bool {
	var scanI int
	var scanC string
	scanParen := 0
	scanI = start + 3
	for scanI < _runeLen(value) {
		scanC = _runeAt(value, scanI)
		if _IsExpansionStart(value, scanI, "$(") {
			scanI = _FindCmdsubEnd(value, scanI+2)
			continue
		}
		if scanC == "(" {
			scanParen += 1
		} else if scanC == ")" {
			if scanParen > 0 {
				scanParen -= 1
			} else if scanI+1 < _runeLen(value) && _runeAt(value, scanI+1) == ")" {
				return true
			} else {
				return false
			}
		}
		scanI += 1
	}
	return false
}

func _FindFunsubEnd(value string, start int) int {
	var c string
	depth := 1
	i := start
	quote := NewQuoteState()
	for i < _runeLen(value) && depth > 0 {
		c = _runeAt(value, i)
		if c == "\\" && i+1 < _runeLen(value) && !(quote.Single) {
			i += 2
			continue
		}
		if c == "'" && !(quote.Double) {
			quote.Single = !(quote.Single)
			i += 1
			continue
		}
		if c == "\"" && !(quote.Single) {
			quote.Double = !(quote.Double)
			i += 1
			continue
		}
		if quote.Single || quote.Double {
			i += 1
			continue
		}
		if c == "{" {
			depth += 1
		} else if c == "}" {
			depth -= 1
			if depth == 0 {
				return i + 1
			}
		}
		i += 1
	}
	return _runeLen(value)
}

func _FindCmdsubEnd(value string, start int) int {
	var i int
	var inCasePatterns bool
	var c string
	var j int
	depth := 1
	i = start
	caseDepth := 0
	inCasePatterns = false
	arithDepth := 0
	arithParenDepth := 0
	for i < _runeLen(value) && depth > 0 {
		c = _runeAt(value, i)
		if c == "\\" && i+1 < _runeLen(value) {
			i += 2
			continue
		}
		if c == "'" {
			i = _SkipSingleQuoted(value, i+1)
			continue
		}
		if c == "\"" {
			i = _SkipDoubleQuoted(value, i+1)
			continue
		}
		if c == "#" && arithDepth == 0 && (i == start || _runeAt(value, i-1) == " " || _runeAt(value, i-1) == "\t" || _runeAt(value, i-1) == "\n" || _runeAt(value, i-1) == ";" || _runeAt(value, i-1) == "|" || _runeAt(value, i-1) == "&" || _runeAt(value, i-1) == "(" || _runeAt(value, i-1) == ")") {
			for i < _runeLen(value) && _runeAt(value, i) != "\n" {
				i += 1
			}
			continue
		}
		if strings.HasPrefix(value[i:], "<<<") {
			i += 3
			for i < _runeLen(value) && (_runeAt(value, i) == " " || _runeAt(value, i) == "\t") {
				i += 1
			}
			if i < _runeLen(value) && _runeAt(value, i) == "\"" {
				i += 1
				for i < _runeLen(value) && _runeAt(value, i) != "\"" {
					if _runeAt(value, i) == "\\" && i+1 < _runeLen(value) {
						i += 2
					} else {
						i += 1
					}
				}
				if i < _runeLen(value) {
					i += 1
				}
			} else if i < _runeLen(value) && _runeAt(value, i) == "'" {
				i += 1
				for i < _runeLen(value) && _runeAt(value, i) != "'" {
					i += 1
				}
				if i < _runeLen(value) {
					i += 1
				}
			} else {
				for i < _runeLen(value) && !strings.Contains(" \t\n;|&<>()", _runeAt(value, i)) {
					i += 1
				}
			}
			continue
		}
		if _IsExpansionStart(value, i, "$((") {
			if _IsValidArithmeticStart(value, i) {
				arithDepth += 1
				i += 3
				continue
			}
			j = _FindCmdsubEnd(value, i+2)
			i = j
			continue
		}
		if arithDepth > 0 && arithParenDepth == 0 && strings.HasPrefix(value[i:], "))") {
			arithDepth -= 1
			i += 2
			continue
		}
		if c == "`" {
			i = _SkipBacktick(value, i)
			continue
		}
		if arithDepth == 0 && strings.HasPrefix(value[i:], "<<") {
			i = _SkipHeredoc(value, i)
			continue
		}
		if strings.HasPrefix(value[i:], "case") && _IsWordBoundary(value, i, 4) {
			caseDepth += 1
			inCasePatterns = false
			i += 4
			continue
		}
		if caseDepth > 0 && strings.HasPrefix(value[i:], "in") && _IsWordBoundary(value, i, 2) {
			inCasePatterns = true
			i += 2
			continue
		}
		if strings.HasPrefix(value[i:], "esac") && _IsWordBoundary(value, i, 4) {
			if caseDepth > 0 {
				caseDepth -= 1
				inCasePatterns = false
			}
			i += 4
			continue
		}
		if strings.HasPrefix(value[i:], ";;") {
			i += 2
			continue
		}
		if c == "(" {
			if !(inCasePatterns && caseDepth > 0) {
				if arithDepth > 0 {
					arithParenDepth += 1
				} else {
					depth += 1
				}
			}
		} else if c == ")" {
			if inCasePatterns && caseDepth > 0 {
				if !(_LookaheadForEsac(value, i+1, caseDepth)) {
					depth -= 1
				}
			} else if arithDepth > 0 {
				if arithParenDepth > 0 {
					arithParenDepth -= 1
				}
			} else {
				depth -= 1
			}
		}
		i += 1
	}
	return i
}

func _FindBracedParamEnd(value string, start int) int {
	var i int
	var inDouble bool
	var dolbraceState int
	var c string
	var end int
	depth := 1
	i = start
	inDouble = false
	dolbraceState = DolbraceState_PARAM
	for i < _runeLen(value) && depth > 0 {
		c = _runeAt(value, i)
		if c == "\\" && i+1 < _runeLen(value) {
			i += 2
			continue
		}
		if c == "'" && dolbraceState == DolbraceState_QUOTE && !(inDouble) {
			i = _SkipSingleQuoted(value, i+1)
			continue
		}
		if c == "\"" {
			inDouble = !(inDouble)
			i += 1
			continue
		}
		if inDouble {
			i += 1
			continue
		}
		if dolbraceState == DolbraceState_PARAM && strings.Contains("%#^,", c) {
			dolbraceState = DolbraceState_QUOTE
		} else if dolbraceState == DolbraceState_PARAM && strings.Contains(":-=?+/", c) {
			dolbraceState = DolbraceState_WORD
		}
		if c == "[" && dolbraceState == DolbraceState_PARAM && !(inDouble) {
			end = _SkipSubscript(value, i, 0)
			if end != -1 {
				i = end
				continue
			}
		}
		if (c == "<" || c == ">") && i+1 < _runeLen(value) && _runeAt(value, i+1) == "(" {
			i = _FindCmdsubEnd(value, i+2)
			continue
		}
		if c == "{" {
			depth += 1
		} else if c == "}" {
			depth -= 1
			if depth == 0 {
				return i + 1
			}
		}
		if _IsExpansionStart(value, i, "$(") {
			i = _FindCmdsubEnd(value, i+2)
			continue
		}
		if _IsExpansionStart(value, i, "${") {
			i = _FindBracedParamEnd(value, i+2)
			continue
		}
		i += 1
	}
	return i
}

func _SkipHeredoc(value string, start int) int {
	var i int
	var delimStart int
	var quoteChar string
	var delimiter string
	var inBacktick bool
	var c string
	var lineStart int
	var lineEnd int
	var line string
	var trailingBs int
	var nextLineStart int
	var stripped string
	var tabsStripped int
	i = start + 2
	if i < _runeLen(value) && _runeAt(value, i) == "-" {
		i += 1
	}
	for i < _runeLen(value) && _IsWhitespaceNoNewline(_runeAt(value, i)) {
		i += 1
	}
	delimStart = i
	quoteChar = ""
	if i < _runeLen(value) && (_runeAt(value, i) == "\"" || _runeAt(value, i) == "'") {
		quoteChar = _runeAt(value, i)
		i += 1
		delimStart = i
		for i < _runeLen(value) && _runeAt(value, i) != quoteChar {
			i += 1
		}
		delimiter = _Substring(value, delimStart, i)
		if i < _runeLen(value) {
			i += 1
		}
	} else if i < _runeLen(value) && _runeAt(value, i) == "\\" {
		i += 1
		delimStart = i
		if i < _runeLen(value) {
			i += 1
		}
		for i < _runeLen(value) && !(_IsMetachar(_runeAt(value, i))) {
			i += 1
		}
		delimiter = _Substring(value, delimStart, i)
	} else {
		for i < _runeLen(value) && !(_IsMetachar(_runeAt(value, i))) {
			i += 1
		}
		delimiter = _Substring(value, delimStart, i)
	}
	parenDepth := 0
	quote := NewQuoteState()
	inBacktick = false
	for i < _runeLen(value) && _runeAt(value, i) != "\n" {
		c = _runeAt(value, i)
		if c == "\\" && i+1 < _runeLen(value) && (quote.Double || inBacktick) {
			i += 2
			continue
		}
		if c == "'" && !(quote.Double) && !(inBacktick) {
			quote.Single = !(quote.Single)
			i += 1
			continue
		}
		if c == "\"" && !(quote.Single) && !(inBacktick) {
			quote.Double = !(quote.Double)
			i += 1
			continue
		}
		if c == "`" && !(quote.Single) {
			inBacktick = !(inBacktick)
			i += 1
			continue
		}
		if quote.Single || quote.Double || inBacktick {
			i += 1
			continue
		}
		if c == "(" {
			parenDepth += 1
		} else if c == ")" {
			if parenDepth == 0 {
				break
			}
			parenDepth -= 1
		}
		i += 1
	}
	if i < _runeLen(value) && _runeAt(value, i) == ")" {
		return i
	}
	if i < _runeLen(value) && _runeAt(value, i) == "\n" {
		i += 1
	}
	for i < _runeLen(value) {
		lineStart = i
		lineEnd = i
		for lineEnd < _runeLen(value) && _runeAt(value, lineEnd) != "\n" {
			lineEnd += 1
		}
		line = _Substring(value, lineStart, lineEnd)
		for lineEnd < _runeLen(value) {
			trailingBs = 0
			for j := _runeLen(line) - 1; j > -1; j += -1 {
				if _runeAt(line, j) == "\\" {
					trailingBs += 1
				} else {
					break
				}
			}
			if trailingBs%2 == 0 {
				break
			}
			line = _Substring(line, 0, _runeLen(line)-1)
			lineEnd += 1
			nextLineStart = lineEnd
			for lineEnd < _runeLen(value) && _runeAt(value, lineEnd) != "\n" {
				lineEnd += 1
			}
			line = line + _Substring(value, nextLineStart, lineEnd)
		}
		if start+2 < _runeLen(value) && _runeAt(value, start+2) == "-" {
			stripped = strings.TrimLeft(line, "\t")
		} else {
			stripped = line
		}
		if stripped == delimiter {
			if lineEnd < _runeLen(value) {
				return lineEnd + 1
			} else {
				return lineEnd
			}
		}
		if strings.HasPrefix(stripped, delimiter) && _runeLen(stripped) > _runeLen(delimiter) {
			tabsStripped = _runeLen(line) - _runeLen(stripped)
			return lineStart + tabsStripped + _runeLen(delimiter)
		}
		if lineEnd < _runeLen(value) {
			i = lineEnd + 1
		} else {
			i = lineEnd
		}
	}
	return i
}

func _FindHeredocContentEnd(source string, start int, delimiters []interface{}) (int, int) {
	if len(delimiters) == 0 {
		return start, start
	}
	pos := start
	for pos < len(source) && string(source[pos]) != "\n" {
		pos++
	}
	if pos >= len(source) {
		return start, start
	}
	contentStart := pos
	pos++
	for _, dt := range delimiters {
		delimTuple := dt.([]interface{})
		delimiter := delimTuple[0].(string)
		stripTabs := delimTuple[1].(bool)
		for pos < len(source) {
			lineStart := pos
			lineEnd := pos
			for lineEnd < len(source) && string(source[lineEnd]) != "\n" {
				lineEnd++
			}
			line := _Substring(source, lineStart, lineEnd)
			for lineEnd < len(source) {
				trailingBs := 0
				for j := len(line) - 1; j >= 0; j-- {
					if string(line[j]) == "\\" {
						trailingBs++
					} else {
						break
					}
				}
				if trailingBs%2 == 0 {
					break
				}
				line = _Substring(line, 0, len(line)-1)
				lineEnd++
				nextLineStart := lineEnd
				for lineEnd < len(source) && string(source[lineEnd]) != "\n" {
					lineEnd++
				}
				line = line + _Substring(source, nextLineStart, lineEnd)
			}
			var lineStripped string
			if stripTabs {
				lineStripped = strings.TrimLeft(line, "\t")
			} else {
				lineStripped = line
			}
			if lineStripped == delimiter {
				if lineEnd < len(source) {
					pos = lineEnd + 1
				} else {
					pos = lineEnd
				}
				break
			}
			if strings.HasPrefix(lineStripped, delimiter) && len(lineStripped) > len(delimiter) {
				tabsStripped := len(line) - len(lineStripped)
				pos = lineStart + tabsStripped + len(delimiter)
				break
			}
			if lineEnd < len(source) {
				pos = lineEnd + 1
			} else {
				pos = lineEnd
			}
		}
	}
	return contentStart, pos
}

func _IsWordBoundary(s string, pos int, wordLen int) bool {
	var prev string
	if pos > 0 {
		prev = _runeAt(s, pos-1)
		if (unicode.IsLetter(_runeFromChar(prev)) || unicode.IsDigit(_runeFromChar(prev))) || prev == "_" {
			return false
		}
		if strings.Contains("{}!", prev) {
			return false
		}
	}
	end := pos + wordLen
	if end < _runeLen(s) && ((unicode.IsLetter(_runeFromChar(_runeAt(s, end))) || unicode.IsDigit(_runeFromChar(_runeAt(s, end)))) || _runeAt(s, end) == "_") {
		return false
	}
	return true
}

func _IsQuote(c string) bool {
	return c == "'" || c == "\""
}

func _CollapseWhitespace(s string) string {
	var prevWasWs bool
	result := []string{}
	prevWasWs = false
	for _, c := range s {
		if c == ' ' || c == '\t' {
			if !(prevWasWs) {
				result = append(result, " ")
			}
			prevWasWs = true
		} else {
			result = append(result, string(c))
			prevWasWs = false
		}
	}
	joined := strings.Join(result, "")
	return strings.TrimSpace(joined)
}

func _CountTrailingBackslashes(s string) int {
	count := 0
	for i := _runeLen(s) - 1; i > -1; i += -1 {
		if _runeAt(s, i) == "\\" {
			count += 1
		} else {
			break
		}
	}
	return count
}

func _NormalizeHeredocDelimiter(delimiter string) string {
	var depth int
	var inner []string
	var innerStr string
	result := []string{}
	i := 0
	for i < _runeLen(delimiter) {
		if i+1 < _runeLen(delimiter) && _Substring(delimiter, i, i+2) == "$(" {
			result = append(result, "$(")
			i += 2
			depth = 1
			inner = []string{}
			for i < _runeLen(delimiter) && depth > 0 {
				if _runeAt(delimiter, i) == "(" {
					depth += 1
					inner = append(inner, _runeAt(delimiter, i))
				} else if _runeAt(delimiter, i) == ")" {
					depth -= 1
					if depth == 0 {
						innerStr = strings.Join(inner, "")
						innerStr = _CollapseWhitespace(innerStr)
						result = append(result, innerStr)
						result = append(result, ")")
					} else {
						inner = append(inner, _runeAt(delimiter, i))
					}
				} else {
					inner = append(inner, _runeAt(delimiter, i))
				}
				i += 1
			}
		} else if i+1 < _runeLen(delimiter) && _Substring(delimiter, i, i+2) == "${" {
			result = append(result, "${")
			i += 2
			depth = 1
			inner = []string{}
			for i < _runeLen(delimiter) && depth > 0 {
				if _runeAt(delimiter, i) == "{" {
					depth += 1
					inner = append(inner, _runeAt(delimiter, i))
				} else if _runeAt(delimiter, i) == "}" {
					depth -= 1
					if depth == 0 {
						innerStr = strings.Join(inner, "")
						innerStr = _CollapseWhitespace(innerStr)
						result = append(result, innerStr)
						result = append(result, "}")
					} else {
						inner = append(inner, _runeAt(delimiter, i))
					}
				} else {
					inner = append(inner, _runeAt(delimiter, i))
				}
				i += 1
			}
		} else if i+1 < _runeLen(delimiter) && strings.Contains("<>", _runeAt(delimiter, i)) && _runeAt(delimiter, i+1) == "(" {
			result = append(result, _runeAt(delimiter, i))
			result = append(result, "(")
			i += 2
			depth = 1
			inner = []string{}
			for i < _runeLen(delimiter) && depth > 0 {
				if _runeAt(delimiter, i) == "(" {
					depth += 1
					inner = append(inner, _runeAt(delimiter, i))
				} else if _runeAt(delimiter, i) == ")" {
					depth -= 1
					if depth == 0 {
						innerStr = strings.Join(inner, "")
						innerStr = _CollapseWhitespace(innerStr)
						result = append(result, innerStr)
						result = append(result, ")")
					} else {
						inner = append(inner, _runeAt(delimiter, i))
					}
				} else {
					inner = append(inner, _runeAt(delimiter, i))
				}
				i += 1
			}
		} else {
			result = append(result, _runeAt(delimiter, i))
			i += 1
		}
	}
	return strings.Join(result, "")
}

func _IsMetachar(c string) bool {
	return c == " " || c == "\t" || c == "\n" || c == "|" || c == "&" || c == ";" || c == "(" || c == ")" || c == "<" || c == ">"
}

func _IsFunsubChar(c string) bool {
	return c == " " || c == "\t" || c == "\n" || c == "|"
}

func _IsExtglobPrefix(c string) bool {
	return c == "@" || c == "?" || c == "*" || c == "+" || c == "!"
}

func _IsRedirectChar(c string) bool {
	return c == "<" || c == ">"
}

func _IsSpecialParam(c string) bool {
	return c == "?" || c == "$" || c == "!" || c == "#" || c == "@" || c == "*" || c == "-" || c == "&"
}

func _IsSpecialParamUnbraced(c string) bool {
	return c == "?" || c == "$" || c == "!" || c == "#" || c == "@" || c == "*" || c == "-"
}

func _IsDigit(c string) bool {
	return c >= "0" && c <= "9"
}

func _IsSemicolonOrNewline(c string) bool {
	return c == ";" || c == "\n"
}

func _IsWordEndContext(c string) bool {
	return c == " " || c == "\t" || c == "\n" || c == ";" || c == "|" || c == "&" || c == "<" || c == ">" || c == "(" || c == ")"
}

func _SkipMatchedPair(s string, start int, open string, close string, flags int) int {
	var i int
	var passNext bool
	var backq bool
	var c string
	var literal int
	n := _runeLen(s)
	if (flags & SmpPastOpen) != 0 {
		i = start
	} else {
		if start >= n || _runeAt(s, start) != open {
			return -1
		}
		i = start + 1
	}
	depth := 1
	passNext = false
	backq = false
	for i < n && depth > 0 {
		c = _runeAt(s, i)
		if passNext {
			passNext = false
			i += 1
			continue
		}
		literal = flags & SmpLiteral
		if !(literal != 0) && c == "\\" {
			passNext = true
			i += 1
			continue
		}
		if backq {
			if c == "`" {
				backq = false
			}
			i += 1
			continue
		}
		if !(literal != 0) && c == "`" {
			backq = true
			i += 1
			continue
		}
		if !(literal != 0) && c == "'" {
			i = _SkipSingleQuoted(s, i+1)
			continue
		}
		if !(literal != 0) && c == "\"" {
			i = _SkipDoubleQuoted(s, i+1)
			continue
		}
		if !(literal != 0) && _IsExpansionStart(s, i, "$(") {
			i = _FindCmdsubEnd(s, i+2)
			continue
		}
		if !(literal != 0) && _IsExpansionStart(s, i, "${") {
			i = _FindBracedParamEnd(s, i+2)
			continue
		}
		if !(literal != 0) && c == open {
			depth += 1
		} else if c == close {
			depth -= 1
		}
		i += 1
	}
	return _ternary(depth == 0, i, -1)
}

func _SkipSubscript(s string, start int, flags int) int {
	return _SkipMatchedPair(s, start, "[", "]", flags)
}

func _Assignment(s string, flags int) int {
	var i int
	var c string
	var subFlags int
	var end int
	if !(len(s) > 0) {
		return -1
	}
	if !(unicode.IsLetter(_runeFromChar(_runeAt(s, 0))) || _runeAt(s, 0) == "_") {
		return -1
	}
	i = 1
	for i < _runeLen(s) {
		c = _runeAt(s, i)
		if c == "=" {
			return i
		}
		if c == "[" {
			subFlags = _ternary((flags&2) != 0, SmpLiteral, 0)
			end = _SkipSubscript(s, i, subFlags)
			if end == -1 {
				return -1
			}
			i = end
			if i < _runeLen(s) && _runeAt(s, i) == "+" {
				i += 1
			}
			if i < _runeLen(s) && _runeAt(s, i) == "=" {
				return i
			}
			return -1
		}
		if c == "+" {
			if i+1 < _runeLen(s) && _runeAt(s, i+1) == "=" {
				return i + 1
			}
			return -1
		}
		if !((unicode.IsLetter(_runeFromChar(c)) || unicode.IsDigit(_runeFromChar(c))) || c == "_") {
			return -1
		}
		i += 1
	}
	return -1
}

func _IsArrayAssignmentPrefix(chars []string) bool {
	var i int
	var end int
	if !(len(chars) > 0) {
		return false
	}
	if !(unicode.IsLetter(_runeFromChar(chars[0])) || chars[0] == "_") {
		return false
	}
	s := strings.Join(chars, "")
	i = 1
	for i < _runeLen(s) && ((unicode.IsLetter(_runeFromChar(_runeAt(s, i))) || unicode.IsDigit(_runeFromChar(_runeAt(s, i)))) || _runeAt(s, i) == "_") {
		i += 1
	}
	for i < _runeLen(s) {
		if _runeAt(s, i) != "[" {
			return false
		}
		end = _SkipSubscript(s, i, SmpLiteral)
		if end == -1 {
			return false
		}
		i = end
	}
	return true
}

func _IsSpecialParamOrDigit(c string) bool {
	return _IsSpecialParam(c) || _IsDigit(c)
}

func _IsParamExpansionOp(c string) bool {
	return c == ":" || c == "-" || c == "=" || c == "+" || c == "?" || c == "#" || c == "%" || c == "/" || c == "^" || c == "," || c == "@" || c == "*" || c == "["
}

func _IsSimpleParamOp(c string) bool {
	return c == "-" || c == "=" || c == "?" || c == "+"
}

func _IsEscapeCharInBacktick(c string) bool {
	return c == "$" || c == "`" || c == "\\"
}

func _IsNegationBoundary(c string) bool {
	return _IsWhitespace(c) || c == ";" || c == "|" || c == ")" || c == "&" || c == ">" || c == "<"
}

func _IsBackslashEscaped(value string, idx int) bool {
	bsCount := 0
	j := idx - 1
	for j >= 0 && _runeAt(value, j) == "\\" {
		bsCount += 1
		j -= 1
	}
	return bsCount%2 == 1
}

func _IsDollarDollarParen(value string, idx int) bool {
	dollarCount := 0
	j := idx - 1
	for j >= 0 && _runeAt(value, j) == "$" {
		dollarCount += 1
		j -= 1
	}
	return dollarCount%2 == 1
}

func _IsParen(c string) bool {
	return c == "(" || c == ")"
}

func _IsCaretOrBang(c string) bool {
	return c == "!" || c == "^"
}

func _IsAtOrStar(c string) bool {
	return c == "@" || c == "*"
}

func _IsDigitOrDash(c string) bool {
	return _IsDigit(c) || c == "-"
}

func _IsNewlineOrRightParen(c string) bool {
	return c == "\n" || c == ")"
}

func _IsSemicolonNewlineBrace(c string) bool {
	return c == ";" || c == "\n" || c == "{"
}

func _LooksLikeAssignment(s string) bool {
	return _Assignment(s, 0) != -1
}

func _IsValidIdentifier(name string) bool {
	if !(len(name) > 0) {
		return false
	}
	if !(unicode.IsLetter(_runeFromChar(_runeAt(name, 0))) || _runeAt(name, 0) == "_") {
		return false
	}
	for _, c := range _Substring(name, 1, _runeLen(name)) {
		if !((unicode.IsLetter(_runeFromChar(c)) || unicode.IsDigit(_runeFromChar(c))) || c == '_') {
			return false
		}
	}
	return true
}

func Parse(source string, extglob bool) []Node {
	parser := NewParser(source, false, extglob)
	return parser.Parse()
}

func NewToken(typ int, value string, pos int, parts []Node, word Node) *Token {
	t := &Token{}
	t.Type = typ
	t.Value = value
	t.Pos = pos
	t.Parts = _ternary(parts != nil, parts, []Node{})
	t.Word = word
	return t
}

func NewSavedParserState(parserState int, dolbraceState int, pendingHeredocs []Node, ctxStack []*ParseContext, eofToken string) *SavedParserState {
	s := &SavedParserState{}
	s.Parser_state = parserState
	s.Dolbrace_state = dolbraceState
	s.Pending_heredocs = pendingHeredocs
	s.Ctx_stack = ctxStack
	s.Eof_token = eofToken
	return s
}

func NewQuoteState() *QuoteState {
	q := &QuoteState{}
	q.Single = false
	q.Double = false
	q._Stack = []quoteStackEntry{}
	return q
}

func (q *QuoteState) Push() {
	q._Stack = append(q._Stack, quoteStackEntry{q.Single, q.Double})
	q.Single = false
	q.Double = false
}

func (q *QuoteState) Pop() {
	if len(q._Stack) > 0 {
		entry := q._Stack[len(q._Stack)-1]
		q._Stack = q._Stack[:len(q._Stack)-1]
		q.Single = entry.single
		q.Double = entry.double
	}
}

func (q *QuoteState) InQuotes() bool {
	return q.Single || q.Double
}

func (q *QuoteState) Copy() *QuoteState {
	qs := &QuoteState{}
	qs.Single = q.Single
	qs.Double = q.Double
	qs._Stack = make([]quoteStackEntry, len(q._Stack))
	copy(qs._Stack, q._Stack)
	return qs
}

func (q *QuoteState) OuterDouble() bool {
	if len(q._Stack) == 0 {
		return false
	}
	return q._Stack[len(q._Stack)-1].double
}

func NewParseContext(kind int) *ParseContext {
	p := &ParseContext{}
	p.Kind = kind
	p.Paren_depth = 0
	p.Brace_depth = 0
	p.Bracket_depth = 0
	p.Case_depth = 0
	p.Arith_depth = 0
	p.Arith_paren_depth = 0
	p.Quote = NewQuoteState()
	return p
}

func (p *ParseContext) Copy() *ParseContext {
	ctx := NewParseContext(p.Kind)
	ctx.Paren_depth = p.Paren_depth
	ctx.Brace_depth = p.Brace_depth
	ctx.Bracket_depth = p.Bracket_depth
	ctx.Case_depth = p.Case_depth
	ctx.Arith_depth = p.Arith_depth
	ctx.Arith_paren_depth = p.Arith_paren_depth
	ctx.Quote = p.Quote.Copy()
	return ctx
}

func NewContextStack() *ContextStack {
	c := &ContextStack{}
	c._Stack = []*ParseContext{NewParseContext(0)}
	return c
}

func (c *ContextStack) GetCurrent() *ParseContext {
	return c._Stack[len(c._Stack)-1]
}

func (c *ContextStack) Push(kind int) {
	c._Stack = append(c._Stack, NewParseContext(kind))
}

func (c *ContextStack) Pop() *ParseContext {
	if len(c._Stack) > 1 {
		return _pop(&c._Stack)
	}
	return c._Stack[0]
}

func (c *ContextStack) CopyStack() []*ParseContext {
	result := []*ParseContext{}
	for _, ctx := range c._Stack {
		result = append(result, ctx.Copy())
	}
	return result
}

func (c *ContextStack) RestoreFrom(savedStack []*ParseContext) {
	result := []*ParseContext{}
	for _, ctx := range savedStack {
		result = append(result, ctx.Copy())
	}
	c._Stack = result
}

func NewLexer(source string, extglob bool) *Lexer {
	l := &Lexer{}
	l.Source = source
	l.Source_runes = []rune(source)
	l.Pos = 0
	l.Length = _runeLen(source)
	l.Quote = NewQuoteState()
	l._Token_cache = nil
	l._Parser_state = ParserStateFlags_NONE
	l._Dolbrace_state = DolbraceState_NONE
	l._Pending_heredocs = []Node{}
	l._Extglob = extglob
	l._Parser = nil
	l._Eof_token = ""
	l._Last_read_token = nil
	l._Word_context = WordCtxNormal
	l._At_command_start = false
	l._In_array_literal = false
	l._In_assign_builtin = false
	l._Post_read_pos = 0
	l._Cached_word_context = WordCtxNormal
	l._Cached_at_command_start = false
	l._Cached_in_array_literal = false
	l._Cached_in_assign_builtin = false
	return l
}

func (l *Lexer) Peek() string {
	if l.Pos >= l.Length {
		return ""
	}
	return string(string(l.Source_runes[l.Pos]))
}

func (l *Lexer) Advance() string {
	if l.Pos >= l.Length {
		return ""
	}
	c := string(l.Source_runes[l.Pos])
	l.Pos += 1
	return string(c)
}

func (l *Lexer) AtEnd() bool {
	return l.Pos >= l.Length
}

func (l *Lexer) Lookahead(n int) string {
	return _Substring(l.Source, l.Pos, l.Pos+n)
}

func (l *Lexer) IsMetachar(c string) bool {
	return strings.Contains("|&;()<> \t\n", c)
}

func (l *Lexer) _ReadOperator() *Token {
	start := l.Pos
	c := l.Peek()
	if c == "" {
		return nil
	}
	two := l.Lookahead(2)
	three := l.Lookahead(3)
	if three == ";;&" {
		l.Pos += 3
		return NewToken(TokenType_SEMI_SEMI_AMP, three, start, nil, nil)
	}
	if three == "<<-" {
		l.Pos += 3
		return NewToken(TokenType_LESS_LESS_MINUS, three, start, nil, nil)
	}
	if three == "<<<" {
		l.Pos += 3
		return NewToken(TokenType_LESS_LESS_LESS, three, start, nil, nil)
	}
	if three == "&>>" {
		l.Pos += 3
		return NewToken(TokenType_AMP_GREATER_GREATER, three, start, nil, nil)
	}
	if two == "&&" {
		l.Pos += 2
		return NewToken(TokenType_AND_AND, two, start, nil, nil)
	}
	if two == "||" {
		l.Pos += 2
		return NewToken(TokenType_OR_OR, two, start, nil, nil)
	}
	if two == ";;" {
		l.Pos += 2
		return NewToken(TokenType_SEMI_SEMI, two, start, nil, nil)
	}
	if two == ";&" {
		l.Pos += 2
		return NewToken(TokenType_SEMI_AMP, two, start, nil, nil)
	}
	if two == "<<" {
		l.Pos += 2
		return NewToken(TokenType_LESS_LESS, two, start, nil, nil)
	}
	if two == ">>" {
		l.Pos += 2
		return NewToken(TokenType_GREATER_GREATER, two, start, nil, nil)
	}
	if two == "<&" {
		l.Pos += 2
		return NewToken(TokenType_LESS_AMP, two, start, nil, nil)
	}
	if two == ">&" {
		l.Pos += 2
		return NewToken(TokenType_GREATER_AMP, two, start, nil, nil)
	}
	if two == "<>" {
		l.Pos += 2
		return NewToken(TokenType_LESS_GREATER, two, start, nil, nil)
	}
	if two == ">|" {
		l.Pos += 2
		return NewToken(TokenType_GREATER_PIPE, two, start, nil, nil)
	}
	if two == "&>" {
		l.Pos += 2
		return NewToken(TokenType_AMP_GREATER, two, start, nil, nil)
	}
	if two == "|&" {
		l.Pos += 2
		return NewToken(TokenType_PIPE_AMP, two, start, nil, nil)
	}
	if c == ";" {
		l.Pos += 1
		return NewToken(TokenType_SEMI, c, start, nil, nil)
	}
	if c == "|" {
		l.Pos += 1
		return NewToken(TokenType_PIPE, c, start, nil, nil)
	}
	if c == "&" {
		l.Pos += 1
		return NewToken(TokenType_AMP, c, start, nil, nil)
	}
	if c == "(" {
		if l._Word_context == WordCtxRegex {
			return nil
		}
		l.Pos += 1
		return NewToken(TokenType_LPAREN, c, start, nil, nil)
	}
	if c == ")" {
		if l._Word_context == WordCtxRegex {
			return nil
		}
		l.Pos += 1
		return NewToken(TokenType_RPAREN, c, start, nil, nil)
	}
	if c == "<" {
		if l.Pos+1 < l.Length && string(l.Source_runes[l.Pos+1]) == "(" {
			return nil
		}
		l.Pos += 1
		return NewToken(TokenType_LESS, c, start, nil, nil)
	}
	if c == ">" {
		if l.Pos+1 < l.Length && string(l.Source_runes[l.Pos+1]) == "(" {
			return nil
		}
		l.Pos += 1
		return NewToken(TokenType_GREATER, c, start, nil, nil)
	}
	if c == "\n" {
		l.Pos += 1
		return NewToken(TokenType_NEWLINE, c, start, nil, nil)
	}
	return nil
}

func (l *Lexer) SkipBlanks() {
	var c string
	for l.Pos < l.Length {
		c = string(l.Source_runes[l.Pos])
		if c != " " && c != "\t" {
			break
		}
		l.Pos += 1
	}
}

func (l *Lexer) _SkipComment() bool {
	var prev string
	if l.Pos >= l.Length {
		return false
	}
	if string(l.Source_runes[l.Pos]) != "#" {
		return false
	}
	if l.Quote.InQuotes() {
		return false
	}
	if l.Pos > 0 {
		prev = string(l.Source_runes[l.Pos-1])
		if !strings.Contains(" \t\n;|&(){}", prev) {
			return false
		}
	}
	for l.Pos < l.Length && string(l.Source_runes[l.Pos]) != "\n" {
		l.Pos += 1
	}
	return true
}

func (l *Lexer) _ReadSingleQuote(start int) (string, bool) {
	var sawNewline bool
	var c string
	chars := []string{"'"}
	sawNewline = false
	for l.Pos < l.Length {
		c = string(l.Source_runes[l.Pos])
		if c == "\n" {
			sawNewline = true
		}
		chars = append(chars, c)
		l.Pos += 1
		if c == "'" {
			return strings.Join(chars, ""), sawNewline
		}
	}
	panic(NewParseError("Unterminated single quote", start, 0))
}

func (l *Lexer) _IsWordTerminator(ctx int, ch string, bracketDepth int, parenDepth int) bool {
	if ctx == WordCtxRegex {
		if ch == "]" && l.Pos+1 < l.Length && string(l.Source_runes[l.Pos+1]) == "]" {
			return true
		}
		if ch == "&" && l.Pos+1 < l.Length && string(l.Source_runes[l.Pos+1]) == "&" {
			return true
		}
		if ch == ")" && parenDepth == 0 {
			return true
		}
		return _IsWhitespace(ch) && parenDepth == 0
	}
	if ctx == WordCtxCond {
		if ch == "]" && l.Pos+1 < l.Length && string(l.Source_runes[l.Pos+1]) == "]" {
			return true
		}
		if ch == ")" {
			return true
		}
		if ch == "&" {
			return true
		}
		if ch == "|" {
			return true
		}
		if ch == ";" {
			return true
		}
		if _IsRedirectChar(ch) && !(l.Pos+1 < l.Length && string(l.Source_runes[l.Pos+1]) == "(") {
			return true
		}
		return _IsWhitespace(ch)
	}
	if (l._Parser_state&ParserStateFlags_PST_EOFTOKEN) != 0 && l._Eof_token != "" && ch == l._Eof_token && bracketDepth == 0 {
		return true
	}
	if _IsRedirectChar(ch) && l.Pos+1 < l.Length && string(l.Source_runes[l.Pos+1]) == "(" {
		return false
	}
	return _IsMetachar(ch) && bracketDepth == 0
}

func (l *Lexer) _ReadBracketExpression(chars *[]string, parts *[]Node, forRegex bool, parenDepth int) bool {
	var scan int
	var bracketWillClose bool
	var sc string
	var nextCh string
	var c string
	if forRegex {
		scan = l.Pos + 1
		if scan < l.Length && string(l.Source_runes[scan]) == "^" {
			scan += 1
		}
		if scan < l.Length && string(l.Source_runes[scan]) == "]" {
			scan += 1
		}
		bracketWillClose = false
		for scan < l.Length {
			sc = string(l.Source_runes[scan])
			if sc == "]" && scan+1 < l.Length && string(l.Source_runes[scan+1]) == "]" {
				break
			}
			if sc == ")" && parenDepth > 0 {
				break
			}
			if sc == "&" && scan+1 < l.Length && string(l.Source_runes[scan+1]) == "&" {
				break
			}
			if sc == "]" {
				bracketWillClose = true
				break
			}
			if sc == "[" && scan+1 < l.Length && string(l.Source_runes[scan+1]) == ":" {
				scan += 2
				for scan < l.Length && !(string(l.Source_runes[scan]) == ":" && scan+1 < l.Length && string(l.Source_runes[scan+1]) == "]") {
					scan += 1
				}
				if scan < l.Length {
					scan += 2
				}
				continue
			}
			scan += 1
		}
		if !(bracketWillClose) {
			return false
		}
	} else {
		if l.Pos+1 >= l.Length {
			return false
		}
		nextCh = string(l.Source_runes[l.Pos+1])
		if _IsWhitespaceNoNewline(nextCh) || nextCh == "&" || nextCh == "|" {
			return false
		}
	}
	*chars = append(*chars, l.Advance())
	if !(l.AtEnd()) && l.Peek() == "^" {
		*chars = append(*chars, l.Advance())
	}
	if !(l.AtEnd()) && l.Peek() == "]" {
		*chars = append(*chars, l.Advance())
	}
	for !(l.AtEnd()) {
		c = l.Peek()
		if c == "]" {
			*chars = append(*chars, l.Advance())
			break
		}
		if c == "[" && l.Pos+1 < l.Length && string(l.Source_runes[l.Pos+1]) == ":" {
			*chars = append(*chars, l.Advance())
			*chars = append(*chars, l.Advance())
			for !(l.AtEnd()) && !(l.Peek() == ":" && l.Pos+1 < l.Length && string(l.Source_runes[l.Pos+1]) == "]") {
				*chars = append(*chars, l.Advance())
			}
			if !(l.AtEnd()) {
				*chars = append(*chars, l.Advance())
				*chars = append(*chars, l.Advance())
			}
		} else if !(forRegex) && c == "[" && l.Pos+1 < l.Length && string(l.Source_runes[l.Pos+1]) == "=" {
			*chars = append(*chars, l.Advance())
			*chars = append(*chars, l.Advance())
			for !(l.AtEnd()) && !(l.Peek() == "=" && l.Pos+1 < l.Length && string(l.Source_runes[l.Pos+1]) == "]") {
				*chars = append(*chars, l.Advance())
			}
			if !(l.AtEnd()) {
				*chars = append(*chars, l.Advance())
				*chars = append(*chars, l.Advance())
			}
		} else if !(forRegex) && c == "[" && l.Pos+1 < l.Length && string(l.Source_runes[l.Pos+1]) == "." {
			*chars = append(*chars, l.Advance())
			*chars = append(*chars, l.Advance())
			for !(l.AtEnd()) && !(l.Peek() == "." && l.Pos+1 < l.Length && string(l.Source_runes[l.Pos+1]) == "]") {
				*chars = append(*chars, l.Advance())
			}
			if !(l.AtEnd()) {
				*chars = append(*chars, l.Advance())
				*chars = append(*chars, l.Advance())
			}
		} else if forRegex && c == "$" {
			l._SyncToParser()
			if !(l._Parser._ParseDollarExpansion(chars, parts, false)) {
				l._SyncFromParser()
				*chars = append(*chars, l.Advance())
			} else {
				l._SyncFromParser()
			}
		} else {
			*chars = append(*chars, l.Advance())
		}
	}
	return true
}

func (l *Lexer) _ParseMatchedPair(openChar string, closeChar string, flags int, initialWasDollar bool) string {
	var passNext bool
	var wasDollar bool
	var wasGtlt bool
	var ch string
	var quoteFlags int
	var nested string
	var nextCh string
	var afterBracePos int
	var inDquote bool
	var direction string
	start := l.Pos
	count := 1
	chars := []string{}
	passNext = false
	wasDollar = initialWasDollar
	wasGtlt = false
	for count > 0 {
		if l.AtEnd() {
			panic(NewMatchedPairError(fmt.Sprintf("unexpected EOF while looking for matching `%v'", closeChar), start, 0))
		}
		ch = l.Advance()
		if (flags&MatchedPairFlags_DOLBRACE) != 0 && l._Dolbrace_state == DolbraceState_OP {
			if !strings.Contains("#%^,~:-=?+/", ch) {
				l._Dolbrace_state = DolbraceState_WORD
			}
		}
		if passNext {
			passNext = false
			chars = append(chars, ch)
			wasDollar = ch == "$"
			wasGtlt = strings.Contains("<>", ch)
			continue
		}
		if openChar == "'" {
			if ch == closeChar {
				count -= 1
				if count == 0 {
					break
				}
			}
			if ch == "\\" && (flags&MatchedPairFlags_ALLOWESC) != 0 {
				passNext = true
			}
			chars = append(chars, ch)
			wasDollar = false
			wasGtlt = false
			continue
		}
		if ch == "\\" {
			if !(l.AtEnd()) && l.Peek() == "\n" {
				l.Advance()
				wasDollar = false
				wasGtlt = false
				continue
			}
			passNext = true
			chars = append(chars, ch)
			wasDollar = false
			wasGtlt = false
			continue
		}
		if ch == closeChar {
			count -= 1
			if count == 0 {
				break
			}
			chars = append(chars, ch)
			wasDollar = false
			wasGtlt = strings.Contains("<>", ch)
			continue
		}
		if ch == openChar && openChar != closeChar {
			if !((flags&MatchedPairFlags_DOLBRACE) != 0 && openChar == "{") {
				count += 1
			}
			chars = append(chars, ch)
			wasDollar = false
			wasGtlt = strings.Contains("<>", ch)
			continue
		}
		if strings.Contains("'\"`", ch) && openChar != closeChar {
			if ch == "'" {
				chars = append(chars, ch)
				quoteFlags = _ternary(wasDollar, flags|MatchedPairFlags_ALLOWESC, flags)
				nested = l._ParseMatchedPair("'", "'", quoteFlags, false)
				chars = append(chars, nested)
				chars = append(chars, "'")
				wasDollar = false
				wasGtlt = false
				continue
			} else if ch == "\"" {
				chars = append(chars, ch)
				nested = l._ParseMatchedPair("\"", "\"", flags|MatchedPairFlags_DQUOTE, false)
				chars = append(chars, nested)
				chars = append(chars, "\"")
				wasDollar = false
				wasGtlt = false
				continue
			} else if ch == "`" {
				chars = append(chars, ch)
				nested = l._ParseMatchedPair("`", "`", flags, false)
				chars = append(chars, nested)
				chars = append(chars, "`")
				wasDollar = false
				wasGtlt = false
				continue
			}
		}
		if ch == "$" && !(l.AtEnd()) && !((flags & MatchedPairFlags_EXTGLOB) != 0) {
			nextCh = l.Peek()
			if wasDollar {
				chars = append(chars, ch)
				wasDollar = false
				wasGtlt = false
				continue
			}
			if nextCh == "{" {
				if (flags & MatchedPairFlags_ARITH) != 0 {
					afterBracePos = l.Pos + 1
					if afterBracePos >= l.Length || !(_IsFunsubChar(string(l.Source_runes[afterBracePos]))) {
						chars = append(chars, ch)
						wasDollar = true
						wasGtlt = false
						continue
					}
				}
				l.Pos -= 1
				l._SyncToParser()
				inDquote = (flags&MatchedPairFlags_DQUOTE != 0)
				paramNode, paramText := l._Parser._ParseParamExpansion(inDquote)
				_ = paramNode
				_ = paramText
				l._SyncFromParser()
				if paramNode != nil {
					chars = append(chars, paramText)
					wasDollar = false
					wasGtlt = false
				} else {
					chars = append(chars, l.Advance())
					wasDollar = true
					wasGtlt = false
				}
				continue
			} else if nextCh == "(" {
				l.Pos -= 1
				l._SyncToParser()
				if l.Pos+2 < l.Length && string(l.Source_runes[l.Pos+2]) == "(" {
					arithNode, arithText := l._Parser._ParseArithmeticExpansion()
					_ = arithNode
					_ = arithText
					l._SyncFromParser()
					if arithNode != nil {
						chars = append(chars, arithText)
						wasDollar = false
						wasGtlt = false
					} else {
						l._SyncToParser()
						cmdNode, cmdText := l._Parser._ParseCommandSubstitution()
						_ = cmdNode
						_ = cmdText
						l._SyncFromParser()
						if cmdNode != nil {
							chars = append(chars, cmdText)
							wasDollar = false
							wasGtlt = false
						} else {
							chars = append(chars, l.Advance())
							chars = append(chars, l.Advance())
							wasDollar = false
							wasGtlt = false
						}
					}
				} else {
					cmdNode, cmdText := l._Parser._ParseCommandSubstitution()
					_ = cmdNode
					_ = cmdText
					l._SyncFromParser()
					if cmdNode != nil {
						chars = append(chars, cmdText)
						wasDollar = false
						wasGtlt = false
					} else {
						chars = append(chars, l.Advance())
						chars = append(chars, l.Advance())
						wasDollar = false
						wasGtlt = false
					}
				}
				continue
			} else if nextCh == "[" {
				l.Pos -= 1
				l._SyncToParser()
				arithNode, arithText := l._Parser._ParseDeprecatedArithmetic()
				_ = arithNode
				_ = arithText
				l._SyncFromParser()
				if arithNode != nil {
					chars = append(chars, arithText)
					wasDollar = false
					wasGtlt = false
				} else {
					chars = append(chars, l.Advance())
					wasDollar = true
					wasGtlt = false
				}
				continue
			}
		}
		if ch == "(" && wasGtlt && (flags&MatchedPairFlags_DOLBRACE|MatchedPairFlags_ARRAYSUB) != 0 {
			direction = _pop(&chars)
			l.Pos -= 1
			l._SyncToParser()
			procsubNode, procsubText := l._Parser._ParseProcessSubstitution()
			_ = procsubNode
			_ = procsubText
			l._SyncFromParser()
			if procsubNode != nil {
				chars = append(chars, procsubText)
				wasDollar = false
				wasGtlt = false
			} else {
				chars = append(chars, direction)
				chars = append(chars, l.Advance())
				wasDollar = false
				wasGtlt = false
			}
			continue
		}
		chars = append(chars, ch)
		wasDollar = ch == "$"
		wasGtlt = strings.Contains("<>", ch)
	}
	return strings.Join(chars, "")
}

func (l *Lexer) _CollectParamArgument(flags int, wasDollar bool) string {
	return l._ParseMatchedPair("{", "}", flags|MatchedPairFlags_DOLBRACE, wasDollar)
}

func (l *Lexer) _ReadWordInternal(ctx int, atCommandStart bool, inArrayLiteral bool, inAssignBuiltin bool) *Word {
	var bracketStartPos int
	var seenEquals bool
	var ch string
	var prevChar string
	var forRegex bool
	var content string
	var trackNewline bool
	var inSingleInDquote bool
	var c string
	var nextC string
	var cmdsubResult0 Node
	var cmdsubResult1 string
	var handleLineContinuation bool
	var nextCh string
	var ansiResult0 Node
	var ansiResult1 string
	var localeResult0 Node
	var localeResult1 string
	var localeResult2 []Node
	var procsubResult0 Node
	var procsubResult1 string
	var isArrayAssign bool
	var arrayResult0 Node
	var arrayResult1 string
	start := l.Pos
	chars := []string{}
	parts := []Node{}
	bracketDepth := 0
	bracketStartPos = -1
	seenEquals = false
	parenDepth := 0
	for !(l.AtEnd()) {
		ch = l.Peek()
		if ctx == WordCtxRegex {
			if ch == "\\" && l.Pos+1 < l.Length && string(l.Source_runes[l.Pos+1]) == "\n" {
				l.Advance()
				l.Advance()
				continue
			}
		}
		if ctx != WordCtxNormal && l._IsWordTerminator(ctx, ch, bracketDepth, parenDepth) {
			break
		}
		if ctx == WordCtxNormal && ch == "[" {
			if bracketDepth > 0 {
				bracketDepth += 1
				chars = append(chars, l.Advance())
				continue
			}
			if len(chars) > 0 && atCommandStart && !(seenEquals) && _IsArrayAssignmentPrefix(chars) {
				prevChar = chars[len(chars)-1]
				if (unicode.IsLetter(_runeFromChar(prevChar)) || unicode.IsDigit(_runeFromChar(prevChar))) || prevChar == "_" {
					bracketStartPos = l.Pos
					bracketDepth += 1
					chars = append(chars, l.Advance())
					continue
				}
			}
			if !(len(chars) > 0) && !(seenEquals) && inArrayLiteral {
				bracketStartPos = l.Pos
				bracketDepth += 1
				chars = append(chars, l.Advance())
				continue
			}
		}
		if ctx == WordCtxNormal && ch == "]" && bracketDepth > 0 {
			bracketDepth -= 1
			chars = append(chars, l.Advance())
			continue
		}
		if ctx == WordCtxNormal && ch == "=" && bracketDepth == 0 {
			seenEquals = true
		}
		if ctx == WordCtxRegex && ch == "(" {
			parenDepth += 1
			chars = append(chars, l.Advance())
			continue
		}
		if ctx == WordCtxRegex && ch == ")" {
			if parenDepth > 0 {
				parenDepth -= 1
				chars = append(chars, l.Advance())
				continue
			}
			break
		}
		if _containsAny([]interface{}{WordCtxCond, WordCtxRegex}, ctx) && ch == "[" {
			forRegex = ctx == WordCtxRegex
			if l._ReadBracketExpression(&chars, &parts, forRegex, parenDepth) {
				continue
			}
			chars = append(chars, l.Advance())
			continue
		}
		if ctx == WordCtxCond && ch == "(" {
			if l._Extglob && len(chars) > 0 && _IsExtglobPrefix(chars[len(chars)-1]) {
				chars = append(chars, l.Advance())
				content = l._ParseMatchedPair("(", ")", MatchedPairFlags_EXTGLOB, false)
				chars = append(chars, content)
				chars = append(chars, ")")
				continue
			} else {
				break
			}
		}
		if ctx == WordCtxRegex && _IsWhitespace(ch) && parenDepth > 0 {
			chars = append(chars, l.Advance())
			continue
		}
		if ch == "'" {
			l.Advance()
			trackNewline = ctx == WordCtxNormal
			content, sawNewline := l._ReadSingleQuote(start)
			_ = content
			_ = sawNewline
			chars = append(chars, content)
			if trackNewline && sawNewline && l._Parser != nil {
				l._Parser._Saw_newline_in_single_quote = true
			}
			continue
		}
		if ch == "\"" {
			l.Advance()
			if ctx == WordCtxNormal {
				chars = append(chars, "\"")
				inSingleInDquote = false
				for !(l.AtEnd()) && (inSingleInDquote || l.Peek() != "\"") {
					c = l.Peek()
					if inSingleInDquote {
						chars = append(chars, l.Advance())
						if c == "'" {
							inSingleInDquote = false
						}
						continue
					}
					if c == "\\" && l.Pos+1 < l.Length {
						nextC = string(l.Source_runes[l.Pos+1])
						if nextC == "\n" {
							l.Advance()
							l.Advance()
						} else {
							chars = append(chars, l.Advance())
							chars = append(chars, l.Advance())
						}
					} else if c == "$" {
						l._SyncToParser()
						if !(l._Parser._ParseDollarExpansion(&chars, &parts, true)) {
							l._SyncFromParser()
							chars = append(chars, l.Advance())
						} else {
							l._SyncFromParser()
						}
					} else if c == "`" {
						l._SyncToParser()
						cmdsubResult0, cmdsubResult1 = l._Parser._ParseBacktickSubstitution()
						l._SyncFromParser()
						if cmdsubResult0 != nil {
							parts = append(parts, cmdsubResult0.(Node))
							chars = append(chars, cmdsubResult1)
						} else {
							chars = append(chars, l.Advance())
						}
					} else {
						chars = append(chars, l.Advance())
					}
				}
				if l.AtEnd() {
					panic(NewParseError("Unterminated double quote", start, 0))
				}
				chars = append(chars, l.Advance())
			} else {
				handleLineContinuation = ctx == WordCtxCond
				l._SyncToParser()
				l._Parser._ScanDoubleQuote(&chars, &parts, start, handleLineContinuation)
				l._SyncFromParser()
			}
			continue
		}
		if ch == "\\" && l.Pos+1 < l.Length {
			nextCh = string(l.Source_runes[l.Pos+1])
			if ctx != WordCtxRegex && nextCh == "\n" {
				l.Advance()
				l.Advance()
			} else {
				chars = append(chars, l.Advance())
				chars = append(chars, l.Advance())
			}
			continue
		}
		if ctx != WordCtxRegex && ch == "$" && l.Pos+1 < l.Length && string(l.Source_runes[l.Pos+1]) == "'" {
			ansiResult0, ansiResult1 = l._ReadAnsiCQuote()
			if ansiResult0 != nil {
				parts = append(parts, ansiResult0.(Node))
				chars = append(chars, ansiResult1)
			} else {
				chars = append(chars, l.Advance())
			}
			continue
		}
		if ctx != WordCtxRegex && ch == "$" && l.Pos+1 < l.Length && string(l.Source_runes[l.Pos+1]) == "\"" {
			localeResult0, localeResult1, localeResult2 = l._ReadLocaleString()
			if localeResult0 != nil {
				parts = append(parts, localeResult0.(Node))
				parts = append(parts, localeResult2...)
				chars = append(chars, localeResult1)
			} else {
				chars = append(chars, l.Advance())
			}
			continue
		}
		if ch == "$" {
			l._SyncToParser()
			if !(l._Parser._ParseDollarExpansion(&chars, &parts, false)) {
				l._SyncFromParser()
				chars = append(chars, l.Advance())
			} else {
				l._SyncFromParser()
				if l._Extglob && ctx == WordCtxNormal && len(chars) > 0 && len(chars[len(chars)-1]) == 2 && _runeAt(chars[len(chars)-1], 0) == "$" && strings.Contains("?*@", _runeAt(chars[len(chars)-1], 1)) && !(l.AtEnd()) && l.Peek() == "(" {
					chars = append(chars, l.Advance())
					content = l._ParseMatchedPair("(", ")", MatchedPairFlags_EXTGLOB, false)
					chars = append(chars, content)
					chars = append(chars, ")")
				}
			}
			continue
		}
		if ctx != WordCtxRegex && ch == "`" {
			l._SyncToParser()
			cmdsubResult0, cmdsubResult1 = l._Parser._ParseBacktickSubstitution()
			l._SyncFromParser()
			if cmdsubResult0 != nil {
				parts = append(parts, cmdsubResult0.(Node))
				chars = append(chars, cmdsubResult1)
			} else {
				chars = append(chars, l.Advance())
			}
			continue
		}
		if ctx != WordCtxRegex && _IsRedirectChar(ch) && l.Pos+1 < l.Length && string(l.Source_runes[l.Pos+1]) == "(" {
			l._SyncToParser()
			procsubResult0, procsubResult1 = l._Parser._ParseProcessSubstitution()
			l._SyncFromParser()
			if procsubResult0 != nil {
				parts = append(parts, procsubResult0.(Node))
				chars = append(chars, procsubResult1)
			} else if len(procsubResult1) > 0 {
				chars = append(chars, procsubResult1)
			} else {
				chars = append(chars, l.Advance())
				if ctx == WordCtxNormal {
					chars = append(chars, l.Advance())
				}
			}
			continue
		}
		if ctx == WordCtxNormal && ch == "(" && len(chars) > 0 && bracketDepth == 0 {
			isArrayAssign = false
			if len(chars) >= 3 && chars[len(chars)-2] == "+" && chars[len(chars)-1] == "=" {
				isArrayAssign = _IsArrayAssignmentPrefix(chars[0 : len(chars)-2])
			} else if chars[len(chars)-1] == "=" && len(chars) >= 2 {
				isArrayAssign = _IsArrayAssignmentPrefix(chars[0 : len(chars)-1])
			}
			if isArrayAssign && (atCommandStart || inAssignBuiltin) {
				l._SyncToParser()
				arrayResult0, arrayResult1 = l._Parser._ParseArrayLiteral()
				l._SyncFromParser()
				if arrayResult0 != nil {
					parts = append(parts, arrayResult0.(Node))
					chars = append(chars, arrayResult1)
				} else {
					break
				}
				continue
			}
		}
		if l._Extglob && ctx == WordCtxNormal && _IsExtglobPrefix(ch) && l.Pos+1 < l.Length && string(l.Source_runes[l.Pos+1]) == "(" {
			chars = append(chars, l.Advance())
			chars = append(chars, l.Advance())
			content = l._ParseMatchedPair("(", ")", MatchedPairFlags_EXTGLOB, false)
			chars = append(chars, content)
			chars = append(chars, ")")
			continue
		}
		if ctx == WordCtxNormal && (l._Parser_state&ParserStateFlags_PST_EOFTOKEN) != 0 && l._Eof_token != "" && ch == l._Eof_token && bracketDepth == 0 {
			if !(len(chars) > 0) {
				chars = append(chars, l.Advance())
			}
			break
		}
		if ctx == WordCtxNormal && _IsMetachar(ch) && bracketDepth == 0 {
			break
		}
		chars = append(chars, l.Advance())
	}
	if bracketDepth > 0 && bracketStartPos != -1 && l.AtEnd() {
		panic(NewMatchedPairError("unexpected EOF looking for `]'", bracketStartPos, 0))
	}
	if !(len(chars) > 0) {
		return nil
	}
	if len(parts) > 0 {
		return NewWord(strings.Join(chars, ""), parts)
	}
	return NewWord(strings.Join(chars, ""), nil)
}

func (l *Lexer) _ReadWord() *Token {
	start := l.Pos
	if l.Pos >= l.Length {
		return nil
	}
	c := l.Peek()
	if c == "" {
		return nil
	}
	isProcsub := (c == "<" || c == ">") && l.Pos+1 < l.Length && string(l.Source_runes[l.Pos+1]) == "("
	isRegexParen := l._Word_context == WordCtxRegex && (c == "(" || c == ")")
	if l.IsMetachar(c) && !(isProcsub) && !(isRegexParen) {
		return nil
	}
	word := l._ReadWordInternal(l._Word_context, l._At_command_start, l._In_array_literal, l._In_assign_builtin)
	if word == nil {
		return nil
	}
	return NewToken(TokenType_WORD, word.Value, start, nil, word)
}

func (l *Lexer) NextToken() *Token {
	var tok *Token
	if l._Token_cache != nil {
		tok = l._Token_cache
		l._Token_cache = nil
		l._Last_read_token = tok
		return tok
	}
	l.SkipBlanks()
	if l.AtEnd() {
		tok = NewToken(TokenType_EOF, "", l.Pos, nil, nil)
		l._Last_read_token = tok
		return tok
	}
	if l._Eof_token != "" && l.Peek() == l._Eof_token && !((l._Parser_state & ParserStateFlags_PST_CASEPAT) != 0) && !((l._Parser_state & ParserStateFlags_PST_EOFTOKEN) != 0) {
		tok = NewToken(TokenType_EOF, "", l.Pos, nil, nil)
		l._Last_read_token = tok
		return tok
	}
	for l._SkipComment() {
		l.SkipBlanks()
		if l.AtEnd() {
			tok = NewToken(TokenType_EOF, "", l.Pos, nil, nil)
			l._Last_read_token = tok
			return tok
		}
		if l._Eof_token != "" && l.Peek() == l._Eof_token && !((l._Parser_state & ParserStateFlags_PST_CASEPAT) != 0) && !((l._Parser_state & ParserStateFlags_PST_EOFTOKEN) != 0) {
			tok = NewToken(TokenType_EOF, "", l.Pos, nil, nil)
			l._Last_read_token = tok
			return tok
		}
	}
	tok = l._ReadOperator()
	if tok != nil {
		l._Last_read_token = tok
		return tok
	}
	tok = l._ReadWord()
	if tok != nil {
		l._Last_read_token = tok
		return tok
	}
	tok = NewToken(TokenType_EOF, "", l.Pos, nil, nil)
	l._Last_read_token = tok
	return tok
}

func (l *Lexer) PeekToken() *Token {
	var savedLast *Token
	if l._Token_cache == nil {
		savedLast = l._Last_read_token
		l._Token_cache = l.NextToken()
		l._Last_read_token = savedLast
	}
	return l._Token_cache
}

func (l *Lexer) _ReadAnsiCQuote() (Node, string) {
	var foundClose bool
	var ch string
	if l.AtEnd() || l.Peek() != "$" {
		return nil, ""
	}
	if l.Pos+1 >= l.Length || string(l.Source_runes[l.Pos+1]) != "'" {
		return nil, ""
	}
	start := l.Pos
	l.Advance()
	l.Advance()
	contentChars := []string{}
	foundClose = false
	for !(l.AtEnd()) {
		ch = l.Peek()
		if ch == "'" {
			l.Advance()
			foundClose = true
			break
		} else if ch == "\\" {
			contentChars = append(contentChars, l.Advance())
			if !(l.AtEnd()) {
				contentChars = append(contentChars, l.Advance())
			}
		} else {
			contentChars = append(contentChars, l.Advance())
		}
	}
	if !(foundClose) {
		panic(NewMatchedPairError("unexpected EOF while looking for matching `''", start, 0))
	}
	text := _Substring(l.Source, start, l.Pos)
	content := strings.Join(contentChars, "")
	node := NewAnsiCQuote(content)
	return node, text
}

func (l *Lexer) _SyncToParser() {
	if l._Parser != nil {
		l._Parser.Pos = l.Pos
	}
}

func (l *Lexer) _SyncFromParser() {
	if l._Parser != nil {
		l.Pos = l._Parser.Pos
	}
}

func (l *Lexer) _ReadLocaleString() (Node, string, []Node) {
	var foundClose bool
	var ch string
	var nextCh string
	if l.AtEnd() || l.Peek() != "$" {
		return nil, "", []Node{}
	}
	if l.Pos+1 >= l.Length || string(l.Source_runes[l.Pos+1]) != "\"" {
		return nil, "", []Node{}
	}
	start := l.Pos
	l.Advance()
	l.Advance()
	contentChars := []string{}
	innerParts := []Node{}
	foundClose = false
	for !(l.AtEnd()) {
		ch = l.Peek()
		if ch == "\"" {
			l.Advance()
			foundClose = true
			break
		} else if ch == "\\" && l.Pos+1 < l.Length {
			nextCh = string(l.Source_runes[l.Pos+1])
			if nextCh == "\n" {
				l.Advance()
				l.Advance()
			} else {
				contentChars = append(contentChars, l.Advance())
				contentChars = append(contentChars, l.Advance())
			}
		} else if ch == "$" && l.Pos+2 < l.Length && string(l.Source_runes[l.Pos+1]) == "(" && string(l.Source_runes[l.Pos+2]) == "(" {
			l._SyncToParser()
			arithNode, arithText := l._Parser._ParseArithmeticExpansion()
			_ = arithNode
			_ = arithText
			l._SyncFromParser()
			if arithNode != nil {
				innerParts = append(innerParts, arithNode.(Node))
				contentChars = append(contentChars, arithText)
			} else {
				l._SyncToParser()
				cmdsubNode, cmdsubText := l._Parser._ParseCommandSubstitution()
				_ = cmdsubNode
				_ = cmdsubText
				l._SyncFromParser()
				if cmdsubNode != nil {
					innerParts = append(innerParts, cmdsubNode.(Node))
					contentChars = append(contentChars, cmdsubText)
				} else {
					contentChars = append(contentChars, l.Advance())
				}
			}
		} else if _IsExpansionStart(l.Source, l.Pos, "$(") {
			l._SyncToParser()
			cmdsubNode, cmdsubText := l._Parser._ParseCommandSubstitution()
			_ = cmdsubNode
			_ = cmdsubText
			l._SyncFromParser()
			if cmdsubNode != nil {
				innerParts = append(innerParts, cmdsubNode.(Node))
				contentChars = append(contentChars, cmdsubText)
			} else {
				contentChars = append(contentChars, l.Advance())
			}
		} else if ch == "$" {
			l._SyncToParser()
			paramNode, paramText := l._Parser._ParseParamExpansion(false)
			_ = paramNode
			_ = paramText
			l._SyncFromParser()
			if paramNode != nil {
				innerParts = append(innerParts, paramNode.(Node))
				contentChars = append(contentChars, paramText)
			} else {
				contentChars = append(contentChars, l.Advance())
			}
		} else if ch == "`" {
			l._SyncToParser()
			cmdsubNode, cmdsubText := l._Parser._ParseBacktickSubstitution()
			_ = cmdsubNode
			_ = cmdsubText
			l._SyncFromParser()
			if cmdsubNode != nil {
				innerParts = append(innerParts, cmdsubNode.(Node))
				contentChars = append(contentChars, cmdsubText)
			} else {
				contentChars = append(contentChars, l.Advance())
			}
		} else {
			contentChars = append(contentChars, l.Advance())
		}
	}
	if !(foundClose) {
		l.Pos = start
		return nil, "", []Node{}
	}
	content := strings.Join(contentChars, "")
	text := "$\"" + content + "\""
	return NewLocaleString(content), text, innerParts
}

func (l *Lexer) _UpdateDolbraceForOp(op string, hasParam bool) {
	if l._Dolbrace_state == DolbraceState_NONE {
		return
	}
	if op == "" || _runeLen(op) == 0 {
		return
	}
	firstChar := _runeAt(op, 0)
	if l._Dolbrace_state == DolbraceState_PARAM && hasParam {
		if strings.Contains("%#^,", firstChar) {
			l._Dolbrace_state = DolbraceState_QUOTE
			return
		}
		if firstChar == "/" {
			l._Dolbrace_state = DolbraceState_QUOTE2
			return
		}
	}
	if l._Dolbrace_state == DolbraceState_PARAM {
		if strings.Contains("#%^,~:-=?+/", firstChar) {
			l._Dolbrace_state = DolbraceState_OP
		}
	}
}

func (l *Lexer) _ConsumeParamOperator() string {
	var nextCh string
	if l.AtEnd() {
		return ""
	}
	ch := l.Peek()
	if ch == ":" {
		l.Advance()
		if l.AtEnd() {
			return ":"
		}
		nextCh = l.Peek()
		if _IsSimpleParamOp(nextCh) {
			l.Advance()
			return ":" + nextCh
		}
		return ":"
	}
	if _IsSimpleParamOp(ch) {
		l.Advance()
		return ch
	}
	if ch == "#" {
		l.Advance()
		if !(l.AtEnd()) && l.Peek() == "#" {
			l.Advance()
			return "##"
		}
		return "#"
	}
	if ch == "%" {
		l.Advance()
		if !(l.AtEnd()) && l.Peek() == "%" {
			l.Advance()
			return "%%"
		}
		return "%"
	}
	if ch == "/" {
		l.Advance()
		if !(l.AtEnd()) {
			nextCh = l.Peek()
			if nextCh == "/" {
				l.Advance()
				return "//"
			} else if nextCh == "#" {
				l.Advance()
				return "/#"
			} else if nextCh == "%" {
				l.Advance()
				return "/%"
			}
		}
		return "/"
	}
	if ch == "^" {
		l.Advance()
		if !(l.AtEnd()) && l.Peek() == "^" {
			l.Advance()
			return "^^"
		}
		return "^"
	}
	if ch == "," {
		l.Advance()
		if !(l.AtEnd()) && l.Peek() == "," {
			l.Advance()
			return ",,"
		}
		return ","
	}
	if ch == "@" {
		l.Advance()
		return "@"
	}
	return ""
}

func (l *Lexer) _ParamSubscriptHasClose(startPos int) bool {
	var c string
	depth := 1
	i := startPos + 1
	quote := NewQuoteState()
	for i < l.Length {
		c = string(l.Source_runes[i])
		if quote.Single {
			if c == "'" {
				quote.Single = false
			}
			i += 1
			continue
		}
		if quote.Double {
			if c == "\\" && i+1 < l.Length {
				i += 2
				continue
			}
			if c == "\"" {
				quote.Double = false
			}
			i += 1
			continue
		}
		if c == "'" {
			quote.Single = true
			i += 1
			continue
		}
		if c == "\"" {
			quote.Double = true
			i += 1
			continue
		}
		if c == "\\" {
			i += 2
			continue
		}
		if c == "}" {
			return false
		}
		if c == "[" {
			depth += 1
		} else if c == "]" {
			depth -= 1
			if depth == 0 {
				return true
			}
		}
		i += 1
	}
	return false
}

func (l *Lexer) _ConsumeParamName() string {
	var nameChars []string
	var c string
	var content string
	if l.AtEnd() {
		return ""
	}
	ch := l.Peek()
	if _IsSpecialParam(ch) {
		if ch == "$" && l.Pos+1 < l.Length && strings.Contains("{'\"", string(l.Source_runes[l.Pos+1])) {
			return ""
		}
		l.Advance()
		return ch
	}
	if _strIsDigits(ch) {
		nameChars = []string{}
		for !(l.AtEnd()) && _strIsDigits(l.Peek()) {
			nameChars = append(nameChars, l.Advance())
		}
		return strings.Join(nameChars, "")
	}
	if unicode.IsLetter(_runeFromChar(ch)) || ch == "_" {
		nameChars = []string{}
		for !(l.AtEnd()) {
			c = l.Peek()
			if (unicode.IsLetter(_runeFromChar(c)) || unicode.IsDigit(_runeFromChar(c))) || c == "_" {
				nameChars = append(nameChars, l.Advance())
			} else if c == "[" {
				if !(l._ParamSubscriptHasClose(l.Pos)) {
					break
				}
				nameChars = append(nameChars, l.Advance())
				content = l._ParseMatchedPair("[", "]", MatchedPairFlags_ARRAYSUB, false)
				nameChars = append(nameChars, content)
				nameChars = append(nameChars, "]")
				break
			} else {
				break
			}
		}
		if len(nameChars) > 0 {
			return strings.Join(nameChars, "")
		} else {
			return ""
		}
	}
	return ""
}

func (l *Lexer) _ReadParamExpansion(inDquote bool) (Node, string) {
	var text string
	var nameStart int
	var c string
	var name string
	if l.AtEnd() || l.Peek() != "$" {
		return nil, ""
	}
	start := l.Pos
	l.Advance()
	if l.AtEnd() {
		l.Pos = start
		return nil, ""
	}
	ch := l.Peek()
	if ch == "{" {
		l.Advance()
		return l._ReadBracedParam(start, inDquote)
	}
	if _IsSpecialParamUnbraced(ch) || _IsDigit(ch) || ch == "#" {
		l.Advance()
		text = _Substring(l.Source, start, l.Pos)
		return NewParamExpansion(ch, "", ""), text
	}
	if unicode.IsLetter(_runeFromChar(ch)) || ch == "_" {
		nameStart = l.Pos
		for !(l.AtEnd()) {
			c = l.Peek()
			if (unicode.IsLetter(_runeFromChar(c)) || unicode.IsDigit(_runeFromChar(c))) || c == "_" {
				l.Advance()
			} else {
				break
			}
		}
		name = _Substring(l.Source, nameStart, l.Pos)
		text = _Substring(l.Source, start, l.Pos)
		return NewParamExpansion(name, "", ""), text
	}
	l.Pos = start
	return nil, ""
}

func (l *Lexer) _ReadBracedParam(start int, inDquote bool) (Node, string) {
	var param string
	var text string
	var suffix string
	var trailing string
	var op string
	var arg string
	var content string
	var dollarCount int
	var backtickPos int
	var bc string
	var nextC string
	var flags int
	var paramEndsWithDollar bool
	var inner string
	var subParser *Parser
	var parsed Node
	var formatted string
	if l.AtEnd() {
		panic(NewMatchedPairError("unexpected EOF looking for `}'", start, 0))
	}
	savedDolbrace := l._Dolbrace_state
	l._Dolbrace_state = DolbraceState_PARAM
	ch := l.Peek()
	if _IsFunsubChar(ch) {
		l._Dolbrace_state = savedDolbrace
		return l._ReadFunsub(start)
	}
	if ch == "#" {
		l.Advance()
		param = l._ConsumeParamName()
		if len(param) > 0 && !(l.AtEnd()) && l.Peek() == "}" {
			l.Advance()
			text = _Substring(l.Source, start, l.Pos)
			l._Dolbrace_state = savedDolbrace
			return NewParamLength(param), text
		}
		l.Pos = start + 2
	}
	if ch == "!" {
		l.Advance()
		for !(l.AtEnd()) && _IsWhitespaceNoNewline(l.Peek()) {
			l.Advance()
		}
		param = l._ConsumeParamName()
		if len(param) > 0 {
			for !(l.AtEnd()) && _IsWhitespaceNoNewline(l.Peek()) {
				l.Advance()
			}
			if !(l.AtEnd()) && l.Peek() == "}" {
				l.Advance()
				text = _Substring(l.Source, start, l.Pos)
				l._Dolbrace_state = savedDolbrace
				return NewParamIndirect(param, "", ""), text
			}
			if !(l.AtEnd()) && _IsAtOrStar(l.Peek()) {
				suffix = l.Advance()
				trailing = l._ParseMatchedPair("{", "}", MatchedPairFlags_DOLBRACE, false)
				text = _Substring(l.Source, start, l.Pos)
				l._Dolbrace_state = savedDolbrace
				return NewParamIndirect(param+suffix+trailing, "", ""), text
			}
			op = l._ConsumeParamOperator()
			if op == "" && !(l.AtEnd()) && !strings.Contains("}\"'`", l.Peek()) {
				op = l.Advance()
			}
			if op != "" && !strings.Contains("\"'`", op) {
				arg = l._ParseMatchedPair("{", "}", MatchedPairFlags_DOLBRACE, false)
				text = _Substring(l.Source, start, l.Pos)
				l._Dolbrace_state = savedDolbrace
				return NewParamIndirect(param, op, arg), text
			}
			if l.AtEnd() {
				l._Dolbrace_state = savedDolbrace
				panic(NewMatchedPairError("unexpected EOF looking for `}'", start, 0))
			}
			l.Pos = start + 2
		} else {
			l.Pos = start + 2
		}
	}
	param = l._ConsumeParamName()
	if !(len(param) > 0) {
		if !(l.AtEnd()) && (strings.Contains("-=+?", l.Peek()) || l.Peek() == ":" && l.Pos+1 < l.Length && _IsSimpleParamOp(string(l.Source_runes[l.Pos+1]))) {
			param = ""
		} else {
			content = l._ParseMatchedPair("{", "}", MatchedPairFlags_DOLBRACE, false)
			text = "${" + content + "}"
			l._Dolbrace_state = savedDolbrace
			return NewParamExpansion(content, "", ""), text
		}
	}
	if l.AtEnd() {
		l._Dolbrace_state = savedDolbrace
		panic(NewMatchedPairError("unexpected EOF looking for `}'", start, 0))
	}
	if l.Peek() == "}" {
		l.Advance()
		text = _Substring(l.Source, start, l.Pos)
		l._Dolbrace_state = savedDolbrace
		return NewParamExpansion(param, "", ""), text
	}
	op = l._ConsumeParamOperator()
	if op == "" {
		if !(l.AtEnd()) && l.Peek() == "$" && l.Pos+1 < l.Length && _containsAny([]interface{}{"\"", "'"}, string(l.Source_runes[l.Pos+1])) {
			dollarCount = 1 + _CountConsecutiveDollarsBefore(l.Source, l.Pos)
			if dollarCount%2 == 1 {
				op = ""
			} else {
				op = l.Advance()
			}
		} else if !(l.AtEnd()) && l.Peek() == "`" {
			backtickPos = l.Pos
			l.Advance()
			for !(l.AtEnd()) && l.Peek() != "`" {
				bc = l.Peek()
				if bc == "\\" && l.Pos+1 < l.Length {
					nextC = string(l.Source_runes[l.Pos+1])
					if _IsEscapeCharInBacktick(nextC) {
						l.Advance()
					}
				}
				l.Advance()
			}
			if l.AtEnd() {
				l._Dolbrace_state = savedDolbrace
				panic(NewParseError("Unterminated backtick", backtickPos, 0))
			}
			l.Advance()
			op = "`"
		} else if !(l.AtEnd()) && l.Peek() == "$" && l.Pos+1 < l.Length && string(l.Source_runes[l.Pos+1]) == "{" {
			op = ""
		} else if !(l.AtEnd()) && _containsAny([]interface{}{"'", "\""}, l.Peek()) {
			op = ""
		} else if !(l.AtEnd()) && l.Peek() == "\\" {
			op = l.Advance()
			if !(l.AtEnd()) {
				op += l.Advance()
			}
		} else {
			op = l.Advance()
		}
	}
	l._UpdateDolbraceForOp(op, _runeLen(param) > 0)
	func() {
		defer func() {
			if r := recover(); r != nil {
				l._Dolbrace_state = savedDolbrace
				panic(r)
			}
		}()
		flags = _ternary(inDquote, MatchedPairFlags_DQUOTE, MatchedPairFlags_NONE)
		paramEndsWithDollar = param != "" && strings.HasSuffix(param, "$")
		arg = l._CollectParamArgument(flags, paramEndsWithDollar)
	}()
	if _containsAny([]interface{}{"<", ">"}, op) && strings.HasPrefix(arg, "(") && strings.HasSuffix(arg, ")") {
		inner = _Substring(arg, 1, _runeLen(arg)-1)
		func() {
			defer func() {
				if r := recover(); r != nil {
				}
			}()
			subParser = NewParser(inner, true, l._Parser._Extglob)
			parsed = subParser.ParseList(true)
			if parsed != nil && subParser.AtEnd() {
				formatted = _FormatCmdsubNode(parsed, 0, true, false, true)
				arg = "(" + formatted + ")"
			}
		}()
	}
	text = "${" + param + op + arg + "}"
	l._Dolbrace_state = savedDolbrace
	return NewParamExpansion(param, op, arg), text
}

func (l *Lexer) _ReadFunsub(start int) (Node, string) {
	return l._Parser._ParseFunsub(start)
}

func NewWord(value string, parts []Node) *Word {
	w := &Word{}
	w.kind = "word"
	w.Value = value
	if parts == nil {
		parts = []Node{}
	}
	w.Parts = parts
	return w
}

func (w *Word) ToSexp() string {
	var value string
	value = w.Value
	value = w._ExpandAllAnsiCQuotes(value)
	value = w._StripLocaleStringDollars(value)
	value = w._NormalizeArrayWhitespace(value)
	value = w._FormatCommandSubstitutions(value, false)
	value = w._NormalizeParamExpansionNewlines(value)
	value = w._StripArithLineContinuations(value)
	value = w._DoubleCtlescSmart(value)
	value = strings.ReplaceAll(value, "\x7f", "\x01\x7f")
	value = strings.ReplaceAll(value, "\\", "\\\\")
	if strings.HasSuffix(value, "\\\\") && !(strings.HasSuffix(value, "\\\\\\\\")) {
		value = value + "\\\\"
	}
	escaped := strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(value, "\"", "\\\""), "\n", "\\n"), "\t", "\\t")
	return "(word \"" + escaped + "\")"
}

func (w *Word) _AppendWithCtlesc(result *[]byte, byteVal int) {
	*result = append(*result, byte(byteVal))
}

func (w *Word) _DoubleCtlescSmart(value string) string {
	var bsCount int
	result := []rune{}
	quote := NewQuoteState()
	for _, c := range value {
		if c == '\'' && !(quote.Double) {
			quote.Single = !(quote.Single)
		} else if c == '"' && !(quote.Single) {
			quote.Double = !(quote.Double)
		}
		result = append(result, c)
		if c == '\x01' {
			if quote.Double {
				bsCount = 0
				for j := len(result) - 2; j > -1; j += -1 {
					if result[j] == '\\' {
						bsCount += 1
					} else {
						break
					}
				}
				if bsCount%2 == 0 {
					result = append(result, '\x01')
				}
			} else {
				result = append(result, '\x01')
			}
		}
	}
	return string(result)
}

func (w *Word) _NormalizeParamExpansionNewlines(value string) string {
	var c string
	var hadLeadingNewline bool
	var depth int
	var ch string
	result := []string{}
	i := 0
	quote := NewQuoteState()
	for i < _runeLen(value) {
		c = _runeAt(value, i)
		if c == "'" && !(quote.Double) {
			quote.Single = !(quote.Single)
			result = append(result, c)
			i += 1
		} else if c == "\"" && !(quote.Single) {
			quote.Double = !(quote.Double)
			result = append(result, c)
			i += 1
		} else if _IsExpansionStart(value, i, "${") && !(quote.Single) {
			result = append(result, "$")
			result = append(result, "{")
			i += 2
			hadLeadingNewline = i < _runeLen(value) && _runeAt(value, i) == "\n"
			if hadLeadingNewline {
				result = append(result, " ")
				i += 1
			}
			depth = 1
			for i < _runeLen(value) && depth > 0 {
				ch = _runeAt(value, i)
				if ch == "\\" && i+1 < _runeLen(value) && !(quote.Single) {
					if _runeAt(value, i+1) == "\n" {
						i += 2
						continue
					}
					result = append(result, ch)
					result = append(result, _runeAt(value, i+1))
					i += 2
					continue
				}
				if ch == "'" && !(quote.Double) {
					quote.Single = !(quote.Single)
				} else if ch == "\"" && !(quote.Single) {
					quote.Double = !(quote.Double)
				} else if !(quote.InQuotes()) {
					if ch == "{" {
						depth += 1
					} else if ch == "}" {
						depth -= 1
						if depth == 0 {
							if hadLeadingNewline {
								result = append(result, " ")
							}
							result = append(result, ch)
							i += 1
							break
						}
					}
				}
				result = append(result, ch)
				i += 1
			}
		} else {
			result = append(result, c)
			i += 1
		}
	}
	return strings.Join(result, "")
}

func (w *Word) _ShSingleQuote(s string) string {
	if !(len(s) > 0) {
		return "''"
	}
	if s == "'" {
		return "\\'"
	}
	result := []string{"'"}
	for _, c := range s {
		if c == '\'' {
			result = append(result, "'\\''")
		} else {
			result = append(result, string(c))
		}
	}
	result = append(result, "'")
	return strings.Join(result, "")
}

func (w *Word) _AnsiCToBytes(inner string) []byte {
	var i int
	var c string
	var simple int
	var j int
	var hexStr string
	var byteVal int
	var codepoint int
	var ctrlChar string
	var skipExtra int
	var ctrlVal int
	result := []byte{}
	i = 0
	for i < _runeLen(inner) {
		if _runeAt(inner, i) == "\\" && i+1 < _runeLen(inner) {
			c = _runeAt(inner, i+1)
			simple = _GetAnsiEscape(c)
			if simple >= 0 {
				result = append(result, byte(simple))
				i += 2
			} else if c == "'" {
				result = append(result, byte(39))
				i += 2
			} else if c == "x" {
				if i+2 < _runeLen(inner) && _runeAt(inner, i+2) == "{" {
					j = i + 3
					for j < _runeLen(inner) && _IsHexDigit(_runeAt(inner, j)) {
						j += 1
					}
					hexStr = _Substring(inner, i+3, j)
					if j < _runeLen(inner) && _runeAt(inner, j) == "}" {
						j += 1
					}
					if !(len(hexStr) > 0) {
						return result
					}
					byteVal = _parseInt(hexStr, 16) & 255
					if byteVal == 0 {
						return result
					}
					w._AppendWithCtlesc(&result, byteVal)
					i = j
				} else {
					j = i + 2
					for j < _runeLen(inner) && j < i+4 && _IsHexDigit(_runeAt(inner, j)) {
						j += 1
					}
					if j > i+2 {
						byteVal = _parseInt(_Substring(inner, i+2, j), 16)
						if byteVal == 0 {
							return result
						}
						w._AppendWithCtlesc(&result, byteVal)
						i = j
					} else {
						result = append(result, inner[i])
						i += 1
					}
				}
			} else if c == "u" {
				j = i + 2
				for j < _runeLen(inner) && j < i+6 && _IsHexDigit(_runeAt(inner, j)) {
					j += 1
				}
				if j > i+2 {
					codepoint = _parseInt(_Substring(inner, i+2, j), 16)
					if codepoint == 0 {
						return result
					}
					result = append(result, []byte(string(rune(codepoint)))...)
					i = j
				} else {
					result = append(result, inner[i])
					i += 1
				}
			} else if c == "U" {
				j = i + 2
				for j < _runeLen(inner) && j < i+10 && _IsHexDigit(_runeAt(inner, j)) {
					j += 1
				}
				if j > i+2 {
					codepoint = _parseInt(_Substring(inner, i+2, j), 16)
					if codepoint == 0 {
						return result
					}
					result = append(result, []byte(string(rune(codepoint)))...)
					i = j
				} else {
					result = append(result, inner[i])
					i += 1
				}
			} else if c == "c" {
				if i+3 <= _runeLen(inner) {
					ctrlChar = _runeAt(inner, i+2)
					skipExtra = 0
					if ctrlChar == "\\" && i+4 <= _runeLen(inner) && _runeAt(inner, i+3) == "\\" {
						skipExtra = 1
					}
					ctrlVal = int(rune(ctrlChar[0])) & 31
					if ctrlVal == 0 {
						return result
					}
					w._AppendWithCtlesc(&result, ctrlVal)
					i += 3 + skipExtra
				} else {
					result = append(result, inner[i])
					i += 1
				}
			} else if c == "0" {
				j = i + 2
				for j < _runeLen(inner) && j < i+4 && _IsOctalDigit(_runeAt(inner, j)) {
					j += 1
				}
				if j > i+2 {
					byteVal = _parseInt(_Substring(inner, i+1, j), 8) & 255
					if byteVal == 0 {
						return result
					}
					w._AppendWithCtlesc(&result, byteVal)
					i = j
				} else {
					return result
				}
			} else if c >= "1" && c <= "7" {
				j = i + 1
				for j < _runeLen(inner) && j < i+4 && _IsOctalDigit(_runeAt(inner, j)) {
					j += 1
				}
				byteVal = _parseInt(_Substring(inner, i+1, j), 8) & 255
				if byteVal == 0 {
					return result
				}
				w._AppendWithCtlesc(&result, byteVal)
				i = j
			} else {
				result = append(result, byte(92))
				result = append(result, byte(int(rune(c[0]))))
				i += 2
			}
		} else {
			result = append(result, []byte(_runeAt(inner, i))...)
			i += 1
		}
	}
	return result
}

func (w *Word) _ExpandAnsiCEscapes(value string) string {
	if !(strings.HasPrefix(value, "'") && strings.HasSuffix(value, "'")) {
		return value
	}
	inner := _Substring(value, 1, _runeLen(value)-1)
	literalBytes := w._AnsiCToBytes(inner)
	literalStr := string(literalBytes)
	return w._ShSingleQuote(literalStr)
}

func (w *Word) _ExpandAllAnsiCQuotes(value string) string {
	var i int
	var inBacktick bool
	var ch string
	var effectiveInDquote bool
	var isAnsiC bool
	var j int
	var ansiStr string
	var expanded string
	var outerInDquote bool
	var inner string
	var resultStr string
	var inPattern bool
	var lastBraceIdx int
	var afterBrace string
	var varNameLen int
	var c interface{}
	var opStart string
	var firstChar string
	var rest string
	result := []string{}
	i = 0
	quote := NewQuoteState()
	inBacktick = false
	braceDepth := 0
	for i < _runeLen(value) {
		ch = _runeAt(value, i)
		if ch == "`" && !(quote.Single) {
			inBacktick = !(inBacktick)
			result = append(result, ch)
			i += 1
			continue
		}
		if inBacktick {
			if ch == "\\" && i+1 < _runeLen(value) {
				result = append(result, ch)
				result = append(result, _runeAt(value, i+1))
				i += 2
			} else {
				result = append(result, ch)
				i += 1
			}
			continue
		}
		if !(quote.Single) {
			if _IsExpansionStart(value, i, "${") {
				braceDepth += 1
				quote.Push()
				result = append(result, "${")
				i += 2
				continue
			} else if ch == "}" && braceDepth > 0 && !(quote.Double) {
				braceDepth -= 1
				result = append(result, ch)
				quote.Pop()
				i += 1
				continue
			}
		}
		effectiveInDquote = quote.Double
		if ch == "'" && !(effectiveInDquote) {
			isAnsiC = !(quote.Single) && i > 0 && _runeAt(value, i-1) == "$" && _CountConsecutiveDollarsBefore(value, i-1)%2 == 0
			if !(isAnsiC) {
				quote.Single = !(quote.Single)
			}
			result = append(result, ch)
			i += 1
		} else if ch == "\"" && !(quote.Single) {
			quote.Double = !(quote.Double)
			result = append(result, ch)
			i += 1
		} else if ch == "\\" && i+1 < _runeLen(value) && !(quote.Single) {
			result = append(result, ch)
			result = append(result, _runeAt(value, i+1))
			i += 2
		} else if strings.HasPrefix(value[i:], "$'") && !(quote.Single) && !(effectiveInDquote) && _CountConsecutiveDollarsBefore(value, i)%2 == 0 {
			j = i + 2
			for j < _runeLen(value) {
				if _runeAt(value, j) == "\\" && j+1 < _runeLen(value) {
					j += 2
				} else if _runeAt(value, j) == "'" {
					j += 1
					break
				} else {
					j += 1
				}
			}
			ansiStr = _Substring(value, i, j)
			expanded = w._ExpandAnsiCEscapes(_Substring(ansiStr, 1, _runeLen(ansiStr)))
			outerInDquote = quote.OuterDouble()
			if braceDepth > 0 && outerInDquote && strings.HasPrefix(expanded, "'") && strings.HasSuffix(expanded, "'") {
				inner = _Substring(expanded, 1, _runeLen(expanded)-1)
				if strings.Index(inner, "\x01") == -1 {
					resultStr = strings.Join(result, "")
					inPattern = false
					lastBraceIdx = strings.LastIndex(resultStr, "${")
					if lastBraceIdx >= 0 {
						afterBrace = _Substring(resultStr, lastBraceIdx+2, _runeLen(resultStr))
						varNameLen = 0
						if len(afterBrace) > 0 {
							if strings.Contains("@*#?-$!0123456789_", _runeAt(afterBrace, 0)) {
								varNameLen = 1
							} else if unicode.IsLetter(_runeFromChar(_runeAt(afterBrace, 0))) || _runeAt(afterBrace, 0) == "_" {
								for varNameLen < _runeLen(afterBrace) {
									c = _runeAt(afterBrace, varNameLen)
									if !((unicode.IsLetter(_runeFromChar(c)) || unicode.IsDigit(_runeFromChar(c))) || c == "_") {
										break
									}
									varNameLen += 1
								}
							}
						}
						if varNameLen > 0 && varNameLen < _runeLen(afterBrace) && !strings.Contains("#?-", _runeAt(afterBrace, 0)) {
							opStart = _Substring(afterBrace, varNameLen, _runeLen(afterBrace))
							if strings.HasPrefix(opStart, "@") && _runeLen(opStart) > 1 {
								opStart = _Substring(opStart, 1, _runeLen(opStart))
							}
							for _, op := range []string{"//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"} {
								if strings.HasPrefix(opStart, op) {
									inPattern = true
									break
								}
							}
							if !(inPattern) && len(opStart) > 0 && !strings.Contains("%#/^,~:+-=?", _runeAt(opStart, 0)) {
								for _, op := range []string{"//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"} {
									if strings.Contains(opStart, op) {
										inPattern = true
										break
									}
								}
							}
						} else if varNameLen == 0 && _runeLen(afterBrace) > 1 {
							firstChar = _runeAt(afterBrace, 0)
							if !strings.Contains("%#/^,", firstChar) {
								rest = _Substring(afterBrace, 1, _runeLen(afterBrace))
								for _, op := range []string{"//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"} {
									if strings.Contains(rest, op) {
										inPattern = true
										break
									}
								}
							}
						}
					}
					if !(inPattern) {
						expanded = inner
					}
				}
			}
			result = append(result, expanded)
			i = j
		} else {
			result = append(result, ch)
			i += 1
		}
	}
	return strings.Join(result, "")
}

func (w *Word) _StripLocaleStringDollars(value string) string {
	var bracketInDoubleQuote bool
	var ch string
	var dollarCount int
	result := []string{}
	i := 0
	braceDepth := 0
	bracketDepth := 0
	quote := NewQuoteState()
	braceQuote := NewQuoteState()
	bracketInDoubleQuote = false
	for i < _runeLen(value) {
		ch = _runeAt(value, i)
		if ch == "\\" && i+1 < _runeLen(value) && !(quote.Single) && !(braceQuote.Single) {
			result = append(result, ch)
			result = append(result, _runeAt(value, i+1))
			i += 2
		} else if strings.HasPrefix(value[i:], "${") && !(quote.Single) && !(braceQuote.Single) && (i == 0 || _runeAt(value, i-1) != "$") {
			braceDepth += 1
			braceQuote.Double = false
			braceQuote.Single = false
			result = append(result, "$")
			result = append(result, "{")
			i += 2
		} else if ch == "}" && braceDepth > 0 && !(quote.Single) && !(braceQuote.Double) && !(braceQuote.Single) {
			braceDepth -= 1
			result = append(result, ch)
			i += 1
		} else if ch == "[" && braceDepth > 0 && !(quote.Single) && !(braceQuote.Double) {
			bracketDepth += 1
			bracketInDoubleQuote = false
			result = append(result, ch)
			i += 1
		} else if ch == "]" && bracketDepth > 0 && !(quote.Single) && !(bracketInDoubleQuote) {
			bracketDepth -= 1
			result = append(result, ch)
			i += 1
		} else if ch == "'" && !(quote.Double) && braceDepth == 0 {
			quote.Single = !(quote.Single)
			result = append(result, ch)
			i += 1
		} else if ch == "\"" && !(quote.Single) && braceDepth == 0 {
			quote.Double = !(quote.Double)
			result = append(result, ch)
			i += 1
		} else if ch == "\"" && !(quote.Single) && bracketDepth > 0 {
			bracketInDoubleQuote = !(bracketInDoubleQuote)
			result = append(result, ch)
			i += 1
		} else if ch == "\"" && !(quote.Single) && !(braceQuote.Single) && braceDepth > 0 {
			braceQuote.Double = !(braceQuote.Double)
			result = append(result, ch)
			i += 1
		} else if ch == "'" && !(quote.Double) && !(braceQuote.Double) && braceDepth > 0 {
			braceQuote.Single = !(braceQuote.Single)
			result = append(result, ch)
			i += 1
		} else if strings.HasPrefix(value[i:], "$\"") && !(quote.Single) && !(braceQuote.Single) && (braceDepth > 0 || bracketDepth > 0 || !(quote.Double)) && !(braceQuote.Double) && !(bracketInDoubleQuote) {
			dollarCount = 1 + _CountConsecutiveDollarsBefore(value, i)
			if dollarCount%2 == 1 {
				result = append(result, "\"")
				if bracketDepth > 0 {
					bracketInDoubleQuote = true
				} else if braceDepth > 0 {
					braceQuote.Double = true
				} else {
					quote.Double = true
				}
				i += 2
			} else {
				result = append(result, ch)
				i += 1
			}
		} else {
			result = append(result, ch)
			i += 1
		}
	}
	return strings.Join(result, "")
}

func (w *Word) _NormalizeArrayWhitespace(value string) string {
	var depth int
	var closeParenPos int
	i := 0
	if !(i < _runeLen(value) && (unicode.IsLetter(_runeFromChar(_runeAt(value, i))) || _runeAt(value, i) == "_")) {
		return value
	}
	i += 1
	for i < _runeLen(value) && ((unicode.IsLetter(_runeFromChar(_runeAt(value, i))) || unicode.IsDigit(_runeFromChar(_runeAt(value, i)))) || _runeAt(value, i) == "_") {
		i += 1
	}
	for i < _runeLen(value) && _runeAt(value, i) == "[" {
		depth = 1
		i += 1
		for i < _runeLen(value) && depth > 0 {
			if _runeAt(value, i) == "[" {
				depth += 1
			} else if _runeAt(value, i) == "]" {
				depth -= 1
			}
			i += 1
		}
		if depth != 0 {
			return value
		}
	}
	if i < _runeLen(value) && _runeAt(value, i) == "+" {
		i += 1
	}
	if !(i+1 < _runeLen(value) && _runeAt(value, i) == "=" && _runeAt(value, i+1) == "(") {
		return value
	}
	prefix := _Substring(value, 0, i+1)
	openParenPos := i + 1
	if strings.HasSuffix(value, ")") {
		closeParenPos = _runeLen(value) - 1
	} else {
		closeParenPos = w._FindMatchingParen(value, openParenPos)
		if closeParenPos < 0 {
			return value
		}
	}
	inner := _Substring(value, openParenPos+1, closeParenPos)
	suffix := _Substring(value, closeParenPos+1, _runeLen(value))
	result := w._NormalizeArrayInner(inner)
	return prefix + "(" + result + ")" + suffix
}

func (w *Word) _FindMatchingParen(value string, openPos int) int {
	var ch string
	if openPos >= _runeLen(value) || _runeAt(value, openPos) != "(" {
		return -1
	}
	i := openPos + 1
	depth := 1
	quote := NewQuoteState()
	for i < _runeLen(value) && depth > 0 {
		ch = _runeAt(value, i)
		if ch == "\\" && i+1 < _runeLen(value) && !(quote.Single) {
			i += 2
			continue
		}
		if ch == "'" && !(quote.Double) {
			quote.Single = !(quote.Single)
			i += 1
			continue
		}
		if ch == "\"" && !(quote.Single) {
			quote.Double = !(quote.Double)
			i += 1
			continue
		}
		if quote.Single || quote.Double {
			i += 1
			continue
		}
		if ch == "#" {
			for i < _runeLen(value) && _runeAt(value, i) != "\n" {
				i += 1
			}
			continue
		}
		if ch == "(" {
			depth += 1
		} else if ch == ")" {
			depth -= 1
			if depth == 0 {
				return i
			}
		}
		i += 1
	}
	return -1
}

func (w *Word) _NormalizeArrayInner(inner string) string {
	var i int
	var inWhitespace bool
	var ch string
	var j int
	var dqContent []string
	var dqBraceDepth int
	var depth int
	normalized := []string{}
	i = 0
	inWhitespace = true
	braceDepth := 0
	bracketDepth := 0
	for i < _runeLen(inner) {
		ch = _runeAt(inner, i)
		if _IsWhitespace(ch) {
			if !(inWhitespace) && len(normalized) > 0 && braceDepth == 0 && bracketDepth == 0 {
				normalized = append(normalized, " ")
				inWhitespace = true
			}
			if braceDepth > 0 || bracketDepth > 0 {
				normalized = append(normalized, ch)
			}
			i += 1
		} else if ch == "'" {
			inWhitespace = false
			j = i + 1
			for j < _runeLen(inner) && _runeAt(inner, j) != "'" {
				j += 1
			}
			normalized = append(normalized, _Substring(inner, i, j+1))
			i = j + 1
		} else if ch == "\"" {
			inWhitespace = false
			j = i + 1
			dqContent = []string{"\""}
			dqBraceDepth = 0
			for j < _runeLen(inner) {
				if _runeAt(inner, j) == "\\" && j+1 < _runeLen(inner) {
					if _runeAt(inner, j+1) == "\n" {
						j += 2
					} else {
						dqContent = append(dqContent, _runeAt(inner, j))
						dqContent = append(dqContent, _runeAt(inner, j+1))
						j += 2
					}
				} else if _IsExpansionStart(inner, j, "${") {
					dqContent = append(dqContent, "${")
					dqBraceDepth += 1
					j += 2
				} else if _runeAt(inner, j) == "}" && dqBraceDepth > 0 {
					dqContent = append(dqContent, "}")
					dqBraceDepth -= 1
					j += 1
				} else if _runeAt(inner, j) == "\"" && dqBraceDepth == 0 {
					dqContent = append(dqContent, "\"")
					j += 1
					break
				} else {
					dqContent = append(dqContent, _runeAt(inner, j))
					j += 1
				}
			}
			normalized = append(normalized, strings.Join(dqContent, ""))
			i = j
		} else if ch == "\\" && i+1 < _runeLen(inner) {
			if _runeAt(inner, i+1) == "\n" {
				i += 2
			} else {
				inWhitespace = false
				normalized = append(normalized, _Substring(inner, i, i+2))
				i += 2
			}
		} else if _IsExpansionStart(inner, i, "$((") {
			inWhitespace = false
			j = i + 3
			depth = 1
			for j < _runeLen(inner) && depth > 0 {
				if j+1 < _runeLen(inner) && _runeAt(inner, j) == "(" && _runeAt(inner, j+1) == "(" {
					depth += 1
					j += 2
				} else if j+1 < _runeLen(inner) && _runeAt(inner, j) == ")" && _runeAt(inner, j+1) == ")" {
					depth -= 1
					j += 2
				} else {
					j += 1
				}
			}
			normalized = append(normalized, _Substring(inner, i, j))
			i = j
		} else if _IsExpansionStart(inner, i, "$(") {
			inWhitespace = false
			j = i + 2
			depth = 1
			for j < _runeLen(inner) && depth > 0 {
				if _runeAt(inner, j) == "(" && j > 0 && _runeAt(inner, j-1) == "$" {
					depth += 1
				} else if _runeAt(inner, j) == ")" {
					depth -= 1
				} else if _runeAt(inner, j) == "'" {
					j += 1
					for j < _runeLen(inner) && _runeAt(inner, j) != "'" {
						j += 1
					}
				} else if _runeAt(inner, j) == "\"" {
					j += 1
					for j < _runeLen(inner) {
						if _runeAt(inner, j) == "\\" && j+1 < _runeLen(inner) {
							j += 2
							continue
						}
						if _runeAt(inner, j) == "\"" {
							break
						}
						j += 1
					}
				}
				j += 1
			}
			normalized = append(normalized, _Substring(inner, i, j))
			i = j
		} else if (ch == "<" || ch == ">") && i+1 < _runeLen(inner) && _runeAt(inner, i+1) == "(" {
			inWhitespace = false
			j = i + 2
			depth = 1
			for j < _runeLen(inner) && depth > 0 {
				if _runeAt(inner, j) == "(" {
					depth += 1
				} else if _runeAt(inner, j) == ")" {
					depth -= 1
				} else if _runeAt(inner, j) == "'" {
					j += 1
					for j < _runeLen(inner) && _runeAt(inner, j) != "'" {
						j += 1
					}
				} else if _runeAt(inner, j) == "\"" {
					j += 1
					for j < _runeLen(inner) {
						if _runeAt(inner, j) == "\\" && j+1 < _runeLen(inner) {
							j += 2
							continue
						}
						if _runeAt(inner, j) == "\"" {
							break
						}
						j += 1
					}
				}
				j += 1
			}
			normalized = append(normalized, _Substring(inner, i, j))
			i = j
		} else if _IsExpansionStart(inner, i, "${") {
			inWhitespace = false
			normalized = append(normalized, "${")
			braceDepth += 1
			i += 2
		} else if ch == "{" && braceDepth > 0 {
			normalized = append(normalized, ch)
			braceDepth += 1
			i += 1
		} else if ch == "}" && braceDepth > 0 {
			normalized = append(normalized, ch)
			braceDepth -= 1
			i += 1
		} else if ch == "#" && braceDepth == 0 && inWhitespace {
			for i < _runeLen(inner) && _runeAt(inner, i) != "\n" {
				i += 1
			}
		} else if ch == "[" {
			if inWhitespace || bracketDepth > 0 {
				bracketDepth += 1
			}
			inWhitespace = false
			normalized = append(normalized, ch)
			i += 1
		} else if ch == "]" && bracketDepth > 0 {
			normalized = append(normalized, ch)
			bracketDepth -= 1
			i += 1
		} else {
			inWhitespace = false
			normalized = append(normalized, ch)
			i += 1
		}
	}
	return strings.TrimRight(strings.Join(normalized, ""), " \t\n\r\x0b\x0c")
}

func (w *Word) _StripArithLineContinuations(value string) string {
	var start int
	var depth int
	var arithContent []string
	var firstCloseIdx int
	var numBackslashes int
	var j int
	var content string
	var closing string
	result := []string{}
	i := 0
	for i < _runeLen(value) {
		if _IsExpansionStart(value, i, "$((") {
			start = i
			i += 3
			depth = 2
			arithContent = []string{}
			firstCloseIdx = -1
			for i < _runeLen(value) && depth > 0 {
				if _runeAt(value, i) == "(" {
					arithContent = append(arithContent, "(")
					depth += 1
					i += 1
					if depth > 1 {
						firstCloseIdx = -1
					}
				} else if _runeAt(value, i) == ")" {
					if depth == 2 {
						firstCloseIdx = len(arithContent)
					}
					depth -= 1
					if depth > 0 {
						arithContent = append(arithContent, ")")
					}
					i += 1
				} else if _runeAt(value, i) == "\\" && i+1 < _runeLen(value) && _runeAt(value, i+1) == "\n" {
					numBackslashes = 0
					j = len(arithContent) - 1
					for j >= 0 && arithContent[j] == "\n" {
						j -= 1
					}
					for j >= 0 && arithContent[j] == "\\" {
						numBackslashes += 1
						j -= 1
					}
					if numBackslashes%2 == 1 {
						arithContent = append(arithContent, "\\")
						arithContent = append(arithContent, "\n")
						i += 2
					} else {
						i += 2
					}
					if depth == 1 {
						firstCloseIdx = -1
					}
				} else {
					arithContent = append(arithContent, _runeAt(value, i))
					i += 1
					if depth == 1 {
						firstCloseIdx = -1
					}
				}
			}
			if depth == 0 || depth == 1 && firstCloseIdx != -1 {
				content = strings.Join(arithContent, "")
				if firstCloseIdx != -1 {
					content = _Substring(content, 0, firstCloseIdx)
					closing = _ternary(depth == 0, "))", ")")
					result = append(result, "$(("+content+closing)
				} else {
					result = append(result, "$(("+content+")")
				}
			} else {
				result = append(result, _Substring(value, start, i))
			}
		} else {
			result = append(result, _runeAt(value, i))
			i += 1
		}
	}
	return strings.Join(result, "")
}

func (w *Word) _CollectCmdsubs(node Node) []Node {
	result := []Node{}
	switch n := node.(type) {
	case *CommandSubstitution:
		result = append(result, n)
	}
	return result
}

func (w *Word) _CollectProcsubs(node Node) []Node {
	result := []Node{}
	switch n := node.(type) {
	case *ProcessSubstitution:
		result = append(result, n)
	}
	return result
}

func (w *Word) _FormatCommandSubstitutions(value string, inArith bool) string {
	var hasArith bool
	var hasUntrackedCmdsub bool
	var hasUntrackedProcsub bool
	var i int
	var j int
	var inner string
	var node Node
	var formatted string
	var parser *Parser
	var parsed Node
	var cmdsubNode Node
	var hasPipe bool
	var prefix string
	var origInner string
	var endsWithNewline bool
	var suffix string
	var isProcsub bool
	var direction string
	var compact bool
	var rawContent string
	var leadingWsEnd int
	var leadingWs string
	var stripped string
	var normalizedWs string
	var spaced string
	var rawStripped string
	var finalOutput string
	var depth int
	var terminator string
	var braceQuote *QuoteState
	var c string
	var formattedInner string
	cmdsubParts := []Node{}
	procsubParts := []Node{}
	hasArith = false
	for _, p := range w.Parts {
		if p.Kind() == "cmdsub" {
			cmdsubParts = append(cmdsubParts, p)
		} else if p.Kind() == "procsub" {
			procsubParts = append(procsubParts, p)
		} else if p.Kind() == "arith" {
			hasArith = true
		} else {
			cmdsubParts = append(cmdsubParts, w._CollectCmdsubs(p)...)
			procsubParts = append(procsubParts, w._CollectProcsubs(p)...)
		}
	}
	hasBraceCmdsub := strings.Index(value, "${ ") != -1 || strings.Index(value, "${\t") != -1 || strings.Index(value, "${\n") != -1 || strings.Index(value, "${|") != -1
	hasUntrackedCmdsub = false
	hasUntrackedProcsub = false
	idx := 0
	scanQuote := NewQuoteState()
	for idx < _runeLen(value) {
		if _runeAt(value, idx) == "\"" {
			scanQuote.Double = !(scanQuote.Double)
			idx += 1
		} else if _runeAt(value, idx) == "'" && !(scanQuote.Double) {
			idx += 1
			for idx < _runeLen(value) && _runeAt(value, idx) != "'" {
				idx += 1
			}
			if idx < _runeLen(value) {
				idx += 1
			}
		} else if strings.HasPrefix(value[idx:], "$(") && !(strings.HasPrefix(value[idx:], "$((")) && !(_IsBackslashEscaped(value, idx)) && !(_IsDollarDollarParen(value, idx)) {
			hasUntrackedCmdsub = true
			break
		} else if (strings.HasPrefix(value[idx:], "<(") || strings.HasPrefix(value[idx:], ">(")) && !(scanQuote.Double) {
			if idx == 0 || !(unicode.IsLetter(_runeFromChar(_runeAt(value, idx-1))) || unicode.IsDigit(_runeFromChar(_runeAt(value, idx-1)))) && !strings.Contains("\"'", _runeAt(value, idx-1)) {
				hasUntrackedProcsub = true
				break
			}
			idx += 1
		} else {
			idx += 1
		}
	}
	hasParamWithProcsubPattern := strings.Contains(value, "${") && (strings.Contains(value, "<(") || strings.Contains(value, ">("))
	if !(len(cmdsubParts) > 0) && !(len(procsubParts) > 0) && !(hasBraceCmdsub) && !(hasUntrackedCmdsub) && !(hasUntrackedProcsub) && !(hasParamWithProcsubPattern) {
		return value
	}
	result := []string{}
	i = 0
	cmdsubIdx := 0
	procsubIdx := 0
	mainQuote := NewQuoteState()
	extglobDepth := 0
	deprecatedArithDepth := 0
	arithDepth := 0
	arithParenDepth := 0
	for i < _runeLen(value) {
		if i > 0 && _IsExtglobPrefix(_runeAt(value, i-1)) && _runeAt(value, i) == "(" && !(_IsBackslashEscaped(value, i-1)) {
			extglobDepth += 1
			result = append(result, _runeAt(value, i))
			i += 1
			continue
		}
		if _runeAt(value, i) == ")" && extglobDepth > 0 {
			extglobDepth -= 1
			result = append(result, _runeAt(value, i))
			i += 1
			continue
		}
		if strings.HasPrefix(value[i:], "$[") && !(_IsBackslashEscaped(value, i)) {
			deprecatedArithDepth += 1
			result = append(result, _runeAt(value, i))
			i += 1
			continue
		}
		if _runeAt(value, i) == "]" && deprecatedArithDepth > 0 {
			deprecatedArithDepth -= 1
			result = append(result, _runeAt(value, i))
			i += 1
			continue
		}
		if _IsExpansionStart(value, i, "$((") && !(_IsBackslashEscaped(value, i)) && hasArith {
			arithDepth += 1
			arithParenDepth += 2
			result = append(result, "$((")
			i += 3
			continue
		}
		if arithDepth > 0 && arithParenDepth == 2 && strings.HasPrefix(value[i:], "))") {
			arithDepth -= 1
			arithParenDepth -= 2
			result = append(result, "))")
			i += 2
			continue
		}
		if arithDepth > 0 {
			if _runeAt(value, i) == "(" {
				arithParenDepth += 1
				result = append(result, _runeAt(value, i))
				i += 1
				continue
			} else if _runeAt(value, i) == ")" {
				arithParenDepth -= 1
				result = append(result, _runeAt(value, i))
				i += 1
				continue
			}
		}
		if _IsExpansionStart(value, i, "$((") && !(hasArith) {
			j = _FindCmdsubEnd(value, i+2)
			result = append(result, _Substring(value, i, j))
			if cmdsubIdx < len(cmdsubParts) {
				cmdsubIdx += 1
			}
			i = j
			continue
		}
		if strings.HasPrefix(value[i:], "$(") && !(strings.HasPrefix(value[i:], "$((")) && !(_IsBackslashEscaped(value, i)) && !(_IsDollarDollarParen(value, i)) {
			j = _FindCmdsubEnd(value, i+2)
			if extglobDepth > 0 {
				result = append(result, _Substring(value, i, j))
				if cmdsubIdx < len(cmdsubParts) {
					cmdsubIdx += 1
				}
				i = j
				continue
			}
			inner = _Substring(value, i+2, j-1)
			if cmdsubIdx < len(cmdsubParts) {
				node = cmdsubParts[cmdsubIdx]
				formatted = _FormatCmdsubNode(node.(*CommandSubstitution).Command, 0, false, false, false)
				cmdsubIdx += 1
			} else {
				func() {
					defer func() {
						if r := recover(); r != nil {
							formatted = inner
						}
					}()
					parser = NewParser(inner, false, false)
					parsed = parser.ParseList(true)
					formatted = _ternary(parsed != nil, _FormatCmdsubNode(parsed, 0, false, false, false), "")
				}()
			}
			if strings.HasPrefix(formatted, "(") {
				result = append(result, "$( "+formatted+")")
			} else {
				result = append(result, "$("+formatted+")")
			}
			i = j
		} else if _runeAt(value, i) == "`" && cmdsubIdx < len(cmdsubParts) {
			j = i + 1
			for j < _runeLen(value) {
				if _runeAt(value, j) == "\\" && j+1 < _runeLen(value) {
					j += 2
					continue
				}
				if _runeAt(value, j) == "`" {
					j += 1
					break
				}
				j += 1
			}
			result = append(result, _Substring(value, i, j))
			cmdsubIdx += 1
			i = j
		} else if _IsExpansionStart(value, i, "${") && i+2 < _runeLen(value) && _IsFunsubChar(_runeAt(value, i+2)) && !(_IsBackslashEscaped(value, i)) {
			j = _FindFunsubEnd(value, i+2)
			cmdsubNode = func() Node {
				if cmdsubIdx < len(cmdsubParts) {
					return cmdsubParts[cmdsubIdx]
				}
				return nil
			}()
			if func() bool { t, ok := cmdsubNode.(*CommandSubstitution); return ok && t.Brace }() {
				node = cmdsubNode
				formatted = _FormatCmdsubNode(node.(*CommandSubstitution).Command, 0, false, false, false)
				hasPipe = _runeAt(value, i+2) == "|"
				prefix = _ternary(hasPipe, "${|", "${ ")
				origInner = _Substring(value, i+2, j-1)
				endsWithNewline = strings.HasSuffix(origInner, "\n")
				if !(len(formatted) > 0) || (len(formatted) > 0 && strings.TrimSpace(formatted) == "") {
					suffix = "}"
				} else if strings.HasSuffix(formatted, "&") || strings.HasSuffix(formatted, "& ") {
					suffix = _ternary(strings.HasSuffix(formatted, "&"), " }", "}")
				} else if endsWithNewline {
					suffix = "\n }"
				} else {
					suffix = "; }"
				}
				result = append(result, prefix+formatted+suffix)
				cmdsubIdx += 1
			} else {
				result = append(result, _Substring(value, i, j))
			}
			i = j
		} else if (strings.HasPrefix(value[i:], ">(") || strings.HasPrefix(value[i:], "<(")) && !(mainQuote.Double) && deprecatedArithDepth == 0 && arithDepth == 0 {
			isProcsub = i == 0 || !(unicode.IsLetter(_runeFromChar(_runeAt(value, i-1))) || unicode.IsDigit(_runeFromChar(_runeAt(value, i-1)))) && !strings.Contains("\"'", _runeAt(value, i-1))
			if extglobDepth > 0 {
				j = _FindCmdsubEnd(value, i+2)
				result = append(result, _Substring(value, i, j))
				if procsubIdx < len(procsubParts) {
					procsubIdx += 1
				}
				i = j
				continue
			}
			if procsubIdx < len(procsubParts) {
				direction = _runeAt(value, i)
				j = _FindCmdsubEnd(value, i+2)
				node = procsubParts[procsubIdx]
				compact = _StartsWithSubshell(node.(*ProcessSubstitution).Command)
				formatted = _FormatCmdsubNode(node.(*ProcessSubstitution).Command, 0, true, compact, true)
				rawContent = _Substring(value, i+2, j-1)
				if node.(*ProcessSubstitution).Command.Kind() == "subshell" {
					leadingWsEnd = 0
					for leadingWsEnd < _runeLen(rawContent) && strings.Contains(" \t\n", _runeAt(rawContent, leadingWsEnd)) {
						leadingWsEnd += 1
					}
					leadingWs = _Substring(rawContent, 0, leadingWsEnd)
					stripped = _Substring(rawContent, leadingWsEnd, _runeLen(rawContent))
					if strings.HasPrefix(stripped, "(") {
						if len(leadingWs) > 0 {
							normalizedWs = strings.ReplaceAll(strings.ReplaceAll(leadingWs, "\n", " "), "\t", " ")
							spaced = _FormatCmdsubNode(node.(*ProcessSubstitution).Command, 0, false, false, false)
							result = append(result, direction+"("+normalizedWs+spaced+")")
						} else {
							rawContent = strings.ReplaceAll(rawContent, "\\\n", "")
							result = append(result, direction+"("+rawContent+")")
						}
						procsubIdx += 1
						i = j
						continue
					}
				}
				rawContent = _Substring(value, i+2, j-1)
				rawStripped = strings.ReplaceAll(rawContent, "\\\n", "")
				if _StartsWithSubshell(node.(*ProcessSubstitution).Command) && formatted != rawStripped {
					result = append(result, direction+"("+rawStripped+")")
				} else {
					finalOutput = direction + "(" + formatted + ")"
					result = append(result, finalOutput)
				}
				procsubIdx += 1
				i = j
			} else if isProcsub && len(w.Parts) > 0 {
				direction = _runeAt(value, i)
				j = _FindCmdsubEnd(value, i+2)
				if j > _runeLen(value) || j > 0 && j <= _runeLen(value) && _runeAt(value, j-1) != ")" {
					result = append(result, _runeAt(value, i))
					i += 1
					continue
				}
				inner = _Substring(value, i+2, j-1)
				func() {
					defer func() {
						if r := recover(); r != nil {
							formatted = inner
						}
					}()
					parser = NewParser(inner, false, false)
					parsed = parser.ParseList(true)
					if parsed != nil && parser.Pos == _runeLen(inner) && !strings.Contains(inner, "\n") {
						compact = _StartsWithSubshell(parsed)
						formatted = _FormatCmdsubNode(parsed, 0, true, compact, true)
					} else {
						formatted = inner
					}
				}()
				result = append(result, direction+"("+formatted+")")
				i = j
			} else if isProcsub {
				direction = _runeAt(value, i)
				j = _FindCmdsubEnd(value, i+2)
				if j > _runeLen(value) || j > 0 && j <= _runeLen(value) && _runeAt(value, j-1) != ")" {
					result = append(result, _runeAt(value, i))
					i += 1
					continue
				}
				inner = _Substring(value, i+2, j-1)
				if inArith {
					result = append(result, direction+"("+inner+")")
				} else if strings.TrimSpace(inner) != "" {
					stripped = strings.TrimLeft(inner, " \t")
					result = append(result, direction+"("+stripped+")")
				} else {
					result = append(result, direction+"("+inner+")")
				}
				i = j
			} else {
				result = append(result, _runeAt(value, i))
				i += 1
			}
		} else if (_IsExpansionStart(value, i, "${ ") || _IsExpansionStart(value, i, "${\t") || _IsExpansionStart(value, i, "${\n") || _IsExpansionStart(value, i, "${|")) && !(_IsBackslashEscaped(value, i)) {
			prefix = strings.ReplaceAll(strings.ReplaceAll(_Substring(value, i, i+3), "\t", " "), "\n", " ")
			j = i + 3
			depth = 1
			for j < _runeLen(value) && depth > 0 {
				if _runeAt(value, j) == "{" {
					depth += 1
				} else if _runeAt(value, j) == "}" {
					depth -= 1
				}
				j += 1
			}
			inner = _Substring(value, i+2, j-1)
			if strings.TrimSpace(inner) == "" {
				result = append(result, "${ }")
			} else {
				func() {
					defer func() {
						if r := recover(); r != nil {
							result = append(result, _Substring(value, i, j))
						}
					}()
					parser = NewParser(strings.TrimLeft(inner, " \t\n|"), false, false)
					parsed = parser.ParseList(true)
					if parsed != nil {
						formatted = _FormatCmdsubNode(parsed, 0, false, false, false)
						formatted = strings.TrimRight(formatted, ";")
						if strings.HasSuffix(strings.TrimRight(inner, " \t"), "\n") {
							terminator = "\n }"
						} else if strings.HasSuffix(formatted, " &") {
							terminator = " }"
						} else {
							terminator = "; }"
						}
						result = append(result, prefix+formatted+terminator)
					} else {
						result = append(result, "${ }")
					}
				}()
			}
			i = j
		} else if _IsExpansionStart(value, i, "${") && !(_IsBackslashEscaped(value, i)) {
			j = i + 2
			depth = 1
			braceQuote = NewQuoteState()
			for j < _runeLen(value) && depth > 0 {
				c = _runeAt(value, j)
				if c == "\\" && j+1 < _runeLen(value) && !(braceQuote.Single) {
					j += 2
					continue
				}
				if c == "'" && !(braceQuote.Double) {
					braceQuote.Single = !(braceQuote.Single)
				} else if c == "\"" && !(braceQuote.Single) {
					braceQuote.Double = !(braceQuote.Double)
				} else if !(braceQuote.InQuotes()) {
					if _IsExpansionStart(value, j, "$(") && !(strings.HasPrefix(value[j:], "$((")) {
						j = _FindCmdsubEnd(value, j+2)
						continue
					}
					if c == "{" {
						depth += 1
					} else if c == "}" {
						depth -= 1
					}
				}
				j += 1
			}
			if depth > 0 {
				inner = _Substring(value, i+2, j)
			} else {
				inner = _Substring(value, i+2, j-1)
			}
			formattedInner = w._FormatCommandSubstitutions(inner, false)
			formattedInner = w._NormalizeExtglobWhitespace(formattedInner)
			if depth == 0 {
				result = append(result, "${"+formattedInner+"}")
			} else {
				result = append(result, "${"+formattedInner)
			}
			i = j
		} else if _runeAt(value, i) == "\"" {
			mainQuote.Double = !(mainQuote.Double)
			result = append(result, _runeAt(value, i))
			i += 1
		} else if _runeAt(value, i) == "'" && !(mainQuote.Double) {
			j = i + 1
			for j < _runeLen(value) && _runeAt(value, j) != "'" {
				j += 1
			}
			if j < _runeLen(value) {
				j += 1
			}
			result = append(result, _Substring(value, i, j))
			i = j
		} else {
			result = append(result, _runeAt(value, i))
			i += 1
		}
	}
	return strings.Join(result, "")
}

func (w *Word) _NormalizeExtglobWhitespace(value string) string {
	var prefixChar string
	var depth int
	var patternParts []string
	var currentPart []string
	var hasPipe bool
	var partContent string
	result := []string{}
	i := 0
	extglobQuote := NewQuoteState()
	deprecatedArithDepth := 0
	for i < _runeLen(value) {
		if _runeAt(value, i) == "\"" {
			extglobQuote.Double = !(extglobQuote.Double)
			result = append(result, _runeAt(value, i))
			i += 1
			continue
		}
		if strings.HasPrefix(value[i:], "$[") && !(_IsBackslashEscaped(value, i)) {
			deprecatedArithDepth += 1
			result = append(result, _runeAt(value, i))
			i += 1
			continue
		}
		if _runeAt(value, i) == "]" && deprecatedArithDepth > 0 {
			deprecatedArithDepth -= 1
			result = append(result, _runeAt(value, i))
			i += 1
			continue
		}
		if i+1 < _runeLen(value) && _runeAt(value, i+1) == "(" {
			prefixChar = _runeAt(value, i)
			if strings.Contains("><", prefixChar) && !(extglobQuote.Double) && deprecatedArithDepth == 0 {
				result = append(result, prefixChar)
				result = append(result, "(")
				i += 2
				depth = 1
				patternParts = []string{}
				currentPart = []string{}
				hasPipe = false
				for i < _runeLen(value) && depth > 0 {
					if _runeAt(value, i) == "\\" && i+1 < _runeLen(value) {
						currentPart = append(currentPart, _Substring(value, i, i+2))
						i += 2
						continue
					} else if _runeAt(value, i) == "(" {
						depth += 1
						currentPart = append(currentPart, _runeAt(value, i))
						i += 1
					} else if _runeAt(value, i) == ")" {
						depth -= 1
						if depth == 0 {
							partContent = strings.Join(currentPart, "")
							if strings.Contains(partContent, "<<") {
								patternParts = append(patternParts, partContent)
							} else if hasPipe {
								patternParts = append(patternParts, strings.TrimSpace(partContent))
							} else {
								patternParts = append(patternParts, partContent)
							}
							break
						}
						currentPart = append(currentPart, _runeAt(value, i))
						i += 1
					} else if _runeAt(value, i) == "|" && depth == 1 {
						if i+1 < _runeLen(value) && _runeAt(value, i+1) == "|" {
							currentPart = append(currentPart, "||")
							i += 2
						} else {
							hasPipe = true
							partContent = strings.Join(currentPart, "")
							if strings.Contains(partContent, "<<") {
								patternParts = append(patternParts, partContent)
							} else {
								patternParts = append(patternParts, strings.TrimSpace(partContent))
							}
							currentPart = []string{}
							i += 1
						}
					} else {
						currentPart = append(currentPart, _runeAt(value, i))
						i += 1
					}
				}
				result = append(result, strings.Join(patternParts, " | "))
				if depth == 0 {
					result = append(result, ")")
					i += 1
				}
				continue
			}
		}
		result = append(result, _runeAt(value, i))
		i += 1
	}
	return strings.Join(result, "")
}

func (w *Word) GetCondFormattedValue() string {
	value := w._ExpandAllAnsiCQuotes(w.Value)
	value = w._StripLocaleStringDollars(value)
	value = w._FormatCommandSubstitutions(value, false)
	value = w._NormalizeExtglobWhitespace(value)
	value = strings.ReplaceAll(value, "\x01", "\x01\x01")
	return strings.TrimRight(value, "\n")
}

func NewCommand(words []Node, redirects []Node) *Command {
	c := &Command{}
	c.kind = "command"
	c.Words = words
	if redirects == nil {
		redirects = []Node{}
	}
	c.Redirects = redirects
	return c
}

func (c *Command) ToSexp() string {
	parts := []string{}
	for _, w := range c.Words {
		parts = append(parts, w.ToSexp())
	}
	for _, r := range c.Redirects {
		parts = append(parts, r.ToSexp())
	}
	inner := strings.Join(parts, " ")
	if !(len(inner) > 0) {
		return "(command)"
	}
	return "(command " + inner + ")"
}

func NewPipeline(commands []Node) *Pipeline {
	p := &Pipeline{}
	p.kind = "pipeline"
	p.Commands = commands
	return p
}

func (p *Pipeline) ToSexp() string {
	var cmd Node
	var needsRedirect bool
	var pair interface{}
	var needs bool
	var result string
	if len(p.Commands) == 1 {
		return p.Commands[0].ToSexp()
	}
	cmds := []interface{}{}
	i := 0
	for i < len(p.Commands) {
		cmd = p.Commands[i]
		if cmd.Kind() == "pipe-both" {
			i += 1
			continue
		}
		needsRedirect = i+1 < len(p.Commands) && p.Commands[i+1].Kind() == "pipe-both"
		cmds = append(cmds, []interface{}{cmd, needsRedirect})
		i += 1
	}
	if len(cmds) == 1 {
		pair = cmds[0]
		cmd = pair.([]interface{})[0].(Node)
		needs = pair.([]interface{})[1].(bool)
		return p._CmdSexp(cmd, needs)
	}
	lastPair := cmds[len(cmds)-1]
	lastCmd := lastPair.([]interface{})[0].(Node)
	lastNeeds := lastPair.([]interface{})[1].(bool)
	result = p._CmdSexp(lastCmd, lastNeeds)
	j := len(cmds) - 2
	for j >= 0 {
		pair = cmds[j]
		cmd = pair.([]interface{})[0].(Node)
		needs = pair.([]interface{})[1].(bool)
		if needs && cmd.Kind() != "command" {
			result = "(pipe " + cmd.ToSexp() + " (redirect \">&\" 1) " + result + ")"
		} else {
			result = "(pipe " + p._CmdSexp(cmd, needs) + " " + result + ")"
		}
		j -= 1
	}
	return result
}

func (p *Pipeline) _CmdSexp(cmd Node, needsRedirect bool) string {
	var parts []string
	if !(needsRedirect) {
		return cmd.ToSexp()
	}
	if c, ok := cmd.(*Command); ok {
		parts = []string{}
		for _, w := range c.Words {
			parts = append(parts, w.ToSexp())
		}
		for _, r := range c.Redirects {
			parts = append(parts, r.ToSexp())
		}
		parts = append(parts, "(redirect \">&\" 1)")
		return "(command " + strings.Join(parts, " ") + ")"
	}
	return cmd.ToSexp()
}

func NewList(parts []Node) *List {
	l := &List{}
	l.kind = "list"
	l.Parts = parts
	return l
}

func (l *List) ToSexp() string {
	var parts []Node
	var left []Node
	var right []Node
	var leftSexp string
	var rightSexp string
	var innerParts []Node
	var innerList Node
	parts = append([]Node{}, l.Parts...)
	opNames := map[string]string{"&&": "and", "||": "or", ";": "semi", "\n": "semi", "&": "background"}
	for len(parts) > 1 && parts[len(parts)-1].Kind() == "operator" && (parts[len(parts)-1].(*Operator).Op == ";" || parts[len(parts)-1].(*Operator).Op == "\n") {
		parts = parts[0 : len(parts)-1]
	}
	if len(parts) == 1 {
		return parts[0].ToSexp()
	}
	if parts[len(parts)-1].Kind() == "operator" && parts[len(parts)-1].(*Operator).Op == "&" {
		for i := len(parts) - 3; i > 0; i += -2 {
			if parts[i].Kind() == "operator" && (parts[i].(*Operator).Op == ";" || parts[i].(*Operator).Op == "\n") {
				left = parts[0:i]
				right = parts[i+1 : len(parts)-1]
				if len(left) > 1 {
					leftSexp = NewList(left).ToSexp()
				} else {
					leftSexp = left[0].ToSexp()
				}
				if len(right) > 1 {
					rightSexp = NewList(right).ToSexp()
				} else {
					rightSexp = right[0].ToSexp()
				}
				return "(semi " + leftSexp + " (background " + rightSexp + "))"
			}
		}
		innerParts = parts[0 : len(parts)-1]
		if len(innerParts) == 1 {
			return "(background " + innerParts[0].ToSexp() + ")"
		}
		innerList = NewList(innerParts)
		return "(background " + innerList.ToSexp() + ")"
	}
	return l._ToSexpWithPrecedence(parts, opNames)
}

func (l *List) _ToSexpWithPrecedence(parts []Node, opNames map[string]string) string {
	var segments [][]Node
	var start int
	var seg []Node
	var result string
	semiPositions := []int{}
	for i := 0; i < len(parts); i++ {
		if parts[i].Kind() == "operator" && (parts[i].(*Operator).Op == ";" || parts[i].(*Operator).Op == "\n") {
			semiPositions = append(semiPositions, i)
		}
	}
	if len(semiPositions) > 0 {
		segments = [][]Node{}
		start = 0
		for _, pos := range semiPositions {
			seg = parts[start:pos]
			if len(seg) > 0 && seg[0].Kind() != "operator" {
				segments = append(segments, seg)
			}
			start = pos + 1
		}
		seg = parts[start:len(parts)]
		if len(seg) > 0 && seg[0].Kind() != "operator" {
			segments = append(segments, seg)
		}
		if !(len(segments) > 0) {
			return "()"
		}
		result = l._ToSexpAmpAndHigher(segments[0], opNames)
		for i := 1; i < len(segments); i++ {
			result = "(semi " + result + " " + l._ToSexpAmpAndHigher(segments[i], opNames) + ")"
		}
		return result
	}
	return l._ToSexpAmpAndHigher(parts, opNames)
}

func (l *List) _ToSexpAmpAndHigher(parts []Node, opNames map[string]string) string {
	var segments [][]Node
	var start int
	var result string
	if len(parts) == 1 {
		return parts[0].ToSexp()
	}
	ampPositions := []int{}
	for i := 1; i < len(parts)-1; i += 2 {
		if parts[i].Kind() == "operator" && parts[i].(*Operator).Op == "&" {
			ampPositions = append(ampPositions, i)
		}
	}
	if len(ampPositions) > 0 {
		segments = [][]Node{}
		start = 0
		for _, pos := range ampPositions {
			segments = append(segments, parts[start:pos])
			start = pos + 1
		}
		segments = append(segments, parts[start:len(parts)])
		result = l._ToSexpAndOr(segments[0], opNames)
		for i := 1; i < len(segments); i++ {
			result = "(background " + result + " " + l._ToSexpAndOr(segments[i], opNames) + ")"
		}
		return result
	}
	return l._ToSexpAndOr(parts, opNames)
}

func (l *List) _ToSexpAndOr(parts []Node, opNames map[string]string) string {
	var result string
	var op Node
	var cmd Node
	var opName string
	if len(parts) == 1 {
		return parts[0].ToSexp()
	}
	result = parts[0].ToSexp()
	for i := 1; i < len(parts)-1; i += 2 {
		op = parts[i]
		cmd = parts[i+1]
		opName = _mapGet(opNames, op.(*Operator).Op, op.(*Operator).Op)
		result = "(" + opName + " " + result + " " + cmd.ToSexp() + ")"
	}
	return result
}

func NewOperator(op string) *Operator {
	o := &Operator{}
	o.kind = "operator"
	o.Op = op
	return o
}

func (o *Operator) ToSexp() string {
	names := map[string]string{"&&": "and", "||": "or", ";": "semi", "&": "bg", "|": "pipe"}
	return "(" + _mapGet(names, o.Op, o.Op) + ")"
}

func NewPipeBoth() *PipeBoth {
	p := &PipeBoth{}
	p.kind = "pipe-both"
	return p
}

func (p *PipeBoth) ToSexp() string {
	return "(pipe-both)"
}

func NewEmpty() *Empty {
	e := &Empty{}
	e.kind = "empty"
	return e
}

func (e *Empty) ToSexp() string {
	return ""
}

func NewComment(text string) *Comment {
	c := &Comment{}
	c.kind = "comment"
	c.Text = text
	return c
}

func (c *Comment) ToSexp() string {
	return ""
}

func NewRedirect(op string, target Node, fd int) *Redirect {
	r := &Redirect{}
	r.kind = "redirect"
	r.Op = op
	r.Target = target
	r.Fd = fd
	return r
}

func (r *Redirect) ToSexp() string {
	var op string
	var j int
	var targetVal string
	var raw string
	var fdTarget string
	var outVal string
	op = strings.TrimLeft(r.Op, "0123456789")
	if strings.HasPrefix(op, "{") {
		j = 1
		if j < _runeLen(op) && (unicode.IsLetter(_runeFromChar(_runeAt(op, j))) || _runeAt(op, j) == "_") {
			j += 1
			for j < _runeLen(op) && ((unicode.IsLetter(_runeFromChar(_runeAt(op, j))) || unicode.IsDigit(_runeFromChar(_runeAt(op, j)))) || _runeAt(op, j) == "_") {
				j += 1
			}
			if j < _runeLen(op) && _runeAt(op, j) == "[" {
				j += 1
				for j < _runeLen(op) && _runeAt(op, j) != "]" {
					j += 1
				}
				if j < _runeLen(op) && _runeAt(op, j) == "]" {
					j += 1
				}
			}
			if j < _runeLen(op) && _runeAt(op, j) == "}" {
				op = _Substring(op, j+1, _runeLen(op))
			}
		}
	}
	targetVal = r.Target.(*Word).Value
	targetVal = r.Target.(*Word)._ExpandAllAnsiCQuotes(targetVal)
	targetVal = r.Target.(*Word)._StripLocaleStringDollars(targetVal)
	targetVal = r.Target.(*Word)._FormatCommandSubstitutions(targetVal, false)
	targetVal = r.Target.(*Word)._StripArithLineContinuations(targetVal)
	if strings.HasSuffix(targetVal, "\\") && !(strings.HasSuffix(targetVal, "\\\\")) {
		targetVal = targetVal + "\\"
	}
	if strings.HasPrefix(targetVal, "&") {
		if op == ">" {
			op = ">&"
		} else if op == "<" {
			op = "<&"
		}
		raw = _Substring(targetVal, 1, _runeLen(targetVal))
		if _strIsDigits(raw) && _mustAtoi(raw) <= 2147483647 {
			return "(redirect \"" + op + "\" " + fmt.Sprint(_mustAtoi(raw)) + ")"
		}
		if strings.HasSuffix(raw, "-") && _strIsDigits(_Substring(raw, 0, _runeLen(raw)-1)) && _mustAtoi(_Substring(raw, 0, _runeLen(raw)-1)) <= 2147483647 {
			return "(redirect \"" + op + "\" " + fmt.Sprint(_mustAtoi(_Substring(raw, 0, _runeLen(raw)-1))) + ")"
		}
		if targetVal == "&-" {
			return "(redirect \">&-\" 0)"
		}
		fdTarget = _ternary(strings.HasSuffix(raw, "-"), _Substring(raw, 0, _runeLen(raw)-1), raw)
		return "(redirect \"" + op + "\" \"" + fdTarget + "\")"
	}
	if op == ">&" || op == "<&" {
		if _strIsDigits(targetVal) && _mustAtoi(targetVal) <= 2147483647 {
			return "(redirect \"" + op + "\" " + fmt.Sprint(_mustAtoi(targetVal)) + ")"
		}
		if targetVal == "-" {
			return "(redirect \">&-\" 0)"
		}
		if strings.HasSuffix(targetVal, "-") && _strIsDigits(_Substring(targetVal, 0, _runeLen(targetVal)-1)) && _mustAtoi(_Substring(targetVal, 0, _runeLen(targetVal)-1)) <= 2147483647 {
			return "(redirect \"" + op + "\" " + fmt.Sprint(_mustAtoi(_Substring(targetVal, 0, _runeLen(targetVal)-1))) + ")"
		}
		outVal = _ternary(strings.HasSuffix(targetVal, "-"), _Substring(targetVal, 0, _runeLen(targetVal)-1), targetVal)
		return "(redirect \"" + op + "\" \"" + outVal + "\")"
	}
	return "(redirect \"" + op + "\" \"" + targetVal + "\")"
}

func NewHereDoc(delimiter string, content string, stripTabs bool, quoted bool, fd int, complete bool) *HereDoc {
	h := &HereDoc{}
	h.kind = "heredoc"
	h.Delimiter = delimiter
	h.Content = content
	h.Strip_tabs = stripTabs
	h.Quoted = quoted
	h.Fd = fd
	h.Complete = complete
	h._Start_pos = -1
	return h
}

func (h *HereDoc) ToSexp() string {
	var content string
	op := _ternary(h.Strip_tabs, "<<-", "<<")
	content = h.Content
	if strings.HasSuffix(content, "\\") && !(strings.HasSuffix(content, "\\\\")) {
		content = content + "\\"
	}
	return fmt.Sprintf("(redirect \"%v\" \"%v\")", op, content)
}

func NewSubshell(body Node, redirects []Node) *Subshell {
	s := &Subshell{}
	s.kind = "subshell"
	s.Body = body
	s.Redirects = redirects
	return s
}

func (s *Subshell) ToSexp() string {
	base := "(subshell " + s.Body.ToSexp() + ")"
	return _AppendRedirects(base, s.Redirects)
}

func NewBraceGroup(body Node, redirects []Node) *BraceGroup {
	b := &BraceGroup{}
	b.kind = "brace-group"
	b.Body = body
	b.Redirects = redirects
	return b
}

func (b *BraceGroup) ToSexp() string {
	base := "(brace-group " + b.Body.ToSexp() + ")"
	return _AppendRedirects(base, b.Redirects)
}

func NewIf(condition Node, thenBody Node, elseBody Node, redirects []Node) *If {
	i := &If{}
	i.kind = "if"
	i.Condition = condition
	i.Then_body = thenBody
	i.Else_body = elseBody
	if redirects == nil {
		redirects = []Node{}
	}
	i.Redirects = redirects
	return i
}

func (i *If) ToSexp() string {
	var result string
	result = "(if " + i.Condition.ToSexp() + " " + i.Then_body.ToSexp()
	if i.Else_body != nil {
		result = result + " " + i.Else_body.ToSexp()
	}
	result = result + ")"
	for _, r := range i.Redirects {
		result = result + " " + r.ToSexp()
	}
	return result
}

func NewWhile(condition Node, body Node, redirects []Node) *While {
	w := &While{}
	w.kind = "while"
	w.Condition = condition
	w.Body = body
	if redirects == nil {
		redirects = []Node{}
	}
	w.Redirects = redirects
	return w
}

func (w *While) ToSexp() string {
	base := "(while " + w.Condition.ToSexp() + " " + w.Body.ToSexp() + ")"
	return _AppendRedirects(base, w.Redirects)
}

func NewUntil(condition Node, body Node, redirects []Node) *Until {
	u := &Until{}
	u.kind = "until"
	u.Condition = condition
	u.Body = body
	if redirects == nil {
		redirects = []Node{}
	}
	u.Redirects = redirects
	return u
}

func (u *Until) ToSexp() string {
	base := "(until " + u.Condition.ToSexp() + " " + u.Body.ToSexp() + ")"
	return _AppendRedirects(base, u.Redirects)
}

func NewFor(variable string, words []Node, body Node, redirects []Node) *For {
	f := &For{}
	f.kind = "for"
	f.Var = variable
	f.Words = words
	f.Body = body
	if redirects == nil {
		redirects = []Node{}
	}
	f.Redirects = redirects
	return f
}

func (f *For) ToSexp() string {
	var suffix string
	var redirectParts []string
	var wordParts []string
	var wordStrs string
	suffix = ""
	if len(f.Redirects) > 0 {
		redirectParts = []string{}
		for _, r := range f.Redirects {
			redirectParts = append(redirectParts, r.ToSexp())
		}
		suffix = " " + strings.Join(redirectParts, " ")
	}
	tempWord := NewWord(f.Var, []Node{})
	varFormatted := tempWord._FormatCommandSubstitutions(f.Var, false)
	varEscaped := strings.ReplaceAll(strings.ReplaceAll(varFormatted, "\\", "\\\\"), "\"", "\\\"")
	if f.Words == nil {
		return "(for (word \"" + varEscaped + "\") (in (word \"\\\"$@\\\"\")) " + f.Body.ToSexp() + ")" + suffix
	} else if len(f.Words) == 0 {
		return "(for (word \"" + varEscaped + "\") (in) " + f.Body.ToSexp() + ")" + suffix
	} else {
		wordParts = []string{}
		for _, w := range f.Words {
			wordParts = append(wordParts, w.ToSexp())
		}
		wordStrs = strings.Join(wordParts, " ")
		return "(for (word \"" + varEscaped + "\") (in " + wordStrs + ") " + f.Body.ToSexp() + ")" + suffix
	}
}

func NewForArith(init string, cond string, incr string, body Node, redirects []Node) *ForArith {
	f := &ForArith{}
	f.kind = "for-arith"
	f.Init = init
	f.Cond = cond
	f.Incr = incr
	f.Body = body
	if redirects == nil {
		redirects = []Node{}
	}
	f.Redirects = redirects
	return f
}

func (f *ForArith) ToSexp() string {
	var suffix string
	var redirectParts []string
	suffix = ""
	if len(f.Redirects) > 0 {
		redirectParts = []string{}
		for _, r := range f.Redirects {
			redirectParts = append(redirectParts, r.ToSexp())
		}
		suffix = " " + strings.Join(redirectParts, " ")
	}
	initVal := _ternary(f.Init != "", f.Init, "1")
	condVal := _ternary(f.Cond != "", f.Cond, "1")
	incrVal := _ternary(f.Incr != "", f.Incr, "1")
	initStr := _FormatArithVal(initVal)
	condStr := _FormatArithVal(condVal)
	incrStr := _FormatArithVal(incrVal)
	bodyStr := f.Body.ToSexp()
	return fmt.Sprintf("(arith-for (init (word \"%v\")) (test (word \"%v\")) (step (word \"%v\")) %v)%v", initStr, condStr, incrStr, bodyStr, suffix)
}

func NewSelect(variable string, words []Node, body Node, redirects []Node) *Select {
	s := &Select{}
	s.kind = "select"
	s.Var = variable
	s.Words = words
	s.Body = body
	if redirects == nil {
		redirects = []Node{}
	}
	s.Redirects = redirects
	return s
}

func (s *Select) ToSexp() string {
	var suffix string
	var redirectParts []string
	var wordParts []string
	var wordStrs string
	var inClause string
	suffix = ""
	if len(s.Redirects) > 0 {
		redirectParts = []string{}
		for _, r := range s.Redirects {
			redirectParts = append(redirectParts, r.ToSexp())
		}
		suffix = " " + strings.Join(redirectParts, " ")
	}
	varEscaped := strings.ReplaceAll(strings.ReplaceAll(s.Var, "\\", "\\\\"), "\"", "\\\"")
	if s.Words != nil {
		wordParts = []string{}
		for _, w := range s.Words {
			wordParts = append(wordParts, w.ToSexp())
		}
		wordStrs = strings.Join(wordParts, " ")
		if len(s.Words) > 0 {
			inClause = "(in " + wordStrs + ")"
		} else {
			inClause = "(in)"
		}
	} else {
		inClause = "(in (word \"\\\"$@\\\"\"))"
	}
	return "(select (word \"" + varEscaped + "\") " + inClause + " " + s.Body.ToSexp() + ")" + suffix
}

func NewCase(word Node, patterns []Node, redirects []Node) *Case {
	c := &Case{}
	c.kind = "case"
	c.Word = word
	c.Patterns = patterns
	if redirects == nil {
		redirects = []Node{}
	}
	c.Redirects = redirects
	return c
}

func (c *Case) ToSexp() string {
	parts := []string{}
	parts = append(parts, "(case "+c.Word.ToSexp())
	for _, p := range c.Patterns {
		parts = append(parts, p.ToSexp())
	}
	base := strings.Join(parts, " ") + ")"
	return _AppendRedirects(base, c.Redirects)
}

func NewCasePattern(pattern string, body Node, terminator string) *CasePattern {
	c := &CasePattern{}
	c.kind = "pattern"
	c.Pattern = pattern
	c.Body = body
	c.Terminator = terminator
	return c
}

func (c *CasePattern) ToSexp() string {
	var current []string
	var i int
	var ch string
	var result0 int
	var result1 []string
	alternatives := []string{}
	current = []string{}
	i = 0
	depth := 0
	for i < _runeLen(c.Pattern) {
		ch = _runeAt(c.Pattern, i)
		if ch == "\\" && i+1 < _runeLen(c.Pattern) {
			current = append(current, _Substring(c.Pattern, i, i+2))
			i += 2
		} else if (ch == "@" || ch == "?" || ch == "*" || ch == "+" || ch == "!") && i+1 < _runeLen(c.Pattern) && _runeAt(c.Pattern, i+1) == "(" {
			current = append(current, ch)
			current = append(current, "(")
			depth += 1
			i += 2
		} else if _IsExpansionStart(c.Pattern, i, "$(") {
			current = append(current, ch)
			current = append(current, "(")
			depth += 1
			i += 2
		} else if ch == "(" && depth > 0 {
			current = append(current, ch)
			depth += 1
			i += 1
		} else if ch == ")" && depth > 0 {
			current = append(current, ch)
			depth -= 1
			i += 1
		} else if ch == "[" {
			result0, result1, _ = _ConsumeBracketClass(c.Pattern, i, depth)
			i = result0
			current = append(current, result1...)
		} else if ch == "'" && depth == 0 {
			result0, result1 = _ConsumeSingleQuote(c.Pattern, i)
			i = result0
			current = append(current, result1...)
		} else if ch == "\"" && depth == 0 {
			result0, result1 = _ConsumeDoubleQuote(c.Pattern, i)
			i = result0
			current = append(current, result1...)
		} else if ch == "|" && depth == 0 {
			alternatives = append(alternatives, strings.Join(current, ""))
			current = []string{}
			i += 1
		} else {
			current = append(current, ch)
			i += 1
		}
	}
	alternatives = append(alternatives, strings.Join(current, ""))
	wordList := []string{}
	for _, alt := range alternatives {
		wordList = append(wordList, NewWord(alt, nil).ToSexp())
	}
	patternStr := strings.Join(wordList, " ")
	parts := []string{"(pattern (" + patternStr + ")"}
	if c.Body != nil {
		parts = append(parts, " "+c.Body.ToSexp())
	} else {
		parts = append(parts, " ()")
	}
	parts = append(parts, ")")
	return strings.Join(parts, "")
}

func NewFunction(name string, body Node) *Function {
	f := &Function{}
	f.kind = "function"
	f.Name = name
	f.Body = body
	return f
}

func (f *Function) ToSexp() string {
	return "(function \"" + f.Name + "\" " + f.Body.ToSexp() + ")"
}

func NewParamExpansion(param string, op string, arg string) *ParamExpansion {
	p := &ParamExpansion{}
	p.kind = "param"
	p.Param = param
	p.Op = op
	p.Arg = arg
	return p
}

func (p *ParamExpansion) ToSexp() string {
	var escapedOp string
	var argVal string
	var escapedArg string
	escapedParam := strings.ReplaceAll(strings.ReplaceAll(p.Param, "\\", "\\\\"), "\"", "\\\"")
	if p.Op != "" {
		escapedOp = strings.ReplaceAll(strings.ReplaceAll(p.Op, "\\", "\\\\"), "\"", "\\\"")
		if p.Arg != "" {
			argVal = p.Arg
		} else {
			argVal = ""
		}
		escapedArg = strings.ReplaceAll(strings.ReplaceAll(argVal, "\\", "\\\\"), "\"", "\\\"")
		return "(param \"" + escapedParam + "\" \"" + escapedOp + "\" \"" + escapedArg + "\")"
	}
	return "(param \"" + escapedParam + "\")"
}

func NewParamLength(param string) *ParamLength {
	p := &ParamLength{}
	p.kind = "param-len"
	p.Param = param
	return p
}

func (p *ParamLength) ToSexp() string {
	escaped := strings.ReplaceAll(strings.ReplaceAll(p.Param, "\\", "\\\\"), "\"", "\\\"")
	return "(param-len \"" + escaped + "\")"
}

func NewParamIndirect(param string, op string, arg string) *ParamIndirect {
	p := &ParamIndirect{}
	p.kind = "param-indirect"
	p.Param = param
	p.Op = op
	p.Arg = arg
	return p
}

func (p *ParamIndirect) ToSexp() string {
	var escapedOp string
	var argVal string
	var escapedArg string
	escaped := strings.ReplaceAll(strings.ReplaceAll(p.Param, "\\", "\\\\"), "\"", "\\\"")
	if p.Op != "" {
		escapedOp = strings.ReplaceAll(strings.ReplaceAll(p.Op, "\\", "\\\\"), "\"", "\\\"")
		if p.Arg != "" {
			argVal = p.Arg
		} else {
			argVal = ""
		}
		escapedArg = strings.ReplaceAll(strings.ReplaceAll(argVal, "\\", "\\\\"), "\"", "\\\"")
		return "(param-indirect \"" + escaped + "\" \"" + escapedOp + "\" \"" + escapedArg + "\")"
	}
	return "(param-indirect \"" + escaped + "\")"
}

func NewCommandSubstitution(command Node, brace bool) *CommandSubstitution {
	c := &CommandSubstitution{}
	c.kind = "cmdsub"
	c.Command = command
	c.Brace = brace
	return c
}

func (c *CommandSubstitution) ToSexp() string {
	if c.Brace {
		return "(funsub " + c.Command.ToSexp() + ")"
	}
	return "(cmdsub " + c.Command.ToSexp() + ")"
}

func NewArithmeticExpansion(expression Node) *ArithmeticExpansion {
	a := &ArithmeticExpansion{}
	a.kind = "arith"
	a.Expression = expression
	return a
}

func (a *ArithmeticExpansion) ToSexp() string {
	if _isNilNode(a.Expression) {
		return "(arith)"
	}
	return "(arith " + a.Expression.ToSexp() + ")"
}

func NewArithmeticCommand(expression Node, redirects []Node, rawContent string) *ArithmeticCommand {
	a := &ArithmeticCommand{}
	a.kind = "arith-cmd"
	a.Expression = expression
	if redirects == nil {
		redirects = []Node{}
	}
	a.Redirects = redirects
	a.Raw_content = rawContent
	return a
}

func (a *ArithmeticCommand) ToSexp() string {
	var redirectParts []string
	var redirectSexps string
	formatted := NewWord(a.Raw_content, nil)._FormatCommandSubstitutions(a.Raw_content, true)
	escaped := strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(formatted, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n"), "\t", "\\t")
	result := "(arith (word \"" + escaped + "\"))"
	if len(a.Redirects) > 0 {
		redirectParts = []string{}
		for _, r := range a.Redirects {
			redirectParts = append(redirectParts, r.ToSexp())
		}
		redirectSexps = strings.Join(redirectParts, " ")
		return result + " " + redirectSexps
	}
	return result
}

func NewArithNumber(value string) *ArithNumber {
	a := &ArithNumber{}
	a.kind = "number"
	a.Value = value
	return a
}

func (a *ArithNumber) ToSexp() string {
	return "(number \"" + a.Value + "\")"
}

func NewArithEmpty() *ArithEmpty {
	a := &ArithEmpty{}
	a.kind = "empty"
	return a
}

func (a *ArithEmpty) ToSexp() string {
	return "(empty)"
}

func NewArithVar(name string) *ArithVar {
	a := &ArithVar{}
	a.kind = "var"
	a.Name = name
	return a
}

func (a *ArithVar) ToSexp() string {
	return "(var \"" + a.Name + "\")"
}

func NewArithBinaryOp(op string, left Node, right Node) *ArithBinaryOp {
	a := &ArithBinaryOp{}
	a.kind = "binary-op"
	a.Op = op
	a.Left = left
	a.Right = right
	return a
}

func (a *ArithBinaryOp) ToSexp() string {
	return "(binary-op \"" + a.Op + "\" " + a.Left.ToSexp() + " " + a.Right.ToSexp() + ")"
}

func NewArithUnaryOp(op string, operand Node) *ArithUnaryOp {
	a := &ArithUnaryOp{}
	a.kind = "unary-op"
	a.Op = op
	a.Operand = operand
	return a
}

func (a *ArithUnaryOp) ToSexp() string {
	return "(unary-op \"" + a.Op + "\" " + a.Operand.ToSexp() + ")"
}

func NewArithPreIncr(operand Node) *ArithPreIncr {
	a := &ArithPreIncr{}
	a.kind = "pre-incr"
	a.Operand = operand
	return a
}

func (a *ArithPreIncr) ToSexp() string {
	return "(pre-incr " + a.Operand.ToSexp() + ")"
}

func NewArithPostIncr(operand Node) *ArithPostIncr {
	a := &ArithPostIncr{}
	a.kind = "post-incr"
	a.Operand = operand
	return a
}

func (a *ArithPostIncr) ToSexp() string {
	return "(post-incr " + a.Operand.ToSexp() + ")"
}

func NewArithPreDecr(operand Node) *ArithPreDecr {
	a := &ArithPreDecr{}
	a.kind = "pre-decr"
	a.Operand = operand
	return a
}

func (a *ArithPreDecr) ToSexp() string {
	return "(pre-decr " + a.Operand.ToSexp() + ")"
}

func NewArithPostDecr(operand Node) *ArithPostDecr {
	a := &ArithPostDecr{}
	a.kind = "post-decr"
	a.Operand = operand
	return a
}

func (a *ArithPostDecr) ToSexp() string {
	return "(post-decr " + a.Operand.ToSexp() + ")"
}

func NewArithAssign(op string, target Node, value Node) *ArithAssign {
	a := &ArithAssign{}
	a.kind = "assign"
	a.Op = op
	a.Target = target
	a.Value = value
	return a
}

func (a *ArithAssign) ToSexp() string {
	return "(assign \"" + a.Op + "\" " + a.Target.ToSexp() + " " + a.Value.ToSexp() + ")"
}

func NewArithTernary(condition Node, ifTrue Node, ifFalse Node) *ArithTernary {
	a := &ArithTernary{}
	a.kind = "ternary"
	a.Condition = condition
	a.If_true = ifTrue
	a.If_false = ifFalse
	return a
}

func (a *ArithTernary) ToSexp() string {
	return "(ternary " + a.Condition.ToSexp() + " " + a.If_true.ToSexp() + " " + a.If_false.ToSexp() + ")"
}

func NewArithComma(left Node, right Node) *ArithComma {
	a := &ArithComma{}
	a.kind = "comma"
	a.Left = left
	a.Right = right
	return a
}

func (a *ArithComma) ToSexp() string {
	return "(comma " + a.Left.ToSexp() + " " + a.Right.ToSexp() + ")"
}

func NewArithSubscript(array string, index Node) *ArithSubscript {
	a := &ArithSubscript{}
	a.kind = "subscript"
	a.Array = array
	a.Index = index
	return a
}

func (a *ArithSubscript) ToSexp() string {
	return "(subscript \"" + a.Array + "\" " + a.Index.ToSexp() + ")"
}

func NewArithEscape(char string) *ArithEscape {
	a := &ArithEscape{}
	a.kind = "escape"
	a.Char = char
	return a
}

func (a *ArithEscape) ToSexp() string {
	return "(escape \"" + a.Char + "\")"
}

func NewArithDeprecated(expression string) *ArithDeprecated {
	a := &ArithDeprecated{}
	a.kind = "arith-deprecated"
	a.Expression = expression
	return a
}

func (a *ArithDeprecated) ToSexp() string {
	escaped := strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(a.Expression, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n")
	return "(arith-deprecated \"" + escaped + "\")"
}

func NewArithConcat(parts []Node) *ArithConcat {
	a := &ArithConcat{}
	a.kind = "arith-concat"
	a.Parts = parts
	return a
}

func (a *ArithConcat) ToSexp() string {
	sexps := []string{}
	for _, p := range a.Parts {
		sexps = append(sexps, p.ToSexp())
	}
	return "(arith-concat " + strings.Join(sexps, " ") + ")"
}

func NewAnsiCQuote(content string) *AnsiCQuote {
	a := &AnsiCQuote{}
	a.kind = "ansi-c"
	a.Content = content
	return a
}

func (a *AnsiCQuote) ToSexp() string {
	escaped := strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(a.Content, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n")
	return "(ansi-c \"" + escaped + "\")"
}

func NewLocaleString(content string) *LocaleString {
	l := &LocaleString{}
	l.kind = "locale"
	l.Content = content
	return l
}

func (l *LocaleString) ToSexp() string {
	escaped := strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(l.Content, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n")
	return "(locale \"" + escaped + "\")"
}

func NewProcessSubstitution(direction string, command Node) *ProcessSubstitution {
	p := &ProcessSubstitution{}
	p.kind = "procsub"
	p.Direction = direction
	p.Command = command
	return p
}

func (p *ProcessSubstitution) ToSexp() string {
	return "(procsub \"" + p.Direction + "\" " + p.Command.ToSexp() + ")"
}

func NewNegation(pipeline Node) *Negation {
	n := &Negation{}
	n.kind = "negation"
	n.Pipeline = pipeline
	return n
}

func (n *Negation) ToSexp() string {
	if _isNilNode(n.Pipeline) {
		return "(negation (command))"
	}
	return "(negation " + n.Pipeline.ToSexp() + ")"
}

func NewTime(pipeline Node, posix bool) *Time {
	t := &Time{}
	t.kind = "time"
	t.Pipeline = pipeline
	t.Posix = posix
	return t
}

func (t *Time) ToSexp() string {
	if _isNilNode(t.Pipeline) {
		if t.Posix {
			return "(time -p (command))"
		} else {
			return "(time (command))"
		}
	}
	if t.Posix {
		return "(time -p " + t.Pipeline.ToSexp() + ")"
	}
	return "(time " + t.Pipeline.ToSexp() + ")"
}

func NewConditionalExpr(body interface{}, redirects []Node) *ConditionalExpr {
	c := &ConditionalExpr{}
	c.kind = "cond-expr"
	c.Body = body
	if redirects == nil {
		redirects = []Node{}
	}
	c.Redirects = redirects
	return c
}

func (c *ConditionalExpr) ToSexp() string {
	var escaped string
	var result string
	var redirectParts []string
	var redirectSexps string
	body := c.Body
	switch b := body.(type) {
	case string:
		escaped = strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(b, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n")
		result = "(cond \"" + escaped + "\")"
	default:
		result = "(cond " + b.(Node).ToSexp() + ")"
	}
	if len(c.Redirects) > 0 {
		redirectParts = []string{}
		for _, r := range c.Redirects {
			redirectParts = append(redirectParts, r.ToSexp())
		}
		redirectSexps = strings.Join(redirectParts, " ")
		return result + " " + redirectSexps
	}
	return result
}

func NewUnaryTest(op string, operand Node) *UnaryTest {
	u := &UnaryTest{}
	u.kind = "unary-test"
	u.Op = op
	u.Operand = operand
	return u
}

func (u *UnaryTest) ToSexp() string {
	operandVal := u.Operand.(*Word).GetCondFormattedValue()
	return "(cond-unary \"" + u.Op + "\" (cond-term \"" + operandVal + "\"))"
}

func NewBinaryTest(op string, left Node, right Node) *BinaryTest {
	b := &BinaryTest{}
	b.kind = "binary-test"
	b.Op = op
	b.Left = left
	b.Right = right
	return b
}

func (b *BinaryTest) ToSexp() string {
	leftVal := b.Left.(*Word).GetCondFormattedValue()
	rightVal := b.Right.(*Word).GetCondFormattedValue()
	return "(cond-binary \"" + b.Op + "\" (cond-term \"" + leftVal + "\") (cond-term \"" + rightVal + "\"))"
}

func NewCondAnd(left Node, right Node) *CondAnd {
	c := &CondAnd{}
	c.kind = "cond-and"
	c.Left = left
	c.Right = right
	return c
}

func (c *CondAnd) ToSexp() string {
	return "(cond-and " + c.Left.ToSexp() + " " + c.Right.ToSexp() + ")"
}

func NewCondOr(left Node, right Node) *CondOr {
	c := &CondOr{}
	c.kind = "cond-or"
	c.Left = left
	c.Right = right
	return c
}

func (c *CondOr) ToSexp() string {
	return "(cond-or " + c.Left.ToSexp() + " " + c.Right.ToSexp() + ")"
}

func NewCondNot(operand Node) *CondNot {
	c := &CondNot{}
	c.kind = "cond-not"
	c.Operand = operand
	return c
}

func (c *CondNot) ToSexp() string {
	return c.Operand.ToSexp()
}

func NewCondParen(inner Node) *CondParen {
	c := &CondParen{}
	c.kind = "cond-paren"
	c.Inner = inner
	return c
}

func (c *CondParen) ToSexp() string {
	return "(cond-expr " + c.Inner.ToSexp() + ")"
}

func NewArray(elements []Node) *Array {
	a := &Array{}
	a.kind = "array"
	a.Elements = elements
	return a
}

func (a *Array) ToSexp() string {
	if !(len(a.Elements) > 0) {
		return "(array)"
	}
	parts := []string{}
	for _, e := range a.Elements {
		parts = append(parts, e.ToSexp())
	}
	inner := strings.Join(parts, " ")
	return "(array " + inner + ")"
}

func NewCoproc(command Node, name string) *Coproc {
	c := &Coproc{}
	c.kind = "coproc"
	c.Command = command
	c.Name = name
	return c
}

func (c *Coproc) ToSexp() string {
	var name string
	if c.Name != "" {
		name = c.Name
	} else {
		name = "COPROC"
	}
	return "(coproc \"" + name + "\" " + c.Command.ToSexp() + ")"
}

func NewParser(source string, inProcessSub bool, extglob bool) *Parser {
	p := &Parser{}
	p.Source = source
	p.Source_runes = []rune(source)
	p.Pos = 0
	p.Length = _runeLen(source)
	p._Pending_heredocs = []Node{}
	p._Cmdsub_heredoc_end = -1
	p._Saw_newline_in_single_quote = false
	p._In_process_sub = inProcessSub
	p._Extglob = extglob
	p._Ctx = NewContextStack()
	p._Lexer = NewLexer(source, extglob)
	p._Lexer._Parser = p
	p._Token_history = []*Token{nil, nil, nil, nil}
	p._Parser_state = ParserStateFlags_NONE
	p._Dolbrace_state = DolbraceState_NONE
	p._Eof_token = ""
	p._Word_context = WordCtxNormal
	p._At_command_start = false
	p._In_array_literal = false
	p._In_assign_builtin = false
	p._Arith_src = ""
	p._Arith_pos = 0
	p._Arith_len = 0
	return p
}

func (p *Parser) _SetState(flag int) {
	p._Parser_state = p._Parser_state | flag
}

func (p *Parser) _ClearState(flag int) {
	p._Parser_state = p._Parser_state & ^flag
}

func (p *Parser) _InState(flag int) bool {
	return p._Parser_state&flag != 0
}

func (p *Parser) _SaveParserState() *SavedParserState {
	return NewSavedParserState(p._Parser_state, p._Dolbrace_state, append([]Node{}, p._Pending_heredocs...), p._Ctx.CopyStack(), p._Eof_token)
}

func (p *Parser) _RestoreParserState(saved *SavedParserState) {
	p._Parser_state = saved.Parser_state
	p._Dolbrace_state = saved.Dolbrace_state
	p._Eof_token = saved.Eof_token
	p._Ctx.RestoreFrom(saved.Ctx_stack)
}

func (p *Parser) _RecordToken(tok *Token) {
	p._Token_history = []*Token{tok, p._Token_history[0], p._Token_history[1], p._Token_history[2]}
}

func (p *Parser) _UpdateDolbraceForOp(op string, hasParam bool) {
	if p._Dolbrace_state == DolbraceState_NONE {
		return
	}
	if op == "" || _runeLen(op) == 0 {
		return
	}
	firstChar := _runeAt(op, 0)
	if p._Dolbrace_state == DolbraceState_PARAM && hasParam {
		if strings.Contains("%#^,", firstChar) {
			p._Dolbrace_state = DolbraceState_QUOTE
			return
		}
		if firstChar == "/" {
			p._Dolbrace_state = DolbraceState_QUOTE2
			return
		}
	}
	if p._Dolbrace_state == DolbraceState_PARAM {
		if strings.Contains("#%^,~:-=?+/", firstChar) {
			p._Dolbrace_state = DolbraceState_OP
		}
	}
}

func (p *Parser) _SyncLexer() {
	if p._Lexer._Token_cache != nil {
		if p._Lexer._Token_cache.Pos != p.Pos || p._Lexer._Cached_word_context != p._Word_context || p._Lexer._Cached_at_command_start != p._At_command_start || p._Lexer._Cached_in_array_literal != p._In_array_literal || p._Lexer._Cached_in_assign_builtin != p._In_assign_builtin {
			p._Lexer._Token_cache = nil
		}
	}
	if p._Lexer.Pos != p.Pos {
		p._Lexer.Pos = p.Pos
	}
	p._Lexer._Eof_token = p._Eof_token
	p._Lexer._Parser_state = p._Parser_state
	p._Lexer._Last_read_token = p._Token_history[0]
	p._Lexer._Word_context = p._Word_context
	p._Lexer._At_command_start = p._At_command_start
	p._Lexer._In_array_literal = p._In_array_literal
	p._Lexer._In_assign_builtin = p._In_assign_builtin
}

func (p *Parser) _SyncParser() {
	p.Pos = p._Lexer.Pos
}

func (p *Parser) _LexPeekToken() *Token {
	if p._Lexer._Token_cache != nil && p._Lexer._Token_cache.Pos == p.Pos && p._Lexer._Cached_word_context == p._Word_context && p._Lexer._Cached_at_command_start == p._At_command_start && p._Lexer._Cached_in_array_literal == p._In_array_literal && p._Lexer._Cached_in_assign_builtin == p._In_assign_builtin {
		return p._Lexer._Token_cache
	}
	savedPos := p.Pos
	p._SyncLexer()
	result := p._Lexer.PeekToken()
	p._Lexer._Cached_word_context = p._Word_context
	p._Lexer._Cached_at_command_start = p._At_command_start
	p._Lexer._Cached_in_array_literal = p._In_array_literal
	p._Lexer._Cached_in_assign_builtin = p._In_assign_builtin
	p._Lexer._Post_read_pos = p._Lexer.Pos
	p.Pos = savedPos
	return result
}

func (p *Parser) _LexNextToken() *Token {
	var tok *Token
	if p._Lexer._Token_cache != nil && p._Lexer._Token_cache.Pos == p.Pos && p._Lexer._Cached_word_context == p._Word_context && p._Lexer._Cached_at_command_start == p._At_command_start && p._Lexer._Cached_in_array_literal == p._In_array_literal && p._Lexer._Cached_in_assign_builtin == p._In_assign_builtin {
		tok = p._Lexer.NextToken()
		p.Pos = p._Lexer._Post_read_pos
		p._Lexer.Pos = p._Lexer._Post_read_pos
	} else {
		p._SyncLexer()
		tok = p._Lexer.NextToken()
		p._Lexer._Cached_word_context = p._Word_context
		p._Lexer._Cached_at_command_start = p._At_command_start
		p._Lexer._Cached_in_array_literal = p._In_array_literal
		p._Lexer._Cached_in_assign_builtin = p._In_assign_builtin
		p._SyncParser()
	}
	p._RecordToken(tok)
	return tok
}

func (p *Parser) _LexSkipBlanks() {
	p._SyncLexer()
	p._Lexer.SkipBlanks()
	p._SyncParser()
}

func (p *Parser) _LexSkipComment() bool {
	p._SyncLexer()
	result := p._Lexer._SkipComment()
	p._SyncParser()
	return result
}

func (p *Parser) _LexIsCommandTerminator() bool {
	tok := p._LexPeekToken()
	t := tok.Type
	return _containsAny([]interface{}{TokenType_EOF, TokenType_NEWLINE, TokenType_PIPE, TokenType_SEMI, TokenType_LPAREN, TokenType_RPAREN, TokenType_AMP}, t)
}

func (p *Parser) _LexPeekOperator() (int, string) {
	tok := p._LexPeekToken()
	t := tok.Type
	if t >= TokenType_SEMI && t <= TokenType_GREATER || t >= TokenType_AND_AND && t <= TokenType_PIPE_AMP {
		return t, tok.Value
	}
	return 0, ""
}

func (p *Parser) _LexPeekReservedWord() string {
	var word string
	tok := p._LexPeekToken()
	if tok.Type != TokenType_WORD {
		return ""
	}
	word = tok.Value
	if strings.HasSuffix(word, "\\\n") {
		word = _Substring(word, 0, _runeLen(word)-2)
	}
	if ReservedWords[word] || _containsAny([]interface{}{"{", "}", "[[", "]]", "!", "time"}, word) {
		return word
	}
	return ""
}

func (p *Parser) _LexIsAtReservedWord(word string) bool {
	reserved := p._LexPeekReservedWord()
	return reserved == word
}

func (p *Parser) _LexConsumeWord(expected string) bool {
	var word string
	tok := p._LexPeekToken()
	if tok.Type != TokenType_WORD {
		return false
	}
	word = tok.Value
	if strings.HasSuffix(word, "\\\n") {
		word = _Substring(word, 0, _runeLen(word)-2)
	}
	if word == expected {
		p._LexNextToken()
		return true
	}
	return false
}

func (p *Parser) _LexPeekCaseTerminator() string {
	tok := p._LexPeekToken()
	t := tok.Type
	if t == TokenType_SEMI_SEMI {
		return ";;"
	}
	if t == TokenType_SEMI_AMP {
		return ";&"
	}
	if t == TokenType_SEMI_SEMI_AMP {
		return ";;&"
	}
	return ""
}

func (p *Parser) AtEnd() bool {
	return p.Pos >= p.Length
}

func (p *Parser) Peek() string {
	if p.AtEnd() {
		return ""
	}
	return string(string(p.Source_runes[p.Pos]))
}

func (p *Parser) Advance() string {
	if p.AtEnd() {
		return ""
	}
	ch := string(p.Source_runes[p.Pos])
	p.Pos += 1
	return string(ch)
}

func (p *Parser) PeekAt(offset int) string {
	pos := p.Pos + offset
	if pos < 0 || pos >= p.Length {
		return ""
	}
	return string(string(p.Source_runes[pos]))
}

func (p *Parser) Lookahead(n int) string {
	return _Substring(p.Source, p.Pos, p.Pos+n)
}

func (p *Parser) _IsBangFollowedByProcsub() bool {
	if p.Pos+2 >= p.Length {
		return false
	}
	nextChar := string(p.Source_runes[p.Pos+1])
	if nextChar != ">" && nextChar != "<" {
		return false
	}
	return string(p.Source_runes[p.Pos+2]) == "("
}

func (p *Parser) SkipWhitespace() {
	var ch string
	for !(p.AtEnd()) {
		p._LexSkipBlanks()
		if p.AtEnd() {
			break
		}
		ch = p.Peek()
		if ch == "#" {
			p._LexSkipComment()
		} else if ch == "\\" && p.PeekAt(1) == "\n" {
			p.Advance()
			p.Advance()
		} else {
			break
		}
	}
}

func (p *Parser) SkipWhitespaceAndNewlines() {
	var ch string
	for !(p.AtEnd()) {
		ch = p.Peek()
		if _IsWhitespace(ch) {
			p.Advance()
			if ch == "\n" {
				p._GatherHeredocBodies()
				if p._Cmdsub_heredoc_end != -1 && p._Cmdsub_heredoc_end > p.Pos {
					p.Pos = p._Cmdsub_heredoc_end
					p._Cmdsub_heredoc_end = -1
				}
			}
		} else if ch == "#" {
			for !(p.AtEnd()) && p.Peek() != "\n" {
				p.Advance()
			}
		} else if ch == "\\" && p.PeekAt(1) == "\n" {
			p.Advance()
			p.Advance()
		} else {
			break
		}
	}
}

func (p *Parser) _AtListTerminatingBracket() bool {
	var nextPos int
	if p.AtEnd() {
		return false
	}
	ch := p.Peek()
	if p._Eof_token != "" && ch == p._Eof_token {
		return true
	}
	if ch == ")" {
		return true
	}
	if ch == "}" {
		nextPos = p.Pos + 1
		if nextPos >= p.Length {
			return true
		}
		return _IsWordEndContext(string(p.Source_runes[nextPos]))
	}
	return false
}

func (p *Parser) _AtEofToken() bool {
	if p._Eof_token == "" {
		return false
	}
	tok := p._LexPeekToken()
	if p._Eof_token == ")" {
		return tok.Type == TokenType_RPAREN
	}
	if p._Eof_token == "}" {
		return tok.Type == TokenType_WORD && tok.Value == "}"
	}
	return false
}

func (p *Parser) _CollectRedirects() []Node {
	var redirect interface{}
	redirects := []Node{}
	for true {
		p.SkipWhitespace()
		redirect = p.ParseRedirect()
		if redirect == nil {
			break
		}
		redirects = append(redirects, redirect.(Node))
	}
	return _ternary(len(redirects) > 0, redirects, nil)
}

func (p *Parser) _ParseLoopBody(context string) Node {
	var brace *BraceGroup
	var body Node
	if p.Peek() == "{" {
		brace = p.ParseBraceGroup()
		if brace == nil {
			panic(NewParseError(fmt.Sprintf("Expected brace group body in %v", context), p._LexPeekToken().Pos, 0))
		}
		return brace.Body
	}
	if p._LexConsumeWord("do") {
		body = p.ParseListUntil(map[string]struct{}{"done": {}})
		if _isNilNode(body) {
			panic(NewParseError("Expected commands after 'do'", p._LexPeekToken().Pos, 0))
		}
		p.SkipWhitespaceAndNewlines()
		if !(p._LexConsumeWord("done")) {
			panic(NewParseError(fmt.Sprintf("Expected 'done' to close %v", context), p._LexPeekToken().Pos, 0))
		}
		return body
	}
	panic(NewParseError(fmt.Sprintf("Expected 'do' or '{' in %v", context), p._LexPeekToken().Pos, 0))
}

func (p *Parser) PeekWord() string {
	var ch string
	var word string
	savedPos := p.Pos
	p.SkipWhitespace()
	if p.AtEnd() || _IsMetachar(p.Peek()) {
		p.Pos = savedPos
		return ""
	}
	chars := []string{}
	for !(p.AtEnd()) && !(_IsMetachar(p.Peek())) {
		ch = p.Peek()
		if _IsQuote(ch) {
			break
		}
		if ch == "\\" && p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "\n" {
			break
		}
		if ch == "\\" && p.Pos+1 < p.Length {
			chars = append(chars, p.Advance())
			chars = append(chars, p.Advance())
			continue
		}
		chars = append(chars, p.Advance())
	}
	if len(chars) > 0 {
		word = strings.Join(chars, "")
	} else {
		word = ""
	}
	p.Pos = savedPos
	return word
}

func (p *Parser) ConsumeWord(expected string) bool {
	var keywordWord string
	var hasLeadingBrace bool
	savedPos := p.Pos
	p.SkipWhitespace()
	word := p.PeekWord()
	keywordWord = word
	hasLeadingBrace = false
	if word != "" && p._In_process_sub && _runeLen(word) > 1 && _runeAt(word, 0) == "}" {
		keywordWord = _Substring(word, 1, _runeLen(word))
		hasLeadingBrace = true
	}
	if keywordWord != expected {
		p.Pos = savedPos
		return false
	}
	p.SkipWhitespace()
	if hasLeadingBrace {
		p.Advance()
	}
	for range expected {
		p.Advance()
	}
	for p.Peek() == "\\" && p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "\n" {
		p.Advance()
		p.Advance()
	}
	return true
}

func (p *Parser) _IsWordTerminator(ctx int, ch string, bracketDepth int, parenDepth int) bool {
	p._SyncLexer()
	return p._Lexer._IsWordTerminator(ctx, ch, bracketDepth, parenDepth)
}

func (p *Parser) _ScanDoubleQuote(chars *[]string, parts *[]Node, start int, handleLineContinuation bool) {
	var c string
	var nextC string
	*chars = append(*chars, "\"")
	for !(p.AtEnd()) && p.Peek() != "\"" {
		c = p.Peek()
		if c == "\\" && p.Pos+1 < p.Length {
			nextC = string(p.Source_runes[p.Pos+1])
			if handleLineContinuation && nextC == "\n" {
				p.Advance()
				p.Advance()
			} else {
				*chars = append(*chars, p.Advance())
				*chars = append(*chars, p.Advance())
			}
		} else if c == "$" {
			if !(p._ParseDollarExpansion(chars, parts, true)) {
				*chars = append(*chars, p.Advance())
			}
		} else {
			*chars = append(*chars, p.Advance())
		}
	}
	if p.AtEnd() {
		panic(NewParseError("Unterminated double quote", start, 0))
	}
	*chars = append(*chars, p.Advance())
}

func (p *Parser) _ParseDollarExpansion(chars *[]string, parts *[]Node, inDquote bool) bool {
	var result0 Node
	var result1 string
	if p.Pos+2 < p.Length && string(p.Source_runes[p.Pos+1]) == "(" && string(p.Source_runes[p.Pos+2]) == "(" {
		result0, result1 = p._ParseArithmeticExpansion()
		if result0 != nil {
			*parts = append(*parts, result0.(Node))
			*chars = append(*chars, result1)
			return true
		}
		result0, result1 = p._ParseCommandSubstitution()
		if result0 != nil {
			*parts = append(*parts, result0.(Node))
			*chars = append(*chars, result1)
			return true
		}
		return false
	}
	if p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "[" {
		result0, result1 = p._ParseDeprecatedArithmetic()
		if result0 != nil {
			*parts = append(*parts, result0.(Node))
			*chars = append(*chars, result1)
			return true
		}
		return false
	}
	if p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "(" {
		result0, result1 = p._ParseCommandSubstitution()
		if result0 != nil {
			*parts = append(*parts, result0.(Node))
			*chars = append(*chars, result1)
			return true
		}
		return false
	}
	result0, result1 = p._ParseParamExpansion(inDquote)
	if result0 != nil {
		*parts = append(*parts, result0.(Node))
		*chars = append(*chars, result1)
		return true
	}
	return false
}

func (p *Parser) _ParseWordInternal(ctx int, atCommandStart bool, inArrayLiteral bool) *Word {
	p._Word_context = ctx
	return p.ParseWord(atCommandStart, inArrayLiteral, false)
}

func (p *Parser) ParseWord(atCommandStart bool, inArrayLiteral bool, inAssignBuiltin bool) *Word {
	p.SkipWhitespace()
	if p.AtEnd() {
		return nil
	}
	p._At_command_start = atCommandStart
	p._In_array_literal = inArrayLiteral
	p._In_assign_builtin = inAssignBuiltin
	tok := p._LexPeekToken()
	if tok.Type != TokenType_WORD {
		p._At_command_start = false
		p._In_array_literal = false
		p._In_assign_builtin = false
		return nil
	}
	p._LexNextToken()
	p._At_command_start = false
	p._In_array_literal = false
	p._In_assign_builtin = false
	return tok.Word.(*Word)
}

func (p *Parser) _ParseCommandSubstitution() (Node, string) {
	var start int
	_ = start
	var saved *SavedParserState
	_ = saved
	var cmd Node
	_ = cmd
	var textEnd int
	_ = textEnd
	var text string
	_ = text
	if p.AtEnd() || p.Peek() != "$" {
		return nil, ""
	}
	start = p.Pos
	p.Advance()

	if p.AtEnd() || p.Peek() != "(" {
		p.Pos = start
		return nil, ""
	}
	p.Advance()

	saved = p._SaveParserState()
	p._SetState(ParserStateFlags_PST_CMDSUBST | ParserStateFlags_PST_EOFTOKEN)
	p._Eof_token = ")"

	cmd = p.ParseList(true)
	if _isNilNode(cmd) {
		cmd = NewEmpty()
	}

	p.SkipWhitespaceAndNewlines()
	if p.AtEnd() || p.Peek() != ")" {
		p._RestoreParserState(saved)
		p.Pos = start
		return nil, ""
	}

	p.Advance()
	textEnd = p.Pos
	text = _Substring(p.Source, start, textEnd)

	p._RestoreParserState(saved)
	return NewCommandSubstitution(cmd, false), text
}

func (p *Parser) _ParseFunsub(start int) (Node, string) {
	var saved *SavedParserState
	_ = saved
	var cmd Node
	_ = cmd
	var text string
	_ = text
	p._SyncParser()
	if !(p.AtEnd()) && p.Peek() == "|" {
		p.Advance()
	}

	saved = p._SaveParserState()
	p._SetState(ParserStateFlags_PST_CMDSUBST | ParserStateFlags_PST_EOFTOKEN)
	p._Eof_token = "}"

	cmd = p.ParseList(true)
	if _isNilNode(cmd) {
		cmd = NewEmpty()
	}

	p.SkipWhitespaceAndNewlines()
	if p.AtEnd() || p.Peek() != "}" {
		p._RestoreParserState(saved)
		panic(NewMatchedPairError("unexpected EOF looking for `}'", start, 0))
	}

	p.Advance()
	text = _Substring(p.Source, start, p.Pos)
	p._RestoreParserState(saved)
	p._SyncLexer()
	return NewCommandSubstitution(cmd, true), text
}

func (p *Parser) _IsAssignmentWord(word Node) bool {
	return _Assignment(word.(*Word).Value, 0) != -1
}

func (p *Parser) _ParseBacktickSubstitution() (Node, string) {
	if p.AtEnd() || p.Peek() != "`" {
		return nil, ""
	}

	start := p.Pos
	p.Advance()

	contentChars := []string{}
	textChars := []string{"`"}

	type heredocInfo struct {
		delimiter string
		stripTabs bool
	}
	pendingHeredocs := []heredocInfo{}
	inHeredocBody := false
	currentHeredocDelim := ""
	currentHeredocStrip := false

	for !p.AtEnd() && (inHeredocBody || p.Peek() != "`") {
		if inHeredocBody {
			lineStart := p.Pos
			lineEnd := lineStart
			for lineEnd < p.Length && string(p.Source[lineEnd]) != "\n" {
				lineEnd++
			}
			line := _Substring(p.Source, lineStart, lineEnd)
			checkLine := line
			if currentHeredocStrip {
				checkLine = strings.TrimLeft(line, "\t")
			}

			if checkLine == currentHeredocDelim {
				for _, ch := range line {
					contentChars = append(contentChars, string(ch))
					textChars = append(textChars, string(ch))
				}
				p.Pos = lineEnd
				if p.Pos < p.Length && string(p.Source[p.Pos]) == "\n" {
					contentChars = append(contentChars, "\n")
					textChars = append(textChars, "\n")
					p.Advance()
				}
				inHeredocBody = false
				if len(pendingHeredocs) > 0 {
					currentHeredocDelim = pendingHeredocs[0].delimiter
					currentHeredocStrip = pendingHeredocs[0].stripTabs
					pendingHeredocs = pendingHeredocs[1:]
					inHeredocBody = true
				}
			} else if strings.HasPrefix(checkLine, currentHeredocDelim) && len(checkLine) > len(currentHeredocDelim) {
				tabsStripped := len(line) - len(checkLine)
				endPos := tabsStripped + len(currentHeredocDelim)
				for i := 0; i < endPos; i++ {
					contentChars = append(contentChars, string(line[i]))
					textChars = append(textChars, string(line[i]))
				}
				p.Pos = lineStart + endPos
				inHeredocBody = false
				if len(pendingHeredocs) > 0 {
					currentHeredocDelim = pendingHeredocs[0].delimiter
					currentHeredocStrip = pendingHeredocs[0].stripTabs
					pendingHeredocs = pendingHeredocs[1:]
					inHeredocBody = true
				}
			} else {
				for _, ch := range line {
					contentChars = append(contentChars, string(ch))
					textChars = append(textChars, string(ch))
				}
				p.Pos = lineEnd
				if p.Pos < p.Length && string(p.Source[p.Pos]) == "\n" {
					contentChars = append(contentChars, "\n")
					textChars = append(textChars, "\n")
					p.Advance()
				}
			}
			continue
		}

		c := p.Peek()

		if c == "\\" && p.Pos+1 < p.Length {
			nextC := string(p.Source[p.Pos+1])
			if nextC == "\n" {
				p.Advance()
				p.Advance()
			} else if _IsEscapeCharInBacktick(nextC) {
				p.Advance()
				escaped := p.Advance()
				contentChars = append(contentChars, escaped)
				textChars = append(textChars, "\\")
				textChars = append(textChars, escaped)
			} else {
				ch := p.Advance()
				contentChars = append(contentChars, ch)
				textChars = append(textChars, ch)
			}
			continue
		}

		if c == "<" && p.Pos+1 < p.Length && string(p.Source[p.Pos+1]) == "<" {
			if p.Pos+2 < p.Length && string(p.Source[p.Pos+2]) == "<" {
				contentChars = append(contentChars, p.Advance())
				textChars = append(textChars, "<")
				contentChars = append(contentChars, p.Advance())
				textChars = append(textChars, "<")
				contentChars = append(contentChars, p.Advance())
				textChars = append(textChars, "<")
				for !p.AtEnd() && _IsWhitespaceNoNewline(p.Peek()) {
					ch := p.Advance()
					contentChars = append(contentChars, ch)
					textChars = append(textChars, ch)
				}
				for !p.AtEnd() && !_IsWhitespace(p.Peek()) && p.Peek() != "(" && p.Peek() != ")" {
					if p.Peek() == "\\" && p.Pos+1 < p.Length {
						ch := p.Advance()
						contentChars = append(contentChars, ch)
						textChars = append(textChars, ch)
						ch = p.Advance()
						contentChars = append(contentChars, ch)
						textChars = append(textChars, ch)
					} else if p.Peek() == "\"" || p.Peek() == "'" {
						quote := p.Peek()
						ch := p.Advance()
						contentChars = append(contentChars, ch)
						textChars = append(textChars, ch)
						for !p.AtEnd() && p.Peek() != quote {
							if quote == "\"" && p.Peek() == "\\" {
								ch = p.Advance()
								contentChars = append(contentChars, ch)
								textChars = append(textChars, ch)
							}
							ch = p.Advance()
							contentChars = append(contentChars, ch)
							textChars = append(textChars, ch)
						}
						if !p.AtEnd() {
							ch = p.Advance()
							contentChars = append(contentChars, ch)
							textChars = append(textChars, ch)
						}
					} else {
						ch := p.Advance()
						contentChars = append(contentChars, ch)
						textChars = append(textChars, ch)
					}
				}
				continue
			}

			contentChars = append(contentChars, p.Advance())
			textChars = append(textChars, "<")
			contentChars = append(contentChars, p.Advance())
			textChars = append(textChars, "<")
			stripTabs := false
			if !p.AtEnd() && p.Peek() == "-" {
				stripTabs = true
				contentChars = append(contentChars, p.Advance())
				textChars = append(textChars, "-")
			}
			for !p.AtEnd() && _IsWhitespaceNoNewline(p.Peek()) {
				ch := p.Advance()
				contentChars = append(contentChars, ch)
				textChars = append(textChars, ch)
			}
			delimiterChars := []string{}
			if !p.AtEnd() {
				ch := p.Peek()
				if _IsQuote(ch) {
					quote := p.Advance()
					contentChars = append(contentChars, quote)
					textChars = append(textChars, quote)
					for !p.AtEnd() && p.Peek() != quote {
						dch := p.Advance()
						contentChars = append(contentChars, dch)
						textChars = append(textChars, dch)
						delimiterChars = append(delimiterChars, dch)
					}
					if !p.AtEnd() {
						closing := p.Advance()
						contentChars = append(contentChars, closing)
						textChars = append(textChars, closing)
					}
				} else if ch == "\\" {
					esc := p.Advance()
					contentChars = append(contentChars, esc)
					textChars = append(textChars, esc)
					if !p.AtEnd() {
						dch := p.Advance()
						contentChars = append(contentChars, dch)
						textChars = append(textChars, dch)
						delimiterChars = append(delimiterChars, dch)
					}
					for !p.AtEnd() && !_IsMetachar(p.Peek()) {
						dch := p.Advance()
						contentChars = append(contentChars, dch)
						textChars = append(textChars, dch)
						delimiterChars = append(delimiterChars, dch)
					}
				} else {
					for !p.AtEnd() && !_IsMetachar(p.Peek()) && p.Peek() != "`" {
						ch := p.Peek()
						if _IsQuote(ch) {
							quote := p.Advance()
							contentChars = append(contentChars, quote)
							textChars = append(textChars, quote)
							for !p.AtEnd() && p.Peek() != quote {
								dch := p.Advance()
								contentChars = append(contentChars, dch)
								textChars = append(textChars, dch)
								delimiterChars = append(delimiterChars, dch)
							}
							if !p.AtEnd() {
								closing := p.Advance()
								contentChars = append(contentChars, closing)
								textChars = append(textChars, closing)
							}
						} else if ch == "\\" {
							esc := p.Advance()
							contentChars = append(contentChars, esc)
							textChars = append(textChars, esc)
							if !p.AtEnd() {
								dch := p.Advance()
								contentChars = append(contentChars, dch)
								textChars = append(textChars, dch)
								delimiterChars = append(delimiterChars, dch)
							}
						} else {
							dch := p.Advance()
							contentChars = append(contentChars, dch)
							textChars = append(textChars, dch)
							delimiterChars = append(delimiterChars, dch)
						}
					}
				}
			}
			delimiter := strings.Join(delimiterChars, "")
			if delimiter != "" {
				pendingHeredocs = append(pendingHeredocs, heredocInfo{delimiter, stripTabs})
			}
			continue
		}

		if c == "\n" {
			ch := p.Advance()
			contentChars = append(contentChars, ch)
			textChars = append(textChars, ch)
			if len(pendingHeredocs) > 0 {
				currentHeredocDelim = pendingHeredocs[0].delimiter
				currentHeredocStrip = pendingHeredocs[0].stripTabs
				pendingHeredocs = pendingHeredocs[1:]
				inHeredocBody = true
			}
			continue
		}

		ch := p.Advance()
		contentChars = append(contentChars, ch)
		textChars = append(textChars, ch)
	}

	if p.AtEnd() {
		panic(NewParseError("Unterminated backtick", start, 0))
	}

	p.Advance()
	textChars = append(textChars, "`")
	text := strings.Join(textChars, "")
	content := strings.Join(contentChars, "")

	if len(pendingHeredocs) > 0 {
		delimiters := make([]interface{}, len(pendingHeredocs))
		for i, h := range pendingHeredocs {
			delimiters[i] = []interface{}{h.delimiter, h.stripTabs}
		}
		heredocStart, heredocEnd := _FindHeredocContentEnd(p.Source, p.Pos, delimiters)
		if heredocEnd > heredocStart {
			content = content + _Substring(p.Source, heredocStart, heredocEnd)
			if p._Cmdsub_heredoc_end < 0 {
				p._Cmdsub_heredoc_end = heredocEnd
			} else {
				if heredocEnd > p._Cmdsub_heredoc_end {
					p._Cmdsub_heredoc_end = heredocEnd
				}
			}
		}
	}

	subParser := NewParser(content, false, p._Extglob)
	cmd := subParser.ParseList(true)
	if _isNilNode(cmd) {
		cmd = NewEmpty()
	}

	return NewCommandSubstitution(cmd, false), text
}

func (p *Parser) _ParseProcessSubstitution() (Node, string) {
	if p.AtEnd() || !_IsRedirectChar(p.Peek()) {
		return nil, ""
	}

	start := p.Pos
	direction := p.Advance()

	if p.AtEnd() || p.Peek() != "(" {
		p.Pos = start
		return nil, ""
	}
	p.Advance()

	saved := p._SaveParserState()
	oldInProcessSub := p._In_process_sub
	p._In_process_sub = true
	p._SetState(ParserStateFlags_PST_EOFTOKEN)
	p._Eof_token = ")"

	var result struct {
		node Node
		text string
		ok   bool
	}

	func() {
		defer func() {
			if r := recover(); r != nil {
				result.ok = false
			}
		}()

		cmd := p.ParseList(true)
		if _isNilNode(cmd) {
			cmd = NewEmpty()
		}

		p.SkipWhitespaceAndNewlines()
		if p.AtEnd() || p.Peek() != ")" {
			panic("not at closing paren")
		}

		p.Advance()
		text := _Substring(p.Source, start, p.Pos)
		text = _StripLineContinuationsCommentAware(text)
		result.node = NewProcessSubstitution(direction, cmd)
		result.text = text
		result.ok = true
	}()

	p._RestoreParserState(saved)
	p._In_process_sub = oldInProcessSub

	if result.ok {
		return result.node, result.text
	}

	contentStartChar := ""
	if start+2 < p.Length {
		contentStartChar = string(p.Source[start+2])
	}

	if contentStartChar == " " || contentStartChar == "\t" || contentStartChar == "\n" {
		panic(NewParseError("Invalid process substitution", start, 0))
	}

	p.Pos = start + 2
	p._Lexer.Pos = p.Pos
	p._Lexer._ParseMatchedPair("(", ")", 0, false)
	p.Pos = p._Lexer.Pos
	text := _Substring(p.Source, start, p.Pos)
	text = _StripLineContinuationsCommentAware(text)
	return nil, text
}

func (p *Parser) _ParseArrayLiteral() (Node, string) {
	var word *Word
	if p.AtEnd() || p.Peek() != "(" {
		return nil, ""
	}
	start := p.Pos
	p.Advance()
	p._SetState(ParserStateFlags_PST_COMPASSIGN)
	elements := []Node{}
	for true {
		p.SkipWhitespaceAndNewlines()
		if p.AtEnd() {
			p._ClearState(ParserStateFlags_PST_COMPASSIGN)
			panic(NewParseError("Unterminated array literal", start, 0))
		}
		if p.Peek() == ")" {
			break
		}
		word = p.ParseWord(false, true, false)
		if word == nil {
			if p.Peek() == ")" {
				break
			}
			p._ClearState(ParserStateFlags_PST_COMPASSIGN)
			panic(NewParseError("Expected word in array literal", p.Pos, 0))
		}
		elements = append(elements, word)
	}
	if p.AtEnd() || p.Peek() != ")" {
		p._ClearState(ParserStateFlags_PST_COMPASSIGN)
		panic(NewParseError("Expected ) to close array literal", p.Pos, 0))
	}
	p.Advance()
	text := _Substring(p.Source, start, p.Pos)
	p._ClearState(ParserStateFlags_PST_COMPASSIGN)
	return NewArray(elements), text
}

func (p *Parser) _ParseArithmeticExpansion() (Node, string) {
	var firstClosePos int
	var c string
	var content string
	var expr Node
	if p.AtEnd() || p.Peek() != "$" {
		return nil, ""
	}
	start := p.Pos
	if p.Pos+2 >= p.Length || string(p.Source_runes[p.Pos+1]) != "(" || string(p.Source_runes[p.Pos+2]) != "(" {
		return nil, ""
	}
	p.Advance()
	p.Advance()
	p.Advance()
	contentStart := p.Pos
	depth := 2
	firstClosePos = -1
	for !(p.AtEnd()) && depth > 0 {
		c = p.Peek()
		if c == "'" {
			p.Advance()
			for !(p.AtEnd()) && p.Peek() != "'" {
				p.Advance()
			}
			if !(p.AtEnd()) {
				p.Advance()
			}
		} else if c == "\"" {
			p.Advance()
			for !(p.AtEnd()) {
				if p.Peek() == "\\" && p.Pos+1 < p.Length {
					p.Advance()
					p.Advance()
				} else if p.Peek() == "\"" {
					p.Advance()
					break
				} else {
					p.Advance()
				}
			}
		} else if c == "\\" && p.Pos+1 < p.Length {
			p.Advance()
			p.Advance()
		} else if c == "(" {
			depth += 1
			p.Advance()
		} else if c == ")" {
			if depth == 2 {
				firstClosePos = p.Pos
			}
			depth -= 1
			if depth == 0 {
				break
			}
			p.Advance()
		} else {
			if depth == 1 {
				firstClosePos = -1
			}
			p.Advance()
		}
	}
	if depth != 0 {
		if p.AtEnd() {
			panic(NewMatchedPairError("unexpected EOF looking for `))'", start, 0))
		}
		p.Pos = start
		return nil, ""
	}
	if firstClosePos != -1 {
		content = _Substring(p.Source, contentStart, firstClosePos)
	} else {
		content = _Substring(p.Source, contentStart, p.Pos)
	}
	p.Advance()
	text := _Substring(p.Source, start, p.Pos)
	parseOk := true
	func() {
		defer func() {
			if r := recover(); r != nil {
				parseOk = false
			}
		}()
		expr = p._ParseArithExpr(content)
	}()
	if !parseOk {
		p.Pos = start
		return nil, ""
	}
	return NewArithmeticExpansion(expr), text
}

func (p *Parser) _ParseArithExpr(content string) Node {
	var result Node
	savedArithSrc := p._Arith_src
	savedArithPos := p._Arith_pos
	savedArithLen := p._Arith_len
	savedParserState := p._Parser_state
	p._SetState(ParserStateFlags_PST_ARITH)
	p._Arith_src = content
	p._Arith_pos = 0
	p._Arith_len = _runeLen(content)
	p._ArithSkipWs()
	if p._ArithAtEnd() {
		result = nil
	} else {
		result = p._ArithParseComma()
	}
	p._Parser_state = savedParserState
	if savedArithSrc != "" {
		p._Arith_src = savedArithSrc
		p._Arith_pos = savedArithPos
		p._Arith_len = savedArithLen
	}
	return result
}

func (p *Parser) _ArithAtEnd() bool {
	return p._Arith_pos >= p._Arith_len
}

func (p *Parser) _ArithPeek(offset int) string {
	pos := p._Arith_pos + offset
	if pos >= p._Arith_len {
		return ""
	}
	return _runeAt(p._Arith_src, pos)
}

func (p *Parser) _ArithAdvance() string {
	if p._ArithAtEnd() {
		return ""
	}
	c := _runeAt(p._Arith_src, p._Arith_pos)
	p._Arith_pos += 1
	return c
}

func (p *Parser) _ArithSkipWs() {
	var c string
	for !(p._ArithAtEnd()) {
		c = _runeAt(p._Arith_src, p._Arith_pos)
		if _IsWhitespace(c) {
			p._Arith_pos += 1
		} else if c == "\\" && p._Arith_pos+1 < p._Arith_len && _runeAt(p._Arith_src, p._Arith_pos+1) == "\n" {
			p._Arith_pos += 2
		} else {
			break
		}
	}
}

func (p *Parser) _ArithMatch(s string) bool {
	return strings.HasPrefix(p._Arith_src[p._Arith_pos:], s)
}

func (p *Parser) _ArithConsume(s string) bool {
	if p._ArithMatch(s) {
		p._Arith_pos += _runeLen(s)
		return true
	}
	return false
}

func (p *Parser) _ArithParseComma() Node {
	var left Node
	var right Node
	left = p._ArithParseAssign()
	for true {
		p._ArithSkipWs()
		if p._ArithConsume(",") {
			p._ArithSkipWs()
			right = p._ArithParseAssign()
			left = NewArithComma(left, right)
		} else {
			break
		}
	}
	return left
}

func (p *Parser) _ArithParseAssign() Node {
	var right Node
	left := p._ArithParseTernary()
	p._ArithSkipWs()
	assignOps := []string{"<<=", ">>=", "+=", "-=", "*=", "/=", "%=", "&=", "^=", "|=", "="}
	for _, op := range assignOps {
		if p._ArithMatch(op) {
			if op == "=" && p._ArithPeek(1) == "=" {
				break
			}
			p._ArithConsume(op)
			p._ArithSkipWs()
			right = p._ArithParseAssign()
			return NewArithAssign(op, left, right)
		}
	}
	return left
}

func (p *Parser) _ArithParseTernary() Node {
	var ifTrue Node
	var ifFalse Node
	cond := p._ArithParseLogicalOr()
	p._ArithSkipWs()
	if p._ArithConsume("?") {
		p._ArithSkipWs()
		if p._ArithMatch(":") {
			ifTrue = nil
		} else {
			ifTrue = p._ArithParseAssign()
		}
		p._ArithSkipWs()
		if p._ArithConsume(":") {
			p._ArithSkipWs()
			if p._ArithAtEnd() || p._ArithPeek(0) == ")" {
				ifFalse = nil
			} else {
				ifFalse = p._ArithParseTernary()
			}
		} else {
			ifFalse = nil
		}
		return NewArithTernary(cond, ifTrue, ifFalse)
	}
	return cond
}

func (p *Parser) _ArithParseLeftAssoc(ops []string, parsefn interface{}) Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ArithParseLogicalOr() Node {
	left := p._ArithParseLogicalAnd()
	for {
		p._ArithSkipWs()
		matched := false
		if p._ArithMatch("||") {
			p._ArithConsume("||")
			p._ArithSkipWs()
			left = NewArithBinaryOp("||", left, p._ArithParseLogicalAnd())
			matched = true
		}
		if !matched {
			break
		}
	}
	return left
}

func (p *Parser) _ArithParseLogicalAnd() Node {
	left := p._ArithParseBitwiseOr()
	for {
		p._ArithSkipWs()
		matched := false
		if p._ArithMatch("&&") {
			p._ArithConsume("&&")
			p._ArithSkipWs()
			left = NewArithBinaryOp("&&", left, p._ArithParseBitwiseOr())
			matched = true
		}
		if !matched {
			break
		}
	}
	return left
}

func (p *Parser) _ArithParseBitwiseOr() Node {
	var left Node
	var right Node
	left = p._ArithParseBitwiseXor()
	for true {
		p._ArithSkipWs()
		if p._ArithPeek(0) == "|" && p._ArithPeek(1) != "|" && p._ArithPeek(1) != "=" {
			p._ArithAdvance()
			p._ArithSkipWs()
			right = p._ArithParseBitwiseXor()
			left = NewArithBinaryOp("|", left, right)
		} else {
			break
		}
	}
	return left
}

func (p *Parser) _ArithParseBitwiseXor() Node {
	var left Node
	var right Node
	left = p._ArithParseBitwiseAnd()
	for true {
		p._ArithSkipWs()
		if p._ArithPeek(0) == "^" && p._ArithPeek(1) != "=" {
			p._ArithAdvance()
			p._ArithSkipWs()
			right = p._ArithParseBitwiseAnd()
			left = NewArithBinaryOp("^", left, right)
		} else {
			break
		}
	}
	return left
}

func (p *Parser) _ArithParseBitwiseAnd() Node {
	var left Node
	var right Node
	left = p._ArithParseEquality()
	for true {
		p._ArithSkipWs()
		if p._ArithPeek(0) == "&" && p._ArithPeek(1) != "&" && p._ArithPeek(1) != "=" {
			p._ArithAdvance()
			p._ArithSkipWs()
			right = p._ArithParseEquality()
			left = NewArithBinaryOp("&", left, right)
		} else {
			break
		}
	}
	return left
}

func (p *Parser) _ArithParseEquality() Node {
	left := p._ArithParseComparison()
	for {
		p._ArithSkipWs()
		matched := false
		if p._ArithMatch("==") {
			p._ArithConsume("==")
			p._ArithSkipWs()
			left = NewArithBinaryOp("==", left, p._ArithParseComparison())
			matched = true
		} else if p._ArithMatch("!=") {
			p._ArithConsume("!=")
			p._ArithSkipWs()
			left = NewArithBinaryOp("!=", left, p._ArithParseComparison())
			matched = true
		}
		if !matched {
			break
		}
	}
	return left
}

func (p *Parser) _ArithParseComparison() Node {
	var left Node
	var right Node
	left = p._ArithParseShift()
	for true {
		p._ArithSkipWs()
		if p._ArithMatch("<=") {
			p._ArithConsume("<=")
			p._ArithSkipWs()
			right = p._ArithParseShift()
			left = NewArithBinaryOp("<=", left, right)
		} else if p._ArithMatch(">=") {
			p._ArithConsume(">=")
			p._ArithSkipWs()
			right = p._ArithParseShift()
			left = NewArithBinaryOp(">=", left, right)
		} else if p._ArithPeek(0) == "<" && p._ArithPeek(1) != "<" && p._ArithPeek(1) != "=" {
			p._ArithAdvance()
			p._ArithSkipWs()
			right = p._ArithParseShift()
			left = NewArithBinaryOp("<", left, right)
		} else if p._ArithPeek(0) == ">" && p._ArithPeek(1) != ">" && p._ArithPeek(1) != "=" {
			p._ArithAdvance()
			p._ArithSkipWs()
			right = p._ArithParseShift()
			left = NewArithBinaryOp(">", left, right)
		} else {
			break
		}
	}
	return left
}

func (p *Parser) _ArithParseShift() Node {
	var left Node
	var right Node
	left = p._ArithParseAdditive()
	for true {
		p._ArithSkipWs()
		if p._ArithMatch("<<=") {
			break
		}
		if p._ArithMatch(">>=") {
			break
		}
		if p._ArithMatch("<<") {
			p._ArithConsume("<<")
			p._ArithSkipWs()
			right = p._ArithParseAdditive()
			left = NewArithBinaryOp("<<", left, right)
		} else if p._ArithMatch(">>") {
			p._ArithConsume(">>")
			p._ArithSkipWs()
			right = p._ArithParseAdditive()
			left = NewArithBinaryOp(">>", left, right)
		} else {
			break
		}
	}
	return left
}

func (p *Parser) _ArithParseAdditive() Node {
	var left Node
	var c string
	var c2 string
	var right Node
	left = p._ArithParseMultiplicative()
	for true {
		p._ArithSkipWs()
		c = p._ArithPeek(0)
		c2 = p._ArithPeek(1)
		if c == "+" && c2 != "+" && c2 != "=" {
			p._ArithAdvance()
			p._ArithSkipWs()
			right = p._ArithParseMultiplicative()
			left = NewArithBinaryOp("+", left, right)
		} else if c == "-" && c2 != "-" && c2 != "=" {
			p._ArithAdvance()
			p._ArithSkipWs()
			right = p._ArithParseMultiplicative()
			left = NewArithBinaryOp("-", left, right)
		} else {
			break
		}
	}
	return left
}

func (p *Parser) _ArithParseMultiplicative() Node {
	var left Node
	var c string
	var c2 string
	var right Node
	left = p._ArithParseExponentiation()
	for true {
		p._ArithSkipWs()
		c = p._ArithPeek(0)
		c2 = p._ArithPeek(1)
		if c == "*" && c2 != "*" && c2 != "=" {
			p._ArithAdvance()
			p._ArithSkipWs()
			right = p._ArithParseExponentiation()
			left = NewArithBinaryOp("*", left, right)
		} else if c == "/" && c2 != "=" {
			p._ArithAdvance()
			p._ArithSkipWs()
			right = p._ArithParseExponentiation()
			left = NewArithBinaryOp("/", left, right)
		} else if c == "%" && c2 != "=" {
			p._ArithAdvance()
			p._ArithSkipWs()
			right = p._ArithParseExponentiation()
			left = NewArithBinaryOp("%", left, right)
		} else {
			break
		}
	}
	return left
}

func (p *Parser) _ArithParseExponentiation() Node {
	var right Node
	left := p._ArithParseUnary()
	p._ArithSkipWs()
	if p._ArithMatch("**") {
		p._ArithConsume("**")
		p._ArithSkipWs()
		right = p._ArithParseExponentiation()
		return NewArithBinaryOp("**", left, right)
	}
	return left
}

func (p *Parser) _ArithParseUnary() Node {
	var operand Node
	p._ArithSkipWs()
	if p._ArithMatch("++") {
		p._ArithConsume("++")
		p._ArithSkipWs()
		operand = p._ArithParseUnary()
		return NewArithPreIncr(operand)
	}
	if p._ArithMatch("--") {
		p._ArithConsume("--")
		p._ArithSkipWs()
		operand = p._ArithParseUnary()
		return NewArithPreDecr(operand)
	}
	c := p._ArithPeek(0)
	if c == "!" {
		p._ArithAdvance()
		p._ArithSkipWs()
		operand = p._ArithParseUnary()
		return NewArithUnaryOp("!", operand)
	}
	if c == "~" {
		p._ArithAdvance()
		p._ArithSkipWs()
		operand = p._ArithParseUnary()
		return NewArithUnaryOp("~", operand)
	}
	if c == "+" && p._ArithPeek(1) != "+" {
		p._ArithAdvance()
		p._ArithSkipWs()
		operand = p._ArithParseUnary()
		return NewArithUnaryOp("+", operand)
	}
	if c == "-" && p._ArithPeek(1) != "-" {
		p._ArithAdvance()
		p._ArithSkipWs()
		operand = p._ArithParseUnary()
		return NewArithUnaryOp("-", operand)
	}
	return p._ArithParsePostfix()
}

func (p *Parser) _ArithParsePostfix() Node {
	var left Node
	var index Node
	left = p._ArithParsePrimary()
	for true {
		p._ArithSkipWs()
		if p._ArithMatch("++") {
			p._ArithConsume("++")
			left = NewArithPostIncr(left)
		} else if p._ArithMatch("--") {
			p._ArithConsume("--")
			left = NewArithPostDecr(left)
		} else if p._ArithPeek(0) == "[" {
			if l, ok := left.(*ArithVar); ok {
				p._ArithAdvance()
				p._ArithSkipWs()
				index = p._ArithParseComma()
				p._ArithSkipWs()
				if !(p._ArithConsume("]")) {
					panic(NewParseError("Expected ']' in array subscript", p._Arith_pos, 0))
				}
				left = NewArithSubscript(l.Name, index)
			} else {
				break
			}
		} else {
			break
		}
	}
	return left
}

func (p *Parser) _ArithParsePrimary() Node {
	var expr Node
	var escapedChar string
	p._ArithSkipWs()
	c := p._ArithPeek(0)
	if c == "(" {
		p._ArithAdvance()
		p._ArithSkipWs()
		expr = p._ArithParseComma()
		p._ArithSkipWs()
		if !(p._ArithConsume(")")) {
			panic(NewParseError("Expected ')' in arithmetic expression", p._Arith_pos, 0))
		}
		return expr
	}
	if c == "#" && p._ArithPeek(1) == "$" {
		p._ArithAdvance()
		return p._ArithParseExpansion()
	}
	if c == "$" {
		return p._ArithParseExpansion()
	}
	if c == "'" {
		return p._ArithParseSingleQuote()
	}
	if c == "\"" {
		return p._ArithParseDoubleQuote()
	}
	if c == "`" {
		return p._ArithParseBacktick()
	}
	if c == "\\" {
		p._ArithAdvance()
		if p._ArithAtEnd() {
			panic(NewParseError("Unexpected end after backslash in arithmetic", p._Arith_pos, 0))
		}
		escapedChar = p._ArithAdvance()
		return NewArithEscape(escapedChar)
	}
	if p._ArithAtEnd() || strings.Contains(")]:,;?|&<>=!+-*/%^~#{}", c) {
		return NewArithEmpty()
	}
	return p._ArithParseNumberOrVar()
}

func (p *Parser) _ArithParseExpansion() Node {
	var ch string
	if !(p._ArithConsume("$")) {
		panic(NewParseError("Expected '$'", p._Arith_pos, 0))
	}
	c := p._ArithPeek(0)
	if c == "(" {
		return p._ArithParseCmdsub()
	}
	if c == "{" {
		return p._ArithParseBracedParam()
	}
	nameChars := []string{}
	for !(p._ArithAtEnd()) {
		ch = p._ArithPeek(0)
		if (unicode.IsLetter(_runeFromChar(ch)) || unicode.IsDigit(_runeFromChar(ch))) || ch == "_" {
			nameChars = append(nameChars, p._ArithAdvance())
		} else if (_IsSpecialParamOrDigit(ch) || ch == "#") && !(len(nameChars) > 0) {
			nameChars = append(nameChars, p._ArithAdvance())
			break
		} else {
			break
		}
	}
	if !(len(nameChars) > 0) {
		panic(NewParseError("Expected variable name after $", p._Arith_pos, 0))
	}
	return NewParamExpansion(strings.Join(nameChars, ""), "", "")
}

func (p *Parser) _ArithParseCmdsub() Node {
	var depth int
	var contentStart int
	var ch string
	var content string
	var innerExpr Node
	p._ArithAdvance()
	if p._ArithPeek(0) == "(" {
		p._ArithAdvance()
		depth = 1
		contentStart = p._Arith_pos
		for !(p._ArithAtEnd()) && depth > 0 {
			ch = p._ArithPeek(0)
			if ch == "(" {
				depth += 1
				p._ArithAdvance()
			} else if ch == ")" {
				if depth == 1 && p._ArithPeek(1) == ")" {
					break
				}
				depth -= 1
				p._ArithAdvance()
			} else {
				p._ArithAdvance()
			}
		}
		content = _Substring(p._Arith_src, contentStart, p._Arith_pos)
		p._ArithAdvance()
		p._ArithAdvance()
		innerExpr = p._ParseArithExpr(content)
		return NewArithmeticExpansion(innerExpr)
	}
	depth = 1
	contentStart = p._Arith_pos
	for !(p._ArithAtEnd()) && depth > 0 {
		ch = p._ArithPeek(0)
		if ch == "(" {
			depth += 1
			p._ArithAdvance()
		} else if ch == ")" {
			depth -= 1
			if depth == 0 {
				break
			}
			p._ArithAdvance()
		} else {
			p._ArithAdvance()
		}
	}
	content = _Substring(p._Arith_src, contentStart, p._Arith_pos)
	p._ArithAdvance()
	subParser := NewParser(content, false, p._Extglob)
	cmd := subParser.ParseList(true)
	return NewCommandSubstitution(cmd, false)
}

func (p *Parser) _ArithParseBracedParam() Node {
	var nameChars []string
	var ch string
	p._ArithAdvance()
	if p._ArithPeek(0) == "!" {
		p._ArithAdvance()
		nameChars = []string{}
		for !(p._ArithAtEnd()) && p._ArithPeek(0) != "}" {
			nameChars = append(nameChars, p._ArithAdvance())
		}
		p._ArithConsume("}")
		return NewParamIndirect(strings.Join(nameChars, ""), "", "")
	}
	if p._ArithPeek(0) == "#" {
		p._ArithAdvance()
		nameChars = []string{}
		for !(p._ArithAtEnd()) && p._ArithPeek(0) != "}" {
			nameChars = append(nameChars, p._ArithAdvance())
		}
		p._ArithConsume("}")
		return NewParamLength(strings.Join(nameChars, ""))
	}
	nameChars = []string{}
	for !(p._ArithAtEnd()) {
		ch = p._ArithPeek(0)
		if ch == "}" {
			p._ArithAdvance()
			return NewParamExpansion(strings.Join(nameChars, ""), "", "")
		}
		if _IsParamExpansionOp(ch) {
			break
		}
		nameChars = append(nameChars, p._ArithAdvance())
	}
	name := strings.Join(nameChars, "")
	opChars := []string{}
	depth := 1
	for !(p._ArithAtEnd()) && depth > 0 {
		ch = p._ArithPeek(0)
		if ch == "{" {
			depth += 1
			opChars = append(opChars, p._ArithAdvance())
		} else if ch == "}" {
			depth -= 1
			if depth == 0 {
				break
			}
			opChars = append(opChars, p._ArithAdvance())
		} else {
			opChars = append(opChars, p._ArithAdvance())
		}
	}
	p._ArithConsume("}")
	opStr := strings.Join(opChars, "")
	if strings.HasPrefix(opStr, ":-") {
		return NewParamExpansion(name, ":-", _Substring(opStr, 2, _runeLen(opStr)))
	}
	if strings.HasPrefix(opStr, ":=") {
		return NewParamExpansion(name, ":=", _Substring(opStr, 2, _runeLen(opStr)))
	}
	if strings.HasPrefix(opStr, ":+") {
		return NewParamExpansion(name, ":+", _Substring(opStr, 2, _runeLen(opStr)))
	}
	if strings.HasPrefix(opStr, ":?") {
		return NewParamExpansion(name, ":?", _Substring(opStr, 2, _runeLen(opStr)))
	}
	if strings.HasPrefix(opStr, ":") {
		return NewParamExpansion(name, ":", _Substring(opStr, 1, _runeLen(opStr)))
	}
	if strings.HasPrefix(opStr, "##") {
		return NewParamExpansion(name, "##", _Substring(opStr, 2, _runeLen(opStr)))
	}
	if strings.HasPrefix(opStr, "#") {
		return NewParamExpansion(name, "#", _Substring(opStr, 1, _runeLen(opStr)))
	}
	if strings.HasPrefix(opStr, "%%") {
		return NewParamExpansion(name, "%%", _Substring(opStr, 2, _runeLen(opStr)))
	}
	if strings.HasPrefix(opStr, "%") {
		return NewParamExpansion(name, "%", _Substring(opStr, 1, _runeLen(opStr)))
	}
	if strings.HasPrefix(opStr, "//") {
		return NewParamExpansion(name, "//", _Substring(opStr, 2, _runeLen(opStr)))
	}
	if strings.HasPrefix(opStr, "/") {
		return NewParamExpansion(name, "/", _Substring(opStr, 1, _runeLen(opStr)))
	}
	return NewParamExpansion(name, "", opStr)
}

func (p *Parser) _ArithParseSingleQuote() Node {
	p._ArithAdvance()
	contentStart := p._Arith_pos
	for !(p._ArithAtEnd()) && p._ArithPeek(0) != "'" {
		p._ArithAdvance()
	}
	content := _Substring(p._Arith_src, contentStart, p._Arith_pos)
	if !(p._ArithConsume("'")) {
		panic(NewParseError("Unterminated single quote in arithmetic", p._Arith_pos, 0))
	}
	return NewArithNumber(content)
}

func (p *Parser) _ArithParseDoubleQuote() Node {
	var c string
	p._ArithAdvance()
	contentStart := p._Arith_pos
	for !(p._ArithAtEnd()) && p._ArithPeek(0) != "\"" {
		c = p._ArithPeek(0)
		if c == "\\" && !(p._ArithAtEnd()) {
			p._ArithAdvance()
			p._ArithAdvance()
		} else {
			p._ArithAdvance()
		}
	}
	content := _Substring(p._Arith_src, contentStart, p._Arith_pos)
	if !(p._ArithConsume("\"")) {
		panic(NewParseError("Unterminated double quote in arithmetic", p._Arith_pos, 0))
	}
	return NewArithNumber(content)
}

func (p *Parser) _ArithParseBacktick() Node {
	var c string
	p._ArithAdvance()
	contentStart := p._Arith_pos
	for !(p._ArithAtEnd()) && p._ArithPeek(0) != "`" {
		c = p._ArithPeek(0)
		if c == "\\" && !(p._ArithAtEnd()) {
			p._ArithAdvance()
			p._ArithAdvance()
		} else {
			p._ArithAdvance()
		}
	}
	content := _Substring(p._Arith_src, contentStart, p._Arith_pos)
	if !(p._ArithConsume("`")) {
		panic(NewParseError("Unterminated backtick in arithmetic", p._Arith_pos, 0))
	}
	subParser := NewParser(content, false, p._Extglob)
	cmd := subParser.ParseList(true)
	return NewCommandSubstitution(cmd, false)
}

func (p *Parser) _ArithParseNumberOrVar() Node {
	var ch string
	var prefix string
	var expansion Node
	p._ArithSkipWs()
	chars := []string{}
	c := p._ArithPeek(0)
	if _strIsDigits(c) {
		for !(p._ArithAtEnd()) {
			ch = p._ArithPeek(0)
			if (unicode.IsLetter(_runeFromChar(ch)) || unicode.IsDigit(_runeFromChar(ch))) || ch == "#" || ch == "_" {
				chars = append(chars, p._ArithAdvance())
			} else {
				break
			}
		}
		prefix = strings.Join(chars, "")
		if !(p._ArithAtEnd()) && p._ArithPeek(0) == "$" {
			expansion = p._ArithParseExpansion()
			return NewArithConcat([]Node{NewArithNumber(prefix), expansion})
		}
		return NewArithNumber(prefix)
	}
	if unicode.IsLetter(_runeFromChar(c)) || c == "_" {
		for !(p._ArithAtEnd()) {
			ch = p._ArithPeek(0)
			if (unicode.IsLetter(_runeFromChar(ch)) || unicode.IsDigit(_runeFromChar(ch))) || ch == "_" {
				chars = append(chars, p._ArithAdvance())
			} else {
				break
			}
		}
		return NewArithVar(strings.Join(chars, ""))
	}
	panic(NewParseError("Unexpected character '"+c+"' in arithmetic expression", p._Arith_pos, 0))
}

func (p *Parser) _ParseDeprecatedArithmetic() (Node, string) {
	if p.AtEnd() || p.Peek() != "$" {
		return nil, ""
	}
	start := p.Pos
	if p.Pos+1 >= p.Length || string(p.Source_runes[p.Pos+1]) != "[" {
		return nil, ""
	}
	p.Advance()
	p.Advance()
	p._Lexer.Pos = p.Pos
	content := p._Lexer._ParseMatchedPair("[", "]", MatchedPairFlags_ARITH, false)
	p.Pos = p._Lexer.Pos
	text := _Substring(p.Source, start, p.Pos)
	return NewArithDeprecated(content), text
}

func (p *Parser) _ParseParamExpansion(inDquote bool) (Node, string) {
	p._SyncLexer()
	result0, result1 := p._Lexer._ReadParamExpansion(inDquote)
	p._SyncParser()
	return result0, result1
}

func (p *Parser) ParseRedirect() interface{} {
	var fd int
	var varfd string
	var saved int
	var varnameChars []string
	var inBracket bool
	var ch string
	var varname string
	var isValidVarfd bool
	var left int
	var right int
	var base string
	var fdChars []string
	var op string
	var target *Word
	var stripTabs bool
	var nextCh string
	var wordStart int
	var fdTarget string
	var innerWord *Word
	p.SkipWhitespace()
	if p.AtEnd() {
		return nil
	}
	start := p.Pos
	fd = -1
	varfd = ""
	if p.Peek() == "{" {
		saved = p.Pos
		p.Advance()
		varnameChars = []string{}
		inBracket = false
		for !(p.AtEnd()) && !(_IsRedirectChar(p.Peek())) {
			ch = p.Peek()
			if ch == "}" && !(inBracket) {
				break
			} else if ch == "[" {
				inBracket = true
				varnameChars = append(varnameChars, p.Advance())
			} else if ch == "]" {
				inBracket = false
				varnameChars = append(varnameChars, p.Advance())
			} else if (unicode.IsLetter(_runeFromChar(ch)) || unicode.IsDigit(_runeFromChar(ch))) || ch == "_" {
				varnameChars = append(varnameChars, p.Advance())
			} else if inBracket && !(_IsMetachar(ch)) {
				varnameChars = append(varnameChars, p.Advance())
			} else {
				break
			}
		}
		varname = strings.Join(varnameChars, "")
		isValidVarfd = false
		if len(varname) > 0 {
			if unicode.IsLetter(_runeFromChar(_runeAt(varname, 0))) || _runeAt(varname, 0) == "_" {
				if strings.Contains(varname, "[") || strings.Contains(varname, "]") {
					left = strings.Index(varname, "[")
					right = strings.LastIndex(varname, "]")
					if left != -1 && right == _runeLen(varname)-1 && right > left+1 {
						base = _Substring(varname, 0, left)
						if len(base) > 0 && (unicode.IsLetter(_runeFromChar(_runeAt(base, 0))) || _runeAt(base, 0) == "_") {
							isValidVarfd = true
							for _, c := range _Substring(base, 1, _runeLen(base)) {
								if !((unicode.IsLetter(_runeFromChar(c)) || unicode.IsDigit(_runeFromChar(c))) || c == '_') {
									isValidVarfd = false
									break
								}
							}
						}
					}
				} else {
					isValidVarfd = true
					for _, c := range _Substring(varname, 1, _runeLen(varname)) {
						if !((unicode.IsLetter(_runeFromChar(c)) || unicode.IsDigit(_runeFromChar(c))) || c == '_') {
							isValidVarfd = false
							break
						}
					}
				}
			}
		}
		if !(p.AtEnd()) && p.Peek() == "}" && isValidVarfd {
			p.Advance()
			varfd = varname
		} else {
			p.Pos = saved
		}
	}
	if varfd == "" && p.Peek() != "" && _strIsDigits(p.Peek()) {
		fdChars = []string{}
		for !(p.AtEnd()) && _strIsDigits(p.Peek()) {
			fdChars = append(fdChars, p.Advance())
		}
		fd = _mustAtoi(strings.Join(fdChars, ""))
	}
	ch = p.Peek()
	if ch == "&" && p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == ">" {
		if fd != -1 || varfd != "" {
			p.Pos = start
			return nil
		}
		p.Advance()
		p.Advance()
		if !(p.AtEnd()) && p.Peek() == ">" {
			p.Advance()
			op = "&>>"
		} else {
			op = "&>"
		}
		p.SkipWhitespace()
		target = p.ParseWord(false, false, false)
		if target == nil {
			panic(NewParseError("Expected target for redirect "+op, p.Pos, 0))
		}
		return NewRedirect(op, target, 0)
	}
	if ch == "" || !(_IsRedirectChar(ch)) {
		p.Pos = start
		return nil
	}
	if fd == -1 && p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "(" {
		p.Pos = start
		return nil
	}
	op = p.Advance()
	stripTabs = false
	if !(p.AtEnd()) {
		nextCh = p.Peek()
		if op == ">" && nextCh == ">" {
			p.Advance()
			op = ">>"
		} else if op == "<" && nextCh == "<" {
			p.Advance()
			if !(p.AtEnd()) && p.Peek() == "<" {
				p.Advance()
				op = "<<<"
			} else if !(p.AtEnd()) && p.Peek() == "-" {
				p.Advance()
				op = "<<"
				stripTabs = true
			} else {
				op = "<<"
			}
		} else if op == "<" && nextCh == ">" {
			p.Advance()
			op = "<>"
		} else if op == ">" && nextCh == "|" {
			p.Advance()
			op = ">|"
		} else if fd == -1 && varfd == "" && op == ">" && nextCh == "&" {
			if p.Pos+1 >= p.Length || !(_IsDigitOrDash(string(p.Source_runes[p.Pos+1]))) {
				p.Advance()
				op = ">&"
			}
		} else if fd == -1 && varfd == "" && op == "<" && nextCh == "&" {
			if p.Pos+1 >= p.Length || !(_IsDigitOrDash(string(p.Source_runes[p.Pos+1]))) {
				p.Advance()
				op = "<&"
			}
		}
	}
	if op == "<<" {
		return p._ParseHeredoc(fd, stripTabs)
	}
	if varfd != "" {
		op = "{" + varfd + "}" + op
	} else if fd != -1 {
		op = fmt.Sprint(fd) + op
	}
	if !(p.AtEnd()) && p.Peek() == "&" {
		p.Advance()
		p.SkipWhitespace()
		if !(p.AtEnd()) && p.Peek() == "-" {
			if p.Pos+1 < p.Length && !(_IsMetachar(string(p.Source_runes[p.Pos+1]))) {
				p.Advance()
				target = NewWord("&-", nil)
			} else {
				target = nil
			}
		} else {
			target = nil
		}
		if target == nil {
			if !(p.AtEnd()) && (_strIsDigits(p.Peek()) || p.Peek() == "-") {
				wordStart = p.Pos
				fdChars = []string{}
				for !(p.AtEnd()) && _strIsDigits(p.Peek()) {
					fdChars = append(fdChars, p.Advance())
				}
				if len(fdChars) > 0 {
					fdTarget = strings.Join(fdChars, "")
				} else {
					fdTarget = ""
				}
				if !(p.AtEnd()) && p.Peek() == "-" {
					fdTarget += p.Advance()
				}
				if fdTarget != "-" && !(p.AtEnd()) && !(_IsMetachar(p.Peek())) {
					p.Pos = wordStart
					innerWord = p.ParseWord(false, false, false)
					if innerWord != nil {
						target = NewWord("&"+innerWord.Value, nil)
						target.Parts = innerWord.Parts
					} else {
						panic(NewParseError("Expected target for redirect "+op, p.Pos, 0))
					}
				} else {
					target = NewWord("&"+fdTarget, nil)
				}
			} else {
				innerWord = p.ParseWord(false, false, false)
				if innerWord != nil {
					target = NewWord("&"+innerWord.Value, nil)
					target.Parts = innerWord.Parts
				} else {
					panic(NewParseError("Expected target for redirect "+op, p.Pos, 0))
				}
			}
		}
	} else {
		p.SkipWhitespace()
		if _containsAny([]interface{}{">&", "<&"}, op) && !(p.AtEnd()) && p.Peek() == "-" {
			if p.Pos+1 < p.Length && !(_IsMetachar(string(p.Source_runes[p.Pos+1]))) {
				p.Advance()
				target = NewWord("&-", nil)
			} else {
				target = p.ParseWord(false, false, false)
			}
		} else {
			target = p.ParseWord(false, false, false)
		}
	}
	if target == nil {
		panic(NewParseError("Expected target for redirect "+op, p.Pos, 0))
	}
	return NewRedirect(op, target, 0)
}

func (p *Parser) _ParseHeredocDelimiter() (string, bool) {
	var quoted bool
	var ch string
	var c string
	var nextCh string
	var esc string
	var escVal int
	var depth int
	var dollarCount int
	var j int
	p.SkipWhitespace()
	quoted = false
	delimiterChars := []string{}
	for true {
		for !(p.AtEnd()) && !(_IsMetachar(p.Peek())) {
			ch = p.Peek()
			if ch == "\"" {
				quoted = true
				p.Advance()
				for !(p.AtEnd()) && p.Peek() != "\"" {
					delimiterChars = append(delimiterChars, p.Advance())
				}
				if !(p.AtEnd()) {
					p.Advance()
				}
			} else if ch == "'" {
				quoted = true
				p.Advance()
				for !(p.AtEnd()) && p.Peek() != "'" {
					c = p.Advance()
					if c == "\n" {
						p._Saw_newline_in_single_quote = true
					}
					delimiterChars = append(delimiterChars, c)
				}
				if !(p.AtEnd()) {
					p.Advance()
				}
			} else if ch == "\\" {
				p.Advance()
				if !(p.AtEnd()) {
					nextCh = p.Peek()
					if nextCh == "\n" {
						p.Advance()
					} else {
						quoted = true
						delimiterChars = append(delimiterChars, p.Advance())
					}
				}
			} else if ch == "$" && p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "'" {
				quoted = true
				p.Advance()
				p.Advance()
				for !(p.AtEnd()) && p.Peek() != "'" {
					c = p.Peek()
					if c == "\\" && p.Pos+1 < p.Length {
						p.Advance()
						esc = p.Peek()
						escVal = _GetAnsiEscape(esc)
						if escVal >= 0 {
							delimiterChars = append(delimiterChars, string(rune(escVal)))
							p.Advance()
						} else if esc == "'" {
							delimiterChars = append(delimiterChars, p.Advance())
						} else {
							delimiterChars = append(delimiterChars, p.Advance())
						}
					} else {
						delimiterChars = append(delimiterChars, p.Advance())
					}
				}
				if !(p.AtEnd()) {
					p.Advance()
				}
			} else if _IsExpansionStart(p.Source, p.Pos, "$(") {
				delimiterChars = append(delimiterChars, p.Advance())
				delimiterChars = append(delimiterChars, p.Advance())
				depth = 1
				for !(p.AtEnd()) && depth > 0 {
					c = p.Peek()
					if c == "(" {
						depth += 1
					} else if c == ")" {
						depth -= 1
					}
					delimiterChars = append(delimiterChars, p.Advance())
				}
			} else if ch == "$" && p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "{" {
				dollarCount = 0
				j = p.Pos - 1
				for j >= 0 && string(p.Source_runes[j]) == "$" {
					dollarCount += 1
					j -= 1
				}
				if j >= 0 && string(p.Source_runes[j]) == "\\" {
					dollarCount -= 1
				}
				if dollarCount%2 == 1 {
					delimiterChars = append(delimiterChars, p.Advance())
				} else {
					delimiterChars = append(delimiterChars, p.Advance())
					delimiterChars = append(delimiterChars, p.Advance())
					depth = 0
					for !(p.AtEnd()) {
						c = p.Peek()
						if c == "{" {
							depth += 1
						} else if c == "}" {
							delimiterChars = append(delimiterChars, p.Advance())
							if depth == 0 {
								break
							}
							depth -= 1
							if depth == 0 && !(p.AtEnd()) && _IsMetachar(p.Peek()) {
								break
							}
							continue
						}
						delimiterChars = append(delimiterChars, p.Advance())
					}
				}
			} else if ch == "$" && p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "[" {
				dollarCount = 0
				j = p.Pos - 1
				for j >= 0 && string(p.Source_runes[j]) == "$" {
					dollarCount += 1
					j -= 1
				}
				if j >= 0 && string(p.Source_runes[j]) == "\\" {
					dollarCount -= 1
				}
				if dollarCount%2 == 1 {
					delimiterChars = append(delimiterChars, p.Advance())
				} else {
					delimiterChars = append(delimiterChars, p.Advance())
					delimiterChars = append(delimiterChars, p.Advance())
					depth = 1
					for !(p.AtEnd()) && depth > 0 {
						c = p.Peek()
						if c == "[" {
							depth += 1
						} else if c == "]" {
							depth -= 1
						}
						delimiterChars = append(delimiterChars, p.Advance())
					}
				}
			} else if ch == "`" {
				delimiterChars = append(delimiterChars, p.Advance())
				for !(p.AtEnd()) && p.Peek() != "`" {
					c = p.Peek()
					if c == "'" {
						delimiterChars = append(delimiterChars, p.Advance())
						for !(p.AtEnd()) && p.Peek() != "'" && p.Peek() != "`" {
							delimiterChars = append(delimiterChars, p.Advance())
						}
						if !(p.AtEnd()) && p.Peek() == "'" {
							delimiterChars = append(delimiterChars, p.Advance())
						}
					} else if c == "\"" {
						delimiterChars = append(delimiterChars, p.Advance())
						for !(p.AtEnd()) && p.Peek() != "\"" && p.Peek() != "`" {
							if p.Peek() == "\\" && p.Pos+1 < p.Length {
								delimiterChars = append(delimiterChars, p.Advance())
							}
							delimiterChars = append(delimiterChars, p.Advance())
						}
						if !(p.AtEnd()) && p.Peek() == "\"" {
							delimiterChars = append(delimiterChars, p.Advance())
						}
					} else if c == "\\" && p.Pos+1 < p.Length {
						delimiterChars = append(delimiterChars, p.Advance())
						delimiterChars = append(delimiterChars, p.Advance())
					} else {
						delimiterChars = append(delimiterChars, p.Advance())
					}
				}
				if !(p.AtEnd()) {
					delimiterChars = append(delimiterChars, p.Advance())
				}
			} else {
				delimiterChars = append(delimiterChars, p.Advance())
			}
		}
		if !(p.AtEnd()) && strings.Contains("<>", p.Peek()) && p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "(" {
			delimiterChars = append(delimiterChars, p.Advance())
			delimiterChars = append(delimiterChars, p.Advance())
			depth = 1
			for !(p.AtEnd()) && depth > 0 {
				c = p.Peek()
				if c == "(" {
					depth += 1
				} else if c == ")" {
					depth -= 1
				}
				delimiterChars = append(delimiterChars, p.Advance())
			}
			continue
		}
		break
	}
	return strings.Join(delimiterChars, ""), quoted
}

func (p *Parser) _ReadHeredocLine(quoted bool) (string, int) {
	var line string
	var trailingBs int
	var nextLineStart int
	lineStart := p.Pos
	lineEnd := p.Pos
	for lineEnd < p.Length && string(p.Source_runes[lineEnd]) != "\n" {
		lineEnd += 1
	}
	line = _Substring(p.Source, lineStart, lineEnd)
	if !(quoted) {
		for lineEnd < p.Length {
			trailingBs = _CountTrailingBackslashes(line)
			if trailingBs%2 == 0 {
				break
			}
			line = _Substring(line, 0, _runeLen(line)-1)
			lineEnd += 1
			nextLineStart = lineEnd
			for lineEnd < p.Length && string(p.Source_runes[lineEnd]) != "\n" {
				lineEnd += 1
			}
			line = line + _Substring(p.Source, nextLineStart, lineEnd)
		}
	}
	return line, lineEnd
}

func (p *Parser) _LineMatchesDelimiter(line string, delimiter string, stripTabs bool) (bool, string) {
	checkLine := _ternary(stripTabs, strings.TrimLeft(line, "\t"), line)
	normalizedCheck := _NormalizeHeredocDelimiter(checkLine)
	normalizedDelim := _NormalizeHeredocDelimiter(delimiter)
	return normalizedCheck == normalizedDelim, checkLine
}

func (p *Parser) _GatherHeredocBodies() {
	for _, heredocNode := range p._Pending_heredocs {
		heredoc := heredocNode.(*HereDoc)
		var contentLines []string
		lineStart := p.Pos

		for p.Pos < p.Length {
			lineStart = p.Pos
			line, lineEnd := p._ReadHeredocLine(heredoc.Quoted)
			matches, checkLine := p._LineMatchesDelimiter(line, heredoc.Delimiter, heredoc.Strip_tabs)

			if matches {
				if lineEnd < p.Length {
					p.Pos = lineEnd + 1
				} else {
					p.Pos = lineEnd
				}
				break
			}

			// Check for delimiter followed by cmdsub/procsub closer
			normalizedCheck := _NormalizeHeredocDelimiter(checkLine)
			normalizedDelim := _NormalizeHeredocDelimiter(heredoc.Delimiter)

			// In command substitution: line starts with delimiter
			if p._Eof_token == ")" && strings.HasPrefix(normalizedCheck, normalizedDelim) {
				tabsStripped := len(line) - len(checkLine)
				p.Pos = lineStart + tabsStripped + len(heredoc.Delimiter)
				break
			}

			// At EOF with line starting with delimiter (process sub case)
			if lineEnd >= p.Length &&
				strings.HasPrefix(normalizedCheck, normalizedDelim) &&
				p._In_process_sub {
				tabsStripped := len(line) - len(checkLine)
				p.Pos = lineStart + tabsStripped + len(heredoc.Delimiter)
				break
			}

			// Add line to content
			contentLine := line
			if heredoc.Strip_tabs {
				contentLine = strings.TrimLeft(line, "\t")
			}

			if lineEnd < p.Length {
				contentLines = append(contentLines, contentLine+"\n")
				p.Pos = lineEnd + 1
			} else {
				// EOF - bash keeps trailing newline unless escaped
				addNewline := true
				if !heredoc.Quoted && _CountTrailingBackslashes(line)%2 == 1 {
					addNewline = false
				}
				if addNewline {
					contentLines = append(contentLines, contentLine+"\n")
				} else {
					contentLines = append(contentLines, contentLine)
				}
				p.Pos = p.Length
			}
		}

		heredoc.Content = strings.Join(contentLines, "")
	}
	p._Pending_heredocs = []Node{}
}

func (p *Parser) _ParseHeredoc(fd int, stripTabs bool) *HereDoc {
	startPos := p.Pos
	p._SetState(ParserStateFlags_PST_HEREDOC)
	delimiter, quoted := p._ParseHeredocDelimiter()
	for _, existing := range p._Pending_heredocs {
		h := existing.(*HereDoc)
		if h._Start_pos == startPos && h.Delimiter == delimiter {
			p._ClearState(ParserStateFlags_PST_HEREDOC)
			return h
		}
	}
	heredoc := NewHereDoc(delimiter, "", stripTabs, quoted, fd, false)
	heredoc._Start_pos = startPos
	p._Pending_heredocs = append(p._Pending_heredocs, heredoc)
	p._ClearState(ParserStateFlags_PST_HEREDOC)
	return heredoc
}

func (p *Parser) ParseCommand() *Command {
	var reserved string
	var redirect interface{}
	var allAssignments bool
	var inAssignBuiltin bool
	var word *Word
	words := []Node{}
	redirects := []Node{}
	for true {
		p.SkipWhitespace()
		if p._LexIsCommandTerminator() {
			break
		}
		if len(words) == 0 {
			reserved = p._LexPeekReservedWord()
			if reserved == "}" || reserved == "]]" {
				break
			}
		}
		redirect = p.ParseRedirect()
		if redirect != nil {
			redirects = append(redirects, redirect.(Node))
			continue
		}
		allAssignments = true
		for _, w := range words {
			if !(p._IsAssignmentWord(w)) {
				allAssignments = false
				break
			}
		}
		inAssignBuiltin = len(words) > 0 && AssignmentBuiltins[words[0].(*Word).Value]
		word = p.ParseWord(!(len(words) > 0) || allAssignments && len(redirects) == 0, false, inAssignBuiltin)
		if word == nil {
			break
		}
		words = append(words, word)
	}
	if !(len(words) > 0) && !(len(redirects) > 0) {
		return nil
	}
	return NewCommand(words, redirects)
}

func (p *Parser) ParseSubshell() *Subshell {
	p.SkipWhitespace()
	if p.AtEnd() || p.Peek() != "(" {
		return nil
	}
	p.Advance()
	p._SetState(ParserStateFlags_PST_SUBSHELL)
	body := p.ParseList(true)
	if _isNilNode(body) {
		p._ClearState(ParserStateFlags_PST_SUBSHELL)
		panic(NewParseError("Expected command in subshell", p.Pos, 0))
	}
	p.SkipWhitespace()
	if p.AtEnd() || p.Peek() != ")" {
		p._ClearState(ParserStateFlags_PST_SUBSHELL)
		panic(NewParseError("Expected ) to close subshell", p.Pos, 0))
	}
	p.Advance()
	p._ClearState(ParserStateFlags_PST_SUBSHELL)
	return NewSubshell(body, p._CollectRedirects())
}

func (p *Parser) ParseArithmeticCommand() *ArithmeticCommand {
	var c string
	p.SkipWhitespace()
	if p.AtEnd() || p.Peek() != "(" || p.Pos+1 >= p.Length || string(p.Source_runes[p.Pos+1]) != "(" {
		return nil
	}
	savedPos := p.Pos
	p.Advance()
	p.Advance()
	contentStart := p.Pos
	depth := 1
	for !(p.AtEnd()) && depth > 0 {
		c = p.Peek()
		if c == "'" {
			p.Advance()
			for !(p.AtEnd()) && p.Peek() != "'" {
				p.Advance()
			}
			if !(p.AtEnd()) {
				p.Advance()
			}
		} else if c == "\"" {
			p.Advance()
			for !(p.AtEnd()) {
				if p.Peek() == "\\" && p.Pos+1 < p.Length {
					p.Advance()
					p.Advance()
				} else if p.Peek() == "\"" {
					p.Advance()
					break
				} else {
					p.Advance()
				}
			}
		} else if c == "\\" && p.Pos+1 < p.Length {
			p.Advance()
			p.Advance()
		} else if c == "(" {
			depth += 1
			p.Advance()
		} else if c == ")" {
			if depth == 1 && p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == ")" {
				break
			}
			depth -= 1
			if depth == 0 {
				p.Pos = savedPos
				return nil
			}
			p.Advance()
		} else {
			p.Advance()
		}
	}
	if p.AtEnd() {
		panic(NewMatchedPairError("unexpected EOF looking for `))'", savedPos, 0))
	}
	if depth != 1 {
		p.Pos = savedPos
		return nil
	}
	content := _Substring(p.Source, contentStart, p.Pos)
	content = strings.ReplaceAll(content, "\\\n", "")
	p.Advance()
	p.Advance()
	expr := p._ParseArithExpr(content)
	return NewArithmeticCommand(expr, p._CollectRedirects(), content)
}

func (p *Parser) ParseConditionalExpr() *ConditionalExpr {
	p.SkipWhitespace()
	if p.AtEnd() || p.Peek() != "[" || p.Pos+1 >= p.Length || string(p.Source_runes[p.Pos+1]) != "[" {
		return nil
	}
	nextPos := p.Pos + 2
	if nextPos < p.Length && !(_IsWhitespace(string(p.Source_runes[nextPos])) || string(p.Source_runes[nextPos]) == "\\" && nextPos+1 < p.Length && string(p.Source_runes[nextPos+1]) == "\n") {
		return nil
	}
	p.Advance()
	p.Advance()
	p._SetState(ParserStateFlags_PST_CONDEXPR)
	p._Word_context = WordCtxCond
	body := p._ParseCondOr()
	for !(p.AtEnd()) && _IsWhitespaceNoNewline(p.Peek()) {
		p.Advance()
	}
	if p.AtEnd() || p.Peek() != "]" || p.Pos+1 >= p.Length || string(p.Source_runes[p.Pos+1]) != "]" {
		p._ClearState(ParserStateFlags_PST_CONDEXPR)
		p._Word_context = WordCtxNormal
		panic(NewParseError("Expected ]] to close conditional expression", p.Pos, 0))
	}
	p.Advance()
	p.Advance()
	p._ClearState(ParserStateFlags_PST_CONDEXPR)
	p._Word_context = WordCtxNormal
	return NewConditionalExpr(body, p._CollectRedirects())
}

func (p *Parser) _CondSkipWhitespace() {
	for !(p.AtEnd()) {
		if _IsWhitespaceNoNewline(p.Peek()) {
			p.Advance()
		} else if p.Peek() == "\\" && p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "\n" {
			p.Advance()
			p.Advance()
		} else if p.Peek() == "\n" {
			p.Advance()
		} else {
			break
		}
	}
}

func (p *Parser) _CondAtEnd() bool {
	return p.AtEnd() || p.Peek() == "]" && p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "]"
}

func (p *Parser) _ParseCondOr() Node {
	var right Node
	p._CondSkipWhitespace()
	left := p._ParseCondAnd()
	p._CondSkipWhitespace()
	if !(p._CondAtEnd()) && p.Peek() == "|" && p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "|" {
		p.Advance()
		p.Advance()
		right = p._ParseCondOr()
		return NewCondOr(left, right)
	}
	return left
}

func (p *Parser) _ParseCondAnd() Node {
	var right Node
	p._CondSkipWhitespace()
	left := p._ParseCondTerm()
	p._CondSkipWhitespace()
	if !(p._CondAtEnd()) && p.Peek() == "&" && p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "&" {
		p.Advance()
		p.Advance()
		right = p._ParseCondAnd()
		return NewCondAnd(left, right)
	}
	return left
}

func (p *Parser) _ParseCondTerm() Node {
	var operand Node
	var inner Node
	var op string
	var word2 *Word
	var savedPos int
	var opWord *Word
	p._CondSkipWhitespace()
	if p._CondAtEnd() {
		panic(NewParseError("Unexpected end of conditional expression", p.Pos, 0))
	}
	if p.Peek() == "!" {
		if p.Pos+1 < p.Length && !(_IsWhitespaceNoNewline(string(p.Source_runes[p.Pos+1]))) {
		} else {
			p.Advance()
			operand = p._ParseCondTerm()
			return NewCondNot(operand)
		}
	}
	if p.Peek() == "(" {
		p.Advance()
		inner = p._ParseCondOr()
		p._CondSkipWhitespace()
		if p.AtEnd() || p.Peek() != ")" {
			panic(NewParseError("Expected ) in conditional expression", p.Pos, 0))
		}
		p.Advance()
		return NewCondParen(inner)
	}
	word1 := p._ParseCondWord()
	if word1 == nil {
		panic(NewParseError("Expected word in conditional expression", p.Pos, 0))
	}
	p._CondSkipWhitespace()
	if CondUnaryOps[word1.Value] {
		operand = p._ParseCondWord()
		if _isNilNode(operand) {
			panic(NewParseError("Expected operand after "+word1.Value, p.Pos, 0))
		}
		return NewUnaryTest(word1.Value, operand)
	}
	if !(p._CondAtEnd()) && p.Peek() != "&" && p.Peek() != "|" && p.Peek() != ")" {
		if _IsRedirectChar(p.Peek()) && !(p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "(") {
			op = p.Advance()
			p._CondSkipWhitespace()
			word2 = p._ParseCondWord()
			if word2 == nil {
				panic(NewParseError("Expected operand after "+op, p.Pos, 0))
			}
			return NewBinaryTest(op, word1, word2)
		}
		savedPos = p.Pos
		opWord = p._ParseCondWord()
		if opWord != nil && CondBinaryOps[opWord.Value] {
			p._CondSkipWhitespace()
			if opWord.Value == "=~" {
				word2 = p._ParseCondRegexWord()
			} else {
				word2 = p._ParseCondWord()
			}
			if word2 == nil {
				panic(NewParseError("Expected operand after "+opWord.Value, p.Pos, 0))
			}
			return NewBinaryTest(opWord.Value, word1, word2)
		} else {
			p.Pos = savedPos
		}
	}
	return NewUnaryTest("-n", word1)
}

func (p *Parser) _ParseCondWord() *Word {
	p._CondSkipWhitespace()
	if p._CondAtEnd() {
		return nil
	}
	c := p.Peek()
	if _IsParen(c) {
		return nil
	}
	if c == "&" && p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "&" {
		return nil
	}
	if c == "|" && p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "|" {
		return nil
	}
	return p._ParseWordInternal(WordCtxCond, false, false)
}

func (p *Parser) _ParseCondRegexWord() *Word {
	p._CondSkipWhitespace()
	if p._CondAtEnd() {
		return nil
	}
	p._SetState(ParserStateFlags_PST_REGEXP)
	result := p._ParseWordInternal(WordCtxRegex, false, false)
	p._ClearState(ParserStateFlags_PST_REGEXP)
	p._Word_context = WordCtxCond
	return result
}

func (p *Parser) ParseBraceGroup() *BraceGroup {
	p.SkipWhitespace()
	if !(p._LexConsumeWord("{")) {
		return nil
	}
	p.SkipWhitespaceAndNewlines()
	body := p.ParseList(true)
	if _isNilNode(body) {
		panic(NewParseError("Expected command in brace group", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespace()
	if !(p._LexConsumeWord("}")) {
		panic(NewParseError("Expected } to close brace group", p._LexPeekToken().Pos, 0))
	}
	return NewBraceGroup(body, p._CollectRedirects())
}

func (p *Parser) ParseIf() *If {
	var elseBody Node
	var elifCondition Node
	var elifThenBody Node
	var innerElse Node
	p.SkipWhitespace()
	if !(p._LexConsumeWord("if")) {
		return nil
	}
	condition := p.ParseListUntil(map[string]struct{}{"then": {}})
	if _isNilNode(condition) {
		panic(NewParseError("Expected condition after 'if'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("then")) {
		panic(NewParseError("Expected 'then' after if condition", p._LexPeekToken().Pos, 0))
	}
	thenBody := p.ParseListUntil(map[string]struct{}{"elif": {}, "else": {}, "fi": {}})
	if _isNilNode(thenBody) {
		panic(NewParseError("Expected commands after 'then'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	elseBody = nil
	if p._LexIsAtReservedWord("elif") {
		p._LexConsumeWord("elif")
		elifCondition = p.ParseListUntil(map[string]struct{}{"then": {}})
		if _isNilNode(elifCondition) {
			panic(NewParseError("Expected condition after 'elif'", p._LexPeekToken().Pos, 0))
		}
		p.SkipWhitespaceAndNewlines()
		if !(p._LexConsumeWord("then")) {
			panic(NewParseError("Expected 'then' after elif condition", p._LexPeekToken().Pos, 0))
		}
		elifThenBody = p.ParseListUntil(map[string]struct{}{"elif": {}, "else": {}, "fi": {}})
		if _isNilNode(elifThenBody) {
			panic(NewParseError("Expected commands after 'then'", p._LexPeekToken().Pos, 0))
		}
		p.SkipWhitespaceAndNewlines()
		innerElse = nil
		if p._LexIsAtReservedWord("elif") {
			innerElse = p._ParseElifChain()
		} else if p._LexIsAtReservedWord("else") {
			p._LexConsumeWord("else")
			innerElse = p.ParseListUntil(map[string]struct{}{"fi": {}})
			if _isNilNode(innerElse) {
				panic(NewParseError("Expected commands after 'else'", p._LexPeekToken().Pos, 0))
			}
		}
		elseBody = NewIf(elifCondition, elifThenBody, innerElse, nil)
	} else if p._LexIsAtReservedWord("else") {
		p._LexConsumeWord("else")
		elseBody = p.ParseListUntil(map[string]struct{}{"fi": {}})
		if _isNilNode(elseBody) {
			panic(NewParseError("Expected commands after 'else'", p._LexPeekToken().Pos, 0))
		}
	}
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("fi")) {
		panic(NewParseError("Expected 'fi' to close if statement", p._LexPeekToken().Pos, 0))
	}
	return NewIf(condition, thenBody, elseBody, p._CollectRedirects())
}

func (p *Parser) _ParseElifChain() *If {
	var elseBody Node
	p._LexConsumeWord("elif")
	condition := p.ParseListUntil(map[string]struct{}{"then": {}})
	if _isNilNode(condition) {
		panic(NewParseError("Expected condition after 'elif'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("then")) {
		panic(NewParseError("Expected 'then' after elif condition", p._LexPeekToken().Pos, 0))
	}
	thenBody := p.ParseListUntil(map[string]struct{}{"elif": {}, "else": {}, "fi": {}})
	if _isNilNode(thenBody) {
		panic(NewParseError("Expected commands after 'then'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	elseBody = nil
	if p._LexIsAtReservedWord("elif") {
		elseBody = p._ParseElifChain()
	} else if p._LexIsAtReservedWord("else") {
		p._LexConsumeWord("else")
		elseBody = p.ParseListUntil(map[string]struct{}{"fi": {}})
		if _isNilNode(elseBody) {
			panic(NewParseError("Expected commands after 'else'", p._LexPeekToken().Pos, 0))
		}
	}
	return NewIf(condition, thenBody, elseBody, nil)
}

func (p *Parser) ParseWhile() *While {
	p.SkipWhitespace()
	if !(p._LexConsumeWord("while")) {
		return nil
	}
	condition := p.ParseListUntil(map[string]struct{}{"do": {}})
	if _isNilNode(condition) {
		panic(NewParseError("Expected condition after 'while'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("do")) {
		panic(NewParseError("Expected 'do' after while condition", p._LexPeekToken().Pos, 0))
	}
	body := p.ParseListUntil(map[string]struct{}{"done": {}})
	if _isNilNode(body) {
		panic(NewParseError("Expected commands after 'do'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("done")) {
		panic(NewParseError("Expected 'done' to close while loop", p._LexPeekToken().Pos, 0))
	}
	return NewWhile(condition, body, p._CollectRedirects())
}

func (p *Parser) ParseUntil() *Until {
	p.SkipWhitespace()
	if !(p._LexConsumeWord("until")) {
		return nil
	}
	condition := p.ParseListUntil(map[string]struct{}{"do": {}})
	if _isNilNode(condition) {
		panic(NewParseError("Expected condition after 'until'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("do")) {
		panic(NewParseError("Expected 'do' after until condition", p._LexPeekToken().Pos, 0))
	}
	body := p.ParseListUntil(map[string]struct{}{"done": {}})
	if _isNilNode(body) {
		panic(NewParseError("Expected commands after 'do'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("done")) {
		panic(NewParseError("Expected 'done' to close until loop", p._LexPeekToken().Pos, 0))
	}
	return NewUntil(condition, body, p._CollectRedirects())
}

func (p *Parser) ParseFor() Node {
	var varWord *Word
	var varName string
	var words []Node
	var sawDelimiter bool
	var word *Word
	var braceGroup *BraceGroup
	p.SkipWhitespace()
	if !(p._LexConsumeWord("for")) {
		return nil
	}
	p.SkipWhitespace()
	if p.Peek() == "(" && p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "(" {
		return p._ParseForArith()
	}
	if p.Peek() == "$" {
		varWord = p.ParseWord(false, false, false)
		if varWord == nil {
			panic(NewParseError("Expected variable name after 'for'", p._LexPeekToken().Pos, 0))
		}
		varName = varWord.Value
	} else {
		varName = p.PeekWord()
		if varName == "" {
			panic(NewParseError("Expected variable name after 'for'", p._LexPeekToken().Pos, 0))
		}
		p.ConsumeWord(varName)
	}
	p.SkipWhitespace()
	if p.Peek() == ";" {
		p.Advance()
	}
	p.SkipWhitespaceAndNewlines()
	words = nil
	if p._LexIsAtReservedWord("in") {
		p._LexConsumeWord("in")
		p.SkipWhitespace()
		sawDelimiter = _IsSemicolonOrNewline(p.Peek())
		if p.Peek() == ";" {
			p.Advance()
		}
		p.SkipWhitespaceAndNewlines()
		words = []Node{}
		for true {
			p.SkipWhitespace()
			if p.AtEnd() {
				break
			}
			if _IsSemicolonOrNewline(p.Peek()) {
				sawDelimiter = true
				if p.Peek() == ";" {
					p.Advance()
				}
				break
			}
			if p._LexIsAtReservedWord("do") {
				if sawDelimiter {
					break
				}
				panic(NewParseError("Expected ';' or newline before 'do'", p._LexPeekToken().Pos, 0))
			}
			word = p.ParseWord(false, false, false)
			if word == nil {
				break
			}
			words = append(words, word)
		}
	}
	p.SkipWhitespaceAndNewlines()
	if p.Peek() == "{" {
		braceGroup = p.ParseBraceGroup()
		if braceGroup == nil {
			panic(NewParseError("Expected brace group in for loop", p._LexPeekToken().Pos, 0))
		}
		return NewFor(varName, words, braceGroup.Body, p._CollectRedirects())
	}
	if !(p._LexConsumeWord("do")) {
		panic(NewParseError("Expected 'do' in for loop", p._LexPeekToken().Pos, 0))
	}
	body := p.ParseListUntil(map[string]struct{}{"done": {}})
	if _isNilNode(body) {
		panic(NewParseError("Expected commands after 'do'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("done")) {
		panic(NewParseError("Expected 'done' to close for loop", p._LexPeekToken().Pos, 0))
	}
	return NewFor(varName, words, body, p._CollectRedirects())
}

func (p *Parser) _ParseForArith() *ForArith {
	var current []string
	var ch string
	p.Advance()
	p.Advance()
	parts := []string{}
	current = []string{}
	parenDepth := 0
	for !(p.AtEnd()) {
		ch = p.Peek()
		if ch == "(" {
			parenDepth += 1
			current = append(current, p.Advance())
		} else if ch == ")" {
			if parenDepth > 0 {
				parenDepth -= 1
				current = append(current, p.Advance())
			} else if p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == ")" {
				parts = append(parts, strings.TrimLeft(strings.Join(current, ""), " \t"))
				p.Advance()
				p.Advance()
				break
			} else {
				current = append(current, p.Advance())
			}
		} else if ch == ";" && parenDepth == 0 {
			parts = append(parts, strings.TrimLeft(strings.Join(current, ""), " \t"))
			current = []string{}
			p.Advance()
		} else {
			current = append(current, p.Advance())
		}
	}
	if len(parts) != 3 {
		panic(NewParseError("Expected three expressions in for ((;;))", p.Pos, 0))
	}
	init := parts[0]
	cond := parts[1]
	incr := parts[2]
	p.SkipWhitespace()
	if !(p.AtEnd()) && p.Peek() == ";" {
		p.Advance()
	}
	p.SkipWhitespaceAndNewlines()
	body := p._ParseLoopBody("for loop")
	return NewForArith(init, cond, incr, body, p._CollectRedirects())
}

func (p *Parser) ParseSelect() *Select {
	var words []Node
	var word *Word
	p.SkipWhitespace()
	if !(p._LexConsumeWord("select")) {
		return nil
	}
	p.SkipWhitespace()
	varName := p.PeekWord()
	if varName == "" {
		panic(NewParseError("Expected variable name after 'select'", p._LexPeekToken().Pos, 0))
	}
	p.ConsumeWord(varName)
	p.SkipWhitespace()
	if p.Peek() == ";" {
		p.Advance()
	}
	p.SkipWhitespaceAndNewlines()
	words = nil
	if p._LexIsAtReservedWord("in") {
		p._LexConsumeWord("in")
		p.SkipWhitespaceAndNewlines()
		words = []Node{}
		for true {
			p.SkipWhitespace()
			if p.AtEnd() {
				break
			}
			if _IsSemicolonNewlineBrace(p.Peek()) {
				if p.Peek() == ";" {
					p.Advance()
				}
				break
			}
			if p._LexIsAtReservedWord("do") {
				break
			}
			word = p.ParseWord(false, false, false)
			if word == nil {
				break
			}
			words = append(words, word)
		}
	}
	p.SkipWhitespaceAndNewlines()
	body := p._ParseLoopBody("select")
	return NewSelect(varName, words, body, p._CollectRedirects())
}

func (p *Parser) _ConsumeCaseTerminator() string {
	term := p._LexPeekCaseTerminator()
	if term != "" {
		p._LexNextToken()
		return term
	}
	return ";;"
}

func (p *Parser) ParseCase() *Case {
	var saved int
	var isPattern bool
	var nextCh string
	var patternChars []string
	var extglobDepth int
	var ch string
	var parenDepth int
	var c string
	var isCharClass bool
	var scanPos int
	var scanDepth int
	var hasFirstBracketLiteral bool
	var sc string
	var pattern string
	var body Node
	var isEmptyBody bool
	var isAtTerminator bool
	var terminator string
	if !(p.ConsumeWord("case")) {
		return nil
	}
	p._SetState(ParserStateFlags_PST_CASESTMT)
	p.SkipWhitespace()
	word := p.ParseWord(false, false, false)
	if word == nil {
		panic(NewParseError("Expected word after 'case'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("in")) {
		panic(NewParseError("Expected 'in' after case word", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	patterns := []Node{}
	p._SetState(ParserStateFlags_PST_CASEPAT)
	for true {
		p.SkipWhitespaceAndNewlines()
		if p._LexIsAtReservedWord("esac") {
			saved = p.Pos
			p.SkipWhitespace()
			for !(p.AtEnd()) && !(_IsMetachar(p.Peek())) && !(_IsQuote(p.Peek())) {
				p.Advance()
			}
			p.SkipWhitespace()
			isPattern = false
			if !(p.AtEnd()) && p.Peek() == ")" {
				if p._Eof_token == ")" {
					isPattern = false
				} else {
					p.Advance()
					p.SkipWhitespace()
					if !(p.AtEnd()) {
						nextCh = p.Peek()
						if nextCh == ";" {
							isPattern = true
						} else if !(_IsNewlineOrRightParen(nextCh)) {
							isPattern = true
						}
					}
				}
			}
			p.Pos = saved
			if !(isPattern) {
				break
			}
		}
		p.SkipWhitespaceAndNewlines()
		if !(p.AtEnd()) && p.Peek() == "(" {
			p.Advance()
			p.SkipWhitespaceAndNewlines()
		}
		patternChars = []string{}
		extglobDepth = 0
		for !(p.AtEnd()) {
			ch = p.Peek()
			if ch == ")" {
				if extglobDepth > 0 {
					patternChars = append(patternChars, p.Advance())
					extglobDepth -= 1
				} else {
					p.Advance()
					break
				}
			} else if ch == "\\" {
				if p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "\n" {
					p.Advance()
					p.Advance()
				} else {
					patternChars = append(patternChars, p.Advance())
					if !(p.AtEnd()) {
						patternChars = append(patternChars, p.Advance())
					}
				}
			} else if _IsExpansionStart(p.Source, p.Pos, "$(") {
				patternChars = append(patternChars, p.Advance())
				patternChars = append(patternChars, p.Advance())
				if !(p.AtEnd()) && p.Peek() == "(" {
					patternChars = append(patternChars, p.Advance())
					parenDepth = 2
					for !(p.AtEnd()) && parenDepth > 0 {
						c = p.Peek()
						if c == "(" {
							parenDepth += 1
						} else if c == ")" {
							parenDepth -= 1
						}
						patternChars = append(patternChars, p.Advance())
					}
				} else {
					extglobDepth += 1
				}
			} else if ch == "(" && extglobDepth > 0 {
				patternChars = append(patternChars, p.Advance())
				extglobDepth += 1
			} else if p._Extglob && _IsExtglobPrefix(ch) && p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "(" {
				patternChars = append(patternChars, p.Advance())
				patternChars = append(patternChars, p.Advance())
				extglobDepth += 1
			} else if ch == "[" {
				isCharClass = false
				scanPos = p.Pos + 1
				scanDepth = 0
				hasFirstBracketLiteral = false
				if scanPos < p.Length && _IsCaretOrBang(string(p.Source_runes[scanPos])) {
					scanPos += 1
				}
				if scanPos < p.Length && string(p.Source_runes[scanPos]) == "]" {
					if strings.Index(p.Source, "]") != -1 {
						scanPos += 1
						hasFirstBracketLiteral = true
					}
				}
				for scanPos < p.Length {
					sc = string(p.Source_runes[scanPos])
					if sc == "]" && scanDepth == 0 {
						isCharClass = true
						break
					} else if sc == "[" {
						scanDepth += 1
					} else if sc == ")" && scanDepth == 0 {
						break
					} else if sc == "|" && scanDepth == 0 {
						break
					}
					scanPos += 1
				}
				if isCharClass {
					patternChars = append(patternChars, p.Advance())
					if !(p.AtEnd()) && _IsCaretOrBang(p.Peek()) {
						patternChars = append(patternChars, p.Advance())
					}
					if hasFirstBracketLiteral && !(p.AtEnd()) && p.Peek() == "]" {
						patternChars = append(patternChars, p.Advance())
					}
					for !(p.AtEnd()) && p.Peek() != "]" {
						patternChars = append(patternChars, p.Advance())
					}
					if !(p.AtEnd()) {
						patternChars = append(patternChars, p.Advance())
					}
				} else {
					patternChars = append(patternChars, p.Advance())
				}
			} else if ch == "'" {
				patternChars = append(patternChars, p.Advance())
				for !(p.AtEnd()) && p.Peek() != "'" {
					patternChars = append(patternChars, p.Advance())
				}
				if !(p.AtEnd()) {
					patternChars = append(patternChars, p.Advance())
				}
			} else if ch == "\"" {
				patternChars = append(patternChars, p.Advance())
				for !(p.AtEnd()) && p.Peek() != "\"" {
					if p.Peek() == "\\" && p.Pos+1 < p.Length {
						patternChars = append(patternChars, p.Advance())
					}
					patternChars = append(patternChars, p.Advance())
				}
				if !(p.AtEnd()) {
					patternChars = append(patternChars, p.Advance())
				}
			} else if _IsWhitespace(ch) {
				if extglobDepth > 0 {
					patternChars = append(patternChars, p.Advance())
				} else {
					p.Advance()
				}
			} else {
				patternChars = append(patternChars, p.Advance())
			}
		}
		pattern = strings.Join(patternChars, "")
		if !(len(pattern) > 0) {
			panic(NewParseError("Expected pattern in case statement", p._LexPeekToken().Pos, 0))
		}
		p.SkipWhitespace()
		body = nil
		isEmptyBody = p._LexPeekCaseTerminator() != ""
		if !(isEmptyBody) {
			p.SkipWhitespaceAndNewlines()
			if !(p.AtEnd()) && !(p._LexIsAtReservedWord("esac")) {
				isAtTerminator = p._LexPeekCaseTerminator() != ""
				if !(isAtTerminator) {
					body = p.ParseListUntil(map[string]struct{}{"esac": {}})
					p.SkipWhitespace()
				}
			}
		}
		terminator = p._ConsumeCaseTerminator()
		p.SkipWhitespaceAndNewlines()
		patterns = append(patterns, NewCasePattern(pattern, body, terminator))
	}
	p._ClearState(ParserStateFlags_PST_CASEPAT)
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("esac")) {
		p._ClearState(ParserStateFlags_PST_CASESTMT)
		panic(NewParseError("Expected 'esac' to close case statement", p._LexPeekToken().Pos, 0))
	}
	p._ClearState(ParserStateFlags_PST_CASESTMT)
	return NewCase(word, patterns, p._CollectRedirects())
}

func (p *Parser) ParseCoproc() *Coproc {
	var name string
	var ch string
	var body Node
	var nextWord string
	p.SkipWhitespace()
	if !(p._LexConsumeWord("coproc")) {
		return nil
	}
	p.SkipWhitespace()
	name = ""
	ch = ""
	if !(p.AtEnd()) {
		ch = p.Peek()
	}
	if ch == "{" {
		body = p.ParseBraceGroup()
		if !_isNilNode(body) {
			return NewCoproc(body, name)
		}
	}
	if ch == "(" {
		if p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "(" {
			body = p.ParseArithmeticCommand()
			if !_isNilNode(body) {
				return NewCoproc(body, name)
			}
		}
		body = p.ParseSubshell()
		if !_isNilNode(body) {
			return NewCoproc(body, name)
		}
	}
	nextWord = p._LexPeekReservedWord()
	if nextWord != "" && CompoundKeywords[nextWord] {
		body = p.ParseCompoundCommand()
		if !_isNilNode(body) {
			return NewCoproc(body, name)
		}
	}
	wordStart := p.Pos
	potentialName := p.PeekWord()
	if len(potentialName) > 0 {
		for !(p.AtEnd()) && !(_IsMetachar(p.Peek())) && !(_IsQuote(p.Peek())) {
			p.Advance()
		}
		p.SkipWhitespace()
		ch = ""
		if !(p.AtEnd()) {
			ch = p.Peek()
		}
		nextWord = p._LexPeekReservedWord()
		if _IsValidIdentifier(potentialName) {
			if ch == "{" {
				name = potentialName
				body = p.ParseBraceGroup()
				if !_isNilNode(body) {
					return NewCoproc(body, name)
				}
			} else if ch == "(" {
				name = potentialName
				if p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "(" {
					body = p.ParseArithmeticCommand()
				} else {
					body = p.ParseSubshell()
				}
				if !_isNilNode(body) {
					return NewCoproc(body, name)
				}
			} else if nextWord != "" && CompoundKeywords[nextWord] {
				name = potentialName
				body = p.ParseCompoundCommand()
				if !_isNilNode(body) {
					return NewCoproc(body, name)
				}
			}
		}
		p.Pos = wordStart
	}
	body = p.ParseCommand()
	if !_isNilNode(body) {
		return NewCoproc(body, name)
	}
	panic(NewParseError("Expected command after coproc", p.Pos, 0))
}

func (p *Parser) ParseFunction() *Function {
	var name string
	var body Node
	p.SkipWhitespace()
	if p.AtEnd() {
		return nil
	}
	savedPos := p.Pos
	if p._LexIsAtReservedWord("function") {
		p._LexConsumeWord("function")
		p.SkipWhitespace()
		name = p.PeekWord()
		if name == "" {
			p.Pos = savedPos
			return nil
		}
		p.ConsumeWord(name)
		p.SkipWhitespace()
		if !(p.AtEnd()) && p.Peek() == "(" {
			if p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == ")" {
				p.Advance()
				p.Advance()
			}
		}
		p.SkipWhitespaceAndNewlines()
		body = p._ParseCompoundCommand()
		if _isNilNode(body) {
			panic(NewParseError("Expected function body", p.Pos, 0))
		}
		return NewFunction(name, body)
	}
	name = p.PeekWord()
	if name == "" || ReservedWords[name] {
		return nil
	}
	if _LooksLikeAssignment(name) {
		return nil
	}
	p.SkipWhitespace()
	nameStart := p.Pos
	for !(p.AtEnd()) && !(_IsMetachar(p.Peek())) && !(_IsQuote(p.Peek())) && !(_IsParen(p.Peek())) {
		p.Advance()
	}
	name = _Substring(p.Source, nameStart, p.Pos)
	if !(len(name) > 0) {
		p.Pos = savedPos
		return nil
	}
	braceDepth := 0
	i := 0
	for i < _runeLen(name) {
		if _IsExpansionStart(name, i, "${") {
			braceDepth += 1
			i += 2
			continue
		}
		if _runeAt(name, i) == "}" {
			braceDepth -= 1
		}
		i += 1
	}
	if braceDepth > 0 {
		p.Pos = savedPos
		return nil
	}
	posAfterName := p.Pos
	p.SkipWhitespace()
	hasWhitespace := p.Pos > posAfterName
	if !(hasWhitespace) && len(name) > 0 && strings.Contains("*?@+!$", _runeAt(name, _runeLen(name)-1)) {
		p.Pos = savedPos
		return nil
	}
	if p.AtEnd() || p.Peek() != "(" {
		p.Pos = savedPos
		return nil
	}
	p.Advance()
	p.SkipWhitespace()
	if p.AtEnd() || p.Peek() != ")" {
		p.Pos = savedPos
		return nil
	}
	p.Advance()
	p.SkipWhitespaceAndNewlines()
	body = p._ParseCompoundCommand()
	if _isNilNode(body) {
		panic(NewParseError("Expected function body", p.Pos, 0))
	}
	return NewFunction(name, body)
}

func (p *Parser) _ParseCompoundCommand() Node {
	if rTmp := p.ParseBraceGroup(); rTmp != nil {
		return rTmp
	}
	if !(p.AtEnd()) && p.Peek() == "(" && p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "(" {
		if rTmp := p.ParseArithmeticCommand(); rTmp != nil {
			return rTmp
		}
	}
	if rTmp := p.ParseSubshell(); rTmp != nil {
		return rTmp
	}
	if rTmp := p.ParseConditionalExpr(); rTmp != nil {
		return rTmp
	}
	if rTmp := p.ParseIf(); rTmp != nil {
		return rTmp
	}
	if rTmp := p.ParseWhile(); rTmp != nil {
		return rTmp
	}
	if rTmp := p.ParseUntil(); rTmp != nil {
		return rTmp
	}
	if rTmp := p.ParseFor(); rTmp != nil {
		return rTmp
	}
	if rTmp := p.ParseCase(); rTmp != nil {
		return rTmp
	}
	if rTmp := p.ParseSelect(); rTmp != nil {
		return rTmp
	}
	return nil
}

func (p *Parser) _AtListUntilTerminator(stopWords map[string]struct{}) bool {
	var nextPos int
	if p.AtEnd() {
		return true
	}
	if p.Peek() == ")" {
		return true
	}
	if p.Peek() == "}" {
		nextPos = p.Pos + 1
		if nextPos >= p.Length || _IsWordEndContext(string(p.Source_runes[nextPos])) {
			return true
		}
	}
	reserved := p._LexPeekReservedWord()
	if reserved != "" && func() bool { _, ok := stopWords[reserved]; return ok }() {
		return true
	}
	if p._LexPeekCaseTerminator() != "" {
		return true
	}
	return false
}

func (p *Parser) ParseListUntil(stopWords map[string]struct{}) Node {
	var pipeline Node
	var op string
	var nextOp string
	p.SkipWhitespaceAndNewlines()
	reserved := p._LexPeekReservedWord()
	if reserved != "" && func() bool { _, ok := stopWords[reserved]; return ok }() {
		return nil
	}
	pipeline = p.ParsePipeline()
	if _isNilNode(pipeline) {
		return nil
	}
	parts := []Node{pipeline}
	for true {
		p.SkipWhitespace()
		op = p.ParseListOperator()
		if op == "" {
			if !(p.AtEnd()) && p.Peek() == "\n" {
				p.Advance()
				p._GatherHeredocBodies()
				if p._Cmdsub_heredoc_end != -1 && p._Cmdsub_heredoc_end > p.Pos {
					p.Pos = p._Cmdsub_heredoc_end
					p._Cmdsub_heredoc_end = -1
				}
				p.SkipWhitespaceAndNewlines()
				if p._AtListUntilTerminator(stopWords) {
					break
				}
				nextOp = p._PeekListOperator()
				if _containsAny([]interface{}{"&", ";"}, nextOp) {
					break
				}
				op = "\n"
			} else {
				break
			}
		}
		if op == "" {
			break
		}
		if op == ";" {
			p.SkipWhitespaceAndNewlines()
			if p._AtListUntilTerminator(stopWords) {
				break
			}
			parts = append(parts, NewOperator(op))
		} else if op == "&" {
			parts = append(parts, NewOperator(op))
			p.SkipWhitespaceAndNewlines()
			if p._AtListUntilTerminator(stopWords) {
				break
			}
		} else if _containsAny([]interface{}{"&&", "||"}, op) {
			parts = append(parts, NewOperator(op))
			p.SkipWhitespaceAndNewlines()
		} else {
			parts = append(parts, NewOperator(op))
		}
		if p._AtListUntilTerminator(stopWords) {
			break
		}
		pipeline = p.ParsePipeline()
		if _isNilNode(pipeline) {
			panic(NewParseError("Expected command after "+op, p.Pos, 0))
		}
		parts = append(parts, pipeline)
	}
	if len(parts) == 1 {
		return parts[0]
	}
	return NewList(parts)
}

func (p *Parser) ParseCompoundCommand() Node {
	var reserved string
	var word string
	var keywordWord string
	p.SkipWhitespace()
	if p.AtEnd() {
		return nil
	}
	ch := p.Peek()
	if ch == "(" && p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "(" {
		if rTmp := p.ParseArithmeticCommand(); rTmp != nil {
			return rTmp
		}
	}
	if ch == "(" {
		return p.ParseSubshell()
	}
	if ch == "{" {
		if rTmp := p.ParseBraceGroup(); rTmp != nil {
			return rTmp
		}
	}
	if ch == "[" && p.Pos+1 < p.Length && string(p.Source_runes[p.Pos+1]) == "[" {
		if rTmp := p.ParseConditionalExpr(); rTmp != nil {
			return rTmp
		}
	}
	reserved = p._LexPeekReservedWord()
	if reserved == "" && p._In_process_sub {
		word = p.PeekWord()
		if word != "" && _runeLen(word) > 1 && _runeAt(word, 0) == "}" {
			keywordWord = _Substring(word, 1, _runeLen(word))
			if ReservedWords[keywordWord] || _containsAny([]interface{}{"{", "}", "[[", "]]", "!", "time"}, keywordWord) {
				reserved = keywordWord
			}
		}
	}
	if _containsAny([]interface{}{"fi", "then", "elif", "else", "done", "esac", "do", "in"}, reserved) {
		panic(NewParseError(fmt.Sprintf("Unexpected reserved word '%v'", reserved), p._LexPeekToken().Pos, 0))
	}
	if reserved == "if" {
		return p.ParseIf()
	}
	if reserved == "while" {
		return p.ParseWhile()
	}
	if reserved == "until" {
		return p.ParseUntil()
	}
	if reserved == "for" {
		return p.ParseFor()
	}
	if reserved == "select" {
		return p.ParseSelect()
	}
	if reserved == "case" {
		return p.ParseCase()
	}
	if reserved == "function" {
		return p.ParseFunction()
	}
	if reserved == "coproc" {
		return p.ParseCoproc()
	}
	if fTmp := p.ParseFunction(); fTmp != nil {
		return fTmp
	}
	return p.ParseCommand()
}

func (p *Parser) ParsePipeline() Node {
	var prefixOrder string
	var timePosix bool
	var saved int
	var inner Node
	var result Node
	p.SkipWhitespace()
	prefixOrder = ""
	timePosix = false
	if p._LexIsAtReservedWord("time") {
		p._LexConsumeWord("time")
		prefixOrder = "time"
		p.SkipWhitespace()
		if !(p.AtEnd()) && p.Peek() == "-" {
			saved = p.Pos
			p.Advance()
			if !(p.AtEnd()) && p.Peek() == "p" {
				p.Advance()
				if p.AtEnd() || _IsMetachar(p.Peek()) {
					timePosix = true
				} else {
					p.Pos = saved
				}
			} else {
				p.Pos = saved
			}
		}
		p.SkipWhitespace()
		if !(p.AtEnd()) && strings.HasPrefix(p.Source[p.Pos:], "--") {
			if p.Pos+2 >= p.Length || _IsWhitespace(string(p.Source_runes[p.Pos+2])) {
				p.Advance()
				p.Advance()
				timePosix = true
				p.SkipWhitespace()
			}
		}
		for p._LexIsAtReservedWord("time") {
			p._LexConsumeWord("time")
			p.SkipWhitespace()
			if !(p.AtEnd()) && p.Peek() == "-" {
				saved = p.Pos
				p.Advance()
				if !(p.AtEnd()) && p.Peek() == "p" {
					p.Advance()
					if p.AtEnd() || _IsMetachar(p.Peek()) {
						timePosix = true
					} else {
						p.Pos = saved
					}
				} else {
					p.Pos = saved
				}
			}
		}
		p.SkipWhitespace()
		if !(p.AtEnd()) && p.Peek() == "!" {
			if (p.Pos+1 >= p.Length || _IsNegationBoundary(string(p.Source_runes[p.Pos+1]))) && !(p._IsBangFollowedByProcsub()) {
				p.Advance()
				prefixOrder = "time_negation"
				p.SkipWhitespace()
			}
		}
	} else if !(p.AtEnd()) && p.Peek() == "!" {
		if (p.Pos+1 >= p.Length || _IsNegationBoundary(string(p.Source_runes[p.Pos+1]))) && !(p._IsBangFollowedByProcsub()) {
			p.Advance()
			p.SkipWhitespace()
			inner = p.ParsePipeline()
			if i, ok := inner.(*Negation); ok {
				if i.Pipeline != nil {
					return i.Pipeline
				} else {
					return NewCommand([]Node{}, nil)
				}
			}
			return NewNegation(inner)
		}
	}
	result = p._ParseSimplePipeline()
	if prefixOrder == "time" {
		result = NewTime(result, timePosix)
	} else if prefixOrder == "negation" {
		result = NewNegation(result)
	} else if prefixOrder == "time_negation" {
		result = NewTime(result, timePosix)
		result = NewNegation(result)
	} else if prefixOrder == "negation_time" {
		result = NewTime(result, timePosix)
		result = NewNegation(result)
	} else if _isNilNode(result) {
		return nil
	}
	return result
}

func (p *Parser) _ParseSimplePipeline() Node {
	var cmd Node
	var isPipeBoth bool
	cmd = p.ParseCompoundCommand()
	if _isNilNode(cmd) {
		return nil
	}
	commands := []Node{cmd}
	for true {
		p.SkipWhitespace()
		tokenType, value := p._LexPeekOperator()
		_ = tokenType
		_ = value
		if tokenType == 0 {
			break
		}
		if tokenType != TokenType_PIPE && tokenType != TokenType_PIPE_AMP {
			break
		}
		p._LexNextToken()
		isPipeBoth = tokenType == TokenType_PIPE_AMP
		p.SkipWhitespaceAndNewlines()
		if isPipeBoth {
			commands = append(commands, NewPipeBoth())
		}
		cmd = p.ParseCompoundCommand()
		if _isNilNode(cmd) {
			panic(NewParseError("Expected command after |", p.Pos, 0))
		}
		commands = append(commands, cmd)
	}
	if len(commands) == 1 {
		return commands[0]
	}
	return NewPipeline(commands)
}

func (p *Parser) ParseListOperator() string {
	p.SkipWhitespace()
	tokenType, _ := p._LexPeekOperator()
	_ = tokenType
	if tokenType == 0 {
		return ""
	}
	if tokenType == TokenType_AND_AND {
		p._LexNextToken()
		return "&&"
	}
	if tokenType == TokenType_OR_OR {
		p._LexNextToken()
		return "||"
	}
	if tokenType == TokenType_SEMI {
		p._LexNextToken()
		return ";"
	}
	if tokenType == TokenType_AMP {
		p._LexNextToken()
		return "&"
	}
	return ""
}

func (p *Parser) _PeekListOperator() string {
	savedPos := p.Pos
	op := p.ParseListOperator()
	p.Pos = savedPos
	return op
}

func (p *Parser) ParseList(newlineAsSeparator bool) Node {
	var pipeline Node
	var op string
	var nextOp string
	if newlineAsSeparator {
		p.SkipWhitespaceAndNewlines()
	} else {
		p.SkipWhitespace()
	}
	pipeline = p.ParsePipeline()
	if _isNilNode(pipeline) {
		return nil
	}
	parts := []Node{pipeline}
	if p._InState(ParserStateFlags_PST_EOFTOKEN) && p._AtEofToken() {
		return _ternary(len(parts) == 1, parts[0], Node(NewList(parts)))
	}
	for true {
		p.SkipWhitespace()
		op = p.ParseListOperator()
		if op == "" {
			if !(p.AtEnd()) && p.Peek() == "\n" {
				if !(newlineAsSeparator) {
					break
				}
				p.Advance()
				p._GatherHeredocBodies()
				if p._Cmdsub_heredoc_end != -1 && p._Cmdsub_heredoc_end > p.Pos {
					p.Pos = p._Cmdsub_heredoc_end
					p._Cmdsub_heredoc_end = -1
				}
				p.SkipWhitespaceAndNewlines()
				if p.AtEnd() || p._AtListTerminatingBracket() {
					break
				}
				nextOp = p._PeekListOperator()
				if _containsAny([]interface{}{"&", ";"}, nextOp) {
					break
				}
				op = "\n"
			} else {
				break
			}
		}
		if op == "" {
			break
		}
		parts = append(parts, NewOperator(op))
		if _containsAny([]interface{}{"&&", "||"}, op) {
			p.SkipWhitespaceAndNewlines()
		} else if op == "&" {
			p.SkipWhitespace()
			if p.AtEnd() || p._AtListTerminatingBracket() {
				break
			}
			if p.Peek() == "\n" {
				if newlineAsSeparator {
					p.SkipWhitespaceAndNewlines()
					if p.AtEnd() || p._AtListTerminatingBracket() {
						break
					}
				} else {
					break
				}
			}
		} else if op == ";" {
			p.SkipWhitespace()
			if p.AtEnd() || p._AtListTerminatingBracket() {
				break
			}
			if p.Peek() == "\n" {
				if newlineAsSeparator {
					p.SkipWhitespaceAndNewlines()
					if p.AtEnd() || p._AtListTerminatingBracket() {
						break
					}
				} else {
					break
				}
			}
		}
		pipeline = p.ParsePipeline()
		if _isNilNode(pipeline) {
			panic(NewParseError("Expected command after "+op, p.Pos, 0))
		}
		parts = append(parts, pipeline)
		if p._InState(ParserStateFlags_PST_EOFTOKEN) && p._AtEofToken() {
			break
		}
	}
	if len(parts) == 1 {
		return parts[0]
	}
	return NewList(parts)
}

func (p *Parser) ParseComment() Node {
	if p.AtEnd() || p.Peek() != "#" {
		return nil
	}
	start := p.Pos
	for !(p.AtEnd()) && p.Peek() != "\n" {
		p.Advance()
	}
	text := _Substring(p.Source, start, p.Pos)
	return NewComment(text)
}

func (p *Parser) Parse() []Node {
	var comment Node
	var result Node
	var foundNewline bool
	source := strings.TrimSpace(p.Source)
	if !(len(source) > 0) {
		return []Node{NewEmpty()}
	}
	results := []Node{}
	for true {
		p.SkipWhitespace()
		for !(p.AtEnd()) && p.Peek() == "\n" {
			p.Advance()
		}
		if p.AtEnd() {
			break
		}
		comment = p.ParseComment()
		if !(comment != nil) {
			break
		}
	}
	for !(p.AtEnd()) {
		result = p.ParseList(false)
		if !_isNilNode(result) {
			results = append(results, result)
		}
		p.SkipWhitespace()
		foundNewline = false
		for !(p.AtEnd()) && p.Peek() == "\n" {
			foundNewline = true
			p.Advance()
			p._GatherHeredocBodies()
			if p._Cmdsub_heredoc_end != -1 && p._Cmdsub_heredoc_end > p.Pos {
				p.Pos = p._Cmdsub_heredoc_end
				p._Cmdsub_heredoc_end = -1
			}
			p.SkipWhitespace()
		}
		if !(foundNewline) && !(p.AtEnd()) {
			panic(NewParseError("Syntax error", p.Pos, 0))
		}
	}
	if !(len(results) > 0) {
		return []Node{NewEmpty()}
	}
	if p._Saw_newline_in_single_quote && p.Source != "" && string(p.Source_runes[len(p.Source_runes)-1]) == "\\" && !(len(p.Source_runes) >= 3 && string(p.Source_runes[len(p.Source_runes)-3:len(p.Source_runes)-1]) == "\\\n") {
		if !(p._LastWordOnOwnLine(results)) {
			p._StripTrailingBackslashFromLastWord(results)
		}
	}
	return results
}

func (p *Parser) _LastWordOnOwnLine(nodes []Node) bool {
	return len(nodes) >= 2
}

func (p *Parser) _StripTrailingBackslashFromLastWord(nodes []Node) {
	if !(len(nodes) > 0) {
		return
	}
	lastNode := nodes[len(nodes)-1]
	lastWord := p._FindLastWord(lastNode)
	if lastWord != nil && strings.HasSuffix(lastWord.Value, "\\") {
		lastWord.Value = _Substring(lastWord.Value, 0, _runeLen(lastWord.Value)-1)
		if !(len(lastWord.Value) > 0) && func() bool { _, ok := lastNode.(*Command); return ok }() && len(lastNode.(*Command).Words) > 0 {
			_pop(&lastNode.(*Command).Words)
		}
	}
}

func (p *Parser) _FindLastWord(node Node) *Word {
	var lastWord *Word
	var lastRedirect Node
	switch n := node.(type) {
	case *Word:
		return n
	case *Command:
		if len(n.Words) > 0 {
			lastWord = n.Words[len(n.Words)-1].(*Word)
			if strings.HasSuffix(lastWord.Value, "\\") {
				return lastWord
			}
		}
		if len(n.Redirects) > 0 {
			lastRedirect = n.Redirects[len(n.Redirects)-1]
			if func() bool { _, ok := lastRedirect.(*Redirect); return ok }() {
				return lastRedirect.(*Redirect).Target.(*Word)
			}
		}
		if len(n.Words) > 0 {
			return n.Words[len(n.Words)-1].(*Word)
		}
	case *Pipeline:
		if len(n.Commands) > 0 {
			return p._FindLastWord(n.Commands[len(n.Commands)-1])
		}
	case *List:
		if len(n.Parts) > 0 {
			return p._FindLastWord(n.Parts[len(n.Parts)-1])
		}
	}
	return nil
}
