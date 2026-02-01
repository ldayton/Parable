"""Builder utilities extracted from frontend.py."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from .ast_compat import ASTNode, is_type

from ..ir import (
    INT,
    Constant,
    Field,
    Function,
    InterfaceDef,
    InterfaceRef,
    Loc,
    MethodSig,
    Module,
    Param,
    Pointer,
    Receiver,
    STRING,
    Struct,
    StructRef,
    VOID,
    loc_unknown,
)
from ..type_overrides import MODULE_CONSTANTS

if TYPE_CHECKING:
    from .. import ir
    from ..ir import FuncInfo, StructInfo, SymbolTable, Type
    from .context import TypeContext


@dataclass
class BuilderCallbacks:
    """Callbacks for builder phase that need lowering/type conversion."""

    annotation_to_str: Callable[[ASTNode | None], str]
    py_type_to_ir: Callable[[str, bool], "Type"]
    py_return_type_to_ir: Callable[[str], "Type"]
    lower_expr: Callable[[ASTNode], "ir.Expr"]
    lower_stmts: Callable[[list[ASTNode]], list["ir.Stmt"]]
    collect_var_types: Callable[[list[ASTNode]], tuple[dict, dict, set, dict]]
    is_exception_subclass: Callable[[str], bool]
    extract_union_struct_names: Callable[[str], list[str]]
    loc_from_node: Callable[[ASTNode], "Loc"]
    # Set up class context before collect_var_types (sets _current_class_name, _current_func_info)
    setup_context: Callable[[str, "FuncInfo | None"], None]
    # Combined callback: set up type context then lower statements
    setup_and_lower_stmts: Callable[
        [str, "FuncInfo | None", "TypeContext", list[ASTNode]], list["ir.Stmt"]
    ]


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
        # Get from parent's field type
        typ = INT  # Default
        field_info = parent_info.fields.get(param_name)
        if field_info:
            typ = field_info.typ
        params.append(Param(name=param_name, typ=typ, loc=loc_unknown()))
    # Build body: return &ClassName{ParentClass{...}}
    # Use StructLit with embedded type
    body: list[ir.Stmt] = []
    # Create parent struct literal
    parent_lit = ir.StructLit(
        struct_name=parent_class,
        fields={
            param_name: ir.Var(name=param_name, typ=params[i].typ)
            for i, param_name in enumerate(parent_info.init_params)
        },
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
        loc=loc_unknown(),
    )


def build_constructor(
    class_name: str,
    init_ast: ASTNode,
    info: "StructInfo",
    callbacks: BuilderCallbacks,
) -> Function:
    """Build a NewXxx constructor function from __init__ AST."""
    from .. import ir
    from .context import TypeContext

    # Build parameters (same as __init__ excluding self)
    params: list[Param] = []
    param_types: dict[str, "Type"] = {}
    init_args = init_ast.get("args", {})
    init_args_args = init_args.get("args", []) if isinstance(init_args, dict) else []
    for arg in init_args_args:
        arg_name = arg.get("arg")
        if arg_name == "self":
            continue
        arg_annotation = arg.get("annotation")
        py_type = callbacks.annotation_to_str(arg_annotation) if arg_annotation else ""
        typ = callbacks.py_type_to_ir(py_type, False) if py_type else InterfaceRef("any")
        params.append(Param(name=arg_name, typ=typ, loc=loc_unknown()))
        param_types[arg_name] = typ
    # Handle default arguments
    n_params = len(params)
    init_defaults = init_args.get("defaults", []) if isinstance(init_args, dict) else []
    n_defaults = len(init_defaults)
    for i, default_ast in enumerate(init_defaults):
        param_idx = n_params - n_defaults + i
        if 0 <= param_idx and param_idx < n_params:
            params[param_idx].default = callbacks.lower_expr(default_ast)
    # Set up context first (needed by collect_var_types)
    callbacks.setup_context(class_name, None)
    # Collect variable types and build type context
    init_body = init_ast.get("body", [])
    var_types, tuple_vars, sentinel_ints, list_element_unions = callbacks.collect_var_types(
        init_body
    )
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
        target=ir.VarLV(name="self", loc=loc_unknown()),
        value=ir.StructLit(
            struct_name=class_name,
            fields={},
            typ=Pointer(StructRef(class_name)),
            loc=loc_unknown(),
        ),
        loc=loc_unknown(),
    )
    self_init.is_declaration = True
    body.append(self_init)
    # Lower __init__ body with type context (excluding any "return" statements which are implicit in __init__)
    init_body_lowered = callbacks.setup_and_lower_stmts(class_name, None, type_ctx, init_body)
    body.extend(init_body_lowered)
    # Return self
    body.append(
        ir.Return(
            value=ir.Var(name="self", typ=Pointer(StructRef(class_name)), loc=loc_unknown()),
            loc=loc_unknown(),
        )
    )
    return Function(
        name=f"New{class_name}",
        params=params,
        ret=Pointer(StructRef(class_name)),
        body=body,
        loc=loc_unknown(),
    )


def build_method_shell(
    node: ASTNode,
    class_name: str,
    symbols: "SymbolTable",
    callbacks: BuilderCallbacks,
    with_body: bool = False,
) -> Function:
    """Build IR Function for a method. Set with_body=True to lower statements."""
    from .context import TypeContext

    node_name = node.get("name")
    info = symbols.structs.get(class_name)
    func_info = info.methods.get(node_name) if info else None
    params = []
    if func_info:
        for p in func_info.params:
            params.append(Param(name=p.name, typ=p.typ, default=p.default_value, loc=loc_unknown()))
    body: list["ir.Stmt"] = []
    if with_body:
        # Set up context first (needed by collect_var_types)
        callbacks.setup_context(class_name, func_info)
        # Collect variable types from body and add parameters + self
        node_body = node.get("body", [])
        var_types, tuple_vars, sentinel_ints, list_element_unions = callbacks.collect_var_types(
            node_body
        )
        if func_info:
            for p in func_info.params:
                var_types[p.name] = p.typ
        var_types["self"] = Pointer(StructRef(class_name))
        # Extract union types from parameter annotations
        union_types: dict[str, list[str]] = {}
        node_args = node.get("args", {})
        all_args = node_args.get("args", []) if isinstance(node_args, dict) else []
        non_self_args = [a for a in all_args if a.get("arg") != "self"]
        for arg in non_self_args:
            arg_annotation = arg.get("annotation")
            if arg_annotation:
                py_type = callbacks.annotation_to_str(arg_annotation)
                structs = callbacks.extract_union_struct_names(py_type)
                if structs:
                    union_types[arg.get("arg")] = structs
        type_ctx = TypeContext(
            return_type=func_info.return_type if func_info else VOID,
            var_types=var_types,
            tuple_vars=tuple_vars,
            sentinel_ints=sentinel_ints,
            union_types=union_types,
            list_element_unions=list_element_unions,
        )
        body = callbacks.setup_and_lower_stmts(class_name, func_info, type_ctx, node_body)
    return Function(
        name=node_name,
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
    node: ASTNode,
    symbols: "SymbolTable",
    callbacks: BuilderCallbacks,
    with_body: bool = False,
) -> Function:
    """Build IR Function from AST. Set with_body=True to lower statements."""
    from .context import TypeContext

    node_name = node.get("name")
    func_info = symbols.functions.get(node_name)
    params = []
    if func_info:
        for p in func_info.params:
            params.append(Param(name=p.name, typ=p.typ, default=p.default_value, loc=loc_unknown()))
    body: list["ir.Stmt"] = []
    if with_body:
        # Set up context first (needed by collect_var_types) - empty class name for functions
        callbacks.setup_context("", func_info)
        # Collect variable types from body and add parameters
        var_types, tuple_vars, sentinel_ints, list_element_unions = callbacks.collect_var_types(
            node.get("body", [])
        )
        if func_info:
            for p in func_info.params:
                var_types[p.name] = p.typ
        # Extract union types from parameter annotations
        union_types: dict[str, list[str]] = {}
        args = node.get("args", {})
        args_list = args.get("args", [])
        non_self_args = [a for a in args_list if a.get("arg") != "self"]
        for arg in non_self_args:
            annotation = arg.get("annotation")
            if annotation:
                py_type = callbacks.annotation_to_str(annotation)
                structs = callbacks.extract_union_struct_names(py_type)
                if structs:
                    union_types[arg.get("arg")] = structs
        type_ctx = TypeContext(
            return_type=func_info.return_type if func_info else VOID,
            var_types=var_types,
            tuple_vars=tuple_vars,
            sentinel_ints=sentinel_ints,
            union_types=union_types,
            list_element_unions=list_element_unions,
        )
        body = callbacks.setup_and_lower_stmts("", func_info, type_ctx, node.get("body", []))
    return Function(
        name=node_name,
        params=params,
        ret=func_info.return_type if func_info else VOID,
        body=body,
        loc=callbacks.loc_from_node(node),
    )


def build_struct(
    node: ASTNode,
    symbols: "SymbolTable",
    callbacks: BuilderCallbacks,
    with_body: bool = False,
    hierarchy_root: str | None = None,
) -> tuple[Struct | None, Function | None]:
    """Build IR Struct from class definition. Returns (struct, constructor_func)."""
    # Node is emitted as InterfaceDef, not Struct
    node_name = node.get("name")
    if hierarchy_root and node_name == hierarchy_root:
        return None, None
    info = symbols.structs.get(node_name)
    if not info:
        return None, None
    # Build fields
    fields = []
    for name, field_info in info.fields.items():
        fields.append(
            Field(
                name=name,
                typ=field_info.typ,
                loc=loc_unknown(),
            )
        )
    # Build methods
    methods = []
    init_ast: ASTNode | None = None
    for stmt in node.get("body", []):
        if is_type(stmt, ["FunctionDef"]):
            if stmt.get("name") == "__init__":
                init_ast = stmt
            else:
                method = build_method_shell(
                    stmt, node_name, symbols, callbacks, with_body=with_body
                )
                methods.append(method)
    # Synthesize GetKind() for Node structs with a kind field
    if info.is_node and "kind" in info.fields:
        has_getkind = any(m.name in ("GetKind", "get_kind") for m in methods)
        if not has_getkind:
            from .. import ir

            getkind_method = Function(
                name="GetKind",
                params=[],
                ret=STRING,
                body=[
                    ir.Return(
                        value=ir.FieldAccess(
                            obj=ir.Var(name="self", typ=Pointer(StructRef(node_name))),
                            field="kind",
                            typ=STRING,
                        )
                    )
                ],
                receiver=Receiver(name="self", typ=StructRef(node_name), pointer=True),
            )
            methods.append(getkind_method)
    implements = []
    if info.is_node and hierarchy_root:
        implements.append(hierarchy_root)
    # Determine embedded type for exception inheritance
    embedded_type = None
    if info.is_exception and info.bases:
        base = info.bases[0]
        if base != "Exception" and callbacks.is_exception_subclass(base):
            embedded_type = base
    struct = Struct(
        name=node_name,
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
        ctor_func = build_constructor(node_name, init_ast, info, callbacks)
    elif with_body and info.needs_constructor and embedded_type and not init_ast:
        # Exception subclass with no __init__ - forward to parent constructor
        ctor_func = build_forwarding_constructor(node_name, embedded_type, symbols)
    return struct, ctor_func


def build_module(
    tree: ASTNode,
    symbols: "SymbolTable",
    callbacks: BuilderCallbacks,
    hierarchy_root: str | None = None,
) -> Module:
    """Build IR Module from collected symbols."""
    from .. import ir

    module = Module(name="parable")
    module.hierarchy_root = hierarchy_root
    # Build constants from MODULE_CONSTANTS overrides
    for const_name, (const_type, go_value) in MODULE_CONSTANTS.items():
        # Strip quotes from go_value to get the actual string content
        str_value = go_value.strip('"')
        value = ir.StringLit(value=str_value, typ=STRING, loc=loc_unknown())
        module.constants.append(
            Constant(name=const_name, typ=const_type, value=value, loc=loc_unknown())
        )
    # Build constants (module-level and class-level)
    for node in tree.get("body", []):
        if is_type(node, ["Assign"]) and len(node.get("targets", [])) == 1:
            target = node.get("targets", [])[0]
            # Skip constants already handled by MODULE_CONSTANTS
            if is_type(target, ["Name"]) and target.get("id") in MODULE_CONSTANTS:
                continue
            if is_type(target, ["Name"]) and target.get("id") in symbols.constants:
                value = callbacks.lower_expr(node.get("value"))
                const_type = symbols.constants[target.get("id")]
                module.constants.append(
                    Constant(
                        name=target.get("id"),
                        typ=const_type,
                        value=value,
                        loc=callbacks.loc_from_node(node),
                    )
                )
        elif is_type(node, ["ClassDef"]):
            # Build class-level constants
            for stmt in node.get("body", []):
                if is_type(stmt, ["Assign"]) and len(stmt.get("targets", [])) == 1:
                    target = stmt.get("targets", [])[0]
                    if is_type(target, ["Name"]) and target.get("id", "").isupper():
                        const_name = f"{node.get('name')}_{target.get('id')}"
                        if const_name in symbols.constants:
                            value = callbacks.lower_expr(stmt.get("value"))
                            module.constants.append(
                                Constant(
                                    name=const_name,
                                    typ=INT,
                                    value=value,
                                    loc=callbacks.loc_from_node(stmt),
                                )
                            )
    # Build Node interface (abstract base for AST nodes)
    if hierarchy_root:
        node_interface = InterfaceDef(
            name=hierarchy_root,
            methods=[
                MethodSig(name="GetKind", params=[], ret=STRING),
                MethodSig(name="ToSexp", params=[], ret=STRING),
            ],
            fields=[Field(name="kind", typ=STRING)],
        )
        module.interfaces.append(node_interface)
    # Build structs (with method bodies) and collect constructor functions
    constructor_funcs: list[Function] = []
    for node in tree.get("body", []):
        if is_type(node, ["ClassDef"]):
            struct, ctor = build_struct(node, symbols, callbacks, with_body=True, hierarchy_root=hierarchy_root)
            if struct:
                module.structs.append(struct)
            if ctor:
                constructor_funcs.append(ctor)
    # Build functions (with bodies)
    for node in tree.get("body", []):
        if is_type(node, ["FunctionDef"]):
            func = build_function_shell(node, symbols, callbacks, with_body=True)
            module.functions.append(func)
    # Add constructor functions (must come after regular functions for dependency order)
    module.functions.extend(constructor_funcs)
    return module
