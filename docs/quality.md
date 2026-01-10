# Parser Quality Analysis

Comparison of `src/parable/core/parser.py` against three well-regarded recursive descent parsers:

| Implementation | Language | Notable Qualities |
|----------------|----------|-------------------|
| Go compiler | Go | Single-file parser, `got()`/`want()` helpers, grammar comments, nesting tracking |
| Crafting Interpreters | Java | Clean precedence-by-call-depth, `match()`/`consume()` helpers, error synchronization |
| Rob Pike's regex | C | Radical simplicity, recursion as design method, ~30 lines |

## Current State

**Structure (good):**
- Clear grammar-to-method mapping: `parse_list()` → `parse_pipeline()` → `parse_compound_command()` → specific constructs
- Arithmetic expression parser follows Crafting Interpreters' precedence pattern exactly
- No separate lexer - appropriate for bash's context-sensitive grammar

**Size:** ~4700 lines, single file

## Issues

### 1. `parse_word()` is a 300-line monolith (lines 190-489)

Handles too many concerns:
- Quote parsing (single, double, ANSI-C, locale)
- Escape handling
- Bracket depth tracking for array subscripts
- Parameter expansions (`$var`, `${...}`)
- Command substitution (`$(...)`, backticks)
- Arithmetic expansion (`$((...))`, `$[...]`)
- Process substitution (`<(...)`, `>(...)`)
- Extglob patterns (`@()`, `?()`, `*()`, `+()`, `!()`)
- Array literals

Compare to Go's `operand()` (74 lines) or Crafting Interpreters' `primary()` (38 lines) - both delegate aggressively.

### 2. Duplicated expansion-parsing logic

The same `$`-expansion handling appears in:
- `parse_word()` lines 243-397
- `_parse_command_substitution()` lines 529-587
- `_parse_cond_word()` lines 3067-3118
- `_parse_braced_param()` lines 2088-2176

Each has slightly different quoting context but the core logic (detect `$((`, `$(`, `${`, `$var`) is repeated.

### 3. Missing helper patterns

Go has:
```go
func (p *parser) got(tok token) bool {
    if p.tok == tok { p.next(); return true }
    return false
}
func (p *parser) want(tok token) {
    if !p.got(tok) { p.syntaxError("expected " + tokstring(tok)) }
}
```

Crafting Interpreters has:
```java
private boolean match(TokenType... types) { ... }
private Token consume(TokenType type, String message) { ... }
```

Parable manually writes `if self.peek() == X: self.advance()` patterns throughout.

### 4. Quote-scanning duplication

Similar quote-aware scanning loops appear in:
- `_parse_command_substitution()` - finding matching `)`
- `_parse_heredoc()` - finding line end
- `_parse_braced_param()` - finding matching `}`
- `parse_word()` - handling double quotes

## Refactoring Plan

### Phase 1: Extract helpers

```python
def got(self, ch: str) -> bool:
    """Consume character if it matches, return success."""
    if not self.at_end() and self.peek() == ch:
        self.advance()
        return True
    return False

def want(self, ch: str) -> None:
    """Consume character or raise error."""
    if not self.got(ch):
        raise ParseError(f"Expected '{ch}'", pos=self.pos)

def match(self, s: str) -> bool:
    """Check if next characters match s (without consuming)."""
    return self.source[self.pos:self.pos + len(s)] == s

def consume(self, s: str) -> bool:
    """If next chars match s, consume them and return True."""
    if self.match(s):
        self.pos += len(s)
        return True
    return False
```

### Phase 2: Extract expansion parsing

```python
def _parse_expansion(self) -> tuple[Node | None, str]:
    """Parse any $-expansion at current position.

    Handles: $var, ${...}, $((...)), $(...), $'...', $"..."
    Returns (node, raw_text) or (None, "") if not an expansion.
    """
    ...
```

Call from `parse_word()`, `_parse_cond_word()`, and double-quote loops.

### Phase 3: Extract quote-aware scanning

```python
def _scan_to_closer(self, closer: str, *,
                     track_parens: bool = False,
                     track_braces: bool = False) -> str:
    """Scan forward to closing delimiter, respecting quotes and nesting."""
    ...
```

### Phase 4: Decompose `parse_word()`

Split into:
1. `_parse_single_quoted()` - trivial, no expansions
2. `_parse_double_quoted()` - calls `_parse_expansion()`
3. `_parse_unquoted_segment()` - metachar termination + expansions
4. `parse_word()` - orchestrates the above, tracks bracket depth

## References

- Go parser: `~/source/go/src/cmd/compile/internal/syntax/parser.go`
- Crafting Interpreters: `~/source/craftinginterpreters/java/com/craftinginterpreters/lox/Parser.java`
- Pike regex: `~/source/pike-regex/beautiful.html`
