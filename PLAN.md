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

**Remaining character-based:**
- `parse_word()` / `_parse_word_internal()` - full expansion parsing
- Newline handling in `parse_list()` - special heredoc/separator logic

---

## Progress on Path A

### Completed Steps
1. ✓ Move remaining expansion methods to Lexer (ansi_c_quote, locale_string, param_expansion)
2. ✓ EOF token mechanism implemented for command/process substitution
3. ✓ `parse_command()` now token-based for terminator detection (hybrid approach)

### Remaining Work
- Move `_parse_word_internal` to Lexer (optional - hybrid approach may be sufficient)
- Full token-based parsing for word consumption (if needed)

### Architecture Notes
The **hybrid approach** works well:
- Token-based terminator detection enables EOF token mechanism
- Character-based word parsing handles complex expansion logic
- Position syncing (`_sync_lexer()`, `_sync_parser()`) bridges the two modes

Moving `_parse_word_internal` to Lexer would require extensive callback usage since expansion parsing (especially command substitution) needs `parse_list()`. The hybrid approach avoids this complexity while still achieving the key goal: proper tokenizer-parser separation for terminators.

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
| `_parse_word_internal`         | orchestrates all expansion methods           |

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
