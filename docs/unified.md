# Parable Development Guide

## Priorities

| Priority | Focus | Goal |
|----------|-------|------|
| P1 | Usability | Features for tool authors |
| P2 | Nice to have | Narrower use cases |

---

## P1: Usability

### Position tracking

AST nodes have no source location information. Required for syntax highlighters, linters, IDEs, source maps.

**Approach:** Store byte offsets (16 bytes/node). Compute line/column lazily. Opt-in to avoid overhead.

```python
ast = parse(code, track_positions=True)
node.start_offset  # always available
node.start_line    # computed on first access
node.start_col     # computed on first access
```

**Effort:** Medium

### JSON serialization

```python
ast.to_dict()  # For JSON serialization
ast.to_json()  # Direct JSON output
```

**Effort:** Low

### Visitor pattern

```python
class MyVisitor(Visitor):
    def visit_CommandSubstitution(self, node):
        print(f"Found command sub: {node}")

visitor = MyVisitor()
visitor.walk(ast)
```

**Effort:** Low

---

## P2: Nice to Have

### Error recovery

Parse incomplete/invalid input and return best-effort AST. Required for IDE use cases.

**Effort:** High | **Downside:** Partial ASTs confuse downstream tools. Recovery heuristics are brittle.

### Comments preservation

Attach comments to AST nodes. Required for formatters and doc generators.

**Effort:** Medium | **Downside:** Lexer rewrite. Ambiguous attachment (preceding or following node?).

### Source reconstruction

Reconstruct source from AST: `ast.to_source()`. Required for formatters and refactoring tools.

**Effort:** Medium | **Downside:** Either preserve whitespace (memory) or accept lossy reconstruction.

---

## Quality Analysis

Comparison against three reference parsers:

| Implementation | Language | Notable Qualities |
|----------------|----------|-------------------|
| Go compiler | Go | `got()`/`want()` helpers, grammar comments, nesting tracking |
| Crafting Interpreters | Java | `match()`/`consume()` helpers, error synchronization |
| Rob Pike's regex | C | Radical simplicity, ~30 lines |

### What's Good

