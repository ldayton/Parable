"""Type override dictionaries for parable.py transpilation.

These override Python's loose type hints with concrete IR types.
Used by the frontend when Python annotations are ambiguous (e.g., bare `list`).
"""

from .ir import (
    BOOL,
    INT,
    STRING,
    Interface,
    Optional,
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
    # _read_bracket_expression, _parse_dollar_expansion, _scan_double_quote: auto-detected
    # restore_from, copy_stack: annotated in parable.py
    # SavedParserState constructor parameters: annotated in parable.py
    # Token constructor parts: annotated in parable.py
    # _append_redirects: annotated in parable.py
    # _append_with_ctlesc: auto-detected (bytearray mutation)
    # ParseError/MatchedPairError constructor uses int, not *int
    ("NewParseError", "pos"): INT,
    ("NewParseError", "line"): INT,
    ("NewMatchedPairError", "pos"): INT,
    ("NewMatchedPairError", "line"): INT,
}

# Override field types for fields without proper annotations
# Maps (class_name, field_name) -> IR type (field_name is Python name, lowercase)
FIELD_TYPE_OVERRIDES: dict[tuple[str, str], Type] = {
    ("Lexer", "_word_context"): INT,
    ("Parser", "_word_context"): INT,
    # Array.elements is list[Word] - need concrete type for field access
    ("Array", "elements"): Slice(Pointer(StructRef("Word"))),
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
    # For/Select.words is []*Word | None - null indicates "no in clause" (iterate $@)
    ("For", "words"): Optional(Slice(Pointer(StructRef("Word")))),
    ("Select", "words"): Optional(Slice(Pointer(StructRef("Word")))),
    # Redirects fields are []Node, not *[]Node (nil slice is fine in Go)
    ("For", "redirects"): Slice(StructRef("Node")),
    ("Select", "redirects"): Slice(StructRef("Node")),
    ("Subshell", "redirects"): Slice(StructRef("Node")),
    ("ArithmeticCommand", "redirects"): Slice(StructRef("Node")),
    ("Conditional", "redirects"): Slice(StructRef("Node")),
    ("BraceGroup", "redirects"): Slice(StructRef("Node")),
    # Redirect.target is Word | None -> *Word in Go
    ("Redirect", "target"): Pointer(StructRef("Word")),
    # ParseError uses int with 0 sentinel, not *int
    ("ParseError", "pos"): INT,
    ("ParseError", "line"): INT,
}

# Override return types for methods that return generic list
# Maps method_name -> IR return type
# Most methods now use proper annotations: _collect_cmdsubs, _collect_procsubs,
# _collect_redirects, copy_stack. Others auto-detected as Node.
RETURN_TYPE_OVERRIDES: dict[str, Type] = {}

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
    # op field - on Operator (List parts access), Redirect (redirect formatting)
    "op": ["Operator", "Redirect"],
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
    "body": ["CasePattern", "BraceGroup", "For", "ForArith", "While", "Until", "Select", "Conditional"],
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

# Module-level constants that need custom emission (empty - all constants auto-detected)
MODULE_CONSTANTS: dict[str, tuple[Type, str]] = {}

# Override local variable types when inference fails
# Maps (function_name, var_name) -> IR type
VAR_TYPE_OVERRIDES: dict[tuple[str, str], Type] = {
    # _collect_redirects.redirects: auto-inferred from self.parse_redirect() return type
    # Tuple element types inferred incorrectly
    ("_read_heredoc_body", "pending_heredocs"): Slice(Tuple((STRING, BOOL))),
    # parse_if.else_body, parse_if.inner_else, _parse_elif_chain.else_body: auto-inferred from self.method() return types
    # Hoisted word lists in for/select parsing (interface{} instead of []*Word)
    ("parse_for", "words"): Slice(Pointer(StructRef("Word"))),
    ("parse_select", "words"): Slice(Pointer(StructRef("Word"))),
    # parse_case.body, parse_coproc.body, _parse_compound_command.result,
    # _parse_function.body, _parse_coproc.body, parse_compound_command.result:
    # auto-inferred from multiple Node-subtype assignments
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
# Maps (class_name, field_name) -> sentinel value
# These fields use the sentinel value instead of nil for None comparison
SENTINEL_INT_FIELDS: dict[tuple[str, str], int] = {
    ("Parser", "_cmdsub_heredoc_end"): -1,
    # ParseError uses 0 for "no value" (matching old transpiler)
    ("ParseError", "pos"): 0,
    ("ParseError", "line"): 0,
}
