---
name: test-go
description: Run transpiler tests, fix failures, commit only on improvement
---

Iteratively improve the new IR-based transpiler by fixing test failures.

## Workflow

### Step 1: Get baseline

Run `just test-new-go` from the transpiler directory and capture counts:
```bash
cd /Users/lily/source/Parable/transpiler && just test-new-go 2>&1 | tail -5
```

Parse the line: `X passed, Y failed in Z.XXs`
Store `baseline_passed = X` and `baseline_failed = Y`.

### Step 2: Pick a failure to investigate

Run with verbose output to see specific failures:
```bash
cd /Users/lily/source/Parable/src && go run ./cmd/run-tests -v 2>&1 | head -100
```

Pick a failure that looks tractable. Smaller tests (oils/, parable/) are easier than large ones (gnu-bash/).

Get details on a specific test:
```bash
cd /Users/lily/source/Parable/src && go run ./cmd/run-tests -f "test name" -v 2>&1
```

### Step 3: Compare generated vs working code

The working Go code is in git history. Compare specific functions:
```bash
git -C /Users/lily/source/Parable show HEAD:src/parable.go | grep -A 50 "func.*FunctionName"
```

Compare with generated code:
```bash
grep -A 50 "func.*FunctionName" /Users/lily/source/Parable/transpiler/dist/parable.go
```

### Step 4: Fix the transpiler

Edit files in `/Users/lily/source/Parable/transpiler/src/`:
- `ir.py` - IR node definitions
- `frontend.py` - Python AST → IR
- `middleend.py` - IR analysis
- `backend/go.py` - IR → Go code

The source being transpiled is `/Users/lily/source/Parable/src/parable.py`.

### Step 5: Verify improvement

Run `just test-new-go` again:
```bash
cd /Users/lily/source/Parable/transpiler && just test-new-go 2>&1 | tail -5
```

Parse new counts: `new_passed` and `new_failed`.

**Success criteria:** `new_passed > baseline_passed`

### Step 6: Commit only if improved

If `new_passed > baseline_passed`:
```bash
cd /Users/lily/source/Parable/transpiler
git add src/ dist/parable.go
git commit -m "transpiler: [description] (X→Y tests passing)"
```

Restore src/parable.go after testing:
```bash
git -C /Users/lily/source/Parable checkout src/parable.go
```

If no improvement, revert changes and try a different approach.

### Step 7: Report

```
Baseline: X passed, Y failed
After: A passed, B failed
Delta: +Z passing
Root cause: [what was wrong in the transpiler]
Fix: [what you changed]
Commit: [hash or "no commit - no improvement"]
```

## Key Files

| File | Purpose |
|------|---------|
| `src/parable.py` | Python source being transpiled |
| `transpiler/src/frontend.py` | Python AST → IR |
| `transpiler/src/backend/go.py` | IR → Go code |
| `transpiler/dist/parable.go` | Generated Go output |
| `src/parable.go` | Working Go (in git, don't edit) |

## Common Issues

- **Missing method**: Frontend not emitting IR for a Python method
- **Wrong type**: Frontend inferring wrong type, backend emits wrong Go
- **Missing conversion**: Python idiom not translated (e.g., string methods)
- **Struct issues**: Fields, embedding, or methods not generated correctly

## Important

- Only commit when tests improve
- Restore `src/parable.go` from git after testing
- Small incremental fixes are better than big risky changes
- Check `just check` compiles before running full tests
