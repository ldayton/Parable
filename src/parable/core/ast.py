"""AST node types for Parable."""

from dataclasses import dataclass, field


@dataclass
class Node:
    """Base class for all AST nodes."""

    kind: str

    def to_sexp(self) -> str:
        """Convert node to S-expression string for testing."""
        raise NotImplementedError


@dataclass
class Word(Node):
    """A word token, possibly containing expansions."""

    value: str
    parts: list[Node] = field(default_factory=list)

    def __init__(self, value: str, parts: list[Node] = None):
        self.kind = "word"
        self.value = value
        self.parts = parts or []

    def to_sexp(self) -> str:
        import re
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
        value = value.replace("\x01", "\x01\x01")
        # Prefix DEL (0x7f) with CTLESC - bash oracle quotes this control char
        value = value.replace("\x7f", "\x01\x7f")
        # Escape backslashes for s-expression output
        value = value.replace("\\", "\\\\")
        # Escape double quotes, newlines, and tabs
        escaped = value.replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
        return f'(word "{escaped}")'

    def _append_with_ctlesc(self, result: bytearray, byte_val: int):
        """Append byte to result (CTLESC doubling happens later in to_sexp)."""
        result.append(byte_val)

    def _expand_ansi_c_escapes(self, value: str) -> str:
        """Expand ANSI-C escape sequences in $'...' strings.

        Uses bytes internally so \\x escapes can form valid UTF-8 sequences.
        Invalid UTF-8 is replaced with U+FFFD.
        """
        if not (value.startswith("'") and value.endswith("'")):
            return value
        inner = value[1:-1]
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
                expanded = self._expand_ansi_c_escapes(ansi_str[1:])  # Pass 'hello\nworld'
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
        import re
        # Match array assignment pattern: name=( or name+=(
        match = re.match(r'^([a-zA-Z_][a-zA-Z_0-9]*\+?=)\(', value)
        if not match or not value.endswith(')'):
            return value
        prefix = match.group(1)  # e.g., "arr=" or "arr+="
        # Extract content inside parentheses
        inner = value[len(prefix) + 1 : -1]
        # Normalize whitespace while respecting quotes
        normalized = []
        i = 0
        in_whitespace = True  # Start true to skip leading whitespace
        while i < len(inner):
            ch = inner[i]
            if ch in ' \t\n':
                if not in_whitespace and normalized:
                    normalized.append(' ')
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
                    if inner[j] == '\\' and j + 1 < len(inner):
                        j += 2
                    elif inner[j] == '"':
                        break
                    else:
                        j += 1
                normalized.append(inner[i : j + 1])
                i = j + 1
            elif ch == '\\' and i + 1 < len(inner):
                # Escape sequence
                in_whitespace = False
                normalized.append(inner[i : i + 2])
                i += 2
            else:
                in_whitespace = False
                normalized.append(ch)
                i += 1
        # Strip trailing space
        result = ''.join(normalized).rstrip(' ')
        return f"{prefix}({result})"

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
        if isinstance(node, CommandSubstitution):
            result.append(node)
        elif hasattr(node, "expression") and node.expression is not None:
            # ArithmeticExpansion, ArithBinaryOp, etc.
            result.extend(self._collect_cmdsubs(node.expression))
        if hasattr(node, "left"):
            result.extend(self._collect_cmdsubs(node.left))
        if hasattr(node, "right"):
            result.extend(self._collect_cmdsubs(node.right))
        if hasattr(node, "operand"):
            result.extend(self._collect_cmdsubs(node.operand))
        if hasattr(node, "condition"):
            result.extend(self._collect_cmdsubs(node.condition))
        if hasattr(node, "true_value"):
            result.extend(self._collect_cmdsubs(node.true_value))
        if hasattr(node, "false_value"):
            result.extend(self._collect_cmdsubs(node.false_value))
        return result

    def _format_command_substitutions(self, value: str) -> str:
        """Replace $(...) and >(...) / <(...) with oracle-formatted AST output."""
        # Collect command substitutions from all parts, including nested ones
        cmdsub_parts = []
        procsub_parts = []
        for p in self.parts:
            if isinstance(p, CommandSubstitution):
                cmdsub_parts.append(p)
            elif isinstance(p, ProcessSubstitution):
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
            if value[i : i + 2] == "$(" and value[i : i + 3] != "$((" and cmdsub_idx < len(cmdsub_parts):
                # Find matching close paren using bash-aware matching
                j = _find_cmdsub_end(value, i + 2)
                # Format this command substitution
                node = cmdsub_parts[cmdsub_idx]
                formatted = _format_cmdsub_node(node.command)
                # Add space after $( if content starts with ( to avoid $((
                if formatted.startswith("("):
                    result.append(f"$( {formatted})")
                else:
                    result.append(f"$({formatted})")
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
                result.append(f"{direction}({formatted})")
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
                from parable.core.parser import Parser
                try:
                    parser = Parser(inner.lstrip(" |"))
                    parsed = parser.parse_list()
                    if parsed:
                        formatted = _format_cmdsub_node(parsed)
                        result.append(f"{prefix}{formatted}; }}")
                    else:
                        result.append(value[i:j])
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


