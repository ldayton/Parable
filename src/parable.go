package parable

import (
	"fmt"
	"reflect"
	"strconv"
	"strings"
	"unicode/utf8"
)

// Node is the interface for all AST nodes
type Node interface {
	ToSexp() string
	GetKind() string
}

// Helper functions
func toSet(items interface{}) map[interface{}]bool {
	m := make(map[interface{}]bool)
	switch v := items.(type) {
	case []interface{}:
		for _, item := range v {
			m[item] = true
		}
	case string:
		for _, c := range v {
			m[string(c)] = true
		}
	}
	return m
}

func contains(set map[interface{}]bool, key interface{}) bool {
	return set[key]
}

func substring(s string, start, end int) string {
	if end > len(s) {
		end = len(s)
	}
	if start < 0 {
		start = 0
	}
	return s[start:end]
}

func parseInt(s string, base int) int {
	n, _ := strconv.ParseInt(s, base, 64)
	return int(n)
}

func toInt(v interface{}) int {
	switch x := v.(type) {
	case int:
		return x
	case string:
		n, _ := strconv.Atoi(x)
		return n
	default:
		return 0
	}
}

var _ = substring
var _ = parseInt
var _ = toInt

func appendByte(slice []byte, val int) []byte {
	return append(slice, byte(val))
}

func joinStrings(items []interface{}, sep string) string {
	strs := make([]string, len(items))
	for i, item := range items {
		strs[i] = fmt.Sprintf("%v", item)
	}
	return strings.Join(strs, sep)
}

func sublist(items []interface{}, start, end int) []interface{} {
	if start < 0 {
		start = 0
	}
	if end > len(items) {
		end = len(items)
	}
	return items[start:end]
}

func isAlpha_h(s string) bool {
	for _, c := range s {
		if !((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z')) {
			return false
		}
	}
	return len(s) > 0
}

func isAlnum_h(s string) bool {
	for _, c := range s {
		if !((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9')) {
			return false
		}
	}
	return len(s) > 0
}

func isDigit_h(s string) bool {
	for _, c := range s {
		if !(c >= '0' && c <= '9') {
			return false
		}
	}
	return len(s) > 0
}

func isSpace_h(s string) bool {
	for _, c := range s {
		if !(c == ' ' || c == '\t' || c == '\n' || c == '\r') {
			return false
		}
	}
	return len(s) > 0
}

func getAttr(obj interface{}, attr string, defaultVal interface{}) interface{} {
	// Simplified getattr - just return default for now
	return defaultVal
}

func byteToStr(b byte) string { return string([]byte{b}) }

func pairFirst(p interface{}) Node {
	if arr, ok := p.([]interface{}); ok && len(arr) > 0 {
		if n, ok := arr[0].(Node); ok {
			return n
		}
	}
	return nil
}

func pairSecond(p interface{}) bool {
	if arr, ok := p.([]interface{}); ok && len(arr) > 1 {
		if b, ok := arr[1].(bool); ok {
			return b
		}
	}
	return false
}

func getCommand(n interface{}) Node {
	v := reflect.ValueOf(n)
	if v.Kind() == reflect.Ptr {
		v = v.Elem()
	}
	f := v.FieldByName("Command")
	if f.IsValid() {
		if cmd, ok := f.Interface().(Node); ok {
			return cmd
		}
	}
	return nil
}

type ParseError struct {
	Message string
	Pos     *int
	Line    *int
}

func (p *ParseError) Error() string {
	return p.formatMessage()
}

func NewParseError(message string, pos *int, line *int) *ParseError {
	p := &ParseError{}
	p.Message = message
	p.Pos = pos
	p.Line = line
	return p
}

func (p *ParseError) formatMessage() string {
	if (p.Line != nil) && (p.Pos != nil) {
		return ((((("Parse error at line " + fmt.Sprintf("%v", p.Line)) + ", position ") + fmt.Sprintf("%v", p.Pos)) + ": ") + p.Message)
	} else if p.Pos != nil {
		return ((("Parse error at position " + fmt.Sprintf("%v", p.Pos)) + ": ") + p.Message)
	}
	return ("Parse error: " + p.Message)
}

func isHexDigit(c byte) bool {
	return (((c >= '0') && (c <= '9')) || ((c >= 'a') && (c <= 'f')) || ((c >= 'A') && (c <= 'F')))
}

func isOctalDigit(c byte) bool {
	return ((c >= '0') && (c <= '7'))
}

// ANSI-C escape sequence byte values
var ANSI_C_ESCAPES = map[string]interface{}{"a": 7, "b": 8, "e": 27, "E": 27, "f": 12, "n": 10, "r": 13, "t": 9, "v": 11, "\\": 92, "\"": 34, "?": 63}

func getAnsiEscape(c byte) int {
	if c == 'a' {
		return 7
	}
	if c == 'b' {
		return 8
	}
	if (c == 'e') || (c == 'E') {
		return 27
	}
	if c == 'f' {
		return 12
	}
	if c == 'n' {
		return 10
	}
	if c == 'r' {
		return 13
	}
	if c == 't' {
		return 9
	}
	if c == 'v' {
		return 11
	}
	if c == '\\' {
		return 92
	}
	if c == '"' {
		return 34
	}
	if c == '?' {
		return 63
	}
	return -1
}

func isWhitespace(c byte) bool {
	return ((c == ' ') || (c == '\t') || (c == '\n'))
}

func isWhitespaceNoNewline(c byte) bool {
	return ((c == ' ') || (c == '\t'))
}

func startsWithAt(s string, pos int, prefix string) bool {
	return strings.HasPrefix(s[pos:], prefix)
}

type Word struct {
	Value string
	Parts []Node
	Kind  string
}

func (w *Word) GetKind() string {
	return w.Kind
}

func NewWord(value string, parts []Node) *Word {
	w := &Word{}
	w.Kind = "word"
	w.Value = value
	w.Parts = parts
	return w
}

func (w *Word) ToSexp() string {
	value := w.Value
	// Expand ALL $'...' ANSI-C quotes (handles escapes and strips $)
	value = w.expandAllAnsiCQuotes(value)
	// Strip $ from locale strings $"..." (quote-aware)
	value = w.stripLocaleStringDollars(value)
	// Normalize whitespace in array assignments: name=(a  b\tc) -> name=(a b c)
	value = w.normalizeArrayWhitespace(value)
	// Format command substitutions with bash-oracle pretty-printing (before escaping)
	value = w.formatCommandSubstitutions(value)
	// Strip line continuations (backslash-newline) from arithmetic expressions
	value = w.stripArithLineContinuations(value)
	// Double CTLESC (0x01) bytes - bash-oracle uses this for quoting control chars
	// Exception: don't double when preceded by odd number of backslashes (escaped)
	value = w.doubleCtlescSmart(value)
	// Prefix DEL (0x7f) with CTLESC - bash-oracle quotes this control char
	value = strings.ReplaceAll(value, "", "")
	// Escape backslashes for s-expression output
	value = strings.ReplaceAll(value, "\\", "\\\\")
	// Escape double quotes, newlines, and tabs
	escaped := strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(value, "\"", "\\\""), "\n", "\\n"), "\t", "\\t")
	return (("(word \"" + escaped) + "\")")
}

func (w *Word) appendWithCtlesc(result []byte, byte_val int) {
	result = append(result, byte(byte_val))
}

func (w *Word) doubleCtlescSmart(value string) string {
	result := []interface{}{}
	in_single := false
	in_double := false
	var bs_count int
	var j int
	for _, c := range value {
		// Track quote state
		if (c == '\'') && !(in_double) {
			in_single = !(in_single)
		} else if (c == '"') && !(in_single) {
			in_double = !(in_double)
		}
		result = append(result, c)
		if c == '\x01' {
			// Only count backslashes in double-quoted context (where they escape)
			// In single quotes, backslashes are literal, so always double CTLESC
			if in_double {
				bs_count = 0
				for j := (len(result) - 2); j > -1; j-- {
					if result[j] == '\\' {
						bs_count += 1
					} else {
						break
					}
				}
				if (bs_count % 2) == 0 {
					result = append(result, "")
				}
			} else {
				// Outside double quotes (including single quotes): always double
				result = append(result, "")
			}
		}
	}
	return joinStrings(result, "")
}

func (w *Word) expandAnsiCEscapes(value string) string {
	if !(strings.HasPrefix(value, "'") && strings.HasSuffix(value, "'")) {
		return value
	}
	inner := substring(value, 1, (len(value) - 1))
	result := []byte{}
	i := 0
	for i < len(inner) {
		var ctrl_val int
		var j int
		var ctrl_char byte
		var simple int
		var byte_val int
		var hex_str string
		var codepoint int
		if (inner[i] == '\\') && ((i + 1) < len(inner)) {
			c := inner[(i + 1)]
			// Check simple escapes first
			simple = getAnsiEscape(c)
			if simple >= 0 {
				result = append(result, byte(simple))
				i += 2
			} else if c == '\'' {
				// bash-oracle outputs \' as '\'' (shell quoting trick)
				result = append(result, []byte{39, 92, 39, 39}...)
				i += 2
			} else if c == 'x' {
				// Check for \x{...} brace syntax (bash 5.3+)
				if ((i + 2) < len(inner)) && (inner[(i+2)] == '{') {
					// Find closing brace or end of hex digits
					j = (i + 3)
					for (j < len(inner)) && isHexDigit(inner[j]) {
						j += 1
					}
					hex_str = substring(inner, (i + 3), j)
					if (j < len(inner)) && (inner[j] == '}') {
						j += 1
					}
					// If no hex digits, treat as NUL (truncates)
					if hex_str == "" {
						return (("'" + string(result)) + "'")
					}
					byte_val = (parseInt(hex_str, 16) & 255)
					if byte_val == 0 {
						return (("'" + string(result)) + "'")
					}
					w.appendWithCtlesc(result, byte_val)
					i = j
				} else {
					// Hex escape \xHH (1-2 hex digits) - raw byte
					j = (i + 2)
					for (j < len(inner)) && (j < (i + 4)) && isHexDigit(inner[j]) {
						j += 1
					}
					if j > (i + 2) {
						byte_val = parseInt(substring(inner, (i+2), j), 16)
						if byte_val == 0 {
							// NUL truncates string
							return (("'" + string(result)) + "'")
						}
						w.appendWithCtlesc(result, byte_val)
						i = j
					} else {
						result = append(result, inner[i])
						i += 1
					}
				}
			} else if c == 'u' {
				// Unicode escape \uHHHH (1-4 hex digits) - encode as UTF-8
				j = (i + 2)
				for (j < len(inner)) && (j < (i + 6)) && isHexDigit(inner[j]) {
					j += 1
				}
				if j > (i + 2) {
					codepoint = parseInt(substring(inner, (i+2), j), 16)
					if codepoint == 0 {
						// NUL truncates string
						return (("'" + string(result)) + "'")
					}
					result = append(result, []byte(string(rune(codepoint)))...)
					i = j
				} else {
					result = append(result, inner[i])
					i += 1
				}
			} else if c == 'U' {
				// Unicode escape \UHHHHHHHH (1-8 hex digits) - encode as UTF-8
				j = (i + 2)
				for (j < len(inner)) && (j < (i + 10)) && isHexDigit(inner[j]) {
					j += 1
				}
				if j > (i + 2) {
					codepoint = parseInt(substring(inner, (i+2), j), 16)
					if codepoint == 0 {
						// NUL truncates string
						return (("'" + string(result)) + "'")
					}
					result = append(result, []byte(string(rune(codepoint)))...)
					i = j
				} else {
					result = append(result, inner[i])
					i += 1
				}
			} else if c == 'c' {
				// Control character \cX - mask with 0x1f
				if (i + 3) <= len(inner) {
					ctrl_char = inner[(i + 2)]
					ctrl_val = (int(ctrl_char) & 31)
					if ctrl_val == 0 {
						// NUL truncates string
						return (("'" + string(result)) + "'")
					}
					w.appendWithCtlesc(result, ctrl_val)
					i += 3
				} else {
					result = append(result, inner[i])
					i += 1
				}
			} else if c == '0' {
				// Nul or octal \0 or \0NNN
				j = (i + 2)
				for (j < len(inner)) && (j < (i + 5)) && isOctalDigit(inner[j]) {
					j += 1
				}
				if j > (i + 2) {
					byte_val = parseInt(substring(inner, (i+1), j), 8)
					if byte_val == 0 {
						// NUL truncates string
						return (("'" + string(result)) + "'")
					}
					w.appendWithCtlesc(result, byte_val)
					i = j
				} else {
					// Just \0 - NUL truncates string
					return (("'" + string(result)) + "'")
				}
			} else if (c >= '1') && (c <= '7') {
				// Octal escape \NNN (1-3 digits) - raw byte
				j = (i + 1)
				for (j < len(inner)) && (j < (i + 4)) && isOctalDigit(inner[j]) {
					j += 1
				}
				byte_val = parseInt(substring(inner, (i+1), j), 8)
				if byte_val == 0 {
					// NUL truncates string
					return (("'" + string(result)) + "'")
				}
				w.appendWithCtlesc(result, byte_val)
				i = j
			} else {
				// Unknown escape - preserve as-is
				result = append(result, 92)
				result = append(result, c)
				i += 2
			}
		} else {
			result = append(result, inner[i])
			i += 1
		}
	}
	// Decode as UTF-8, replacing invalid sequences with U+FFFD
	return (("'" + string(result)) + "'")
}

