"""Tongues IR - Language-agnostic intermediate representation.

This module defines the complete IR type system and serves as the specification.
Each node's docstring documents its semantics and invariants.

Architecture:
    Source -> Frontend (phases 2-9) -> [IR] -> Middleend (phases 10-14) -> Backend -> Target

Frontend produces fully-typed IR. Middleend annotates IR in place. Backend emits code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


# ============================================================
# OWNERSHIP
#
# Memory ownership annotations inferred by phase 14 (ownership.py).
# Backends use these to emit correct memory management code.
# ============================================================

Ownership = Literal["owned", "borrowed", "shared", "weak"]
"""Ownership classification for values and references.

| Kind     | Meaning                          | C                    | Go      | Java    | Python  | Rust        | TS      |
|----------|----------------------------------|----------------------|---------|---------|---------|-------------|---------|
| owned    | Value owned by this binding      | arena-allocated      | (GC)    | (GC)    | (GC)    | T / Box<T>  | (GC)    |
| borrowed | Reference to caller's value      | pointer (no free)    | (GC)    | (GC)    | (GC)    | &T          | (GC)    |
| shared   | Runtime-managed (inference fail) | refcounted           | (GC)    | (GC)    | (GC)    | Rc<T>       | (GC)    |
| weak     | Back-reference (no ownership)    | non-owning pointer   | (GC)    | WeakRef | weakref | Weak<T>     | (GC)    |

