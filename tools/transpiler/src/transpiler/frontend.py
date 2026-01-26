"""Frontend: Python AST -> IR.

Converts parable.py Python subset to language-agnostic IR.
All analysis happens here; backends just emit syntax.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .go_overrides import FIELD_TYPE_OVERRIDES, PARAM_TYPE_OVERRIDES, RETURN_TYPE_OVERRIDES
from .ir import (
    BOOL,
    BYTE,
    FLOAT,
    INT,
    STRING,
    VOID,
    Constant,
    Field,
    FieldInfo,
    FuncInfo,
    FuncType,
    Function,
    Interface,
    Loc,
    Map,
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
    TupleAssign,
    Type,
)

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


@dataclass
class TypeContext:
    """Context for bidirectional type inference (Pierce & Turner style)."""
    expected: Type | None = None  # Top-down expected type from parent
    var_types: dict[str, Type] = field(default_factory=dict)  # Variable types in scope
    return_type: Type | None = None  # Current function's return type


class Frontend:
    """Converts Python AST to IR Module."""

    def __init__(self) -> None:
        self.symbols = SymbolTable()
        self._node_types: set[str] = set()  # classes that inherit from Node
        # Type inference context
        self._current_func_info: FuncInfo | None = None
        self._current_class_name: str = ""
        self._type_ctx: TypeContext = TypeContext()

    def transpile(self, source: str) -> Module:
        """Parse Python source and produce IR Module."""
        tree = ast.parse(source)
        # Pass 1: Collect class names and inheritance
        self._collect_class_names(tree)
        # Pass 2: Mark Node subclasses
        self._mark_node_subclasses()
        # Pass 3: Collect function and method signatures
        self._collect_signatures(tree)
        # Pass 4: Collect struct fields
        self._collect_fields(tree)
        # Pass 5: Collect module-level constants
        self._collect_constants(tree)
        # Build IR Module
        return self._build_module(tree)

    def _collect_class_names(self, tree: ast.Module) -> None:
        """Pass 1: Collect all class names and their bases."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [self._get_base_name(b) for b in node.bases]
                self.symbols.structs[node.name] = StructInfo(
                    name=node.name, bases=bases
                )

    def _mark_node_subclasses(self) -> None:
        """Pass 2: Mark classes that inherit from Node."""
        for name, info in self.symbols.structs.items():
            info.is_node = self._is_node_subclass(name)
            if info.is_node:
                self._node_types.add(name)

    def _is_node_subclass(self, name: str) -> bool:
        """Check if a class is a Node subclass (directly or transitively)."""
        if name == "Node":
            return True
        info = self.symbols.structs.get(name)
        if not info:
            return False
        return any(self._is_node_subclass(base) for base in info.bases)

    def _collect_signatures(self, tree: ast.Module) -> None:
        """Pass 3: Collect function and method signatures."""
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                self.symbols.functions[node.name] = self._extract_func_info(node)
            elif isinstance(node, ast.ClassDef):
                self._collect_class_methods(node)

    def _collect_class_methods(self, node: ast.ClassDef) -> None:
        """Collect method signatures for a class."""
        info = self.symbols.structs[node.name]
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef):
                func_info = self._extract_func_info(stmt, is_method=True)
                func_info.is_method = True
                func_info.receiver_type = node.name
                info.methods[stmt.name] = func_info

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
                py_type = self._annotation_to_str(stmt.annotation)
                typ = self._py_type_to_ir(py_type)
                info.fields[stmt.target.id] = FieldInfo(
                    name=stmt.target.id, typ=typ, py_name=stmt.target.id
                )
        # Collect fields from __init__
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                self._collect_init_fields(stmt, info)

    def _collect_init_fields(self, init: ast.FunctionDef, info: StructInfo) -> None:
        """Collect fields assigned in __init__."""
        param_types: dict[str, str] = {}
        # Record __init__ parameter order (excluding self) for constructor calls
        for arg in init.args.args:
            if arg.arg != "self":
                info.init_params.append(arg.arg)
                if arg.annotation:
                    param_types[arg.arg] = self._annotation_to_str(arg.annotation)
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
                        typ = self._py_type_to_ir(py_type)
                        # Apply field type overrides (keep for compatibility)
                        override_key = (info.name, field_name)
                        if override_key in FIELD_TYPE_OVERRIDES:
                            # Convert Go type override to IR type
                            go_type = FIELD_TYPE_OVERRIDES[override_key]
                            typ = self._go_type_to_ir(go_type)
                        info.fields[field_name] = FieldInfo(
                            name=field_name, typ=typ, py_name=field_name
                        )
            elif isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "self"
                    ):
                        field_name = target.attr
                        if field_name not in info.fields:
                            typ = self._infer_type_from_value(stmt.value, param_types)
                            info.fields[field_name] = FieldInfo(
                                name=field_name, typ=typ, py_name=field_name
                            )

    def _collect_constants(self, tree: ast.Module) -> None:
        """Pass 5: Collect module-level and class-level constants."""
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name) and target.id.isupper():
                    # All-caps name = constant
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, int):
                        self.symbols.constants[target.id] = INT
            # Collect class-level constants (e.g., TokenType.EOF = 0)
            elif isinstance(node, ast.ClassDef):
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                        target = stmt.targets[0]
                        if isinstance(target, ast.Name) and target.id.isupper():
                            if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, int):
                                # Store as ClassName_CONST_NAME
                                const_name = f"{node.name}_{target.id}"
                                self.symbols.constants[const_name] = INT

    def _extract_func_info(
        self, node: ast.FunctionDef, is_method: bool = False
    ) -> FuncInfo:
        """Extract function signature information."""
        params = []
        non_self_args = [a for a in node.args.args if a.arg != "self"]
        n_params = len(non_self_args)
        n_defaults = len(node.args.defaults) if node.args.defaults else 0
        for i, arg in enumerate(non_self_args):
            py_type = self._annotation_to_str(arg.annotation) if arg.annotation else ""
            typ = self._py_type_to_ir(py_type) if py_type else Interface("any")
            # Check for overrides
            override_key = (node.name, arg.arg)
            if override_key in PARAM_TYPE_OVERRIDES:
                typ = self._go_type_to_ir(PARAM_TYPE_OVERRIDES[override_key])
            has_default = False
            default_value = None
            # Check if this param has a default
            if i >= n_params - n_defaults:
                has_default = True
                default_idx = i - (n_params - n_defaults)
                if node.args.defaults and default_idx < len(node.args.defaults):
                    default_value = self._lower_expr(node.args.defaults[default_idx])
            params.append(ParamInfo(name=arg.arg, typ=typ, has_default=has_default, default_value=default_value))
        return_type = VOID
        if node.returns:
            py_return = self._annotation_to_str(node.returns)
            return_type = self._py_return_type_to_ir(py_return)
        # Apply return type overrides
        if node.name in RETURN_TYPE_OVERRIDES:
            return_type = self._go_type_to_ir(RETURN_TYPE_OVERRIDES[node.name])
        return FuncInfo(
            name=node.name,
            params=params,
            return_type=return_type,
            is_method=is_method,
        )

    def _build_module(self, tree: ast.Module) -> Module:
        """Build IR Module from collected symbols."""
        from . import ir
        module = Module(name="parable")
        # Build constants (module-level and class-level)
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name) and target.id in self.symbols.constants:
                    value = self._lower_expr(node.value)
                    module.constants.append(
                        Constant(name=target.id, typ=INT, value=value, loc=self._loc_from_node(node))
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
        # Build structs
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                struct = self._build_struct(node)
                if struct:
                    module.structs.append(struct)
        # Build functions
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                func = self._build_function_shell(node)
                module.functions.append(func)
        return module

    def _build_struct(self, node: ast.ClassDef) -> Struct | None:
        """Build IR Struct from class definition."""
        info = self.symbols.structs.get(node.name)
        if not info:
            return None
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
        # Build methods (shells only for Phase 2)
        methods = []
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name != "__init__":
                method = self._build_method_shell(stmt, node.name)
                methods.append(method)
        implements = []
        if info.is_node:
            implements.append("Node")
        return Struct(
            name=node.name,
            fields=fields,
            methods=methods,
            implements=implements,
            loc=self._loc_from_node(node),
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
            var_types = self._collect_var_types(node.body)
            if func_info:
                for p in func_info.params:
                    var_types[p.name] = p.typ
            self._type_ctx = TypeContext(
                return_type=func_info.return_type if func_info else VOID,
                var_types=var_types,
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
        from .ir import Receiver
        body = []
        if with_body:
            # Set up type context for this method
            self._current_func_info = func_info
            self._current_class_name = class_name
            # Collect variable types from body and add parameters + self
            var_types = self._collect_var_types(node.body)
            if func_info:
                for p in func_info.params:
                    var_types[p.name] = p.typ
            var_types["self"] = Pointer(StructRef(class_name))
            self._type_ctx = TypeContext(
                return_type=func_info.return_type if func_info else VOID,
                var_types=var_types,
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
        if hasattr(node, "lineno"):
            return Loc(
                line=node.lineno,
                col=node.col_offset,
                end_line=getattr(node, "end_lineno", node.lineno) or node.lineno,
                end_col=getattr(node, "end_col_offset", node.col_offset) or node.col_offset,
            )
        return Loc.unknown()

    def _get_base_name(self, base: ast.expr) -> str:
        """Extract base class name from AST node."""
        if isinstance(base, ast.Name):
            return base.id
        if isinstance(base, ast.Attribute):
            return base.attr
        return ""

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
        if not py_type:
            return Interface("any")
        # Handle simple types
        if py_type in TYPE_MAP:
            return TYPE_MAP[py_type]
        # Handle bare "list" without type args
        if py_type == "list":
            return Slice(Interface("any"))
        # Handle bare "dict" without type args
        if py_type == "dict":
            return Map(STRING, Interface("any"))
        # Handle bare "set" without type args
        if py_type == "set":
            return Set(Interface("any"))
        # Handle X | None -> Optional[base type]
        if " | " in py_type:
            parts = self._split_union_types(py_type)
            if len(parts) > 1:
                parts = [p for p in parts if p != "None"]
                if len(parts) == 1:
                    inner = self._py_type_to_ir(parts[0], concrete_nodes)
                    return Optional(inner)
                # If all parts are Node subclasses, return Node interface
                if all(self._is_node_subclass(p) for p in parts):
                    return Interface("Node")
                return Interface("any")
        # Handle list[X]
        if py_type.startswith("list["):
            inner = py_type[5:-1]
            return Slice(self._py_type_to_ir(inner, concrete_nodes))
        # Handle dict[K, V]
        if py_type.startswith("dict["):
            inner = py_type[5:-1]
            parts = self._split_type_args(inner)
            if len(parts) == 2:
                return Map(
                    self._py_type_to_ir(parts[0], concrete_nodes),
                    self._py_type_to_ir(parts[1], concrete_nodes),
                )
        # Handle set[X]
        if py_type.startswith("set["):
            inner = py_type[4:-1]
            return Set(self._py_type_to_ir(inner, concrete_nodes))
        # Handle tuple[...] - in parameters, use interface
        if py_type.startswith("tuple["):
            return Interface("any")
        # Handle Callable
        if py_type.startswith("Callable["):
            return self._parse_callable_type(py_type, concrete_nodes)
        # Handle class names
        if py_type in self.symbols.structs:
            info = self.symbols.structs[py_type]
            if info.is_node or py_type == "Node":
                if concrete_nodes and py_type != "Node":
                    return Pointer(StructRef(py_type))
                return Interface("Node")
            return Pointer(StructRef(py_type))
        # Known internal types
        if py_type in ("Token", "QuoteState", "ParseContext", "Lexer", "Parser"):
            return Pointer(StructRef(py_type))
        # Type aliases - union types of Node subtypes
        if py_type in ("ArithNode", "CondNode"):
            return Interface("Node")
        # Python builtin aliases
        if py_type == "bytearray":
            return Slice(BYTE)
        if py_type == "tuple":
            return Interface("any")
        # Type alias mappings
        if py_type == "CommandSub":
            return Pointer(StructRef("CommandSubstitution"))
        if py_type == "ProcessSub":
            return Pointer(StructRef("ProcessSubstitution"))
        # Unknown type - return as interface
        return Interface(py_type)

    def _py_return_type_to_ir(self, py_type: str) -> Type:
        """Convert Python return type to IR, handling tuples as multiple returns."""
        if not py_type or py_type == "None":
            return VOID
        # Handle unions before tuple
        if " | " in py_type:
            parts = self._split_union_types(py_type)
            if len(parts) > 1:
                parts = [p for p in parts if p != "None"]
                if len(parts) == 1:
                    return self._py_return_type_to_ir(parts[0])
                return Interface("any")
        # Handle tuple[...] specially for return types
        if py_type.startswith("tuple["):
            inner = py_type[6:-1]
            parts = self._split_type_args(inner)
            from .ir import Tuple
            elements = tuple(self._py_type_to_ir(p, concrete_nodes=True) for p in parts)
            return Tuple(elements)
        # For non-tuples, use standard conversion with concrete node types
        return self._py_type_to_ir(py_type, concrete_nodes=True)

    def _parse_callable_type(self, py_type: str, concrete_nodes: bool) -> Type:
        """Parse Callable[[], ReturnType] -> FuncType."""
        inner = py_type[9:-1]  # Remove "Callable[" and "]"
        parts = self._split_type_args(inner)
        if len(parts) >= 2:
            args_str = parts[0]
            ret_type = parts[-1]
            ret = self._py_type_to_ir(ret_type, concrete_nodes)
            # Handle empty args list "[]"
            if args_str == "[]":
                return FuncType(params=(), ret=ret)
            # Handle args list like "[int, str]"
            if args_str.startswith("[") and args_str.endswith("]"):
                args_inner = args_str[1:-1]
                if args_inner:
                    param_types = tuple(
                        self._py_type_to_ir(a.strip(), concrete_nodes)
                        for a in args_inner.split(",")
                    )
                    return FuncType(params=param_types, ret=ret)
                return FuncType(params=(), ret=ret)
        return Interface("any")

    def _go_type_to_ir(self, go_type: str) -> Type:
        """Convert Go type string to IR Type (for overrides)."""
        if go_type == "string":
            return STRING
        if go_type == "int":
            return INT
        if go_type == "bool":
            return BOOL
        if go_type == "float64":
            return FLOAT
        if go_type == "interface{}":
            return Interface("any")
        if go_type == "Node":
            return Interface("Node")
        if go_type.startswith("[]"):
            elem = self._go_type_to_ir(go_type[2:])
            return Slice(elem)
        if go_type.startswith("*"):
            target = go_type[1:]
            # Recursively parse the target type (could be slice, struct, etc.)
            return Pointer(self._go_type_to_ir(target))
        if go_type.startswith("map["):
            # Parse map[K]V
            bracket_end = go_type.find("]")
            if bracket_end > 4:
                key = self._go_type_to_ir(go_type[4:bracket_end])
                value = self._go_type_to_ir(go_type[bracket_end + 1 :])
                return Map(key, value)
        if go_type.startswith("(") and go_type.endswith(")"):
            # Tuple return type
            inner = go_type[1:-1]
            parts = [p.strip() for p in inner.split(",")]
            from .ir import Tuple
            elements = tuple(self._go_type_to_ir(p) for p in parts)
            return Tuple(elements)
        # Unknown - treat as struct ref
        return StructRef(go_type)

    def _infer_type_from_value(
        self, node: ast.expr, param_types: dict[str, str]
    ) -> Type:
        """Infer IR type from an expression."""
        match node:
            case ast.Constant(value=bool()):
                return BOOL
            case ast.Constant(value=int()):
                return INT
            case ast.Constant(value=str()):
                return STRING
            case ast.Constant(value=None):
                return Interface("any")
            case ast.List(elts=[first, *_]):
                return Slice(self._infer_type_from_value(first, param_types))
            case ast.List():
                return Slice(Interface("any"))
            case ast.Dict(values=values) if values and all(
                isinstance(v, ast.Constant) and isinstance(v.value, str) for v in values
            ):
                return Map(STRING, STRING)
            case ast.Dict():
                return Map(STRING, Interface("any"))
            case ast.Name(id=name) if name in param_types:
                return self._py_type_to_ir(param_types[name])
            case ast.Name(id="True" | "False"):
                return BOOL
            case ast.Name(id="None"):
                return Interface("any")
            case ast.Call(func=ast.Name(id="len")):
                return INT
            case ast.Call(func=ast.Name(id=func_name)) if func_name in self.symbols.structs:
                info = self.symbols.structs[func_name]
                if info.is_node:
                    return Interface("Node")
                return Pointer(StructRef(func_name))
            case ast.Call(func=ast.Name(id="QuoteState")):
                return Pointer(StructRef("QuoteState"))
            case ast.Call(func=ast.Name(id="ContextStack")):
                return Pointer(StructRef("ContextStack"))
            case ast.Attribute(value=ast.Name(id=class_name)) if class_name in (
                "ParserStateFlags",
                "DolbraceState",
                "TokenType",
                "MatchedPairFlags",
                "WordCtx",
                "ParseContext",
            ):
                return INT
        return Interface("any")

    def _split_union_types(self, s: str) -> list[str]:
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

    def _split_type_args(self, s: str) -> list[str]:
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

    # ============================================================
    # LOCAL TYPE INFERENCE (Pierce & Turner style)
    # ============================================================

    def _collect_var_types(self, stmts: list[ast.stmt]) -> dict[str, Type]:
        """Pre-scan function body to collect variable types from usage patterns."""
        var_types: dict[str, Type] = {}
        for stmt in ast.walk(ast.Module(body=stmts, type_ignores=[])):
            # Infer from append() calls: var.append(x) -> var is []T where T = type(x)
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                if isinstance(call.func, ast.Attribute) and call.func.attr == "append":
                    if isinstance(call.func.value, ast.Name) and call.args:
                        var_name = call.func.value.id
                        elem_type = self._infer_element_type_from_append_arg(call.args[0])
                        if elem_type != Interface("any"):
                            var_types[var_name] = Slice(elem_type)
            # Infer from annotated assignments
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                py_type = self._annotation_to_str(stmt.annotation)
                var_types[stmt.target.id] = self._py_type_to_ir(py_type)
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
        return var_types

    def _infer_element_type_from_append_arg(self, arg: ast.expr) -> Type:
        """Infer slice element type from what's being appended."""
        # Method call that returns a pointer: .Copy() returns same type
        if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute):
            method = arg.func.attr
            if method == "Copy":
                # x.Copy() where x is ctx -> *ParseContext
                if isinstance(arg.func.value, ast.Name):
                    var = arg.func.value.id
                    if var == "ctx":
                        return Pointer(StructRef("ParseContext"))
        # Constructor calls
        if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name):
            class_name = arg.func.id
            if class_name in self.symbols.structs:
                info = self.symbols.structs[class_name]
                if info.is_node:
                    return Interface("Node")
                return Pointer(StructRef(class_name))
        return Interface("any")

    def _synthesize_type(self, expr: "ir.Expr") -> Type:
        """Bottom-up type synthesis: compute type from expression structure."""
        from . import ir
        # Literals have known types
        if isinstance(expr, (ir.IntLit, ir.FloatLit, ir.StringLit, ir.BoolLit)):
            return expr.typ
        # Variable lookup
        if isinstance(expr, ir.Var):
            if expr.name in self._type_ctx.var_types:
                return self._type_ctx.var_types[expr.name]
            # Check function parameters
            if self._current_func_info:
                for p in self._current_func_info.params:
                    if p.name == expr.name:
                        return p.typ
        # Field access - look up field type
        if isinstance(expr, ir.FieldAccess):
            obj_type = self._synthesize_type(expr.obj)
            return self._synthesize_field_type(obj_type, expr.field)
        # Method call - look up return type
        if isinstance(expr, ir.MethodCall):
            obj_type = self._synthesize_type(expr.obj)
            return self._synthesize_method_return_type(obj_type, expr.method)
        # Index - derive element type
        if isinstance(expr, ir.Index):
            obj_type = self._synthesize_type(expr.obj)
            return self._synthesize_index_type(obj_type)
        return expr.typ

    def _synthesize_field_type(self, obj_type: Type, field: str) -> Type:
        """Look up field type from struct info."""
        # Handle Pointer(StructRef(...))
        if isinstance(obj_type, Pointer) and isinstance(obj_type.target, StructRef):
            struct_name = obj_type.target.name
            if struct_name in self.symbols.structs:
                field_info = self.symbols.structs[struct_name].fields.get(field)
                if field_info:
                    return field_info.typ
        # Handle direct StructRef
        if isinstance(obj_type, StructRef):
            if obj_type.name in self.symbols.structs:
                field_info = self.symbols.structs[obj_type.name].fields.get(field)
                if field_info:
                    return field_info.typ
        return Interface("any")

    def _synthesize_method_return_type(self, obj_type: Type, method: str) -> Type:
        """Look up method return type from struct info."""
        # Extract struct name from various type wrappers
        struct_name = self._extract_struct_name(obj_type)
        if struct_name and struct_name in self.symbols.structs:
            method_info = self.symbols.structs[struct_name].methods.get(method)
            if method_info:
                return method_info.return_type
        return Interface("any")

    def _extract_struct_name(self, typ: Type) -> str | None:
        """Extract struct name from wrapped types like Pointer, Optional, etc."""
        if isinstance(typ, StructRef):
            return typ.name
        if isinstance(typ, Pointer):
            return self._extract_struct_name(typ.target)
        if isinstance(typ, Optional):
            return self._extract_struct_name(typ.inner)
        return None

    def _synthesize_index_type(self, obj_type: Type) -> Type:
        """Derive element type from indexing a container."""
        if isinstance(obj_type, Slice):
            return obj_type.element
        if isinstance(obj_type, Map):
            return obj_type.value
        if obj_type == STRING:
            return BYTE  # string[i] returns byte in Go
        return Interface("any")

    def _coerce(self, expr: "ir.Expr", from_type: Type, to_type: Type) -> "ir.Expr":
        """Apply type coercions when synthesized type doesn't match expected."""
        from . import ir
        # byte → string: wrap with string() cast
        if from_type == BYTE and to_type == STRING:
            return ir.Cast(expr=expr, to_type=STRING, typ=STRING, loc=expr.loc)
        # nil → string: convert to empty string
        if isinstance(expr, ir.NilLit) and to_type == STRING:
            return ir.StringLit(value="", typ=STRING, loc=expr.loc)
        # []interface{} → []T: use typed slice
        if isinstance(from_type, Slice) and isinstance(to_type, Slice):
            if from_type.element == Interface("any"):
                # Update the expression's type to the expected slice type
                expr.typ = to_type
                if isinstance(expr, ir.SliceLit):
                    expr.element_type = to_type.element
        return expr

    # ============================================================
    # EXPRESSION LOWERING (Phase 3)
    # ============================================================

    def _lower_expr_as_bool(self, node: ast.expr) -> "ir.Expr":
        """Lower expression used in boolean context, adding truthy checks as needed."""
        from . import ir
        # Already boolean expressions - lower directly
        if isinstance(node, ast.Compare):
            return self._lower_expr(node)
        if isinstance(node, ast.BoolOp):
            # For BoolOp, recursively lower operands as booleans
            op = "&&" if isinstance(node.op, ast.And) else "||"
            result = self._lower_expr_as_bool(node.values[0])
            for val in node.values[1:]:
                right = self._lower_expr_as_bool(val)
                result = ir.BinaryOp(op=op, left=result, right=right, typ=BOOL, loc=self._loc_from_node(node))
            return result
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            operand = self._lower_expr_as_bool(node.operand)
            return ir.UnaryOp(op="!", operand=operand, typ=BOOL, loc=self._loc_from_node(node))
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return self._lower_expr(node)
        if isinstance(node, ast.Name) and node.id in ("True", "False"):
            return self._lower_expr(node)
        if isinstance(node, ast.Call):
            # Calls that return bool are fine
            if isinstance(node.func, ast.Attribute):
                # Methods like .startswith(), .endswith(), .isdigit() return bool
                if node.func.attr in ("startswith", "endswith", "isdigit", "isalpha", "isalnum", "isspace"):
                    return self._lower_expr(node)
                # Check if the method returns bool by looking up its return type
                method_return_type = self._infer_expr_type_from_ast(node)
                if method_return_type == BOOL:
                    return self._lower_expr(node)
            elif isinstance(node.func, ast.Name):
                if node.func.id in ("isinstance", "hasattr", "callable", "bool"):
                    return self._lower_expr(node)
                # Check if the function returns bool by looking up its return type
                func_name = node.func.id
                if func_name in self.symbols.functions:
                    func_info = self.symbols.functions[func_name]
                    if func_info.return_type == BOOL:
                        return self._lower_expr(node)
        # Non-boolean expression - needs truthy check
        expr = self._lower_expr(node)
        # Use the IR expression's type if available, otherwise infer from AST
        expr_type = expr.typ if hasattr(expr, 'typ') and expr.typ != Interface("any") else self._infer_expr_type_from_ast(node)
        # Bool expressions don't need nil check
        if expr_type == BOOL:
            return expr
        # String truthy check: s != ""
        if expr_type == STRING:
            return ir.BinaryOp(op="!=", left=expr, right=ir.StringLit(value="", typ=STRING), typ=BOOL, loc=self._loc_from_node(node))
        # Int truthy check: n != 0
        if expr_type == INT:
            return ir.BinaryOp(op="!=", left=expr, right=ir.IntLit(value=0, typ=INT), typ=BOOL, loc=self._loc_from_node(node))
        # Check attribute access (likely pointer/optional)
        if isinstance(node, ast.Attribute):
            return ir.IsNil(expr=expr, negated=True, typ=BOOL, loc=self._loc_from_node(node))
        # Check name that might be pointer - but only if type is unknown or pointer
        if isinstance(node, ast.Name):
            # If type is unknown, assume pointer
            if expr_type == Interface("any"):
                return ir.IsNil(expr=expr, negated=True, typ=BOOL, loc=self._loc_from_node(node))
            # If type is a pointer, use nil check
            if isinstance(expr_type, (Pointer, Optional)):
                return ir.IsNil(expr=expr, negated=True, typ=BOOL, loc=self._loc_from_node(node))
            # Otherwise just return the expression (shouldn't reach here for valid types)
            return expr
        # For other expressions, assume it's a pointer check
        return ir.IsNil(expr=expr, negated=True, typ=BOOL, loc=self._loc_from_node(node))

    def _lower_expr(self, node: ast.expr) -> "ir.Expr":
        """Lower a Python expression to IR."""
        from . import ir
        method = f"_lower_expr_{node.__class__.__name__}"
        if hasattr(self, method):
            return getattr(self, method)(node)
        # Fallback for unimplemented expressions
        return ir.Var(name=f"TODO_{node.__class__.__name__}", typ=Interface("any"))

    def _lower_expr_Constant(self, node: ast.Constant) -> "ir.Expr":
        from . import ir
        if isinstance(node.value, bool):
            return ir.BoolLit(value=node.value, typ=BOOL, loc=self._loc_from_node(node))
        if isinstance(node.value, int):
            return ir.IntLit(value=node.value, typ=INT, loc=self._loc_from_node(node))
        if isinstance(node.value, float):
            return ir.FloatLit(value=node.value, typ=FLOAT, loc=self._loc_from_node(node))
        if isinstance(node.value, str):
            return ir.StringLit(value=node.value, typ=STRING, loc=self._loc_from_node(node))
        if node.value is None:
            return ir.NilLit(typ=Interface("any"), loc=self._loc_from_node(node))
        return ir.Var(name=f"TODO_Constant_{type(node.value)}", typ=Interface("any"))

    def _lower_expr_Name(self, node: ast.Name) -> "ir.Expr":
        from . import ir
        if node.id == "True":
            return ir.BoolLit(value=True, typ=BOOL, loc=self._loc_from_node(node))
        if node.id == "False":
            return ir.BoolLit(value=False, typ=BOOL, loc=self._loc_from_node(node))
        if node.id == "None":
            return ir.NilLit(typ=Interface("any"), loc=self._loc_from_node(node))
        # Variable reference - type will be resolved during analysis
        return ir.Var(name=node.id, typ=Interface("any"), loc=self._loc_from_node(node))

    def _lower_expr_Attribute(self, node: ast.Attribute) -> "ir.Expr":
        from . import ir
        # Check for class constant access (e.g., TokenType.EOF -> TokenType_EOF)
        if isinstance(node.value, ast.Name):
            class_name = node.value.id
            const_name = f"{class_name}_{node.attr}"
            if const_name in self.symbols.constants:
                return ir.Var(name=const_name, typ=INT, loc=self._loc_from_node(node))
        obj = self._lower_expr(node.value)
        return ir.FieldAccess(
            obj=obj, field=node.attr, typ=Interface("any"), loc=self._loc_from_node(node)
        )

    def _lower_expr_Subscript(self, node: ast.Subscript) -> "ir.Expr":
        from . import ir
        obj = self._lower_expr(node.value)
        if isinstance(node.slice, ast.Slice):
            low = self._lower_expr(node.slice.lower) if node.slice.lower else None
            high = self._lower_expr(node.slice.upper) if node.slice.upper else None
            return ir.SliceExpr(
                obj=obj, low=low, high=high, typ=Interface("any"), loc=self._loc_from_node(node)
            )
        idx = self._lower_expr(node.slice)
        index_expr = ir.Index(obj=obj, index=idx, typ=Interface("any"), loc=self._loc_from_node(node))
        # Check if indexing a string field - if so, wrap with Cast to string
        # In Go, string[i] returns byte, but Python returns str
        if self._is_string_index(node):
            return ir.Cast(expr=index_expr, to_type=STRING, typ=STRING, loc=self._loc_from_node(node))
        return index_expr

    def _is_string_index(self, node: ast.Subscript) -> bool:
        """Check if this is indexing a string (field or variable)."""
        # Check for self.source[...] pattern
        if isinstance(node.value, ast.Attribute):
            if isinstance(node.value.value, ast.Name) and node.value.value.id == "self":
                field = node.value.attr
                if self._current_class_name in self.symbols.structs:
                    struct_info = self.symbols.structs[self._current_class_name]
                    field_info = struct_info.fields.get(field)
                    if field_info and field_info.typ == STRING:
                        return True
        # Check for string variable[...] pattern
        if isinstance(node.value, ast.Name):
            var_name = node.value.id
            if var_name in self._type_ctx.var_types:
                if self._type_ctx.var_types[var_name] == STRING:
                    return True
        return False

    def _infer_expr_type_from_ast(self, node: ast.expr) -> Type:
        """Infer the type of a Python AST expression without lowering it."""
        # Constant literals
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return BOOL
            if isinstance(node.value, int):
                return INT
            if isinstance(node.value, str):
                return STRING
            if isinstance(node.value, float):
                return FLOAT
        # Variable lookup
        if isinstance(node, ast.Name):
            if node.id in self._type_ctx.var_types:
                return self._type_ctx.var_types[node.id]
            # Check function parameters
            if self._current_func_info:
                for p in self._current_func_info.params:
                    if p.name == node.id:
                        return p.typ
        # Field access on self
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id == "self":
                field = node.attr
                if self._current_class_name in self.symbols.structs:
                    struct_info = self.symbols.structs[self._current_class_name]
                    field_info = struct_info.fields.get(field)
                    if field_info:
                        return field_info.typ
        # Method call - look up return type
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            obj_type = self._infer_expr_type_from_ast(node.func.value)
            return self._synthesize_method_return_type(obj_type, node.func.attr)
        # String indexing returns string (after our Cast)
        if isinstance(node, ast.Subscript) and self._is_string_index(node):
            return STRING
        # BinOp - infer type based on operator
        if isinstance(node, ast.BinOp):
            if isinstance(node.op, (ast.BitAnd, ast.BitOr, ast.BitXor, ast.LShift, ast.RShift)):
                return INT
            if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.FloorDiv, ast.Mod)):
                left_type = self._infer_expr_type_from_ast(node.left)
                right_type = self._infer_expr_type_from_ast(node.right)
                if left_type == INT or right_type == INT:
                    return INT
        return Interface("any")

    def _lower_expr_BinOp(self, node: ast.BinOp) -> "ir.Expr":
        from . import ir
        left = self._lower_expr(node.left)
        right = self._lower_expr(node.right)
        op = self._binop_to_str(node.op)
        # Infer result type based on operator
        result_type: Type = Interface("any")
        if isinstance(node.op, (ast.BitAnd, ast.BitOr, ast.BitXor, ast.LShift, ast.RShift)):
            result_type = INT
        elif isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.FloorDiv, ast.Mod)):
            # Check if operands are ints
            left_type = self._infer_expr_type_from_ast(node.left)
            right_type = self._infer_expr_type_from_ast(node.right)
            if left_type == INT or right_type == INT:
                result_type = INT
        return ir.BinaryOp(op=op, left=left, right=right, typ=result_type, loc=self._loc_from_node(node))

    def _lower_expr_Compare(self, node: ast.Compare) -> "ir.Expr":
        from . import ir
        # Handle simple comparisons
        if len(node.ops) == 1 and len(node.comparators) == 1:
            left = self._lower_expr(node.left)
            right = self._lower_expr(node.comparators[0])
            op = self._cmpop_to_str(node.ops[0])
            # Special case for "is None" / "is not None"
            if isinstance(node.ops[0], ast.Is) and isinstance(node.comparators[0], ast.Constant) and node.comparators[0].value is None:
                # For strings, compare to empty string; for bools, compare to false
                left_type = self._infer_expr_type_from_ast(node.left)
                if left_type == STRING:
                    cmp_op = "=="
                    return ir.BinaryOp(op=cmp_op, left=left, right=ir.StringLit(value="", typ=STRING), typ=BOOL, loc=self._loc_from_node(node))
                if left_type == BOOL:
                    return ir.UnaryOp(op="!", operand=left, typ=BOOL, loc=self._loc_from_node(node))
                return ir.IsNil(expr=left, negated=False, typ=BOOL, loc=self._loc_from_node(node))
            if isinstance(node.ops[0], ast.IsNot) and isinstance(node.comparators[0], ast.Constant) and node.comparators[0].value is None:
                # For strings, compare to non-empty string; for bools, just use the bool itself
                left_type = self._infer_expr_type_from_ast(node.left)
                if left_type == STRING:
                    cmp_op = "!="
                    return ir.BinaryOp(op=cmp_op, left=left, right=ir.StringLit(value="", typ=STRING), typ=BOOL, loc=self._loc_from_node(node))
                if left_type == BOOL:
                    return left  # bool is its own truthy value
                return ir.IsNil(expr=left, negated=True, typ=BOOL, loc=self._loc_from_node(node))
            # Handle string vs pointer/optional string comparison: dereference the pointer side
            left_type = self._infer_expr_type_from_ast(node.left)
            right_type = self._infer_expr_type_from_ast(node.comparators[0])
            if left_type == STRING and isinstance(right_type, (Optional, Pointer)):
                inner = right_type.inner if isinstance(right_type, Optional) else right_type.target
                if inner == STRING:
                    right = ir.UnaryOp(op="*", operand=right, typ=STRING, loc=self._loc_from_node(node))
            elif right_type == STRING and isinstance(left_type, (Optional, Pointer)):
                inner = left_type.inner if isinstance(left_type, Optional) else left_type.target
                if inner == STRING:
                    left = ir.UnaryOp(op="*", operand=left, typ=STRING, loc=self._loc_from_node(node))
            return ir.BinaryOp(op=op, left=left, right=right, typ=BOOL, loc=self._loc_from_node(node))
        # Chain comparisons - convert to AND of pairwise comparisons
        result = None
        prev = self._lower_expr(node.left)
        for op, comp in zip(node.ops, node.comparators):
            curr = self._lower_expr(comp)
            cmp = ir.BinaryOp(op=self._cmpop_to_str(op), left=prev, right=curr, typ=BOOL, loc=self._loc_from_node(node))
            if result is None:
                result = cmp
            else:
                result = ir.BinaryOp(op="&&", left=result, right=cmp, typ=BOOL, loc=self._loc_from_node(node))
            prev = curr
        return result or ir.BoolLit(value=True, typ=BOOL)

    def _lower_expr_BoolOp(self, node: ast.BoolOp) -> "ir.Expr":
        from . import ir
        op = "&&" if isinstance(node.op, ast.And) else "||"
        result = self._lower_expr(node.values[0])
        for val in node.values[1:]:
            right = self._lower_expr(val)
            result = ir.BinaryOp(op=op, left=result, right=right, typ=BOOL, loc=self._loc_from_node(node))
        return result

    def _lower_expr_UnaryOp(self, node: ast.UnaryOp) -> "ir.Expr":
        from . import ir
        operand = self._lower_expr(node.operand)
        op = self._unaryop_to_str(node.op)
        return ir.UnaryOp(op=op, operand=operand, typ=Interface("any"), loc=self._loc_from_node(node))

    def _lower_expr_Call(self, node: ast.Call) -> "ir.Expr":
        from . import ir
        args = [self._lower_expr(a) for a in node.args]
        # Method call
        if isinstance(node.func, ast.Attribute):
            obj = self._lower_expr(node.func.value)
            method = node.func.attr
            # Handle Python list methods that need special Go treatment
            if method == "append" and args:
                # Look up actual type of the object (might be pointer to slice for params)
                obj_type = self._infer_expr_type_from_ast(node.func.value)
                # list.append(x) -> append(list, x) in Go (handled via MethodCall for now)
                return ir.MethodCall(
                    obj=obj, method="append", args=args,
                    receiver_type=obj_type if obj_type != Interface("any") else Slice(Interface("any")),
                    typ=VOID, loc=self._loc_from_node(node)
                )
            if method == "pop" and not args:
                # list.pop() -> return last element and shrink slice
                return ir.MethodCall(
                    obj=obj, method="pop", args=[],
                    receiver_type=Slice(Interface("any")), typ=Interface("any"), loc=self._loc_from_node(node)
                )
            # Infer receiver type for proper method lookup
            obj_type = self._infer_expr_type_from_ast(node.func.value)
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
                return ir.Len(expr=args[0], typ=INT, loc=self._loc_from_node(node))
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
                # list(x) is a copy operation
                return ir.MethodCall(
                    obj=args[0], method="copy", args=[],
                    receiver_type=Slice(Interface("any")), typ=Slice(Interface("any")), loc=self._loc_from_node(node)
                )
            # Check for constructor calls (class names)
            if func_name in self.symbols.structs:
                # Constructor call -> StructLit with fields mapped from positional args
                struct_info = self.symbols.structs[func_name]
                fields: dict[str, ir.Expr] = {}
                for i, arg_expr in enumerate(args):
                    if i < len(struct_info.init_params):
                        param_name = struct_info.init_params[i]
                        fields[param_name] = arg_expr
                return ir.StructLit(
                    struct_name=func_name, fields=fields,
                    typ=Pointer(StructRef(func_name)), loc=self._loc_from_node(node)
                )
            return ir.Call(func=func_name, args=args, typ=Interface("any"), loc=self._loc_from_node(node))
        return ir.Var(name="TODO_Call", typ=Interface("any"))

    def _lower_expr_IfExp(self, node: ast.IfExp) -> "ir.Expr":
        from . import ir
        cond = self._lower_expr(node.test)
        then_expr = self._lower_expr(node.body)
        else_expr = self._lower_expr(node.orelse)
        # Infer type from branches - prefer then branch, fall back to else
        result_type = self._infer_expr_type_from_ast(node.body)
        if result_type == Interface("any"):
            result_type = self._infer_expr_type_from_ast(node.orelse)
        return ir.Ternary(
            cond=cond, then_expr=then_expr, else_expr=else_expr,
            typ=result_type, loc=self._loc_from_node(node)
        )

    def _lower_expr_List(self, node: ast.List) -> "ir.Expr":
        from . import ir
        elements = [self._lower_expr(e) for e in node.elts]
        # Infer element type from first element if available
        element_type: Type = Interface("any")
        if node.elts:
            element_type = self._infer_expr_type_from_ast(node.elts[0])
        return ir.SliceLit(
            element_type=element_type, elements=elements,
            typ=Slice(element_type), loc=self._loc_from_node(node)
        )

    def _lower_expr_Dict(self, node: ast.Dict) -> "ir.Expr":
        from . import ir
        entries = []
        for k, v in zip(node.keys, node.values):
            if k is not None:
                entries.append((self._lower_expr(k), self._lower_expr(v)))
        return ir.MapLit(
            key_type=STRING, value_type=Interface("any"), entries=entries,
            typ=Map(STRING, Interface("any")), loc=self._loc_from_node(node)
        )

    def _lower_expr_JoinedStr(self, node: ast.JoinedStr) -> "ir.Expr":
        """Lower Python f-string to StringFormat IR node."""
        template_parts: list[str] = []
        args: list["ir.Expr"] = []
        for part in node.values:
            if isinstance(part, ast.Constant):
                # Escape % signs in literal parts for fmt.Sprintf
                template_parts.append(str(part.value).replace("%", "%%"))
            elif isinstance(part, ast.FormattedValue):
                template_parts.append("%v")
                args.append(self._lower_expr(part.value))
        template = "".join(template_parts)
        return StringFormat(template=template, args=args, typ=STRING, loc=self._loc_from_node(node))

    def _lower_expr_Tuple(self, node: ast.Tuple) -> "ir.Expr":
        """Lower Python tuple literal to TupleLit IR node."""
        from . import ir
        elements = [self._lower_expr(e) for e in node.elts]
        return ir.TupleLit(elements=elements, typ=Interface("any"), loc=self._loc_from_node(node))

    def _binop_to_str(self, op: ast.operator) -> str:
        return {
            ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
            ast.FloorDiv: "/", ast.Mod: "%", ast.Pow: "**",
            ast.LShift: "<<", ast.RShift: ">>",
            ast.BitOr: "|", ast.BitXor: "^", ast.BitAnd: "&",
        }.get(type(op), "+")

    def _cmpop_to_str(self, op: ast.cmpop) -> str:
        return {
            ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=",
            ast.Gt: ">", ast.GtE: ">=", ast.Is: "==", ast.IsNot: "!=",
            ast.In: "in", ast.NotIn: "not in",
        }.get(type(op), "==")

    def _unaryop_to_str(self, op: ast.unaryop) -> str:
        return {ast.Not: "!", ast.USub: "-", ast.UAdd: "+", ast.Invert: "~"}.get(type(op), "-")

    # ============================================================
    # STATEMENT LOWERING (Phase 3)
    # ============================================================

    def _lower_stmt(self, node: ast.stmt) -> "ir.Stmt":
        """Lower a Python statement to IR."""
        from . import ir
        method = f"_lower_stmt_{node.__class__.__name__}"
        if hasattr(self, method):
            return getattr(self, method)(node)
        # Fallback for unimplemented statements
        return ir.ExprStmt(expr=ir.Var(name=f"TODO_{node.__class__.__name__}", typ=Interface("any")))

    def _lower_stmts(self, stmts: list[ast.stmt]) -> list["ir.Stmt"]:
        """Lower a list of statements."""
        return [self._lower_stmt(s) for s in stmts]

    def _lower_stmt_Expr(self, node: ast.Expr) -> "ir.Stmt":
        from . import ir
        # Skip docstrings
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return ir.ExprStmt(expr=ir.Var(name="_skip_docstring", typ=VOID))
        return ir.ExprStmt(expr=self._lower_expr(node.value), loc=self._loc_from_node(node))

    def _lower_stmt_Assign(self, node: ast.Assign) -> "ir.Stmt":
        from . import ir
        value = self._lower_expr(node.value)
        if len(node.targets) == 1:
            target = node.targets[0]
            # Handle tuple unpacking: a, b = func() where func returns tuple
            if isinstance(target, ast.Tuple) and len(target.elts) == 2:
                # Special case for popping from stack with tuple unpacking
                if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
                    if node.value.func.attr == "pop":
                        # a, b = stack.pop() -> entry := stack[len(stack)-1]; stack = stack[:len(stack)-1]; a = entry.A; b = entry.B
                        obj = self._lower_expr(node.value.func.value)
                        obj_lval = self._lower_lvalue(node.value.func.value)
                        lval0 = self._lower_lvalue(target.elts[0])
                        lval1 = self._lower_lvalue(target.elts[1])
                        len_minus_1 = ir.BinaryOp(op="-", left=ir.Len(expr=obj, typ=INT), right=ir.IntLit(value=1, typ=INT), typ=INT)
                        # Use quoteStackEntry type for the entry
                        entry_type = StructRef("quoteStackEntry")
                        entry_var = ir.Var(name="_entry", typ=entry_type)
                        return ir.Block(body=[
                            ir.VarDecl(name="_entry", typ=entry_type, value=ir.Index(obj=obj, index=len_minus_1, typ=entry_type)),
                            ir.Assign(target=obj_lval, value=ir.SliceExpr(obj=obj, high=len_minus_1, typ=Interface("any"))),
                            ir.Assign(target=lval0, value=ir.FieldAccess(obj=entry_var, field="Single", typ=BOOL)),
                            ir.Assign(target=lval1, value=ir.FieldAccess(obj=entry_var, field="Double", typ=BOOL)),
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
            # Coerce value to target type if known
            if isinstance(target, ast.Name) and target.id in self._type_ctx.var_types:
                expected_type = self._type_ctx.var_types[target.id]
                from_type = self._synthesize_type(value)
                value = self._coerce(value, from_type, expected_type)
            lval = self._lower_lvalue(target)
            return ir.Assign(target=lval, value=value, loc=self._loc_from_node(node))
        # Multiple targets - emit first one (simplification)
        lval = self._lower_lvalue(node.targets[0])
        return ir.Assign(target=lval, value=value, loc=self._loc_from_node(node))

    def _lower_stmt_AnnAssign(self, node: ast.AnnAssign) -> "ir.Stmt":
        from . import ir
        py_type = self._annotation_to_str(node.annotation)
        typ = self._py_type_to_ir(py_type)
        if node.value:
            value = self._lower_expr(node.value)
            # Coerce value to annotated type
            from_type = self._synthesize_type(value)
            value = self._coerce(value, from_type, typ)
        else:
            value = None
        if isinstance(node.target, ast.Name):
            return ir.VarDecl(name=node.target.id, typ=typ, value=value, loc=self._loc_from_node(node))
        # Attribute target - treat as assignment
        lval = self._lower_lvalue(node.target)
        if value:
            return ir.Assign(target=lval, value=value, loc=self._loc_from_node(node))
        return ir.ExprStmt(expr=ir.Var(name="_skip_ann", typ=VOID))

    def _lower_stmt_AugAssign(self, node: ast.AugAssign) -> "ir.Stmt":
        from . import ir
        lval = self._lower_lvalue(node.target)
        value = self._lower_expr(node.value)
        op = self._binop_to_str(node.op)
        return ir.OpAssign(target=lval, op=op, value=value, loc=self._loc_from_node(node))

    def _lower_stmt_Return(self, node: ast.Return) -> "ir.Stmt":
        from . import ir
        value = self._lower_expr(node.value) if node.value else None
        # Apply type coercion based on function return type
        if value and self._type_ctx.return_type:
            from_type = self._synthesize_type(value)
            value = self._coerce(value, from_type, self._type_ctx.return_type)
        return ir.Return(value=value, loc=self._loc_from_node(node))

    def _lower_stmt_If(self, node: ast.If) -> "ir.Stmt":
        from . import ir
        cond = self._lower_expr_as_bool(node.test)
        then_body = self._lower_stmts(node.body)
        else_body = self._lower_stmts(node.orelse) if node.orelse else []
        return ir.If(cond=cond, then_body=then_body, else_body=else_body, loc=self._loc_from_node(node))

    def _lower_stmt_While(self, node: ast.While) -> "ir.Stmt":
        from . import ir
        cond = self._lower_expr_as_bool(node.test)
        body = self._lower_stmts(node.body)
        return ir.While(cond=cond, body=body, loc=self._loc_from_node(node))

    def _lower_stmt_For(self, node: ast.For) -> "ir.Stmt":
        from . import ir
        iterable = self._lower_expr(node.iter)
        body = self._lower_stmts(node.body)
        # Determine index and value names
        index = None
        value = None
        if isinstance(node.target, ast.Name):
            if node.target.id == "_":
                pass  # Discard
            else:
                value = node.target.id
        elif isinstance(node.target, ast.Tuple) and len(node.target.elts) == 2:
            if isinstance(node.target.elts[0], ast.Name):
                index = node.target.elts[0].id if node.target.elts[0].id != "_" else None
            if isinstance(node.target.elts[1], ast.Name):
                value = node.target.elts[1].id if node.target.elts[1].id != "_" else None
        return ir.ForRange(index=index, value=value, iterable=iterable, body=body, loc=self._loc_from_node(node))

    def _lower_stmt_Break(self, node: ast.Break) -> "ir.Stmt":
        from . import ir
        return ir.Break(loc=self._loc_from_node(node))

    def _lower_stmt_Continue(self, node: ast.Continue) -> "ir.Stmt":
        from . import ir
        return ir.Continue(loc=self._loc_from_node(node))

    def _lower_stmt_Pass(self, node: ast.Pass) -> "ir.Stmt":
        from . import ir
        return ir.ExprStmt(expr=ir.Var(name="_pass", typ=VOID), loc=self._loc_from_node(node))

    def _lower_stmt_Raise(self, node: ast.Raise) -> "ir.Stmt":
        from . import ir
        if node.exc:
            # Extract error type and message from exception
            if isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name):
                error_type = node.exc.func.id
                msg = self._lower_expr(node.exc.args[0]) if node.exc.args else ir.StringLit(value="", typ=STRING)
                pos = self._lower_expr(node.exc.args[1]) if len(node.exc.args) > 1 else ir.IntLit(value=0, typ=INT)
                return ir.Raise(error_type=error_type, message=msg, pos=pos, loc=self._loc_from_node(node))
        return ir.Raise(error_type="Error", message=ir.StringLit(value="", typ=STRING), pos=ir.IntLit(value=0, typ=INT), loc=self._loc_from_node(node))

    def _lower_stmt_Try(self, node: ast.Try) -> "ir.Stmt":
        from . import ir
        body = self._lower_stmts(node.body)
        catch_var = None
        catch_body: list[ir.Stmt] = []
        reraise = False
        if node.handlers:
            handler = node.handlers[0]
            catch_var = handler.name
            catch_body = self._lower_stmts(handler.body)
            # Check if handler re-raises
            for stmt in handler.body:
                if isinstance(stmt, ast.Raise) and stmt.exc is None:
                    reraise = True
        return ir.TryCatch(body=body, catch_var=catch_var, catch_body=catch_body, reraise=reraise, loc=self._loc_from_node(node))

    def _lower_stmt_FunctionDef(self, node: ast.FunctionDef) -> "ir.Stmt":
        from . import ir
        # Skip local function definitions for now
        return ir.ExprStmt(expr=ir.Var(name=f"_local_func_{node.name}", typ=VOID))

    def _lower_lvalue(self, node: ast.expr) -> "ir.LValue":
        """Lower an expression to an LValue."""
        from . import ir
        if isinstance(node, ast.Name):
            return ir.VarLV(name=node.id, loc=self._loc_from_node(node))
        if isinstance(node, ast.Attribute):
            obj = self._lower_expr(node.value)
            return ir.FieldLV(obj=obj, field=node.attr, loc=self._loc_from_node(node))
        if isinstance(node, ast.Subscript):
            obj = self._lower_expr(node.value)
            idx = self._lower_expr(node.slice)
            return ir.IndexLV(obj=obj, index=idx, loc=self._loc_from_node(node))
        return ir.VarLV(name="_unknown_lvalue", loc=self._loc_from_node(node))