func (w *Word) expandAllAnsiCQuotes(value string) string {
	result := []interface{}{}
	i := 0
	in_single_quote := false
	in_double_quote := false
	brace_depth := 0
	for i < len(value) {
		ch := value[i]
		// Track brace depth for parameter expansions
		if !(in_single_quote) {
			if startsWithAt(value, i, "${") {
				brace_depth += 1
				result = append(result, "${")
				i += 2
				continue
			} else if (ch == '}') && (brace_depth > 0) {
				brace_depth -= 1
				result = append(result, ch)
				i += 1
				continue
			}
		}
		// Inside ${...}, we can expand $'...' even if originally in double quotes
		effective_in_dquote := (in_double_quote && (brace_depth == 0))
		// Track quote state to avoid matching $' inside regular quotes
		var j int
		var prev string
		var last interface{}
		var ansi_str string
		var expanded string
		if (ch == '\'') && !(effective_in_dquote) {
			// Check if this is start of $'...' ANSI-C string
			if !(in_single_quote) && (i > 0) && (value[(i-1)] == '$') {
				// This is handled below when we see $'
				result = append(result, ch)
				i += 1
			} else if in_single_quote {
				// End of single-quoted string
				in_single_quote = false
				result = append(result, ch)
				i += 1
			} else {
				// Start of regular single-quoted string
				in_single_quote = true
				result = append(result, ch)
				i += 1
			}
		} else if (ch == '"') && !(in_single_quote) {
			in_double_quote = !(in_double_quote)
			result = append(result, ch)
			i += 1
		} else if (ch == '\\') && ((i + 1) < len(value)) && !(in_single_quote) {
			// Backslash escape - skip both chars to avoid misinterpreting \" or \'
			result = append(result, ch)
			result = append(result, value[(i+1)])
			i += 2
		} else if startsWithAt(value, i, "$'") && !(in_single_quote) && !(effective_in_dquote) {
			// ANSI-C quoted string - find matching closing quote
			j = (i + 2)
			for j < len(value) {
				if (value[j] == '\\') && ((j + 1) < len(value)) {
					j += 2
				} else if value[j] == '\'' {
					j += 1
					break
				} else {
					j += 1
				}
			}
			// Extract and expand the $'...' sequence
			ansi_str = substring(value, i, j)
			// Strip the $ and expand escapes
			expanded = w.expandAnsiCEscapes(substring(ansi_str, 1, len(ansi_str)))
			// Inside ${...}, strip quotes for default/alternate value operators
			// but keep them for pattern replacement operators
			if (brace_depth > 0) && strings.HasPrefix(expanded, "'") && strings.HasSuffix(expanded, "'") {
				inner := substring(expanded, 1, (len(expanded) - 1))
				// Only strip if non-empty, no CTLESC, and after a default value operator
				if (inner != "") && (strings.Index(inner, "") == -1) {
					// Check what precedes - default value ops: :- := :+ :? - = + ?
					if len(result) >= 2 {
						prev = joinStrings(sublist(result, (len(result)-2), len(result)), "")
					} else {
						prev = ""
					}
					if strings.HasSuffix(prev, ":-") || strings.HasSuffix(prev, ":=") || strings.HasSuffix(prev, ":+") || strings.HasSuffix(prev, ":?") {
						expanded = inner
					} else if len(result) >= 1 {
						last = result[(len(result) - 1)]
						// Single char operators (not after :), but not /
						if ((last == '-') || (last == '=') || (last == '+') || (last == '?')) && ((len(result) < 2) || (result[(len(result)-2)] != ':')) {
							expanded = inner
						}
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
	return joinStrings(result, "")
}

func (w *Word) stripLocaleStringDollars(value string) string {
	result := []interface{}{}
	i := 0
	in_single_quote := false
	in_double_quote := false
	for i < len(value) {
		ch := value[i]
		if (ch == '\'') && !(in_double_quote) {
			in_single_quote = !(in_single_quote)
			result = append(result, ch)
			i += 1
		} else if (ch == '"') && !(in_single_quote) {
			in_double_quote = !(in_double_quote)
			result = append(result, ch)
			i += 1
		} else if (ch == '\\') && ((i + 1) < len(value)) {
			// Escape - copy both chars
			result = append(result, ch)
			result = append(result, value[(i+1)])
			i += 2
		} else if startsWithAt(value, i, "$\"") && !(in_single_quote) && !(in_double_quote) {
			// Locale string $"..." outside quotes - strip the $ and enter double quote
			result = append(result, "\"")
			in_double_quote = true
			i += 2
		} else {
			result = append(result, ch)
			i += 1
		}
	}
	return joinStrings(result, "")
}

func (w *Word) normalizeArrayWhitespace(value string) string {
	// Match array assignment pattern: name=( or name+=(
	if !(strings.HasSuffix(value, ")")) {
		return value
	}
	// Parse identifier: starts with letter/underscore, then alnum/underscore
	i := 0
	if !((i < len(value)) && (isAlpha_h(string(value[i])) || (value[i] == '_'))) {
		return value
	}
	i += 1
	for (i < len(value)) && (isAlnum_h(string(value[i])) || (value[i] == '_')) {
		i += 1
	}
	// Optional + for +=
	if (i < len(value)) && (value[i] == '+') {
		i += 1
	}
	// Must have =(
	if !(((i + 1) < len(value)) && (value[i] == '=') && (value[(i+1)] == '(')) {
		return value
	}
	prefix := substring(value, 0, (i + 1))
	// Extract content inside parentheses
	inner := substring(value, (len(prefix) + 1), (len(value) - 1))
	// Normalize whitespace while respecting quotes
	normalized := []interface{}{}
	i = 0
	in_whitespace := true
	for i < len(inner) {
		ch := inner[i]
		var j int
		if isWhitespace(ch) {
			if !(in_whitespace) && (len(normalized) > 0) {
				normalized = append(normalized, " ")
				in_whitespace = true
			}
			i += 1
		} else if ch == '\'' {
			// Single-quoted string - preserve as-is
			in_whitespace = false
			j = (i + 1)
			for (j < len(inner)) && (inner[j] != '\'') {
				j += 1
			}
			normalized = append(normalized, substring(inner, i, (j+1)))
			i = (j + 1)
		} else if ch == '"' {
			// Double-quoted string - preserve as-is
			in_whitespace = false
			j = (i + 1)
			for j < len(inner) {
				if (inner[j] == '\\') && ((j + 1) < len(inner)) {
					j += 2
				} else if inner[j] == '"' {
					break
				} else {
					j += 1
				}
			}
			normalized = append(normalized, substring(inner, i, (j+1)))
			i = (j + 1)
		} else if (ch == '\\') && ((i + 1) < len(inner)) {
			// Escape sequence
			in_whitespace = false
			normalized = append(normalized, substring(inner, i, (i+2)))
			i += 2
		} else {
			in_whitespace = false
			normalized = append(normalized, ch)
			i += 1
		}
	}
	// Strip trailing space
	result := strings.TrimRight(joinStrings(normalized, ""), " ")
	return (((prefix + "(") + result) + ")")
}

func (w *Word) stripArithLineContinuations(value string) string {
	result := []interface{}{}
	i := 0
	for i < len(value) {
		// Check for $(( arithmetic expression
		var start int
		var depth int
		if startsWithAt(value, i, "$((") {
			// Find matching ))
			start = i
			i += 3
			depth = 1
			arith_content := []interface{}{}
			for (i < len(value)) && (depth > 0) {
				if startsWithAt(value, i, "((") {
					arith_content = append(arith_content, "((")
					depth += 1
					i += 2
				} else if startsWithAt(value, i, "))") {
					depth -= 1
					if depth > 0 {
						arith_content = append(arith_content, "))")
					}
					i += 2
				} else if (value[i] == '\\') && ((i + 1) < len(value)) && (value[(i+1)] == '\n') {
					// Skip backslash-newline (line continuation)
					i += 2
				} else {
					arith_content = append(arith_content, value[i])
					i += 1
				}
			}
			if depth == 0 {
				// Found proper )) closing - this is arithmetic
				result = append(result, (("$((" + joinStrings(arith_content, "")) + "))"))
			} else {
				// Didn't find )) - not arithmetic (likely $( + ( subshell), pass through
				result = append(result, substring(value, start, i))
			}
		} else {
			result = append(result, value[i])
			i += 1
		}
	}
	return joinStrings(result, "")
}

func (w *Word) collectCmdsubs(node interface{}) []interface{} {
	result := []interface{}{}
	node_kind := getAttr(node, "kind", nil)
	var expr interface{}
	if node_kind == "cmdsub" {
		result = append(result, node)
	} else {
		expr = getAttr(node, "expression", nil)
		if expr != nil {
			// ArithmeticExpansion, ArithBinaryOp, etc.
			result = append(result, w.collectCmdsubs(expr)...)
		}
	}
	left := getAttr(node, "left", nil)
	if left != nil {
		result = append(result, w.collectCmdsubs(left)...)
	}
	right := getAttr(node, "right", nil)
	if right != nil {
		result = append(result, w.collectCmdsubs(right)...)
	}
	operand := getAttr(node, "operand", nil)
	if operand != nil {
		result = append(result, w.collectCmdsubs(operand)...)
	}
	condition := getAttr(node, "condition", nil)
	if condition != nil {
		result = append(result, w.collectCmdsubs(condition)...)
	}
	true_value := getAttr(node, "true_value", nil)
	if true_value != nil {
		result = append(result, w.collectCmdsubs(true_value)...)
	}
	false_value := getAttr(node, "false_value", nil)
	if false_value != nil {
		result = append(result, w.collectCmdsubs(false_value)...)
	}
	return result
}

func (w *Word) formatCommandSubstitutions(value string) string {
	// Collect command substitutions from all parts, including nested ones
	cmdsub_parts := []interface{}{}
	procsub_parts := []interface{}{}
	for _, p := range w.Parts {
		if p.GetKind() == "cmdsub" {
			cmdsub_parts = append(cmdsub_parts, p)
		} else if p.GetKind() == "procsub" {
			procsub_parts = append(procsub_parts, p)
		} else {
			cmdsub_parts = append(cmdsub_parts, w.collectCmdsubs(p)...)
		}
	}
	// Check if we have ${ or ${| brace command substitutions to format
	has_brace_cmdsub := ((strings.Index(value, "${ ") != -1) || (strings.Index(value, "${|") != -1))
	if (len(cmdsub_parts) == 0) && (len(procsub_parts) == 0) && !(has_brace_cmdsub) {
		return value
	}
	result := []interface{}{}
	i := 0
	cmdsub_idx := 0
	procsub_idx := 0
	for i < len(value) {
		// Check for $( command substitution (but not $(( arithmetic)
		var j int
		var node Node
		var formatted string
		var depth int
		var direction byte
		if startsWithAt(value, i, "$(") && !(startsWithAt(value, i, "$((")) && (cmdsub_idx < len(cmdsub_parts)) {
			// Find matching close paren using bash-aware matching
			j = findCmdsubEnd(value, (i + 2))
			// Format this command substitution
			node = cmdsub_parts[cmdsub_idx].(Node)
			formatted = formatCmdsubNode(getCommand(node), 0, false)
			// Add space after $( if content starts with ( to avoid $((
			if strings.HasPrefix(formatted, "(") {
				result = append(result, (("$( " + formatted) + ")"))
			} else {
				result = append(result, (("$(" + formatted) + ")"))
			}
			cmdsub_idx += 1
			i = j
		} else if (value[i] == '`') && (cmdsub_idx < len(cmdsub_parts)) {
			// Check for backtick command substitution
			// Find matching backtick
			j = (i + 1)
			for j < len(value) {
				if (value[j] == '\\') && ((j + 1) < len(value)) {
					j += 2
					continue
				}
				if value[j] == '`' {
					j += 1
					break
				}
				j += 1
			}
			// Keep backtick substitutions as-is (bash-oracle doesn't reformat them)
			result = append(result, substring(value, i, j))
			cmdsub_idx += 1
			i = j
		} else if (startsWithAt(value, i, ">(") || startsWithAt(value, i, "<(")) && (procsub_idx < len(procsub_parts)) {
			// Check for >( or <( process substitution
			direction = value[i]
			// Find matching close paren
			j = findCmdsubEnd(value, (i + 2))
			// Format this process substitution (with in_procsub=True for no-space subshells)
			node = procsub_parts[procsub_idx].(Node)
			formatted = formatCmdsubNode(getCommand(node), 0, false)
			result = append(result, (((byteToStr(direction) + "(") + formatted) + ")"))
			procsub_idx += 1
			i = j
		} else if startsWithAt(value, i, "${ ") || startsWithAt(value, i, "${|") {
			// Check for ${ (space) or ${| brace command substitution
			prefix := substring(value, i, (i + 3))
			// Find matching close brace
			j = (i + 3)
			depth = 1
			for (j < len(value)) && (depth > 0) {
				if value[j] == '{' {
					depth += 1
				} else if value[j] == '}' {
					depth -= 1
				}
				j += 1
			}
			// Parse and format the inner content
			inner := substring(value, (i + 2), (j - 1))
			// Check if content is all whitespace - normalize to single space
			if strings.TrimSpace(inner) == "" {
				result = append(result, "${ }")
			} else {
				// try {
				parser := NewParser(strings.TrimLeft(inner, " |"))
				parsed := parser.ParseList(true)
				if parsed != nil {
					formatted = formatCmdsubNode(parsed, 0, false)
					result = append(result, ((prefix + formatted) + "; }"))
				} else {
					result = append(result, "${ }")
				}
				// } catch {
				// ...
				// }
			}
			i = j
		} else {
			result = append(result, value[i])
			i += 1
		}
	}
	return joinStrings(result, "")
}

func (w *Word) GetCondFormattedValue() string {
	// Expand ANSI-C quotes
	value := w.expandAllAnsiCQuotes(w.Value)
	// Format command substitutions
	value = w.formatCommandSubstitutions(value)
	// Bash doubles CTLESC (\x01) characters in output
	value = strings.ReplaceAll(value, "", "")
	return strings.TrimRight(value, "\n")
}

type Command struct {
	Words     []Node
	Redirects []Node
	Kind      string
}

func (c *Command) GetKind() string {
	return c.Kind
}

func NewCommand(words []Node, redirects []Node) *Command {
	c := &Command{}
	c.Kind = "command"
	c.Words = words
	c.Redirects = redirects
	return c
}

func (c *Command) ToSexp() string {
	parts := []interface{}{}
	for _, w := range c.Words {
		parts = append(parts, w.ToSexp())
	}
	for _, r := range c.Redirects {
		parts = append(parts, r.ToSexp())
	}
	inner := joinStrings(parts, " ")
	if inner == "" {
		return "(command)"
	}
	return (("(command " + inner) + ")")
}

type Pipeline struct {
	Commands []Node
	Kind     string
}

func (p *Pipeline) GetKind() string {
	return p.Kind
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
	// Build list of (cmd, needs_pipe_both_redirect) filtering out PipeBoth markers
	cmds := []interface{}{}
	i := 0
	for i < len(p.Commands) {
		cmd := p.Commands[i]
		if cmd.GetKind() == "pipe-both" {
			i += 1
			continue
		}
		// Check if next element is PipeBoth
		needs_redirect := (((i + 1) < len(p.Commands)) && (p.Commands[(i+1)].GetKind() == "pipe-both"))
		cmds = append(cmds, []interface{}{cmd, needs_redirect})
		i += 1
	}
	var pair interface{}
	var needs bool
	if len(cmds) == 1 {
		pair = cmds[0]
		cmd = pairFirst(pair)
		needs = pairSecond(pair)
		return p.cmdSexp(cmd, needs)
	}
	// Nest right-associatively: (pipe a (pipe b c))
	last_pair := cmds[(len(cmds) - 1)]
	last_cmd := pairFirst(last_pair)
	last_needs := pairSecond(last_pair)
	result := p.cmdSexp(last_cmd, last_needs)
	j := (len(cmds) - 2)
	for j >= 0 {
		pair = cmds[j]
		cmd = pairFirst(pair)
		needs = pairSecond(pair)
		if needs && (cmd.GetKind() != "command") {
			// Compound command: redirect as sibling in pipe
			result = (((("(pipe " + cmd.ToSexp()) + " (redirect \">&\" 1) ") + result) + ")")
		} else {
			result = (((("(pipe " + p.cmdSexp(cmd, needs)) + " ") + result) + ")")
		}
		j -= 1
	}
	return result
}

func (p *Pipeline) cmdSexp(cmd Node, needs_redirect bool) string {
	if !(needs_redirect) {
		return cmd.ToSexp()
	}
	var w interface{}
	var r interface{}
	if cmd.GetKind() == "command" {
		// Inject redirect inside command
		parts := []interface{}{}
		for _, w := range cmd.Words {
			parts = append(parts, w.ToSexp())
		}
		for _, r := range cmd.Redirects {
			parts = append(parts, r.ToSexp())
		}
		parts = append(parts, "(redirect \">&\" 1)")
		return (("(command " + joinStrings(parts, " ")) + ")")
	}
	// Compound command handled by caller
	return cmd.ToSexp()
}

type List struct {
	Parts []Node
	Kind  string
}

func (l *List) GetKind() string {
	return l.Kind
}

func NewList(parts []Node) *List {
	l := &List{}
	l.Kind = "list"
	l.Parts = parts
	return l
}

func (l *List) ToSexp() string {
	// parts = [cmd, op, cmd, op, cmd, ...]
	// Bash precedence: && and || bind tighter than ; and &
	parts := toSlice(l.Parts)
	op_names := map[string]interface{}{"&&": "and", "||": "or", ";": "semi", "\n": "semi", "&": "background"}
	// Strip trailing ; or \n (bash ignores it)
	for (len(parts) > 1) && (parts[(len(parts)-1)].(Node).GetKind() == "operator") && ((parts[(len(parts)-1)].(Node).Op == ';') || (parts[(len(parts)-1)].(Node).Op == '\n')) {
		parts = sublist(parts, 0, (len(parts) - 1))
	}
	if len(parts) == 1 {
		return parts[0].(Node).ToSexp()
	}
	// Handle trailing & as unary background operator
	// & only applies to the immediately preceding pipeline, not the whole list
	var left_sexp interface{}
	var left interface{}
	var right_sexp interface{}
	var right interface{}
	var inner_parts interface{}
	var inner_list interface{}
	if (parts[(len(parts)-1)].(Node).GetKind() == "operator") && (parts[(len(parts)-1)].(Node).Op == '&') {
		// Find rightmost ; or \n to split there
		for i := (len(parts) - 3); i > 0; i-- {
			if (parts[i].(Node).GetKind() == "operator") && ((parts[i].(Node).Op == ';') || (parts[i].(Node).Op == '\n')) {
				left = sublist(parts, 0, i)
				right = sublist(parts, (i + 1), (len(parts) - 1))
				if len(left) > 1 {
					left_sexp = NewList(left).ToSexp()
				} else {
					left_sexp = left[0].ToSexp()
				}
				if len(right) > 1 {
					right_sexp = NewList(right).ToSexp()
				} else {
					right_sexp = right[0].ToSexp()
				}
				return (((("(semi " + left_sexp) + " (background ") + right_sexp) + "))")
			}
		}
		// No ; or \n found, background the whole list (minus trailing &)
		inner_parts = sublist(parts, 0, (len(parts) - 1))
		if len(inner_parts) == 1 {
			return (("(background " + inner_parts[0].(Node).ToSexp()) + ")")
		}
		inner_list = NewList(inner_parts)
		return (("(background " + inner_list.ToSexp()) + ")")
	}
	// Process by precedence: first split on ; and &, then on && and ||
	return l.toSexpWithPrecedence(parts, op_names)
}

func (l *List) toSexpWithPrecedence(parts []interface{}, op_names map[string]interface{}) string {
	// Process operators by precedence: ; (lowest), then &, then && and ||
	// Split on ; or \n first (rightmost for left-associativity)
	var left_sexp interface{}
	var left interface{}
	var right_sexp interface{}
	var right interface{}
	for i := (len(parts) - 2); i > 0; i-- {
		if (parts[i].(Node).GetKind() == "operator") && ((parts[i].(Node).Op == ';') || (parts[i].(Node).Op == '\n')) {
			left = sublist(parts, 0, i)
			right = sublist(parts, (i + 1), len(parts))
			if len(left) > 1 {
				left_sexp = NewList(left).ToSexp()
			} else {
				left_sexp = left[0].ToSexp()
			}
			if len(right) > 1 {
				right_sexp = NewList(right).ToSexp()
			} else {
				right_sexp = right[0].ToSexp()
			}
			return (((("(semi " + left_sexp) + " ") + right_sexp) + ")")
		}
	}
	// Then split on & (rightmost for left-associativity)
	for i := (len(parts) - 2); i > 0; i-- {
		if (parts[i].(Node).GetKind() == "operator") && (parts[i].(Node).Op == '&') {
			left = sublist(parts, 0, i)
			right = sublist(parts, (i + 1), len(parts))
			if len(left) > 1 {
				left_sexp = NewList(left).ToSexp()
			} else {
				left_sexp = left[0].ToSexp()
			}
			if len(right) > 1 {
				right_sexp = NewList(right).ToSexp()
			} else {
				right_sexp = right[0].ToSexp()
			}
			return (((("(background " + left_sexp) + " ") + right_sexp) + ")")
		}
	}
	// No ; or &, process high-prec ops (&&, ||) left-associatively
	result := parts[0].(Node).ToSexp()
	var op string
	var cmd Node
	var op_name interface{}
	for i := 1; i < (len(parts) - 1); i += 2 {
		op = parts[i].(Node)
		cmd = parts[(i + 1)].(Node)
		op_name = mapGet(op_names, op.Op, op.Op)
		result = (((((("(" + op_name) + " ") + result) + " ") + cmd.ToSexp()) + ")")
	}
	return result
}

type Operator struct {
	Op   string
	Kind string
}

func (o *Operator) GetKind() string {
	return o.Kind
}

func NewOperator(op string) *Operator {
	o := &Operator{}
	o.Kind = "operator"
	o.Op = op
	return o
}

func (o *Operator) ToSexp() string {
	names := map[string]interface{}{"&&": "and", "||": "or", ";": "semi", "&": "bg", "|": "pipe"}
	return (("(" + mapGet(names, o.Op, o.Op)) + ")")
}

type PipeBoth struct {
	Kind string
}

func (p *PipeBoth) GetKind() string {
	return p.Kind
}

func NewPipeBoth() *PipeBoth {
	p := &PipeBoth{}
	p.Kind = "pipe-both"
	return p
}

func (p *PipeBoth) ToSexp() string {
	return "(pipe-both)"
}

type Empty struct {
	Kind string
}

func (e *Empty) GetKind() string {
	return e.Kind
}

func NewEmpty() *Empty {
	e := &Empty{}
	e.Kind = "empty"
	return e
}

func (e *Empty) ToSexp() string {
	return ""
}

type Comment struct {
	Text string
	Kind string
}

func (c *Comment) GetKind() string {
	return c.Kind
}

func NewComment(text string) *Comment {
	c := &Comment{}
	c.Kind = "comment"
	c.Text = text
	return c
}

func (c *Comment) ToSexp() string {
	// bash-oracle doesn't output comments
	return ""
}

type Redirect struct {
	Op     string
	Target Word
	Fd     int
	Kind   string
}

func (r *Redirect) GetKind() string {
	return r.Kind
}

func NewRedirect(op string, target Word, fd *int) *Redirect {
	r := &Redirect{}
	r.Kind = "redirect"
	r.Op = op
	r.Target = target
	r.Fd = fd
	return r
}

func (r *Redirect) ToSexp() string {
	// Strip fd prefix from operator (e.g., "2>" -> ">", "{fd}>" -> ">")
	op := strings.TrimLeft(r.Op, "0123456789")
	// Strip {varname} prefix if present
	var j int
	if strings.HasPrefix(op, "{") {
		j = 1
		if (j < len(op)) && (isAlpha_h(string(op[j])) || (op[j] == '_')) {
			j += 1
			for (j < len(op)) && (isAlnum_h(string(op[j])) || (op[j] == '_')) {
				j += 1
			}
			if (j < len(op)) && (op[j] == '}') {
				op = substring(op, (j + 1), len(op))
			}
		}
	}
	target_val := r.Target.Value
	// Expand ANSI-C $'...' quotes (converts escapes like \n to actual newline)
	target_val = NewWord(target_val).expandAllAnsiCQuotes(target_val)
	// Strip $ from locale strings $"..."
	target_val = strings.ReplaceAll(target_val, "$\"", "\"")
	// For fd duplication, target starts with & (e.g., "&1", "&2", "&-")
	var fd_target interface{}
	if strings.HasPrefix(target_val, "&") {
		// Determine the real operator
		if op == '>' {
			op = ">&"
		} else if op == '<' {
			op = "<&"
		}
		fd_target = strings.TrimRight(substring(target_val, 1, len(target_val)), "-")
		if isDigit_h(fd_target) {
			return (((("(redirect \"" + op) + "\" ") + fd_target) + ")")
		} else if target_val == "&-" {
			return "(redirect \">&-\" 0)"
		} else {
			// Variable fd dup like >&$fd or >&$fd- (move) - strip the & and trailing -
			return (((("(redirect \"" + op) + "\" \"") + fd_target) + "\")")
		}
	}
	// Handle case where op is already >& or <&
	if (op == ">&") || (op == "<&") {
		if isDigit_h(target_val) {
			return (((("(redirect \"" + op) + "\" ") + target_val) + ")")
		}
		// Variable fd dup with move indicator (trailing -)
		target_val = strings.TrimRight(target_val, "-")
		return (((("(redirect \"" + op) + "\" \"") + target_val) + "\")")
	}
	return (((("(redirect \"" + op) + "\" \"") + target_val) + "\")")
}

type HereDoc struct {
	Delimiter string
	Content   string
	StripTabs bool
	Quoted    bool
	Fd        int
	Kind      string
}

func (h *HereDoc) GetKind() string {
	return h.Kind
}

func NewHereDoc(delimiter string, content string, strip_tabs bool, quoted bool, fd *int) *HereDoc {
	h := &HereDoc{}
	h.Kind = "heredoc"
	h.Delimiter = delimiter
	h.Content = content
	h.StripTabs = strip_tabs
	h.Quoted = quoted
	h.Fd = fd
	return h
}

func (h *HereDoc) ToSexp() string {
	var op string
	if h.StripTabs {
		op = "<<-"
	} else {
		op = "<<"
	}
	return (((("(redirect \"" + op) + "\" \"") + h.Content) + "\")")
}

type Subshell struct {
	Body      Node
	Redirects []Node
	Kind      string
}

func (s *Subshell) GetKind() string {
	return s.Kind
}

func NewSubshell(body Node, redirects []Node) *Subshell {
	s := &Subshell{}
	s.Kind = "subshell"
	s.Body = body
	s.Redirects = redirects
	return s
}

func (s *Subshell) ToSexp() string {
	base := (("(subshell " + s.Body.ToSexp()) + ")")
	var redirect_parts interface{}
	var r interface{}
	if s.Redirects {
		redirect_parts = []interface{}{}
		for _, r := range s.Redirects {
			redirect_parts = append(redirect_parts, r.ToSexp())
		}
		return ((base + " ") + strings.Join(redirect_parts, " "))
	}
	return base
}

type BraceGroup struct {
	Body      Node
	Redirects []Node
	Kind      string
}

func (b *BraceGroup) GetKind() string {
	return b.Kind
}

func NewBraceGroup(body Node, redirects []Node) *BraceGroup {
	b := &BraceGroup{}
	b.Kind = "brace-group"
	b.Body = body
	b.Redirects = redirects
	return b
}

func (b *BraceGroup) ToSexp() string {
	base := (("(brace-group " + b.Body.ToSexp()) + ")")
	var redirect_parts interface{}
	var r interface{}
	if b.Redirects {
		redirect_parts = []interface{}{}
		for _, r := range b.Redirects {
			redirect_parts = append(redirect_parts, r.ToSexp())
		}
		return ((base + " ") + strings.Join(redirect_parts, " "))
	}
	return base
}

type If struct {
	Condition Node
	ThenBody  Node
	ElseBody  Node
	Redirects []Node
	Kind      string
}

func (i *If) GetKind() string {
	return i.Kind
}

func NewIf(condition Node, then_body Node, else_body Node, redirects []Node) *If {
	i := &If{}
	i.Kind = "if"
	i.Condition = condition
	i.ThenBody = then_body
	i.ElseBody = else_body
	i.Redirects = redirects
	return i
}

func (i *If) ToSexp() string {
	result := ((("(if " + i.Condition.ToSexp()) + " ") + i.ThenBody.ToSexp())
	if i.ElseBody {
		result = ((result + " ") + i.ElseBody.ToSexp())
	}
	result = (result + ")")
	for _, r := range i.Redirects {
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

func (w *While) GetKind() string {
	return w.Kind
}

func NewWhile(condition Node, body Node, redirects []Node) *While {
	w := &While{}
	w.Kind = "while"
	w.Condition = condition
	w.Body = body
	w.Redirects = redirects
	return w
}

func (w *While) ToSexp() string {
	base := (((("(while " + w.Condition.ToSexp()) + " ") + w.Body.ToSexp()) + ")")
	var redirect_parts interface{}
	var r interface{}
	if w.Redirects {
		redirect_parts = []interface{}{}
		for _, r := range w.Redirects {
			redirect_parts = append(redirect_parts, r.ToSexp())
		}
		return ((base + " ") + strings.Join(redirect_parts, " "))
	}
	return base
}

type Until struct {
	Condition Node
	Body      Node
	Redirects []Node
	Kind      string
}

func (u *Until) GetKind() string {
	return u.Kind
}

func NewUntil(condition Node, body Node, redirects []Node) *Until {
	u := &Until{}
	u.Kind = "until"
	u.Condition = condition
	u.Body = body
	u.Redirects = redirects
	return u
}

func (u *Until) ToSexp() string {
	base := (((("(until " + u.Condition.ToSexp()) + " ") + u.Body.ToSexp()) + ")")
	var redirect_parts interface{}
	var r interface{}
	if u.Redirects {
		redirect_parts = []interface{}{}
		for _, r := range u.Redirects {
			redirect_parts = append(redirect_parts, r.ToSexp())
		}
		return ((base + " ") + strings.Join(redirect_parts, " "))
	}
	return base
}

type For struct {
	Var       string
	Words     []Node
	Body      Node
	Redirects []Node
	Kind      string
}

func (f *For) GetKind() string {
	return f.Kind
}

func NewFor(variable string, words []Node, body Node, redirects []Node) *For {
	f := &For{}
	f.Kind = "for"
	f.Var = variable
	f.Words = words
	f.Body = body
	f.Redirects = redirects
	return f
}

func (f *For) ToSexp() string {
	// bash-oracle format: (for (word "var") (in (word "a") ...) body)
	suffix := ""
	var redirect_parts interface{}
	var r interface{}
	if f.Redirects {
		redirect_parts = []interface{}{}
		for _, r := range f.Redirects {
			redirect_parts = append(redirect_parts, r.ToSexp())
		}
		suffix = (" " + strings.Join(redirect_parts, " "))
	}
	var_escaped := strings.ReplaceAll(strings.ReplaceAll(f.Var, "\\", "\\\\"), "\"", "\\\"")
	var w interface{}
	var word_parts interface{}
	var word_strs interface{}
	if f.Words == nil {
		// No 'in' clause - bash-oracle implies (in (word "\"$@\""))
		return ((((("(for (word \"" + var_escaped) + "\") (in (word \"\\\"$@\\\"\")) ") + f.Body.ToSexp()) + ")") + suffix)
	} else if len(f.Words) == 0 {
		// Empty 'in' clause - bash-oracle outputs (in)
		return ((((("(for (word \"" + var_escaped) + "\") (in) ") + f.Body.ToSexp()) + ")") + suffix)
	} else {
		word_parts = []interface{}{}
		for _, w := range f.Words {
			word_parts = append(word_parts, w.ToSexp())
		}
		word_strs = strings.Join(word_parts, " ")
		return ((((((("(for (word \"" + var_escaped) + "\") (in ") + word_strs) + ") ") + f.Body.ToSexp()) + ")") + suffix)
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

func (f *ForArith) GetKind() string {
	return f.Kind
}

func NewForArith(init string, cond string, incr string, body Node, redirects []Node) *ForArith {
	f := &ForArith{}
	f.Kind = "for-arith"
	f.Init = init
	f.Cond = cond
	f.Incr = incr
	f.Body = body
	f.Redirects = redirects
	return f
}

func (f *ForArith) ToSexp() string {
	// bash-oracle format: (arith-for (init (word "x")) (test (word "y")) (step (word "z")) body)
	FormatArithVal := func(s string) string {
		// Use Word's methods to expand ANSI-C quotes and strip locale $
		w := NewWord(s, []interface{}{})
		val := w.expandAllAnsiCQuotes(s)
		val = w.stripLocaleStringDollars(val)
		val = strings.ReplaceAll(strings.ReplaceAll(val, "\\", "\\\\"), "\"", "\\\"")
		return val
	}

	suffix := ""
	if f.Redirects {
		redirect_parts := []interface{}{}
		for _, r := range f.Redirects {
			redirect_parts = append(redirect_parts, r.ToSexp())
		}
		suffix = (" " + strings.Join(redirect_parts, " "))
	}
	var init_val interface{}
	if f.Init {
		init_val = f.Init
	} else {
		init_val = "1"
	}
	var cond_val interface{}
	if f.Cond {
		cond_val = normalizeFdRedirects(f.Cond)
	} else {
		cond_val = "1"
	}
	var incr_val interface{}
	if f.Incr {
		incr_val = f.Incr
	} else {
		incr_val = "1"
	}
	return ((((((((((("(arith-for (init (word \"" + FormatArithVal(init_val)) + "\")) ") + "(test (word \"") + FormatArithVal(cond_val)) + "\")) ") + "(step (word \"") + FormatArithVal(incr_val)) + "\")) ") + f.Body.ToSexp()) + ")") + suffix)
}

type Select struct {
	Var       string
	Words     []Node
	Body      Node
	Redirects []Node
	Kind      string
}

func (s *Select) GetKind() string {
	return s.Kind
}

func NewSelect(variable string, words []Node, body Node, redirects []Node) *Select {
	s := &Select{}
	s.Kind = "select"
	s.Var = variable
	s.Words = words
	s.Body = body
	s.Redirects = redirects
	return s
}

func (s *Select) ToSexp() string {
	// bash-oracle format: (select (word "var") (in (word "a") ...) body)
	suffix := ""
	var redirect_parts interface{}
	var r interface{}
	if s.Redirects {
		redirect_parts = []interface{}{}
		for _, r := range s.Redirects {
			redirect_parts = append(redirect_parts, r.ToSexp())
		}
		suffix = (" " + strings.Join(redirect_parts, " "))
	}
	var_escaped := strings.ReplaceAll(strings.ReplaceAll(s.Var, "\\", "\\\\"), "\"", "\\\"")
	var in_clause string
	var word_strs interface{}
	var w interface{}
	var word_parts interface{}
	if s.Words != nil {
		word_parts = []interface{}{}
		for _, w := range s.Words {
			word_parts = append(word_parts, w.ToSexp())
		}
		word_strs = strings.Join(word_parts, " ")
		if s.Words {
			in_clause = (("(in " + word_strs) + ")")
		} else {
			in_clause = "(in)"
		}
	} else {
		// No 'in' clause means implicit "$@"
		in_clause = "(in (word \"\\\"$@\\\"\"))"
	}
	return ((((((("(select (word \"" + var_escaped) + "\") ") + in_clause) + " ") + s.Body.ToSexp()) + ")") + suffix)
}

type Case struct {
	Word      Word
	Patterns  []Node
	Redirects []Node
	Kind      string
}

func (c *Case) GetKind() string {
	return c.Kind
}

func NewCase(word Word, patterns []Node, redirects []Node) *Case {
	c := &Case{}
	c.Kind = "case"
	c.Word = word
	c.Patterns = patterns
	c.Redirects = redirects
	return c
}

func (c *Case) ToSexp() string {
	parts := []interface{}{}
	parts = append(parts, ("(case " + c.Word.ToSexp()))
	for _, p := range c.Patterns {
		parts = append(parts, p.ToSexp())
	}
	base := (joinStrings(parts, " ") + ")")
	var redirect_parts interface{}
	var r interface{}
	if c.Redirects {
		redirect_parts = []interface{}{}
		for _, r := range c.Redirects {
			redirect_parts = append(redirect_parts, r.ToSexp())
		}
		return ((base + " ") + strings.Join(redirect_parts, " "))
	}
	return base
}

func consumeSingleQuote(s string, start int) []interface{} {
	chars := []interface{}{"'"}
	i := (start + 1)
	for (i < len(s)) && (s[i] != '\'') {
		chars = append(chars, s[i])
		i += 1
	}
	if i < len(s) {
		chars = append(chars, s[i])
		i += 1
	}
	return []interface{}{i, chars}
}

func consumeDoubleQuote(s string, start int) []interface{} {
	chars := []interface{}{"\""}
	i := (start + 1)
	for (i < len(s)) && (s[i] != '"') {
		if (s[i] == '\\') && ((i + 1) < len(s)) {
			chars = append(chars, s[i])
			i += 1
		}
		chars = append(chars, s[i])
		i += 1
	}
	if i < len(s) {
		chars = append(chars, s[i])
		i += 1
	}
	return []interface{}{i, chars}
}

func hasBracketClose(s string, start int, depth int) bool {
	i := start
	for i < len(s) {
		if s[i] == ']' {
			return true
		}
		if ((s[i] == '|') || (s[i] == ')')) && (depth == 0) {
			return false
		}
		i += 1
	}
	return false
}

func consumeBracketClass(s string, start int, depth int) []interface{} {
	// First scan to see if this is a valid bracket expression
	scan_pos := (start + 1)
	// Skip [! or [^ at start
	if (scan_pos < len(s)) && ((s[scan_pos] == '!') || (s[scan_pos] == '^')) {
		scan_pos += 1
	}
	// Handle ] as first char
	if (scan_pos < len(s)) && (s[scan_pos] == ']') {
		if hasBracketClose(s, (scan_pos + 1), depth) {
			scan_pos += 1
		}
	}
	// Scan for closing ]
	is_bracket := false
	for scan_pos < len(s) {
		if s[scan_pos] == ']' {
			is_bracket = true
			break
		}
		if (s[scan_pos] == ')') && (depth == 0) {
			break
		}
		scan_pos += 1
	}
	if !(is_bracket) {
		return []interface{}{(start + 1), []interface{}{"["}, false}
	}
	// Valid bracket - consume it
	chars := []interface{}{"["}
	i := (start + 1)
	// Handle [! or [^
	if (i < len(s)) && ((s[i] == '!') || (s[i] == '^')) {
		chars = append(chars, s[i])
		i += 1
	}
	// Handle ] as first char
	if (i < len(s)) && (s[i] == ']') {
		if hasBracketClose(s, (i + 1), depth) {
			chars = append(chars, s[i])
			i += 1
		}
	}
	// Consume until ]
	for (i < len(s)) && (s[i] != ']') {
		chars = append(chars, s[i])
		i += 1
	}
	if i < len(s) {
		chars = append(chars, s[i])
		i += 1
	}
	return []interface{}{i, chars, true}
}

type CasePattern struct {
	Pattern    string
	Body       Node
	Terminator string
	Kind       string
}

func (c *CasePattern) GetKind() string {
	return c.Kind
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
	// bash-oracle format: (pattern ((word "a") (word "b")) body)
	// Split pattern by | respecting escapes, extglobs, quotes, and brackets
	alternatives := []interface{}{}
	current := []interface{}{}
	i := 0
	depth := 0
	for i < len(c.Pattern) {
		ch := c.Pattern[i]
		var result interface{}
		if (ch == '\\') && ((i + 1) < len(c.Pattern)) {
			current = append(current, substring(c.Pattern, i, (i+2)))
			i += 2
		} else if ((ch == '@') || (ch == '?') || (ch == '*') || (ch == '+') || (ch == '!')) && ((i + 1) < len(c.Pattern)) && (c.Pattern[(i+1)] == '(') {
			// Start of extglob: @(, ?(, *(, +(, !(
			current = append(current, ch)
			current = append(current, "(")
			depth += 1
			i += 2
		} else if (ch == '$') && ((i + 1) < len(c.Pattern)) && (c.Pattern[(i+1)] == '(') {
			// $( command sub or $(( arithmetic - track depth
			current = append(current, ch)
			current = append(current, "(")
			depth += 1
			i += 2
		} else if (ch == '(') && (depth > 0) {
			current = append(current, ch)
			depth += 1
			i += 1
		} else if (ch == ')') && (depth > 0) {
			current = append(current, ch)
			depth -= 1
			i += 1
		} else if ch == '[' {
			result = consumeBracketClass(c.Pattern, i, depth)
			i = result[0]
			current = append(current, result[1]...)
		} else if (ch == '\'') && (depth == 0) {
			result = consumeSingleQuote(c.Pattern, i)
			i = result[0]
			current = append(current, result[1]...)
		} else if (ch == '"') && (depth == 0) {
			result = consumeDoubleQuote(c.Pattern, i)
			i = result[0]
			current = append(current, result[1]...)
		} else if (ch == '|') && (depth == 0) {
			alternatives = append(alternatives, strings.Join(current, ""))
			current = []interface{}{}
			i += 1
		} else {
			current = append(current, ch)
			i += 1
		}
	}
	alternatives = append(alternatives, strings.Join(current, ""))
	word_list := []interface{}{}
	for _, alt := range alternatives {
		// Use Word.to_sexp() to properly expand ANSI-C quotes and escape
		word_list = append(word_list, NewWord(alt).ToSexp())
	}
	pattern_str := strings.Join(word_list, " ")
	parts := []interface{}{(("(pattern (" + pattern_str) + ")")}
	if c.Body {
		parts = append(parts, (" " + c.Body.ToSexp()))
	} else {
		parts = append(parts, " ()")
	}
	// bash-oracle doesn't output fallthrough/falltest markers
	parts = append(parts, ")")
	return joinStrings(parts, "")
}

type Function struct {
	Name string
	Body Node
	Kind string
}

func (f *Function) GetKind() string {
	return f.Kind
}

func NewFunction(name string, body Node) *Function {
	f := &Function{}
	f.Kind = "function"
	f.Name = name
	f.Body = body
	return f
}

func (f *Function) ToSexp() string {
	return (((("(function \"" + f.Name) + "\" ") + f.Body.ToSexp()) + ")")
}

type ParamExpansion struct {
	Param string
	Op    string
	Arg   string
	Kind  string
}

func (p *ParamExpansion) GetKind() string {
	return p.Kind
}

func NewParamExpansion(param string, op *string, arg *string) *ParamExpansion {
	p := &ParamExpansion{}
	p.Kind = "param"
	p.Param = param
	p.Op = op
	p.Arg = arg
	return p
}

func (p *ParamExpansion) ToSexp() string {
	escaped_param := strings.ReplaceAll(strings.ReplaceAll(p.Param, "\\", "\\\\"), "\"", "\\\"")
	var arg_val interface{}
	var escaped_op interface{}
	var escaped_arg interface{}
	if p.Op != nil {
		escaped_op = strings.ReplaceAll(strings.ReplaceAll(p.Op, "\\", "\\\\"), "\"", "\\\"")
		if p.Arg != nil {
			arg_val = p.Arg
		} else {
			arg_val = ""
		}
		escaped_arg = strings.ReplaceAll(strings.ReplaceAll(arg_val, "\\", "\\\\"), "\"", "\\\"")
		return (((((("(param \"" + escaped_param) + "\" \"") + escaped_op) + "\" \"") + escaped_arg) + "\")")
	}
	return (("(param \"" + escaped_param) + "\")")
}

type ParamLength struct {
	Param string
	Kind  string
}

func (p *ParamLength) GetKind() string {
	return p.Kind
}

func NewParamLength(param string) *ParamLength {
	p := &ParamLength{}
	p.Kind = "param-len"
	p.Param = param
	return p
}

func (p *ParamLength) ToSexp() string {
	escaped := strings.ReplaceAll(strings.ReplaceAll(p.Param, "\\", "\\\\"), "\"", "\\\"")
	return (("(param-len \"" + escaped) + "\")")
}

type ParamIndirect struct {
	Param string
	Op    string
	Arg   string
	Kind  string
}

func (p *ParamIndirect) GetKind() string {
	return p.Kind
}

func NewParamIndirect(param string, op *string, arg *string) *ParamIndirect {
	p := &ParamIndirect{}
	p.Kind = "param-indirect"
	p.Param = param
	p.Op = op
	p.Arg = arg
	return p
}

func (p *ParamIndirect) ToSexp() string {
	escaped := strings.ReplaceAll(strings.ReplaceAll(p.Param, "\\", "\\\\"), "\"", "\\\"")
	var arg_val interface{}
	var escaped_op interface{}
	var escaped_arg interface{}
	if p.Op != nil {
		escaped_op = strings.ReplaceAll(strings.ReplaceAll(p.Op, "\\", "\\\\"), "\"", "\\\"")
		if p.Arg != nil {
			arg_val = p.Arg
		} else {
			arg_val = ""
		}
		escaped_arg = strings.ReplaceAll(strings.ReplaceAll(arg_val, "\\", "\\\\"), "\"", "\\\"")
		return (((((("(param-indirect \"" + escaped) + "\" \"") + escaped_op) + "\" \"") + escaped_arg) + "\")")
	}
	return (("(param-indirect \"" + escaped) + "\")")
}

type CommandSubstitution struct {
	Command Node
	Kind    string
}

func (c *CommandSubstitution) GetKind() string {
	return c.Kind
}

func NewCommandSubstitution(command Node) *CommandSubstitution {
	c := &CommandSubstitution{}
	c.Kind = "cmdsub"
	c.Command = command
	return c
}

func (c *CommandSubstitution) ToSexp() string {
	return (("(cmdsub " + c.Command.ToSexp()) + ")")
}

type ArithmeticExpansion struct {
	Expression Node
	Kind       string
}

func (a *ArithmeticExpansion) GetKind() string {
	return a.Kind
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
	return (("(arith " + a.Expression.ToSexp()) + ")")
}

type ArithmeticCommand struct {
	Expression Node
	Redirects  []Node
	RawContent string
	Kind       string
}

func (a *ArithmeticCommand) GetKind() string {
	return a.Kind
}

func NewArithmeticCommand(expression Node, redirects []Node, raw_content string) *ArithmeticCommand {
	a := &ArithmeticCommand{}
	a.Kind = "arith-cmd"
	a.Expression = expression
	a.Redirects = redirects
	a.RawContent = raw_content
	return a
}

func (a *ArithmeticCommand) ToSexp() string {
	// bash-oracle format: (arith (word "content"))
	// Redirects are siblings: (arith (word "...")) (redirect ...)
	escaped := strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(a.RawContent, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n")
	result := (("(arith (word \"" + escaped) + "\"))")
	var redirect_sexps interface{}
	var redirect_parts interface{}
	var r interface{}
	if a.Redirects {
		redirect_parts = []interface{}{}
		for _, r := range a.Redirects {
			redirect_parts = append(redirect_parts, r.ToSexp())
		}
		redirect_sexps = strings.Join(redirect_parts, " ")
		return ((result + " ") + redirect_sexps)
	}
	return result
}

// Arithmetic expression nodes
type ArithNumber struct {
	Value string
	Kind  string
}

func (a *ArithNumber) GetKind() string {
	return a.Kind
}

func NewArithNumber(value string) *ArithNumber {
	a := &ArithNumber{}
	a.Kind = "number"
	a.Value = value
	return a
}

func (a *ArithNumber) ToSexp() string {
	return (("(number \"" + a.Value) + "\")")
}

type ArithVar struct {
	Name string
	Kind string
}

func (a *ArithVar) GetKind() string {
	return a.Kind
}

func NewArithVar(name string) *ArithVar {
	a := &ArithVar{}
	a.Kind = "var"
	a.Name = name
	return a
}

func (a *ArithVar) ToSexp() string {
	return (("(var \"" + a.Name) + "\")")
}

type ArithBinaryOp struct {
	Op    string
	Left  Node
	Right Node
	Kind  string
}

func (a *ArithBinaryOp) GetKind() string {
	return a.Kind
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
	return (((((("(binary-op \"" + a.Op) + "\" ") + a.Left.ToSexp()) + " ") + a.Right.ToSexp()) + ")")
}

type ArithUnaryOp struct {
	Op      string
	Operand Node
	Kind    string
}

func (a *ArithUnaryOp) GetKind() string {
	return a.Kind
}

func NewArithUnaryOp(op string, operand Node) *ArithUnaryOp {
	a := &ArithUnaryOp{}
	a.Kind = "unary-op"
	a.Op = op
	a.Operand = operand
	return a
}

func (a *ArithUnaryOp) ToSexp() string {
	return (((("(unary-op \"" + a.Op) + "\" ") + a.Operand.ToSexp()) + ")")
}

type ArithPreIncr struct {
	Operand Node
	Kind    string
}

func (a *ArithPreIncr) GetKind() string {
	return a.Kind
}

func NewArithPreIncr(operand Node) *ArithPreIncr {
	a := &ArithPreIncr{}
	a.Kind = "pre-incr"
	a.Operand = operand
	return a
}

func (a *ArithPreIncr) ToSexp() string {
	return (("(pre-incr " + a.Operand.ToSexp()) + ")")
}

type ArithPostIncr struct {
	Operand Node
	Kind    string
}

func (a *ArithPostIncr) GetKind() string {
	return a.Kind
}

func NewArithPostIncr(operand Node) *ArithPostIncr {
	a := &ArithPostIncr{}
	a.Kind = "post-incr"
	a.Operand = operand
	return a
}

func (a *ArithPostIncr) ToSexp() string {
	return (("(post-incr " + a.Operand.ToSexp()) + ")")
}

type ArithPreDecr struct {
	Operand Node
	Kind    string
}

func (a *ArithPreDecr) GetKind() string {
	return a.Kind
}

func NewArithPreDecr(operand Node) *ArithPreDecr {
	a := &ArithPreDecr{}
	a.Kind = "pre-decr"
	a.Operand = operand
	return a
}

func (a *ArithPreDecr) ToSexp() string {
	return (("(pre-decr " + a.Operand.ToSexp()) + ")")
}

type ArithPostDecr struct {
	Operand Node
	Kind    string
}

func (a *ArithPostDecr) GetKind() string {
	return a.Kind
}

func NewArithPostDecr(operand Node) *ArithPostDecr {
	a := &ArithPostDecr{}
	a.Kind = "post-decr"
	a.Operand = operand
	return a
}

func (a *ArithPostDecr) ToSexp() string {
	return (("(post-decr " + a.Operand.ToSexp()) + ")")
}

type ArithAssign struct {
	Op     string
	Target Node
	Value  Node
	Kind   string
}

func (a *ArithAssign) GetKind() string {
	return a.Kind
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
	return (((((("(assign \"" + a.Op) + "\" ") + a.Target.ToSexp()) + " ") + a.Value.ToSexp()) + ")")
}

type ArithTernary struct {
	Condition Node
	IfTrue    Node
	IfFalse   Node
	Kind      string
}

func (a *ArithTernary) GetKind() string {
	return a.Kind
}

func NewArithTernary(condition Node, if_true Node, if_false Node) *ArithTernary {
	a := &ArithTernary{}
	a.Kind = "ternary"
	a.Condition = condition
	a.IfTrue = if_true
	a.IfFalse = if_false
	return a
}

func (a *ArithTernary) ToSexp() string {
	return (((((("(ternary " + a.Condition.ToSexp()) + " ") + a.IfTrue.ToSexp()) + " ") + a.IfFalse.ToSexp()) + ")")
}

type ArithComma struct {
	Left  Node
	Right Node
	Kind  string
}

func (a *ArithComma) GetKind() string {
	return a.Kind
}

func NewArithComma(left Node, right Node) *ArithComma {
	a := &ArithComma{}
	a.Kind = "comma"
	a.Left = left
	a.Right = right
	return a
}

func (a *ArithComma) ToSexp() string {
	return (((("(comma " + a.Left.ToSexp()) + " ") + a.Right.ToSexp()) + ")")
}

type ArithSubscript struct {
	Array string
	Index Node
	Kind  string
}

func (a *ArithSubscript) GetKind() string {
	return a.Kind
}

func NewArithSubscript(array string, index Node) *ArithSubscript {
	a := &ArithSubscript{}
	a.Kind = "subscript"
	a.Array = array
	a.Index = index
	return a
}

func (a *ArithSubscript) ToSexp() string {
	return (((("(subscript \"" + a.Array) + "\" ") + a.Index.ToSexp()) + ")")
}

type ArithEscape struct {
	Char string
	Kind string
}

func (a *ArithEscape) GetKind() string {
	return a.Kind
}

func NewArithEscape(char string) *ArithEscape {
	a := &ArithEscape{}
	a.Kind = "escape"
	a.Char = char
	return a
}

func (a *ArithEscape) ToSexp() string {
	return (("(escape \"" + a.Char) + "\")")
}

type ArithDeprecated struct {
	Expression string
	Kind       string
}

func (a *ArithDeprecated) GetKind() string {
	return a.Kind
}

func NewArithDeprecated(expression string) *ArithDeprecated {
	a := &ArithDeprecated{}
	a.Kind = "arith-deprecated"
	a.Expression = expression
	return a
}

func (a *ArithDeprecated) ToSexp() string {
	escaped := strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(a.Expression, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n")
	return (("(arith-deprecated \"" + escaped) + "\")")
}

type AnsiCQuote struct {
	Content string
	Kind    string
}

func (a *AnsiCQuote) GetKind() string {
	return a.Kind
}

func NewAnsiCQuote(content string) *AnsiCQuote {
	a := &AnsiCQuote{}
	a.Kind = "ansi-c"
	a.Content = content
	return a
}

func (a *AnsiCQuote) ToSexp() string {
	escaped := strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(a.Content, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n")
	return (("(ansi-c \"" + escaped) + "\")")
}

type LocaleString struct {
	Content string
	Kind    string
}

func (l *LocaleString) GetKind() string {
	return l.Kind
}

func NewLocaleString(content string) *LocaleString {
	l := &LocaleString{}
	l.Kind = "locale"
	l.Content = content
	return l
}

func (l *LocaleString) ToSexp() string {
	escaped := strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(l.Content, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n")
	return (("(locale \"" + escaped) + "\")")
}

type ProcessSubstitution struct {
	Direction string
	Command   Node
	Kind      string
}

func (p *ProcessSubstitution) GetKind() string {
	return p.Kind
}

func NewProcessSubstitution(direction string, command Node) *ProcessSubstitution {
	p := &ProcessSubstitution{}
	p.Kind = "procsub"
	p.Direction = direction
	p.Command = command
	return p
}

func (p *ProcessSubstitution) ToSexp() string {
	return (((("(procsub \"" + p.Direction) + "\" ") + p.Command.ToSexp()) + ")")
}

type Negation struct {
	Pipeline Node
	Kind     string
}

func (n *Negation) GetKind() string {
	return n.Kind
}

func NewNegation(pipeline Node) *Negation {
	n := &Negation{}
	n.Kind = "negation"
	n.Pipeline = pipeline
	return n
}

func (n *Negation) ToSexp() string {
	if n.Pipeline == nil {
		// Bare "!" with no command - bash-oracle shows empty command
		return "(negation (command))"
	}
	return (("(negation " + n.Pipeline.ToSexp()) + ")")
}

type Time struct {
	Pipeline Node
	Posix    bool
	Kind     string
}

func (t *Time) GetKind() string {
	return t.Kind
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
		// Bare "time" with no command - bash-oracle shows empty command
		if t.Posix {
			return "(time -p (command))"
		} else {
			return "(time (command))"
		}
	}
	if t.Posix {
		return (("(time -p " + t.Pipeline.ToSexp()) + ")")
	}
	return (("(time " + t.Pipeline.ToSexp()) + ")")
}

type ConditionalExpr struct {
	Body      Node
	Redirects []Node
	Kind      string
}

func (c *ConditionalExpr) GetKind() string {
	return c.Kind
}

func NewConditionalExpr(body Node, redirects []Node) *ConditionalExpr {
	c := &ConditionalExpr{}
	c.Kind = "cond-expr"
	c.Body = body
	c.Redirects = redirects
	return c
}

func (c *ConditionalExpr) ToSexp() string {
	// bash-oracle format: (cond ...) not (cond-expr ...)
	// Redirects are siblings, not children: (cond ...) (redirect ...)
	body_kind := getAttr(c.Body, "kind", nil)
	var result int
	var escaped interface{}
	if body_kind == nil {
		// body is a string
		escaped = strings.ReplaceAll(strings.ReplaceAll(strings.ReplaceAll(c.Body, "\\", "\\\\"), "\"", "\\\""), "\n", "\\n")
		result = (("(cond \"" + escaped) + "\")")
	} else {
		result = (("(cond " + c.Body.ToSexp()) + ")")
	}
	var redirect_sexps interface{}
	var redirect_parts interface{}
	var r interface{}
	if c.Redirects {
		redirect_parts = []interface{}{}
		for _, r := range c.Redirects {
			redirect_parts = append(redirect_parts, r.ToSexp())
		}
		redirect_sexps = strings.Join(redirect_parts, " ")
		return ((result + " ") + redirect_sexps)
	}
	return result
}

type UnaryTest struct {
	Op      string
	Operand Word
	Kind    string
}

func (u *UnaryTest) GetKind() string {
	return u.Kind
}

func NewUnaryTest(op string, operand Word) *UnaryTest {
	u := &UnaryTest{}
	u.Kind = "unary-test"
	u.Op = op
	u.Operand = operand
	return u
}

func (u *UnaryTest) ToSexp() string {
	// bash-oracle format: (cond-unary "-f" (cond-term "file"))
	// cond-term preserves content as-is (no backslash escaping)
	return (((("(cond-unary \"" + u.Op) + "\" (cond-term \"") + u.Operand.Value) + "\"))")
}

type BinaryTest struct {
	Op    string
	Left  Word
	Right Word
	Kind  string
}

func (b *BinaryTest) GetKind() string {
	return b.Kind
}

func NewBinaryTest(op string, left Word, right Word) *BinaryTest {
	b := &BinaryTest{}
	b.Kind = "binary-test"
	b.Op = op
	b.Left = left
	b.Right = right
	return b
}

func (b *BinaryTest) ToSexp() string {
	// bash-oracle format: (cond-binary "==" (cond-term "x") (cond-term "y"))
	// cond-term preserves content as-is (no backslash escaping)
	left_val := b.Left.GetCondFormattedValue()
	right_val := b.Right.GetCondFormattedValue()
	return (((((("(cond-binary \"" + b.Op) + "\" (cond-term \"") + left_val) + "\") (cond-term \"") + right_val) + "\"))")
}

type CondAnd struct {
	Left  Node
	Right Node
	Kind  string
}

func (c *CondAnd) GetKind() string {
	return c.Kind
}

func NewCondAnd(left Node, right Node) *CondAnd {
	c := &CondAnd{}
	c.Kind = "cond-and"
	c.Left = left
	c.Right = right
	return c
}

func (c *CondAnd) ToSexp() string {
	return (((("(cond-and " + c.Left.ToSexp()) + " ") + c.Right.ToSexp()) + ")")
}

type CondOr struct {
	Left  Node
	Right Node
	Kind  string
}

func (c *CondOr) GetKind() string {
	return c.Kind
}

func NewCondOr(left Node, right Node) *CondOr {
	c := &CondOr{}
	c.Kind = "cond-or"
	c.Left = left
	c.Right = right
	return c
}

func (c *CondOr) ToSexp() string {
	return (((("(cond-or " + c.Left.ToSexp()) + " ") + c.Right.ToSexp()) + ")")
}

type CondNot struct {
	Operand Node
	Kind    string
}

func (c *CondNot) GetKind() string {
	return c.Kind
}

func NewCondNot(operand Node) *CondNot {
	c := &CondNot{}
	c.Kind = "cond-not"
	c.Operand = operand
	return c
}

func (c *CondNot) ToSexp() string {
	// bash-oracle ignores negation - just output the operand
	return c.Operand.ToSexp()
}

type CondParen struct {
	Inner Node
	Kind  string
}

func (c *CondParen) GetKind() string {
	return c.Kind
}

func NewCondParen(inner Node) *CondParen {
	c := &CondParen{}
	c.Kind = "cond-paren"
	c.Inner = inner
	return c
}

func (c *CondParen) ToSexp() string {
	return (("(cond-expr " + c.Inner.ToSexp()) + ")")
}

type Array struct {
	Elements []Node
	Kind     string
}

func (a *Array) GetKind() string {
	return a.Kind
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
	parts := []interface{}{}
	for _, e := range a.Elements {
		parts = append(parts, e.ToSexp())
	}
	inner := joinStrings(parts, " ")
	return (("(array " + inner) + ")")
}

type Coproc struct {
	Command Node
	Name    string
	Kind    string
}

func (c *Coproc) GetKind() string {
	return c.Kind
}

func NewCoproc(command Node, name *string) *Coproc {
	c := &Coproc{}
	c.Kind = "coproc"
	c.Command = command
	c.Name = name
	return c
}

func (c *Coproc) ToSexp() string {
	// Use provided name for compound commands, "COPROC" for simple commands
	var name interface{}
	if c.Name {
		name = c.Name
	} else {
		name = "COPROC"
	}
	return (((("(coproc \"" + name) + "\" ") + c.Command.ToSexp()) + ")")
}

func formatCmdsubNode(node Node, indent int, in_procsub bool) string {
	if indent == nil {
		indent = 0
	}
	if in_procsub == nil {
		in_procsub = false
	}
	sp := repeatStr(" ", indent)
	inner_sp := repeatStr(" ", (indent + 4))
	if node.GetKind() == "empty" {
		return ""
	}
	var w interface{}
	var val interface{}
	var r interface{}
	if node.GetKind() == "command" {
		parts := []interface{}{}
		for _, w := range node.Words {
			val = w.expandAllAnsiCQuotes(w.Value)
			val = w.formatCommandSubstitutions(val)
			parts = append(parts, val)
		}
		for _, r := range node.Redirects {
			parts = append(parts, formatRedirect(r))
		}
		return joinStrings(parts, " ")
	}
	var cmd_parts interface{}
	var cmd Node
	if node.GetKind() == "pipeline" {
		cmd_parts = []interface{}{}
		for _, cmd := range node.Commands {
			cmd_parts = append(cmd_parts, formatCmdsubNode(cmd, indent, false))
		}
		return strings.Join(cmd_parts, " | ")
	}
	var p interface{}
	var s interface{}
	if node.GetKind() == "list" {
		// Join commands with operators
		result := []interface{}{}
		for _, p := range node.Parts {
			if p.GetKind() == "operator" {
				if p.Op == ';' {
					result = append(result, ";")
				} else if p.Op == '\n' {
					// Skip newline if it follows a semicolon (redundant separator)
					if (len(result) > 0) && (result[(len(result)-1)] == ';') {
						continue
					}
					result = append(result, "\n")
				} else if p.Op == '&' {
					result = append(result, " &")
				} else {
					result = append(result, (" " + p.Op))
				}
			} else {
				if (len(result) > 0) && !(strings.HasSuffix(result[(len(result)-1)], []interface{}{" ", "\n"})) {
					result = append(result, " ")
				}
				result = append(result, formatCmdsubNode(p, indent, false))
			}
		}
		// Strip trailing ; or newline
		s = joinStrings(result, "")
		for strings.HasSuffix(s, ";") || strings.HasSuffix(s, "\n") {
			s = substring(s, 0, (len(s) - 1))
		}
		return s
	}
	var else_body interface{}
	var cond interface{}
	var then_body interface{}
	if node.GetKind() == "if" {
		cond = formatCmdsubNode(node.Condition, indent, false)
		then_body = formatCmdsubNode(node.ThenBody, (indent + 4), false)
		result = ((((("if " + cond) + "; then\n") + inner_sp) + then_body) + ";")
		if node.ElseBody {
			else_body = formatCmdsubNode(node.ElseBody, (indent + 4), false)
			result = ((((((result + "\n") + sp) + "else\n") + inner_sp) + else_body) + ";")
		}
		result = (((result + "\n") + sp) + "fi")
		return result
	}
	var body interface{}
	if node.GetKind() == "while" {
		cond = formatCmdsubNode(node.Condition, indent, false)
		body = formatCmdsubNode(node.Body, (indent + 4), false)
		return ((((((("while " + cond) + "; do\n") + inner_sp) + body) + ";\n") + sp) + "done")
	}
	if node.GetKind() == "until" {
		cond = formatCmdsubNode(node.Condition, indent, false)
		body = formatCmdsubNode(node.Body, (indent + 4), false)
		return ((((((("until " + cond) + "; do\n") + inner_sp) + body) + ";\n") + sp) + "done")
	}
	var word_vals interface{}
	var variable interface{}
	var words []Node
	if node.GetKind() == "for" {
		variable = node.Var
		body = formatCmdsubNode(node.Body, (indent + 4), false)
		if node.Words {
			word_vals = []interface{}{}
			for _, w := range node.Words {
				word_vals = append(word_vals, w.Value)
			}
			words = strings.Join(word_vals, " ")
			return ((((((((("for " + variable) + " in ") + words) + ";\ndo\n") + inner_sp) + body) + ";\n") + sp) + "done")
		}
		return ((((((("for " + variable) + ";\ndo\n") + inner_sp) + body) + ";\n") + sp) + "done")
	}
	var patterns interface{}
	var pat_indent interface{}
	var word Node
	var term interface{}
	var pattern_str interface{}
	var term_indent interface{}
	var pat interface{}
	if node.GetKind() == "case" {
		word = node.Word.Value
		patterns = []interface{}{}
		i := 0
		for i < len(node.Patterns) {
			p = node.Patterns[i]
			pat = strings.ReplaceAll(p.Pattern, "|", " | ")
			if p.Body {
				body = formatCmdsubNode(p.Body, (indent + 8), false)
			} else {
				body = ""
			}
			term = p.Terminator
			pat_indent = repeatStr(" ", (indent + 8))
			term_indent = repeatStr(" ", (indent + 4))
			if i == 0 {
				// First pattern on same line as 'in'
				patterns = append(patterns, (((((((" " + pat) + ")\n") + pat_indent) + body) + "\n") + term_indent) + term))
			} else {
				patterns = append(patterns, ((((((pat + ")\n") + pat_indent) + body) + "\n") + term_indent) + term))
			}
			i += 1
		}
		pattern_str = strings.Join(patterns, ("\n" + repeatStr(" ", (indent+4))))
		return (((((("case " + word) + " in") + pattern_str) + "\n") + sp) + "esac")
	}
	var name string
	if node.GetKind() == "function" {
		name = node.Name
		// Get the body content - if it's a BraceGroup, unwrap it
		if node.Body.GetKind() == "brace-group" {
			body = formatCmdsubNode(node.Body.Body, (indent + 4), false)
		} else {
			body = formatCmdsubNode(node.Body, (indent + 4), false)
		}
		body = strings.TrimRight(body, ";")
		return ((((("function " + name) + " () \n{ \n") + inner_sp) + body) + "\n}")
	}
	var redirect_parts interface{}
	var redirects interface{}
	if node.GetKind() == "subshell" {
		body = formatCmdsubNode(node.Body, indent, in_procsub)
		redirects = ""
		if node.Redirects {
			redirect_parts = []interface{}{}
			for _, r := range node.Redirects {
				redirect_parts = append(redirect_parts, formatRedirect(r))
			}
			redirects = strings.Join(redirect_parts, " ")
		}
		if in_procsub {
			if redirects {
				return ((("(" + body) + ") ") + redirects)
			}
			return (("(" + body) + ")")
		}
		if redirects {
			return ((("( " + body) + " ) ") + redirects)
		}
		return (("( " + body) + " )")
	}
	if node.GetKind() == "brace-group" {
		body = formatCmdsubNode(node.Body, indent, false)
		body = strings.TrimRight(body, ";")
		return (("{ " + body) + "; }")
	}
	if node.GetKind() == "arith-cmd" {
		return (("((" + node.RawContent) + "))")
	}
	// Fallback: return empty for unknown types
	return ""
}

func formatRedirect(r Node) string {
	var op string
	var delim interface{}
	if r.GetKind() == "heredoc" {
		// Include heredoc content: <<DELIM\ncontent\nDELIM\n
		if r.StripTabs {
			op = "<<-"
		} else {
			op = "<<"
		}
		if r.Quoted {
			delim = (("'" + r.Delimiter) + "'")
		} else {
			delim = r.Delimiter
		}
		return (((((op + delim) + "\n") + r.Content) + r.Delimiter) + "\n")
	}
	op = r.Op
	target := r.Target.Value
	// For fd duplication (target starts with &), handle normalization
	if strings.HasPrefix(target, "&") {
		// Normalize N<&- to N>&- (close always uses >)
		if (target == "&-") && strings.HasSuffix(op, "<") {
			op = (substring(op, 0, (len(op)-1)) + ">")
		}
		// Add default fd for bare >&N or <&N
		if op == '>' {
			op = "1>"
		} else if op == '<' {
			op = "0<"
		}
		return (op + target)
	}
	return ((op + " ") + target)
}

func normalizeFdRedirects(s string) string {
	// Match >&N or <&N not preceded by a digit, add default fd
	result := []interface{}{}
	i := 0
	for i < len(s) {
		// Check for >&N or <&N
		var prev_is_digit interface{}
		if ((i + 2) < len(s)) && (s[(i+1)] == '&') && isDigit_h(string(s[(i+2)])) {
			prev_is_digit = ((i > 0) && isDigit_h(string(s[(i-1)])))
			if (s[i] == '>') && !(prev_is_digit) {
				result = append(result, "1>&")
				result = append(result, s[(i+2)])
				i += 3
				continue
			} else if (s[i] == '<') && !(prev_is_digit) {
				result = append(result, "0<&")
				result = append(result, s[(i+2)])
				i += 3
				continue
			}
		}
		result = append(result, s[i])
		i += 1
	}
	return joinStrings(result, "")
}

func findCmdsubEnd(value string, start int) int {
	depth := 1
	i := start
	in_single := false
	in_double := false
	case_depth := 0
	in_case_patterns := false
	for (i < len(value)) && (depth > 0) {
		c := value[i]
		// Handle escapes
		if (c == '\\') && ((i + 1) < len(value)) && !(in_single) {
			i += 2
			continue
		}
		// Handle quotes
		if (c == '\'') && !(in_double) {
			in_single = !(in_single)
			i += 1
			continue
		}
		if (c == '"') && !(in_single) {
			in_double = !(in_double)
			i += 1
			continue
		}
		if in_single {
			i += 1
			continue
		}
		var j int
		if in_double {
			// Inside double quotes, $() command substitution is still active
			if startsWithAt(value, i, "$(") && !(startsWithAt(value, i, "$((")) {
				// Recursively find end of nested command substitution
				j = findCmdsubEnd(value, (i + 2))
				i = j
				continue
			}
			// Skip other characters inside double quotes
			i += 1
			continue
		}
		// Handle comments - skip from # to end of line
		// Only treat # as comment if preceded by whitespace or at start
		if (c == '#') && ((i == start) || (value[(i-1)] == ' ') || (value[(i-1)] == '\t') || (value[(i-1)] == '\n') || (value[(i-1)] == ';') || (value[(i-1)] == '|') || (value[(i-1)] == '&') || (value[(i-1)] == '(') || (value[(i-1)] == ')')) {
			for (i < len(value)) && (value[i] != '\n') {
				i += 1
			}
			continue
		}
		// Handle heredocs
		if startsWithAt(value, i, "<<") {
			i = skipHeredoc(value, i)
			continue
		}
		// Check for 'case' keyword
		if startsWithAt(value, i, "case") && isWordBoundary(value, i, 4) {
			case_depth += 1
			in_case_patterns = false
			i += 4
			continue
		}
		// Check for 'in' keyword (after case)
		if (case_depth > 0) && startsWithAt(value, i, "in") && isWordBoundary(value, i, 2) {
			in_case_patterns = true
			i += 2
			continue
		}
		// Check for 'esac' keyword
		if startsWithAt(value, i, "esac") && isWordBoundary(value, i, 4) {
			if case_depth > 0 {
				case_depth -= 1
				in_case_patterns = false
			}
			i += 4
			continue
		}
		// Check for ';;' (end of case pattern, next pattern or esac follows)
		if startsWithAt(value, i, ";;") {
			i += 2
			continue
		}
		// Handle parens
		if c == '(' {
			depth += 1
		} else if c == ')' {
			// In case patterns, ) after pattern name is not a grouping paren
			if in_case_patterns && (case_depth > 0) {
				// This ) is a case pattern terminator, skip it
			} else {
				depth -= 1
			}
		}
		i += 1
	}
	return i
}

func skipHeredoc(value string, start int) int {
	i := (start + 2)
	// Handle <<- (strip tabs)
	if (i < len(value)) && (value[i] == '-') {
		i += 1
	}
	// Skip whitespace before delimiter
	for (i < len(value)) && isWhitespaceNoNewline(value[i]) {
		i += 1
	}
	// Extract delimiter - may be quoted
	delim_start := i
	quote_char := nil
	var delimiter interface{}
	if (i < len(value)) && ((value[i] == '"') || (value[i] == '\'')) {
		quote_char = value[i]
		i += 1
		delim_start = i
		for (i < len(value)) && (value[i] != quote_char) {
			i += 1
		}
		delimiter = substring(value, delim_start, i)
		if i < len(value) {
			i += 1
		}
	} else if (i < len(value)) && (value[i] == '\\') {
		// Backslash-quoted delimiter like <<\EOF
		i += 1
		delim_start = i
		for (i < len(value)) && !(isWhitespace(value[i])) {
			i += 1
		}
		delimiter = substring(value, delim_start, i)
	} else {
		// Unquoted delimiter
		for (i < len(value)) && !(isWhitespace(value[i])) {
			i += 1
		}
		delimiter = substring(value, delim_start, i)
	}
	// Skip to end of line (heredoc content starts on next line)
	for (i < len(value)) && (value[i] != '\n') {
		i += 1
	}
	if i < len(value) {
		i += 1
	}
	// Find the end delimiter on its own line
	for i < len(value) {
		line_start := i
		// Find end of this line
		line_end := i
		for (line_end < len(value)) && (value[line_end] != '\n') {
			line_end += 1
		}
		line := substring(value, line_start, line_end)
		// Check if this line is the delimiter (possibly with leading tabs for <<-)
		var stripped interface{}
		if ((start + 2) < len(value)) && (value[(start+2)] == '-') {
			stripped = strings.TrimLeft(line, "\t")
		} else {
			stripped = line
		}
		if stripped == delimiter {
			// Found end - return position after delimiter line
			if line_end < len(value) {
				return (line_end + 1)
			} else {
				return line_end
			}
		}
		if line_end < len(value) {
			i = (line_end + 1)
		} else {
			i = line_end
		}
	}
	return i
}

func isWordBoundary(s string, pos int, word_len int) bool {
	// Check character before
	if (pos > 0) && isAlnum_h(string(s[(pos-1)])) {
		return false
	}
	// Check character after
	end := (pos + word_len)
	if (end < len(s)) && isAlnum_h(string(s[end])) {
		return false
	}
	return true
}

// Reserved words that cannot be command names
var RESERVED_WORDS = toSet([]interface{}{"if", "then", "elif", "else", "fi", "while", "until", "for", "select", "do", "done", "case", "esac", "in", "function", "coproc"})

// Metacharacters that break words (unquoted)
// Note: {} are NOT metacharacters - they're only special at command position
// for brace groups. In words like {a,b,c}, braces are literal.
var METACHAR = toSet(" \t\n|&;()<>")
var COND_UNARY_OPS = toSet([]interface{}{"-a", "-b", "-c", "-d", "-e", "-f", "-g", "-h", "-k", "-p", "-r", "-s", "-t", "-u", "-w", "-x", "-G", "-L", "-N", "-O", "-S", "-z", "-n", "-o", "-v", "-R"})
var COND_BINARY_OPS = toSet([]interface{}{"==", "!=", "=~", "=", "<", ">", "-eq", "-ne", "-lt", "-le", "-gt", "-ge", "-nt", "-ot", "-ef"})
var COMPOUND_KEYWORDS = toSet([]interface{}{"while", "until", "for", "if", "case", "select"})

func isQuote(c byte) bool {
	return ((c == '\'') || (c == '"'))
}

func isMetachar(c byte) bool {
	return ((c == ' ') || (c == '\t') || (c == '\n') || (c == '|') || (c == '&') || (c == ';') || (c == '(') || (c == ')') || (c == '<') || (c == '>'))
}

func isExtglobPrefix(c byte) bool {
	return ((c == '@') || (c == '?') || (c == '*') || (c == '+') || (c == '!'))
}

func isRedirectChar(c byte) bool {
	return ((c == '<') || (c == '>'))
}

func isSpecialParam(c byte) bool {
	return ((c == '?') || (c == '$') || (c == '!') || (c == '#') || (c == '@') || (c == '*') || (c == '-'))
}

func isDigit(c byte) bool {
	return ((c >= '0') && (c <= '9'))
}

func isSemicolonOrNewline(c byte) bool {
	return ((c == ';') || (c == '\n'))
}

func isRightBracket(c byte) bool {
	return ((c == ')') || (c == '}'))
}

func isWordStartContext(c byte) bool {
	return ((c == ' ') || (c == '\t') || (c == '\n') || (c == ';') || (c == '|') || (c == '&') || (c == '<') || (c == '('))
}

func isWordEndContext(c byte) bool {
	return ((c == ' ') || (c == '\t') || (c == '\n') || (c == ';') || (c == '|') || (c == '&') || (c == '<') || (c == '>') || (c == '(') || (c == ')'))
}

func isSpecialParamOrDigit(c byte) bool {
	return (isSpecialParam(c) || isDigit(c))
}

func isParamExpansionOp(c byte) bool {
	return ((c == ':') || (c == '-') || (c == '=') || (c == '+') || (c == '?') || (c == '#') || (c == '%') || (c == '/') || (c == '^') || (c == ',') || (c == '@') || (c == '*') || (c == '['))
}

func isSimpleParamOp(c byte) bool {
	return ((c == '-') || (c == '=') || (c == '?') || (c == '+'))
}

func isEscapeCharInDquote(c byte) bool {
	return ((c == '$') || (c == '`') || (c == '\\'))
}

func isListTerminator(c byte) bool {
	return ((c == '\n') || (c == '|') || (c == ';') || (c == '(') || (c == ')'))
}

func isSemicolonOrAmp(c byte) bool {
	return ((c == ';') || (c == '&'))
}

func isParen(c byte) bool {
	return ((c == '(') || (c == ')'))
}

func isCaretOrBang(c byte) bool {
	return ((c == '!') || (c == '^'))
}

func isAtOrStar(c byte) bool {
	return ((c == '@') || (c == '*'))
}

func isDigitOrDash(c byte) bool {
	return (isDigit(c) || (c == '-'))
}

func isNewlineOrRightParen(c byte) bool {
	return ((c == '\n') || (c == ')'))
}

func isNewlineOrRightBracket(c byte) bool {
	return ((c == '\n') || (c == ')') || (c == '}'))
}

func isSemicolonNewlineBrace(c byte) bool {
	return ((c == ';') || (c == '\n') || (c == '{'))
}

func isReservedWord(word string) bool {
	return contains(RESERVED_WORDS, word)
}

func isCompoundKeyword(word string) bool {
	return contains(COMPOUND_KEYWORDS, word)
}

func isCondUnaryOp(op string) bool {
	return contains(COND_UNARY_OPS, op)
}

func isCondBinaryOp(op string) bool {
	return contains(COND_BINARY_OPS, op)
}

func strContains(haystack string, needle string) bool {
	return (strings.Index(haystack, needle) != -1)
}

type Parser struct {
	Source            string
	Pos               int
	Length            int
	pendingHeredocEnd interface{}
}

func NewParser(source string) *Parser {
	p := &Parser{}
	p.Source = source
	p.Pos = 0
	p.Length = len(source)
	p.pendingHeredocEnd = nil
	return p
}

func (p *Parser) AtEnd() bool {
	return (p.Pos >= p.Length)
}

func (p *Parser) Peek() string {
	if p.AtEnd() {
		return nil
	}
	return p.Source[p.Pos]
}

func (p *Parser) Advance() string {
	if p.AtEnd() {
		return nil
	}
	ch := p.Source[p.Pos]
	p.Pos += 1
	return ch
}

func (p *Parser) SkipWhitespace() {
	for !(p.AtEnd()) {
		ch := p.Peek()
		if isWhitespaceNoNewline(ch) {
			p.Advance()
		} else if ch == '#' {
			// Skip comment to end of line (but not the newline itself)
			for !(p.AtEnd()) && (p.Peek() != '\n') {
				p.Advance()
			}
		} else if (ch == '\\') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '\n') {
			// Backslash-newline is line continuation - skip both
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
		if isWhitespace(ch) {
			p.Advance()
			// After advancing past a newline, skip any pending heredoc content
			if ch == '\n' {
				if (p.pendingHeredocEnd != nil) && (p.pendingHeredocEnd > p.Pos) {
					p.Pos = p.pendingHeredocEnd
					p.pendingHeredocEnd = nil
				}
			}
		} else if ch == '#' {
			// Skip comment to end of line
			for !(p.AtEnd()) && (p.Peek() != '\n') {
				p.Advance()
			}
		} else if (ch == '\\') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '\n') {
			// Backslash-newline is line continuation - skip both
			p.Advance()
			p.Advance()
		} else {
			break
		}
	}
}

func (p *Parser) PeekWord() string {
	saved_pos := p.Pos
	p.SkipWhitespace()
	if p.AtEnd() || isMetachar(p.Peek()) {
		p.Pos = saved_pos
		return nil
	}
	chars := []interface{}{}
	for !(p.AtEnd()) && !(isMetachar(p.Peek())) {
		ch := p.Peek()
		// Stop at quotes - don't include in peek
		if isQuote(ch) {
			break
		}
		chars = append(chars, p.Advance())
	}
	var word string
	if chars {
		word = strings.Join(chars, "")
	} else {
		word = nil
	}
	p.Pos = saved_pos
	return word
}

func (p *Parser) ConsumeWord(expected string) bool {
	saved_pos := p.Pos
	p.SkipWhitespace()
	word := p.PeekWord()
	if word != expected {
		p.Pos = saved_pos
		return false
	}
	// Actually consume the word
	p.SkipWhitespace()
	for _, _ := range expected {
		p.Advance()
	}
	return true
}

func (p *Parser) ParseWord(at_command_start bool) Node {
	if at_command_start == nil {
		at_command_start = false
	}
	p.SkipWhitespace()
	if p.AtEnd() {
		return nil
	}
	start := p.Pos
	chars := []interface{}{}
	parts := []interface{}{}
	bracket_depth := 0
	seen_equals := false
	for !(p.AtEnd()) {
		ch := p.Peek()
		// Track bracket depth for array subscripts like a[1+2]=3
		// Inside brackets, metacharacters like | and ( are literal
		// Only track [ after we've seen some chars (so [ -f file ] still works)
		// Only at command start (array assignments), not in argument position
		// Only BEFORE = sign (key=1],a[1 should not track the [1 part)
		// Only after identifier char (not [[ which is conditional keyword)
		var prev_char interface{}
		if (ch == '[') && chars && at_command_start && !(seen_equals) {
			prev_char = chars[(len(chars) - 1)]
			if isAlnum_h(prev_char) || ((prev_char == '_') || (prev_char == ']')) {
				bracket_depth += 1
				chars = append(chars, p.Advance())
				continue
			}
		}
		if (ch == ']') && (bracket_depth > 0) {
			bracket_depth -= 1
			chars = append(chars, p.Advance())
			continue
		}
		if (ch == '=') && (bracket_depth == 0) {
			seen_equals = true
		}
		// Single-quoted string - no expansion
		var arith_result interface{}
		var arith_node interface{}
		var arith_text interface{}
		var cmdsub_result interface{}
		var cmdsub_node interface{}
		var cmdsub_text interface{}
		var ansi_text interface{}
		var paren_depth interface{}
		var next_c interface{}
		var ansi_result interface{}
		var locale_result interface{}
		var procsub_node interface{}
		var locale_node interface{}
		var inner_parts interface{}
		var locale_text interface{}
		var ansi_node interface{}
		var param_result interface{}
		var extglob_depth interface{}
		var param_text interface{}
		var array_text interface{}
		var next_ch interface{}
		var procsub_text interface{}
		var procsub_result interface{}
		var param_node interface{}
		var array_node interface{}
		var pc interface{}
		var array_result interface{}
		if ch == '\'' {
			p.Advance()
			chars = append(chars, "'")
			for !(p.AtEnd()) && (p.Peek() != '\'') {
				chars = append(chars, p.Advance())
			}
			if p.AtEnd() {
				panic(NewParseError("Unterminated single quote"))
			}
			chars = append(chars, p.Advance())
		} else if ch == '"' {
			// Double-quoted string - expansions happen inside
			p.Advance()
			chars = append(chars, "\"")
			for !(p.AtEnd()) && (p.Peek() != '"') {
				c := p.Peek()
				// Handle escape sequences in double quotes
				if (c == '\\') && ((p.Pos + 1) < p.Length) {
					next_c = p.Source[(p.Pos + 1)]
					if next_c == '\n' {
						// Line continuation - skip both backslash and newline
						p.Advance()
						p.Advance()
					} else {
						chars = append(chars, p.Advance())
						chars = append(chars, p.Advance())
					}
				} else if (c == '$') && ((p.Pos + 2) < p.Length) && (p.Source[(p.Pos+1)] == '(') && (p.Source[(p.Pos+2)] == '(') {
					// Handle arithmetic expansion $((...))
					arith_result = p.parseArithmeticExpansion()
					arith_node = arith_result[0]
					arith_text = arith_result[1]
					if arith_node {
						parts = append(parts, arith_node)
						chars = append(chars, arith_text)
					} else {
						// Not arithmetic - try command substitution
						cmdsub_result = p.parseCommandSubstitution()
						cmdsub_node = cmdsub_result[0]
						cmdsub_text = cmdsub_result[1]
						if cmdsub_node {
							parts = append(parts, cmdsub_node)
							chars = append(chars, cmdsub_text)
						} else {
							chars = append(chars, p.Advance())
						}
					}
				} else if (c == '$') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '[') {
					// Handle deprecated arithmetic expansion $[expr]
					arith_result = p.parseDeprecatedArithmetic()
					arith_node = arith_result[0]
					arith_text = arith_result[1]
					if arith_node {
						parts = append(parts, arith_node)
						chars = append(chars, arith_text)
					} else {
						chars = append(chars, p.Advance())
					}
				} else if (c == '$') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(') {
					// Handle command substitution $(...)
					cmdsub_result = p.parseCommandSubstitution()
					cmdsub_node = cmdsub_result[0]
					cmdsub_text = cmdsub_result[1]
					if cmdsub_node {
						parts = append(parts, cmdsub_node)
						chars = append(chars, cmdsub_text)
					} else {
						chars = append(chars, p.Advance())
					}
				} else if c == '$' {
					// Handle parameter expansion inside double quotes
					param_result = p.parseParamExpansion()
					param_node = param_result[0]
					param_text = param_result[1]
					if param_node {
						parts = append(parts, param_node)
						chars = append(chars, param_text)
					} else {
						chars = append(chars, p.Advance())
					}
				} else if c == '`' {
					// Handle backtick command substitution
					cmdsub_result = p.parseBacktickSubstitution()
					cmdsub_node = cmdsub_result[0]
					cmdsub_text = cmdsub_result[1]
					if cmdsub_node {
						parts = append(parts, cmdsub_node)
						chars = append(chars, cmdsub_text)
					} else {
						chars = append(chars, p.Advance())
					}
				} else {
					chars = append(chars, p.Advance())
				}
			}
			if p.AtEnd() {
				panic(NewParseError("Unterminated double quote"))
			}
			chars = append(chars, p.Advance())
		} else if (ch == '\\') && ((p.Pos + 1) < p.Length) {
			// Escape outside quotes
			next_ch = p.Source[(p.Pos + 1)]
			if next_ch == '\n' {
				// Line continuation - skip both backslash and newline
				p.Advance()
				p.Advance()
			} else {
				chars = append(chars, p.Advance())
				chars = append(chars, p.Advance())
			}
		} else if (ch == '$') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '\'') {
			// ANSI-C quoting $'...'
			ansi_result = p.parseAnsiCQuote()
			ansi_node = ansi_result[0]
			ansi_text = ansi_result[1]
			if ansi_node {
				parts = append(parts, ansi_node)
				chars = append(chars, ansi_text)
			} else {
				chars = append(chars, p.Advance())
			}
		} else if (ch == '$') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '"') {
			// Locale translation $"..."
			locale_result = p.parseLocaleString()
			locale_node = locale_result[0]
			locale_text = locale_result[1]
			inner_parts = locale_result[2]
			if locale_node {
				parts = append(parts, locale_node)
				parts = append(parts, inner_parts...)
				chars = append(chars, locale_text)
			} else {
				chars = append(chars, p.Advance())
			}
		} else if (ch == '$') && ((p.Pos + 2) < p.Length) && (p.Source[(p.Pos+1)] == '(') && (p.Source[(p.Pos+2)] == '(') {
			// Arithmetic expansion $((...)) - try before command substitution
			// If it fails (returns None), fall through to command substitution
			arith_result = p.parseArithmeticExpansion()
			arith_node = arith_result[0]
			arith_text = arith_result[1]
			if arith_node {
				parts = append(parts, arith_node)
				chars = append(chars, arith_text)
			} else {
				// Not arithmetic (e.g., '$( ( ... ) )' is command sub + subshell)
				cmdsub_result = p.parseCommandSubstitution()
				cmdsub_node = cmdsub_result[0]
				cmdsub_text = cmdsub_result[1]
				if cmdsub_node {
					parts = append(parts, cmdsub_node)
					chars = append(chars, cmdsub_text)
				} else {
					chars = append(chars, p.Advance())
				}
			}
		} else if (ch == '$') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '[') {
			// Deprecated arithmetic expansion $[expr]
			arith_result = p.parseDeprecatedArithmetic()
			arith_node = arith_result[0]
			arith_text = arith_result[1]
			if arith_node {
				parts = append(parts, arith_node)
				chars = append(chars, arith_text)
			} else {
				chars = append(chars, p.Advance())
			}
		} else if (ch == '$') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(') {
			// Command substitution $(...)
			cmdsub_result = p.parseCommandSubstitution()
			cmdsub_node = cmdsub_result[0]
			cmdsub_text = cmdsub_result[1]
			if cmdsub_node {
				parts = append(parts, cmdsub_node)
				chars = append(chars, cmdsub_text)
			} else {
				chars = append(chars, p.Advance())
			}
		} else if ch == '$' {
			// Parameter expansion $var or ${...}
			param_result = p.parseParamExpansion()
			param_node = param_result[0]
			param_text = param_result[1]
			if param_node {
				parts = append(parts, param_node)
				chars = append(chars, param_text)
			} else {
				chars = append(chars, p.Advance())
			}
		} else if ch == '`' {
			// Backtick command substitution
			cmdsub_result = p.parseBacktickSubstitution()
			cmdsub_node = cmdsub_result[0]
			cmdsub_text = cmdsub_result[1]
			if cmdsub_node {
				parts = append(parts, cmdsub_node)
				chars = append(chars, cmdsub_text)
			} else {
				chars = append(chars, p.Advance())
			}
		} else if isRedirectChar(ch) && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(') {
			// Process substitution <(...) or >(...)
			procsub_result = p.parseProcessSubstitution()
			procsub_node = procsub_result[0]
			procsub_text = procsub_result[1]
			if procsub_node {
				parts = append(parts, procsub_node)
				chars = append(chars, procsub_text)
			} else {
				// Not a process substitution, treat as metacharacter
				break
			}
		} else if (ch == '(') && chars && ((chars[(len(chars)-1)] == '=') || ((len(chars) >= 2) && (chars[(len(chars)-2)] == '+') && (chars[(len(chars)-1)] == '='))) {
			// Array literal: name=(elements) or name+=(elements)
			array_result = p.parseArrayLiteral()
			array_node = array_result[0]
			array_text = array_result[1]
			if array_node {
				parts = append(parts, array_node)
				chars = append(chars, array_text)
			} else {
				// Unexpected: ( without matching )
				break
			}
		} else if isExtglobPrefix(ch) && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(') {
			// Extglob pattern @(), ?(), *(), +(), !()
			chars = append(chars, p.Advance())
			chars = append(chars, p.Advance())
			extglob_depth = 1
			for !(p.AtEnd()) && (extglob_depth > 0) {
				c = p.Peek()
				if c == ')' {
					chars = append(chars, p.Advance())
					extglob_depth -= 1
				} else if c == '(' {
					chars = append(chars, p.Advance())
					extglob_depth += 1
				} else if c == '\\' {
					chars = append(chars, p.Advance())
					if !(p.AtEnd()) {
						chars = append(chars, p.Advance())
					}
				} else if c == '\'' {
					chars = append(chars, p.Advance())
					for !(p.AtEnd()) && (p.Peek() != '\'') {
						chars = append(chars, p.Advance())
					}
					if !(p.AtEnd()) {
						chars = append(chars, p.Advance())
					}
				} else if c == '"' {
					chars = append(chars, p.Advance())
					for !(p.AtEnd()) && (p.Peek() != '"') {
						if (p.Peek() == '\\') && ((p.Pos + 1) < p.Length) {
							chars = append(chars, p.Advance())
						}
						chars = append(chars, p.Advance())
					}
					if !(p.AtEnd()) {
						chars = append(chars, p.Advance())
					}
				} else if (c == '$') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(') {
					// $() or $(()) inside extglob
					chars = append(chars, p.Advance())
					chars = append(chars, p.Advance())
					if !(p.AtEnd()) && (p.Peek() == '(') {
						// $(()) arithmetic
						chars = append(chars, p.Advance())
						paren_depth = 2
						for !(p.AtEnd()) && (paren_depth > 0) {
							pc = p.Peek()
							if pc == '(' {
								paren_depth += 1
							} else if pc == ')' {
								paren_depth -= 1
							}
							chars = append(chars, p.Advance())
						}
					} else {
						// $() command sub - count as nested paren
						extglob_depth += 1
					}
				} else if isExtglobPrefix(c) && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(') {
					// Nested extglob
					chars = append(chars, p.Advance())
					chars = append(chars, p.Advance())
					extglob_depth += 1
				} else {
					chars = append(chars, p.Advance())
				}
			}
		} else if isMetachar(ch) && (bracket_depth == 0) {
			// Metacharacter ends the word (unless inside brackets like a[x|y]=1)
			break
		} else {
			// Regular character (including metacharacters inside brackets)
			chars = append(chars, p.Advance())
		}
	}
	if !(chars) {
		return nil
	}
	if len(parts) > 0 {
		return NewWord(strings.Join(chars, ""), parts)
	} else {
		return NewWord(strings.Join(chars, ""), nil)
	}
}

func (p *Parser) parseCommandSubstitution() {
	if p.AtEnd() || (p.Peek() != '$') {
		return []interface{}{nil, ""}
	}
	start := p.Pos
	p.Advance()
	if p.AtEnd() || (p.Peek() != '(') {
		p.Pos = start
		return []interface{}{nil, ""}
	}
	p.Advance()
	// Find matching closing paren, being aware of:
	// - Nested $() and plain ()
	// - Quoted strings
	// - case statements (where ) after pattern isn't a closer)
	content_start := p.Pos
	depth := 1
	case_depth := 0
	for !(p.AtEnd()) && (depth > 0) {
		c := p.Peek()
		// Single-quoted string - no special chars inside
		if c == '\'' {
			p.Advance()
			for !(p.AtEnd()) && (p.Peek() != '\'') {
				p.Advance()
			}
			if !(p.AtEnd()) {
				p.Advance()
			}
			continue
		}
		// Double-quoted string - handle escapes and nested $()
		var nested_depth interface{}
		var nc interface{}
		if c == '"' {
			p.Advance()
			for !(p.AtEnd()) && (p.Peek() != '"') {
				if (p.Peek() == '\\') && ((p.Pos + 1) < p.Length) {
					p.Advance()
					p.Advance()
				} else if (p.Peek() == '$') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(') {
					// Nested $() in double quotes - recurse to find matching )
					// Command substitution creates new quoting context
					p.Advance()
					p.Advance()
					nested_depth = 1
					for !(p.AtEnd()) && (nested_depth > 0) {
						nc = p.Peek()
						if nc == '\'' {
							p.Advance()
							for !(p.AtEnd()) && (p.Peek() != '\'') {
								p.Advance()
							}
							if !(p.AtEnd()) {
								p.Advance()
							}
						} else if nc == '"' {
							p.Advance()
							for !(p.AtEnd()) && (p.Peek() != '"') {
								if (p.Peek() == '\\') && ((p.Pos + 1) < p.Length) {
									p.Advance()
								}
								p.Advance()
							}
							if !(p.AtEnd()) {
								p.Advance()
							}
						} else if (nc == '\\') && ((p.Pos + 1) < p.Length) {
							p.Advance()
							p.Advance()
						} else if (nc == '$') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(') {
							p.Advance()
							p.Advance()
							nested_depth += 1
						} else if nc == '(' {
							nested_depth += 1
							p.Advance()
						} else if nc == ')' {
							nested_depth -= 1
							if nested_depth > 0 {
								p.Advance()
							}
						} else {
							p.Advance()
						}
					}
					if nested_depth == 0 {
						p.Advance()
					}
				} else {
					p.Advance()
				}
			}
			if !(p.AtEnd()) {
				p.Advance()
			}
			continue
		}
		// Backslash escape
		if (c == '\\') && ((p.Pos + 1) < p.Length) {
			p.Advance()
			p.Advance()
			continue
		}
		// Comment - skip until newline
		if (c == '#') && p.isWordBoundaryBefore() {
			for !(p.AtEnd()) && (p.Peek() != '\n') {
				p.Advance()
			}
			continue
		}
		// Heredoc - skip until delimiter line is found
		var quote interface{}
		var ch interface{}
		var delimiter interface{}
		var line interface{}
		var delimiter_chars interface{}
		var line_start interface{}
		var line_end interface{}
		if (c == '<') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '<') {
			p.Advance()
			p.Advance()
			// Check for <<- (strip tabs)
			if !(p.AtEnd()) && (p.Peek() == '-') {
				p.Advance()
			}
			// Skip whitespace before delimiter
			for !(p.AtEnd()) && isWhitespaceNoNewline(p.Peek()) {
				p.Advance()
			}
			// Parse delimiter (handle quoting)
			delimiter_chars = []interface{}{}
			if !(p.AtEnd()) {
				ch = p.Peek()
				if isQuote(ch) {
					quote = p.Advance()
					for !(p.AtEnd()) && (p.Peek() != quote) {
						delimiter_chars = append(delimiter_chars, p.Advance())
					}
					if !(p.AtEnd()) {
						p.Advance()
					}
				} else if ch == '\\' {
					p.Advance()
					// Backslash quotes - first char can be special, then read word
					if !(p.AtEnd()) {
						delimiter_chars = append(delimiter_chars, p.Advance())
					}
					for !(p.AtEnd()) && !(isMetachar(p.Peek())) {
						delimiter_chars = append(delimiter_chars, p.Advance())
					}
				} else {
					// Unquoted delimiter with possible embedded quotes
					for !(p.AtEnd()) && !(isMetachar(p.Peek())) {
						ch = p.Peek()
						if isQuote(ch) {
							quote = p.Advance()
							for !(p.AtEnd()) && (p.Peek() != quote) {
								delimiter_chars = append(delimiter_chars, p.Advance())
							}
							if !(p.AtEnd()) {
								p.Advance()
							}
						} else if ch == '\\' {
							p.Advance()
							if !(p.AtEnd()) {
								delimiter_chars = append(delimiter_chars, p.Advance())
							}
						} else {
							delimiter_chars = append(delimiter_chars, p.Advance())
						}
					}
				}
			}
			delimiter = strings.Join(delimiter_chars, "")
			if delimiter {
				// Skip to end of current line
				for !(p.AtEnd()) && (p.Peek() != '\n') {
					p.Advance()
				}
				// Skip newline
				if !(p.AtEnd()) && (p.Peek() == '\n') {
					p.Advance()
				}
				// Skip lines until we find the delimiter
				for !(p.AtEnd()) {
					line_start = p.Pos
					line_end = p.Pos
					for (line_end < p.Length) && (p.Source[line_end] != '\n') {
						line_end += 1
					}
					line = substring(p.Source, line_start, line_end)
					// Move position to end of line
					p.Pos = line_end
					// Check if this line matches delimiter
					if (line == delimiter) || (strings.TrimLeft(line, "\t") == delimiter) {
						// Skip newline after delimiter
						if !(p.AtEnd()) && (p.Peek() == '\n') {
							p.Advance()
						}
						break
					}
					// Skip newline and continue
					if !(p.AtEnd()) && (p.Peek() == '\n') {
						p.Advance()
					}
				}
			}
			continue
		}
		// Track case/esac for pattern terminator handling
		// Check for 'case' keyword (word boundary: preceded by space/newline/start)
		if (c == 'c') && p.isWordBoundaryBefore() {
			if p.lookaheadKeyword("case") {
				case_depth += 1
				p.skipKeyword("case")
				continue
			}
		}
		// Check for 'esac' keyword
		if (c == 'e') && p.isWordBoundaryBefore() && (case_depth > 0) {
			if p.lookaheadKeyword("esac") {
				case_depth -= 1
				p.skipKeyword("esac")
				continue
			}
		}
		// Handle parentheses
		var q interface{}
		var temp_case_depth interface{}
		var temp_depth interface{}
		var found_esac interface{}
		var tc interface{}
		var saved interface{}
		if c == '(' {
			depth += 1
		} else if c == ')' {
			// In case statement, ) after pattern is a terminator, not a paren
			// Only decrement depth if we're not in a case pattern position
			if (case_depth > 0) && (depth == 1) {
				// This ) might be a case pattern terminator, not closing the $(
				// Look ahead to see if there's still content that needs esac
				saved = p.Pos
				p.Advance()
				// Scan ahead to see if we find esac that closes our case
				// before finding a ) that could close our $(
				temp_depth = 0
				temp_case_depth = case_depth
				found_esac = false
				for !(p.AtEnd()) {
					tc = p.Peek()
					if (tc == '\'') || (tc == '"') {
						// Skip quoted strings
						q = tc
						p.Advance()
						for !(p.AtEnd()) && (p.Peek() != q) {
							if (q == '"') && (p.Peek() == '\\') {
								p.Advance()
							}
							p.Advance()
						}
						if !(p.AtEnd()) {
							p.Advance()
						}
					} else if (tc == 'c') && p.isWordBoundaryBefore() && p.lookaheadKeyword("case") {
						// Nested case in lookahead
						temp_case_depth += 1
						p.skipKeyword("case")
					} else if (tc == 'e') && p.isWordBoundaryBefore() && p.lookaheadKeyword("esac") {
						temp_case_depth -= 1
						if temp_case_depth == 0 {
							// All cases are closed
							found_esac = true
							break
						}
						p.skipKeyword("esac")
					} else if tc == '(' {
						temp_depth += 1
						p.Advance()
					} else if tc == ')' {
						// In case, ) is a pattern terminator, not a closer
						if temp_case_depth > 0 {
							p.Advance()
						} else if temp_depth > 0 {
							temp_depth -= 1
							p.Advance()
						} else {
							// Found a ) that could be our closer
							break
						}
					} else {
						p.Advance()
					}
				}
				p.Pos = saved
				if found_esac {
					// This ) is a case pattern terminator, not our closer
					p.Advance()
					continue
				}
			}
			depth -= 1
		}
		if depth > 0 {
			p.Advance()
		}
	}
	if depth != 0 {
		p.Pos = start
		return []interface{}{nil, ""}
	}
	content := substring(p.Source, content_start, p.Pos)
	p.Advance()
	text := substring(p.Source, start, p.Pos)
	// Parse the content as a command list
	sub_parser := NewParser(content)
	cmd := sub_parser.ParseList(true)
	if cmd == nil {
		cmd = NewEmpty()
	}
	return []interface{}{NewCommandSubstitution(cmd), text}
}

func (p *Parser) isWordBoundaryBefore() bool {
	if p.Pos == 0 {
		return true
	}
	prev := p.Source[(p.Pos - 1)]
	return isWordStartContext(prev)
}

func (p *Parser) isAssignmentWord(word Word) bool {
	in_single := false
	in_double := false
	i := 0
	for i < len(word.Value) {
		ch := word.Value[i]
		if (ch == '\'') && !(in_double) {
			in_single = !(in_single)
		} else if (ch == '"') && !(in_single) {
			in_double = !(in_double)
		} else if (ch == '\\') && !(in_single) && ((i + 1) < len(word.Value)) {
			i += 1
			continue
		} else if (ch == '=') && !(in_single) && !(in_double) {
			return true
		}
		i += 1
	}
	return false
}

func (p *Parser) lookaheadKeyword(keyword string) bool {
	if (p.Pos + len(keyword)) > p.Length {
		return false
	}
	if !(startsWithAt(p.Source, p.Pos, keyword)) {
		return false
	}
	// Check word boundary after keyword
	after_pos := (p.Pos + len(keyword))
	if after_pos >= p.Length {
		return true
	}
	after := p.Source[after_pos]
	return isWordEndContext(after)
}

func (p *Parser) skipKeyword(keyword string) {
	for _, _ := range keyword {
		p.Advance()
	}
}

func (p *Parser) parseBacktickSubstitution() {
	if p.AtEnd() || (p.Peek() != '`') {
		return []interface{}{nil, ""}
	}
	start := p.Pos
	p.Advance()
	// Find closing backtick, processing escape sequences as we go.
	// In backticks, backslash is special only before $, `, \, or newline.
	// \$ -> $, \` -> `, \\ -> \, \<newline> -> removed (line continuation)
	// other \X -> \X (backslash is literal)
	// content_chars: what gets parsed as the inner command
	// text_chars: what appears in the word representation (with line continuations removed)
	content_chars := []interface{}{}
	text_chars := []interface{}{"`"}
	for !(p.AtEnd()) && (p.Peek() != '`') {
		c := p.Peek()
		var ch interface{}
		var escaped interface{}
		var next_c interface{}
		if (c == '\\') && ((p.Pos + 1) < p.Length) {
			next_c = p.Source[(p.Pos + 1)]
			if next_c == '\n' {
				// Line continuation: skip both backslash and newline
				p.Advance()
				p.Advance()
			} else if isEscapeCharInDquote(next_c) {
				// Don't add to content_chars or text_chars
				// Escape sequence: skip backslash in content, keep both in text
				p.Advance()
				escaped = p.Advance()
				content_chars = append(content_chars, escaped)
				text_chars = append(text_chars, "\\")
				text_chars = append(text_chars, escaped)
			} else {
				// Backslash is literal before other characters
				ch = p.Advance()
				content_chars = append(content_chars, ch)
				text_chars = append(text_chars, ch)
			}
		} else {
			ch = p.Advance()
			content_chars = append(content_chars, ch)
			text_chars = append(text_chars, ch)
		}
	}
	if p.AtEnd() {
		p.Pos = start
		return []interface{}{nil, ""}
	}
	p.Advance()
	text_chars = append(text_chars, "`")
	text := strings.Join(text_chars, "")
	content := strings.Join(content_chars, "")
	// Parse the content as a command list
	sub_parser := NewParser(content)
	cmd := sub_parser.ParseList(true)
	if cmd == nil {
		cmd = NewEmpty()
	}
	return []interface{}{NewCommandSubstitution(cmd), text}
}

func (p *Parser) parseProcessSubstitution() {
	if p.AtEnd() || !(isRedirectChar(p.Peek())) {
		return []interface{}{nil, ""}
	}
	start := p.Pos
	direction := p.Advance()
	if p.AtEnd() || (p.Peek() != '(') {
		p.Pos = start
		return []interface{}{nil, ""}
	}
	p.Advance()
	// Find matching ) - track nested parens and handle quotes
	content_start := p.Pos
	depth := 1
	for !(p.AtEnd()) && (depth > 0) {
		c := p.Peek()
		// Single-quoted string
		if c == '\'' {
			p.Advance()
			for !(p.AtEnd()) && (p.Peek() != '\'') {
				p.Advance()
			}
			if !(p.AtEnd()) {
				p.Advance()
			}
			continue
		}
		// Double-quoted string
		if c == '"' {
			p.Advance()
			for !(p.AtEnd()) && (p.Peek() != '"') {
				if (p.Peek() == '\\') && ((p.Pos + 1) < p.Length) {
					p.Advance()
				}
				p.Advance()
			}
			if !(p.AtEnd()) {
				p.Advance()
			}
			continue
		}
		// Backslash escape
		if (c == '\\') && ((p.Pos + 1) < p.Length) {
			p.Advance()
			p.Advance()
			continue
		}
		// Nested parentheses (including nested process substitutions)
		if c == '(' {
			depth += 1
		} else if c == ')' {
			depth -= 1
			if depth == 0 {
				break
			}
		}
		p.Advance()
	}
	if depth != 0 {
		p.Pos = start
		return []interface{}{nil, ""}
	}
	content := substring(p.Source, content_start, p.Pos)
	p.Advance()
	text := substring(p.Source, start, p.Pos)
	// Parse the content as a command list
	sub_parser := NewParser(content)
	cmd := sub_parser.ParseList(true)
	if cmd == nil {
		cmd = NewEmpty()
	}
	return []interface{}{NewProcessSubstitution(direction, cmd), text}
}

func (p *Parser) parseArrayLiteral() {
	if p.AtEnd() || (p.Peek() != '(') {
		return []interface{}{nil, ""}
	}
	start := p.Pos
	p.Advance()
	elements := []interface{}{}
	for true {
		// Skip whitespace and newlines between elements
		for !(p.AtEnd()) && isWhitespace(p.Peek()) {
			p.Advance()
		}
		if p.AtEnd() {
			panic(NewParseError("Unterminated array literal"))
		}
		if p.Peek() == ')' {
			break
		}
		// Parse an element word
		word := p.ParseWord()
		if word == nil {
			// Might be a closing paren or error
			if p.Peek() == ')' {
				break
			}
			panic(NewParseError("Expected word in array literal"))
		}
		elements = append(elements, word)
	}
	if p.AtEnd() || (p.Peek() != ')') {
		panic(NewParseError("Expected ) to close array literal"))
	}
	p.Advance()
	text := substring(p.Source, start, p.Pos)
	return []interface{}{NewArray(elements), text}
}

func (p *Parser) parseArithmeticExpansion() {
	if p.AtEnd() || (p.Peek() != '$') {
		return []interface{}{nil, ""}
	}
	start := p.Pos
	// Check for $((
	if ((p.Pos + 2) >= p.Length) || (p.Source[(p.Pos+1)] != '(') || (p.Source[(p.Pos+2)] != '(') {
		return []interface{}{nil, ""}
	}
	p.Advance()
	p.Advance()
	p.Advance()
	// Find matching )) - need to track nested parens
	// Must be )) with no space between - ') )' is command sub + subshell
	content_start := p.Pos
	depth := 1
	for !(p.AtEnd()) && (depth > 0) {
		c := p.Peek()
		if c == '(' {
			depth += 1
			p.Advance()
		} else if c == ')' {
			// Check for ))
			if (depth == 1) && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == ')') {
				// Found the closing ))
				break
			}
			depth -= 1
			if depth == 0 {
				// Closed with ) but next isn't ) - this is $( ( ... ) )
				p.Pos = start
				return []interface{}{nil, ""}
			}
			p.Advance()
		} else {
			p.Advance()
		}
	}
	if p.AtEnd() || (depth != 1) {
		p.Pos = start
		return []interface{}{nil, ""}
	}
	content := substring(p.Source, content_start, p.Pos)
	p.Advance()
	p.Advance()
	text := substring(p.Source, start, p.Pos)
	// Parse the arithmetic expression
	expr := p.parseArithExpr(content)
	return []interface{}{NewArithmeticExpansion(expr), text}
}

func (p *Parser) parseArithExpr(content string) Node {
	// ========== Arithmetic expression parser ==========
	// Operator precedence (lowest to highest):
	// 1. comma (,)
	// 2. assignment (= += -= *= /= %= <<= >>= &= ^= |=)
	// 3. ternary (? :)
	// 4. logical or (||)
	// 5. logical and (&&)
	// 6. bitwise or (|)
	// 7. bitwise xor (^)
	// 8. bitwise and (&)
	// 9. equality (== !=)
	// 10. comparison (< > <= >=)
	// 11. shift (<< >>)
	// 12. addition (+ -)
	// 13. multiplication (* / %)
	// 14. exponentiation (**)
	// 15. unary (! ~ + - ++ --)
	// 16. postfix (++ -- [])
	// Save any existing arith context (for nested parsing)
	saved_arith_src := getAttr(p, "_arith_src", nil)
	saved_arith_pos := getAttr(p, "_arith_pos", nil)
	saved_arith_len := getAttr(p, "_arith_len", nil)
	p.arithSrc = content
	p.arithPos = 0
	p.arithLen = len(content)
	p.arithSkipWs()
	var result interface{}
	if p.arithAtEnd() {
		result = nil
	} else {
		result = p.arithParseComma()
	}
	// Restore previous arith context
	if saved_arith_src != nil {
		p.arithSrc = saved_arith_src
		p.arithPos = saved_arith_pos
		p.arithLen = saved_arith_len
	}
	return result
}

func (p *Parser) arithAtEnd() bool {
	return (p.arithPos >= p.arithLen)
}

func (p *Parser) arithPeek(offset int) string {
	if offset == nil {
		offset = 0
	}
	pos := (p.arithPos + offset)
	if pos >= p.arithLen {
		return ""
	}
	return p.arithSrc[pos]
}

func (p *Parser) arithAdvance() string {
	if p.arithAtEnd() {
		return ""
	}
	c := p.arithSrc[p.arithPos]
	p.arithPos += 1
	return c
}

func (p *Parser) arithSkipWs() {
	for !(p.arithAtEnd()) {
		c := p.arithSrc[p.arithPos]
		if isWhitespace(c) {
			p.arithPos += 1
		} else if (c == '\\') && ((p.arithPos + 1) < p.arithLen) && (p.arithSrc[(p.arithPos+1)] == '\n') {
			// Backslash-newline continuation
			p.arithPos += 2
		} else {
			break
		}
	}
}

func (p *Parser) arithMatch(s string) bool {
	return startsWithAt(p.arithSrc, p.arithPos, s)
}

func (p *Parser) arithConsume(s string) bool {
	if p.arithMatch(s) {
		p.arithPos += len(s)
		return true
	}
	return false
}

func (p *Parser) arithParseComma() Node {
	left := p.arithParseAssign()
	for true {
		p.arithSkipWs()
		var right interface{}
		if p.arithConsume(",") {
			p.arithSkipWs()
			right = p.arithParseAssign()
			left = NewArithComma(left, right)
		} else {
			break
		}
	}
	return left
}

func (p *Parser) arithParseAssign() Node {
	left := p.arithParseTernary()
	p.arithSkipWs()
	// Check for assignment operators
	assign_ops := []interface{}{"<<=", ">>=", "+=", "-=", "*=", "/=", "%=", "&=", "^=", "|=", "="}
	var right interface{}
	for _, op := range assign_ops {
		if p.arithMatch(op) {
			// Make sure it's not == or !=
			if (op == '=') && (p.arithPeek(1) == '=') {
				break
			}
			p.arithConsume(op)
			p.arithSkipWs()
			right = p.arithParseAssign()
			return NewArithAssign(op, left, right)
		}
	}
	return left
}

func (p *Parser) arithParseTernary() Node {
	cond := p.arithParseLogicalOr()
	p.arithSkipWs()
	var if_false interface{}
	var if_true interface{}
	if p.arithConsume("?") {
		p.arithSkipWs()
		// True branch can be empty (e.g., 4 ? : $A - invalid at runtime, valid syntax)
		if p.arithMatch(":") {
			if_true = nil
		} else {
			if_true = p.arithParseAssign()
		}
		p.arithSkipWs()
		// Check for : (may be missing in malformed expressions like 1 ? 20)
		if p.arithConsume(":") {
			p.arithSkipWs()
			// False branch can be empty (e.g., 4 ? 20 : - invalid at runtime)
			if p.arithAtEnd() || (p.arithPeek() == ')') {
				if_false = nil
			} else {
				if_false = p.arithParseTernary()
			}
		} else {
			if_false = nil
		}
		return NewArithTernary(cond, if_true, if_false)
	}
	return cond
}

func (p *Parser) arithParseLogicalOr() Node {
	left := p.arithParseLogicalAnd()
	for true {
		p.arithSkipWs()
		var right interface{}
		if p.arithMatch("||") {
			p.arithConsume("||")
			p.arithSkipWs()
			right = p.arithParseLogicalAnd()
			left = NewArithBinaryOp("||", left, right)
		} else {
			break
		}
	}
	return left
}

func (p *Parser) arithParseLogicalAnd() Node {
	left := p.arithParseBitwiseOr()
	for true {
		p.arithSkipWs()
		var right interface{}
		if p.arithMatch("&&") {
			p.arithConsume("&&")
			p.arithSkipWs()
			right = p.arithParseBitwiseOr()
			left = NewArithBinaryOp("&&", left, right)
		} else {
			break
		}
	}
	return left
}

func (p *Parser) arithParseBitwiseOr() Node {
	left := p.arithParseBitwiseXor()
	for true {
		p.arithSkipWs()
		// Make sure it's not || or |=
		var right interface{}
		if (p.arithPeek() == '|') && ((p.arithPeek(1) != '|') && (p.arithPeek(1) != '=')) {
			p.arithAdvance()
			p.arithSkipWs()
			right = p.arithParseBitwiseXor()
			left = NewArithBinaryOp("|", left, right)
		} else {
			break
		}
	}
	return left
}

func (p *Parser) arithParseBitwiseXor() Node {
	left := p.arithParseBitwiseAnd()
	for true {
		p.arithSkipWs()
		// Make sure it's not ^=
		var right interface{}
		if (p.arithPeek() == '^') && (p.arithPeek(1) != '=') {
			p.arithAdvance()
			p.arithSkipWs()
			right = p.arithParseBitwiseAnd()
			left = NewArithBinaryOp("^", left, right)
		} else {
			break
		}
	}
	return left
}

func (p *Parser) arithParseBitwiseAnd() Node {
	left := p.arithParseEquality()
	for true {
		p.arithSkipWs()
		// Make sure it's not && or &=
		var right interface{}
		if (p.arithPeek() == '&') && ((p.arithPeek(1) != '&') && (p.arithPeek(1) != '=')) {
			p.arithAdvance()
			p.arithSkipWs()
			right = p.arithParseEquality()
			left = NewArithBinaryOp("&", left, right)
		} else {
			break
		}
	}
	return left
}

func (p *Parser) arithParseEquality() Node {
	left := p.arithParseComparison()
	for true {
		p.arithSkipWs()
		var right interface{}
		if p.arithMatch("==") {
			p.arithConsume("==")
			p.arithSkipWs()
			right = p.arithParseComparison()
			left = NewArithBinaryOp("==", left, right)
		} else if p.arithMatch("!=") {
			p.arithConsume("!=")
			p.arithSkipWs()
			right = p.arithParseComparison()
			left = NewArithBinaryOp("!=", left, right)
		} else {
			break
		}
	}
	return left
}

func (p *Parser) arithParseComparison() Node {
	left := p.arithParseShift()
	for true {
		p.arithSkipWs()
		var right interface{}
		if p.arithMatch("<=") {
			p.arithConsume("<=")
			p.arithSkipWs()
			right = p.arithParseShift()
			left = NewArithBinaryOp("<=", left, right)
		} else if p.arithMatch(">=") {
			p.arithConsume(">=")
			p.arithSkipWs()
			right = p.arithParseShift()
			left = NewArithBinaryOp(">=", left, right)
		} else if (p.arithPeek() == '<') && ((p.arithPeek(1) != '<') && (p.arithPeek(1) != '=')) {
			p.arithAdvance()
			p.arithSkipWs()
			right = p.arithParseShift()
			left = NewArithBinaryOp("<", left, right)
		} else if (p.arithPeek() == '>') && ((p.arithPeek(1) != '>') && (p.arithPeek(1) != '=')) {
			p.arithAdvance()
			p.arithSkipWs()
			right = p.arithParseShift()
			left = NewArithBinaryOp(">", left, right)
		} else {
			break
		}
	}
	return left
}

func (p *Parser) arithParseShift() Node {
	left := p.arithParseAdditive()
	for true {
		p.arithSkipWs()
		if p.arithMatch("<<=") {
			break
		}
		if p.arithMatch(">>=") {
			break
		}
		var right interface{}
		if p.arithMatch("<<") {
			p.arithConsume("<<")
			p.arithSkipWs()
			right = p.arithParseAdditive()
			left = NewArithBinaryOp("<<", left, right)
		} else if p.arithMatch(">>") {
			p.arithConsume(">>")
			p.arithSkipWs()
			right = p.arithParseAdditive()
			left = NewArithBinaryOp(">>", left, right)
		} else {
			break
		}
	}
	return left
}

func (p *Parser) arithParseAdditive() Node {
	left := p.arithParseMultiplicative()
	for true {
		p.arithSkipWs()
		c := p.arithPeek()
		c2 := p.arithPeek(1)
		var right interface{}
		if (c == '+') && ((c2 != '+') && (c2 != '=')) {
			p.arithAdvance()
			p.arithSkipWs()
			right = p.arithParseMultiplicative()
			left = NewArithBinaryOp("+", left, right)
		} else if (c == '-') && ((c2 != '-') && (c2 != '=')) {
			p.arithAdvance()
			p.arithSkipWs()
			right = p.arithParseMultiplicative()
			left = NewArithBinaryOp("-", left, right)
		} else {
			break
		}
	}
	return left
}

func (p *Parser) arithParseMultiplicative() Node {
	left := p.arithParseExponentiation()
	for true {
		p.arithSkipWs()
		c := p.arithPeek()
		c2 := p.arithPeek(1)
		var right interface{}
		if (c == '*') && ((c2 != '*') && (c2 != '=')) {
			p.arithAdvance()
			p.arithSkipWs()
			right = p.arithParseExponentiation()
			left = NewArithBinaryOp("*", left, right)
		} else if (c == '/') && (c2 != '=') {
			p.arithAdvance()
			p.arithSkipWs()
			right = p.arithParseExponentiation()
			left = NewArithBinaryOp("/", left, right)
		} else if (c == '%') && (c2 != '=') {
			p.arithAdvance()
			p.arithSkipWs()
			right = p.arithParseExponentiation()
			left = NewArithBinaryOp("%", left, right)
		} else {
			break
		}
	}
	return left
}

func (p *Parser) arithParseExponentiation() Node {
	left := p.arithParseUnary()
	p.arithSkipWs()
	var right interface{}
	if p.arithMatch("**") {
		p.arithConsume("**")
		p.arithSkipWs()
		right = p.arithParseExponentiation()
		return NewArithBinaryOp("**", left, right)
	}
	return left
}

func (p *Parser) arithParseUnary() Node {
	p.arithSkipWs()
	// Pre-increment/decrement
	var operand interface{}
	if p.arithMatch("++") {
		p.arithConsume("++")
		p.arithSkipWs()
		operand = p.arithParseUnary()
		return NewArithPreIncr(operand)
	}
	if p.arithMatch("--") {
		p.arithConsume("--")
		p.arithSkipWs()
		operand = p.arithParseUnary()
		return NewArithPreDecr(operand)
	}
	// Unary operators
	c := p.arithPeek()
	if c == '!' {
		p.arithAdvance()
		p.arithSkipWs()
		operand = p.arithParseUnary()
		return NewArithUnaryOp("!", operand)
	}
	if c == '~' {
		p.arithAdvance()
		p.arithSkipWs()
		operand = p.arithParseUnary()
		return NewArithUnaryOp("~", operand)
	}
	if (c == '+') && (p.arithPeek(1) != '+') {
		p.arithAdvance()
		p.arithSkipWs()
		operand = p.arithParseUnary()
		return NewArithUnaryOp("+", operand)
	}
	if (c == '-') && (p.arithPeek(1) != '-') {
		p.arithAdvance()
		p.arithSkipWs()
		operand = p.arithParseUnary()
		return NewArithUnaryOp("-", operand)
	}
	return p.arithParsePostfix()
}

func (p *Parser) arithParsePostfix() Node {
	left := p.arithParsePrimary()
	for true {
		p.arithSkipWs()
		var index interface{}
		if p.arithMatch("++") {
			p.arithConsume("++")
			left = NewArithPostIncr(left)
		} else if p.arithMatch("--") {
			p.arithConsume("--")
			left = NewArithPostDecr(left)
		} else if p.arithPeek() == '[' {
			// Array subscript - but only for variables
			if left.GetKind() == "var" {
				p.arithAdvance()
				p.arithSkipWs()
				index = p.arithParseComma()
				p.arithSkipWs()
				if !(p.arithConsume("]")) {
					panic(NewParseError("Expected ']' in array subscript"))
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

func (p *Parser) arithParsePrimary() Node {
	p.arithSkipWs()
	c := p.arithPeek()
	// Parenthesized expression
	var expr interface{}
	if c == '(' {
		p.arithAdvance()
		p.arithSkipWs()
		expr = p.arithParseComma()
		p.arithSkipWs()
		if !(p.arithConsume(")")) {
			panic(NewParseError("Expected ')' in arithmetic expression"))
		}
		return expr
	}
	// Parameter expansion ${...} or $var or $(...)
	if c == '$' {
		return p.arithParseExpansion()
	}
	// Single-quoted string - content becomes the number
	if c == '\'' {
		return p.arithParseSingleQuote()
	}
	// Double-quoted string - may contain expansions
	if c == '"' {
		return p.arithParseDoubleQuote()
	}
	// Backtick command substitution
	if c == '`' {
		return p.arithParseBacktick()
	}
	// Escape sequence \X (not line continuation, which is handled in _arith_skip_ws)
	// Escape covers only the single character after backslash
	var escaped_char interface{}
	if c == '\\' {
		p.arithAdvance()
		if p.arithAtEnd() {
			panic(NewParseError("Unexpected end after backslash in arithmetic"))
		}
		escaped_char = p.arithAdvance()
		return NewArithEscape(escaped_char)
	}
	// Number or variable
	return p.arithParseNumberOrVar()
}

func (p *Parser) arithParseExpansion() Node {
	if !(p.arithConsume("$")) {
		panic(NewParseError("Expected '$'"))
	}
	c := p.arithPeek()
	// Command substitution $(...)
	if c == '(' {
		return p.arithParseCmdsub()
	}
	// Braced parameter ${...}
	if c == '{' {
		return p.arithParseBracedParam()
	}
	// Simple $var
	name_chars := []interface{}{}
	for !(p.arithAtEnd()) {
		ch := p.arithPeek()
		if isAlnum_h(ch) || (ch == '_') {
			name_chars = append(name_chars, p.arithAdvance())
		} else if (isSpecialParamOrDigit(ch) || (ch == '#')) && !(name_chars) {
			// Special parameters
			name_chars = append(name_chars, p.arithAdvance())
			break
		} else {
			break
		}
	}
	if !(name_chars) {
		panic(NewParseError("Expected variable name after $"))
	}
	return NewParamExpansion(strings.Join(name_chars, ""))
}

func (p *Parser) arithParseCmdsub() Node {
	// We're positioned after $, at (
	p.arithAdvance()
	// Check for $(( which is nested arithmetic
	var depth int
	var inner_expr interface{}
	var ch interface{}
	var content_start interface{}
	var content interface{}
	if p.arithPeek() == '(' {
		p.arithAdvance()
		depth = 1
		content_start = p.arithPos
		for !(p.arithAtEnd()) && (depth > 0) {
			ch = p.arithPeek()
			if ch == '(' {
				depth += 1
				p.arithAdvance()
			} else if ch == ')' {
				if (depth == 1) && (p.arithPeek(1) == ')') {
					break
				}
				depth -= 1
				p.arithAdvance()
			} else {
				p.arithAdvance()
			}
		}
		content = substring(p.arithSrc, content_start, p.arithPos)
		p.arithAdvance()
		p.arithAdvance()
		inner_expr = p.parseArithExpr(content)
		return NewArithmeticExpansion(inner_expr)
	}
	// Regular command substitution
	depth = 1
	content_start = p.arithPos
	for !(p.arithAtEnd()) && (depth > 0) {
		ch = p.arithPeek()
		if ch == '(' {
			depth += 1
			p.arithAdvance()
		} else if ch == ')' {
			depth -= 1
			if depth == 0 {
				break
			}
			p.arithAdvance()
		} else {
			p.arithAdvance()
		}
	}
	content = substring(p.arithSrc, content_start, p.arithPos)
	p.arithAdvance()
	// Parse the command inside
	saved_pos := p.Pos
	saved_src := p.Source
	saved_len := p.Length
	p.Source = content
	p.Pos = 0
	p.Length = len(content)
	cmd := p.ParseList(true)
	p.Source = saved_src
	p.Pos = saved_pos
	p.Length = saved_len
	return NewCommandSubstitution(cmd)
}

func (p *Parser) arithParseBracedParam() Node {
	p.arithAdvance()
	// Handle indirect ${!var}
	var name_chars interface{}
	if p.arithPeek() == '!' {
		p.arithAdvance()
		name_chars = []interface{}{}
		for !(p.arithAtEnd()) && (p.arithPeek() != '}') {
			name_chars = append(name_chars, p.arithAdvance())
		}
		p.arithConsume("}")
		return NewParamIndirect(strings.Join(name_chars, ""))
	}
	// Handle length ${#var}
	if p.arithPeek() == '#' {
		p.arithAdvance()
		name_chars = []interface{}{}
		for !(p.arithAtEnd()) && (p.arithPeek() != '}') {
			name_chars = append(name_chars, p.arithAdvance())
		}
		p.arithConsume("}")
		return NewParamLength(strings.Join(name_chars, ""))
	}
	// Regular ${var} or ${var...}
	name_chars = []interface{}{}
	for !(p.arithAtEnd()) {
		ch := p.arithPeek()
		if ch == '}' {
			p.arithAdvance()
			return NewParamExpansion(strings.Join(name_chars, ""))
		}
		if isParamExpansionOp(ch) {
			// Operator follows
			break
		}
		name_chars = append(name_chars, p.arithAdvance())
	}
	name := strings.Join(name_chars, "")
	// Check for operator
	op_chars := []interface{}{}
	depth := 1
	for !(p.arithAtEnd()) && (depth > 0) {
		ch = p.arithPeek()
		if ch == '{' {
			depth += 1
			op_chars = append(op_chars, p.arithAdvance())
		} else if ch == '}' {
			depth -= 1
			if depth == 0 {
				break
			}
			op_chars = append(op_chars, p.arithAdvance())
		} else {
			op_chars = append(op_chars, p.arithAdvance())
		}
	}
	p.arithConsume("}")
	op_str := strings.Join(op_chars, "")
	// Parse the operator
	if strings.HasPrefix(op_str, ":-") {
		return NewParamExpansion(name, ":-", substring(op_str, 2, len(op_str)))
	}
	if strings.HasPrefix(op_str, ":=") {
		return NewParamExpansion(name, ":=", substring(op_str, 2, len(op_str)))
	}
	if strings.HasPrefix(op_str, ":+") {
		return NewParamExpansion(name, ":+", substring(op_str, 2, len(op_str)))
	}
	if strings.HasPrefix(op_str, ":?") {
		return NewParamExpansion(name, ":?", substring(op_str, 2, len(op_str)))
	}
	if strings.HasPrefix(op_str, ":") {
		return NewParamExpansion(name, ":", substring(op_str, 1, len(op_str)))
	}
	if strings.HasPrefix(op_str, "##") {
		return NewParamExpansion(name, "##", substring(op_str, 2, len(op_str)))
	}
	if strings.HasPrefix(op_str, "#") {
		return NewParamExpansion(name, "#", substring(op_str, 1, len(op_str)))
	}
	if strings.HasPrefix(op_str, "%%") {
		return NewParamExpansion(name, "%%", substring(op_str, 2, len(op_str)))
	}
	if strings.HasPrefix(op_str, "%") {
		return NewParamExpansion(name, "%", substring(op_str, 1, len(op_str)))
	}
	if strings.HasPrefix(op_str, "//") {
		return NewParamExpansion(name, "//", substring(op_str, 2, len(op_str)))
	}
	if strings.HasPrefix(op_str, "/") {
		return NewParamExpansion(name, "/", substring(op_str, 1, len(op_str)))
	}
	return NewParamExpansion(name, "", op_str)
}

func (p *Parser) arithParseSingleQuote() Node {
	p.arithAdvance()
	content_start := p.arithPos
	for !(p.arithAtEnd()) && (p.arithPeek() != '\'') {
		p.arithAdvance()
	}
	content := substring(p.arithSrc, content_start, p.arithPos)
	if !(p.arithConsume("'")) {
		panic(NewParseError("Unterminated single quote in arithmetic"))
	}
	return NewArithNumber(content)
}

func (p *Parser) arithParseDoubleQuote() Node {
	p.arithAdvance()
	content_start := p.arithPos
	for !(p.arithAtEnd()) && (p.arithPeek() != '"') {
		c := p.arithPeek()
		if (c == '\\') && !(p.arithAtEnd()) {
			p.arithAdvance()
			p.arithAdvance()
		} else {
			p.arithAdvance()
		}
	}
	content := substring(p.arithSrc, content_start, p.arithPos)
	if !(p.arithConsume("\"")) {
		panic(NewParseError("Unterminated double quote in arithmetic"))
	}
	return NewArithNumber(content)
}

func (p *Parser) arithParseBacktick() Node {
	p.arithAdvance()
	content_start := p.arithPos
	for !(p.arithAtEnd()) && (p.arithPeek() != '`') {
		c := p.arithPeek()
		if (c == '\\') && !(p.arithAtEnd()) {
			p.arithAdvance()
			p.arithAdvance()
		} else {
			p.arithAdvance()
		}
	}
	content := substring(p.arithSrc, content_start, p.arithPos)
	if !(p.arithConsume("`")) {
		panic(NewParseError("Unterminated backtick in arithmetic"))
	}
	// Parse the command inside
	saved_pos := p.Pos
	saved_src := p.Source
	saved_len := p.Length
	p.Source = content
	p.Pos = 0
	p.Length = len(content)
	cmd := p.ParseList(true)
	p.Source = saved_src
	p.Pos = saved_pos
	p.Length = saved_len
	return NewCommandSubstitution(cmd)
}

func (p *Parser) arithParseNumberOrVar() Node {
	p.arithSkipWs()
	chars := []interface{}{}
	c := p.arithPeek()
	// Check for number (starts with digit or base#)
	var ch interface{}
	if isDigit_h(c) {
		// Could be decimal, hex (0x), octal (0), or base#n
		for !(p.arithAtEnd()) {
			ch = p.arithPeek()
			if isAlnum_h(ch) || ((ch == '#') || (ch == '_')) {
				chars = append(chars, p.arithAdvance())
			} else {
				break
			}
		}
		return NewArithNumber(strings.Join(chars, ""))
	}
	// Variable name (starts with letter or _)
	if isAlpha_h(c) || (c == '_') {
		for !(p.arithAtEnd()) {
			ch = p.arithPeek()
			if isAlnum_h(ch) || (ch == '_') {
				chars = append(chars, p.arithAdvance())
			} else {
				break
			}
		}
		return NewArithVar(strings.Join(chars, ""))
	}
	panic(NewParseError((("Unexpected character '" + c) + "' in arithmetic expression")))
}

func (p *Parser) parseDeprecatedArithmetic() {
	if p.AtEnd() || (p.Peek() != '$') {
		return []interface{}{nil, ""}
	}
	start := p.Pos
	// Check for $[
	if ((p.Pos + 1) >= p.Length) || (p.Source[(p.Pos+1)] != '[') {
		return []interface{}{nil, ""}
	}
	p.Advance()
	p.Advance()
	// Find matching ] - need to track nested brackets
	content_start := p.Pos
	depth := 1
	for !(p.AtEnd()) && (depth > 0) {
		c := p.Peek()
		if c == '[' {
			depth += 1
			p.Advance()
		} else if c == ']' {
			depth -= 1
			if depth == 0 {
				break
			}
			p.Advance()
		} else {
			p.Advance()
		}
	}
	if p.AtEnd() || (depth != 0) {
		p.Pos = start
		return []interface{}{nil, ""}
	}
	content := substring(p.Source, content_start, p.Pos)
	p.Advance()
	text := substring(p.Source, start, p.Pos)
	return []interface{}{NewArithDeprecated(content), text}
}

func (p *Parser) parseAnsiCQuote() {
	if p.AtEnd() || (p.Peek() != '$') {
		return []interface{}{nil, ""}
	}
	if ((p.Pos + 1) >= p.Length) || (p.Source[(p.Pos+1)] != '\'') {
		return []interface{}{nil, ""}
	}
	start := p.Pos
	p.Advance()
	p.Advance()
	content_chars := []interface{}{}
	found_close := false
	for !(p.AtEnd()) {
		ch := p.Peek()
		if ch == '\'' {
			p.Advance()
			found_close = true
			break
		} else if ch == '\\' {
			// Escape sequence - include both backslash and following char in content
			content_chars = append(content_chars, p.Advance())
			if !(p.AtEnd()) {
				content_chars = append(content_chars, p.Advance())
			}
		} else {
			content_chars = append(content_chars, p.Advance())
		}
	}
	if !(found_close) {
		// Unterminated - reset and return None
		p.Pos = start
		return []interface{}{nil, ""}
	}
	text := substring(p.Source, start, p.Pos)
	content := strings.Join(content_chars, "")
	return []interface{}{NewAnsiCQuote(content), text}
}

func (p *Parser) parseLocaleString() {
	if p.AtEnd() || (p.Peek() != '$') {
		return []interface{}{nil, "", []interface{}{}}
	}
	if ((p.Pos + 1) >= p.Length) || (p.Source[(p.Pos+1)] != '"') {
		return []interface{}{nil, "", []interface{}{}}
	}
	start := p.Pos
	p.Advance()
	p.Advance()
	content_chars := []interface{}{}
	inner_parts := []interface{}{}
	found_close := false
	for !(p.AtEnd()) {
		ch := p.Peek()
		var cmdsub_result interface{}
		var cmdsub_node interface{}
		var cmdsub_text interface{}
		var param_result interface{}
		var arith_result interface{}
		var arith_node interface{}
		var param_text interface{}
		var next_ch interface{}
		var param_node interface{}
		var arith_text interface{}
		if ch == '"' {
			p.Advance()
			found_close = true
			break
		} else if (ch == '\\') && ((p.Pos + 1) < p.Length) {
			// Escape sequence (line continuation removes both)
			next_ch = p.Source[(p.Pos + 1)]
			if next_ch == '\n' {
				// Line continuation - skip both backslash and newline
				p.Advance()
				p.Advance()
			} else {
				content_chars = append(content_chars, p.Advance())
				content_chars = append(content_chars, p.Advance())
			}
		} else if (ch == '$') && ((p.Pos + 2) < p.Length) && (p.Source[(p.Pos+1)] == '(') && (p.Source[(p.Pos+2)] == '(') {
			// Handle arithmetic expansion $((...))
			arith_result = p.parseArithmeticExpansion()
			arith_node = arith_result[0]
			arith_text = arith_result[1]
			if arith_node {
				inner_parts = append(inner_parts, arith_node)
				content_chars = append(content_chars, arith_text)
			} else {
				// Not arithmetic - try command substitution
				cmdsub_result = p.parseCommandSubstitution()
				cmdsub_node = cmdsub_result[0]
				cmdsub_text = cmdsub_result[1]
				if cmdsub_node {
					inner_parts = append(inner_parts, cmdsub_node)
					content_chars = append(content_chars, cmdsub_text)
				} else {
					content_chars = append(content_chars, p.Advance())
				}
			}
		} else if (ch == '$') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(') {
			// Handle command substitution $(...)
			cmdsub_result = p.parseCommandSubstitution()
			cmdsub_node = cmdsub_result[0]
			cmdsub_text = cmdsub_result[1]
			if cmdsub_node {
				inner_parts = append(inner_parts, cmdsub_node)
				content_chars = append(content_chars, cmdsub_text)
			} else {
				content_chars = append(content_chars, p.Advance())
			}
		} else if ch == '$' {
			// Handle parameter expansion
			param_result = p.parseParamExpansion()
			param_node = param_result[0]
			param_text = param_result[1]
			if param_node {
				inner_parts = append(inner_parts, param_node)
				content_chars = append(content_chars, param_text)
			} else {
				content_chars = append(content_chars, p.Advance())
			}
		} else if ch == '`' {
			// Handle backtick command substitution
			cmdsub_result = p.parseBacktickSubstitution()
			cmdsub_node = cmdsub_result[0]
			cmdsub_text = cmdsub_result[1]
			if cmdsub_node {
				inner_parts = append(inner_parts, cmdsub_node)
				content_chars = append(content_chars, cmdsub_text)
			} else {
				content_chars = append(content_chars, p.Advance())
			}
		} else {
			content_chars = append(content_chars, p.Advance())
		}
	}
	if !(found_close) {
		// Unterminated - reset and return None
		p.Pos = start
		return []interface{}{nil, "", []interface{}{}}
	}
	content := strings.Join(content_chars, "")
	// Reconstruct text from parsed content (handles line continuation removal)
	text := (("$\"" + content) + "\"")
	return []interface{}{NewLocaleString(content), text, inner_parts}
}

func (p *Parser) parseParamExpansion() {
	if p.AtEnd() || (p.Peek() != '$') {
		return []interface{}{nil, ""}
	}
	start := p.Pos
	p.Advance()
	if p.AtEnd() {
		p.Pos = start
		return []interface{}{nil, ""}
	}
	ch := p.Peek()
	// Braced expansion ${...}
	if ch == '{' {
		p.Advance()
		return p.parseBracedParam(start)
	}
	// Simple expansion $var or $special
	// Special parameters: ?$!#@*-0-9
	var text string
	if isSpecialParamOrDigit(ch) || (ch == '#') {
		p.Advance()
		text = substring(p.Source, start, p.Pos)
		return []interface{}{NewParamExpansion(ch), text}
	}
	// Variable name [a-zA-Z_][a-zA-Z0-9_]*
	var name_start interface{}
	var name string
	if isAlpha_h(ch) || (ch == '_') {
		name_start = p.Pos
		for !(p.AtEnd()) {
			c := p.Peek()
			if isAlnum_h(c) || (c == '_') {
				p.Advance()
			} else {
				break
			}
		}
		name = substring(p.Source, name_start, p.Pos)
		text = substring(p.Source, start, p.Pos)
		return []interface{}{NewParamExpansion(name), text}
	}
	// Not a valid expansion, restore position
	p.Pos = start
	return []interface{}{nil, ""}
}

func (p *Parser) parseBracedParam(start int) {
	if p.AtEnd() {
		p.Pos = start
		return []interface{}{nil, ""}
	}
	ch := p.Peek()
	// ${#param} - length
	var param interface{}
	var text string
	if ch == '#' {
		p.Advance()
		param = p.consumeParamName()
		if param && !(p.AtEnd()) && (p.Peek() == '}') {
			p.Advance()
			text = substring(p.Source, start, p.Pos)
			return []interface{}{NewParamLength(param), text}
		}
		p.Pos = start
		return []interface{}{nil, ""}
	}
	// ${!param} or ${!param<op><arg>} - indirect
	var arg_chars interface{}
	var op string
	var depth int
	var suffix interface{}
	var arg Node
	if ch == '!' {
		p.Advance()
		param = p.consumeParamName()
		if param {
			// Skip optional whitespace before closing brace
			for !(p.AtEnd()) && isWhitespaceNoNewline(p.Peek()) {
				p.Advance()
			}
			if !(p.AtEnd()) && (p.Peek() == '}') {
				p.Advance()
				text = substring(p.Source, start, p.Pos)
				return []interface{}{NewParamIndirect(param), text}
			}
			// ${!prefix@} and ${!prefix*} are prefix matching (lists variable names)
			// These are NOT operators - the @/* is part of the indirect form
			if !(p.AtEnd()) && isAtOrStar(p.Peek()) {
				suffix = p.Advance()
				for !(p.AtEnd()) && isWhitespaceNoNewline(p.Peek()) {
					p.Advance()
				}
				if !(p.AtEnd()) && (p.Peek() == '}') {
					p.Advance()
					text = substring(p.Source, start, p.Pos)
					return []interface{}{NewParamIndirect((param + suffix)), text}
				}
				// Not a valid prefix match, reset
				p.Pos = start
				return []interface{}{nil, ""}
			}
			// Check for operator (e.g., ${!##} = indirect of # with # op)
			op = p.consumeParamOperator()
			if op != nil {
				// Parse argument until closing brace
				arg_chars = []interface{}{}
				depth = 1
				for !(p.AtEnd()) && (depth > 0) {
					c := p.Peek()
					if (c == '$') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '{') {
						depth += 1
						arg_chars = append(arg_chars, p.Advance())
						arg_chars = append(arg_chars, p.Advance())
					} else if c == '}' {
						depth -= 1
						if depth > 0 {
							arg_chars = append(arg_chars, p.Advance())
						}
					} else if c == '\\' {
						arg_chars = append(arg_chars, p.Advance())
						if !(p.AtEnd()) {
							arg_chars = append(arg_chars, p.Advance())
						}
					} else {
						arg_chars = append(arg_chars, p.Advance())
					}
				}
				if depth == 0 {
					p.Advance()
					arg = strings.Join(arg_chars, "")
					text = substring(p.Source, start, p.Pos)
					return []interface{}{NewParamIndirect(param, op, arg), text}
				}
			}
		}
		p.Pos = start
		return []interface{}{nil, ""}
	}
	// ${param} or ${param<op><arg>}
	param = p.consumeParamName()
	var content_start interface{}
	var content interface{}
	if !(param) {
		// Unknown syntax like ${(M)...} (zsh) - consume until matching }
		// Bash accepts these syntactically but fails at runtime
		depth = 1
		content_start = p.Pos
		for !(p.AtEnd()) && (depth > 0) {
			c = p.Peek()
			if c == '{' {
				depth += 1
				p.Advance()
			} else if c == '}' {
				depth -= 1
				if depth == 0 {
					break
				}
				p.Advance()
			} else if c == '\\' {
				p.Advance()
				if !(p.AtEnd()) {
					p.Advance()
				}
			} else {
				p.Advance()
			}
		}
		if depth == 0 {
			content = substring(p.Source, content_start, p.Pos)
			p.Advance()
			text = substring(p.Source, start, p.Pos)
			return []interface{}{NewParamExpansion(content), text}
		}
		p.Pos = start
		return []interface{}{nil, ""}
	}
	if p.AtEnd() {
		p.Pos = start
		return []interface{}{nil, ""}
	}
	// Check for closing brace (simple expansion)
	if p.Peek() == '}' {
		p.Advance()
		text = substring(p.Source, start, p.Pos)
		return []interface{}{NewParamExpansion(param), text}
	}
	// Parse operator
	op = p.consumeParamOperator()
	if op == nil {
		// Unknown operator - bash still parses these (fails at runtime)
		// Treat the current char as the operator
		op = p.Advance()
	}
	// Parse argument (everything until closing brace)
	// Track quote state and nesting
	arg_chars = []interface{}{}
	depth = 1
	in_single_quote := false
	in_double_quote := false
	for !(p.AtEnd()) && (depth > 0) {
		c = p.Peek()
		// Single quotes - no escapes, just scan to closing quote
		var paren_depth interface{}
		var bc interface{}
		var next_c interface{}
		var pc interface{}
		if (c == '\'') && !(in_double_quote) {
			if in_single_quote {
				in_single_quote = false
			} else {
				in_single_quote = true
			}
			arg_chars = append(arg_chars, p.Advance())
		} else if (c == '"') && !(in_single_quote) {
			// Double quotes - toggle state
			in_double_quote = !(in_double_quote)
			arg_chars = append(arg_chars, p.Advance())
		} else if (c == '\\') && !(in_single_quote) {
			// Escape - skip next char (line continuation removes both)
			if ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '\n') {
				// Line continuation - skip both backslash and newline
				p.Advance()
				p.Advance()
			} else {
				arg_chars = append(arg_chars, p.Advance())
				if !(p.AtEnd()) {
					arg_chars = append(arg_chars, p.Advance())
				}
			}
		} else if (c == '$') && !(in_single_quote) && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '{') {
			// Nested ${...} - increase depth (outside single quotes)
			depth += 1
			arg_chars = append(arg_chars, p.Advance())
			arg_chars = append(arg_chars, p.Advance())
		} else if (c == '$') && !(in_single_quote) && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(') {
			// Command substitution $(...) - scan to matching )
			arg_chars = append(arg_chars, p.Advance())
			arg_chars = append(arg_chars, p.Advance())
			paren_depth = 1
			for !(p.AtEnd()) && (paren_depth > 0) {
				pc = p.Peek()
				if pc == '(' {
					paren_depth += 1
				} else if pc == ')' {
					paren_depth -= 1
				} else if pc == '\\' {
					arg_chars = append(arg_chars, p.Advance())
					if !(p.AtEnd()) {
						arg_chars = append(arg_chars, p.Advance())
					}
					continue
				}
				arg_chars = append(arg_chars, p.Advance())
			}
		} else if (c == '`') && !(in_single_quote) {
			// Backtick command substitution - scan to matching `
			arg_chars = append(arg_chars, p.Advance())
			for !(p.AtEnd()) && (p.Peek() != '`') {
				bc = p.Peek()
				if (bc == '\\') && ((p.Pos + 1) < p.Length) {
					next_c = p.Source[(p.Pos + 1)]
					if isEscapeCharInDquote(next_c) {
						arg_chars = append(arg_chars, p.Advance())
					}
				}
				arg_chars = append(arg_chars, p.Advance())
			}
			if !(p.AtEnd()) {
				arg_chars = append(arg_chars, p.Advance())
			}
		} else if c == '}' {
			// Closing brace - handle depth for nested ${...}
			if in_single_quote {
				// Inside single quotes, } is literal
				arg_chars = append(arg_chars, p.Advance())
			} else if in_double_quote {
				// Inside double quotes, } can close nested ${...}
				if depth > 1 {
					depth -= 1
					arg_chars = append(arg_chars, p.Advance())
				} else {
					// Literal } in double quotes (not closing nested)
					arg_chars = append(arg_chars, p.Advance())
				}
			} else {
				depth -= 1
				if depth > 0 {
					arg_chars = append(arg_chars, p.Advance())
				}
			}
		} else {
			arg_chars = append(arg_chars, p.Advance())
		}
	}
	if depth != 0 {
		p.Pos = start
		return []interface{}{nil, ""}
	}
	p.Advance()
	arg = strings.Join(arg_chars, "")
	// Reconstruct text from parsed components (handles line continuation removal)
	text = (((("${" + param) + op) + arg) + "}")
	return []interface{}{NewParamExpansion(param, op, arg), text}
}

func (p *Parser) consumeParamName() string {
	if p.AtEnd() {
		return nil
	}
	ch := p.Peek()
	// Special parameters
	if isSpecialParam(ch) {
		p.Advance()
		return ch
	}
	// Digits (positional params)
	var name_chars interface{}
	if isDigit_h(ch) {
		name_chars = []interface{}{}
		for !(p.AtEnd()) && isDigit_h(p.Peek()) {
			name_chars = append(name_chars, p.Advance())
		}
		return strings.Join(name_chars, "")
	}
	// Variable name
	var sc interface{}
	var bracket_depth interface{}
	if isAlpha_h(ch) || (ch == '_') {
		name_chars = []interface{}{}
		for !(p.AtEnd()) {
			c := p.Peek()
			if isAlnum_h(c) || (c == '_') {
				name_chars = append(name_chars, p.Advance())
			} else if c == '[' {
				// Array subscript - track bracket depth
				name_chars = append(name_chars, p.Advance())
				bracket_depth = 1
				for !(p.AtEnd()) && (bracket_depth > 0) {
					sc = p.Peek()
					if sc == '[' {
						bracket_depth += 1
					} else if sc == ']' {
						bracket_depth -= 1
						if bracket_depth == 0 {
							break
						}
					}
					name_chars = append(name_chars, p.Advance())
				}
				if !(p.AtEnd()) && (p.Peek() == ']') {
					name_chars = append(name_chars, p.Advance())
				}
				break
			} else {
				break
			}
		}
		if name_chars {
			return strings.Join(name_chars, "")
		} else {
			return nil
		}
	}
	return nil
}

func (p *Parser) consumeParamOperator() string {
	if p.AtEnd() {
		return nil
	}
	ch := p.Peek()
	// Operators with optional colon prefix: :- := :? :+
	var next_ch interface{}
	if ch == ':' {
		p.Advance()
		if p.AtEnd() {
			return ":"
		}
		next_ch = p.Peek()
		if isSimpleParamOp(next_ch) {
			p.Advance()
			return (":" + next_ch)
		}
		// Just : (substring)
		return ":"
	}
	// Operators without colon: - = ? +
	if isSimpleParamOp(ch) {
		p.Advance()
		return ch
	}
	// Pattern removal: # ## % %%
	if ch == '#' {
		p.Advance()
		if !(p.AtEnd()) && (p.Peek() == '#') {
			p.Advance()
			return "##"
		}
		return "#"
	}
	if ch == '%' {
		p.Advance()
		if !(p.AtEnd()) && (p.Peek() == '%') {
			p.Advance()
			return "%%"
		}
		return "%"
	}
	// Substitution: / // /# /%
	if ch == '/' {
		p.Advance()
		if !(p.AtEnd()) {
			next_ch = p.Peek()
			if next_ch == '/' {
				p.Advance()
				return "//"
			} else if next_ch == '#' {
				p.Advance()
				return "/#"
			} else if next_ch == '%' {
				p.Advance()
				return "/%"
			}
		}
		return "/"
	}
	// Case modification: ^ ^^ , ,,
	if ch == '^' {
		p.Advance()
		if !(p.AtEnd()) && (p.Peek() == '^') {
			p.Advance()
			return "^^"
		}
		return "^"
	}
	if ch == ',' {
		p.Advance()
		if !(p.AtEnd()) && (p.Peek() == ',') {
			p.Advance()
			return ",,"
		}
		return ","
	}
	// Transformation: @
	if ch == '@' {
		p.Advance()
		return "@"
	}
	return nil
}

func (p *Parser) ParseRedirect() Node {
	p.SkipWhitespace()
	if p.AtEnd() {
		return nil
	}
	start := p.Pos
	fd := nil
	varfd := nil
	// Check for variable fd {varname} or {varname[subscript]} before redirect
	var varname_chars interface{}
	var ch interface{}
	var saved interface{}
	if p.Peek() == '{' {
		saved = p.Pos
		p.Advance()
		varname_chars = []interface{}{}
		for !(p.AtEnd()) && ((p.Peek() != '}') && !(isRedirectChar(p.Peek()))) {
			ch = p.Peek()
			if isAlnum_h(ch) || ((ch == '_') || (ch == '[') || (ch == ']')) {
				varname_chars = append(varname_chars, p.Advance())
			} else {
				break
			}
		}
		if !(p.AtEnd()) && (p.Peek() == '}') && varname_chars {
			p.Advance()
			varfd = strings.Join(varname_chars, "")
		} else {
			// Not a valid variable fd, restore
			p.Pos = saved
		}
	}
	// Check for optional fd number before redirect (if no varfd)
	var fd_chars interface{}
	if (varfd == nil) && p.Peek() && isDigit_h(p.Peek()) {
		fd_chars = []interface{}{}
		for !(p.AtEnd()) && isDigit_h(p.Peek()) {
			fd_chars = append(fd_chars, p.Advance())
		}
		fd = toInt(strings.Join(fd_chars, ""))
	}
	ch = p.Peek()
	// Handle &> and &>> (redirect both stdout and stderr)
	// Note: &> does NOT take a preceding fd number. If we consumed digits,
	// they should be a separate word, not an fd. E.g., "2&>1" is command "2"
	// with redirect "&> 1", not fd 2 redirected.
	var op string
	var target interface{}
	if (ch == '&') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '>') {
		if fd != nil {
			// We consumed digits that should be a word, not an fd
			// Restore position and let parse_word handle them
			p.Pos = start
			return nil
		}
		p.Advance()
		p.Advance()
		if !(p.AtEnd()) && (p.Peek() == '>') {
			p.Advance()
			op = "&>>"
		} else {
			op = "&>"
		}
		p.SkipWhitespace()
		target = p.ParseWord()
		if target == nil {
			panic(NewParseError(("Expected target for redirect " + op)))
		}
		return NewRedirect(op, target)
	}
	if (ch == nil) || !(isRedirectChar(ch)) {
		// Not a redirect, restore position
		p.Pos = start
		return nil
	}
	// Check for process substitution <(...) or >(...) - not a redirect
	// Only treat as redirect if there's a space before ( or an fd number
	if (fd == nil) && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(') {
		// This is a process substitution, not a redirect
		p.Pos = start
		return nil
	}
	// Parse the redirect operator
	op = p.Advance()
	// Check for multi-char operators
	strip_tabs := false
	var next_ch interface{}
	if !(p.AtEnd()) {
		next_ch = p.Peek()
		if (op == '>') && (next_ch == '>') {
			p.Advance()
			op = ">>"
		} else if (op == '<') && (next_ch == '<') {
			p.Advance()
			if !(p.AtEnd()) && (p.Peek() == '<') {
				p.Advance()
				op = "<<<"
			} else if !(p.AtEnd()) && (p.Peek() == '-') {
				p.Advance()
				op = "<<"
				strip_tabs = true
			} else {
				op = "<<"
			}
		} else if (op == '<') && (next_ch == '>') {
			// Handle <> (read-write)
			p.Advance()
			op = "<>"
		} else if (op == '>') && (next_ch == '|') {
			// Handle >| (noclobber override)
			p.Advance()
			op = ">|"
		} else if (fd == nil) && (varfd == nil) && (op == '>') && (next_ch == '&') {
			// Only consume >& or <& as operators if NOT followed by a digit or -
			// (>&2 should be > with target &2, not >& with target 2)
			// (>&- should be > with target &-, not >& with target -)
			// Peek ahead to see if there's a digit or - after &
			if ((p.Pos + 1) >= p.Length) || !(isDigitOrDash(p.Source[(p.Pos + 1)])) {
				p.Advance()
				op = ">&"
			}
		} else if (fd == nil) && (varfd == nil) && (op == '<') && (next_ch == '&') {
			if ((p.Pos + 1) >= p.Length) || !(isDigitOrDash(p.Source[(p.Pos + 1)])) {
				p.Advance()
				op = "<&"
			}
		}
	}
	// Handle here document
	if op == "<<" {
		return p.parseHeredoc(fd, strip_tabs)
	}
	// Combine fd or varfd with operator if present
	if varfd != nil {
		op = ((("{" + varfd) + "}") + op)
	} else if fd != nil {
		op = (fmt.Sprintf("%v", fd) + op)
	}
	p.SkipWhitespace()
	// Handle fd duplication targets like &1, &2, &-, &10-, &$var
	var fd_target interface{}
	var inner_word interface{}
	if !(p.AtEnd()) && (p.Peek() == '&') {
		p.Advance()
		// Parse the fd number or - for close, including move syntax like &10-
		if !(p.AtEnd()) && (isDigit_h(p.Peek()) || (p.Peek() == '-')) {
			fd_chars = []interface{}{}
			for !(p.AtEnd()) && isDigit_h(p.Peek()) {
				fd_chars = append(fd_chars, p.Advance())
			}
			if fd_chars {
				fd_target = strings.Join(fd_chars, "")
			} else {
				fd_target = ""
			}
			// Handle just - for close, or N- for move syntax
			if !(p.AtEnd()) && (p.Peek() == '-') {
				fd_target += p.Advance()
			}
			target = NewWord(("&" + fd_target))
		} else {
			// Could be &$var or &word - parse word and prepend &
			inner_word = p.ParseWord()
			if inner_word != nil {
				target = NewWord(("&" + inner_word.Value))
				target.Parts = inner_word.Parts
			} else {
				panic(NewParseError(("Expected target for redirect " + op)))
			}
		}
	} else {
		target = p.ParseWord()
	}
	if target == nil {
		panic(NewParseError(("Expected target for redirect " + op)))
	}
	return NewRedirect(op, target)
}

func (p *Parser) parseHeredoc(fd int, strip_tabs bool) HereDoc {
	p.SkipWhitespace()
	// Parse the delimiter, handling quoting (can be mixed like 'EOF'"2")
	quoted := false
	delimiter_chars := []interface{}{}
	for !(p.AtEnd()) && !(isMetachar(p.Peek())) {
		ch := p.Peek()
		var depth int
		var next_ch interface{}
		if ch == '"' {
			quoted = true
			p.Advance()
			for !(p.AtEnd()) && (p.Peek() != '"') {
				delimiter_chars = append(delimiter_chars, p.Advance())
			}
			if !(p.AtEnd()) {
				p.Advance()
			}
		} else if ch == '\'' {
			quoted = true
			p.Advance()
			for !(p.AtEnd()) && (p.Peek() != '\'') {
				delimiter_chars = append(delimiter_chars, p.Advance())
			}
			if !(p.AtEnd()) {
				p.Advance()
			}
		} else if ch == '\\' {
			p.Advance()
			if !(p.AtEnd()) {
				next_ch = p.Peek()
				if next_ch == '\n' {
					// Backslash-newline: continue delimiter on next line
					p.Advance()
				} else {
					// Regular escape - quotes the next char
					quoted = true
					delimiter_chars = append(delimiter_chars, p.Advance())
				}
			}
		} else if (ch == '$') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(') {
			// Command substitution embedded in delimiter
			delimiter_chars = append(delimiter_chars, p.Advance())
			delimiter_chars = append(delimiter_chars, p.Advance())
			depth = 1
			for !(p.AtEnd()) && (depth > 0) {
				c := p.Peek()
				if c == '(' {
					depth += 1
				} else if c == ')' {
					depth -= 1
				}
				delimiter_chars = append(delimiter_chars, p.Advance())
			}
		} else {
			delimiter_chars = append(delimiter_chars, p.Advance())
		}
	}
	delimiter := strings.Join(delimiter_chars, "")
	// Find the end of the current line (command continues until newline)
	// We need to mark where the heredoc content starts
	// Must be quote-aware - newlines inside quoted strings don't end the line
	line_end := p.Pos
	for (line_end < p.Length) && (p.Source[line_end] != '\n') {
		ch = p.Source[line_end]
		if ch == '\'' {
			// Single-quoted string - skip to closing quote (no escapes)
			line_end += 1
			for (line_end < p.Length) && (p.Source[line_end] != '\'') {
				line_end += 1
			}
		} else if ch == '"' {
			// Double-quoted string - skip to closing quote (with escapes)
			line_end += 1
			for (line_end < p.Length) && (p.Source[line_end] != '"') {
				if (p.Source[line_end] == '\\') && ((line_end + 1) < p.Length) {
					line_end += 2
				} else {
					line_end += 1
				}
			}
		} else if (ch == '\\') && ((line_end + 1) < p.Length) {
			// Backslash escape - skip both chars
			line_end += 2
			continue
		}
		line_end += 1
	}
	// Find heredoc content starting position
	// If there's already a pending heredoc, this one's content starts after that
	var content_start interface{}
	if (p.pendingHeredocEnd != nil) && (p.pendingHeredocEnd > line_end) {
		content_start = p.pendingHeredocEnd
	} else if line_end < p.Length {
		content_start = (line_end + 1)
	} else {
		content_start = p.Length
	}
	// Find the delimiter line
	content_lines := []interface{}{}
	scan_pos := content_start
	for scan_pos < p.Length {
		// Find end of current line
		line_start := scan_pos
		line_end = scan_pos
		for (line_end < p.Length) && (p.Source[line_end] != '\n') {
			line_end += 1
		}
		line := substring(p.Source, line_start, line_end)
		// For unquoted heredocs, process backslash-newline before checking delimiter
		// Join continued lines to check the full logical line against delimiter
		var next_line_start interface{}
		if !(quoted) {
			for strings.HasSuffix(line, "\\") && (line_end < p.Length) {
				// Continue to next line
				line = substring(line, 0, (len(line) - 1))
				line_end += 1
				next_line_start = line_end
				for (line_end < p.Length) && (p.Source[line_end] != '\n') {
					line_end += 1
				}
				line = (line + substring(p.Source, next_line_start, line_end))
			}
		}
		// Check if this line is the delimiter
		check_line := line
		if strip_tabs != "" {
			check_line = strings.TrimLeft(line, "\t")
		}
		if check_line == delimiter {
			// Found the end - update parser position past the heredoc
			// We need to consume the heredoc content from the input
			// But we can't do that here because we haven't finished parsing the command line
			// Store the heredoc info and let the command parser handle it
			break
		}
		// Add line to content (with newline, since we consumed continuations above)
		if strip_tabs != "" {
			line = strings.TrimLeft(line, "\t")
		}
		content_lines = append(content_lines, (line + "\n"))
		// Move past the newline
		if line_end < p.Length {
			scan_pos = (line_end + 1)
		} else {
			scan_pos = p.Length
		}
	}
	// Join content (newlines already included per line)
	content := strings.Join(content_lines, "")
	// Store the position where heredoc content ends so we can skip it later
	// line_end points to the end of the delimiter line (after any continuations)
	heredoc_end := line_end
	if heredoc_end < p.Length {
		heredoc_end += 1
	}
	// Register this heredoc's end position
	if p.pendingHeredocEnd == nil {
		p.pendingHeredocEnd = heredoc_end
	} else {
		p.pendingHeredocEnd = max(p.pendingHeredocEnd, heredoc_end)
	}
	return NewHereDoc(delimiter, content, strip_tabs, quoted, fd)
}

func (p *Parser) ParseCommand() Node {
	words := []interface{}{}
	redirects := []interface{}{}
	for true {
		p.SkipWhitespace()
		if p.AtEnd() {
			break
		}
		ch := p.Peek()
		// Check for command terminators, but &> and &>> are redirects, not terminators
		if isListTerminator(ch) {
			break
		}
		if (ch == '&') && !(((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '>')) {
			break
		}
		// } is only a terminator at command position (closing a brace group)
		// In argument position, } is just a regular word
		var next_pos interface{}
		if (p.Peek() == '}') && !(words) {
			// Check if } would be a standalone word (next char is whitespace/meta/EOF)
			next_pos = (p.Pos + 1)
			if (next_pos >= p.Length) || isWordEndContext(p.Source[next_pos]) {
				break
			}
		}
		// Try to parse a redirect first
		redirect := p.ParseRedirect()
		if redirect != nil {
			redirects = append(redirects, redirect)
			continue
		}
		// Otherwise parse a word
		// Allow array assignments like a[1 + 2]= in prefix position (before first non-assignment)
		// Check if all previous words were assignments (contain = not inside quotes)
		all_assignments := true
		for _, w := range words {
			if !(p.isAssignmentWord(w)) {
				all_assignments = false
				break
			}
		}
		word := p.ParseWord()
		if word == nil {
			break
		}
		words = append(words, word)
	}
	if !(words) && !(redirects) {
		return nil
	}
	return NewCommand(words, redirects)
}

func (p *Parser) ParseSubshell() Node {
	p.SkipWhitespace()
	if p.AtEnd() || (p.Peek() != '(') {
		return nil
	}
	p.Advance()
	body := p.ParseList(true)
	if body == nil {
		panic(NewParseError("Expected command in subshell"))
	}
	p.SkipWhitespace()
	if p.AtEnd() || (p.Peek() != ')') {
		panic(NewParseError("Expected ) to close subshell"))
	}
	p.Advance()
	// Collect trailing redirects
	redirects := []interface{}{}
	for true {
		p.SkipWhitespace()
		redirect := p.ParseRedirect()
		if redirect == nil {
			break
		}
		redirects = append(redirects, redirect)
	}
	if redirects {
		return NewSubshell(body, redirects)
	} else {
		return NewSubshell(body, nil)
	}
}

func (p *Parser) ParseArithmeticCommand() Node {
	p.SkipWhitespace()
	// Check for ((
	if p.AtEnd() || (p.Peek() != '(') || ((p.Pos + 1) >= p.Length) || (p.Source[(p.Pos+1)] != '(') {
		return nil
	}
	saved_pos := p.Pos
	p.Advance()
	p.Advance()
	// Find matching )) - track nested parens
	// Must be )) with no space between - ') )' is nested subshells
	content_start := p.Pos
	depth := 1
	for !(p.AtEnd()) && (depth > 0) {
		c := p.Peek()
		if c == '(' {
			depth += 1
			p.Advance()
		} else if c == ')' {
			// Check for )) (must be consecutive, no space)
			if (depth == 1) && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == ')') {
				// Found the closing ))
				break
			}
			depth -= 1
			if depth == 0 {
				// Closed with ) but next isn't ) - this is nested subshells, not arithmetic
				p.Pos = saved_pos
				return nil
			}
			p.Advance()
		} else {
			p.Advance()
		}
	}
	if p.AtEnd() || (depth != 1) {
		// Didn't find )) - might be nested subshells or malformed
		p.Pos = saved_pos
		return nil
	}
	content := substring(p.Source, content_start, p.Pos)
	p.Advance()
	p.Advance()
	// Parse the arithmetic expression
	expr := p.parseArithExpr(content)
	// Collect trailing redirects
	redirects := []interface{}{}
	for true {
		p.SkipWhitespace()
		redirect := p.ParseRedirect()
		if redirect == nil {
			break
		}
		redirects = append(redirects, redirect)
	}
	redir_arg := nil
	if redirects {
		redir_arg = redirects
	}
	return NewArithmeticCommand(expr, redir_arg)
}

func (p *Parser) ParseConditionalExpr() Node {
	// Unary operators for [[ ]] conditionals
	// Binary operators for [[ ]] conditionals
	p.SkipWhitespace()
	// Check for [[
	if p.AtEnd() || (p.Peek() != '[') || ((p.Pos + 1) >= p.Length) || (p.Source[(p.Pos+1)] != '[') {
		return nil
	}
	p.Advance()
	p.Advance()
	// Parse the conditional expression body
	body := p.parseCondOr()
	// Skip whitespace before ]]
	for !(p.AtEnd()) && isWhitespaceNoNewline(p.Peek()) {
		p.Advance()
	}
	// Expect ]]
	if p.AtEnd() || (p.Peek() != ']') || ((p.Pos + 1) >= p.Length) || (p.Source[(p.Pos+1)] != ']') {
		panic(NewParseError("Expected ]] to close conditional expression"))
	}
	p.Advance()
	p.Advance()
	// Collect trailing redirects
	redirects := []interface{}{}
	for true {
		p.SkipWhitespace()
		redirect := p.ParseRedirect()
		if redirect == nil {
			break
		}
		redirects = append(redirects, redirect)
	}
	redir_arg := nil
	if redirects {
		redir_arg = redirects
	}
	return NewConditionalExpr(body, redir_arg)
}

func (p *Parser) condSkipWhitespace() {
	for !(p.AtEnd()) {
		if isWhitespaceNoNewline(p.Peek()) {
			p.Advance()
		} else if (p.Peek() == '\\') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '\n') {
			p.Advance()
			p.Advance()
		} else if p.Peek() == '\n' {
			// Bare newline is also allowed inside [[ ]]
			p.Advance()
		} else {
			break
		}
	}
}

func (p *Parser) condAtEnd() bool {
	return (p.AtEnd() || ((p.Peek() == ']') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == ']')))
}

func (p *Parser) parseCondOr() Node {
	p.condSkipWhitespace()
	left := p.parseCondAnd()
	p.condSkipWhitespace()
	var right interface{}
	if !(p.condAtEnd()) && (p.Peek() == '|') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '|') {
		p.Advance()
		p.Advance()
		right = p.parseCondOr()
		return NewCondOr(left, right)
	}
	return left
}

func (p *Parser) parseCondAnd() Node {
	p.condSkipWhitespace()
	left := p.parseCondTerm()
	p.condSkipWhitespace()
	var right interface{}
	if !(p.condAtEnd()) && (p.Peek() == '&') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '&') {
		p.Advance()
		p.Advance()
		right = p.parseCondAnd()
		return NewCondAnd(left, right)
	}
	return left
}

func (p *Parser) parseCondTerm() Node {
	p.condSkipWhitespace()
	if p.condAtEnd() {
		panic(NewParseError("Unexpected end of conditional expression"))
	}
	// Negation: ! term
	var operand interface{}
	if p.Peek() == '!' {
		// Check it's not != operator (need whitespace after !)
		if ((p.Pos + 1) < p.Length) && !(isWhitespaceNoNewline(p.Source[(p.Pos + 1)])) {
		} else {
			p.Advance()
			operand = p.parseCondTerm()
			return NewCondNot(operand)
		}
	}
	// Parenthesized group: ( or_expr )
	if p.Peek() == '(' {
		p.Advance()
		inner := p.parseCondOr()
		p.condSkipWhitespace()
		if p.AtEnd() || (p.Peek() != ')') {
			panic(NewParseError("Expected ) in conditional expression"))
		}
		p.Advance()
		return NewCondParen(inner)
	}
	// Parse first word
	word1 := p.parseCondWord()
	if word1 == nil {
		panic(NewParseError("Expected word in conditional expression"))
	}
	p.condSkipWhitespace()
	// Check if word1 is a unary operator
	if isCondUnaryOp(word1.Value) {
		// Unary test: -f file
		operand = p.parseCondWord()
		if operand == nil {
			panic(NewParseError(("Expected operand after " + word1.Value)))
		}
		return NewUnaryTest(word1.Value, operand)
	}
	// Check if next token is a binary operator
	var op_word interface{}
	var op string
	var saved_pos interface{}
	var word2 interface{}
	if !(p.condAtEnd()) && ((p.Peek() != '&') && (p.Peek() != '|') && (p.Peek() != ')')) {
		// Handle < and > as binary operators (they terminate words)
		// But not <( or >( which are process substitution
		if isRedirectChar(p.Peek()) && !(((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(')) {
			op = p.Advance()
			p.condSkipWhitespace()
			word2 = p.parseCondWord()
			if word2 == nil {
				panic(NewParseError(("Expected operand after " + op)))
			}
			return NewBinaryTest(op, word1, word2)
		}
		// Peek at next word to see if it's a binary operator
		saved_pos = p.Pos
		op_word = p.parseCondWord()
		if op_word && isCondBinaryOp(op_word.Value) {
			// Binary test: word1 op word2
			p.condSkipWhitespace()
			// For =~ operator, the RHS is a regex where ( ) are grouping, not conditional grouping
			if op_word.Value == "=~" {
				word2 = p.parseCondRegexWord()
			} else {
				word2 = p.parseCondWord()
			}
			if word2 == nil {
				panic(NewParseError(("Expected operand after " + op_word.Value)))
			}
			return NewBinaryTest(op_word.Value, word1, word2)
		} else {
			// Not a binary op, restore position
			p.Pos = saved_pos
		}
	}
	// Bare word: implicit -n test
	return NewUnaryTest("-n", word1)
}

func (p *Parser) parseCondWord() Node {
	p.condSkipWhitespace()
	if p.condAtEnd() {
		return nil
	}
	// Check for special tokens that aren't words
	c := p.Peek()
	if isParen(c) {
		return nil
	}
	// Note: ! alone is handled by _parse_cond_term() as negation operator
	// Here we allow ! as a word so it can be used as pattern in binary tests
	if (c == '&') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '&') {
		return nil
	}
	if (c == '|') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '|') {
		return nil
	}
	start := p.Pos
	chars := []interface{}{}
	parts := []interface{}{}
	for !(p.AtEnd()) {
		ch := p.Peek()
		// End of conditional
		if (ch == ']') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == ']') {
			break
		}
		// Word terminators in conditionals
		if isWhitespaceNoNewline(ch) {
			break
		}
		// < and > are string comparison operators in [[ ]], terminate words
		// But <(...) and >(...) are process substitution - don't break
		if isRedirectChar(ch) && !(((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(')) {
			break
		}
		// ( and ) end words unless part of extended glob: @(...), ?(...), *(...), +(...), !(...)
		var depth int
		if ch == '(' {
			// Check if this is an extended glob (preceded by @, ?, *, +, or !)
			if chars && isExtglobPrefix(chars[(len(chars)-1)]) {
				// Extended glob - consume the parenthesized content
				chars = append(chars, p.Advance())
				depth = 1
				for !(p.AtEnd()) && (depth > 0) {
					c = p.Peek()
					if c == '(' {
						depth += 1
					} else if c == ')' {
						depth -= 1
					}
					chars = append(chars, p.Advance())
				}
				continue
			} else {
				break
			}
		}
		if ch == ')' {
			break
		}
		if (ch == '&') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '&') {
			break
		}
		if (ch == '|') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '|') {
			break
		}
		// Single-quoted string
		var cmdsub_result interface{}
		var cmdsub_node interface{}
		var cmdsub_text interface{}
		var param_result interface{}
		var next_c interface{}
		var procsub_node interface{}
		var arith_result interface{}
		var arith_node interface{}
		var param_text interface{}
		var procsub_text interface{}
		var procsub_result interface{}
		var param_node interface{}
		var arith_text interface{}
		if ch == '\'' {
			p.Advance()
			chars = append(chars, "'")
			for !(p.AtEnd()) && (p.Peek() != '\'') {
				chars = append(chars, p.Advance())
			}
			if p.AtEnd() {
				panic(NewParseError("Unterminated single quote"))
			}
			chars = append(chars, p.Advance())
		} else if ch == '"' {
			// Double-quoted string
			p.Advance()
			chars = append(chars, "\"")
			for !(p.AtEnd()) && (p.Peek() != '"') {
				c = p.Peek()
				if (c == '\\') && ((p.Pos + 1) < p.Length) {
					next_c = p.Source[(p.Pos + 1)]
					if next_c == '\n' {
						// Line continuation - skip both backslash and newline
						p.Advance()
						p.Advance()
					} else {
						chars = append(chars, p.Advance())
						chars = append(chars, p.Advance())
					}
				} else if c == '$' {
					// Handle expansions inside double quotes
					if ((p.Pos + 2) < p.Length) && (p.Source[(p.Pos+1)] == '(') && (p.Source[(p.Pos+2)] == '(') {
						arith_result = p.parseArithmeticExpansion()
						arith_node = arith_result[0]
						arith_text = arith_result[1]
						if arith_node {
							parts = append(parts, arith_node)
							chars = append(chars, arith_text)
						} else {
							// Not arithmetic - try command substitution
							cmdsub_result = p.parseCommandSubstitution()
							cmdsub_node = cmdsub_result[0]
							cmdsub_text = cmdsub_result[1]
							if cmdsub_node {
								parts = append(parts, cmdsub_node)
								chars = append(chars, cmdsub_text)
							} else {
								chars = append(chars, p.Advance())
							}
						}
					} else if ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(') {
						cmdsub_result = p.parseCommandSubstitution()
						cmdsub_node = cmdsub_result[0]
						cmdsub_text = cmdsub_result[1]
						if cmdsub_node {
							parts = append(parts, cmdsub_node)
							chars = append(chars, cmdsub_text)
						} else {
							chars = append(chars, p.Advance())
						}
					} else {
						param_result = p.parseParamExpansion()
						param_node = param_result[0]
						param_text = param_result[1]
						if param_node {
							parts = append(parts, param_node)
							chars = append(chars, param_text)
						} else {
							chars = append(chars, p.Advance())
						}
					}
				} else {
					chars = append(chars, p.Advance())
				}
			}
			if p.AtEnd() {
				panic(NewParseError("Unterminated double quote"))
			}
			chars = append(chars, p.Advance())
		} else if (ch == '\\') && ((p.Pos + 1) < p.Length) {
			// Escape
			chars = append(chars, p.Advance())
			chars = append(chars, p.Advance())
		} else if (ch == '$') && ((p.Pos + 2) < p.Length) && (p.Source[(p.Pos+1)] == '(') && (p.Source[(p.Pos+2)] == '(') {
			// Arithmetic expansion $((...))
			arith_result = p.parseArithmeticExpansion()
			arith_node = arith_result[0]
			arith_text = arith_result[1]
			if arith_node {
				parts = append(parts, arith_node)
				chars = append(chars, arith_text)
			} else {
				chars = append(chars, p.Advance())
			}
		} else if (ch == '$') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(') {
			// Command substitution $(...)
			cmdsub_result = p.parseCommandSubstitution()
			cmdsub_node = cmdsub_result[0]
			cmdsub_text = cmdsub_result[1]
			if cmdsub_node {
				parts = append(parts, cmdsub_node)
				chars = append(chars, cmdsub_text)
			} else {
				chars = append(chars, p.Advance())
			}
		} else if ch == '$' {
			// Parameter expansion $var or ${...}
			param_result = p.parseParamExpansion()
			param_node = param_result[0]
			param_text = param_result[1]
			if param_node {
				parts = append(parts, param_node)
				chars = append(chars, param_text)
			} else {
				chars = append(chars, p.Advance())
			}
		} else if isRedirectChar(ch) && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(') {
			// Process substitution <(...) or >(...)
			procsub_result = p.parseProcessSubstitution()
			procsub_node = procsub_result[0]
			procsub_text = procsub_result[1]
			if procsub_node {
				parts = append(parts, procsub_node)
				chars = append(chars, procsub_text)
			} else {
				chars = append(chars, p.Advance())
			}
		} else if ch == '`' {
			// Backtick command substitution
			cmdsub_result = p.parseBacktickSubstitution()
			cmdsub_node = cmdsub_result[0]
			cmdsub_text = cmdsub_result[1]
			if cmdsub_node {
				parts = append(parts, cmdsub_node)
				chars = append(chars, cmdsub_text)
			} else {
				chars = append(chars, p.Advance())
			}
		} else {
			// Regular character
			chars = append(chars, p.Advance())
		}
	}
	if !(chars) {
		return nil
	}
	parts_arg := nil
	if len(parts) > 0 {
		parts_arg = parts
	}
	return NewWord(strings.Join(chars, ""), parts_arg)
}

func (p *Parser) parseCondRegexWord() Node {
	p.condSkipWhitespace()
	if p.condAtEnd() {
		return nil
	}
	start := p.Pos
	chars := []interface{}{}
	parts := []interface{}{}
	paren_depth := 0
	for !(p.AtEnd()) {
		ch := p.Peek()
		// End of conditional
		if (ch == ']') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == ']') {
			break
		}
		// Backslash-newline continuation (check before space/escape handling)
		if (ch == '\\') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '\n') {
			p.Advance()
			p.Advance()
			continue
		}
		// Escape sequences - consume both characters (including escaped spaces)
		if (ch == '\\') && ((p.Pos + 1) < p.Length) {
			chars = append(chars, p.Advance())
			chars = append(chars, p.Advance())
			continue
		}
		// Track regex grouping parentheses
		if ch == '(' {
			paren_depth += 1
			chars = append(chars, p.Advance())
			continue
		}
		if ch == ')' {
			if paren_depth > 0 {
				paren_depth -= 1
				chars = append(chars, p.Advance())
				continue
			}
			// Unmatched ) - probably end of pattern
			break
		}
		// Regex character class [...] - consume until closing ]
		// Handles [[:alpha:]], [^0-9], []a-z] (] as first char), etc.
		if ch == '[' {
			chars = append(chars, p.Advance())
			// Handle negation [^
			if !(p.AtEnd()) && (p.Peek() == '^') {
				chars = append(chars, p.Advance())
			}
			// Handle ] as first char (literal ])
			if !(p.AtEnd()) && (p.Peek() == ']') {
				chars = append(chars, p.Advance())
			}
			// Consume until closing ]
			for !(p.AtEnd()) {
				c := p.Peek()
				if c == ']' {
					chars = append(chars, p.Advance())
					break
				}
				if (c == '[') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == ':') {
					// POSIX class like [:alpha:] inside bracket expression
					chars = append(chars, p.Advance())
					chars = append(chars, p.Advance())
					for !(p.AtEnd()) && !((p.Peek() == ':') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == ']')) {
						chars = append(chars, p.Advance())
					}
					if !(p.AtEnd()) {
						chars = append(chars, p.Advance())
						chars = append(chars, p.Advance())
					}
				} else {
					chars = append(chars, p.Advance())
				}
			}
			continue
		}
		// Word terminators - space/tab ends the regex (unless inside parens), as do && and ||
		if isWhitespace(ch) && (paren_depth == 0) {
			break
		}
		if isWhitespace(ch) && (paren_depth > 0) {
			// Space inside regex parens is part of the pattern
			chars = append(chars, p.Advance())
			continue
		}
		if (ch == '&') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '&') {
			break
		}
		if (ch == '|') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '|') {
			break
		}
		// Single-quoted string
		if ch == '\'' {
			p.Advance()
			chars = append(chars, "'")
			for !(p.AtEnd()) && (p.Peek() != '\'') {
				chars = append(chars, p.Advance())
			}
			if p.AtEnd() {
				panic(NewParseError("Unterminated single quote"))
			}
			chars = append(chars, p.Advance())
			continue
		}
		// Double-quoted string
		var param_text interface{}
		var param_node interface{}
		var param_result interface{}
		if ch == '"' {
			p.Advance()
			chars = append(chars, "\"")
			for !(p.AtEnd()) && (p.Peek() != '"') {
				c = p.Peek()
				if (c == '\\') && ((p.Pos + 1) < p.Length) {
					chars = append(chars, p.Advance())
					chars = append(chars, p.Advance())
				} else if c == '$' {
					param_result = p.parseParamExpansion()
					param_node = param_result[0]
					param_text = param_result[1]
					if param_node {
						parts = append(parts, param_node)
						chars = append(chars, param_text)
					} else {
						chars = append(chars, p.Advance())
					}
				} else {
					chars = append(chars, p.Advance())
				}
			}
			if p.AtEnd() {
				panic(NewParseError("Unterminated double quote"))
			}
			chars = append(chars, p.Advance())
			continue
		}
		// Command substitution $(...) or parameter expansion $var or ${...}
		var cmdsub_result interface{}
		var cmdsub_text interface{}
		var cmdsub_node interface{}
		if ch == '$' {
			// Try command substitution first
			if ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(') {
				cmdsub_result = p.parseCommandSubstitution()
				cmdsub_node = cmdsub_result[0]
				cmdsub_text = cmdsub_result[1]
				if cmdsub_node {
					parts = append(parts, cmdsub_node)
					chars = append(chars, cmdsub_text)
					continue
				}
			}
			param_result = p.parseParamExpansion()
			param_node = param_result[0]
			param_text = param_result[1]
			if param_node {
				parts = append(parts, param_node)
				chars = append(chars, param_text)
			} else {
				chars = append(chars, p.Advance())
			}
			continue
		}
		// Regular character (including ( ) which are regex grouping)
		chars = append(chars, p.Advance())
	}
	if !(chars) {
		return nil
	}
	parts_arg := nil
	if len(parts) > 0 {
		parts_arg = parts
	}
	return NewWord(strings.Join(chars, ""), parts_arg)
}

