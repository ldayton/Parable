---
name: c-fix
description: Run C transpiler tests, fix failures, commit only on improvement
---

Fix C backend test failures.

## Context

The transpiler converts `src/parable.py` into 10 target languages. The same source passes all tests in 9 other backends (Python, Go, Java, JavaScript, TypeScript, Ruby, Lua, PHP, C#). **The bug is always in `transpiler/src/backend/c.py`**, not in the source or tests.

## Paths

| Path                          | Description                                                |
| ----------------------------- | ---------------------------------------------------------- |
| `transpiler/src/backend/c.py` | C backend (edit this)                                      |
| `dist/c/`                     | Generated output (don't edit directly, but commit changes) |

## Running tests locally (no Docker)

Transpile, compile, and test all run locally. Combined one-liner:

```bash
cd /home/lilydayton/source/Parable/transpiler && uv run python -m src.tongues --target c < ../src/parable.py > ../dist/c/parable.c && cd ../dist/c && gcc -Wall -Wextra -O2 -std=c11 -o run_tests run_tests.c && ./run_tests ../../tests/ 2>&1 | tee /tmp/c-test.out | tail -2 | head -1
```

## Step 1: Get baseline and first failure

Run the one-liner above. Store baseline counts from `X passed, Y failed`.

Then list all failing tests (paths are relative, starting with `tests/`):
```bash
grep -E "^tests/" /tmp/c-test.out | head -20
```

Get details of a specific failure (replace TEST_NAME with actual test name from list):
```bash
grep -A50 "TEST_NAME" /tmp/c-test.out | head -60
```

The output shows:
- `Input:` - the shell code being parsed
- `Expected:` - the expected S-expression
- `Actual:` - what C produced (often `<parse error>`)
- `Error:` - the C error message showing what failed

## Step 2: Fix it

The error trace points to a line in `dist/c/parable.c`. Find the corresponding code in `transpiler/src/backend/c.py` and fix it.

## Step 3: Verify and commit

Re-run the one-liner from above. If `new_passed > baseline_passed`, run `just check` first:
```bash
just -f /home/lilydayton/source/Parable/justfile check
git -C /home/lilydayton/source/Parable add transpiler/src/ dist/
git -C /home/lilydayton/source/Parable commit -m "c: [fix description] (X→Y passing)"
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

- Run ALL commands directly with Bash—do NOT use the Task tool or spawn subagents
- Only commit when tests improve
- Small incremental fixes are better than big risky changes
- Backend must remain generic—no Parable-specific names
- Don't edit dist/ directly—it's generated, but do commit the regenerated output
