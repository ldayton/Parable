# Parable Development

## Current Goal: Oracle Alignment

Parable's s-expression output must match bash-oracle (GNU Bash 5.3 with `--dump-ast`).

**Status:** 1,583 passed, 2,625 failed (38%). See `docs/roadmap.md` for failure classification.

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

## Completed Fixes

- ✅ **Words**: Now output plain text (no nested expansion nodes)
- ✅ **Redirects**: Target as plain string, fd separated from operator

## Top Fixes Needed

1. **Semi wrapper** (73%): Multi-statement input outputs `(semi ...)` but should be separate lines
2. **Case statements** (6%): Match case pattern/body format
3. **Functions** (6%): Match `(function ...)` format
4. **For loops** (1%): Various formatting differences
5. **Conditionals** (1%): Match `(cond ...)` format for `[[ ]]`
