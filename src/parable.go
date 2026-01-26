package parable

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
	TokentypeEof                  = 0
	TokentypeWord                 = 1
	TokentypeNewline              = 2
	TokentypeSemi                 = 10
	TokentypePipe                 = 11
	TokentypeAmp                  = 12
	TokentypeLparen               = 13
	TokentypeRparen               = 14
	TokentypeLbrace               = 15
	TokentypeRbrace               = 16
	TokentypeLess                 = 17
	TokentypeGreater              = 18
	TokentypeAndAnd               = 30
	TokentypeOrOr                 = 31
	TokentypeSemiSemi             = 32
	TokentypeSemiAmp              = 33
	TokentypeSemiSemiAmp          = 34
	TokentypeLessLess             = 35
	TokentypeGreaterGreater       = 36
	TokentypeLessAmp              = 37
	TokentypeGreaterAmp           = 38
	TokentypeLessGreater          = 39
	TokentypeGreaterPipe          = 40
	TokentypeLessLessMinus        = 41
	TokentypeLessLessLess         = 42
	TokentypeAmpGreater           = 43
	TokentypeAmpGreaterGreater    = 44
	TokentypePipeAmp              = 45
	TokentypeIf                   = 50
	TokentypeThen                 = 51
	TokentypeElse                 = 52
	TokentypeElif                 = 53
	TokentypeFi                   = 54
	TokentypeCase                 = 55
	TokentypeEsac                 = 56
	TokentypeFor                  = 57
	TokentypeWhile                = 58
	TokentypeUntil                = 59
	TokentypeDo                   = 60
	TokentypeDone                 = 61
	TokentypeIn                   = 62
	TokentypeFunction             = 63
	TokentypeSelect               = 64
	TokentypeCoproc               = 65
	TokentypeTime                 = 66
	TokentypeBang                 = 67
	TokentypeLbracketLbracket     = 68
	TokentypeRbracketRbracket     = 69
	TokentypeAssignmentWord       = 80
	TokentypeNumber               = 81
	ParserstateflagsNone          = 0
	ParserstateflagsPstCasepat    = 1
	ParserstateflagsPstCmdsubst   = 2
	ParserstateflagsPstCasestmt   = 4
	ParserstateflagsPstCondexpr   = 8
	ParserstateflagsPstCompassign = 16
	ParserstateflagsPstArith      = 32
	ParserstateflagsPstHeredoc    = 64
	ParserstateflagsPstRegexp     = 128
	ParserstateflagsPstExtpat     = 256
	ParserstateflagsPstSubshell   = 512
	ParserstateflagsPstRedirlist  = 1024
	ParserstateflagsPstComment    = 2048
	ParserstateflagsPstEoftoken   = 4096
	DolbracestateNone             = 0
	DolbracestateParam            = 1
	DolbracestateOp               = 2
	DolbracestateWord             = 4
	DolbracestateQuote            = 64
	DolbracestateQuote2           = 128
	MatchedpairflagsNone          = 0
	MatchedpairflagsDquote        = 1
	MatchedpairflagsDolbrace      = 2
	MatchedpairflagsCommand       = 4
	MatchedpairflagsArith         = 8
	MatchedpairflagsAllowesc      = 16
	MatchedpairflagsExtglob       = 32
	MatchedpairflagsFirstclose    = 64
	MatchedpairflagsArraysub      = 128
	MatchedpairflagsBackquote     = 256
	ParsecontextNormal            = 0
	ParsecontextCommandSub        = 1
	ParsecontextArithmetic        = 2
	ParsecontextCasePattern       = 3
	ParsecontextBraceExpansion    = 4
	smpLiteral                    = 1
	smpPastOpen                   = 2
	WordCtxNormal                 = 0
	WordCtxCond                   = 1
	WordCtxRegex                  = 2
)

type ParseError struct {
	Message string
	Pos     *int
	Line    *int
}

func (s *ParseError) formatMessage() string {
	if s.Line != nil && s.Pos != nil {
		return fmt.Sprintf("Parse error at line %v, position %v: %v", s.Line, s.Pos, s.Message)
	} else if s.Pos != nil {
		return fmt.Sprintf("Parse error at position %v: %v", s.Pos, s.Message)
	}
	return fmt.Sprintf("Parse error: %v", s.Message)
}

type MatchedPairError struct {
}

type TokenType struct {
}

type Token struct {
	Type  int
	Value string
	Pos   int
	Parts []Node
	Word  *Node
}

func (s *Token) repr() string {
	if s.Word != nil {
		return fmt.Sprintf("Token(%v, %v, %v, word=%v)", s.Type, s.Value, s.Pos, s.Word)
	}
	if s.Parts != nil {
		return fmt.Sprintf("Token(%v, %v, %v, parts=%v)", s.Type, s.Value, s.Pos, len(s.Parts))
	}
	return fmt.Sprintf("Token(%v, %v, %v)", s.Type, s.Value, s.Pos)
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
	EofToken        *string
}

type QuoteState struct {
	Single bool
	Double bool
	stack  []quoteStackEntry
}

func (s *QuoteState) Push() {
	s.stack = append(s.stack, struct{ Single, Double bool }{s.Single, s.Double})
	s.Single = false
	s.Double = false
}

func (s *QuoteState) Pop() {
	if s.stack != nil {
		{
			var entry quoteStackEntry = s.stack[(len(s.stack) - 1)]
			s.stack = s.stack[:(len(s.stack) - 1)]
			s.Single = entry.Single
			s.Double = entry.Double
		}
	}
}

func (s *QuoteState) InQuotes() bool {
	return (s.Single || s.Double)
}

func (s *QuoteState) Copy() *QuoteState {
	qs := &QuoteState{}
	qs.Single = s.Single
	qs.Double = s.Double
	qs.stack = append(s.stack[:0:0], s.stack...)
	return qs
}

