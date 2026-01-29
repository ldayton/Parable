"""Phase 3: Verify dict-based AST conforms to Tongues subset.

Validates the AST from Phase 2 against language constraints defined in spec.md.
Written in the Tongues subset (no generators, closures, lambdas, getattr).
"""

from typing import Callable

# Type alias for AST dict nodes (avoids bare dict violations)
ASTNode = dict[str, object]


class Violation:
    """A subset violation with location and diagnostic."""

    def __init__(
        self,
        lineno: int,
        col: int,
        category: str,
        message: str,
        is_warning: bool,
    ):
        self.lineno: int = lineno
        self.col: int = col
        self.category: str = category
        self.message: str = message
        self.is_warning: bool = is_warning

    def __repr__(self) -> str:
        prefix = "warning" if self.is_warning else "error"
        return (
            prefix
            + ":"
            + str(self.lineno)
            + ":"
            + str(self.col)
            + ": ["
            + self.category
            + "] "
            + self.message
        )


class VerifyResult:
    """Result of subset verification."""

    def __init__(self) -> None:
        self.violations: list[Violation] = []
        self.node_count: int = 0

    def add_error(self, lineno: int, col: int, category: str, message: str) -> None:
        self.violations.append(Violation(lineno, col, category, message, False))

    def add_warning(self, lineno: int, col: int, category: str, message: str) -> None:
        self.violations.append(Violation(lineno, col, category, message, True))

    def errors(self) -> list[Violation]:
        result: list[Violation] = []
        i = 0
        while i < len(self.violations):
            v = self.violations[i]
            if not v.is_warning:
                result.append(v)
            i += 1
        return result

    def warnings(self) -> list[Violation]:
        result: list[Violation] = []
        i = 0
        while i < len(self.violations):
            v = self.violations[i]
            if v.is_warning:
                result.append(v)
            i += 1
        return result

    def ok(self) -> bool:
        return len(self.errors()) == 0


# Allowed builtins from spec.md
ALLOWED_BUILTINS: set[str] = {
    # Math
    "abs", "min", "max", "sum", "round", "divmod", "pow",
    # Conversion
    "int", "float", "str", "bool", "bytes", "chr", "ord",
    # Collections
    "list", "dict", "set", "tuple", "frozenset", "len", "sorted",
    # Type check
    "isinstance",
    # Iteration (enumerate/zip only in for-loop headers)
    "range", "enumerate", "zip",
    # Formatting
    "repr", "ascii", "bin", "hex", "oct",
    # Boolean
    "all", "any",
    # Other
    "slice", "super", "object", "Exception", "BaseException",
    # print is handled specially
    "print",
}

# Builtins that are explicitly banned
BANNED_BUILTINS: set[str] = {
    "getattr", "setattr", "hasattr", "delattr",
    "type", "vars", "dir", "globals", "locals",
    "id", "callable", "eval", "exec", "compile", "__import__",
    "issubclass", "hash", "format", "memoryview",
    "iter", "next", "map", "filter", "reversed",
    "open", "input", "breakpoint", "help", "exit", "quit",
    "staticmethod", "classmethod", "property",
}

# Node types that are completely banned
BANNED_NODES: set[str] = {
    "AsyncFunctionDef", "AsyncFor", "AsyncWith", "Await",
    "Yield", "YieldFrom",
    "With",
    "Lambda",
    "Global", "Nonlocal",
    "TypeAlias", "TryStar",
}

# Functions that eagerly consume generator expressions
EAGER_CONSUMERS: set[str] = {
    "tuple", "list", "set", "frozenset",
    "any", "all", "sum", "min", "max", "sorted",
}

# Allowed stdlib imports (for typing and dataclasses)
# Internal imports (relative or within the project) are always allowed
ALLOWED_STDLIB: set[str] = {
    "__future__", "typing", "collections.abc", "dataclasses",
}

# Bare collection types that need type parameters
BARE_COLLECTION_TYPES: set[str] = {"list", "dict", "set", "tuple"}

