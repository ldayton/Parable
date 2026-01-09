# Parable Roadmap

Features to make Parable more useful for downstream projects.

## Summary

```
Feature                Priority   Effort   Impact         Status
────────────────────────────────────────────────────────────────────
[[ ]] parsing          P1         Medium   Very High      ✓ Done
$(( )) parsing         P1         High     Very High      ✓ Done
Extglob in case        P1         Low      Medium         ✓ Done
Extglob in words       P1         Low      Medium         Bug
Parens in comments     P1         Low      Medium         ✓ Done
Empty for list         P1         Low      Low            Bug
Empty heredoc delim    P1         Low      Low            Bug
Position tracking      P2         Medium   Very High      Not started
JSON serialization     P2         Low      High           Not started
Visitor pattern        P2         Low      High           Not started
Error recovery         P3         High     Medium-High    Not started
Comments preservation  P3         Medium   Medium         Not started
Source reconstruction  P3         Medium   Medium         Not started
```

- **P1 Correctness:** Required. Without these, tools miss hidden command substitutions.
- **P2 Usability:** Practical necessities for tool authors.
- **P3 Nice to have:** Narrower use cases.

---

## P1: Correctness

These features are required for tools that need complete visibility into bash scripts.

### Parse `[[ ]]` conditional internals

**Status:** ✓ Implemented

`[[ -f "$file" && $(cmd) ]]` now produces:
```
(cond-expr (cond-and (unary-test "-f" (word "\"$file\"" (param "file"))) (unary-test "-n" (word "$(cmd)" (cmdsub (command (word "cmd")))))))
```

Command substitutions, parameter expansions, and arithmetic expansions inside `[[ ]]` are now visible to AST walkers.

**Implemented operators:**
- Unary: `-a`, `-b`, `-c`, `-d`, `-e`, `-f`, `-g`, `-h`, `-k`, `-p`, `-r`, `-s`, `-t`, `-u`, `-w`, `-x`, `-G`, `-L`, `-N`, `-O`, `-S`, `-z`, `-n`, `-o`, `-v`, `-R`
- Binary: `==`, `!=`, `=~`, `=`, `<`, `>`, `-eq`, `-ne`, `-lt`, `-le`, `-gt`, `-ge`, `-nt`, `-ot`, `-ef`
- Logical: `&&`, `||`, `!`
- Grouping: `( )`
- Extended globs: `@(...)`, `?(...)`, `*(...)`, `+(...)`, `!(...)`
- Regex patterns with grouping parentheses

### Parse `$(( ))` arithmetic internals

**Status:** ✓ Implemented

`echo $(( $(get_val) + x++ ))` now produces:
```
(command (word "echo") (word "$(($(get_val) + x++))" (arith (binary-op "+" (cmdsub (command (word "get_val"))) (post-incr (var "x"))))))
```

Command substitutions, parameter expansions, and side effects inside `$(( ))` are now visible to AST walkers.

**Implemented operators:**
- Arithmetic: `+`, `-`, `*`, `/`, `%`, `**`
- Bitwise: `&`, `|`, `^`, `~`, `<<`, `>>`
- Comparison: `<`, `>`, `<=`, `>=`, `==`, `!=`
- Logical: `&&`, `||`, `!`
- Assignment: `=`, `+=`, `-=`, `*=`, `/=`, `%=`, `<<=`, `>>=`, `&=`, `|=`, `^=`
- Increment/Decrement: `++x`, `x++`, `--x`, `x--`
- Ternary: `? :`
- Comma: `,`
- Grouping: `( )`
- Array subscript: `arr[expr]`
- Nested expansions: `$(cmd)`, `${var}`, `$((...))`
- Numbers: decimal, hex (`0xFF`), octal (`0777`), base-N (`2#1010`)
- Line continuation: `\<newline>`

### Extglob patterns in case statements

**Status:** ✓ Implemented

`case $x in @(a|b)) echo match;; esac` now parses correctly.

The case pattern parser recognizes extended glob syntax (`@(...)`, `?(...)`, `*(...)`, `+(...)`, `!(...)`), including:
- Nested extglobs: `@(@(a|b))`
- Grouping parens inside extglob: `@((a|b))`
- Command substitution inside: `@($(cmd))`
- Arithmetic inside: `@($((1+2)))`
- Character classes: `@([a-z]*)`

### Extglob patterns in words

**Status:** Bug

`echo @(a|b)` fails with "Parser not fully implemented yet".

Extglob patterns work in case statements but not in regular words/arguments. With `shopt -s extglob`, patterns like `@()`, `?()`, `*()`, `+()` are valid anywhere globs are valid.

### Parentheses in comments

**Status:** ✓ Implemented

`# has (parens)` now parses correctly as a Comment node.

Comments (`#` to end of line) are now parsed as Comment AST nodes instead of being skipped or causing parse errors.

### Empty for list

**Status:** Bug

`for x in; do :; done` fails with "Expected words after 'in'".

Bash allows empty word lists in for loops - the loop simply doesn't execute.

### Empty heredoc delimiter

**Status:** Bug

`cat <<''` fails with "Expected delimiter for here document".

Empty string is a valid heredoc delimiter - the heredoc ends at the first empty line.

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

