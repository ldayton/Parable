"""Type flow analysis: compute types at control flow join points."""

from src.ir import InterfaceRef, StructRef, Type


def join_types(t1: Type | None, t2: Type | None) -> Type | None:
    """Compute joined type for variables assigned in multiple branches.

    For hoisting variables assigned in multiple branches:
    - If one branch assigns nil (InterfaceRef("any")) and another assigns concrete, use concrete
    - Go interfaces are nil-able, so InterfaceRef can hold nil without widening
    - If both are different struct types, widen to InterfaceRef("any")
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
    # If one is a named InterfaceRef and other is StructRef, use the InterfaceRef
    if isinstance(t1, InterfaceRef) and t1.name != "any" and isinstance(t2, StructRef):
        return t1
    if isinstance(t2, InterfaceRef) and t2.name != "any" and isinstance(t1, StructRef):
        return t2
    # If both are different StructRefs, widen to "any" (we don't know their common interface)
    if isinstance(t1, StructRef) and isinstance(t2, StructRef) and t1.name != t2.name:
        return InterfaceRef("any")
    # Otherwise keep first type (arbitrary but deterministic)
    return t1