func (p *Parser) ParseBraceGroup() Node {
	p.SkipWhitespace()
	if p.AtEnd() || (p.Peek() != '{') {
		return nil
	}
	// Check that { is followed by whitespace (it's a reserved word)
	if ((p.Pos + 1) < p.Length) && !(isWhitespace(p.Source[(p.Pos + 1)])) {
		return nil
	}
	p.Advance()
	p.SkipWhitespaceAndNewlines()
	body := p.ParseList(true)
	if body == nil {
		panic(NewParseError("Expected command in brace group"))
	}
	p.SkipWhitespace()
	if p.AtEnd() || (p.Peek() != '}') {
		panic(NewParseError("Expected } to close brace group"))
	}
	p.Advance()
	// Collect trailing redirects
	redirects := []interface{}{}
	for true {
		p.SkipWhitespace()
		redirect := p.ParseRedirect()
		if redirect == nil {
			break
		}
		redirects = append(redirects, redirect)
	}
	redir_arg := nil
	if redirects {
		redir_arg = redirects
	}
	return NewBraceGroup(body, redir_arg)
}

func (p *Parser) ParseIf() Node {
	p.SkipWhitespace()
	// Check for 'if' keyword
	if p.PeekWord() != "if" {
		return nil
	}
	p.ConsumeWord("if")
	// Parse condition (a list that ends at 'then')
	condition := p.ParseListUntil(toSet([]interface{}{"then"}))
	if condition == nil {
		panic(NewParseError("Expected condition after 'if'"))
	}
	// Expect 'then'
	p.SkipWhitespaceAndNewlines()
	if !(p.ConsumeWord("then")) {
		panic(NewParseError("Expected 'then' after if condition"))
	}
	// Parse then body (ends at elif, else, or fi)
	then_body := p.ParseListUntil(toSet([]interface{}{"elif", "else", "fi"}))
	if then_body == nil {
		panic(NewParseError("Expected commands after 'then'"))
	}
	// Check what comes next: elif, else, or fi
	p.SkipWhitespaceAndNewlines()
	next_word := p.PeekWord()
	else_body := nil
	var inner_next interface{}
	var elif_condition interface{}
	var inner_else interface{}
	var elif_then_body interface{}
	if next_word == "elif" {
		// elif is syntactic sugar for else if ... fi
		p.ConsumeWord("elif")
		// Parse the rest as a nested if (but we've already consumed 'elif')
		// We need to parse: condition; then body [elif|else|fi]
		elif_condition = p.ParseListUntil(toSet([]interface{}{"then"}))
		if elif_condition == nil {
			panic(NewParseError("Expected condition after 'elif'"))
		}
		p.SkipWhitespaceAndNewlines()
		if !(p.ConsumeWord("then")) {
			panic(NewParseError("Expected 'then' after elif condition"))
		}
		elif_then_body = p.ParseListUntil(toSet([]interface{}{"elif", "else", "fi"}))
		if elif_then_body == nil {
			panic(NewParseError("Expected commands after 'then'"))
		}
		// Recursively handle more elif/else/fi
		p.SkipWhitespaceAndNewlines()
		inner_next = p.PeekWord()
		inner_else = nil
		if inner_next == "elif" {
			// More elif - recurse by creating a fake "if" and parsing
			// Actually, let's just recursively call a helper
			inner_else = p.parseElifChain()
		} else if inner_next == "else" {
			p.ConsumeWord("else")
			inner_else = p.ParseListUntil(toSet([]interface{}{"fi"}))
			if inner_else == nil {
				panic(NewParseError("Expected commands after 'else'"))
			}
		}
		else_body = NewIf(elif_condition, elif_then_body, inner_else)
	} else if next_word == "else" {
		p.ConsumeWord("else")
		else_body = p.ParseListUntil(toSet([]interface{}{"fi"}))
		if else_body == nil {
			panic(NewParseError("Expected commands after 'else'"))
		}
	}
	// Expect 'fi'
	p.SkipWhitespaceAndNewlines()
	if !(p.ConsumeWord("fi")) {
		panic(NewParseError("Expected 'fi' to close if statement"))
	}
	// Parse optional trailing redirections
	redirects := []interface{}{}
	for true {
		p.SkipWhitespace()
		redirect := p.ParseRedirect()
		if redirect == nil {
			break
		}
		redirects = append(redirects, redirect)
	}
	redir_arg := nil
	if redirects {
		redir_arg = redirects
	}
	return NewIf(condition, then_body, else_body, redir_arg)
}

