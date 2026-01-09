<div align="center">
<pre>
     ////        \\\\                         The wind blows where it wishes,
      ////              \\\\                          and you hear its sound,
  --------////  <strong>P A R A B L E</strong>  \\\\--------      but you do not know where it
        \\\\         ////                         comes from or where it goes.
     \\\\        ////                                              — John 3:8
</pre>
</div>

A hand-written recursive descent parser for bash. No shortcuts, no regexes, no external dependencies—just pure Python that understands bash the way bash understands bash.

---

## Philosophy

Most bash parsers are glorified regex matchers that handle the happy path. Parable is different. Built from the GNU bash manual, the POSIX spec, the bash YACC grammar, and tested against brutal edge cases from open source test suites.

- **5,680 test cases**
- **100% pass rate on the GNU Bash test corpus**
- **100% pass rate on the Oils bash corpus**
- **100% pass rate on the tree-sitter bash corpus**
- **Every test validated against `bash -n`**

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
- **Everything else**: functions, subshells, brace groups, pipelines, lists, all the control structures

## Installation

```bash
git clone https://github.com/ldayton/Parable.git
cd Parable && uv pip install -e .
```

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
