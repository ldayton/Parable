# Parable Transpiler IR

Intermediate representation for Python → {Go, JS, Rust, C} transpilation.

```
parable.py → [Python AST] → Frontend → [IR] → Backend → target code
```

**Frontend** (one implementation): Type inference, symbol resolution, scope analysis, ownership analysis.

**Backends** (per target): Pure syntax emission, ~500-800 lines each.

## Types

### Primitives

```
Primitive { kind: "string" | "int" | "bool" | "float" | "byte" | "rune" | "void" }
```

| IR       | Go        | JS        | Rust     | C               |
| -------- | --------- | --------- | -------- | --------------- |
| `int`    | `int`     | `number`  | `i64`    | `int64_t`       |
| `float`  | `float64` | `number`  | `f64`    | `double`        |
| `bool`   | `bool`    | `boolean` | `bool`   | `bool`          |
| `string` | `string`  | `string`  | `String` | `Str` (ptr+len) |
| `byte`   | `byte`    | `number`  | `u8`     | `uint8_t`       |
| `rune`   | `rune`    | `number`  | `char`   | `int32_t`       |
| `void`   | —         | `void`    | `()`     | `void`          |

### Collections

```
Slice { element: Type }
```

| IR         | Go    | JS         | Rust     | C                                      |
| ---------- | ----- | ---------- | -------- | -------------------------------------- |
| `Slice(T)` | `[]T` | `Array<T>` | `Vec<T>` | `struct { T *data; size_t len, cap; }` |

```
Array { element: Type, size: int }
```

| IR            | Go     | JS         | Rust     | C      |
| ------------- | ------ | ---------- | -------- | ------ |
| `Array(T, N)` | `[N]T` | `Array<T>` | `[T; N]` | `T[N]` |

```
Map { key: Type, value: Type }
```

| IR         | Go        | JS          | Rust           | C              |
| ---------- | --------- | ----------- | -------------- | -------------- |
| `Map(K,V)` | `map[K]V` | `Map<K, V>` | `HashMap<K,V>` | generated hash |

### Pointers and Optionals

```
Pointer { target: Type, owned: bool }
```

| IR                        | Go   | JS  | Rust     | C              |
| ------------------------- | ---- | --- | -------- | -------------- |
| `Pointer(T, owned=true)`  | `*T` | ref | `Box<T>` | `T*` (owns)    |
| `Pointer(T, owned=false)` | `*T` | ref | `&'a T`  | `T*` (borrows) |

```
Optional { inner: Type }
```

| IR            | Go         | JS          | Rust        | C           |
| ------------- | ---------- | ----------- | ----------- | ----------- |
| `Optional(T)` | `*T` / nil | `T \| null` | `Option<T>` | `T*` + NULL |

### Type References

```
StructRef { name: string }          // Reference to defined struct
Interface { name: string }          // Dynamic dispatch (Go interface, Rust dyn Trait)
Union { variants: [Type] }          // Sum type (Go interface, Rust enum, C tagged union)
```

### Functions

```
FuncType { params: [Type], ret: Type, captures: bool }
```

| IR                              | Go          | JS         | Rust           | C               |
| ------------------------------- | ----------- | ---------- | -------------- | --------------- |
| `FuncType(..., captures=false)` | `func(...)` | `function` | `fn(...)`      | `T (*)(…)`      |
| `FuncType(..., captures=true)`  | `func(...)` | `function` | `impl Fn(...)` | struct + fn ptr |

### Strings

```
StringSlice                         // Borrowed immutable view
```

| IR            | Go       | JS       | Rust   | C             |
| ------------- | -------- | -------- | ------ | ------------- |
| `StringSlice` | `string` | `string` | `&str` | `const char*` |

## Source Locations

All nodes carry source position:

```
Loc { line: int, col: int, end_line: int, end_col: int }
```

Line is 1-indexed, column is 0-indexed. Enables error messages, source maps, IDE integration.

