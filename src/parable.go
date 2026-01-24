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

// MatchedPairError is raised when a matched pair is unclosed at EOF.
type MatchedPairError struct {
	ParseError
}

// Node is the base interface for all AST nodes.
type Node interface {
	Kind() string
	ToSexp() string
}

type TokenType struct {
}

type Token struct {
	Type  int
	Value string
	Pos   int
	Parts interface{}
	Word  Node
}

type ParserStateFlags struct {
}

type DolbraceState struct {
}

type MatchedPairFlags struct {
}

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
}

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
}

type Lexer struct {
	RESERVED_WORDS     map[string]int
	Source             string
	Pos                int
	Length             interface{}
	Quote              *QuoteState
	_Parser_state      interface{}
	_Dolbrace_state    interface{}
	_Extglob           bool
	_Word_context      interface{}
	_At_command_start  bool
	_In_array_literal  bool
	_In_assign_builtin bool
}

type Word struct {
	Value string
	Parts []Node
	Kind  string
}

type Command struct {
	Words     []Node
	Redirects []Node
	Kind      string
}

type Pipeline struct {
	Commands []Node
	Kind     string
}

type List struct {
	Parts []Node
	Kind  string
}

type Operator struct {
	Op   string
	Kind string
}

type PipeBoth struct {
	Kind string
}

type Empty struct {
	Kind string
}

type Comment struct {
	Text string
	Kind string
}

type Redirect struct {
	Op     string
	Target Node
	Fd     int
	Kind   string
}

type HereDoc struct {
	Delimiter  string
	Content    string
	Strip_tabs bool
	Quoted     bool
	Fd         int
	Complete   bool
	_Start_pos int
	Kind       string
}

type Subshell struct {
	Body      Node
	Redirects []interface{}
	Kind      string
}

type BraceGroup struct {
	Body      Node
	Redirects []interface{}
	Kind      string
}

type If struct {
	Condition Node
	Then_body Node
	Else_body Node
	Redirects []Node
	Kind      string
}

type While struct {
	Condition Node
	Body      Node
	Redirects []Node
	Kind      string
}

type Until struct {
	Condition Node
	Body      Node
	Redirects []Node
	Kind      string
}

type For struct {
	Var       string
	Words     []interface{}
	Body      Node
	Redirects []Node
	Kind      string
}

type ForArith struct {
	Init      string
	Cond      string
	Incr      string
	Body      Node
	Redirects []Node
	Kind      string
}

type Select struct {
	Var       string
	Words     []interface{}
	Body      Node
	Redirects []Node
	Kind      string
}

type Case struct {
	Word      Node
	Patterns  []Node
	Redirects []Node
	Kind      string
}

type CasePattern struct {
	Pattern    string
	Body       Node
	Terminator string
	Kind       string
}

type Function struct {
	Name string
	Body Node
	Kind string
}

type ParamExpansion struct {
	Param string
	Op    string
	Arg   string
	Kind  string
}

type ParamLength struct {
	Param string
	Kind  string
}

type ParamIndirect struct {
	Param string
	Op    string
	Arg   string
	Kind  string
}

type CommandSubstitution struct {
	Command Node
	Brace   bool
	Kind    string
}

type ArithmeticExpansion struct {
	Expression Node
	Kind       string
}

type ArithmeticCommand struct {
	Expression  Node
	Redirects   []interface{}
	Raw_content string
	Kind        string
}

type ArithNumber struct {
	Value string
	Kind  string
}

type ArithEmpty struct {
	Kind string
}

type ArithVar struct {
	Name string
	Kind string
}

type ArithBinaryOp struct {
	Op    string
	Left  Node
	Right Node
	Kind  string
}

type ArithUnaryOp struct {
	Op      string
	Operand Node
	Kind    string
}

type ArithPreIncr struct {
	Operand Node
	Kind    string
}

type ArithPostIncr struct {
	Operand Node
	Kind    string
}

type ArithPreDecr struct {
	Operand Node
	Kind    string
}

type ArithPostDecr struct {
	Operand Node
	Kind    string
}

type ArithAssign struct {
	Op     string
	Target Node
	Value  Node
	Kind   string
}

type ArithTernary struct {
	Condition Node
	If_true   Node
	If_false  Node
	Kind      string
}

type ArithComma struct {
	Left  Node
	Right Node
	Kind  string
}

type ArithSubscript struct {
	Array string
	Index Node
	Kind  string
}

type ArithEscape struct {
	Char string
	Kind string
}

type ArithDeprecated struct {
	Expression string
	Kind       string
}

type ArithConcat struct {
	Parts []Node
	Kind  string
}

type AnsiCQuote struct {
	Content string
	Kind    string
}

type LocaleString struct {
	Content string
	Kind    string
}

type ProcessSubstitution struct {
	Direction string
	Command   Node
	Kind      string
}

