# Parable Architecture Evolution Proposal

## Goal

Match bash's parsing behavior exactly. While Parable passes an extensive test corpus, the fuzzer consistently finds differences due to context-sensitive complexities. The hypothesis is that we need to mirror bash's architectural patterns more closely.

## Current State Comparison

| Aspect | Bash | Parable |
|--------|------|---------|
| **Quote State** | `struct dstack` with push/pop | `QuoteState` class with push/pop |
| **Parser State** | 28 `PST_*` flags in bitmask | 5 `ParseContext.kind` values |
| **Lexer State** | 16 `LEX_*` flags | None (no lexer) |
| **Token Stream** | `yylex()` produces tokens | No tokens, direct string parsing |
| **Token History** | Last 4 tokens tracked | None |
| **Dollar-Brace** | `DOLBRACE_*` state machine | Inline handling |
| **Nested Parsing** | Save/restore full state | New Parser instance |

## Proposals

### 1. Add a Lexer Layer (Highest Impact)

Bash's context-sensitive lexing is where most complexity lives. The same character means different things based on state:

```
$x      # $ followed by word → parameter
$(      # $ followed by ( → command sub
$((     # $ followed by (( → arithmetic
${      # $ followed by { → brace expansion
$'      # $ followed by ' → ANSI-C quote
```

**Current Parable:** Handles this inline in parsing functions, duplicating logic.

**Proposal:** Create a `Lexer` class that:
- Tracks `LEX_*` style flags (`was_dollar`, `in_comment`, `pass_next`, etc.)
- Produces tokens with type and value
- Handles quote-aware character classification in one place

```python
class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.was_dollar = False      # LEX_WASDOL
        self.pass_next = False       # LEX_PASSNEXT (after backslash)
        self.in_comment = False      # LEX_INCOMMENT
        self.check_comment = True    # LEX_CKCOMMENT
        self.quote = QuoteState()

    def next_token(self) -> Token:
        # Single place for context-sensitive tokenization
        ...
```

**Bash reference:** `parse.y` lines 3055+ (`read_token`), lines 5305+ (`read_token_word`)

---

### 2. Mirror Bash's Parser State Flags

Bash has 28 `PST_*` flags that encode parsing context. Parable's 5 `ParseContext.kind` values are too coarse.

**Key flags to add:**

```python
class ParserState:
    PST_CASEPAT = 0x0001      # In case pattern list - ) is terminator not paren
    PST_CMDSUBST = 0x0002     # In $(...) - affects comment handling
    PST_CASESTMT = 0x0004     # Parsing case statement
    PST_CONDEXPR = 0x0008     # Inside [[ ]] - different quoting rules
    PST_COMPASSIGN = 0x0010   # In compound assignment x=(...)
    PST_ARITH = 0x0020        # In $((...)) - # is not comment
    PST_HEREDOC = 0x0040      # Reading heredoc body
    PST_REGEXP = 0x0080       # Parsing regex in [[ =~ ]]
    PST_EXTPAT = 0x0100       # Parsing extended pattern @(...) etc
    PST_ALLOWOPNBRC = 0x0200  # Allow open brace for function def
```

**Why it matters - these flags answer:**
- Is `#` a comment starter? (Not in arithmetic, not mid-word)
- Is `)` closing a subshell? (Not if in case pattern)
- Is `<` a redirect? (Not if in `[[ ]]` comparison)
- Are single quotes special? (Not in `$'...'` ANSI-C context)

**Bash reference:** `parser.h` lines 35-62

---

### 3. Add Token History

Bash tracks `current_token`, `last_read_token`, `token_before_that`, `two_tokens_ago`. This enables context-sensitive decisions.

```python
class Parser:
    def __init__(self, ...):
        self.token_history = [None, None, None, None]

    def record_token(self, token):
        self.token_history = [token] + self.token_history[:3]

    def last_token_was(self, *types):
        return self.token_history[1] and self.token_history[1].type in types
```

**Why it matters:**
- After `for`, expect `in` keyword
- After `case`, expect word then `in`
- After `;;`, back to pattern list
- After `{`, could be brace group or brace expansion

**Bash reference:** `parse.y` lines 283-286

---

### 4. Implement DOLBRACE State Machine

`${...}` parsing has specific states that affect quoting:

```python
class DolbraceState:
    PARAM = 0x01   # Reading parameter name: ${foo
    OP = 0x02      # Reading operator: ${foo%
    WORD = 0x04    # Reading word: ${foo%bar
    QUOTE = 0x40   # Single quote special in double quotes
    QUOTE2 = 0x80  # Single quote semi-special
```

**State transitions:**
```
${foo       → PARAM
${foo%      → OP
${foo%bar   → WORD (single quotes now literal)
${foo:-bar  → WORD (single quotes still special)
```

**Why it matters:**
- In `${foo%'bar'}`, single quotes are literal in WORD state
- In `${foo:-'bar'}`, single quotes are still special
- Without tracking this, quote handling in `${...}` is error-prone

**Bash reference:** `parse.y` lines 184-190, `subst.c`

---

### 5. Unify Boundary Detection with Parsing