Default ownership:
- VarDecl: owned (unless assigned from borrowed)
- Param: borrowed (unless explicitly takes ownership)
- Field: owned (unless marked weak for back-references)
- Return: owned (ownership transfers to caller)
"""


# ============================================================
# SOURCE LOCATIONS
# ============================================================


@dataclass(unsafe_hash=True)
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


def loc_unknown() -> Loc:
    """Factory for unknown source location."""
    return Loc(0, 0, 0, 0)


# ============================================================
# TYPES
#
# All types are frozen (immutable, hashable). The frontend resolves
# all type annotations to these representations by phase 5.
# ============================================================


@dataclass(unsafe_hash=True)
class Type:
    """Base for all types. Abstract."""


@dataclass(unsafe_hash=True)
class Primitive(Type):
    """Primitive types with direct target-language equivalents.

    | Kind   | C        | Go      | Java    | Python  | Rust   | TS      |
    |--------|----------|---------|---------|---------|--------|---------|
    | string | char*    | string  | String  | str     | String | string  |
    | int    | int64_t  | int     | long    | int     | i64    | number  |
    | bool   | bool     | bool    | boolean | bool    | bool   | boolean |
    | float  | double   | float64 | double  | float   | f64    | number  |
    | byte   | uint8_t  | byte    | byte    | int     | u8     | number  |
    | rune   | int32_t  | rune    | int     | str     | char   | string  |
    | void   | void     | (none)  | void    | None    | ()     | void    |
    """

    kind: Literal["string", "int", "bool", "float", "byte", "rune", "void"]


@dataclass(unsafe_hash=True)
class Char(Type):
    """Single character type, distinct from string.

    Used for:
    - Single-character literals: 'a'
    - Result of string indexing: s[i]
    - Character classification predicates

    Backends map to: Go rune, Java char, Rust char.
    """


@dataclass(unsafe_hash=True)
class CharSequence(Type):
    """String converted for character-based indexing.

    Used when a string variable is indexed by character position.
    Frontend infers this type; single conversion point at scope entry.

    | Target | Representation |
    |--------|----------------|
    | C      | int32_t*       |
    | Go     | []rune         |
    | Java   | char[]         |
    | Python | str            |
    | Rust   | Vec<char>      |
    | TS     | string         |

    Invariants:
    - Indexing yields Char, not byte
    - Length is character count, not byte count
    """


@dataclass(unsafe_hash=True)
class Bytes(Type):
    """Byte sequence type for binary I/O.

    | Target | Representation |
    |--------|----------------|
    | C      | uint8_t*       |
    | Go     | []byte         |
    | Java   | byte[]         |
    | Python | bytes          |
    | Rust   | Vec<u8>        |
    | TS     | Uint8Array     |

    Distinct from Slice(BYTE) for semantic clarity in I/O operations.
    """


@dataclass(unsafe_hash=True)
class Slice(Type):
    """Growable sequence with homogeneous elements.

    | Target | Representation     |
    |--------|--------------------|
    | C      | T* + len           |
    | Go     | []T                |
    | Java   | ArrayList<T>       |
    | Python | list[T]            |
    | Rust   | Vec<T>             |
    | TS     | T[]                |

    Invariants:
    - element is a valid Type (not None)
    """

    element: Type


@dataclass(unsafe_hash=True)
class Array(Type):
    """Fixed-size array with compile-time known length.

    | Target | Representation |
    |--------|----------------|
    | C      | T[N]           |
    | Go     | [N]T           |
    | Java   | T[]            |
    | Python | tuple[T, ...]  |
    | Rust   | [T; N]         |
    | TS     | T[] (readonly) |

    Invariants:
    - size > 0
    - element is a valid Type
    """

    element: Type
    size: int


@dataclass(unsafe_hash=True)
class Map(Type):
    """Key-value mapping with homogeneous keys and values.

    | Target | Representation   |
    |--------|------------------|
    | C      | hashmap struct   |
    | Go     | map[K]V          |
    | Java   | HashMap<K, V>    |
    | Python | dict[K, V]       |
    | Rust   | HashMap<K, V>    |
    | TS     | Map<K, V>        |

    Invariants:
    - key is hashable type (Primitive, StructRef with value semantics)
    - value is a valid Type
    """

    key: Type
    value: Type


@dataclass(unsafe_hash=True)
class Set(Type):
    """Unordered collection of unique elements.

    | Target | Representation   |
    |--------|------------------|
    | C      | hashset struct   |
    | Go     | map[T]struct{}   |
    | Java   | HashSet<T>       |
    | Python | set[T]           |
    | Rust   | HashSet<T>       |
    | TS     | Set<T>           |

    Invariants:
    - element is hashable type
    """

    element: Type


@dataclass(unsafe_hash=True)
class Tuple(Type):
    """Fixed-size heterogeneous sequence.

    | Target | Representation          |
    |--------|-------------------------|
    | C      | struct { T1; T2; ... }  |
    | Go     | multiple return values  |
    | Java   | record or Object[]      |
    | Python | tuple[T1, T2, ...]      |
    | Rust   | (T1, T2, ...)           |
    | TS     | [T1, T2, ...]           |

    Invariants:
    - len(elements) >= 2
    """

    elements: tuple[Type, ...]


@dataclass(unsafe_hash=True)
class Pointer(Type):
    """Pointer with optional ownership tracking.

    | Target | owned=True | owned=False |
    |--------|------------|-------------|
    | C      | T*         | T*          |
    | Go     | *T         | *T          |
    | Java   | T          | T           |
    | Python | T          | T           |
    | Rust   | Box<T>     | &T          |
    | TS     | T          | T           |

    Invariants:
    - target is not Void
    """

    target: Type
    owned: bool = True


@dataclass(unsafe_hash=True)
class Optional(Type):
    """Nullable value (sum of T and nil).

    | Target | Representation |
    |--------|----------------|
    | C      | T* (NULL)      |
    | Go     | *T (nil)       |
    | Java   | Optional<T>    |
    | Python | T | None       |
    | Rust   | Option<T>      |
    | TS     | T | null       |

    Invariants:
    - inner is not Optional (no nested optionals)
    - inner is not Void
    """

    inner: Type


@dataclass(unsafe_hash=True)
class StructRef(Type):
    """Reference to a struct by name.

    Resolved by frontend; name must exist in Module.structs.
    """

    name: str


@dataclass(unsafe_hash=True)
class InterfaceRef(Type):
    """Reference to an interface by name.

    | Target | Representation      |
    |--------|---------------------|
    | C      | void* + vtable      |
    | Go     | InterfaceName       |
    | Java   | InterfaceName       |
    | Python | Protocol            |
    | Rust   | dyn Trait           |
    | TS     | InterfaceName       |

    Special names:
    - "any": Go any/interface{}, Python Any, Rust dyn Any, Java Object
    """

    name: str


@dataclass(unsafe_hash=True)
class Union(Type):
    """Closed discriminated union (sum type).

    All variants share a discriminant field (typically `kind: string`).

    | Target | Representation          |
    |--------|-------------------------|
    | C      | tagged union            |
    | Go     | interface + type switch |
    | Java   | sealed interface        |
    | Python | Union + @dataclass      |
    | Rust   | enum                    |
    | TS     | discriminated union     |

    Invariants:
    - len(variants) >= 2
    - all variants have compatible discriminant field
    """

    name: str
    variants: tuple[StructRef, ...]


@dataclass(unsafe_hash=True)
class FuncType(Type):
    """Function type (for function pointers, callbacks, closures).

    | Target | Representation            |
    |--------|---------------------------|
    | C      | R (*)(P...)               |
    | Go     | func(P...) R              |
    | Java   | @FunctionalInterface / λ  |
    | Python | Callable[[P...], R]       |
    | Rust   | fn(P...) -> R / Fn trait  |
    | TS     | (p: P...) => R            |

    Invariants:
    - ret is valid Type (use VOID for no return)
    - When captures=True and receiver is set, receiver contains the type of the
      bound object (typically Pointer(StructRef(class_name)))
    """

    params: tuple[Type, ...]
    ret: Type
    captures: bool = False  # True if closure (captures environment)
    receiver: Type | None = None  # Receiver type for bound methods


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
BYTES = Bytes()
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
    hierarchy_root: str | None = None  # Root interface for Node-like class hierarchies


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
    loc: Loc = field(default_factory=loc_unknown)
    is_exception: bool = False
    embedded_type: str | None = None  # Exception inheritance
    const_fields: dict[str, str] = field(default_factory=dict)


@dataclass
class Field:
    """Struct field.

    Invariants:
    - typ is fully resolved (no unresolved type variables)
    - If default is present, default.typ is assignable to typ

    Ownership semantics:
    - owned (default): Field owns its value; destroyed with struct
    - weak: Back-reference; does not own (prevents cycles)
    """

    name: str
    typ: Type
    default: Expr | None = None
    loc: Loc = field(default_factory=loc_unknown)
    # Ownership annotations (phase 14)
    ownership: Ownership = "owned"


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
    loc: Loc = field(default_factory=loc_unknown)


@dataclass
class MethodSig:
    """Method signature in an interface."""

    name: str
    params: list[Param]
    ret: Type
    loc: Loc = field(default_factory=loc_unknown)


@dataclass
class Enum:
    """Enumeration definition.

    | Target | Representation           |
    |--------|--------------------------|
    | C      | enum or #define          |
    | Go     | const iota or string     |
    | Java   | enum                     |
    | Python | Enum or StrEnum          |
    | Rust   | enum                     |
    | TS     | enum or union            |

    Invariants:
    - len(variants) >= 1
    - Variant names are unique
    """

    name: str
    variants: list[EnumVariant]
    loc: Loc = field(default_factory=loc_unknown)


@dataclass
class EnumVariant:
    """Single variant in an enumeration."""

    name: str
    value: int | str | None = None  # None = auto-assign
    loc: Loc = field(default_factory=loc_unknown)


@dataclass
class Export:
    """Module export declaration.

    Specifies which symbols are public API.
    """

    name: str
    kind: Literal["function", "struct", "constant", "interface", "enum"]
    loc: Loc = field(default_factory=loc_unknown)


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
    loc: Loc = field(default_factory=loc_unknown)
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
    - ownership: Does this param take ownership or borrow?

    Ownership semantics:
    - borrowed (default): Caller retains ownership; callee cannot store
    - owned: Ownership transfers to callee; caller must not use after call
    """

    name: str
    typ: Type
    default: Expr | None = None
    mutable: bool = False  # Rust: mut
    loc: Loc = field(default_factory=loc_unknown)
    # Middleend annotations
    is_modified: bool = False
    is_unused: bool = False
    # Ownership annotations (phase 14)
    ownership: Ownership = "borrowed"


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
    loc: Loc = field(default_factory=loc_unknown)