@dataclass
class Command(Node):
    """A simple command (words + redirections)."""

    words: list[Word]
    redirects: list[Node] = field(default_factory=list)

    def __init__(self, words: list[Word], redirects: list[Node] = None):
        self.kind = "command"
        self.words = words
        self.redirects = redirects or []

    def to_sexp(self) -> str:
        parts = [w.to_sexp() for w in self.words]
        parts.extend(r.to_sexp() for r in self.redirects)
        inner = " ".join(parts)
        return "(command)" if not inner else f"(command {inner})"


@dataclass
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
        for i, cmd in enumerate(self.commands):
            if isinstance(cmd, PipeBoth):
                continue
            # Check if next element is PipeBoth
            needs_redirect = (i + 1 < len(self.commands) and isinstance(self.commands[i + 1], PipeBoth))
            cmds.append((cmd, needs_redirect))
        if len(cmds) == 1:
            cmd, needs = cmds[0]
            return self._cmd_sexp(cmd, needs)
        # Nest right-associatively: (pipe a (pipe b c))
        last_cmd, last_needs = cmds[-1]
        result = self._cmd_sexp(last_cmd, last_needs)
        for cmd, needs in reversed(cmds[:-1]):
            if needs and not isinstance(cmd, Command):
                # Compound command: redirect as sibling in pipe
                result = f'(pipe {cmd.to_sexp()} (redirect ">&" 1) {result})'
            else:
                result = f"(pipe {self._cmd_sexp(cmd, needs)} {result})"
        return result

    def _cmd_sexp(self, cmd: Node, needs_redirect: bool) -> str:
        """Get s-expression for a command, optionally injecting pipe-both redirect."""
        if not needs_redirect:
            return cmd.to_sexp()
        if isinstance(cmd, Command):
            # Inject redirect inside command
            parts = [w.to_sexp() for w in cmd.words]
            parts.extend(r.to_sexp() for r in cmd.redirects)
            parts.append('(redirect ">&" 1)')
            return f"(command {' '.join(parts)})"
        # Compound command handled by caller
        return cmd.to_sexp()


@dataclass
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
        while len(parts) > 1 and isinstance(parts[-1], Operator) and parts[-1].op in (";", "\n"):
            parts = parts[:-1]
        if len(parts) == 1:
            return parts[0].to_sexp()
        # Handle trailing & as unary background operator
        # & only applies to the immediately preceding pipeline, not the whole list
        if isinstance(parts[-1], Operator) and parts[-1].op == "&":
            # Find rightmost ; or \n to split there
            for i in range(len(parts) - 3, 0, -2):
                if isinstance(parts[i], Operator) and parts[i].op in (";", "\n"):
                    left = parts[:i]
                    right = parts[i + 1 : -1]  # exclude trailing &
                    left_sexp = List(left).to_sexp() if len(left) > 1 else left[0].to_sexp()
                    right_sexp = (
                        List(right).to_sexp() if len(right) > 1 else right[0].to_sexp()
                    )
                    return f"(semi {left_sexp} (background {right_sexp}))"
            # No ; or \n found, background the whole list (minus trailing &)
            inner_parts = parts[:-1]
            if len(inner_parts) == 1:
                return f"(background {inner_parts[0].to_sexp()})"
            inner_list = List(inner_parts)
            return f"(background {inner_list.to_sexp()})"
        # Process by precedence: first split on ; and &, then on && and ||
        return self._to_sexp_with_precedence(parts, op_names)

    def _to_sexp_with_precedence(self, parts: list, op_names: dict) -> str:
        # Process operators by precedence: ; (lowest), then &, then && and ||
        # Split on ; or \n first (rightmost for left-associativity)
        for i in range(len(parts) - 2, 0, -2):
            if isinstance(parts[i], Operator) and parts[i].op in (";", "\n"):
                left = parts[:i]
                right = parts[i + 1 :]
                left_sexp = List(left).to_sexp() if len(left) > 1 else left[0].to_sexp()
                right_sexp = List(right).to_sexp() if len(right) > 1 else right[0].to_sexp()
                return f"(semi {left_sexp} {right_sexp})"
        # Then split on & (rightmost for left-associativity)
        for i in range(len(parts) - 2, 0, -2):
            if isinstance(parts[i], Operator) and parts[i].op == "&":
                left = parts[:i]
                right = parts[i + 1 :]
                left_sexp = List(left).to_sexp() if len(left) > 1 else left[0].to_sexp()
                right_sexp = List(right).to_sexp() if len(right) > 1 else right[0].to_sexp()
                return f"(background {left_sexp} {right_sexp})"
        # No ; or &, process high-prec ops (&&, ||) left-associatively
        result = parts[0].to_sexp()
        for i in range(1, len(parts) - 1, 2):
            op = parts[i]
            cmd = parts[i + 1]
            op_name = op_names.get(op.op, op.op)
            result = f"({op_name} {result} {cmd.to_sexp()})"
        return result


