# Parable Roadmap

Features to make Parable more useful for downstream projects.

## Oils Test Suite Status

Parable is tested against the [Oils](https://www.oilshell.org/) project's bash test corpus. Current status: **2473 passed, 22 failed**.

### Parser Bugs (22 failures)

| Category | Count | Description |
|----------|------:|-------------|
| Parenthesis ambiguity | 6 | `((` disambiguation between arithmetic and subshell |
| KSH command substitution | 2 | `${ cmd; }` ksh-style command sub not implemented |
| zsh idioms | 2 | zsh-specific idioms |
| Variable expansion edge cases | 4 | `${var}` with braces/operators edge cases |
| Array index parsing | 1 | `a[1+2]=3` LHS array index expressions |
| Ternary with assignment | 1 | `$((1 ? a=1 : 42))` assignment in ternary |
| Heredoc delimiter | 1 | Bad command substitution as heredoc delimiter |
| Conditional special chars | 2 | Escaped quotes and special chars in `[[ ]]` |
| Miscellaneous | 3 | trap DEBUG, builtin cat subshell crash |

### Recently Fixed

- ✅ **Quotes in comments (173 tests)**: Comments now properly ignored during lexing.
- ✅ **Newline after && and || (2 tests)**: Commands can appear on next line.
- ✅ **Quotes/backticks in arithmetic (10 tests)**: `$(('1'))` and `` $((`cmd`)) `` now parse.
- ✅ **Redirects after compound commands (5 tests)**: `[[ ]] > file`, `(( )) > file`, `case ... esac > file` work.
- ✅ **Backticks in conditionals (1 test)**: `` [[ `cmd` = x ]] `` now parses.

### Remaining Priority Fixes

1. **Parenthesis ambiguity (6 tests)**: `((`...`) )` - arithmetic closing with space before last `)`.

2. **Ternary with assignment (1 test)**: `$((1 ? a=1 : 42))` - assignment expressions in ternary branches.

3. **KSH command substitution (2 tests)**: `${ echo hi; }` - ksh-style command sub (different from `$()`).

4. **Variable expansion edge cases (4 tests)**: Complex `${var}` expansions with nested braces.

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
