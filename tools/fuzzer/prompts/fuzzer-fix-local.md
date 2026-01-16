## Local: Git Setup and PR Creation

**Before starting** (after step 1 in base):
```bash
git switch main
git pull
git switch -c fuzz-$FUZZ_ID
```

**After all checks pass** (after step 7 in base):

Commit, push, and create the PR:
```bash
git add -A
git commit -m "fuzzer fix: <short description>"
git push -u origin HEAD
gh pr create --title "fuzzer fix: <short description>" --body ""
```

Include this in the PR body:
```
## Summary
- Brief description of the bug and fix, include the MRE

## Test plan
- [ ] New test added to `tests/parable/character-fuzzer/fuzz-$FUZZ_ID.tests`
- [ ] `just check` passes
```
