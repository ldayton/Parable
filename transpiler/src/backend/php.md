# PHP Backend Implementation Plan

## Goal
Create a clean, generic PHP backend for the Tongues transpiler that:
- Uses only IR type information (no type override tables)
- Has no domain-specific knowledge (no hardcoded interface names, prefixes, etc.)
- Follows PHP idioms (PascalCase classes, camelCase methods, $variables)
- Targets PHP 8.1+ (union types, enums, readonly, match expressions)

## Files to Create

### `/Users/lily/source/Parable/transpiler/src/backend/php.py`

```python
class PhpBackend:
    def __init__(self) -> None:
        self.indent = 0
        self.lines: list[str] = []
        self.receiver_name: str | None = None

    def emit(self, module: Module) -> str:
        """Emit complete PHP source from IR Module."""
```

**Structure:**
1. Reserved word handling (`_PHP_RESERVED` frozenset, `_` suffix for escaping)
2. Naming helpers (`_pascal()`, `_camel()`, `_safe_name()`)
3. Type mapping (`_type(typ: Type) -> str`)
4. Module emission (`_emit_module()`, `_emit_constants()`, `_emit_interface()`, `_emit_struct()`, `_emit_functions()`)
5. Statement dispatch (`_emit_stmt()` with match/case to specific handlers)
6. Expression dispatch (`_expr()` with match/case to specific handlers)
7. LValue emission (`_lvalue()`)

## Type Mapping

| IR Type | PHP Type |
|---------|----------|
| `Primitive("string")` | `string` |
| `Primitive("int")` | `int` |
| `Primitive("bool")` | `bool` |
| `Primitive("float")` | `float` |
| `Primitive("byte")` | `int` |
| `Primitive("rune")` | `string` |
| `Slice(T)` | `array` (docblock: `T[]`) |
| `Map(K, V)` | `array` (docblock: `array<K, V>`) |
| `Set(T)` | `array` (keys as set members) |
| `Tuple(...)` | `array` (docblock: `array{T1, T2, ...}`) |
| `Optional(T)` | `?T` (nullable) |
| `StructRef(X)` | `X` |
| `InterfaceRef(X)` | `X` (no prefix convention) |
| `FuncType` | `Closure` or `callable` |

## Key PHP Features to Use

- **Match expressions**: `match ($x) { Foo::class => ..., ... }` (PHP 8.0+)
- **Union types**: `int|string` (PHP 8.0+)
- **Nullable types**: `?string` for optional
- **Enums**: `enum Foo { case Bar; }` (PHP 8.1+)
- **Readonly properties**: `public readonly int $x` (PHP 8.1+)
- **Constructor promotion**: `public function __construct(public int $x)` (PHP 8.0+)
- **Named arguments**: `foo(name: $value)` (PHP 8.0+)
- **Ternary**: `$cond ? $a : $b` - native, no IIFE
- **Null coalescing**: `$x ?? $default`
- **try/catch**: Direct mapping

## PHP-Specific Considerations

### No Generics
PHP lacks generics. Use docblocks for IDE/static analysis support:
```php
/** @var array<string, Node> */
private array $nodes = [];

/** @param list<int> $items */
public function process(array $items): void
```

### Arrays as Lists and Maps
PHP uses `array` for both sequences and associative arrays:
- Lists: `[1, 2, 3]` with integer keys
- Maps: `['a' => 1, 'b' => 2]` with string/int keys
- Sets: `['a' => true, 'b' => true]` (keys as members)

### Tuples as Arrays
No native tuples; use indexed arrays with docblocks:
```php
/** @return array{int, string} */
public function getPair(): array {
    return [42, "hello"];
}
[$a, $b] = $this->getPair();
```

## Files to Modify

### `/Users/lily/source/Parable/transpiler/src/tongues.py`

Add import (after existing backend imports):
```python
from .backend.php import PhpBackend
```

Update BACKENDS dict:
```python
BACKENDS: dict[str, type[...]] = {
    "go": GoBackend,
    "java": JavaBackend,
    "py": PythonBackend,
    "ts": TsBackend,
    "cs": CSharpBackend,
    "php": PhpBackend,
}
```

Update USAGE string:
```python
--target TARGET   Output language: go, java, py, ts, cs, php (default: go)
```

### `/Users/lily/source/Parable/transpiler/tests/run_codegen_tests.py`

Add import (after existing backend imports):
```python
from src.backend.php import PhpBackend
```

Update BACKENDS dict:
```python
BACKENDS: dict[str, type[...]] = {
    "go": GoBackend,
    "java": JavaBackend,
    "python": PythonBackend,
    "ts": TsBackend,
    "cs": CSharpBackend,
    "php": PhpBackend,
}
```

### `/Users/lily/source/Parable/transpiler/tests/codegen/basic.tests`

Add `--- php` sections to each test case with expected PHP output.

## Implementation Order

1. **Core infrastructure** (~100 lines)
   - Imports, reserved words, naming helpers
   - `PhpBackend` class with `__init__`, `emit`, `_line`
   - `_type()` method for all IR types

2. **Module structure** (~150 lines)
   - `_emit_module()` - `<?php declare(strict_types=1);`
   - `_emit_constants()` - `const` or `define()`
   - `_emit_interface()` - PHP interface with methods
   - `_emit_enum()` - PHP 8.1 enum
   - `_emit_struct()` - class with properties, constructor promotion

