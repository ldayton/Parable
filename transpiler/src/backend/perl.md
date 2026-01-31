# Perl Backend Status

## Current State

- **Codegen tests**: 39/39 passing
- **Syntax check** (`just prep pl`): Passes with warnings
- **Test runner** (`just test pl`): 40 passed, 4534 failed

## Known Issues

### 1. Module-Level Functions in Wrong Package (BLOCKING)

**Symptom**: `Undefined subroutine &main::parse` at runtime

**Cause**: After emitting classes (`package Foo; ... package Bar; ...`), module-level functions are still inside the last package scope (`package Parser;`). The test runner calls `main::parse()` but the function is actually `Parser::parse()`.

**Evidence**:
```
$ rg -n "^package" /tmp/transpile.pl | tail -3
5035:package Coproc;
5062:package Parser;
# No "package main;" before module-level functions

$ rg -n "^sub parse\b" /tmp/transpile.pl
9012:sub parse ($self) {      # Parser method
10959:sub parse ($source, $extglob) {  # Module-level function (but inside Parser::)
```

**Fix**: Emit `package main;` before module-level functions when classes have been emitted. In `_emit_module()`, after emitting all packages and before emitting module-level functions:
```perl
package main;  # Return to main package for module-level functions

sub parse ($source, $extglob) { ... }
sub new_parser (...) { ... }
```

**Location**: `perl.py:_emit_module()` - add `package main;` transition

### 2. Subroutine Redefinition Warnings

**Symptom**: `Subroutine parse_compound_command redefined at line 8670`

**Cause**: The IR contains functions with the same name at different scopes (e.g., `Parser.parse` method and `parse` module-level function). When all end up in the same Perl package, they collide.

**Evidence**:
```
Subroutine parse_compound_command redefined at /tmp/transpile.pl line 8670.
Subroutine parse redefined at /tmp/transpile.pl line 10959.
```

**Fix**: This will be resolved by Issue #1 - once module-level functions go to `package main;`, they won't collide with class methods in their respective packages.

### 3. Variable Masking Warnings (42 instances)

**Symptom**: `"my" variable $foo masks earlier declaration in same scope`

**Cause**: We pre-declare variables at function scope (`my $foo;`) to handle Perl's block scoping, but the middleend also hoists declarations before control flow. This causes:
```perl
my $op;  # Our pre-declaration
...
my $op = ...;  # Middleend hoisting - masks the earlier one
```

**Evidence**: 42 warnings like:
```
"my" variable $op masks earlier declaration in same scope at line 1734
"my" variable $ch masks earlier declaration in same scope at line 6654
```

**Fix Options**:
1. **Skip `my` for pre-declared vars in `_emit_hoisted_vars`**: Track which vars were pre-declared and don't emit `my` again
2. **Use assignment instead of declaration for hoisted vars**: Change `my $x = ...` to `$x = ...` when var is pre-declared

**Location**: `perl.py:_emit_hoisted_vars()` - check against `_predeclared_vars` set

### 4. Character Iteration Bug

**Symptom**: Iterating over string characters produces wrong results

**Evidence**: In generated code:
```perl
for my $c (@{substr($name, 1)}) {  # WRONG: substr returns string, not arrayref
```

**Fix**: String character iteration needs `split('', substr($name, 1))`:
```perl
for my $c (split('', substr($name, 1))) {
```

**Location**: `perl.py:_emit_for_range()` - handle `Slice(Primitive("byte"))` over string

---

## Implementation Plan

### Phase 1: Fix Package Scoping (Critical)

1. Track whether any classes have been emitted in `_emit_module()`
2. Before emitting module-level functions, emit `package main;` if classes were emitted
3. Verify with `just test pl` - should eliminate "Undefined subroutine" errors

### Phase 2: Fix Variable Masking Warnings

1. Add `_predeclared_vars: set[str]` to track pre-declared variables per function
2. Populate it in `_emit_function_body()` from `_collect_undeclared_assigns()`
3. In `_emit_hoisted_vars()`, skip `my` for vars already in `_predeclared_vars`

### Phase 3: Fix String Iteration

1. In `_emit_for_range()`, detect when iterating over string bytes
2. Emit `split('', $str)` instead of `@{$str}`

### Phase 4: Run Full Test Suite

1. `just test pl` - aim for majority passing
2. Analyze remaining failures by category
3. Fix in priority order

---

## Reference: Original Implementation Plan

<details>
<summary>Initial design document (click to expand)</summary>

### Goal
Create a clean, generic Perl backend for the Tongues transpiler that:
- Uses only IR type information (no type override tables)
- Has no domain-specific knowledge (no hardcoded interface names, prefixes, etc.)
- Follows Perl idioms (sigils, references, `use strict; use warnings;`)
- Targets Perl 5.36+ with native subroutine signatures

### Type Mapping

| IR Type | Perl Representation | Notes |
|---------|---------------------|-------|
| `Primitive("string")` | scalar | Native |
| `Primitive("int")` | scalar | Native (arbitrary precision) |
| `Primitive("bool")` | scalar | `1`/`0` or `!!` for coercion |
| `Slice(T)` | arrayref `[]` | `@$ref` to dereference |
| `Map(K, V)` | hashref `{}` | `%$ref` to dereference |
| `Optional(T)` | scalar | `undef` for None |
| `StructRef(X)` | blessed hashref | `bless {}, 'X'` |
| `FuncType` | coderef | `sub { ... }` or `\&name` |

### Key Perl Operators

| Operation | Numeric | String |
|-----------|---------|--------|
| Equal | `==` | `eq` |
| Not equal | `!=` | `ne` |
| Less than | `<` | `lt` |
| Greater than | `>` | `gt` |
| Concatenate | N/A | `.` |

### IR → Perl Mappings

| IR Construct | Perl Output |
|--------------|-------------|
| `Len(slice)` | `scalar @$slice` |
| `Len(str)` | `length($s)` |
| `Index(slice, i)` | `$slice->[$i]` |
| `Index(str, i)` | `substr($s, $i, 1)` |
| `IsNil(x)` | `!defined($x)` |
| `TryCatch` | `eval { ... }; if ($@) { ... }` |
| `Raise(msg)` | `die $msg` |
| `Break` | `last` |
| `Continue` | `next` |
| `ForRange(i, 0, n)` | `for my $i (0 .. $n-1)` |

</details>

---

## Verification Commands

```bash
# Syntax check only
just prep pl

# Full test suite
just test pl

# Codegen tests (should stay at 39/39)
just test-codegen

# Debug specific function
just emit pl | grep -A 20 "^sub parse "
```