func (p *Parser) parseElifChain() If {
	p.ConsumeWord("elif")
	condition := p.ParseListUntil(toSet([]interface{}{"then"}))
	if condition == nil {
		panic(NewParseError("Expected condition after 'elif'"))
	}
	p.SkipWhitespaceAndNewlines()
	if !(p.ConsumeWord("then")) {
		panic(NewParseError("Expected 'then' after elif condition"))
	}
	then_body := p.ParseListUntil(toSet([]interface{}{"elif", "else", "fi"}))
	if then_body == nil {
		panic(NewParseError("Expected commands after 'then'"))
	}
	p.SkipWhitespaceAndNewlines()
	next_word := p.PeekWord()
	else_body := nil
	if next_word == "elif" {
		else_body = p.parseElifChain()
	} else if next_word == "else" {
		p.ConsumeWord("else")
		else_body = p.ParseListUntil(toSet([]interface{}{"fi"}))
		if else_body == nil {
			panic(NewParseError("Expected commands after 'else'"))
		}
	}
	return NewIf(condition, then_body, else_body)
}

func (p *Parser) ParseWhile() Node {
	p.SkipWhitespace()
	if p.PeekWord() != "while" {
		return nil
	}
	p.ConsumeWord("while")
	// Parse condition (ends at 'do')
	condition := p.ParseListUntil(toSet([]interface{}{"do"}))
	if condition == nil {
		panic(NewParseError("Expected condition after 'while'"))
	}
	// Expect 'do'
	p.SkipWhitespaceAndNewlines()
	if !(p.ConsumeWord("do")) {
		panic(NewParseError("Expected 'do' after while condition"))
	}
	// Parse body (ends at 'done')
	body := p.ParseListUntil(toSet([]interface{}{"done"}))
	if body == nil {
		panic(NewParseError("Expected commands after 'do'"))
	}
	// Expect 'done'
	p.SkipWhitespaceAndNewlines()
	if !(p.ConsumeWord("done")) {
		panic(NewParseError("Expected 'done' to close while loop"))
	}
	// Parse optional trailing redirections
	redirects := []interface{}{}
	for true {
		p.SkipWhitespace()
		redirect := p.ParseRedirect()
		if redirect == nil {
			break
		}
		redirects = append(redirects, redirect)
	}
	redir_arg := nil
	if redirects {
		redir_arg = redirects
	}
	return NewWhile(condition, body, redir_arg)
}