3. **Statements** (~300 lines)
   - Simple: VarDecl, Assign, TupleAssign, OpAssign, Return, ExprStmt, NoOp
   - Control: If, While, ForRange, ForClassic, Break, Continue, Block
   - Complex: TryCatch, Raise, SoftFail, TypeSwitch, Match

4. **Expressions** (~400 lines)
   - Literals: IntLit, FloatLit, StringLit, CharLit, BoolLit, NilLit
   - Access: Var, FieldAccess, Index, SliceExpr
   - Calls: Call, MethodCall, StaticCall
   - Operators: BinaryOp, UnaryOp, Ternary
   - Types: Cast, TypeAssert, IsType, IsNil, Truthy
   - Collections: Len, MakeSlice, MakeMap, SliceLit, MapLit, SetLit, TupleLit, StructLit
   - Strings: StringConcat, StringFormat, ParseInt, IntToStr, CharClassify, TrimChars, CharAt, Substring

5. **LValues** (~30 lines)
   - VarLV, FieldLV, IndexLV, DerefLV

6. **Registration & tests**
   - Update tongues.py and run_codegen_tests.py
   - Add `--- php` sections to test files

## Expression Mapping

| IR Expression | PHP Output |
|---------------|------------|
| `Var("x")` | `$x` |
| `FieldAccess(obj, "name")` | `$obj->name` |
| `Index(arr, i)` | `$arr[$i]` |
| `MethodCall(obj, "foo", args)` | `$obj->foo($args)` |
| `StaticCall("Foo", "bar", args)` | `Foo::bar($args)` |
| `Call("func", args)` | `func($args)` |
| `BinaryOp("+", a, b)` | `$a + $b` |
| `BinaryOp("==", a, b)` | `$a === $b` (strict equality) |
| `IsNil(x)` | `$x === null` |
| `IsType(x, T)` | `$x instanceof T` |
| `Len(x)` | `count($x)` or `strlen($x)` |
| `StringConcat(parts)` | `$a . $b . $c` |
| `StringFormat(fmt, args)` | `sprintf($fmt, ...$args)` |
| `CharAt(s, i)` | `$s[$i]` or `mb_substr($s, $i, 1)` |
| `Substring(s, a, b)` | `substr($s, $a, $b - $a)` |
| `ParseInt(s)` | `(int)$s` or `intval($s)` |
| `IntToStr(n)` | `(string)$n` or `strval($n)` |
| `Ternary(c, t, f)` | `$c ? $t : $f` |
| `SliceLit(elems)` | `[$e1, $e2, ...]` |
| `MapLit(pairs)` | `[$k1 => $v1, ...]` |
| `StructLit(T, fields)` | `new T($f1, $f2, ...)` |

## Statement Mapping

| IR Statement | PHP Output |
|--------------|------------|
| `VarDecl(x, T, val)` | `$x = $val;` |
| `Assign(lv, val)` | `$lv = $val;` |
| `TupleAssign([a,b], val)` | `[$a, $b] = $val;` |
| `If(cond, then, else)` | `if ($cond) { ... } else { ... }` |
| `While(cond, body)` | `while ($cond) { ... }` |
| `ForRange(x, iter, body)` | `foreach ($iter as $x) { ... }` |
| `ForClassic(i, start, end, body)` | `for ($i = $start; $i < $end; $i++) { ... }` |
| `TryCatch(try, exc, var, catch)` | `try { ... } catch (Exc $var) { ... }` |
| `Raise(exc)` | `throw $exc;` |
| `Return(val)` | `return $val;` |
| `TypeSwitch(val, cases)` | `match (true) { $val instanceof A => ..., ... }` |

## Character/String Handling

PHP strings are byte sequences by default. For Unicode:
- Use `mb_*` functions for multibyte support
- `mb_substr($s, $i, 1)` for character access
- `mb_strlen($s)` for character count
- `strlen($s)` for byte count

## What NOT to Do

- **No type override tables** - IR has complete type info
- **No domain-specific names** - no "Node", "ArithVar", "ParseError" hardcoding
- **No frontend compensation** - if IR is incomplete, that's a frontend bug
- **No helper functions** - use PHP's native string/array methods

## Verification

```bash
cd /Users/lily/source/Parable/transpiler

# Run codegen tests
python3 tests/run_codegen_tests.py tests/codegen/

# Manual test
echo 'def add(a: int, b: int) -> int:
    return a + b' | python3 -m src.tongues --target php
```

Expected output for simple function:
```php
<?php

declare(strict_types=1);

function add(int $a, int $b): int
{
    return $a + $b;
}
```

## Estimated Size

~900-1100 lines (smaller than Go/Java due to simpler type system, native match, ternary)

## Known Issues / Fix Plan

### Tuple Field Access Bug

**Problem:** Tests fail with `Attempt to read property "f0" on array` because tuple field access generates `$pair->f0` instead of `$pair[0]`.

**Root Cause:** In `php.py` line 680, the check uses lowercase `"f"`:
```python
if isinstance(obj_type, Tuple) and field.startswith("f") and field[1:].isdigit():
```

But the IR uses uppercase `"F0"`, `"F1"`, etc. All other backends use uppercase `"F"`.

**Fix:** Change line 680 from `field.startswith("f")` to `field.startswith("F")`.

**File:** `transpiler/src/backend/php.py` (line 680)

**Verification:**
```bash
just backend-test php
```
