"""Hand-built IR fixture for backend development.

Exercises core IR constructs needed for parable.py transpilation.
"""

from src.ir import (
    Array,
    BOOL,
    FLOAT,
    INT,
    STRING,
    VOID,
    Assign,
    BinaryOp,
    Block,
    BoolLit,
    Break,
    Call,
    Cast,
    Constant,
    Continue,
    ExprStmt,
    Field,
    FieldAccess,
    FieldLV,
    FloatLit,
    ForClassic,
    ForRange,
    Function,
    If,
    Index,
    IndexLV,
    InterfaceDef,
    # Expressions
    IntLit,
    IsNil,
    Len,
    Loc,
    MakeMap,
    MakeSlice,
    Map,
    MapLit,
    Match,
    MatchCase,
    MethodCall,
    MethodSig,
    # Declarations
    DerefLV,
    Module,
    NilLit,
    OpAssign,
    Optional,
    Param,
    Pointer,
    Raise,
    Receiver,
    Return,
    Set,
    SetLit,
    Slice,
    SliceExpr,
    SliceLit,
    SoftFail,
    StaticCall,
    StringConcat,
    StringFormat,
    StringLit,
    StringSlice,
    Struct,
    StructLit,
    StructRef,
    Tuple,
    Ternary,
    TryCatch,
    TupleLit,
    UnaryOp,
    Union,
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

    # --- Interface: Scanner (exercises InterfaceDef) ---
    scanner_iface = InterfaceDef(
        name="Scanner",
        methods=[
            MethodSig(name="peek", params=[], ret=INT),
            MethodSig(name="advance", params=[], ret=VOID),
        ],
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
                                value=TupleLit(
                                    elements=[
                                        StructLit(struct_name="Token", fields={}, typ=token_ref, loc=L),
                                        BoolLit(value=False, typ=BOOL, loc=L),
                                    ],
                                    typ=Tuple(elements=(token_ref, BOOL)),
                                    loc=L,
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
                        value=TupleLit(
                            elements=[
                                StructLit(
                                    struct_name="Token",
                                    fields={
                                        "kind": StringLit(value="word", typ=STRING, loc=L),
                                        "text": Var(name="text", typ=STRING, loc=L),
                                        "pos": Var(name="start", typ=INT, loc=L),
                                    },
                                    typ=token_ref,
                                    loc=L,
                                ),
                                BoolLit(value=True, typ=BOOL, loc=L),
                            ],
                            typ=Tuple(elements=(token_ref, BOOL)),
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
                    # result := lx.scan_word(); tok := result[0]; ok := result[1]
                    VarDecl(
                        name="result",
                        typ=Tuple(elements=(token_ref, BOOL)),
                        value=MethodCall(
                            obj=Var(name="lx", typ=lexer_ref, loc=L),
                            method="scan_word",
                            args=[],
                            receiver_type=lexer_ref,
                            typ=Tuple(elements=(token_ref, BOOL)),
                            loc=L,
                        ),
                        loc=L,
                    ),
                    VarDecl(
                        name="tok",
                        typ=token_ref,
                        value=Index(
                            obj=Var(name="result", typ=Tuple(elements=(token_ref, BOOL)), loc=L),
                            index=IntLit(value=0, typ=INT, loc=L),
                            typ=token_ref,
                            loc=L,
                        ),
                        mutable=True,
                        loc=L,
                    ),
                    VarDecl(
                        name="ok",
                        typ=BOOL,
                        value=Index(
                            obj=Var(name="result", typ=Tuple(elements=(token_ref, BOOL)), loc=L),
                            index=IntLit(value=1, typ=INT, loc=L),
                            typ=BOOL,
                            loc=L,
                        ),
                        loc=L,
                    ),
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

    # --- Function: sum_positions (exercises ForClassic, Assign) ---
    sum_positions_func = Function(
        name="sum_positions",
        params=[Param(name="tokens", typ=token_slice)],
        ret=INT,
        body=[
            # sum := 0
            VarDecl(
                name="sum", typ=INT, value=IntLit(value=0, typ=INT, loc=L), mutable=True, loc=L
            ),
            # for i := 0; i < len(tokens); i = i + 1
            ForClassic(
                init=VarDecl(
                    name="i", typ=INT, value=IntLit(value=0, typ=INT, loc=L), mutable=True, loc=L
                ),
                cond=BinaryOp(
                    op="<",
                    left=Var(name="i", typ=INT, loc=L),
                    right=Len(expr=Var(name="tokens", typ=token_slice, loc=L), typ=INT, loc=L),
                    typ=BOOL,
                    loc=L,
                ),
                post=Assign(
                    target=VarLV(name="i", loc=L),
                    value=BinaryOp(
                        op="+",
                        left=Var(name="i", typ=INT, loc=L),
                        right=IntLit(value=1, typ=INT, loc=L),
                        typ=INT,
                        loc=L,
                    ),
                    loc=L,
                ),
                body=[
                    # sum = sum + tokens[i].pos
                    Assign(
                        target=VarLV(name="sum", loc=L),
                        value=BinaryOp(
                            op="+",
                            left=Var(name="sum", typ=INT, loc=L),
                            right=FieldAccess(
                                obj=Index(
                                    obj=Var(name="tokens", typ=token_slice, loc=L),
                                    index=Var(name="i", typ=INT, loc=L),
                                    typ=token_ref,
                                    loc=L,
                                ),
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
                loc=L,
            ),
            Return(value=Var(name="sum", typ=INT, loc=L), loc=L),
        ],
    )

    # --- Function: first_word_pos (exercises Break) ---
    first_word_pos_func = Function(
        name="first_word_pos",
        params=[Param(name="tokens", typ=token_slice)],
        ret=INT,
        body=[
            VarDecl(
                name="pos", typ=INT, value=IntLit(value=-1, typ=INT, loc=L), mutable=True, loc=L
            ),
            ForRange(
                index=None,
                value="tok",
                iterable=Var(name="tokens", typ=token_slice, loc=L),
                body=[
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
                            Assign(
                                target=VarLV(name="pos", loc=L),
                                value=FieldAccess(
                                    obj=Var(name="tok", typ=token_ref, loc=L),
                                    field="pos",
                                    typ=INT,
                                    loc=L,
                                ),
                                loc=L,
                            ),
                            Break(loc=L),
                        ],
                        loc=L,
                    ),
                ],
                loc=L,
            ),
            Return(value=Var(name="pos", typ=INT, loc=L), loc=L),
        ],
    )

    # --- Function: max_int (exercises Ternary) ---
    max_int_func = Function(
        name="max_int",
        params=[Param(name="a", typ=INT), Param(name="b", typ=INT)],
        ret=INT,
        body=[
            Return(
                value=Ternary(
                    cond=BinaryOp(
                        op=">",
                        left=Var(name="a", typ=INT, loc=L),
                        right=Var(name="b", typ=INT, loc=L),
                        typ=BOOL,
                        loc=L,
                    ),
                    then_expr=Var(name="a", typ=INT, loc=L),
                    else_expr=Var(name="b", typ=INT, loc=L),
                    typ=INT,
                    loc=L,
                ),
                loc=L,
            ),
        ],
    )

    # --- Function: default_kinds (exercises Map, MapLit) ---
    string_int_map = Map(key=STRING, value=INT)
    default_kinds_func = Function(
        name="default_kinds",
        params=[],
        ret=string_int_map,
        body=[
            Return(
                value=MapLit(
                    key_type=STRING,
                    value_type=INT,
                    entries=[
                        (StringLit(value="word", typ=STRING, loc=L), IntLit(value=1, typ=INT, loc=L)),
                        (StringLit(value="num", typ=STRING, loc=L), IntLit(value=2, typ=INT, loc=L)),
                        (StringLit(value="op", typ=STRING, loc=L), IntLit(value=3, typ=INT, loc=L)),
                    ],
                    typ=string_int_map,
                    loc=L,
                ),
                loc=L,
            ),
        ],
    )

    # --- Function: scoped_work (exercises Block) ---
    scoped_work_func = Function(
        name="scoped_work",
        params=[Param(name="x", typ=INT)],
        ret=INT,
        body=[
            VarDecl(name="result", typ=INT, value=IntLit(value=0, typ=INT, loc=L), mutable=True, loc=L),
            Block(
                body=[
                    VarDecl(
                        name="temp",
                        typ=INT,
                        value=BinaryOp(
                            op="*",
                            left=Var(name="x", typ=INT, loc=L),
                            right=IntLit(value=2, typ=INT, loc=L),
                            typ=INT,
                            loc=L,
                        ),
                        loc=L,
                    ),
                    Assign(
                        target=VarLV(name="result", loc=L),
                        value=BinaryOp(
                            op="+",
                            left=Var(name="temp", typ=INT, loc=L),
                            right=IntLit(value=1, typ=INT, loc=L),
                            typ=INT,
                            loc=L,
                        ),
                        loc=L,
                    ),
                ],
                loc=L,
            ),
            Return(value=Var(name="result", typ=INT, loc=L), loc=L),
        ],
    )

    # --- Function: kind_priority (exercises Match) ---
    kind_priority_func = Function(
        name="kind_priority",
        params=[Param(name="kind", typ=STRING)],
        ret=INT,
        body=[
            Match(
                expr=Var(name="kind", typ=STRING, loc=L),
                cases=[
                    MatchCase(
                        patterns=[StringLit(value="word", typ=STRING, loc=L)],
                        body=[Return(value=IntLit(value=1, typ=INT, loc=L), loc=L)],
                    ),
                    MatchCase(
                        patterns=[
                            StringLit(value="num", typ=STRING, loc=L),
                            StringLit(value="float", typ=STRING, loc=L),
                        ],
                        body=[Return(value=IntLit(value=2, typ=INT, loc=L), loc=L)],
                    ),
                    MatchCase(
                        patterns=[StringLit(value="op", typ=STRING, loc=L)],
                        body=[Return(value=IntLit(value=3, typ=INT, loc=L), loc=L)],
                    ),
                ],
                default=[Return(value=IntLit(value=0, typ=INT, loc=L), loc=L)],
                loc=L,
            ),
        ],
    )

    # --- Function: safe_tokenize (exercises TryCatch) ---
    safe_tokenize_func = Function(
        name="safe_tokenize",
        params=[Param(name="source", typ=STRING)],
        ret=token_slice,
        body=[
            VarDecl(
                name="tokens",
                typ=token_slice,
                value=SliceLit(element_type=token_ref, elements=[], typ=token_slice, loc=L),
                mutable=True,
                loc=L,
            ),
            TryCatch(
                body=[
                    Assign(
                        target=VarLV(name="tokens", loc=L),
                        value=Call(
                            func="tokenize",
                            args=[Var(name="source", typ=STRING, loc=L)],
                            typ=token_slice,
                            loc=L,
                        ),
                        loc=L,
                    ),
                ],
                catch_var="e",
                catch_body=[
                    Assign(
                        target=VarLV(name="tokens", loc=L),
                        value=SliceLit(element_type=token_ref, elements=[], typ=token_slice, loc=L),
                        loc=L,
                    ),
                ],
                loc=L,
            ),
            Return(value=Var(name="tokens", typ=token_slice, loc=L), loc=L),
        ],
    )

    # --- Function: pi (exercises FloatLit) ---
    pi_func = Function(
        name="pi",
        params=[],
        ret=FLOAT,
        body=[
            Return(value=FloatLit(value=3.14159, typ=FLOAT, loc=L), loc=L),
        ],
    )

    # --- Function: describe_token (exercises StringFormat) ---
    describe_token_func = Function(
        name="describe_token",
        params=[Param(name="tok", typ=token_ref)],
        ret=STRING,
        body=[
            Return(
                value=StringFormat(
                    template="Token({0}, {1}, {2})",
                    args=[
                        FieldAccess(obj=Var(name="tok", typ=token_ref, loc=L), field="kind", typ=STRING, loc=L),
                        FieldAccess(obj=Var(name="tok", typ=token_ref, loc=L), field="text", typ=STRING, loc=L),
                        FieldAccess(obj=Var(name="tok", typ=token_ref, loc=L), field="pos", typ=INT, loc=L),
                    ],
                    typ=STRING,
                    loc=L,
                ),
                loc=L,
            ),
        ],
    )

    # --- Function: set_first_kind (exercises IndexLV) ---
    set_first_kind_func = Function(
        name="set_first_kind",
        params=[Param(name="tokens", typ=token_slice), Param(name="kind", typ=STRING)],
        ret=VOID,
        body=[
            If(
                cond=BinaryOp(
                    op=">",
                    left=Len(expr=Var(name="tokens", typ=token_slice, loc=L), typ=INT, loc=L),
                    right=IntLit(value=0, typ=INT, loc=L),
                    typ=BOOL,
                    loc=L,
                ),
                then_body=[
                    Assign(
                        target=IndexLV(
                            obj=Var(name="tokens", typ=token_slice, loc=L),
                            index=IntLit(value=0, typ=INT, loc=L),
                            loc=L,
                        ),
                        value=StructLit(
                            struct_name="Token",
                            fields={
                                "kind": Var(name="kind", typ=STRING, loc=L),
                                "text": StringLit(value="", typ=STRING, loc=L),
                                "pos": IntLit(value=0, typ=INT, loc=L),
                            },
                            typ=token_ref,
                            loc=L,
                        ),
                        loc=L,
                    ),
                ],
                loc=L,
            ),
        ],
    )

    # --- Function: make_int_slice (exercises MakeSlice) ---
    int_slice = Slice(INT)
    make_int_slice_func = Function(
        name="make_int_slice",
        params=[Param(name="n", typ=INT)],
        ret=int_slice,
        body=[
            Return(
                value=MakeSlice(
                    element_type=INT,
                    length=Var(name="n", typ=INT, loc=L),
                    typ=int_slice,
                    loc=L,
                ),
                loc=L,
            ),
        ],
    )

    # --- Function: int_to_float (exercises Cast) ---
    int_to_float_func = Function(
        name="int_to_float",
        params=[Param(name="n", typ=INT)],
        ret=FLOAT,
        body=[
            Return(
                value=Cast(
                    expr=Var(name="n", typ=INT, loc=L),
                    to_type=FLOAT,
                    typ=FLOAT,
                    loc=L,
                ),
                loc=L,
            ),
        ],
    )

    # --- Function: known_kinds (exercises Set, SetLit) ---
    string_set = Set(element=STRING)
    known_kinds_func = Function(
        name="known_kinds",
        params=[],
        ret=string_set,
        body=[
            Return(
                value=SetLit(
                    element_type=STRING,
                    elements=[
                        StringLit(value="word", typ=STRING, loc=L),
                        StringLit(value="num", typ=STRING, loc=L),
                        StringLit(value="op", typ=STRING, loc=L),
                    ],
                    typ=string_set,
                    loc=L,
                ),
                loc=L,
            ),
        ],
    )

    # --- Function: call_static (exercises StaticCall) ---
    call_static_func = Function(
        name="call_static",
        params=[],
        ret=token_ref,
        body=[
            Return(
                value=StaticCall(
                    on_type=token_ref,
                    method="empty",
                    args=[],
                    typ=token_ref,
                    loc=L,
                ),
                loc=L,
            ),
        ],
    )

    # --- Function: new_kind_map (exercises MakeMap) ---
    new_kind_map_func = Function(
        name="new_kind_map",
        params=[],
        ret=string_int_map,
        body=[
            Return(
                value=MakeMap(
                    key_type=STRING,
                    value_type=INT,
                    typ=string_int_map,
                    loc=L,
                ),
                loc=L,
            ),
        ],
    )

    # --- Function: get_array_first (exercises Array) ---
    int_array = Array(element=INT, size=10)
    get_array_first_func = Function(
        name="get_array_first",
        params=[Param(name="arr", typ=int_array)],
        ret=INT,
        body=[
            Return(
                value=Index(
                    obj=Var(name="arr", typ=int_array, loc=L),
                    index=IntLit(value=0, typ=INT, loc=L),
                    typ=INT,
                    loc=L,
                ),
                loc=L,
            ),
        ],
    )

    # --- Function: maybe_get (exercises SoftFail) ---
    maybe_get_func = Function(
        name="maybe_get",
        params=[Param(name="tokens", typ=token_slice), Param(name="idx", typ=INT)],
        ret=opt_token,
        body=[
            If(
                cond=BinaryOp(
                    op=">=",
                    left=Var(name="idx", typ=INT, loc=L),
                    right=Len(expr=Var(name="tokens", typ=token_slice, loc=L), typ=INT, loc=L),
                    typ=BOOL,
                    loc=L,
                ),
                then_body=[SoftFail(loc=L)],
                loc=L,
            ),
            Return(
                value=Index(
                    obj=Var(name="tokens", typ=token_slice, loc=L),
                    index=Var(name="idx", typ=INT, loc=L),
                    typ=token_ref,
                    loc=L,
                ),
                loc=L,
            ),
        ],
    )

    # --- Function: set_via_ptr (exercises Pointer, DerefLV) ---
    int_ptr = Pointer(target=INT)
    set_via_ptr_func = Function(
        name="set_via_ptr",
        params=[Param(name="ptr", typ=int_ptr), Param(name="val", typ=INT)],
        ret=VOID,
        body=[
            Assign(
                target=DerefLV(ptr=Var(name="ptr", typ=int_ptr, loc=L), loc=L),
                value=Var(name="val", typ=INT, loc=L),
                loc=L,
            ),
        ],
    )

    # --- Function: identity_str (exercises StringSlice) ---
    str_slice = StringSlice()
    identity_str_func = Function(
        name="identity_str",
        params=[Param(name="s", typ=str_slice)],
        ret=str_slice,
        body=[
            Return(value=Var(name="s", typ=str_slice, loc=L), loc=L),
        ],
    )

    # --- Function: accept_union (exercises Union) ---
    token_or_lexer = Union(name="", variants=(token_ref, lexer_ref))
    accept_union_func = Function(
        name="accept_union",
        params=[Param(name="obj", typ=token_or_lexer)],
        ret=BOOL,
        body=[
            Return(value=BoolLit(value=True, typ=BOOL, loc=L), loc=L),
        ],
    )

    return Module(
        name="fixture",
        structs=[token_struct, lexer_struct],
        interfaces=[scanner_iface],
        functions=[
            is_space_func,
            tokenize_func,
            count_words_func,
            format_token_func,
            find_token_func,
            example_nil_check_func,
            sum_positions_func,
            first_word_pos_func,
            max_int_func,
            default_kinds_func,
            scoped_work_func,
            kind_priority_func,
            safe_tokenize_func,
            pi_func,
            describe_token_func,
            set_first_kind_func,
            make_int_slice_func,
            int_to_float_func,
            known_kinds_func,
            call_static_func,
            new_kind_map_func,
            get_array_first_func,
            maybe_get_func,
            set_via_ptr_func,
            identity_str_func,
            accept_union_func,
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
