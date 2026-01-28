---
name: java-fix
description: Run Java transpiler tests, fix failures, commit only on improvement
---

Fix Java backend test failures.

## Paths

| Path | Description |
|------|-------------|
| `transpiler/src/backend/java.py` | Java backend (edit this) |
| `dist/java/` | Generated output (don't edit directly, but commit changes) |

## Step 1: Get baseline and first failure

```bash
cd /Users/lily/source/Parable
just backend-test java 2>&1 | tail -1
```

Store baseline counts from `X passed, Y failed`.

Then get actual failures:
```bash
java -cp dist/java/classes Parable --run-tests tests -f 01_words 2>&1 | head -50
```

This filters to one test file and shows error details:
- `Input:` - the shell code being parsed
- `Expected:` - the expected S-expression
- `Actual:` - what Java produced (often `<exception>`)
- `Error:` - the Java stack trace showing what failed

## Step 2: Fix it

The error trace points to a method in `dist/java/Parable.java`. Find the corresponding code in `transpiler/src/backend/java.py` and fix it.

## Step 3: Verify and commit

```bash
just backend-test java 2>&1 | tail -1
```

If `new_passed > baseline_passed`, run `just check` first:
```bash
just -f /Users/lily/source/Parable/justfile check
git -C /Users/lily/source/Parable add transpiler/src/ dist/
git -C /Users/lily/source/Parable commit -m "transpiler/java: [fix description] (X→Y passing)"
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