@dataclass
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
        return f"({names.get(self.op, self.op)})"


@dataclass
class PipeBoth(Node):
    """Marker for |& pipe (stdout + stderr)."""

    def __init__(self):
        self.kind = "pipe-both"

    def to_sexp(self) -> str:
        return "(pipe-both)"


@dataclass
class Empty(Node):
    """Empty input."""

    def __init__(self):
        self.kind = "empty"

    def to_sexp(self) -> str:
        return ""


@dataclass
class Comment(Node):
    """A comment (# to end of line)."""

    text: str

    def __init__(self, text: str):
        self.kind = "comment"
        self.text = text

    def to_sexp(self) -> str:
        # Oracle doesn't output comments
        return ""


@dataclass
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
        import re
        # Strip fd prefix from operator (e.g., "2>" -> ">", "{fd}>" -> ">")
        op = self.op.lstrip("0123456789")
        op = re.sub(r"^\{[a-zA-Z_][a-zA-Z_0-9]*\}", "", op)
        target_val = self.target.value
        # Expand ANSI-C $'...' quotes (converts escapes like \n to actual newline)
        target_val = Word(target_val)._expand_all_ansi_c_quotes(target_val)
        # Strip $ from locale strings $"..."
        target_val = re.sub(r'\$"', '"', target_val)
        # For fd duplication, target starts with & (e.g., "&1", "&2", "&-")
        if target_val.startswith("&"):
            # Determine the real operator
            if op == ">":
                op = ">&"
            elif op == "<":
                op = "<&"
            fd_target = target_val[1:].rstrip("-")  # "&1" -> "1", "&1-" -> "1"
            if fd_target.isdigit():
                return f'(redirect "{op}" {fd_target})'
            elif target_val == "&-":
                return f'(redirect ">&-" 0)'
            else:
                # Variable fd dup like >&$fd or >&$fd- (move) - strip the & and trailing -
                return f'(redirect "{op}" "{fd_target}")'
        # Handle case where op is already >& or <&
        if op in (">&", "<&"):
            if target_val.isdigit():
                return f'(redirect "{op}" {target_val})'
            # Variable fd dup with move indicator (trailing -)
            target_val = target_val.rstrip("-")
            return f'(redirect "{op}" "{target_val}")'
        return f'(redirect "{op}" "{target_val}")'


@dataclass
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
        return f'(redirect "{op}" "{self.content}")'


@dataclass
class Subshell(Node):
    """A subshell ( list )."""

    body: Node
    redirects: list["Redirect | HereDoc"] | None = None

    def __init__(self, body: Node, redirects: list["Redirect | HereDoc"] | None = None):
        self.kind = "subshell"
        self.body = body
        self.redirects = redirects

    def to_sexp(self) -> str:
        base = f"(subshell {self.body.to_sexp()})"
        if self.redirects:
            return base + " " + " ".join(r.to_sexp() for r in self.redirects)
        return base


@dataclass
class BraceGroup(Node):
    """A brace group { list; }."""

    body: Node
    redirects: list["Redirect | HereDoc"] | None = None

    def __init__(self, body: Node, redirects: list["Redirect | HereDoc"] | None = None):
        self.kind = "brace-group"
        self.body = body
        self.redirects = redirects

    def to_sexp(self) -> str:
        base = f"(brace-group {self.body.to_sexp()})"
        if self.redirects:
            return base + " " + " ".join(r.to_sexp() for r in self.redirects)
        return base


