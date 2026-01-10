# Parser Quality Analysis

Comparison of `src/parable/core/parser.py` against three well-regarded recursive descent parsers:

| Implementation        | Language | Notable Qualities                                                                    |
| --------------------- | -------- | ------------------------------------------------------------------------------------ |
| Go compiler           | Go       | Single-file parser, `got()`/`want()` helpers, grammar comments, nesting tracking     |
| Crafting Interpreters | Java     | Clean precedence-by-call-depth, `match()`/`consume()` helpers, error synchronization |
| Rob Pike's regex      | C        | Radical simplicity, recursion as design method, ~30 lines                            |

## What's Good

**Structure:**
- Clear grammar-to-method mapping: `parse_list()` → `parse_pipeline()` → `parse_compound_command()` → specific constructs
- Arithmetic expression parser follows Crafting Interpreters' precedence pattern exactly
- No separate lexer - appropriate for bash's context-sensitive grammar

**Size:** ~4700 lines, single file

## Issues

### A. Parser Structure

**#1. `parse_word()` is a 300-line monolith (lines 190-489)**

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

**#2. Duplicated expansion-parsing logic**

The same `$`-expansion handling appears in:
- `parse_word()` lines 243-397
- `_parse_command_substitution()` lines 529-587
- `_parse_cond_word()` lines 3067-3118
- `_parse_braced_param()` lines 2088-2176

Each has slightly different quoting context but the core logic (detect `$((`, `$(`, `${`, `$var`) is repeated.

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

Parable manually writes `if self.peek() == X: self.advance()` patterns throughout.

**#4. Quote-scanning duplication**

Similar quote-aware scanning loops appear in:
- `_parse_command_substitution()` - finding matching `)`
- `_parse_heredoc()` - finding line end
- `_parse_braced_param()` - finding matching `}`
- `parse_word()` - handling double quotes

### B. Control Flow

**#5. Repeated keyword-dispatch pattern**

`parse_compound_command()` uses cascading if/elif for keywords. Go and Crafting Interpreters use `match()` helper returning bool to make dispatch cleaner.

**#6. Manual peek-advance sequences**

The pattern `if self.peek() == X: self.advance()` appears 50+ times. Reference parsers encapsulate this in `got()` or `match()`.

**#7. Inconsistent error recovery**

Some methods raise immediately, others attempt recovery. No systematic synchronization like Crafting Interpreters' `synchronize()`.

**#8. Deep nesting in conditionals**

Several methods have 5+ levels of nesting. Reference parsers keep methods flat by early returns and delegation.

**#9. Repeated boundary checks**

`if not self.at_end() and self.peek() == ...` appears frequently. A `check()` method could encapsulate this.

**#10. Loop-and-accumulate patterns**

Many methods build lists with `while` loops and `.append()`. Could use helper methods that return lists.

**#11. Inconsistent use of `_skip_whitespace()`**

Called explicitly in some contexts, implicit in others. Creates confusion about parser state after method calls.

### C. Performance

**#12. Repeated string scanning**

`parse_word()` rescans for quotes, expansions, and metachars in overlapping passes. A single-pass approach would be faster.

**#13. Backtracking in ambiguous constructs**

Some constructs require saving position and restoring on failure. Could be reduced with better lookahead.

### D. State Management

| Aspect            | Go                           | Crafting Interpreters  | Parable                                        |
| ----------------- | ---------------------------- | ---------------------- | ---------------------------------------------- |
| State location    | Explicit struct fields       | Instance fields        | Mix of instance + dynamic attrs                |
| Position tracking | Single `pos`                 | Single `current`       | `pos` + parallel `arith_pos`                   |
| Lookahead         | `tok`, `lit` (current token) | `tokens[current]`      | Direct `source[pos]` access                    |
| Nesting tracking  | `nestLev` counter            | Call stack only        | Multiple: `paren_depth`, `bracket_depth`, etc. |
| Mode flags        | Implicit in call stack       | Implicit in call stack | Explicit `in_*` parameters                     |

**#14. Dynamic attribute `_pending_heredoc_end`**

Created at runtime with `setattr()`, invisible to static analysis:
```python
self._pending_heredoc_end = end_pos
```

**#15. Parallel cursor for arithmetic**

`_arith_pos`, `_arith_source` duplicate the main position tracking, creating synchronization risk.

**#16. Multiple depth counters**

`paren_depth`, `bracket_depth`, `brace_depth` tracked separately rather than unified nesting stack.

**#17. No exception safety**

State mutations aren't protected by try/finally. Parse failures can leave state corrupted.

### E. AST Design

