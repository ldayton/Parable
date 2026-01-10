"""AST node types for Parable."""


class Node:
    """Base class for all AST nodes."""

    kind: str

    def to_sexp(self) -> str:
        """Convert node to S-expression string for testing."""
        raise NotImplementedError


class Word(Node):
    """A word token, possibly containing expansions."""

    value: str
    parts: list[Node]

    def __init__(self, value: str, parts: list[Node] = None):
        self.kind = "word"
        self.value = value
        if parts is None:
            parts = []
        self.parts = parts

    def to_sexp(self) -> str:
        value = self.value
        # Expand ALL $'...' ANSI-C quotes (handles escapes and strips $)
        value = self._expand_all_ansi_c_quotes(value)
        # Strip $ from locale strings $"..." (quote-aware)
        value = self._strip_locale_string_dollars(value)
        # Normalize whitespace in array assignments: name=(a  b\tc) -> name=(a b c)
        value = self._normalize_array_whitespace(value)
        # Format command substitutions with oracle pretty-printing (before escaping)
        value = self._format_command_substitutions(value)
        # Strip line continuations (backslash-newline) from arithmetic expressions
        value = self._strip_arith_line_continuations(value)
        # Double CTLESC (0x01) bytes - bash oracle uses this for quoting control chars
        # Exception: don't double when preceded by odd number of backslashes (escaped)
        value = self._double_ctlesc_smart(value)
        # Prefix DEL (0x7f) with CTLESC - bash oracle quotes this control char
        value = value.replace("\x7f", "\x01\x7f")
        # Escape backslashes for s-expression output
        value = value.replace("\\", "\\\\")
        # Escape double quotes, newlines, and tabs
        escaped = value.replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
        return '(word "' + escaped + '")'

    def _append_with_ctlesc(self, result: bytearray, byte_val: int):
        """Append byte to result (CTLESC doubling happens later in to_sexp)."""
        result.append(byte_val)

    def _double_ctlesc_smart(self, value: str) -> str:
        """Double CTLESC bytes unless escaped by backslash inside double quotes."""
        result = []
        in_single = False
        in_double = False
        for c in value:
            # Track quote state
            if c == "'" and not in_double:
                in_single = not in_single
            elif c == '"' and not in_single:
                in_double = not in_double
            result.append(c)
            if c == "\x01":
                # Only count backslashes in double-quoted context (where they escape)
                # In single quotes, backslashes are literal, so always double CTLESC
                if in_double:
                    bs_count = 0
                    for j in range(len(result) - 2, -1, -1):
                        if result[j] == "\\":
                            bs_count += 1
                        else:
                            break
                    if bs_count % 2 == 0:
                        result.append("\x01")
                else:
                    # Outside double quotes (including single quotes): always double
                    result.append("\x01")
        return "".join(result)

    def _expand_ansi_c_escapes(self, value: str) -> str:
        """Expand ANSI-C escape sequences in $'...' strings.

        Uses bytes internally so \\x escapes can form valid UTF-8 sequences.
        Invalid UTF-8 is replaced with U+FFFD.
        """
        if not (value.startswith("'") and value.endswith("'")):
            return value
        inner = value[1 : len(value) - 1]
        result = bytearray()
        i = 0
        while i < len(inner):
            if inner[i] == "\\" and i + 1 < len(inner):
                c = inner[i + 1]
                if c == "a":
                    result.append(0x07)
                    i += 2
                elif c == "b":
                    result.append(0x08)
                    i += 2
                elif c in ("e", "E"):
                    result.append(0x1B)
                    i += 2
                elif c == "f":
                    result.append(0x0C)
                    i += 2
                elif c == "n":
                    result.append(0x0A)
                    i += 2
                elif c == "r":
                    result.append(0x0D)
                    i += 2
                elif c == "t":
                    result.append(0x09)
                    i += 2
                elif c == "v":
                    result.append(0x0B)
                    i += 2
                elif c == "\\":
                    result.append(0x5C)
                    i += 2
                elif c == "'":
                    # Oracle outputs \' as '\'' (shell quoting trick)
                    result.extend(b"'\\''")
                    i += 2
                elif c == '"':
                    result.append(0x22)
                    i += 2
                elif c == "?":
                    result.append(0x3F)
                    i += 2
                elif c == "x":
                    # Check for \x{...} brace syntax (bash 5.3+)
                    if i + 2 < len(inner) and inner[i + 2] == "{":
                        # Find closing brace or end of hex digits
                        j = i + 3
                        while j < len(inner) and inner[j] in "0123456789abcdefABCDEF":
                            j += 1
                        hex_str = inner[i + 3 : j]
                        if j < len(inner) and inner[j] == "}":
                            j += 1  # consume }
                        # If no hex digits, treat as NUL (truncates)
                        if not hex_str:
                            return "'" + result.decode("utf-8", errors="replace") + "'"
                        byte_val = int(hex_str, 16) & 0xFF  # Take low byte
                        if byte_val == 0:
                            return "'" + result.decode("utf-8", errors="replace") + "'"
                        self._append_with_ctlesc(result, byte_val)
                        i = j
                    else:
                        # Hex escape \xHH (1-2 hex digits) - raw byte
                        j = i + 2
                        while j < len(inner) and j < i + 4 and inner[j] in "0123456789abcdefABCDEF":
                            j += 1
                        if j > i + 2:
                            byte_val = int(inner[i + 2 : j], 16)
                            if byte_val == 0:
                                # NUL truncates string
                                return "'" + result.decode("utf-8", errors="replace") + "'"
                            self._append_with_ctlesc(result, byte_val)
                            i = j
                        else:
                            result.append(ord(inner[i]))
                            i += 1
                elif c == "u":
                    # Unicode escape \uHHHH (1-4 hex digits) - encode as UTF-8
                    j = i + 2
                    while j < len(inner) and j < i + 6 and inner[j] in "0123456789abcdefABCDEF":
                        j += 1
                    if j > i + 2:
                        codepoint = int(inner[i + 2 : j], 16)
                        if codepoint == 0:
                            # NUL truncates string
                            return "'" + result.decode("utf-8", errors="replace") + "'"
                        result.extend(chr(codepoint).encode("utf-8"))
                        i = j
                    else:
                        result.append(ord(inner[i]))
                        i += 1
                elif c == "U":
                    # Unicode escape \UHHHHHHHH (1-8 hex digits) - encode as UTF-8
                    j = i + 2
                    while j < len(inner) and j < i + 10 and inner[j] in "0123456789abcdefABCDEF":
                        j += 1
                    if j > i + 2:
                        codepoint = int(inner[i + 2 : j], 16)
                        if codepoint == 0:
                            # NUL truncates string
                            return "'" + result.decode("utf-8", errors="replace") + "'"
                        result.extend(chr(codepoint).encode("utf-8"))
                        i = j
                    else:
                        result.append(ord(inner[i]))
                        i += 1
                elif c == "c":
                    # Control character \cX - mask with 0x1f
                    if i + 3 <= len(inner):
                        ctrl_char = inner[i + 2]
                        ctrl_val = ord(ctrl_char) & 0x1F
                        if ctrl_val == 0:
                            # NUL truncates string
                            return "'" + result.decode("utf-8", errors="replace") + "'"
                        self._append_with_ctlesc(result, ctrl_val)
                        i += 3
                    else:
                        result.append(ord(inner[i]))
                        i += 1
                elif c == "0":
                    # Nul or octal \0 or \0NNN
                    j = i + 2
                    while j < len(inner) and j < i + 5 and inner[j] in "01234567":
                        j += 1
                    if j > i + 2:
                        byte_val = int(inner[i + 1 : j], 8)
                        if byte_val == 0:
                            # NUL truncates string
                            return "'" + result.decode("utf-8", errors="replace") + "'"
                        self._append_with_ctlesc(result, byte_val)
                        i = j
                    else:
                        # Just \0 - NUL truncates string
                        return "'" + result.decode("utf-8", errors="replace") + "'"
                elif c in "1234567":
                    # Octal escape \NNN (1-3 digits) - raw byte
                    j = i + 1
                    while j < len(inner) and j < i + 4 and inner[j] in "01234567":
                        j += 1
                    byte_val = int(inner[i + 1 : j], 8)
                    if byte_val == 0:
                        # NUL truncates string
                        return "'" + result.decode("utf-8", errors="replace") + "'"
                    self._append_with_ctlesc(result, byte_val)
                    i = j
                else:
                    # Unknown escape - preserve as-is
                    result.append(0x5C)
                    result.append(ord(c))
                    i += 2
            else:
                result.extend(inner[i].encode("utf-8"))
                i += 1
        # Decode as UTF-8, replacing invalid sequences with U+FFFD
        return "'" + result.decode("utf-8", errors="replace") + "'"

    def _expand_all_ansi_c_quotes(self, value: str) -> str:
        """Find and expand ALL $'...' ANSI-C quoted strings in value."""
        result = []
        i = 0
        in_single_quote = False
        in_double_quote = False
        brace_depth = 0  # Track ${...} nesting - inside braces, $'...' is expanded
        while i < len(value):
            ch = value[i]
            # Track brace depth for parameter expansions
            if not in_single_quote:
                if value[i : i + 2] == "${":
                    brace_depth += 1
                    result.append("${")
                    i += 2
                    continue
                elif ch == "}" and brace_depth > 0:
                    brace_depth -= 1
                    result.append(ch)
                    i += 1
                    continue
            # Inside ${...}, we can expand $'...' even if originally in double quotes
            effective_in_dquote = in_double_quote and brace_depth == 0
            # Track quote state to avoid matching $' inside regular quotes
            if ch == "'" and not effective_in_dquote:
                # Check if this is start of $'...' ANSI-C string
                if not in_single_quote and i > 0 and value[i - 1] == "$":
                    # This is handled below when we see $'
                    result.append(ch)
                    i += 1
                elif in_single_quote:
                    # End of single-quoted string
                    in_single_quote = False
                    result.append(ch)
                    i += 1
                else:
                    # Start of regular single-quoted string
                    in_single_quote = True
                    result.append(ch)
                    i += 1
            elif ch == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
                result.append(ch)
                i += 1
            elif ch == "\\" and i + 1 < len(value) and not in_single_quote:
                # Backslash escape - skip both chars to avoid misinterpreting \" or \'
                result.append(ch)
                result.append(value[i + 1])
                i += 2
            elif value[i : i + 2] == "$'" and not in_single_quote and not effective_in_dquote:
                # ANSI-C quoted string - find matching closing quote
                j = i + 2
                while j < len(value):
                    if value[j] == "\\" and j + 1 < len(value):
                        j += 2  # Skip escaped char
                    elif value[j] == "'":
                        j += 1  # Include closing quote
                        break
                    else:
                        j += 1
                # Extract and expand the $'...' sequence
                ansi_str = value[i:j]  # e.g. $'hello\nworld'
                # Strip the $ and expand escapes
                expanded = self._expand_ansi_c_escapes(
                    ansi_str[1 : len(ansi_str)]
                )  # Pass 'hello\nworld'
                # Inside ${...}, strip quotes for default/alternate value operators
                # but keep them for pattern replacement operators
                if brace_depth > 0 and expanded.startswith("'") and expanded.endswith("'"):
                    inner = expanded[1 : len(expanded) - 1]
                    # Only strip if non-empty, no CTLESC, and after a default value operator
                    if inner and "\x01" not in inner:
                        # Check what precedes - default value ops: :- := :+ :? - = + ?
                        prev = (
                            "".join(result[len(result) - 2 : len(result)])
                            if len(result) >= 2
                            else ""
                        )
                        if (
                            prev.endswith(":-")
                            or prev.endswith(":=")
                            or prev.endswith(":+")
                            or prev.endswith(":?")
                        ):
                            expanded = inner
                        elif len(result) >= 1:
                            last = result[len(result) - 1]
                            # Single char operators (not after :), but not /
                            if last in "-=+?" and (
                                len(result) < 2 or result[len(result) - 2] != ":"
                            ):
                                expanded = inner
                result.append(expanded)
                i = j
            else:
                result.append(ch)
                i += 1
        return "".join(result)

    def _strip_locale_string_dollars(self, value: str) -> str:
        """Strip $ from locale strings $"..." while tracking quote context."""
        result = []
        i = 0
        in_single_quote = False
        in_double_quote = False
        while i < len(value):
            ch = value[i]
            if ch == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
                result.append(ch)
                i += 1
            elif ch == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
                result.append(ch)
                i += 1
            elif ch == "\\" and i + 1 < len(value):
                # Escape - copy both chars
                result.append(ch)
                result.append(value[i + 1])
                i += 2
            elif value[i : i + 2] == '$"' and not in_single_quote and not in_double_quote:
                # Locale string $"..." outside quotes - strip the $ and enter double quote
                result.append('"')
                in_double_quote = True
                i += 2
            else:
                result.append(ch)
                i += 1
        return "".join(result)

    def _normalize_array_whitespace(self, value: str) -> str:
        """Normalize whitespace inside array assignments: arr=(a  b\tc) -> arr=(a b c)."""
        # Match array assignment pattern: name=( or name+=(
        if not value.endswith(")"):
            return value
        # Parse identifier: starts with letter/underscore, then alnum/underscore
        i = 0
        if not (i < len(value) and (value[i].isalpha() or value[i] == "_")):
            return value
        i += 1
        while i < len(value) and (value[i].isalnum() or value[i] == "_"):
            i += 1
        # Optional + for +=
        if i < len(value) and value[i] == "+":
            i += 1
        # Must have =(
        if not (i + 1 < len(value) and value[i] == "=" and value[i + 1] == "("):
            return value
        prefix = value[: i + 1]  # e.g., "arr=" or "arr+="
        # Extract content inside parentheses
        inner = value[len(prefix) + 1 : -1]
        # Normalize whitespace while respecting quotes
        normalized = []
        i = 0
        in_whitespace = True  # Start true to skip leading whitespace
        while i < len(inner):
            ch = inner[i]
            if ch in " \t\n":
                if not in_whitespace and normalized:
                    normalized.append(" ")
                    in_whitespace = True
                i += 1
            elif ch == "'":
                # Single-quoted string - preserve as-is
                in_whitespace = False
                j = i + 1
                while j < len(inner) and inner[j] != "'":
                    j += 1
                normalized.append(inner[i : j + 1])
                i = j + 1
            elif ch == '"':
                # Double-quoted string - preserve as-is
                in_whitespace = False
                j = i + 1
                while j < len(inner):
                    if inner[j] == "\\" and j + 1 < len(inner):
                        j += 2
                    elif inner[j] == '"':
                        break
                    else:
                        j += 1
                normalized.append(inner[i : j + 1])
                i = j + 1
            elif ch == "\\" and i + 1 < len(inner):
                # Escape sequence
                in_whitespace = False
                normalized.append(inner[i : i + 2])
                i += 2
            else:
                in_whitespace = False
                normalized.append(ch)
                i += 1
        # Strip trailing space
        result = "".join(normalized).rstrip(" ")
        return prefix + "(" + result + ")"

    def _strip_arith_line_continuations(self, value: str) -> str:
        """Strip backslash-newline (line continuation) from inside $((...))."""
        result = []
        i = 0
        while i < len(value):
            # Check for $(( arithmetic expression
            if value[i : i + 3] == "$((":
                # Find matching ))
                start = i
                i += 3
                depth = 1
                arith_content = []
                while i < len(value) and depth > 0:
                    if value[i : i + 2] == "((":
                        arith_content.append("((")
                        depth += 1
                        i += 2
                    elif value[i : i + 2] == "))":
                        depth -= 1
                        if depth > 0:
                            arith_content.append("))")
                        i += 2
                    elif value[i] == "\\" and i + 1 < len(value) and value[i + 1] == "\n":
                        # Skip backslash-newline (line continuation)
                        i += 2
                    else:
                        arith_content.append(value[i])
                        i += 1
                if depth == 0:
                    # Found proper )) closing - this is arithmetic
                    result.append("$((" + "".join(arith_content) + "))")
                else:
                    # Didn't find )) - not arithmetic (likely $( + ( subshell), pass through
                    result.append(value[start:i])
            else:
                result.append(value[i])
                i += 1
        return "".join(result)

    def _collect_cmdsubs(self, node) -> list:
        """Recursively collect CommandSubstitution nodes from an AST node."""
        result = []
        node_kind = getattr(node, "kind", None)
        if node_kind == "cmdsub":
            result.append(node)
        else:
            expr = getattr(node, "expression", None)
            if expr is not None:
                # ArithmeticExpansion, ArithBinaryOp, etc.
                result.extend(self._collect_cmdsubs(expr))
        left = getattr(node, "left", None)
        if left is not None:
            result.extend(self._collect_cmdsubs(left))
        right = getattr(node, "right", None)
        if right is not None:
            result.extend(self._collect_cmdsubs(right))
        operand = getattr(node, "operand", None)
        if operand is not None:
            result.extend(self._collect_cmdsubs(operand))
        condition = getattr(node, "condition", None)
        if condition is not None:
            result.extend(self._collect_cmdsubs(condition))
        true_value = getattr(node, "true_value", None)
        if true_value is not None:
            result.extend(self._collect_cmdsubs(true_value))
        false_value = getattr(node, "false_value", None)
        if false_value is not None:
            result.extend(self._collect_cmdsubs(false_value))
        return result

    def _format_command_substitutions(self, value: str) -> str:
        """Replace $(...) and >(...) / <(...) with oracle-formatted AST output."""
        # Collect command substitutions from all parts, including nested ones
        cmdsub_parts = []
        procsub_parts = []
        for p in self.parts:
            if p.kind == "cmdsub":
                cmdsub_parts.append(p)
            elif p.kind == "procsub":
                procsub_parts.append(p)
            else:
                cmdsub_parts.extend(self._collect_cmdsubs(p))
        # Check if we have ${ or ${| brace command substitutions to format
        has_brace_cmdsub = "${ " in value or "${|" in value
        if not cmdsub_parts and not procsub_parts and not has_brace_cmdsub:
            return value
        result = []
        i = 0
        cmdsub_idx = 0
        procsub_idx = 0
        while i < len(value):
            # Check for $( command substitution (but not $(( arithmetic)
            if (
                value[i : i + 2] == "$("
                and value[i : i + 3] != "$(("
                and cmdsub_idx < len(cmdsub_parts)
            ):
                # Find matching close paren using bash-aware matching
                j = _find_cmdsub_end(value, i + 2)
                # Format this command substitution
                node = cmdsub_parts[cmdsub_idx]
                formatted = _format_cmdsub_node(node.command)
                # Add space after $( if content starts with ( to avoid $((
                if formatted.startswith("("):
                    result.append("$( " + formatted + ")")
                else:
                    result.append("$(" + formatted + ")")
                cmdsub_idx += 1
                i = j
            # Check for backtick command substitution
            elif value[i] == "`" and cmdsub_idx < len(cmdsub_parts):
                # Find matching backtick
                j = i + 1
                while j < len(value):
                    if value[j] == "\\" and j + 1 < len(value):
                        j += 2
                        continue
                    if value[j] == "`":
                        j += 1
                        break
                    j += 1
                # Keep backtick substitutions as-is (oracle doesn't reformat them)
                result.append(value[i:j])
                cmdsub_idx += 1
                i = j
            # Check for >( or <( process substitution
            elif value[i : i + 2] in (">(", "<(") and procsub_idx < len(procsub_parts):
                direction = value[i]
                # Find matching close paren
                j = _find_cmdsub_end(value, i + 2)
                # Format this process substitution (with in_procsub=True for no-space subshells)
                node = procsub_parts[procsub_idx]
                formatted = _format_cmdsub_node(node.command, in_procsub=True)
                result.append(direction + "(" + formatted + ")")
                procsub_idx += 1
                i = j
            # Check for ${ (space) or ${| brace command substitution
            elif value[i : i + 3] == "${ " or value[i : i + 3] == "${|":
                prefix = value[i : i + 3]
                # Find matching close brace
                j = i + 3
                depth = 1
                while j < len(value) and depth > 0:
                    if value[j] == "{":
                        depth += 1
                    elif value[j] == "}":
                        depth -= 1
                    j += 1
                # Parse and format the inner content
                inner = value[i + 2 : j - 1]  # Content between ${ and }
                # Check if content is all whitespace - normalize to single space
                if inner.strip() == "":
                    result.append("${ }")
                else:
                    from .parser import Parser

                    try:
                        parser = Parser(inner.lstrip(" |"))
                        parsed = parser.parse_list()
                        if parsed:
                            formatted = _format_cmdsub_node(parsed)
                            result.append(prefix + formatted + "; }")
                        else:
                            result.append("${ }")
                    except Exception:
                        result.append(value[i:j])
                i = j
            else:
                result.append(value[i])
                i += 1
        return "".join(result)

    def get_cond_formatted_value(self) -> str:
        """Return value with command substitutions formatted for cond-term output."""
        # Expand ANSI-C quotes
        value = self._expand_all_ansi_c_quotes(self.value)
        # Format command substitutions
        value = self._format_command_substitutions(value)
        # Bash doubles CTLESC (\x01) characters in output
        value = value.replace("\x01", "\x01\x01")
        return value.rstrip("\n")


