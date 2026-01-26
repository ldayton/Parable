# Parable Transpiler IR

Intermediate representation for Python → {Go, TS, Rust, C} transpilation.

```
parable.py → [Python AST] → Frontend → [IR] → Backend → target code
```

**Frontend** (one implementation): Type inference, symbol resolution, scope analysis, ownership analysis.

**Backends** (per target): Pure syntax emission, ~500-800 lines each.

**TypeScript strategy**: Backend emits `.ts` files; `tsc` produces `.js` + `.d.ts`. No separate JS backend needed.

## Source Language Subset

parable.py uses a restricted Python subset designed for straightforward transpilation. The style checker (`check_style.py`) enforces these constraints.

### Banned Constructs

| Category              | Banned                                                    | Use Instead                                       |
| --------------------- | --------------------------------------------------------- | ------------------------------------------------- |
| **Generators**        | `yield`, `yield from`, `(x for x in y)`                   | Return list or use callback                       |
| **Async**             | `async def`, `await`, `async for`, `async with`           | Synchronous code only                             |
| **Closures**          | `nonlocal`, `global`, `lambda`, nested functions          | Pass as parameter, module-level function          |
| **Metaprogramming**   | `@decorator`, `getattr`, `hasattr`, `type()`, `__class__` | Direct calls, explicit field access, `isinstance` |
| **OOP patterns**      | `@staticmethod`, `@classmethod`, `@property`              | Module-level function, explicit getter            |
| **Pattern matching**  | `match`/`case`                                            | `if`/`elif` chain                                 |
| **Context managers**  | `with` statement                                          | `try`/`finally`                                   |
| **Python idioms**     | `a < b < c`, `x or []`, `x ** 2`, `pow()`                 | Explicit comparisons, `if x is None`, multiply    |
| **Iteration helpers** | `all`, `any`                                              | Explicit loop with early return                   |
| **Assignment**        | `del`, tuple unpack from variable, mutable default        | Reassign, unpack from call, `None` default        |
| **Call spreading**    | `f(*args)`, `f(**kwargs)`                                 | Pass arguments explicitly                         |
| **Inheritance**       | Multiple inheritance, nested classes                      | Single inheritance, module-level classes          |
| **Dunder methods**    | `__str__`, `__eq__`, etc.                                 | Only `__init__`, `__new__`, `__repr__` allowed    |
| **Exceptions**        | Bare `except:`, `assert`                                  | `except ExceptionType:`, `if not x: raise`        |
| **Identity**          | `is`/`is not` with non-None                               | `==` (except `x is None`)                         |
| **Imports**           | Any except `__future__`, `typing`, `collections.abc`      | Self-contained code                               |

### Required Annotations

All functions must have return type and parameter type annotations. Collection types must be parameterized.

```python
# Required
def parse(source: str, pos: int) -> tuple[Node | None, str]: ...

# Banned (missing types, bare collections)
def parse(source, pos): ...
def get_items() -> list: ...
```

### Allowed Constructs

The subset includes: classes, methods, functions, `if`/`elif`/`else`, `while`, `for x in collection`, `try`/`except`/`finally`, `raise`, slicing `a[x:y]` and `a[::step]`, negative indexing `lst[-1]`, `isinstance`, `len`, string/list/dict/set operations, `Union` types, `| None` optionals, f-strings (limited), list/dict/set comprehensions, `:=` walrus operator, `enumerate`, `zip`, `reversed`, `//` floor division.

## Source Code Properties

Beyond style rules, parable.py has structural properties relevant to transpilation:

### AST Structure
- **Strict tree**: Parent→child references only. No cycles, no shared nodes, no back-references.
- **Immutable after construction**: Nodes are built once and never modified.
- **Single inheritance**: All AST nodes inherit from `Node`. No multiple inheritance.
- **Discriminated union**: Every node has `self.kind = "literal"` set in `__init__`.

### Type System
- **Explicit unions**: `ArithNode = Union[ArithNumber, ArithVar, ...]` defined at module level.
- **Optional via union**: `T | None` for nullable values.
- **No type aliases**: Types are used directly or via explicit `Union`.

### Control Flow
- **Type dispatch via `.kind`**: `if node.kind == "command":` pattern, not `isinstance`.
- **Error handling**: `raise ParseError(msg, pos)` / `raise MatchedPairError(msg, pos)`.
- **Soft failure**: Return `(None, "")` tuple to signal "try alternative".
- **No recursion limits**: Call depth bounded by input nesting, not problematic.

### Data Patterns
- **Two-phase returns**: `tuple[Node | None, str]` — parsed node plus raw text consumed.
- **String building**: `chars: list[str]` → `chars.append(ch)` → `"".join(chars)`.
- **State via attributes**: `self.pos`, `self.source`, `self._stack` — mutable instance state.
- **Enum-like constants**: `class TokenType:` with `EOF = 0`, `WORD = 1`, etc.