# ============================================================
# STATEMENTS
# ============================================================


@dataclass(kw_only=True)
class Stmt:
    """Base for all statements. Abstract."""

    loc: Loc = field(default_factory=loc_unknown)


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
    | C      | T x = v         | const T x = v |
    | Go     | var x T = v     | (same)        |
    | Java   | T x = v         | final T x = v |
    | Python | x = v           | x = v         |
    | Rust   | let mut x = v   | let x = v     |
    | TS     | let x = v       | const x = v   |

    Middleend annotations:
    - is_reassigned: Variable assigned again after declaration
    - is_const: Never reassigned (enables const/final emission)
    - initial_value_unused: Initial value overwritten before read
    - ownership: Who owns this value (owned/borrowed/shared)
    - region: Arena/region this value belongs to (None = default/stack)
    """

    name: str
    typ: Type
    value: Expr | None = None
    mutable: bool = True
    # Middleend annotations
    is_reassigned: bool = False
    is_const: bool = False
    initial_value_unused: bool = False
    # Ownership annotations (phase 14)
    ownership: Ownership = "owned"
    region: str | None = None


@dataclass
class Assign(Stmt):
    """Assignment to existing variable or location.

    Semantics: target := value

    Middleend annotations:
    - is_declaration: This is the first assignment (Python-style declaration)
    - decl_typ: Declared type (when different from value.typ, e.g. unified from branches)
    """

    target: LValue
    value: Expr
    # Middleend annotations
    is_declaration: bool = False
    decl_typ: "Type | None" = None


@dataclass
class TupleAssign(Stmt):
    """Multi-value assignment: a, b = expr

    Semantics: Destructure expr (tuple or multi-return) into targets.

    Invariants:
    - len(targets) matches arity of value.typ (Tuple or multi-return)

    Middleend annotations:
    - is_declaration: This is the first assignment (Python-style declaration)
    - unused_indices: Which targets are never used (for _ placeholders)
    """

    targets: list[LValue]
    value: Expr
    # Middleend annotations
    is_declaration: bool = False
    unused_indices: list[int] = field(default_factory=list)
    new_targets: list[str] = field(default_factory=list)


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
    | C      | switch on tag + cast              |
    | Go     | switch binding := expr.(type)     |
    | Java   | switch with instanceof patterns   |
    | Python | match with type guards            |
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
    binding_reassigned: bool = False
    hoisted_vars: list[tuple[str, Type]] = field(default_factory=list)


@dataclass
class TypeCase:
    """A case in a type switch.

    Invariants:
    - typ is a concrete type (not Union or any)
    """

    typ: Type
    body: list[Stmt]
    loc: Loc = field(default_factory=loc_unknown)


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
    loc: Loc = field(default_factory=loc_unknown)


@dataclass
class ForRange(Stmt):
    """Iterate over collection.

    Semantics:
    - For each (index, value) in iterable, execute body
    - index is None if unused
    - value is None if unused

    | Target | Representation                |
    |--------|-------------------------------|
    | C      | for (i=0; i<len; i++)         |
    | Go     | for i, v := range iterable    |
    | Java   | for (var v : iterable)        |
    | Python | for i, v in enumerate(iter)   |
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

    Middleend annotations:
    - no_scope: Block doesn't create a new scope (emitted without braces)
    """

    body: list[Stmt]
    # Middleend annotations
    no_scope: bool = False


@dataclass
class TryCatch(Stmt):
    """Exception handling.

    Semantics:
    - Execute body
    - If exception of catch_type is raised, bind to catch_var and execute catch_body
    - If reraise is True, catch_body re-raises after cleanup

    | Target | Representation                |
    |--------|-------------------------------|
    | C      | setjmp/longjmp or error codes |
    | Go     | defer/recover pattern         |
    | Java   | try/catch                     |
    | Python | try/except                    |
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
    has_returns: bool = False
    has_catch_returns: bool = False
    hoisted_vars: list[tuple[str, Type]] = field(default_factory=list)