@dataclass
class If(Node):
    """An if statement."""

    condition: Node
    then_body: Node
    else_body: Node | None = None
    redirects: list[Node] = field(default_factory=list)

    def __init__(
        self, condition: Node, then_body: Node, else_body: Node = None, redirects: list[Node] = None
    ):
        self.kind = "if"
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body
        self.redirects = redirects or []

    def to_sexp(self) -> str:
        result = f"(if {self.condition.to_sexp()} {self.then_body.to_sexp()}"
        if self.else_body:
            result += f" {self.else_body.to_sexp()}"
        result += ")"
        for r in self.redirects:
            result += f" {r.to_sexp()}"
        return result


@dataclass
class While(Node):
    """A while loop."""

    condition: Node
    body: Node
    redirects: list[Node] = field(default_factory=list)

    def __init__(self, condition: Node, body: Node, redirects: list[Node] = None):
        self.kind = "while"
        self.condition = condition
        self.body = body
        self.redirects = redirects or []

    def to_sexp(self) -> str:
        base = f"(while {self.condition.to_sexp()} {self.body.to_sexp()})"
        if self.redirects:
            return base + " " + " ".join(r.to_sexp() for r in self.redirects)
        return base


@dataclass
class Until(Node):
    """An until loop."""

    condition: Node
    body: Node
    redirects: list[Node] = field(default_factory=list)

    def __init__(self, condition: Node, body: Node, redirects: list[Node] = None):
        self.kind = "until"
        self.condition = condition
        self.body = body
        self.redirects = redirects or []

    def to_sexp(self) -> str:
        base = f"(until {self.condition.to_sexp()} {self.body.to_sexp()})"
        if self.redirects:
            return base + " " + " ".join(r.to_sexp() for r in self.redirects)
        return base


@dataclass
class For(Node):
    """A for loop."""

    var: str
    words: list[Word] | None
    body: Node
    redirects: list[Node] = field(default_factory=list)

    def __init__(
        self, var: str, words: list[Word] | None, body: Node, redirects: list[Node] = None
    ):
        self.kind = "for"
        self.var = var
        self.words = words
        self.body = body
        self.redirects = redirects or []

    def to_sexp(self) -> str:
        # Oracle format: (for (word "var") (in (word "a") ...) body)
        suffix = " " + " ".join(r.to_sexp() for r in self.redirects) if self.redirects else ""
        var_escaped = self.var.replace("\\", "\\\\").replace('"', '\\"')
        if self.words is None:
            # No 'in' clause - oracle implies (in (word "\"$@\""))
            return f'(for (word "{var_escaped}") (in (word "\\"$@\\"")) {self.body.to_sexp()}){suffix}'
        elif len(self.words) == 0:
            # Empty 'in' clause - oracle outputs (in)
            return f'(for (word "{var_escaped}") (in) {self.body.to_sexp()}){suffix}'
        else:
            word_strs = " ".join(w.to_sexp() for w in self.words)
            return f'(for (word "{var_escaped}") (in {word_strs}) {self.body.to_sexp()}){suffix}'


@dataclass
class ForArith(Node):
    """A C-style for loop: for ((init; cond; incr)); do ... done."""

    init: str
    cond: str
    incr: str
    body: Node
    redirects: list[Node] = field(default_factory=list)

    def __init__(self, init: str, cond: str, incr: str, body: Node, redirects: list[Node] = None):
        self.kind = "for-arith"
        self.init = init
        self.cond = cond
        self.incr = incr
        self.body = body
        self.redirects = redirects or []

    def to_sexp(self) -> str:
        # Oracle format: (arith-for (init (word "x")) (test (word "y")) (step (word "z")) body)
        def format_arith_val(s: str) -> str:
            # Use Word's methods to expand ANSI-C quotes and strip locale $
            w = Word(s, [])
            val = w._expand_all_ansi_c_quotes(s)
            val = w._strip_locale_string_dollars(val)
            val = val.replace("\\", "\\\\").replace('"', '\\"')
            return val
        suffix = " " + " ".join(r.to_sexp() for r in self.redirects) if self.redirects else ""
        init_val = self.init if self.init else "1"
        cond_val = _normalize_fd_redirects(self.cond) if self.cond else "1"
        incr_val = self.incr if self.incr else "1"
        return (
            f'(arith-for (init (word "{format_arith_val(init_val)}")) '
            f'(test (word "{format_arith_val(cond_val)}")) '
            f'(step (word "{format_arith_val(incr_val)}")) {self.body.to_sexp()}){suffix}'
        )


