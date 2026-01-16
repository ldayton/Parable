## Workflow Mode

**The fuzzer has already been run and the output is provided above.** Start from step 3 (creating the MRE).

Skip these steps (the workflow handles them):
- Steps 1-2: Fuzzer already ran
- Steps 5, 7: Workflow runs verification after you're done
- Git commands and PR creation

**Important:** You cannot run shell commands. Analyze the fuzzer output to understand the discrepancy, then:
1. Create the MRE by reasoning about what characters can be removed
2. Add the failing test file
3. Fix the bug in `src/parable.py`
4. Write pr-body.md

**After all checks pass** (after step 7 in base):

Write PR description to `pr-body.md`:
```markdown
## Summary
- Brief description of the bug and fix

## Test plan
- [ ] New test added to `tests/parable/character-fuzzer/fuzz-$FUZZ_ID.tests`
- [ ] `just check` passes
```
