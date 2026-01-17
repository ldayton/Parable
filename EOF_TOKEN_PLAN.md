# Plan: EOF Token Mechanism for Command Substitution

## Overview

Implement bash's `shell_eof_token` mechanism to allow parsing command substitutions directly without creating sub-parsers. This eliminates ~350 lines of duplicated scanning logic and enables moving substitution methods to the Lexer.

## Bash's Mechanism (Reference)

```c
// parse.y line 4519
shell_eof_token = close;  // ')' for $(), '}' for ${}

// parse.y line 3683 - in read_token()
if ((parser_state & PST_CMDSUBST) && character == shell_eof_token)
    peek_char = shell_getc(0);  // Don't skip newlines

// parse.y line 3080 - in yylex()
if ((parser_state & PST_EOFTOKEN) && current_token == shell_eof_token)
    return current_token;  // Return the token, parser treats as terminator
```

Key points:
1. `shell_eof_token` is saved/restored as part of parser state
2. `PST_EOFTOKEN` flag enables the mechanism
3. When the closing char is seen at depth 0, it's returned as a token
4. The grammar rules check for this token to terminate parsing

---

## Implementation Plan

### Phase 1: Add EOF Token Infrastructure

#### Step 1.1: Add fields to Parser

```python
class Parser:
    def __init__(self, source: str, ...):
        ...
        self._eof_token: str | None = None  # Character that acts as EOF
        self._eof_depth: int = 0  # Depth counter for nested constructs
```

#### Step 1.2: Update SavedParserState

```python
class SavedParserState:
    def __init__(self, ..., eof_token: str | None, eof_depth: int):
        ...
        self.eof_token = eof_token
        self.eof_depth = eof_depth
```

#### Step 1.3: Update save/restore methods

```python
def _save_parser_state(self) -> SavedParserState:
    return SavedParserState(
        ...,
        eof_token=self._eof_token,
        eof_depth=self._eof_depth,
    )

def _restore_parser_state(self, saved: SavedParserState) -> None:
    ...
    self._eof_token = saved.eof_token
    self._eof_depth = saved.eof_depth
```

**Verification:** `just test` (no behavior change yet)

---

### Phase 2: Add EOF Token Checking to Lexer

#### Step 2.1: Add EOF token fields to Lexer

```python
class Lexer:
    def __init__(self, source: str):
        ...
        self._eof_token: str | None = None
        self._eof_depth: int = 0
```

#### Step 2.2: Sync EOF token between Parser and Lexer

Update `_sync_lexer()` and `_sync_parser()`:

```python
def _sync_lexer(self) -> None:
    self._lexer.pos = self.pos
    self._lexer._token_cache = None
    self._lexer._eof_token = self._eof_token
    self._lexer._eof_depth = self._eof_depth

def _sync_parser(self) -> None:
    self.pos = self._lexer.pos
    self._eof_depth = self._lexer._eof_depth  # Depth may have changed
```

#### Step 2.3: Check EOF token in Lexer.next_token()

In `next_token()`, before reading operators:

```python
def next_token(self) -> Token:
    self.skip_whitespace_and_comments()

    # Check for EOF token at depth 0
    if (self._eof_token is not None
        and not self.at_end()
        and self.peek() == self._eof_token
        and self._eof_depth == 0
        and not self.quote.single  # Not inside quotes
        and not self.quote.double):
        # Return the char as its own token type
        # Parser will recognize this as the terminator
        return Token(TokenType.EOF_MARKER, self._eof_token, self.pos)

    # ... rest of next_token
```

**Note:** Need a new `TokenType.EOF_MARKER` or reuse existing mechanism.

**Verification:** `just test` (no behavior change yet)

---

### Phase 3: Handle Depth Tracking

#### Step 3.1: Track depth for nested `()`

When lexing `(`:
```python
if self._eof_token == ')':
    self._eof_depth += 1
```

When lexing `)`:
```python
if self._eof_token == ')' and self._eof_depth > 0:
    self._eof_depth -= 1
```

#### Step 3.2: Handle depth in word parsing

Inside `_parse_word_internal` or equivalent, when seeing `(` or `)`:
- Increment/decrement `_eof_depth` appropriately
- Only applies when outside quotes

#### Step 3.3: Handle arithmetic `$(())`

When `_eof_token == ')'` and we see `$((`:
- This is arithmetic, not our closer
- Need to scan past the matching `))`

**Verification:** Add test cases for nested parens

---

### Phase 4: Refactor _parse_command_substitution

#### Step 4.1: Remove scanning loop

Replace the ~350 line scanning loop with:

```python
def _parse_command_substitution(self) -> tuple[Node | None, str]:
    if self.at_end() or self.peek() != "$":
        return None, ""

    start = self.pos
    self.advance()  # consume $

    if self.at_end() or self.peek() != "(":
        self.pos = start
        return None, ""

    self.advance()  # consume (

    # Save state and set up EOF token
    saved = self._save_parser_state()
    self._set_state(ParserStateFlags.PST_CMDSUBST)
    self._eof_token = ')'
    self._eof_depth = 0

    # Parse directly - will stop when ) is seen at depth 0
    cmd = self.parse_list()
    if cmd is None:
        cmd = Empty()

    # Verify we stopped at )
    self.skip_whitespace()
    if self.at_end() or self.peek() != ')':
        self._restore_parser_state(saved)
        raise ParseError("Unterminated command substitution", pos=start)

    self.advance()  # consume )
    text = _substring(self.source, start, self.pos)

    self._restore_parser_state(saved)
    return CommandSubstitution(cmd), text
```

**Verification:** `just test && just transpile && just test-js`

---

### Phase 5: Handle Edge Cases

#### Step 5.1: Case patterns

In case statements, `)` after a pattern is NOT our closer:
```bash
$(case x in a) echo;; esac)
```

The `)` after `a` terminates the pattern, not the command sub.

**Solution:** When `PST_CASEPAT` is set, `)` doesn't decrement depth / trigger EOF.

```python
# In parse_case_pattern or equivalent
if self._eof_token == ')' and not (self._parser_state & PST_CASEPAT):
    # Normal ) handling
else:
    # This ) is a case pattern terminator, not our EOF
```

#### Step 5.2: Quotes

`)` inside quotes is literal:
```bash
$(echo ")")
```

**Solution:** Already handled - we check `not self.quote.single and not self.quote.double`

#### Step 5.3: Heredocs

```bash
$(cat <<EOF
content with ) here
EOF
)
```

**Solution:** The heredoc body is gathered separately after the newline. The `)` in the body is part of the heredoc content, not seen by the tokenizer.

#### Step 5.4: Backslash escape

```bash
$(echo \))
```

The `\)` should produce a literal `)`, not trigger EOF.

**Solution:** Handle in word parsing - `\)` is an escape sequence.

**Verification:** Add specific test cases for each edge case

---

### Phase 6: Move to Lexer

#### Step 6.1: Add _read_command_substitution to Lexer

```python
def _read_command_substitution(self) -> tuple["Node | None", str]:
    if self.at_end() or self.peek() != "$":
        return None, ""

    start = self.pos
    self.advance()  # $

    if self.at_end() or self.peek() != "(":
        self.pos = start
        return None, ""

    self.advance()  # (

    # Sync and set up EOF token
    self._sync_to_parser()
    saved = self._parser._save_parser_state()
    self._parser._set_state(ParserStateFlags.PST_CMDSUBST)
    self._parser._eof_token = ')'
    self._parser._eof_depth = 0
    self._sync_from_parser()  # Get EOF token into lexer

    # Parse via parser callback
    cmd = self._parser.parse_list()
    if cmd is None:
        cmd = Empty()

    self._sync_to_parser()
    self._parser.skip_whitespace()

    if self._parser.at_end() or self._parser.peek() != ')':
        self._parser._restore_parser_state(saved)
        raise ParseError("Unterminated command substitution", pos=start)

    self._parser.advance()  # )
    self._sync_from_parser()

    text = _substring(self.source, start, self.pos)
    self._parser._restore_parser_state(saved)

    return CommandSubstitution(cmd), text
```

#### Step 6.2: Update Parser to delegate

```python
def _parse_command_substitution(self) -> tuple[Node | None, str]:
    """Parse $(...) command substitution. Delegates to Lexer."""
    self._sync_lexer()
    result = self._lexer._read_command_substitution()
    self._sync_parser()
    return result
```

**Verification:** `just test && just transpile && just test-js`

---

### Phase 7: Refactor Backtick and Process Substitution

#### Step 7.1: _parse_backtick_substitution

Similar pattern but with `` ` `` as EOF token.

```python
self._eof_token = '`'
```

#### Step 7.2: _parse_process_substitution

For `<(...)` and `>(...)`:

```python
self._eof_token = ')'
```

**Verification:** `just test && just transpile && just test-js`

---

### Phase 8: Cleanup

#### Step 8.1: Remove dead scanning code

Delete the old scanning loops from Parser.

#### Step 8.2: Remove sub-parser creation

No more `Parser(content)` for these methods.

#### Step 8.3: Final validation

```bash
just test && just transpile && just test-js && just fuzz
```

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Case pattern edge cases | Explicit PST_CASEPAT handling |
| Nested arithmetic $(()) | Detect and skip arithmetic |
| Quote handling | Check quote state before EOF |
| Heredoc content | Heredocs gathered separately |
| Position sync issues | Careful sync before/after callbacks |

---

## Summary

| Phase | Description | Complexity |
|-------|-------------|------------|
| 1 | Add EOF token infrastructure | Low |
| 2 | Add EOF checking to Lexer | Low |
| 3 | Depth tracking | Medium |
| 4 | Refactor command substitution | Medium |
| 5 | Handle edge cases | High |
| 6 | Move to Lexer | Medium |
| 7 | Backtick and process sub | Medium |
| 8 | Cleanup | Low |

**Estimated lines changed:** ~-400 (net reduction)

**Key benefit:** Eliminates duplicated scanning logic, matches bash architecture.
