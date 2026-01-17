# Plan: Move Word Parsing to Lexer (Approach A)

## Current Progress

**Completed:**
- Phase 1: Infrastructure (Token.parts, Lexer state, save/restore) ✓
- Step 3.1: Move `_parse_ansi_c_quote` to Lexer ✓
- Step 3.2: Move `_parse_locale_string` to Lexer ✓
- Step 3.3: Move `_parse_param_expansion` to Lexer (+ helpers: `_consume_param_name`, `_consume_param_operator`, `_param_subscript_has_close`, `_read_braced_param`) ✓
- Add Parser back-reference to Lexer for callbacks ✓
- Add Lexer sync helpers (`_sync_to_parser`, `_sync_from_parser`) ✓
- Update transpiler to handle forward references ✓

**Deferred (cannot easily move to Lexer):**
- `_parse_arithmetic_expansion` - calls `_parse_arith_expr` which calls `parse_list()`, creating recursive Parser interactions
- `_parse_command_substitution` - creates new `Parser(content)` sub-parser
- `_parse_backtick_substitution` - creates new `Parser(content)` sub-parser
- `_parse_process_substitution` - creates new `Parser(content)` sub-parser
- `_parse_array_literal` - may create sub-parser for nested content
- `_parse_dollar_expansion` - dispatcher that calls all expansion methods
- `_parse_word_internal` - main word reader, orchestrates all expansion methods

**Assessment:**
The "leaf" expansion methods (ansi_c_quote, locale_string, param_expansion) have been successfully moved to Lexer. These are self-contained and don't create new Parser instances.

The remaining methods all either:
1. Create new `Parser(content)` sub-parsers to parse nested command content
2. Call methods like `parse_list()` which recursively trigger more parsing

Moving these to Lexer would require the Lexer to create Parser instances or maintain complex bidirectional callbacks, which goes against the separation of concerns.

## Goal

Refactor Parable to match bash's architecture where the Lexer produces fully-parsed WORD tokens with expansion parts, and the Parser consumes tokens rather than parsing character-by-character.

## Current State

```
Parser._parse_word_internal()  →  Word(value, parts)
        ↓
    calls _parse_dollar_expansion()
    calls _parse_command_substitution()
    calls _parse_param_expansion()
    ... etc (all in Parser)
```

## Target State

```
Lexer._read_word()  →  Token(WORD, value, parts=[...])
        ↓
    calls _read_dollar_expansion()
    calls _read_command_substitution()
    calls _read_param_expansion()
    ... etc (all in Lexer)

Parser.parse_word()  →  tok = self._lex_next_token()
                        if tok.type == WORD:
                            return Word(tok.value, tok.parts)
```

---

## Phase 1: Infrastructure (~50 lines)

### Step 1.1: Add `parts` field to Token

```python
class Token:
    def __init__(self, type_: int, value: str, pos: int, parts: list = None):
        self.type = type_
        self.value = value
        self.pos = pos
        self.parts = parts if parts is not None else []
```

**Verification:** `just test` (no behavior change)

### Step 1.2: Add parser state to Lexer

Lexer needs access to PST_* flags for context-sensitive tokenization.

```python
class Lexer:
    def __init__(self, source: str):
        ...
        self._parser_state = ParserStateFlags.NONE
        self._dolbrace_state = DolbraceState.NONE
```

**Verification:** `just test`

### Step 1.3: Add save/restore state to Lexer

```python
class Lexer:
    def _save_state(self) -> LexerSavedState:
        return LexerSavedState(
            pos=self.pos,
            parser_state=self._parser_state,
            dolbrace_state=self._dolbrace_state,
            quote=self.quote.copy(),
        )

    def _restore_state(self, saved: LexerSavedState) -> None:
        self.pos = saved.pos
        self._parser_state = saved.parser_state
        self._dolbrace_state = saved.dolbrace_state
        self.quote = saved.quote
```

**Verification:** `just test`

### Step 1.4: Add AST node imports/access to Lexer

Lexer needs to create Node subclasses (CommandSubstitution, ParameterExpansion, etc.).
These are already module-level, so just ensure Lexer methods can use them.

**Verification:** `just test`

---

## Phase 2: Move Quote Scanning (~100 lines)

### Step 2.1: Enhance Lexer._scan_single_quoted

Current Lexer has basic `_scan_single_quoted`. Enhance to match Parser's `_scan_single_quote`:
- Track newlines for error reporting
- Handle unterminated quotes

