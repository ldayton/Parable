---
name: ts-fix
description: Run TypeScript transpiler tests, fix failures, commit only on improvement
---

Fix TypeScript backend test failures.

## Paths

| Path | Description |
|------|-------------|
| `transpiler/src/backend/typescript.py` | TypeScript backend (edit this) |
| `dist/` | Generated output for all backends (don't edit directly, but commit changes) |

## Step 1: Get baseline and first failure

```bash
cd /Users/lily/source/Parable
just backend-test ts 2>&1 | tail -1
```

Store baseline counts from `X passed, Y failed`.

Then get actual failures (the runner hides them when >110):
```bash
node tests/bin/run-js-tests.js dist/js -f 01_words 2>&1 | head -50
```

This filters to one test file and shows error details:
- `Input:` - the shell code being parsed
- `Expected:` - the expected S-expression
- `Actual:` - what JS produced (often `<exception>`)
- `Error:` - the JS stack trace showing what failed

## Step 2: Fix it

The error trace points to a function in `dist/js/parable.js`. Find the corresponding code in `transpiler/src/backend/typescript.py` and fix it.

## Step 3: Verify and commit

```bash
just backend-test ts 2>&1 | tail -1
```

If `new_passed > baseline_passed`, run `just check` first:
```bash
just -f /Users/lily/source/Parable/justfile check
git -C /Users/lily/source/Parable add transpiler/src/ dist/
git -C /Users/lily/source/Parable commit -m "transpiler/ts: [fix description] (X→Y passing)"
```

## Step 4: Report and stop

```
Baseline: X passed, Y failed
After: A passed, B failed
Delta: +Z passing
Fix: [what you changed]
Commit: [hash]
```

DO NOT CONTINUE after a commit.

## Important

- Only commit when tests improve
- Small incremental fixes are better than big risky changes
- Backend must remain generic—no Parable-specific names
- Don't edit dist/ directly—it's generated, but do commit the regenerated output
