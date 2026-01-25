# Tests

Every test validated against real bash 5.3 ASTs.

## Usage

```bash
just test       # Python (3.14)
just test-js    # JavaScript
just test-go    # Go
just test-all   # All Python versions (3.10-3.14, PyPy)
```

### Options

```bash
just test -v                  # Verbose output
just test -f heredoc          # Filter by name
just test tests/parable/pipes.tests   # Run specific file
```

## Test Format

Tests use a simple format:

```
=== test name
input goes here
---
(expected sexp output)
---
```

## Directories

- `parable/` — Parable hand-written tests
- `corpus/gnu-bash/` — GNU Bash 5.3 test suite
- `corpus/oils/` — Oils project bash corpus
- `corpus/tree-sitter-bash/` — tree-sitter-bash test cases