```python
def _scan_single_quoted(self, chars: list, track_newline: bool = False) -> None:
    """Scan single-quoted content into chars. Caller consumed opening '."""
    # Port from Parser._scan_single_quote (line 5536)
```

**Verification:** `just test`

### Step 2.2: Enhance Lexer._scan_double_quoted

Enhance to handle:
- Backslash escapes
- Nested `$()` command substitutions
- Nested `${}` parameter expansions
- Backtick substitutions

```python
def _scan_double_quoted(self, chars: list, parts: list, start: int) -> None:
    """Scan double-quoted content. Caller consumed opening "."""
    # Port from Parser._scan_double_quote (line 5698)
```

**Verification:** `just test`

### Step 2.3: Add bracket expression scanning

```python
def _scan_bracket_expression(self, chars: list, parts: list, ...) -> bool:
    """Scan [...] bracket expression for globs/regex."""
    # Port from Parser._scan_bracket_expression (line 5548)
```

**Verification:** `just test`

---

## Phase 3: Move Expansion Parsing (~600 lines)

**Order matters - start with leaf functions that don't call others.**

### Step 3.1: Move _parse_ansi_c_quote → Lexer._read_ansi_c_quote

This is self-contained, good starting point.

```python
def _read_ansi_c_quote(self) -> tuple[Node | None, str]:
    """Read $'...' ANSI-C quoted string."""
    # Port from Parser._parse_ansi_c_quote (line 7893)
```

Update Parser._parse_ansi_c_quote to delegate:
```python
def _parse_ansi_c_quote(self):
    self._sync_lexer_to_parser()
    result = self._lexer._read_ansi_c_quote()
    self._sync_parser_to_lexer()
    return result
```

**Verification:** `just test && just transpile && just test-js`

### Step 3.2: Move _parse_locale_string → Lexer._read_locale_string

```python
def _read_locale_string(self) -> tuple[Node | None, str, list[Node]]:
    # Port from Parser._parse_locale_string (line 7932)
```

**Verification:** `just test && just transpile && just test-js`

### Step 3.3: Move _parse_param_expansion → Lexer._read_param_expansion

This is complex (~200 lines) but self-contained.

```python
def _read_param_expansion(self) -> tuple[Node | None, str]:
    # Port from Parser._parse_param_expansion (line 8035)
```

**Verification:** `just test && just transpile && just test-js`

### Step 3.4: Move _parse_arithmetic_expansion → Lexer._read_arithmetic_expansion

```python
def _read_arithmetic_expansion(self) -> tuple[Node | None, str]:
    # Port from Parser._parse_arithmetic_expansion (line 7061)
```

**Verification:** `just test && just transpile && just test-js`

### Step 3.5: Move _parse_command_substitution → Lexer._read_command_substitution

This is the most complex (~350 lines). It creates sub-parsers.

**Challenge:** Currently creates `Parser(content)` for nested parsing.
**Solution:** Keep creating sub-parsers for now; optimize later.

```python
def _read_command_substitution(self) -> tuple[Node | None, str]:
    # Port from Parser._parse_command_substitution (line 6076)
    # Still creates Parser(content) internally
```

**Verification:** `just test && just transpile && just test-js`

### Step 3.6: Move _parse_backtick_substitution → Lexer._read_backtick_substitution

```python
def _read_backtick_substitution(self) -> tuple[Node | None, str]:
    # Port from Parser._parse_backtick_substitution (line 6509)
```

**Verification:** `just test && just transpile && just test-js`

### Step 3.7: Move _parse_process_substitution → Lexer._read_process_substitution

```python
def _read_process_substitution(self) -> tuple[Node | None, str]:
    # Port from Parser._parse_process_substitution (line 6785)
```

**Verification:** `just test && just transpile && just test-js`

### Step 3.8: Move _parse_array_literal → Lexer._read_array_literal

```python
def _read_array_literal(self) -> tuple[Node | None, str]:
    # Port from Parser._parse_array_literal (line 7015)
```

**Verification:** `just test && just transpile && just test-js`

### Step 3.9: Move _parse_dollar_expansion → Lexer._read_dollar_expansion

This dispatches to the above methods based on what follows $.

```python
def _read_dollar_expansion(self, chars: list, parts: list) -> bool:
    # Port from Parser._parse_dollar_expansion (line 5722)
    # Calls _read_param_expansion, _read_command_substitution, etc.
```

