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

**Merging the PR:**

Once the PR is created, squash merge and delete the remote branch immediately:
```bash
gh pr merge <PR#> --squash --delete-branch
```

**Important:** Do NOT wait for GitHub workflow checks to complete. As long as `just check` passes locally, that's the only standard required. Merge immediately after creating the PR.

**If the merge fails due to conflicts:**

1. Try to salvage the PR by resolving conflicts:
   ```bash
   git switch main
   git pull
   git switch fuzz-$FUZZ_ID
   git rebase main
   # Resolve any conflicts
   just transpile  # Re-transpile after resolving conflicts
   git add -A
   git rebase --continue
   git push --force-with-lease
   ```

2. Run `just check` again to ensure everything still passes locally

3. If the bug is already fixed in main (your test now passes without your changes), close the PR and delete the remote branch:
   ```bash
   gh pr close <PR#>
   git push origin --delete fuzz-$FUZZ_ID
   ```

4. Otherwise, retry the merge:
   ```bash
   gh pr merge <PR#> --squash --delete-branch
   ```

**After successful merge:**

Output a success message in the format:
```
🚀 merge successful: <PR URL>
```
