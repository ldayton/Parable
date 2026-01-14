# Fuzzer Bug Hunt

Run the fuzzer to find and fix a parser bug.

All commands run from `~/source/Parable`.

## Steps

1. **Run the fuzzer** until you have 10 unique discrepancies where both parsers succeed but produce different ASTs:
   ```bash
   uv run python ~/source/Parable/tools/fuzzer/fuzz.py -n 10000 --both-succeed -v
   ```
   Increase `-n` if needed. Stop when you have 10.

2. **Pick one at random.** Not the first one. Roll a die or use Python:
   ```bash
   uv run python -c "import random; print(random.randint(0, 9))"
   ```

3. **Create an MRE.** Shrink the input to the smallest string that still shows the discrepancy. Verify with (from repo root):
   ```bash
   ~/source/bash-oracle/bash-oracle -e 'INPUT'
   uv run python -c "import sys; sys.path.insert(0, 'src'); from parable import parse; print(' '.join(n.to_sexp() for n in parse('INPUT')))"
   ```
   Keep removing characters until you can't anymore.

4. **Add a failing test.** Find the appropriate `.tests` file in `tests/` and add:
   ```
   === descriptive name
   INPUT
   ---
   (expected s-expr from bash-oracle)
   ---
   ```

5. **Run formatters and verify the test fails:**
   ```bash
   just fmt --fix
   just lint --fix
   just test
   ```
   Confirm your new test fails.

6. **Fix the bug** in `src/parable.py`. The fix should make Parable match bash-oracle.

7. **Run the full check:**
   ```bash
   just fmt --fix
   just lint --fix
   just check
   ```

8. **Commit and push:**
   ```bash
   git add -A
   git commit -m "Fix: descriptive message"
   git push
   ```

## Notes

- The fuzzer requires `~/source/bash-oracle/bash-oracle`
- Discrepancies where one parser errors are less interesting than where both succeed differently
- If the MRE turns out to be a bash-oracle bug (not Parable), pick a different discrepancy
- One bug fix per commit