@dataclass
class Raise(Stmt):
    """Raise exception.

    Semantics:
    - If reraise_var is set, re-raise that caught exception
    - Otherwise, create new exception of error_type with message and pos

    | Target | Representation          |
    |--------|-------------------------|
    | C      | longjmp or return error |
    | Go     | panic(Error{...})       |
    | Java   | throw new Exception(...)|
    | Python | raise Exception(...)    |
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

    | Target | Representation      |
    |--------|---------------------|
    | C      | return NULL         |
    | Go     | return nil          |
    | Java   | return Optional.empty() |
    | Python | return None         |
    | Rust   | return None         |
    | TS     | return null         |
    """


@dataclass
class Print(Stmt):
    """Print output.

    Semantics: Write value to stdout or stderr, with optional newline.

    | Target | newline=True         | newline=False       |
    |--------|----------------------|---------------------|
    | C      | printf("%s\\n", x)   | printf("%s", x)     |
    | Go     | fmt.Println(x)       | fmt.Print(x)        |
    | Java   | System.out.println(x)| System.out.print(x) |
    | Python | print(x)             | print(x, end='')    |
    | Rust   | println!("{}", x)    | print!("{}", x)     |
    | TS     | console.log(x)       | process.stdout.write|

    Invariants:
    - value.typ is STRING or convertible to string
    """

    value: Expr
    newline: bool = True
    stderr: bool = False


