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

**Approach:** Store byte offsets (16 bytes/node). Compute line/column lazily. Opt-in via `parse(code, track_positions=True)`.

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

**Effort:** Medium | **Downside:** Lexer rewrite. Ambiguous attachment.

### Source reconstruction

Reconstruct source from AST: `ast.to_source()`. Required for formatters and refactoring tools.

**Effort:** Medium | **Downside:** Either preserve whitespace (memory) or accept lossy reconstruction.

---

## Quality Analysis

Comparison against Go compiler parser, Crafting Interpreters, and Rob Pike's regex. See [quality.md](quality.md) for full analysis.

### What's Good

- Clear grammar-to-method mapping
- Arithmetic parser follows Crafting Interpreters' precedence pattern
- No separate lexer (appropriate for bash's context-sensitive grammar)

### Issues

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

---

## Optimization Opportunities

See [optimizations.md](optimizations.md) for implementation details and CPython internals.

| Optimization            | Speedup | Memory | LLM Impact |
| ----------------------- | ------- | ------ | ---------- |
| Inline hot paths        | 5-10%   | —      | Moderate   |
| Cached character sets   | 3-5%    | —      | Low        |
| ASCII range checks      | 5-8%    | —      | Moderate   |
| `__slots__` on nodes    | —       | 40-50% | Low        |
| Unchecked advance       | 2-3%    | —      | High       |
| Dispatch tables         | 3-5%    | —      | High       |
| Table-driven precedence | 2-3%    | —      | Very High  |
| Bulk consumption        | 1-2%    | —      | Low        |

---

## Decisions

### Performance

Apply optimizations with low LLM impact:

| Do | Optimization | Rationale |
|----|--------------|-----------|
| ✓ | Inline hot paths | 5-10% gain, moderate LLM impact |
| ✓ | Cached character sets | Clean pattern, low LLM impact |
| ✓ | ASCII range checks | Correct for bash (ASCII-only identifiers) |
| ✓ | `__slots__` on AST nodes | 40-50% memory, well-known pattern |
| ✓ | Bulk consumption | Clearer intent than char-by-char |
| ✗ | Unchecked advance | Two similar methods confuse LLMs |
| ✗ | Dispatch tables | Fragments logic, hard to trace |
| ✗ | Table-driven precedence | Explicit methods are clearer |

### AST Formatting

For issue #18 (`Word.to_sexp()` 480 lines):

| Option | Approach | Verdict |
|--------|----------|---------|
| 1 | Visitor pattern | More infrastructure |
| 2 | Match statements | Python 3.10+ only |
| 3 | Extract to formatter module | **Use this** — lowest risk |

---

## Refactoring Plan

Phases ordered by dependency and risk:

| Phase | Task | Issues Addressed |
|-------|------|------------------|
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