func (p *Parser) ParseUntil() Node {
	p.SkipWhitespace()
	if p.PeekWord() != "until" {
		return nil
	}
	p.ConsumeWord("until")
	// Parse condition (ends at 'do')
	condition := p.ParseListUntil(toSet([]interface{}{"do"}))
	if condition == nil {
		panic(NewParseError("Expected condition after 'until'"))
	}
	// Expect 'do'
	p.SkipWhitespaceAndNewlines()
	if !(p.ConsumeWord("do")) {
		panic(NewParseError("Expected 'do' after until condition"))
	}
	// Parse body (ends at 'done')
	body := p.ParseListUntil(toSet([]interface{}{"done"}))
	if body == nil {
		panic(NewParseError("Expected commands after 'do'"))
	}
	// Expect 'done'
	p.SkipWhitespaceAndNewlines()
	if !(p.ConsumeWord("done")) {
		panic(NewParseError("Expected 'done' to close until loop"))
	}
	// Parse optional trailing redirections
	redirects := []interface{}{}
	for true {
		p.SkipWhitespace()
		redirect := p.ParseRedirect()
		if redirect == nil {
			break
		}
		redirects = append(redirects, redirect)
	}
	redir_arg := nil
	if redirects {
		redir_arg = redirects
	}
	return NewUntil(condition, body, redir_arg)
}

