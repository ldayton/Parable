# Parable

A hand-written recursive descent parser for bash. No shortcuts, no regexes, no external dependencies—just pure Python that understands bash the way bash understands bash.

---

## Philosophy

Most bash parsers are glorified regex matchers that handle the happy path. Parable is different. Built from the GNU bash manual, the POSIX spec, the bash YACC grammar, and tested against the [tree-sitter-bash](https://github.com/tree-sitter/tree-sitter-bash) and [Oils](https://github.com/oilshell/oil) test suites. Every test case validated against real bash.

**3,962 test cases.** Every one passes `bash -n` syntax validation.

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
uv run pytest
```

28 test modules covering progressively deeper bash semantics. Every input is validated against bash 4.0+ with `bash -n`. The tree-sitter-bash and Oils corpora run as separate test suites—Parable parses what they parse, but doesn't accept syntax that bash rejects.

## Project Structure

```
src/parable/
├── __init__.py        # parse() entry point
└── core/
    ├── ast.py         # AST node definitions
    └── parser.py      # Recursive descent parser (~3000 lines)

tests/
├── *.tests                      # 1,374 test cases in custom format
└── corpus/
    ├── tree-sitter-bash/        # 93 tree-sitter-bash corpus tests
    └── oils/                    # 2,495 Oils spec tests
```

## License

MIT