### What Does NOT Exist
- No lambdas or closures
- No decorators
- No metaclasses
- No descriptors or properties
- No `__getattr__` / `__setattr__` magic
- No multiple inheritance
- No abstract base classes (just convention)
- No external dependencies

## Types

### Primitives

```
Primitive { kind: "string" | "int" | "bool" | "float" | "byte" | "rune" | "void" }
```

| IR       | Go        | TS        | Rust     | C               |
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

| IR         | Go    | TS         | Rust     | C                                      |
| ---------- | ----- | ---------- | -------- | -------------------------------------- |
| `Slice(T)` | `[]T` | `Array<T>` | `Vec<T>` | `struct { T *data; size_t len, cap; }` |

```
Array { element: Type, size: int }
```

| IR            | Go     | TS         | Rust     | C      |
| ------------- | ------ | ---------- | -------- | ------ |
| `Array(T, N)` | `[N]T` | `Array<T>` | `[T; N]` | `T[N]` |

```
Map { key: Type, value: Type }
```

| IR         | Go        | TS          | Rust           | C              |
| ---------- | --------- | ----------- | -------------- | -------------- |
| `Map(K,V)` | `map[K]V` | `Map<K, V>` | `HashMap<K,V>` | generated hash |

```
Set { element: Type }
```

| IR       | Go           | TS       | Rust          | C              |
| -------- | ------------ | -------- | ------------- | -------------- |
| `Set(T)` | `map[T]bool` | `Set<T>` | `HashSet<T>`  | generated hash |

```
Tuple { elements: [Type] }
```

| IR             | Go           | TS           | Rust         | C                    |
| -------------- | ------------ | ------------ | ------------ | -------------------- |
| `Tuple(T1,T2)` | `(T1, T2)`   | `[T1, T2]`   | `(T1, T2)`   | struct or out-params |

Used for multi-value returns like `tuple[Node | None, str]`. Go emits multiple return values; other backends use native tuples.

### Pointers and Optionals

```
Pointer { target: Type, owned: bool }
```

| IR                        | Go   | TS  | Rust     | C              |
| ------------------------- | ---- | --- | -------- | -------------- |
| `Pointer(T, owned=true)`  | `*T` | ref | `Box<T>` | `T*` (owns)    |
| `Pointer(T, owned=false)` | `*T` | ref | `&'a T`  | `T*` (borrows) |

```
Optional { inner: Type }
```

| IR            | Go         | TS          | Rust        | C           |
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

| IR                              | Go          | TS         | Rust           | C               |
| ------------------------------- | ----------- | ---------- | -------------- | --------------- |
| `FuncType(..., captures=false)` | `func(...)` | `function` | `fn(...)`      | `T (*)(…)`      |
| `FuncType(..., captures=true)`  | `func(...)` | `function` | `impl Fn(...)` | struct + fn ptr |

### Strings

```
StringSlice                         // Borrowed immutable view
```

| IR            | Go       | TS       | Rust   | C             |
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
    doc: string?                // module docstring
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
    doc: string?                // class docstring
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
    doc: string?                // function/method docstring
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

**Default parameters:** Go lacks default arguments. Emission strategy by pattern:

| Pattern                  | Go Emission                 | Example                                             |
| ------------------------ | --------------------------- | --------------------------------------------------- |
| `bool = False`           | Omit; zero value is `false` | `func F(debug bool)`                                |
| `T \| None = None`       | Omit; zero value is `nil`   | `func F(opts *Options)`                             |
| Multiple optional        | Options struct              | `func F(opts FOptions)` with `FOptions{Field: val}` |
| Single trailing optional | Variadic                    | `func F(required int, opt ...string)`               |

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

| IR              | Go           | TS      | Rust      | C            |
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

| IR           | Go                | TS                          | Rust                   | C                 |
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

| IR      | Go           | TS      | Rust                     | C                 |
| ------- | ------------ | ------- | ------------------------ | ----------------- |
| `Raise` | `panic(...)` | `throw` | `return Err(ParseError)` | `longjmp` or goto |

**Calling fallible functions:**

Bare calls propagate errors automatically:
| Context | Go           | TS           | Rust      | C            |
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

| IR         | Go              | TS          | Rust                      | C                |
| ---------- | --------------- | ----------- | ------------------------- | ---------------- |
| `TryCatch` | `defer/recover` | `try/catch` | `match call() { Ok/Err }` | `setjmp/longjmp` |

**Soft failure** (return None to signal "try alternative"):
```
SoftFail { }                    // return None / (None, "")
```

| IR         | Go           | TS            | Rust          | C             |
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

| IR      | Go         | TS           | Rust          | C           |
| ------- | ---------- | ------------ | ------------- | ----------- |
| `IsNil` | `x == nil` | `x === null` | `x.is_none()` | `x == NULL` |

### Allocation

```
MakeSlice { element_type: Type, length: Expr?, capacity: Expr? }
MakeMap { key_type: Type, value_type: Type }
SliceLit { element_type: Type, elements: [Expr] }
MapLit { key_type: Type, value_type: Type, entries: [(Expr, Expr)] }
SetLit { element_type: Type, elements: [Expr] }
StructLit { struct_name: string, fields: {string: Expr} }
```

