"""Builder utilities extracted from frontend.py."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from ..ir import INT, Field, Function, Interface, Loc, Param, Pointer, Receiver, Struct, StructRef, VOID
from ..type_overrides import PARAM_TYPE_OVERRIDES

if TYPE_CHECKING:
    from .. import ir
    from ..ir import FuncInfo, StructInfo, SymbolTable, Type
    from .context import TypeContext


@dataclass
class BuilderCallbacks:
    """Callbacks for builder phase that need lowering/type conversion."""
    annotation_to_str: Callable[[ast.expr | None], str]
    py_type_to_ir: Callable[[str, bool], "Type"]
    py_return_type_to_ir: Callable[[str], "Type"]
    lower_expr: Callable[[ast.expr], "ir.Expr"]
    lower_stmts: Callable[[list[ast.stmt]], list["ir.Stmt"]]
    collect_var_types: Callable[[list[ast.stmt]], tuple[dict, dict, set, dict]]
    is_exception_subclass: Callable[[str], bool]
    extract_union_struct_names: Callable[[str], list[str]]
    loc_from_node: Callable[[ast.AST], "Loc"]
    # Set up class context before collect_var_types (sets _current_class_name, _current_func_info)
    setup_context: Callable[[str, "FuncInfo | None"], None]
    # Combined callback: set up type context then lower statements
    setup_and_lower_stmts: Callable[[str, "FuncInfo | None", "TypeContext", list[ast.stmt]], list["ir.Stmt"]]


def build_forwarding_constructor(
    class_name: str,
    parent_class: str,
    symbols: "SymbolTable",
) -> Function:
    """Build a forwarding constructor for exception subclasses with no __init__."""
    from .. import ir
    # Get parent class info to copy its parameters
    parent_info = symbols.structs.get(parent_class)
    if not parent_info:
        raise ValueError(f"Unknown parent class: {parent_class}")
    # Build parameters from parent's __init__ params
    params: list[Param] = []
    for param_name in parent_info.init_params:
        # Check for parameter type overrides
        typ = INT  # Default
        override_key = (f"New{class_name}", param_name)
        if override_key in PARAM_TYPE_OVERRIDES:
            typ = PARAM_TYPE_OVERRIDES[override_key]
        else:
            # Try parent constructor override
            parent_key = (f"New{parent_class}", param_name)
            if parent_key in PARAM_TYPE_OVERRIDES:
                typ = PARAM_TYPE_OVERRIDES[parent_key]
            else:
                # Get from parent's field type
                field_info = parent_info.fields.get(param_name)
                if field_info:
                    typ = field_info.typ
        params.append(Param(name=param_name, typ=typ, loc=Loc.unknown()))
    # Build body: return &ClassName{ParentClass{...}}
    # Use StructLit with embedded type
    body: list[ir.Stmt] = []
    # Create parent struct literal
    parent_lit = ir.StructLit(
        struct_name=parent_class,
        fields={param_name: ir.Var(name=param_name, typ=params[i].typ) for i, param_name in enumerate(parent_info.init_params)},
        typ=StructRef(parent_class),
    )
    # Create struct with embedded parent - typ=Pointer makes backend emit &
    struct_lit = ir.StructLit(
        struct_name=class_name,
        fields={},
        typ=Pointer(StructRef(class_name)),
        embedded_value=parent_lit,
    )
    # Return pointer to struct
    ret = ir.Return(value=struct_lit)
    body.append(ret)
    return Function(
        name=f"New{class_name}",
        params=params,
        ret=Pointer(StructRef(class_name)),
        body=body,
        loc=Loc.unknown(),
    )


def build_constructor(
    class_name: str,
    init_ast: ast.FunctionDef,
    info: "StructInfo",
    callbacks: BuilderCallbacks,
) -> Function:
    """Build a NewXxx constructor function from __init__ AST."""
    from .. import ir
    from .context import TypeContext
    # Build parameters (same as __init__ excluding self)
    params: list[Param] = []
    param_types: dict[str, "Type"] = {}
    for arg in init_ast.args.args:
        if arg.arg == "self":
            continue
        py_type = callbacks.annotation_to_str(arg.annotation) if arg.annotation else ""
        typ = callbacks.py_type_to_ir(py_type, False) if py_type else Interface("any")
        # Check for parameter type overrides
        override_key = (f"New{class_name}", arg.arg)
        if override_key in PARAM_TYPE_OVERRIDES:
            typ = PARAM_TYPE_OVERRIDES[override_key]
        else:
            # Try __init__ param overrides
            override_key = ("__init__", arg.arg)
            if override_key in PARAM_TYPE_OVERRIDES:
                typ = PARAM_TYPE_OVERRIDES[override_key]
        params.append(Param(name=arg.arg, typ=typ, loc=Loc.unknown()))
        param_types[arg.arg] = typ
    # Handle default arguments
    n_params = len(params)
    n_defaults = len(init_ast.args.defaults) if init_ast.args.defaults else 0
    for i, default_ast in enumerate(init_ast.args.defaults or []):
        param_idx = n_params - n_defaults + i
        if 0 <= param_idx < n_params:
            params[param_idx].default = callbacks.lower_expr(default_ast)
    # Set up context first (needed by collect_var_types)
    callbacks.setup_context(class_name, None)
    # Collect variable types and build type context
    var_types, tuple_vars, sentinel_ints, list_element_unions = callbacks.collect_var_types(init_ast.body)
    var_types.update(param_types)
    var_types["self"] = Pointer(StructRef(class_name))
    type_ctx = TypeContext(
        return_type=Pointer(StructRef(class_name)),
        var_types=var_types,
        tuple_vars=tuple_vars,
        sentinel_ints=sentinel_ints,
        list_element_unions=list_element_unions,
    )
    # Build constructor body:
    # 1. self := &ClassName{}
    # 2. ... __init__ body statements ...
    # 3. return self
    body: list[ir.Stmt] = []
    # Create self = &ClassName{}
    self_init = ir.Assign(
        target=ir.VarLV(name="self", loc=Loc.unknown()),
        value=ir.StructLit(
            struct_name=class_name,
            fields={},
            typ=Pointer(StructRef(class_name)),
            loc=Loc.unknown(),
        ),
        loc=Loc.unknown(),
    )
    self_init.is_declaration = True
    body.append(self_init)
    # Lower __init__ body with type context (excluding any "return" statements which are implicit in __init__)
    init_body = callbacks.setup_and_lower_stmts(class_name, None, type_ctx, init_ast.body)
    body.extend(init_body)
    # Return self
    body.append(ir.Return(
        value=ir.Var(name="self", typ=Pointer(StructRef(class_name)), loc=Loc.unknown()),
        loc=Loc.unknown(),
    ))
    return Function(
        name=f"New{class_name}",
        params=params,
        ret=Pointer(StructRef(class_name)),
        body=body,
        loc=Loc.unknown(),
    )


def build_method_shell(
    node: ast.FunctionDef,
    class_name: str,
    symbols: "SymbolTable",
    callbacks: BuilderCallbacks,
    with_body: bool = False,
) -> Function:
    """Build IR Function for a method. Set with_body=True to lower statements."""
    from .context import TypeContext
    info = symbols.structs.get(class_name)
    func_info = info.methods.get(node.name) if info else None
    params = []
    if func_info:
        for p in func_info.params:
            params.append(
                Param(name=p.name, typ=p.typ, default=p.default_value, loc=Loc.unknown())
            )
    body: list["ir.Stmt"] = []
    if with_body:
        # Set up context first (needed by collect_var_types)
        callbacks.setup_context(class_name, func_info)
        # Collect variable types from body and add parameters + self
        var_types, tuple_vars, sentinel_ints, list_element_unions = callbacks.collect_var_types(node.body)
        if func_info:
            for p in func_info.params:
                var_types[p.name] = p.typ
        var_types["self"] = Pointer(StructRef(class_name))
        # Extract union types from parameter annotations
        union_types: dict[str, list[str]] = {}
        non_self_args = [a for a in node.args.args if a.arg != "self"]
        for arg in non_self_args:
            if arg.annotation:
                py_type = callbacks.annotation_to_str(arg.annotation)
                structs = callbacks.extract_union_struct_names(py_type)
                if structs:
                    union_types[arg.arg] = structs
        type_ctx = TypeContext(
            return_type=func_info.return_type if func_info else VOID,
            var_types=var_types,
            tuple_vars=tuple_vars,
            sentinel_ints=sentinel_ints,
            union_types=union_types,
            list_element_unions=list_element_unions,
        )
        body = callbacks.setup_and_lower_stmts(class_name, func_info, type_ctx, node.body)
    return Function(
        name=node.name,
        params=params,
        ret=func_info.return_type if func_info else VOID,
        body=body,
        receiver=Receiver(
            name="self",
            typ=StructRef(class_name),
            pointer=True,
        ),
        loc=callbacks.loc_from_node(node),
    )


def build_function_shell(
    node: ast.FunctionDef,
    symbols: "SymbolTable",
    callbacks: BuilderCallbacks,
    with_body: bool = False,
) -> Function:
    """Build IR Function from AST. Set with_body=True to lower statements."""
    from .context import TypeContext
    func_info = symbols.functions.get(node.name)
    params = []
    if func_info:
        for p in func_info.params:
            params.append(
                Param(name=p.name, typ=p.typ, default=p.default_value, loc=Loc.unknown())
            )
    body: list["ir.Stmt"] = []
    if with_body:
        # Set up context first (needed by collect_var_types) - empty class name for functions
        callbacks.setup_context("", func_info)
        # Collect variable types from body and add parameters
        var_types, tuple_vars, sentinel_ints, list_element_unions = callbacks.collect_var_types(node.body)
        if func_info:
            for p in func_info.params:
                var_types[p.name] = p.typ
        # Extract union types from parameter annotations
        union_types: dict[str, list[str]] = {}
        non_self_args = [a for a in node.args.args if a.arg != "self"]
        for arg in non_self_args:
            if arg.annotation:
                py_type = callbacks.annotation_to_str(arg.annotation)
                structs = callbacks.extract_union_struct_names(py_type)
                if structs:
                    union_types[arg.arg] = structs
        type_ctx = TypeContext(
            return_type=func_info.return_type if func_info else VOID,
            var_types=var_types,
            tuple_vars=tuple_vars,
            sentinel_ints=sentinel_ints,
            union_types=union_types,
            list_element_unions=list_element_unions,
        )
        body = callbacks.setup_and_lower_stmts("", func_info, type_ctx, node.body)
    return Function(
        name=node.name,
        params=params,
        ret=func_info.return_type if func_info else VOID,
        body=body,
        loc=callbacks.loc_from_node(node),
    )


def build_struct(
    node: ast.ClassDef,
    symbols: "SymbolTable",
    callbacks: BuilderCallbacks,
    with_body: bool = False,
) -> tuple[Struct | None, Function | None]:
    """Build IR Struct from class definition. Returns (struct, constructor_func)."""
    # Node is emitted as InterfaceDef, not Struct
    if node.name == "Node":
        return None, None
    info = symbols.structs.get(node.name)
    if not info:
        return None, None
    # Build fields
    fields = []
    for name, field_info in info.fields.items():
        fields.append(
            Field(
                name=name,
                typ=field_info.typ,
                loc=Loc.unknown(),
            )
        )
    # Build methods
    methods = []
    init_ast: ast.FunctionDef | None = None
    for stmt in node.body:
        if isinstance(stmt, ast.FunctionDef):
            if stmt.name == "__init__":
                init_ast = stmt
            else:
                method = build_method_shell(stmt, node.name, symbols, callbacks, with_body=with_body)
                methods.append(method)
    implements = []
    if info.is_node:
        implements.append("Node")
    # Determine embedded type for exception inheritance
    embedded_type = None
    if info.is_exception and info.bases:
        base = info.bases[0]
        if base != "Exception" and callbacks.is_exception_subclass(base):
            embedded_type = base
    struct = Struct(
        name=node.name,
        fields=fields,
        methods=methods,
        implements=implements,
        loc=callbacks.loc_from_node(node),
        is_exception=info.is_exception,
        embedded_type=embedded_type,
    )
    # Generate constructor function if needed
    ctor_func: Function | None = None
    if with_body and info.needs_constructor and init_ast:
        ctor_func = build_constructor(node.name, init_ast, info, callbacks)
    elif with_body and info.needs_constructor and embedded_type and not init_ast:
        # Exception subclass with no __init__ - forward to parent constructor
        ctor_func = build_forwarding_constructor(node.name, embedded_type, symbols)
    return struct, ctor_func
