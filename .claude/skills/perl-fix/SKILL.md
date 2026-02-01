---
name: perl-fix
description: Run Perl transpiler tests, fix failures, commit only on improvement
---

Fix Perl backend test failures.

## Context

The transpiler converts `src/parable.py` into 10 target languages. The same source passes all tests in 9 other backends (Python, Go, Java, JavaScript, TypeScript, Ruby, Lua, PHP, C#). **The bug is always in `transpiler/src/backend/perl.py`**, not in the source or tests.

## Paths

| Path                             | Description                                                |
| -------------------------------- | ---------------------------------------------------------- |
| `transpiler/src/backend/perl.py` | Perl backend (edit this)                                   |
| `dist/perl/`                     | Generated output (don't edit directly, but commit changes) |

## Step 1: Get baseline and first failure

```bash
cd /home/lilydayton/source/Parable
just backend-test perl 2>&1 | tail -2 | head -1
```

Store baseline counts from `X passed, Y failed`.

Then get actual failures:
```bash
perl dist/perl/parable.pl --run-tests tests -f 01_words 2>&1 | head -50
```

This filters to one test file and shows error details:
- `Input:` - the shell code being parsed
- `Expected:` - the expected S-expression
- `Actual:` - what Perl produced (often `<parse error>`)
- `Error:` - the Perl error message showing what failed

## Step 2: Fix it

The error trace points to a line in `dist/perl/parable.pl`. Find the corresponding code in `transpiler/src/backend/perl.py` and fix it.

## Step 3: Verify and commit

```bash
just backend-test perl 2>&1 | tail -2 | head -1
```

If `new_passed > baseline_passed`, run `just check` first:
```bash
just -f /home/lilydayton/source/Parable/justfile check
git -C /home/lilydayton/source/Parable add transpiler/src/ dist/
git -C /home/lilydayton/source/Parable commit -m "perl: [fix description] (X→Y passing)"
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
