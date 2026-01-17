# Parable Lexer Evolution Plan

## Goal

Match bash's parsing behavior exactly by mirroring bash's architectural patterns. The fuzzer consistently finds differences due to context-sensitive complexities that require proper tokenizer-parser separation.

---

## Architecture Comparison

| Aspect             | Bash                          | Parable (Current)                   |
| ------------------ | ----------------------------- | ----------------------------------- |
| **Token Stream**   | `yylex()` produces tokens     | Parser does character-level parsing |
| **Parser State**   | 28 `PST_*` flags in bitmask   | `ParserStateFlags` (partial)        |
| **Lexer State**    | 16 `LEX_*` flags              | Lexer exists but Parser bypasses it |
| **Quote State**    | `struct dstack` with push/pop | `QuoteState` class ✓                |
| **Token History**  | Last 4 tokens tracked         | `_token_history` ✓                  |
| **Dollar-Brace**   | `DOLBRACE_*` state machine    | `DolbraceState` ✓                   |
| **Nested Parsing** | Save/restore full state       | Sub-parser instances                |

---

## Key Insight (January 2026)

**The EOF token mechanism DOES work, even with character-based parsing.**

Initial attempts failed because the Parser bypassed the Lexer. The solution:

1. Add `_eof_token` and `_eof_depth` to both Parser and Lexer
2. Sync state via `_sync_lexer()` before parsing nested content
3. Have `Lexer.next_token()` return EOF when hitting delimiter at depth 0
4. Track paren depth in `Lexer._read_operator()` with PST_CASEPAT handling

This eliminated ~550 lines of scanning code from `_parse_command_substitution` and `_parse_process_substitution`. The key was having the Lexer check EOF token conditions, even though the Parser still does character-level work for most things.

---

## Completed Work

### Infrastructure
- `TokenType` constants mirroring bash ✓
- `Token` class with type, value, pos, parts ✓
- `Lexer` class with `next_token()`, `peek_token()` ✓
- `ParserStateFlags` (PST_*) bitmask ✓
- `DolbraceState` machine ✓
- `QuoteState` with push/pop ✓
- Token history tracking ✓
- Parser/Lexer sync helpers ✓

### Lexer Methods
- Operator tokenization ✓
- Comment handling ✓
- Word tokenization (basic) ✓
- Quote scanning ✓
- Reserved word detection ✓
- Expansion type detection ✓

### Moved to Lexer
- `_read_ansi_c_quote` ✓
- `_read_locale_string` ✓
- `_read_param_expansion` (+ helpers) ✓
- `_read_single_quote` ✓
- `_is_word_terminator` ✓
- `_read_bracket_expression` ✓
- `_read_word_internal` ✓ (with callbacks to Parser for nested parsing)

### Parser State Flags in Use
- `PST_CASEPAT` - set in `parse_case()` ✓
- `PST_ARITH` - set in `_parse_arith_expr()` ✓

---

## Current State

The Parser now uses a **hybrid approach**:
- **Token-based terminator detection**: `parse_command()` uses `_lex_is_command_terminator()` which enables the EOF token mechanism
- **Character-based word parsing**: `parse_word()` still does character-level expansion parsing

```python
# Current implementation (hybrid):
def parse_command(self):
    while True:
        self.skip_whitespace()
        if self._lex_is_command_terminator():  # Token-based via Lexer
            break
        ...
        word = self.parse_word()  # Character-based expansion parsing
        ...
```

This works because `_lex_peek_token()` doesn't advance Parser position - only `_lex_next_token()` does. The Lexer's EOF token mechanism is checked during terminator detection, while word parsing still uses character-level methods.

**Key methods using tokens:**
- `parse_command()` - uses `_lex_is_command_terminator()` for terminators ✓
- `parse_list_operator()` - uses `_lex_peek_operator()` and `_lex_next_token()` ✓
- `_parse_simple_pipeline()` - uses `_lex_peek_operator()` for pipe detection ✓
- `parse_pipeline()` - uses `_lex_is_at_reserved_word()` for time/! detection ✓

**Word parsing now in Lexer:**
- `parse_word()` delegates to `Lexer._read_word_internal()` via callbacks
- Parser methods (`_parse_command_substitution`, etc.) called back from Lexer as needed

**Remaining character-based:**
- Newline handling in `parse_list()` - special heredoc/separator logic

---

## Full Architectural Consistency Plan

### Goal
Parser consumes tokens exclusively. No character-level parsing in Parser.

```python
# Target architecture:
def parse_command(self):
    while True:
        tok = self._lex_peek_token()
        if tok.type in TERMINATORS:
            break
        if tok.type == TokenType.WORD:
            self._lex_next_token()
            word = tok.word  # Word object with expansions
            words.append(word)
```

