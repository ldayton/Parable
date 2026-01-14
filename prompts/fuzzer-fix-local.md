Find and fix one parser bug using the fuzzer.

## Steps

1. **Start from main and sync:** 
   ```bash
   git switch main
   git pull
   ```

2. **Create a branch with a random name:**
   ```bash
   git switch -c fuzz-$RANDOM
   ```

3. **Run the fuzzer** to find a discrepancy where both parsers succeed but differ:
   ```bash
   uv run python tools/fuzzer/fuzz.py --both-succeed --stop-after 1 -v
   ```

4. **Create an MRE.** Shrink the input to the smallest string that still shows the discrepancy:
   ```bash
   ~/source/bash-oracle/bash-oracle -e 'INPUT'   # oracle
   uv run bin/parable-dump.py 'INPUT'            # parable
   ```
   Keep removing characters until you can't anymore.

5. **Add a failing test** to `tests/parable/36_fuzzer.tests`:
   ```
   === descriptive name
   INPUT
   ---
   (expected s-expr from bash-oracle)
   ---
   ```

6. **Verify the test fails:**
   ```bash
   just fmt --fix
   just lint --fix
   just test
   ```

7. **Fix the bug** in `src/parable.py`. The fix should make Parable match bash-oracle.

8. **Run the full check:**
   ```bash
   just fmt --fix
   just lint --fix
   just check
   ```
   This MUST pass before you are done.

9. **Commit, push, and create the PR:**
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
    - [ ] New test added to `tests/parable/36_fuzzer.tests`
    - [ ] `just check` passes
    ```

## Notes

- If the fuzzer finds no discrepancies, exit successfully with no changes
- If the MRE turns out to be a bash-oracle bug (not Parable), try again with the fuzzer
- ONLY modify files directly related to the fix