## Declarations

### Module

```
Module {
    name: string
    structs: [Struct]
    interfaces: [InterfaceDef]
    functions: [Function]
    constants: [Constant]
}
```

### Struct

```
Struct {
    name: string
    fields: [Field]
    methods: [Function]
    implements: [string]        // interface names
}

Field { name: string, typ: Type, default: Expr? }
```

### Interface

```
InterfaceDef {
    name: string
    methods: [MethodSig]
}

MethodSig { name: string, params: [Param], ret: Type }
```

### Function

```
Function {
    name: string
    params: [Param]
    ret: Type
    body: [Stmt]
    receiver: Receiver?         // present for methods
    fallible: bool              // can raise ParseError
}

Receiver {
    name: string                // "self", "p", etc.
    typ: StructRef
    mutable: bool               // Rust: &mut self
    pointer: bool               // Go: *T receiver
}

Param {
    name: string
    typ: Type
    default: Expr?
    mutable: bool               // Rust: mut
}
```

### Constant

```
Constant { name: string, typ: Type, value: Expr }
```

## Statements

All statements carry `loc: Loc`.

### Variables

```
VarDecl { name: string, typ: Type, value: Expr?, mutable: bool }
```

| IR              | Go           | JS      | Rust      | C            |
| --------------- | ------------ | ------- | --------- | ------------ |
| `mutable=true`  | `var` / `:=` | `let`   | `let mut` | no qualifier |
| `mutable=false` | `const`      | `const` | `let`     | `const`      |

### Assignment

```
Assign { target: LValue, value: Expr }
OpAssign { target: LValue, op: string, value: Expr }    // +=, -=, *=, etc.
```

### Control Flow

```
If {
    cond: Expr
    then_body: [Stmt]
    else_body: [Stmt]
    init: VarDecl?              // Go: if x := ...; cond { }
}

TypeSwitch {
    expr: Expr
    binding: string             // variable name in each case
    cases: [TypeCase]
    default: [Stmt]
}

TypeCase { typ: Type, body: [Stmt] }

Match {
    expr: Expr
    cases: [MatchCase]
    default: [Stmt]
}

MatchCase { patterns: [Expr], body: [Stmt] }
```

`TypeSwitch` translates `isinstance` chains:

| IR           | Go                | JS                          | Rust                   | C                 |
| ------------ | ----------------- | --------------------------- | ---------------------- | ----------------- |
| `TypeSwitch` | `switch x.(type)` | `if (x instanceof T)` chain | `match x { T => ... }` | `switch (x->tag)` |

### Loops

```
ForRange {
    index: string?              // None if unused
    value: string?
    iterable: Expr
    body: [Stmt]
}

ForClassic {
    init: Stmt?
    cond: Expr?
    post: Stmt?
    body: [Stmt]
}

While { cond: Expr, body: [Stmt] }

Break { label: string? }
Continue { label: string? }
```

### Error Handling

**Two failure modes:**
- **Soft failure**: Returns `None` — "try alternative parsing"
- **Hard failure**: Raises exception — "committed and failed"

Exceptions are NOT used for control flow. Most propagate to top; few backtracking points catch them.

**Error type:**
```
ParseError { message: string, pos: int, line: int? }
MatchedPairError extends ParseError   // unclosed construct at EOF
```

**Fallible functions** (marked with `fallible: bool` on Function):
```
Raise { error_type: string, message: Expr, pos: Expr }
```

| IR      | Go           | JS      | Rust                     | C                 |
| ------- | ------------ | ------- | ------------------------ | ----------------- |
| `Raise` | `panic(...)` | `throw` | `return Err(ParseError)` | `longjmp` or goto |

**Calling fallible functions:**

Bare calls propagate errors automatically:
| Context | Go           | JS           | Rust      | C            |
| ------- | ------------ | ------------ | --------- | ------------ |
| Default | panic floats | throw floats | `call()?` | check + goto |