# Allowed dunder methods
ALLOWED_DUNDERS: set[str] = {"__init__", "__new__", "__repr__"}


def get_children(node: ASTNode) -> list[ASTNode]:
    """Get all child nodes from a dict-based AST node."""
    children: list[ASTNode] = []
    keys = list(node.keys())
    i = 0
    while i < len(keys):
        key = keys[i]
        if key.startswith("_") or key in ("lineno", "col_offset", "end_lineno", "end_col_offset"):
            i += 1
            continue
        val = node[key]
        if isinstance(val, dict) and "_type" in val:
            children.append(val)
        elif isinstance(val, list):
            j = 0
            while j < len(val):
                item = val[j]
                if isinstance(item, dict) and "_type" in item:
                    children.append(item)
                j += 1
        i += 1
    return children


def walk(node: ASTNode, visitor: Callable[[ASTNode], None]) -> None:
    """Walk dict-based AST, calling visitor on each node."""
    visitor(node)
    children = get_children(node)
    i = 0
    while i < len(children):
        walk(children[i], visitor)
        i += 1


def is_bare_collection(annotation: ASTNode | None) -> bool:
    """Check if annotation is a bare collection type without parameters."""
    if annotation is None:
        return False
    if annotation.get("_type") != "Name":
        return False
    name_id = annotation.get("id")
    if name_id is None:
        return False
    return name_id in BARE_COLLECTION_TYPES


def is_none_constant(node: ASTNode) -> bool:
    """Check if node is None constant."""
    if node.get("_type") != "Constant":
        return False
    return node.get("value") is None


def is_obvious_literal(node: ASTNode) -> bool:
    """Check if node is a literal with obvious type."""
    if node.get("_type") != "Constant":
        return False
    val = node.get("value")
    if val is None:
        return False
    return isinstance(val, (str, int, bool, float))


def get_name_id(node: ASTNode) -> str | None:
    """Get id from Name node."""
    if node.get("_type") == "Name":
        return node.get("id")
    return None


def get_attr_name(node: ASTNode) -> str | None:
    """Get attr from Attribute node."""
    if node.get("_type") == "Attribute":
        return node.get("attr")
    return None


def collect_annotated_fields(class_node: ASTNode) -> set[str]:
    """Collect all field names with type annotations in a class (including in methods)."""
    fields: set[str] = set()
    nodes_to_visit: list[ASTNode] = [class_node]
    i = 0
    while i < len(nodes_to_visit):
        node = nodes_to_visit[i]
        node_type = node.get("_type", "")
        if node_type == "AnnAssign":
            target = node.get("target", {})
            target_type = target.get("_type", "")
            # Class-level: x: int = 0
            if target_type == "Name":
                target_id = target.get("id")
                if target_id is not None:
                    fields.add(target_id)
            # Method-level: self.x: int = 0
            if target_type == "Attribute":
                target_value = target.get("value", {})
                if get_name_id(target_value) == "self":
                    attr = target.get("attr")
                    if attr is not None:
                        fields.add(attr)
        # Add children to visit
        children = get_children(node)
        j = 0
        while j < len(children):
            nodes_to_visit.append(children[j])
            j += 1
        i += 1
    return fields