---

### Phase 1: Move Word Parsing Helpers to Lexer

**Already done:**
- `_read_ansi_c_quote` ✓
- `_read_locale_string` ✓
- `_read_param_expansion` ✓

**To move (simple, no parse_list dependency):**

| Method | Lines | Complexity | Notes |
|--------|-------|------------|-------|
| `_is_word_terminator` | 40 | Low | Context-sensitive termination logic |
| `_scan_single_quote` | 12 | Low | Just scans to closing `'` |
| `_scan_bracket_expression` | 90 | Medium | `[...]` for globs/regex |

**Stays in Parser (needs parse_list):**
- `_parse_command_substitution` - uses EOF token + parse_list
- `_parse_process_substitution` - uses EOF token + parse_list
- `_parse_backtick_substitution` - escape processing + sub-parser
- `_parse_arithmetic_expansion` - separate arith parser
- `_parse_array_literal` - loops calling parse_word

---

### Phase 2: Move `_parse_word_internal` to Lexer

Create `Lexer._read_word_internal()` (~300 lines) with callbacks:

```python
class Lexer:
    def _read_word_internal(self, ctx: int, ...) -> Word | None:
        chars = []
        parts = []
        while not self.at_end():
            ch = self.peek()
            # ... existing logic ...

            # For expansions needing Parser:
            if ch == "$" and self._peek_next() == "(":
                self._sync_to_parser()
                node, text = self._parser._parse_command_substitution()
                self._sync_from_parser()
                if node:
                    parts.append(node)
                    chars.append(text)
                continue
            # ... etc ...
        return Word("".join(chars), parts if parts else None)
```

**Callback pattern (already established):**
```python
self._sync_to_parser()           # Lexer.pos → Parser.pos
result = self._parser.method()   # Call Parser method
self._sync_from_parser()         # Parser.pos → Lexer.pos
```

---

### Phase 3: Update Token to Carry Word

```python
class Token:
    type: int
    value: str
    pos: int
    word: Word | None = None  # NEW: parsed Word object for WORD tokens
```

Update `Lexer._read_word()`:
```python
def _read_word(self) -> Token | None:
    word = self._read_word_internal(WORD_CTX_NORMAL)
    if word is None:
        return None
    return Token(TokenType.WORD, word.value, start, word=word)
```

---

### Phase 4: Update Parser to Consume Word Tokens

```python
def parse_word(self, at_command_start=False, in_array_literal=False) -> Word | None:
    self.skip_whitespace()
    tok = self._lex_peek_token()
    if tok.type != TokenType.WORD:
        return None
    self._lex_next_token()  # Consume the token
    return tok.word
```

**Methods to update:**
- `parse_command()` - use `tok.word` instead of `parse_word()`
- `parse_for()`, `parse_case()`, etc. - same pattern
- `_parse_array_literal()` - needs special handling (Lexer callback)

---

### Phase 5: Handle Context-Sensitive Word Parsing

The three word contexts need different handling:

| Context | Where Used | Termination Rules |
|---------|------------|-------------------|
| `WORD_CTX_NORMAL` | Commands, assignments | Metacharacters terminate |
| `WORD_CTX_COND` | Inside `[[ ]]` | `]]`, `&&`, `\|\|` terminate |
| `WORD_CTX_REGEX` | RHS of `=~` | `]]`, whitespace terminate |

**Option A:** Lexer checks Parser state flags to determine context
```python
def _read_word_internal(self):
    if self._parser_state & PST_CONDEXPR:
        ctx = WORD_CTX_COND
    elif self._parser_state & PST_REGEXP:
        ctx = WORD_CTX_REGEX
    else:
        ctx = WORD_CTX_NORMAL
```

**Option B:** Parser tells Lexer which context via method parameter
```python
def _lex_next_word(self, ctx: int) -> Word | None:
    self._sync_lexer()
    self._lexer._word_context = ctx
    tok = self._lexer.next_token()
    ...
```

---

### Execution Order

1. **Phase 1a:** Move `_scan_single_quote` to Lexer ✓
2. **Phase 1b:** Move `_is_word_terminator` to Lexer ✓
3. **Phase 1c:** Move `_scan_bracket_expression` to Lexer ✓
4. **Phase 2:** Move `_parse_word_internal` to Lexer as `_read_word_internal` ✓
5. **Phase 3:** Add `word` field to Token class ✓
6. **Phase 4:** ~~Update `parse_word()` to consume tokens~~ (Deferred - see note)
7. **Phase 5:** ~~Handle context-sensitive cases~~ (Deferred - see note)

