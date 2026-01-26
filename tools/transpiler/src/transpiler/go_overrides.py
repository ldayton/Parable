"""Type override dictionaries for Go transpiler."""

# Override parameter types for functions with bare "list" annotations
# Maps (method_name, param_name) -> Go type
# Use *[]T (pointer-to-slice) for parameters that are mutated by the callee
PARAM_TYPE_OVERRIDES: dict[tuple[str, str], str] = {
    ("_read_bracket_expression", "chars"): "*[]string",
    ("_read_bracket_expression", "parts"): "*[]Node",
    ("_parse_dollar_expansion", "chars"): "*[]string",
    ("_parse_dollar_expansion", "parts"): "*[]Node",
    ("_scan_double_quote", "chars"): "*[]string",
    ("_scan_double_quote", "parts"): "*[]Node",
    ("restore_from", "saved_stack"): "[]*ParseContext",
    ("copy_stack", "_result"): "[]*ParseContext",  # return type hint
    # SavedParserState constructor parameters
    ("__init__", "pending_heredocs"): "[]Node",
    # Token constructor parameters
    ("__init__", "parts"): "[]Node",
    ("__init__", "ctx_stack"): "[]*ParseContext",
    # List class methods - parts is always []Node, op_names is map[string]string
    ("_to_sexp_with_precedence", "parts"): "[]Node",
    ("_to_sexp_with_precedence", "op_names"): "map[string]string",
    ("_to_sexp_amp_and_higher", "parts"): "[]Node",
    ("_to_sexp_amp_and_higher", "op_names"): "map[string]string",
    ("_to_sexp_and_or", "parts"): "[]Node",
    ("_to_sexp_and_or", "op_names"): "map[string]string",
    # Redirect handling - only reads, no mutation
    ("_append_redirects", "redirects"): "[]Node",
    # Bytearray mutation - needs pointer to avoid losing appends
    ("_append_with_ctlesc", "result"): "*[]byte",
}

# Override field types for fields without proper annotations
# Maps (class_name, field_name) -> Go type (field_name is Python name, lowercase)
FIELD_TYPE_OVERRIDES: dict[tuple[str, str], str] = {
    ("Lexer", "_word_context"): "int",
    ("Parser", "_word_context"): "int",
    # Source_runes for rune-based indexing (Unicode support)
    ("Lexer", "source_runes"): "[]rune",
    ("Parser", "source_runes"): "[]rune",
    # Untyped list fields that need concrete slice types
    ("SavedParserState", "pending_heredocs"): "[]Node",
    ("SavedParserState", "ctx_stack"): "[]*ParseContext",
    ("SavedParserState", "token_history"): "[]*Token",
    ("Parser", "_token_history"): "[]*Token",
    # Dynamically created fields for arithmetic parsing
    ("Parser", "_arith_src"): "string",
    ("Parser", "_arith_pos"): "int",
    # QuoteState uses tuple stack - use custom struct
    ("QuoteState", "_stack"): "[]quoteStackEntry",
    ("Parser", "_arith_len"): "int",
}

# Override return types for methods that return generic list
# Maps method_name -> Go return type
RETURN_TYPE_OVERRIDES: dict[str, str] = {
    "_collect_cmdsubs": "[]Node",
    "_collect_procsubs": "[]Node",
    "_collect_redirects": "[]Node",
    "copy_stack": "[]*ParseContext",
    "parse_for": "Node",  # Returns For | ForArith | None
}

# Tuple element types for functions returning tuples with typed elements
# Maps function_name -> {element_index -> Go type}
TUPLE_ELEMENT_TYPES: dict[str, dict[int, str]] = {
    "_ConsumeSingleQuote": {0: "int", 1: "[]string"},
    "_ConsumeDoubleQuote": {0: "int", 1: "[]string"},
    "_ConsumeBracketClass": {0: "int", 1: "[]string"},
}

# Union field discriminators for Node | str union types
# Maps (receiver_type, field_name) -> (discriminator_var, nil_type, non_nil_type)
# discriminator_var is the variable that holds getattr(field, "kind", nil)
# field_name is the Python name (lowercase), not the Go name
UNION_FIELDS: dict[tuple[str, str], tuple[str, str, str]] = {
    ("ConditionalExpr", "body"): ("bodyKind", "string", "Node"),
}