class Command(Node):
    """A simple command (words + redirections)."""

    words: list[Word]
    redirects: list[Node]

    def __init__(self, words: list[Word], redirects: list[Node] = None):
        self.kind = "command"
        self.words = words
        if redirects is None:
            redirects = []
        self.redirects = redirects

    def to_sexp(self) -> str:
        parts = []
        for w in self.words:
            parts.append(w.to_sexp())
        for r in self.redirects:
            parts.append(r.to_sexp())
        inner = " ".join(parts)
        if not inner:
            return "(command)"
        return "(command " + inner + ")"


class Pipeline(Node):
    """A pipeline of commands."""

    commands: list[Node]

    def __init__(self, commands: list[Node]):
        self.kind = "pipeline"
        self.commands = commands

    def to_sexp(self) -> str:
        if len(self.commands) == 1:
            return self.commands[0].to_sexp()
        # Build list of (cmd, needs_pipe_both_redirect) filtering out PipeBoth markers
        cmds = []
        i = 0
        while i < len(self.commands):
            cmd = self.commands[i]
            if cmd.kind == "pipe-both":
                i += 1
                continue
            # Check if next element is PipeBoth
            needs_redirect = i + 1 < len(self.commands) and self.commands[i + 1].kind == "pipe-both"
            cmds.append((cmd, needs_redirect))
            i += 1
        if len(cmds) == 1:
            pair = cmds[0]
            cmd = pair[0]
            needs = pair[1]
            return self._cmd_sexp(cmd, needs)
        # Nest right-associatively: (pipe a (pipe b c))
        last_pair = cmds[len(cmds) - 1]
        last_cmd = last_pair[0]
        last_needs = last_pair[1]
        result = self._cmd_sexp(last_cmd, last_needs)
        j = len(cmds) - 2
        while j >= 0:
            pair = cmds[j]
            cmd = pair[0]
            needs = pair[1]
            if needs and cmd.kind != "command":
                # Compound command: redirect as sibling in pipe
                result = "(pipe " + cmd.to_sexp() + ' (redirect ">&" 1) ' + result + ")"
            else:
                result = "(pipe " + self._cmd_sexp(cmd, needs) + " " + result + ")"
            j -= 1
        return result

    def _cmd_sexp(self, cmd: Node, needs_redirect: bool) -> str:
        """Get s-expression for a command, optionally injecting pipe-both redirect."""
        if not needs_redirect:
            return cmd.to_sexp()
        if cmd.kind == "command":
            # Inject redirect inside command
            parts = []
            for w in cmd.words:
                parts.append(w.to_sexp())
            for r in cmd.redirects:
                parts.append(r.to_sexp())
            parts.append('(redirect ">&" 1)')
            return "(command " + " ".join(parts) + ")"
        # Compound command handled by caller
        return cmd.to_sexp()


