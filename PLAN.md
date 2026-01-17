# Parable Lexer Evolution Plan

## Goal

Match bash's parsing behavior exactly by mirroring bash's architectural patterns. The fuzzer consistently finds differences due to context-sensitive complexities that require proper tokenizer-parser separation.

---

## Architecture Comparison

| Aspect | Bash | Parable (Current) |
|--------|------|-------------------|
| **Token Stream** | `yylex()` produces tokens | Parser does character-level parsing |
| **Parser State** | 28 `PST_*` flags in bitmask | `ParserStateFlags` (partial) |
| **Lexer State** | 16 `LEX_*` flags | Lexer exists but Parser bypasses it |
| **Quote State** | `struct dstack` with push/pop | `QuoteState` class ✓ |
| **Token History** | Last 4 tokens tracked | `_token_history` ✓ |
| **Dollar-Brace** | `DOLBRACE_*` state machine | `DolbraceState` ✓ |
| **Nested Parsing** | Save/restore full state | Sub-parser instances |

---

## Key Insight (January 2026)

**The Parser is character-based, not token-based.**

We attempted to implement bash's `shell_eof_token` mechanism to eliminate sub-parsers. It failed because:

```
Bash:     Tokenizer (read_token/yylex) → tokens → Parser (yyparse)
Parable:  Parser.parse_list() calls self.peek()/advance() directly
```

Functions like `parse_list()`, `parse_command()`, `parse_pipeline()` bypass the Lexer entirely. Even when we set `_eof_token` on the Lexer, the Parser never sees it.

**The EOF token mechanism is a consequence of tokenizer-parser architecture, not something that can be bolted on.**

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

The Lexer exists and has significant functionality, but the Parser mostly ignores it. Key parsing functions do character-level parsing directly:

```python
# Current pattern (character-based):
def parse_command(self):
    while True:
        self.skip_whitespace()
        if self.at_end():    # Parser.at_end()
            break
        ch = self.peek()     # Parser.peek() - bypasses Lexer!
        ...
```

The methods that were moved to Lexer work via callbacks - the Lexer calls back to Parser methods, creating bidirectional dependencies.

---

## Two Paths Forward

### Path A: Move Methods First (Incremental)
1. Move remaining expansion methods to Lexer (keep sub-parsers)
2. Move `_parse_word_internal` to Lexer
3. Make Parser use Lexer for tokenization
4. Implement EOF token mechanism → remove sub-parsers

**Pros:** Lower risk, incremental progress
**Cons:** Carries sub-parsers and bidirectional callbacks longer

### Path B: Make Parser Token-Based First (Direct)
1. Refactor `parse_command()`, `parse_list()`, etc. to use `_lex_next_token()`
2. EOF token mechanism works naturally
3. Move methods to Lexer cleanly (no sub-parsers needed)

**Pros:** Cleaner architecture, enables all blocked work
**Cons:** Higher risk, touches core parsing loop

---

## Blocked Work (Requires Token-Based Parser)

### EOF Token Mechanism
Set `)` as EOF token for `$()`, have Lexer return EOF, parser stops automatically. Eliminates ~350 lines of scanning code and sub-parser creation.

### Unified Scanning/Parsing
Remove `_find_cmdsub_end` and similar pre-scanning functions. Parse nested constructs inline with save/restore state.

### Clean Lexer Migration
Move `_parse_command_substitution`, `_parse_backtick_substitution`, etc. to Lexer without sub-parsers or Parser callbacks.

---

## Methods Still in Parser (Need Sub-Parsers)

| Method | Why |
|--------|-----|
| `_parse_arithmetic_expansion` | calls `parse_list()` |
| `_parse_command_substitution` | creates sub-parser |
| `_parse_backtick_substitution` | creates sub-parser |
| `_parse_process_substitution` | creates sub-parser |
| `_parse_array_literal` | may create sub-parser |
| `_parse_dollar_expansion` | dispatcher |
| `_parse_word_internal` | orchestrates all |

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