**Backtracking** (rare):
```
TryCatch {
    body: [Stmt]
    catch_var: string?          // None if error ignored
    catch_body: [Stmt]
    reraise: bool               // catch cleans up then re-raises
}
```

| IR         | Go              | JS          | Rust                      | C                |
| ---------- | --------------- | ----------- | ------------------------- | ---------------- |
| `TryCatch` | `defer/recover` | `try/catch` | `match call() { Ok/Err }` | `setjmp/longjmp` |

**Soft failure** (return None to signal "try alternative"):
```
SoftFail { }                    // return None / (None, "")
```

| IR         | Go           | JS            | Rust          | C             |
| ---------- | ------------ | ------------- | ------------- | ------------- |
| `SoftFail` | `return nil` | `return null` | `return None` | `return NULL` |

### Returns and Blocks

```
Return { value: Expr? }
ExprStmt { expr: Expr }                 // expression used as statement
Block { body: [Stmt] }                  // scoped statement group
```

## Expressions

All expressions carry `typ: Type` and `loc: Loc`.

### Literals

```
IntLit { value: int }
FloatLit { value: float }
StringLit { value: string }
BoolLit { value: bool }
NilLit { }                              // nil/null/None
```

### Access

```
Var { name: string }

FieldAccess {
    obj: Expr
    field: string
    through_pointer: bool       // Go auto-deref
}

Index {
    obj: Expr
    index: Expr
    bounds_check: bool          // C can skip
    returns_optional: bool      // Go map returns (v, ok)
}

SliceExpr { obj: Expr, low: Expr?, high: Expr? }
```

### Calls

```
Call { func: string, args: [Expr] }

MethodCall {
    obj: Expr
    method: string
    args: [Expr]
    receiver_type: Type         // resolved by frontend
}

StaticCall { on_type: Type, method: string, args: [Expr] }
```

### Operators

```
BinaryOp { op: string, left: Expr, right: Expr }
UnaryOp { op: string, operand: Expr }
Ternary { cond: Expr, then_expr: Expr, else_expr: Expr }
```

Go lacks ternary; backend emits IIFE: `func() T { if cond { return a } return b }()`

### Type Operations

```
Cast { expr: Expr, to_type: Type }
TypeAssert { expr: Expr, asserted: Type, safe: bool }
IsType { expr: Expr, tested_type: Type }
IsNil { expr: Expr, negated: bool }
Len { expr: Expr }
```

`IsNil` is explicit (not `BinaryOp("==", x, NilLit)`):

| IR      | Go         | JS           | Rust          | C           |
| ------- | ---------- | ------------ | ------------- | ----------- |
| `IsNil` | `x == nil` | `x === null` | `x.is_none()` | `x == NULL` |

### Allocation

```
MakeSlice { element_type: Type, length: Expr?, capacity: Expr? }
MakeMap { key_type: Type, value_type: Type }
SliceLit { element_type: Type, elements: [Expr] }
MapLit { key_type: Type, value_type: Type, entries: [(Expr, Expr)] }
StructLit { struct_name: string, fields: {string: Expr} }
```

### Strings

```
StringConcat { parts: [Expr] }
StringFormat { template: string, args: [Expr] }
```

| IR             | Go            | JS               | Rust      | C          |
| -------------- | ------------- | ---------------- | --------- | ---------- |
| `StringConcat` | `+`           | `+`              | `format!` | `snprintf` |
| `StringFormat` | `fmt.Sprintf` | template literal | `format!` | `snprintf` |

### Closures

```
Lambda {
    params: [Param]
    body: [Stmt]
    captures: [Capture]
}

Capture { name: string, by_ref: bool }
```

Explicit captures required for Rust (`move` keyword) and C (environment struct).

## LValues

Assignment targets:

```
VarLV { name: string }
FieldLV { obj: Expr, field: string }
IndexLV { obj: Expr, index: Expr }
DerefLV { ptr: Expr }
```

## Frontend Responsibilities

The frontend (Python AST → IR) performs all analysis:

1. **Type inference** — Resolve types from annotations and usage
2. **Symbol resolution** — Build table of structs, methods, functions
3. **Scope analysis** — Variable lifetimes, hoisting requirements
4. **Ownership analysis** — Mark `Pointer.owned` for Rust/C
5. **Method resolution** — Fill `MethodCall.receiver_type`
6. **Nil analysis** — `x is None` → `IsNil`
7. **Truthiness** — `if items:` → `if len(items) > 0`
8. **Type narrowing** — `isinstance` → `TypeSwitch`
9. **Fallibility analysis** — Mark functions containing `raise` as `fallible=true`

## Backend Responsibilities

Backends (IR → target) handle only syntax:

1. **Name conversion** — snake_case → camelCase/PascalCase
2. **Syntax emission** — IR nodes → target syntax
3. **Error propagation** — Fallible calls: Go uses panic, Rust uses `?`, JS uses throw
4. **Idioms** — Target-specific patterns (defer/recover, try/catch)
5. **Formatting** — Indentation, line breaks

## Memory Strategy

### Rust Backend

Arena allocation with single lifetime `'arena` for all AST nodes:

```rust
struct Command<'arena> {
    words: Vec<'arena, &'arena Word<'arena>>,
}
```

Uses `bumpalo::Bump`. Sidesteps ownership inference.

### C Backend

Arena allocation with ptr+len strings:

```c
typedef struct { const char *data; size_t len; } Str;
typedef struct { char *base; char *ptr; size_t cap; } Arena;

void *arena_alloc(Arena *a, size_t size);
```

No per-node `free()`. Single `arena_free()` at end.

## Truthiness Semantics

Python's `if x:` has type-dependent meaning. Parable restricts this to four unambiguous patterns:

| Type        | Pattern     | Meaning      | IR Transform                       |
| ----------- | ----------- | ------------ | ---------------------------------- |
| `bool`      | `if flag:`  | Boolean test | None (pass through)                |
| `T \| None` | `if node:`  | Not None     | `IsNil(node, negated=true)`        |
| `list[T]`   | `if items:` | Non-empty    | `BinaryOp(">", Len(items), 0)`     |
| `str`       | `if s:`     | Non-empty    | `BinaryOp("!=", s, StringLit(""))` |

**Constraint:** No variable may have a type where truthiness is ambiguous (e.g., `list[T] | None` where `if x:` could mean "not None" or "non-empty"). The frontend infers types and selects the appropriate transform. Style enforcement requires explicit `is not None` checks for Optional parameters.

## Union Types

All unions are **closed** (fixed variants) and discriminated via `.kind` string field.

```
Union { name: string, variants: [StructRef] }
```

| IR      | Go                     | JS             | Rust   | C            |
| ------- | ---------------------- | -------------- | ------ | ------------ |
| `Union` | interface + type switch | class + `kind` | `enum` | tagged union |

## Ownership Model

AST is a **strict tree**: parent→child only, no cycles, no shared nodes, no back-references.

Nodes are immutable after construction. All nodes live until parse completion.

Arena allocation with single lifetime `'arena`. No reference counting needed.

## String Handling

Two string representations:

```
StringRef { start: u32, end: u32 }    // Byte range into source buffer
ArenaStr { ptr: *const u8, len: u32 } // Arena-allocated
```

| Field type | Representation | Example |
| ---------- | -------------- | ------- |
| Parameter names, delimiters | `StringRef` | `ParamExpansion.param`, `HereDoc.delimiter` |
| Constructed content | `ArenaStr` | `Word.value`, `AnsiCQuote.content` |
| Operator literals | `&'static str` | `Operator.op` |

Input buffer must outlive AST, or copy referenced ranges into arena at parse end.
