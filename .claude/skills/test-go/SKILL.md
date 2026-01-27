---
name: test-go
description: Run transpiler tests, fix failures, commit only on improvement
---

Iteratively improve the new IR-based transpiler by fixing test failures.

## ⚠️ WARNING

**Only use `just test-new-go`** from the transpiler directory. Do NOT run any other just targets (like `just go`, `just check`, etc.) as they may have different behaviors or side effects.

## Paths

All paths are relative to `/Users/lily/source/Parable/`:

| Path | Description |
|------|-------------|
| `src/parable.py` | Python source being transpiled |
| `transpiler/parable-old-transpiler.go` | Working Go code from old transpiler (reference only, DO NOT modify) |
| `transpiler/dist/parable.go` | Generated Go output from new transpiler |
| `transpiler/src/` | New transpiler source code to edit |
| `tools/transpiler/src/transpiler/` | Old transpiler source (reference only) |

The `just test-new-go` target transpiles, writes to `transpiler/dist/`, and runs tests from there.

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
cd /Users/lily/source/Parable/transpiler/dist && go run ./cmd/run-tests -v ../../tests 2>&1 | head -100
```

Pick a failure that looks tractable. Smaller tests (oils/, parable/) are easier than large ones (gnu-bash/).

Get details on a specific test:
```bash
cd /Users/lily/source/Parable/transpiler/dist && go run ./cmd/run-tests -v -f "test name" ../../tests 2>&1
```

### Step 3: Compare generated vs working code

The working Go code from the old transpiler is at `transpiler/parable-old-transpiler.go`. Compare specific functions:
```bash
grep -A 50 "func.*FunctionName" /Users/lily/source/Parable/transpiler/parable-old-transpiler.go
```

Compare with generated code from new transpiler:
```bash
grep -A 50 "func.*FunctionName" /Users/lily/source/Parable/transpiler/dist/parable.go
```

### Step 4: Fix the transpiler

Edit files in `/Users/lily/source/Parable/transpiler/src/`:
- `ir.py` - IR node definitions
- `frontend.py` - Python AST → IR
- `middleend.py` - IR analysis
- `backend/go.py` - IR → Go code

### Step 5: Verify improvement

Run `just test-new-go` again:
```bash
cd /Users/lily/source/Parable/transpiler && just test-new-go 2>&1 | tail -5
```

Parse new counts: `new_passed` and `new_failed`.

**Success criteria:** `new_passed > baseline_passed`

### Step 6: Commit only if improved

If `new_passed > baseline_passed`, commit both the transpiler changes and the new generated output:
```bash
cd /Users/lily/source/Parable/transpiler
git add src/ dist/parable.go
git commit -m "transpiler: [description] (X→Y tests passing)"
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

## Common Issues

- **Missing method**: Frontend not emitting IR for a Python method
- **Wrong type**: Frontend inferring wrong type, backend emits wrong Go
- **Missing conversion**: Python idiom not translated (e.g., string methods)
- **Struct issues**: Fields, embedding, or methods not generated correctly

## Important

- **Only use `just test-new-go`** - no other just targets
- Only commit when tests improve
- Small incremental fixes are better than big risky changes
