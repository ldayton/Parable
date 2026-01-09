# Parable Roadmap

Features to make Parable more useful for downstream projects.

## Test Suite Status

Parable is tested against bash-oracle (GNU Bash 5.3 patched with `--dump-ast`).

**Current:** 545 passed, 3663 failed (13% pass rate)

Test corpora:
- **Oils bash corpus:** 2,495 tests
- **tree-sitter-bash corpus:** 93 tests
- **GNU Bash test corpus:** 78 tests
- **Parable hand-written tests:** 1,542 tests

Total: 4,208 tests (4,201 verified against oracle, 7 skipped due to binary content)

---

## P1: Oracle Alignment

Parable's s-expression output must match bash-oracle exactly. Failure classification:

| Count | % | Issue | Fix |
|------:|----:|-------|-----|
| 2403 | 65.6% | `(param ...)` inside words | Remove nested expansion nodes from word output |
| 410 | 11.2% | Other | Mixed issues |
| 238 | 6.5% | Arithmetic differences | Match `(arith ...)` format |
| 143 | 3.9% | Redirect target wrapped in `(word ...)` | Output filename as plain string |
| 132 | 3.6% | `(cmdsub ...)` inside words | Remove nested expansion nodes from word output |
| 97 | 2.6% | Heredoc handling | Match heredoc content format |
| 91 | 2.5% | `[[ ... ]]` conditional expressions | Match `(cond ...)` format |
| 46 | 1.3% | FD prefix in redirect op (`"2>"` vs `">"`) | Separate fd number from operator |
| 23 | 0.6% | Function definitions | Match `(function ...)` format |
| 23 | 0.6% | Process substitution in words | Remove nested expansion nodes |
| <50 | <2% | Compound, loops, case, background, empty, if | Various |

**High-impact fixes (76% of failures):**
1. Remove `(param ...)` / `(cmdsub ...)` / `(procsub ...)` from inside `(word ...)` — just output the text
2. Output redirect targets as plain strings, not `(word ...)`
3. Separate fd number from redirect operator

---

## Summary

```
Feature                Priority   Effort   Impact         Status
────────────────────────────────────────────────────────────────────
Position tracking      P2         Medium   Very High      Not started
JSON serialization     P2         Low      High           Not started
Visitor pattern        P2         Low      High           Not started
Error recovery         P3         High     Medium-High    Not started
Comments preservation  P3         Medium   Medium         Not started
Source reconstruction  P3         Medium   Medium         Not started
```

- **P2 Usability:** Practical necessities for tool authors.
- **P3 Nice to have:** Narrower use cases.

---

## P2: Usability

Features that make Parable practical for tool authors.

### Position tracking (optional)

**Status:** Not implemented

AST nodes have no source location information. Required for:
- Syntax highlighters
- Linters with precise error locations
- IDEs
- Source maps

**Approach:** Store only byte offsets (16 bytes/node). Compute line/column lazily on demand from a line index. Make it opt-in to avoid overhead when not needed.

```python
ast = parse(code, track_positions=True)
node.start_offset  # always available
node.start_line    # computed on first access
node.start_col     # computed on first access
```

**Effort:** Medium

### JSON serialization

**Status:** Not implemented

```python
ast.to_dict()  # For JSON serialization
ast.to_json()  # Direct JSON output
```

**Effort:** Low

### Visitor pattern

**Status:** Not implemented

```python
class MyVisitor(Visitor):
    def visit_CommandSubstitution(self, node):
        print(f"Found command sub: {node}")

visitor = MyVisitor()
visitor.walk(ast)
```

**Effort:** Low

## P3: Nice to Have

Features with narrower use cases.

### Error recovery

**Status:** Not implemented

Parse incomplete/invalid input and return best-effort AST. Required for IDE use cases where code is often in an invalid state.

**Effort:** High (architectural change)

**Downside:** Partial ASTs can confuse downstream tools. Recovery heuristics are brittle.

### Comments preservation

**Status:** Not implemented

Attach comments to AST nodes. Required for formatters and doc generators.

**Effort:** Medium

**Downside:** Lexer rewrite. Ambiguous attachment (does comment belong to preceding or following node?).

### Source reconstruction

**Status:** Not implemented

Reconstruct source from AST: `ast.to_source()`. Required for formatters and refactoring tools.

**Effort:** Medium

**Downside:** Either preserve original whitespace (memory cost) or accept lossy reconstruction. Edge cases with heredocs and quotes.