func (s *QuoteState) OuterDouble() bool {
	if len(s.stack) == 0 {
		return false
	}
	return s.stack[(len(s.stack) - 1)].Double
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

func (s *ParseContext) Copy() *ParseContext {
	ctx := &ParseContext{Kind: s.Kind}
	ctx.ParenDepth = s.ParenDepth
	ctx.BraceDepth = s.BraceDepth
	ctx.BracketDepth = s.BracketDepth
	ctx.CaseDepth = s.CaseDepth
	ctx.ArithDepth = s.ArithDepth
	ctx.ArithParenDepth = s.ArithParenDepth
	ctx.Quote = s.Quote.Copy()
	return ctx
}

type ContextStack struct {
	stack []*ParseContext
}

func (s *ContextStack) GetCurrent() *ParseContext {
	return s.stack[(len(s.stack) - 1)]
}

func (s *ContextStack) Push(kind int) {
	s.stack = append(s.stack, &ParseContext{Kind: kind})
}

func (s *ContextStack) Pop() *ParseContext {
	if len(s.stack) > 1 {
		return s.stack[len(s.stack)-1]
	}
	return s.stack[0]
}

func (s *ContextStack) CopyStack() []*ParseContext {
	result := []*ParseContext{}
	for _, ctx := range s.stack {
		result = append(result, ctx.Copy())
	}
	return result
}

func (s *ContextStack) RestoreFrom(savedStack []*ParseContext) {
	result := []*ParseContext{}
	for _, ctx := range savedStack {
		result = append(result, ctx.Copy())
	}
	s.stack = result
}

type Lexer struct {
	ReservedWords         map[string]int
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
	eofToken              *string
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

func (s *Lexer) Peek() string {
	if s.Pos >= s.Length {
		return ""
	}
	return string(s.Source[s.Pos])
}

func (s *Lexer) Advance() string {
	if s.Pos >= s.Length {
		return ""
	}
	c := string(s.Source[s.Pos])
	s.Pos += 1
	return c
}

func (s *Lexer) AtEnd() bool {
	return (s.Pos >= s.Length)
}

func (s *Lexer) Lookahead(n int) string {
	return substring(s.Source, s.Pos, (s.Pos + n))
}

func (s *Lexer) IsMetachar(c string) bool {
	return strings.Contains("|&;()<> \t\n", c)
}

func (s *Lexer) readOperator() *Token {
	start := s.Pos
	c := s.Peek()
	if c == "" {
		return nil
	}
	two := s.Lookahead(2)
	three := s.Lookahead(3)
	if three == ";;&" {
		s.Pos += 3
		return &Token{Type: TokentypeSemiSemiAmp, Value: three, Pos: start}
	}
	if three == "<<-" {
		s.Pos += 3
		return &Token{Type: TokentypeLessLessMinus, Value: three, Pos: start}
	}
	if three == "<<<" {
		s.Pos += 3
		return &Token{Type: TokentypeLessLessLess, Value: three, Pos: start}
	}
	if three == "&>>" {
		s.Pos += 3
		return &Token{Type: TokentypeAmpGreaterGreater, Value: three, Pos: start}
	}
	if two == "&&" {
		s.Pos += 2
		return &Token{Type: TokentypeAndAnd, Value: two, Pos: start}
	}
	if two == "||" {
		s.Pos += 2
		return &Token{Type: TokentypeOrOr, Value: two, Pos: start}
	}
	if two == ";;" {
		s.Pos += 2
		return &Token{Type: TokentypeSemiSemi, Value: two, Pos: start}
	}
	if two == ";&" {
		s.Pos += 2
		return &Token{Type: TokentypeSemiAmp, Value: two, Pos: start}
	}
	if two == "<<" {
		s.Pos += 2
		return &Token{Type: TokentypeLessLess, Value: two, Pos: start}
	}
	if two == ">>" {
		s.Pos += 2
		return &Token{Type: TokentypeGreaterGreater, Value: two, Pos: start}
	}
	if two == "<&" {
		s.Pos += 2
		return &Token{Type: TokentypeLessAmp, Value: two, Pos: start}
	}
	if two == ">&" {
		s.Pos += 2
		return &Token{Type: TokentypeGreaterAmp, Value: two, Pos: start}
	}
	if two == "<>" {
		s.Pos += 2
		return &Token{Type: TokentypeLessGreater, Value: two, Pos: start}
	}
	if two == ">|" {
		s.Pos += 2
		return &Token{Type: TokentypeGreaterPipe, Value: two, Pos: start}
	}
	if two == "&>" {
		s.Pos += 2
		return &Token{Type: TokentypeAmpGreater, Value: two, Pos: start}
	}
	if two == "|&" {
		s.Pos += 2
		return &Token{Type: TokentypePipeAmp, Value: two, Pos: start}
	}
	if c == ";" {
		s.Pos += 1
		return &Token{Type: TokentypeSemi, Value: c, Pos: start}
	}
	if c == "|" {
		s.Pos += 1
		return &Token{Type: TokentypePipe, Value: c, Pos: start}
	}
	if c == "&" {
		s.Pos += 1
		return &Token{Type: TokentypeAmp, Value: c, Pos: start}
	}
	if c == "(" {
		if s.wordContext == WordCtxRegex {
			return nil
		}
		s.Pos += 1
		return &Token{Type: TokentypeLparen, Value: c, Pos: start}
	}
	if c == ")" {
		if s.wordContext == WordCtxRegex {
			return nil
		}
		s.Pos += 1
		return &Token{Type: TokentypeRparen, Value: c, Pos: start}
	}
	if c == "<" {
		if ((s.Pos + 1) < s.Length) && (string(s.Source[(s.Pos+1)]) == "(") {
			return nil
		}
		s.Pos += 1
		return &Token{Type: TokentypeLess, Value: c, Pos: start}
	}
	if c == ">" {
		if ((s.Pos + 1) < s.Length) && (string(s.Source[(s.Pos+1)]) == "(") {
			return nil
		}
		s.Pos += 1
		return &Token{Type: TokentypeGreater, Value: c, Pos: start}
	}
	if c == "\n" {
		s.Pos += 1
		return &Token{Type: TokentypeNewline, Value: c, Pos: start}
	}
	return nil
}

func (s *Lexer) SkipBlanks() {
	for s.Pos < s.Length {
		c := string(s.Source[s.Pos])
		if (c != " ") && (c != "\t") {
			break
		}
		s.Pos += 1
	}
}

func (s *Lexer) skipComment() bool {
	if s.Pos >= s.Length {
		return false
	}
	if string(s.Source[s.Pos]) != "#" {
		return false
	}
	if s.Quote.InQuotes() {
		return false
	}
	if s.Pos > 0 {
		prev := string(s.Source[(s.Pos - 1)])
		if !strings.Contains(" \t\n;|&(){}", prev) {
			return false
		}
	}
	for (s.Pos < s.Length) && (string(s.Source[s.Pos]) != "\n") {
		s.Pos += 1
	}
	return true
}

func (s *Lexer) readSingleQuote(start int) (string, bool) {
	chars := []string{"'"}
	sawNewline := false
	for s.Pos < s.Length {
		c := string(s.Source[s.Pos])
		if c == "\n" {
			sawNewline = true
		}
		chars = append(chars, c)
		s.Pos += 1
		if c == "'" {
			return strings.Join(chars, ""), sawNewline
		}
	}
	panic("Unterminated single quote")
}

func (s *Lexer) isWordTerminator(ctx int, ch string, bracketDepth int, parenDepth int) bool {
	if ctx == WordCtxRegex {
		if ((ch == "]") && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "]") {
			return true
		}
		if ((ch == "&") && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "&") {
			return true
		}
		if (ch == ")") && (parenDepth == 0) {
			return true
		}
		return (isWhitespace(ch) && (parenDepth == 0))
	}
	if ctx == WordCtxCond {
		if ((ch == "]") && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "]") {
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
		if isRedirectChar(ch) && !(((s.Pos + 1) < s.Length) && (string(s.Source[(s.Pos+1)]) == "(")) {
			return true
		}
		return isWhitespace(ch)
	}
	if ((((s.parserState & ParserstateflagsPstEoftoken) != 0) && s.eofToken != nil) && (ch == *s.eofToken)) && (bracketDepth == 0) {
		return true
	}
	if (isRedirectChar(ch) && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "(") {
		return false
	}
	return (isMetachar(ch) && (bracketDepth == 0))
}

func (s *Lexer) readBracketExpression(chars *[]string, parts *[]Node, forRegex bool, parenDepth int) bool {
	if forRegex {
		scan := (s.Pos + 1)
		if (scan < s.Length) && (string(s.Source[scan]) == "^") {
			scan += 1
		}
		if (scan < s.Length) && (string(s.Source[scan]) == "]") {
			scan += 1
		}
		bracketWillClose := false
		for scan < s.Length {
			sc := string(s.Source[scan])
			if ((sc == "]") && ((scan + 1) < s.Length)) && (string(s.Source[(scan+1)]) == "]") {
				break
			}
			if (sc == ")") && (parenDepth > 0) {
				break
			}
			if ((sc == "&") && ((scan + 1) < s.Length)) && (string(s.Source[(scan+1)]) == "&") {
				break
			}
			if sc == "]" {
				bracketWillClose = true
				break
			}
			if ((sc == "[") && ((scan + 1) < s.Length)) && (string(s.Source[(scan+1)]) == ":") {
				scan += 2
				for (scan < s.Length) && !(((string(s.Source[scan]) == ":") && ((scan + 1) < s.Length)) && (string(s.Source[(scan+1)]) == "]")) {
					scan += 1
				}
				if scan < s.Length {
					scan += 2
				}
				continue
			}
			scan += 1
		}
		if !bracketWillClose {
			return false
		}
	} else {
		if (s.Pos + 1) >= s.Length {
			return false
		}
		nextCh := string(s.Source[(s.Pos + 1)])
		if (isWhitespaceNoNewline(nextCh) || (nextCh == "&")) || (nextCh == "|") {
			return false
		}
	}
	*chars = append(*chars, s.Advance())
	if !s.AtEnd() && (s.Peek() == "^") {
		*chars = append(*chars, s.Advance())
	}
	if !s.AtEnd() && (s.Peek() == "]") {
		*chars = append(*chars, s.Advance())
	}
	for !s.AtEnd() {
		c := s.Peek()
		if c == "]" {
			*chars = append(*chars, s.Advance())
			break
		}
		if ((c == "[") && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == ":") {
			*chars = append(*chars, s.Advance())
			*chars = append(*chars, s.Advance())
			for !s.AtEnd() && !(((s.Peek() == ":") && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "]")) {
				*chars = append(*chars, s.Advance())
			}
			if !s.AtEnd() {
				*chars = append(*chars, s.Advance())
				*chars = append(*chars, s.Advance())
			}
		} else if ((!forRegex && (c == "[")) && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "=") {
			*chars = append(*chars, s.Advance())
			*chars = append(*chars, s.Advance())
			for !s.AtEnd() && !(((s.Peek() == "=") && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "]")) {
				*chars = append(*chars, s.Advance())
			}
			if !s.AtEnd() {
				*chars = append(*chars, s.Advance())
				*chars = append(*chars, s.Advance())
			}
		} else if ((!forRegex && (c == "[")) && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == ".") {
			*chars = append(*chars, s.Advance())
			*chars = append(*chars, s.Advance())
			for !s.AtEnd() && !(((s.Peek() == ".") && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "]")) {
				*chars = append(*chars, s.Advance())
			}
			if !s.AtEnd() {
				*chars = append(*chars, s.Advance())
				*chars = append(*chars, s.Advance())
			}
		} else if forRegex && (c == "$") {
			s.syncToParser()
			if !s.parser.parseDollarExpansion(chars, parts, false) {
				s.syncFromParser()
				*chars = append(*chars, s.Advance())
			} else {
				s.syncFromParser()
			}
		} else {
			*chars = append(*chars, s.Advance())
		}
	}
	return true
}

func (s *Lexer) parseMatchedPair(openChar string, closeChar string, flags int, initialWasDollar bool) string {
	var nested string
	var wasDollar bool
	var wasGtlt bool
	var cmdNode *Node
	var cmdText string
	var arithNode *Node
	var arithText string
	start := s.Pos
	count := 1
	var chars []string = []string{}
	passNext := false
	wasDollar = initialWasDollar
	wasGtlt = false
	for count > 0 {
		if s.AtEnd() {
			panic(fmt.Sprintf("unexpected EOF while looking for matching `%v'", closeChar))
		}
		ch := s.Advance()
		if ((flags & MatchedpairflagsDolbrace) != 0) && (s.dolbraceState == DolbracestateOp) {
			if !strings.Contains("#%^,~:-=?+/", ch) {
				s.dolbraceState = DolbracestateWord
			}
		}
		if passNext {
			passNext = false
			chars = append(chars, ch)
			wasDollar = (ch == "$")
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
			if (ch == "\\") && ((flags & MatchedpairflagsAllowesc) != 0) {
				passNext = true
			}
			chars = append(chars, ch)
			wasDollar = false
			wasGtlt = false
			continue
		}
		if ch == "\\" {
			if !s.AtEnd() && (s.Peek() == "\n") {
				s.Advance()
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
		if (ch == openChar) && (openChar != closeChar) {
			if !(((flags & MatchedpairflagsDolbrace) != 0) && (openChar == "{")) {
				count += 1
			}
			chars = append(chars, ch)
			wasDollar = false
			wasGtlt = strings.Contains("<>", ch)
			continue
		}
		if strings.Contains("'\"`", ch) && (openChar != closeChar) {
			if ch == "'" {
				chars = append(chars, ch)
				quoteFlags := func() int {
					if wasDollar {
						return (flags | MatchedpairflagsAllowesc)
					} else {
						return flags
					}
				}()
				nested = s.parseMatchedPair("'", "'", quoteFlags, false)
				chars = append(chars, nested)
				chars = append(chars, "'")
				wasDollar = false
				wasGtlt = false
				continue
			} else if ch == "\"" {
				chars = append(chars, ch)
				nested = s.parseMatchedPair("\"", "\"", (flags | MatchedpairflagsDquote), false)
				chars = append(chars, nested)
				chars = append(chars, "\"")
				wasDollar = false
				wasGtlt = false
				continue
			} else if ch == "`" {
				chars = append(chars, ch)
				nested = s.parseMatchedPair("`", "`", flags, false)
				chars = append(chars, nested)
				chars = append(chars, "`")
				wasDollar = false
				wasGtlt = false
				continue
			}
		}
		if ((ch == "$") && !s.AtEnd()) && !((flags & MatchedpairflagsExtglob) != 0) {
			nextCh := s.Peek()
			if wasDollar {
				chars = append(chars, ch)
				wasDollar = false
				wasGtlt = false
				continue
			}
			if nextCh == "{" {
				if (flags & MatchedpairflagsArith) != 0 {
					afterBracePos := (s.Pos + 1)
					if (afterBracePos >= s.Length) || !isFunsubChar(string(s.Source[afterBracePos])) {
						chars = append(chars, ch)
						wasDollar = true
						wasGtlt = false
						continue
					}
				}
				s.Pos -= 1
				s.syncToParser()
				inDquote := ((flags & MatchedpairflagsDquote) != 0)
				paramNode, paramText := s.parser.parseParamExpansion(inDquote)
				s.syncFromParser()
				if paramNode != nil {
					chars = append(chars, paramText)
					wasDollar = false
					wasGtlt = false
				} else {
					chars = append(chars, s.Advance())
					wasDollar = true
					wasGtlt = false
				}
				continue
			} else if nextCh == "(" {
				s.Pos -= 1
				s.syncToParser()
				if ((s.Pos + 2) < s.Length) && (string(s.Source[(s.Pos+2)]) == "(") {
					arithNode, arithText = s.parser.parseArithmeticExpansion()
					s.syncFromParser()
					if arithNode != nil {
						chars = append(chars, arithText)
						wasDollar = false
						wasGtlt = false
					} else {
						s.syncToParser()
						cmdNode, cmdText = s.parser.parseCommandSubstitution()
						s.syncFromParser()
						if cmdNode != nil {
							chars = append(chars, cmdText)
							wasDollar = false
							wasGtlt = false
						} else {
							chars = append(chars, s.Advance())
							chars = append(chars, s.Advance())
							wasDollar = false
							wasGtlt = false
						}
					}
				} else {
					cmdNode, cmdText = s.parser.parseCommandSubstitution()
					s.syncFromParser()
					if cmdNode != nil {
						chars = append(chars, cmdText)
						wasDollar = false
						wasGtlt = false
					} else {
						chars = append(chars, s.Advance())
						chars = append(chars, s.Advance())
						wasDollar = false
						wasGtlt = false
					}
				}
				continue
			} else if nextCh == "[" {
				s.Pos -= 1
				s.syncToParser()
				arithNode, arithText = s.parser.parseDeprecatedArithmetic()
				s.syncFromParser()
				if arithNode != nil {
					chars = append(chars, arithText)
					wasDollar = false
					wasGtlt = false
				} else {
					chars = append(chars, s.Advance())
					wasDollar = true
					wasGtlt = false
				}
				continue
			}
		}
		if ((ch == "(") && wasGtlt) && ((flags & (MatchedpairflagsDolbrace | MatchedpairflagsArraysub)) != 0) {
			direction := chars[len(chars)-1]
			s.Pos -= 1
			s.syncToParser()
			procsubNode, procsubText := s.parser.parseProcessSubstitution()
			s.syncFromParser()
			if procsubNode != nil {
				chars = append(chars, procsubText)
				wasDollar = false
				wasGtlt = false
			} else {
				chars = append(chars, direction)
				chars = append(chars, s.Advance())
				wasDollar = false
				wasGtlt = false
			}
			continue
		}
		chars = append(chars, ch)
		wasDollar = (ch == "$")
		wasGtlt = strings.Contains("<>", ch)
	}
	return strings.Join(chars, "")
}

func (s *Lexer) collectParamArgument(flags int, wasDollar bool) string {
	return s.parseMatchedPair("{", "}", (flags | MatchedpairflagsDolbrace), wasDollar)
}

func (s *Lexer) readWordInternal(ctx int, atCommandStart bool, inArrayLiteral bool, inAssignBuiltin bool) *Word {
	var isArrayAssign interface{}
	start := s.Pos
	var chars []string = []string{}
	var parts []Node = []Node{}
	bracketDepth := 0
	var bracketStartPos *int = nil
	seenEquals := false
	parenDepth := 0
	for !s.AtEnd() {
		ch := s.Peek()
		if ctx == WordCtxRegex {
			if ((ch == "\\") && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "\n") {
				s.Advance()
				s.Advance()
				continue
			}
		}
		if (ctx != WordCtxNormal) && s.isWordTerminator(ctx, ch, bracketDepth, parenDepth) {
			break
		}
		if (ctx == WordCtxNormal) && (ch == "[") {
			if bracketDepth > 0 {
				bracketDepth += 1
				chars = append(chars, s.Advance())
				continue
			}
			if ((chars && atCommandStart) && !seenEquals) && isArrayAssignmentPrefix(chars) {
				prevChar := chars[(len(chars) - 1)]
				if prevChar.Isalnum() || (prevChar == "_") {
					bracketStartPos := s.Pos
					bracketDepth += 1
					chars = append(chars, s.Advance())
					continue
				}
			}
			if (!chars && !seenEquals) && inArrayLiteral {
				bracketStartPos = s.Pos
				bracketDepth += 1
				chars = append(chars, s.Advance())
				continue
			}
		}
		if ((ctx == WordCtxNormal) && (ch == "]")) && (bracketDepth > 0) {
			bracketDepth -= 1
			chars = append(chars, s.Advance())
			continue
		}
		if ((ctx == WordCtxNormal) && (ch == "=")) && (bracketDepth == 0) {
			seenEquals = true
		}
		if (ctx == WordCtxRegex) && (ch == "(") {
			parenDepth += 1
			chars = append(chars, s.Advance())
			continue
		}
		if (ctx == WordCtxRegex) && (ch == ")") {
			if parenDepth > 0 {
				parenDepth -= 1
				chars = append(chars, s.Advance())
				continue
			}
			break
		}
		if strings.Contains(struct{ Single, Double bool }{WordCtxCond, WordCtxRegex}, ctx) && (ch == "[") {
			forRegex := (ctx == WordCtxRegex)
			if s.readBracketExpression(chars, parts, false, 0) {
				continue
			}
			chars = append(chars, s.Advance())
			continue
		}
		if (ctx == WordCtxCond) && (ch == "(") {
			if (s.extglob && chars) && isExtglobPrefix(chars[(len(chars)-1)]) {
				chars = append(chars, s.Advance())
				content := s.parseMatchedPair("(", ")", MatchedpairflagsExtglob, false)
				chars = append(chars, content)
				chars = append(chars, ")")
				continue
			} else {
				break
			}
		}
		if ((ctx == WordCtxRegex) && isWhitespace(ch)) && (parenDepth > 0) {
			chars = append(chars, s.Advance())
			continue
		}
		if ch == "'" {
			s.Advance()
			trackNewline := (ctx == WordCtxNormal)
			content, sawNewline := s.readSingleQuote(start)
			chars = append(chars, content)
			if (trackNewline != nil && sawNewline != nil) && s.parser != nil {
				s.parser.sawNewlineInSingleQuote = true
			}
			continue
		}
		if ch == "\"" {
			s.Advance()
			if ctx == WordCtxNormal {
				chars = append(chars, "\"")
				inSingleInDquote := false
				for !s.AtEnd() && (inSingleInDquote || (s.Peek() != "\"")) {
					c := s.Peek()
					if inSingleInDquote {
						chars = append(chars, s.Advance())
						if c == "'" {
							inSingleInDquote = false
						}
						continue
					}
					if (c == "\\") && ((s.Pos + 1) < s.Length) {
						nextC := string(s.Source[(s.Pos + 1)])
						if nextC == "\n" {
							s.Advance()
							s.Advance()
						} else {
							chars = append(chars, s.Advance())
							chars = append(chars, s.Advance())
						}
					} else if c == "$" {
						s.syncToParser()
						if !s.parser.parseDollarExpansion(chars, parts, false) {
							s.syncFromParser()
							chars = append(chars, s.Advance())
						} else {
							s.syncFromParser()
						}
					} else if c == "`" {
						s.syncToParser()
						cmdsubResult := s.parser.parseBacktickSubstitution()
						s.syncFromParser()
						if cmdsubResult[0] != nil {
							parts = append(parts, cmdsubResult[0])
							chars = append(chars, cmdsubResult[1])
						} else {
							chars = append(chars, s.Advance())
						}
					} else {
						chars = append(chars, s.Advance())
					}
				}
				if s.AtEnd() {
					panic("Unterminated double quote")
				}
				chars = append(chars, s.Advance())
			} else {
				handleLineContinuation := (ctx == WordCtxCond)
				s.syncToParser()
				s.parser.scanDoubleQuote(chars, parts, start, handleLineContinuation)
				s.syncFromParser()
			}
			continue
		}
		if (ch == "\\") && ((s.Pos + 1) < s.Length) {
			nextCh := string(s.Source[(s.Pos + 1)])
			if (ctx != WordCtxRegex) && (nextCh == "\n") {
				s.Advance()
				s.Advance()
			} else {
				chars = append(chars, s.Advance())
				chars = append(chars, s.Advance())
			}
			continue
		}
		if (((ctx != WordCtxRegex) && (ch == "$")) && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "'") {
			ansiResult := s.readAnsiCQuote()
			if ansiResult[0] != nil {
				parts = append(parts, ansiResult[0])
				chars = append(chars, ansiResult[1])
			} else {
				chars = append(chars, s.Advance())
			}
			continue
		}
		if (((ctx != WordCtxRegex) && (ch == "$")) && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "\"") {
			localeResult := s.readLocaleString()
			if localeResult[0] != nil {
				parts = append(parts, localeResult[0])
				parts.Extend(localeResult[2])
				chars = append(chars, localeResult[1])
			} else {
				chars = append(chars, s.Advance())
			}
			continue
		}
		if ch == "$" {
			s.syncToParser()
			if !s.parser.parseDollarExpansion(chars, parts, false) {
				s.syncFromParser()
				chars = append(chars, s.Advance())
			} else {
				s.syncFromParser()
				if ((((((s.extglob && (ctx == WordCtxNormal)) && chars) && (len(chars[(len(chars)-1)]) == 2)) && (chars[(len(chars) - 1)][0] == "$")) && strings.Contains("?*@", chars[(len(chars) - 1)][1])) && !s.AtEnd()) && (s.Peek() == "(") {
					chars = append(chars, s.Advance())
					content = s.parseMatchedPair("(", ")", MatchedpairflagsExtglob, false)
					chars = append(chars, content)
					chars = append(chars, ")")
				}
			}
			continue
		}
		if (ctx != WordCtxRegex) && (ch == "`") {
			s.syncToParser()
			cmdsubResult = s.parser.parseBacktickSubstitution()
			s.syncFromParser()
			if cmdsubResult[0] != nil {
				parts = append(parts, cmdsubResult[0])
				chars = append(chars, cmdsubResult[1])
			} else {
				chars = append(chars, s.Advance())
			}
			continue
		}
		if (((ctx != WordCtxRegex) && isRedirectChar(ch)) && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "(") {
			s.syncToParser()
			procsubResult := s.parser.parseProcessSubstitution()
			s.syncFromParser()
			if procsubResult[0] != nil {
				parts = append(parts, procsubResult[0])
				chars = append(chars, procsubResult[1])
			} else if procsubResult[1] != nil {
				chars = append(chars, procsubResult[1])
			} else {
				chars = append(chars, s.Advance())
				if ctx == WordCtxNormal {
					chars = append(chars, s.Advance())
				}
			}
			continue
		}
		if (((ctx == WordCtxNormal) && (ch == "(")) && chars) && (bracketDepth == 0) {
			isArrayAssign = false
			if ((len(chars) >= 3) && (chars[(len(chars)-2)] == "+")) && (chars[(len(chars)-1)] == "=") {
				isArrayAssign = isArrayAssignmentPrefix(chars[:-2])
			} else if (chars[(len(chars)-1)] == "=") && (len(chars) >= 2) {
				isArrayAssign = isArrayAssignmentPrefix(chars[:-1])
			}
			if isArrayAssign && (atCommandStart || inAssignBuiltin) {
				s.syncToParser()
				arrayResult := s.parser.parseArrayLiteral()
				s.syncFromParser()
				if arrayResult[0] != nil {
					parts = append(parts, arrayResult[0])
					chars = append(chars, arrayResult[1])
				} else {
					break
				}
				continue
			}
		}
		if (((s.extglob && (ctx == WordCtxNormal)) && isExtglobPrefix(ch)) && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "(") {
			chars = append(chars, s.Advance())
			chars = append(chars, s.Advance())
			content = s.parseMatchedPair("(", ")", MatchedpairflagsExtglob, false)
			chars = append(chars, content)
			chars = append(chars, ")")
			continue
		}
		if ((((ctx == WordCtxNormal) && ((s.parserState & ParserstateflagsPstEoftoken) != 0)) && s.eofToken != nil) && (ch == *s.eofToken)) && (bracketDepth == 0) {
			if !chars {
				chars = append(chars, s.Advance())
			}
			break
		}
		if ((ctx == WordCtxNormal) && isMetachar(ch)) && (bracketDepth == 0) {
			break
		}
		chars = append(chars, s.Advance())
	}
	if ((bracketDepth > 0) && bracketStartPos != nil) && s.AtEnd() {
		panic("unexpected EOF looking for `]'")
	}
	if !chars {
		return nil
	}
	if parts {
		return &Word{Value: strings.Join(chars, ""), Parts: parts}
	}
	return &Word{Value: strings.Join(chars, ""), Parts: nil}
}

func (s *Lexer) readWord() *Token {
	start := s.Pos
	if s.Pos >= s.Length {
		return nil
	}
	c := s.Peek()
	if c == "" {
		return nil
	}
	isProcsub := ((((c == "<") || (c == ">")) && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "("))
	isRegexParen := ((s.wordContext == WordCtxRegex) && ((c == "(") || (c == ")")))
	if (s.IsMetachar(c) && !isProcsub != nil) && !isRegexParen != nil {
		return nil
	}
	word := s.readWordInternal(s.wordContext, s.atCommandStart, s.inArrayLiteral, s.inAssignBuiltin)
	if word == nil {
		return nil
	}
	return &Token{Type: TokentypeWord, Value: word.Value, Pos: start, Parts: nil, Word: word}
}

func (s *Lexer) NextToken() *Token {
	if s.tokenCache != nil {
		tok := s.tokenCache
		s.tokenCache = nil
		s.lastReadToken = tok
		return tok
	}
	s.SkipBlanks()
	if s.AtEnd() {
		tok = &Token{Type: TokentypeEof, Value: "", Pos: s.Pos}
		s.lastReadToken = tok
		return tok
	}
	if ((s.eofToken != nil && (s.Peek() == *s.eofToken)) && !((s.parserState & ParserstateflagsPstCasepat) != 0)) && !((s.parserState & ParserstateflagsPstEoftoken) != 0) {
		tok = &Token{Type: TokentypeEof, Value: "", Pos: s.Pos}
		s.lastReadToken = tok
		return tok
	}
	for s.skipComment() {
		s.SkipBlanks()
		if s.AtEnd() {
			tok = &Token{Type: TokentypeEof, Value: "", Pos: s.Pos}
			s.lastReadToken = tok
			return tok
		}
		if ((s.eofToken != nil && (s.Peek() == *s.eofToken)) && !((s.parserState & ParserstateflagsPstCasepat) != 0)) && !((s.parserState & ParserstateflagsPstEoftoken) != 0) {
			tok = &Token{Type: TokentypeEof, Value: "", Pos: s.Pos}
			s.lastReadToken = tok
			return tok
		}
	}
	tok = s.readOperator()
	if tok != nil {
		s.lastReadToken = tok
		return tok
	}
	tok = s.readWord()
	if tok != nil {
		s.lastReadToken = tok
		return tok
	}
	tok = &Token{Type: TokentypeEof, Value: "", Pos: s.Pos}
	s.lastReadToken = tok
	return tok
}

func (s *Lexer) PeekToken() *Token {
	if s.tokenCache == nil {
		savedLast := s.lastReadToken
		s.tokenCache = s.NextToken()
		s.lastReadToken = savedLast
	}
	return s.tokenCache
}

func (s *Lexer) readAnsiCQuote() (*Node, string) {
	if s.AtEnd() || (s.Peek() != "$") {
		return nil, ""
	}
	if ((s.Pos + 1) >= s.Length) || (string(s.Source[(s.Pos+1)]) != "'") {
		return nil, ""
	}
	start := s.Pos
	s.Advance()
	s.Advance()
	var contentChars []string = []string{}
	foundClose := false
	for !s.AtEnd() {
		ch := s.Peek()
		if ch == "'" {
			s.Advance()
			foundClose = true
			break
		} else if ch == "\\" {
			contentChars = append(contentChars, s.Advance())
			if !s.AtEnd() {
				contentChars = append(contentChars, s.Advance())
			}
		} else {
			contentChars = append(contentChars, s.Advance())
		}
	}
	if !foundClose {
		panic("unexpected EOF while looking for matching `''")
	}
	text := substring(s.Source, start, s.Pos)
	content := strings.Join(contentChars, "")
	node := &AnsiCQuote{Content: content}
	return node, text
}

func (s *Lexer) syncToParser() {
	if s.parser != nil {
		s.parser.Pos = s.Pos
	}
}

func (s *Lexer) syncFromParser() {
	if s.parser != nil {
		s.Pos = s.parser.Pos
	}
}

func (s *Lexer) readLocaleString() (*Node, string, []Node) {
	var cmdsubNode *Node
	var cmdsubText string
	if s.AtEnd() || (s.Peek() != "$") {
		return nil, "", []interface{}{}
	}
	if ((s.Pos + 1) >= s.Length) || (string(s.Source[(s.Pos+1)]) != "\"") {
		return nil, "", []interface{}{}
	}
	start := s.Pos
	s.Advance()
	s.Advance()
	var contentChars []string = []string{}
	var innerParts []Node = []Node{}
	foundClose := false
	for !s.AtEnd() {
		ch := s.Peek()
		if ch == "\"" {
			s.Advance()
			foundClose = true
			break
		} else if (ch == "\\") && ((s.Pos + 1) < s.Length) {
			nextCh := string(s.Source[(s.Pos + 1)])
			if nextCh == "\n" {
				s.Advance()
				s.Advance()
			} else {
				contentChars = append(contentChars, s.Advance())
				contentChars = append(contentChars, s.Advance())
			}
		} else if (((ch == "$") && ((s.Pos + 2) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "(")) && (string(s.Source[(s.Pos+2)]) == "(") {
			s.syncToParser()
			arithNode, arithText := s.parser.parseArithmeticExpansion()
			s.syncFromParser()
			if arithNode != nil {
				innerParts = append(innerParts, arithNode)
				contentChars = append(contentChars, arithText)
			} else {
				s.syncToParser()
				cmdsubNode, cmdsubText = s.parser.parseCommandSubstitution()
				s.syncFromParser()
				if cmdsubNode != nil {
					innerParts = append(innerParts, cmdsubNode)
					contentChars = append(contentChars, cmdsubText)
				} else {
					contentChars = append(contentChars, s.Advance())
				}
			}
		} else if isExpansionStart(s.Source, s.Pos, "$(") {
			s.syncToParser()
			cmdsubNode, cmdsubText = s.parser.parseCommandSubstitution()
			s.syncFromParser()
			if cmdsubNode != nil {
				innerParts = append(innerParts, cmdsubNode)
				contentChars = append(contentChars, cmdsubText)
			} else {
				contentChars = append(contentChars, s.Advance())
			}
		} else if ch == "$" {
			s.syncToParser()
			paramNode, paramText := s.parser.parseParamExpansion(false)
			s.syncFromParser()
			if paramNode != nil {
				innerParts = append(innerParts, paramNode)
				contentChars = append(contentChars, paramText)
			} else {
				contentChars = append(contentChars, s.Advance())
			}
		} else if ch == "`" {
			s.syncToParser()
			cmdsubNode, cmdsubText = s.parser.parseBacktickSubstitution()
			s.syncFromParser()
			if cmdsubNode != nil {
				innerParts = append(innerParts, cmdsubNode)
				contentChars = append(contentChars, cmdsubText)
			} else {
				contentChars = append(contentChars, s.Advance())
			}
		} else {
			contentChars = append(contentChars, s.Advance())
		}
	}
	if !foundClose {
		s.Pos = start
		return nil, "", []interface{}{}
	}
	content := strings.Join(contentChars, "")
	text := (("$\"" + content) + "\"")
	return &LocaleString{Content: content}, text, innerParts
}

func (s *Lexer) updateDolbraceForOp(op *string, hasParam bool) {
	if s.dolbraceState == DolbracestateNone {
		return
	}
	if op == nil || (len(op) == 0) {
		return
	}
	firstChar := op[0]
	if (s.dolbraceState == DolbracestateParam) && hasParam {
		if strings.Contains("%#^,", firstChar) {
			s.dolbraceState = DolbracestateQuote
			return
		}
		if firstChar == "/" {
			s.dolbraceState = DolbracestateQuote2
			return
		}
	}
	if s.dolbraceState == DolbracestateParam {
		if strings.Contains("#%^,~:-=?+/", firstChar) {
			s.dolbraceState = DolbracestateOp
		}
	}
}

func (s *Lexer) consumeParamOperator() string {
	if s.AtEnd() {
		return ""
	}
	ch := s.Peek()
	if ch == ":" {
		s.Advance()
		if s.AtEnd() {
			return ":"
		}
		nextCh := s.Peek()
		if isSimpleParamOp(nextCh) {
			s.Advance()
			return (":" + nextCh)
		}
		return ":"
	}
	if isSimpleParamOp(ch) {
		s.Advance()
		return ch
	}
	if ch == "#" {
		s.Advance()
		if !s.AtEnd() && (s.Peek() == "#") {
			s.Advance()
			return "##"
		}
		return "#"
	}
	if ch == "%" {
		s.Advance()
		if !s.AtEnd() && (s.Peek() == "%") {
			s.Advance()
			return "%%"
		}
		return "%"
	}
	if ch == "/" {
		s.Advance()
		if !s.AtEnd() {
			nextCh = s.Peek()
			if nextCh == "/" {
				s.Advance()
				return "//"
			} else if nextCh == "#" {
				s.Advance()
				return "/#"
			} else if nextCh == "%" {
				s.Advance()
				return "/%"
			}
		}
		return "/"
	}
	if ch == "^" {
		s.Advance()
		if !s.AtEnd() && (s.Peek() == "^") {
			s.Advance()
			return "^^"
		}
		return "^"
	}
	if ch == "," {
		s.Advance()
		if !s.AtEnd() && (s.Peek() == ",") {
			s.Advance()
			return ",,"
		}
		return ","
	}
	if ch == "@" {
		s.Advance()
		return "@"
	}
	return ""
}

func (s *Lexer) paramSubscriptHasClose(startPos int) bool {
	depth := 1
	i := (startPos + 1)
	quote := &QuoteState{}
	for i < s.Length {
		c := string(s.Source[i])
		if quote.Single != nil {
			if c == "'" {
				quote.Single = false
			}
			i += 1
			continue
		}
		if quote.Double != nil {
			if (c == "\\") && ((i + 1) < s.Length) {
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

func (s *Lexer) consumeParamName() string {
	if s.AtEnd() {
		return ""
	}
	ch := s.Peek()
	if isSpecialParam(ch) {
		if ((ch == "$") && ((s.Pos + 1) < s.Length)) && strings.Contains("{'\"", string(s.Source[(s.Pos+1)])) {
			return ""
		}
		s.Advance()
		return ch
	}
	if ch.Isdigit() {
		var nameChars []string = []string{}
		for !s.AtEnd() && s.Peek().Isdigit() {
			nameChars = append(nameChars, s.Advance())
		}
		return strings.Join(nameChars, "")
	}
	if ch.Isalpha() || (ch == "_") {
		nameChars := []string{}
		for !s.AtEnd() {
			c := s.Peek()
			if c.Isalnum() || (c == "_") {
				nameChars = append(nameChars, s.Advance())
			} else if c == "[" {
				if !s.paramSubscriptHasClose(s.Pos) {
					break
				}
				nameChars = append(nameChars, s.Advance())
				content := s.parseMatchedPair("[", "]", MatchedpairflagsArraysub, false)
				nameChars = append(nameChars, content)
				nameChars = append(nameChars, "]")
				break
			} else {
				break
			}
		}
		if nameChars {
			return strings.Join(nameChars, "")
		} else {
			return ""
		}
	}
	return ""
}

func (s *Lexer) readParamExpansion(inDquote bool) (*Node, string) {
	if s.AtEnd() || (s.Peek() != "$") {
		return nil, ""
	}
	start := s.Pos
	s.Advance()
	if s.AtEnd() {
		s.Pos = start
		return nil, ""
	}
	ch := s.Peek()
	if ch == "{" {
		s.Advance()
		return s.readBracedParam(start, inDquote)
	}
	if (isSpecialParamUnbraced(ch) || isDigit(ch)) || (ch == "#") {
		s.Advance()
		text := substring(s.Source, start, s.Pos)
		return &ParamExpansion{Param: ch}, text
	}
	if ch.Isalpha() || (ch == "_") {
		nameStart := s.Pos
		for !s.AtEnd() {
			c := s.Peek()
			if c.Isalnum() || (c == "_") {
				s.Advance()
			} else {
				break
			}
		}
		name := substring(s.Source, nameStart, s.Pos)
		text = substring(s.Source, start, s.Pos)
		return &ParamExpansion{Param: name}, text
	}
	s.Pos = start
	return nil, ""
}

func (s *Lexer) readBracedParam(start int, inDquote bool) (*Node, string) {
	var op string
	if s.AtEnd() {
		panic("unexpected EOF looking for `}'")
	}
	savedDolbrace := s.dolbraceState
	s.dolbraceState = DolbracestateParam
	ch := s.Peek()
	if isFunsubChar(ch) {
		s.dolbraceState = savedDolbrace
		return s.readFunsub(start)
	}
	if ch == "#" {
		s.Advance()
		param := s.consumeParamName()
		if ((param != "") && !s.AtEnd()) && (s.Peek() == "}") {
			s.Advance()
			text := substring(s.Source, start, s.Pos)
			s.dolbraceState = savedDolbrace
			return &ParamLength{Param: param}, text
		}
		s.Pos = (start + 2)
	}
	if ch == "!" {
		s.Advance()
		for !s.AtEnd() && isWhitespaceNoNewline(s.Peek()) {
			s.Advance()
		}
		param = s.consumeParamName()
		if param != "" {
			for !s.AtEnd() && isWhitespaceNoNewline(s.Peek()) {
				s.Advance()
			}
			if !s.AtEnd() && (s.Peek() == "}") {
				s.Advance()
				text = substring(s.Source, start, s.Pos)
				s.dolbraceState = savedDolbrace
				return &ParamIndirect{Param: param}, text
			}
			if !s.AtEnd() && isAtOrStar(s.Peek()) {
				suffix := s.Advance()
				trailing := s.parseMatchedPair("{", "}", MatchedpairflagsDolbrace, false)
				text = substring(s.Source, start, s.Pos)
				s.dolbraceState = savedDolbrace
				return &ParamIndirect{Param: ((param + suffix) + trailing)}, text
			}
			op = s.consumeParamOperator()
			if ((op == "") && !s.AtEnd()) && !strings.Contains("}\"'`", s.Peek()) {
				op = s.Advance()
			}
			if (op != "") && !strings.Contains("\"'`", op) {
				arg := s.parseMatchedPair("{", "}", MatchedpairflagsDolbrace, false)
				text = substring(s.Source, start, s.Pos)
				s.dolbraceState = savedDolbrace
				return &ParamIndirect{Param: param, Op: op, Arg: arg}, text
			}
			if s.AtEnd() {
				s.dolbraceState = savedDolbrace
				panic("unexpected EOF looking for `}'")
			}
			s.Pos = (start + 2)
		} else {
			s.Pos = (start + 2)
		}
	}
	param = s.consumeParamName()
	if !(param != "") {
		if !s.AtEnd() && (strings.Contains("-=+?", s.Peek()) || (((s.Peek() == ":") && ((s.Pos + 1) < s.Length)) && isSimpleParamOp(string(s.Source[(s.Pos+1)])))) {
			param = ""
		} else {
			content := s.parseMatchedPair("{", "}", MatchedpairflagsDolbrace, false)
			text = (("${" + content) + "}")
			s.dolbraceState = savedDolbrace
			return &ParamExpansion{Param: content}, text
		}
	}
	if s.AtEnd() {
		s.dolbraceState = savedDolbrace
		panic("unexpected EOF looking for `}'")
	}
	if s.Peek() == "}" {
		s.Advance()
		text = substring(s.Source, start, s.Pos)
		s.dolbraceState = savedDolbrace
		return &ParamExpansion{Param: param}, text
	}
	op = s.consumeParamOperator()
	if op == "" {
		if ((!s.AtEnd() && (s.Peek() == "$")) && ((s.Pos + 1) < s.Length)) && strings.Contains(struct{ Single, Double bool }{"\"", "'"}, string(s.Source[(s.Pos+1)])) {
			dollarCount := (1 + countConsecutiveDollarsBefore(s.Source, s.Pos))
			if (dollarCount % 2) == 1 {
				op = ""
			} else {
				op = s.Advance()
			}
		} else if !s.AtEnd() && (s.Peek() == "`") {
			backtickPos := s.Pos
			s.Advance()
			for !s.AtEnd() && (s.Peek() != "`") {
				bc := s.Peek()
				if (bc == "\\") && ((s.Pos + 1) < s.Length) {
					nextC := string(s.Source[(s.Pos + 1)])
					if isEscapeCharInBacktick(nextC) {
						s.Advance()
					}
				}
				s.Advance()
			}
			if s.AtEnd() {
				s.dolbraceState = savedDolbrace
				panic("Unterminated backtick")
			}
			s.Advance()
			op = "`"
		} else if ((!s.AtEnd() && (s.Peek() == "$")) && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "{") {
			op = ""
		} else if !s.AtEnd() && strings.Contains(struct{ Single, Double bool }{"'", "\""}, s.Peek()) {
			op = ""
		} else if !s.AtEnd() && (s.Peek() == "\\") {
			op = s.Advance()
			if !s.AtEnd() {
				op += s.Advance()
			}
		} else {
			op = s.Advance()
		}
	}
	s.updateDolbraceForOp(op, (len(param) > 0))
	func() {
		defer func() {
			if e := recover(); e != nil {
				s.dolbraceState = savedDolbrace
				panic("")
			}
		}()
		flags := func() interface{} {
			if inDquote {
				return MatchedpairflagsDquote
			} else {
				return MatchedpairflagsNone
			}
		}()
		paramEndsWithDollar := ((param != "") && param.Endswith("$"))
		arg = s.collectParamArgument(flags, paramEndsWithDollar)
	}()
	if (strings.Contains(struct{ Single, Double bool }{"<", ">"}, op) && arg.Startswith("(")) && arg.Endswith(")") {
		inner := arg[1:-1]
		func() {
			defer func() {
				if r := recover(); r != nil {
				}
			}()
			subParser := &Parser{Source: inner}
			parsed := subParser.ParseList()
			if parsed != nil && subParser.AtEnd() != nil {
				formatted := formatCmdsubNode(parsed, 0, true, false, true)
				arg = (("(" + formatted) + ")")
			}
		}()
	}
	text = (((("${" + param) + op) + arg) + "}")
	s.dolbraceState = savedDolbrace
	return &ParamExpansion{Param: param, Op: op, Arg: arg}, text
}

func (s *Lexer) readFunsub(start int) (*Node, string) {
	return s.parser.parseFunsub(start)
}

type Node struct {
	Kind string
}

func (s *Node) ToSexp() string {
	panic("")
}

type Word struct {
	Value string
	Parts []Node
	Kind  string
}

func (s *Word) ToSexp() string {
	value := s.Value
	value = s.expandAllAnsiCQuotes(value)
	value = s.stripLocaleStringDollars(value)
	value = s.normalizeArrayWhitespace(value)
	value = s.formatCommandSubstitutions(value, false)
	value = s.normalizeParamExpansionNewlines(value)
	value = s.stripArithLineContinuations(value)
	value = s.doubleCtlescSmart(value)
	value = value.Replace("", "")
	value = value.Replace("\\", "\\\\")
	if value.Endswith("\\\\") && !value.Endswith("\\\\\\\\") {
		value = (value + "\\\\")
	}
	escaped := value.Replace("\"", "\\\"").Replace("\n", "\\n").Replace("\t", "\\t")
	return (("(word \"" + escaped) + "\")")
}

func (s *Word) appendWithCtlesc(result *[]byte, byteVal int) {
	*result = append(*result, byteVal)
}

func (s *Word) doubleCtlescSmart(value string) string {
	result := []interface{}{}
	quote := &QuoteState{}
	for _, c := range value {
		if (c == "'") && !quote.Double != nil {
			quote.Single = !quote.Single
		} else if (c == "\"") && !quote.Single != nil {
			quote.Double = !quote.Double
		}
		result = append(result, c)
		if c == "" {
			if quote.Double != nil {
				bsCount := 0
				for _, j := range Range((len(result) - 2), -1, -1) {
					if result[j] == "\\" {
						bsCount += 1
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

func (s *Word) normalizeParamExpansionNewlines(value string) string {
	result := []interface{}{}
	i := 0
	quote := &QuoteState{}
	for i < len(value) {
		c := string(value[i])
		if (c == "'") && !quote.Double != nil {
			quote.Single = !quote.Single
			result = append(result, c)
			i += 1
		} else if (c == "\"") && !quote.Single != nil {
			quote.Double = !quote.Double
			result = append(result, c)
			i += 1
		} else if isExpansionStart(value, i, "${") && !quote.Single != nil {
			result = append(result, "$")
			result = append(result, "{")
			i += 2
			hadLeadingNewline := ((i < len(value)) && (string(value[i]) == "\n"))
			if hadLeadingNewline != nil {
				result = append(result, " ")
				i += 1
			}
			depth := 1
			for (i < len(value)) && (depth > 0) {
				ch := string(value[i])
				if ((ch == "\\") && ((i + 1) < len(value))) && !quote.Single != nil {
					if string(value[(i+1)]) == "\n" {
						i += 2
						continue
					}
					result = append(result, ch)
					result = append(result, string(value[(i+1)]))
					i += 2
					continue
				}
				if (ch == "'") && !quote.Double != nil {
					quote.Single = !quote.Single
				} else if (ch == "\"") && !quote.Single != nil {
					quote.Double = !quote.Double
				} else if !quote.InQuotes() != nil {
					if ch == "{" {
						depth += 1
					} else if ch == "}" {
						depth -= 1
						if depth == 0 {
							if hadLeadingNewline != nil {
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

func (w0 *Word) shSingleQuote(s string) string {
	if !(s != "") {
		return "''"
	}
	if s == "'" {
		return "\\'"
	}
	result := []string{"'"}
	for _, c := range s {
		if c == "'" {
			result = append(result, "'\\''")
		} else {
			result = append(result, c)
		}
	}
	result = append(result, "'")
	return strings.Join(result, "")
}

func (s *Word) ansiCToBytes(inner string) []byte {
	var j int
	var byteVal int
	var i interface{}
	var codepoint interface{}
	result := Bytearray()
	i = 0
	for i < len(inner) {
		if (string(inner[i]) == "\\") && ((i + 1) < len(inner)) {
			c := string(inner[(i + 1)])
			simple := getAnsiEscape(c)
			if simple >= 0 {
				result = append(result, simple)
				i += 2
			} else if c == "'" {
				result = append(result, 39)
				i += 2
			} else if c == "x" {
				if ((i + 2) < len(inner)) && (string(inner[(i+2)]) == "{") {
					j = (i + 3)
					for (j < len(inner)) && isHexDigit(string(inner[j])) {
						j += 1
					}
					hexStr := substring(inner, (i + 3), j)
					if (j < len(inner)) && (string(inner[j]) == "}") {
						j += 1
					}
					if !hexStr != nil {
						return result
					}
					byteVal = (Int(hexStr, 16) & 255)
					if byteVal == 0 {
						return result
					}
					s.appendWithCtlesc(result, byteVal)
					i = j
				} else {
					j = (i + 2)
					for ((j < len(inner)) && (j < (i + 4))) && isHexDigit(string(inner[j])) {
						j += 1
					}
					if j > (i + 2) {
						byteVal = Int(substring(inner, (i+2), j), 16)
						if byteVal == 0 {
							return result
						}
						s.appendWithCtlesc(result, byteVal)
						i = j
					} else {
						result = append(result, Ord(string(inner[i])))
						i += 1
					}
				}
			} else if c == "u" {
				j = (i + 2)
				for ((j < len(inner)) && (j < (i + 6))) && isHexDigit(string(inner[j])) {
					j += 1
				}
				if j > (i + 2) {
					codepoint = Int(substring(inner, (i+2), j), 16)
					if codepoint == 0 {
						return result
					}
					result.Extend(Chr(codepoint).Encode("utf-8"))
					i = j
				} else {
					result = append(result, Ord(string(inner[i])))
					i += 1
				}
			} else if c == "U" {
				j = (i + 2)
				for ((j < len(inner)) && (j < (i + 10))) && isHexDigit(string(inner[j])) {
					j += 1
				}
				if j > (i + 2) {
					codepoint = Int(substring(inner, (i+2), j), 16)
					if codepoint == 0 {
						return result
					}
					result.Extend(Chr(codepoint).Encode("utf-8"))
					i = j
				} else {
					result = append(result, Ord(string(inner[i])))
					i += 1
				}
			} else if c == "c" {
				if (i + 3) <= len(inner) {
					ctrlChar := string(inner[(i + 2)])
					skipExtra := 0
					if ((ctrlChar == "\\") && ((i + 4) <= len(inner))) && (string(inner[(i+3)]) == "\\") {
						skipExtra = 1
					}
					ctrlVal := (Ord(ctrlChar) & 31)
					if ctrlVal == 0 {
						return result
					}
					s.appendWithCtlesc(result, ctrlVal)
					i += (3 + skipExtra)
				} else {
					result = append(result, Ord(string(inner[i])))
					i += 1
				}
			} else if c == "0" {
				j = (i + 2)
				for ((j < len(inner)) && (j < (i + 4))) && isOctalDigit(string(inner[j])) {
					j += 1
				}
				if j > (i + 2) {
					byteVal = (Int(substring(inner, (i+1), j), 8) & 255)
					if byteVal == 0 {
						return result
					}
					s.appendWithCtlesc(result, byteVal)
					i = j
				} else {
					return result
				}
			} else if (c >= "1") && (c <= "7") {
				j = (i + 1)
				for ((j < len(inner)) && (j < (i + 4))) && isOctalDigit(string(inner[j])) {
					j += 1
				}
				byteVal = (Int(substring(inner, (i+1), j), 8) & 255)
				if byteVal == 0 {
					return result
				}
				s.appendWithCtlesc(result, byteVal)
				i = j
			} else {
				result = append(result, 92)
				result = append(result, Ord(c))
				i += 2
			}
		} else {
			result.Extend(string(inner[i]).Encode("utf-8"))
			i += 1
		}
	}
	return result
}

func (s *Word) expandAnsiCEscapes(value string) string {
	if !(value.Startswith("'") && value.Endswith("'")) {
		return value
	}
	inner := substring(value, 1, (len(value) - 1))
	literalBytes := s.ansiCToBytes(inner)
	literalStr := literalBytes.Decode("utf-8")
	return s.shSingleQuote(literalStr)
}

func (s *Word) expandAllAnsiCQuotes(value string) string {
	var inPattern bool
	result := []interface{}{}
	i := 0
	quote := &QuoteState{}
	inBacktick := false
	braceDepth := 0
	for i < len(value) {
		ch := string(value[i])
		if (ch == "`") && !quote.Single != nil {
			inBacktick = !inBacktick
			result = append(result, ch)
			i += 1
			continue
		}
		if inBacktick {
			if (ch == "\\") && ((i + 1) < len(value)) {
				result = append(result, ch)
				result = append(result, string(value[(i+1)]))
				i += 2
			} else {
				result = append(result, ch)
				i += 1
			}
			continue
		}
		if !quote.Single != nil {
			if isExpansionStart(value, i, "${") {
				braceDepth += 1
				quote.Push()
				result = append(result, "${")
				i += 2
				continue
			} else if ((ch == "}") && (braceDepth > 0)) && !quote.Double != nil {
				braceDepth -= 1
				result = append(result, ch)
				quote[len(quote)-1]
				i += 1
				continue
			}
		}
		effectiveInDquote := quote.Double
		if (ch == "'") && !effectiveInDquote != nil {
			isAnsiC := (((!quote.Single && (i > 0)) && (string(value[(i-1)]) == "$")) && ((countConsecutiveDollarsBefore(value, (i-1)) % 2) == 0))
			if !isAnsiC != nil {
				quote.Single = !quote.Single
			}
			result = append(result, ch)
			i += 1
		} else if (ch == "\"") && !quote.Single != nil {
			quote.Double = !quote.Double
			result = append(result, ch)
			i += 1
		} else if ((ch == "\\") && ((i + 1) < len(value))) && !quote.Single != nil {
			result = append(result, ch)
			result = append(result, string(value[(i+1)]))
			i += 2
		} else if ((startsWithAt(value, i, "$'") && !quote.Single != nil) && !effectiveInDquote != nil) && ((countConsecutiveDollarsBefore(value, i) % 2) == 0) {
			j := (i + 2)
			for j < len(value) {
				if (string(value[j]) == "\\") && ((j + 1) < len(value)) {
					j += 2
				} else if string(value[j]) == "'" {
					j += 1
					break
				} else {
					j += 1
				}
			}
			ansiStr := substring(value, i, j)
			expanded := s.expandAnsiCEscapes(substring(ansiStr, 1, len(ansiStr)))
			outerInDquote := quote.OuterDouble()
			if (((braceDepth > 0) && outerInDquote != nil) && expanded.Startswith("'")) && expanded.Endswith("'") {
				inner := substring(expanded, 1, (len(expanded) - 1))
				if inner.Find("") == -1 {
					resultStr := strings.Join(result, "")
					inPattern = false
					lastBraceIdx := resultStr.Rfind("${")
					if lastBraceIdx >= 0 {
						afterBrace := resultStr[(lastBraceIdx + 2):]
						varNameLen := 0
						if afterBrace != nil {
							if strings.Contains("@*#?-$!0123456789_", afterBrace[0]) {
								varNameLen = 1
							} else if afterBrace[0].Isalpha() || (afterBrace[0] == "_") {
								for varNameLen < len(afterBrace) {
									c := afterBrace[varNameLen]
									if !(c.Isalnum() || (c == "_")) {
										break
									}
									varNameLen += 1
								}
							}
						}
						if ((varNameLen > 0) && (varNameLen < len(afterBrace))) && !strings.Contains("#?-", afterBrace[0]) {
							opStart := afterBrace[varNameLen:]
							if opStart.Startswith("@") && (len(opStart) > 1) {
								opStart = opStart[1:]
							}
							for _, op := range []string{"//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"} {
								if opStart.Startswith(op) {
									inPattern = true
									break
								}
							}
							if (!inPattern && opStart != nil) && !strings.Contains("%#/^,~:+-=?", opStart[0]) {
								for _, op := range []string{"//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"} {
									if strings.Contains(opStart, op) {
										inPattern = true
										break
									}
								}
							}
						} else if (varNameLen == 0) && (len(afterBrace) > 1) {
							firstChar := afterBrace[0]
							if !strings.Contains("%#/^,", firstChar) {
								rest := afterBrace[1:]
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
			i += 1
		}
	}
	return strings.Join(result, "")
}

func (s *Word) stripLocaleStringDollars(value string) string {
	var bracketInDoubleQuote bool
	result := []interface{}{}
	i := 0
	braceDepth := 0
	bracketDepth := 0
	quote := &QuoteState{}
	braceQuote := &QuoteState{}
	bracketInDoubleQuote = false
	for i < len(value) {
		ch := string(value[i])
		if (((ch == "\\") && ((i + 1) < len(value))) && !quote.Single != nil) && !braceQuote.Single != nil {
			result = append(result, ch)
			result = append(result, string(value[(i+1)]))
			i += 2
		} else if ((startsWithAt(value, i, "${") && !quote.Single != nil) && !braceQuote.Single != nil) && ((i == 0) || (string(value[(i-1)]) != "$")) {
			braceDepth += 1
			braceQuote.Double = false
			braceQuote.Single = false
			result = append(result, "$")
			result = append(result, "{")
			i += 2
		} else if ((((ch == "}") && (braceDepth > 0)) && !quote.Single != nil) && !braceQuote.Double != nil) && !braceQuote.Single != nil {
			braceDepth -= 1
			result = append(result, ch)
			i += 1
		} else if (((ch == "[") && (braceDepth > 0)) && !quote.Single != nil) && !braceQuote.Double != nil {
			bracketDepth += 1
			bracketInDoubleQuote = false
			result = append(result, ch)
			i += 1
		} else if (((ch == "]") && (bracketDepth > 0)) && !quote.Single != nil) && !bracketInDoubleQuote {
			bracketDepth -= 1
			result = append(result, ch)
			i += 1
		} else if ((ch == "'") && !quote.Double != nil) && (braceDepth == 0) {
			quote.Single = !quote.Single
			result = append(result, ch)
			i += 1
		} else if ((ch == "\"") && !quote.Single != nil) && (braceDepth == 0) {
			quote.Double = !quote.Double
			result = append(result, ch)
			i += 1
		} else if ((ch == "\"") && !quote.Single != nil) && (bracketDepth > 0) {
			bracketInDoubleQuote = !bracketInDoubleQuote
			result = append(result, ch)
			i += 1
		} else if (((ch == "\"") && !quote.Single != nil) && !braceQuote.Single != nil) && (braceDepth > 0) {
			braceQuote.Double = !braceQuote.Double
			result = append(result, ch)
			i += 1
		} else if (((ch == "'") && !quote.Double != nil) && !braceQuote.Double != nil) && (braceDepth > 0) {
			braceQuote.Single = !braceQuote.Single
			result = append(result, ch)
			i += 1
		} else if ((((startsWithAt(value, i, "$\"") && !quote.Single != nil) && !braceQuote.Single != nil) && (((braceDepth > 0) || (bracketDepth > 0)) || !quote.Double != nil)) && !braceQuote.Double != nil) && !bracketInDoubleQuote {
			dollarCount := (1 + countConsecutiveDollarsBefore(value, i))
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
				i += 1
			}
		} else {
			result = append(result, ch)
			i += 1
		}
	}
	return strings.Join(result, "")
}

func (s *Word) normalizeArrayWhitespace(value string) string {
	var closeParenPos int
	i := 0
	if !((i < len(value)) && (string(value[i]).Isalpha() || (string(value[i]) == "_"))) {
		return value
	}
	i += 1
	for (i < len(value)) && (string(value[i]).Isalnum() || (string(value[i]) == "_")) {
		i += 1
	}
	for (i < len(value)) && (string(value[i]) == "[") {
		depth := 1
		i += 1
		for (i < len(value)) && (depth > 0) {
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
	if (i < len(value)) && (string(value[i]) == "+") {
		i += 1
	}
	if !((((i + 1) < len(value)) && (string(value[i]) == "=")) && (string(value[(i+1)]) == "(")) {
		return value
	}
	prefix := substring(value, 0, (i + 1))
	openParenPos := (i + 1)
	if value.Endswith(")") {
		closeParenPos = (len(value) - 1)
	} else {
		closeParenPos = s.findMatchingParen(value, openParenPos)
		if closeParenPos < 0 {
			return value
		}
	}
	inner := substring(value, (openParenPos + 1), closeParenPos)
	suffix := substring(value, (closeParenPos + 1), len(value))
	result := s.normalizeArrayInner(inner)
	return ((((prefix + "(") + result) + ")") + suffix)
}

func (s *Word) findMatchingParen(value string, openPos int) int {
	if (openPos >= len(value)) || (string(value[openPos]) != "(") {
		return -1
	}
	i := (openPos + 1)
	depth := 1
	quote := &QuoteState{}
	for (i < len(value)) && (depth > 0) {
		ch := string(value[i])
		if ((ch == "\\") && ((i + 1) < len(value))) && !quote.Single != nil {
			i += 2
			continue
		}
		if (ch == "'") && !quote.Double != nil {
			quote.Single = !quote.Single
			i += 1
			continue
		}
		if (ch == "\"") && !quote.Single != nil {
			quote.Double = !quote.Double
			i += 1
			continue
		}
		if quote.Single != nil || quote.Double != nil {
			i += 1
			continue
		}
		if ch == "#" {
			for (i < len(value)) && (string(value[i]) != "\n") {
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

func (s *Word) normalizeArrayInner(inner string) string {
	var inWhitespace bool
	var j int
	var i int
	var depth int
	normalized := []interface{}{}
	i = 0
	inWhitespace = true
	braceDepth := 0
	bracketDepth := 0
	for i < len(inner) {
		ch := string(inner[i])
		if isWhitespace(ch) {
			if ((!inWhitespace && normalized != nil) && (braceDepth == 0)) && (bracketDepth == 0) {
				normalized = append(normalized, " ")
				inWhitespace = true
			}
			if (braceDepth > 0) || (bracketDepth > 0) {
				normalized = append(normalized, ch)
			}
			i += 1
		} else if ch == "'" {
			inWhitespace = false
			j = (i + 1)
			for (j < len(inner)) && (string(inner[j]) != "'") {
				j += 1
			}
			normalized = append(normalized, substring(inner, i, (j+1)))
			i = (j + 1)
		} else if ch == "\"" {
			inWhitespace = false
			j = (i + 1)
			dqContent := []string{"\""}
			dqBraceDepth := 0
			for j < len(inner) {
				if (string(inner[j]) == "\\") && ((j + 1) < len(inner)) {
					if string(inner[(j+1)]) == "\n" {
						j += 2
					} else {
						dqContent = append(dqContent, string(inner[j]))
						dqContent = append(dqContent, string(inner[(j+1)]))
						j += 2
					}
				} else if isExpansionStart(inner, j, "${") {
					dqContent = append(dqContent, "${")
					dqBraceDepth += 1
					j += 2
				} else if (string(inner[j]) == "}") && (dqBraceDepth > 0) {
					dqContent = append(dqContent, "}")
					dqBraceDepth -= 1
					j += 1
				} else if (string(inner[j]) == "\"") && (dqBraceDepth == 0) {
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
		} else if (ch == "\\") && ((i + 1) < len(inner)) {
			if string(inner[(i+1)]) == "\n" {
				i += 2
			} else {
				inWhitespace = false
				normalized = append(normalized, substring(inner, i, (i+2)))
				i += 2
			}
		} else if isExpansionStart(inner, i, "$((") {
			inWhitespace = false
			j = (i + 3)
			depth = 1
			for (j < len(inner)) && (depth > 0) {
				if (((j + 1) < len(inner)) && (string(inner[j]) == "(")) && (string(inner[(j+1)]) == "(") {
					depth += 1
					j += 2
				} else if (((j + 1) < len(inner)) && (string(inner[j]) == ")")) && (string(inner[(j+1)]) == ")") {
					depth -= 1
					j += 2
				} else {
					j += 1
				}
			}
			normalized = append(normalized, substring(inner, i, j))
			i = j
		} else if isExpansionStart(inner, i, "$(") {
			inWhitespace = false
			j = (i + 2)
			depth = 1
			for (j < len(inner)) && (depth > 0) {
				if ((string(inner[j]) == "(") && (j > 0)) && (string(inner[(j-1)]) == "$") {
					depth += 1
				} else if string(inner[j]) == ")" {
					depth -= 1
				} else if string(inner[j]) == "'" {
					j += 1
					for (j < len(inner)) && (string(inner[j]) != "'") {
						j += 1
					}
				} else if string(inner[j]) == "\"" {
					j += 1
					for j < len(inner) {
						if (string(inner[j]) == "\\") && ((j + 1) < len(inner)) {
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
			normalized = append(normalized, substring(inner, i, j))
			i = j
		} else if (((ch == "<") || (ch == ">")) && ((i + 1) < len(inner))) && (string(inner[(i+1)]) == "(") {
			inWhitespace = false
			j = (i + 2)
			depth = 1
			for (j < len(inner)) && (depth > 0) {
				if string(inner[j]) == "(" {
					depth += 1
				} else if string(inner[j]) == ")" {
					depth -= 1
				} else if string(inner[j]) == "'" {
					j += 1
					for (j < len(inner)) && (string(inner[j]) != "'") {
						j += 1
					}
				} else if string(inner[j]) == "\"" {
					j += 1
					for j < len(inner) {
						if (string(inner[j]) == "\\") && ((j + 1) < len(inner)) {
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
			normalized = append(normalized, substring(inner, i, j))
			i = j
		} else if isExpansionStart(inner, i, "${") {
			inWhitespace = false
			normalized = append(normalized, "${")
			braceDepth += 1
			i += 2
		} else if (ch == "{") && (braceDepth > 0) {
			normalized = append(normalized, ch)
			braceDepth += 1
			i += 1
		} else if (ch == "}") && (braceDepth > 0) {
			normalized = append(normalized, ch)
			braceDepth -= 1
			i += 1
		} else if ((ch == "#") && (braceDepth == 0)) && inWhitespace {
			for (i < len(inner)) && (string(inner[i]) != "\n") {
				i += 1
			}
		} else if ch == "[" {
			if inWhitespace || (bracketDepth > 0) {
				bracketDepth += 1
			}
			inWhitespace = false
			normalized = append(normalized, ch)
			i += 1
		} else if (ch == "]") && (bracketDepth > 0) {
			normalized = append(normalized, ch)
			bracketDepth -= 1
			i += 1
		} else {
			inWhitespace = false
			normalized = append(normalized, ch)
			i += 1
		}
	}
	return strings.Join(normalized, "").Rstrip()
}

func (s *Word) stripArithLineContinuations(value string) string {
	var firstCloseIdx interface{}
	result := []interface{}{}
	i := 0
	for i < len(value) {
		if isExpansionStart(value, i, "$((") {
			start := i
			i += 3
			depth := 2
			arithContent := []interface{}{}
			var firstCloseIdx *int = nil
			for (i < len(value)) && (depth > 0) {
				if string(value[i]) == "(" {
					arithContent = append(arithContent, "(")
					depth += 1
					i += 1
					if depth > 1 {
						firstCloseIdx = nil
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
				} else if ((string(value[i]) == "\\") && ((i + 1) < len(value))) && (string(value[(i+1)]) == "\n") {
					numBackslashes := 0
					j := (len(arithContent) - 1)
					for (j >= 0) && (arithContent[j] == "\n") {
						j -= 1
					}
					for (j >= 0) && (arithContent[j] == "\\") {
						numBackslashes += 1
						j -= 1
					}
					if (numBackslashes % 2) == 1 {
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
			if (depth == 0) || ((depth == 1) && firstCloseIdx != nil) {
				content := strings.Join(arithContent, "")
				if firstCloseIdx != nil {
					content = content[:firstCloseIdx]
					closing := func() string {
						if depth == 0 {
							return "))"
						} else {
							return ")"
						}
					}()
					result = append(result, (("$((" + content) + closing))
				} else {
					result = append(result, (("$((" + content) + ")"))
				}
			} else {
				result = append(result, substring(value, start, i))
			}
		} else {
			result = append(result, string(value[i]))
			i += 1
		}
	}
	return strings.Join(result, "")
}

func (s *Word) collectCmdsubs(node Node) []Node {
	var result []Node = []Node{}
	if Isinstance(node, CommandSubstitution) {
		result = append(result, node)
	} else if Isinstance(node, Array) {
		for _, elem := range node.Elements {
			for _, p := range elem.Parts {
				if Isinstance(p, CommandSubstitution) {
					result = append(result, p)
				} else {
					result.Extend(s.collectCmdsubs(p))
				}
			}
		}
	} else if Isinstance(node, ArithmeticExpansion) {
		if node.Expression != nil {
			result.Extend(s.collectCmdsubs(node.Expression))
		}
	} else if Isinstance(node, ArithBinaryOp) || Isinstance(node, ArithComma) {
		result.Extend(s.collectCmdsubs(node.Left))
		result.Extend(s.collectCmdsubs(node.Right))
	} else if (((Isinstance(node, ArithUnaryOp) || Isinstance(node, ArithPreIncr)) || Isinstance(node, ArithPostIncr)) || Isinstance(node, ArithPreDecr)) || Isinstance(node, ArithPostDecr) {
		result.Extend(s.collectCmdsubs(node.Operand))
	} else if Isinstance(node, ArithTernary) {
		result.Extend(s.collectCmdsubs(node.Condition))
		result.Extend(s.collectCmdsubs(node.IfTrue))
		result.Extend(s.collectCmdsubs(node.IfFalse))
	} else if Isinstance(node, ArithAssign) {
		result.Extend(s.collectCmdsubs(node.Target))
		result.Extend(s.collectCmdsubs(node.Value))
	}
	return result
}

func (s *Word) collectProcsubs(node Node) []Node {
	var result []Node = []Node{}
	if Isinstance(node, ProcessSubstitution) {
		result = append(result, node)
	} else if Isinstance(node, Array) {
		for _, elem := range node.Elements {
			for _, p := range elem.Parts {
				if Isinstance(p, ProcessSubstitution) {
					result = append(result, p)
				} else {
					result.Extend(s.collectProcsubs(p))
				}
			}
		}
	}
	return result
}

func (s *Word) formatCommandSubstitutions(value string, inArith bool) string {
	var suffix string
	var direction string
	var j interface{}
	var stripped interface{}
	var i interface{}
	var inner interface{}
	var node interface{}
	var formatted interface{}
	var prefix string
	var depth int
	cmdsubParts := []interface{}{}
	procsubParts := []interface{}{}
	hasArith := false
	for _, p := range s.Parts {
		if p.Kind == "cmdsub" {
			cmdsubParts = append(cmdsubParts, p)
		} else if p.Kind == "procsub" {
			procsubParts = append(procsubParts, p)
		} else if p.Kind == "arith" {
			hasArith = true
		} else {
			cmdsubParts.Extend(s.collectCmdsubs(p))
			procsubParts.Extend(s.collectProcsubs(p))
		}
	}
	hasBraceCmdsub := ((((value.Find("${ ") != -1) || (value.Find("${\t") != -1)) || (value.Find("${\n") != -1)) || (value.Find("${|") != -1))
	hasUntrackedCmdsub := false
	hasUntrackedProcsub := false
	idx := 0
	scanQuote := &QuoteState{}
	for idx < len(value) {
		if string(value[idx]) == "\"" {
			scanQuote.Double = !scanQuote.Double
			idx += 1
		} else if (string(value[idx]) == "'") && !scanQuote.Double != nil {
			idx += 1
			for (idx < len(value)) && (string(value[idx]) != "'") {
				idx += 1
			}
			if idx < len(value) {
				idx += 1
			}
		} else if ((startsWithAt(value, idx, "$(") && !startsWithAt(value, idx, "$((")) && !isBackslashEscaped(value, idx)) && !isDollarDollarParen(value, idx) {
			hasUntrackedCmdsub = true
			break
		} else if (startsWithAt(value, idx, "<(") || startsWithAt(value, idx, ">(")) && !scanQuote.Double != nil {
			if (idx == 0) || (!string(value[(idx-1)]).Isalnum() && !strings.Contains("\"'", string(value[(idx-1)]))) {
				hasUntrackedProcsub = true
				break
			}
			idx += 1
		} else {
			idx += 1
		}
	}
	hasParamWithProcsubPattern := (strings.Contains(value, "${") && (strings.Contains(value, "<(") || strings.Contains(value, ">(")))
	if ((((!cmdsubParts != nil && !procsubParts != nil) && !hasBraceCmdsub != nil) && !hasUntrackedCmdsub) && !hasUntrackedProcsub) && !hasParamWithProcsubPattern != nil {
		return value
	}
	result := []interface{}{}
	i = 0
	cmdsubIdx := 0
	procsubIdx := 0
	mainQuote := &QuoteState{}
	extglobDepth := 0
	deprecatedArithDepth := 0
	arithDepth := 0
	arithParenDepth := 0
	for i < len(value) {
		if (((i > 0) && isExtglobPrefix(string(value[(i-1)]))) && (string(value[i]) == "(")) && !isBackslashEscaped(value, (i-1)) {
			extglobDepth += 1
			result = append(result, string(value[i]))
			i += 1
			continue
		}
		if (string(value[i]) == ")") && (extglobDepth > 0) {
			extglobDepth -= 1
			result = append(result, string(value[i]))
			i += 1
			continue
		}
		if startsWithAt(value, i, "$[") && !isBackslashEscaped(value, i) {
			deprecatedArithDepth += 1
			result = append(result, string(value[i]))
			i += 1
			continue
		}
		if (string(value[i]) == "]") && (deprecatedArithDepth > 0) {
			deprecatedArithDepth -= 1
			result = append(result, string(value[i]))
			i += 1
			continue
		}
		if (isExpansionStart(value, i, "$((") && !isBackslashEscaped(value, i)) && hasArith {
			arithDepth += 1
			arithParenDepth += 2
			result = append(result, "$((")
			i += 3
			continue
		}
		if ((arithDepth > 0) && (arithParenDepth == 2)) && startsWithAt(value, i, "))") {
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
		if isExpansionStart(value, i, "$((") && !hasArith {
			j = findCmdsubEnd(value, (i + 2))
			result = append(result, substring(value, i, j))
			if cmdsubIdx < len(cmdsubParts) {
				cmdsubIdx += 1
			}
			i = j
			continue
		}
		if ((startsWithAt(value, i, "$(") && !startsWithAt(value, i, "$((")) && !isBackslashEscaped(value, i)) && !isDollarDollarParen(value, i) {
			j = findCmdsubEnd(value, (i + 2))
			if extglobDepth > 0 {
				result = append(result, substring(value, i, j))
				if cmdsubIdx < len(cmdsubParts) {
					cmdsubIdx += 1
				}
				i = j
				continue
			}
			inner = substring(value, (i + 2), (j - 1))
			if cmdsubIdx < len(cmdsubParts) {
				node = cmdsubParts[cmdsubIdx]
				formatted = formatCmdsubNode(node.Command)
				cmdsubIdx += 1
			} else {
				func() {
					defer func() {
						if r := recover(); r != nil {
							formatted = inner
						}
					}()
					parser := &Parser{Source: inner}
					parsed := parser.ParseList()
					formatted = func() string {
						if parsed {
							return formatCmdsubNode(parsed)
						} else {
							return ""
						}
					}()
				}()
			}
			if formatted.Startswith("(") {
				result = append(result, (("$( " + formatted) + ")"))
			} else {
				result = append(result, (("$(" + formatted) + ")"))
			}
			i = j
		} else if (string(value[i]) == "`") && (cmdsubIdx < len(cmdsubParts)) {
			j = (i + 1)
			for j < len(value) {
				if (string(value[j]) == "\\") && ((j + 1) < len(value)) {
					j += 2
					continue
				}
				if string(value[j]) == "`" {
					j += 1
					break
				}
				j += 1
			}
			result = append(result, substring(value, i, j))
			cmdsubIdx += 1
			i = j
		} else if ((isExpansionStart(value, i, "${") && ((i + 2) < len(value))) && isFunsubChar(string(value[(i+2)]))) && !isBackslashEscaped(value, i) {
			j = findFunsubEnd(value, (i + 2))
			cmdsubNode := func() interface{} {
				if cmdsubIdx < len(cmdsubParts) {
					return cmdsubParts[cmdsubIdx]
				} else {
					return nil
				}
			}()
			if Isinstance(cmdsubNode, CommandSubstitution) && cmdsubNode.Brace != nil {
				node = cmdsubNode
				formatted = formatCmdsubNode(node.Command)
				hasPipe := (string(value[(i+2)]) == "|")
				prefix = func() string {
					if hasPipe {
						return "${|"
					} else {
						return "${ "
					}
				}()
				origInner := substring(value, (i + 2), (j - 1))
				endsWithNewline := origInner.Endswith("\n")
				if !formatted != nil || formatted.Isspace() {
					suffix = "}"
				} else if formatted.Endswith("&") || formatted.Endswith("& ") {
					suffix = func() string {
						if formatted.Endswith("&") {
							return " }"
						} else {
							return "}"
						}
					}()
				} else if endsWithNewline != nil {
					suffix = "\n }"
				} else {
					suffix = "; }"
				}
				result = append(result, ((prefix + formatted) + suffix))
				cmdsubIdx += 1
			} else {
				result = append(result, substring(value, i, j))
			}
			i = j
		} else if (((startsWithAt(value, i, ">(") || startsWithAt(value, i, "<(")) && !mainQuote.Double != nil) && (deprecatedArithDepth == 0)) && (arithDepth == 0) {
			isProcsub := ((i == 0) || (!string(value[(i-1)]).Isalnum() && !strings.Contains("\"'", string(value[(i-1)]))))
			if extglobDepth > 0 {
				j = findCmdsubEnd(value, (i + 2))
				result = append(result, substring(value, i, j))
				if procsubIdx < len(procsubParts) {
					procsubIdx += 1
				}
				i = j
				continue
			}
			if procsubIdx < len(procsubParts) {
				direction = string(value[i])
				j = findCmdsubEnd(value, (i + 2))
				node = procsubParts[procsubIdx]
				compact := startsWithSubshell(node.Command)
				formatted = formatCmdsubNode(node.Command, 0, true, compact, true)
				rawContent := substring(value, (i + 2), (j - 1))
				if node.Command.Kind == "subshell" {
					leadingWsEnd := 0
					for (leadingWsEnd < len(rawContent)) && strings.Contains(" \t\n", rawContent[leadingWsEnd]) {
						leadingWsEnd += 1
					}
					leadingWs := rawContent[:leadingWsEnd]
					stripped = rawContent[leadingWsEnd:]
					if stripped.Startswith("(") {
						if leadingWs != nil {
							normalizedWs := leadingWs.Replace("\n", " ").Replace("\t", " ")
							spaced := formatCmdsubNode(node.Command)
							result = append(result, ((((direction + "(") + normalizedWs) + spaced) + ")"))
						} else {
							rawContent = rawContent.Replace("\\\n", "")
							result = append(result, (((direction + "(") + rawContent) + ")"))
						}
						procsubIdx += 1
						i = j
						continue
					}
				}
				rawContent = substring(value, (i + 2), (j - 1))
				rawStripped := rawContent.Replace("\\\n", "")
				if startsWithSubshell(node.Command) && (formatted != rawStripped) {
					result = append(result, (((direction + "(") + rawStripped) + ")"))
				} else {
					finalOutput := (((direction + "(") + formatted) + ")")
					result = append(result, finalOutput)
				}
				procsubIdx += 1
				i = j
			} else if isProcsub != nil && (len(s.Parts) != 0) {
				direction = string(value[i])
				j = findCmdsubEnd(value, (i + 2))
				if (j > len(value)) || (((j > 0) && (j <= len(value))) && (string(value[(j-1)]) != ")")) {
					result = append(result, string(value[i]))
					i += 1
					continue
				}
				inner = substring(value, (i + 2), (j - 1))
				func() {
					defer func() {
						if r := recover(); r != nil {
							formatted = inner
						}
					}()
					parser = &Parser{Source: inner}
					parsed = parser.ParseList()
					if (parsed != nil && (parser.Pos == len(inner))) && !strings.Contains(inner, "\n") {
						compact = startsWithSubshell(parsed)
						formatted = formatCmdsubNode(parsed, 0, true, compact, true)
					} else {
						formatted = inner
					}
				}()
				result = append(result, (((direction + "(") + formatted) + ")"))
				i = j
			} else if isProcsub != nil {
				direction = string(value[i])
				j = findCmdsubEnd(value, (i + 2))
				if (j > len(value)) || (((j > 0) && (j <= len(value))) && (string(value[(j-1)]) != ")")) {
					result = append(result, string(value[i]))
					i += 1
					continue
				}
				inner = substring(value, (i + 2), (j - 1))
				if inArith {
					result = append(result, (((direction + "(") + inner) + ")"))
				} else if inner.Strip() != nil {
					stripped = inner.Lstrip(" \t")
					result = append(result, (((direction + "(") + stripped) + ")"))
				} else {
					result = append(result, (((direction + "(") + inner) + ")"))
				}
				i = j
			} else {
				result = append(result, string(value[i]))
				i += 1
			}
		} else if (((isExpansionStart(value, i, "${ ") || isExpansionStart(value, i, "${\t")) || isExpansionStart(value, i, "${\n")) || isExpansionStart(value, i, "${|")) && !isBackslashEscaped(value, i) {
			prefix = substring(value, i, (i+3)).Replace("\t", " ").Replace("\n", " ")
			j = (i + 3)
			depth = 1
			for (j < len(value)) && (depth > 0) {
				if string(value[j]) == "{" {
					depth += 1
				} else if string(value[j]) == "}" {
					depth -= 1
				}
				j += 1
			}
			inner = substring(value, (i + 2), (j - 1))
			if inner.Strip() == "" {
				result = append(result, "${ }")
			} else {
				func() {
					defer func() {
						if r := recover(); r != nil {
							result = append(result, substring(value, i, j))
						}
					}()
					parser = &Parser{Source: inner.Lstrip(" \t\n|")}
					parsed = parser.ParseList()
					if parsed != nil {
						formatted = formatCmdsubNode(parsed)
						formatted = formatted.Rstrip(";")
						if inner.Rstrip(" \t").Endswith("\n") {
							terminator := "\n }"
						} else if formatted.Endswith(" &") {
							terminator = " }"
						} else {
							terminator = "; }"
						}
						result = append(result, ((prefix + formatted) + terminator))
					} else {
						result = append(result, "${ }")
					}
				}()
			}
			i = j
		} else if isExpansionStart(value, i, "${") && !isBackslashEscaped(value, i) {
			j = (i + 2)
			depth = 1
			braceQuote := &QuoteState{}
			for (j < len(value)) && (depth > 0) {
				c := string(value[j])
				if ((c == "\\") && ((j + 1) < len(value))) && !braceQuote.Single != nil {
					j += 2
					continue
				}
				if (c == "'") && !braceQuote.Double != nil {
					braceQuote.Single = !braceQuote.Single
				} else if (c == "\"") && !braceQuote.Single != nil {
					braceQuote.Double = !braceQuote.Double
				} else if !braceQuote.InQuotes() != nil {
					if isExpansionStart(value, j, "$(") && !startsWithAt(value, j, "$((") {
						j = findCmdsubEnd(value, (j + 2))
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
				inner = substring(value, (i + 2), j)
			} else {
				inner = substring(value, (i + 2), (j - 1))
			}
			formattedInner := s.formatCommandSubstitutions(inner, false)
			formattedInner = s.normalizeExtglobWhitespace(formattedInner)
			if depth == 0 {
				result = append(result, (("${" + formattedInner) + "}"))
			} else {
				result = append(result, ("${" + formattedInner))
			}
			i = j
		} else if string(value[i]) == "\"" {
			mainQuote.Double = !mainQuote.Double
			result = append(result, string(value[i]))
			i += 1
		} else if (string(value[i]) == "'") && !mainQuote.Double != nil {
			j = (i + 1)
			for (j < len(value)) && (string(value[j]) != "'") {
				j += 1
			}
			if j < len(value) {
				j += 1
			}
			result = append(result, substring(value, i, j))
			i = j
		} else {
			result = append(result, string(value[i]))
			i += 1
		}
	}
	return strings.Join(result, "")
}

func (s *Word) normalizeExtglobWhitespace(value string) string {
	var partContent interface{}
	result := []interface{}{}
	i := 0
	extglobQuote := &QuoteState{}
	deprecatedArithDepth := 0
	for i < len(value) {
		if string(value[i]) == "\"" {
			extglobQuote.Double = !extglobQuote.Double
			result = append(result, string(value[i]))
			i += 1
			continue
		}
		if startsWithAt(value, i, "$[") && !isBackslashEscaped(value, i) {
			deprecatedArithDepth += 1
			result = append(result, string(value[i]))
			i += 1
			continue
		}
		if (string(value[i]) == "]") && (deprecatedArithDepth > 0) {
			deprecatedArithDepth -= 1
			result = append(result, string(value[i]))
			i += 1
			continue
		}
		if ((i + 1) < len(value)) && (string(value[(i+1)]) == "(") {
			prefixChar := string(value[i])
			if (strings.Contains("><", prefixChar) && !extglobQuote.Double != nil) && (deprecatedArithDepth == 0) {
				result = append(result, prefixChar)
				result = append(result, "(")
				i += 2
				depth := 1
				patternParts := []interface{}{}
				currentPart := []interface{}{}
				hasPipe := false
				for (i < len(value)) && (depth > 0) {
					if (string(value[i]) == "\\") && ((i + 1) < len(value)) {
						currentPart = append(currentPart, value[i:(i+2)])
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
								patternParts = append(patternParts, partContent.Strip())
							} else {
								patternParts = append(patternParts, partContent)
							}
							break
						}
						currentPart = append(currentPart, string(value[i]))
						i += 1
					} else if (string(value[i]) == "|") && (depth == 1) {
						if ((i + 1) < len(value)) && (string(value[(i+1)]) == "|") {
							currentPart = append(currentPart, "||")
							i += 2
						} else {
							hasPipe = true
							partContent = strings.Join(currentPart, "")
							if strings.Contains(partContent, "<<") {
								patternParts = append(patternParts, partContent)
							} else {
								patternParts = append(patternParts, partContent.Strip())
							}
							currentPart = []interface{}{}
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

func (s *Word) GetCondFormattedValue() string {
	value := s.expandAllAnsiCQuotes(s.Value)
	value = s.stripLocaleStringDollars(value)
	value = s.formatCommandSubstitutions(value, false)
	value = s.normalizeExtglobWhitespace(value)
	value = value.Replace("", "")
	return value.Rstrip("\n")
}

type Command struct {
	Words     []Node
	Redirects []Node
	Kind      string
}

func (s *Command) ToSexp() string {
	parts := []interface{}{}
	for _, w := range s.Words {
		parts = append(parts, w.ToSexp())
	}
	for _, r := range s.Redirects {
		parts = append(parts, r.ToSexp())
	}
	inner := strings.Join(parts, " ")
	if !inner != nil {
		return "(command)"
	}
	return (("(command " + inner) + ")")
}

type Pipeline struct {
	Commands []Node
	Kind     string
}

func (s *Pipeline) ToSexp() string {
	var result interface{}
	if len(s.Commands) == 1 {
		return s.Commands[0].ToSexp()
	}
	cmds := []interface{}{}
	i := 0
	for i < len(s.Commands) {
		cmd := s.Commands[i]
		if cmd.Kind == "pipe-both" {
			i += 1
			continue
		}
		needsRedirect := (((i + 1) < len(s.Commands)) && (s.Commands[(i+1)].Kind == "pipe-both"))
		cmds = append(cmds, struct{ Single, Double bool }{cmd, needsRedirect})
		i += 1
	}
	if len(cmds) == 1 {
		pair := cmds[0]
		cmd = pair[0]
		needs := pair[1]
		return s.cmdSexp(cmd, needs)
	}
	lastPair := cmds[(len(cmds) - 1)]
	lastCmd := lastPair[0]
	lastNeeds := lastPair[1]
	result = s.cmdSexp(lastCmd, lastNeeds)
	j := (len(cmds) - 2)
	for j >= 0 {
		pair = cmds[j]
		cmd = pair[0]
		needs = pair[1]
		if needs != nil && (cmd.Kind != "command") {
			result = (((("(pipe " + cmd.ToSexp()) + " (redirect \">&\" 1) ") + result) + ")")
		} else {
			result = (((("(pipe " + s.cmdSexp(cmd, needs)) + " ") + result) + ")")
		}
		j -= 1
	}
	return result
}

func (s *Pipeline) cmdSexp(cmd Node, needsRedirect bool) string {
	if !needsRedirect {
		return cmd.ToSexp()
	}
	if cmd.Kind == "command" {
		parts := []interface{}{}
		for _, w := range cmd.Words {
			parts = append(parts, w.ToSexp())
		}
		for _, r := range cmd.Redirects {
			parts = append(parts, r.ToSexp())
		}
		parts = append(parts, "(redirect \">&\" 1)")
		return (("(command " + strings.Join(parts, " ")) + ")")
	}
	return cmd.ToSexp()
}

type List struct {
	Parts []Node
	Kind  string
}

func (s *List) ToSexp() string {
	var leftSexp interface{}
	var rightSexp interface{}
	parts := append(s.Parts[:0:0], s.Parts...)
	opNames := map[string]interface{}{"&&": "and", "||": "or", ";": "semi", "\n": "semi", "&": "background"}
	for ((len(parts) > 1) && (parts[(len(parts)-1)].Kind == "operator")) && ((parts[(len(parts)-1)].Op == ";") || (parts[(len(parts)-1)].Op == "\n")) {
		parts = sublist(parts, 0, (len(parts) - 1))
	}
	if len(parts) == 1 {
		return parts[0].ToSexp()
	}
	if (parts[(len(parts)-1)].Kind == "operator") && (parts[(len(parts)-1)].Op == "&") {
		for _, i := range Range((len(parts) - 3), 0, -2) {
			if (parts[i].Kind == "operator") && ((parts[i].Op == ";") || (parts[i].Op == "\n")) {
				left := sublist(parts, 0, i)
				right := sublist(parts, (i + 1), (len(parts) - 1))
				if len(left) > 1 {
					leftSexp = &List{Parts: left}.ToSexp()
				} else {
					leftSexp = left[0].ToSexp()
				}
				if len(right) > 1 {
					rightSexp = &List{Parts: right}.ToSexp()
				} else {
					rightSexp = right[0].ToSexp()
				}
				return (((("(semi " + leftSexp) + " (background ") + rightSexp) + "))")
			}
		}
		innerParts := sublist(parts, 0, (len(parts) - 1))
		if len(innerParts) == 1 {
			return (("(background " + innerParts[0].ToSexp()) + ")")
		}
		innerList := &List{Parts: innerParts}
		return (("(background " + innerList.ToSexp()) + ")")
	}
	return s.toSexpWithPrecedence(parts, opNames)
}

func (s *List) toSexpWithPrecedence(parts []Node, opNames map[string]string) string {
	semiPositions := []interface{}{}
	for _, i := range Range(len(parts)) {
		if (parts[i].Kind == "operator") && ((parts[i].Op == ";") || (parts[i].Op == "\n")) {
			semiPositions = append(semiPositions, i)
		}
	}
	if semiPositions != nil {
		segments := []interface{}{}
		start := 0
		for _, pos := range semiPositions {
			seg := sublist(parts, start, pos)
			if seg != nil && (seg[0].Kind != "operator") {
				segments = append(segments, seg)
			}
			start = (pos + 1)
		}
		seg = sublist(parts, start, len(parts))
		if seg != nil && (seg[0].Kind != "operator") {
			segments = append(segments, seg)
		}
		if !segments != nil {
			return "()"
		}
		result := s.toSexpAmpAndHigher(segments[0], opNames)
		for _, i := range Range(1, len(segments)) {
			result = (((("(semi " + result) + " ") + s.toSexpAmpAndHigher(segments[i], opNames)) + ")")
		}
		return result
	}
	return s.toSexpAmpAndHigher(parts, opNames)
}

func (s *List) toSexpAmpAndHigher(parts []Node, opNames map[string]string) string {
	if len(parts) == 1 {
		return parts[0].ToSexp()
	}
	ampPositions := []interface{}{}
	for _, i := range Range(1, (len(parts) - 1), 2) {
		if (parts[i].Kind == "operator") && (parts[i].Op == "&") {
			ampPositions = append(ampPositions, i)
		}
	}
	if ampPositions != nil {
		segments := []interface{}{}
		start := 0
		for _, pos := range ampPositions {
			segments = append(segments, sublist(parts, start, pos))
			start = (pos + 1)
		}
		segments = append(segments, sublist(parts, start, len(parts)))
		result := s.toSexpAndOr(segments[0], opNames)
		for _, i := range Range(1, len(segments)) {
			result = (((("(background " + result) + " ") + s.toSexpAndOr(segments[i], opNames)) + ")")
		}
		return result
	}
	return s.toSexpAndOr(parts, opNames)
}

func (s *List) toSexpAndOr(parts []Node, opNames map[string]string) string {
	if len(parts) == 1 {
		return parts[0].ToSexp()
	}
	result := parts[0].ToSexp()
	for _, i := range Range(1, (len(parts) - 1), 2) {
		op := parts[i]
		cmd := parts[(i + 1)]
		opName := opNames.Get(op.Op, op.Op)
		result = (((((("(" + opName) + " ") + result) + " ") + cmd.ToSexp()) + ")")
	}
	return result
}

type Operator struct {
	Op   string
	Kind string
}

func (s *Operator) ToSexp() string {
	names := map[string]interface{}{"&&": "and", "||": "or", ";": "semi", "&": "bg", "|": "pipe"}
	return (("(" + names.Get(s.Op, s.Op)) + ")")
}

type PipeBoth struct {
	Kind string
}

func (s *PipeBoth) ToSexp() string {
	return "(pipe-both)"
}

type Empty struct {
	Kind string
}

func (s *Empty) ToSexp() string {
	return ""
}

type Comment struct {
	Text string
	Kind string
}

func (s *Comment) ToSexp() string {
	return ""
}

type Redirect struct {
	Op     string
	Target Node
	Fd     *int
	Kind   string
}

func (s *Redirect) ToSexp() string {
	var op string
	op = s.Op.Lstrip("0123456789")
	if op.Startswith("{") {
		j := 1
		if (j < len(op)) && (string(op[j]).Isalpha() || (string(op[j]) == "_")) {
			j += 1
			for (j < len(op)) && (string(op[j]).Isalnum() || (string(op[j]) == "_")) {
				j += 1
			}
			if (j < len(op)) && (string(op[j]) == "[") {
				j += 1
				for (j < len(op)) && (string(op[j]) != "]") {
					j += 1
				}
				if (j < len(op)) && (string(op[j]) == "]") {
					j += 1
				}
			}
			if (j < len(op)) && (string(op[j]) == "}") {
				op = substring(op, (j + 1), len(op))
			}
		}
	}
	targetVal := s.Target.Value
	targetVal = s.Target.expandAllAnsiCQuotes(targetVal)
	targetVal = s.Target.stripLocaleStringDollars(targetVal)
	targetVal = s.Target.formatCommandSubstitutions(targetVal)
	targetVal = s.Target.stripArithLineContinuations(targetVal)
	if targetVal.Endswith("\\") && !targetVal.Endswith("\\\\") {
		targetVal = (targetVal + "\\")
	}
	if targetVal.Startswith("&") {
		if op == ">" {
			op = ">&"
		} else if op == "<" {
			op = "<&"
		}
		raw := substring(targetVal, 1, len(targetVal))
		if raw.Isdigit() && (Int(raw) <= 2147483647) {
			return (((("(redirect \"" + op) + "\" ") + Str(Int(raw))) + ")")
		}
		if (raw.Endswith("-") && raw[:-1].Isdigit()) && (Int(raw[:-1]) <= 2147483647) {
			return (((("(redirect \"" + op) + "\" ") + Str(Int(raw[:-1]))) + ")")
		}
		if targetVal == "&-" {
			return "(redirect \">&-\" 0)"
		}
		fdTarget := func() interface{} {
			if raw.Endswith("-") {
				return raw[:-1]
			} else {
				return raw
			}
		}()
		return (((("(redirect \"" + op) + "\" \"") + fdTarget) + "\")")
	}
	if (op == ">&") || (op == "<&") {
		if targetVal.Isdigit() && (Int(targetVal) <= 2147483647) {
			return (((("(redirect \"" + op) + "\" ") + Str(Int(targetVal))) + ")")
		}
		if targetVal == "-" {
			return "(redirect \">&-\" 0)"
		}
		if (targetVal.Endswith("-") && targetVal[:-1].Isdigit()) && (Int(targetVal[:-1]) <= 2147483647) {
			return (((("(redirect \"" + op) + "\" ") + Str(Int(targetVal[:-1]))) + ")")
		}
		outVal := func() interface{} {
			if targetVal.Endswith("-") {
				return targetVal[:-1]
			} else {
				return targetVal
			}
		}()
		return (((("(redirect \"" + op) + "\" \"") + outVal) + "\")")
	}
	return (((("(redirect \"" + op) + "\" \"") + targetVal) + "\")")
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

func (s *HereDoc) ToSexp() string {
	op := func() string {
		if s.StripTabs {
			return "<<-"
		} else {
			return "<<"
		}
	}()
	content := s.Content
	if content.Endswith("\\") && !content.Endswith("\\\\") {
		content = (content + "\\")
	}
	return fmt.Sprintf("(redirect \"%v\" \"%v\")", op, content)
}

type Subshell struct {
	Body      Node
	Redirects *[]Node
	Kind      string
}

func (s *Subshell) ToSexp() string {
	base := (("(subshell " + s.Body.ToSexp()) + ")")
	return appendRedirects(base, s.Redirects)
}

type BraceGroup struct {
	Body      Node
	Redirects *[]Node
	Kind      string
}

func (s *BraceGroup) ToSexp() string {
	base := (("(brace-group " + s.Body.ToSexp()) + ")")
	return appendRedirects(base, s.Redirects)
}

type If struct {
	Condition Node
	ThenBody  Node
	ElseBody  *Node
	Redirects []Node
	Kind      string
}

func (s *If) ToSexp() string {
	result := ((("(if " + s.Condition.ToSexp()) + " ") + s.ThenBody.ToSexp())
	if s.ElseBody != nil {
		result = ((result + " ") + s.ElseBody.ToSexp())
	}
	result = (result + ")")
	for _, r := range s.Redirects {
		result = ((result + " ") + r.ToSexp())
	}
	return result
}

type While struct {
	Condition Node
	Body      Node
	Redirects []Node
	Kind      string
}

func (s *While) ToSexp() string {
	base := (((("(while " + s.Condition.ToSexp()) + " ") + s.Body.ToSexp()) + ")")
	return appendRedirects(base, s.Redirects)
}

type Until struct {
	Condition Node
	Body      Node
	Redirects []Node
	Kind      string
}

func (s *Until) ToSexp() string {
	base := (((("(until " + s.Condition.ToSexp()) + " ") + s.Body.ToSexp()) + ")")
	return appendRedirects(base, s.Redirects)
}

type For struct {
	Var       string
	Words     *[]Node
	Body      Node
	Redirects []Node
	Kind      string
}

func (s *For) ToSexp() string {
	suffix := ""
	if s.Redirects != nil {
		redirectParts := []interface{}{}
		for _, r := range s.Redirects {
			redirectParts = append(redirectParts, r.ToSexp())
		}
		suffix = (" " + strings.Join(redirectParts, " "))
	}
	tempWord := &Word{Value: s.Var, Parts: []interface{}{}}
	varFormatted := tempWord.formatCommandSubstitutions(s.Var)
	varEscaped := varFormatted.Replace("\\", "\\\\").Replace("\"", "\\\"")
	if s.Words == nil {
		return ((((("(for (word \"" + varEscaped) + "\") (in (word \"\\\"$@\\\"\")) ") + s.Body.ToSexp()) + ")") + suffix)
	} else if len(s.Words) == 0 {
		return ((((("(for (word \"" + varEscaped) + "\") (in) ") + s.Body.ToSexp()) + ")") + suffix)
	} else {
		wordParts := []interface{}{}
		for _, w := range s.Words {
			wordParts = append(wordParts, w.ToSexp())
		}
		wordStrs := strings.Join(wordParts, " ")
		return ((((((("(for (word \"" + varEscaped) + "\") (in ") + wordStrs) + ") ") + s.Body.ToSexp()) + ")") + suffix)
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

func (s *ForArith) ToSexp() string {
	suffix := ""
	if s.Redirects != nil {
		redirectParts := []interface{}{}
		for _, r := range s.Redirects {
			redirectParts = append(redirectParts, r.ToSexp())
		}
		suffix = (" " + strings.Join(redirectParts, " "))
	}
	initVal := func() string {
		if s.Init {
			return s.Init
		} else {
			return "1"
		}
	}()
	condVal := func() string {
		if s.Cond {
			return s.Cond
		} else {
			return "1"
		}
	}()
	incrVal := func() string {
		if s.Incr {
			return s.Incr
		} else {
			return "1"
		}
	}()
	initStr := formatArithVal(initVal)
	condStr := formatArithVal(condVal)
	incrStr := formatArithVal(incrVal)
	bodyStr := s.Body.ToSexp()
	return fmt.Sprintf("(arith-for (init (word \"%v\")) (test (word \"%v\")) (step (word \"%v\")) %v)%v", initStr, condStr, incrStr, bodyStr, suffix)
}

type Select struct {
	Var       string
	Words     *[]Node
	Body      Node
	Redirects []Node
	Kind      string
}

func (s *Select) ToSexp() string {
	var inClause interface{}
	suffix := ""
	if s.Redirects != nil {
		redirectParts := []interface{}{}
		for _, r := range s.Redirects {
			redirectParts = append(redirectParts, r.ToSexp())
		}
		suffix = (" " + strings.Join(redirectParts, " "))
	}
	varEscaped := s.Var.Replace("\\", "\\\\").Replace("\"", "\\\"")
	if s.Words != nil {
		wordParts := []interface{}{}
		for _, w := range s.Words {
			wordParts = append(wordParts, w.ToSexp())
		}
		wordStrs := strings.Join(wordParts, " ")
		if s.Words != nil {
			inClause = (("(in " + wordStrs) + ")")
		} else {
			inClause = "(in)"
		}
	} else {
		inClause = "(in (word \"\\\"$@\\\"\"))"
	}
	return ((((((("(select (word \"" + varEscaped) + "\") ") + inClause) + " ") + s.Body.ToSexp()) + ")") + suffix)
}

type Case struct {
	Word      Node
	Patterns  []Node
	Redirects []Node
	Kind      string
}

func (s *Case) ToSexp() string {
	parts := []interface{}{}
	parts = append(parts, ("(case " + s.Word.ToSexp()))
	for _, p := range s.Patterns {
		parts = append(parts, p.ToSexp())
	}
	base := (strings.Join(parts, " ") + ")")
	return appendRedirects(base, s.Redirects)
}

type CasePattern struct {
	Pattern    string
	Body       *Node
	Terminator string
	Kind       string
}

func (s *CasePattern) ToSexp() string {
	var result interface{}
	var i interface{}
	alternatives := []interface{}{}
	current := []interface{}{}
	i = 0
	depth := 0
	for i < len(s.Pattern) {
		ch := string(s.Pattern[i])
		if (ch == "\\") && ((i + 1) < len(s.Pattern)) {
			current = append(current, substring(s.Pattern, i, (i+2)))
			i += 2
		} else if ((((((ch == "@") || (ch == "?")) || (ch == "*")) || (ch == "+")) || (ch == "!")) && ((i + 1) < len(s.Pattern))) && (string(s.Pattern[(i+1)]) == "(") {
			current = append(current, ch)
			current = append(current, "(")
			depth += 1
			i += 2
		} else if isExpansionStart(s.Pattern, i, "$(") {
			current = append(current, ch)
			current = append(current, "(")
			depth += 1
			i += 2
		} else if (ch == "(") && (depth > 0) {
			current = append(current, ch)
			depth += 1
			i += 1
		} else if (ch == ")") && (depth > 0) {
			current = append(current, ch)
			depth -= 1
			i += 1
		} else if ch == "[" {
			result = consumeBracketClass(s.Pattern, i, depth)
			i = result[0]
			current.Extend(result[1])
		} else if (ch == "'") && (depth == 0) {
			result = consumeSingleQuote(s.Pattern, i)
			i = result[0]
			current.Extend(result[1])
		} else if (ch == "\"") && (depth == 0) {
			result = consumeDoubleQuote(s.Pattern, i)
			i = result[0]
			current.Extend(result[1])
		} else if (ch == "|") && (depth == 0) {
			alternatives = append(alternatives, strings.Join(current, ""))
			current = []interface{}{}
			i += 1
		} else {
			current = append(current, ch)
			i += 1
		}
	}
	alternatives = append(alternatives, strings.Join(current, ""))
	wordList := []interface{}{}
	for _, alt := range alternatives {
		wordList = append(wordList, &Word{Value: alt}.ToSexp())
	}
	patternStr := strings.Join(wordList, " ")
	parts := []interface{}{(("(pattern (" + patternStr) + ")")}
	if s.Body != nil {
		parts = append(parts, (" " + s.Body.ToSexp()))
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

func (s *Function) ToSexp() string {
	return (((("(function \"" + s.Name) + "\" ") + s.Body.ToSexp()) + ")")
}

type ParamExpansion struct {
	Param string
	Op    *string
	Arg   *string
	Kind  string
}

func (s *ParamExpansion) ToSexp() string {
	var argVal interface{}
	escapedParam := s.Param.Replace("\\", "\\\\").Replace("\"", "\\\"")
	if s.Op != nil {
		escapedOp := s.Op.Replace("\\", "\\\\").Replace("\"", "\\\"")
		if s.Arg != nil {
			argVal = s.Arg
		} else {
			argVal = ""
		}
		escapedArg := argVal.Replace("\\", "\\\\").Replace("\"", "\\\"")
		return (((((("(param \"" + escapedParam) + "\" \"") + escapedOp) + "\" \"") + escapedArg) + "\")")
	}
	return (("(param \"" + escapedParam) + "\")")
}

type ParamLength struct {
	Param string
	Kind  string
}

func (s *ParamLength) ToSexp() string {
	escaped := s.Param.Replace("\\", "\\\\").Replace("\"", "\\\"")
	return (("(param-len \"" + escaped) + "\")")
}

type ParamIndirect struct {
	Param string
	Op    *string
	Arg   *string
	Kind  string
}

func (s *ParamIndirect) ToSexp() string {
	var argVal interface{}
	escaped := s.Param.Replace("\\", "\\\\").Replace("\"", "\\\"")
	if s.Op != nil {
		escapedOp := s.Op.Replace("\\", "\\\\").Replace("\"", "\\\"")
		if s.Arg != nil {
			argVal = s.Arg
		} else {
			argVal = ""
		}
		escapedArg := argVal.Replace("\\", "\\\\").Replace("\"", "\\\"")
		return (((((("(param-indirect \"" + escaped) + "\" \"") + escapedOp) + "\" \"") + escapedArg) + "\")")
	}
	return (("(param-indirect \"" + escaped) + "\")")
}

type CommandSubstitution struct {
	Command Node
	Brace   bool
	Kind    string
}

func (s *CommandSubstitution) ToSexp() string {
	if s.Brace {
		return (("(funsub " + s.Command.ToSexp()) + ")")
	}
	return (("(cmdsub " + s.Command.ToSexp()) + ")")
}

type ArithmeticExpansion struct {
	Expression *Node
	Kind       string
}

func (s *ArithmeticExpansion) ToSexp() string {
	if s.Expression == nil {
		return "(arith)"
	}
	return (("(arith " + s.Expression.ToSexp()) + ")")
}

type ArithmeticCommand struct {
	Expression *Node
	Redirects  []Node
	RawContent string
	Kind       string
}

func (s *ArithmeticCommand) ToSexp() string {
	formatted := &Word{Value: s.RawContent}.formatCommandSubstitutions(s.RawContent)
	escaped := formatted.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", "\\n").Replace("\t", "\\t")
	result := (("(arith (word \"" + escaped) + "\"))")
	if s.Redirects != nil {
		redirectParts := []interface{}{}
		for _, r := range s.Redirects {
			redirectParts = append(redirectParts, r.ToSexp())
		}
		redirectSexps := strings.Join(redirectParts, " ")
		return ((result + " ") + redirectSexps)
	}
	return result
}

type ArithNumber struct {
	Value string
	Kind  string
}

func (s *ArithNumber) ToSexp() string {
	return (("(number \"" + s.Value) + "\")")
}

type ArithEmpty struct {
	Kind string
}

func (s *ArithEmpty) ToSexp() string {
	return "(empty)"
}

type ArithVar struct {
	Name string
	Kind string
}

func (s *ArithVar) ToSexp() string {
	return (("(var \"" + s.Name) + "\")")
}

type ArithBinaryOp struct {
	Op    string
	Left  Node
	Right Node
	Kind  string
}

func (s *ArithBinaryOp) ToSexp() string {
	return (((((("(binary-op \"" + s.Op) + "\" ") + s.Left.ToSexp()) + " ") + s.Right.ToSexp()) + ")")
}

type ArithUnaryOp struct {
	Op      string
	Operand Node
	Kind    string
}

func (s *ArithUnaryOp) ToSexp() string {
	return (((("(unary-op \"" + s.Op) + "\" ") + s.Operand.ToSexp()) + ")")
}

type ArithPreIncr struct {
	Operand Node
	Kind    string
}

func (s *ArithPreIncr) ToSexp() string {
	return (("(pre-incr " + s.Operand.ToSexp()) + ")")
}

type ArithPostIncr struct {
	Operand Node
	Kind    string
}

func (s *ArithPostIncr) ToSexp() string {
	return (("(post-incr " + s.Operand.ToSexp()) + ")")
}

type ArithPreDecr struct {
	Operand Node
	Kind    string
}

func (s *ArithPreDecr) ToSexp() string {
	return (("(pre-decr " + s.Operand.ToSexp()) + ")")
}

type ArithPostDecr struct {
	Operand Node
	Kind    string
}

func (s *ArithPostDecr) ToSexp() string {
	return (("(post-decr " + s.Operand.ToSexp()) + ")")
}

type ArithAssign struct {
	Op     string
	Target Node
	Value  Node
	Kind   string
}

func (s *ArithAssign) ToSexp() string {
	return (((((("(assign \"" + s.Op) + "\" ") + s.Target.ToSexp()) + " ") + s.Value.ToSexp()) + ")")
}

type ArithTernary struct {
	Condition Node
	IfTrue    Node
	IfFalse   Node
	Kind      string
}

func (s *ArithTernary) ToSexp() string {
	return (((((("(ternary " + s.Condition.ToSexp()) + " ") + s.IfTrue.ToSexp()) + " ") + s.IfFalse.ToSexp()) + ")")
}

type ArithComma struct {
	Left  Node
	Right Node
	Kind  string
}

func (s *ArithComma) ToSexp() string {
	return (((("(comma " + s.Left.ToSexp()) + " ") + s.Right.ToSexp()) + ")")
}

type ArithSubscript struct {
	Array string
	Index Node
	Kind  string
}

func (s *ArithSubscript) ToSexp() string {
	return (((("(subscript \"" + s.Array) + "\" ") + s.Index.ToSexp()) + ")")
}

type ArithEscape struct {
	Char string
	Kind string
}

func (s *ArithEscape) ToSexp() string {
	return (("(escape \"" + s.Char) + "\")")
}

type ArithDeprecated struct {
	Expression string
	Kind       string
}

func (s *ArithDeprecated) ToSexp() string {
	escaped := s.Expression.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", "\\n")
	return (("(arith-deprecated \"" + escaped) + "\")")
}

type ArithConcat struct {
	Parts []Node
	Kind  string
}

func (s *ArithConcat) ToSexp() string {
	sexps := []interface{}{}
	for _, p := range s.Parts {
		sexps = append(sexps, p.ToSexp())
	}
	return (("(arith-concat " + strings.Join(sexps, " ")) + ")")
}

type AnsiCQuote struct {
	Content string
	Kind    string
}

func (s *AnsiCQuote) ToSexp() string {
	escaped := s.Content.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", "\\n")
	return (("(ansi-c \"" + escaped) + "\")")
}

type LocaleString struct {
	Content string
	Kind    string
}

func (s *LocaleString) ToSexp() string {
	escaped := s.Content.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", "\\n")
	return (("(locale \"" + escaped) + "\")")
}

type ProcessSubstitution struct {
	Direction string
	Command   Node
	Kind      string
}

func (s *ProcessSubstitution) ToSexp() string {
	return (((("(procsub \"" + s.Direction) + "\" ") + s.Command.ToSexp()) + ")")
}

type Negation struct {
	Pipeline Node
	Kind     string
}

func (s *Negation) ToSexp() string {
	if s.Pipeline == nil {
		return "(negation (command))"
	}
	return (("(negation " + s.Pipeline.ToSexp()) + ")")
}

type Time struct {
	Pipeline Node
	Posix    bool
	Kind     string
}

func (s *Time) ToSexp() string {
	if s.Pipeline == nil {
		if s.Posix {
			return "(time -p (command))"
		} else {
			return "(time (command))"
		}
	}
	if s.Posix {
		return (("(time -p " + s.Pipeline.ToSexp()) + ")")
	}
	return (("(time " + s.Pipeline.ToSexp()) + ")")
}

type ConditionalExpr struct {
	Body      interface{}
	Redirects []Node
	Kind      string
}

func (s *ConditionalExpr) ToSexp() string {
	var result interface{}
	body := s.Body
	if Isinstance(body, str) {
		escaped := body.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", "\\n")
		result = (("(cond \"" + escaped) + "\")")
	} else {
		result = (("(cond " + body.ToSexp()) + ")")
	}
	if s.Redirects != nil {
		redirectParts := []interface{}{}
		for _, r := range s.Redirects {
			redirectParts = append(redirectParts, r.ToSexp())
		}
		redirectSexps := strings.Join(redirectParts, " ")
		return ((result + " ") + redirectSexps)
	}
	return result
}

type UnaryTest struct {
	Op      string
	Operand Node
	Kind    string
}

func (s *UnaryTest) ToSexp() string {
	operandVal := s.Operand.GetCondFormattedValue()
	return (((("(cond-unary \"" + s.Op) + "\" (cond-term \"") + operandVal) + "\"))")
}

type BinaryTest struct {
	Op    string
	Left  Node
	Right Node
	Kind  string
}

func (s *BinaryTest) ToSexp() string {
	leftVal := s.Left.GetCondFormattedValue()
	rightVal := s.Right.GetCondFormattedValue()
	return (((((("(cond-binary \"" + s.Op) + "\" (cond-term \"") + leftVal) + "\") (cond-term \"") + rightVal) + "\"))")
}

type CondAnd struct {
	Left  Node
	Right Node
	Kind  string
}

func (s *CondAnd) ToSexp() string {
	return (((("(cond-and " + s.Left.ToSexp()) + " ") + s.Right.ToSexp()) + ")")
}

type CondOr struct {
	Left  Node
	Right Node
	Kind  string
}

func (s *CondOr) ToSexp() string {
	return (((("(cond-or " + s.Left.ToSexp()) + " ") + s.Right.ToSexp()) + ")")
}

type CondNot struct {
	Operand Node
	Kind    string
}

func (s *CondNot) ToSexp() string {
	return s.Operand.ToSexp()
}

type CondParen struct {
	Inner Node
	Kind  string
}

func (s *CondParen) ToSexp() string {
	return (("(cond-expr " + s.Inner.ToSexp()) + ")")
}

type Array struct {
	Elements []Node
	Kind     string
}

func (s *Array) ToSexp() string {
	if !s.Elements != nil {
		return "(array)"
	}
	parts := []interface{}{}
	for _, e := range s.Elements {
		parts = append(parts, e.ToSexp())
	}
	inner := strings.Join(parts, " ")
	return (("(array " + inner) + ")")
}

type Coproc struct {
	Command Node
	Name    *string
	Kind    string
}

func (s *Coproc) ToSexp() string {
	var name interface{}
	if s.Name != nil {
		name = s.Name
	} else {
		name = "COPROC"
	}
	return (((("(coproc \"" + name) + "\" ") + s.Command.ToSexp()) + ")")
}

type Parser struct {
	Source                  string
	Pos                     int
	Length                  int
	pendingHeredocs         []Node
	cmdsubHeredocEnd        *int
	sawNewlineInSingleQuote bool
	inProcessSub            bool
	extglob                 bool
	ctx                     *ContextStack
	lexer                   *Lexer
	tokenHistory            []*Token
	parserState             int
	dolbraceState           int
	eofToken                *string
	wordContext             int
	atCommandStart          bool
	inArrayLiteral          bool
	inAssignBuiltin         bool
	arithSrc                string
	arithPos                int
	arithLen                int
}

func (s *Parser) setState(flag int) {
	s.parserState = (s.parserState | flag)
}

func (s *Parser) clearState(flag int) {
	s.parserState = (s.parserState & ~flag)
}

func (s *Parser) inState(flag int) bool {
	return ((s.parserState & flag) != 0)
}

func (s *Parser) saveParserState() *SavedParserState {
	return &SavedParserState{}
}

func (s *Parser) restoreParserState(saved *SavedParserState) {
	s.parserState = saved.ParserState
	s.dolbraceState = saved.DolbraceState
	s.eofToken = saved.EofToken
	s.ctx.RestoreFrom(saved.CtxStack)
}

func (s *Parser) recordToken(tok *Token) {
	s.tokenHistory = []*Token{tok, s.tokenHistory[0], s.tokenHistory[1], s.tokenHistory[2]}
}

func (s *Parser) updateDolbraceForOp(op *string, hasParam bool) {
	if s.dolbraceState == DolbracestateNone {
		return
	}
	if op == nil || (len(op) == 0) {
		return
	}
	firstChar := op[0]
	if (s.dolbraceState == DolbracestateParam) && hasParam {
		if strings.Contains("%#^,", firstChar) {
			s.dolbraceState = DolbracestateQuote
			return
		}
		if firstChar == "/" {
			s.dolbraceState = DolbracestateQuote2
			return
		}
	}
	if s.dolbraceState == DolbracestateParam {
		if strings.Contains("#%^,~:-=?+/", firstChar) {
			s.dolbraceState = DolbracestateOp
		}
	}
}

func (s *Parser) syncLexer() {
	if s.lexer.tokenCache != nil {
		if ((((s.lexer.tokenCache.Pos != s.Pos) || (s.lexer.cachedWordContext != s.wordContext)) || (s.lexer.cachedAtCommandStart != s.atCommandStart)) || (s.lexer.cachedInArrayLiteral != s.inArrayLiteral)) || (s.lexer.cachedInAssignBuiltin != s.inAssignBuiltin) {
			s.lexer.tokenCache = nil
		}
	}
	if s.lexer.Pos != s.Pos {
		s.lexer.Pos = s.Pos
	}
	s.lexer.eofToken = s.eofToken
	s.lexer.parserState = s.parserState
	s.lexer.lastReadToken = s.tokenHistory[0]
	s.lexer.wordContext = s.wordContext
	s.lexer.atCommandStart = s.atCommandStart
	s.lexer.inArrayLiteral = s.inArrayLiteral
	s.lexer.inAssignBuiltin = s.inAssignBuiltin
}

func (s *Parser) syncParser() {
	s.Pos = s.lexer.Pos
}

func (s *Parser) lexPeekToken() *Token {
	if ((((s.lexer.tokenCache != nil && (s.lexer.tokenCache.Pos == s.Pos)) && (s.lexer.cachedWordContext == s.wordContext)) && (s.lexer.cachedAtCommandStart == s.atCommandStart)) && (s.lexer.cachedInArrayLiteral == s.inArrayLiteral)) && (s.lexer.cachedInAssignBuiltin == s.inAssignBuiltin) {
		return s.lexer.tokenCache
	}
	savedPos := s.Pos
	s.syncLexer()
	result := s.lexer.PeekToken()
	s.lexer.cachedWordContext = s.wordContext
	s.lexer.cachedAtCommandStart = s.atCommandStart
	s.lexer.cachedInArrayLiteral = s.inArrayLiteral
	s.lexer.cachedInAssignBuiltin = s.inAssignBuiltin
	s.lexer.postReadPos = s.lexer.Pos
	s.Pos = savedPos
	return result
}

func (s *Parser) lexNextToken() *Token {
	var tok *Token
	if ((((s.lexer.tokenCache != nil && (s.lexer.tokenCache.Pos == s.Pos)) && (s.lexer.cachedWordContext == s.wordContext)) && (s.lexer.cachedAtCommandStart == s.atCommandStart)) && (s.lexer.cachedInArrayLiteral == s.inArrayLiteral)) && (s.lexer.cachedInAssignBuiltin == s.inAssignBuiltin) {
		tok = s.lexer.NextToken()
		s.Pos = s.lexer.postReadPos
		s.lexer.Pos = s.lexer.postReadPos
	} else {
		s.syncLexer()
		tok = s.lexer.NextToken()
		s.lexer.cachedWordContext = s.wordContext
		s.lexer.cachedAtCommandStart = s.atCommandStart
		s.lexer.cachedInArrayLiteral = s.inArrayLiteral
		s.lexer.cachedInAssignBuiltin = s.inAssignBuiltin
		s.syncParser()
	}
	s.recordToken(tok)
	return tok
}

func (s *Parser) lexSkipBlanks() {
	s.syncLexer()
	s.lexer.SkipBlanks()
	s.syncParser()
}

func (s *Parser) lexSkipComment() bool {
	s.syncLexer()
	result := s.lexer.skipComment()
	s.syncParser()
	return result
}

func (s *Parser) lexIsCommandTerminator() bool {
	tok := s.lexPeekToken()
	t := tok.Type
	return strings.Contains(struct{}{F0: TokentypeEof, F1: TokentypeNewline, F2: TokentypePipe, F3: TokentypeSemi, F4: TokentypeLparen, F5: TokentypeRparen, F6: TokentypeAmp}, t)
}

func (s *Parser) lexPeekOperator() (int, string) {
	tok := s.lexPeekToken()
	t := tok.Type
	if ((t >= TokentypeSemi) && (t <= TokentypeGreater)) || ((t >= TokentypeAndAnd) && (t <= TokentypePipeAmp)) {
		return t, tok.Value
	}
	return 0, ""
}

func (s *Parser) lexPeekReservedWord() string {
	tok := s.lexPeekToken()
	if tok.Type != TokentypeWord {
		return ""
	}
	word := tok.Value
	if word.Endswith("\\\n") {
		word = word[:-2]
	}
	if strings.Contains(ReservedWords, word) || strings.Contains(struct{}{F0: "{", F1: "}", F2: "[[", F3: "]]", F4: "!", F5: "time"}, word) {
		return word
	}
	return ""
}

func (s *Parser) lexIsAtReservedWord(word string) bool {
	reserved := s.lexPeekReservedWord()
	return (reserved == word)
}

func (s *Parser) lexConsumeWord(expected string) bool {
	tok := s.lexPeekToken()
	if tok.Type != TokentypeWord {
		return false
	}
	word := tok.Value
	if word.Endswith("\\\n") {
		word = word[:-2]
	}
	if word == expected {
		s.lexNextToken()
		return true
	}
	return false
}

func (s *Parser) lexPeekCaseTerminator() string {
	tok := s.lexPeekToken()
	t := tok.Type
	if t == TokentypeSemiSemi {
		return ";;"
	}
	if t == TokentypeSemiAmp {
		return ";&"
	}
	if t == TokentypeSemiSemiAmp {
		return ";;&"
	}
	return ""
}

func (s *Parser) AtEnd() bool {
	return (s.Pos >= s.Length)
}

func (s *Parser) Peek() string {
	if s.AtEnd() {
		return ""
	}
	return string(s.Source[s.Pos])
}

func (s *Parser) Advance() string {
	if s.AtEnd() {
		return ""
	}
	ch := string(s.Source[s.Pos])
	s.Pos += 1
	return ch
}

func (s *Parser) PeekAt(offset int) string {
	pos := (s.Pos + offset)
	if (pos < 0) || (pos >= s.Length) {
		return ""
	}
	return string(s.Source[pos])
}

func (s *Parser) Lookahead(n int) string {
	return substring(s.Source, s.Pos, (s.Pos + n))
}

func (s *Parser) isBangFollowedByProcsub() bool {
	if (s.Pos + 2) >= s.Length {
		return false
	}
	nextChar := string(s.Source[(s.Pos + 1)])
	if (nextChar != ">") && (nextChar != "<") {
		return false
	}
	return (string(s.Source[(s.Pos+2)]) == "(")
}

func (s *Parser) SkipWhitespace() {
	for !s.AtEnd() {
		s.lexSkipBlanks()
		if s.AtEnd() {
			break
		}
		ch := s.Peek()
		if ch == "#" {
			s.lexSkipComment()
		} else if (ch == "\\") && (s.PeekAt(1) == "\n") {
			s.Advance()
			s.Advance()
		} else {
			break
		}
	}
}

func (s *Parser) SkipWhitespaceAndNewlines() {
	for !s.AtEnd() {
		ch := s.Peek()
		if isWhitespace(ch) {
			s.Advance()
			if ch == "\n" {
				s.gatherHeredocBodies()
				if s.cmdsubHeredocEnd != nil && (s.cmdsubHeredocEnd > s.Pos) {
					s.Pos = s.cmdsubHeredocEnd
					s.cmdsubHeredocEnd = nil
				}
			}
		} else if ch == "#" {
			for !s.AtEnd() && (s.Peek() != "\n") {
				s.Advance()
			}
		} else if (ch == "\\") && (s.PeekAt(1) == "\n") {
			s.Advance()
			s.Advance()
		} else {
			break
		}
	}
}

func (s *Parser) atListTerminatingBracket() bool {
	if s.AtEnd() {
		return false
	}
	ch := s.Peek()
	if s.eofToken != nil && (ch == *s.eofToken) {
		return true
	}
	if ch == ")" {
		return true
	}
	if ch == "}" {
		nextPos := (s.Pos + 1)
		if nextPos >= s.Length {
			return true
		}
		return isWordEndContext(string(s.Source[nextPos]))
	}
	return false
}

func (s *Parser) atEofToken() bool {
	if s.eofToken == nil {
		return false
	}
	tok := s.lexPeekToken()
	if *s.eofToken == ")" {
		return (tok.Type == TokentypeRparen)
	}
	if *s.eofToken == "}" {
		return ((tok.Type == TokentypeWord) && (tok.Value == "}"))
	}
	return false
}

func (s *Parser) collectRedirects() []Node {
	redirects := []interface{}{}
	for true {
		s.SkipWhitespace()
		redirect := s.ParseRedirect()
		if redirect == nil {
			break
		}
		redirects = append(redirects, redirect)
	}
	return func() interface{} {
		if redirects {
			return redirects
		} else {
			return nil
		}
	}()
}

func (s *Parser) parseLoopBody(context string) Node {
	if s.Peek() == "{" {
		brace := s.ParseBraceGroup()
		if brace == nil {
			panic(fmt.Sprintf("Expected brace group body in %v", context))
		}
		return brace.Body
	}
	if s.lexConsumeWord("do") {
		body := s.ParseListUntil(TodoSet)
		if body == nil {
			panic("Expected commands after 'do'")
		}
		s.SkipWhitespaceAndNewlines()
		if !s.lexConsumeWord("done") {
			panic(fmt.Sprintf("Expected 'done' to close %v", context))
		}
		return body
	}
	panic(fmt.Sprintf("Expected 'do' or '{' in %v", context))
}

func (s *Parser) PeekWord() string {
	var word interface{}
	savedPos := s.Pos
	s.SkipWhitespace()
	if s.AtEnd() || isMetachar(s.Peek()) {
		s.Pos = savedPos
		return ""
	}
	chars := []interface{}{}
	for !s.AtEnd() && !isMetachar(s.Peek()) {
		ch := s.Peek()
		if isQuote(ch) {
			break
		}
		if ((ch == "\\") && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "\n") {
			break
		}
		if (ch == "\\") && ((s.Pos + 1) < s.Length) {
			chars = append(chars, s.Advance())
			chars = append(chars, s.Advance())
			continue
		}
		chars = append(chars, s.Advance())
	}
	if chars != nil {
		word = strings.Join(chars, "")
	} else {
		word = nil
	}
	s.Pos = savedPos
	return word
}

func (s *Parser) ConsumeWord(expected string) bool {
	savedPos := s.Pos
	s.SkipWhitespace()
	word := s.PeekWord()
	keywordWord := word
	hasLeadingBrace := false
	if (((word != "") && s.inProcessSub) && (len(word) > 1)) && (string(word[0]) == "}") {
		keywordWord = word[1:]
		hasLeadingBrace = true
	}
	if keywordWord != expected {
		s.Pos = savedPos
		return false
	}
	s.SkipWhitespace()
	if hasLeadingBrace {
		s.Advance()
	}
	for range expected {
		s.Advance()
	}
	for ((s.Peek() == "\\") && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "\n") {
		s.Advance()
		s.Advance()
	}
	return true
}

func (s *Parser) isWordTerminator(ctx int, ch string, bracketDepth int, parenDepth int) bool {
	s.syncLexer()
	return s.lexer.isWordTerminator(ctx, ch, bracketDepth, parenDepth)
}

func (s *Parser) scanDoubleQuote(chars *[]string, parts *[]Node, start int, handleLineContinuation bool) {
	*chars = append(*chars, "\"")
	for !s.AtEnd() && (s.Peek() != "\"") {
		c := s.Peek()
		if (c == "\\") && ((s.Pos + 1) < s.Length) {
			nextC := string(s.Source[(s.Pos + 1)])
			if handleLineContinuation && (nextC == "\n") {
				s.Advance()
				s.Advance()
			} else {
				*chars = append(*chars, s.Advance())
				*chars = append(*chars, s.Advance())
			}
		} else if c == "$" {
			if !s.parseDollarExpansion(chars, parts, false) {
				*chars = append(*chars, s.Advance())
			}
		} else {
			*chars = append(*chars, s.Advance())
		}
	}
	if s.AtEnd() {
		panic("Unterminated double quote")
	}
	*chars = append(*chars, s.Advance())
}

func (s *Parser) parseDollarExpansion(chars *[]string, parts *[]Node, inDquote bool) bool {
	if (((s.Pos + 2) < s.Length) && (string(s.Source[(s.Pos+1)]) == "(")) && (string(s.Source[(s.Pos+2)]) == "(") {
		result := s.parseArithmeticExpansion()
		if result[0] != nil {
			*parts = append(*parts, result[0])
			*chars = append(*chars, result[1])
			return true
		}
		result = s.parseCommandSubstitution()
		if result[0] != nil {
			*parts = append(*parts, result[0])
			*chars = append(*chars, result[1])
			return true
		}
		return false
	}
	if ((s.Pos + 1) < s.Length) && (string(s.Source[(s.Pos+1)]) == "[") {
		result = s.parseDeprecatedArithmetic()
		if result[0] != nil {
			*parts = append(*parts, result[0])
			*chars = append(*chars, result[1])
			return true
		}
		return false
	}
	if ((s.Pos + 1) < s.Length) && (string(s.Source[(s.Pos+1)]) == "(") {
		result = s.parseCommandSubstitution()
		if result[0] != nil {
			*parts = append(*parts, result[0])
			*chars = append(*chars, result[1])
			return true
		}
		return false
	}
	result = s.parseParamExpansion(inDquote)
	if result[0] != nil {
		*parts = append(*parts, result[0])
		*chars = append(*chars, result[1])
		return true
	}
	return false
}

func (s *Parser) parseWordInternal(ctx int, atCommandStart bool, inArrayLiteral bool) *Word {
	s.wordContext = ctx
	return s.ParseWord(atCommandStart, inArrayLiteral, false)
}

func (s *Parser) ParseWord(atCommandStart bool, inArrayLiteral bool, inAssignBuiltin bool) *Word {
	s.SkipWhitespace()
	if s.AtEnd() {
		return nil
	}
	s.atCommandStart = atCommandStart
	s.inArrayLiteral = inArrayLiteral
	s.inAssignBuiltin = inAssignBuiltin
	tok := s.lexPeekToken()
	if tok.Type != TokentypeWord {
		s.atCommandStart = false
		s.inArrayLiteral = false
		s.inAssignBuiltin = false
		return nil
	}
	s.lexNextToken()
	s.atCommandStart = false
	s.inArrayLiteral = false
	s.inAssignBuiltin = false
	return tok.Word
}

func (s *Parser) parseCommandSubstitution() (*Node, string) {
	if s.AtEnd() || (s.Peek() != "$") {
		return nil, ""
	}
	start := s.Pos
	s.Advance()
	if s.AtEnd() || (s.Peek() != "(") {
		s.Pos = start
		return nil, ""
	}
	s.Advance()
	saved := s.saveParserState()
	s.setState((ParserstateflagsPstCmdsubst | ParserstateflagsPstEoftoken))
	s.eofToken = ")"
	cmd := s.ParseList(true)
	if cmd == nil {
		cmd = &Empty{}
	}
	s.SkipWhitespaceAndNewlines()
	if s.AtEnd() || (s.Peek() != ")") {
		s.restoreParserState(saved)
		s.Pos = start
		return nil, ""
	}
	s.Advance()
	textEnd := s.Pos
	text := substring(s.Source, start, textEnd)
	s.restoreParserState(saved)
	return &CommandSubstitution{Command: cmd}, text
}

func (s *Parser) parseFunsub(start int) (*Node, string) {
	s.syncParser()
	if !s.AtEnd() && (s.Peek() == "|") {
		s.Advance()
	}
	saved := s.saveParserState()
	s.setState((ParserstateflagsPstCmdsubst | ParserstateflagsPstEoftoken))
	s.eofToken = "}"
	cmd := s.ParseList(true)
	if cmd == nil {
		cmd = &Empty{}
	}
	s.SkipWhitespaceAndNewlines()
	if s.AtEnd() || (s.Peek() != "}") {
		s.restoreParserState(saved)
		panic("unexpected EOF looking for `}'")
	}
	s.Advance()
	text := substring(s.Source, start, s.Pos)
	s.restoreParserState(saved)
	s.syncLexer()
	return &CommandSubstitution{Command: cmd}, text
}

func (s *Parser) isAssignmentWord(word Node) bool {
	return (assignment(word.Value) != -1)
}

func (s *Parser) parseBacktickSubstitution() (*Node, string) {
	var inHeredocBody bool
	var pendingHeredocs interface{}
	var currentHeredocDelim bool
	var currentHeredocStrip bool
	var ch string
	var dch string
	var quote string
	var closing string
	var esc string
	if s.AtEnd() || (s.Peek() != "`") {
		return nil, ""
	}
	start := s.Pos
	s.Advance()
	var contentChars []string = []string{}
	textChars := []string{"`"}
	var pendingHeredocs []interface{} = []interface{}{}
	inHeredocBody = false
	currentHeredocDelim = ""
	currentHeredocStrip = false
	for !s.AtEnd() && (inHeredocBody || (s.Peek() != "`")) {
		if inHeredocBody {
			lineStart := s.Pos
			lineEnd := lineStart
			for (lineEnd < s.Length) && (string(s.Source[lineEnd]) != "\n") {
				lineEnd += 1
			}
			line := substring(s.Source, lineStart, lineEnd)
			checkLine := func() interface{} {
				if currentHeredocStrip {
					return line.Lstrip("\t")
				} else {
					return line
				}
			}()
			if checkLine == currentHeredocDelim {
				for _, ch := range line {
					contentChars = append(contentChars, ch)
					textChars = append(textChars, ch)
				}
				s.Pos = lineEnd
				if (s.Pos < s.Length) && (string(s.Source[s.Pos]) == "\n") {
					contentChars = append(contentChars, "\n")
					textChars = append(textChars, "\n")
					s.Advance()
				}
				inHeredocBody = false
				if len(pendingHeredocs) > 0 {
					{
						var entry quoteStackEntry = pendingHeredocs[(len(pendingHeredocs) - 1)]
						pendingHeredocs = pendingHeredocs[:(len(pendingHeredocs) - 1)]
						currentHeredocDelim = entry.Single
						currentHeredocStrip = entry.Double
					}
					inHeredocBody = true
				}
			} else if checkLine.Startswith(currentHeredocDelim) && (len(checkLine) > len(currentHeredocDelim)) {
				tabsStripped := (len(line) - len(checkLine))
				endPos := (tabsStripped + len(currentHeredocDelim))
				for _, i := range Range(endPos) {
					contentChars = append(contentChars, line[i])
					textChars = append(textChars, line[i])
				}
				s.Pos = (lineStart + endPos)
				inHeredocBody = false
				if len(pendingHeredocs) > 0 {
					{
						var entry quoteStackEntry = pendingHeredocs[(len(pendingHeredocs) - 1)]
						pendingHeredocs = pendingHeredocs[:(len(pendingHeredocs) - 1)]
						currentHeredocDelim = entry.Single
						currentHeredocStrip = entry.Double
					}
					inHeredocBody = true
				}
			} else {
				for _, ch := range line {
					contentChars = append(contentChars, ch)
					textChars = append(textChars, ch)
				}
				s.Pos = lineEnd
				if (s.Pos < s.Length) && (string(s.Source[s.Pos]) == "\n") {
					contentChars = append(contentChars, "\n")
					textChars = append(textChars, "\n")
					s.Advance()
				}
			}
			continue
		}
		c := s.Peek()
		if (c == "\\") && ((s.Pos + 1) < s.Length) {
			nextC := string(s.Source[(s.Pos + 1)])
			if nextC == "\n" {
				s.Advance()
				s.Advance()
			} else if isEscapeCharInBacktick(nextC) {
				s.Advance()
				escaped := s.Advance()
				contentChars = append(contentChars, escaped)
				textChars = append(textChars, "\\")
				textChars = append(textChars, escaped)
			} else {
				ch = s.Advance()
				contentChars = append(contentChars, ch)
				textChars = append(textChars, ch)
			}
			continue
		}
		if ((c == "<") && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "<") {
			if ((s.Pos + 2) < s.Length) && (string(s.Source[(s.Pos+2)]) == "<") {
				contentChars = append(contentChars, s.Advance())
				textChars = append(textChars, "<")
				contentChars = append(contentChars, s.Advance())
				textChars = append(textChars, "<")
				contentChars = append(contentChars, s.Advance())
				textChars = append(textChars, "<")
				for !s.AtEnd() && isWhitespaceNoNewline(s.Peek()) {
					ch = s.Advance()
					contentChars = append(contentChars, ch)
					textChars = append(textChars, ch)
				}
				for (!s.AtEnd() && !isWhitespace(s.Peek())) && !strings.Contains("()", s.Peek()) {
					if (s.Peek() == "\\") && ((s.Pos + 1) < s.Length) {
						ch = s.Advance()
						contentChars = append(contentChars, ch)
						textChars = append(textChars, ch)
						ch = s.Advance()
						contentChars = append(contentChars, ch)
						textChars = append(textChars, ch)
					} else if strings.Contains("\"'", s.Peek()) {
						quote = s.Peek()
						ch = s.Advance()
						contentChars = append(contentChars, ch)
						textChars = append(textChars, ch)
						for !s.AtEnd() && (s.Peek() != quote) {
							if (quote == "\"") && (s.Peek() == "\\") {
								ch = s.Advance()
								contentChars = append(contentChars, ch)
								textChars = append(textChars, ch)
							}
							ch = s.Advance()
							contentChars = append(contentChars, ch)
							textChars = append(textChars, ch)
						}
						if !s.AtEnd() {
							ch = s.Advance()
							contentChars = append(contentChars, ch)
							textChars = append(textChars, ch)
						}
					} else {
						ch = s.Advance()
						contentChars = append(contentChars, ch)
						textChars = append(textChars, ch)
					}
				}
				continue
			}
			contentChars = append(contentChars, s.Advance())
			textChars = append(textChars, "<")
			contentChars = append(contentChars, s.Advance())
			textChars = append(textChars, "<")
			stripTabs := false
			if !s.AtEnd() && (s.Peek() == "-") {
				stripTabs = true
				contentChars = append(contentChars, s.Advance())
				textChars = append(textChars, "-")
			}
			for !s.AtEnd() && isWhitespaceNoNewline(s.Peek()) {
				ch = s.Advance()
				contentChars = append(contentChars, ch)
				textChars = append(textChars, ch)
			}
			var delimiterChars []string = []string{}
			if !s.AtEnd() {
				ch = s.Peek()
				if isQuote(ch) {
					quote = s.Advance()
					contentChars = append(contentChars, quote)
					textChars = append(textChars, quote)
					for !s.AtEnd() && (s.Peek() != quote) {
						dch = s.Advance()
						contentChars = append(contentChars, dch)
						textChars = append(textChars, dch)
						delimiterChars = append(delimiterChars, dch)
					}
					if !s.AtEnd() {
						closing = s.Advance()
						contentChars = append(contentChars, closing)
						textChars = append(textChars, closing)
					}
				} else if ch == "\\" {
					esc = s.Advance()
					contentChars = append(contentChars, esc)
					textChars = append(textChars, esc)
					if !s.AtEnd() {
						dch = s.Advance()
						contentChars = append(contentChars, dch)
						textChars = append(textChars, dch)
						delimiterChars = append(delimiterChars, dch)
					}
					for !s.AtEnd() && !isMetachar(s.Peek()) {
						dch = s.Advance()
						contentChars = append(contentChars, dch)
						textChars = append(textChars, dch)
						delimiterChars = append(delimiterChars, dch)
					}
				} else {
					for (!s.AtEnd() && !isMetachar(s.Peek())) && (s.Peek() != "`") {
						ch = s.Peek()
						if isQuote(ch) {
							quote = s.Advance()
							contentChars = append(contentChars, quote)
							textChars = append(textChars, quote)
							for !s.AtEnd() && (s.Peek() != quote) {
								dch = s.Advance()
								contentChars = append(contentChars, dch)
								textChars = append(textChars, dch)
								delimiterChars = append(delimiterChars, dch)
							}
							if !s.AtEnd() {
								closing = s.Advance()
								contentChars = append(contentChars, closing)
								textChars = append(textChars, closing)
							}
						} else if ch == "\\" {
							esc = s.Advance()
							contentChars = append(contentChars, esc)
							textChars = append(textChars, esc)
							if !s.AtEnd() {
								dch = s.Advance()
								contentChars = append(contentChars, dch)
								textChars = append(textChars, dch)
								delimiterChars = append(delimiterChars, dch)
							}
						} else {
							dch = s.Advance()
							contentChars = append(contentChars, dch)
							textChars = append(textChars, dch)
							delimiterChars = append(delimiterChars, dch)
						}
					}
				}
			}
			delimiter := strings.Join(delimiterChars, "")
			if delimiter != nil {
				pendingHeredocs = append(pendingHeredocs, struct{ Single, Double bool }{delimiter, stripTabs})
			}
			continue
		}
		if c == "\n" {
			ch = s.Advance()
			contentChars = append(contentChars, ch)
			textChars = append(textChars, ch)
			if len(pendingHeredocs) > 0 {
				{
					var entry quoteStackEntry = pendingHeredocs[(len(pendingHeredocs) - 1)]
					pendingHeredocs = pendingHeredocs[:(len(pendingHeredocs) - 1)]
					currentHeredocDelim = entry.Single
					currentHeredocStrip = entry.Double
				}
				inHeredocBody = true
			}
			continue
		}
		ch = s.Advance()
		contentChars = append(contentChars, ch)
		textChars = append(textChars, ch)
	}
	if s.AtEnd() {
		panic("Unterminated backtick")
	}
	s.Advance()
	textChars = append(textChars, "`")
	text := strings.Join(textChars, "")
	content := strings.Join(contentChars, "")
	if len(pendingHeredocs) > 0 {
		heredocStart, heredocEnd := findHeredocContentEnd(s.Source, s.Pos, pendingHeredocs)
		if heredocEnd > heredocStart {
			content = (content + substring(s.Source, heredocStart, heredocEnd))
			if s.cmdsubHeredocEnd == nil {
				s.cmdsubHeredocEnd = heredocEnd
			} else {
				s.cmdsubHeredocEnd = Max(s.cmdsubHeredocEnd, heredocEnd)
			}
		}
	}
	subParser := &Parser{Source: content}
	cmd := subParser.ParseList()
	if cmd == nil {
		cmd = &Empty{}
	}
	return &CommandSubstitution{Command: cmd}, text
}

func (s *Parser) parseProcessSubstitution() (*Node, string) {
	if s.AtEnd() || !isRedirectChar(s.Peek()) {
		return nil, ""
	}
	start := s.Pos
	direction := s.Advance()
	if s.AtEnd() || (s.Peek() != "(") {
		s.Pos = start
		return nil, ""
	}
	s.Advance()
	saved := s.saveParserState()
	oldInProcessSub := s.inProcessSub
	s.inProcessSub = true
	s.setState(ParserstateflagsPstEoftoken)
	s.eofToken = ")"
	func() {
		defer func() {
			if e := recover(); e != nil {
				s.restoreParserState(saved)
				s.inProcessSub = oldInProcessSub
				contentStartChar := func() string {
					if (start + 2) < s.Length {
						return string(s.Source[(start + 2)])
					} else {
						return ""
					}
				}()
				if strings.Contains(" \t\n", contentStartChar) {
					panic("")
				}
				s.Pos = (start + 2)
				s.lexer.Pos = s.Pos
				s.lexer.parseMatchedPair("(", ")", 0, false)
				s.Pos = s.lexer.Pos
				text := substring(s.Source, start, s.Pos)
				text = stripLineContinuationsCommentAware(text)
				return nil, text
			}
		}()
		cmd := s.ParseList(true)
		if cmd == nil {
			cmd = &Empty{}
		}
		s.SkipWhitespaceAndNewlines()
		if s.AtEnd() || (s.Peek() != ")") {
			panic("Invalid process substitution")
		}
		s.Advance()
		textEnd := s.Pos
		text = substring(s.Source, start, textEnd)
		text = stripLineContinuationsCommentAware(text)
		s.restoreParserState(saved)
		s.inProcessSub = oldInProcessSub
		return &ProcessSubstitution{Direction: direction, Command: cmd}, text
	}()
}

func (s *Parser) parseArrayLiteral() (*Node, string) {
	if s.AtEnd() || (s.Peek() != "(") {
		return nil, ""
	}
	start := s.Pos
	s.Advance()
	s.setState(ParserstateflagsPstCompassign)
	elements := []interface{}{}
	for true {
		s.SkipWhitespaceAndNewlines()
		if s.AtEnd() {
			s.clearState(ParserstateflagsPstCompassign)
			panic("Unterminated array literal")
		}
		if s.Peek() == ")" {
			break
		}
		word := s.ParseWord(false, true, false)
		if word == nil {
			if s.Peek() == ")" {
				break
			}
			s.clearState(ParserstateflagsPstCompassign)
			panic("Expected word in array literal")
		}
		elements = append(elements, word)
	}
	if s.AtEnd() || (s.Peek() != ")") {
		s.clearState(ParserstateflagsPstCompassign)
		panic("Expected ) to close array literal")
	}
	s.Advance()
	text := substring(s.Source, start, s.Pos)
	s.clearState(ParserstateflagsPstCompassign)
	return &Array{Elements: elements}, text
}

func (s *Parser) parseArithmeticExpansion() (*Node, string) {
	var firstClosePos interface{}
	var content interface{}
	if s.AtEnd() || (s.Peek() != "$") {
		return nil, ""
	}
	start := s.Pos
	if (((s.Pos + 2) >= s.Length) || (string(s.Source[(s.Pos+1)]) != "(")) || (string(s.Source[(s.Pos+2)]) != "(") {
		return nil, ""
	}
	s.Advance()
	s.Advance()
	s.Advance()
	contentStart := s.Pos
	depth := 2
	var firstClosePos *int = nil
	for !s.AtEnd() && (depth > 0) {
		c := s.Peek()
		if c == "'" {
			s.Advance()
			for !s.AtEnd() && (s.Peek() != "'") {
				s.Advance()
			}
			if !s.AtEnd() {
				s.Advance()
			}
		} else if c == "\"" {
			s.Advance()
			for !s.AtEnd() {
				if (s.Peek() == "\\") && ((s.Pos + 1) < s.Length) {
					s.Advance()
					s.Advance()
				} else if s.Peek() == "\"" {
					s.Advance()
					break
				} else {
					s.Advance()
				}
			}
		} else if (c == "\\") && ((s.Pos + 1) < s.Length) {
			s.Advance()
			s.Advance()
		} else if c == "(" {
			depth += 1
			s.Advance()
		} else if c == ")" {
			if depth == 2 {
				firstClosePos = s.Pos
			}
			depth -= 1
			if depth == 0 {
				break
			}
			s.Advance()
		} else {
			if depth == 1 {
				firstClosePos = nil
			}
			s.Advance()
		}
	}
	if depth != 0 {
		if s.AtEnd() {
			panic("unexpected EOF looking for `))'")
		}
		s.Pos = start
		return nil, ""
	}
	if firstClosePos != nil {
		content = substring(s.Source, contentStart, firstClosePos)
	} else {
		content = substring(s.Source, contentStart, s.Pos)
	}
	s.Advance()
	text := substring(s.Source, start, s.Pos)
	func() {
		defer func() {
			if r := recover(); r != nil {
				s.Pos = start
				return nil, ""
			}
		}()
		expr := s.parseArithExpr(content)
	}()
	return &ArithmeticExpansion{Expression: expr}, text
}

func (s *Parser) parseArithExpr(content string) Node {
	var result interface{}
	savedArithSrc := s.arithSrc
	savedArithPos := s.arithPos
	savedArithLen := s.arithLen
	savedParserState := s.parserState
	s.setState(ParserstateflagsPstArith)
	s.arithSrc = content
	s.arithPos = 0
	s.arithLen = len(content)
	s.arithSkipWs()
	if s.arithAtEnd() {
		result = nil
	} else {
		result = s.arithParseComma()
	}
	s.parserState = savedParserState
	if savedArithSrc != "" {
		s.arithSrc = savedArithSrc
		s.arithPos = savedArithPos
		s.arithLen = savedArithLen
	}
	return result
}

func (s *Parser) arithAtEnd() bool {
	return (s.arithPos >= s.arithLen)
}

func (s *Parser) arithPeek(offset int) string {
	pos := (s.arithPos + offset)
	if pos >= s.arithLen {
		return ""
	}
	return string(s.arithSrc[pos])
}

func (s *Parser) arithAdvance() string {
	if s.arithAtEnd() {
		return ""
	}
	c := string(s.arithSrc[s.arithPos])
	s.arithPos += 1
	return c
}

func (s *Parser) arithSkipWs() {
	for !s.arithAtEnd() {
		c := string(s.arithSrc[s.arithPos])
		if isWhitespace(c) {
			s.arithPos += 1
		} else if ((c == "\\") && ((s.arithPos + 1) < s.arithLen)) && (string(s.arithSrc[(s.arithPos+1)]) == "\n") {
			s.arithPos += 2
		} else {
			break
		}
	}
}

func (p0 *Parser) arithMatch(s string) bool {
	return startsWithAt(p0.arithSrc, p0.arithPos, s)
}

func (p0 *Parser) arithConsume(s string) bool {
	if p0.arithMatch(s) {
		p0.arithPos += len(s)
		return true
	}
	return false
}

func (s *Parser) arithParseComma() Node {
	left := s.arithParseAssign()
	for true {
		s.arithSkipWs()
		if s.arithConsume(",") {
			s.arithSkipWs()
			right := s.arithParseAssign()
			left = &ArithComma{Left: left, Right: right}
		} else {
			break
		}
	}
	return left
}

func (s *Parser) arithParseAssign() Node {
	left := s.arithParseTernary()
	s.arithSkipWs()
	assignOps := []string{"<<=", ">>=", "+=", "-=", "*=", "/=", "%=", "&=", "^=", "|=", "="}
	for _, op := range assignOps {
		if s.arithMatch(op) {
			if (op == "=") && (s.arithPeek(1) == "=") {
				break
			}
			s.arithConsume(op)
			s.arithSkipWs()
			right := s.arithParseAssign()
			return &ArithAssign{Op: op, Target: left, Value: right}
		}
	}
	return left
}

func (s *Parser) arithParseTernary() Node {
	var ifTrue interface{}
	var ifFalse interface{}
	cond := s.arithParseLogicalOr()
	s.arithSkipWs()
	if s.arithConsume("?") {
		s.arithSkipWs()
		if s.arithMatch(":") {
			ifTrue = nil
		} else {
			ifTrue = s.arithParseAssign()
		}
		s.arithSkipWs()
		if s.arithConsume(":") {
			s.arithSkipWs()
			if s.arithAtEnd() || (s.arithPeek(0) == ")") {
				ifFalse = nil
			} else {
				ifFalse = s.arithParseTernary()
			}
		} else {
			ifFalse = nil
		}
		return &ArithTernary{Condition: cond, IfTrue: ifTrue, IfFalse: ifFalse}
	}
	return cond
}

func (s *Parser) arithParseLeftAssoc(ops []string, parsefn interface{}) Node {
	left := Parsefn()
	for true {
		s.arithSkipWs()
		matched := false
		for _, op := range ops {
			if s.arithMatch(op) {
				s.arithConsume(op)
				s.arithSkipWs()
				left = &ArithBinaryOp{Op: op, Left: left, Right: Parsefn()}
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

func (s *Parser) arithParseLogicalOr() Node {
	return s.arithParseLeftAssoc([]string{"||"}, s.arithParseLogicalAnd)
}

func (s *Parser) arithParseLogicalAnd() Node {
	return s.arithParseLeftAssoc([]string{"&&"}, s.arithParseBitwiseOr)
}

func (s *Parser) arithParseBitwiseOr() Node {
	left := s.arithParseBitwiseXor()
	for true {
		s.arithSkipWs()
		if (s.arithPeek(0) == "|") && ((s.arithPeek(1) != "|") && (s.arithPeek(1) != "=")) {
			s.arithAdvance()
			s.arithSkipWs()
			right := s.arithParseBitwiseXor()
			left = &ArithBinaryOp{Op: "|", Left: left, Right: right}
		} else {
			break
		}
	}
	return left
}

func (s *Parser) arithParseBitwiseXor() Node {
	left := s.arithParseBitwiseAnd()
	for true {
		s.arithSkipWs()
		if (s.arithPeek(0) == "^") && (s.arithPeek(1) != "=") {
			s.arithAdvance()
			s.arithSkipWs()
			right := s.arithParseBitwiseAnd()
			left = &ArithBinaryOp{Op: "^", Left: left, Right: right}
		} else {
			break
		}
	}
	return left
}

func (s *Parser) arithParseBitwiseAnd() Node {
	left := s.arithParseEquality()
	for true {
		s.arithSkipWs()
		if (s.arithPeek(0) == "&") && ((s.arithPeek(1) != "&") && (s.arithPeek(1) != "=")) {
			s.arithAdvance()
			s.arithSkipWs()
			right := s.arithParseEquality()
			left = &ArithBinaryOp{Op: "&", Left: left, Right: right}
		} else {
			break
		}
	}
	return left
}

func (s *Parser) arithParseEquality() Node {
	return s.arithParseLeftAssoc([]string{"==", "!="}, s.arithParseComparison)
}

func (s *Parser) arithParseComparison() Node {
	var right Node
	var left *ArithBinaryOp
	left = s.arithParseShift()
	for true {
		s.arithSkipWs()
		if s.arithMatch("<=") {
			s.arithConsume("<=")
			s.arithSkipWs()
			right = s.arithParseShift()
			left = &ArithBinaryOp{Op: "<=", Left: left, Right: right}
		} else if s.arithMatch(">=") {
			s.arithConsume(">=")
			s.arithSkipWs()
			right = s.arithParseShift()
			left = &ArithBinaryOp{Op: ">=", Left: left, Right: right}
		} else if (s.arithPeek(0) == "<") && ((s.arithPeek(1) != "<") && (s.arithPeek(1) != "=")) {
			s.arithAdvance()
			s.arithSkipWs()
			right = s.arithParseShift()
			left = &ArithBinaryOp{Op: "<", Left: left, Right: right}
		} else if (s.arithPeek(0) == ">") && ((s.arithPeek(1) != ">") && (s.arithPeek(1) != "=")) {
			s.arithAdvance()
			s.arithSkipWs()
			right = s.arithParseShift()
			left = &ArithBinaryOp{Op: ">", Left: left, Right: right}
		} else {
			break
		}
	}
	return left
}

func (s *Parser) arithParseShift() Node {
	var right Node
	var left *ArithBinaryOp
	left = s.arithParseAdditive()
	for true {
		s.arithSkipWs()
		if s.arithMatch("<<=") {
			break
		}
		if s.arithMatch(">>=") {
			break
		}
		if s.arithMatch("<<") {
			s.arithConsume("<<")
			s.arithSkipWs()
			right = s.arithParseAdditive()
			left = &ArithBinaryOp{Op: "<<", Left: left, Right: right}
		} else if s.arithMatch(">>") {
			s.arithConsume(">>")
			s.arithSkipWs()
			right = s.arithParseAdditive()
			left = &ArithBinaryOp{Op: ">>", Left: left, Right: right}
		} else {
			break
		}
	}
	return left
}

func (s *Parser) arithParseAdditive() Node {
	var right Node
	var left *ArithBinaryOp
	left = s.arithParseMultiplicative()
	for true {
		s.arithSkipWs()
		c := s.arithPeek(0)
		c2 := s.arithPeek(1)
		if (c == "+") && ((c2 != "+") && (c2 != "=")) {
			s.arithAdvance()
			s.arithSkipWs()
			right = s.arithParseMultiplicative()
			left = &ArithBinaryOp{Op: "+", Left: left, Right: right}
		} else if (c == "-") && ((c2 != "-") && (c2 != "=")) {
			s.arithAdvance()
			s.arithSkipWs()
			right = s.arithParseMultiplicative()
			left = &ArithBinaryOp{Op: "-", Left: left, Right: right}
		} else {
			break
		}
	}
	return left
}

func (s *Parser) arithParseMultiplicative() Node {
	var right Node
	var left *ArithBinaryOp
	left = s.arithParseExponentiation()
	for true {
		s.arithSkipWs()
		c := s.arithPeek(0)
		c2 := s.arithPeek(1)
		if (c == "*") && ((c2 != "*") && (c2 != "=")) {
			s.arithAdvance()
			s.arithSkipWs()
			right = s.arithParseExponentiation()
			left = &ArithBinaryOp{Op: "*", Left: left, Right: right}
		} else if (c == "/") && (c2 != "=") {
			s.arithAdvance()
			s.arithSkipWs()
			right = s.arithParseExponentiation()
			left = &ArithBinaryOp{Op: "/", Left: left, Right: right}
		} else if (c == "%") && (c2 != "=") {
			s.arithAdvance()
			s.arithSkipWs()
			right = s.arithParseExponentiation()
			left = &ArithBinaryOp{Op: "%", Left: left, Right: right}
		} else {
			break
		}
	}
	return left
}

func (s *Parser) arithParseExponentiation() Node {
	left := s.arithParseUnary()
	s.arithSkipWs()
	if s.arithMatch("**") {
		s.arithConsume("**")
		s.arithSkipWs()
		right := s.arithParseExponentiation()
		return &ArithBinaryOp{Op: "**", Left: left, Right: right}
	}
	return left
}

func (s *Parser) arithParseUnary() Node {
	s.arithSkipWs()
	if s.arithMatch("++") {
		s.arithConsume("++")
		s.arithSkipWs()
		operand := s.arithParseUnary()
		return &ArithPreIncr{Operand: operand}
	}
	if s.arithMatch("--") {
		s.arithConsume("--")
		s.arithSkipWs()
		operand = s.arithParseUnary()
		return &ArithPreDecr{Operand: operand}
	}
	c := s.arithPeek(0)
	if c == "!" {
		s.arithAdvance()
		s.arithSkipWs()
		operand = s.arithParseUnary()
		return &ArithUnaryOp{Op: "!", Operand: operand}
	}
	if c == "~" {
		s.arithAdvance()
		s.arithSkipWs()
		operand = s.arithParseUnary()
		return &ArithUnaryOp{Op: "~", Operand: operand}
	}
	if (c == "+") && (s.arithPeek(1) != "+") {
		s.arithAdvance()
		s.arithSkipWs()
		operand = s.arithParseUnary()
		return &ArithUnaryOp{Op: "+", Operand: operand}
	}
	if (c == "-") && (s.arithPeek(1) != "-") {
		s.arithAdvance()
		s.arithSkipWs()
		operand = s.arithParseUnary()
		return &ArithUnaryOp{Op: "-", Operand: operand}
	}
	return s.arithParsePostfix()
}

func (s *Parser) arithParsePostfix() Node {
	var left *ArithPostIncr
	left = s.arithParsePrimary()
	for true {
		s.arithSkipWs()
		if s.arithMatch("++") {
			s.arithConsume("++")
			left = &ArithPostIncr{Operand: left}
		} else if s.arithMatch("--") {
			s.arithConsume("--")
			left = &ArithPostDecr{Operand: left}
		} else if s.arithPeek(0) == "[" {
			if left.Kind == "var" {
				s.arithAdvance()
				s.arithSkipWs()
				index := s.arithParseComma()
				s.arithSkipWs()
				if !s.arithConsume("]") {
					panic("Expected ']' in array subscript")
				}
				left = &ArithSubscript{Array: left.Name, Index: index}
			} else {
				break
			}
		} else {
			break
		}
	}
	return left
}

func (s *Parser) arithParsePrimary() Node {
	s.arithSkipWs()
	c := s.arithPeek(0)
	if c == "(" {
		s.arithAdvance()
		s.arithSkipWs()
		expr := s.arithParseComma()
		s.arithSkipWs()
		if !s.arithConsume(")") {
			panic("Expected ')' in arithmetic expression")
		}
		return expr
	}
	if (c == "#") && (s.arithPeek(1) == "$") {
		s.arithAdvance()
		return s.arithParseExpansion()
	}
	if c == "$" {
		return s.arithParseExpansion()
	}
	if c == "'" {
		return s.arithParseSingleQuote()
	}
	if c == "\"" {
		return s.arithParseDoubleQuote()
	}
	if c == "`" {
		return s.arithParseBacktick()
	}
	if c == "\\" {
		s.arithAdvance()
		if s.arithAtEnd() {
			panic("Unexpected end after backslash in arithmetic")
		}
		escapedChar := s.arithAdvance()
		return &ArithEscape{Char: escapedChar}
	}
	if s.arithAtEnd() || strings.Contains(")]:,;?|&<>=!+-*/%^~#{}", c) {
		return &ArithEmpty{}
	}
	return s.arithParseNumberOrVar()
}

func (s *Parser) arithParseExpansion() Node {
	if !s.arithConsume("$") {
		panic("Expected '$'")
	}
	c := s.arithPeek(0)
	if c == "(" {
		return s.arithParseCmdsub()
	}
	if c == "{" {
		return s.arithParseBracedParam()
	}
	nameChars := []interface{}{}
	for !s.arithAtEnd() {
		ch := s.arithPeek(0)
		if ch.Isalnum() || (ch == "_") {
			nameChars = append(nameChars, s.arithAdvance())
		} else if (isSpecialParamOrDigit(ch) || (ch == "#")) && !nameChars != nil {
			nameChars = append(nameChars, s.arithAdvance())
			break
		} else {
			break
		}
	}
	if !nameChars != nil {
		panic("Expected variable name after $")
	}
	return &ParamExpansion{Param: strings.Join(nameChars, "")}
}

func (s *Parser) arithParseCmdsub() Node {
	s.arithAdvance()
	if s.arithPeek(0) == "(" {
		s.arithAdvance()
		depth := 1
		contentStart := s.arithPos
		for !s.arithAtEnd() && (depth > 0) {
			ch := s.arithPeek(0)
			if ch == "(" {
				depth += 1
				s.arithAdvance()
			} else if ch == ")" {
				if (depth == 1) && (s.arithPeek(1) == ")") {
					break
				}
				depth -= 1
				s.arithAdvance()
			} else {
				s.arithAdvance()
			}
		}
		content := substring(s.arithSrc, contentStart, s.arithPos)
		s.arithAdvance()
		s.arithAdvance()
		innerExpr := s.parseArithExpr(content)
		return &ArithmeticExpansion{Expression: innerExpr}
	}
	depth = 1
	contentStart = s.arithPos
	for !s.arithAtEnd() && (depth > 0) {
		ch = s.arithPeek(0)
		if ch == "(" {
			depth += 1
			s.arithAdvance()
		} else if ch == ")" {
			depth -= 1
			if depth == 0 {
				break
			}
			s.arithAdvance()
		} else {
			s.arithAdvance()
		}
	}
	content = substring(s.arithSrc, contentStart, s.arithPos)
	s.arithAdvance()
	subParser := &Parser{Source: content}
	cmd := subParser.ParseList()
	return &CommandSubstitution{Command: cmd}
}

func (s *Parser) arithParseBracedParam() Node {
	s.arithAdvance()
	if s.arithPeek(0) == "!" {
		s.arithAdvance()
		nameChars := []interface{}{}
		for !s.arithAtEnd() && (s.arithPeek(0) != "}") {
			nameChars = append(nameChars, s.arithAdvance())
		}
		s.arithConsume("}")
		return &ParamIndirect{Param: strings.Join(nameChars, "")}
	}
	if s.arithPeek(0) == "#" {
		s.arithAdvance()
		nameChars = []interface{}{}
		for !s.arithAtEnd() && (s.arithPeek(0) != "}") {
			nameChars = append(nameChars, s.arithAdvance())
		}
		s.arithConsume("}")
		return &ParamLength{Param: strings.Join(nameChars, "")}
	}
	nameChars = []interface{}{}
	for !s.arithAtEnd() {
		ch := s.arithPeek(0)
		if ch == "}" {
			s.arithAdvance()
			return &ParamExpansion{Param: strings.Join(nameChars, "")}
		}
		if isParamExpansionOp(ch) {
			break
		}
		nameChars = append(nameChars, s.arithAdvance())
	}
	name := strings.Join(nameChars, "")
	opChars := []interface{}{}
	depth := 1
	for !s.arithAtEnd() && (depth > 0) {
		ch = s.arithPeek(0)
		if ch == "{" {
			depth += 1
			opChars = append(opChars, s.arithAdvance())
		} else if ch == "}" {
			depth -= 1
			if depth == 0 {
				break
			}
			opChars = append(opChars, s.arithAdvance())
		} else {
			opChars = append(opChars, s.arithAdvance())
		}
	}
	s.arithConsume("}")
	opStr := strings.Join(opChars, "")
	if opStr.Startswith(":-") {
		return &ParamExpansion{Param: name, Op: ":-", Arg: substring(opStr, 2, len(opStr))}
	}
	if opStr.Startswith(":=") {
		return &ParamExpansion{Param: name, Op: ":=", Arg: substring(opStr, 2, len(opStr))}
	}
	if opStr.Startswith(":+") {
		return &ParamExpansion{Param: name, Op: ":+", Arg: substring(opStr, 2, len(opStr))}
	}
	if opStr.Startswith(":?") {
		return &ParamExpansion{Param: name, Op: ":?", Arg: substring(opStr, 2, len(opStr))}
	}
	if opStr.Startswith(":") {
		return &ParamExpansion{Param: name, Op: ":", Arg: substring(opStr, 1, len(opStr))}
	}
	if opStr.Startswith("##") {
		return &ParamExpansion{Param: name, Op: "##", Arg: substring(opStr, 2, len(opStr))}
	}
	if opStr.Startswith("#") {
		return &ParamExpansion{Param: name, Op: "#", Arg: substring(opStr, 1, len(opStr))}
	}
	if opStr.Startswith("%%") {
		return &ParamExpansion{Param: name, Op: "%%", Arg: substring(opStr, 2, len(opStr))}
	}
	if opStr.Startswith("%") {
		return &ParamExpansion{Param: name, Op: "%", Arg: substring(opStr, 1, len(opStr))}
	}
	if opStr.Startswith("//") {
		return &ParamExpansion{Param: name, Op: "//", Arg: substring(opStr, 2, len(opStr))}
	}
	if opStr.Startswith("/") {
		return &ParamExpansion{Param: name, Op: "/", Arg: substring(opStr, 1, len(opStr))}
	}
	return &ParamExpansion{Param: name, Op: "", Arg: opStr}
}

func (s *Parser) arithParseSingleQuote() Node {
	s.arithAdvance()
	contentStart := s.arithPos
	for !s.arithAtEnd() && (s.arithPeek(0) != "'") {
		s.arithAdvance()
	}
	content := substring(s.arithSrc, contentStart, s.arithPos)
	if !s.arithConsume("'") {
		panic("Unterminated single quote in arithmetic")
	}
	return &ArithNumber{Value: content}
}

func (s *Parser) arithParseDoubleQuote() Node {
	s.arithAdvance()
	contentStart := s.arithPos
	for !s.arithAtEnd() && (s.arithPeek(0) != "\"") {
		c := s.arithPeek(0)
		if (c == "\\") && !s.arithAtEnd() {
			s.arithAdvance()
			s.arithAdvance()
		} else {
			s.arithAdvance()
		}
	}
	content := substring(s.arithSrc, contentStart, s.arithPos)
	if !s.arithConsume("\"") {
		panic("Unterminated double quote in arithmetic")
	}
	return &ArithNumber{Value: content}
}

func (s *Parser) arithParseBacktick() Node {
	s.arithAdvance()
	contentStart := s.arithPos
	for !s.arithAtEnd() && (s.arithPeek(0) != "`") {
		c := s.arithPeek(0)
		if (c == "\\") && !s.arithAtEnd() {
			s.arithAdvance()
			s.arithAdvance()
		} else {
			s.arithAdvance()
		}
	}
	content := substring(s.arithSrc, contentStart, s.arithPos)
	if !s.arithConsume("`") {
		panic("Unterminated backtick in arithmetic")
	}
	subParser := &Parser{Source: content}
	cmd := subParser.ParseList()
	return &CommandSubstitution{Command: cmd}
}

func (s *Parser) arithParseNumberOrVar() Node {
	s.arithSkipWs()
	chars := []interface{}{}
	c := s.arithPeek(0)
	if c.Isdigit() {
		for !s.arithAtEnd() {
			ch := s.arithPeek(0)
			if ch.Isalnum() || ((ch == "#") || (ch == "_")) {
				chars = append(chars, s.arithAdvance())
			} else {
				break
			}
		}
		prefix := strings.Join(chars, "")
		if !s.arithAtEnd() && (s.arithPeek(0) == "$") {
			expansion := s.arithParseExpansion()
			return &ArithConcat{Parts: []interface{}{&ArithNumber{Value: prefix}, expansion}}
		}
		return &ArithNumber{Value: prefix}
	}
	if c.Isalpha() || (c == "_") {
		for !s.arithAtEnd() {
			ch = s.arithPeek(0)
			if ch.Isalnum() || (ch == "_") {
				chars = append(chars, s.arithAdvance())
			} else {
				break
			}
		}
		return &ArithVar{Name: strings.Join(chars, "")}
	}
	panic((("Unexpected character '" + c) + "' in arithmetic expression"))
}

func (s *Parser) parseDeprecatedArithmetic() (*Node, string) {
	if s.AtEnd() || (s.Peek() != "$") {
		return nil, ""
	}
	start := s.Pos
	if ((s.Pos + 1) >= s.Length) || (string(s.Source[(s.Pos+1)]) != "[") {
		return nil, ""
	}
	s.Advance()
	s.Advance()
	s.lexer.Pos = s.Pos
	content := s.lexer.parseMatchedPair("[", "]", MatchedpairflagsArith, false)
	s.Pos = s.lexer.Pos
	text := substring(s.Source, start, s.Pos)
	return &ArithDeprecated{Expression: content}, text
}

func (s *Parser) parseParamExpansion(inDquote bool) (*Node, string) {
	s.syncLexer()
	result := s.lexer.readParamExpansion(inDquote)
	s.syncParser()
	return result
}

func (s *Parser) ParseRedirect() interface{} {
	var inBracket bool
	var isValidVarfd bool
	var op string
	var target *Word
	var fdTarget interface{}
	var innerWord *Word
	s.SkipWhitespace()
	if s.AtEnd() {
		return nil
	}
	start := s.Pos
	fd := nil
	varfd := nil
	if s.Peek() == "{" {
		saved := s.Pos
		s.Advance()
		varnameChars := []interface{}{}
		inBracket = false
		for !s.AtEnd() && !isRedirectChar(s.Peek()) {
			ch := s.Peek()
			if (ch == "}") && !inBracket {
				break
			} else if ch == "[" {
				inBracket = true
				varnameChars = append(varnameChars, s.Advance())
			} else if ch == "]" {
				inBracket = false
				varnameChars = append(varnameChars, s.Advance())
			} else if ch.Isalnum() || (ch == "_") {
				varnameChars = append(varnameChars, s.Advance())
			} else if inBracket && !isMetachar(ch) {
				varnameChars = append(varnameChars, s.Advance())
			} else {
				break
			}
		}
		varname := strings.Join(varnameChars, "")
		isValidVarfd = false
		if varname != nil {
			if varname[0].Isalpha() || (varname[0] == "_") {
				if strings.Contains(varname, "[") || strings.Contains(varname, "]") {
					left := varname.Find("[")
					right := varname.Rfind("]")
					if ((left != -1) && (right == (len(varname) - 1))) && (right > (left + 1)) {
						base := varname[:left]
						if base != nil && (base[0].Isalpha() || (base[0] == "_")) {
							isValidVarfd = true
							for _, c := range base[1:] {
								if !(c.Isalnum() || (c == "_")) {
									isValidVarfd = false
									break
								}
							}
						}
					}
				} else {
					isValidVarfd = true
					for _, c := range varname[1:] {
						if !(c.Isalnum() || (c == "_")) {
							isValidVarfd = false
							break
						}
					}
				}
			}
		}
		if (!s.AtEnd() && (s.Peek() == "}")) && isValidVarfd {
			s.Advance()
			varfd = varname
		} else {
			s.Pos = saved
		}
	}
	if (varfd == nil && (s.Peek() != "")) && s.Peek().Isdigit() {
		fdChars := []interface{}{}
		for !s.AtEnd() && s.Peek().Isdigit() {
			fdChars = append(fdChars, s.Advance())
		}
		fd = Int(strings.Join(fdChars, ""))
	}
	ch = s.Peek()
	if ((ch == "&") && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == ">") {
		if fd != nil || varfd != nil {
			s.Pos = start
			return nil
		}
		s.Advance()
		s.Advance()
		if !s.AtEnd() && (s.Peek() == ">") {
			s.Advance()
			op = "&>>"
		} else {
			op = "&>"
		}
		s.SkipWhitespace()
		target = s.ParseWord(false, false, false)
		if target == nil {
			panic(("Expected target for redirect " + op))
		}
		return &Redirect{Op: op, Target: target}
	}
	if (ch == "") || !isRedirectChar(ch) {
		s.Pos = start
		return nil
	}
	if (fd == nil && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "(") {
		s.Pos = start
		return nil
	}
	op = s.Advance()
	stripTabs := false
	if !s.AtEnd() {
		nextCh := s.Peek()
		if (op == ">") && (nextCh == ">") {
			s.Advance()
			op = ">>"
		} else if (op == "<") && (nextCh == "<") {
			s.Advance()
			if !s.AtEnd() && (s.Peek() == "<") {
				s.Advance()
				op = "<<<"
			} else if !s.AtEnd() && (s.Peek() == "-") {
				s.Advance()
				op = "<<"
				stripTabs = true
			} else {
				op = "<<"
			}
		} else if (op == "<") && (nextCh == ">") {
			s.Advance()
			op = "<>"
		} else if (op == ">") && (nextCh == "|") {
			s.Advance()
			op = ">|"
		} else if ((fd == nil && varfd == nil) && (op == ">")) && (nextCh == "&") {
			if ((s.Pos + 1) >= s.Length) || !isDigitOrDash(string(s.Source[(s.Pos+1)])) {
				s.Advance()
				op = ">&"
			}
		} else if ((fd == nil && varfd == nil) && (op == "<")) && (nextCh == "&") {
			if ((s.Pos + 1) >= s.Length) || !isDigitOrDash(string(s.Source[(s.Pos+1)])) {
				s.Advance()
				op = "<&"
			}
		}
	}
	if op == "<<" {
		return s.parseHeredoc(fd, stripTabs)
	}
	if varfd != nil {
		op = ((("{" + varfd) + "}") + op)
	} else if fd != nil {
		op = (Str(fd) + op)
	}
	if !s.AtEnd() && (s.Peek() == "&") {
		s.Advance()
		s.SkipWhitespace()
		if !s.AtEnd() && (s.Peek() == "-") {
			if ((s.Pos + 1) < s.Length) && !isMetachar(string(s.Source[(s.Pos+1)])) {
				s.Advance()
				target = &Word{Value: "&-"}
			} else {
				target = nil
			}
		} else {
			target = nil
		}
		if target == nil {
			if !s.AtEnd() && (s.Peek().Isdigit() || (s.Peek() == "-")) {
				wordStart := s.Pos
				fdChars = []interface{}{}
				for !s.AtEnd() && s.Peek().Isdigit() {
					fdChars = append(fdChars, s.Advance())
				}
				if fdChars != nil {
					fdTarget = strings.Join(fdChars, "")
				} else {
					fdTarget = ""
				}
				if !s.AtEnd() && (s.Peek() == "-") {
					fdTarget += s.Advance()
				}
				if ((fdTarget != "-") && !s.AtEnd()) && !isMetachar(s.Peek()) {
					s.Pos = wordStart
					innerWord = s.ParseWord(false, false, false)
					if innerWord != nil {
						target = &Word{Value: ("&" + innerWord.Value)}
						target.Parts = innerWord.Parts
					} else {
						panic(("Expected target for redirect " + op))
					}
				} else {
					target = &Word{Value: ("&" + fdTarget)}
				}
			} else {
				innerWord = s.ParseWord(false, false, false)
				if innerWord != nil {
					target = &Word{Value: ("&" + innerWord.Value)}
					target.Parts = innerWord.Parts
				} else {
					panic(("Expected target for redirect " + op))
				}
			}
		}
	} else {
		s.SkipWhitespace()
		if (strings.Contains(struct{ Single, Double bool }{">&", "<&"}, op) && !s.AtEnd()) && (s.Peek() == "-") {
			if ((s.Pos + 1) < s.Length) && !isMetachar(string(s.Source[(s.Pos+1)])) {
				s.Advance()
				target = &Word{Value: "&-"}
			} else {
				target = s.ParseWord(false, false, false)
			}
		} else {
			target = s.ParseWord(false, false, false)
		}
	}
	if target == nil {
		panic(("Expected target for redirect " + op))
	}
	return &Redirect{Op: op, Target: target}
}

func (s *Parser) parseHeredocDelimiter() (string, bool) {
	var quoted bool
	var c string
	var depth int
	var dollarCount int
	var j int
	s.SkipWhitespace()
	quoted = false
	var delimiterChars []string = []string{}
	for true {
		for !s.AtEnd() && !isMetachar(s.Peek()) {
			ch := s.Peek()
			if ch == "\"" {
				quoted = true
				s.Advance()
				for !s.AtEnd() && (s.Peek() != "\"") {
					delimiterChars = append(delimiterChars, s.Advance())
				}
				if !s.AtEnd() {
					s.Advance()
				}
			} else if ch == "'" {
				quoted = true
				s.Advance()
				for !s.AtEnd() && (s.Peek() != "'") {
					c = s.Advance()
					if c == "\n" {
						s.sawNewlineInSingleQuote = true
					}
					delimiterChars = append(delimiterChars, c)
				}
				if !s.AtEnd() {
					s.Advance()
				}
			} else if ch == "\\" {
				s.Advance()
				if !s.AtEnd() {
					nextCh := s.Peek()
					if nextCh == "\n" {
						s.Advance()
					} else {
						quoted = true
						delimiterChars = append(delimiterChars, s.Advance())
					}
				}
			} else if ((ch == "$") && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "'") {
				quoted = true
				s.Advance()
				s.Advance()
				for !s.AtEnd() && (s.Peek() != "'") {
					c = s.Peek()
					if (c == "\\") && ((s.Pos + 1) < s.Length) {
						s.Advance()
						esc := s.Peek()
						escVal := getAnsiEscape(esc)
						if escVal >= 0 {
							delimiterChars = append(delimiterChars, Chr(escVal))
							s.Advance()
						} else if esc == "'" {
							delimiterChars = append(delimiterChars, s.Advance())
						} else {
							delimiterChars = append(delimiterChars, s.Advance())
						}
					} else {
						delimiterChars = append(delimiterChars, s.Advance())
					}
				}
				if !s.AtEnd() {
					s.Advance()
				}
			} else if isExpansionStart(s.Source, s.Pos, "$(") {
				delimiterChars = append(delimiterChars, s.Advance())
				delimiterChars = append(delimiterChars, s.Advance())
				depth = 1
				for !s.AtEnd() && (depth > 0) {
					c = s.Peek()
					if c == "(" {
						depth += 1
					} else if c == ")" {
						depth -= 1
					}
					delimiterChars = append(delimiterChars, s.Advance())
				}
			} else if ((ch == "$") && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "{") {
				dollarCount = 0
				j = (s.Pos - 1)
				for (j >= 0) && (string(s.Source[j]) == "$") {
					dollarCount += 1
					j -= 1
				}
				if (j >= 0) && (string(s.Source[j]) == "\\") {
					dollarCount -= 1
				}
				if (dollarCount % 2) == 1 {
					delimiterChars = append(delimiterChars, s.Advance())
				} else {
					delimiterChars = append(delimiterChars, s.Advance())
					delimiterChars = append(delimiterChars, s.Advance())
					depth = 0
					for !s.AtEnd() {
						c = s.Peek()
						if c == "{" {
							depth += 1
						} else if c == "}" {
							delimiterChars = append(delimiterChars, s.Advance())
							if depth == 0 {
								break
							}
							depth -= 1
							if ((depth == 0) && !s.AtEnd()) && isMetachar(s.Peek()) {
								break
							}
							continue
						}
						delimiterChars = append(delimiterChars, s.Advance())
					}
				}
			} else if ((ch == "$") && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "[") {
				dollarCount = 0
				j = (s.Pos - 1)
				for (j >= 0) && (string(s.Source[j]) == "$") {
					dollarCount += 1
					j -= 1
				}
				if (j >= 0) && (string(s.Source[j]) == "\\") {
					dollarCount -= 1
				}
				if (dollarCount % 2) == 1 {
					delimiterChars = append(delimiterChars, s.Advance())
				} else {
					delimiterChars = append(delimiterChars, s.Advance())
					delimiterChars = append(delimiterChars, s.Advance())
					depth = 1
					for !s.AtEnd() && (depth > 0) {
						c = s.Peek()
						if c == "[" {
							depth += 1
						} else if c == "]" {
							depth -= 1
						}
						delimiterChars = append(delimiterChars, s.Advance())
					}
				}
			} else if ch == "`" {
				delimiterChars = append(delimiterChars, s.Advance())
				for !s.AtEnd() && (s.Peek() != "`") {
					c = s.Peek()
					if c == "'" {
						delimiterChars = append(delimiterChars, s.Advance())
						for (!s.AtEnd() && (s.Peek() != "'")) && (s.Peek() != "`") {
							delimiterChars = append(delimiterChars, s.Advance())
						}
						if !s.AtEnd() && (s.Peek() == "'") {
							delimiterChars = append(delimiterChars, s.Advance())
						}
					} else if c == "\"" {
						delimiterChars = append(delimiterChars, s.Advance())
						for (!s.AtEnd() && (s.Peek() != "\"")) && (s.Peek() != "`") {
							if (s.Peek() == "\\") && ((s.Pos + 1) < s.Length) {
								delimiterChars = append(delimiterChars, s.Advance())
							}
							delimiterChars = append(delimiterChars, s.Advance())
						}
						if !s.AtEnd() && (s.Peek() == "\"") {
							delimiterChars = append(delimiterChars, s.Advance())
						}
					} else if (c == "\\") && ((s.Pos + 1) < s.Length) {
						delimiterChars = append(delimiterChars, s.Advance())
						delimiterChars = append(delimiterChars, s.Advance())
					} else {
						delimiterChars = append(delimiterChars, s.Advance())
					}
				}
				if !s.AtEnd() {
					delimiterChars = append(delimiterChars, s.Advance())
				}
			} else {
				delimiterChars = append(delimiterChars, s.Advance())
			}
		}
		if ((!s.AtEnd() && strings.Contains("<>", s.Peek())) && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "(") {
			delimiterChars = append(delimiterChars, s.Advance())
			delimiterChars = append(delimiterChars, s.Advance())
			depth = 1
			for !s.AtEnd() && (depth > 0) {
				c = s.Peek()
				if c == "(" {
					depth += 1
				} else if c == ")" {
					depth -= 1
				}
				delimiterChars = append(delimiterChars, s.Advance())
			}
			continue
		}
		break
	}
	return strings.Join(delimiterChars, ""), quoted
}

func (s *Parser) readHeredocLine(quoted bool) (string, int) {
	lineStart := s.Pos
	lineEnd := s.Pos
	for (lineEnd < s.Length) && (string(s.Source[lineEnd]) != "\n") {
		lineEnd += 1
	}
	line := substring(s.Source, lineStart, lineEnd)
	if !quoted {
		for lineEnd < s.Length {
			trailingBs := countTrailingBackslashes(line)
			if (trailingBs % 2) == 0 {
				break
			}
			line = substring(line, 0, (len(line) - 1))
			lineEnd += 1
			nextLineStart := lineEnd
			for (lineEnd < s.Length) && (string(s.Source[lineEnd]) != "\n") {
				lineEnd += 1
			}
			line = (line + substring(s.Source, nextLineStart, lineEnd))
		}
	}
	return line, lineEnd
}

func (s *Parser) lineMatchesDelimiter(line string, delimiter string, stripTabs bool) (bool, string) {
	checkLine := func() string {
		if stripTabs {
			return line.Lstrip("\t")
		} else {
			return line
		}
	}()
	normalizedCheck := normalizeHeredocDelimiter(checkLine)
	normalizedDelim := normalizeHeredocDelimiter(delimiter)
	return (normalizedCheck == normalizedDelim), checkLine
}

func (s *Parser) gatherHeredocBodies() {
	for _, heredoc := range s.pendingHeredocs {
		var contentLines []string = []string{}
		lineStart := s.Pos
		for s.Pos < s.Length {
			lineStart = s.Pos
			line, lineEnd := s.readHeredocLine(heredoc.Quoted)
			matches, checkLine := s.lineMatchesDelimiter(line, heredoc.Delimiter, heredoc.StripTabs)
			if matches != nil {
				s.Pos = func() int {
					if lineEnd < s.Length {
						return (lineEnd + 1)
					} else {
						return lineEnd
					}
				}()
				break
			}
			normalizedCheck := normalizeHeredocDelimiter(checkLine)
			normalizedDelim := normalizeHeredocDelimiter(heredoc.Delimiter)
			if (*s.eofToken == ")") && normalizedCheck.Startswith(normalizedDelim) {
				tabsStripped := (len(line) - len(checkLine))
				s.Pos = ((lineStart + tabsStripped) + len(heredoc.Delimiter))
				break
			}
			if ((lineEnd >= s.Length) && normalizedCheck.Startswith(normalizedDelim)) && s.inProcessSub {
				tabsStripped = (len(line) - len(checkLine))
				s.Pos = ((lineStart + tabsStripped) + len(heredoc.Delimiter))
				break
			}
			if heredoc.StripTabs != nil {
				line = line.Lstrip("\t")
			}
			if lineEnd < s.Length {
				contentLines = append(contentLines, (line + "\n"))
				s.Pos = (lineEnd + 1)
			} else {
				addNewline := true
				if !heredoc.Quoted != nil && ((countTrailingBackslashes(line) % 2) == 1) {
					addNewline = false
				}
				contentLines = append(contentLines, (line + func() string {
					if addNewline {
						return "\n"
					} else {
						return ""
					}
				}()))
				s.Pos = s.Length
			}
		}
		heredoc.Content = strings.Join(contentLines, "")
	}
	s.pendingHeredocs = []interface{}{}
}

func (s *Parser) parseHeredoc(fd *int, stripTabs bool) *HereDoc {
	startPos := s.Pos
	s.setState(ParserstateflagsPstHeredoc)
	delimiter, quoted := s.parseHeredocDelimiter()
	for _, existing := range s.pendingHeredocs {
		if (existing.startPos == startPos) && (existing.Delimiter == delimiter) {
			s.clearState(ParserstateflagsPstHeredoc)
			return existing
		}
	}
	heredoc := &HereDoc{Delimiter: delimiter, Content: "", StripTabs: stripTabs, Quoted: quoted, Fd: fd, Complete: false}
	heredoc.startPos = startPos
	s.pendingHeredocs = append(s.pendingHeredocs, heredoc)
	s.clearState(ParserstateflagsPstHeredoc)
	return heredoc
}

func (s *Parser) ParseCommand() *Command {
	words := []interface{}{}
	redirects := []interface{}{}
	for true {
		s.SkipWhitespace()
		if s.lexIsCommandTerminator() {
			break
		}
		if len(words) == 0 {
			reserved := s.lexPeekReservedWord()
			if (reserved == "}") || (reserved == "]]") {
				break
			}
		}
		redirect := s.ParseRedirect()
		if redirect != nil {
			redirects = append(redirects, redirect)
			continue
		}
		allAssignments := true
		for _, w := range words {
			if !s.isAssignmentWord(w) {
				allAssignments = false
				break
			}
		}
		inAssignBuiltin := ((len(words) > 0) && strings.Contains(AssignmentBuiltins, words[0].Value))
		word := s.ParseWord(false, false, false)
		if word == nil {
			break
		}
		words = append(words, word)
	}
	if !words != nil && !redirects != nil {
		return nil
	}
	return &Command{Words: words, Redirects: redirects}
}

func (s *Parser) ParseSubshell() *Subshell {
	s.SkipWhitespace()
	if s.AtEnd() || (s.Peek() != "(") {
		return nil
	}
	s.Advance()
	s.setState(ParserstateflagsPstSubshell)
	body := s.ParseList(true)
	if body == nil {
		s.clearState(ParserstateflagsPstSubshell)
		panic("Expected command in subshell")
	}
	s.SkipWhitespace()
	if s.AtEnd() || (s.Peek() != ")") {
		s.clearState(ParserstateflagsPstSubshell)
		panic("Expected ) to close subshell")
	}
	s.Advance()
	s.clearState(ParserstateflagsPstSubshell)
	return &Subshell{Body: body, Redirects: s.collectRedirects()}
}

func (s *Parser) ParseArithmeticCommand() *ArithmeticCommand {
	s.SkipWhitespace()
	if ((s.AtEnd() || (s.Peek() != "(")) || ((s.Pos + 1) >= s.Length)) || (string(s.Source[(s.Pos+1)]) != "(") {
		return nil
	}
	savedPos := s.Pos
	s.Advance()
	s.Advance()
	contentStart := s.Pos
	depth := 1
	for !s.AtEnd() && (depth > 0) {
		c := s.Peek()
		if c == "'" {
			s.Advance()
			for !s.AtEnd() && (s.Peek() != "'") {
				s.Advance()
			}
			if !s.AtEnd() {
				s.Advance()
			}
		} else if c == "\"" {
			s.Advance()
			for !s.AtEnd() {
				if (s.Peek() == "\\") && ((s.Pos + 1) < s.Length) {
					s.Advance()
					s.Advance()
				} else if s.Peek() == "\"" {
					s.Advance()
					break
				} else {
					s.Advance()
				}
			}
		} else if (c == "\\") && ((s.Pos + 1) < s.Length) {
			s.Advance()
			s.Advance()
		} else if c == "(" {
			depth += 1
			s.Advance()
		} else if c == ")" {
			if ((depth == 1) && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == ")") {
				break
			}
			depth -= 1
			if depth == 0 {
				s.Pos = savedPos
				return nil
			}
			s.Advance()
		} else {
			s.Advance()
		}
	}
	if s.AtEnd() {
		panic("unexpected EOF looking for `))'")
	}
	if depth != 1 {
		s.Pos = savedPos
		return nil
	}
	content := substring(s.Source, contentStart, s.Pos)
	content = content.Replace("\\\n", "")
	s.Advance()
	s.Advance()
	expr := s.parseArithExpr(content)
	return &ArithmeticCommand{Expression: expr, Redirects: s.collectRedirects()}
}

func (s *Parser) ParseConditionalExpr() *ConditionalExpr {
	s.SkipWhitespace()
	if ((s.AtEnd() || (s.Peek() != "[")) || ((s.Pos + 1) >= s.Length)) || (string(s.Source[(s.Pos+1)]) != "[") {
		return nil
	}
	nextPos := (s.Pos + 2)
	if (nextPos < s.Length) && !(isWhitespace(string(s.Source[nextPos])) || (((string(s.Source[nextPos]) == "\\") && ((nextPos + 1) < s.Length)) && (string(s.Source[(nextPos+1)]) == "\n"))) {
		return nil
	}
	s.Advance()
	s.Advance()
	s.setState(ParserstateflagsPstCondexpr)
	s.wordContext = WordCtxCond
	body := s.parseCondOr()
	for !s.AtEnd() && isWhitespaceNoNewline(s.Peek()) {
		s.Advance()
	}
	if ((s.AtEnd() || (s.Peek() != "]")) || ((s.Pos + 1) >= s.Length)) || (string(s.Source[(s.Pos+1)]) != "]") {
		s.clearState(ParserstateflagsPstCondexpr)
		s.wordContext = WordCtxNormal
		panic("Expected ]] to close conditional expression")
	}
	s.Advance()
	s.Advance()
	s.clearState(ParserstateflagsPstCondexpr)
	s.wordContext = WordCtxNormal
	return &ConditionalExpr{Body: body, Redirects: s.collectRedirects()}
}

func (s *Parser) condSkipWhitespace() {
	for !s.AtEnd() {
		if isWhitespaceNoNewline(s.Peek()) {
			s.Advance()
		} else if ((s.Peek() == "\\") && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "\n") {
			s.Advance()
			s.Advance()
		} else if s.Peek() == "\n" {
			s.Advance()
		} else {
			break
		}
	}
}

func (s *Parser) condAtEnd() bool {
	return (s.AtEnd() || (((s.Peek() == "]") && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "]")))
}

func (s *Parser) parseCondOr() Node {
	s.condSkipWhitespace()
	left := s.parseCondAnd()
	s.condSkipWhitespace()
	if ((!s.condAtEnd() && (s.Peek() == "|")) && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "|") {
		s.Advance()
		s.Advance()
		right := s.parseCondOr()
		return &CondOr{Left: left, Right: right}
	}
	return left
}

func (s *Parser) parseCondAnd() Node {
	s.condSkipWhitespace()
	left := s.parseCondTerm()
	s.condSkipWhitespace()
	if ((!s.condAtEnd() && (s.Peek() == "&")) && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "&") {
		s.Advance()
		s.Advance()
		right := s.parseCondAnd()
		return &CondAnd{Left: left, Right: right}
	}
	return left
}

func (s *Parser) parseCondTerm() Node {
	var word2 *Word
	s.condSkipWhitespace()
	if s.condAtEnd() {
		panic("Unexpected end of conditional expression")
	}
	if s.Peek() == "!" {
		if ((s.Pos + 1) < s.Length) && !isWhitespaceNoNewline(string(s.Source[(s.Pos+1)])) {
		} else {
			s.Advance()
			operand := s.parseCondTerm()
			return &CondNot{Operand: operand}
		}
	}
	if s.Peek() == "(" {
		s.Advance()
		inner := s.parseCondOr()
		s.condSkipWhitespace()
		if s.AtEnd() || (s.Peek() != ")") {
			panic("Expected ) in conditional expression")
		}
		s.Advance()
		return &CondParen{Inner: inner}
	}
	word1 := s.parseCondWord()
	if word1 == nil {
		panic("Expected word in conditional expression")
	}
	s.condSkipWhitespace()
	if strings.Contains(CondUnaryOps, word1.Value) {
		operand = s.parseCondWord()
		if operand == nil {
			panic(("Expected operand after " + word1.Value))
		}
		return &UnaryTest{Op: word1.Value, Operand: operand}
	}
	if !s.condAtEnd() && (((s.Peek() != "&") && (s.Peek() != "|")) && (s.Peek() != ")")) {
		if isRedirectChar(s.Peek()) && !(((s.Pos + 1) < s.Length) && (string(s.Source[(s.Pos+1)]) == "(")) {
			op := s.Advance()
			s.condSkipWhitespace()
			word2 = s.parseCondWord()
			if word2 == nil {
				panic(("Expected operand after " + op))
			}
			return &BinaryTest{Op: op, Left: word1, Right: word2}
		}
		savedPos := s.Pos
		opWord := s.parseCondWord()
		if opWord != nil && strings.Contains(CondBinaryOps, opWord.Value) {
			s.condSkipWhitespace()
			if opWord.Value == "=~" {
				word2 = s.parseCondRegexWord()
			} else {
				word2 = s.parseCondWord()
			}
			if word2 == nil {
				panic(("Expected operand after " + opWord.Value))
			}
			return &BinaryTest{Op: opWord.Value, Left: word1, Right: word2}
		} else {
			s.Pos = savedPos
		}
	}
	return &UnaryTest{Op: "-n", Operand: word1}
}

func (s *Parser) parseCondWord() *Word {
	s.condSkipWhitespace()
	if s.condAtEnd() {
		return nil
	}
	c := s.Peek()
	if isParen(c) {
		return nil
	}
	if ((c == "&") && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "&") {
		return nil
	}
	if ((c == "|") && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "|") {
		return nil
	}
	return s.parseWordInternal(WordCtxCond, false, false)
}

func (s *Parser) parseCondRegexWord() *Word {
	s.condSkipWhitespace()
	if s.condAtEnd() {
		return nil
	}
	s.setState(ParserstateflagsPstRegexp)
	result := s.parseWordInternal(WordCtxRegex, false, false)
	s.clearState(ParserstateflagsPstRegexp)
	s.wordContext = WordCtxCond
	return result
}

func (s *Parser) ParseBraceGroup() *BraceGroup {
	s.SkipWhitespace()
	if !s.lexConsumeWord("{") {
		return nil
	}
	s.SkipWhitespaceAndNewlines()
	body := s.ParseList(true)
	if body == nil {
		panic("Expected command in brace group")
	}
	s.SkipWhitespace()
	if !s.lexConsumeWord("}") {
		panic("Expected } to close brace group")
	}
	return &BraceGroup{Body: body, Redirects: s.collectRedirects()}
}

func (s *Parser) ParseIf() *If {
	var innerElse *If
	var elseBody *If
	s.SkipWhitespace()
	if !s.lexConsumeWord("if") {
		return nil
	}
	condition := s.ParseListUntil(TodoSet)
	if condition == nil {
		panic("Expected condition after 'if'")
	}
	s.SkipWhitespaceAndNewlines()
	if !s.lexConsumeWord("then") {
		panic("Expected 'then' after if condition")
	}
	thenBody := s.ParseListUntil(TodoSet)
	if thenBody == nil {
		panic("Expected commands after 'then'")
	}
	s.SkipWhitespaceAndNewlines()
	elseBody = nil
	if s.lexIsAtReservedWord("elif") {
		s.lexConsumeWord("elif")
		elifCondition := s.ParseListUntil(TodoSet)
		if elifCondition == nil {
			panic("Expected condition after 'elif'")
		}
		s.SkipWhitespaceAndNewlines()
		if !s.lexConsumeWord("then") {
			panic("Expected 'then' after elif condition")
		}
		elifThenBody := s.ParseListUntil(TodoSet)
		if elifThenBody == nil {
			panic("Expected commands after 'then'")
		}
		s.SkipWhitespaceAndNewlines()
		innerElse = nil
		if s.lexIsAtReservedWord("elif") {
			innerElse = s.parseElifChain()
		} else if s.lexIsAtReservedWord("else") {
			s.lexConsumeWord("else")
			innerElse = s.ParseListUntil(TodoSet)
			if innerElse == nil {
				panic("Expected commands after 'else'")
			}
		}
		elseBody = &If{Condition: elifCondition, ThenBody: elifThenBody, ElseBody: innerElse}
	} else if s.lexIsAtReservedWord("else") {
		s.lexConsumeWord("else")
		elseBody = s.ParseListUntil(TodoSet)
		if elseBody == nil {
			panic("Expected commands after 'else'")
		}
	}
	s.SkipWhitespaceAndNewlines()
	if !s.lexConsumeWord("fi") {
		panic("Expected 'fi' to close if statement")
	}
	return &If{Condition: condition, ThenBody: thenBody, ElseBody: elseBody, Redirects: s.collectRedirects()}
}

func (s *Parser) parseElifChain() *If {
	var elseBody *If
	s.lexConsumeWord("elif")
	condition := s.ParseListUntil(TodoSet)
	if condition == nil {
		panic("Expected condition after 'elif'")
	}
	s.SkipWhitespaceAndNewlines()
	if !s.lexConsumeWord("then") {
		panic("Expected 'then' after elif condition")
	}
	thenBody := s.ParseListUntil(TodoSet)
	if thenBody == nil {
		panic("Expected commands after 'then'")
	}
	s.SkipWhitespaceAndNewlines()
	elseBody = nil
	if s.lexIsAtReservedWord("elif") {
		elseBody = s.parseElifChain()
	} else if s.lexIsAtReservedWord("else") {
		s.lexConsumeWord("else")
		elseBody = s.ParseListUntil(TodoSet)
		if elseBody == nil {
			panic("Expected commands after 'else'")
		}
	}
	return &If{Condition: condition, ThenBody: thenBody, ElseBody: elseBody}
}

func (s *Parser) ParseWhile() *While {
	s.SkipWhitespace()
	if !s.lexConsumeWord("while") {
		return nil
	}
	condition := s.ParseListUntil(TodoSet)
	if condition == nil {
		panic("Expected condition after 'while'")
	}
	s.SkipWhitespaceAndNewlines()
	if !s.lexConsumeWord("do") {
		panic("Expected 'do' after while condition")
	}
	body := s.ParseListUntil(TodoSet)
	if body == nil {
		panic("Expected commands after 'do'")
	}
	s.SkipWhitespaceAndNewlines()
	if !s.lexConsumeWord("done") {
		panic("Expected 'done' to close while loop")
	}
	return &While{Condition: condition, Body: body, Redirects: s.collectRedirects()}
}

func (s *Parser) ParseUntil() *Until {
	s.SkipWhitespace()
	if !s.lexConsumeWord("until") {
		return nil
	}
	condition := s.ParseListUntil(TodoSet)
	if condition == nil {
		panic("Expected condition after 'until'")
	}
	s.SkipWhitespaceAndNewlines()
	if !s.lexConsumeWord("do") {
		panic("Expected 'do' after until condition")
	}
	body := s.ParseListUntil(TodoSet)
	if body == nil {
		panic("Expected commands after 'do'")
	}
	s.SkipWhitespaceAndNewlines()
	if !s.lexConsumeWord("done") {
		panic("Expected 'done' to close until loop")
	}
	return &Until{Condition: condition, Body: body, Redirects: s.collectRedirects()}
}

func (s *Parser) ParseFor() Node {
	var varName interface{}
	s.SkipWhitespace()
	if !s.lexConsumeWord("for") {
		return nil
	}
	s.SkipWhitespace()
	if ((s.Peek() == "(") && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "(") {
		return s.parseForArith()
	}
	if s.Peek() == "$" {
		varWord := s.ParseWord(false, false, false)
		if varWord == nil {
			panic("Expected variable name after 'for'")
		}
		varName = varWord.Value
	} else {
		varName = s.PeekWord()
		if varName == "" {
			panic("Expected variable name after 'for'")
		}
		s.ConsumeWord(varName)
	}
	s.SkipWhitespace()
	if s.Peek() == ";" {
		s.Advance()
	}
	s.SkipWhitespaceAndNewlines()
	words := nil
	if s.lexIsAtReservedWord("in") {
		s.lexConsumeWord("in")
		s.SkipWhitespace()
		sawDelimiter := isSemicolonOrNewline(s.Peek())
		if s.Peek() == ";" {
			s.Advance()
		}
		s.SkipWhitespaceAndNewlines()
		words = []interface{}{}
		for true {
			s.SkipWhitespace()
			if s.AtEnd() {
				break
			}
			if isSemicolonOrNewline(s.Peek()) {
				sawDelimiter = true
				if s.Peek() == ";" {
					s.Advance()
				}
				break
			}
			if s.lexIsAtReservedWord("do") {
				if sawDelimiter {
					break
				}
				panic("Expected ';' or newline before 'do'")
			}
			word := s.ParseWord(false, false, false)
			if word == nil {
				break
			}
			words = append(words, word)
		}
	}
	s.SkipWhitespaceAndNewlines()
	if s.Peek() == "{" {
		braceGroup := s.ParseBraceGroup()
		if braceGroup == nil {
			panic("Expected brace group in for loop")
		}
		return &For{Var: varName, Words: words, Body: braceGroup.Body, Redirects: s.collectRedirects()}
	}
	if !s.lexConsumeWord("do") {
		panic("Expected 'do' in for loop")
	}
	body := s.ParseListUntil(TodoSet)
	if body == nil {
		panic("Expected commands after 'do'")
	}
	s.SkipWhitespaceAndNewlines()
	if !s.lexConsumeWord("done") {
		panic("Expected 'done' to close for loop")
	}
	return &For{Var: varName, Words: words, Body: body, Redirects: s.collectRedirects()}
}

func (s *Parser) parseForArith() *ForArith {
	s.Advance()
	s.Advance()
	parts := []interface{}{}
	current := []interface{}{}
	parenDepth := 0
	for !s.AtEnd() {
		ch := s.Peek()
		if ch == "(" {
			parenDepth += 1
			current = append(current, s.Advance())
		} else if ch == ")" {
			if parenDepth > 0 {
				parenDepth -= 1
				current = append(current, s.Advance())
			} else if ((s.Pos + 1) < s.Length) && (string(s.Source[(s.Pos+1)]) == ")") {
				parts = append(parts, strings.Join(current, "").Lstrip(" \t"))
				s.Advance()
				s.Advance()
				break
			} else {
				current = append(current, s.Advance())
			}
		} else if (ch == ";") && (parenDepth == 0) {
			parts = append(parts, strings.Join(current, "").Lstrip(" \t"))
			current = []interface{}{}
			s.Advance()
		} else {
			current = append(current, s.Advance())
		}
	}
	if len(parts) != 3 {
		panic("Expected three expressions in for ((;;))")
	}
	init := parts[0]
	cond := parts[1]
	incr := parts[2]
	s.SkipWhitespace()
	if !s.AtEnd() && (s.Peek() == ";") {
		s.Advance()
	}
	s.SkipWhitespaceAndNewlines()
	body := s.parseLoopBody("for loop")
	return &ForArith{Init: init, Cond: cond, Incr: incr, Body: body, Redirects: s.collectRedirects()}
}

func (s *Parser) ParseSelect() *Select {
	s.SkipWhitespace()
	if !s.lexConsumeWord("select") {
		return nil
	}
	s.SkipWhitespace()
	varName := s.PeekWord()
	if varName == "" {
		panic("Expected variable name after 'select'")
	}
	s.ConsumeWord(varName)
	s.SkipWhitespace()
	if s.Peek() == ";" {
		s.Advance()
	}
	s.SkipWhitespaceAndNewlines()
	words := nil
	if s.lexIsAtReservedWord("in") {
		s.lexConsumeWord("in")
		s.SkipWhitespaceAndNewlines()
		words = []interface{}{}
		for true {
			s.SkipWhitespace()
			if s.AtEnd() {
				break
			}
			if isSemicolonNewlineBrace(s.Peek()) {
				if s.Peek() == ";" {
					s.Advance()
				}
				break
			}
			if s.lexIsAtReservedWord("do") {
				break
			}
			word := s.ParseWord(false, false, false)
			if word == nil {
				break
			}
			words = append(words, word)
		}
	}
	s.SkipWhitespaceAndNewlines()
	body := s.parseLoopBody("select")
	return &Select{Var: varName, Words: words, Body: body, Redirects: s.collectRedirects()}
}

func (s *Parser) consumeCaseTerminator() string {
	term := s.lexPeekCaseTerminator()
	if term != "" {
		s.lexNextToken()
		return term
	}
	return ";;"
}

func (s *Parser) ParseCase() *Case {
	var isPattern bool
	if !s.ConsumeWord("case") {
		return nil
	}
	s.setState(ParserstateflagsPstCasestmt)
	s.SkipWhitespace()
	word := s.ParseWord(false, false, false)
	if word == nil {
		panic("Expected word after 'case'")
	}
	s.SkipWhitespaceAndNewlines()
	if !s.lexConsumeWord("in") {
		panic("Expected 'in' after case word")
	}
	s.SkipWhitespaceAndNewlines()
	patterns := []Node{}
	s.setState(ParserstateflagsPstCasepat)
	for true {
		s.SkipWhitespaceAndNewlines()
		if s.lexIsAtReservedWord("esac") {
			saved := s.Pos
			s.SkipWhitespace()
			for (!s.AtEnd() && !isMetachar(s.Peek())) && !isQuote(s.Peek()) {
				s.Advance()
			}
			s.SkipWhitespace()
			isPattern = false
			if !s.AtEnd() && (s.Peek() == ")") {
				if *s.eofToken == ")" {
					isPattern = false
				} else {
					s.Advance()
					s.SkipWhitespace()
					if !s.AtEnd() {
						nextCh := s.Peek()
						if nextCh == ";" {
							isPattern = true
						} else if !isNewlineOrRightParen(nextCh) {
							isPattern = true
						}
					}
				}
			}
			s.Pos = saved
			if !isPattern {
				break
			}
		}
		s.SkipWhitespaceAndNewlines()
		if !s.AtEnd() && (s.Peek() == "(") {
			s.Advance()
			s.SkipWhitespaceAndNewlines()
		}
		patternChars := []interface{}{}
		extglobDepth := 0
		for !s.AtEnd() {
			ch := s.Peek()
			if ch == ")" {
				if extglobDepth > 0 {
					patternChars = append(patternChars, s.Advance())
					extglobDepth -= 1
				} else {
					s.Advance()
					break
				}
			} else if ch == "\\" {
				if ((s.Pos + 1) < s.Length) && (string(s.Source[(s.Pos+1)]) == "\n") {
					s.Advance()
					s.Advance()
				} else {
					patternChars = append(patternChars, s.Advance())
					if !s.AtEnd() {
						patternChars = append(patternChars, s.Advance())
					}
				}
			} else if isExpansionStart(s.Source, s.Pos, "$(") {
				patternChars = append(patternChars, s.Advance())
				patternChars = append(patternChars, s.Advance())
				if !s.AtEnd() && (s.Peek() == "(") {
					patternChars = append(patternChars, s.Advance())
					parenDepth := 2
					for !s.AtEnd() && (parenDepth > 0) {
						c := s.Peek()
						if c == "(" {
							parenDepth += 1
						} else if c == ")" {
							parenDepth -= 1
						}
						patternChars = append(patternChars, s.Advance())
					}
				} else {
					extglobDepth += 1
				}
			} else if (ch == "(") && (extglobDepth > 0) {
				patternChars = append(patternChars, s.Advance())
				extglobDepth += 1
			} else if ((s.extglob && isExtglobPrefix(ch)) && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "(") {
				patternChars = append(patternChars, s.Advance())
				patternChars = append(patternChars, s.Advance())
				extglobDepth += 1
			} else if ch == "[" {
				isCharClass := false
				scanPos := (s.Pos + 1)
				scanDepth := 0
				hasFirstBracketLiteral := false
				if (scanPos < s.Length) && isCaretOrBang(string(s.Source[scanPos])) {
					scanPos += 1
				}
				if (scanPos < s.Length) && (string(s.Source[scanPos]) == "]") {
					if s.Source.Find("]", (scanPos+1)) != -1 {
						scanPos += 1
						hasFirstBracketLiteral = true
					}
				}
				for scanPos < s.Length {
					sc := string(s.Source[scanPos])
					if (sc == "]") && (scanDepth == 0) {
						isCharClass = true
						break
					} else if sc == "[" {
						scanDepth += 1
					} else if (sc == ")") && (scanDepth == 0) {
						break
					} else if (sc == "|") && (scanDepth == 0) {
						break
					}
					scanPos += 1
				}
				if isCharClass {
					patternChars = append(patternChars, s.Advance())
					if !s.AtEnd() && isCaretOrBang(s.Peek()) {
						patternChars = append(patternChars, s.Advance())
					}
					if (hasFirstBracketLiteral && !s.AtEnd()) && (s.Peek() == "]") {
						patternChars = append(patternChars, s.Advance())
					}
					for !s.AtEnd() && (s.Peek() != "]") {
						patternChars = append(patternChars, s.Advance())
					}
					if !s.AtEnd() {
						patternChars = append(patternChars, s.Advance())
					}
				} else {
					patternChars = append(patternChars, s.Advance())
				}
			} else if ch == "'" {
				patternChars = append(patternChars, s.Advance())
				for !s.AtEnd() && (s.Peek() != "'") {
					patternChars = append(patternChars, s.Advance())
				}
				if !s.AtEnd() {
					patternChars = append(patternChars, s.Advance())
				}
			} else if ch == "\"" {
				patternChars = append(patternChars, s.Advance())
				for !s.AtEnd() && (s.Peek() != "\"") {
					if (s.Peek() == "\\") && ((s.Pos + 1) < s.Length) {
						patternChars = append(patternChars, s.Advance())
					}
					patternChars = append(patternChars, s.Advance())
				}
				if !s.AtEnd() {
					patternChars = append(patternChars, s.Advance())
				}
			} else if isWhitespace(ch) {
				if extglobDepth > 0 {
					patternChars = append(patternChars, s.Advance())
				} else {
					s.Advance()
				}
			} else {
				patternChars = append(patternChars, s.Advance())
			}
		}
		pattern := strings.Join(patternChars, "")
		if !pattern != nil {
			panic("Expected pattern in case statement")
		}
		s.SkipWhitespace()
		body := nil
		isEmptyBody := (s.lexPeekCaseTerminator() != "")
		if !isEmptyBody != nil {
			s.SkipWhitespaceAndNewlines()
			if !s.AtEnd() && !s.lexIsAtReservedWord("esac") {
				isAtTerminator := (s.lexPeekCaseTerminator() != "")
				if !isAtTerminator != nil {
					body = s.ParseListUntil(TodoSet)
					s.SkipWhitespace()
				}
			}
		}
		terminator := s.consumeCaseTerminator()
		s.SkipWhitespaceAndNewlines()
		patterns = append(patterns, &CasePattern{Pattern: pattern, Body: body, Terminator: terminator})
	}
	s.clearState(ParserstateflagsPstCasepat)
	s.SkipWhitespaceAndNewlines()
	if !s.lexConsumeWord("esac") {
		s.clearState(ParserstateflagsPstCasestmt)
		panic("Expected 'esac' to close case statement")
	}
	s.clearState(ParserstateflagsPstCasestmt)
	return &Case{Word: word, Patterns: patterns, Redirects: s.collectRedirects()}
}

func (s *Parser) ParseCoproc() *Coproc {
	var body *ArithmeticCommand
	var name interface{}
	s.SkipWhitespace()
	if !s.lexConsumeWord("coproc") {
		return nil
	}
	s.SkipWhitespace()
	name = nil
	ch := ""
	if !s.AtEnd() {
		ch = s.Peek()
	}
	if ch == "{" {
		body = s.ParseBraceGroup()
		if body != nil {
			return &Coproc{Command: body, Name: name}
		}
	}
	if ch == "(" {
		if ((s.Pos + 1) < s.Length) && (string(s.Source[(s.Pos+1)]) == "(") {
			body = s.ParseArithmeticCommand()
			if body != nil {
				return &Coproc{Command: body, Name: name}
			}
		}
		body = s.ParseSubshell()
		if body != nil {
			return &Coproc{Command: body, Name: name}
		}
	}
	nextWord := s.lexPeekReservedWord()
	if (nextWord != "") && strings.Contains(CompoundKeywords, nextWord) {
		body = s.ParseCompoundCommand()
		if body != nil {
			return &Coproc{Command: body, Name: name}
		}
	}
	wordStart := s.Pos
	potentialName := s.PeekWord()
	if potentialName != "" {
		for (!s.AtEnd() && !isMetachar(s.Peek())) && !isQuote(s.Peek()) {
			s.Advance()
		}
		s.SkipWhitespace()
		ch = ""
		if !s.AtEnd() {
			ch = s.Peek()
		}
		nextWord = s.lexPeekReservedWord()
		if isValidIdentifier(potentialName) {
			if ch == "{" {
				name = potentialName
				body = s.ParseBraceGroup()
				if body != nil {
					return &Coproc{Command: body, Name: name}
				}
			} else if ch == "(" {
				name = potentialName
				if ((s.Pos + 1) < s.Length) && (string(s.Source[(s.Pos+1)]) == "(") {
					body = s.ParseArithmeticCommand()
				} else {
					body = s.ParseSubshell()
				}
				if body != nil {
					return &Coproc{Command: body, Name: name}
				}
			} else if (nextWord != "") && strings.Contains(CompoundKeywords, nextWord) {
				name = potentialName
				body = s.ParseCompoundCommand()
				if body != nil {
					return &Coproc{Command: body, Name: name}
				}
			}
		}
		s.Pos = wordStart
	}
	body = s.ParseCommand()
	if body != nil {
		return &Coproc{Command: body, Name: name}
	}
	panic("Expected command after coproc")
}

func (s *Parser) ParseFunction() *Function {
	s.SkipWhitespace()
	if s.AtEnd() {
		return nil
	}
	savedPos := s.Pos
	if s.lexIsAtReservedWord("function") {
		s.lexConsumeWord("function")
		s.SkipWhitespace()
		name := s.PeekWord()
		if name == "" {
			s.Pos = savedPos
			return nil
		}
		s.ConsumeWord(name)
		s.SkipWhitespace()
		if !s.AtEnd() && (s.Peek() == "(") {
			if ((s.Pos + 1) < s.Length) && (string(s.Source[(s.Pos+1)]) == ")") {
				s.Advance()
				s.Advance()
			}
		}
		s.SkipWhitespaceAndNewlines()
		body := s.parseCompoundCommand()
		if body == nil {
			panic("Expected function body")
		}
		return &Function{Name: name, Body: body}
	}
	name = s.PeekWord()
	if (name == "") || strings.Contains(ReservedWords, name) {
		return nil
	}
	if looksLikeAssignment(name) {
		return nil
	}
	s.SkipWhitespace()
	nameStart := s.Pos
	for ((!s.AtEnd() && !isMetachar(s.Peek())) && !isQuote(s.Peek())) && !isParen(s.Peek()) {
		s.Advance()
	}
	name = substring(s.Source, nameStart, s.Pos)
	if !(name != "") {
		s.Pos = savedPos
		return nil
	}
	braceDepth := 0
	i := 0
	for i < len(name) {
		if isExpansionStart(name, i, "${") {
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
		s.Pos = savedPos
		return nil
	}
	posAfterName := s.Pos
	s.SkipWhitespace()
	hasWhitespace := (s.Pos > posAfterName)
	if (!hasWhitespace != nil && (name != "")) && strings.Contains("*?@+!$", string(name[(len(name)-1)])) {
		s.Pos = savedPos
		return nil
	}
	if s.AtEnd() || (s.Peek() != "(") {
		s.Pos = savedPos
		return nil
	}
	s.Advance()
	s.SkipWhitespace()
	if s.AtEnd() || (s.Peek() != ")") {
		s.Pos = savedPos
		return nil
	}
	s.Advance()
	s.SkipWhitespaceAndNewlines()
	body = s.parseCompoundCommand()
	if body == nil {
		panic("Expected function body")
	}
	return &Function{Name: name, Body: body}
}

func (s *Parser) parseCompoundCommand() Node {
	result := s.ParseBraceGroup()
	if result != nil {
		return result
	}
	if ((!s.AtEnd() && (s.Peek() == "(")) && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "(") {
		result = s.ParseArithmeticCommand()
		if result != nil {
			return result
		}
	}
	result = s.ParseSubshell()
	if result != nil {
		return result
	}
	result = s.ParseConditionalExpr()
	if result != nil {
		return result
	}
	result = s.ParseIf()
	if result != nil {
		return result
	}
	result = s.ParseWhile()
	if result != nil {
		return result
	}
	result = s.ParseUntil()
	if result != nil {
		return result
	}
	result = s.ParseFor()
	if result != nil {
		return result
	}
	result = s.ParseCase()
	if result != nil {
		return result
	}
	result = s.ParseSelect()
	if result != nil {
		return result
	}
	return nil
}

func (s *Parser) atListUntilTerminator(stopWords map[string]struct{}) bool {
	if s.AtEnd() {
		return true
	}
	if s.Peek() == ")" {
		return true
	}
	if s.Peek() == "}" {
		nextPos := (s.Pos + 1)
		if (nextPos >= s.Length) || isWordEndContext(string(s.Source[nextPos])) {
			return true
		}
	}
	reserved := s.lexPeekReservedWord()
	if (reserved != "") && strings.Contains(stopWords, reserved) {
		return true
	}
	if s.lexPeekCaseTerminator() != "" {
		return true
	}
	return false
}

func (s *Parser) ParseListUntil(stopWords map[string]struct{}) Node {
	s.SkipWhitespaceAndNewlines()
	reserved := s.lexPeekReservedWord()
	if (reserved != "") && strings.Contains(stopWords, reserved) {
		return nil
	}
	pipeline := s.ParsePipeline()
	if pipeline == nil {
		return nil
	}
	parts := []Node{pipeline}
	for true {
		s.SkipWhitespace()
		op := s.ParseListOperator()
		if op == "" {
			if !s.AtEnd() && (s.Peek() == "\n") {
				s.Advance()
				s.gatherHeredocBodies()
				if s.cmdsubHeredocEnd != nil && (s.cmdsubHeredocEnd > s.Pos) {
					s.Pos = s.cmdsubHeredocEnd
					s.cmdsubHeredocEnd = nil
				}
				s.SkipWhitespaceAndNewlines()
				if s.atListUntilTerminator(stopWords) {
					break
				}
				nextOp := s.peekListOperator()
				if strings.Contains(struct{ Single, Double bool }{"&", ";"}, nextOp) {
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
			s.SkipWhitespaceAndNewlines()
			if s.atListUntilTerminator(stopWords) {
				break
			}
			parts = append(parts, &Operator{Op: op})
		} else if op == "&" {
			parts = append(parts, &Operator{Op: op})
			s.SkipWhitespaceAndNewlines()
			if s.atListUntilTerminator(stopWords) {
				break
			}
		} else if strings.Contains(struct{ Single, Double bool }{"&&", "||"}, op) {
			parts = append(parts, &Operator{Op: op})
			s.SkipWhitespaceAndNewlines()
		} else {
			parts = append(parts, &Operator{Op: op})
		}
		if s.atListUntilTerminator(stopWords) {
			break
		}
		pipeline = s.ParsePipeline()
		if pipeline == nil {
			panic(("Expected command after " + op))
		}
		parts = append(parts, pipeline)
	}
	if len(parts) == 1 {
		return parts[0]
	}
	return &List{Parts: parts}
}

func (s *Parser) ParseCompoundCommand() Node {
	s.SkipWhitespace()
	if s.AtEnd() {
		return nil
	}
	ch := s.Peek()
	if ((ch == "(") && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "(") {
		result := s.ParseArithmeticCommand()
		if result != nil {
			return result
		}
	}
	if ch == "(" {
		return s.ParseSubshell()
	}
	if ch == "{" {
		result = s.ParseBraceGroup()
		if result != nil {
			return result
		}
	}
	if ((ch == "[") && ((s.Pos + 1) < s.Length)) && (string(s.Source[(s.Pos+1)]) == "[") {
		result = s.ParseConditionalExpr()
		if result != nil {
			return result
		}
	}
	reserved := s.lexPeekReservedWord()
	if (reserved == "") && s.inProcessSub {
		word := s.PeekWord()
		if ((word != "") && (len(word) > 1)) && (string(word[0]) == "}") {
			keywordWord := word[1:]
			if strings.Contains(ReservedWords, keywordWord) || strings.Contains(struct{}{F0: "{", F1: "}", F2: "[[", F3: "]]", F4: "!", F5: "time"}, keywordWord) {
				reserved = keywordWord
			}
		}
	}
	if strings.Contains(struct{}{F0: "fi", F1: "then", F2: "elif", F3: "else", F4: "done", F5: "esac", F6: "do", F7: "in"}, reserved) {
		panic(fmt.Sprintf("Unexpected reserved word '%v'", reserved))
	}
	if reserved == "if" {
		return s.ParseIf()
	}
	if reserved == "while" {
		return s.ParseWhile()
	}
	if reserved == "until" {
		return s.ParseUntil()
	}
	if reserved == "for" {
		return s.ParseFor()
	}
	if reserved == "select" {
		return s.ParseSelect()
	}
	if reserved == "case" {
		return s.ParseCase()
	}
	if reserved == "function" {
		return s.ParseFunction()
	}
	if reserved == "coproc" {
		return s.ParseCoproc()
	}
	func_ := s.ParseFunction()
	if func_ != nil {
		return func_
	}
	return s.ParseCommand()
}

func (s *Parser) ParsePipeline() Node {
	var result *Time
	s.SkipWhitespace()
	prefixOrder := ""
	timePosix := false
	if s.lexIsAtReservedWord("time") {
		s.lexConsumeWord("time")
		prefixOrder = "time"
		s.SkipWhitespace()
		if !s.AtEnd() && (s.Peek() == "-") {
			saved := s.Pos
			s.Advance()
			if !s.AtEnd() && (s.Peek() == "p") {
				s.Advance()
				if s.AtEnd() || isMetachar(s.Peek()) {
					timePosix = true
				} else {
					s.Pos = saved
				}
			} else {
				s.Pos = saved
			}
		}
		s.SkipWhitespace()
		if !s.AtEnd() && startsWithAt(s.Source, s.Pos, "--") {
			if ((s.Pos + 2) >= s.Length) || isWhitespace(string(s.Source[(s.Pos+2)])) {
				s.Advance()
				s.Advance()
				timePosix = true
				s.SkipWhitespace()
			}
		}
		for s.lexIsAtReservedWord("time") {
			s.lexConsumeWord("time")
			s.SkipWhitespace()
			if !s.AtEnd() && (s.Peek() == "-") {
				saved = s.Pos
				s.Advance()
				if !s.AtEnd() && (s.Peek() == "p") {
					s.Advance()
					if s.AtEnd() || isMetachar(s.Peek()) {
						timePosix = true
					} else {
						s.Pos = saved
					}
				} else {
					s.Pos = saved
				}
			}
		}
		s.SkipWhitespace()
		if !s.AtEnd() && (s.Peek() == "!") {
			if (((s.Pos + 1) >= s.Length) || isNegationBoundary(string(s.Source[(s.Pos+1)]))) && !s.isBangFollowedByProcsub() {
				s.Advance()
				prefixOrder = "time_negation"
				s.SkipWhitespace()
			}
		}
	} else if !s.AtEnd() && (s.Peek() == "!") {
		if (((s.Pos + 1) >= s.Length) || isNegationBoundary(string(s.Source[(s.Pos+1)]))) && !s.isBangFollowedByProcsub() {
			s.Advance()
			s.SkipWhitespace()
			inner := s.ParsePipeline()
			if inner != nil && (inner.Kind == "negation") {
				if inner.Pipeline != nil {
					return inner.Pipeline
				} else {
					return &Command{Words: []interface{}{}}
				}
			}
			return &Negation{Pipeline: inner}
		}
	}
	result = s.parseSimplePipeline()
	if prefixOrder == "time" {
		result = &Time{Pipeline: result, Posix: timePosix}
	} else if prefixOrder == "negation" {
		result = &Negation{Pipeline: result}
	} else if prefixOrder == "time_negation" {
		result = &Time{Pipeline: result, Posix: timePosix}
		result = &Negation{Pipeline: result}
	} else if prefixOrder == "negation_time" {
		result = &Time{Pipeline: result, Posix: timePosix}
		result = &Negation{Pipeline: result}
	} else if result == nil {
		return nil
	}
	return result
}

func (s *Parser) parseSimplePipeline() Node {
	cmd := s.ParseCompoundCommand()
	if cmd == nil {
		return nil
	}
	commands := []Node{cmd}
	for true {
		s.SkipWhitespace()
		tokenType, value := s.lexPeekOperator()
		if tokenType == 0 {
			break
		}
		if (tokenType != TokentypePipe) && (tokenType != TokentypePipeAmp) {
			break
		}
		s.lexNextToken()
		isPipeBoth := (tokenType == TokentypePipeAmp)
		s.SkipWhitespaceAndNewlines()
		if isPipeBoth != nil {
			commands = append(commands, &PipeBoth{})
		}
		cmd = s.ParseCompoundCommand()
		if cmd == nil {
			panic("Expected command after |")
		}
		commands = append(commands, cmd)
	}
	if len(commands) == 1 {
		return commands[0]
	}
	return &Pipeline{Commands: commands}
}

func (s *Parser) ParseListOperator() string {
	s.SkipWhitespace()
	tokenType, _ := s.lexPeekOperator()
	if tokenType == 0 {
		return ""
	}
	if tokenType == TokentypeAndAnd {
		s.lexNextToken()
		return "&&"
	}
	if tokenType == TokentypeOrOr {
		s.lexNextToken()
		return "||"
	}
	if tokenType == TokentypeSemi {
		s.lexNextToken()
		return ";"
	}
	if tokenType == TokentypeAmp {
		s.lexNextToken()
		return "&"
	}
	return ""
}

func (s *Parser) peekListOperator() string {
	savedPos := s.Pos
	op := s.ParseListOperator()
	s.Pos = savedPos
	return op
}

func (s *Parser) ParseList(newlineAsSeparator bool) Node {
	if newlineAsSeparator {
		s.SkipWhitespaceAndNewlines()
	} else {
		s.SkipWhitespace()
	}
	pipeline := s.ParsePipeline()
	if pipeline == nil {
		return nil
	}
	parts := []Node{pipeline}
	if s.inState(ParserstateflagsPstEoftoken) && s.atEofToken() {
		return func() interface{} {
			if len(parts) == 1 {
				return parts[0]
			} else {
				return &List{Parts: parts}
			}
		}()
	}
	for true {
		s.SkipWhitespace()
		op := s.ParseListOperator()
		if op == "" {
			if !s.AtEnd() && (s.Peek() == "\n") {
				if !newlineAsSeparator {
					break
				}
				s.Advance()
				s.gatherHeredocBodies()
				if s.cmdsubHeredocEnd != nil && (s.cmdsubHeredocEnd > s.Pos) {
					s.Pos = s.cmdsubHeredocEnd
					s.cmdsubHeredocEnd = nil
				}
				s.SkipWhitespaceAndNewlines()
				if s.AtEnd() || s.atListTerminatingBracket() {
					break
				}
				nextOp := s.peekListOperator()
				if strings.Contains(struct{ Single, Double bool }{"&", ";"}, nextOp) {
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
		parts = append(parts, &Operator{Op: op})
		if strings.Contains(struct{ Single, Double bool }{"&&", "||"}, op) {
			s.SkipWhitespaceAndNewlines()
		} else if op == "&" {
			s.SkipWhitespace()
			if s.AtEnd() || s.atListTerminatingBracket() {
				break
			}
			if s.Peek() == "\n" {
				if newlineAsSeparator {
					s.SkipWhitespaceAndNewlines()
					if s.AtEnd() || s.atListTerminatingBracket() {
						break
					}
				} else {
					break
				}
			}
		} else if op == ";" {
			s.SkipWhitespace()
			if s.AtEnd() || s.atListTerminatingBracket() {
				break
			}
			if s.Peek() == "\n" {
				if newlineAsSeparator {
					s.SkipWhitespaceAndNewlines()
					if s.AtEnd() || s.atListTerminatingBracket() {
						break
					}
				} else {
					break
				}
			}
		}
		pipeline = s.ParsePipeline()
		if pipeline == nil {
			panic(("Expected command after " + op))
		}
		parts = append(parts, pipeline)
		if s.inState(ParserstateflagsPstEoftoken) && s.atEofToken() {
			break
		}
	}
	if len(parts) == 1 {
		return parts[0]
	}
	return &List{Parts: parts}
}

func (s *Parser) ParseComment() Node {
	if s.AtEnd() || (s.Peek() != "#") {
		return nil
	}
	start := s.Pos
	for !s.AtEnd() && (s.Peek() != "\n") {
		s.Advance()
	}
	text := substring(s.Source, start, s.Pos)
	return &Comment{Text: text}
}

func (s *Parser) Parse() []Node {
	source := s.Source.Strip()
	if !source != nil {
		return []Node{&Empty{}}
	}
	results := []Node{}
	for true {
		s.SkipWhitespace()
		for !s.AtEnd() && (s.Peek() == "\n") {
			s.Advance()
		}
		if s.AtEnd() {
			break
		}
		comment := s.ParseComment()
		if !comment {
			break
		}
	}
	for !s.AtEnd() {
		result := s.ParseList(true)
		if result != nil {
			results = append(results, result)
		}
		s.SkipWhitespace()
		foundNewline := false
		for !s.AtEnd() && (s.Peek() == "\n") {
			foundNewline = true
			s.Advance()
			s.gatherHeredocBodies()
			if s.cmdsubHeredocEnd != nil && (s.cmdsubHeredocEnd > s.Pos) {
				s.Pos = s.cmdsubHeredocEnd
				s.cmdsubHeredocEnd = nil
			}
			s.SkipWhitespace()
		}
		if !foundNewline && !s.AtEnd() {
			panic("Syntax error")
		}
	}
	if !results {
		return []Node{&Empty{}}
	}
	if ((s.sawNewlineInSingleQuote && (s.Source != "")) && (string(s.Source[(len(s.Source)-1)]) == "\\")) && !((len(s.Source) >= 3) && (s.Source[(len(s.Source)-3):(len(s.Source)-1)] == "\\\n")) {
		if !s.lastWordOnOwnLine(results) {
			s.stripTrailingBackslashFromLastWord(results)
		}
	}
	return results
}

func (s *Parser) lastWordOnOwnLine(nodes []Node) bool {
	return (len(nodes) >= 2)
}

func (s *Parser) stripTrailingBackslashFromLastWord(nodes []Node) {
	if !nodes {
		return
	}
	lastNode := nodes[(len(nodes) - 1)]
	lastWord := s.findLastWord(lastNode)
	if lastWord != nil && lastWord.Value.Endswith("\\") {
		lastWord.Value = substring(lastWord.Value, 0, (len(lastWord.Value) - 1))
		if (!lastWord.Value != nil && Isinstance(lastNode, Command)) && lastNode.Words != nil {
			lastNode.Words[len(lastNode.Words)-1]
		}
	}
}

func (s *Parser) findLastWord(node Node) *Word {
	if Isinstance(node, Word) {
		return node
	}
	if Isinstance(node, Command) {
		if node.Words != nil {
			lastWord := node.Words[(len(node.Words) - 1)]
			if lastWord.Value.Endswith("\\") {
				return lastWord
			}
		}
		if node.Redirects != nil {
			lastRedirect := node.Redirects[(len(node.Redirects) - 1)]
			if Isinstance(lastRedirect, Redirect) {
				return lastRedirect.Target
			}
		}
		if node.Words != nil {
			return node.Words[(len(node.Words) - 1)]
		}
	}
	if Isinstance(node, Pipeline) {
		if node.Commands != nil {
			return s.findLastWord(node.Commands[(len(node.Commands) - 1)])
		}
	}
	if Isinstance(node, List) {
		if node.Parts != nil {
			return s.findLastWord(node.Parts[(len(node.Parts) - 1)])
		}
	}
	return nil
}

func isHexDigit(c string) bool {
	return ((((c >= "0") && (c <= "9")) || ((c >= "a") && (c <= "f"))) || ((c >= "A") && (c <= "F")))
}

func isOctalDigit(c string) bool {
	return ((c >= "0") && (c <= "7"))
}

func getAnsiEscape(c string) int {
	return AnsiCEscapes.Get(c, -1)
}

func isWhitespace(c string) bool {
	return (((c == " ") || (c == "\t")) || (c == "\n"))
}

func isWhitespaceNoNewline(c string) bool {
	return ((c == " ") || (c == "\t"))
}

func substring(s string, start int, end int) string {
	if end > len(s) {
		end = len(s)
	}
	return s[start:end]
}

func startsWithAt(s string, pos int, prefix string) bool {
	return s.Startswith(prefix, pos)
}

func countConsecutiveDollarsBefore(s string, pos int) int {
	count := 0
	k := (pos - 1)
	for (k >= 0) && (string(s[k]) == "$") {
		bsCount := 0
		j := (k - 1)
		for (j >= 0) && (string(s[j]) == "\\") {
			bsCount += 1
			j -= 1
		}
		if (bsCount % 2) == 1 {
			break
		}
		count += 1
		k -= 1
	}
	return count
}

func isExpansionStart(s string, pos int, delimiter string) bool {
	if !startsWithAt(s, pos, delimiter) {
		return false
	}
	return ((countConsecutiveDollarsBefore(s, pos) % 2) == 0)
}

func sublist(lst []Node, start int, end int) []Node {
	return lst[start:end]
}

func repeatStr(s string, n int) string {
	result := []interface{}{}
	i := 0
	for i < n {
		result = append(result, s)
		i += 1
	}
	return strings.Join(result, "")
}

func stripLineContinuationsCommentAware(text string) string {
	result := []interface{}{}
	i := 0
	inComment := false
	quote := &QuoteState{}
	for i < len(text) {
		c := string(text[i])
		if ((c == "\\") && ((i + 1) < len(text))) && (string(text[(i+1)]) == "\n") {
			numPrecedingBackslashes := 0
			j := (i - 1)
			for (j >= 0) && (string(text[j]) == "\\") {
				numPrecedingBackslashes += 1
				j -= 1
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
			i += 1
			continue
		}
		if ((c == "'") && !quote.Double != nil) && !inComment {
			quote.Single = !quote.Single
		} else if ((c == "\"") && !quote.Single != nil) && !inComment {
			quote.Double = !quote.Double
		} else if ((c == "#") && !quote.Single != nil) && !inComment {
			inComment = true
		}
		result = append(result, c)
		i += 1
	}
	return strings.Join(result, "")
}

func appendRedirects(base string, redirects []Node) string {
	if redirects {
		parts := []interface{}{}
		for _, r := range redirects {
			parts = append(parts, r.ToSexp())
		}
		return ((base + " ") + strings.Join(parts, " "))
	}
	return base
}

func formatArithVal(s string) string {
	w := &Word{Value: s, Parts: []interface{}{}}
	val := w.expandAllAnsiCQuotes(s)
	val = w.stripLocaleStringDollars(val)
	val = w.formatCommandSubstitutions(val)
	val = val.Replace("\\", "\\\\").Replace("\"", "\\\"")
	val = val.Replace("\n", "\\n").Replace("\t", "\\t")
	return val
}

func consumeSingleQuote(s string, start int) (int, []string) {
	chars := []string{"'"}
	i := (start + 1)
	for (i < len(s)) && (string(s[i]) != "'") {
		chars = append(chars, string(s[i]))
		i += 1
	}
	if i < len(s) {
		chars = append(chars, string(s[i]))
		i += 1
	}
	return i, chars
}

func consumeDoubleQuote(s string, start int) (int, []string) {
	chars := []string{"\""}
	i := (start + 1)
	for (i < len(s)) && (string(s[i]) != "\"") {
		if (string(s[i]) == "\\") && ((i + 1) < len(s)) {
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
	return i, chars
}

func hasBracketClose(s string, start int, depth int) bool {
	i := start
	for i < len(s) {
		if string(s[i]) == "]" {
			return true
		}
		if ((string(s[i]) == "|") || (string(s[i]) == ")")) && (depth == 0) {
			return false
		}
		i += 1
	}
	return false
}

func consumeBracketClass(s string, start int, depth int) (int, []string, bool) {
	scanPos := (start + 1)
	if (scanPos < len(s)) && ((string(s[scanPos]) == "!") || (string(s[scanPos]) == "^")) {
		scanPos += 1
	}
	if (scanPos < len(s)) && (string(s[scanPos]) == "]") {
		if hasBracketClose(s, (scanPos + 1), depth) {
			scanPos += 1
		}
	}
	isBracket := false
	for scanPos < len(s) {
		if string(s[scanPos]) == "]" {
			isBracket = true
			break
		}
		if (string(s[scanPos]) == ")") && (depth == 0) {
			break
		}
		if (string(s[scanPos]) == "|") && (depth == 0) {
			break
		}
		scanPos += 1
	}
	if !isBracket {
		return (start + 1), []string{"["}, false
	}
	chars := []string{"["}
	i := (start + 1)
	if (i < len(s)) && ((string(s[i]) == "!") || (string(s[i]) == "^")) {
		chars = append(chars, string(s[i]))
		i += 1
	}
	if (i < len(s)) && (string(s[i]) == "]") {
		if hasBracketClose(s, (i + 1), depth) {
			chars = append(chars, string(s[i]))
			i += 1
		}
	}
	for (i < len(s)) && (string(s[i]) != "]") {
		chars = append(chars, string(s[i]))
		i += 1
	}
	if i < len(s) {
		chars = append(chars, string(s[i]))
		i += 1
	}
	return i, chars, true
}

func formatCondBody(node Node) string {
	kind := node.Kind
	if kind == "unary-test" {
		operandVal := node.Operand.GetCondFormattedValue()
		return ((node.Op + " ") + operandVal)
	}
	if kind == "binary-test" {
		leftVal := node.Left.GetCondFormattedValue()
		rightVal := node.Right.GetCondFormattedValue()
		return ((((leftVal + " ") + node.Op) + " ") + rightVal)
	}
	if kind == "cond-and" {
		return ((formatCondBody(node.Left) + " && ") + formatCondBody(node.Right))
	}
	if kind == "cond-or" {
		return ((formatCondBody(node.Left) + " || ") + formatCondBody(node.Right))
	}
	if kind == "cond-not" {
		return ("! " + formatCondBody(node.Operand))
	}
	if kind == "cond-paren" {
		return (("( " + formatCondBody(node.Inner)) + " )")
	}
	return ""
}

func startsWithSubshell(node Node) bool {
	if node.Kind == "subshell" {
		return true
	}
	if node.Kind == "list" {
		for _, p := range node.Parts {
			if p.Kind != "operator" {
				return startsWithSubshell(p)
			}
		}
		return false
	}
	if node.Kind == "pipeline" {
		if node.Commands != nil {
			return startsWithSubshell(node.Commands[0])
		}
		return false
	}
	return false
}

func formatCmdsubNode(node Node, indent int, inProcsub bool, compactRedirects bool, procsubFirst bool) string {
	var result interface{}
	var formatted interface{}
	var hasHeredoc bool
	var skippedSemi bool
	var last string
	var firstNl interface{}
	var body interface{}
	if node == nil {
		return ""
	}
	sp := repeatStr(" ", indent)
	innerSp := repeatStr(" ", (indent + 4))
	if node.Kind == "empty" {
		return ""
	}
	if node.Kind == "command" {
		parts := []interface{}{}
		for _, w := range node.Words {
			val := w.expandAllAnsiCQuotes(w.Value)
			val = w.stripLocaleStringDollars(val)
			val = w.normalizeArrayWhitespace(val)
			val = w.formatCommandSubstitutions(val)
			parts = append(parts, val)
		}
		heredocs := []interface{}{}
		for _, r := range node.Redirects {
			if r.Kind == "heredoc" {
				heredocs = append(heredocs, r)
			}
		}
		for _, r := range node.Redirects {
			parts = append(parts, formatRedirect(r))
		}
		if (compactRedirects && node.Words != nil) && node.Redirects != nil {
			wordParts := parts[:len(node.Words)]
			redirectParts := parts[len(node.Words):]
			result = (strings.Join(wordParts, " ") + strings.Join(redirectParts, ""))
		} else {
			result = strings.Join(parts, " ")
		}
		for _, h := range heredocs {
			result = (result + formatHeredocBody(h))
		}
		return result
	}
	if node.Kind == "pipeline" {
		cmds := []interface{}{}
		i := 0
		for i < len(node.Commands) {
			cmd := node.Commands[i]
			if cmd.Kind == "pipe-both" {
				i += 1
				continue
			}
			needsRedirect := (((i + 1) < len(node.Commands)) && (node.Commands[(i+1)].Kind == "pipe-both"))
			cmds = append(cmds, struct{ Single, Double bool }{cmd, needsRedirect})
			i += 1
		}
		resultParts := []interface{}{}
		idx := 0
		for idx < len(cmds) {
			unknownLvalue := cmds[idx]
			formatted = formatCmdsubNode(cmd, indent, inProcsub, false, (procsubFirst && (idx == 0)))
			isLast := (idx == (len(cmds) - 1))
			hasHeredoc = false
			if (cmd.Kind == "command") && cmd.Redirects != nil {
				for _, r := range cmd.Redirects {
					if r.Kind == "heredoc" {
						hasHeredoc = true
						break
					}
				}
			}
			if needsRedirect != nil {
				if hasHeredoc {
					firstNl = formatted.Find("\n")
					if firstNl != -1 {
						formatted = ((formatted[:firstNl] + " 2>&1") + formatted[firstNl:])
					} else {
						formatted = (formatted + " 2>&1")
					}
				} else {
					formatted = (formatted + " 2>&1")
				}
			}
			if !isLast != nil && hasHeredoc {
				firstNl = formatted.Find("\n")
				if firstNl != -1 {
					formatted = ((formatted[:firstNl] + " |") + formatted[firstNl:])
				}
				resultParts = append(resultParts, formatted)
			} else {
				resultParts = append(resultParts, formatted)
			}
			idx += 1
		}
		compactPipe := ((inProcsub && cmds) && (cmds[0][0].Kind == "subshell"))
		result = ""
		idx = 0
		for idx < len(resultParts) {
			part := resultParts[idx]
			if idx > 0 {
				if result.Endswith("\n") {
					result = ((result + "  ") + part)
				} else if compactPipe != nil {
					result = ((result + "|") + part)
				} else {
					result = ((result + " | ") + part)
				}
			} else {
				result = part
			}
			idx += 1
		}
		return result
	}
	if node.Kind == "list" {
		hasHeredoc = false
		for _, p := range node.Parts {
			if (p.Kind == "command") && p.Redirects != nil {
				for _, r := range p.Redirects {
					if r.Kind == "heredoc" {
						hasHeredoc = true
						break
					}
				}
			} else if p.Kind == "pipeline" {
				for _, cmd := range p.Commands {
					if (cmd.Kind == "command") && cmd.Redirects != nil {
						for _, r := range cmd.Redirects {
							if r.Kind == "heredoc" {
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
		result = []interface{}{}
		skippedSemi = false
		cmdCount := 0
		for _, p := range node.Parts {
			if p.Kind == "operator" {
				if p.Op == ";" {
					if (result != "") && string(result[(len(result)-1)]).Endswith("\n") {
						skippedSemi = true
						continue
					}
					if ((len(result) >= 3) && (string(result[(len(result)-2)]) == "\n")) && string(result[(len(result)-3)]).Endswith("\n") {
						skippedSemi = true
						continue
					}
					result = append(result, ";")
					skippedSemi = false
				} else if p.Op == "\n" {
					if (result != "") && (string(result[(len(result)-1)]) == ";") {
						skippedSemi = false
						continue
					}
					if (result != "") && string(result[(len(result)-1)]).Endswith("\n") {
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
					if ((result != "") && strings.Contains(string(result[(len(result)-1)]), "<<")) && strings.Contains(string(result[(len(result)-1)]), "\n") {
						last = string(result[(len(result) - 1)])
						if strings.Contains(last, " |") || last.Startswith("|") {
							result[(len(result) - 1)] = (last + " &")
						} else {
							firstNl = last.Find("\n")
							result[(len(result) - 1)] = ((last[:firstNl] + " &") + last[firstNl:])
						}
					} else {
						result = append(result, " &")
					}
				} else if ((result != "") && strings.Contains(string(result[(len(result)-1)]), "<<")) && strings.Contains(string(result[(len(result)-1)]), "\n") {
					last = string(result[(len(result) - 1)])
					firstNl = last.Find("\n")
					result[(len(result) - 1)] = ((((last[:firstNl] + " ") + p.Op) + " ") + last[firstNl:])
				} else {
					result = append(result, (" " + p.Op))
				}
			} else {
				if (result != "") && !string(result[(len(result)-1)]).Endswith(struct{ Single, Double bool }{" ", "\n"}) {
					result = append(result, " ")
				}
				formattedCmd := formatCmdsubNode(p, indent, inProcsub, compactRedirects, (procsubFirst && (cmdCount == 0)))
				if len(result) > 0 {
					last = string(result[(len(result) - 1)])
					if strings.Contains(last, " || \n") || strings.Contains(last, " && \n") {
						formattedCmd = (" " + formattedCmd)
					}
				}
				if skippedSemi {
					formattedCmd = (" " + formattedCmd)
					skippedSemi = false
				}
				result = append(result, formattedCmd)
				cmdCount += 1
			}
		}
		s := strings.Join(result, "")
		if strings.Contains(s, " &\n") && s.Endswith("\n") {
			return (s + " ")
		}
		for s.Endswith(";") {
			s = substring(s, 0, (len(s) - 1))
		}
		if !hasHeredoc {
			for s.Endswith("\n") {
				s = substring(s, 0, (len(s) - 1))
			}
		}
		return s
	}
	if node.Kind == "if" {
		cond := formatCmdsubNode(node.Condition, indent)
		thenBody := formatCmdsubNode(node.ThenBody, (indent + 4))
		result = ((((("if " + cond) + "; then\n") + innerSp) + thenBody) + ";")
		if node.ElseBody != nil {
			elseBody := formatCmdsubNode(node.ElseBody, (indent + 4))
			result = ((((((result + "\n") + sp) + "else\n") + innerSp) + elseBody) + ";")
		}
		result = (((result + "\n") + sp) + "fi")
		return result
	}
	if node.Kind == "while" {
		cond = formatCmdsubNode(node.Condition, indent)
		body = formatCmdsubNode(node.Body, (indent + 4))
		result = ((((((("while " + cond) + "; do\n") + innerSp) + body) + ";\n") + sp) + "done")
		if node.Redirects != nil {
			for _, r := range node.Redirects {
				result = ((result + " ") + formatRedirect(r))
			}
		}
		return result
	}
	if node.Kind == "until" {
		cond = formatCmdsubNode(node.Condition, indent)
		body = formatCmdsubNode(node.Body, (indent + 4))
		result = ((((((("until " + cond) + "; do\n") + innerSp) + body) + ";\n") + sp) + "done")
		if node.Redirects != nil {
			for _, r := range node.Redirects {
				result = ((result + " ") + formatRedirect(r))
			}
		}
		return result
	}
	if node.Kind == "for" {
		var_ := node.Var
		body = formatCmdsubNode(node.Body, (indent + 4))
		if node.Words != nil {
			wordVals := []interface{}{}
			for _, w := range node.Words {
				wordVals = append(wordVals, w.Value)
			}
			words := strings.Join(wordVals, " ")
			if words != nil {
				result = ((((((((((("for " + var_) + " in ") + words) + ";\n") + sp) + "do\n") + innerSp) + body) + ";\n") + sp) + "done")
			} else {
				result = ((((((((("for " + var_) + " in ;\n") + sp) + "do\n") + innerSp) + body) + ";\n") + sp) + "done")
			}
		} else {
			result = ((((((((("for " + var_) + " in \"$@\";\n") + sp) + "do\n") + innerSp) + body) + ";\n") + sp) + "done")
		}
		if node.Redirects != nil {
			for _, r := range node.Redirects {
				result = ((result + " ") + formatRedirect(r))
			}
		}
		return result
	}
	if node.Kind == "for-arith" {
		body = formatCmdsubNode(node.Body, (indent + 4))
		result = ((((((((((("for ((" + node.Init) + "; ") + node.Cond) + "; ") + node.Incr) + "))\ndo\n") + innerSp) + body) + ";\n") + sp) + "done")
		if node.Redirects != nil {
			for _, r := range node.Redirects {
				result = ((result + " ") + formatRedirect(r))
			}
		}
		return result
	}
	if node.Kind == "case" {
		word := node.Word.Value
		patterns := []interface{}{}
		i = 0
		for i < len(node.Patterns) {
			p := node.Patterns[i]
			pat := p.Pattern.Replace("|", " | ")
			if p.Body != nil {
				body = formatCmdsubNode(p.Body, (indent + 8))
			} else {
				body = ""
			}
			term := p.Terminator
			patIndent := repeatStr(" ", (indent + 8))
			termIndent := repeatStr(" ", (indent + 4))
			bodyPart := func() string {
				if body {
					return ((patIndent + body) + "\n")
				} else {
					return "\n"
				}
			}()
			if i == 0 {
				patterns = append(patterns, (((((" " + pat) + ")\n") + bodyPart) + termIndent) + term))
			} else {
				patterns = append(patterns, ((((pat + ")\n") + bodyPart) + termIndent) + term))
			}
			i += 1
		}
		patternStr := strings.Join(patterns, ("\n" + repeatStr(" ", (indent+4))))
		redirects := ""
		if node.Redirects != nil {
			redirectParts = []interface{}{}
			for _, r := range node.Redirects {
				redirectParts = append(redirectParts, formatRedirect(r))
			}
			redirects = (" " + strings.Join(redirectParts, " "))
		}
		return ((((((("case " + word) + " in") + patternStr) + "\n") + sp) + "esac") + redirects)
	}
	if node.Kind == "function" {
		name := node.Name
		innerBody := func() interface{} {
			if node.Body.Kind == "brace-group" {
				return node.Body.Body
			} else {
				return node.Body
			}
		}()
		body = formatCmdsubNode(innerBody, (indent + 4)).Rstrip(";")
		return fmt.Sprintf("function %v () \n{ \n%v%v\n}", name, innerSp, body)
	}
	if node.Kind == "subshell" {
		body = formatCmdsubNode(node.Body, indent, inProcsub, compactRedirects)
		redirects = ""
		if node.Redirects != nil {
			redirectParts = []interface{}{}
			for _, r := range node.Redirects {
				redirectParts = append(redirectParts, formatRedirect(r))
			}
			redirects = strings.Join(redirectParts, " ")
		}
		if procsubFirst {
			if redirects != "" {
				return ((("(" + body) + ") ") + redirects)
			}
			return (("(" + body) + ")")
		}
		if redirects != "" {
			return ((("( " + body) + " ) ") + redirects)
		}
		return (("( " + body) + " )")
	}
	if node.Kind == "brace-group" {
		body = formatCmdsubNode(node.Body, indent)
		body = body.Rstrip(";")
		terminator := func() string {
			if body.Endswith(" &") {
				return " }"
			} else {
				return "; }"
			}
		}()
		redirects = ""
		if node.Redirects != nil {
			redirectParts = []interface{}{}
			for _, r := range node.Redirects {
				redirectParts = append(redirectParts, formatRedirect(r))
			}
			redirects = strings.Join(redirectParts, " ")
		}
		if redirects != "" {
			return (((("{ " + body) + terminator) + " ") + redirects)
		}
		return (("{ " + body) + terminator)
	}
	if node.Kind == "arith-cmd" {
		return (("((" + node.RawContent) + "))")
	}
	if node.Kind == "cond-expr" {
		body = formatCondBody(node.Body)
		return (("[[ " + body) + " ]]")
	}
	if node.Kind == "negation" {
		if node.Pipeline != nil {
			return ("! " + formatCmdsubNode(node.Pipeline, indent))
		}
		return "! "
	}
	if node.Kind == "time" {
		prefix := func() string {
			if node.Posix {
				return "time -p "
			} else {
				return "time "
			}
		}()
		if node.Pipeline != nil {
			return (prefix + formatCmdsubNode(node.Pipeline, indent))
		}
		return prefix
	}
	return ""
}

func formatRedirect(r Node, compact bool, heredocOpOnly bool) string {
	var op string
	var delim interface{}
	if r.Kind == "heredoc" {
		if r.StripTabs != nil {
			op = "<<-"
		} else {
			op = "<<"
		}
		if r.Fd != nil && (r.Fd != 0) {
			op = (Str(r.Fd) + op)
		}
		if r.Quoted != nil {
			delim = (("'" + r.Delimiter) + "'")
		} else {
			delim = r.Delimiter
		}
		if heredocOpOnly {
			return (op + delim)
		}
		return (((((op + delim) + "\n") + r.Content) + r.Delimiter) + "\n")
	}
	op = r.Op
	if op == "1>" {
		op = ">"
	} else if op == "0<" {
		op = "<"
	}
	target := r.Target.Value
	target = r.Target.expandAllAnsiCQuotes(target)
	target = r.Target.stripLocaleStringDollars(target)
	target = r.Target.formatCommandSubstitutions(target)
	if target.Startswith("&") {
		wasInputClose := false
		if (target == "&-") && op.Endswith("<") {
			wasInputClose = true
			op = (substring(op, 0, (len(op)-1)) + ">")
		}
		afterAmp := substring(target, 1, len(target))
		isLiteralFd := ((afterAmp == "-") || ((len(afterAmp) > 0) && afterAmp[0].Isdigit()))
		if isLiteralFd != nil {
			if (op == ">") || (op == ">&") {
				op = func() string {
					if wasInputClose {
						return "0>"
					} else {
						return "1>"
					}
				}()
			} else if (op == "<") || (op == "<&") {
				op = "0<"
			}
		} else if op == "1>" {
			op = ">"
		} else if op == "0<" {
			op = "<"
		}
		return (op + target)
	}
	if op.Endswith("&") {
		return (op + target)
	}
	if compact {
		return (op + target)
	}
	return ((op + " ") + target)
}

func formatHeredocBody(r Node) string {
	return ((("\n" + r.Content) + r.Delimiter) + "\n")
}

func lookaheadForEsac(value string, start int, caseDepth int) bool {
	i := start
	depth := caseDepth
	quote := &QuoteState{}
	for i < len(value) {
		c := string(value[i])
		if ((c == "\\") && ((i + 1) < len(value))) && quote.Double != nil {
			i += 2
			continue
		}
		if (c == "'") && !quote.Double != nil {
			quote.Single = !quote.Single
			i += 1
			continue
		}
		if (c == "\"") && !quote.Single != nil {
			quote.Double = !quote.Double
			i += 1
			continue
		}
		if quote.Single != nil || quote.Double != nil {
			i += 1
			continue
		}
		if startsWithAt(value, i, "case") && isWordBoundary(value, i, 4) {
			depth += 1
			i += 4
		} else if startsWithAt(value, i, "esac") && isWordBoundary(value, i, 4) {
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

func skipBacktick(value string, start int) int {
	i := (start + 1)
	for (i < len(value)) && (string(value[i]) != "`") {
		if (string(value[i]) == "\\") && ((i + 1) < len(value)) {
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

func skipSingleQuoted(s string, start int) int {
	i := start
	for (i < len(s)) && (string(s[i]) != "'") {
		i += 1
	}
	return func() int {
		if i < len(s) {
			return (i + 1)
		} else {
			return i
		}
	}()
}

func skipDoubleQuoted(s string, start int) int {
	unknownLvalue := struct{ Single, Double bool }{start, len(s)}
	passNext := false
	for i < n {
		c := string(s[i])
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
				backq := false
			}
			i += 1
			continue
		}
		if c == "`" {
			backq = true
			i += 1
			continue
		}
		if (c == "$") && ((i + 1) < n) {
			if string(s[(i+1)]) == "(" {
				i := findCmdsubEnd(s, (i + 2))
				continue
			}
			if string(s[(i+1)]) == "{" {
				i = findBracedParamEnd(s, (i + 2))
				continue
			}
		}
		if c == "\"" {
			return (i + 1)
		}
		i += 1
	}
	return i
}

func isValidArithmeticStart(value string, start int) bool {
	scanParen := 0
	scanI := (start + 3)
	for scanI < len(value) {
		scanC := string(value[scanI])
		if isExpansionStart(value, scanI, "$(") {
			scanI = findCmdsubEnd(value, (scanI + 2))
			continue
		}
		if scanC == "(" {
			scanParen += 1
		} else if scanC == ")" {
			if scanParen > 0 {
				scanParen -= 1
			} else if ((scanI + 1) < len(value)) && (string(value[(scanI+1)]) == ")") {
				return true
			} else {
				return false
			}
		}
		scanI += 1
	}
	return false
}

func findFunsubEnd(value string, start int) int {
	depth := 1
	i := start
	quote := &QuoteState{}
	for (i < len(value)) && (depth > 0) {
		c := string(value[i])
		if ((c == "\\") && ((i + 1) < len(value))) && !quote.Single != nil {
			i += 2
			continue
		}
		if (c == "'") && !quote.Double != nil {
			quote.Single = !quote.Single
			i += 1
			continue
		}
		if (c == "\"") && !quote.Single != nil {
			quote.Double = !quote.Double
			i += 1
			continue
		}
		if quote.Single != nil || quote.Double != nil {
			i += 1
			continue
		}
		if c == "{" {
			depth += 1
		} else if c == "}" {
			depth -= 1
			if depth == 0 {
				return (i + 1)
			}
		}
		i += 1
	}
	return len(value)
}

func findCmdsubEnd(value string, start int) int {
	depth := 1
	i := start
	caseDepth := 0
	inCasePatterns := false
	arithDepth := 0
	arithParenDepth := 0
	for (i < len(value)) && (depth > 0) {
		c := string(value[i])
		if (c == "\\") && ((i + 1) < len(value)) {
			i += 2
			continue
		}
		if c == "'" {
			i = skipSingleQuoted(value, (i + 1))
			continue
		}
		if c == "\"" {
			i = skipDoubleQuoted(value, (i + 1))
			continue
		}
		if ((c == "#") && (arithDepth == 0)) && (((((((((i == start) || (string(value[(i-1)]) == " ")) || (string(value[(i-1)]) == "\t")) || (string(value[(i-1)]) == "\n")) || (string(value[(i-1)]) == ";")) || (string(value[(i-1)]) == "|")) || (string(value[(i-1)]) == "&")) || (string(value[(i-1)]) == "(")) || (string(value[(i-1)]) == ")")) {
			for (i < len(value)) && (string(value[i]) != "\n") {
				i += 1
			}
			continue
		}
		if startsWithAt(value, i, "<<<") {
			i += 3
			for (i < len(value)) && ((string(value[i]) == " ") || (string(value[i]) == "\t")) {
				i += 1
			}
			if (i < len(value)) && (string(value[i]) == "\"") {
				i += 1
				for (i < len(value)) && (string(value[i]) != "\"") {
					if (string(value[i]) == "\\") && ((i + 1) < len(value)) {
						i += 2
					} else {
						i += 1
					}
				}
				if i < len(value) {
					i += 1
				}
			} else if (i < len(value)) && (string(value[i]) == "'") {
				i += 1
				for (i < len(value)) && (string(value[i]) != "'") {
					i += 1
				}
				if i < len(value) {
					i += 1
				}
			} else {
				for (i < len(value)) && !strings.Contains(" \t\n;|&<>()", string(value[i])) {
					i += 1
				}
			}
			continue
		}
		if isExpansionStart(value, i, "$((") {
			if isValidArithmeticStart(value, i) {
				arithDepth += 1
				i += 3
				continue
			}
			j := findCmdsubEnd(value, (i + 2))
			i = j
			continue
		}
		if ((arithDepth > 0) && (arithParenDepth == 0)) && startsWithAt(value, i, "))") {
			arithDepth -= 1
			i += 2
			continue
		}
		if c == "`" {
			i = skipBacktick(value, i)
			continue
		}
		if (arithDepth == 0) && startsWithAt(value, i, "<<") {
			i = skipHeredoc(value, i)
			continue
		}
		if startsWithAt(value, i, "case") && isWordBoundary(value, i, 4) {
			caseDepth += 1
			inCasePatterns = false
			i += 4
			continue
		}
		if ((caseDepth > 0) && startsWithAt(value, i, "in")) && isWordBoundary(value, i, 2) {
			inCasePatterns = true
			i += 2
			continue
		}
		if startsWithAt(value, i, "esac") && isWordBoundary(value, i, 4) {
			if caseDepth > 0 {
				caseDepth -= 1
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
			if !(inCasePatterns && (caseDepth > 0)) {
				if arithDepth > 0 {
					arithParenDepth += 1
				} else {
					depth += 1
				}
			}
		} else if c == ")" {
			if inCasePatterns && (caseDepth > 0) {
				if !lookaheadForEsac(value, (i + 1), caseDepth) {
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

func findBracedParamEnd(value string, start int) int {
	var dolbraceState int
	depth := 1
	i := start
	inDouble := false
	dolbraceState = DolbracestateParam
	for (i < len(value)) && (depth > 0) {
		c := string(value[i])
		if (c == "\\") && ((i + 1) < len(value)) {
			i += 2
			continue
		}
		if ((c == "'") && (dolbraceState == DolbracestateQuote)) && !inDouble {
			i = skipSingleQuoted(value, (i + 1))
			continue
		}
		if c == "\"" {
			inDouble = !inDouble
			i += 1
			continue
		}
		if inDouble {
			i += 1
			continue
		}
		if (dolbraceState == DolbracestateParam) && strings.Contains("%#^,", c) {
			dolbraceState = DolbracestateQuote
		} else if (dolbraceState == DolbracestateParam) && strings.Contains(":-=?+/", c) {
			dolbraceState = DolbracestateWord
		}
		if ((c == "[") && (dolbraceState == DolbracestateParam)) && !inDouble {
			end := skipSubscript(value, i, 0)
			if end != -1 {
				i = end
				continue
			}
		}
		if (((c == "<") || (c == ">")) && ((i + 1) < len(value))) && (string(value[(i+1)]) == "(") {
			i = findCmdsubEnd(value, (i + 2))
			continue
		}
		if c == "{" {
			depth += 1
		} else if c == "}" {
			depth -= 1
			if depth == 0 {
				return (i + 1)
			}
		}
		if isExpansionStart(value, i, "$(") {
			i = findCmdsubEnd(value, (i + 2))
			continue
		}
		if isExpansionStart(value, i, "${") {
			i = findBracedParamEnd(value, (i + 2))
			continue
		}
		i += 1
	}
	return i
}

func skipHeredoc(value string, start int) int {
	var delimStart interface{}
	var delimiter interface{}
	var stripped interface{}
	var i int
	i = (start + 2)
	if (i < len(value)) && (string(value[i]) == "-") {
		i += 1
	}
	for (i < len(value)) && isWhitespaceNoNewline(string(value[i])) {
		i += 1
	}
	delimStart = i
	quoteChar := nil
	if (i < len(value)) && ((string(value[i]) == "\"") || (string(value[i]) == "'")) {
		quoteChar = string(value[i])
		i += 1
		delimStart = i
		for (i < len(value)) && (string(value[i]) != quoteChar) {
			i += 1
		}
		delimiter = substring(value, delimStart, i)
		if i < len(value) {
			i += 1
		}
	} else if (i < len(value)) && (string(value[i]) == "\\") {
		i += 1
		delimStart = i
		if i < len(value) {
			i += 1
		}
		for (i < len(value)) && !isMetachar(string(value[i])) {
			i += 1
		}
		delimiter = substring(value, delimStart, i)
	} else {
		for (i < len(value)) && !isMetachar(string(value[i])) {
			i += 1
		}
		delimiter = substring(value, delimStart, i)
	}
	parenDepth := 0
	quote := &QuoteState{}
	inBacktick := false
	for (i < len(value)) && (string(value[i]) != "\n") {
		c := string(value[i])
		if ((c == "\\") && ((i + 1) < len(value))) && (quote.Double != nil || inBacktick) {
			i += 2
			continue
		}
		if ((c == "'") && !quote.Double != nil) && !inBacktick {
			quote.Single = !quote.Single
			i += 1
			continue
		}
		if ((c == "\"") && !quote.Single != nil) && !inBacktick {
			quote.Double = !quote.Double
			i += 1
			continue
		}
		if (c == "`") && !quote.Single != nil {
			inBacktick = !inBacktick
			i += 1
			continue
		}
		if (quote.Single != nil || quote.Double != nil) || inBacktick {
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
	if (i < len(value)) && (string(value[i]) == ")") {
		return i
	}
	if (i < len(value)) && (string(value[i]) == "\n") {
		i += 1
	}
	for i < len(value) {
		lineStart := i
		lineEnd := i
		for (lineEnd < len(value)) && (string(value[lineEnd]) != "\n") {
			lineEnd += 1
		}
		line := substring(value, lineStart, lineEnd)
		for lineEnd < len(value) {
			trailingBs := 0
			for _, j := range Range((len(line) - 1), -1, -1) {
				if line[j] == "\\" {
					trailingBs += 1
				} else {
					break
				}
			}
			if (trailingBs % 2) == 0 {
				break
			}
			line = line[:-1]
			lineEnd += 1
			nextLineStart := lineEnd
			for (lineEnd < len(value)) && (string(value[lineEnd]) != "\n") {
				lineEnd += 1
			}
			line = (line + substring(value, nextLineStart, lineEnd))
		}
		if ((start + 2) < len(value)) && (string(value[(start+2)]) == "-") {
			stripped = line.Lstrip("\t")
		} else {
			stripped = line
		}
		if stripped == delimiter {
			if lineEnd < len(value) {
				return (lineEnd + 1)
			} else {
				return lineEnd
			}
		}
		if stripped.Startswith(delimiter) && (len(stripped) > len(delimiter)) {
			tabsStripped := (len(line) - len(stripped))
			return ((lineStart + tabsStripped) + len(delimiter))
		}
		if lineEnd < len(value) {
			i = (lineEnd + 1)
		} else {
			i = lineEnd
		}
	}
	return i
}

func findHeredocContentEnd(source string, start int, delimiters []interface{}) (int, int) {
	var lineStripped interface{}
	if !delimiters {
		return start, start
	}
	pos := start
	for (pos < len(source)) && (string(source[pos]) != "\n") {
		pos += 1
	}
	if pos >= len(source) {
		return start, start
	}
	contentStart := pos
	pos += 1
	for delimiter, stripTabs := range delimiters {
		for pos < len(source) {
			lineStart := pos
			lineEnd := pos
			for (lineEnd < len(source)) && (string(source[lineEnd]) != "\n") {
				lineEnd += 1
			}
			line := substring(source, lineStart, lineEnd)
			for lineEnd < len(source) {
				trailingBs := 0
				for _, j := range Range((len(line) - 1), -1, -1) {
					if line[j] == "\\" {
						trailingBs += 1
					} else {
						break
					}
				}
				if (trailingBs % 2) == 0 {
					break
				}
				line = line[:-1]
				lineEnd += 1
				nextLineStart := lineEnd
				for (lineEnd < len(source)) && (string(source[lineEnd]) != "\n") {
					lineEnd += 1
				}
				line = (line + substring(source, nextLineStart, lineEnd))
			}
			if stripTabs != nil {
				lineStripped = line.Lstrip("\t")
			} else {
				lineStripped = line
			}
			if lineStripped == delimiter {
				pos = func() int {
					if lineEnd < len(source) {
						return (lineEnd + 1)
					} else {
						return lineEnd
					}
				}()
				break
			}
			if lineStripped.Startswith(delimiter) && (len(lineStripped) > len(delimiter)) {
				tabsStripped := (len(line) - len(lineStripped))
				pos = ((lineStart + tabsStripped) + len(delimiter))
				break
			}
			pos = func() int {
				if lineEnd < len(source) {
					return (lineEnd + 1)
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
		prev := string(s[(pos - 1)])
		if prev.Isalnum() || (prev == "_") {
			return false
		}
		if strings.Contains("{}!", prev) {
			return false
		}
	}
	end := (pos + wordLen)
	if (end < len(s)) && (string(s[end]).Isalnum() || (string(s[end]) == "_")) {
		return false
	}
	return true
}

func isQuote(c string) bool {
	return ((c == "'") || (c == "\""))
}

func collapseWhitespace(s string) string {
	var prevWasWs bool
	result := []interface{}{}
	prevWasWs = false
	for _, c := range s {
		if (c == " ") || (c == "\t") {
			if !prevWasWs {
				result = append(result, " ")
			}
			prevWasWs = true
		} else {
			result = append(result, c)
			prevWasWs = false
		}
	}
	joined := strings.Join(result, "")
	return joined.Strip(" \t")
}

func countTrailingBackslashes(s string) int {
	count := 0
	for _, i := range Range((len(s) - 1), -1, -1) {
		if string(s[i]) == "\\" {
			count += 1
		} else {
			break
		}
	}
	return count
}

func normalizeHeredocDelimiter(delimiter string) string {
	var depth int
	var inner []interface{}
	var innerStr interface{}
	result := []interface{}{}
	i := 0
	for i < len(delimiter) {
		if ((i + 1) < len(delimiter)) && (delimiter[i:(i+2)] == "$(") {
			result = append(result, "$(")
			i += 2
			depth = 1
			inner = []interface{}{}
			for (i < len(delimiter)) && (depth > 0) {
				if string(delimiter[i]) == "(" {
					depth += 1
					inner = append(inner, string(delimiter[i]))
				} else if string(delimiter[i]) == ")" {
					depth -= 1
					if depth == 0 {
						innerStr = strings.Join(inner, "")
						innerStr = collapseWhitespace(innerStr)
						result = append(result, innerStr)
						result = append(result, ")")
					} else {
						inner = append(inner, string(delimiter[i]))
					}
				} else {
					inner = append(inner, string(delimiter[i]))
				}
				i += 1
			}
		} else if ((i + 1) < len(delimiter)) && (delimiter[i:(i+2)] == "${") {
			result = append(result, "${")
			i += 2
			depth = 1
			inner = []interface{}{}
			for (i < len(delimiter)) && (depth > 0) {
				if string(delimiter[i]) == "{" {
					depth += 1
					inner = append(inner, string(delimiter[i]))
				} else if string(delimiter[i]) == "}" {
					depth -= 1
					if depth == 0 {
						innerStr = strings.Join(inner, "")
						innerStr = collapseWhitespace(innerStr)
						result = append(result, innerStr)
						result = append(result, "}")
					} else {
						inner = append(inner, string(delimiter[i]))
					}
				} else {
					inner = append(inner, string(delimiter[i]))
				}
				i += 1
			}
		} else if (((i + 1) < len(delimiter)) && strings.Contains("<>", string(delimiter[i]))) && (string(delimiter[(i+1)]) == "(") {
			result = append(result, string(delimiter[i]))
			result = append(result, "(")
			i += 2
			depth = 1
			inner = []interface{}{}
			for (i < len(delimiter)) && (depth > 0) {
				if string(delimiter[i]) == "(" {
					depth += 1
					inner = append(inner, string(delimiter[i]))
				} else if string(delimiter[i]) == ")" {
					depth -= 1
					if depth == 0 {
						innerStr = strings.Join(inner, "")
						innerStr = collapseWhitespace(innerStr)
						result = append(result, innerStr)
						result = append(result, ")")
					} else {
						inner = append(inner, string(delimiter[i]))
					}
				} else {
					inner = append(inner, string(delimiter[i]))
				}
				i += 1
			}
		} else {
			result = append(result, string(delimiter[i]))
			i += 1
		}
	}
	return strings.Join(result, "")
}

func isMetachar(c string) bool {
	return ((((((((((c == " ") || (c == "\t")) || (c == "\n")) || (c == "|")) || (c == "&")) || (c == ";")) || (c == "(")) || (c == ")")) || (c == "<")) || (c == ">"))
}

func isFunsubChar(c string) bool {
	return ((((c == " ") || (c == "\t")) || (c == "\n")) || (c == "|"))
}

func isExtglobPrefix(c string) bool {
	return (((((c == "@") || (c == "?")) || (c == "*")) || (c == "+")) || (c == "!"))
}

func isRedirectChar(c string) bool {
	return ((c == "<") || (c == ">"))
}

func isSpecialParam(c string) bool {
	return ((((((((c == "?") || (c == "$")) || (c == "!")) || (c == "#")) || (c == "@")) || (c == "*")) || (c == "-")) || (c == "&"))
}

func isSpecialParamUnbraced(c string) bool {
	return (((((((c == "?") || (c == "$")) || (c == "!")) || (c == "#")) || (c == "@")) || (c == "*")) || (c == "-"))
}

func isDigit(c string) bool {
	return ((c >= "0") && (c <= "9"))
}

func isSemicolonOrNewline(c string) bool {
	return ((c == ";") || (c == "\n"))
}

func isWordEndContext(c string) bool {
	return ((((((((((c == " ") || (c == "\t")) || (c == "\n")) || (c == ";")) || (c == "|")) || (c == "&")) || (c == "<")) || (c == ">")) || (c == "(")) || (c == ")"))
}

func skipMatchedPair(s string, start int, open string, close string, flags int) int {
	var i interface{}
	n := len(s)
	if (flags & SmpPastOpen) != 0 {
		i = start
	} else {
		if (start >= n) || (string(s[start]) != open) {
			return -1
		}
		i = (start + 1)
	}
	depth := 1
	passNext := false
	backq := false
	for (i < n) && (depth > 0) {
		c := string(s[i])
		if passNext {
			passNext = false
			i += 1
			continue
		}
		literal := (flags & SmpLiteral)
		if !literal != nil && (c == "\\") {
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
		if !literal != nil && (c == "`") {
			backq = true
			i += 1
			continue
		}
		if !literal != nil && (c == "'") {
			i = skipSingleQuoted(s, (i + 1))
			continue
		}
		if !literal != nil && (c == "\"") {
			i = skipDoubleQuoted(s, (i + 1))
			continue
		}
		if !literal != nil && isExpansionStart(s, i, "$(") {
			i = findCmdsubEnd(s, (i + 2))
			continue
		}
		if !literal != nil && isExpansionStart(s, i, "${") {
			i = findBracedParamEnd(s, (i + 2))
			continue
		}
		if !literal != nil && (c == open) {
			depth += 1
		} else if c == close {
			depth -= 1
		}
		i += 1
	}
	return func() interface{} {
		if depth == 0 {
			return i
		} else {
			return -1
		}
	}()
}

func skipSubscript(s string, start int, flags int) int {
	return skipMatchedPair(s, start, "[", "]", flags)
}

func assignment(s string, flags int) int {
	if !(s != "") {
		return -1
	}
	if !(string(s[0]).Isalpha() || (string(s[0]) == "_")) {
		return -1
	}
	i := 1
	for i < len(s) {
		c := string(s[i])
		if c == "=" {
			return i
		}
		if c == "[" {
			subFlags := func() int {
				if flags & 2 {
					return SmpLiteral
				} else {
					return 0
				}
			}()
			end := skipSubscript(s, i, subFlags)
			if end == -1 {
				return -1
			}
			i = end
			if (i < len(s)) && (string(s[i]) == "+") {
				i += 1
			}
			if (i < len(s)) && (string(s[i]) == "=") {
				return i
			}
			return -1
		}
		if c == "+" {
			if ((i + 1) < len(s)) && (string(s[(i+1)]) == "=") {
				return (i + 1)
			}
			return -1
		}
		if !(c.Isalnum() || (c == "_")) {
			return -1
		}
		i += 1
	}
	return -1
}

func isArrayAssignmentPrefix(chars []string) bool {
	if !chars {
		return false
	}
	if !(chars[0].Isalpha() || (chars[0] == "_")) {
		return false
	}
	s := strings.Join(chars, "")
	i := 1
	for (i < len(s)) && (s[i].Isalnum() || (s[i] == "_")) {
		i += 1
	}
	for i < len(s) {
		if s[i] != "[" {
			return false
		}
		end := skipSubscript(s, i, SmpLiteral)
		if end == -1 {
			return false
		}
		i = end
	}
	return true
}

func isSpecialParamOrDigit(c string) bool {
	return (isSpecialParam(c) || isDigit(c))
}

func isParamExpansionOp(c string) bool {
	return (((((((((((((c == ":") || (c == "-")) || (c == "=")) || (c == "+")) || (c == "?")) || (c == "#")) || (c == "%")) || (c == "/")) || (c == "^")) || (c == ",")) || (c == "@")) || (c == "*")) || (c == "["))
}

func isSimpleParamOp(c string) bool {
	return ((((c == "-") || (c == "=")) || (c == "?")) || (c == "+"))
}

func isEscapeCharInBacktick(c string) bool {
	return (((c == "$") || (c == "`")) || (c == "\\"))
}

func isNegationBoundary(c string) bool {
	return ((((((isWhitespace(c) || (c == ";")) || (c == "|")) || (c == ")")) || (c == "&")) || (c == ">")) || (c == "<"))
}

func isBackslashEscaped(value string, idx int) bool {
	bsCount := 0
	j := (idx - 1)
	for (j >= 0) && (string(value[j]) == "\\") {
		bsCount += 1
		j -= 1
	}
	return ((bsCount % 2) == 1)
}

func isDollarDollarParen(value string, idx int) bool {
	dollarCount := 0
	j := (idx - 1)
	for (j >= 0) && (string(value[j]) == "$") {
		dollarCount += 1
		j -= 1
	}
	return ((dollarCount % 2) == 1)
}

func isParen(c string) bool {
	return ((c == "(") || (c == ")"))
}

func isCaretOrBang(c string) bool {
	return ((c == "!") || (c == "^"))
}

func isAtOrStar(c string) bool {
	return ((c == "@") || (c == "*"))
}

func isDigitOrDash(c string) bool {
	return (isDigit(c) || (c == "-"))
}

func isNewlineOrRightParen(c string) bool {
	return ((c == "\n") || (c == ")"))
}

func isSemicolonNewlineBrace(c string) bool {
	return (((c == ";") || (c == "\n")) || (c == "{"))
}

func looksLikeAssignment(s string) bool {
	return (assignment(s) != -1)
}

func isValidIdentifier(name string) bool {
	if !(name != "") {
		return false
	}
	if !(string(name[0]).Isalpha() || (string(name[0]) == "_")) {
		return false
	}
	for _, c := range name[1:] {
		if !(c.Isalnum() || (c == "_")) {
			return false
		}
	}
	return true
}

func Parse(source string, extglob bool) []Node {
	parser := &Parser{Source: source, InProcessSub: false, Extglob: extglob}
	return parser.Parse()
}