@dataclass
class EntryPoint(Stmt):
    """Program entry point marker.

    Semantics: Marks main() function with if __name__ == "__main__" guard.

    | Target | Representation                    |
    |--------|-----------------------------------|
    | C      | int main(int argc, char** argv)   |
    | Go     | func main()                       |
    | Java   | public static void main(String[]) |
    | Python | if __name__ == "__main__":        |
    | Rust   | fn main()                         |
    | TS     | (immediate execution)             |

    The function body is in the associated Function node.
    """

    function_name: str = "main"


# ============================================================
# EXPRESSIONS
#
# All expressions carry their resolved type (typ field).
# This is an invariant established by frontend phase 8.
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
    - escapes: This expression's value escapes its scope (stored in field, returned, etc.)
    """

    typ: Type
    loc: Loc = field(default_factory=loc_unknown)
    # Middleend annotations
    is_interface: bool = False
    narrowed_type: Type | None = None
    # Ownership annotations (phase 14)
    escapes: bool = False


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
    """Subslice: obj[low:high:step]

    Semantics: Extract subsequence from low (inclusive) to high (exclusive) with step.

    | Target | Representation              |
    |--------|-----------------------------|
    | C      | slice_range(obj, lo, hi, s) |
    | Go     | obj[lo:hi] (no step)        |
    | Java   | subList(lo, hi)             |
    | Python | obj[lo:hi:step]             |
    | Rust   | obj[lo..hi].step_by(s)      |
    | TS     | obj.slice(lo, hi)           |

    Invariants:
    - obj.typ is Slice, Array, or STRING
    - low.typ is INT if present
    - high.typ is INT if present
    - step.typ is INT if present
    - typ matches obj.typ (or Slice if obj is Array)
    """

    obj: Expr
    low: Expr | None = None
    high: Expr | None = None
    step: Expr | None = None


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
    | C      | Type_method(args)  |
    | Go     | Type.Method(args)  |
    | Java   | Type.method(args)  |
    | Rust   | Type::method(args) |
    | TS     | Type.method(args)  |
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
    | C      | len > 0 or x != NULL or x != 0    |
    | Go     | len(s) > 0 or x != nil or x != 0  |
    | Java   | !s.isEmpty() or x != null         |
    | Python | bool(x)                           |
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
    | C      | (T)x           |
    | Go     | T(x)           |
    | Java   | (T) x          |
    | Python | T(x)           |
    | Rust   | x as T         |
    | TS     | x as T         |

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
    | C      | tag check + cast    | (T*)x             |
    | Go     | x.(T) with ok check | x.(T) panic       |
    | Java   | instanceof + (T) x  | (T) x             |
    | Python | assert isinstance   | cast(T, x)        |
    | Rust   | downcast checked    | downcast unchecked|
    | TS     | x as T (with guard) | x as T            |

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
    | C      | x->tag == T_TAG          |
    | Go     | _, ok := x.(T)           |
    | Java   | x instanceof T           |
    | Python | isinstance(x, T)         |
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
    | C      | x == NULL                |
    | Go     | x == nil (or reflection) |
    | Java   | x == null                |
    | Python | x is None                |
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
    | C      | x.len          |
    | Go     | len(x)         |
    | Java   | x.size()       |
    | Python | len(x)         |
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
    | C      | arena_alloc(cap * sizeof(T))|
    | Go     | make([]T, len, cap)         |
    | Java   | new ArrayList<>(cap)        |
    | Python | []                          |
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
    | C      | hashmap_new()       |
    | Go     | make(map[K]V)       |
    | Java   | new HashMap<>()     |
    | Python | {}                  |
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
    | C      | (T[]){a, b, c}   |
    | Go     | []T{a, b, c}     |
    | Java   | List.of(a, b, c) |
    | Python | [a, b, c]        |
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

    | Target | Representation             |
    |--------|----------------------------|
    | C      | hashset_from(a, b, ...)    |
    | Go     | map[T]struct{}{a: {}, ...} |
    | Java   | Set.of(a, b)               |
    | Python | {a, b}                     |
    | Rust   | HashSet::from([a, b])      |
    | TS     | new Set([a, b])            |

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

    | Target | Representation            |
    |--------|---------------------------|
    | C      | (StructName){.f1=v1, ...} |
    | Go     | &StructName{f1: v1, ...}  |
    | Java   | new StructName(v1, ...)   |
    | Python | StructName(f1=v1, ...)    |
    | Rust   | StructName { f1: v1, ... }|
    | TS     | { f1: v1, ... } as T      |

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
    | C      | s.data[s.len-1]  |
    | Go     | s[len(s)-1]      |
    | Java   | s.get(s.size()-1)|
    | Python | s[-1]            |
    | Rust   | s.last()         |
    | TS     | s[s.length-1]    |

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
    | C      | utf8_char_at(s, i)        |
    | Go     | []rune(s)[i] or runes[i]  |
    | Java   | s.charAt(i)               |
    | Python | s[i]                      |
    | Rust   | s.chars().nth(i)          |
    | TS     | s.charAt(i) or s[i]       |

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
    | C      | utf8_char_count(s)  |
    | Go     | len([]rune(s))      |
    | Java   | s.length()          |
    | Python | len(s)              |
    | Rust   | s.chars().count()   |
    | TS     | s.length            |

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
    | C      | utf8_substring(s, lo, hi)   |
    | Go     | string([]rune(s)[lo:hi])    |
    | Java   | s.substring(lo, hi)         |
    | Python | s[lo:hi]                    |
    | Rust   | s.chars().skip(lo).take(hi-lo).collect() |
    | TS     | s.substring(lo, hi)         |

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
    | C      | str_concat(s1, s2, ...)   |
    | Go     | s1 + s2 + ... or builder  |
    | Java   | s1 + s2 or StringBuilder  |
    | Python | s1 + s2 or f-string       |
    | Rust   | format!("{}{}", s1, s2)   |
    | TS     | s1 + s2 or template       |

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
    | C      | snprintf(buf, tmpl, ...)|
    | Go     | fmt.Sprintf(tmpl, args) |
    | Java   | String.format(tmpl, ...)|
    | Python | f-string or .format()   |
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
    | C      | str_trim(s, chars, mode)              |
    | Go     | strings.TrimLeft/Right/Trim           |
    | Java   | regex or manual                       |
    | Python | s.lstrip/rstrip/strip(chars)          |
    | Rust   | s.trim_start_matches/trim_end_matches |
    | TS     | regex or manual                       |

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

    | Kind   | C           | Go                  | Java                      | Python       | Rust                 | TS          |
    |--------|-------------|---------------------|---------------------------|--------------|----------------------|-------------|
    | alnum  | isalnum(c)  | unicode.IsLetter || unicode.IsDigit | Character.isLetterOrDigit | c.isalnum()  | c.is_alphanumeric() | /\w/.test   |
    | digit  | isdigit(c)  | unicode.IsDigit     | Character.isDigit         | c.isdigit()  | c.is_ascii_digit()   | /\d/.test   |
    | alpha  | isalpha(c)  | unicode.IsLetter    | Character.isLetter        | c.isalpha()  | c.is_alphabetic()    | /[a-zA-Z]/  |
    | space  | isspace(c)  | unicode.IsSpace     | Character.isWhitespace    | c.isspace()  | c.is_whitespace()    | /\s/.test   |
    | upper  | isupper(c)  | unicode.IsUpper     | Character.isUpperCase     | c.isupper()  | c.is_uppercase()     | /[A-Z]/     |
    | lower  | islower(c)  | unicode.IsLower     | Character.isLowerCase     | c.islower()  | c.is_lowercase()     | /[a-z]/     |

    Invariants:
    - char.typ is CHAR or RUNE or STRING (single char)
    - typ is BOOL
    """

    kind: Literal["alnum", "digit", "alpha", "space", "upper", "lower"]
    char: Expr


