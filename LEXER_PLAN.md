# Incremental Plan: Adding a Lexer Layer to Parable

This plan adds a lexer layer to `parable.py` incrementally. After each increment:
1. Run `just test` (Python tests pass)
2. Run `just transpile` (generates parable.js)
3. Run `just test-js` (JavaScript tests pass)
4. Commit the changes

## Overview

The lexer will be a "pull" lexer - the Parser calls `next_token()` when it needs a token. This allows incremental migration: Parser can use Lexer for some constructs while still doing direct parsing for others.

---

## Phase 1: Token Infrastructure (No Behavior Change)

### Increment 1.1: Add TokenType constants

Add token type constants as class-level integers. These mirror bash's token types.

```python
class TokenType:
    EOF = 0
    WORD = 1
    NEWLINE = 2

    # Operators (single char)
    SEMI = 10        # ;
    PIPE = 11        # |
    AMP = 12         # &
    LPAREN = 13      # (
    RPAREN = 14      # )
    LBRACE = 15      # {
    RBRACE = 16      # }
    LESS = 17        # <
    GREATER = 18     # >

    # Multi-char operators
    AND_AND = 30     # &&
    OR_OR = 31       # ||
    SEMI_SEMI = 32   # ;;
    SEMI_AMP = 33    # ;&
    SEMI_SEMI_AMP = 34  # ;;&
    LESS_LESS = 35   # <<
    GREATER_GREATER = 36  # >>
    LESS_AMP = 37    # <&
    GREATER_AMP = 38 # >&
    LESS_GREATER = 39    # <>
    GREATER_PIPE = 40    # >|
    LESS_LESS_MINUS = 41 # <<-
    LESS_LESS_LESS = 42  # <<<
    AMP_GREATER = 43     # &>
    AMP_GREATER_GREATER = 44  # &>>
    PIPE_AMP = 45    # |&

    # Reserved words (recognized contextually)
    IF = 50
    THEN = 51
    ELSE = 52
    ELIF = 53
    FI = 54
    CASE = 55
    ESAC = 56
    FOR = 57
    WHILE = 58
    UNTIL = 59
    DO = 60
    DONE = 61
    IN = 62
    FUNCTION = 63
    SELECT = 64
    COPROC = 65
    TIME = 66
    BANG = 67        # ! (reserved word context)
    LBRACKET_LBRACKET = 68  # [[
    RBRACKET_RBRACKET = 69  # ]]

    # Special
    ASSIGNMENT_WORD = 80
    NUMBER = 81      # fd number before redirect
```

**Test:** All tests pass (no behavior change)
**Commit:** "feat: add TokenType constants for lexer"

---

### Increment 1.2: Add Token class

Add Token dataclass to hold tokenized results.

```python
class Token:
    def __init__(self, type_: int, value: str, pos: int):
        self.type = type_
        self.value = value
        self.pos = pos  # Position in source where token starts

    def __repr__(self) -> str:
        return f"Token({self.type}, {self.value!r}, {self.pos})"
```

**Test:** All tests pass (no behavior change)
**Commit:** "feat: add Token class for lexer output"

---

### Increment 1.3: Add LexerState flags

Add LEX_* style flags as constants. These track lexer state during tokenization.

```python
class LexerState:
    NONE = 0
    WASDOL = 0x0001      # Previous char was $
    CKCOMMENT = 0x0002   # Check for # comments
    INCOMMENT = 0x0004   # Currently in comment
    PASSNEXT = 0x0008    # Next char is escaped (after backslash)
    INHEREDOC = 0x0080   # In here-document body
    HEREDELIM = 0x0100   # Reading here-doc delimiter
    STRIPDOC = 0x0200    # <<- strips tabs
    QUOTEDDOC = 0x0400   # Here-doc delimiter was quoted
    INWORD = 0x0800      # Building a word
```

**Test:** All tests pass (no behavior change)
**Commit:** "feat: add LexerState flags for lexer context"

---

## Phase 2: Lexer Class Skeleton

### Increment 2.1: Create empty Lexer class

Add Lexer class with basic structure but no functionality. Parser doesn't use it yet.