class List(Node):
    """A list of pipelines with operators."""

    parts: list[Node]  # alternating: pipeline, operator, pipeline, ...

    def __init__(self, parts: list[Node]):
        self.kind = "list"
        self.parts = parts

    def to_sexp(self) -> str:
        # parts = [cmd, op, cmd, op, cmd, ...]
        # Bash precedence: && and || bind tighter than ; and &
        parts = list(self.parts)
        op_names = {"&&": "and", "||": "or", ";": "semi", "\n": "semi", "&": "background"}
        # Strip trailing ; or \n (bash ignores it)
        while (
            len(parts) > 1
            and parts[len(parts) - 1].kind == "operator"
            and parts[len(parts) - 1].op in (";", "\n")
        ):
            parts = parts[0 : len(parts) - 1]
        if len(parts) == 1:
            return parts[0].to_sexp()
        # Handle trailing & as unary background operator
        # & only applies to the immediately preceding pipeline, not the whole list
        if parts[len(parts) - 1].kind == "operator" and parts[len(parts) - 1].op == "&":
            # Find rightmost ; or \n to split there
            for i in range(len(parts) - 3, 0, -2):
                if parts[i].kind == "operator" and parts[i].op in (";", "\n"):
                    left = parts[0:i]
                    right = parts[i + 1 : len(parts) - 1]  # exclude trailing &
                    left_sexp = List(left).to_sexp() if len(left) > 1 else left[0].to_sexp()
                    right_sexp = List(right).to_sexp() if len(right) > 1 else right[0].to_sexp()
                    return "(semi " + left_sexp + " (background " + right_sexp + "))"
            # No ; or \n found, background the whole list (minus trailing &)
            inner_parts = parts[0 : len(parts) - 1]
            if len(inner_parts) == 1:
                return "(background " + inner_parts[0].to_sexp() + ")"
            inner_list = List(inner_parts)
            return "(background " + inner_list.to_sexp() + ")"
        # Process by precedence: first split on ; and &, then on && and ||
        return self._to_sexp_with_precedence(parts, op_names)

    def _to_sexp_with_precedence(self, parts: list, op_names: dict) -> str:
        # Process operators by precedence: ; (lowest), then &, then && and ||
        # Split on ; or \n first (rightmost for left-associativity)
        for i in range(len(parts) - 2, 0, -2):
            if parts[i].kind == "operator" and parts[i].op in (";", "\n"):
                left = parts[:i]
                right = parts[i + 1 :]
                left_sexp = List(left).to_sexp() if len(left) > 1 else left[0].to_sexp()
                right_sexp = List(right).to_sexp() if len(right) > 1 else right[0].to_sexp()
                return "(semi " + left_sexp + " " + right_sexp + ")"
        # Then split on & (rightmost for left-associativity)
        for i in range(len(parts) - 2, 0, -2):
            if parts[i].kind == "operator" and parts[i].op == "&":
                left = parts[:i]
                right = parts[i + 1 :]
                left_sexp = List(left).to_sexp() if len(left) > 1 else left[0].to_sexp()
                right_sexp = List(right).to_sexp() if len(right) > 1 else right[0].to_sexp()
                return "(background " + left_sexp + " " + right_sexp + ")"
        # No ; or &, process high-prec ops (&&, ||) left-associatively
        result = parts[0].to_sexp()
        for i in range(1, len(parts) - 1, 2):
            op = parts[i]
            cmd = parts[i + 1]
            op_name = op_names.get(op.op, op.op)
            result = "(" + op_name + " " + result + " " + cmd.to_sexp() + ")"
        return result


