# Parable Roadmap

Features to make Parable more useful for downstream projects.

## Test Suite Status

Parable is tested against bash-oracle (GNU Bash 5.3 patched with `--dump-ast`).

**Current:** 3,607 passed, 601 failed (86% pass rate)

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
| 313 | 52.1% | Corpus tests (mixed issues) | Various oracle format differences |
| 41 | 6.8% | ANSI-C quoting `$'...'` | Strip `$` prefix from output |
| 35 | 5.8% | Variable fd `{fd}>` | Handle fd capture syntax |
| 31 | 5.2% | Locale strings `$"..."` | Strip `$` prefix from output |
| 26 | 4.3% | Pipe stderr `\|&` | Transform to `(redirect ">&" 1)` |
| 22 | 3.7% | Extglob patterns | Handle `+(...)`, `*(...)`, etc. in case |
| 19 | 3.2% | Command substitution internals | Newline/formatting inside `$(...)` |
| 17 | 2.8% | Named coproc/select/C-for edge cases | Various compound statement fixes |
| 7 | 1.2% | Obscure edge cases | Unusual syntax combinations |
| 4 | 0.7% | Time/negation nesting | Correct `!` and `time` interaction |
| 86 | 14.3% | Other scattered issues | Misc failures across test files |

**Completed fixes:**
- ✅ Words output plain text (no nested `(param ...)`, `(cmdsub ...)`, `(procsub ...)`)
- ✅ Redirect targets output as plain strings
- ✅ FD number separated from redirect operator
- ✅ Top-level statements output as separate s-expressions (not wrapped in `(semi ...)`)
- ✅ Arithmetic commands use raw content format `(arith (word "..."))`
- ✅ Conditional expressions use `(cond ...)` with `cond-unary`, `cond-binary`, `cond-term`
- ✅ Parenthesized conditionals wrapped in `(cond-expr ...)`
- ✅ Conditional negation `!` dropped from output (oracle ignores it)
- ✅ For loops use `(for (word "var") (in ...) body)` format
- ✅ Select uses same format as for loop
- ✅ Case patterns use `(pattern ((word "a")) body)` format with escaped pipes
- ✅ C-style for uses `(arith-for (init ...) (test ...) (step ...) body)`
- ✅ Case fallthrough markers removed from output
- ✅ Coproc always outputs `"COPROC"` as name
- ✅ Heredocs output as `(redirect "<<" "content")` with literal newlines
- ✅ Heredoc backslash-newline continuation handled

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
