"""Phase 4: Scope analysis and name binding.

Builds a symbol table mapping names to their declarations. Validates that all
referenced names resolve. Since Phase 3 guarantees no nested functions and no
global/nonlocal, scoping is simple: local → module → builtin.

Written in the Tongues subset (no generators, closures, lambdas, getattr).
"""

from typing import Callable

# Type alias for AST dict nodes
ASTNode = dict[str, object]


# Allowed builtins (copied from subset.py)
ALLOWED_BUILTINS: set[str] = {
    # Math
    "abs", "min", "max", "sum", "round", "divmod", "pow",
    # Conversion
    "int", "float", "str", "bool", "bytes", "bytearray", "chr", "ord", "complex",
    # Collections
    "list", "dict", "set", "tuple", "frozenset", "len", "sorted",
    # Type check
    "isinstance",
    # Iteration
    "range", "enumerate", "zip",
    # Formatting
    "repr", "ascii", "bin", "hex", "oct",
    # Boolean
    "all", "any",
    # Other
    "slice", "super", "object", "Exception", "BaseException", "NotImplementedError",
    "ValueError", "TypeError", "KeyError", "IndexError", "AttributeError", "RuntimeError",
    # print is handled specially
    "print",
}


class NameInfo:
    """Information about a declared name."""

    def __init__(
        self,
        name: str,
        kind: str,
        scope: str,
        lineno: int,
        col: int,
        decl_class: str,
        decl_func: str,
    ):
        self.name: str = name
        self.kind: str = kind  # "class" | "function" | "variable" | "parameter" | "field" | "builtin" | "constant"
        self.scope: str = scope  # "builtin" | "module" | "class" | "local"
        self.lineno: int = lineno
        self.col: int = col
        self.decl_class: str = decl_class  # Class name if field/method
        self.decl_func: str = decl_func  # Function name if local/param

    def __repr__(self) -> str:
        return "NameInfo(" + self.name + ", " + self.kind + ", " + self.scope + ")"


class NameTable:
    """Symbol table for resolved names."""

    def __init__(self) -> None:
        self.module_names: dict[str, NameInfo] = {}
        self.class_names: dict[str, dict[str, NameInfo]] = {}
        self.local_names: dict[tuple[str, str], dict[str, NameInfo]] = {}

    def add_module(self, info: NameInfo) -> None:
        self.module_names[info.name] = info

    def add_class_member(self, class_name: str, info: NameInfo) -> None:
        if class_name not in self.class_names:
            self.class_names[class_name] = {}
        self.class_names[class_name][info.name] = info

    def add_local(self, class_name: str, func_name: str, info: NameInfo) -> None:
        key: tuple[str, str] = (class_name, func_name)
        if key not in self.local_names:
            self.local_names[key] = {}
        self.local_names[key][info.name] = info

    def get_module(self, name: str) -> NameInfo | None:
        return self.module_names.get(name)

    def get_class_member(self, class_name: str, name: str) -> NameInfo | None:
        class_members = self.class_names.get(class_name)
        if class_members is None:
            return None
        return class_members.get(name)

    def get_local(self, class_name: str, func_name: str, name: str) -> NameInfo | None:
        key: tuple[str, str] = (class_name, func_name)
        local_scope = self.local_names.get(key)
        if local_scope is None:
            return None
        return local_scope.get(name)


class NameViolation:
    """A name resolution error with location."""

    def __init__(
        self,
        lineno: int,
        col: int,
        category: str,
        message: str,
    ):
        self.lineno: int = lineno
        self.col: int = col
        self.category: str = category
        self.message: str = message

    def __repr__(self) -> str:
        return (
            "error:"
            + str(self.lineno)
            + ":"
            + str(self.col)
            + ": ["
            + self.category
            + "] "
            + self.message
        )


class NameResult:
    """Result of name resolution."""

    def __init__(self) -> None:
        self.table: NameTable = NameTable()
        self.violations: list[NameViolation] = []
        self.warnings: list[NameViolation] = []

    def add_error(self, lineno: int, col: int, category: str, message: str) -> None:
        self.violations.append(NameViolation(lineno, col, category, message))

    def add_warning(self, lineno: int, col: int, category: str, message: str) -> None:
        self.warnings.append(NameViolation(lineno, col, category, message))

    def errors(self) -> list[NameViolation]:
        return self.violations

    def ok(self) -> bool:
        return len(self.violations) == 0


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


