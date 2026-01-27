"""Frontend: Python AST -> IR.

Converts parable.py Python subset to language-agnostic IR.
All analysis happens here; backends just emit syntax.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .type_overrides import FIELD_TYPE_OVERRIDES, PARAM_TYPE_OVERRIDES, RETURN_TYPE_OVERRIDES
from .ir import (
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

# Mapping from .kind string values to class names (for x.kind == "..." patterns)
KIND_TO_CLASS: dict[str, str] = {
    "word": "Word",
    "command": "Command",
    "pipeline": "Pipeline",
    "list": "List",
    "operator": "Operator",
    "pipe-both": "PipeBoth",
    "empty": "Empty",
    "comment": "Comment",
    "redirect": "Redirect",
    "heredoc": "Heredoc",
    "subshell": "Subshell",
    "brace-group": "BraceGroup",
    "if": "If",
    "while": "While",
    "until": "Until",
    "for": "For",
    "for-arith": "ForArith",
    "select": "Select",
    "case": "Case",
    "pattern": "Pattern",
    "function": "Function",
    "param": "Parameter",
    "param-len": "ParameterLength",
    "param-indirect": "ParameterIndirect",
    "cmdsub": "CommandSubstitution",
    "arith": "ArithmeticExpansion",
    "arith-cmd": "ArithCommand",
    "number": "ArithNumber",
    "var": "ArithVar",
    "binary-op": "ArithBinaryOp",
    "unary-op": "ArithUnaryOp",
    "pre-incr": "ArithPreIncr",
    "post-incr": "ArithPostIncr",
    "pre-decr": "ArithPreDecr",
    "post-decr": "ArithPostDecr",
    "assign": "ArithAssign",
    "ternary": "ArithTernary",
    "comma": "ArithComma",
    "subscript": "ArithSubscript",
    "escape": "EscapeSequence",
    "arith-deprecated": "ArithDeprecatedExpr",
    "arith-concat": "ArithConcat",
    "ansi-c": "AnsiCQuote",
    "locale": "LocaleQuote",
    "procsub": "ProcessSubstitution",
    "negation": "Negation",
    "time": "Time",
    "cond-expr": "ConditionalExpr",
    "unary-test": "UnaryTest",
    "binary-test": "BinaryTest",
    "cond-and": "CondAnd",
    "cond-or": "CondOr",
    "cond-not": "CondNot",
    "cond-paren": "CondParen",
    "array": "Array",
    "coproc": "Coproc",
}


@dataclass
class TypeContext:
    """Context for bidirectional type inference (Pierce & Turner style)."""
    expected: Type | None = None  # Top-down expected type from parent
    var_types: dict[str, Type] = field(default_factory=dict)  # Variable types in scope
    return_type: Type | None = None  # Current function's return type
    tuple_vars: dict[str, list[str]] = field(default_factory=dict)  # Maps var -> synthetic var names
    sentinel_ints: set[str] = field(default_factory=set)  # Variables that use -1 sentinel for None
    narrowed_vars: set[str] = field(default_factory=set)  # Variables narrowed from interface type


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
                            typ = FIELD_TYPE_OVERRIDES[override_key]
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
                            # Apply field type overrides
                            override_key = (info.name, field_name)
                            if override_key in FIELD_TYPE_OVERRIDES:
                                typ = FIELD_TYPE_OVERRIDES[override_key]
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
                typ = PARAM_TYPE_OVERRIDES[override_key]
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
            return_type = RETURN_TYPE_OVERRIDES[node.name]
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
        # Build Node interface (abstract base for AST nodes)
        node_interface = InterfaceDef(
            name="Node",
            methods=[
                MethodSig(name="GetKind", params=[], ret=STRING),
                MethodSig(name="ToSexp", params=[], ret=STRING),
            ],
        )
        module.interfaces.append(node_interface)
        # Build structs (with method bodies)
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                struct = self._build_struct(node, with_body=True)
                if struct:
                    module.structs.append(struct)
        # Build functions (with bodies)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                func = self._build_function_shell(node, with_body=True)
                module.functions.append(func)
        return module

    def _build_struct(self, node: ast.ClassDef, with_body: bool = False) -> Struct | None:
        """Build IR Struct from class definition."""
        # Node is emitted as InterfaceDef, not Struct
        if node.name == "Node":
            return None
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
        # Build methods
        methods = []
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name != "__init__":
                method = self._build_method_shell(stmt, node.name, with_body=with_body)
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
            var_types, tuple_vars, sentinel_ints = self._collect_var_types(node.body)
            if func_info:
                for p in func_info.params:
                    var_types[p.name] = p.typ
            self._type_ctx = TypeContext(
                return_type=func_info.return_type if func_info else VOID,
                var_types=var_types,
                tuple_vars=tuple_vars,
                sentinel_ints=sentinel_ints,
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
            var_types, tuple_vars, sentinel_ints = self._collect_var_types(node.body)
            if func_info:
                for p in func_info.params:
                    var_types[p.name] = p.typ
            var_types["self"] = Pointer(StructRef(class_name))
            self._type_ctx = TypeContext(
                return_type=func_info.return_type if func_info else VOID,
                var_types=var_types,
                tuple_vars=tuple_vars,
                sentinel_ints=sentinel_ints,
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
                    # For Node | None, use Node interface (interfaces are nilable in Go)
                    if parts[0] == "Node" or self._is_node_subclass(parts[0]):
                        return Interface("Node")
                    # For str | None, just use string (empty string represents None)
                    if inner == STRING:
                        return STRING
                    # For int | None, use int with -1 sentinel (handled elsewhere)
                    if inner == INT:
                        return Optional(inner)
                    return Optional(inner)
                # If all parts are Node subclasses, return Node interface (nilable)
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

    def _collect_var_types(self, stmts: list[ast.stmt]) -> tuple[dict[str, Type], dict[str, list[str]], set[str]]:
        """Pre-scan function body to collect variable types, tuple var mappings, and sentinel ints."""
        var_types: dict[str, Type] = {}
        tuple_vars: dict[str, list[str]] = {}
        sentinel_ints: set[str] = set()
        # First pass: collect For loop variable types (needed for append inference)
        for stmt in ast.walk(ast.Module(body=stmts, type_ignores=[])):
            if isinstance(stmt, ast.For):
                if isinstance(stmt.target, ast.Name):
                    loop_var = stmt.target.id
                    iterable_type = self._infer_iterable_type(stmt.iter, var_types)
                    if isinstance(iterable_type, Slice):
                        var_types[loop_var] = iterable_type.element
                elif isinstance(stmt.target, ast.Tuple) and len(stmt.target.elts) == 2:
                    if isinstance(stmt.target.elts[1], ast.Name):
                        loop_var = stmt.target.elts[1].id
                        iterable_type = self._infer_iterable_type(stmt.iter, var_types)
                        if isinstance(iterable_type, Slice):
                            var_types[loop_var] = iterable_type.element
        # Second pass: infer other variable types
        for stmt in ast.walk(ast.Module(body=stmts, type_ignores=[])):
            # Infer from append() calls: var.append(x) -> var is []T where T = type(x)
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                if isinstance(call.func, ast.Attribute) and call.func.attr == "append":
                    if isinstance(call.func.value, ast.Name) and call.args:
                        var_name = call.func.value.id
                        elem_type = self._infer_element_type_from_append_arg(call.args[0], var_types)
                        if elem_type != Interface("any"):
                            var_types[var_name] = Slice(elem_type)
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
                    # Infer from subscript/slice on strings: var = str[...] -> string
                    elif isinstance(stmt.value, ast.Subscript):
                        container_type: Type = Interface("any")
                        if isinstance(stmt.value.value, ast.Name):
                            container_name = stmt.value.value.id
                            if container_name in var_types:
                                container_type = var_types[container_name]
                        if container_type == STRING:
                            var_types[var_name] = STRING
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
        return var_types, tuple_vars, sentinel_ints

    def _infer_iterable_type(self, node: ast.expr, var_types: dict[str, Type]) -> Type:
        """Infer the type of an iterable expression."""
        # self.field
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id == "self" and self._current_class_name:
                struct_info = self.symbols.structs.get(self._current_class_name)
                if struct_info:
                    field_info = struct_info.fields.get(node.attr)
                    if field_info:
                        return field_info.typ
        # Variable reference
        if isinstance(node, ast.Name):
            if node.id in var_types:
                return var_types[node.id]
        return Interface("any")

    def _infer_element_type_from_append_arg(self, arg: ast.expr, var_types: dict[str, Type]) -> Type:
        """Infer slice element type from what's being appended."""
        # Variable reference with known type (e.g., loop variable)
        if isinstance(arg, ast.Name):
            if arg.id in var_types:
                return var_types[arg.id]
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
        # String methods that return string
        if obj_type == STRING and method in ("join", "replace", "lower", "upper", "strip", "lstrip", "rstrip", "format"):
            return STRING
        # String methods that return int
        if obj_type == STRING and method in ("find", "rfind", "index", "rindex", "count"):
            return INT
        # String methods that return bool
        if obj_type == STRING and method in ("startswith", "endswith", "isdigit", "isalpha", "isalnum", "isspace"):
            return BOOL
        # Extract struct name from various type wrappers
        struct_name = self._extract_struct_name(obj_type)
        if struct_name and struct_name in self.symbols.structs:
            method_info = self.symbols.structs[struct_name].methods.get(method)
            if method_info:
                return method_info.return_type
        return Interface("any")

    def _merge_keyword_args(self, obj_type: Type, method: str, args: list, node: ast.Call) -> list:
        """Merge keyword arguments into positional args at their proper positions."""
        from . import ir
        if not node.keywords:
            return args
        struct_name = self._extract_struct_name(obj_type)
        if not struct_name or struct_name not in self.symbols.structs:
            return args
        method_info = self.symbols.structs[struct_name].methods.get(method)
        if not method_info:
            return args
        # Build param name -> index map
        param_indices: dict[str, int] = {}
        for i, param in enumerate(method_info.params):
            param_indices[param.name] = i
        # Extend args list if needed
        result = list(args)
        for kw in node.keywords:
            if kw.arg and kw.arg in param_indices:
                idx = param_indices[kw.arg]
                # Extend list if necessary
                while len(result) <= idx:
                    result.append(None)
                result[idx] = self._lower_expr(kw.value)
        return result

    def _fill_default_args(self, obj_type: Type, method: str, args: list) -> list:
        """Fill in missing arguments with default values for methods with optional params."""
        from . import ir
        struct_name = self._extract_struct_name(obj_type)
        if not struct_name or struct_name not in self.symbols.structs:
            return args
        method_info = self.symbols.structs[struct_name].methods.get(method)
        if not method_info:
            return args
        n_expected = len(method_info.params)
        # Extend to full length if needed
        result = list(args)
        while len(result) < n_expected:
            result.append(None)
        # Fill in None slots with defaults
        for i, arg in enumerate(result):
            if arg is None and i < n_expected:
                param = method_info.params[i]
                if param.has_default and param.default_value is not None:
                    result[i] = param.default_value
        return result

    def _fill_default_args_for_func(self, func_info: FuncInfo, args: list) -> list:
        """Fill in missing arguments with default values for free functions with optional params."""
        n_expected = len(func_info.params)
        if len(args) >= n_expected:
            return args
        # Extend to full length if needed
        result = list(args)
        while len(result) < n_expected:
            result.append(None)
        # Fill in None slots with defaults
        for i, arg in enumerate(result):
            if arg is None and i < n_expected:
                param = func_info.params[i]
                if param.has_default and param.default_value is not None:
                    result[i] = param.default_value
        return result

    def _add_address_of_for_ptr_params(self, obj_type: Type, method: str, args: list, orig_args: list[ast.expr]) -> list:
        """Add & when passing slice to pointer-to-slice parameter."""
        from . import ir
        struct_name = self._extract_struct_name(obj_type)
        if not struct_name or struct_name not in self.symbols.structs:
            return args
        method_info = self.symbols.structs[struct_name].methods.get(method)
        if not method_info:
            return args
        result = list(args)
        for i, arg in enumerate(result):
            if i >= len(method_info.params) or i >= len(orig_args):
                break
            param = method_info.params[i]
            param_type = param.typ
            # Check if param expects pointer to slice but arg is slice
            if isinstance(param_type, Pointer) and isinstance(param_type.target, Slice):
                # Infer arg type from AST
                arg_type = self._infer_expr_type_from_ast(orig_args[i])
                if isinstance(arg_type, Slice) and not isinstance(arg_type, Pointer):
                    # Wrap with address-of
                    result[i] = ir.UnaryOp(op="&", operand=arg, typ=param_type, loc=arg.loc if hasattr(arg, 'loc') else Loc.unknown())
        return result

    def _extract_struct_name(self, typ: Type) -> str | None:
        """Extract struct name from wrapped types like Pointer, Optional, etc."""
        if isinstance(typ, StructRef):
            return typ.name
        if isinstance(typ, Pointer):
            return self._extract_struct_name(typ.target)
        if isinstance(typ, Optional):
            return self._extract_struct_name(typ.inner)
        return None

    def _infer_call_return_type(self, node: ast.Call) -> Type:
        """Infer the return type of a function or method call."""
        from .ir import Tuple
        if isinstance(node.func, ast.Attribute):
            # Method call - look up return type
            obj_type = self._infer_expr_type_from_ast(node.func.value)
            struct_name = self._extract_struct_name(obj_type)
            if struct_name and struct_name in self.symbols.structs:
                method_info = self.symbols.structs[struct_name].methods.get(node.func.attr)
                if method_info:
                    return method_info.return_type
        elif isinstance(node.func, ast.Name):
            # Free function call
            func_name = node.func.id
            if func_name in self.symbols.functions:
                return self.symbols.functions[func_name].return_type
        return Interface("any")

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
        # Tuple coercion: coerce each element individually
        if isinstance(to_type, Tuple) and isinstance(expr, ir.TupleLit):
            new_elements = []
            for i, elem in enumerate(expr.elements):
                if i < len(to_type.elements):
                    elem_from_type = self._synthesize_type(elem)
                    new_elements.append(self._coerce(elem, elem_from_type, to_type.elements[i]))
                else:
                    new_elements.append(elem)
            expr.elements = new_elements
            expr.typ = to_type
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
            # Track isinstance narrowing for AND chains
            narrowed_var: str | None = None
            narrowed_old_type: Type | None = None
            was_already_narrowed = False
            if isinstance(node.op, ast.And):
                isinstance_check = self._is_isinstance_call(node.values[0])
                if isinstance_check:
                    var_name, type_name = isinstance_check
                    narrowed_var = var_name
                    narrowed_old_type = self._type_ctx.var_types.get(var_name)
                    was_already_narrowed = var_name in self._type_ctx.narrowed_vars
                    self._type_ctx.var_types[var_name] = self._resolve_type_name(type_name)
                    self._type_ctx.narrowed_vars.add(var_name)
            for val in node.values[1:]:
                right = self._lower_expr_as_bool(val)
                result = ir.BinaryOp(op=op, left=result, right=right, typ=BOOL, loc=self._loc_from_node(node))
            # Restore narrowed type and tracking
            if narrowed_var is not None:
                if narrowed_old_type is not None:
                    self._type_ctx.var_types[narrowed_var] = narrowed_old_type
                else:
                    self._type_ctx.var_types.pop(narrowed_var, None)
                if not was_already_narrowed:
                    self._type_ctx.narrowed_vars.discard(narrowed_var)
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
        # Slice/Map/Set truthy check: len(x) > 0
        if isinstance(expr_type, (Slice, Map, Set)):
            return ir.BinaryOp(op=">", left=ir.Len(expr=expr, typ=INT, loc=self._loc_from_node(node)), right=ir.IntLit(value=0, typ=INT), typ=BOOL, loc=self._loc_from_node(node))
        # Interface truthy check: x != nil
        if isinstance(expr_type, Interface):
            return ir.IsNil(expr=expr, negated=True, typ=BOOL, loc=self._loc_from_node(node))
        # Pointer/Optional truthy check: x != nil
        if isinstance(expr_type, (Pointer, Optional)):
            return ir.IsNil(expr=expr, negated=True, typ=BOOL, loc=self._loc_from_node(node))
        # Check name that might be pointer or interface - use nil check
        if isinstance(node, ast.Name):
            # If type is interface, use nil check (interfaces are nilable)
            if isinstance(expr_type, Interface):
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
        # Look up variable type from context
        var_type = self._type_ctx.var_types.get(node.id, Interface("any"))
        return ir.Var(name=node.id, typ=var_type, loc=self._loc_from_node(node))

    def _lower_expr_Attribute(self, node: ast.Attribute) -> "ir.Expr":
        from . import ir
        # Check for class constant access (e.g., TokenType.EOF -> TokenType_EOF)
        if isinstance(node.value, ast.Name):
            class_name = node.value.id
            const_name = f"{class_name}_{node.attr}"
            if const_name in self.symbols.constants:
                return ir.Var(name=const_name, typ=INT, loc=self._loc_from_node(node))
        obj = self._lower_expr(node.value)
        # If accessing field on a narrowed variable, wrap in TypeAssert
        if isinstance(node.value, ast.Name) and node.value.id in self._type_ctx.narrowed_vars:
            var_type = self._type_ctx.var_types.get(node.value.id)
            if var_type and isinstance(var_type, Pointer) and isinstance(var_type.target, StructRef):
                obj = ir.TypeAssert(
                    expr=obj, asserted=var_type, safe=True,
                    typ=var_type, loc=self._loc_from_node(node.value)
                )
        # Infer field type for self.field accesses
        field_type: Type = Interface("any")
        if isinstance(node.value, ast.Name) and node.value.id == "self":
            if self._current_class_name in self.symbols.structs:
                struct_info = self.symbols.structs[self._current_class_name]
                field_info = struct_info.fields.get(node.attr)
                if field_info:
                    field_type = field_info.typ
        return ir.FieldAccess(
            obj=obj, field=node.attr, typ=field_type, loc=self._loc_from_node(node)
        )

    def _lower_expr_Subscript(self, node: ast.Subscript) -> "ir.Expr":
        from . import ir
        # Check for tuple var indexing: cmdsub_result[0] -> cmdsub_result0
        if isinstance(node.value, ast.Name) and isinstance(node.slice, ast.Constant):
            var_name = node.value.id
            if var_name in self._type_ctx.tuple_vars and isinstance(node.slice.value, int):
                idx = node.slice.value
                synthetic_names = self._type_ctx.tuple_vars[var_name]
                if 0 <= idx < len(synthetic_names):
                    syn_name = synthetic_names[idx]
                    typ = self._type_ctx.var_types.get(syn_name, Interface("any"))
                    return ir.Var(name=syn_name, typ=typ, loc=self._loc_from_node(node))
        obj = self._lower_expr(node.value)
        if isinstance(node.slice, ast.Slice):
            low = self._convert_negative_index(node.slice.lower, obj, node) if node.slice.lower else None
            high = self._convert_negative_index(node.slice.upper, obj, node) if node.slice.upper else None
            # Slicing preserves type - string slice is still string, slice of slice is still slice
            slice_type: Type = self._infer_expr_type_from_ast(node.value)
            if slice_type == Interface("any"):
                slice_type = obj.typ if hasattr(obj, 'typ') else Interface("any")
            return ir.SliceExpr(
                obj=obj, low=low, high=high, typ=slice_type, loc=self._loc_from_node(node)
            )
        idx = self._convert_negative_index(node.slice, obj, node)
        # Infer element type from slice type
        elem_type: Type = Interface("any")
        obj_type = getattr(obj, 'typ', None)
        if isinstance(obj_type, Slice):
            elem_type = obj_type.element
        index_expr = ir.Index(obj=obj, index=idx, typ=elem_type, loc=self._loc_from_node(node))
        # Check if indexing a string - if so, wrap with Cast to string
        # In Go, string[i] returns byte, but Python returns str
        # Check both AST inference and lowered expression type
        is_string = self._infer_expr_type_from_ast(node.value) == STRING
        if not is_string and hasattr(obj, 'typ') and obj.typ == STRING:
            is_string = True
        if is_string:
            return ir.Cast(expr=index_expr, to_type=STRING, typ=STRING, loc=self._loc_from_node(node))
        return index_expr

    def _convert_negative_index(self, idx_node: ast.expr, obj: "ir.Expr", parent: ast.AST) -> "ir.Expr":
        """Convert negative index -N to len(obj) - N."""
        from . import ir
        # Check for -N pattern (UnaryOp with USub on positive int constant)
        if isinstance(idx_node, ast.UnaryOp) and isinstance(idx_node.op, ast.USub):
            if isinstance(idx_node.operand, ast.Constant) and isinstance(idx_node.operand.value, int):
                n = idx_node.operand.value
                if n > 0:
                    # len(obj) - N
                    return ir.BinaryOp(
                        op="-",
                        left=ir.Len(expr=obj, typ=INT, loc=self._loc_from_node(parent)),
                        right=ir.IntLit(value=n, typ=INT, loc=self._loc_from_node(idx_node)),
                        typ=INT,
                        loc=self._loc_from_node(idx_node)
                    )
        # Not a negative constant, lower normally
        return self._lower_expr(idx_node)

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
        # Field access
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id == "self":
                field = node.attr
                if self._current_class_name in self.symbols.structs:
                    struct_info = self.symbols.structs[self._current_class_name]
                    field_info = struct_info.fields.get(field)
                    if field_info:
                        return field_info.typ
            else:
                # Field access on other objects - infer object type then look up field
                obj_type = self._infer_expr_type_from_ast(node.value)
                struct_name = self._extract_struct_name(obj_type)
                if struct_name and struct_name in self.symbols.structs:
                    struct_info = self.symbols.structs[struct_name]
                    field_info = struct_info.fields.get(node.attr)
                    if field_info:
                        return field_info.typ
        # Method call - look up return type
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            obj_type = self._infer_expr_type_from_ast(node.func.value)
            return self._synthesize_method_return_type(obj_type, node.func.attr)
        # Free function call - look up return type
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.symbols.functions:
                return self.symbols.functions[func_name].return_type
        # Subscript - derive element type from container
        if isinstance(node, ast.Subscript):
            val_type = self._infer_expr_type_from_ast(node.value)
            if val_type == STRING:
                return STRING  # string indexing returns string (after Cast)
            if isinstance(val_type, Slice):
                return val_type.element
            if isinstance(val_type, Map):
                return val_type.value
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
                # For sentinel ints (int | None using -1), compare to -1
                if isinstance(node.left, ast.Name) and node.left.id in self._type_ctx.sentinel_ints:
                    return ir.BinaryOp(op="==", left=left, right=ir.IntLit(value=-1, typ=INT), typ=BOOL, loc=self._loc_from_node(node))
                return ir.IsNil(expr=left, negated=False, typ=BOOL, loc=self._loc_from_node(node))
            if isinstance(node.ops[0], ast.IsNot) and isinstance(node.comparators[0], ast.Constant) and node.comparators[0].value is None:
                # For strings, compare to non-empty string; for bools, just use the bool itself
                left_type = self._infer_expr_type_from_ast(node.left)
                if left_type == STRING:
                    cmp_op = "!="
                    return ir.BinaryOp(op=cmp_op, left=left, right=ir.StringLit(value="", typ=STRING), typ=BOOL, loc=self._loc_from_node(node))
                if left_type == BOOL:
                    return left  # bool is its own truthy value
                # For sentinel ints (int | None using -1), compare to -1
                if isinstance(node.left, ast.Name) and node.left.id in self._type_ctx.sentinel_ints:
                    return ir.BinaryOp(op="!=", left=left, right=ir.IntLit(value=-1, typ=INT), typ=BOOL, loc=self._loc_from_node(node))
                return ir.IsNil(expr=left, negated=True, typ=BOOL, loc=self._loc_from_node(node))
            # Handle "x in (a, b, c)" -> "x == a || x == b || x == c"
            if isinstance(node.ops[0], (ast.In, ast.NotIn)) and isinstance(node.comparators[0], ast.Tuple):
                negated = isinstance(node.ops[0], ast.NotIn)
                cmp_op = "!=" if negated else "=="
                join_op = "&&" if negated else "||"
                elts = node.comparators[0].elts
                if elts:
                    result = ir.BinaryOp(op=cmp_op, left=left, right=self._lower_expr(elts[0]), typ=BOOL, loc=self._loc_from_node(node))
                    for elt in elts[1:]:
                        cmp = ir.BinaryOp(op=cmp_op, left=left, right=self._lower_expr(elt), typ=BOOL, loc=self._loc_from_node(node))
                        result = ir.BinaryOp(op=join_op, left=result, right=cmp, typ=BOOL, loc=self._loc_from_node(node))
                    return result
                return ir.BoolLit(value=not negated, typ=BOOL, loc=self._loc_from_node(node))
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
        result = self._lower_expr_as_bool(node.values[0])
        for val in node.values[1:]:
            right = self._lower_expr_as_bool(val)
            result = ir.BinaryOp(op=op, left=result, right=right, typ=BOOL, loc=self._loc_from_node(node))
        return result

    def _lower_expr_UnaryOp(self, node: ast.UnaryOp) -> "ir.Expr":
        from . import ir
        # For 'not' operator, convert operand to boolean first
        if isinstance(node.op, ast.Not):
            operand = self._lower_expr_as_bool(node.operand)
            return ir.UnaryOp(op="!", operand=operand, typ=BOOL, loc=self._loc_from_node(node))
        operand = self._lower_expr(node.operand)
        op = self._unaryop_to_str(node.op)
        return ir.UnaryOp(op=op, operand=operand, typ=Interface("any"), loc=self._loc_from_node(node))

    def _lower_expr_Call(self, node: ast.Call) -> "ir.Expr":
        from . import ir
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
                # list.append(x) -> append(list, x) in Go (handled via MethodCall for now)
                return ir.MethodCall(
                    obj=obj, method="append", args=args,
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
            # Merge keyword arguments into args at proper positions
            args = self._merge_keyword_args(obj_type, method, args, node)
            # Fill in default values for any remaining missing parameters
            args = self._fill_default_args(obj_type, method, args)
            # Add & for pointer-to-slice params
            args = self._add_address_of_for_ptr_params(obj_type, method, args, node.args)
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
            # Check for isinstance(x, Type) -> IsType expression
            if func_name == "isinstance" and len(node.args) == 2:
                expr = self._lower_expr(node.args[0])
                if isinstance(node.args[1], ast.Name):
                    type_name = node.args[1].id
                    tested_type = self._resolve_type_name(type_name)
                    return ir.IsType(expr=expr, tested_type=tested_type, typ=BOOL, loc=self._loc_from_node(node))
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
            # Look up function return type and fill default args from symbol table
            ret_type: Type = Interface("any")
            if func_name in self.symbols.functions:
                func_info = self.symbols.functions[func_name]
                ret_type = func_info.return_type
                # Fill in default arguments
                args = self._fill_default_args_for_func(func_info, args)
            return ir.Call(func=func_name, args=args, typ=ret_type, loc=self._loc_from_node(node))
        return ir.Var(name="TODO_Call", typ=Interface("any"))

    def _lower_expr_IfExp(self, node: ast.IfExp) -> "ir.Expr":
        from . import ir
        cond = self._lower_expr_as_bool(node.test)
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
        element_types = tuple(e.typ for e in elements)
        return ir.TupleLit(elements=elements, typ=Tuple(elements=element_types), loc=self._loc_from_node(node))

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
        from .ir import Tuple as TupleType
        value = self._lower_expr(node.value)
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
            # Handle sentinel ints: var = None -> var = -1
            if (isinstance(target, ast.Name) and
                target.id in self._type_ctx.sentinel_ints and
                isinstance(value, ir.NilLit)):
                value = ir.IntLit(value=-1, typ=INT, loc=self._loc_from_node(node))
            # Coerce value to target type if known
            if isinstance(target, ast.Name) and target.id in self._type_ctx.var_types:
                expected_type = self._type_ctx.var_types[target.id]
                from_type = self._synthesize_type(value)
                value = self._coerce(value, from_type, expected_type)
            # Track variable type dynamically for later use in nested scopes
            if isinstance(target, ast.Name) and target.id not in self._type_ctx.var_types:
                value_type = self._synthesize_type(value)
                if value_type != Interface("any"):
                    self._type_ctx.var_types[target.id] = value_type
            # Propagate narrowed status: if assigning from a narrowed var, target is also narrowed
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Name):
                if node.value.id in self._type_ctx.narrowed_vars:
                    self._type_ctx.narrowed_vars.add(target.id)
                    # Also set the narrowed type for the target
                    narrowed_type = self._type_ctx.var_types.get(node.value.id)
                    if narrowed_type:
                        self._type_ctx.var_types[target.id] = narrowed_type
            lval = self._lower_lvalue(target)
            return ir.Assign(target=lval, value=value, loc=self._loc_from_node(node))
        # Multiple targets - emit first one (simplification)
        lval = self._lower_lvalue(node.targets[0])
        return ir.Assign(target=lval, value=value, loc=self._loc_from_node(node))

    def _lower_stmt_AnnAssign(self, node: ast.AnnAssign) -> "ir.Stmt":
        from . import ir
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

    def _is_isinstance_call(self, node: ast.expr) -> tuple[str, str] | None:
        """Check if node is isinstance(var, Type). Returns (var_name, type_name) or None."""
        if not isinstance(node, ast.Call):
            return None
        if not isinstance(node.func, ast.Name) or node.func.id != "isinstance":
            return None
        if len(node.args) != 2:
            return None
        if not isinstance(node.args[0], ast.Name):
            return None
        if not isinstance(node.args[1], ast.Name):
            return None
        return (node.args[0].id, node.args[1].id)

    def _is_kind_check(self, node: ast.expr) -> tuple[str, str] | None:
        """Check if node is x.kind == "typename". Returns (var_name, class_name) or None."""
        if not isinstance(node, ast.Compare):
            return None
        if len(node.ops) != 1 or not isinstance(node.ops[0], ast.Eq):
            return None
        if len(node.comparators) != 1:
            return None
        # Check for x.kind on left side
        if not isinstance(node.left, ast.Attribute) or node.left.attr != "kind":
            return None
        if not isinstance(node.left.value, ast.Name):
            return None
        var_name = node.left.value.id
        # Check for string constant on right side
        comparator = node.comparators[0]
        if not isinstance(comparator, ast.Constant) or not isinstance(comparator.value, str):
            return None
        kind_value = comparator.value
        # Map kind string to class name
        if kind_value not in KIND_TO_CLASS:
            return None
        return (var_name, KIND_TO_CLASS[kind_value])

    def _extract_isinstance_or_chain(self, node: ast.expr) -> tuple[str, list[str]] | None:
        """Extract isinstance/kind checks from expression. Returns (var_name, [type_names]) or None."""
        # Handle simple isinstance call
        simple = self._is_isinstance_call(node)
        if simple:
            return (simple[0], [simple[1]])
        # Handle x.kind == "typename" pattern
        kind_check = self._is_kind_check(node)
        if kind_check:
            return (kind_check[0], [kind_check[1]])
        # Handle isinstance(x, A) or isinstance(x, B) or ...
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
            var_name: str | None = None
            type_names: list[str] = []
            for value in node.values:
                check = self._is_isinstance_call(value) or self._is_kind_check(value)
                if not check:
                    return None  # Not all are isinstance/kind calls
                if var_name is None:
                    var_name = check[0]
                elif var_name != check[0]:
                    return None  # Different variables
                type_names.append(check[1])
            if var_name and type_names:
                return (var_name, type_names)
        return None

    def _extract_isinstance_from_and(self, node: ast.expr) -> tuple[str, str] | None:
        """Extract isinstance(var, Type) from compound AND expression.
        Returns (var_name, type_name) or None if no isinstance found."""
        if not isinstance(node, ast.BoolOp) or not isinstance(node.op, ast.And):
            return None
        # Check each value in the AND chain for isinstance
        for value in node.values:
            result = self._is_isinstance_call(value)
            if result:
                return result
        return None

    def _collect_isinstance_chain(self, node: ast.If, var_name: str) -> tuple[list["ir.TypeCase"], list["ir.Stmt"]]:
        """Collect isinstance checks on same variable into TypeSwitch cases."""
        from . import ir
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
        if name in self.symbols.structs:
            return Pointer(StructRef(name))
        return Interface(name)

    def _lower_stmt_If(self, node: ast.If) -> "ir.Stmt":
        from . import ir
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
        if isinstance_in_and:
            var_name, type_name = isinstance_in_and
            typ = self._resolve_type_name(type_name)
            old_type = self._type_ctx.var_types.get(var_name)
            was_already_narrowed = var_name in self._type_ctx.narrowed_vars
            self._type_ctx.var_types[var_name] = typ
            self._type_ctx.narrowed_vars.add(var_name)
            then_body = self._lower_stmts(node.body)
            if old_type is not None:
                self._type_ctx.var_types[var_name] = old_type
            else:
                self._type_ctx.var_types.pop(var_name, None)
            if not was_already_narrowed:
                self._type_ctx.narrowed_vars.discard(var_name)
        else:
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
        from .ir import RUNE
        iterable = self._lower_expr(node.iter)
        # Determine loop variable types based on iterable type
        iterable_type = self._infer_expr_type_from_ast(node.iter)
        # Determine index and value names
        index = None
        value = None
        if isinstance(node.target, ast.Name):
            if node.target.id == "_":
                pass  # Discard
            else:
                value = node.target.id
                # Iterating over string yields runes
                if iterable_type == STRING:
                    self._type_ctx.var_types[value] = RUNE
        elif isinstance(node.target, ast.Tuple) and len(node.target.elts) == 2:
            if isinstance(node.target.elts[0], ast.Name):
                index = node.target.elts[0].id if node.target.elts[0].id != "_" else None
            if isinstance(node.target.elts[1], ast.Name):
                value = node.target.elts[1].id if node.target.elts[1].id != "_" else None
                # for i, c in string yields index (int) and rune
                if iterable_type == STRING and value:
                    self._type_ctx.var_types[value] = RUNE
        # Lower body after setting up loop variable types
        body = self._lower_stmts(node.body)
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
                # Check for pos kwarg
                pos = ir.IntLit(value=0, typ=INT)
                if len(node.exc.args) > 1:
                    pos = self._lower_expr(node.exc.args[1])
                else:
                    # Check kwargs for pos
                    for kw in node.exc.keywords:
                        if kw.arg == "pos":
                            pos = self._lower_expr(kw.value)
                            break
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