type Negation struct {
	Pipeline Node
	Kind     string
}

type Time struct {
	Pipeline Node
	Posix    bool
	Kind     string
}

type ConditionalExpr struct {
	Body      interface{}
	Redirects []interface{}
	Kind      string
}

type UnaryTest struct {
	Op      string
	Operand Node
	Kind    string
}

type BinaryTest struct {
	Op    string
	Left  Node
	Right Node
	Kind  string
}

type CondAnd struct {
	Left  Node
	Right Node
	Kind  string
}

type CondOr struct {
	Left  Node
	Right Node
	Kind  string
}

type CondNot struct {
	Operand Node
	Kind    string
}

type CondParen struct {
	Inner Node
	Kind  string
}

type Array struct {
	Elements []Node
	Kind     string
}

type Coproc struct {
	Command Node
	Name    string
	Kind    string
}

type Parser struct {
	Source                       string
	Pos                          int
	Length                       interface{}
	_Saw_newline_in_single_quote bool
	_In_process_sub              bool
	_Extglob                     bool
	_Ctx                         *ContextStack
	_Lexer                       *Lexer
	_Parser_state                interface{}
	_Dolbrace_state              interface{}
	_Word_context                interface{}
	_At_command_start            bool
	_In_array_literal            bool
	_In_assign_builtin           bool
}

func _IsHexDigit(c string) bool {
	panic("TODO")
}

func _IsOctalDigit(c string) bool {
	panic("TODO")
}

func _GetAnsiEscape(c string) int {
	panic("TODO")
}

func _IsWhitespace(c string) bool {
	panic("TODO")
}

func _IsWhitespaceNoNewline(c string) bool {
	panic("TODO")
}

func _Substring(s string, start int, end int) string {
	panic("TODO")
}

func _StartsWithAt(s string, pos int, prefix string) bool {
	panic("TODO")
}

func _CountConsecutiveDollarsBefore(s string, pos int) int {
	panic("TODO")
}

func _IsExpansionStart(s string, pos int, delimiter string) bool {
	panic("TODO")
}

func _Sublist(lst []interface{}, start int, end int) []interface{} {
	panic("TODO")
}

func _RepeatStr(s string, n int) string {
	panic("TODO")
}

func _StripLineContinuationsCommentAware(text string) string {
	panic("TODO")
}

func _AppendRedirects(base string, redirects []interface{}) string {
	panic("TODO")
}

func _ConsumeSingleQuote(s string, start int) interface{} {
	panic("TODO")
}

func _ConsumeDoubleQuote(s string, start int) interface{} {
	panic("TODO")
}

func _HasBracketClose(s string, start int, depth int) bool {
	panic("TODO")
}

func _ConsumeBracketClass(s string, start int, depth int) interface{} {
	panic("TODO")
}

func _FormatCondBody(node Node) string {
	panic("TODO")
}

func _StartsWithSubshell(node Node) bool {
	panic("TODO")
}

func _FormatCmdsubNode(node Node, indent int, inProcsub bool, compactRedirects bool, procsubFirst bool) string {
	panic("TODO")
}

func _FormatRedirect(r interface{}, compact bool, heredocOpOnly bool) string {
	panic("TODO")
}

func _FormatHeredocBody(r Node) string {
	panic("TODO")
}

func _LookaheadForEsac(value string, start int, caseDepth int) bool {
	panic("TODO")
}

func _SkipBacktick(value string, start int) int {
	panic("TODO")
}

func _SkipSingleQuoted(s string, start int) int {
	panic("TODO")
}

func _SkipDoubleQuoted(s string, start int) int {
	panic("TODO")
}

func _IsValidArithmeticStart(value string, start int) bool {
	panic("TODO")
}

func _FindFunsubEnd(value string, start int) int {
	panic("TODO")
}

func _FindCmdsubEnd(value string, start int) int {
	panic("TODO")
}

func _FindBracedParamEnd(value string, start int) int {
	panic("TODO")
}

func _SkipHeredoc(value string, start int) int {
	panic("TODO")
}

func _FindHeredocContentEnd(source string, start int, delimiters []interface{}) interface{} {
	panic("TODO")
}

func _IsWordBoundary(s string, pos int, wordLen int) bool {
	panic("TODO")
}

func _IsQuote(c string) bool {
	panic("TODO")
}

func _CollapseWhitespace(s string) string {
	panic("TODO")
}

func _CountTrailingBackslashes(s string) int {
	panic("TODO")
}

func _NormalizeHeredocDelimiter(delimiter string) string {
	panic("TODO")
}

func _IsMetachar(c string) bool {
	panic("TODO")
}

func _IsFunsubChar(c string) bool {
	panic("TODO")
}

func _IsExtglobPrefix(c string) bool {
	panic("TODO")
}

func _IsRedirectChar(c string) bool {
	panic("TODO")
}