class Verifier:
    """Visitor that checks Tongues subset constraints."""

    def __init__(self) -> None:
        self.result: VerifyResult = VerifyResult()
        self.in_class: bool = False
        self.class_name: str = ""
        self.in_function: bool = False
        self.function_name: str = ""
        self.annotated_params: set[str] = set()
        self.annotated_fields: set[str] = set()
        # Context flags for eager iteration
        self.in_eager_consumer: bool = False
        self.in_for_iter: bool = False

    def error(self, node: ASTNode, category: str, message: str) -> None:
        lineno = node.get("lineno", 0)
        col = node.get("col_offset", 0)
        self.result.add_error(lineno, col, category, message)

    def warning(self, node: ASTNode, category: str, message: str) -> None:
        lineno = node.get("lineno", 0)
        col = node.get("col_offset", 0)
        self.result.add_warning(lineno, col, category, message)

    def visit(self, node: ASTNode) -> None:
        """Dispatch to appropriate visit method."""
        self.result.node_count += 1
        node_type = node.get("_type", "")
        # Check banned nodes first
        if node_type in BANNED_NODES:
            self.visit_banned_node(node, node_type)
            return
        # Explicit dispatch (self-hosting: no getattr)
        if node_type == "Module":
            self.visit_Module(node)
        elif node_type == "FunctionDef":
            self.visit_FunctionDef(node)
        elif node_type == "ClassDef":
            self.visit_ClassDef(node)
        elif node_type == "Call":
            self.visit_Call(node)
        elif node_type == "Compare":
            self.visit_Compare(node)
        elif node_type == "BoolOp":
            self.visit_BoolOp(node)
        elif node_type == "Assign":
            self.visit_Assign(node)
        elif node_type == "AnnAssign":
            self.visit_AnnAssign(node)
        elif node_type == "For":
            self.visit_For(node)
        elif node_type == "While":
            self.visit_While(node)
        elif node_type == "Try":
            self.visit_Try(node)
        elif node_type == "ExceptHandler":
            self.visit_ExceptHandler(node)
        elif node_type == "Import":
            self.visit_Import(node)
        elif node_type == "ImportFrom":
            self.visit_ImportFrom(node)
        elif node_type == "Attribute":
            self.visit_Attribute(node)
        elif node_type == "BinOp":
            self.visit_BinOp(node)
        elif node_type == "Delete":
            self.visit_Delete(node)
        elif node_type == "JoinedStr":
            self.visit_JoinedStr(node)
        elif node_type == "FormattedValue":
            self.visit_FormattedValue(node)
        elif node_type == "GeneratorExp":
            self.visit_GeneratorExp(node)
        elif node_type == "Match":
            pass
        else:
            # Unknown node types get a warning
            if node_type and not self.is_known_node(node_type):
                self.warning(node, "syntax", "unknown node type: " + node_type)
            # Still traverse children for all nodes
            children = get_children(node)
            i = 0
            while i < len(children):
                self.visit(children[i])
                i += 1

    def is_known_node(self, node_type: str) -> bool:
        """Check if node type is recognized."""
        known: set[str] = {
            "Module", "FunctionDef", "ClassDef", "Return", "Assign", "AnnAssign",
            "AugAssign", "For", "While", "If", "Raise", "Try", "ExceptHandler",
            "Import", "ImportFrom", "Pass", "Break", "Continue", "Expr",
            "BoolOp", "BinOp", "UnaryOp", "IfExp", "Dict", "Set", "ListComp",
            "SetComp", "DictComp", "GeneratorExp", "Compare", "Call", "JoinedStr", "FormattedValue",
            "Constant", "Attribute", "Subscript", "Starred", "Name", "List",
            "Tuple", "Slice", "And", "Or", "Add", "Sub", "Mult", "Div",
            "Mod", "Pow", "LShift", "RShift", "BitOr", "BitXor", "BitAnd",
            "FloorDiv", "Invert", "Not", "UAdd", "USub", "Eq", "NotEq",
            "Lt", "LtE", "Gt", "GtE", "Is", "IsNot", "In", "NotIn",
            "arg", "arguments", "keyword", "alias", "Match", "match_case",
            "MatchValue", "MatchSingleton", "MatchSequence", "MatchMapping",
            "MatchClass", "MatchStar", "MatchAs", "MatchOr", "Assert",
        }
        return node_type in known

    def visit_banned_node(self, node: ASTNode, node_type: str) -> None:
        """Report error for banned node type."""
        category = "syntax"
        message = node_type + " is not allowed"
        if node_type in ("AsyncFunctionDef", "AsyncFor", "AsyncWith", "Await"):
            category = "async"
            message = "async/await is not allowed"
        elif node_type in ("Yield", "YieldFrom", "GeneratorExp"):
            category = "generator"
            message = "generators are not allowed"
        elif node_type == "With":
            category = "control"
            message = "with statement: use try/finally instead"
        elif node_type == "Lambda":
            category = "function"
            message = "lambda: use named function instead"
        elif node_type in ("Global", "Nonlocal"):
            category = "control"
            message = node_type.lower() + ": pass as parameter instead"
        self.error(node, category, message)

    def visit_Module(self, node: ASTNode) -> None:
        """Visit module - just traverse body."""
        body = node.get("body", [])
        i = 0
        while i < len(body):
            self.visit(body[i])
            i += 1

    def visit_FunctionDef(self, node: ASTNode) -> None:
        """Check function definition constraints."""
        name = node.get("name", "")
        # Check decorators
        decorators = node.get("decorator_list", [])
        i = 0
        while i < len(decorators):
            dec = decorators[i]
            dec_name = get_name_id(dec)
            if dec_name is None:
                dec_name = get_attr_name(dec)
            if dec_name == "staticmethod":
                self.error(node, "function", "@staticmethod: use module-level function")
            elif dec_name == "classmethod":
                self.error(node, "function", "@classmethod: use module-level function")
            elif dec_name == "property":
                self.error(node, "function", "@property: use explicit getter method")
            else:
                self.error(node, "function", "decorators are not allowed")
            i += 1
        # Check nested function
        if self.in_function:
            self.error(
                node, "function",
                "nested function '" + name + "': define at module level"
            )
        # Check dunder methods
        if name.startswith("__") and name.endswith("__"):
            if name not in ALLOWED_DUNDERS:
                self.error(
                    node, "function",
                    "dunder method " + name + ": only __init__/__new__/__repr__ allowed"
                )
        # Check **kwargs
        args_node = node.get("args", {})
        if args_node.get("kwarg") is not None:
            self.error(node, "function", "**kwargs: use explicit parameters")
        # Check return type (except __init__, __new__)
        if name not in ("__init__", "__new__"):
            if node.get("returns") is None:
                self.error(node, "types", "missing return type: def " + name + "() -> ...")
        # Check return type bare collection
        returns = node.get("returns")
        if returns is not None and is_bare_collection(returns):
            self.error(
                node, "types",
                "bare " + returns.get("id", "") + ": " + name + "() return needs type parameter"
            )
        # Check parameter types
        args_list = args_node.get("args", [])
        old_annotated = self.annotated_params
        self.annotated_params = set()
        j = 0
        while j < len(args_list):
            arg = args_list[j]
            arg_name = arg.get("arg", "")
            annotation = arg.get("annotation")
            # Skip self/cls first param
            if j == 0 and arg_name in ("self", "cls"):
                j += 1
                continue
            if annotation is None:
                self.error(node, "types", "missing param type: " + arg_name + " in " + name + "()")
            else:
                self.annotated_params.add(arg_name)
                if is_bare_collection(annotation):
                    self.error(
                        node, "types",
                        "bare " + annotation.get("id", "") + ": " + arg_name + " needs type parameter"
                    )
            j += 1
        # Check mutable defaults
        defaults = args_node.get("defaults", [])
        kw_defaults = args_node.get("kw_defaults", [])
        all_defaults: list[ASTNode] = []
        k = 0
        while k < len(defaults):
            all_defaults.append(defaults[k])
            k += 1
        k = 0
        while k < len(kw_defaults):
            d = kw_defaults[k]
            if d is not None:
                all_defaults.append(d)
            k += 1
        k = 0
        while k < len(all_defaults):
            d = all_defaults[k]
            d_type = d.get("_type", "")
            if d_type in ("List", "Dict", "Set"):
                self.error(node, "function", "mutable default argument: use None and initialize in body")
                break
            k += 1
        # Visit body
        old_in_function = self.in_function
        old_function_name = self.function_name
        self.in_function = True
        self.function_name = name
        body = node.get("body", [])
        m = 0
        while m < len(body):
            self.visit(body[m])
            m += 1
        self.in_function = old_in_function
        self.function_name = old_function_name
        self.annotated_params = old_annotated

    def visit_ClassDef(self, node: ASTNode) -> None:
        """Check class definition constraints."""
        name = node.get("name", "")
        # Check decorators - only @dataclass (no arguments) is allowed
        decorators = node.get("decorator_list", [])
        if isinstance(decorators, list):
            i = 0
            while i < len(decorators):
                dec = decorators[i]
                if isinstance(dec, dict):
                    dec_type = dec.get("_type", "")
                    if dec_type == "Name" and dec.get("id") == "dataclass":
                        pass  # @dataclass with no arguments is allowed
                    elif dec_type == "Call":
                        func = dec.get("func")
                        if isinstance(func, dict) and func.get("id") == "dataclass":
                            self.error(node, "class", "@dataclass arguments not allowed")
                        else:
                            self.error(node, "class", "class decorator not allowed")
                    else:
                        self.error(node, "class", "class decorator not allowed")
                i += 1
        # Check nested class
        if self.in_class:
            self.error(node, "class", "nested class: define at module level")
        # Check multiple inheritance (Exception doesn't count)
        bases = node.get("bases", [])
        real_bases: list[ASTNode] = []
        j = 0
        while j < len(bases):
            b = bases[j]
            b_name = get_name_id(b)
            if b_name != "Exception":
                real_bases.append(b)
            j += 1
        if len(real_bases) > 1:
            self.error(node, "class", "multiple inheritance: use single base class")
        # Collect annotated fields (walk entire class including method bodies)
        old_fields = self.annotated_fields
        self.annotated_fields = collect_annotated_fields(node)
        body = node.get("body", [])
        # Visit body
        old_in_class = self.in_class
        old_class_name = self.class_name
        self.in_class = True
        self.class_name = name
        m = 0
        while m < len(body):
            child = body[m]
            # Check nested class
            if child.get("_type") == "ClassDef":
                self.error(child, "class", "nested class: define at module level")
            self.visit(child)
            m += 1
        self.in_class = old_in_class
        self.class_name = old_class_name
        self.annotated_fields = old_fields

    def visit_Call(self, node: ASTNode) -> None:
        """Check function call constraints."""
        func = node.get("func", {})
        func_name = get_name_id(func)
        # Check banned builtins
        if func_name is not None and func_name in BANNED_BUILTINS:
            self.error(node, "builtin", func_name + "() is not allowed")
        # Check enumerate/zip only allowed in for-loop iter
        if func_name in ("enumerate", "zip") and not self.in_for_iter:
            self.error(node, "builtin", func_name + "() only allowed in for-loop header")
        # Check if this is an eager consumer (for generator expressions)
        is_eager = func_name is not None and func_name in EAGER_CONSUMERS
        # Also check for str.join method call
        if not is_eager and isinstance(func, dict) and func.get("_type") == "Attribute":
            if func.get("attr") == "join":
                is_eager = True
        # Check *args in call
        args = node.get("args", [])
        i = 0
        while i < len(args):
            arg = args[i]
            if arg.get("_type") == "Starred":
                self.error(node, "expression", "*args in call: unpack arguments explicitly")
                break
            i += 1
        # Check **kwargs in call
        keywords = node.get("keywords", [])
        j = 0
        while j < len(keywords):
            kw = keywords[j]
            if kw.get("arg") is None:
                self.error(node, "expression", "**kwargs in call: pass arguments explicitly")
                break
            j += 1
        # Visit children
        self.visit(func)
        # Set eager consumer context when visiting args
        old_in_eager = self.in_eager_consumer
        if is_eager:
            self.in_eager_consumer = True
        k = 0
        while k < len(args):
            self.visit(args[k])
            k += 1
        self.in_eager_consumer = old_in_eager
        m = 0
        while m < len(keywords):
            kw = keywords[m]
            val = kw.get("value")
            if val is not None:
                self.visit(val)
            m += 1

    def visit_Compare(self, node: ASTNode) -> None:
        """Check comparison constraints."""
        ops = node.get("ops", [])
        comparators = node.get("comparators", [])
        # Check chained comparison
        if len(ops) > 1:
            self.error(node, "expression", "chained comparison: use 'and' explicitly")
        # Check is/is not with non-None
        left = node.get("left", {})
        i = 0
        while i < len(ops):
            op = ops[i]
            comparator = comparators[i]
            op_type = op.get("_type", "")
            if op_type in ("Is", "IsNot"):
                left_is_none = is_none_constant(left)
                right_is_none = is_none_constant(comparator)
                if not left_is_none and not right_is_none:
                    self.error(node, "reflection", "is/is not: only use with None")
            left = comparator
            i += 1
        # Visit children
        self.visit(node.get("left", {}))
        j = 0
        while j < len(comparators):
            self.visit(comparators[j])
            j += 1

    def visit_BoolOp(self, node: ASTNode) -> None:
        """Check boolean operation constraints."""
        op = node.get("op", {})
        op_type = op.get("_type", "")
        values = node.get("values", [])
        # Check or-default pattern: x or []
        if op_type == "Or":
            i = 1
            while i < len(values):
                val = values[i]
                val_type = val.get("_type", "")
                if val_type in ("List", "Dict", "Set"):
                    self.error(node, "expression", "or-default: use 'if x is None: x = ...' instead")
                if val_type == "Constant":
                    v = val.get("value")
                    if v in (0, "", None, False):
                        self.error(node, "expression", "or-default: use 'if x is None: x = ...' instead")
                i += 1
        # Visit children
        j = 0
        while j < len(values):
            self.visit(values[j])
            j += 1

    def visit_Assign(self, node: ASTNode) -> None:
        """Check assignment constraints."""
        targets = node.get("targets", [])
        value = node.get("value", {})
        # Check tuple unpack from variable
        if len(targets) == 1:
            target = targets[0]
            if target.get("_type") == "Tuple" and value.get("_type") == "Name":
                self.error(node, "expression", "tuple unpack from variable: unpack directly from call")
        # Check unannotated field assigns in class
        if self.in_class:
            i = 0
            while i < len(targets):
                target = targets[i]
                if target.get("_type") == "Attribute":
                    target_value = target.get("value", {})
                    if get_name_id(target_value) == "self":
                        field_name = target.get("attr", "")
                        if field_name not in self.annotated_fields:
                            # Skip if value is annotated param
                            val_name = get_name_id(value)
                            if val_name is not None and val_name in self.annotated_params:
                                self.annotated_fields.add(field_name)
                            elif is_obvious_literal(value):
                                self.annotated_fields.add(field_name)
                            else:
                                self.error(
                                    node, "types",
                                    "unannotated field: self." + field_name + " needs type annotation"
                                )
                                self.annotated_fields.add(field_name)
                i += 1
        # Visit children
        j = 0
        while j < len(targets):
            self.visit(targets[j])
            j += 1
        self.visit(value)

    def visit_AnnAssign(self, node: ASTNode) -> None:
        """Check annotated assignment constraints."""
        annotation = node.get("annotation")
        target = node.get("target", {})
        # Check bare collection
        if is_bare_collection(annotation):
            target_name = target.get("id", "?")
            self.error(
                node, "types",
                "bare " + annotation.get("id", "") + ": " + target_name + " needs type parameter"
            )
        # Visit children
        self.visit(target)
        if annotation is not None:
            self.visit(annotation)
        value = node.get("value")
        if value is not None:
            self.visit(value)

    def visit_For(self, node: ASTNode) -> None:
        """Check for loop constraints."""
        # Check loop else
        orelse = node.get("orelse", [])
        if len(orelse) > 0:
            self.error(node, "control", "loop else: use flag variable instead")
        # Visit children
        target = node.get("target")
        if target is not None:
            self.visit(target)
        iter_node = node.get("iter")
        if iter_node is not None:
            # Set context flag for enumerate/zip in for-loop iter
            old_in_for_iter = self.in_for_iter
            self.in_for_iter = True
            self.visit(iter_node)
            self.in_for_iter = old_in_for_iter
        body = node.get("body", [])
        i = 0
        while i < len(body):
            self.visit(body[i])
            i += 1
        j = 0
        while j < len(orelse):
            self.visit(orelse[j])
            j += 1

    def visit_While(self, node: ASTNode) -> None:
        """Check while loop constraints."""
        # Check loop else
        orelse = node.get("orelse", [])
        if len(orelse) > 0:
            self.error(node, "control", "loop else: use flag variable instead")
        # Visit children
        test = node.get("test")
        if test is not None:
            self.visit(test)
        body = node.get("body", [])
        i = 0
        while i < len(body):
            self.visit(body[i])
            i += 1
        j = 0
        while j < len(orelse):
            self.visit(orelse[j])
            j += 1

    def visit_Try(self, node: ASTNode) -> None:
        """Check try statement constraints."""
        # Check try else
        orelse = node.get("orelse", [])
        if len(orelse) > 0:
            self.error(node, "control", "try else: move else code after try block")
        # Visit children
        body = node.get("body", [])
        i = 0
        while i < len(body):
            self.visit(body[i])
            i += 1
        handlers = node.get("handlers", [])
        j = 0
        while j < len(handlers):
            self.visit(handlers[j])
            j += 1
        k = 0
        while k < len(orelse):
            self.visit(orelse[k])
            k += 1
        finalbody = node.get("finalbody", [])
        m = 0
        while m < len(finalbody):
            self.visit(finalbody[m])
            m += 1

    def visit_ExceptHandler(self, node: ASTNode) -> None:
        """Check except handler constraints."""
        # Check bare except
        exc_type = node.get("type")
        if exc_type is None:
            self.error(node, "control", "bare except: specify exception type")
        # Visit children
        if exc_type is not None:
            self.visit(exc_type)
        body = node.get("body", [])
        i = 0
        while i < len(body):
            self.visit(body[i])
            i += 1

    def visit_Import(self, node: ASTNode) -> None:
        """Check import constraints."""
        self.error(node, "import", "import: not allowed, code must be self-contained")

    def visit_ImportFrom(self, node: ASTNode) -> None:
        """Check from import constraints.

        Relative imports and imports within the project are allowed.
        Only typing-related stdlib imports are allowed for external modules.
        """
        level = node.get("level", 0)
        if level > 0:
            return
        module = node.get("module")
        if module is None:
            return
        top_module = module.split(".")[0]
        if top_module in ALLOWED_STDLIB:
            return

    def visit_Attribute(self, node: ASTNode) -> None:
        """Check attribute access constraints."""
        attr = node.get("attr", "")
        # Check __class__
        if attr == "__class__":
            self.error(node, "reflection", "__class__: use isinstance() instead")
        # Check __dict__
        if attr == "__dict__":
            self.error(node, "reflection", "__dict__: direct attribute access only")
        # Visit value
        value = node.get("value")
        if value is not None:
            self.visit(value)

    def visit_BinOp(self, node: ASTNode) -> None:
        """Visit binary operation children."""
        # Visit children
        left = node.get("left")
        right = node.get("right")
        if left is not None:
            self.visit(left)
        if right is not None:
            self.visit(right)

    def visit_Delete(self, node: ASTNode) -> None:
        """Check delete statement - banned."""
        self.error(node, "syntax", "del: reassign or let variable go out of scope")

    def visit_JoinedStr(self, node: ASTNode) -> None:
        """Visit f-string, check children."""
        values = node.get("values", [])
        i = 0
        while i < len(values):
            self.visit(values[i])
            i += 1

    def visit_FormattedValue(self, node: ASTNode) -> None:
        """Check f-string replacement field: {expr} only, no !conv or :spec."""
        conversion = node.get("conversion", -1)
        if conversion != -1:
            self.error(node, "syntax", "f-string !conversion not supported")
        format_spec = node.get("format_spec")
        if format_spec is not None:
            self.error(node, "syntax", "f-string :format_spec not supported")
        value = node.get("value")
        if value is not None:
            self.visit(value)

    def visit_GeneratorExp(self, node: ASTNode) -> None:
        """Check generator expression - only allowed in eager consumer context."""
        if not self.in_eager_consumer:
            self.error(node, "generator", "generator expression only allowed in eager consumer (tuple, list, any, all, etc.)")
        # Visit children (elt, generators)
        elt = node.get("elt")
        if elt is not None:
            self.visit(elt)
        generators = node.get("generators", [])
        i = 0
        while i < len(generators):
            gen = generators[i]
            if isinstance(gen, dict):
                target = gen.get("target")
                if target is not None:
                    self.visit(target)
                iter_node = gen.get("iter")
                if iter_node is not None:
                    self.visit(iter_node)
                ifs = gen.get("ifs", [])
                j = 0
                while j < len(ifs):
                    self.visit(ifs[j])
                    j += 1
            i += 1