func (p *Parser) ParseFor() Node {
	p.SkipWhitespace()
	if p.PeekWord() != "for" {
		return nil
	}
	p.ConsumeWord("for")
	p.SkipWhitespace()
	// Check for C-style for loop: for ((init; cond; incr))
	if (p.Peek() == '(') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(') {
		return p.parseForArith()
	}
	// Parse variable name (bash allows reserved words as variable names in for loops)
	var_name := p.PeekWord()
	if var_name == nil {
		panic(NewParseError("Expected variable name after 'for'"))
	}
	p.ConsumeWord(var_name)
	p.SkipWhitespace()
	// Handle optional semicolon or newline before 'in' or 'do'
	if p.Peek() == ';' {
		p.Advance()
	}
	p.SkipWhitespaceAndNewlines()
	// Check for optional 'in' clause
	words := nil
	var word Node
	if p.PeekWord() == "in" {
		p.ConsumeWord("in")
		p.SkipWhitespaceAndNewlines()
		// Parse words until semicolon, newline, or 'do'
		words = []interface{}{}
		for true {
			p.SkipWhitespace()
			// Check for end of word list
			if p.AtEnd() {
				break
			}
			if isSemicolonOrNewline(p.Peek()) {
				if p.Peek() == ';' {
					p.Advance()
				}
				break
			}
			if p.PeekWord() == "do" {
				break
			}
			word = p.ParseWord()
			if word == nil {
				break
			}
			words = append(words, word)
		}
	}
	// Skip to 'do'
	p.SkipWhitespaceAndNewlines()
	// Expect 'do'
	if !(p.ConsumeWord("do")) {
		panic(NewParseError("Expected 'do' in for loop"))
	}
	// Parse body (ends at 'done')
	body := p.ParseListUntil(toSet([]interface{}{"done"}))
	if body == nil {
		panic(NewParseError("Expected commands after 'do'"))
	}
	// Expect 'done'
	p.SkipWhitespaceAndNewlines()
	if !(p.ConsumeWord("done")) {
		panic(NewParseError("Expected 'done' to close for loop"))
	}
	// Parse optional trailing redirections
	redirects := []interface{}{}
	for true {
		p.SkipWhitespace()
		redirect := p.ParseRedirect()
		if redirect == nil {
			break
		}
		redirects = append(redirects, redirect)
	}
	redir_arg := nil
	if redirects {
		redir_arg = redirects
	}
	return NewFor(var_name, words, body, redir_arg)
}

