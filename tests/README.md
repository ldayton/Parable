# Tests

Every test validated against real bash 5.3 ASTs.

## Usage

```bash
just test       # Python (3.14)
just test-js    # JavaScript
just test-go    # Go
just test-all   # All Python versions (3.8-3.14, PyPy)
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

- `bin/` — Test runners and corpus utilities
- `parable/` — Parable hand-written tests
- `corpus/gnu-bash/` — GNU Bash 5.3 test suite
- `corpus/oils/` — Oils project bash corpus
- `corpus/tree-sitter-bash/` — tree-sitter-bash test cases

## Corpus Utilities

Scripts in `bin/` for working with test corpora. Require [bash-oracle](https://github.com/ldayton/bash-oracle).

```bash
# Verify test expectations match bash-oracle
./tests/bin/verify-tests.py

# Run Parable against bigtable-bash corpus
./tests/bin/run-corpus.py

# Convert external corpora to .tests format
./tests/bin/convert-gnu-bash.py
./tests/bin/convert-oils.py
./tests/bin/convert-tree-sitter.py
```
