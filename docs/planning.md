# Parable Development Guide

Decisions in this document follow the [project philosophy](../README.md#philosophy):

1. **LLM-driven development** — clarity wins over performance; verbose beats clever
2. **Match bash exactly** — bash is the oracle
3. **Pure Python** — one parser file, one AST file
4. **Fast as possible** — pay the cost for clarity, then claw back every microsecond

---

## Priorities

| Priority | Focus                 | Goal                   |
| -------- | --------------------- | ---------------------- |
| P1       | Essential usability   | So others can use this |
| P2       | Quality & performance | Internal improvements  |
| P3       | Nice to have          | Narrower use cases     |

| Priority   | Category     | Item                            | Rationale                            |
| ---------- | ------------ | ------------------------------- | ------------------------------------ |
| **P1**     | Usability    | Position tracking (#32)         | Linters, IDEs, source maps need it   |
| **P1**     | Usability    | JSON serialization              | Interop with other tools             |
| **P1**     | Usability    | Line/column in errors (#30)     | Users can't debug without this       |
|            |              |                                 |                                      |
| **P2**     | Performance  | Inline hot paths                | 5-10% gain, low clarity cost         |
| **P2**     | Performance  | Cached character sets           | 3-5% gain, common pattern            |
| **P2**     | Performance  | ASCII range checks              | 5-8% gain, correct for bash          |
| **P2**     | Performance  | `__slots__` on AST nodes        | 40-50% memory                        |
| **P2**     | Performance  | Bulk consumption                | Clearer intent                       |
| **P2**     | Quality      | Exception safety (#17)          | High severity, state corruption risk |
| **P2**     | Quality      | Extract `to_sexp()` (#18-19)    | High severity, 480-line method       |
| **P2**     | Quality      | Add helpers (#3, #6, #9)        | Foundation for other refactoring     |
|            |              |                                 |                                      |
| **P3**     | Nice to have | Error recovery                  | IDE use cases only                   |
| **P3**     | Nice to have | Comments preservation           | Formatters only                      |
| **P3**     | Nice to have | Source reconstruction           | Formatters only                      |
| **P3**     | Quality      | Decompose `parse_word()` (#1-4) | Depends on P2 helpers                |
|            |              |                                 |                                      |
| **Future** |              | Incremental parsing (#31)       | High effort, narrow use              |
| **Future** |              | Syntax tree protocol (#34)      | High effort                          |
| **Future** |              | Dialect handling (#36)          | Low severity                         |
| **Future** |              | Naming standardization (#22-27) | Low severity, cosmetic               |
| **Future** |              | Rejected optimizations          | Violate [1]                          |

---

## P1: Essential Usability

So others can use Parable as a tool. Correctness [2] assumed; approaches follow [1] (clarity) and [3] (simplicity).

### Position tracking

AST nodes have no source location information (#32). Required for syntax highlighters, linters, IDEs, source maps.

**Approach:** Store byte offsets (start + end = 16 bytes/node). Compute line/column lazily. Opt-in to avoid overhead when not needed [4].

```python
ast = parse(code, track_positions=True)
node.start_offset  # always available
node.end_offset    # always available
node.start_line    # computed on first access
```

**Effort:** Medium

### JSON serialization

```python
ast.to_dict()  # For JSON serialization
ast.to_json()  # Direct JSON output
```

**Effort:** Low

### Line/column in errors

Error positions are currently byte offsets only (#30). Users must compute line/column themselves.

**Approach:** Include line/column in `ParseError`. Compute from offset using line index.

**Effort:** Low

---

## P2: Quality & Performance

Internal improvements per [1] (clarity) and [4] (fast as possible).

### Performance

See [Optimization Opportunities](#optimization-opportunities) for details. Approved optimizations:

- Inline hot paths (5-10%)
- Cached character sets (3-5%)
- ASCII range checks (5-8%)
- `__slots__` on AST nodes (40-50% memory)
- Bulk consumption (1-2%)

### Quality

Priority refactoring from [Quality Analysis](#quality-analysis):

| Task                              | Issues     | Rationale                       | Dependency |
| --------------------------------- | ---------- | ------------------------------- | ---------- |
| Add `match()`/`consume()` helpers | #3, #6, #9 | Foundation for other work       | None       |
| Exception safety                  | #17        | High severity, state corruption | None       |
| Extract `to_sexp()` formatters    | #18, #19   | High severity, 480-line method  | None       |

**AST Formatting approach** for #18: Extract to formatter module with explicit `isinstance()` chains [1, 3]. Visitor pattern rejected (clever indirection violates [1]).

---

## P3: Nice to Have

Narrower use cases or dependencies on P2 work.

### Error recovery

Parse incomplete/invalid input and return best-effort AST. Required for IDE use cases.

**Effort:** High | **Downside:** Partial ASTs confuse downstream tools. Recovery heuristics are brittle.

### Comments preservation

Attach comments to AST nodes. Required for formatters and doc generators.

**Effort:** Medium | **Downside:** Lexer rewrite. Ambiguous attachment (preceding or following node?).

### Source reconstruction

Reconstruct source from AST: `ast.to_source()`. Required for formatters and refactoring tools.

**Effort:** Medium | **Downside:** Either preserve whitespace (memory) or accept lossy reconstruction.

### Decompose parse_word()

Issue #1: 300-line monolith. **Dependency:** P2 helpers must be in place first. Consider #2 (expansion logic) and #4 (quote scanning) as part of this work.

---

## Quality Analysis

Comparison against three reference parsers:

| Implementation        | Language | Notable Qualities                                            |
| --------------------- | -------- | ------------------------------------------------------------ |
| Go compiler           | Go       | `got()`/`want()` helpers, grammar comments, nesting tracking |
| Crafting Interpreters | Java     | `match()`/`consume()` helpers, error synchronization         |
| Rob Pike's regex      | C        | Radical simplicity, ~30 lines                                |

### What's Good

Per **LLM-driven development** [1] and **Pure Python** [3]:

- Clear grammar-to-method mapping: `parse_list()` → `parse_pipeline()` → `parse_compound_command()` — verbose, traceable [1]
- Arithmetic parser follows Crafting Interpreters' precedence pattern — explicit over clever [1]
- No separate lexer — appropriate for bash's context-sensitive grammar; fewer moving parts [3]

### Issues by Category

#### A. Structure

**#1. `parse_word()` is a 300-line monolith**

Handles quotes, escapes, expansions, process substitution, extglob, arrays. Compare to Go's `operand()` (74 lines) or Crafting Interpreters' `primary()` (38 lines).

**#2. Duplicated expansion-parsing logic**

Same `$`-expansion handling in 4 places:
- `parse_word()`
- `_parse_command_substitution()`
- `_parse_cond_word()`
- `_parse_braced_param()`

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

| #   | Issue                                | Severity | Effort |
| --- | ------------------------------------ | -------- | ------ |
| 5   | Keyword dispatch (cascading if/elif) | Low      | Low    |
| 6   | Manual peek-advance (50+ times)      | Medium   | Low    |
| 7   | Inconsistent error recovery          | Medium   | High   |
| 8   | Deep nesting (5+ levels)             | Low      | Medium |
| 9   | Repeated boundary checks             | Low      | Low    |
| 10  | Loop-and-accumulate patterns         | Low      | Low    |
| 11  | Inconsistent `_skip_whitespace()`    | Low      | Low    |

#### C. Performance

| #   | Issue                                      | Severity | Effort |
| --- | ------------------------------------------ | -------- | ------ |
| 12  | Repeated string scanning in `parse_word()` | Medium   | High   |
| 13  | Backtracking in ambiguous constructs       | Low      | Medium |

#### D. State Management

| Aspect            | Go                           | Crafting Interpreters  | Parable                                        |
| ----------------- | ---------------------------- | ---------------------- | ---------------------------------------------- |
| State location    | Explicit struct fields       | Instance fields        | Mix of instance + dynamic attrs                |
| Position tracking | Single `pos`                 | Single `current`       | `pos` + parallel `arith_pos`                   |
| Lookahead         | `tok`, `lit` (current token) | `tokens[current]`      | Direct `source[pos]` access                    |
| Nesting tracking  | `nestLev` counter            | Call stack only        | Multiple: `paren_depth`, `bracket_depth`, etc. |
| Mode flags        | Implicit in call stack       | Implicit in call stack | Explicit `in_*` parameters                     |

| #   | Issue                                          | Severity | Effort |
| --- | ---------------------------------------------- | -------- | ------ |
| 14  | Dynamic `_pending_heredoc_end` via `setattr()` | Medium   | Low    |
| 15  | Parallel cursor for arithmetic (`_arith_pos`)  | Medium   | Medium |
| 16  | Multiple depth counters                        | Low      | Medium |
| 17  | No exception safety (no try/finally)           | High     | Medium |

#### E. AST Design

| Aspect           | Go                   | Crafting Interpreters | Parable              |
| ---------------- | -------------------- | --------------------- | -------------------- |
| Node count       | ~80                  | 21 (Expr) + 9 (Stmt)  | 47                   |
| Definition style | Structs              | Generated classes     | Dataclasses          |
| Visitor pattern  | No (type switches)   | Yes (`Visitor<R>`)    | No                   |
| Position info    | Explicit `Pos` field | Token reference       | Implicit from source |
| Formatting       | Separate printer     | `AstPrinter` visitor  | `to_sexp()` methods  |

| #   | Issue                         | Severity | Effort |
| --- | ----------------------------- | -------- | ------ |
| 18  | `Word.to_sexp()` is 480 lines | High     | High   |
| 19  | Mixed data and presentation   | Medium   | High   |
| 20  | Redundant `kind` field        | Low      | Low    |
| 21  | Inconsistent node granularity | Low      | High   |

#### F. Naming

| Convention      | Go                | Crafting Interpreters  | Parable                       |
| --------------- | ----------------- | ---------------------- | ----------------------------- |
| Parse methods   | `funcDecl()`      | `function()`           | `parse_function_definition()` |
| Helpers         | `got()`, `want()` | `match()`, `consume()` | None                          |
| Private         | Unexported        | Private keyword        | `_` prefix                    |
| Boolean methods | `is*`             | `is*`, `check*`        | Mixed                         |

| #   | Issue                                           | Severity | Effort |
| --- | ----------------------------------------------- | -------- | ------ |
| 22  | Inconsistent `_parse` vs `parse` prefix         | Low      | Low    |
| 23  | Hungarian-ish parameters (`in_array_subscript`) | Low      | Low    |
| 24  | Abbreviation inconsistency                      | Low      | Low    |
| 25  | Boolean parameter proliferation                 | Medium   | Medium |
| 26  | Unclear method boundaries                       | Low      | Medium |
| 27  | No docstring conventions                        | Low      | Medium |

Note: "Verbose method names" removed — verbosity is a feature per [1].

#### G. API Design

| Aspect      | Go                  | Crafting Interpreters        | Parable               |
| ----------- | ------------------- | ---------------------------- | --------------------- |
| Entry point | `Parse(src)`        | `new Parser(tokens).parse()` | `Parser(src).parse()` |
| Options     | `Mode` flags        | None                         | None                  |
| Error type  | `Error` with `Pos`  | `ParseError`                 | `ParseError`          |
| Re-entrancy | New parser per file | New parser per input         | Stateful instance     |

| #   | Issue                            | Severity | Effort |
| --- | -------------------------------- | -------- | ------ |
| 28  | Limited public API               | Medium   | Low    |
| 29  | No parse options                 | Medium   | Medium |
| 30  | Error positions are offsets only | Medium   | Low    |
| 31  | No incremental parsing           | Low      | High   |
| 32  | No AST location spans            | Medium   | Medium |
| 33  | Coupled to source string         | Low      | Medium |
| 34  | No syntax tree protocol          | Medium   | High   |
| 35  | Mixed concerns in module         | Low      | Low    |
| 36  | No version/dialect handling      | Low      | Medium |

---

## Optimization Opportunities

Each optimization is assessed for speed gain and clarity cost per principle [1] (LLM-driven development) and [4] (fast as possible).

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

**Impact:** 5-10% speedup | **Clarity cost:** Moderate — loses semantic abstraction

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

**Impact:** 3-5% speedup | **Clarity cost:** Low — common pattern

### 3. ASCII Range Checks

```python
# Current
if ch.isalpha() or ch == "_":
    ...

# Optimized
def _is_name_start(ch: str) -> bool:
    return ('a' <= ch <= 'z') or ('A' <= ch <= 'Z') or ch == '_'
```

**Impact:** 5-8% speedup | **Clarity cost:** Moderate — less intuitive than `.isalpha()`

Note: Bash identifiers are ASCII-only. `.isalpha()` accepts Unicode, which would be wrong.

### 4. `__slots__` on AST Nodes

```python
@dataclass(slots=True)
class Word(Node):
    value: str
    parts: list[Node] = field(default_factory=list)
```

**Impact:** 40-50% memory reduction | **Clarity cost:** Low — well-known pattern

### 5. Unchecked Advance Variant

```python
def _advance_unchecked(self) -> str:
    ch = self.source[self.pos]
    self.pos += 1
    return ch
```

**Impact:** 2-3% in tight loops | **Clarity cost:** High — two similar methods confuse

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

**Impact:** 3-5% | **Clarity cost:** High — fragments logic, hard to trace

### 7. Table-Driven Arithmetic Precedence

Replace 27 explicit methods with precedence climbing algorithm.

**Impact:** 2-3% speedup, significant code reduction | **Clarity cost:** Very High — algorithm is hard to modify correctly

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

**Impact:** 1-2% | **Clarity cost:** Low — slicing is idiomatic

### CPython Internals

Reference data for optimization decisions per [4] (fast as possible).

**Membership testing:**
| Pattern            | Time             |
| ------------------ | ---------------- |
| `x in set`         | ~100 ns (O(1))   |
| `x in list` (miss) | ~11 ms (O(n))    |
| `x in "abc"`       | O(n) linear scan |

Set literals in membership tests are compiled to `frozenset` at compile time.

**Local variable access:**
| Opcode             | Relative Speed |
| ------------------ | -------------- |
| LOAD_FAST (local)  | 1x             |
| LOAD_ATTR (self.x) | ~2x slower     |

Aliasing `source = self.source` in hot loops still helps, even in Python 3.11+.

**Function call overhead:** 50-100 ns per call.

### Summary

| # | Optimization | Verdict | Rationale |
|---|--------------|---------|-----------|
| 1 | Inline hot paths | ✓ | Low clarity cost |
| 2 | Cached character sets | ✓ | Common pattern |
| 3 | ASCII range checks | ✓ | Correct for bash |
| 4 | `__slots__` on AST nodes | ✓ | Well-known pattern |
| 5 | Unchecked advance | ✗ | Two similar methods confuse [1] |
| 6 | First-character dispatch | ✗ | Fragments logic [1] |
| 7 | Table-driven precedence | ✗ | Hard to modify [1] |
| 8 | Bulk consumption | ✓ | Idiomatic slicing |

---

## References

- Go parser: `~/source/go/src/cmd/compile/internal/syntax/parser.go`
- Crafting Interpreters: `~/source/craftinginterpreters/java/com/craftinginterpreters/lox/Parser.java`
- Rob Pike's regex: `~/source/pike-regex/beautiful.html`