# --- Numeric Conversion ---


@dataclass
class ParseInt(Expr):
    """Parse string to integer with specified base.

    | Target | Representation                      |
    |--------|-------------------------------------|
    | Go     | _parseInt(s, base) (helper)         |
    | Java   | (int) Long.parseLong(s, base)       |
    | Python | int(s, base)                        |
    | TS     | parseInt(s, base)                   |

    Invariants:
    - string.typ is STRING
    - base.typ is INT (typically IntLit 10 or 16)
    - typ is INT
    """

    string: Expr
    base: Expr


@dataclass
class IntToStr(Expr):
    """Convert integer to string.

    | Target | Representation            |
    |--------|---------------------------|
    | C      | snprintf(buf, "%lld", n)  |
    | Go     | strconv.Itoa(n)           |
    | Java   | String.valueOf(n)         |
    | Python | str(n)                    |
    | Rust   | n.to_string()             |
    | TS     | String(n) or n.toString() |

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

    | Target | Representation                             |
    |--------|---------------------------------------------|
    | C      | x == sentinel ? NULL : &x                  |
    | Go     | if x == sentinel { nil } else { x }        |
    | Java   | x == sentinel ? Optional.empty() : Optional.of(x) |
    | Python | None if x == sentinel else x               |
    | Rust   | if x == sentinel { None } else { Some(x) } |
    | TS     | x === sentinel ? null : x                  |

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
    | C      | &x             |
    | Go     | &x             |
    | Java   | x (reference)  |
    | Python | x (reference)  |
    | Rust   | &x or Box::new |
    | TS     | x (reference)  |

    Invariants:
    - operand is addressable (variable, field, index)
    - typ is Pointer(operand.typ)
    """

    operand: Expr


