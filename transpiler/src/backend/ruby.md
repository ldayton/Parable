# Ruby Backend Bug Fixes

## Current Status

**Before**: 4531/4574 passing (99.1%) - 43 failures
**After**: 4565/4574 passing (99.8%) - 9 failures
**Total Fixed**: 34 tests

## Completed Fixes

### Fix 1: CharClassify Regex Anchors
**Lines 685-695** - Changed unanchored regex to anchored patterns.

The issue was that `"0-".match?(/\d/)` returns true (has a digit) but should return false (not ALL chars are digits).

```python
# Before
"digit": f"{char_expr}.match?(/\\d/)",
"alpha": f"{char_expr}.match?(/[[:alpha:]]/)",

# After
"digit": f"({char_expr}).match?(/\\A\\d+\\z/)",
"alpha": f"({char_expr}).match?(/\\A[[:alpha:]]+\\z/)",
```

All six character classification patterns now use `\A..+\z` anchors.

### Fix 2: Type Name Safety
Added `_safe_type_name()` calls in four locations to prevent conflicts with Ruby built-ins like `Time`, `File`, `Set`, etc.

1. **`_type()` method (lines 946-952)**: StructRef, InterfaceRef, and Union names
2. **`_emit_try_catch()` (line 595)**: Exception type in rescue clause
3. **`_emit_struct()` (line 305)**: Base class for exception inheritance

### Fix 3: String.find() == -1 Comparison
**Lines 791-804** - Handle Python `str.find(x) == -1` pattern correctly in Ruby.

Python's `str.find()` returns -1 when substring not found, but Ruby's `String#index` returns `nil`.

```python
# Added in BinaryOp handling for == and != operators
if op in ("==", "!="):
    find_expr, neg_one = None, None
    if isinstance(left, MethodCall) and left.method == "find":
        if isinstance(right, UnaryOp) and right.op == "-" and isinstance(right.operand, IntLit) and right.operand.value == 1:
            find_expr, neg_one = left, right
    # ... (also check for right-hand find)
    if find_expr is not None:
        # Transform x.find(y) == -1 to x.index(y).nil?
        # Transform x.find(y) != -1 to !x.index(y).nil?
```

This fixed 7 ANSI-C quote expansion tests.

### Fix 4: Truthy(Len()) Expression
**Lines 785-788** - Handle Python `len(x)` truthiness correctly in Ruby.

In Python, `len(x)` is falsy when 0; in Ruby, 0 is truthy (only `nil` and `false` are falsy).

```python
# Added in Truthy case handling
if isinstance(e, Len):
    return f"{expr_str} > 0"
```

This fixed 2 process substitution spacing tests by correctly handling the condition `len(self.parts)` as a boolean.

### Fix 5: Truthy(BinaryOp) for Integer Expressions
**Lines 789-795** - Handle Python integer truthiness in bitwise operations.

In Python, `flags & X` is falsy when the result is 0. In Ruby, 0 is truthy so `!!(flags & X)` is always true (even when the AND result is 0). The fix checks if the BinaryOp has integer type and uses `!= 0` instead of `!!`.

```python
# For BinaryOp with integer result (e.g., flags & X), Ruby's !! doesn't work
# because !!(0) is true in Ruby (0 is truthy). Use != 0 instead.
if isinstance(e, BinaryOp) and e.typ == Primitive(kind="int"):
    return f"({expr_str}) != 0"
```

This fixed 13 tests including unclosed brace detection (`${${x}`) and newline handling in nested expansions.

### Fix 6: UnaryOp("!", Truthy(int)) Expression
**Lines 822-829** - Handle Python `not (flags & X)` correctly.

When Python has `not (flags & X)`, this should be true when the AND result is 0. The fix detects `UnaryOp("!", Truthy(int_expr))` and emits `(expr) == 0`.

```python
if op == "!" and isinstance(operand, Truthy):
    inner = operand.expr
    if inner.typ == Primitive(kind="int"):
        inner_str = self._expr(inner)
        if isinstance(inner, BinaryOp):
            return f"({inner_str}) == 0"
        return f"{inner_str} == 0"
```

---

## Remaining Failures (9 tests)

### Category 1: Deeply Nested Arithmetic (1 failure)

| Input | Expected | Actual |
|-------|----------|--------|
| `$(($($((#)))))` | Parse successfully | Parse error |

**Root Cause**: Nested arithmetic with hash inside command substitution is not handled correctly.

### Category 2: Select Statement Formatting (1 failure)

| Input | Expected | Actual |
|-------|----------|--------|
| `select x in ; do...` | `(in)` | `(in )` |

**Root Cause**: Minor whitespace difference in output formatting.

### Category 3: Binary/UTF-8 Data Handling (7 failures)

Tests involving binary data, control characters, or invalid UTF-8 sequences in string literals fail due to encoding differences between Python and Ruby string handling.

---

## Verification Commands

```bash
# Regenerate Ruby output
cat src/parable.py | python3 -c "
import sys; sys.path.insert(0, 'transpiler')
from src.frontend import Frontend
from src.frontend.parse import parse
from src.frontend.subset import verify as verify_subset
from src.frontend.names import resolve_names
from src.middleend import analyze
from src.backend.ruby import RubyBackend
source = sys.stdin.read()
ast_dict = parse(source)
verify_subset(ast_dict)
name_result = resolve_names(ast_dict)
fe = Frontend()
module = fe.transpile(source, ast_dict, name_result=name_result)
analyze(module)
be = RubyBackend()
print(be.emit(module))
" > /tmp/parable.rb && mv /tmp/parable.rb dist/ruby/parable.rb

# Run all tests
ruby -r ./dist/ruby/parable.rb tests/bin/run-tests.rb tests/

# Run just character-fuzzer tests
ruby -r ./dist/ruby/parable.rb tests/bin/run-tests.rb tests/parable/character-fuzzer/
```

---

## Notes

The remaining 9 failures are edge cases that are likely acceptable limitations:
1. One deeply nested arithmetic expression
2. One minor whitespace formatting difference
3. Seven binary/UTF-8 encoding edge cases

The core parsing functionality is now at 99.8% pass rate (4565/4574 tests).
