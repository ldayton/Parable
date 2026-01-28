package parable

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
	TokenTypeEOF                  = 0
	TokenTypeWORD                 = 1
	TokenTypeNEWLINE              = 2
	TokenTypeSEMI                 = 10
	TokenTypePIPE                 = 11
	TokenTypeAMP                  = 12
	TokenTypeLPAREN               = 13
	TokenTypeRPAREN               = 14
	TokenTypeLBRACE               = 15
	TokenTypeRBRACE               = 16
	TokenTypeLESS                 = 17
	TokenTypeGREATER              = 18
	TokenTypeANDAND               = 30
	TokenTypeOROR                 = 31
	TokenTypeSEMISEMI             = 32
	TokenTypeSEMIAMP              = 33
	TokenTypeSEMISEMIAMP          = 34
	TokenTypeLESSLESS             = 35
	TokenTypeGREATERGREATER       = 36
	TokenTypeLESSAMP              = 37
	TokenTypeGREATERAMP           = 38
	TokenTypeLESSGREATER          = 39
	TokenTypeGREATERPIPE          = 40
	TokenTypeLESSLESSMINUS        = 41
	TokenTypeLESSLESSLESS         = 42
	TokenTypeAMPGREATER           = 43
	TokenTypeAMPGREATERGREATER    = 44
	TokenTypePIPEAMP              = 45
	TokenTypeIF                   = 50
	TokenTypeTHEN                 = 51
	TokenTypeELSE                 = 52
	TokenTypeELIF                 = 53
	TokenTypeFI                   = 54
	TokenTypeCASE                 = 55
	TokenTypeESAC                 = 56
	TokenTypeFOR                  = 57
	TokenTypeWHILE                = 58
	TokenTypeUNTIL                = 59
	TokenTypeDO                   = 60
	TokenTypeDONE                 = 61
	TokenTypeIN                   = 62
	TokenTypeFUNCTION             = 63
	TokenTypeSELECT               = 64
	TokenTypeCOPROC               = 65
	TokenTypeTIME                 = 66
	TokenTypeBANG                 = 67
	TokenTypeLBRACKETLBRACKET     = 68
	TokenTypeRBRACKETRBRACKET     = 69
	TokenTypeASSIGNMENTWORD       = 80
	TokenTypeNUMBER               = 81
	ParserStateFlagsNONE          = 0
	ParserStateFlagsPSTCASEPAT    = 1
	ParserStateFlagsPSTCMDSUBST   = 2
	ParserStateFlagsPSTCASESTMT   = 4
	ParserStateFlagsPSTCONDEXPR   = 8
	ParserStateFlagsPSTCOMPASSIGN = 16
	ParserStateFlagsPSTARITH      = 32
	ParserStateFlagsPSTHEREDOC    = 64
	ParserStateFlagsPSTREGEXP     = 128
	ParserStateFlagsPSTEXTPAT     = 256
	ParserStateFlagsPSTSUBSHELL   = 512
	ParserStateFlagsPSTREDIRLIST  = 1024
	ParserStateFlagsPSTCOMMENT    = 2048
	ParserStateFlagsPSTEOFTOKEN   = 4096
	DolbraceStateNONE             = 0
	DolbraceStatePARAM            = 1
	DolbraceStateOP               = 2
	DolbraceStateWORD             = 4
	DolbraceStateQUOTE            = 64
	DolbraceStateQUOTE2           = 128
	MatchedPairFlagsNONE          = 0
	MatchedPairFlagsDQUOTE        = 1
	MatchedPairFlagsDOLBRACE      = 2
	MatchedPairFlagsCOMMAND       = 4
	MatchedPairFlagsARITH         = 8
	MatchedPairFlagsALLOWESC      = 16
	MatchedPairFlagsEXTGLOB       = 32
	MatchedPairFlagsFIRSTCLOSE    = 64
	MatchedPairFlagsARRAYSUB      = 128
	MatchedPairFlagsBACKQUOTE     = 256
	ParseContextNORMAL            = 0
	ParseContextCOMMANDSUB        = 1
	ParseContextARITHMETIC        = 2
	ParseContextCASEPATTERN       = 3
	ParseContextBRACEEXPANSION    = 4
	SMPLITERAL                    = 1
	SMPPASTOPEN                   = 2
	WORDCTXNORMAL                 = 0
	WORDCTXCOND                   = 1
	WORDCTXREGEX                  = 2
)

var (
	ANSICESCAPES       = map[string]int{"a": 7, "b": 8, "e": 27, "E": 27, "f": 12, "n": 10, "r": 13, "t": 9, "v": 11, "\\": 92, "\"": 34, "?": 63}
	RESERVEDWORDS      = map[string]struct{}{"if": {}, "then": {}, "elif": {}, "else": {}, "fi": {}, "while": {}, "until": {}, "for": {}, "select": {}, "do": {}, "done": {}, "case": {}, "esac": {}, "in": {}, "function": {}, "coproc": {}}
	CONDUNARYOPS       = map[string]struct{}{"-a": {}, "-b": {}, "-c": {}, "-d": {}, "-e": {}, "-f": {}, "-g": {}, "-h": {}, "-k": {}, "-p": {}, "-r": {}, "-s": {}, "-t": {}, "-u": {}, "-w": {}, "-x": {}, "-G": {}, "-L": {}, "-N": {}, "-O": {}, "-S": {}, "-z": {}, "-n": {}, "-o": {}, "-v": {}, "-R": {}}
	CONDBINARYOPS      = map[string]struct{}{"==": {}, "!=": {}, "=~": {}, "=": {}, "<": {}, ">": {}, "-eq": {}, "-ne": {}, "-lt": {}, "-le": {}, "-gt": {}, "-ge": {}, "-nt": {}, "-ot": {}, "-ef": {}}
	COMPOUNDKEYWORDS   = map[string]struct{}{"while": {}, "until": {}, "for": {}, "if": {}, "case": {}, "select": {}}
	ASSIGNMENTBUILTINS = map[string]struct{}{"alias": {}, "declare": {}, "typeset": {}, "local": {}, "export": {}, "readonly": {}, "eval": {}, "let": {}}
)

type Node interface {
	GetKind() string
	ToSexp() string
}

type ParseError struct {
	Message string
	Pos     int
	Line    int
}

func (self *ParseError) Error() string {
	return self.formatMessage()
}

func (self *ParseError) formatMessage() string {
	if self.Line != 0 && self.Pos != 0 {
		return fmt.Sprintf("Parse error at line %v, position %v: %v", self.Line, self.Pos, self.Message)
	} else if self.Pos != 0 {
		return fmt.Sprintf("Parse error at position %v: %v", self.Pos, self.Message)
	}
	return fmt.Sprintf("Parse error: %v", self.Message)
}

type MatchedPairError struct {
	ParseError
}

type TokenType struct {
}

type Token struct {
	Type  int
	Value string
	Pos   int
	Parts []Node
	Word  *Word
}

func (self *Token) repr() string {
	if self.Word != nil {
		return fmt.Sprintf("Token(%v, %v, %v, word=%v)", self.Type, self.Value, self.Pos, self.Word)
	}
	if len(self.Parts) > 0 {
		return fmt.Sprintf("Token(%v, %v, %v, parts=%v)", self.Type, self.Value, self.Pos, len(self.Parts))
	}
	return fmt.Sprintf("Token(%v, %v, %v)", self.Type, self.Value, self.Pos)
}

type ParserStateFlags struct {
}

type DolbraceState struct {
}

type MatchedPairFlags struct {
}

type SavedParserState struct {
	ParserState     int
	DolbraceState   int
	PendingHeredocs []Node
	CtxStack        []*ParseContext
	EofToken        string
}

type QuoteState struct {
	Single bool
	Double bool
	stack  []struct {
		F0 bool
		F1 bool
	}
}

func (self *QuoteState) Push() {
	self.stack = append(self.stack, struct {
		F0 bool
		F1 bool
	}{self.Single, self.Double})
	self.Single = false
	self.Double = false
}

func (self *QuoteState) Pop() {
	if len(self.stack) > 0 {
		{
			var entry struct {
				F0 bool
				F1 bool
			} = self.stack[len(self.stack)-1]
			self.stack = self.stack[:len(self.stack)-1]
			self.Single = entry.F0
			self.Double = entry.F1
		}
	}
}

func (self *QuoteState) InQuotes() bool {
	return self.Single || self.Double
}

func (self *QuoteState) Copy() *QuoteState {
	qs := NewQuoteState()
	qs.Single = self.Single
	qs.Double = self.Double
	qs.stack = append(self.stack[:0:0], self.stack...)
	return qs
}

func (self *QuoteState) OuterDouble() bool {
	if len(self.stack) == 0 {
		return false
	}
	return self.stack[len(self.stack)-1].F1
}

type ParseContext struct {
	Kind            int
	ParenDepth      int
	BraceDepth      int
	BracketDepth    int
	CaseDepth       int
	ArithDepth      int
	ArithParenDepth int
	Quote           *QuoteState
}

func (self *ParseContext) Copy() *ParseContext {
	ctx := NewParseContext(self.Kind)
	ctx.ParenDepth = self.ParenDepth
	ctx.BraceDepth = self.BraceDepth
	ctx.BracketDepth = self.BracketDepth
	ctx.CaseDepth = self.CaseDepth
	ctx.ArithDepth = self.ArithDepth
	ctx.ArithParenDepth = self.ArithParenDepth
	ctx.Quote = self.Quote.Copy()
	return ctx
}

type ContextStack struct {
	stack []*ParseContext
}

func (self *ContextStack) GetCurrent() *ParseContext {
	return self.stack[len(self.stack)-1]
}

func (self *ContextStack) Push(kind int) {
	self.stack = append(self.stack, NewParseContext(kind))
}

func (self *ContextStack) Pop() *ParseContext {
	if len(self.stack) > 1 {
		return self.stack[len(self.stack)-1]
	}
	return self.stack[0]
}

func (self *ContextStack) CopyStack() []*ParseContext {
	result := []*ParseContext{}
	for _, ctx := range self.stack {
		result = append(result, ctx.Copy())
	}
	return result
}

func (self *ContextStack) RestoreFrom(savedStack []*ParseContext) {
	result := []*ParseContext{}
	for _, ctx := range savedStack {
		result = append(result, ctx.Copy())
	}
	self.stack = result
}

type Lexer struct {
	RESERVEDWORDS         map[string]int
	Source                string
	Pos                   int
	Length                int
	Quote                 *QuoteState
	tokenCache            *Token
	parserState           int
	dolbraceState         int
	pendingHeredocs       []Node
	extglob               bool
	parser                *Parser
	eofToken              string
	lastReadToken         *Token
	wordContext           int
	atCommandStart        bool
	inArrayLiteral        bool
	inAssignBuiltin       bool
	postReadPos           int
	cachedWordContext     int
	cachedAtCommandStart  bool
	cachedInArrayLiteral  bool
	cachedInAssignBuiltin bool
}

func (self *Lexer) Peek() string {
	if self.Pos >= self.Length {
		return ""
	}
	return string(_runeAt(self.Source, self.Pos))
}

func (self *Lexer) Advance() string {
	if self.Pos >= self.Length {
		return ""
	}
	c := string(_runeAt(self.Source, self.Pos))
	self.Pos++
	return c
}

func (self *Lexer) AtEnd() bool {
	return self.Pos >= self.Length
}

func (self *Lexer) Lookahead(n int) string {
	return substring(self.Source, self.Pos, self.Pos+n)
}

func (self *Lexer) IsMetachar(c string) bool {
	return strings.Contains("|&;()<> \t\n", c)
}

func (self *Lexer) readOperator() *Token {
	start := self.Pos
	c := self.Peek()
	if c == "" {
		return nil
	}
	two := self.Lookahead(2)
	three := self.Lookahead(3)
	if three == ";;&" {
		self.Pos += 3
		return &Token{Type: TokenTypeSEMISEMIAMP, Value: three, Pos: start}
	}
	if three == "<<-" {
		self.Pos += 3
		return &Token{Type: TokenTypeLESSLESSMINUS, Value: three, Pos: start}
	}
	if three == "<<<" {
		self.Pos += 3
		return &Token{Type: TokenTypeLESSLESSLESS, Value: three, Pos: start}
	}
	if three == "&>>" {
		self.Pos += 3
		return &Token{Type: TokenTypeAMPGREATERGREATER, Value: three, Pos: start}
	}
	if two == "&&" {
		self.Pos += 2
		return &Token{Type: TokenTypeANDAND, Value: two, Pos: start}
	}
	if two == "||" {
		self.Pos += 2
		return &Token{Type: TokenTypeOROR, Value: two, Pos: start}
	}
	if two == ";;" {
		self.Pos += 2
		return &Token{Type: TokenTypeSEMISEMI, Value: two, Pos: start}
	}
	if two == ";&" {
		self.Pos += 2
		return &Token{Type: TokenTypeSEMIAMP, Value: two, Pos: start}
	}
	if two == "<<" {
		self.Pos += 2
		return &Token{Type: TokenTypeLESSLESS, Value: two, Pos: start}
	}
	if two == ">>" {
		self.Pos += 2
		return &Token{Type: TokenTypeGREATERGREATER, Value: two, Pos: start}
	}
	if two == "<&" {
		self.Pos += 2
		return &Token{Type: TokenTypeLESSAMP, Value: two, Pos: start}
	}
	if two == ">&" {
		self.Pos += 2
		return &Token{Type: TokenTypeGREATERAMP, Value: two, Pos: start}
	}
	if two == "<>" {
		self.Pos += 2
		return &Token{Type: TokenTypeLESSGREATER, Value: two, Pos: start}
	}
	if two == ">|" {
		self.Pos += 2
		return &Token{Type: TokenTypeGREATERPIPE, Value: two, Pos: start}
	}
	if two == "&>" {
		self.Pos += 2
		return &Token{Type: TokenTypeAMPGREATER, Value: two, Pos: start}
	}
	if two == "|&" {
		self.Pos += 2
		return &Token{Type: TokenTypePIPEAMP, Value: two, Pos: start}
	}
	if c == ";" {
		self.Pos++
		return &Token{Type: TokenTypeSEMI, Value: c, Pos: start}
	}
	if c == "|" {
		self.Pos++
		return &Token{Type: TokenTypePIPE, Value: c, Pos: start}
	}
	if c == "&" {
		self.Pos++
		return &Token{Type: TokenTypeAMP, Value: c, Pos: start}
	}
	if c == "(" {
		if self.wordContext == WORDCTXREGEX {
			return nil
		}
		self.Pos++
		return &Token{Type: TokenTypeLPAREN, Value: c, Pos: start}
	}
	if c == ")" {
		if self.wordContext == WORDCTXREGEX {
			return nil
		}
		self.Pos++
		return &Token{Type: TokenTypeRPAREN, Value: c, Pos: start}
	}
	if c == "<" {
		if self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "(" {
			return nil
		}
		self.Pos++
		return &Token{Type: TokenTypeLESS, Value: c, Pos: start}
	}
	if c == ">" {
		if self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "(" {
			return nil
		}
		self.Pos++
		return &Token{Type: TokenTypeGREATER, Value: c, Pos: start}
	}
	if c == "\n" {
		self.Pos++
		return &Token{Type: TokenTypeNEWLINE, Value: c, Pos: start}
	}
	return nil
}

func (self *Lexer) SkipBlanks() {
	for self.Pos < self.Length {
		c := string(_runeAt(self.Source, self.Pos))
		if c != " " && c != "\t" {
			break
		}
		self.Pos++
	}
}

func (self *Lexer) skipComment() bool {
	if self.Pos >= self.Length {
		return false
	}
	if string(_runeAt(self.Source, self.Pos)) != "#" {
		return false
	}
	if self.Quote.InQuotes() {
		return false
	}
	if self.Pos > 0 {
		prev := string(_runeAt(self.Source, self.Pos-1))
		if !strings.Contains(" \t\n;|&(){}", prev) {
			return false
		}
	}
	for self.Pos < self.Length && string(_runeAt(self.Source, self.Pos)) != "\n" {
		self.Pos++
	}
	return true
}

func (self *Lexer) readSingleQuote(start int) (string, bool) {
	chars := []string{"'"}
	sawNewline := false
	for self.Pos < self.Length {
		c := string(_runeAt(self.Source, self.Pos))
		if c == "\n" {
			sawNewline = true
		}
		chars = append(chars, c)
		self.Pos++
		if c == "'" {
			return strings.Join(chars, ""), sawNewline
		}
	}
	panic(NewParseError("Unterminated single quote", start, 0))
}

