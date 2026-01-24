package parable

import (
	"fmt"
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
	Pending_heredocs []interface{}
	Ctx_stack        []interface{}
	Eof_token        string
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
	_Word_context             interface{}
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
	Redirects []interface{}
	kind      string
}

func (s *Subshell) Kind() string {
	return s.kind
}

type BraceGroup struct {
	Body      Node
	Redirects []interface{}
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
	Words     []interface{}
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
	Words     []interface{}
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
	Redirects   []interface{}
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
	Redirects []interface{}
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
	_Word_context                interface{}
	_At_command_start            bool
	_In_array_literal            bool
	_In_assign_builtin           bool
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
	count := 0
	k := pos - 1
	for k >= 0 && s[k] == '$' {
		bsCount := 0
		j := k - 1
		for j >= 0 && s[j] == '\\' {
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
	result := []string{}
	i := 0
	for i < n {
		result = append(result, s)
		i += 1
	}
	return strings.Join(result, "")
}

func _StripLineContinuationsCommentAware(text string) string {
	result := []string{}
	i := 0
	inComment := false
	quote := NewQuoteState()
	for i < len(text) {
		c := text[i]
		if c == '\\' && i+1 < len(text) && text[i+1] == '\n' {
			numPrecedingBackslashes := 0
			j := i - 1
			for j >= 0 && text[j] == '\\' {
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
		if c == '\n' {
			inComment = false
			result = append(result, string(c))
			i += 1
			continue
		}
		if c == '\'' && !(quote.Double) && !(inComment) {
			quote.Single = !(quote.Single)
		} else if c == '"' && !(quote.Single) && !(inComment) {
			quote.Double = !(quote.Double)
		} else if c == '#' && !(quote.Single) && !(inComment) {
			inComment = true
		}
		result = append(result, string(c))
		i += 1
	}
	return strings.Join(result, "")
}

func _AppendRedirects(base string, redirects []interface{}) string {
	if len(redirects) > 0 {
		parts := []string{}
		for _, r := range redirects {
			parts = append(parts, r.(Node).ToSexp())
		}
		return base + " " + strings.Join(parts, " ")
	}
	return base
}

func _ConsumeSingleQuote(s string, start int) interface{} {
	chars := []string{"'"}
	i := start + 1
	for i < len(s) && s[i] != '\'' {
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
	chars := []string{"\""}
	i := start + 1
	for i < len(s) && s[i] != '"' {
		if s[i] == '\\' && i+1 < len(s) {
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
	i := start
	for i < len(s) {
		if s[i] == ']' {
			return true
		}
		if s[i] == '|' || s[i] == ')' && depth == 0 {
			return false
		}
		i += 1
	}
	return false
}

func _ConsumeBracketClass(s string, start int, depth int) interface{} {
	scanPos := start + 1
	if scanPos < len(s) && s[scanPos] == '!' || s[scanPos] == '^' {
		scanPos += 1
	}
	if scanPos < len(s) && s[scanPos] == ']' {
		if _HasBracketClose(s, scanPos+1, depth) {
			scanPos += 1
		}
	}
	isBracket := false
	for scanPos < len(s) {
		if s[scanPos] == ']' {
			isBracket = true
			break
		}
		if s[scanPos] == ')' && depth == 0 {
			break
		}
		if s[scanPos] == '|' && depth == 0 {
			break
		}
		scanPos += 1
	}
	if !(isBracket) {
		return []interface{}{start + 1, []string{"["}, false}
	}
	chars := []string{"["}
	i := start + 1
	if i < len(s) && s[i] == '!' || s[i] == '^' {
		chars = append(chars, string(s[i]))
		i += 1
	}
	if i < len(s) && s[i] == ']' {
		if _HasBracketClose(s, i+1, depth) {
			chars = append(chars, string(s[i]))
			i += 1
		}
	}
	for i < len(s) && s[i] != ']' {
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

func _FormatRedirect(r interface{}, compact bool, heredocOpOnly bool) string {
	panic("TODO: function needs manual transpilation")
}

func _FormatHeredocBody(r Node) string {
	panic("TODO: function needs manual transpilation")
}

func _LookaheadForEsac(value string, start int, caseDepth int) bool {
	i := start
	depth := caseDepth
	quote := NewQuoteState()
	for i < len(value) {
		c := value[i]
		if c == '\\' && i+1 < len(value) && quote.Double {
			i += 2
			continue
		}
		if c == '\'' && !(quote.Double) {
			quote.Single = !(quote.Single)
			i += 1
			continue
		}
		if c == '"' && !(quote.Single) {
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
		} else if c == '(' {
			i += 1
		} else if c == ')' {
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
	for i < len(value) && value[i] != '`' {
		if value[i] == '\\' && i+1 < len(value) {
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
	scanParen := 0
	scanI := start + 3
	for scanI < len(value) {
		scanC := value[scanI]
		if _IsExpansionStart(value, scanI, "$(") {
			scanI = _FindCmdsubEnd(value, scanI+2)
			continue
		}
		if scanC == '(' {
			scanParen += 1
		} else if scanC == ')' {
			if scanParen > 0 {
				scanParen -= 1
			} else if scanI+1 < len(value) && value[scanI+1] == ')' {
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
	depth := 1
	i := start
	quote := NewQuoteState()
	for i < len(value) && depth > 0 {
		c := value[i]
		if c == '\\' && i+1 < len(value) && !(quote.Single) {
			i += 2
			continue
		}
		if c == '\'' && !(quote.Double) {
			quote.Single = !(quote.Single)
			i += 1
			continue
		}
		if c == '"' && !(quote.Single) {
			quote.Double = !(quote.Double)
			i += 1
			continue
		}
		if quote.Single || quote.Double {
			i += 1
			continue
		}
		if c == '{' {
			depth += 1
		} else if c == '}' {
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
	depth := 1
	i := start
	caseDepth := 0
	inCasePatterns := false
	arithDepth := 0
	arithParenDepth := 0
	for i < len(value) && depth > 0 {
		c := value[i]
		if c == '\\' && i+1 < len(value) {
			i += 2
			continue
		}
		if c == '\'' {
			i = _SkipSingleQuoted(value, i+1)
			continue
		}
		if c == '"' {
			i = _SkipDoubleQuoted(value, i+1)
			continue
		}
		if c == '#' && arithDepth == 0 && i == start || value[i-1] == ' ' || value[i-1] == '\t' || value[i-1] == '\n' || value[i-1] == ';' || value[i-1] == '|' || value[i-1] == '&' || value[i-1] == '(' || value[i-1] == ')' {
			for i < len(value) && value[i] != '\n' {
				i += 1
			}
			continue
		}
		if strings.HasPrefix(value[i:], "<<<") {
			i += 3
			for i < len(value) && value[i] == ' ' || value[i] == '\t' {
				i += 1
			}
			if i < len(value) && value[i] == '"' {
				i += 1
				for i < len(value) && value[i] != '"' {
					if value[i] == '\\' && i+1 < len(value) {
						i += 2
					} else {
						i += 1
					}
				}
				if i < len(value) {
					i += 1
				}
			} else if i < len(value) && value[i] == '\'' {
				i += 1
				for i < len(value) && value[i] != '\'' {
					i += 1
				}
				if i < len(value) {
					i += 1
				}
			} else {
				for i < len(value) && !strings.ContainsRune(" \t\n;|&<>()", rune(value[i])) {
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
			j := _FindCmdsubEnd(value, i+2)
			i = j
			continue
		}
		if arithDepth > 0 && arithParenDepth == 0 && strings.HasPrefix(value[i:], "))") {
			arithDepth -= 1
			i += 2
			continue
		}
		if c == '`' {
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
		if c == '(' {
			if !(inCasePatterns && caseDepth > 0) {
				if arithDepth > 0 {
					arithParenDepth += 1
				} else {
					depth += 1
				}
			}
		} else if c == ')' {
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
	depth := 1
	i := start
	inDouble := false
	dolbraceState := DolbraceState_PARAM
	for i < len(value) && depth > 0 {
		c := value[i]
		if c == '\\' && i+1 < len(value) {
			i += 2
			continue
		}
		if c == '\'' && dolbraceState == DolbraceState_QUOTE && !(inDouble) {
			i = _SkipSingleQuoted(value, i+1)
			continue
		}
		if c == '"' {
			inDouble = !(inDouble)
			i += 1
			continue
		}
		if inDouble {
			i += 1
			continue
		}
		if dolbraceState == DolbraceState_PARAM && strings.ContainsRune("%#^,", rune(c)) {
			dolbraceState = DolbraceState_QUOTE
		} else if dolbraceState == DolbraceState_PARAM && strings.ContainsRune(":-=?+/", rune(c)) {
			dolbraceState = DolbraceState_WORD
		}
		if c == '[' && dolbraceState == DolbraceState_PARAM && !(inDouble) {
			end := _SkipSubscript(value, i, 0)
			if end != -1 {
				i = end
				continue
			}
		}
		if c == '<' || c == '>' && i+1 < len(value) && value[i+1] == '(' {
			i = _FindCmdsubEnd(value, i+2)
			continue
		}
		if c == '{' {
			depth += 1
		} else if c == '}' {
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
	if pos > 0 {
		prev := s[pos-1]
		if (unicode.IsLetter(_runeFromChar(prev)) || unicode.IsDigit(_runeFromChar(prev))) || prev == '_' {
			return false
		}
		if strings.ContainsRune("{}!", rune(prev)) {
			return false
		}
	}
	end := pos + wordLen
	if end < len(s) && (unicode.IsLetter(_runeFromChar(s[end])) || unicode.IsDigit(_runeFromChar(s[end]))) || s[end] == '_' {
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
	count := 0
	for i := len(s) - 1; i > -1; i += -1 {
		if s[i] == '\\' {
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
	if !(len(s) > 0) {
		return -1
	}
	if !(unicode.IsLetter(_runeFromChar(s[0])) || s[0] == '_') {
		return -1
	}
	i := 1
	for i < len(s) {
		c := s[i]
		if c == '=' {
			return i
		}
		if c == '[' {
			subFlags := _ternary((flags&2) != 0, SmpLiteral, 0)
			end := _SkipSubscript(s, i, subFlags)
			if end == -1 {
				return -1
			}
			i = end
			if i < len(s) && s[i] == '+' {
				i += 1
			}
			if i < len(s) && s[i] == '=' {
				return i
			}
			return -1
		}
		if c == '+' {
			if i+1 < len(s) && s[i+1] == '=' {
				return i + 1
			}
			return -1
		}
		if !((unicode.IsLetter(_runeFromChar(c)) || unicode.IsDigit(_runeFromChar(c))) || c == '_') {
			return -1
		}
		i += 1
	}
	return -1
}

func _IsArrayAssignmentPrefix(chars []string) bool {
	if !(len(chars) > 0) {
		return false
	}
	if !(unicode.IsLetter(_runeFromChar(chars[0])) || chars[0] == "_") {
		return false
	}
	s := strings.Join(chars, "")
	i := 1
	for i < len(s) && (unicode.IsLetter(_runeFromChar(s[i])) || unicode.IsDigit(_runeFromChar(s[i]))) || s[i] == '_' {
		i += 1
	}
	for i < len(s) {
		if s[i] != '[' {
			return false
		}
		end := _SkipSubscript(s, i, SmpLiteral)
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
	for j >= 0 && value[j] == '\\' {
		bsCount += 1
		j -= 1
	}
	return bsCount%2 == 1
}

func _IsDollarDollarParen(value string, idx int) bool {
	dollarCount := 0
	j := idx - 1
	for j >= 0 && value[j] == '$' {
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
	if !(unicode.IsLetter(_runeFromChar(name[0])) || name[0] == '_') {
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
	parser := NewParser(source, false, extglob)
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

func NewSavedParserState(parserState int, dolbraceState int, pendingHeredocs []interface{}, ctxStack []interface{}, eofToken string) *SavedParserState {
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

func (c *ContextStack) CopyStack() []interface{} {
	result := []interface{}{}
	for _, ctx := range c._Stack {
		result = append(result, ctx.Copy())
	}
	return result
}

func (c *ContextStack) RestoreFrom(savedStack []*ParseContext) {
	result := []interface{}{}
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
	return string(l.Source[l.Pos])
}

func (l *Lexer) Advance() string {
	if l.Pos >= l.Length {
		return ""
	}
	c := l.Source[l.Pos]
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
		if l.Pos+1 < l.Length && l.Source[l.Pos+1] == '(' {
			return nil
		}
		l.Pos += 1
		return NewToken(TokenType_LESS, c, start, nil, nil)
	}
	if c == ">" {
		if l.Pos+1 < l.Length && l.Source[l.Pos+1] == '(' {
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
	for l.Pos < l.Length {
		c := l.Source[l.Pos]
		if c != ' ' && c != '\t' {
			break
		}
		l.Pos += 1
	}
}

func (l *Lexer) _SkipComment() bool {
	if l.Pos >= l.Length {
		return false
	}
	if l.Source[l.Pos] != '#' {
		return false
	}
	if l.Quote.InQuotes() {
		return false
	}
	if l.Pos > 0 {
		prev := l.Source[l.Pos-1]
		if !strings.ContainsRune(" \t\n;|&(){}", rune(prev)) {
			return false
		}
	}
	for l.Pos < l.Length && l.Source[l.Pos] != '\n' {
		l.Pos += 1
	}
	return true
}

func (l *Lexer) _ReadSingleQuote(start int) (string, bool) {
	chars := []string{"'"}
	sawNewline := false
	for l.Pos < l.Length {
		c := l.Source[l.Pos]
		if c == '\n' {
			sawNewline = true
		}
		chars = append(chars, string(c))
		l.Pos += 1
		if c == '\'' {
			return strings.Join(chars, ""), sawNewline
		}
	}
	panic(NewParseError("Unterminated single quote", start, 0))
}

func (l *Lexer) _IsWordTerminator(ctx int, ch string, bracketDepth int, parenDepth int) bool {
	if ctx == WordCtxRegex {
		if ch == "]" && l.Pos+1 < l.Length && l.Source[l.Pos+1] == ']' {
			return true
		}
		if ch == "&" && l.Pos+1 < l.Length && l.Source[l.Pos+1] == '&' {
			return true
		}
		if ch == ")" && parenDepth == 0 {
			return true
		}
		return _IsWhitespace(ch) && parenDepth == 0
	}
	if ctx == WordCtxCond {
		if ch == "]" && l.Pos+1 < l.Length && l.Source[l.Pos+1] == ']' {
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
		if _IsRedirectChar(ch) && !(l.Pos+1 < l.Length && l.Source[l.Pos+1] == '(') {
			return true
		}
		return _IsWhitespace(ch)
	}
	if (l._Parser_state&ParserStateFlags_PST_EOFTOKEN) != 0 && l._Eof_token != "" && ch == l._Eof_token && bracketDepth == 0 {
		return true
	}
	if _IsRedirectChar(ch) && l.Pos+1 < l.Length && l.Source[l.Pos+1] == '(' {
		return false
	}
	return _IsMetachar(ch) && bracketDepth == 0
}

func (l *Lexer) _ReadBracketExpression(chars []string, parts []Node, forRegex bool, parenDepth int) bool {
	var scan int
	var bracketWillClose bool
	var sc byte
	var nextCh byte
	if forRegex {
		scan = l.Pos + 1
		if scan < l.Length && l.Source[scan] == '^' {
			scan += 1
		}
		if scan < l.Length && l.Source[scan] == ']' {
			scan += 1
		}
		bracketWillClose = false
		for scan < l.Length {
			sc = l.Source[scan]
			if sc == ']' && scan+1 < l.Length && l.Source[scan+1] == ']' {
				break
			}
			if sc == ')' && parenDepth > 0 {
				break
			}
			if sc == '&' && scan+1 < l.Length && l.Source[scan+1] == '&' {
				break
			}
			if sc == ']' {
				bracketWillClose = true
				break
			}
			if sc == '[' && scan+1 < l.Length && l.Source[scan+1] == ':' {
				scan += 2
				for scan < l.Length && !(l.Source[scan] == ':' && scan+1 < l.Length && l.Source[scan+1] == ']') {
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
		nextCh = l.Source[l.Pos+1]
		if _IsWhitespaceNoNewline(string(nextCh)) || nextCh == '&' || nextCh == '|' {
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
		c := l.Peek()
		if c == "]" {
			chars = append(chars, l.Advance())
			break
		}
		if c == "[" && l.Pos+1 < l.Length && l.Source[l.Pos+1] == ':' {
			chars = append(chars, l.Advance())
			chars = append(chars, l.Advance())
			for !(l.AtEnd()) && !(l.Peek() == ":" && l.Pos+1 < l.Length && l.Source[l.Pos+1] == ']') {
				chars = append(chars, l.Advance())
			}
			if !(l.AtEnd()) {
				chars = append(chars, l.Advance())
				chars = append(chars, l.Advance())
			}
		} else if !(forRegex) && c == "[" && l.Pos+1 < l.Length && l.Source[l.Pos+1] == '=' {
			chars = append(chars, l.Advance())
			chars = append(chars, l.Advance())
			for !(l.AtEnd()) && !(l.Peek() == "=" && l.Pos+1 < l.Length && l.Source[l.Pos+1] == ']') {
				chars = append(chars, l.Advance())
			}
			if !(l.AtEnd()) {
				chars = append(chars, l.Advance())
				chars = append(chars, l.Advance())
			}
		} else if !(forRegex) && c == "[" && l.Pos+1 < l.Length && l.Source[l.Pos+1] == '.' {
			chars = append(chars, l.Advance())
			chars = append(chars, l.Advance())
			for !(l.AtEnd()) && !(l.Peek() == "." && l.Pos+1 < l.Length && l.Source[l.Pos+1] == ']') {
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

func (l *Lexer) _ParseMatchedPair(openChar string, closeChar string, flags int) string {
	start := l.Pos
	count := 1
	chars := []string{}
	passNext := false
	wasDollar := false
	wasGtlt := false
	for count > 0 {
		if l.AtEnd() {
			panic(NewMatchedPairError(fmt.Sprintf("unexpected EOF while looking for matching `%v'", closeChar), start, 0))
		}
		ch := l.Advance()
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
			var quoteFlags int
			var nested string
			if ch == "'" {
				chars = append(chars, ch)
				quoteFlags = _ternary(wasDollar, flags|MatchedPairFlags_ALLOWESC, flags)
				nested := l._ParseMatchedPair("'", "'", quoteFlags)
				chars = append(chars, nested)
				chars = append(chars, "'")
				wasDollar = false
				wasGtlt = false
				continue
			} else if ch == "\"" {
				chars = append(chars, ch)
				nested := l._ParseMatchedPair("\"", "\"", flags|MatchedPairFlags_DQUOTE)
				chars = append(chars, nested)
				chars = append(chars, "\"")
				wasDollar = false
				wasGtlt = false
				continue
			} else if ch == "`" {
				chars = append(chars, ch)
				nested := l._ParseMatchedPair("`", "`", flags)
				chars = append(chars, nested)
				chars = append(chars, "`")
				wasDollar = false
				wasGtlt = false
				continue
			}
		}
		if ch == "$" && !(l.AtEnd()) && !((flags & MatchedPairFlags_EXTGLOB) != 0) {
			nextCh := l.Peek()
			if wasDollar {
				chars = append(chars, ch)
				wasDollar = false
				wasGtlt = false
				continue
			}
			var afterBracePos int
			var inDquote bool
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
				if l.Pos+2 < l.Length && l.Source[l.Pos+2] == '(' {
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

func (l *Lexer) _CollectParamArgument(flags int) string {
	return l._ParseMatchedPair("{", "}", flags|MatchedPairFlags_DOLBRACE)
}

func (l *Lexer) _ReadWordInternal(ctx int, atCommandStart bool, inArrayLiteral bool, inAssignBuiltin bool) Node {
	start := l.Pos
	chars := []string{}
	parts := []Node{}
	bracketDepth := 0
	bracketStartPos := -1
	seenEquals := false
	parenDepth := 0
	for !(l.AtEnd()) {
		ch := l.Peek()
		if ctx == WordCtxRegex {
			if ch == "\\" && l.Pos+1 < l.Length && l.Source[l.Pos+1] == '\n' {
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
				prevChar := chars[len(chars)-1]
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
			forRegex := ctx == WordCtxRegex
			if l._ReadBracketExpression(chars, parts, forRegex, parenDepth) {
				continue
			}
			chars = append(chars, l.Advance())
			continue
		}
		if ctx == WordCtxCond && ch == "(" {
			var content string
			if l._Extglob && len(chars) > 0 && _IsExtglobPrefix(chars[len(chars)-1]) {
				chars = append(chars, l.Advance())
				content := l._ParseMatchedPair("(", ")", MatchedPairFlags_EXTGLOB)
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
			trackNewline := ctx == WordCtxNormal
			content, sawNewline := l._ReadSingleQuote(start)
			chars = append(chars, content)
			if trackNewline && sawNewline && l._Parser != nil {
				l._Parser._Saw_newline_in_single_quote = true
			}
			continue
		}
		if ch == "\"" {
			l.Advance()
			var inSingleInDquote bool
			var c string
			var nextC byte
			var handleLineContinuation bool
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
						nextC = l.Source[l.Pos+1]
						if nextC == '\n' {
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
						cmdsubResult0, cmdsubResult1 := l._Parser._ParseBacktickSubstitution()
						l._SyncFromParser()
						if cmdsubResult0 != nil {
							parts = append(parts, cmdsubResult0)
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
			nextCh := l.Source[l.Pos+1]
			if ctx != WordCtxRegex && nextCh == '\n' {
				l.Advance()
				l.Advance()
			} else {
				chars = append(chars, l.Advance())
				chars = append(chars, l.Advance())
			}
			continue
		}
		if ctx != WordCtxRegex && ch == "$" && l.Pos+1 < l.Length && l.Source[l.Pos+1] == '\'' {
			ansiResult0, ansiResult1 := l._ReadAnsiCQuote()
			if ansiResult0 != nil {
				parts = append(parts, ansiResult0)
				chars = append(chars, ansiResult1)
			} else {
				chars = append(chars, l.Advance())
			}
			continue
		}
		if ctx != WordCtxRegex && ch == "$" && l.Pos+1 < l.Length && l.Source[l.Pos+1] == '"' {
			localeResult0, localeResult1, localeResult2 := l._ReadLocaleString()
			if localeResult0 != nil {
				parts = append(parts, localeResult0)
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
				if l._Extglob && ctx == WordCtxNormal && len(chars) > 0 && len(chars[len(chars)-1]) == 2 && chars[len(chars)-1][0] == '$' && strings.ContainsRune("?*@", rune(chars[len(chars)-1][1])) && !(l.AtEnd()) && l.Peek() == "(" {
					chars = append(chars, l.Advance())
					content := l._ParseMatchedPair("(", ")", MatchedPairFlags_EXTGLOB)
					chars = append(chars, content)
					chars = append(chars, ")")
				}
			}
			continue
		}
		if ctx != WordCtxRegex && ch == "`" {
			l._SyncToParser()
			cmdsubResult0, cmdsubResult1 := l._Parser._ParseBacktickSubstitution()
			l._SyncFromParser()
			if cmdsubResult0 != nil {
				parts = append(parts, cmdsubResult0)
				chars = append(chars, cmdsubResult1)
			} else {
				chars = append(chars, l.Advance())
			}
			continue
		}
		if ctx != WordCtxRegex && _IsRedirectChar(ch) && l.Pos+1 < l.Length && l.Source[l.Pos+1] == '(' {
			l._SyncToParser()
			procsubResult0, procsubResult1 := l._Parser._ParseProcessSubstitution()
			l._SyncFromParser()
			if procsubResult0 != nil {
				parts = append(parts, procsubResult0)
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
			isArrayAssign := false
			if len(chars) >= 3 && chars[len(chars)-2] == "+" && chars[len(chars)-1] == "=" {
				isArrayAssign = _IsArrayAssignmentPrefix(chars[0 : len(chars)-2])
			} else if chars[len(chars)-1] == "=" && len(chars) >= 2 {
				isArrayAssign = _IsArrayAssignmentPrefix(chars[0 : len(chars)-1])
			}
			if isArrayAssign && atCommandStart || inAssignBuiltin {
				l._SyncToParser()
				arrayResult0, arrayResult1 := l._Parser._ParseArrayLiteral()
				l._SyncFromParser()
				if arrayResult0 != nil {
					parts = append(parts, arrayResult0)
					chars = append(chars, arrayResult1)
				} else {
					break
				}
				continue
			}
		}
		if l._Extglob && ctx == WordCtxNormal && _IsExtglobPrefix(ch) && l.Pos+1 < l.Length && l.Source[l.Pos+1] == '(' {
			chars = append(chars, l.Advance())
			chars = append(chars, l.Advance())
			content := l._ParseMatchedPair("(", ")", MatchedPairFlags_EXTGLOB)
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
	isProcsub := c == "<" || c == ">" && l.Pos+1 < l.Length && l.Source[l.Pos+1] == '('
	isRegexParen := l._Word_context == WordCtxRegex && c == "(" || c == ")"
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
	if l._Token_cache != nil {
		tok := l._Token_cache
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
	if l._Token_cache == nil {
		savedLast := l._Last_read_token
		l._Token_cache = l.NextToken()
		l._Last_read_token = savedLast
	}
	return l._Token_cache
}

func (l *Lexer) _ReadAnsiCQuote() (Node, string) {
	if l.AtEnd() || l.Peek() != "$" {
		return nil, ""
	}
	if l.Pos+1 >= l.Length || l.Source[l.Pos+1] != '\'' {
		return nil, ""
	}
	start := l.Pos
	l.Advance()
	l.Advance()
	contentChars := []string{}
	foundClose := false
	for !(l.AtEnd()) {
		ch := l.Peek()
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
	text := l.Source[start:l.Pos]
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
	if l.AtEnd() || l.Peek() != "$" {
		return nil, "", []interface{}{}
	}
	if l.Pos+1 >= l.Length || l.Source[l.Pos+1] != '"' {
		return nil, "", []interface{}{}
	}
	start := l.Pos
	l.Advance()
	l.Advance()
	contentChars := []string{}
	innerParts := []Node{}
	foundClose := false
	for !(l.AtEnd()) {
		ch := l.Peek()
		var nextCh byte
		if ch == "\"" {
			l.Advance()
			foundClose = true
			break
		} else if ch == "\\" && l.Pos+1 < l.Length {
			nextCh = l.Source[l.Pos+1]
			if nextCh == '\n' {
				l.Advance()
				l.Advance()
			} else {
				contentChars = append(contentChars, l.Advance())
				contentChars = append(contentChars, l.Advance())
			}
		} else if ch == "$" && l.Pos+2 < l.Length && l.Source[l.Pos+1] == '(' && l.Source[l.Pos+2] == '(' {
			l._SyncToParser()
			arithNode, arithText := l._Parser._ParseArithmeticExpansion()
			l._SyncFromParser()
			if arithNode != nil {
				innerParts = append(innerParts, arithNode)
				contentChars = append(contentChars, arithText)
			} else {
				l._SyncToParser()
				cmdsubNode, cmdsubText := l._Parser._ParseCommandSubstitution()
				l._SyncFromParser()
				if cmdsubNode != nil {
					innerParts = append(innerParts, cmdsubNode)
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
				innerParts = append(innerParts, cmdsubNode)
				contentChars = append(contentChars, cmdsubText)
			} else {
				contentChars = append(contentChars, l.Advance())
			}
		} else if ch == "$" {
			l._SyncToParser()
			paramNode, paramText := l._Parser._ParseParamExpansion(false)
			l._SyncFromParser()
			if paramNode != nil {
				innerParts = append(innerParts, paramNode)
				contentChars = append(contentChars, paramText)
			} else {
				contentChars = append(contentChars, l.Advance())
			}
		} else if ch == "`" {
			l._SyncToParser()
			cmdsubNode, cmdsubText := l._Parser._ParseBacktickSubstitution()
			l._SyncFromParser()
			if cmdsubNode != nil {
				innerParts = append(innerParts, cmdsubNode)
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
		return nil, "", []interface{}{}
	}
	content := strings.Join(contentChars, "")
	text := "$\"" + content + "\""
	return NewLocaleString(content), text, innerParts
}

func (l *Lexer) _UpdateDolbraceForOp(op string, hasParam bool) {
	if l._Dolbrace_state == DolbraceState_NONE {
		return
	}
	if op == "" || len(op) == 0 {
		return
	}
	firstChar := op[0]
	if l._Dolbrace_state == DolbraceState_PARAM && hasParam {
		if strings.ContainsRune("%#^,", rune(firstChar)) {
			l._Dolbrace_state = DolbraceState_QUOTE
			return
		}
		if firstChar == '/' {
			l._Dolbrace_state = DolbraceState_QUOTE2
			return
		}
	}
	if l._Dolbrace_state == DolbraceState_PARAM {
		if strings.ContainsRune("#%^,~:-=?+/", rune(firstChar)) {
			l._Dolbrace_state = DolbraceState_OP
		}
	}
}

func (l *Lexer) _ConsumeParamOperator() string {
	if l.AtEnd() {
		return ""
	}
	ch := l.Peek()
	if ch == ":" {
		l.Advance()
		if l.AtEnd() {
			return ":"
		}
		nextCh := l.Peek()
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
	depth := 1
	i := startPos + 1
	quote := NewQuoteState()
	for i < l.Length {
		c := l.Source[i]
		if quote.Single {
			if c == '\'' {
				quote.Single = false
			}
			i += 1
			continue
		}
		if quote.Double {
			if c == '\\' && i+1 < l.Length {
				i += 2
				continue
			}
			if c == '"' {
				quote.Double = false
			}
			i += 1
			continue
		}
		if c == '\'' {
			quote.Single = true
			i += 1
			continue
		}
		if c == '"' {
			quote.Double = true
			i += 1
			continue
		}
		if c == '\\' {
			i += 2
			continue
		}
		if c == '}' {
			return false
		}
		if c == '[' {
			depth += 1
		} else if c == ']' {
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
	if l.AtEnd() {
		return ""
	}
	ch := l.Peek()
	if _IsSpecialParam(ch) {
		if ch == "$" && l.Pos+1 < l.Length && strings.ContainsRune("{'\"", rune(l.Source[l.Pos+1])) {
			return ""
		}
		l.Advance()
		return ch
	}
	if unicode.IsDigit(_runeFromChar(ch)) {
		nameChars := []string{}
		for !(l.AtEnd()) && unicode.IsDigit(_runeFromChar(l.Peek())) {
			nameChars = append(nameChars, l.Advance())
		}
		return strings.Join(nameChars, "")
	}
	if unicode.IsLetter(_runeFromChar(ch)) || ch == "_" {
		nameChars = []string{}
		for !(l.AtEnd()) {
			c := l.Peek()
			var content string
			if (unicode.IsLetter(_runeFromChar(c)) || unicode.IsDigit(_runeFromChar(c))) || c == "_" {
				nameChars = append(nameChars, l.Advance())
			} else if c == "[" {
				if !(l._ParamSubscriptHasClose(l.Pos)) {
					break
				}
				nameChars = append(nameChars, l.Advance())
				content := l._ParseMatchedPair("[", "]", MatchedPairFlags_ARRAYSUB)
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
		text := l.Source[start:l.Pos]
		return NewParamExpansion(ch, "", ""), text
	}
	if unicode.IsLetter(_runeFromChar(ch)) || ch == "_" {
		nameStart := l.Pos
		for !(l.AtEnd()) {
			c := l.Peek()
			if (unicode.IsLetter(_runeFromChar(c)) || unicode.IsDigit(_runeFromChar(c))) || c == "_" {
				l.Advance()
			} else {
				break
			}
		}
		name := l.Source[nameStart:l.Pos]
		text = l.Source[start:l.Pos]
		return NewParamExpansion(name, "", ""), text
	}
	l.Pos = start
	return nil, ""
}

func (l *Lexer) _ReadBracedParam(start int, inDquote bool) (Node, string) {
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
		param := l._ConsumeParamName()
		if param && !(l.AtEnd()) && l.Peek() == "}" {
			l.Advance()
			text := l.Source[start:l.Pos]
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
		var suffix string
		var trailing string
		var op string
		var arg string
		if param {
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
				trailing := l._ParseMatchedPair("{", "}", MatchedPairFlags_DOLBRACE)
				text = l.Source[start:l.Pos]
				l._Dolbrace_state = savedDolbrace
				return NewParamIndirect(param+suffix+trailing, "", ""), text
			}
			op = l._ConsumeParamOperator()
			if op == nil && !(l.AtEnd()) && !strings.Contains("}\"'`", l.Peek()) {
				op = l.Advance()
			}
			if op != nil && !strings.Contains("\"'`", op) {
				arg := l._ParseMatchedPair("{", "}", MatchedPairFlags_DOLBRACE)
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
	if !(param) {
		var content string
		if !(l.AtEnd()) && strings.Contains("-=+?", l.Peek()) || l.Peek() == ":" && l.Pos+1 < l.Length && _IsSimpleParamOp(l.Source[l.Pos+1]) {
			param = ""
		} else {
			content := l._ParseMatchedPair("{", "}", MatchedPairFlags_DOLBRACE)
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
	if op == nil {
		var dollarCount int
		var backtickPos int
		var bc string
		var nextC byte
		if !(l.AtEnd()) && l.Peek() == "$" && l.Pos+1 < l.Length && _containsAny([]interface{}{"\"", "'"}, l.Source[l.Pos+1]) {
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
					nextC = l.Source[l.Pos+1]
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
		} else if !(l.AtEnd()) && l.Peek() == "$" && l.Pos+1 < l.Length && l.Source[l.Pos+1] == '{' {
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
		inner := arg[1 : len(arg)-1]
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
	w.Kind = "word"
	w.Value = value
	if parts == nil {
		parts = []Node{}
	}
	w.Parts = parts
	return w
}

func (w *Word) ToSexp() string {
	value := w.Value
	value = w._ExpandAllAnsiCQuotes(value)
	value = w._StripLocaleStringDollars(value)
	value = w._NormalizeArrayWhitespace(value)
	value = w._FormatCommandSubstitutions(value, false)
	value = w._NormalizeParamExpansionNewlines(value)
	value = w._StripArithLineContinuations(value)
	value = w._DoubleCtlescSmart(value)
	value = strings.ReplaceAll(value, "", "")
	value = strings.ReplaceAll(value, "\\", "\\\\")
	if strings.HasSuffix(value, "\\\\") && !(strings.HasSuffix(value, "\\\\\\\\")) {
		value = value + "\\\\"
	}
	escaped := strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(value, "\"", "\\\""), "\n", "\\n"), "\t", "\\t")
	return "(word \"" + escaped + "\")"
}

func (w *Word) _AppendWithCtlesc(result []byte, byteVal int) {
	result = append(result, byteVal)
}

func (w *Word) _DoubleCtlescSmart(value string) string {
	result := []rune{}
	quote := NewQuoteState()
	for _, c := range value {
		if c == '\'' && !(quote.Double) {
			quote.Single = !(quote.Single)
		} else if c == '"' && !(quote.Single) {
			quote.Double = !(quote.Double)
		}
		result = append(result, c)
		if c == '' {
			var bsCount int
			if quote.Double {
				bsCount = 0
				for j := len(result) - 2; j > -1; j += -1 {
					if result[j] == "\\" {
						bsCount += 1
					} else {
						break
					}
				}
				if bsCount%2 == 0 {
					result = append(result, "")
				}
			} else {
				result = append(result, "")
			}
		}
	}
	return strings.Join(result, "")
}

func (w *Word) _NormalizeParamExpansionNewlines(value string) string {
	result := []byte{}
	i := 0
	quote := NewQuoteState()
	for i < len(value) {
		c := value[i]
		var hadLeadingNewline bool
		var depth int
		var ch byte
		if c == '\'' && !(quote.Double) {
			quote.Single = !(quote.Single)
			result = append(result, c)
			i += 1
		} else if c == '"' && !(quote.Single) {
			quote.Double = !(quote.Double)
			result = append(result, c)
			i += 1
		} else if _IsExpansionStart(value, i, "${") && !(quote.Single) {
			result = append(result, "$")
			result = append(result, "{")
			i += 2
			hadLeadingNewline = i < len(value) && value[i] == '\n'
			if hadLeadingNewline {
				result = append(result, " ")
				i += 1
			}
			depth = 1
			for i < len(value) && depth > 0 {
				ch = value[i]
				if ch == '\\' && i+1 < len(value) && !(quote.Single) {
					if value[i+1] == '\n' {
						i += 2
						continue
					}
					result = append(result, ch)
					result = append(result, value[i+1])
					i += 2
					continue
				}
				if ch == '\'' && !(quote.Double) {
					quote.Single = !(quote.Single)
				} else if ch == '"' && !(quote.Single) {
					quote.Double = !(quote.Double)
				} else if !(quote.InQuotes()) {
					if ch == '{' {
						depth += 1
					} else if ch == '}' {
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

func (w *Word) _ExpandAnsiCEscapes(value string) string {
	if !(strings.HasPrefix(value, "'") && strings.HasSuffix(value, "'")) {
		return value
	}
	inner := value[1 : len(value)-1]
	result := []byte{}
	i := 0
	for i < len(inner) {
		var c byte
		var simple interface{}
		var j interface{}
		var hexStr interface{}
		var byteVal int
		var codepoint int
		var ctrlChar byte
		var skipExtra int
		var ctrlVal int
		if inner[i] == '\\' && i+1 < len(inner) {
			c = inner[i+1]
			simple = _GetAnsiEscape(string(c))
			if simple >= 0 {
				result = append(result, simple)
				i += 2
			} else if c == '\'' {
				result = append(result, []byte{39, 92, 39, 39}...)
				i += 2
			} else if c == 'x' {
				if i+2 < len(inner) && inner[i+2] == '{' {
					j = i + 3
					for j < len(inner) && _IsHexDigit(string(inner[j])) {
						j += 1
					}
					hexStr = inner[i+3 : j]
					if j < len(inner) && inner[j] == '}' {
						j += 1
					}
					if !(hexStr) {
						return "'" + string(result) + "'"
					}
					byteVal = _parseInt(hexStr, 16) & 255
					if byteVal == 0 {
						return "'" + string(result) + "'"
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
							return "'" + string(result) + "'"
						}
						w._AppendWithCtlesc(result, byteVal)
						i = j
					} else {
						result = append(result, rune(inner[i][0]))
						i += 1
					}
				}
			} else if c == 'u' {
				j = i + 2
				for j < len(inner) && j < i+6 && _IsHexDigit(string(inner[j])) {
					j += 1
				}
				if j > i+2 {
					codepoint = _parseInt(inner[i+2:j], 16)
					if codepoint == 0 {
						return "'" + string(result) + "'"
					}
					result = append(result, []byte(string(rune(codepoint)))...)
					i = j
				} else {
					result = append(result, rune(inner[i][0]))
					i += 1
				}
			} else if c == 'U' {
				j = i + 2
				for j < len(inner) && j < i+10 && _IsHexDigit(string(inner[j])) {
					j += 1
				}
				if j > i+2 {
					codepoint = _parseInt(inner[i+2:j], 16)
					if codepoint == 0 {
						return "'" + string(result) + "'"
					}
					result = append(result, []byte(string(rune(codepoint)))...)
					i = j
				} else {
					result = append(result, rune(inner[i][0]))
					i += 1
				}
			} else if c == 'c' {
				if i+3 <= len(inner) {
					ctrlChar = inner[i+2]
					skipExtra = 0
					if ctrlChar == '\\' && i+4 <= len(inner) && inner[i+3] == '\\' {
						skipExtra = 1
					}
					ctrlVal = rune(ctrlChar[0]) & 31
					if ctrlVal == 0 {
						return "'" + string(result) + "'"
					}
					w._AppendWithCtlesc(result, ctrlVal)
					i += 3 + skipExtra
				} else {
					result = append(result, rune(inner[i][0]))
					i += 1
				}
			} else if c == '0' {
				j = i + 2
				for j < len(inner) && j < i+4 && _IsOctalDigit(string(inner[j])) {
					j += 1
				}
				if j > i+2 {
					byteVal = _parseInt(inner[i+1:j], 8) & 255
					if byteVal == 0 {
						return "'" + string(result) + "'"
					}
					w._AppendWithCtlesc(result, byteVal)
					i = j
				} else {
					return "'" + string(result) + "'"
				}
			} else if c >= '1' && c <= '7' {
				j = i + 1
				for j < len(inner) && j < i+4 && _IsOctalDigit(string(inner[j])) {
					j += 1
				}
				byteVal = _parseInt(inner[i+1:j], 8) & 255
				if byteVal == 0 {
					return "'" + string(result) + "'"
				}
				w._AppendWithCtlesc(result, byteVal)
				i = j
			} else {
				result = append(result, 92)
				result = append(result, rune(c[0]))
				i += 2
			}
		} else {
			result = append(result, []byte(inner[i])...)
			i += 1
		}
	}
	return "'" + string(result) + "'"
}

func (w *Word) _ExpandAllAnsiCQuotes(value string) string {
	result := []byte{}
	i := 0
	quote := NewQuoteState()
	inBacktick := false
	braceDepth := 0
	for i < len(value) {
		ch := value[i]
		if ch == '`' && !(quote.Single) {
			inBacktick = !(inBacktick)
			result = append(result, ch)
			i += 1
			continue
		}
		if inBacktick {
			if ch == '\\' && i+1 < len(value) {
				result = append(result, ch)
				result = append(result, value[i+1])
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
			} else if ch == '}' && braceDepth > 0 && !(quote.Double) {
				braceDepth -= 1
				result = append(result, ch)
				panic("TODO: incomplete implementation")
			}
		}
		effectiveInDquote := quote.Double
		var isAnsiC bool
		var j interface{}
		var ansiStr interface{}
		var expanded interface{}
		var outerInDquote interface{}
		var inner interface{}
		var resultStr interface{}
		var inPattern bool
		var lastBraceIdx interface{}
		var afterBrace byte
		var varNameLen int
		var c interface{}
		var opStart interface{}
		var firstChar interface{}
		var rest interface{}
		if ch == '\'' && !(effectiveInDquote) {
			isAnsiC = !(quote.Single) && i > 0 && value[i-1] == '$' && _CountConsecutiveDollarsBefore(value, i-1)%2 == 0
			if !(isAnsiC) {
				quote.Single = !(quote.Single)
			}
			result = append(result, ch)
			i += 1
		} else if ch == '"' && !(quote.Single) {
			quote.Double = !(quote.Double)
			result = append(result, ch)
			i += 1
		} else if ch == '\\' && i+1 < len(value) && !(quote.Single) {
			result = append(result, ch)
			result = append(result, value[i+1])
			i += 2
		} else if strings.HasPrefix(value[i:], "$'") && !(quote.Single) && !(effectiveInDquote) && _CountConsecutiveDollarsBefore(value, i)%2 == 0 {
			j = i + 2
			for j < len(value) {
				if value[j] == '\\' && j+1 < len(value) {
					j += 2
				} else if value[j] == '\'' {
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
				if strings.Index(inner, "") == -1 {
					resultStr = strings.Join(result, "")
					inPattern = false
					lastBraceIdx = strings.LastIndex(resultStr, "${")
					if lastBraceIdx >= 0 {
						afterBrace = resultStr[lastBraceIdx+2:]
						varNameLen = 0
						if afterBrace {
							if strings.Contains("@*#?-$!0123456789_", afterBrace[0]) {
								varNameLen = 1
							} else if unicode.IsLetter(_runeFromChar(afterBrace[0])) || afterBrace[0] == "_" {
								for varNameLen < len(afterBrace) {
									c = afterBrace[varNameLen]
									if !((unicode.IsLetter(_runeFromChar(c)) || unicode.IsDigit(_runeFromChar(c))) || c == "_") {
										break
									}
									varNameLen += 1
								}
							}
						}
						if varNameLen > 0 && varNameLen < len(afterBrace) && !strings.Contains("#?-", afterBrace[0]) {
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
							if !(inPattern) && opStart && !strings.Contains("%#/^,~:+-=?", opStart[0]) {
								for _, op := range []string{"//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"} {
									if _contains(opStart, op) {
										inPattern = true
										break
									}
								}
							}
						} else if varNameLen == 0 && len(afterBrace) > 1 {
							firstChar = afterBrace[0]
							if !strings.Contains("%#/^,", firstChar) {
								rest = afterBrace[1:]
								for _, op := range []string{"//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"} {
									if _contains(rest, op) {
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
	result := []byte{}
	i := 0
	braceDepth := 0
	bracketDepth := 0
	quote := NewQuoteState()
	braceQuote := NewQuoteState()
	bracketInDoubleQuote := false
	for i < len(value) {
		ch := value[i]
		var dollarCount int
		if ch == '\\' && i+1 < len(value) && !(quote.Single) && !(braceQuote.Single) {
			result = append(result, ch)
			result = append(result, value[i+1])
			i += 2
		} else if strings.HasPrefix(value[i:], "${") && !(quote.Single) && !(braceQuote.Single) && i == 0 || value[i-1] != '$' {
			braceDepth += 1
			braceQuote.Double = false
			braceQuote.Single = false
			result = append(result, "$")
			result = append(result, "{")
			i += 2
		} else if ch == '}' && braceDepth > 0 && !(quote.Single) && !(braceQuote.Double) && !(braceQuote.Single) {
			braceDepth -= 1
			result = append(result, ch)
			i += 1
		} else if ch == '[' && braceDepth > 0 && !(quote.Single) && !(braceQuote.Double) {
			bracketDepth += 1
			bracketInDoubleQuote = false
			result = append(result, ch)
			i += 1
		} else if ch == ']' && bracketDepth > 0 && !(quote.Single) && !(bracketInDoubleQuote) {
			bracketDepth -= 1
			result = append(result, ch)
			i += 1
		} else if ch == '\'' && !(quote.Double) && braceDepth == 0 {
			quote.Single = !(quote.Single)
			result = append(result, ch)
			i += 1
		} else if ch == '"' && !(quote.Single) && braceDepth == 0 {
			quote.Double = !(quote.Double)
			result = append(result, ch)
			i += 1
		} else if ch == '"' && !(quote.Single) && bracketDepth > 0 {
			bracketInDoubleQuote = !(bracketInDoubleQuote)
			result = append(result, ch)
			i += 1
		} else if ch == '"' && !(quote.Single) && !(braceQuote.Single) && braceDepth > 0 {
			braceQuote.Double = !(braceQuote.Double)
			result = append(result, ch)
			i += 1
		} else if ch == '\'' && !(quote.Double) && !(braceQuote.Double) && braceDepth > 0 {
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
	i := 0
	if !(i < len(value) && unicode.IsLetter(_runeFromChar(value[i])) || value[i] == '_') {
		return value
	}
	i += 1
	for i < len(value) && (unicode.IsLetter(_runeFromChar(value[i])) || unicode.IsDigit(_runeFromChar(value[i]))) || value[i] == '_' {
		i += 1
	}
	for i < len(value) && value[i] == '[' {
		depth := 1
		i += 1
		for i < len(value) && depth > 0 {
			if value[i] == '[' {
				depth += 1
			} else if value[i] == ']' {
				depth -= 1
			}
			i += 1
		}
		if depth != 0 {
			return value
		}
	}
	if i < len(value) && value[i] == '+' {
		i += 1
	}
	if !(i+1 < len(value) && value[i] == '=' && value[i+1] == '(') {
		return value
	}
	prefix := value[0 : i+1]
	openParenPos := i + 1
	var closeParenPos interface{}
	if strings.HasSuffix(value, ")") {
		closeParenPos = len(value) - 1
	} else {
		closeParenPos = w._FindMatchingParen(value, openParenPos)
		if closeParenPos < 0 {
			return value
		}
	}
	inner := value[openParenPos+1 : closeParenPos]
	suffix := value[closeParenPos+1 : len(value)]
	result := w._NormalizeArrayInner(inner)
	return prefix + "(" + result + ")" + suffix
}

func (w *Word) _FindMatchingParen(value string, openPos int) int {
	if openPos >= len(value) || value[openPos] != '(' {
		return -1
	}
	i := openPos + 1
	depth := 1
	quote := NewQuoteState()
	for i < len(value) && depth > 0 {
		ch := value[i]
		if ch == '\\' && i+1 < len(value) && !(quote.Single) {
			i += 2
			continue
		}
		if ch == '\'' && !(quote.Double) {
			quote.Single = !(quote.Single)
			i += 1
			continue
		}
		if ch == '"' && !(quote.Single) {
			quote.Double = !(quote.Double)
			i += 1
			continue
		}
		if quote.Single || quote.Double {
			i += 1
			continue
		}
		if ch == '#' {
			for i < len(value) && value[i] != '\n' {
				i += 1
			}
			continue
		}
		if ch == '(' {
			depth += 1
		} else if ch == ')' {
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
	normalized := []string{}
	i := 0
	inWhitespace := true
	braceDepth := 0
	bracketDepth := 0
	for i < len(inner) {
		ch := inner[i]
		var j interface{}
		var dqContent []string
		var dqBraceDepth int
		var depth int
		if _IsWhitespace(string(ch)) {
			if !(inWhitespace) && len(normalized) > 0 && braceDepth == 0 && bracketDepth == 0 {
				normalized = append(normalized, " ")
				inWhitespace = true
			}
			if braceDepth > 0 || bracketDepth > 0 {
				normalized = append(normalized, string(ch))
			}
			i += 1
		} else if ch == '\'' {
			inWhitespace = false
			j = i + 1
			for j < len(inner) && inner[j] != '\'' {
				j += 1
			}
			normalized = append(normalized, inner[i:j+1])
			i = j + 1
		} else if ch == '"' {
			inWhitespace = false
			j = i + 1
			dqContent = []string{"\""}
			dqBraceDepth = 0
			for j < len(inner) {
				if inner[j] == '\\' && j+1 < len(inner) {
					if inner[j+1] == '\n' {
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
				} else if inner[j] == '}' && dqBraceDepth > 0 {
					dqContent = append(dqContent, "}")
					dqBraceDepth -= 1
					j += 1
				} else if inner[j] == '"' && dqBraceDepth == 0 {
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
		} else if ch == '\\' && i+1 < len(inner) {
			if inner[i+1] == '\n' {
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
				if j+1 < len(inner) && inner[j] == '(' && inner[j+1] == '(' {
					depth += 1
					j += 2
				} else if j+1 < len(inner) && inner[j] == ')' && inner[j+1] == ')' {
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
				if inner[j] == '(' && j > 0 && inner[j-1] == '$' {
					depth += 1
				} else if inner[j] == ')' {
					depth -= 1
				} else if inner[j] == '\'' {
					j += 1
					for j < len(inner) && inner[j] != '\'' {
						j += 1
					}
				} else if inner[j] == '"' {
					j += 1
					for j < len(inner) {
						if inner[j] == '\\' && j+1 < len(inner) {
							j += 2
							continue
						}
						if inner[j] == '"' {
							break
						}
						j += 1
					}
				}
				j += 1
			}
			normalized = append(normalized, inner[i:j])
			i = j
		} else if ch == '<' || ch == '>' && i+1 < len(inner) && inner[i+1] == '(' {
			inWhitespace = false
			j = i + 2
			depth = 1
			for j < len(inner) && depth > 0 {
				if inner[j] == '(' {
					depth += 1
				} else if inner[j] == ')' {
					depth -= 1
				} else if inner[j] == '\'' {
					j += 1
					for j < len(inner) && inner[j] != '\'' {
						j += 1
					}
				} else if inner[j] == '"' {
					j += 1
					for j < len(inner) {
						if inner[j] == '\\' && j+1 < len(inner) {
							j += 2
							continue
						}
						if inner[j] == '"' {
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
		} else if ch == '{' && braceDepth > 0 {
			normalized = append(normalized, string(ch))
			braceDepth += 1
			i += 1
		} else if ch == '}' && braceDepth > 0 {
			normalized = append(normalized, string(ch))
			braceDepth -= 1
			i += 1
		} else if ch == '#' && braceDepth == 0 && inWhitespace {
			for i < len(inner) && inner[i] != '\n' {
				i += 1
			}
		} else if ch == '[' {
			if inWhitespace || bracketDepth > 0 {
				bracketDepth += 1
			}
			inWhitespace = false
			normalized = append(normalized, string(ch))
			i += 1
		} else if ch == ']' && bracketDepth > 0 {
			normalized = append(normalized, string(ch))
			bracketDepth -= 1
			i += 1
		} else {
			inWhitespace = false
			normalized = append(normalized, string(ch))
			i += 1
		}
	}
	return strings.TrimRight(strings.Join(normalized, ""), " \t")
}

func (w *Word) _StripArithLineContinuations(value string) string {
	result := []byte{}
	i := 0
	for i < len(value) {
		var start interface{}
		var depth int
		var arithContent []string
		var firstCloseIdx interface{}
		var numBackslashes int
		var j interface{}
		var content interface{}
		var closing string
		if _IsExpansionStart(value, i, "$((") {
			start = i
			i += 3
			depth = 2
			arithContent = []string{}
			firstCloseIdx = nil
			for i < len(value) && depth > 0 {
				if value[i] == '(' {
					arithContent = append(arithContent, "(")
					depth += 1
					i += 1
					if depth > 1 {
						firstCloseIdx = nil
					}
				} else if value[i] == ')' {
					if depth == 2 {
						firstCloseIdx = len(arithContent)
					}
					depth -= 1
					if depth > 0 {
						arithContent = append(arithContent, ")")
					}
					i += 1
				} else if value[i] == '\\' && i+1 < len(value) && value[i+1] == '\n' {
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
						firstCloseIdx = nil
					}
				} else {
					arithContent = append(arithContent, string(value[i]))
					i += 1
					if depth == 1 {
						firstCloseIdx = nil
					}
				}
			}
			if depth == 0 || depth == 1 && firstCloseIdx != nil {
				content = strings.Join(arithContent, "")
				if firstCloseIdx != nil {
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
			result = append(result, value[i])
			i += 1
		}
	}
	return strings.Join(result, "")
}

func (w *Word) _CollectCmdsubs(node interface{}) []interface{} {
	result := []interface{}{}
	nodeKind := _getattr(node, "kind", nil)
	var elements interface{}
	var parts interface{}
	var expr interface{}
	if nodeKind == "cmdsub" {
		result = append(result, node)
	} else if nodeKind == "array" {
		elements = _getattr(node, "elements", []interface{}{})
		for _, elem := range elements {
			parts = _getattr(elem, "parts", []interface{}{})
			for _, p := range parts {
				if _getattr(p, "kind", nil) == "cmdsub" {
					result = append(result, p)
				} else {
					result = append(result, w._CollectCmdsubs(p)...)
				}
			}
		}
	} else {
		expr = _getattr(node, "expression", nil)
		if expr != nil {
			result = append(result, w._CollectCmdsubs(expr)...)
		}
	}
	left := _getattr(node, "left", nil)
	if left != nil {
		result = append(result, w._CollectCmdsubs(left)...)
	}
	right := _getattr(node, "right", nil)
	if right != nil {
		result = append(result, w._CollectCmdsubs(right)...)
	}
	operand := _getattr(node, "operand", nil)
	if operand != nil {
		result = append(result, w._CollectCmdsubs(operand)...)
	}
	condition := _getattr(node, "condition", nil)
	if condition != nil {
		result = append(result, w._CollectCmdsubs(condition)...)
	}
	trueValue := _getattr(node, "true_value", nil)
	if trueValue != nil {
		result = append(result, w._CollectCmdsubs(trueValue)...)
	}
	falseValue := _getattr(node, "false_value", nil)
	if falseValue != nil {
		result = append(result, w._CollectCmdsubs(falseValue)...)
	}
	return result
}

func (w *Word) _CollectProcsubs(node interface{}) []interface{} {
	result := []interface{}{}
	nodeKind := _getattr(node, "kind", nil)
	var elements interface{}
	var parts interface{}
	if nodeKind == "procsub" {
		result = append(result, node)
	} else if nodeKind == "array" {
		elements = _getattr(node, "elements", []interface{}{})
		for _, elem := range elements {
			parts = _getattr(elem, "parts", []interface{}{})
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
	cmdsubParts := []interface{}{}
	procsubParts := []interface{}{}
	hasArith := false
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
	hasUntrackedCmdsub := false
	hasUntrackedProcsub := false
	idx := 0
	scanQuote := NewQuoteState()
	for idx < len(value) {
		if value[idx] == '"' {
			scanQuote.Double = !(scanQuote.Double)
			idx += 1
		} else if value[idx] == '\'' && !(scanQuote.Double) {
			idx += 1
			for idx < len(value) && value[idx] != '\'' {
				idx += 1
			}
			if idx < len(value) {
				idx += 1
			}
		} else if strings.HasPrefix(value[idx:], "$(") && !(strings.HasPrefix(value[idx:], "$((")) && !(_IsBackslashEscaped(value, idx)) && !(_IsDollarDollarParen(value, idx)) {
			hasUntrackedCmdsub = true
			break
		} else if strings.HasPrefix(value[idx:], "<(") || strings.HasPrefix(value[idx:], ">(") && !(scanQuote.Double) {
			if idx == 0 || !(unicode.IsLetter(_runeFromChar(value[idx-1])) || unicode.IsDigit(_runeFromChar(value[idx-1]))) && !strings.ContainsRune("\"'", rune(value[idx-1])) {
				hasUntrackedProcsub = true
				break
			}
			idx += 1
		} else {
			idx += 1
		}
	}
	hasParamWithProcsubPattern := _contains(value, "${") && _contains(value, "<(") || _contains(value, ">(")
	if !(len(cmdsubParts) > 0) && !(len(procsubParts) > 0) && !(hasBraceCmdsub) && !(hasUntrackedCmdsub) && !(hasUntrackedProcsub) && !(hasParamWithProcsubPattern) {
		return value
	}
	result := []byte{}
	i := 0
	cmdsubIdx := 0
	procsubIdx := 0
	mainQuote := NewQuoteState()
	extglobDepth := 0
	deprecatedArithDepth := 0
	arithDepth := 0
	arithParenDepth := 0
	for i < len(value) {
		if i > 0 && _IsExtglobPrefix(string(value[i-1])) && value[i] == '(' && !(_IsBackslashEscaped(value, i-1)) {
			extglobDepth += 1
			result = append(result, value[i])
			i += 1
			continue
		}
		if value[i] == ')' && extglobDepth > 0 {
			extglobDepth -= 1
			result = append(result, value[i])
			i += 1
			continue
		}
		if strings.HasPrefix(value[i:], "$[") && !(_IsBackslashEscaped(value, i)) {
			deprecatedArithDepth += 1
			result = append(result, value[i])
			i += 1
			continue
		}
		if value[i] == ']' && deprecatedArithDepth > 0 {
			deprecatedArithDepth -= 1
			result = append(result, value[i])
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
			if value[i] == '(' {
				arithParenDepth += 1
				result = append(result, value[i])
				i += 1
				continue
			} else if value[i] == ')' {
				arithParenDepth -= 1
				result = append(result, value[i])
				i += 1
				continue
			}
		}
		if _IsExpansionStart(value, i, "$((") && !(hasArith) {
			j := _FindCmdsubEnd(value, i+2)
			result = append(result, value[i:j])
			if cmdsubIdx < len(cmdsubParts) {
				cmdsubIdx += 1
			}
			i = j
			continue
		}
		var inner interface{}
		var node interface{}
		var formatted interface{}
		var hasPipe bool
		var prefix string
		var origInner interface{}
		var endsWithNewline interface{}
		var suffix string
		var isProcsub bool
		var direction byte
		var compact interface{}
		var rawContent interface{}
		var leadingWsEnd int
		var leadingWs interface{}
		var stripped interface{}
		var normalizedWs interface{}
		var spaced interface{}
		var rawStripped interface{}
		var finalOutput interface{}
		var depth int
		var braceQuote interface{}
		var c byte
		var formattedInner string
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
				formatted = _FormatCmdsubNode(node.Command, 0, false, false, false)
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
		} else if value[i] == '`' && cmdsubIdx < len(cmdsubParts) {
			j = i + 1
			for j < len(value) {
				if value[j] == '\\' && j+1 < len(value) {
					j += 2
					continue
				}
				if value[j] == '`' {
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
			if cmdsubIdx < len(cmdsubParts) && _getattr(cmdsubParts[cmdsubIdx], "brace", false) {
				node = cmdsubParts[cmdsubIdx]
				formatted = _FormatCmdsubNode(node.Command, 0, false, false, false)
				hasPipe = value[i+2] == '|'
				prefix = _ternary(hasPipe, "${|", "${ ")
				origInner = value[i+2 : j-1]
				endsWithNewline = strings.HasSuffix(origInner, "\n")
				if !(formatted) || formatted.Isspace() {
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
			isProcsub = i == 0 || !(unicode.IsLetter(_runeFromChar(value[i-1])) || unicode.IsDigit(_runeFromChar(value[i-1]))) && !strings.ContainsRune("\"'", rune(value[i-1]))
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
				direction = value[i]
				j = _FindCmdsubEnd(value, i+2)
				node = procsubParts[procsubIdx]
				compact = _StartsWithSubshell(node.Command)
				formatted = _FormatCmdsubNode(node.Command, 0, true, compact, true)
				rawContent = value[i+2 : j-1]
				if node.Command.Kind() == "subshell" {
					leadingWsEnd = 0
					for leadingWsEnd < len(rawContent) && strings.Contains(" \t\n", rawContent[leadingWsEnd]) {
						leadingWsEnd += 1
					}
					leadingWs = rawContent[0:leadingWsEnd]
					stripped = rawContent[leadingWsEnd:]
					if strings.HasPrefix(stripped, "(") {
						if leadingWs {
							normalizedWs = strings.ReplaceAll(strings.ReplaceAll(leadingWs, "\n", " "), "\t", " ")
							spaced = _FormatCmdsubNode(node.Command, 0, false, false, false)
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
				if _StartsWithSubshell(node.Command) && formatted != rawStripped {
					result = append(result, direction+"("+rawStripped+")")
				} else {
					finalOutput = direction + "(" + formatted + ")"
					result = append(result, finalOutput)
				}
				procsubIdx += 1
				i = j
			} else if isProcsub && len(w.Parts) {
				direction = value[i]
				j = _FindCmdsubEnd(value, i+2)
				if j > len(value) || j > 0 && j <= len(value) && value[j-1] != ')' {
					result = append(result, value[i])
					i += 1
					continue
				}
				inner = value[i+2 : j-1]
				panic("TODO: incomplete implementation")
			} else if isProcsub {
				direction = value[i]
				j = _FindCmdsubEnd(value, i+2)
				if j > len(value) || j > 0 && j <= len(value) && value[j-1] != ')' {
					result = append(result, value[i])
					i += 1
					continue
				}
				inner = value[i+2 : j-1]
				if inArith {
					result = append(result, direction+"("+inner+")")
				} else if strings.TrimSpace(inner) {
					stripped = strings.TrimLeft(inner, " \t")
					result = append(result, direction+"("+stripped+")")
				} else {
					result = append(result, direction+"("+inner+")")
				}
				i = j
			} else {
				result = append(result, value[i])
				i += 1
			}
		} else if _IsExpansionStart(value, i, "${ ") || _IsExpansionStart(value, i, "${\t") || _IsExpansionStart(value, i, "${\n") || _IsExpansionStart(value, i, "${|") && !(_IsBackslashEscaped(value, i)) {
			prefix = strings.ReplaceAll(strings.ReplaceAll(value[i:i+3], "\t", " "), "\n", " ")
			j = i + 3
			depth = 1
			for j < len(value) && depth > 0 {
				if value[j] == '{' {
					depth += 1
				} else if value[j] == '}' {
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
				c = value[j]
				if c == '\\' && j+1 < len(value) && !(braceQuote.Single) {
					j += 2
					continue
				}
				if c == '\'' && !(braceQuote.Double) {
					braceQuote.Single = !(braceQuote.Single)
				} else if c == '"' && !(braceQuote.Single) {
					braceQuote.Double = !(braceQuote.Double)
				} else if !(braceQuote.InQuotes()) {
					if _IsExpansionStart(value, j, "$(") && !(strings.HasPrefix(value[j:], "$((")) {
						j = _FindCmdsubEnd(value, j+2)
						continue
					}
					if c == '{' {
						depth += 1
					} else if c == '}' {
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
		} else if value[i] == '"' {
			mainQuote.Double = !(mainQuote.Double)
			result = append(result, value[i])
			i += 1
		} else if value[i] == '\'' && !(mainQuote.Double) {
			j = i + 1
			for j < len(value) && value[j] != '\'' {
				j += 1
			}
			if j < len(value) {
				j += 1
			}
			result = append(result, value[i:j])
			i = j
		} else {
			result = append(result, value[i])
			i += 1
		}
	}
	return strings.Join(result, "")
}

func (w *Word) _NormalizeExtglobWhitespace(value string) string {
	result := []byte{}
	i := 0
	extglobQuote := NewQuoteState()
	deprecatedArithDepth := 0
	for i < len(value) {
		if value[i] == '"' {
			extglobQuote.Double = !(extglobQuote.Double)
			result = append(result, value[i])
			i += 1
			continue
		}
		if strings.HasPrefix(value[i:], "$[") && !(_IsBackslashEscaped(value, i)) {
			deprecatedArithDepth += 1
			result = append(result, value[i])
			i += 1
			continue
		}
		if value[i] == ']' && deprecatedArithDepth > 0 {
			deprecatedArithDepth -= 1
			result = append(result, value[i])
			i += 1
			continue
		}
		if i+1 < len(value) && value[i+1] == '(' {
			prefixChar := value[i]
			if strings.ContainsRune("><", rune(prefixChar)) && !(extglobQuote.Double) && deprecatedArithDepth == 0 {
				result = append(result, prefixChar)
				result = append(result, "(")
				i += 2
				depth := 1
				patternParts := []string{}
				currentPart := []byte{}
				hasPipe := false
				for i < len(value) && depth > 0 {
					var partContent interface{}
					if value[i] == '\\' && i+1 < len(value) {
						currentPart = append(currentPart, value[i:i+2])
						i += 2
						continue
					} else if value[i] == '(' {
						depth += 1
						currentPart = append(currentPart, value[i])
						i += 1
					} else if value[i] == ')' {
						depth -= 1
						if depth == 0 {
							partContent = strings.Join(currentPart, "")
							if _contains(partContent, "<<") {
								patternParts = append(patternParts, partContent)
							} else if hasPipe {
								patternParts = append(patternParts, strings.TrimSpace(partContent))
							} else {
								patternParts = append(patternParts, partContent)
							}
							break
						}
						currentPart = append(currentPart, value[i])
						i += 1
					} else if value[i] == '|' && depth == 1 {
						if i+1 < len(value) && value[i+1] == '|' {
							currentPart = append(currentPart, "||")
							i += 2
						} else {
							hasPipe = true
							partContent = strings.Join(currentPart, "")
							if _contains(partContent, "<<") {
								patternParts = append(patternParts, partContent)
							} else {
								patternParts = append(patternParts, strings.TrimSpace(partContent))
							}
							currentPart = []byte{}
							i += 1
						}
					} else {
						currentPart = append(currentPart, value[i])
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
		result = append(result, value[i])
		i += 1
	}
	return strings.Join(result, "")
}

func (w *Word) GetCondFormattedValue() string {
	value := w._ExpandAllAnsiCQuotes(w.Value)
	value = w._StripLocaleStringDollars(value)
	value = w._FormatCommandSubstitutions(value, false)
	value = w._NormalizeExtglobWhitespace(value)
	value = strings.ReplaceAll(value, "", "")
	return strings.TrimRight(value, "\n")
}

func NewCommand(words []Node, redirects []Node) *Command {
	c := &Command{}
	c.Kind = "command"
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
		parts = append(parts, r.(Node).ToSexp())
	}
	inner := strings.Join(parts, " ")
	if !(inner) {
		return "(command)"
	}
	return "(command " + inner + ")"
}

func NewPipeline(commands []Node) *Pipeline {
	p := &Pipeline{}
	p.Kind = "pipeline"
	p.Commands = commands
	return p
}

func (p *Pipeline) ToSexp() string {
	if len(p.Commands) == 1 {
		return p.Commands[0].ToSexp()
	}
	cmds := []interface{}{}
	i := 0
	for i < len(p.Commands) {
		cmd := p.Commands[i]
		if cmd.Kind() == "pipe-both" {
			i += 1
			continue
		}
		needsRedirect := i+1 < len(p.Commands) && p.Commands[i+1].Kind() == "pipe-both"
		cmds = append(cmds, []interface{}{cmd, needsRedirect})
		i += 1
	}
	if len(cmds) == 1 {
		pair := cmds[0]
		cmd = pair[0]
		needs := pair[1]
		return p._CmdSexp(cmd, needs)
	}
	lastPair := cmds[len(cmds)-1]
	lastCmd := lastPair[0]
	lastNeeds := lastPair[1]
	result := p._CmdSexp(lastCmd, lastNeeds)
	j := len(cmds) - 2
	for j >= 0 {
		pair = cmds[j]
		cmd = pair[0]
		needs = pair[1]
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
	if !(needsRedirect) {
		return cmd.ToSexp()
	}
	if cmd.Kind() == "command" {
		parts := []string{}
		for _, w := range cmd.Words {
			parts = append(parts, w.ToSexp())
		}
		for _, r := range cmd.Redirects {
			parts = append(parts, r.(Node).ToSexp())
		}
		parts = append(parts, "(redirect \">&\" 1)")
		return "(command " + strings.Join(parts, " ") + ")"
	}
	return cmd.ToSexp()
}

func NewList(parts []Node) *List {
	l := &List{}
	l.Kind = "list"
	l.Parts = parts
	return l
}

func (l *List) ToSexp() string {
	parts := append([]interface{}, l.Parts...)
	opNames := map[string]interface{}{"&&": "and", "||": "or", ";": "semi", "\n": "semi", "&": "background"}
	for len(parts) > 1 && parts[len(parts)-1].Kind() == "operator" && parts[len(parts)-1].Op == ";" || parts[len(parts)-1].Op == "\n" {
		parts = parts[0 : len(parts)-1]
	}
	if len(parts) == 1 {
		return parts[0].ToSexp()
	}
	if parts[len(parts)-1].Kind() == "operator" && parts[len(parts)-1].Op == "&" {
		for i := len(parts) - 3; i > 0; i += -2 {
			if parts[i].Kind() == "operator" && parts[i].Op == ";" || parts[i].Op == "\n" {
				left := parts[0:i]
				right := parts[i+1 : len(parts)-1]
				var leftSexp interface{}
				if len(left) > 1 {
					leftSexp = NewList(left).ToSexp()
				} else {
					leftSexp = left[0].ToSexp()
				}
				var rightSexp interface{}
				if len(right) > 1 {
					rightSexp = NewList(right).ToSexp()
				} else {
					rightSexp = right[0].ToSexp()
				}
				return "(semi " + leftSexp + " (background " + rightSexp + "))"
			}
		}
		innerParts := parts[0 : len(parts)-1]
		if len(innerParts) == 1 {
			return "(background " + innerParts[0].ToSexp() + ")"
		}
		innerList := NewList(innerParts)
		return "(background " + innerList.ToSexp() + ")"
	}
	return l._ToSexpWithPrecedence(parts, opNames)
}

func (l *List) _ToSexpWithPrecedence(parts []interface{}, opNames interface{}) string {
	semiPositions := []interface{}{}
	for i := 0; i < len(parts); i++ {
		if parts[i].Kind() == "operator" && parts[i].Op == ";" || parts[i].Op == "\n" {
			semiPositions = append(semiPositions, i)
		}
	}
	if len(semiPositions) > 0 {
		segments := []interface{}{}
		start := 0
		for _, pos := range semiPositions {
			seg := parts[start:pos]
			if seg && seg[0].Kind() != "operator" {
				segments = append(segments, seg)
			}
			start = pos + 1
		}
		seg = parts[start:len(parts)]
		if seg && seg[0].Kind() != "operator" {
			segments = append(segments, seg)
		}
		if !(len(segments) > 0) {
			return "()"
		}
		result := l._ToSexpAmpAndHigher(segments[0], opNames)
		for i := 1; i < len(segments); i++ {
			result = "(semi " + result + " " + l._ToSexpAmpAndHigher(segments[i], opNames) + ")"
		}
		return result
	}
	return l._ToSexpAmpAndHigher(parts, opNames)
}

func (l *List) _ToSexpAmpAndHigher(parts []interface{}, opNames interface{}) string {
	if len(parts) == 1 {
		return parts[0].ToSexp()
	}
	ampPositions := []interface{}{}
	for i := 1; i < len(parts)-1; i += 2 {
		if parts[i].Kind() == "operator" && parts[i].Op == "&" {
			ampPositions = append(ampPositions, i)
		}
	}
	if len(ampPositions) > 0 {
		segments := []interface{}{}
		start := 0
		for _, pos := range ampPositions {
			segments = append(segments, parts[start:pos])
			start = pos + 1
		}
		segments = append(segments, parts[start:len(parts)])
		result := l._ToSexpAndOr(segments[0], opNames)
		for i := 1; i < len(segments); i++ {
			result = "(background " + result + " " + l._ToSexpAndOr(segments[i], opNames) + ")"
		}
		return result
	}
	return l._ToSexpAndOr(parts, opNames)
}

func (l *List) _ToSexpAndOr(parts []interface{}, opNames interface{}) string {
	if len(parts) == 1 {
		return parts[0].ToSexp()
	}
	result := parts[0].ToSexp()
	for i := 1; i < len(parts)-1; i += 2 {
		op := parts[i]
		cmd := parts[i+1]
		opName := _mapGet(opNames, op.Op, op.Op)
		result = "(" + opName + " " + result + " " + cmd.ToSexp() + ")"
	}
	return result
}

func NewOperator(op string) *Operator {
	o := &Operator{}
	o.Kind = "operator"
	o.Op = op
	return o
}

func (o *Operator) ToSexp() string {
	names := map[string]interface{}{"&&": "and", "||": "or", ";": "semi", "&": "bg", "|": "pipe"}
	return "(" + _mapGet(names, o.Op, o.Op) + ")"
}

func NewPipeBoth() *PipeBoth {
	p := &PipeBoth{}
	p.Kind = "pipe-both"
	return p
}

func (p *PipeBoth) ToSexp() string {
	return "(pipe-both)"
}

func NewEmpty() *Empty {
	e := &Empty{}
	e.Kind = "empty"
	return e
}

func (e *Empty) ToSexp() string {
	return ""
}

func NewComment(text string) *Comment {
	c := &Comment{}
	c.Kind = "comment"
	c.Text = text
	return c
}

func (c *Comment) ToSexp() string {
	return ""
}

func NewRedirect(op string, target Node, fd int) *Redirect {
	r := &Redirect{}
	r.Kind = "redirect"
	r.Op = op
	r.Target = target
	r.Fd = fd
	return r
}

func (r *Redirect) ToSexp() string {
	op := strings.TrimLeft(r.Op, "0123456789")
	if strings.HasPrefix(op, "{") {
		j := 1
		if j < len(op) && unicode.IsLetter(_runeFromChar(op[j])) || op[j] == '_' {
			j += 1
			for j < len(op) && (unicode.IsLetter(_runeFromChar(op[j])) || unicode.IsDigit(_runeFromChar(op[j]))) || op[j] == '_' {
				j += 1
			}
			if j < len(op) && op[j] == '[' {
				j += 1
				for j < len(op) && op[j] != ']' {
					j += 1
				}
				if j < len(op) && op[j] == ']' {
					j += 1
				}
			}
			if j < len(op) && op[j] == '}' {
				op = op[j+1 : len(op)]
			}
		}
	}
	targetVal := r.Target.Value
	targetVal = r.Target._ExpandAllAnsiCQuotes(targetVal)
	targetVal = r.Target._StripLocaleStringDollars(targetVal)
	targetVal = r.Target._FormatCommandSubstitutions(targetVal, false)
	targetVal = r.Target._StripArithLineContinuations(targetVal)
	if strings.HasSuffix(targetVal, "\\") && !(strings.HasSuffix(targetVal, "\\\\")) {
		targetVal = targetVal + "\\"
	}
	if strings.HasPrefix(targetVal, "&") {
		if op == ">" {
			op = ">&"
		} else if op == "<" {
			op = "<&"
		}
		raw := targetVal[1:len(targetVal)]
		if unicode.IsDigit(_runeFromChar(raw)) && _mustAtoi(raw) <= 2147483647 {
			return "(redirect \"" + op + "\" " + fmt.Sprint(_mustAtoi(raw)) + ")"
		}
		if strings.HasSuffix(raw, "-") && unicode.IsDigit(_runeFromChar(raw[0:len(raw)-1])) && _mustAtoi(raw[0:len(raw)-1]) <= 2147483647 {
			return "(redirect \"" + op + "\" " + fmt.Sprint(_mustAtoi(raw[0:len(raw)-1])) + ")"
		}
		if targetVal == "&-" {
			return "(redirect \">&-\" 0)"
		}
		fdTarget := _ternary(strings.HasSuffix(raw, "-"), raw[0:len(raw)-1], raw)
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
		outVal := _ternary(strings.HasSuffix(targetVal, "-"), targetVal[0:len(targetVal)-1], targetVal)
		return "(redirect \"" + op + "\" \"" + outVal + "\")"
	}
	return "(redirect \"" + op + "\" \"" + targetVal + "\")"
}

func NewHereDoc(delimiter string, content string, stripTabs bool, quoted bool, fd int, complete bool) *HereDoc {
	h := &HereDoc{}
	h.Kind = "heredoc"
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
	op := _ternary(h.Strip_tabs, "<<-", "<<")
	content := h.Content
	if strings.HasSuffix(content, "\\") && !(strings.HasSuffix(content, "\\\\")) {
		content = content + "\\"
	}
	return fmt.Sprintf("(redirect \"%v\" \"%v\")", op, content)
}

func NewSubshell(body Node, redirects []interface{}) *Subshell {
	s := &Subshell{}
	s.Kind = "subshell"
	s.Body = body
	s.Redirects = redirects
	return s
}

func (s *Subshell) ToSexp() string {
	base := "(subshell " + s.Body.ToSexp() + ")"
	return _AppendRedirects(base, s.Redirects)
}

func NewBraceGroup(body Node, redirects []interface{}) *BraceGroup {
	b := &BraceGroup{}
	b.Kind = "brace-group"
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
	i.Kind = "if"
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
	result := "(if " + i.Condition.ToSexp() + " " + i.Then_body.ToSexp()
	if i.Else_body {
		result = result + " " + i.Else_body.ToSexp()
	}
	result = result + ")"
	for _, r := range i.Redirects {
		result = result + " " + r.(Node).ToSexp()
	}
	return result
}

func NewWhile(condition Node, body Node, redirects []Node) *While {
	w := &While{}
	w.Kind = "while"
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
	u.Kind = "until"
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

func NewFor(variable string, words []interface{}, body Node, redirects []Node) *For {
	f := &For{}
	f.Kind = "for"
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
	suffix := ""
	if len(f.Redirects) > 0 {
		redirectParts := []string{}
		for _, r := range f.Redirects {
			redirectParts = append(redirectParts, r.(Node).ToSexp())
		}
		suffix = " " + strings.Join(redirectParts, " ")
	}
	tempWord := NewWord(f.Var, []interface{}{})
	varFormatted := tempWord._FormatCommandSubstitutions(f.Var)
	varEscaped := strings.ReplaceAll(strings.ReplaceAll(varFormatted, "\\", "\\\\"), "\"", "\\\"")
	var wordParts []string
	var wordStrs interface{}
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
	f.Kind = "for-arith"
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
	panic("TODO: Statement type FunctionDef")
	suffix := ""
	if len(f.Redirects) > 0 {
		redirectParts := []string{}
		for _, r := range f.Redirects {
			redirectParts = append(redirectParts, r.(Node).ToSexp())
		}
		suffix = " " + strings.Join(redirectParts, " ")
	}
	initVal := _ternary(f.Init, f.Init, "1")
	condVal := _ternary(f.Cond, f.Cond, "1")
	incrVal := _ternary(f.Incr, f.Incr, "1")
	initStr := FormatArithVal(initVal)
	condStr := FormatArithVal(condVal)
	incrStr := FormatArithVal(incrVal)
	bodyStr := f.Body.ToSexp()
	return fmt.Sprintf("(arith-for (init (word \"%v\")) (test (word \"%v\")) (step (word \"%v\")) %v)%v", initStr, condStr, incrStr, bodyStr, suffix)
}

func NewSelect(variable string, words []interface{}, body Node, redirects []Node) *Select {
	s := &Select{}
	s.Kind = "select"
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
	suffix := ""
	if len(s.Redirects) > 0 {
		redirectParts := []string{}
		for _, r := range s.Redirects {
			redirectParts = append(redirectParts, r.(Node).ToSexp())
		}
		suffix = " " + strings.Join(redirectParts, " ")
	}
	varEscaped := strings.ReplaceAll(strings.ReplaceAll(s.Var, "\\", "\\\\"), "\"", "\\\"")
	var wordParts []string
	var wordStrs interface{}
	var inClause string
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
	c.Kind = "case"
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
	c.Kind = "pattern"
	c.Pattern = pattern
	c.Body = body
	c.Terminator = terminator
	return c
}

func (c *CasePattern) ToSexp() string {
	alternatives := []string{}
	current := []interface{}{}
	i := 0
	depth := 0
	for i < len(c.Pattern) {
		ch := c.Pattern[i]
		var result interface{}
		if ch == "\\" && i+1 < len(c.Pattern) {
			current = append(current, c.Pattern[i:i+2])
			i += 2
		} else if ch == "@" || ch == "?" || ch == "*" || ch == "+" || ch == "!" && i+1 < len(c.Pattern) && c.Pattern[i+1] == "(" {
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
			i = result[0]
			current = append(current, result[1]...)
		} else if ch == "'" && depth == 0 {
			result = _ConsumeSingleQuote(c.Pattern, i)
			i = result[0]
			current = append(current, result[1]...)
		} else if ch == "\"" && depth == 0 {
			result = _ConsumeDoubleQuote(c.Pattern, i)
			i = result[0]
			current = append(current, result[1]...)
		} else if ch == "|" && depth == 0 {
			alternatives = append(alternatives, strings.Join(current, ""))
			current = []interface{}{}
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
	parts := []interface{}{"(pattern (" + patternStr + ")"}
	if len(c.Body) > 0 {
		parts = append(parts, " "+c.Body.ToSexp())
	} else {
		parts = append(parts, " ()")
	}
	parts = append(parts, ")")
	return strings.Join(parts, "")
}

func NewFunction(name string, body Node) *Function {
	f := &Function{}
	f.Kind = "function"
	f.Name = name
	f.Body = body
	return f
}

func (f *Function) ToSexp() string {
	return "(function \"" + f.Name + "\" " + f.Body.ToSexp() + ")"
}

func NewParamExpansion(param string, op string, arg string) *ParamExpansion {
	p := &ParamExpansion{}
	p.Kind = "param"
	p.Param = param
	p.Op = op
	p.Arg = arg
	return p
}

func (p *ParamExpansion) ToSexp() string {
	escapedParam := strings.ReplaceAll(strings.ReplaceAll(p.Param, "\\", "\\\\"), "\"", "\\\"")
	if p.Op != nil {
		escapedOp := strings.ReplaceAll(strings.ReplaceAll(p.Op, "\\", "\\\\"), "\"", "\\\"")
		var argVal interface{}
		if p.Arg != nil {
			argVal = p.Arg
		} else {
			argVal = ""
		}
		escapedArg := strings.ReplaceAll(strings.ReplaceAll(argVal, "\\", "\\\\"), "\"", "\\\"")
		return "(param \"" + escapedParam + "\" \"" + escapedOp + "\" \"" + escapedArg + "\")"
	}
	return "(param \"" + escapedParam + "\")"
}

func NewParamLength(param string) *ParamLength {
	p := &ParamLength{}
	p.Kind = "param-len"
	p.Param = param
	return p
}

func (p *ParamLength) ToSexp() string {
	escaped := strings.ReplaceAll(strings.ReplaceAll(p.Param, "\\", "\\\\"), "\"", "\\\"")
	return "(param-len \"" + escaped + "\")"
}

func NewParamIndirect(param string, op string, arg string) *ParamIndirect {
	p := &ParamIndirect{}
	p.Kind = "param-indirect"
	p.Param = param
	p.Op = op
	p.Arg = arg
	return p
}

func (p *ParamIndirect) ToSexp() string {
	escaped := strings.ReplaceAll(strings.ReplaceAll(p.Param, "\\", "\\\\"), "\"", "\\\"")
	if p.Op != nil {
		escapedOp := strings.ReplaceAll(strings.ReplaceAll(p.Op, "\\", "\\\\"), "\"", "\\\"")
		var argVal interface{}
		if p.Arg != nil {
			argVal = p.Arg
		} else {
			argVal = ""
		}
		escapedArg := strings.ReplaceAll(strings.ReplaceAll(argVal, "\\", "\\\\"), "\"", "\\\"")
		return "(param-indirect \"" + escaped + "\" \"" + escapedOp + "\" \"" + escapedArg + "\")"
	}
	return "(param-indirect \"" + escaped + "\")"
}

func NewCommandSubstitution(command Node, brace bool) *CommandSubstitution {
	c := &CommandSubstitution{}
	c.Kind = "cmdsub"
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
	a.Kind = "arith"
	a.Expression = expression
	return a
}

func (a *ArithmeticExpansion) ToSexp() string {
	if a.Expression == nil {
		return "(arith)"
	}
	return "(arith " + a.Expression.ToSexp() + ")"
}

func NewArithmeticCommand(expression Node, redirects []interface{}, rawContent string) *ArithmeticCommand {
	a := &ArithmeticCommand{}
	a.Kind = "arith-cmd"
	a.Expression = expression
	if redirects == nil {
		redirects = []interface{}{}
	}
	a.Redirects = redirects
	a.Raw_content = rawContent
	return a
}

func (a *ArithmeticCommand) ToSexp() string {
	formatted := NewWord(a.Raw_content, nil)._FormatCommandSubstitutions(a.Raw_content)
	escaped := strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(formatted, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n"), "\t", "\\t")
	result := "(arith (word \"" + escaped + "\"))"
	if len(a.Redirects) > 0 {
		redirectParts := []string{}
		for _, r := range a.Redirects {
			redirectParts = append(redirectParts, r.(Node).ToSexp())
		}
		redirectSexps := strings.Join(redirectParts, " ")
		return result + " " + redirectSexps
	}
	return result
}

func NewArithNumber(value string) *ArithNumber {
	a := &ArithNumber{}
	a.Kind = "number"
	a.Value = value
	return a
}

func (a *ArithNumber) ToSexp() string {
	return "(number \"" + a.Value + "\")"
}

func NewArithEmpty() *ArithEmpty {
	a := &ArithEmpty{}
	a.Kind = "empty"
	return a
}

func (a *ArithEmpty) ToSexp() string {
	return "(empty)"
}

func NewArithVar(name string) *ArithVar {
	a := &ArithVar{}
	a.Kind = "var"
	a.Name = name
	return a
}

func (a *ArithVar) ToSexp() string {
	return "(var \"" + a.Name + "\")"
}

func NewArithBinaryOp(op string, left Node, right Node) *ArithBinaryOp {
	a := &ArithBinaryOp{}
	a.Kind = "binary-op"
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
	a.Kind = "unary-op"
	a.Op = op
	a.Operand = operand
	return a
}

func (a *ArithUnaryOp) ToSexp() string {
	return "(unary-op \"" + a.Op + "\" " + a.Operand.ToSexp() + ")"
}

func NewArithPreIncr(operand Node) *ArithPreIncr {
	a := &ArithPreIncr{}
	a.Kind = "pre-incr"
	a.Operand = operand
	return a
}

func (a *ArithPreIncr) ToSexp() string {
	return "(pre-incr " + a.Operand.ToSexp() + ")"
}

func NewArithPostIncr(operand Node) *ArithPostIncr {
	a := &ArithPostIncr{}
	a.Kind = "post-incr"
	a.Operand = operand
	return a
}

func (a *ArithPostIncr) ToSexp() string {
	return "(post-incr " + a.Operand.ToSexp() + ")"
}

func NewArithPreDecr(operand Node) *ArithPreDecr {
	a := &ArithPreDecr{}
	a.Kind = "pre-decr"
	a.Operand = operand
	return a
}

func (a *ArithPreDecr) ToSexp() string {
	return "(pre-decr " + a.Operand.ToSexp() + ")"
}

func NewArithPostDecr(operand Node) *ArithPostDecr {
	a := &ArithPostDecr{}
	a.Kind = "post-decr"
	a.Operand = operand
	return a
}

func (a *ArithPostDecr) ToSexp() string {
	return "(post-decr " + a.Operand.ToSexp() + ")"
}

func NewArithAssign(op string, target Node, value Node) *ArithAssign {
	a := &ArithAssign{}
	a.Kind = "assign"
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
	a.Kind = "ternary"
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
	a.Kind = "comma"
	a.Left = left
	a.Right = right
	return a
}

func (a *ArithComma) ToSexp() string {
	return "(comma " + a.Left.ToSexp() + " " + a.Right.ToSexp() + ")"
}

func NewArithSubscript(array string, index Node) *ArithSubscript {
	a := &ArithSubscript{}
	a.Kind = "subscript"
	a.Array = array
	a.Index = index
	return a
}

func (a *ArithSubscript) ToSexp() string {
	return "(subscript \"" + a.Array + "\" " + a.Index.ToSexp() + ")"
}

func NewArithEscape(char string) *ArithEscape {
	a := &ArithEscape{}
	a.Kind = "escape"
	a.Char = char
	return a
}

func (a *ArithEscape) ToSexp() string {
	return "(escape \"" + a.Char + "\")"
}

func NewArithDeprecated(expression string) *ArithDeprecated {
	a := &ArithDeprecated{}
	a.Kind = "arith-deprecated"
	a.Expression = expression
	return a
}

func (a *ArithDeprecated) ToSexp() string {
	escaped := strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(a.Expression, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n")
	return "(arith-deprecated \"" + escaped + "\")"
}

func NewArithConcat(parts []Node) *ArithConcat {
	a := &ArithConcat{}
	a.Kind = "arith-concat"
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
	a.Kind = "ansi-c"
	a.Content = content
	return a
}

func (a *AnsiCQuote) ToSexp() string {
	escaped := strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(a.Content, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n")
	return "(ansi-c \"" + escaped + "\")"
}

func NewLocaleString(content string) *LocaleString {
	l := &LocaleString{}
	l.Kind = "locale"
	l.Content = content
	return l
}

func (l *LocaleString) ToSexp() string {
	escaped := strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(l.Content, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n")
	return "(locale \"" + escaped + "\")"
}

func NewProcessSubstitution(direction string, command Node) *ProcessSubstitution {
	p := &ProcessSubstitution{}
	p.Kind = "procsub"
	p.Direction = direction
	p.Command = command
	return p
}

func (p *ProcessSubstitution) ToSexp() string {
	return "(procsub \"" + p.Direction + "\" " + p.Command.ToSexp() + ")"
}

func NewNegation(pipeline Node) *Negation {
	n := &Negation{}
	n.Kind = "negation"
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
	t.Kind = "time"
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

func NewConditionalExpr(body interface{}, redirects []interface{}) *ConditionalExpr {
	c := &ConditionalExpr{}
	c.Kind = "cond-expr"
	c.Body = body
	if redirects == nil {
		redirects = []interface{}{}
	}
	c.Redirects = redirects
	return c
}

func (c *ConditionalExpr) ToSexp() string {
	bodyKind := _getattr(c.Body, "kind", nil)
	var escaped interface{}
	var result interface{}
	if bodyKind == nil {
		escaped = strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(c.Body, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n")
		result = "(cond \"" + escaped + "\")"
	} else {
		result = "(cond " + c.Body.ToSexp() + ")"
	}
	if len(c.Redirects) > 0 {
		redirectParts := []string{}
		for _, r := range c.Redirects {
			redirectParts = append(redirectParts, r.(Node).ToSexp())
		}
		redirectSexps := strings.Join(redirectParts, " ")
		return result + " " + redirectSexps
	}
	return result
}

func NewUnaryTest(op string, operand Node) *UnaryTest {
	u := &UnaryTest{}
	u.Kind = "unary-test"
	u.Op = op
	u.Operand = operand
	return u
}

func (u *UnaryTest) ToSexp() string {
	operandVal := u.Operand.GetCondFormattedValue()
	return "(cond-unary \"" + u.Op + "\" (cond-term \"" + operandVal + "\"))"
}

func NewBinaryTest(op string, left Node, right Node) *BinaryTest {
	b := &BinaryTest{}
	b.Kind = "binary-test"
	b.Op = op
	b.Left = left
	b.Right = right
	return b
}

func (b *BinaryTest) ToSexp() string {
	leftVal := b.Left.GetCondFormattedValue()
	rightVal := b.Right.GetCondFormattedValue()
	return "(cond-binary \"" + b.Op + "\" (cond-term \"" + leftVal + "\") (cond-term \"" + rightVal + "\"))"
}

func NewCondAnd(left Node, right Node) *CondAnd {
	c := &CondAnd{}
	c.Kind = "cond-and"
	c.Left = left
	c.Right = right
	return c
}

func (c *CondAnd) ToSexp() string {
	return "(cond-and " + c.Left.ToSexp() + " " + c.Right.ToSexp() + ")"
}

func NewCondOr(left Node, right Node) *CondOr {
	c := &CondOr{}
	c.Kind = "cond-or"
	c.Left = left
	c.Right = right
	return c
}

func (c *CondOr) ToSexp() string {
	return "(cond-or " + c.Left.ToSexp() + " " + c.Right.ToSexp() + ")"
}

func NewCondNot(operand Node) *CondNot {
	c := &CondNot{}
	c.Kind = "cond-not"
	c.Operand = operand
	return c
}

func (c *CondNot) ToSexp() string {
	return c.Operand.ToSexp()
}

func NewCondParen(inner Node) *CondParen {
	c := &CondParen{}
	c.Kind = "cond-paren"
	c.Inner = inner
	return c
}

func (c *CondParen) ToSexp() string {
	return "(cond-expr " + c.Inner.ToSexp() + ")"
}

func NewArray(elements []Node) *Array {
	a := &Array{}
	a.Kind = "array"
	a.Elements = elements
	return a
}

func (a *Array) ToSexp() string {
	if !(a.Elements) {
		return "(array)"
	}
	parts := []string{}
	for _, e := range a.Elements {
		parts = append(parts, e.(Node).ToSexp())
	}
	inner := strings.Join(parts, " ")
	return "(array " + inner + ")"
}

func NewCoproc(command Node, name string) *Coproc {
	c := &Coproc{}
	c.Kind = "coproc"
	c.Command = command
	c.Name = name
	return c
}

func (c *Coproc) ToSexp() string {
	var name interface{}
	if c.Name {
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
	return NewSavedParserState(p._Parser_state, p._Dolbrace_state, append([]interface{}, p._Pending_heredocs...), p._Ctx.CopyStack(), p._Eof_token)
}

func (p *Parser) _RestoreParserState(saved *SavedParserState) {
	p._Parser_state = saved.Parser_state
	p._Dolbrace_state = saved.Dolbrace_state
	p._Eof_token = saved.Eof_token
	p._Ctx.RestoreFrom(saved.Ctx_stack)
}

func (p *Parser) _RecordToken(tok *Token) {
	p._Token_history = []interface{}{tok, p._Token_history[0], p._Token_history[1], p._Token_history[2]}
}

func (p *Parser) _UpdateDolbraceForOp(op string, hasParam bool) {
	if p._Dolbrace_state == DolbraceState_NONE {
		return
	}
	if op == "" || len(op) == 0 {
		return
	}
	firstChar := op[0]
	if p._Dolbrace_state == DolbraceState_PARAM && hasParam {
		if strings.ContainsRune("%#^,", rune(firstChar)) {
			p._Dolbrace_state = DolbraceState_QUOTE
			return
		}
		if firstChar == '/' {
			p._Dolbrace_state = DolbraceState_QUOTE2
			return
		}
	}
	if p._Dolbrace_state == DolbraceState_PARAM {
		if strings.ContainsRune("#%^,~:-=?+/", rune(firstChar)) {
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

func (p *Parser) _LexPeekOperator() (int, interface{}) {
	tok := p._LexPeekToken()
	t := tok.Type
	if t >= TokenType_SEMI && t <= TokenType_GREATER || t >= TokenType_AND_AND && t <= TokenType_PIPE_AMP {
		return t, tok.Value
	}
	return nil
}

func (p *Parser) _LexPeekReservedWord() string {
	tok := p._LexPeekToken()
	if tok.Type != TokenType_WORD {
		return ""
	}
	word := tok.Value
	if strings.HasSuffix(word, "\\\n") {
		word = word[0 : len(word)-2]
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
	tok := p._LexPeekToken()
	if tok.Type != TokenType_WORD {
		return false
	}
	word := tok.Value
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
	return string(p.Source[p.Pos])
}

func (p *Parser) Advance() string {
	if p.AtEnd() {
		return ""
	}
	ch := p.Source[p.Pos]
	p.Pos += 1
	return string(ch)
}

func (p *Parser) PeekAt(offset int) string {
	pos := p.Pos + offset
	if pos < 0 || pos >= p.Length {
		return ""
	}
	return string(p.Source[pos])
}

func (p *Parser) Lookahead(n int) string {
	return p.Source[p.Pos : p.Pos+n]
}

func (p *Parser) _IsBangFollowedByProcsub() bool {
	if p.Pos+2 >= p.Length {
		return false
	}
	nextChar := p.Source[p.Pos+1]
	if nextChar != '>' && nextChar != '<' {
		return false
	}
	return p.Source[p.Pos+2] == '('
}

func (p *Parser) SkipWhitespace() {
	for !(p.AtEnd()) {
		p._LexSkipBlanks()
		if p.AtEnd() {
			break
		}
		ch := p.Peek()
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
	for !(p.AtEnd()) {
		ch := p.Peek()
		if _IsWhitespace(ch) {
			p.Advance()
			if ch == "\n" {
				p._GatherHeredocBodies()
				if p._Cmdsub_heredoc_end != nil && p._Cmdsub_heredoc_end > p.Pos {
					p.Pos = p._Cmdsub_heredoc_end
					p._Cmdsub_heredoc_end = nil
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
		nextPos := p.Pos + 1
		if nextPos >= p.Length {
			return true
		}
		return _IsWordEndContext(p.Source[nextPos])
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

func (p *Parser) _CollectRedirects() []interface{} {
	redirects := []interface{}{}
	for true {
		p.SkipWhitespace()
		redirect := p.ParseRedirect()
		if redirect == nil {
			break
		}
		redirects = append(redirects, redirect)
	}
	return _ternary(len(redirects) > 0, redirects, nil)
}

func (p *Parser) _ParseLoopBody(context string) Node {
	if p.Peek() == "{" {
		brace := p.ParseBraceGroup()
		if brace == nil {
			panic(NewParseError(fmt.Sprintf("Expected brace group body in %v", context), p._LexPeekToken().Pos, 0))
		}
		return brace.Body
	}
	if p._LexConsumeWord("do") {
		body := p.ParseListUntil(map[interface{}]struct{}{"done": {}})
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
	savedPos := p.Pos
	p.SkipWhitespace()
	if p.AtEnd() || _IsMetachar(p.Peek()) {
		p.Pos = savedPos
		return ""
	}
	chars := []interface{}{}
	for !(p.AtEnd()) && !(_IsMetachar(p.Peek())) {
		ch := p.Peek()
		if _IsQuote(ch) {
			break
		}
		if ch == "\\" && p.Pos+1 < p.Length && p.Source[p.Pos+1] == '\n' {
			break
		}
		if ch == "\\" && p.Pos+1 < p.Length {
			chars = append(chars, p.Advance())
			chars = append(chars, p.Advance())
			continue
		}
		chars = append(chars, p.Advance())
	}
	var word interface{}
	if len(chars) > 0 {
		word = strings.Join(chars, "")
	} else {
		word = nil
	}
	p.Pos = savedPos
	return word
}

func (p *Parser) ConsumeWord(expected string) bool {
	savedPos := p.Pos
	p.SkipWhitespace()
	word := p.PeekWord()
	keywordWord := word
	hasLeadingBrace := false
	if word != nil && p._In_process_sub && len(word) > 1 && word[0] == '}' {
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
	for p.Peek() == "\\" && p.Pos+1 < p.Length && p.Source[p.Pos+1] == '\n' {
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
	chars = append(chars, "\"")
	for !(p.AtEnd()) && p.Peek() != "\"" {
		c := p.Peek()
		var nextC byte
		if c == "\\" && p.Pos+1 < p.Length {
			nextC = p.Source[p.Pos+1]
			if handleLineContinuation && nextC == '\n' {
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
	if p.Pos+2 < p.Length && p.Source[p.Pos+1] == '(' && p.Source[p.Pos+2] == '(' {
		result0, result1 := p._ParseArithmeticExpansion()
		if result0 != nil {
			parts = append(parts, result0)
			chars = append(chars, result1)
			return true
		}
		result0, result1 := p._ParseCommandSubstitution()
		if result0 != nil {
			parts = append(parts, result0)
			chars = append(chars, result1)
			return true
		}
		return false
	}
	if p.Pos+1 < p.Length && p.Source[p.Pos+1] == '[' {
		result0, result1 := p._ParseDeprecatedArithmetic()
		if result0 != nil {
			parts = append(parts, result0)
			chars = append(chars, result1)
			return true
		}
		return false
	}
	if p.Pos+1 < p.Length && p.Source[p.Pos+1] == '(' {
		result0, result1 := p._ParseCommandSubstitution()
		if result0 != nil {
			parts = append(parts, result0)
			chars = append(chars, result1)
			return true
		}
		return false
	}
	result0, result1 := p._ParseParamExpansion(inDquote)
	if result0 != nil {
		parts = append(parts, result0)
		chars = append(chars, result1)
		return true
	}
	return false
}

func (p *Parser) _ParseWordInternal(ctx int, atCommandStart bool, inArrayLiteral bool) Node {
	p._Word_context = ctx
	return p.ParseWord(atCommandStart, inArrayLiteral, false)
}

func (p *Parser) ParseWord(atCommandStart bool, inArrayLiteral bool, inAssignBuiltin bool) Node {
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
	return tok.Word
}

func (p *Parser) _ParseCommandSubstitution() (Node, string) {
	if p.AtEnd() || p.Peek() != "$" {
		return nil, ""
	}
	start := p.Pos
	p.Advance()
	if p.AtEnd() || p.Peek() != "(" {
		p.Pos = start
		return nil, ""
	}
	p.Advance()
	saved := p._SaveParserState()
	p._SetState(ParserStateFlags_PST_CMDSUBST | ParserStateFlags_PST_EOFTOKEN)
	p._Eof_token = ")"
	cmd := p.ParseList(true)
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
	textEnd := p.Pos
	text := p.Source[start:textEnd]
	p._RestoreParserState(saved)
	return NewCommandSubstitution(cmd, false), text
}

func (p *Parser) _ParseFunsub(start int) (Node, string) {
	p._SyncParser()
	if !(p.AtEnd()) && p.Peek() == "|" {
		p.Advance()
	}
	saved := p._SaveParserState()
	p._SetState(ParserStateFlags_PST_CMDSUBST | ParserStateFlags_PST_EOFTOKEN)
	p._Eof_token = "}"
	cmd := p.ParseList(true)
	if cmd == nil {
		cmd = NewEmpty()
	}
	p.SkipWhitespaceAndNewlines()
	if p.AtEnd() || p.Peek() != "}" {
		p._RestoreParserState(saved)
		panic(NewMatchedPairError("unexpected EOF looking for `}'", start, 0))
	}
	p.Advance()
	text := p.Source[start:p.Pos]
	p._RestoreParserState(saved)
	p._SyncLexer()
	return NewCommandSubstitution(cmd, true), text
}

func (p *Parser) _IsAssignmentWord(word Node) bool {
	return _Assignment(word.Value, 0) != -1
}

func (p *Parser) _ParseBacktickSubstitution() (Node, string) {
	if p.AtEnd() || p.Peek() != "`" {
		return nil, ""
	}
	start := p.Pos
	p.Advance()
	contentChars := []string{}
	textChars := []string{"`"}
	pendingHeredocs := []interface{}{}
	inHeredocBody := false
	currentHeredocDelim := ""
	currentHeredocStrip := false
	for !(p.AtEnd()) && inHeredocBody || p.Peek() != "`" {
		if inHeredocBody {
			lineStart := p.Pos
			lineEnd := lineStart
			for lineEnd < p.Length && p.Source[lineEnd] != '\n' {
				lineEnd += 1
			}
			line := p.Source[lineStart:lineEnd]
			checkLine := _ternary(currentHeredocStrip, strings.TrimLeft(line, "\t"), line)
			var tabsStripped interface{}
			var endPos interface{}
			if checkLine == currentHeredocDelim {
				for _, ch := range line {
					contentChars = append(contentChars, ch)
					textChars = append(textChars, ch)
				}
				p.Pos = lineEnd
				if p.Pos < p.Length && p.Source[p.Pos] == '\n' {
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
					contentChars = append(contentChars, ch)
					textChars = append(textChars, ch)
				}
				p.Pos = lineEnd
				if p.Pos < p.Length && p.Source[p.Pos] == '\n' {
					contentChars = append(contentChars, "\n")
					textChars = append(textChars, "\n")
					p.Advance()
				}
			}
			continue
		}
		c := p.Peek()
		if c == "\\" && p.Pos+1 < p.Length {
			nextC := p.Source[p.Pos+1]
			var escaped string
			var ch string
			if nextC == '\n' {
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
				contentChars = append(contentChars, ch)
				textChars = append(textChars, ch)
			}
			continue
		}
		if c == "<" && p.Pos+1 < p.Length && p.Source[p.Pos+1] == '<' {
			if p.Pos+2 < p.Length && p.Source[p.Pos+2] == '<' {
				contentChars = append(contentChars, p.Advance())
				textChars = append(textChars, "<")
				contentChars = append(contentChars, p.Advance())
				textChars = append(textChars, "<")
				contentChars = append(contentChars, p.Advance())
				textChars = append(textChars, "<")
				for !(p.AtEnd()) && _IsWhitespaceNoNewline(p.Peek()) {
					ch = p.Advance()
					contentChars = append(contentChars, ch)
					textChars = append(textChars, ch)
				}
				for !(p.AtEnd()) && !(_IsWhitespace(p.Peek())) && !strings.Contains("()", p.Peek()) {
					var quote string
					if p.Peek() == "\\" && p.Pos+1 < p.Length {
						ch = p.Advance()
						contentChars = append(contentChars, ch)
						textChars = append(textChars, ch)
						ch = p.Advance()
						contentChars = append(contentChars, ch)
						textChars = append(textChars, ch)
					} else if strings.Contains("\"'", p.Peek()) {
						quote = p.Peek()
						ch = p.Advance()
						contentChars = append(contentChars, ch)
						textChars = append(textChars, ch)
						for !(p.AtEnd()) && p.Peek() != quote {
							if quote == "\"" && p.Peek() == "\\" {
								ch = p.Advance()
								contentChars = append(contentChars, ch)
								textChars = append(textChars, ch)
							}
							ch = p.Advance()
							contentChars = append(contentChars, ch)
							textChars = append(textChars, ch)
						}
						if !(p.AtEnd()) {
							ch = p.Advance()
							contentChars = append(contentChars, ch)
							textChars = append(textChars, ch)
						}
					} else {
						ch = p.Advance()
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
			if !(p.AtEnd()) && p.Peek() == "-" {
				stripTabs = true
				contentChars = append(contentChars, p.Advance())
				textChars = append(textChars, "-")
			}
			for !(p.AtEnd()) && _IsWhitespaceNoNewline(p.Peek()) {
				ch = p.Advance()
				contentChars = append(contentChars, ch)
				textChars = append(textChars, ch)
			}
			delimiterChars := []string{}
			if !(p.AtEnd()) {
				ch = p.Peek()
				var dch string
				var closing string
				var esc string
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
			delimiter := strings.Join(delimiterChars, "")
			if len(delimiter) > 0 {
				pendingHeredocs = append(pendingHeredocs, []interface{}{delimiter, stripTabs})
			}
			continue
		}
		if c == "\n" {
			ch = p.Advance()
			contentChars = append(contentChars, ch)
			textChars = append(textChars, ch)
			if len(pendingHeredocs) > 0 {
				panic("TODO: incomplete implementation")
			}
			continue
		}
		ch = p.Advance()
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
		heredocStart, heredocEnd := _FindHeredocContentEnd(p.Source, p.Pos, pendingHeredocs)
		if heredocEnd > heredocStart {
			content = content + p.Source[heredocStart:heredocEnd]
			if p._Cmdsub_heredoc_end == nil {
				p._Cmdsub_heredoc_end = heredocEnd
			} else {
				p._Cmdsub_heredoc_end = _max(p._Cmdsub_heredoc_end, heredocEnd)
			}
		}
	}
	subParser := NewParser(content, false, p._Extglob)
	cmd := subParser.ParseList()
	if cmd == nil {
		cmd = NewEmpty()
	}
	return NewCommandSubstitution(cmd, false), text
}

func (p *Parser) _ParseProcessSubstitution() (Node, string) {
	if p.AtEnd() || !(_IsRedirectChar(p.Peek())) {
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
	panic("TODO: try/except")
}

func (p *Parser) _ParseArrayLiteral() (Node, string) {
	if p.AtEnd() || p.Peek() != "(" {
		return nil, ""
	}
	start := p.Pos
	p.Advance()
	p._SetState(ParserStateFlags_PST_COMPASSIGN)
	elements := []interface{}{}
	for true {
		p.SkipWhitespaceAndNewlines()
		if p.AtEnd() {
			p._ClearState(ParserStateFlags_PST_COMPASSIGN)
			panic(NewParseError("Unterminated array literal", start, 0))
		}
		if p.Peek() == ")" {
			break
		}
		word := p.ParseWord(false, true, false)
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
	text := p.Source[start:p.Pos]
	p._ClearState(ParserStateFlags_PST_COMPASSIGN)
	return NewArray(elements), text
}

func (p *Parser) _ParseArithmeticExpansion() (Node, string) {
	if p.AtEnd() || p.Peek() != "$" {
		return nil, ""
	}
	start := p.Pos
	if p.Pos+2 >= p.Length || p.Source[p.Pos+1] != '(' || p.Source[p.Pos+2] != '(' {
		return nil, ""
	}
	p.Advance()
	p.Advance()
	p.Advance()
	contentStart := p.Pos
	depth := 2
	firstClosePos := -1
	for !(p.AtEnd()) && depth > 0 {
		c := p.Peek()
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
				firstClosePos = nil
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
	var content interface{}
	if firstClosePos != -1 {
		content = p.Source[contentStart:firstClosePos]
	} else {
		content = p.Source[contentStart:p.Pos]
	}
	p.Advance()
	text := p.Source[start:p.Pos]
	panic("TODO: try/except")
	return NewArithmeticExpansion(expr), text
}

func (p *Parser) _ParseArithExpr(content string) Node {
	savedArithSrc := _getattr(p, "_arith_src", nil)
	savedArithPos := _getattr(p, "_arith_pos", nil)
	savedArithLen := _getattr(p, "_arith_len", nil)
	savedParserState := p._Parser_state
	p._SetState(ParserStateFlags_PST_ARITH)
	p._Arith_src = content
	p._Arith_pos = 0
	p._Arith_len = len(content)
	p._ArithSkipWs()
	var result interface{}
	if p._ArithAtEnd() {
		result = nil
	} else {
		result = p._ArithParseComma()
	}
	p._Parser_state = savedParserState
	if savedArithSrc != nil {
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
	return p._Arith_src[pos]
}

func (p *Parser) _ArithAdvance() string {
	if p._ArithAtEnd() {
		return ""
	}
	c := p._Arith_src[p._Arith_pos]
	p._Arith_pos += 1
	return c
}

func (p *Parser) _ArithSkipWs() {
	for !(p._ArithAtEnd()) {
		c := p._Arith_src[p._Arith_pos]
		if _IsWhitespace(c) {
			p._Arith_pos += 1
		} else if c == "\\" && p._Arith_pos+1 < p._Arith_len && p._Arith_src[p._Arith_pos+1] == "\n" {
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
	left := p._ArithParseAssign()
	for true {
		p._ArithSkipWs()
		var right Node
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
			right := p._ArithParseAssign()
			return NewArithAssign(op, left, right)
		}
	}
	return left
}

func (p *Parser) _ArithParseTernary() Node {
	cond := p._ArithParseLogicalOr()
	p._ArithSkipWs()
	if p._ArithConsume("?") {
		p._ArithSkipWs()
		var ifTrue interface{}
		if p._ArithMatch(":") {
			ifTrue = nil
		} else {
			ifTrue = p._ArithParseAssign()
		}
		p._ArithSkipWs()
		var ifFalse Node
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

func (p *Parser) _ArithParseLeftAssoc(ops []interface{}, parsefn interface{}) Node {
	left := Parsefn()
	for true {
		p._ArithSkipWs()
		matched := false
		for _, op := range ops {
			if p._ArithMatch(op) {
				p._ArithConsume(op)
				p._ArithSkipWs()
				left = NewArithBinaryOp(op, left, Parsefn())
				matched = true
				break
			}
		}
		if !(matched) {
			break
		}
	}
	return left
}

func (p *Parser) _ArithParseLogicalOr() Node {
	return p._ArithParseLeftAssoc([]string{"||"}, p._Arith_parse_logical_and)
}

func (p *Parser) _ArithParseLogicalAnd() Node {
	return p._ArithParseLeftAssoc([]string{"&&"}, p._Arith_parse_bitwise_or)
}

func (p *Parser) _ArithParseBitwiseOr() Node {
	left := p._ArithParseBitwiseXor()
	for true {
		p._ArithSkipWs()
		var right Node
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
	left := p._ArithParseBitwiseAnd()
	for true {
		p._ArithSkipWs()
		var right Node
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
	left := p._ArithParseEquality()
	for true {
		p._ArithSkipWs()
		var right Node
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
	return p._ArithParseLeftAssoc([]string{"==", "!="}, p._Arith_parse_comparison)
}

func (p *Parser) _ArithParseComparison() Node {
	left := p._ArithParseShift()
	for true {
		p._ArithSkipWs()
		var right Node
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
	left := p._ArithParseAdditive()
	for true {
		p._ArithSkipWs()
		if p._ArithMatch("<<=") {
			break
		}
		if p._ArithMatch(">>=") {
			break
		}
		var right Node
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
	left := p._ArithParseMultiplicative()
	for true {
		p._ArithSkipWs()
		c := p._ArithPeek(0)
		c2 := p._ArithPeek(1)
		var right Node
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
	left := p._ArithParseExponentiation()
	for true {
		p._ArithSkipWs()
		c := p._ArithPeek(0)
		c2 := p._ArithPeek(1)
		var right Node
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
	left := p._ArithParseUnary()
	p._ArithSkipWs()
	if p._ArithMatch("**") {
		p._ArithConsume("**")
		p._ArithSkipWs()
		right := p._ArithParseExponentiation()
		return NewArithBinaryOp("**", left, right)
	}
	return left
}

func (p *Parser) _ArithParseUnary() Node {
	p._ArithSkipWs()
	if p._ArithMatch("++") {
		p._ArithConsume("++")
		p._ArithSkipWs()
		operand := p._ArithParseUnary()
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
	left := p._ArithParsePrimary()
	for true {
		p._ArithSkipWs()
		var index Node
		if p._ArithMatch("++") {
			p._ArithConsume("++")
			left = NewArithPostIncr(left)
		} else if p._ArithMatch("--") {
			p._ArithConsume("--")
			left = NewArithPostDecr(left)
		} else if p._ArithPeek(0) == "[" {
			if left.Kind() == "var" {
				p._ArithAdvance()
				p._ArithSkipWs()
				index = p._ArithParseComma()
				p._ArithSkipWs()
				if !(p._ArithConsume("]")) {
					panic(NewParseError("Expected ']' in array subscript", p._Arith_pos, 0))
				}
				left = NewArithSubscript(left.Name, index)
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
	p._ArithSkipWs()
	c := p._ArithPeek(0)
	if c == "(" {
		p._ArithAdvance()
		p._ArithSkipWs()
		expr := p._ArithParseComma()
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
		escapedChar := p._ArithAdvance()
		return NewArithEscape(escapedChar)
	}
	if p._ArithAtEnd() || strings.Contains(")]:,;?|&<>=!+-*/%^~#{}", c) {
		return NewArithEmpty()
	}
	return p._ArithParseNumberOrVar()
}

func (p *Parser) _ArithParseExpansion() Node {
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
	nameChars := []interface{}{}
	for !(p._ArithAtEnd()) {
		ch := p._ArithPeek(0)
		if (unicode.IsLetter(_runeFromChar(ch)) || unicode.IsDigit(_runeFromChar(ch))) || ch == "_" {
			nameChars = append(nameChars, p._ArithAdvance())
		} else if _IsSpecialParamOrDigit(ch) || ch == "#" && !(len(nameChars) > 0) {
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
	p._ArithAdvance()
	if p._ArithPeek(0) == "(" {
		p._ArithAdvance()
		depth := 1
		contentStart := p._Arith_pos
		for !(p._ArithAtEnd()) && depth > 0 {
			ch := p._ArithPeek(0)
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
		content := p._Arith_src[contentStart:p._Arith_pos]
		p._ArithAdvance()
		p._ArithAdvance()
		innerExpr := p._ParseArithExpr(content)
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
	subParser := NewParser(content, false, p._Extglob)
	cmd := subParser.ParseList()
	return NewCommandSubstitution(cmd, false)
}

func (p *Parser) _ArithParseBracedParam() Node {
	p._ArithAdvance()
	if p._ArithPeek(0) == "!" {
		p._ArithAdvance()
		nameChars := []interface{}{}
		for !(p._ArithAtEnd()) && p._ArithPeek(0) != "}" {
			nameChars = append(nameChars, p._ArithAdvance())
		}
		p._ArithConsume("}")
		return NewParamIndirect(strings.Join(nameChars, ""), "", "")
	}
	if p._ArithPeek(0) == "#" {
		p._ArithAdvance()
		nameChars = []interface{}{}
		for !(p._ArithAtEnd()) && p._ArithPeek(0) != "}" {
			nameChars = append(nameChars, p._ArithAdvance())
		}
		p._ArithConsume("}")
		return NewParamLength(strings.Join(nameChars, ""))
	}
	nameChars = []interface{}{}
	for !(p._ArithAtEnd()) {
		ch := p._ArithPeek(0)
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
	opChars := []interface{}{}
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
	p._ArithAdvance()
	contentStart := p._Arith_pos
	for !(p._ArithAtEnd()) && p._ArithPeek(0) != "'" {
		p._ArithAdvance()
	}
	content := p._Arith_src[contentStart:p._Arith_pos]
	if !(p._ArithConsume("'")) {
		panic(NewParseError("Unterminated single quote in arithmetic", p._Arith_pos, 0))
	}
	return NewArithNumber(content)
}

func (p *Parser) _ArithParseDoubleQuote() Node {
	p._ArithAdvance()
	contentStart := p._Arith_pos
	for !(p._ArithAtEnd()) && p._ArithPeek(0) != "\"" {
		c := p._ArithPeek(0)
		if c == "\\" && !(p._ArithAtEnd()) {
			p._ArithAdvance()
			p._ArithAdvance()
		} else {
			p._ArithAdvance()
		}
	}
	content := p._Arith_src[contentStart:p._Arith_pos]
	if !(p._ArithConsume("\"")) {
		panic(NewParseError("Unterminated double quote in arithmetic", p._Arith_pos, 0))
	}
	return NewArithNumber(content)
}

func (p *Parser) _ArithParseBacktick() Node {
	p._ArithAdvance()
	contentStart := p._Arith_pos
	for !(p._ArithAtEnd()) && p._ArithPeek(0) != "`" {
		c := p._ArithPeek(0)
		if c == "\\" && !(p._ArithAtEnd()) {
			p._ArithAdvance()
			p._ArithAdvance()
		} else {
			p._ArithAdvance()
		}
	}
	content := p._Arith_src[contentStart:p._Arith_pos]
	if !(p._ArithConsume("`")) {
		panic(NewParseError("Unterminated backtick in arithmetic", p._Arith_pos, 0))
	}
	subParser := NewParser(content, false, p._Extglob)
	cmd := subParser.ParseList()
	return NewCommandSubstitution(cmd, false)
}

func (p *Parser) _ArithParseNumberOrVar() Node {
	p._ArithSkipWs()
	chars := []interface{}{}
	c := p._ArithPeek(0)
	if unicode.IsDigit(_runeFromChar(c)) {
		for !(p._ArithAtEnd()) {
			ch := p._ArithPeek(0)
			if (unicode.IsLetter(_runeFromChar(ch)) || unicode.IsDigit(_runeFromChar(ch))) || ch == "#" || ch == "_" {
				chars = append(chars, p._ArithAdvance())
			} else {
				break
			}
		}
		prefix := strings.Join(chars, "")
		if !(p._ArithAtEnd()) && p._ArithPeek(0) == "$" {
			expansion := p._ArithParseExpansion()
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
	if p.Pos+1 >= p.Length || p.Source[p.Pos+1] != '[' {
		return nil, ""
	}
	p.Advance()
	p.Advance()
	p._Lexer.Pos = p.Pos
	content := p._Lexer._ParseMatchedPair("[", "]", MatchedPairFlags_ARITH)
	p.Pos = p._Lexer.Pos
	text := p.Source[start:p.Pos]
	return NewArithDeprecated(content), text
}

func (p *Parser) _ParseParamExpansion(inDquote bool) (Node, string) {
	p._SyncLexer()
	result0, result1 := p._Lexer._ReadParamExpansion(inDquote)
	p._SyncParser()
	return result
}

func (p *Parser) ParseRedirect() interface{} {
	p.SkipWhitespace()
	if p.AtEnd() {
		return nil
	}
	start := p.Pos
	fd := nil
	varfd := nil
	if p.Peek() == "{" {
		saved := p.Pos
		p.Advance()
		varnameChars := []interface{}{}
		inBracket := false
		for !(p.AtEnd()) && !(_IsRedirectChar(p.Peek())) {
			ch := p.Peek()
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
		varname := strings.Join(varnameChars, "")
		isValidVarfd := false
		if varname {
			if unicode.IsLetter(_runeFromChar(varname[0])) || varname[0] == "_" {
				var left interface{}
				var right interface{}
				var base interface{}
				if _contains(varname, "[") || _contains(varname, "]") {
					left = strings.Index(varname, "[")
					right = strings.LastIndex(varname, "]")
					if left != -1 && right == len(varname)-1 && right > left+1 {
						base = varname[0:left]
						if base && unicode.IsLetter(_runeFromChar(base[0])) || base[0] == "_" {
							isValidVarfd = true
							for _, c := range base[1:] {
								if !((unicode.IsLetter(_runeFromChar(c)) || unicode.IsDigit(_runeFromChar(c))) || c == "_") {
									isValidVarfd = false
									break
								}
							}
						}
					}
				} else {
					isValidVarfd = true
					for _, c := range varname[1:] {
						if !((unicode.IsLetter(_runeFromChar(c)) || unicode.IsDigit(_runeFromChar(c))) || c == "_") {
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
	if varfd == nil && p.Peek() && unicode.IsDigit(_runeFromChar(p.Peek())) {
		fdChars := []interface{}{}
		for !(p.AtEnd()) && unicode.IsDigit(_runeFromChar(p.Peek())) {
			fdChars = append(fdChars, p.Advance())
		}
		fd = _mustAtoi(strings.Join(fdChars, ""))
	}
	ch = p.Peek()
	if ch == "&" && p.Pos+1 < p.Length && p.Source[p.Pos+1] == '>' {
		if fd != nil || varfd != nil {
			p.Pos = start
			return nil
		}
		p.Advance()
		p.Advance()
		var op string
		if !(p.AtEnd()) && p.Peek() == ">" {
			p.Advance()
			op = "&>>"
		} else {
			op = "&>"
		}
		p.SkipWhitespace()
		target := p.ParseWord(false, false, false)
		if target == nil {
			panic(NewParseError("Expected target for redirect "+op, p.Pos, 0))
		}
		return NewRedirect(op, target, 0)
	}
	if ch == "" || !(_IsRedirectChar(ch)) {
		p.Pos = start
		return nil
	}
	if fd == nil && p.Pos+1 < p.Length && p.Source[p.Pos+1] == '(' {
		p.Pos = start
		return nil
	}
	op = p.Advance()
	stripTabs := false
	if !(p.AtEnd()) {
		nextCh := p.Peek()
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
		} else if fd == nil && varfd == nil && op == ">" && nextCh == "&" {
			if p.Pos+1 >= p.Length || !(_IsDigitOrDash(p.Source[p.Pos+1])) {
				p.Advance()
				op = ">&"
			}
		} else if fd == nil && varfd == nil && op == "<" && nextCh == "&" {
			if p.Pos+1 >= p.Length || !(_IsDigitOrDash(p.Source[p.Pos+1])) {
				p.Advance()
				op = "<&"
			}
		}
	}
	if op == "<<" {
		return p._ParseHeredoc(fd, stripTabs)
	}
	if varfd != nil {
		op = "{" + varfd + "}" + op
	} else if fd != nil {
		op = fmt.Sprint(fd) + op
	}
	var wordStart int
	var fdTarget string
	var innerWord Node
	if !(p.AtEnd()) && p.Peek() == "&" {
		p.Advance()
		p.SkipWhitespace()
		if !(p.AtEnd()) && p.Peek() == "-" {
			if p.Pos+1 < p.Length && !(_IsMetachar(string(p.Source[p.Pos+1]))) {
				p.Advance()
				target = NewWord("&-", nil)
			} else {
				target = nil
			}
		} else {
			target = nil
		}
		if target == nil {
			if !(p.AtEnd()) && unicode.IsDigit(_runeFromChar(p.Peek())) || p.Peek() == "-" {
				wordStart = p.Pos
				fdChars = []interface{}{}
				for !(p.AtEnd()) && unicode.IsDigit(_runeFromChar(p.Peek())) {
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
			if p.Pos+1 < p.Length && !(_IsMetachar(string(p.Source[p.Pos+1]))) {
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
	p.SkipWhitespace()
	quoted := false
	delimiterChars := []string{}
	for true {
		for !(p.AtEnd()) && !(_IsMetachar(p.Peek())) {
			ch := p.Peek()
			var c string
			var nextCh string
			var esc string
			var escVal interface{}
			var depth int
			var dollarCount int
			var j int
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
			} else if ch == "$" && p.Pos+1 < p.Length && p.Source[p.Pos+1] == '\'' {
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
			} else if ch == "$" && p.Pos+1 < p.Length && p.Source[p.Pos+1] == '{' {
				dollarCount = 0
				j = p.Pos - 1
				for j >= 0 && p.Source[j] == '$' {
					dollarCount += 1
					j -= 1
				}
				if j >= 0 && p.Source[j] == '\\' {
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
			} else if ch == "$" && p.Pos+1 < p.Length && p.Source[p.Pos+1] == '[' {
				dollarCount = 0
				j = p.Pos - 1
				for j >= 0 && p.Source[j] == '$' {
					dollarCount += 1
					j -= 1
				}
				if j >= 0 && p.Source[j] == '\\' {
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
		if !(p.AtEnd()) && strings.Contains("<>", p.Peek()) && p.Pos+1 < p.Length && p.Source[p.Pos+1] == '(' {
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
	lineStart := p.Pos
	lineEnd := p.Pos
	for lineEnd < p.Length && p.Source[lineEnd] != '\n' {
		lineEnd += 1
	}
	line := p.Source[lineStart:lineEnd]
	if !(quoted) {
		for lineEnd < p.Length {
			trailingBs := _CountTrailingBackslashes(line)
			if trailingBs%2 == 0 {
				break
			}
			line = line[0 : len(line)-1]
			lineEnd += 1
			nextLineStart := lineEnd
			for lineEnd < p.Length && p.Source[lineEnd] != '\n' {
				lineEnd += 1
			}
			line = line + p.Source[nextLineStart:lineEnd]
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
	for _, heredoc := range p._Pending_heredocs {
		contentLines := []string{}
		lineStart := p.Pos
		for p.Pos < p.Length {
			lineStart = p.Pos
			line, lineEnd := p._ReadHeredocLine(heredoc.Quoted)
			matches, checkLine := p._LineMatchesDelimiter(line, heredoc.Delimiter, heredoc.Strip_tabs)
			if matches {
				p.Pos = _ternary(lineEnd < p.Length, lineEnd+1, lineEnd)
				break
			}
			normalizedCheck := _NormalizeHeredocDelimiter(checkLine)
			normalizedDelim := _NormalizeHeredocDelimiter(heredoc.Delimiter)
			if p._Eof_token == ")" && strings.HasPrefix(normalizedCheck, normalizedDelim) {
				tabsStripped := len(line) - len(checkLine)
				p.Pos = lineStart + tabsStripped + len(heredoc.Delimiter)
				break
			}
			if lineEnd >= p.Length && strings.HasPrefix(normalizedCheck, normalizedDelim) && p._In_process_sub {
				tabsStripped = len(line) - len(checkLine)
				p.Pos = lineStart + tabsStripped + len(heredoc.Delimiter)
				break
			}
			if heredoc.Strip_tabs {
				line = strings.TrimLeft(line, "\t")
			}
			var addNewline bool
			if lineEnd < p.Length {
				contentLines = append(contentLines, line+"\n")
				p.Pos = lineEnd + 1
			} else {
				addNewline = true
				if !(heredoc.Quoted) && _CountTrailingBackslashes(line)%2 == 1 {
					addNewline = false
				}
				contentLines = append(contentLines, line+_ternary(addNewline, "\n", ""))
				p.Pos = p.Length
			}
		}
		heredoc.Content = strings.Join(contentLines, "")
	}
	p._Pending_heredocs = []interface{}{}
}

func (p *Parser) _ParseHeredoc(fd int, stripTabs bool) Node {
	startPos := p.Pos
	p._SetState(ParserStateFlags_PST_HEREDOC)
	delimiter, quoted := p._ParseHeredocDelimiter()
	for _, existing := range p._Pending_heredocs {
		if existing._Start_pos == startPos && existing.Delimiter == delimiter {
			p._ClearState(ParserStateFlags_PST_HEREDOC)
			return existing
		}
	}
	heredoc := NewHereDoc(delimiter, "", stripTabs, quoted, fd, false)
	heredoc._Start_pos = startPos
	p._Pending_heredocs = append(p._Pending_heredocs, heredoc)
	p._ClearState(ParserStateFlags_PST_HEREDOC)
	return heredoc
}

func (p *Parser) ParseCommand() Node {
	words := []interface{}{}
	redirects := []interface{}{}
	for true {
		p.SkipWhitespace()
		if p._LexIsCommandTerminator() {
			break
		}
		if len(words) == 0 {
			reserved := p._LexPeekReservedWord()
			if reserved == "}" || reserved == "]]" {
				break
			}
		}
		redirect := p.ParseRedirect()
		if redirect != nil {
			redirects = append(redirects, redirect)
			continue
		}
		allAssignments := true
		for _, w := range words {
			if !(p._IsAssignmentWord(w)) {
				allAssignments = false
				break
			}
		}
		inAssignBuiltin := len(words) > 0 && AssignmentBuiltins[words[0].Value]
		word := p.ParseWord(!(len(words) > 0) || allAssignments && len(redirects) == 0, false, inAssignBuiltin)
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

func (p *Parser) ParseSubshell() Node {
	p.SkipWhitespace()
	if p.AtEnd() || p.Peek() != "(" {
		return nil
	}
	p.Advance()
	p._SetState(ParserStateFlags_PST_SUBSHELL)
	body := p.ParseList(true)
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

func (p *Parser) ParseArithmeticCommand() Node {
	p.SkipWhitespace()
	if p.AtEnd() || p.Peek() != "(" || p.Pos+1 >= p.Length || p.Source[p.Pos+1] != '(' {
		return nil
	}
	savedPos := p.Pos
	p.Advance()
	p.Advance()
	contentStart := p.Pos
	depth := 1
	for !(p.AtEnd()) && depth > 0 {
		c := p.Peek()
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
			if depth == 1 && p.Pos+1 < p.Length && p.Source[p.Pos+1] == ')' {
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
	content := p.Source[contentStart:p.Pos]
	content = strings.ReplaceAll(content, "\\\n", "")
	p.Advance()
	p.Advance()
	expr := p._ParseArithExpr(content)
	return NewArithmeticCommand(expr, p._CollectRedirects(), content)
}

func (p *Parser) ParseConditionalExpr() Node {
	p.SkipWhitespace()
	if p.AtEnd() || p.Peek() != "[" || p.Pos+1 >= p.Length || p.Source[p.Pos+1] != '[' {
		return nil
	}
	nextPos := p.Pos + 2
	if nextPos < p.Length && !(_IsWhitespace(string(p.Source[nextPos])) || p.Source[nextPos] == '\\' && nextPos+1 < p.Length && p.Source[nextPos+1] == '\n') {
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
	if p.AtEnd() || p.Peek() != "]" || p.Pos+1 >= p.Length || p.Source[p.Pos+1] != ']' {
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
		} else if p.Peek() == "\\" && p.Pos+1 < p.Length && p.Source[p.Pos+1] == '\n' {
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
	return p.AtEnd() || p.Peek() == "]" && p.Pos+1 < p.Length && p.Source[p.Pos+1] == ']'
}

func (p *Parser) _ParseCondOr() Node {
	p._CondSkipWhitespace()
	left := p._ParseCondAnd()
	p._CondSkipWhitespace()
	if !(p._CondAtEnd()) && p.Peek() == "|" && p.Pos+1 < p.Length && p.Source[p.Pos+1] == '|' {
		p.Advance()
		p.Advance()
		right := p._ParseCondOr()
		return NewCondOr(left, right)
	}
	return left
}

func (p *Parser) _ParseCondAnd() Node {
	p._CondSkipWhitespace()
	left := p._ParseCondTerm()
	p._CondSkipWhitespace()
	if !(p._CondAtEnd()) && p.Peek() == "&" && p.Pos+1 < p.Length && p.Source[p.Pos+1] == '&' {
		p.Advance()
		p.Advance()
		right := p._ParseCondAnd()
		return NewCondAnd(left, right)
	}
	return left
}

func (p *Parser) _ParseCondTerm() Node {
	p._CondSkipWhitespace()
	if p._CondAtEnd() {
		panic(NewParseError("Unexpected end of conditional expression", p.Pos, 0))
	}
	if p.Peek() == "!" {
		var operand Node
		if p.Pos+1 < p.Length && !(_IsWhitespaceNoNewline(string(p.Source[p.Pos+1]))) {
		} else {
			p.Advance()
			operand = p._ParseCondTerm()
			return NewCondNot(operand)
		}
	}
	if p.Peek() == "(" {
		p.Advance()
		inner := p._ParseCondOr()
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
		if operand == nil {
			panic(NewParseError("Expected operand after "+word1.Value, p.Pos, 0))
		}
		return NewUnaryTest(word1.Value, operand)
	}
	if !(p._CondAtEnd()) && p.Peek() != "&" && p.Peek() != "|" && p.Peek() != ")" {
		if _IsRedirectChar(p.Peek()) && !(p.Pos+1 < p.Length && p.Source[p.Pos+1] == '(') {
			op := p.Advance()
			p._CondSkipWhitespace()
			word2 := p._ParseCondWord()
			if word2 == nil {
				panic(NewParseError("Expected operand after "+op, p.Pos, 0))
			}
			return NewBinaryTest(op, word1, word2)
		}
		savedPos := p.Pos
		opWord := p._ParseCondWord()
		if opWord && CondBinaryOps[opWord.Value] {
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

func (p *Parser) _ParseCondWord() Node {
	p._CondSkipWhitespace()
	if p._CondAtEnd() {
		return nil
	}
	c := p.Peek()
	if _IsParen(c) {
		return nil
	}
	if c == "&" && p.Pos+1 < p.Length && p.Source[p.Pos+1] == '&' {
		return nil
	}
	if c == "|" && p.Pos+1 < p.Length && p.Source[p.Pos+1] == '|' {
		return nil
	}
	return p._ParseWordInternal(WordCtxCond, false, false)
}

func (p *Parser) _ParseCondRegexWord() Node {
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

func (p *Parser) ParseBraceGroup() Node {
	p.SkipWhitespace()
	if !(p._LexConsumeWord("{")) {
		return nil
	}
	p.SkipWhitespaceAndNewlines()
	body := p.ParseList(true)
	if body == nil {
		panic(NewParseError("Expected command in brace group", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespace()
	if !(p._LexConsumeWord("}")) {
		panic(NewParseError("Expected } to close brace group", p._LexPeekToken().Pos, 0))
	}
	return NewBraceGroup(body, p._CollectRedirects())
}

func (p *Parser) ParseIf() Node {
	p.SkipWhitespace()
	if !(p._LexConsumeWord("if")) {
		return nil
	}
	condition := p.ParseListUntil(map[interface{}]struct{}{"then": {}})
	if condition == nil {
		panic(NewParseError("Expected condition after 'if'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("then")) {
		panic(NewParseError("Expected 'then' after if condition", p._LexPeekToken().Pos, 0))
	}
	thenBody := p.ParseListUntil(map[interface{}]struct{}{"elif": {}, "else": {}, "fi": {}})
	if thenBody == nil {
		panic(NewParseError("Expected commands after 'then'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	elseBody := nil
	var elifCondition Node
	var elifThenBody Node
	var innerElse Node
	if p._LexIsAtReservedWord("elif") {
		p._LexConsumeWord("elif")
		elifCondition = p.ParseListUntil(map[interface{}]struct{}{"then": {}})
		if elifCondition == nil {
			panic(NewParseError("Expected condition after 'elif'", p._LexPeekToken().Pos, 0))
		}
		p.SkipWhitespaceAndNewlines()
		if !(p._LexConsumeWord("then")) {
			panic(NewParseError("Expected 'then' after elif condition", p._LexPeekToken().Pos, 0))
		}
		elifThenBody = p.ParseListUntil(map[interface{}]struct{}{"elif": {}, "else": {}, "fi": {}})
		if elifThenBody == nil {
			panic(NewParseError("Expected commands after 'then'", p._LexPeekToken().Pos, 0))
		}
		p.SkipWhitespaceAndNewlines()
		innerElse = nil
		if p._LexIsAtReservedWord("elif") {
			innerElse = p._ParseElifChain()
		} else if p._LexIsAtReservedWord("else") {
			p._LexConsumeWord("else")
			innerElse = p.ParseListUntil(map[interface{}]struct{}{"fi": {}})
			if innerElse == nil {
				panic(NewParseError("Expected commands after 'else'", p._LexPeekToken().Pos, 0))
			}
		}
		elseBody = NewIf(elifCondition, elifThenBody, innerElse, nil)
	} else if p._LexIsAtReservedWord("else") {
		p._LexConsumeWord("else")
		elseBody = p.ParseListUntil(map[interface{}]struct{}{"fi": {}})
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

func (p *Parser) _ParseElifChain() Node {
	p._LexConsumeWord("elif")
	condition := p.ParseListUntil(map[interface{}]struct{}{"then": {}})
	if condition == nil {
		panic(NewParseError("Expected condition after 'elif'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("then")) {
		panic(NewParseError("Expected 'then' after elif condition", p._LexPeekToken().Pos, 0))
	}
	thenBody := p.ParseListUntil(map[interface{}]struct{}{"elif": {}, "else": {}, "fi": {}})
	if thenBody == nil {
		panic(NewParseError("Expected commands after 'then'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	elseBody := nil
	if p._LexIsAtReservedWord("elif") {
		elseBody = p._ParseElifChain()
	} else if p._LexIsAtReservedWord("else") {
		p._LexConsumeWord("else")
		elseBody = p.ParseListUntil(map[interface{}]struct{}{"fi": {}})
		if elseBody == nil {
			panic(NewParseError("Expected commands after 'else'", p._LexPeekToken().Pos, 0))
		}
	}
	return NewIf(condition, thenBody, elseBody, nil)
}

func (p *Parser) ParseWhile() Node {
	p.SkipWhitespace()
	if !(p._LexConsumeWord("while")) {
		return nil
	}
	condition := p.ParseListUntil(map[interface{}]struct{}{"do": {}})
	if condition == nil {
		panic(NewParseError("Expected condition after 'while'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("do")) {
		panic(NewParseError("Expected 'do' after while condition", p._LexPeekToken().Pos, 0))
	}
	body := p.ParseListUntil(map[interface{}]struct{}{"done": {}})
	if body == nil {
		panic(NewParseError("Expected commands after 'do'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("done")) {
		panic(NewParseError("Expected 'done' to close while loop", p._LexPeekToken().Pos, 0))
	}
	return NewWhile(condition, body, p._CollectRedirects())
}

func (p *Parser) ParseUntil() Node {
	p.SkipWhitespace()
	if !(p._LexConsumeWord("until")) {
		return nil
	}
	condition := p.ParseListUntil(map[interface{}]struct{}{"do": {}})
	if condition == nil {
		panic(NewParseError("Expected condition after 'until'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("do")) {
		panic(NewParseError("Expected 'do' after until condition", p._LexPeekToken().Pos, 0))
	}
	body := p.ParseListUntil(map[interface{}]struct{}{"done": {}})
	if body == nil {
		panic(NewParseError("Expected commands after 'do'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("done")) {
		panic(NewParseError("Expected 'done' to close until loop", p._LexPeekToken().Pos, 0))
	}
	return NewUntil(condition, body, p._CollectRedirects())
}

func (p *Parser) ParseFor() interface{} {
	p.SkipWhitespace()
	if !(p._LexConsumeWord("for")) {
		return nil
	}
	p.SkipWhitespace()
	if p.Peek() == "(" && p.Pos+1 < p.Length && p.Source[p.Pos+1] == '(' {
		return p._ParseForArith()
	}
	var varWord Node
	var varName interface{}
	if p.Peek() == "$" {
		varWord = p.ParseWord(false, false, false)
		if varWord == nil {
			panic(NewParseError("Expected variable name after 'for'", p._LexPeekToken().Pos, 0))
		}
		varName = varWord.Value
	} else {
		varName = p.PeekWord()
		if varName == nil {
			panic(NewParseError("Expected variable name after 'for'", p._LexPeekToken().Pos, 0))
		}
		p.ConsumeWord(varName)
	}
	p.SkipWhitespace()
	if p.Peek() == ";" {
		p.Advance()
	}
	p.SkipWhitespaceAndNewlines()
	words := nil
	if p._LexIsAtReservedWord("in") {
		p._LexConsumeWord("in")
		p.SkipWhitespace()
		sawDelimiter := _IsSemicolonOrNewline(p.Peek())
		if p.Peek() == ";" {
			p.Advance()
		}
		p.SkipWhitespaceAndNewlines()
		words = []interface{}{}
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
			word := p.ParseWord(false, false, false)
			if word == nil {
				break
			}
			words = append(words, word)
		}
	}
	p.SkipWhitespaceAndNewlines()
	if p.Peek() == "{" {
		braceGroup := p.ParseBraceGroup()
		if braceGroup == nil {
			panic(NewParseError("Expected brace group in for loop", p._LexPeekToken().Pos, 0))
		}
		return NewFor(varName, words, braceGroup.Body, p._CollectRedirects())
	}
	if !(p._LexConsumeWord("do")) {
		panic(NewParseError("Expected 'do' in for loop", p._LexPeekToken().Pos, 0))
	}
	body := p.ParseListUntil(map[interface{}]struct{}{"done": {}})
	if body == nil {
		panic(NewParseError("Expected commands after 'do'", p._LexPeekToken().Pos, 0))
	}
	p.SkipWhitespaceAndNewlines()
	if !(p._LexConsumeWord("done")) {
		panic(NewParseError("Expected 'done' to close for loop", p._LexPeekToken().Pos, 0))
	}
	return NewFor(varName, words, body, p._CollectRedirects())
}

func (p *Parser) _ParseForArith() Node {
	p.Advance()
	p.Advance()
	parts := []string{}
	current := []interface{}{}
	parenDepth := 0
	for !(p.AtEnd()) {
		ch := p.Peek()
		if ch == "(" {
			parenDepth += 1
			current = append(current, p.Advance())
		} else if ch == ")" {
			if parenDepth > 0 {
				parenDepth -= 1
				current = append(current, p.Advance())
			} else if p.Pos+1 < p.Length && p.Source[p.Pos+1] == ')' {
				parts = append(parts, strings.TrimLeft(strings.Join(current, ""), " \t"))
				p.Advance()
				p.Advance()
				break
			} else {
				current = append(current, p.Advance())
			}
		} else if ch == ";" && parenDepth == 0 {
			parts = append(parts, strings.TrimLeft(strings.Join(current, ""), " \t"))
			current = []interface{}{}
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

func (p *Parser) ParseSelect() Node {
	p.SkipWhitespace()
	if !(p._LexConsumeWord("select")) {
		return nil
	}
	p.SkipWhitespace()
	varName := p.PeekWord()
	if varName == nil {
		panic(NewParseError("Expected variable name after 'select'", p._LexPeekToken().Pos, 0))
	}
	p.ConsumeWord(varName)
	p.SkipWhitespace()
	if p.Peek() == ";" {
		p.Advance()
	}
	p.SkipWhitespaceAndNewlines()
	words := nil
	if p._LexIsAtReservedWord("in") {
		p._LexConsumeWord("in")
		p.SkipWhitespaceAndNewlines()
		words = []interface{}{}
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
			word := p.ParseWord(false, false, false)
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
	if term != nil {
		p._LexNextToken()
		return term
	}
	return ";;"
}

func (p *Parser) ParseCase() Node {
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
	patterns := []interface{}{}
	p._SetState(ParserStateFlags_PST_CASEPAT)
	for true {
		p.SkipWhitespaceAndNewlines()
		if p._LexIsAtReservedWord("esac") {
			saved := p.Pos
			p.SkipWhitespace()
			for !(p.AtEnd()) && !(_IsMetachar(p.Peek())) && !(_IsQuote(p.Peek())) {
				p.Advance()
			}
			p.SkipWhitespace()
			isPattern := false
			if !(p.AtEnd()) && p.Peek() == ")" {
				var nextCh string
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
		patternChars := []interface{}{}
		extglobDepth := 0
		for !(p.AtEnd()) {
			ch := p.Peek()
			var parenDepth int
			var c string
			var isCharClass bool
			var scanPos int
			var scanDepth int
			var hasFirstBracketLiteral bool
			var sc byte
			if ch == ")" {
				if extglobDepth > 0 {
					patternChars = append(patternChars, p.Advance())
					extglobDepth -= 1
				} else {
					p.Advance()
					break
				}
			} else if ch == "\\" {
				if p.Pos+1 < p.Length && p.Source[p.Pos+1] == '\n' {
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
			} else if p._Extglob && _IsExtglobPrefix(ch) && p.Pos+1 < p.Length && p.Source[p.Pos+1] == '(' {
				patternChars = append(patternChars, p.Advance())
				patternChars = append(patternChars, p.Advance())
				extglobDepth += 1
			} else if ch == "[" {
				isCharClass = false
				scanPos = p.Pos + 1
				scanDepth = 0
				hasFirstBracketLiteral = false
				if scanPos < p.Length && _IsCaretOrBang(p.Source[scanPos]) {
					scanPos += 1
				}
				if scanPos < p.Length && p.Source[scanPos] == ']' {
					if strings.Index(p.Source, "]") != -1 {
						scanPos += 1
						hasFirstBracketLiteral = true
					}
				}
				for scanPos < p.Length {
					sc = p.Source[scanPos]
					if sc == ']' && scanDepth == 0 {
						isCharClass = true
						break
					} else if sc == '[' {
						scanDepth += 1
					} else if sc == ')' && scanDepth == 0 {
						break
					} else if sc == '|' && scanDepth == 0 {
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
		pattern := strings.Join(patternChars, "")
		if !(pattern) {
			panic(NewParseError("Expected pattern in case statement", p._LexPeekToken().Pos, 0))
		}
		p.SkipWhitespace()
		body := nil
		isEmptyBody := p._LexPeekCaseTerminator() != nil
		if !(isEmptyBody) {
			p.SkipWhitespaceAndNewlines()
			if !(p.AtEnd()) && !(p._LexIsAtReservedWord("esac")) {
				isAtTerminator := p._LexPeekCaseTerminator() != nil
				if !(isAtTerminator) {
					body = p.ParseListUntil(map[interface{}]struct{}{"esac": {}})
					p.SkipWhitespace()
				}
			}
		}
		terminator := p._ConsumeCaseTerminator()
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

func (p *Parser) ParseCoproc() Node {
	p.SkipWhitespace()
	if !(p._LexConsumeWord("coproc")) {
		return nil
	}
	p.SkipWhitespace()
	name := nil
	ch := nil
	if !(p.AtEnd()) {
		ch = p.Peek()
	}
	if ch == "{" {
		body := p.ParseBraceGroup()
		if body != nil {
			return NewCoproc(body, name)
		}
	}
	if ch == "(" {
		if p.Pos+1 < p.Length && p.Source[p.Pos+1] == '(' {
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
	nextWord := p._LexPeekReservedWord()
	if nextWord != nil && CompoundKeywords[nextWord] {
		body = p.ParseCompoundCommand()
		if body != nil {
			return NewCoproc(body, name)
		}
	}
	wordStart := p.Pos
	potentialName := p.PeekWord()
	if potentialName {
		for !(p.AtEnd()) && !(_IsMetachar(p.Peek())) && !(_IsQuote(p.Peek())) {
			p.Advance()
		}
		p.SkipWhitespace()
		ch = nil
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
				if p.Pos+1 < p.Length && p.Source[p.Pos+1] == '(' {
					body = p.ParseArithmeticCommand()
				} else {
					body = p.ParseSubshell()
				}
				if body != nil {
					return NewCoproc(body, name)
				}
			} else if nextWord != nil && CompoundKeywords[nextWord] {
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

func (p *Parser) ParseFunction() Node {
	p.SkipWhitespace()
	if p.AtEnd() {
		return nil
	}
	savedPos := p.Pos
	if p._LexIsAtReservedWord("function") {
		p._LexConsumeWord("function")
		p.SkipWhitespace()
		name := p.PeekWord()
		if name == nil {
			p.Pos = savedPos
			return nil
		}
		p.ConsumeWord(name)
		p.SkipWhitespace()
		if !(p.AtEnd()) && p.Peek() == "(" {
			if p.Pos+1 < p.Length && p.Source[p.Pos+1] == ')' {
				p.Advance()
				p.Advance()
			}
		}
		p.SkipWhitespaceAndNewlines()
		body := p._ParseCompoundCommand()
		if body == nil {
			panic(NewParseError("Expected function body", p.Pos, 0))
		}
		return NewFunction(name, body)
	}
	name = p.PeekWord()
	if name == nil || ReservedWords[name] {
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
	name = p.Source[nameStart:p.Pos]
	if !(len(name) > 0) {
		p.Pos = savedPos
		return nil
	}
	braceDepth := 0
	i := 0
	for i < len(name) {
		if _IsExpansionStart(name, i, "${") {
			braceDepth += 1
			i += 2
			continue
		}
		if name[i] == '}' {
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
	if !(hasWhitespace) && len(name) > 0 && strings.ContainsRune("*?@+!$", rune(name[len(name)-1])) {
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
	result := p.ParseBraceGroup()
	if result != nil {
		return result
	}
	if !(p.AtEnd()) && p.Peek() == "(" && p.Pos+1 < p.Length && p.Source[p.Pos+1] == '(' {
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

func (p *Parser) _AtListUntilTerminator(stopWords interface{}) bool {
	if p.AtEnd() {
		return true
	}
	if p.Peek() == ")" {
		return true
	}
	if p.Peek() == "}" {
		nextPos := p.Pos + 1
		if nextPos >= p.Length || _IsWordEndContext(p.Source[nextPos]) {
			return true
		}
	}
	reserved := p._LexPeekReservedWord()
	if reserved != nil && _contains(stopWords, reserved) {
		return true
	}
	if p._LexPeekCaseTerminator() != nil {
		return true
	}
	return false
}

func (p *Parser) ParseListUntil(stopWords interface{}) Node {
	p.SkipWhitespaceAndNewlines()
	reserved := p._LexPeekReservedWord()
	if reserved != nil && _contains(stopWords, reserved) {
		return nil
	}
	pipeline := p.ParsePipeline()
	if pipeline == nil {
		return nil
	}
	parts := []interface{}{pipeline}
	for true {
		p.SkipWhitespace()
		op := p.ParseListOperator()
		if op == nil {
			var nextOp string
			if !(p.AtEnd()) && p.Peek() == "\n" {
				p.Advance()
				p._GatherHeredocBodies()
				if p._Cmdsub_heredoc_end != nil && p._Cmdsub_heredoc_end > p.Pos {
					p.Pos = p._Cmdsub_heredoc_end
					p._Cmdsub_heredoc_end = nil
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
		if op == nil {
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
	p.SkipWhitespace()
	if p.AtEnd() {
		return nil
	}
	ch := p.Peek()
	if ch == "(" && p.Pos+1 < p.Length && p.Source[p.Pos+1] == '(' {
		result := p.ParseArithmeticCommand()
		if result != nil {
			return result
		}
	}
	if ch == "(" {
		return p.ParseSubshell()
	}
	if ch == "{" {
		result = p.ParseBraceGroup()
		if result != nil {
			return result
		}
	}
	if ch == "[" && p.Pos+1 < p.Length && p.Source[p.Pos+1] == '[' {
		result = p.ParseConditionalExpr()
		if result != nil {
			return result
		}
	}
	reserved := p._LexPeekReservedWord()
	if reserved == nil && p._In_process_sub {
		word := p.PeekWord()
		if word != nil && len(word) > 1 && word[0] == '}' {
			keywordWord := word[1:]
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
	fn := p.ParseFunction()
	if fn != nil {
		return fn
	}
	return p.ParseCommand()
}

func (p *Parser) ParsePipeline() Node {
	p.SkipWhitespace()
	prefixOrder := nil
	timePosix := false
	var saved int
	var inner Node
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
			if p.Pos+2 >= p.Length || _IsWhitespace(string(p.Source[p.Pos+2])) {
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
			if p.Pos+1 >= p.Length || _IsNegationBoundary(p.Source[p.Pos+1]) && !(p._IsBangFollowedByProcsub()) {
				p.Advance()
				prefixOrder = "time_negation"
				p.SkipWhitespace()
			}
		}
	} else if !(p.AtEnd()) && p.Peek() == "!" {
		if p.Pos+1 >= p.Length || _IsNegationBoundary(p.Source[p.Pos+1]) && !(p._IsBangFollowedByProcsub()) {
			p.Advance()
			p.SkipWhitespace()
			inner = p.ParsePipeline()
			if inner != nil && inner.Kind() == "negation" {
				if inner.Pipeline != nil {
					return inner.Pipeline
				} else {
					return NewCommand([]interface{}{}, nil)
				}
			}
			return NewNegation(inner)
		}
	}
	result := p._ParseSimplePipeline()
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
	} else if result == nil {
		return nil
	}
	return result
}

func (p *Parser) _ParseSimplePipeline() Node {
	cmd := p.ParseCompoundCommand()
	if cmd == nil {
		return nil
	}
	commands := []interface{}{cmd}
	for true {
		p.SkipWhitespace()
		op0, op1 := p._LexPeekOperator()
		if op == nil {
			break
		}
		panic("TODO: incomplete implementation")
	}
	if len(commands) == 1 {
		return commands[0]
	}
	return NewPipeline(commands)
}

func (p *Parser) ParseListOperator() string {
	p.SkipWhitespace()
	op0, op1 := p._LexPeekOperator()
	if op == nil {
		return ""
	}
	panic("TODO: Tuple unpacking from Name")
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
	if newlineAsSeparator {
		p.SkipWhitespaceAndNewlines()
	} else {
		p.SkipWhitespace()
	}
	pipeline := p.ParsePipeline()
	if pipeline == nil {
		return nil
	}
	parts := []interface{}{pipeline}
	if p._InState(ParserStateFlags_PST_EOFTOKEN) && p._AtEofToken() {
		return _ternary(len(parts) == 1, parts[0], NewList(parts))
	}
	for true {
		p.SkipWhitespace()
		op := p.ParseListOperator()
		if op == nil {
			var nextOp string
			if !(p.AtEnd()) && p.Peek() == "\n" {
				if !(newlineAsSeparator) {
					break
				}
				p.Advance()
				p._GatherHeredocBodies()
				if p._Cmdsub_heredoc_end != nil && p._Cmdsub_heredoc_end > p.Pos {
					p.Pos = p._Cmdsub_heredoc_end
					p._Cmdsub_heredoc_end = nil
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
		if op == nil {
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
		if pipeline == nil {
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
	text := p.Source[start:p.Pos]
	return NewComment(text)
}

func (p *Parser) Parse() []Node {
	source := strings.TrimSpace(p.Source)
	if !(source) {
		return []Node{NewEmpty()}
	}
	results := []interface{}{}
	for true {
		p.SkipWhitespace()
		for !(p.AtEnd()) && p.Peek() == "\n" {
			p.Advance()
		}
		if p.AtEnd() {
			break
		}
		comment := p.ParseComment()
		if !(comment) {
			break
		}
	}
	for !(p.AtEnd()) {
		result := p.ParseList(false)
		if result != nil {
			results = append(results, result)
		}
		p.SkipWhitespace()
		foundNewline := false
		for !(p.AtEnd()) && p.Peek() == "\n" {
			foundNewline = true
			p.Advance()
			p._GatherHeredocBodies()
			if p._Cmdsub_heredoc_end != nil && p._Cmdsub_heredoc_end > p.Pos {
				p.Pos = p._Cmdsub_heredoc_end
				p._Cmdsub_heredoc_end = nil
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
	if p._Saw_newline_in_single_quote && p.Source && p.Source[len(p.Source)-1] == '\\' && !(len(p.Source) >= 3 && p.Source[len(p.Source)-3:len(p.Source)-1] == "\\\n") {
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
	if lastWord && strings.HasSuffix(lastWord.Value, "\\") {
		lastWord.Value = lastWord.Value[0 : len(lastWord.Value)-1]
		panic("TODO: incomplete implementation")
	}
}

func (p *Parser) _FindLastWord(node Node) Node {
	panic("TODO: isinstance")
	panic("TODO: isinstance")
	panic("TODO: isinstance")
	panic("TODO: isinstance")
	return nil
}