func _IsSpecialParam(c string) bool {
	panic("TODO")
}

func _IsSpecialParamUnbraced(c string) bool {
	panic("TODO")
}

func _IsDigit(c string) bool {
	panic("TODO")
}

func _IsSemicolonOrNewline(c string) bool {
	panic("TODO")
}

func _IsWordEndContext(c string) bool {
	panic("TODO")
}

func _SkipMatchedPair(s string, start int, open string, close string, flags int) int {
	panic("TODO")
}

func _SkipSubscript(s string, start int, flags int) int {
	panic("TODO")
}

func _Assignment(s string, flags int) int {
	panic("TODO")
}

func _IsArrayAssignmentPrefix(chars []string) bool {
	panic("TODO")
}

func _IsSpecialParamOrDigit(c string) bool {
	panic("TODO")
}

func _IsParamExpansionOp(c string) bool {
	panic("TODO")
}

func _IsSimpleParamOp(c string) bool {
	panic("TODO")
}

func _IsEscapeCharInBacktick(c string) bool {
	panic("TODO")
}

func _IsNegationBoundary(c string) bool {
	panic("TODO")
}

func _IsBackslashEscaped(value string, idx int) bool {
	panic("TODO")
}

func _IsDollarDollarParen(value string, idx int) bool {
	panic("TODO")
}

func _IsParen(c string) bool {
	panic("TODO")
}

func _IsCaretOrBang(c string) bool {
	panic("TODO")
}

func _IsAtOrStar(c string) bool {
	panic("TODO")
}

func _IsDigitOrDash(c string) bool {
	panic("TODO")
}

func _IsNewlineOrRightParen(c string) bool {
	panic("TODO")
}

func _IsSemicolonNewlineBrace(c string) bool {
	panic("TODO")
}

func _LooksLikeAssignment(s string) bool {
	panic("TODO")
}

func _IsValidIdentifier(name string) bool {
	panic("TODO")
}

func Parse(source string, extglob bool) []Node {
	panic("TODO")
}

func NewToken(typ int, value string, pos int, parts []interface{}, word Node) *Token {
	panic("TODO")
}

func NewSavedParserState(parserState int, dolbraceState int, pendingHeredocs []interface{}, ctxStack []interface{}, eofToken string) *SavedParserState {
	panic("TODO")
}

func NewQuoteState() *QuoteState {
	panic("TODO")
}

func (q *QuoteState) Push() {
	panic("TODO")
}

func (q *QuoteState) Pop() {
	panic("TODO")
}

func (q *QuoteState) InQuotes() bool {
	panic("TODO")
}

func (q *QuoteState) Copy() *QuoteState {
	panic("TODO")
}

func (q *QuoteState) OuterDouble() bool {
	panic("TODO")
}

func NewParseContext(kind int) *ParseContext {
	panic("TODO")
}

func (p *ParseContext) Copy() *ParseContext {
	panic("TODO")
}

func NewContextStack() *ContextStack {
	panic("TODO")
}

func (c *ContextStack) GetCurrent() *ParseContext {
	panic("TODO")
}

func (c *ContextStack) Push(kind int) {
	panic("TODO")
}

func (c *ContextStack) Pop() *ParseContext {
	panic("TODO")
}

func (c *ContextStack) CopyStack() []interface{} {
	panic("TODO")
}

func (c *ContextStack) RestoreFrom(savedStack []interface{}) {
	panic("TODO")
}

func NewLexer(source string, extglob bool) *Lexer {
	panic("TODO")
}

func (l *Lexer) Peek() string {
	panic("TODO")
}

func (l *Lexer) Advance() string {
	panic("TODO")
}

func (l *Lexer) AtEnd() bool {
	panic("TODO")
}

func (l *Lexer) Lookahead(n int) string {
	panic("TODO")
}

func (l *Lexer) IsMetachar(c string) bool {
	panic("TODO")
}

func (l *Lexer) _ReadOperator() *Token {
	panic("TODO")
}

func (l *Lexer) SkipBlanks() {
	panic("TODO")
}

func (l *Lexer) _SkipComment() bool {
	panic("TODO")
}

func (l *Lexer) _ReadSingleQuote(start int) interface{} {
	panic("TODO")
}

func (l *Lexer) _IsWordTerminator(ctx int, ch string, bracketDepth int, parenDepth int) bool {
	panic("TODO")
}

func (l *Lexer) _ReadBracketExpression(chars []interface{}, parts []interface{}, forRegex bool, parenDepth int) bool {
	panic("TODO")
}

func (l *Lexer) _ParseMatchedPair(openChar string, closeChar string, flags int) string {
	panic("TODO")
}

func (l *Lexer) _CollectParamArgument(flags int) string {
	panic("TODO")
}