def get_name_id(node: ASTNode) -> str | None:
    """Get id from Name node."""
    if node.get("_type") == "Name":
        return node.get("id")
    return None


def is_all_caps(name: str) -> bool:
    """Check if name is ALL_CAPS (constant convention)."""
    if len(name) == 0:
        return False
    i = 0
    while i < len(name):
        c = name[i]
        if c != "_" and not c.isupper() and not c.isdigit():
            return False
        i += 1
    # Must have at least one letter
    j = 0
    has_letter = False
    while j < len(name):
        if name[j].isupper():
            has_letter = True
            break
        j += 1
    return has_letter


def is_type_alias(name: str, value: dict[str, object]) -> bool:
    """Check if this looks like a type alias (PascalCase = type expression)."""
    if len(name) == 0:
        return False
    # Must start with uppercase
    if not name[0].isupper():
        return False
    # Value should be a Subscript (like dict[str, object]) or Name (like int)
    value_type = value.get("_type", "")
    if value_type == "Subscript" or value_type == "Name" or value_type == "BinOp":
        return True
    return False


class NameResolver:
    """Resolves names in a dict-based AST."""

    def __init__(self) -> None:
        self.result: NameResult = NameResult()
        self.current_class: str = ""
        self.current_func: str = ""

    def error(self, node: ASTNode, category: str, message: str) -> None:
        lineno = node.get("lineno", 0)
        col = node.get("col_offset", 0)
        self.result.add_error(lineno, col, category, message)

    def warning(self, node: ASTNode, category: str, message: str) -> None:
        lineno = node.get("lineno", 0)
        col = node.get("col_offset", 0)
        self.result.add_warning(lineno, col, category, message)

    def resolve(self, ast_dict: ASTNode) -> NameResult:
        """Main entry point: run all passes and return result."""
        self.pass1_module_names(ast_dict)
        self.pass2_class_names(ast_dict)
        self.pass3_locals_and_refs(ast_dict)
        return self.result

    def pass1_module_names(self, ast_dict: ASTNode) -> None:
        """Pass 1: Collect module-level names (classes, functions, constants)."""
        body = ast_dict.get("body", [])
        i = 0
        while i < len(body):
            stmt = body[i]
            node_type = stmt.get("_type", "")
            lineno = stmt.get("lineno", 0)
            col = stmt.get("col_offset", 0)
            if node_type == "ClassDef":
                name = stmt.get("name", "")
                existing = self.result.table.get_module(name)
                if existing is not None:
                    self.error(stmt, "redefinition", "'" + name + "' already defined at line " + str(existing.lineno))
                else:
                    info = NameInfo(name, "class", "module", lineno, col, "", "")
                    self.result.table.add_module(info)
            elif node_type == "FunctionDef":
                name = stmt.get("name", "")
                existing = self.result.table.get_module(name)
                if existing is not None:
                    self.error(stmt, "redefinition", "'" + name + "' already defined at line " + str(existing.lineno))
                else:
                    info = NameInfo(name, "function", "module", lineno, col, "", "")
                    self.result.table.add_module(info)
            elif node_type == "Assign":
                targets = stmt.get("targets", [])
                value = stmt.get("value", {})
                j = 0
                while j < len(targets):
                    target = targets[j]
                    if target.get("_type") == "Name":
                        name = target.get("id", "")
                        existing = self.result.table.get_module(name)
                        if existing is None:
                            if is_all_caps(name):
                                info = NameInfo(name, "constant", "module", lineno, col, "", "")
                                self.result.table.add_module(info)
                            elif is_type_alias(name, value):
                                info = NameInfo(name, "type_alias", "module", lineno, col, "", "")
                                self.result.table.add_module(info)
                    j += 1
            elif node_type == "AnnAssign":
                target = stmt.get("target", {})
                if target.get("_type") == "Name":
                    name = target.get("id", "")
                    existing = self.result.table.get_module(name)
                    if existing is None:
                        kind = "constant" if is_all_caps(name) else "variable"
                        info = NameInfo(name, kind, "module", lineno, col, "", "")
                        self.result.table.add_module(info)
            elif node_type == "ImportFrom":
                # Register imported names in module scope
                names_list = stmt.get("names", [])
                j = 0
                while j < len(names_list):
                    alias = names_list[j]
                    if isinstance(alias, dict):
                        # Use asname if present, otherwise use name
                        asname = alias.get("asname")
                        import_name = alias.get("name", "")
                        bound_name = asname if asname is not None else import_name
                        if bound_name != "" and bound_name != "*":
                            info = NameInfo(bound_name, "import", "module", lineno, col, "", "")
                            self.result.table.add_module(info)
                    j += 1
            elif node_type == "If":
                # Handle TYPE_CHECKING blocks - imports inside are module-level
                test = stmt.get("test", {})
                if test.get("_type") == "Name" and test.get("id") == "TYPE_CHECKING":
                    if_body = stmt.get("body", [])
                    j = 0
                    while j < len(if_body):
                        if_stmt = if_body[j]
                        if if_stmt.get("_type") == "ImportFrom":
                            if_names = if_stmt.get("names", [])
                            k = 0
                            while k < len(if_names):
                                alias = if_names[k]
                                if isinstance(alias, dict):
                                    asname = alias.get("asname")
                                    import_name = alias.get("name", "")
                                    bound_name = asname if asname is not None else import_name
                                    if bound_name != "" and bound_name != "*":
                                        if_lineno = if_stmt.get("lineno", 0)
                                        if_col = if_stmt.get("col_offset", 0)
                                        info = NameInfo(bound_name, "import", "module", if_lineno, if_col, "", "")
                                        self.result.table.add_module(info)
                                k += 1
                        j += 1
            i += 1

    def pass2_class_names(self, ast_dict: ASTNode) -> None:
        """Pass 2: Collect class-level names (methods, fields)."""
        body = ast_dict.get("body", [])
        i = 0
        while i < len(body):
            stmt = body[i]
            if stmt.get("_type") == "ClassDef":
                self.collect_class_members(stmt)
            i += 1

    def collect_class_members(self, class_node: ASTNode) -> None:
        """Collect all members of a class."""
        class_name = class_node.get("name", "")
        body = class_node.get("body", [])
        # First pass: collect methods and annotated fields
        i = 0
        while i < len(body):
            stmt = body[i]
            node_type = stmt.get("_type", "")
            lineno = stmt.get("lineno", 0)
            col = stmt.get("col_offset", 0)
            if node_type == "FunctionDef":
                name = stmt.get("name", "")
                info = NameInfo(name, "function", "class", lineno, col, class_name, "")
                self.result.table.add_class_member(class_name, info)
            elif node_type == "AnnAssign":
                target = stmt.get("target", {})
                if target.get("_type") == "Name":
                    name = target.get("id", "")
                    info = NameInfo(name, "field", "class", lineno, col, class_name, "")
                    self.result.table.add_class_member(class_name, info)
            i += 1
        # Second pass: collect self.x assignments in __init__
        j = 0
        while j < len(body):
            stmt = body[j]
            if stmt.get("_type") == "FunctionDef" and stmt.get("name") == "__init__":
                self.collect_init_fields(class_name, stmt)
            j += 1

    def collect_init_fields(self, class_name: str, init_node: ASTNode) -> None:
        """Collect self.x = ... fields from __init__."""
        body = init_node.get("body", [])
        nodes_to_visit: list[ASTNode] = []
        i = 0
        while i < len(body):
            nodes_to_visit.append(body[i])
            i += 1
        j = 0
        while j < len(nodes_to_visit):
            node = nodes_to_visit[j]
            node_type = node.get("_type", "")
            if node_type == "Assign":
                targets = node.get("targets", [])
                k = 0
                while k < len(targets):
                    target = targets[k]
                    if target.get("_type") == "Attribute":
                        value_node = target.get("value", {})
                        if get_name_id(value_node) == "self":
                            attr = target.get("attr", "")
                            existing = self.result.table.get_class_member(class_name, attr)
                            if existing is None:
                                lineno = node.get("lineno", 0)
                                col = node.get("col_offset", 0)
                                info = NameInfo(attr, "field", "class", lineno, col, class_name, "")
                                self.result.table.add_class_member(class_name, info)
                    k += 1
            elif node_type == "AnnAssign":
                target = node.get("target", {})
                if target.get("_type") == "Attribute":
                    value_node = target.get("value", {})
                    if get_name_id(value_node) == "self":
                        attr = target.get("attr", "")
                        existing = self.result.table.get_class_member(class_name, attr)
                        if existing is None:
                            lineno = node.get("lineno", 0)
                            col = node.get("col_offset", 0)
                            info = NameInfo(attr, "field", "class", lineno, col, class_name, "")
                            self.result.table.add_class_member(class_name, info)
            # Add children for If, While, etc.
            children = get_children(node)
            m = 0
            while m < len(children):
                child = children[m]
                child_type = child.get("_type", "")
                # Skip nested functions (shouldn't exist per Phase 3)
                if child_type != "FunctionDef":
                    nodes_to_visit.append(child)
                m += 1
            j += 1

    def pass3_locals_and_refs(self, ast_dict: ASTNode) -> None:
        """Pass 3: Collect locals and resolve all name references."""
        body = ast_dict.get("body", [])
        i = 0
        while i < len(body):
            stmt = body[i]
            node_type = stmt.get("_type", "")
            if node_type == "FunctionDef":
                self.process_function(stmt, "", stmt.get("name", ""))
            elif node_type == "ClassDef":
                self.process_class(stmt)
            i += 1

    def process_class(self, class_node: ASTNode) -> None:
        """Process all methods in a class."""
        class_name = class_node.get("name", "")
        body = class_node.get("body", [])
        i = 0
        while i < len(body):
            stmt = body[i]
            if stmt.get("_type") == "FunctionDef":
                func_name = stmt.get("name", "")
                self.process_function(stmt, class_name, func_name)
            i += 1

    def process_function(self, func_node: ASTNode, class_name: str, func_name: str) -> None:
        """Process a function: collect params/locals, then resolve references."""
        self.current_class = class_name
        self.current_func = func_name
        # Collect parameters
        args_node = func_node.get("args", {})
        args_list = args_node.get("args", [])
        i = 0
        while i < len(args_list):
            arg = args_list[i]
            arg_name = arg.get("arg", "")
            lineno = arg.get("lineno", 0)
            col = arg.get("col_offset", 0)
            # Add self/cls without shadowing warning
            if i == 0 and arg_name in ("self", "cls"):
                info = NameInfo(arg_name, "parameter", "local", lineno, col, class_name, func_name)
                self.result.table.add_local(class_name, func_name, info)
                i += 1
                continue
            # Warn if parameter shadows a builtin
            if arg_name in ALLOWED_BUILTINS:
                self.warning(arg, "shadowing", "parameter '" + arg_name + "' shadows builtin")
            info = NameInfo(arg_name, "parameter", "local", lineno, col, class_name, func_name)
            self.result.table.add_local(class_name, func_name, info)
            i += 1
        # Collect local variables from body
        body = func_node.get("body", [])
        self.collect_locals_from_body(body, class_name, func_name)
        # Resolve all Name references
        self.resolve_references_in_body(body, class_name, func_name)
        self.current_class = ""
        self.current_func = ""

    def collect_locals_from_body(self, body: list[ASTNode], class_name: str, func_name: str) -> None:
        """Collect local variable names from function body."""
        nodes_to_visit: list[ASTNode] = []
        i = 0
        while i < len(body):
            nodes_to_visit.append(body[i])
            i += 1
        j = 0
        while j < len(nodes_to_visit):
            node = nodes_to_visit[j]
            node_type = node.get("_type", "")
            if node_type == "Assign":
                targets = node.get("targets", [])
                k = 0
                while k < len(targets):
                    self.collect_assign_target(targets[k], class_name, func_name, node)
                    k += 1
            elif node_type == "AnnAssign":
                target = node.get("target", {})
                if target.get("_type") == "Name":
                    name = target.get("id", "")
                    existing = self.result.table.get_local(class_name, func_name, name)
                    if existing is None:
                        lineno = node.get("lineno", 0)
                        col = node.get("col_offset", 0)
                        info = NameInfo(name, "variable", "local", lineno, col, class_name, func_name)
                        self.result.table.add_local(class_name, func_name, info)
            elif node_type == "For":
                target = node.get("target", {})
                self.collect_assign_target(target, class_name, func_name, node)
            elif node_type == "ExceptHandler":
                exc_name = node.get("name")
                if exc_name is not None:
                    existing = self.result.table.get_local(class_name, func_name, exc_name)
                    if existing is None:
                        lineno = node.get("lineno", 0)
                        col = node.get("col_offset", 0)
                        info = NameInfo(exc_name, "variable", "local", lineno, col, class_name, func_name)
                        self.result.table.add_local(class_name, func_name, info)
            elif node_type == "ImportFrom":
                # Register imported names in local scope
                names_list = node.get("names", [])
                k = 0
                while k < len(names_list):
                    alias = names_list[k]
                    if isinstance(alias, dict):
                        asname = alias.get("asname")
                        import_name = alias.get("name", "")
                        bound_name = asname if asname is not None else import_name
                        if bound_name != "" and bound_name != "*":
                            existing = self.result.table.get_local(class_name, func_name, bound_name)
                            if existing is None:
                                lineno = node.get("lineno", 0)
                                col = node.get("col_offset", 0)
                                info = NameInfo(bound_name, "import", "local", lineno, col, class_name, func_name)
                                self.result.table.add_local(class_name, func_name, info)
                    k += 1
            elif node_type in ("ListComp", "SetComp", "DictComp", "GeneratorExp"):
                # Collect comprehension loop variables
                generators = node.get("generators", [])
                k = 0
                while k < len(generators):
                    gen = generators[k]
                    if isinstance(gen, dict):
                        target = gen.get("target", {})
                        self.collect_assign_target(target, class_name, func_name, node)
                    k += 1
            elif node_type == "Match":
                # Collect pattern variables from match/case
                cases = node.get("cases", [])
                k = 0
                while k < len(cases):
                    case_node = cases[k]
                    if isinstance(case_node, dict):
                        pattern = case_node.get("pattern", {})
                        self.collect_pattern_names(pattern, class_name, func_name, node)
                    k += 1
            elif node_type == "NamedExpr":
                # Walrus operator: (x := expr)
                target = node.get("target", {})
                if target.get("_type") == "Name":
                    name = target.get("id", "")
                    existing = self.result.table.get_local(class_name, func_name, name)
                    if existing is None:
                        lineno = node.get("lineno", 0)
                        col = node.get("col_offset", 0)
                        info = NameInfo(name, "variable", "local", lineno, col, class_name, func_name)
                        self.result.table.add_local(class_name, func_name, info)
            # Add children (skip nested FunctionDef - shouldn't exist per Phase 3)
            children = get_children(node)
            m = 0
            while m < len(children):
                child = children[m]
                if child.get("_type") != "FunctionDef":
                    nodes_to_visit.append(child)
                m += 1
            j += 1

    def collect_assign_target(self, target: ASTNode, class_name: str, func_name: str, stmt: ASTNode) -> None:
        """Collect names from an assignment target."""
        target_type = target.get("_type", "")
        if target_type == "Name":
            name = target.get("id", "")
            existing = self.result.table.get_local(class_name, func_name, name)
            if existing is None:
                lineno = stmt.get("lineno", 0)
                col = stmt.get("col_offset", 0)
                info = NameInfo(name, "variable", "local", lineno, col, class_name, func_name)
                self.result.table.add_local(class_name, func_name, info)
        elif target_type == "Tuple" or target_type == "List":
            elts = target.get("elts", [])
            i = 0
            while i < len(elts):
                self.collect_assign_target(elts[i], class_name, func_name, stmt)
                i += 1
        # Attribute targets (self.x) are handled in pass2

    def collect_pattern_names(self, pattern: ASTNode, class_name: str, func_name: str, stmt: ASTNode) -> None:
        """Collect names bound by a match pattern."""
        pattern_type = pattern.get("_type", "")
        if pattern_type == "MatchAs":
            # MatchAs(pattern=inner, name=bound_name)
            name = pattern.get("name")
            if name is not None and name != "_":
                existing = self.result.table.get_local(class_name, func_name, name)
                if existing is None:
                    lineno = pattern.get("lineno", 0)
                    col = pattern.get("col_offset", 0)
                    info = NameInfo(name, "variable", "local", lineno, col, class_name, func_name)
                    self.result.table.add_local(class_name, func_name, info)
            inner = pattern.get("pattern")
            if inner is not None:
                self.collect_pattern_names(inner, class_name, func_name, stmt)
        elif pattern_type == "MatchClass":
            # MatchClass(cls=..., patterns=[], kwd_attrs=[], kwd_patterns=[])
            # The kwd_patterns bind their values as names
            kwd_attrs = pattern.get("kwd_attrs", [])
            kwd_patterns = pattern.get("kwd_patterns", [])
            i = 0
            while i < len(kwd_patterns):
                self.collect_pattern_names(kwd_patterns[i], class_name, func_name, stmt)
                i += 1
            # Positional patterns
            patterns = pattern.get("patterns", [])
            i = 0
            while i < len(patterns):
                self.collect_pattern_names(patterns[i], class_name, func_name, stmt)
                i += 1
        elif pattern_type == "MatchMapping":
            # MatchMapping(keys=[], patterns=[], rest=name)
            patterns = pattern.get("patterns", [])
            i = 0
            while i < len(patterns):
                self.collect_pattern_names(patterns[i], class_name, func_name, stmt)
                i += 1
            rest = pattern.get("rest")
            if rest is not None:
                existing = self.result.table.get_local(class_name, func_name, rest)
                if existing is None:
                    lineno = pattern.get("lineno", 0)
                    col = pattern.get("col_offset", 0)
                    info = NameInfo(rest, "variable", "local", lineno, col, class_name, func_name)
                    self.result.table.add_local(class_name, func_name, info)
        elif pattern_type == "MatchSequence":
            # MatchSequence(patterns=[])
            patterns = pattern.get("patterns", [])
            i = 0
            while i < len(patterns):
                self.collect_pattern_names(patterns[i], class_name, func_name, stmt)
                i += 1
        elif pattern_type == "MatchStar":
            # MatchStar(name=bound_name)
            name = pattern.get("name")
            if name is not None and name != "_":
                existing = self.result.table.get_local(class_name, func_name, name)
                if existing is None:
                    lineno = pattern.get("lineno", 0)
                    col = pattern.get("col_offset", 0)
                    info = NameInfo(name, "variable", "local", lineno, col, class_name, func_name)
                    self.result.table.add_local(class_name, func_name, info)
        elif pattern_type == "MatchOr":
            # MatchOr(patterns=[]) - all alternatives should bind same names
            patterns = pattern.get("patterns", [])
            if len(patterns) > 0:
                self.collect_pattern_names(patterns[0], class_name, func_name, stmt)

    def resolve_references_in_body(self, body: list[ASTNode], class_name: str, func_name: str) -> None:
        """Walk body and resolve all Name nodes with ctx=Load."""
        nodes_to_visit: list[ASTNode] = []
        i = 0
        while i < len(body):
            nodes_to_visit.append(body[i])
            i += 1
        j = 0
        while j < len(nodes_to_visit):
            node = nodes_to_visit[j]
            node_type = node.get("_type", "")
            if node_type == "Name":
                ctx = node.get("ctx", {})
                ctx_type = ctx.get("_type", "")
                if ctx_type == "Load":
                    name = node.get("id", "")
                    if not self.resolve_name(name, class_name, func_name):
                        self.error(node, "undefined", "name '" + name + "' is not defined")
            # Add children (skip nested FunctionDef)
            children = get_children(node)
            m = 0
            while m < len(children):
                child = children[m]
                if child.get("_type") != "FunctionDef":
                    nodes_to_visit.append(child)
                m += 1
            j += 1

    def resolve_name(self, name: str, class_name: str, func_name: str) -> bool:
        """Try to resolve a name: local → module → builtin."""
        # Check local scope
        local_info = self.result.table.get_local(class_name, func_name, name)
        if local_info is not None:
            return True
        # Check module scope
        module_info = self.result.table.get_module(name)
        if module_info is not None:
            return True
        # Check builtin scope
        if name in ALLOWED_BUILTINS:
            return True
        return False


def resolve_names(ast_dict: ASTNode) -> NameResult:
    """Phase 4: Resolve all names in the AST.

    Args:
        ast_dict: Dict-based AST from parse.py (validated by verify)

    Returns:
        NameResult with symbol table and any violations found
    """
    resolver = NameResolver()
    return resolver.resolve(ast_dict)