class Operator(Node):
    """An operator token (&&, ||, ;, &, |)."""

    op: str

    def __init__(self, op: str):
        self.kind = "operator"
        self.op = op

    def to_sexp(self) -> str:
        names = {
            "&&": "and",
            "||": "or",
            ";": "semi",
            "&": "bg",
            "|": "pipe",
        }
        return "(" + names.get(self.op, self.op) + ")"


class PipeBoth(Node):
    """Marker for |& pipe (stdout + stderr)."""

    def __init__(self):
        self.kind = "pipe-both"

    def to_sexp(self) -> str:
        return "(pipe-both)"


class Empty(Node):
    """Empty input."""

    def __init__(self):
        self.kind = "empty"

    def to_sexp(self) -> str:
        return ""


class Comment(Node):
    """A comment (# to end of line)."""

    text: str

    def __init__(self, text: str):
        self.kind = "comment"
        self.text = text

    def to_sexp(self) -> str:
        # Oracle doesn't output comments
        return ""


class Redirect(Node):
    """A redirection."""

    op: str
    target: Word
    fd: int | None = None

    def __init__(self, op: str, target: Word, fd: int = None):
        self.kind = "redirect"
        self.op = op
        self.target = target
        self.fd = fd

    def to_sexp(self) -> str:
        # Strip fd prefix from operator (e.g., "2>" -> ">", "{fd}>" -> ">")
        op = self.op.lstrip("0123456789")
        # Strip {varname} prefix if present
        if op.startswith("{"):
            j = 1
            if j < len(op) and (op[j].isalpha() or op[j] == "_"):
                j += 1
                while j < len(op) and (op[j].isalnum() or op[j] == "_"):
                    j += 1
                if j < len(op) and op[j] == "}":
                    op = op[j + 1 :]
        target_val = self.target.value
        # Expand ANSI-C $'...' quotes (converts escapes like \n to actual newline)
        target_val = Word(target_val)._expand_all_ansi_c_quotes(target_val)
        # Strip $ from locale strings $"..."
        target_val = target_val.replace('$"', '"')
        # For fd duplication, target starts with & (e.g., "&1", "&2", "&-")
        if target_val.startswith("&"):
            # Determine the real operator
            if op == ">":
                op = ">&"
            elif op == "<":
                op = "<&"
            fd_target = target_val[1 : len(target_val)].rstrip("-")  # "&1" -> "1", "&1-" -> "1"
            if fd_target.isdigit():
                return '(redirect "' + op + '" ' + fd_target + ")"
            elif target_val == "&-":
                return '(redirect ">&-" 0)'
            else:
                # Variable fd dup like >&$fd or >&$fd- (move) - strip the & and trailing -
                return '(redirect "' + op + '" "' + fd_target + '")'
        # Handle case where op is already >& or <&
        if op in (">&", "<&"):
            if target_val.isdigit():
                return '(redirect "' + op + '" ' + target_val + ")"
            # Variable fd dup with move indicator (trailing -)
            target_val = target_val.rstrip("-")
            return '(redirect "' + op + '" "' + target_val + '")'
        return '(redirect "' + op + '" "' + target_val + '")'


class HereDoc(Node):
    """A here document <<DELIM ... DELIM."""

    delimiter: str
    content: str
    strip_tabs: bool = False
    quoted: bool = False
    fd: int | None = None

    def __init__(
        self,
        delimiter: str,
        content: str,
        strip_tabs: bool = False,
        quoted: bool = False,
        fd: int = None,
    ):
        self.kind = "heredoc"
        self.delimiter = delimiter
        self.content = content
        self.strip_tabs = strip_tabs
        self.quoted = quoted
        self.fd = fd

    def to_sexp(self) -> str:
        op = "<<-" if self.strip_tabs else "<<"
        return '(redirect "' + op + '" "' + self.content + '")'


class Subshell(Node):
    """A subshell ( list )."""

    body: Node
    redirects: list["Redirect | HereDoc"] | None = None

    def __init__(self, body: Node, redirects: list["Redirect | HereDoc"] | None = None):
        self.kind = "subshell"
        self.body = body
        self.redirects = redirects

    def to_sexp(self) -> str:
        base = "(subshell " + self.body.to_sexp() + ")"
        if self.redirects:
            redirect_parts = []
            for r in self.redirects:
                redirect_parts.append(r.to_sexp())
            return base + " " + " ".join(redirect_parts)
        return base


class BraceGroup(Node):
    """A brace group { list; }."""

    body: Node
    redirects: list["Redirect | HereDoc"] | None = None

    def __init__(self, body: Node, redirects: list["Redirect | HereDoc"] | None = None):
        self.kind = "brace-group"
        self.body = body
        self.redirects = redirects

    def to_sexp(self) -> str:
        base = "(brace-group " + self.body.to_sexp() + ")"
        if self.redirects:
            redirect_parts = []
            for r in self.redirects:
                redirect_parts.append(r.to_sexp())
            return base + " " + " ".join(redirect_parts)
        return base


class If(Node):
    """An if statement."""

    condition: Node
    then_body: Node
    else_body: Node | None = None
    redirects: list[Node]

    def __init__(
        self, condition: Node, then_body: Node, else_body: Node = None, redirects: list[Node] = None
    ):
        self.kind = "if"
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body
        if redirects is None:
            redirects = []
        self.redirects = redirects

    def to_sexp(self) -> str:
        result = "(if " + self.condition.to_sexp() + " " + self.then_body.to_sexp()
        if self.else_body:
            result = result + " " + self.else_body.to_sexp()
        result = result + ")"
        for r in self.redirects:
            result = result + " " + r.to_sexp()
        return result


class While(Node):
    """A while loop."""

    condition: Node
    body: Node
    redirects: list[Node]

    def __init__(self, condition: Node, body: Node, redirects: list[Node] = None):
        self.kind = "while"
        self.condition = condition
        self.body = body
        if redirects is None:
            redirects = []
        self.redirects = redirects

    def to_sexp(self) -> str:
        base = "(while " + self.condition.to_sexp() + " " + self.body.to_sexp() + ")"
        if self.redirects:
            redirect_parts = []
            for r in self.redirects:
                redirect_parts.append(r.to_sexp())
            return base + " " + " ".join(redirect_parts)
        return base


class Until(Node):
    """An until loop."""

    condition: Node
    body: Node
    redirects: list[Node]

    def __init__(self, condition: Node, body: Node, redirects: list[Node] = None):
        self.kind = "until"
        self.condition = condition
        self.body = body
        if redirects is None:
            redirects = []
        self.redirects = redirects

    def to_sexp(self) -> str:
        base = "(until " + self.condition.to_sexp() + " " + self.body.to_sexp() + ")"
        if self.redirects:
            redirect_parts = []
            for r in self.redirects:
                redirect_parts.append(r.to_sexp())
            return base + " " + " ".join(redirect_parts)
        return base


class For(Node):
    """A for loop."""

    var: str
    words: list[Word] | None
    body: Node
    redirects: list[Node]

    def __init__(
        self, var: str, words: list[Word] | None, body: Node, redirects: list[Node] = None
    ):
        self.kind = "for"
        self.var = var
        self.words = words
        self.body = body
        if redirects is None:
            redirects = []
        self.redirects = redirects

    def to_sexp(self) -> str:
        # Oracle format: (for (word "var") (in (word "a") ...) body)
        suffix = ""
        if self.redirects:
            redirect_parts = []
            for r in self.redirects:
                redirect_parts.append(r.to_sexp())
            suffix = " " + " ".join(redirect_parts)
        var_escaped = self.var.replace("\\", "\\\\").replace('"', '\\"')
        if self.words is None:
            # No 'in' clause - oracle implies (in (word "\"$@\""))
            return (
                '(for (word "'
                + var_escaped
                + '") (in (word "\\"$@\\"")) '
                + self.body.to_sexp()
                + ")"
                + suffix
            )
        elif len(self.words) == 0:
            # Empty 'in' clause - oracle outputs (in)
            return '(for (word "' + var_escaped + '") (in) ' + self.body.to_sexp() + ")" + suffix
        else:
            word_parts = []
            for w in self.words:
                word_parts.append(w.to_sexp())
            word_strs = " ".join(word_parts)
            return (
                '(for (word "'
                + var_escaped
                + '") (in '
                + word_strs
                + ") "
                + self.body.to_sexp()
                + ")"
                + suffix
            )


