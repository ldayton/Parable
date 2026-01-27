---
name: fix-go-test
description: Fix a random failing Go transpiler test, verify improvement
---

Fix a randomly-selected failing test in the new IR-based Go transpiler, then verify the fix reduced failures.

**CRITICAL: Only use `just test-new-go`. Do not run any other just target under any circumstances.**

## Workflow

### Step 1: Get baseline failure count

Run from the `transpiler/` directory:
```bash
just test-new-go
```

Capture the failure count from the output line:
```
X passed, Y failed in Z.XXs
```

Store Y as `baseline_failures`.

### Step 2: Find a good failing test

Run with filter to see failing tests with details:
```bash
go run -C transpiler/dist ./cmd/run-tests -f "oils/misc.tests" ../../tests 2>&1 | head -100
```

**Select a random failure** from the list, not the first one. If your random selection is a large multi-command test (like `arith` or `builtins`), pick a different random test. Tests in `oils/` or `parable/` directories tend to be smaller.

To get details on a specific test:
```bash
go run -C transpiler/dist ./cmd/run-tests -f "test name substring" ../../tests 2>&1
```

### Step 3: Analyze the failure

Compare Expected vs Actual output. Common failure types:
- `<error>` expected but got `<exception>` → parser is panicking instead of returning error
- Output mismatch → transpiler logic bug
- Missing/extra whitespace → formatting issue
- **Empty or truncated output** → ToSexp() method returning wrong value (often a missing type switch case)

Read the relevant test file to understand the input and expected output.

**Debugging tip:** Create a test script to run the Go parser directly:
```bash
cd ~/source/Parable/transpiler/dist && go run /tmp/test_parser.go 'bash code here'
```

### Step 4: Fix the transpiler

**IMPORTANT:** `dist/parable.go` is generated code - do NOT edit it directly.

Edit the new IR-based transpiler instead. The transpiler is in `transpiler/src/`:
- `frontend.py` - Python AST → IR
- `middleend.py` - IR analysis
- `backend/go.py` - IR → Go code

The reference implementation is `src/parable.py`. The transpiler converts Python → Go.

When fixing:
1. Find the relevant Python code in `src/parable.py`
2. Find the corresponding transpiler logic in `transpiler/src/` (usually `frontend.py` or `backend/go.py`)
3. Fix the transpiler to generate correct Go code
4. Run `just test-new-go` which regenerates and tests

### Step 5: Verify improvement

Run `just test-new-go` again and extract the new failure count.

**Success criteria:** New failure count < baseline_failures

### Step 6: Commit the fix

If the failure count decreased, commit the transpiler change:
```bash
git -C transpiler add src/ && git -C transpiler commit -m "Fix: [brief description of what was fixed]"
```

Do NOT push.

### Step 7: Report

Output a summary:
```
Baseline: X failures
After fix: Y failures
Delta: -Z
Root cause: [brief description of the transpiler issue]
Commit: [commit hash]
```

## Test File Format

```
=== test name
input bash code
---
expected output (or <error> for syntax errors)
---
```

## Finding Corresponding Code

For panics, stack traces show Go function names like `_ReadBracedParam`:
1. Search for the same name in `src/parable.py` to find the reference implementation
2. Search for the same name in `transpiler/src/` to find the transpiler handling

For silent failures (wrong output, not panics):
1. Identify which AST node type has the wrong ToSexp() output
2. Find the class in `src/parable.py` and look at its `to_sexp()` method
3. Search for the transpiler code that handles that pattern (e.g., isinstance checks)

## Important Notes

- **Only use `just test-new-go`. No other just targets.**
- Fix ONE root cause per invocation (but this may fix many tests)
- If the fix doesn't reduce failures, revert and report the issue
- Panics (`<exception>`) are usually missing error handling in the Go code
- Silent failures (empty output) are often missing type switch cases
- The Python parser is the reference implementation - match its behavior
- A good fix to a fundamental transpiler issue can reduce 100+ failures at once
