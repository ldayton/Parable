"""Frontend: Python AST -> IR.

Converts parable.py Python subset to language-agnostic IR.
All analysis happens here; backends just emit syntax.
"""

from __future__ import annotations

import ast

from ..ir import (
    BOOL,
    BYTE,
    FLOAT,
    INT,
    RUNE,
    STRING,
    VOID,
    FuncInfo,
    Function,
    Loc,
    Module,
    Slice,
    StructInfo,
    Struct,
    SymbolTable,
    Type,
)
from .context import FrontendContext, LoweringDispatch, TypeContext
from . import type_inference
from . import lowering
from . import collection
from . import builders

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
        collection.collect_class_names(tree, self.symbols)
        # Pass 2: Mark Node subclasses
        collection.mark_node_subclasses(self.symbols, self._node_types)
        # Pass 2b: Mark Exception subclasses
        collection.mark_exception_subclasses(self.symbols)
        # Pass 3: Collect function and method signatures
        self._collect_signatures(tree)
        # Pass 4: Collect struct fields
        self._collect_fields(tree)
        # Pass 4b: Build kind -> struct mapping from const_fields
        collection.build_kind_mapping(self.symbols, self._kind_to_struct, self._kind_to_class)
        # Pass 5: Collect module-level constants
        collection.collect_constants(tree, self.symbols)
        # Build IR Module
        return self._build_module(tree)

    def _is_node_subclass(self, name: str) -> bool:
        """Check if a class is a Node subclass (directly or transitively)."""
        return type_inference.is_node_subclass(name, self.symbols)

    def _is_exception_subclass(self, name: str) -> bool:
        """Check if a class is an Exception subclass (directly or transitively)."""
        return collection.is_exception_subclass(name, self.symbols)

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
            extract_union_struct_names=lambda py_type: type_inference.extract_union_struct_names(py_type, self._node_types),
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
            extract_union_struct_names=lambda py_type: type_inference.extract_union_struct_names(py_type, self._node_types),
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
            extract_union_struct_names=lambda py_type: type_inference.extract_union_struct_names(py_type, self._node_types),
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
            extract_union_struct_names=lambda py_type: type_inference.extract_union_struct_names(py_type, self._node_types),
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
            extract_union_struct_names=lambda py_type: type_inference.extract_union_struct_names(py_type, self._node_types),
            loc_from_node=self._loc_from_node,
            setup_context=self._setup_context,
            setup_and_lower_stmts=self._setup_and_lower_stmts,
        )
        return builders.build_method_shell(node, class_name, self.symbols, callbacks, with_body)

    def _loc_from_node(self, node: ast.AST) -> Loc:
        """Create Loc from AST node."""
        return lowering.loc_from_node(node)

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

    def _infer_type_from_value(
        self, node: ast.expr, param_types: dict[str, str]
    ) -> Type:
        """Infer IR type from an expression."""
        return type_inference.infer_type_from_value(node, param_types, self.symbols, self._node_types)

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

    def _is_len_call(self, node: ast.expr) -> bool:
        """Check if node is a len() call."""
        return lowering.is_len_call(node)

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

    # ============================================================
    # EXPRESSION LOWERING (Phase 3)
    # ============================================================

    def _make_ctx_and_dispatch(self) -> tuple[FrontendContext, LoweringDispatch]:
        """Build FrontendContext and LoweringDispatch for lowering functions."""
        exception_subclasses = {
            name for name, info in self.symbols.structs.items() if info.is_exception
        }
        ctx = FrontendContext(
            symbols=self.symbols,
            type_ctx=self._type_ctx,
            current_func_info=self._current_func_info,
            current_class_name=self._current_class_name,
            node_types=self._node_types,
            kind_to_struct=self._kind_to_struct,
            kind_to_class=self._kind_to_class,
            current_catch_var=self._current_catch_var,
            exception_subclasses=exception_subclasses,
        )
        dispatch = LoweringDispatch(
            lower_expr=self._lower_expr,
            lower_expr_as_bool=self._lower_expr_as_bool,
            lower_stmts=self._lower_stmts,
            lower_lvalue=self._lower_lvalue,
            lower_expr_List=self._lower_expr_List,
            infer_expr_type_from_ast=self._infer_expr_type_from_ast,
            annotation_to_str=self._annotation_to_str,
            merge_keyword_args=self._merge_keyword_args,
            fill_default_args=self._fill_default_args,
            merge_keyword_args_for_func=self._merge_keyword_args_for_func,
            add_address_of_for_ptr_params=self._add_address_of_for_ptr_params,
            deref_for_slice_params=self._deref_for_slice_params,
            deref_for_func_slice_params=self._deref_for_func_slice_params,
            coerce_sentinel_to_ptr=self._coerce_sentinel_to_ptr,
            set_catch_var=self._set_catch_var,
        )
        return ctx, dispatch

    def _lower_expr_as_bool(self, node: ast.expr) -> "ir.Expr":
        """Lower expression used in boolean context, adding truthy checks as needed."""
        return lowering.lower_expr_as_bool(
            node, self._lower_expr, self._lower_expr_as_bool, self._infer_expr_type_from_ast,
            self._is_isinstance_call, self._resolve_type_name, self._type_ctx, self.symbols
        )

    def _lower_expr(self, node: ast.expr) -> "ir.Expr":
        """Lower a Python expression to IR."""
        ctx, dispatch = self._make_ctx_and_dispatch()
        return lowering.lower_expr(node, ctx, dispatch)

    def _infer_expr_type_from_ast(self, node: ast.expr) -> Type:
        """Infer the type of a Python AST expression without lowering it."""
        return type_inference.infer_expr_type_from_ast(
            node, self._type_ctx, self.symbols, self._current_func_info, self._current_class_name, self._node_types
        )

    def _lower_expr_List(self, node: ast.List, expected_type: Type | None = None) -> "ir.Expr":
        return lowering.lower_expr_List(
            node, self._lower_expr, self._infer_expr_type_from_ast, self._type_ctx.expected, expected_type
        )

    # ============================================================
    # STATEMENT LOWERING (Phase 3)
    # ============================================================

    def _lower_stmt(self, node: ast.stmt) -> "ir.Stmt":
        """Lower a Python statement to IR."""
        ctx, dispatch = self._make_ctx_and_dispatch()
        return lowering.lower_stmt(node, ctx, dispatch)

    def _lower_stmts(self, stmts: list[ast.stmt]) -> list["ir.Stmt"]:
        """Lower a list of statements."""
        return [self._lower_stmt(s) for s in stmts]

    def _is_isinstance_call(self, node: ast.expr) -> tuple[str, str] | None:
        """Check if node is isinstance(var, Type). Returns (var_name, type_name) or None."""
        return lowering.is_isinstance_call(node)

    def _is_kind_check(self, node: ast.expr) -> tuple[str, str] | None:
        """Check if node is x.kind == "typename". Returns (var_name, class_name) or None."""
        return lowering.is_kind_check(node, self._kind_to_class)

    def _resolve_type_name(self, name: str) -> Type:
        """Resolve a class name to an IR type (for isinstance checks)."""
        return lowering.resolve_type_name(name, TYPE_MAP, self.symbols)

    def _set_catch_var(self, var: str | None) -> str | None:
        """Set the current catch variable and return the previous value."""
        saved = self._current_catch_var
        self._current_catch_var = var
        return saved

    def _lower_lvalue(self, node: ast.expr) -> "ir.LValue":
        """Lower an expression to an LValue."""
        return lowering.lower_lvalue(node, self._lower_expr)