func (p *Parser) parseForArith() ForArith {
	// We've already consumed 'for' and positioned at '(('
	p.Advance()
	p.Advance()
	// Parse the three expressions separated by semicolons
	// Each can be empty
	parts := []interface{}{}
	current := []interface{}{}
	paren_depth := 0
	for !(p.AtEnd()) {
		ch := p.Peek()
		if ch == '(' {
			paren_depth += 1
			current = append(current, p.Advance())
		} else if ch == ')' {
			if paren_depth > 0 {
				paren_depth -= 1
				current = append(current, p.Advance())
			} else if ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == ')') {
				// Check for closing ))
				// End of ((...)) - preserve trailing whitespace
				parts = append(parts, strings.TrimLeft(strings.Join(current, ""), " \t\n"))
				p.Advance()
				p.Advance()
				break
			} else {
				current = append(current, p.Advance())
			}
		} else if (ch == ';') && (paren_depth == 0) {
			// Preserve trailing whitespace in expressions
			parts = append(parts, strings.TrimLeft(strings.Join(current, ""), " \t\n"))
			current = []interface{}{}
			p.Advance()
		} else {
			current = append(current, p.Advance())
		}
	}
	if len(parts) != 3 {
		panic(NewParseError("Expected three expressions in for ((;;))"))
	}
	init := parts[0].(Node)
	cond := parts[1].(Node)
	incr := parts[2].(Node)
	p.SkipWhitespace()
	// Handle optional semicolon
	if !(p.AtEnd()) && (p.Peek() == ';') {
		p.Advance()
	}
	p.SkipWhitespaceAndNewlines()
	// Parse body - either do/done or brace group
	var body interface{}
	var brace interface{}
	if p.Peek() == '{' {
		brace = p.ParseBraceGroup()
		if brace == nil {
			panic(NewParseError("Expected brace group body in for loop"))
		}
		// Unwrap the brace-group to match bash-oracle output format
		body = brace.Body
	} else if p.ConsumeWord("do") {
		body = p.ParseListUntil(toSet([]interface{}{"done"}))
		if body == nil {
			panic(NewParseError("Expected commands after 'do'"))
		}
		p.SkipWhitespaceAndNewlines()
		if !(p.ConsumeWord("done")) {
			panic(NewParseError("Expected 'done' to close for loop"))
		}
	} else {
		panic(NewParseError("Expected 'do' or '{' in for loop"))
	}
	// Parse optional trailing redirections
	redirects := []interface{}{}
	for true {
		p.SkipWhitespace()
		redirect := p.ParseRedirect()
		if redirect == nil {
			break
		}
		redirects = append(redirects, redirect)
	}
	redir_arg := nil
	if redirects {
		redir_arg = redirects
	}
	return NewForArith(init, cond, incr, body, redir_arg)
}

func (p *Parser) ParseSelect() Node {
	p.SkipWhitespace()
	if p.PeekWord() != "select" {
		return nil
	}
	p.ConsumeWord("select")
	p.SkipWhitespace()
	// Parse variable name
	var_name := p.PeekWord()
	if var_name == nil {
		panic(NewParseError("Expected variable name after 'select'"))
	}
	p.ConsumeWord(var_name)
	p.SkipWhitespace()
	// Handle optional semicolon before 'in', 'do', or '{'
	if p.Peek() == ';' {
		p.Advance()
	}
	p.SkipWhitespaceAndNewlines()
	// Check for optional 'in' clause
	words := nil
	var word Node
	if p.PeekWord() == "in" {
		p.ConsumeWord("in")
		p.SkipWhitespaceAndNewlines()
		// Parse words until semicolon, newline, 'do', or '{'
		words = []interface{}{}
		for true {
			p.SkipWhitespace()
			// Check for end of word list
			if p.AtEnd() {
				break
			}
			if isSemicolonNewlineBrace(p.Peek()) {
				if p.Peek() == ';' {
					p.Advance()
				}
				break
			}
			if p.PeekWord() == "do" {
				break
			}
			word = p.ParseWord()
			if word == nil {
				break
			}
			words = append(words, word)
		}
	}
	// Empty word list is allowed for select (unlike for)
	// Skip whitespace before body
	p.SkipWhitespaceAndNewlines()
	// Parse body - either do/done or brace group
	var body interface{}
	var brace interface{}
	if p.Peek() == '{' {
		brace = p.ParseBraceGroup()
		if brace == nil {
			panic(NewParseError("Expected brace group body in select"))
		}
		// Unwrap the brace-group to match bash-oracle output format
		body = brace.Body
	} else if p.ConsumeWord("do") {
		// Parse body (ends at 'done')
		body = p.ParseListUntil(toSet([]interface{}{"done"}))
		if body == nil {
			panic(NewParseError("Expected commands after 'do'"))
		}
		// Expect 'done'
		p.SkipWhitespaceAndNewlines()
		if !(p.ConsumeWord("done")) {
			panic(NewParseError("Expected 'done' to close select"))
		}
	} else {
		panic(NewParseError("Expected 'do' or '{' in select"))
	}
	// Parse optional trailing redirections
	redirects := []interface{}{}
	for true {
		p.SkipWhitespace()
		redirect := p.ParseRedirect()
		if redirect == nil {
			break
		}
		redirects = append(redirects, redirect)
	}
	redir_arg := nil
	if redirects {
		redir_arg = redirects
	}
	return NewSelect(var_name, words, body, redir_arg)
}