| Aspect           | Go                   | Crafting Interpreters | Parable              |
| ---------------- | -------------------- | --------------------- | -------------------- |
| Node count       | ~80                  | 21 (Expr) + 9 (Stmt)  | 47                   |
| Definition style | Structs              | Generated classes     | Dataclasses          |
| Visitor pattern  | No (type switches)   | Yes (`Visitor<R>`)    | No                   |
| Position info    | Explicit `Pos` field | Token reference       | Implicit from source |
| Formatting       | Separate printer     | `AstPrinter` visitor  | `to_sexp()` methods  |

**#18. `Word.to_sexp()` is 480 lines**

A single method handles formatting for all word part types. Should be separate formatter or visitor.

**#19. Mixed data and presentation**

AST nodes contain both structural data and formatting logic (`to_sexp()`). Violates single responsibility.

**#20. No visitor pattern**

Operations on AST require type-checking with `isinstance()` throughout. Reference parsers use visitor or pattern matching.

**#21. Redundant `kind` field**

Some nodes have a `kind` discriminator that duplicates type information available from the class itself.

**#22. Inconsistent node granularity**

Some constructs get their own node type, others are represented as generic `Word` with parts. Inconsistent abstraction level.

### F. Naming

| Convention      | Go                     | Crafting Interpreters  | Parable                       |
| --------------- | ---------------------- | ---------------------- | ----------------------------- |
| Parse methods   | `funcDecl()`           | `function()`           | `parse_function_definition()` |
| Helpers         | `got()`, `want()`      | `match()`, `consume()` | None (inline code)            |
| Private         | Unexported (lowercase) | Private keyword        | `_` prefix                    |
| Boolean methods | `is*`                  | `is*`, `check*`        | Mixed                         |

**#23. Verbose method names**

`parse_compound_command()` vs Go's `compoundStmt()` or Crafting's `statement()`. Prefixes add noise.

**#24. Inconsistent `_parse` vs `parse` prefix**

Public methods use `parse_`, private use `_parse_`, but distinction unclear for internal-only methods.

**#25. Hungarian-ish parameter names**

Parameters like `in_array_subscript` read as type annotations rather than descriptive names.

**#26. Abbreviation inconsistency**

Mix of `pos` (abbreviated) and `position` (full), `cmd` and `command`.

**#27. Boolean parameter proliferation**

Methods take many boolean flags (`allow_empty`, `in_array`, `for_case_pattern`) instead of mode enums or options objects.

**#28. Unclear method boundaries**

Hard to tell from names what `_parse_braced_param()` returns vs what `_parse_parameter_expansion()` returns.

**#29. No docstring conventions**

Some methods have docstrings, others don't. No consistent format for parameters/returns.

### G. API Design

| Aspect      | Go                  | Crafting Interpreters        | Parable               |
| ----------- | ------------------- | ---------------------------- | --------------------- |
| Entry point | `Parse(src)`        | `new Parser(tokens).parse()` | `Parser(src).parse()` |
| Options     | `Mode` flags        | None                         | None                  |
| Error type  | `Error` with `Pos`  | `ParseError`                 | `ParseError`          |
| Re-entrancy | New parser per file | New parser per input         | Stateful instance     |

**#30. Limited public API**

Only `Parser.parse()` is clearly public. Internal methods exposed without clear contract.

**#31. No parse options**

Can't configure behavior (e.g., strict mode, error recovery, dialect).

**#32. Error positions are offsets only**

No line/column info in errors. Users must compute from source.

**#33. No incremental parsing**

Must reparse entire source on any change. No support for partial updates.

**#34. No AST location spans**

Nodes don't track start/end positions in source. Limits tooling (refactoring, highlighting).

**#35. Coupled to source string**

Parser holds reference to source. Can't parse from streams or iterators.

**#36. No syntax tree protocol**

No standard interface for walking/transforming AST. Each tool reimplements traversal.

**#37. Mixed concerns in module**

`parser.py` contains Parser, error types, and helper functions. Could be split.

**#38. No version/dialect handling**

Bash versions differ (4.x vs 5.x features). No way to specify target.

## Refactoring Plan

### Phase 1: Add `match()`/`consume()` helpers
Extract common peek-advance patterns. Low risk, immediate readability wins.

### Phase 2: Extract `_parse_expansion()`
Unify `$`-expansion handling from 4 locations. Moderate complexity.

### Phase 3: Extract quote-aware scanner
Create `_scan_to_closer()` for balanced delimiter finding.

### Phase 4: Decompose `parse_word()`
Split into `_parse_single_quoted()`, `_parse_double_quoted()`, `_parse_unquoted_segment()`.

### Phase 5: Unify state management
Replace dynamic attributes with explicit fields. Add try/finally guards.