class ForArith(Node):
    """A C-style for loop: for ((init; cond; incr)); do ... done."""

    init: str
    cond: str
    incr: str
    body: Node
    redirects: list[Node]

    def __init__(self, init: str, cond: str, incr: str, body: Node, redirects: list[Node] = None):
        self.kind = "for-arith"
        self.init = init
        self.cond = cond
        self.incr = incr
        self.body = body
        if redirects is None:
            redirects = []
        self.redirects = redirects

    def to_sexp(self) -> str:
        # Oracle format: (arith-for (init (word "x")) (test (word "y")) (step (word "z")) body)
        def format_arith_val(s: str) -> str:
            # Use Word's methods to expand ANSI-C quotes and strip locale $
            w = Word(s, [])
            val = w._expand_all_ansi_c_quotes(s)
            val = w._strip_locale_string_dollars(val)
            val = val.replace("\\", "\\\\").replace('"', '\\"')
            return val

        suffix = ""
        if self.redirects:
            redirect_parts = []
            for r in self.redirects:
                redirect_parts.append(r.to_sexp())
            suffix = " " + " ".join(redirect_parts)
        init_val = self.init if self.init else "1"
        cond_val = _normalize_fd_redirects(self.cond) if self.cond else "1"
        incr_val = self.incr if self.incr else "1"
        return (
            '(arith-for (init (word "'
            + format_arith_val(init_val)
            + '")) '
            + '(test (word "'
            + format_arith_val(cond_val)
            + '")) '
            + '(step (word "'
            + format_arith_val(incr_val)
            + '")) '
            + self.body.to_sexp()
            + ")"
            + suffix
        )


class Select(Node):
    """A select statement."""

    var: str
    words: list[Word] | None
    body: Node
    redirects: list[Node]

    def __init__(
        self, var: str, words: list[Word] | None, body: Node, redirects: list[Node] = None
    ):
        self.kind = "select"
        self.var = var
        self.words = words
        self.body = body
        if redirects is None:
            redirects = []
        self.redirects = redirects

    def to_sexp(self) -> str:
        # Oracle format: (select (word "var") (in (word "a") ...) body)
        suffix = ""
        if self.redirects:
            redirect_parts = []
            for r in self.redirects:
                redirect_parts.append(r.to_sexp())
            suffix = " " + " ".join(redirect_parts)
        var_escaped = self.var.replace("\\", "\\\\").replace('"', '\\"')
        if self.words is not None:
            word_parts = []
            for w in self.words:
                word_parts.append(w.to_sexp())
            word_strs = " ".join(word_parts)
            if self.words:
                in_clause = "(in " + word_strs + ")"
            else:
                in_clause = "(in)"
        else:
            # No 'in' clause means implicit "$@"
            in_clause = '(in (word "\\"$@\\""))'
        return (
            '(select (word "'
            + var_escaped
            + '") '
            + in_clause
            + " "
            + self.body.to_sexp()
            + ")"
            + suffix
        )


class Case(Node):
    """A case statement."""

    word: Word
    patterns: list["CasePattern"]
    redirects: list[Node]

    def __init__(self, word: Word, patterns: list["CasePattern"], redirects: list[Node] = None):
        self.kind = "case"
        self.word = word
        self.patterns = patterns
        if redirects is None:
            redirects = []
        self.redirects = redirects

    def to_sexp(self) -> str:
        parts = []
        parts.append("(case " + self.word.to_sexp())
        for p in self.patterns:
            parts.append(p.to_sexp())
        base = " ".join(parts) + ")"
        if self.redirects:
            redirect_parts = []
            for r in self.redirects:
                redirect_parts.append(r.to_sexp())
            return base + " " + " ".join(redirect_parts)
        return base


class CasePattern(Node):
    """A pattern clause in a case statement."""

    pattern: str
    body: Node | None
    terminator: str = ";;"  # ";;", ";&", or ";;&"

    def __init__(self, pattern: str, body: Node | None, terminator: str = ";;"):
        self.kind = "pattern"
        self.pattern = pattern
        self.body = body
        self.terminator = terminator

    def to_sexp(self) -> str:
        # Oracle format: (pattern ((word "a") (word "b")) body)
        # Split pattern by | respecting escapes, extglobs, quotes, and brackets
        alternatives = []
        current = []
        i = 0
        depth = 0  # Track extglob/paren depth
        while i < len(self.pattern):
            ch = self.pattern[i]
            if ch == "\\" and i + 1 < len(self.pattern):
                current.append(self.pattern[i : i + 2])
                i += 2
            elif ch in "@?*+!" and i + 1 < len(self.pattern) and self.pattern[i + 1] == "(":
                # Start of extglob: @(, ?(, *(, +(, !(
                current.append(ch)
                current.append("(")
                depth += 1
                i += 2
            elif ch == "$" and i + 1 < len(self.pattern) and self.pattern[i + 1] == "(":
                # $( command sub or $(( arithmetic - track depth
                current.append(ch)
                current.append("(")
                depth += 1
                i += 2
            elif ch == "(" and depth > 0:
                current.append(ch)
                depth += 1
                i += 1
            elif ch == ")" and depth > 0:
                current.append(ch)
                depth -= 1
                i += 1
            elif ch == "[":
                # Character class - but only if there's a matching ]
                # First scan to check if ] exists before ) at same depth
                scan_pos = i + 1
                # Skip [! or [^ at start
                if scan_pos < len(self.pattern) and self.pattern[scan_pos] in "!^":
                    scan_pos += 1
                # Handle ] as first char - it's literal only if there's more content
                # [] is a complete (empty) bracket, but []] has literal ] then closing ]
                if scan_pos < len(self.pattern) and self.pattern[scan_pos] == "]":
                    # Check if there's another ] after this one (making first ] literal)
                    # but only within this pattern (stop at | or ) at depth 0)
                    has_another_close = False
                    for check_pos in range(scan_pos + 1, len(self.pattern)):
                        if self.pattern[check_pos] == "]":
                            has_another_close = True
                            break
                        if self.pattern[check_pos] in "|)" and depth == 0:
                            break
                    if has_another_close:
                        scan_pos += 1  # Skip first ] as literal
                is_char_class = False
                while scan_pos < len(self.pattern):
                    sc = self.pattern[scan_pos]
                    if sc == "]":
                        is_char_class = True
                        break
                    elif sc == ")" and depth == 0:
                        # Hit pattern closer before ]
                        break
                    scan_pos += 1
                if not is_char_class:
                    # No matching ], treat [ as literal
                    current.append(ch)
                    i += 1
                else:
                    # Valid character class - consume until ]
                    current.append(ch)
                    i += 1
                    # Handle [! or [^ at start
                    if i < len(self.pattern) and self.pattern[i] in "!^":
                        current.append(self.pattern[i])
                        i += 1
                    # Handle ] as first char - only literal if there's another ]
                    # within this pattern (before | at depth 0)
                    if i < len(self.pattern) and self.pattern[i] == "]":
                        # Check if there's another ] to close (making this one literal)
                        has_another = False
                        for check_pos in range(i + 1, len(self.pattern)):
                            if self.pattern[check_pos] == "]":
                                has_another = True
                                break
                            if self.pattern[check_pos] in "|)" and depth == 0:
                                break
                        if has_another:
                            current.append(self.pattern[i])
                            i += 1
                    # Consume until closing ]
                    while i < len(self.pattern) and self.pattern[i] != "]":
                        current.append(self.pattern[i])
                        i += 1
                    if i < len(self.pattern):
                        current.append(self.pattern[i])  # ]
                        i += 1
            elif ch == "'" and depth == 0:
                # Single-quoted string - consume until closing '
                current.append(ch)
                i += 1
                while i < len(self.pattern) and self.pattern[i] != "'":
                    current.append(self.pattern[i])
                    i += 1
                if i < len(self.pattern):
                    current.append(self.pattern[i])  # '
                    i += 1
            elif ch == '"' and depth == 0:
                # Double-quoted string - consume until closing "
                current.append(ch)
                i += 1
                while i < len(self.pattern) and self.pattern[i] != '"':
                    if self.pattern[i] == "\\" and i + 1 < len(self.pattern):
                        current.append(self.pattern[i])
                        i += 1
                    current.append(self.pattern[i])
                    i += 1
                if i < len(self.pattern):
                    current.append(self.pattern[i])  # "
                    i += 1
            elif ch == "|" and depth == 0:
                alternatives.append("".join(current))
                current = []
                i += 1
            else:
                current.append(ch)
                i += 1
        alternatives.append("".join(current))
        word_list = []
        for alt in alternatives:
            # Use Word.to_sexp() to properly expand ANSI-C quotes and escape
            word_list.append(Word(alt).to_sexp())
        pattern_str = " ".join(word_list)
        parts = ["(pattern (" + pattern_str + ")"]
        if self.body:
            parts.append(" " + self.body.to_sexp())
        else:
            parts.append(" ()")
        # Oracle doesn't output fallthrough/falltest markers
        parts.append(")")
        return "".join(parts)


