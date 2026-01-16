Find and fix one parser bug using the fuzzer.

## Steps

1. **Run the fuzzer** to find a discrepancy where both parsers succeed but differ:
   ```bash
   cd tools/fuzzer && uv run fuzzer --character --both-succeed --stop-after 1 -v
   ```

2. **Create an MRE.** Shrink the input to the smallest string that still shows the discrepancy:
   ```bash
   ~/source/bash-oracle/bash-oracle -e 'INPUT'   # oracle
   uv run bin/parable-dump.py 'INPUT'            # parable
   ```
   Keep removing characters until you can't anymore.

3. **Add a failing test** to `tests/parable/36_fuzzer.tests`:
   ```
   === descriptive name
   INPUT
   ---
   (expected s-expr from bash-oracle)
   ---
   ```

4. **Verify the test fails:**
   ```bash
   just fmt --fix
   just lint --fix
   just test
   ```

5. **Fix the bug** in `src/parable.py`. The fix should make Parable match bash-oracle.

6. **Run the full check:**
   ```bash
   just fmt --fix
   just lint --fix
   just check
   ```
   This MUST pass before you are done.

7. **Write PR description** to `pr-body.md`:
   ```markdown
   ## Summary
   - Brief description of the bug and fix

   ## Test plan
   - [ ] New test added to `tests/parable/36_fuzzer.tests`
   - [ ] `just check` passes
   ```

## Notes

- If the fuzzer finds no discrepancies, exit successfully with no changes
- If the MRE turns out to be a bash-oracle bug (not Parable), try again with the fuzzer
- ONLY modify files directly related to the fix
- Do NOT create a git commit or PR (the workflow handles this)
