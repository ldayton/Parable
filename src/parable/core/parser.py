"""Recursive descent parser for bash."""

from .ast import (
    BraceGroup,
    Case,
    CasePattern,
    Command,
    Empty,
    For,
    If,
    List,
    Node,
    Operator,
    Pipeline,
    Redirect,
    Subshell,
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
    "do",
    "done",
    "case",
    "esac",
    "in",
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
        """Parse a word token."""
        self.skip_whitespace()

        if self.at_end():
            return None

        start = self.pos
        chars = []

        while not self.at_end():
            ch = self.peek()

            # Single-quoted string
            if ch == "'":
                self.advance()  # consume opening quote
                chars.append("'")
                while not self.at_end() and self.peek() != "'":
                    chars.append(self.advance())
                if self.at_end():
                    raise ParseError("Unterminated single quote", pos=start)
                chars.append(self.advance())  # consume closing quote

            # Double-quoted string
            elif ch == '"':
                self.advance()  # consume opening quote
                chars.append('"')
                while not self.at_end() and self.peek() != '"':
                    c = self.peek()
                    # Handle escape sequences in double quotes
                    if c == "\\" and self.pos + 1 < self.length:
                        chars.append(self.advance())  # backslash
                        chars.append(self.advance())  # escaped char
                    # Handle nested command substitution in double quotes
                    elif (
                        c == "$" and self.pos + 1 < self.length and self.source[self.pos + 1] == "("
                    ):
                        chars.append(self.advance())  # $
                        chars.append(self.advance())  # (
                        depth = 1
                        while not self.at_end() and depth > 0:
                            nc = self.peek()
                            if nc == "(":
                                depth += 1
                            elif nc == ")":
                                depth -= 1
                            chars.append(self.advance())
                    else:
                        chars.append(self.advance())
                if self.at_end():
                    raise ParseError("Unterminated double quote", pos=start)
                chars.append(self.advance())  # consume closing quote

            # Command substitution $(...) - parse as unit
            elif ch == "$" and self.pos + 1 < self.length and self.source[self.pos + 1] == "(":
                chars.append(self.advance())  # $
                chars.append(self.advance())  # (
                depth = 1
                while not self.at_end() and depth > 0:
                    nc = self.peek()
                    if nc == "(":
                        depth += 1
                    elif nc == ")":
                        depth -= 1
                    chars.append(self.advance())

            # Metacharacter ends the word
            elif ch in METACHAR:
                break

            # Regular character
            else:
                chars.append(self.advance())

        if not chars:
            return None

        return Word("".join(chars))

    def parse_redirect(self) -> Redirect | None:
        """Parse a redirection operator and target."""
        self.skip_whitespace()
        if self.at_end():
            return None

        start = self.pos
        fd = None

        # Check for optional fd number before redirect
        if self.peek() and self.peek().isdigit():
            fd = int(self.peek())
            self.advance()

        ch = self.peek()
        if ch is None or ch not in "<>":
            # Not a redirect, restore position
            self.pos = start
            return None

        # Parse the redirect operator
        op = self.advance()

        # Check for multi-char operators
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
                else:
                    op = "<<"
            # Handle >| (noclobber override)
            elif op == ">" and next_ch == "|":
                self.advance()
                op = ">|"
            # Only consume >& or <& as operators if NOT followed by a digit
            # (>&2 should be > with target &2, not >& with target 2)
            elif fd is None and op == ">" and next_ch == "&":
                # Peek ahead to see if there's a digit after &
                if self.pos + 1 >= self.length or not self.source[self.pos + 1].isdigit():
                    self.advance()
                    op = ">&"
            elif fd is None and op == "<" and next_ch == "&":
                if self.pos + 1 >= self.length or not self.source[self.pos + 1].isdigit():
                    self.advance()
                    op = "<&"

        # Combine fd with operator if present
        if fd is not None:
            op = f"{fd}{op}"

        self.skip_whitespace()

        # Handle fd duplication targets like &1, &2
        if not self.at_end() and self.peek() == "&":
            start_target = self.pos
            self.advance()  # consume &
            # Parse the fd number
            if not self.at_end() and self.peek().isdigit():
                fd_target = self.advance()
                target = Word(f"&{fd_target}")
            else:
                # Not a valid fd dup, restore
                self.pos = start_target
                target = self.parse_word()
        else:
            target = self.parse_word()

        if target is None:
            raise ParseError(f"Expected target for redirect {op}", pos=self.pos)

        return Redirect(op, target)

    def parse_command(self) -> Command | None:
        """Parse a simple command (sequence of words and redirections)."""
        words = []
        redirects = []

        while True:
            self.skip_whitespace()
            if self.at_end() or self.peek() in "\n|&;()":
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

        return Subshell(body)

    def parse_brace_group(self) -> BraceGroup | None:
        """Parse a brace group { list }."""
        self.skip_whitespace()
        if self.at_end() or self.peek() != "{":
            return None

        # Check that { is followed by whitespace (it's a reserved word)
        if self.pos + 1 < self.length and self.source[self.pos + 1] not in " \t\n":
            return None

        self.advance()  # consume {

        body = self.parse_list()
        if body is None:
            raise ParseError("Expected command in brace group", pos=self.pos)

        self.skip_whitespace()
        if self.at_end() or self.peek() != "}":
            raise ParseError("Expected } to close brace group", pos=self.pos)
        self.advance()  # consume }

        return BraceGroup(body)

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

        return If(condition, then_body, else_body)

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

        return While(condition, body)

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

        return Until(condition, body)

    def parse_for(self) -> For | None:
        """Parse a for loop: for name [in words]; do list; done."""
        self.skip_whitespace()

        if self.peek_word() != "for":
            return None

        self.consume_word("for")
        self.skip_whitespace()

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

        return For(var_name, words, body)

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

            # Parse pattern (everything until ')')
            # Pattern can contain | for alternation, quotes, globs, etc.
            pattern_chars = []
            while not self.at_end():
                ch = self.peek()
                if ch == ")":
                    self.advance()  # consume )
                    break
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

            # Parse commands until ;; or esac
            # Commands are optional (can have empty body)
            self.skip_whitespace()

            body = None
            # Check for empty body: ;; right after pattern
            is_empty_body = (
                not self.at_end()
                and self.peek() == ";"
                and self.pos + 1 < self.length
                and self.source[self.pos + 1] == ";"
            )

            if not is_empty_body:
                # Skip newlines and check if there's content before ;; or esac
                self.skip_whitespace_and_newlines()
                if not self.at_end() and self.peek_word() != "esac":
                    # Check again for ;; after whitespace/newlines
                    is_at_terminator = (
                        self.peek() == ";"
                        and self.pos + 1 < self.length
                        and self.source[self.pos + 1] == ";"
                    )
                    if not is_at_terminator:
                        body = self.parse_list_until({"esac"})
                        self.skip_whitespace()

            # Handle ;; terminator
            if not self.at_end() and self.peek() == ";":
                self.advance()
                if not self.at_end() and self.peek() == ";":
                    self.advance()  # consume second ;

            self.skip_whitespace_and_newlines()

            patterns.append(CasePattern(pattern, body))

        # Expect 'esac'
        self.skip_whitespace_and_newlines()
        if not self.consume_word("esac"):
            raise ParseError("Expected 'esac' to close case statement", pos=self.pos)

        return Case(word, patterns)

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
                # Also check for ;; (case terminator)
                at_case_terminator = (
                    self.peek() == ";"
                    and self.pos + 1 < self.length
                    and self.source[self.pos + 1] == ";"
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
            # Also check for ;; (case terminator)
            if self.peek_word() in stop_words:
                break
            if (
                self.peek() == ";"
                and self.pos + 1 < self.length
                and self.source[self.pos + 1] == ";"
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

        # Subshell
        if ch == "(":
            return self.parse_subshell()

        # Brace group
        if ch == "{":
            result = self.parse_brace_group()
            if result is not None:
                return result
            # Fall through to simple command if not a brace group

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

        # Case statement
        if word == "case":
            return self.parse_case()

        # Simple command
        return self.parse_command()

    def parse_pipeline(self) -> Node | None:
        """Parse a pipeline (commands separated by |)."""
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
            self.skip_whitespace()

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
            # Don't treat ;; as a single semicolon (it's a case terminator)
            if self.pos + 1 < self.length and self.source[self.pos + 1] == ";":
                return None
            self.advance()
            return ";"

        return None

    def parse_list(self) -> Node | None:
        """Parse a command list (pipelines separated by &&, ||, ;, &)."""
        pipeline = self.parse_pipeline()
        if pipeline is None:
            return None

        parts = [pipeline]

        while True:
            op = self.parse_list_operator()
            if op is None:
                break

            parts.append(Operator(op))

            # For & at end of list, don't require another command
            if op == "&":
                self.skip_whitespace()
                if self.at_end() or self.peek() in "\n)}":
                    break

            # For ; at end of list, don't require another command
            if op == ";":
                self.skip_whitespace()
                if self.at_end() or self.peek() in "\n)}":
                    break

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

        # Skip trailing newlines
        while not self.at_end() and self.peek() == "\n":
            self.advance()

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
