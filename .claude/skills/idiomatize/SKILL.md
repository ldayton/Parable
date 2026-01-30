---
name: idiomatize
description: Find non-idiomatic patterns in transpiler output, write tests, fix them
args: <lang>
---

Improve idiomaticity of transpiler output for a target language.

## Arguments

- `<lang>`: Target language (`python`, `go`, `java`, `ts`)

## Paths

| Path | Description |
|------|-------------|
| `transpiler/src/backend/<lang>.py` | Backend to fix |
| `transpiler/src/frontend/lowering.py` | Lowering phase (for IR-level fixes) |
| `transpiler/src/ir.py` | IR definitions |
| `transpiler/tests/codegen/<lang>_idioms.tests` | Idiom tests for this language |
| `transpiler/spec.md` | Spec for which phase handles what |

## Step 1: Find non-idiomatic patterns

Transpile sample code and inspect output:

```bash
cd /Users/lily/source/Parable/transpiler
echo 'def foo(x: int) -> int:
    return x + 1' | uv run python -m src.tongues --target <lang> 2>/dev/null
```

For real-world output, transpile the parser:
```bash
uv run python -m src.tongues --target <lang> < ../src/parable.py 2>/dev/null | head -200
```

Look for:
- Factory functions instead of constructors
- Marker variables that shouldn't appear
- Non-idiomatic naming (PascalCase methods in Python, etc.)
- Unnecessary helper functions
- Verbose patterns that have idiomatic equivalents

## Step 2: Consult spec.md

Read `transpiler/spec.md` to determine which phase should handle the fix:
- **Frontend/lowering**: IR-level issues (marker variables, semantic IR nodes)
- **Backend**: Language-specific emission

## Fixing at the right layer

**Never compensate in backends for problems in lowering.** If lowering emits non-semantic IR that produces ugly output, fix lowering to emit semantic IR—even if it means updating other backends.

Example of the wrong approach:
- Lowering expands `a, b = stack.pop()` into 4 statements for Go's benefit
- Python backend detects this pattern and re-condenses it
- This is a workaround, not a fix

Example of the right approach:
- Lowering emits semantic `TupleAssign` with `MethodCall("pop")`
- Python backend emits `a, b = stack.pop()` naturally
- Go backend expands it because Go slices don't have `.pop()`

The principle: **Each backend handles its own limitations.** Lowering should emit the most semantic IR possible. Backends that can't handle it expand/transform as needed.

## Step 3: Write a failing test

Add a test to `transpiler/tests/codegen/<lang>_idioms.tests`:

```
=== descriptive test name
<python input>
--- <lang>
<expected idiomatic output>
---
```

For Python, omit `--- python` to use input as expected (identity transform).

**IMPORTANT:** Verify the test FAILS before proceeding:
```bash
just test-codegen
```

If the test passes, the pattern is already idiomatic—find a different one.

## Step 4: Fix it

Based on spec.md:
- If lowering issue: edit `src/frontend/lowering.py`
- If backend issue: edit `src/backend/<lang>.py`
- If new IR node needed: add to `src/ir.py`, update all backends

## Step 5: Verify and commit

Run the full check suite **from the repository root** (not from transpiler/):
```bash
just -f /Users/lily/source/Parable/justfile check
```

If all checks pass:
```bash
git -C /Users/lily/source/Parable add transpiler/ dist/
git -C /Users/lily/source/Parable commit -m "transpiler/<lang>: [fix description]"
```

Do NOT commit if `just check` fails.

## Step 6: Report

```
Pattern: [what was non-idiomatic]
Phase: [lowering|backend]
Fix: [what you changed]
Test: [test name in <lang>_idioms.tests]
```

## Common non-idiomatic patterns by language

### Python
- `_skip_super_init` marker in output
- `NewFoo()` factory functions instead of `Foo()`
- PascalCase method names (`GetKind` vs `get_kind`)
- `self._stack = self._stack[:-1]` instead of `self._stack.pop()`

### Go
- Helper functions instead of stdlib (`_parseInt` vs `strconv.Atoi`)
- `_runeAt`/`_runeLen` instead of proper `[]rune` handling
- IIFE for ternary instead of if/else assignment

### Java
- `String.valueOf(s.charAt(i))` for char comparisons
- Helper predicates taking `String` instead of `char`
- Field-by-field init instead of constructor

### TypeScript
- `var` instead of `let`/`const`
- `any` type instead of proper types
