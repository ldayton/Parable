# Corpus Bug Fix Workflow

One bug per iteration. Do not batch. Failures are already in `tools/bash-oracle/bin/failures.txt`.

1. **Pick failure** → take the NEXT bug from `failures.txt`. Test with Parable to see error type (parse error vs mismatch)
2. **Create MRE** → minimal bash that reproduces the issue
3. **Get oracle output** → `~/source/bash-oracle/bash-oracle -e 'MRE'` (syntax errors output nothing, just error message to stderr)
4. **Add failing test** → append to appropriate `tests/parable/*.tests`
5. **Confirm it fails** → `just test` — DO NOT proceed to step 6 until test fails
6. **Fix the bug** → edit `src/parable.py`
7. **Confirm it passes** → `just test`
8. **Full check** → `just check` (includes transpile, all Python versions, JS)
9. **Commit & push** → single bug per commit, commit and push together in one command
10. **Remove from failures.txt** → delete the line you just fixed
11. **Loop** → reread this prompt, then back to step 1

## Test file format

```
=== test name
input code here
---
expected sexp output (or <error> for syntax errors)
---
```
