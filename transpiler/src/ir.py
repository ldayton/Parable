"""Tongues IR - Language-agnostic intermediate representation.

This module defines the complete IR type system and serves as the specification.
Each node's docstring documents its semantics and invariants.

Architecture:
    Source -> Frontend (phases 1-8) -> [IR] -> Middleend (phases 10-13) -> Backend -> Target

Frontend produces fully-typed IR. Middleend annotates IR in place. Backend emits code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


# ============================================================
# SOURCE LOCATIONS
# ============================================================


@dataclass(frozen=True)
class Loc:
    """Source location for error messages and source maps.

    Invariants:
    - line >= 1 for valid locations (0 indicates unknown)
    - col >= 0 (0-indexed within line)
    - end_line >= line
    - end_col >= 0
    """

    line: int  # 1-indexed, 0 = unknown
    col: int  # 0-indexed
    end_line: int
    end_col: int

    @classmethod
    def unknown(cls) -> Loc:
        return cls(0, 0, 0, 0)


# ============================================================
# TYPES
#
# All types are frozen (immutable, hashable). The frontend resolves
# all type annotations to these representations by phase 4.
# ============================================================


@dataclass(frozen=True)
class Type:
    """Base for all types. Abstract."""


@dataclass(frozen=True)
class Primitive(Type):
    """Primitive types with direct target-language equivalents.

    | Kind   | Go      | Rust   | C        | Java    |
    |--------|---------|--------|----------|---------|
    | string | string  | String | char*    | String  |
    | int    | int     | i64    | int64_t  | long    |
    | bool   | bool    | bool   | bool     | boolean |
    | float  | float64 | f64    | double   | double  |
    | byte   | byte    | u8     | uint8_t  | byte    |
    | rune   | rune    | char   | int32_t  | int     |
    | void   | (none)  | ()     | void     | void    |
    """

    kind: Literal["string", "int", "bool", "float", "byte", "rune", "void"]


@dataclass(frozen=True)
class Char(Type):
    """Single character type, distinct from string.

    Used for:
    - Single-character literals: 'a'
    - Result of string indexing: s[i]
    - Character classification predicates

    Backends map to: Go rune, Java char, Rust char.
    """


@dataclass(frozen=True)
class CharSequence(Type):
    """String converted for character-based indexing.

    Used when a string variable is indexed by character position.
    Frontend infers this type; single conversion point at scope entry.

    | Target | Representation |
    |--------|----------------|
    | Go     | []rune         |
    | Java   | char[]         |
    | Rust   | Vec<char>      |
    | TS     | string         |

    Invariants:
    - Indexing yields Char, not byte
    - Length is character count, not byte count
    """


@dataclass(frozen=True)
class Slice(Type):
    """Growable sequence with homogeneous elements.

    | Target | Representation     |
    |--------|--------------------|
    | Go     | []T                |
    | Rust   | Vec<T>             |
    | Java   | ArrayList<T>       |
    | TS     | T[]                |

    Invariants:
    - element is a valid Type (not None)
    """

    element: Type


@dataclass(frozen=True)
class Array(Type):
    """Fixed-size array with compile-time known length.

    | Target | Representation |
    |--------|----------------|
    | Go     | [N]T           |
    | Rust   | [T; N]         |
    | C      | T[N]           |

    Invariants:
    - size > 0
    - element is a valid Type
    """

    element: Type
    size: int


@dataclass(frozen=True)
class Map(Type):
    """Key-value mapping with homogeneous keys and values.

    | Target | Representation   |
    |--------|------------------|
    | Go     | map[K]V          |
    | Rust   | HashMap<K, V>    |
    | Java   | HashMap<K, V>    |

    Invariants:
    - key is hashable type (Primitive, StructRef with value semantics)
    - value is a valid Type
    """

    key: Type
    value: Type


@dataclass(frozen=True)
class Set(Type):
    """Unordered collection of unique elements.

    | Target | Representation   |
    |--------|------------------|
    | Go     | map[T]struct{}   |
    | Rust   | HashSet<T>       |
    | Java   | HashSet<T>       |

    Invariants:
    - element is hashable type
    """

    element: Type


@dataclass(frozen=True)
class Tuple(Type):
    """Fixed-size heterogeneous sequence.

    | Target | Representation          |
    |--------|-------------------------|
    | Go     | multiple return values  |
    | Rust   | (T1, T2, ...)           |
    | TS     | [T1, T2, ...]           |

    Invariants:
    - len(elements) >= 2
    """

    elements: tuple[Type, ...]


@dataclass(frozen=True)
class Pointer(Type):
    """Pointer with optional ownership tracking.

    | Target | owned=True | owned=False |
    |--------|------------|-------------|
    | Go     | *T         | *T          |
    | Rust   | Box<T>     | &T          |
    | C      | T*         | T*          |

    Invariants:
    - target is not Void
    """

    target: Type
    owned: bool = True


@dataclass(frozen=True)
class Optional(Type):
    """Nullable value (sum of T and nil).

    | Target | Representation |
    |--------|----------------|
    | Go     | *T (nil)       |
    | Rust   | Option<T>      |
    | TS     | T | null       |

    Invariants:
    - inner is not Optional (no nested optionals)
    - inner is not Void
    """

    inner: Type


@dataclass(frozen=True)
class StructRef(Type):
    """Reference to a struct by name.

    Resolved by frontend; name must exist in Module.structs.
    """

    name: str


@dataclass(frozen=True)
class InterfaceRef(Type):
    """Reference to an interface by name.

    | Target | Representation      |
    |--------|---------------------|
    | Go     | InterfaceName       |
    | Rust   | dyn Trait           |
    | Java   | InterfaceName       |

    Special names:
    - "any": Go any/interface{}, Rust dyn Any, Java Object
    """

    name: str


@dataclass(frozen=True)
class Union(Type):
    """Closed discriminated union (sum type).

    All variants share a discriminant field (typically `kind: string`).

    | Target | Representation        |
    |--------|----------------------|
    | Go     | interface + type switch |
    | Rust   | enum                 |
    | TS     | discriminated union  |

    Invariants:
    - len(variants) >= 2
    - all variants have compatible discriminant field
    """

    name: str
    variants: tuple[StructRef, ...]


@dataclass(frozen=True)
class FuncType(Type):
    """Function type (for function pointers, callbacks, closures).

    | Target | Representation           |
    |--------|--------------------------|
    | Go     | func(P...) R             |
    | Rust   | fn(P...) -> R / Fn trait |

    Invariants:
    - ret is valid Type (use VOID for no return)
    """

    params: tuple[Type, ...]
    ret: Type
    captures: bool = False  # True if closure (captures environment)


# Singleton primitive types
STRING = Primitive("string")
INT = Primitive("int")
BOOL = Primitive("bool")
FLOAT = Primitive("float")
BYTE = Primitive("byte")
RUNE = Primitive("rune")
VOID = Primitive("void")
CHAR = Char()
CHAR_SEQUENCE = CharSequence()
StringSlice = STRING  # Backward compat: was separate type, maps to string


# ============================================================
# TOP-LEVEL DECLARATIONS
# ============================================================


@dataclass
class Module:
    """A complete transpilation unit.

    Invariants (post-frontend):
    - All StructRef names resolve to entries in structs
    - All InterfaceRef names resolve to entries in interfaces
    - No circular struct dependencies (fields don't form cycles)
    """

    name: str
    doc: str | None = None
    structs: list[Struct] = field(default_factory=list)
    interfaces: list[InterfaceDef] = field(default_factory=list)
    functions: list[Function] = field(default_factory=list)
    constants: list[Constant] = field(default_factory=list)
    enums: list[Enum] = field(default_factory=list)
    exports: list[Export] = field(default_factory=list)


@dataclass
class Struct:
    """Struct/class definition.

    Invariants:
    - Field names are unique within struct
    - Method names are unique within struct
    - implements contains only valid interface names
    - If is_exception, may have embedded_type for inheritance chain
    """

    name: str
    doc: str | None = None
    fields: list[Field] = field(default_factory=list)
    methods: list[Function] = field(default_factory=list)
    implements: list[str] = field(default_factory=list)
    loc: Loc = field(default_factory=Loc.unknown)
    is_exception: bool = False
    embedded_type: str | None = None  # Exception inheritance


@dataclass
class Field:
    """Struct field.

    Invariants:
    - typ is fully resolved (no unresolved type variables)
    - If default is present, default.typ is assignable to typ
    """

    name: str
    typ: Type
    default: Expr | None = None
    loc: Loc = field(default_factory=Loc.unknown)


@dataclass
class InterfaceDef:
    """Interface definition.

    Specifies a set of methods that implementing structs must provide.

    Invariants:
    - Method names are unique
    - fields contains discriminant fields for tagged unions (e.g., kind: string)
    """

    name: str
    methods: list[MethodSig] = field(default_factory=list)
    fields: list[Field] = field(default_factory=list)  # Discriminant fields
    loc: Loc = field(default_factory=Loc.unknown)


@dataclass
class MethodSig:
    """Method signature in an interface."""

    name: str
    params: list[Param]
    ret: Type
    loc: Loc = field(default_factory=Loc.unknown)


@dataclass
class Enum:
    """Enumeration definition.

    | Target | Representation           |
    |--------|--------------------------|
    | Go     | const iota or string     |
    | Rust   | enum                     |
    | TS     | enum or union            |

    Invariants:
    - len(variants) >= 1
    - Variant names are unique
    """

    name: str
    variants: list[EnumVariant]
    loc: Loc = field(default_factory=Loc.unknown)


@dataclass
class EnumVariant:
    """Single variant in an enumeration."""

    name: str
    value: int | str | None = None  # None = auto-assign
    loc: Loc = field(default_factory=Loc.unknown)


@dataclass
class Export:
    """Module export declaration.

    Specifies which symbols are public API.
    """

    name: str
    kind: Literal["function", "struct", "constant", "interface", "enum"]
    loc: Loc = field(default_factory=Loc.unknown)


@dataclass
class Function:
    """Function or method definition.

    Invariants:
    - All paths return a value if ret != VOID
    - Parameter names are unique
    - If receiver is present, this is a method

    Middleend annotations (set by phases 10-13):
    - needs_named_returns: Function has try/catch with catch-body returns (Go)
    - rune_vars: Variables needing []rune conversion at scope entry (Go)
    """

    name: str
    params: list[Param]
    ret: Type
    body: list[Stmt]
    doc: str | None = None
    receiver: Receiver | None = None
    fallible: bool = False  # Can raise/panic
    loc: Loc = field(default_factory=Loc.unknown)
    # Middleend annotations
    needs_named_returns: bool = False
    rune_vars: list[str] = field(default_factory=list)


@dataclass
class Receiver:
    """Method receiver (self).

    Invariants:
    - typ references a valid struct
    """

    name: str  # "self", "p", etc.
    typ: StructRef
    mutable: bool = False  # Rust: &mut self
    pointer: bool = True  # Go: *T receiver


@dataclass
class Param:
    """Function parameter.

    Middleend annotations:
    - is_modified: Parameter is assigned/mutated in function body
    - is_unused: Parameter is never referenced
    """

    name: str
    typ: Type
    default: Expr | None = None
    mutable: bool = False  # Rust: mut
    loc: Loc = field(default_factory=Loc.unknown)
    # Middleend annotations
    is_modified: bool = False
    is_unused: bool = False


@dataclass
class Constant:
    """Module-level constant.

    Invariants:
    - value is a compile-time constant expression
    - value.typ matches typ
    """

    name: str
    typ: Type
    value: Expr
    loc: Loc = field(default_factory=Loc.unknown)


# ============================================================
# STATEMENTS
# ============================================================


@dataclass(kw_only=True)
class Stmt:
    """Base for all statements. Abstract."""

    loc: Loc = field(default_factory=Loc.unknown)


@dataclass
class NoOp(Stmt):
    """No operation. Used for empty blocks, pass statements.

    Backends may emit nothing or a comment.
    """


@dataclass
class VarDecl(Stmt):
    """Variable declaration with optional initializer.

    Semantics:
    - Introduces name into current scope
    - If value is None, variable has zero value for typ

    | Target | mutable=True    | mutable=False |
    |--------|-----------------|---------------|
    | Go     | var x T = v     | (same)        |
    | Rust   | let mut x = v   | let x = v     |
    | TS     | let x = v       | const x = v   |
    | Java   | T x = v         | final T x = v |

    Middleend annotations:
    - is_reassigned: Variable assigned again after declaration
    - is_const: Never reassigned (enables const/final emission)
    - initial_value_unused: Initial value overwritten before read
    """

    name: str
    typ: Type
    value: Expr | None = None
    mutable: bool = True
    # Middleend annotations
    is_reassigned: bool = False
    is_const: bool = False
    initial_value_unused: bool = False


@dataclass
class Assign(Stmt):
    """Assignment to existing variable or location.

    Semantics: target := value

    Middleend annotations:
    - is_declaration: This is the first assignment (Python-style declaration)
    """

    target: LValue
    value: Expr
    # Middleend annotations
    is_declaration: bool = False


@dataclass
class TupleAssign(Stmt):
    """Multi-value assignment: a, b = expr

    Semantics: Destructure expr (tuple or multi-return) into targets.

    Invariants:
    - len(targets) matches arity of value.typ (Tuple or multi-return)

    Middleend annotations:
    - unused_indices: Which targets are never used (for _ placeholders)
    """

    targets: list[LValue]
    value: Expr
    # Middleend annotations
    unused_indices: list[int] = field(default_factory=list)


@dataclass
class OpAssign(Stmt):
    """Compound assignment: target op= value

    Semantics: target := target op value

    Invariants:
    - op is one of: +, -, *, /, %, &, |, ^, <<, >>
    """

    target: LValue
    op: str
    value: Expr


@dataclass
class ExprStmt(Stmt):
    """Expression evaluated for side effects, result discarded.

    Invariants:
    - expr has side effects (call, method call) or is intentionally discarded
    """

    expr: Expr


@dataclass
class Return(Stmt):
    """Return from function.

    Semantics:
    - If value is None, return void (function must have ret = VOID)
    - Otherwise, return value (value.typ must match function ret)
    """

    value: Expr | None = None


@dataclass
class If(Stmt):
    """Conditional statement.

    Semantics:
    - Evaluate cond; if truthy, execute then_body; else execute else_body
    - If init is present, execute init first (Go-style if-init)

    Invariants:
    - cond.typ is BOOL
    - init, if present, is VarDecl

    Middleend annotations:
    - hoisted_vars: Variables first assigned in branches, used after (Go)
    """

    cond: Expr
    then_body: list[Stmt]
    else_body: list[Stmt] = field(default_factory=list)
    init: VarDecl | None = None
    # Middleend annotations
    hoisted_vars: list[tuple[str, Type]] = field(default_factory=list)


@dataclass
class TypeSwitch(Stmt):
    """Switch on runtime type.

    Semantics:
    - Evaluate expr
    - Match against cases by type
    - In matching case, binding has narrowed type

    | Target | Representation                    |
    |--------|-----------------------------------|
    | Go     | switch binding := expr.(type)     |
    | Rust   | match with downcast               |
    | TS     | if/else with typeof/instanceof    |

    Middleend annotations:
    - binding_unused: Binding variable never referenced in any case
    - hoisted_vars: Variables needing hoisting
    """

    expr: Expr
    binding: str
    cases: list[TypeCase] = field(default_factory=list)
    default: list[Stmt] = field(default_factory=list)
    # Middleend annotations
    binding_unused: bool = False
    hoisted_vars: list[tuple[str, Type]] = field(default_factory=list)


@dataclass
class TypeCase:
    """A case in a type switch.

    Invariants:
    - typ is a concrete type (not Union or any)
    """

    typ: Type
    body: list[Stmt]
    loc: Loc = field(default_factory=Loc.unknown)


@dataclass
class Match(Stmt):
    """Value matching (switch/case on values).

    Semantics:
    - Evaluate expr
    - Compare against each case's patterns
    - Execute body of first matching case
    - If no match, execute default

    Invariants:
    - All pattern types match expr.typ

    Middleend annotations:
    - hoisted_vars: Variables needing hoisting
    """

    expr: Expr
    cases: list[MatchCase] = field(default_factory=list)
    default: list[Stmt] = field(default_factory=list)
    # Middleend annotations
    hoisted_vars: list[tuple[str, Type]] = field(default_factory=list)


@dataclass
class MatchCase:
    """A case in a match statement.

    Invariants:
    - len(patterns) >= 1
    - All patterns are constant expressions
    """

    patterns: list[Expr]
    body: list[Stmt]
    loc: Loc = field(default_factory=Loc.unknown)


@dataclass
class ForRange(Stmt):
    """Iterate over collection.

    Semantics:
    - For each (index, value) in iterable, execute body
    - index is None if unused
    - value is None if unused

    | Target | Representation                |
    |--------|-------------------------------|
    | Go     | for i, v := range iterable    |
    | Rust   | for (i, v) in iter.enumerate()|
    | TS     | for (const [i, v] of entries) |

    Middleend annotations:
    - hoisted_vars: Variables needing hoisting
    """

    index: str | None
    value: str | None
    iterable: Expr
    body: list[Stmt]
    # Middleend annotations
    hoisted_vars: list[tuple[str, Type]] = field(default_factory=list)


@dataclass
class ForClassic(Stmt):
    """C-style for loop: for (init; cond; post) body

    Semantics:
    - Execute init
    - While cond is true: execute body, then post

    Used for range() iteration and index-based loops.

    Middleend annotations:
    - hoisted_vars: Variables needing hoisting
    """

    init: Stmt | None
    cond: Expr | None
    post: Stmt | None
    body: list[Stmt]
    # Middleend annotations
    hoisted_vars: list[tuple[str, Type]] = field(default_factory=list)


@dataclass
class While(Stmt):
    """While loop.

    Semantics: While cond is true, execute body.

    Invariants:
    - cond.typ is BOOL

    Middleend annotations:
    - hoisted_vars: Variables needing hoisting
    """

    cond: Expr
    body: list[Stmt]
    # Middleend annotations
    hoisted_vars: list[tuple[str, Type]] = field(default_factory=list)


@dataclass
class Break(Stmt):
    """Break from loop.

    If label is present, break from labeled loop.
    """

    label: str | None = None


@dataclass
class Continue(Stmt):
    """Continue to next iteration.

    If label is present, continue labeled loop.
    """

    label: str | None = None


@dataclass
class Block(Stmt):
    """Scoped block.

    Semantics: Execute body in new scope. Variables declared
    inside are not visible outside.
    """

    body: list[Stmt]


@dataclass
class TryCatch(Stmt):
    """Exception handling.

    Semantics:
    - Execute body
    - If exception of catch_type is raised, bind to catch_var and execute catch_body
    - If reraise is True, catch_body re-raises after cleanup

    | Target | Representation                |
    |--------|-------------------------------|
    | Go     | defer/recover pattern         |
    | Rust   | Result + ? or panic/catch     |
    | TS     | try/catch                     |

    Middleend annotations:
    - catch_var_unused: catch_var never referenced in catch_body
    - hoisted_vars: Variables needing hoisting
    """

    body: list[Stmt]
    catch_var: str | None = None
    catch_type: Type | None = None  # Exception type to catch
    catch_body: list[Stmt] = field(default_factory=list)
    reraise: bool = False
    # Middleend annotations
    catch_var_unused: bool = False
    hoisted_vars: list[tuple[str, Type]] = field(default_factory=list)


@dataclass
class Raise(Stmt):
    """Raise exception.

    Semantics:
    - If reraise_var is set, re-raise that caught exception
    - Otherwise, create new exception of error_type with message and pos

    | Target | Representation          |
    |--------|-------------------------|
    | Go     | panic(Error{...})       |
    | Rust   | return Err(...) or panic|
    | TS     | throw new Error(...)    |
    """

    error_type: str
    message: Expr
    pos: Expr
    reraise_var: str | None = None


@dataclass
class SoftFail(Stmt):
    """Return nil/None to signal failure without exception.

    Used in parser combinators: "try this, if it doesn't match, return nil".

    | Target | Representation |
    |--------|----------------|
    | Go     | return nil     |
    | Rust   | return None    |
    """


# ============================================================
# EXPRESSIONS
#
# All expressions carry their resolved type (typ field).
# This is an invariant established by frontend phase 7.
# ============================================================


@dataclass(kw_only=True)
class Expr:
    """Base for all expressions. Abstract.

    Invariants (post-frontend):
    - typ is fully resolved
    - typ is not None

    Middleend annotations:
    - is_interface: Expression statically typed as interface (affects nil checks in Go)
    - narrowed_type: More precise type at this use site after type guards
    """

    typ: Type
    loc: Loc = field(default_factory=Loc.unknown)
    # Middleend annotations
    is_interface: bool = False
    narrowed_type: Type | None = None


# --- Literals ---


@dataclass
class IntLit(Expr):
    """Integer literal.

    Invariants:
    - typ is INT
    """

    value: int


@dataclass
class FloatLit(Expr):
    """Float literal.

    Invariants:
    - typ is FLOAT
    """

    value: float


@dataclass
class StringLit(Expr):
    """String literal.

    Invariants:
    - typ is STRING
    """

    value: str


@dataclass
class CharLit(Expr):
    """Single character literal.

    Distinct from StringLit for backends that distinguish char/string.

    Invariants:
    - len(value) == 1
    - typ is CHAR or RUNE
    """

    value: str


@dataclass
class BoolLit(Expr):
    """Boolean literal.

    Invariants:
    - typ is BOOL
    """

    value: bool


@dataclass
class NilLit(Expr):
    """Nil/null/None literal.

    Invariants:
    - typ is Optional(T) or Pointer(T) for some T
    """


# --- Variables and Access ---


@dataclass
class Var(Expr):
    """Variable reference.

    Semantics: Evaluate to current value of named variable.

    Invariants:
    - name is in scope
    - typ matches declaration type (or narrowed_type if set)
    """

    name: str


@dataclass
class FieldAccess(Expr):
    """Field access: obj.field

    Semantics: Access field of struct value.

    Invariants:
    - obj.typ is StructRef or Pointer(StructRef)
    - field exists on that struct
    - typ matches field type
    """

    obj: Expr
    field: str
    through_pointer: bool = False  # Go auto-deref


@dataclass
class Index(Expr):
    """Indexing: obj[index]

    Semantics:
    - Slice/Array: element at index (0-based)
    - Map: value for key
    - String: character at index (use CharAt for semantic clarity)

    Invariants:
    - obj.typ is Slice, Array, Map, or STRING
    - For Slice/Array: index.typ is INT
    - For Map: index.typ matches key type
    """

    obj: Expr
    index: Expr
    bounds_check: bool = True
    returns_optional: bool = False  # Go map returns (v, ok)


@dataclass
class SliceExpr(Expr):
    """Subslice: obj[low:high]

    Semantics: Extract subsequence from low (inclusive) to high (exclusive).

    Invariants:
    - obj.typ is Slice, Array, or STRING
    - low.typ is INT if present
    - high.typ is INT if present
    - typ matches obj.typ (or Slice if obj is Array)
    """

    obj: Expr
    low: Expr | None = None
    high: Expr | None = None


# --- Calls ---


@dataclass
class Call(Expr):
    """Free function call.

    Semantics: Call function with arguments, return result.

    Invariants:
    - func exists in module scope
    - len(args) matches function arity (considering defaults)
    - arg types match parameter types
    - typ matches function return type
    """

    func: str
    args: list[Expr]


@dataclass
class MethodCall(Expr):
    """Method call: obj.method(args)

    Semantics: Call method on receiver with arguments.

    Invariants:
    - method exists on receiver_type
    - arg types match parameter types
    - typ matches method return type
    """

    obj: Expr
    method: str
    args: list[Expr]
    receiver_type: Type


@dataclass
class StaticCall(Expr):
    """Static method / associated function.

    Semantics: Call method without instance receiver.

    | Target | Representation     |
    |--------|--------------------|
    | Go     | Type.Method(args)  |
    | Rust   | Type::method(args) |
    | Java   | Type.method(args)  |
    """

    on_type: Type
    method: str
    args: list[Expr]


@dataclass
class FuncRef(Expr):
    """Reference to a function or bound method.

    Semantics:
    - If obj is None: reference to free function
    - If obj is present: bound method (captures receiver)

    Invariants:
    - typ is FuncType
    """

    name: str
    obj: Expr | None = None  # Receiver for bound method


# --- Operators ---


@dataclass
class BinaryOp(Expr):
    """Binary operation: left op right

    Operator semantics:
    - Arithmetic (+, -, *, /, %, **): numeric operands, numeric result
    - Comparison (==, !=, <, <=, >, >=): compatible operands, BOOL result
    - Logical (&&, ||): BOOL operands, BOOL result (short-circuit)
    - Bitwise (&, |, ^, <<, >>): INT operands, INT result

    Invariants:
    - For &&, ||: left.typ == right.typ == BOOL, typ == BOOL
    - For comparisons: typ == BOOL
    - String + is NOT represented here; use StringConcat
    """

    op: str
    left: Expr
    right: Expr


@dataclass
class UnaryOp(Expr):
    """Unary operation: op operand

    Operator semantics:
    - Negation (-): numeric operand and result
    - Logical not (!): BOOL operand and result
    - Bitwise not (~): INT operand and result
    - Dereference (*): Pointer operand, target result

    Note: Address-of (&) uses AddrOf for semantic clarity.
    """

    op: str  # "-", "!", "~", "*"
    operand: Expr


@dataclass
class Truthy(Expr):
    """Truthiness test.

    Semantics: Test if value is "truthy" (non-zero, non-empty, non-nil).

    | Source     | Meaning                    |
    |------------|----------------------------|
    | if x       | x is truthy                |
    | if s       | s is non-empty             |
    | if lst     | lst is non-empty           |
    | if opt     | opt is not nil             |

    | Target | Representation                    |
    |--------|-----------------------------------|
    | Go     | len(s) > 0 or x != nil or x != 0  |
    | Rust   | !s.is_empty() or x.is_some()      |
    | TS     | !!x or x.length > 0               |

    Invariants:
    - typ is BOOL
    """

    expr: Expr


@dataclass
class Ternary(Expr):
    """Ternary conditional: cond ? then_expr : else_expr

    Semantics: If cond, evaluate then_expr; else evaluate else_expr.

    Invariants:
    - cond.typ is BOOL
    - then_expr.typ and else_expr.typ are compatible
    - typ is common type of branches

    Backend guidance:
    - needs_statement: Go lacks ternary; emit if/else with temp var
    """

    cond: Expr
    then_expr: Expr
    else_expr: Expr
    needs_statement: bool = False


# --- Type Operations ---


@dataclass
class Cast(Expr):
    """Type conversion.

    Semantics: Convert expr to to_type.

    | Target | Representation |
    |--------|----------------|
    | Go     | T(x)           |
    | Rust   | x as T         |
    | Java   | (T) x          |

    Invariants:
    - Conversion is valid (numeric↔numeric, etc.)
    """

    expr: Expr
    to_type: Type


@dataclass
class TypeAssert(Expr):
    """Runtime type assertion.

    Semantics: Assert expr has type asserted at runtime.

    | Target | safe=True           | safe=False        |
    |--------|---------------------|-------------------|
    | Go     | x.(T) with ok check | x.(T) panic       |
    | Rust   | downcast checked    | downcast unchecked|

    Invariants:
    - expr.typ is interface or union containing asserted
    """

    expr: Expr
    asserted: Type
    safe: bool = True


@dataclass
class IsType(Expr):
    """Type test: is expr of type tested_type?

    Semantics: Return true if runtime type matches.

    | Target | Representation           |
    |--------|--------------------------|
    | Go     | _, ok := x.(T)           |
    | Rust   | x.is::<T>() or match     |
    | TS     | x instanceof T           |

    Invariants:
    - typ is BOOL
    """

    expr: Expr
    tested_type: Type


@dataclass
class IsNil(Expr):
    """Nil check.

    Semantics: Test if expr is nil/null/None.

    | Target | Representation           |
    |--------|--------------------------|
    | Go     | x == nil (or reflection) |
    | Rust   | x.is_none()              |
    | TS     | x === null               |

    Backend note: For Go interfaces, may need reflection-based check.
    See is_interface annotation on expr.

    Invariants:
    - typ is BOOL
    - expr.typ is Optional or Pointer or Interface
    """

    expr: Expr
    negated: bool = False  # true = "is not nil"


# --- Collection Operations ---


@dataclass
class Len(Expr):
    """Length of collection or string.

    | Target | Representation |
    |--------|----------------|
    | Go     | len(x)         |
    | Rust   | x.len()        |
    | TS     | x.length       |

    Invariants:
    - expr.typ is Slice, Array, Map, Set, or STRING
    - typ is INT
    """

    expr: Expr


@dataclass
class MakeSlice(Expr):
    """Allocate new slice.

    | Target | Representation              |
    |--------|-----------------------------|
    | Go     | make([]T, len, cap)         |
    | Rust   | Vec::with_capacity(cap)     |
    | TS     | new Array(len)              |

    Invariants:
    - typ is Slice(element_type)
    """

    element_type: Type
    length: Expr | None = None
    capacity: Expr | None = None


@dataclass
class MakeMap(Expr):
    """Allocate new map.

    | Target | Representation      |
    |--------|---------------------|
    | Go     | make(map[K]V)       |
    | Rust   | HashMap::new()      |
    | TS     | new Map()           |

    Invariants:
    - typ is Map(key_type, value_type)
    """

    key_type: Type
    value_type: Type


@dataclass
class SliceLit(Expr):
    """Slice literal with elements.

    | Target | Representation   |
    |--------|------------------|
    | Go     | []T{a, b, c}     |
    | Rust   | vec![a, b, c]    |
    | TS     | [a, b, c]        |

    Invariants:
    - All elements have types assignable to element_type
    - typ is Slice(element_type)
    """

    element_type: Type
    elements: list[Expr]


@dataclass
class MapLit(Expr):
    """Map literal.

    Invariants:
    - All keys have type key_type
    - All values have type value_type
    - typ is Map(key_type, value_type)
    """

    key_type: Type
    value_type: Type
    entries: list[tuple[Expr, Expr]]


@dataclass
class SetLit(Expr):
    """Set literal.

    | Target | Representation           |
    |--------|--------------------------|
    | Go     | map[T]struct{}{a: {}, ...} |
    | Rust   | HashSet::from([a, b])    |
    | TS     | new Set([a, b])          |

    Invariants:
    - All elements have type element_type
    - typ is Set(element_type)
    """

    element_type: Type
    elements: list[Expr]


@dataclass
class TupleLit(Expr):
    """Tuple literal.

    Invariants:
    - typ is Tuple with matching element types
    """

    elements: list[Expr]


@dataclass
class StructLit(Expr):
    """Struct instantiation.

    Semantics: Create new instance with specified field values.

    | Target | Representation           |
    |--------|--------------------------|
    | Go     | &StructName{f1: v1, ...} |
    | Rust   | StructName { f1: v1, ... }|

    Invariants:
    - struct_name exists in module
    - All required fields have values
    - Field value types match field types
    - typ is StructRef(struct_name) or Pointer thereof
    """

    struct_name: str
    fields: dict[str, Expr]
    embedded_value: Expr | None = None  # For embedded struct (exception inheritance)


@dataclass
class LastElement(Expr):
    """Last element of sequence.

    Semantics: Equivalent to seq[len(seq)-1] but semantic.

    | Target | Representation   |
    |--------|------------------|
    | Go     | s[len(s)-1]      |
    | Python | s[-1]            |
    | Java   | s.get(s.size()-1)|

    Invariants:
    - sequence.typ is Slice or Array
    - typ is element type
    """

    sequence: Expr


@dataclass
class SliceConvert(Expr):
    """Convert slice element type (for covariance).

    Semantics: Convert []A to []B where A is subtype of B.

    Used when passing concrete slice to interface slice parameter.
    Some backends need explicit conversion (Go), others don't (TS).

    Invariants:
    - source.typ is Slice(A)
    - A is subtype of target_element_type
    - typ is Slice(target_element_type)
    """

    source: Expr
    target_element_type: Type


# --- String Operations (Semantic IR) ---


@dataclass
class CharAt(Expr):
    """Character at index in string.

    Semantics: Get single character at position (0-indexed).

    | Target | Representation            |
    |--------|---------------------------|
    | Go     | []rune(s)[i] or runes[i]  |
    | Java   | s.charAt(i)               |
    | Rust   | s.chars().nth(i)          |

    Invariants:
    - string.typ is STRING
    - index.typ is INT
    - typ is CHAR or RUNE
    """

    string: Expr
    index: Expr


@dataclass
class CharLen(Expr):
    """Character length of string (not byte length).

    Semantics: Count of Unicode characters.

    | Target | Representation      |
    |--------|---------------------|
    | Go     | len([]rune(s))      |
    | Java   | s.length()          |
    | Rust   | s.chars().count()   |

    Invariants:
    - string.typ is STRING
    - typ is INT
    """

    string: Expr


@dataclass
class Substring(Expr):
    """Extract substring by character indices.

    Semantics: Characters from low (inclusive) to high (exclusive).

    | Target | Representation              |
    |--------|-----------------------------|
    | Go     | string([]rune(s)[lo:hi])    |
    | Java   | s.substring(lo, hi)         |
    | Rust   | s.chars().skip(lo).take(hi-lo).collect() |

    Invariants:
    - string.typ is STRING
    - low.typ is INT if present
    - high.typ is INT if present
    - typ is STRING
    """

    string: Expr
    low: Expr | None = None
    high: Expr | None = None


@dataclass
class StringConcat(Expr):
    """String concatenation.

    Semantics: Concatenate all parts into single string.

    | Target | Representation            |
    |--------|---------------------------|
    | Go     | s1 + s2 + ... or builder  |
    | Rust   | format!("{}{}", s1, s2)   |

    Invariants:
    - len(parts) >= 2
    - All parts have type STRING (after conversion)
    - typ is STRING
    """

    parts: list[Expr]


@dataclass
class StringFormat(Expr):
    """Format string with arguments.

    Semantics: Substitute args into template placeholders.

    | Target | Representation          |
    |--------|-------------------------|
    | Go     | fmt.Sprintf(tmpl, args) |
    | Rust   | format!(tmpl, args)     |
    | TS     | template literal        |

    Invariants:
    - Placeholder count matches len(args)
    - typ is STRING
    """

    template: str
    args: list[Expr]


@dataclass
class TrimChars(Expr):
    """Trim characters from string.

    Semantics: Remove chars from specified side(s) of string.

    | Target | Representation                        |
    |--------|---------------------------------------|
    | Go     | strings.TrimLeft/Right/Trim           |
    | Python | s.lstrip/rstrip/strip(chars)          |
    | Java   | regex or manual                       |

    Invariants:
    - string.typ is STRING
    - chars.typ is STRING (set of chars to trim)
    - typ is STRING
    """

    string: Expr
    chars: Expr
    mode: Literal["left", "right", "both"]


@dataclass
class CharClassify(Expr):
    """Character classification test.

    Semantics: Test if character belongs to class.

    | Kind   | Go                  | Java                 |
    |--------|---------------------|----------------------|
    | alnum  | unicode.IsLetter || unicode.IsDigit | Character.isLetterOrDigit |
    | digit  | unicode.IsDigit     | Character.isDigit    |
    | alpha  | unicode.IsLetter    | Character.isLetter   |
    | space  | unicode.IsSpace     | Character.isWhitespace |
    | upper  | unicode.IsUpper     | Character.isUpperCase |
    | lower  | unicode.IsLower     | Character.isLowerCase |

    Invariants:
    - char.typ is CHAR or RUNE or STRING (single char)
    - typ is BOOL
    """

    kind: Literal["alnum", "digit", "alpha", "space", "upper", "lower"]
    char: Expr


# --- Numeric Conversion ---


@dataclass
class ParseInt(Expr):
    """Parse string to integer.

    Semantics: Convert decimal string representation to int.

    | Target | Representation        |
    |--------|-----------------------|
    | Go     | strconv.Atoi(s)       |
    | Java   | Integer.parseInt(s)   |
    | Rust   | s.parse::<i64>()      |

    Error handling depends on context (may panic or return error).

    Invariants:
    - string.typ is STRING
    - typ is INT
    """

    string: Expr


@dataclass
class IntToStr(Expr):
    """Convert integer to string.

    | Target | Representation       |
    |--------|----------------------|
    | Go     | strconv.Itoa(n)      |
    | Java   | String.valueOf(n)    |
    | Rust   | n.to_string()        |

    Invariants:
    - value.typ is INT
    - typ is STRING
    """

    value: Expr


@dataclass
class SentinelToOptional(Expr):
    """Convert sentinel value to Optional.

    Semantics: If expr equals sentinel, return nil; else return expr.

    Common pattern: -1 as "not found" → None

    | Target | Representation                     |
    |--------|------------------------------------|
    | Go     | if x == sentinel { nil } else { x }|
    | Rust   | if x == sentinel { None } else { Some(x) } |

    Invariants:
    - expr.typ matches sentinel.typ
    - typ is Optional(expr.typ)
    """

    expr: Expr
    sentinel: Expr


# --- Pointer Operations ---


@dataclass
class AddrOf(Expr):
    """Take address of value.

    Semantics: Create pointer to value.

    | Target | Representation |
    |--------|----------------|
    | Go     | &x             |
    | Rust   | &x or Box::new |
    | C      | &x             |

    Invariants:
    - operand is addressable (variable, field, index)
    - typ is Pointer(operand.typ)
    """

    operand: Expr


# ============================================================
# LVALUES (Assignment Targets)
# ============================================================


@dataclass(kw_only=True)
class LValue:
    """Base for assignment targets. Abstract."""

    loc: Loc = field(default_factory=Loc.unknown)


@dataclass
class VarLV(LValue):
    """Variable as lvalue."""

    name: str


@dataclass
class FieldLV(LValue):
    """Field access as lvalue: obj.field = ..."""

    obj: Expr
    field: str


@dataclass
class IndexLV(LValue):
    """Index as lvalue: obj[index] = ..."""

    obj: Expr
    index: Expr


@dataclass
class DerefLV(LValue):
    """Pointer dereference as lvalue: *ptr = ..."""

    ptr: Expr


# ============================================================
# SYMBOL TABLE (Frontend Output)
#
# Metadata collected during frontend phases, used by middleend
# and backend for code generation decisions.
# ============================================================


@dataclass
class SymbolTable:
    """Symbol information collected by frontend."""

    structs: dict[str, StructInfo] = field(default_factory=dict)
    functions: dict[str, FuncInfo] = field(default_factory=dict)
    constants: dict[str, Type] = field(default_factory=dict)


@dataclass
class StructInfo:
    """Metadata about a struct."""

    name: str
    fields: dict[str, FieldInfo] = field(default_factory=dict)
    methods: dict[str, FuncInfo] = field(default_factory=dict)
    is_node: bool = False  # Implements Node interface
    is_exception: bool = False  # Inherits from Exception
    bases: list[str] = field(default_factory=list)
    init_params: list[str] = field(default_factory=list)
    param_to_field: dict[str, str] = field(default_factory=dict)
    needs_constructor: bool = False  # __init__ has computed values
    const_fields: dict[str, str] = field(default_factory=dict)


@dataclass
class FieldInfo:
    """Metadata about a field."""

    name: str
    typ: Type
    py_name: str = ""


@dataclass
class FuncInfo:
    """Metadata about a function or method."""

    name: str
    params: list[ParamInfo] = field(default_factory=list)
    return_type: Type = VOID
    is_method: bool = False
    receiver_type: str = ""


@dataclass
class ParamInfo:
    """Metadata about a parameter."""

    name: str
    typ: Type
    has_default: bool = False
    default_value: Expr | None = None
