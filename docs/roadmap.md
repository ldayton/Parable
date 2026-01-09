# Parable Roadmap

Features to make Parable more useful for downstream projects.

## Oils Test Suite Status

Parable is tested against the [Oils](https://www.oilshell.org/) project's bash test corpus. Current status: **2282 passed, 213 failed**.

### Parser Bugs (213 failures)

| Error Type | Count | Description |
|------------|------:|-------------|
| Unterminated single quote | 80 | Quotes inside comments (`# don't`) incorrectly start strings |
| Parser not fully implemented | 60 | Various unimplemented constructs |
| Unexpected char in arithmetic | 8 | Quotes/backticks in `$((...))` - valid bash |
| Expected )) to close arithmetic | 7 | Arithmetic expression edge cases |
| Unterminated double quote | 5 | Double quotes inside comments |
| Expected } to close brace group | 5 | Complex brace group constructs |
| Expected 'fi' to close if | 2 | If statement edge cases |
| Expected ]] to close conditional | 2 | Conditional expression edge cases |
| Expected command after &&/\|\| | 2 | Newline after && or \|\| before command |
| Expected ':' in ternary | 1 | Assignment expressions in ternary branches |
| Expected operand after == | 1 | Comparison edge case |

### Priority Fixes

1. **Quotes in comments (85 tests)**: The lexer treats `'` and `"` inside comments as starting strings. This is the single biggest issue.

2. **Command substitution in arithmetic (1 test)**: `` $((`echo 1`)) `` is valid bash - backticks should be allowed inside arithmetic.

3. **Newline after && and || (2 tests)**: Commands can appear on the next line after `&&` or `||`.

4. **Redirects after compound commands (multiple tests)**: `[[ ]] > file`, `(( )) > file`, `case ... esac > file` are valid.

5. **Ternary with assignment (1 test)**: `$((1 ? a=1 : 42))` - assignment expressions should work in ternary branches.

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
