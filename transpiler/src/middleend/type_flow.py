"""Type flow analysis: compute types at control flow join points."""

from src.ir import InterfaceRef, StructRef, Type


def join_types(t1: Type | None, t2: Type | None) -> Type | None:
    """Compute joined type for variables assigned in multiple branches.

    For hoisting variables assigned in multiple branches:
    - If one branch assigns nil (InterfaceRef("any")) and another assigns Node, use Node
    - Go interfaces are nil-able, so InterfaceRef("Node") can hold nil without widening
    - If both are different Node subtypes, use InterfaceRef("Node") as the common type
    """
    if t1 is None:
        return t2
    if t2 is None:
        return t1
    if t1 == t2:
        return t1
    # Prefer named interface over "any" (nil gets typed as InterfaceRef("any"))
    if isinstance(t1, InterfaceRef) and t1.name == "any" and isinstance(t2, InterfaceRef):
        return t2
    if isinstance(t2, InterfaceRef) and t2.name == "any" and isinstance(t1, InterfaceRef):
        return t1
    # Prefer any concrete type over InterfaceRef("any")
    if isinstance(t1, InterfaceRef) and t1.name == "any":
        return t2
    if isinstance(t2, InterfaceRef) and t2.name == "any":
        return t1
    # If one is InterfaceRef("Node") and other is StructRef, use InterfaceRef("Node")
    if isinstance(t1, InterfaceRef) and t1.name == "Node":
        return t1
    if isinstance(t2, InterfaceRef) and t2.name == "Node":
        return t2
    # If both are different StructRefs, they're likely Node subtypes - use InterfaceRef("Node")
    # This handles cases like BraceGroup vs ArithmeticCommand assigned to same variable
    if isinstance(t1, StructRef) and isinstance(t2, StructRef) and t1.name != t2.name:
        return InterfaceRef("Node")
    # Otherwise keep first type (arbitrary but deterministic)
    return t1
