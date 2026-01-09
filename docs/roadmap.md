# Parable Roadmap

Features to make Parable more useful for downstream projects.

## Summary

```
Feature                Priority   Effort   Impact
──────────────────────────────────────────────────────────
[[ ]] parsing          P1         Medium   Very High
$(( )) parsing         P1         High     Very High
Position tracking      P2         Medium   Very High
JSON serialization     P2         Low      High
Visitor pattern        P2         Low      High
Error recovery         P3         High     Medium-High
Comments preservation  P3         Medium   Medium
Source reconstruction  P3         Medium   Medium
```

- **P1 Correctness:** Required. Without these, tools miss hidden command substitutions.
- **P2 Usability:** Practical necessities for tool authors.
- **P3 Nice to have:** Narrower use cases.

---

## P1: Correctness

These features are required for tools that need complete visibility into bash scripts.

### Parse `[[ ]]` conditional internals

**Status:** Not implemented

Currently `[[ -f "$file" && $(cmd) ]]` produces:
```
(cond-expr "-f \"$file\" && $(cmd)")
```

The `$(cmd)` is invisible to AST walkers. This breaks security scanners, linters, and any tool that needs to find all command substitutions.

**Required output:**
```
(cond-expr
  (and
    (unary-test "-f" (word "$file" (param-exp "file")))
    (word "$(cmd)" (cmd-sub (command (word "cmd"))))))
```

**Effort:** Medium (~200 lines)

**Operators to handle:**
- Unary: `-e`, `-f`, `-d`, `-r`, `-w`, `-x`, `-s`, `-z`, `-n`, etc.
- Binary: `==`, `!=`, `=~`, `-eq`, `-ne`, `-lt`, `-gt`, `-le`, `-ge`, `-nt`, `-ot`, `-ef`
- Logical: `&&`, `||`, `!`
- Grouping: `( )`

### Parse `$(( ))` arithmetic internals

**Status:** Not implemented

Currently `echo $(( $(get_val) + x++ ))` produces:
```
(command (word "echo") (word "$(( $(get_val) + x++ ))" (arith " $(get_val) + x++ ")))
```

The nested `$(get_val)` is buried in a raw string. Side effects (`x++`) are also invisible.

**Required output:**
```
(arith
  (binary-op "+"
    (cmd-sub (command (word "get_val")))
    (post-incr (var "x"))))
```

**Effort:** High (~500 lines)

**Operators to handle:**
- Arithmetic: `+`, `-`, `*`, `/`, `%`, `**`
- Bitwise: `&`, `|`, `^`, `~`, `<<`, `>>`
- Comparison: `<`, `>`, `<=`, `>=`, `==`, `!=`
- Logical: `&&`, `||`, `!`
- Assignment: `=`, `+=`, `-=`, `*=`, `/=`, `%=`, `<<=`, `>>=`, `&=`, `|=`, `^=`
- Increment: `++x`, `x++`, `--x`, `x--`
- Ternary: `? :`
- Comma: `,`
- Grouping: `( )`
- Array subscript: `arr[expr]`
- Nested expansions: `$(cmd)`, `${var}`

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

