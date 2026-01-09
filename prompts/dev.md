# Parable Development

## Current Goal: Oracle Alignment

Parable's s-expression output must match bash-oracle (GNU Bash 5.3 with `--dump-ast`).

See `docs/roadmap.md` for current status and failure classification.

## Workflow

1. **Run tests** to see current failures
2. **Pick a failure category** from roadmap (start with highest-impact)
3. **Examine failures** - compare Parable output vs expected (oracle output)
4. **Fix `to_sexp()` methods** in `src/parable/core/ast.py`
5. **Run tests** to verify fix and check for regressions
6. **Commit** when a category is fixed or substantially improved

## Commands

```bash
just test                               # run tests (Python 3.14)
just test -k "redirect"                 # by name pattern
just test tests/05_redirects.tests      # single file
just test-all                           # all Python versions (required before committing)
```

## Key Files

- `src/parable/core/ast.py` - AST nodes with `to_sexp()` methods (main edit target)
- `tests/*.tests` - test files (input + expected oracle output)
- `tests/testformat.py` - test file parser
- `tools/bash-oracle/` - oracle binary and verification tools
- `docs/roadmap.md` - failure classification and priorities
