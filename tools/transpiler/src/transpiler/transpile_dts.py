"""Generate TypeScript definitions from parable.py type annotations."""

import ast
import re
import sys
from pathlib import Path


def extract_python_types(py_source: str) -> dict[str, dict[str, str]]:
    """Extract class type annotations from Python source."""
    tree = ast.parse(py_source)
    classes = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        # Only process Node subclasses
        bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
        if "Node" not in bases and node.name != "Node":
            continue

        props = {}
        for item in node.body:
            # Class-level annotations (not in __init__)
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                prop_name = item.target.id
                prop_type = ast.unparse(item.annotation)
                props[prop_name] = prop_type

        if props or node.name == "Node":
            classes[node.name] = props

    return classes


def py_type_to_ts(py_type: str) -> str:
    """Convert Python type annotation to TypeScript type."""
    # Handle list types first (before splitting on |)
    if py_type.startswith("list["):
        # Find matching bracket
        depth = 0
        for i, c in enumerate(py_type):
            if c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    inner = py_type[5:i]
                    rest = py_type[i + 1 :]
                    ts_inner = py_type_to_ts(inner)
                    if " | " in ts_inner:
                        ts_list = f"({ts_inner})[]"
                    else:
                        ts_list = f"{ts_inner}[]"
                    if rest:
                        # Handle e.g., list[X] | None
                        return py_type_to_ts(ts_list + rest)
                    return ts_list

    # Handle None -> null
    if py_type == "None":
        return "null"
    if py_type == "null":
        return "null"

    # Handle Union types
    if py_type.startswith("Union["):
        inner = py_type[6:-1]
        parts = _split_union(inner)
        ts_parts = [py_type_to_ts(p.strip()) for p in parts]
        return " | ".join(ts_parts)

    # Handle X | Y syntax (but not inside brackets)
    if " | " in py_type:
        parts = _split_union_bar(py_type)
        ts_parts = [py_type_to_ts(p.strip()) for p in parts]
        return " | ".join(ts_parts)

    # Basic type mappings
    mappings = {
        "str": "string",
        "int": "number",
        "bool": "boolean",
        "float": "number",
    }

    return mappings.get(py_type, py_type)


def _split_union_bar(s: str) -> list[str]:
    """Split on | respecting brackets."""
    parts = []
    depth = 0
    current = ""
    i = 0
    while i < len(s):
        c = s[i]
        if c == "[":
            depth += 1
            current += c
        elif c == "]":
            depth -= 1
            current += c
        elif c == "|" and depth == 0 and i > 0 and s[i - 1] == " ":
            # Found ' | '
            parts.append(current.rstrip())
            current = ""
            i += 2  # Skip '| '
            continue
        else:
            current += c
        i += 1
    if current.strip():
        parts.append(current.strip())
    return parts


def _split_union(s: str) -> list[str]:
    """Split union type string, respecting nested brackets."""
    parts = []
    depth = 0
    current = ""
    for c in s:
        if c == "[":
            depth += 1
            current += c
        elif c == "]":
            depth -= 1
            current += c
        elif c == "," and depth == 0:
            parts.append(current.strip())
            current = ""
        else:
            current += c
    if current.strip():
        parts.append(current.strip())
    return parts


def extract_js_classes(js_source: str) -> list[dict]:
    """Extract class definitions from JavaScript source for structure."""
    classes = []

    class_pattern = re.compile(
        r"^class\s+(\w+)\s+extends\s+(\w+)\s*\{(.*?)^\}",
        re.MULTILINE | re.DOTALL,
    )

    for match in class_pattern.finditer(js_source):
        name = match.group(1)
        parent = match.group(2)
        body = match.group(3)

        ctor_match = re.search(
            r"constructor\s*\(([^)]*)\)\s*\{(.*?)\n\t\}",
            body,
            re.DOTALL,
        )
        if not ctor_match:
            continue

        ctor_body = ctor_match.group(2)

        kind_match = re.search(r'this\.kind\s*=\s*"([^"]+)"', ctor_body)
        kind = kind_match.group(1) if kind_match else None

        props = []
        for prop_match in re.finditer(r"this\.(\w+)\s*=\s*(\w+)", ctor_body):
            prop_name = prop_match.group(1)
            if prop_name != "kind":
                props.append(prop_name)

        classes.append(
            {
                "name": name,
                "parent": parent,
                "kind": kind,
                "props": props,
            }
        )

    return classes


