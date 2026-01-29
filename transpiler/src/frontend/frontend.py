"""Frontend: Python AST -> IR.

Converts parable.py Python subset to language-agnostic IR.
All analysis happens here; backends just emit syntax.
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from ..type_overrides import FIELD_TYPE_OVERRIDES, MODULE_CONSTANTS, NODE_FIELD_TYPES, NODE_METHOD_TYPES, PARAM_TYPE_OVERRIDES, RETURN_TYPE_OVERRIDES, SENTINEL_INT_FIELDS, VAR_TYPE_OVERRIDES
from ..ir import (
    BOOL,
    BYTE,
    FLOAT,
    INT,
    RUNE,
    STRING,
    VOID,
    Constant,
    Field,
    FieldInfo,
    FuncInfo,
    FuncType,
    Function,
    Interface,
    InterfaceDef,
    Loc,
    Map,
    MethodSig,
    Module,
    Optional,
    Param,
    ParamInfo,
    Pointer,
    Primitive,
    Set,
    Slice,
    StringFormat,
    StructInfo,
    StructRef,
    Struct,
    SymbolTable,
    Tuple,
    TupleAssign,
    Type,
    TypeCase,
    TypeSwitch,
)
from .context import TypeContext
from . import type_inference
from . import lowering
from . import collection

if TYPE_CHECKING:
    pass

# Python type -> IR type mapping for primitives
TYPE_MAP: dict[str, Type] = {
    "str": STRING,
    "int": INT,
    "bool": BOOL,
    "float": FLOAT,
    "bytes": Slice(BYTE),
    "bytearray": Slice(BYTE),
}


class Frontend:
    """Converts Python AST to IR Module."""

    def __init__(self) -> None:
        self.symbols = SymbolTable()
        self._node_types: set[str] = set()  # classes that inherit from Node
        # Type inference context
        self._current_func_info: FuncInfo | None = None
        self._current_class_name: str = ""
        self._type_ctx: TypeContext = TypeContext()
        self._current_catch_var: str | None = None  # track catch variable for raise e pattern
        # Auto-generated kind -> struct mappings (built from class const_fields)
        self._kind_to_struct: dict[str, str] = {}
        self._kind_to_class: dict[str, str] = {}

    def transpile(self, source: str) -> Module:
        """Parse Python source and produce IR Module."""
        tree = ast.parse(source)
        # Pass 1: Collect class names and inheritance
        self._collect_class_names(tree)
        # Pass 2: Mark Node subclasses
        self._mark_node_subclasses()
        # Pass 2b: Mark Exception subclasses
        self._mark_exception_subclasses()
        # Pass 3: Collect function and method signatures
        self._collect_signatures(tree)
        # Pass 4: Collect struct fields
        self._collect_fields(tree)
        # Pass 4b: Build kind -> struct mapping from const_fields
        self._build_kind_mapping()
        # Pass 5: Collect module-level constants
        self._collect_constants(tree)
        # Build IR Module
        return self._build_module(tree)

    def _collect_class_names(self, tree: ast.Module) -> None:
        """Pass 1: Collect all class names and their bases."""
        collection.collect_class_names(tree, self.symbols)

    def _mark_node_subclasses(self) -> None:
        """Pass 2: Mark classes that inherit from Node."""
        collection.mark_node_subclasses(self.symbols, self._node_types)

    def _is_node_subclass(self, name: str) -> bool:
        """Check if a class is a Node subclass (directly or transitively)."""
        return type_inference.is_node_subclass(name, self.symbols)

    def _mark_exception_subclasses(self) -> None:
        """Pass 2b: Mark classes that inherit from Exception."""
        collection.mark_exception_subclasses(self.symbols)

    def _is_exception_subclass(self, name: str) -> bool:
        """Check if a class is an Exception subclass (directly or transitively)."""
        return collection.is_exception_subclass(name, self.symbols)

    def _build_kind_mapping(self) -> None:
        """Build kind -> struct/class mappings from const_fields["kind"] values."""
        collection.build_kind_mapping(
            self.symbols, self._kind_to_struct, self._kind_to_class
        )

    def _collect_signatures(self, tree: ast.Module) -> None:
        """Pass 3: Collect function and method signatures."""
        callbacks = collection.CollectionCallbacks(
            annotation_to_str=self._annotation_to_str,
            py_type_to_ir=self._py_type_to_ir,
            py_return_type_to_ir=self._py_return_type_to_ir,
            lower_expr=self._lower_expr,
        )
        collection.collect_signatures(tree, self.symbols, callbacks)

    def _collect_class_methods(self, node: ast.ClassDef) -> None:
        """Collect method signatures for a class."""
        callbacks = collection.CollectionCallbacks(
            annotation_to_str=self._annotation_to_str,
            py_type_to_ir=self._py_type_to_ir,
            py_return_type_to_ir=self._py_return_type_to_ir,
            lower_expr=self._lower_expr,
        )
        collection.collect_class_methods(node, self.symbols, callbacks)

    def _collect_fields(self, tree: ast.Module) -> None:
        """Pass 4: Collect struct fields from class definitions."""
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                self._collect_class_fields(node)

    def _collect_class_fields(self, node: ast.ClassDef) -> None:
        """Collect fields from class body and __init__."""
        info = self.symbols.structs[node.name]
        # Collect class-level annotations
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                field_name = stmt.target.id
                py_type = self._annotation_to_str(stmt.annotation)
                typ = self._py_type_to_ir(py_type)
                # Apply field type overrides
                override_key = (info.name, field_name)
                if override_key in FIELD_TYPE_OVERRIDES:
                    typ = FIELD_TYPE_OVERRIDES[override_key]
                info.fields[field_name] = FieldInfo(
                    name=field_name, typ=typ, py_name=field_name
                )
        # Collect fields from __init__
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                self._collect_init_fields(stmt, info)
        # Exception classes always need constructors for panic(NewXxx(...)) pattern
        if info.is_exception:
            info.needs_constructor = True

    def _collect_init_fields(self, init: ast.FunctionDef, info: StructInfo) -> None:
        """Collect fields assigned in __init__."""
        param_types: dict[str, str] = {}
        # Record __init__ parameter order (excluding self) for constructor calls
        for arg in init.args.args:
            if arg.arg != "self":
                info.init_params.append(arg.arg)
                if arg.annotation:
                    param_types[arg.arg] = self._annotation_to_str(arg.annotation)
        # Track whether __init__ has computed initializations
        has_computed_init = False
        for stmt in ast.walk(init):
            if isinstance(stmt, ast.AnnAssign):
                if (
                    isinstance(stmt.target, ast.Attribute)
                    and isinstance(stmt.target.value, ast.Name)
                    and stmt.target.value.id == "self"
                ):
                    field_name = stmt.target.attr
                    if field_name not in info.fields:
                        py_type = self._annotation_to_str(stmt.annotation)
                        typ = self._py_type_to_ir(py_type, concrete_nodes=True)
                        # Apply field type overrides (keep for compatibility)
                        override_key = (info.name, field_name)
                        if override_key in FIELD_TYPE_OVERRIDES:
                            typ = FIELD_TYPE_OVERRIDES[override_key]
                        info.fields[field_name] = FieldInfo(
                            name=field_name, typ=typ, py_name=field_name
                        )
                    # Check if value is computed (not just a param reference)
                    if stmt.value is not None:
                        if not (isinstance(stmt.value, ast.Name) and stmt.value.id in info.init_params):
                            has_computed_init = True
            elif isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "self"
                    ):
                        field_name = target.attr
                        # Track param-to-field mapping: self.field = param
                        is_simple_param = isinstance(stmt.value, ast.Name) and stmt.value.id in info.init_params
                        # Track constant string assignments: self.kind = "operator"
                        is_const_str = isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str)
                        if is_simple_param:
                            info.param_to_field[stmt.value.id] = field_name
                        elif is_const_str:
                            info.const_fields[field_name] = stmt.value.value
                        else:
                            # Computed initialization - need constructor
                            has_computed_init = True
                        if field_name not in info.fields:
                            typ = self._infer_type_from_value(stmt.value, param_types)
                            # Apply field type overrides
                            override_key = (info.name, field_name)
                            if override_key in FIELD_TYPE_OVERRIDES:
                                typ = FIELD_TYPE_OVERRIDES[override_key]
                            info.fields[field_name] = FieldInfo(
                                name=field_name, typ=typ, py_name=field_name
                            )
        # Flag if constructor is needed - only for structs that critically need it
        # (Parser, Lexer need computed Length, nested constructors, back-references)
        NEEDS_CONSTRUCTOR = {"Parser", "Lexer", "ContextStack", "QuoteState", "ParseContext"}
        if has_computed_init and info.name in NEEDS_CONSTRUCTOR:
            info.needs_constructor = True

    def _collect_constants(self, tree: ast.Module) -> None:
        """Pass 5: Collect module-level and class-level constants."""
        collection.collect_constants(tree, self.symbols)

    def _detect_mutated_params(self, node: ast.FunctionDef) -> set[str]:
        """Detect which parameters are mutated in the function body."""
        return collection.detect_mutated_params(node)

    def _extract_func_info(
        self, node: ast.FunctionDef, is_method: bool = False
    ) -> FuncInfo:
        """Extract function signature information."""
        callbacks = collection.CollectionCallbacks(
            annotation_to_str=self._annotation_to_str,
            py_type_to_ir=self._py_type_to_ir,
            py_return_type_to_ir=self._py_return_type_to_ir,
            lower_expr=self._lower_expr,
        )
        return collection.extract_func_info(node, callbacks, is_method)

    def _build_module(self, tree: ast.Module) -> Module:
        """Build IR Module from collected symbols."""
        from .. import ir
        module = Module(name="parable")
        # Build constants from MODULE_CONSTANTS overrides
        for const_name, (const_type, go_value) in MODULE_CONSTANTS.items():
            # Strip quotes from go_value to get the actual string content
            str_value = go_value.strip('"')
            value = ir.StringLit(value=str_value, typ=STRING, loc=Loc.unknown())
            module.constants.append(
                Constant(name=const_name, typ=const_type, value=value, loc=Loc.unknown())
            )
        # Build constants (module-level and class-level)
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                # Skip constants already handled by MODULE_CONSTANTS
                if isinstance(target, ast.Name) and target.id in MODULE_CONSTANTS:
                    continue
                if isinstance(target, ast.Name) and target.id in self.symbols.constants:
                    value = self._lower_expr(node.value)
                    const_type = self.symbols.constants[target.id]
                    module.constants.append(
                        Constant(name=target.id, typ=const_type, value=value, loc=self._loc_from_node(node))
                    )
            elif isinstance(node, ast.ClassDef):
                # Build class-level constants
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                        target = stmt.targets[0]
                        if isinstance(target, ast.Name) and target.id.isupper():
                            const_name = f"{node.name}_{target.id}"
                            if const_name in self.symbols.constants:
                                value = self._lower_expr(stmt.value)
                                module.constants.append(
                                    Constant(name=const_name, typ=INT, value=value, loc=self._loc_from_node(stmt))
                                )
        # Build Node interface (abstract base for AST nodes)
        node_interface = InterfaceDef(
            name="Node",
            methods=[
                MethodSig(name="GetKind", params=[], ret=STRING),
                MethodSig(name="ToSexp", params=[], ret=STRING),
            ],
        )
        module.interfaces.append(node_interface)
        # Build structs (with method bodies) and collect constructor functions
        constructor_funcs: list[Function] = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                struct, ctor = self._build_struct(node, with_body=True)
                if struct:
                    module.structs.append(struct)
                if ctor:
                    constructor_funcs.append(ctor)
        # Build functions (with bodies)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                func = self._build_function_shell(node, with_body=True)
                module.functions.append(func)
        # Add constructor functions (must come after regular functions for dependency order)
        module.functions.extend(constructor_funcs)
        return module

    def _build_struct(self, node: ast.ClassDef, with_body: bool = False) -> tuple[Struct | None, Function | None]:
        """Build IR Struct from class definition. Returns (struct, constructor_func)."""
        # Node is emitted as InterfaceDef, not Struct
        if node.name == "Node":
            return None, None
        info = self.symbols.structs.get(node.name)
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
                    method = self._build_method_shell(stmt, node.name, with_body=with_body)
                    methods.append(method)
        implements = []
        if info.is_node:
            implements.append("Node")
        # Determine embedded type for exception inheritance
        embedded_type = None
        if info.is_exception and info.bases:
            base = info.bases[0]
            if base != "Exception" and self._is_exception_subclass(base):
                embedded_type = base
        struct = Struct(
            name=node.name,
            fields=fields,
            methods=methods,
            implements=implements,
            loc=self._loc_from_node(node),
            is_exception=info.is_exception,
            embedded_type=embedded_type,
        )
        # Generate constructor function if needed
        ctor_func: Function | None = None
        if with_body and info.needs_constructor and init_ast:
            ctor_func = self._build_constructor(node.name, init_ast, info)
        elif with_body and info.needs_constructor and embedded_type and not init_ast:
            # Exception subclass with no __init__ - forward to parent constructor
            ctor_func = self._build_forwarding_constructor(node.name, embedded_type)
        return struct, ctor_func

    def _build_forwarding_constructor(self, class_name: str, parent_class: str) -> Function:
        """Build a forwarding constructor for exception subclasses with no __init__."""
        from .. import ir
        # Get parent class info to copy its parameters
        parent_info = self.symbols.structs.get(parent_class)
        if not parent_info:
            raise ValueError(f"Unknown parent class: {parent_class}")
        # Build parameters from parent's __init__ params
        params: list[Param] = []
        args: list[ir.Var] = []
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
            args.append(ir.Var(name=param_name, typ=typ))
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

    def _build_constructor(self, class_name: str, init_ast: ast.FunctionDef, info: StructInfo) -> Function:
        """Build a NewXxx constructor function from __init__ AST."""
        from .. import ir
        # Build parameters (same as __init__ excluding self)
        params: list[Param] = []
        param_types: dict[str, Type] = {}
        for arg in init_ast.args.args:
            if arg.arg == "self":
                continue
            py_type = self._annotation_to_str(arg.annotation) if arg.annotation else ""
            typ = self._py_type_to_ir(py_type) if py_type else Interface("any")
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
                params[param_idx].default = self._lower_expr(default_ast)
        # Set up type context for lowering __init__ body
        self._current_func_info = None
        self._current_class_name = class_name
        var_types, tuple_vars, sentinel_ints, list_element_unions = self._collect_var_types(init_ast.body)
        var_types.update(param_types)
        var_types["self"] = Pointer(StructRef(class_name))
        self._type_ctx = TypeContext(
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
        # Lower __init__ body (excluding any "return" statements which are implicit in __init__)
        init_body = self._lower_stmts(init_ast.body)
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

    def _build_function_shell(self, node: ast.FunctionDef, with_body: bool = False) -> Function:
        """Build IR Function from AST. Set with_body=True to lower statements."""
        func_info = self.symbols.functions.get(node.name)
        params = []
        if func_info:
            for p in func_info.params:
                params.append(
                    Param(name=p.name, typ=p.typ, default=p.default_value, loc=Loc.unknown())
                )
        body = []
        if with_body:
            # Set up type context for this function
            self._current_func_info = func_info
            self._current_class_name = ""
            # Collect variable types from body and add parameters
            var_types, tuple_vars, sentinel_ints, list_element_unions = self._collect_var_types(node.body)
            if func_info:
                for p in func_info.params:
                    var_types[p.name] = p.typ
            # Extract union types from parameter annotations
            union_types: dict[str, list[str]] = {}
            non_self_args = [a for a in node.args.args if a.arg != "self"]
            for arg in non_self_args:
                if arg.annotation:
                    py_type = self._annotation_to_str(arg.annotation)
                    structs = self._extract_union_struct_names(py_type)
                    if structs:
                        union_types[arg.arg] = structs
            self._type_ctx = TypeContext(
                return_type=func_info.return_type if func_info else VOID,
                var_types=var_types,
                tuple_vars=tuple_vars,
                sentinel_ints=sentinel_ints,
                union_types=union_types,
                list_element_unions=list_element_unions,
            )
            body = self._lower_stmts(node.body)
        return Function(
            name=node.name,
            params=params,
            ret=func_info.return_type if func_info else VOID,
            body=body,
            loc=self._loc_from_node(node),
        )

    def _build_method_shell(self, node: ast.FunctionDef, class_name: str, with_body: bool = False) -> Function:
        """Build IR Function for a method. Set with_body=True to lower statements."""
        info = self.symbols.structs.get(class_name)
        func_info = info.methods.get(node.name) if info else None
        params = []
        if func_info:
            for p in func_info.params:
                params.append(
                    Param(name=p.name, typ=p.typ, default=p.default_value, loc=Loc.unknown())
                )
        from ..ir import Receiver
        body = []
        if with_body:
            # Set up type context for this method
            self._current_func_info = func_info
            self._current_class_name = class_name
            # Collect variable types from body and add parameters + self
            var_types, tuple_vars, sentinel_ints, list_element_unions = self._collect_var_types(node.body)
            if func_info:
                for p in func_info.params:
                    var_types[p.name] = p.typ
            var_types["self"] = Pointer(StructRef(class_name))
            # Extract union types from parameter annotations
            union_types: dict[str, list[str]] = {}
            non_self_args = [a for a in node.args.args if a.arg != "self"]
            for arg in non_self_args:
                if arg.annotation:
                    py_type = self._annotation_to_str(arg.annotation)
                    structs = self._extract_union_struct_names(py_type)
                    if structs:
                        union_types[arg.arg] = structs
            self._type_ctx = TypeContext(
                return_type=func_info.return_type if func_info else VOID,
                var_types=var_types,
                tuple_vars=tuple_vars,
                sentinel_ints=sentinel_ints,
                union_types=union_types,
                list_element_unions=list_element_unions,
            )
            body = self._lower_stmts(node.body)
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
            loc=self._loc_from_node(node),
        )

    def _loc_from_node(self, node: ast.AST) -> Loc:
        """Create Loc from AST node."""
        return lowering.loc_from_node(node)

    def _get_base_name(self, base: ast.expr) -> str:
        """Extract base class name from AST node."""
        return collection.get_base_name(base)

    def _annotation_to_str(self, node: ast.expr | None) -> str:
        """Convert type annotation AST to string."""
        match node:
            case None:
                return ""
            case ast.Name(id=name):
                return name
            case ast.Constant(value=None):
                return "None"
            case ast.Constant(value=v):
                return str(v)
            case ast.List(elts=elts):
                # For annotations like Callable[[], T], the first arg is an ast.List
                args = ", ".join(self._annotation_to_str(e) for e in elts)
                return f"[{args}]"
            case ast.Subscript(value=val, slice=ast.Tuple(elts=elts)):
                base = self._annotation_to_str(val)
                args = ", ".join(self._annotation_to_str(e) for e in elts)
                return f"{base}[{args}]"
            case ast.Subscript(value=val, slice=slc):
                base = self._annotation_to_str(val)
                return f"{base}[{self._annotation_to_str(slc)}]"
            case ast.BinOp(left=left, right=right, op=ast.BitOr()):
                return f"{self._annotation_to_str(left)} | {self._annotation_to_str(right)}"
            case ast.Attribute(attr=attr):
                return attr
            case _:
                return ""

    def _py_type_to_ir(self, py_type: str, concrete_nodes: bool = False) -> Type:
        """Convert Python type string to IR Type."""
        return type_inference.py_type_to_ir(py_type, self.symbols, self._node_types, concrete_nodes)

    def _py_return_type_to_ir(self, py_type: str) -> Type:
        """Convert Python return type to IR, handling tuples as multiple returns."""
        return type_inference.py_return_type_to_ir(py_type, self.symbols, self._node_types)

    def _parse_callable_type(self, py_type: str, concrete_nodes: bool) -> Type:
        """Parse Callable[[], ReturnType] -> FuncType."""
        return type_inference.parse_callable_type(py_type, concrete_nodes, self.symbols, self._node_types)

    def _extract_union_struct_names(self, py_type: str) -> list[str] | None:
        """Extract struct names from a union type like 'Redirect | HereDoc'.
        Returns None if not a union of Node subclasses."""
        if " | " not in py_type:
            return None
        parts = self._split_union_types(py_type)
        if len(parts) <= 1:
            return None
        # Filter out None
        parts = [p for p in parts if p != "None"]
        if len(parts) <= 1:
            return None
        # Check if all parts are Node subclasses
        if not all(self._is_node_subclass(p) for p in parts):
            return None
        return parts

    def _make_default_value(self, typ: Type, loc: Loc) -> "ir.Expr":
        """Create a default value expression for a given type."""
        from .. import ir
        # Pointer and interface types use nil
        if isinstance(typ, (Pointer, Optional, Interface)):
            return ir.NilLit(typ=typ, loc=loc)
        # Primitive types use their zero values
        if isinstance(typ, Primitive):
            if typ.kind == "bool":
                return ir.BoolLit(value=False, typ=BOOL, loc=loc)
            if typ.kind == "int":
                return ir.IntLit(value=0, typ=INT, loc=loc)
            if typ.kind == "string":
                return ir.StringLit(value="", typ=STRING, loc=loc)
            if typ.kind == "float":
                return ir.FloatLit(value=0.0, typ=FLOAT, loc=loc)
        # Slice/Map/Set use nil (Go zero value)
        if isinstance(typ, (Slice, Map, Set)):
            return ir.NilLit(typ=typ, loc=loc)
        # StructRef uses nil (pointer to struct)
        if isinstance(typ, StructRef):
            return ir.NilLit(typ=Pointer(typ), loc=loc)
        # Fallback to nil
        return ir.NilLit(typ=typ, loc=loc)

    def _infer_type_from_value(
        self, node: ast.expr, param_types: dict[str, str]
    ) -> Type:
        """Infer IR type from an expression."""
        return type_inference.infer_type_from_value(node, param_types, self.symbols, self._node_types)

    def _split_union_types(self, s: str) -> list[str]:
        """Split union types on | respecting nested brackets."""
        return type_inference.split_union_types(s)

    def _split_type_args(self, s: str) -> list[str]:
        """Split type arguments like 'K, V' respecting nested brackets."""
        return type_inference.split_type_args(s)

    # ============================================================
    # LOCAL TYPE INFERENCE (Pierce & Turner style)
    # ============================================================

    def _collect_var_types(self, stmts: list[ast.stmt]) -> tuple[dict[str, Type], dict[str, list[str]], set[str]]:
        """Pre-scan function body to collect variable types, tuple var mappings, and sentinel ints."""
        var_types: dict[str, Type] = {}
        tuple_vars: dict[str, list[str]] = {}
        sentinel_ints: set[str] = set()
        # Track variables assigned None and their concrete types (for Optional inference)
        vars_assigned_none: set[str] = set()
        vars_all_types: dict[str, list[Type]] = {}  # Track all types assigned to each var
        # Preliminary pass: find variables assigned both None and typed values
        for stmt in ast.walk(ast.Module(body=stmts, type_ignores=[])):
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                target = stmt.targets[0]
                if isinstance(target, ast.Name):
                    var_name = target.id
                    if var_name not in vars_all_types:
                        vars_all_types[var_name] = []
                    # Check if assigning None
                    if isinstance(stmt.value, ast.Constant) and stmt.value.value is None:
                        vars_assigned_none.add(var_name)
                    # Check if assigning typed value
                    elif isinstance(stmt.value, ast.Constant):
                        if isinstance(stmt.value.value, int) and not isinstance(stmt.value.value, bool):
                            vars_all_types[var_name].append(INT)
                        elif isinstance(stmt.value.value, str):
                            vars_all_types[var_name].append(STRING)
                    elif isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Name):
                        # int(...) call
                        if stmt.value.func.id == "int":
                            vars_all_types[var_name].append(INT)
                        elif stmt.value.func.id == "str":
                            vars_all_types[var_name].append(STRING)
                    # String method calls: x = "".join(...), etc.
                    elif isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Attribute):
                        method = stmt.value.func.attr
                        if method in ("join", "strip", "lstrip", "rstrip", "lower", "upper", "replace", "format"):
                            vars_all_types[var_name].append(STRING)
                        # self.method() calls - check return type
                        elif isinstance(stmt.value.func.value, ast.Name) and stmt.value.func.value.id == "self":
                            if self._current_class_name and self._current_class_name in self.symbols.structs:
                                method_info = self.symbols.structs[self._current_class_name].methods.get(method)
                                if method_info:
                                    vars_all_types[var_name].append(method_info.return_type)
                    # Assignment from known variable: varfd = varname
                    elif isinstance(stmt.value, ast.Name):
                        if stmt.value.id in vars_all_types and vars_all_types[stmt.value.id]:
                            vars_all_types[var_name].extend(vars_all_types[stmt.value.id])
        # Unify types for each variable
        vars_concrete_type: dict[str, Type] = {}
        for var_name, types in vars_all_types.items():
            if not types:
                continue
            # Deduplicate types
            unique_types = list(set(types))
            if len(unique_types) == 1:
                vars_concrete_type[var_name] = unique_types[0]
            else:
                # Multiple types - check if all are Node-related
                all_node = all(
                    t == Interface("Node") or t == StructRef("Node") or
                    (isinstance(t, Pointer) and isinstance(t.target, StructRef) and t.target.name in self._node_types)
                    for t in unique_types
                )
                if all_node:
                    vars_concrete_type[var_name] = Interface("Node")
                # Otherwise, no unified type (will fall back to default inference)
        # First pass: collect For loop variable types (needed for append inference)
        for stmt in ast.walk(ast.Module(body=stmts, type_ignores=[])):
            if isinstance(stmt, ast.For):
                if isinstance(stmt.target, ast.Name):
                    loop_var = stmt.target.id
                    # Check for range() call - loop variable is INT
                    if (isinstance(stmt.iter, ast.Call) and
                        isinstance(stmt.iter.func, ast.Name) and
                        stmt.iter.func.id == "range"):
                        var_types[loop_var] = INT
                    else:
                        iterable_type = self._infer_iterable_type(stmt.iter, var_types)
                        if isinstance(iterable_type, Slice):
                            var_types[loop_var] = iterable_type.element
                elif isinstance(stmt.target, ast.Tuple) and len(stmt.target.elts) == 2:
                    if isinstance(stmt.target.elts[1], ast.Name):
                        loop_var = stmt.target.elts[1].id
                        iterable_type = self._infer_iterable_type(stmt.iter, var_types)
                        if isinstance(iterable_type, Slice):
                            var_types[loop_var] = iterable_type.element
        # Second pass: infer variable types from assignments (runs first to populate var_types)
        for stmt in ast.walk(ast.Module(body=stmts, type_ignores=[])):
            # Infer from annotated assignments
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                py_type = self._annotation_to_str(stmt.annotation)
                typ = self._py_type_to_ir(py_type)
                # int | None = None uses -1 sentinel, so track as INT not Optional
                if (isinstance(typ, Optional) and typ.inner == INT and
                    stmt.value and isinstance(stmt.value, ast.Constant) and stmt.value.value is None):
                    var_types[stmt.target.id] = INT
                    sentinel_ints.add(stmt.target.id)
                else:
                    var_types[stmt.target.id] = typ
            # Infer from return statements: if returning var and return type is known
            if isinstance(stmt, ast.Return) and stmt.value:
                if isinstance(stmt.value, ast.Name):
                    var_name = stmt.value.id
                    if self._current_func_info and isinstance(self._current_func_info.return_type, Slice):
                        var_types[var_name] = self._current_func_info.return_type
            # Infer from field assignments: self.field = var -> var has field's type
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                target = stmt.targets[0]
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                    if target.value.id == "self" and isinstance(stmt.value, ast.Name):
                        var_name = stmt.value.id
                        field_name = target.attr
                        # Look up field type from current class
                        if self._current_class_name in self.symbols.structs:
                            struct_info = self.symbols.structs[self._current_class_name]
                            field_info = struct_info.fields.get(field_name)
                            if field_info:
                                var_types[var_name] = field_info.typ
                # Infer from method call assignments: var = self.method() -> var has method's return type
                if isinstance(target, ast.Name) and isinstance(stmt.value, ast.Call):
                    var_name = target.id
                    call = stmt.value
                    if isinstance(call.func, ast.Attribute):
                        method_name = call.func.attr
                        # Get object type
                        if isinstance(call.func.value, ast.Name):
                            obj_name = call.func.value.id
                            if obj_name == "self" and self._current_class_name:
                                struct_info = self.symbols.structs.get(self._current_class_name)
                                if struct_info:
                                    method_info = struct_info.methods.get(method_name)
                                    if method_info:
                                        var_types[var_name] = method_info.return_type
                # Infer from literal assignments
                if isinstance(target, ast.Name):
                    var_name = target.id
                    if isinstance(stmt.value, ast.Constant):
                        if isinstance(stmt.value.value, bool):
                            var_types[var_name] = BOOL
                        elif isinstance(stmt.value.value, int):
                            var_types[var_name] = INT
                        elif isinstance(stmt.value.value, str):
                            var_types[var_name] = STRING
                    elif isinstance(stmt.value, ast.Name):
                        if stmt.value.id in ("True", "False"):
                            var_types[var_name] = BOOL
                    # Comparisons and bool ops always produce bool
                    elif isinstance(stmt.value, (ast.Compare, ast.BoolOp)):
                        var_types[var_name] = BOOL
                    # BinOp with arithmetic operators produce int
                    elif isinstance(stmt.value, ast.BinOp):
                        if isinstance(stmt.value.op, (ast.Sub, ast.Mult, ast.FloorDiv, ast.Mod)):
                            var_types[var_name] = INT
                        elif isinstance(stmt.value.op, ast.Add):
                            # Could be int or string - check operands
                            if self._is_len_call(stmt.value.left) or self._is_len_call(stmt.value.right):
                                var_types[var_name] = INT
                    # Infer from list/dict literals - element type inferred later from appends
                    elif isinstance(stmt.value, ast.List):
                        var_types[var_name] = Slice(Interface("any"))
                    elif isinstance(stmt.value, ast.Dict):
                        var_types[var_name] = Map(STRING, Interface("any"))
                    # Infer from field access: var = obj.field -> var has field's type
                    elif isinstance(stmt.value, ast.Attribute):
                        # Look up field type using local var_types (not self._type_ctx)
                        attr_node = stmt.value
                        field_name = attr_node.attr
                        obj_type: Type = Interface("any")
                        if isinstance(attr_node.value, ast.Name):
                            obj_name = attr_node.value.id
                            if obj_name == "self" and self._current_class_name:
                                obj_type = Pointer(StructRef(self._current_class_name))
                            elif obj_name in var_types:
                                obj_type = var_types[obj_name]
                        struct_name = self._extract_struct_name(obj_type)
                        if struct_name and struct_name in self.symbols.structs:
                            field_info = self.symbols.structs[struct_name].fields.get(field_name)
                            if field_info:
                                var_types[var_name] = field_info.typ
                    # Infer from subscript/slice: var = container[...] -> element type
                    elif isinstance(stmt.value, ast.Subscript):
                        container_type: Type = Interface("any")
                        if isinstance(stmt.value.value, ast.Name):
                            container_name = stmt.value.value.id
                            if container_name in var_types:
                                container_type = var_types[container_name]
                        # Also handle field access: self.field[i]
                        elif isinstance(stmt.value.value, ast.Attribute):
                            attr = stmt.value.value
                            if isinstance(attr.value, ast.Name):
                                if attr.value.id == "self" and self._current_class_name:
                                    struct_info = self.symbols.structs.get(self._current_class_name)
                                    if struct_info:
                                        field_info = struct_info.fields.get(attr.attr)
                                        if field_info:
                                            container_type = field_info.typ
                                elif attr.value.id in var_types:
                                    obj_type = var_types[attr.value.id]
                                    struct_name = self._extract_struct_name(obj_type)
                                    if struct_name and struct_name in self.symbols.structs:
                                        field_info = self.symbols.structs[struct_name].fields.get(attr.attr)
                                        if field_info:
                                            container_type = field_info.typ
                        if container_type == STRING:
                            var_types[var_name] = STRING
                        elif isinstance(container_type, Slice):
                            # Indexing a slice gives the element type
                            var_types[var_name] = container_type.element
                        elif isinstance(container_type, Map):
                            # Indexing a map gives the value type
                            var_types[var_name] = container_type.value
                        elif isinstance(container_type, Tuple):
                            # Indexing a tuple with constant gives element type
                            if isinstance(stmt.value.slice, ast.Constant) and isinstance(stmt.value.slice.value, int):
                                idx = stmt.value.slice.value
                                if 0 <= idx < len(container_type.elements):
                                    var_types[var_name] = container_type.elements[idx]
                    # Infer from method calls: var = obj.method() -> method return type
                    elif isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Attribute):
                        method_name = stmt.value.func.attr
                        obj_type: Type = Interface("any")
                        if isinstance(stmt.value.func.value, ast.Name):
                            obj_name = stmt.value.func.value.id
                            if obj_name == "self" and self._current_class_name:
                                obj_type = Pointer(StructRef(self._current_class_name))
                            elif obj_name in var_types:
                                obj_type = var_types[obj_name]
                            # Handle known string functions
                            elif obj_name == "strings" and method_name in ("Join", "Replace", "ToLower", "ToUpper", "Trim", "TrimSpace"):
                                var_types[var_name] = STRING
                                continue
                        struct_name = self._extract_struct_name(obj_type)
                        if struct_name and struct_name in self.symbols.structs:
                            method_info = self.symbols.structs[struct_name].methods.get(method_name)
                            if method_info:
                                var_types[var_name] = method_info.return_type
            # Handle tuple unpacking: a, b = func() where func returns tuple
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                target = stmt.targets[0]
                if isinstance(target, ast.Tuple) and isinstance(stmt.value, ast.Call):
                    # Get return type of the called function/method
                    ret_type = self._infer_call_return_type(stmt.value)
                    if isinstance(ret_type, Tuple):
                        for i, elt in enumerate(target.elts):
                            if isinstance(elt, ast.Name) and i < len(ret_type.elements):
                                var_types[elt.id] = ret_type.elements[i]
                # Handle single var = tuple-returning func (will be expanded to synthetic vars)
                elif isinstance(target, ast.Name) and isinstance(stmt.value, ast.Call):
                    ret_type = self._infer_call_return_type(stmt.value)
                    if isinstance(ret_type, Tuple) and len(ret_type.elements) > 1:
                        base_name = target.id
                        synthetic_names = [f"{base_name}{i}" for i in range(len(ret_type.elements))]
                        tuple_vars[base_name] = synthetic_names
                        for i, elem_type in enumerate(ret_type.elements):
                            var_types[f"{base_name}{i}"] = elem_type
                    # Handle constructor calls: var = ClassName()
                    elif isinstance(stmt.value.func, ast.Name):
                        class_name = stmt.value.func.id
                        if class_name in self.symbols.structs:
                            var_types[target.id] = Pointer(StructRef(class_name))
                        # Handle free function calls: var = func()
                        elif class_name in self.symbols.functions:
                            var_types[target.id] = self.symbols.functions[class_name].return_type
                        # Handle builtin calls: bytearray(), list(), dict(), etc.
                        elif class_name == "bytearray":
                            var_types[target.id] = Slice(BYTE)
                        elif class_name == "list":
                            var_types[target.id] = Slice(Interface("any"))
                        elif class_name == "dict":
                            var_types[target.id] = Map(Interface("any"), Interface("any"))
        # Third pass: infer types from append() calls (after all variable types are collected)
        # Note: don't overwrite already-known specific slice types (e.g., bytearray -> []byte)
        for stmt in ast.walk(ast.Module(body=stmts, type_ignores=[])):
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                if isinstance(call.func, ast.Attribute) and call.func.attr == "append":
                    if isinstance(call.func.value, ast.Name) and call.args:
                        var_name = call.func.value.id
                        # Don't overwrite already-known specific slice types (e.g., bytearray)
                        # But DO infer if current type is generic Slice(any)
                        if var_name in var_types and isinstance(var_types[var_name], Slice):
                            current_elem = var_types[var_name].element
                            if current_elem != Interface("any"):
                                continue  # Skip - already has specific element type
                        elem_type = self._infer_element_type_from_append_arg(call.args[0], var_types)
                        if elem_type != Interface("any"):
                            var_types[var_name] = Slice(elem_type)
        # Third-and-a-half pass: detect kind-guarded appends to track list element union types
        # Pattern: if/elif p.kind == "something": list_var.append(p)
        # This records that list_var contains items of struct type for "something"
        list_element_unions: dict[str, list[str]] = {}
        for stmt in ast.walk(ast.Module(body=stmts, type_ignores=[])):
            if isinstance(stmt, ast.If):
                # Check the test condition for kind checks
                kind_check = self._is_kind_check(stmt.test)
                if kind_check:
                    checked_var, struct_name = kind_check
                    # Look for append calls in the body
                    for body_stmt in stmt.body:
                        if (isinstance(body_stmt, ast.Expr) and isinstance(body_stmt.value, ast.Call)):
                            call = body_stmt.value
                            if (isinstance(call.func, ast.Attribute) and call.func.attr == "append" and
                                isinstance(call.func.value, ast.Name) and call.args and
                                isinstance(call.args[0], ast.Name) and call.args[0].id == checked_var):
                                list_var = call.func.value.id
                                if list_var not in list_element_unions:
                                    list_element_unions[list_var] = []
                                if struct_name not in list_element_unions[list_var]:
                                    list_element_unions[list_var].append(struct_name)
        # Fourth pass: re-run assignment type inference to propagate types through chains
        # This handles cases like: pair = cmds[0]; needs = pair[1]
        # where pair's type depends on cmds, and needs' type depends on pair
        for _ in range(2):  # Run a couple iterations to handle multi-step chains
            for stmt in ast.walk(ast.Module(body=stmts, type_ignores=[])):
                if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                    target = stmt.targets[0]
                    if isinstance(target, ast.Name):
                        var_name = target.id
                        if isinstance(stmt.value, ast.Subscript):
                            container_type: Type = Interface("any")
                            if isinstance(stmt.value.value, ast.Name):
                                container_name = stmt.value.value.id
                                if container_name in var_types:
                                    container_type = var_types[container_name]
                            if isinstance(container_type, Slice):
                                var_types[var_name] = container_type.element
                            elif isinstance(container_type, Tuple):
                                if isinstance(stmt.value.slice, ast.Constant) and isinstance(stmt.value.slice.value, int):
                                    idx = stmt.value.slice.value
                                    if 0 <= idx < len(container_type.elements):
                                        var_types[var_name] = container_type.elements[idx]
        # Fifth pass: unify types from if/else branches
        for stmt in ast.walk(ast.Module(body=stmts, type_ignores=[])):
            if isinstance(stmt, ast.If) and stmt.orelse:
                then_vars = self._collect_branch_var_types(stmt.body, var_types)
                else_vars = self._collect_branch_var_types(stmt.orelse, var_types)
                unified = self._unify_branch_types(then_vars, else_vars)
                for var, typ in unified.items():
                    # Only update if not already set or currently generic
                    if var not in var_types or var_types[var] == Interface("any"):
                        var_types[var] = typ
        # Sixth pass: variables assigned both None and typed value
        # For strings, use empty string as sentinel (not pointer)
        # For ints, use -1 as sentinel (simpler than pointers)
        for var_name in vars_assigned_none:
            if var_name in vars_concrete_type:
                concrete_type = vars_concrete_type[var_name]
                if concrete_type == STRING:
                    # String with None -> just use string (empty = None)
                    var_types[var_name] = STRING
                elif concrete_type == INT:
                    # Int with None -> use sentinel (-1 = None)
                    var_types[var_name] = INT
                    sentinel_ints.add(var_name)
                elif concrete_type == Interface("Node"):
                    # Node with None -> use Node interface (nilable in Go)
                    var_types[var_name] = Interface("Node")
                else:
                    # Other types -> use Optional (pointer)
                    var_types[var_name] = Optional(concrete_type)
        # Seventh pass: variables with multiple Node types (not assigned None)
        # These are variables assigned different Node subtypes in branches or sequentially
        # The unified Node type takes precedence over any single assignment's type
        for var_name, concrete_type in vars_concrete_type.items():
            if var_name not in vars_assigned_none and concrete_type == Interface("Node"):
                var_types[var_name] = Interface("Node")
        return var_types, tuple_vars, sentinel_ints, list_element_unions

    def _infer_iterable_type(self, node: ast.expr, var_types: dict[str, Type]) -> Type:
        """Infer the type of an iterable expression."""
        return type_inference.infer_iterable_type(node, var_types, self._current_class_name, self.symbols)

    def _infer_element_type_from_append_arg(self, arg: ast.expr, var_types: dict[str, Type]) -> Type:
        """Infer slice element type from what's being appended."""
        # Constant literals
        if isinstance(arg, ast.Constant):
            if isinstance(arg.value, bool):
                return BOOL
            if isinstance(arg.value, int):
                return INT
            if isinstance(arg.value, str):
                return STRING
            if isinstance(arg.value, float):
                return FLOAT
        # Variable reference with known type (e.g., loop variable)
        if isinstance(arg, ast.Name):
            if arg.id in var_types:
                return var_types[arg.id]
            # Check function parameters
            if self._current_func_info:
                for p in self._current_func_info.params:
                    if p.name == arg.id:
                        return p.typ
        # Field access: self.field or obj.field
        if isinstance(arg, ast.Attribute):
            if isinstance(arg.value, ast.Name):
                if arg.value.id == "self" and self._current_class_name:
                    struct_info = self.symbols.structs.get(self._current_class_name)
                    if struct_info:
                        field_info = struct_info.fields.get(arg.attr)
                        if field_info:
                            return field_info.typ
                elif arg.value.id in var_types:
                    obj_type = var_types[arg.value.id]
                    struct_name = self._extract_struct_name(obj_type)
                    if struct_name and struct_name in self.symbols.structs:
                        field_info = self.symbols.structs[struct_name].fields.get(arg.attr)
                        if field_info:
                            return field_info.typ
        # Subscript: container[i] -> infer element type from container
        if isinstance(arg, ast.Subscript):
            container_type = self._infer_container_type_from_ast(arg.value, var_types)
            if container_type == STRING:
                return STRING  # string[i] in Python returns a string
            if isinstance(container_type, Slice):
                return container_type.element
        # Tuple literal: (a, b, ...) -> Tuple(type(a), type(b), ...)
        if isinstance(arg, ast.Tuple):
            elem_types = []
            for elt in arg.elts:
                elem_types.append(self._infer_element_type_from_append_arg(elt, var_types))
            return Tuple(tuple(elem_types))
        # Method calls
        if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute):
            method = arg.func.attr
            # String methods that return string
            if method in ("strip", "lstrip", "rstrip", "lower", "upper", "replace", "join", "format", "to_sexp"):
                return STRING
            # .Copy() returns same type
            if method == "Copy":
                # x.Copy() where x is ctx -> *ParseContext
                if isinstance(arg.func.value, ast.Name):
                    var = arg.func.value.id
                    if var == "ctx":
                        return Pointer(StructRef("ParseContext"))
        # Function/constructor calls
        if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name):
            func_name = arg.func.id
            # String conversion functions
            if func_name in ("str", "string", "substring", "chr"):
                return STRING
            # Constructor calls
            if func_name in self.symbols.structs:
                info = self.symbols.structs[func_name]
                if info.is_node:
                    return Interface("Node")
                return Pointer(StructRef(func_name))
            # Function return types
            if func_name in self.symbols.functions:
                return self.symbols.functions[func_name].return_type
        # Method calls: obj.method() -> look up method return type
        if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute):
            method_name = arg.func.attr
            # Handle self.method() calls directly using current class name
            # (can't use _infer_expr_type_from_ast here - _type_ctx not set yet)
            if isinstance(arg.func.value, ast.Name) and arg.func.value.id == "self":
                if self._current_class_name and self._current_class_name in self.symbols.structs:
                    method_info = self.symbols.structs[self._current_class_name].methods.get(method_name)
                    if method_info:
                        return method_info.return_type
            # Handle other obj.method() calls via var_types lookup
            elif isinstance(arg.func.value, ast.Name) and arg.func.value.id in var_types:
                obj_type = var_types[arg.func.value.id]
                struct_name = self._extract_struct_name(obj_type)
                if struct_name and struct_name in self.symbols.structs:
                    method_info = self.symbols.structs[struct_name].methods.get(method_name)
                    if method_info:
                        return method_info.return_type
        return Interface("any")

    def _infer_container_type_from_ast(self, node: ast.expr, var_types: dict[str, Type]) -> Type:
        """Infer the type of a container expression from AST."""
        return type_inference.infer_container_type_from_ast(
            node, self.symbols, self._current_class_name, self._current_func_info, var_types
        )

    def _unify_branch_types(self, then_vars: dict[str, Type], else_vars: dict[str, Type]) -> dict[str, Type]:
        """Unify variable types from if/else branches."""
        unified: dict[str, Type] = {}
        for var in set(then_vars) | set(else_vars):
            t1, t2 = then_vars.get(var), else_vars.get(var)
            if t1 == t2 and t1 is not None:
                unified[var] = t1
            elif t1 is not None and t2 is None:
                unified[var] = t1
            elif t2 is not None and t1 is None:
                unified[var] = t2
        return unified

    def _collect_branch_var_types(self, stmts: list[ast.stmt], var_types: dict[str, Type]) -> dict[str, Type]:
        """Collect variable types assigned in a list of statements (for branch analysis)."""
        branch_vars: dict[str, Type] = {}
        # Walk entire subtree to find all assignments (may be nested in for/while/etc)
        for stmt in ast.walk(ast.Module(body=stmts, type_ignores=[])):
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                target = stmt.targets[0]
                if isinstance(target, ast.Name):
                    var_name = target.id
                    # Infer type from value
                    if isinstance(stmt.value, ast.Constant):
                        if isinstance(stmt.value.value, str):
                            branch_vars[var_name] = STRING
                        elif isinstance(stmt.value.value, int) and not isinstance(stmt.value.value, bool):
                            branch_vars[var_name] = INT
                        elif isinstance(stmt.value.value, bool):
                            branch_vars[var_name] = BOOL
                    elif isinstance(stmt.value, ast.BinOp):
                        # String concatenation -> STRING
                        if isinstance(stmt.value.op, ast.Add):
                            left_type = self._infer_branch_expr_type(stmt.value.left, var_types, branch_vars)
                            right_type = self._infer_branch_expr_type(stmt.value.right, var_types, branch_vars)
                            if left_type == STRING or right_type == STRING:
                                branch_vars[var_name] = STRING
                            elif left_type == INT or right_type == INT:
                                branch_vars[var_name] = INT
                    elif isinstance(stmt.value, ast.Name):
                        # Assign from another variable
                        if stmt.value.id in var_types:
                            branch_vars[var_name] = var_types[stmt.value.id]
                        elif stmt.value.id in branch_vars:
                            branch_vars[var_name] = branch_vars[stmt.value.id]
                    # Method calls (e.g., x.to_sexp() returns STRING)
                    elif isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Attribute):
                        method = stmt.value.func.attr
                        if method in ("to_sexp", "format", "strip", "lower", "upper", "replace", "join"):
                            branch_vars[var_name] = STRING
        return branch_vars

    def _infer_branch_expr_type(self, node: ast.expr, var_types: dict[str, Type], branch_vars: dict[str, Type]) -> Type:
        """Infer type of expression during branch analysis."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return STRING
            if isinstance(node.value, int) and not isinstance(node.value, bool):
                return INT
            if isinstance(node.value, bool):
                return BOOL
        if isinstance(node, ast.Name):
            if node.id in branch_vars:
                return branch_vars[node.id]
            if node.id in var_types:
                return var_types[node.id]
        if isinstance(node, ast.BinOp):
            left = self._infer_branch_expr_type(node.left, var_types, branch_vars)
            right = self._infer_branch_expr_type(node.right, var_types, branch_vars)
            if left == STRING or right == STRING:
                return STRING
            if left == INT or right == INT:
                return INT
        return Interface("any")

    def _synthesize_type(self, expr: "ir.Expr") -> Type:
        """Bottom-up type synthesis: compute type from expression structure."""
        return type_inference.synthesize_type(
            expr, self._type_ctx, self._current_func_info, self.symbols, self._node_types
        )

    def _synthesize_field_type(self, obj_type: Type, field: str) -> Type:
        """Look up field type from struct info."""
        return type_inference.synthesize_field_type(obj_type, field, self.symbols)

    def _synthesize_method_return_type(self, obj_type: Type, method: str) -> Type:
        """Look up method return type from struct info."""
        return type_inference.synthesize_method_return_type(obj_type, method, self.symbols, self._node_types)

    def _merge_keyword_args(self, obj_type: Type, method: str, args: list, node: ast.Call) -> list:
        """Merge keyword arguments into positional args at their proper positions."""
        return lowering.merge_keyword_args(
            obj_type, method, args, node, self.symbols, self._lower_expr, self._extract_struct_name
        )

    def _fill_default_args(self, obj_type: Type, method: str, args: list) -> list:
        """Fill in missing arguments with default values for methods with optional params."""
        return lowering.fill_default_args(obj_type, method, args, self.symbols, self._extract_struct_name)

    def _merge_keyword_args_for_func(self, func_info: FuncInfo, args: list, node: ast.Call) -> list:
        """Merge keyword arguments into positional args at their proper positions for free functions."""
        return lowering.merge_keyword_args_for_func(func_info, args, node, self._lower_expr)

    def _fill_default_args_for_func(self, func_info: FuncInfo, args: list) -> list:
        """Fill in missing arguments with default values for free functions with optional params."""
        return lowering.fill_default_args_for_func(func_info, args)

    def _add_address_of_for_ptr_params(self, obj_type: Type, method: str, args: list, orig_args: list[ast.expr]) -> list:
        """Add & when passing slice to pointer-to-slice parameter."""
        return lowering.add_address_of_for_ptr_params(
            obj_type, method, args, orig_args, self.symbols, self._extract_struct_name, self._infer_expr_type_from_ast
        )

    def _deref_for_slice_params(self, obj_type: Type, method: str, args: list, orig_args: list[ast.expr]) -> list:
        """Dereference * when passing pointer-to-slice to slice parameter."""
        return lowering.deref_for_slice_params(
            obj_type, method, args, orig_args, self.symbols, self._extract_struct_name, self._infer_expr_type_from_ast
        )

    def _deref_for_func_slice_params(self, func_name: str, args: list, orig_args: list[ast.expr]) -> list:
        """Dereference * when passing pointer-to-slice to slice parameter for free functions."""
        return lowering.deref_for_func_slice_params(
            func_name, args, orig_args, self.symbols, self._infer_expr_type_from_ast
        )

    def _extract_struct_name(self, typ: Type) -> str | None:
        """Extract struct name from wrapped types like Pointer, Optional, etc."""
        return type_inference.extract_struct_name(typ)

    def _coerce_args_to_node(self, func_info: "FuncInfo", args: list) -> list:
        """Add type assertions when passing interface{} to Node parameter."""
        return lowering.coerce_args_to_node(func_info, args)

    def _is_pointer_to_slice(self, typ: Type) -> bool:
        """Check if type is pointer-to-slice (Pointer(Slice) only, NOT Optional(Slice))."""
        return lowering.is_pointer_to_slice(typ)

    def _is_len_call(self, node: ast.expr) -> bool:
        """Check if node is a len() call."""
        return lowering.is_len_call(node)

    def _get_inner_slice(self, typ: Type) -> Slice | None:
        """Get the inner Slice from Pointer(Slice) only, NOT Optional(Slice)."""
        return lowering.get_inner_slice(typ)

    def _coerce_sentinel_to_ptr(self, obj_type: Type, method: str, args: list, orig_args: list) -> list:
        """Wrap sentinel ints with _intPtr() when passing to Optional(int) params."""
        return lowering.coerce_sentinel_to_ptr(
            obj_type, method, args, orig_args, self.symbols, self._type_ctx.sentinel_ints, self._extract_struct_name
        )

    def _infer_call_return_type(self, node: ast.Call) -> Type:
        """Infer the return type of a function or method call."""
        return type_inference.infer_call_return_type(
            node, self.symbols, self._type_ctx, self._current_func_info, self._current_class_name, self._node_types
        )

    def _synthesize_index_type(self, obj_type: Type) -> Type:
        """Derive element type from indexing a container."""
        return type_inference.synthesize_index_type(obj_type)

    def _coerce(self, expr: "ir.Expr", from_type: Type, to_type: Type) -> "ir.Expr":
        """Apply type coercions when synthesized type doesn't match expected."""
        return type_inference.coerce(
            expr, from_type, to_type, self._type_ctx, self._current_func_info, self.symbols, self._node_types
        )

    # ============================================================
    # EXPRESSION LOWERING (Phase 3)
    # ============================================================

    def _lower_expr_as_bool(self, node: ast.expr) -> "ir.Expr":
        """Lower expression used in boolean context, adding truthy checks as needed."""
        return lowering.lower_expr_as_bool(
            node, self._lower_expr, self._lower_expr_as_bool, self._infer_expr_type_from_ast,
            self._is_isinstance_call, self._resolve_type_name, self._type_ctx, self.symbols
        )

    def _lower_expr(self, node: ast.expr) -> "ir.Expr":
        """Lower a Python expression to IR."""
        from .. import ir
        method = f"_lower_expr_{node.__class__.__name__}"
        if hasattr(self, method):
            return getattr(self, method)(node)
        # Fallback for unimplemented expressions
        return ir.Var(name=f"TODO_{node.__class__.__name__}", typ=Interface("any"))

    def _lower_expr_Constant(self, node: ast.Constant) -> "ir.Expr":
        return lowering.lower_expr_Constant(node)

    def _lower_expr_Name(self, node: ast.Name) -> "ir.Expr":
        return lowering.lower_expr_Name(node, self._type_ctx, self.symbols)

    def _lower_expr_Attribute(self, node: ast.Attribute) -> "ir.Expr":
        return lowering.lower_expr_Attribute(
            node, self.symbols, self._type_ctx, self._current_class_name,
            NODE_FIELD_TYPES, self._lower_expr, self._is_node_interface_type
        )

    def _is_node_interface_type(self, typ: Type | None) -> bool:
        """Check if a type is the Node interface type."""
        return type_inference.is_node_interface_type(typ)

    def _is_node_subtype(self, typ: Type | None) -> bool:
        """Check if a type is a Node subtype (pointer to struct implementing Node)."""
        return type_inference.is_node_subtype(typ, self._node_types)

    def _lower_expr_Subscript(self, node: ast.Subscript) -> "ir.Expr":
        return lowering.lower_expr_Subscript(
            node, self._type_ctx, self._lower_expr, self._convert_negative_index, self._infer_expr_type_from_ast
        )

    def _convert_negative_index(self, idx_node: ast.expr, obj: "ir.Expr", parent: ast.AST) -> "ir.Expr":
        """Convert negative index -N to len(obj) - N."""
        return lowering.convert_negative_index(idx_node, obj, parent, self._lower_expr)

    def _infer_expr_type_from_ast(self, node: ast.expr) -> Type:
        """Infer the type of a Python AST expression without lowering it."""
        return type_inference.infer_expr_type_from_ast(
            node, self._type_ctx, self.symbols, self._current_func_info, self._current_class_name, self._node_types
        )

    def _lower_expr_BinOp(self, node: ast.BinOp) -> "ir.Expr":
        return lowering.lower_expr_BinOp(node, self._lower_expr, self._infer_expr_type_from_ast)

    def _is_sentinel_int(self, node: ast.expr) -> bool:
        """Check if an expression is a sentinel int (uses a sentinel value for None)."""
        return lowering.is_sentinel_int(node, self._type_ctx, self._current_class_name, SENTINEL_INT_FIELDS)

    def _get_sentinel_value(self, node: ast.expr) -> int | None:
        """Get the sentinel value for a sentinel int expression, or None if not a sentinel int."""
        return lowering.get_sentinel_value(node, self._type_ctx, self._current_class_name, SENTINEL_INT_FIELDS)

    def _lower_expr_Compare(self, node: ast.Compare) -> "ir.Expr":
        return lowering.lower_expr_Compare(
            node, self._lower_expr, self._infer_expr_type_from_ast,
            self._type_ctx, self._current_class_name, SENTINEL_INT_FIELDS
        )

    def _lower_expr_BoolOp(self, node: ast.BoolOp) -> "ir.Expr":
        return lowering.lower_expr_BoolOp(node, self._lower_expr_as_bool)

    def _lower_expr_UnaryOp(self, node: ast.UnaryOp) -> "ir.Expr":
        return lowering.lower_expr_UnaryOp(node, self._lower_expr, self._lower_expr_as_bool)

    def _lower_expr_Call(self, node: ast.Call) -> "ir.Expr":
        from .. import ir
        args = [self._lower_expr(a) for a in node.args]
        # Method call
        if isinstance(node.func, ast.Attribute):
            method = node.func.attr
            # Handle chr(n).encode("utf-8") -> []byte(string(rune(n)))
            if method == "encode" and isinstance(node.func.value, ast.Call):
                inner_call = node.func.value
                if isinstance(inner_call.func, ast.Name) and inner_call.func.id == "chr":
                    # chr(n).encode("utf-8") -> cast to []byte
                    chr_arg = self._lower_expr(inner_call.args[0])
                    rune_cast = ir.Cast(expr=chr_arg, to_type=RUNE, typ=RUNE, loc=self._loc_from_node(node))
                    str_cast = ir.Cast(expr=rune_cast, to_type=STRING, typ=STRING, loc=self._loc_from_node(node))
                    return ir.Cast(expr=str_cast, to_type=Slice(BYTE), typ=Slice(BYTE), loc=self._loc_from_node(node))
            # Handle str.encode("utf-8") -> []byte(str)
            if method == "encode":
                obj = self._lower_expr(node.func.value)
                return ir.Cast(expr=obj, to_type=Slice(BYTE), typ=Slice(BYTE), loc=self._loc_from_node(node))
            # Handle bytes.decode("utf-8") -> string(bytes)
            if method == "decode":
                obj = self._lower_expr(node.func.value)
                return ir.Cast(expr=obj, to_type=STRING, typ=STRING, loc=self._loc_from_node(node))
            obj = self._lower_expr(node.func.value)
            # Handle Python list methods that need special Go treatment
            if method == "append" and args:
                # Look up actual type of the object (might be pointer to slice for params)
                obj_type = self._infer_expr_type_from_ast(node.func.value)
                # Check if appending to a byte slice - need to cast int to byte
                elem_type = None
                if isinstance(obj_type, Slice):
                    elem_type = obj_type.element
                elif isinstance(obj_type, Pointer) and isinstance(obj_type.target, Slice):
                    elem_type = obj_type.target.element
                # Coerce int to byte for byte slices (Python bytearray.append accepts int)
                coerced_args = args
                if elem_type == BYTE and len(args) == 1:
                    arg = args[0]
                    # Check if arg is int-typed (via AST inference or lowered type)
                    arg_ast_type = self._infer_expr_type_from_ast(node.args[0])
                    if arg_ast_type == INT or (hasattr(arg, 'typ') and arg.typ == INT):
                        coerced_args = [ir.Cast(expr=arg, to_type=BYTE, typ=BYTE, loc=arg.loc)]
                # list.append(x) -> append(list, x) in Go (handled via MethodCall for now)
                return ir.MethodCall(
                    obj=obj, method="append", args=coerced_args,
                    receiver_type=obj_type if obj_type != Interface("any") else Slice(Interface("any")),
                    typ=VOID, loc=self._loc_from_node(node)
                )
            # Infer receiver type for proper method lookup
            obj_type = self._infer_expr_type_from_ast(node.func.value)
            if method == "pop" and not args and isinstance(obj_type, Slice):
                # list.pop() -> return last element and shrink slice (only for slices)
                return ir.MethodCall(
                    obj=obj, method="pop", args=[],
                    receiver_type=obj_type, typ=obj_type.element, loc=self._loc_from_node(node)
                )
            # Check if calling a method on a Node-typed expression that needs type assertion
            # Do this early so we can use the asserted type for default arg lookup
            if self._is_node_interface_type(obj_type) and method in NODE_METHOD_TYPES:
                struct_name = NODE_METHOD_TYPES[method]
                asserted_type = Pointer(StructRef(struct_name))
                obj = ir.TypeAssert(
                    expr=obj, asserted=asserted_type, safe=True,
                    typ=asserted_type, loc=self._loc_from_node(node.func.value)
                )
                # Use asserted type for subsequent lookups
                obj_type = asserted_type
            # Merge keyword arguments into args at proper positions
            args = self._merge_keyword_args(obj_type, method, args, node)
            # Fill in default values for any remaining missing parameters
            args = self._fill_default_args(obj_type, method, args)
            # Coerce sentinel ints to pointers for *int params
            args = self._coerce_sentinel_to_ptr(obj_type, method, args, node.args)
            # Add & for pointer-to-slice params
            args = self._add_address_of_for_ptr_params(obj_type, method, args, node.args)
            # Dereference * for slice params
            args = self._deref_for_slice_params(obj_type, method, args, node.args)
            # Infer return type
            ret_type = self._synthesize_method_return_type(obj_type, method)
            return ir.MethodCall(
                obj=obj, method=method, args=args,
                receiver_type=obj_type, typ=ret_type, loc=self._loc_from_node(node)
            )
        # Free function call
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            # Check for len()
            if func_name == "len" and args:
                arg = args[0]
                arg_type = self._infer_expr_type_from_ast(node.args[0])
                # Dereference Pointer(Slice) or Optional(Slice) for len()
                inner_slice = self._get_inner_slice(arg_type)
                if inner_slice is not None:
                    arg = ir.UnaryOp(op="*", operand=arg, typ=inner_slice, loc=arg.loc)
                return ir.Len(expr=arg, typ=INT, loc=self._loc_from_node(node))
            # Check for bool() - convert to comparison
            if func_name == "bool" and args:
                # bool(x) -> x != 0 for ints, x != "" for strings, x != nil for pointers
                arg_type = self._infer_expr_type_from_ast(node.args[0])
                if arg_type == INT:
                    return ir.BinaryOp(op="!=", left=args[0], right=ir.IntLit(value=0, typ=INT), typ=BOOL, loc=self._loc_from_node(node))
                if arg_type == STRING:
                    return ir.BinaryOp(op="!=", left=args[0], right=ir.StringLit(value="", typ=STRING), typ=BOOL, loc=self._loc_from_node(node))
                # Default: assume pointer/optional, check != nil
                return ir.IsNil(expr=args[0], negated=True, typ=BOOL, loc=self._loc_from_node(node))
            # Check for list() copy
            if func_name == "list" and args:
                # list(x) is a copy operation - preserve element type from source
                source_type = getattr(args[0], 'typ', None)
                if isinstance(source_type, Slice):
                    result_type = source_type
                else:
                    result_type = Slice(Interface("any"))
                return ir.MethodCall(
                    obj=args[0], method="copy", args=[],
                    receiver_type=result_type, typ=result_type, loc=self._loc_from_node(node)
                )
            # Check for bytearray() constructor
            if func_name == "bytearray" and not args:
                return ir.MakeSlice(
                    element_type=BYTE, length=None, capacity=None,
                    typ=Slice(BYTE), loc=self._loc_from_node(node)
                )
            # Check for int(s, base) conversion
            if func_name == "int" and len(args) == 2:
                return ir.Call(
                    func="_parseInt", args=args,
                    typ=INT, loc=self._loc_from_node(node)
                )
            # Check for int(s) - string to int conversion
            if func_name == "int" and len(args) == 1:
                arg_type = self._infer_expr_type_from_ast(node.args[0])
                if arg_type == STRING:
                    # String to int: use _parseInt with base 10
                    return ir.Call(
                        func="_parseInt",
                        args=[args[0], ir.IntLit(value=10, typ=INT, loc=self._loc_from_node(node))],
                        typ=INT, loc=self._loc_from_node(node)
                    )
                else:
                    # Already numeric: just cast to int
                    return ir.Cast(expr=args[0], to_type=INT, typ=INT, loc=self._loc_from_node(node))
            # Check for str(n) - int to string conversion
            if func_name == "str" and len(args) == 1:
                arg_type = self._infer_expr_type_from_ast(node.args[0])
                if arg_type == INT:
                    return ir.Call(
                        func="_intToStr", args=args,
                        typ=STRING, loc=self._loc_from_node(node)
                    )
                # Handle *int or Optional[int] - dereference first
                if isinstance(arg_type, (Optional, Pointer)):
                    inner = arg_type.inner if isinstance(arg_type, Optional) else arg_type.target
                    if inner == INT:
                        deref_arg = ir.UnaryOp(op="*", operand=args[0], typ=INT, loc=self._loc_from_node(node))
                        return ir.Call(
                            func="_intToStr", args=[deref_arg],
                            typ=STRING, loc=self._loc_from_node(node)
                        )
                # Already string or convert via fmt
                return ir.Cast(expr=args[0], to_type=STRING, typ=STRING, loc=self._loc_from_node(node))
            # Check for ord(c) -> int(c[0]) (get Unicode code point)
            if func_name == "ord" and len(args) == 1:
                # ord(c) -> cast the first character to int
                # In Go: int(c[0]) for strings, int(c) for bytes/runes
                arg_type = self._infer_expr_type_from_ast(node.args[0])
                if arg_type in (BYTE, RUNE):
                    # Already a byte/rune: just cast to int
                    return ir.Cast(expr=args[0], to_type=INT, typ=INT, loc=self._loc_from_node(node))
                else:
                    # String or unknown: index to get first byte, then cast to int
                    indexed = ir.Index(obj=args[0], index=ir.IntLit(value=0, typ=INT), typ=BYTE)
                    return ir.Cast(expr=indexed, to_type=INT, typ=INT, loc=self._loc_from_node(node))
            # Check for chr(n) -> string(rune(n))
            if func_name == "chr" and len(args) == 1:
                rune_cast = ir.Cast(expr=args[0], to_type=RUNE, typ=RUNE, loc=self._loc_from_node(node))
                return ir.Cast(expr=rune_cast, to_type=STRING, typ=STRING, loc=self._loc_from_node(node))
            # Check for max(a, b) -> a > b ? a : b
            if func_name == "max" and len(args) == 2:
                cond = ir.BinaryOp(op=">", left=args[0], right=args[1], typ=BOOL, loc=self._loc_from_node(node))
                return ir.Ternary(cond=cond, then_expr=args[0], else_expr=args[1], typ=INT, loc=self._loc_from_node(node))
            # Check for min(a, b) -> a < b ? a : b
            if func_name == "min" and len(args) == 2:
                cond = ir.BinaryOp(op="<", left=args[0], right=args[1], typ=BOOL, loc=self._loc_from_node(node))
                return ir.Ternary(cond=cond, then_expr=args[0], else_expr=args[1], typ=INT, loc=self._loc_from_node(node))
            # Check for isinstance(x, Type) -> IsType expression
            if func_name == "isinstance" and len(node.args) == 2:
                expr = self._lower_expr(node.args[0])
                if isinstance(node.args[1], ast.Name):
                    type_name = node.args[1].id
                    tested_type = self._resolve_type_name(type_name)
                    return ir.IsType(expr=expr, tested_type=tested_type, typ=BOOL, loc=self._loc_from_node(node))
            # Check for constructor calls (class names)
            if func_name in self.symbols.structs:
                struct_info = self.symbols.structs[func_name]
                # If struct needs constructor, call NewXxx instead of StructLit
                if struct_info.needs_constructor:
                    # Build param name -> index map for keyword arg handling
                    param_indices: dict[str, int] = {}
                    for i, param_name in enumerate(struct_info.init_params):
                        param_indices[param_name] = i
                    # Initialize args list with Nones
                    n_params = len(struct_info.init_params)
                    ctor_args: list[ir.Expr | None] = [None] * n_params
                    # First, place positional args
                    for i, arg_ast in enumerate(node.args):
                        if i < n_params:
                            param_name = struct_info.init_params[i]
                            field_name = struct_info.param_to_field.get(param_name, param_name)
                            field_info = struct_info.fields.get(field_name)
                            expected_type = field_info.typ if field_info else None
                            if isinstance(expected_type, Pointer) and isinstance(expected_type.target, Slice):
                                expected_type = expected_type.target
                            if isinstance(arg_ast, ast.List):
                                ctor_args[i] = self._lower_expr_List(arg_ast, expected_type)
                            elif (isinstance(arg_ast, ast.Call) and isinstance(arg_ast.func, ast.Name)
                                  and arg_ast.func.id == "list" and arg_ast.args):
                                ctor_args[i] = self._lower_list_call_with_expected_type(arg_ast, expected_type)
                            else:
                                ctor_args[i] = args[i]
                    # Then, place keyword args in their proper positions
                    for kw in node.keywords:
                        if kw.arg and kw.arg in param_indices:
                            idx = param_indices[kw.arg]
                            param_name = struct_info.init_params[idx]
                            field_name = struct_info.param_to_field.get(param_name, param_name)
                            field_info = struct_info.fields.get(field_name)
                            expected_type = field_info.typ if field_info else None
                            if isinstance(expected_type, Pointer) and isinstance(expected_type.target, Slice):
                                expected_type = expected_type.target
                            if isinstance(kw.value, ast.List):
                                ctor_args[idx] = self._lower_expr_List(kw.value, expected_type)
                            elif (isinstance(kw.value, ast.Call) and isinstance(kw.value.func, ast.Name)
                                  and kw.value.func.id == "list" and kw.value.args):
                                ctor_args[idx] = self._lower_list_call_with_expected_type(kw.value, expected_type)
                            else:
                                ctor_args[idx] = self._lower_expr(kw.value)
                    # Fill in default values for any remaining None slots
                    for i in range(n_params):
                        if ctor_args[i] is None:
                            param_name = struct_info.init_params[i]
                            field_name = struct_info.param_to_field.get(param_name, param_name)
                            field_info = struct_info.fields.get(field_name)
                            field_type = field_info.typ if field_info else Interface("any")
                            ctor_args[i] = self._make_default_value(field_type, self._loc_from_node(node))
                    return ir.Call(
                        func=f"New{func_name}",
                        args=ctor_args,  # type: ignore
                        typ=Pointer(StructRef(func_name)),
                        loc=self._loc_from_node(node),
                    )
                # Simple struct: emit StructLit with fields mapped from positional and keyword args
                fields: dict[str, ir.Expr] = {}
                for i, arg_ast in enumerate(node.args):
                    if i < len(struct_info.init_params):
                        param_name = struct_info.init_params[i]
                        # Map param name to actual field name (e.g., in_process_sub -> _in_process_sub)
                        field_name = struct_info.param_to_field.get(param_name, param_name)
                        # Look up field type for expected type context
                        field_info = struct_info.fields.get(field_name)
                        expected_type = field_info.typ if field_info else None
                        # Handle pointer-wrapped slice types
                        if isinstance(expected_type, Pointer) and isinstance(expected_type.target, Slice):
                            expected_type = expected_type.target
                        # Re-lower list args with expected type context
                        if isinstance(arg_ast, ast.List):
                            fields[field_name] = self._lower_expr_List(arg_ast, expected_type)
                        else:
                            fields[field_name] = args[i]
                # Handle keyword arguments for struct literals
                if node.keywords:
                    for kw in node.keywords:
                        if kw.arg:
                            # Map param name to field name (handle snake_case to PascalCase)
                            field_name = struct_info.param_to_field.get(kw.arg, kw.arg)
                            field_info = struct_info.fields.get(field_name)
                            expected_type = field_info.typ if field_info else None
                            if isinstance(expected_type, Pointer) and isinstance(expected_type.target, Slice):
                                expected_type = expected_type.target
                            if isinstance(kw.value, ast.List):
                                fields[field_name] = self._lower_expr_List(kw.value, expected_type)
                            elif (isinstance(kw.value, ast.Call) and isinstance(kw.value.func, ast.Name)
                                  and kw.value.func.id == "list" and kw.value.args):
                                fields[field_name] = self._lower_list_call_with_expected_type(kw.value, expected_type)
                            else:
                                fields[field_name] = self._lower_expr(kw.value)
                # Add constant field initializations from __init__
                for const_name, const_value in struct_info.const_fields.items():
                    if const_name not in fields:
                        fields[const_name] = ir.StringLit(value=const_value, typ=STRING, loc=self._loc_from_node(node))
                return ir.StructLit(
                    struct_name=func_name, fields=fields,
                    typ=Pointer(StructRef(func_name)), loc=self._loc_from_node(node)
                )
            # Look up function return type and fill default args from symbol table
            ret_type: Type = Interface("any")
            if func_name in self.symbols.functions:
                func_info = self.symbols.functions[func_name]
                ret_type = func_info.return_type
                # Merge keyword arguments into positional args
                args = self._merge_keyword_args_for_func(func_info, args, node)
                # Fill in default arguments
                args = self._fill_default_args_for_func(func_info, args)
                # Dereference * for slice params
                args = self._deref_for_func_slice_params(func_name, args, node.args)
                # Add type assertions for interface{} -> Node coercion
                args = self._coerce_args_to_node(func_info, args)
            return ir.Call(func=func_name, args=args, typ=ret_type, loc=self._loc_from_node(node))
        return ir.Var(name="TODO_Call", typ=Interface("any"))

    def _lower_expr_IfExp(self, node: ast.IfExp) -> "ir.Expr":
        return lowering.lower_expr_IfExp(
            node, self._lower_expr, self._lower_expr_as_bool,
            self._extract_attr_kind_check, self._type_ctx
        )

    def _lower_expr_List(self, node: ast.List, expected_type: Type | None = None) -> "ir.Expr":
        return lowering.lower_expr_List(
            node, self._lower_expr, self._infer_expr_type_from_ast, self._type_ctx.expected, expected_type
        )

    def _lower_list_call_with_expected_type(self, node: ast.Call, expected_type: Type | None) -> "ir.Expr":
        """Handle list(x) call with expected type context for covariant copies."""
        return lowering.lower_list_call_with_expected_type(node, self._lower_expr, expected_type)

    def _lower_expr_Dict(self, node: ast.Dict) -> "ir.Expr":
        return lowering.lower_expr_Dict(node, self._lower_expr, self._infer_expr_type_from_ast)

    def _lower_expr_JoinedStr(self, node: ast.JoinedStr) -> "ir.Expr":
        """Lower Python f-string to StringFormat IR node."""
        return lowering.lower_expr_JoinedStr(node, self._lower_expr)

    def _lower_expr_Tuple(self, node: ast.Tuple) -> "ir.Expr":
        """Lower Python tuple literal to TupleLit IR node."""
        return lowering.lower_expr_Tuple(node, self._lower_expr)

    def _lower_expr_Set(self, node: ast.Set) -> "ir.Expr":
        """Lower Python set literal to SetLit IR node."""
        return lowering.lower_expr_Set(node, self._lower_expr)

    def _binop_to_str(self, op: ast.operator) -> str:
        return lowering.binop_to_str(op)

    def _cmpop_to_str(self, op: ast.cmpop) -> str:
        return lowering.cmpop_to_str(op)

    def _unaryop_to_str(self, op: ast.unaryop) -> str:
        return lowering.unaryop_to_str(op)

    # ============================================================
    # STATEMENT LOWERING (Phase 3)
    # ============================================================

    def _lower_stmt(self, node: ast.stmt) -> "ir.Stmt":
        """Lower a Python statement to IR."""
        from .. import ir
        method = f"_lower_stmt_{node.__class__.__name__}"
        if hasattr(self, method):
            return getattr(self, method)(node)
        # Fallback for unimplemented statements
        return ir.ExprStmt(expr=ir.Var(name=f"TODO_{node.__class__.__name__}", typ=Interface("any")))

    def _lower_stmts(self, stmts: list[ast.stmt]) -> list["ir.Stmt"]:
        """Lower a list of statements."""
        return [self._lower_stmt(s) for s in stmts]

    def _lower_stmt_Expr(self, node: ast.Expr) -> "ir.Stmt":
        return lowering.lower_stmt_Expr(node, self._lower_expr)

    def _is_super_init_call(self, node: ast.expr) -> bool:
        """Check if expression is super().__init__(...)."""
        return lowering.is_super_init_call(node)

    def _lower_stmt_Assign(self, node: ast.Assign) -> "ir.Stmt":
        from .. import ir
        from ..ir import Tuple as TupleType
        # Check VAR_TYPE_OVERRIDES to set expected type before lowering
        if len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                func_name = self._current_func_info.name if self._current_func_info else ""
                override_key = (func_name, target.id)
                if override_key in VAR_TYPE_OVERRIDES:
                    self._type_ctx.expected = VAR_TYPE_OVERRIDES[override_key]
            # For field assignments (self.field = value), use field type as expected
            elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                if target.value.id == "self" and self._current_class_name:
                    struct_info = self.symbols.structs.get(self._current_class_name)
                    if struct_info:
                        field_info = struct_info.fields.get(target.attr)
                        if field_info:
                            self._type_ctx.expected = field_info.typ
        value = self._lower_expr(node.value)
        self._type_ctx.expected = None  # Reset expected type
        if len(node.targets) == 1:
            target = node.targets[0]
            # Handle single var = tuple-returning func: x = func() -> x0, x1 := func()
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Call):
                ret_type = self._infer_call_return_type(node.value)
                if isinstance(ret_type, TupleType) and len(ret_type.elements) > 1:
                    # Generate synthetic variable names and track for later index access
                    base_name = target.id
                    synthetic_names = [f"{base_name}{i}" for i in range(len(ret_type.elements))]
                    self._type_ctx.tuple_vars[base_name] = synthetic_names
                    # Also track types of synthetic vars
                    for i, syn_name in enumerate(synthetic_names):
                        self._type_ctx.var_types[syn_name] = ret_type.elements[i]
                    targets = []
                    for i in range(len(ret_type.elements)):
                        targets.append(ir.VarLV(name=f"{base_name}{i}", loc=self._loc_from_node(target)))
                    return ir.TupleAssign(
                        targets=targets,
                        value=value,
                        loc=self._loc_from_node(node)
                    )
            # Handle simple pop: var = list.pop() -> var = list[len(list)-1]; list = list[:len(list)-1]
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Attribute) and node.value.func.attr == "pop" and not node.value.args:
                    obj = self._lower_expr(node.value.func.value)
                    obj_type = self._infer_expr_type_from_ast(node.value.func.value)
                    if isinstance(obj_type, Slice):
                        obj_lval = self._lower_lvalue(node.value.func.value)
                        lval = self._lower_lvalue(target)
                        elem_type = obj_type.element
                        len_minus_1 = ir.BinaryOp(op="-", left=ir.Len(expr=obj, typ=INT), right=ir.IntLit(value=1, typ=INT), typ=INT)
                        block = ir.Block(body=[
                            ir.Assign(target=lval, value=ir.Index(obj=obj, index=len_minus_1, typ=elem_type)),
                            ir.Assign(target=obj_lval, value=ir.SliceExpr(obj=obj, high=len_minus_1, typ=obj_type)),
                        ], loc=self._loc_from_node(node))
                        block.no_scope = True  # Emit without braces
                        return block
            # Handle tuple unpacking: a, b = func() where func returns tuple
            if isinstance(target, ast.Tuple) and len(target.elts) == 2:
                # Special case for popping from stack with tuple unpacking
                if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
                    if node.value.func.attr == "pop":
                        # a, b = stack.pop() -> entry := stack[len(stack)-1]; stack = stack[:len(stack)-1]; a = entry.F0; b = entry.F1
                        obj = self._lower_expr(node.value.func.value)
                        obj_lval = self._lower_lvalue(node.value.func.value)
                        lval0 = self._lower_lvalue(target.elts[0])
                        lval1 = self._lower_lvalue(target.elts[1])
                        len_minus_1 = ir.BinaryOp(op="-", left=ir.Len(expr=obj, typ=INT), right=ir.IntLit(value=1, typ=INT), typ=INT)
                        # Infer tuple element type from the list's type if available
                        entry_type: Type = Tuple((BOOL, BOOL))  # Default
                        if isinstance(node.value.func.value, ast.Name):
                            var_name = node.value.func.value.id
                            if var_name in self._type_ctx.var_types:
                                list_type = self._type_ctx.var_types[var_name]
                                if isinstance(list_type, Slice) and isinstance(list_type.element, Tuple):
                                    entry_type = list_type.element
                        # Get field types from entry_type
                        f0_type = entry_type.elements[0] if isinstance(entry_type, Tuple) and len(entry_type.elements) > 0 else BOOL
                        f1_type = entry_type.elements[1] if isinstance(entry_type, Tuple) and len(entry_type.elements) > 1 else BOOL
                        entry_var = ir.Var(name="_entry", typ=entry_type)
                        return ir.Block(body=[
                            ir.VarDecl(name="_entry", typ=entry_type, value=ir.Index(obj=obj, index=len_minus_1, typ=entry_type)),
                            ir.Assign(target=obj_lval, value=ir.SliceExpr(obj=obj, high=len_minus_1, typ=Interface("any"))),
                            ir.Assign(target=lval0, value=ir.FieldAccess(obj=entry_var, field="F0", typ=f0_type)),
                            ir.Assign(target=lval1, value=ir.FieldAccess(obj=entry_var, field="F1", typ=f1_type)),
                        ], loc=self._loc_from_node(node))
                    else:
                        # General tuple unpacking: a, b = obj.method()
                        lval0 = self._lower_lvalue(target.elts[0])
                        lval1 = self._lower_lvalue(target.elts[1])
                        return ir.TupleAssign(
                            targets=[lval0, lval1],
                            value=value,
                            loc=self._loc_from_node(node)
                        )
                # General tuple unpacking for function calls: a, b = func()
                if isinstance(node.value, ast.Call):
                    lval0 = self._lower_lvalue(target.elts[0])
                    lval1 = self._lower_lvalue(target.elts[1])
                    return ir.TupleAssign(
                        targets=[lval0, lval1],
                        value=value,
                        loc=self._loc_from_node(node)
                    )
                # Tuple unpacking from index: a, b = list[idx] where list is []Tuple
                if isinstance(node.value, ast.Subscript):
                    # Infer tuple element type from the list's type
                    entry_type: Type = Tuple((Interface("any"), Interface("any")))  # Default
                    if isinstance(node.value.value, ast.Name):
                        var_name = node.value.value.id
                        if var_name in self._type_ctx.var_types:
                            list_type = self._type_ctx.var_types[var_name]
                            if isinstance(list_type, Slice) and isinstance(list_type.element, Tuple):
                                entry_type = list_type.element
                    # Get field types from entry_type
                    f0_type = entry_type.elements[0] if isinstance(entry_type, Tuple) and len(entry_type.elements) > 0 else Interface("any")
                    f1_type = entry_type.elements[1] if isinstance(entry_type, Tuple) and len(entry_type.elements) > 1 else Interface("any")
                    lval0 = self._lower_lvalue(target.elts[0])
                    lval1 = self._lower_lvalue(target.elts[1])
                    entry_var = ir.Var(name="_entry", typ=entry_type)
                    # Update var_types for the targets
                    if isinstance(target.elts[0], ast.Name):
                        self._type_ctx.var_types[target.elts[0].id] = f0_type
                    if isinstance(target.elts[1], ast.Name):
                        self._type_ctx.var_types[target.elts[1].id] = f1_type
                    return ir.Block(body=[
                        ir.VarDecl(name="_entry", typ=entry_type, value=value),
                        ir.Assign(target=lval0, value=ir.FieldAccess(obj=entry_var, field="F0", typ=f0_type)),
                        ir.Assign(target=lval1, value=ir.FieldAccess(obj=entry_var, field="F1", typ=f1_type)),
                    ], loc=self._loc_from_node(node))
                # Tuple unpacking from tuple literal: a, b = x, y
                if isinstance(node.value, ast.Tuple) and len(node.value.elts) == 2:
                    lval0 = self._lower_lvalue(target.elts[0])
                    lval1 = self._lower_lvalue(target.elts[1])
                    val0 = self._lower_expr(node.value.elts[0])
                    val1 = self._lower_expr(node.value.elts[1])
                    # Update var_types
                    if isinstance(target.elts[0], ast.Name):
                        self._type_ctx.var_types[target.elts[0].id] = self._synthesize_type(val0)
                    if isinstance(target.elts[1], ast.Name):
                        self._type_ctx.var_types[target.elts[1].id] = self._synthesize_type(val1)
                    block = ir.Block(body=[
                        ir.Assign(target=lval0, value=val0),
                        ir.Assign(target=lval1, value=val1),
                    ], loc=self._loc_from_node(node))
                    block.no_scope = True  # Don't emit braces
                    return block
            # Handle sentinel ints: var = None -> var = -1
            if isinstance(value, ir.NilLit) and self._is_sentinel_int(target):
                value = ir.IntLit(value=-1, typ=INT, loc=self._loc_from_node(node))
            # Track variable type dynamically for later use in nested scopes
            # Apply VAR_TYPE_OVERRIDES first, then coerce
            if isinstance(target, ast.Name):
                func_name = self._current_func_info.name if self._current_func_info else ""
                override_key = (func_name, target.id)
                if override_key in VAR_TYPE_OVERRIDES:
                    self._type_ctx.var_types[target.id] = VAR_TYPE_OVERRIDES[override_key]
            # Coerce value to target type if known
            if isinstance(target, ast.Name) and target.id in self._type_ctx.var_types:
                expected_type = self._type_ctx.var_types[target.id]
                from_type = self._synthesize_type(value)
                value = self._coerce(value, from_type, expected_type)
            # Track variable type dynamically for later use in nested scopes
            if isinstance(target, ast.Name):
                # Check VAR_TYPE_OVERRIDES first
                func_name = self._current_func_info.name if self._current_func_info else ""
                override_key = (func_name, target.id)
                if override_key in VAR_TYPE_OVERRIDES:
                    pass  # Already set above
                else:
                    value_type = self._synthesize_type(value)
                    # Update type if it's concrete (not any) and either:
                    # - Variable not yet tracked, or
                    # - Variable was RUNE from for-loop but now assigned STRING (from method call)
                    current_type = self._type_ctx.var_types.get(target.id)
                    if value_type != Interface("any"):
                        if current_type is None or (current_type == RUNE and value_type == STRING):
                            self._type_ctx.var_types[target.id] = value_type
            # Propagate narrowed status: if assigning from a narrowed var, target is also narrowed
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Name):
                if node.value.id in self._type_ctx.narrowed_vars:
                    self._type_ctx.narrowed_vars.add(target.id)
                    # Also set the narrowed type for the target
                    narrowed_type = self._type_ctx.var_types.get(node.value.id)
                    if narrowed_type:
                        self._type_ctx.var_types[target.id] = narrowed_type
            # Track kind = node.kind assignments for kind-based type narrowing
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Attribute):
                if node.value.attr == "kind" and isinstance(node.value.value, ast.Name):
                    self._type_ctx.kind_source_vars[target.id] = node.value.value.id
            # Propagate list element union types: var = list[idx] where list has known element unions
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Subscript):
                if isinstance(node.value.value, ast.Name):
                    list_var = node.value.value.id
                    if list_var in self._type_ctx.list_element_unions:
                        self._type_ctx.union_types[target.id] = self._type_ctx.list_element_unions[list_var]
                        # Also reset var_types to Node so union_types logic is used for field access
                        self._type_ctx.var_types[target.id] = Interface("Node")
            lval = self._lower_lvalue(target)
            assign = ir.Assign(target=lval, value=value, loc=self._loc_from_node(node))
            # Add declaration type if VAR_TYPE_OVERRIDE applies or if var_types has a unified Node type
            if isinstance(target, ast.Name):
                func_name = self._current_func_info.name if self._current_func_info else ""
                override_key = (func_name, target.id)
                if override_key in VAR_TYPE_OVERRIDES:
                    assign.decl_typ = VAR_TYPE_OVERRIDES[override_key]
                elif target.id in self._type_ctx.var_types:
                    # Use unified Node type from var_types for hoisted variables
                    unified_type = self._type_ctx.var_types[target.id]
                    if unified_type == Interface("Node"):
                        expr_type = self._synthesize_type(value)
                        if unified_type != expr_type:
                            assign.decl_typ = unified_type
            return assign
        # Multiple targets: a = b = val -> emit assignment for each target
        stmts: list[ir.Stmt] = []
        for target in node.targets:
            lval = self._lower_lvalue(target)
            stmts.append(ir.Assign(target=lval, value=value, loc=self._loc_from_node(node)))
            # Track variable type
            if isinstance(target, ast.Name):
                value_type = self._synthesize_type(value)
                if value_type != Interface("any"):
                    self._type_ctx.var_types[target.id] = value_type
        if len(stmts) == 1:
            return stmts[0]
        block = ir.Block(body=stmts, loc=self._loc_from_node(node))
        block.no_scope = True  # Don't emit braces
        return block

    def _lower_stmt_AnnAssign(self, node: ast.AnnAssign) -> "ir.Stmt":
        from .. import ir
        py_type = self._annotation_to_str(node.annotation)
        typ = self._py_type_to_ir(py_type)
        # Handle int | None = None -> use -1 as sentinel
        if (isinstance(typ, Optional) and typ.inner == INT and
            node.value and isinstance(node.value, ast.Constant) and node.value.value is None):
            if isinstance(node.target, ast.Name):
                # Store as plain int with -1 sentinel
                return ir.VarDecl(name=node.target.id, typ=INT,
                                  value=ir.IntLit(value=-1, typ=INT, loc=self._loc_from_node(node)),
                                  loc=self._loc_from_node(node))
        # Determine expected type for lowering (use field type for field assignments)
        expected_type = typ
        if (isinstance(node.target, ast.Attribute) and
            isinstance(node.target.value, ast.Name) and
            node.target.value.id == "self" and
            self._current_class_name):
            field_name = node.target.attr
            struct_info = self.symbols.structs.get(self._current_class_name)
            if struct_info:
                field_info = struct_info.fields.get(field_name)
                if field_info:
                    expected_type = field_info.typ
        if node.value:
            # For list values, pass expected type to get correct element type
            if isinstance(node.value, ast.List):
                value = self._lower_expr_List(node.value, expected_type)
            else:
                value = self._lower_expr(node.value)
            # Coerce value to expected type
            from_type = self._synthesize_type(value)
            value = self._coerce(value, from_type, expected_type)
        else:
            value = None
        if isinstance(node.target, ast.Name):
            # Update type context with declared type (overrides any earlier inference)
            self._type_ctx.var_types[node.target.id] = typ
            return ir.VarDecl(name=node.target.id, typ=typ, value=value, loc=self._loc_from_node(node))
        # Attribute target - treat as assignment
        lval = self._lower_lvalue(node.target)
        if value:
            # Handle sentinel ints for field assignments: self.field = None -> self.field = -1
            if isinstance(value, ir.NilLit) and self._is_sentinel_int(node.target):
                value = ir.IntLit(value=-1, typ=INT, loc=self._loc_from_node(node))
            # For field assignments, coerce to the actual field type (from struct info)
            if (isinstance(node.target, ast.Attribute) and
                isinstance(node.target.value, ast.Name) and
                node.target.value.id == "self" and
                self._current_class_name):
                field_name = node.target.attr
                struct_info = self.symbols.structs.get(self._current_class_name)
                if struct_info:
                    field_info = struct_info.fields.get(field_name)
                    if field_info:
                        from_type = self._synthesize_type(value)
                        value = self._coerce(value, from_type, field_info.typ)
            return ir.Assign(target=lval, value=value, loc=self._loc_from_node(node))
        return ir.ExprStmt(expr=ir.Var(name="_skip_ann", typ=VOID))

    def _lower_stmt_AugAssign(self, node: ast.AugAssign) -> "ir.Stmt":
        return lowering.lower_stmt_AugAssign(node, self._lower_lvalue, self._lower_expr)

    def _lower_stmt_Return(self, node: ast.Return) -> "ir.Stmt":
        return lowering.lower_stmt_Return(
            node, self._lower_expr, self._synthesize_type, self._coerce, self._type_ctx.return_type
        )

    def _is_isinstance_call(self, node: ast.expr) -> tuple[str, str] | None:
        """Check if node is isinstance(var, Type). Returns (var_name, type_name) or None."""
        return lowering.is_isinstance_call(node)

    def _is_kind_check(self, node: ast.expr) -> tuple[str, str] | None:
        """Check if node is x.kind == "typename". Returns (var_name, class_name) or None."""
        return lowering.is_kind_check(node, self._kind_to_class)

    def _extract_isinstance_or_chain(self, node: ast.expr) -> tuple[str, list[str]] | None:
        """Extract isinstance/kind checks from expression. Returns (var_name, [type_names]) or None."""
        return lowering.extract_isinstance_or_chain(node, self._kind_to_class)

    def _extract_isinstance_from_and(self, node: ast.expr) -> tuple[str, str] | None:
        """Extract isinstance(var, Type) from compound AND expression.
        Returns (var_name, type_name) or None if no isinstance found."""
        return lowering.extract_isinstance_from_and(node)

    def _extract_kind_check(self, node: ast.expr) -> tuple[str, str] | None:
        """Extract kind-based type narrowing from `kind == "value"` or `node.kind == "value"`.
        Returns (node_var_name, struct_name) or None if not a kind check."""
        return lowering.extract_kind_check(node, self._kind_to_struct, self._type_ctx.kind_source_vars)

    def _extract_attr_kind_check(self, node: ast.expr) -> tuple[tuple[str, ...], str] | None:
        """Extract kind check for attribute paths like `node.body.kind == "value"`.
        Returns (attr_path_tuple, struct_name) or None."""
        return lowering.extract_attr_kind_check(node, self._kind_to_struct)

    def _get_attr_path(self, node: ast.expr) -> tuple[str, ...] | None:
        """Extract attribute path as tuple (e.g., node.body -> ("node", "body"))."""
        return lowering.get_attr_path(node)

    def _collect_isinstance_chain(self, node: ast.If, var_name: str) -> tuple[list["ir.TypeCase"], list["ir.Stmt"]]:
        """Collect isinstance checks on same variable into TypeSwitch cases."""
        from .. import ir
        cases: list[ir.TypeCase] = []
        current = node
        while True:
            # Check for single isinstance or isinstance-or-chain
            check = self._extract_isinstance_or_chain(current.test)
            if not check or check[0] != var_name:
                break
            _, type_names = check
            # Lower body once, generate case for each type
            # For or chains, duplicate the body for each type
            for type_name in type_names:
                typ = self._resolve_type_name(type_name)
                # Temporarily narrow the variable type for this branch
                # Note: Don't add to narrowed_vars here - TypeSwitch already handles
                # type narrowing in Go via the switch binding
                old_type = self._type_ctx.var_types.get(var_name)
                self._type_ctx.var_types[var_name] = typ
                body = [self._lower_stmt(s) for s in current.body]
                # Restore original type
                if old_type is not None:
                    self._type_ctx.var_types[var_name] = old_type
                else:
                    self._type_ctx.var_types.pop(var_name, None)
                cases.append(ir.TypeCase(typ=typ, body=body, loc=self._loc_from_node(current)))
            # Check for elif isinstance chain
            if len(current.orelse) == 1 and isinstance(current.orelse[0], ast.If):
                current = current.orelse[0]
            elif current.orelse:
                # Has else block - becomes default
                default = [self._lower_stmt(s) for s in current.orelse]
                return cases, default
            else:
                return cases, []
        # Reached non-isinstance condition - treat rest as default
        if current != node:
            default = [self._lower_stmt(ast.If(test=current.test, body=current.body, orelse=current.orelse))]
            return cases, default
        return [], []

    def _resolve_type_name(self, name: str) -> Type:
        """Resolve a class name to an IR type (for isinstance checks)."""
        return lowering.resolve_type_name(name, TYPE_MAP, self.symbols)

    def _lower_stmt_If(self, node: ast.If) -> "ir.Stmt":
        from .. import ir
        # Check for isinstance chain pattern (including 'or' patterns)
        isinstance_check = self._extract_isinstance_or_chain(node.test)
        if isinstance_check:
            var_name, _ = isinstance_check
            # Try to collect full isinstance chain on same variable
            cases, default = self._collect_isinstance_chain(node, var_name)
            if cases:
                var_expr = self._lower_expr(ast.Name(id=var_name, ctx=ast.Load()))
                return TypeSwitch(
                    expr=var_expr,
                    binding=var_name,
                    cases=cases,
                    default=default,
                    loc=self._loc_from_node(node)
                )
        # Fall back to regular If emission
        cond = self._lower_expr_as_bool(node.test)
        # Check for isinstance in compound AND condition for type narrowing
        isinstance_in_and = self._extract_isinstance_from_and(node.test)
        # Check for kind-based type narrowing (kind == "value")
        kind_check = self._extract_kind_check(node.test)
        narrowed_var = None
        old_type = None
        was_already_narrowed = False
        if isinstance_in_and:
            var_name, type_name = isinstance_in_and
            typ = self._resolve_type_name(type_name)
            narrowed_var = var_name
            old_type = self._type_ctx.var_types.get(var_name)
            was_already_narrowed = var_name in self._type_ctx.narrowed_vars
            self._type_ctx.var_types[var_name] = typ
            self._type_ctx.narrowed_vars.add(var_name)
        elif kind_check:
            var_name, struct_name = kind_check
            typ = Pointer(StructRef(struct_name))
            narrowed_var = var_name
            old_type = self._type_ctx.var_types.get(var_name)
            was_already_narrowed = var_name in self._type_ctx.narrowed_vars
            self._type_ctx.var_types[var_name] = typ
            self._type_ctx.narrowed_vars.add(var_name)
        then_body = self._lower_stmts(node.body)
        # Restore narrowed type after processing body
        if narrowed_var is not None:
            if old_type is not None:
                self._type_ctx.var_types[narrowed_var] = old_type
            else:
                self._type_ctx.var_types.pop(narrowed_var, None)
            if not was_already_narrowed:
                self._type_ctx.narrowed_vars.discard(narrowed_var)
        else_body = self._lower_stmts(node.orelse) if node.orelse else []
        return ir.If(cond=cond, then_body=then_body, else_body=else_body, loc=self._loc_from_node(node))

    def _lower_stmt_While(self, node: ast.While) -> "ir.Stmt":
        return lowering.lower_stmt_While(node, self._lower_expr_as_bool, self._lower_stmts)

    def _lower_stmt_For(self, node: ast.For) -> "ir.Stmt":
        from .. import ir
        from ..ir import RUNE
        iterable = self._lower_expr(node.iter)
        # Determine loop variable types based on iterable type
        iterable_type = self._infer_expr_type_from_ast(node.iter)
        # Dereference Pointer(Slice) or Optional(Slice) for range
        inner_slice = self._get_inner_slice(iterable_type)
        if inner_slice is not None:
            iterable = ir.UnaryOp(op="*", operand=iterable, typ=inner_slice, loc=iterable.loc)
            iterable_type = inner_slice
        # Determine index and value names
        index = None
        value = None
        # Get element type for loop variable
        elem_type: Type | None = None
        if iterable_type == STRING:
            elem_type = RUNE
        elif isinstance(iterable_type, Slice):
            elem_type = iterable_type.element
        if isinstance(node.target, ast.Name):
            if node.target.id == "_":
                pass  # Discard
            else:
                value = node.target.id
                if elem_type:
                    self._type_ctx.var_types[value] = elem_type
        elif isinstance(node.target, ast.Tuple) and len(node.target.elts) == 2:
            # Check if iterating over Slice(Tuple) - need tuple unpacking, not (index, value)
            if isinstance(elem_type, Tuple) and len(elem_type.elements) >= 2:
                # Generate: for _, _item := range iterable; a := _item.F0; b := _item.F1
                item_var = "_item"
                # Set types for unpacked variables
                unpack_vars: list[tuple[int, str]] = []
                for i, elt in enumerate(node.target.elts):
                    if isinstance(elt, ast.Name) and elt.id != "_":
                        unpack_vars.append((i, elt.id))
                        if i < len(elem_type.elements):
                            self._type_ctx.var_types[elt.id] = elem_type.elements[i]
                # Lower body after setting up types
                body = self._lower_stmts(node.body)
                # Prepend unpacking assignments
                unpack_stmts: list[ir.Stmt] = []
                for i, var_name in unpack_vars:
                    field_type = elem_type.elements[i] if i < len(elem_type.elements) else Interface("any")
                    field_access = ir.FieldAccess(
                        obj=ir.Var(name=item_var, typ=elem_type, loc=self._loc_from_node(node)),
                        field=f"F{i}",
                        typ=field_type,
                        loc=self._loc_from_node(node),
                    )
                    unpack_stmts.append(ir.Assign(
                        target=ir.VarLV(name=var_name),
                        value=field_access,
                        loc=self._loc_from_node(node),
                    ))
                return ir.ForRange(
                    index=None,
                    value=item_var,
                    iterable=iterable,
                    body=unpack_stmts + body,
                    loc=self._loc_from_node(node),
                )
            # Otherwise treat as (index, value) iteration
            if isinstance(node.target.elts[0], ast.Name):
                index = node.target.elts[0].id if node.target.elts[0].id != "_" else None
            if isinstance(node.target.elts[1], ast.Name):
                value = node.target.elts[1].id if node.target.elts[1].id != "_" else None
                if elem_type and value:
                    self._type_ctx.var_types[value] = elem_type
        # Lower body after setting up loop variable types
        body = self._lower_stmts(node.body)
        return ir.ForRange(index=index, value=value, iterable=iterable, body=body, loc=self._loc_from_node(node))

    def _lower_stmt_Break(self, node: ast.Break) -> "ir.Stmt":
        return lowering.lower_stmt_Break(node)

    def _lower_stmt_Continue(self, node: ast.Continue) -> "ir.Stmt":
        return lowering.lower_stmt_Continue(node)

    def _lower_stmt_Pass(self, node: ast.Pass) -> "ir.Stmt":
        return lowering.lower_stmt_Pass(node)

    def _lower_stmt_Raise(self, node: ast.Raise) -> "ir.Stmt":
        return lowering.lower_stmt_Raise(node, self._lower_expr, self._current_catch_var)

    def _lower_stmt_Try(self, node: ast.Try) -> "ir.Stmt":
        from .. import ir
        body = self._lower_stmts(node.body)
        catch_var = None
        catch_body: list[ir.Stmt] = []
        reraise = False
        if node.handlers:
            handler = node.handlers[0]
            catch_var = handler.name
            # Set catch var context so raise e can be detected
            saved_catch_var = self._current_catch_var
            self._current_catch_var = catch_var
            catch_body = self._lower_stmts(handler.body)
            self._current_catch_var = saved_catch_var
            # Check if handler re-raises (bare raise)
            for stmt in handler.body:
                if isinstance(stmt, ast.Raise) and stmt.exc is None:
                    reraise = True
        return ir.TryCatch(body=body, catch_var=catch_var, catch_body=catch_body, reraise=reraise, loc=self._loc_from_node(node))

    def _lower_stmt_FunctionDef(self, node: ast.FunctionDef) -> "ir.Stmt":
        return lowering.lower_stmt_FunctionDef(node)

    def _lower_lvalue(self, node: ast.expr) -> "ir.LValue":
        """Lower an expression to an LValue."""
        return lowering.lower_lvalue(node, self._lower_expr)
