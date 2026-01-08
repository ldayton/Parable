# Parable

A recursive descent parser for bash shell scripts.

---

Parable parses bash source code into an abstract syntax tree (AST) for analysis, transformation, or interpretation.

## Installation

```bash
# Clone the repo
git clone https://github.com/ldayton/Parable.git
cd Parable

# Install with uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

## Usage

```python
from parable import parse

# Parse a simple command
nodes = parse("echo hello world")
print(nodes[0].to_sexp())
# (command (word "echo") (word "hello") (word "world"))

# Parse a pipeline
nodes = parse("cat file.txt | grep pattern | head -5")
print(nodes[0].to_sexp())
# (pipeline (command (word "cat") (word "file.txt")) (command (word "grep") (word "pattern")) (command (word "head") (word "-5")))

# Parse control structures
nodes = parse("if test -f foo; then echo exists; fi")
print(nodes[0].to_sexp())
# (if (command (word "test") (word "-f") (word "foo")) (command (word "echo") (word "exists")))
```

## Supported Syntax

- Simple commands with arguments
- Pipelines (`cmd1 | cmd2 | cmd3`)
- Lists with operators (`&&`, `||`, `;`, `&`)
- Redirections (`>`, `>>`, `<`, `<<`, `<<<`, `>&`, etc.)
- Subshells (`(commands)`)
- Brace groups (`{ commands; }`)
- If statements (`if`/`then`/`elif`/`else`/`fi`)
- While and until loops
- For loops (`for var in words; do ...; done`)
- Case statements (`case word in pattern) ...;; esac`)
- Quoting (single quotes, double quotes, escapes)
- Command substitution (`$(...)`)

## Project Structure

```
src/parable/
├── __init__.py           # Package exports
└── core/
    ├── __init__.py
    ├── ast.py            # AST node definitions
    ├── errors.py         # Error types
    └── parser.py         # Recursive descent parser

tests/
├── conftest.py           # Pytest configuration
├── 01_words.tests        # Word parsing tests
├── 02_commands.tests     # Command tests
├── 03_pipelines.tests    # Pipeline tests
├── 04_lists.tests        # List operator tests
├── 05_redirects.tests    # Redirection tests
├── 06_compound.tests     # Subshell/brace group tests
├── 07_if.tests           # If statement tests
├── 08_loops.tests        # Loop tests
└── 09_case.tests         # Case statement tests

bin/
└── parable-dump.py       # CLI tool to inspect parse output
```

## Development

```bash
# Run tests
uv run pytest

# Run linter
uv run ruff check .

# Format code
uv run ruff format .
```

## Test Format

Tests use a custom `.tests` format:

```
=== test name
input bash code
---
(expected s-expression)
```

## License

MIT