@dataclass
class Select(Node):
    """A select statement."""

    var: str
    words: list[Word] | None
    body: Node
    redirects: list[Node] = field(default_factory=list)

    def __init__(
        self, var: str, words: list[Word] | None, body: Node, redirects: list[Node] = None
    ):
        self.kind = "select"
        self.var = var
        self.words = words
        self.body = body
        self.redirects = redirects or []

    def to_sexp(self) -> str:
        # Oracle format: (select (word "var") (in (word "a") ...) body)
        suffix = " " + " ".join(r.to_sexp() for r in self.redirects) if self.redirects else ""
        var_escaped = self.var.replace("\\", "\\\\").replace('"', '\\"')
        if self.words is not None:
            word_strs = " ".join(w.to_sexp() for w in self.words)
            in_clause = f"(in {word_strs})" if self.words else "(in)"
        else:
            # No 'in' clause means implicit "$@"
            in_clause = '(in (word "\\"$@\\""))'
        return f'(select (word "{var_escaped}") {in_clause} {self.body.to_sexp()}){suffix}'


@dataclass
class Case(Node):
    """A case statement."""

    word: Word
    patterns: list["CasePattern"]
    redirects: list[Node]

    def __init__(self, word: Word, patterns: list["CasePattern"], redirects: list[Node] = None):
        self.kind = "case"
        self.word = word
        self.patterns = patterns
        self.redirects = redirects or []

    def to_sexp(self) -> str:
        parts = [f"(case {self.word.to_sexp()}"]
        parts.extend(p.to_sexp() for p in self.patterns)
        base = " ".join(parts) + ")"
        if self.redirects:
            return base + " " + " ".join(r.to_sexp() for r in self.redirects)
        return base


@dataclass
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
        parts = [f"(pattern ({pattern_str})"]
        if self.body:
            parts.append(f" {self.body.to_sexp()}")
        else:
            parts.append(" ()")
        # Oracle doesn't output fallthrough/falltest markers
        parts.append(")")
        return "".join(parts)


@dataclass
class Function(Node):
    """A function definition."""

    name: str
    body: Node

    def __init__(self, name: str, body: Node):
        self.kind = "function"
        self.name = name
        self.body = body

    def to_sexp(self) -> str:
        return f'(function "{self.name}" {self.body.to_sexp()})'


@dataclass
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
            escaped_arg = (self.arg or "").replace("\\", "\\\\").replace('"', '\\"')
            return f'(param "{escaped_param}" "{escaped_op}" "{escaped_arg}")'
        return f'(param "{escaped_param}")'


@dataclass
class ParamLength(Node):
    """A parameter length expansion ${#var}."""

    param: str

    def __init__(self, param: str):
        self.kind = "param-len"
        self.param = param

    def to_sexp(self) -> str:
        escaped = self.param.replace("\\", "\\\\").replace('"', '\\"')
        return f'(param-len "{escaped}")'


@dataclass
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
            escaped_arg = (self.arg or "").replace("\\", "\\\\").replace('"', '\\"')
            return f'(param-indirect "{escaped}" "{escaped_op}" "{escaped_arg}")'
        return f'(param-indirect "{escaped}")'


@dataclass
class CommandSubstitution(Node):
    """A command substitution $(...) or `...`."""

    command: Node

    def __init__(self, command: Node):
        self.kind = "cmdsub"
        self.command = command

    def to_sexp(self) -> str:
        return f"(cmdsub {self.command.to_sexp()})"


@dataclass
class ArithmeticExpansion(Node):
    """An arithmetic expansion $((...)) with parsed internals."""

    expression: "Node | None"  # Parsed arithmetic expression, or None for empty

    def __init__(self, expression: "Node | None"):
        self.kind = "arith"
        self.expression = expression

    def to_sexp(self) -> str:
        if self.expression is None:
            return "(arith)"
        return f"(arith {self.expression.to_sexp()})"


@dataclass
class ArithmeticCommand(Node):
    """An arithmetic command ((...)) with parsed internals."""

    expression: "Node | None"  # Parsed arithmetic expression, or None for empty
    redirects: list[Node]
    raw_content: str  # Raw expression text for oracle-compatible output

    def __init__(self, expression: "Node | None", redirects: list[Node] = None, raw_content: str = ""):
        self.kind = "arith-cmd"
        self.expression = expression
        self.redirects = redirects or []
        self.raw_content = raw_content

    def to_sexp(self) -> str:
        # Oracle format: (arith (word "content"))
        # Redirects are siblings: (arith (word "...")) (redirect ...)
        escaped = self.raw_content.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        result = f'(arith (word "{escaped}"))'
        if self.redirects:
            redirect_sexps = " ".join(r.to_sexp() for r in self.redirects)
            return f"{result} {redirect_sexps}"
        return result


# Arithmetic expression nodes


