# Corpus Bug Fix Workflow

One bug per iteration. Do not batch.

1. **Run corpus** → `./tools/bash-oracle/bin/run-corpus.py`
2. **Pick first failure** → check `failures.txt`, test with Parable to see error type (parse error vs mismatch)
3. **Create MRE** → minimal bash that reproduces the issue
4. **Get oracle output** → `echo 'MRE' | ~/source/bash/bash-oracle --dump-ast`
5. **Add failing test** → append to appropriate `tests/parable/*.tests`
6. **Confirm it fails** → `just test -f "test name"`
7. **Fix the bug** → edit `src/parable.py`
8. **Confirm it passes** → `just test -f "test name"`
9. **Full check** → `just check` (includes transpile, all Python versions, JS)
10. **Commit & push** → single bug per commit
11. **Loop** → back to step 1
