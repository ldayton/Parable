"""Type inference utilities extracted from frontend.py."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..ir import (
    BOOL,
    BYTE,
    FLOAT,
    INT,
    STRING,
    VOID,
    FuncInfo,
    FuncType,
    InterfaceRef,
    Map,
    Optional,
    Pointer,
    Set,
    Slice,
    StructRef,
    SymbolTable,
    Tuple,
    Type,
)

if TYPE_CHECKING:
    from .. import ir
    from .context import TypeContext

# Python type -> IR type mapping for primitives
TYPE_MAP: dict[str, Type] = {
    "str": STRING,
    "int": INT,
    "bool": BOOL,
    "float": FLOAT,
    "bytes": Slice(BYTE),
    "bytearray": Slice(BYTE),
}


def split_union_types(s: str) -> list[str]:
    """Split union types on | respecting nested brackets."""
    parts = []
    current: list[str] = []
    depth = 0
    for c in s:
        if c == "[":
            depth += 1
            current.append(c)
        elif c == "]":
            depth -= 1
            current.append(c)
        elif c == "|" and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(c)
    if current:
        parts.append("".join(current).strip())
    return parts


def extract_union_struct_names(py_type: str, node_types: set[str]) -> list[str] | None:
    """Extract struct names from a union type like 'Redirect | HereDoc'.
    Returns None if not a union of Node subclasses."""
    if " | " not in py_type:
        return None
    parts = split_union_types(py_type)
    if len(parts) <= 1:
        return None
    parts = [p for p in parts if p != "None"]
    if len(parts) <= 1:
        return None
    if not all(p in node_types for p in parts):
        return None
    return parts


def split_type_args(s: str) -> list[str]:
    """Split type arguments like 'K, V' respecting nested brackets."""
    parts = []
    current: list[str] = []
    depth = 0
    for c in s:
        if c == "[":
            depth += 1
            current.append(c)
        elif c == "]":
            depth -= 1
            current.append(c)
        elif c == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(c)
    if current:
        parts.append("".join(current).strip())
    return parts


def extract_struct_name(typ: Type) -> str | None:
    """Extract struct name from wrapped types like Pointer, Optional, etc."""
    if isinstance(typ, StructRef):
        return typ.name
    if isinstance(typ, Pointer):
        return extract_struct_name(typ.target)
    if isinstance(typ, Optional):
        return extract_struct_name(typ.inner)
    return None


def is_node_interface_type(typ: Type | None) -> bool:
    """Check if a type is the Node interface type."""
    if typ is None:
        return False
    # InterfaceRef("Node")
    if isinstance(typ, InterfaceRef) and typ.name == "Node":
        return True
    # StructRef("Node")
    if isinstance(typ, StructRef) and typ.name == "Node":
        return True
    return False


def is_node_subtype(typ: Type | None, node_types: set[str]) -> bool:
    """Check if a type is a Node subtype (pointer to struct implementing Node)."""
    if typ is None:
        return False
    # Check Pointer(StructRef(X)) where X is a Node subclass
    if isinstance(typ, Pointer) and isinstance(typ.target, StructRef):
        struct_name = typ.target.name
        if struct_name in node_types:
            return True
    return False


def is_node_subclass(name: str, symbols: SymbolTable) -> bool:
    """Check if a class is a Node subclass (directly or transitively)."""
    if name == "Node":
        return True
    info = symbols.structs.get(name)
    if not info:
        return False
    return any(is_node_subclass(base, symbols) for base in info.bases)


def parse_callable_type(
    py_type: str,
    concrete_nodes: bool,
    symbols: SymbolTable,
    node_types: set[str],
) -> Type:
    """Parse Callable[[], ReturnType] -> FuncType."""
    inner = py_type[9:-1]  # Remove "Callable[" and "]"
    parts = split_type_args(inner)
    if len(parts) >= 2:
        args_str = parts[0]
        ret_type = parts[-1]
        ret = py_type_to_ir(ret_type, symbols, node_types, concrete_nodes)
        # Handle empty args list "[]"
        if args_str == "[]":
            return FuncType(params=(), ret=ret)
        # Handle args list like "[int, str]"
        if args_str.startswith("[") and args_str.endswith("]"):
            args_inner = args_str[1:-1]
            if args_inner:
                param_types = tuple(
                    py_type_to_ir(a.strip(), symbols, node_types, concrete_nodes)
                    for a in args_inner.split(",")
                )
                return FuncType(params=param_types, ret=ret)
            return FuncType(params=(), ret=ret)
    return InterfaceRef("any")


def py_type_to_ir(
    py_type: str,
    symbols: SymbolTable,
    node_types: set[str],
    concrete_nodes: bool = False,
) -> Type:
    """Convert Python type string to IR Type."""
    if not py_type:
        return InterfaceRef("any")
    # Handle simple types
    if py_type in TYPE_MAP:
        return TYPE_MAP[py_type]
    # Handle bare "list" without type args
    if py_type == "list":
        return Slice(InterfaceRef("any"))
    # Handle bare "dict" without type args
    if py_type == "dict":
        return Map(STRING, InterfaceRef("any"))
    # Handle bare "set" without type args
    if py_type == "set":
        return Set(InterfaceRef("any"))
    # Handle X | None -> Optional[base type]
    if " | " in py_type:
        parts = split_union_types(py_type)
        if len(parts) > 1:
            parts = [p for p in parts if p != "None"]
            if len(parts) == 1:
                inner = py_type_to_ir(parts[0], symbols, node_types, concrete_nodes)
                # For Node | None, use Node interface (interfaces are nilable in Go)
                if parts[0] == "Node" or is_node_subclass(parts[0], symbols):
                    return InterfaceRef("Node")
                # For str | None, just use string (empty string represents None)
                if inner == STRING:
                    return STRING
                # For int | None, use int with -1 sentinel (handled elsewhere)
                if inner == INT:
                    return Optional(inner)
                return Optional(inner)
            # If all parts are Node subclasses, return Node interface (nilable)
            if all(is_node_subclass(p, symbols) for p in parts):
                return InterfaceRef("Node")
            return InterfaceRef("any")
    # Handle list[X]
    if py_type.startswith("list["):
        inner = py_type[5:-1]
        return Slice(py_type_to_ir(inner, symbols, node_types, concrete_nodes))
    # Handle dict[K, V]
    if py_type.startswith("dict["):
        inner = py_type[5:-1]
        parts = split_type_args(inner)
        if len(parts) == 2:
            return Map(
                py_type_to_ir(parts[0], symbols, node_types, concrete_nodes),
                py_type_to_ir(parts[1], symbols, node_types, concrete_nodes),
            )
    # Handle set[X]
    if py_type.startswith("set["):
        inner = py_type[4:-1]
        return Set(py_type_to_ir(inner, symbols, node_types, concrete_nodes))
    # Handle tuple[...] - parse element types for typed tuples
    if py_type.startswith("tuple["):
        inner = py_type[6:-1]
        parts = split_type_args(inner)
        elements = tuple(py_type_to_ir(p, symbols, node_types, concrete_nodes) for p in parts)
        return Tuple(elements)
    # Handle Callable
    if py_type.startswith("Callable["):
        return parse_callable_type(py_type, concrete_nodes, symbols, node_types)
    # Handle class names
    if py_type in symbols.structs:
        info = symbols.structs[py_type]
        if info.is_node or py_type == "Node":
            if concrete_nodes and py_type != "Node":
                return Pointer(StructRef(py_type))
            return InterfaceRef("Node")
        return Pointer(StructRef(py_type))
    # Known internal types
    if py_type in ("Token", "QuoteState", "ParseContext", "Lexer", "Parser"):
        return Pointer(StructRef(py_type))
    # Type aliases - union types of Node subtypes
    if py_type in ("ArithNode", "CondNode"):
        return InterfaceRef("Node")
    # Python builtin aliases
    if py_type == "bytearray":
        return Slice(BYTE)
    if py_type == "tuple":
        return InterfaceRef("any")
    # Type alias mappings
    if py_type == "CommandSub":
        return Pointer(StructRef("CommandSubstitution"))
    if py_type == "ProcessSub":
        return Pointer(StructRef("ProcessSubstitution"))
    # Unknown type - return as interface
    return InterfaceRef(py_type)


def py_return_type_to_ir(
    py_type: str,
    symbols: SymbolTable,
    node_types: set[str],
) -> Type:
    """Convert Python return type to IR, handling tuples as multiple returns."""
    if not py_type or py_type == "None":
        return VOID
    # Handle unions before tuple
    if " | " in py_type:
        parts = split_union_types(py_type)
        if len(parts) > 1:
            parts = [p for p in parts if p != "None"]
            if len(parts) == 1:
                return py_return_type_to_ir(parts[0], symbols, node_types)
            # Check if all parts are Node subclasses -> return Node interface
            if all(p in node_types for p in parts):
                return StructRef("Node")
            return InterfaceRef("any")
    # Handle tuple[...] specially for return types
    if py_type.startswith("tuple["):
        inner = py_type[6:-1]
        parts = split_type_args(inner)
        elements = tuple(py_type_to_ir(p, symbols, node_types, concrete_nodes=True) for p in parts)
        return Tuple(elements)
    # For non-tuples, use standard conversion with concrete node types
    return py_type_to_ir(py_type, symbols, node_types, concrete_nodes=True)


def infer_type_from_value(
    node: dict,
    param_types: dict[str, str],
    symbols: SymbolTable,
    node_types: set[str],
) -> Type:
    """Infer IR type from an expression."""
    from .ast_compat import is_type

    node_t = node.get("_type")
    if node_t == "Constant":
        value = node.get("value")
        if isinstance(value, bool):
            return BOOL
        if isinstance(value, int):
            return INT
        if isinstance(value, str):
            return STRING
        if value is None:
            return InterfaceRef("any")
    elif node_t == "List":
        elts = node.get("elts", [])
        if elts:
            return Slice(infer_type_from_value(elts[0], param_types, symbols, node_types))
        return Slice(InterfaceRef("any"))
    elif node_t == "Dict":
        values = node.get("values", [])
        if values and all(
            isinstance(v, dict) and v.get("_type") == "Constant" and isinstance(v.get("value"), str)
            for v in values
        ):
            return Map(STRING, STRING)
        return Map(STRING, InterfaceRef("any"))
    elif node_t == "Name":
        name = node.get("id")
        if name in param_types:
            return py_type_to_ir(param_types[name], symbols, node_types)
        if name in ("True", "False"):
            return BOOL
        if name == "None":
            return InterfaceRef("any")
    elif node_t == "Call":
        func = node.get("func")
        if is_type(func, "Name"):
            func_name = func.get("id")
            if func_name == "len":
                return INT
            if func_name in symbols.structs:
                info = symbols.structs[func_name]
                if info.is_node:
                    return InterfaceRef("Node")
                return Pointer(StructRef(func_name))
            if func_name == "QuoteState":
                return Pointer(StructRef("QuoteState"))
            if func_name == "ContextStack":
                return Pointer(StructRef("ContextStack"))
    elif node_t == "Attribute":
        value = node.get("value")
        if is_type(value, "Name"):
            class_name = value.get("id")
            if class_name in (
                "ParserStateFlags",
                "DolbraceState",
                "TokenType",
                "MatchedPairFlags",
                "WordCtx",
                "ParseContext",
            ):
                return INT
    return InterfaceRef("any")


def infer_iterable_type(
    node: dict,
    var_types: dict[str, Type],
    current_class_name: str,
    symbols: SymbolTable,
) -> Type:
    """Infer the type of an iterable expression."""
    from .ast_compat import is_type

    # self.field
    if is_type(node, "Attribute"):
        value = node.get("value")
        if is_type(value, "Name"):
            if value.get("id") == "self" and current_class_name:
                struct_info = symbols.structs.get(current_class_name)
                if struct_info:
                    field_info = struct_info.fields.get(node.get("attr"))
                    if field_info:
                        return field_info.typ
    # Variable reference
    if is_type(node, "Name"):
        name_id = node.get("id")
        if name_id in var_types:
            return var_types[name_id]
    return InterfaceRef("any")


def infer_container_type_from_ast(
    node: dict,
    symbols: SymbolTable,
    current_class_name: str,
    current_func_info: FuncInfo | None,
    var_types: dict[str, Type],
) -> Type:
    """Infer the type of a container expression from AST."""
    from .ast_compat import is_type

    if is_type(node, "Name"):
        name_id = node.get("id")
        if name_id in var_types:
            return var_types[name_id]
        # Check function parameters
        if current_func_info:
            for p in current_func_info.params:
                if p.name == name_id:
                    return p.typ
    elif is_type(node, "Attribute"):
        value = node.get("value")
        if is_type(value, "Name"):
            value_id = value.get("id")
            if value_id == "self" and current_class_name:
                struct_info = symbols.structs.get(current_class_name)
                if struct_info:
                    field_info = struct_info.fields.get(node.get("attr"))
                    if field_info:
                        return field_info.typ
            elif value_id in var_types:
                obj_type = var_types[value_id]
                struct_name = extract_struct_name(obj_type)
                if struct_name and struct_name in symbols.structs:
                    field_info = symbols.structs[struct_name].fields.get(node.get("attr"))
                    if field_info:
                        return field_info.typ
    return InterfaceRef("any")


def synthesize_field_type(
    obj_type: Type,
    field: str,
    symbols: SymbolTable,
) -> Type:
    """Look up field type from struct info."""
    # Handle Pointer(StructRef(...))
    if isinstance(obj_type, Pointer) and isinstance(obj_type.target, StructRef):
        struct_name = obj_type.target.name
        if struct_name in symbols.structs:
            field_info = symbols.structs[struct_name].fields.get(field)
            if field_info:
                return field_info.typ
    # Handle direct StructRef
    if isinstance(obj_type, StructRef):
        if obj_type.name in symbols.structs:
            field_info = symbols.structs[obj_type.name].fields.get(field)
            if field_info:
                return field_info.typ
    return InterfaceRef("any")


def synthesize_method_return_type(
    obj_type: Type,
    method: str,
    symbols: SymbolTable,
    node_types: set[str],
) -> Type:
    """Look up method return type from struct info."""
    # String methods that return string
    if obj_type == STRING and method in (
        "join",
        "replace",
        "lower",
        "upper",
        "strip",
        "lstrip",
        "rstrip",
        "format",
    ):
        return STRING
    # String methods that return int
    if obj_type == STRING and method in ("find", "rfind", "index", "rindex", "count"):
        return INT
    # String methods that return bool
    if obj_type == STRING and method in (
        "startswith",
        "endswith",
        "isdigit",
        "isalpha",
        "isalnum",
        "isspace",
    ):
        return BOOL
    # Node interface methods
    if is_node_interface_type(obj_type):
        if method in ("to_sexp", "ToSexp"):
            return STRING
        if method in ("get_kind", "GetKind"):
            return STRING
    # Extract struct name from various type wrappers
    struct_name = extract_struct_name(obj_type)
    if struct_name and struct_name in symbols.structs:
        method_info = symbols.structs[struct_name].methods.get(method)
        if method_info:
            return method_info.return_type
    return InterfaceRef("any")


def synthesize_index_type(obj_type: Type) -> Type:
    """Derive element type from indexing a container."""
    if isinstance(obj_type, Slice):
        return obj_type.element
    if isinstance(obj_type, Map):
        return obj_type.value
    if obj_type == STRING:
        return BYTE  # string[i] returns byte in Go
    return InterfaceRef("any")


def synthesize_type(
    expr: "ir.Expr",
    type_ctx: "TypeContext",
    current_func_info: FuncInfo | None,
    symbols: SymbolTable,
    node_types: set[str],
) -> Type:
    """Bottom-up type synthesis: compute type from expression structure."""
    from .. import ir

    # Literals have known types
    if isinstance(expr, (ir.IntLit, ir.FloatLit, ir.StringLit, ir.BoolLit)):
        return expr.typ
    # Variable lookup
    if isinstance(expr, ir.Var):
        if expr.name in type_ctx.var_types:
            return type_ctx.var_types[expr.name]
        # Check function parameters
        if current_func_info:
            for p in current_func_info.params:
                if p.name == expr.name:
                    return p.typ
    # Field access - look up field type
    if isinstance(expr, ir.FieldAccess):
        obj_type = synthesize_type(expr.obj, type_ctx, current_func_info, symbols, node_types)
        return synthesize_field_type(obj_type, expr.field, symbols)
    # Method call - look up return type
    if isinstance(expr, ir.MethodCall):
        obj_type = synthesize_type(expr.obj, type_ctx, current_func_info, symbols, node_types)
        return synthesize_method_return_type(obj_type, expr.method, symbols, node_types)
    # Index - derive element type
    if isinstance(expr, ir.Index):
        obj_type = synthesize_type(expr.obj, type_ctx, current_func_info, symbols, node_types)
        return synthesize_index_type(obj_type)
    return expr.typ


def infer_expr_type_from_ast(
    node: dict,
    type_ctx: "TypeContext",
    symbols: SymbolTable,
    current_func_info: FuncInfo | None,
    current_class_name: str,
    node_types: set[str],
) -> Type:
    """Infer the type of a Python AST expression without lowering it."""
    from .ast_compat import is_type, op_type

    node_t = node.get("_type")
    # Constant literals
    if node_t == "Constant":
        value = node.get("value")
        if isinstance(value, bool):
            return BOOL
        if isinstance(value, int):
            return INT
        if isinstance(value, str):
            return STRING
        if isinstance(value, float):
            return FLOAT
    # Variable lookup
    if node_t == "Name":
        name_id = node.get("id")
        if name_id in type_ctx.var_types:
            return type_ctx.var_types[name_id]
        # Check constants
        if name_id in symbols.constants:
            return symbols.constants[name_id]
        # Check function parameters
        if current_func_info:
            for p in current_func_info.params:
                if p.name == name_id:
                    return p.typ
    # Field access
    if node_t == "Attribute":
        value = node.get("value")
        if is_type(value, "Name") and value.get("id") == "self":
            field = node.get("attr")
            if current_class_name in symbols.structs:
                struct_info = symbols.structs[current_class_name]
                field_info = struct_info.fields.get(field)
                if field_info:
                    return field_info.typ
        else:
            # Field access on other objects - infer object type then look up field
            obj_type = infer_expr_type_from_ast(
                value, type_ctx, symbols, current_func_info, current_class_name, node_types
            )
            struct_name = extract_struct_name(obj_type)
            if struct_name and struct_name in symbols.structs:
                struct_info = symbols.structs[struct_name]
                field_info = struct_info.fields.get(node.get("attr"))
                if field_info:
                    return field_info.typ
    # Method call - look up return type
    if node_t == "Call":
        func = node.get("func")
        if is_type(func, "Attribute"):
            obj_type = infer_expr_type_from_ast(
                func.get("value"), type_ctx, symbols, current_func_info, current_class_name, node_types
            )
            return synthesize_method_return_type(obj_type, func.get("attr"), symbols, node_types)
        # Free function call - look up return type
        if is_type(func, "Name"):
            func_name = func.get("id")
            # Built-in functions
            if func_name == "len":
                return INT
            if func_name in ("int", "ord"):
                return INT
            if func_name in ("str", "chr"):
                return STRING
            if func_name == "bool":
                return BOOL
            # Constructor calls
            if func_name in symbols.structs:
                return Pointer(StructRef(func_name))
            # Regular function calls
            if func_name in symbols.functions:
                return symbols.functions[func_name].return_type
    # Subscript - derive element type from container
    if node_t == "Subscript":
        val_type = infer_expr_type_from_ast(
            node.get("value"), type_ctx, symbols, current_func_info, current_class_name, node_types
        )
        if val_type == STRING:
            return STRING  # string indexing returns string (after Cast)
        if isinstance(val_type, Slice):
            return val_type.element
        if isinstance(val_type, Map):
            return val_type.value
    # BinOp - infer type based on operator
    if node_t == "BinOp":
        op = op_type(node.get("op"))
        if op in ("BitAnd", "BitOr", "BitXor", "LShift", "RShift"):
            return INT
        if op in ("Add", "Sub", "Mult", "FloorDiv", "Mod"):
            left_type = infer_expr_type_from_ast(
                node.get("left"), type_ctx, symbols, current_func_info, current_class_name, node_types
            )
            right_type = infer_expr_type_from_ast(
                node.get("right"), type_ctx, symbols, current_func_info, current_class_name, node_types
            )
            if left_type == INT or right_type == INT:
                return INT
    return InterfaceRef("any")


def infer_call_return_type(
    node: dict,
    symbols: SymbolTable,
    type_ctx: "TypeContext",
    current_func_info: FuncInfo | None,
    current_class_name: str,
    node_types: set[str],
) -> Type:
    """Infer the return type of a function or method call."""
    from .ast_compat import is_type

    func = node.get("func")
    if is_type(func, "Attribute"):
        # Method call - look up return type
        obj_type = infer_expr_type_from_ast(
            func.get("value"), type_ctx, symbols, current_func_info, current_class_name, node_types
        )
        struct_name = extract_struct_name(obj_type)
        if struct_name and struct_name in symbols.structs:
            method_info = symbols.structs[struct_name].methods.get(func.get("attr"))
            if method_info:
                return method_info.return_type
    elif is_type(func, "Name"):
        # Free function call
        func_name = func.get("id")
        if func_name in symbols.functions:
            return symbols.functions[func_name].return_type
    return InterfaceRef("any")


def coerce(
    expr: "ir.Expr",
    from_type: Type,
    to_type: Type,
    type_ctx: "TypeContext",
    current_func_info: FuncInfo | None,
    symbols: SymbolTable,
    node_types: set[str],
) -> "ir.Expr":
    """Apply type coercions when synthesized type doesn't match expected."""
    from .. import ir

    # byte → string: wrap with string() cast
    if from_type == BYTE and to_type == STRING:
        return ir.Cast(expr=expr, to_type=STRING, typ=STRING, loc=expr.loc)
    # nil → string: convert to empty string
    if isinstance(expr, ir.NilLit) and to_type == STRING:
        return ir.StringLit(value="", typ=STRING, loc=expr.loc)
    # nil → Optional(T): update NilLit type for proper Go emission
    if isinstance(expr, ir.NilLit) and isinstance(to_type, Optional):
        expr.typ = to_type
        return expr
    # nil → nilable types: update NilLit type (interfaces, pointers, and slices are nilable in Go)
    if isinstance(expr, ir.NilLit) and isinstance(
        to_type, (InterfaceRef, StructRef, Pointer, Slice)
    ):
        expr.typ = to_type
        return expr
    # []interface{} → []T: use typed slice
    if isinstance(from_type, Slice) and isinstance(to_type, Slice):
        if from_type.element == InterfaceRef("any"):
            # Update the expression's type to the expected slice type
            expr.typ = to_type
            if isinstance(expr, ir.SliceLit):
                expr.element_type = to_type.element
        # []*Subtype → []Node: for Node interface covariance (Go slices aren't covariant)
        elif is_node_subtype(from_type.element, node_types) and is_node_interface_type(
            to_type.element
        ):
            expr.typ = to_type
            if isinstance(expr, ir.SliceLit):
                expr.element_type = to_type.element
    # Tuple coercion: coerce each element individually
    if isinstance(to_type, Tuple) and isinstance(expr, ir.TupleLit):
        new_elements = []
        for i, elem in enumerate(expr.elements):
            if i < len(to_type.elements):
                elem_from_type = synthesize_type(
                    elem, type_ctx, current_func_info, symbols, node_types
                )
                new_elements.append(
                    coerce(
                        elem,
                        elem_from_type,
                        to_type.elements[i],
                        type_ctx,
                        current_func_info,
                        symbols,
                        node_types,
                    )
                )
            else:
                new_elements.append(elem)
        expr.elements = new_elements
        expr.typ = to_type
    return expr
