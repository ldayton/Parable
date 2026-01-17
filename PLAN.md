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

## Architectural Gaps (January 2026)

Based on studying bash source (`~/source/bash-oracle`), these core patterns are missing:

### 1. `open_brace_count` - Brace Nesting Tracker

**Bash** (`parse.y`):
```c
static int open_brace_count;  // Global counter

// In read_token():
if (character == '{') {
    open_brace_count++;
    return '{';
}
if (character == '}') {
    if (open_brace_count > 0 && reserved_word_acceptable(last_read_token)) {
        open_brace_count--;
        return '}';  // RBRACE token
    }
    // Otherwise it's just a literal '}'
}
```

**Parable**: Missing. Currently uses ad-hoc checks in `parse_simple_command()`. This is why `}` at command position is mishandled - bash knows `}` is only special when `open_brace_count > 0`.

**Impact**: Input `}` returns literal word vs. RBRACE token based on whether we're inside `{ ... }`.

### 2. `reserved_word_acceptable()` - Centralized Gate

**Bash** (`parse.y:3835`):
```c
static int reserved_word_acceptable(int toksym) {
    switch (toksym) {
        case '\n': case ';': case '(': case ')':
        case '|': case '&': case '{': case '}':
        case AND_AND: case BANG: case BAR_AND:
        case DO: case DONE: case ELIF: case ELSE:
        case ESAC: case FI: case IF: case OR_OR:
        case SEMI_SEMI: case SEMI_AND: case SEMI_SEMI_AND:
        case THEN: case TIME: case TIMEOPT: case TIMEIGN:
        case COPROC: case UNTIL: case WHILE:
        case 0:  // Start of input
            return 1;
        default:
            return 0;
    }
}
```

**Parable**: Logic is scattered across `_lex_peek_reserved_word()`, `_reserved_word_token()`, and `parse_simple_command()`. Each has partial, inconsistent checks.

**Impact**: Reserved words recognized in wrong contexts. `]]` after `foo` should be literal.

### 3. `dstack` - Delimiter Stack with Push/Pop

**Bash** (`parse.y:220`):
```c
struct dstack {
    unsigned char *delimiters;
    int delimiter_depth;
    int delimiter_space;
};
#define push_delimiter(ds, c) ...
#define pop_delimiter(ds) ...
```

**Parable**: Uses `QuoteState` class with boolean fields, not a true stack. Works for simple nesting but can't track:
- Which delimiter is unclosed (for error messages)
- Position where delimiter opened
- Proper LIFO ordering

### 4. `special_case_tokens()` - Centralized Reclassification

**Bash** (`parse.y:4091`):
```c
static int special_case_tokens(char *tokstr) {
    if (last_read_token == WORD && token_before_that == FUNCTION)
        return WORD;  // Function name, not reserved word
    if (last_read_token == WORD && token_before_that == CASE)
        return WORD;  // Case word, not reserved word
    // ... more context-dependent reclassification
}
```

**Parable**: Ad-hoc checks scattered throughout. No single place that handles token reclassification based on parser history.

---

## Convergence Plan

### Phase A: Add `open_brace_count` ✓

**Completed:** Added infrastructure for tracking brace/bracket nesting.

1. ✓ Add `_open_brace_count` and `_open_cond_count` to Parser
2. ✓ Increment/decrement in `parse_brace_group()` and `parse_conditional_expr()`
3. ✓ Save/restore in `SavedParserState` for nested parsing (e.g., `$(...)`)

**Note:** In bash, `open_brace_count` affects lexer token type (RBRACE vs falling through
to word parsing). In Parable, we track the count for potential future use in
`reserved_word_acceptable()` logic, but the current reserved word recognition still
works because `}` at command position always breaks the command loop, and whether it's
successfully consumed depends on whether `parse_brace_group()` is expecting it.

### Phase B: Implement `reserved_word_acceptable()` ✓

**Completed:** Added centralized `_reserved_word_acceptable()` method.

