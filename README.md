<div align="center">
<pre>
     ////        \\\\                         The wind blows where it wishes,
      ////              \\\\                          and you hear its sound,
  --------////  P A R A B L E  \\\\--------      but you do not know where it
        \\\\         ////                        comes from or where it goes.
     \\\\        ////                                              — John 3:8
</pre>
</div>

A recursive descent parser for bash in pure Python. 4,700 lines, no dependencies, no compromises.

---

## Philosophy

**LLM-driven development.** This project is an exercise in maximizing what LLMs can do. A 4,700-line recursive descent parser for one of the ugliest grammars in computing, built and maintained almost entirely through AI assistance—it wouldn't exist without them. When performance and clarity conflict, clarity wins. Verbose beats clever. The code should be readable by both humans and models.

**Match bash exactly.** Bash is the oracle. We patched GNU Bash 5.3 with `--dump-ast` to emit its internal parse tree, then test against it. No spec interpretation, no "close enough"—if bash parses it one way, so do we. Bash always tells the truth, even when it's lying.

**Pure Python.** One parser file, one AST file. Runs anywhere Python runs.

**Fast as possible.** Recursive descent is inherently slower than table-driven parsing. We pay that cost for clarity, then claw back every microsecond we can.

## What It Handles

The dark corners of bash that break other parsers:

- **Parameter expansion**: `${var:-default}`, `${var:+alt}`, `${var%pattern}`, `${!prefix*}`, `${var@Q}`
- **Nested substitutions**: `echo $(cat <(grep ${pattern:-".*"} "$file"))`
- **Here documents**: `<<EOF`, `<<-EOF`, `<<<word`, quoted/unquoted delimiters
- **Process substitution**: `<(cmd)`, `>(cmd)` as arguments or redirects
- **Arithmetic**: `$(( ))`, `$[ ]` (deprecated), C-style `for ((i=0; i<10; i++))`
- **Conditionals**: `[[ ]]` with `=~`, `-eq`, pattern matching, `&&`, `||`
- **Arrays**: `arr=(a b c)`, `${arr[@]}`, `${!arr[@]}`, `${#arr[@]}`
- **Quoting edge cases**: `$'ansi\nescapes'`, `$"locale"`, adjacent quotes, backslash semantics
- **Obscure redirects**: `{fd}>file`, `3<&0-`, `&>`, `|&`, `>|`
- **Coprocesses**: `coproc name { commands; }`
- **Case fallthrough**: `;&` and `;;&`
- **Everything else**: functions, subshells, brace groups, pipelines, lists—the full grammar

## Test Coverage

- **GNU Bash test corpus:** 19,370 lines
- **Oils bash corpus:** 2,495 tests
- **tree-sitter-bash corpus:** 125 tests
- **Parable hand-written tests:** 1,542 tests
- **Every test validated against real bash 5.3 ASTs**

## Usage

```python
from parable import parse

# Returns an AST, not string manipulation
ast = parse("ps aux | grep python | awk '{print $2}'")

# S-expression output for inspection
print(ast[0].to_sexp())
# (pipeline
#   (command (word "ps") (word "aux"))
#   (command (word "grep") (word "python"))
#   (command (word "awk") (word "'{print $2}'")))

# Handles the weird stuff
ast = parse("cat <<'EOF'\nheredoc content\nEOF")
print(ast[0].to_sexp())
# (command (word "cat") (heredoc-quoted "EOF" "heredoc content\n"))
```

## Installation

```bash
git clone https://github.com/ldayton/Parable.git
cd Parable && uv pip install -e .
```

## Tests

```bash
just test        # Run tests (Python 3.14)
just test-py312  # Run tests on specific version
just test-all    # Run tests on all versions (3.10-3.14)
```

32 test modules covering progressively deeper bash semantics plus corpus testing of edge cases.

## Benchmarks

```bash
just bench  # Run all benchmarks
```

## Formatting

```bash
just fmt   # Check formatting with ruff
just lint  # Check linting with ruff
```

## Project Structure

```
src/parable/
├── __init__.py        # parse() entry point
└── core/
    ├── ast.py         # AST node definitions
    └── parser.py      # Recursive descent parser (~4500 lines)

tests/
├── *.tests                      # 1,517 test cases in custom format
└── corpus/
    ├── gnu-bash/                # GNU Bash test corpus tests
    ├── tree-sitter-bash/        # tree-sitter bash corpus tests
    └── oils/                    # Oils spec tests
```

## License

MIT