func (l *Lexer) _ReadWordInternal(ctx int, atCommandStart bool, inArrayLiteral bool, inAssignBuiltin bool) Node {
	panic("TODO")
}

func (l *Lexer) _ReadWord() *Token {
	panic("TODO")
}

func (l *Lexer) NextToken() *Token {
	panic("TODO")
}

func (l *Lexer) PeekToken() *Token {
	panic("TODO")
}

func (l *Lexer) _ReadAnsiCQuote() interface{} {
	panic("TODO")
}

func (l *Lexer) _SyncToParser() {
	panic("TODO")
}

func (l *Lexer) _SyncFromParser() {
	panic("TODO")
}

func (l *Lexer) _ReadLocaleString() interface{} {
	panic("TODO")
}

func (l *Lexer) _UpdateDolbraceForOp(op string, hasParam bool) {
	panic("TODO")
}

func (l *Lexer) _ConsumeParamOperator() string {
	panic("TODO")
}

func (l *Lexer) _ParamSubscriptHasClose(startPos int) bool {
	panic("TODO")
}

func (l *Lexer) _ConsumeParamName() string {
	panic("TODO")
}

func (l *Lexer) _ReadParamExpansion(inDquote bool) interface{} {
	panic("TODO")
}

func (l *Lexer) _ReadBracedParam(start int, inDquote bool) interface{} {
	panic("TODO")
}

func (l *Lexer) _ReadFunsub(start int) interface{} {
	panic("TODO")
}

func NewWord(value string, parts []Node) *Word {
	panic("TODO")
}

func (w *Word) ToSexp() string {
	panic("TODO")
}

func (w *Word) _AppendWithCtlesc(result []byte, byteVal int) {
	panic("TODO")
}

func (w *Word) _DoubleCtlescSmart(value string) string {
	panic("TODO")
}

func (w *Word) _NormalizeParamExpansionNewlines(value string) string {
	panic("TODO")
}

func (w *Word) _ExpandAnsiCEscapes(value string) string {
	panic("TODO")
}

func (w *Word) _ExpandAllAnsiCQuotes(value string) string {
	panic("TODO")
}

func (w *Word) _StripLocaleStringDollars(value string) string {
	panic("TODO")
}

func (w *Word) _NormalizeArrayWhitespace(value string) string {
	panic("TODO")
}

func (w *Word) _FindMatchingParen(value string, openPos int) int {
	panic("TODO")
}

func (w *Word) _NormalizeArrayInner(inner string) string {
	panic("TODO")
}

func (w *Word) _StripArithLineContinuations(value string) string {
	panic("TODO")
}

func (w *Word) _CollectCmdsubs(node interface{}) []interface{} {
	panic("TODO")
}

func (w *Word) _CollectProcsubs(node interface{}) []interface{} {
	panic("TODO")
}

func (w *Word) _FormatCommandSubstitutions(value string, inArith bool) string {
	panic("TODO")
}

func (w *Word) _NormalizeExtglobWhitespace(value string) string {
	panic("TODO")
}

func (w *Word) GetCondFormattedValue() string {
	panic("TODO")
}

func NewCommand(words []Node, redirects []Node) *Command {
	panic("TODO")
}

func (c *Command) ToSexp() string {
	panic("TODO")
}

func NewPipeline(commands []Node) *Pipeline {
	panic("TODO")
}

func (p *Pipeline) ToSexp() string {
	panic("TODO")
}

func (p *Pipeline) _CmdSexp(cmd Node, needsRedirect bool) string {
	panic("TODO")
}

func NewList(parts []Node) *List {
	panic("TODO")
}

func (l *List) ToSexp() string {
	panic("TODO")
}

func (l *List) _ToSexpWithPrecedence(parts []interface{}, opNames map[string]interface{}) string {
	panic("TODO")
}

func (l *List) _ToSexpAmpAndHigher(parts []interface{}, opNames map[string]interface{}) string {
	panic("TODO")
}

func (l *List) _ToSexpAndOr(parts []interface{}, opNames map[string]interface{}) string {
	panic("TODO")
}

func NewOperator(op string) *Operator {
	panic("TODO")
}

func (o *Operator) ToSexp() string {
	panic("TODO")
}

func NewPipeBoth() *PipeBoth {
	panic("TODO")
}

func (p *PipeBoth) ToSexp() string {
	panic("TODO")
}

func NewEmpty() *Empty {
	panic("TODO")
}

func (e *Empty) ToSexp() string {
	panic("TODO")
}

func NewComment(text string) *Comment {
	panic("TODO")
}

func (c *Comment) ToSexp() string {
	panic("TODO")
}

func NewRedirect(op string, target Node, fd int) *Redirect {
	panic("TODO")
}

func (r *Redirect) ToSexp() string {
	panic("TODO")
}

func NewHereDoc(delimiter string, content string, stripTabs bool, quoted bool, fd int, complete bool) *HereDoc {
	panic("TODO")
}

