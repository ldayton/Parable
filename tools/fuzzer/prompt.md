# Fuzzer Bug Hunt

Run the fuzzer to find and fix a parser bug.

## Steps

1. **Run the fuzzer** until you have 10 unique discrepancies where both parsers succeed but produce different ASTs:
   ```bash
   cd /home/lilydayton/source/Parable
   python tools/fuzzer/fuzz.py -n 10000 --both-succeed -v
   ```
   Increase `-n` if needed. Stop when you have 10.

2. **Pick one at random.** Not the first one. Use `random.randint(0, 9)` or similar.

3. **Create an MRE.** Manually shrink the input to the smallest string that still shows the discrepancy. Verify:
   ```bash
   ~/source/bash-oracle/bash-oracle -e 'INPUT'
   python -c "from src.parable import parse; print(parse('INPUT')[0].to_sexp())"
   ```

4. **Add a failing test.** Find the appropriate `.tests` file in `tests/` and add:
   ```
   === descriptive name
   INPUT
   ---
   (expected s-expr from bash-oracle)
   ---
   ```

5. **Verify the test fails:**
   ```bash
   just test
   ```

6. **Fix the bug** in `src/parable.py`. The fix should make Parable match bash-oracle.

7. **Run the full check:**
   ```bash
   just check
   ```

8. **Commit and push:**
   ```bash
   git add -A && git commit -m "Fix: descriptive message" && git push
   ```

## Notes

- The fuzzer requires `~/source/bash-oracle/bash-oracle` to exist
- Discrepancies where one parser errors are less interesting than where both succeed differently
- If the MRE is a bash-oracle bug (not Parable), pick a different discrepancy
- Keep commits atomic: one bug fix per commit