**Current Parable approach:**
```python
# Step 1: Scan ahead to find where $(...) ends
end = _find_cmdsub_end(source, start)
content = source[start:end]

# Step 2: Parse the content separately
sub_parser = Parser(content)
result = sub_parser.parse()
```

**Problems:**
- Duplicate logic in scanner and parser
- Scanner must replicate all quote/context rules
- Easy for them to diverge

**Bash approach:** Single pass - lexer/parser work together. When `$(` is seen, parser state is saved, recursive parse happens, state is restored.

**Proposal:** Parse incrementally without pre-scanning:
```python
def parse_command_substitution(self):
    self.expect('$')
    self.expect('(')
    saved_state = self.save_state()
    self.state |= PST_CMDSUBST
    content = self.parse_compound_list()
    self.expect(')')
    self.restore_state(saved_state)
    return CommandSubstitution(content)
```

**Bash reference:** `parse.y` lines 4451+ (`parse_comsub`), lines 7220+ (`save_parser_state`)

---

### 6. Lexer State Flags (LEX_*)

If implementing a lexer, these flags are critical:

```python
class LexerState:
    LEX_WASDOL = 0x0001     # Last char was '$'
    LEX_CKCOMMENT = 0x0002  # Check for comments
    LEX_INCOMMENT = 0x0004  # Inside a comment
    LEX_PASSNEXT = 0x0008   # Last char was backslash (pass next char through)
    LEX_RESWDOK = 0x0010    # Reserved word ok here
    LEX_CKCASE = 0x0020     # Check for 'case'
    LEX_INCASE = 0x0040     # Inside case statement
    LEX_INHEREDOC = 0x0080  # Inside here-doc body
    LEX_HEREDELIM = 0x0100  # Reading here-doc delimiter
    LEX_STRIPDOC = 0x0200   # Strip tabs from here-doc (<<-)
    LEX_QUOTEDDOC = 0x0400  # Here-doc delimiter was quoted
    LEX_INWORD = 0x0800     # Inside a word
    LEX_GTLT = 0x1000       # Just saw < or >
    LEX_CKESAC = 0x2000     # Check for 'esac' after 'in'
```

**Bash reference:** `parse.y` lines 160-180

---

## Recommended Implementation Order

### Phase 1: Understand Failures (No Code Changes)

1. Run fuzzer extensively, collect failure cases
2. Categorize failures by type:
   - Quote context errors
   - Comment detection errors
   - Case pattern errors
   - Heredoc errors
   - Conditional expression errors
   - Arithmetic errors
3. Map each category to bash architectural patterns

### Phase 2: Add Parser State Flags

1. Expand `ParseContext` or add `ParserState` bitmask
2. Set flags at appropriate points in parsing
3. Use flags to make context-sensitive decisions
4. Test against categorized failures

### Phase 3: Add Token History

1. Add token history tracking to Parser
2. Use history for keyword recognition
3. Use history for context decisions (after `for`, after `case`, etc.)

### Phase 4: Introduce Lexer Layer (Incremental)

1. Create `Lexer` class with basic tokenization
2. Add `LEX_*` flags incrementally
3. Migrate Parser to consume tokens instead of characters
4. One construct at a time: start with simple words, then quotes, then expansions

### Phase 5: Implement DOLBRACE State Machine

1. Add `dolbrace_state` tracking to lexer/parser
2. Implement state transitions for `${...}` operators
3. Use state to determine quote behavior

### Phase 6: Unify Scanning and Parsing

1. Remove `_find_cmdsub_end` and similar boundary-detection functions
2. Implement save/restore state pattern
3. Parse nested constructs inline with state management

---

## Quick Wins (Before Major Refactors)

### Port Bash's Exact Conditional Checks

Many bugs can be fixed by porting bash's exact conditions. Example - bash's comment detection:

```c
/* Bash: Check for comments only in certain contexts */
if (character == '#' &&
    (parser_state & PST_CASEPAT) == 0 &&
    (parser_state & PST_ARITH) == 0 &&
    shellmeta(last_read_char))
```

Translate to Parable:
```python
def is_comment_start(self, ch: str) -> bool:
    if ch != '#':
        return False
    if self.state & PST_CASEPAT:
        return False
    if self.state & PST_ARITH:
        return False
    if self.pos == 0:
        return True
    prev = self.source[self.pos - 1]
    return prev in ' \t\n;|&(){'
```

### Study Specific Bash Functions

Key functions to study in `bash-oracle/parse.y`:
- `read_token()` (line 3055) - main tokenizer
- `read_token_word()` (line 5305) - word tokenization
- `parse_matched_pair()` (line 3877) - quote matching
- `parse_comsub()` (line 4451) - command substitution
- `parse_dparen()` (line 4650) - arithmetic

---

## Success Metrics

1. **Fuzzer convergence** - Fuzzer should find fewer novel differences over time
2. **Test coverage** - Existing tests continue to pass
3. **Code simplification** - Less duplicated logic between scanning and parsing
4. **Architectural alignment** - Data structures mirror bash's patterns

---

## References

- `bash-oracle/parse.y` - Main parser (10k+ lines)
- `bash-oracle/parser.h` - Parser structures and flags
- `bash-oracle/subst.c` - Parameter expansion
- `bash-oracle/expr.c` - Arithmetic evaluation