@dataclass
class WeakRef(Expr):
    """Create weak (non-owning) reference.

    Used for back-references in cyclic structures. The referenced
    value must outlive this reference.

    | Target | Representation  |
    |--------|-----------------|
    | C      | x (no refcount) |
    | Go     | (no change)     |
    | Java   | WeakReference<> |
    | Python | weakref.ref(x)  |
    | Rust   | Weak::new(&x)   |
    | TS     | WeakRef<>       |

    Invariants:
    - operand is addressable
    - typ is Pointer(operand.typ) or equivalent weak wrapper
    """

    operand: Expr


# --- I/O Expressions ---


@dataclass
class ReadLine(Expr):
    """Read line from stdin.

    Semantics: Read until newline or EOF. Returns empty string on EOF.

    | Target | Representation              |
    |--------|------------------------------|
    | C      | fgets(buf, size, stdin)      |
    | Go     | bufio.Scanner.Scan()         |
    | Java   | BufferedReader.readLine()    |
    | Python | sys.stdin.readline()         |
    | Rust   | stdin().read_line(&mut buf)  |
    | TS     | readline.question() sync     |

    Invariants:
    - typ is STRING
    """


@dataclass
class ReadAll(Expr):
    """Read all remaining input from stdin.

    Semantics: Read until EOF. Returns complete contents as string.

    | Target | Representation              |
    |--------|------------------------------|
    | C      | read() loop                  |
    | Go     | io.ReadAll(os.Stdin)         |
    | Java   | Scanner + StringBuilder      |
    | Python | sys.stdin.read()             |
    | Rust   | io::read_to_string(stdin())  |
    | TS     | fs.readFileSync(0, 'utf8')   |

    Invariants:
    - typ is STRING
    """


@dataclass
class ReadBytes(Expr):
    """Read all bytes from stdin.

    Semantics: Read binary data until EOF.

    | Target | Representation              |
    |--------|------------------------------|
    | C      | fread() loop                 |
    | Go     | io.ReadAll(os.Stdin)         |
    | Java   | InputStream.readAllBytes()   |
    | Python | sys.stdin.buffer.read()      |
    | Rust   | stdin().read_to_end(&mut v)  |
    | TS     | fs.readFileSync(0)           |

    Invariants:
    - typ is BYTES
    """


@dataclass
class ReadBytesN(Expr):
    """Read up to n bytes from stdin.

    Semantics: Read up to count bytes. May return fewer at EOF.

    | Target | Representation               |
    |--------|-------------------------------|
    | C      | fread(buf, 1, n, stdin)       |
    | Go     | io.ReadAtLeast(stdin, buf, n) |
    | Java   | InputStream.readNBytes(n)     |
    | Python | sys.stdin.buffer.read(n)      |
    | Rust   | stdin().take(n).read(&mut v)  |
    | TS     | manual Buffer allocation      |

    Invariants:
    - count.typ is INT
    - typ is BYTES
    """

    count: Expr


