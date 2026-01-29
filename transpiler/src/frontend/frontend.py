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
from .context import FrontendContext, LoweringDispatch, TypeContext
from . import type_inference
from . import lowering
from . import collection
from . import builders

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
        callbacks = collection.CollectionCallbacks(
            annotation_to_str=self._annotation_to_str,
            py_type_to_ir=self._py_type_to_ir,
            py_return_type_to_ir=self._py_return_type_to_ir,
            lower_expr=self._lower_expr,
            infer_type_from_value=self._infer_type_from_value,
        )
        collection.collect_fields(tree, self.symbols, callbacks)

    def _collect_class_fields(self, node: ast.ClassDef) -> None:
        """Collect fields from class body and __init__."""
        callbacks = collection.CollectionCallbacks(
            annotation_to_str=self._annotation_to_str,
            py_type_to_ir=self._py_type_to_ir,
            py_return_type_to_ir=self._py_return_type_to_ir,
            lower_expr=self._lower_expr,
            infer_type_from_value=self._infer_type_from_value,
        )
        collection.collect_class_fields(node, self.symbols, callbacks)

    def _collect_init_fields(self, init: ast.FunctionDef, info: StructInfo) -> None:
        """Collect fields assigned in __init__."""
        callbacks = collection.CollectionCallbacks(
            annotation_to_str=self._annotation_to_str,
            py_type_to_ir=self._py_type_to_ir,
            py_return_type_to_ir=self._py_return_type_to_ir,
            lower_expr=self._lower_expr,
            infer_type_from_value=self._infer_type_from_value,
        )
        collection.collect_init_fields(init, info, callbacks)

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
        callbacks = builders.BuilderCallbacks(
            annotation_to_str=self._annotation_to_str,
            py_type_to_ir=self._py_type_to_ir,
            py_return_type_to_ir=self._py_return_type_to_ir,
            lower_expr=self._lower_expr,
            lower_stmts=self._lower_stmts,
            collect_var_types=self._collect_var_types,
            is_exception_subclass=self._is_exception_subclass,
            extract_union_struct_names=self._extract_union_struct_names,
            loc_from_node=self._loc_from_node,
            setup_context=self._setup_context,
            setup_and_lower_stmts=self._setup_and_lower_stmts,
        )
        return builders.build_module(tree, self.symbols, callbacks)

    def _build_struct(self, node: ast.ClassDef, with_body: bool = False) -> tuple[Struct | None, Function | None]:
        """Build IR Struct from class definition. Returns (struct, constructor_func)."""
        callbacks = builders.BuilderCallbacks(
            annotation_to_str=self._annotation_to_str,
            py_type_to_ir=self._py_type_to_ir,
            py_return_type_to_ir=self._py_return_type_to_ir,
            lower_expr=self._lower_expr,
            lower_stmts=self._lower_stmts,
            collect_var_types=self._collect_var_types,
            is_exception_subclass=self._is_exception_subclass,
            extract_union_struct_names=self._extract_union_struct_names,
            loc_from_node=self._loc_from_node,
            setup_context=self._setup_context,
            setup_and_lower_stmts=self._setup_and_lower_stmts,
        )
        return builders.build_struct(node, self.symbols, callbacks, with_body)

    def _build_forwarding_constructor(self, class_name: str, parent_class: str) -> Function:
        """Build a forwarding constructor for exception subclasses with no __init__."""
        return builders.build_forwarding_constructor(class_name, parent_class, self.symbols)

    def _build_constructor(self, class_name: str, init_ast: ast.FunctionDef, info: StructInfo) -> Function:
        """Build a NewXxx constructor function from __init__ AST."""
        callbacks = builders.BuilderCallbacks(
            annotation_to_str=self._annotation_to_str,
            py_type_to_ir=self._py_type_to_ir,
            py_return_type_to_ir=self._py_return_type_to_ir,
            lower_expr=self._lower_expr,
            lower_stmts=self._lower_stmts,
            collect_var_types=self._collect_var_types,
            is_exception_subclass=self._is_exception_subclass,
            extract_union_struct_names=self._extract_union_struct_names,
            loc_from_node=self._loc_from_node,
            setup_context=self._setup_context,
            setup_and_lower_stmts=self._setup_and_lower_stmts,
        )
        return builders.build_constructor(class_name, init_ast, info, callbacks)

    def _setup_context(self, class_name: str, func_info: FuncInfo | None) -> None:
        """Set up class context for var type collection."""
        self._current_class_name = class_name
        self._current_func_info = func_info

    def _setup_and_lower_stmts(
        self,
        class_name: str,
        func_info: FuncInfo | None,
        type_ctx: TypeContext,
        stmts: list[ast.stmt],
    ) -> list:
        """Set up type context and lower statements."""
        self._current_class_name = class_name
        self._current_func_info = func_info
        self._type_ctx = type_ctx
        return self._lower_stmts(stmts)

    def _build_function_shell(self, node: ast.FunctionDef, with_body: bool = False) -> Function:
        """Build IR Function from AST. Set with_body=True to lower statements."""
        callbacks = builders.BuilderCallbacks(
            annotation_to_str=self._annotation_to_str,
            py_type_to_ir=self._py_type_to_ir,
            py_return_type_to_ir=self._py_return_type_to_ir,
            lower_expr=self._lower_expr,
            lower_stmts=self._lower_stmts,
            collect_var_types=self._collect_var_types,
            is_exception_subclass=self._is_exception_subclass,
            extract_union_struct_names=self._extract_union_struct_names,
            loc_from_node=self._loc_from_node,
            setup_context=self._setup_context,
            setup_and_lower_stmts=self._setup_and_lower_stmts,
        )
        return builders.build_function_shell(node, self.symbols, callbacks, with_body)

    def _build_method_shell(self, node: ast.FunctionDef, class_name: str, with_body: bool = False) -> Function:
        """Build IR Function for a method. Set with_body=True to lower statements."""
        callbacks = builders.BuilderCallbacks(
            annotation_to_str=self._annotation_to_str,
            py_type_to_ir=self._py_type_to_ir,
            py_return_type_to_ir=self._py_return_type_to_ir,
            lower_expr=self._lower_expr,
            lower_stmts=self._lower_stmts,
            collect_var_types=self._collect_var_types,
            is_exception_subclass=self._is_exception_subclass,
            extract_union_struct_names=self._extract_union_struct_names,
            loc_from_node=self._loc_from_node,
            setup_context=self._setup_context,
            setup_and_lower_stmts=self._setup_and_lower_stmts,
        )
        return builders.build_method_shell(node, class_name, self.symbols, callbacks, with_body)

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

    def _collect_var_types(self, stmts: list[ast.stmt]) -> tuple[dict[str, Type], dict[str, list[str]], set[str], dict[str, list[str]]]:
        """Pre-scan function body to collect variable types, tuple var mappings, and sentinel ints."""
        callbacks = collection.CollectionCallbacks(
            annotation_to_str=self._annotation_to_str,
            py_type_to_ir=self._py_type_to_ir,
            py_return_type_to_ir=self._py_return_type_to_ir,
            lower_expr=self._lower_expr,
            infer_type_from_value=self._infer_type_from_value,
            extract_struct_name=self._extract_struct_name,
            infer_container_type_from_ast=self._infer_container_type_from_ast,
            is_len_call=self._is_len_call,
            is_kind_check=self._is_kind_check,
            infer_call_return_type=self._infer_call_return_type,
            infer_iterable_type=self._infer_iterable_type,
            infer_element_type_from_append_arg=self._infer_element_type_from_append_arg,
        )
        return collection.collect_var_types(
            stmts, self.symbols, self._current_class_name,
            self._current_func_info, self._node_types, callbacks
        )

    def _infer_iterable_type(self, node: ast.expr, var_types: dict[str, Type]) -> Type:
        """Infer the type of an iterable expression."""
        return type_inference.infer_iterable_type(node, var_types, self._current_class_name, self.symbols)

    def _infer_element_type_from_append_arg(self, arg: ast.expr, var_types: dict[str, Type]) -> Type:
        """Infer slice element type from what's being appended."""
        callbacks = collection.CollectionCallbacks(
            annotation_to_str=self._annotation_to_str,
            py_type_to_ir=self._py_type_to_ir,
            py_return_type_to_ir=self._py_return_type_to_ir,
            lower_expr=self._lower_expr,
            infer_type_from_value=self._infer_type_from_value,
            extract_struct_name=self._extract_struct_name,
            infer_container_type_from_ast=self._infer_container_type_from_ast,
        )
        return collection.infer_element_type_from_append_arg(
            arg, var_types, self.symbols, self._current_class_name,
            self._current_func_info, callbacks
        )

    def _infer_container_type_from_ast(self, node: ast.expr, var_types: dict[str, Type]) -> Type:
        """Infer the type of a container expression from AST."""
        return type_inference.infer_container_type_from_ast(
            node, self.symbols, self._current_class_name, self._current_func_info, var_types
        )

    def _unify_branch_types(self, then_vars: dict[str, Type], else_vars: dict[str, Type]) -> dict[str, Type]:
        """Unify variable types from if/else branches."""
        return collection.unify_branch_types(then_vars, else_vars)

    def _collect_branch_var_types(self, stmts: list[ast.stmt], var_types: dict[str, Type]) -> dict[str, Type]:
        """Collect variable types assigned in a list of statements (for branch analysis)."""
        return collection.collect_branch_var_types(stmts, var_types)

    def _infer_branch_expr_type(self, node: ast.expr, var_types: dict[str, Type], branch_vars: dict[str, Type]) -> Type:
        """Infer type of expression during branch analysis."""
        return collection.infer_branch_expr_type(node, var_types, branch_vars)

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
        """Lower a Python function/method call to IR."""
        ctx = FrontendContext(
            symbols=self.symbols,
            type_ctx=self._type_ctx,
            current_func_info=self._current_func_info,
            current_class_name=self._current_class_name,
            node_types=self._node_types,
            kind_to_struct=self._kind_to_struct,
            kind_to_class=self._kind_to_class,
            current_catch_var=self._current_catch_var,
        )
        dispatch = LoweringDispatch(
            lower_expr=self._lower_expr,
            lower_expr_as_bool=self._lower_expr_as_bool,
            lower_stmts=self._lower_stmts,
            lower_lvalue=self._lower_lvalue,
            lower_expr_List=self._lower_expr_List,
            infer_expr_type_from_ast=self._infer_expr_type_from_ast,
            infer_call_return_type=self._infer_call_return_type,
            synthesize_type=self._synthesize_type,
            coerce=self._coerce,
            annotation_to_str=self._annotation_to_str,
            py_type_to_ir=self._py_type_to_ir,
            make_default_value=self._make_default_value,
            extract_struct_name=self._extract_struct_name,
            is_exception_subclass=self._is_exception_subclass,
            is_node_subclass=self._is_node_subclass,
            is_sentinel_int=self._is_sentinel_int,
            get_sentinel_value=self._get_sentinel_value,
            resolve_type_name=self._resolve_type_name,
            get_inner_slice=self._get_inner_slice,
            merge_keyword_args=self._merge_keyword_args,
            fill_default_args=self._fill_default_args,
            merge_keyword_args_for_func=self._merge_keyword_args_for_func,
            fill_default_args_for_func=self._fill_default_args_for_func,
            add_address_of_for_ptr_params=self._add_address_of_for_ptr_params,
            deref_for_slice_params=self._deref_for_slice_params,
            deref_for_func_slice_params=self._deref_for_func_slice_params,
            coerce_sentinel_to_ptr=self._coerce_sentinel_to_ptr,
            coerce_args_to_node=self._coerce_args_to_node,
            is_node_interface_type=self._is_node_interface_type,
            synthesize_method_return_type=self._synthesize_method_return_type,
        )
        return lowering.lower_expr_Call(node, ctx, dispatch)

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