func (h *HereDoc) ToSexp() string {
	panic("TODO")
}

func NewSubshell(body Node, redirects []interface{}) *Subshell {
	panic("TODO")
}

func (s *Subshell) ToSexp() string {
	panic("TODO")
}

func NewBraceGroup(body Node, redirects []interface{}) *BraceGroup {
	panic("TODO")
}

func (b *BraceGroup) ToSexp() string {
	panic("TODO")
}

func NewIf(condition Node, thenBody Node, elseBody Node, redirects []Node) *If {
	panic("TODO")
}

func (i *If) ToSexp() string {
	panic("TODO")
}

func NewWhile(condition Node, body Node, redirects []Node) *While {
	panic("TODO")
}

func (w *While) ToSexp() string {
	panic("TODO")
}

func NewUntil(condition Node, body Node, redirects []Node) *Until {
	panic("TODO")
}

func (u *Until) ToSexp() string {
	panic("TODO")
}

func NewFor(variable string, words []interface{}, body Node, redirects []Node) *For {
	panic("TODO")
}

func (f *For) ToSexp() string {
	panic("TODO")
}

func NewForArith(init string, cond string, incr string, body Node, redirects []Node) *ForArith {
	panic("TODO")
}

func (f *ForArith) ToSexp() string {
	panic("TODO")
}

func NewSelect(variable string, words []interface{}, body Node, redirects []Node) *Select {
	panic("TODO")
}

func (s *Select) ToSexp() string {
	panic("TODO")
}

func NewCase(word Node, patterns []Node, redirects []Node) *Case {
	panic("TODO")
}

func (c *Case) ToSexp() string {
	panic("TODO")
}

func NewCasePattern(pattern string, body Node, terminator string) *CasePattern {
	panic("TODO")
}

func (c *CasePattern) ToSexp() string {
	panic("TODO")
}

func NewFunction(name string, body Node) *Function {
	panic("TODO")
}

func (f *Function) ToSexp() string {
	panic("TODO")
}

func NewParamExpansion(param string, op string, arg string) *ParamExpansion {
	panic("TODO")
}

func (p *ParamExpansion) ToSexp() string {
	panic("TODO")
}

func NewParamLength(param string) *ParamLength {
	panic("TODO")
}

func (p *ParamLength) ToSexp() string {
	panic("TODO")
}

func NewParamIndirect(param string, op string, arg string) *ParamIndirect {
	panic("TODO")
}

func (p *ParamIndirect) ToSexp() string {
	panic("TODO")
}

func NewCommandSubstitution(command Node, brace bool) *CommandSubstitution {
	panic("TODO")
}

func (c *CommandSubstitution) ToSexp() string {
	panic("TODO")
}

func NewArithmeticExpansion(expression Node) *ArithmeticExpansion {
	panic("TODO")
}

func (a *ArithmeticExpansion) ToSexp() string {
	panic("TODO")
}

func NewArithmeticCommand(expression Node, redirects []interface{}, rawContent string) *ArithmeticCommand {
	panic("TODO")
}

func (a *ArithmeticCommand) ToSexp() string {
	panic("TODO")
}

func NewArithNumber(value string) *ArithNumber {
	panic("TODO")
}

func (a *ArithNumber) ToSexp() string {
	panic("TODO")
}

func NewArithEmpty() *ArithEmpty {
	panic("TODO")
}

func (a *ArithEmpty) ToSexp() string {
	panic("TODO")
}

func NewArithVar(name string) *ArithVar {
	panic("TODO")
}

func (a *ArithVar) ToSexp() string {
	panic("TODO")
}

func NewArithBinaryOp(op string, left Node, right Node) *ArithBinaryOp {
	panic("TODO")
}

func (a *ArithBinaryOp) ToSexp() string {
	panic("TODO")
}

func NewArithUnaryOp(op string, operand Node) *ArithUnaryOp {
	panic("TODO")
}

func (a *ArithUnaryOp) ToSexp() string {
	panic("TODO")
}

func NewArithPreIncr(operand Node) *ArithPreIncr {
	panic("TODO")
}

func (a *ArithPreIncr) ToSexp() string {
	panic("TODO")
}

func NewArithPostIncr(operand Node) *ArithPostIncr {
	panic("TODO")
}

func (a *ArithPostIncr) ToSexp() string {
	panic("TODO")
}

func NewArithPreDecr(operand Node) *ArithPreDecr {
	panic("TODO")
}

func (a *ArithPreDecr) ToSexp() string {
	panic("TODO")
}

func NewArithPostDecr(operand Node) *ArithPostDecr {
	panic("TODO")
}

func (a *ArithPostDecr) ToSexp() string {
	panic("TODO")
}

func NewArithAssign(op string, target Node, value Node) *ArithAssign {
	panic("TODO")
}

