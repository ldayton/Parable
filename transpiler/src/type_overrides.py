"""Type override dictionaries for parable.py transpilation.

These override Python's loose type hints with concrete IR types.
Used by the frontend when Python annotations are ambiguous (e.g., bare `list`).
"""

from .ir import (
    BOOL,
    INT,
    RUNE,
    STRING,
    BYTE,
    Map,
    Pointer,
    Slice,
    StructRef,
    Tuple,
    Type,
)

# Override parameter types for functions with bare "list" annotations
# Maps (method_name, param_name) -> IR type
# Use Pointer(Slice(...)) for parameters that are mutated by the callee
PARAM_TYPE_OVERRIDES: dict[tuple[str, str], Type] = {
    ("_read_bracket_expression", "chars"): Pointer(Slice(STRING)),
    ("_read_bracket_expression", "parts"): Pointer(Slice(StructRef("Node"))),
    ("_parse_dollar_expansion", "chars"): Pointer(Slice(STRING)),
    ("_parse_dollar_expansion", "parts"): Pointer(Slice(StructRef("Node"))),
    ("_scan_double_quote", "chars"): Pointer(Slice(STRING)),
    ("_scan_double_quote", "parts"): Pointer(Slice(StructRef("Node"))),
    ("restore_from", "saved_stack"): Slice(Pointer(StructRef("ParseContext"))),
    ("copy_stack", "_result"): Slice(Pointer(StructRef("ParseContext"))),  # return type hint
    # SavedParserState constructor parameters
    ("__init__", "pending_heredocs"): Slice(StructRef("Node")),
    # Token constructor parameters
    ("__init__", "parts"): Slice(StructRef("Node")),
    ("__init__", "ctx_stack"): Slice(Pointer(StructRef("ParseContext"))),
    # List class methods - parts is always []Node, op_names is map[string]string
    ("_to_sexp_with_precedence", "parts"): Slice(StructRef("Node")),
    ("_to_sexp_with_precedence", "op_names"): Map(STRING, STRING),
    ("_to_sexp_amp_and_higher", "parts"): Slice(StructRef("Node")),
    ("_to_sexp_amp_and_higher", "op_names"): Map(STRING, STRING),
    ("_to_sexp_and_or", "parts"): Slice(StructRef("Node")),
    ("_to_sexp_and_or", "op_names"): Map(STRING, STRING),
    # Redirect handling - only reads, no mutation
    ("_append_redirects", "redirects"): Slice(StructRef("Node")),
    # Bytearray mutation - needs pointer to avoid losing appends
    ("_append_with_ctlesc", "result"): Pointer(Slice(BYTE)),
}

# Override field types for fields without proper annotations
# Maps (class_name, field_name) -> IR type (field_name is Python name, lowercase)
FIELD_TYPE_OVERRIDES: dict[tuple[str, str], Type] = {
    ("Lexer", "_word_context"): INT,
    ("Parser", "_word_context"): INT,
    # Array.elements is list[Word] - need concrete type for field access
    ("Array", "elements"): Slice(Pointer(StructRef("Word"))),
    # Source_runes for rune-based indexing (Unicode support)
    ("Lexer", "source_runes"): Slice(RUNE),
    ("Parser", "source_runes"): Slice(RUNE),
    # Untyped list fields that need concrete slice types
    ("SavedParserState", "pending_heredocs"): Slice(StructRef("Node")),
    ("SavedParserState", "ctx_stack"): Slice(Pointer(StructRef("ParseContext"))),
    ("SavedParserState", "token_history"): Slice(Pointer(StructRef("Token"))),
    ("Parser", "_token_history"): Slice(Pointer(StructRef("Token"))),
    # Dynamically created fields for arithmetic parsing
    ("Parser", "_arith_src"): STRING,
    ("Parser", "_arith_pos"): INT,
    # QuoteState uses tuple stack - use generic tuple struct
    ("QuoteState", "_stack"): Slice(Tuple((BOOL, BOOL))),
    ("Parser", "_arith_len"): INT,
}

# Override return types for methods that return generic list
# Maps method_name -> IR return type
RETURN_TYPE_OVERRIDES: dict[str, Type] = {
    "_collect_cmdsubs": Slice(StructRef("Node")),
    "_collect_procsubs": Slice(StructRef("Node")),
    "_collect_redirects": Slice(StructRef("Node")),
    "copy_stack": Slice(Pointer(StructRef("ParseContext"))),
    "parse_for": StructRef("Node"),  # Returns For | ForArith | None
}

# Tuple element types for functions returning tuples with typed elements
# Maps function_name -> {element_index -> IR type}
TUPLE_ELEMENT_TYPES: dict[str, dict[int, Type]] = {
    "_ConsumeSingleQuote": {0: INT, 1: Slice(STRING)},
    "_ConsumeDoubleQuote": {0: INT, 1: Slice(STRING)},
    "_ConsumeBracketClass": {0: INT, 1: Slice(STRING)},
}

# Union field discriminators for Node | str union types
# Maps (receiver_type, field_name) -> (discriminator_var, nil_type, non_nil_type)
# discriminator_var is the variable that holds getattr(field, "kind", nil)
# field_name is the Python name (lowercase), not the Go name
UNION_FIELDS: dict[tuple[str, str], tuple[str, Type, Type]] = {
    ("ConditionalExpr", "body"): ("bodyKind", STRING, StructRef("Node")),
}
