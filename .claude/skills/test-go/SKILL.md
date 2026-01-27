---
name: test-go
description: Run transpiler tests, fix failures, commit only on improvement
---

Iteratively improve the new IR-based transpiler by fixing test failures.

## Paths

All paths are relative to `/Users/lily/source/Parable/`:

| Path | Description |
|------|-------------|
| `src/parable.py` | Python source being transpiled |
| `transpiler/parable-old-transpiler-output.go` | Working Go code from old transpiler (reference only, DO NOT modify) |
| `transpiler/dist/parable.go` | Generated Go output from new transpiler |
| `transpiler/src/` | New transpiler source code to edit |
| `tools/transpiler/src/transpiler/` | Old transpiler source (reference only) |

## Workflow

### Step 1: Transpile and get baseline

```bash
cd /Users/lily/source/Parable/transpiler
uv run python -m src.cli ../src/parable.py > /tmp/parable-ir.go && gofmt /tmp/parable-ir.go > dist/parable.go
```

Then run full test suite, saving output to /tmp:
```bash
cd /Users/lily/source/Parable/transpiler/dist
go run ./cmd/run-tests ../../tests > /tmp/test-output.txt 2>&1
tail -3 /tmp/test-output.txt
```

Parse the line: `X passed, Y failed in Z.XXs`
Store `baseline_passed = X` and `baseline_failed = Y`.

### Step 2: Pick a failure and jump in

View the first failures:
```bash
head -100 /tmp/test-output.txt
```

Pick a failure with a small, simple input and start working on it immediately. Skip huge multi-line inputs in favor of small ones.

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

Retranspile and run full suite:
```bash
cd /Users/lily/source/Parable/transpiler
uv run python -m src.cli ../src/parable.py > /tmp/parable-ir.go && gofmt /tmp/parable-ir.go > dist/parable.go
cd dist && go run ./cmd/run-tests ../../tests 2>&1 | tail -1
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

### Step 8: Stop

DO NOT CONTINUE after a commit

## Common Issues

- **Missing method**: Frontend not emitting IR for a Python method
- **Wrong type**: Frontend inferring wrong type, backend emits wrong Go
- **Missing conversion**: Python idiom not translated (e.g., string methods)
- **Struct issues**: Fields, embedding, or methods not generated correctly

## Important

- Only commit when tests improve
- Small incremental fixes are better than big risky changes
- Backend must remain generic. It's cheating to look for Parable-specific names.
- Do not directly modify parable.go, it's generated output.