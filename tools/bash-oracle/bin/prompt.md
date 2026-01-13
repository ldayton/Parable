# Corpus Bug Fix Workflow

One bug per iteration. Do not batch.

1. **Run corpus** → `uv run python tools/bash-oracle/bin/run-corpus.py`
2. **Pick first failure** → check `failures.txt`, test with Parable to see error type (parse error vs mismatch)
3. **Create MRE** → minimal bash that reproduces the issue
4. **Get oracle output** → `~/source/bash-oracle/bash-oracle -e 'MRE'` (syntax errors output nothing, just error message to stderr)
5. **Add failing test** → append to appropriate `tests/parable/*.tests`
6. **Confirm it fails** → `just test` — DO NOT proceed to step 7 until test fails
7. **Fix the bug** → edit `src/parable.py`
8. **Confirm it passes** → `just test`
9. **Full check** → `just check` (includes transpile, all Python versions, JS)
10. **Commit & push** → single bug per commit
11. **Loop** → reread this prompt, then back to step 1

## Test file format

```
=== test name
input code here
---
expected sexp output (or <error> for syntax errors)
---
```
