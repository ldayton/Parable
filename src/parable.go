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

func _runeAt(s string, i int) rune {
	if i < len(s) {
		return rune(s[i])
	}
	return 0
}

func _strToRune(s string) rune {
	if len(s) > 0 {
		return rune(s[0])
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
		if len(v) > 0 {
			return rune(v[0])
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
	Parts interface{}
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
	_Stack []interface{}
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
	_Pending_heredocs         []interface{}
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

func _Substring(s string, start int, end int) string {
	return s[start:end]
}

func _StartsWithAt(s string, pos int, prefix string) bool {
	return strings.HasPrefix(s, prefix)
}

func _CountConsecutiveDollarsBefore(s string, pos int) int {
	var count int
	_ = count
	var k int
	_ = k
	var bsCount int
	_ = bsCount
	var j int
	_ = j
	count = 0
	k = pos - 1
	for k >= 0 && string(s[k]) == "$" {
		bsCount = 0
		j = k - 1
		for j >= 0 && string(s[j]) == "\\" {
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

func _Sublist(lst []interface{}, start int, end int) []interface{} {
	return lst[start:end]
}

func _RepeatStr(s string, n int) string {
	var result []string
	_ = result
	var i int
	_ = i
	result = []string{}
	i = 0
	for i < n {
		result = append(result, s)
		i += 1
	}
	return strings.Join(result, "")
}

func _StripLineContinuationsCommentAware(text string) string {
	var result []string
	_ = result
	var i int
	_ = i
	var inComment bool
	_ = inComment
	var quote *QuoteState
	_ = quote
	var c string
	_ = c
	var numPrecedingBackslashes int
	_ = numPrecedingBackslashes
	var j int
	_ = j
	result = []string{}
	i = 0
	inComment = false
	quote = NewQuoteState()
	for i < len(text) {
		c = string(text[i])
		if c == "\\" && i+1 < len(text) && string(text[i+1]) == "\n" {
			numPrecedingBackslashes = 0
			j = i - 1
			for j >= 0 && string(text[j]) == "\\" {
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
	_ = parts
	if len(redirects) > 0 {
		parts = []string{}
		for _, r := range redirects {
			parts = append(parts, r.ToSexp())
		}
		return base + " " + strings.Join(parts, " ")
	}
	return base
}

func _ConsumeSingleQuote(s string, start int) interface{} {
	var chars []string
	_ = chars
	var i int
	_ = i
	chars = []string{"'"}
	i = start + 1
	for i < len(s) && string(s[i]) != "'" {
		chars = append(chars, string(s[i]))
		i += 1
	}
	if i < len(s) {
		chars = append(chars, string(s[i]))
		i += 1
	}
	return []interface{}{i, chars}
}

func _ConsumeDoubleQuote(s string, start int) interface{} {
	var chars []string
	_ = chars
	var i int
	_ = i
	chars = []string{"\""}
	i = start + 1
	for i < len(s) && string(s[i]) != "\"" {
		if string(s[i]) == "\\" && i+1 < len(s) {
			chars = append(chars, string(s[i]))
			i += 1
		}
		chars = append(chars, string(s[i]))
		i += 1
	}
	if i < len(s) {
		chars = append(chars, string(s[i]))
		i += 1
	}
	return []interface{}{i, chars}
}

func _HasBracketClose(s string, start int, depth int) bool {
	var i int
	_ = i
	i = start
	for i < len(s) {
		if string(s[i]) == "]" {
			return true
		}
		if string(s[i]) == "|" || string(s[i]) == ")" && depth == 0 {
			return false
		}
		i += 1
	}
	return false
}

func _ConsumeBracketClass(s string, start int, depth int) interface{} {
	var scanPos int
	_ = scanPos
	var isBracket bool
	_ = isBracket
	var chars []string
	_ = chars
	var i int
	_ = i
	scanPos = start + 1
	if scanPos < len(s) && string(s[scanPos]) == "!" || string(s[scanPos]) == "^" {
		scanPos += 1
	}
	if scanPos < len(s) && string(s[scanPos]) == "]" {
		if _HasBracketClose(s, scanPos+1, depth) {
			scanPos += 1
		}
	}
	isBracket = false
	for scanPos < len(s) {
		if string(s[scanPos]) == "]" {
			isBracket = true
			break
		}
		if string(s[scanPos]) == ")" && depth == 0 {
			break
		}
		if string(s[scanPos]) == "|" && depth == 0 {
			break
		}
		scanPos += 1
	}
	if !(isBracket) {
		return []interface{}{start + 1, []string{"["}, false}
	}
	chars = []string{"["}
	i = start + 1
	if i < len(s) && string(s[i]) == "!" || string(s[i]) == "^" {
		chars = append(chars, string(s[i]))
		i += 1
	}
	if i < len(s) && string(s[i]) == "]" {
		if _HasBracketClose(s, i+1, depth) {
			chars = append(chars, string(s[i]))
			i += 1
		}
	}
	for i < len(s) && string(s[i]) != "]" {
		chars = append(chars, string(s[i]))
		i += 1
	}
	if i < len(s) {
		chars = append(chars, string(s[i]))
		i += 1
	}
	return []interface{}{i, chars, true}
}

func _FormatCondBody(node Node) string {
	panic("TODO: function needs manual transpilation")
}

func _StartsWithSubshell(node Node) bool {
	panic("TODO: function needs manual transpilation")
}

func _FormatCmdsubNode(node Node, indent int, inProcsub bool, compactRedirects bool, procsubFirst bool) string {
	panic("TODO: function needs manual transpilation")
}

func _FormatRedirect(r Node, compact bool, heredocOpOnly bool) string {
	panic("TODO: function needs manual transpilation")
}

func _FormatHeredocBody(r Node) string {
	panic("TODO: function needs manual transpilation")
}

func _LookaheadForEsac(value string, start int, caseDepth int) bool {
	var i int
	_ = i
	var depth int
	_ = depth
	var quote *QuoteState
	_ = quote
	var c string
	_ = c
	i = start
	depth = caseDepth
	quote = NewQuoteState()
	for i < len(value) {
		c = string(value[i])
		if c == "\\" && i+1 < len(value) && quote.Double {
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
	var i int
	_ = i
	i = start + 1
	for i < len(value) && string(value[i]) != "`" {
		if string(value[i]) == "\\" && i+1 < len(value) {
			i += 2
		} else {
			i += 1
		}
	}
	if i < len(value) {
		i += 1
	}
	return i
}

func _SkipSingleQuoted(s string, start int) int {
	panic("TODO: function needs manual transpilation")
}

func _SkipDoubleQuoted(s string, start int) int {
	panic("TODO: function needs manual transpilation")
}

func _IsValidArithmeticStart(value string, start int) bool {
	var scanParen int
	_ = scanParen
	var scanI int
	_ = scanI
	var scanC string
	_ = scanC
	scanParen = 0
	scanI = start + 3
	for scanI < len(value) {
		scanC = string(value[scanI])
		if _IsExpansionStart(value, scanI, "$(") {
			scanI = _FindCmdsubEnd(value, scanI+2)
			continue
		}
		if scanC == "(" {
			scanParen += 1
		} else if scanC == ")" {
			if scanParen > 0 {
				scanParen -= 1
			} else if scanI+1 < len(value) && string(value[scanI+1]) == ")" {
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
	var depth int
	_ = depth
	var i int
	_ = i
	var quote *QuoteState
	_ = quote
	var c string
	_ = c
	depth = 1
	i = start
	quote = NewQuoteState()
	for i < len(value) && depth > 0 {
		c = string(value[i])
		if c == "\\" && i+1 < len(value) && !(quote.Single) {
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
	return len(value)
}

func _FindCmdsubEnd(value string, start int) int {
	var depth int
	_ = depth
	var i int
	_ = i
	var caseDepth int
	_ = caseDepth
	var inCasePatterns bool
	_ = inCasePatterns
	var arithDepth int
	_ = arithDepth
	var arithParenDepth int
	_ = arithParenDepth
	var c string
	_ = c
	var j int
	_ = j
	depth = 1
	i = start
	caseDepth = 0
	inCasePatterns = false
	arithDepth = 0
	arithParenDepth = 0
	for i < len(value) && depth > 0 {
		c = string(value[i])
		if c == "\\" && i+1 < len(value) {
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
		if c == "#" && arithDepth == 0 && i == start || string(value[i-1]) == " " || string(value[i-1]) == "\t" || string(value[i-1]) == "\n" || string(value[i-1]) == ";" || string(value[i-1]) == "|" || string(value[i-1]) == "&" || string(value[i-1]) == "(" || string(value[i-1]) == ")" {
			for i < len(value) && string(value[i]) != "\n" {
				i += 1
			}
			continue
		}
		if strings.HasPrefix(value[i:], "<<<") {
			i += 3
			for i < len(value) && string(value[i]) == " " || string(value[i]) == "\t" {
				i += 1
			}
			if i < len(value) && string(value[i]) == "\"" {
				i += 1
				for i < len(value) && string(value[i]) != "\"" {
					if string(value[i]) == "\\" && i+1 < len(value) {
						i += 2
					} else {
						i += 1
					}
				}
				if i < len(value) {
					i += 1
				}
			} else if i < len(value) && string(value[i]) == "'" {
				i += 1
				for i < len(value) && string(value[i]) != "'" {
					i += 1
				}
				if i < len(value) {
					i += 1
				}
			} else {
				for i < len(value) && !strings.Contains(" \t\n;|&<>()", string(value[i])) {
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
	var depth int
	_ = depth
	var i int
	_ = i
	var inDouble bool
	_ = inDouble
	var dolbraceState int
	_ = dolbraceState
	var c string
	_ = c
	var end int
	_ = end
	depth = 1
	i = start
	inDouble = false
	dolbraceState = DolbraceState_PARAM
	for i < len(value) && depth > 0 {
		c = string(value[i])
		if c == "\\" && i+1 < len(value) {
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
		if c == "<" || c == ">" && i+1 < len(value) && string(value[i+1]) == "(" {
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
	panic("TODO: function needs manual transpilation")
}

func _FindHeredocContentEnd(source string, start int, delimiters []interface{}) (int, int) {
	panic("TODO: function needs manual transpilation")
}

func _IsWordBoundary(s string, pos int, wordLen int) bool {
	var prev string
	_ = prev
	var end int
	_ = end
	if pos > 0 {
		prev = string(s[pos-1])
		if (unicode.IsLetter(_runeFromChar(prev)) || unicode.IsDigit(_runeFromChar(prev))) || prev == "_" {
			return false
		}
		if strings.Contains("{}!", prev) {
			return false
		}
	}
	end = pos + wordLen
	if end < len(s) && (unicode.IsLetter(_runeFromChar(string(s[end]))) || unicode.IsDigit(_runeFromChar(string(s[end])))) || string(s[end]) == "_" {
		return false
	}
	return true
}

func _IsQuote(c string) bool {
	return c == "'" || c == "\""
}

func _CollapseWhitespace(s string) string {
	panic("TODO: function needs manual transpilation")
}

func _CountTrailingBackslashes(s string) int {
	var count int
	_ = count
	count = 0
	for i := len(s) - 1; i > -1; i += -1 {
		if string(s[i]) == "\\" {
			count += 1
		} else {
			break
		}
	}
	return count
}

func _NormalizeHeredocDelimiter(delimiter string) string {
	panic("TODO: function needs manual transpilation")
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
	panic("TODO: function needs manual transpilation")
}

func _SkipSubscript(s string, start int, flags int) int {
	return _SkipMatchedPair(s, start, "[", "]", flags)
}

func _Assignment(s string, flags int) int {
	var i int
	_ = i
	var c string
	_ = c
	var subFlags int
	_ = subFlags
	var end int
	_ = end
	if !(len(s) > 0) {
		return -1
	}
	if !(unicode.IsLetter(_runeFromChar(string(s[0]))) || string(s[0]) == "_") {
		return -1
	}
	i = 1
	for i < len(s) {
		c = string(s[i])
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
			if i < len(s) && string(s[i]) == "+" {
				i += 1
			}
			if i < len(s) && string(s[i]) == "=" {
				return i
			}
			return -1
		}
		if c == "+" {
			if i+1 < len(s) && string(s[i+1]) == "=" {
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
	var s string
	_ = s
	var i int
	_ = i
	var end int
	_ = end
	if !(len(chars) > 0) {
		return false
	}
	if !(unicode.IsLetter(_runeFromChar(chars[0])) || chars[0] == "_") {
		return false
	}
	s = strings.Join(chars, "")
	i = 1
	for i < len(s) && (unicode.IsLetter(_runeFromChar(string(s[i]))) || unicode.IsDigit(_runeFromChar(string(s[i])))) || string(s[i]) == "_" {
		i += 1
	}
	for i < len(s) {
		if string(s[i]) != "[" {
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
	var bsCount int
	_ = bsCount
	var j int
	_ = j
	bsCount = 0
	j = idx - 1
	for j >= 0 && string(value[j]) == "\\" {
		bsCount += 1
		j -= 1
	}
	return bsCount%2 == 1
}

func _IsDollarDollarParen(value string, idx int) bool {
	var dollarCount int
	_ = dollarCount
	var j int
	_ = j
	dollarCount = 0
	j = idx - 1
	for j >= 0 && string(value[j]) == "$" {
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
	if !(unicode.IsLetter(_runeFromChar(string(name[0]))) || string(name[0]) == "_") {
		return false
	}
	for _, c := range name[1:] {
		if !((unicode.IsLetter(_runeFromChar(c)) || unicode.IsDigit(_runeFromChar(c))) || c == '_') {
			return false
		}
	}
	return true
}

func Parse(source string, extglob bool) []Node {
	var parser *Parser
	_ = parser
	parser = NewParser(source, false, extglob)
	return parser.Parse()
}

func NewToken(typ int, value string, pos int, parts []interface{}, word Node) *Token {
	t := &Token{}
	t.Type = typ
	t.Value = value
	t.Pos = pos
	t.Parts = _ternary(parts != nil, parts, []interface{}{})
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
	q._Stack = []interface{}{}
	return q
}

func (q *QuoteState) Push() {
	q._Stack = append(q._Stack, []interface{}{q.Single, q.Double})
	q.Single = false
	q.Double = false
}

func (q *QuoteState) Pop() {
	panic("TODO: method needs manual implementation")
}

func (q *QuoteState) InQuotes() bool {
	return q.Single || q.Double
}

func (q *QuoteState) Copy() *QuoteState {
	panic("TODO: method needs manual implementation")
}

func (q *QuoteState) OuterDouble() bool {
	panic("TODO: method needs manual implementation")
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
	panic("TODO: method needs manual implementation")
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
	panic("TODO: method needs manual implementation")
}

func (c *ContextStack) CopyStack() []*ParseContext {
	var result []*ParseContext
	_ = result
	result = []*ParseContext{}
	for _, ctx := range c._Stack {
		result = append(result, ctx.Copy())
	}
	return result
}

func (c *ContextStack) RestoreFrom(savedStack []*ParseContext) {
	var result []*ParseContext
	_ = result
	result = []*ParseContext{}
	for _, ctx := range savedStack {
		result = append(result, ctx.Copy())
	}
	c._Stack = result
}

func NewLexer(source string, extglob bool) *Lexer {
	l := &Lexer{}
	l.Source = source
	l.Pos = 0
	l.Length = len(source)
	l.Quote = NewQuoteState()
	l._Token_cache = nil
	l._Parser_state = ParserStateFlags_NONE
	l._Dolbrace_state = DolbraceState_NONE
	l._Pending_heredocs = []interface{}{}
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
	return string(string(l.Source[l.Pos]))
}

func (l *Lexer) Advance() string {
	var c string
	_ = c
	if l.Pos >= l.Length {
		return ""
	}
	c = string(l.Source[l.Pos])
	l.Pos += 1
	return string(c)
}

func (l *Lexer) AtEnd() bool {
	return l.Pos >= l.Length
}

func (l *Lexer) Lookahead(n int) string {
	return l.Source[l.Pos : l.Pos+n]
}

func (l *Lexer) IsMetachar(c string) bool {
	return strings.Contains("|&;()<> \t\n", c)
}

func (l *Lexer) _ReadOperator() *Token {
	var start int
	_ = start
	var c string
	_ = c
	var two string
	_ = two
	var three string
	_ = three
	start = l.Pos
	c = l.Peek()
	if c == "" {
		return nil
	}
	two = l.Lookahead(2)
	three = l.Lookahead(3)
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
		if l.Pos+1 < l.Length && string(l.Source[l.Pos+1]) == "(" {
			return nil
		}
		l.Pos += 1
		return NewToken(TokenType_LESS, c, start, nil, nil)
	}
	if c == ">" {
		if l.Pos+1 < l.Length && string(l.Source[l.Pos+1]) == "(" {
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
	_ = c
	for l.Pos < l.Length {
		c = string(l.Source[l.Pos])
		if c != " " && c != "\t" {
			break
		}
		l.Pos += 1
	}
}

func (l *Lexer) _SkipComment() bool {
	var prev string
	_ = prev
	if l.Pos >= l.Length {
		return false
	}
	if string(l.Source[l.Pos]) != "#" {
		return false
	}
	if l.Quote.InQuotes() {
		return false
	}
	if l.Pos > 0 {
		prev = string(l.Source[l.Pos-1])
		if !strings.Contains(" \t\n;|&(){}", prev) {
			return false
		}
	}
	for l.Pos < l.Length && string(l.Source[l.Pos]) != "\n" {
		l.Pos += 1
	}
	return true
}

func (l *Lexer) _ReadSingleQuote(start int) (string, bool) {
	var chars []string
	_ = chars
	var sawNewline bool
	_ = sawNewline
	var c string
	_ = c
	chars = []string{"'"}
	sawNewline = false
	for l.Pos < l.Length {
		c = string(l.Source[l.Pos])
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
		if ch == "]" && l.Pos+1 < l.Length && string(l.Source[l.Pos+1]) == "]" {
			return true
		}
		if ch == "&" && l.Pos+1 < l.Length && string(l.Source[l.Pos+1]) == "&" {
			return true
		}
		if ch == ")" && parenDepth == 0 {
			return true
		}
		return _IsWhitespace(ch) && parenDepth == 0
	}
	if ctx == WordCtxCond {
		if ch == "]" && l.Pos+1 < l.Length && string(l.Source[l.Pos+1]) == "]" {
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
		if _IsRedirectChar(ch) && !(l.Pos+1 < l.Length && string(l.Source[l.Pos+1]) == "(") {
			return true
		}
		return _IsWhitespace(ch)
	}
	if (l._Parser_state&ParserStateFlags_PST_EOFTOKEN) != 0 && l._Eof_token != "" && ch == l._Eof_token && bracketDepth == 0 {
		return true
	}
	if _IsRedirectChar(ch) && l.Pos+1 < l.Length && string(l.Source[l.Pos+1]) == "(" {
		return false
	}
	return _IsMetachar(ch) && bracketDepth == 0
}

func (l *Lexer) _ReadBracketExpression(chars []string, parts []Node, forRegex bool, parenDepth int) bool {
	var scan int
	_ = scan
	var bracketWillClose bool
	_ = bracketWillClose
	var sc string
	_ = sc
	var nextCh string
	_ = nextCh
	var c string
	_ = c
	if forRegex {
		scan = l.Pos + 1
		if scan < l.Length && string(l.Source[scan]) == "^" {
			scan += 1
		}
		if scan < l.Length && string(l.Source[scan]) == "]" {
			scan += 1
		}
		bracketWillClose = false
		for scan < l.Length {
			sc = string(l.Source[scan])
			if sc == "]" && scan+1 < l.Length && string(l.Source[scan+1]) == "]" {
				break
			}
			if sc == ")" && parenDepth > 0 {
				break
			}
			if sc == "&" && scan+1 < l.Length && string(l.Source[scan+1]) == "&" {
				break
			}
			if sc == "]" {
				bracketWillClose = true
				break
			}
			if sc == "[" && scan+1 < l.Length && string(l.Source[scan+1]) == ":" {
				scan += 2
				for scan < l.Length && !(string(l.Source[scan]) == ":" && scan+1 < l.Length && string(l.Source[scan+1]) == "]") {
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
		nextCh = string(l.Source[l.Pos+1])
		if _IsWhitespaceNoNewline(nextCh) || nextCh == "&" || nextCh == "|" {
			return false
		}
	}
	chars = append(chars, l.Advance())
	if !(l.AtEnd()) && l.Peek() == "^" {
		chars = append(chars, l.Advance())
	}
	if !(l.AtEnd()) && l.Peek() == "]" {
		chars = append(chars, l.Advance())
	}
	for !(l.AtEnd()) {
		c = l.Peek()
		if c == "]" {
			chars = append(chars, l.Advance())
			break
		}
		if c == "[" && l.Pos+1 < l.Length && string(l.Source[l.Pos+1]) == ":" {
			chars = append(chars, l.Advance())
			chars = append(chars, l.Advance())
			for !(l.AtEnd()) && !(l.Peek() == ":" && l.Pos+1 < l.Length && string(l.Source[l.Pos+1]) == "]") {
				chars = append(chars, l.Advance())
			}
			if !(l.AtEnd()) {
				chars = append(chars, l.Advance())
				chars = append(chars, l.Advance())
			}
		} else if !(forRegex) && c == "[" && l.Pos+1 < l.Length && string(l.Source[l.Pos+1]) == "=" {
			chars = append(chars, l.Advance())
			chars = append(chars, l.Advance())
			for !(l.AtEnd()) && !(l.Peek() == "=" && l.Pos+1 < l.Length && string(l.Source[l.Pos+1]) == "]") {
				chars = append(chars, l.Advance())
			}
			if !(l.AtEnd()) {
				chars = append(chars, l.Advance())
				chars = append(chars, l.Advance())
			}
		} else if !(forRegex) && c == "[" && l.Pos+1 < l.Length && string(l.Source[l.Pos+1]) == "." {
			chars = append(chars, l.Advance())
			chars = append(chars, l.Advance())
			for !(l.AtEnd()) && !(l.Peek() == "." && l.Pos+1 < l.Length && string(l.Source[l.Pos+1]) == "]") {
				chars = append(chars, l.Advance())
			}
			if !(l.AtEnd()) {
				chars = append(chars, l.Advance())
				chars = append(chars, l.Advance())
			}
		} else if forRegex && c == "$" {
			l._SyncToParser()
			if !(l._Parser._ParseDollarExpansion(chars, parts, false)) {
				l._SyncFromParser()
				chars = append(chars, l.Advance())
			} else {
				l._SyncFromParser()
			}
		} else {
			chars = append(chars, l.Advance())
		}
	}
	return true
}

func (l *Lexer) _ParseMatchedPair(openChar string, closeChar string, flags int, initialWasDollar bool) string {
	var start int
	_ = start
	var count int
	_ = count
	var chars []string
	_ = chars
	var passNext bool
	_ = passNext
	var wasDollar bool
	_ = wasDollar
	var wasGtlt bool
	_ = wasGtlt
	var ch string
	_ = ch
	var quoteFlags int
	_ = quoteFlags
	var nested string
	_ = nested
	var nextCh string
	_ = nextCh
	var afterBracePos int
	_ = afterBracePos
	var inDquote bool
	_ = inDquote
	var direction string
	_ = direction
	start = l.Pos
	count = 1
	chars = []string{}
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
					if afterBracePos >= l.Length || !(_IsFunsubChar(string(l.Source[afterBracePos]))) {
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
				if l.Pos+2 < l.Length && string(l.Source[l.Pos+2]) == "(" {
					arithNode, arithText := l._Parser._ParseArithmeticExpansion()
					l._SyncFromParser()
					if arithNode != nil {
						chars = append(chars, arithText)
						wasDollar = false
						wasGtlt = false
					} else {
						l._SyncToParser()
						cmdNode, cmdText := l._Parser._ParseCommandSubstitution()
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
			panic("TODO: incomplete implementation")
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
	var start int
	_ = start
	var chars []string
	_ = chars
	var parts []Node
	_ = parts
	var bracketDepth int
	_ = bracketDepth
	var bracketStartPos int
	_ = bracketStartPos
	var seenEquals bool
	_ = seenEquals
	var parenDepth int
	_ = parenDepth
	var ch string
	_ = ch
	var prevChar string
	_ = prevChar
	var forRegex bool
	_ = forRegex
	var content string
	_ = content
	var trackNewline bool
	_ = trackNewline
	var inSingleInDquote bool
	_ = inSingleInDquote
	var c string
	_ = c
	var nextC string
	_ = nextC
	var cmdsubResult0 Node
	_ = cmdsubResult0
	var cmdsubResult1 string
	_ = cmdsubResult1
	var handleLineContinuation bool
	_ = handleLineContinuation
	var nextCh string
	_ = nextCh
	var ansiResult0 Node
	_ = ansiResult0
	var ansiResult1 string
	_ = ansiResult1
	var localeResult0 Node
	_ = localeResult0
	var localeResult1 string
	_ = localeResult1
	var localeResult2 []Node
	_ = localeResult2
	var procsubResult0 Node
	_ = procsubResult0
	var procsubResult1 string
	_ = procsubResult1
	var isArrayAssign bool
	_ = isArrayAssign
	var arrayResult0 Node
	_ = arrayResult0
	var arrayResult1 string
	_ = arrayResult1
	start = l.Pos
	chars = []string{}
	parts = []Node{}
	bracketDepth = 0
	bracketStartPos = -1
	seenEquals = false
	parenDepth = 0
	for !(l.AtEnd()) {
		ch = l.Peek()
		if ctx == WordCtxRegex {
			if ch == "\\" && l.Pos+1 < l.Length && string(l.Source[l.Pos+1]) == "\n" {
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
			if l._ReadBracketExpression(chars, parts, forRegex, parenDepth) {
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
				for !(l.AtEnd()) && inSingleInDquote || l.Peek() != "\"" {
					c = l.Peek()
					if inSingleInDquote {
						chars = append(chars, l.Advance())
						if c == "'" {
							inSingleInDquote = false
						}
						continue
					}
					if c == "\\" && l.Pos+1 < l.Length {
						nextC = string(l.Source[l.Pos+1])
						if nextC == "\n" {
							l.Advance()
							l.Advance()
						} else {
							chars = append(chars, l.Advance())
							chars = append(chars, l.Advance())
						}
					} else if c == "$" {
						l._SyncToParser()
						if !(l._Parser._ParseDollarExpansion(chars, parts, true)) {
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
				l._Parser._ScanDoubleQuote(chars, parts, start, handleLineContinuation)
				l._SyncFromParser()
			}
			continue
		}
		if ch == "\\" && l.Pos+1 < l.Length {
			nextCh = string(l.Source[l.Pos+1])
			if ctx != WordCtxRegex && nextCh == "\n" {
				l.Advance()
				l.Advance()
			} else {
				chars = append(chars, l.Advance())
				chars = append(chars, l.Advance())
			}
			continue
		}
		if ctx != WordCtxRegex && ch == "$" && l.Pos+1 < l.Length && string(l.Source[l.Pos+1]) == "'" {
			ansiResult0, ansiResult1 = l._ReadAnsiCQuote()
			if ansiResult0 != nil {
				parts = append(parts, ansiResult0.(Node))
				chars = append(chars, ansiResult1)
			} else {
				chars = append(chars, l.Advance())
			}
			continue
		}
		if ctx != WordCtxRegex && ch == "$" && l.Pos+1 < l.Length && string(l.Source[l.Pos+1]) == "\"" {
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
			if !(l._Parser._ParseDollarExpansion(chars, parts, false)) {
				l._SyncFromParser()
				chars = append(chars, l.Advance())
			} else {
				l._SyncFromParser()
				if l._Extglob && ctx == WordCtxNormal && len(chars) > 0 && len(chars[len(chars)-1]) == 2 && string(chars[len(chars)-1][0]) == "$" && strings.Contains("?*@", string(chars[len(chars)-1][1])) && !(l.AtEnd()) && l.Peek() == "(" {
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
		if ctx != WordCtxRegex && _IsRedirectChar(ch) && l.Pos+1 < l.Length && string(l.Source[l.Pos+1]) == "(" {
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
			if isArrayAssign && atCommandStart || inAssignBuiltin {
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
		if l._Extglob && ctx == WordCtxNormal && _IsExtglobPrefix(ch) && l.Pos+1 < l.Length && string(l.Source[l.Pos+1]) == "(" {
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
	var start int
	_ = start
	var c string
	_ = c
	var isProcsub bool
	_ = isProcsub
	var isRegexParen bool
	_ = isRegexParen
	var word *Word
	_ = word
	start = l.Pos
	if l.Pos >= l.Length {
		return nil
	}
	c = l.Peek()
	if c == "" {
		return nil
	}
	isProcsub = c == "<" || c == ">" && l.Pos+1 < l.Length && string(l.Source[l.Pos+1]) == "("
	isRegexParen = l._Word_context == WordCtxRegex && c == "(" || c == ")"
	if l.IsMetachar(c) && !(isProcsub) && !(isRegexParen) {
		return nil
	}
	word = l._ReadWordInternal(l._Word_context, l._At_command_start, l._In_array_literal, l._In_assign_builtin)
	if word == nil {
		return nil
	}
	return NewToken(TokenType_WORD, word.Value, start, nil, word)
}

func (l *Lexer) NextToken() *Token {
	var tok *Token
	_ = tok
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
	_ = savedLast
	if l._Token_cache == nil {
		savedLast = l._Last_read_token
		l._Token_cache = l.NextToken()
		l._Last_read_token = savedLast
	}
	return l._Token_cache
}

func (l *Lexer) _ReadAnsiCQuote() (Node, string) {
	var start int
	_ = start
	var contentChars []string
	_ = contentChars
	var foundClose bool
	_ = foundClose
	var ch string
	_ = ch
	var text string
	_ = text
	var content string
	_ = content
	var node *AnsiCQuote
	_ = node
	if l.AtEnd() || l.Peek() != "$" {
		return nil, ""
	}
	if l.Pos+1 >= l.Length || string(l.Source[l.Pos+1]) != "'" {
		return nil, ""
	}
	start = l.Pos
	l.Advance()
	l.Advance()
	contentChars = []string{}
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
	text = l.Source[start:l.Pos]
	content = strings.Join(contentChars, "")
	node = NewAnsiCQuote(content)
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
	var start int
	_ = start
	var contentChars []string
	_ = contentChars
	var innerParts []Node
	_ = innerParts
	var foundClose bool
	_ = foundClose
	var ch string
	_ = ch
	var nextCh string
	_ = nextCh
	var content string
	_ = content
	var text string
	_ = text
	if l.AtEnd() || l.Peek() != "$" {
		return nil, "", []Node{}
	}
	if l.Pos+1 >= l.Length || string(l.Source[l.Pos+1]) != "\"" {
		return nil, "", []Node{}
	}
	start = l.Pos
	l.Advance()
	l.Advance()
	contentChars = []string{}
	innerParts = []Node{}
	foundClose = false
	for !(l.AtEnd()) {
		ch = l.Peek()
		if ch == "\"" {
			l.Advance()
			foundClose = true
			break
		} else if ch == "\\" && l.Pos+1 < l.Length {
			nextCh = string(l.Source[l.Pos+1])
			if nextCh == "\n" {
				l.Advance()
				l.Advance()
			} else {
				contentChars = append(contentChars, l.Advance())
				contentChars = append(contentChars, l.Advance())
			}
		} else if ch == "$" && l.Pos+2 < l.Length && string(l.Source[l.Pos+1]) == "(" && string(l.Source[l.Pos+2]) == "(" {
			l._SyncToParser()
			arithNode, arithText := l._Parser._ParseArithmeticExpansion()
			l._SyncFromParser()
			if arithNode != nil {
				innerParts = append(innerParts, arithNode.(Node))
				contentChars = append(contentChars, arithText)
			} else {
				l._SyncToParser()
				cmdsubNode, cmdsubText := l._Parser._ParseCommandSubstitution()
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
	content = strings.Join(contentChars, "")
	text = "$\"" + content + "\""
	return NewLocaleString(content), text, innerParts
}

func (l *Lexer) _UpdateDolbraceForOp(op string, hasParam bool) {
	var firstChar string
	_ = firstChar
	if l._Dolbrace_state == DolbraceState_NONE {
		return
	}
	if op == "" || len(op) == 0 {
		return
	}
	firstChar = string(op[0])
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
	var ch string
	_ = ch
	var nextCh string
	_ = nextCh
	if l.AtEnd() {
		return ""
	}
	ch = l.Peek()
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
	var depth int
	_ = depth
	var i int
	_ = i
	var quote *QuoteState
	_ = quote
	var c string
	_ = c
	depth = 1
	i = startPos + 1
	quote = NewQuoteState()
	for i < l.Length {
		c = string(l.Source[i])
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
	var ch string
	_ = ch
	var nameChars []string
	_ = nameChars
	var c string
	_ = c
	var content string
	_ = content
	if l.AtEnd() {
		return ""
	}
	ch = l.Peek()
	if _IsSpecialParam(ch) {
		if ch == "$" && l.Pos+1 < l.Length && strings.Contains("{'\"", string(l.Source[l.Pos+1])) {
			return ""
		}
		l.Advance()
		return ch
	}
	if unicode.IsDigit(_runeFromChar(ch)) {
		nameChars = []string{}
		for !(l.AtEnd()) && unicode.IsDigit(_runeFromChar(l.Peek())) {
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
	var start int
	_ = start
	var ch string
	_ = ch
	var text string
	_ = text
	var nameStart int
	_ = nameStart
	var c string
	_ = c
	var name string
	_ = name
	if l.AtEnd() || l.Peek() != "$" {
		return nil, ""
	}
	start = l.Pos
	l.Advance()
	if l.AtEnd() {
		l.Pos = start
		return nil, ""
	}
	ch = l.Peek()
	if ch == "{" {
		l.Advance()
		return l._ReadBracedParam(start, inDquote)
	}
	if _IsSpecialParamUnbraced(ch) || _IsDigit(ch) || ch == "#" {
		l.Advance()
		text = l.Source[start:l.Pos]
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
		name = l.Source[nameStart:l.Pos]
		text = l.Source[start:l.Pos]
		return NewParamExpansion(name, "", ""), text
	}
	l.Pos = start
	return nil, ""
}

func (l *Lexer) _ReadBracedParam(start int, inDquote bool) (Node, string) {
	var savedDolbrace int
	_ = savedDolbrace
	var ch string
	_ = ch
	var param string
	_ = param
	var text string
	_ = text
	var suffix string
	_ = suffix
	var trailing string
	_ = trailing
	var op string
	_ = op
	var arg string
	_ = arg
	var content string
	_ = content
	var dollarCount int
	_ = dollarCount
	var backtickPos int
	_ = backtickPos
	var bc string
	_ = bc
	var nextC string
	_ = nextC
	var flags int
	_ = flags
	var paramEndsWithDollar bool
	_ = paramEndsWithDollar
	var e interface{}
	_ = e
	var inner string
	_ = inner
	var subParser *Parser
	_ = subParser
	var parsed Node
	_ = parsed
	var formatted string
	_ = formatted
	if l.AtEnd() {
		panic(NewMatchedPairError("unexpected EOF looking for `}'", start, 0))
	}
	savedDolbrace = l._Dolbrace_state
	l._Dolbrace_state = DolbraceState_PARAM
	ch = l.Peek()
	if _IsFunsubChar(ch) {
		l._Dolbrace_state = savedDolbrace
		return l._ReadFunsub(start)
	}
	if ch == "#" {
		l.Advance()
		param = l._ConsumeParamName()
		if len(param) > 0 && !(l.AtEnd()) && l.Peek() == "}" {
			l.Advance()
			text = l.Source[start:l.Pos]
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
				text = l.Source[start:l.Pos]
				l._Dolbrace_state = savedDolbrace
				return NewParamIndirect(param, "", ""), text
			}
			if !(l.AtEnd()) && _IsAtOrStar(l.Peek()) {
				suffix = l.Advance()
				trailing = l._ParseMatchedPair("{", "}", MatchedPairFlags_DOLBRACE, false)
				text = l.Source[start:l.Pos]
				l._Dolbrace_state = savedDolbrace
				return NewParamIndirect(param+suffix+trailing, "", ""), text
			}
			op = l._ConsumeParamOperator()
			if op == "" && !(l.AtEnd()) && !strings.Contains("}\"'`", l.Peek()) {
				op = l.Advance()
			}
			if op != "" && !strings.Contains("\"'`", op) {
				arg = l._ParseMatchedPair("{", "}", MatchedPairFlags_DOLBRACE, false)
				text = l.Source[start:l.Pos]
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
		if !(l.AtEnd()) && strings.Contains("-=+?", l.Peek()) || l.Peek() == ":" && l.Pos+1 < l.Length && _IsSimpleParamOp(string(l.Source[l.Pos+1])) {
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
		text = l.Source[start:l.Pos]
		l._Dolbrace_state = savedDolbrace
		return NewParamExpansion(param, "", ""), text
	}
	op = l._ConsumeParamOperator()
	if op == "" {
		if !(l.AtEnd()) && l.Peek() == "$" && l.Pos+1 < l.Length && _containsAny([]interface{}{"\"", "'"}, string(l.Source[l.Pos+1])) {
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
					nextC = string(l.Source[l.Pos+1])
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
		} else if !(l.AtEnd()) && l.Peek() == "$" && l.Pos+1 < l.Length && string(l.Source[l.Pos+1]) == "{" {
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
	l._UpdateDolbraceForOp(op, len(param) > 0)
	panic("TODO: try/except")
	if _containsAny([]interface{}{"<", ">"}, op) && strings.HasPrefix(arg, "(") && strings.HasSuffix(arg, ")") {
		inner = arg[1 : len(arg)-1]
		panic("TODO: incomplete implementation")
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
	_ = value
	var escaped string
	_ = escaped
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
	escaped = strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(value, "\"", "\\\""), "\n", "\\n"), "\t", "\\t")
	return "(word \"" + escaped + "\")"
}

func (w *Word) _AppendWithCtlesc(result []byte, byteVal int) {
	result = append(result, byte(byteVal))
}

func (w *Word) _DoubleCtlescSmart(value string) string {
	var result []rune
	_ = result
	var quote *QuoteState
	_ = quote
	var bsCount int
	_ = bsCount
	result = []rune{}
	quote = NewQuoteState()
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
	var result []string
	_ = result
	var i int
	_ = i
	var quote *QuoteState
	_ = quote
	var c string
	_ = c
	var hadLeadingNewline bool
	_ = hadLeadingNewline
	var depth int
	_ = depth
	var ch string
	_ = ch
	result = []string{}
	i = 0
	quote = NewQuoteState()
	for i < len(value) {
		c = string(value[i])
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
			hadLeadingNewline = i < len(value) && string(value[i]) == "\n"
			if hadLeadingNewline {
				result = append(result, " ")
				i += 1
			}
			depth = 1
			for i < len(value) && depth > 0 {
				ch = string(value[i])
				if ch == "\\" && i+1 < len(value) && !(quote.Single) {
					if string(value[i+1]) == "\n" {
						i += 2
						continue
					}
					result = append(result, ch)
					result = append(result, string(value[i+1]))
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
	var result []string
	_ = result
	if !(len(s) > 0) {
		return "''"
	}
	if s == "'" {
		return "\\'"
	}
	result = []string{"'"}
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
	var result []byte
	_ = result
	var i int
	_ = i
	var c string
	_ = c
	var simple int
	_ = simple
	var j int
	_ = j
	var hexStr string
	_ = hexStr
	var byteVal int
	_ = byteVal
	var codepoint int
	_ = codepoint
	var ctrlChar string
	_ = ctrlChar
	var skipExtra int
	_ = skipExtra
	var ctrlVal int
	_ = ctrlVal
	result = []byte{}
	i = 0
	for i < len(inner) {
		if string(inner[i]) == "\\" && i+1 < len(inner) {
			c = string(inner[i+1])
			simple = _GetAnsiEscape(c)
			if simple >= 0 {
				result = append(result, byte(simple))
				i += 2
			} else if c == "'" {
				result = append(result, byte(39))
				i += 2
			} else if c == "x" {
				if i+2 < len(inner) && string(inner[i+2]) == "{" {
					j = i + 3
					for j < len(inner) && _IsHexDigit(string(inner[j])) {
						j += 1
					}
					hexStr = inner[i+3 : j]
					if j < len(inner) && string(inner[j]) == "}" {
						j += 1
					}
					if !(len(hexStr) > 0) {
						return result
					}
					byteVal = _parseInt(hexStr, 16) & 255
					if byteVal == 0 {
						return result
					}
					w._AppendWithCtlesc(result, byteVal)
					i = j
				} else {
					j = i + 2
					for j < len(inner) && j < i+4 && _IsHexDigit(string(inner[j])) {
						j += 1
					}
					if j > i+2 {
						byteVal = _parseInt(inner[i+2:j], 16)
						if byteVal == 0 {
							return result
						}
						w._AppendWithCtlesc(result, byteVal)
						i = j
					} else {
						result = append(result, inner[i])
						i += 1
					}
				}
			} else if c == "u" {
				j = i + 2
				for j < len(inner) && j < i+6 && _IsHexDigit(string(inner[j])) {
					j += 1
				}
				if j > i+2 {
					codepoint = _parseInt(inner[i+2:j], 16)
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
				for j < len(inner) && j < i+10 && _IsHexDigit(string(inner[j])) {
					j += 1
				}
				if j > i+2 {
					codepoint = _parseInt(inner[i+2:j], 16)
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
				if i+3 <= len(inner) {
					ctrlChar = string(inner[i+2])
					skipExtra = 0
					if ctrlChar == "\\" && i+4 <= len(inner) && string(inner[i+3]) == "\\" {
						skipExtra = 1
					}
					ctrlVal = int(rune(ctrlChar[0])) & 31
					if ctrlVal == 0 {
						return result
					}
					w._AppendWithCtlesc(result, ctrlVal)
					i += 3 + skipExtra
				} else {
					result = append(result, inner[i])
					i += 1
				}
			} else if c == "0" {
				j = i + 2
				for j < len(inner) && j < i+4 && _IsOctalDigit(string(inner[j])) {
					j += 1
				}
				if j > i+2 {
					byteVal = _parseInt(inner[i+1:j], 8) & 255
					if byteVal == 0 {
						return result
					}
					w._AppendWithCtlesc(result, byteVal)
					i = j
				} else {
					return result
				}
			} else if c >= "1" && c <= "7" {
				j = i + 1
				for j < len(inner) && j < i+4 && _IsOctalDigit(string(inner[j])) {
					j += 1
				}
				byteVal = _parseInt(inner[i+1:j], 8) & 255
				if byteVal == 0 {
					return result
				}
				w._AppendWithCtlesc(result, byteVal)
				i = j
			} else {
				result = append(result, byte(92))
				result = append(result, byte(int(rune(c[0]))))
				i += 2
			}
		} else {
			result = append(result, []byte(string(inner[i]))...)
			i += 1
		}
	}
	return result
}

func (w *Word) _ExpandAnsiCEscapes(value string) string {
	var inner string
	_ = inner
	var literalBytes []byte
	_ = literalBytes
	var literalStr string
	_ = literalStr
	if !(strings.HasPrefix(value, "'") && strings.HasSuffix(value, "'")) {
		return value
	}
	inner = value[1 : len(value)-1]
	literalBytes = w._AnsiCToBytes(inner)
	literalStr = string(literalBytes)
	return w._ShSingleQuote(literalStr)
}

func (w *Word) _ExpandAllAnsiCQuotes(value string) string {
	var result []string
	_ = result
	var i int
	_ = i
	var quote *QuoteState
	_ = quote
	var inBacktick bool
	_ = inBacktick
	var braceDepth int
	_ = braceDepth
	var ch string
	_ = ch
	var effectiveInDquote bool
	_ = effectiveInDquote
	var isAnsiC bool
	_ = isAnsiC
	var j int
	_ = j
	var ansiStr string
	_ = ansiStr
	var expanded string
	_ = expanded
	var outerInDquote bool
	_ = outerInDquote
	var inner string
	_ = inner
	var resultStr string
	_ = resultStr
	var inPattern bool
	_ = inPattern
	var lastBraceIdx int
	_ = lastBraceIdx
	var afterBrace string
	_ = afterBrace
	var varNameLen int
	_ = varNameLen
	var c interface{}
	_ = c
	var opStart string
	_ = opStart
	var firstChar string
	_ = firstChar
	var rest string
	_ = rest
	result = []string{}
	i = 0
	quote = NewQuoteState()
	inBacktick = false
	braceDepth = 0
	for i < len(value) {
		ch = string(value[i])
		if ch == "`" && !(quote.Single) {
			inBacktick = !(inBacktick)
			result = append(result, ch)
			i += 1
			continue
		}
		if inBacktick {
			if ch == "\\" && i+1 < len(value) {
				result = append(result, ch)
				result = append(result, string(value[i+1]))
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
				panic("TODO: incomplete implementation")
			}
		}
		effectiveInDquote = quote.Double
		if ch == "'" && !(effectiveInDquote) {
			isAnsiC = !(quote.Single) && i > 0 && string(value[i-1]) == "$" && _CountConsecutiveDollarsBefore(value, i-1)%2 == 0
			if !(isAnsiC) {
				quote.Single = !(quote.Single)
			}
			result = append(result, ch)
			i += 1
		} else if ch == "\"" && !(quote.Single) {
			quote.Double = !(quote.Double)
			result = append(result, ch)
			i += 1
		} else if ch == "\\" && i+1 < len(value) && !(quote.Single) {
			result = append(result, ch)
			result = append(result, string(value[i+1]))
			i += 2
		} else if strings.HasPrefix(value[i:], "$'") && !(quote.Single) && !(effectiveInDquote) && _CountConsecutiveDollarsBefore(value, i)%2 == 0 {
			j = i + 2
			for j < len(value) {
				if string(value[j]) == "\\" && j+1 < len(value) {
					j += 2
				} else if string(value[j]) == "'" {
					j += 1
					break
				} else {
					j += 1
				}
			}
			ansiStr = value[i:j]
			expanded = w._ExpandAnsiCEscapes(ansiStr[1:len(ansiStr)])
			outerInDquote = quote.OuterDouble()
			if braceDepth > 0 && outerInDquote && strings.HasPrefix(expanded, "'") && strings.HasSuffix(expanded, "'") {
				inner = expanded[1 : len(expanded)-1]
				if strings.Index(inner, "\x01") == -1 {
					resultStr = strings.Join(result, "")
					inPattern = false
					lastBraceIdx = strings.LastIndex(resultStr, "${")
					if lastBraceIdx >= 0 {
						afterBrace = resultStr[lastBraceIdx+2:]
						varNameLen = 0
						if len(afterBrace) > 0 {
							if strings.Contains("@*#?-$!0123456789_", string(afterBrace[0])) {
								varNameLen = 1
							} else if unicode.IsLetter(_runeFromChar(string(afterBrace[0]))) || string(afterBrace[0]) == "_" {
								for varNameLen < len(afterBrace) {
									c = string(afterBrace[varNameLen])
									if !((unicode.IsLetter(_runeFromChar(c)) || unicode.IsDigit(_runeFromChar(c))) || c == "_") {
										break
									}
									varNameLen += 1
								}
							}
						}
						if varNameLen > 0 && varNameLen < len(afterBrace) && !strings.Contains("#?-", string(afterBrace[0])) {
							opStart = afterBrace[varNameLen:]
							if strings.HasPrefix(opStart, "@") && len(opStart) > 1 {
								opStart = opStart[1:]
							}
							for _, op := range []string{"//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"} {
								if strings.HasPrefix(opStart, op) {
									inPattern = true
									break
								}
							}
							if !(inPattern) && len(opStart) > 0 && !strings.Contains("%#/^,~:+-=?", string(opStart[0])) {
								for _, op := range []string{"//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"} {
									if strings.Contains(opStart, op) {
										inPattern = true
										break
									}
								}
							}
						} else if varNameLen == 0 && len(afterBrace) > 1 {
							firstChar = string(afterBrace[0])
							if !strings.Contains("%#/^,", firstChar) {
								rest = afterBrace[1:]
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
	var result []string
	_ = result
	var i int
	_ = i
	var braceDepth int
	_ = braceDepth
	var bracketDepth int
	_ = bracketDepth
	var quote *QuoteState
	_ = quote
	var braceQuote *QuoteState
	_ = braceQuote
	var bracketInDoubleQuote bool
	_ = bracketInDoubleQuote
	var ch string
	_ = ch
	var dollarCount int
	_ = dollarCount
	result = []string{}
	i = 0
	braceDepth = 0
	bracketDepth = 0
	quote = NewQuoteState()
	braceQuote = NewQuoteState()
	bracketInDoubleQuote = false
	for i < len(value) {
		ch = string(value[i])
		if ch == "\\" && i+1 < len(value) && !(quote.Single) && !(braceQuote.Single) {
			result = append(result, ch)
			result = append(result, string(value[i+1]))
			i += 2
		} else if strings.HasPrefix(value[i:], "${") && !(quote.Single) && !(braceQuote.Single) && i == 0 || string(value[i-1]) != "$" {
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
		} else if strings.HasPrefix(value[i:], "$\"") && !(quote.Single) && !(braceQuote.Single) && braceDepth > 0 || bracketDepth > 0 || !(quote.Double) && !(braceQuote.Double) && !(bracketInDoubleQuote) {
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
	var i int
	_ = i
	var depth int
	_ = depth
	var prefix string
	_ = prefix
	var openParenPos int
	_ = openParenPos
	var closeParenPos int
	_ = closeParenPos
	var inner string
	_ = inner
	var suffix string
	_ = suffix
	var result string
	_ = result
	i = 0
	if !(i < len(value) && unicode.IsLetter(_runeFromChar(string(value[i]))) || string(value[i]) == "_") {
		return value
	}
	i += 1
	for i < len(value) && (unicode.IsLetter(_runeFromChar(string(value[i]))) || unicode.IsDigit(_runeFromChar(string(value[i])))) || string(value[i]) == "_" {
		i += 1
	}
	for i < len(value) && string(value[i]) == "[" {
		depth = 1
		i += 1
		for i < len(value) && depth > 0 {
			if string(value[i]) == "[" {
				depth += 1
			} else if string(value[i]) == "]" {
				depth -= 1
			}
			i += 1
		}
		if depth != 0 {
			return value
		}
	}
	if i < len(value) && string(value[i]) == "+" {
		i += 1
	}
	if !(i+1 < len(value) && string(value[i]) == "=" && string(value[i+1]) == "(") {
		return value
	}
	prefix = value[0 : i+1]
	openParenPos = i + 1
	if strings.HasSuffix(value, ")") {
		closeParenPos = len(value) - 1
	} else {
		closeParenPos = w._FindMatchingParen(value, openParenPos)
		if closeParenPos < 0 {
			return value
		}
	}
	inner = value[openParenPos+1 : closeParenPos]
	suffix = value[closeParenPos+1 : len(value)]
	result = w._NormalizeArrayInner(inner)
	return prefix + "(" + result + ")" + suffix
}

func (w *Word) _FindMatchingParen(value string, openPos int) int {
	var i int
	_ = i
	var depth int
	_ = depth
	var quote *QuoteState
	_ = quote
	var ch string
	_ = ch
	if openPos >= len(value) || string(value[openPos]) != "(" {
		return -1
	}
	i = openPos + 1
	depth = 1
	quote = NewQuoteState()
	for i < len(value) && depth > 0 {
		ch = string(value[i])
		if ch == "\\" && i+1 < len(value) && !(quote.Single) {
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
			for i < len(value) && string(value[i]) != "\n" {
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
	var normalized []string
	_ = normalized
	var i int
	_ = i
	var inWhitespace bool
	_ = inWhitespace
	var braceDepth int
	_ = braceDepth
	var bracketDepth int
	_ = bracketDepth
	var ch string
	_ = ch
	var j int
	_ = j
	var dqContent []string
	_ = dqContent
	var dqBraceDepth int
	_ = dqBraceDepth
	var depth int
	_ = depth
	normalized = []string{}
	i = 0
	inWhitespace = true
	braceDepth = 0
	bracketDepth = 0
	for i < len(inner) {
		ch = string(inner[i])
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
			for j < len(inner) && string(inner[j]) != "'" {
				j += 1
			}
			normalized = append(normalized, inner[i:j+1])
			i = j + 1
		} else if ch == "\"" {
			inWhitespace = false
			j = i + 1
			dqContent = []string{"\""}
			dqBraceDepth = 0
			for j < len(inner) {
				if string(inner[j]) == "\\" && j+1 < len(inner) {
					if string(inner[j+1]) == "\n" {
						j += 2
					} else {
						dqContent = append(dqContent, string(inner[j]))
						dqContent = append(dqContent, string(inner[j+1]))
						j += 2
					}
				} else if _IsExpansionStart(inner, j, "${") {
					dqContent = append(dqContent, "${")
					dqBraceDepth += 1
					j += 2
				} else if string(inner[j]) == "}" && dqBraceDepth > 0 {
					dqContent = append(dqContent, "}")
					dqBraceDepth -= 1
					j += 1
				} else if string(inner[j]) == "\"" && dqBraceDepth == 0 {
					dqContent = append(dqContent, "\"")
					j += 1
					break
				} else {
					dqContent = append(dqContent, string(inner[j]))
					j += 1
				}
			}
			normalized = append(normalized, strings.Join(dqContent, ""))
			i = j
		} else if ch == "\\" && i+1 < len(inner) {
			if string(inner[i+1]) == "\n" {
				i += 2
			} else {
				inWhitespace = false
				normalized = append(normalized, inner[i:i+2])
				i += 2
			}
		} else if _IsExpansionStart(inner, i, "$((") {
			inWhitespace = false
			j = i + 3
			depth = 1
			for j < len(inner) && depth > 0 {
				if j+1 < len(inner) && string(inner[j]) == "(" && string(inner[j+1]) == "(" {
					depth += 1
					j += 2
				} else if j+1 < len(inner) && string(inner[j]) == ")" && string(inner[j+1]) == ")" {
					depth -= 1
					j += 2
				} else {
					j += 1
				}
			}
			normalized = append(normalized, inner[i:j])
			i = j
		} else if _IsExpansionStart(inner, i, "$(") {
			inWhitespace = false
			j = i + 2
			depth = 1
			for j < len(inner) && depth > 0 {
				if string(inner[j]) == "(" && j > 0 && string(inner[j-1]) == "$" {
					depth += 1
				} else if string(inner[j]) == ")" {
					depth -= 1
				} else if string(inner[j]) == "'" {
					j += 1
					for j < len(inner) && string(inner[j]) != "'" {
						j += 1
					}
				} else if string(inner[j]) == "\"" {
					j += 1
					for j < len(inner) {
						if string(inner[j]) == "\\" && j+1 < len(inner) {
							j += 2
							continue
						}
						if string(inner[j]) == "\"" {
							break
						}
						j += 1
					}
				}
				j += 1
			}
			normalized = append(normalized, inner[i:j])
			i = j
		} else if ch == "<" || ch == ">" && i+1 < len(inner) && string(inner[i+1]) == "(" {
			inWhitespace = false
			j = i + 2
			depth = 1
			for j < len(inner) && depth > 0 {
				if string(inner[j]) == "(" {
					depth += 1
				} else if string(inner[j]) == ")" {
					depth -= 1
				} else if string(inner[j]) == "'" {
					j += 1
					for j < len(inner) && string(inner[j]) != "'" {
						j += 1
					}
				} else if string(inner[j]) == "\"" {
					j += 1
					for j < len(inner) {
						if string(inner[j]) == "\\" && j+1 < len(inner) {
							j += 2
							continue
						}
						if string(inner[j]) == "\"" {
							break
						}
						j += 1
					}
				}
				j += 1
			}
			normalized = append(normalized, inner[i:j])
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
			for i < len(inner) && string(inner[i]) != "\n" {
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
	return strings.TrimRight(strings.Join(normalized, ""), " \t")
}

func (w *Word) _StripArithLineContinuations(value string) string {
	var result []string
	_ = result
	var i int
	_ = i
	var start int
	_ = start
	var depth int
	_ = depth
	var arithContent []string
	_ = arithContent
	var firstCloseIdx int
	_ = firstCloseIdx
	var numBackslashes int
	_ = numBackslashes
	var j int
	_ = j
	var content string
	_ = content
	var closing string
	_ = closing
	result = []string{}
	i = 0
	for i < len(value) {
		if _IsExpansionStart(value, i, "$((") {
			start = i
			i += 3
			depth = 2
			arithContent = []string{}
			firstCloseIdx = -1
			for i < len(value) && depth > 0 {
				if string(value[i]) == "(" {
					arithContent = append(arithContent, "(")
					depth += 1
					i += 1
					if depth > 1 {
						firstCloseIdx = -1
					}
				} else if string(value[i]) == ")" {
					if depth == 2 {
						firstCloseIdx = len(arithContent)
					}
					depth -= 1
					if depth > 0 {
						arithContent = append(arithContent, ")")
					}
					i += 1
				} else if string(value[i]) == "\\" && i+1 < len(value) && string(value[i+1]) == "\n" {
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
					arithContent = append(arithContent, string(value[i]))
					i += 1
					if depth == 1 {
						firstCloseIdx = -1
					}
				}
			}
			if depth == 0 || depth == 1 && firstCloseIdx != -1 {
				content = strings.Join(arithContent, "")
				if firstCloseIdx != -1 {
					content = content[0:firstCloseIdx]
					closing = _ternary(depth == 0, "))", ")")
					result = append(result, "$(("+content+closing)
				} else {
					result = append(result, "$(("+content+")")
				}
			} else {
				result = append(result, value[start:i])
			}
		} else {
			result = append(result, string(value[i]))
			i += 1
		}
	}
	return strings.Join(result, "")
}

func (w *Word) _CollectCmdsubs(node Node) []Node {
	var result []Node
	_ = result
	var nodeKind interface{}
	_ = nodeKind
	var elements []Node
	_ = elements
	var parts []Node
	_ = parts
	var expr Node
	_ = expr
	var left Node
	_ = left
	var right Node
	_ = right
	var operand Node
	_ = operand
	var condition Node
	_ = condition
	var trueValue Node
	_ = trueValue
	var falseValue Node
	_ = falseValue
	result = []Node{}
	nodeKind = _getattr(node, "kind", nil)
	if nodeKind == "cmdsub" {
		result = append(result, node)
	} else if nodeKind == "array" {
		elements = _getattr(node, "elements", []interface{}{}).([]Node)
		for _, elem := range elements {
			parts = _getattr(elem, "parts", []interface{}{}).([]Node)
			for _, p := range parts {
				if _getattr(p, "kind", nil) == "cmdsub" {
					result = append(result, p)
				} else {
					result = append(result, w._CollectCmdsubs(p)...)
				}
			}
		}
	} else {
		expr = _getattr(node, "expression", nil).(Node)
		if expr != nil {
			result = append(result, w._CollectCmdsubs(expr)...)
		}
	}
	left = _getattr(node, "left", nil).(Node)
	if left != nil {
		result = append(result, w._CollectCmdsubs(left)...)
	}
	right = _getattr(node, "right", nil).(Node)
	if right != nil {
		result = append(result, w._CollectCmdsubs(right)...)
	}
	operand = _getattr(node, "operand", nil).(Node)
	if operand != nil {
		result = append(result, w._CollectCmdsubs(operand)...)
	}
	condition = _getattr(node, "condition", nil).(Node)
	if condition != nil {
		result = append(result, w._CollectCmdsubs(condition)...)
	}
	trueValue = _getattr(node, "true_value", nil).(Node)
	if trueValue != nil {
		result = append(result, w._CollectCmdsubs(trueValue)...)
	}
	falseValue = _getattr(node, "false_value", nil).(Node)
	if falseValue != nil {
		result = append(result, w._CollectCmdsubs(falseValue)...)
	}
	return result
}

func (w *Word) _CollectProcsubs(node Node) []Node {
	var result []Node
	_ = result
	var nodeKind interface{}
	_ = nodeKind
	var elements []Node
	_ = elements
	var parts []Node
	_ = parts
	result = []Node{}
	nodeKind = _getattr(node, "kind", nil)
	if nodeKind == "procsub" {
		result = append(result, node)
	} else if nodeKind == "array" {
		elements = _getattr(node, "elements", []interface{}{}).([]Node)
		for _, elem := range elements {
			parts = _getattr(elem, "parts", []interface{}{}).([]Node)
			for _, p := range parts {
				if _getattr(p, "kind", nil) == "procsub" {
					result = append(result, p)
				} else {
					result = append(result, w._CollectProcsubs(p)...)
				}
			}
		}
	}
	return result
}

func (w *Word) _FormatCommandSubstitutions(value string, inArith bool) string {
	var cmdsubParts []Node
	_ = cmdsubParts
	var procsubParts []Node
	_ = procsubParts
	var hasArith bool
	_ = hasArith
	var hasBraceCmdsub bool
	_ = hasBraceCmdsub
	var hasUntrackedCmdsub bool
	_ = hasUntrackedCmdsub
	var hasUntrackedProcsub bool
	_ = hasUntrackedProcsub
	var idx int
	_ = idx
	var scanQuote *QuoteState
	_ = scanQuote
	var hasParamWithProcsubPattern bool
	_ = hasParamWithProcsubPattern
	var result []string
	_ = result
	var i int
	_ = i
	var cmdsubIdx int
	_ = cmdsubIdx
	var procsubIdx int
	_ = procsubIdx
	var mainQuote *QuoteState
	_ = mainQuote
	var extglobDepth int
	_ = extglobDepth
	var deprecatedArithDepth int
	_ = deprecatedArithDepth
	var arithDepth int
	_ = arithDepth
	var arithParenDepth int
	_ = arithParenDepth
	var j int
	_ = j
	var inner string
	_ = inner
	var node Node
	_ = node
	var formatted string
	_ = formatted
	var parser *Parser
	_ = parser
	var parsed Node
	_ = parsed
	var hasPipe bool
	_ = hasPipe
	var prefix string
	_ = prefix
	var origInner string
	_ = origInner
	var endsWithNewline bool
	_ = endsWithNewline
	var suffix string
	_ = suffix
	var isProcsub bool
	_ = isProcsub
	var direction string
	_ = direction
	var compact bool
	_ = compact
	var rawContent string
	_ = rawContent
	var leadingWsEnd int
	_ = leadingWsEnd
	var leadingWs string
	_ = leadingWs
	var stripped string
	_ = stripped
	var normalizedWs string
	_ = normalizedWs
	var spaced string
	_ = spaced
	var rawStripped string
	_ = rawStripped
	var finalOutput string
	_ = finalOutput
	var depth int
	_ = depth
	var terminator string
	_ = terminator
	var braceQuote *QuoteState
	_ = braceQuote
	var c string
	_ = c
	var formattedInner string
	_ = formattedInner
	cmdsubParts = []Node{}
	procsubParts = []Node{}
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
	hasBraceCmdsub = strings.Index(value, "${ ") != -1 || strings.Index(value, "${\t") != -1 || strings.Index(value, "${\n") != -1 || strings.Index(value, "${|") != -1
	hasUntrackedCmdsub = false
	hasUntrackedProcsub = false
	idx = 0
	scanQuote = NewQuoteState()
	for idx < len(value) {
		if string(value[idx]) == "\"" {
			scanQuote.Double = !(scanQuote.Double)
			idx += 1
		} else if string(value[idx]) == "'" && !(scanQuote.Double) {
			idx += 1
			for idx < len(value) && string(value[idx]) != "'" {
				idx += 1
			}
			if idx < len(value) {
				idx += 1
			}
		} else if strings.HasPrefix(value[idx:], "$(") && !(strings.HasPrefix(value[idx:], "$((")) && !(_IsBackslashEscaped(value, idx)) && !(_IsDollarDollarParen(value, idx)) {
			hasUntrackedCmdsub = true
			break
		} else if strings.HasPrefix(value[idx:], "<(") || strings.HasPrefix(value[idx:], ">(") && !(scanQuote.Double) {
			if idx == 0 || !(unicode.IsLetter(_runeFromChar(string(value[idx-1]))) || unicode.IsDigit(_runeFromChar(string(value[idx-1])))) && !strings.Contains("\"'", string(value[idx-1])) {
				hasUntrackedProcsub = true
				break
			}
			idx += 1
		} else {
			idx += 1
		}
	}
	hasParamWithProcsubPattern = strings.Contains(value, "${") && strings.Contains(value, "<(") || strings.Contains(value, ">(")
	if !(len(cmdsubParts) > 0) && !(len(procsubParts) > 0) && !(hasBraceCmdsub) && !(hasUntrackedCmdsub) && !(hasUntrackedProcsub) && !(hasParamWithProcsubPattern) {
		return value
	}
	result = []string{}
	i = 0
	cmdsubIdx = 0
	procsubIdx = 0
	mainQuote = NewQuoteState()
	extglobDepth = 0
	deprecatedArithDepth = 0
	arithDepth = 0
	arithParenDepth = 0
	for i < len(value) {
		if i > 0 && _IsExtglobPrefix(string(value[i-1])) && string(value[i]) == "(" && !(_IsBackslashEscaped(value, i-1)) {
			extglobDepth += 1
			result = append(result, string(value[i]))
			i += 1
			continue
		}
		if string(value[i]) == ")" && extglobDepth > 0 {
			extglobDepth -= 1
			result = append(result, string(value[i]))
			i += 1
			continue
		}
		if strings.HasPrefix(value[i:], "$[") && !(_IsBackslashEscaped(value, i)) {
			deprecatedArithDepth += 1
			result = append(result, string(value[i]))
			i += 1
			continue
		}
		if string(value[i]) == "]" && deprecatedArithDepth > 0 {
			deprecatedArithDepth -= 1
			result = append(result, string(value[i]))
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
			if string(value[i]) == "(" {
				arithParenDepth += 1
				result = append(result, string(value[i]))
				i += 1
				continue
			} else if string(value[i]) == ")" {
				arithParenDepth -= 1
				result = append(result, string(value[i]))
				i += 1
				continue
			}
		}
		if _IsExpansionStart(value, i, "$((") && !(hasArith) {
			j = _FindCmdsubEnd(value, i+2)
			result = append(result, value[i:j])
			if cmdsubIdx < len(cmdsubParts) {
				cmdsubIdx += 1
			}
			i = j
			continue
		}
		if strings.HasPrefix(value[i:], "$(") && !(strings.HasPrefix(value[i:], "$((")) && !(_IsBackslashEscaped(value, i)) && !(_IsDollarDollarParen(value, i)) {
			j = _FindCmdsubEnd(value, i+2)
			if extglobDepth > 0 {
				result = append(result, value[i:j])
				if cmdsubIdx < len(cmdsubParts) {
					cmdsubIdx += 1
				}
				i = j
				continue
			}
			inner = value[i+2 : j-1]
			if cmdsubIdx < len(cmdsubParts) {
				node = cmdsubParts[cmdsubIdx]
				formatted = _FormatCmdsubNode(node.(*CommandSubstitution).Command, 0, false, false, false)
				cmdsubIdx += 1
			} else {
				panic("TODO: incomplete implementation")
			}
			if strings.HasPrefix(formatted, "(") {
				result = append(result, "$( "+formatted+")")
			} else {
				result = append(result, "$("+formatted+")")
			}
			i = j
		} else if string(value[i]) == "`" && cmdsubIdx < len(cmdsubParts) {
			j = i + 1
			for j < len(value) {
				if string(value[j]) == "\\" && j+1 < len(value) {
					j += 2
					continue
				}
				if string(value[j]) == "`" {
					j += 1
					break
				}
				j += 1
			}
			result = append(result, value[i:j])
			cmdsubIdx += 1
			i = j
		} else if _IsExpansionStart(value, i, "${") && i+2 < len(value) && _IsFunsubChar(string(value[i+2])) && !(_IsBackslashEscaped(value, i)) {
			j = _FindFunsubEnd(value, i+2)
			if cmdsubIdx < len(cmdsubParts) && _getattr(cmdsubParts[cmdsubIdx], "brace", false).(bool) {
				node = cmdsubParts[cmdsubIdx]
				formatted = _FormatCmdsubNode(node.(*CommandSubstitution).Command, 0, false, false, false)
				hasPipe = string(value[i+2]) == "|"
				prefix = _ternary(hasPipe, "${|", "${ ")
				origInner = value[i+2 : j-1]
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
				result = append(result, value[i:j])
			}
			i = j
		} else if strings.HasPrefix(value[i:], ">(") || strings.HasPrefix(value[i:], "<(") && !(mainQuote.Double) && deprecatedArithDepth == 0 && arithDepth == 0 {
			isProcsub = i == 0 || !(unicode.IsLetter(_runeFromChar(string(value[i-1]))) || unicode.IsDigit(_runeFromChar(string(value[i-1])))) && !strings.Contains("\"'", string(value[i-1]))
			if extglobDepth > 0 {
				j = _FindCmdsubEnd(value, i+2)
				result = append(result, value[i:j])
				if procsubIdx < len(procsubParts) {
					procsubIdx += 1
				}
				i = j
				continue
			}
			if procsubIdx < len(procsubParts) {
				direction = string(value[i])
				j = _FindCmdsubEnd(value, i+2)
				node = procsubParts[procsubIdx]
				compact = _StartsWithSubshell(node.(*CommandSubstitution).Command)
				formatted = _FormatCmdsubNode(node.(*CommandSubstitution).Command, 0, true, compact, true)
				rawContent = value[i+2 : j-1]
				if node.(*CommandSubstitution).Command.Kind() == "subshell" {
					leadingWsEnd = 0
					for leadingWsEnd < len(rawContent) && strings.Contains(" \t\n", string(rawContent[leadingWsEnd])) {
						leadingWsEnd += 1
					}
					leadingWs = rawContent[0:leadingWsEnd]
					stripped = rawContent[leadingWsEnd:]
					if strings.HasPrefix(stripped, "(") {
						if len(leadingWs) > 0 {
							normalizedWs = strings.ReplaceAll(strings.ReplaceAll(leadingWs, "\n", " "), "\t", " ")
							spaced = _FormatCmdsubNode(node.(*CommandSubstitution).Command, 0, false, false, false)
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
				rawContent = value[i+2 : j-1]
				rawStripped = strings.ReplaceAll(rawContent, "\\\n", "")
				if _StartsWithSubshell(node.(*CommandSubstitution).Command) && formatted != rawStripped {
					result = append(result, direction+"("+rawStripped+")")
				} else {
					finalOutput = direction + "(" + formatted + ")"
					result = append(result, finalOutput)
				}
				procsubIdx += 1
				i = j
			} else if isProcsub && len(w.Parts) > 0 {
				direction = string(value[i])
				j = _FindCmdsubEnd(value, i+2)
				if j > len(value) || j > 0 && j <= len(value) && string(value[j-1]) != ")" {
					result = append(result, string(value[i]))
					i += 1
					continue
				}
				inner = value[i+2 : j-1]
				panic("TODO: incomplete implementation")
			} else if isProcsub {
				direction = string(value[i])
				j = _FindCmdsubEnd(value, i+2)
				if j > len(value) || j > 0 && j <= len(value) && string(value[j-1]) != ")" {
					result = append(result, string(value[i]))
					i += 1
					continue
				}
				inner = value[i+2 : j-1]
				if inArith {
					result = append(result, direction+"("+inner+")")
				} else if len(strings.TrimSpace(inner)) > 0 {
					stripped = strings.TrimLeft(inner, " \t")
					result = append(result, direction+"("+stripped+")")
				} else {
					result = append(result, direction+"("+inner+")")
				}
				i = j
			} else {
				result = append(result, string(value[i]))
				i += 1
			}
		} else if _IsExpansionStart(value, i, "${ ") || _IsExpansionStart(value, i, "${\t") || _IsExpansionStart(value, i, "${\n") || _IsExpansionStart(value, i, "${|") && !(_IsBackslashEscaped(value, i)) {
			prefix = strings.ReplaceAll(strings.ReplaceAll(value[i:i+3], "\t", " "), "\n", " ")
			j = i + 3
			depth = 1
			for j < len(value) && depth > 0 {
				if string(value[j]) == "{" {
					depth += 1
				} else if string(value[j]) == "}" {
					depth -= 1
				}
				j += 1
			}
			inner = value[i+2 : j-1]
			if strings.TrimSpace(inner) == "" {
				result = append(result, "${ }")
			} else {
				panic("TODO: incomplete implementation")
			}
			i = j
		} else if _IsExpansionStart(value, i, "${") && !(_IsBackslashEscaped(value, i)) {
			j = i + 2
			depth = 1
			braceQuote = NewQuoteState()
			for j < len(value) && depth > 0 {
				c = string(value[j])
				if c == "\\" && j+1 < len(value) && !(braceQuote.Single) {
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
				inner = value[i+2 : j]
			} else {
				inner = value[i+2 : j-1]
			}
			formattedInner = w._FormatCommandSubstitutions(inner, false)
			formattedInner = w._NormalizeExtglobWhitespace(formattedInner)
			if depth == 0 {
				result = append(result, "${"+formattedInner+"}")
			} else {
				result = append(result, "${"+formattedInner)
			}
			i = j
		} else if string(value[i]) == "\"" {
			mainQuote.Double = !(mainQuote.Double)
			result = append(result, string(value[i]))
			i += 1
		} else if string(value[i]) == "'" && !(mainQuote.Double) {
			j = i + 1
			for j < len(value) && string(value[j]) != "'" {
				j += 1
			}
			if j < len(value) {
				j += 1
			}
			result = append(result, value[i:j])
			i = j
		} else {
			result = append(result, string(value[i]))
			i += 1
		}
	}
	return strings.Join(result, "")
}

func (w *Word) _NormalizeExtglobWhitespace(value string) string {
	var result []string
	_ = result
	var i int
	_ = i
	var extglobQuote *QuoteState
	_ = extglobQuote
	var deprecatedArithDepth int
	_ = deprecatedArithDepth
	var prefixChar string
	_ = prefixChar
	var depth int
	_ = depth
	var patternParts []string
	_ = patternParts
	var currentPart []string
	_ = currentPart
	var hasPipe bool
	_ = hasPipe
	var partContent string
	_ = partContent
	result = []string{}
	i = 0
	extglobQuote = NewQuoteState()
	deprecatedArithDepth = 0
	for i < len(value) {
		if string(value[i]) == "\"" {
			extglobQuote.Double = !(extglobQuote.Double)
			result = append(result, string(value[i]))
			i += 1
			continue
		}
		if strings.HasPrefix(value[i:], "$[") && !(_IsBackslashEscaped(value, i)) {
			deprecatedArithDepth += 1
			result = append(result, string(value[i]))
			i += 1
			continue
		}
		if string(value[i]) == "]" && deprecatedArithDepth > 0 {
			deprecatedArithDepth -= 1
			result = append(result, string(value[i]))
			i += 1
			continue
		}
		if i+1 < len(value) && string(value[i+1]) == "(" {
			prefixChar = string(value[i])
			if strings.Contains("><", prefixChar) && !(extglobQuote.Double) && deprecatedArithDepth == 0 {
				result = append(result, prefixChar)
				result = append(result, "(")
				i += 2
				depth = 1
				patternParts = []string{}
				currentPart = []string{}
				hasPipe = false
				for i < len(value) && depth > 0 {
					if string(value[i]) == "\\" && i+1 < len(value) {
						currentPart = append(currentPart, value[i:i+2])
						i += 2
						continue
					} else if string(value[i]) == "(" {
						depth += 1
						currentPart = append(currentPart, string(value[i]))
						i += 1
					} else if string(value[i]) == ")" {
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
						currentPart = append(currentPart, string(value[i]))
						i += 1
					} else if string(value[i]) == "|" && depth == 1 {
						if i+1 < len(value) && string(value[i+1]) == "|" {
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
						currentPart = append(currentPart, string(value[i]))
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
		result = append(result, string(value[i]))
		i += 1
	}
	return strings.Join(result, "")
}

func (w *Word) GetCondFormattedValue() string {
	var value string
	_ = value
	value = w._ExpandAllAnsiCQuotes(w.Value)
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
	var parts []string
	_ = parts
	var inner string
	_ = inner
	parts = []string{}
	for _, w := range c.Words {
		parts = append(parts, w.ToSexp())
	}
	for _, r := range c.Redirects {
		parts = append(parts, r.ToSexp())
	}
	inner = strings.Join(parts, " ")
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
	var cmds []interface{}
	_ = cmds
	var i int
	_ = i
	var cmd Node
	_ = cmd
	var needsRedirect bool
	_ = needsRedirect
	var pair interface{}
	_ = pair
	var needs bool
	_ = needs
	var lastPair interface{}
	_ = lastPair
	var lastCmd Node
	_ = lastCmd
	var lastNeeds bool
	_ = lastNeeds
	var result string
	_ = result
	var j int
	_ = j
	if len(p.Commands) == 1 {
		return p.Commands[0].ToSexp()
	}
	cmds = []interface{}{}
	i = 0
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
	lastPair = cmds[len(cmds)-1]
	lastCmd = lastPair.([]interface{})[0].(Node)
	lastNeeds = lastPair.([]interface{})[1].(bool)
	result = p._CmdSexp(lastCmd, lastNeeds)
	j = len(cmds) - 2
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
	_ = parts
	if !(needsRedirect) {
		return cmd.ToSexp()
	}
	if cmd.Kind() == "command" {
		parts = []string{}
		for _, w := range cmd.(*Command).Words {
			parts = append(parts, w.ToSexp())
		}
		for _, r := range cmd.(*Command).Redirects {
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
	_ = parts
	var opNames map[string]string
	_ = opNames
	var left []Node
	_ = left
	var right []Node
	_ = right
	var leftSexp string
	_ = leftSexp
	var rightSexp string
	_ = rightSexp
	var innerParts []Node
	_ = innerParts
	var innerList Node
	_ = innerList
	parts = append([]Node{}, l.Parts...)
	opNames = map[string]string{"&&": "and", "||": "or", ";": "semi", "\n": "semi", "&": "background"}
	for len(parts) > 1 && parts[len(parts)-1].Kind() == "operator" && parts[len(parts)-1].(*Operator).Op == ";" || parts[len(parts)-1].(*Operator).Op == "\n" {
		parts = parts[0 : len(parts)-1]
	}
	if len(parts) == 1 {
		return parts[0].ToSexp()
	}
	if parts[len(parts)-1].Kind() == "operator" && parts[len(parts)-1].(*Operator).Op == "&" {
		for i := len(parts) - 3; i > 0; i += -2 {
			if parts[i].Kind() == "operator" && parts[i].(*Operator).Op == ";" || parts[i].(*Operator).Op == "\n" {
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
	var semiPositions []int
	_ = semiPositions
	var segments [][]Node
	_ = segments
	var start int
	_ = start
	var seg []Node
	_ = seg
	var result string
	_ = result
	semiPositions = []int{}
	for i := 0; i < len(parts); i++ {
		if parts[i].Kind() == "operator" && parts[i].(*Operator).Op == ";" || parts[i].(*Operator).Op == "\n" {
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
	var ampPositions []int
	_ = ampPositions
	var segments [][]Node
	_ = segments
	var start int
	_ = start
	var result string
	_ = result
	if len(parts) == 1 {
		return parts[0].ToSexp()
	}
	ampPositions = []int{}
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
	_ = result
	var op Node
	_ = op
	var cmd Node
	_ = cmd
	var opName string
	_ = opName
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
	var names map[string]string
	_ = names
	names = map[string]string{"&&": "and", "||": "or", ";": "semi", "&": "bg", "|": "pipe"}
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
	_ = op
	var j int
	_ = j
	var targetVal string
	_ = targetVal
	var raw string
	_ = raw
	var fdTarget string
	_ = fdTarget
	var outVal string
	_ = outVal
	op = strings.TrimLeft(r.Op, "0123456789")
	if strings.HasPrefix(op, "{") {
		j = 1
		if j < len(op) && unicode.IsLetter(_runeFromChar(string(op[j]))) || string(op[j]) == "_" {
			j += 1
			for j < len(op) && (unicode.IsLetter(_runeFromChar(string(op[j]))) || unicode.IsDigit(_runeFromChar(string(op[j])))) || string(op[j]) == "_" {
				j += 1
			}
			if j < len(op) && string(op[j]) == "[" {
				j += 1
				for j < len(op) && string(op[j]) != "]" {
					j += 1
				}
				if j < len(op) && string(op[j]) == "]" {
					j += 1
				}
			}
			if j < len(op) && string(op[j]) == "}" {
				op = op[j+1 : len(op)]
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
		raw = targetVal[1:len(targetVal)]
		if unicode.IsDigit(_runeFromChar(raw)) && _mustAtoi(raw) <= 2147483647 {
			return "(redirect \"" + op + "\" " + fmt.Sprint(_mustAtoi(raw)) + ")"
		}
		if strings.HasSuffix(raw, "-") && unicode.IsDigit(_runeFromChar(raw[0:len(raw)-1])) && _mustAtoi(raw[0:len(raw)-1]) <= 2147483647 {
			return "(redirect \"" + op + "\" " + fmt.Sprint(_mustAtoi(raw[0:len(raw)-1])) + ")"
		}
		if targetVal == "&-" {
			return "(redirect \">&-\" 0)"
		}
		fdTarget = _ternary(strings.HasSuffix(raw, "-"), raw[0:len(raw)-1], raw)
		return "(redirect \"" + op + "\" \"" + fdTarget + "\")"
	}
	if op == ">&" || op == "<&" {
		if unicode.IsDigit(_runeFromChar(targetVal)) && _mustAtoi(targetVal) <= 2147483647 {
			return "(redirect \"" + op + "\" " + fmt.Sprint(_mustAtoi(targetVal)) + ")"
		}
		if targetVal == "-" {
			return "(redirect \">&-\" 0)"
		}
		if strings.HasSuffix(targetVal, "-") && unicode.IsDigit(_runeFromChar(targetVal[0:len(targetVal)-1])) && _mustAtoi(targetVal[0:len(targetVal)-1]) <= 2147483647 {
			return "(redirect \"" + op + "\" " + fmt.Sprint(_mustAtoi(targetVal[0:len(targetVal)-1])) + ")"
		}
		outVal = _ternary(strings.HasSuffix(targetVal, "-"), targetVal[0:len(targetVal)-1], targetVal)
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
	var op string
	_ = op
	var content string
	_ = content
	op = _ternary(h.Strip_tabs, "<<-", "<<")
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
	var base string
	_ = base
	base = "(subshell " + s.Body.ToSexp() + ")"
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
	var base string
	_ = base
	base = "(brace-group " + b.Body.ToSexp() + ")"
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
	_ = result
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
	var base string
	_ = base
	base = "(while " + w.Condition.ToSexp() + " " + w.Body.ToSexp() + ")"
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
	var base string
	_ = base
	base = "(until " + u.Condition.ToSexp() + " " + u.Body.ToSexp() + ")"
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
	_ = suffix
	var redirectParts []string
	_ = redirectParts
	var tempWord *Word
	_ = tempWord
	var varFormatted string
	_ = varFormatted
	var varEscaped string
	_ = varEscaped
	var wordParts []string
	_ = wordParts
	var wordStrs string
	_ = wordStrs
	suffix = ""
	if len(f.Redirects) > 0 {
		redirectParts = []string{}
		for _, r := range f.Redirects {
			redirectParts = append(redirectParts, r.ToSexp())
		}
		suffix = " " + strings.Join(redirectParts, " ")
	}
	tempWord = NewWord(f.Var, []Node{})
	varFormatted = tempWord._FormatCommandSubstitutions(f.Var, false)
	varEscaped = strings.ReplaceAll(strings.ReplaceAll(varFormatted, "\\", "\\\\"), "\"", "\\\"")
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
	_ = suffix
	var redirectParts []string
	_ = redirectParts
	var initVal string
	_ = initVal
	var condVal string
	_ = condVal
	var incrVal string
	_ = incrVal
	var initStr string
	_ = initStr
	var condStr string
	_ = condStr
	var incrStr string
	_ = incrStr
	var bodyStr string
	_ = bodyStr
	suffix = ""
	if len(f.Redirects) > 0 {
		redirectParts = []string{}
		for _, r := range f.Redirects {
			redirectParts = append(redirectParts, r.ToSexp())
		}
		suffix = " " + strings.Join(redirectParts, " ")
	}
	initVal = _ternary(f.Init != "", f.Init, "1")
	condVal = _ternary(f.Cond != "", f.Cond, "1")
	incrVal = _ternary(f.Incr != "", f.Incr, "1")
	initStr = _FormatArithVal(initVal)
	condStr = _FormatArithVal(condVal)
	incrStr = _FormatArithVal(incrVal)
	bodyStr = f.Body.ToSexp()
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
	_ = suffix
	var redirectParts []string
	_ = redirectParts
	var varEscaped string
	_ = varEscaped
	var wordParts []string
	_ = wordParts
	var wordStrs string
	_ = wordStrs
	var inClause string
	_ = inClause
	suffix = ""
	if len(s.Redirects) > 0 {
		redirectParts = []string{}
		for _, r := range s.Redirects {
			redirectParts = append(redirectParts, r.ToSexp())
		}
		suffix = " " + strings.Join(redirectParts, " ")
	}
	varEscaped = strings.ReplaceAll(strings.ReplaceAll(s.Var, "\\", "\\\\"), "\"", "\\\"")
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
	var parts []string
	_ = parts
	var base string
	_ = base
	parts = []string{}
	parts = append(parts, "(case "+c.Word.ToSexp())
	for _, p := range c.Patterns {
		parts = append(parts, p.ToSexp())
	}
	base = strings.Join(parts, " ") + ")"
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
	var alternatives []string
	_ = alternatives
	var current []string
	_ = current
	var i int
	_ = i
	var depth int
	_ = depth
	var ch string
	_ = ch
	var result interface{}
	_ = result
	var wordList []string
	_ = wordList
	var patternStr string
	_ = patternStr
	var parts []string
	_ = parts
	alternatives = []string{}
	current = []string{}
	i = 0
	depth = 0
	for i < len(c.Pattern) {
		ch = string(c.Pattern[i])
		if ch == "\\" && i+1 < len(c.Pattern) {
			current = append(current, c.Pattern[i:i+2])
			i += 2
		} else if ch == "@" || ch == "?" || ch == "*" || ch == "+" || ch == "!" && i+1 < len(c.Pattern) && string(c.Pattern[i+1]) == "(" {
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
			result = _ConsumeBracketClass(c.Pattern, i, depth)
			i = result.([]interface{})[0].(int)
			current = append(current, result.([]interface{})[1].([]string)...)
		} else if ch == "'" && depth == 0 {
			result = _ConsumeSingleQuote(c.Pattern, i)
			i = result.([]interface{})[0].(int)
			current = append(current, result.([]interface{})[1].([]string)...)
		} else if ch == "\"" && depth == 0 {
			result = _ConsumeDoubleQuote(c.Pattern, i)
			i = result.([]interface{})[0].(int)
			current = append(current, result.([]interface{})[1].([]string)...)
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
	wordList = []string{}
	for _, alt := range alternatives {
		wordList = append(wordList, NewWord(alt, nil).ToSexp())
	}
	patternStr = strings.Join(wordList, " ")
	parts = []string{"(pattern (" + patternStr + ")"}
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
	var escapedParam string
	_ = escapedParam
	var escapedOp string
	_ = escapedOp
	var argVal string
	_ = argVal
	var escapedArg string
	_ = escapedArg
	escapedParam = strings.ReplaceAll(strings.ReplaceAll(p.Param, "\\", "\\\\"), "\"", "\\\"")
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
	var escaped string
	_ = escaped
	escaped = strings.ReplaceAll(strings.ReplaceAll(p.Param, "\\", "\\\\"), "\"", "\\\"")
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
	var escaped string
	_ = escaped
	var escapedOp string
	_ = escapedOp
	var argVal string
	_ = argVal
	var escapedArg string
	_ = escapedArg
	escaped = strings.ReplaceAll(strings.ReplaceAll(p.Param, "\\", "\\\\"), "\"", "\\\"")
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
	if a.Expression == nil {
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
	var formatted string
	_ = formatted
	var escaped string
	_ = escaped
	var result string
	_ = result
	var redirectParts []string
	_ = redirectParts
	var redirectSexps string
	_ = redirectSexps
	formatted = NewWord(a.Raw_content, nil)._FormatCommandSubstitutions(a.Raw_content, true)
	escaped = strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(formatted, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n"), "\t", "\\t")
	result = "(arith (word \"" + escaped + "\"))"
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
	var escaped string
	_ = escaped
	escaped = strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(a.Expression, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n")
	return "(arith-deprecated \"" + escaped + "\")"
}

func NewArithConcat(parts []Node) *ArithConcat {
	a := &ArithConcat{}
	a.kind = "arith-concat"
	a.Parts = parts
	return a
}

func (a *ArithConcat) ToSexp() string {
	var sexps []string
	_ = sexps
	sexps = []string{}
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
	var escaped string
	_ = escaped
	escaped = strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(a.Content, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n")
	return "(ansi-c \"" + escaped + "\")"
}

func NewLocaleString(content string) *LocaleString {
	l := &LocaleString{}
	l.kind = "locale"
	l.Content = content
	return l
}

func (l *LocaleString) ToSexp() string {
	var escaped string
	_ = escaped
	escaped = strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(l.Content, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n")
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
	if n.Pipeline == nil {
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
	if t.Pipeline == nil {
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
	var bodyKind interface{}
	_ = bodyKind
	var escaped string
	_ = escaped
	var result string
	_ = result
	var redirectParts []string
	_ = redirectParts
	var redirectSexps string
	_ = redirectSexps
	bodyKind = _getattr(c.Body, "kind", nil)
	if bodyKind == nil {
		escaped = strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(c.Body.(string), "\\", "\\\\"), "\"", "\\\""), "\n", "\\n")
		result = "(cond \"" + escaped + "\")"
	} else {
		result = "(cond " + c.Body.(Node).ToSexp() + ")"
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
	var operandVal string
	_ = operandVal
	operandVal = u.Operand.(*Word).GetCondFormattedValue()
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
	var leftVal string
	_ = leftVal
	var rightVal string
	_ = rightVal
	leftVal = b.Left.(*Word).GetCondFormattedValue()
	rightVal = b.Right.(*Word).GetCondFormattedValue()
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
	var parts []string
	_ = parts
	var inner string
	_ = inner
	if !(len(a.Elements) > 0) {
		return "(array)"
	}
	parts = []string{}
	for _, e := range a.Elements {
		parts = append(parts, e.ToSexp())
	}
	inner = strings.Join(parts, " ")
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
	_ = name
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
	p.Pos = 0
	p.Length = len(source)
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
	var firstChar string
	_ = firstChar
	if p._Dolbrace_state == DolbraceState_NONE {
		return
	}
	if op == "" || len(op) == 0 {
		return
	}
	firstChar = string(op[0])
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
	var savedPos int
	_ = savedPos
	var result *Token
	_ = result
	if p._Lexer._Token_cache != nil && p._Lexer._Token_cache.Pos == p.Pos && p._Lexer._Cached_word_context == p._Word_context && p._Lexer._Cached_at_command_start == p._At_command_start && p._Lexer._Cached_in_array_literal == p._In_array_literal && p._Lexer._Cached_in_assign_builtin == p._In_assign_builtin {
		return p._Lexer._Token_cache
	}
	savedPos = p.Pos
	p._SyncLexer()
	result = p._Lexer.PeekToken()
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
	_ = tok
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
	var result bool
	_ = result
	p._SyncLexer()
	result = p._Lexer._SkipComment()
	p._SyncParser()
	return result
}

func (p *Parser) _LexIsCommandTerminator() bool {
	var tok *Token
	_ = tok
	var t int
	_ = t
	tok = p._LexPeekToken()
	t = tok.Type
	return _containsAny([]interface{}{TokenType_EOF, TokenType_NEWLINE, TokenType_PIPE, TokenType_SEMI, TokenType_LPAREN, TokenType_RPAREN, TokenType_AMP}, t)
}

func (p *Parser) _LexPeekOperator() (int, string) {
	var tok *Token
	_ = tok
	var t int
	_ = t
	tok = p._LexPeekToken()
	t = tok.Type
	if t >= TokenType_SEMI && t <= TokenType_GREATER || t >= TokenType_AND_AND && t <= TokenType_PIPE_AMP {
		return t, tok.Value
	}
	return 0, ""
}

func (p *Parser) _LexPeekReservedWord() string {
	var tok *Token
	_ = tok
	var word string
	_ = word
	tok = p._LexPeekToken()
	if tok.Type != TokenType_WORD {
		return ""
	}
	word = tok.Value
	if strings.HasSuffix(word, "\\\n") {
		word = word[0 : len(word)-2]
	}
	if ReservedWords[word] || _containsAny([]interface{}{"{", "}", "[[", "]]", "!", "time"}, word) {
		return word
	}
	return ""
}

func (p *Parser) _LexIsAtReservedWord(word string) bool {
	var reserved string
	_ = reserved
	reserved = p._LexPeekReservedWord()
	return reserved == word
}

func (p *Parser) _LexConsumeWord(expected string) bool {
	var tok *Token
	_ = tok
	var word string
	_ = word
	tok = p._LexPeekToken()
	if tok.Type != TokenType_WORD {
		return false
	}
	word = tok.Value
	if strings.HasSuffix(word, "\\\n") {
		word = word[0 : len(word)-2]
	}
	if word == expected {
		p._LexNextToken()
		return true
	}
	return false
}

func (p *Parser) _LexPeekCaseTerminator() string {
	var tok *Token
	_ = tok
	var t int
	_ = t
	tok = p._LexPeekToken()
	t = tok.Type
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
	return string(string(p.Source[p.Pos]))
}

func (p *Parser) Advance() string {
	var ch string
	_ = ch
	if p.AtEnd() {
		return ""
	}
	ch = string(p.Source[p.Pos])
	p.Pos += 1
	return string(ch)
}

func (p *Parser) PeekAt(offset int) string {
	var pos int
	_ = pos
	pos = p.Pos + offset
	if pos < 0 || pos >= p.Length {
		return ""
	}
	return string(string(p.Source[pos]))
}

func (p *Parser) Lookahead(n int) string {
	return p.Source[p.Pos : p.Pos+n]
}

func (p *Parser) _IsBangFollowedByProcsub() bool {
	var nextChar string
	_ = nextChar
	if p.Pos+2 >= p.Length {
		return false
	}
	nextChar = string(p.Source[p.Pos+1])
	if nextChar != ">" && nextChar != "<" {
		return false
	}
	return string(p.Source[p.Pos+2]) == "("
}

func (p *Parser) SkipWhitespace() {
	var ch string
	_ = ch
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
	_ = ch
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
	var ch string
	_ = ch
	var nextPos int
	_ = nextPos
	if p.AtEnd() {
		return false
	}
	ch = p.Peek()
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
		return _IsWordEndContext(string(p.Source[nextPos]))
	}
	return false
}

func (p *Parser) _AtEofToken() bool {
	var tok *Token
	_ = tok
	if p._Eof_token == "" {
		return false
	}
	tok = p._LexPeekToken()
	if p._Eof_token == ")" {
		return tok.Type == TokenType_RPAREN
	}
	if p._Eof_token == "}" {
		return tok.Type == TokenType_WORD && tok.Value == "}"
	}
	return false
}

func (p *Parser) _CollectRedirects() []Node {
	var redirects []Node
	_ = redirects
	var redirect interface{}
	_ = redirect
	redirects = []Node{}
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
	_ = brace
	var body Node
	_ = body
	if p.Peek() == "{" {
		brace = p.ParseBraceGroup()
		if brace == nil {
			panic(NewParseError(fmt.Sprintf("Expected brace group body in %v", context), p._LexPeekToken().Pos, 0))
		}
		return brace.Body
	}
	if p._LexConsumeWord("do") {
		body = p.ParseListUntil(map[string]struct{}{"done": {}})
		if body == nil {
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
	var savedPos int
	_ = savedPos
	var chars []string
	_ = chars
	var ch string
	_ = ch
	var word string
	_ = word
	savedPos = p.Pos
	p.SkipWhitespace()
	if p.AtEnd() || _IsMetachar(p.Peek()) {
		p.Pos = savedPos
		return ""
	}
	chars = []string{}
	for !(p.AtEnd()) && !(_IsMetachar(p.Peek())) {
		ch = p.Peek()
		if _IsQuote(ch) {
			break
		}
		if ch == "\\" && p.Pos+1 < p.Length && string(p.Source[p.Pos+1]) == "\n" {
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
	var savedPos int
	_ = savedPos
	var word string
	_ = word
	var keywordWord string
	_ = keywordWord
	var hasLeadingBrace bool
	_ = hasLeadingBrace
	savedPos = p.Pos
	p.SkipWhitespace()
	word = p.PeekWord()
	keywordWord = word
	hasLeadingBrace = false
	if word != "" && p._In_process_sub && len(word) > 1 && string(word[0]) == "}" {
		keywordWord = word[1:]
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
	for p.Peek() == "\\" && p.Pos+1 < p.Length && string(p.Source[p.Pos+1]) == "\n" {
		p.Advance()
		p.Advance()
	}
	return true
}

func (p *Parser) _IsWordTerminator(ctx int, ch string, bracketDepth int, parenDepth int) bool {
	p._SyncLexer()
	return p._Lexer._IsWordTerminator(ctx, ch, bracketDepth, parenDepth)
}

func (p *Parser) _ScanDoubleQuote(chars []string, parts []Node, start int, handleLineContinuation bool) {
	var c string
	_ = c
	var nextC string
	_ = nextC
	chars = append(chars, "\"")
	for !(p.AtEnd()) && p.Peek() != "\"" {
		c = p.Peek()
		if c == "\\" && p.Pos+1 < p.Length {
			nextC = string(p.Source[p.Pos+1])
			if handleLineContinuation && nextC == "\n" {
				p.Advance()
				p.Advance()
			} else {
				chars = append(chars, p.Advance())
				chars = append(chars, p.Advance())
			}
		} else if c == "$" {
			if !(p._ParseDollarExpansion(chars, parts, true)) {
				chars = append(chars, p.Advance())
			}
		} else {
			chars = append(chars, p.Advance())
		}
	}
	if p.AtEnd() {
		panic(NewParseError("Unterminated double quote", start, 0))
	}
	chars = append(chars, p.Advance())
}

func (p *Parser) _ParseDollarExpansion(chars []string, parts []Node, inDquote bool) bool {
	var result0 Node
	_ = result0
	var result1 string
	_ = result1
	if p.Pos+2 < p.Length && string(p.Source[p.Pos+1]) == "(" && string(p.Source[p.Pos+2]) == "(" {
		result0, result1 = p._ParseArithmeticExpansion()
		if result0 != nil {
			parts = append(parts, result0.(Node))
			chars = append(chars, result1)
			return true
		}
		result0, result1 = p._ParseCommandSubstitution()
		if result0 != nil {
			parts = append(parts, result0.(Node))
			chars = append(chars, result1)
			return true
		}
		return false
	}
	if p.Pos+1 < p.Length && string(p.Source[p.Pos+1]) == "[" {
		result0, result1 = p._ParseDeprecatedArithmetic()
		if result0 != nil {
			parts = append(parts, result0.(Node))
			chars = append(chars, result1)
			return true
		}
		return false
	}
	if p.Pos+1 < p.Length && string(p.Source[p.Pos+1]) == "(" {
		result0, result1 = p._ParseCommandSubstitution()
		if result0 != nil {
			parts = append(parts, result0.(Node))
			chars = append(chars, result1)
			return true
		}
		return false
	}
	result0, result1 = p._ParseParamExpansion(inDquote)
	if result0 != nil {
		parts = append(parts, result0.(Node))
		chars = append(chars, result1)
		return true
	}
	return false
}

func (p *Parser) _ParseWordInternal(ctx int, atCommandStart bool, inArrayLiteral bool) *Word {
	p._Word_context = ctx
	return p.ParseWord(atCommandStart, inArrayLiteral, false)
}

func (p *Parser) ParseWord(atCommandStart bool, inArrayLiteral bool, inAssignBuiltin bool) *Word {
	var tok *Token
	_ = tok
	p.SkipWhitespace()
	if p.AtEnd() {
		return nil
	}
	p._At_command_start = atCommandStart
	p._In_array_literal = inArrayLiteral
	p._In_assign_builtin = inAssignBuiltin
	tok = p._LexPeekToken()
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
	if cmd == nil {
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
	text = p.Source[start:textEnd]
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
	if cmd == nil {
		cmd = NewEmpty()
	}
	p.SkipWhitespaceAndNewlines()
	if p.AtEnd() || p.Peek() != "}" {
		p._RestoreParserState(saved)
		panic(NewMatchedPairError("unexpected EOF looking for `}'", start, 0))
	}
	p.Advance()
	text = p.Source[start:p.Pos]
	p._RestoreParserState(saved)
	p._SyncLexer()
	return NewCommandSubstitution(cmd, true), text
}

func (p *Parser) _IsAssignmentWord(word Node) bool {
	return _Assignment(word.(*Word).Value, 0) != -1
}

func (p *Parser) _ParseBacktickSubstitution() (Node, string) {
	var start int
	_ = start
	var contentChars []string
	_ = contentChars
	var textChars []string
	_ = textChars
	var pendingHeredocs []interface{}
	_ = pendingHeredocs
	var inHeredocBody bool
	_ = inHeredocBody
	var currentHeredocDelim string
	_ = currentHeredocDelim
	var currentHeredocStrip bool
	_ = currentHeredocStrip
	var lineStart int
	_ = lineStart
	var lineEnd int
	_ = lineEnd
	var line string
	_ = line
	var checkLine string
	_ = checkLine
	var tabsStripped int
	_ = tabsStripped
	var endPos int
	_ = endPos
	var c string
	_ = c
	var nextC string
	_ = nextC
	var escaped string
	_ = escaped
	var ch string
	_ = ch
	var quote string
	_ = quote
	var stripTabs bool
	_ = stripTabs
	var delimiterChars []string
	_ = delimiterChars
	var dch string
	_ = dch
	var closing string
	_ = closing
	var esc string
	_ = esc
	var delimiter string
	_ = delimiter
	var text string
	_ = text
	var content string
	_ = content
	var subParser *Parser
	_ = subParser
	var cmd Node
	_ = cmd
	if p.AtEnd() || p.Peek() != "`" {
		return nil, ""
	}
	start = p.Pos
	p.Advance()
	contentChars = []string{}
	textChars = []string{"`"}
	pendingHeredocs = []interface{}{}
	inHeredocBody = false
	currentHeredocDelim = ""
	currentHeredocStrip = false
	for !(p.AtEnd()) && inHeredocBody || p.Peek() != "`" {
		if inHeredocBody {
			lineStart = p.Pos
			lineEnd = lineStart
			for lineEnd < p.Length && string(p.Source[lineEnd]) != "\n" {
				lineEnd += 1
			}
			line = p.Source[lineStart:lineEnd]
			checkLine = _ternary(currentHeredocStrip, strings.TrimLeft(line, "\t"), line)
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
					panic("TODO: incomplete implementation")
				}
			} else if strings.HasPrefix(checkLine, currentHeredocDelim) && len(checkLine) > len(currentHeredocDelim) {
				tabsStripped = len(line) - len(checkLine)
				endPos = tabsStripped + len(currentHeredocDelim)
				for i := 0; i < endPos; i++ {
					contentChars = append(contentChars, string(line[i]))
					textChars = append(textChars, string(line[i]))
				}
				p.Pos = lineStart + endPos
				inHeredocBody = false
				if len(pendingHeredocs) > 0 {
					panic("TODO: incomplete implementation")
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
		c = p.Peek()
		if c == "\\" && p.Pos+1 < p.Length {
			nextC = string(p.Source[p.Pos+1])
			if nextC == "\n" {
				p.Advance()
				p.Advance()
			} else if _IsEscapeCharInBacktick(nextC) {
				p.Advance()
				escaped = p.Advance()
				contentChars = append(contentChars, escaped)
				textChars = append(textChars, "\\")
				textChars = append(textChars, escaped)
			} else {
				ch = p.Advance()
				contentChars = append(contentChars, string(ch))
				textChars = append(textChars, string(ch))
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
				for !(p.AtEnd()) && _IsWhitespaceNoNewline(p.Peek()) {
					ch = p.Advance()
					contentChars = append(contentChars, string(ch))
					textChars = append(textChars, string(ch))
				}
				for !(p.AtEnd()) && !(_IsWhitespace(p.Peek())) && !strings.Contains("()", p.Peek()) {
					if p.Peek() == "\\" && p.Pos+1 < p.Length {
						ch = p.Advance()
						contentChars = append(contentChars, string(ch))
						textChars = append(textChars, string(ch))
						ch = p.Advance()
						contentChars = append(contentChars, string(ch))
						textChars = append(textChars, string(ch))
					} else if strings.Contains("\"'", p.Peek()) {
						quote = p.Peek()
						ch = p.Advance()
						contentChars = append(contentChars, string(ch))
						textChars = append(textChars, string(ch))
						for !(p.AtEnd()) && p.Peek() != quote {
							if quote == "\"" && p.Peek() == "\\" {
								ch = p.Advance()
								contentChars = append(contentChars, string(ch))
								textChars = append(textChars, string(ch))
							}
							ch = p.Advance()
							contentChars = append(contentChars, string(ch))
							textChars = append(textChars, string(ch))
						}
						if !(p.AtEnd()) {
							ch = p.Advance()
							contentChars = append(contentChars, string(ch))
							textChars = append(textChars, string(ch))
						}
					} else {
						ch = p.Advance()
						contentChars = append(contentChars, string(ch))
						textChars = append(textChars, string(ch))
					}
				}
				continue
			}
			contentChars = append(contentChars, p.Advance())
			textChars = append(textChars, "<")
			contentChars = append(contentChars, p.Advance())
			textChars = append(textChars, "<")
			stripTabs = false
			if !(p.AtEnd()) && p.Peek() == "-" {
				stripTabs = true
				contentChars = append(contentChars, p.Advance())
				textChars = append(textChars, "-")
			}
			for !(p.AtEnd()) && _IsWhitespaceNoNewline(p.Peek()) {
				ch = p.Advance()
				contentChars = append(contentChars, string(ch))
				textChars = append(textChars, string(ch))
			}
			delimiterChars = []string{}
			if !(p.AtEnd()) {
				ch = p.Peek()
				if _IsQuote(ch) {
					quote = p.Advance()
					contentChars = append(contentChars, quote)
					textChars = append(textChars, quote)
					for !(p.AtEnd()) && p.Peek() != quote {
						dch = p.Advance()
						contentChars = append(contentChars, dch)
						textChars = append(textChars, dch)
						delimiterChars = append(delimiterChars, dch)
					}
					if !(p.AtEnd()) {
						closing = p.Advance()
						contentChars = append(contentChars, closing)
						textChars = append(textChars, closing)
					}
				} else if ch == "\\" {
					esc = p.Advance()
					contentChars = append(contentChars, esc)
					textChars = append(textChars, esc)
					if !(p.AtEnd()) {
						dch = p.Advance()
						contentChars = append(contentChars, dch)
						textChars = append(textChars, dch)
						delimiterChars = append(delimiterChars, dch)
					}
					for !(p.AtEnd()) && !(_IsMetachar(p.Peek())) {
						dch = p.Advance()
						contentChars = append(contentChars, dch)
						textChars = append(textChars, dch)
						delimiterChars = append(delimiterChars, dch)
					}
				} else {
					for !(p.AtEnd()) && !(_IsMetachar(p.Peek())) && p.Peek() != "`" {
						ch = p.Peek()
						if _IsQuote(ch) {
							quote = p.Advance()
							contentChars = append(contentChars, quote)
							textChars = append(textChars, quote)
							for !(p.AtEnd()) && p.Peek() != quote {
								dch = p.Advance()
								contentChars = append(contentChars, dch)
								textChars = append(textChars, dch)
								delimiterChars = append(delimiterChars, dch)
							}
							if !(p.AtEnd()) {
								closing = p.Advance()
								contentChars = append(contentChars, closing)
								textChars = append(textChars, closing)
							}
						} else if ch == "\\" {
							esc = p.Advance()
							contentChars = append(contentChars, esc)
							textChars = append(textChars, esc)
							if !(p.AtEnd()) {
								dch = p.Advance()
								contentChars = append(contentChars, dch)
								textChars = append(textChars, dch)
								delimiterChars = append(delimiterChars, dch)
							}
						} else {
							dch = p.Advance()
							contentChars = append(contentChars, dch)
							textChars = append(textChars, dch)
							delimiterChars = append(delimiterChars, dch)
						}
					}
				}
			}
			delimiter = strings.Join(delimiterChars, "")
			if len(delimiter) > 0 {
				pendingHeredocs = append(pendingHeredocs, []interface{}{delimiter, stripTabs})
			}
			continue
		}
		if c == "\n" {
			ch = p.Advance()
			contentChars = append(contentChars, string(ch))
			textChars = append(textChars, string(ch))
			if len(pendingHeredocs) > 0 {
				panic("TODO: incomplete implementation")
			}
			continue
		}
		ch = p.Advance()
		contentChars = append(contentChars, string(ch))
		textChars = append(textChars, string(ch))
	}
	if p.AtEnd() {
		panic(NewParseError("Unterminated backtick", start, 0))
	}
	p.Advance()
	textChars = append(textChars, "`")
	text = strings.Join(textChars, "")
	content = strings.Join(contentChars, "")
	if len(pendingHeredocs) > 0 {
		heredocStart, heredocEnd := _FindHeredocContentEnd(p.Source, p.Pos, pendingHeredocs)
		if heredocEnd > heredocStart {
			content = content + p.Source[heredocStart:heredocEnd]
			if p._Cmdsub_heredoc_end == -1 {
				p._Cmdsub_heredoc_end = heredocEnd
			} else {
				p._Cmdsub_heredoc_end = _max(p._Cmdsub_heredoc_end, heredocEnd)
			}
		}
	}
	subParser = NewParser(content, false, p._Extglob)
	cmd = subParser.ParseList(true)
	if cmd == nil {
		cmd = NewEmpty()
	}
	return NewCommandSubstitution(cmd, false), text
}

func (p *Parser) _ParseProcessSubstitution() (Node, string) {
	var start int
	_ = start
	var direction string
	_ = direction
	var saved *SavedParserState
	_ = saved
	var oldInProcessSub bool
	_ = oldInProcessSub
	var cmd Node
	_ = cmd
	var textEnd int
	_ = textEnd
	var text string
	_ = text
	var e interface{}
	_ = e
	var contentStartChar string
	_ = contentStartChar
	if p.AtEnd() || !(_IsRedirectChar(p.Peek())) {
		return nil, ""
	}
	start = p.Pos
	direction = p.Advance()
	if p.AtEnd() || p.Peek() != "(" {
		p.Pos = start
		return nil, ""
	}
	p.Advance()
	saved = p._SaveParserState()
	oldInProcessSub = p._In_process_sub
	p._In_process_sub = true
	p._SetState(ParserStateFlags_PST_EOFTOKEN)
	p._Eof_token = ")"
	panic("TODO: try/except")
}

func (p *Parser) _ParseArrayLiteral() (Node, string) {
	var start int
	_ = start
	var elements []Node
	_ = elements
	var word *Word
	_ = word
	var text string
	_ = text
	if p.AtEnd() || p.Peek() != "(" {
		return nil, ""
	}
	start = p.Pos
	p.Advance()
	p._SetState(ParserStateFlags_PST_COMPASSIGN)
	elements = []Node{}
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
	text = p.Source[start:p.Pos]
	p._ClearState(ParserStateFlags_PST_COMPASSIGN)
	return NewArray(elements), text
}

func (p *Parser) _ParseArithmeticExpansion() (Node, string) {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ParseArithExpr(content string) Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ArithAtEnd() bool {
	return p._Arith_pos >= p._Arith_len
}

func (p *Parser) _ArithPeek(offset int) string {
	var pos int
	_ = pos
	pos = p._Arith_pos + offset
	if pos >= p._Arith_len {
		return ""
	}
	return string(p._Arith_src[pos])
}

func (p *Parser) _ArithAdvance() string {
	var c string
	_ = c
	if p._ArithAtEnd() {
		return ""
	}
	c = string(p._Arith_src[p._Arith_pos])
	p._Arith_pos += 1
	return c
}

func (p *Parser) _ArithSkipWs() {
	var c string
	_ = c
	for !(p._ArithAtEnd()) {
		c = string(p._Arith_src[p._Arith_pos])
		if _IsWhitespace(c) {
			p._Arith_pos += 1
		} else if c == "\\" && p._Arith_pos+1 < p._Arith_len && string(p._Arith_src[p._Arith_pos+1]) == "\n" {
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
		p._Arith_pos += len(s)
		return true
	}
	return false
}

func (p *Parser) _ArithParseComma() Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ArithParseAssign() Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ArithParseTernary() Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ArithParseLeftAssoc(ops []interface{}, parsefn interface{}) Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ArithParseLogicalOr() Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ArithParseLogicalAnd() Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ArithParseBitwiseOr() Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ArithParseBitwiseXor() Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ArithParseBitwiseAnd() Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ArithParseEquality() Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ArithParseComparison() Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ArithParseShift() Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ArithParseAdditive() Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ArithParseMultiplicative() Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ArithParseExponentiation() Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ArithParseUnary() Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ArithParsePostfix() Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ArithParsePrimary() Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ArithParseExpansion() Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ArithParseCmdsub() Node {
	var depth int
	_ = depth
	var contentStart int
	_ = contentStart
	var ch string
	_ = ch
	var content string
	_ = content
	var innerExpr Node
	_ = innerExpr
	var subParser *Parser
	_ = subParser
	var cmd Node
	_ = cmd
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
		content = p._Arith_src[contentStart:p._Arith_pos]
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
	content = p._Arith_src[contentStart:p._Arith_pos]
	p._ArithAdvance()
	subParser = NewParser(content, false, p._Extglob)
	cmd = subParser.ParseList(true)
	return NewCommandSubstitution(cmd, false)
}

func (p *Parser) _ArithParseBracedParam() Node {
	var nameChars []string
	_ = nameChars
	var ch string
	_ = ch
	var name string
	_ = name
	var opChars []string
	_ = opChars
	var depth int
	_ = depth
	var opStr string
	_ = opStr
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
	name = strings.Join(nameChars, "")
	opChars = []string{}
	depth = 1
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
	opStr = strings.Join(opChars, "")
	if strings.HasPrefix(opStr, ":-") {
		return NewParamExpansion(name, ":-", opStr[2:len(opStr)])
	}
	if strings.HasPrefix(opStr, ":=") {
		return NewParamExpansion(name, ":=", opStr[2:len(opStr)])
	}
	if strings.HasPrefix(opStr, ":+") {
		return NewParamExpansion(name, ":+", opStr[2:len(opStr)])
	}
	if strings.HasPrefix(opStr, ":?") {
		return NewParamExpansion(name, ":?", opStr[2:len(opStr)])
	}
	if strings.HasPrefix(opStr, ":") {
		return NewParamExpansion(name, ":", opStr[1:len(opStr)])
	}
	if strings.HasPrefix(opStr, "##") {
		return NewParamExpansion(name, "##", opStr[2:len(opStr)])
	}
	if strings.HasPrefix(opStr, "#") {
		return NewParamExpansion(name, "#", opStr[1:len(opStr)])
	}
	if strings.HasPrefix(opStr, "%%") {
		return NewParamExpansion(name, "%%", opStr[2:len(opStr)])
	}
	if strings.HasPrefix(opStr, "%") {
		return NewParamExpansion(name, "%", opStr[1:len(opStr)])
	}
	if strings.HasPrefix(opStr, "//") {
		return NewParamExpansion(name, "//", opStr[2:len(opStr)])
	}
	if strings.HasPrefix(opStr, "/") {
		return NewParamExpansion(name, "/", opStr[1:len(opStr)])
	}
	return NewParamExpansion(name, "", opStr)
}

func (p *Parser) _ArithParseSingleQuote() Node {
	var contentStart int
	_ = contentStart
	var content string
	_ = content
	p._ArithAdvance()
	contentStart = p._Arith_pos
	for !(p._ArithAtEnd()) && p._ArithPeek(0) != "'" {
		p._ArithAdvance()
	}
	content = p._Arith_src[contentStart:p._Arith_pos]
	if !(p._ArithConsume("'")) {
		panic(NewParseError("Unterminated single quote in arithmetic", p._Arith_pos, 0))
	}
	return NewArithNumber(content)
}

func (p *Parser) _ArithParseDoubleQuote() Node {
	var contentStart int
	_ = contentStart
	var c string
	_ = c
	var content string
	_ = content
	p._ArithAdvance()
	contentStart = p._Arith_pos
	for !(p._ArithAtEnd()) && p._ArithPeek(0) != "\"" {
		c = p._ArithPeek(0)
		if c == "\\" && !(p._ArithAtEnd()) {
			p._ArithAdvance()
			p._ArithAdvance()
		} else {
			p._ArithAdvance()
		}
	}
	content = p._Arith_src[contentStart:p._Arith_pos]
	if !(p._ArithConsume("\"")) {
		panic(NewParseError("Unterminated double quote in arithmetic", p._Arith_pos, 0))
	}
	return NewArithNumber(content)
}

func (p *Parser) _ArithParseBacktick() Node {
	var contentStart int
	_ = contentStart
	var c string
	_ = c
	var content string
	_ = content
	var subParser *Parser
	_ = subParser
	var cmd Node
	_ = cmd
	p._ArithAdvance()
	contentStart = p._Arith_pos
	for !(p._ArithAtEnd()) && p._ArithPeek(0) != "`" {
		c = p._ArithPeek(0)
		if c == "\\" && !(p._ArithAtEnd()) {
			p._ArithAdvance()
			p._ArithAdvance()
		} else {
			p._ArithAdvance()
		}
	}
	content = p._Arith_src[contentStart:p._Arith_pos]
	if !(p._ArithConsume("`")) {
		panic(NewParseError("Unterminated backtick in arithmetic", p._Arith_pos, 0))
	}
	subParser = NewParser(content, false, p._Extglob)
	cmd = subParser.ParseList(true)
	return NewCommandSubstitution(cmd, false)
}

func (p *Parser) _ArithParseNumberOrVar() Node {
	var chars []string
	_ = chars
	var c string
	_ = c
	var ch string
	_ = ch
	var prefix string
	_ = prefix
	var expansion Node
	_ = expansion
	p._ArithSkipWs()
	chars = []string{}
	c = p._ArithPeek(0)
	if unicode.IsDigit(_runeFromChar(c)) {
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
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ParseParamExpansion(inDquote bool) (Node, string) {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) ParseRedirect() interface{} {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ParseHeredocDelimiter() (string, bool) {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ReadHeredocLine(quoted bool) (string, int) {
	var lineStart int
	_ = lineStart
	var lineEnd int
	_ = lineEnd
	var line string
	_ = line
	var trailingBs int
	_ = trailingBs
	var nextLineStart int
	_ = nextLineStart
	lineStart = p.Pos
	lineEnd = p.Pos
	for lineEnd < p.Length && string(p.Source[lineEnd]) != "\n" {
		lineEnd += 1
	}
	line = p.Source[lineStart:lineEnd]
	if !(quoted) {
		for lineEnd < p.Length {
			trailingBs = _CountTrailingBackslashes(line)
			if trailingBs%2 == 0 {
				break
			}
			line = line[0 : len(line)-1]
			lineEnd += 1
			nextLineStart = lineEnd
			for lineEnd < p.Length && string(p.Source[lineEnd]) != "\n" {
				lineEnd += 1
			}
			line = line + p.Source[nextLineStart:lineEnd]
		}
	}
	return line, lineEnd
}

func (p *Parser) _LineMatchesDelimiter(line string, delimiter string, stripTabs bool) (bool, string) {
	var checkLine string
	_ = checkLine
	var normalizedCheck string
	_ = normalizedCheck
	var normalizedDelim string
	_ = normalizedDelim
	checkLine = _ternary(stripTabs, strings.TrimLeft(line, "\t"), line)
	normalizedCheck = _NormalizeHeredocDelimiter(checkLine)
	normalizedDelim = _NormalizeHeredocDelimiter(delimiter)
	return normalizedCheck == normalizedDelim, checkLine
}

func (p *Parser) _GatherHeredocBodies() {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ParseHeredoc(fd int, stripTabs bool) *HereDoc {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) ParseCommand() *Command {
	var words []Node
	_ = words
	var redirects []Node
	_ = redirects
	var reserved string
	_ = reserved
	var redirect interface{}
	_ = redirect
	var allAssignments bool
	_ = allAssignments
	var inAssignBuiltin bool
	_ = inAssignBuiltin
	var word *Word
	_ = word
	words = []Node{}
	redirects = []Node{}
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
	var body Node
	_ = body
	p.SkipWhitespace()
	if p.AtEnd() || p.Peek() != "(" {
		return nil
	}
	p.Advance()
	p._SetState(ParserStateFlags_PST_SUBSHELL)
	body = p.ParseList(true)
	if body == nil {
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
	var savedPos int
	_ = savedPos
	var contentStart int
	_ = contentStart
	var depth int
	_ = depth
	var c string
	_ = c
	var content string
	_ = content
	var expr Node
	_ = expr
	p.SkipWhitespace()
	if p.AtEnd() || p.Peek() != "(" || p.Pos+1 >= p.Length || string(p.Source[p.Pos+1]) != "(" {
		return nil
	}
	savedPos = p.Pos
	p.Advance()
	p.Advance()
	contentStart = p.Pos
	depth = 1
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
			if depth == 1 && p.Pos+1 < p.Length && string(p.Source[p.Pos+1]) == ")" {
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
	content = p.Source[contentStart:p.Pos]
	content = strings.ReplaceAll(content, "\\\n", "")
	p.Advance()
	p.Advance()
	expr = p._ParseArithExpr(content)
	return NewArithmeticCommand(expr, p._CollectRedirects(), content)
}

func (p *Parser) ParseConditionalExpr() *ConditionalExpr {
	var nextPos int
	_ = nextPos
	var body Node
	_ = body
	p.SkipWhitespace()
	if p.AtEnd() || p.Peek() != "[" || p.Pos+1 >= p.Length || string(p.Source[p.Pos+1]) != "[" {
		return nil
	}
	nextPos = p.Pos + 2
	if nextPos < p.Length && !(_IsWhitespace(string(p.Source[nextPos])) || string(p.Source[nextPos]) == "\\" && nextPos+1 < p.Length && string(p.Source[nextPos+1]) == "\n") {
		return nil
	}
	p.Advance()
	p.Advance()
	p._SetState(ParserStateFlags_PST_CONDEXPR)
	p._Word_context = WordCtxCond
	body = p._ParseCondOr()
	for !(p.AtEnd()) && _IsWhitespaceNoNewline(p.Peek()) {
		p.Advance()
	}
	if p.AtEnd() || p.Peek() != "]" || p.Pos+1 >= p.Length || string(p.Source[p.Pos+1]) != "]" {
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
		} else if p.Peek() == "\\" && p.Pos+1 < p.Length && string(p.Source[p.Pos+1]) == "\n" {
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
	return p.AtEnd() || p.Peek() == "]" && p.Pos+1 < p.Length && string(p.Source[p.Pos+1]) == "]"
}

func (p *Parser) _ParseCondOr() Node {
	var left Node
	_ = left
	var right Node
	_ = right
	p._CondSkipWhitespace()
	left = p._ParseCondAnd()
	p._CondSkipWhitespace()
	if !(p._CondAtEnd()) && p.Peek() == "|" && p.Pos+1 < p.Length && string(p.Source[p.Pos+1]) == "|" {
		p.Advance()
		p.Advance()
		right = p._ParseCondOr()
		return NewCondOr(left, right)
	}
	return left
}

func (p *Parser) _ParseCondAnd() Node {
	var left Node
	_ = left
	var right Node
	_ = right
	p._CondSkipWhitespace()
	left = p._ParseCondTerm()
	p._CondSkipWhitespace()
	if !(p._CondAtEnd()) && p.Peek() == "&" && p.Pos+1 < p.Length && string(p.Source[p.Pos+1]) == "&" {
		p.Advance()
		p.Advance()
		right = p._ParseCondAnd()
		return NewCondAnd(left, right)
	}
	return left
}

func (p *Parser) _ParseCondTerm() Node {
	var operand Node
	_ = operand
	var inner Node
	_ = inner
	var word1 *Word
	_ = word1
	var op string
	_ = op
	var word2 *Word
	_ = word2
	var savedPos int
	_ = savedPos
	var opWord *Word
	_ = opWord
	p._CondSkipWhitespace()
	if p._CondAtEnd() {
		panic(NewParseError("Unexpected end of conditional expression", p.Pos, 0))
	}
	if p.Peek() == "!" {
		if p.Pos+1 < p.Length && !(_IsWhitespaceNoNewline(string(p.Source[p.Pos+1]))) {
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
	word1 = p._ParseCondWord()
	if word1 == nil {
		panic(NewParseError("Expected word in conditional expression", p.Pos, 0))
	}
	p._CondSkipWhitespace()
	if CondUnaryOps[word1.Value] {
		operand = p._ParseCondWord()
		if operand == nil {
			panic(NewParseError("Expected operand after "+word1.Value, p.Pos, 0))
		}
		return NewUnaryTest(word1.Value, operand)
	}
	if !(p._CondAtEnd()) && p.Peek() != "&" && p.Peek() != "|" && p.Peek() != ")" {
		if _IsRedirectChar(p.Peek()) && !(p.Pos+1 < p.Length && string(p.Source[p.Pos+1]) == "(") {
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
	var c string
	_ = c
	p._CondSkipWhitespace()
	if p._CondAtEnd() {
		return nil
	}
	c = p.Peek()
	if _IsParen(c) {
		return nil
	}
	if c == "&" && p.Pos+1 < p.Length && string(p.Source[p.Pos+1]) == "&" {
		return nil
	}
	if c == "|" && p.Pos+1 < p.Length && string(p.Source[p.Pos+1]) == "|" {
		return nil
	}
	return p._ParseWordInternal(WordCtxCond, false, false)
}

func (p *Parser) _ParseCondRegexWord() *Word {
	var result *Word
	_ = result
	p._CondSkipWhitespace()
	if p._CondAtEnd() {
		return nil
	}
	p._SetState(ParserStateFlags_PST_REGEXP)
	result = p._ParseWordInternal(WordCtxRegex, false, false)
	p._ClearState(ParserStateFlags_PST_REGEXP)
	p._Word_context = WordCtxCond
	return result
}

func (p *Parser) ParseBraceGroup() *BraceGroup {
	var body Node
	_ = body
	p.SkipWhitespace()
	if !(p._LexConsumeWord("{")) {
		return nil
	}
	p.SkipWhitespaceAndNewlines()
	body = p.ParseList(true)
	if body == nil {
		panic(NewParseError("Expected command in brace group", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespace()
	if !(p._LexConsumeWord("}")) {
		panic(NewParseError("Expected } to close brace group", p._LexPeekToken().Pos, 0))
	}
	return NewBraceGroup(body, p._CollectRedirects())
}

func (p *Parser) ParseIf() *If {
	var condition Node
	_ = condition
	var thenBody Node
	_ = thenBody
	var elseBody Node
	_ = elseBody
	var elifCondition Node
	_ = elifCondition
	var elifThenBody Node
	_ = elifThenBody
	var innerElse Node
	_ = innerElse
	p.SkipWhitespace()
	if !(p._LexConsumeWord("if")) {
		return nil
	}
	condition = p.ParseListUntil(map[string]struct{}{"then": {}})
	if condition == nil {
		panic(NewParseError("Expected condition after 'if'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("then")) {
		panic(NewParseError("Expected 'then' after if condition", p._LexPeekToken().Pos, 0))
	}
	thenBody = p.ParseListUntil(map[string]struct{}{"elif": {}, "else": {}, "fi": {}})
	if thenBody == nil {
		panic(NewParseError("Expected commands after 'then'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	elseBody = nil
	if p._LexIsAtReservedWord("elif") {
		p._LexConsumeWord("elif")
		elifCondition = p.ParseListUntil(map[string]struct{}{"then": {}})
		if elifCondition == nil {
			panic(NewParseError("Expected condition after 'elif'", p._LexPeekToken().Pos, 0))
		}
		p.SkipWhitespaceAndNewlines()
		if !(p._LexConsumeWord("then")) {
			panic(NewParseError("Expected 'then' after elif condition", p._LexPeekToken().Pos, 0))
		}
		elifThenBody = p.ParseListUntil(map[string]struct{}{"elif": {}, "else": {}, "fi": {}})
		if elifThenBody == nil {
			panic(NewParseError("Expected commands after 'then'", p._LexPeekToken().Pos, 0))
		}
		p.SkipWhitespaceAndNewlines()
		innerElse = nil
		if p._LexIsAtReservedWord("elif") {
			innerElse = p._ParseElifChain()
		} else if p._LexIsAtReservedWord("else") {
			p._LexConsumeWord("else")
			innerElse = p.ParseListUntil(map[string]struct{}{"fi": {}})
			if innerElse == nil {
				panic(NewParseError("Expected commands after 'else'", p._LexPeekToken().Pos, 0))
			}
		}
		elseBody = NewIf(elifCondition, elifThenBody, innerElse, nil)
	} else if p._LexIsAtReservedWord("else") {
		p._LexConsumeWord("else")
		elseBody = p.ParseListUntil(map[string]struct{}{"fi": {}})
		if elseBody == nil {
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
	var condition Node
	_ = condition
	var thenBody Node
	_ = thenBody
	var elseBody Node
	_ = elseBody
	p._LexConsumeWord("elif")
	condition = p.ParseListUntil(map[string]struct{}{"then": {}})
	if condition == nil {
		panic(NewParseError("Expected condition after 'elif'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("then")) {
		panic(NewParseError("Expected 'then' after elif condition", p._LexPeekToken().Pos, 0))
	}
	thenBody = p.ParseListUntil(map[string]struct{}{"elif": {}, "else": {}, "fi": {}})
	if thenBody == nil {
		panic(NewParseError("Expected commands after 'then'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	elseBody = nil
	if p._LexIsAtReservedWord("elif") {
		elseBody = p._ParseElifChain()
	} else if p._LexIsAtReservedWord("else") {
		p._LexConsumeWord("else")
		elseBody = p.ParseListUntil(map[string]struct{}{"fi": {}})
		if elseBody == nil {
			panic(NewParseError("Expected commands after 'else'", p._LexPeekToken().Pos, 0))
		}
	}
	return NewIf(condition, thenBody, elseBody, nil)
}

func (p *Parser) ParseWhile() *While {
	var condition Node
	_ = condition
	var body Node
	_ = body
	p.SkipWhitespace()
	if !(p._LexConsumeWord("while")) {
		return nil
	}
	condition = p.ParseListUntil(map[string]struct{}{"do": {}})
	if condition == nil {
		panic(NewParseError("Expected condition after 'while'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("do")) {
		panic(NewParseError("Expected 'do' after while condition", p._LexPeekToken().Pos, 0))
	}
	body = p.ParseListUntil(map[string]struct{}{"done": {}})
	if body == nil {
		panic(NewParseError("Expected commands after 'do'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("done")) {
		panic(NewParseError("Expected 'done' to close while loop", p._LexPeekToken().Pos, 0))
	}
	return NewWhile(condition, body, p._CollectRedirects())
}

func (p *Parser) ParseUntil() *Until {
	var condition Node
	_ = condition
	var body Node
	_ = body
	p.SkipWhitespace()
	if !(p._LexConsumeWord("until")) {
		return nil
	}
	condition = p.ParseListUntil(map[string]struct{}{"do": {}})
	if condition == nil {
		panic(NewParseError("Expected condition after 'until'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("do")) {
		panic(NewParseError("Expected 'do' after until condition", p._LexPeekToken().Pos, 0))
	}
	body = p.ParseListUntil(map[string]struct{}{"done": {}})
	if body == nil {
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
	_ = varWord
	var varName string
	_ = varName
	var words []Node
	_ = words
	var sawDelimiter bool
	_ = sawDelimiter
	var word *Word
	_ = word
	var braceGroup *BraceGroup
	_ = braceGroup
	var body Node
	_ = body
	p.SkipWhitespace()
	if !(p._LexConsumeWord("for")) {
		return nil
	}
	p.SkipWhitespace()
	if p.Peek() == "(" && p.Pos+1 < p.Length && string(p.Source[p.Pos+1]) == "(" {
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
	body = p.ParseListUntil(map[string]struct{}{"done": {}})
	if body == nil {
		panic(NewParseError("Expected commands after 'do'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("done")) {
		panic(NewParseError("Expected 'done' to close for loop", p._LexPeekToken().Pos, 0))
	}
	return NewFor(varName, words, body, p._CollectRedirects())
}

func (p *Parser) _ParseForArith() *ForArith {
	var parts []string
	_ = parts
	var current []string
	_ = current
	var parenDepth int
	_ = parenDepth
	var ch string
	_ = ch
	var init string
	_ = init
	var cond string
	_ = cond
	var incr string
	_ = incr
	var body Node
	_ = body
	p.Advance()
	p.Advance()
	parts = []string{}
	current = []string{}
	parenDepth = 0
	for !(p.AtEnd()) {
		ch = p.Peek()
		if ch == "(" {
			parenDepth += 1
			current = append(current, p.Advance())
		} else if ch == ")" {
			if parenDepth > 0 {
				parenDepth -= 1
				current = append(current, p.Advance())
			} else if p.Pos+1 < p.Length && string(p.Source[p.Pos+1]) == ")" {
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
	init = parts[0]
	cond = parts[1]
	incr = parts[2]
	p.SkipWhitespace()
	if !(p.AtEnd()) && p.Peek() == ";" {
		p.Advance()
	}
	p.SkipWhitespaceAndNewlines()
	body = p._ParseLoopBody("for loop")
	return NewForArith(init, cond, incr, body, p._CollectRedirects())
}

func (p *Parser) ParseSelect() *Select {
	var varName string
	_ = varName
	var words []Node
	_ = words
	var word *Word
	_ = word
	var body Node
	_ = body
	p.SkipWhitespace()
	if !(p._LexConsumeWord("select")) {
		return nil
	}
	p.SkipWhitespace()
	varName = p.PeekWord()
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
	body = p._ParseLoopBody("select")
	return NewSelect(varName, words, body, p._CollectRedirects())
}

func (p *Parser) _ConsumeCaseTerminator() string {
	var term string
	_ = term
	term = p._LexPeekCaseTerminator()
	if term != "" {
		p._LexNextToken()
		return term
	}
	return ";;"
}

func (p *Parser) ParseCase() *Case {
	var word *Word
	_ = word
	var patterns []Node
	_ = patterns
	var saved int
	_ = saved
	var isPattern bool
	_ = isPattern
	var nextCh string
	_ = nextCh
	var patternChars []string
	_ = patternChars
	var extglobDepth int
	_ = extglobDepth
	var ch string
	_ = ch
	var parenDepth int
	_ = parenDepth
	var c string
	_ = c
	var isCharClass bool
	_ = isCharClass
	var scanPos int
	_ = scanPos
	var scanDepth int
	_ = scanDepth
	var hasFirstBracketLiteral bool
	_ = hasFirstBracketLiteral
	var sc string
	_ = sc
	var pattern string
	_ = pattern
	var body Node
	_ = body
	var isEmptyBody bool
	_ = isEmptyBody
	var isAtTerminator bool
	_ = isAtTerminator
	var terminator string
	_ = terminator
	if !(p.ConsumeWord("case")) {
		return nil
	}
	p._SetState(ParserStateFlags_PST_CASESTMT)
	p.SkipWhitespace()
	word = p.ParseWord(false, false, false)
	if word == nil {
		panic(NewParseError("Expected word after 'case'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("in")) {
		panic(NewParseError("Expected 'in' after case word", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	patterns = []Node{}
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
				if p.Pos+1 < p.Length && string(p.Source[p.Pos+1]) == "\n" {
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
			} else if p._Extglob && _IsExtglobPrefix(ch) && p.Pos+1 < p.Length && string(p.Source[p.Pos+1]) == "(" {
				patternChars = append(patternChars, p.Advance())
				patternChars = append(patternChars, p.Advance())
				extglobDepth += 1
			} else if ch == "[" {
				isCharClass = false
				scanPos = p.Pos + 1
				scanDepth = 0
				hasFirstBracketLiteral = false
				if scanPos < p.Length && _IsCaretOrBang(string(p.Source[scanPos])) {
					scanPos += 1
				}
				if scanPos < p.Length && string(p.Source[scanPos]) == "]" {
					if strings.Index(p.Source, "]") != -1 {
						scanPos += 1
						hasFirstBracketLiteral = true
					}
				}
				for scanPos < p.Length {
					sc = string(p.Source[scanPos])
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
	_ = name
	var ch string
	_ = ch
	var body Node
	_ = body
	var nextWord string
	_ = nextWord
	var wordStart int
	_ = wordStart
	var potentialName string
	_ = potentialName
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
		if body != nil {
			return NewCoproc(body, name)
		}
	}
	if ch == "(" {
		if p.Pos+1 < p.Length && string(p.Source[p.Pos+1]) == "(" {
			body = p.ParseArithmeticCommand()
			if body != nil {
				return NewCoproc(body, name)
			}
		}
		body = p.ParseSubshell()
		if body != nil {
			return NewCoproc(body, name)
		}
	}
	nextWord = p._LexPeekReservedWord()
	if nextWord != "" && CompoundKeywords[nextWord] {
		body = p.ParseCompoundCommand()
		if body != nil {
			return NewCoproc(body, name)
		}
	}
	wordStart = p.Pos
	potentialName = p.PeekWord()
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
				if body != nil {
					return NewCoproc(body, name)
				}
			} else if ch == "(" {
				name = potentialName
				if p.Pos+1 < p.Length && string(p.Source[p.Pos+1]) == "(" {
					body = p.ParseArithmeticCommand()
				} else {
					body = p.ParseSubshell()
				}
				if body != nil {
					return NewCoproc(body, name)
				}
			} else if nextWord != "" && CompoundKeywords[nextWord] {
				name = potentialName
				body = p.ParseCompoundCommand()
				if body != nil {
					return NewCoproc(body, name)
				}
			}
		}
		p.Pos = wordStart
	}
	body = p.ParseCommand()
	if body != nil {
		return NewCoproc(body, name)
	}
	panic(NewParseError("Expected command after coproc", p.Pos, 0))
}

func (p *Parser) ParseFunction() *Function {
	var savedPos int
	_ = savedPos
	var name string
	_ = name
	var body Node
	_ = body
	var nameStart int
	_ = nameStart
	var braceDepth int
	_ = braceDepth
	var i int
	_ = i
	var posAfterName int
	_ = posAfterName
	var hasWhitespace bool
	_ = hasWhitespace
	p.SkipWhitespace()
	if p.AtEnd() {
		return nil
	}
	savedPos = p.Pos
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
			if p.Pos+1 < p.Length && string(p.Source[p.Pos+1]) == ")" {
				p.Advance()
				p.Advance()
			}
		}
		p.SkipWhitespaceAndNewlines()
		body = p._ParseCompoundCommand()
		if body == nil {
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
	nameStart = p.Pos
	for !(p.AtEnd()) && !(_IsMetachar(p.Peek())) && !(_IsQuote(p.Peek())) && !(_IsParen(p.Peek())) {
		p.Advance()
	}
	name = p.Source[nameStart:p.Pos]
	if !(len(name) > 0) {
		p.Pos = savedPos
		return nil
	}
	braceDepth = 0
	i = 0
	for i < len(name) {
		if _IsExpansionStart(name, i, "${") {
			braceDepth += 1
			i += 2
			continue
		}
		if string(name[i]) == "}" {
			braceDepth -= 1
		}
		i += 1
	}
	if braceDepth > 0 {
		p.Pos = savedPos
		return nil
	}
	posAfterName = p.Pos
	p.SkipWhitespace()
	hasWhitespace = p.Pos > posAfterName
	if !(hasWhitespace) && len(name) > 0 && strings.Contains("*?@+!$", string(name[len(name)-1])) {
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
	if body == nil {
		panic(NewParseError("Expected function body", p.Pos, 0))
	}
	return NewFunction(name, body)
}

func (p *Parser) _ParseCompoundCommand() Node {
	var result Node
	_ = result
	result = p.ParseBraceGroup()
	if result != nil {
		return result
	}
	if !(p.AtEnd()) && p.Peek() == "(" && p.Pos+1 < p.Length && string(p.Source[p.Pos+1]) == "(" {
		result = p.ParseArithmeticCommand()
		if result != nil {
			return result
		}
	}
	result = p.ParseSubshell()
	if result != nil {
		return result
	}
	result = p.ParseConditionalExpr()
	if result != nil {
		return result
	}
	result = p.ParseIf()
	if result != nil {
		return result
	}
	result = p.ParseWhile()
	if result != nil {
		return result
	}
	result = p.ParseUntil()
	if result != nil {
		return result
	}
	result = p.ParseFor()
	if result != nil {
		return result
	}
	result = p.ParseCase()
	if result != nil {
		return result
	}
	result = p.ParseSelect()
	if result != nil {
		return result
	}
	return nil
}

func (p *Parser) _AtListUntilTerminator(stopWords map[string]struct{}) bool {
	var nextPos int
	_ = nextPos
	var reserved string
	_ = reserved
	if p.AtEnd() {
		return true
	}
	if p.Peek() == ")" {
		return true
	}
	if p.Peek() == "}" {
		nextPos = p.Pos + 1
		if nextPos >= p.Length || _IsWordEndContext(string(p.Source[nextPos])) {
			return true
		}
	}
	reserved = p._LexPeekReservedWord()
	if reserved != "" && func() bool { _, ok := stopWords[reserved]; return ok }() {
		return true
	}
	if p._LexPeekCaseTerminator() != "" {
		return true
	}
	return false
}

func (p *Parser) ParseListUntil(stopWords map[string]struct{}) Node {
	var reserved string
	_ = reserved
	var pipeline Node
	_ = pipeline
	var parts []Node
	_ = parts
	var op string
	_ = op
	var nextOp string
	_ = nextOp
	p.SkipWhitespaceAndNewlines()
	reserved = p._LexPeekReservedWord()
	if reserved != "" && func() bool { _, ok := stopWords[reserved]; return ok }() {
		return nil
	}
	pipeline = p.ParsePipeline()
	if pipeline == nil {
		return nil
	}
	parts = []Node{pipeline}
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
		if pipeline == nil {
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
	panic("TODO: method needs manual implementation")
}

func (p *Parser) ParsePipeline() Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _ParseSimplePipeline() Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) ParseListOperator() string {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _PeekListOperator() string {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) ParseList(newlineAsSeparator bool) Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) ParseComment() Node {
	var start int
	_ = start
	var text string
	_ = text
	if p.AtEnd() || p.Peek() != "#" {
		return nil
	}
	start = p.Pos
	for !(p.AtEnd()) && p.Peek() != "\n" {
		p.Advance()
	}
	text = p.Source[start:p.Pos]
	return NewComment(text)
}

func (p *Parser) Parse() []Node {
	panic("TODO: method needs manual implementation")
}

func (p *Parser) _LastWordOnOwnLine(nodes []Node) bool {
	return len(nodes) >= 2
}

func (p *Parser) _StripTrailingBackslashFromLastWord(nodes []Node) {
	var lastNode Node
	_ = lastNode
	var lastWord *Word
	_ = lastWord
	if !(len(nodes) > 0) {
		return
	}
	lastNode = nodes[len(nodes)-1]
	lastWord = p._FindLastWord(lastNode)
	if lastWord != nil && strings.HasSuffix(lastWord.Value, "\\") {
		lastWord.Value = lastWord.Value[0 : len(lastWord.Value)-1]
		panic("TODO: incomplete implementation")
	}
}

func (p *Parser) _FindLastWord(node Node) *Word {
	var lastWord interface{}
	_ = lastWord
	var lastRedirect interface{}
	_ = lastRedirect
	panic("TODO: isinstance")
	panic("TODO: isinstance")
	panic("TODO: isinstance")
	panic("TODO: isinstance")
	return nil
}