def verify(ast_dict: ASTNode) -> VerifyResult:
    """Verify dict-based AST conforms to Tongues subset.

    Args:
        ast_dict: Dict-based AST from parse.py

    Returns:
        VerifyResult with any violations found
    """
    verifier = Verifier()
    verifier.visit(ast_dict)
    return verifier.result


class ImportInfo:
    """Information about an import statement."""

    def __init__(self, module: str, level: int, lineno: int, col: int):
        self.module: str = module
        self.level: int = level
        self.lineno: int = lineno
        self.col: int = col


def extract_imports(ast_dict: ASTNode) -> list[ImportInfo]:
    """Extract all from-imports from an AST."""
    result: list[ImportInfo] = []
    body = ast_dict.get("body", [])
    if not isinstance(body, list):
        return result
    i = 0
    while i < len(body):
        node = body[i]
        if isinstance(node, dict) and node.get("_type") == "ImportFrom":
            module = node.get("module")
            if module is None:
                module = ""
            level = node.get("level", 0)
            if not isinstance(level, int):
                level = 0
            lineno = node.get("lineno", 1)
            if not isinstance(lineno, int):
                lineno = 1
            col = node.get("col_offset", 0)
            if not isinstance(col, int):
                col = 0
            if module == "" and level > 0:
                # from . import X, Y - each name is a module
                names = node.get("names", [])
                j = 0
                while j < len(names):
                    name_node = names[j]
                    if isinstance(name_node, dict):
                        name = name_node.get("name", "")
                        if name != "" and name != "*":
                            result.append(ImportInfo(name, level, lineno, col))
                    j += 1
            else:
                result.append(ImportInfo(module, level, lineno, col))
        i += 1
    return result


class ProjectVerifyResult:
    """Result of project-level verification."""

    def __init__(self) -> None:
        self.file_results: dict[str, VerifyResult] = {}
        self.unresolved_imports: list[tuple[str, ImportInfo]] = []

    def errors(self) -> list[str]:
        """Get all errors as formatted strings."""
        result: list[str] = []
        files = sorted(self.file_results.keys())
        i = 0
        while i < len(files):
            f = files[i]
            file_result = self.file_results[f]
            errs = file_result.errors()
            j = 0
            while j < len(errs):
                result.append(f + ": " + str(errs[j]))
                j += 1
            i += 1
        j = 0
        while j < len(self.unresolved_imports):
            file_path, imp = self.unresolved_imports[j]
            msg = file_path + ":" + str(imp.lineno) + ":" + str(imp.col)
            msg = msg + ": [import] unresolved import: " + imp.module
            result.append(msg)
            j += 1
        return result

    def has_errors(self) -> bool:
        """Check if there are any errors."""
        if len(self.unresolved_imports) > 0:
            return True
        files = list(self.file_results.keys())
        i = 0
        while i < len(files):
            if self.file_results[files[i]].has_errors():
                return True
            i += 1
        return False
