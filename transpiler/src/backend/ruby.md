# Ruby Backend Bug Fixes

## Status After Initial Fixes

**Before**: 4531/4574 passing (99.1%) - 43 failures
**After**: 4543/4574 passing (99.3%) - 31 failures
**Fixed**: 12 tests

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

---

## Remaining Failures (31 tests)

### Category 1: ANSI-C Quotes in Parameter Expansion (6 failures)

**Problem**: `$'...'` inside `${...}` is not being expanded.

| Input | Expected | Actual |
|-------|----------|--------|
| `"${$''}"` | `"${}"` | `"${''}"`|
| `"${x$''}"` | `"${x}"` | `"${x''}"` |
| `"${%$'b'}"` | `"${%b}"` | `"${%'b'}"` |
| `"${x~%$'b'}"` | `"${x~%b}"` | `"${x~%'b'}"` |

**Root Cause**: The `expand_all_ansi_c_quotes` function in the transpiled Ruby code has a logic issue. When inside `${...}`, it should expand `$'...'` but currently doesn't.

Looking at the Ruby output at line 2118:
```ruby
elsif starts_with_at(value, i, "$'") && !quote.single && !effective_in_dquote && ...
```

The `effective_in_dquote = quote.double` on line 2103 should be false after `quote.push()` resets state, but there may be an issue with how the condition chain works or how the quote state is being tracked.

**Investigation needed**:
- Trace through `expand_all_ansi_c_quotes` with input `"${$''}"` in both Python and Ruby
- Check if `quote.push()` and `quote.double` behave identically
- Verify `starts_with_at` function works correctly in Ruby

### Category 2: Newline Handling in Parameter Expansion (2 failures)

**Problem**: Newlines inside `${...}` cause word splitting.

| Input | Expected | Actual |
|-------|----------|--------|
| `${a${b}\nx}` | Single word | Split at newline |

**Root Cause**: The `normalize_param_expansion_newlines` function may not be handling all cases correctly in Ruby.

### Category 3: Parse Error Detection (2 failures)

**Problem**: Some malformed inputs are accepted instead of rejected.

| Input | Expected | Actual |
|-------|----------|--------|
| `${${x}` | Error (unclosed) | Accepted |
| `${x:-$(<})}` | Parse with `}` in filename | Parse error |

**Root Cause**: Brace depth tracking or error detection differs between Python and Ruby.

### Category 4: Process Substitution Spacing (2 failures)

**Problem**: Whitespace handling in `<(...)` differs.

| Input | Expected | Actual |
|-------|----------|--------|
| `((<( a)))` | `<( a)` preserved | `<(a)` space removed |
| `for ((<(a>b);;))` | `<(a>b)` preserved | `<(a > b)` spaces added |

**Root Cause**: The formatting functions for arithmetic expressions are normalizing whitespace differently.

### Category 5: Large Corpus Tests (19 failures)

These are in `tests/corpus/gnu-bash/` and appear to be downstream effects of the above issues, particularly the ANSI-C quote expansion problem affecting complex scripts.

---

## Implementation Plan for Remaining Fixes

### Priority 1: ANSI-C Quote Expansion (High Impact)

This is the highest priority as it affects the most tests.

**Approach**: Add debug tracing to compare Python vs Ruby behavior:

1. In Python, trace `_expand_all_ansi_c_quotes("\"${$''}\"")`:
   - Track `brace_depth`, `quote.single`, `quote.double`, `effective_in_dquote` at each step
   - Verify the `$'...'` branch is taken

2. In Ruby, add equivalent tracing and compare

3. The fix will likely be in one of:
   - The `starts_with_at` function (Ruby string indexing differs from Python)
   - The `quote.push`/`quote.pop` implementation
   - The condition ordering in the while loop

**Files to check**:
- `src/parable.py` lines 2380-2562: `_expand_all_ansi_c_quotes`
- `dist/rb/parable.rb` lines 2062-2200: `expand_all_ansi_c_quotes`

### Priority 2: Newline Handling

**Approach**: Compare `normalize_param_expansion_newlines` between Python and Ruby for the failing input.

### Priority 3: Parse Error Detection

**Approach**: These may be acceptable differences or may require adjusting brace depth tracking in the Ruby transpiled code.

### Priority 4: Process Substitution Spacing

**Approach**: Check arithmetic expression formatting in the transpiler output.

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
" > dist/rb/parable.rb

# Run all tests
ruby -r ./dist/rb/parable.rb tests/bin/run-tests.rb tests/

# Run just character-fuzzer tests
ruby -r ./dist/rb/parable.rb tests/bin/run-tests.rb tests/parable/character-fuzzer/

# Test specific input
echo '${$'"'"''"'"'}' | ruby -r ./dist/rb/parable.rb -e 'puts parse(STDIN.read.chomp).to_sexp'
```

---

## Notes

The remaining failures are NOT in the Ruby backend code generator (`transpiler/src/backend/ruby.py`). They are in the **transpiled parser** (`dist/rb/parable.rb`) - specifically in how the parsing/normalization functions behave differently in Ruby vs Python.

This means the fixes need to either:
1. Adjust the Python source (`src/parable.py`) to work correctly when transpiled to Ruby
2. Add Ruby-specific handling in the backend for these edge cases
3. Accept some behavioral differences as limitations