1. ✓ Created `_reserved_word_acceptable()` that checks token history
2. ✓ Returns True after command separators (`;`, `|`, `&`, `&&`, `||`, `\n`, etc.)
3. ✓ Returns True after reserved words expecting commands (`if`, `then`, `do`, etc.)
4. ✓ Returns True at start of input (None in token history)

**Note:** The method is infrastructure - not yet actively called. Current code achieves
similar results via `len(words) == 0` checks in `parse_simple_command()`, which is
effectively checking "command start position". The centralized method enables future
consolidation of these scattered checks.

### Phase C: Enhance DelimiterStack ✓

**Completed:** Added `DelimiterStack` class for tracking delimiters with positions.

1. ✓ Created `DelimiterStack` class with `push(delim, pos)`, `pop()`, `peek()`
2. ✓ Store (delimiter_char, start_pos) tuples
3. ✓ Added `_delimiter_stack` to Parser
4. ✓ Used in `parse_brace_group()` for better error messages

**Example:** `{ echo hello` now produces:
`Parse error at position 12: Expected \`}' to match \`{' at position 0`

### Phase D: Consolidate `special_case_tokens()`

1. Create single method for context-dependent token reclassification
2. Move ad-hoc checks from `_reserved_word_token()` and elsewhere
3. Use token history for decisions

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

The Parser now uses **token-based parsing** for words:

```python
# Current implementation (token-based):
def parse_word(self, at_command_start=False, in_array_literal=False) -> Word | None:
    self.skip_whitespace()
    if self.at_end():
        return None
    # Set context for Lexer before peeking
    self._at_command_start = at_command_start
    self._in_array_literal = in_array_literal
    tok = self._lex_peek_token()
    if tok.type != TokenType.WORD:
        return None
    self._lex_next_token()
    return tok.word
```

**Key methods using tokens:**
- `parse_command()` - uses `_lex_is_command_terminator()` for terminators ✓
- `parse_list_operator()` - uses `_lex_peek_operator()` and `_lex_next_token()` ✓
- `_parse_simple_pipeline()` - uses `_lex_peek_operator()` for pipe detection ✓
- `parse_pipeline()` - uses `_lex_is_at_reserved_word()` for time/! detection ✓
- `parse_word()` - consumes WORD tokens with pre-parsed Word objects ✓

**Word parsing flow:**
1. Parser sets word context (`_at_command_start`, `_in_array_literal`, `_word_context`)
2. `_sync_lexer()` syncs context to Lexer (invalidates cache if context changed)
3. `Lexer._read_word()` calls `_read_word_internal()` with context
4. `_read_word_internal()` uses callbacks to Parser for nested parsing (`$()`, etc.)
5. Token returned with pre-parsed `Word` object in `tok.word`

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
6. **Phase 4:** Update `parse_word()` to consume tokens ✓
7. **Phase 5:** Handle context-sensitive cases ✓

**Phases 4-5 completed (January 2026, PR #332):** Initial concerns about infinite
recursion were resolved. The recursion IS bounded by input nesting depth - each
recursive call advances position in input, and the EOF token mechanism stops at
delimiters. Key implementation details:
- Word context state (`_at_command_start`, `_in_array_literal`, `_word_context`) synced from Parser to Lexer
- Token cache tracks context and invalidates on context mismatch
- `_post_read_pos` handles heredoc position advancement during tokenization
- Heredoc registration is idempotent to handle re-tokenization

---

### Risk Mitigation

- **Test after each phase** - `just test && just transpile && just test-js`
- **Keep old methods temporarily** - delete only after new ones proven
- **Incremental PRs** - one phase per PR for easy rollback

---

### Success Criteria

1. ~~`parse_command()` never calls `self.peek()` or `self.advance()`~~ (Hybrid approach)
2. All word parsing goes through `Lexer._read_word_internal()` ✓
3. Token.word field carries pre-parsed Word object ✓
4. `parse_word()` consumes WORD tokens instead of bypassing tokenizer ✓
5. All 4515+ tests pass ✓
6. Fuzzer finds no new differences

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