func (a *ArithAssign) ToSexp() string {
	panic("TODO")
}

func NewArithTernary(condition Node, ifTrue Node, ifFalse Node) *ArithTernary {
	panic("TODO")
}

func (a *ArithTernary) ToSexp() string {
	panic("TODO")
}

func NewArithComma(left Node, right Node) *ArithComma {
	panic("TODO")
}

func (a *ArithComma) ToSexp() string {
	panic("TODO")
}

func NewArithSubscript(array string, index Node) *ArithSubscript {
	panic("TODO")
}

func (a *ArithSubscript) ToSexp() string {
	panic("TODO")
}

func NewArithEscape(char string) *ArithEscape {
	panic("TODO")
}

func (a *ArithEscape) ToSexp() string {
	panic("TODO")
}

func NewArithDeprecated(expression string) *ArithDeprecated {
	panic("TODO")
}

func (a *ArithDeprecated) ToSexp() string {
	panic("TODO")
}

func NewArithConcat(parts []Node) *ArithConcat {
	panic("TODO")
}

func (a *ArithConcat) ToSexp() string {
	panic("TODO")
}

func NewAnsiCQuote(content string) *AnsiCQuote {
	panic("TODO")
}

func (a *AnsiCQuote) ToSexp() string {
	panic("TODO")
}

func NewLocaleString(content string) *LocaleString {
	panic("TODO")
}

func (l *LocaleString) ToSexp() string {
	panic("TODO")
}

func NewProcessSubstitution(direction string, command Node) *ProcessSubstitution {
	panic("TODO")
}

func (p *ProcessSubstitution) ToSexp() string {
	panic("TODO")
}

func NewNegation(pipeline Node) *Negation {
	panic("TODO")
}

func (n *Negation) ToSexp() string {
	panic("TODO")
}

func NewTime(pipeline Node, posix bool) *Time {
	panic("TODO")
}

func (t *Time) ToSexp() string {
	panic("TODO")
}

func NewConditionalExpr(body interface{}, redirects []interface{}) *ConditionalExpr {
	panic("TODO")
}

func (c *ConditionalExpr) ToSexp() string {
	panic("TODO")
}

func NewUnaryTest(op string, operand Node) *UnaryTest {
	panic("TODO")
}

func (u *UnaryTest) ToSexp() string {
	panic("TODO")
}

func NewBinaryTest(op string, left Node, right Node) *BinaryTest {
	panic("TODO")
}

func (b *BinaryTest) ToSexp() string {
	panic("TODO")
}

func NewCondAnd(left Node, right Node) *CondAnd {
	panic("TODO")
}

func (c *CondAnd) ToSexp() string {
	panic("TODO")
}

func NewCondOr(left Node, right Node) *CondOr {
	panic("TODO")
}

func (c *CondOr) ToSexp() string {
	panic("TODO")
}

func NewCondNot(operand Node) *CondNot {
	panic("TODO")
}

func (c *CondNot) ToSexp() string {
	panic("TODO")
}

func NewCondParen(inner Node) *CondParen {
	panic("TODO")
}

func (c *CondParen) ToSexp() string {
	panic("TODO")
}

func NewArray(elements []Node) *Array {
	panic("TODO")
}

func (a *Array) ToSexp() string {
	panic("TODO")
}

func NewCoproc(command Node, name string) *Coproc {
	panic("TODO")
}

func (c *Coproc) ToSexp() string {
	panic("TODO")
}

func NewParser(source string, inProcessSub bool, extglob bool) *Parser {
	panic("TODO")
}

func (p *Parser) _SetState(flag int) {
	panic("TODO")
}

func (p *Parser) _ClearState(flag int) {
	panic("TODO")
}

func (p *Parser) _InState(flag int) bool {
	panic("TODO")
}

func (p *Parser) _SaveParserState() *SavedParserState {
	panic("TODO")
}

func (p *Parser) _RestoreParserState(saved *SavedParserState) {
	panic("TODO")
}

func (p *Parser) _RecordToken(tok *Token) {
	panic("TODO")
}

func (p *Parser) _UpdateDolbraceForOp(op string, hasParam bool) {
	panic("TODO")
}

func (p *Parser) _SyncLexer() {
	panic("TODO")
}

func (p *Parser) _SyncParser() {
	panic("TODO")
}

func (p *Parser) _LexPeekToken() *Token {
	panic("TODO")
}

func (p *Parser) _LexNextToken() *Token {
	panic("TODO")
}

func (p *Parser) _LexSkipBlanks() {
	panic("TODO")
}

func (p *Parser) _LexSkipComment() bool {
	panic("TODO")
}

func (p *Parser) _LexIsCommandTerminator() bool {
	panic("TODO")
}

func (p *Parser) _LexPeekOperator() interface{} {
	panic("TODO")
}

