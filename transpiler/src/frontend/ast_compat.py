"""Compatibility layer for dict-based AST."""

from typing import Iterator

ASTNode = dict[str, object]


def dict_walk(node: ASTNode) -> Iterator[ASTNode]:
    """Walk dict-based AST like ast.walk()."""
    yield node
    for key, value in node.items():
        if key.startswith("_"):
            continue
        if isinstance(value, dict) and "_type" in value:
            yield from dict_walk(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and "_type" in item:
                    yield from dict_walk(item)


def node_type(node: ASTNode) -> str:
    """Get node type string."""
    return node.get("_type", "")


def is_type(node: object, *type_names: str) -> bool:
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