**Verification:** `just test && just transpile && just test-js`

---

## Phase 4: Move Word Parsing (~300 lines)

### Step 4.1: Create Lexer._read_word_full

Port `_parse_word_internal` to Lexer as `_read_word_full`:

```python
def _read_word_full(self, ctx: int, at_command_start: bool = False,
                    in_array_literal: bool = False) -> Token | None:
    """Read a complete WORD token with expansion parts."""
    # Port from Parser._parse_word_internal (line 5766)
    # Returns Token(WORD, value, pos, parts=[...])
```

**Verification:** `just test && just transpile && just test-js`

### Step 4.2: Update Lexer._read_word to use _read_word_full

Replace simple `_read_word` with call to `_read_word_full`:

```python
def _read_word(self) -> Token | None:
    return self._read_word_full(WORD_CTX_NORMAL)
```

**Verification:** `just test && just transpile && just test-js`

### Step 4.3: Update Lexer.next_token

```python
def next_token(self) -> Token:
    ...
    tok = self._read_operator()
    if tok is not None:
        return tok
    tok = self._read_word_full(WORD_CTX_NORMAL)  # Full word with parts
    if tok is not None:
        return tok
    return Token(TokenType.EOF, "", self.pos)
```

**Verification:** `just test && just transpile && just test-js`

---

## Phase 5: Update Parser (~200 lines removed)

### Step 5.1: Simplify Parser.parse_word

```python
def parse_word(self, at_command_start: bool = False,
               in_array_literal: bool = False) -> Word | None:
    self.skip_whitespace()
    self._sync_lexer_to_parser()
    tok = self._lexer._read_word_full(
        WORD_CTX_NORMAL, at_command_start, in_array_literal
    )
    if tok is None:
        return None
    self._sync_parser_to_lexer()
    return Word(tok.value, tok.parts)
```

**Verification:** `just test && just transpile && just test-js`

### Step 5.2: Remove Parser._parse_word_internal

Delete the 300-line function - it's now in Lexer.

**Verification:** `just test && just transpile && just test-js`

### Step 5.3: Remove Parser expansion methods (now delegating)

Remove:
- `_parse_dollar_expansion`
- `_parse_command_substitution`
- `_parse_backtick_substitution`
- `_parse_process_substitution`
- `_parse_param_expansion`
- `_parse_arithmetic_expansion`
- `_parse_ansi_c_quote`
- `_parse_locale_string`
- `_parse_array_literal`

These are now `Lexer._read_*` methods.

**Verification:** `just test && just transpile && just test-js`

### Step 5.4: Remove redundant Parser character methods

Parser no longer needs direct character access for word parsing:
- Keep `peek()`, `advance()` for now (used by other parsing)
- Later: evaluate if Parser needs any character access

**Verification:** `just test && just transpile && just test-js`

---

## Phase 6: Cleanup (~50 lines)

### Step 6.1: Consolidate position sync

Review `_sync_lexer_to_parser` / `_sync_parser_to_lexer` usage.
Simplify if possible.

### Step 6.2: Remove dead code

Search for any orphaned helper methods.

### Step 6.3: Update comments and docstrings

Reflect new architecture.

### Step 6.4: Final validation

```bash
just test && just transpile && just test-js && just fuzz
```

---

## Summary

| Phase | Description | Lines Changed | Risk |
|-------|-------------|---------------|------|
| 1 | Infrastructure | +50 | Low |
| 2 | Quote scanning | +100, -100 | Low |
| 3 | Expansion parsing | +600, -600 | Medium |
| 4 | Word parsing | +300, -0 | Medium |
| 5 | Parser simplification | +50, -800 | Medium |
| 6 | Cleanup | -50 | Low |
| **Total** | | Net: -400 lines | |

## Files Modified

- `src/parable.py` - main changes
- `src/parable.js` - auto-generated via transpile

## Rollback Strategy

Each phase is a separate commit. If tests fail, revert to previous commit.

## Dependencies

Methods must be moved in order (leaf functions first):
```
_read_ansi_c_quote (leaf)
_read_locale_string (leaf)
_read_param_expansion (leaf)
_read_arithmetic_expansion (leaf)
_read_command_substitution (complex, creates sub-parser)
_read_backtick_substitution (similar to command sub)
_read_process_substitution (similar to command sub)
_read_array_literal (calls _read_word recursively)
_read_dollar_expansion (dispatcher, calls all above)
_read_word_full (main word reader, calls all above)
```
