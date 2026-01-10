#!/usr/bin/env python3
"""Transpile parable.py's restricted Python subset to JavaScript."""

import ast
import sys
from pathlib import Path


class JSTranspiler(ast.NodeVisitor):
    def __init__(self):
        self.indent = 0
        self.output = []
        self.in_class_body = False
        self.in_method = False
        self.class_has_base = False
        self.declared_vars = set()
        self.class_names = set()

    def emit(self, text: str):
        self.output.append("    " * self.indent + text)

    def emit_raw(self, text: str):
        self.output.append(text)

    def transpile(self, source: str) -> str:
        tree = ast.parse(source)
        self.visit(tree)
        return "\n".join(self.output)

    def visit_Module(self, node: ast.Module):
        for stmt in node.body:
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
            self.visit(stmt)
        self.in_class_body = old_in_class
        self.class_has_base = old_has_base
        self.indent -= 1
        self.emit("}")
        self.emit("")

    def _safe_name(self, name: str) -> str:
        """Rename JS reserved words and conflicting globals."""
        reserved = {
            "var": "variable", "class": "cls", "function": "func",
            "in": "inVal", "with": "withVal",
            "Array": "ArrayNode",  # Avoid shadowing JS global
        }
        return reserved.get(name, name)

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
        """Convert snake_case to camelCase."""
        parts = name.split("_")
        return parts[0] + "".join(p.capitalize() for p in parts[1:])

    def visit_FunctionDef(self, node: ast.FunctionDef):
        args = [self._safe_name(a.arg) for a in node.args.args if a.arg != "self"]
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
        self.in_class_body = False
        self.in_method = True
        # Start with function parameters as declared
        self.declared_vars = set(a.arg for a in node.args.args if a.arg != "self")
        # Helper to emit default argument checks
        def emit_defaults():
            defaults = node.args.defaults
            if defaults:
                non_self_args = [a for a in node.args.args if a.arg != "self"]
                first_default_idx = len(non_self_args) - len(defaults)
                for i, default in enumerate(defaults):
                    # Skip None defaults - they're already undefined/null in JS
                    if isinstance(default, ast.Constant) and default.value is None:
                        continue
                    arg_name = self._safe_name(non_self_args[first_default_idx + i].arg)
                    default_val = self.visit_expr(default)
                    self.emit(f"if ({arg_name} == null) {{ {arg_name} = {default_val}; }}")
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
                args_use_self = any(
                    "self" in ast.dump(arg) for arg in super_args
                )
                if args_use_self:
                    # Emit super() with no args first
                    self.emit("super();")
                else:
                    self.visit(super_stmt)
            else:
                self.emit("super();")
            emit_defaults()  # After super() for constructors
            for stmt in other_stmts:
                self.visit(stmt)
        else:
            emit_defaults()  # At start for regular methods
            for stmt in node.body:
                self.visit(stmt)
        self.in_class_body = old_in_class
        self.in_method = old_in_method
        self.declared_vars = old_declared
        self.indent -= 1
        self.emit("}")
        self.emit("")

    def visit_Return(self, node: ast.Return):
        if node.value:
            self.emit(f"return {self.visit_expr(node.value)};")
        else:
            self.emit("return;")

    def visit_Assign(self, node: ast.Assign):
        target = self.visit_expr(node.targets[0])
        value = self.visit_expr(node.value)
        if isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            if self.in_class_body:
                self.emit(f"{target} = {value};")
            elif var_name in self.declared_vars:
                self.emit(f"{target} = {value};")
            else:
                self.declared_vars.add(var_name)
                self.emit(f"var {target} = {value};")
        else:
            self.emit(f"{target} = {value};")

    def visit_AnnAssign(self, node: ast.AnnAssign):
        target = self.visit_expr(node.target)
        if node.value:
            value = self.visit_expr(node.value)
            var_name = node.target.id if isinstance(node.target, ast.Name) else None
            if self.in_class_body:
                self.emit(f"{target} = {value};")
            elif var_name and var_name in self.declared_vars:
                self.emit(f"{target} = {value};")
            else:
                if var_name:
                    self.declared_vars.add(var_name)
                self.emit(f"var {target} = {value};")

    def visit_AugAssign(self, node: ast.AugAssign):
        target = self.visit_expr(node.target)
        op = self.visit_op(node.op)
        value = self.visit_expr(node.value)
        self.emit(f"{target} {op}= {value};")

    def visit_If(self, node: ast.If):
        self._emit_if(node, is_elif=False)

    def _emit_if(self, node: ast.If, is_elif: bool):
        test = self.visit_expr(node.test)
        # Handle self.attr truthiness checks - in Python [] is falsy but in JS it's truthy
        # Only add length check for known array-like attributes
        array_attrs = {"redirects", "parts", "elements", "words", "patterns", "commands"}
        if (isinstance(node.test, ast.Attribute)
            and isinstance(node.test.value, ast.Name)
            and node.test.value.id == "self"
            and node.test.attr in array_attrs):
            test = f"{test} && {test}.length"
        if is_elif:
            self.emit_raw("    " * self.indent + f"}} else if ({test}) {{")
        else:
            self.emit(f"if ({test}) {{")
        self.indent += 1
        for stmt in node.body:
            self.visit(stmt)
        self.indent -= 1
        if node.orelse:
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                self._emit_if(node.orelse[0], is_elif=True)
            else:
                self.emit("} else {")
                self.indent += 1
                for stmt in node.orelse:
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
            self.visit(stmt)
        self.indent -= 1
        self.emit("}")

    def visit_For(self, node: ast.For):
        target = self.visit_expr(node.target)
        # Track loop variable as declared
        if isinstance(node.target, ast.Name):
            self.declared_vars.add(node.target.id)
        iter_expr = node.iter
        # Handle range() specially
        if isinstance(iter_expr, ast.Call) and isinstance(iter_expr.func, ast.Name) and iter_expr.func.id == "range":
            args = iter_expr.args
            if len(args) == 1:
                self.emit(f"for (var {target} = 0; {target} < {self.visit_expr(args[0])}; {target}++) {{")
            elif len(args) == 2:
                self.emit(f"for (var {target} = {self.visit_expr(args[0])}; {target} < {self.visit_expr(args[1])}; {target}++) {{")
            else:
                start, end, step = args
                # Check if step is negative for proper comparison and decrement
                is_negative = False
                if isinstance(step, ast.UnaryOp) and isinstance(step.op, ast.USub):
                    is_negative = True
                elif isinstance(step, ast.Constant) and step.value < 0:
                    is_negative = True
                if is_negative:
                    self.emit(f"for (var {target} = {self.visit_expr(start)}; {target} > {self.visit_expr(end)}; {target}--) {{")
                else:
                    step_val = self.visit_expr(step)
                    self.emit(f"for (var {target} = {self.visit_expr(start)}; {target} < {self.visit_expr(end)}; {target} += {step_val}) {{")
        else:
            self.emit(f"for (var {target} of {self.visit_expr(iter_expr)}) {{")
        self.indent += 1
        for stmt in node.body:
            self.visit(stmt)
        self.indent -= 1
        self.emit("}")

    def visit_Expr(self, node: ast.Expr):
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
            self.visit(stmt)
        self.indent -= 1
        for handler in node.handlers:
            name = handler.name or "_"
            self.emit(f"}} catch ({name}) {{")
            self.indent += 1
            for stmt in handler.body:
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
            "True": "true", "False": "false", "None": "null", "self": "this",
            "Exception": "Error", "NotImplementedError": 'new Error("Not implemented")',
        }
        name = mapping.get(node.id, node.id)
        return self._safe_name(name)

    def visit_expr_Constant(self, node: ast.Constant) -> str:
        if isinstance(node.value, str):
            escaped = node.value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
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

    def visit_expr_Subscript(self, node: ast.Subscript) -> str:
        value = self.visit_expr(node.value)
        if isinstance(node.slice, ast.Slice):
            lower = self.visit_expr(node.slice.lower) if node.slice.lower else "0"
            upper = self.visit_expr(node.slice.upper) if node.slice.upper else ""
            if upper:
                return f"{value}.slice({lower}, {upper})"
            return f"{value}.slice({lower})"
        return f"{value}[{self.visit_expr(node.slice)}]"

    def visit_expr_Call(self, node: ast.Call) -> str:
        # Combine positional and keyword args (JS doesn't have kwargs, so treat as positional)
        all_args = [self.visit_expr(a) for a in node.args]
        for kw in node.keywords:
            all_args.append(self.visit_expr(kw.value))
        args = ", ".join(all_args)
        # Handle method calls
        if isinstance(node.func, ast.Attribute):
            # Special case: super().__init__(args) -> super(args)
            if (node.func.attr == "__init__"
                and isinstance(node.func.value, ast.Call)
                and isinstance(node.func.value.func, ast.Name)
                and node.func.value.func.id == "super"):
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
                    chars = self.visit_expr(node.args[0])
                    return f'{obj}.replace(new RegExp("^[" + {chars} + "]+"), "")'
                return f"{obj}.trimStart()"
            # Handle rstrip with character set argument
            if method == "rstrip":
                if len(node.args) == 1:
                    chars = self.visit_expr(node.args[0])
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
                    return f"({obj}[{key}] !== undefined ? {obj}[{key}] : {default})"
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
                    checks = [f"{obj}.endsWith({self.visit_expr(elt)})" for elt in node.args[0].elts]
                    return f"({' || '.join(checks)})"
            if method == "startswith" and len(node.args) == 1:
                if isinstance(node.args[0], (ast.Tuple, ast.List)):
                    checks = [f"{obj}.startsWith({self.visit_expr(elt)})" for elt in node.args[0].elts]
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
                return f"parseInt({args}, 10)"
            if name == "ord":
                return f"{args}.charCodeAt(0)"
            if name == "chr":
                # Use fromCodePoint for full unicode support (including > 0xFFFF)
                return f"String.fromCodePoint({args})"
            if name == "isinstance":
                return f"{node.args[0].id} instanceof {self.visit_expr(node.args[1])}"
            if name == "getattr":
                obj = self.visit_expr(node.args[0])
                attr = self.visit_expr(node.args[1])
                if len(node.args) >= 3:
                    default = self.visit_expr(node.args[2])
                    return f"({obj}[{attr}] !== undefined ? {obj}[{attr}] : {default})"
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
            if name in self.class_names:
                return f"new {self._safe_name(name)}({args})"
            # Convert snake_case function names to camelCase
            if "_" in name:
                name = self._camel_case(name)
            return f"{name}({args})"
        return f"{self.visit_expr(node.func)}({args})"

    def visit_expr_BinOp(self, node: ast.BinOp) -> str:
        left = self.visit_expr(node.left)
        right = self.visit_expr(node.right)
        op = self.visit_op(node.op)
        return f"({left} {op} {right})"

    def visit_expr_Compare(self, node: ast.Compare) -> str:
        # Handle single comparison with in/not in specially
        if len(node.ops) == 1:
            left = self.visit_expr(node.left)
            right = self.visit_expr(node.comparators[0])
            op = node.ops[0]
            if isinstance(op, ast.In):
                return f"{right}.has({left})"
            if isinstance(op, ast.NotIn):
                return f"!{right}.has({left})"
        result = self.visit_expr(node.left)
        for op, comparator in zip(node.ops, node.comparators):
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
            return f"!{operand}"
        if isinstance(node.op, ast.USub):
            return f"-{operand}"
        return f"/* TODO: UnaryOp {node.op} */{operand}"

    def visit_expr_IfExp(self, node: ast.IfExp) -> str:
        test = self.visit_expr(node.test)
        body = self.visit_expr(node.body)
        orelse = self.visit_expr(node.orelse)
        return f"({test} ? {body} : {orelse})"

    def visit_expr_List(self, node: ast.List) -> str:
        elements = ", ".join(self.visit_expr(e) for e in node.elts)
        return f"[{elements}]"

    def visit_expr_Dict(self, node: ast.Dict) -> str:
        pairs = []
        for k, v in zip(node.keys, node.values):
            pairs.append(f"{self.visit_expr(k)}: {self.visit_expr(v)}")
        return "{" + ", ".join(pairs) + "}"

    def visit_expr_Tuple(self, node: ast.Tuple) -> str:
        elements = ", ".join(self.visit_expr(e) for e in node.elts)
        return f"[{elements}]"

    def visit_expr_Set(self, node: ast.Set) -> str:
        elements = ", ".join(self.visit_expr(e) for e in node.elts)
        return f"new Set([{elements}])"

    def visit_op(self, op: ast.operator) -> str:
        ops = {
            ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
            ast.FloorDiv: "Math.floor(/", ast.Mod: "%", ast.Pow: "**",
            ast.LShift: "<<", ast.RShift: ">>", ast.BitOr: "|",
            ast.BitXor: "^", ast.BitAnd: "&",
        }
        return ops.get(type(op), "/* ? */")

    def visit_cmpop(self, op: ast.cmpop) -> str:
        ops = {
            ast.Eq: "===", ast.NotEq: "!==", ast.Lt: "<", ast.LtE: "<=",
            ast.Gt: ">", ast.GtE: ">=", ast.Is: "==", ast.IsNot: "!=",  # == for is None checks (handles undefined)
            ast.In: "in", ast.NotIn: "not in",
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
