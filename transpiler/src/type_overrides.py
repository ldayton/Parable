"""Remaining type overrides for parable.py transpilation.

Most type overrides have been eliminated by improving type inference in the frontend.
Only MODULE_CONSTANTS and RETURN_TYPE_OVERRIDES remain.
"""

from .ir import BYTE, Slice, Type

# Override return types for methods that return generic list
# Maps method_name -> IR return type
# _string_to_bytes returns list[int] in Python but should be []byte in Go
RETURN_TYPE_OVERRIDES: dict[str, Type] = {
    "_string_to_bytes": Slice(BYTE),
}

# Module-level constants that need custom emission (empty - all constants auto-detected)
MODULE_CONSTANTS: dict[str, tuple[Type, str]] = {}
