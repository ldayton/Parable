#!/usr/bin/env python3
"""Transpile parable.py's restricted Python subset to JavaScript."""

import ast
import io
import sys
import tokenize
from pathlib import Path


class JSTranspiler(ast.NodeVisitor):
    def __init__(self):
        self.indent = 0
        self.output = []
        self.in_class_body = False
        self.in_method = False
        self.class_has_base = False
        self.declared_vars = set()
        # Pre-populate with known class names (needed for forward references)
        # Lexer methods may instantiate Node subclasses defined later in the file
        self.class_names = {
            "Parser",
            "Word",
            "ParseError",
            # Node subclasses used by Lexer for expansion parsing
            "AnsiCQuote",
            "LocaleString",
            "CommandSubstitution",
            "ProcessSubstitution",
            "ArithmeticExpansion",
            "ParamExpansion",
            "ParamLength",
            "ParamIndirect",
            "ArrayLiteral",
            "Empty",
            "ArithEmpty",
        }
        self.comments = {}  # line_number -> comment_text
        self.last_line = 0
        self._in_assignment_target = False
        self._reassigned_vars = set()
        self._emitted_vars = set()
        self._top_level_first_assign = set()  # Vars first assigned at top level
        self._block_depth = 0

    def emit(self, text: str):
        self.output.append("    " * self.indent + text)

    def emit_raw(self, text: str):
        self.output.append(text)

    def emit_comments_before(self, line: int):
        for comment_line in sorted(self.comments.keys()):
            if comment_line >= line:
                break
            if comment_line > self.last_line:
                comment = self.comments[comment_line].lstrip("# ").rstrip()
                self.emit(f"// {comment}")
        self.last_line = line

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
        tree = ast.parse(source)
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

    def visit_Module(self, node: ast.Module):
        # Emit module docstring as JSDoc comment
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
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
                    if line.strip():
                        self.emit(f" * {line}")
                    else:
                        self.emit(" *")
                self.emit(" */")
            self.emit("")
        for stmt in node.body:
            # Skip typing imports (from typing import ...)
            if isinstance(stmt, ast.ImportFrom) and stmt.module == "typing":
                continue
            # Skip type alias assignments (ArithNode = Union[...])
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                if isinstance(stmt.value, ast.Subscript):
                    if isinstance(stmt.value.value, ast.Name) and stmt.value.value.id == "Union":
                        continue
            # Skip unused module-level variable definitions
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                if isinstance(stmt.targets[0], ast.Name):
                    var_name = stmt.targets[0].id
                    if not self._is_name_used(var_name, node, stmt):
                        continue
            self.emit_comments_before(stmt.lineno)
            self.visit(stmt)

    def visit_ClassDef(self, node: ast.ClassDef):
        safe_name = self._safe_name(node.name)
        self.class_names.add(node.name)  # Track original name for isinstance checks
        bases = [self.visit_expr(b) for b in node.bases]
        extends = f" extends {bases[0]}" if bases else ""
        self.emit(f"class {safe_name}{extends} {{")
        self.indent += 1
        old_in_class = self.in_class_body
        old_has_base = self.class_has_base
        self.in_class_body = True
        self.class_has_base = bool(bases)
        for stmt in node.body:
            self.emit_comments_before(stmt.lineno)
            self.visit(stmt)
        self.in_class_body = old_in_class
        self.class_has_base = old_has_base
        self.indent -= 1
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
        if not isinstance(stmt, ast.Expr):
            return False
        call = stmt.value
        if not isinstance(call, ast.Call):
            return False
        if not isinstance(call.func, ast.Attribute):
            return False
        if call.func.attr != "__init__":
            return False
        if not isinstance(call.func.value, ast.Call):
            return False
        if not isinstance(call.func.value.func, ast.Name):
            return False
        return call.func.value.func.id == "super"

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

    def _collect_local_vars(self, stmts: list) -> set:
        """Collect all variable names assigned in a list of statements."""
        counts, _ = self._count_assignments(stmts)
        return set(counts.keys())

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

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Skip helper functions that are inlined
        if node.name in ("_substring", "_sublist", "_repeat_str"):
            return
        # Build args with default values in signature
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
        # Handle *args as rest parameter
        if node.args.vararg:
            args.append("..." + self._safe_name(node.args.vararg.arg))
        args_str = ", ".join(args)
        name = "constructor" if node.name == "__init__" else self._camel_case(node.name)
        if self.in_class_body and not self.in_method:
            # Class method
            self.emit(f"{name}({args_str}) {{")
        else:
            # Top-level or nested function
            self.emit(f"function {name}({args_str}) {{")
        self.indent += 1
        old_in_class = self.in_class_body
        old_in_method = self.in_method
        old_declared = self.declared_vars
        old_reassigned = self._reassigned_vars
        old_emitted = self._emitted_vars
        old_top_level = self._top_level_first_assign
        self.in_class_body = False
        self.in_method = True
        # Track variables for const vs let at point of use
        param_names = {a.arg for a in node.args.args if a.arg != "self"}
        if node.args.vararg:
            param_names.add(node.args.vararg.arg)
        assignment_counts, top_level_first = self._count_assignments(node.body)
        local_vars = set(assignment_counts.keys()) - param_names
        self.declared_vars = param_names | local_vars
        self._reassigned_vars = {name for name, count in assignment_counts.items() if count > 1}
        self._top_level_first_assign = top_level_first - param_names
        # Hoist vars not first-assigned at top level (they're used before assigned in main flow)
        hoisted = local_vars - self._top_level_first_assign
        if hoisted:
            sorted_vars = sorted(self._safe_name(v) for v in hoisted)
            self.emit(f"let {', '.join(sorted_vars)};")
        self._emitted_vars = set(param_names) | hoisted

        # For constructors in subclasses, emit super() first
        if name == "constructor" and self.class_has_base:
            # Find and emit super() call first, or add one if missing
            super_stmt = None
            other_stmts = []
            for stmt in node.body:
                if self._is_super_call(stmt):
                    super_stmt = stmt
                else:
                    other_stmts.append(stmt)
            if super_stmt:
                # Check if super() args reference self - if so, we need to emit super() first
                # then the assignments, then update message if needed
                call = super_stmt.value
                super_args = call.args
                args_use_self = any("self" in ast.dump(arg) for arg in super_args)
                if args_use_self:
                    # Emit super() with no args first
                    self.emit("super();")
                else:
                    self.visit(super_stmt)
            else:
                self.emit("super();")
            for stmt in other_stmts:
                self.emit_comments_before(stmt.lineno)
                self.visit(stmt)
        else:
            for stmt in node.body:
                self.emit_comments_before(stmt.lineno)
                self.visit(stmt)
        self.in_class_body = old_in_class
        self.in_method = old_in_method
        self.declared_vars = old_declared
        self._reassigned_vars = old_reassigned
        self._emitted_vars = old_emitted
        self._top_level_first_assign = old_top_level
        self.indent -= 1
        self.emit("}")
        self.emit("")

    def visit_Return(self, node: ast.Return):
        if node.value:
            self.emit(f"return {self.visit_expr(node.value)};")
        else:
            self.emit("return;")

    def _get_declaration_keyword(self, names: set) -> str | None:
        """Get const/let keyword for first assignment, or None if already declared."""
        undeclared = names - self._emitted_vars
        if not undeclared:
            return None
        self._emitted_vars.update(undeclared)
        # Use let if any variable in this assignment is reassigned elsewhere
        if undeclared & self._reassigned_vars:
            return "let"
        return "const"

    def visit_Assign(self, node: ast.Assign):
        self._in_assignment_target = True
        targets = [self.visit_expr(t) for t in node.targets]
        self._in_assignment_target = False
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
                keyword = self._get_declaration_keyword(names)
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
            keyword = self._get_declaration_keyword(names)
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

    def _emit_if(self, node: ast.If, is_elif: bool):
        test = self.visit_expr(node.test)
        # Handle truthiness checks - in Python [] is falsy but in JS it's truthy
        # Only add length check for known array-like attributes/variables
        array_attrs = {"redirects", "parts", "elements", "words", "patterns", "commands"}
        if (
            isinstance(node.test, ast.Attribute)
            and isinstance(node.test.value, ast.Name)
            and node.test.attr in array_attrs
        ):
            test = f"{test}?.length"
        elif isinstance(node.test, ast.Name) and node.test.id in array_attrs:
            test = f"{test}?.length"
        if is_elif:
            self.emit_raw("    " * self.indent + f"}} else if ({test}) {{")
        else:
            self.emit(f"if ({test}) {{")
        self.indent += 1
        for stmt in node.body:
            self.emit_comments_before(stmt.lineno)
            self.visit(stmt)
        self.indent -= 1
        if node.orelse:
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                self._emit_if(node.orelse[0], is_elif=True)
            else:
                self.emit("} else {")
                self.indent += 1
                for stmt in node.orelse:
                    self.emit_comments_before(stmt.lineno)
                    self.visit(stmt)
                self.indent -= 1
                self.emit("}")
        else:
            self.emit("}")

    def visit_While(self, node: ast.While):
        test = self.visit_expr(node.test)
        self.emit(f"while ({test}) {{")
        self.indent += 1
        for stmt in node.body:
            self.emit_comments_before(stmt.lineno)
            self.visit(stmt)
        self.indent -= 1
        self.emit("}")

    def visit_For(self, node: ast.For):
        target = self.visit_expr(node.target)
        iter_expr = node.iter
        # For loops always declare their own block-scoped variable
        # Use let for loop variables (they're reassigned each iteration)
        decl = "let "
        # Handle range() specially
        if (
            isinstance(iter_expr, ast.Call)
            and isinstance(iter_expr.func, ast.Name)
            and iter_expr.func.id == "range"
        ):
            args = iter_expr.args
            if len(args) == 1:
                self.emit(
                    f"for ({decl}{target} = 0; {target} < {self.visit_expr(args[0])}; {target}++) {{"
                )
            elif len(args) == 2:
                self.emit(
                    f"for ({decl}{target} = {self.visit_expr(args[0])}; {target} < {self.visit_expr(args[1])}; {target}++) {{"
                )
            else:
                start, end, step = args
                # Check if step is negative for proper comparison and decrement
                is_negative = False
                if isinstance(step, ast.UnaryOp) and isinstance(step.op, ast.USub):
                    is_negative = True
                elif isinstance(step, ast.Constant) and step.value < 0:
                    is_negative = True
                if is_negative:
                    self.emit(
                        f"for ({decl}{target} = {self.visit_expr(start)}; {target} > {self.visit_expr(end)}; {target}--) {{"
                    )
                else:
                    step_val = self.visit_expr(step)
                    self.emit(
                        f"for ({decl}{target} = {self.visit_expr(start)}; {target} < {self.visit_expr(end)}; {target} += {step_val}) {{"
                    )
        else:
            self.emit(f"for ({decl}{target} of {self.visit_expr(iter_expr)}) {{")
        self.indent += 1
        for stmt in node.body:
            self.emit_comments_before(stmt.lineno)
            self.visit(stmt)
        self.indent -= 1
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
        self.indent += 1
        for stmt in node.body:
            self.emit_comments_before(stmt.lineno)
            self.visit(stmt)
        self.indent -= 1
        for handler in node.handlers:
            name = handler.name or "_"
            self.emit(f"}} catch ({name}) {{")
            self.indent += 1
            for stmt in handler.body:
                self.emit_comments_before(stmt.lineno)
                self.visit(stmt)
            self.indent -= 1
        self.emit("}")

    # Expression visitors return strings
    def visit_expr(self, node: ast.expr) -> str:
        method = f"visit_expr_{node.__class__.__name__}"
        if hasattr(self, method):
            return getattr(self, method)(node)
        return f"/* TODO: {node.__class__.__name__} */"

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
            if key.isidentifier() and key not in (
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
            ):
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

    def visit_expr_Call(self, node: ast.Call) -> str:
        # Combine positional and keyword args (JS doesn't have kwargs, so treat as positional)
        all_args = [self._visit_callback_arg(a) for a in node.args]
        # Handle keyword args that skip positional defaults
        # Specific case: _format_cmdsub_node(x, in_procsub=True) -> FormatCmdsubNode(x, 0, true)
        for kw in node.keywords:
            if kw.arg == "in_procsub" and len(all_args) == 1:
                all_args.append("0")  # default for indent
            all_args.append(self.visit_expr(kw.value))
        args = ", ".join(all_args)
        # Handle method calls
        if isinstance(node.func, ast.Attribute):
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
            # Map Python methods to JS
            method_map = {
                "append": "push",
                "startswith": "startsWith",
                "endswith": "endsWith",
                "strip": "trim",
                # rstrip handled specially below
                "lower": "toLowerCase",
                "upper": "toUpperCase",
                # extend handled specially below
                "find": "indexOf",
                "rfind": "lastIndexOf",
                "replace": "replaceAll",  # Python replaces all, JS replace() only first
            }
            # Handle character class methods with regex
            if method == "isalpha":
                return f"/^[a-zA-Z]$/.test({obj})"
            if method == "isdigit":
                return f"/^[0-9]+$/.test({obj})"
            if method == "isalnum":
                return f"/^[a-zA-Z0-9]$/.test({obj})"
            if method == "isspace":
                return f"/^\\s$/.test({obj})"
            # Handle lstrip with character set argument
            if method == "lstrip":
                if len(node.args) == 1:
                    arg = node.args[0]
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        escaped = self._escape_regex_chars(arg.value)
                        return f'{obj}.replace(/^[{escaped}]+/, "")'
                    chars = self.visit_expr(arg)
                    return f'{obj}.replace(new RegExp("^[" + {chars} + "]+"), "")'
                return f"{obj}.trimStart()"
            # Handle rstrip with character set argument
            if method == "rstrip":
                if len(node.args) == 1:
                    arg = node.args[0]
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        escaped = self._escape_regex_chars(arg.value)
                        return f'{obj}.replace(/[{escaped}]+$/, "")'
                    chars = self.visit_expr(arg)
                    return f'{obj}.replace(new RegExp("[" + {chars} + "]+$"), "")'
                return f"{obj}.trimEnd()"
            # Handle str.encode() - returns array of byte values
            if method == "encode":
                return f"Array.from(new TextEncoder().encode({obj}))"
            # Handle bytes.decode() - converts byte array to string
            if method == "decode":
                return f"new TextDecoder().decode(new Uint8Array({obj}))"
            # Handle dict.get(key) and dict.get(key, default)
            if method == "get":
                if len(node.args) >= 2:
                    key = self.visit_expr(node.args[0])
                    default = self.visit_expr(node.args[1])
                    return f"({obj}[{key}] ?? {default})"
                elif len(node.args) == 1:
                    key = self.visit_expr(node.args[0])
                    return f"{obj}[{key}]"
            # Handle list.extend() - needs spread operator
            if method == "extend":
                if len(node.args) == 1:
                    items = self.visit_expr(node.args[0])
                    return f"{obj}.push(...{items})"
            # Handle endswith/startswith with tuple argument (JS only accepts string)
            if method == "endswith" and len(node.args) == 1:
                if isinstance(node.args[0], (ast.Tuple, ast.List)):
                    checks = [
                        f"{obj}.endsWith({self.visit_expr(elt)})" for elt in node.args[0].elts
                    ]
                    return f"({' || '.join(checks)})"
            if method == "startswith" and len(node.args) == 1:
                if isinstance(node.args[0], (ast.Tuple, ast.List)):
                    checks = [
                        f"{obj}.startsWith({self.visit_expr(elt)})" for elt in node.args[0].elts
                    ]
                    return f"({' || '.join(checks)})"
            method = method_map.get(method, method)
            # Convert remaining snake_case to camelCase
            if "_" in method:
                method = self._camel_case(method)
            # Special case: separator.join(lst) -> lst.join(separator)
            # In Python, join is a string method; in JS, it's an array method
            if method == "join" and len(node.args) == 1:
                sep = self.visit_expr(node.func.value)
                return f"{args}.join({sep})"
            return f"{obj}.{method}({args})"
        # Handle builtins
        if isinstance(node.func, ast.Name):
            name = node.func.id
            if name == "len":
                return f"{args}.length"
            if name == "str":
                return f"String({args})"
            if name == "int":
                if len(node.args) >= 2:
                    return f"parseInt({args})"
                return f"parseInt({args}, 10)"
            if name == "bool":
                # Warn if bool() is called on a bare variable - could be a list
                # (Python bool([]) is False, JS Boolean([]) is true)
                # Safe: bool(flags & MASK), bool(x > 0). Unsafe: bool(mylist)
                if len(node.args) == 1 and isinstance(node.args[0], ast.Name):
                    raise ValueError(
                        f"bool({node.args[0].id}) may have different behavior in JS for arrays. "
                        f"Use 'len({node.args[0].id}) > 0' for lists or explicit comparison for other types."
                    )
                return f"Boolean({args})"
            if name == "ord":
                return f"{args}.charCodeAt(0)"
            if name == "chr":
                # Use fromCodePoint for full unicode support (including > 0xFFFF)
                return f"String.fromCodePoint({args})"
            if name == "isinstance":
                return f"{node.args[0].id} instanceof {self.visit_expr(node.args[1])}"
            if name == "getattr":
                obj = self.visit_expr(node.args[0])
                attr_node = node.args[1]
                # Use dot notation for string attrs that are valid identifiers
                if isinstance(attr_node, ast.Constant) and isinstance(attr_node.value, str):
                    key = attr_node.value
                    if key.isidentifier():
                        # Convert snake_case to camelCase for self attributes
                        if obj == "this" and "_" in key:
                            key = self._camel_case(key)
                        if len(node.args) >= 3:
                            default = self.visit_expr(node.args[2])
                            return f"({obj}.{key} ?? {default})"
                        return f"{obj}.{key}"
                attr = self.visit_expr(attr_node)
                if len(node.args) >= 3:
                    default = self.visit_expr(node.args[2])
                    return f"({obj}[{attr}] ?? {default})"
                return f"{obj}[{attr}]"
            if name == "bytearray":
                return "[]"
            if name == "list":
                if args:
                    return f"Array.from({args})"
                return "[]"
            if name == "set":
                return f"new Set({args})"
            if name == "max":
                return f"Math.max({args})"
            if name == "min":
                return f"Math.min({args})"
            if name in ("_substring", "_sublist"):
                obj = self.visit_expr(node.args[0])
                start = self.visit_expr(node.args[1])
                end = self.visit_expr(node.args[2])
                return f"{obj}.slice({start}, {end})"
            if name == "_repeat_str":
                s = self.visit_expr(node.args[0])
                n = self.visit_expr(node.args[1])
                return f"{s}.repeat({n})"
            if name in self.class_names:
                return f"new {self._safe_name(name)}({args})"
            # Convert snake_case function names to camelCase
            if "_" in name:
                name = self._camel_case(name)
            return f"{name}({args})"
        return f"{self.visit_expr(node.func)}({args})"

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
        result = self.visit_expr(node.left)
        for op, comparator in zip(node.ops, node.comparators, strict=True):
            op_str = self.visit_cmpop(op)
            result += f" {op_str} {self.visit_expr(comparator)}"
        return f"({result})"

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
                rest_src = ast.dump(ast.Module(body=[ast.Expr(value=vv) for vv in node.values[1:]]))
                if f"Name(id='{first_name}'" in rest_src and "Subscript" in rest_src:
                    values.append(f"{first_name}.length > 0")
                    continue
            values.append(self.visit_expr(v))
        return f"({op.join(values)})"

    def visit_expr_UnaryOp(self, node: ast.UnaryOp) -> str:
        operand = self.visit_expr(node.operand)
        if isinstance(node.op, ast.Not):
            # Handle `not list_var` - in Python empty list is falsy, in JS array is truthy
            # Convert to `list_var.length === 0` for common list variable names
            if isinstance(node.operand, ast.Name):
                name = node.operand.id
                list_suffixes = (
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
                if name.endswith(list_suffixes) or name in list_suffixes:
                    return f"{name}.length === 0"
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
            ast.FloorDiv: "Math.floor(/",
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
            ast.Is: "==",
            ast.IsNot: "!=",  # == for is None checks (handles undefined)
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