- Clear grammar-to-method mapping: `parse_list()` → `parse_pipeline()` → `parse_compound_command()`
- Arithmetic parser follows Crafting Interpreters' precedence pattern
- No separate lexer (appropriate for bash's context-sensitive grammar)

### Issues by Category

#### A. Structure

**#1. `parse_word()` is a 300-line monolith**

Handles quotes, escapes, expansions, process substitution, extglob, arrays. Compare to Go's `operand()` (74 lines) or Crafting Interpreters' `primary()` (38 lines).

**#2. Duplicated expansion-parsing logic**

Same `$`-expansion handling in 4 places:
- `parse_word()` lines 243-397
- `_parse_command_substitution()` lines 529-587
- `_parse_cond_word()` lines 3067-3118
- `_parse_braced_param()` lines 2088-2176

**#3. Missing helper patterns**

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

Parable manually writes `if self.peek() == X: self.advance()` throughout.

**#4. Quote-scanning duplication**

Similar quote-aware scanning loops in `_parse_command_substitution()`, `_parse_heredoc()`, `_parse_braced_param()`, `parse_word()`.

#### B. Control Flow

| # | Issue | Severity | Effort |
|---|-------|----------|--------|
| 5 | Keyword dispatch (cascading if/elif) | Low | Low |
| 6 | Manual peek-advance (50+ times) | Medium | Low |
| 7 | Inconsistent error recovery | Medium | High |
| 8 | Deep nesting (5+ levels) | Low | Medium |
| 9 | Repeated boundary checks | Low | Low |
| 10 | Loop-and-accumulate patterns | Low | Low |
| 11 | Inconsistent `_skip_whitespace()` | Low | Low |

#### C. Performance

| # | Issue | Severity | Effort |
|---|-------|----------|--------|
| 12 | Repeated string scanning in `parse_word()` | Medium | High |
| 13 | Backtracking in ambiguous constructs | Low | Medium |

#### D. State Management

| Aspect | Go | Crafting Interpreters | Parable |
|--------|----|-----------------------|---------|
| State location | Explicit struct fields | Instance fields | Mix of instance + dynamic attrs |
| Position tracking | Single `pos` | Single `current` | `pos` + parallel `arith_pos` |
| Nesting tracking | `nestLev` counter | Call stack only | Multiple: `paren_depth`, `bracket_depth`, etc. |

| # | Issue | Severity | Effort |
|---|-------|----------|--------|
| 14 | Dynamic `_pending_heredoc_end` via `setattr()` | Medium | Low |
| 15 | Parallel cursor for arithmetic (`_arith_pos`) | Medium | Medium |
| 16 | Multiple depth counters | Low | Medium |
| 17 | No exception safety (no try/finally) | High | Medium |

#### E. AST Design

| Aspect | Go | Crafting Interpreters | Parable |
|--------|----|-----------------------|---------|
| Node count | ~80 | 21 (Expr) + 9 (Stmt) | 47 |
| Visitor pattern | No (type switches) | Yes (`Visitor<R>`) | No |
| Formatting | Separate printer | `AstPrinter` visitor | `to_sexp()` methods |

| # | Issue | Severity | Effort |
|---|-------|----------|--------|
| 18 | `Word.to_sexp()` is 480 lines | High | High |
| 19 | Mixed data and presentation | Medium | High |
| 20 | No visitor pattern | Medium | High |
| 21 | Redundant `kind` field | Low | Low |
| 22 | Inconsistent node granularity | Low | High |

#### F. Naming

| Convention | Go | Crafting Interpreters | Parable |
|------------|----|-----------------------|---------|
| Parse methods | `funcDecl()` | `function()` | `parse_function_definition()` |
| Helpers | `got()`, `want()` | `match()`, `consume()` | None |
| Private | Unexported | Private keyword | `_` prefix |

| # | Issue | Severity | Effort |
|---|-------|----------|--------|
| 23 | Verbose method names | Low | Medium |
| 24 | Inconsistent `_parse` vs `parse` prefix | Low | Low |
| 25 | Hungarian-ish parameters (`in_array_subscript`) | Low | Low |
| 26 | Abbreviation inconsistency | Low | Low |
| 27 | Boolean parameter proliferation | Medium | Medium |
| 28 | Unclear method boundaries | Low | Medium |
| 29 | No docstring conventions | Low | Medium |

#### G. API Design

| Aspect | Go | Crafting Interpreters | Parable |
|--------|----|-----------------------|---------|
| Entry point | `Parse(src)` | `new Parser(tokens).parse()` | `Parser(src).parse()` |
| Options | `Mode` flags | None | None |
| Error type | `Error` with `Pos` | `ParseError` | `ParseError` |

| # | Issue | Severity | Effort |
|---|-------|----------|--------|
| 30 | Limited public API | Medium | Low |
| 31 | No parse options | Medium | Medium |
| 32 | Error positions are offsets only | Medium | Low |
| 33 | No incremental parsing | Low | High |
| 34 | No AST location spans | Medium | Medium |
| 35 | Coupled to source string | Low | Medium |
| 36 | No syntax tree protocol | Medium | High |
| 37 | Mixed concerns in module | Low | Low |
| 38 | No version/dialect handling | Low | Medium |

---

## Optimization Opportunities

### 1. Inline Hot Path Methods

```python
# Current
def peek(self) -> str | None:
    if self.at_end():
        return None
    return self.source[self.pos]

# Optimized
def peek(self) -> str | None:
    return self.source[self.pos] if self.pos < self.length else None
```

**Impact:** 5-10% speedup | **LLM Impact:** Moderate — loses semantic abstraction

### 2. Cached Character Sets

```python
# Current
if ch in " \t\n":
    ...

# Optimized
_WHITESPACE_NEWLINE = frozenset(' \t\n')
if ch in _WHITESPACE_NEWLINE:
    ...
```

**Impact:** 3-5% speedup | **LLM Impact:** Low — common pattern

### 3. ASCII Range Checks

```python
# Current
if ch.isalpha() or ch == "_":
    ...

# Optimized
def _is_name_start(ch: str) -> bool:
    return ('a' <= ch <= 'z') or ('A' <= ch <= 'Z') or ch == '_'
```

**Impact:** 5-8% speedup | **LLM Impact:** Moderate — less intuitive than `.isalpha()`

Note: Bash identifiers are ASCII-only. `.isalpha()` accepts Unicode, which would be wrong.

### 4. `__slots__` on AST Nodes

```python
@dataclass(slots=True)
class Word(Node):
    value: str
    parts: list[Node] = field(default_factory=list)
```

**Impact:** 40-50% memory reduction | **LLM Impact:** Low — well-known pattern

### 5. Unchecked Advance Variant

```python
def _advance_unchecked(self) -> str:
    ch = self.source[self.pos]
    self.pos += 1
    return ch
```

**Impact:** 2-3% in tight loops | **LLM Impact:** High — two similar methods confuse

### 6. First-Character Dispatch

```python
_WORD_HANDLERS = {
    "'": '_handle_single_quote',
    '"': '_handle_double_quote',
    ...
}
handler = _WORD_HANDLERS.get(ch)
if handler:
    getattr(self, handler)(chars, parts)
```

**Impact:** 3-5% | **LLM Impact:** High — fragments logic, hard to trace

### 7. Table-Driven Arithmetic Precedence

Replace 27 explicit methods with precedence climbing algorithm.

**Impact:** 2-3% speedup, significant code reduction | **LLM Impact:** Very High — algorithm is hard for LLMs to modify correctly

### 8. Bulk Character Consumption

```python
# Current
name_chars = []
while not self.at_end() and (self.peek().isalnum() or self.peek() == "_"):
    name_chars.append(self.advance())
return "".join(name_chars)

# Optimized
start = self.pos
while pos < length and (('a' <= ch <= 'z') or ('A' <= ch <= 'Z') or ('0' <= ch <= '9') or ch == '_'):
    pos += 1
return source[start:pos]
```

**Impact:** 1-2% | **LLM Impact:** Low — slicing is idiomatic

### CPython Internals

**Membership testing:**
| Pattern | Time |
|---------|------|
| `x in set` | ~100 ns (O(1)) |
| `x in list` (miss) | ~11 ms (O(n)) |
| `x in "abc"` | O(n) linear scan |

Set literals in membership tests are compiled to `frozenset` at compile time.

**Local variable access:**
| Opcode | Relative Speed |
|--------|----------------|
| LOAD_FAST (local) | 1x |
| LOAD_ATTR (self.x) | ~2x slower |

Aliasing `source = self.source` in hot loops still helps, even in Python 3.11+.

**Function call overhead:** 50-100 ns per call.

---

## Decisions

### Performance

| Do | Optimization | Rationale |
|----|--------------|-----------|
| ✓ | Inline hot paths | 5-10% gain, acceptable LLM impact |
| ✓ | Cached character sets | Clean pattern, low LLM impact |
| ✓ | ASCII range checks | Correct for bash, moderate LLM impact |
| ✓ | `__slots__` on AST nodes | 40-50% memory, well-known |
| ✓ | Bulk consumption | Clearer intent than char-by-char |
| ✗ | Unchecked advance | Two similar methods confuse LLMs |
| ✗ | Dispatch tables | Fragments logic |
| ✗ | Table-driven precedence | Explicit methods are clearer |

### AST Formatting

For issue #18 (`Word.to_sexp()` 480 lines):

| Option | Approach | Verdict |
|--------|----------|---------|
| 1 | Visitor pattern | More infrastructure |
| 2 | Match statements | Python 3.10+ only |
| 3 | Extract to formatter module | **Use this** |

---

## Refactoring Plan

Phases ordered by dependency and risk:

| Phase | Task | Issues |
|-------|------|--------|
| 1 | Add `match()`/`consume()` helpers | #3, #6, #9 |
| 2 | Extract `_parse_expansion()` | #2 |
| 3 | Extract quote-aware scanner | #4 |
| 4 | Decompose `parse_word()` | #1 |
| 5 | Unify state management | #14, #17 |
| 6 | Consolidate depth tracking | #15, #16 |
| 7 | Extract formatters from AST | #18, #19 |
| 8 | Standardize naming | #23-29 |
| 9 | Improve API surface | #30-38 |

---

## References

- Go parser: `~/source/go/src/cmd/compile/internal/syntax/parser.go`
- Crafting Interpreters: `~/source/craftinginterpreters/java/com/craftinginterpreters/lox/Parser.java`
- Rob Pike's regex: `~/source/pike-regex/beautiful.html`