func (p *Parser) _LexPeekReservedWord() string {
	panic("TODO")
}

func (p *Parser) _LexIsAtReservedWord(word string) bool {
	panic("TODO")
}

func (p *Parser) _LexConsumeWord(expected string) bool {
	panic("TODO")
}

func (p *Parser) _LexPeekCaseTerminator() string {
	panic("TODO")
}

func (p *Parser) AtEnd() bool {
	panic("TODO")
}

func (p *Parser) Peek() string {
	panic("TODO")
}

func (p *Parser) Advance() string {
	panic("TODO")
}

func (p *Parser) PeekAt(offset int) string {
	panic("TODO")
}

func (p *Parser) Lookahead(n int) string {
	panic("TODO")
}

func (p *Parser) _IsBangFollowedByProcsub() bool {
	panic("TODO")
}

func (p *Parser) SkipWhitespace() {
	panic("TODO")
}

func (p *Parser) SkipWhitespaceAndNewlines() {
	panic("TODO")
}

func (p *Parser) _AtListTerminatingBracket() bool {
	panic("TODO")
}

func (p *Parser) _AtEofToken() bool {
	panic("TODO")
}

func (p *Parser) _CollectRedirects() []interface{} {
	panic("TODO")
}

func (p *Parser) _ParseLoopBody(context string) Node {
	panic("TODO")
}

func (p *Parser) PeekWord() string {
	panic("TODO")
}

func (p *Parser) ConsumeWord(expected string) bool {
	panic("TODO")
}

func (p *Parser) _IsWordTerminator(ctx int, ch string, bracketDepth int, parenDepth int) bool {
	panic("TODO")
}

func (p *Parser) _ScanDoubleQuote(chars []interface{}, parts []interface{}, start int, handleLineContinuation bool) {
	panic("TODO")
}

func (p *Parser) _ParseDollarExpansion(chars []interface{}, parts []interface{}, inDquote bool) bool {
	panic("TODO")
}

func (p *Parser) _ParseWordInternal(ctx int, atCommandStart bool, inArrayLiteral bool) Node {
	panic("TODO")
}

func (p *Parser) ParseWord(atCommandStart bool, inArrayLiteral bool, inAssignBuiltin bool) Node {
	panic("TODO")
}

func (p *Parser) _ParseCommandSubstitution() interface{} {
	panic("TODO")
}

func (p *Parser) _ParseFunsub(start int) interface{} {
	panic("TODO")
}

func (p *Parser) _IsAssignmentWord(word Node) bool {
	panic("TODO")
}

func (p *Parser) _ParseBacktickSubstitution() interface{} {
	panic("TODO")
}

func (p *Parser) _ParseProcessSubstitution() interface{} {
	panic("TODO")
}

func (p *Parser) _ParseArrayLiteral() interface{} {
	panic("TODO")
}

func (p *Parser) _ParseArithmeticExpansion() interface{} {
	panic("TODO")
}

func (p *Parser) _ParseArithExpr(content string) Node {
	panic("TODO")
}

func (p *Parser) _ArithAtEnd() bool {
	panic("TODO")
}

func (p *Parser) _ArithPeek(offset int) string {
	panic("TODO")
}

func (p *Parser) _ArithAdvance() string {
	panic("TODO")
}

func (p *Parser) _ArithSkipWs() {
	panic("TODO")
}

func (p *Parser) _ArithMatch(s string) bool {
	panic("TODO")
}

func (p *Parser) _ArithConsume(s string) bool {
	panic("TODO")
}

func (p *Parser) _ArithParseComma() Node {
	panic("TODO")
}

func (p *Parser) _ArithParseAssign() Node {
	panic("TODO")
}

func (p *Parser) _ArithParseTernary() Node {
	panic("TODO")
}

func (p *Parser) _ArithParseLeftAssoc(ops []interface{}, parsefn interface{}) Node {
	panic("TODO")
}

func (p *Parser) _ArithParseLogicalOr() Node {
	panic("TODO")
}

func (p *Parser) _ArithParseLogicalAnd() Node {
	panic("TODO")
}

func (p *Parser) _ArithParseBitwiseOr() Node {
	panic("TODO")
}

func (p *Parser) _ArithParseBitwiseXor() Node {
	panic("TODO")
}

func (p *Parser) _ArithParseBitwiseAnd() Node {
	panic("TODO")
}

func (p *Parser) _ArithParseEquality() Node {
	panic("TODO")
}

func (p *Parser) _ArithParseComparison() Node {
	panic("TODO")
}

func (p *Parser) _ArithParseShift() Node {
	panic("TODO")
}

func (p *Parser) _ArithParseAdditive() Node {
	panic("TODO")
}

func (p *Parser) _ArithParseMultiplicative() Node {
	panic("TODO")
}

func (p *Parser) _ArithParseExponentiation() Node {
	panic("TODO")
}