@dataclass
class ArithNumber(Node):
    """A numeric literal in arithmetic context."""

    value: str  # Raw string (may be hex, octal, base#n)

    def __init__(self, value: str):
        self.kind = "number"
        self.value = value

    def to_sexp(self) -> str:
        return f'(number "{self.value}")'


@dataclass
class ArithVar(Node):
    """A variable reference in arithmetic context (without $)."""

    name: str

    def __init__(self, name: str):
        self.kind = "var"
        self.name = name

    def to_sexp(self) -> str:
        return f'(var "{self.name}")'


@dataclass
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
        return f'(binary-op "{self.op}" {self.left.to_sexp()} {self.right.to_sexp()})'


@dataclass
class ArithUnaryOp(Node):
    """A unary operation in arithmetic."""

    op: str
    operand: Node

    def __init__(self, op: str, operand: Node):
        self.kind = "unary-op"
        self.op = op
        self.operand = operand

    def to_sexp(self) -> str:
        return f'(unary-op "{self.op}" {self.operand.to_sexp()})'


@dataclass
class ArithPreIncr(Node):
    """Pre-increment ++var."""

    operand: Node

    def __init__(self, operand: Node):
        self.kind = "pre-incr"
        self.operand = operand

    def to_sexp(self) -> str:
        return f"(pre-incr {self.operand.to_sexp()})"


@dataclass
class ArithPostIncr(Node):
    """Post-increment var++."""

    operand: Node

    def __init__(self, operand: Node):
        self.kind = "post-incr"
        self.operand = operand

    def to_sexp(self) -> str:
        return f"(post-incr {self.operand.to_sexp()})"


@dataclass
class ArithPreDecr(Node):
    """Pre-decrement --var."""

    operand: Node

    def __init__(self, operand: Node):
        self.kind = "pre-decr"
        self.operand = operand

    def to_sexp(self) -> str:
        return f"(pre-decr {self.operand.to_sexp()})"


@dataclass
class ArithPostDecr(Node):
    """Post-decrement var--."""

    operand: Node

    def __init__(self, operand: Node):
        self.kind = "post-decr"
        self.operand = operand

    def to_sexp(self) -> str:
        return f"(post-decr {self.operand.to_sexp()})"


@dataclass
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
        return f'(assign "{self.op}" {self.target.to_sexp()} {self.value.to_sexp()})'


@dataclass
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
        return f"(ternary {self.condition.to_sexp()} {self.if_true.to_sexp()} {self.if_false.to_sexp()})"


@dataclass
class ArithComma(Node):
    """Comma operator expr, expr."""

    left: Node
    right: Node

    def __init__(self, left: Node, right: Node):
        self.kind = "comma"
        self.left = left
        self.right = right

    def to_sexp(self) -> str:
        return f"(comma {self.left.to_sexp()} {self.right.to_sexp()})"


@dataclass
class ArithSubscript(Node):
    """Array subscript arr[expr]."""

    array: str
    index: Node

    def __init__(self, array: str, index: Node):
        self.kind = "subscript"
        self.array = array
        self.index = index

    def to_sexp(self) -> str:
        return f'(subscript "{self.array}" {self.index.to_sexp()})'


@dataclass
class ArithEscape(Node):
    """An escaped character in arithmetic expression."""

    char: str

    def __init__(self, char: str):
        self.kind = "escape"
        self.char = char

    def to_sexp(self) -> str:
        return f'(escape "{self.char}")'


@dataclass
class ArithDeprecated(Node):
    """A deprecated arithmetic expansion $[expr]."""

    expression: str

    def __init__(self, expression: str):
        self.kind = "arith-deprecated"
        self.expression = expression

    def to_sexp(self) -> str:
        escaped = self.expression.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'(arith-deprecated "{escaped}")'


@dataclass
class AnsiCQuote(Node):
    """An ANSI-C quoted string $'...'."""

    content: str

    def __init__(self, content: str):
        self.kind = "ansi-c"
        self.content = content

    def to_sexp(self) -> str:
        escaped = self.content.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'(ansi-c "{escaped}")'


@dataclass
class LocaleString(Node):
    """A locale-translated string $"..."."""

    content: str

    def __init__(self, content: str):
        self.kind = "locale"
        self.content = content

    def to_sexp(self) -> str:
        escaped = self.content.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'(locale "{escaped}")'


@dataclass
class ProcessSubstitution(Node):
    """A process substitution <(...) or >(...)."""

    direction: str  # "<" for input, ">" for output
    command: Node

    def __init__(self, direction: str, command: Node):
        self.kind = "procsub"
        self.direction = direction
        self.command = command

    def to_sexp(self) -> str:
        return f'(procsub "{self.direction}" {self.command.to_sexp()})'