```python
class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.length = len(source)
        self.state = LexerState.CKCOMMENT  # Start checking for comments
        self.quote = QuoteState()
        self._token_cache: Token | None = None

    def peek(self) -> str | None:
        """Return current character without consuming."""
        if self.pos >= self.length:
            return None
        return self.source[self.pos]

    def advance(self) -> str | None:
        """Consume and return current character."""
        if self.pos >= self.length:
            return None
        c = self.source[self.pos]
        self.pos += 1
        return c

    def at_end(self) -> bool:
        return self.pos >= self.length
```

**Test:** All tests pass (no behavior change)
**Commit:** "feat: add Lexer class skeleton"

---

### Increment 2.2: Add character classification methods to Lexer

Move/duplicate character classification methods into Lexer.

```python
class Lexer:
    # ... existing methods ...

    def is_metachar(self, c: str) -> bool:
        """Return True if c is a shell metacharacter."""
        return c in "|&;()<> \t\n"

    def is_operator_start(self, c: str) -> bool:
        """Return True if c can start an operator."""
        return c in "|&;<>()"

    def is_blank(self, c: str) -> bool:
        """Return True if c is blank (space or tab)."""
        return c == " " or c == "\t"
```

**Test:** All tests pass (no behavior change)
**Commit:** "feat: add character classification methods to Lexer"

---

## Phase 3: Implement Basic Tokenization (Operators Only)

### Increment 3.1: Implement operator tokenization

Add method to recognize and return operator tokens.

```python
class Lexer:
    # ... existing ...

    def _read_operator(self) -> Token | None:
        """Try to read an operator token. Returns None if not at operator."""
        start = self.pos
        c = self.peek()
        if c is None:
            return None

        # Check two-char operators first
        two = self.source[self.pos:self.pos + 2] if self.pos + 1 < self.length else ""
        three = self.source[self.pos:self.pos + 3] if self.pos + 2 < self.length else ""

        # Three-char operators
        if three == ";;&":
            self.pos += 3
            return Token(TokenType.SEMI_SEMI_AMP, three, start)
        if three == "<<-":
            self.pos += 3
            return Token(TokenType.LESS_LESS_MINUS, three, start)
        if three == "<<<":
            self.pos += 3
            return Token(TokenType.LESS_LESS_LESS, three, start)
        if three == "&>>":
            self.pos += 3
            return Token(TokenType.AMP_GREATER_GREATER, three, start)

        # Two-char operators
        if two == "&&":
            self.pos += 2
            return Token(TokenType.AND_AND, two, start)
        if two == "||":
            self.pos += 2
            return Token(TokenType.OR_OR, two, start)
        if two == ";;":
            self.pos += 2
            return Token(TokenType.SEMI_SEMI, two, start)
        if two == ";&":
            self.pos += 2
            return Token(TokenType.SEMI_AMP, two, start)
        if two == "<<":
            self.pos += 2
            return Token(TokenType.LESS_LESS, two, start)
        if two == ">>":
            self.pos += 2
            return Token(TokenType.GREATER_GREATER, two, start)
        if two == "<&":
            self.pos += 2
            return Token(TokenType.LESS_AMP, two, start)
        if two == ">&":
            self.pos += 2
            return Token(TokenType.GREATER_AMP, two, start)
        if two == "<>":
            self.pos += 2
            return Token(TokenType.LESS_GREATER, two, start)
        if two == ">|":
            self.pos += 2
            return Token(TokenType.GREATER_PIPE, two, start)
        if two == "&>":
            self.pos += 2
            return Token(TokenType.AMP_GREATER, two, start)
        if two == "|&":
            self.pos += 2
            return Token(TokenType.PIPE_AMP, two, start)

        # Single-char operators
        if c == ";":
            self.pos += 1
            return Token(TokenType.SEMI, c, start)
        if c == "|":
            self.pos += 1
            return Token(TokenType.PIPE, c, start)
        if c == "&":
            self.pos += 1
            return Token(TokenType.AMP, c, start)
        if c == "(":
            self.pos += 1
            return Token(TokenType.LPAREN, c, start)
        if c == ")":
            self.pos += 1
            return Token(TokenType.RPAREN, c, start)
        if c == "<":
            self.pos += 1
            return Token(TokenType.LESS, c, start)
        if c == ">":
            self.pos += 1
            return Token(TokenType.GREATER, c, start)
        if c == "\n":
            self.pos += 1
            return Token(TokenType.NEWLINE, c, start)

        return None
```

