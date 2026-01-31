# Perl Backend Implementation Plan

## Goal
Create a clean, generic Perl backend for the Tongues transpiler that:
- Uses only IR type information (no type override tables)
- Has no domain-specific knowledge (no hardcoded interface names, prefixes, etc.)
- Follows Perl idioms (sigils, references, `use strict; use warnings;`)
- Targets Perl 5.36+ with native subroutine signatures

## Files to Create

### `/Users/lily/source/Parable/transpiler/src/backend/perl.py`

```python
class PerlBackend:
    def __init__(self) -> None:
        self.indent = 0
        self.lines: list[str] = []
        self.receiver_name: str | None = None

    def emit(self, module: Module) -> str:
        """Emit complete Perl source from IR Module."""
```

**Structure:**
1. Reserved word handling (`_PERL_RESERVED` frozenset, suffix `_` for escaping)
2. Naming helpers (`_snake()`, `_safe_name()`, `_sigil()`)
3. Type→sigil mapping (`_sigil(typ: Type) -> str`)
4. Module emission (`_emit_module()`, `_emit_constants()`, `_emit_package()`, `_emit_functions()`)
5. Statement dispatch (`_emit_stmt()` with match/case to specific handlers)
6. Expression dispatch (`_expr()` with match/case to specific handlers)
7. LValue emission (`_lvalue()`)

## Type Mapping

Perl is dynamically typed; types map to runtime representations:

| IR Type | Perl Representation | Notes |
|---------|---------------------|-------|
| `Primitive("string")` | scalar | Native |
| `Primitive("int")` | scalar | Native (arbitrary precision) |
| `Primitive("bool")` | scalar | `1`/`0` or `!!` for coercion |
| `Primitive("float")` | scalar | Native |
| `Primitive("byte")` | scalar | `ord()`/`chr()` for conversion |
| `Primitive("rune")` | scalar | Single character string |
| `Slice(T)` | arrayref `[]` | `@$ref` to dereference |
| `Map(K, V)` | hashref `{}` | `%$ref` to dereference |
| `Set(T)` | hashref `{}` | Keys only, values = 1 |
| `Tuple(...)` | arrayref `[]` | Access via `$ref->[0]`, `$ref->[1]` |
| `Optional(T)` | scalar | `undef` for None |
| `StructRef(X)` | blessed hashref | `bless {}, 'X'` |
| `InterfaceRef(X)` | scalar | Duck typing, no prefix |
| `FuncType` | coderef | `sub { ... }` or `\&name` |

## Key Perl Features to Use

- **Signatures**: `sub foo ($a, $b) { ... }` — native in 5.36+
- **References**: `\@array`, `\%hash`, `$ref->method()` for OO
- **Autovivification**: Arrays/hashes grow automatically
- **Duck typing**: No interface declarations needed
- **Ternary**: `$cond ? $a : $b` — native
- **Range**: `for my $i (0 .. $n-1)` — native
- **Pattern matching**: `given`/`when` or chained `if`/`elsif`
- **Exception handling**: `eval { ... }; if ($@) { ... }`

## Sigil Rules

| Context | Sigil | Example |
|---------|-------|---------|
| Scalar variable | `$` | `$x`, `$name` |
| Array variable | `@` | `@items` |
| Hash variable | `%` | `%lookup` |
| Array element | `$` | `$items[0]`, `$ref->[0]` |
| Hash element | `$` | `$lookup{key}`, `$ref->{key}` |
| Subroutine | `&` | `&func` (rarely needed) |
| Coderef call | | `$coderef->()` |

For IR, always use references for collections:
- `Slice` → `$items = [...]` (arrayref, access via `$items->[$i]`)
- `Map` → `$lookup = {...}` (hashref, access via `$lookup->{$k}`)

## OO Strategy

Use simple blessed hashrefs (no Moo/Moose dependency):

```perl
package Foo;
use strict;
use warnings;

sub new ($class, $x, $y) {
    return bless { x => $x, y => $y }, $class;
}

sub x ($self) { $self->{x} }
sub set_x ($self, $val) { $self->{x} = $val }
```

Alternatively, generate accessors inline:
```perl
sub x ($self, $val = undef) {
    $self->{x} = $val if defined $val;
    return $self->{x};
}
```

## Files to Modify

### `/Users/lily/source/Parable/transpiler/src/tongues.py`

Add import (after line 15):
```python
from .backend.perl import PerlBackend
```

Update BACKENDS dict:
```python
BACKENDS: dict[str, type[...]] = {
    "go": GoBackend,
    "java": JavaBackend,
    "py": PythonBackend,
    "ts": TsBackend,
    "pl": PerlBackend,
}
```

Update USAGE string:
```python
--target TARGET   Output language: go, java, py, ts, pl (default: go)
```

### `/Users/lily/source/Parable/transpiler/tests/run_codegen_tests.py`

Add import:
```python
from src.backend.perl import PerlBackend
```

Update BACKENDS dict:
```python
BACKENDS: dict[str, type[...]] = {
    "go": GoBackend,
    "java": JavaBackend,
    "python": PythonBackend,
    "ts": TsBackend,
    "pl": PerlBackend,
}
```

### `/Users/lily/source/Parable/transpiler/tests/codegen/basic.tests`

Add `--- pl` sections to each test case with expected Perl output.

## Implementation Order

