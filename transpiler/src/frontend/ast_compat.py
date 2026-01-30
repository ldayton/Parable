"""Compatibility layer for dict-based AST."""

ASTNode = dict[str, object]


def dict_walk(node: ASTNode) -> list[ASTNode]:
    """Walk dict-based AST like ast.walk(), returns list of all nodes."""
    result: list[ASTNode] = [node]
    keys = list(node.keys())
    i = 0
    while i < len(keys):
        key = keys[i]
        if not key.startswith("_"):
            value = node[key]
            if isinstance(value, dict) and "_type" in value:
                result = result + dict_walk(value)
            elif isinstance(value, list):
                j = 0
                while j < len(value):
                    item = value[j]
                    if isinstance(item, dict) and "_type" in item:
                        result = result + dict_walk(item)
                    j += 1
        i += 1
    return result


def node_type(node: ASTNode) -> str:
    """Get node type string."""
    return node.get("_type", "")


def is_type(node: object, type_names: list[str]) -> bool:
    """Check if node is one of the given AST types."""
    if not isinstance(node, dict):
        return False
    return node.get("_type") in type_names


def op_type(op: object) -> str:
    """Get operator type string from op dict."""
    if isinstance(op, dict):
        return op.get("_type", "")
    return ""


def get(node: ASTNode, attr: str, default: object = None) -> object:
    """Get attribute from AST node dict."""
    return node.get(attr, default)