class Function(Node):
    """A function definition."""

    name: str
    body: Node

    def __init__(self, name: str, body: Node):
        self.kind = "function"
        self.name = name
        self.body = body

    def to_sexp(self) -> str:
        return '(function "' + self.name + '" ' + self.body.to_sexp() + ")"


class ParamExpansion(Node):
    """A parameter expansion ${var} or ${var:-default}."""

    param: str
    op: str | None = None
    arg: str | None = None

    def __init__(self, param: str, op: str = None, arg: str = None):
        self.kind = "param"
        self.param = param
        self.op = op
        self.arg = arg

    def to_sexp(self) -> str:
        escaped_param = self.param.replace("\\", "\\\\").replace('"', '\\"')
        if self.op is not None:
            escaped_op = self.op.replace("\\", "\\\\").replace('"', '\\"')
            arg_val = self.arg if self.arg is not None else ""
            escaped_arg = arg_val.replace("\\", "\\\\").replace('"', '\\"')
            return '(param "' + escaped_param + '" "' + escaped_op + '" "' + escaped_arg + '")'
        return '(param "' + escaped_param + '")'


class ParamLength(Node):
    """A parameter length expansion ${#var}."""

    param: str

    def __init__(self, param: str):
        self.kind = "param-len"
        self.param = param

    def to_sexp(self) -> str:
        escaped = self.param.replace("\\", "\\\\").replace('"', '\\"')
        return '(param-len "' + escaped + '")'


class ParamIndirect(Node):
    """An indirect parameter expansion ${!var} or ${!var<op><arg>}."""

    param: str
    op: str | None
    arg: str | None

    def __init__(self, param: str, op: str | None = None, arg: str | None = None):
        self.kind = "param-indirect"
        self.param = param
        self.op = op
        self.arg = arg

    def to_sexp(self) -> str:
        escaped = self.param.replace("\\", "\\\\").replace('"', '\\"')
        if self.op is not None:
            escaped_op = self.op.replace("\\", "\\\\").replace('"', '\\"')
            arg_val = self.arg if self.arg is not None else ""
            escaped_arg = arg_val.replace("\\", "\\\\").replace('"', '\\"')
            return '(param-indirect "' + escaped + '" "' + escaped_op + '" "' + escaped_arg + '")'
        return '(param-indirect "' + escaped + '")'


class CommandSubstitution(Node):
    """A command substitution $(...) or `...`."""

    command: Node

    def __init__(self, command: Node):
        self.kind = "cmdsub"
        self.command = command

    def to_sexp(self) -> str:
        return "(cmdsub " + self.command.to_sexp() + ")"


class ArithmeticExpansion(Node):
    """An arithmetic expansion $((...)) with parsed internals."""

    expression: "Node | None"  # Parsed arithmetic expression, or None for empty

    def __init__(self, expression: "Node | None"):
        self.kind = "arith"
        self.expression = expression

    def to_sexp(self) -> str:
        if self.expression is None:
            return "(arith)"
        return "(arith " + self.expression.to_sexp() + ")"


class ArithmeticCommand(Node):
    """An arithmetic command ((...)) with parsed internals."""

    expression: "Node | None"  # Parsed arithmetic expression, or None for empty
    redirects: list[Node]
    raw_content: str  # Raw expression text for oracle-compatible output

    def __init__(
        self, expression: "Node | None", redirects: list[Node] = None, raw_content: str = ""
    ):
        self.kind = "arith-cmd"
        self.expression = expression
        if redirects is None:
            redirects = []
        self.redirects = redirects
        self.raw_content = raw_content

    def to_sexp(self) -> str:
        # Oracle format: (arith (word "content"))
        # Redirects are siblings: (arith (word "...")) (redirect ...)
        escaped = self.raw_content.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        result = '(arith (word "' + escaped + '"))'
        if self.redirects:
            redirect_parts = []
            for r in self.redirects:
                redirect_parts.append(r.to_sexp())
            redirect_sexps = " ".join(redirect_parts)
            return result + " " + redirect_sexps
        return result


# Arithmetic expression nodes


class ArithNumber(Node):
    """A numeric literal in arithmetic context."""

    value: str  # Raw string (may be hex, octal, base#n)

    def __init__(self, value: str):
        self.kind = "number"
        self.value = value

    def to_sexp(self) -> str:
        return '(number "' + self.value + '")'


class ArithVar(Node):
    """A variable reference in arithmetic context (without $)."""

    name: str

    def __init__(self, name: str):
        self.kind = "var"
        self.name = name

    def to_sexp(self) -> str:
        return '(var "' + self.name + '")'


class ArithBinaryOp(Node):
    """A binary operation in arithmetic."""

    op: str
    left: Node
    right: Node

    def __init__(self, op: str, left: Node, right: Node):
        self.kind = "binary-op"
        self.op = op
        self.left = left
        self.right = right

    def to_sexp(self) -> str:
        return (
            '(binary-op "' + self.op + '" ' + self.left.to_sexp() + " " + self.right.to_sexp() + ")"
        )


class ArithUnaryOp(Node):
    """A unary operation in arithmetic."""

    op: str
    operand: Node

    def __init__(self, op: str, operand: Node):
        self.kind = "unary-op"
        self.op = op
        self.operand = operand

    def to_sexp(self) -> str:
        return '(unary-op "' + self.op + '" ' + self.operand.to_sexp() + ")"


class ArithPreIncr(Node):
    """Pre-increment ++var."""

    operand: Node

    def __init__(self, operand: Node):
        self.kind = "pre-incr"
        self.operand = operand

    def to_sexp(self) -> str:
        return "(pre-incr " + self.operand.to_sexp() + ")"


class ArithPostIncr(Node):
    """Post-increment var++."""

    operand: Node

    def __init__(self, operand: Node):
        self.kind = "post-incr"
        self.operand = operand

    def to_sexp(self) -> str:
        return "(post-incr " + self.operand.to_sexp() + ")"


class ArithPreDecr(Node):
    """Pre-decrement --var."""

    operand: Node

    def __init__(self, operand: Node):
        self.kind = "pre-decr"
        self.operand = operand

    def to_sexp(self) -> str:
        return "(pre-decr " + self.operand.to_sexp() + ")"


class ArithPostDecr(Node):
    """Post-decrement var--."""

    operand: Node

    def __init__(self, operand: Node):
        self.kind = "post-decr"
        self.operand = operand

    def to_sexp(self) -> str:
        return "(post-decr " + self.operand.to_sexp() + ")"


class ArithAssign(Node):
    """Assignment operation (=, +=, -=, etc.)."""

    op: str
    target: Node
    value: Node

    def __init__(self, op: str, target: Node, value: Node):
        self.kind = "assign"
        self.op = op
        self.target = target
        self.value = value

    def to_sexp(self) -> str:
        return (
            '(assign "' + self.op + '" ' + self.target.to_sexp() + " " + self.value.to_sexp() + ")"
        )


class ArithTernary(Node):
    """Ternary conditional expr ? expr : expr."""

    condition: Node
    if_true: Node
    if_false: Node

    def __init__(self, condition: Node, if_true: Node, if_false: Node):
        self.kind = "ternary"
        self.condition = condition
        self.if_true = if_true
        self.if_false = if_false

    def to_sexp(self) -> str:
        return (
            "(ternary "
            + self.condition.to_sexp()
            + " "
            + self.if_true.to_sexp()
            + " "
            + self.if_false.to_sexp()
            + ")"
        )


class ArithComma(Node):
    """Comma operator expr, expr."""

    left: Node
    right: Node

    def __init__(self, left: Node, right: Node):
        self.kind = "comma"
        self.left = left
        self.right = right

    def to_sexp(self) -> str:
        return "(comma " + self.left.to_sexp() + " " + self.right.to_sexp() + ")"


class ArithSubscript(Node):
    """Array subscript arr[expr]."""

    array: str
    index: Node

    def __init__(self, array: str, index: Node):
        self.kind = "subscript"
        self.array = array
        self.index = index

    def to_sexp(self) -> str:
        return '(subscript "' + self.array + '" ' + self.index.to_sexp() + ")"


class ArithEscape(Node):
    """An escaped character in arithmetic expression."""

    char: str

    def __init__(self, char: str):
        self.kind = "escape"
        self.char = char

    def to_sexp(self) -> str:
        return '(escape "' + self.char + '")'


class ArithDeprecated(Node):
    """A deprecated arithmetic expansion $[expr]."""

    expression: str

    def __init__(self, expression: str):
        self.kind = "arith-deprecated"
        self.expression = expression

    def to_sexp(self) -> str:
        escaped = self.expression.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return '(arith-deprecated "' + escaped + '")'