def generate_dts(js_classes: list[dict], py_types: dict[str, dict[str, str]]) -> str:
    """Generate TypeScript definitions from JS structure and Python types."""
    lines = [
        "/**",
        " * Parable.js - A recursive descent parser for bash.",
        " *",
        " * MIT License - https://github.com/ldayton/Parable",
        " *",
        " * @packageDocumentation",
        " */",
        "",
    ]

    error_classes = [
        c for c in js_classes if c["parent"] == "Error" or c["name"] == "MatchedPairError"
    ]
    node_classes = [c for c in js_classes if c["parent"] == "Node"]

    # Error classes
    lines.append("// Error classes")
    for cls in error_classes:
        if cls["name"] == "ParseError":
            lines.extend(
                [
                    "export class ParseError extends Error {",
                    "\treadonly message: string;",
                    "\treadonly pos: number | null;",
                    "\treadonly line: number | null;",
                    "}",
                    "",
                ]
            )

    # Base interface
    lines.extend(
        [
            "// Base node interface",
            "interface NodeBase {",
            "\treadonly kind: string;",
            "\ttoSexp(): string;",
            "}",
            "",
        ]
    )

    # Categories
    categories = {
        "structural": [
            "Word",
            "Command",
            "Pipeline",
            "List",
            "Operator",
            "PipeBoth",
            "Empty",
            "Comment",
        ],
        "redirect": ["Redirect", "HereDoc"],
        "compound": [
            "Subshell",
            "BraceGroup",
            "If",
            "While",
            "Until",
            "For",
            "ForArith",
            "Select",
            "Case",
            "CasePattern",
            "FunctionNode",
        ],
        "expansion": [
            "ParamExpansion",
            "ParamLength",
            "ParamIndirect",
            "CommandSubstitution",
            "ArithmeticExpansion",
            "ProcessSubstitution",
        ],
        "arithmetic": [
            "ArithNumber",
            "ArithEmpty",
            "ArithVar",
            "ArithBinaryOp",
            "ArithUnaryOp",
            "ArithPreIncr",
            "ArithPostIncr",
            "ArithPreDecr",
            "ArithPostDecr",
            "ArithAssign",
            "ArithTernary",
            "ArithComma",
            "ArithSubscript",
            "ArithEscape",
            "ArithDeprecated",
            "ArithConcat",
            "ArithmeticCommand",
        ],
        "conditional": [
            "ConditionalExpr",
            "UnaryTest",
            "BinaryTest",
            "CondAnd",
            "CondOr",
            "CondNot",
            "CondParen",
        ],
        "quote": ["AnsiCQuote", "LocaleString"],
        "special": ["Negation", "Time", "ArrayNode", "Coproc"],
    }

    category_names = {
        "structural": "Structural nodes",
        "redirect": "Redirections",
        "compound": "Compound commands",
        "expansion": "Expansions",
        "arithmetic": "Arithmetic expression nodes",
        "conditional": "Conditional expression nodes",
        "quote": "Quote nodes",
        "special": "Special nodes",
    }

    # Map JS class name to Python class name
    js_to_py = {
        "FunctionNode": "Function",
        "ArrayNode": "Array",
    }

    class_by_name = {c["name"]: c for c in node_classes}

    for cat, names in categories.items():
        lines.append(f"// {category_names[cat]}")
        for js_name in names:
            if js_name not in class_by_name:
                continue
            cls = class_by_name[js_name]
            py_name = js_to_py.get(js_name, js_name)
            py_props = py_types.get(py_name, {})

            lines.append(f"export interface {js_name} extends NodeBase {{")
            if cls["kind"]:
                lines.append(f'\treadonly kind: "{cls["kind"]}";')

            for prop_name in cls["props"]:
                # Map JS prop name to Python prop name
                py_prop = prop_name
                if py_prop == "variable":
                    py_prop = "var"

                if py_prop in py_props:
                    ts_type = py_type_to_ts(py_props[py_prop])
                else:
                    # Fallback for unmapped properties
                    ts_type = "unknown"

                lines.append(f"\treadonly {prop_name}: {ts_type};")
            lines.append("}")
            lines.append("")

    # Union types
    arith_types = [n for n in categories["arithmetic"] if n != "ArithmeticCommand"]
    cond_types = [n for n in categories["conditional"] if n != "ConditionalExpr"]

    lines.extend(
        [
            "// Union type for arithmetic expression nodes",
            "export type ArithNode =",
        ]
    )
    for i, name in enumerate(arith_types):
        sep = ";" if i == len(arith_types) - 1 else ""
        lines.append(f"\t| {name}{sep}")
    lines.append("")

    lines.extend(
        [
            "// Union type for conditional expression nodes",
            "export type CondNode =",
        ]
    )
    for i, name in enumerate(cond_types):
        sep = ";" if i == len(cond_types) - 1 else ""
        lines.append(f"\t| {name}{sep}")
    lines.append("")

    # Main Node union
    excluded = set(arith_types) | set(cond_types)
    all_node_names = []
    for names in categories.values():
        all_node_names.extend(names)
    main_nodes = [n for n in all_node_names if n not in excluded]

    lines.extend(
        [
            "// Union type for all AST nodes",
            "export type Node =",
        ]
    )
    for i, name in enumerate(main_nodes):
        sep = ";" if i == len(main_nodes) - 1 else ""
        lines.append(f"\t| {name}{sep}")
    lines.append("")

    # Parse function
    lines.extend(
        [
            "/**",
            " * Parse bash source code into an AST.",
            " * @param source - The bash source code to parse",
            " * @param extglob - Enable extended glob patterns (default: false)",
            " * @returns An array of parsed AST nodes",
            " * @throws {ParseError} If the source contains syntax errors",
            " */",
            "export function parse(source: string, extglob?: boolean): Node[];",
            "",
        ]
    )

    return "\n".join(lines)


def main():
    """Generate TypeScript definitions from parable.js and parable.py."""
    if len(sys.argv) < 2:
        print("Usage: transpiler --transpile-dts <parable.js> [parable.py]", file=sys.stderr)
        sys.exit(1)

    js_path = Path(sys.argv[1]).resolve()
    if len(sys.argv) >= 3:
        py_path = Path(sys.argv[2]).resolve()
    else:
        py_path = js_path.parent / "parable.py"

    with open(js_path) as f:
        js_source = f.read()

    with open(py_path) as f:
        py_source = f.read()

    js_classes = extract_js_classes(js_source)
    py_types = extract_python_types(py_source)
    dts = generate_dts(js_classes, py_types)
    print(dts)


if __name__ == "__main__":
    main()