@dataclass
class WriteBytes(Expr):
    """Write bytes to stdout or stderr.

    Semantics: Write binary data. Returns count of bytes written.

    | Target | Representation               |
    |--------|-------------------------------|
    | C      | fwrite(data, 1, len, stdout)  |
    | Go     | os.Stdout.Write(data)         |
    | Java   | OutputStream.write(data)      |
    | Python | sys.stdout.buffer.write(data) |
    | Rust   | stdout().write_all(&data)     |
    | TS     | process.stdout.write(data)    |

    Invariants:
    - data.typ is BYTES
    - typ is INT (bytes written)
    """

    data: Expr
    stderr: bool = False


@dataclass
class Args(Expr):
    """Command-line arguments.

    Semantics: Program arguments as string slice. argv[0] is program name.

    | Target | Representation              |
    |--------|------------------------------|
    | C      | argv[0..argc]                |
    | Go     | os.Args                      |
    | Java   | args (empty string for [0])  |
    | Python | sys.argv                     |
    | Rust   | std::env::args().collect()   |
    | TS     | process.argv.slice(1)        |

    Invariants:
    - typ is Slice(STRING)
    """


@dataclass
class GetEnv(Expr):
    """Get environment variable.

    Semantics: Returns value or default (nil if no default).

    | Target | Representation                |
    |--------|-------------------------------|
    | C      | getenv(name)                  |
    | Go     | os.Getenv(name)               |
    | Java   | System.getenv(name)           |
    | Python | os.getenv(name, default)      |
    | Rust   | std::env::var(name).ok()      |
    | TS     | process.env[name]             |

    Invariants:
    - name.typ is STRING
    - typ is Optional(STRING) or STRING if default provided
    """

    name: Expr
    default: Expr | None = None


# --- Comprehensions ---


@dataclass
class ListComp(Expr):
    """List comprehension: [expr for target in iter if cond]

    Semantics: Build list by iterating and filtering.

    | Target | Representation                      |
    |--------|-------------------------------------|
    | C      | loop with array_push                |
    | Go     | for loop with append                |
    | Java   | stream().filter().map().collect()   |
    | Python | [expr for target in iter if cond]   |
    | Rust   | iter.filter().map().collect()       |
    | TS     | iter.filter().map() or loop         |

    Invariants:
    - iterable.typ is Slice, Array, or iterable
    - typ is Slice(element.typ)
    """

    element: Expr
    target: str
    iterable: Expr
    condition: Expr | None = None


@dataclass
class SetComp(Expr):
    """Set comprehension: {expr for target in iter if cond}

    Semantics: Build set by iterating and filtering.

    Invariants:
    - iterable.typ is Slice, Array, or iterable
    - typ is Set(element.typ)
    """

    element: Expr
    target: str
    iterable: Expr
    condition: Expr | None = None


@dataclass
class DictComp(Expr):
    """Dict comprehension: {key: value for target in iter if cond}

    Semantics: Build map by iterating and filtering.

    Invariants:
    - iterable.typ is Slice, Array, or iterable
    - typ is Map(key.typ, value.typ)
    """

    key: Expr
    value: Expr
    target: str
    iterable: Expr
    condition: Expr | None = None


# ============================================================
# LVALUES (Assignment Targets)
# ============================================================


@dataclass(kw_only=True)
class LValue:
    """Base for assignment targets. Abstract."""

    loc: Loc = field(default_factory=loc_unknown)


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
    # Maps field_name -> list of struct names that have this field (for Node subclasses)
    field_to_structs: dict[str, list[str]] = field(default_factory=dict)
    # Maps method_name -> struct name that has this method (for Node subclasses)
    method_to_structs: dict[str, str] = field(default_factory=dict)


@dataclass
class OwnershipInfo:
    """Ownership analysis results for a module (phase 14)."""

    # Variables that escape their scope
    escaping_vars: set[str] = field(default_factory=set)
    # Variables with ambiguous ownership (need runtime management)
    shared_vars: set[str] = field(default_factory=set)
    # Back-reference fields in structs: struct_name -> [field_names]
    weak_fields: dict[str, list[str]] = field(default_factory=dict)


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