**Note on Phases 4-5:** These phases would require `Lexer._read_word()` to call
`_read_word_internal()`, but this creates infinite recursion: `_read_word_internal()`
uses callbacks to Parser methods like `_parse_dollar_expansion()`, which eventually
call back to Lexer. The current hybrid approach works well:
- Token-based: terminators, operators, reserved words
- Lexer-based: word parsing via `_read_word_internal()` with Parser callbacks

---

### Risk Mitigation

- **Test after each phase** - `just test && just transpile && just test-js`
- **Keep old methods temporarily** - delete only after new ones proven
- **Incremental PRs** - one phase per PR for easy rollback

---

### Success Criteria

1. ~~`parse_command()` never calls `self.peek()` or `self.advance()`~~ (Hybrid approach)
2. All word parsing goes through `Lexer._read_word_internal()` ✓
3. Token.word field available for future use ✓
4. All 4515+ tests pass ✓
5. Fuzzer finds no new differences

---

## Completed: EOF Token Mechanism

### What Works Now
- `_parse_command_substitution`: Uses EOF token `)`, calls `parse_list()` directly ✓
- `_parse_process_substitution`: Uses EOF token `)`, calls `parse_list()` directly ✓
- Eliminated ~550 lines of scanning code ✓
- No sub-parsers needed for command/process substitution ✓

### What Doesn't Apply
- `_parse_backtick_substitution`: Escape handling (`\$`, `` \` ``, `\\`, `\<newline>`) requires character-by-character processing before parsing. Cannot use EOF token directly.
- `_parse_arithmetic_expansion`: Uses separate arithmetic expression parser, not shell parser.

### Remaining Scanning Code
`_find_cmdsub_end` and related functions are still used by:
- `_format_command_substitutions` (Word.to_sexp output formatting)
- `_parse_backtick_substitution` (escape processing)

---

## Methods Still in Parser

| Method                         | Status                                       |
| ------------------------------ | -------------------------------------------- |
| `_parse_command_substitution`  | ✓ Uses EOF token, calls `parse_list()` inline |
| `_parse_process_substitution`  | ✓ Uses EOF token, calls `parse_list()` inline |
| `_parse_backtick_substitution` | Needs escape processing, uses sub-parser     |
| `_parse_arithmetic_expansion`  | Uses separate arithmetic parser              |
| `_parse_array_literal`         | `=(...)` may contain command subs            |
| `_parse_dollar_expansion`      | dispatcher for above                         |
| `_parse_word_internal`         | ✓ Delegates to `Lexer._read_word_internal()` |
| `_scan_single_quote`           | ✓ Delegates to `Lexer._read_single_quote()`  |
| `_is_word_terminator`          | ✓ Delegates to `Lexer._is_word_terminator()` |
| `_scan_bracket_expression`     | ✓ Delegates to `Lexer._read_bracket_expression()` |

---

## Reference

### Parser State Flags (PST_*)

```python
PST_CASEPAT = 0x0001      # In case pattern - ) is terminator not paren
PST_CMDSUBST = 0x0002     # In $(...) - affects comment handling
PST_CASESTMT = 0x0004     # Parsing case statement
PST_CONDEXPR = 0x0008     # Inside [[ ]] - different quoting rules
PST_COMPASSIGN = 0x0010   # In compound assignment x=(...)
PST_ARITH = 0x0020        # In $((...)) - # is not comment
PST_HEREDOC = 0x0040      # Reading heredoc body
PST_REGEXP = 0x0080       # Parsing regex in [[ =~ ]]
PST_EXTPAT = 0x0100       # Parsing extended pattern @(...)
PST_SUBSHELL = 0x0200     # In (...) subshell
```

### Token Types

```python
# Operators
SEMI = 10        # ;
PIPE = 11        # |
AMP = 12         # &
LPAREN = 13      # (
RPAREN = 14      # )
AND_AND = 30     # &&
OR_OR = 31       # ||
SEMI_SEMI = 32   # ;;
LESS_LESS = 35   # <<
# ... etc

# Reserved words (contextual)
IF, THEN, ELSE, ELIF, FI = 50-54
CASE, ESAC = 55-56
FOR, WHILE, UNTIL, DO, DONE = 57-61
```

### Bash Reference Files

- `parse.y:3055+` - `read_token()` main tokenizer
- `parse.y:5305+` - `read_token_word()` word tokenization
- `parse.y:4451+` - `parse_comsub()` command substitution
- `parse.y:7220+` - `save_parser_state()` / `restore_parser_state()`
- `parser.h:35-62` - PST_* flags
- `parse.y:160-180` - LEX_* flags

---

## Success Metrics

1. **Fuzzer convergence** - fewer novel differences over time
2. **Test coverage** - all tests continue to pass
3. **Code simplification** - less duplicated scanning/parsing logic
4. **Architectural alignment** - Parser consumes tokens, not characters
