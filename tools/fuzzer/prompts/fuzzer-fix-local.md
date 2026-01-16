## Local: Git Setup and PR Creation

**Pre-flight check** (run once at the start):
```bash
gh api repos/:owner/:repo --jq '.permissions.push'
```
If this returns `false`, the token lacks push permissions and PRs will fail. Stop and report the error.

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

Once the PR is created, wait for CI to register (max 5 attempts):
```bash
for i in 1 2 3 4 5; do
  sleep 10
  STATUS=$(gh pr view <PR#> --json statusCheckRollup --jq '.statusCheckRollup | length')
  if [ "$STATUS" -gt 0 ]; then
    echo "CI registered, waiting for completion..."
    gh pr checks <PR#> --watch
    break
  fi
  echo "Attempt $i: no checks yet..."
  if [ "$i" -eq 5 ]; then
    echo "ERROR: CI never started after 5 attempts. This usually means the PR was created by a bot token and GitHub is blocking workflow triggers. A human must manually trigger the workflow or merge the PR."
    exit 1
  fi
done
```

After the workflow passes, squash merge and delete the remote branch:
```bash
gh pr merge <PR#> --squash --delete-branch
```

**Important:** GitHub requires the "Just Check" workflow to pass before allowing the merge. Do not attempt to merge until the checks complete successfully.

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