@dataclass
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
        return f"(negation {self.pipeline.to_sexp()})"


@dataclass
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
            return f"(time -p {self.pipeline.to_sexp()})"
        return f"(time {self.pipeline.to_sexp()})"


@dataclass
class ConditionalExpr(Node):
    """A conditional expression [[ expression ]]."""

    body: "Node | str"  # Parsed node or raw string for backwards compat
    redirects: list[Node]

    def __init__(self, body: "Node | str", redirects: list[Node] = None):
        self.kind = "cond-expr"
        self.body = body
        self.redirects = redirects or []

    def to_sexp(self) -> str:
        # Oracle format: (cond ...) not (cond-expr ...)
        # Redirects are siblings, not children: (cond ...) (redirect ...)
        if isinstance(self.body, str):
            escaped = self.body.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
            result = f'(cond "{escaped}")'
        else:
            result = f"(cond {self.body.to_sexp()})"
        if self.redirects:
            redirect_sexps = " ".join(r.to_sexp() for r in self.redirects)
            return f"{result} {redirect_sexps}"
        return result


@dataclass
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
        return f'(cond-unary "{self.op}" (cond-term "{self.operand.value}"))'


@dataclass
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
        return f'(cond-binary "{self.op}" (cond-term "{left_val}") (cond-term "{right_val}"))'


@dataclass
class CondAnd(Node):
    """Logical AND in [[ ]], e.g., expr1 && expr2."""

    left: Node
    right: Node

    def __init__(self, left: Node, right: Node):
        self.kind = "cond-and"
        self.left = left
        self.right = right

    def to_sexp(self) -> str:
        return f"(cond-and {self.left.to_sexp()} {self.right.to_sexp()})"


@dataclass
class CondOr(Node):
    """Logical OR in [[ ]], e.g., expr1 || expr2."""

    left: Node
    right: Node

    def __init__(self, left: Node, right: Node):
        self.kind = "cond-or"
        self.left = left
        self.right = right

    def to_sexp(self) -> str:
        return f"(cond-or {self.left.to_sexp()} {self.right.to_sexp()})"


@dataclass
class CondNot(Node):
    """Logical NOT in [[ ]], e.g., ! expr."""

    operand: Node

    def __init__(self, operand: Node):
        self.kind = "cond-not"
        self.operand = operand

    def to_sexp(self) -> str:
        # Oracle ignores negation - just output the operand
        return self.operand.to_sexp()


@dataclass
class CondParen(Node):
    """Parenthesized group in [[ ]], e.g., ( expr )."""

    inner: Node

    def __init__(self, inner: Node):
        self.kind = "cond-paren"
        self.inner = inner

    def to_sexp(self) -> str:
        return f"(cond-expr {self.inner.to_sexp()})"


@dataclass
class Array(Node):
    """An array literal (word1 word2 ...)."""

    elements: list[Word]

    def __init__(self, elements: list[Word]):
        self.kind = "array"
        self.elements = elements

    def to_sexp(self) -> str:
        if not self.elements:
            return "(array)"
        inner = " ".join(e.to_sexp() for e in self.elements)
        return f"(array {inner})"


@dataclass
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
        return f'(coproc "{name}" {self.command.to_sexp()})'