### Strings

```
StringConcat { parts: [Expr] }
StringFormat { template: string, args: [Expr] }
```

| IR             | Go            | TS               | Rust      | C          |
| -------------- | ------------- | ---------------- | --------- | ---------- |
| `StringConcat` | `+`           | `+`              | `format!` | `snprintf` |
| `StringFormat` | `fmt.Sprintf` | template literal | `format!` | `snprintf` |

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
4. **Ownership analysis** — Mark `Pointer.owned` for Rust/C (see Ownership Model)
5. **Method resolution** — Fill `MethodCall.receiver_type`
6. **Nil analysis** — `x is None` → `IsNil`
7. **Truthiness** — `if items:` → `if len(items) > 0`
8. **Type narrowing** — `isinstance` → `TypeSwitch` (see below)
9. **Fallibility analysis** — Mark functions containing `raise` as `fallible=true`

### Type Narrowing

Convert `isinstance` chains to `TypeSwitch`:

```python
# Python source
if isinstance(node, CommandSubstitution):
    process(node.command)
elif isinstance(node, ArithBinaryOp) or isinstance(node, ArithComma):
    process_binary(node)
```

```
// IR
TypeSwitch {
    expr: node
    binding: "node"
    cases: [
        TypeCase { typ: StructRef("CommandSubstitution"), body: [...] }
        TypeCase { typ: Union("", [StructRef("ArithBinaryOp"), StructRef("ArithComma")]), body: [...] }
    ]
}
```

**Collection element types:** When a field is annotated `list[Node]` but usage shows specific types, the frontend narrows:

| Annotation          | Actual Usage          | Resolved Type                         |
| ------------------- | --------------------- | ------------------------------------- |
| `list[Node]`        | Only `Word` assigned  | `Slice(StructRef("Word"))`            |
| `list[Node]`        | Mixed expansion types | `Slice(Union("Expansion", [...]))`    |
| `ArithNode \| None` | Type alias            | `Optional(Union("ArithNode", [...]))` |

Resolve Python `Union[...]` and `X | Y` type aliases to IR `Union` with explicit variants.

## Backend Responsibilities

Backends (IR → target) handle only syntax:

1. **Name conversion** — snake_case → camelCase/PascalCase
2. **Syntax emission** — IR nodes → target syntax
3. **Error propagation** — Fallible calls: Go uses panic, Rust uses `?`, TS uses throw
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

### Python Backend

Emit idiomatic Python, shedding `check_style.py` restrictions. The source is written in restricted Python for transpilation; the Python backend produces clean Pythonic output.

**Easy transforms:**
```
lst[len(lst)-1]     →  lst[-1]
int(a / b)          →  a // b
a < b and b < c     →  a < b < c
if x is None: x=[]  →  x = x or []
TypeSwitch          →  match/case
```

**Pattern-based transforms:**
```
i = 0                       for i, item in enumerate(items):
for item in items:      →       process(item)
    process(item)
    i += 1

for i in range(len(a)):     for x, y in zip(a, b):
    x = a[i]            →       process(x, y)
    y = b[i]
    process(x, y)
```

**Not recoverable** (not in IR): `**kwargs`, decorators, generators, `async`/`await`.

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

| IR      | Go                      | TS             | Rust   | C            |
| ------- | ----------------------- | -------------- | ------ | ------------ |
| `Union` | interface + type switch | class + `kind` | `enum` | tagged union |

## Ownership Model

AST is a **strict tree**: parent→child only, no cycles, no shared nodes, no back-references.

Nodes are immutable after construction. All nodes live until parse completion.

Arena allocation with single lifetime `'arena`. No reference counting needed.

**Ownership rule:** All child references are owned. No inference needed for parable.py:

| Field Pattern   | Ownership        | Rust                          | C                   |
| --------------- | ---------------- | ----------------------------- | ------------------- |
| `field: Node`   | Owned            | `Box<Node>` or `&'arena Node` | `Node*` (arena)     |
| `field: [Node]` | Owned collection | `Vec<&'arena Node>`           | `NodeSlice` (arena) |
| `field: Node?`  | Owned optional   | `Option<&'arena Node>`        | `Node*` (nullable)  |

Back-references (if ever needed) would use indices, not pointers: `parent_idx: u32`.

## String Handling

Two string representations:

```
StringRef { start: u32, end: u32 }    // Byte range into source buffer
ArenaStr { ptr: *const u8, len: u32 } // Arena-allocated
```

| Field type                  | Representation | Example                                     |
| --------------------------- | -------------- | ------------------------------------------- |
| Parameter names, delimiters | `StringRef`    | `ParamExpansion.param`, `HereDoc.delimiter` |
| Constructed content         | `ArenaStr`     | `Word.value`, `AnsiCQuote.content`          |
| Operator literals           | `&'static str` | `Operator.op`                               |

Input buffer must outlive AST, or copy referenced ranges into arena at parse end.
