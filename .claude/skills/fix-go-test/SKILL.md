---
name: fix-go-test
description: Fix the first failing Go transpiler test, verify improvement
---

Fix one failing test in the Go transpiler, then verify the fix reduced failures.

## Workflow

### Step 1: Get baseline failure count

Run `just test-go` and capture the failure count from the output line:
```
X passed, Y failed in Z.XXs
```

Store Y as `baseline_failures`.

### Step 2: Find a good failing test

Run with filter to see failing tests with details (limited to 50):
```bash
go run -C src ./cmd/run-tests -f "oils/misc.tests" 2>&1 | head -100
```

If the first failure is a large multi-command test (like `arith` or `builtins`), look for a simpler single-command test. Tests in `oils/` or `parable/` directories tend to be smaller.

To get details on a specific test:
```bash
go run -C src ./cmd/run-tests -f "test name substring" 2>&1
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
cd ~/source/Parable/src && go run /tmp/test_parser.go 'bash code here'
```

### Step 4: Fix the transpiler

**IMPORTANT:** `src/parable.go` is generated code - do NOT edit it directly.

Edit the transpiler instead: `tools/transpiler/src/transpiler/transpile_go.py`

The reference implementation is `src/parable.py`. The transpiler converts Python → Go.

When fixing:
1. Find the relevant Python code in `src/parable.py`
2. Find the corresponding transpiler logic in `transpile_go.py`
3. Fix the transpiler to generate correct Go code
4. Run `just test-go` which regenerates and tests

### Step 5: Verify improvement

Run `just test-go` again and extract the new failure count.

**Success criteria:** New failure count < baseline_failures

### Step 6: Commit the fix

If the failure count decreased, commit the transpiler change:
```bash
git add tools/transpiler/src/transpiler/transpile_go.py && git commit -m "Fix: [brief description of what was fixed]"
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
2. Search for the same name in `transpile_go.py` to find the transpiler handling

For silent failures (wrong output, not panics):
1. Identify which AST node type has the wrong ToSexp() output
2. Find the class in `src/parable.py` and look at its `to_sexp()` method
3. Search for the transpiler code that handles that pattern (e.g., isinstance checks)

## Common Transpiler Patterns

The transpiler converts Python → Go. Common issues:

- **isinstance with else**: `if isinstance(x, str): ... else: ...` needs a `default:` case in the Go type switch
- **Method calls on interface types**: Need type assertions like `x.(Node).Method()`
- **None vs empty string**: Python `None` may need to be `""` or `nil` in Go depending on context

## Important Notes

- Fix ONE root cause per invocation (but this may fix many tests)
- If the fix doesn't reduce failures, revert and report the issue
- Panics (`<exception>`) are usually missing error handling in the Go code
- Silent failures (empty output) are often missing type switch cases
- The Python parser is the reference implementation - match its behavior
- A good fix to a fundamental transpiler issue can reduce 100+ failures at once