class AnsiCQuote(Node):
    """An ANSI-C quoted string $'...'."""

    content: str

    def __init__(self, content: str):
        self.kind = "ansi-c"
        self.content = content

    def to_sexp(self) -> str:
        escaped = self.content.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return '(ansi-c "' + escaped + '")'


class LocaleString(Node):
    """A locale-translated string $"..."."""

    content: str

    def __init__(self, content: str):
        self.kind = "locale"
        self.content = content

    def to_sexp(self) -> str:
        escaped = self.content.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return '(locale "' + escaped + '")'


class ProcessSubstitution(Node):
    """A process substitution <(...) or >(...)."""

    direction: str  # "<" for input, ">" for output
    command: Node

    def __init__(self, direction: str, command: Node):
        self.kind = "procsub"
        self.direction = direction
        self.command = command

    def to_sexp(self) -> str:
        return '(procsub "' + self.direction + '" ' + self.command.to_sexp() + ")"


class Negation(Node):
    """Pipeline negation with !."""

    pipeline: Node

    def __init__(self, pipeline: Node):
        self.kind = "negation"
        self.pipeline = pipeline

    def to_sexp(self) -> str:
        if self.pipeline is None:
            # Bare "!" with no command - oracle shows empty command
            return "(negation (command))"
        return "(negation " + self.pipeline.to_sexp() + ")"


class Time(Node):
    """Time measurement with time keyword."""

    pipeline: Node
    posix: bool = False  # -p flag

    def __init__(self, pipeline: Node, posix: bool = False):
        self.kind = "time"
        self.pipeline = pipeline
        self.posix = posix

    def to_sexp(self) -> str:
        if self.pipeline is None:
            # Bare "time" with no command - oracle shows empty command
            return "(time -p (command))" if self.posix else "(time (command))"
        if self.posix:
            return "(time -p " + self.pipeline.to_sexp() + ")"
        return "(time " + self.pipeline.to_sexp() + ")"


class ConditionalExpr(Node):
    """A conditional expression [[ expression ]]."""

    body: "Node | str"  # Parsed node or raw string for backwards compat
    redirects: list[Node]

    def __init__(self, body: "Node | str", redirects: list[Node] = None):
        self.kind = "cond-expr"
        self.body = body
        if redirects is None:
            redirects = []
        self.redirects = redirects

    def to_sexp(self) -> str:
        # Oracle format: (cond ...) not (cond-expr ...)
        # Redirects are siblings, not children: (cond ...) (redirect ...)
        body_kind = getattr(self.body, "kind", None)
        if body_kind is None:
            # body is a string
            escaped = self.body.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
            result = '(cond "' + escaped + '")'
        else:
            result = "(cond " + self.body.to_sexp() + ")"
        if self.redirects:
            redirect_parts = []
            for r in self.redirects:
                redirect_parts.append(r.to_sexp())
            redirect_sexps = " ".join(redirect_parts)
            return result + " " + redirect_sexps
        return result


class UnaryTest(Node):
    """A unary test in [[ ]], e.g., -f file, -z string."""

    op: str
    operand: Word

    def __init__(self, op: str, operand: Word):
        self.kind = "unary-test"
        self.op = op
        self.operand = operand

    def to_sexp(self) -> str:
        # Oracle format: (cond-unary "-f" (cond-term "file"))
        # cond-term preserves content as-is (no backslash escaping)
        return '(cond-unary "' + self.op + '" (cond-term "' + self.operand.value + '"))'


class BinaryTest(Node):
    """A binary test in [[ ]], e.g., $a == $b, file1 -nt file2."""

    op: str
    left: Word
    right: Word

    def __init__(self, op: str, left: Word, right: Word):
        self.kind = "binary-test"
        self.op = op
        self.left = left
        self.right = right

    def to_sexp(self) -> str:
        # Oracle format: (cond-binary "==" (cond-term "x") (cond-term "y"))
        # cond-term preserves content as-is (no backslash escaping)
        left_val = self.left.get_cond_formatted_value()
        right_val = self.right.get_cond_formatted_value()
        return (
            '(cond-binary "'
            + self.op
            + '" (cond-term "'
            + left_val
            + '") (cond-term "'
            + right_val
            + '"))'
        )


class CondAnd(Node):
    """Logical AND in [[ ]], e.g., expr1 && expr2."""

    left: Node
    right: Node

    def __init__(self, left: Node, right: Node):
        self.kind = "cond-and"
        self.left = left
        self.right = right

    def to_sexp(self) -> str:
        return "(cond-and " + self.left.to_sexp() + " " + self.right.to_sexp() + ")"


class CondOr(Node):
    """Logical OR in [[ ]], e.g., expr1 || expr2."""

    left: Node
    right: Node

    def __init__(self, left: Node, right: Node):
        self.kind = "cond-or"
        self.left = left
        self.right = right

    def to_sexp(self) -> str:
        return "(cond-or " + self.left.to_sexp() + " " + self.right.to_sexp() + ")"


class CondNot(Node):
    """Logical NOT in [[ ]], e.g., ! expr."""

    operand: Node

    def __init__(self, operand: Node):
        self.kind = "cond-not"
        self.operand = operand

    def to_sexp(self) -> str:
        # Oracle ignores negation - just output the operand
        return self.operand.to_sexp()


class CondParen(Node):
    """Parenthesized group in [[ ]], e.g., ( expr )."""

    inner: Node

    def __init__(self, inner: Node):
        self.kind = "cond-paren"
        self.inner = inner

    def to_sexp(self) -> str:
        return "(cond-expr " + self.inner.to_sexp() + ")"


class Array(Node):
    """An array literal (word1 word2 ...)."""

    elements: list[Word]

    def __init__(self, elements: list[Word]):
        self.kind = "array"
        self.elements = elements

    def to_sexp(self) -> str:
        if not self.elements:
            return "(array)"
        parts = []
        for e in self.elements:
            parts.append(e.to_sexp())
        inner = " ".join(parts)
        return "(array " + inner + ")"


class Coproc(Node):
    """A coprocess coproc [NAME] command."""

    command: Node
    name: str | None = None

    def __init__(self, command: Node, name: str = None):
        self.kind = "coproc"
        self.command = command
        self.name = name

    def to_sexp(self) -> str:
        # Use provided name for compound commands, "COPROC" for simple commands
        name = self.name if self.name else "COPROC"
        return '(coproc "' + name + '" ' + self.command.to_sexp() + ")"