### Phase 6: Consolidate depth tracking
Replace multiple counters with nesting stack or unified approach.

### Phase 7: Extract formatters from AST
Move `to_sexp()` logic to separate visitor/formatter module.

### Phase 8: Standardize naming
Adopt consistent conventions for methods, parameters, abbreviations.

### Phase 9: Improve API surface
Add options, location info, clear public/private boundary.

## Issue Tracker

| #   | Category  | Issue                          | Severity | Effort |
| --- | --------- | ------------------------------ | -------- | ------ |
| 1   | Structure | `parse_word()` monolith        | High     | High   |
| 2   | Structure | Duplicated expansion logic     | High     | Medium |
| 3   | Structure | Missing helpers                | Medium   | Low    |
| 4   | Structure | Quote-scanning duplication     | Medium   | Medium |
| 5   | Control   | Keyword dispatch               | Low      | Low    |
| 6   | Control   | Manual peek-advance            | Medium   | Low    |
| 7   | Control   | Inconsistent error recovery    | Medium   | High   |
| 8   | Control   | Deep nesting                   | Low      | Medium |
| 9   | Control   | Repeated boundary checks       | Low      | Low    |
| 10  | Control   | Loop-accumulate patterns       | Low      | Low    |
| 11  | Control   | Inconsistent whitespace        | Low      | Low    |
| 12  | Perf      | Repeated scanning              | Medium   | High   |
| 13  | Perf      | Backtracking                   | Low      | Medium |
| 14  | State     | Dynamic `_pending_heredoc_end` | Medium   | Low    |
| 15  | State     | Parallel arithmetic cursor     | Medium   | Medium |
| 16  | State     | Multiple depth counters        | Low      | Medium |
| 17  | State     | No exception safety            | High     | Medium |
| 18  | AST       | `Word.to_sexp()` 480 lines     | High     | High   |
| 19  | AST       | Mixed data/presentation        | Medium   | High   |
| 20  | AST       | No visitor pattern             | Medium   | High   |
| 21  | AST       | Redundant `kind` field         | Low      | Low    |
| 22  | AST       | Inconsistent granularity       | Low      | High   |
| 23  | Naming    | Verbose method names           | Low      | Medium |
| 24  | Naming    | Inconsistent prefixes          | Low      | Low    |
| 25  | Naming    | Hungarian parameters           | Low      | Low    |
| 26  | Naming    | Abbreviation inconsistency     | Low      | Low    |
| 27  | Naming    | Boolean proliferation          | Medium   | Medium |
| 28  | Naming    | Unclear boundaries             | Low      | Medium |
| 29  | Naming    | No docstring conventions       | Low      | Medium |
| 30  | API       | Limited public API             | Medium   | Low    |
| 31  | API       | No parse options               | Medium   | Medium |
| 32  | API       | Offset-only errors             | Medium   | Low    |
| 33  | API       | No incremental parsing         | Low      | High   |
| 34  | API       | No location spans              | Medium   | Medium |
| 35  | API       | Coupled to string              | Low      | Medium |
| 36  | API       | No tree protocol               | Medium   | High   |
| 37  | API       | Mixed concerns                 | Low      | Low    |
| 38  | API       | No dialect handling            | Low      | Medium |

## Recommendations by Category

### AST Recommendations

Three approaches to address formatting concerns:

1. **Visitor pattern** (Crafting Interpreters style): Define `AstVisitor` interface, implement `SexpFormatter` visitor
2. **Match statements** (Python 3.10+): Use structural pattern matching in external functions
3. **Extract formatters**: Move `to_sexp()` to standalone module that imports AST types

Recommended: Option 3 (extract formatters) as lowest-risk first step.

### Naming Recommendations

1. Drop `parse_` prefix for internal methods - context makes it obvious
2. Replace boolean flags with enums: `ParseMode.ARRAY_SUBSCRIPT` vs `in_array_subscript=True`
3. Standardize abbreviations: always `pos` or always `position`
4. Add docstrings to all public methods with Args/Returns sections

### API Recommendations

1. Add `ParseOptions` dataclass for configuration
2. Include line/column in `ParseError`
3. Add `Node.span` property returning `(start, end)` positions
4. Split `parser.py` into `parser.py`, `errors.py`, `helpers.py`
5. Consider `ast.walk()` generator for tree traversal

## References

- Go parser: `~/source/go/src/cmd/compile/internal/syntax/parser.go`
- Crafting Interpreters: `~/source/craftinginterpreters/java/com/craftinginterpreters/lox/Parser.java`
- Pike regex: `~/source/pike-regex/beautiful.html`