func (p *Parser) isCaseTerminator() bool {
	if p.AtEnd() || (p.Peek() != ';') {
		return false
	}
	if (p.Pos + 1) >= p.Length {
		return false
	}
	next_ch := p.Source[(p.Pos + 1)]
	// ;; or ;& or ;;& (which is actually ;;&)
	return isSemicolonOrAmp(next_ch)
}

func (p *Parser) consumeCaseTerminator() string {
	if p.AtEnd() || (p.Peek() != ';') {
		return ";;"
	}
	p.Advance()
	if p.AtEnd() {
		return ";;"
	}
	ch := p.Peek()
	if ch == ';' {
		p.Advance()
		// Check for ;;&
		if !(p.AtEnd()) && (p.Peek() == '&') {
			p.Advance()
			return ";;&"
		}
		return ";;"
	} else if ch == '&' {
		p.Advance()
		return ";&"
	}
	return ";;"
}

func (p *Parser) ParseCase() Node {
	p.SkipWhitespace()
	if p.PeekWord() != "case" {
		return nil
	}
	p.ConsumeWord("case")
	p.SkipWhitespace()
	// Parse the word to match
	word := p.ParseWord()
	if word == nil {
		panic(NewParseError("Expected word after 'case'"))
	}
	p.SkipWhitespaceAndNewlines()
	// Expect 'in'
	if !(p.ConsumeWord("in")) {
		panic(NewParseError("Expected 'in' after case word"))
	}
	p.SkipWhitespaceAndNewlines()
	// Parse pattern clauses until 'esac'
	patterns := []interface{}{}
	for true {
		p.SkipWhitespaceAndNewlines()
		// Check if we're at 'esac' (but not 'esac)' which is esac as a pattern)
		var is_pattern interface{}
		var saved interface{}
		var next_ch interface{}
		if p.PeekWord() == "esac" {
			// Look ahead to see if esac is a pattern (esac followed by ) then body/;;)
			// or the closing keyword (esac followed by ) that closes containing construct)
			saved = p.Pos
			p.SkipWhitespace()
			// Consume "esac"
			for !(p.AtEnd()) && !(isMetachar(p.Peek())) && !(isQuote(p.Peek())) {
				p.Advance()
			}
			p.SkipWhitespace()
			// Check for ) and what follows
			is_pattern = false
			if !(p.AtEnd()) && (p.Peek() == ')') {
				p.Advance()
				p.SkipWhitespace()
				// esac is a pattern if there's body content or ;; after )
				// Not a pattern if ) is followed by end, newline, or another )
				if !(p.AtEnd()) {
					next_ch = p.Peek()
					// If followed by ;; or actual command content, it's a pattern
					if next_ch == ';' {
						is_pattern = true
					} else if !(isNewlineOrRightParen(next_ch)) {
						is_pattern = true
					}
				}
			}
			p.Pos = saved
			if !(is_pattern) {
				break
			}
		}
		// Skip optional leading ( before pattern (POSIX allows this)
		p.SkipWhitespaceAndNewlines()
		if !(p.AtEnd()) && (p.Peek() == '(') {
			p.Advance()
			p.SkipWhitespaceAndNewlines()
		}
		// Parse pattern (everything until ')' at depth 0)
		// Pattern can contain | for alternation, quotes, globs, extglobs, etc.
		// Extglob patterns @(), ?(), *(), +(), !() contain nested parens
		pattern_chars := []interface{}{}
		extglob_depth := 0
		for !(p.AtEnd()) {
			ch := p.Peek()
			var scan_pos interface{}
			var has_first_bracket_literal interface{}
			var paren_depth interface{}
			var sc interface{}
			var is_char_class interface{}
			var scan_depth interface{}
			if ch == ')' {
				if extglob_depth > 0 {
					// Inside extglob, consume the ) and decrement depth
					pattern_chars = append(pattern_chars, p.Advance())
					extglob_depth -= 1
				} else {
					// End of pattern
					p.Advance()
					break
				}
			} else if ch == '\\' {
				// Line continuation or backslash escape
				if ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '\n') {
					// Line continuation - skip both backslash and newline
					p.Advance()
					p.Advance()
				} else {
					// Normal escape - consume both chars
					pattern_chars = append(pattern_chars, p.Advance())
					if !(p.AtEnd()) {
						pattern_chars = append(pattern_chars, p.Advance())
					}
				}
			} else if (ch == '$') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(') {
				// $( or $(( - command sub or arithmetic
				pattern_chars = append(pattern_chars, p.Advance())
				pattern_chars = append(pattern_chars, p.Advance())
				if !(p.AtEnd()) && (p.Peek() == '(') {
					// $(( arithmetic - need to find matching ))
					pattern_chars = append(pattern_chars, p.Advance())
					paren_depth = 2
					for !(p.AtEnd()) && (paren_depth > 0) {
						c := p.Peek()
						if c == '(' {
							paren_depth += 1
						} else if c == ')' {
							paren_depth -= 1
						}
						pattern_chars = append(pattern_chars, p.Advance())
					}
				} else {
					// $() command sub - track single paren
					extglob_depth += 1
				}
			} else if (ch == '(') && (extglob_depth > 0) {
				// Grouping paren inside extglob
				pattern_chars = append(pattern_chars, p.Advance())
				extglob_depth += 1
			} else if isExtglobPrefix(ch) && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(') {
				// Extglob opener: @(, ?(, *(, +(, !(
				pattern_chars = append(pattern_chars, p.Advance())
				pattern_chars = append(pattern_chars, p.Advance())
				extglob_depth += 1
			} else if ch == '[' {
				// Character class - but only if there's a matching ]
				// ] must come before ) at same depth (either extglob or pattern)
				is_char_class = false
				scan_pos = (p.Pos + 1)
				scan_depth = 0
				has_first_bracket_literal = false
				// Skip [! or [^ at start
				if (scan_pos < p.Length) && isCaretOrBang(p.Source[scan_pos]) {
					scan_pos += 1
				}
				// Skip ] as first char (literal in char class) only if there's another ]
				if (scan_pos < p.Length) && (p.Source[scan_pos] == ']') {
					// Check if there's another ] later
					if strings.Index(p.Source, "]", (scan_pos+1)) != -1 {
						scan_pos += 1
						has_first_bracket_literal = true
					}
				}
				for scan_pos < p.Length {
					sc = p.Source[scan_pos]
					if (sc == ']') && (scan_depth == 0) {
						is_char_class = true
						break
					} else if sc == '[' {
						scan_depth += 1
					} else if (sc == ')') && (scan_depth == 0) {
						// Hit pattern/extglob closer before finding ]
						break
					} else if (sc == '|') && (scan_depth == 0) && (extglob_depth > 0) {
						// Hit alternation in extglob - ] must be in this branch
						break
					}
					scan_pos += 1
				}
				if is_char_class {
					pattern_chars = append(pattern_chars, p.Advance())
					// Handle [! or [^ at start
					if !(p.AtEnd()) && isCaretOrBang(p.Peek()) {
						pattern_chars = append(pattern_chars, p.Advance())
					}
					// Handle ] as first char (literal) only if we detected it in scan
					if has_first_bracket_literal && !(p.AtEnd()) && (p.Peek() == ']') {
						pattern_chars = append(pattern_chars, p.Advance())
					}
					// Consume until closing ]
					for !(p.AtEnd()) && (p.Peek() != ']') {
						pattern_chars = append(pattern_chars, p.Advance())
					}
					if !(p.AtEnd()) {
						pattern_chars = append(pattern_chars, p.Advance())
					}
				} else {
					// Not a valid char class, treat [ as literal
					pattern_chars = append(pattern_chars, p.Advance())
				}
			} else if ch == '\'' {
				// Single-quoted string in pattern
				pattern_chars = append(pattern_chars, p.Advance())
				for !(p.AtEnd()) && (p.Peek() != '\'') {
					pattern_chars = append(pattern_chars, p.Advance())
				}
				if !(p.AtEnd()) {
					pattern_chars = append(pattern_chars, p.Advance())
				}
			} else if ch == '"' {
				// Double-quoted string in pattern
				pattern_chars = append(pattern_chars, p.Advance())
				for !(p.AtEnd()) && (p.Peek() != '"') {
					if (p.Peek() == '\\') && ((p.Pos + 1) < p.Length) {
						pattern_chars = append(pattern_chars, p.Advance())
					}
					pattern_chars = append(pattern_chars, p.Advance())
				}
				if !(p.AtEnd()) {
					pattern_chars = append(pattern_chars, p.Advance())
				}
			} else if isWhitespace(ch) {
				// Skip whitespace at top level, but preserve inside $() or extglob
				if extglob_depth > 0 {
					pattern_chars = append(pattern_chars, p.Advance())
				} else {
					p.Advance()
				}
			} else {
				pattern_chars = append(pattern_chars, p.Advance())
			}
		}
		pattern := strings.Join(pattern_chars, "")
		if !(pattern) {
			panic(NewParseError("Expected pattern in case statement"))
		}
		// Parse commands until ;;, ;&, ;;&, or esac
		// Commands are optional (can have empty body)
		p.SkipWhitespace()
		body := nil
		// Check for empty body: terminator right after pattern
		is_empty_body := p.isCaseTerminator()
		var is_at_terminator interface{}
		if !(is_empty_body) {
			// Skip newlines and check if there's content before terminator or esac
			p.SkipWhitespaceAndNewlines()
			if !(p.AtEnd()) && (p.PeekWord() != "esac") {
				// Check again for terminator after whitespace/newlines
				is_at_terminator = p.isCaseTerminator()
				if !(is_at_terminator) {
					body = p.ParseListUntil(toSet([]interface{}{"esac"}))
					p.SkipWhitespace()
				}
			}
		}
		// Handle terminator: ;;, ;&, or ;;&
		terminator := p.consumeCaseTerminator()
		p.SkipWhitespaceAndNewlines()
		patterns = append(patterns, NewCasePattern(pattern, body, terminator))
	}
	// Expect 'esac'
	p.SkipWhitespaceAndNewlines()
	if !(p.ConsumeWord("esac")) {
		panic(NewParseError("Expected 'esac' to close case statement"))
	}
	// Collect trailing redirects
	redirects := []interface{}{}
	for true {
		p.SkipWhitespace()
		redirect := p.ParseRedirect()
		if redirect == nil {
			break
		}
		redirects = append(redirects, redirect)
	}
	redir_arg := nil
	if redirects {
		redir_arg = redirects
	}
	return NewCase(word, patterns, redir_arg)
}

func (p *Parser) ParseCoproc() Node {
	p.SkipWhitespace()
	if p.AtEnd() {
		return nil
	}
	if p.PeekWord() != "coproc" {
		return nil
	}
	p.ConsumeWord("coproc")
	p.SkipWhitespace()
	name := nil
	// Check for compound command directly (no NAME)
	ch := nil
	if !(p.AtEnd()) {
		ch = p.Peek()
	}
	var body interface{}
	if ch == '{' {
		body = p.ParseBraceGroup()
		if body != nil {
			return NewCoproc(body, name)
		}
	}
	if ch == '(' {
		if ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(') {
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
	// Check for reserved word compounds directly
	next_word := p.PeekWord()
	if isCompoundKeyword(next_word) {
		body = p.ParseCompoundCommand()
		if body != nil {
			return NewCoproc(body, name)
		}
	}
	// Check if first word is NAME followed by compound command
	word_start := p.Pos
	potential_name := p.PeekWord()
	if potential_name {
		// Skip past the potential name
		for !(p.AtEnd()) && !(isMetachar(p.Peek())) && !(isQuote(p.Peek())) {
			p.Advance()
		}
		p.SkipWhitespace()
		// Check what follows
		ch = nil
		if !(p.AtEnd()) {
			ch = p.Peek()
		}
		next_word = p.PeekWord()
		if ch == '{' {
			// NAME { ... } - extract name
			name = potential_name
			body = p.ParseBraceGroup()
			if body != nil {
				return NewCoproc(body, name)
			}
		} else if ch == '(' {
			// NAME ( ... ) - extract name
			name = potential_name
			if ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(') {
				body = p.ParseArithmeticCommand()
			} else {
				body = p.ParseSubshell()
			}
			if body != nil {
				return NewCoproc(body, name)
			}
		} else if isCompoundKeyword(next_word) {
			// NAME followed by reserved compound - extract name
			name = potential_name
			body = p.ParseCompoundCommand()
			if body != nil {
				return NewCoproc(body, name)
			}
		}
		// Not followed by compound - restore position and parse as simple command
		p.Pos = word_start
	}
	// Parse as simple command (includes any "NAME" as part of the command)
	body = p.ParseCommand()
	if body != nil {
		return NewCoproc(body, name)
	}
	panic(NewParseError("Expected command after coproc"))
}

func (p *Parser) ParseFunction() Node {
	p.SkipWhitespace()
	if p.AtEnd() {
		return nil
	}
	saved_pos := p.Pos
	// Check for 'function' keyword form
	var name string
	var body interface{}
	if p.PeekWord() == "function" {
		p.ConsumeWord("function")
		p.SkipWhitespace()
		// Get function name
		name = p.PeekWord()
		if name == nil {
			p.Pos = saved_pos
			return nil
		}
		p.ConsumeWord(name)
		p.SkipWhitespace()
		// Optional () after name - but only if it's actually ()
		// and not the start of a subshell body
		if !(p.AtEnd()) && (p.Peek() == '(') {
			// Check if this is () or start of subshell
			if ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == ')') {
				p.Advance()
				p.Advance()
			}
		}
		// else: the ( is start of subshell body, don't consume
		p.SkipWhitespaceAndNewlines()
		// Parse body (any compound command)
		body = p.parseCompoundCommand()
		if body == nil {
			panic(NewParseError("Expected function body"))
		}
		return NewFunction(name, body)
	}
	// Check for POSIX form: name()
	// We need to peek ahead to see if there's a () after the word
	name = p.PeekWord()
	if (name == nil) || isReservedWord(name) {
		return nil
	}
	// Assignment words (containing =) are not function definitions
	if strContains(name, "=") {
		return nil
	}
	// Save position after the name
	p.SkipWhitespace()
	name_start := p.Pos
	// Consume the name
	for !(p.AtEnd()) && !(isMetachar(p.Peek())) && !(isQuote(p.Peek())) && !(isParen(p.Peek())) {
		p.Advance()
	}
	name = substring(p.Source, name_start, p.Pos)
	if !(name) {
		p.Pos = saved_pos
		return nil
	}
	// Check for () - whitespace IS allowed between name and (
	p.SkipWhitespace()
	if p.AtEnd() || (p.Peek() != '(') {
		p.Pos = saved_pos
		return nil
	}
	p.Advance()
	p.SkipWhitespace()
	if p.AtEnd() || (p.Peek() != ')') {
		p.Pos = saved_pos
		return nil
	}
	p.Advance()
	p.SkipWhitespaceAndNewlines()
	// Parse body (any compound command)
	body = p.parseCompoundCommand()
	if body == nil {
		panic(NewParseError("Expected function body"))
	}
	return NewFunction(name, body)
}

func (p *Parser) parseCompoundCommand() Node {
	// Try each compound command type
	result := p.ParseBraceGroup()
	if len(result) > 0 {
		return result
	}
	result = p.ParseSubshell()
	if len(result) > 0 {
		return result
	}
	result = p.ParseConditionalExpr()
	if len(result) > 0 {
		return result
	}
	result = p.ParseIf()
	if len(result) > 0 {
		return result
	}
	result = p.ParseWhile()
	if len(result) > 0 {
		return result
	}
	result = p.ParseUntil()
	if len(result) > 0 {
		return result
	}
	result = p.ParseFor()
	if len(result) > 0 {
		return result
	}
	result = p.ParseCase()
	if len(result) > 0 {
		return result
	}
	result = p.ParseSelect()
	if len(result) > 0 {
		return result
	}
	return nil
}

func (p *Parser) ParseListUntil(stop_words interface{}) Node {
	// Check if we're already at a stop word
	p.SkipWhitespaceAndNewlines()
	if contains(stop_words, p.PeekWord()) {
		return nil
	}
	pipeline := p.ParsePipeline()
	if pipeline == nil {
		return nil
	}
	parts := []interface{}{pipeline}
	for true {
		// Check for newline as implicit command separator
		p.SkipWhitespace()
		has_newline := false
		for !(p.AtEnd()) && (p.Peek() == '\n') {
			has_newline = true
			p.Advance()
			// Skip past any pending heredoc content after newline
			if (p.pendingHeredocEnd != nil) && (p.pendingHeredocEnd > p.Pos) {
				p.Pos = p.pendingHeredocEnd
				p.pendingHeredocEnd = nil
			}
			p.SkipWhitespace()
		}
		op := p.ParseListOperator()
		// Newline acts as implicit semicolon if followed by more commands
		if (op == nil) && has_newline {
			// Check if there's another command (not a stop word)
			if !(p.AtEnd()) && !contains(stop_words, p.PeekWord()) && !(isRightBracket(p.Peek())) {
				op = "\n"
			}
		}
		if op == nil {
			break
		}
		// For & at end of list, don't require another command
		if op == '&' {
			parts = append(parts, NewOperator(op))
			p.SkipWhitespaceAndNewlines()
			if p.AtEnd() || contains(stop_words, p.PeekWord()) || isNewlineOrRightBracket(p.Peek()) {
				break
			}
		}
		// For ; - check if it's a terminator before a stop word (don't include it)
		var at_case_terminator interface{}
		if op == ';' {
			p.SkipWhitespaceAndNewlines()
			// Also check for ;;, ;&, or ;;& (case terminators)
			at_case_terminator = ((p.Peek() == ';') && ((p.Pos + 1) < p.Length) && isSemicolonOrAmp(p.Source[(p.Pos+1)]))
			if p.AtEnd() || contains(stop_words, p.PeekWord()) || isNewlineOrRightBracket(p.Peek()) || at_case_terminator {
				// Don't include trailing semicolon - it's just a terminator
				break
			}
			parts = append(parts, NewOperator(op))
		} else if op != '&' {
			parts = append(parts, NewOperator(op))
		}
		// Check for stop words before parsing next pipeline
		p.SkipWhitespaceAndNewlines()
		// Also check for ;;, ;&, or ;;& (case terminators)
		if contains(stop_words, p.PeekWord()) {
			break
		}
		if (p.Peek() == ';') && ((p.Pos + 1) < p.Length) && isSemicolonOrAmp(p.Source[(p.Pos+1)]) {
			break
		}
		pipeline = p.ParsePipeline()
		if pipeline == nil {
			panic(NewParseError(("Expected command after " + op)))
		}
		parts = append(parts, pipeline)
	}
	if len(parts) == 1 {
		return parts[0].(Node)
	}
	return NewList(parts)
}

func (p *Parser) ParseCompoundCommand() Node {
	p.SkipWhitespace()
	if p.AtEnd() {
		return nil
	}
	ch := p.Peek()
	// Arithmetic command ((...)) - check before subshell
	if (ch == '(') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '(') {
		result := p.ParseArithmeticCommand()
		if result != nil {
			return result
		}
	}
	// Not arithmetic (e.g., '(( x ) )' is nested subshells) - fall through
	// Subshell
	if ch == '(' {
		return p.ParseSubshell()
	}
	// Brace group
	if ch == '{' {
		result = p.ParseBraceGroup()
		if result != nil {
			return result
		}
	}
	// Fall through to simple command if not a brace group
	// Conditional expression [[ ]] - check before reserved words
	if (ch == '[') && ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '[') {
		return p.ParseConditionalExpr()
	}
	// Check for reserved words
	word := p.PeekWord()
	// If statement
	if word == "if" {
		return p.ParseIf()
	}
	// While loop
	if word == "while" {
		return p.ParseWhile()
	}
	// Until loop
	if word == "until" {
		return p.ParseUntil()
	}
	// For loop
	if word == "for" {
		return p.ParseFor()
	}
	// Select statement
	if word == "select" {
		return p.ParseSelect()
	}
	// Case statement
	if word == "case" {
		return p.ParseCase()
	}
	// Function definition (function keyword form)
	if word == "function" {
		return p.ParseFunction()
	}
	// Coproc
	if word == "coproc" {
		return p.ParseCoproc()
	}
	// Try POSIX function definition (name() form) before simple command
	fn := p.ParseFunction()
	if fn != nil {
		return fn
	}
	// Simple command
	return p.ParseCommand()
}

func (p *Parser) ParsePipeline() Node {
	p.SkipWhitespace()
	// Track order of prefixes: "time", "negation", or "time_negation" or "negation_time"
	prefix_order := nil
	time_posix := false
	// Check for 'time' prefix first
	var saved interface{}
	if p.PeekWord() == "time" {
		p.ConsumeWord("time")
		prefix_order = "time"
		p.SkipWhitespace()
		// Check for -p flag
		if !(p.AtEnd()) && (p.Peek() == '-') {
			saved = p.Pos
			p.Advance()
			if !(p.AtEnd()) && (p.Peek() == 'p') {
				p.Advance()
				if p.AtEnd() || isWhitespace(p.Peek()) {
					time_posix = true
				} else {
					p.Pos = saved
				}
			} else {
				p.Pos = saved
			}
		}
		p.SkipWhitespace()
		// Check for -- (end of options) - implies -p per bash-oracle
		if !(p.AtEnd()) && startsWithAt(p.Source, p.Pos, "--") {
			if ((p.Pos + 2) >= p.Length) || isWhitespace(p.Source[(p.Pos+2)]) {
				p.Advance()
				p.Advance()
				time_posix = true
				p.SkipWhitespace()
			}
		}
		// Skip nested time keywords (time time X collapses to time X)
		for p.PeekWord() == "time" {
			p.ConsumeWord("time")
			p.SkipWhitespace()
			// Check for -p after nested time
			if !(p.AtEnd()) && (p.Peek() == '-') {
				saved = p.Pos
				p.Advance()
				if !(p.AtEnd()) && (p.Peek() == 'p') {
					p.Advance()
					if p.AtEnd() || isWhitespace(p.Peek()) {
						time_posix = true
					} else {
						p.Pos = saved
					}
				} else {
					p.Pos = saved
				}
			}
			p.SkipWhitespace()
		}
		// Check for ! after time
		if !(p.AtEnd()) && (p.Peek() == '!') {
			if ((p.Pos + 1) >= p.Length) || isWhitespace(p.Source[(p.Pos+1)]) {
				p.Advance()
				prefix_order = "time_negation"
				p.SkipWhitespace()
			}
		}
	} else if !(p.AtEnd()) && (p.Peek() == '!') {
		// Check for '!' negation prefix (if no time yet)
		if ((p.Pos + 1) >= p.Length) || isWhitespace(p.Source[(p.Pos+1)]) {
			p.Advance()
			p.SkipWhitespace()
			// Recursively parse pipeline to handle ! ! cmd, ! time cmd, etc.
			// Bare ! (no following command) is valid POSIX - equivalent to false
			inner := p.ParsePipeline()
			// Double negation cancels out (! ! cmd -> cmd, ! ! -> empty command)
			if (inner != nil) && (inner.GetKind() == "negation") {
				if inner.Pipeline != nil {
					return inner.Pipeline
				} else {
					return NewCommand([]interface{}{})
				}
			}
			return NewNegation(inner)
		}
	}
	// Parse the actual pipeline
	result := p.parseSimplePipeline()
	// Wrap based on prefix order
	// Note: bare time and time ! are valid (null command timing)
	if prefix_order == "time" {
		result = NewTime(result, time_posix)
	} else if prefix_order == "negation" {
		result = NewNegation(result)
	} else if prefix_order == "time_negation" {
		// time ! cmd -> Negation(Time(cmd)) per bash-oracle
		result = NewTime(result, time_posix)
		result = NewNegation(result)
	} else if prefix_order == "negation_time" {
		// ! time cmd -> Negation(Time(cmd))
		result = NewTime(result, time_posix)
		result = NewNegation(result)
	} else if result == nil {
		// No prefix and no pipeline
		return nil
	}
	return result
}

func (p *Parser) parseSimplePipeline() Node {
	cmd := p.ParseCompoundCommand()
	if cmd == nil {
		return nil
	}
	commands := []interface{}{cmd}
	for true {
		p.SkipWhitespace()
		if p.AtEnd() || (p.Peek() != '|') {
			break
		}
		// Check it's not ||
		if ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '|') {
			break
		}
		p.Advance()
		// Check for |& (pipe stderr)
		is_pipe_both := false
		if !(p.AtEnd()) && (p.Peek() == '&') {
			p.Advance()
			is_pipe_both = true
		}
		p.SkipWhitespaceAndNewlines()
		// Add pipe-both marker if this is a |& pipe
		if is_pipe_both {
			commands = append(commands, NewPipeBoth())
		}
		cmd = p.ParseCompoundCommand()
		if cmd == nil {
			panic(NewParseError("Expected command after |"))
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
	if p.AtEnd() {
		return nil
	}
	ch := p.Peek()
	if ch == '&' {
		// Check if this is &> or &>> (redirect), not background operator
		if ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '>') {
			return nil
		}
		p.Advance()
		if !(p.AtEnd()) && (p.Peek() == '&') {
			p.Advance()
			return "&&"
		}
		return "&"
	}
	if ch == '|' {
		if ((p.Pos + 1) < p.Length) && (p.Source[(p.Pos+1)] == '|') {
			p.Advance()
			p.Advance()
			return "||"
		}
		return nil
	}
	if ch == ';' {
		// Don't treat ;;, ;&, or ;;& as a single semicolon (they're case terminators)
		if ((p.Pos + 1) < p.Length) && isSemicolonOrAmp(p.Source[(p.Pos+1)]) {
			return nil
		}
		p.Advance()
		return ";"
	}
	return nil
}

func (p *Parser) ParseList(newline_as_separator bool) Node {
	if newline_as_separator == nil {
		newline_as_separator = true
	}
	if newline_as_separator {
		p.SkipWhitespaceAndNewlines()
	} else {
		p.SkipWhitespace()
	}
	pipeline := p.ParsePipeline()
	if pipeline == nil {
		return nil
	}
	parts := []interface{}{pipeline}
	for true {
		// Check for newline as implicit command separator
		p.SkipWhitespace()
		has_newline := false
		for !(p.AtEnd()) && (p.Peek() == '\n') {
			has_newline = true
			// If not treating newlines as separators, stop here
			if !(newline_as_separator) {
				break
			}
			p.Advance()
			// Skip past any pending heredoc content after newline
			if (p.pendingHeredocEnd != nil) && (p.pendingHeredocEnd > p.Pos) {
				p.Pos = p.pendingHeredocEnd
				p.pendingHeredocEnd = nil
			}
			p.SkipWhitespace()
		}
		// If we hit a newline and not treating them as separators, stop
		if has_newline && !(newline_as_separator) {
			break
		}
		op := p.ParseListOperator()
		// Newline acts as implicit semicolon if followed by more commands
		if (op == nil) && has_newline {
			if !(p.AtEnd()) && !(isRightBracket(p.Peek())) {
				op = "\n"
			}
		}
		if op == nil {
			break
		}
		// Don't add duplicate semicolon (e.g., explicit ; followed by newline)
		if !((op == ';') && (len(parts) > 0) && (parts[(len(parts)-1)].(Node).GetKind() == "operator") && (parts[(len(parts)-1)].(Node).Op == ';')) {
			parts = append(parts, NewOperator(op))
		}
		// For & at end of list, don't require another command
		if op == '&' {
			p.SkipWhitespace()
			if p.AtEnd() || isRightBracket(p.Peek()) {
				break
			}
			// Newline after & - in compound commands, skip it (& acts as separator)
			// At top level, newline terminates (separate commands)
			if p.Peek() == '\n' {
				if newline_as_separator {
					p.SkipWhitespaceAndNewlines()
					if p.AtEnd() || isRightBracket(p.Peek()) {
						break
					}
				} else {
					break
				}
			}
		}
		// For ; at end of list, don't require another command
		if op == ';' {
			p.SkipWhitespace()
			if p.AtEnd() || isRightBracket(p.Peek()) {
				break
			}
			// Newline after ; means continue to see if more commands follow
			if p.Peek() == '\n' {
				continue
			}
		}
		// For && and ||, allow newlines before the next command
		if (op == "&&") || (op == "||") {
			p.SkipWhitespaceAndNewlines()
		}
		pipeline = p.ParsePipeline()
		if pipeline == nil {
			panic(NewParseError(("Expected command after " + op)))
		}
		parts = append(parts, pipeline)
	}
	if len(parts) == 1 {
		return parts[0].(Node)
	}
	return NewList(parts)
}

func (p *Parser) ParseComment() Node {
	if p.AtEnd() || (p.Peek() != '#') {
		return nil
	}
	start := p.Pos
	for !(p.AtEnd()) && (p.Peek() != '\n') {
		p.Advance()
	}
	text := substring(p.Source, start, p.Pos)
	return NewComment(text)
}

func (p *Parser) Parse() []Node {
	source := strings.TrimSpace(p.Source)
	if !(source) {
		return []interface{}{NewEmpty()}
	}
	results := []interface{}{}
	// Skip leading comments (bash-oracle doesn't output them)
	for true {
		p.SkipWhitespace()
		// Skip newlines but not comments
		for !(p.AtEnd()) && (p.Peek() == '\n') {
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
	// Don't add to results - bash-oracle doesn't output comments
	// Parse statements separated by newlines as separate top-level nodes
	for !(p.AtEnd()) {
		result := p.ParseList(true)
		if result != nil {
			results = append(results, result)
		}
		p.SkipWhitespace()
		// Skip newlines (and any pending heredoc content) between statements
		found_newline := false
		for !(p.AtEnd()) && (p.Peek() == '\n') {
			found_newline = true
			p.Advance()
			// Skip past any pending heredoc content after newline
			if (p.pendingHeredocEnd != nil) && (p.pendingHeredocEnd > p.Pos) {
				p.Pos = p.pendingHeredocEnd
				p.pendingHeredocEnd = nil
			}
			p.SkipWhitespace()
		}
		// If no newline and not at end, we have unparsed content
		if !(found_newline) && !(p.AtEnd()) {
			panic(NewParseError("Parser not fully implemented yet"))
		}
	}
	if !(results) {
		return []interface{}{NewEmpty()}
	}
	return results
}

func Parse(source string) ([]Node, error) {
	parser := NewParser(source)
	return parser.Parse()
}
