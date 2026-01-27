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
    Interface,
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
    # Use -1 sentinel instead of *int for heredoc end position
    ("Parser", "_cmdsub_heredoc_end"): INT,
    # Token.word is *Word, not Node interface
    ("Token", "word"): Pointer(StructRef("Word")),
    # Pipeline.commands is []Node
    ("Pipeline", "commands"): Slice(Interface("Node")),
    # Command.words is []*Word (Go slices aren't covariant)
    ("Command", "words"): Slice(Pointer(StructRef("Word"))),
    # For/Select.words is []*Word | None - use slice (nil is valid)
    ("For", "words"): Slice(Pointer(StructRef("Word"))),
    ("Select", "words"): Slice(Pointer(StructRef("Word"))),
    # Redirects fields are []Node, not *[]Node (nil slice is fine in Go)
    ("For", "redirects"): Slice(StructRef("Node")),
    ("Select", "redirects"): Slice(StructRef("Node")),
    ("Subshell", "redirects"): Slice(StructRef("Node")),
    ("ArithmeticCommand", "redirects"): Slice(StructRef("Node")),
    ("Conditional", "redirects"): Slice(StructRef("Node")),
    ("BraceGroup", "redirects"): Slice(StructRef("Node")),
    # Redirect.target is Word | None -> *Word in Go
    ("Redirect", "target"): Pointer(StructRef("Word")),
}