**Test:** All tests pass (no behavior change - method exists but isn't called)
**Commit:** "feat: implement operator tokenization in Lexer"

---

### Increment 3.2: Add skip_blanks method

```python
class Lexer:
    def skip_blanks(self) -> None:
        """Skip spaces and tabs (not newlines)."""
        while self.pos < self.length:
            c = self.source[self.pos]
            if c != " " and c != "\t":
                break
            self.pos += 1
```

**Test:** All tests pass (no behavior change)
**Commit:** "feat: add skip_blanks to Lexer"

---

### Increment 3.3: Implement comment handling

```python
class Lexer:
    def _skip_comment(self) -> bool:
        """Skip comment if at # in comment-allowed context. Returns True if skipped."""
        if self.pos >= self.length:
            return False
        if self.source[self.pos] != "#":
            return False
        if self.quote.in_quotes():
            return False
        # Check if in comment-allowed position (start of line or after blank/meta)
        if self.pos > 0:
            prev = self.source[self.pos - 1]
            if prev not in " \t\n;|&(){}":
                return False
        # Skip to end of line
        while self.pos < self.length and self.source[self.pos] != "\n":
            self.pos += 1
        return True
```

**Test:** All tests pass (no behavior change)
**Commit:** "feat: add comment handling to Lexer"

---

## Phase 4: Word Tokenization (Complex)

### Increment 4.1: Add word boundary detection

```python
class Lexer:
    def is_word_char(self, c: str) -> bool:
        """Return True if c can be part of an unquoted word."""
        if c is None:
            return False
        return not self.is_metachar(c)
```

**Test:** All tests pass (no behavior change)
**Commit:** "feat: add word boundary detection to Lexer"

---

### Increment 4.2: Implement basic word tokenization (unquoted only)

This is a simplified word reader that doesn't handle quotes or expansions - those will be added incrementally.

```python
class Lexer:
    def _read_word_simple(self) -> Token | None:
        """Read a simple unquoted word (no quotes, no expansions)."""
        start = self.pos
        if self.pos >= self.length:
            return None
        c = self.peek()
        if c is None or self.is_metachar(c):
            return None

        chars = []
        while self.pos < self.length:
            c = self.source[self.pos]
            if self.is_metachar(c):
                break
            if c == "\\":
                # Escape handling
                chars.append(c)
                self.pos += 1
                if self.pos < self.length:
                    chars.append(self.source[self.pos])
                    self.pos += 1
                continue
            if c == "'" or c == '"':
                # For now, just accumulate - full quote handling comes later
                chars.append(c)
                self.pos += 1
                continue
            chars.append(c)
            self.pos += 1

        if not chars:
            return None
        return Token(TokenType.WORD, "".join(chars), start)
```

**Test:** All tests pass (no behavior change)
**Commit:** "feat: add basic word tokenization to Lexer"

---

### Increment 4.3: Add single quote handling to Lexer

```python
class Lexer:
    def _scan_single_quoted(self) -> str:
        """Scan content inside single quotes. Caller has consumed opening quote."""
        chars = ["'"]
        while self.pos < self.length:
            c = self.source[self.pos]
            chars.append(c)
            self.pos += 1
            if c == "'":
                break
        return "".join(chars)
```

**Test:** All tests pass (no behavior change)
**Commit:** "feat: add single quote handling to Lexer"

---

### Increment 4.4: Add double quote handling to Lexer

```python
class Lexer:
    def _scan_double_quoted(self) -> str:
        """Scan content inside double quotes. Caller has consumed opening quote."""
        chars = ['"']
        while self.pos < self.length:
            c = self.source[self.pos]
            if c == "\\":
                chars.append(c)
                self.pos += 1
                if self.pos < self.length:
                    chars.append(self.source[self.pos])
                    self.pos += 1
                continue
            chars.append(c)
            self.pos += 1
            if c == '"':
                break
        return "".join(chars)
```

**Test:** All tests pass (no behavior change)
**Commit:** "feat: add double quote handling to Lexer"

---

### Increment 4.5: Integrate quote handling into word tokenization

Update `_read_word_simple` to properly handle quotes.

```python
class Lexer:
    def _read_word(self) -> Token | None:
        """Read a word token, handling quotes."""
        start = self.pos
        if self.pos >= self.length:
            return None
        c = self.peek()
        if c is None or self.is_metachar(c):
            return None

        chars = []
        while self.pos < self.length:
            c = self.source[self.pos]
            if self.is_metachar(c) and not self.quote.in_quotes():
                break
            if c == "\\":
                chars.append(c)
                self.pos += 1
                if self.pos < self.length:
                    chars.append(self.source[self.pos])
                    self.pos += 1
                continue
            if c == "'" and not self.quote.double:
                self.pos += 1
                chars.append(self._scan_single_quoted())
                continue
            if c == '"' and not self.quote.single:
                self.pos += 1
                chars.append(self._scan_double_quoted())
                continue
            chars.append(c)
            self.pos += 1

        if not chars:
            return None
        return Token(TokenType.WORD, "".join(chars), start)
```

**Test:** All tests pass (no behavior change)
**Commit:** "feat: integrate quote handling in Lexer word tokenization"

---

## Phase 5: Main next_token() Method

### Increment 5.1: Implement next_token()

Combine all pieces into the main tokenization entry point.

```python
class Lexer:
    def next_token(self) -> Token:
        """Return the next token from the input."""
        # Return cached token if available
        if self._token_cache is not None:
            tok = self._token_cache
            self._token_cache = None
            return tok

        # Skip blanks
        self.skip_blanks()

        # Check for EOF
        if self.at_end():
            return Token(TokenType.EOF, "", self.pos)

        # Skip comments
        while self._skip_comment():
            self.skip_blanks()
            if self.at_end():
                return Token(TokenType.EOF, "", self.pos)

        # Try operator
        tok = self._read_operator()
        if tok is not None:
            return tok

        # Must be a word
        tok = self._read_word()
        if tok is not None:
            return tok

        # Fallback - shouldn't reach here
        return Token(TokenType.EOF, "", self.pos)

    def peek_token(self) -> Token:
        """Peek at next token without consuming."""
        if self._token_cache is None:
            self._token_cache = self.next_token()
        return self._token_cache

    def unget_token(self, tok: Token) -> None:
        """Push a token back to be returned by next call."""
        self._token_cache = tok
```

**Test:** All tests pass (no behavior change - Lexer not integrated yet)
**Commit:** "feat: implement next_token() in Lexer"

---

## Phase 6: Parser Integration (Gradual)

### Increment 6.1: Add Lexer instance to Parser

Parser creates and holds a Lexer, but doesn't use it yet.

```python
class Parser:
    def __init__(self, source: str, in_process_sub: bool = False):
        self.source = source
        self.pos = 0
        self.length = len(source)
        self._lexer = Lexer(source)  # NEW: lexer instance
        # ... rest unchanged ...
```

**Test:** All tests pass
**Commit:** "feat: add Lexer instance to Parser"

---

### Increment 6.2: Add token history tracking

Following bash's pattern of tracking last 4 tokens.

```python
class Parser:
    def __init__(self, source: str, in_process_sub: bool = False):
        # ... existing ...
        self._token_history: list[Token | None] = [None, None, None, None]

    def _record_token(self, tok: Token) -> None:
        """Record token in history, shifting older tokens."""
        self._token_history = [tok] + self._token_history[:3]

    def _last_token(self) -> Token | None:
        """Return the most recently read token."""
        return self._token_history[0]

    def _last_token_type(self) -> int | None:
        """Return type of most recently read token, or None."""
        tok = self._token_history[0]
        return tok.type if tok else None
```

**Test:** All tests pass (no behavior change - not used yet)
**Commit:** "feat: add token history tracking to Parser"

---

### Increment 6.3: Use Lexer for operator detection in one place

Pick one simple location where Parser checks for operators (e.g., `&&` or `||`) and use Lexer there as a proof of concept. The key is to keep both paths working.

```python
# In parse_list() or similar, add parallel lexer-based check:
# This is just for validation - don't change behavior yet
```

Actually, this phase is tricky because we need to carefully maintain behavior. A better approach:

### Increment 6.3: Add Lexer-based lookahead helper

Add a method that uses Lexer to peek ahead, for validation/debugging.

```python
class Parser:
    def _lexer_peek_operator(self) -> str | None:
        """Use Lexer to peek at operator. For debugging/validation."""
        saved_pos = self._lexer.pos
        saved_state = self._lexer.state
        self._lexer.pos = self.pos
        self._lexer.skip_blanks()
        tok = self._lexer._read_operator()
        result = tok.value if tok else None
        self._lexer.pos = saved_pos
        self._lexer.state = saved_state
        return result
```

**Test:** All tests pass
**Commit:** "feat: add Lexer-based lookahead helper to Parser"

---

## Phase 7: Reserved Word Recognition

### Increment 7.1: Add reserved word detection to Lexer

```python
class Lexer:
    RESERVED_WORDS = {
        "if": TokenType.IF,
        "then": TokenType.THEN,
        "else": TokenType.ELSE,
        "elif": TokenType.ELIF,
        "fi": TokenType.FI,
        "case": TokenType.CASE,
        "esac": TokenType.ESAC,
        "for": TokenType.FOR,
        "while": TokenType.WHILE,
        "until": TokenType.UNTIL,
        "do": TokenType.DO,
        "done": TokenType.DONE,
        "in": TokenType.IN,
        "function": TokenType.FUNCTION,
        "select": TokenType.SELECT,
        "coproc": TokenType.COPROC,
        "time": TokenType.TIME,
        "!": TokenType.BANG,
        "[[": TokenType.LBRACKET_LBRACKET,
        "]]": TokenType.RBRACKET_RBRACKET,
        "{": TokenType.LBRACE,
        "}": TokenType.RBRACE,
    }

    def classify_word(self, word: str, reserved_ok: bool) -> int:
        """Classify a word token - may be reserved word if unquoted and allowed."""
        if reserved_ok and word in self.RESERVED_WORDS:
            return self.RESERVED_WORDS[word]
        return TokenType.WORD
```

**Test:** All tests pass (no behavior change)
**Commit:** "feat: add reserved word detection to Lexer"

---

## Phase 8: Dollar Expansion Recognition

### Increment 8.1: Add expansion start detection

```python
class Lexer:
    def is_expansion_start(self, c: str, next_c: str | None) -> bool:
        """Return True if at start of an expansion ($, backtick, etc)."""
        if c == "$":
            return True
        if c == "`":
            return True
        return False

    def peek_expansion_type(self) -> str | None:
        """Peek at what kind of expansion follows $. Returns None if not at $."""
        if self.pos >= self.length or self.source[self.pos] != "$":
            return None
        if self.pos + 1 >= self.length:
            return "bare"  # Just $
        next_c = self.source[self.pos + 1]
        if next_c == "(":
            if self.pos + 2 < self.length and self.source[self.pos + 2] == "(":
                return "arithmetic"  # $((
            return "command"  # $(
        if next_c == "{":
            return "brace"  # ${
        if next_c == "'":
            return "ansi"  # $'
        if next_c == '"':
            return "locale"  # $"
        return "simple"  # $name or $1 etc
```

**Test:** All tests pass (no behavior change)
**Commit:** "feat: add expansion detection to Lexer"

---

## Phase 9: PST_* Parser State Flags

### Increment 9.1: Add ParserState flags

Expand beyond 5 ParseContext.kind values to proper bitmask flags.

```python
class ParserStateFlags:
    NONE = 0
    PST_CASEPAT = 0x0001      # In case pattern list
    PST_CMDSUBST = 0x0002     # In $(...) command substitution
    PST_CASESTMT = 0x0004     # Parsing case statement
    PST_CONDEXPR = 0x0008     # Inside [[ ]]
    PST_COMPASSIGN = 0x0010   # In compound assignment x=(...)
    PST_ARITH = 0x0020        # In $((...))
    PST_HEREDOC = 0x0040      # Reading heredoc body
    PST_REGEXP = 0x0080       # Parsing regex in [[ =~ ]]
    PST_EXTPAT = 0x0100       # Parsing extended pattern
    PST_SUBSHELL = 0x0200     # In (...) subshell
    PST_REDIRLIST = 0x0400    # Parsing redirections before command
    PST_COMMENT = 0x0800      # In comment (# to EOL)
```

**Test:** All tests pass (no behavior change)
**Commit:** "feat: add ParserStateFlags for context tracking"

---

### Increment 9.2: Add parser_state to Parser

```python
class Parser:
    def __init__(self, source: str, in_process_sub: bool = False):
        # ... existing ...
        self._parser_state = ParserStateFlags.NONE

    def _set_state(self, flag: int) -> None:
        self._parser_state |= flag

    def _clear_state(self, flag: int) -> None:
        self._parser_state &= ~flag

    def _in_state(self, flag: int) -> bool:
        return (self._parser_state & flag) != 0
```

**Test:** All tests pass (no behavior change)
**Commit:** "feat: add parser_state bitmask to Parser"

---

### Increment 9.3: Set PST_CASEPAT in case parsing

Update case pattern parsing to set/clear the flag.

```python
# In parse_case() or case pattern handling:
self._set_state(ParserStateFlags.PST_CASEPAT)
# ... parse patterns ...
self._clear_state(ParserStateFlags.PST_CASEPAT)
```

**Test:** All tests pass
**Commit:** "feat: set PST_CASEPAT during case pattern parsing"

---

### Increment 9.4: Set PST_ARITH in arithmetic parsing

```python
# In arithmetic parsing:
self._set_state(ParserStateFlags.PST_ARITH)
# ... parse arithmetic ...
self._clear_state(ParserStateFlags.PST_ARITH)
```

**Test:** All tests pass
**Commit:** "feat: set PST_ARITH during arithmetic parsing"

---

## Phase 10: Comment Detection Using State

### Increment 10.1: Use PST_* flags for comment detection

Update comment detection to check parser state flags.

```python
def _is_comment_start(self) -> bool:
    """Check if current position is start of a comment."""
    if self.pos >= self.length or self.source[self.pos] != "#":
        return False
    # Not a comment in case patterns
    if self._in_state(ParserStateFlags.PST_CASEPAT):
        return False
    # Not a comment in arithmetic
    if self._in_state(ParserStateFlags.PST_ARITH):
        return False
    # Must be at word boundary
    if self.pos > 0:
        prev = self.source[self.pos - 1]
        if prev not in " \t\n;|&(){}":
            return False
    return True
```

**Test:** All tests pass
**Commit:** "feat: use PST_* flags for comment detection"

---

## Phase 11: Full Lexer Integration

At this point, we have all the infrastructure. The remaining work is to:

1. Gradually migrate each parsing function to use Lexer tokens
2. Remove duplicate logic between Lexer and Parser
3. Use parser state flags consistently

Each migration should be done construct-by-construct:

### Increment 11.1: Migrate operator parsing to use Lexer
### Increment 11.2: Migrate reserved word detection to use Lexer
### Increment 11.3: Migrate simple command parsing to use Lexer
### Increment 11.4: Migrate pipeline parsing to use Lexer
### Increment 11.5: Migrate list parsing to use Lexer
... and so on.

Each of these is a full commit with tests passing.

---

## Summary of Commits

1. feat: add TokenType constants for lexer
2. feat: add Token class for lexer output
3. feat: add LexerState flags for lexer context
4. feat: add Lexer class skeleton
5. feat: add character classification methods to Lexer
6. feat: implement operator tokenization in Lexer
7. feat: add skip_blanks to Lexer
8. feat: add comment handling to Lexer
9. feat: add word boundary detection to Lexer
10. feat: add basic word tokenization to Lexer
11. feat: add single quote handling to Lexer
12. feat: add double quote handling to Lexer
13. feat: integrate quote handling in Lexer word tokenization
14. feat: implement next_token() in Lexer
15. feat: add Lexer instance to Parser
16. feat: add token history tracking to Parser
17. feat: add Lexer-based lookahead helper to Parser
18. feat: add reserved word detection to Lexer
19. feat: add expansion detection to Lexer
20. feat: add ParserStateFlags for context tracking
21. feat: add parser_state bitmask to Parser
22. feat: set PST_CASEPAT during case pattern parsing
23. feat: set PST_ARITH during arithmetic parsing
24. feat: use PST_* flags for comment detection
25. (continuing incremental migration...)

---

## Key Principles

1. **No behavior change until integration** - All new code is added but not used until tested
2. **Tests pass after every commit** - `just test && just transpile && just test-js`
3. **Small, focused changes** - Each increment does one thing
4. **Parallel structures first** - Build the new system alongside the old, then migrate
5. **Mirror bash patterns** - Use PST_*, LEX_* flag names and semantics from bash

---

## Reference: Bash Source Files

Key files to study in `~/source/bash-oracle/`:
- `parse.y` lines 3055+ (`read_token`) - main tokenizer
- `parse.y` lines 5305+ (`read_token_word`) - word tokenization
- `parse.y` lines 160-180 - LEX_* flags
- `parser.h` lines 35-62 - PST_* flags
- `command.h` lines 131-170 - WORD_DESC and W_* word flags
