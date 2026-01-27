"""Transpiler IR - Language-agnostic intermediate representation.

Architecture:
    parable.py -> [Python AST] -> Frontend -> [IR] -> Backend -> target code

The frontend handles all analysis (types, scopes, patterns, symbols).
Backends handle only syntax emission - no analysis.
Middleend annotations are added dynamically at runtime, not defined here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# ============================================================
# SOURCE LOCATIONS
# ============================================================


@dataclass(frozen=True)
class Loc:
    """Source location for error messages and source maps."""

    line: int  # 1-indexed
    col: int  # 0-indexed
    end_line: int
    end_col: int

    @classmethod
    def unknown(cls) -> Loc:
        return cls(0, 0, 0, 0)


# ============================================================
# TYPES
# ============================================================


@dataclass(frozen=True)
class Type:
    """Base for all types."""


@dataclass(frozen=True)
class Primitive(Type):
    """Primitive types: string, int, bool, float, byte, rune, void."""

    kind: Literal["string", "int", "bool", "float", "byte", "rune", "void"]


@dataclass(frozen=True)
class Slice(Type):
    """Growable sequence. Go: []T, JS: Array, Rust: Vec<T>."""

    element: Type


@dataclass(frozen=True)
class Array(Type):
    """Fixed-size array. Go: [N]T, Rust: [T; N]."""

    element: Type
    size: int


@dataclass(frozen=True)
class Map(Type):
    """Map/dictionary. Go: map[K]V, Rust: HashMap<K,V>."""

    key: Type
    value: Type


@dataclass(frozen=True)
class Set(Type):
    """Set. Go: map[T]bool, JS: Set<T>, Rust: HashSet<T>."""

    element: Type


@dataclass(frozen=True)
class Tuple(Type):
    """Fixed-size heterogeneous sequence. Go: multiple returns, TS: [T1, T2]."""

    elements: tuple[Type, ...]


@dataclass(frozen=True)
class Pointer(Type):
    """Pointer with ownership tracking for Rust/C."""

    target: Type
    owned: bool = True


@dataclass(frozen=True)
class Optional(Type):
    """Nullable value. Go: *T/nil, JS: T|null, Rust: Option<T>."""

    inner: Type


@dataclass(frozen=True)
class StructRef(Type):
    """Reference to a defined struct by name."""

    name: str


@dataclass(frozen=True)
class Interface(Type):
    """Dynamic dispatch interface. Go: interface, Rust: dyn Trait."""

    name: str  # "Node", "any"


@dataclass(frozen=True)
class Union(Type):
    """Sum type. Go: interface, Rust: enum.

    All unions are closed (fixed variants) and discriminated via .kind field.
    """

    name: str
    variants: tuple[StructRef, ...]


@dataclass(frozen=True)
class FuncType(Type):
    """Function pointer or closure."""

    params: tuple[Type, ...]
    ret: Type
    captures: bool = False


@dataclass(frozen=True)
class StringSlice(Type):
    """Borrowed string slice. Go: string, Rust: &str."""


# Singleton types
STRING = Primitive("string")
INT = Primitive("int")
BOOL = Primitive("bool")
FLOAT = Primitive("float")
BYTE = Primitive("byte")
RUNE = Primitive("rune")
VOID = Primitive("void")


# ============================================================
# TOP-LEVEL DECLARATIONS
# ============================================================


@dataclass
class Module:
    """A complete transpilation unit."""

    name: str
    doc: str | None = None
    structs: list[Struct] = field(default_factory=list)
    interfaces: list[InterfaceDef] = field(default_factory=list)
    functions: list[Function] = field(default_factory=list)
    constants: list[Constant] = field(default_factory=list)


@dataclass
class Struct:
    """Struct/class definition."""

    name: str
    doc: str | None = None
    fields: list[Field] = field(default_factory=list)
    methods: list[Function] = field(default_factory=list)
    implements: list[str] = field(default_factory=list)  # interface names
    loc: Loc = field(default_factory=Loc.unknown)
    is_exception: bool = False
    embedded_type: str | None = None  # For exception inheritance (e.g., "ParseError")


@dataclass
class Field:
    """Struct field."""

    name: str
    typ: Type
    default: Expr | None = None
    loc: Loc = field(default_factory=Loc.unknown)


@dataclass
class InterfaceDef:
    """Interface definition."""

    name: str
    methods: list[MethodSig] = field(default_factory=list)
    loc: Loc = field(default_factory=Loc.unknown)


@dataclass
class MethodSig:
    """Method signature in an interface."""

    name: str
    params: list[Param]
    ret: Type
    loc: Loc = field(default_factory=Loc.unknown)


@dataclass
class Function:
    """Function or method definition."""

    name: str
    params: list[Param]
    ret: Type
    body: list[Stmt]
    doc: str | None = None
    receiver: Receiver | None = None  # for methods
    fallible: bool = False  # can raise ParseError
    loc: Loc = field(default_factory=Loc.unknown)


@dataclass
class Receiver:
    """Method receiver (self)."""

    name: str  # "self", "p", etc.
    typ: StructRef
    mutable: bool = False  # Rust: &mut self
    pointer: bool = True  # Go: *T receiver


@dataclass
class Param:
    """Function parameter."""

    name: str
    typ: Type
    default: Expr | None = None
    mutable: bool = False  # Rust: mut
    loc: Loc = field(default_factory=Loc.unknown)


@dataclass
class Constant:
    """Module-level constant."""

    name: str
    typ: Type
    value: Expr
    loc: Loc = field(default_factory=Loc.unknown)


# ============================================================
# STATEMENTS
# ============================================================


@dataclass(kw_only=True)
class Stmt:
    """Base for all statements."""

    loc: Loc = field(default_factory=Loc.unknown)


@dataclass
class VarDecl(Stmt):
    """Variable declaration with optional initializer."""

    name: str
    typ: Type
    value: Expr | None = None
    mutable: bool = True  # JS: let/const, Rust: let/let mut


@dataclass
class Assign(Stmt):
    """Assignment statement."""

    target: LValue
    value: Expr


@dataclass
class TupleAssign(Stmt):
    """Multi-value assignment: a, b = func()"""

    targets: list[LValue]
    value: Expr


@dataclass
class OpAssign(Stmt):
    """Compound assignment: +=, -=, etc."""

    target: LValue
    op: str  # "+", "-", "*", "/", etc.
    value: Expr


@dataclass
class ExprStmt(Stmt):
    """Expression as statement (for side effects)."""

    expr: Expr


@dataclass
class Return(Stmt):
    """Return statement."""

    value: Expr | None = None


@dataclass
class If(Stmt):
    """If statement with optional else."""

    cond: Expr
    then_body: list[Stmt]
    else_body: list[Stmt] = field(default_factory=list)
    init: VarDecl | None = None  # Go: if x := ...; cond { }


@dataclass
class TypeSwitch(Stmt):
    """Switch on runtime type. isinstance -> TypeSwitch in frontend."""

    expr: Expr
    binding: str  # variable name bound to narrowed type in each case
    cases: list[TypeCase] = field(default_factory=list)
    default: list[Stmt] = field(default_factory=list)


@dataclass
class TypeCase:
    """A case in a type switch."""

    typ: Type
    body: list[Stmt]
    loc: Loc = field(default_factory=Loc.unknown)


@dataclass
class Match(Stmt):
    """Value matching (switch/case)."""

    expr: Expr
    cases: list[MatchCase] = field(default_factory=list)
    default: list[Stmt] = field(default_factory=list)


@dataclass
class MatchCase:
    """A case in a match statement."""

    patterns: list[Expr]  # multiple values can share body
    body: list[Stmt]
    loc: Loc = field(default_factory=Loc.unknown)


@dataclass
class ForRange(Stmt):
    """Iterate over collection."""

    index: str | None  # None if unused
    value: str | None  # None if unused
    iterable: Expr
    body: list[Stmt]


@dataclass
class ForClassic(Stmt):
    """C-style for loop."""

    init: Stmt | None
    cond: Expr | None
    post: Stmt | None
    body: list[Stmt]


@dataclass
class While(Stmt):
    """While loop."""

    cond: Expr
    body: list[Stmt]


@dataclass
class Break(Stmt):
    """Break statement."""

    label: str | None = None


@dataclass
class Continue(Stmt):
    """Continue statement."""

    label: str | None = None


@dataclass
class Block(Stmt):
    """Scoped block."""

    body: list[Stmt]


@dataclass
class TryCatch(Stmt):
    """Backtracking for error recovery. Go: defer/recover, JS: try/catch."""

    body: list[Stmt]
    catch_var: str | None = None  # None if error ignored
    catch_body: list[Stmt] = field(default_factory=list)
    reraise: bool = False  # catch cleans up then re-raises


@dataclass
class Raise(Stmt):
    """Raise error in fallible function. Go: panic, JS: throw."""

    error_type: str  # "ParseError", "MatchedPairError"
    message: Expr
    pos: Expr


@dataclass
class SoftFail(Stmt):
    """Return None to signal 'try alternative'. Go: return nil."""


# ============================================================
# EXPRESSIONS
# ============================================================


@dataclass(kw_only=True)
class Expr:
    """Base for all expressions. All expressions carry their resolved type."""

    typ: Type
    loc: Loc = field(default_factory=Loc.unknown)


@dataclass
class IntLit(Expr):
    """Integer literal."""

    value: int


@dataclass
class FloatLit(Expr):
    """Float literal."""

    value: float


@dataclass
class StringLit(Expr):
    """String literal."""

    value: str


@dataclass
class BoolLit(Expr):
    """Boolean literal."""

    value: bool


@dataclass
class NilLit(Expr):
    """Nil/null/None literal."""


@dataclass
class Var(Expr):
    """Variable reference."""

    name: str


@dataclass
class FieldAccess(Expr):
    """Field access: obj.field."""

    obj: Expr
    field: str
    through_pointer: bool = False  # Go auto-deref


@dataclass
class Index(Expr):
    """Array/slice/map indexing: obj[index]."""

    obj: Expr
    index: Expr
    bounds_check: bool = True
    returns_optional: bool = False  # Go map returns (v, ok)


@dataclass
class SliceExpr(Expr):
    """Subslice: obj[low:high]."""

    obj: Expr
    low: Expr | None = None
    high: Expr | None = None


@dataclass
class Call(Expr):
    """Free function call."""

    func: str
    args: list[Expr]


@dataclass
class MethodCall(Expr):
    """Method call with resolved receiver."""

    obj: Expr
    method: str
    args: list[Expr]
    receiver_type: Type  # resolved by frontend


@dataclass
class StaticCall(Expr):
    """Static method / associated function. Rust: Type::method()."""

    on_type: Type
    method: str
    args: list[Expr]


@dataclass
class BinaryOp(Expr):
    """Binary operation: left op right."""

    op: str  # "+", "-", "==", "&&", "||", etc.
    left: Expr
    right: Expr


@dataclass
class UnaryOp(Expr):
    """Unary operation: op operand."""

    op: str  # "-", "!", "~", "&", "*"
    operand: Expr


@dataclass
class Ternary(Expr):
    """Ternary conditional. Go lacks this, backend must emit IIFE or lift."""

    cond: Expr
    then_expr: Expr
    else_expr: Expr


@dataclass
class Cast(Expr):
    """Type conversion. Go: T(x), Rust: x as T."""

    expr: Expr
    to_type: Type


@dataclass
class TypeAssert(Expr):
    """Runtime type assertion. Go: x.(T), Rust: downcast."""

    expr: Expr
    asserted: Type
    safe: bool = True  # false = panic on failure


@dataclass
class IsType(Expr):
    """Type test. Go: _, ok := x.(T), JS: instanceof."""

    expr: Expr
    tested_type: Type


@dataclass
class IsNil(Expr):
    """Explicit nil check. Go: x == nil, Rust: x.is_none()."""

    expr: Expr
    negated: bool = False  # true for "!= nil"


@dataclass
class Len(Expr):
    """Length. Go: len(), JS: .length, Rust: .len()."""

    expr: Expr


@dataclass
class MakeSlice(Expr):
    """Allocate slice. Go: make([]T, len, cap), Rust: Vec::with_capacity."""

    element_type: Type
    length: Expr | None = None
    capacity: Expr | None = None


@dataclass
class MakeMap(Expr):
    """Allocate map. Go: make(map[K]V), Rust: HashMap::new()."""

    key_type: Type
    value_type: Type


@dataclass
class SliceLit(Expr):
    """Slice literal. Go: []T{...}, JS: [...], Rust: vec![...]."""

    element_type: Type
    elements: list[Expr]


@dataclass
class MapLit(Expr):
    """Map literal."""

    key_type: Type
    value_type: Type
    entries: list[tuple[Expr, Expr]]


@dataclass
class SetLit(Expr):
    """Set literal. Go: map[T]bool{...}, JS: new Set([...])."""

    element_type: Type
    elements: list[Expr]


@dataclass
class TupleLit(Expr):
    """Tuple literal. Go: anonymous struct or multiple values."""

    elements: list[Expr]


@dataclass
class StructLit(Expr):
    """Struct instantiation."""

    struct_name: str
    fields: dict[str, Expr]


@dataclass
class StringConcat(Expr):
    """String concatenation. Go: +, Rust: format!."""

    parts: list[Expr]


@dataclass
class StringFormat(Expr):
    """Format string. Go: fmt.Sprintf, Rust: format!."""

    template: str
    args: list[Expr]


# ============================================================
# LVALUES (Assignment Targets)
# ============================================================


@dataclass(kw_only=True)
class LValue:
    """Base for assignment targets."""

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
    is_node: bool = False  # True if implements Node interface
    is_exception: bool = False  # True if inherits from Exception
    bases: list[str] = field(default_factory=list)
    init_params: list[str] = field(default_factory=list)  # __init__ param order
    param_to_field: dict[str, str] = field(default_factory=dict)  # Maps param name to field name
    needs_constructor: bool = False  # True if __init__ has computed initializations
    const_fields: dict[str, str] = field(default_factory=dict)  # Constant field initializations (e.g., self.kind = "operator")


@dataclass
class FieldInfo:
    """Metadata about a field."""

    name: str
    typ: Type
    py_name: str = ""  # original Python name


@dataclass
class FuncInfo:
    """Metadata about a function or method."""

    name: str
    params: list[ParamInfo] = field(default_factory=list)
    return_type: Type = VOID
    is_method: bool = False
    receiver_type: str = ""  # struct name for methods


@dataclass
class ParamInfo:
    """Metadata about a parameter."""

    name: str
    typ: Type
    has_default: bool = False
    default_value: "Expr | None" = None  # IR expression for default value
