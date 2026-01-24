#!/usr/bin/env python3
"""Transpile parable.py's restricted Python subset to JavaScript."""

import ast
import io
import sys
import tokenize
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FunctionScope:
    """Tracks variable state within a function for const/let declaration."""

    declared: set = field(default_factory=set)
    reassigned: set = field(default_factory=set)
    emitted: set = field(default_factory=set)
    top_level_first: set = field(default_factory=set)


class _NotHandled:
    """Sentinel indicating a handler did not process the input."""

    __slots__ = ()

    def __bool__(self):
        raise TypeError("Use 'is NOT_HANDLED' instead of truthiness check")

    def __repr__(self):
        return "NOT_HANDLED"


NOT_HANDLED = _NotHandled()


class JSTranspiler(ast.NodeVisitor):
    def __init__(self):
        self.indent = 0
        self.output = []
        self.in_class_body = False
        self.in_method = False
        self.class_has_base = False
        self.scope = FunctionScope()
        self.class_names = set()  # populated by pre-pass in transpile()
        self.comments = {}  # line_number -> comment_text
        self._sorted_comment_lines = []  # populated once in transpile()
        self.last_line = 0
        self._in_assignment_target = False

    def emit(self, text: str) -> None:
        self.output.append("    " * self.indent + text)

    def emit_raw(self, text: str) -> None:
        self.output.append(text)

    def emit_same_line(self, text: str) -> None:
        """Emit text at current indent, closing previous block on same line."""
        self.output.append("    " * self.indent + text)

    def emit_comments_before(self, line: int) -> None:
        for comment_line in self._sorted_comment_lines:
            if comment_line >= line:
                break
            if comment_line > self.last_line:
                comment = self.comments[comment_line].lstrip("# ").rstrip()
                self.emit(f"// {comment}")
        self.last_line = line

    @contextmanager
    def _scoped(self, **attrs):
        """Temporarily set attributes, restoring originals on exit."""
        old = {k: getattr(self, k) for k in attrs}
        for k, v in attrs.items():
            setattr(self, k, v)
        try:
            yield
        finally:
            for k, v in old.items():
                setattr(self, k, v)

    @contextmanager
    def _indented(self):
        """Temporarily increase indentation level."""
        self.indent += 1
        try:
            yield
        finally:
            self.indent -= 1

    def transpile(self, source: str) -> str:
        # Extract standalone comments (not inline) using tokenize
        lines = source.splitlines()
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                line_num, col = tok.start
                # Only keep comments where preceding content on line is whitespace
                if lines[line_num - 1][:col].strip() == "":
                    self.comments[line_num] = tok.string
        self._sorted_comment_lines = sorted(self.comments.keys())
        tree = ast.parse(source)
        self.class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
        self.visit(tree)
        return "\n".join(self.output)

    def _is_name_used(self, name: str, tree: ast.Module, skip_stmt: ast.stmt) -> bool:
        """Check if a name is used anywhere in the module besides its definition."""
        skip_nodes = set(ast.walk(skip_stmt))
        for node in ast.walk(tree):
            if node in skip_nodes:
                continue
            if isinstance(node, ast.Name) and node.id == name:
                return True
        return False

    def _name_is_subscripted(self, name: str, exprs: list[ast.expr]) -> bool:
        """Check if name is used as the base of a subscript in any of the expressions."""
        for expr in exprs:
            for node in ast.walk(expr):
                if isinstance(node, ast.Subscript):
                    if isinstance(node.value, ast.Name) and node.value.id == name:
                        return True
        return False

    def _references_self(self, exprs: list[ast.expr]) -> bool:
        """Check if any expression references 'self'."""
        for expr in exprs:
            for node in ast.walk(expr):
                if isinstance(node, ast.Name) and node.id == "self":
                    return True
        return False

    def _is_array_attr(self, node: ast.expr) -> bool:
        """Check if node matches known array attributes (for if statement truthiness)."""
        if isinstance(node, ast.Name):
            return node.id in self._ARRAY_ATTRS
        if isinstance(node, ast.Attribute):
            return node.attr in self._ARRAY_ATTRS
        return False

    def _is_list_var(self, node: ast.expr) -> bool:
        """Check if node is likely a list variable (for negation truthiness)."""
        return isinstance(node, ast.Name) and (
            node.id.endswith(self._LIST_SUFFIXES) or node.id in self._LIST_SUFFIXES
        )

    def _emit_module_docstring(self, node: ast.Module) -> None:
        """Emit module docstring as JSDoc comment if present."""
        if not (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            return
        docstring = (
            node.body[0]
            .value.value.strip()
            .replace("Parable -", "Parable.js -", 1)
            .replace("from parable import parse", "import { parse } from './parable.js';")
            .replace("ast = parse(", "const ast = parse(")
        )
        lines = docstring.split("\n")
        if len(lines) == 1:
            self.emit(f"/** {docstring} */")
        else:
            self.emit("/**")
            for line in lines:
                self.emit(f" * {line}" if line.strip() else " *")
            self.emit(" */")
        self.emit("")

    def visit_Module(self, node: ast.Module):
        self._emit_module_docstring(node)
        for stmt in node.body:
            # Skip typing imports (from typing import ...)
            if isinstance(stmt, ast.ImportFrom) and stmt.module == "typing":
                continue
            # Skip type aliases and unused module-level variable definitions
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                # Type alias (ArithNode = Union[...])
                if isinstance(stmt.value, ast.Subscript):
                    if isinstance(stmt.value.value, ast.Name) and stmt.value.value.id == "Union":
                        continue
                # Unused variable
                if isinstance(stmt.targets[0], ast.Name):
                    if not self._is_name_used(stmt.targets[0].id, node, stmt):
                        continue
            self.emit_comments_before(stmt.lineno)
            self.visit(stmt)

    def visit_ClassDef(self, node: ast.ClassDef):
        safe_name = self._safe_name(node.name)
        bases = [self.visit_expr(b) for b in node.bases]
        extends = f" extends {bases[0]}" if bases else ""
        self.emit(f"class {safe_name}{extends} {{")
        with self._indented(), self._scoped(in_class_body=True, class_has_base=bool(bases)):
            for stmt in node.body:
                self.emit_comments_before(stmt.lineno)
                self.visit(stmt)
        self.emit("}")
        self.emit("")

    def _safe_name(self, name: str) -> str:
        """Rename JS reserved words and conflicting globals."""
        reserved = {
            "var": "variable",
            "class": "cls",
            "function": "func",
            "in": "inVal",
            "with": "withVal",
            "Array": "ArrayNode",  # Avoid shadowing JS global
            "Function": "FunctionNode",  # Avoid shadowing JS global
        }
        return reserved.get(name, name)

    def _escape_regex_chars(self, s: str) -> str:
        """Escape special regex characters for use in a character class."""
        result = []
        for c in s:
            # Note: - doesn't need escaping at start/end of character class
            if c in r"\]^":
                result.append("\\" + c)
            elif c == "\t":
                result.append("\\t")
            elif c == "\n":
                result.append("\\n")
            else:
                result.append(c)
        return "".join(result)

    def _is_super_call(self, stmt: ast.stmt) -> bool:
        """Check if statement is a super().__init__() call."""
        return (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Call)
            and isinstance(stmt.value.func, ast.Attribute)
            and stmt.value.func.attr == "__init__"
            and isinstance(stmt.value.func.value, ast.Call)
            and isinstance(stmt.value.func.value.func, ast.Name)
            and stmt.value.func.value.func.id == "super"
        )

    def _camel_case(self, name: str) -> str:
        """Convert snake_case or PascalCase to camelCase, preserving leading underscore."""
        prefix = ""
        if name.startswith("_"):
            prefix = "_"
            name = name[1:]
        parts = name.split("_")
        result = parts[0] + "".join(p.capitalize() for p in parts[1:])
        if result and result[0].isupper():
            result = result[0].lower() + result[1:]
        return prefix + result

    def _collect_names_from_target(self, target: ast.expr) -> set:
        """Recursively collect variable names from an assignment target."""
        names = set()
        if isinstance(target, ast.Name):
            names.add(target.id)
        elif isinstance(target, ast.Tuple):
            for elt in target.elts:
                names.update(self._collect_names_from_target(elt))
        elif isinstance(target, ast.Starred):
            names.update(self._collect_names_from_target(target.value))
        return names

    def _count_assignments(
        self, stmts: list, counts: dict = None, top_level: set = None, in_block: bool = False
    ) -> tuple[dict, set]:
        """Count assignments and track which vars are first assigned at top level."""
        if counts is None:
            counts = {}
        if top_level is None:
            top_level = set()
        for stmt in stmts:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    for name in self._collect_names_from_target(target):
                        if name not in counts and not in_block:
                            top_level.add(name)
                        counts[name] = counts.get(name, 0) + 1
            elif isinstance(stmt, ast.AnnAssign):
                if isinstance(stmt.target, ast.Name) and stmt.value:
                    name = stmt.target.id
                    if name not in counts and not in_block:
                        top_level.add(name)
                    counts[name] = counts.get(name, 0) + 1
            elif isinstance(stmt, ast.AugAssign):
                for name in self._collect_names_from_target(stmt.target):
                    counts[name] = counts.get(name, 0) + 1
            elif isinstance(stmt, ast.For):
                # For loop variables are always block-scoped in JS, don't count them
                # as function-level variables
                self._count_assignments(stmt.body, counts, top_level, True)
                self._count_assignments(stmt.orelse, counts, top_level, True)
            elif isinstance(stmt, ast.While):
                body_counts, _ = self._count_assignments(stmt.body, {}, set(), True)
                for name, count in body_counts.items():
                    # Double count so loop vars use `let` (loops may execute multiple times)
                    counts[name] = counts.get(name, 0) + count * 2
                self._count_assignments(stmt.orelse, counts, top_level, True)
            elif isinstance(stmt, ast.If):
                self._count_assignments(stmt.body, counts, top_level, True)
                self._count_assignments(stmt.orelse, counts, top_level, True)
            elif isinstance(stmt, ast.Try):
                self._count_assignments(stmt.body, counts, top_level, True)
                for handler in stmt.handlers:
                    self._count_assignments(handler.body, counts, top_level, True)
                self._count_assignments(stmt.finalbody, counts, top_level, True)
        return counts, top_level

    def _build_function_signature(self, node: ast.FunctionDef) -> tuple[str, str]:
        """Build JS function signature. Returns (name, args_str)."""
        non_self_args = [a for a in node.args.args if a.arg != "self"]
        defaults = node.args.defaults
        first_default_idx = len(non_self_args) - len(defaults) if defaults else len(non_self_args)
        args = []
        for i, a in enumerate(non_self_args):
            arg_str = self._safe_name(a.arg)
            if i >= first_default_idx:
                default = defaults[i - first_default_idx]
                # Skip None defaults - JS undefined handles this
                if not (isinstance(default, ast.Constant) and default.value is None):
                    arg_str += f" = {self.visit_expr(default)}"
            args.append(arg_str)
        if node.args.vararg:
            args.append("..." + self._safe_name(node.args.vararg.arg))
        name = "constructor" if node.name == "__init__" else self._camel_case(node.name)
        return name, ", ".join(args)

    def _setup_function_scope(self, node: ast.FunctionDef) -> FunctionScope:
        """Analyze function body and set up variable scope. Returns new scope."""
        param_names = {a.arg for a in node.args.args if a.arg != "self"}
        if node.args.vararg:
            param_names.add(node.args.vararg.arg)
        assignment_counts, top_level_first = self._count_assignments(node.body)
        local_vars = set(assignment_counts.keys()) - param_names
        scope = FunctionScope(
            declared=param_names | local_vars,
            reassigned={name for name, count in assignment_counts.items() if count > 1},
            top_level_first=top_level_first - param_names,
        )
        # Hoist vars not first-assigned at top level
        hoisted = local_vars - scope.top_level_first
        if hoisted:
            sorted_vars = sorted(self._safe_name(v) for v in hoisted)
            self.emit(f"let {', '.join(sorted_vars)};")
        scope.emitted = param_names | hoisted
        return scope

    def _emit_constructor_body(self, node: ast.FunctionDef) -> None:
        """Emit constructor body with super() handling."""
        super_stmt = None
        other_stmts = []
        for stmt in node.body:
            if self._is_super_call(stmt):
                super_stmt = stmt
            else:
                other_stmts.append(stmt)
        if super_stmt:
            call = super_stmt.value
            if self._references_self(call.args):
                self.emit("super();")
            else:
                self.visit(super_stmt)
        else:
            self.emit("super();")
        for stmt in other_stmts:
            self.emit_comments_before(stmt.lineno)
            self.visit(stmt)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if node.name in ("_substring", "_sublist", "_repeat_str"):
            return
        name, args_str = self._build_function_signature(node)
        if self.in_class_body and not self.in_method:
            self.emit(f"{name}({args_str}) {{")
        else:
            self.emit(f"function {name}({args_str}) {{")
        with self._indented():
            new_scope = self._setup_function_scope(node)
            with self._scoped(in_class_body=False, in_method=True, scope=new_scope):
                if name == "constructor" and self.class_has_base:
                    self._emit_constructor_body(node)
                else:
                    for stmt in node.body:
                        self.emit_comments_before(stmt.lineno)
                        self.visit(stmt)
        self.emit("}")
        self.emit("")

    def visit_Return(self, node: ast.Return):
        if node.value:
            self.emit(f"return {self.visit_expr(node.value)};")
        else:
            self.emit("return;")

    def _emit_declaration_keyword(self, names: set) -> str | None:
        """Mark names as emitted and return const/let keyword, or None if already declared."""
        undeclared = names - self.scope.emitted
        if not undeclared:
            return None
        self.scope.emitted.update(undeclared)
        # Use let if any variable in this assignment is reassigned elsewhere
        if undeclared & self.scope.reassigned:
            return "let"
        return "const"

    def visit_Assign(self, node: ast.Assign):
        with self._scoped(_in_assignment_target=True):
            targets = [self.visit_expr(t) for t in node.targets]
        value = self.visit_expr(node.value)
        # Module-level assignments get const
        if not self.in_method and not self.in_class_body:
            for target in targets:
                self.emit(f"const {target} = {value};")
        elif self.in_class_body and not self.in_method:
            # Class-level assignments become static fields in JS
            for target in targets:
                self.emit(f"static {target} = {value};")
        else:
            # Emit declaration keyword on first assignment for each target
            for i, target in enumerate(targets):
                names = self._collect_names_from_target(node.targets[i])
                keyword = self._emit_declaration_keyword(names)
                if keyword:
                    self.emit(f"{keyword} {target} = {value};")
                else:
                    self.emit(f"{target} = {value};")

    def visit_AnnAssign(self, node: ast.AnnAssign):
        # Skip class-level type annotations - constructor handles initialization
        if self.in_class_body:
            return
        if node.value:
            target = self.visit_expr(node.target)
            value = self.visit_expr(node.value)
            names = self._collect_names_from_target(node.target)
            keyword = self._emit_declaration_keyword(names)
            if keyword:
                self.emit(f"{keyword} {target} = {value};")
            else:
                self.emit(f"{target} = {value};")

    def visit_AugAssign(self, node: ast.AugAssign):
        target = self.visit_expr(node.target)
        # Use ++ and -- for += 1 and -= 1
        if isinstance(node.value, ast.Constant) and node.value.value == 1:
            if isinstance(node.op, ast.Add):
                self.emit(f"{target}++;")
                return
            if isinstance(node.op, ast.Sub):
                self.emit(f"{target}--;")
                return
        op = self.visit_op(node.op)
        value = self.visit_expr(node.value)
        self.emit(f"{target} {op}= {value};")

    def _is_nullish_assign(self, node: ast.If) -> tuple[str, str] | None:
        """Check if `if x is None: x = val` pattern, return (var, val) or None."""
        if node.orelse:
            return None
        if len(node.body) != 1 or not isinstance(node.body[0], ast.Assign):
            return None
        if not isinstance(node.test, ast.Compare):
            return None
        if len(node.test.ops) != 1 or not isinstance(node.test.ops[0], ast.Is):
            return None
        if not isinstance(node.test.comparators[0], ast.Constant):
            return None
        if node.test.comparators[0].value is not None:
            return None
        if not isinstance(node.test.left, ast.Name):
            return None
        var_name = node.test.left.id
        assign = node.body[0]
        if len(assign.targets) != 1 or not isinstance(assign.targets[0], ast.Name):
            return None
        if assign.targets[0].id != var_name:
            return None
        return (self._safe_name(var_name), self.visit_expr(assign.value))

    def visit_If(self, node: ast.If):
        nullish = self._is_nullish_assign(node)
        if nullish:
            var, val = nullish
            self.emit(f"{var} ??= {val};")
            return
        self._emit_if(node, is_elif=False)

    def _emit_if(self, node: ast.If, is_elif: bool) -> None:
        test = self.visit_expr(node.test)
        # Handle truthiness checks - in Python [] is falsy but in JS it's truthy
        if self._is_array_attr(node.test):
            test = f"{test}?.length"
        if is_elif:
            self.emit_same_line(f"}} else if ({test}) {{")
        else:
            self.emit(f"if ({test}) {{")
        with self._indented():
            for stmt in node.body:
                self.emit_comments_before(stmt.lineno)
                self.visit(stmt)
        if node.orelse:
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                self._emit_if(node.orelse[0], is_elif=True)
            else:
                self.emit("} else {")
                with self._indented():
                    for stmt in node.orelse:
                        self.emit_comments_before(stmt.lineno)
                        self.visit(stmt)
                self.emit("}")
        else:
            self.emit("}")

    def visit_While(self, node: ast.While):
        test = self.visit_expr(node.test)
        self.emit(f"while ({test}) {{")
        with self._indented():
            for stmt in node.body:
                self.emit_comments_before(stmt.lineno)
                self.visit(stmt)
        self.emit("}")

    def _emit_range_header(self, target: str, args: list[ast.expr]) -> str:
        """Build a C-style for loop header from range() arguments."""
        if len(args) == 1:
            return f"for (let {target} = 0; {target} < {self.visit_expr(args[0])}; {target}++)"
        if len(args) == 2:
            return f"for (let {target} = {self.visit_expr(args[0])}; {target} < {self.visit_expr(args[1])}; {target}++)"
        start, end, step = args
        is_negative = (isinstance(step, ast.UnaryOp) and isinstance(step.op, ast.USub)) or (
            isinstance(step, ast.Constant) and step.value < 0
        )
        if is_negative:
            return f"for (let {target} = {self.visit_expr(start)}; {target} > {self.visit_expr(end)}; {target}--)"
        step_val = self.visit_expr(step)
        return f"for (let {target} = {self.visit_expr(start)}; {target} < {self.visit_expr(end)}; {target} += {step_val})"

    def visit_For(self, node: ast.For):
        target = self.visit_expr(node.target)
        iter_expr = node.iter
        if (
            isinstance(iter_expr, ast.Call)
            and isinstance(iter_expr.func, ast.Name)
            and iter_expr.func.id == "range"
        ):
            self.emit(f"{self._emit_range_header(target, iter_expr.args)} {{")
        else:
            self.emit(f"for (let {target} of {self.visit_expr(iter_expr)}) {{")
        with self._indented():
            for stmt in node.body:
                self.emit_comments_before(stmt.lineno)
                self.visit(stmt)
        self.emit("}")

    def visit_Expr(self, node: ast.Expr):
        # Skip bare string literals (docstrings) - they do nothing in JS
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return
        self.emit(f"{self.visit_expr(node.value)};")

    def visit_Pass(self, node: ast.Pass):
        pass

    def visit_Break(self, node: ast.Break):
        self.emit("break;")

    def visit_Continue(self, node: ast.Continue):
        self.emit("continue;")

    def visit_Raise(self, node: ast.Raise):
        if node.exc:
            self.emit(f"throw {self.visit_expr(node.exc)};")
        else:
            self.emit("throw;")

    def visit_Try(self, node: ast.Try):
        self.emit("try {")
        with self._indented():
            for stmt in node.body:
                self.emit_comments_before(stmt.lineno)
                self.visit(stmt)
        for handler in node.handlers:
            name = handler.name or "_"
            self.emit(f"}} catch ({name}) {{")
            with self._indented():
                for stmt in handler.body:
                    self.emit_comments_before(stmt.lineno)
                    self.visit(stmt)
        self.emit("}")

    # Expression visitors return strings
    def visit_expr(self, node: ast.expr) -> str:
        method = f"visit_expr_{node.__class__.__name__}"
        if hasattr(self, method):
            return getattr(self, method)(node)
        raise NotImplementedError(f"No visitor for {node.__class__.__name__}")

    def visit_expr_Name(self, node: ast.Name) -> str:
        mapping = {
            "True": "true",
            "False": "false",
            "None": "null",
            "self": "this",
            "Exception": "Error",
            "NotImplementedError": 'new Error("Not implemented")',
        }
        name = mapping.get(node.id, node.id)
        return self._safe_name(name)

    def visit_expr_Constant(self, node: ast.Constant) -> str:
        if isinstance(node.value, str):
            escaped = (
                node.value.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\t", "\\t")
            )
            return f'"{escaped}"'
        if isinstance(node.value, bytes):
            # Convert bytes to array of numbers
            return "[" + ", ".join(str(b) for b in node.value) + "]"
        if node.value is None:
            return "null"
        if node.value is True:
            return "true"
        if node.value is False:
            return "false"
        return repr(node.value)

    def visit_expr_Attribute(self, node: ast.Attribute) -> str:
        value = self.visit_expr(node.value)
        attr = self._safe_name(node.attr)
        if isinstance(node.value, ast.Name) and node.value.id == "self":
            return f"this.{attr}"
        return f"{value}.{attr}"

    def _is_last_index(self, node: ast.Subscript) -> bool:
        """Check if subscript is arr[len(arr) - 1] pattern (read context only)."""
        if self._in_assignment_target:
            return False
        if not isinstance(node.slice, ast.BinOp) or not isinstance(node.slice.op, ast.Sub):
            return False
        if not isinstance(node.slice.right, ast.Constant) or node.slice.right.value != 1:
            return False
        left = node.slice.left
        if not isinstance(left, ast.Call) or not isinstance(left.func, ast.Name):
            return False
        if left.func.id != "len" or len(left.args) != 1:
            return False
        return ast.dump(left.args[0]) == ast.dump(node.value)

    def visit_expr_Subscript(self, node: ast.Subscript) -> str:
        value = self.visit_expr(node.value)
        # Detect arr[len(arr) - 1] -> arr.at(-1)
        if self._is_last_index(node):
            return f"{value}.at(-1)"
        if isinstance(node.slice, ast.Slice):
            lower = self.visit_expr(node.slice.lower) if node.slice.lower else "0"
            upper = self.visit_expr(node.slice.upper) if node.slice.upper else ""
            if upper:
                return f"{value}.slice({lower}, {upper})"
            return f"{value}.slice({lower})"
        # Use dot notation for string keys that are valid identifiers
        if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            key = node.slice.value
            if key.isidentifier() and key not in self._JS_RESERVED:
                return f"{value}.{key}"
        return f"{value}[{self.visit_expr(node.slice)}]"

    def _visit_callback_arg(self, arg: ast.expr) -> str:
        """Visit an argument, adding .bind(this) for self method references used as callbacks."""
        # Only add .bind(this) for parser methods passed as callbacks
        if (
            isinstance(arg, ast.Attribute)
            and isinstance(arg.value, ast.Name)
            and arg.value.id == "self"
            and (arg.attr.startswith("_arith_parse_") or arg.attr.startswith("_parse_"))
        ):
            # Convert method name to camelCase and add bind
            method_name = self._camel_case(arg.attr)
            return f"this.{method_name}.bind(this)"
        return self.visit_expr(arg)

    # Attributes/names that are known to be arrays (for Python/JS truthiness fix)
    _ARRAY_ATTRS = {"redirects", "parts", "elements", "words", "patterns", "commands"}
    _LIST_SUFFIXES = (
        "_chars",
        "_list",
        "_parts",
        "chars",
        "parts",
        "result",
        "results",
        "items",
        "values",
    )
    # Method name mappings: Python -> JS
    _method_renames = {
        "append": "push",
        "startswith": "startsWith",
        "endswith": "endsWith",
        "strip": "trim",
        "lower": "toLowerCase",
        "upper": "toUpperCase",
        "find": "indexOf",
        "rfind": "lastIndexOf",
        "replace": "replaceAll",
    }
    # Regex-based character class tests
    _char_class_tests = {
        "isalpha": "/^[a-zA-Z]$/",
        "isdigit": "/^[0-9]+$/",
        "isalnum": "/^[a-zA-Z0-9]$/",
        "isspace": "/^\\s$/",
    }
    # JS reserved words that cannot be used with dot notation
    _JS_RESERVED = {
        "class",
        "default",
        "delete",
        "export",
        "import",
        "new",
        "return",
        "super",
        "switch",
        "this",
        "throw",
        "typeof",
        "void",
        "with",
        "yield",
    }

    def _handle_method_call(self, node: ast.Call, obj: str, method: str) -> str | _NotHandled:
        """Handle special method transformations. Returns NOT_HANDLED to fall through."""
        # Character class tests
        if method in self._char_class_tests:
            return f"{self._char_class_tests[method]}.test({obj})"
        # Strip methods with optional character set
        if method in ("lstrip", "rstrip"):
            return self._handle_strip(node, obj, method)
        # Encoding
        if method == "encode":
            return f"new TextEncoder().encode({obj})"
        if method == "decode":
            return f"new TextDecoder().decode(new Uint8Array({obj}))"
        # Dict get
        if method == "get":
            return self._handle_dict_get(node, obj)
        # List extend
        if method == "extend" and len(node.args) == 1:
            return f"{obj}.push(...{self.visit_expr(node.args[0])})"
        # Tuple argument for startswith/endswith
        if method in ("endswith", "startswith") and len(node.args) == 1:
            if isinstance(node.args[0], (ast.Tuple, ast.List)):
                js_method = self._method_renames[method]
                checks = [f"{obj}.{js_method}({self.visit_expr(e)})" for e in node.args[0].elts]
                return f"({' || '.join(checks)})"
        # Join: separator.join(lst) -> lst.join(separator)
        if method == "join" and len(node.args) == 1:
            return f"{self.visit_expr(node.args[0])}.join({obj})"
        return NOT_HANDLED

    def _handle_strip(self, node: ast.Call, obj: str, method: str) -> str:
        """Handle lstrip/rstrip with optional character set argument."""
        if len(node.args) == 1:
            arg = node.args[0]
            anchor = "^" if method == "lstrip" else "$"
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                escaped = self._escape_regex_chars(arg.value)
                pattern = f"{anchor}[{escaped}]+" if method == "lstrip" else f"[{escaped}]+{anchor}"
                return f'{obj}.replace(/{pattern}/, "")'
            chars = self.visit_expr(arg)
            pattern = (
                f'"{anchor}[" + {chars} + "]+"'
                if method == "lstrip"
                else f'"[" + {chars} + "]+{anchor}"'
            )
            return f'{obj}.replace(new RegExp({pattern}), "")'
        return f"{obj}.{'trimStart' if method == 'lstrip' else 'trimEnd'}()"

    def _handle_dict_get(self, node: ast.Call, obj: str) -> str | _NotHandled:
        """Handle dict.get(key) and dict.get(key, default). Returns NOT_HANDLED to fall through."""
        if len(node.args) >= 2:
            key = self.visit_expr(node.args[0])
            default = self.visit_expr(node.args[1])
            return f"({obj}[{key}] ?? {default})"
        if len(node.args) == 1:
            return f"{obj}[{self.visit_expr(node.args[0])}]"
        return NOT_HANDLED

    def visit_expr_Call(self, node: ast.Call) -> str:
        # Combine positional and keyword args (JS doesn't have kwargs, so treat as positional)
        all_args = [self._visit_callback_arg(a) for a in node.args]
        # Python kwargs with skipped positional defaults need explicit JS defaults
        # Maps: (kwarg_name, current_arg_count) -> defaults to insert before the kwarg
        _KWARG_DEFAULTS = {("in_procsub", 1): ["0"]}  # indent=0 default
        for kw in node.keywords:
            for default in _KWARG_DEFAULTS.get((kw.arg, len(all_args)), []):
                all_args.append(default)
            all_args.append(self.visit_expr(kw.value))
        args = ", ".join(all_args)
        if isinstance(node.func, ast.Attribute):
            return self._visit_attr_call(node, args)
        if isinstance(node.func, ast.Name):
            return self._visit_name_call(node, args)
        return f"{self.visit_expr(node.func)}({args})"

    def _visit_attr_call(self, node: ast.Call, args: str) -> str:
        """Handle method calls (obj.method(...))."""
        # Special case: super().__init__(args) -> super(args)
        if (
            node.func.attr == "__init__"
            and isinstance(node.func.value, ast.Call)
            and isinstance(node.func.value.func, ast.Name)
            and node.func.value.func.id == "super"
        ):
            return f"super({args})"
        obj = self.visit_expr(node.func.value)
        method = node.func.attr
        # Try special method handlers first
        result = self._handle_method_call(node, obj, method)
        if result is not NOT_HANDLED:
            return result
        # Apply simple renames, then camelCase conversion
        method = self._method_renames.get(method, method)
        if "_" in method:
            method = self._camel_case(method)
        return f"{obj}.{method}({args})"

    def _visit_name_call(self, node: ast.Call, args: str) -> str:
        """Handle function/builtin calls (name(...))."""
        name = node.func.id
        # Try builtin handlers
        result = self._handle_builtin_call(node, name, args)
        if result is not NOT_HANDLED:
            return result
        # Class instantiation
        if name in self.class_names:
            return f"new {self._safe_name(name)}({args})"
        # Convert snake_case function names to camelCase
        if "_" in name:
            name = self._camel_case(name)
        return f"{name}({args})"

    def _handle_builtin_call(self, node: ast.Call, name: str, args: str) -> str | _NotHandled:
        """Handle Python builtin function calls. Returns NOT_HANDLED if not handled."""
        if name == "len":
            return f"{args}.length"
        if name == "str":
            return f"String({args})"
        if name == "int":
            return f"parseInt({args})" if len(node.args) >= 2 else f"parseInt({args}, 10)"
        if name == "bool":
            # Warn if bool() is called on a bare variable - could be a list
            if len(node.args) == 1 and isinstance(node.args[0], ast.Name):
                raise ValueError(
                    f"bool({node.args[0].id}) may have different behavior in JS for arrays. "
                    f"Use 'len({node.args[0].id}) > 0' for lists or explicit comparison."
                )
            return f"Boolean({args})"
        if name == "ord":
            return f"{args}.charCodeAt(0)"
        if name == "chr":
            return f"String.fromCodePoint({args})"
        if name == "isinstance":
            return f"{self.visit_expr(node.args[0])} instanceof {self.visit_expr(node.args[1])}"
        if name == "getattr":
            return self._handle_getattr(node)
        if name == "bytearray":
            return "[]"
        if name == "list":
            return f"[...{args}]" if args else "[]"
        if name == "set":
            return f"new Set({args})"
        if name == "max":
            return f"Math.max({args})"
        if name == "min":
            return f"Math.min({args})"
        if name in ("_substring", "_sublist"):
            obj, start, end = [self.visit_expr(a) for a in node.args[:3]]
            return f"{obj}.slice({start}, {end})"
        if name == "_repeat_str":
            s, n = self.visit_expr(node.args[0]), self.visit_expr(node.args[1])
            return f"{s}.repeat({n})"
        return NOT_HANDLED

    def _handle_getattr(self, node: ast.Call) -> str:
        """Handle getattr(obj, attr) and getattr(obj, attr, default)."""
        obj = self.visit_expr(node.args[0])
        attr_node = node.args[1]
        default = self.visit_expr(node.args[2]) if len(node.args) >= 3 else None
        # Use dot notation for string attrs that are valid identifiers
        if isinstance(attr_node, ast.Constant) and isinstance(attr_node.value, str):
            key = attr_node.value
            if key.isidentifier():
                if obj == "this" and "_" in key:
                    key = self._camel_case(key)
                return f"({obj}.{key} ?? {default})" if default else f"{obj}.{key}"
        attr = self.visit_expr(attr_node)
        return f"({obj}[{attr}] ?? {default})" if default else f"{obj}[{attr}]"

    def _is_string_concat(self, node: ast.expr) -> bool:
        """Check if an expression is part of string concatenation."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return True
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return self._is_string_concat(node.left) or self._is_string_concat(node.right)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            return node.func.id == "str"
        if isinstance(node, ast.Attribute):
            return True  # Assume attribute access in concat context is string
        return False

    def _flatten_string_concat(self, node: ast.expr) -> list:
        """Flatten a chain of string concatenations into parts."""
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            if self._is_string_concat(node):
                return self._flatten_string_concat(node.left) + self._flatten_string_concat(
                    node.right
                )
        return [node]

    def _build_template_literal(self, parts: list) -> str:
        """Build a JS template literal from parts."""
        result = []
        for part in parts:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                # Escape backticks and ${} in string literals
                escaped = part.value.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
                escaped = escaped.replace("\n", "\\n").replace("\t", "\\t")
                result.append(escaped)
            elif (
                isinstance(part, ast.Call)
                and isinstance(part.func, ast.Name)
                and part.func.id == "str"
            ):
                # str(x) becomes ${x}
                result.append("${" + self.visit_expr(part.args[0]) + "}")
            else:
                # Other expressions become ${expr}
                result.append("${" + self.visit_expr(part) + "}")
        return "`" + "".join(result) + "`"

    def visit_expr_JoinedStr(self, node: ast.JoinedStr) -> str:
        """Handle f-strings by converting to JS template literals."""
        result = []
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                escaped = part.value.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
                escaped = escaped.replace("\n", "\\n").replace("\t", "\\t")
                result.append(escaped)
            elif isinstance(part, ast.FormattedValue):
                result.append("${" + self.visit_expr(part.value) + "}")
        return "`" + "".join(result) + "`"

    def visit_expr_BinOp(self, node: ast.BinOp) -> str:
        # Check for string concatenation - convert to template literal
        if isinstance(node.op, ast.Add) and self._is_string_concat(node):
            parts = self._flatten_string_concat(node)
            # Only use template literal if there's at least one string literal
            has_string = any(
                isinstance(p, ast.Constant) and isinstance(p.value, str) for p in parts
            )
            if has_string:
                return self._build_template_literal(parts)
        # Check for string multiplication - convert to .repeat()
        if isinstance(node.op, ast.Mult):
            left_is_str = isinstance(node.left, ast.Constant) and isinstance(node.left.value, str)
            right_is_str = isinstance(node.right, ast.Constant) and isinstance(
                node.right.value, str
            )
            if left_is_str:
                return f"{self.visit_expr(node.left)}.repeat({self.visit_expr(node.right)})"
            if right_is_str:
                return f"{self.visit_expr(node.right)}.repeat({self.visit_expr(node.left)})"
        left = self.visit_expr(node.left)
        right = self.visit_expr(node.right)
        op = self.visit_op(node.op)
        return f"({left} {op} {right})"

    def _is_set_expr(self, node: ast.expr) -> bool:
        """Check if an expression is likely a set (use .has) vs list/string (use .includes)."""
        if isinstance(node, ast.Set):
            return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "set":
                return True
        if isinstance(node, ast.Name):
            name = node.id
            if name.isupper() or name.endswith(("_words", "_set", "_sets")):
                return True
        return False

    def visit_expr_Compare(self, node: ast.Compare) -> str:
        # Handle single comparison with in/not in specially
        if len(node.ops) == 1:
            left = self.visit_expr(node.left)
            right = self.visit_expr(node.comparators[0])
            op = node.ops[0]
            if isinstance(op, ast.In):
                if self._is_set_expr(node.comparators[0]):
                    return f"{right}.has({left})"
                return f"{right}.includes({left})"
            if isinstance(op, ast.NotIn):
                if self._is_set_expr(node.comparators[0]):
                    return f"!{right}.has({left})"
                return f"!{right}.includes({left})"
            # Handle .find(x) != -1 → .includes(x) and .find(x) == -1 → !.includes(x)
            if self._is_find_comparison(node.left, node.comparators[0], op):
                obj = self.visit_expr(node.left.func.value)
                args = ", ".join(self.visit_expr(a) for a in node.left.args)
                if isinstance(op, ast.NotEq):
                    return f"{obj}.includes({args})"
                return f"!{obj}.includes({args})"
        result = self.visit_expr(node.left)
        for op, comparator in zip(node.ops, node.comparators, strict=True):
            op_str = self.visit_cmpop(op)
            result += f" {op_str} {self.visit_expr(comparator)}"
        return f"({result})"

    def _is_find_comparison(self, left: ast.expr, right: ast.expr, op: ast.cmpop) -> bool:
        """Check if this is a .find(x) == -1 or .find(x) != -1 pattern."""
        if not isinstance(op, (ast.Eq, ast.NotEq)):
            return False
        is_find_call = (
            isinstance(left, ast.Call)
            and isinstance(left.func, ast.Attribute)
            and left.func.attr == "find"
            and len(left.args) in (1, 2)
        )
        is_minus_one = (
            isinstance(right, ast.UnaryOp)
            and isinstance(right.op, ast.USub)
            and isinstance(right.operand, ast.Constant)
            and right.operand.value == 1
        )
        return is_find_call and is_minus_one

    def visit_expr_BoolOp(self, node: ast.BoolOp) -> str:
        op = " && " if isinstance(node.op, ast.And) else " || "
        # Detect pattern: if x and ...x[...]... where x is used with subscript
        # In Python, empty list is falsy; in JS, empty array is truthy
        # Convert first operand to x.length > 0 when subscripted later
        values = []
        first_name = None
        if isinstance(node.op, ast.And) and len(node.values) >= 2:
            if isinstance(node.values[0], ast.Name):
                first_name = node.values[0].id
        for i, v in enumerate(node.values):
            if i == 0 and first_name:
                # Check if any later value subscripts this name
                if self._name_is_subscripted(first_name, node.values[1:]):
                    values.append(f"{first_name}.length > 0")
                    continue
            values.append(self.visit_expr(v))
        return f"({op.join(values)})"

    def visit_expr_UnaryOp(self, node: ast.UnaryOp) -> str:
        operand = self.visit_expr(node.operand)
        if isinstance(node.op, ast.Not):
            # Handle `not list_var` - in Python empty list is falsy, in JS array is truthy
            if self._is_list_var(node.operand):
                return f"{operand}.length === 0"
            return f"!{operand}"
        if isinstance(node.op, ast.USub):
            return f"-{operand}"
        return f"/* TODO: UnaryOp {node.op} */{operand}"

    def visit_expr_IfExp(self, node: ast.IfExp) -> str:
        test = self.visit_expr(node.test)
        body = self.visit_expr(node.body)
        orelse = self.visit_expr(node.orelse)
        return f"({test} ? {body} : {orelse})"

    def visit_expr_Lambda(self, node: ast.Lambda) -> str:
        args = [self._safe_name(a.arg) for a in node.args.args]
        args_str = ", ".join(args)
        body = self.visit_expr(node.body)
        return f"(({args_str}) => {body})"

    def visit_expr_List(self, node: ast.List) -> str:
        elements = ", ".join(self.visit_expr(e) for e in node.elts)
        return f"[{elements}]"

    def visit_expr_Dict(self, node: ast.Dict) -> str:
        pairs = []
        for k, v in zip(node.keys, node.values, strict=True):
            pairs.append(f"{self.visit_expr(k)}: {self.visit_expr(v)}")
        return "{" + ", ".join(pairs) + "}"

    def visit_expr_Tuple(self, node: ast.Tuple) -> str:
        elements = ", ".join(self.visit_expr(e) for e in node.elts)
        return f"[{elements}]"

    def visit_expr_Starred(self, node: ast.Starred) -> str:
        return f"...{self.visit_expr(node.value)}"

    def visit_expr_Set(self, node: ast.Set) -> str:
        elements = ", ".join(self.visit_expr(e) for e in node.elts)
        return f"new Set([{elements}])"

    def visit_op(self, op: ast.operator) -> str:
        ops = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.Mod: "%",
            ast.Pow: "**",
            ast.LShift: "<<",
            ast.RShift: ">>",
            ast.BitOr: "|",
            ast.BitXor: "^",
            ast.BitAnd: "&",
        }
        return ops.get(type(op), "/* ? */")

    def visit_cmpop(self, op: ast.cmpop) -> str:
        ops = {
            ast.Eq: "===",
            ast.NotEq: "!==",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
            ast.Is: "==",  # loose equality so `x is None` matches null/undefined
            ast.IsNot: "!=",
            ast.In: "in",
            ast.NotIn: "not in",
        }
        return ops.get(type(op), "/* ? */")


def main():
    if len(sys.argv) < 2:
        print("Usage: transpile.py <input.py>", file=sys.stderr)
        sys.exit(1)
    source = Path(sys.argv[1]).read_text()
    transpiler = JSTranspiler()
    print(transpiler.transpile(source))
    print()
    print("module.exports = { parse, ParseError };")


if __name__ == "__main__":
    main()
