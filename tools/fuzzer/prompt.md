# Fuzzer Bug Hunt

Run the fuzzer to find and fix a parser bug.

All commands run from `~/source/Parable`.

## Steps

1. **Run the fuzzer** to find 10 unique discrepancies where both parsers succeed but produce different ASTs:
   ```bash
   uv run python ~/source/Parable/tools/fuzzer/fuzz.py --both-succeed --stop-after 10 -v
   ```

2. **Pick one at random.** Not the first one. Roll a die or use Python:
   ```bash
   uv run python -c "import random; print(random.randint(0, 9))"
   ```

3. **Create an MRE.** Shrink the input to the smallest string that still shows the discrepancy. Compare outputs:
   ```bash
   ~/source/bash-oracle/bash-oracle -e 'INPUT'   # oracle
   uv run bin/parable-dump.py 'INPUT'            # parable
   ```
   Keep removing characters until you can't anymore.

4. **Add a failing test** to `tests/parable/36_fuzzer.tests`:
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
