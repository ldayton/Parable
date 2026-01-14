Find and fix one parser bug using the fuzzer.

## Steps

1. **Pick a unique number for this run (avoid conflicts):**
   ```bash
   FUZZ_NUMBER=$RANDOM
   ```

2. **Start from main and sync:** 
   ```bash
   git switch main
   git pull
   ```

3. **Create a branch using that number:**
   ```bash
   git switch -c fuzz-$FUZZ_NUMBER
   ```

4. **Run the fuzzer** to find a discrepancy where both parsers succeed but differ:
   ```bash
   uv run python tools/fuzzer/fuzz.py --both-succeed --stop-after 1 -v
   ```

5. **Create an MRE.** Shrink the input to the smallest string that still shows the discrepancy:
   ```bash
   ~/source/bash-oracle/bash-oracle -e 'INPUT'   # oracle
   uv run bin/parable-dump.py 'INPUT'            # parable
   ```
   Keep removing characters until you can't anymore.

6. **Add a failing test** to `tests/parable/fuzz-$FUZZ_NUMBER.tests`:
   ```
   === descriptive name
   INPUT
   ---
   (expected s-expr from bash-oracle)
   ---
   ```

7. **Verify the test fails:**
   ```bash
   just fmt --fix
   just lint --fix
   just test
   ```

8. **Fix the bug** in `src/parable.py`. The fix should make Parable match bash-oracle.

9. **Run the full check:**
   ```bash
   just fmt --fix
   just lint --fix
   just check
   ```
   This MUST pass before you are done.

10. **Commit, push, and create the PR:**
    ```bash
    git add -A
    git commit -m "fuzzer fix: <short description>"
    git push -u origin HEAD
    gh pr create --title "fuzzer fix: <short description>" --body ""
    ```

    Include this in the PR body:
    ```
    ## Summary
    - Brief description bug and fix, include the MRE

    ## Test plan
    - [ ] New test added to `tests/parable/fuzz-$FUZZ_NUMBER.tests`
    - [ ] `just check` passes
    ```

## Notes

- If the fuzzer finds no discrepancies, exit successfully with no changes
- If the MRE turns out to be a bash-oracle bug (not Parable), try again with the fuzzer
- ONLY modify files directly related to the fix
