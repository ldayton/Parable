"""Recursive descent parser for bash."""

from .ast import (
    AnsiCQuote,
    ArithAssign,
    ArithBinaryOp,
    ArithComma,
    ArithDeprecated,
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
        """Skip spaces and tabs (but not newlines for now)."""
        while not self.at_end() and self.peek() in " \t":
            self.advance()

    def skip_whitespace_and_newlines(self) -> None:
        """Skip spaces, tabs, and newlines."""
        while not self.at_end() and self.peek() in " \t\n":
            self.advance()

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

    def parse_word(self) -> Word | None:
        """Parse a word token, detecting parameter expansions and command substitutions."""
        self.skip_whitespace()

        if self.at_end():
            return None

        start = self.pos
        chars = []
        parts = []

        while not self.at_end():
            ch = self.peek()

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

            # Metacharacter ends the word
            elif ch in METACHAR:
                break

            # Regular character
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

        # Find closing backtick (no nesting for backticks)
        content_start = self.pos
        while not self.at_end() and self.peek() != "`":
            c = self.peek()
            # Handle escaped backtick
            if c == "\\" and self.pos + 1 < self.length and self.source[self.pos + 1] == "`":
                self.advance()  # backslash
                self.advance()  # escaped backtick
            else:
                self.advance()

        if self.at_end():
            self.pos = start
            return None, ""

        content = self.source[content_start : self.pos]
        self.advance()  # consume closing `

        text = self.source[start : self.pos]

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
            if_true = self._arith_parse_ternary()  # right associative
            self._arith_skip_ws()
            if not self._arith_consume(":"):
                raise ParseError("Expected ':' in ternary", pos=self._arith_pos)
            self._arith_skip_ws()
            if_false = self._arith_parse_ternary()  # right associative
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

        # Parameter expansion ${...} or $var
        if c == "$":
            return self._arith_parse_expansion()

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
                # Escape sequence
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

        text = self.source[start : self.pos]
        content = "".join(content_chars)
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
            self.pos = start
            return None, ""

        # Parse argument (everything until closing brace)
        # Only ${...} increases depth, not plain {
        arg_chars = []
        depth = 1
        while not self.at_end() and depth > 0:
            c = self.peek()
            if c == "$" and self.pos + 1 < self.length and self.source[self.pos + 1] == "{":
                # Nested ${...} - increase depth
                depth += 1
                arg_chars.append(self.advance())  # $
                arg_chars.append(self.advance())  # {
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

        if depth != 0:
            self.pos = start
            return None, ""

        self.advance()  # consume final }
        arg = "".join(arg_chars)
        text = self.source[start : self.pos]
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
                    # Array subscript
                    name_chars.append(self.advance())
                    while not self.at_end() and self.peek() != "]":
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

        # Check for variable fd {varname} before redirect
        if self.peek() == "{":
            saved = self.pos
            self.advance()  # consume {
            varname_chars = []
            while not self.at_end() and self.peek() not in "}<>":
                ch = self.peek()
                if ch.isalnum() or ch == "_":
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
            fd = int(self.peek())
            self.advance()

        ch = self.peek()

        # Handle &> and &>> (redirect both stdout and stderr)
        if ch == "&" and self.pos + 1 < self.length and self.source[self.pos + 1] == ">":
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

        # Handle fd duplication targets like &1, &2, &-, &0-, &$var
        if not self.at_end() and self.peek() == "&":
            self.advance()  # consume &
            # Parse the fd number or - for close, including move syntax like &0-
            if not self.at_end() and (self.peek().isdigit() or self.peek() == "-"):
                fd_target = self.advance()
                # Check for move syntax: &N- means duplicate and close (move)
                if fd_target.isdigit() and not self.at_end() and self.peek() == "-":
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

        # Parse the delimiter, handling quoting
        quoted = False
        delimiter_chars = []

        # Check for quoting of delimiter
        if not self.at_end():
            ch = self.peek()
            if ch == '"':
                quoted = True
                self.advance()
                while not self.at_end() and self.peek() != '"':
                    delimiter_chars.append(self.advance())
                if not self.at_end():
                    self.advance()  # closing "
            elif ch == "'":
                quoted = True
                self.advance()
                while not self.at_end() and self.peek() != "'":
                    delimiter_chars.append(self.advance())
                if not self.at_end():
                    self.advance()  # closing '
            elif ch == "\\":
                quoted = True
                self.advance()  # skip backslash
                # Read unquoted delimiter
                while not self.at_end() and self.peek() not in " \t\n;|&<>()":
                    delimiter_chars.append(self.advance())
            else:
                # Unquoted delimiter - but check for partial quoting
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
                        quoted = True
                        self.advance()
                        if not self.at_end():
                            delimiter_chars.append(self.advance())
                    else:
                        delimiter_chars.append(self.advance())

        delimiter = "".join(delimiter_chars)
        if not delimiter:
            raise ParseError("Expected delimiter for here document", pos=self.pos)

        # Find the end of the current line (command continues until newline)
        # We need to mark where the heredoc content starts
        line_end = self.pos
        while line_end < self.length and self.source[line_end] != "\n":
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

            # Add line to content
            if strip_tabs:
                content_lines.append(line.lstrip("\t"))
            else:
                content_lines.append(line)

            # Move past the newline
            scan_pos = line_end + 1 if line_end < self.length else self.length

        # Join content with newlines
        if content_lines:
            content = "\n".join(content_lines) + "\n"
        else:
            content = ""

        # Store the position where heredoc content ends so we can skip it later
        # scan_pos is at the start of the delimiter line, need to move past it
        heredoc_end = scan_pos
        while heredoc_end < self.length and self.source[heredoc_end] != "\n":
            heredoc_end += 1
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
            # } is only a terminator when it's a standalone word (brace group closer)
            # }}} or }foo are regular words
            if self.peek() == "}":
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
            word = self.parse_word()
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
        """Parse an arithmetic command (( expression )) with parsed internals."""
        self.skip_whitespace()

        # Check for ((
        if (
            self.at_end()
            or self.peek() != "("
            or self.pos + 1 >= self.length
            or self.source[self.pos + 1] != "("
        ):
            return None

        self.advance()  # consume first (
        self.advance()  # consume second (

        # Find matching )) - track nested parens
        content_start = self.pos
        depth = 1

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
                self.advance()
            else:
                self.advance()

        if self.at_end() or depth != 1:
            raise ParseError("Expected )) to close arithmetic command", pos=self.pos)

        content = self.source[content_start : self.pos]
        self.advance()  # consume first )
        self.advance()  # consume second )

        # Parse the arithmetic expression
        expr = self._parse_arith_expr(content)
        return ArithmeticCommand(expr)

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

        return ConditionalExpr(body)

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
        """Parse: or_expr = and_expr (|| and_expr)*"""
        self._cond_skip_whitespace()
        left = self._parse_cond_and()

        while True:
            self._cond_skip_whitespace()
            if self._cond_at_end():
                break
            if (
                self.peek() == "|"
                and self.pos + 1 < self.length
                and self.source[self.pos + 1] == "|"
            ):
                self.advance()  # consume first |
                self.advance()  # consume second |
                right = self._parse_cond_and()
                left = CondOr(left, right)
            else:
                break

        return left

    def _parse_cond_and(self) -> Node:
        """Parse: and_expr = term (&& term)*"""
        self._cond_skip_whitespace()
        left = self._parse_cond_term()

        while True:
            self._cond_skip_whitespace()
            if self._cond_at_end():
                break
            if (
                self.peek() == "&"
                and self.pos + 1 < self.length
                and self.source[self.pos + 1] == "&"
            ):
                self.advance()  # consume first &
                self.advance()  # consume second &
                right = self._parse_cond_term()
                left = CondAnd(left, right)
            else:
                break

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
            return inner

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
        # ! alone (followed by space) is negation, but != is a binary operator
        if c == "!" and self.pos + 1 < self.length and self.source[self.pos + 1] in " \t":
            return None
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

            # Parameter expansion $var or ${...}
            if ch == "$":
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

            if not words:
                raise ParseError("Expected words after 'in'", pos=self.pos)

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
                        # End of ((...))
                        parts.append("".join(current).strip())
                        self.advance()  # consume first )
                        self.advance()  # consume second )
                        break
                    else:
                        current.append(self.advance())
            elif ch == ";" and paren_depth == 0:
                parts.append("".join(current).strip())
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
            body = self.parse_brace_group()
            if body is None:
                raise ParseError("Expected brace group body in for loop", pos=self.pos)
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
            body = self.parse_brace_group()
            if body is None:
                raise ParseError("Expected brace group body in select", pos=self.pos)
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
                    # Backslash escape - consume both chars
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
                    # Character class - consume until ]
                    pattern_chars.append(self.advance())
                    # Handle [! or [^ at start
                    if not self.at_end() and self.peek() in "!^":
                        pattern_chars.append(self.advance())
                    # Handle ] as first char (literal)
                    if not self.at_end() and self.peek() == "]":
                        pattern_chars.append(self.advance())
                    # Consume until closing ]
                    while not self.at_end() and self.peek() != "]":
                        pattern_chars.append(self.advance())
                    if not self.at_end():
                        pattern_chars.append(self.advance())  # ]
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
                    # Skip whitespace (including newlines) in pattern but don't include
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

        return Case(word, patterns)

    def parse_coproc(self) -> Coproc | None:
        """Parse a coproc statement.

        Forms:
            coproc command                    # default name COPROC
            coproc NAME command               # named coprocess
            coproc compound_command           # with compound command
            coproc NAME compound_command      # named with compound
        """
        self.skip_whitespace()
        if self.at_end():
            return None

        if self.peek_word() != "coproc":
            return None

        self.consume_word("coproc")
        self.skip_whitespace()

        # Check if next word is a NAME (followed by a command)
        # NAME is uppercase by convention but can be any valid identifier
        name = None

        # Check for compound command first (brace group or subshell)
        ch = self.peek() if not self.at_end() else None
        if ch == "{":
            body = self.parse_brace_group()
            if body is not None:
                return Coproc(body, name)
        if ch == "(":
            # Check for (( arithmetic command
            if self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
                body = self.parse_arithmetic_command()
                if body is not None:
                    return Coproc(body, name)
            body = self.parse_subshell()
            if body is not None:
                return Coproc(body, name)

        # Check for reserved word compounds (while, for, if, etc.)
        next_word = self.peek_word()
        if next_word in ("while", "until", "for", "if", "case"):
            body = self.parse_compound_command()
            if body is not None:
                return Coproc(body, name)

        # Could be NAME followed by command, or just a simple command
        # Try to get the first word
        first_word = self.peek_word()
        if first_word is None:
            raise ParseError("Expected command after coproc", pos=self.pos)

        # Save position and try to parse as NAME + command
        word_start = self.pos
        self.skip_whitespace()

        # Consume the first word
        while not self.at_end() and self.peek() not in METACHAR and self.peek() not in "\"'":
            self.advance()

        potential_name = self.source[word_start : self.pos]
        self.skip_whitespace()

        # If there's more after the first word, check if first word is NAME
        if not self.at_end() and self.peek() not in "\n;|&":
            # Check if there's an actual command following
            next_ch = self.peek()
            if next_ch == "{":
                # coproc NAME { ... } - first word is NAME
                name = potential_name
                body = self.parse_brace_group()
                if body is not None:
                    return Coproc(body, name)
            elif next_ch == "(":
                # coproc NAME ( ... ) - first word is NAME
                name = potential_name
                if self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
                    body = self.parse_arithmetic_command()
                else:
                    body = self.parse_subshell()
                if body is not None:
                    return Coproc(body, name)

            next_word = self.peek_word()
            # If the next word starts with '-', it's an option to first word (command)
            # If the next word is a reserved word compound, first word is NAME
            # Otherwise, if next word looks like a command name, first word is NAME
            if next_word:
                if next_word.startswith("-"):
                    # -n, -x, etc. are options, so first word is command
                    pass
                elif next_word in ("while", "until", "for", "if", "case"):
                    # Reserved compound follows, so first word is NAME
                    name = potential_name
                    body = self.parse_compound_command()
                    if body is not None:
                        return Coproc(body, name)
                elif next_word not in RESERVED_WORDS:
                    # Regular word follows, so first word is NAME
                    name = potential_name
                    body = self.parse_command()
                    if body is not None:
                        return Coproc(body, name)

        # Otherwise, first word is the start of the simple command
        # Restore position and parse as simple command
        self.pos = word_start
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
                    op = ";"  # Treat newline as semicolon

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
            return self.parse_arithmetic_command()

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
                inner = self.parse_pipeline()
                if inner is None:
                    raise ParseError("Expected command after !", pos=self.pos)
                return Negation(inner)

        # Parse the actual pipeline
        result = self._parse_simple_pipeline()
        if result is None:
            if prefix_order:
                raise ParseError("Expected command after time/!", pos=self.pos)
            return None

        # Wrap based on prefix order
        if prefix_order == "time":
            result = Time(result, time_posix)
        elif prefix_order == "negation":
            result = Negation(result)
        elif prefix_order == "time_negation":
            # time ! cmd -> Time(Negation(cmd))
            result = Negation(result)
            result = Time(result, time_posix)
        elif prefix_order == "negation_time":
            # ! time cmd -> Negation(Time(cmd))
            result = Time(result, time_posix)
            result = Negation(result)

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

    def parse_list(self) -> Node | None:
        """Parse a command list (pipelines separated by &&, ||, ;, &)."""
        self.skip_whitespace_and_newlines()
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
                if not self.at_end() and self.peek() not in ")}":
                    op = ";"  # Treat newline as semicolon

            if op is None:
                break

            parts.append(Operator(op))

            # For & at end of list, don't require another command
            if op == "&":
                self.skip_whitespace()
                if self.at_end() or self.peek() in ")}":
                    break
                # Newline after & means continue to see if more commands follow
                if self.peek() == "\n":
                    continue

            # For ; at end of list, don't require another command
            if op == ";":
                self.skip_whitespace()
                if self.at_end() or self.peek() in ")}":
                    break
                # Newline after ; means continue to see if more commands follow
                if self.peek() == "\n":
                    continue

            pipeline = self.parse_pipeline()
            if pipeline is None:
                raise ParseError(f"Expected command after {op}", pos=self.pos)
            parts.append(pipeline)

        if len(parts) == 1:
            return parts[0]
        return List(parts)

    def parse(self) -> list[Node]:
        """Parse the entire input."""
        source = self.source.strip()
        if not source:
            return [Empty()]

        result = self.parse_list()
        if result is None:
            raise ParseError("Expected command", pos=self.pos)

        self.skip_whitespace()

        # Skip trailing newlines and any pending heredoc content
        while not self.at_end() and self.peek() == "\n":
            self.advance()
            # Skip past any pending heredoc content after newline
            if hasattr(self, "_pending_heredoc_end") and self._pending_heredoc_end > self.pos:
                self.pos = self._pending_heredoc_end
                del self._pending_heredoc_end

        if not self.at_end():
            # There's more content - not yet supported
            raise ParseError("Parser not fully implemented yet", pos=self.pos)

        return [result]


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