# Override return types for methods that return generic list
# Maps method_name -> IR return type
RETURN_TYPE_OVERRIDES: dict[str, Type] = {
    "_collect_cmdsubs": Slice(StructRef("Node")),
    "_collect_procsubs": Slice(StructRef("Node")),
    "_collect_redirects": Slice(StructRef("Node")),
    "copy_stack": Slice(Pointer(StructRef("ParseContext"))),
    "parse_for": StructRef("Node"),  # Returns For | ForArith | None
    "parse_redirect": StructRef("Node"),  # Returns Redirect | HereDoc | None
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

# Fields that exist on specific Node subtypes (not in Node interface)
# Maps field_name -> list of struct names that have this field
# Used for type assertions when accessing fields on Node-typed expressions
NODE_FIELD_TYPES: dict[str, list[str]] = {
    # command field - on CommandSubstitution, ProcessSubstitution, Coproc
    "command": ["CommandSubstitution", "ProcessSubstitution", "Coproc"],
    # op field - only on Operator
    "op": ["Operator"],
    # commands field - only on Pipeline
    "commands": ["Pipeline"],
    # parts field - on List (not to be confused with Token.parts)
    # Note: List.parts needs special handling since other structs also have parts
    # value field - on Word (primary), ArithNumber, ConditionalExpr, etc.
    "value": ["Word"],
    # pipeline field - on Negation, Time
    "pipeline": ["Negation", "Time"],
    # words field - on Command (for Node-typed expressions)
    "words": ["Command"],
    # redirects field - on Command and other compound commands
    "redirects": ["Command"],
    # target field - on Redirect
    "target": ["Redirect"],
    # Arithmetic expression fields
    "operand": ["ArithUnaryOp"],
    "left": ["ArithBinaryOp"],
    "right": ["ArithBinaryOp"],
    # CasePattern fields - for case pattern handling
    "pattern": ["CasePattern"],
    "body": ["CasePattern", "For", "ForArith", "While", "Until", "Select", "Conditional"],
    "terminator": ["CasePattern"],
    # HereDoc fields accessed on Node-typed expressions
    "content": ["HereDoc"],
    "delimiter": ["HereDoc"],
}

# Methods that exist on specific Node subtypes (not in Node interface)
# Maps method_name -> struct name that has this method
# Used for type assertions when calling methods on Node-typed expressions
NODE_METHOD_TYPES: dict[str, str] = {
    # Word methods for string manipulation
    "_expand_all_ansi_c_quotes": "Word",
    "_strip_locale_string_dollars": "Word",
    "_format_command_substitutions": "Word",
    "_strip_arith_line_continuations": "Word",
    "get_cond_formatted_value": "Word",
}

# Maps kind string values to struct names
# Used for type narrowing after kind checks like `x.kind == "operator"`
KIND_TO_STRUCT: dict[str, str] = {
    "operator": "Operator",
    "cmdsub": "CommandSubstitution",
    "procsub": "ProcessSubstitution",
    "subshell": "Subshell",
    "pipe-both": "PipeBoth",
    "pipeline": "Pipeline",
    "list": "List",
    "coproc": "Coproc",
    "simple": "SimpleCommand",
    "compound": "CompoundCommand",
    "function": "FunctionDef",
    "for": "For",
    "for-arith": "ForArith",
    "while": "While",
    "until": "Until",
    "if": "If",
    "case": "Case",
    "select": "Select",
    "group": "Group",
    "word": "Word",
    "array": "Array",
    "assignment": "Assignment",
    "redirect": "Redirect",
    "heredoc": "HereDoc",
    "arith-expr": "ArithExpr",
    "arith-cmd": "ArithmeticCommand",
    "cond-expr": "ConditionalExpr",
    # Conditional test nodes
    "unary-test": "UnaryTest",
    "binary-test": "BinaryTest",
    "cond-and": "CondAnd",
    "cond-or": "CondOr",
    "cond-not": "CondNot",
    "cond-paren": "CondParen",
    "negation": "Negation",
    "time": "Time",
}

# Module-level constants that need custom emission
# Maps constant_name -> (type, go_value)
# Used for constants that can't be inferred from simple integer assignment
MODULE_CONSTANTS: dict[str, tuple[Type, str]] = {
    # Empty - RESERVED_WORDS is now emitted as a proper map[string]struct{} set
}

# Override local variable types when inference fails
# Maps (function_name, var_name) -> IR type
VAR_TYPE_OVERRIDES: dict[tuple[str, str], Type] = {
    # Empty list assigned then returned - need concrete element type
    ("_collect_redirects", "redirects"): Slice(StructRef("Node")),
    # Tuple element types inferred incorrectly
    ("_read_heredoc_body", "pending_heredocs"): Slice(Tuple((STRING, BOOL))),
    # Hoisted variables with wrong type inference (interface{} instead of Node)
    ("parse_if", "else_body"): Interface("Node"),
    ("parse_if", "inner_else"): Interface("Node"),
    ("_parse_elif_chain", "else_body"): Interface("Node"),
    # Hoisted word lists in for/select parsing (interface{} instead of []*Word)
    ("parse_for", "words"): Slice(Pointer(StructRef("Word"))),
    ("parse_select", "words"): Slice(Pointer(StructRef("Word"))),
    # Hoisted body variable in case parsing (interface{} instead of Node)
    ("parse_case", "body"): Interface("Node"),
    # Coproc body can be many different Node types
    ("parse_coproc", "body"): Interface("Node"),
    # Compound command result can be many different Node types
    ("_parse_compound_command", "result"): Interface("Node"),
    # Function body can be many different Node types
    ("_parse_function", "body"): Interface("Node"),
    # Coprocess body can be many different Node types (duplicate in Python, diff in Go naming)
    ("_parse_coproc", "body"): Interface("Node"),
    # Public compound command result can be many different Node types
    ("parse_compound_command", "result"): Interface("Node"),
    # _format_cmdsub_node hoisted variables
    ("_format_cmdsub_node", "cmd"): Interface("Node"),
    ("_format_cmdsub_node", "h"): Interface("Node"),
    # Empty list variables that need concrete element types
    ("_format_cmdsub_node", "heredocs"): Slice(Pointer(StructRef("HereDoc"))),
    ("_format_cmdsub_node", "cmds"): Slice(Tuple((Interface("Node"), BOOL))),
    # String list variables in _format_cmdsub_node
    ("_format_cmdsub_node", "word_vals"): Slice(STRING),
    ("_format_cmdsub_node", "patterns"): Slice(STRING),
    ("_format_cmdsub_node", "redirect_parts"): Slice(STRING),
}

# Fields that use -1 sentinel value instead of nil pointer for int | None
# Maps (class_name, field_name) -> True
# These fields use `== -1` instead of `== nil` for None comparison
SENTINEL_INT_FIELDS: set[tuple[str, str]] = {
    ("Parser", "_cmdsub_heredoc_end"),
}
