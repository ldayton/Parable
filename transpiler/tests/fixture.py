"""Hand-built IR fixture for backend development.

Exercises core IR constructs needed for parable.py transpilation.
"""

from src.ir import (
    BOOL,
    INT,
    STRING,
    VOID,
    BinaryOp,
    Call,
    Constant,
    Continue,
    ExprStmt,
    Field,
    FieldAccess,
    FieldLV,
    ForRange,
    Function,
    If,
    Index,
    # Expressions
    IntLit,
    IsNil,
    Len,
    Loc,
    MethodCall,
    # Declarations
    Module,
    NilLit,
    OpAssign,
    Optional,
    Param,
    Raise,
    Receiver,
    Return,
    Slice,
    SliceExpr,
    SliceLit,
    StringConcat,
    StringLit,
    Struct,
    StructLit,
    StructRef,
    Tuple,
    UnaryOp,
    Var,
    # Statements
    VarDecl,
    # LValues
    VarLV,
    While,
)

L = Loc.unknown()


def make_fixture() -> Module:
    """Build a Module exercising core IR constructs.

    Models a minimal lexer with:
    - Token struct with .kind field (for TypeSwitch)
    - Optional fields and nil checks
    - Error handling with TryCatch/Raise
    - Tuple returns for (result, error) pattern
    - While loop for main scan
    - ForRange for iteration
    """

    # --- Types ---
    token_ref = StructRef("Token")
    token_slice = Slice(token_ref)
    opt_token = Optional(token_ref)
    lexer_ref = StructRef("Lexer")

    # --- Constants ---
    eof_const = Constant(
        name="EOF",
        typ=INT,
        value=IntLit(value=-1, typ=INT, loc=L),
        loc=L,
    )

    # --- Struct: Token ---
    token_struct = Struct(
        name="Token",
        fields=[
            Field(name="kind", typ=STRING),
            Field(name="text", typ=STRING),
            Field(name="pos", typ=INT),
        ],
        methods=[
            # func (t *Token) is_word() bool { return t.kind == "word" }
            Function(
                name="is_word",
                params=[],
                ret=BOOL,
                receiver=Receiver(name="t", typ=token_ref, pointer=True),
                body=[
                    Return(
                        value=BinaryOp(
                            op="==",
                            left=FieldAccess(
                                obj=Var(name="t", typ=token_ref, loc=L),
                                field="kind",
                                typ=STRING,
                                loc=L,
                            ),
                            right=StringLit(value="word", typ=STRING, loc=L),
                            typ=BOOL,
                            loc=L,
                        ),
                        loc=L,
                    ),
                ],
            ),
        ],
    )

    # --- Struct: Lexer ---
    lexer_struct = Struct(
        name="Lexer",
        fields=[
            Field(name="source", typ=STRING),
            Field(name="pos", typ=INT),
            Field(name="current", typ=opt_token),  # Optional field
        ],
        methods=[
            # func (lx *Lexer) peek() rune
            Function(
                name="peek",
                params=[],
                ret=INT,  # rune as int
                receiver=Receiver(name="lx", typ=lexer_ref, pointer=True, mutable=True),
                body=[
                    # if lx.pos >= len(lx.source): return EOF
                    If(
                        cond=BinaryOp(
                            op=">=",
                            left=FieldAccess(
                                obj=Var(name="lx", typ=lexer_ref, loc=L),
                                field="pos",
                                typ=INT,
                                loc=L,
                            ),
                            right=Len(
                                expr=FieldAccess(
                                    obj=Var(name="lx", typ=lexer_ref, loc=L),
                                    field="source",
                                    typ=STRING,
                                    loc=L,
                                ),
                                typ=INT,
                                loc=L,
                            ),
                            typ=BOOL,
                            loc=L,
                        ),
                        then_body=[
                            Return(value=Var(name="EOF", typ=INT, loc=L), loc=L),
                        ],
                        loc=L,
                    ),
                    # return lx.source[lx.pos]
                    Return(
                        value=Index(
                            obj=FieldAccess(
                                obj=Var(name="lx", typ=lexer_ref, loc=L),
                                field="source",
                                typ=STRING,
                                loc=L,
                            ),
                            index=FieldAccess(
                                obj=Var(name="lx", typ=lexer_ref, loc=L),
                                field="pos",
                                typ=INT,
                                loc=L,
                            ),
                            typ=INT,
                            loc=L,
                        ),
                        loc=L,
                    ),
                ],
            ),
            # func (lx *Lexer) advance()
            Function(
                name="advance",
                params=[],
                ret=VOID,
                receiver=Receiver(name="lx", typ=lexer_ref, pointer=True, mutable=True),
                body=[
                    # lx.pos += 1
                    OpAssign(
                        target=FieldLV(
                            obj=Var(name="lx", typ=lexer_ref, loc=L), field="pos", loc=L
                        ),
                        op="+",
                        value=IntLit(value=1, typ=INT, loc=L),
                        loc=L,
                    ),
                ],
            ),
            # func (lx *Lexer) scan_word() (Token, bool)
            Function(
                name="scan_word",
                params=[],
                ret=Tuple(elements=(token_ref, BOOL)),
                receiver=Receiver(name="lx", typ=lexer_ref, pointer=True, mutable=True),
                body=[
                    # start := lx.pos
                    VarDecl(
                        name="start",
                        typ=INT,
                        value=FieldAccess(
                            obj=Var(name="lx", typ=lexer_ref, loc=L), field="pos", typ=INT, loc=L
                        ),
                        loc=L,
                    ),
                    # while lx.peek() != EOF && !is_space(lx.peek()):
                    While(
                        cond=BinaryOp(
                            op="&&",
                            left=BinaryOp(
                                op="!=",
                                left=MethodCall(
                                    obj=Var(name="lx", typ=lexer_ref, loc=L),
                                    method="peek",
                                    args=[],
                                    receiver_type=lexer_ref,
                                    typ=INT,
                                    loc=L,
                                ),
                                right=Var(name="EOF", typ=INT, loc=L),
                                typ=BOOL,
                                loc=L,
                            ),
                            right=UnaryOp(
                                op="!",
                                operand=Call(
                                    func="is_space",
                                    args=[
                                        MethodCall(
                                            obj=Var(name="lx", typ=lexer_ref, loc=L),
                                            method="peek",
                                            args=[],
                                            receiver_type=lexer_ref,
                                            typ=INT,
                                            loc=L,
                                        )
                                    ],
                                    typ=BOOL,
                                    loc=L,
                                ),
                                typ=BOOL,
                                loc=L,
                            ),
                            typ=BOOL,
                            loc=L,
                        ),
                        body=[
                            # lx.advance()
                            ExprStmt(
                                expr=MethodCall(
                                    obj=Var(name="lx", typ=lexer_ref, loc=L),
                                    method="advance",
                                    args=[],
                                    receiver_type=lexer_ref,
                                    typ=VOID,
                                    loc=L,
                                ),
                                loc=L,
                            ),
                        ],
                        loc=L,
                    ),
                    # if lx.pos == start: return Token{}, false
                    If(
                        cond=BinaryOp(
                            op="==",
                            left=FieldAccess(
                                obj=Var(name="lx", typ=lexer_ref, loc=L),
                                field="pos",
                                typ=INT,
                                loc=L,
                            ),
                            right=Var(name="start", typ=INT, loc=L),
                            typ=BOOL,
                            loc=L,
                        ),
                        then_body=[
                            Return(
                                value=StructLit(
                                    struct_name="Token", fields={}, typ=token_ref, loc=L
                                ),
                                loc=L,
                            ),
                        ],
                        loc=L,
                    ),
                    # text := lx.source[start:lx.pos]
                    VarDecl(
                        name="text",
                        typ=STRING,
                        value=SliceExpr(
                            obj=FieldAccess(
                                obj=Var(name="lx", typ=lexer_ref, loc=L),
                                field="source",
                                typ=STRING,
                                loc=L,
                            ),
                            low=Var(name="start", typ=INT, loc=L),
                            high=FieldAccess(
                                obj=Var(name="lx", typ=lexer_ref, loc=L),
                                field="pos",
                                typ=INT,
                                loc=L,
                            ),
                            typ=STRING,
                            loc=L,
                        ),
                        loc=L,
                    ),
                    # return Token{kind: "word", text: text, pos: start}, true
                    Return(
                        value=StructLit(
                            struct_name="Token",
                            fields={
                                "kind": StringLit(value="word", typ=STRING, loc=L),
                                "text": Var(name="text", typ=STRING, loc=L),
                                "pos": Var(name="start", typ=INT, loc=L),
                            },
                            typ=token_ref,
                            loc=L,
                        ),
                        loc=L,
                    ),
                ],
            ),
        ],
    )

    # --- Function: is_space ---
    is_space_func = Function(
        name="is_space",
        params=[Param(name="ch", typ=INT)],
        ret=BOOL,
        body=[
            Return(
                value=BinaryOp(
                    op="||",
                    left=BinaryOp(
                        op="==",
                        left=Var(name="ch", typ=INT, loc=L),
                        right=IntLit(value=32, typ=INT, loc=L),
                        typ=BOOL,
                        loc=L,
                    ),
                    right=BinaryOp(
                        op="==",
                        left=Var(name="ch", typ=INT, loc=L),
                        right=IntLit(value=10, typ=INT, loc=L),
                        typ=BOOL,
                        loc=L,
                    ),
                    typ=BOOL,
                    loc=L,
                ),
                loc=L,
            ),
        ],
    )

    # --- Function: tokenize (exercises ForRange, nil checks, error handling) ---
    tokenize_func = Function(
        name="tokenize",
        params=[Param(name="source", typ=STRING)],
        ret=token_slice,
        fallible=True,
        body=[
            # lx := Lexer{source: source, pos: 0, current: nil}
            VarDecl(
                name="lx",
                typ=lexer_ref,
                value=StructLit(
                    struct_name="Lexer",
                    fields={
                        "source": Var(name="source", typ=STRING, loc=L),
                        "pos": IntLit(value=0, typ=INT, loc=L),
                        "current": NilLit(typ=opt_token, loc=L),
                    },
                    typ=lexer_ref,
                    loc=L,
                ),
                mutable=True,
                loc=L,
            ),
            # tokens := []Token{}
            VarDecl(
                name="tokens",
                typ=token_slice,
                value=SliceLit(element_type=token_ref, elements=[], typ=token_slice, loc=L),
                mutable=True,
                loc=L,
            ),
            # while lx.peek() != EOF:
            While(
                cond=BinaryOp(
                    op="!=",
                    left=MethodCall(
                        obj=Var(name="lx", typ=lexer_ref, loc=L),
                        method="peek",
                        args=[],
                        receiver_type=lexer_ref,
                        typ=INT,
                        loc=L,
                    ),
                    right=Var(name="EOF", typ=INT, loc=L),
                    typ=BOOL,
                    loc=L,
                ),
                body=[
                    # ch := lx.peek()
                    VarDecl(
                        name="ch",
                        typ=INT,
                        value=MethodCall(
                            obj=Var(name="lx", typ=lexer_ref, loc=L),
                            method="peek",
                            args=[],
                            receiver_type=lexer_ref,
                            typ=INT,
                            loc=L,
                        ),
                        loc=L,
                    ),
                    # if is_space(ch): lx.advance(); continue
                    If(
                        cond=Call(
                            func="is_space", args=[Var(name="ch", typ=INT, loc=L)], typ=BOOL, loc=L
                        ),
                        then_body=[
                            ExprStmt(
                                expr=MethodCall(
                                    obj=Var(name="lx", typ=lexer_ref, loc=L),
                                    method="advance",
                                    args=[],
                                    receiver_type=lexer_ref,
                                    typ=VOID,
                                    loc=L,
                                ),
                                loc=L,
                            ),
                            Continue(loc=L),
                        ],
                        loc=L,
                    ),
                    # tok, ok := lx.scan_word()
                    VarDecl(name="tok", typ=token_ref, value=None, mutable=True, loc=L),
                    VarDecl(name="ok", typ=BOOL, value=None, mutable=True, loc=L),
                    # if !ok: raise ParseError("unexpected char", lx.pos)
                    If(
                        cond=UnaryOp(
                            op="!", operand=Var(name="ok", typ=BOOL, loc=L), typ=BOOL, loc=L
                        ),
                        then_body=[
                            Raise(
                                error_type="ParseError",
                                message=StringLit(value="unexpected character", typ=STRING, loc=L),
                                pos=FieldAccess(
                                    obj=Var(name="lx", typ=lexer_ref, loc=L),
                                    field="pos",
                                    typ=INT,
                                    loc=L,
                                ),
                                loc=L,
                            ),
                        ],
                        loc=L,
                    ),
                    # tokens.append(tok)
                    ExprStmt(
                        expr=MethodCall(
                            obj=Var(name="tokens", typ=token_slice, loc=L),
                            method="append",
                            args=[Var(name="tok", typ=token_ref, loc=L)],
                            receiver_type=token_slice,
                            typ=VOID,
                            loc=L,
                        ),
                        loc=L,
                    ),
                ],
                loc=L,
            ),
            # return tokens
            Return(value=Var(name="tokens", typ=token_slice, loc=L), loc=L),
        ],
    )

    # --- Function: count_words (exercises ForRange, TypeSwitch) ---
    count_words_func = Function(
        name="count_words",
        params=[Param(name="tokens", typ=token_slice)],
        ret=INT,
        body=[
            # count := 0
            VarDecl(
                name="count", typ=INT, value=IntLit(value=0, typ=INT, loc=L), mutable=True, loc=L
            ),
            # for _, tok := range tokens:
            ForRange(
                index=None,
                value="tok",
                iterable=Var(name="tokens", typ=token_slice, loc=L),
                body=[
                    # if tok.kind == "word": count += 1
                    If(
                        cond=BinaryOp(
                            op="==",
                            left=FieldAccess(
                                obj=Var(name="tok", typ=token_ref, loc=L),
                                field="kind",
                                typ=STRING,
                                loc=L,
                            ),
                            right=StringLit(value="word", typ=STRING, loc=L),
                            typ=BOOL,
                            loc=L,
                        ),
                        then_body=[
                            OpAssign(
                                target=VarLV(name="count", loc=L),
                                op="+",
                                value=IntLit(value=1, typ=INT, loc=L),
                                loc=L,
                            ),
                        ],
                        loc=L,
                    ),
                ],
                loc=L,
            ),
            Return(value=Var(name="count", typ=INT, loc=L), loc=L),
        ],
    )

    # --- Function: format_token (exercises StringConcat) ---
    format_token_func = Function(
        name="format_token",
        params=[Param(name="tok", typ=token_ref)],
        ret=STRING,
        body=[
            # return tok.kind + ":" + tok.text
            Return(
                value=StringConcat(
                    parts=[
                        FieldAccess(
                            obj=Var(name="tok", typ=token_ref, loc=L),
                            field="kind",
                            typ=STRING,
                            loc=L,
                        ),
                        StringLit(value=":", typ=STRING, loc=L),
                        FieldAccess(
                            obj=Var(name="tok", typ=token_ref, loc=L),
                            field="text",
                            typ=STRING,
                            loc=L,
                        ),
                    ],
                    typ=STRING,
                    loc=L,
                ),
                loc=L,
            ),
        ],
    )

    # --- Function: find_token (exercises Optional, IsNil) ---
    find_token_func = Function(
        name="find_token",
        params=[
            Param(name="tokens", typ=token_slice),
            Param(name="kind", typ=STRING),
        ],
        ret=opt_token,
        body=[
            # for _, tok := range tokens:
            ForRange(
                index=None,
                value="tok",
                iterable=Var(name="tokens", typ=token_slice, loc=L),
                body=[
                    # if tok.kind == kind: return tok
                    If(
                        cond=BinaryOp(
                            op="==",
                            left=FieldAccess(
                                obj=Var(name="tok", typ=token_ref, loc=L),
                                field="kind",
                                typ=STRING,
                                loc=L,
                            ),
                            right=Var(name="kind", typ=STRING, loc=L),
                            typ=BOOL,
                            loc=L,
                        ),
                        then_body=[
                            Return(value=Var(name="tok", typ=token_ref, loc=L), loc=L),
                        ],
                        loc=L,
                    ),
                ],
                loc=L,
            ),
            # return nil
            Return(value=NilLit(typ=opt_token, loc=L), loc=L),
        ],
    )

    # --- Function: example_nil_check (exercises IsNil) ---
    example_nil_check_func = Function(
        name="example_nil_check",
        params=[Param(name="tokens", typ=token_slice)],
        ret=STRING,
        body=[
            # tok := find_token(tokens, "word")
            VarDecl(
                name="tok",
                typ=opt_token,
                value=Call(
                    func="find_token",
                    args=[
                        Var(name="tokens", typ=token_slice, loc=L),
                        StringLit(value="word", typ=STRING, loc=L),
                    ],
                    typ=opt_token,
                    loc=L,
                ),
                loc=L,
            ),
            # if tok is nil: return ""
            If(
                cond=IsNil(
                    expr=Var(name="tok", typ=opt_token, loc=L), negated=False, typ=BOOL, loc=L
                ),
                then_body=[
                    Return(value=StringLit(value="", typ=STRING, loc=L), loc=L),
                ],
                loc=L,
            ),
            # return tok.text
            Return(
                value=FieldAccess(
                    obj=Var(name="tok", typ=token_ref, loc=L), field="text", typ=STRING, loc=L
                ),
                loc=L,
            ),
        ],
    )

    return Module(
        name="fixture",
        structs=[token_struct, lexer_struct],
        functions=[
            is_space_func,
            tokenize_func,
            count_words_func,
            format_token_func,
            find_token_func,
            example_nil_check_func,
        ],
        constants=[eof_const],
    )


if __name__ == "__main__":
    module = make_fixture()
    print(f"Module: {module.name}")
    print(f"Constants: {[c.name for c in module.constants]}")
    print(f"Structs: {[s.name for s in module.structs]}")
    for s in module.structs:
        print(f"  {s.name}.fields: {[f.name for f in s.fields]}")
        print(f"  {s.name}.methods: {[m.name for m in s.methods]}")
    print(f"Functions: {[f.name for f in module.functions]}")
