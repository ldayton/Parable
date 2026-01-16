Find and fix one parser bug using the fuzzer.

## Steps

1. **Pick a unique ID for this run:**
   ```bash
   FUZZ_ID=$(openssl rand -hex 16)
   ```

2. **Run the fuzzer** to find a discrepancy where both parsers succeed but differ:
   ```bash
   cd tools/fuzzer && uv run fuzzer --character --both-succeed --stop-after 1 -n 100000 -v
   ```

3. **Create an MRE** using delta debugging to automatically minimize the input:
   ```bash
   cd tools/fuzzer && uv run fuzzer --minimize 'FAILING_INPUT'
   ```
   This outputs the smallest string that still shows the discrepancy.

4. **Add a failing test** to `tests/parable/character-fuzzer/fuzz-$FUZZ_ID.tests`:
   ```
   === descriptive name
   INPUT
   ---
   (expected s-expr from bash-oracle)
   ---
   ```

5. **Verify the test fails:**
   ```bash
   just fmt --fix
   just lint --fix
   just test
   ```

6. **Fix the bug** in `src/parable.py`. The fix should make Parable match bash-oracle.

7. **Run the full check:**
   ```bash
   just fmt --fix
   just lint --fix
   just check
   ```
   This MUST pass before you are done.

## Notes

- If the fuzzer finds no discrepancies, exit successfully with no changes
- If the MRE turns out to be a bash-oracle bug (not Parable), try again with the fuzzer
- ONLY modify files directly related to the fix
