"""Recursive descent parser for bash."""

from .ast import (
    AnsiCQuote,
    ArithAssign,
    ArithBinaryOp,
    ArithComma,
    ArithDeprecated,
    ArithEscape,
    ArithmeticCommand,
    ArithmeticExpansion,
    ArithNumber,
    ArithPostDecr,
    ArithPostIncr,
    ArithPreDecr,
    ArithPreIncr,
    ArithSubscript,
    ArithTernary,
    ArithUnaryOp,
    ArithVar,
    Array,
    BinaryTest,
    BraceGroup,
    Case,
    CasePattern,
    Command,
    CommandSubstitution,
    CondAnd,
    ConditionalExpr,
    CondNot,
    CondOr,
    CondParen,
    Coproc,
    Empty,
    For,
    ForArith,
    Function,
    HereDoc,
    If,
    List,
    LocaleString,
    Negation,
    Node,
    Operator,
    ParamExpansion,
    ParamIndirect,
    ParamLength,
    PipeBoth,
    Pipeline,
    ProcessSubstitution,
    Redirect,
    Select,
    Subshell,
    Time,
    UnaryTest,
    Until,
    While,
    Word,
)
from .errors import ParseError

# Reserved words that cannot be command names
RESERVED_WORDS = {
    "if",
    "then",
    "elif",
    "else",
    "fi",
    "while",
    "until",
    "for",
    "select",
    "do",
    "done",
    "case",
    "esac",
    "in",
    "function",
    "coproc",
}

# Metacharacters that break words (unquoted)
# Note: {} are NOT metacharacters - they're only special at command position
# for brace groups. In words like {a,b,c}, braces are literal.
METACHAR = set(" \t\n|&;()<>")


