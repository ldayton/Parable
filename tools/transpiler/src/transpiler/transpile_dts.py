"""Generate TypeScript definitions from parable.js."""

import re
import sys


def extract_classes(js_source: str) -> list[dict]:
    """Extract class definitions from JavaScript source."""
    classes = []

    # Match class definitions with their constructor bodies
    class_pattern = re.compile(
        r"^class\s+(\w+)\s+extends\s+(\w+)\s*\{(.*?)^\}",
        re.MULTILINE | re.DOTALL,
    )

    for match in class_pattern.finditer(js_source):
        name = match.group(1)
        parent = match.group(2)
        body = match.group(3)

        # Extract constructor
        ctor_match = re.search(
            r"constructor\s*\(([^)]*)\)\s*\{(.*?)\n\t\}",
            body,
            re.DOTALL,
        )
        if not ctor_match:
            continue

        params = [p.strip() for p in ctor_match.group(1).split(",") if p.strip()]
        ctor_body = ctor_match.group(2)

        # Extract kind literal
        kind_match = re.search(r'this\.kind\s*=\s*"([^"]+)"', ctor_body)
        kind = kind_match.group(1) if kind_match else None

        # Extract property assignments
        props = []
        for prop_match in re.finditer(r"this\.(\w+)\s*=\s*(\w+)", ctor_body):
            prop_name = prop_match.group(1)
            prop_value = prop_match.group(2)
            if prop_name != "kind":
                props.append((prop_name, prop_value))

        classes.append(
            {
                "name": name,
                "parent": parent,
                "kind": kind,
                "params": params,
                "props": props,
            }
        )

    return classes


def infer_type(prop_name: str, class_name: str) -> str:
    """Infer TypeScript type from property name and class context."""
    # Array types
    if prop_name in ("words", "redirects", "parts", "elements", "patterns", "commands"):
        if prop_name == "words":
            return "Word[]"
        if prop_name == "redirects":
            return "(Redirect | HereDoc)[]"
        if prop_name == "patterns":
            return "CasePattern[]"
        if prop_name == "elements":
            return "Word[]"
        if prop_name == "commands":
            return "Node[]"
        if prop_name == "parts":
            if class_name == "ArithConcat":
                return "ArithNode[]"
            return "Node[]"

    # Node types
    if prop_name in ("body", "then_body", "else_body", "pipeline", "command"):
        if class_name in ("ConditionalExpr",):
            return "CondNode | string"
        if prop_name in ("else_body", "pipeline"):
            return "Node | null"
        return "Node"

    if prop_name == "word":
        return "Word"

    if prop_name == "target":
        if class_name == "Redirect":
            return "Word"
        return "ArithNode"

    if prop_name in (
        "left",
        "right",
        "operand",
        "expression",
        "index",
        "if_true",
        "if_false",
        "condition",
        "value",
    ):
        # ArithDeprecated.expression is a string (raw text), not ArithNode
        if class_name == "ArithDeprecated" and prop_name == "expression":
            return "string"
        if class_name.startswith("Arith") or class_name in (
            "ArithmeticExpansion",
            "ArithmeticCommand",
        ):
            if prop_name == "expression":
                return "ArithNode | null"
            return "ArithNode"
        if class_name.startswith("Cond") or class_name in ("UnaryTest", "BinaryTest"):
            if class_name in ("UnaryTest", "BinaryTest"):
                return "Word"
            return "CondNode"
        return "Node"

    if prop_name == "inner":
        return "CondNode"

    # String types
    if prop_name in (
        "value",
        "name",
        "op",
        "param",
        "arg",
        "variable",
        "pattern",
        "delimiter",
        "content",
        "text",
        "char",
        "array",
        "terminator",
        "message",
        "init",
        "cond",
        "incr",
        "raw_content",
        "direction",
    ):
        if prop_name == "direction":
            return '"<" | ">"'
        if prop_name in ("arg", "op", "init", "cond", "incr", "name"):
            if class_name in ("ParamExpansion", "ParamIndirect", "ForArith", "Coproc"):
                return "string | null"
        return "string"

    # Boolean types
    if prop_name in ("posix", "brace", "strip_tabs", "quoted", "complete"):
        return "boolean"

    # Number types
    if prop_name in ("fd", "pos", "line"):
        return "number | null"

    return "unknown"


def generate_dts(classes: list[dict]) -> str:
    """Generate TypeScript definitions from extracted classes."""
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

    # Separate by category
    error_classes = [
        c for c in classes if c["parent"] == "Error" or c["name"] == "MatchedPairError"
    ]
    node_classes = [c for c in classes if c["parent"] == "Node"]

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

    # Group nodes by category
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

    # Build lookup
    class_by_name = {c["name"]: c for c in node_classes}

    for cat, names in categories.items():
        lines.append(f"// {category_names[cat]}")
        for name in names:
            if name not in class_by_name:
                continue
            cls = class_by_name[name]
            lines.append(f"export interface {name} extends NodeBase {{")
            if cls["kind"]:
                lines.append(f'\treadonly kind: "{cls["kind"]}";')
            for prop_name, _ in cls["props"]:
                prop_type = infer_type(prop_name, name)
                lines.append(f"\treadonly {prop_name}: {prop_type};")
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

    # Main Node union (excluding ArithNode internals and CondNode internals)
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
    """Generate TypeScript definitions from parable.js."""
    if len(sys.argv) < 2:
        print("Usage: transpiler --generate-dts <parable.js>", file=sys.stderr)
        sys.exit(1)

    js_path = sys.argv[1]
    with open(js_path) as f:
        js_source = f.read()

    classes = extract_classes(js_source)
    dts = generate_dts(classes)
    print(dts)


if __name__ == "__main__":
    main()