func (p *Parser) _ArithParseUnary() Node {
	panic("TODO")
}

func (p *Parser) _ArithParsePostfix() Node {
	panic("TODO")
}

func (p *Parser) _ArithParsePrimary() Node {
	panic("TODO")
}

func (p *Parser) _ArithParseExpansion() Node {
	panic("TODO")
}

func (p *Parser) _ArithParseCmdsub() Node {
	panic("TODO")
}

func (p *Parser) _ArithParseBracedParam() Node {
	panic("TODO")
}

func (p *Parser) _ArithParseSingleQuote() Node {
	panic("TODO")
}

func (p *Parser) _ArithParseDoubleQuote() Node {
	panic("TODO")
}

func (p *Parser) _ArithParseBacktick() Node {
	panic("TODO")
}

func (p *Parser) _ArithParseNumberOrVar() Node {
	panic("TODO")
}

func (p *Parser) _ParseDeprecatedArithmetic() interface{} {
	panic("TODO")
}

func (p *Parser) _ParseParamExpansion(inDquote bool) interface{} {
	panic("TODO")
}

func (p *Parser) ParseRedirect() interface{} {
	panic("TODO")
}

func (p *Parser) _ParseHeredocDelimiter() interface{} {
	panic("TODO")
}

func (p *Parser) _ReadHeredocLine(quoted bool) interface{} {
	panic("TODO")
}

func (p *Parser) _LineMatchesDelimiter(line string, delimiter string, stripTabs bool) interface{} {
	panic("TODO")
}

func (p *Parser) _GatherHeredocBodies() {
	panic("TODO")
}

func (p *Parser) _ParseHeredoc(fd int, stripTabs bool) Node {
	panic("TODO")
}

func (p *Parser) ParseCommand() Node {
	panic("TODO")
}

func (p *Parser) ParseSubshell() Node {
	panic("TODO")
}

func (p *Parser) ParseArithmeticCommand() Node {
	panic("TODO")
}

func (p *Parser) ParseConditionalExpr() Node {
	panic("TODO")
}

func (p *Parser) _CondSkipWhitespace() {
	panic("TODO")
}

func (p *Parser) _CondAtEnd() bool {
	panic("TODO")
}

func (p *Parser) _ParseCondOr() Node {
	panic("TODO")
}

func (p *Parser) _ParseCondAnd() Node {
	panic("TODO")
}

func (p *Parser) _ParseCondTerm() Node {
	panic("TODO")
}

func (p *Parser) _ParseCondWord() Node {
	panic("TODO")
}

func (p *Parser) _ParseCondRegexWord() Node {
	panic("TODO")
}

func (p *Parser) ParseBraceGroup() Node {
	panic("TODO")
}

func (p *Parser) ParseIf() Node {
	panic("TODO")
}

func (p *Parser) _ParseElifChain() Node {
	panic("TODO")
}

func (p *Parser) ParseWhile() Node {
	panic("TODO")
}

func (p *Parser) ParseUntil() Node {
	panic("TODO")
}

func (p *Parser) ParseFor() interface{} {
	panic("TODO")
}

func (p *Parser) _ParseForArith() Node {
	panic("TODO")
}

func (p *Parser) ParseSelect() Node {
	panic("TODO")
}

func (p *Parser) _ConsumeCaseTerminator() string {
	panic("TODO")
}

func (p *Parser) ParseCase() Node {
	panic("TODO")
}

func (p *Parser) ParseCoproc() Node {
	panic("TODO")
}

func (p *Parser) ParseFunction() Node {
	panic("TODO")
}

func (p *Parser) _ParseCompoundCommand() Node {
	panic("TODO")
}

func (p *Parser) _AtListUntilTerminator(stopWords map[string]struct{}) bool {
	panic("TODO")
}

func (p *Parser) ParseListUntil(stopWords map[string]struct{}) Node {
	panic("TODO")
}

func (p *Parser) ParseCompoundCommand() Node {
	panic("TODO")
}

func (p *Parser) ParsePipeline() Node {
	panic("TODO")
}

func (p *Parser) _ParseSimplePipeline() Node {
	panic("TODO")
}

func (p *Parser) ParseListOperator() string {
	panic("TODO")
}

func (p *Parser) _PeekListOperator() string {
	panic("TODO")
}

func (p *Parser) ParseList(newlineAsSeparator bool) Node {
	panic("TODO")
}

func (p *Parser) ParseComment() Node {
	panic("TODO")
}

func (p *Parser) Parse() []Node {
	panic("TODO")
}

func (p *Parser) _LastWordOnOwnLine(nodes []Node) bool {
	panic("TODO")
}

func (p *Parser) _StripTrailingBackslashFromLastWord(nodes []Node) {
	panic("TODO")
}

func (p *Parser) _FindLastWord(node Node) Node {
	panic("TODO")
}
