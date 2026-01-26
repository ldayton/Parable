"""Manual Go code emission for special methods and functions."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .transpile_go import GoTranspiler


# ========== QuoteState methods ==========


def emit_quotestate_push(t: "GoTranspiler", receiver: str):
    """Emit QuoteState.Push() body."""
    t.emit(
        f"{receiver}._Stack = append({receiver}._Stack, quoteStackEntry{{{receiver}.Single, {receiver}.Double}})"
    )
    t.emit(f"{receiver}.Single = false")
    t.emit(f"{receiver}.Double = false")


def emit_quotestate_pop(t: "GoTranspiler", receiver: str):
    """Emit QuoteState.Pop() body."""
    t.emit(f"if len({receiver}._Stack) > 0 {{")
    t.indent += 1
    t.emit(f"entry := {receiver}._Stack[len({receiver}._Stack)-1]")
    t.emit(f"{receiver}._Stack = {receiver}._Stack[:len({receiver}._Stack)-1]")
    t.emit(f"{receiver}.Single = entry.single")
    t.emit(f"{receiver}.Double = entry.double")
    t.indent -= 1
    t.emit("}")


def emit_quotestate_copy(t: "GoTranspiler", receiver: str):
    """Emit QuoteState.Copy() body."""
    t.emit("qs := &QuoteState{}")
    t.emit(f"qs.Single = {receiver}.Single")
    t.emit(f"qs.Double = {receiver}.Double")
    t.emit(f"qs._Stack = make([]quoteStackEntry, len({receiver}._Stack))")
    t.emit(f"copy(qs._Stack, {receiver}._Stack)")
    t.emit("return qs")


def emit_quotestate_outer_double(t: "GoTranspiler", receiver: str):
    """Emit QuoteState.OuterDouble() body."""
    t.emit(f"if len({receiver}._Stack) == 0 {{")
    t.indent += 1
    t.emit("return false")
    t.indent -= 1
    t.emit("}")
    t.emit(f"return {receiver}._Stack[len({receiver}._Stack)-1].double")


# ========== Arithmetic parser ==========


def emit_arith_left_assoc(t: "GoTranspiler", receiver: str, ops: list[str], next_fn: str):
    """Emit inlined left-associative binary operator parsing."""
    t.emit(f"left := {receiver}.{next_fn}()")
    t.emit("for {")
    t.indent += 1
    t.emit(f"{receiver}._ArithSkipWs()")
    t.emit("matched := false")
    for i, op in enumerate(ops):
        cond = "if" if i == 0 else "} else if"
        t.emit(f'{cond} {receiver}._ArithMatch("{op}") {{')
        t.indent += 1
        t.emit(f'{receiver}._ArithConsume("{op}")')
        t.emit(f"{receiver}._ArithSkipWs()")
        t.emit(f'left = NewArithBinaryOp("{op}", left, {receiver}.{next_fn}())')
        t.emit("matched = true")
        t.indent -= 1
    t.emit("}")
    t.emit("if !matched {")
    t.indent += 1
    t.emit("break")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.emit("return left")


# ========== Heredoc methods ==========


def emit_gather_heredoc_bodies(t: "GoTranspiler", receiver: str):
    """Emit full _GatherHeredocBodies implementation."""
    t.emit(f"for _, heredocNode := range {receiver}._Pending_heredocs {{")
    t.indent += 1
    t.emit("heredoc := heredocNode.(*HereDoc)")
    t.emit("var contentLines []string")
    t.emit(f"lineStart := {receiver}.Pos")
    t.emit("")
    t.emit(f"for {receiver}.Pos < {receiver}.Length {{")
    t.indent += 1
    t.emit(f"lineStart = {receiver}.Pos")
    t.emit(f"line, lineEnd := {receiver}._ReadHeredocLine(heredoc.Quoted)")
    t.emit(
        f"matches, checkLine := {receiver}._LineMatchesDelimiter(line, heredoc.Delimiter, heredoc.Strip_tabs)"
    )
    t.emit("")
    t.emit("if matches {")
    t.indent += 1
    t.emit(f"if lineEnd < {receiver}.Length {{")
    t.indent += 1
    t.emit(f"{receiver}.Pos = lineEnd + 1")
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit(f"{receiver}.Pos = lineEnd")
    t.indent -= 1
    t.emit("}")
    t.emit("break")
    t.indent -= 1
    t.emit("}")
    t.emit("")
    t.emit("// Check for delimiter followed by cmdsub/procsub closer")
    t.emit("normalizedCheck := _NormalizeHeredocDelimiter(checkLine)")
    t.emit("normalizedDelim := _NormalizeHeredocDelimiter(heredoc.Delimiter)")
    t.emit("")
    t.emit("// In command substitution: line starts with delimiter")
    t.emit(
        f'if {receiver}._Eof_token == ")" && strings.HasPrefix(normalizedCheck, normalizedDelim) {{'
    )
    t.indent += 1
    t.emit("tabsStripped := len(line) - len(checkLine)")
    t.emit(f"{receiver}.Pos = lineStart + tabsStripped + len(heredoc.Delimiter)")
    t.emit("break")
    t.indent -= 1
    t.emit("}")
    t.emit("")
    t.emit("// At EOF with line starting with delimiter (process sub case)")
    t.emit(f"if lineEnd >= {receiver}.Length &&")
    t.indent += 1
    t.emit("strings.HasPrefix(normalizedCheck, normalizedDelim) &&")
    t.emit(f"{receiver}._In_process_sub {{")
    t.indent -= 1
    t.indent += 1
    t.emit("tabsStripped := len(line) - len(checkLine)")
    t.emit(f"{receiver}.Pos = lineStart + tabsStripped + len(heredoc.Delimiter)")
    t.emit("break")
    t.indent -= 1
    t.emit("}")
    t.emit("")
    t.emit("// Add line to content")
    t.emit("contentLine := line")
    t.emit("if heredoc.Strip_tabs {")
    t.indent += 1
    t.emit('contentLine = strings.TrimLeft(line, "\\t")')
    t.indent -= 1
    t.emit("}")
    t.emit("")
    t.emit(f"if lineEnd < {receiver}.Length {{")
    t.indent += 1
    t.emit('contentLines = append(contentLines, contentLine+"\\n")')
    t.emit(f"{receiver}.Pos = lineEnd + 1")
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit("// EOF - bash keeps trailing newline unless escaped")
    t.emit("addNewline := true")
    t.emit("if !heredoc.Quoted && _CountTrailingBackslashes(line)%2 == 1 {")
    t.indent += 1
    t.emit("addNewline = false")
    t.indent -= 1
    t.emit("}")
    t.emit("if addNewline {")
    t.indent += 1
    t.emit('contentLines = append(contentLines, contentLine+"\\n")')
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit("contentLines = append(contentLines, contentLine)")
    t.indent -= 1
    t.emit("}")
    t.emit(f"{receiver}.Pos = {receiver}.Length")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.emit("")
    t.emit('heredoc.Content = strings.Join(contentLines, "")')
    t.indent -= 1
    t.emit("}")
    t.emit(f"{receiver}._Pending_heredocs = []Node{{}}")


def emit_parse_heredoc(t: "GoTranspiler", receiver: str):
    """Emit _ParseHeredoc with proper type assertion for _pending_heredocs."""
    t.emit(f"startPos := {receiver}.Pos")
    t.emit(f"{receiver}._SetState(ParserStateFlags_PST_HEREDOC)")
    t.emit(f"delimiter, quoted := {receiver}._ParseHeredocDelimiter()")
    t.emit(f"for _, existing := range {receiver}._Pending_heredocs {{")
    t.indent += 1
    t.emit("h := existing.(*HereDoc)")
    t.emit("if h._Start_pos == startPos && h.Delimiter == delimiter {")
    t.indent += 1
    t.emit(f"{receiver}._ClearState(ParserStateFlags_PST_HEREDOC)")
    t.emit("return h")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.emit('heredoc := NewHereDoc(delimiter, "", stripTabs, quoted, fd, false)')
    t.emit("heredoc._Start_pos = startPos")
    t.emit(f"{receiver}._Pending_heredocs = append({receiver}._Pending_heredocs, heredoc)")
    t.emit(f"{receiver}._ClearState(ParserStateFlags_PST_HEREDOC)")
    t.emit("return heredoc")


def emit_parse_process_substitution(t: "GoTranspiler", receiver: str):
    """Emit _ParseProcessSubstitution with panic recovery for try/except pattern."""
    # Initial checks
    t.emit(f"if {receiver}.AtEnd() || !_IsRedirectChar({receiver}.Peek()) {{")
    t.indent += 1
    t.emit('return nil, ""')
    t.indent -= 1
    t.emit("}")
    t.emit("")
    t.emit(f"start := {receiver}.Pos")
    t.emit(f"direction := {receiver}.Advance()")
    t.emit("")
    t.emit(f'if {receiver}.AtEnd() || {receiver}.Peek() != "(" {{')
    t.indent += 1
    t.emit(f"{receiver}.Pos = start")
    t.emit('return nil, ""')
    t.indent -= 1
    t.emit("}")
    t.emit(f"{receiver}.Advance()")
    t.emit("")
    # Save state
    t.emit(f"saved := {receiver}._SaveParserState()")
    t.emit(f"oldInProcessSub := {receiver}._In_process_sub")
    t.emit(f"{receiver}._In_process_sub = true")
    t.emit(f"{receiver}._SetState(ParserStateFlags_PST_EOFTOKEN)")
    t.emit(f'{receiver}._Eof_token = ")"')
    t.emit("")
    # Use defer/recover for panic recovery
    t.emit("var result struct {")
    t.indent += 1
    t.emit("node Node")
    t.emit("text string")
    t.emit("ok   bool")
    t.indent -= 1
    t.emit("}")
    t.emit("")
    t.emit("func() {")
    t.indent += 1
    t.emit("defer func() {")
    t.indent += 1
    t.emit("if r := recover(); r != nil {")
    t.indent += 1
    t.emit("result.ok = false")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}()")
    t.emit("")
    t.emit(f"cmd := {receiver}.ParseList(true)")
    t.emit("if _isNilNode(cmd) {")
    t.indent += 1
    t.emit("cmd = NewEmpty()")
    t.indent -= 1
    t.emit("}")
    t.emit("")
    t.emit(f"{receiver}.SkipWhitespaceAndNewlines()")
    t.emit(f'if {receiver}.AtEnd() || {receiver}.Peek() != ")" {{')
    t.indent += 1
    t.emit('panic("not at closing paren")')
    t.indent -= 1
    t.emit("}")
    t.emit("")
    t.emit(f"{receiver}.Advance()")
    t.emit(f"text := _Substring({receiver}.Source, start, {receiver}.Pos)")
    t.emit("text = _StripLineContinuationsCommentAware(text)")
    t.emit("result.node = NewProcessSubstitution(direction, cmd)")
    t.emit("result.text = text")
    t.emit("result.ok = true")
    t.indent -= 1
    t.emit("}()")
    t.emit("")
    # Restore state
    t.emit(f"{receiver}._RestoreParserState(saved)")
    t.emit(f"{receiver}._In_process_sub = oldInProcessSub")
    t.emit("")
    t.emit("if result.ok {")
    t.indent += 1
    t.emit("return result.node, result.text")
    t.indent -= 1
    t.emit("}")
    t.emit("")
    # Error case - check if we should error or fall back
    t.emit('contentStartChar := ""')
    t.emit(f"if start+2 < {receiver}.Length {{")
    t.indent += 1
    t.emit(f"contentStartChar = string({receiver}.Source[start+2])")
    t.indent -= 1
    t.emit("}")
    t.emit("")
    t.emit(
        'if contentStartChar == " " || contentStartChar == "\\t" || contentStartChar == "\\n" {'
    )
    t.indent += 1
    t.emit('panic(NewParseError("Invalid process substitution", start, 0))')
    t.indent -= 1
    t.emit("}")
    t.emit("")
    # Fall back to matched pair scanning
    t.emit(f"{receiver}.Pos = start + 2")
    t.emit(f"{receiver}._Lexer.Pos = {receiver}.Pos")
    t.emit(f'{receiver}._Lexer._ParseMatchedPair("(", ")", 0, false)')
    t.emit(f"{receiver}.Pos = {receiver}._Lexer.Pos")
    t.emit(f"text := _Substring({receiver}.Source, start, {receiver}.Pos)")
    t.emit("text = _StripLineContinuationsCommentAware(text)")
    t.emit("return nil, text")


def emit_parse_backtick_substitution(t: "GoTranspiler", receiver: str):
    """Emit _ParseBacktickSubstitution with heredoc tracking."""
    # Initial check
    t.emit(f'if {receiver}.AtEnd() || {receiver}.Peek() != "`" {{')
    t.indent += 1
    t.emit('return nil, ""')
    t.indent -= 1
    t.emit("}")
    t.emit("")
    t.emit(f"start := {receiver}.Pos")
    t.emit(f"{receiver}.Advance()")
    t.emit("")
    # Initialize tracking vars
    t.emit("contentChars := []string{}")
    t.emit('textChars := []string{"`"}')
    t.emit("")
    # Heredoc tracking
    t.emit("type heredocInfo struct {")
    t.indent += 1
    t.emit("delimiter string")
    t.emit("stripTabs bool")
    t.indent -= 1
    t.emit("}")
    t.emit("pendingHeredocs := []heredocInfo{}")
    t.emit("inHeredocBody := false")
    t.emit('currentHeredocDelim := ""')
    t.emit("currentHeredocStrip := false")
    t.emit("")
    # Main loop
    t.emit(f'for !{receiver}.AtEnd() && (inHeredocBody || {receiver}.Peek() != "`") {{')
    t.indent += 1
    # Heredoc body mode
    t.emit("if inHeredocBody {")
    t.indent += 1
    t.emit(f"lineStart := {receiver}.Pos")
    t.emit("lineEnd := lineStart")
    t.emit(f'for lineEnd < {receiver}.Length && string({receiver}.Source[lineEnd]) != "\\n" {{')
    t.indent += 1
    t.emit("lineEnd++")
    t.indent -= 1
    t.emit("}")
    t.emit(f"line := _Substring({receiver}.Source, lineStart, lineEnd)")
    t.emit("checkLine := line")
    t.emit("if currentHeredocStrip {")
    t.indent += 1
    t.emit('checkLine = strings.TrimLeft(line, "\\t")')
    t.indent -= 1
    t.emit("}")
    t.emit("")
    # Found delimiter
    t.emit("if checkLine == currentHeredocDelim {")
    t.indent += 1
    t.emit("for _, ch := range line {")
    t.indent += 1
    t.emit("contentChars = append(contentChars, string(ch))")
    t.emit("textChars = append(textChars, string(ch))")
    t.indent -= 1
    t.emit("}")
    t.emit(f"{receiver}.Pos = lineEnd")
    t.emit(
        f'if {receiver}.Pos < {receiver}.Length && string({receiver}.Source[{receiver}.Pos]) == "\\n" {{'
    )
    t.indent += 1
    t.emit('contentChars = append(contentChars, "\\n")')
    t.emit('textChars = append(textChars, "\\n")')
    t.emit(f"{receiver}.Advance()")
    t.indent -= 1
    t.emit("}")
    t.emit("inHeredocBody = false")
    t.emit("if len(pendingHeredocs) > 0 {")
    t.indent += 1
    t.emit("currentHeredocDelim = pendingHeredocs[0].delimiter")
    t.emit("currentHeredocStrip = pendingHeredocs[0].stripTabs")
    t.emit("pendingHeredocs = pendingHeredocs[1:]")
    t.emit("inHeredocBody = true")
    t.indent -= 1
    t.emit("}")
    # Delimiter with trailing content
    t.emit(
        "} else if strings.HasPrefix(checkLine, currentHeredocDelim) && len(checkLine) > len(currentHeredocDelim) {"
    )
    t.indent += 1
    t.emit("tabsStripped := len(line) - len(checkLine)")
    t.emit("endPos := tabsStripped + len(currentHeredocDelim)")
    t.emit("for i := 0; i < endPos; i++ {")
    t.indent += 1
    t.emit("contentChars = append(contentChars, string(line[i]))")
    t.emit("textChars = append(textChars, string(line[i]))")
    t.indent -= 1
    t.emit("}")
    t.emit(f"{receiver}.Pos = lineStart + endPos")
    t.emit("inHeredocBody = false")
    t.emit("if len(pendingHeredocs) > 0 {")
    t.indent += 1
    t.emit("currentHeredocDelim = pendingHeredocs[0].delimiter")
    t.emit("currentHeredocStrip = pendingHeredocs[0].stripTabs")
    t.emit("pendingHeredocs = pendingHeredocs[1:]")
    t.emit("inHeredocBody = true")
    t.indent -= 1
    t.emit("}")
    # Not delimiter - add line
    t.emit("} else {")
    t.indent += 1
    t.emit("for _, ch := range line {")
    t.indent += 1
    t.emit("contentChars = append(contentChars, string(ch))")
    t.emit("textChars = append(textChars, string(ch))")
    t.indent -= 1
    t.emit("}")
    t.emit(f"{receiver}.Pos = lineEnd")
    t.emit(
        f'if {receiver}.Pos < {receiver}.Length && string({receiver}.Source[{receiver}.Pos]) == "\\n" {{'
    )
    t.indent += 1
    t.emit('contentChars = append(contentChars, "\\n")')
    t.emit('textChars = append(textChars, "\\n")')
    t.emit(f"{receiver}.Advance()")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.emit("continue")
    t.indent -= 1
    t.emit("}")
    t.emit("")
    # Normal character processing
    t.emit(f"c := {receiver}.Peek()")
    t.emit("")
    # Escape handling
    t.emit(f'if c == "\\\\" && {receiver}.Pos+1 < {receiver}.Length {{')
    t.indent += 1
    t.emit(f"nextC := string({receiver}.Source[{receiver}.Pos+1])")
    t.emit('if nextC == "\\n" {')
    t.indent += 1
    t.emit(f"{receiver}.Advance()")
    t.emit(f"{receiver}.Advance()")
    t.indent -= 1
    t.emit("} else if _IsEscapeCharInBacktick(nextC) {")
    t.indent += 1
    t.emit(f"{receiver}.Advance()")
    t.emit(f"escaped := {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, escaped)")
    t.emit('textChars = append(textChars, "\\\\")')
    t.emit("textChars = append(textChars, escaped)")
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit(f"ch := {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, ch)")
    t.emit("textChars = append(textChars, ch)")
    t.indent -= 1
    t.emit("}")
    t.emit("continue")
    t.indent -= 1
    t.emit("}")
    t.emit("")
    # Heredoc declaration
    t.emit(
        f'if c == "<" && {receiver}.Pos+1 < {receiver}.Length && string({receiver}.Source[{receiver}.Pos+1]) == "<" {{'
    )
    t.indent += 1
    # Check for here-string <<<
    t.emit(
        f'if {receiver}.Pos+2 < {receiver}.Length && string({receiver}.Source[{receiver}.Pos+2]) == "<" {{'
    )
    t.indent += 1
    t.emit(f"contentChars = append(contentChars, {receiver}.Advance())")
    t.emit('textChars = append(textChars, "<")')
    t.emit(f"contentChars = append(contentChars, {receiver}.Advance())")
    t.emit('textChars = append(textChars, "<")')
    t.emit(f"contentChars = append(contentChars, {receiver}.Advance())")
    t.emit('textChars = append(textChars, "<")')
    t.emit(f"for !{receiver}.AtEnd() && _IsWhitespaceNoNewline({receiver}.Peek()) {{")
    t.indent += 1
    t.emit(f"ch := {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, ch)")
    t.emit("textChars = append(textChars, ch)")
    t.indent -= 1
    t.emit("}")
    t.emit(
        f'for !{receiver}.AtEnd() && !_IsWhitespace({receiver}.Peek()) && {receiver}.Peek() != "(" && {receiver}.Peek() != ")" {{'
    )
    t.indent += 1
    t.emit(f'if {receiver}.Peek() == "\\\\" && {receiver}.Pos+1 < {receiver}.Length {{')
    t.indent += 1
    t.emit(f"ch := {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, ch)")
    t.emit("textChars = append(textChars, ch)")
    t.emit(f"ch = {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, ch)")
    t.emit("textChars = append(textChars, ch)")
    t.emit(f'}} else if {receiver}.Peek() == "\\"" || {receiver}.Peek() == "\'" {{')
    t.indent += 1
    t.emit(f"quote := {receiver}.Peek()")
    t.emit(f"ch := {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, ch)")
    t.emit("textChars = append(textChars, ch)")
    t.emit(f"for !{receiver}.AtEnd() && {receiver}.Peek() != quote {{")
    t.indent += 1
    t.emit(f'if quote == "\\"" && {receiver}.Peek() == "\\\\" {{')
    t.indent += 1
    t.emit(f"ch = {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, ch)")
    t.emit("textChars = append(textChars, ch)")
    t.indent -= 1
    t.emit("}")
    t.emit(f"ch = {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, ch)")
    t.emit("textChars = append(textChars, ch)")
    t.indent -= 1
    t.emit("}")
    t.emit(f"if !{receiver}.AtEnd() {{")
    t.indent += 1
    t.emit(f"ch = {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, ch)")
    t.emit("textChars = append(textChars, ch)")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit(f"ch := {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, ch)")
    t.emit("textChars = append(textChars, ch)")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.emit("continue")
    t.indent -= 1
    t.emit("}")
    t.emit("")
    # Regular heredoc <<
    t.emit(f"contentChars = append(contentChars, {receiver}.Advance())")
    t.emit('textChars = append(textChars, "<")')
    t.emit(f"contentChars = append(contentChars, {receiver}.Advance())")
    t.emit('textChars = append(textChars, "<")')
    t.emit("stripTabs := false")
    t.emit(f'if !{receiver}.AtEnd() && {receiver}.Peek() == "-" {{')
    t.indent += 1
    t.emit("stripTabs = true")
    t.emit(f"contentChars = append(contentChars, {receiver}.Advance())")
    t.emit('textChars = append(textChars, "-")')
    t.indent -= 1
    t.emit("}")
    # Skip whitespace
    t.emit(f"for !{receiver}.AtEnd() && _IsWhitespaceNoNewline({receiver}.Peek()) {{")
    t.indent += 1
    t.emit(f"ch := {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, ch)")
    t.emit("textChars = append(textChars, ch)")
    t.indent -= 1
    t.emit("}")
    # Parse delimiter
    t.emit("delimiterChars := []string{}")
    t.emit(f"if !{receiver}.AtEnd() {{")
    t.indent += 1
    t.emit(f"ch := {receiver}.Peek()")
    t.emit("if _IsQuote(ch) {")
    t.indent += 1
    t.emit(f"quote := {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, quote)")
    t.emit("textChars = append(textChars, quote)")
    t.emit(f"for !{receiver}.AtEnd() && {receiver}.Peek() != quote {{")
    t.indent += 1
    t.emit(f"dch := {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, dch)")
    t.emit("textChars = append(textChars, dch)")
    t.emit("delimiterChars = append(delimiterChars, dch)")
    t.indent -= 1
    t.emit("}")
    t.emit(f"if !{receiver}.AtEnd() {{")
    t.indent += 1
    t.emit(f"closing := {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, closing)")
    t.emit("textChars = append(textChars, closing)")
    t.indent -= 1
    t.emit("}")
    t.emit('} else if ch == "\\\\" {')
    t.indent += 1
    t.emit(f"esc := {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, esc)")
    t.emit("textChars = append(textChars, esc)")
    t.emit(f"if !{receiver}.AtEnd() {{")
    t.indent += 1
    t.emit(f"dch := {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, dch)")
    t.emit("textChars = append(textChars, dch)")
    t.emit("delimiterChars = append(delimiterChars, dch)")
    t.indent -= 1
    t.emit("}")
    t.emit(f"for !{receiver}.AtEnd() && !_IsMetachar({receiver}.Peek()) {{")
    t.indent += 1
    t.emit(f"dch := {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, dch)")
    t.emit("textChars = append(textChars, dch)")
    t.emit("delimiterChars = append(delimiterChars, dch)")
    t.indent -= 1
    t.emit("}")
    t.emit("} else {")
    t.indent += 1
    t.emit(
        f'for !{receiver}.AtEnd() && !_IsMetachar({receiver}.Peek()) && {receiver}.Peek() != "`" {{'
    )
    t.indent += 1
    t.emit(f"ch := {receiver}.Peek()")
    t.emit("if _IsQuote(ch) {")
    t.indent += 1
    t.emit(f"quote := {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, quote)")
    t.emit("textChars = append(textChars, quote)")
    t.emit(f"for !{receiver}.AtEnd() && {receiver}.Peek() != quote {{")
    t.indent += 1
    t.emit(f"dch := {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, dch)")
    t.emit("textChars = append(textChars, dch)")
    t.emit("delimiterChars = append(delimiterChars, dch)")
    t.indent -= 1
    t.emit("}")
    t.emit(f"if !{receiver}.AtEnd() {{")
    t.indent += 1
    t.emit(f"closing := {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, closing)")
    t.emit("textChars = append(textChars, closing)")
    t.indent -= 1
    t.emit("}")
    t.emit('} else if ch == "\\\\" {')
    t.indent += 1
    t.emit(f"esc := {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, esc)")
    t.emit("textChars = append(textChars, esc)")
    t.emit(f"if !{receiver}.AtEnd() {{")
    t.indent += 1
    t.emit(f"dch := {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, dch)")
    t.emit("textChars = append(textChars, dch)")
    t.emit("delimiterChars = append(delimiterChars, dch)")
    t.indent -= 1
    t.emit("}")
    t.emit("} else {")
    t.indent += 1
    t.emit(f"dch := {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, dch)")
    t.emit("textChars = append(textChars, dch)")
    t.emit("delimiterChars = append(delimiterChars, dch)")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.emit('delimiter := strings.Join(delimiterChars, "")')
    t.emit('if delimiter != "" {')
    t.indent += 1
    t.emit("pendingHeredocs = append(pendingHeredocs, heredocInfo{delimiter, stripTabs})")
    t.indent -= 1
    t.emit("}")
    t.emit("continue")
    t.indent -= 1
    t.emit("}")
    t.emit("")
    # Newline - check for heredoc body mode
    t.emit('if c == "\\n" {')
    t.indent += 1
    t.emit(f"ch := {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, ch)")
    t.emit("textChars = append(textChars, ch)")
    t.emit("if len(pendingHeredocs) > 0 {")
    t.indent += 1
    t.emit("currentHeredocDelim = pendingHeredocs[0].delimiter")
    t.emit("currentHeredocStrip = pendingHeredocs[0].stripTabs")
    t.emit("pendingHeredocs = pendingHeredocs[1:]")
    t.emit("inHeredocBody = true")
    t.indent -= 1
    t.emit("}")
    t.emit("continue")
    t.indent -= 1
    t.emit("}")
    t.emit("")
    # Regular character
    t.emit(f"ch := {receiver}.Advance()")
    t.emit("contentChars = append(contentChars, ch)")
    t.emit("textChars = append(textChars, ch)")
    t.indent -= 1
    t.emit("}")
    t.emit("")
    # Check for unterminated backtick
    t.emit(f"if {receiver}.AtEnd() {{")
    t.indent += 1
    t.emit('panic(NewParseError("Unterminated backtick", start, 0))')
    t.indent -= 1
    t.emit("}")
    t.emit("")
    t.emit(f"{receiver}.Advance()")
    t.emit('textChars = append(textChars, "`")')
    t.emit('text := strings.Join(textChars, "")')
    t.emit('content := strings.Join(contentChars, "")')
    t.emit("")
    # Handle heredocs whose bodies follow the closing backtick
    t.emit("if len(pendingHeredocs) > 0 {")
    t.indent += 1
    t.emit("delimiters := make([]interface{}, len(pendingHeredocs))")
    t.emit("for i, h := range pendingHeredocs {")
    t.indent += 1
    t.emit("delimiters[i] = []interface{}{h.delimiter, h.stripTabs}")
    t.indent -= 1
    t.emit("}")
    t.emit(
        f"heredocStart, heredocEnd := _FindHeredocContentEnd({receiver}.Source, {receiver}.Pos, delimiters)"
    )
    t.emit("if heredocEnd > heredocStart {")
    t.indent += 1
    t.emit(f"content = content + _Substring({receiver}.Source, heredocStart, heredocEnd)")
    t.emit(f"if {receiver}._Cmdsub_heredoc_end < 0 {{")
    t.indent += 1
    t.emit(f"{receiver}._Cmdsub_heredoc_end = heredocEnd")
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit(f"if heredocEnd > {receiver}._Cmdsub_heredoc_end {{")
    t.indent += 1
    t.emit(f"{receiver}._Cmdsub_heredoc_end = heredocEnd")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.emit("")
    # Parse the content as a command list
    t.emit(f"subParser := NewParser(content, false, {receiver}._Extglob)")
    t.emit("cmd := subParser.ParseList(true)")
    t.emit("if _isNilNode(cmd) {")
    t.indent += 1
    t.emit("cmd = NewEmpty()")
    t.indent -= 1
    t.emit("}")
    t.emit("")
    t.emit("return NewCommandSubstitution(cmd, false), text")


def emit_parse_command_substitution(t: "GoTranspiler", receiver: str):
    """Emit _ParseCommandSubstitution with _isNilNode check for typed nil."""
    # Variable declarations
    t.emit("var start int")
    t.emit("_ = start")
    t.emit("var saved *SavedParserState")
    t.emit("_ = saved")
    t.emit("var cmd Node")
    t.emit("_ = cmd")
    t.emit("var textEnd int")
    t.emit("_ = textEnd")
    t.emit("var text string")
    t.emit("_ = text")
    # Initial checks
    t.emit(f'if {receiver}.AtEnd() || {receiver}.Peek() != "$" {{')
    t.indent += 1
    t.emit('return nil, ""')
    t.indent -= 1
    t.emit("}")
    t.emit(f"start = {receiver}.Pos")
    t.emit(f"{receiver}.Advance()")
    t.emit("")
    t.emit(f'if {receiver}.AtEnd() || {receiver}.Peek() != "(" {{')
    t.indent += 1
    t.emit(f"{receiver}.Pos = start")
    t.emit('return nil, ""')
    t.indent -= 1
    t.emit("}")
    t.emit(f"{receiver}.Advance()")
    t.emit("")
    # Save state and set up for parsing
    t.emit(f"saved = {receiver}._SaveParserState()")
    t.emit(
        f"{receiver}._SetState(ParserStateFlags_PST_CMDSUBST | ParserStateFlags_PST_EOFTOKEN)"
    )
    t.emit(f'{receiver}._Eof_token = ")"')
    t.emit("")
    # Parse command list with _isNilNode check for typed nil
    t.emit(f"cmd = {receiver}.ParseList(true)")
    t.emit("if _isNilNode(cmd) {")
    t.indent += 1
    t.emit("cmd = NewEmpty()")
    t.indent -= 1
    t.emit("}")
    t.emit("")
    # Check for closing paren
    t.emit(f"{receiver}.SkipWhitespaceAndNewlines()")
    t.emit(f'if {receiver}.AtEnd() || {receiver}.Peek() != ")" {{')
    t.indent += 1
    t.emit(f"{receiver}._RestoreParserState(saved)")
    t.emit(f"{receiver}.Pos = start")
    t.emit('return nil, ""')
    t.indent -= 1
    t.emit("}")
    t.emit("")
    t.emit(f"{receiver}.Advance()")
    t.emit(f"textEnd = {receiver}.Pos")
    t.emit(f"text = _Substring({receiver}.Source, start, textEnd)")
    t.emit("")
    t.emit(f"{receiver}._RestoreParserState(saved)")
    t.emit("return NewCommandSubstitution(cmd, false), text")


def emit_parse_funsub(t: "GoTranspiler", receiver: str):
    """Emit _ParseFunsub with _isNilNode check for typed nil."""
    # Variable declarations
    t.emit("var saved *SavedParserState")
    t.emit("_ = saved")
    t.emit("var cmd Node")
    t.emit("_ = cmd")
    t.emit("var text string")
    t.emit("_ = text")
    # Sync parser and skip leading |
    t.emit(f"{receiver}._SyncParser()")
    t.emit(f'if !({receiver}.AtEnd()) && {receiver}.Peek() == "|" {{')
    t.indent += 1
    t.emit(f"{receiver}.Advance()")
    t.indent -= 1
    t.emit("}")
    t.emit("")
    # Save state and set up for parsing
    t.emit(f"saved = {receiver}._SaveParserState()")
    t.emit(
        f"{receiver}._SetState(ParserStateFlags_PST_CMDSUBST | ParserStateFlags_PST_EOFTOKEN)"
    )
    t.emit(f'{receiver}._Eof_token = "}}"')
    t.emit("")
    # Parse command list with _isNilNode check for typed nil
    t.emit(f"cmd = {receiver}.ParseList(true)")
    t.emit("if _isNilNode(cmd) {")
    t.indent += 1
    t.emit("cmd = NewEmpty()")
    t.indent -= 1
    t.emit("}")
    t.emit("")
    # Check for closing brace
    t.emit(f"{receiver}.SkipWhitespaceAndNewlines()")
    t.emit(f'if {receiver}.AtEnd() || {receiver}.Peek() != "}}" {{')
    t.indent += 1
    t.emit(f"{receiver}._RestoreParserState(saved)")
    t.emit('panic(NewMatchedPairError("unexpected EOF looking for `}\'", start, 0))')
    t.indent -= 1
    t.emit("}")
    t.emit("")
    t.emit(f"{receiver}.Advance()")
    t.emit(f"text = _Substring({receiver}.Source, start, {receiver}.Pos)")
    t.emit(f"{receiver}._RestoreParserState(saved)")
    t.emit(f"{receiver}._SyncLexer()")
    t.emit("return NewCommandSubstitution(cmd, true), text")


# ========== Manual functions (module-level) ==========


def emit_format_heredoc_body(t: "GoTranspiler"):
    """Emit _FormatHeredocBody body."""
    t.emit("h := r.(*HereDoc)")
    t.emit('return "\\n" + h.Content + h.Delimiter + "\\n"')


def emit_starts_with_subshell(t: "GoTranspiler"):
    """Emit _StartsWithSubshell body."""
    t.emit('if node.Kind() == "subshell" {')
    t.indent += 1
    t.emit("return true")
    t.indent -= 1
    t.emit("}")
    t.emit('if node.Kind() == "list" {')
    t.indent += 1
    t.emit("list := node.(*List)")
    t.emit("for _, p := range list.Parts {")
    t.indent += 1
    t.emit('if p.Kind() != "operator" {')
    t.indent += 1
    t.emit("return _StartsWithSubshell(p)")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.emit("return false")
    t.indent -= 1
    t.emit("}")
    t.emit('if node.Kind() == "pipeline" {')
    t.indent += 1
    t.emit("pipeline := node.(*Pipeline)")
    t.emit("if len(pipeline.Commands) > 0 {")
    t.indent += 1
    t.emit("return _StartsWithSubshell(pipeline.Commands[0])")
    t.indent -= 1
    t.emit("}")
    t.emit("return false")
    t.indent -= 1
    t.emit("}")
    t.emit("return false")


def emit_format_cond_body(t: "GoTranspiler"):
    """Emit _FormatCondBody body."""
    t.emit("kind := node.Kind()")
    t.emit('if kind == "unary-test" {')
    t.indent += 1
    t.emit("ut := node.(*UnaryTest)")
    t.emit("operandVal := ut.Operand.(*Word).GetCondFormattedValue()")
    t.emit('return ut.Op + " " + operandVal')
    t.indent -= 1
    t.emit("}")
    t.emit('if kind == "binary-test" {')
    t.indent += 1
    t.emit("bt := node.(*BinaryTest)")
    t.emit("leftVal := bt.Left.(*Word).GetCondFormattedValue()")
    t.emit("rightVal := bt.Right.(*Word).GetCondFormattedValue()")
    t.emit('return leftVal + " " + bt.Op + " " + rightVal')
    t.indent -= 1
    t.emit("}")
    t.emit('if kind == "cond-and" {')
    t.indent += 1
    t.emit("ca := node.(*CondAnd)")
    t.emit('return _FormatCondBody(ca.Left) + " && " + _FormatCondBody(ca.Right)')
    t.indent -= 1
    t.emit("}")
    t.emit('if kind == "cond-or" {')
    t.indent += 1
    t.emit("co := node.(*CondOr)")
    t.emit('return _FormatCondBody(co.Left) + " || " + _FormatCondBody(co.Right)')
    t.indent -= 1
    t.emit("}")
    t.emit('if kind == "cond-not" {')
    t.indent += 1
    t.emit("cn := node.(*CondNot)")
    t.emit('return "! " + _FormatCondBody(cn.Operand)')
    t.indent -= 1
    t.emit("}")
    t.emit('if kind == "cond-paren" {')
    t.indent += 1
    t.emit("cp := node.(*CondParen)")
    t.emit('return "( " + _FormatCondBody(cp.Inner) + " )"')
    t.indent -= 1
    t.emit("}")
    t.emit('return ""')


def emit_format_redirect(t: "GoTranspiler"):
    """Emit _FormatRedirect body."""
    t.emit('if r.Kind() == "heredoc" {')
    t.indent += 1
    t.emit("h := r.(*HereDoc)")
    t.emit("var op string")
    t.emit("if h.Strip_tabs {")
    t.indent += 1
    t.emit('op = "<<-"')
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit('op = "<<"')
    t.indent -= 1
    t.emit("}")
    t.emit("if h.Fd > 0 {")
    t.indent += 1
    t.emit("op = strconv.Itoa(h.Fd) + op")
    t.indent -= 1
    t.emit("}")
    t.emit("var delim string")
    t.emit("if h.Quoted {")
    t.indent += 1
    t.emit('delim = "\'" + h.Delimiter + "\'"')
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit("delim = h.Delimiter")
    t.indent -= 1
    t.emit("}")
    t.emit("if heredocOpOnly {")
    t.indent += 1
    t.emit("return op + delim")
    t.indent -= 1
    t.emit("}")
    t.emit('return op + delim + "\\n" + h.Content + h.Delimiter + "\\n"')
    t.indent -= 1
    t.emit("}")
    t.emit("rd := r.(*Redirect)")
    t.emit("op := rd.Op")
    t.emit('if op == "1>" {')
    t.indent += 1
    t.emit('op = ">"')
    t.indent -= 1
    t.emit('} else if op == "0<" {')
    t.indent += 1
    t.emit('op = "<"')
    t.indent -= 1
    t.emit("}")
    t.emit("targetWord := rd.Target.(*Word)")
    t.emit("target := targetWord.Value")
    t.emit("target = targetWord._ExpandAllAnsiCQuotes(target)")
    t.emit("target = targetWord._StripLocaleStringDollars(target)")
    t.emit("target = targetWord._FormatCommandSubstitutions(target, false)")
    t.emit('if strings.HasPrefix(target, "&") {')
    t.indent += 1
    t.emit("wasInputClose := false")
    t.emit('if target == "&-" && strings.HasSuffix(op, "<") {')
    t.indent += 1
    t.emit("wasInputClose = true")
    t.emit('op = _Substring(op, 0, len(op)-1) + ">"')
    t.indent -= 1
    t.emit("}")
    t.emit("afterAmp := _Substring(target, 1, len(target))")
    t.emit(
        "isLiteralFd := afterAmp == \"-\" || (len(afterAmp) > 0 && afterAmp[0] >= '0' && afterAmp[0] <= '9')"
    )
    t.emit("if isLiteralFd {")
    t.indent += 1
    t.emit('if op == ">" || op == ">&" {')
    t.indent += 1
    t.emit("if wasInputClose {")
    t.indent += 1
    t.emit('op = "0>"')
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit('op = "1>"')
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit('} else if op == "<" || op == "<&" {')
    t.indent += 1
    t.emit('op = "0<"')
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit('if op == "1>" {')
    t.indent += 1
    t.emit('op = ">"')
    t.indent -= 1
    t.emit('} else if op == "0<" {')
    t.indent += 1
    t.emit('op = "<"')
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.emit("return op + target")
    t.indent -= 1
    t.emit("}")
    t.emit('if strings.HasSuffix(op, "&") {')
    t.indent += 1
    t.emit("return op + target")
    t.indent -= 1
    t.emit("}")
    t.emit("if compact {")
    t.indent += 1
    t.emit("return op + target")
    t.indent -= 1
    t.emit("}")
    t.emit('return op + " " + target')


def emit_find_heredoc_content_end(t: "GoTranspiler"):
    """Emit _FindHeredocContentEnd body."""
    t.emit("if len(delimiters) == 0 {")
    t.indent += 1
    t.emit("return start, start")
    t.indent -= 1
    t.emit("}")
    t.emit("pos := start")
    t.emit('for pos < len(source) && string(source[pos]) != "\\n" {')
    t.indent += 1
    t.emit("pos++")
    t.indent -= 1
    t.emit("}")
    t.emit("if pos >= len(source) {")
    t.indent += 1
    t.emit("return start, start")
    t.indent -= 1
    t.emit("}")
    t.emit("contentStart := pos")
    t.emit("pos++")
    t.emit("for _, dt := range delimiters {")
    t.indent += 1
    t.emit("delimTuple := dt.([]interface{})")
    t.emit("delimiter := delimTuple[0].(string)")
    t.emit("stripTabs := delimTuple[1].(bool)")
    t.emit("for pos < len(source) {")
    t.indent += 1
    t.emit("lineStart := pos")
    t.emit("lineEnd := pos")
    t.emit('for lineEnd < len(source) && string(source[lineEnd]) != "\\n" {')
    t.indent += 1
    t.emit("lineEnd++")
    t.indent -= 1
    t.emit("}")
    t.emit("line := _Substring(source, lineStart, lineEnd)")
    t.emit("for lineEnd < len(source) {")
    t.indent += 1
    t.emit("trailingBs := 0")
    t.emit("for j := len(line) - 1; j >= 0; j-- {")
    t.indent += 1
    t.emit('if string(line[j]) == "\\\\" {')
    t.indent += 1
    t.emit("trailingBs++")
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit("break")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.emit("if trailingBs%2 == 0 {")
    t.indent += 1
    t.emit("break")
    t.indent -= 1
    t.emit("}")
    t.emit("line = _Substring(line, 0, len(line)-1)")
    t.emit("lineEnd++")
    t.emit("nextLineStart := lineEnd")
    t.emit('for lineEnd < len(source) && string(source[lineEnd]) != "\\n" {')
    t.indent += 1
    t.emit("lineEnd++")
    t.indent -= 1
    t.emit("}")
    t.emit("line = line + _Substring(source, nextLineStart, lineEnd)")
    t.indent -= 1
    t.emit("}")
    t.emit("var lineStripped string")
    t.emit("if stripTabs {")
    t.indent += 1
    t.emit('lineStripped = strings.TrimLeft(line, "\\t")')
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit("lineStripped = line")
    t.indent -= 1
    t.emit("}")
    t.emit("if lineStripped == delimiter {")
    t.indent += 1
    t.emit("if lineEnd < len(source) {")
    t.indent += 1
    t.emit("pos = lineEnd + 1")
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit("pos = lineEnd")
    t.indent -= 1
    t.emit("}")
    t.emit("break")
    t.indent -= 1
    t.emit("}")
    t.emit(
        "if strings.HasPrefix(lineStripped, delimiter) && len(lineStripped) > len(delimiter) {"
    )
    t.indent += 1
    t.emit("tabsStripped := len(line) - len(lineStripped)")
    t.emit("pos = lineStart + tabsStripped + len(delimiter)")
    t.emit("break")
    t.indent -= 1
    t.emit("}")
    t.emit("if lineEnd < len(source) {")
    t.indent += 1
    t.emit("pos = lineEnd + 1")
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit("pos = lineEnd")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.emit("return contentStart, pos")


def emit_format_cmdsub_node(t: "GoTranspiler"):
    """Emit _FormatCmdsubNode body - large switch on node.Kind()."""
    t.emit("if _isNilNode(node) {")
    t.indent += 1
    t.emit('return ""')
    t.indent -= 1
    t.emit("}")
    t.emit('sp := _RepeatStr(" ", indent)')
    t.emit('innerSp := _RepeatStr(" ", indent+4)')
    t.emit("switch node.Kind() {")
    # case "empty"
    t.emit('case "empty":')
    t.indent += 1
    t.emit('return ""')
    t.indent -= 1
    # case "command"
    t.emit('case "command":')
    t.indent += 1
    t.emit("cmd := node.(*Command)")
    t.emit("parts := []string{}")
    t.emit("for _, wn := range cmd.Words {")
    t.indent += 1
    t.emit("w := wn.(*Word)")
    t.emit("val := w._ExpandAllAnsiCQuotes(w.Value)")
    t.emit("val = w._StripLocaleStringDollars(val)")
    t.emit("val = w._NormalizeArrayWhitespace(val)")
    t.emit("val = w._FormatCommandSubstitutions(val, false)")
    t.emit("parts = append(parts, val)")
    t.indent -= 1
    t.emit("}")
    t.emit("heredocs := []Node{}")
    t.emit("for _, r := range cmd.Redirects {")
    t.indent += 1
    t.emit('if r.Kind() == "heredoc" {')
    t.indent += 1
    t.emit("heredocs = append(heredocs, r)")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.emit("for _, r := range cmd.Redirects {")
    t.indent += 1
    t.emit("parts = append(parts, _FormatRedirect(r, compactRedirects, true))")
    t.indent -= 1
    t.emit("}")
    t.emit("var result string")
    t.emit("if compactRedirects && len(cmd.Words) > 0 && len(cmd.Redirects) > 0 {")
    t.indent += 1
    t.emit('wordParts := strings.Join(parts[:len(cmd.Words)], " ")')
    t.emit('redirectParts := strings.Join(parts[len(cmd.Words):], "")')
    t.emit("result = wordParts + redirectParts")
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit('result = strings.Join(parts, " ")')
    t.indent -= 1
    t.emit("}")
    t.emit("for _, h := range heredocs {")
    t.indent += 1
    t.emit("result = result + _FormatHeredocBody(h)")
    t.indent -= 1
    t.emit("}")
    t.emit("return result")
    t.indent -= 1
    # case "pipeline"
    t.emit('case "pipeline":')
    t.indent += 1
    t.emit("pipeline := node.(*Pipeline)")
    t.emit("type cmdPair struct {")
    t.indent += 1
    t.emit("cmd Node")
    t.emit("needsRedirect bool")
    t.indent -= 1
    t.emit("}")
    t.emit("cmds := []cmdPair{}")
    t.emit("i := 0")
    t.emit("for i < len(pipeline.Commands) {")
    t.indent += 1
    t.emit("c := pipeline.Commands[i]")
    t.emit('if c.Kind() == "pipe-both" {')
    t.indent += 1
    t.emit("i++")
    t.emit("continue")
    t.indent -= 1
    t.emit("}")
    t.emit(
        'needsRedirect := i+1 < len(pipeline.Commands) && pipeline.Commands[i+1].Kind() == "pipe-both"'
    )
    t.emit("cmds = append(cmds, cmdPair{c, needsRedirect})")
    t.emit("i++")
    t.indent -= 1
    t.emit("}")
    t.emit("resultParts := []string{}")
    t.emit("for idx, pair := range cmds {")
    t.indent += 1
    t.emit(
        "formatted := _FormatCmdsubNode(pair.cmd, indent, inProcsub, false, procsubFirst && idx == 0)"
    )
    t.emit("isLast := idx == len(cmds)-1")
    t.emit("hasHeredoc := false")
    t.emit('if pair.cmd.Kind() == "command" {')
    t.indent += 1
    t.emit("c := pair.cmd.(*Command)")
    t.emit("for _, r := range c.Redirects {")
    t.indent += 1
    t.emit('if r.Kind() == "heredoc" {')
    t.indent += 1
    t.emit("hasHeredoc = true")
    t.emit("break")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.emit("if pair.needsRedirect {")
    t.indent += 1
    t.emit("if hasHeredoc {")
    t.indent += 1
    t.emit('firstNl := strings.Index(formatted, "\\n")')
    t.emit("if firstNl != -1 {")
    t.indent += 1
    t.emit(
        'formatted = _Substring(formatted, 0, firstNl) + " 2>&1" + _Substring(formatted, firstNl, len(formatted))'
    )
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit('formatted = formatted + " 2>&1"')
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit('formatted = formatted + " 2>&1"')
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.emit("if !isLast && hasHeredoc {")
    t.indent += 1
    t.emit('firstNl := strings.Index(formatted, "\\n")')
    t.emit("if firstNl != -1 {")
    t.indent += 1
    t.emit(
        'formatted = _Substring(formatted, 0, firstNl) + " |" + _Substring(formatted, firstNl, len(formatted))'
    )
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.emit("resultParts = append(resultParts, formatted)")
    t.indent -= 1
    t.emit("}")
    t.emit('compactPipe := inProcsub && len(cmds) > 0 && cmds[0].cmd.Kind() == "subshell"')
    t.emit('result := ""')
    t.emit("for idx, part := range resultParts {")
    t.indent += 1
    t.emit("if idx > 0 {")
    t.indent += 1
    t.emit('if strings.HasSuffix(result, "\\n") {')
    t.indent += 1
    t.emit('result = result + "  " + part')
    t.indent -= 1
    t.emit("} else if compactPipe {")
    t.indent += 1
    t.emit('result = result + "|" + part')
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit('result = result + " | " + part')
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit("result = part")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.emit("return result")
    t.indent -= 1
    # Continue with case "list" in next edit...
    _emit_format_cmdsub_node_list(t)
    _emit_format_cmdsub_node_remaining(t)


def _emit_format_cmdsub_node_list(t: "GoTranspiler"):
    """Helper to emit the list case of _FormatCmdsubNode."""
    # case "list"
    t.emit('case "list":')
    t.indent += 1
    t.emit("list := node.(*List)")
    t.emit("hasHeredoc := false")
    t.emit("for _, p := range list.Parts {")
    t.indent += 1
    t.emit('if p.Kind() == "command" {')
    t.indent += 1
    t.emit("c := p.(*Command)")
    t.emit("for _, r := range c.Redirects {")
    t.indent += 1
    t.emit('if r.Kind() == "heredoc" {')
    t.indent += 1
    t.emit("hasHeredoc = true")
    t.emit("break")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit('} else if p.Kind() == "pipeline" {')
    t.indent += 1
    t.emit("pl := p.(*Pipeline)")
    t.emit("for _, c := range pl.Commands {")
    t.indent += 1
    t.emit('if c.Kind() == "command" {')
    t.indent += 1
    t.emit("cmd := c.(*Command)")
    t.emit("for _, r := range cmd.Redirects {")
    t.indent += 1
    t.emit('if r.Kind() == "heredoc" {')
    t.indent += 1
    t.emit("hasHeredoc = true")
    t.emit("break")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.emit("if hasHeredoc {")
    t.indent += 1
    t.emit("break")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.emit("resultList := []string{}")
    t.emit("skippedSemi := false")
    t.emit("cmdCount := 0")
    t.emit("for _, p := range list.Parts {")
    t.indent += 1
    t.emit('if p.Kind() == "operator" {')
    t.indent += 1
    t.emit("op := p.(*Operator)")
    t.emit('if op.Op == ";" {')
    t.indent += 1
    t.emit(
        'if len(resultList) > 0 && strings.HasSuffix(resultList[len(resultList)-1], "\\n") {'
    )
    t.indent += 1
    t.emit("skippedSemi = true")
    t.emit("continue")
    t.indent -= 1
    t.emit("}")
    t.emit(
        'if len(resultList) >= 3 && resultList[len(resultList)-2] == "\\n" && strings.HasSuffix(resultList[len(resultList)-3], "\\n") {'
    )
    t.indent += 1
    t.emit("skippedSemi = true")
    t.emit("continue")
    t.indent -= 1
    t.emit("}")
    t.emit('resultList = append(resultList, ";")')
    t.emit("skippedSemi = false")
    t.indent -= 1
    t.emit('} else if op.Op == "\\n" {')
    t.indent += 1
    t.emit('if len(resultList) > 0 && resultList[len(resultList)-1] == ";" {')
    t.indent += 1
    t.emit("skippedSemi = false")
    t.emit("continue")
    t.indent -= 1
    t.emit("}")
    t.emit(
        'if len(resultList) > 0 && strings.HasSuffix(resultList[len(resultList)-1], "\\n") {'
    )
    t.indent += 1
    t.emit("if skippedSemi {")
    t.indent += 1
    t.emit('resultList = append(resultList, " ")')
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit('resultList = append(resultList, "\\n")')
    t.indent -= 1
    t.emit("}")
    t.emit("skippedSemi = false")
    t.emit("continue")
    t.indent -= 1
    t.emit("}")
    t.emit('resultList = append(resultList, "\\n")')
    t.emit("skippedSemi = false")
    t.indent -= 1
    t.emit('} else if op.Op == "&" {')
    t.indent += 1
    t.emit(
        'if len(resultList) > 0 && strings.Contains(resultList[len(resultList)-1], "<<") && strings.Contains(resultList[len(resultList)-1], "\\n") {'
    )
    t.indent += 1
    t.emit("last := resultList[len(resultList)-1]")
    t.emit('if strings.Contains(last, " |") || strings.HasPrefix(last, "|") {')
    t.indent += 1
    t.emit('resultList[len(resultList)-1] = last + " &"')
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit('firstNl := strings.Index(last, "\\n")')
    t.emit(
        'resultList[len(resultList)-1] = _Substring(last, 0, firstNl) + " &" + _Substring(last, firstNl, len(last))'
    )
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit('resultList = append(resultList, " &")')
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit(
        'if len(resultList) > 0 && strings.Contains(resultList[len(resultList)-1], "<<") && strings.Contains(resultList[len(resultList)-1], "\\n") {'
    )
    t.indent += 1
    t.emit("last := resultList[len(resultList)-1]")
    t.emit('firstNl := strings.Index(last, "\\n")')
    t.emit(
        'resultList[len(resultList)-1] = _Substring(last, 0, firstNl) + " " + op.Op + " " + _Substring(last, firstNl, len(last))'
    )
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit('resultList = append(resultList, " "+op.Op)')
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.emit("continue")
    t.indent -= 1
    t.emit("}")
    # Non-operator handling (no else needed, continue skips this for operators)
    t.emit(
        'if len(resultList) > 0 && !strings.HasSuffix(resultList[len(resultList)-1], " ") && !strings.HasSuffix(resultList[len(resultList)-1], "\\n") {'
    )
    t.indent += 1
    t.emit('resultList = append(resultList, " ")')
    t.indent -= 1
    t.emit("}")
    t.emit(
        "formattedCmd := _FormatCmdsubNode(p, indent, inProcsub, compactRedirects, procsubFirst && cmdCount == 0)"
    )
    t.emit("if len(resultList) > 0 {")
    t.indent += 1
    t.emit("last := resultList[len(resultList)-1]")
    t.emit('if strings.Contains(last, " || \\n") || strings.Contains(last, " && \\n") {')
    t.indent += 1
    t.emit('formattedCmd = " " + formattedCmd')
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.emit("if skippedSemi {")
    t.indent += 1
    t.emit('formattedCmd = " " + formattedCmd')
    t.emit("skippedSemi = false")
    t.indent -= 1
    t.emit("}")
    t.emit("resultList = append(resultList, formattedCmd)")
    t.emit("cmdCount++")
    t.indent -= 1
    t.emit("}")
    t.emit('s := strings.Join(resultList, "")')
    t.emit('if strings.Contains(s, " &\\n") && strings.HasSuffix(s, "\\n") {')
    t.indent += 1
    t.emit('return s + " "')
    t.indent -= 1
    t.emit("}")
    t.emit('for strings.HasSuffix(s, ";") {')
    t.indent += 1
    t.emit("s = _Substring(s, 0, len(s)-1)")
    t.indent -= 1
    t.emit("}")
    t.emit("if !hasHeredoc {")
    t.indent += 1
    t.emit('s = strings.TrimSuffix(s, "\\n")')
    t.indent -= 1
    t.emit("}")
    t.emit("return s")
    t.indent -= 1


def _emit_format_cmdsub_node_remaining(t: "GoTranspiler"):
    """Helper to emit remaining cases of _FormatCmdsubNode."""
    # case "if"
    t.emit('case "if":')
    t.indent += 1
    t.emit("ifNode := node.(*If)")
    t.emit("cond := _FormatCmdsubNode(ifNode.Condition, indent, false, false, false)")
    t.emit("thenBody := _FormatCmdsubNode(ifNode.Then_body, indent+4, false, false, false)")
    t.emit('result := "if " + cond + "; then\\n" + innerSp + thenBody + ";"')
    t.emit("if ifNode.Else_body != nil {")
    t.indent += 1
    t.emit("elseBody := _FormatCmdsubNode(ifNode.Else_body, indent+4, false, false, false)")
    t.emit('result = result + "\\n" + sp + "else\\n" + innerSp + elseBody + ";"')
    t.indent -= 1
    t.emit("}")
    t.emit('result = result + "\\n" + sp + "fi"')
    t.emit("return result")
    t.indent -= 1
    # case "while"
    t.emit('case "while":')
    t.indent += 1
    t.emit("whileNode := node.(*While)")
    t.emit("cond := _FormatCmdsubNode(whileNode.Condition, indent, false, false, false)")
    t.emit("body := _FormatCmdsubNode(whileNode.Body, indent+4, false, false, false)")
    t.emit('result := "while " + cond + "; do\\n" + innerSp + body + ";\\n" + sp + "done"')
    t.emit("for _, r := range whileNode.Redirects {")
    t.indent += 1
    t.emit('result = result + " " + _FormatRedirect(r, false, false)')
    t.indent -= 1
    t.emit("}")
    t.emit("return result")
    t.indent -= 1
    # case "until"
    t.emit('case "until":')
    t.indent += 1
    t.emit("untilNode := node.(*Until)")
    t.emit("cond := _FormatCmdsubNode(untilNode.Condition, indent, false, false, false)")
    t.emit("body := _FormatCmdsubNode(untilNode.Body, indent+4, false, false, false)")
    t.emit('result := "until " + cond + "; do\\n" + innerSp + body + ";\\n" + sp + "done"')
    t.emit("for _, r := range untilNode.Redirects {")
    t.indent += 1
    t.emit('result = result + " " + _FormatRedirect(r, false, false)')
    t.indent -= 1
    t.emit("}")
    t.emit("return result")
    t.indent -= 1
    # case "for"
    t.emit('case "for":')
    t.indent += 1
    t.emit("forNode := node.(*For)")
    t.emit("varName := forNode.Var")
    t.emit("body := _FormatCmdsubNode(forNode.Body, indent+4, false, false, false)")
    t.emit("var result string")
    t.emit("if forNode.Words != nil {")
    t.indent += 1
    t.emit("wordVals := []string{}")
    t.emit("for _, wn := range forNode.Words {")
    t.indent += 1
    t.emit("wordVals = append(wordVals, wn.(*Word).Value)")
    t.indent -= 1
    t.emit("}")
    t.emit('words := strings.Join(wordVals, " ")')
    t.emit('if words != "" {')
    t.indent += 1
    t.emit(
        'result = "for " + varName + " in " + words + ";\\n" + sp + "do\\n" + innerSp + body + ";\\n" + sp + "done"'
    )
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit(
        'result = "for " + varName + " in ;\\n" + sp + "do\\n" + innerSp + body + ";\\n" + sp + "done"'
    )
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit(
        'result = "for " + varName + " in \\"$@\\";\\n" + sp + "do\\n" + innerSp + body + ";\\n" + sp + "done"'
    )
    t.indent -= 1
    t.emit("}")
    t.emit("for _, r := range forNode.Redirects {")
    t.indent += 1
    t.emit('result = result + " " + _FormatRedirect(r, false, false)')
    t.indent -= 1
    t.emit("}")
    t.emit("return result")
    t.indent -= 1
    # case "for-arith"
    t.emit('case "for-arith":')
    t.indent += 1
    t.emit("forArith := node.(*ForArith)")
    t.emit("body := _FormatCmdsubNode(forArith.Body, indent+4, false, false, false)")
    t.emit(
        'result := "for ((" + forArith.Init + "; " + forArith.Cond + "; " + forArith.Incr + "))\\ndo\\n" + innerSp + body + ";\\n" + sp + "done"'
    )
    t.emit("for _, r := range forArith.Redirects {")
    t.indent += 1
    t.emit('result = result + " " + _FormatRedirect(r, false, false)')
    t.indent -= 1
    t.emit("}")
    t.emit("return result")
    t.indent -= 1
    # case "select"
    t.emit('case "select":')
    t.indent += 1
    t.emit("selectNode := node.(*Select)")
    t.emit("varName := selectNode.Var")
    t.emit("body := _FormatCmdsubNode(selectNode.Body, indent+4, false, false, false)")
    t.emit("var result string")
    t.emit("if selectNode.Words != nil {")
    t.indent += 1
    t.emit("wordVals := []string{}")
    t.emit("for _, wn := range selectNode.Words {")
    t.indent += 1
    t.emit("wordVals = append(wordVals, wn.(*Word).Value)")
    t.indent -= 1
    t.emit("}")
    t.emit('words := strings.Join(wordVals, " ")')
    t.emit('if words != "" {')
    t.indent += 1
    t.emit(
        'result = "select " + varName + " in " + words + ";\\n" + sp + "do\\n" + innerSp + body + ";\\n" + sp + "done"'
    )
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit(
        'result = "select " + varName + " in ;\\n" + sp + "do\\n" + innerSp + body + ";\\n" + sp + "done"'
    )
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit(
        'result = "select " + varName + " in \\"$@\\";\\n" + sp + "do\\n" + innerSp + body + ";\\n" + sp + "done"'
    )
    t.indent -= 1
    t.emit("}")
    t.emit("for _, r := range selectNode.Redirects {")
    t.indent += 1
    t.emit('result = result + " " + _FormatRedirect(r, false, false)')
    t.indent -= 1
    t.emit("}")
    t.emit("return result")
    t.indent -= 1
    # case "case"
    t.emit('case "case":')
    t.indent += 1
    t.emit("caseNode := node.(*Case)")
    t.emit("word := caseNode.Word.(*Word).Value")
    t.emit("patterns := []string{}")
    t.emit("for i, pn := range caseNode.Patterns {")
    t.indent += 1
    t.emit("p := pn.(*CasePattern)")
    t.emit('pat := strings.ReplaceAll(p.Pattern, "|", " | ")')
    t.emit("var body string")
    t.emit("if p.Body != nil {")
    t.indent += 1
    t.emit("body = _FormatCmdsubNode(p.Body, indent+8, false, false, false)")
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit('body = ""')
    t.indent -= 1
    t.emit("}")
    t.emit("term := p.Terminator")
    t.emit('patIndent := _RepeatStr(" ", indent+8)')
    t.emit('termIndent := _RepeatStr(" ", indent+4)')
    t.emit("var bodyPart string")
    t.emit('if body != "" {')
    t.indent += 1
    t.emit('bodyPart = patIndent + body + "\\n"')
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit('bodyPart = "\\n"')
    t.indent -= 1
    t.emit("}")
    t.emit("if i == 0 {")
    t.indent += 1
    t.emit('patterns = append(patterns, " "+pat+")\\n"+bodyPart+termIndent+term)')
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit('patterns = append(patterns, pat+")\\n"+bodyPart+termIndent+term)')
    t.indent -= 1
    t.emit("}")
    t.indent -= 1
    t.emit("}")
    t.emit('patternStr := strings.Join(patterns, "\\n"+_RepeatStr(" ", indent+4))')
    t.emit('redirects := ""')
    t.emit("if len(caseNode.Redirects) > 0 {")
    t.indent += 1
    t.emit("redirectParts := []string{}")
    t.emit("for _, r := range caseNode.Redirects {")
    t.indent += 1
    t.emit("redirectParts = append(redirectParts, _FormatRedirect(r, false, false))")
    t.indent -= 1
    t.emit("}")
    t.emit('redirects = " " + strings.Join(redirectParts, " ")')
    t.indent -= 1
    t.emit("}")
    t.emit('return "case " + word + " in" + patternStr + "\\n" + sp + "esac" + redirects')
    t.indent -= 1
    # case "function"
    t.emit('case "function":')
    t.indent += 1
    t.emit("funcNode := node.(*Function)")
    t.emit("name := funcNode.Name")
    t.emit("var innerBody Node")
    t.emit('if funcNode.Body.Kind() == "brace-group" {')
    t.indent += 1
    t.emit("bg := funcNode.Body.(*BraceGroup)")
    t.emit("innerBody = bg.Body")
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit("innerBody = funcNode.Body")
    t.indent -= 1
    t.emit("}")
    t.emit("body := _FormatCmdsubNode(innerBody, indent+4, false, false, false)")
    t.emit('body = strings.TrimSuffix(body, ";")')
    t.emit('return "function " + name + " () \\n{ \\n" + innerSp + body + "\\n}"')
    t.indent -= 1
    # case "subshell"
    t.emit('case "subshell":')
    t.indent += 1
    t.emit("subshell := node.(*Subshell)")
    t.emit(
        "body := _FormatCmdsubNode(subshell.Body, indent, inProcsub, compactRedirects, false)"
    )
    t.emit('redirects := ""')
    t.emit("if len(subshell.Redirects) > 0 {")
    t.indent += 1
    t.emit("redirectParts := []string{}")
    t.emit("for _, r := range subshell.Redirects {")
    t.indent += 1
    t.emit("redirectParts = append(redirectParts, _FormatRedirect(r, false, false))")
    t.indent -= 1
    t.emit("}")
    t.emit('redirects = strings.Join(redirectParts, " ")')
    t.indent -= 1
    t.emit("}")
    t.emit("if procsubFirst {")
    t.indent += 1
    t.emit('if redirects != "" {')
    t.indent += 1
    t.emit('return "(" + body + ") " + redirects')
    t.indent -= 1
    t.emit("}")
    t.emit('return "(" + body + ")"')
    t.indent -= 1
    t.emit("}")
    t.emit('if redirects != "" {')
    t.indent += 1
    t.emit('return "( " + body + " ) " + redirects')
    t.indent -= 1
    t.emit("}")
    t.emit('return "( " + body + " )"')
    t.indent -= 1
    # case "brace-group"
    t.emit('case "brace-group":')
    t.indent += 1
    t.emit("bg := node.(*BraceGroup)")
    t.emit("body := _FormatCmdsubNode(bg.Body, indent, false, false, false)")
    t.emit('body = strings.TrimSuffix(body, ";")')
    t.emit("var terminator string")
    t.emit('if strings.HasSuffix(body, " &") {')
    t.indent += 1
    t.emit('terminator = " }"')
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit('terminator = "; }"')
    t.indent -= 1
    t.emit("}")
    t.emit('redirects := ""')
    t.emit("if len(bg.Redirects) > 0 {")
    t.indent += 1
    t.emit("redirectParts := []string{}")
    t.emit("for _, r := range bg.Redirects {")
    t.indent += 1
    t.emit("redirectParts = append(redirectParts, _FormatRedirect(r, false, false))")
    t.indent -= 1
    t.emit("}")
    t.emit('redirects = strings.Join(redirectParts, " ")')
    t.indent -= 1
    t.emit("}")
    t.emit('if redirects != "" {')
    t.indent += 1
    t.emit('return "{ " + body + terminator + " " + redirects')
    t.indent -= 1
    t.emit("}")
    t.emit('return "{ " + body + terminator')
    t.indent -= 1
    # case "arith-cmd"
    t.emit('case "arith-cmd":')
    t.indent += 1
    t.emit("arith := node.(*ArithmeticCommand)")
    t.emit('return "((" + arith.Raw_content + "))"')
    t.indent -= 1
    # case "cond-expr"
    t.emit('case "cond-expr":')
    t.indent += 1
    t.emit("condExpr := node.(*ConditionalExpr)")
    t.emit("body := _FormatCondBody(condExpr.Body.(Node))")
    t.emit('return "[[ " + body + " ]]"')
    t.indent -= 1
    # case "negation"
    t.emit('case "negation":')
    t.indent += 1
    t.emit("neg := node.(*Negation)")
    t.emit("if neg.Pipeline != nil {")
    t.indent += 1
    t.emit('return "! " + _FormatCmdsubNode(neg.Pipeline, indent, false, false, false)')
    t.indent -= 1
    t.emit("}")
    t.emit('return "! "')
    t.indent -= 1
    # case "time"
    t.emit('case "time":')
    t.indent += 1
    t.emit("timeNode := node.(*Time)")
    t.emit("var prefix string")
    t.emit("if timeNode.Posix {")
    t.indent += 1
    t.emit('prefix = "time -p "')
    t.indent -= 1
    t.emit("} else {")
    t.indent += 1
    t.emit('prefix = "time "')
    t.indent -= 1
    t.emit("}")
    t.emit("if timeNode.Pipeline != nil {")
    t.indent += 1
    t.emit("return prefix + _FormatCmdsubNode(timeNode.Pipeline, indent, false, false, false)")
    t.indent -= 1
    t.emit("}")
    t.emit("return prefix")
    t.indent -= 1
    # default
    t.emit("}")
    t.emit('return ""')


# ========== Dictionary Mappings ==========


MANUAL_METHODS: dict[tuple[str, str], Callable[["GoTranspiler", str], None]] = {
    ("QuoteState", "push"): emit_quotestate_push,
    ("QuoteState", "pop"): emit_quotestate_pop,
    ("QuoteState", "copy"): emit_quotestate_copy,
    ("QuoteState", "outer_double"): emit_quotestate_outer_double,
    # Arithmetic parser - inline left_assoc pattern
    ("Parser", "_arith_parse_logical_or"): lambda t, r: emit_arith_left_assoc(
        t, r, ["||"], "_ArithParseLogicalAnd"
    ),
    ("Parser", "_arith_parse_logical_and"): lambda t, r: emit_arith_left_assoc(
        t, r, ["&&"], "_ArithParseBitwiseOr"
    ),
    ("Parser", "_arith_parse_equality"): lambda t, r: emit_arith_left_assoc(
        t, r, ["==", "!="], "_ArithParseComparison"
    ),
    # Heredoc gathering - minimal implementation (full heredocs not yet supported)
    ("Parser", "_gather_heredoc_bodies"): emit_gather_heredoc_bodies,
    # Heredoc parsing - needs type assertion for _pending_heredocs iteration
    ("Parser", "_parse_heredoc"): emit_parse_heredoc,
    # Process substitution - try/except pattern with recover
    ("Parser", "_parse_process_substitution"): emit_parse_process_substitution,
    # Backtick substitution - complex heredoc tracking in local vars
    ("Parser", "_parse_backtick_substitution"): emit_parse_backtick_substitution,
    # Command substitution - needs _isNilNode for typed nil check
    ("Parser", "_parse_command_substitution"): emit_parse_command_substitution,
    # Funsub (brace command substitution) - needs _isNilNode for typed nil check
    ("Parser", "_parse_funsub"): emit_parse_funsub,
}


MANUAL_FUNCTIONS: dict[str, Callable[["GoTranspiler"], None]] = {
    "_format_heredoc_body": emit_format_heredoc_body,
    "_starts_with_subshell": emit_starts_with_subshell,
    "_format_cond_body": emit_format_cond_body,
    "_format_redirect": emit_format_redirect,
    "_find_heredoc_content_end": emit_find_heredoc_content_end,
    "_format_cmdsub_node": emit_format_cmdsub_node,
}
