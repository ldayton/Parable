## Workflow Mode

Do NOT run git commands or create PRs - the workflow handles this.

**After all checks pass** (after step 7 in base):

Write PR description to `pr-body.md`:
```markdown
## Summary
- Brief description of the bug and fix

## Test plan
- [ ] New test added to `tests/parable/character-fuzzer/fuzz-$FUZZ_ID.tests`
- [ ] `just check` passes
```
