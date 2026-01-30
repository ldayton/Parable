"""Frontend: Python AST -> IR.

Converts parable.py Python subset to language-agnostic IR.
All analysis happens here; backends just emit syntax.
"""

from __future__ import annotations

from .ast_compat import ASTNode
from .parse import parse

from ..ir import (
    BOOL,
    BYTE,
    Expr,
    FLOAT,
    INT,
    STRING,
    FuncInfo,
    Module,
    Slice,
    Stmt,
    StructInfo,
    SymbolTable,
    Type,
)
from .context import FrontendContext, LoweringDispatch, TypeContext
from . import type_inference
from . import lowering
from . import collection
from . import signatures
from . import builders
from .names import NameResult

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
        self.symbols: SymbolTable = SymbolTable()
        self._node_types: set[str] = set()  # classes that inherit from Node
        # Type inference context
        self._current_func_info: FuncInfo | None = None
        self._current_class_name: str = ""
        self._type_ctx: TypeContext = TypeContext()
        self._current_catch_var: str | None = None  # track catch variable for raise e pattern
        # Auto-generated kind -> struct mappings (built from class const_fields)
        self._kind_to_struct: dict[str, str] = {}
        self._kind_to_class: dict[str, str] = {}

    def _populate_structs_from_names(self, name_result: NameResult) -> None:
        """Populate structs from NameTable (Phase 4 integration)."""
        for name, info in name_result.table.module_names.items():
            if info.kind == "class":
                self.symbols.structs[name] = StructInfo(name=name, bases=info.bases)

    def transpile(
        self, source: str, tree: ASTNode | None = None, name_result: NameResult | None = None
    ) -> Module:
        """Parse Python source and produce IR Module."""
        from .names import resolve_names

        if tree is None:
            tree = parse(source)
        # Pass 1: Collect class names and inheritance (from Phase 4 name_result)
        if name_result is None:
            name_result = resolve_names(tree)
        self._populate_structs_from_names(name_result)
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

    def _is_exception_subclass(self, name: str) -> bool:
        """Check if a class is an Exception subclass (directly or transitively)."""
        return collection.is_exception_subclass(name, self.symbols)

    def _make_collection_callbacks_basic(self) -> collection.CollectionCallbacks:
        """Create basic CollectionCallbacks with core type/expr callbacks."""
        return collection.CollectionCallbacks(
            annotation_to_str=self._annotation_to_str,
            py_type_to_ir=self._py_type_to_ir,
            py_return_type_to_ir=self._py_return_type_to_ir,
            lower_expr=self._lower_expr,
        )

    def _make_collection_callbacks_with_inference(self) -> collection.CollectionCallbacks:
        """Create CollectionCallbacks with type inference support."""
        cb = self._make_collection_callbacks_basic()
        cb.infer_type_from_value = self._infer_type_from_value
        return cb

    def _collect_signatures(self, tree: ASTNode) -> None:
        """Pass 3: Collect function and method signatures."""
        signatures.collect_signatures(tree, self.symbols, self._make_collection_callbacks_basic())

    def _collect_fields(self, tree: ASTNode) -> None:
        """Pass 4: Collect struct fields from class definitions."""
        collection.collect_fields(
            tree, self.symbols, self._make_collection_callbacks_with_inference()
        )

    def _build_module(self, tree: ASTNode) -> Module:
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
            loc_from_node=lowering.loc_from_node,
            setup_context=self._setup_context,
            setup_and_lower_stmts=self._setup_and_lower_stmts,
        )
        return builders.build_module(tree, self.symbols, callbacks)

    def _setup_context(self, class_name: str, func_info: FuncInfo | None) -> None:
        """Set up class context for var type collection."""
        self._current_class_name = class_name
        self._current_func_info = func_info

    def _extract_union_struct_names(self, py_type: str) -> list[str]:
        """Extract struct names from union type annotation."""
        return type_inference.extract_union_struct_names(py_type, self._node_types)

    def _setup_and_lower_stmts(
        self,
        class_name: str,
        func_info: FuncInfo | None,
        type_ctx: TypeContext,
        stmts: list[ASTNode],
    ) -> list[Stmt]:
        """Set up type context and lower statements."""
        self._current_class_name = class_name
        self._current_func_info = func_info
        self._type_ctx = type_ctx
        return self._lower_stmts(stmts)

    def _annotation_to_str(self, node: ASTNode | None) -> str:
        """Convert type annotation AST to string."""
        if node is None:
            return ""
        if not isinstance(node, dict):
            return ""
        node_t = node.get("_type")
        if node_t == "Name":
            return node.get("id", "")
        if node_t == "Constant":
            v = node.get("value")
            if v is None:
                return "None"
            return str(v)
        if node_t == "List":
            # For annotations like Callable[[], T], the first arg is an ast.List
            elts = node.get("elts", [])
            args = ", ".join(self._annotation_to_str(e) for e in elts)
            return f"[{args}]"
        if node_t == "Subscript":
            base = self._annotation_to_str(node.get("value"))
            slc = node.get("slice", {})
            if slc.get("_type") == "Tuple":
                elts = slc.get("elts", [])
                args = ", ".join(self._annotation_to_str(e) for e in elts)
                return f"{base}[{args}]"
            return f"{base}[{self._annotation_to_str(slc)}]"
        if node_t == "BinOp":
            op = node.get("op", {})
            if op.get("_type") == "BitOr":
                left = self._annotation_to_str(node.get("left"))
                right = self._annotation_to_str(node.get("right"))
                return f"{left} | {right}"
        if node_t == "Attribute":
            return node.get("attr", "")
        return ""

    def _py_type_to_ir(self, py_type: str, concrete_nodes: bool = False) -> Type:
        """Convert Python type string to IR Type."""
        return type_inference.py_type_to_ir(py_type, self.symbols, self._node_types, concrete_nodes)

    def _py_return_type_to_ir(self, py_type: str) -> Type:
        """Convert Python return type to IR, handling tuples as multiple returns."""
        return type_inference.py_return_type_to_ir(py_type, self.symbols, self._node_types)

    def _infer_type_from_value(self, node: ASTNode, param_types: dict[str, str]) -> Type:
        """Infer IR type from an expression."""
        return type_inference.infer_type_from_value(
            node, param_types, self.symbols, self._node_types
        )

    def _collect_var_types(
        self, stmts: list[ASTNode]
    ) -> tuple[dict[str, Type], dict[str, list[str]], set[str], dict[str, list[str]]]:
        """Pre-scan function body to collect variable types, tuple var mappings, and sentinel ints."""
        cb = self._make_collection_callbacks_with_inference()
        cb.extract_struct_name = type_inference.extract_struct_name
        cb.infer_container_type_from_ast = self._infer_container_type_from_ast
        cb.is_len_call = lowering.is_len_call
        cb.is_kind_check = self._is_kind_check
        cb.infer_call_return_type = self._infer_call_return_type
        cb.infer_iterable_type = self._infer_iterable_type
        cb.infer_element_type_from_append_arg = self._infer_element_type_from_append_arg
        return collection.collect_var_types(
            stmts,
            self.symbols,
            self._current_class_name,
            self._current_func_info,
            self._node_types,
            cb,
        )

    def _infer_iterable_type(self, node: ASTNode, var_types: dict[str, Type]) -> Type:
        """Infer the type of an iterable expression."""
        return type_inference.infer_iterable_type(
            node, var_types, self._current_class_name, self.symbols
        )

    def _infer_element_type_from_append_arg(
        self, arg: ASTNode, var_types: dict[str, Type]
    ) -> Type:
        """Infer slice element type from what's being appended."""
        cb = self._make_collection_callbacks_with_inference()
        cb.extract_struct_name = type_inference.extract_struct_name
        cb.infer_container_type_from_ast = self._infer_container_type_from_ast
        return collection.infer_element_type_from_append_arg(
            arg, var_types, self.symbols, self._current_class_name, self._current_func_info, cb
        )

    def _infer_container_type_from_ast(self, node: ASTNode, var_types: dict[str, Type]) -> Type:
        """Infer the type of a container expression from AST."""
        return type_inference.infer_container_type_from_ast(
            node, self.symbols, self._current_class_name, self._current_func_info, var_types
        )

    def _merge_keyword_args(self, obj_type: Type, method: str, args: list[Expr], node: ASTNode) -> list[Expr]:
        return lowering.merge_keyword_args(
            obj_type,
            method,
            args,
            node,
            self.symbols,
            self._lower_expr,
            type_inference.extract_struct_name,
        )

    def _fill_default_args(self, obj_type: Type, method: str, args: list[Expr]) -> list[Expr]:
        return lowering.fill_default_args(
            obj_type, method, args, self.symbols, type_inference.extract_struct_name
        )

    def _merge_keyword_args_for_func(self, func_info: FuncInfo, args: list[Expr], node: ASTNode) -> list[Expr]:
        return lowering.merge_keyword_args_for_func(func_info, args, node, self._lower_expr)

    def _add_address_of_for_ptr_params(
        self, obj_type: Type, method: str, args: list[Expr], orig_args: list[ASTNode]
    ) -> list[Expr]:
        return lowering.add_address_of_for_ptr_params(
            obj_type,
            method,
            args,
            orig_args,
            self.symbols,
            type_inference.extract_struct_name,
            self._infer_expr_type_from_ast,
        )

    def _deref_for_slice_params(
        self, obj_type: Type, method: str, args: list[Expr], orig_args: list[ASTNode]
    ) -> list[Expr]:
        return lowering.deref_for_slice_params(
            obj_type,
            method,
            args,
            orig_args,
            self.symbols,
            type_inference.extract_struct_name,
            self._infer_expr_type_from_ast,
        )

    def _deref_for_func_slice_params(
        self, func_name: str, args: list[Expr], orig_args: list[ASTNode]
    ) -> list[Expr]:
        return lowering.deref_for_func_slice_params(
            func_name, args, orig_args, self.symbols, self._infer_expr_type_from_ast
        )

    def _coerce_sentinel_to_ptr(
        self, obj_type: Type, method: str, args: list[Expr], orig_args: list[Expr]
    ) -> list[Expr]:
        return lowering.coerce_sentinel_to_ptr(
            obj_type,
            method,
            args,
            orig_args,
            self.symbols,
            self._type_ctx.sentinel_ints,
            type_inference.extract_struct_name,
        )

    def _infer_call_return_type(self, node: ASTNode) -> Type:
        return type_inference.infer_call_return_type(
            node,
            self.symbols,
            self._type_ctx,
            self._current_func_info,
            self._current_class_name,
            self._node_types,
        )

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

    def _lower_expr_as_bool(self, node: ASTNode) -> "ir.Expr":
        """Lower expression used in boolean context, adding truthy checks as needed."""
        return lowering.lower_expr_as_bool(
            node,
            self._lower_expr,
            self._lower_expr_as_bool,
            self._infer_expr_type_from_ast,
            self._is_isinstance_call,
            self._resolve_type_name,
            self._type_ctx,
            self.symbols,
        )

    def _lower_expr(self, node: ASTNode) -> "ir.Expr":
        """Lower a Python expression to IR."""
        ctx, dispatch = self._make_ctx_and_dispatch()
        return lowering.lower_expr(node, ctx, dispatch)

    def _infer_expr_type_from_ast(self, node: ASTNode) -> Type:
        """Infer the type of a Python AST expression without lowering it."""
        return type_inference.infer_expr_type_from_ast(
            node,
            self._type_ctx,
            self.symbols,
            self._current_func_info,
            self._current_class_name,
            self._node_types,
        )

    def _lower_expr_List(self, node: ASTNode, expected_type: Type | None = None) -> "ir.Expr":
        return lowering.lower_expr_List(
            node,
            self._lower_expr,
            self._infer_expr_type_from_ast,
            self._type_ctx.expected,
            expected_type,
        )

    def _lower_stmt(self, node: ASTNode) -> "ir.Stmt":
        """Lower a Python statement to IR."""
        ctx, dispatch = self._make_ctx_and_dispatch()
        return lowering.lower_stmt(node, ctx, dispatch)

    def _lower_stmts(self, stmts: list[ASTNode]) -> list["ir.Stmt"]:
        """Lower a list of statements."""
        return [self._lower_stmt(s) for s in stmts]

    def _is_isinstance_call(self, node: ASTNode) -> tuple[str, str] | None:
        """Check if node is isinstance(var, Type). Returns (var_name, type_name) or None."""
        return lowering.is_isinstance_call(node)

    def _is_kind_check(self, node: ASTNode) -> tuple[str, str] | None:
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

    def _lower_lvalue(self, node: ASTNode) -> "ir.LValue":
        """Lower an expression to an LValue."""
        return lowering.lower_lvalue(node, self._lower_expr)