class Parser:
    """Recursive descent parser for bash."""

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.length = len(source)

    def at_end(self) -> bool:
        """Check if we've reached the end of input."""
        return self.pos >= self.length

    def peek(self) -> str | None:
        """Return current character without consuming."""
        if self.at_end():
            return None
        return self.source[self.pos]

    def advance(self) -> str | None:
        """Consume and return current character."""
        if self.at_end():
            return None
        ch = self.source[self.pos]
        self.pos += 1
        return ch

    def skip_whitespace(self) -> None:
        """Skip spaces, tabs, comments, and backslash-newline continuations."""
        while not self.at_end():
            ch = self.peek()
            if ch in " \t":
                self.advance()
            elif ch == "#":
                # Skip comment to end of line (but not the newline itself)
                while not self.at_end() and self.peek() != "\n":
                    self.advance()
            elif ch == "\\" and self.pos + 1 < self.length and self.source[self.pos + 1] == "\n":
                # Backslash-newline is line continuation - skip both
                self.advance()
                self.advance()
            else:
                break

    def skip_whitespace_and_newlines(self) -> None:
        """Skip spaces, tabs, newlines, comments, and backslash-newline continuations."""
        while not self.at_end():
            ch = self.peek()
            if ch in " \t\n":
                self.advance()
                # After advancing past a newline, skip any pending heredoc content
                if ch == "\n":
                    if (
                        hasattr(self, "_pending_heredoc_end")
                        and self._pending_heredoc_end > self.pos
                    ):
                        self.pos = self._pending_heredoc_end
                        del self._pending_heredoc_end
            elif ch == "#":
                # Skip comment to end of line
                while not self.at_end() and self.peek() != "\n":
                    self.advance()
            elif ch == "\\" and self.pos + 1 < self.length and self.source[self.pos + 1] == "\n":
                # Backslash-newline is line continuation - skip both
                self.advance()
                self.advance()
            else:
                break

    def peek_word(self) -> str | None:
        """Peek at the next word without consuming it."""
        saved_pos = self.pos
        self.skip_whitespace()

        if self.at_end() or self.peek() in METACHAR:
            self.pos = saved_pos
            return None

        chars = []
        while not self.at_end() and self.peek() not in METACHAR:
            ch = self.peek()
            # Stop at quotes - don't include in peek
            if ch in "\"'":
                break
            chars.append(self.advance())

        word = "".join(chars) if chars else None
        self.pos = saved_pos
        return word

    def consume_word(self, expected: str) -> bool:
        """Try to consume a specific reserved word. Returns True if successful."""
        saved_pos = self.pos
        self.skip_whitespace()

        word = self.peek_word()
        if word != expected:
            self.pos = saved_pos
            return False

        # Actually consume the word
        self.skip_whitespace()
        for _ in expected:
            self.advance()
        return True

    def parse_word(self, at_command_start: bool = False) -> Word | None:
        """Parse a word token, detecting parameter expansions and command substitutions.

        at_command_start: When True, preserve spaces inside brackets for array
        assignments like a[1 + 2]=. When False, spaces break the word.
        """
        self.skip_whitespace()

        if self.at_end():
            return None

        start = self.pos
        chars = []
        parts = []
        bracket_depth = 0  # Track [...] for array subscripts
        seen_equals = False  # Track if we've seen = (for array assignment detection)

        while not self.at_end():
            ch = self.peek()

            # Track bracket depth for array subscripts like a[1+2]=3
            # Inside brackets, metacharacters like | and ( are literal
            # Only track [ after we've seen some chars (so [ -f file ] still works)
            # Only at command start (array assignments), not in argument position
            # Only BEFORE = sign (key=1],a[1 should not track the [1 part)
            # Only after identifier char (not [[ which is conditional keyword)
            if ch == "[" and chars and at_command_start and not seen_equals:
                prev_char = chars[-1]
                if prev_char.isalnum() or prev_char in "_]":
                    bracket_depth += 1
                    chars.append(self.advance())
                    continue
            if ch == "]" and bracket_depth > 0:
                bracket_depth -= 1
                chars.append(self.advance())
                continue
            if ch == "=" and bracket_depth == 0:
                seen_equals = True

            # Single-quoted string - no expansion
            if ch == "'":
                self.advance()  # consume opening quote
                chars.append("'")
                while not self.at_end() and self.peek() != "'":
                    chars.append(self.advance())
                if self.at_end():
                    raise ParseError("Unterminated single quote", pos=start)
                chars.append(self.advance())  # consume closing quote

            # Double-quoted string - expansions happen inside
            elif ch == '"':
                self.advance()  # consume opening quote
                chars.append('"')
                while not self.at_end() and self.peek() != '"':
                    c = self.peek()
                    # Handle escape sequences in double quotes
                    if c == "\\" and self.pos + 1 < self.length:
                        next_c = self.source[self.pos + 1]
                        if next_c == "\n":
                            # Line continuation - skip both backslash and newline
                            self.advance()
                            self.advance()
                        else:
                            chars.append(self.advance())  # backslash
                            chars.append(self.advance())  # escaped char
                    # Handle arithmetic expansion $((...))
                    elif (
                        c == "$"
                        and self.pos + 2 < self.length
                        and self.source[self.pos + 1] == "("
                        and self.source[self.pos + 2] == "("
                    ):
                        arith_node, arith_text = self._parse_arithmetic_expansion()
                        if arith_node:
                            parts.append(arith_node)
                            chars.append(arith_text)
                        else:
                            # Not arithmetic - try command substitution
                            cmdsub_node, cmdsub_text = self._parse_command_substitution()
                            if cmdsub_node:
                                parts.append(cmdsub_node)
                                chars.append(cmdsub_text)
                            else:
                                chars.append(self.advance())
                    # Handle deprecated arithmetic expansion $[expr]
                    elif (
                        c == "$" and self.pos + 1 < self.length and self.source[self.pos + 1] == "["
                    ):
                        arith_node, arith_text = self._parse_deprecated_arithmetic()
                        if arith_node:
                            parts.append(arith_node)
                            chars.append(arith_text)
                        else:
                            chars.append(self.advance())
                    # Handle command substitution $(...)
                    elif (
                        c == "$" and self.pos + 1 < self.length and self.source[self.pos + 1] == "("
                    ):
                        cmdsub_node, cmdsub_text = self._parse_command_substitution()
                        if cmdsub_node:
                            parts.append(cmdsub_node)
                            chars.append(cmdsub_text)
                        else:
                            chars.append(self.advance())
                    # Handle parameter expansion inside double quotes
                    elif c == "$":
                        param_node, param_text = self._parse_param_expansion()
                        if param_node:
                            parts.append(param_node)
                            chars.append(param_text)
                        else:
                            chars.append(self.advance())  # just $
                    # Handle backtick command substitution
                    elif c == "`":
                        cmdsub_node, cmdsub_text = self._parse_backtick_substitution()
                        if cmdsub_node:
                            parts.append(cmdsub_node)
                            chars.append(cmdsub_text)
                        else:
                            chars.append(self.advance())
                    else:
                        chars.append(self.advance())
                if self.at_end():
                    raise ParseError("Unterminated double quote", pos=start)
                chars.append(self.advance())  # consume closing quote

            # Escape outside quotes
            elif ch == "\\" and self.pos + 1 < self.length:
                next_ch = self.source[self.pos + 1]
                if next_ch == "\n":
                    # Line continuation - skip both backslash and newline
                    self.advance()
                    self.advance()
                else:
                    chars.append(self.advance())  # backslash
                    chars.append(self.advance())  # escaped char

            # ANSI-C quoting $'...'
            elif ch == "$" and self.pos + 1 < self.length and self.source[self.pos + 1] == "'":
                ansi_node, ansi_text = self._parse_ansi_c_quote()
                if ansi_node:
                    parts.append(ansi_node)
                    chars.append(ansi_text)
                else:
                    chars.append(self.advance())

            # Locale translation $"..."
            elif ch == "$" and self.pos + 1 < self.length and self.source[self.pos + 1] == '"':
                locale_node, locale_text, inner_parts = self._parse_locale_string()
                if locale_node:
                    parts.append(locale_node)
                    parts.extend(inner_parts)
                    chars.append(locale_text)
                else:
                    chars.append(self.advance())

            # Arithmetic expansion $((...)) - try before command substitution
            # If it fails (returns None), fall through to command substitution
            elif (
                ch == "$"
                and self.pos + 2 < self.length
                and self.source[self.pos + 1] == "("
                and self.source[self.pos + 2] == "("
            ):
                arith_node, arith_text = self._parse_arithmetic_expansion()
                if arith_node:
                    parts.append(arith_node)
                    chars.append(arith_text)
                else:
                    # Not arithmetic (e.g., '$( ( ... ) )' is command sub + subshell)
                    cmdsub_node, cmdsub_text = self._parse_command_substitution()
                    if cmdsub_node:
                        parts.append(cmdsub_node)
                        chars.append(cmdsub_text)
                    else:
                        chars.append(self.advance())

            # Deprecated arithmetic expansion $[expr]
            elif ch == "$" and self.pos + 1 < self.length and self.source[self.pos + 1] == "[":
                arith_node, arith_text = self._parse_deprecated_arithmetic()
                if arith_node:
                    parts.append(arith_node)
                    chars.append(arith_text)
                else:
                    chars.append(self.advance())

            # Command substitution $(...)
            elif ch == "$" and self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
                cmdsub_node, cmdsub_text = self._parse_command_substitution()
                if cmdsub_node:
                    parts.append(cmdsub_node)
                    chars.append(cmdsub_text)
                else:
                    chars.append(self.advance())

            # Parameter expansion $var or ${...}
            elif ch == "$":
                param_node, param_text = self._parse_param_expansion()
                if param_node:
                    parts.append(param_node)
                    chars.append(param_text)
                else:
                    chars.append(self.advance())  # just $

            # Backtick command substitution
            elif ch == "`":
                cmdsub_node, cmdsub_text = self._parse_backtick_substitution()
                if cmdsub_node:
                    parts.append(cmdsub_node)
                    chars.append(cmdsub_text)
                else:
                    chars.append(self.advance())

            # Process substitution <(...) or >(...)
            elif ch in "<>" and self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
                procsub_node, procsub_text = self._parse_process_substitution()
                if procsub_node:
                    parts.append(procsub_node)
                    chars.append(procsub_text)
                else:
                    # Not a process substitution, treat as metacharacter
                    break

            # Array literal: name=(elements) or name+=(elements)
            elif (
                ch == "("
                and chars
                and (chars[-1] == "=" or (len(chars) >= 2 and chars[-2:] == ["+", "="]))
            ):
                array_node, array_text = self._parse_array_literal()
                if array_node:
                    parts.append(array_node)
                    chars.append(array_text)
                else:
                    # Unexpected: ( without matching )
                    break

            # Extglob pattern @(), ?(), *(), +(), !()
            elif ch in "@?*+!" and self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
                chars.append(self.advance())  # @, ?, *, +, or !
                chars.append(self.advance())  # (
                extglob_depth = 1
                while not self.at_end() and extglob_depth > 0:
                    c = self.peek()
                    if c == ")":
                        chars.append(self.advance())
                        extglob_depth -= 1
                    elif c == "(":
                        chars.append(self.advance())
                        extglob_depth += 1
                    elif c == "\\":
                        chars.append(self.advance())
                        if not self.at_end():
                            chars.append(self.advance())
                    elif c == "'":
                        chars.append(self.advance())
                        while not self.at_end() and self.peek() != "'":
                            chars.append(self.advance())
                        if not self.at_end():
                            chars.append(self.advance())
                    elif c == '"':
                        chars.append(self.advance())
                        while not self.at_end() and self.peek() != '"':
                            if self.peek() == "\\" and self.pos + 1 < self.length:
                                chars.append(self.advance())
                            chars.append(self.advance())
                        if not self.at_end():
                            chars.append(self.advance())
                    elif (
                        c == "$" and self.pos + 1 < self.length and self.source[self.pos + 1] == "("
                    ):
                        # $() or $(()) inside extglob
                        chars.append(self.advance())  # $
                        chars.append(self.advance())  # (
                        if not self.at_end() and self.peek() == "(":
                            # $(()) arithmetic
                            chars.append(self.advance())  # second (
                            paren_depth = 2
                            while not self.at_end() and paren_depth > 0:
                                pc = self.peek()
                                if pc == "(":
                                    paren_depth += 1
                                elif pc == ")":
                                    paren_depth -= 1
                                chars.append(self.advance())
                        else:
                            # $() command sub - count as nested paren
                            extglob_depth += 1
                    elif (
                        c in "@?*+!"
                        and self.pos + 1 < self.length
                        and self.source[self.pos + 1] == "("
                    ):
                        # Nested extglob
                        chars.append(self.advance())  # @, ?, *, +, or !
                        chars.append(self.advance())  # (
                        extglob_depth += 1
                    else:
                        chars.append(self.advance())

            # Metacharacter ends the word (unless inside brackets like a[x|y]=1)
            elif ch in METACHAR and bracket_depth == 0:
                break

            # Regular character (including metacharacters inside brackets)
            else:
                chars.append(self.advance())

        if not chars:
            return None

        return Word("".join(chars), parts if parts else None)

    def _parse_command_substitution(self) -> tuple[Node | None, str]:
        """Parse a $(...) command substitution.

        Returns (node, text) where node is CommandSubstitution and text is raw text.
        """
        if self.at_end() or self.peek() != "$":
            return None, ""

        start = self.pos
        self.advance()  # consume $

        if self.at_end() or self.peek() != "(":
            self.pos = start
            return None, ""

        self.advance()  # consume (

        # Find matching closing paren, being aware of:
        # - Nested $() and plain ()
        # - Quoted strings
        # - case statements (where ) after pattern isn't a closer)
        content_start = self.pos
        depth = 1
        case_depth = 0  # Track nested case statements

        while not self.at_end() and depth > 0:
            c = self.peek()

            # Single-quoted string - no special chars inside
            if c == "'":
                self.advance()
                while not self.at_end() and self.peek() != "'":
                    self.advance()
                if not self.at_end():
                    self.advance()
                continue

            # Double-quoted string - handle escapes and nested $()
            if c == '"':
                self.advance()
                while not self.at_end() and self.peek() != '"':
                    if self.peek() == "\\" and self.pos + 1 < self.length:
                        self.advance()
                        self.advance()
                    elif (
                        self.peek() == "$"
                        and self.pos + 1 < self.length
                        and self.source[self.pos + 1] == "("
                    ):
                        # Nested $() in double quotes - recurse to find matching )
                        # Command substitution creates new quoting context
                        self.advance()  # $
                        self.advance()  # (
                        nested_depth = 1
                        while not self.at_end() and nested_depth > 0:
                            nc = self.peek()
                            if nc == "'":
                                self.advance()
                                while not self.at_end() and self.peek() != "'":
                                    self.advance()
                                if not self.at_end():
                                    self.advance()
                            elif nc == '"':
                                self.advance()
                                while not self.at_end() and self.peek() != '"':
                                    if self.peek() == "\\" and self.pos + 1 < self.length:
                                        self.advance()
                                    self.advance()
                                if not self.at_end():
                                    self.advance()
                            elif nc == "\\" and self.pos + 1 < self.length:
                                self.advance()
                                self.advance()
                            elif (
                                nc == "$"
                                and self.pos + 1 < self.length
                                and self.source[self.pos + 1] == "("
                            ):
                                self.advance()
                                self.advance()
                                nested_depth += 1
                            elif nc == "(":
                                nested_depth += 1
                                self.advance()
                            elif nc == ")":
                                nested_depth -= 1
                                if nested_depth > 0:
                                    self.advance()
                            else:
                                self.advance()
                        if nested_depth == 0:
                            self.advance()  # consume the closing )
                    else:
                        self.advance()
                if not self.at_end():
                    self.advance()
                continue

            # Backslash escape
            if c == "\\" and self.pos + 1 < self.length:
                self.advance()
                self.advance()
                continue

            # Comment - skip until newline
            if c == "#" and self._is_word_boundary_before():
                while not self.at_end() and self.peek() != "\n":
                    self.advance()
                continue

            # Heredoc - skip until delimiter line is found
            if c == "<" and self.pos + 1 < self.length and self.source[self.pos + 1] == "<":
                self.advance()  # first <
                self.advance()  # second <
                # Check for <<- (strip tabs)
                if not self.at_end() and self.peek() == "-":
                    self.advance()
                # Skip whitespace before delimiter
                while not self.at_end() and self.peek() in " \t":
                    self.advance()
                # Parse delimiter (handle quoting)
                delimiter_chars = []
                if not self.at_end():
                    ch = self.peek()
                    if ch in "'\"":
                        quote = self.advance()
                        while not self.at_end() and self.peek() != quote:
                            delimiter_chars.append(self.advance())
                        if not self.at_end():
                            self.advance()  # closing quote
                    elif ch == "\\":
                        self.advance()
                        # Backslash quotes - first char can be special, then read word
                        if not self.at_end():
                            delimiter_chars.append(self.advance())
                        while not self.at_end() and self.peek() not in " \t\n;|&<>()":
                            delimiter_chars.append(self.advance())
                    else:
                        # Unquoted delimiter with possible embedded quotes
                        while not self.at_end() and self.peek() not in " \t\n;|&<>()":
                            ch = self.peek()
                            if ch in "'\"":
                                quote = self.advance()
                                while not self.at_end() and self.peek() != quote:
                                    delimiter_chars.append(self.advance())
                                if not self.at_end():
                                    self.advance()
                            elif ch == "\\":
                                self.advance()
                                if not self.at_end():
                                    delimiter_chars.append(self.advance())
                            else:
                                delimiter_chars.append(self.advance())
                delimiter = "".join(delimiter_chars)
                if delimiter:
                    # Skip to end of current line
                    while not self.at_end() and self.peek() != "\n":
                        self.advance()
                    # Skip newline
                    if not self.at_end() and self.peek() == "\n":
                        self.advance()
                    # Skip lines until we find the delimiter
                    while not self.at_end():
                        line_start = self.pos
                        line_end = self.pos
                        while line_end < self.length and self.source[line_end] != "\n":
                            line_end += 1
                        line = self.source[line_start:line_end]
                        # Move position to end of line
                        self.pos = line_end
                        # Check if this line matches delimiter
                        if line == delimiter or line.lstrip("\t") == delimiter:
                            # Skip newline after delimiter
                            if not self.at_end() and self.peek() == "\n":
                                self.advance()
                            break
                        # Skip newline and continue
                        if not self.at_end() and self.peek() == "\n":
                            self.advance()
                continue

            # Track case/esac for pattern terminator handling
            # Check for 'case' keyword (word boundary: preceded by space/newline/start)
            if c == "c" and self._is_word_boundary_before():
                if self._lookahead_keyword("case"):
                    case_depth += 1
                    self._skip_keyword("case")
                    continue

            # Check for 'esac' keyword
            if c == "e" and self._is_word_boundary_before() and case_depth > 0:
                if self._lookahead_keyword("esac"):
                    case_depth -= 1
                    self._skip_keyword("esac")
                    continue

            # Handle parentheses
            if c == "(":
                depth += 1
            elif c == ")":
                # In case statement, ) after pattern is a terminator, not a paren
                # Only decrement depth if we're not in a case pattern position
                if case_depth > 0 and depth == 1:
                    # This ) might be a case pattern terminator, not closing the $(
                    # Look ahead to see if there's still content that needs esac
                    saved = self.pos
                    self.advance()  # skip this )
                    # Scan ahead to see if we find esac that closes our case
                    # before finding a ) that could close our $(
                    temp_depth = 0
                    temp_case_depth = case_depth  # Track nested cases in lookahead
                    found_esac = False
                    while not self.at_end():
                        tc = self.peek()
                        if tc == "'" or tc == '"':
                            # Skip quoted strings
                            q = tc
                            self.advance()
                            while not self.at_end() and self.peek() != q:
                                if q == '"' and self.peek() == "\\":
                                    self.advance()
                                self.advance()
                            if not self.at_end():
                                self.advance()
                        elif (
                            tc == "c"
                            and self._is_word_boundary_before()
                            and self._lookahead_keyword("case")
                        ):
                            # Nested case in lookahead
                            temp_case_depth += 1
                            self._skip_keyword("case")
                        elif (
                            tc == "e"
                            and self._is_word_boundary_before()
                            and self._lookahead_keyword("esac")
                        ):
                            temp_case_depth -= 1
                            if temp_case_depth == 0:
                                # All cases are closed
                                found_esac = True
                                break
                            self._skip_keyword("esac")
                        elif tc == "(":
                            temp_depth += 1
                            self.advance()
                        elif tc == ")":
                            # In case, ) is a pattern terminator, not a closer
                            if temp_case_depth > 0:
                                self.advance()
                            elif temp_depth > 0:
                                temp_depth -= 1
                                self.advance()
                            else:
                                # Found a ) that could be our closer
                                break
                        else:
                            self.advance()
                    self.pos = saved
                    if found_esac:
                        # This ) is a case pattern terminator, not our closer
                        self.advance()
                        continue
                depth -= 1

            if depth > 0:
                self.advance()

        if depth != 0:
            self.pos = start
            return None, ""

        content = self.source[content_start : self.pos]
        self.advance()  # consume final )

        text = self.source[start : self.pos]

        # Parse the content as a command list
        sub_parser = Parser(content)
        cmd = sub_parser.parse_list()
        if cmd is None:
            cmd = Empty()

        return CommandSubstitution(cmd), text

    def _is_word_boundary_before(self) -> bool:
        """Check if current position is at a word boundary (preceded by space/newline/start)."""
        if self.pos == 0:
            return True
        prev = self.source[self.pos - 1]
        return prev in " \t\n;|&<>("

    def _is_assignment_word(self, word: "Word") -> bool:
        """Check if a word is an assignment (contains = outside of quotes)."""
        in_single = False
        in_double = False
        for i, ch in enumerate(word.value):
            if ch == "'" and not in_double:
                in_single = not in_single
            elif ch == '"' and not in_single:
                in_double = not in_double
            elif ch == "\\" and not in_single and i + 1 < len(word.value):
                continue  # Skip next char
            elif ch == "=" and not in_single and not in_double:
                return True
        return False

    def _lookahead_keyword(self, keyword: str) -> bool:
        """Check if keyword appears at current position followed by word boundary."""
        if self.pos + len(keyword) > self.length:
            return False
        if self.source[self.pos : self.pos + len(keyword)] != keyword:
            return False
        # Check word boundary after keyword
        after_pos = self.pos + len(keyword)
        if after_pos >= self.length:
            return True
        after = self.source[after_pos]
        return after in " \t\n;|&<>()"

    def _skip_keyword(self, keyword: str) -> None:
        """Skip over a keyword."""
        for _ in keyword:
            self.advance()

    def _parse_backtick_substitution(self) -> tuple[Node | None, str]:
        """Parse a `...` command substitution.

        Returns (node, text) where node is CommandSubstitution and text is raw text.
        """
        if self.at_end() or self.peek() != "`":
            return None, ""

        start = self.pos
        self.advance()  # consume opening `

        # Find closing backtick, processing escape sequences as we go.
        # In backticks, backslash is special only before $, `, \, or newline.
        # \$ -> $, \` -> `, \\ -> \, \<newline> -> removed (line continuation)
        # other \X -> \X (backslash is literal)
        # content_chars: what gets parsed as the inner command
        # text_chars: what appears in the word representation (with line continuations removed)
        content_chars = []
        text_chars = ["`"]  # opening backtick
        while not self.at_end() and self.peek() != "`":
            c = self.peek()
            if c == "\\" and self.pos + 1 < self.length:
                next_c = self.source[self.pos + 1]
                if next_c == "\n":
                    # Line continuation: skip both backslash and newline
                    self.advance()  # skip \
                    self.advance()  # skip newline
                    # Don't add to content_chars or text_chars
                elif next_c in "$`\\":
                    # Escape sequence: skip backslash in content, keep both in text
                    self.advance()  # skip \
                    escaped = self.advance()
                    content_chars.append(escaped)
                    text_chars.append("\\")
                    text_chars.append(escaped)
                else:
                    # Backslash is literal before other characters
                    ch = self.advance()
                    content_chars.append(ch)
                    text_chars.append(ch)
            else:
                ch = self.advance()
                content_chars.append(ch)
                text_chars.append(ch)

        if self.at_end():
            self.pos = start
            return None, ""

        self.advance()  # consume closing `
        text_chars.append("`")  # closing backtick
        text = "".join(text_chars)
        content = "".join(content_chars)

        # Parse the content as a command list
        sub_parser = Parser(content)
        cmd = sub_parser.parse_list()
        if cmd is None:
            cmd = Empty()

        return CommandSubstitution(cmd), text

    def _parse_process_substitution(self) -> tuple[Node | None, str]:
        """Parse a <(...) or >(...) process substitution.

        Returns (node, text) where node is ProcessSubstitution and text is raw text.
        """
        if self.at_end() or self.peek() not in "<>":
            return None, ""

        start = self.pos
        direction = self.advance()  # consume < or >

        if self.at_end() or self.peek() != "(":
            self.pos = start
            return None, ""

        self.advance()  # consume (

        # Find matching ) - track nested parens and handle quotes
        content_start = self.pos
        depth = 1

        while not self.at_end() and depth > 0:
            c = self.peek()

            # Single-quoted string
            if c == "'":
                self.advance()
                while not self.at_end() and self.peek() != "'":
                    self.advance()
                if not self.at_end():
                    self.advance()
                continue

            # Double-quoted string
            if c == '"':
                self.advance()
                while not self.at_end() and self.peek() != '"':
                    if self.peek() == "\\" and self.pos + 1 < self.length:
                        self.advance()
                    self.advance()
                if not self.at_end():
                    self.advance()
                continue

            # Backslash escape
            if c == "\\" and self.pos + 1 < self.length:
                self.advance()
                self.advance()
                continue

            # Nested parentheses (including nested process substitutions)
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    break

            self.advance()

        if depth != 0:
            self.pos = start
            return None, ""

        content = self.source[content_start : self.pos]
        self.advance()  # consume final )

        text = self.source[start : self.pos]

        # Parse the content as a command list
        sub_parser = Parser(content)
        cmd = sub_parser.parse_list()
        if cmd is None:
            cmd = Empty()

        return ProcessSubstitution(direction, cmd), text

    def _parse_array_literal(self) -> tuple[Node | None, str]:
        """Parse an array literal (word1 word2 ...).

        Returns (node, text) where node is Array and text is raw text.
        Called when positioned at the opening '(' after '=' or '+='.
        """
        if self.at_end() or self.peek() != "(":
            return None, ""

        start = self.pos
        self.advance()  # consume (

        elements = []

        while True:
            # Skip whitespace and newlines between elements
            while not self.at_end() and self.peek() in " \t\n":
                self.advance()

            if self.at_end():
                raise ParseError("Unterminated array literal", pos=start)

            if self.peek() == ")":
                break

            # Parse an element word
            word = self.parse_word()
            if word is None:
                # Might be a closing paren or error
                if self.peek() == ")":
                    break
                raise ParseError("Expected word in array literal", pos=self.pos)

            elements.append(word)

        if self.at_end() or self.peek() != ")":
            raise ParseError("Expected ) to close array literal", pos=self.pos)
        self.advance()  # consume )

        text = self.source[start : self.pos]
        return Array(elements), text

    def _parse_arithmetic_expansion(self) -> tuple[Node | None, str]:
        """Parse a $((...)) arithmetic expansion with parsed internals.

        Returns (node, text) where node is ArithmeticExpansion and text is raw text.
        Returns (None, "") if this is not arithmetic expansion (e.g., $( ( ... ) )
        which is command substitution containing a subshell).
        """
        if self.at_end() or self.peek() != "$":
            return None, ""

        start = self.pos

        # Check for $((
        if (
            self.pos + 2 >= self.length
            or self.source[self.pos + 1] != "("
            or self.source[self.pos + 2] != "("
        ):
            return None, ""

        self.advance()  # consume $
        self.advance()  # consume first (
        self.advance()  # consume second (

        # Find matching )) - need to track nested parens
        # Must be )) with no space between - ') )' is command sub + subshell
        content_start = self.pos
        depth = 1  # We're inside one level of (( already

        while not self.at_end() and depth > 0:
            c = self.peek()

            if c == "(":
                depth += 1
                self.advance()
            elif c == ")":
                # Check for ))
                if depth == 1 and self.pos + 1 < self.length and self.source[self.pos + 1] == ")":
                    # Found the closing ))
                    break
                depth -= 1
                if depth == 0:
                    # Closed with ) but next isn't ) - this is $( ( ... ) )
                    self.pos = start
                    return None, ""
                self.advance()
            else:
                self.advance()

        if self.at_end() or depth != 1:
            self.pos = start
            return None, ""

        content = self.source[content_start : self.pos]
        self.advance()  # consume first )
        self.advance()  # consume second )

        text = self.source[start : self.pos]

        # Parse the arithmetic expression
        expr = self._parse_arith_expr(content)
        return ArithmeticExpansion(expr), text

    # ========== Arithmetic expression parser ==========
    # Operator precedence (lowest to highest):
    # 1. comma (,)
    # 2. assignment (= += -= *= /= %= <<= >>= &= ^= |=)
    # 3. ternary (? :)
    # 4. logical or (||)
    # 5. logical and (&&)
    # 6. bitwise or (|)
    # 7. bitwise xor (^)
    # 8. bitwise and (&)
    # 9. equality (== !=)
    # 10. comparison (< > <= >=)
    # 11. shift (<< >>)
    # 12. addition (+ -)
    # 13. multiplication (* / %)
    # 14. exponentiation (**)
    # 15. unary (! ~ + - ++ --)
    # 16. postfix (++ -- [])

    def _parse_arith_expr(self, content: str) -> Node | None:
        """Parse an arithmetic expression string into AST nodes."""
        # Save any existing arith context (for nested parsing)
        saved_arith_src = getattr(self, "_arith_src", None)
        saved_arith_pos = getattr(self, "_arith_pos", None)
        saved_arith_len = getattr(self, "_arith_len", None)

        self._arith_src = content
        self._arith_pos = 0
        self._arith_len = len(content)
        self._arith_skip_ws()
        if self._arith_at_end():
            result = None
        else:
            result = self._arith_parse_comma()

        # Restore previous arith context
        if saved_arith_src is not None:
            self._arith_src = saved_arith_src
            self._arith_pos = saved_arith_pos
            self._arith_len = saved_arith_len

        return result

    def _arith_at_end(self) -> bool:
        return self._arith_pos >= self._arith_len

    def _arith_peek(self, offset: int = 0) -> str:
        pos = self._arith_pos + offset
        if pos >= self._arith_len:
            return ""
        return self._arith_src[pos]

    def _arith_advance(self) -> str:
        if self._arith_at_end():
            return ""
        c = self._arith_src[self._arith_pos]
        self._arith_pos += 1
        return c

    def _arith_skip_ws(self) -> None:
        while not self._arith_at_end():
            c = self._arith_src[self._arith_pos]
            if c in " \t\n":
                self._arith_pos += 1
            elif (
                c == "\\"
                and self._arith_pos + 1 < self._arith_len
                and self._arith_src[self._arith_pos + 1] == "\n"
            ):
                # Backslash-newline continuation
                self._arith_pos += 2
            else:
                break

    def _arith_match(self, s: str) -> bool:
        """Check if the next characters match s (without consuming)."""
        return self._arith_src[self._arith_pos : self._arith_pos + len(s)] == s

    def _arith_consume(self, s: str) -> bool:
        """If next chars match s, consume them and return True."""
        if self._arith_match(s):
            self._arith_pos += len(s)
            return True
        return False

    def _arith_parse_comma(self) -> Node:
        """Parse comma expressions (lowest precedence)."""
        left = self._arith_parse_assign()
        while True:
            self._arith_skip_ws()
            if self._arith_consume(","):
                self._arith_skip_ws()
                right = self._arith_parse_assign()
                left = ArithComma(left, right)
            else:
                break
        return left

    def _arith_parse_assign(self) -> Node:
        """Parse assignment expressions (right associative)."""
        left = self._arith_parse_ternary()
        self._arith_skip_ws()
        # Check for assignment operators
        assign_ops = ["<<=", ">>=", "+=", "-=", "*=", "/=", "%=", "&=", "^=", "|=", "="]
        for op in assign_ops:
            if self._arith_match(op):
                # Make sure it's not == or !=
                if op == "=" and self._arith_peek(1) == "=":
                    break
                self._arith_consume(op)
                self._arith_skip_ws()
                right = self._arith_parse_assign()  # right associative
                return ArithAssign(op, left, right)
        return left

    def _arith_parse_ternary(self) -> Node:
        """Parse ternary conditional (right associative)."""
        cond = self._arith_parse_logical_or()
        self._arith_skip_ws()
        if self._arith_consume("?"):
            self._arith_skip_ws()
            # True branch can be empty (e.g., 4 ? : $A - invalid at runtime, valid syntax)
            if self._arith_match(":"):
                if_true = None
            else:
                if_true = self._arith_parse_assign()
            self._arith_skip_ws()
            # Check for : (may be missing in malformed expressions like 1 ? 20)
            if self._arith_consume(":"):
                self._arith_skip_ws()
                # False branch can be empty (e.g., 4 ? 20 : - invalid at runtime)
                if self._arith_at_end() or self._arith_peek() == ")":
                    if_false = None
                else:
                    if_false = self._arith_parse_ternary()
            else:
                if_false = None
            return ArithTernary(cond, if_true, if_false)
        return cond

    def _arith_parse_logical_or(self) -> Node:
        """Parse logical or (||)."""
        left = self._arith_parse_logical_and()
        while True:
            self._arith_skip_ws()
            if self._arith_match("||"):
                self._arith_consume("||")
                self._arith_skip_ws()
                right = self._arith_parse_logical_and()
                left = ArithBinaryOp("||", left, right)
            else:
                break
        return left

    def _arith_parse_logical_and(self) -> Node:
        """Parse logical and (&&)."""
        left = self._arith_parse_bitwise_or()
        while True:
            self._arith_skip_ws()
            if self._arith_match("&&"):
                self._arith_consume("&&")
                self._arith_skip_ws()
                right = self._arith_parse_bitwise_or()
                left = ArithBinaryOp("&&", left, right)
            else:
                break
        return left

    def _arith_parse_bitwise_or(self) -> Node:
        """Parse bitwise or (|)."""
        left = self._arith_parse_bitwise_xor()
        while True:
            self._arith_skip_ws()
            # Make sure it's not || or |=
            if self._arith_peek() == "|" and self._arith_peek(1) not in "|=":
                self._arith_advance()
                self._arith_skip_ws()
                right = self._arith_parse_bitwise_xor()
                left = ArithBinaryOp("|", left, right)
            else:
                break
        return left

    def _arith_parse_bitwise_xor(self) -> Node:
        """Parse bitwise xor (^)."""
        left = self._arith_parse_bitwise_and()
        while True:
            self._arith_skip_ws()
            # Make sure it's not ^=
            if self._arith_peek() == "^" and self._arith_peek(1) != "=":
                self._arith_advance()
                self._arith_skip_ws()
                right = self._arith_parse_bitwise_and()
                left = ArithBinaryOp("^", left, right)
            else:
                break
        return left

    def _arith_parse_bitwise_and(self) -> Node:
        """Parse bitwise and (&)."""
        left = self._arith_parse_equality()
        while True:
            self._arith_skip_ws()
            # Make sure it's not && or &=
            if self._arith_peek() == "&" and self._arith_peek(1) not in "&=":
                self._arith_advance()
                self._arith_skip_ws()
                right = self._arith_parse_equality()
                left = ArithBinaryOp("&", left, right)
            else:
                break
        return left

    def _arith_parse_equality(self) -> Node:
        """Parse equality (== !=)."""
        left = self._arith_parse_comparison()
        while True:
            self._arith_skip_ws()
            if self._arith_match("=="):
                self._arith_consume("==")
                self._arith_skip_ws()
                right = self._arith_parse_comparison()
                left = ArithBinaryOp("==", left, right)
            elif self._arith_match("!="):
                self._arith_consume("!=")
                self._arith_skip_ws()
                right = self._arith_parse_comparison()
                left = ArithBinaryOp("!=", left, right)
            else:
                break
        return left

    def _arith_parse_comparison(self) -> Node:
        """Parse comparison (< > <= >=)."""
        left = self._arith_parse_shift()
        while True:
            self._arith_skip_ws()
            if self._arith_match("<="):
                self._arith_consume("<=")
                self._arith_skip_ws()
                right = self._arith_parse_shift()
                left = ArithBinaryOp("<=", left, right)
            elif self._arith_match(">="):
                self._arith_consume(">=")
                self._arith_skip_ws()
                right = self._arith_parse_shift()
                left = ArithBinaryOp(">=", left, right)
            elif self._arith_peek() == "<" and self._arith_peek(1) not in "<=":
                self._arith_advance()
                self._arith_skip_ws()
                right = self._arith_parse_shift()
                left = ArithBinaryOp("<", left, right)
            elif self._arith_peek() == ">" and self._arith_peek(1) not in ">=":
                self._arith_advance()
                self._arith_skip_ws()
                right = self._arith_parse_shift()
                left = ArithBinaryOp(">", left, right)
            else:
                break
        return left

    def _arith_parse_shift(self) -> Node:
        """Parse shift (<< >>)."""
        left = self._arith_parse_additive()
        while True:
            self._arith_skip_ws()
            if self._arith_match("<<="):
                break  # assignment, not shift
            if self._arith_match(">>="):
                break  # assignment, not shift
            if self._arith_match("<<"):
                self._arith_consume("<<")
                self._arith_skip_ws()
                right = self._arith_parse_additive()
                left = ArithBinaryOp("<<", left, right)
            elif self._arith_match(">>"):
                self._arith_consume(">>")
                self._arith_skip_ws()
                right = self._arith_parse_additive()
                left = ArithBinaryOp(">>", left, right)
            else:
                break
        return left

    def _arith_parse_additive(self) -> Node:
        """Parse addition and subtraction (+ -)."""
        left = self._arith_parse_multiplicative()
        while True:
            self._arith_skip_ws()
            c = self._arith_peek()
            c2 = self._arith_peek(1)
            if c == "+" and c2 not in "+=":
                self._arith_advance()
                self._arith_skip_ws()
                right = self._arith_parse_multiplicative()
                left = ArithBinaryOp("+", left, right)
            elif c == "-" and c2 not in "-=":
                self._arith_advance()
                self._arith_skip_ws()
                right = self._arith_parse_multiplicative()
                left = ArithBinaryOp("-", left, right)
            else:
                break
        return left

    def _arith_parse_multiplicative(self) -> Node:
        """Parse multiplication, division, modulo (* / %)."""
        left = self._arith_parse_exponentiation()
        while True:
            self._arith_skip_ws()
            c = self._arith_peek()
            c2 = self._arith_peek(1)
            if c == "*" and c2 not in "*=":
                self._arith_advance()
                self._arith_skip_ws()
                right = self._arith_parse_exponentiation()
                left = ArithBinaryOp("*", left, right)
            elif c == "/" and c2 != "=":
                self._arith_advance()
                self._arith_skip_ws()
                right = self._arith_parse_exponentiation()
                left = ArithBinaryOp("/", left, right)
            elif c == "%" and c2 != "=":
                self._arith_advance()
                self._arith_skip_ws()
                right = self._arith_parse_exponentiation()
                left = ArithBinaryOp("%", left, right)
            else:
                break
        return left

    def _arith_parse_exponentiation(self) -> Node:
        """Parse exponentiation (**) - right associative."""
        left = self._arith_parse_unary()
        self._arith_skip_ws()
        if self._arith_match("**"):
            self._arith_consume("**")
            self._arith_skip_ws()
            right = self._arith_parse_exponentiation()  # right associative
            return ArithBinaryOp("**", left, right)
        return left

    def _arith_parse_unary(self) -> Node:
        """Parse unary operators (! ~ + - ++ --)."""
        self._arith_skip_ws()
        # Pre-increment/decrement
        if self._arith_match("++"):
            self._arith_consume("++")
            self._arith_skip_ws()
            operand = self._arith_parse_unary()
            return ArithPreIncr(operand)
        if self._arith_match("--"):
            self._arith_consume("--")
            self._arith_skip_ws()
            operand = self._arith_parse_unary()
            return ArithPreDecr(operand)
        # Unary operators
        c = self._arith_peek()
        if c == "!":
            self._arith_advance()
            self._arith_skip_ws()
            operand = self._arith_parse_unary()
            return ArithUnaryOp("!", operand)
        if c == "~":
            self._arith_advance()
            self._arith_skip_ws()
            operand = self._arith_parse_unary()
            return ArithUnaryOp("~", operand)
        if c == "+" and self._arith_peek(1) != "+":
            self._arith_advance()
            self._arith_skip_ws()
            operand = self._arith_parse_unary()
            return ArithUnaryOp("+", operand)
        if c == "-" and self._arith_peek(1) != "-":
            self._arith_advance()
            self._arith_skip_ws()
            operand = self._arith_parse_unary()
            return ArithUnaryOp("-", operand)
        return self._arith_parse_postfix()

    def _arith_parse_postfix(self) -> Node:
        """Parse postfix operators (++ -- [])."""
        left = self._arith_parse_primary()
        while True:
            self._arith_skip_ws()
            if self._arith_match("++"):
                self._arith_consume("++")
                left = ArithPostIncr(left)
            elif self._arith_match("--"):
                self._arith_consume("--")
                left = ArithPostDecr(left)
            elif self._arith_peek() == "[":
                # Array subscript - but only for variables
                if isinstance(left, ArithVar):
                    self._arith_advance()  # consume [
                    self._arith_skip_ws()
                    index = self._arith_parse_comma()
                    self._arith_skip_ws()
                    if not self._arith_consume("]"):
                        raise ParseError("Expected ']' in array subscript", pos=self._arith_pos)
                    left = ArithSubscript(left.name, index)
                else:
                    break
            else:
                break
        return left

    def _arith_parse_primary(self) -> Node:
        """Parse primary expressions (numbers, variables, parens, expansions)."""
        self._arith_skip_ws()
        c = self._arith_peek()

        # Parenthesized expression
        if c == "(":
            self._arith_advance()
            self._arith_skip_ws()
            expr = self._arith_parse_comma()
            self._arith_skip_ws()
            if not self._arith_consume(")"):
                raise ParseError("Expected ')' in arithmetic expression", pos=self._arith_pos)
            return expr

        # Parameter expansion ${...} or $var or $(...)
        if c == "$":
            return self._arith_parse_expansion()

        # Single-quoted string - content becomes the number
        if c == "'":
            return self._arith_parse_single_quote()

        # Double-quoted string - may contain expansions
        if c == '"':
            return self._arith_parse_double_quote()

        # Backtick command substitution
        if c == "`":
            return self._arith_parse_backtick()

        # Escape sequence \X (not line continuation, which is handled in _arith_skip_ws)
        # Escape covers only the single character after backslash
        if c == "\\":
            self._arith_advance()  # consume backslash
            if self._arith_at_end():
                raise ParseError(
                    "Unexpected end after backslash in arithmetic", pos=self._arith_pos
                )
            escaped_char = self._arith_advance()  # consume escaped character
            return ArithEscape(escaped_char)

        # Number or variable
        return self._arith_parse_number_or_var()

    def _arith_parse_expansion(self) -> Node:
        """Parse $var, ${...}, or $(...)."""
        if not self._arith_consume("$"):
            raise ParseError("Expected '$'", pos=self._arith_pos)

        c = self._arith_peek()

        # Command substitution $(...)
        if c == "(":
            return self._arith_parse_cmdsub()

        # Braced parameter ${...}
        if c == "{":
            return self._arith_parse_braced_param()

        # Simple $var
        name_chars = []
        while not self._arith_at_end():
            ch = self._arith_peek()
            if ch.isalnum() or ch == "_":
                name_chars.append(self._arith_advance())
            elif ch in "#?@*!$-0123456789" and not name_chars:
                # Special parameters
                name_chars.append(self._arith_advance())
                break
            else:
                break
        if not name_chars:
            raise ParseError("Expected variable name after $", pos=self._arith_pos)
        return ParamExpansion("".join(name_chars))

    def _arith_parse_cmdsub(self) -> Node:
        """Parse $(...) command substitution inside arithmetic."""
        # We're positioned after $, at (
        self._arith_advance()  # consume (

        # Check for $(( which is nested arithmetic
        if self._arith_peek() == "(":
            self._arith_advance()  # consume second (
            depth = 1
            content_start = self._arith_pos
            while not self._arith_at_end() and depth > 0:
                ch = self._arith_peek()
                if ch == "(":
                    depth += 1
                    self._arith_advance()
                elif ch == ")":
                    if depth == 1 and self._arith_peek(1) == ")":
                        break
                    depth -= 1
                    self._arith_advance()
                else:
                    self._arith_advance()
            content = self._arith_src[content_start : self._arith_pos]
            self._arith_advance()  # consume first )
            self._arith_advance()  # consume second )
            inner_expr = self._parse_arith_expr(content)
            return ArithmeticExpansion(inner_expr)

        # Regular command substitution
        depth = 1
        content_start = self._arith_pos
        while not self._arith_at_end() and depth > 0:
            ch = self._arith_peek()
            if ch == "(":
                depth += 1
                self._arith_advance()
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    break
                self._arith_advance()
            else:
                self._arith_advance()
        content = self._arith_src[content_start : self._arith_pos]
        self._arith_advance()  # consume )

        # Parse the command inside
        saved_pos = self.pos
        saved_src = self.source
        saved_len = self.length
        self.source = content
        self.pos = 0
        self.length = len(content)
        cmd = self.parse_list()
        self.source = saved_src
        self.pos = saved_pos
        self.length = saved_len

        return CommandSubstitution(cmd)

    def _arith_parse_braced_param(self) -> Node:
        """Parse ${...} parameter expansion inside arithmetic."""
        self._arith_advance()  # consume {

        # Handle indirect ${!var}
        if self._arith_peek() == "!":
            self._arith_advance()
            name_chars = []
            while not self._arith_at_end() and self._arith_peek() != "}":
                name_chars.append(self._arith_advance())
            self._arith_consume("}")
            return ParamIndirect("".join(name_chars))

        # Handle length ${#var}
        if self._arith_peek() == "#":
            self._arith_advance()
            name_chars = []
            while not self._arith_at_end() and self._arith_peek() != "}":
                name_chars.append(self._arith_advance())
            self._arith_consume("}")
            return ParamLength("".join(name_chars))

        # Regular ${var} or ${var...}
        name_chars = []
        while not self._arith_at_end():
            ch = self._arith_peek()
            if ch == "}":
                self._arith_advance()
                return ParamExpansion("".join(name_chars))
            if ch in ":-=+?#%/^,@*[":
                # Operator follows
                break
            name_chars.append(self._arith_advance())

        name = "".join(name_chars)

        # Check for operator
        op_chars = []
        depth = 1
        while not self._arith_at_end() and depth > 0:
            ch = self._arith_peek()
            if ch == "{":
                depth += 1
                op_chars.append(self._arith_advance())
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    break
                op_chars.append(self._arith_advance())
            else:
                op_chars.append(self._arith_advance())
        self._arith_consume("}")
        op_str = "".join(op_chars)

        # Parse the operator
        if op_str.startswith(":-"):
            return ParamExpansion(name, ":-", op_str[2:])
        if op_str.startswith(":="):
            return ParamExpansion(name, ":=", op_str[2:])
        if op_str.startswith(":+"):
            return ParamExpansion(name, ":+", op_str[2:])
        if op_str.startswith(":?"):
            return ParamExpansion(name, ":?", op_str[2:])
        if op_str.startswith(":"):
            return ParamExpansion(name, ":", op_str[1:])
        if op_str.startswith("##"):
            return ParamExpansion(name, "##", op_str[2:])
        if op_str.startswith("#"):
            return ParamExpansion(name, "#", op_str[1:])
        if op_str.startswith("%%"):
            return ParamExpansion(name, "%%", op_str[2:])
        if op_str.startswith("%"):
            return ParamExpansion(name, "%", op_str[1:])
        if op_str.startswith("//"):
            return ParamExpansion(name, "//", op_str[2:])
        if op_str.startswith("/"):
            return ParamExpansion(name, "/", op_str[1:])
        return ParamExpansion(name, "", op_str)

    def _arith_parse_single_quote(self) -> Node:
        """Parse '...' inside arithmetic - returns content as a number/string."""
        self._arith_advance()  # consume opening '
        content_start = self._arith_pos
        while not self._arith_at_end() and self._arith_peek() != "'":
            self._arith_advance()
        content = self._arith_src[content_start : self._arith_pos]
        if not self._arith_consume("'"):
            raise ParseError("Unterminated single quote in arithmetic", pos=self._arith_pos)
        return ArithNumber(content)

    def _arith_parse_double_quote(self) -> Node:
        """Parse "..." inside arithmetic - may contain expansions."""
        self._arith_advance()  # consume opening "
        content_start = self._arith_pos
        while not self._arith_at_end() and self._arith_peek() != '"':
            c = self._arith_peek()
            if c == "\\" and not self._arith_at_end():
                self._arith_advance()  # skip backslash
                self._arith_advance()  # skip escaped char
            else:
                self._arith_advance()
        content = self._arith_src[content_start : self._arith_pos]
        if not self._arith_consume('"'):
            raise ParseError("Unterminated double quote in arithmetic", pos=self._arith_pos)
        return ArithNumber(content)

    def _arith_parse_backtick(self) -> Node:
        """Parse `...` command substitution inside arithmetic."""
        self._arith_advance()  # consume opening `
        content_start = self._arith_pos
        while not self._arith_at_end() and self._arith_peek() != "`":
            c = self._arith_peek()
            if c == "\\" and not self._arith_at_end():
                self._arith_advance()  # skip backslash
                self._arith_advance()  # skip escaped char
            else:
                self._arith_advance()
        content = self._arith_src[content_start : self._arith_pos]
        if not self._arith_consume("`"):
            raise ParseError("Unterminated backtick in arithmetic", pos=self._arith_pos)
        # Parse the command inside
        saved_pos = self.pos
        saved_src = self.source
        saved_len = self.length
        self.source = content
        self.pos = 0
        self.length = len(content)
        cmd = self.parse_list()
        self.source = saved_src
        self.pos = saved_pos
        self.length = saved_len
        return CommandSubstitution(cmd)

    def _arith_parse_number_or_var(self) -> Node:
        """Parse a number or variable name."""
        self._arith_skip_ws()
        chars = []
        c = self._arith_peek()

        # Check for number (starts with digit or base#)
        if c.isdigit():
            # Could be decimal, hex (0x), octal (0), or base#n
            while not self._arith_at_end():
                ch = self._arith_peek()
                if ch.isalnum() or ch in "#_":
                    chars.append(self._arith_advance())
                else:
                    break
            return ArithNumber("".join(chars))

        # Variable name (starts with letter or _)
        if c.isalpha() or c == "_":
            while not self._arith_at_end():
                ch = self._arith_peek()
                if ch.isalnum() or ch == "_":
                    chars.append(self._arith_advance())
                else:
                    break
            return ArithVar("".join(chars))

        raise ParseError(
            f"Unexpected character '{c}' in arithmetic expression", pos=self._arith_pos
        )

    def _parse_deprecated_arithmetic(self) -> tuple[Node | None, str]:
        """Parse a deprecated $[expr] arithmetic expansion.

        Returns (node, text) where node is ArithDeprecated and text is raw text.
        """
        if self.at_end() or self.peek() != "$":
            return None, ""

        start = self.pos

        # Check for $[
        if self.pos + 1 >= self.length or self.source[self.pos + 1] != "[":
            return None, ""

        self.advance()  # consume $
        self.advance()  # consume [

        # Find matching ] - need to track nested brackets
        content_start = self.pos
        depth = 1

        while not self.at_end() and depth > 0:
            c = self.peek()

            if c == "[":
                depth += 1
                self.advance()
            elif c == "]":
                depth -= 1
                if depth == 0:
                    break
                self.advance()
            else:
                self.advance()

        if self.at_end() or depth != 0:
            self.pos = start
            return None, ""

        content = self.source[content_start : self.pos]
        self.advance()  # consume ]

        text = self.source[start : self.pos]
        return ArithDeprecated(content), text

    def _parse_ansi_c_quote(self) -> tuple[Node | None, str]:
        """Parse ANSI-C quoting $'...'.

        Returns (node, text) where node is the AST node and text is the raw text.
        Returns (None, "") if not a valid ANSI-C quote.
        """
        if self.at_end() or self.peek() != "$":
            return None, ""
        if self.pos + 1 >= self.length or self.source[self.pos + 1] != "'":
            return None, ""

        start = self.pos
        self.advance()  # consume $
        self.advance()  # consume opening '

        content_chars = []
        while not self.at_end():
            ch = self.peek()
            if ch == "'":
                self.advance()  # consume closing '
                break
            elif ch == "\\":
                # Escape sequence - include both backslash and following char in content
                content_chars.append(self.advance())  # backslash
                if not self.at_end():
                    content_chars.append(self.advance())  # escaped char
            else:
                content_chars.append(self.advance())
        else:
            # Unterminated - reset and return None
            self.pos = start
            return None, ""

        text = self.source[start : self.pos]
        content = "".join(content_chars)
        return AnsiCQuote(content), text

    def _parse_locale_string(self) -> tuple[Node | None, str, list[Node]]:
        """Parse locale translation $"...".

        Returns (node, text, inner_parts) where:
        - node is the LocaleString AST node
        - text is the raw text including $"..."
        - inner_parts is a list of expansion nodes found inside
        Returns (None, "", []) if not a valid locale string.
        """
        if self.at_end() or self.peek() != "$":
            return None, "", []
        if self.pos + 1 >= self.length or self.source[self.pos + 1] != '"':
            return None, "", []

        start = self.pos
        self.advance()  # consume $
        self.advance()  # consume opening "

        content_chars = []
        inner_parts = []

        while not self.at_end():
            ch = self.peek()
            if ch == '"':
                self.advance()  # consume closing "
                break
            elif ch == "\\" and self.pos + 1 < self.length:
                # Escape sequence (line continuation removes both)
                next_ch = self.source[self.pos + 1]
                if next_ch == "\n":
                    # Line continuation - skip both backslash and newline
                    self.advance()
                    self.advance()
                else:
                    content_chars.append(self.advance())  # backslash
                    content_chars.append(self.advance())  # escaped char
            # Handle arithmetic expansion $((...))
            elif (
                ch == "$"
                and self.pos + 2 < self.length
                and self.source[self.pos + 1] == "("
                and self.source[self.pos + 2] == "("
            ):
                arith_node, arith_text = self._parse_arithmetic_expansion()
                if arith_node:
                    inner_parts.append(arith_node)
                    content_chars.append(arith_text)
                else:
                    # Not arithmetic - try command substitution
                    cmdsub_node, cmdsub_text = self._parse_command_substitution()
                    if cmdsub_node:
                        inner_parts.append(cmdsub_node)
                        content_chars.append(cmdsub_text)
                    else:
                        content_chars.append(self.advance())
            # Handle command substitution $(...)
            elif ch == "$" and self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
                cmdsub_node, cmdsub_text = self._parse_command_substitution()
                if cmdsub_node:
                    inner_parts.append(cmdsub_node)
                    content_chars.append(cmdsub_text)
                else:
                    content_chars.append(self.advance())
            # Handle parameter expansion
            elif ch == "$":
                param_node, param_text = self._parse_param_expansion()
                if param_node:
                    inner_parts.append(param_node)
                    content_chars.append(param_text)
                else:
                    content_chars.append(self.advance())
            # Handle backtick command substitution
            elif ch == "`":
                cmdsub_node, cmdsub_text = self._parse_backtick_substitution()
                if cmdsub_node:
                    inner_parts.append(cmdsub_node)
                    content_chars.append(cmdsub_text)
                else:
                    content_chars.append(self.advance())
            else:
                content_chars.append(self.advance())
        else:
            # Unterminated - reset and return None
            self.pos = start
            return None, "", []

        content = "".join(content_chars)
        # Reconstruct text from parsed content (handles line continuation removal)
        text = '$"' + content + '"'
        return LocaleString(content), text, inner_parts

    def _parse_param_expansion(self) -> tuple[Node | None, str]:
        """Parse a parameter expansion starting at $.

        Returns (node, text) where node is the AST node and text is the raw text.
        Returns (None, "") if not a valid parameter expansion.
        """
        if self.at_end() or self.peek() != "$":
            return None, ""

        start = self.pos
        self.advance()  # consume $

        if self.at_end():
            self.pos = start
            return None, ""

        ch = self.peek()

        # Braced expansion ${...}
        if ch == "{":
            self.advance()  # consume {
            return self._parse_braced_param(start)

        # Simple expansion $var or $special
        # Special parameters: ?$!#@*-0-9
        if ch in "?$!#@*-0123456789":
            self.advance()
            text = self.source[start : self.pos]
            return ParamExpansion(ch), text

        # Variable name [a-zA-Z_][a-zA-Z0-9_]*
        if ch.isalpha() or ch == "_":
            name_start = self.pos
            while not self.at_end():
                c = self.peek()
                if c.isalnum() or c == "_":
                    self.advance()
                else:
                    break
            name = self.source[name_start : self.pos]
            text = self.source[start : self.pos]
            return ParamExpansion(name), text

        # Not a valid expansion, restore position
        self.pos = start
        return None, ""

    def _parse_braced_param(self, start: int) -> tuple[Node | None, str]:
        """Parse contents of ${...} after the opening brace.

        start is the position of the $.
        Returns (node, text).
        """
        if self.at_end():
            self.pos = start
            return None, ""

        ch = self.peek()

        # ${#param} - length
        if ch == "#":
            self.advance()
            param = self._consume_param_name()
            if param and not self.at_end() and self.peek() == "}":
                self.advance()
                text = self.source[start : self.pos]
                return ParamLength(param), text
            self.pos = start
            return None, ""

        # ${!param} or ${!param<op><arg>} - indirect
        if ch == "!":
            self.advance()
            param = self._consume_param_name()
            if param:
                # Skip optional whitespace before closing brace
                while not self.at_end() and self.peek() in " \t":
                    self.advance()
                if not self.at_end() and self.peek() == "}":
                    self.advance()
                    text = self.source[start : self.pos]
                    return ParamIndirect(param), text
                # ${!prefix@} and ${!prefix*} are prefix matching (lists variable names)
                # These are NOT operators - the @/* is part of the indirect form
                if not self.at_end() and self.peek() in "@*":
                    suffix = self.advance()
                    while not self.at_end() and self.peek() in " \t":
                        self.advance()
                    if not self.at_end() and self.peek() == "}":
                        self.advance()
                        text = self.source[start : self.pos]
                        return ParamIndirect(param + suffix), text
                    # Not a valid prefix match, reset
                    self.pos = start
                    return None, ""
                # Check for operator (e.g., ${!##} = indirect of # with # op)
                op = self._consume_param_operator()
                if op is not None:
                    # Parse argument until closing brace
                    arg_chars = []
                    depth = 1
                    while not self.at_end() and depth > 0:
                        c = self.peek()
                        if (
                            c == "$"
                            and self.pos + 1 < self.length
                            and self.source[self.pos + 1] == "{"
                        ):
                            depth += 1
                            arg_chars.append(self.advance())
                            arg_chars.append(self.advance())
                        elif c == "}":
                            depth -= 1
                            if depth > 0:
                                arg_chars.append(self.advance())
                        elif c == "\\":
                            arg_chars.append(self.advance())
                            if not self.at_end():
                                arg_chars.append(self.advance())
                        else:
                            arg_chars.append(self.advance())
                    if depth == 0:
                        self.advance()  # consume final }
                        arg = "".join(arg_chars)
                        text = self.source[start : self.pos]
                        return ParamIndirect(param, op, arg), text
            self.pos = start
            return None, ""

        # ${param} or ${param<op><arg>}
        param = self._consume_param_name()
        if not param:
            # Unknown syntax like ${(M)...} (zsh) - consume until matching }
            # Bash accepts these syntactically but fails at runtime
            depth = 1
            content_start = self.pos
            while not self.at_end() and depth > 0:
                c = self.peek()
                if c == "{":
                    depth += 1
                    self.advance()
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        break
                    self.advance()
                elif c == "\\":
                    self.advance()
                    if not self.at_end():
                        self.advance()
                else:
                    self.advance()
            if depth == 0:
                content = self.source[content_start : self.pos]
                self.advance()  # consume final }
                text = self.source[start : self.pos]
                return ParamExpansion(content), text
            self.pos = start
            return None, ""

        if self.at_end():
            self.pos = start
            return None, ""

        # Check for closing brace (simple expansion)
        if self.peek() == "}":
            self.advance()
            text = self.source[start : self.pos]
            return ParamExpansion(param), text

        # Parse operator
        op = self._consume_param_operator()
        if op is None:
            # Unknown operator - bash still parses these (fails at runtime)
            # Treat the current char as the operator
            op = self.advance()

        # Parse argument (everything until closing brace)
        # Track quote state and nesting
        arg_chars = []
        depth = 1
        in_single_quote = False
        in_double_quote = False
        while not self.at_end() and depth > 0:
            c = self.peek()
            # Single quotes - no escapes, just scan to closing quote
            if c == "'" and not in_double_quote:
                if in_single_quote:
                    in_single_quote = False
                else:
                    in_single_quote = True
                arg_chars.append(self.advance())
            # Double quotes - toggle state
            elif c == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
                arg_chars.append(self.advance())
            # Escape - skip next char (line continuation removes both)
            elif c == "\\" and not in_single_quote:
                if self.pos + 1 < self.length and self.source[self.pos + 1] == "\n":
                    # Line continuation - skip both backslash and newline
                    self.advance()
                    self.advance()
                else:
                    arg_chars.append(self.advance())
                    if not self.at_end():
                        arg_chars.append(self.advance())
            # Nested ${...} - increase depth (outside single quotes)
            elif (
                c == "$"
                and not in_single_quote
                and self.pos + 1 < self.length
                and self.source[self.pos + 1] == "{"
            ):
                depth += 1
                arg_chars.append(self.advance())  # $
                arg_chars.append(self.advance())  # {
            # Command substitution $(...) - scan to matching )
            elif (
                c == "$"
                and not in_single_quote
                and self.pos + 1 < self.length
                and self.source[self.pos + 1] == "("
            ):
                arg_chars.append(self.advance())  # $
                arg_chars.append(self.advance())  # (
                paren_depth = 1
                while not self.at_end() and paren_depth > 0:
                    pc = self.peek()
                    if pc == "(":
                        paren_depth += 1
                    elif pc == ")":
                        paren_depth -= 1
                    elif pc == "\\":
                        arg_chars.append(self.advance())
                        if not self.at_end():
                            arg_chars.append(self.advance())
                        continue
                    arg_chars.append(self.advance())
            # Backtick command substitution - scan to matching `
            elif c == "`" and not in_single_quote:
                arg_chars.append(self.advance())  # opening `
                while not self.at_end() and self.peek() != "`":
                    bc = self.peek()
                    if bc == "\\" and self.pos + 1 < self.length:
                        next_c = self.source[self.pos + 1]
                        if next_c in "$`\\":
                            arg_chars.append(self.advance())  # backslash
                    arg_chars.append(self.advance())
                if not self.at_end():
                    arg_chars.append(self.advance())  # closing `
            # Closing brace - handle depth for nested ${...}
            elif c == "}":
                if in_single_quote:
                    # Inside single quotes, } is literal
                    arg_chars.append(self.advance())
                elif in_double_quote:
                    # Inside double quotes, } can close nested ${...}
                    if depth > 1:
                        depth -= 1
                        arg_chars.append(self.advance())
                    else:
                        # Literal } in double quotes (not closing nested)
                        arg_chars.append(self.advance())
                else:
                    depth -= 1
                    if depth > 0:
                        arg_chars.append(self.advance())
            else:
                arg_chars.append(self.advance())

        if depth != 0:
            self.pos = start
            return None, ""

        self.advance()  # consume final }
        arg = "".join(arg_chars)
        # Reconstruct text from parsed components (handles line continuation removal)
        text = "${" + param + op + arg + "}"
        return ParamExpansion(param, op, arg), text

    def _consume_param_name(self) -> str | None:
        """Consume a parameter name (variable name, special char, or array subscript)."""
        if self.at_end():
            return None

        ch = self.peek()

        # Special parameters
        if ch in "?$!#@*-":
            self.advance()
            return ch

        # Digits (positional params)
        if ch.isdigit():
            name_chars = []
            while not self.at_end() and self.peek().isdigit():
                name_chars.append(self.advance())
            return "".join(name_chars)

        # Variable name
        if ch.isalpha() or ch == "_":
            name_chars = []
            while not self.at_end():
                c = self.peek()
                if c.isalnum() or c == "_":
                    name_chars.append(self.advance())
                elif c == "[":
                    # Array subscript - track bracket depth
                    name_chars.append(self.advance())
                    bracket_depth = 1
                    while not self.at_end() and bracket_depth > 0:
                        sc = self.peek()
                        if sc == "[":
                            bracket_depth += 1
                        elif sc == "]":
                            bracket_depth -= 1
                            if bracket_depth == 0:
                                break
                        name_chars.append(self.advance())
                    if not self.at_end() and self.peek() == "]":
                        name_chars.append(self.advance())
                    break
                else:
                    break
            return "".join(name_chars) if name_chars else None

        return None

    def _consume_param_operator(self) -> str | None:
        """Consume a parameter expansion operator."""
        if self.at_end():
            return None

        ch = self.peek()

        # Operators with optional colon prefix: :- := :? :+
        if ch == ":":
            self.advance()
            if self.at_end():
                return ":"
            next_ch = self.peek()
            if next_ch in "-=?+":
                self.advance()
                return ":" + next_ch
            # Just : (substring)
            return ":"

        # Operators without colon: - = ? +
        if ch in "-=?+":
            self.advance()
            return ch

        # Pattern removal: # ## % %%
        if ch == "#":
            self.advance()
            if not self.at_end() and self.peek() == "#":
                self.advance()
                return "##"
            return "#"

        if ch == "%":
            self.advance()
            if not self.at_end() and self.peek() == "%":
                self.advance()
                return "%%"
            return "%"

        # Substitution: / // /# /%
        if ch == "/":
            self.advance()
            if not self.at_end():
                next_ch = self.peek()
                if next_ch == "/":
                    self.advance()
                    return "//"
                elif next_ch == "#":
                    self.advance()
                    return "/#"
                elif next_ch == "%":
                    self.advance()
                    return "/%"
            return "/"

        # Case modification: ^ ^^ , ,,
        if ch == "^":
            self.advance()
            if not self.at_end() and self.peek() == "^":
                self.advance()
                return "^^"
            return "^"

        if ch == ",":
            self.advance()
            if not self.at_end() and self.peek() == ",":
                self.advance()
                return ",,"
            return ","

        # Transformation: @
        if ch == "@":
            self.advance()
            return "@"

        return None

    def parse_redirect(self) -> Redirect | HereDoc | None:
        """Parse a redirection operator and target."""
        self.skip_whitespace()
        if self.at_end():
            return None

        start = self.pos
        fd = None
        varfd = None  # Variable fd like {fd}

        # Check for variable fd {varname} or {varname[subscript]} before redirect
        if self.peek() == "{":
            saved = self.pos
            self.advance()  # consume {
            varname_chars = []
            while not self.at_end() and self.peek() not in "}<>":
                ch = self.peek()
                if ch.isalnum() or ch in "_[]":
                    varname_chars.append(self.advance())
                else:
                    break
            if not self.at_end() and self.peek() == "}" and varname_chars:
                self.advance()  # consume }
                varfd = "".join(varname_chars)
            else:
                # Not a valid variable fd, restore
                self.pos = saved

        # Check for optional fd number before redirect (if no varfd)
        if varfd is None and self.peek() and self.peek().isdigit():
            fd_chars = []
            while not self.at_end() and self.peek().isdigit():
                fd_chars.append(self.advance())
            fd = int("".join(fd_chars))

        ch = self.peek()

        # Handle &> and &>> (redirect both stdout and stderr)
        # Note: &> does NOT take a preceding fd number. If we consumed digits,
        # they should be a separate word, not an fd. E.g., "2&>1" is command "2"
        # with redirect "&> 1", not fd 2 redirected.
        if ch == "&" and self.pos + 1 < self.length and self.source[self.pos + 1] == ">":
            if fd is not None:
                # We consumed digits that should be a word, not an fd
                # Restore position and let parse_word handle them
                self.pos = start
                return None
            self.advance()  # consume &
            self.advance()  # consume >
            if not self.at_end() and self.peek() == ">":
                self.advance()  # consume second > for &>>
                op = "&>>"
            else:
                op = "&>"
            self.skip_whitespace()
            target = self.parse_word()
            if target is None:
                raise ParseError(f"Expected target for redirect {op}", pos=self.pos)
            return Redirect(op, target)

        if ch is None or ch not in "<>":
            # Not a redirect, restore position
            self.pos = start
            return None

        # Check for process substitution <(...) or >(...) - not a redirect
        # Only treat as redirect if there's a space before ( or an fd number
        if fd is None and self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
            # This is a process substitution, not a redirect
            self.pos = start
            return None

        # Parse the redirect operator
        op = self.advance()

        # Check for multi-char operators
        strip_tabs = False
        if not self.at_end():
            next_ch = self.peek()
            if op == ">" and next_ch == ">":
                self.advance()
                op = ">>"
            elif op == "<" and next_ch == "<":
                self.advance()
                if not self.at_end() and self.peek() == "<":
                    self.advance()
                    op = "<<<"
                elif not self.at_end() and self.peek() == "-":
                    self.advance()
                    op = "<<"
                    strip_tabs = True
                else:
                    op = "<<"
            # Handle <> (read-write)
            elif op == "<" and next_ch == ">":
                self.advance()
                op = "<>"
            # Handle >| (noclobber override)
            elif op == ">" and next_ch == "|":
                self.advance()
                op = ">|"
            # Only consume >& or <& as operators if NOT followed by a digit or -
            # (>&2 should be > with target &2, not >& with target 2)
            # (>&- should be > with target &-, not >& with target -)
            elif fd is None and varfd is None and op == ">" and next_ch == "&":
                # Peek ahead to see if there's a digit or - after &
                if self.pos + 1 >= self.length or self.source[self.pos + 1] not in "0123456789-":
                    self.advance()
                    op = ">&"
            elif fd is None and varfd is None and op == "<" and next_ch == "&":
                if self.pos + 1 >= self.length or self.source[self.pos + 1] not in "0123456789-":
                    self.advance()
                    op = "<&"

        # Handle here document
        if op == "<<":
            return self._parse_heredoc(fd, strip_tabs)

        # Combine fd or varfd with operator if present
        if varfd is not None:
            op = f"{{{varfd}}}{op}"
        elif fd is not None:
            op = f"{fd}{op}"

        self.skip_whitespace()

        # Handle fd duplication targets like &1, &2, &-, &10-, &$var
        if not self.at_end() and self.peek() == "&":
            self.advance()  # consume &
            # Parse the fd number or - for close, including move syntax like &10-
            if not self.at_end() and (self.peek().isdigit() or self.peek() == "-"):
                fd_chars = []
                while not self.at_end() and self.peek().isdigit():
                    fd_chars.append(self.advance())
                fd_target = "".join(fd_chars) if fd_chars else ""
                # Handle just - for close, or N- for move syntax
                if not self.at_end() and self.peek() == "-":
                    fd_target += self.advance()  # consume the trailing -
                target = Word(f"&{fd_target}")
            else:
                # Could be &$var or &word - parse word and prepend &
                inner_word = self.parse_word()
                if inner_word is not None:
                    target = Word(f"&{inner_word.value}")
                    target.parts = inner_word.parts
                else:
                    raise ParseError(f"Expected target for redirect {op}", pos=self.pos)
        else:
            target = self.parse_word()

        if target is None:
            raise ParseError(f"Expected target for redirect {op}", pos=self.pos)

        return Redirect(op, target)

    def _parse_heredoc(self, fd: int | None, strip_tabs: bool) -> HereDoc:
        """Parse a here document <<DELIM ... DELIM."""
        self.skip_whitespace()

        # Parse the delimiter, handling quoting (can be mixed like 'EOF'"2")
        quoted = False
        delimiter_chars = []

        while not self.at_end() and self.peek() not in " \t\n;|&<>()":
            ch = self.peek()
            if ch == '"':
                quoted = True
                self.advance()
                while not self.at_end() and self.peek() != '"':
                    delimiter_chars.append(self.advance())
                if not self.at_end():
                    self.advance()
            elif ch == "'":
                quoted = True
                self.advance()
                while not self.at_end() and self.peek() != "'":
                    delimiter_chars.append(self.advance())
                if not self.at_end():
                    self.advance()
            elif ch == "\\":
                self.advance()
                if not self.at_end():
                    next_ch = self.peek()
                    if next_ch == "\n":
                        # Backslash-newline: continue delimiter on next line
                        self.advance()  # skip the newline
                    else:
                        # Regular escape - quotes the next char
                        quoted = True
                        delimiter_chars.append(self.advance())
            elif ch == "$" and self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
                # Command substitution embedded in delimiter
                delimiter_chars.append(self.advance())  # $
                delimiter_chars.append(self.advance())  # (
                depth = 1
                while not self.at_end() and depth > 0:
                    c = self.peek()
                    if c == "(":
                        depth += 1
                    elif c == ")":
                        depth -= 1
                    delimiter_chars.append(self.advance())
            else:
                delimiter_chars.append(self.advance())

        delimiter = "".join(delimiter_chars)

        # Find the end of the current line (command continues until newline)
        # We need to mark where the heredoc content starts
        # Must be quote-aware - newlines inside quoted strings don't end the line
        line_end = self.pos
        while line_end < self.length and self.source[line_end] != "\n":
            ch = self.source[line_end]
            if ch == "'":
                # Single-quoted string - skip to closing quote (no escapes)
                line_end += 1
                while line_end < self.length and self.source[line_end] != "'":
                    line_end += 1
            elif ch == '"':
                # Double-quoted string - skip to closing quote (with escapes)
                line_end += 1
                while line_end < self.length and self.source[line_end] != '"':
                    if self.source[line_end] == "\\" and line_end + 1 < self.length:
                        line_end += 2
                    else:
                        line_end += 1
            elif ch == "\\" and line_end + 1 < self.length:
                # Backslash escape - skip both chars
                line_end += 2
                continue
            line_end += 1

        # Find heredoc content starting position
        # If there's already a pending heredoc, this one's content starts after that
        if hasattr(self, "_pending_heredoc_end") and self._pending_heredoc_end > line_end:
            content_start = self._pending_heredoc_end
        elif line_end < self.length:
            content_start = line_end + 1  # skip the newline
        else:
            content_start = self.length

        # Find the delimiter line
        content_lines = []
        scan_pos = content_start

        while scan_pos < self.length:
            # Find end of current line
            line_start = scan_pos
            line_end = scan_pos
            while line_end < self.length and self.source[line_end] != "\n":
                line_end += 1

            line = self.source[line_start:line_end]

            # For unquoted heredocs, process backslash-newline before checking delimiter
            # Join continued lines to check the full logical line against delimiter
            if not quoted:
                while line.endswith("\\") and line_end < self.length:
                    # Continue to next line
                    line = line[:-1]  # Remove backslash
                    line_end += 1  # Skip newline
                    next_line_start = line_end
                    while line_end < self.length and self.source[line_end] != "\n":
                        line_end += 1
                    line += self.source[next_line_start:line_end]

            # Check if this line is the delimiter
            check_line = line
            if strip_tabs:
                check_line = line.lstrip("\t")

            if check_line == delimiter:
                # Found the end - update parser position past the heredoc
                # We need to consume the heredoc content from the input
                # But we can't do that here because we haven't finished parsing the command line
                # Store the heredoc info and let the command parser handle it
                break

            # Add line to content (with newline, since we consumed continuations above)
            if strip_tabs:
                line = line.lstrip("\t")
            content_lines.append(line + "\n")

            # Move past the newline
            scan_pos = line_end + 1 if line_end < self.length else self.length

        # Join content (newlines already included per line)
        content = "".join(content_lines)

        # Store the position where heredoc content ends so we can skip it later
        # line_end points to the end of the delimiter line (after any continuations)
        heredoc_end = line_end
        if heredoc_end < self.length:
            heredoc_end += 1  # past the newline

        # Register this heredoc's end position
        if not hasattr(self, "_pending_heredoc_end"):
            self._pending_heredoc_end = heredoc_end
        else:
            self._pending_heredoc_end = max(self._pending_heredoc_end, heredoc_end)

        return HereDoc(delimiter, content, strip_tabs, quoted, fd)

    def parse_command(self) -> Command | None:
        """Parse a simple command (sequence of words and redirections)."""
        words = []
        redirects = []

        while True:
            self.skip_whitespace()
            if self.at_end():
                break
            ch = self.peek()
            # Check for command terminators, but &> and &>> are redirects, not terminators
            if ch in "\n|;()":
                break
            if ch == "&" and not (self.pos + 1 < self.length and self.source[self.pos + 1] == ">"):
                break
            # } is only a terminator at command position (closing a brace group)
            # In argument position, } is just a regular word
            if self.peek() == "}" and not words:
                # Check if } would be a standalone word (next char is whitespace/meta/EOF)
                next_pos = self.pos + 1
                if next_pos >= self.length or self.source[next_pos] in " \t\n|&;()<>":
                    break

            # Try to parse a redirect first
            redirect = self.parse_redirect()
            if redirect is not None:
                redirects.append(redirect)
                continue

            # Otherwise parse a word
            # Allow array assignments like a[1 + 2]= in prefix position (before first non-assignment)
            # Check if all previous words were assignments (contain = not inside quotes)
            all_assignments = True
            for w in words:
                if not self._is_assignment_word(w):
                    all_assignments = False
                    break
            word = self.parse_word(at_command_start=not words or all_assignments)
            if word is None:
                break
            words.append(word)

        if not words and not redirects:
            return None

        return Command(words, redirects)

    def parse_subshell(self) -> Subshell | None:
        """Parse a subshell ( list )."""
        self.skip_whitespace()
        if self.at_end() or self.peek() != "(":
            return None

        self.advance()  # consume (

        body = self.parse_list()
        if body is None:
            raise ParseError("Expected command in subshell", pos=self.pos)

        self.skip_whitespace()
        if self.at_end() or self.peek() != ")":
            raise ParseError("Expected ) to close subshell", pos=self.pos)
        self.advance()  # consume )

        # Collect trailing redirects
        redirects = []
        while True:
            self.skip_whitespace()
            redirect = self.parse_redirect()
            if redirect is None:
                break
            redirects.append(redirect)

        return Subshell(body, redirects if redirects else None)

    def parse_arithmetic_command(self) -> ArithmeticCommand | None:
        """Parse an arithmetic command (( expression )) with parsed internals.

        Returns None if this is not an arithmetic command (e.g., nested subshells
        like '( ( x ) )' that close with ') )' instead of '))').
        """
        self.skip_whitespace()

        # Check for ((
        if (
            self.at_end()
            or self.peek() != "("
            or self.pos + 1 >= self.length
            or self.source[self.pos + 1] != "("
        ):
            return None

        saved_pos = self.pos
        self.advance()  # consume first (
        self.advance()  # consume second (

        # Find matching )) - track nested parens
        # Must be )) with no space between - ') )' is nested subshells
        content_start = self.pos
        depth = 1

        while not self.at_end() and depth > 0:
            c = self.peek()

            if c == "(":
                depth += 1
                self.advance()
            elif c == ")":
                # Check for )) (must be consecutive, no space)
                if depth == 1 and self.pos + 1 < self.length and self.source[self.pos + 1] == ")":
                    # Found the closing ))
                    break
                depth -= 1
                if depth == 0:
                    # Closed with ) but next isn't ) - this is nested subshells, not arithmetic
                    self.pos = saved_pos
                    return None
                self.advance()
            else:
                self.advance()

        if self.at_end() or depth != 1:
            # Didn't find )) - might be nested subshells or malformed
            self.pos = saved_pos
            return None

        content = self.source[content_start : self.pos]
        self.advance()  # consume first )
        self.advance()  # consume second )

        # Parse the arithmetic expression
        expr = self._parse_arith_expr(content)

        # Collect trailing redirects
        redirects = []
        while True:
            self.skip_whitespace()
            redirect = self.parse_redirect()
            if redirect is None:
                break
            redirects.append(redirect)

        return ArithmeticCommand(expr, redirects if redirects else None, raw_content=content)

    # Unary operators for [[ ]] conditionals
    COND_UNARY_OPS = {
        "-a",
        "-b",
        "-c",
        "-d",
        "-e",
        "-f",
        "-g",
        "-h",
        "-k",
        "-p",
        "-r",
        "-s",
        "-t",
        "-u",
        "-w",
        "-x",
        "-G",
        "-L",
        "-N",
        "-O",
        "-S",
        "-z",
        "-n",
        "-o",
        "-v",
        "-R",
    }
    # Binary operators for [[ ]] conditionals
    COND_BINARY_OPS = {
        "==",
        "!=",
        "=~",
        "=",
        "<",
        ">",
        "-eq",
        "-ne",
        "-lt",
        "-le",
        "-gt",
        "-ge",
        "-nt",
        "-ot",
        "-ef",
    }

    def parse_conditional_expr(self) -> ConditionalExpr | None:
        """Parse a conditional expression [[ expression ]]."""
        self.skip_whitespace()

        # Check for [[
        if (
            self.at_end()
            or self.peek() != "["
            or self.pos + 1 >= self.length
            or self.source[self.pos + 1] != "["
        ):
            return None

        self.advance()  # consume first [
        self.advance()  # consume second [

        # Parse the conditional expression body
        body = self._parse_cond_or()

        # Skip whitespace before ]]
        while not self.at_end() and self.peek() in " \t":
            self.advance()

        # Expect ]]
        if (
            self.at_end()
            or self.peek() != "]"
            or self.pos + 1 >= self.length
            or self.source[self.pos + 1] != "]"
        ):
            raise ParseError("Expected ]] to close conditional expression", pos=self.pos)

        self.advance()  # consume first ]
        self.advance()  # consume second ]

        # Collect trailing redirects
        redirects = []
        while True:
            self.skip_whitespace()
            redirect = self.parse_redirect()
            if redirect is None:
                break
            redirects.append(redirect)

        return ConditionalExpr(body, redirects if redirects else None)

    def _cond_skip_whitespace(self) -> None:
        """Skip whitespace inside [[ ]], including backslash-newline continuation."""
        while not self.at_end():
            if self.peek() in " \t":
                self.advance()
            elif (
                self.peek() == "\\"
                and self.pos + 1 < self.length
                and self.source[self.pos + 1] == "\n"
            ):
                self.advance()  # consume backslash
                self.advance()  # consume newline
            elif self.peek() == "\n":
                # Bare newline is also allowed inside [[ ]]
                self.advance()
            else:
                break

    def _cond_at_end(self) -> bool:
        """Check if we're at ]] (end of conditional)."""
        return self.at_end() or (
            self.peek() == "]" and self.pos + 1 < self.length and self.source[self.pos + 1] == "]"
        )

    def _parse_cond_or(self) -> Node:
        """Parse: or_expr = and_expr (|| or_expr)?  (right-associative)"""
        self._cond_skip_whitespace()
        left = self._parse_cond_and()
        self._cond_skip_whitespace()
        if (
            not self._cond_at_end()
            and self.peek() == "|"
            and self.pos + 1 < self.length
            and self.source[self.pos + 1] == "|"
        ):
            self.advance()  # consume first |
            self.advance()  # consume second |
            right = self._parse_cond_or()  # recursive for right-associativity
            return CondOr(left, right)
        return left

    def _parse_cond_and(self) -> Node:
        """Parse: and_expr = term (&& and_expr)?  (right-associative)"""
        self._cond_skip_whitespace()
        left = self._parse_cond_term()
        self._cond_skip_whitespace()
        if (
            not self._cond_at_end()
            and self.peek() == "&"
            and self.pos + 1 < self.length
            and self.source[self.pos + 1] == "&"
        ):
            self.advance()  # consume first &
            self.advance()  # consume second &
            right = self._parse_cond_and()  # recursive for right-associativity
            return CondAnd(left, right)
        return left

    def _parse_cond_term(self) -> Node:
        """Parse: term = '!' term | '(' or_expr ')' | unary_test | binary_test | bare_word"""
        self._cond_skip_whitespace()

        if self._cond_at_end():
            raise ParseError("Unexpected end of conditional expression", pos=self.pos)

        # Negation: ! term
        if self.peek() == "!":
            # Check it's not != operator (need whitespace after !)
            if self.pos + 1 < self.length and self.source[self.pos + 1] not in " \t":
                pass  # not negation, fall through to word parsing
            else:
                self.advance()  # consume !
                operand = self._parse_cond_term()
                return CondNot(operand)

        # Parenthesized group: ( or_expr )
        if self.peek() == "(":
            self.advance()  # consume (
            inner = self._parse_cond_or()
            self._cond_skip_whitespace()
            if self.at_end() or self.peek() != ")":
                raise ParseError("Expected ) in conditional expression", pos=self.pos)
            self.advance()  # consume )
            return CondParen(inner)

        # Parse first word
        word1 = self._parse_cond_word()
        if word1 is None:
            raise ParseError("Expected word in conditional expression", pos=self.pos)

        self._cond_skip_whitespace()

        # Check if word1 is a unary operator
        if word1.value in self.COND_UNARY_OPS:
            # Unary test: -f file
            operand = self._parse_cond_word()
            if operand is None:
                raise ParseError(f"Expected operand after {word1.value}", pos=self.pos)
            return UnaryTest(word1.value, operand)

        # Check if next token is a binary operator
        if not self._cond_at_end() and self.peek() not in "&|)":
            # Handle < and > as binary operators (they terminate words)
            # But not <( or >( which are process substitution
            if self.peek() in "<>" and not (
                self.pos + 1 < self.length and self.source[self.pos + 1] == "("
            ):
                op = self.advance()
                self._cond_skip_whitespace()
                word2 = self._parse_cond_word()
                if word2 is None:
                    raise ParseError(f"Expected operand after {op}", pos=self.pos)
                return BinaryTest(op, word1, word2)
            # Peek at next word to see if it's a binary operator
            saved_pos = self.pos
            op_word = self._parse_cond_word()
            if op_word and op_word.value in self.COND_BINARY_OPS:
                # Binary test: word1 op word2
                self._cond_skip_whitespace()
                # For =~ operator, the RHS is a regex where ( ) are grouping, not conditional grouping
                if op_word.value == "=~":
                    word2 = self._parse_cond_regex_word()
                else:
                    word2 = self._parse_cond_word()
                if word2 is None:
                    raise ParseError(f"Expected operand after {op_word.value}", pos=self.pos)
                return BinaryTest(op_word.value, word1, word2)
            else:
                # Not a binary op, restore position
                self.pos = saved_pos

        # Bare word: implicit -n test
        return UnaryTest("-n", word1)

    def _parse_cond_word(self) -> Word | None:
        """Parse a word inside [[ ]], handling expansions but stopping at conditional operators."""
        self._cond_skip_whitespace()

        if self._cond_at_end():
            return None

        # Check for special tokens that aren't words
        c = self.peek()
        if c in "()":
            return None
        # Note: ! alone is handled by _parse_cond_term() as negation operator
        # Here we allow ! as a word so it can be used as pattern in binary tests
        if c == "&" and self.pos + 1 < self.length and self.source[self.pos + 1] == "&":
            return None
        if c == "|" and self.pos + 1 < self.length and self.source[self.pos + 1] == "|":
            return None

        start = self.pos
        chars = []
        parts = []

        while not self.at_end():
            ch = self.peek()

            # End of conditional
            if ch == "]" and self.pos + 1 < self.length and self.source[self.pos + 1] == "]":
                break

            # Word terminators in conditionals
            if ch in " \t":
                break
            # < and > are string comparison operators in [[ ]], terminate words
            # But <(...) and >(...) are process substitution - don't break
            if ch in "<>" and not (self.pos + 1 < self.length and self.source[self.pos + 1] == "("):
                break
            # ( and ) end words unless part of extended glob: @(...), ?(...), *(...), +(...), !(...)
            if ch == "(":
                # Check if this is an extended glob (preceded by @, ?, *, +, or !)
                if chars and chars[-1] in "@?*+!":
                    # Extended glob - consume the parenthesized content
                    chars.append(self.advance())  # (
                    depth = 1
                    while not self.at_end() and depth > 0:
                        c = self.peek()
                        if c == "(":
                            depth += 1
                        elif c == ")":
                            depth -= 1
                        chars.append(self.advance())
                    continue
                else:
                    break
            if ch == ")":
                break
            if ch == "&" and self.pos + 1 < self.length and self.source[self.pos + 1] == "&":
                break
            if ch == "|" and self.pos + 1 < self.length and self.source[self.pos + 1] == "|":
                break

            # Single-quoted string
            if ch == "'":
                self.advance()
                chars.append("'")
                while not self.at_end() and self.peek() != "'":
                    chars.append(self.advance())
                if self.at_end():
                    raise ParseError("Unterminated single quote", pos=start)
                chars.append(self.advance())

            # Double-quoted string
            elif ch == '"':
                self.advance()
                chars.append('"')
                while not self.at_end() and self.peek() != '"':
                    c = self.peek()
                    if c == "\\" and self.pos + 1 < self.length:
                        next_c = self.source[self.pos + 1]
                        if next_c == "\n":
                            # Line continuation - skip both backslash and newline
                            self.advance()
                            self.advance()
                        else:
                            chars.append(self.advance())
                            chars.append(self.advance())
                    elif c == "$":
                        # Handle expansions inside double quotes
                        if (
                            self.pos + 2 < self.length
                            and self.source[self.pos + 1] == "("
                            and self.source[self.pos + 2] == "("
                        ):
                            arith_node, arith_text = self._parse_arithmetic_expansion()
                            if arith_node:
                                parts.append(arith_node)
                                chars.append(arith_text)
                            else:
                                # Not arithmetic - try command substitution
                                cmdsub_node, cmdsub_text = self._parse_command_substitution()
                                if cmdsub_node:
                                    parts.append(cmdsub_node)
                                    chars.append(cmdsub_text)
                                else:
                                    chars.append(self.advance())
                        elif self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
                            cmdsub_node, cmdsub_text = self._parse_command_substitution()
                            if cmdsub_node:
                                parts.append(cmdsub_node)
                                chars.append(cmdsub_text)
                            else:
                                chars.append(self.advance())
                        else:
                            param_node, param_text = self._parse_param_expansion()
                            if param_node:
                                parts.append(param_node)
                                chars.append(param_text)
                            else:
                                chars.append(self.advance())
                    else:
                        chars.append(self.advance())
                if self.at_end():
                    raise ParseError("Unterminated double quote", pos=start)
                chars.append(self.advance())

            # Escape
            elif ch == "\\" and self.pos + 1 < self.length:
                chars.append(self.advance())
                chars.append(self.advance())

            # Arithmetic expansion $((...))
            elif (
                ch == "$"
                and self.pos + 2 < self.length
                and self.source[self.pos + 1] == "("
                and self.source[self.pos + 2] == "("
            ):
                arith_node, arith_text = self._parse_arithmetic_expansion()
                if arith_node:
                    parts.append(arith_node)
                    chars.append(arith_text)
                else:
                    chars.append(self.advance())

            # Command substitution $(...)
            elif ch == "$" and self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
                cmdsub_node, cmdsub_text = self._parse_command_substitution()
                if cmdsub_node:
                    parts.append(cmdsub_node)
                    chars.append(cmdsub_text)
                else:
                    chars.append(self.advance())

            # Parameter expansion $var or ${...}
            elif ch == "$":
                param_node, param_text = self._parse_param_expansion()
                if param_node:
                    parts.append(param_node)
                    chars.append(param_text)
                else:
                    chars.append(self.advance())

            # Process substitution <(...) or >(...)
            elif ch in "<>" and self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
                procsub_node, procsub_text = self._parse_process_substitution()
                if procsub_node:
                    parts.append(procsub_node)
                    chars.append(procsub_text)
                else:
                    chars.append(self.advance())

            # Backtick command substitution
            elif ch == "`":
                cmdsub_node, cmdsub_text = self._parse_backtick_substitution()
                if cmdsub_node:
                    parts.append(cmdsub_node)
                    chars.append(cmdsub_text)
                else:
                    chars.append(self.advance())

            # Regular character
            else:
                chars.append(self.advance())

        if not chars:
            return None

        return Word("".join(chars), parts if parts else None)

    def _parse_cond_regex_word(self) -> Word | None:
        """Parse a regex pattern word in [[ ]], where ( ) are regex grouping, not conditional grouping."""
        self._cond_skip_whitespace()

        if self._cond_at_end():
            return None

        start = self.pos
        chars = []
        parts = []
        paren_depth = 0  # Track regex grouping parens - spaces inside don't terminate

        while not self.at_end():
            ch = self.peek()

            # End of conditional
            if ch == "]" and self.pos + 1 < self.length and self.source[self.pos + 1] == "]":
                break

            # Backslash-newline continuation (check before space/escape handling)
            if ch == "\\" and self.pos + 1 < self.length and self.source[self.pos + 1] == "\n":
                self.advance()  # consume backslash
                self.advance()  # consume newline
                continue

            # Escape sequences - consume both characters (including escaped spaces)
            if ch == "\\" and self.pos + 1 < self.length:
                chars.append(self.advance())
                chars.append(self.advance())
                continue

            # Track regex grouping parentheses
            if ch == "(":
                paren_depth += 1
                chars.append(self.advance())
                continue
            if ch == ")":
                if paren_depth > 0:
                    paren_depth -= 1
                    chars.append(self.advance())
                    continue
                # Unmatched ) - probably end of pattern
                break

            # Regex character class [...] - consume until closing ]
            # Handles [[:alpha:]], [^0-9], []a-z] (] as first char), etc.
            if ch == "[":
                chars.append(self.advance())  # consume [
                # Handle negation [^
                if not self.at_end() and self.peek() == "^":
                    chars.append(self.advance())
                # Handle ] as first char (literal ])
                if not self.at_end() and self.peek() == "]":
                    chars.append(self.advance())
                # Consume until closing ]
                while not self.at_end():
                    c = self.peek()
                    if c == "]":
                        chars.append(self.advance())
                        break
                    if c == "[" and self.pos + 1 < self.length and self.source[self.pos + 1] == ":":
                        # POSIX class like [:alpha:] inside bracket expression
                        chars.append(self.advance())  # [
                        chars.append(self.advance())  # :
                        while not self.at_end() and not (
                            self.peek() == ":"
                            and self.pos + 1 < self.length
                            and self.source[self.pos + 1] == "]"
                        ):
                            chars.append(self.advance())
                        if not self.at_end():
                            chars.append(self.advance())  # :
                            chars.append(self.advance())  # ]
                    else:
                        chars.append(self.advance())
                continue

            # Word terminators - space/tab ends the regex (unless inside parens), as do && and ||
            if ch in " \t\n" and paren_depth == 0:
                break
            if ch in " \t\n" and paren_depth > 0:
                # Space inside regex parens is part of the pattern
                chars.append(self.advance())
                continue
            if ch == "&" and self.pos + 1 < self.length and self.source[self.pos + 1] == "&":
                break
            if ch == "|" and self.pos + 1 < self.length and self.source[self.pos + 1] == "|":
                break

            # Single-quoted string
            if ch == "'":
                self.advance()
                chars.append("'")
                while not self.at_end() and self.peek() != "'":
                    chars.append(self.advance())
                if self.at_end():
                    raise ParseError("Unterminated single quote", pos=start)
                chars.append(self.advance())
                continue

            # Double-quoted string
            if ch == '"':
                self.advance()
                chars.append('"')
                while not self.at_end() and self.peek() != '"':
                    c = self.peek()
                    if c == "\\" and self.pos + 1 < self.length:
                        chars.append(self.advance())
                        chars.append(self.advance())
                    elif c == "$":
                        param_node, param_text = self._parse_param_expansion()
                        if param_node:
                            parts.append(param_node)
                            chars.append(param_text)
                        else:
                            chars.append(self.advance())
                    else:
                        chars.append(self.advance())
                if self.at_end():
                    raise ParseError("Unterminated double quote", pos=start)
                chars.append(self.advance())
                continue

            # Command substitution $(...) or parameter expansion $var or ${...}
            if ch == "$":
                # Try command substitution first
                if self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
                    cmdsub_node, cmdsub_text = self._parse_command_substitution()
                    if cmdsub_node:
                        parts.append(cmdsub_node)
                        chars.append(cmdsub_text)
                        continue
                param_node, param_text = self._parse_param_expansion()
                if param_node:
                    parts.append(param_node)
                    chars.append(param_text)
                else:
                    chars.append(self.advance())
                continue

            # Regular character (including ( ) which are regex grouping)
            chars.append(self.advance())

        if not chars:
            return None

        return Word("".join(chars), parts if parts else None)

    def parse_brace_group(self) -> BraceGroup | None:
        """Parse a brace group { list }."""
        self.skip_whitespace()
        if self.at_end() or self.peek() != "{":
            return None

        # Check that { is followed by whitespace (it's a reserved word)
        if self.pos + 1 < self.length and self.source[self.pos + 1] not in " \t\n":
            return None

        self.advance()  # consume {
        self.skip_whitespace_and_newlines()

        body = self.parse_list()
        if body is None:
            raise ParseError("Expected command in brace group", pos=self.pos)

        self.skip_whitespace()
        if self.at_end() or self.peek() != "}":
            raise ParseError("Expected } to close brace group", pos=self.pos)
        self.advance()  # consume }

        # Collect trailing redirects
        redirects = []
        while True:
            self.skip_whitespace()
            redirect = self.parse_redirect()
            if redirect is None:
                break
            redirects.append(redirect)

        return BraceGroup(body, redirects if redirects else None)

    def parse_if(self) -> If | None:
        """Parse an if statement: if list; then list [elif list; then list]* [else list] fi."""
        self.skip_whitespace()

        # Check for 'if' keyword
        if self.peek_word() != "if":
            return None

        self.consume_word("if")

        # Parse condition (a list that ends at 'then')
        condition = self.parse_list_until({"then"})
        if condition is None:
            raise ParseError("Expected condition after 'if'", pos=self.pos)

        # Expect 'then'
        self.skip_whitespace_and_newlines()
        if not self.consume_word("then"):
            raise ParseError("Expected 'then' after if condition", pos=self.pos)

        # Parse then body (ends at elif, else, or fi)
        then_body = self.parse_list_until({"elif", "else", "fi"})
        if then_body is None:
            raise ParseError("Expected commands after 'then'", pos=self.pos)

        # Check what comes next: elif, else, or fi
        self.skip_whitespace_and_newlines()
        next_word = self.peek_word()

        else_body = None
        if next_word == "elif":
            # elif is syntactic sugar for else if ... fi
            self.consume_word("elif")
            # Parse the rest as a nested if (but we've already consumed 'elif')
            # We need to parse: condition; then body [elif|else|fi]
            elif_condition = self.parse_list_until({"then"})
            if elif_condition is None:
                raise ParseError("Expected condition after 'elif'", pos=self.pos)

            self.skip_whitespace_and_newlines()
            if not self.consume_word("then"):
                raise ParseError("Expected 'then' after elif condition", pos=self.pos)

            elif_then_body = self.parse_list_until({"elif", "else", "fi"})
            if elif_then_body is None:
                raise ParseError("Expected commands after 'then'", pos=self.pos)

            # Recursively handle more elif/else/fi
            self.skip_whitespace_and_newlines()
            inner_next = self.peek_word()

            inner_else = None
            if inner_next == "elif":
                # More elif - recurse by creating a fake "if" and parsing
                # Actually, let's just recursively call a helper
                inner_else = self._parse_elif_chain()
            elif inner_next == "else":
                self.consume_word("else")
                inner_else = self.parse_list_until({"fi"})
                if inner_else is None:
                    raise ParseError("Expected commands after 'else'", pos=self.pos)

            else_body = If(elif_condition, elif_then_body, inner_else)

        elif next_word == "else":
            self.consume_word("else")
            else_body = self.parse_list_until({"fi"})
            if else_body is None:
                raise ParseError("Expected commands after 'else'", pos=self.pos)

        # Expect 'fi'
        self.skip_whitespace_and_newlines()
        if not self.consume_word("fi"):
            raise ParseError("Expected 'fi' to close if statement", pos=self.pos)

        # Parse optional trailing redirections
        redirects = []
        while True:
            self.skip_whitespace()
            redirect = self.parse_redirect()
            if redirect is None:
                break
            redirects.append(redirect)

        return If(condition, then_body, else_body, redirects if redirects else None)

    def _parse_elif_chain(self) -> If:
        """Parse elif chain (after seeing 'elif' keyword)."""
        self.consume_word("elif")

        condition = self.parse_list_until({"then"})
        if condition is None:
            raise ParseError("Expected condition after 'elif'", pos=self.pos)

        self.skip_whitespace_and_newlines()
        if not self.consume_word("then"):
            raise ParseError("Expected 'then' after elif condition", pos=self.pos)

        then_body = self.parse_list_until({"elif", "else", "fi"})
        if then_body is None:
            raise ParseError("Expected commands after 'then'", pos=self.pos)

        self.skip_whitespace_and_newlines()
        next_word = self.peek_word()

        else_body = None
        if next_word == "elif":
            else_body = self._parse_elif_chain()
        elif next_word == "else":
            self.consume_word("else")
            else_body = self.parse_list_until({"fi"})
            if else_body is None:
                raise ParseError("Expected commands after 'else'", pos=self.pos)

        return If(condition, then_body, else_body)

    def parse_while(self) -> While | None:
        """Parse a while loop: while list; do list; done."""
        self.skip_whitespace()

        if self.peek_word() != "while":
            return None

        self.consume_word("while")

        # Parse condition (ends at 'do')
        condition = self.parse_list_until({"do"})
        if condition is None:
            raise ParseError("Expected condition after 'while'", pos=self.pos)

        # Expect 'do'
        self.skip_whitespace_and_newlines()
        if not self.consume_word("do"):
            raise ParseError("Expected 'do' after while condition", pos=self.pos)

        # Parse body (ends at 'done')
        body = self.parse_list_until({"done"})
        if body is None:
            raise ParseError("Expected commands after 'do'", pos=self.pos)

        # Expect 'done'
        self.skip_whitespace_and_newlines()
        if not self.consume_word("done"):
            raise ParseError("Expected 'done' to close while loop", pos=self.pos)

        # Parse optional trailing redirections
        redirects = []
        while True:
            self.skip_whitespace()
            redirect = self.parse_redirect()
            if redirect is None:
                break
            redirects.append(redirect)

        return While(condition, body, redirects if redirects else None)

    def parse_until(self) -> Until | None:
        """Parse an until loop: until list; do list; done."""
        self.skip_whitespace()

        if self.peek_word() != "until":
            return None

        self.consume_word("until")

        # Parse condition (ends at 'do')
        condition = self.parse_list_until({"do"})
        if condition is None:
            raise ParseError("Expected condition after 'until'", pos=self.pos)

        # Expect 'do'
        self.skip_whitespace_and_newlines()
        if not self.consume_word("do"):
            raise ParseError("Expected 'do' after until condition", pos=self.pos)

        # Parse body (ends at 'done')
        body = self.parse_list_until({"done"})
        if body is None:
            raise ParseError("Expected commands after 'do'", pos=self.pos)

        # Expect 'done'
        self.skip_whitespace_and_newlines()
        if not self.consume_word("done"):
            raise ParseError("Expected 'done' to close until loop", pos=self.pos)

        # Parse optional trailing redirections
        redirects = []
        while True:
            self.skip_whitespace()
            redirect = self.parse_redirect()
            if redirect is None:
                break
            redirects.append(redirect)

        return Until(condition, body, redirects if redirects else None)

    def parse_for(self) -> For | ForArith | None:
        """Parse a for loop: for name [in words]; do list; done or C-style for ((;;))."""
        self.skip_whitespace()

        if self.peek_word() != "for":
            return None

        self.consume_word("for")
        self.skip_whitespace()

        # Check for C-style for loop: for ((init; cond; incr))
        if self.peek() == "(" and self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
            return self._parse_for_arith()

        # Parse variable name (bash allows reserved words as variable names in for loops)
        var_name = self.peek_word()
        if var_name is None:
            raise ParseError("Expected variable name after 'for'", pos=self.pos)
        self.consume_word(var_name)

        self.skip_whitespace()

        # Handle optional semicolon or newline before 'in' or 'do'
        if self.peek() == ";":
            self.advance()
        self.skip_whitespace_and_newlines()

        # Check for optional 'in' clause
        words = None
        if self.peek_word() == "in":
            self.consume_word("in")
            self.skip_whitespace_and_newlines()  # Allow newlines after 'in'

            # Parse words until semicolon, newline, or 'do'
            words = []
            while True:
                self.skip_whitespace()
                # Check for end of word list
                if self.at_end():
                    break
                if self.peek() in ";\n":
                    if self.peek() == ";":
                        self.advance()  # consume semicolon
                    break
                if self.peek_word() == "do":
                    break

                word = self.parse_word()
                if word is None:
                    break
                words.append(word)

        # Skip to 'do'
        self.skip_whitespace_and_newlines()

        # Expect 'do'
        if not self.consume_word("do"):
            raise ParseError("Expected 'do' in for loop", pos=self.pos)

        # Parse body (ends at 'done')
        body = self.parse_list_until({"done"})
        if body is None:
            raise ParseError("Expected commands after 'do'", pos=self.pos)

        # Expect 'done'
        self.skip_whitespace_and_newlines()
        if not self.consume_word("done"):
            raise ParseError("Expected 'done' to close for loop", pos=self.pos)

        # Parse optional trailing redirections
        redirects = []
        while True:
            self.skip_whitespace()
            redirect = self.parse_redirect()
            if redirect is None:
                break
            redirects.append(redirect)

        return For(var_name, words, body, redirects if redirects else None)

    def _parse_for_arith(self) -> ForArith:
        """Parse C-style for loop: for ((init; cond; incr)); do list; done."""
        # We've already consumed 'for' and positioned at '(('
        self.advance()  # consume first (
        self.advance()  # consume second (

        # Parse the three expressions separated by semicolons
        # Each can be empty
        parts = []
        current = []
        paren_depth = 0

        while not self.at_end():
            ch = self.peek()
            if ch == "(":
                paren_depth += 1
                current.append(self.advance())
            elif ch == ")":
                if paren_depth > 0:
                    paren_depth -= 1
                    current.append(self.advance())
                else:
                    # Check for closing ))
                    if self.pos + 1 < self.length and self.source[self.pos + 1] == ")":
                        # End of ((...)) - preserve trailing whitespace
                        parts.append("".join(current).lstrip())
                        self.advance()  # consume first )
                        self.advance()  # consume second )
                        break
                    else:
                        current.append(self.advance())
            elif ch == ";" and paren_depth == 0:
                # Preserve trailing whitespace in expressions
                parts.append("".join(current).lstrip())
                current = []
                self.advance()  # consume ;
            else:
                current.append(self.advance())

        if len(parts) != 3:
            raise ParseError("Expected three expressions in for ((;;))", pos=self.pos)

        init, cond, incr = parts

        self.skip_whitespace()

        # Handle optional semicolon
        if not self.at_end() and self.peek() == ";":
            self.advance()

        self.skip_whitespace_and_newlines()

        # Parse body - either do/done or brace group
        if self.peek() == "{":
            brace = self.parse_brace_group()
            if brace is None:
                raise ParseError("Expected brace group body in for loop", pos=self.pos)
            # Unwrap the brace-group to match oracle output format
            body = brace.body
        elif self.consume_word("do"):
            body = self.parse_list_until({"done"})
            if body is None:
                raise ParseError("Expected commands after 'do'", pos=self.pos)
            self.skip_whitespace_and_newlines()
            if not self.consume_word("done"):
                raise ParseError("Expected 'done' to close for loop", pos=self.pos)
        else:
            raise ParseError("Expected 'do' or '{' in for loop", pos=self.pos)

        # Parse optional trailing redirections
        redirects = []
        while True:
            self.skip_whitespace()
            redirect = self.parse_redirect()
            if redirect is None:
                break
            redirects.append(redirect)

        return ForArith(init, cond, incr, body, redirects if redirects else None)

    def parse_select(self) -> Select | None:
        """Parse a select statement: select name [in words]; do list; done."""
        self.skip_whitespace()

        if self.peek_word() != "select":
            return None

        self.consume_word("select")
        self.skip_whitespace()

        # Parse variable name
        var_name = self.peek_word()
        if var_name is None:
            raise ParseError("Expected variable name after 'select'", pos=self.pos)
        self.consume_word(var_name)

        self.skip_whitespace()

        # Handle optional semicolon before 'in', 'do', or '{'
        if self.peek() == ";":
            self.advance()
        self.skip_whitespace_and_newlines()

        # Check for optional 'in' clause
        words = None
        if self.peek_word() == "in":
            self.consume_word("in")
            self.skip_whitespace_and_newlines()  # Allow newlines after 'in'

            # Parse words until semicolon, newline, 'do', or '{'
            words = []
            while True:
                self.skip_whitespace()
                # Check for end of word list
                if self.at_end():
                    break
                if self.peek() in ";\n{":
                    if self.peek() == ";":
                        self.advance()  # consume semicolon
                    break
                if self.peek_word() == "do":
                    break

                word = self.parse_word()
                if word is None:
                    break
                words.append(word)

            # Empty word list is allowed for select (unlike for)

        # Skip whitespace before body
        self.skip_whitespace_and_newlines()

        # Parse body - either do/done or brace group
        if self.peek() == "{":
            brace = self.parse_brace_group()
            if brace is None:
                raise ParseError("Expected brace group body in select", pos=self.pos)
            # Unwrap the brace-group to match oracle output format
            body = brace.body
        elif self.consume_word("do"):
            # Parse body (ends at 'done')
            body = self.parse_list_until({"done"})
            if body is None:
                raise ParseError("Expected commands after 'do'", pos=self.pos)

            # Expect 'done'
            self.skip_whitespace_and_newlines()
            if not self.consume_word("done"):
                raise ParseError("Expected 'done' to close select", pos=self.pos)
        else:
            raise ParseError("Expected 'do' or '{' in select", pos=self.pos)

        # Parse optional trailing redirections
        redirects = []
        while True:
            self.skip_whitespace()
            redirect = self.parse_redirect()
            if redirect is None:
                break
            redirects.append(redirect)

        return Select(var_name, words, body, redirects if redirects else None)

    def _is_case_terminator(self) -> bool:
        """Check if we're at a case pattern terminator (;;, ;&, or ;;&)."""
        if self.at_end() or self.peek() != ";":
            return False
        if self.pos + 1 >= self.length:
            return False
        next_ch = self.source[self.pos + 1]
        # ;; or ;& or ;;& (which is actually ;;&)
        return next_ch in ";&"

    def _consume_case_terminator(self) -> str:
        """Consume and return case pattern terminator (;;, ;&, or ;;&)."""
        if self.at_end() or self.peek() != ";":
            return ";;"  # default
        self.advance()  # consume first ;
        if self.at_end():
            return ";;"
        ch = self.peek()
        if ch == ";":
            self.advance()  # consume second ;
            # Check for ;;&
            if not self.at_end() and self.peek() == "&":
                self.advance()  # consume &
                return ";;&"
            return ";;"
        elif ch == "&":
            self.advance()  # consume &
            return ";&"
        return ";;"

    def parse_case(self) -> Case | None:
        """Parse a case statement: case word in pattern) commands;; ... esac."""
        self.skip_whitespace()

        if self.peek_word() != "case":
            return None

        self.consume_word("case")
        self.skip_whitespace()

        # Parse the word to match
        word = self.parse_word()
        if word is None:
            raise ParseError("Expected word after 'case'", pos=self.pos)

        self.skip_whitespace_and_newlines()

        # Expect 'in'
        if not self.consume_word("in"):
            raise ParseError("Expected 'in' after case word", pos=self.pos)

        self.skip_whitespace_and_newlines()

        # Parse pattern clauses until 'esac'
        patterns = []
        while True:
            self.skip_whitespace_and_newlines()

            # Check if we're at 'esac' (but not 'esac)' which is esac as a pattern)
            if self.peek_word() == "esac":
                # Look ahead to see if esac is a pattern (esac followed by ) then body/;;)
                # or the closing keyword (esac followed by ) that closes containing construct)
                saved = self.pos
                self.skip_whitespace()
                # Consume "esac"
                while (
                    not self.at_end() and self.peek() not in METACHAR and self.peek() not in "\"'"
                ):
                    self.advance()
                self.skip_whitespace()
                # Check for ) and what follows
                is_pattern = False
                if not self.at_end() and self.peek() == ")":
                    self.advance()  # consume )
                    self.skip_whitespace()
                    # esac is a pattern if there's body content or ;; after )
                    # Not a pattern if ) is followed by end, newline, or another )
                    if not self.at_end():
                        next_ch = self.peek()
                        # If followed by ;; or actual command content, it's a pattern
                        if next_ch == ";":
                            is_pattern = True
                        elif next_ch not in "\n)":
                            is_pattern = True
                self.pos = saved
                if not is_pattern:
                    break

            # Skip optional leading ( before pattern (POSIX allows this)
            self.skip_whitespace_and_newlines()
            if not self.at_end() and self.peek() == "(":
                self.advance()
                self.skip_whitespace_and_newlines()

            # Parse pattern (everything until ')' at depth 0)
            # Pattern can contain | for alternation, quotes, globs, extglobs, etc.
            # Extglob patterns @(), ?(), *(), +(), !() contain nested parens
            pattern_chars = []
            extglob_depth = 0
            while not self.at_end():
                ch = self.peek()
                if ch == ")":
                    if extglob_depth > 0:
                        # Inside extglob, consume the ) and decrement depth
                        pattern_chars.append(self.advance())
                        extglob_depth -= 1
                    else:
                        # End of pattern
                        self.advance()
                        break
                elif ch == "\\":
                    # Line continuation or backslash escape
                    if self.pos + 1 < self.length and self.source[self.pos + 1] == "\n":
                        # Line continuation - skip both backslash and newline
                        self.advance()
                        self.advance()
                    else:
                        # Normal escape - consume both chars
                        pattern_chars.append(self.advance())
                        if not self.at_end():
                            pattern_chars.append(self.advance())
                elif ch == "$" and self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
                    # $( or $(( - command sub or arithmetic
                    pattern_chars.append(self.advance())  # $
                    pattern_chars.append(self.advance())  # (
                    if not self.at_end() and self.peek() == "(":
                        # $(( arithmetic - need to find matching ))
                        pattern_chars.append(self.advance())  # second (
                        paren_depth = 2
                        while not self.at_end() and paren_depth > 0:
                            c = self.peek()
                            if c == "(":
                                paren_depth += 1
                            elif c == ")":
                                paren_depth -= 1
                            pattern_chars.append(self.advance())
                    else:
                        # $() command sub - track single paren
                        extglob_depth += 1
                elif ch == "(" and extglob_depth > 0:
                    # Grouping paren inside extglob
                    pattern_chars.append(self.advance())
                    extglob_depth += 1
                elif (
                    ch in "@?*+!"
                    and self.pos + 1 < self.length
                    and self.source[self.pos + 1] == "("
                ):
                    # Extglob opener: @(, ?(, *(, +(, !(
                    pattern_chars.append(self.advance())  # @, ?, *, +, or !
                    pattern_chars.append(self.advance())  # (
                    extglob_depth += 1
                elif ch == "[":
                    # Character class - but only if there's a matching ]
                    # ] must come before ) at same depth (either extglob or pattern)
                    is_char_class = False
                    scan_pos = self.pos + 1
                    scan_depth = 0
                    has_first_bracket_literal = False
                    # Skip [! or [^ at start
                    if scan_pos < self.length and self.source[scan_pos] in "!^":
                        scan_pos += 1
                    # Skip ] as first char (literal in char class) only if there's another ]
                    if scan_pos < self.length and self.source[scan_pos] == "]":
                        # Check if there's another ] later
                        if "]" in self.source[scan_pos + 1 :]:
                            scan_pos += 1
                            has_first_bracket_literal = True
                    while scan_pos < self.length:
                        sc = self.source[scan_pos]
                        if sc == "]" and scan_depth == 0:
                            is_char_class = True
                            break
                        elif sc == "[":
                            scan_depth += 1
                        elif sc == ")" and scan_depth == 0:
                            # Hit pattern/extglob closer before finding ]
                            break
                        elif sc == "|" and scan_depth == 0 and extglob_depth > 0:
                            # Hit alternation in extglob - ] must be in this branch
                            break
                        scan_pos += 1
                    if is_char_class:
                        pattern_chars.append(self.advance())
                        # Handle [! or [^ at start
                        if not self.at_end() and self.peek() in "!^":
                            pattern_chars.append(self.advance())
                        # Handle ] as first char (literal) only if we detected it in scan
                        if has_first_bracket_literal and not self.at_end() and self.peek() == "]":
                            pattern_chars.append(self.advance())
                        # Consume until closing ]
                        while not self.at_end() and self.peek() != "]":
                            pattern_chars.append(self.advance())
                        if not self.at_end():
                            pattern_chars.append(self.advance())  # ]
                    else:
                        # Not a valid char class, treat [ as literal
                        pattern_chars.append(self.advance())
                elif ch == "'":
                    # Single-quoted string in pattern
                    pattern_chars.append(self.advance())
                    while not self.at_end() and self.peek() != "'":
                        pattern_chars.append(self.advance())
                    if not self.at_end():
                        pattern_chars.append(self.advance())
                elif ch == '"':
                    # Double-quoted string in pattern
                    pattern_chars.append(self.advance())
                    while not self.at_end() and self.peek() != '"':
                        if self.peek() == "\\" and self.pos + 1 < self.length:
                            pattern_chars.append(self.advance())
                        pattern_chars.append(self.advance())
                    if not self.at_end():
                        pattern_chars.append(self.advance())
                elif ch in " \t\n":
                    # Skip whitespace at top level, but preserve inside $() or extglob
                    if extglob_depth > 0:
                        pattern_chars.append(self.advance())
                    else:
                        self.advance()
                else:
                    pattern_chars.append(self.advance())

            pattern = "".join(pattern_chars)
            if not pattern:
                raise ParseError("Expected pattern in case statement", pos=self.pos)

            # Parse commands until ;;, ;&, ;;&, or esac
            # Commands are optional (can have empty body)
            self.skip_whitespace()

            body = None
            # Check for empty body: terminator right after pattern
            is_empty_body = self._is_case_terminator()

            if not is_empty_body:
                # Skip newlines and check if there's content before terminator or esac
                self.skip_whitespace_and_newlines()
                if not self.at_end() and self.peek_word() != "esac":
                    # Check again for terminator after whitespace/newlines
                    is_at_terminator = self._is_case_terminator()
                    if not is_at_terminator:
                        body = self.parse_list_until({"esac"})
                        self.skip_whitespace()

            # Handle terminator: ;;, ;&, or ;;&
            terminator = self._consume_case_terminator()

            self.skip_whitespace_and_newlines()

            patterns.append(CasePattern(pattern, body, terminator))

        # Expect 'esac'
        self.skip_whitespace_and_newlines()
        if not self.consume_word("esac"):
            raise ParseError("Expected 'esac' to close case statement", pos=self.pos)

        # Collect trailing redirects
        redirects = []
        while True:
            self.skip_whitespace()
            redirect = self.parse_redirect()
            if redirect is None:
                break
            redirects.append(redirect)

        return Case(word, patterns, redirects if redirects else None)

    def parse_coproc(self) -> Coproc | None:
        """Parse a coproc statement.

        Oracle behavior:
        - For compound commands (brace group, if, while, etc.), extract NAME if present
        - For simple commands, don't extract NAME (treat everything as the command)
        """
        self.skip_whitespace()
        if self.at_end():
            return None

        if self.peek_word() != "coproc":
            return None

        self.consume_word("coproc")
        self.skip_whitespace()

        name = None

        # Check for compound command directly (no NAME)
        ch = self.peek() if not self.at_end() else None
        if ch == "{":
            body = self.parse_brace_group()
            if body is not None:
                return Coproc(body, name)
        if ch == "(":
            if self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
                body = self.parse_arithmetic_command()
                if body is not None:
                    return Coproc(body, name)
            body = self.parse_subshell()
            if body is not None:
                return Coproc(body, name)

        # Check for reserved word compounds directly
        next_word = self.peek_word()
        if next_word in ("while", "until", "for", "if", "case", "select"):
            body = self.parse_compound_command()
            if body is not None:
                return Coproc(body, name)

        # Check if first word is NAME followed by compound command
        word_start = self.pos
        potential_name = self.peek_word()
        if potential_name:
            # Skip past the potential name
            while not self.at_end() and self.peek() not in METACHAR and self.peek() not in "\"'":
                self.advance()
            self.skip_whitespace()

            # Check what follows
            ch = self.peek() if not self.at_end() else None
            next_word = self.peek_word()

            if ch == "{":
                # NAME { ... } - extract name
                name = potential_name
                body = self.parse_brace_group()
                if body is not None:
                    return Coproc(body, name)
            elif ch == "(":
                # NAME ( ... ) - extract name
                name = potential_name
                if self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
                    body = self.parse_arithmetic_command()
                else:
                    body = self.parse_subshell()
                if body is not None:
                    return Coproc(body, name)
            elif next_word in ("while", "until", "for", "if", "case", "select"):
                # NAME followed by reserved compound - extract name
                name = potential_name
                body = self.parse_compound_command()
                if body is not None:
                    return Coproc(body, name)

            # Not followed by compound - restore position and parse as simple command
            self.pos = word_start

        # Parse as simple command (includes any "NAME" as part of the command)
        body = self.parse_command()
        if body is not None:
            return Coproc(body, name)

        raise ParseError("Expected command after coproc", pos=self.pos)

    def parse_function(self) -> Function | None:
        """Parse a function definition.

        Forms:
            name() compound_command           # POSIX form
            function name compound_command    # bash form without parens
            function name() compound_command  # bash form with parens
        """
        self.skip_whitespace()
        if self.at_end():
            return None

        saved_pos = self.pos

        # Check for 'function' keyword form
        if self.peek_word() == "function":
            self.consume_word("function")
            self.skip_whitespace()

            # Get function name
            name = self.peek_word()
            if name is None:
                self.pos = saved_pos
                return None
            self.consume_word(name)
            self.skip_whitespace()

            # Optional () after name - but only if it's actually ()
            # and not the start of a subshell body
            if not self.at_end() and self.peek() == "(":
                # Check if this is () or start of subshell
                if self.pos + 1 < self.length and self.source[self.pos + 1] == ")":
                    self.advance()  # consume (
                    self.advance()  # consume )
                # else: the ( is start of subshell body, don't consume

            self.skip_whitespace_and_newlines()

            # Parse body (any compound command)
            body = self._parse_compound_command()
            if body is None:
                raise ParseError("Expected function body", pos=self.pos)

            return Function(name, body)

        # Check for POSIX form: name()
        # We need to peek ahead to see if there's a () after the word
        name = self.peek_word()
        if name is None or name in RESERVED_WORDS:
            return None

        # Assignment words (containing =) are not function definitions
        if "=" in name:
            return None

        # Save position after the name
        self.skip_whitespace()
        name_start = self.pos

        # Consume the name
        while not self.at_end() and self.peek() not in METACHAR and self.peek() not in "\"'()":
            self.advance()

        name = self.source[name_start : self.pos]
        if not name:
            self.pos = saved_pos
            return None

        # Check for () - whitespace IS allowed between name and (
        self.skip_whitespace()
        if self.at_end() or self.peek() != "(":
            self.pos = saved_pos
            return None

        self.advance()  # consume (
        self.skip_whitespace()
        if self.at_end() or self.peek() != ")":
            self.pos = saved_pos
            return None
        self.advance()  # consume )

        self.skip_whitespace_and_newlines()

        # Parse body (any compound command)
        body = self._parse_compound_command()
        if body is None:
            raise ParseError("Expected function body", pos=self.pos)

        return Function(name, body)

    def _parse_compound_command(self) -> Node | None:
        """Parse any compound command (for function bodies, etc.)."""
        # Try each compound command type
        result = self.parse_brace_group()
        if result:
            return result

        result = self.parse_subshell()
        if result:
            return result

        result = self.parse_conditional_expr()
        if result:
            return result

        result = self.parse_if()
        if result:
            return result

        result = self.parse_while()
        if result:
            return result

        result = self.parse_until()
        if result:
            return result

        result = self.parse_for()
        if result:
            return result

        result = self.parse_case()
        if result:
            return result

        result = self.parse_select()
        if result:
            return result

        return None

    def parse_list_until(self, stop_words: set[str]) -> Node | None:
        """Parse a list that stops before certain reserved words."""
        # Check if we're already at a stop word
        self.skip_whitespace_and_newlines()
        if self.peek_word() in stop_words:
            return None

        pipeline = self.parse_pipeline()
        if pipeline is None:
            return None

        parts = [pipeline]

        while True:
            # Check for newline as implicit command separator
            self.skip_whitespace()
            has_newline = False
            while not self.at_end() and self.peek() == "\n":
                has_newline = True
                self.advance()
                # Skip past any pending heredoc content after newline
                if hasattr(self, "_pending_heredoc_end") and self._pending_heredoc_end > self.pos:
                    self.pos = self._pending_heredoc_end
                    del self._pending_heredoc_end
                self.skip_whitespace()

            op = self.parse_list_operator()

            # Newline acts as implicit semicolon if followed by more commands
            if op is None and has_newline:
                # Check if there's another command (not a stop word)
                if (
                    not self.at_end()
                    and self.peek_word() not in stop_words
                    and self.peek() not in ")}"
                ):
                    op = "\n"  # Newline separator (distinct from explicit ;)

            if op is None:
                break

            # For & at end of list, don't require another command
            if op == "&":
                parts.append(Operator(op))
                self.skip_whitespace_and_newlines()
                if self.at_end() or self.peek_word() in stop_words or self.peek() in "\n)}":
                    break

            # For ; - check if it's a terminator before a stop word (don't include it)
            if op == ";":
                self.skip_whitespace_and_newlines()
                # Also check for ;;, ;&, or ;;& (case terminators)
                at_case_terminator = (
                    self.peek() == ";"
                    and self.pos + 1 < self.length
                    and self.source[self.pos + 1] in ";&"
                )
                if (
                    self.at_end()
                    or self.peek_word() in stop_words
                    or self.peek() in "\n)}"
                    or at_case_terminator
                ):
                    # Don't include trailing semicolon - it's just a terminator
                    break
                parts.append(Operator(op))
            elif op != "&":
                parts.append(Operator(op))

            # Check for stop words before parsing next pipeline
            self.skip_whitespace_and_newlines()
            # Also check for ;;, ;&, or ;;& (case terminators)
            if self.peek_word() in stop_words:
                break
            if (
                self.peek() == ";"
                and self.pos + 1 < self.length
                and self.source[self.pos + 1] in ";&"
            ):
                break

            pipeline = self.parse_pipeline()
            if pipeline is None:
                raise ParseError(f"Expected command after {op}", pos=self.pos)
            parts.append(pipeline)

        if len(parts) == 1:
            return parts[0]
        return List(parts)

    def parse_compound_command(self) -> Node | None:
        """Parse a compound command (subshell, brace group, if, loops, or simple command)."""
        self.skip_whitespace()
        if self.at_end():
            return None

        ch = self.peek()

        # Arithmetic command ((...)) - check before subshell
        if ch == "(" and self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
            result = self.parse_arithmetic_command()
            if result is not None:
                return result
            # Not arithmetic (e.g., '(( x ) )' is nested subshells) - fall through

        # Subshell
        if ch == "(":
            return self.parse_subshell()

        # Brace group
        if ch == "{":
            result = self.parse_brace_group()
            if result is not None:
                return result
            # Fall through to simple command if not a brace group

        # Conditional expression [[ ]] - check before reserved words
        if ch == "[" and self.pos + 1 < self.length and self.source[self.pos + 1] == "[":
            return self.parse_conditional_expr()

        # Check for reserved words
        word = self.peek_word()

        # If statement
        if word == "if":
            return self.parse_if()

        # While loop
        if word == "while":
            return self.parse_while()

        # Until loop
        if word == "until":
            return self.parse_until()

        # For loop
        if word == "for":
            return self.parse_for()

        # Select statement
        if word == "select":
            return self.parse_select()

        # Case statement
        if word == "case":
            return self.parse_case()

        # Function definition (function keyword form)
        if word == "function":
            return self.parse_function()

        # Coproc
        if word == "coproc":
            return self.parse_coproc()

        # Try POSIX function definition (name() form) before simple command
        func = self.parse_function()
        if func is not None:
            return func

        # Simple command
        return self.parse_command()

    def parse_pipeline(self) -> Node | None:
        """Parse a pipeline (commands separated by |), with optional time/negation prefix."""
        self.skip_whitespace()

        # Track order of prefixes: "time", "negation", or "time_negation" or "negation_time"
        prefix_order = None
        time_posix = False

        # Check for 'time' prefix first
        if self.peek_word() == "time":
            self.consume_word("time")
            prefix_order = "time"
            self.skip_whitespace()
            # Check for -p flag
            if not self.at_end() and self.peek() == "-":
                saved = self.pos
                self.advance()
                if not self.at_end() and self.peek() == "p":
                    self.advance()
                    if self.at_end() or self.peek() in " \t\n":
                        time_posix = True
                    else:
                        self.pos = saved
                else:
                    self.pos = saved
            self.skip_whitespace()
            # Check for -- (end of options) - implies -p per bash oracle
            if not self.at_end() and self.source[self.pos : self.pos + 2] == "--":
                if self.pos + 2 >= self.length or self.source[self.pos + 2] in " \t\n":
                    self.advance()
                    self.advance()
                    time_posix = True
                    self.skip_whitespace()
            # Skip nested time keywords (time time X collapses to time X)
            while self.peek_word() == "time":
                self.consume_word("time")
                self.skip_whitespace()
                # Check for -p after nested time
                if not self.at_end() and self.peek() == "-":
                    saved = self.pos
                    self.advance()
                    if not self.at_end() and self.peek() == "p":
                        self.advance()
                        if self.at_end() or self.peek() in " \t\n":
                            time_posix = True
                        else:
                            self.pos = saved
                    else:
                        self.pos = saved
                self.skip_whitespace()
            # Check for ! after time
            if not self.at_end() and self.peek() == "!":
                if self.pos + 1 >= self.length or self.source[self.pos + 1] in " \t\n":
                    self.advance()
                    prefix_order = "time_negation"
                    self.skip_whitespace()

        # Check for '!' negation prefix (if no time yet)
        elif not self.at_end() and self.peek() == "!":
            if self.pos + 1 >= self.length or self.source[self.pos + 1] in " \t\n":
                self.advance()
                self.skip_whitespace()
                # Recursively parse pipeline to handle ! ! cmd, ! time cmd, etc.
                # Bare ! (no following command) is valid POSIX - equivalent to false
                inner = self.parse_pipeline()
                # Double negation cancels out (! ! cmd -> cmd, ! ! -> empty command)
                if isinstance(inner, Negation):
                    return inner.pipeline if inner.pipeline is not None else Command([])
                return Negation(inner)

        # Parse the actual pipeline
        result = self._parse_simple_pipeline()

        # Wrap based on prefix order
        # Note: bare time and time ! are valid (null command timing)
        if prefix_order == "time":
            result = Time(result, time_posix)
        elif prefix_order == "negation":
            result = Negation(result)
        elif prefix_order == "time_negation":
            # time ! cmd -> Negation(Time(cmd)) per bash-oracle
            result = Time(result, time_posix)
            result = Negation(result)
        elif prefix_order == "negation_time":
            # ! time cmd -> Negation(Time(cmd))
            result = Time(result, time_posix)
            result = Negation(result)
        elif result is None:
            # No prefix and no pipeline
            return None

        return result

    def _parse_simple_pipeline(self) -> Node | None:
        """Parse a simple pipeline (commands separated by | or |&) without time/negation."""
        cmd = self.parse_compound_command()
        if cmd is None:
            return None

        commands = [cmd]

        while True:
            self.skip_whitespace()
            if self.at_end() or self.peek() != "|":
                break
            # Check it's not ||
            if self.pos + 1 < self.length and self.source[self.pos + 1] == "|":
                break

            self.advance()  # consume |

            # Check for |& (pipe stderr)
            is_pipe_both = False
            if not self.at_end() and self.peek() == "&":
                self.advance()  # consume &
                is_pipe_both = True

            self.skip_whitespace_and_newlines()  # Allow command on next line after pipe

            # Add pipe-both marker if this is a |& pipe
            if is_pipe_both:
                commands.append(PipeBoth())

            cmd = self.parse_compound_command()
            if cmd is None:
                raise ParseError("Expected command after |", pos=self.pos)
            commands.append(cmd)

        if len(commands) == 1:
            return commands[0]
        return Pipeline(commands)

    def parse_list_operator(self) -> str | None:
        """Parse a list operator (&&, ||, ;, &)."""
        self.skip_whitespace()
        if self.at_end():
            return None

        ch = self.peek()

        if ch == "&":
            # Check if this is &> or &>> (redirect), not background operator
            if self.pos + 1 < self.length and self.source[self.pos + 1] == ">":
                return None  # Let redirect parser handle &> and &>>
            self.advance()
            if not self.at_end() and self.peek() == "&":
                self.advance()
                return "&&"
            return "&"

        if ch == "|":
            if self.pos + 1 < self.length and self.source[self.pos + 1] == "|":
                self.advance()
                self.advance()
                return "||"
            return None  # single | is pipe, not list operator

        if ch == ";":
            # Don't treat ;;, ;&, or ;;& as a single semicolon (they're case terminators)
            if self.pos + 1 < self.length and self.source[self.pos + 1] in ";&":
                return None
            self.advance()
            return ";"

        return None

    def parse_list(self, newline_as_separator: bool = True) -> Node | None:
        """Parse a command list (pipelines separated by &&, ||, ;, &).

        Args:
            newline_as_separator: If True, treat newlines as implicit semicolons.
                If False, stop at newlines (for top-level parsing).
        """
        if newline_as_separator:
            self.skip_whitespace_and_newlines()
        else:
            self.skip_whitespace()
        pipeline = self.parse_pipeline()
        if pipeline is None:
            return None

        parts = [pipeline]

        while True:
            # Check for newline as implicit command separator
            self.skip_whitespace()
            has_newline = False
            while not self.at_end() and self.peek() == "\n":
                has_newline = True
                # If not treating newlines as separators, stop here
                if not newline_as_separator:
                    break
                self.advance()
                # Skip past any pending heredoc content after newline
                if hasattr(self, "_pending_heredoc_end") and self._pending_heredoc_end > self.pos:
                    self.pos = self._pending_heredoc_end
                    del self._pending_heredoc_end
                self.skip_whitespace()

            # If we hit a newline and not treating them as separators, stop
            if has_newline and not newline_as_separator:
                break

            op = self.parse_list_operator()

            # Newline acts as implicit semicolon if followed by more commands
            if op is None and has_newline:
                if not self.at_end() and self.peek() not in ")}":
                    op = "\n"  # Newline separator (distinct from explicit ;)

            if op is None:
                break

            # Don't add duplicate semicolon (e.g., explicit ; followed by newline)
            if not (
                op == ";" and parts and isinstance(parts[-1], Operator) and parts[-1].op == ";"
            ):
                parts.append(Operator(op))

            # For & at end of list, don't require another command
            if op == "&":
                self.skip_whitespace()
                if self.at_end() or self.peek() in ")}":
                    break
                # Newline after & - in compound commands, skip it (& acts as separator)
                # At top level, newline terminates (separate commands)
                if self.peek() == "\n":
                    if newline_as_separator:
                        self.skip_whitespace_and_newlines()
                        if self.at_end() or self.peek() in ")}":
                            break
                    else:
                        break  # Top-level: newline ends this list

            # For ; at end of list, don't require another command
            if op == ";":
                self.skip_whitespace()
                if self.at_end() or self.peek() in ")}":
                    break
                # Newline after ; means continue to see if more commands follow
                if self.peek() == "\n":
                    continue

            # For && and ||, allow newlines before the next command
            if op in ("&&", "||"):
                self.skip_whitespace_and_newlines()

            pipeline = self.parse_pipeline()
            if pipeline is None:
                raise ParseError(f"Expected command after {op}", pos=self.pos)
            parts.append(pipeline)

        if len(parts) == 1:
            return parts[0]
        return List(parts)

    def parse_comment(self) -> Node | None:
        """Parse a comment (# to end of line)."""
        from .ast import Comment

        if self.at_end() or self.peek() != "#":
            return None
        start = self.pos
        while not self.at_end() and self.peek() != "\n":
            self.advance()
        text = self.source[start : self.pos]
        return Comment(text)

    def parse(self) -> list[Node]:
        """Parse the entire input."""
        source = self.source.strip()
        if not source:
            return [Empty()]

        results = []

        # Skip leading comments (bash-oracle doesn't output them)
        while True:
            self.skip_whitespace()
            # Skip newlines but not comments
            while not self.at_end() and self.peek() == "\n":
                self.advance()
            if self.at_end():
                break
            comment = self.parse_comment()
            if not comment:
                break
            # Don't add to results - bash-oracle doesn't output comments

        # Parse statements separated by newlines as separate top-level nodes
        while not self.at_end():
            result = self.parse_list(newline_as_separator=False)
            if result is not None:
                results.append(result)

            self.skip_whitespace()

            # Skip newlines (and any pending heredoc content) between statements
            found_newline = False
            while not self.at_end() and self.peek() == "\n":
                found_newline = True
                self.advance()
                # Skip past any pending heredoc content after newline
                if hasattr(self, "_pending_heredoc_end") and self._pending_heredoc_end > self.pos:
                    self.pos = self._pending_heredoc_end
                    del self._pending_heredoc_end
                self.skip_whitespace()

            # If no newline and not at end, we have unparsed content
            if not found_newline and not self.at_end():
                raise ParseError("Parser not fully implemented yet", pos=self.pos)

        if not results:
            return [Empty()]

        return results


def parse(source: str) -> list[Node]:
    """
    Parse bash source code and return a list of AST nodes.

    Args:
        source: The bash source code to parse.

    Returns:
        A list of AST nodes representing the parsed code.

    Raises:
        ParseError: If the source code cannot be parsed.
    """
    parser = Parser(source)
    return parser.parse()