def _format_cmdsub_node(node: Node, indent: int = 0, in_procsub: bool = False) -> str:
    """Format an AST node for command substitution output (oracle pretty-print format)."""
    sp = " " * indent
    inner_sp = " " * (indent + 4)
    if node.kind == "empty":
        return ""
    if node.kind == "command":
        parts = []
        for w in node.words:
            val = w._expand_all_ansi_c_quotes(w.value)
            val = w._format_command_substitutions(val)
            parts.append(val)
        for r in node.redirects:
            parts.append(_format_redirect(r))
        return " ".join(parts)
    if node.kind == "pipeline":
        cmd_parts = []
        for cmd in node.commands:
            cmd_parts.append(_format_cmdsub_node(cmd, indent))
        return " | ".join(cmd_parts)
    if node.kind == "list":
        # Join commands with operators
        result = []
        for p in node.parts:
            if p.kind == "operator":
                if p.op == ";":
                    result.append(";")
                elif p.op == "\n":
                    # Skip newline if it follows a semicolon (redundant separator)
                    if result and result[len(result) - 1] == ";":
                        continue
                    result.append("\n")
                elif p.op == "&":
                    result.append(" &")
                else:
                    result.append(" " + p.op)
            else:
                if result and not result[len(result) - 1].endswith((" ", "\n")):
                    result.append(" ")
                result.append(_format_cmdsub_node(p, indent))
        # Strip trailing ; or newline
        s = "".join(result)
        while s.endswith(";") or s.endswith("\n"):
            s = s[0 : len(s) - 1]
        return s
    if node.kind == "if":
        cond = _format_cmdsub_node(node.condition, indent)
        then_body = _format_cmdsub_node(node.then_body, indent + 4)
        result = "if " + cond + "; then\n" + inner_sp + then_body + ";"
        if node.else_body:
            else_body = _format_cmdsub_node(node.else_body, indent + 4)
            result = result + "\n" + sp + "else\n" + inner_sp + else_body + ";"
        result = result + "\n" + sp + "fi"
        return result
    if node.kind == "while":
        cond = _format_cmdsub_node(node.condition, indent)
        body = _format_cmdsub_node(node.body, indent + 4)
        return "while " + cond + "; do\n" + inner_sp + body + ";\n" + sp + "done"
    if node.kind == "until":
        cond = _format_cmdsub_node(node.condition, indent)
        body = _format_cmdsub_node(node.body, indent + 4)
        return "until " + cond + "; do\n" + inner_sp + body + ";\n" + sp + "done"
    if node.kind == "for":
        var = node.var
        body = _format_cmdsub_node(node.body, indent + 4)
        if node.words:
            word_vals = []
            for w in node.words:
                word_vals.append(w.value)
            words = " ".join(word_vals)
            return "for " + var + " in " + words + ";\ndo\n" + inner_sp + body + ";\n" + sp + "done"
        return "for " + var + ";\ndo\n" + inner_sp + body + ";\n" + sp + "done"
    if node.kind == "case":
        word = node.word.value
        patterns = []
        i = 0
        while i < len(node.patterns):
            p = node.patterns[i]
            pat = p.pattern.replace("|", " | ")
            body = _format_cmdsub_node(p.body, indent + 8) if p.body else ""
            term = p.terminator  # ;;, ;&, or ;;&
            pat_indent = " " * (indent + 8)
            term_indent = " " * (indent + 4)
            if i == 0:
                # First pattern on same line as 'in'
                patterns.append(" " + pat + ")\n" + pat_indent + body + "\n" + term_indent + term)
            else:
                patterns.append(pat + ")\n" + pat_indent + body + "\n" + term_indent + term)
            i += 1
        pattern_str = ("\n" + " " * (indent + 4)).join(patterns)
        return "case " + word + " in" + pattern_str + "\n" + sp + "esac"
    if node.kind == "function":
        name = node.name
        # Get the body content - if it's a BraceGroup, unwrap it
        if node.body.kind == "brace-group":
            body = _format_cmdsub_node(node.body.body, indent + 4)
        else:
            body = _format_cmdsub_node(node.body, indent + 4)
        body = body.rstrip(";")  # Strip trailing semicolons
        return "function " + name + " () \n{ \n" + inner_sp + body + "\n}"
    if node.kind == "subshell":
        body = _format_cmdsub_node(node.body, indent, in_procsub)
        redirects = ""
        if node.redirects:
            redirect_parts = []
            for r in node.redirects:
                redirect_parts.append(_format_redirect(r))
            redirects = " ".join(redirect_parts)
        if in_procsub:
            if redirects:
                return "(" + body + ") " + redirects
            return "(" + body + ")"
        if redirects:
            return "( " + body + " ) " + redirects
        return "( " + body + " )"
    if node.kind == "brace-group":
        body = _format_cmdsub_node(node.body, indent)
        body = body.rstrip(";")  # Strip trailing semicolons before adding our own
        return "{ " + body + "; }"
    if node.kind == "arith-cmd":
        return "((" + node.raw_content + "))"
    # Fallback: return empty for unknown types
    return ""


def _format_redirect(r: "Redirect | HereDoc") -> str:
    """Format a redirect for command substitution output."""
    if r.kind == "heredoc":
        # Include heredoc content: <<DELIM\ncontent\nDELIM\n
        op = "<<-" if r.strip_tabs else "<<"
        delim = "'" + r.delimiter + "'" if r.quoted else r.delimiter
        return op + delim + "\n" + r.content + r.delimiter + "\n"
    op = r.op
    target = r.target.value
    # For fd duplication (target starts with &), handle normalization
    if target.startswith("&"):
        # Normalize N<&- to N>&- (close always uses >)
        if target == "&-" and op.endswith("<"):
            op = op[0 : len(op) - 1] + ">"
        # Add default fd for bare >&N or <&N
        if op == ">":
            op = "1>"
        elif op == "<":
            op = "0<"
        return op + target
    return op + " " + target


def _normalize_fd_redirects(s: str) -> str:
    """Normalize fd redirects in a raw string: >&2 -> 1>&2, <&N -> 0<&N."""
    # Match >&N or <&N not preceded by a digit, add default fd
    result = []
    i = 0
    while i < len(s):
        # Check for >&N or <&N
        if i + 2 < len(s) and s[i + 1] == "&" and s[i + 2].isdigit():
            prev_is_digit = i > 0 and s[i - 1].isdigit()
            if s[i] == ">" and not prev_is_digit:
                result.append("1>&")
                result.append(s[i + 2])
                i += 3
                continue
            elif s[i] == "<" and not prev_is_digit:
                result.append("0<&")
                result.append(s[i + 2])
                i += 3
                continue
        result.append(s[i])
        i += 1
    return "".join(result)


def _find_cmdsub_end(value: str, start: int) -> int:
    """Find the end of a $(...) command substitution, handling case statements.

    Starts after the opening $(. Returns position after the closing ).
    """
    depth = 1
    i = start
    in_single = False
    in_double = False
    case_depth = 0  # Track nested case statements
    in_case_patterns = False  # After 'in' but before first ;; or esac
    while i < len(value) and depth > 0:
        c = value[i]
        # Handle escapes
        if c == "\\" and i + 1 < len(value) and not in_single:
            i += 2
            continue
        # Handle quotes
        if c == "'" and not in_double:
            in_single = not in_single
            i += 1
            continue
        if c == '"' and not in_single:
            in_double = not in_double
            i += 1
            continue
        if in_single:
            i += 1
            continue
        if in_double:
            # Inside double quotes, $() command substitution is still active
            if value[i : i + 2] == "$(" and value[i : i + 3] != "$((":
                # Recursively find end of nested command substitution
                j = _find_cmdsub_end(value, i + 2)
                i = j
                continue
            # Skip other characters inside double quotes
            i += 1
            continue
        # Handle comments - skip from # to end of line
        # Only treat # as comment if preceded by whitespace or at start
        if c == "#" and (i == start or value[i - 1] in " \t\n;|&()"):
            while i < len(value) and value[i] != "\n":
                i += 1
            continue
        # Handle heredocs
        if value[i : i + 2] == "<<":
            i = _skip_heredoc(value, i)
            continue
        # Check for 'case' keyword
        if value[i : i + 4] == "case" and _is_word_boundary(value, i, 4):
            case_depth += 1
            in_case_patterns = False
            i += 4
            continue
        # Check for 'in' keyword (after case)
        if case_depth > 0 and value[i : i + 2] == "in" and _is_word_boundary(value, i, 2):
            in_case_patterns = True
            i += 2
            continue
        # Check for 'esac' keyword
        if value[i : i + 4] == "esac" and _is_word_boundary(value, i, 4):
            if case_depth > 0:
                case_depth -= 1
                in_case_patterns = False
            i += 4
            continue
        # Check for ';;' (end of case pattern, next pattern or esac follows)
        if value[i : i + 2] == ";;":
            i += 2
            continue
        # Handle parens
        if c == "(":
            depth += 1
        elif c == ")":
            # In case patterns, ) after pattern name is not a grouping paren
            if in_case_patterns and case_depth > 0:
                # This ) is a case pattern terminator, skip it
                pass
            else:
                depth -= 1
        i += 1
    return i


def _skip_heredoc(value: str, start: int) -> int:
    """Skip past a heredoc starting at <<. Returns position after heredoc content."""
    i = start + 2  # Skip <<
    # Handle <<- (strip tabs)
    if i < len(value) and value[i] == "-":
        i += 1
    # Skip whitespace before delimiter
    while i < len(value) and value[i] in " \t":
        i += 1
    # Extract delimiter - may be quoted
    delim_start = i
    quote_char = None
    if i < len(value) and value[i] in "\"'":
        quote_char = value[i]
        i += 1
        delim_start = i
        while i < len(value) and value[i] != quote_char:
            i += 1
        delimiter = value[delim_start:i]
        if i < len(value):
            i += 1  # Skip closing quote
    elif i < len(value) and value[i] == "\\":
        # Backslash-quoted delimiter like <<\EOF
        i += 1
        delim_start = i
        while i < len(value) and value[i] not in " \t\n":
            i += 1
        delimiter = value[delim_start:i]
    else:
        # Unquoted delimiter
        while i < len(value) and value[i] not in " \t\n":
            i += 1
        delimiter = value[delim_start:i]
    # Skip to end of line (heredoc content starts on next line)
    while i < len(value) and value[i] != "\n":
        i += 1
    if i < len(value):
        i += 1  # Skip newline
    # Find the end delimiter on its own line
    while i < len(value):
        line_start = i
        # Find end of this line
        line_end = i
        while line_end < len(value) and value[line_end] != "\n":
            line_end += 1
        line = value[line_start:line_end]
        # Check if this line is the delimiter (possibly with leading tabs for <<-)
        stripped = line.lstrip("\t") if start + 2 < len(value) and value[start + 2] == "-" else line
        if stripped == delimiter:
            # Found end - return position after delimiter line
            return line_end + 1 if line_end < len(value) else line_end
        i = line_end + 1 if line_end < len(value) else line_end
    return i


def _is_word_boundary(s: str, pos: int, word_len: int) -> bool:
    """Check if the word at pos is a standalone word (not part of larger word)."""
    # Check character before
    if pos > 0 and s[pos - 1].isalnum():
        return False
    # Check character after
    end = pos + word_len
    if end < len(s) and s[end].isalnum():
        return False
    return True