1. **Core infrastructure** (~80 lines)
   - Imports, reserved words, naming helpers
   - `PerlBackend` class with `__init__`, `emit`, `_line`
   - Sigil/reference helper functions

2. **Module structure** (~120 lines)
   - `_emit_module()` - `use` statements, `use strict; use warnings; use feature 'signatures';`
   - `_emit_constants()` - `use constant` or `Readonly`
   - `_emit_package()` - `package Name;` with constructor and accessors
   - `_emit_enum()` - constants or hash mapping

3. **Statements** (~250 lines)
   - Simple: VarDecl, Assign, TupleAssign, OpAssign, Return, ExprStmt, NoOp
   - Control: If, While, ForRange, ForClassic, Break (`last`), Continue (`next`), Block
   - Complex: TryCatch (`eval`/`$@`), Raise (`die`), SoftFail, TypeSwitch, Match

4. **Expressions** (~350 lines)
   - Literals: IntLit, FloatLit, StringLit, CharLit, BoolLit, NilLit (`undef`)
   - Access: Var, FieldAccess (`$obj->{field}`), Index (`$ref->[$i]`), SliceExpr
   - Calls: Call, MethodCall (`$obj->method()`), StaticCall (`Package::func()`)
   - Operators: BinaryOp, UnaryOp, Ternary
   - Types: Cast, TypeAssert (`ref($x) eq 'Type'`), IsType, IsNil (`!defined`), Truthy
   - Collections: Len (`scalar @$ref` / `keys %$ref`), MakeSlice, MakeMap, SliceLit, MapLit, SetLit, TupleLit, StructLit
   - Strings: StringConcat (`.`), StringFormat (`sprintf`), ParseInt, IntToStr, CharClassify, TrimChars, CharAt (`substr`), Substring

5. **LValues** (~30 lines)
   - VarLV, FieldLV, IndexLV, DerefLV

6. **Registration & tests**
   - Update tongues.py and run_codegen_tests.py
   - Add `--- pl` sections to test files

## Perl-Specific Mappings

| IR Construct | Perl Output |
|--------------|-------------|
| `BinaryOp(+, a, b)` (int) | `$a + $b` |
| `BinaryOp(+, a, b)` (str) | `$a . $b` |
| `BinaryOp(==, a, b)` (int) | `$a == $b` |
| `BinaryOp(==, a, b)` (str) | `$a eq $b` |
| `Len(slice)` | `scalar @$slice` |
| `Len(map)` | `scalar keys %$map` |
| `Len(str)` | `length($s)` |
| `Index(slice, i)` | `$slice->[$i]` |
| `Index(map, k)` | `$map->{$k}` |
| `Index(str, i)` | `substr($s, $i, 1)` |
| `SliceExpr(s, a, b)` | `substr($s, $a, $b - $a)` (str) |
| `SliceExpr(arr, a, b)` | `[@$arr[$a .. $b-1]]` |
| `IsNil(x)` | `!defined($x)` |
| `Truthy(x)` (str/list) | `$x` (Perl truthiness) |
| `TryCatch` | `eval { ... }; if ($@) { ... }` |
| `Raise(msg)` | `die $msg` |
| `Break` | `last` |
| `Continue` | `next` |
| `ForRange(i, 0, n)` | `for my $i (0 .. $n-1)` |
| `Print(x)` | `say $x` or `print $x` |
| `ReadLine` | `my $line = <STDIN>; chomp $line;` |
| `ReadAll` | `do { local $/; <STDIN> }` |
| `Args` | `@ARGV` |
| `GetEnv(name)` | `$ENV{$name}` |

## String vs Numeric Operators

Perl requires different operators for string vs numeric comparison:

| Operation | Numeric | String |
|-----------|---------|--------|
| Equal | `==` | `eq` |
| Not equal | `!=` | `ne` |
| Less than | `<` | `lt` |
| Greater than | `>` | `gt` |
| Less/equal | `<=` | `le` |
| Greater/equal | `>=` | `ge` |
| Compare | `<=>` | `cmp` |

Backend must check IR types to emit correct operator.

## What NOT to Do

- **No type override tables** - IR has complete type info
- **No domain-specific names** - no hardcoded class names
- **No Moose/Moo** - keep dependency-free with blessed refs
- **No indirect object syntax** - always `$obj->method()`, never `method $obj`

## Verification

```bash
cd /Users/lily/source/Parable/transpiler

# Run codegen tests
python3 tests/run_codegen_tests.py tests/codegen/

# Manual test
echo 'def add(a: int, b: int) -> int:
    return a + b' | python3 -m src.tongues --target pl
```

Expected output for simple function:
```perl
use strict;
use warnings;
use feature 'signatures';
no warnings 'experimental::signatures';

sub add ($a, $b) {
    return $a + $b;
}
```

Expected output for class:
```perl
use strict;
use warnings;
use feature 'signatures';
no warnings 'experimental::signatures';

package Point;

sub new ($class, $x, $y) {
    return bless { x => $x, y => $y }, $class;
}

sub x ($self) { $self->{x} }
sub y ($self) { $self->{y} }

sub distance ($self, $other) {
    my $dx = $self->{x} - $other->{x};
    my $dy = $self->{y} - $other->{y};
    return sqrt($dx * $dx + $dy * $dy);
}

1;
```

## Estimated Size

~800-900 lines (smaller than Go/Java due to dynamic typing, no type declarations, simple OO)