def _format_cmdsub_node(node: Node, indent: int = 0, in_procsub: bool = False) -> str:
    """Format an AST node for command substitution output (oracle pretty-print format)."""
    sp = " " * indent
    inner_sp = " " * (indent + 4)
    if isinstance(node, Empty):
        return ""
    if isinstance(node, Command):
        parts = [w._expand_all_ansi_c_quotes(w.value) for w in node.words]
        for r in node.redirects:
            parts.append(_format_redirect(r))
        return " ".join(parts)
    if isinstance(node, Pipeline):
        return " | ".join(_format_cmdsub_node(cmd, indent) for cmd in node.commands)
    if isinstance(node, List):
        # Join commands with operators
        result = []
        for i, p in enumerate(node.parts):
            if isinstance(p, Operator):
                if p.op == ";":
                    result.append(";")
                elif p.op == "\n":
                    # Skip newline if it follows a semicolon (redundant separator)
                    if result and result[-1] == ";":
                        continue
                    result.append("\n")
                elif p.op == "&":
                    result.append(" &")
                else:
                    result.append(f" {p.op}")
            else:
                if result and not result[-1].endswith((" ", "\n")):
                    result.append(" ")
                result.append(_format_cmdsub_node(p, indent))
        # Strip trailing ; or newline
        s = "".join(result)
        while s.endswith(";") or s.endswith("\n"):
            s = s[:-1]
        return s
    if isinstance(node, If):
        cond = _format_cmdsub_node(node.condition, indent)
        then_body = _format_cmdsub_node(node.then_body, indent + 4)
        result = f"if {cond}; then\n{inner_sp}{then_body};"
        if node.else_body:
            else_body = _format_cmdsub_node(node.else_body, indent + 4)
            result += f"\n{sp}else\n{inner_sp}{else_body};"
        result += f"\n{sp}fi"
        return result
    if isinstance(node, While):
        cond = _format_cmdsub_node(node.condition, indent)
        body = _format_cmdsub_node(node.body, indent + 4)
        return f"while {cond}; do\n{inner_sp}{body};\n{sp}done"
    if isinstance(node, Until):
        cond = _format_cmdsub_node(node.condition, indent)
        body = _format_cmdsub_node(node.body, indent + 4)
        return f"until {cond}; do\n{inner_sp}{body};\n{sp}done"
    if isinstance(node, For):
        var = node.var
        body = _format_cmdsub_node(node.body, indent + 4)
        if node.words:
            words = " ".join(w.value for w in node.words)
            return f"for {var} in {words};\ndo\n{inner_sp}{body};\n{sp}done"
        return f"for {var};\ndo\n{inner_sp}{body};\n{sp}done"
    if isinstance(node, Case):
        word = node.word.value
        patterns = []
        for i, p in enumerate(node.patterns):
            pat = p.pattern.replace("|", " | ")
            body = _format_cmdsub_node(p.body, indent + 8) if p.body else ""
            term = p.terminator  # ;;, ;&, or ;;&
            if i == 0:
                # First pattern on same line as 'in'
                patterns.append(f" {pat})\n{' ' * (indent + 8)}{body}\n{' ' * (indent + 4)}{term}")
            else:
                patterns.append(f"{pat})\n{' ' * (indent + 8)}{body}\n{' ' * (indent + 4)}{term}")
        pattern_str = f"\n{' ' * (indent + 4)}".join(patterns)
        return f"case {word} in{pattern_str}\n{sp}esac"
    if isinstance(node, Function):
        name = node.name
        # Get the body content - if it's a BraceGroup, unwrap it
        if isinstance(node.body, BraceGroup):
            body = _format_cmdsub_node(node.body.body, indent + 4)
        else:
            body = _format_cmdsub_node(node.body, indent + 4)
        body = body.rstrip(";")  # Strip trailing semicolons
        return f"function {name} () \n{{ \n{inner_sp}{body}\n}}"
    if isinstance(node, Subshell):
        body = _format_cmdsub_node(node.body, indent, in_procsub)
        redirects = " ".join(_format_redirect(r) for r in node.redirects) if node.redirects else ""
        if in_procsub:
            if redirects:
                return f"({body}) {redirects}"
            return f"({body})"
        if redirects:
            return f"( {body} ) {redirects}"
        return f"( {body} )"
    if isinstance(node, BraceGroup):
        body = _format_cmdsub_node(node.body, indent)
        body = body.rstrip(";")  # Strip trailing semicolons before adding our own
        return f"{{ {body}; }}"
    if isinstance(node, ArithmeticCommand):
        return f"(({node.raw_content}))"
    # Fallback: return empty for unknown types
    return ""


def _format_redirect(r: "Redirect | HereDoc") -> str:
    """Format a redirect for command substitution output."""
    if isinstance(r, HereDoc):
        # Include heredoc content: <<DELIM\ncontent\nDELIM\n
        op = "<<-" if r.strip_tabs else "<<"
        return f"{op}{r.delimiter}\n{r.content}{r.delimiter}\n"
    op = r.op
    target = r.target.value
    # For fd duplication (target starts with &), handle normalization
    if target.startswith("&"):
        # Normalize N<&- to N>&- (close always uses >)
        if target == "&-" and op.endswith("<"):
            op = op[:-1] + ">"
        # Add default fd for bare >&N or <&N
        if op == ">":
            op = "1>"
        elif op == "<":
            op = "0<"
        return f"{op}{target}"
    return f"{op} {target}"


def _normalize_fd_redirects(s: str) -> str:
    """Normalize fd redirects in a raw string: >&2 -> 1>&2, <&N -> 0<&N."""
    import re
    # Match >&N or <&N not preceded by a digit, add default fd
    # >&N -> 1>&N, <&N -> 0<&N
    s = re.sub(r'(?<![0-9])>&(\d)', r'1>&\1', s)
    s = re.sub(r'(?<![0-9])<&(\d)', r'0<&\1', s)
    return s


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