func (self *Lexer) isWordTerminator(ctx int, ch string, bracketDepth int, parenDepth int) bool {
	if ctx == WORDCTXREGEX {
		if ch == "]" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "]" {
			return true
		}
		if ch == "&" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "&" {
			return true
		}
		if ch == ")" && parenDepth == 0 {
			return true
		}
		return isWhitespace(ch) && parenDepth == 0
	}
	if ctx == WORDCTXCOND {
		if ch == "]" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "]" {
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
		if isRedirectChar(ch) && !(self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "(") {
			return true
		}
		return isWhitespace(ch)
	}
	if (self.parserState&ParserStateFlagsPSTEOFTOKEN) != 0 && self.eofToken != "" && ch == self.eofToken && bracketDepth == 0 {
		return true
	}
	if isRedirectChar(ch) && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "(" {
		return false
	}
	return isMetachar(ch) && bracketDepth == 0
}

func (self *Lexer) readBracketExpression(chars *[]string, parts []Node, forRegex bool, parenDepth int) bool {
	if forRegex {
		scan := self.Pos + 1
		if scan < self.Length && string(_runeAt(self.Source, scan)) == "^" {
			scan++
		}
		if scan < self.Length && string(_runeAt(self.Source, scan)) == "]" {
			scan++
		}
		bracketWillClose := false
		for scan < self.Length {
			sc := string(_runeAt(self.Source, scan))
			if sc == "]" && scan+1 < self.Length && string(_runeAt(self.Source, scan+1)) == "]" {
				break
			}
			if sc == ")" && parenDepth > 0 {
				break
			}
			if sc == "&" && scan+1 < self.Length && string(_runeAt(self.Source, scan+1)) == "&" {
				break
			}
			if sc == "]" {
				bracketWillClose = true
				break
			}
			if sc == "[" && scan+1 < self.Length && string(_runeAt(self.Source, scan+1)) == ":" {
				scan += 2
				for scan < self.Length && !(string(_runeAt(self.Source, scan)) == ":" && scan+1 < self.Length && string(_runeAt(self.Source, scan+1)) == "]") {
					scan++
				}
				if scan < self.Length {
					scan += 2
				}
				continue
			}
			scan++
		}
		if !bracketWillClose {
			return false
		}
	} else {
		if self.Pos+1 >= self.Length {
			return false
		}
		nextCh := string(_runeAt(self.Source, self.Pos+1))
		if isWhitespaceNoNewline(nextCh) || nextCh == "&" || nextCh == "|" {
			return false
		}
	}
	*chars = append(*chars, self.Advance())
	if !self.AtEnd() && self.Peek() == "^" {
		*chars = append(*chars, self.Advance())
	}
	if !self.AtEnd() && self.Peek() == "]" {
		*chars = append(*chars, self.Advance())
	}
	for !self.AtEnd() {
		c := self.Peek()
		if c == "]" {
			*chars = append(*chars, self.Advance())
			break
		}
		if c == "[" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == ":" {
			*chars = append(*chars, self.Advance())
			*chars = append(*chars, self.Advance())
			for !self.AtEnd() && !(self.Peek() == ":" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "]") {
				*chars = append(*chars, self.Advance())
			}
			if !self.AtEnd() {
				*chars = append(*chars, self.Advance())
				*chars = append(*chars, self.Advance())
			}
		} else if !forRegex && c == "[" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "=" {
			*chars = append(*chars, self.Advance())
			*chars = append(*chars, self.Advance())
			for !self.AtEnd() && !(self.Peek() == "=" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "]") {
				*chars = append(*chars, self.Advance())
			}
			if !self.AtEnd() {
				*chars = append(*chars, self.Advance())
				*chars = append(*chars, self.Advance())
			}
		} else if !forRegex && c == "[" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "." {
			*chars = append(*chars, self.Advance())
			*chars = append(*chars, self.Advance())
			for !self.AtEnd() && !(self.Peek() == "." && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "]") {
				*chars = append(*chars, self.Advance())
			}
			if !self.AtEnd() {
				*chars = append(*chars, self.Advance())
				*chars = append(*chars, self.Advance())
			}
		} else if forRegex && c == "$" {
			self.syncToParser()
			if !self.parser.parseDollarExpansion(chars, &parts, false) {
				self.syncFromParser()
				*chars = append(*chars, self.Advance())
			} else {
				self.syncFromParser()
			}
		} else {
			*chars = append(*chars, self.Advance())
		}
	}
	return true
}

func (self *Lexer) parseMatchedPair(openChar string, closeChar string, flags int, initialWasDollar bool) string {
	start := self.Pos
	count := 1
	chars := []string{}
	passNext := false
	wasDollar := initialWasDollar
	wasGtlt := false
	for count > 0 {
		if self.AtEnd() {
			panic(NewMatchedPairError(fmt.Sprintf("unexpected EOF while looking for matching `%v'", closeChar), start, 0))
		}
		ch := self.Advance()
		if (flags&MatchedPairFlagsDOLBRACE) != 0 && self.dolbraceState == DolbraceStateOP {
			if !strings.Contains("#%^,~:-=?+/", ch) {
				self.dolbraceState = DolbraceStateWORD
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
				count--
				if count == 0 {
					break
				}
			}
			if ch == "\\" && (flags&MatchedPairFlagsALLOWESC) != 0 {
				passNext = true
			}
			chars = append(chars, ch)
			wasDollar = false
			wasGtlt = false
			continue
		}
		if ch == "\\" {
			if !self.AtEnd() && self.Peek() == "\n" {
				self.Advance()
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
			count--
			if count == 0 {
				break
			}
			chars = append(chars, ch)
			wasDollar = false
			wasGtlt = strings.Contains("<>", ch)
			continue
		}
		if ch == openChar && openChar != closeChar {
			if !((flags&MatchedPairFlagsDOLBRACE) != 0 && openChar == "{") {
				count++
			}
			chars = append(chars, ch)
			wasDollar = false
			wasGtlt = strings.Contains("<>", ch)
			continue
		}
		if strings.Contains("'\"`", ch) && openChar != closeChar {
			var nested string
			if ch == "'" {
				chars = append(chars, ch)
				quoteFlags := func() int {
					if wasDollar {
						return (flags | MatchedPairFlagsALLOWESC)
					} else {
						return flags
					}
				}()
				nested = self.parseMatchedPair("'", "'", quoteFlags, false)
				chars = append(chars, nested)
				chars = append(chars, "'")
				wasDollar = false
				wasGtlt = false
				continue
			} else if ch == "\"" {
				chars = append(chars, ch)
				nested = self.parseMatchedPair("\"", "\"", (flags | MatchedPairFlagsDQUOTE), false)
				chars = append(chars, nested)
				chars = append(chars, "\"")
				wasDollar = false
				wasGtlt = false
				continue
			} else if ch == "`" {
				chars = append(chars, ch)
				nested = self.parseMatchedPair("`", "`", flags, false)
				chars = append(chars, nested)
				chars = append(chars, "`")
				wasDollar = false
				wasGtlt = false
				continue
			}
		}
		if ch == "$" && !self.AtEnd() && !((flags & MatchedPairFlagsEXTGLOB) != 0) {
			nextCh := self.Peek()
			if wasDollar {
				chars = append(chars, ch)
				wasDollar = false
				wasGtlt = false
				continue
			}
			if nextCh == "{" {
				if (flags & MatchedPairFlagsARITH) != 0 {
					afterBracePos := self.Pos + 1
					if afterBracePos >= self.Length || !isFunsubChar(string(_runeAt(self.Source, afterBracePos))) {
						chars = append(chars, ch)
						wasDollar = true
						wasGtlt = false
						continue
					}
				}
				self.Pos--
				self.syncToParser()
				inDquote := (flags & MatchedPairFlagsDQUOTE) != 0
				paramNode, paramText := self.parser.parseParamExpansion(inDquote)
				self.syncFromParser()
				if !_isNilInterface(paramNode) {
					chars = append(chars, paramText)
					wasDollar = false
					wasGtlt = false
				} else {
					chars = append(chars, self.Advance())
					wasDollar = true
					wasGtlt = false
				}
				continue
			} else if nextCh == "(" {
				self.Pos--
				self.syncToParser()
				var cmdNode Node
				var cmdText string
				if self.Pos+2 < self.Length && string(_runeAt(self.Source, self.Pos+2)) == "(" {
					arithNode, arithText := self.parser.parseArithmeticExpansion()
					self.syncFromParser()
					if !_isNilInterface(arithNode) {
						chars = append(chars, arithText)
						wasDollar = false
						wasGtlt = false
					} else {
						self.syncToParser()
						cmdNode, cmdText = self.parser.parseCommandSubstitution()
						self.syncFromParser()
						if !_isNilInterface(cmdNode) {
							chars = append(chars, cmdText)
							wasDollar = false
							wasGtlt = false
						} else {
							chars = append(chars, self.Advance())
							chars = append(chars, self.Advance())
							wasDollar = false
							wasGtlt = false
						}
					}
				} else {
					cmdNode, cmdText = self.parser.parseCommandSubstitution()
					self.syncFromParser()
					if !_isNilInterface(cmdNode) {
						chars = append(chars, cmdText)
						wasDollar = false
						wasGtlt = false
					} else {
						chars = append(chars, self.Advance())
						chars = append(chars, self.Advance())
						wasDollar = false
						wasGtlt = false
					}
				}
				continue
			} else if nextCh == "[" {
				self.Pos--
				self.syncToParser()
				arithNode, arithText := self.parser.parseDeprecatedArithmetic()
				self.syncFromParser()
				if !_isNilInterface(arithNode) {
					chars = append(chars, arithText)
					wasDollar = false
					wasGtlt = false
				} else {
					chars = append(chars, self.Advance())
					wasDollar = true
					wasGtlt = false
				}
				continue
			}
		}
		if ch == "(" && wasGtlt && (flags&(MatchedPairFlagsDOLBRACE|MatchedPairFlagsARRAYSUB)) != 0 {
			direction := chars[len(chars)-1]
			chars = chars[:len(chars)-1]
			self.Pos--
			self.syncToParser()
			procsubNode, procsubText := self.parser.parseProcessSubstitution()
			self.syncFromParser()
			if !_isNilInterface(procsubNode) {
				chars = append(chars, procsubText)
				wasDollar = false
				wasGtlt = false
			} else {
				chars = append(chars, direction)
				chars = append(chars, self.Advance())
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

func (self *Lexer) collectParamArgument(flags int, wasDollar bool) string {
	return self.parseMatchedPair("{", "}", (flags | MatchedPairFlagsDOLBRACE), wasDollar)
}

func (self *Lexer) readWordInternal(ctx int, atCommandStart bool, inArrayLiteral bool, inAssignBuiltin bool) *Word {
	start := self.Pos
	chars := []string{}
	parts := []Node{}
	bracketDepth := 0
	bracketStartPos := -1
	seenEquals := false
	parenDepth := 0
	for !self.AtEnd() {
		ch := self.Peek()
		if ctx == WORDCTXREGEX {
			if ch == "\\" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "\n" {
				self.Advance()
				self.Advance()
				continue
			}
		}
		if ctx != WORDCTXNORMAL && self.isWordTerminator(ctx, ch, bracketDepth, parenDepth) {
			break
		}
		if ctx == WORDCTXNORMAL && ch == "[" {
			if bracketDepth > 0 {
				bracketDepth++
				chars = append(chars, self.Advance())
				continue
			}
			if len(chars) > 0 && atCommandStart && !seenEquals && isArrayAssignmentPrefix(chars) {
				prevChar := chars[len(chars)-1]
				if _strIsAlnum(prevChar) || prevChar == "_" {
					bracketStartPos = self.Pos
					bracketDepth++
					chars = append(chars, self.Advance())
					continue
				}
			}
			if !(len(chars) > 0) && !seenEquals && inArrayLiteral {
				bracketStartPos = self.Pos
				bracketDepth++
				chars = append(chars, self.Advance())
				continue
			}
		}
		if ctx == WORDCTXNORMAL && ch == "]" && bracketDepth > 0 {
			bracketDepth--
			chars = append(chars, self.Advance())
			continue
		}
		if ctx == WORDCTXNORMAL && ch == "=" && bracketDepth == 0 {
			seenEquals = true
		}
		if ctx == WORDCTXREGEX && ch == "(" {
			parenDepth++
			chars = append(chars, self.Advance())
			continue
		}
		if ctx == WORDCTXREGEX && ch == ")" {
			if parenDepth > 0 {
				parenDepth--
				chars = append(chars, self.Advance())
				continue
			}
			break
		}
		if (ctx == WORDCTXCOND || ctx == WORDCTXREGEX) && ch == "[" {
			forRegex := ctx == WORDCTXREGEX
			if self.readBracketExpression(&chars, parts, forRegex, parenDepth) {
				continue
			}
			chars = append(chars, self.Advance())
			continue
		}
		var content string
		if ctx == WORDCTXCOND && ch == "(" {
			if self.extglob && len(chars) > 0 && isExtglobPrefix(chars[len(chars)-1]) {
				chars = append(chars, self.Advance())
				content = self.parseMatchedPair("(", ")", MatchedPairFlagsEXTGLOB, false)
				chars = append(chars, content)
				chars = append(chars, ")")
				continue
			} else {
				break
			}
		}
		if ctx == WORDCTXREGEX && isWhitespace(ch) && parenDepth > 0 {
			chars = append(chars, self.Advance())
			continue
		}
		if ch == "'" {
			self.Advance()
			trackNewline := ctx == WORDCTXNORMAL
			content, sawNewline := self.readSingleQuote(start)
			chars = append(chars, content)
			if trackNewline && sawNewline && self.parser != nil {
				self.parser.sawNewlineInSingleQuote = true
			}
			continue
		}
		var cmdsubResult0 Node
		var cmdsubResult1 string
		if ch == "\"" {
			self.Advance()
			if ctx == WORDCTXNORMAL {
				chars = append(chars, "\"")
				inSingleInDquote := false
				for !self.AtEnd() && (inSingleInDquote || self.Peek() != "\"") {
					c := self.Peek()
					if inSingleInDquote {
						chars = append(chars, self.Advance())
						if c == "'" {
							inSingleInDquote = false
						}
						continue
					}
					if c == "\\" && self.Pos+1 < self.Length {
						nextC := string(_runeAt(self.Source, self.Pos+1))
						if nextC == "\n" {
							self.Advance()
							self.Advance()
						} else {
							chars = append(chars, self.Advance())
							chars = append(chars, self.Advance())
						}
					} else if c == "$" {
						self.syncToParser()
						if !self.parser.parseDollarExpansion(&chars, &parts, true) {
							self.syncFromParser()
							chars = append(chars, self.Advance())
						} else {
							self.syncFromParser()
						}
					} else if c == "`" {
						self.syncToParser()
						cmdsubResult0, cmdsubResult1 = self.parser.parseBacktickSubstitution()
						self.syncFromParser()
						if !_isNilInterface(cmdsubResult0) {
							parts = append(parts, cmdsubResult0)
							chars = append(chars, cmdsubResult1)
						} else {
							chars = append(chars, self.Advance())
						}
					} else {
						chars = append(chars, self.Advance())
					}
				}
				if self.AtEnd() {
					panic(NewParseError("Unterminated double quote", start, 0))
				}
				chars = append(chars, self.Advance())
			} else {
				handleLineContinuation := ctx == WORDCTXCOND
				self.syncToParser()
				self.parser.scanDoubleQuote(&chars, parts, start, handleLineContinuation)
				self.syncFromParser()
			}
			continue
		}
		if ch == "\\" && self.Pos+1 < self.Length {
			nextCh := string(_runeAt(self.Source, self.Pos+1))
			if ctx != WORDCTXREGEX && nextCh == "\n" {
				self.Advance()
				self.Advance()
			} else {
				chars = append(chars, self.Advance())
				chars = append(chars, self.Advance())
			}
			continue
		}
		if ctx != WORDCTXREGEX && ch == "$" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "'" {
			ansiResult0, ansiResult1 := self.readAnsiCQuote()
			if !_isNilInterface(ansiResult0) {
				parts = append(parts, ansiResult0)
				chars = append(chars, ansiResult1)
			} else {
				chars = append(chars, self.Advance())
			}
			continue
		}
		if ctx != WORDCTXREGEX && ch == "$" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "\"" {
			localeResult0, localeResult1, localeResult2 := self.readLocaleString()
			if !_isNilInterface(localeResult0) {
				parts = append(parts, localeResult0)
				parts = append(parts, localeResult2...)
				chars = append(chars, localeResult1)
			} else {
				chars = append(chars, self.Advance())
			}
			continue
		}
		if ch == "$" {
			self.syncToParser()
			if !self.parser.parseDollarExpansion(&chars, &parts, false) {
				self.syncFromParser()
				chars = append(chars, self.Advance())
			} else {
				self.syncFromParser()
				if self.extglob && ctx == WORDCTXNORMAL && len(chars) > 0 && _runeLen(chars[len(chars)-1]) == 2 && string(_runeAt(chars[len(chars)-1], 0)) == "$" && strings.Contains("?*@", string(_runeAt(chars[len(chars)-1], 1))) && !self.AtEnd() && self.Peek() == "(" {
					chars = append(chars, self.Advance())
					content = self.parseMatchedPair("(", ")", MatchedPairFlagsEXTGLOB, false)
					chars = append(chars, content)
					chars = append(chars, ")")
				}
			}
			continue
		}
		if ctx != WORDCTXREGEX && ch == "`" {
			self.syncToParser()
			cmdsubResult0, cmdsubResult1 = self.parser.parseBacktickSubstitution()
			self.syncFromParser()
			if !_isNilInterface(cmdsubResult0) {
				parts = append(parts, cmdsubResult0)
				chars = append(chars, cmdsubResult1)
			} else {
				chars = append(chars, self.Advance())
			}
			continue
		}
		if ctx != WORDCTXREGEX && isRedirectChar(ch) && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "(" {
			self.syncToParser()
			procsubResult0, procsubResult1 := self.parser.parseProcessSubstitution()
			self.syncFromParser()
			if !_isNilInterface(procsubResult0) {
				parts = append(parts, procsubResult0)
				chars = append(chars, procsubResult1)
			} else if procsubResult1 != "" {
				chars = append(chars, procsubResult1)
			} else {
				chars = append(chars, self.Advance())
				if ctx == WORDCTXNORMAL {
					chars = append(chars, self.Advance())
				}
			}
			continue
		}
		if ctx == WORDCTXNORMAL && ch == "(" && len(chars) > 0 && bracketDepth == 0 {
			isArrayAssign := false
			if len(chars) >= 3 && chars[len(chars)-2] == "+" && chars[len(chars)-1] == "=" {
				isArrayAssign = isArrayAssignmentPrefix(chars[:len(chars)-2])
			} else if chars[len(chars)-1] == "=" && len(chars) >= 2 {
				isArrayAssign = isArrayAssignmentPrefix(chars[:len(chars)-1])
			}
			if isArrayAssign && (atCommandStart || inAssignBuiltin) {
				self.syncToParser()
				arrayResult0, arrayResult1 := self.parser.parseArrayLiteral()
				self.syncFromParser()
				if !_isNilInterface(arrayResult0) {
					parts = append(parts, arrayResult0)
					chars = append(chars, arrayResult1)
				} else {
					break
				}
				continue
			}
		}
		if self.extglob && ctx == WORDCTXNORMAL && isExtglobPrefix(ch) && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "(" {
			chars = append(chars, self.Advance())
			chars = append(chars, self.Advance())
			content = self.parseMatchedPair("(", ")", MatchedPairFlagsEXTGLOB, false)
			chars = append(chars, content)
			chars = append(chars, ")")
			continue
		}
		if ctx == WORDCTXNORMAL && (self.parserState&ParserStateFlagsPSTEOFTOKEN) != 0 && self.eofToken != "" && ch == self.eofToken && bracketDepth == 0 {
			if !(len(chars) > 0) {
				chars = append(chars, self.Advance())
			}
			break
		}
		if ctx == WORDCTXNORMAL && isMetachar(ch) && bracketDepth == 0 {
			break
		}
		chars = append(chars, self.Advance())
	}
	if bracketDepth > 0 && bracketStartPos != -1 && self.AtEnd() {
		panic(NewMatchedPairError("unexpected EOF looking for `]'", bracketStartPos, 0))
	}
	if !(len(chars) > 0) {
		return nil
	}
	if len(parts) > 0 {
		return &Word{Value: strings.Join(chars, ""), Parts: parts, Kind: "word"}
	}
	return &Word{Value: strings.Join(chars, ""), Parts: nil, Kind: "word"}
}

func (self *Lexer) readWord() *Token {
	start := self.Pos
	if self.Pos >= self.Length {
		return nil
	}
	c := self.Peek()
	if c == "" {
		return nil
	}
	isProcsub := (c == "<" || c == ">") && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "("
	isRegexParen := self.wordContext == WORDCTXREGEX && (c == "(" || c == ")")
	if self.IsMetachar(c) && !isProcsub && !isRegexParen {
		return nil
	}
	word := self.readWordInternal(self.wordContext, self.atCommandStart, self.inArrayLiteral, self.inAssignBuiltin)
	if word == nil {
		return nil
	}
	return &Token{Type: TokenTypeWORD, Value: word.Value, Pos: start, Parts: nil, Word: word}
}

func (self *Lexer) NextToken() *Token {
	var tok *Token
	if self.tokenCache != nil {
		tok = self.tokenCache
		self.tokenCache = nil
		self.lastReadToken = tok
		return tok
	}
	self.SkipBlanks()
	if self.AtEnd() {
		tok = &Token{Type: TokenTypeEOF, Value: "", Pos: self.Pos}
		self.lastReadToken = tok
		return tok
	}
	if self.eofToken != "" && self.Peek() == self.eofToken && !((self.parserState & ParserStateFlagsPSTCASEPAT) != 0) && !((self.parserState & ParserStateFlagsPSTEOFTOKEN) != 0) {
		tok = &Token{Type: TokenTypeEOF, Value: "", Pos: self.Pos}
		self.lastReadToken = tok
		return tok
	}
	for self.skipComment() {
		self.SkipBlanks()
		if self.AtEnd() {
			tok = &Token{Type: TokenTypeEOF, Value: "", Pos: self.Pos}
			self.lastReadToken = tok
			return tok
		}
		if self.eofToken != "" && self.Peek() == self.eofToken && !((self.parserState & ParserStateFlagsPSTCASEPAT) != 0) && !((self.parserState & ParserStateFlagsPSTEOFTOKEN) != 0) {
			tok = &Token{Type: TokenTypeEOF, Value: "", Pos: self.Pos}
			self.lastReadToken = tok
			return tok
		}
	}
	tok = self.readOperator()
	if tok != nil {
		self.lastReadToken = tok
		return tok
	}
	tok = self.readWord()
	if tok != nil {
		self.lastReadToken = tok
		return tok
	}
	tok = &Token{Type: TokenTypeEOF, Value: "", Pos: self.Pos}
	self.lastReadToken = tok
	return tok
}

func (self *Lexer) PeekToken() *Token {
	if self.tokenCache == nil {
		savedLast := self.lastReadToken
		self.tokenCache = self.NextToken()
		self.lastReadToken = savedLast
	}
	return self.tokenCache
}

func (self *Lexer) readAnsiCQuote() (Node, string) {
	if self.AtEnd() || self.Peek() != "$" {
		return nil, ""
	}
	if self.Pos+1 >= self.Length || string(_runeAt(self.Source, self.Pos+1)) != "'" {
		return nil, ""
	}
	start := self.Pos
	self.Advance()
	self.Advance()
	contentChars := []string{}
	foundClose := false
	for !self.AtEnd() {
		ch := self.Peek()
		if ch == "'" {
			self.Advance()
			foundClose = true
			break
		} else if ch == "\\" {
			contentChars = append(contentChars, self.Advance())
			if !self.AtEnd() {
				contentChars = append(contentChars, self.Advance())
			}
		} else {
			contentChars = append(contentChars, self.Advance())
		}
	}
	if !foundClose {
		panic(NewMatchedPairError("unexpected EOF while looking for matching `''", start, 0))
	}
	text := substring(self.Source, start, self.Pos)
	content := strings.Join(contentChars, "")
	node := &AnsiCQuote{Content: content, Kind: "ansi-c"}
	return node, text
}

func (self *Lexer) syncToParser() {
	if self.parser != nil {
		self.parser.Pos = self.Pos
	}
}

func (self *Lexer) syncFromParser() {
	if self.parser != nil {
		self.Pos = self.parser.Pos
	}
}

func (self *Lexer) readLocaleString() (Node, string, []Node) {
	if self.AtEnd() || self.Peek() != "$" {
		return nil, "", []Node{}
	}
	if self.Pos+1 >= self.Length || string(_runeAt(self.Source, self.Pos+1)) != "\"" {
		return nil, "", []Node{}
	}
	start := self.Pos
	self.Advance()
	self.Advance()
	contentChars := []string{}
	innerParts := []Node{}
	foundClose := false
	for !self.AtEnd() {
		ch := self.Peek()
		if ch == "\"" {
			self.Advance()
			foundClose = true
			break
		} else if ch == "\\" && self.Pos+1 < self.Length {
			nextCh := string(_runeAt(self.Source, self.Pos+1))
			if nextCh == "\n" {
				self.Advance()
				self.Advance()
			} else {
				contentChars = append(contentChars, self.Advance())
				contentChars = append(contentChars, self.Advance())
			}
		} else if ch == "$" && self.Pos+2 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "(" && string(_runeAt(self.Source, self.Pos+2)) == "(" {
			self.syncToParser()
			arithNode, arithText := self.parser.parseArithmeticExpansion()
			self.syncFromParser()
			if !_isNilInterface(arithNode) {
				innerParts = append(innerParts, arithNode)
				contentChars = append(contentChars, arithText)
			} else {
				self.syncToParser()
				cmdsubNode, cmdsubText := self.parser.parseCommandSubstitution()
				self.syncFromParser()
				if !_isNilInterface(cmdsubNode) {
					innerParts = append(innerParts, cmdsubNode)
					contentChars = append(contentChars, cmdsubText)
				} else {
					contentChars = append(contentChars, self.Advance())
				}
			}
		} else if isExpansionStart(self.Source, self.Pos, "$(") {
			self.syncToParser()
			cmdsubNode, cmdsubText := self.parser.parseCommandSubstitution()
			self.syncFromParser()
			if !_isNilInterface(cmdsubNode) {
				innerParts = append(innerParts, cmdsubNode)
				contentChars = append(contentChars, cmdsubText)
			} else {
				contentChars = append(contentChars, self.Advance())
			}
		} else if ch == "$" {
			self.syncToParser()
			paramNode, paramText := self.parser.parseParamExpansion(false)
			self.syncFromParser()
			if !_isNilInterface(paramNode) {
				innerParts = append(innerParts, paramNode)
				contentChars = append(contentChars, paramText)
			} else {
				contentChars = append(contentChars, self.Advance())
			}
		} else if ch == "`" {
			self.syncToParser()
			cmdsubNode, cmdsubText := self.parser.parseBacktickSubstitution()
			self.syncFromParser()
			if !_isNilInterface(cmdsubNode) {
				innerParts = append(innerParts, cmdsubNode)
				contentChars = append(contentChars, cmdsubText)
			} else {
				contentChars = append(contentChars, self.Advance())
			}
		} else {
			contentChars = append(contentChars, self.Advance())
		}
	}
	if !foundClose {
		self.Pos = start
		return nil, "", []Node{}
	}
	content := strings.Join(contentChars, "")
	text := "$\"" + content + "\""
	return &LocaleString{Content: content, Kind: "locale"}, text, innerParts
}

func (self *Lexer) updateDolbraceForOp(op string, hasParam bool) {
	if self.dolbraceState == DolbraceStateNONE {
		return
	}
	if op == "" || _runeLen(op) == 0 {
		return
	}
	firstChar := string(_runeAt(op, 0))
	if self.dolbraceState == DolbraceStatePARAM && hasParam {
		if strings.Contains("%#^,", firstChar) {
			self.dolbraceState = DolbraceStateQUOTE
			return
		}
		if firstChar == "/" {
			self.dolbraceState = DolbraceStateQUOTE2
			return
		}
	}
	if self.dolbraceState == DolbraceStatePARAM {
		if strings.Contains("#%^,~:-=?+/", firstChar) {
			self.dolbraceState = DolbraceStateOP
		}
	}
}

func (self *Lexer) consumeParamOperator() string {
	if self.AtEnd() {
		return ""
	}
	ch := self.Peek()
	var nextCh string
	if ch == ":" {
		self.Advance()
		if self.AtEnd() {
			return ":"
		}
		nextCh = self.Peek()
		if isSimpleParamOp(nextCh) {
			self.Advance()
			return ":" + nextCh
		}
		return ":"
	}
	if isSimpleParamOp(ch) {
		self.Advance()
		return ch
	}
	if ch == "#" {
		self.Advance()
		if !self.AtEnd() && self.Peek() == "#" {
			self.Advance()
			return "##"
		}
		return "#"
	}
	if ch == "%" {
		self.Advance()
		if !self.AtEnd() && self.Peek() == "%" {
			self.Advance()
			return "%%"
		}
		return "%"
	}
	if ch == "/" {
		self.Advance()
		if !self.AtEnd() {
			nextCh = self.Peek()
			if nextCh == "/" {
				self.Advance()
				return "//"
			} else if nextCh == "#" {
				self.Advance()
				return "/#"
			} else if nextCh == "%" {
				self.Advance()
				return "/%"
			}
		}
		return "/"
	}
	if ch == "^" {
		self.Advance()
		if !self.AtEnd() && self.Peek() == "^" {
			self.Advance()
			return "^^"
		}
		return "^"
	}
	if ch == "," {
		self.Advance()
		if !self.AtEnd() && self.Peek() == "," {
			self.Advance()
			return ",,"
		}
		return ","
	}
	if ch == "@" {
		self.Advance()
		return "@"
	}
	return ""
}

func (self *Lexer) paramSubscriptHasClose(startPos int) bool {
	depth := 1
	i := startPos + 1
	quote := NewQuoteState()
	for i < self.Length {
		c := string(_runeAt(self.Source, i))
		if quote.Single {
			if c == "'" {
				quote.Single = false
			}
			i++
			continue
		}
		if quote.Double {
			if c == "\\" && i+1 < self.Length {
				i += 2
				continue
			}
			if c == "\"" {
				quote.Double = false
			}
			i++
			continue
		}
		if c == "'" {
			quote.Single = true
			i++
			continue
		}
		if c == "\"" {
			quote.Double = true
			i++
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
			depth++
		} else if c == "]" {
			depth--
			if depth == 0 {
				return true
			}
		}
		i++
	}
	return false
}

func (self *Lexer) consumeParamName() string {
	if self.AtEnd() {
		return ""
	}
	ch := self.Peek()
	if isSpecialParam(ch) {
		if ch == "$" && self.Pos+1 < self.Length && strings.Contains("{'\"", string(_runeAt(self.Source, self.Pos+1))) {
			return ""
		}
		self.Advance()
		return ch
	}
	if _strIsDigit(ch) {
		nameChars := []string{}
		for !self.AtEnd() && _strIsDigit(self.Peek()) {
			nameChars = append(nameChars, self.Advance())
		}
		return strings.Join(nameChars, "")
	}
	if _strIsAlpha(ch) || ch == "_" {
		nameChars := []string{}
		for !self.AtEnd() {
			c := self.Peek()
			if _strIsAlnum(c) || c == "_" {
				nameChars = append(nameChars, self.Advance())
			} else if c == "[" {
				if !self.paramSubscriptHasClose(self.Pos) {
					break
				}
				nameChars = append(nameChars, self.Advance())
				content := self.parseMatchedPair("[", "]", MatchedPairFlagsARRAYSUB, false)
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

func (self *Lexer) readParamExpansion(inDquote bool) (Node, string) {
	if self.AtEnd() || self.Peek() != "$" {
		return nil, ""
	}
	start := self.Pos
	self.Advance()
	if self.AtEnd() {
		self.Pos = start
		return nil, ""
	}
	ch := self.Peek()
	if ch == "{" {
		self.Advance()
		return self.readBracedParam(start, inDquote)
	}
	var text string
	if isSpecialParamUnbraced(ch) || isDigit(ch) || ch == "#" {
		self.Advance()
		text = substring(self.Source, start, self.Pos)
		return &ParamExpansion{Param: ch, Kind: "param"}, text
	}
	if _strIsAlpha(ch) || ch == "_" {
		nameStart := self.Pos
		for !self.AtEnd() {
			c := self.Peek()
			if _strIsAlnum(c) || c == "_" {
				self.Advance()
			} else {
				break
			}
		}
		name := substring(self.Source, nameStart, self.Pos)
		text = substring(self.Source, start, self.Pos)
		return &ParamExpansion{Param: name, Kind: "param"}, text
	}
	self.Pos = start
	return nil, ""
}

func (self *Lexer) readBracedParam(start int, inDquote bool) (Node, string) {
	if self.AtEnd() {
		panic(NewMatchedPairError("unexpected EOF looking for `}'", start, 0))
	}
	savedDolbrace := self.dolbraceState
	self.dolbraceState = DolbraceStatePARAM
	ch := self.Peek()
	if isFunsubChar(ch) {
		self.dolbraceState = savedDolbrace
		return self.readFunsub(start)
	}
	var param string
	var text string
	if ch == "#" {
		self.Advance()
		param = self.consumeParamName()
		if param != "" && !self.AtEnd() && self.Peek() == "}" {
			self.Advance()
			text = substring(self.Source, start, self.Pos)
			self.dolbraceState = savedDolbrace
			return &ParamLength{Param: param, Kind: "param-len"}, text
		}
		self.Pos = start + 2
	}
	var op string
	var arg string
	if ch == "!" {
		self.Advance()
		for !self.AtEnd() && isWhitespaceNoNewline(self.Peek()) {
			self.Advance()
		}
		param = self.consumeParamName()
		if param != "" {
			for !self.AtEnd() && isWhitespaceNoNewline(self.Peek()) {
				self.Advance()
			}
			if !self.AtEnd() && self.Peek() == "}" {
				self.Advance()
				text = substring(self.Source, start, self.Pos)
				self.dolbraceState = savedDolbrace
				return &ParamIndirect{Param: param, Kind: "param-indirect"}, text
			}
			if !self.AtEnd() && isAtOrStar(self.Peek()) {
				suffix := self.Advance()
				trailing := self.parseMatchedPair("{", "}", MatchedPairFlagsDOLBRACE, false)
				text = substring(self.Source, start, self.Pos)
				self.dolbraceState = savedDolbrace
				return &ParamIndirect{Param: param + suffix + trailing, Kind: "param-indirect"}, text
			}
			op = self.consumeParamOperator()
			if op == "" && !self.AtEnd() && !strings.Contains("}\"'`", self.Peek()) {
				op = self.Advance()
			}
			if op != "" && !strings.Contains("\"'`", op) {
				arg = self.parseMatchedPair("{", "}", MatchedPairFlagsDOLBRACE, false)
				text = substring(self.Source, start, self.Pos)
				self.dolbraceState = savedDolbrace
				return &ParamIndirect{Param: param, Op: op, Arg: arg, Kind: "param-indirect"}, text
			}
			if self.AtEnd() {
				self.dolbraceState = savedDolbrace
				panic(NewMatchedPairError("unexpected EOF looking for `}'", start, 0))
			}
			self.Pos = start + 2
		} else {
			self.Pos = start + 2
		}
	}
	param = self.consumeParamName()
	if !(param != "") {
		if !self.AtEnd() && (strings.Contains("-=+?", self.Peek()) || self.Peek() == ":" && self.Pos+1 < self.Length && isSimpleParamOp(string(_runeAt(self.Source, self.Pos+1)))) {
			param = ""
		} else {
			content := self.parseMatchedPair("{", "}", MatchedPairFlagsDOLBRACE, false)
			text = "${" + content + "}"
			self.dolbraceState = savedDolbrace
			return &ParamExpansion{Param: content, Kind: "param"}, text
		}
	}
	if self.AtEnd() {
		self.dolbraceState = savedDolbrace
		panic(NewMatchedPairError("unexpected EOF looking for `}'", start, 0))
	}
	if self.Peek() == "}" {
		self.Advance()
		text = substring(self.Source, start, self.Pos)
		self.dolbraceState = savedDolbrace
		return &ParamExpansion{Param: param, Kind: "param"}, text
	}
	op = self.consumeParamOperator()
	if op == "" {
		if !self.AtEnd() && self.Peek() == "$" && self.Pos+1 < self.Length && (string(_runeAt(self.Source, self.Pos+1)) == "\"" || string(_runeAt(self.Source, self.Pos+1)) == "'") {
			dollarCount := 1 + countConsecutiveDollarsBefore(self.Source, self.Pos)
			if (dollarCount % 2) == 1 {
				op = ""
			} else {
				op = self.Advance()
			}
		} else if !self.AtEnd() && self.Peek() == "`" {
			backtickPos := self.Pos
			self.Advance()
			for !self.AtEnd() && self.Peek() != "`" {
				bc := self.Peek()
				if bc == "\\" && self.Pos+1 < self.Length {
					nextC := string(_runeAt(self.Source, self.Pos+1))
					if isEscapeCharInBacktick(nextC) {
						self.Advance()
					}
				}
				self.Advance()
			}
			if self.AtEnd() {
				self.dolbraceState = savedDolbrace
				panic(NewParseError("Unterminated backtick", backtickPos, 0))
			}
			self.Advance()
			op = "`"
		} else if !self.AtEnd() && self.Peek() == "$" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "{" {
			op = ""
		} else if !self.AtEnd() && (self.Peek() == "'" || self.Peek() == "\"") {
			op = ""
		} else if !self.AtEnd() && self.Peek() == "\\" {
			op = self.Advance()
			if !self.AtEnd() {
				op += self.Advance()
			}
		} else {
			op = self.Advance()
		}
	}
	self.updateDolbraceForOp(op, _runeLen(param) > 0)
	func() {
		defer func() {
			if e := recover(); e != nil {
				self.dolbraceState = savedDolbrace
				panic(e)
			}
		}()
		flags := func() int {
			if inDquote {
				return MatchedPairFlagsDQUOTE
			} else {
				return MatchedPairFlagsNONE
			}
		}()
		paramEndsWithDollar := param != "" && strings.HasSuffix(param, "$")
		arg = self.collectParamArgument(flags, paramEndsWithDollar)
	}()
	if (op == "<" || op == ">") && strings.HasPrefix(arg, "(") && strings.HasSuffix(arg, ")") {
		inner := _Substring(arg, 1, _runeLen(arg)-1)
		func() {
			defer func() {
				if r := recover(); r != nil {
				}
			}()
			subParser := NewParser(inner, true, self.parser.extglob)
			parsed := subParser.ParseList(true)
			if !_isNilInterface(parsed) && subParser.AtEnd() {
				formatted := formatCmdsubNode(parsed, 0, true, false, true)
				arg = "(" + formatted + ")"
			}
		}()
	}
	text = "${" + param + op + arg + "}"
	self.dolbraceState = savedDolbrace
	return &ParamExpansion{Param: param, Op: op, Arg: arg, Kind: "param"}, text
}

func (self *Lexer) readFunsub(start int) (Node, string) {
	return self.parser.parseFunsub(start)
}

type Word struct {
	Value string
	Parts []Node
	Kind  string
}

func (self *Word) GetKind() string { return self.Kind }

func (self *Word) ToSexp() string {
	value := self.Value
	value = self.expandAllAnsiCQuotes(value)
	value = self.stripLocaleStringDollars(value)
	value = self.normalizeArrayWhitespace(value)
	value = self.formatCommandSubstitutions(value, false)
	value = self.normalizeParamExpansionNewlines(value)
	value = self.stripArithLineContinuations(value)
	value = self.doubleCtlescSmart(value)
	value = strings.ReplaceAll(value, "", "")
	value = strings.ReplaceAll(value, "\\", "\\\\")
	if strings.HasSuffix(value, "\\\\") && !strings.HasSuffix(value, "\\\\\\\\") {
		value = value + "\\\\"
	}
	escaped := strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(value, "\"", "\\\""), "\n", "\\n"), "\t", "\\t")
	return "(word \"" + escaped + "\")"
}

func (self *Word) appendWithCtlesc(result *[]byte, byteVal int) {
	*result = append(*result, byte(byteVal))
}

func (self *Word) doubleCtlescSmart(value string) string {
	result := []string{}
	quote := NewQuoteState()
	for _, c := range value {
		if c == '\'' && !quote.Double {
			quote.Single = !quote.Single
		} else if c == '"' && !quote.Single {
			quote.Double = !quote.Double
		}
		result = append(result, string(c))
		if c == '\x01' {
			if quote.Double {
				bsCount := 0
				for _, j := range Range(len(result)-2, -1, -1) {
					if result[j] == "\\" {
						bsCount++
					} else {
						break
					}
				}
				if (bsCount % 2) == 0 {
					result = append(result, "")
				}
			} else {
				result = append(result, "")
			}
		}
	}
	return strings.Join(result, "")
}

func (self *Word) normalizeParamExpansionNewlines(value string) string {
	result := []string{}
	i := 0
	quote := NewQuoteState()
	for i < _runeLen(value) {
		c := string(_runeAt(value, i))
		if c == "'" && !quote.Double {
			quote.Single = !quote.Single
			result = append(result, c)
			i++
		} else if c == "\"" && !quote.Single {
			quote.Double = !quote.Double
			result = append(result, c)
			i++
		} else if isExpansionStart(value, i, "${") && !quote.Single {
			result = append(result, "$")
			result = append(result, "{")
			i += 2
			hadLeadingNewline := i < _runeLen(value) && string(_runeAt(value, i)) == "\n"
			if hadLeadingNewline {
				result = append(result, " ")
				i++
			}
			depth := 1
			for i < _runeLen(value) && depth > 0 {
				ch := string(_runeAt(value, i))
				if ch == "\\" && i+1 < _runeLen(value) && !quote.Single {
					if string(_runeAt(value, i+1)) == "\n" {
						i += 2
						continue
					}
					result = append(result, ch)
					result = append(result, string(_runeAt(value, i+1)))
					i += 2
					continue
				}
				if ch == "'" && !quote.Double {
					quote.Single = !quote.Single
				} else if ch == "\"" && !quote.Single {
					quote.Double = !quote.Double
				} else if !quote.InQuotes() {
					if ch == "{" {
						depth++
					} else if ch == "}" {
						depth--
						if depth == 0 {
							if hadLeadingNewline {
								result = append(result, " ")
							}
							result = append(result, ch)
							i++
							break
						}
					}
				}
				result = append(result, ch)
				i++
			}
		} else {
			result = append(result, c)
			i++
		}
	}
	return strings.Join(result, "")
}

func (self *Word) shSingleQuote(s string) string {
	if !(s != "") {
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

func (self *Word) ansiCToBytes(inner string) []byte {
	result := make([]byte, 0)
	i := 0
	for i < _runeLen(inner) {
		if string(_runeAt(inner, i)) == "\\" && i+1 < _runeLen(inner) {
			c := string(_runeAt(inner, i+1))
			simple := getAnsiEscape(c)
			if simple >= 0 {
				result = append(result, byte(simple))
				i += 2
			} else if c == "'" {
				result = append(result, byte(39))
				i += 2
			} else if c == "x" {
				if i+2 < _runeLen(inner) && string(_runeAt(inner, i+2)) == "{" {
					j := i + 3
					for j < _runeLen(inner) && isHexDigit(string(_runeAt(inner, j))) {
						j++
					}
					hexStr := substring(inner, i+3, j)
					if j < _runeLen(inner) && string(_runeAt(inner, j)) == "}" {
						j++
					}
					if !(hexStr != "") {
						return result
					}
					byteVal := (_parseInt(hexStr, 16) & 255)
					if byteVal == 0 {
						return result
					}
					self.appendWithCtlesc(&result, byteVal)
					i = j
				} else {
					j := i + 2
					for j < _runeLen(inner) && j < i+4 && isHexDigit(string(_runeAt(inner, j))) {
						j++
					}
					if j > i+2 {
						byteVal := _parseInt(substring(inner, i+2, j), 16)
						if byteVal == 0 {
							return result
						}
						self.appendWithCtlesc(&result, byteVal)
						i = j
					} else {
						result = append(result, byte(int(string(_runeAt(inner, i))[0])))
						i++
					}
				}
			} else if c == "u" {
				j := i + 2
				for j < _runeLen(inner) && j < i+6 && isHexDigit(string(_runeAt(inner, j))) {
					j++
				}
				if j > i+2 {
					codepoint := _parseInt(substring(inner, i+2, j), 16)
					if codepoint == 0 {
						return result
					}
					result = append(result, []byte(string(rune(codepoint)))...)
					i = j
				} else {
					result = append(result, byte(int(string(_runeAt(inner, i))[0])))
					i++
				}
			} else if c == "U" {
				j := i + 2
				for j < _runeLen(inner) && j < i+10 && isHexDigit(string(_runeAt(inner, j))) {
					j++
				}
				if j > i+2 {
					codepoint := _parseInt(substring(inner, i+2, j), 16)
					if codepoint == 0 {
						return result
					}
					result = append(result, []byte(string(rune(codepoint)))...)
					i = j
				} else {
					result = append(result, byte(int(string(_runeAt(inner, i))[0])))
					i++
				}
			} else if c == "c" {
				if i+3 <= _runeLen(inner) {
					ctrlChar := string(_runeAt(inner, i+2))
					skipExtra := 0
					if ctrlChar == "\\" && i+4 <= _runeLen(inner) && string(_runeAt(inner, i+3)) == "\\" {
						skipExtra = 1
					}
					ctrlVal := (int(ctrlChar[0]) & 31)
					if ctrlVal == 0 {
						return result
					}
					self.appendWithCtlesc(&result, ctrlVal)
					i += 3 + skipExtra
				} else {
					result = append(result, byte(int(string(_runeAt(inner, i))[0])))
					i++
				}
			} else if c == "0" {
				j := i + 2
				for j < _runeLen(inner) && j < i+4 && isOctalDigit(string(_runeAt(inner, j))) {
					j++
				}
				if j > i+2 {
					byteVal := (_parseInt(substring(inner, i+1, j), 8) & 255)
					if byteVal == 0 {
						return result
					}
					self.appendWithCtlesc(&result, byteVal)
					i = j
				} else {
					return result
				}
			} else if c >= "1" && c <= "7" {
				j := i + 1
				for j < _runeLen(inner) && j < i+4 && isOctalDigit(string(_runeAt(inner, j))) {
					j++
				}
				byteVal := (_parseInt(substring(inner, i+1, j), 8) & 255)
				if byteVal == 0 {
					return result
				}
				self.appendWithCtlesc(&result, byteVal)
				i = j
			} else {
				result = append(result, byte(92))
				result = append(result, byte(int(c[0])))
				i += 2
			}
		} else {
			result = append(result, []byte(string(_runeAt(inner, i)))...)
			i++
		}
	}
	return result
}

func (self *Word) expandAnsiCEscapes(value string) string {
	if !(strings.HasPrefix(value, "'") && strings.HasSuffix(value, "'")) {
		return value
	}
	inner := substring(value, 1, _runeLen(value)-1)
	literalBytes := self.ansiCToBytes(inner)
	literalStr := string(literalBytes)
	return self.shSingleQuote(literalStr)
}

func (self *Word) expandAllAnsiCQuotes(value string) string {
	result := []string{}
	i := 0
	quote := NewQuoteState()
	inBacktick := false
	braceDepth := 0
	for i < _runeLen(value) {
		ch := string(_runeAt(value, i))
		if ch == "`" && !quote.Single {
			inBacktick = !inBacktick
			result = append(result, ch)
			i++
			continue
		}
		if inBacktick {
			if ch == "\\" && i+1 < _runeLen(value) {
				result = append(result, ch)
				result = append(result, string(_runeAt(value, i+1)))
				i += 2
			} else {
				result = append(result, ch)
				i++
			}
			continue
		}
		if !quote.Single {
			if isExpansionStart(value, i, "${") {
				braceDepth++
				quote.Push()
				result = append(result, "${")
				i += 2
				continue
			} else if ch == "}" && braceDepth > 0 && !quote.Double {
				braceDepth--
				result = append(result, ch)
				quote.Pop()
				i++
				continue
			}
		}
		effectiveInDquote := quote.Double
		if ch == "'" && !effectiveInDquote {
			isAnsiC := !quote.Single && i > 0 && string(_runeAt(value, i-1)) == "$" && (countConsecutiveDollarsBefore(value, i-1)%2) == 0
			if !isAnsiC {
				quote.Single = !quote.Single
			}
			result = append(result, ch)
			i++
		} else if ch == "\"" && !quote.Single {
			quote.Double = !quote.Double
			result = append(result, ch)
			i++
		} else if ch == "\\" && i+1 < _runeLen(value) && !quote.Single {
			result = append(result, ch)
			result = append(result, string(_runeAt(value, i+1)))
			i += 2
		} else if startsWithAt(value, i, "$'") && !quote.Single && !effectiveInDquote && (countConsecutiveDollarsBefore(value, i)%2) == 0 {
			j := i + 2
			for j < _runeLen(value) {
				if string(_runeAt(value, j)) == "\\" && j+1 < _runeLen(value) {
					j += 2
				} else if string(_runeAt(value, j)) == "'" {
					j++
					break
				} else {
					j++
				}
			}
			ansiStr := substring(value, i, j)
			expanded := self.expandAnsiCEscapes(substring(ansiStr, 1, _runeLen(ansiStr)))
			outerInDquote := quote.OuterDouble()
			if braceDepth > 0 && outerInDquote && strings.HasPrefix(expanded, "'") && strings.HasSuffix(expanded, "'") {
				inner := substring(expanded, 1, _runeLen(expanded)-1)
				if strings.Index(inner, "") == -1 {
					resultStr := strings.Join(result, "")
					inPattern := false
					lastBraceIdx := strings.LastIndex(resultStr, "${")
					if lastBraceIdx >= 0 {
						afterBrace := _Substring(resultStr, lastBraceIdx+2, _runeLen(resultStr))
						varNameLen := 0
						if afterBrace != "" {
							if strings.Contains("@*#?-$!0123456789_", string(_runeAt(afterBrace, 0))) {
								varNameLen = 1
							} else if _strIsAlpha(string(_runeAt(afterBrace, 0))) || string(_runeAt(afterBrace, 0)) == "_" {
								for varNameLen < _runeLen(afterBrace) {
									c := string(_runeAt(afterBrace, varNameLen))
									if !(_strIsAlnum(c) || c == "_") {
										break
									}
									varNameLen++
								}
							}
						}
						if varNameLen > 0 && varNameLen < _runeLen(afterBrace) && !strings.Contains("#?-", string(_runeAt(afterBrace, 0))) {
							opStart := _Substring(afterBrace, varNameLen, _runeLen(afterBrace))
							if strings.HasPrefix(opStart, "@") && _runeLen(opStart) > 1 {
								opStart = _Substring(opStart, 1, _runeLen(opStart))
							}
							for _, op := range []string{"//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"} {
								if strings.HasPrefix(opStart, op) {
									inPattern = true
									break
								}
							}
							if !inPattern && opStart != "" && !strings.Contains("%#/^,~:+-=?", string(_runeAt(opStart, 0))) {
								for _, op := range []string{"//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"} {
									if strings.Contains(opStart, op) {
										inPattern = true
										break
									}
								}
							}
						} else if varNameLen == 0 && _runeLen(afterBrace) > 1 {
							firstChar := string(_runeAt(afterBrace, 0))
							if !strings.Contains("%#/^,", firstChar) {
								rest := _Substring(afterBrace, 1, _runeLen(afterBrace))
								for _, op := range []string{"//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"} {
									if strings.Contains(rest, op) {
										inPattern = true
										break
									}
								}
							}
						}
					}
					if !inPattern {
						expanded = inner
					}
				}
			}
			result = append(result, expanded)
			i = j
		} else {
			result = append(result, ch)
			i++
		}
	}
	return strings.Join(result, "")
}

func (self *Word) stripLocaleStringDollars(value string) string {
	result := []string{}
	i := 0
	braceDepth := 0
	bracketDepth := 0
	quote := NewQuoteState()
	braceQuote := NewQuoteState()
	bracketInDoubleQuote := false
	for i < _runeLen(value) {
		ch := string(_runeAt(value, i))
		if ch == "\\" && i+1 < _runeLen(value) && !quote.Single && !braceQuote.Single {
			result = append(result, ch)
			result = append(result, string(_runeAt(value, i+1)))
			i += 2
		} else if startsWithAt(value, i, "${") && !quote.Single && !braceQuote.Single && (i == 0 || string(_runeAt(value, i-1)) != "$") {
			braceDepth++
			braceQuote.Double = false
			braceQuote.Single = false
			result = append(result, "$")
			result = append(result, "{")
			i += 2
		} else if ch == "}" && braceDepth > 0 && !quote.Single && !braceQuote.Double && !braceQuote.Single {
			braceDepth--
			result = append(result, ch)
			i++
		} else if ch == "[" && braceDepth > 0 && !quote.Single && !braceQuote.Double {
			bracketDepth++
			bracketInDoubleQuote = false
			result = append(result, ch)
			i++
		} else if ch == "]" && bracketDepth > 0 && !quote.Single && !bracketInDoubleQuote {
			bracketDepth--
			result = append(result, ch)
			i++
		} else if ch == "'" && !quote.Double && braceDepth == 0 {
			quote.Single = !quote.Single
			result = append(result, ch)
			i++
		} else if ch == "\"" && !quote.Single && braceDepth == 0 {
			quote.Double = !quote.Double
			result = append(result, ch)
			i++
		} else if ch == "\"" && !quote.Single && bracketDepth > 0 {
			bracketInDoubleQuote = !bracketInDoubleQuote
			result = append(result, ch)
			i++
		} else if ch == "\"" && !quote.Single && !braceQuote.Single && braceDepth > 0 {
			braceQuote.Double = !braceQuote.Double
			result = append(result, ch)
			i++
		} else if ch == "'" && !quote.Double && !braceQuote.Double && braceDepth > 0 {
			braceQuote.Single = !braceQuote.Single
			result = append(result, ch)
			i++
		} else if startsWithAt(value, i, "$\"") && !quote.Single && !braceQuote.Single && (braceDepth > 0 || bracketDepth > 0 || !quote.Double) && !braceQuote.Double && !bracketInDoubleQuote {
			dollarCount := 1 + countConsecutiveDollarsBefore(value, i)
			if (dollarCount % 2) == 1 {
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
				i++
			}
		} else {
			result = append(result, ch)
			i++
		}
	}
	return strings.Join(result, "")
}

func (self *Word) normalizeArrayWhitespace(value string) string {
	i := 0
	if !(i < _runeLen(value) && (_strIsAlpha(string(_runeAt(value, i))) || string(_runeAt(value, i)) == "_")) {
		return value
	}
	i++
	for i < _runeLen(value) && (_strIsAlnum(string(_runeAt(value, i))) || string(_runeAt(value, i)) == "_") {
		i++
	}
	for i < _runeLen(value) && string(_runeAt(value, i)) == "[" {
		depth := 1
		i++
		for i < _runeLen(value) && depth > 0 {
			if string(_runeAt(value, i)) == "[" {
				depth++
			} else if string(_runeAt(value, i)) == "]" {
				depth--
			}
			i++
		}
		if depth != 0 {
			return value
		}
	}
	if i < _runeLen(value) && string(_runeAt(value, i)) == "+" {
		i++
	}
	if !(i+1 < _runeLen(value) && string(_runeAt(value, i)) == "=" && string(_runeAt(value, i+1)) == "(") {
		return value
	}
	prefix := substring(value, 0, i+1)
	openParenPos := i + 1
	var closeParenPos int
	if strings.HasSuffix(value, ")") {
		closeParenPos = _runeLen(value) - 1
	} else {
		closeParenPos = self.findMatchingParen(value, openParenPos)
		if closeParenPos < 0 {
			return value
		}
	}
	inner := substring(value, openParenPos+1, closeParenPos)
	suffix := substring(value, closeParenPos+1, _runeLen(value))
	result := self.normalizeArrayInner(inner)
	return prefix + "(" + result + ")" + suffix
}

func (self *Word) findMatchingParen(value string, openPos int) int {
	if openPos >= _runeLen(value) || string(_runeAt(value, openPos)) != "(" {
		return -1
	}
	i := openPos + 1
	depth := 1
	quote := NewQuoteState()
	for i < _runeLen(value) && depth > 0 {
		ch := string(_runeAt(value, i))
		if ch == "\\" && i+1 < _runeLen(value) && !quote.Single {
			i += 2
			continue
		}
		if ch == "'" && !quote.Double {
			quote.Single = !quote.Single
			i++
			continue
		}
		if ch == "\"" && !quote.Single {
			quote.Double = !quote.Double
			i++
			continue
		}
		if quote.Single || quote.Double {
			i++
			continue
		}
		if ch == "#" {
			for i < _runeLen(value) && string(_runeAt(value, i)) != "\n" {
				i++
			}
			continue
		}
		if ch == "(" {
			depth++
		} else if ch == ")" {
			depth--
			if depth == 0 {
				return i
			}
		}
		i++
	}
	return -1
}

func (self *Word) normalizeArrayInner(inner string) string {
	normalized := []string{}
	i := 0
	inWhitespace := true
	braceDepth := 0
	bracketDepth := 0
	for i < _runeLen(inner) {
		ch := string(_runeAt(inner, i))
		if isWhitespace(ch) {
			if !inWhitespace && len(normalized) > 0 && braceDepth == 0 && bracketDepth == 0 {
				normalized = append(normalized, " ")
				inWhitespace = true
			}
			if braceDepth > 0 || bracketDepth > 0 {
				normalized = append(normalized, ch)
			}
			i++
		} else if ch == "'" {
			inWhitespace = false
			j := i + 1
			for j < _runeLen(inner) && string(_runeAt(inner, j)) != "'" {
				j++
			}
			normalized = append(normalized, substring(inner, i, j+1))
			i = j + 1
		} else if ch == "\"" {
			inWhitespace = false
			j := i + 1
			dqContent := []string{"\""}
			dqBraceDepth := 0
			for j < _runeLen(inner) {
				if string(_runeAt(inner, j)) == "\\" && j+1 < _runeLen(inner) {
					if string(_runeAt(inner, j+1)) == "\n" {
						j += 2
					} else {
						dqContent = append(dqContent, string(_runeAt(inner, j)))
						dqContent = append(dqContent, string(_runeAt(inner, j+1)))
						j += 2
					}
				} else if isExpansionStart(inner, j, "${") {
					dqContent = append(dqContent, "${")
					dqBraceDepth++
					j += 2
				} else if string(_runeAt(inner, j)) == "}" && dqBraceDepth > 0 {
					dqContent = append(dqContent, "}")
					dqBraceDepth--
					j++
				} else if string(_runeAt(inner, j)) == "\"" && dqBraceDepth == 0 {
					dqContent = append(dqContent, "\"")
					j++
					break
				} else {
					dqContent = append(dqContent, string(_runeAt(inner, j)))
					j++
				}
			}
			normalized = append(normalized, strings.Join(dqContent, ""))
			i = j
		} else if ch == "\\" && i+1 < _runeLen(inner) {
			if string(_runeAt(inner, i+1)) == "\n" {
				i += 2
			} else {
				inWhitespace = false
				normalized = append(normalized, substring(inner, i, i+2))
				i += 2
			}
		} else if isExpansionStart(inner, i, "$((") {
			inWhitespace = false
			j := i + 3
			depth := 1
			for j < _runeLen(inner) && depth > 0 {
				if j+1 < _runeLen(inner) && string(_runeAt(inner, j)) == "(" && string(_runeAt(inner, j+1)) == "(" {
					depth++
					j += 2
				} else if j+1 < _runeLen(inner) && string(_runeAt(inner, j)) == ")" && string(_runeAt(inner, j+1)) == ")" {
					depth--
					j += 2
				} else {
					j++
				}
			}
			normalized = append(normalized, substring(inner, i, j))
			i = j
		} else if isExpansionStart(inner, i, "$(") {
			inWhitespace = false
			j := i + 2
			depth := 1
			for j < _runeLen(inner) && depth > 0 {
				if string(_runeAt(inner, j)) == "(" && j > 0 && string(_runeAt(inner, j-1)) == "$" {
					depth++
				} else if string(_runeAt(inner, j)) == ")" {
					depth--
				} else if string(_runeAt(inner, j)) == "'" {
					j++
					for j < _runeLen(inner) && string(_runeAt(inner, j)) != "'" {
						j++
					}
				} else if string(_runeAt(inner, j)) == "\"" {
					j++
					for j < _runeLen(inner) {
						if string(_runeAt(inner, j)) == "\\" && j+1 < _runeLen(inner) {
							j += 2
							continue
						}
						if string(_runeAt(inner, j)) == "\"" {
							break
						}
						j++
					}
				}
				j++
			}
			normalized = append(normalized, substring(inner, i, j))
			i = j
		} else if (ch == "<" || ch == ">") && i+1 < _runeLen(inner) && string(_runeAt(inner, i+1)) == "(" {
			inWhitespace = false
			j := i + 2
			depth := 1
			for j < _runeLen(inner) && depth > 0 {
				if string(_runeAt(inner, j)) == "(" {
					depth++
				} else if string(_runeAt(inner, j)) == ")" {
					depth--
				} else if string(_runeAt(inner, j)) == "'" {
					j++
					for j < _runeLen(inner) && string(_runeAt(inner, j)) != "'" {
						j++
					}
				} else if string(_runeAt(inner, j)) == "\"" {
					j++
					for j < _runeLen(inner) {
						if string(_runeAt(inner, j)) == "\\" && j+1 < _runeLen(inner) {
							j += 2
							continue
						}
						if string(_runeAt(inner, j)) == "\"" {
							break
						}
						j++
					}
				}
				j++
			}
			normalized = append(normalized, substring(inner, i, j))
			i = j
		} else if isExpansionStart(inner, i, "${") {
			inWhitespace = false
			normalized = append(normalized, "${")
			braceDepth++
			i += 2
		} else if ch == "{" && braceDepth > 0 {
			normalized = append(normalized, ch)
			braceDepth++
			i++
		} else if ch == "}" && braceDepth > 0 {
			normalized = append(normalized, ch)
			braceDepth--
			i++
		} else if ch == "#" && braceDepth == 0 && inWhitespace {
			for i < _runeLen(inner) && string(_runeAt(inner, i)) != "\n" {
				i++
			}
		} else if ch == "[" {
			if inWhitespace || bracketDepth > 0 {
				bracketDepth++
			}
			inWhitespace = false
			normalized = append(normalized, ch)
			i++
		} else if ch == "]" && bracketDepth > 0 {
			normalized = append(normalized, ch)
			bracketDepth--
			i++
		} else {
			inWhitespace = false
			normalized = append(normalized, ch)
			i++
		}
	}
	return strings.TrimRight(strings.Join(normalized, ""), " \t\n\r")
}

func (self *Word) stripArithLineContinuations(value string) string {
	result := []string{}
	i := 0
	for i < _runeLen(value) {
		if isExpansionStart(value, i, "$((") {
			start := i
			i += 3
			depth := 2
			arithContent := []string{}
			firstCloseIdx := -1
			for i < _runeLen(value) && depth > 0 {
				if string(_runeAt(value, i)) == "(" {
					arithContent = append(arithContent, "(")
					depth++
					i++
					if depth > 1 {
						firstCloseIdx = -1
					}
				} else if string(_runeAt(value, i)) == ")" {
					if depth == 2 {
						firstCloseIdx = len(arithContent)
					}
					depth--
					if depth > 0 {
						arithContent = append(arithContent, ")")
					}
					i++
				} else if string(_runeAt(value, i)) == "\\" && i+1 < _runeLen(value) && string(_runeAt(value, i+1)) == "\n" {
					numBackslashes := 0
					j := len(arithContent) - 1
					for j >= 0 && arithContent[j] == "\n" {
						j--
					}
					for j >= 0 && arithContent[j] == "\\" {
						numBackslashes++
						j--
					}
					if (numBackslashes % 2) == 1 {
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
					arithContent = append(arithContent, string(_runeAt(value, i)))
					i++
					if depth == 1 {
						firstCloseIdx = -1
					}
				}
			}
			if depth == 0 || depth == 1 && firstCloseIdx != -1 {
				content := strings.Join(arithContent, "")
				if firstCloseIdx != -1 {
					content = _Substring(content, 0, firstCloseIdx)
					closing := func() string {
						if depth == 0 {
							return "))"
						} else {
							return ")"
						}
					}()
					result = append(result, "$(("+content+closing)
				} else {
					result = append(result, "$(("+content+")")
				}
			} else {
				result = append(result, substring(value, start, i))
			}
		} else {
			result = append(result, string(_runeAt(value, i)))
			i++
		}
	}
	return strings.Join(result, "")
}

func (self *Word) collectCmdsubs(node Node) []Node {
	result := []Node{}
	switch node := node.(type) {
	case *CommandSubstitution:
		result = append(result, node)
	case *Array:
		for _, elem := range node.Elements {
			for _, p := range elem.Parts {
				switch p := p.(type) {
				case *CommandSubstitution:
					result = append(result, p)
				default:
					p = p.(Node)
					result = append(result, self.collectCmdsubs(p)...)
				}
			}
		}
	case *ArithmeticExpansion:
		if node.Expression != nil {
			result = append(result, self.collectCmdsubs(node.Expression)...)
		}
	case *ArithBinaryOp:
		result = append(result, self.collectCmdsubs(node.Left)...)
		result = append(result, self.collectCmdsubs(node.Right)...)
	case *ArithComma:
		result = append(result, self.collectCmdsubs(node.Left)...)
		result = append(result, self.collectCmdsubs(node.Right)...)
	case *ArithUnaryOp:
		result = append(result, self.collectCmdsubs(node.Operand)...)
	case *ArithPreIncr:
		result = append(result, self.collectCmdsubs(node.Operand)...)
	case *ArithPostIncr:
		result = append(result, self.collectCmdsubs(node.Operand)...)
	case *ArithPreDecr:
		result = append(result, self.collectCmdsubs(node.Operand)...)
	case *ArithPostDecr:
		result = append(result, self.collectCmdsubs(node.Operand)...)
	case *ArithTernary:
		result = append(result, self.collectCmdsubs(node.Condition)...)
		result = append(result, self.collectCmdsubs(node.IfTrue)...)
		result = append(result, self.collectCmdsubs(node.IfFalse)...)
	case *ArithAssign:
		result = append(result, self.collectCmdsubs(node.Target)...)
		result = append(result, self.collectCmdsubs(node.Value)...)
	}
	return result
}

func (self *Word) collectProcsubs(node Node) []Node {
	result := []Node{}
	switch node := node.(type) {
	case *ProcessSubstitution:
		result = append(result, node)
	case *Array:
		for _, elem := range node.Elements {
			for _, p := range elem.Parts {
				switch p := p.(type) {
				case *ProcessSubstitution:
					result = append(result, p)
				default:
					p = p.(Node)
					result = append(result, self.collectProcsubs(p)...)
				}
			}
		}
	}
	return result
}

func (self *Word) formatCommandSubstitutions(value string, inArith bool) string {
	cmdsubParts := []Node{}
	procsubParts := []Node{}
	hasArith := false
	for _, p := range self.Parts {
		switch p := p.(type) {
		case *CommandSubstitution:
			cmdsubParts = append(cmdsubParts, p)
		case *ProcessSubstitution:
			procsubParts = append(procsubParts, p)
		case *ArithmeticExpansion:
			hasArith = true
		default:
			p = p.(Node)
			cmdsubParts = append(cmdsubParts, self.collectCmdsubs(p)...)
			procsubParts = append(procsubParts, self.collectProcsubs(p)...)
		}
	}
	hasBraceCmdsub := strings.Index(value, "${ ") != -1 || strings.Index(value, "${\t") != -1 || strings.Index(value, "${\n") != -1 || strings.Index(value, "${|") != -1
	hasUntrackedCmdsub := false
	hasUntrackedProcsub := false
	idx := 0
	scanQuote := NewQuoteState()
	for idx < _runeLen(value) {
		if string(_runeAt(value, idx)) == "\"" {
			scanQuote.Double = !scanQuote.Double
			idx++
		} else if string(_runeAt(value, idx)) == "'" && !scanQuote.Double {
			idx++
			for idx < _runeLen(value) && string(_runeAt(value, idx)) != "'" {
				idx++
			}
			if idx < _runeLen(value) {
				idx++
			}
		} else if startsWithAt(value, idx, "$(") && !startsWithAt(value, idx, "$((") && !isBackslashEscaped(value, idx) && !isDollarDollarParen(value, idx) {
			hasUntrackedCmdsub = true
			break
		} else if (startsWithAt(value, idx, "<(") || startsWithAt(value, idx, ">(")) && !scanQuote.Double {
			if idx == 0 || !_strIsAlnum(string(_runeAt(value, idx-1))) && !strings.Contains("\"'", string(_runeAt(value, idx-1))) {
				hasUntrackedProcsub = true
				break
			}
			idx++
		} else {
			idx++
		}
	}
	hasParamWithProcsubPattern := strings.Contains(value, "${") && (strings.Contains(value, "<(") || strings.Contains(value, ">("))
	if !(len(cmdsubParts) > 0) && !(len(procsubParts) > 0) && !hasBraceCmdsub && !hasUntrackedCmdsub && !hasUntrackedProcsub && !hasParamWithProcsubPattern {
		return value
	}
	result := []string{}
	i := 0
	cmdsubIdx := 0
	procsubIdx := 0
	mainQuote := NewQuoteState()
	extglobDepth := 0
	deprecatedArithDepth := 0
	arithDepth := 0
	arithParenDepth := 0
	for i < _runeLen(value) {
		if i > 0 && isExtglobPrefix(string(_runeAt(value, i-1))) && string(_runeAt(value, i)) == "(" && !isBackslashEscaped(value, i-1) {
			extglobDepth++
			result = append(result, string(_runeAt(value, i)))
			i++
			continue
		}
		if string(_runeAt(value, i)) == ")" && extglobDepth > 0 {
			extglobDepth--
			result = append(result, string(_runeAt(value, i)))
			i++
			continue
		}
		if startsWithAt(value, i, "$[") && !isBackslashEscaped(value, i) {
			deprecatedArithDepth++
			result = append(result, string(_runeAt(value, i)))
			i++
			continue
		}
		if string(_runeAt(value, i)) == "]" && deprecatedArithDepth > 0 {
			deprecatedArithDepth--
			result = append(result, string(_runeAt(value, i)))
			i++
			continue
		}
		if isExpansionStart(value, i, "$((") && !isBackslashEscaped(value, i) && hasArith {
			arithDepth++
			arithParenDepth += 2
			result = append(result, "$((")
			i += 3
			continue
		}
		if arithDepth > 0 && arithParenDepth == 2 && startsWithAt(value, i, "))") {
			arithDepth--
			arithParenDepth -= 2
			result = append(result, "))")
			i += 2
			continue
		}
		if arithDepth > 0 {
			if string(_runeAt(value, i)) == "(" {
				arithParenDepth++
				result = append(result, string(_runeAt(value, i)))
				i++
				continue
			} else if string(_runeAt(value, i)) == ")" {
				arithParenDepth--
				result = append(result, string(_runeAt(value, i)))
				i++
				continue
			}
		}
		var j int
		if isExpansionStart(value, i, "$((") && !hasArith {
			j = findCmdsubEnd(value, i+2)
			result = append(result, substring(value, i, j))
			if cmdsubIdx < len(cmdsubParts) {
				cmdsubIdx++
			}
			i = j
			continue
		}
		var inner string
		var node Node
		var formatted string
		var parser *Parser
		var parsed Node
		if startsWithAt(value, i, "$(") && !startsWithAt(value, i, "$((") && !isBackslashEscaped(value, i) && !isDollarDollarParen(value, i) {
			j = findCmdsubEnd(value, i+2)
			if extglobDepth > 0 {
				result = append(result, substring(value, i, j))
				if cmdsubIdx < len(cmdsubParts) {
					cmdsubIdx++
				}
				i = j
				continue
			}
			inner = substring(value, i+2, j-1)
			if cmdsubIdx < len(cmdsubParts) {
				node = cmdsubParts[cmdsubIdx]
				formatted = formatCmdsubNode(node.(*CommandSubstitution).Command, 0, false, false, false)
				cmdsubIdx++
			} else {
				func() {
					defer func() {
						if r := recover(); r != nil {
							formatted = inner
						}
					}()
					parser = NewParser(inner, false, false)
					parsed = parser.ParseList(true)
					formatted = func() string {
						if !_isNilInterface(parsed) {
							return formatCmdsubNode(parsed, 0, false, false, false)
						} else {
							return ""
						}
					}()
				}()
			}
			if strings.HasPrefix(formatted, "(") {
				result = append(result, "$( "+formatted+")")
			} else {
				result = append(result, "$("+formatted+")")
			}
			i = j
		} else if string(_runeAt(value, i)) == "`" && cmdsubIdx < len(cmdsubParts) {
			j = i + 1
			for j < _runeLen(value) {
				if string(_runeAt(value, j)) == "\\" && j+1 < _runeLen(value) {
					j += 2
					continue
				}
				if string(_runeAt(value, j)) == "`" {
					j++
					break
				}
				j++
			}
			result = append(result, substring(value, i, j))
			cmdsubIdx++
			i = j
		} else if isExpansionStart(value, i, "${") && i+2 < _runeLen(value) && isFunsubChar(string(_runeAt(value, i+2))) && !isBackslashEscaped(value, i) {
			j = findFunsubEnd(value, i+2)
			cmdsubNode := func() Node {
				if cmdsubIdx < len(cmdsubParts) {
					return cmdsubParts[cmdsubIdx]
				} else {
					return nil
				}
			}()
			if func() bool { _, ok := cmdsubNode.(*CommandSubstitution); return ok }() && cmdsubNode.(*CommandSubstitution).Brace {
				node = cmdsubNode
				formatted = formatCmdsubNode(node.(*CommandSubstitution).Command, 0, false, false, false)
				hasPipe := string(_runeAt(value, i+2)) == "|"
				prefix := func() string {
					if hasPipe {
						return "${|"
					} else {
						return "${ "
					}
				}()
				origInner := substring(value, i+2, j-1)
				endsWithNewline := strings.HasSuffix(origInner, "\n")
				var suffix string
				if !(formatted != "") || _strIsSpace(formatted) {
					suffix = "}"
				} else if strings.HasSuffix(formatted, "&") || strings.HasSuffix(formatted, "& ") {
					suffix = func() string {
						if strings.HasSuffix(formatted, "&") {
							return " }"
						} else {
							return "}"
						}
					}()
				} else if endsWithNewline {
					suffix = "\n }"
				} else {
					suffix = "; }"
				}
				result = append(result, prefix+formatted+suffix)
				cmdsubIdx++
			} else {
				result = append(result, substring(value, i, j))
			}
			i = j
		} else if (startsWithAt(value, i, ">(") || startsWithAt(value, i, "<(")) && !mainQuote.Double && deprecatedArithDepth == 0 && arithDepth == 0 {
			isProcsub := i == 0 || !_strIsAlnum(string(_runeAt(value, i-1))) && !strings.Contains("\"'", string(_runeAt(value, i-1)))
			if extglobDepth > 0 {
				j = findCmdsubEnd(value, i+2)
				result = append(result, substring(value, i, j))
				if procsubIdx < len(procsubParts) {
					procsubIdx++
				}
				i = j
				continue
			}
			var direction string
			var compact bool
			var stripped string
			if procsubIdx < len(procsubParts) {
				direction = string(_runeAt(value, i))
				j = findCmdsubEnd(value, i+2)
				node = procsubParts[procsubIdx]
				compact = startsWithSubshell(node.(*ProcessSubstitution).Command)
				formatted = formatCmdsubNode(node.(*ProcessSubstitution).Command, 0, true, compact, true)
				rawContent := substring(value, i+2, j-1)
				if node.(*ProcessSubstitution).Command.GetKind() == "subshell" {
					leadingWsEnd := 0
					for leadingWsEnd < _runeLen(rawContent) && strings.Contains(" \t\n", string(_runeAt(rawContent, leadingWsEnd))) {
						leadingWsEnd++
					}
					leadingWs := _Substring(rawContent, 0, leadingWsEnd)
					stripped = _Substring(rawContent, leadingWsEnd, _runeLen(rawContent))
					if strings.HasPrefix(stripped, "(") {
						if leadingWs != "" {
							normalizedWs := strings.ReplaceAll(strings.ReplaceAll(leadingWs, "\n", " "), "\t", " ")
							spaced := formatCmdsubNode(node.(*ProcessSubstitution).Command, 0, false, false, false)
							result = append(result, direction+"("+normalizedWs+spaced+")")
						} else {
							rawContent = strings.ReplaceAll(rawContent, "\\\n", "")
							result = append(result, direction+"("+rawContent+")")
						}
						procsubIdx++
						i = j
						continue
					}
				}
				rawContent = substring(value, i+2, j-1)
				rawStripped := strings.ReplaceAll(rawContent, "\\\n", "")
				if startsWithSubshell(node.(*ProcessSubstitution).Command) && formatted != rawStripped {
					result = append(result, direction+"("+rawStripped+")")
				} else {
					finalOutput := direction + "(" + formatted + ")"
					result = append(result, finalOutput)
				}
				procsubIdx++
				i = j
			} else if isProcsub && len(self.Parts) != 0 {
				direction = string(_runeAt(value, i))
				j = findCmdsubEnd(value, i+2)
				if j > _runeLen(value) || j > 0 && j <= _runeLen(value) && string(_runeAt(value, j-1)) != ")" {
					result = append(result, string(_runeAt(value, i)))
					i++
					continue
				}
				inner = substring(value, i+2, j-1)
				func() {
					defer func() {
						if r := recover(); r != nil {
							formatted = inner
						}
					}()
					parser = NewParser(inner, false, false)
					parsed = parser.ParseList(true)
					if !_isNilInterface(parsed) && parser.Pos == _runeLen(inner) && !strings.Contains(inner, "\n") {
						compact = startsWithSubshell(parsed)
						formatted = formatCmdsubNode(parsed, 0, true, compact, true)
					} else {
						formatted = inner
					}
				}()
				result = append(result, direction+"("+formatted+")")
				i = j
			} else if isProcsub {
				direction = string(_runeAt(value, i))
				j = findCmdsubEnd(value, i+2)
				if j > _runeLen(value) || j > 0 && j <= _runeLen(value) && string(_runeAt(value, j-1)) != ")" {
					result = append(result, string(_runeAt(value, i)))
					i++
					continue
				}
				inner = substring(value, i+2, j-1)
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
				result = append(result, string(_runeAt(value, i)))
				i++
			}
		} else if (isExpansionStart(value, i, "${ ") || isExpansionStart(value, i, "${\t") || isExpansionStart(value, i, "${\n") || isExpansionStart(value, i, "${|")) && !isBackslashEscaped(value, i) {
			prefix := strings.ReplaceAll(strings.ReplaceAll(substring(value, i, i+3), "\t", " "), "\n", " ")
			j = i + 3
			depth := 1
			for j < _runeLen(value) && depth > 0 {
				if string(_runeAt(value, j)) == "{" {
					depth++
				} else if string(_runeAt(value, j)) == "}" {
					depth--
				}
				j++
			}
			inner = substring(value, i+2, j-1)
			if strings.TrimSpace(inner) == "" {
				result = append(result, "${ }")
			} else {
				func() {
					defer func() {
						if r := recover(); r != nil {
							result = append(result, substring(value, i, j))
						}
					}()
					parser = NewParser(strings.TrimLeft(inner, " \t\n|"), false, false)
					parsed = parser.ParseList(true)
					if !_isNilInterface(parsed) {
						formatted = formatCmdsubNode(parsed, 0, false, false, false)
						formatted = strings.TrimRight(formatted, ";")
						var terminator string
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
		} else if isExpansionStart(value, i, "${") && !isBackslashEscaped(value, i) {
			j = i + 2
			depth := 1
			braceQuote := NewQuoteState()
			for j < _runeLen(value) && depth > 0 {
				c := string(_runeAt(value, j))
				if c == "\\" && j+1 < _runeLen(value) && !braceQuote.Single {
					j += 2
					continue
				}
				if c == "'" && !braceQuote.Double {
					braceQuote.Single = !braceQuote.Single
				} else if c == "\"" && !braceQuote.Single {
					braceQuote.Double = !braceQuote.Double
				} else if !braceQuote.InQuotes() {
					if isExpansionStart(value, j, "$(") && !startsWithAt(value, j, "$((") {
						j = findCmdsubEnd(value, j+2)
						continue
					}
					if c == "{" {
						depth++
					} else if c == "}" {
						depth--
					}
				}
				j++
			}
			if depth > 0 {
				inner = substring(value, i+2, j)
			} else {
				inner = substring(value, i+2, j-1)
			}
			formattedInner := self.formatCommandSubstitutions(inner, false)
			formattedInner = self.normalizeExtglobWhitespace(formattedInner)
			if depth == 0 {
				result = append(result, "${"+formattedInner+"}")
			} else {
				result = append(result, "${"+formattedInner)
			}
			i = j
		} else if string(_runeAt(value, i)) == "\"" {
			mainQuote.Double = !mainQuote.Double
			result = append(result, string(_runeAt(value, i)))
			i++
		} else if string(_runeAt(value, i)) == "'" && !mainQuote.Double {
			j = i + 1
			for j < _runeLen(value) && string(_runeAt(value, j)) != "'" {
				j++
			}
			if j < _runeLen(value) {
				j++
			}
			result = append(result, substring(value, i, j))
			i = j
		} else {
			result = append(result, string(_runeAt(value, i)))
			i++
		}
	}
	return strings.Join(result, "")
}

func (self *Word) normalizeExtglobWhitespace(value string) string {
	result := []string{}
	i := 0
	extglobQuote := NewQuoteState()
	deprecatedArithDepth := 0
	for i < _runeLen(value) {
		if string(_runeAt(value, i)) == "\"" {
			extglobQuote.Double = !extglobQuote.Double
			result = append(result, string(_runeAt(value, i)))
			i++
			continue
		}
		if startsWithAt(value, i, "$[") && !isBackslashEscaped(value, i) {
			deprecatedArithDepth++
			result = append(result, string(_runeAt(value, i)))
			i++
			continue
		}
		if string(_runeAt(value, i)) == "]" && deprecatedArithDepth > 0 {
			deprecatedArithDepth--
			result = append(result, string(_runeAt(value, i)))
			i++
			continue
		}
		if i+1 < _runeLen(value) && string(_runeAt(value, i+1)) == "(" {
			prefixChar := string(_runeAt(value, i))
			if strings.Contains("><", prefixChar) && !extglobQuote.Double && deprecatedArithDepth == 0 {
				result = append(result, prefixChar)
				result = append(result, "(")
				i += 2
				depth := 1
				patternParts := []string{}
				currentPart := []string{}
				hasPipe := false
				for i < _runeLen(value) && depth > 0 {
					if string(_runeAt(value, i)) == "\\" && i+1 < _runeLen(value) {
						currentPart = append(currentPart, _Substring(value, i, i+2))
						i += 2
						continue
					} else if string(_runeAt(value, i)) == "(" {
						depth++
						currentPart = append(currentPart, string(_runeAt(value, i)))
						i++
					} else if string(_runeAt(value, i)) == ")" {
						depth--
						if depth == 0 {
							partContent := strings.Join(currentPart, "")
							if strings.Contains(partContent, "<<") {
								patternParts = append(patternParts, partContent)
							} else if hasPipe {
								patternParts = append(patternParts, strings.TrimSpace(partContent))
							} else {
								patternParts = append(patternParts, partContent)
							}
							break
						}
						currentPart = append(currentPart, string(_runeAt(value, i)))
						i++
					} else if string(_runeAt(value, i)) == "|" && depth == 1 {
						if i+1 < _runeLen(value) && string(_runeAt(value, i+1)) == "|" {
							currentPart = append(currentPart, "||")
							i += 2
						} else {
							hasPipe = true
							partContent := strings.Join(currentPart, "")
							if strings.Contains(partContent, "<<") {
								patternParts = append(patternParts, partContent)
							} else {
								patternParts = append(patternParts, strings.TrimSpace(partContent))
							}
							currentPart = []string{}
							i++
						}
					} else {
						currentPart = append(currentPart, string(_runeAt(value, i)))
						i++
					}
				}
				result = append(result, strings.Join(patternParts, " | "))
				if depth == 0 {
					result = append(result, ")")
					i++
				}
				continue
			}
		}
		result = append(result, string(_runeAt(value, i)))
		i++
	}
	return strings.Join(result, "")
}

func (self *Word) GetCondFormattedValue() string {
	value := self.expandAllAnsiCQuotes(self.Value)
	value = self.stripLocaleStringDollars(value)
	value = self.formatCommandSubstitutions(value, false)
	value = self.normalizeExtglobWhitespace(value)
	value = strings.ReplaceAll(value, "", "")
	return strings.TrimRight(value, "\n")
}

type Command struct {
	Words     []*Word
	Redirects []Node
	Kind      string
}

func (self *Command) GetKind() string { return self.Kind }

func (self *Command) ToSexp() string {
	parts := []string{}
	for _, w := range self.Words {
		parts = append(parts, w.ToSexp())
	}
	for _, r := range self.Redirects {
		parts = append(parts, r.ToSexp())
	}
	inner := strings.Join(parts, " ")
	if !(inner != "") {
		return "(command)"
	}
	return "(command " + inner + ")"
}

type Pipeline struct {
	Commands []Node
	Kind     string
}

func (self *Pipeline) GetKind() string { return self.Kind }

func (self *Pipeline) ToSexp() string {
	if len(self.Commands) == 1 {
		return self.Commands[0].ToSexp()
	}
	cmds := []struct {
		F0 Node
		F1 bool
	}{}
	i := 0
	var cmd Node
	for i < len(self.Commands) {
		cmd = self.Commands[i]
		switch cmd.(type) {
		case *PipeBoth:
			i++
			continue
		}
		needsRedirect := i+1 < len(self.Commands) && self.Commands[i+1].GetKind() == "pipe-both"
		cmds = append(cmds, struct {
			F0 Node
			F1 bool
		}{cmd, needsRedirect})
		i++
	}
	var pair struct {
		F0 Node
		F1 bool
	}
	var needs bool
	if len(cmds) == 1 {
		pair = cmds[0]
		cmd = pair.F0
		needs = pair.F1
		return self.cmdSexp(cmd, needs)
	}
	lastPair := cmds[len(cmds)-1]
	lastCmd := lastPair.F0
	lastNeeds := lastPair.F1
	result := self.cmdSexp(lastCmd, lastNeeds)
	j := len(cmds) - 2
	for j >= 0 {
		pair = cmds[j]
		cmd = pair.F0
		needs = pair.F1
		if needs && cmd.GetKind() != "command" {
			result = "(pipe " + cmd.ToSexp() + " (redirect \">&\" 1) " + result + ")"
		} else {
			result = "(pipe " + self.cmdSexp(cmd, needs) + " " + result + ")"
		}
		j--
	}
	return result
}

func (self *Pipeline) cmdSexp(cmd Node, needsRedirect bool) string {
	if !needsRedirect {
		return cmd.ToSexp()
	}
	switch cmd := cmd.(type) {
	case *Command:
		parts := []string{}
		for _, w := range cmd.Words {
			parts = append(parts, w.ToSexp())
		}
		for _, r := range cmd.Redirects {
			parts = append(parts, r.ToSexp())
		}
		parts = append(parts, "(redirect \">&\" 1)")
		return "(command " + strings.Join(parts, " ") + ")"
	}
	return cmd.ToSexp()
}

type List struct {
	Parts []Node
	Kind  string
}

func (self *List) GetKind() string { return self.Kind }

func (self *List) ToSexp() string {
	parts := append(self.Parts[:0:0], self.Parts...)
	opNames := map[string]string{"&&": "and", "||": "or", ";": "semi", "\n": "semi", "&": "background"}
	for len(parts) > 1 && parts[len(parts)-1].GetKind() == "operator" && (parts[len(parts)-1].(*Operator).Op == ";" || parts[len(parts)-1].(*Operator).Op == "\n") {
		parts = sublist(parts, 0, len(parts)-1)
	}
	if len(parts) == 1 {
		return parts[0].ToSexp()
	}
	if parts[len(parts)-1].GetKind() == "operator" && parts[len(parts)-1].(*Operator).Op == "&" {
		for _, i := range Range(len(parts)-3, 0, -2) {
			if parts[i].GetKind() == "operator" && (parts[i].(*Operator).Op == ";" || parts[i].(*Operator).Op == "\n") {
				left := sublist(parts, 0, i)
				right := sublist(parts, i+1, len(parts)-1)
				var leftSexp string
				if len(left) > 1 {
					leftSexp = (&List{Parts: left, Kind: "list"}).ToSexp()
				} else {
					leftSexp = left[0].ToSexp()
				}
				var rightSexp string
				if len(right) > 1 {
					rightSexp = (&List{Parts: right, Kind: "list"}).ToSexp()
				} else {
					rightSexp = right[0].ToSexp()
				}
				return "(semi " + leftSexp + " (background " + rightSexp + "))"
			}
		}
		innerParts := sublist(parts, 0, len(parts)-1)
		if len(innerParts) == 1 {
			return "(background " + innerParts[0].ToSexp() + ")"
		}
		innerList := &List{Parts: innerParts, Kind: "list"}
		return "(background " + innerList.ToSexp() + ")"
	}
	return self.toSexpWithPrecedence(parts, opNames)
}

func (self *List) toSexpWithPrecedence(parts []Node, opNames map[string]string) string {
	semiPositions := []int{}
	for _, i := range Range(len(parts)) {
		if parts[i].GetKind() == "operator" && (parts[i].(*Operator).Op == ";" || parts[i].(*Operator).Op == "\n") {
			semiPositions = append(semiPositions, i)
		}
	}
	if len(semiPositions) > 0 {
		segments := [][]Node{}
		start := 0
		var seg []Node
		for _, pos := range semiPositions {
			seg = sublist(parts, start, pos)
			if len(seg) > 0 && seg[0].GetKind() != "operator" {
				segments = append(segments, seg)
			}
			start = pos + 1
		}
		seg = sublist(parts, start, len(parts))
		if len(seg) > 0 && seg[0].GetKind() != "operator" {
			segments = append(segments, seg)
		}
		if !(len(segments) > 0) {
			return "()"
		}
		result := self.toSexpAmpAndHigher(segments[0], opNames)
		for _, i := range Range(1, len(segments)) {
			result = "(semi " + result + " " + self.toSexpAmpAndHigher(segments[i], opNames) + ")"
		}
		return result
	}
	return self.toSexpAmpAndHigher(parts, opNames)
}

func (self *List) toSexpAmpAndHigher(parts []Node, opNames map[string]string) string {
	if len(parts) == 1 {
		return parts[0].ToSexp()
	}
	ampPositions := []int{}
	for _, i := range Range(1, len(parts)-1, 2) {
		if parts[i].GetKind() == "operator" && parts[i].(*Operator).Op == "&" {
			ampPositions = append(ampPositions, i)
		}
	}
	if len(ampPositions) > 0 {
		segments := [][]Node{}
		start := 0
		for _, pos := range ampPositions {
			segments = append(segments, sublist(parts, start, pos))
			start = pos + 1
		}
		segments = append(segments, sublist(parts, start, len(parts)))
		result := self.toSexpAndOr(segments[0], opNames)
		for _, i := range Range(1, len(segments)) {
			result = "(background " + result + " " + self.toSexpAndOr(segments[i], opNames) + ")"
		}
		return result
	}
	return self.toSexpAndOr(parts, opNames)
}

func (self *List) toSexpAndOr(parts []Node, opNames map[string]string) string {
	if len(parts) == 1 {
		return parts[0].ToSexp()
	}
	result := parts[0].ToSexp()
	for _, i := range Range(1, len(parts)-1, 2) {
		op := parts[i]
		cmd := parts[i+1]
		opName := _mapGet(opNames, op.(*Operator).Op, op.(*Operator).Op)
		result = "(" + opName + " " + result + " " + cmd.ToSexp() + ")"
	}
	return result
}

type Operator struct {
	Op   string
	Kind string
}

func (self *Operator) GetKind() string { return self.Kind }

func (self *Operator) ToSexp() string {
	names := map[string]string{"&&": "and", "||": "or", ";": "semi", "&": "bg", "|": "pipe"}
	return "(" + _mapGet(names, self.Op, self.Op) + ")"
}

type PipeBoth struct {
	Kind string
}

func (self *PipeBoth) GetKind() string { return self.Kind }

func (self *PipeBoth) ToSexp() string {
	return "(pipe-both)"
}

type Empty struct {
	Kind string
}

func (self *Empty) GetKind() string { return self.Kind }

func (self *Empty) ToSexp() string {
	return ""
}

type Comment struct {
	Text string
	Kind string
}

func (self *Comment) GetKind() string { return self.Kind }

func (self *Comment) ToSexp() string {
	return ""
}

type Redirect struct {
	Op     string
	Target *Word
	Fd     *int
	Kind   string
}

func (self *Redirect) GetKind() string { return self.Kind }

func (self *Redirect) ToSexp() string {
	op := strings.TrimLeft(self.Op, "0123456789")
	if strings.HasPrefix(op, "{") {
		j := 1
		if j < _runeLen(op) && (_strIsAlpha(string(_runeAt(op, j))) || string(_runeAt(op, j)) == "_") {
			j++
			for j < _runeLen(op) && (_strIsAlnum(string(_runeAt(op, j))) || string(_runeAt(op, j)) == "_") {
				j++
			}
			if j < _runeLen(op) && string(_runeAt(op, j)) == "[" {
				j++
				for j < _runeLen(op) && string(_runeAt(op, j)) != "]" {
					j++
				}
				if j < _runeLen(op) && string(_runeAt(op, j)) == "]" {
					j++
				}
			}
			if j < _runeLen(op) && string(_runeAt(op, j)) == "}" {
				op = substring(op, j+1, _runeLen(op))
			}
		}
	}
	targetVal := self.Target.Value
	targetVal = self.Target.expandAllAnsiCQuotes(targetVal)
	targetVal = self.Target.stripLocaleStringDollars(targetVal)
	targetVal = self.Target.formatCommandSubstitutions(targetVal, false)
	targetVal = self.Target.stripArithLineContinuations(targetVal)
	if strings.HasSuffix(targetVal, "\\") && !strings.HasSuffix(targetVal, "\\\\") {
		targetVal = targetVal + "\\"
	}
	if strings.HasPrefix(targetVal, "&") {
		if op == ">" {
			op = ">&"
		} else if op == "<" {
			op = "<&"
		}
		raw := substring(targetVal, 1, _runeLen(targetVal))
		if _strIsDigit(raw) && _parseInt(raw, 10) <= 2147483647 {
			return "(redirect \"" + op + "\" " + _intToStr(_parseInt(raw, 10)) + ")"
		}
		if strings.HasSuffix(raw, "-") && _strIsDigit(_Substring(raw, 0, _runeLen(raw)-1)) && _parseInt(_Substring(raw, 0, _runeLen(raw)-1), 10) <= 2147483647 {
			return "(redirect \"" + op + "\" " + _intToStr(_parseInt(_Substring(raw, 0, _runeLen(raw)-1), 10)) + ")"
		}
		if targetVal == "&-" {
			return "(redirect \">&-\" 0)"
		}
		fdTarget := func() string {
			if strings.HasSuffix(raw, "-") {
				return _Substring(raw, 0, _runeLen(raw)-1)
			} else {
				return raw
			}
		}()
		return "(redirect \"" + op + "\" \"" + fdTarget + "\")"
	}
	if op == ">&" || op == "<&" {
		if _strIsDigit(targetVal) && _parseInt(targetVal, 10) <= 2147483647 {
			return "(redirect \"" + op + "\" " + _intToStr(_parseInt(targetVal, 10)) + ")"
		}
		if targetVal == "-" {
			return "(redirect \">&-\" 0)"
		}
		if strings.HasSuffix(targetVal, "-") && _strIsDigit(_Substring(targetVal, 0, _runeLen(targetVal)-1)) && _parseInt(_Substring(targetVal, 0, _runeLen(targetVal)-1), 10) <= 2147483647 {
			return "(redirect \"" + op + "\" " + _intToStr(_parseInt(_Substring(targetVal, 0, _runeLen(targetVal)-1), 10)) + ")"
		}
		outVal := func() string {
			if strings.HasSuffix(targetVal, "-") {
				return _Substring(targetVal, 0, _runeLen(targetVal)-1)
			} else {
				return targetVal
			}
		}()
		return "(redirect \"" + op + "\" \"" + outVal + "\")"
	}
	return "(redirect \"" + op + "\" \"" + targetVal + "\")"
}

type HereDoc struct {
	Delimiter string
	Content   string
	StripTabs bool
	Quoted    bool
	Fd        *int
	Complete  bool
	startPos  int
	Kind      string
}

func (self *HereDoc) GetKind() string { return self.Kind }

func (self *HereDoc) ToSexp() string {
	op := func() string {
		if self.StripTabs {
			return "<<-"
		} else {
			return "<<"
		}
	}()
	content := self.Content
	if strings.HasSuffix(content, "\\") && !strings.HasSuffix(content, "\\\\") {
		content = content + "\\"
	}
	return fmt.Sprintf("(redirect \"%v\" \"%v\")", op, content)
}

type Subshell struct {
	Body      Node
	Redirects []Node
	Kind      string
}

func (self *Subshell) GetKind() string { return self.Kind }

func (self *Subshell) ToSexp() string {
	base := "(subshell " + self.Body.ToSexp() + ")"
	return appendRedirects(base, self.Redirects)
}

type BraceGroup struct {
	Body      Node
	Redirects []Node
	Kind      string
}

func (self *BraceGroup) GetKind() string { return self.Kind }

func (self *BraceGroup) ToSexp() string {
	base := "(brace-group " + self.Body.ToSexp() + ")"
	return appendRedirects(base, self.Redirects)
}

type If struct {
	Condition Node
	ThenBody  Node
	ElseBody  Node
	Redirects []Node
	Kind      string
}

func (self *If) GetKind() string { return self.Kind }

func (self *If) ToSexp() string {
	result := "(if " + self.Condition.ToSexp() + " " + self.ThenBody.ToSexp()
	if !_isNilInterface(self.ElseBody) {
		result = result + " " + self.ElseBody.ToSexp()
	}
	result = result + ")"
	for _, r := range self.Redirects {
		result = result + " " + r.ToSexp()
	}
	return result
}

type While struct {
	Condition Node
	Body      Node
	Redirects []Node
	Kind      string
}

func (self *While) GetKind() string { return self.Kind }

func (self *While) ToSexp() string {
	base := "(while " + self.Condition.ToSexp() + " " + self.Body.ToSexp() + ")"
	return appendRedirects(base, self.Redirects)
}

type Until struct {
	Condition Node
	Body      Node
	Redirects []Node
	Kind      string
}

func (self *Until) GetKind() string { return self.Kind }

func (self *Until) ToSexp() string {
	base := "(until " + self.Condition.ToSexp() + " " + self.Body.ToSexp() + ")"
	return appendRedirects(base, self.Redirects)
}

type For struct {
	Var       string
	Words     []*Word
	Body      Node
	Redirects []Node
	Kind      string
}

func (self *For) GetKind() string { return self.Kind }

func (self *For) ToSexp() string {
	suffix := ""
	if len(self.Redirects) > 0 {
		redirectParts := []string{}
		for _, r := range self.Redirects {
			redirectParts = append(redirectParts, r.ToSexp())
		}
		suffix = " " + strings.Join(redirectParts, " ")
	}
	tempWord := &Word{Value: self.Var, Parts: []Node{}, Kind: "word"}
	varFormatted := tempWord.formatCommandSubstitutions(self.Var, false)
	varEscaped := strings.ReplaceAll(strings.ReplaceAll(varFormatted, "\\", "\\\\"), "\"", "\\\"")
	if self.Words == nil {
		return "(for (word \"" + varEscaped + "\") (in (word \"\\\"$@\\\"\")) " + self.Body.ToSexp() + ")" + suffix
	} else if len(self.Words) == 0 {
		return "(for (word \"" + varEscaped + "\") (in) " + self.Body.ToSexp() + ")" + suffix
	} else {
		wordParts := []string{}
		for _, w := range self.Words {
			wordParts = append(wordParts, w.ToSexp())
		}
		wordStrs := strings.Join(wordParts, " ")
		return "(for (word \"" + varEscaped + "\") (in " + wordStrs + ") " + self.Body.ToSexp() + ")" + suffix
	}
}

type ForArith struct {
	Init      string
	Cond      string
	Incr      string
	Body      Node
	Redirects []Node
	Kind      string
}

func (self *ForArith) GetKind() string { return self.Kind }

func (self *ForArith) ToSexp() string {
	suffix := ""
	if len(self.Redirects) > 0 {
		redirectParts := []string{}
		for _, r := range self.Redirects {
			redirectParts = append(redirectParts, r.ToSexp())
		}
		suffix = " " + strings.Join(redirectParts, " ")
	}
	initVal := func() string {
		if self.Init != "" {
			return self.Init
		} else {
			return "1"
		}
	}()
	condVal := func() string {
		if self.Cond != "" {
			return self.Cond
		} else {
			return "1"
		}
	}()
	incrVal := func() string {
		if self.Incr != "" {
			return self.Incr
		} else {
			return "1"
		}
	}()
	initStr := formatArithVal(initVal)
	condStr := formatArithVal(condVal)
	incrStr := formatArithVal(incrVal)
	bodyStr := self.Body.ToSexp()
	return fmt.Sprintf("(arith-for (init (word \"%v\")) (test (word \"%v\")) (step (word \"%v\")) %v)%v", initStr, condStr, incrStr, bodyStr, suffix)
}

type Select struct {
	Var       string
	Words     []*Word
	Body      Node
	Redirects []Node
	Kind      string
}

func (self *Select) GetKind() string { return self.Kind }

func (self *Select) ToSexp() string {
	suffix := ""
	if len(self.Redirects) > 0 {
		redirectParts := []string{}
		for _, r := range self.Redirects {
			redirectParts = append(redirectParts, r.ToSexp())
		}
		suffix = " " + strings.Join(redirectParts, " ")
	}
	varEscaped := strings.ReplaceAll(strings.ReplaceAll(self.Var, "\\", "\\\\"), "\"", "\\\"")
	var inClause string
	if self.Words != nil {
		wordParts := []string{}
		for _, w := range self.Words {
			wordParts = append(wordParts, w.ToSexp())
		}
		wordStrs := strings.Join(wordParts, " ")
		if len(self.Words) > 0 {
			inClause = "(in " + wordStrs + ")"
		} else {
			inClause = "(in)"
		}
	} else {
		inClause = "(in (word \"\\\"$@\\\"\"))"
	}
	return "(select (word \"" + varEscaped + "\") " + inClause + " " + self.Body.ToSexp() + ")" + suffix
}

type Case struct {
	Word      Node
	Patterns  []Node
	Redirects []Node
	Kind      string
}

func (self *Case) GetKind() string { return self.Kind }

func (self *Case) ToSexp() string {
	parts := []string{}
	parts = append(parts, "(case "+self.Word.ToSexp())
	for _, p := range self.Patterns {
		parts = append(parts, p.ToSexp())
	}
	base := strings.Join(parts, " ") + ")"
	return appendRedirects(base, self.Redirects)
}

type CasePattern struct {
	Pattern    string
	Body       Node
	Terminator string
	Kind       string
}

func (self *CasePattern) GetKind() string { return self.Kind }

func (self *CasePattern) ToSexp() string {
	alternatives := []string{}
	current := []string{}
	i := 0
	depth := 0
	for i < _runeLen(self.Pattern) {
		ch := string(_runeAt(self.Pattern, i))
		if ch == "\\" && i+1 < _runeLen(self.Pattern) {
			current = append(current, substring(self.Pattern, i, i+2))
			i += 2
		} else if (ch == "@" || ch == "?" || ch == "*" || ch == "+" || ch == "!") && i+1 < _runeLen(self.Pattern) && string(_runeAt(self.Pattern, i+1)) == "(" {
			current = append(current, ch)
			current = append(current, "(")
			depth++
			i += 2
		} else if isExpansionStart(self.Pattern, i, "$(") {
			current = append(current, ch)
			current = append(current, "(")
			depth++
			i += 2
		} else if ch == "(" && depth > 0 {
			current = append(current, ch)
			depth++
			i++
		} else if ch == ")" && depth > 0 {
			current = append(current, ch)
			depth--
			i++
		} else if ch == "[" {
			result0, result1, _ := consumeBracketClass(self.Pattern, i, depth)
			i = result0
			current = append(current, result1...)
		} else if ch == "'" && depth == 0 {
			result0, result1 := consumeSingleQuote(self.Pattern, i)
			i = result0
			current = append(current, result1...)
		} else if ch == "\"" && depth == 0 {
			result0, result1 := consumeDoubleQuote(self.Pattern, i)
			i = result0
			current = append(current, result1...)
		} else if ch == "|" && depth == 0 {
			alternatives = append(alternatives, strings.Join(current, ""))
			current = []string{}
			i++
		} else {
			current = append(current, ch)
			i++
		}
	}
	alternatives = append(alternatives, strings.Join(current, ""))
	wordList := []string{}
	for _, alt := range alternatives {
		wordList = append(wordList, (&Word{Value: alt, Kind: "word"}).ToSexp())
	}
	patternStr := strings.Join(wordList, " ")
	parts := []string{"(pattern (" + patternStr + ")"}
	if !_isNilInterface(self.Body) {
		parts = append(parts, " "+self.Body.ToSexp())
	} else {
		parts = append(parts, " ()")
	}
	parts = append(parts, ")")
	return strings.Join(parts, "")
}

type Function struct {
	Name string
	Body Node
	Kind string
}

func (self *Function) GetKind() string { return self.Kind }

func (self *Function) ToSexp() string {
	return "(function \"" + self.Name + "\" " + self.Body.ToSexp() + ")"
}

type ParamExpansion struct {
	Param string
	Op    string
	Arg   string
	Kind  string
}

func (self *ParamExpansion) GetKind() string { return self.Kind }

func (self *ParamExpansion) ToSexp() string {
	escapedParam := strings.ReplaceAll(strings.ReplaceAll(self.Param, "\\", "\\\\"), "\"", "\\\"")
	if self.Op != "" {
		escapedOp := strings.ReplaceAll(strings.ReplaceAll(self.Op, "\\", "\\\\"), "\"", "\\\"")
		var argVal string
		if self.Arg != "" {
			argVal = self.Arg
		} else {
			argVal = ""
		}
		escapedArg := strings.ReplaceAll(strings.ReplaceAll(argVal, "\\", "\\\\"), "\"", "\\\"")
		return "(param \"" + escapedParam + "\" \"" + escapedOp + "\" \"" + escapedArg + "\")"
	}
	return "(param \"" + escapedParam + "\")"
}

type ParamLength struct {
	Param string
	Kind  string
}

func (self *ParamLength) GetKind() string { return self.Kind }

func (self *ParamLength) ToSexp() string {
	escaped := strings.ReplaceAll(strings.ReplaceAll(self.Param, "\\", "\\\\"), "\"", "\\\"")
	return "(param-len \"" + escaped + "\")"
}

type ParamIndirect struct {
	Param string
	Op    string
	Arg   string
	Kind  string
}

func (self *ParamIndirect) GetKind() string { return self.Kind }

func (self *ParamIndirect) ToSexp() string {
	escaped := strings.ReplaceAll(strings.ReplaceAll(self.Param, "\\", "\\\\"), "\"", "\\\"")
	if self.Op != "" {
		escapedOp := strings.ReplaceAll(strings.ReplaceAll(self.Op, "\\", "\\\\"), "\"", "\\\"")
		var argVal string
		if self.Arg != "" {
			argVal = self.Arg
		} else {
			argVal = ""
		}
		escapedArg := strings.ReplaceAll(strings.ReplaceAll(argVal, "\\", "\\\\"), "\"", "\\\"")
		return "(param-indirect \"" + escaped + "\" \"" + escapedOp + "\" \"" + escapedArg + "\")"
	}
	return "(param-indirect \"" + escaped + "\")"
}

type CommandSubstitution struct {
	Command Node
	Brace   bool
	Kind    string
}

func (self *CommandSubstitution) GetKind() string { return self.Kind }

func (self *CommandSubstitution) ToSexp() string {
	if self.Brace {
		return "(funsub " + self.Command.ToSexp() + ")"
	}
	return "(cmdsub " + self.Command.ToSexp() + ")"
}

type ArithmeticExpansion struct {
	Expression Node
	Kind       string
}

func (self *ArithmeticExpansion) GetKind() string { return self.Kind }

func (self *ArithmeticExpansion) ToSexp() string {
	if self.Expression == nil {
		return "(arith)"
	}
	return "(arith " + self.Expression.ToSexp() + ")"
}

type ArithmeticCommand struct {
	Expression Node
	Redirects  []Node
	RawContent string
	Kind       string
}

func (self *ArithmeticCommand) GetKind() string { return self.Kind }

func (self *ArithmeticCommand) ToSexp() string {
	formatted := (&Word{Value: self.RawContent, Kind: "word"}).formatCommandSubstitutions(self.RawContent, true)
	escaped := strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(formatted, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n"), "\t", "\\t")
	result := "(arith (word \"" + escaped + "\"))"
	if len(self.Redirects) > 0 {
		redirectParts := []string{}
		for _, r := range self.Redirects {
			redirectParts = append(redirectParts, r.ToSexp())
		}
		redirectSexps := strings.Join(redirectParts, " ")
		return result + " " + redirectSexps
	}
	return result
}

type ArithNumber struct {
	Value string
	Kind  string
}

func (self *ArithNumber) GetKind() string { return self.Kind }

func (self *ArithNumber) ToSexp() string {
	return "(number \"" + self.Value + "\")"
}

type ArithEmpty struct {
	Kind string
}

func (self *ArithEmpty) GetKind() string { return self.Kind }

func (self *ArithEmpty) ToSexp() string {
	return "(empty)"
}

type ArithVar struct {
	Name string
	Kind string
}

func (self *ArithVar) GetKind() string { return self.Kind }

func (self *ArithVar) ToSexp() string {
	return "(var \"" + self.Name + "\")"
}

type ArithBinaryOp struct {
	Op    string
	Left  Node
	Right Node
	Kind  string
}

func (self *ArithBinaryOp) GetKind() string { return self.Kind }

func (self *ArithBinaryOp) ToSexp() string {
	return "(binary-op \"" + self.Op + "\" " + self.Left.ToSexp() + " " + self.Right.ToSexp() + ")"
}

type ArithUnaryOp struct {
	Op      string
	Operand Node
	Kind    string
}

func (self *ArithUnaryOp) GetKind() string { return self.Kind }

func (self *ArithUnaryOp) ToSexp() string {
	return "(unary-op \"" + self.Op + "\" " + self.Operand.ToSexp() + ")"
}

type ArithPreIncr struct {
	Operand Node
	Kind    string
}

func (self *ArithPreIncr) GetKind() string { return self.Kind }

func (self *ArithPreIncr) ToSexp() string {
	return "(pre-incr " + self.Operand.ToSexp() + ")"
}

type ArithPostIncr struct {
	Operand Node
	Kind    string
}

func (self *ArithPostIncr) GetKind() string { return self.Kind }

func (self *ArithPostIncr) ToSexp() string {
	return "(post-incr " + self.Operand.ToSexp() + ")"
}

type ArithPreDecr struct {
	Operand Node
	Kind    string
}

func (self *ArithPreDecr) GetKind() string { return self.Kind }

func (self *ArithPreDecr) ToSexp() string {
	return "(pre-decr " + self.Operand.ToSexp() + ")"
}

type ArithPostDecr struct {
	Operand Node
	Kind    string
}

func (self *ArithPostDecr) GetKind() string { return self.Kind }

func (self *ArithPostDecr) ToSexp() string {
	return "(post-decr " + self.Operand.ToSexp() + ")"
}

type ArithAssign struct {
	Op     string
	Target Node
	Value  Node
	Kind   string
}

func (self *ArithAssign) GetKind() string { return self.Kind }

func (self *ArithAssign) ToSexp() string {
	return "(assign \"" + self.Op + "\" " + self.Target.ToSexp() + " " + self.Value.ToSexp() + ")"
}

type ArithTernary struct {
	Condition Node
	IfTrue    Node
	IfFalse   Node
	Kind      string
}

func (self *ArithTernary) GetKind() string { return self.Kind }

func (self *ArithTernary) ToSexp() string {
	return "(ternary " + self.Condition.ToSexp() + " " + self.IfTrue.ToSexp() + " " + self.IfFalse.ToSexp() + ")"
}

type ArithComma struct {
	Left  Node
	Right Node
	Kind  string
}

func (self *ArithComma) GetKind() string { return self.Kind }

func (self *ArithComma) ToSexp() string {
	return "(comma " + self.Left.ToSexp() + " " + self.Right.ToSexp() + ")"
}

type ArithSubscript struct {
	Array string
	Index Node
	Kind  string
}

func (self *ArithSubscript) GetKind() string { return self.Kind }

func (self *ArithSubscript) ToSexp() string {
	return "(subscript \"" + self.Array + "\" " + self.Index.ToSexp() + ")"
}

type ArithEscape struct {
	Char string
	Kind string
}

func (self *ArithEscape) GetKind() string { return self.Kind }

func (self *ArithEscape) ToSexp() string {
	return "(escape \"" + self.Char + "\")"
}

type ArithDeprecated struct {
	Expression string
	Kind       string
}

func (self *ArithDeprecated) GetKind() string { return self.Kind }

func (self *ArithDeprecated) ToSexp() string {
	escaped := strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(self.Expression, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n")
	return "(arith-deprecated \"" + escaped + "\")"
}

type ArithConcat struct {
	Parts []Node
	Kind  string
}

func (self *ArithConcat) GetKind() string { return self.Kind }

func (self *ArithConcat) ToSexp() string {
	sexps := []string{}
	for _, p := range self.Parts {
		sexps = append(sexps, p.ToSexp())
	}
	return "(arith-concat " + strings.Join(sexps, " ") + ")"
}

type AnsiCQuote struct {
	Content string
	Kind    string
}

func (self *AnsiCQuote) GetKind() string { return self.Kind }

func (self *AnsiCQuote) ToSexp() string {
	escaped := strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(self.Content, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n")
	return "(ansi-c \"" + escaped + "\")"
}

type LocaleString struct {
	Content string
	Kind    string
}

func (self *LocaleString) GetKind() string { return self.Kind }

func (self *LocaleString) ToSexp() string {
	escaped := strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(self.Content, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n")
	return "(locale \"" + escaped + "\")"
}

type ProcessSubstitution struct {
	Direction string
	Command   Node
	Kind      string
}

func (self *ProcessSubstitution) GetKind() string { return self.Kind }

func (self *ProcessSubstitution) ToSexp() string {
	return "(procsub \"" + self.Direction + "\" " + self.Command.ToSexp() + ")"
}

type Negation struct {
	Pipeline Node
	Kind     string
}

func (self *Negation) GetKind() string { return self.Kind }

func (self *Negation) ToSexp() string {
	if _isNilInterface(self.Pipeline) {
		return "(negation (command))"
	}
	return "(negation " + self.Pipeline.ToSexp() + ")"
}

type Time struct {
	Pipeline Node
	Posix    bool
	Kind     string
}

func (self *Time) GetKind() string { return self.Kind }

func (self *Time) ToSexp() string {
	if _isNilInterface(self.Pipeline) {
		if self.Posix {
			return "(time -p (command))"
		} else {
			return "(time (command))"
		}
	}
	if self.Posix {
		return "(time -p " + self.Pipeline.ToSexp() + ")"
	}
	return "(time " + self.Pipeline.ToSexp() + ")"
}

type ConditionalExpr struct {
	Body      interface{}
	Redirects []Node
	Kind      string
}

func (self *ConditionalExpr) GetKind() string { return self.Kind }

func (self *ConditionalExpr) ToSexp() string {
	body := self.Body
	var result string
	switch body := body.(type) {
	case string:
		escaped := strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(body, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n")
		result = "(cond \"" + escaped + "\")"
	default:
		{
			body := body.(Node)
			result = "(cond " + body.ToSexp() + ")"
		}
	}
	if len(self.Redirects) > 0 {
		redirectParts := []string{}
		for _, r := range self.Redirects {
			redirectParts = append(redirectParts, r.ToSexp())
		}
		redirectSexps := strings.Join(redirectParts, " ")
		return result + " " + redirectSexps
	}
	return result
}

type UnaryTest struct {
	Op      string
	Operand Node
	Kind    string
}

func (self *UnaryTest) GetKind() string { return self.Kind }

func (self *UnaryTest) ToSexp() string {
	operandVal := self.Operand.(*Word).GetCondFormattedValue()
	return "(cond-unary \"" + self.Op + "\" (cond-term \"" + operandVal + "\"))"
}

type BinaryTest struct {
	Op    string
	Left  Node
	Right Node
	Kind  string
}

func (self *BinaryTest) GetKind() string { return self.Kind }

func (self *BinaryTest) ToSexp() string {
	leftVal := self.Left.(*Word).GetCondFormattedValue()
	rightVal := self.Right.(*Word).GetCondFormattedValue()
	return "(cond-binary \"" + self.Op + "\" (cond-term \"" + leftVal + "\") (cond-term \"" + rightVal + "\"))"
}

type CondAnd struct {
	Left  Node
	Right Node
	Kind  string
}

func (self *CondAnd) GetKind() string { return self.Kind }

func (self *CondAnd) ToSexp() string {
	return "(cond-and " + self.Left.ToSexp() + " " + self.Right.ToSexp() + ")"
}

type CondOr struct {
	Left  Node
	Right Node
	Kind  string
}

func (self *CondOr) GetKind() string { return self.Kind }

func (self *CondOr) ToSexp() string {
	return "(cond-or " + self.Left.ToSexp() + " " + self.Right.ToSexp() + ")"
}

type CondNot struct {
	Operand Node
	Kind    string
}

func (self *CondNot) GetKind() string { return self.Kind }

func (self *CondNot) ToSexp() string {
	return self.Operand.ToSexp()
}

type CondParen struct {
	Inner Node
	Kind  string
}

func (self *CondParen) GetKind() string { return self.Kind }

func (self *CondParen) ToSexp() string {
	return "(cond-expr " + self.Inner.ToSexp() + ")"
}

type Array struct {
	Elements []*Word
	Kind     string
}

func (self *Array) GetKind() string { return self.Kind }

func (self *Array) ToSexp() string {
	if !(len(self.Elements) > 0) {
		return "(array)"
	}
	parts := []string{}
	for _, e := range self.Elements {
		parts = append(parts, e.ToSexp())
	}
	inner := strings.Join(parts, " ")
	return "(array " + inner + ")"
}

type Coproc struct {
	Command Node
	Name    string
	Kind    string
}

func (self *Coproc) GetKind() string { return self.Kind }

func (self *Coproc) ToSexp() string {
	var name string
	if self.Name != "" {
		name = self.Name
	} else {
		name = "COPROC"
	}
	return "(coproc \"" + name + "\" " + self.Command.ToSexp() + ")"
}

type Parser struct {
	Source                  string
	Pos                     int
	Length                  int
	pendingHeredocs         []*HereDoc
	cmdsubHeredocEnd        int
	sawNewlineInSingleQuote bool
	inProcessSub            bool
	extglob                 bool
	ctx                     *ContextStack
	lexer                   *Lexer
	tokenHistory            []*Token
	parserState             int
	dolbraceState           int
	eofToken                string
	wordContext             int
	atCommandStart          bool
	inArrayLiteral          bool
	inAssignBuiltin         bool
	arithSrc                string
	arithPos                int
	arithLen                int
}

func (self *Parser) setState(flag int) {
	self.parserState = (self.parserState | flag)
}

func (self *Parser) clearState(flag int) {
	self.parserState = (self.parserState & ^flag)
}

func (self *Parser) inState(flag int) bool {
	return (self.parserState & flag) != 0
}

func (self *Parser) saveParserState() *SavedParserState {
	return &SavedParserState{ParserState: self.parserState, DolbraceState: self.dolbraceState, PendingHeredocs: func() []Node {
		_r := make([]Node, len(self.pendingHeredocs))
		for _i, _v := range self.pendingHeredocs {
			_r[_i] = _v
		}
		return _r
	}(), CtxStack: self.ctx.CopyStack(), EofToken: self.eofToken}
}

func (self *Parser) restoreParserState(saved *SavedParserState) {
	self.parserState = saved.ParserState
	self.dolbraceState = saved.DolbraceState
	self.eofToken = saved.EofToken
	self.ctx.RestoreFrom(saved.CtxStack)
}

func (self *Parser) recordToken(tok *Token) {
	self.tokenHistory = []*Token{tok, self.tokenHistory[0], self.tokenHistory[1], self.tokenHistory[2]}
}

func (self *Parser) updateDolbraceForOp(op string, hasParam bool) {
	if self.dolbraceState == DolbraceStateNONE {
		return
	}
	if op == "" || _runeLen(op) == 0 {
		return
	}
	firstChar := string(_runeAt(op, 0))
	if self.dolbraceState == DolbraceStatePARAM && hasParam {
		if strings.Contains("%#^,", firstChar) {
			self.dolbraceState = DolbraceStateQUOTE
			return
		}
		if firstChar == "/" {
			self.dolbraceState = DolbraceStateQUOTE2
			return
		}
	}
	if self.dolbraceState == DolbraceStatePARAM {
		if strings.Contains("#%^,~:-=?+/", firstChar) {
			self.dolbraceState = DolbraceStateOP
		}
	}
}

func (self *Parser) syncLexer() {
	if self.lexer.tokenCache != nil {
		if self.lexer.tokenCache.Pos != self.Pos || self.lexer.cachedWordContext != self.wordContext || self.lexer.cachedAtCommandStart != self.atCommandStart || self.lexer.cachedInArrayLiteral != self.inArrayLiteral || self.lexer.cachedInAssignBuiltin != self.inAssignBuiltin {
			self.lexer.tokenCache = nil
		}
	}
	if self.lexer.Pos != self.Pos {
		self.lexer.Pos = self.Pos
	}
	self.lexer.eofToken = self.eofToken
	self.lexer.parserState = self.parserState
	self.lexer.lastReadToken = self.tokenHistory[0]
	self.lexer.wordContext = self.wordContext
	self.lexer.atCommandStart = self.atCommandStart
	self.lexer.inArrayLiteral = self.inArrayLiteral
	self.lexer.inAssignBuiltin = self.inAssignBuiltin
}

func (self *Parser) syncParser() {
	self.Pos = self.lexer.Pos
}

func (self *Parser) lexPeekToken() *Token {
	if self.lexer.tokenCache != nil && self.lexer.tokenCache.Pos == self.Pos && self.lexer.cachedWordContext == self.wordContext && self.lexer.cachedAtCommandStart == self.atCommandStart && self.lexer.cachedInArrayLiteral == self.inArrayLiteral && self.lexer.cachedInAssignBuiltin == self.inAssignBuiltin {
		return self.lexer.tokenCache
	}
	savedPos := self.Pos
	self.syncLexer()
	result := self.lexer.PeekToken()
	self.lexer.cachedWordContext = self.wordContext
	self.lexer.cachedAtCommandStart = self.atCommandStart
	self.lexer.cachedInArrayLiteral = self.inArrayLiteral
	self.lexer.cachedInAssignBuiltin = self.inAssignBuiltin
	self.lexer.postReadPos = self.lexer.Pos
	self.Pos = savedPos
	return result
}

func (self *Parser) lexNextToken() *Token {
	var tok *Token
	if self.lexer.tokenCache != nil && self.lexer.tokenCache.Pos == self.Pos && self.lexer.cachedWordContext == self.wordContext && self.lexer.cachedAtCommandStart == self.atCommandStart && self.lexer.cachedInArrayLiteral == self.inArrayLiteral && self.lexer.cachedInAssignBuiltin == self.inAssignBuiltin {
		tok = self.lexer.NextToken()
		self.Pos = self.lexer.postReadPos
		self.lexer.Pos = self.lexer.postReadPos
	} else {
		self.syncLexer()
		tok = self.lexer.NextToken()
		self.lexer.cachedWordContext = self.wordContext
		self.lexer.cachedAtCommandStart = self.atCommandStart
		self.lexer.cachedInArrayLiteral = self.inArrayLiteral
		self.lexer.cachedInAssignBuiltin = self.inAssignBuiltin
		self.syncParser()
	}
	self.recordToken(tok)
	return tok
}

func (self *Parser) lexSkipBlanks() {
	self.syncLexer()
	self.lexer.SkipBlanks()
	self.syncParser()
}

func (self *Parser) lexSkipComment() bool {
	self.syncLexer()
	result := self.lexer.skipComment()
	self.syncParser()
	return result
}

func (self *Parser) lexIsCommandTerminator() bool {
	tok := self.lexPeekToken()
	t := tok.Type
	return t == TokenTypeEOF || t == TokenTypeNEWLINE || t == TokenTypePIPE || t == TokenTypeSEMI || t == TokenTypeLPAREN || t == TokenTypeRPAREN || t == TokenTypeAMP
}

func (self *Parser) lexPeekOperator() (int, string) {
	tok := self.lexPeekToken()
	t := tok.Type
	if t >= TokenTypeSEMI && t <= TokenTypeGREATER || t >= TokenTypeANDAND && t <= TokenTypePIPEAMP {
		return t, tok.Value
	}
	return 0, ""
}

func (self *Parser) lexPeekReservedWord() string {
	tok := self.lexPeekToken()
	if tok.Type != TokenTypeWORD {
		return ""
	}
	word := tok.Value
	if strings.HasSuffix(word, "\\\n") {
		word = _Substring(word, 0, _runeLen(word)-2)
	}
	if func() bool { _, ok := RESERVEDWORDS[word]; return ok }() || word == "{" || word == "}" || word == "[[" || word == "]]" || word == "!" || word == "time" {
		return word
	}
	return ""
}

func (self *Parser) lexIsAtReservedWord(word string) bool {
	reserved := self.lexPeekReservedWord()
	return reserved == word
}

func (self *Parser) lexConsumeWord(expected string) bool {
	tok := self.lexPeekToken()
	if tok.Type != TokenTypeWORD {
		return false
	}
	word := tok.Value
	if strings.HasSuffix(word, "\\\n") {
		word = _Substring(word, 0, _runeLen(word)-2)
	}
	if word == expected {
		self.lexNextToken()
		return true
	}
	return false
}

func (self *Parser) lexPeekCaseTerminator() string {
	tok := self.lexPeekToken()
	t := tok.Type
	if t == TokenTypeSEMISEMI {
		return ";;"
	}
	if t == TokenTypeSEMIAMP {
		return ";&"
	}
	if t == TokenTypeSEMISEMIAMP {
		return ";;&"
	}
	return ""
}

func (self *Parser) AtEnd() bool {
	return self.Pos >= self.Length
}

func (self *Parser) Peek() string {
	if self.AtEnd() {
		return ""
	}
	return string(_runeAt(self.Source, self.Pos))
}

func (self *Parser) Advance() string {
	if self.AtEnd() {
		return ""
	}
	ch := string(_runeAt(self.Source, self.Pos))
	self.Pos++
	return ch
}

func (self *Parser) PeekAt(offset int) string {
	pos := self.Pos + offset
	if pos < 0 || pos >= self.Length {
		return ""
	}
	return string(_runeAt(self.Source, pos))
}

func (self *Parser) Lookahead(n int) string {
	return substring(self.Source, self.Pos, self.Pos+n)
}

func (self *Parser) isBangFollowedByProcsub() bool {
	if self.Pos+2 >= self.Length {
		return false
	}
	nextChar := string(_runeAt(self.Source, self.Pos+1))
	if nextChar != ">" && nextChar != "<" {
		return false
	}
	return string(_runeAt(self.Source, self.Pos+2)) == "("
}

func (self *Parser) SkipWhitespace() {
	for !self.AtEnd() {
		self.lexSkipBlanks()
		if self.AtEnd() {
			break
		}
		ch := self.Peek()
		if ch == "#" {
			self.lexSkipComment()
		} else if ch == "\\" && self.PeekAt(1) == "\n" {
			self.Advance()
			self.Advance()
		} else {
			break
		}
	}
}

func (self *Parser) SkipWhitespaceAndNewlines() {
	for !self.AtEnd() {
		ch := self.Peek()
		if isWhitespace(ch) {
			self.Advance()
			if ch == "\n" {
				self.gatherHeredocBodies()
				if self.cmdsubHeredocEnd != -1 && self.cmdsubHeredocEnd > self.Pos {
					self.Pos = self.cmdsubHeredocEnd
					self.cmdsubHeredocEnd = -1
				}
			}
		} else if ch == "#" {
			for !self.AtEnd() && self.Peek() != "\n" {
				self.Advance()
			}
		} else if ch == "\\" && self.PeekAt(1) == "\n" {
			self.Advance()
			self.Advance()
		} else {
			break
		}
	}
}

func (self *Parser) atListTerminatingBracket() bool {
	if self.AtEnd() {
		return false
	}
	ch := self.Peek()
	if self.eofToken != "" && ch == self.eofToken {
		return true
	}
	if ch == ")" {
		return true
	}
	if ch == "}" {
		nextPos := self.Pos + 1
		if nextPos >= self.Length {
			return true
		}
		return isWordEndContext(string(_runeAt(self.Source, nextPos)))
	}
	return false
}

func (self *Parser) atEofToken() bool {
	if self.eofToken == "" {
		return false
	}
	tok := self.lexPeekToken()
	if self.eofToken == ")" {
		return tok.Type == TokenTypeRPAREN
	}
	if self.eofToken == "}" {
		return tok.Type == TokenTypeWORD && tok.Value == "}"
	}
	return false
}

func (self *Parser) collectRedirects() []Node {
	redirects := []Node{}
	for true {
		self.SkipWhitespace()
		redirect := self.ParseRedirect()
		if redirect == nil {
			break
		}
		redirects = append(redirects, redirect)
	}
	if len(redirects) > 0 {
		return redirects
	}
	return nil
}

func (self *Parser) parseLoopBody(context string) Node {
	if self.Peek() == "{" {
		brace := self.ParseBraceGroup()
		if brace == nil {
			panic(NewParseError(fmt.Sprintf("Expected brace group body in %v", context), self.lexPeekToken().Pos, 0))
		}
		return brace.Body
	}
	if self.lexConsumeWord("do") {
		body := self.ParseListUntil(map[string]struct{}{"done": {}})
		if _isNilInterface(body) {
			panic(NewParseError("Expected commands after 'do'", self.lexPeekToken().Pos, 0))
		}
		self.SkipWhitespaceAndNewlines()
		if !self.lexConsumeWord("done") {
			panic(NewParseError(fmt.Sprintf("Expected 'done' to close %v", context), self.lexPeekToken().Pos, 0))
		}
		return body
	}
	panic(NewParseError(fmt.Sprintf("Expected 'do' or '{' in %v", context), self.lexPeekToken().Pos, 0))
}

func (self *Parser) PeekWord() string {
	savedPos := self.Pos
	self.SkipWhitespace()
	if self.AtEnd() || isMetachar(self.Peek()) {
		self.Pos = savedPos
		return ""
	}
	chars := []string{}
	for !self.AtEnd() && !isMetachar(self.Peek()) {
		ch := self.Peek()
		if isQuote(ch) {
			break
		}
		if ch == "\\" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "\n" {
			break
		}
		if ch == "\\" && self.Pos+1 < self.Length {
			chars = append(chars, self.Advance())
			chars = append(chars, self.Advance())
			continue
		}
		chars = append(chars, self.Advance())
	}
	var word string
	if len(chars) > 0 {
		word = strings.Join(chars, "")
	} else {
		word = ""
	}
	self.Pos = savedPos
	return word
}

func (self *Parser) ConsumeWord(expected string) bool {
	savedPos := self.Pos
	self.SkipWhitespace()
	word := self.PeekWord()
	keywordWord := word
	hasLeadingBrace := false
	if word != "" && self.inProcessSub && _runeLen(word) > 1 && string(_runeAt(word, 0)) == "}" {
		keywordWord = _Substring(word, 1, _runeLen(word))
		hasLeadingBrace = true
	}
	if keywordWord != expected {
		self.Pos = savedPos
		return false
	}
	self.SkipWhitespace()
	if hasLeadingBrace {
		self.Advance()
	}
	for range expected {
		self.Advance()
	}
	for self.Peek() == "\\" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "\n" {
		self.Advance()
		self.Advance()
	}
	return true
}

func (self *Parser) isWordTerminator(ctx int, ch string, bracketDepth int, parenDepth int) bool {
	self.syncLexer()
	return self.lexer.isWordTerminator(ctx, ch, bracketDepth, parenDepth)
}

func (self *Parser) scanDoubleQuote(chars *[]string, parts []Node, start int, handleLineContinuation bool) {
	*chars = append(*chars, "\"")
	for !self.AtEnd() && self.Peek() != "\"" {
		c := self.Peek()
		if c == "\\" && self.Pos+1 < self.Length {
			nextC := string(_runeAt(self.Source, self.Pos+1))
			if handleLineContinuation && nextC == "\n" {
				self.Advance()
				self.Advance()
			} else {
				*chars = append(*chars, self.Advance())
				*chars = append(*chars, self.Advance())
			}
		} else if c == "$" {
			if !self.parseDollarExpansion(chars, &parts, true) {
				*chars = append(*chars, self.Advance())
			}
		} else {
			*chars = append(*chars, self.Advance())
		}
	}
	if self.AtEnd() {
		panic(NewParseError("Unterminated double quote", start, 0))
	}
	*chars = append(*chars, self.Advance())
}

func (self *Parser) parseDollarExpansion(chars *[]string, parts *[]Node, inDquote bool) bool {
	var result0 Node
	var result1 string
	if self.Pos+2 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "(" && string(_runeAt(self.Source, self.Pos+2)) == "(" {
		result0, result1 = self.parseArithmeticExpansion()
		if !_isNilInterface(result0) {
			*parts = append(*parts, result0)
			*chars = append(*chars, result1)
			return true
		}
		result0, result1 = self.parseCommandSubstitution()
		if !_isNilInterface(result0) {
			*parts = append(*parts, result0)
			*chars = append(*chars, result1)
			return true
		}
		return false
	}
	if self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "[" {
		result0, result1 = self.parseDeprecatedArithmetic()
		if !_isNilInterface(result0) {
			*parts = append(*parts, result0)
			*chars = append(*chars, result1)
			return true
		}
		return false
	}
	if self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "(" {
		result0, result1 = self.parseCommandSubstitution()
		if !_isNilInterface(result0) {
			*parts = append(*parts, result0)
			*chars = append(*chars, result1)
			return true
		}
		return false
	}
	result0, result1 = self.parseParamExpansion(inDquote)
	if !_isNilInterface(result0) {
		*parts = append(*parts, result0)
		*chars = append(*chars, result1)
		return true
	}
	return false
}

func (self *Parser) parseWordInternal(ctx int, atCommandStart bool, inArrayLiteral bool) *Word {
	self.wordContext = ctx
	return self.ParseWord(atCommandStart, inArrayLiteral, false)
}

func (self *Parser) ParseWord(atCommandStart bool, inArrayLiteral bool, inAssignBuiltin bool) *Word {
	self.SkipWhitespace()
	if self.AtEnd() {
		return nil
	}
	self.atCommandStart = atCommandStart
	self.inArrayLiteral = inArrayLiteral
	self.inAssignBuiltin = inAssignBuiltin
	tok := self.lexPeekToken()
	if tok.Type != TokenTypeWORD {
		self.atCommandStart = false
		self.inArrayLiteral = false
		self.inAssignBuiltin = false
		return nil
	}
	self.lexNextToken()
	self.atCommandStart = false
	self.inArrayLiteral = false
	self.inAssignBuiltin = false
	return tok.Word
}

func (self *Parser) parseCommandSubstitution() (Node, string) {
	if self.AtEnd() || self.Peek() != "$" {
		return nil, ""
	}
	start := self.Pos
	self.Advance()
	if self.AtEnd() || self.Peek() != "(" {
		self.Pos = start
		return nil, ""
	}
	self.Advance()
	saved := self.saveParserState()
	self.setState((ParserStateFlagsPSTCMDSUBST | ParserStateFlagsPSTEOFTOKEN))
	self.eofToken = ")"
	cmd := self.ParseList(true)
	if cmd == nil {
		cmd = &Empty{Kind: "empty"}
	}
	self.SkipWhitespaceAndNewlines()
	if self.AtEnd() || self.Peek() != ")" {
		self.restoreParserState(saved)
		self.Pos = start
		return nil, ""
	}
	self.Advance()
	textEnd := self.Pos
	text := substring(self.Source, start, textEnd)
	self.restoreParserState(saved)
	return &CommandSubstitution{Command: cmd, Kind: "cmdsub"}, text
}

func (self *Parser) parseFunsub(start int) (Node, string) {
	self.syncParser()
	if !self.AtEnd() && self.Peek() == "|" {
		self.Advance()
	}
	saved := self.saveParserState()
	self.setState((ParserStateFlagsPSTCMDSUBST | ParserStateFlagsPSTEOFTOKEN))
	self.eofToken = "}"
	cmd := self.ParseList(true)
	if cmd == nil {
		cmd = &Empty{Kind: "empty"}
	}
	self.SkipWhitespaceAndNewlines()
	if self.AtEnd() || self.Peek() != "}" {
		self.restoreParserState(saved)
		panic(NewMatchedPairError("unexpected EOF looking for `}'", start, 0))
	}
	self.Advance()
	text := substring(self.Source, start, self.Pos)
	self.restoreParserState(saved)
	self.syncLexer()
	return &CommandSubstitution{Command: cmd, Brace: true, Kind: "cmdsub"}, text
}

func (self *Parser) isAssignmentWord(word Node) bool {
	return assignment(word.(*Word).Value, 0) != -1
}

func (self *Parser) parseBacktickSubstitution() (Node, string) {
	if self.AtEnd() || self.Peek() != "`" {
		return nil, ""
	}
	start := self.Pos
	self.Advance()
	contentChars := []string{}
	textChars := []string{"`"}
	pendingHeredocs := []struct {
		F0 string
		F1 bool
	}{}
	inHeredocBody := false
	currentHeredocDelim := ""
	currentHeredocStrip := false
	for !self.AtEnd() && (inHeredocBody || self.Peek() != "`") {
		if inHeredocBody {
			lineStart := self.Pos
			lineEnd := lineStart
			for lineEnd < self.Length && string(_runeAt(self.Source, lineEnd)) != "\n" {
				lineEnd++
			}
			line := substring(self.Source, lineStart, lineEnd)
			checkLine := func() string {
				if currentHeredocStrip {
					return strings.TrimLeft(line, "\t")
				} else {
					return line
				}
			}()
			if checkLine == currentHeredocDelim {
				for _, ch := range line {
					contentChars = append(contentChars, string(ch))
					textChars = append(textChars, string(ch))
				}
				self.Pos = lineEnd
				if self.Pos < self.Length && string(_runeAt(self.Source, self.Pos)) == "\n" {
					contentChars = append(contentChars, "\n")
					textChars = append(textChars, "\n")
					self.Advance()
				}
				inHeredocBody = false
				if len(pendingHeredocs) > 0 {
					{
						var entry struct {
							F0 string
							F1 bool
						} = pendingHeredocs[len(pendingHeredocs)-1]
						pendingHeredocs = pendingHeredocs[:len(pendingHeredocs)-1]
						currentHeredocDelim = entry.F0
						currentHeredocStrip = entry.F1
					}
					inHeredocBody = true
				}
			} else if strings.HasPrefix(checkLine, currentHeredocDelim) && _runeLen(checkLine) > _runeLen(currentHeredocDelim) {
				tabsStripped := _runeLen(line) - _runeLen(checkLine)
				endPos := tabsStripped + _runeLen(currentHeredocDelim)
				for _, i := range Range(endPos) {
					contentChars = append(contentChars, string(_runeAt(line, i)))
					textChars = append(textChars, string(_runeAt(line, i)))
				}
				self.Pos = lineStart + endPos
				inHeredocBody = false
				if len(pendingHeredocs) > 0 {
					{
						var entry struct {
							F0 string
							F1 bool
						} = pendingHeredocs[len(pendingHeredocs)-1]
						pendingHeredocs = pendingHeredocs[:len(pendingHeredocs)-1]
						currentHeredocDelim = entry.F0
						currentHeredocStrip = entry.F1
					}
					inHeredocBody = true
				}
			} else {
				for _, ch := range line {
					contentChars = append(contentChars, string(ch))
					textChars = append(textChars, string(ch))
				}
				self.Pos = lineEnd
				if self.Pos < self.Length && string(_runeAt(self.Source, self.Pos)) == "\n" {
					contentChars = append(contentChars, "\n")
					textChars = append(textChars, "\n")
					self.Advance()
				}
			}
			continue
		}
		c := self.Peek()
		var ch string
		if c == "\\" && self.Pos+1 < self.Length {
			nextC := string(_runeAt(self.Source, self.Pos+1))
			if nextC == "\n" {
				self.Advance()
				self.Advance()
			} else if isEscapeCharInBacktick(nextC) {
				self.Advance()
				escaped := self.Advance()
				contentChars = append(contentChars, escaped)
				textChars = append(textChars, "\\")
				textChars = append(textChars, escaped)
			} else {
				ch = self.Advance()
				contentChars = append(contentChars, ch)
				textChars = append(textChars, ch)
			}
			continue
		}
		if c == "<" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "<" {
			var quote string
			if self.Pos+2 < self.Length && string(_runeAt(self.Source, self.Pos+2)) == "<" {
				contentChars = append(contentChars, self.Advance())
				textChars = append(textChars, "<")
				contentChars = append(contentChars, self.Advance())
				textChars = append(textChars, "<")
				contentChars = append(contentChars, self.Advance())
				textChars = append(textChars, "<")
				for !self.AtEnd() && isWhitespaceNoNewline(self.Peek()) {
					ch = self.Advance()
					contentChars = append(contentChars, ch)
					textChars = append(textChars, ch)
				}
				for !self.AtEnd() && !isWhitespace(self.Peek()) && !strings.Contains("()", self.Peek()) {
					if self.Peek() == "\\" && self.Pos+1 < self.Length {
						ch = self.Advance()
						contentChars = append(contentChars, ch)
						textChars = append(textChars, ch)
						ch = self.Advance()
						contentChars = append(contentChars, ch)
						textChars = append(textChars, ch)
					} else if strings.Contains("\"'", self.Peek()) {
						quote = self.Peek()
						ch = self.Advance()
						contentChars = append(contentChars, ch)
						textChars = append(textChars, ch)
						for !self.AtEnd() && self.Peek() != quote {
							if quote == "\"" && self.Peek() == "\\" {
								ch = self.Advance()
								contentChars = append(contentChars, ch)
								textChars = append(textChars, ch)
							}
							ch = self.Advance()
							contentChars = append(contentChars, ch)
							textChars = append(textChars, ch)
						}
						if !self.AtEnd() {
							ch = self.Advance()
							contentChars = append(contentChars, ch)
							textChars = append(textChars, ch)
						}
					} else {
						ch = self.Advance()
						contentChars = append(contentChars, ch)
						textChars = append(textChars, ch)
					}
				}
				continue
			}
			contentChars = append(contentChars, self.Advance())
			textChars = append(textChars, "<")
			contentChars = append(contentChars, self.Advance())
			textChars = append(textChars, "<")
			stripTabs := false
			if !self.AtEnd() && self.Peek() == "-" {
				stripTabs = true
				contentChars = append(contentChars, self.Advance())
				textChars = append(textChars, "-")
			}
			for !self.AtEnd() && isWhitespaceNoNewline(self.Peek()) {
				ch = self.Advance()
				contentChars = append(contentChars, ch)
				textChars = append(textChars, ch)
			}
			delimiterChars := []string{}
			if !self.AtEnd() {
				ch = self.Peek()
				var dch string
				var closing string
				if isQuote(ch) {
					quote = self.Advance()
					contentChars = append(contentChars, quote)
					textChars = append(textChars, quote)
					for !self.AtEnd() && self.Peek() != quote {
						dch = self.Advance()
						contentChars = append(contentChars, dch)
						textChars = append(textChars, dch)
						delimiterChars = append(delimiterChars, dch)
					}
					if !self.AtEnd() {
						closing = self.Advance()
						contentChars = append(contentChars, closing)
						textChars = append(textChars, closing)
					}
				} else if ch == "\\" {
					esc := self.Advance()
					contentChars = append(contentChars, esc)
					textChars = append(textChars, esc)
					if !self.AtEnd() {
						dch = self.Advance()
						contentChars = append(contentChars, dch)
						textChars = append(textChars, dch)
						delimiterChars = append(delimiterChars, dch)
					}
					for !self.AtEnd() && !isMetachar(self.Peek()) {
						dch = self.Advance()
						contentChars = append(contentChars, dch)
						textChars = append(textChars, dch)
						delimiterChars = append(delimiterChars, dch)
					}
				} else {
					for !self.AtEnd() && !isMetachar(self.Peek()) && self.Peek() != "`" {
						ch = self.Peek()
						if isQuote(ch) {
							quote = self.Advance()
							contentChars = append(contentChars, quote)
							textChars = append(textChars, quote)
							for !self.AtEnd() && self.Peek() != quote {
								dch = self.Advance()
								contentChars = append(contentChars, dch)
								textChars = append(textChars, dch)
								delimiterChars = append(delimiterChars, dch)
							}
							if !self.AtEnd() {
								closing = self.Advance()
								contentChars = append(contentChars, closing)
								textChars = append(textChars, closing)
							}
						} else if ch == "\\" {
							esc := self.Advance()
							contentChars = append(contentChars, esc)
							textChars = append(textChars, esc)
							if !self.AtEnd() {
								dch = self.Advance()
								contentChars = append(contentChars, dch)
								textChars = append(textChars, dch)
								delimiterChars = append(delimiterChars, dch)
							}
						} else {
							dch = self.Advance()
							contentChars = append(contentChars, dch)
							textChars = append(textChars, dch)
							delimiterChars = append(delimiterChars, dch)
						}
					}
				}
			}
			delimiter := strings.Join(delimiterChars, "")
			if delimiter != "" {
				pendingHeredocs = append(pendingHeredocs, struct {
					F0 string
					F1 bool
				}{delimiter, stripTabs})
			}
			continue
		}
		if c == "\n" {
			ch = self.Advance()
			contentChars = append(contentChars, ch)
			textChars = append(textChars, ch)
			if len(pendingHeredocs) > 0 {
				{
					var entry struct {
						F0 string
						F1 bool
					} = pendingHeredocs[len(pendingHeredocs)-1]
					pendingHeredocs = pendingHeredocs[:len(pendingHeredocs)-1]
					currentHeredocDelim = entry.F0
					currentHeredocStrip = entry.F1
				}
				inHeredocBody = true
			}
			continue
		}
		ch = self.Advance()
		contentChars = append(contentChars, ch)
		textChars = append(textChars, ch)
	}
	if self.AtEnd() {
		panic(NewParseError("Unterminated backtick", start, 0))
	}
	self.Advance()
	textChars = append(textChars, "`")
	text := strings.Join(textChars, "")
	content := strings.Join(contentChars, "")
	if len(pendingHeredocs) > 0 {
		heredocStart, heredocEnd := findHeredocContentEnd(self.Source, self.Pos, pendingHeredocs)
		if heredocEnd > heredocStart {
			content = content + substring(self.Source, heredocStart, heredocEnd)
			if self.cmdsubHeredocEnd == -1 {
				self.cmdsubHeredocEnd = heredocEnd
			} else {
				self.cmdsubHeredocEnd = func() int {
					if self.cmdsubHeredocEnd > heredocEnd {
						return self.cmdsubHeredocEnd
					} else {
						return heredocEnd
					}
				}()
			}
		}
	}
	subParser := NewParser(content, false, self.extglob)
	cmd := subParser.ParseList(true)
	if cmd == nil {
		cmd = &Empty{Kind: "empty"}
	}
	return &CommandSubstitution{Command: cmd, Kind: "cmdsub"}, text
}

func (self *Parser) parseProcessSubstitution() (result0 Node, result1 string) {
	if self.AtEnd() || !isRedirectChar(self.Peek()) {
		return nil, ""
	}
	start := self.Pos
	direction := self.Advance()
	if self.AtEnd() || self.Peek() != "(" {
		self.Pos = start
		return nil, ""
	}
	self.Advance()
	saved := self.saveParserState()
	oldInProcessSub := self.inProcessSub
	self.inProcessSub = true
	self.setState(ParserStateFlagsPSTEOFTOKEN)
	self.eofToken = ")"
	defer func() {
		if e := recover(); e != nil {
			self.restoreParserState(saved)
			self.inProcessSub = oldInProcessSub
			contentStartChar := func() string {
				if start+2 < self.Length {
					return string(_runeAt(self.Source, start+2))
				} else {
					return ""
				}
			}()
			if strings.Contains(" \t\n", contentStartChar) {
				panic(e)
			}
			self.Pos = start + 2
			self.lexer.Pos = self.Pos
			self.lexer.parseMatchedPair("(", ")", 0, false)
			self.Pos = self.lexer.Pos
			text := substring(self.Source, start, self.Pos)
			text = stripLineContinuationsCommentAware(text)
			result0 = nil
			result1 = text
		}
	}()
	cmd := self.ParseList(true)
	if cmd == nil {
		cmd = &Empty{Kind: "empty"}
	}
	self.SkipWhitespaceAndNewlines()
	if self.AtEnd() || self.Peek() != ")" {
		panic(NewParseError("Invalid process substitution", start, 0))
	}
	self.Advance()
	textEnd := self.Pos
	text := substring(self.Source, start, textEnd)
	text = stripLineContinuationsCommentAware(text)
	self.restoreParserState(saved)
	self.inProcessSub = oldInProcessSub
	return &ProcessSubstitution{Direction: direction, Command: cmd, Kind: "procsub"}, text
}

func (self *Parser) parseArrayLiteral() (Node, string) {
	if self.AtEnd() || self.Peek() != "(" {
		return nil, ""
	}
	start := self.Pos
	self.Advance()
	self.setState(ParserStateFlagsPSTCOMPASSIGN)
	elements := []*Word{}
	for true {
		self.SkipWhitespaceAndNewlines()
		if self.AtEnd() {
			self.clearState(ParserStateFlagsPSTCOMPASSIGN)
			panic(NewParseError("Unterminated array literal", start, 0))
		}
		if self.Peek() == ")" {
			break
		}
		word := self.ParseWord(false, true, false)
		if word == nil {
			if self.Peek() == ")" {
				break
			}
			self.clearState(ParserStateFlagsPSTCOMPASSIGN)
			panic(NewParseError("Expected word in array literal", self.Pos, 0))
		}
		elements = append(elements, word)
	}
	if self.AtEnd() || self.Peek() != ")" {
		self.clearState(ParserStateFlagsPSTCOMPASSIGN)
		panic(NewParseError("Expected ) to close array literal", self.Pos, 0))
	}
	self.Advance()
	text := substring(self.Source, start, self.Pos)
	self.clearState(ParserStateFlagsPSTCOMPASSIGN)
	return &Array{Elements: elements, Kind: "array"}, text
}

func (self *Parser) parseArithmeticExpansion() (result0 Node, result1 string) {
	if self.AtEnd() || self.Peek() != "$" {
		return nil, ""
	}
	start := self.Pos
	if self.Pos+2 >= self.Length || string(_runeAt(self.Source, self.Pos+1)) != "(" || string(_runeAt(self.Source, self.Pos+2)) != "(" {
		return nil, ""
	}
	self.Advance()
	self.Advance()
	self.Advance()
	contentStart := self.Pos
	depth := 2
	firstClosePos := -1
	for !self.AtEnd() && depth > 0 {
		c := self.Peek()
		if c == "'" {
			self.Advance()
			for !self.AtEnd() && self.Peek() != "'" {
				self.Advance()
			}
			if !self.AtEnd() {
				self.Advance()
			}
		} else if c == "\"" {
			self.Advance()
			for !self.AtEnd() {
				if self.Peek() == "\\" && self.Pos+1 < self.Length {
					self.Advance()
					self.Advance()
				} else if self.Peek() == "\"" {
					self.Advance()
					break
				} else {
					self.Advance()
				}
			}
		} else if c == "\\" && self.Pos+1 < self.Length {
			self.Advance()
			self.Advance()
		} else if c == "(" {
			depth++
			self.Advance()
		} else if c == ")" {
			if depth == 2 {
				firstClosePos = self.Pos
			}
			depth--
			if depth == 0 {
				break
			}
			self.Advance()
		} else {
			if depth == 1 {
				firstClosePos = -1
			}
			self.Advance()
		}
	}
	if depth != 0 {
		if self.AtEnd() {
			panic(NewMatchedPairError("unexpected EOF looking for `))'", start, 0))
		}
		self.Pos = start
		return nil, ""
	}
	var content string
	if firstClosePos != -1 {
		content = substring(self.Source, contentStart, firstClosePos)
	} else {
		content = substring(self.Source, contentStart, self.Pos)
	}
	self.Advance()
	text := substring(self.Source, start, self.Pos)
	var expr Node
	defer func() {
		if r := recover(); r != nil {
			self.Pos = start
			result0 = nil
			result1 = ""
		}
	}()
	expr = self.parseArithExpr(content)
	return &ArithmeticExpansion{Expression: expr, Kind: "arith"}, text
}

func (self *Parser) parseArithExpr(content string) Node {
	savedArithSrc := self.arithSrc
	savedArithPos := self.arithPos
	savedArithLen := self.arithLen
	savedParserState := self.parserState
	self.setState(ParserStateFlagsPSTARITH)
	self.arithSrc = content
	self.arithPos = 0
	self.arithLen = _runeLen(content)
	self.arithSkipWs()
	var result Node
	if self.arithAtEnd() {
		result = nil
	} else {
		result = self.arithParseComma()
	}
	self.parserState = savedParserState
	if savedArithSrc != "" {
		self.arithSrc = savedArithSrc
		self.arithPos = savedArithPos
		self.arithLen = savedArithLen
	}
	return result
}

func (self *Parser) arithAtEnd() bool {
	return self.arithPos >= self.arithLen
}

func (self *Parser) arithPeek(offset int) string {
	pos := self.arithPos + offset
	if pos >= self.arithLen {
		return ""
	}
	return string(_runeAt(self.arithSrc, pos))
}

func (self *Parser) arithAdvance() string {
	if self.arithAtEnd() {
		return ""
	}
	c := string(_runeAt(self.arithSrc, self.arithPos))
	self.arithPos++
	return c
}

func (self *Parser) arithSkipWs() {
	for !self.arithAtEnd() {
		c := string(_runeAt(self.arithSrc, self.arithPos))
		if isWhitespace(c) {
			self.arithPos++
		} else if c == "\\" && self.arithPos+1 < self.arithLen && string(_runeAt(self.arithSrc, self.arithPos+1)) == "\n" {
			self.arithPos += 2
		} else {
			break
		}
	}
}

func (self *Parser) arithMatch(s string) bool {
	return startsWithAt(self.arithSrc, self.arithPos, s)
}

func (self *Parser) arithConsume(s string) bool {
	if self.arithMatch(s) {
		self.arithPos += _runeLen(s)
		return true
	}
	return false
}

func (self *Parser) arithParseComma() Node {
	left := self.arithParseAssign()
	for true {
		self.arithSkipWs()
		if self.arithConsume(",") {
			self.arithSkipWs()
			right := self.arithParseAssign()
			left = &ArithComma{Left: left, Right: right, Kind: "comma"}
		} else {
			break
		}
	}
	return left
}

func (self *Parser) arithParseAssign() Node {
	left := self.arithParseTernary()
	self.arithSkipWs()
	assignOps := []string{"<<=", ">>=", "+=", "-=", "*=", "/=", "%=", "&=", "^=", "|=", "="}
	for _, op := range assignOps {
		if self.arithMatch(op) {
			if op == "=" && self.arithPeek(1) == "=" {
				break
			}
			self.arithConsume(op)
			self.arithSkipWs()
			right := self.arithParseAssign()
			return &ArithAssign{Op: op, Target: left, Value: right, Kind: "assign"}
		}
	}
	return left
}

func (self *Parser) arithParseTernary() Node {
	cond := self.arithParseLogicalOr()
	self.arithSkipWs()
	if self.arithConsume("?") {
		self.arithSkipWs()
		var ifTrue Node
		if self.arithMatch(":") {
			ifTrue = nil
		} else {
			ifTrue = self.arithParseAssign()
		}
		self.arithSkipWs()
		var ifFalse Node
		if self.arithConsume(":") {
			self.arithSkipWs()
			if self.arithAtEnd() || self.arithPeek(0) == ")" {
				ifFalse = nil
			} else {
				ifFalse = self.arithParseTernary()
			}
		} else {
			ifFalse = nil
		}
		return &ArithTernary{Condition: cond, IfTrue: ifTrue, IfFalse: ifFalse, Kind: "ternary"}
	}
	return cond
}

func (self *Parser) arithParseLeftAssoc(ops []string, parsefn func() Node) Node {
	left := parsefn()
	for true {
		self.arithSkipWs()
		matched := false
		for _, op := range ops {
			if self.arithMatch(op) {
				self.arithConsume(op)
				self.arithSkipWs()
				left = &ArithBinaryOp{Op: op, Left: left, Right: parsefn(), Kind: "binary-op"}
				matched = true
				break
			}
		}
		if !matched {
			break
		}
	}
	return left
}

func (self *Parser) arithParseLogicalOr() Node {
	return self.arithParseLeftAssoc([]string{"||"}, self.arithParseLogicalAnd)
}

func (self *Parser) arithParseLogicalAnd() Node {
	return self.arithParseLeftAssoc([]string{"&&"}, self.arithParseBitwiseOr)
}

func (self *Parser) arithParseBitwiseOr() Node {
	left := self.arithParseBitwiseXor()
	for true {
		self.arithSkipWs()
		if self.arithPeek(0) == "|" && self.arithPeek(1) != "|" && self.arithPeek(1) != "=" {
			self.arithAdvance()
			self.arithSkipWs()
			right := self.arithParseBitwiseXor()
			left = &ArithBinaryOp{Op: "|", Left: left, Right: right, Kind: "binary-op"}
		} else {
			break
		}
	}
	return left
}

func (self *Parser) arithParseBitwiseXor() Node {
	left := self.arithParseBitwiseAnd()
	for true {
		self.arithSkipWs()
		if self.arithPeek(0) == "^" && self.arithPeek(1) != "=" {
			self.arithAdvance()
			self.arithSkipWs()
			right := self.arithParseBitwiseAnd()
			left = &ArithBinaryOp{Op: "^", Left: left, Right: right, Kind: "binary-op"}
		} else {
			break
		}
	}
	return left
}

func (self *Parser) arithParseBitwiseAnd() Node {
	left := self.arithParseEquality()
	for true {
		self.arithSkipWs()
		if self.arithPeek(0) == "&" && self.arithPeek(1) != "&" && self.arithPeek(1) != "=" {
			self.arithAdvance()
			self.arithSkipWs()
			right := self.arithParseEquality()
			left = &ArithBinaryOp{Op: "&", Left: left, Right: right, Kind: "binary-op"}
		} else {
			break
		}
	}
	return left
}

func (self *Parser) arithParseEquality() Node {
	return self.arithParseLeftAssoc([]string{"==", "!="}, self.arithParseComparison)
}

func (self *Parser) arithParseComparison() Node {
	left := self.arithParseShift()
	for true {
		self.arithSkipWs()
		var right Node
		if self.arithMatch("<=") {
			self.arithConsume("<=")
			self.arithSkipWs()
			right = self.arithParseShift()
			left = &ArithBinaryOp{Op: "<=", Left: left, Right: right, Kind: "binary-op"}
		} else if self.arithMatch(">=") {
			self.arithConsume(">=")
			self.arithSkipWs()
			right = self.arithParseShift()
			left = &ArithBinaryOp{Op: ">=", Left: left, Right: right, Kind: "binary-op"}
		} else if self.arithPeek(0) == "<" && self.arithPeek(1) != "<" && self.arithPeek(1) != "=" {
			self.arithAdvance()
			self.arithSkipWs()
			right = self.arithParseShift()
			left = &ArithBinaryOp{Op: "<", Left: left, Right: right, Kind: "binary-op"}
		} else if self.arithPeek(0) == ">" && self.arithPeek(1) != ">" && self.arithPeek(1) != "=" {
			self.arithAdvance()
			self.arithSkipWs()
			right = self.arithParseShift()
			left = &ArithBinaryOp{Op: ">", Left: left, Right: right, Kind: "binary-op"}
		} else {
			break
		}
	}
	return left
}

func (self *Parser) arithParseShift() Node {
	left := self.arithParseAdditive()
	for true {
		self.arithSkipWs()
		if self.arithMatch("<<=") {
			break
		}
		if self.arithMatch(">>=") {
			break
		}
		var right Node
		if self.arithMatch("<<") {
			self.arithConsume("<<")
			self.arithSkipWs()
			right = self.arithParseAdditive()
			left = &ArithBinaryOp{Op: "<<", Left: left, Right: right, Kind: "binary-op"}
		} else if self.arithMatch(">>") {
			self.arithConsume(">>")
			self.arithSkipWs()
			right = self.arithParseAdditive()
			left = &ArithBinaryOp{Op: ">>", Left: left, Right: right, Kind: "binary-op"}
		} else {
			break
		}
	}
	return left
}

func (self *Parser) arithParseAdditive() Node {
	left := self.arithParseMultiplicative()
	for true {
		self.arithSkipWs()
		c := self.arithPeek(0)
		c2 := self.arithPeek(1)
		var right Node
		if c == "+" && c2 != "+" && c2 != "=" {
			self.arithAdvance()
			self.arithSkipWs()
			right = self.arithParseMultiplicative()
			left = &ArithBinaryOp{Op: "+", Left: left, Right: right, Kind: "binary-op"}
		} else if c == "-" && c2 != "-" && c2 != "=" {
			self.arithAdvance()
			self.arithSkipWs()
			right = self.arithParseMultiplicative()
			left = &ArithBinaryOp{Op: "-", Left: left, Right: right, Kind: "binary-op"}
		} else {
			break
		}
	}
	return left
}

func (self *Parser) arithParseMultiplicative() Node {
	left := self.arithParseExponentiation()
	for true {
		self.arithSkipWs()
		c := self.arithPeek(0)
		c2 := self.arithPeek(1)
		var right Node
		if c == "*" && c2 != "*" && c2 != "=" {
			self.arithAdvance()
			self.arithSkipWs()
			right = self.arithParseExponentiation()
			left = &ArithBinaryOp{Op: "*", Left: left, Right: right, Kind: "binary-op"}
		} else if c == "/" && c2 != "=" {
			self.arithAdvance()
			self.arithSkipWs()
			right = self.arithParseExponentiation()
			left = &ArithBinaryOp{Op: "/", Left: left, Right: right, Kind: "binary-op"}
		} else if c == "%" && c2 != "=" {
			self.arithAdvance()
			self.arithSkipWs()
			right = self.arithParseExponentiation()
			left = &ArithBinaryOp{Op: "%", Left: left, Right: right, Kind: "binary-op"}
		} else {
			break
		}
	}
	return left
}

func (self *Parser) arithParseExponentiation() Node {
	left := self.arithParseUnary()
	self.arithSkipWs()
	if self.arithMatch("**") {
		self.arithConsume("**")
		self.arithSkipWs()
		right := self.arithParseExponentiation()
		return &ArithBinaryOp{Op: "**", Left: left, Right: right, Kind: "binary-op"}
	}
	return left
}

func (self *Parser) arithParseUnary() Node {
	self.arithSkipWs()
	var operand Node
	if self.arithMatch("++") {
		self.arithConsume("++")
		self.arithSkipWs()
		operand = self.arithParseUnary()
		return &ArithPreIncr{Operand: operand, Kind: "pre-incr"}
	}
	if self.arithMatch("--") {
		self.arithConsume("--")
		self.arithSkipWs()
		operand = self.arithParseUnary()
		return &ArithPreDecr{Operand: operand, Kind: "pre-decr"}
	}
	c := self.arithPeek(0)
	if c == "!" {
		self.arithAdvance()
		self.arithSkipWs()
		operand = self.arithParseUnary()
		return &ArithUnaryOp{Op: "!", Operand: operand, Kind: "unary-op"}
	}
	if c == "~" {
		self.arithAdvance()
		self.arithSkipWs()
		operand = self.arithParseUnary()
		return &ArithUnaryOp{Op: "~", Operand: operand, Kind: "unary-op"}
	}
	if c == "+" && self.arithPeek(1) != "+" {
		self.arithAdvance()
		self.arithSkipWs()
		operand = self.arithParseUnary()
		return &ArithUnaryOp{Op: "+", Operand: operand, Kind: "unary-op"}
	}
	if c == "-" && self.arithPeek(1) != "-" {
		self.arithAdvance()
		self.arithSkipWs()
		operand = self.arithParseUnary()
		return &ArithUnaryOp{Op: "-", Operand: operand, Kind: "unary-op"}
	}
	return self.arithParsePostfix()
}

func (self *Parser) arithParsePostfix() Node {
	left := self.arithParsePrimary()
	for true {
		self.arithSkipWs()
		if self.arithMatch("++") {
			self.arithConsume("++")
			left = &ArithPostIncr{Operand: left, Kind: "post-incr"}
		} else if self.arithMatch("--") {
			self.arithConsume("--")
			left = &ArithPostDecr{Operand: left, Kind: "post-decr"}
		} else if self.arithPeek(0) == "[" {
			if leftVar, ok := left.(*ArithVar); ok {
				self.arithAdvance()
				self.arithSkipWs()
				index := self.arithParseComma()
				self.arithSkipWs()
				if !self.arithConsume("]") {
					panic(NewParseError("Expected ']' in array subscript", self.arithPos, 0))
				}
				left = &ArithSubscript{Array: leftVar.Name, Index: index, Kind: "subscript"}
			} else {
				break
			}
		} else {
			break
		}
	}
	return left
}

func (self *Parser) arithParsePrimary() Node {
	self.arithSkipWs()
	c := self.arithPeek(0)
	if c == "(" {
		self.arithAdvance()
		self.arithSkipWs()
		expr := self.arithParseComma()
		self.arithSkipWs()
		if !self.arithConsume(")") {
			panic(NewParseError("Expected ')' in arithmetic expression", self.arithPos, 0))
		}
		return expr
	}
	if c == "#" && self.arithPeek(1) == "$" {
		self.arithAdvance()
		return self.arithParseExpansion()
	}
	if c == "$" {
		return self.arithParseExpansion()
	}
	if c == "'" {
		return self.arithParseSingleQuote()
	}
	if c == "\"" {
		return self.arithParseDoubleQuote()
	}
	if c == "`" {
		return self.arithParseBacktick()
	}
	if c == "\\" {
		self.arithAdvance()
		if self.arithAtEnd() {
			panic(NewParseError("Unexpected end after backslash in arithmetic", self.arithPos, 0))
		}
		escapedChar := self.arithAdvance()
		return &ArithEscape{Char: escapedChar, Kind: "escape"}
	}
	if self.arithAtEnd() || strings.Contains(")]:,;?|&<>=!+-*/%^~#{}", c) {
		return &ArithEmpty{Kind: "empty"}
	}
	return self.arithParseNumberOrVar()
}

func (self *Parser) arithParseExpansion() Node {
	if !self.arithConsume("$") {
		panic(NewParseError("Expected '$'", self.arithPos, 0))
	}
	c := self.arithPeek(0)
	if c == "(" {
		return self.arithParseCmdsub()
	}
	if c == "{" {
		return self.arithParseBracedParam()
	}
	nameChars := []string{}
	for !self.arithAtEnd() {
		ch := self.arithPeek(0)
		if _strIsAlnum(ch) || ch == "_" {
			nameChars = append(nameChars, self.arithAdvance())
		} else if (isSpecialParamOrDigit(ch) || ch == "#") && !(len(nameChars) > 0) {
			nameChars = append(nameChars, self.arithAdvance())
			break
		} else {
			break
		}
	}
	if !(len(nameChars) > 0) {
		panic(NewParseError("Expected variable name after $", self.arithPos, 0))
	}
	return &ParamExpansion{Param: strings.Join(nameChars, ""), Kind: "param"}
}

func (self *Parser) arithParseCmdsub() Node {
	self.arithAdvance()
	var depth int
	var contentStart int
	var ch string
	var content string
	if self.arithPeek(0) == "(" {
		self.arithAdvance()
		depth = 1
		contentStart = self.arithPos
		for !self.arithAtEnd() && depth > 0 {
			ch = self.arithPeek(0)
			if ch == "(" {
				depth++
				self.arithAdvance()
			} else if ch == ")" {
				if depth == 1 && self.arithPeek(1) == ")" {
					break
				}
				depth--
				self.arithAdvance()
			} else {
				self.arithAdvance()
			}
		}
		content = substring(self.arithSrc, contentStart, self.arithPos)
		self.arithAdvance()
		self.arithAdvance()
		innerExpr := self.parseArithExpr(content)
		return &ArithmeticExpansion{Expression: innerExpr, Kind: "arith"}
	}
	depth = 1
	contentStart = self.arithPos
	for !self.arithAtEnd() && depth > 0 {
		ch = self.arithPeek(0)
		if ch == "(" {
			depth++
			self.arithAdvance()
		} else if ch == ")" {
			depth--
			if depth == 0 {
				break
			}
			self.arithAdvance()
		} else {
			self.arithAdvance()
		}
	}
	content = substring(self.arithSrc, contentStart, self.arithPos)
	self.arithAdvance()
	subParser := NewParser(content, false, self.extglob)
	cmd := subParser.ParseList(true)
	return &CommandSubstitution{Command: cmd, Kind: "cmdsub"}
}

func (self *Parser) arithParseBracedParam() Node {
	self.arithAdvance()
	var nameChars []string
	if self.arithPeek(0) == "!" {
		self.arithAdvance()
		nameChars = []string{}
		for !self.arithAtEnd() && self.arithPeek(0) != "}" {
			nameChars = append(nameChars, self.arithAdvance())
		}
		self.arithConsume("}")
		return &ParamIndirect{Param: strings.Join(nameChars, ""), Kind: "param-indirect"}
	}
	if self.arithPeek(0) == "#" {
		self.arithAdvance()
		nameChars = []string{}
		for !self.arithAtEnd() && self.arithPeek(0) != "}" {
			nameChars = append(nameChars, self.arithAdvance())
		}
		self.arithConsume("}")
		return &ParamLength{Param: strings.Join(nameChars, ""), Kind: "param-len"}
	}
	nameChars = []string{}
	var ch string
	for !self.arithAtEnd() {
		ch = self.arithPeek(0)
		if ch == "}" {
			self.arithAdvance()
			return &ParamExpansion{Param: strings.Join(nameChars, ""), Kind: "param"}
		}
		if isParamExpansionOp(ch) {
			break
		}
		nameChars = append(nameChars, self.arithAdvance())
	}
	name := strings.Join(nameChars, "")
	opChars := []string{}
	depth := 1
	for !self.arithAtEnd() && depth > 0 {
		ch = self.arithPeek(0)
		if ch == "{" {
			depth++
			opChars = append(opChars, self.arithAdvance())
		} else if ch == "}" {
			depth--
			if depth == 0 {
				break
			}
			opChars = append(opChars, self.arithAdvance())
		} else {
			opChars = append(opChars, self.arithAdvance())
		}
	}
	self.arithConsume("}")
	opStr := strings.Join(opChars, "")
	if strings.HasPrefix(opStr, ":-") {
		return &ParamExpansion{Param: name, Op: ":-", Arg: substring(opStr, 2, _runeLen(opStr)), Kind: "param"}
	}
	if strings.HasPrefix(opStr, ":=") {
		return &ParamExpansion{Param: name, Op: ":=", Arg: substring(opStr, 2, _runeLen(opStr)), Kind: "param"}
	}
	if strings.HasPrefix(opStr, ":+") {
		return &ParamExpansion{Param: name, Op: ":+", Arg: substring(opStr, 2, _runeLen(opStr)), Kind: "param"}
	}
	if strings.HasPrefix(opStr, ":?") {
		return &ParamExpansion{Param: name, Op: ":?", Arg: substring(opStr, 2, _runeLen(opStr)), Kind: "param"}
	}
	if strings.HasPrefix(opStr, ":") {
		return &ParamExpansion{Param: name, Op: ":", Arg: substring(opStr, 1, _runeLen(opStr)), Kind: "param"}
	}
	if strings.HasPrefix(opStr, "##") {
		return &ParamExpansion{Param: name, Op: "##", Arg: substring(opStr, 2, _runeLen(opStr)), Kind: "param"}
	}
	if strings.HasPrefix(opStr, "#") {
		return &ParamExpansion{Param: name, Op: "#", Arg: substring(opStr, 1, _runeLen(opStr)), Kind: "param"}
	}
	if strings.HasPrefix(opStr, "%%") {
		return &ParamExpansion{Param: name, Op: "%%", Arg: substring(opStr, 2, _runeLen(opStr)), Kind: "param"}
	}
	if strings.HasPrefix(opStr, "%") {
		return &ParamExpansion{Param: name, Op: "%", Arg: substring(opStr, 1, _runeLen(opStr)), Kind: "param"}
	}
	if strings.HasPrefix(opStr, "//") {
		return &ParamExpansion{Param: name, Op: "//", Arg: substring(opStr, 2, _runeLen(opStr)), Kind: "param"}
	}
	if strings.HasPrefix(opStr, "/") {
		return &ParamExpansion{Param: name, Op: "/", Arg: substring(opStr, 1, _runeLen(opStr)), Kind: "param"}
	}
	return &ParamExpansion{Param: name, Op: "", Arg: opStr, Kind: "param"}
}

func (self *Parser) arithParseSingleQuote() Node {
	self.arithAdvance()
	contentStart := self.arithPos
	for !self.arithAtEnd() && self.arithPeek(0) != "'" {
		self.arithAdvance()
	}
	content := substring(self.arithSrc, contentStart, self.arithPos)
	if !self.arithConsume("'") {
		panic(NewParseError("Unterminated single quote in arithmetic", self.arithPos, 0))
	}
	return &ArithNumber{Value: content, Kind: "number"}
}

func (self *Parser) arithParseDoubleQuote() Node {
	self.arithAdvance()
	contentStart := self.arithPos
	for !self.arithAtEnd() && self.arithPeek(0) != "\"" {
		c := self.arithPeek(0)
		if c == "\\" && !self.arithAtEnd() {
			self.arithAdvance()
			self.arithAdvance()
		} else {
			self.arithAdvance()
		}
	}
	content := substring(self.arithSrc, contentStart, self.arithPos)
	if !self.arithConsume("\"") {
		panic(NewParseError("Unterminated double quote in arithmetic", self.arithPos, 0))
	}
	return &ArithNumber{Value: content, Kind: "number"}
}

func (self *Parser) arithParseBacktick() Node {
	self.arithAdvance()
	contentStart := self.arithPos
	for !self.arithAtEnd() && self.arithPeek(0) != "`" {
		c := self.arithPeek(0)
		if c == "\\" && !self.arithAtEnd() {
			self.arithAdvance()
			self.arithAdvance()
		} else {
			self.arithAdvance()
		}
	}
	content := substring(self.arithSrc, contentStart, self.arithPos)
	if !self.arithConsume("`") {
		panic(NewParseError("Unterminated backtick in arithmetic", self.arithPos, 0))
	}
	subParser := NewParser(content, false, self.extglob)
	cmd := subParser.ParseList(true)
	return &CommandSubstitution{Command: cmd, Kind: "cmdsub"}
}

func (self *Parser) arithParseNumberOrVar() Node {
	self.arithSkipWs()
	chars := []string{}
	c := self.arithPeek(0)
	var ch string
	if _strIsDigit(c) {
		for !self.arithAtEnd() {
			ch = self.arithPeek(0)
			if _strIsAlnum(ch) || ch == "#" || ch == "_" {
				chars = append(chars, self.arithAdvance())
			} else {
				break
			}
		}
		prefix := strings.Join(chars, "")
		if !self.arithAtEnd() && self.arithPeek(0) == "$" {
			expansion := self.arithParseExpansion()
			return &ArithConcat{Parts: []Node{&ArithNumber{Value: prefix, Kind: "number"}, expansion}, Kind: "arith-concat"}
		}
		return &ArithNumber{Value: prefix, Kind: "number"}
	}
	if _strIsAlpha(c) || c == "_" {
		for !self.arithAtEnd() {
			ch = self.arithPeek(0)
			if _strIsAlnum(ch) || ch == "_" {
				chars = append(chars, self.arithAdvance())
			} else {
				break
			}
		}
		return &ArithVar{Name: strings.Join(chars, ""), Kind: "var"}
	}
	panic(NewParseError("Unexpected character '"+c+"' in arithmetic expression", self.arithPos, 0))
}

func (self *Parser) parseDeprecatedArithmetic() (Node, string) {
	if self.AtEnd() || self.Peek() != "$" {
		return nil, ""
	}
	start := self.Pos
	if self.Pos+1 >= self.Length || string(_runeAt(self.Source, self.Pos+1)) != "[" {
		return nil, ""
	}
	self.Advance()
	self.Advance()
	self.lexer.Pos = self.Pos
	content := self.lexer.parseMatchedPair("[", "]", MatchedPairFlagsARITH, false)
	self.Pos = self.lexer.Pos
	text := substring(self.Source, start, self.Pos)
	return &ArithDeprecated{Expression: content, Kind: "arith-deprecated"}, text
}

func (self *Parser) parseParamExpansion(inDquote bool) (Node, string) {
	self.syncLexer()
	result0, result1 := self.lexer.readParamExpansion(inDquote)
	self.syncParser()
	return result0, result1
}

func (self *Parser) ParseRedirect() Node {
	self.SkipWhitespace()
	if self.AtEnd() {
		return nil
	}
	start := self.Pos
	fd := -1
	varfd := ""
	var ch string
	if self.Peek() == "{" {
		saved := self.Pos
		self.Advance()
		varnameChars := []string{}
		inBracket := false
		for !self.AtEnd() && !isRedirectChar(self.Peek()) {
			ch = self.Peek()
			if ch == "}" && !inBracket {
				break
			} else if ch == "[" {
				inBracket = true
				varnameChars = append(varnameChars, self.Advance())
			} else if ch == "]" {
				inBracket = false
				varnameChars = append(varnameChars, self.Advance())
			} else if _strIsAlnum(ch) || ch == "_" {
				varnameChars = append(varnameChars, self.Advance())
			} else if inBracket && !isMetachar(ch) {
				varnameChars = append(varnameChars, self.Advance())
			} else {
				break
			}
		}
		varname := strings.Join(varnameChars, "")
		isValidVarfd := false
		if varname != "" {
			if _strIsAlpha(string(_runeAt(varname, 0))) || string(_runeAt(varname, 0)) == "_" {
				if strings.Contains(varname, "[") || strings.Contains(varname, "]") {
					left := strings.Index(varname, "[")
					right := strings.LastIndex(varname, "]")
					if left != -1 && right == _runeLen(varname)-1 && right > left+1 {
						base := _Substring(varname, 0, left)
						if base != "" && (_strIsAlpha(string(_runeAt(base, 0))) || string(_runeAt(base, 0)) == "_") {
							isValidVarfd = true
							for _, c := range _Substring(base, 1, _runeLen(base)) {
								if !(_strIsAlnum(string(c)) || c == '_') {
									isValidVarfd = false
									break
								}
							}
						}
					}
				} else {
					isValidVarfd = true
					for _, c := range _Substring(varname, 1, _runeLen(varname)) {
						if !(_strIsAlnum(string(c)) || c == '_') {
							isValidVarfd = false
							break
						}
					}
				}
			}
		}
		if !self.AtEnd() && self.Peek() == "}" && isValidVarfd {
			self.Advance()
			varfd = varname
		} else {
			self.Pos = saved
		}
	}
	var fdChars []string
	if varfd == "" && self.Peek() != "" && _strIsDigit(self.Peek()) {
		fdChars = []string{}
		for !self.AtEnd() && _strIsDigit(self.Peek()) {
			fdChars = append(fdChars, self.Advance())
		}
		fd = _parseInt(strings.Join(fdChars, ""), 10)
	}
	ch = self.Peek()
	var op string
	var target *Word
	if ch == "&" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == ">" {
		if fd != -1 || varfd != "" {
			self.Pos = start
			return nil
		}
		self.Advance()
		self.Advance()
		if !self.AtEnd() && self.Peek() == ">" {
			self.Advance()
			op = "&>>"
		} else {
			op = "&>"
		}
		self.SkipWhitespace()
		target = self.ParseWord(false, false, false)
		if target == nil {
			panic(NewParseError("Expected target for redirect "+op, self.Pos, 0))
		}
		return &Redirect{Op: op, Target: target, Kind: "redirect"}
	}
	if ch == "" || !isRedirectChar(ch) {
		self.Pos = start
		return nil
	}
	if fd == -1 && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "(" {
		self.Pos = start
		return nil
	}
	op = self.Advance()
	stripTabs := false
	if !self.AtEnd() {
		nextCh := self.Peek()
		if op == ">" && nextCh == ">" {
			self.Advance()
			op = ">>"
		} else if op == "<" && nextCh == "<" {
			self.Advance()
			if !self.AtEnd() && self.Peek() == "<" {
				self.Advance()
				op = "<<<"
			} else if !self.AtEnd() && self.Peek() == "-" {
				self.Advance()
				op = "<<"
				stripTabs = true
			} else {
				op = "<<"
			}
		} else if op == "<" && nextCh == ">" {
			self.Advance()
			op = "<>"
		} else if op == ">" && nextCh == "|" {
			self.Advance()
			op = ">|"
		} else if fd == -1 && varfd == "" && op == ">" && nextCh == "&" {
			if self.Pos+1 >= self.Length || !isDigitOrDash(string(_runeAt(self.Source, self.Pos+1))) {
				self.Advance()
				op = ">&"
			}
		} else if fd == -1 && varfd == "" && op == "<" && nextCh == "&" {
			if self.Pos+1 >= self.Length || !isDigitOrDash(string(_runeAt(self.Source, self.Pos+1))) {
				self.Advance()
				op = "<&"
			}
		}
	}
	if op == "<<" {
		return self.parseHeredoc(_intPtr(fd), stripTabs)
	}
	if varfd != "" {
		op = "{" + varfd + "}" + op
	} else if fd != -1 {
		op = _intToStr(fd) + op
	}
	if !self.AtEnd() && self.Peek() == "&" {
		self.Advance()
		self.SkipWhitespace()
		if !self.AtEnd() && self.Peek() == "-" {
			if self.Pos+1 < self.Length && !isMetachar(string(_runeAt(self.Source, self.Pos+1))) {
				self.Advance()
				target = &Word{Value: "&-", Kind: "word"}
			} else {
				target = nil
			}
		} else {
			target = nil
		}
		if target == nil {
			var innerWord *Word
			if !self.AtEnd() && (_strIsDigit(self.Peek()) || self.Peek() == "-") {
				wordStart := self.Pos
				fdChars = []string{}
				for !self.AtEnd() && _strIsDigit(self.Peek()) {
					fdChars = append(fdChars, self.Advance())
				}
				var fdTarget string
				if len(fdChars) > 0 {
					fdTarget = strings.Join(fdChars, "")
				} else {
					fdTarget = ""
				}
				if !self.AtEnd() && self.Peek() == "-" {
					fdTarget += self.Advance()
				}
				if fdTarget != "-" && !self.AtEnd() && !isMetachar(self.Peek()) {
					self.Pos = wordStart
					innerWord = self.ParseWord(false, false, false)
					if innerWord != nil {
						target = &Word{Value: "&" + innerWord.Value, Kind: "word"}
						target.Parts = innerWord.Parts
					} else {
						panic(NewParseError("Expected target for redirect "+op, self.Pos, 0))
					}
				} else {
					target = &Word{Value: "&" + fdTarget, Kind: "word"}
				}
			} else {
				innerWord = self.ParseWord(false, false, false)
				if innerWord != nil {
					target = &Word{Value: "&" + innerWord.Value, Kind: "word"}
					target.Parts = innerWord.Parts
				} else {
					panic(NewParseError("Expected target for redirect "+op, self.Pos, 0))
				}
			}
		}
	} else {
		self.SkipWhitespace()
		if (op == ">&" || op == "<&") && !self.AtEnd() && self.Peek() == "-" {
			if self.Pos+1 < self.Length && !isMetachar(string(_runeAt(self.Source, self.Pos+1))) {
				self.Advance()
				target = &Word{Value: "&-", Kind: "word"}
			} else {
				target = self.ParseWord(false, false, false)
			}
		} else {
			target = self.ParseWord(false, false, false)
		}
	}
	if target == nil {
		panic(NewParseError("Expected target for redirect "+op, self.Pos, 0))
	}
	return &Redirect{Op: op, Target: target, Kind: "redirect"}
}

func (self *Parser) parseHeredocDelimiter() (string, bool) {
	self.SkipWhitespace()
	quoted := false
	delimiterChars := []string{}
	for true {
		var c string
		var depth int
		for !self.AtEnd() && !isMetachar(self.Peek()) {
			ch := self.Peek()
			if ch == "\"" {
				quoted = true
				self.Advance()
				for !self.AtEnd() && self.Peek() != "\"" {
					delimiterChars = append(delimiterChars, self.Advance())
				}
				if !self.AtEnd() {
					self.Advance()
				}
			} else if ch == "'" {
				quoted = true
				self.Advance()
				for !self.AtEnd() && self.Peek() != "'" {
					c = self.Advance()
					if c == "\n" {
						self.sawNewlineInSingleQuote = true
					}
					delimiterChars = append(delimiterChars, c)
				}
				if !self.AtEnd() {
					self.Advance()
				}
			} else if ch == "\\" {
				self.Advance()
				if !self.AtEnd() {
					nextCh := self.Peek()
					if nextCh == "\n" {
						self.Advance()
					} else {
						quoted = true
						delimiterChars = append(delimiterChars, self.Advance())
					}
				}
			} else if ch == "$" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "'" {
				quoted = true
				self.Advance()
				self.Advance()
				for !self.AtEnd() && self.Peek() != "'" {
					c = self.Peek()
					if c == "\\" && self.Pos+1 < self.Length {
						self.Advance()
						esc := self.Peek()
						escVal := getAnsiEscape(esc)
						if escVal >= 0 {
							delimiterChars = append(delimiterChars, string(rune(escVal)))
							self.Advance()
						} else if esc == "'" {
							delimiterChars = append(delimiterChars, self.Advance())
						} else {
							delimiterChars = append(delimiterChars, self.Advance())
						}
					} else {
						delimiterChars = append(delimiterChars, self.Advance())
					}
				}
				if !self.AtEnd() {
					self.Advance()
				}
			} else if isExpansionStart(self.Source, self.Pos, "$(") {
				delimiterChars = append(delimiterChars, self.Advance())
				delimiterChars = append(delimiterChars, self.Advance())
				depth = 1
				for !self.AtEnd() && depth > 0 {
					c = self.Peek()
					if c == "(" {
						depth++
					} else if c == ")" {
						depth--
					}
					delimiterChars = append(delimiterChars, self.Advance())
				}
			} else if ch == "$" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "{" {
				dollarCount := 0
				j := self.Pos - 1
				for j >= 0 && string(_runeAt(self.Source, j)) == "$" {
					dollarCount++
					j--
				}
				if j >= 0 && string(_runeAt(self.Source, j)) == "\\" {
					dollarCount--
				}
				if (dollarCount % 2) == 1 {
					delimiterChars = append(delimiterChars, self.Advance())
				} else {
					delimiterChars = append(delimiterChars, self.Advance())
					delimiterChars = append(delimiterChars, self.Advance())
					depth = 0
					for !self.AtEnd() {
						c = self.Peek()
						if c == "{" {
							depth++
						} else if c == "}" {
							delimiterChars = append(delimiterChars, self.Advance())
							if depth == 0 {
								break
							}
							depth--
							if depth == 0 && !self.AtEnd() && isMetachar(self.Peek()) {
								break
							}
							continue
						}
						delimiterChars = append(delimiterChars, self.Advance())
					}
				}
			} else if ch == "$" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "[" {
				dollarCount := 0
				j := self.Pos - 1
				for j >= 0 && string(_runeAt(self.Source, j)) == "$" {
					dollarCount++
					j--
				}
				if j >= 0 && string(_runeAt(self.Source, j)) == "\\" {
					dollarCount--
				}
				if (dollarCount % 2) == 1 {
					delimiterChars = append(delimiterChars, self.Advance())
				} else {
					delimiterChars = append(delimiterChars, self.Advance())
					delimiterChars = append(delimiterChars, self.Advance())
					depth = 1
					for !self.AtEnd() && depth > 0 {
						c = self.Peek()
						if c == "[" {
							depth++
						} else if c == "]" {
							depth--
						}
						delimiterChars = append(delimiterChars, self.Advance())
					}
				}
			} else if ch == "`" {
				delimiterChars = append(delimiterChars, self.Advance())
				for !self.AtEnd() && self.Peek() != "`" {
					c = self.Peek()
					if c == "'" {
						delimiterChars = append(delimiterChars, self.Advance())
						for !self.AtEnd() && self.Peek() != "'" && self.Peek() != "`" {
							delimiterChars = append(delimiterChars, self.Advance())
						}
						if !self.AtEnd() && self.Peek() == "'" {
							delimiterChars = append(delimiterChars, self.Advance())
						}
					} else if c == "\"" {
						delimiterChars = append(delimiterChars, self.Advance())
						for !self.AtEnd() && self.Peek() != "\"" && self.Peek() != "`" {
							if self.Peek() == "\\" && self.Pos+1 < self.Length {
								delimiterChars = append(delimiterChars, self.Advance())
							}
							delimiterChars = append(delimiterChars, self.Advance())
						}
						if !self.AtEnd() && self.Peek() == "\"" {
							delimiterChars = append(delimiterChars, self.Advance())
						}
					} else if c == "\\" && self.Pos+1 < self.Length {
						delimiterChars = append(delimiterChars, self.Advance())
						delimiterChars = append(delimiterChars, self.Advance())
					} else {
						delimiterChars = append(delimiterChars, self.Advance())
					}
				}
				if !self.AtEnd() {
					delimiterChars = append(delimiterChars, self.Advance())
				}
			} else {
				delimiterChars = append(delimiterChars, self.Advance())
			}
		}
		if !self.AtEnd() && strings.Contains("<>", self.Peek()) && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "(" {
			delimiterChars = append(delimiterChars, self.Advance())
			delimiterChars = append(delimiterChars, self.Advance())
			depth = 1
			for !self.AtEnd() && depth > 0 {
				c = self.Peek()
				if c == "(" {
					depth++
				} else if c == ")" {
					depth--
				}
				delimiterChars = append(delimiterChars, self.Advance())
			}
			continue
		}
		break
	}
	return strings.Join(delimiterChars, ""), quoted
}

func (self *Parser) readHeredocLine(quoted bool) (string, int) {
	lineStart := self.Pos
	lineEnd := self.Pos
	for lineEnd < self.Length && string(_runeAt(self.Source, lineEnd)) != "\n" {
		lineEnd++
	}
	line := substring(self.Source, lineStart, lineEnd)
	if !quoted {
		for lineEnd < self.Length {
			trailingBs := countTrailingBackslashes(line)
			if (trailingBs % 2) == 0 {
				break
			}
			line = substring(line, 0, _runeLen(line)-1)
			lineEnd++
			nextLineStart := lineEnd
			for lineEnd < self.Length && string(_runeAt(self.Source, lineEnd)) != "\n" {
				lineEnd++
			}
			line = line + substring(self.Source, nextLineStart, lineEnd)
		}
	}
	return line, lineEnd
}

func (self *Parser) lineMatchesDelimiter(line string, delimiter string, stripTabs bool) (bool, string) {
	checkLine := func() string {
		if stripTabs {
			return strings.TrimLeft(line, "\t")
		} else {
			return line
		}
	}()
	normalizedCheck := normalizeHeredocDelimiter(checkLine)
	normalizedDelim := normalizeHeredocDelimiter(delimiter)
	return normalizedCheck == normalizedDelim, checkLine
}

func (self *Parser) gatherHeredocBodies() {
	for _, heredoc := range self.pendingHeredocs {
		contentLines := []string{}
		lineStart := self.Pos
		for self.Pos < self.Length {
			lineStart = self.Pos
			line, lineEnd := self.readHeredocLine(heredoc.Quoted)
			matches, checkLine := self.lineMatchesDelimiter(line, heredoc.Delimiter, heredoc.StripTabs)
			if matches {
				self.Pos = func() int {
					if lineEnd < self.Length {
						return lineEnd + 1
					} else {
						return lineEnd
					}
				}()
				break
			}
			normalizedCheck := normalizeHeredocDelimiter(checkLine)
			normalizedDelim := normalizeHeredocDelimiter(heredoc.Delimiter)
			var tabsStripped int
			if self.eofToken == ")" && strings.HasPrefix(normalizedCheck, normalizedDelim) {
				tabsStripped = _runeLen(line) - _runeLen(checkLine)
				self.Pos = lineStart + tabsStripped + _runeLen(heredoc.Delimiter)
				break
			}
			if lineEnd >= self.Length && strings.HasPrefix(normalizedCheck, normalizedDelim) && self.inProcessSub {
				tabsStripped = _runeLen(line) - _runeLen(checkLine)
				self.Pos = lineStart + tabsStripped + _runeLen(heredoc.Delimiter)
				break
			}
			if heredoc.StripTabs {
				line = strings.TrimLeft(line, "\t")
			}
			if lineEnd < self.Length {
				contentLines = append(contentLines, line+"\n")
				self.Pos = lineEnd + 1
			} else {
				addNewline := true
				if !heredoc.Quoted && (countTrailingBackslashes(line)%2) == 1 {
					addNewline = false
				}
				contentLines = append(contentLines, line+func() string {
					if addNewline {
						return "\n"
					} else {
						return ""
					}
				}())
				self.Pos = self.Length
			}
		}
		heredoc.Content = strings.Join(contentLines, "")
	}
	self.pendingHeredocs = []*HereDoc{}
}

func (self *Parser) parseHeredoc(fd *int, stripTabs bool) *HereDoc {
	startPos := self.Pos
	self.setState(ParserStateFlagsPSTHEREDOC)
	delimiter, quoted := self.parseHeredocDelimiter()
	for _, existing := range self.pendingHeredocs {
		if existing.startPos == startPos && existing.Delimiter == delimiter {
			self.clearState(ParserStateFlagsPSTHEREDOC)
			return existing
		}
	}
	heredoc := &HereDoc{Delimiter: delimiter, Content: "", StripTabs: stripTabs, Quoted: quoted, Fd: fd, Complete: false, Kind: "heredoc"}
	heredoc.startPos = startPos
	self.pendingHeredocs = append(self.pendingHeredocs, heredoc)
	self.clearState(ParserStateFlagsPSTHEREDOC)
	return heredoc
}

func (self *Parser) ParseCommand() *Command {
	words := []*Word{}
	redirects := []Node{}
	for true {
		self.SkipWhitespace()
		if self.lexIsCommandTerminator() {
			break
		}
		if len(words) == 0 {
			reserved := self.lexPeekReservedWord()
			if reserved == "}" || reserved == "]]" {
				break
			}
		}
		redirect := self.ParseRedirect()
		if redirect != nil {
			redirects = append(redirects, redirect)
			continue
		}
		allAssignments := true
		for _, w := range words {
			if !self.isAssignmentWord(w) {
				allAssignments = false
				break
			}
		}
		inAssignBuiltin := len(words) > 0 && func() bool { _, ok := ASSIGNMENTBUILTINS[words[0].Value]; return ok }()
		word := self.ParseWord(!(len(words) > 0) || allAssignments && len(redirects) == 0, false, inAssignBuiltin)
		if word == nil {
			break
		}
		words = append(words, word)
	}
	if !(len(words) > 0) && !(len(redirects) > 0) {
		return nil
	}
	return &Command{Words: words, Redirects: redirects, Kind: "command"}
}

func (self *Parser) ParseSubshell() *Subshell {
	self.SkipWhitespace()
	if self.AtEnd() || self.Peek() != "(" {
		return nil
	}
	self.Advance()
	self.setState(ParserStateFlagsPSTSUBSHELL)
	body := self.ParseList(true)
	if _isNilInterface(body) {
		self.clearState(ParserStateFlagsPSTSUBSHELL)
		panic(NewParseError("Expected command in subshell", self.Pos, 0))
	}
	self.SkipWhitespace()
	if self.AtEnd() || self.Peek() != ")" {
		self.clearState(ParserStateFlagsPSTSUBSHELL)
		panic(NewParseError("Expected ) to close subshell", self.Pos, 0))
	}
	self.Advance()
	self.clearState(ParserStateFlagsPSTSUBSHELL)
	return &Subshell{Body: body, Redirects: self.collectRedirects(), Kind: "subshell"}
}

func (self *Parser) ParseArithmeticCommand() *ArithmeticCommand {
	self.SkipWhitespace()
	if self.AtEnd() || self.Peek() != "(" || self.Pos+1 >= self.Length || string(_runeAt(self.Source, self.Pos+1)) != "(" {
		return nil
	}
	savedPos := self.Pos
	self.Advance()
	self.Advance()
	contentStart := self.Pos
	depth := 1
	for !self.AtEnd() && depth > 0 {
		c := self.Peek()
		if c == "'" {
			self.Advance()
			for !self.AtEnd() && self.Peek() != "'" {
				self.Advance()
			}
			if !self.AtEnd() {
				self.Advance()
			}
		} else if c == "\"" {
			self.Advance()
			for !self.AtEnd() {
				if self.Peek() == "\\" && self.Pos+1 < self.Length {
					self.Advance()
					self.Advance()
				} else if self.Peek() == "\"" {
					self.Advance()
					break
				} else {
					self.Advance()
				}
			}
		} else if c == "\\" && self.Pos+1 < self.Length {
			self.Advance()
			self.Advance()
		} else if c == "(" {
			depth++
			self.Advance()
		} else if c == ")" {
			if depth == 1 && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == ")" {
				break
			}
			depth--
			if depth == 0 {
				self.Pos = savedPos
				return nil
			}
			self.Advance()
		} else {
			self.Advance()
		}
	}
	if self.AtEnd() {
		panic(NewMatchedPairError("unexpected EOF looking for `))'", savedPos, 0))
	}
	if depth != 1 {
		self.Pos = savedPos
		return nil
	}
	content := substring(self.Source, contentStart, self.Pos)
	content = strings.ReplaceAll(content, "\\\n", "")
	self.Advance()
	self.Advance()
	expr := self.parseArithExpr(content)
	return &ArithmeticCommand{Expression: expr, Redirects: self.collectRedirects(), RawContent: content, Kind: "arith-cmd"}
}

func (self *Parser) ParseConditionalExpr() *ConditionalExpr {
	self.SkipWhitespace()
	if self.AtEnd() || self.Peek() != "[" || self.Pos+1 >= self.Length || string(_runeAt(self.Source, self.Pos+1)) != "[" {
		return nil
	}
	nextPos := self.Pos + 2
	if nextPos < self.Length && !(isWhitespace(string(_runeAt(self.Source, nextPos))) || string(_runeAt(self.Source, nextPos)) == "\\" && nextPos+1 < self.Length && string(_runeAt(self.Source, nextPos+1)) == "\n") {
		return nil
	}
	self.Advance()
	self.Advance()
	self.setState(ParserStateFlagsPSTCONDEXPR)
	self.wordContext = WORDCTXCOND
	body := self.parseCondOr()
	for !self.AtEnd() && isWhitespaceNoNewline(self.Peek()) {
		self.Advance()
	}
	if self.AtEnd() || self.Peek() != "]" || self.Pos+1 >= self.Length || string(_runeAt(self.Source, self.Pos+1)) != "]" {
		self.clearState(ParserStateFlagsPSTCONDEXPR)
		self.wordContext = WORDCTXNORMAL
		panic(NewParseError("Expected ]] to close conditional expression", self.Pos, 0))
	}
	self.Advance()
	self.Advance()
	self.clearState(ParserStateFlagsPSTCONDEXPR)
	self.wordContext = WORDCTXNORMAL
	return &ConditionalExpr{Body: body, Redirects: self.collectRedirects(), Kind: "cond-expr"}
}

func (self *Parser) condSkipWhitespace() {
	for !self.AtEnd() {
		if isWhitespaceNoNewline(self.Peek()) {
			self.Advance()
		} else if self.Peek() == "\\" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "\n" {
			self.Advance()
			self.Advance()
		} else if self.Peek() == "\n" {
			self.Advance()
		} else {
			break
		}
	}
}

func (self *Parser) condAtEnd() bool {
	return self.AtEnd() || self.Peek() == "]" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "]"
}

func (self *Parser) parseCondOr() Node {
	self.condSkipWhitespace()
	left := self.parseCondAnd()
	self.condSkipWhitespace()
	if !self.condAtEnd() && self.Peek() == "|" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "|" {
		self.Advance()
		self.Advance()
		right := self.parseCondOr()
		return &CondOr{Left: left, Right: right, Kind: "cond-or"}
	}
	return left
}

func (self *Parser) parseCondAnd() Node {
	self.condSkipWhitespace()
	left := self.parseCondTerm()
	self.condSkipWhitespace()
	if !self.condAtEnd() && self.Peek() == "&" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "&" {
		self.Advance()
		self.Advance()
		right := self.parseCondAnd()
		return &CondAnd{Left: left, Right: right, Kind: "cond-and"}
	}
	return left
}

func (self *Parser) parseCondTerm() Node {
	self.condSkipWhitespace()
	if self.condAtEnd() {
		panic(NewParseError("Unexpected end of conditional expression", self.Pos, 0))
	}
	var operand Node
	if self.Peek() == "!" {
		if self.Pos+1 < self.Length && !isWhitespaceNoNewline(string(_runeAt(self.Source, self.Pos+1))) {
		} else {
			self.Advance()
			operand = self.parseCondTerm()
			return &CondNot{Operand: operand, Kind: "cond-not"}
		}
	}
	if self.Peek() == "(" {
		self.Advance()
		inner := self.parseCondOr()
		self.condSkipWhitespace()
		if self.AtEnd() || self.Peek() != ")" {
			panic(NewParseError("Expected ) in conditional expression", self.Pos, 0))
		}
		self.Advance()
		return &CondParen{Inner: inner, Kind: "cond-paren"}
	}
	word1 := self.parseCondWord()
	if word1 == nil {
		panic(NewParseError("Expected word in conditional expression", self.Pos, 0))
	}
	self.condSkipWhitespace()
	if func() bool { _, ok := CONDUNARYOPS[word1.Value]; return ok }() {
		operand = self.parseCondWord()
		if _isNilInterface(operand) {
			panic(NewParseError("Expected operand after "+word1.Value, self.Pos, 0))
		}
		return &UnaryTest{Op: word1.Value, Operand: operand, Kind: "unary-test"}
	}
	if !self.condAtEnd() && self.Peek() != "&" && self.Peek() != "|" && self.Peek() != ")" {
		var word2 *Word
		if isRedirectChar(self.Peek()) && !(self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "(") {
			op := self.Advance()
			self.condSkipWhitespace()
			word2 = self.parseCondWord()
			if word2 == nil {
				panic(NewParseError("Expected operand after "+op, self.Pos, 0))
			}
			return &BinaryTest{Op: op, Left: word1, Right: word2, Kind: "binary-test"}
		}
		savedPos := self.Pos
		opWord := self.parseCondWord()
		if opWord != nil && func() bool { _, ok := CONDBINARYOPS[opWord.Value]; return ok }() {
			self.condSkipWhitespace()
			if opWord.Value == "=~" {
				word2 = self.parseCondRegexWord()
			} else {
				word2 = self.parseCondWord()
			}
			if word2 == nil {
				panic(NewParseError("Expected operand after "+opWord.Value, self.Pos, 0))
			}
			return &BinaryTest{Op: opWord.Value, Left: word1, Right: word2, Kind: "binary-test"}
		} else {
			self.Pos = savedPos
		}
	}
	return &UnaryTest{Op: "-n", Operand: word1, Kind: "unary-test"}
}

func (self *Parser) parseCondWord() *Word {
	self.condSkipWhitespace()
	if self.condAtEnd() {
		return nil
	}
	c := self.Peek()
	if isParen(c) {
		return nil
	}
	if c == "&" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "&" {
		return nil
	}
	if c == "|" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "|" {
		return nil
	}
	return self.parseWordInternal(WORDCTXCOND, false, false)
}

func (self *Parser) parseCondRegexWord() *Word {
	self.condSkipWhitespace()
	if self.condAtEnd() {
		return nil
	}
	self.setState(ParserStateFlagsPSTREGEXP)
	result := self.parseWordInternal(WORDCTXREGEX, false, false)
	self.clearState(ParserStateFlagsPSTREGEXP)
	self.wordContext = WORDCTXCOND
	return result
}

func (self *Parser) ParseBraceGroup() *BraceGroup {
	self.SkipWhitespace()
	if !self.lexConsumeWord("{") {
		return nil
	}
	self.SkipWhitespaceAndNewlines()
	body := self.ParseList(true)
	if _isNilInterface(body) {
		panic(NewParseError("Expected command in brace group", self.lexPeekToken().Pos, 0))
	}
	self.SkipWhitespace()
	if !self.lexConsumeWord("}") {
		panic(NewParseError("Expected } to close brace group", self.lexPeekToken().Pos, 0))
	}
	return &BraceGroup{Body: body, Redirects: self.collectRedirects(), Kind: "brace-group"}
}

func (self *Parser) ParseIf() *If {
	self.SkipWhitespace()
	if !self.lexConsumeWord("if") {
		return nil
	}
	condition := self.ParseListUntil(map[string]struct{}{"then": {}})
	if _isNilInterface(condition) {
		panic(NewParseError("Expected condition after 'if'", self.lexPeekToken().Pos, 0))
	}
	self.SkipWhitespaceAndNewlines()
	if !self.lexConsumeWord("then") {
		panic(NewParseError("Expected 'then' after if condition", self.lexPeekToken().Pos, 0))
	}
	thenBody := self.ParseListUntil(map[string]struct{}{"elif": {}, "else": {}, "fi": {}})
	if _isNilInterface(thenBody) {
		panic(NewParseError("Expected commands after 'then'", self.lexPeekToken().Pos, 0))
	}
	self.SkipWhitespaceAndNewlines()
	var elseBody Node
	if self.lexIsAtReservedWord("elif") {
		self.lexConsumeWord("elif")
		elifCondition := self.ParseListUntil(map[string]struct{}{"then": {}})
		if _isNilInterface(elifCondition) {
			panic(NewParseError("Expected condition after 'elif'", self.lexPeekToken().Pos, 0))
		}
		self.SkipWhitespaceAndNewlines()
		if !self.lexConsumeWord("then") {
			panic(NewParseError("Expected 'then' after elif condition", self.lexPeekToken().Pos, 0))
		}
		elifThenBody := self.ParseListUntil(map[string]struct{}{"elif": {}, "else": {}, "fi": {}})
		if _isNilInterface(elifThenBody) {
			panic(NewParseError("Expected commands after 'then'", self.lexPeekToken().Pos, 0))
		}
		self.SkipWhitespaceAndNewlines()
		var innerElse Node
		if self.lexIsAtReservedWord("elif") {
			innerElse = self.parseElifChain()
		} else if self.lexIsAtReservedWord("else") {
			self.lexConsumeWord("else")
			innerElse = self.ParseListUntil(map[string]struct{}{"fi": {}})
			if _isNilInterface(innerElse) {
				panic(NewParseError("Expected commands after 'else'", self.lexPeekToken().Pos, 0))
			}
		}
		elseBody = &If{Condition: elifCondition, ThenBody: elifThenBody, ElseBody: innerElse, Kind: "if"}
	} else if self.lexIsAtReservedWord("else") {
		self.lexConsumeWord("else")
		elseBody = self.ParseListUntil(map[string]struct{}{"fi": {}})
		if _isNilInterface(elseBody) {
			panic(NewParseError("Expected commands after 'else'", self.lexPeekToken().Pos, 0))
		}
	}
	self.SkipWhitespaceAndNewlines()
	if !self.lexConsumeWord("fi") {
		panic(NewParseError("Expected 'fi' to close if statement", self.lexPeekToken().Pos, 0))
	}
	return &If{Condition: condition, ThenBody: thenBody, ElseBody: elseBody, Redirects: self.collectRedirects(), Kind: "if"}
}

func (self *Parser) parseElifChain() *If {
	self.lexConsumeWord("elif")
	condition := self.ParseListUntil(map[string]struct{}{"then": {}})
	if _isNilInterface(condition) {
		panic(NewParseError("Expected condition after 'elif'", self.lexPeekToken().Pos, 0))
	}
	self.SkipWhitespaceAndNewlines()
	if !self.lexConsumeWord("then") {
		panic(NewParseError("Expected 'then' after elif condition", self.lexPeekToken().Pos, 0))
	}
	thenBody := self.ParseListUntil(map[string]struct{}{"elif": {}, "else": {}, "fi": {}})
	if _isNilInterface(thenBody) {
		panic(NewParseError("Expected commands after 'then'", self.lexPeekToken().Pos, 0))
	}
	self.SkipWhitespaceAndNewlines()
	var elseBody Node
	if self.lexIsAtReservedWord("elif") {
		elseBody = self.parseElifChain()
	} else if self.lexIsAtReservedWord("else") {
		self.lexConsumeWord("else")
		elseBody = self.ParseListUntil(map[string]struct{}{"fi": {}})
		if _isNilInterface(elseBody) {
			panic(NewParseError("Expected commands after 'else'", self.lexPeekToken().Pos, 0))
		}
	}
	return &If{Condition: condition, ThenBody: thenBody, ElseBody: elseBody, Kind: "if"}
}

func (self *Parser) ParseWhile() *While {
	self.SkipWhitespace()
	if !self.lexConsumeWord("while") {
		return nil
	}
	condition := self.ParseListUntil(map[string]struct{}{"do": {}})
	if _isNilInterface(condition) {
		panic(NewParseError("Expected condition after 'while'", self.lexPeekToken().Pos, 0))
	}
	self.SkipWhitespaceAndNewlines()
	if !self.lexConsumeWord("do") {
		panic(NewParseError("Expected 'do' after while condition", self.lexPeekToken().Pos, 0))
	}
	body := self.ParseListUntil(map[string]struct{}{"done": {}})
	if _isNilInterface(body) {
		panic(NewParseError("Expected commands after 'do'", self.lexPeekToken().Pos, 0))
	}
	self.SkipWhitespaceAndNewlines()
	if !self.lexConsumeWord("done") {
		panic(NewParseError("Expected 'done' to close while loop", self.lexPeekToken().Pos, 0))
	}
	return &While{Condition: condition, Body: body, Redirects: self.collectRedirects(), Kind: "while"}
}

func (self *Parser) ParseUntil() *Until {
	self.SkipWhitespace()
	if !self.lexConsumeWord("until") {
		return nil
	}
	condition := self.ParseListUntil(map[string]struct{}{"do": {}})
	if _isNilInterface(condition) {
		panic(NewParseError("Expected condition after 'until'", self.lexPeekToken().Pos, 0))
	}
	self.SkipWhitespaceAndNewlines()
	if !self.lexConsumeWord("do") {
		panic(NewParseError("Expected 'do' after until condition", self.lexPeekToken().Pos, 0))
	}
	body := self.ParseListUntil(map[string]struct{}{"done": {}})
	if _isNilInterface(body) {
		panic(NewParseError("Expected commands after 'do'", self.lexPeekToken().Pos, 0))
	}
	self.SkipWhitespaceAndNewlines()
	if !self.lexConsumeWord("done") {
		panic(NewParseError("Expected 'done' to close until loop", self.lexPeekToken().Pos, 0))
	}
	return &Until{Condition: condition, Body: body, Redirects: self.collectRedirects(), Kind: "until"}
}

func (self *Parser) ParseFor() Node {
	self.SkipWhitespace()
	if !self.lexConsumeWord("for") {
		return nil
	}
	self.SkipWhitespace()
	if self.Peek() == "(" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "(" {
		return self.parseForArith()
	}
	var varName string
	if self.Peek() == "$" {
		varWord := self.ParseWord(false, false, false)
		if varWord == nil {
			panic(NewParseError("Expected variable name after 'for'", self.lexPeekToken().Pos, 0))
		}
		varName = varWord.Value
	} else {
		varName = self.PeekWord()
		if varName == "" {
			panic(NewParseError("Expected variable name after 'for'", self.lexPeekToken().Pos, 0))
		}
		self.ConsumeWord(varName)
	}
	self.SkipWhitespace()
	if self.Peek() == ";" {
		self.Advance()
	}
	self.SkipWhitespaceAndNewlines()
	var words []*Word
	if self.lexIsAtReservedWord("in") {
		self.lexConsumeWord("in")
		self.SkipWhitespace()
		sawDelimiter := isSemicolonOrNewline(self.Peek())
		if self.Peek() == ";" {
			self.Advance()
		}
		self.SkipWhitespaceAndNewlines()
		words = []*Word{}
		for true {
			self.SkipWhitespace()
			if self.AtEnd() {
				break
			}
			if isSemicolonOrNewline(self.Peek()) {
				sawDelimiter = true
				if self.Peek() == ";" {
					self.Advance()
				}
				break
			}
			if self.lexIsAtReservedWord("do") {
				if sawDelimiter {
					break
				}
				panic(NewParseError("Expected ';' or newline before 'do'", self.lexPeekToken().Pos, 0))
			}
			word := self.ParseWord(false, false, false)
			if word == nil {
				break
			}
			words = append(words, word)
		}
	}
	self.SkipWhitespaceAndNewlines()
	if self.Peek() == "{" {
		braceGroup := self.ParseBraceGroup()
		if braceGroup == nil {
			panic(NewParseError("Expected brace group in for loop", self.lexPeekToken().Pos, 0))
		}
		return &For{Var: varName, Words: words, Body: braceGroup.Body, Redirects: self.collectRedirects(), Kind: "for"}
	}
	if !self.lexConsumeWord("do") {
		panic(NewParseError("Expected 'do' in for loop", self.lexPeekToken().Pos, 0))
	}
	body := self.ParseListUntil(map[string]struct{}{"done": {}})
	if _isNilInterface(body) {
		panic(NewParseError("Expected commands after 'do'", self.lexPeekToken().Pos, 0))
	}
	self.SkipWhitespaceAndNewlines()
	if !self.lexConsumeWord("done") {
		panic(NewParseError("Expected 'done' to close for loop", self.lexPeekToken().Pos, 0))
	}
	return &For{Var: varName, Words: words, Body: body, Redirects: self.collectRedirects(), Kind: "for"}
}

func (self *Parser) parseForArith() *ForArith {
	self.Advance()
	self.Advance()
	parts := []string{}
	current := []string{}
	parenDepth := 0
	for !self.AtEnd() {
		ch := self.Peek()
		if ch == "(" {
			parenDepth++
			current = append(current, self.Advance())
		} else if ch == ")" {
			if parenDepth > 0 {
				parenDepth--
				current = append(current, self.Advance())
			} else if self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == ")" {
				parts = append(parts, strings.TrimLeft(strings.Join(current, ""), " \t"))
				self.Advance()
				self.Advance()
				break
			} else {
				current = append(current, self.Advance())
			}
		} else if ch == ";" && parenDepth == 0 {
			parts = append(parts, strings.TrimLeft(strings.Join(current, ""), " \t"))
			current = []string{}
			self.Advance()
		} else {
			current = append(current, self.Advance())
		}
	}
	if len(parts) != 3 {
		panic(NewParseError("Expected three expressions in for ((;;))", self.Pos, 0))
	}
	init := parts[0]
	cond := parts[1]
	incr := parts[2]
	self.SkipWhitespace()
	if !self.AtEnd() && self.Peek() == ";" {
		self.Advance()
	}
	self.SkipWhitespaceAndNewlines()
	body := self.parseLoopBody("for loop")
	return &ForArith{Init: init, Cond: cond, Incr: incr, Body: body, Redirects: self.collectRedirects(), Kind: "for-arith"}
}

func (self *Parser) ParseSelect() *Select {
	self.SkipWhitespace()
	if !self.lexConsumeWord("select") {
		return nil
	}
	self.SkipWhitespace()
	varName := self.PeekWord()
	if varName == "" {
		panic(NewParseError("Expected variable name after 'select'", self.lexPeekToken().Pos, 0))
	}
	self.ConsumeWord(varName)
	self.SkipWhitespace()
	if self.Peek() == ";" {
		self.Advance()
	}
	self.SkipWhitespaceAndNewlines()
	var words []*Word
	if self.lexIsAtReservedWord("in") {
		self.lexConsumeWord("in")
		self.SkipWhitespaceAndNewlines()
		words = []*Word{}
		for true {
			self.SkipWhitespace()
			if self.AtEnd() {
				break
			}
			if isSemicolonNewlineBrace(self.Peek()) {
				if self.Peek() == ";" {
					self.Advance()
				}
				break
			}
			if self.lexIsAtReservedWord("do") {
				break
			}
			word := self.ParseWord(false, false, false)
			if word == nil {
				break
			}
			words = append(words, word)
		}
	}
	self.SkipWhitespaceAndNewlines()
	body := self.parseLoopBody("select")
	return &Select{Var: varName, Words: words, Body: body, Redirects: self.collectRedirects(), Kind: "select"}
}

func (self *Parser) consumeCaseTerminator() string {
	term := self.lexPeekCaseTerminator()
	if term != "" {
		self.lexNextToken()
		return term
	}
	return ";;"
}

func (self *Parser) ParseCase() *Case {
	if !self.ConsumeWord("case") {
		return nil
	}
	self.setState(ParserStateFlagsPSTCASESTMT)
	self.SkipWhitespace()
	word := self.ParseWord(false, false, false)
	if word == nil {
		panic(NewParseError("Expected word after 'case'", self.lexPeekToken().Pos, 0))
	}
	self.SkipWhitespaceAndNewlines()
	if !self.lexConsumeWord("in") {
		panic(NewParseError("Expected 'in' after case word", self.lexPeekToken().Pos, 0))
	}
	self.SkipWhitespaceAndNewlines()
	patterns := []Node{}
	self.setState(ParserStateFlagsPSTCASEPAT)
	for true {
		self.SkipWhitespaceAndNewlines()
		if self.lexIsAtReservedWord("esac") {
			saved := self.Pos
			self.SkipWhitespace()
			for !self.AtEnd() && !isMetachar(self.Peek()) && !isQuote(self.Peek()) {
				self.Advance()
			}
			self.SkipWhitespace()
			isPattern := false
			if !self.AtEnd() && self.Peek() == ")" {
				if self.eofToken == ")" {
					isPattern = false
				} else {
					self.Advance()
					self.SkipWhitespace()
					if !self.AtEnd() {
						nextCh := self.Peek()
						if nextCh == ";" {
							isPattern = true
						} else if !isNewlineOrRightParen(nextCh) {
							isPattern = true
						}
					}
				}
			}
			self.Pos = saved
			if !isPattern {
				break
			}
		}
		self.SkipWhitespaceAndNewlines()
		if !self.AtEnd() && self.Peek() == "(" {
			self.Advance()
			self.SkipWhitespaceAndNewlines()
		}
		patternChars := []string{}
		extglobDepth := 0
		for !self.AtEnd() {
			ch := self.Peek()
			if ch == ")" {
				if extglobDepth > 0 {
					patternChars = append(patternChars, self.Advance())
					extglobDepth--
				} else {
					self.Advance()
					break
				}
			} else if ch == "\\" {
				if self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "\n" {
					self.Advance()
					self.Advance()
				} else {
					patternChars = append(patternChars, self.Advance())
					if !self.AtEnd() {
						patternChars = append(patternChars, self.Advance())
					}
				}
			} else if isExpansionStart(self.Source, self.Pos, "$(") {
				patternChars = append(patternChars, self.Advance())
				patternChars = append(patternChars, self.Advance())
				if !self.AtEnd() && self.Peek() == "(" {
					patternChars = append(patternChars, self.Advance())
					parenDepth := 2
					for !self.AtEnd() && parenDepth > 0 {
						c := self.Peek()
						if c == "(" {
							parenDepth++
						} else if c == ")" {
							parenDepth--
						}
						patternChars = append(patternChars, self.Advance())
					}
				} else {
					extglobDepth++
				}
			} else if ch == "(" && extglobDepth > 0 {
				patternChars = append(patternChars, self.Advance())
				extglobDepth++
			} else if self.extglob && isExtglobPrefix(ch) && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "(" {
				patternChars = append(patternChars, self.Advance())
				patternChars = append(patternChars, self.Advance())
				extglobDepth++
			} else if ch == "[" {
				isCharClass := false
				scanPos := self.Pos + 1
				scanDepth := 0
				hasFirstBracketLiteral := false
				if scanPos < self.Length && isCaretOrBang(string(_runeAt(self.Source, scanPos))) {
					scanPos++
				}
				if scanPos < self.Length && string(_runeAt(self.Source, scanPos)) == "]" {
					if strings.Index(self.Source, "]") != -1 {
						scanPos++
						hasFirstBracketLiteral = true
					}
				}
				for scanPos < self.Length {
					sc := string(_runeAt(self.Source, scanPos))
					if sc == "]" && scanDepth == 0 {
						isCharClass = true
						break
					} else if sc == "[" {
						scanDepth++
					} else if sc == ")" && scanDepth == 0 {
						break
					} else if sc == "|" && scanDepth == 0 {
						break
					}
					scanPos++
				}
				if isCharClass {
					patternChars = append(patternChars, self.Advance())
					if !self.AtEnd() && isCaretOrBang(self.Peek()) {
						patternChars = append(patternChars, self.Advance())
					}
					if hasFirstBracketLiteral && !self.AtEnd() && self.Peek() == "]" {
						patternChars = append(patternChars, self.Advance())
					}
					for !self.AtEnd() && self.Peek() != "]" {
						patternChars = append(patternChars, self.Advance())
					}
					if !self.AtEnd() {
						patternChars = append(patternChars, self.Advance())
					}
				} else {
					patternChars = append(patternChars, self.Advance())
				}
			} else if ch == "'" {
				patternChars = append(patternChars, self.Advance())
				for !self.AtEnd() && self.Peek() != "'" {
					patternChars = append(patternChars, self.Advance())
				}
				if !self.AtEnd() {
					patternChars = append(patternChars, self.Advance())
				}
			} else if ch == "\"" {
				patternChars = append(patternChars, self.Advance())
				for !self.AtEnd() && self.Peek() != "\"" {
					if self.Peek() == "\\" && self.Pos+1 < self.Length {
						patternChars = append(patternChars, self.Advance())
					}
					patternChars = append(patternChars, self.Advance())
				}
				if !self.AtEnd() {
					patternChars = append(patternChars, self.Advance())
				}
			} else if isWhitespace(ch) {
				if extglobDepth > 0 {
					patternChars = append(patternChars, self.Advance())
				} else {
					self.Advance()
				}
			} else {
				patternChars = append(patternChars, self.Advance())
			}
		}
		pattern := strings.Join(patternChars, "")
		if !(pattern != "") {
			panic(NewParseError("Expected pattern in case statement", self.lexPeekToken().Pos, 0))
		}
		self.SkipWhitespace()
		var body Node
		isEmptyBody := self.lexPeekCaseTerminator() != ""
		if !isEmptyBody {
			self.SkipWhitespaceAndNewlines()
			if !self.AtEnd() && !self.lexIsAtReservedWord("esac") {
				isAtTerminator := self.lexPeekCaseTerminator() != ""
				if !isAtTerminator {
					body = self.ParseListUntil(map[string]struct{}{"esac": {}})
					self.SkipWhitespace()
				}
			}
		}
		terminator := self.consumeCaseTerminator()
		self.SkipWhitespaceAndNewlines()
		patterns = append(patterns, &CasePattern{Pattern: pattern, Body: body, Terminator: terminator, Kind: "pattern"})
	}
	self.clearState(ParserStateFlagsPSTCASEPAT)
	self.SkipWhitespaceAndNewlines()
	if !self.lexConsumeWord("esac") {
		self.clearState(ParserStateFlagsPSTCASESTMT)
		panic(NewParseError("Expected 'esac' to close case statement", self.lexPeekToken().Pos, 0))
	}
	self.clearState(ParserStateFlagsPSTCASESTMT)
	return &Case{Word: word, Patterns: patterns, Redirects: self.collectRedirects(), Kind: "case"}
}

func (self *Parser) ParseCoproc() *Coproc {
	self.SkipWhitespace()
	if !self.lexConsumeWord("coproc") {
		return nil
	}
	self.SkipWhitespace()
	name := ""
	ch := ""
	if !self.AtEnd() {
		ch = self.Peek()
	}
	var body Node
	if ch == "{" {
		body = self.ParseBraceGroup()
		if !_isNilInterface(body) {
			return &Coproc{Command: body, Name: name, Kind: "coproc"}
		}
	}
	if ch == "(" {
		if self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "(" {
			body = self.ParseArithmeticCommand()
			if !_isNilInterface(body) {
				return &Coproc{Command: body, Name: name, Kind: "coproc"}
			}
		}
		body = self.ParseSubshell()
		if !_isNilInterface(body) {
			return &Coproc{Command: body, Name: name, Kind: "coproc"}
		}
	}
	nextWord := self.lexPeekReservedWord()
	if nextWord != "" && func() bool { _, ok := COMPOUNDKEYWORDS[nextWord]; return ok }() {
		body = self.ParseCompoundCommand()
		if !_isNilInterface(body) {
			return &Coproc{Command: body, Name: name, Kind: "coproc"}
		}
	}
	wordStart := self.Pos
	potentialName := self.PeekWord()
	if potentialName != "" {
		for !self.AtEnd() && !isMetachar(self.Peek()) && !isQuote(self.Peek()) {
			self.Advance()
		}
		self.SkipWhitespace()
		ch = ""
		if !self.AtEnd() {
			ch = self.Peek()
		}
		nextWord = self.lexPeekReservedWord()
		if isValidIdentifier(potentialName) {
			if ch == "{" {
				name = potentialName
				body = self.ParseBraceGroup()
				if !_isNilInterface(body) {
					return &Coproc{Command: body, Name: name, Kind: "coproc"}
				}
			} else if ch == "(" {
				name = potentialName
				if self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "(" {
					body = self.ParseArithmeticCommand()
				} else {
					body = self.ParseSubshell()
				}
				if !_isNilInterface(body) {
					return &Coproc{Command: body, Name: name, Kind: "coproc"}
				}
			} else if nextWord != "" && func() bool { _, ok := COMPOUNDKEYWORDS[nextWord]; return ok }() {
				name = potentialName
				body = self.ParseCompoundCommand()
				if !_isNilInterface(body) {
					return &Coproc{Command: body, Name: name, Kind: "coproc"}
				}
			}
		}
		self.Pos = wordStart
	}
	body = self.ParseCommand()
	if !_isNilInterface(body) {
		return &Coproc{Command: body, Name: name, Kind: "coproc"}
	}
	panic(NewParseError("Expected command after coproc", self.Pos, 0))
}

func (self *Parser) ParseFunction() *Function {
	self.SkipWhitespace()
	if self.AtEnd() {
		return nil
	}
	savedPos := self.Pos
	var name string
	var body Node
	if self.lexIsAtReservedWord("function") {
		self.lexConsumeWord("function")
		self.SkipWhitespace()
		name = self.PeekWord()
		if name == "" {
			self.Pos = savedPos
			return nil
		}
		self.ConsumeWord(name)
		self.SkipWhitespace()
		if !self.AtEnd() && self.Peek() == "(" {
			if self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == ")" {
				self.Advance()
				self.Advance()
			}
		}
		self.SkipWhitespaceAndNewlines()
		body = self.parseCompoundCommand()
		if _isNilInterface(body) {
			panic(NewParseError("Expected function body", self.Pos, 0))
		}
		return &Function{Name: name, Body: body, Kind: "function"}
	}
	name = self.PeekWord()
	if name == "" || func() bool { _, ok := RESERVEDWORDS[name]; return ok }() {
		return nil
	}
	if looksLikeAssignment(name) {
		return nil
	}
	self.SkipWhitespace()
	nameStart := self.Pos
	for !self.AtEnd() && !isMetachar(self.Peek()) && !isQuote(self.Peek()) && !isParen(self.Peek()) {
		self.Advance()
	}
	name = substring(self.Source, nameStart, self.Pos)
	if !(name != "") {
		self.Pos = savedPos
		return nil
	}
	braceDepth := 0
	i := 0
	for i < _runeLen(name) {
		if isExpansionStart(name, i, "${") {
			braceDepth++
			i += 2
			continue
		}
		if string(_runeAt(name, i)) == "}" {
			braceDepth--
		}
		i++
	}
	if braceDepth > 0 {
		self.Pos = savedPos
		return nil
	}
	posAfterName := self.Pos
	self.SkipWhitespace()
	hasWhitespace := self.Pos > posAfterName
	if !hasWhitespace && name != "" && strings.Contains("*?@+!$", string(_runeAt(name, _runeLen(name)-1))) {
		self.Pos = savedPos
		return nil
	}
	if self.AtEnd() || self.Peek() != "(" {
		self.Pos = savedPos
		return nil
	}
	self.Advance()
	self.SkipWhitespace()
	if self.AtEnd() || self.Peek() != ")" {
		self.Pos = savedPos
		return nil
	}
	self.Advance()
	self.SkipWhitespaceAndNewlines()
	body = self.parseCompoundCommand()
	if _isNilInterface(body) {
		panic(NewParseError("Expected function body", self.Pos, 0))
	}
	return &Function{Name: name, Body: body, Kind: "function"}
}

func (self *Parser) parseCompoundCommand() Node {
	var result Node = self.ParseBraceGroup()
	if !_isNilInterface(result) {
		return result
	}
	if !self.AtEnd() && self.Peek() == "(" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "(" {
		result = self.ParseArithmeticCommand()
		if !_isNilInterface(result) {
			return result
		}
	}
	result = self.ParseSubshell()
	if !_isNilInterface(result) {
		return result
	}
	result = self.ParseConditionalExpr()
	if !_isNilInterface(result) {
		return result
	}
	result = self.ParseIf()
	if !_isNilInterface(result) {
		return result
	}
	result = self.ParseWhile()
	if !_isNilInterface(result) {
		return result
	}
	result = self.ParseUntil()
	if !_isNilInterface(result) {
		return result
	}
	result = self.ParseFor()
	if !_isNilInterface(result) {
		return result
	}
	result = self.ParseCase()
	if !_isNilInterface(result) {
		return result
	}
	result = self.ParseSelect()
	if !_isNilInterface(result) {
		return result
	}
	return nil
}

func (self *Parser) atListUntilTerminator(stopWords map[string]struct{}) bool {
	if self.AtEnd() {
		return true
	}
	if self.Peek() == ")" {
		return true
	}
	if self.Peek() == "}" {
		nextPos := self.Pos + 1
		if nextPos >= self.Length || isWordEndContext(string(_runeAt(self.Source, nextPos))) {
			return true
		}
	}
	reserved := self.lexPeekReservedWord()
	if reserved != "" && func() bool { _, ok := stopWords[reserved]; return ok }() {
		return true
	}
	if self.lexPeekCaseTerminator() != "" {
		return true
	}
	return false
}

func (self *Parser) ParseListUntil(stopWords map[string]struct{}) Node {
	self.SkipWhitespaceAndNewlines()
	reserved := self.lexPeekReservedWord()
	if reserved != "" && func() bool { _, ok := stopWords[reserved]; return ok }() {
		return nil
	}
	pipeline := self.ParsePipeline()
	if _isNilInterface(pipeline) {
		return nil
	}
	parts := []Node{pipeline}
	for true {
		self.SkipWhitespace()
		op := self.ParseListOperator()
		if op == "" {
			if !self.AtEnd() && self.Peek() == "\n" {
				self.Advance()
				self.gatherHeredocBodies()
				if self.cmdsubHeredocEnd != -1 && self.cmdsubHeredocEnd > self.Pos {
					self.Pos = self.cmdsubHeredocEnd
					self.cmdsubHeredocEnd = -1
				}
				self.SkipWhitespaceAndNewlines()
				if self.atListUntilTerminator(stopWords) {
					break
				}
				nextOp := self.peekListOperator()
				if nextOp == "&" || nextOp == ";" {
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
			self.SkipWhitespaceAndNewlines()
			if self.atListUntilTerminator(stopWords) {
				break
			}
			parts = append(parts, &Operator{Op: op, Kind: "operator"})
		} else if op == "&" {
			parts = append(parts, &Operator{Op: op, Kind: "operator"})
			self.SkipWhitespaceAndNewlines()
			if self.atListUntilTerminator(stopWords) {
				break
			}
		} else if op == "&&" || op == "||" {
			parts = append(parts, &Operator{Op: op, Kind: "operator"})
			self.SkipWhitespaceAndNewlines()
		} else {
			parts = append(parts, &Operator{Op: op, Kind: "operator"})
		}
		if self.atListUntilTerminator(stopWords) {
			break
		}
		pipeline = self.ParsePipeline()
		if _isNilInterface(pipeline) {
			panic(NewParseError("Expected command after "+op, self.Pos, 0))
		}
		parts = append(parts, pipeline)
	}
	if len(parts) == 1 {
		return parts[0]
	}
	return &List{Parts: parts, Kind: "list"}
}

func (self *Parser) ParseCompoundCommand() Node {
	self.SkipWhitespace()
	if self.AtEnd() {
		return nil
	}
	ch := self.Peek()
	var result Node
	if ch == "(" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "(" {
		result = self.ParseArithmeticCommand()
		if !_isNilInterface(result) {
			return result
		}
	}
	if ch == "(" {
		return self.ParseSubshell()
	}
	if ch == "{" {
		result = self.ParseBraceGroup()
		if !_isNilInterface(result) {
			return result
		}
	}
	if ch == "[" && self.Pos+1 < self.Length && string(_runeAt(self.Source, self.Pos+1)) == "[" {
		result = self.ParseConditionalExpr()
		if !_isNilInterface(result) {
			return result
		}
	}
	reserved := self.lexPeekReservedWord()
	if reserved == "" && self.inProcessSub {
		word := self.PeekWord()
		if word != "" && _runeLen(word) > 1 && string(_runeAt(word, 0)) == "}" {
			keywordWord := _Substring(word, 1, _runeLen(word))
			if func() bool { _, ok := RESERVEDWORDS[keywordWord]; return ok }() || keywordWord == "{" || keywordWord == "}" || keywordWord == "[[" || keywordWord == "]]" || keywordWord == "!" || keywordWord == "time" {
				reserved = keywordWord
			}
		}
	}
	if reserved == "fi" || reserved == "then" || reserved == "elif" || reserved == "else" || reserved == "done" || reserved == "esac" || reserved == "do" || reserved == "in" {
		panic(NewParseError(fmt.Sprintf("Unexpected reserved word '%v'", reserved), self.lexPeekToken().Pos, 0))
	}
	if reserved == "if" {
		return self.ParseIf()
	}
	if reserved == "while" {
		return self.ParseWhile()
	}
	if reserved == "until" {
		return self.ParseUntil()
	}
	if reserved == "for" {
		return self.ParseFor()
	}
	if reserved == "select" {
		return self.ParseSelect()
	}
	if reserved == "case" {
		return self.ParseCase()
	}
	if reserved == "function" {
		return self.ParseFunction()
	}
	if reserved == "coproc" {
		return self.ParseCoproc()
	}
	func_ := self.ParseFunction()
	if func_ != nil {
		return func_
	}
	return self.ParseCommand()
}

func (self *Parser) ParsePipeline() Node {
	self.SkipWhitespace()
	prefixOrder := ""
	timePosix := false
	if self.lexIsAtReservedWord("time") {
		self.lexConsumeWord("time")
		prefixOrder = "time"
		self.SkipWhitespace()
		var saved int
		if !self.AtEnd() && self.Peek() == "-" {
			saved = self.Pos
			self.Advance()
			if !self.AtEnd() && self.Peek() == "p" {
				self.Advance()
				if self.AtEnd() || isMetachar(self.Peek()) {
					timePosix = true
				} else {
					self.Pos = saved
				}
			} else {
				self.Pos = saved
			}
		}
		self.SkipWhitespace()
		if !self.AtEnd() && startsWithAt(self.Source, self.Pos, "--") {
			if self.Pos+2 >= self.Length || isWhitespace(string(_runeAt(self.Source, self.Pos+2))) {
				self.Advance()
				self.Advance()
				timePosix = true
				self.SkipWhitespace()
			}
		}
		for self.lexIsAtReservedWord("time") {
			self.lexConsumeWord("time")
			self.SkipWhitespace()
			if !self.AtEnd() && self.Peek() == "-" {
				saved = self.Pos
				self.Advance()
				if !self.AtEnd() && self.Peek() == "p" {
					self.Advance()
					if self.AtEnd() || isMetachar(self.Peek()) {
						timePosix = true
					} else {
						self.Pos = saved
					}
				} else {
					self.Pos = saved
				}
			}
		}
		self.SkipWhitespace()
		if !self.AtEnd() && self.Peek() == "!" {
			if (self.Pos+1 >= self.Length || isNegationBoundary(string(_runeAt(self.Source, self.Pos+1)))) && !self.isBangFollowedByProcsub() {
				self.Advance()
				prefixOrder = "time_negation"
				self.SkipWhitespace()
			}
		}
	} else if !self.AtEnd() && self.Peek() == "!" {
		if (self.Pos+1 >= self.Length || isNegationBoundary(string(_runeAt(self.Source, self.Pos+1)))) && !self.isBangFollowedByProcsub() {
			self.Advance()
			self.SkipWhitespace()
			inner := self.ParsePipeline()
			if !_isNilInterface(inner) && inner.GetKind() == "negation" {
				if !_isNilInterface(inner.(*Negation).Pipeline) {
					return inner.(*Negation).Pipeline
				} else {
					return &Command{Words: []*Word{}, Kind: "command"}
				}
			}
			return &Negation{Pipeline: inner, Kind: "negation"}
		}
	}
	result := self.parseSimplePipeline()
	if prefixOrder == "time" {
		result = &Time{Pipeline: result, Posix: timePosix, Kind: "time"}
	} else if prefixOrder == "negation" {
		result = &Negation{Pipeline: result, Kind: "negation"}
	} else if prefixOrder == "time_negation" {
		result = &Time{Pipeline: result, Posix: timePosix, Kind: "time"}
		result = &Negation{Pipeline: result, Kind: "negation"}
	} else if prefixOrder == "negation_time" {
		result = &Time{Pipeline: result, Posix: timePosix, Kind: "time"}
		result = &Negation{Pipeline: result, Kind: "negation"}
	} else if result == nil {
		return nil
	}
	return result
}

func (self *Parser) parseSimplePipeline() Node {
	cmd := self.ParseCompoundCommand()
	if _isNilInterface(cmd) {
		return nil
	}
	commands := []Node{cmd}
	for true {
		self.SkipWhitespace()
		tokenType, _ := self.lexPeekOperator()
		if tokenType == 0 {
			break
		}
		if tokenType != TokenTypePIPE && tokenType != TokenTypePIPEAMP {
			break
		}
		self.lexNextToken()
		isPipeBoth := tokenType == TokenTypePIPEAMP
		self.SkipWhitespaceAndNewlines()
		if isPipeBoth {
			commands = append(commands, &PipeBoth{Kind: "pipe-both"})
		}
		cmd = self.ParseCompoundCommand()
		if _isNilInterface(cmd) {
			panic(NewParseError("Expected command after |", self.Pos, 0))
		}
		commands = append(commands, cmd)
	}
	if len(commands) == 1 {
		return commands[0]
	}
	return &Pipeline{Commands: commands, Kind: "pipeline"}
}

func (self *Parser) ParseListOperator() string {
	self.SkipWhitespace()
	tokenType, _ := self.lexPeekOperator()
	if tokenType == 0 {
		return ""
	}
	if tokenType == TokenTypeANDAND {
		self.lexNextToken()
		return "&&"
	}
	if tokenType == TokenTypeOROR {
		self.lexNextToken()
		return "||"
	}
	if tokenType == TokenTypeSEMI {
		self.lexNextToken()
		return ";"
	}
	if tokenType == TokenTypeAMP {
		self.lexNextToken()
		return "&"
	}
	return ""
}

func (self *Parser) peekListOperator() string {
	savedPos := self.Pos
	op := self.ParseListOperator()
	self.Pos = savedPos
	return op
}

func (self *Parser) ParseList(newlineAsSeparator bool) Node {
	if newlineAsSeparator {
		self.SkipWhitespaceAndNewlines()
	} else {
		self.SkipWhitespace()
	}
	pipeline := self.ParsePipeline()
	if _isNilInterface(pipeline) {
		return nil
	}
	parts := []Node{pipeline}
	if self.inState(ParserStateFlagsPSTEOFTOKEN) && self.atEofToken() {
		if len(parts) == 1 {
			return parts[0]
		}
		return &List{Parts: parts, Kind: "list"}
	}
	for true {
		self.SkipWhitespace()
		op := self.ParseListOperator()
		if op == "" {
			if !self.AtEnd() && self.Peek() == "\n" {
				if !newlineAsSeparator {
					break
				}
				self.Advance()
				self.gatherHeredocBodies()
				if self.cmdsubHeredocEnd != -1 && self.cmdsubHeredocEnd > self.Pos {
					self.Pos = self.cmdsubHeredocEnd
					self.cmdsubHeredocEnd = -1
				}
				self.SkipWhitespaceAndNewlines()
				if self.AtEnd() || self.atListTerminatingBracket() {
					break
				}
				nextOp := self.peekListOperator()
				if nextOp == "&" || nextOp == ";" {
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
		parts = append(parts, &Operator{Op: op, Kind: "operator"})
		if op == "&&" || op == "||" {
			self.SkipWhitespaceAndNewlines()
		} else if op == "&" {
			self.SkipWhitespace()
			if self.AtEnd() || self.atListTerminatingBracket() {
				break
			}
			if self.Peek() == "\n" {
				if newlineAsSeparator {
					self.SkipWhitespaceAndNewlines()
					if self.AtEnd() || self.atListTerminatingBracket() {
						break
					}
				} else {
					break
				}
			}
		} else if op == ";" {
			self.SkipWhitespace()
			if self.AtEnd() || self.atListTerminatingBracket() {
				break
			}
			if self.Peek() == "\n" {
				if newlineAsSeparator {
					self.SkipWhitespaceAndNewlines()
					if self.AtEnd() || self.atListTerminatingBracket() {
						break
					}
				} else {
					break
				}
			}
		}
		pipeline = self.ParsePipeline()
		if _isNilInterface(pipeline) {
			panic(NewParseError("Expected command after "+op, self.Pos, 0))
		}
		parts = append(parts, pipeline)
		if self.inState(ParserStateFlagsPSTEOFTOKEN) && self.atEofToken() {
			break
		}
	}
	if len(parts) == 1 {
		return parts[0]
	}
	return &List{Parts: parts, Kind: "list"}
}

func (self *Parser) ParseComment() Node {
	if self.AtEnd() || self.Peek() != "#" {
		return nil
	}
	start := self.Pos
	for !self.AtEnd() && self.Peek() != "\n" {
		self.Advance()
	}
	text := substring(self.Source, start, self.Pos)
	return &Comment{Text: text, Kind: "comment"}
}

func (self *Parser) Parse() []Node {
	source := strings.TrimSpace(self.Source)
	if !(source != "") {
		return []Node{&Empty{Kind: "empty"}}
	}
	results := []Node{}
	for true {
		self.SkipWhitespace()
		for !self.AtEnd() && self.Peek() == "\n" {
			self.Advance()
		}
		if self.AtEnd() {
			break
		}
		comment := self.ParseComment()
		if !(!_isNilInterface(comment)) {
			break
		}
	}
	for !self.AtEnd() {
		result := self.ParseList(false)
		if !_isNilInterface(result) {
			results = append(results, result)
		}
		self.SkipWhitespace()
		foundNewline := false
		for !self.AtEnd() && self.Peek() == "\n" {
			foundNewline = true
			self.Advance()
			self.gatherHeredocBodies()
			if self.cmdsubHeredocEnd != -1 && self.cmdsubHeredocEnd > self.Pos {
				self.Pos = self.cmdsubHeredocEnd
				self.cmdsubHeredocEnd = -1
			}
			self.SkipWhitespace()
		}
		if !foundNewline && !self.AtEnd() {
			panic(NewParseError("Syntax error", self.Pos, 0))
		}
	}
	if !(len(results) > 0) {
		return []Node{&Empty{Kind: "empty"}}
	}
	if self.sawNewlineInSingleQuote && self.Source != "" && string(_runeAt(self.Source, _runeLen(self.Source)-1)) == "\\" && !(_runeLen(self.Source) >= 3 && _Substring(self.Source, _runeLen(self.Source)-3, _runeLen(self.Source)-1) == "\\\n") {
		if !self.lastWordOnOwnLine(results) {
			self.stripTrailingBackslashFromLastWord(results)
		}
	}
	return results
}

func (self *Parser) lastWordOnOwnLine(nodes []Node) bool {
	return len(nodes) >= 2
}

func (self *Parser) stripTrailingBackslashFromLastWord(nodes []Node) {
	if !(len(nodes) > 0) {
		return
	}
	lastNode := nodes[len(nodes)-1]
	lastWord := self.findLastWord(lastNode)
	if lastWord != nil && strings.HasSuffix(lastWord.Value, "\\") {
		lastWord.Value = substring(lastWord.Value, 0, _runeLen(lastWord.Value)-1)
		if !(lastWord.Value != "") && func() bool { _, ok := lastNode.(*Command); return ok }() && len(lastNode.(*Command).Words) > 0 {
			lastNode.(*Command).Words = lastNode.(*Command).Words[:len(lastNode.(*Command).Words)-1]
		}
	}
}

func (self *Parser) findLastWord(node Node) *Word {
	switch node := node.(type) {
	case *Word:
		return node
	}
	switch node := node.(type) {
	case *Command:
		if len(node.Words) > 0 {
			lastWord := node.Words[len(node.Words)-1]
			if strings.HasSuffix(lastWord.Value, "\\") {
				return lastWord
			}
		}
		if len(node.Redirects) > 0 {
			lastRedirect := node.Redirects[len(node.Redirects)-1]
			switch lastRedirect := lastRedirect.(type) {
			case *Redirect:
				return lastRedirect.Target
			}
		}
		if len(node.Words) > 0 {
			return node.Words[len(node.Words)-1]
		}
	}
	switch node := node.(type) {
	case *Pipeline:
		if len(node.Commands) > 0 {
			return self.findLastWord(node.Commands[len(node.Commands)-1])
		}
	}
	switch node := node.(type) {
	case *List:
		if len(node.Parts) > 0 {
			return self.findLastWord(node.Parts[len(node.Parts)-1])
		}
	}
	return nil
}

func isHexDigit(c string) bool {
	return c >= "0" && c <= "9" || c >= "a" && c <= "f" || c >= "A" && c <= "F"
}

func isOctalDigit(c string) bool {
	return c >= "0" && c <= "7"
}

func getAnsiEscape(c string) int {
	return _mapGet(ANSICESCAPES, c, -1)
}

func isWhitespace(c string) bool {
	return c == " " || c == "\t" || c == "\n"
}

func isWhitespaceNoNewline(c string) bool {
	return c == " " || c == "\t"
}

func substring(s string, start int, end int) string {
	if end > _runeLen(s) {
		end = _runeLen(s)
	}
	return _Substring(s, start, end)
}

func startsWithAt(s string, pos int, prefix string) bool {
	return strings.HasPrefix(s[pos:], prefix)
}

func countConsecutiveDollarsBefore(s string, pos int) int {
	count := 0
	k := pos - 1
	for k >= 0 && string(_runeAt(s, k)) == "$" {
		bsCount := 0
		j := k - 1
		for j >= 0 && string(_runeAt(s, j)) == "\\" {
			bsCount++
			j--
		}
		if (bsCount % 2) == 1 {
			break
		}
		count++
		k--
	}
	return count
}

func isExpansionStart(s string, pos int, delimiter string) bool {
	if !startsWithAt(s, pos, delimiter) {
		return false
	}
	return (countConsecutiveDollarsBefore(s, pos) % 2) == 0
}

func sublist(lst []Node, start int, end int) []Node {
	return lst[start:end]
}

func repeatStr(s string, n int) string {
	result := []string{}
	i := 0
	for i < n {
		result = append(result, s)
		i++
	}
	return strings.Join(result, "")
}

func stripLineContinuationsCommentAware(text string) string {
	result := []string{}
	i := 0
	inComment := false
	quote := NewQuoteState()
	for i < _runeLen(text) {
		c := string(_runeAt(text, i))
		if c == "\\" && i+1 < _runeLen(text) && string(_runeAt(text, i+1)) == "\n" {
			numPrecedingBackslashes := 0
			j := i - 1
			for j >= 0 && string(_runeAt(text, j)) == "\\" {
				numPrecedingBackslashes++
				j--
			}
			if (numPrecedingBackslashes % 2) == 0 {
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
			i++
			continue
		}
		if c == "'" && !quote.Double && !inComment {
			quote.Single = !quote.Single
		} else if c == "\"" && !quote.Single && !inComment {
			quote.Double = !quote.Double
		} else if c == "#" && !quote.Single && !inComment {
			inComment = true
		}
		result = append(result, c)
		i++
	}
	return strings.Join(result, "")
}

func appendRedirects(base string, redirects []Node) string {
	if len(redirects) > 0 {
		parts := []string{}
		for _, r := range redirects {
			parts = append(parts, r.ToSexp())
		}
		return base + " " + strings.Join(parts, " ")
	}
	return base
}

func formatArithVal(s string) string {
	w := &Word{Value: s, Parts: []Node{}, Kind: "word"}
	val := w.expandAllAnsiCQuotes(s)
	val = w.stripLocaleStringDollars(val)
	val = w.formatCommandSubstitutions(val, false)
	val = strings.ReplaceAll(strings.ReplaceAll(val, "\\", "\\\\"), "\"", "\\\"")
	val = strings.ReplaceAll(strings.ReplaceAll(val, "\n", "\\n"), "\t", "\\t")
	return val
}

func consumeSingleQuote(s string, start int) (int, []string) {
	chars := []string{"'"}
	i := start + 1
	for i < _runeLen(s) && string(_runeAt(s, i)) != "'" {
		chars = append(chars, string(_runeAt(s, i)))
		i++
	}
	if i < _runeLen(s) {
		chars = append(chars, string(_runeAt(s, i)))
		i++
	}
	return i, chars
}

func consumeDoubleQuote(s string, start int) (int, []string) {
	chars := []string{"\""}
	i := start + 1
	for i < _runeLen(s) && string(_runeAt(s, i)) != "\"" {
		if string(_runeAt(s, i)) == "\\" && i+1 < _runeLen(s) {
			chars = append(chars, string(_runeAt(s, i)))
			i++
		}
		chars = append(chars, string(_runeAt(s, i)))
		i++
	}
	if i < _runeLen(s) {
		chars = append(chars, string(_runeAt(s, i)))
		i++
	}
	return i, chars
}

func hasBracketClose(s string, start int, depth int) bool {
	i := start
	for i < _runeLen(s) {
		if string(_runeAt(s, i)) == "]" {
			return true
		}
		if (string(_runeAt(s, i)) == "|" || string(_runeAt(s, i)) == ")") && depth == 0 {
			return false
		}
		i++
	}
	return false
}

func consumeBracketClass(s string, start int, depth int) (int, []string, bool) {
	scanPos := start + 1
	if scanPos < _runeLen(s) && (string(_runeAt(s, scanPos)) == "!" || string(_runeAt(s, scanPos)) == "^") {
		scanPos++
	}
	if scanPos < _runeLen(s) && string(_runeAt(s, scanPos)) == "]" {
		if hasBracketClose(s, scanPos+1, depth) {
			scanPos++
		}
	}
	isBracket := false
	for scanPos < _runeLen(s) {
		if string(_runeAt(s, scanPos)) == "]" {
			isBracket = true
			break
		}
		if string(_runeAt(s, scanPos)) == ")" && depth == 0 {
			break
		}
		if string(_runeAt(s, scanPos)) == "|" && depth == 0 {
			break
		}
		scanPos++
	}
	if !isBracket {
		return start + 1, []string{"["}, false
	}
	chars := []string{"["}
	i := start + 1
	if i < _runeLen(s) && (string(_runeAt(s, i)) == "!" || string(_runeAt(s, i)) == "^") {
		chars = append(chars, string(_runeAt(s, i)))
		i++
	}
	if i < _runeLen(s) && string(_runeAt(s, i)) == "]" {
		if hasBracketClose(s, i+1, depth) {
			chars = append(chars, string(_runeAt(s, i)))
			i++
		}
	}
	for i < _runeLen(s) && string(_runeAt(s, i)) != "]" {
		chars = append(chars, string(_runeAt(s, i)))
		i++
	}
	if i < _runeLen(s) {
		chars = append(chars, string(_runeAt(s, i)))
		i++
	}
	return i, chars, true
}

func formatCondBody(node Node) string {
	kind := node.GetKind()
	if kind == "unary-test" {
		operandVal := node.(*UnaryTest).Operand.(*Word).GetCondFormattedValue()
		return node.(*UnaryTest).Op + " " + operandVal
	}
	if kind == "binary-test" {
		leftVal := node.(*BinaryTest).Left.(*Word).GetCondFormattedValue()
		rightVal := node.(*BinaryTest).Right.(*Word).GetCondFormattedValue()
		return leftVal + " " + node.(*BinaryTest).Op + " " + rightVal
	}
	if kind == "cond-and" {
		return formatCondBody(node.(*CondAnd).Left) + " && " + formatCondBody(node.(*CondAnd).Right)
	}
	if kind == "cond-or" {
		return formatCondBody(node.(*CondOr).Left) + " || " + formatCondBody(node.(*CondOr).Right)
	}
	if kind == "cond-not" {
		return "! " + formatCondBody(node.(*CondNot).Operand)
	}
	if kind == "cond-paren" {
		return "( " + formatCondBody(node.(*CondParen).Inner) + " )"
	}
	return ""
}

func startsWithSubshell(node Node) bool {
	switch node.(type) {
	case *Subshell:
		return true
	}
	switch node := node.(type) {
	case *List:
		for _, p := range node.Parts {
			if p.GetKind() != "operator" {
				return startsWithSubshell(p)
			}
		}
		return false
	}
	switch node := node.(type) {
	case *Pipeline:
		if len(node.Commands) > 0 {
			return startsWithSubshell(node.Commands[0])
		}
		return false
	}
	return false
}

func formatCmdsubNode(node Node, indent int, inProcsub bool, compactRedirects bool, procsubFirst bool) string {
	if _isNilInterface(node) {
		return ""
	}
	sp := repeatStr(" ", indent)
	innerSp := repeatStr(" ", indent+4)
	switch node.(type) {
	case *ArithEmpty:
		return ""
	}
	switch node := node.(type) {
	case *Command:
		parts := []string{}
		for _, w := range node.Words {
			val := w.expandAllAnsiCQuotes(w.Value)
			val = w.stripLocaleStringDollars(val)
			val = w.normalizeArrayWhitespace(val)
			val = w.formatCommandSubstitutions(val, false)
			parts = append(parts, val)
		}
		var heredocs []*HereDoc = []*HereDoc{}
		for _, r := range node.Redirects {
			switch r := r.(type) {
			case *HereDoc:
				heredocs = append(heredocs, r)
			}
		}
		for _, r := range node.Redirects {
			parts = append(parts, formatRedirect(r, compactRedirects, true))
		}
		var result string
		if compactRedirects && len(node.Words) > 0 && len(node.Redirects) > 0 {
			wordParts := parts[:len(node.Words)]
			var redirectParts []string = parts[len(node.Words):]
			result = strings.Join(wordParts, " ") + strings.Join(redirectParts, "")
		} else {
			result = strings.Join(parts, " ")
		}
		for _, h := range heredocs {
			result = result + formatHeredocBody(h)
		}
		return result
	}
	switch node := node.(type) {
	case *Pipeline:
		var cmds []struct {
			F0 Node
			F1 bool
		} = []struct {
			F0 Node
			F1 bool
		}{}
		i := 0
		var cmd Node
		var needsRedirect bool
		for i < len(node.Commands) {
			cmd = node.Commands[i]
			switch cmd.(type) {
			case *PipeBoth:
				i++
				continue
			}
			needsRedirect = i+1 < len(node.Commands) && node.Commands[i+1].GetKind() == "pipe-both"
			cmds = append(cmds, struct {
				F0 Node
				F1 bool
			}{cmd, needsRedirect})
			i++
		}
		resultParts := []string{}
		idx := 0
		for idx < len(cmds) {
			{
				var entry struct {
					F0 Node
					F1 bool
				} = cmds[idx]
				cmd = entry.F0
				needsRedirect = entry.F1
			}
			formatted := formatCmdsubNode(cmd, indent, inProcsub, false, procsubFirst && idx == 0)
			isLast := idx == len(cmds)-1
			hasHeredoc := false
			if cmd.GetKind() == "command" && len(cmd.(*Command).Redirects) > 0 {
				for _, r := range cmd.(*Command).Redirects {
					switch r.(type) {
					case *HereDoc:
						hasHeredoc = true
						break
					}
				}
			}
			var firstNl int
			if needsRedirect {
				if hasHeredoc {
					firstNl = strings.Index(formatted, "\n")
					if firstNl != -1 {
						formatted = _Substring(formatted, 0, firstNl) + " 2>&1" + _Substring(formatted, firstNl, _runeLen(formatted))
					} else {
						formatted = formatted + " 2>&1"
					}
				} else {
					formatted = formatted + " 2>&1"
				}
			}
			if !isLast && hasHeredoc {
				firstNl = strings.Index(formatted, "\n")
				if firstNl != -1 {
					formatted = _Substring(formatted, 0, firstNl) + " |" + _Substring(formatted, firstNl, _runeLen(formatted))
				}
				resultParts = append(resultParts, formatted)
			} else {
				resultParts = append(resultParts, formatted)
			}
			idx++
		}
		compactPipe := inProcsub && len(cmds) > 0 && cmds[0].F0.GetKind() == "subshell"
		result := ""
		idx = 0
		for idx < len(resultParts) {
			part := resultParts[idx]
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
			idx++
		}
		return result
	}
	switch node := node.(type) {
	case *List:
		hasHeredoc := false
		for _, p := range node.Parts {
			if p.GetKind() == "command" && len(p.(*Command).Redirects) > 0 {
				for _, r := range p.(*Command).Redirects {
					switch r.(type) {
					case *HereDoc:
						hasHeredoc = true
						break
					}
				}
			} else {
				switch p := p.(type) {
				case *Pipeline:
					for _, cmd := range p.Commands {
						if cmd.GetKind() == "command" && len(cmd.(*Command).Redirects) > 0 {
							for _, r := range cmd.(*Command).Redirects {
								switch r.(type) {
								case *HereDoc:
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
		}
		result := []string{}
		skippedSemi := false
		cmdCount := 0
		for _, p := range node.Parts {
			switch p := p.(type) {
			case *Operator:
				if p.Op == ";" {
					if len(result) > 0 && strings.HasSuffix(result[len(result)-1], "\n") {
						skippedSemi = true
						continue
					}
					if len(result) >= 3 && result[len(result)-2] == "\n" && strings.HasSuffix(result[len(result)-3], "\n") {
						skippedSemi = true
						continue
					}
					result = append(result, ";")
					skippedSemi = false
				} else if p.Op == "\n" {
					if len(result) > 0 && result[len(result)-1] == ";" {
						skippedSemi = false
						continue
					}
					if len(result) > 0 && strings.HasSuffix(result[len(result)-1], "\n") {
						result = append(result, func() string {
							if skippedSemi {
								return " "
							} else {
								return "\n"
							}
						}())
						skippedSemi = false
						continue
					}
					result = append(result, "\n")
					skippedSemi = false
				} else if p.Op == "&" {
					if len(result) > 0 && strings.Contains(result[len(result)-1], "<<") && strings.Contains(result[len(result)-1], "\n") {
						last := result[len(result)-1]
						if strings.Contains(last, " |") || strings.HasPrefix(last, "|") {
							result[len(result)-1] = last + " &"
						} else {
							firstNl := strings.Index(last, "\n")
							result[len(result)-1] = _Substring(last, 0, firstNl) + " &" + _Substring(last, firstNl, _runeLen(last))
						}
					} else {
						result = append(result, " &")
					}
				} else if len(result) > 0 && strings.Contains(result[len(result)-1], "<<") && strings.Contains(result[len(result)-1], "\n") {
					last := result[len(result)-1]
					firstNl := strings.Index(last, "\n")
					result[len(result)-1] = _Substring(last, 0, firstNl) + " " + p.Op + " " + _Substring(last, firstNl, _runeLen(last))
				} else {
					result = append(result, " "+p.Op)
				}
			default:
				p = p.(Node)
				if len(result) > 0 && !strings.HasSuffix(result[len(result)-1], " ") && !strings.HasSuffix(result[len(result)-1], "\n") {
					result = append(result, " ")
				}
				formattedCmd := formatCmdsubNode(p, indent, inProcsub, compactRedirects, procsubFirst && cmdCount == 0)
				if len(result) > 0 {
					last := result[len(result)-1]
					if strings.Contains(last, " || \n") || strings.Contains(last, " && \n") {
						formattedCmd = " " + formattedCmd
					}
				}
				if skippedSemi {
					formattedCmd = " " + formattedCmd
					skippedSemi = false
				}
				result = append(result, formattedCmd)
				cmdCount++
			}
		}
		s := strings.Join(result, "")
		if strings.Contains(s, " &\n") && strings.HasSuffix(s, "\n") {
			return s + " "
		}
		for strings.HasSuffix(s, ";") {
			s = substring(s, 0, _runeLen(s)-1)
		}
		if !hasHeredoc {
			for strings.HasSuffix(s, "\n") {
				s = substring(s, 0, _runeLen(s)-1)
			}
		}
		return s
	}
	switch node := node.(type) {
	case *If:
		cond := formatCmdsubNode(node.Condition, indent, false, false, false)
		thenBody := formatCmdsubNode(node.ThenBody, indent+4, false, false, false)
		result := "if " + cond + "; then\n" + innerSp + thenBody + ";"
		if !_isNilInterface(node.ElseBody) {
			elseBody := formatCmdsubNode(node.ElseBody, indent+4, false, false, false)
			result = result + "\n" + sp + "else\n" + innerSp + elseBody + ";"
		}
		result = result + "\n" + sp + "fi"
		return result
	}
	switch node := node.(type) {
	case *While:
		cond := formatCmdsubNode(node.Condition, indent, false, false, false)
		body := formatCmdsubNode(node.Body, indent+4, false, false, false)
		result := "while " + cond + "; do\n" + innerSp + body + ";\n" + sp + "done"
		if len(node.Redirects) > 0 {
			for _, r := range node.Redirects {
				result = result + " " + formatRedirect(r, false, false)
			}
		}
		return result
	}
	switch node := node.(type) {
	case *Until:
		cond := formatCmdsubNode(node.Condition, indent, false, false, false)
		body := formatCmdsubNode(node.Body, indent+4, false, false, false)
		result := "until " + cond + "; do\n" + innerSp + body + ";\n" + sp + "done"
		if len(node.Redirects) > 0 {
			for _, r := range node.Redirects {
				result = result + " " + formatRedirect(r, false, false)
			}
		}
		return result
	}
	switch node := node.(type) {
	case *For:
		var_ := node.Var
		body := formatCmdsubNode(node.Body, indent+4, false, false, false)
		var result string
		if node.Words != nil {
			var wordVals []string = []string{}
			for _, w := range node.Words {
				wordVals = append(wordVals, w.Value)
			}
			words := strings.Join(wordVals, " ")
			if words != "" {
				result = "for " + var_ + " in " + words + ";\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done"
			} else {
				result = "for " + var_ + " in ;\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done"
			}
		} else {
			result = "for " + var_ + " in \"$@\";\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done"
		}
		if len(node.Redirects) > 0 {
			for _, r := range node.Redirects {
				result = result + " " + formatRedirect(r, false, false)
			}
		}
		return result
	}
	switch node := node.(type) {
	case *ForArith:
		body := formatCmdsubNode(node.Body, indent+4, false, false, false)
		result := "for ((" + node.Init + "; " + node.Cond + "; " + node.Incr + "))\ndo\n" + innerSp + body + ";\n" + sp + "done"
		if len(node.Redirects) > 0 {
			for _, r := range node.Redirects {
				result = result + " " + formatRedirect(r, false, false)
			}
		}
		return result
	}
	switch node := node.(type) {
	case *Case:
		word := node.Word.(*Word).Value
		var patterns []string = []string{}
		i := 0
		for i < len(node.Patterns) {
			p := node.Patterns[i]
			pat := strings.ReplaceAll(p.(*CasePattern).Pattern, "|", " | ")
			var body string
			if !_isNilInterface(p.(*CasePattern).Body) {
				body = formatCmdsubNode(p.(*CasePattern).Body, indent+8, false, false, false)
			} else {
				body = ""
			}
			term := p.(*CasePattern).Terminator
			patIndent := repeatStr(" ", indent+8)
			termIndent := repeatStr(" ", indent+4)
			bodyPart := func() string {
				if body != "" {
					return patIndent + body + "\n"
				} else {
					return "\n"
				}
			}()
			if i == 0 {
				patterns = append(patterns, " "+pat+")\n"+bodyPart+termIndent+term)
			} else {
				patterns = append(patterns, pat+")\n"+bodyPart+termIndent+term)
			}
			i++
		}
		patternStr := strings.Join(patterns, "\n"+repeatStr(" ", indent+4))
		redirects := ""
		if len(node.Redirects) > 0 {
			var redirectParts []string = []string{}
			for _, r := range node.Redirects {
				redirectParts = append(redirectParts, formatRedirect(r, false, false))
			}
			redirects = " " + strings.Join(redirectParts, " ")
		}
		return "case " + word + " in" + patternStr + "\n" + sp + "esac" + redirects
	}
	switch node := node.(type) {
	case *Function:
		name := node.Name
		innerBody := func() Node {
			if node.Body.GetKind() == "brace-group" {
				return node.Body.(*BraceGroup).Body
			} else {
				return node.Body
			}
		}()
		body := strings.TrimRight(formatCmdsubNode(innerBody, indent+4, false, false, false), ";")
		return fmt.Sprintf("function %v () \n{ \n%v%v\n}", name, innerSp, body)
	}
	switch node := node.(type) {
	case *Subshell:
		body := formatCmdsubNode(node.Body, indent, inProcsub, compactRedirects, false)
		redirects := ""
		if len(node.Redirects) > 0 {
			var redirectParts []string = []string{}
			for _, r := range node.Redirects {
				redirectParts = append(redirectParts, formatRedirect(r, false, false))
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
	}
	switch node := node.(type) {
	case *BraceGroup:
		body := formatCmdsubNode(node.Body, indent, false, false, false)
		body = strings.TrimRight(body, ";")
		terminator := func() string {
			if strings.HasSuffix(body, " &") {
				return " }"
			} else {
				return "; }"
			}
		}()
		redirects := ""
		if len(node.Redirects) > 0 {
			var redirectParts []string = []string{}
			for _, r := range node.Redirects {
				redirectParts = append(redirectParts, formatRedirect(r, false, false))
			}
			redirects = strings.Join(redirectParts, " ")
		}
		if redirects != "" {
			return "{ " + body + terminator + " " + redirects
		}
		return "{ " + body + terminator
	}
	switch node := node.(type) {
	case *ArithmeticCommand:
		return "((" + node.RawContent + "))"
	}
	switch node := node.(type) {
	case *ConditionalExpr:
		body := formatCondBody(node.Body.(Node))
		return "[[ " + body + " ]]"
	}
	switch node := node.(type) {
	case *Negation:
		if !_isNilInterface(node.Pipeline) {
			return "! " + formatCmdsubNode(node.Pipeline, indent, false, false, false)
		}
		return "! "
	}
	switch node := node.(type) {
	case *Time:
		prefix := func() string {
			if node.Posix {
				return "time -p "
			} else {
				return "time "
			}
		}()
		if !_isNilInterface(node.Pipeline) {
			return prefix + formatCmdsubNode(node.Pipeline, indent, false, false, false)
		}
		return prefix
	}
	return ""
}

func formatRedirect(r Node, compact bool, heredocOpOnly bool) string {
	switch r := r.(type) {
	case *HereDoc:
		var op string
		if r.StripTabs {
			op = "<<-"
		} else {
			op = "<<"
		}
		if r.Fd != nil && *r.Fd != 0 {
			op = _intToStr(*r.Fd) + op
		}
		var delim string
		if r.Quoted {
			delim = "'" + r.Delimiter + "'"
		} else {
			delim = r.Delimiter
		}
		if heredocOpOnly {
			return op + delim
		}
		return op + delim + "\n" + r.Content + r.Delimiter + "\n"
	}
	op := r.(*Redirect).Op
	if op == "1>" {
		op = ">"
	} else if op == "0<" {
		op = "<"
	}
	target := r.(*Redirect).Target.Value
	target = r.(*Redirect).Target.expandAllAnsiCQuotes(target)
	target = r.(*Redirect).Target.stripLocaleStringDollars(target)
	target = r.(*Redirect).Target.formatCommandSubstitutions(target, false)
	if strings.HasPrefix(target, "&") {
		wasInputClose := false
		if target == "&-" && strings.HasSuffix(op, "<") {
			wasInputClose = true
			op = substring(op, 0, _runeLen(op)-1) + ">"
		}
		afterAmp := substring(target, 1, _runeLen(target))
		isLiteralFd := afterAmp == "-" || _runeLen(afterAmp) > 0 && _strIsDigit(string(_runeAt(afterAmp, 0)))
		if isLiteralFd {
			if op == ">" || op == ">&" {
				op = func() string {
					if wasInputClose {
						return "0>"
					} else {
						return "1>"
					}
				}()
			} else if op == "<" || op == "<&" {
				op = "0<"
			}
		} else if op == "1>" {
			op = ">"
		} else if op == "0<" {
			op = "<"
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

func formatHeredocBody(r Node) string {
	return "\n" + r.(*HereDoc).Content + r.(*HereDoc).Delimiter + "\n"
}

func lookaheadForEsac(value string, start int, caseDepth int) bool {
	i := start
	depth := caseDepth
	quote := NewQuoteState()
	for i < _runeLen(value) {
		c := string(_runeAt(value, i))
		if c == "\\" && i+1 < _runeLen(value) && quote.Double {
			i += 2
			continue
		}
		if c == "'" && !quote.Double {
			quote.Single = !quote.Single
			i++
			continue
		}
		if c == "\"" && !quote.Single {
			quote.Double = !quote.Double
			i++
			continue
		}
		if quote.Single || quote.Double {
			i++
			continue
		}
		if startsWithAt(value, i, "case") && isWordBoundary(value, i, 4) {
			depth++
			i += 4
		} else if startsWithAt(value, i, "esac") && isWordBoundary(value, i, 4) {
			depth--
			if depth == 0 {
				return true
			}
			i += 4
		} else if c == "(" {
			i++
		} else if c == ")" {
			if depth > 0 {
				i++
			} else {
				break
			}
		} else {
			i++
		}
	}
	return false
}

func skipBacktick(value string, start int) int {
	i := start + 1
	for i < _runeLen(value) && string(_runeAt(value, i)) != "`" {
		if string(_runeAt(value, i)) == "\\" && i+1 < _runeLen(value) {
			i += 2
		} else {
			i++
		}
	}
	if i < _runeLen(value) {
		i++
	}
	return i
}

func skipSingleQuoted(s string, start int) int {
	i := start
	for i < _runeLen(s) && string(_runeAt(s, i)) != "'" {
		i++
	}
	if i < _runeLen(s) {
		return i + 1
	}
	return i
}

func skipDoubleQuoted(s string, start int) int {
	i := start
	n := _runeLen(s)
	passNext := false
	backq := false
	for i < n {
		c := string(_runeAt(s, i))
		if passNext {
			passNext = false
			i++
			continue
		}
		if c == "\\" {
			passNext = true
			i++
			continue
		}
		if backq {
			if c == "`" {
				backq = false
			}
			i++
			continue
		}
		if c == "`" {
			backq = true
			i++
			continue
		}
		if c == "$" && i+1 < n {
			if string(_runeAt(s, i+1)) == "(" {
				i = findCmdsubEnd(s, i+2)
				continue
			}
			if string(_runeAt(s, i+1)) == "{" {
				i = findBracedParamEnd(s, i+2)
				continue
			}
		}
		if c == "\"" {
			return i + 1
		}
		i++
	}
	return i
}

func isValidArithmeticStart(value string, start int) bool {
	scanParen := 0
	scanI := start + 3
	for scanI < _runeLen(value) {
		scanC := string(_runeAt(value, scanI))
		if isExpansionStart(value, scanI, "$(") {
			scanI = findCmdsubEnd(value, scanI+2)
			continue
		}
		if scanC == "(" {
			scanParen++
		} else if scanC == ")" {
			if scanParen > 0 {
				scanParen--
			} else if scanI+1 < _runeLen(value) && string(_runeAt(value, scanI+1)) == ")" {
				return true
			} else {
				return false
			}
		}
		scanI++
	}
	return false
}

func findFunsubEnd(value string, start int) int {
	depth := 1
	i := start
	quote := NewQuoteState()
	for i < _runeLen(value) && depth > 0 {
		c := string(_runeAt(value, i))
		if c == "\\" && i+1 < _runeLen(value) && !quote.Single {
			i += 2
			continue
		}
		if c == "'" && !quote.Double {
			quote.Single = !quote.Single
			i++
			continue
		}
		if c == "\"" && !quote.Single {
			quote.Double = !quote.Double
			i++
			continue
		}
		if quote.Single || quote.Double {
			i++
			continue
		}
		if c == "{" {
			depth++
		} else if c == "}" {
			depth--
			if depth == 0 {
				return i + 1
			}
		}
		i++
	}
	return _runeLen(value)
}

func findCmdsubEnd(value string, start int) int {
	depth := 1
	i := start
	caseDepth := 0
	inCasePatterns := false
	arithDepth := 0
	arithParenDepth := 0
	for i < _runeLen(value) && depth > 0 {
		c := string(_runeAt(value, i))
		if c == "\\" && i+1 < _runeLen(value) {
			i += 2
			continue
		}
		if c == "'" {
			i = skipSingleQuoted(value, i+1)
			continue
		}
		if c == "\"" {
			i = skipDoubleQuoted(value, i+1)
			continue
		}
		if c == "#" && arithDepth == 0 && (i == start || string(_runeAt(value, i-1)) == " " || string(_runeAt(value, i-1)) == "\t" || string(_runeAt(value, i-1)) == "\n" || string(_runeAt(value, i-1)) == ";" || string(_runeAt(value, i-1)) == "|" || string(_runeAt(value, i-1)) == "&" || string(_runeAt(value, i-1)) == "(" || string(_runeAt(value, i-1)) == ")") {
			for i < _runeLen(value) && string(_runeAt(value, i)) != "\n" {
				i++
			}
			continue
		}
		if startsWithAt(value, i, "<<<") {
			i += 3
			for i < _runeLen(value) && (string(_runeAt(value, i)) == " " || string(_runeAt(value, i)) == "\t") {
				i++
			}
			if i < _runeLen(value) && string(_runeAt(value, i)) == "\"" {
				i++
				for i < _runeLen(value) && string(_runeAt(value, i)) != "\"" {
					if string(_runeAt(value, i)) == "\\" && i+1 < _runeLen(value) {
						i += 2
					} else {
						i++
					}
				}
				if i < _runeLen(value) {
					i++
				}
			} else if i < _runeLen(value) && string(_runeAt(value, i)) == "'" {
				i++
				for i < _runeLen(value) && string(_runeAt(value, i)) != "'" {
					i++
				}
				if i < _runeLen(value) {
					i++
				}
			} else {
				for i < _runeLen(value) && !strings.Contains(" \t\n;|&<>()", string(_runeAt(value, i))) {
					i++
				}
			}
			continue
		}
		if isExpansionStart(value, i, "$((") {
			if isValidArithmeticStart(value, i) {
				arithDepth++
				i += 3
				continue
			}
			j := findCmdsubEnd(value, i+2)
			i = j
			continue
		}
		if arithDepth > 0 && arithParenDepth == 0 && startsWithAt(value, i, "))") {
			arithDepth--
			i += 2
			continue
		}
		if c == "`" {
			i = skipBacktick(value, i)
			continue
		}
		if arithDepth == 0 && startsWithAt(value, i, "<<") {
			i = skipHeredoc(value, i)
			continue
		}
		if startsWithAt(value, i, "case") && isWordBoundary(value, i, 4) {
			caseDepth++
			inCasePatterns = false
			i += 4
			continue
		}
		if caseDepth > 0 && startsWithAt(value, i, "in") && isWordBoundary(value, i, 2) {
			inCasePatterns = true
			i += 2
			continue
		}
		if startsWithAt(value, i, "esac") && isWordBoundary(value, i, 4) {
			if caseDepth > 0 {
				caseDepth--
				inCasePatterns = false
			}
			i += 4
			continue
		}
		if startsWithAt(value, i, ";;") {
			i += 2
			continue
		}
		if c == "(" {
			if !(inCasePatterns && caseDepth > 0) {
				if arithDepth > 0 {
					arithParenDepth++
				} else {
					depth++
				}
			}
		} else if c == ")" {
			if inCasePatterns && caseDepth > 0 {
				if !lookaheadForEsac(value, i+1, caseDepth) {
					depth--
				}
			} else if arithDepth > 0 {
				if arithParenDepth > 0 {
					arithParenDepth--
				}
			} else {
				depth--
			}
		}
		i++
	}
	return i
}

func findBracedParamEnd(value string, start int) int {
	depth := 1
	i := start
	inDouble := false
	dolbraceState := DolbraceStatePARAM
	for i < _runeLen(value) && depth > 0 {
		c := string(_runeAt(value, i))
		if c == "\\" && i+1 < _runeLen(value) {
			i += 2
			continue
		}
		if c == "'" && dolbraceState == DolbraceStateQUOTE && !inDouble {
			i = skipSingleQuoted(value, i+1)
			continue
		}
		if c == "\"" {
			inDouble = !inDouble
			i++
			continue
		}
		if inDouble {
			i++
			continue
		}
		if dolbraceState == DolbraceStatePARAM && strings.Contains("%#^,", c) {
			dolbraceState = DolbraceStateQUOTE
		} else if dolbraceState == DolbraceStatePARAM && strings.Contains(":-=?+/", c) {
			dolbraceState = DolbraceStateWORD
		}
		if c == "[" && dolbraceState == DolbraceStatePARAM && !inDouble {
			end := skipSubscript(value, i, 0)
			if end != -1 {
				i = end
				continue
			}
		}
		if (c == "<" || c == ">") && i+1 < _runeLen(value) && string(_runeAt(value, i+1)) == "(" {
			i = findCmdsubEnd(value, i+2)
			continue
		}
		if c == "{" {
			depth++
		} else if c == "}" {
			depth--
			if depth == 0 {
				return i + 1
			}
		}
		if isExpansionStart(value, i, "$(") {
			i = findCmdsubEnd(value, i+2)
			continue
		}
		if isExpansionStart(value, i, "${") {
			i = findBracedParamEnd(value, i+2)
			continue
		}
		i++
	}
	return i
}

func skipHeredoc(value string, start int) int {
	i := start + 2
	if i < _runeLen(value) && string(_runeAt(value, i)) == "-" {
		i++
	}
	for i < _runeLen(value) && isWhitespaceNoNewline(string(_runeAt(value, i))) {
		i++
	}
	delimStart := i
	var quoteChar interface{}
	var delimiter string
	if i < _runeLen(value) && (string(_runeAt(value, i)) == "\"" || string(_runeAt(value, i)) == "'") {
		quoteChar = string(_runeAt(value, i))
		i++
		delimStart = i
		for i < _runeLen(value) && string(_runeAt(value, i)) != quoteChar {
			i++
		}
		delimiter = substring(value, delimStart, i)
		if i < _runeLen(value) {
			i++
		}
	} else if i < _runeLen(value) && string(_runeAt(value, i)) == "\\" {
		i++
		delimStart = i
		if i < _runeLen(value) {
			i++
		}
		for i < _runeLen(value) && !isMetachar(string(_runeAt(value, i))) {
			i++
		}
		delimiter = substring(value, delimStart, i)
	} else {
		for i < _runeLen(value) && !isMetachar(string(_runeAt(value, i))) {
			i++
		}
		delimiter = substring(value, delimStart, i)
	}
	parenDepth := 0
	quote := NewQuoteState()
	inBacktick := false
	for i < _runeLen(value) && string(_runeAt(value, i)) != "\n" {
		c := string(_runeAt(value, i))
		if c == "\\" && i+1 < _runeLen(value) && (quote.Double || inBacktick) {
			i += 2
			continue
		}
		if c == "'" && !quote.Double && !inBacktick {
			quote.Single = !quote.Single
			i++
			continue
		}
		if c == "\"" && !quote.Single && !inBacktick {
			quote.Double = !quote.Double
			i++
			continue
		}
		if c == "`" && !quote.Single {
			inBacktick = !inBacktick
			i++
			continue
		}
		if quote.Single || quote.Double || inBacktick {
			i++
			continue
		}
		if c == "(" {
			parenDepth++
		} else if c == ")" {
			if parenDepth == 0 {
				break
			}
			parenDepth--
		}
		i++
	}
	if i < _runeLen(value) && string(_runeAt(value, i)) == ")" {
		return i
	}
	if i < _runeLen(value) && string(_runeAt(value, i)) == "\n" {
		i++
	}
	for i < _runeLen(value) {
		lineStart := i
		lineEnd := i
		for lineEnd < _runeLen(value) && string(_runeAt(value, lineEnd)) != "\n" {
			lineEnd++
		}
		line := substring(value, lineStart, lineEnd)
		for lineEnd < _runeLen(value) {
			trailingBs := 0
			for _, j := range Range(_runeLen(line)-1, -1, -1) {
				if string(_runeAt(line, j)) == "\\" {
					trailingBs++
				} else {
					break
				}
			}
			if (trailingBs % 2) == 0 {
				break
			}
			line = _Substring(line, 0, _runeLen(line)-1)
			lineEnd++
			nextLineStart := lineEnd
			for lineEnd < _runeLen(value) && string(_runeAt(value, lineEnd)) != "\n" {
				lineEnd++
			}
			line = line + substring(value, nextLineStart, lineEnd)
		}
		var stripped string
		if start+2 < _runeLen(value) && string(_runeAt(value, start+2)) == "-" {
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
			tabsStripped := _runeLen(line) - _runeLen(stripped)
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

func findHeredocContentEnd(source string, start int, delimiters []struct {
	F0 string
	F1 bool
}) (int, int) {
	if !(len(delimiters) > 0) {
		return start, start
	}
	pos := start
	for pos < _runeLen(source) && string(_runeAt(source, pos)) != "\n" {
		pos++
	}
	if pos >= _runeLen(source) {
		return start, start
	}
	contentStart := pos
	pos++
	for _, item := range delimiters {
		delimiter := item.F0
		stripTabs := item.F1
		for pos < _runeLen(source) {
			lineStart := pos
			lineEnd := pos
			for lineEnd < _runeLen(source) && string(_runeAt(source, lineEnd)) != "\n" {
				lineEnd++
			}
			line := substring(source, lineStart, lineEnd)
			for lineEnd < _runeLen(source) {
				trailingBs := 0
				for _, j := range Range(_runeLen(line)-1, -1, -1) {
					if string(_runeAt(line, j)) == "\\" {
						trailingBs++
					} else {
						break
					}
				}
				if (trailingBs % 2) == 0 {
					break
				}
				line = _Substring(line, 0, _runeLen(line)-1)
				lineEnd++
				nextLineStart := lineEnd
				for lineEnd < _runeLen(source) && string(_runeAt(source, lineEnd)) != "\n" {
					lineEnd++
				}
				line = line + substring(source, nextLineStart, lineEnd)
			}
			var lineStripped string
			if stripTabs {
				lineStripped = strings.TrimLeft(line, "\t")
			} else {
				lineStripped = line
			}
			if lineStripped == delimiter {
				pos = func() int {
					if lineEnd < _runeLen(source) {
						return lineEnd + 1
					} else {
						return lineEnd
					}
				}()
				break
			}
			if strings.HasPrefix(lineStripped, delimiter) && _runeLen(lineStripped) > _runeLen(delimiter) {
				tabsStripped := _runeLen(line) - _runeLen(lineStripped)
				pos = lineStart + tabsStripped + _runeLen(delimiter)
				break
			}
			pos = func() int {
				if lineEnd < _runeLen(source) {
					return lineEnd + 1
				} else {
					return lineEnd
				}
			}()
		}
	}
	return contentStart, pos
}

func isWordBoundary(s string, pos int, wordLen int) bool {
	if pos > 0 {
		prev := string(_runeAt(s, pos-1))
		if _strIsAlnum(prev) || prev == "_" {
			return false
		}
		if strings.Contains("{}!", prev) {
			return false
		}
	}
	end := pos + wordLen
	if end < _runeLen(s) && (_strIsAlnum(string(_runeAt(s, end))) || string(_runeAt(s, end)) == "_") {
		return false
	}
	return true
}

func isQuote(c string) bool {
	return c == "'" || c == "\""
}

func collapseWhitespace(s string) string {
	result := []string{}
	prevWasWs := false
	for _, c := range s {
		if c == ' ' || c == '\t' {
			if !prevWasWs {
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

func countTrailingBackslashes(s string) int {
	count := 0
	for _, i := range Range(_runeLen(s)-1, -1, -1) {
		if string(_runeAt(s, i)) == "\\" {
			count++
		} else {
			break
		}
	}
	return count
}

func normalizeHeredocDelimiter(delimiter string) string {
	result := []string{}
	i := 0
	for i < _runeLen(delimiter) {
		var depth int
		var inner []string
		var innerStr string
		if i+1 < _runeLen(delimiter) && _Substring(delimiter, i, i+2) == "$(" {
			result = append(result, "$(")
			i += 2
			depth = 1
			inner = []string{}
			for i < _runeLen(delimiter) && depth > 0 {
				if string(_runeAt(delimiter, i)) == "(" {
					depth++
					inner = append(inner, string(_runeAt(delimiter, i)))
				} else if string(_runeAt(delimiter, i)) == ")" {
					depth--
					if depth == 0 {
						innerStr = strings.Join(inner, "")
						innerStr = collapseWhitespace(innerStr)
						result = append(result, innerStr)
						result = append(result, ")")
					} else {
						inner = append(inner, string(_runeAt(delimiter, i)))
					}
				} else {
					inner = append(inner, string(_runeAt(delimiter, i)))
				}
				i++
			}
		} else if i+1 < _runeLen(delimiter) && _Substring(delimiter, i, i+2) == "${" {
			result = append(result, "${")
			i += 2
			depth = 1
			inner = []string{}
			for i < _runeLen(delimiter) && depth > 0 {
				if string(_runeAt(delimiter, i)) == "{" {
					depth++
					inner = append(inner, string(_runeAt(delimiter, i)))
				} else if string(_runeAt(delimiter, i)) == "}" {
					depth--
					if depth == 0 {
						innerStr = strings.Join(inner, "")
						innerStr = collapseWhitespace(innerStr)
						result = append(result, innerStr)
						result = append(result, "}")
					} else {
						inner = append(inner, string(_runeAt(delimiter, i)))
					}
				} else {
					inner = append(inner, string(_runeAt(delimiter, i)))
				}
				i++
			}
		} else if i+1 < _runeLen(delimiter) && strings.Contains("<>", string(_runeAt(delimiter, i))) && string(_runeAt(delimiter, i+1)) == "(" {
			result = append(result, string(_runeAt(delimiter, i)))
			result = append(result, "(")
			i += 2
			depth = 1
			inner = []string{}
			for i < _runeLen(delimiter) && depth > 0 {
				if string(_runeAt(delimiter, i)) == "(" {
					depth++
					inner = append(inner, string(_runeAt(delimiter, i)))
				} else if string(_runeAt(delimiter, i)) == ")" {
					depth--
					if depth == 0 {
						innerStr = strings.Join(inner, "")
						innerStr = collapseWhitespace(innerStr)
						result = append(result, innerStr)
						result = append(result, ")")
					} else {
						inner = append(inner, string(_runeAt(delimiter, i)))
					}
				} else {
					inner = append(inner, string(_runeAt(delimiter, i)))
				}
				i++
			}
		} else {
			result = append(result, string(_runeAt(delimiter, i)))
			i++
		}
	}
	return strings.Join(result, "")
}

func isMetachar(c string) bool {
	return c == " " || c == "\t" || c == "\n" || c == "|" || c == "&" || c == ";" || c == "(" || c == ")" || c == "<" || c == ">"
}

func isFunsubChar(c string) bool {
	return c == " " || c == "\t" || c == "\n" || c == "|"
}

func isExtglobPrefix(c string) bool {
	return c == "@" || c == "?" || c == "*" || c == "+" || c == "!"
}

func isRedirectChar(c string) bool {
	return c == "<" || c == ">"
}

func isSpecialParam(c string) bool {
	return c == "?" || c == "$" || c == "!" || c == "#" || c == "@" || c == "*" || c == "-" || c == "&"
}

func isSpecialParamUnbraced(c string) bool {
	return c == "?" || c == "$" || c == "!" || c == "#" || c == "@" || c == "*" || c == "-"
}

func isDigit(c string) bool {
	return c >= "0" && c <= "9"
}

func isSemicolonOrNewline(c string) bool {
	return c == ";" || c == "\n"
}

func isWordEndContext(c string) bool {
	return c == " " || c == "\t" || c == "\n" || c == ";" || c == "|" || c == "&" || c == "<" || c == ">" || c == "(" || c == ")"
}

func skipMatchedPair(s string, start int, open string, close string, flags int) int {
	n := _runeLen(s)
	var i int
	if (flags & SMPPASTOPEN) != 0 {
		i = start
	} else {
		if start >= n || string(_runeAt(s, start)) != open {
			return -1
		}
		i = start + 1
	}
	depth := 1
	passNext := false
	backq := false
	for i < n && depth > 0 {
		c := string(_runeAt(s, i))
		if passNext {
			passNext = false
			i++
			continue
		}
		literal := (flags & SMPLITERAL)
		if !(literal != 0) && c == "\\" {
			passNext = true
			i++
			continue
		}
		if backq {
			if c == "`" {
				backq = false
			}
			i++
			continue
		}
		if !(literal != 0) && c == "`" {
			backq = true
			i++
			continue
		}
		if !(literal != 0) && c == "'" {
			i = skipSingleQuoted(s, i+1)
			continue
		}
		if !(literal != 0) && c == "\"" {
			i = skipDoubleQuoted(s, i+1)
			continue
		}
		if !(literal != 0) && isExpansionStart(s, i, "$(") {
			i = findCmdsubEnd(s, i+2)
			continue
		}
		if !(literal != 0) && isExpansionStart(s, i, "${") {
			i = findBracedParamEnd(s, i+2)
			continue
		}
		if !(literal != 0) && c == open {
			depth++
		} else if c == close {
			depth--
		}
		i++
	}
	if depth == 0 {
		return i
	}
	return -1
}

func skipSubscript(s string, start int, flags int) int {
	return skipMatchedPair(s, start, "[", "]", flags)
}

func assignment(s string, flags int) int {
	if !(s != "") {
		return -1
	}
	if !(_strIsAlpha(string(_runeAt(s, 0))) || string(_runeAt(s, 0)) == "_") {
		return -1
	}
	i := 1
	for i < _runeLen(s) {
		c := string(_runeAt(s, i))
		if c == "=" {
			return i
		}
		if c == "[" {
			subFlags := func() int {
				if (flags & 2) != 0 {
					return SMPLITERAL
				} else {
					return 0
				}
			}()
			end := skipSubscript(s, i, subFlags)
			if end == -1 {
				return -1
			}
			i = end
			if i < _runeLen(s) && string(_runeAt(s, i)) == "+" {
				i++
			}
			if i < _runeLen(s) && string(_runeAt(s, i)) == "=" {
				return i
			}
			return -1
		}
		if c == "+" {
			if i+1 < _runeLen(s) && string(_runeAt(s, i+1)) == "=" {
				return i + 1
			}
			return -1
		}
		if !(_strIsAlnum(c) || c == "_") {
			return -1
		}
		i++
	}
	return -1
}

func isArrayAssignmentPrefix(chars []string) bool {
	if !(len(chars) > 0) {
		return false
	}
	if !(_strIsAlpha(chars[0]) || chars[0] == "_") {
		return false
	}
	s := strings.Join(chars, "")
	i := 1
	for i < _runeLen(s) && (_strIsAlnum(string(_runeAt(s, i))) || string(_runeAt(s, i)) == "_") {
		i++
	}
	for i < _runeLen(s) {
		if string(_runeAt(s, i)) != "[" {
			return false
		}
		end := skipSubscript(s, i, SMPLITERAL)
		if end == -1 {
			return false
		}
		i = end
	}
	return true
}

func isSpecialParamOrDigit(c string) bool {
	return isSpecialParam(c) || isDigit(c)
}

func isParamExpansionOp(c string) bool {
	return c == ":" || c == "-" || c == "=" || c == "+" || c == "?" || c == "#" || c == "%" || c == "/" || c == "^" || c == "," || c == "@" || c == "*" || c == "["
}

func isSimpleParamOp(c string) bool {
	return c == "-" || c == "=" || c == "?" || c == "+"
}

func isEscapeCharInBacktick(c string) bool {
	return c == "$" || c == "`" || c == "\\"
}

func isNegationBoundary(c string) bool {
	return isWhitespace(c) || c == ";" || c == "|" || c == ")" || c == "&" || c == ">" || c == "<"
}

func isBackslashEscaped(value string, idx int) bool {
	bsCount := 0
	j := idx - 1
	for j >= 0 && string(_runeAt(value, j)) == "\\" {
		bsCount++
		j--
	}
	return (bsCount % 2) == 1
}

func isDollarDollarParen(value string, idx int) bool {
	dollarCount := 0
	j := idx - 1
	for j >= 0 && string(_runeAt(value, j)) == "$" {
		dollarCount++
		j--
	}
	return (dollarCount % 2) == 1
}

func isParen(c string) bool {
	return c == "(" || c == ")"
}

func isCaretOrBang(c string) bool {
	return c == "!" || c == "^"
}

func isAtOrStar(c string) bool {
	return c == "@" || c == "*"
}

func isDigitOrDash(c string) bool {
	return isDigit(c) || c == "-"
}

func isNewlineOrRightParen(c string) bool {
	return c == "\n" || c == ")"
}

func isSemicolonNewlineBrace(c string) bool {
	return c == ";" || c == "\n" || c == "{"
}

func looksLikeAssignment(s string) bool {
	return assignment(s, 0) != -1
}

func isValidIdentifier(name string) bool {
	if !(name != "") {
		return false
	}
	if !(_strIsAlpha(string(_runeAt(name, 0))) || string(_runeAt(name, 0)) == "_") {
		return false
	}
	for _, c := range _Substring(name, 1, _runeLen(name)) {
		if !(_strIsAlnum(string(c)) || c == '_') {
			return false
		}
	}
	return true
}

func Parse(source string, extglob bool) []Node {
	parser := NewParser(source, false, extglob)
	return parser.Parse()
}

func NewParseError(message string, pos int, line int) *ParseError {
	self := &ParseError{}
	self.Message = message
	self.Pos = pos
	self.Line = line
	return self
}

func NewMatchedPairError(message string, pos int, line int) *MatchedPairError {
	return &MatchedPairError{ParseError{Message: message, Pos: pos, Line: line}}
}

func NewQuoteState() *QuoteState {
	self := &QuoteState{}
	self.Single = false
	self.Double = false
	self.stack = []struct {
		F0 bool
		F1 bool
	}{}
	return self
}

func NewParseContext(kind int) *ParseContext {
	self := &ParseContext{}
	self.Kind = kind
	self.ParenDepth = 0
	self.BraceDepth = 0
	self.BracketDepth = 0
	self.CaseDepth = 0
	self.ArithDepth = 0
	self.ArithParenDepth = 0
	self.Quote = NewQuoteState()
	return self
}

func NewContextStack() *ContextStack {
	self := &ContextStack{}
	self.stack = []*ParseContext{NewParseContext(0)}
	return self
}

func NewLexer(source string, extglob bool) *Lexer {
	self := &Lexer{}
	self.Source = source
	self.Pos = 0
	self.Length = _runeLen(source)
	self.Quote = NewQuoteState()
	self.tokenCache = nil
	self.parserState = ParserStateFlagsNONE
	self.dolbraceState = DolbraceStateNONE
	self.pendingHeredocs = []Node{}
	self.extglob = extglob
	self.parser = nil
	self.eofToken = ""
	self.lastReadToken = nil
	self.wordContext = WORDCTXNORMAL
	self.atCommandStart = false
	self.inArrayLiteral = false
	self.inAssignBuiltin = false
	self.postReadPos = 0
	self.cachedWordContext = WORDCTXNORMAL
	self.cachedAtCommandStart = false
	self.cachedInArrayLiteral = false
	self.cachedInAssignBuiltin = false
	return self
}

func NewParser(source string, inProcessSub bool, extglob bool) *Parser {
	self := &Parser{}
	self.Source = source
	self.Pos = 0
	self.Length = _runeLen(source)
	self.pendingHeredocs = []*HereDoc{}
	self.cmdsubHeredocEnd = -1
	self.sawNewlineInSingleQuote = false
	self.inProcessSub = inProcessSub
	self.extglob = extglob
	self.ctx = NewContextStack()
	self.lexer = NewLexer(source, extglob)
	self.lexer.parser = self
	self.tokenHistory = []*Token{nil, nil, nil, nil}
	self.parserState = ParserStateFlagsNONE
	self.dolbraceState = DolbraceStateNONE
	self.eofToken = ""
	self.wordContext = WORDCTXNORMAL
	self.atCommandStart = false
	self.inArrayLiteral = false
	self.inAssignBuiltin = false
	self.arithSrc = ""
	self.arithPos = 0
	self.arithLen = 0
	return self
}
