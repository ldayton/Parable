function range(start, end, step) {
    if (end === undefined) {
        end = start;
        start = 0;
    }
    if (step === undefined) {
        step = 1;
    }
    var result = [];
    if (step > 0) {
        for (var i = start; i < end; i += step)
            result.push(i);
    }
    else {
        for (var i = start; i > end; i += step)
            result.push(i);
    }
    return result;
}
var ANSI_C_ESCAPES = new Map([["a", 7], ["b", 8], ["e", 27], ["E", 27], ["f", 12], ["n", 10], ["r", 13], ["t", 9], ["v", 11], ["\\", 92], ["\"", 34], ["?", 63]]);
var TokenType_EOF = 0;
var TokenType_WORD = 1;
var TokenType_NEWLINE = 2;
var TokenType_SEMI = 10;
var TokenType_PIPE = 11;
var TokenType_AMP = 12;
var TokenType_LPAREN = 13;
var TokenType_RPAREN = 14;
var TokenType_LBRACE = 15;
var TokenType_RBRACE = 16;
var TokenType_LESS = 17;
var TokenType_GREATER = 18;
var TokenType_AND_AND = 30;
var TokenType_OR_OR = 31;
var TokenType_SEMI_SEMI = 32;
var TokenType_SEMI_AMP = 33;
var TokenType_SEMI_SEMI_AMP = 34;
var TokenType_LESS_LESS = 35;
var TokenType_GREATER_GREATER = 36;
var TokenType_LESS_AMP = 37;
var TokenType_GREATER_AMP = 38;
var TokenType_LESS_GREATER = 39;
var TokenType_GREATER_PIPE = 40;
var TokenType_LESS_LESS_MINUS = 41;
var TokenType_LESS_LESS_LESS = 42;
var TokenType_AMP_GREATER = 43;
var TokenType_AMP_GREATER_GREATER = 44;
var TokenType_PIPE_AMP = 45;
var TokenType_IF = 50;
var TokenType_THEN = 51;
var TokenType_ELSE = 52;
var TokenType_ELIF = 53;
var TokenType_FI = 54;
var TokenType_CASE = 55;
var TokenType_ESAC = 56;
var TokenType_FOR = 57;
var TokenType_WHILE = 58;
var TokenType_UNTIL = 59;
var TokenType_DO = 60;
var TokenType_DONE = 61;
var TokenType_IN = 62;
var TokenType_FUNCTION = 63;
var TokenType_SELECT = 64;
var TokenType_COPROC = 65;
var TokenType_TIME = 66;
var TokenType_BANG = 67;
var TokenType_LBRACKET_LBRACKET = 68;
var TokenType_RBRACKET_RBRACKET = 69;
var TokenType_ASSIGNMENT_WORD = 80;
var TokenType_NUMBER = 81;
var ParserStateFlags_NONE = 0;
var ParserStateFlags_PST_CASEPAT = 1;
var ParserStateFlags_PST_CMDSUBST = 2;
var ParserStateFlags_PST_CASESTMT = 4;
var ParserStateFlags_PST_CONDEXPR = 8;
var ParserStateFlags_PST_COMPASSIGN = 16;
var ParserStateFlags_PST_ARITH = 32;
var ParserStateFlags_PST_HEREDOC = 64;
var ParserStateFlags_PST_REGEXP = 128;
var ParserStateFlags_PST_EXTPAT = 256;
var ParserStateFlags_PST_SUBSHELL = 512;
var ParserStateFlags_PST_REDIRLIST = 1024;
var ParserStateFlags_PST_COMMENT = 2048;
var ParserStateFlags_PST_EOFTOKEN = 4096;
var DolbraceState_NONE = 0;
var DolbraceState_PARAM = 1;
var DolbraceState_OP = 2;
var DolbraceState_WORD = 4;
var DolbraceState_QUOTE = 64;
var DolbraceState_QUOTE2 = 128;
var MatchedPairFlags_NONE = 0;
var MatchedPairFlags_DQUOTE = 1;
var MatchedPairFlags_DOLBRACE = 2;
var MatchedPairFlags_COMMAND = 4;
var MatchedPairFlags_ARITH = 8;
var MatchedPairFlags_ALLOWESC = 16;
var MatchedPairFlags_EXTGLOB = 32;
var MatchedPairFlags_FIRSTCLOSE = 64;
var MatchedPairFlags_ARRAYSUB = 128;
var MatchedPairFlags_BACKQUOTE = 256;
var ParseContext_NORMAL = 0;
var ParseContext_COMMAND_SUB = 1;
var ParseContext_ARITHMETIC = 2;
var ParseContext_CASE_PATTERN = 3;
var ParseContext_BRACE_EXPANSION = 4;
var RESERVED_WORDS = new Set(["if", "then", "elif", "else", "fi", "while", "until", "for", "select", "do", "done", "case", "esac", "in", "function", "coproc"]);
var COND_UNARY_OPS = new Set(["-a", "-b", "-c", "-d", "-e", "-f", "-g", "-h", "-k", "-p", "-r", "-s", "-t", "-u", "-w", "-x", "-G", "-L", "-N", "-O", "-S", "-z", "-n", "-o", "-v", "-R"]);
var COND_BINARY_OPS = new Set(["==", "!=", "=~", "=", "<", ">", "-eq", "-ne", "-lt", "-le", "-gt", "-ge", "-nt", "-ot", "-ef"]);
var COMPOUND_KEYWORDS = new Set(["while", "until", "for", "if", "case", "select"]);
var ASSIGNMENT_BUILTINS = new Set(["alias", "declare", "typeset", "local", "export", "readonly", "eval", "let"]);
var _SMP_LITERAL = 1;
var _SMP_PAST_OPEN = 2;
var WORD_CTX_NORMAL = 0;
var WORD_CTX_COND = 1;
var WORD_CTX_REGEX = 2;
var ParseError = /** @class */ (function () {
    function ParseError(message, pos, line) {
        if (message === void 0) { message = ""; }
        if (pos === void 0) { pos = 0; }
        if (line === void 0) { line = 0; }
        this.message = message;
        this.pos = pos;
        this.line = line;
    }
    ParseError.prototype.FormatMessage = function () {
        if (this.line !== 0 && this.pos !== 0) {
            return "Parse error at line ".concat(this.line, ", position ").concat(this.pos, ": ").concat(this.message);
        }
        else {
            if (this.pos !== 0) {
                return "Parse error at position ".concat(this.pos, ": ").concat(this.message);
            }
        }
        return "Parse error: ".concat(this.message);
    };
    return ParseError;
}());
var MatchedPairError = /** @class */ (function () {
    function MatchedPairError() {
    }
    return MatchedPairError;
}());
var TokenType = /** @class */ (function () {
    function TokenType() {
    }
    return TokenType;
}());
var Token = /** @class */ (function () {
    function Token(typeName, value, pos, parts, word) {
        if (typeName === void 0) { typeName = 0; }
        if (value === void 0) { value = ""; }
        if (pos === void 0) { pos = 0; }
        if (parts === void 0) { parts = []; }
        if (word === void 0) { word = null; }
        this.typeName = typeName;
        this.value = value;
        this.pos = pos;
        this.parts = parts !== null && parts !== void 0 ? parts : [];
        this.word = word;
    }
    Token.prototype.Repr = function () {
        if (this.word !== null) {
            return "Token(".concat(this.typeName, ", ").concat(this.value, ", ").concat(this.pos, ", word=").concat(this.word, ")");
        }
        if (this.parts.length > 0) {
            return "Token(".concat(this.typeName, ", ").concat(this.value, ", ").concat(this.pos, ", parts=").concat(this.parts.length, ")");
        }
        return "Token(".concat(this.typeName, ", ").concat(this.value, ", ").concat(this.pos, ")");
    };
    return Token;
}());
var ParserStateFlags = /** @class */ (function () {
    function ParserStateFlags() {
    }
    return ParserStateFlags;
}());
var DolbraceState = /** @class */ (function () {
    function DolbraceState() {
    }
    return DolbraceState;
}());
var MatchedPairFlags = /** @class */ (function () {
    function MatchedPairFlags() {
    }
    return MatchedPairFlags;
}());
var SavedParserState = /** @class */ (function () {
    function SavedParserState(parserState, dolbraceState, pendingHeredocs, ctxStack, eofToken) {
        if (parserState === void 0) { parserState = 0; }
        if (dolbraceState === void 0) { dolbraceState = 0; }
        if (pendingHeredocs === void 0) { pendingHeredocs = []; }
        if (ctxStack === void 0) { ctxStack = []; }
        if (eofToken === void 0) { eofToken = ""; }
        this.parserState = parserState;
        this.dolbraceState = dolbraceState;
        this.pendingHeredocs = pendingHeredocs !== null && pendingHeredocs !== void 0 ? pendingHeredocs : [];
        this.ctxStack = ctxStack !== null && ctxStack !== void 0 ? ctxStack : [];
        this.eofToken = eofToken;
    }
    return SavedParserState;
}());
var QuoteState = /** @class */ (function () {
    function QuoteState(single, double, Stack) {
        if (single === void 0) { single = false; }
        if (double === void 0) { double = false; }
        if (Stack === void 0) { Stack = []; }
        this.single = single;
        this.double = double;
        this.Stack = Stack !== null && Stack !== void 0 ? Stack : [];
    }
    QuoteState.prototype.push = function () {
        this.Stack.push([this.single, this.double]);
        this.single = false;
        this.double = false;
    };
    QuoteState.prototype.pop = function () {
        if (this.Stack.length > 0) {
            {
                var Entry = this.Stack[this.Stack.length - 1];
                this.Stack = this.Stack.slice(0, this.Stack.length - 1);
                this.single = Entry[0];
                this.double = Entry[1];
            }
        }
    };
    QuoteState.prototype.inQuotes = function () {
        return this.single || this.double;
    };
    QuoteState.prototype.copy = function () {
        var qs = newQuoteState();
        qs.single = this.single;
        qs.double = this.double;
        qs.Stack = this.Stack.slice();
        return qs;
    };
    QuoteState.prototype.outerDouble = function () {
        if (this.Stack.length === 0) {
            return false;
        }
        return this.Stack[this.Stack.length - 1][1];
    };
    return QuoteState;
}());
var ParseContext = /** @class */ (function () {
    function ParseContext(kind, parenDepth, braceDepth, bracketDepth, caseDepth, arithDepth, arithParenDepth, quote) {
        if (kind === void 0) { kind = 0; }
        if (parenDepth === void 0) { parenDepth = 0; }
        if (braceDepth === void 0) { braceDepth = 0; }
        if (bracketDepth === void 0) { bracketDepth = 0; }
        if (caseDepth === void 0) { caseDepth = 0; }
        if (arithDepth === void 0) { arithDepth = 0; }
        if (arithParenDepth === void 0) { arithParenDepth = 0; }
        if (quote === void 0) { quote = null; }
        this.kind = kind;
        this.parenDepth = parenDepth;
        this.braceDepth = braceDepth;
        this.bracketDepth = bracketDepth;
        this.caseDepth = caseDepth;
        this.arithDepth = arithDepth;
        this.arithParenDepth = arithParenDepth;
        this.quote = quote;
    }
    ParseContext.prototype.copy = function () {
        var ctx = newParseContext(this.kind);
        ctx.parenDepth = this.parenDepth;
        ctx.braceDepth = this.braceDepth;
        ctx.bracketDepth = this.bracketDepth;
        ctx.caseDepth = this.caseDepth;
        ctx.arithDepth = this.arithDepth;
        ctx.arithParenDepth = this.arithParenDepth;
        ctx.quote = this.quote.copy();
        return ctx;
    };
    return ParseContext;
}());
var ContextStack = /** @class */ (function () {
    function ContextStack(Stack) {
        if (Stack === void 0) { Stack = []; }
        this.Stack = Stack !== null && Stack !== void 0 ? Stack : [];
    }
    ContextStack.prototype.getCurrent = function () {
        return this.Stack[this.Stack.length - 1];
    };
    ContextStack.prototype.push = function (kind) {
        this.Stack.push(newParseContext(kind));
    };
    ContextStack.prototype.pop = function () {
        if (this.Stack.length > 1) {
            return this.Stack.pop();
        }
        return this.Stack[0];
    };
    ContextStack.prototype.copyStack = function () {
        var result = [];
        for (var _i = 0, _a = this.Stack; _i < _a.length; _i++) {
            var ctx = _a[_i];
            result.push(ctx.copy());
        }
        return result;
    };
    ContextStack.prototype.restoreFrom = function (savedStack) {
        var result = [];
        for (var _i = 0, savedStack_1 = savedStack; _i < savedStack_1.length; _i++) {
            var ctx = savedStack_1[_i];
            result.push(ctx.copy());
        }
        this.Stack = result;
    };
    return ContextStack;
}());
var Lexer = /** @class */ (function () {
    function Lexer(RESERVED_WORDS, source, pos, length, quote, TokenCache, ParserState, DolbraceState, PendingHeredocs, Extglob, Parser, EofToken, LastReadToken, WordContext, AtCommandStart, InArrayLiteral, InAssignBuiltin, PostReadPos, CachedWordContext, CachedAtCommandStart, CachedInArrayLiteral, CachedInAssignBuiltin) {
        if (RESERVED_WORDS === void 0) { RESERVED_WORDS = new Map(); }
        if (source === void 0) { source = ""; }
        if (pos === void 0) { pos = 0; }
        if (length === void 0) { length = 0; }
        if (quote === void 0) { quote = null; }
        if (TokenCache === void 0) { TokenCache = null; }
        if (ParserState === void 0) { ParserState = 0; }
        if (DolbraceState === void 0) { DolbraceState = 0; }
        if (PendingHeredocs === void 0) { PendingHeredocs = []; }
        if (Extglob === void 0) { Extglob = false; }
        if (Parser === void 0) { Parser = null; }
        if (EofToken === void 0) { EofToken = ""; }
        if (LastReadToken === void 0) { LastReadToken = null; }
        if (WordContext === void 0) { WordContext = 0; }
        if (AtCommandStart === void 0) { AtCommandStart = false; }
        if (InArrayLiteral === void 0) { InArrayLiteral = false; }
        if (InAssignBuiltin === void 0) { InAssignBuiltin = false; }
        if (PostReadPos === void 0) { PostReadPos = 0; }
        if (CachedWordContext === void 0) { CachedWordContext = 0; }
        if (CachedAtCommandStart === void 0) { CachedAtCommandStart = false; }
        if (CachedInArrayLiteral === void 0) { CachedInArrayLiteral = false; }
        if (CachedInAssignBuiltin === void 0) { CachedInAssignBuiltin = false; }
        this.RESERVED_WORDS = RESERVED_WORDS;
        this.source = source;
        this.pos = pos;
        this.length = length;
        this.quote = quote;
        this.TokenCache = TokenCache;
        this.ParserState = ParserState;
        this.DolbraceState = DolbraceState;
        this.PendingHeredocs = PendingHeredocs !== null && PendingHeredocs !== void 0 ? PendingHeredocs : [];
        this.Extglob = Extglob;
        this.Parser = Parser;
        this.EofToken = EofToken;
        this.LastReadToken = LastReadToken;
        this.WordContext = WordContext;
        this.AtCommandStart = AtCommandStart;
        this.InArrayLiteral = InArrayLiteral;
        this.InAssignBuiltin = InAssignBuiltin;
        this.PostReadPos = PostReadPos;
        this.CachedWordContext = CachedWordContext;
        this.CachedAtCommandStart = CachedAtCommandStart;
        this.CachedInArrayLiteral = CachedInArrayLiteral;
        this.CachedInAssignBuiltin = CachedInAssignBuiltin;
    }
    Lexer.prototype.peek = function () {
        if (this.pos >= this.length) {
            return "";
        }
        return this.source[this.pos];
    };
    Lexer.prototype.advance = function () {
        if (this.pos >= this.length) {
            return "";
        }
        var c = this.source[this.pos];
        this.pos += 1;
        return c;
    };
    Lexer.prototype.atEnd = function () {
        return this.pos >= this.length;
    };
    Lexer.prototype.lookahead = function (n) {
        return Substring(this.source, this.pos, this.pos + n);
    };
    Lexer.prototype.isMetachar = function (c) {
        return "|&;()<> \t\n".includes(c);
    };
    Lexer.prototype.ReadOperator = function () {
        var start = this.pos;
        var c = this.peek();
        if (c === "") {
            return null;
        }
        var two = this.lookahead(2);
        var three = this.lookahead(3);
        if (three === ";;&") {
            this.pos += 3;
            return new Token(TokenType_SEMI_SEMI_AMP, three, start, [], []);
        }
        if (three === "<<-") {
            this.pos += 3;
            return new Token(TokenType_LESS_LESS_MINUS, three, start, [], []);
        }
        if (three === "<<<") {
            this.pos += 3;
            return new Token(TokenType_LESS_LESS_LESS, three, start, [], []);
        }
        if (three === "&>>") {
            this.pos += 3;
            return new Token(TokenType_AMP_GREATER_GREATER, three, start, [], []);
        }
        if (two === "&&") {
            this.pos += 2;
            return new Token(TokenType_AND_AND, two, start, [], []);
        }
        if (two === "||") {
            this.pos += 2;
            return new Token(TokenType_OR_OR, two, start, [], []);
        }
        if (two === ";;") {
            this.pos += 2;
            return new Token(TokenType_SEMI_SEMI, two, start, [], []);
        }
        if (two === ";&") {
            this.pos += 2;
            return new Token(TokenType_SEMI_AMP, two, start, [], []);
        }
        if (two === "<<") {
            this.pos += 2;
            return new Token(TokenType_LESS_LESS, two, start, [], []);
        }
        if (two === ">>") {
            this.pos += 2;
            return new Token(TokenType_GREATER_GREATER, two, start, [], []);
        }
        if (two === "<&") {
            this.pos += 2;
            return new Token(TokenType_LESS_AMP, two, start, [], []);
        }
        if (two === ">&") {
            this.pos += 2;
            return new Token(TokenType_GREATER_AMP, two, start, [], []);
        }
        if (two === "<>") {
            this.pos += 2;
            return new Token(TokenType_LESS_GREATER, two, start, [], []);
        }
        if (two === ">|") {
            this.pos += 2;
            return new Token(TokenType_GREATER_PIPE, two, start, [], []);
        }
        if (two === "&>") {
            this.pos += 2;
            return new Token(TokenType_AMP_GREATER, two, start, [], []);
        }
        if (two === "|&") {
            this.pos += 2;
            return new Token(TokenType_PIPE_AMP, two, start, [], []);
        }
        if (c === ";") {
            this.pos += 1;
            return new Token(TokenType_SEMI, c, start, [], []);
        }
        if (c === "|") {
            this.pos += 1;
            return new Token(TokenType_PIPE, c, start, [], []);
        }
        if (c === "&") {
            this.pos += 1;
            return new Token(TokenType_AMP, c, start, [], []);
        }
        if (c === "(") {
            if (this.WordContext === WORD_CTX_REGEX) {
                return null;
            }
            this.pos += 1;
            return new Token(TokenType_LPAREN, c, start, [], []);
        }
        if (c === ")") {
            if (this.WordContext === WORD_CTX_REGEX) {
                return null;
            }
            this.pos += 1;
            return new Token(TokenType_RPAREN, c, start, [], []);
        }
        if (c === "<") {
            if (this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
                return null;
            }
            this.pos += 1;
            return new Token(TokenType_LESS, c, start, [], []);
        }
        if (c === ">") {
            if (this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
                return null;
            }
            this.pos += 1;
            return new Token(TokenType_GREATER, c, start, [], []);
        }
        if (c === "\n") {
            this.pos += 1;
            return new Token(TokenType_NEWLINE, c, start, [], []);
        }
        return null;
    };
    Lexer.prototype.skipBlanks = function () {
        while (this.pos < this.length) {
            var c = this.source[this.pos];
            if (c !== " " && c !== "\t") {
                break;
            }
            this.pos += 1;
        }
    };
    Lexer.prototype.SkipComment = function () {
        if (this.pos >= this.length) {
            return false;
        }
        if (this.source[this.pos] !== "#") {
            return false;
        }
        if (this.quote.inQuotes()) {
            return false;
        }
        if (this.pos > 0) {
            var prev = this.source[this.pos - 1];
            if (!" \t\n;|&(){}".includes(prev)) {
                return false;
            }
        }
        while (this.pos < this.length && this.source[this.pos] !== "\n") {
            this.pos += 1;
        }
        return true;
    };
    Lexer.prototype.ReadSingleQuote = function (start) {
        var chars = ["'"];
        var sawNewline = false;
        while (this.pos < this.length) {
            var c = this.source[this.pos];
            if (c === "\n") {
                sawNewline = true;
            }
            chars.push(c);
            this.pos += 1;
            if (c === "'") {
                return [chars.join(""), sawNewline];
            }
        }
        throw new Error("".concat("Unterminated single quote", " at position ").concat(start));
    };
    Lexer.prototype.IsWordTerminator = function (ctx, ch, bracketDepth, parenDepth) {
        if (ctx === WORD_CTX_REGEX) {
            if (ch === "]" && this.pos + 1 < this.length && this.source[this.pos + 1] === "]") {
                return true;
            }
            if (ch === "&" && this.pos + 1 < this.length && this.source[this.pos + 1] === "&") {
                return true;
            }
            if (ch === ")" && parenDepth === 0) {
                return true;
            }
            return IsWhitespace(ch) && parenDepth === 0;
        }
        if (ctx === WORD_CTX_COND) {
            if (ch === "]" && this.pos + 1 < this.length && this.source[this.pos + 1] === "]") {
                return true;
            }
            if (ch === ")") {
                return true;
            }
            if (ch === "&") {
                return true;
            }
            if (ch === "|") {
                return true;
            }
            if (ch === ";") {
                return true;
            }
            if (IsRedirectChar(ch) && !(this.pos + 1 < this.length && this.source[this.pos + 1] === "(")) {
                return true;
            }
            return IsWhitespace(ch);
        }
        if ((this.ParserState & ParserStateFlags_PST_EOFTOKEN) !== 0 && this.EofToken !== "" && ch === this.EofToken && bracketDepth === 0) {
            return true;
        }
        if (IsRedirectChar(ch) && this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
            return false;
        }
        return IsMetachar(ch) && bracketDepth === 0;
    };
    Lexer.prototype.ReadBracketExpression = function (chars, parts, forRegex, parenDepth) {
        if (forRegex) {
            var scan = this.pos + 1;
            if (scan < this.length && this.source[scan] === "^") {
                scan += 1;
            }
            if (scan < this.length && this.source[scan] === "]") {
                scan += 1;
            }
            var bracketWillClose = false;
            while (scan < this.length) {
                var sc = this.source[scan];
                if (sc === "]" && scan + 1 < this.length && this.source[scan + 1] === "]") {
                    break;
                }
                if (sc === ")" && parenDepth > 0) {
                    break;
                }
                if (sc === "&" && scan + 1 < this.length && this.source[scan + 1] === "&") {
                    break;
                }
                if (sc === "]") {
                    bracketWillClose = true;
                    break;
                }
                if (sc === "[" && scan + 1 < this.length && this.source[scan + 1] === ":") {
                    scan += 2;
                    while (scan < this.length && !(this.source[scan] === ":" && scan + 1 < this.length && this.source[scan + 1] === "]")) {
                        scan += 1;
                    }
                    if (scan < this.length) {
                        scan += 2;
                    }
                    continue;
                }
                scan += 1;
            }
            if (!bracketWillClose) {
                return false;
            }
        }
        else {
            if (this.pos + 1 >= this.length) {
                return false;
            }
            var nextCh = this.source[this.pos + 1];
            if (IsWhitespaceNoNewline(nextCh) || nextCh === "&" || nextCh === "|") {
                return false;
            }
        }
        chars.push(this.advance());
        if (!this.atEnd() && this.peek() === "^") {
            chars.push(this.advance());
        }
        if (!this.atEnd() && this.peek() === "]") {
            chars.push(this.advance());
        }
        while (!this.atEnd()) {
            var c = this.peek();
            if (c === "]") {
                chars.push(this.advance());
                break;
            }
            if (c === "[" && this.pos + 1 < this.length && this.source[this.pos + 1] === ":") {
                chars.push(this.advance());
                chars.push(this.advance());
                while (!this.atEnd() && !(this.peek() === ":" && this.pos + 1 < this.length && this.source[this.pos + 1] === "]")) {
                    chars.push(this.advance());
                }
                if (!this.atEnd()) {
                    chars.push(this.advance());
                    chars.push(this.advance());
                }
            }
            else {
                if (!forRegex && c === "[" && this.pos + 1 < this.length && this.source[this.pos + 1] === "=") {
                    chars.push(this.advance());
                    chars.push(this.advance());
                    while (!this.atEnd() && !(this.peek() === "=" && this.pos + 1 < this.length && this.source[this.pos + 1] === "]")) {
                        chars.push(this.advance());
                    }
                    if (!this.atEnd()) {
                        chars.push(this.advance());
                        chars.push(this.advance());
                    }
                }
                else {
                    if (!forRegex && c === "[" && this.pos + 1 < this.length && this.source[this.pos + 1] === ".") {
                        chars.push(this.advance());
                        chars.push(this.advance());
                        while (!this.atEnd() && !(this.peek() === "." && this.pos + 1 < this.length && this.source[this.pos + 1] === "]")) {
                            chars.push(this.advance());
                        }
                        if (!this.atEnd()) {
                            chars.push(this.advance());
                            chars.push(this.advance());
                        }
                    }
                    else {
                        if (forRegex && c === "$") {
                            this.SyncToParser();
                            if (!this.Parser.ParseDollarExpansion(chars, parts, false)) {
                                this.SyncFromParser();
                                chars.push(this.advance());
                            }
                            else {
                                this.SyncFromParser();
                            }
                        }
                        else {
                            chars.push(this.advance());
                        }
                    }
                }
            }
        }
        return true;
    };
    Lexer.prototype.ParseMatchedPair = function (openChar, closeChar, flags, initialWasDollar) {
        var start = this.pos;
        var count = 1;
        var chars = [];
        var passNext = false;
        var wasDollar = initialWasDollar;
        var wasGtlt = false;
        while (count > 0) {
            if (this.atEnd()) {
                throw new Error("".concat("unexpected EOF while looking for matching `".concat(closeChar, "'"), " at position ").concat(start));
            }
            var ch = this.advance();
            if ((flags & MatchedPairFlags_DOLBRACE) !== 0 && this.DolbraceState === DolbraceState_OP) {
                if (!"#%^,~:-=?+/".includes(ch)) {
                    this.DolbraceState = DolbraceState_WORD;
                }
            }
            if (passNext) {
                passNext = false;
                chars.push(ch);
                wasDollar = ch === "$";
                wasGtlt = "<>".includes(ch);
                continue;
            }
            if (openChar === "'") {
                if (ch === closeChar) {
                    count -= 1;
                    if (count === 0) {
                        break;
                    }
                }
                if (ch === "\\" && (flags & MatchedPairFlags_ALLOWESC) !== 0) {
                    passNext = true;
                }
                chars.push(ch);
                wasDollar = false;
                wasGtlt = false;
                continue;
            }
            if (ch === "\\") {
                if (!this.atEnd() && this.peek() === "\n") {
                    this.advance();
                    wasDollar = false;
                    wasGtlt = false;
                    continue;
                }
                passNext = true;
                chars.push(ch);
                wasDollar = false;
                wasGtlt = false;
                continue;
            }
            if (ch === closeChar) {
                count -= 1;
                if (count === 0) {
                    break;
                }
                chars.push(ch);
                wasDollar = false;
                wasGtlt = "<>".includes(ch);
                continue;
            }
            if (ch === openChar && openChar !== closeChar) {
                if (!((flags & MatchedPairFlags_DOLBRACE) !== 0 && openChar === "{")) {
                    count += 1;
                }
                chars.push(ch);
                wasDollar = false;
                wasGtlt = "<>".includes(ch);
                continue;
            }
            if ("'\"`".includes(ch) && openChar !== closeChar) {
                if (ch === "'") {
                    chars.push(ch);
                    var quoteFlags = wasDollar ? flags | MatchedPairFlags_ALLOWESC : flags;
                    var nested = this.ParseMatchedPair("'", "'", quoteFlags, false);
                    chars.push(nested);
                    chars.push("'");
                    wasDollar = false;
                    wasGtlt = false;
                    continue;
                }
                else {
                    if (ch === "\"") {
                        chars.push(ch);
                        var nested = this.ParseMatchedPair("\"", "\"", flags | MatchedPairFlags_DQUOTE, false);
                        chars.push(nested);
                        chars.push("\"");
                        wasDollar = false;
                        wasGtlt = false;
                        continue;
                    }
                    else {
                        if (ch === "`") {
                            chars.push(ch);
                            var nested = this.ParseMatchedPair("`", "`", flags, false);
                            chars.push(nested);
                            chars.push("`");
                            wasDollar = false;
                            wasGtlt = false;
                            continue;
                        }
                    }
                }
            }
            if (ch === "$" && !this.atEnd() && !((flags & MatchedPairFlags_EXTGLOB) !== 0)) {
                var nextCh = this.peek();
                if (wasDollar) {
                    chars.push(ch);
                    wasDollar = false;
                    wasGtlt = false;
                    continue;
                }
                if (nextCh === "{") {
                    if ((flags & MatchedPairFlags_ARITH) !== 0) {
                        var afterBracePos = this.pos + 1;
                        if (afterBracePos >= this.length || !IsFunsubChar(this.source[afterBracePos])) {
                            chars.push(ch);
                            wasDollar = true;
                            wasGtlt = false;
                            continue;
                        }
                    }
                    this.pos -= 1;
                    this.SyncToParser();
                    var inDquote = (flags & MatchedPairFlags_DQUOTE) !== 0;
                    var _a = this.Parser.ParseParamExpansion(inDquote), paramNode = _a[0], paramText = _a[1];
                    this.SyncFromParser();
                    if (paramNode !== null) {
                        chars.push(paramText);
                        wasDollar = false;
                        wasGtlt = false;
                    }
                    else {
                        chars.push(this.advance());
                        wasDollar = true;
                        wasGtlt = false;
                    }
                    continue;
                }
                else {
                    if (nextCh === "(") {
                        this.pos -= 1;
                        this.SyncToParser();
                        if (this.pos + 2 < this.length && this.source[this.pos + 2] === "(") {
                            var _b = this.Parser.ParseArithmeticExpansion(), arithNode = _b[0], arithText = _b[1];
                            this.SyncFromParser();
                            if (arithNode !== null) {
                                chars.push(arithText);
                                wasDollar = false;
                                wasGtlt = false;
                            }
                            else {
                                this.SyncToParser();
                                var _c = this.Parser.ParseCommandSubstitution(), cmdNode = _c[0], cmdText = _c[1];
                                this.SyncFromParser();
                                if (cmdNode !== null) {
                                    chars.push(cmdText);
                                    wasDollar = false;
                                    wasGtlt = false;
                                }
                                else {
                                    chars.push(this.advance());
                                    chars.push(this.advance());
                                    wasDollar = false;
                                    wasGtlt = false;
                                }
                            }
                        }
                        else {
                            var _d = this.Parser.ParseCommandSubstitution(), cmdNode = _d[0], cmdText = _d[1];
                            this.SyncFromParser();
                            if (cmdNode !== null) {
                                chars.push(cmdText);
                                wasDollar = false;
                                wasGtlt = false;
                            }
                            else {
                                chars.push(this.advance());
                                chars.push(this.advance());
                                wasDollar = false;
                                wasGtlt = false;
                            }
                        }
                        continue;
                    }
                    else {
                        if (nextCh === "[") {
                            this.pos -= 1;
                            this.SyncToParser();
                            var _f = this.Parser.ParseDeprecatedArithmetic(), arithNode = _f[0], arithText = _f[1];
                            this.SyncFromParser();
                            if (arithNode !== null) {
                                chars.push(arithText);
                                wasDollar = false;
                                wasGtlt = false;
                            }
                            else {
                                chars.push(this.advance());
                                wasDollar = true;
                                wasGtlt = false;
                            }
                            continue;
                        }
                    }
                }
            }
            if (ch === "(" && wasGtlt && (flags & (MatchedPairFlags_DOLBRACE | MatchedPairFlags_ARRAYSUB)) !== 0) {
                {
                    var direction = chars[chars.length - 1];
                    chars = chars.slice(0, chars.length - 1);
                }
                this.pos -= 1;
                this.SyncToParser();
                var _g = this.Parser.ParseProcessSubstitution(), procsubNode = _g[0], procsubText = _g[1];
                this.SyncFromParser();
                if (procsubNode !== null) {
                    chars.push(procsubText);
                    wasDollar = false;
                    wasGtlt = false;
                }
                else {
                    chars.push(direction);
                    chars.push(this.advance());
                    wasDollar = false;
                    wasGtlt = false;
                }
                continue;
            }
            chars.push(ch);
            wasDollar = ch === "$";
            wasGtlt = "<>".includes(ch);
        }
        return chars.join("");
    };
    Lexer.prototype.CollectParamArgument = function (flags, wasDollar) {
        return this.ParseMatchedPair("{", "}", flags | MatchedPairFlags_DOLBRACE, wasDollar);
    };
    Lexer.prototype.ReadWordInternal = function (ctx, atCommandStart, inArrayLiteral, inAssignBuiltin) {
        var _a;
        var start = this.pos;
        var chars = [];
        var parts = [];
        var bracketDepth = 0;
        var bracketStartPos = -1;
        var seenEquals = false;
        var parenDepth = 0;
        while (!this.atEnd()) {
            var ch = this.peek();
            if (ctx === WORD_CTX_REGEX) {
                if (ch === "\\" && this.pos + 1 < this.length && this.source[this.pos + 1] === "\n") {
                    this.advance();
                    this.advance();
                    continue;
                }
            }
            if (ctx !== WORD_CTX_NORMAL && this.IsWordTerminator(ctx, ch, bracketDepth, parenDepth)) {
                break;
            }
            if (ctx === WORD_CTX_NORMAL && ch === "[") {
                if (bracketDepth > 0) {
                    bracketDepth += 1;
                    chars.push(this.advance());
                    continue;
                }
                if (chars.length > 0 && atCommandStart && !seenEquals && IsArrayAssignmentPrefix(chars)) {
                    var prevChar = chars[chars.length - 1];
                    if (/^[a-zA-Z0-9]$/.test(prevChar) || prevChar === "_") {
                        bracketStartPos = this.pos;
                        bracketDepth += 1;
                        chars.push(this.advance());
                        continue;
                    }
                }
                if (!(chars.length > 0) && !seenEquals && inArrayLiteral) {
                    bracketStartPos = this.pos;
                    bracketDepth += 1;
                    chars.push(this.advance());
                    continue;
                }
            }
            if (ctx === WORD_CTX_NORMAL && ch === "]" && bracketDepth > 0) {
                bracketDepth -= 1;
                chars.push(this.advance());
                continue;
            }
            if (ctx === WORD_CTX_NORMAL && ch === "=" && bracketDepth === 0) {
                seenEquals = true;
            }
            if (ctx === WORD_CTX_REGEX && ch === "(") {
                parenDepth += 1;
                chars.push(this.advance());
                continue;
            }
            if (ctx === WORD_CTX_REGEX && ch === ")") {
                if (parenDepth > 0) {
                    parenDepth -= 1;
                    chars.push(this.advance());
                    continue;
                }
                break;
            }
            if ((ctx === WORD_CTX_COND || ctx === WORD_CTX_REGEX) && ch === "[") {
                var forRegex = ctx === WORD_CTX_REGEX;
                if (this.ReadBracketExpression(chars, parts, forRegex, parenDepth)) {
                    continue;
                }
                chars.push(this.advance());
                continue;
            }
            if (ctx === WORD_CTX_COND && ch === "(") {
                if (this.Extglob && chars.length > 0 && IsExtglobPrefix(chars[chars.length - 1])) {
                    chars.push(this.advance());
                    var content = this.ParseMatchedPair("(", ")", MatchedPairFlags_EXTGLOB, false);
                    chars.push(content);
                    chars.push(")");
                    continue;
                }
                else {
                    break;
                }
            }
            if (ctx === WORD_CTX_REGEX && IsWhitespace(ch) && parenDepth > 0) {
                chars.push(this.advance());
                continue;
            }
            if (ch === "'") {
                this.advance();
                var trackNewline = ctx === WORD_CTX_NORMAL;
                var sawNewline;
                _a = this.ReadSingleQuote(start), content = _a[0], sawNewline = _a[1];
                chars.push(content);
                if (trackNewline && sawNewline && this.Parser !== null) {
                    this.Parser.SawNewlineInSingleQuote = true;
                }
                continue;
            }
            if (ch === "\"") {
                this.advance();
                if (ctx === WORD_CTX_NORMAL) {
                    chars.push("\"");
                    var inSingleInDquote = false;
                    while (!this.atEnd() && (inSingleInDquote || this.peek() !== "\"")) {
                        var c = this.peek();
                        if (inSingleInDquote) {
                            chars.push(this.advance());
                            if (c === "'") {
                                inSingleInDquote = false;
                            }
                            continue;
                        }
                        if (c === "\\" && this.pos + 1 < this.length) {
                            var nextC = this.source[this.pos + 1];
                            if (nextC === "\n") {
                                this.advance();
                                this.advance();
                            }
                            else {
                                chars.push(this.advance());
                                chars.push(this.advance());
                            }
                        }
                        else {
                            if (c === "$") {
                                this.SyncToParser();
                                if (!this.Parser.ParseDollarExpansion(chars, parts, true)) {
                                    this.SyncFromParser();
                                    chars.push(this.advance());
                                }
                                else {
                                    this.SyncFromParser();
                                }
                            }
                            else {
                                if (c === "`") {
                                    this.SyncToParser();
                                    var _b = this.Parser.ParseBacktickSubstitution(), cmdsubResult0 = _b[0], cmdsubResult1 = _b[1];
                                    this.SyncFromParser();
                                    if (cmdsubResult0 !== null) {
                                        parts.push(cmdsubResult0);
                                        chars.push(cmdsubResult1);
                                    }
                                    else {
                                        chars.push(this.advance());
                                    }
                                }
                                else {
                                    chars.push(this.advance());
                                }
                            }
                        }
                    }
                    if (this.atEnd()) {
                        throw new Error("".concat("Unterminated double quote", " at position ").concat(start));
                    }
                    chars.push(this.advance());
                }
                else {
                    var handleLineContinuation = ctx === WORD_CTX_COND;
                    this.SyncToParser();
                    this.Parser.ScanDoubleQuote(chars, parts, start, handleLineContinuation);
                    this.SyncFromParser();
                }
                continue;
            }
            if (ch === "\\" && this.pos + 1 < this.length) {
                var nextCh = this.source[this.pos + 1];
                if (ctx !== WORD_CTX_REGEX && nextCh === "\n") {
                    this.advance();
                    this.advance();
                }
                else {
                    chars.push(this.advance());
                    chars.push(this.advance());
                }
                continue;
            }
            if (ctx !== WORD_CTX_REGEX && ch === "$" && this.pos + 1 < this.length && this.source[this.pos + 1] === "'") {
                var _c = this.ReadAnsiCQuote(), ansiResult0 = _c[0], ansiResult1 = _c[1];
                if (ansiResult0 !== null) {
                    parts.push(ansiResult0);
                    chars.push(ansiResult1);
                }
                else {
                    chars.push(this.advance());
                }
                continue;
            }
            if (ctx !== WORD_CTX_REGEX && ch === "$" && this.pos + 1 < this.length && this.source[this.pos + 1] === "\"") {
                var _d = this.ReadLocaleString(), localeResult0 = _d[0], localeResult1 = _d[1], localeResult2 = _d[2];
                if (localeResult0 !== null) {
                    parts.push(localeResult0);
                    parts.push.apply(parts, localeResult2);
                    chars.push(localeResult1);
                }
                else {
                    chars.push(this.advance());
                }
                continue;
            }
            if (ch === "$") {
                this.SyncToParser();
                if (!this.Parser.ParseDollarExpansion(chars, parts, false)) {
                    this.SyncFromParser();
                    chars.push(this.advance());
                }
                else {
                    this.SyncFromParser();
                    if (this.Extglob && ctx === WORD_CTX_NORMAL && chars.length > 0 && chars[chars.length - 1].length === 2 && chars[chars.length - 1][0] === "$" && "?*@".includes(chars[chars.length - 1][1]) && !this.atEnd() && this.peek() === "(") {
                        chars.push(this.advance());
                        var content = this.ParseMatchedPair("(", ")", MatchedPairFlags_EXTGLOB, false);
                        chars.push(content);
                        chars.push(")");
                    }
                }
                continue;
            }
            if (ctx !== WORD_CTX_REGEX && ch === "`") {
                this.SyncToParser();
                var _f = this.Parser.ParseBacktickSubstitution(), cmdsubResult0 = _f[0], cmdsubResult1 = _f[1];
                this.SyncFromParser();
                if (cmdsubResult0 !== null) {
                    parts.push(cmdsubResult0);
                    chars.push(cmdsubResult1);
                }
                else {
                    chars.push(this.advance());
                }
                continue;
            }
            if (ctx !== WORD_CTX_REGEX && IsRedirectChar(ch) && this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
                this.SyncToParser();
                var _g = this.Parser.ParseProcessSubstitution(), procsubResult0 = _g[0], procsubResult1 = _g[1];
                this.SyncFromParser();
                if (procsubResult0 !== null) {
                    parts.push(procsubResult0);
                    chars.push(procsubResult1);
                }
                else {
                    if (procsubResult1 !== "") {
                        chars.push(procsubResult1);
                    }
                    else {
                        chars.push(this.advance());
                        if (ctx === WORD_CTX_NORMAL) {
                            chars.push(this.advance());
                        }
                    }
                }
                continue;
            }
            if (ctx === WORD_CTX_NORMAL && ch === "(" && chars.length > 0 && bracketDepth === 0) {
                var isArrayAssign = false;
                if (chars.length >= 3 && chars[chars.length - 2] === "+" && chars[chars.length - 1] === "=") {
                    isArrayAssign = IsArrayAssignmentPrefix(chars.slice(0, chars.length - 2));
                }
                else {
                    if (chars[chars.length - 1] === "=" && chars.length >= 2) {
                        isArrayAssign = IsArrayAssignmentPrefix(chars.slice(0, chars.length - 1));
                    }
                }
                if (isArrayAssign && (atCommandStart || inAssignBuiltin)) {
                    this.SyncToParser();
                    var _h = this.Parser.ParseArrayLiteral(), arrayResult0 = _h[0], arrayResult1 = _h[1];
                    this.SyncFromParser();
                    if (arrayResult0 !== null) {
                        parts.push(arrayResult0);
                        chars.push(arrayResult1);
                    }
                    else {
                        break;
                    }
                    continue;
                }
            }
            if (this.Extglob && ctx === WORD_CTX_NORMAL && IsExtglobPrefix(ch) && this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
                chars.push(this.advance());
                chars.push(this.advance());
                var content = this.ParseMatchedPair("(", ")", MatchedPairFlags_EXTGLOB, false);
                chars.push(content);
                chars.push(")");
                continue;
            }
            if (ctx === WORD_CTX_NORMAL && (this.ParserState & ParserStateFlags_PST_EOFTOKEN) !== 0 && this.EofToken !== "" && ch === this.EofToken && bracketDepth === 0) {
                if (!(chars.length > 0)) {
                    chars.push(this.advance());
                }
                break;
            }
            if (ctx === WORD_CTX_NORMAL && IsMetachar(ch) && bracketDepth === 0) {
                break;
            }
            chars.push(this.advance());
        }
        if (bracketDepth > 0 && bracketStartPos !== -1 && this.atEnd()) {
            throw new Error("".concat("unexpected EOF looking for `]'", " at position ").concat(bracketStartPos));
        }
        if (!(chars.length > 0)) {
            return null;
        }
        if (parts.length > 0) {
            return new Word(chars.join(""), parts, "word");
        }
        return new Word(chars.join(""), null, "word");
    };
    Lexer.prototype.ReadWord = function () {
        var start = this.pos;
        if (this.pos >= this.length) {
            return null;
        }
        var c = this.peek();
        if (c === "") {
            return null;
        }
        var isProcsub = (c === "<" || c === ">") && this.pos + 1 < this.length && this.source[this.pos + 1] === "(";
        var isRegexParen = this.WordContext === WORD_CTX_REGEX && (c === "(" || c === ")");
        if (this.isMetachar(c) && !isProcsub && !isRegexParen) {
            return null;
        }
        var word = this.ReadWordInternal(this.WordContext, this.AtCommandStart, this.InArrayLiteral, this.InAssignBuiltin);
        if (word === null) {
            return null;
        }
        return new Token(TokenType_WORD, word.value, start, null, word);
    };
    Lexer.prototype.nextToken = function () {
        if (this.TokenCache !== null) {
            var tok = this.TokenCache;
            this.TokenCache = null;
            this.LastReadToken = tok;
            return tok;
        }
        this.skipBlanks();
        if (this.atEnd()) {
            var tok = new Token(TokenType_EOF, "", this.pos, [], []);
            this.LastReadToken = tok;
            return tok;
        }
        if (this.EofToken !== "" && this.peek() === this.EofToken && !((this.ParserState & ParserStateFlags_PST_CASEPAT) !== 0) && !((this.ParserState & ParserStateFlags_PST_EOFTOKEN) !== 0)) {
            var tok = new Token(TokenType_EOF, "", this.pos, [], []);
            this.LastReadToken = tok;
            return tok;
        }
        while (this.SkipComment()) {
            this.skipBlanks();
            if (this.atEnd()) {
                var tok = new Token(TokenType_EOF, "", this.pos, [], []);
                this.LastReadToken = tok;
                return tok;
            }
            if (this.EofToken !== "" && this.peek() === this.EofToken && !((this.ParserState & ParserStateFlags_PST_CASEPAT) !== 0) && !((this.ParserState & ParserStateFlags_PST_EOFTOKEN) !== 0)) {
                var tok = new Token(TokenType_EOF, "", this.pos, [], []);
                this.LastReadToken = tok;
                return tok;
            }
        }
        var tok = this.ReadOperator();
        if (tok !== null) {
            this.LastReadToken = tok;
            return tok;
        }
        tok = this.ReadWord();
        if (tok !== null) {
            this.LastReadToken = tok;
            return tok;
        }
        tok = new Token(TokenType_EOF, "", this.pos, [], []);
        this.LastReadToken = tok;
        return tok;
    };
    Lexer.prototype.peekToken = function () {
        if (this.TokenCache === null) {
            var savedLast = this.LastReadToken;
            this.TokenCache = this.nextToken();
            this.LastReadToken = savedLast;
        }
        return this.TokenCache;
    };
    Lexer.prototype.ReadAnsiCQuote = function () {
        if (this.atEnd() || this.peek() !== "$") {
            return [null, ""];
        }
        if (this.pos + 1 >= this.length || this.source[this.pos + 1] !== "'") {
            return [null, ""];
        }
        var start = this.pos;
        this.advance();
        this.advance();
        var contentChars = [];
        var foundClose = false;
        while (!this.atEnd()) {
            var ch = this.peek();
            if (ch === "'") {
                this.advance();
                foundClose = true;
                break;
            }
            else {
                if (ch === "\\") {
                    contentChars.push(this.advance());
                    if (!this.atEnd()) {
                        contentChars.push(this.advance());
                    }
                }
                else {
                    contentChars.push(this.advance());
                }
            }
        }
        if (!foundClose) {
            throw new Error("".concat("unexpected EOF while looking for matching `''", " at position ").concat(start));
        }
        var text = Substring(this.source, start, this.pos);
        var content = contentChars.join("");
        var node = new AnsiCQuote(content, "ansi-c");
        return [node, text];
    };
    Lexer.prototype.SyncToParser = function () {
        if (this.Parser !== null) {
            this.Parser.pos = this.pos;
        }
    };
    Lexer.prototype.SyncFromParser = function () {
        if (this.Parser !== null) {
            this.pos = this.Parser.pos;
        }
    };
    Lexer.prototype.ReadLocaleString = function () {
        if (this.atEnd() || this.peek() !== "$") {
            return [null, "", []];
        }
        if (this.pos + 1 >= this.length || this.source[this.pos + 1] !== "\"") {
            return [null, "", []];
        }
        var start = this.pos;
        this.advance();
        this.advance();
        var contentChars = [];
        var innerParts = [];
        var foundClose = false;
        while (!this.atEnd()) {
            var ch = this.peek();
            if (ch === "\"") {
                this.advance();
                foundClose = true;
                break;
            }
            else {
                if (ch === "\\" && this.pos + 1 < this.length) {
                    var nextCh = this.source[this.pos + 1];
                    if (nextCh === "\n") {
                        this.advance();
                        this.advance();
                    }
                    else {
                        contentChars.push(this.advance());
                        contentChars.push(this.advance());
                    }
                }
                else {
                    if (ch === "$" && this.pos + 2 < this.length && this.source[this.pos + 1] === "(" && this.source[this.pos + 2] === "(") {
                        this.SyncToParser();
                        var _a = this.Parser.ParseArithmeticExpansion(), arithNode = _a[0], arithText = _a[1];
                        this.SyncFromParser();
                        if (arithNode !== null) {
                            innerParts.push(arithNode);
                            contentChars.push(arithText);
                        }
                        else {
                            this.SyncToParser();
                            var _b = this.Parser.ParseCommandSubstitution(), cmdsubNode = _b[0], cmdsubText = _b[1];
                            this.SyncFromParser();
                            if (cmdsubNode !== null) {
                                innerParts.push(cmdsubNode);
                                contentChars.push(cmdsubText);
                            }
                            else {
                                contentChars.push(this.advance());
                            }
                        }
                    }
                    else {
                        if (IsExpansionStart(this.source, this.pos, "$(")) {
                            this.SyncToParser();
                            var _c = this.Parser.ParseCommandSubstitution(), cmdsubNode = _c[0], cmdsubText = _c[1];
                            this.SyncFromParser();
                            if (cmdsubNode !== null) {
                                innerParts.push(cmdsubNode);
                                contentChars.push(cmdsubText);
                            }
                            else {
                                contentChars.push(this.advance());
                            }
                        }
                        else {
                            if (ch === "$") {
                                this.SyncToParser();
                                var _d = this.Parser.ParseParamExpansion(false), paramNode = _d[0], paramText = _d[1];
                                this.SyncFromParser();
                                if (paramNode !== null) {
                                    innerParts.push(paramNode);
                                    contentChars.push(paramText);
                                }
                                else {
                                    contentChars.push(this.advance());
                                }
                            }
                            else {
                                if (ch === "`") {
                                    this.SyncToParser();
                                    var _f = this.Parser.ParseBacktickSubstitution(), cmdsubNode = _f[0], cmdsubText = _f[1];
                                    this.SyncFromParser();
                                    if (cmdsubNode !== null) {
                                        innerParts.push(cmdsubNode);
                                        contentChars.push(cmdsubText);
                                    }
                                    else {
                                        contentChars.push(this.advance());
                                    }
                                }
                                else {
                                    contentChars.push(this.advance());
                                }
                            }
                        }
                    }
                }
            }
        }
        if (!foundClose) {
            this.pos = start;
            return [null, "", []];
        }
        var content = contentChars.join("");
        var text = "$\"" + content + "\"";
        return [new LocaleString(content, "locale"), text, innerParts];
    };
    Lexer.prototype.UpdateDolbraceForOp = function (op, hasParam) {
        if (this.DolbraceState === DolbraceState_NONE) {
            return;
        }
        if (op === "" || op.length === 0) {
            return;
        }
        var firstChar = op[0];
        if (this.DolbraceState === DolbraceState_PARAM && hasParam) {
            if ("%#^,".includes(firstChar)) {
                this.DolbraceState = DolbraceState_QUOTE;
                return;
            }
            if (firstChar === "/") {
                this.DolbraceState = DolbraceState_QUOTE2;
                return;
            }
        }
        if (this.DolbraceState === DolbraceState_PARAM) {
            if ("#%^,~:-=?+/".includes(firstChar)) {
                this.DolbraceState = DolbraceState_OP;
            }
        }
    };
    Lexer.prototype.ConsumeParamOperator = function () {
        if (this.atEnd()) {
            return "";
        }
        var ch = this.peek();
        if (ch === ":") {
            this.advance();
            if (this.atEnd()) {
                return ":";
            }
            var nextCh = this.peek();
            if (IsSimpleParamOp(nextCh)) {
                this.advance();
                return ":" + nextCh;
            }
            return ":";
        }
        if (IsSimpleParamOp(ch)) {
            this.advance();
            return ch;
        }
        if (ch === "#") {
            this.advance();
            if (!this.atEnd() && this.peek() === "#") {
                this.advance();
                return "##";
            }
            return "#";
        }
        if (ch === "%") {
            this.advance();
            if (!this.atEnd() && this.peek() === "%") {
                this.advance();
                return "%%";
            }
            return "%";
        }
        if (ch === "/") {
            this.advance();
            if (!this.atEnd()) {
                var nextCh = this.peek();
                if (nextCh === "/") {
                    this.advance();
                    return "//";
                }
                else {
                    if (nextCh === "#") {
                        this.advance();
                        return "/#";
                    }
                    else {
                        if (nextCh === "%") {
                            this.advance();
                            return "/%";
                        }
                    }
                }
            }
            return "/";
        }
        if (ch === "^") {
            this.advance();
            if (!this.atEnd() && this.peek() === "^") {
                this.advance();
                return "^^";
            }
            return "^";
        }
        if (ch === ",") {
            this.advance();
            if (!this.atEnd() && this.peek() === ",") {
                this.advance();
                return ",,";
            }
            return ",";
        }
        if (ch === "@") {
            this.advance();
            return "@";
        }
        return "";
    };
    Lexer.prototype.ParamSubscriptHasClose = function (startPos) {
        var depth = 1;
        var i = startPos + 1;
        var quote = newQuoteState();
        while (i < this.length) {
            var c = this.source[i];
            if (quote.single) {
                if (c === "'") {
                    quote.single = false;
                }
                i += 1;
                continue;
            }
            if (quote.double) {
                if (c === "\\" && i + 1 < this.length) {
                    i += 2;
                    continue;
                }
                if (c === "\"") {
                    quote.double = false;
                }
                i += 1;
                continue;
            }
            if (c === "'") {
                quote.single = true;
                i += 1;
                continue;
            }
            if (c === "\"") {
                quote.double = true;
                i += 1;
                continue;
            }
            if (c === "\\") {
                i += 2;
                continue;
            }
            if (c === "}") {
                return false;
            }
            if (c === "[") {
                depth += 1;
            }
            else {
                if (c === "]") {
                    depth -= 1;
                    if (depth === 0) {
                        return true;
                    }
                }
            }
            i += 1;
        }
        return false;
    };
    Lexer.prototype.ConsumeParamName = function () {
        if (this.atEnd()) {
            return "";
        }
        var ch = this.peek();
        if (IsSpecialParam(ch)) {
            if (ch === "$" && this.pos + 1 < this.length && "{'\"".includes(this.source[this.pos + 1])) {
                return "";
            }
            this.advance();
            return ch;
        }
        if (/^[0-9]+$/.test(ch)) {
            var nameChars = [];
            while (!this.atEnd() && /^[0-9]+$/.test(this.peek())) {
                nameChars.push(this.advance());
            }
            return nameChars.join("");
        }
        if (/^[a-zA-Z]$/.test(ch) || ch === "_") {
            var nameChars = [];
            while (!this.atEnd()) {
                var c = this.peek();
                if (/^[a-zA-Z0-9]$/.test(c) || c === "_") {
                    nameChars.push(this.advance());
                }
                else {
                    if (c === "[") {
                        if (!this.ParamSubscriptHasClose(this.pos)) {
                            break;
                        }
                        nameChars.push(this.advance());
                        var content = this.ParseMatchedPair("[", "]", MatchedPairFlags_ARRAYSUB, false);
                        nameChars.push(content);
                        nameChars.push("]");
                        break;
                    }
                    else {
                        break;
                    }
                }
            }
            if (nameChars.length > 0) {
                return nameChars.join("");
            }
            else {
                return "";
            }
        }
        return "";
    };
    Lexer.prototype.ReadParamExpansion = function (inDquote) {
        if (this.atEnd() || this.peek() !== "$") {
            return [null, ""];
        }
        var start = this.pos;
        this.advance();
        if (this.atEnd()) {
            this.pos = start;
            return [null, ""];
        }
        var ch = this.peek();
        if (ch === "{") {
            this.advance();
            return this.ReadBracedParam(start, inDquote);
        }
        if (IsSpecialParamUnbraced(ch) || IsDigit(ch) || ch === "#") {
            this.advance();
            var text = Substring(this.source, start, this.pos);
            return [new ParamExpansion(ch, [], [], "param"), text];
        }
        if (/^[a-zA-Z]$/.test(ch) || ch === "_") {
            var nameStart = this.pos;
            while (!this.atEnd()) {
                var c = this.peek();
                if (/^[a-zA-Z0-9]$/.test(c) || c === "_") {
                    this.advance();
                }
                else {
                    break;
                }
            }
            var name = Substring(this.source, nameStart, this.pos);
            var text = Substring(this.source, start, this.pos);
            return [new ParamExpansion(name, [], [], "param"), text];
        }
        this.pos = start;
        return [null, ""];
    };
    Lexer.prototype.ReadBracedParam = function (start, inDquote) {
        if (this.atEnd()) {
            throw new Error("".concat("unexpected EOF looking for `}'", " at position ").concat(start));
        }
        var savedDolbrace = this.DolbraceState;
        this.DolbraceState = DolbraceState_PARAM;
        var ch = this.peek();
        if (IsFunsubChar(ch)) {
            this.DolbraceState = savedDolbrace;
            return this.ReadFunsub(start);
        }
        if (ch === "#") {
            this.advance();
            var param = this.ConsumeParamName();
            if (param !== "" && !this.atEnd() && this.peek() === "}") {
                this.advance();
                var text = Substring(this.source, start, this.pos);
                this.DolbraceState = savedDolbrace;
                return [new ParamLength(param, "param-len"), text];
            }
            this.pos = start + 2;
        }
        if (ch === "!") {
            this.advance();
            while (!this.atEnd() && IsWhitespaceNoNewline(this.peek())) {
                this.advance();
            }
            var param = this.ConsumeParamName();
            if (param !== "") {
                while (!this.atEnd() && IsWhitespaceNoNewline(this.peek())) {
                    this.advance();
                }
                if (!this.atEnd() && this.peek() === "}") {
                    this.advance();
                    var text = Substring(this.source, start, this.pos);
                    this.DolbraceState = savedDolbrace;
                    return [new ParamIndirect(param, [], [], "param-indirect"), text];
                }
                if (!this.atEnd() && IsAtOrStar(this.peek())) {
                    var suffix = this.advance();
                    var trailing = this.ParseMatchedPair("{", "}", MatchedPairFlags_DOLBRACE, false);
                    var text = Substring(this.source, start, this.pos);
                    this.DolbraceState = savedDolbrace;
                    return [new ParamIndirect(param + suffix + trailing, [], [], "param-indirect"), text];
                }
                var op = this.ConsumeParamOperator();
                if (op === "" && !this.atEnd() && !"}\"'`".includes(this.peek())) {
                    op = this.advance();
                }
                if (op !== "" && !"\"'`".includes(op)) {
                    var arg = this.ParseMatchedPair("{", "}", MatchedPairFlags_DOLBRACE, false);
                    var text = Substring(this.source, start, this.pos);
                    this.DolbraceState = savedDolbrace;
                    return [new ParamIndirect(param, op, arg, "param-indirect"), text];
                }
                if (this.atEnd()) {
                    this.DolbraceState = savedDolbrace;
                    throw new Error("".concat("unexpected EOF looking for `}'", " at position ").concat(start));
                }
                this.pos = start + 2;
            }
            else {
                this.pos = start + 2;
            }
        }
        var param = this.ConsumeParamName();
        if (!(param !== "")) {
            if (!this.atEnd() && ("-=+?".includes(this.peek()) || this.peek() === ":" && this.pos + 1 < this.length && IsSimpleParamOp(this.source[this.pos + 1]))) {
                param = "";
            }
            else {
                var content = this.ParseMatchedPair("{", "}", MatchedPairFlags_DOLBRACE, false);
                var text = "${" + content + "}";
                this.DolbraceState = savedDolbrace;
                return [new ParamExpansion(content, [], [], "param"), text];
            }
        }
        if (this.atEnd()) {
            this.DolbraceState = savedDolbrace;
            throw new Error("".concat("unexpected EOF looking for `}'", " at position ").concat(start));
        }
        if (this.peek() === "}") {
            this.advance();
            var text = Substring(this.source, start, this.pos);
            this.DolbraceState = savedDolbrace;
            return [new ParamExpansion(param, [], [], "param"), text];
        }
        var op = this.ConsumeParamOperator();
        if (op === "") {
            if (!this.atEnd() && this.peek() === "$" && this.pos + 1 < this.length && (this.source[this.pos + 1] === "\"" || this.source[this.pos + 1] === "'")) {
                var dollarCount = 1 + CountConsecutiveDollarsBefore(this.source, this.pos);
                if (dollarCount % 2 === 1) {
                    op = "";
                }
                else {
                    op = this.advance();
                }
            }
            else {
                if (!this.atEnd() && this.peek() === "`") {
                    var backtickPos = this.pos;
                    this.advance();
                    while (!this.atEnd() && this.peek() !== "`") {
                        var bc = this.peek();
                        if (bc === "\\" && this.pos + 1 < this.length) {
                            var nextC = this.source[this.pos + 1];
                            if (IsEscapeCharInBacktick(nextC)) {
                                this.advance();
                            }
                        }
                        this.advance();
                    }
                    if (this.atEnd()) {
                        this.DolbraceState = savedDolbrace;
                        throw new Error("".concat("Unterminated backtick", " at position ").concat(backtickPos));
                    }
                    this.advance();
                    op = "`";
                }
                else {
                    if (!this.atEnd() && this.peek() === "$" && this.pos + 1 < this.length && this.source[this.pos + 1] === "{") {
                        op = "";
                    }
                    else {
                        if (!this.atEnd() && (this.peek() === "'" || this.peek() === "\"")) {
                            op = "";
                        }
                        else {
                            if (!this.atEnd() && this.peek() === "\\") {
                                op = this.advance();
                                if (!this.atEnd()) {
                                    op += this.advance();
                                }
                            }
                            else {
                                op = this.advance();
                            }
                        }
                    }
                }
            }
        }
        this.UpdateDolbraceForOp(op, param.length > 0);
        try {
            var flags = inDquote ? MatchedPairFlags_DQUOTE : MatchedPairFlags_NONE;
            var paramEndsWithDollar = param !== "" && param.endsWith("$");
            var arg = this.CollectParamArgument(flags, paramEndsWithDollar);
        }
        catch (e) {
            this.DolbraceState = savedDolbrace;
            throw new Error("".concat("", " at position ").concat(0));
        }
        if ((op === "<" || op === ">") && arg.startsWith("(") && arg.endsWith(")")) {
            var inner = arg.slice(1, arg.length - 1);
            try {
                var subParser = newParser(inner, true, this.Parser.Extglob);
                var parsed = subParser.parseList(true);
                if (parsed !== null && subParser.atEnd()) {
                    var formatted = FormatCmdsubNode(parsed, 0, true, false, true);
                    var arg = "(" + formatted + ")";
                }
            }
            catch (_e) {
            }
        }
        var text = "${" + param + op + arg + "}";
        this.DolbraceState = savedDolbrace;
        return [new ParamExpansion(param, op, arg, "param"), text];
    };
    Lexer.prototype.ReadFunsub = function (start) {
        return this.Parser.ParseFunsub(start);
    };
    return Lexer;
}());
var Word = /** @class */ (function () {
    function Word(value, parts, kind) {
        if (value === void 0) { value = ""; }
        if (parts === void 0) { parts = []; }
        if (kind === void 0) { kind = ""; }
        this.value = value;
        this.parts = parts !== null && parts !== void 0 ? parts : [];
        this.kind = kind;
    }
    Word.prototype.getKind = function () {
        return this.kind;
    };
    Word.prototype.toSexp = function () {
        var value = this.value;
        value = this.ExpandAllAnsiCQuotes(value);
        value = this.StripLocaleStringDollars(value);
        value = this.NormalizeArrayWhitespace(value);
        value = this.FormatCommandSubstitutions(value, false);
        value = this.NormalizeParamExpansionNewlines(value);
        value = this.StripArithLineContinuations(value);
        value = this.DoubleCtlescSmart(value);
        value = value.replace(//g, "");
        value = value.replace(/\\/g, "\\\\");
        if (value.endsWith("\\\\") && !value.endsWith("\\\\\\\\")) {
            value = value + "\\\\";
        }
        var escaped = value.replace(/"/g, "\\\"").replace(/\n/g, "\\n").replace(/\t/g, "\\t");
        return "(word \"" + escaped + "\")";
    };
    Word.prototype.AppendWithCtlesc = function (result, byteVal) {
        result.push(byteVal);
    };
    Word.prototype.DoubleCtlescSmart = function (value) {
        var result = [];
        var quote = newQuoteState();
        for (var _i = 0, value_1 = value; _i < value_1.length; _i++) {
            var c = value_1[_i];
            if (c === "'" && !quote.double) {
                quote.single = !quote.single;
            }
            else {
                if (c === "\"" && !quote.single) {
                    quote.double = !quote.double;
                }
            }
            result.push(c);
            if (c === "") {
                if (quote.double) {
                    var bsCount = 0;
                    for (var _a = 0, _b = range(result.length - 2, -1, -1); _a < _b.length; _a++) {
                        var j = _b[_a];
                        if (result[j] === "\\") {
                            bsCount += 1;
                        }
                        else {
                            break;
                        }
                    }
                    if (bsCount % 2 === 0) {
                        result.push("");
                    }
                }
                else {
                    result.push("");
                }
            }
        }
        return result.join("");
    };
    Word.prototype.NormalizeParamExpansionNewlines = function (value) {
        var result = [];
        var i = 0;
        var quote = newQuoteState();
        while (i < value.length) {
            var c = value[i];
            if (c === "'" && !quote.double) {
                quote.single = !quote.single;
                result.push(c);
                i += 1;
            }
            else {
                if (c === "\"" && !quote.single) {
                    quote.double = !quote.double;
                    result.push(c);
                    i += 1;
                }
                else {
                    if (IsExpansionStart(value, i, "${") && !quote.single) {
                        result.push("$");
                        result.push("{");
                        i += 2;
                        var hadLeadingNewline = i < value.length && value[i] === "\n";
                        if (hadLeadingNewline) {
                            result.push(" ");
                            i += 1;
                        }
                        var depth = 1;
                        while (i < value.length && depth > 0) {
                            var ch = value[i];
                            if (ch === "\\" && i + 1 < value.length && !quote.single) {
                                if (value[i + 1] === "\n") {
                                    i += 2;
                                    continue;
                                }
                                result.push(ch);
                                result.push(value[i + 1]);
                                i += 2;
                                continue;
                            }
                            if (ch === "'" && !quote.double) {
                                quote.single = !quote.single;
                            }
                            else {
                                if (ch === "\"" && !quote.single) {
                                    quote.double = !quote.double;
                                }
                                else {
                                    if (!quote.inQuotes()) {
                                        if (ch === "{") {
                                            depth += 1;
                                        }
                                        else {
                                            if (ch === "}") {
                                                depth -= 1;
                                                if (depth === 0) {
                                                    if (hadLeadingNewline) {
                                                        result.push(" ");
                                                    }
                                                    result.push(ch);
                                                    i += 1;
                                                    break;
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            result.push(ch);
                            i += 1;
                        }
                    }
                    else {
                        result.push(c);
                        i += 1;
                    }
                }
            }
        }
        return result.join("");
    };
    Word.prototype.ShSingleQuote = function (s) {
        if (!(s !== "")) {
            return "''";
        }
        if (s === "'") {
            return "\\'";
        }
        var result = ["'"];
        for (var _i = 0, s_1 = s; _i < s_1.length; _i++) {
            var c = s_1[_i];
            if (c === "'") {
                result.push("'\\''");
            }
            else {
                result.push(c);
            }
        }
        result.push("'");
        return result.join("");
    };
    Word.prototype.AnsiCToBytes = function (inner) {
        var result = [];
        var i = 0;
        while (i < inner.length) {
            if (inner[i] === "\\" && i + 1 < inner.length) {
                var c = inner[i + 1];
                var simple = GetAnsiEscape(c);
                if (simple >= 0) {
                    result.push(simple);
                    i += 2;
                }
                else {
                    if (c === "'") {
                        result.push(39);
                        i += 2;
                    }
                    else {
                        if (c === "x") {
                            if (i + 2 < inner.length && inner[i + 2] === "{") {
                                var j = i + 3;
                                while (j < inner.length && IsHexDigit(inner[j])) {
                                    j += 1;
                                }
                                var hexStr = Substring(inner, i + 3, j);
                                if (j < inner.length && inner[j] === "}") {
                                    j += 1;
                                }
                                if (!(hexStr !== "")) {
                                    return result;
                                }
                                var byteVal = parseInt(hexStr, 16) & 255;
                                if (byteVal === 0) {
                                    return result;
                                }
                                this.AppendWithCtlesc(result, byteVal);
                                i = j;
                            }
                            else {
                                var j = i + 2;
                                while (j < inner.length && j < i + 4 && IsHexDigit(inner[j])) {
                                    j += 1;
                                }
                                if (j > i + 2) {
                                    var byteVal = parseInt(Substring(inner, i + 2, j), 16);
                                    if (byteVal === 0) {
                                        return result;
                                    }
                                    this.AppendWithCtlesc(result, byteVal);
                                    i = j;
                                }
                                else {
                                    result.push(inner[i][0]);
                                    i += 1;
                                }
                            }
                        }
                        else {
                            if (c === "u") {
                                var j = i + 2;
                                while (j < inner.length && j < i + 6 && IsHexDigit(inner[j])) {
                                    j += 1;
                                }
                                if (j > i + 2) {
                                    var codepoint = parseInt(Substring(inner, i + 2, j), 16);
                                    if (codepoint === 0) {
                                        return result;
                                    }
                                    result.push.apply(result, Array.from(new TextEncoder().encode(String.fromCodePoint(codepoint))));
                                    i = j;
                                }
                                else {
                                    result.push(inner[i][0]);
                                    i += 1;
                                }
                            }
                            else {
                                if (c === "U") {
                                    var j = i + 2;
                                    while (j < inner.length && j < i + 10 && IsHexDigit(inner[j])) {
                                        j += 1;
                                    }
                                    if (j > i + 2) {
                                        var codepoint = parseInt(Substring(inner, i + 2, j), 16);
                                        if (codepoint === 0) {
                                            return result;
                                        }
                                        result.push.apply(result, Array.from(new TextEncoder().encode(String.fromCodePoint(codepoint))));
                                        i = j;
                                    }
                                    else {
                                        result.push(inner[i][0]);
                                        i += 1;
                                    }
                                }
                                else {
                                    if (c === "c") {
                                        if (i + 3 <= inner.length) {
                                            var ctrlChar = inner[i + 2];
                                            var skipExtra = 0;
                                            if (ctrlChar === "\\" && i + 4 <= inner.length && inner[i + 3] === "\\") {
                                                skipExtra = 1;
                                            }
                                            var ctrlVal = ctrlChar[0] & 31;
                                            if (ctrlVal === 0) {
                                                return result;
                                            }
                                            this.AppendWithCtlesc(result, ctrlVal);
                                            i += 3 + skipExtra;
                                        }
                                        else {
                                            result.push(inner[i][0]);
                                            i += 1;
                                        }
                                    }
                                    else {
                                        if (c === "0") {
                                            var j = i + 2;
                                            while (j < inner.length && j < i + 4 && IsOctalDigit(inner[j])) {
                                                j += 1;
                                            }
                                            if (j > i + 2) {
                                                var byteVal = parseInt(Substring(inner, i + 1, j), 8) & 255;
                                                if (byteVal === 0) {
                                                    return result;
                                                }
                                                this.AppendWithCtlesc(result, byteVal);
                                                i = j;
                                            }
                                            else {
                                                return result;
                                            }
                                        }
                                        else {
                                            if (c >= "1" && c <= "7") {
                                                var j = i + 1;
                                                while (j < inner.length && j < i + 4 && IsOctalDigit(inner[j])) {
                                                    j += 1;
                                                }
                                                var byteVal = parseInt(Substring(inner, i + 1, j), 8) & 255;
                                                if (byteVal === 0) {
                                                    return result;
                                                }
                                                this.AppendWithCtlesc(result, byteVal);
                                                i = j;
                                            }
                                            else {
                                                result.push(92);
                                                result.push(c[0]);
                                                i += 2;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            else {
                result.push.apply(result, Array.from(new TextEncoder().encode(inner[i])));
                i += 1;
            }
        }
        return result;
    };
    Word.prototype.ExpandAnsiCEscapes = function (value) {
        if (!(value.startsWith("'") && value.endsWith("'"))) {
            return value;
        }
        var inner = Substring(value, 1, value.length - 1);
        var literalBytes = this.AnsiCToBytes(inner);
        var literalStr = new TextDecoder().decode(new Uint8Array(literalBytes));
        return this.ShSingleQuote(literalStr);
    };
    Word.prototype.ExpandAllAnsiCQuotes = function (value) {
        var result = [];
        var i = 0;
        var quote = newQuoteState();
        var inBacktick = false;
        var braceDepth = 0;
        while (i < value.length) {
            var ch = value[i];
            if (ch === "`" && !quote.single) {
                inBacktick = !inBacktick;
                result.push(ch);
                i += 1;
                continue;
            }
            if (inBacktick) {
                if (ch === "\\" && i + 1 < value.length) {
                    result.push(ch);
                    result.push(value[i + 1]);
                    i += 2;
                }
                else {
                    result.push(ch);
                    i += 1;
                }
                continue;
            }
            if (!quote.single) {
                if (IsExpansionStart(value, i, "${")) {
                    braceDepth += 1;
                    quote.push();
                    result.push("${");
                    i += 2;
                    continue;
                }
                else {
                    if (ch === "}" && braceDepth > 0 && !quote.double) {
                        braceDepth -= 1;
                        result.push(ch);
                        quote.pop();
                        i += 1;
                        continue;
                    }
                }
            }
            var effectiveInDquote = quote.double;
            if (ch === "'" && !effectiveInDquote) {
                var isAnsiC = !quote.single && i > 0 && value[i - 1] === "$" && CountConsecutiveDollarsBefore(value, i - 1) % 2 === 0;
                if (!isAnsiC) {
                    quote.single = !quote.single;
                }
                result.push(ch);
                i += 1;
            }
            else {
                if (ch === "\"" && !quote.single) {
                    quote.double = !quote.double;
                    result.push(ch);
                    i += 1;
                }
                else {
                    if (ch === "\\" && i + 1 < value.length && !quote.single) {
                        result.push(ch);
                        result.push(value[i + 1]);
                        i += 2;
                    }
                    else {
                        if (StartsWithAt(value, i, "$'") && !quote.single && !effectiveInDquote && CountConsecutiveDollarsBefore(value, i) % 2 === 0) {
                            var j = i + 2;
                            while (j < value.length) {
                                if (value[j] === "\\" && j + 1 < value.length) {
                                    j += 2;
                                }
                                else {
                                    if (value[j] === "'") {
                                        j += 1;
                                        break;
                                    }
                                    else {
                                        j += 1;
                                    }
                                }
                            }
                            var ansiStr = Substring(value, i, j);
                            var expanded = this.ExpandAnsiCEscapes(Substring(ansiStr, 1, ansiStr.length));
                            var outerInDquote = quote.outerDouble();
                            if (braceDepth > 0 && outerInDquote && expanded.startsWith("'") && expanded.endsWith("'")) {
                                var inner = Substring(expanded, 1, expanded.length - 1);
                                if (inner.indexOf("") === -1) {
                                    var resultStr = result.join("");
                                    var inPattern = false;
                                    var lastBraceIdx = resultStr.lastIndexOf("${");
                                    if (lastBraceIdx >= 0) {
                                        var afterBrace = resultStr.slice(lastBraceIdx + 2);
                                        var varNameLen = 0;
                                        if (afterBrace !== "") {
                                            if ("@*#?-$!0123456789_".includes(afterBrace[0])) {
                                                varNameLen = 1;
                                            }
                                            else {
                                                if (/^[a-zA-Z]$/.test(afterBrace[0]) || afterBrace[0] === "_") {
                                                    while (varNameLen < afterBrace.length) {
                                                        var c = afterBrace[varNameLen];
                                                        if (!(/^[a-zA-Z0-9]$/.test(c) || c === "_")) {
                                                            break;
                                                        }
                                                        varNameLen += 1;
                                                    }
                                                }
                                            }
                                        }
                                        if (varNameLen > 0 && varNameLen < afterBrace.length && !"#?-".includes(afterBrace[0])) {
                                            var opStart = afterBrace.slice(varNameLen);
                                            if (opStart.startsWith("@") && opStart.length > 1) {
                                                opStart = opStart.slice(1);
                                            }
                                            for (var _i = 0, _a = ["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"]; _i < _a.length; _i++) {
                                                var op = _a[_i];
                                                if (opStart.startsWith(op)) {
                                                    inPattern = true;
                                                    break;
                                                }
                                            }
                                            if (!inPattern && opStart !== "" && !"%#/^,~:+-=?".includes(opStart[0])) {
                                                for (var _b = 0, _c = ["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"]; _b < _c.length; _b++) {
                                                    var op = _c[_b];
                                                    if (opStart.includes(op)) {
                                                        inPattern = true;
                                                        break;
                                                    }
                                                }
                                            }
                                        }
                                        else {
                                            if (varNameLen === 0 && afterBrace.length > 1) {
                                                var firstChar = afterBrace[0];
                                                if (!"%#/^,".includes(firstChar)) {
                                                    var rest = afterBrace.slice(1);
                                                    for (var _d = 0, _f = ["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"]; _d < _f.length; _d++) {
                                                        var op = _f[_d];
                                                        if (rest.includes(op)) {
                                                            inPattern = true;
                                                            break;
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                    if (!inPattern) {
                                        expanded = inner;
                                    }
                                }
                            }
                            result.push(expanded);
                            i = j;
                        }
                        else {
                            result.push(ch);
                            i += 1;
                        }
                    }
                }
            }
        }
        return result.join("");
    };
    Word.prototype.StripLocaleStringDollars = function (value) {
        var result = [];
        var i = 0;
        var braceDepth = 0;
        var bracketDepth = 0;
        var quote = newQuoteState();
        var braceQuote = newQuoteState();
        var bracketInDoubleQuote = false;
        while (i < value.length) {
            var ch = value[i];
            if (ch === "\\" && i + 1 < value.length && !quote.single && !braceQuote.single) {
                result.push(ch);
                result.push(value[i + 1]);
                i += 2;
            }
            else {
                if (StartsWithAt(value, i, "${") && !quote.single && !braceQuote.single && (i === 0 || value[i - 1] !== "$")) {
                    braceDepth += 1;
                    braceQuote.double = false;
                    braceQuote.single = false;
                    result.push("$");
                    result.push("{");
                    i += 2;
                }
                else {
                    if (ch === "}" && braceDepth > 0 && !quote.single && !braceQuote.double && !braceQuote.single) {
                        braceDepth -= 1;
                        result.push(ch);
                        i += 1;
                    }
                    else {
                        if (ch === "[" && braceDepth > 0 && !quote.single && !braceQuote.double) {
                            bracketDepth += 1;
                            bracketInDoubleQuote = false;
                            result.push(ch);
                            i += 1;
                        }
                        else {
                            if (ch === "]" && bracketDepth > 0 && !quote.single && !bracketInDoubleQuote) {
                                bracketDepth -= 1;
                                result.push(ch);
                                i += 1;
                            }
                            else {
                                if (ch === "'" && !quote.double && braceDepth === 0) {
                                    quote.single = !quote.single;
                                    result.push(ch);
                                    i += 1;
                                }
                                else {
                                    if (ch === "\"" && !quote.single && braceDepth === 0) {
                                        quote.double = !quote.double;
                                        result.push(ch);
                                        i += 1;
                                    }
                                    else {
                                        if (ch === "\"" && !quote.single && bracketDepth > 0) {
                                            bracketInDoubleQuote = !bracketInDoubleQuote;
                                            result.push(ch);
                                            i += 1;
                                        }
                                        else {
                                            if (ch === "\"" && !quote.single && !braceQuote.single && braceDepth > 0) {
                                                braceQuote.double = !braceQuote.double;
                                                result.push(ch);
                                                i += 1;
                                            }
                                            else {
                                                if (ch === "'" && !quote.double && !braceQuote.double && braceDepth > 0) {
                                                    braceQuote.single = !braceQuote.single;
                                                    result.push(ch);
                                                    i += 1;
                                                }
                                                else {
                                                    if (StartsWithAt(value, i, "$\"") && !quote.single && !braceQuote.single && (braceDepth > 0 || bracketDepth > 0 || !quote.double) && !braceQuote.double && !bracketInDoubleQuote) {
                                                        var dollarCount = 1 + CountConsecutiveDollarsBefore(value, i);
                                                        if (dollarCount % 2 === 1) {
                                                            result.push("\"");
                                                            if (bracketDepth > 0) {
                                                                bracketInDoubleQuote = true;
                                                            }
                                                            else {
                                                                if (braceDepth > 0) {
                                                                    braceQuote.double = true;
                                                                }
                                                                else {
                                                                    quote.double = true;
                                                                }
                                                            }
                                                            i += 2;
                                                        }
                                                        else {
                                                            result.push(ch);
                                                            i += 1;
                                                        }
                                                    }
                                                    else {
                                                        result.push(ch);
                                                        i += 1;
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        return result.join("");
    };
    Word.prototype.NormalizeArrayWhitespace = function (value) {
        var i = 0;
        if (!(i < value.length && (/^[a-zA-Z]$/.test(value[i]) || value[i] === "_"))) {
            return value;
        }
        i += 1;
        while (i < value.length && (/^[a-zA-Z0-9]$/.test(value[i]) || value[i] === "_")) {
            i += 1;
        }
        while (i < value.length && value[i] === "[") {
            var depth = 1;
            i += 1;
            while (i < value.length && depth > 0) {
                if (value[i] === "[") {
                    depth += 1;
                }
                else {
                    if (value[i] === "]") {
                        depth -= 1;
                    }
                }
                i += 1;
            }
            if (depth !== 0) {
                return value;
            }
        }
        if (i < value.length && value[i] === "+") {
            i += 1;
        }
        if (!(i + 1 < value.length && value[i] === "=" && value[i + 1] === "(")) {
            return value;
        }
        var prefix = Substring(value, 0, i + 1);
        var openParenPos = i + 1;
        if (value.endsWith(")")) {
            var closeParenPos = value.length - 1;
        }
        else {
            var closeParenPos = this.FindMatchingParen(value, openParenPos);
            if (closeParenPos < 0) {
                return value;
            }
        }
        var inner = Substring(value, openParenPos + 1, closeParenPos);
        var suffix = Substring(value, closeParenPos + 1, value.length);
        var result = this.NormalizeArrayInner(inner);
        return prefix + "(" + result + ")" + suffix;
    };
    Word.prototype.FindMatchingParen = function (value, openPos) {
        if (openPos >= value.length || value[openPos] !== "(") {
            return -1;
        }
        var i = openPos + 1;
        var depth = 1;
        var quote = newQuoteState();
        while (i < value.length && depth > 0) {
            var ch = value[i];
            if (ch === "\\" && i + 1 < value.length && !quote.single) {
                i += 2;
                continue;
            }
            if (ch === "'" && !quote.double) {
                quote.single = !quote.single;
                i += 1;
                continue;
            }
            if (ch === "\"" && !quote.single) {
                quote.double = !quote.double;
                i += 1;
                continue;
            }
            if (quote.single || quote.double) {
                i += 1;
                continue;
            }
            if (ch === "#") {
                while (i < value.length && value[i] !== "\n") {
                    i += 1;
                }
                continue;
            }
            if (ch === "(") {
                depth += 1;
            }
            else {
                if (ch === ")") {
                    depth -= 1;
                    if (depth === 0) {
                        return i;
                    }
                }
            }
            i += 1;
        }
        return -1;
    };
    Word.prototype.NormalizeArrayInner = function (inner) {
        var normalized = [];
        var i = 0;
        var inWhitespace = true;
        var braceDepth = 0;
        var bracketDepth = 0;
        while (i < inner.length) {
            var ch = inner[i];
            if (IsWhitespace(ch)) {
                if (!inWhitespace && normalized.length > 0 && braceDepth === 0 && bracketDepth === 0) {
                    normalized.push(" ");
                    inWhitespace = true;
                }
                if (braceDepth > 0 || bracketDepth > 0) {
                    normalized.push(ch);
                }
                i += 1;
            }
            else {
                if (ch === "'") {
                    inWhitespace = false;
                    var j = i + 1;
                    while (j < inner.length && inner[j] !== "'") {
                        j += 1;
                    }
                    normalized.push(Substring(inner, i, j + 1));
                    i = j + 1;
                }
                else {
                    if (ch === "\"") {
                        inWhitespace = false;
                        var j = i + 1;
                        var dqContent = ["\""];
                        var dqBraceDepth = 0;
                        while (j < inner.length) {
                            if (inner[j] === "\\" && j + 1 < inner.length) {
                                if (inner[j + 1] === "\n") {
                                    j += 2;
                                }
                                else {
                                    dqContent.push(inner[j]);
                                    dqContent.push(inner[j + 1]);
                                    j += 2;
                                }
                            }
                            else {
                                if (IsExpansionStart(inner, j, "${")) {
                                    dqContent.push("${");
                                    dqBraceDepth += 1;
                                    j += 2;
                                }
                                else {
                                    if (inner[j] === "}" && dqBraceDepth > 0) {
                                        dqContent.push("}");
                                        dqBraceDepth -= 1;
                                        j += 1;
                                    }
                                    else {
                                        if (inner[j] === "\"" && dqBraceDepth === 0) {
                                            dqContent.push("\"");
                                            j += 1;
                                            break;
                                        }
                                        else {
                                            dqContent.push(inner[j]);
                                            j += 1;
                                        }
                                    }
                                }
                            }
                        }
                        normalized.push(dqContent.join(""));
                        i = j;
                    }
                    else {
                        if (ch === "\\" && i + 1 < inner.length) {
                            if (inner[i + 1] === "\n") {
                                i += 2;
                            }
                            else {
                                inWhitespace = false;
                                normalized.push(Substring(inner, i, i + 2));
                                i += 2;
                            }
                        }
                        else {
                            if (IsExpansionStart(inner, i, "$((")) {
                                inWhitespace = false;
                                var j = i + 3;
                                var depth = 1;
                                while (j < inner.length && depth > 0) {
                                    if (j + 1 < inner.length && inner[j] === "(" && inner[j + 1] === "(") {
                                        depth += 1;
                                        j += 2;
                                    }
                                    else {
                                        if (j + 1 < inner.length && inner[j] === ")" && inner[j + 1] === ")") {
                                            depth -= 1;
                                            j += 2;
                                        }
                                        else {
                                            j += 1;
                                        }
                                    }
                                }
                                normalized.push(Substring(inner, i, j));
                                i = j;
                            }
                            else {
                                if (IsExpansionStart(inner, i, "$(")) {
                                    inWhitespace = false;
                                    var j = i + 2;
                                    var depth = 1;
                                    while (j < inner.length && depth > 0) {
                                        if (inner[j] === "(" && j > 0 && inner[j - 1] === "$") {
                                            depth += 1;
                                        }
                                        else {
                                            if (inner[j] === ")") {
                                                depth -= 1;
                                            }
                                            else {
                                                if (inner[j] === "'") {
                                                    j += 1;
                                                    while (j < inner.length && inner[j] !== "'") {
                                                        j += 1;
                                                    }
                                                }
                                                else {
                                                    if (inner[j] === "\"") {
                                                        j += 1;
                                                        while (j < inner.length) {
                                                            if (inner[j] === "\\" && j + 1 < inner.length) {
                                                                j += 2;
                                                                continue;
                                                            }
                                                            if (inner[j] === "\"") {
                                                                break;
                                                            }
                                                            j += 1;
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                        j += 1;
                                    }
                                    normalized.push(Substring(inner, i, j));
                                    i = j;
                                }
                                else {
                                    if ((ch === "<" || ch === ">") && i + 1 < inner.length && inner[i + 1] === "(") {
                                        inWhitespace = false;
                                        var j = i + 2;
                                        var depth = 1;
                                        while (j < inner.length && depth > 0) {
                                            if (inner[j] === "(") {
                                                depth += 1;
                                            }
                                            else {
                                                if (inner[j] === ")") {
                                                    depth -= 1;
                                                }
                                                else {
                                                    if (inner[j] === "'") {
                                                        j += 1;
                                                        while (j < inner.length && inner[j] !== "'") {
                                                            j += 1;
                                                        }
                                                    }
                                                    else {
                                                        if (inner[j] === "\"") {
                                                            j += 1;
                                                            while (j < inner.length) {
                                                                if (inner[j] === "\\" && j + 1 < inner.length) {
                                                                    j += 2;
                                                                    continue;
                                                                }
                                                                if (inner[j] === "\"") {
                                                                    break;
                                                                }
                                                                j += 1;
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                            j += 1;
                                        }
                                        normalized.push(Substring(inner, i, j));
                                        i = j;
                                    }
                                    else {
                                        if (IsExpansionStart(inner, i, "${")) {
                                            inWhitespace = false;
                                            normalized.push("${");
                                            braceDepth += 1;
                                            i += 2;
                                        }
                                        else {
                                            if (ch === "{" && braceDepth > 0) {
                                                normalized.push(ch);
                                                braceDepth += 1;
                                                i += 1;
                                            }
                                            else {
                                                if (ch === "}" && braceDepth > 0) {
                                                    normalized.push(ch);
                                                    braceDepth -= 1;
                                                    i += 1;
                                                }
                                                else {
                                                    if (ch === "#" && braceDepth === 0 && inWhitespace) {
                                                        while (i < inner.length && inner[i] !== "\n") {
                                                            i += 1;
                                                        }
                                                    }
                                                    else {
                                                        if (ch === "[") {
                                                            if (inWhitespace || bracketDepth > 0) {
                                                                bracketDepth += 1;
                                                            }
                                                            inWhitespace = false;
                                                            normalized.push(ch);
                                                            i += 1;
                                                        }
                                                        else {
                                                            if (ch === "]" && bracketDepth > 0) {
                                                                normalized.push(ch);
                                                                bracketDepth -= 1;
                                                                i += 1;
                                                            }
                                                            else {
                                                                inWhitespace = false;
                                                                normalized.push(ch);
                                                                i += 1;
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        return normalized.join("").trimEnd();
    };
    Word.prototype.StripArithLineContinuations = function (value) {
        var result = [];
        var i = 0;
        while (i < value.length) {
            if (IsExpansionStart(value, i, "$((")) {
                var start = i;
                i += 3;
                var depth = 2;
                var arithContent = [];
                var firstCloseIdx = -1;
                while (i < value.length && depth > 0) {
                    if (value[i] === "(") {
                        arithContent.push("(");
                        depth += 1;
                        i += 1;
                        if (depth > 1) {
                            firstCloseIdx = -1;
                        }
                    }
                    else {
                        if (value[i] === ")") {
                            if (depth === 2) {
                                firstCloseIdx = arithContent.length;
                            }
                            depth -= 1;
                            if (depth > 0) {
                                arithContent.push(")");
                            }
                            i += 1;
                        }
                        else {
                            if (value[i] === "\\" && i + 1 < value.length && value[i + 1] === "\n") {
                                var numBackslashes = 0;
                                var j = arithContent.length - 1;
                                while (j >= 0 && arithContent[j] === "\n") {
                                    j -= 1;
                                }
                                while (j >= 0 && arithContent[j] === "\\") {
                                    numBackslashes += 1;
                                    j -= 1;
                                }
                                if (numBackslashes % 2 === 1) {
                                    arithContent.push("\\");
                                    arithContent.push("\n");
                                    i += 2;
                                }
                                else {
                                    i += 2;
                                }
                                if (depth === 1) {
                                    firstCloseIdx = -1;
                                }
                            }
                            else {
                                arithContent.push(value[i]);
                                i += 1;
                                if (depth === 1) {
                                    firstCloseIdx = -1;
                                }
                            }
                        }
                    }
                }
                if (depth === 0 || depth === 1 && firstCloseIdx !== -1) {
                    var content = arithContent.join("");
                    if (firstCloseIdx !== -1) {
                        content = content.slice(0, firstCloseIdx);
                        var closing = depth === 0 ? "))" : ")";
                        result.push("$((" + content + closing);
                    }
                    else {
                        result.push("$((" + content + ")");
                    }
                }
                else {
                    result.push(Substring(value, start, i));
                }
            }
            else {
                result.push(value[i]);
                i += 1;
            }
        }
        return result.join("");
    };
    Word.prototype.CollectCmdsubs = function (node) {
        var result = [];
        if (node instanceof CommandSubstitution) {
            result.push(node);
        }
        else if (node instanceof ArrayName) {
            for (var _i = 0, _a = node.elements; _i < _a.length; _i++) {
                var elem = _a[_i];
                for (var _b = 0, _c = elem.parts; _b < _c.length; _b++) {
                    var p = _c[_b];
                    if (p instanceof CommandSubstitution) {
                        result.push(p);
                    }
                    else {
                        result.push.apply(result, this.CollectCmdsubs(p));
                    }
                }
            }
        }
        else if (node instanceof ArithmeticExpansion) {
            if (node.expression !== null) {
                result.push.apply(result, this.CollectCmdsubs(node.expression));
            }
        }
        else if (node instanceof ArithBinaryOp) {
            result.push.apply(result, this.CollectCmdsubs(node.left));
            result.push.apply(result, this.CollectCmdsubs(node.right));
        }
        else if (node instanceof ArithComma) {
            result.push.apply(result, this.CollectCmdsubs(node.left));
            result.push.apply(result, this.CollectCmdsubs(node.right));
        }
        else if (node instanceof ArithUnaryOp) {
            result.push.apply(result, this.CollectCmdsubs(node.operand));
        }
        else if (node instanceof ArithPreIncr) {
            result.push.apply(result, this.CollectCmdsubs(node.operand));
        }
        else if (node instanceof ArithPostIncr) {
            result.push.apply(result, this.CollectCmdsubs(node.operand));
        }
        else if (node instanceof ArithPreDecr) {
            result.push.apply(result, this.CollectCmdsubs(node.operand));
        }
        else if (node instanceof ArithPostDecr) {
            result.push.apply(result, this.CollectCmdsubs(node.operand));
        }
        else if (node instanceof ArithTernary) {
            result.push.apply(result, this.CollectCmdsubs(node.condition));
            result.push.apply(result, this.CollectCmdsubs(node.ifTrue));
            result.push.apply(result, this.CollectCmdsubs(node.ifFalse));
        }
        else if (node instanceof ArithAssign) {
            result.push.apply(result, this.CollectCmdsubs(node.target));
            result.push.apply(result, this.CollectCmdsubs(node.value));
        }
        return result;
    };
    Word.prototype.CollectProcsubs = function (node) {
        var result = [];
        if (node instanceof ProcessSubstitution) {
            result.push(node);
        }
        else if (node instanceof ArrayName) {
            for (var _i = 0, _a = node.elements; _i < _a.length; _i++) {
                var elem = _a[_i];
                for (var _b = 0, _c = elem.parts; _b < _c.length; _b++) {
                    var p = _c[_b];
                    if (p instanceof ProcessSubstitution) {
                        result.push(p);
                    }
                    else {
                        result.push.apply(result, this.CollectProcsubs(p));
                    }
                }
            }
        }
        return result;
    };
    Word.prototype.FormatCommandSubstitutions = function (value, inArith) {
        var cmdsubParts = [];
        var procsubParts = [];
        var hasArith = false;
        for (var _i = 0, _a = this.parts; _i < _a.length; _i++) {
            var p = _a[_i];
            if (p instanceof CommandSubstitution) {
                cmdsubParts.push(p);
            }
            else if (p instanceof ProcessSubstitution) {
                procsubParts.push(p);
            }
            else if (p instanceof ArithmeticExpansion) {
                hasArith = true;
            }
            else {
                cmdsubParts.push.apply(cmdsubParts, this.CollectCmdsubs(p));
                procsubParts.push.apply(procsubParts, this.CollectProcsubs(p));
            }
        }
        var hasBraceCmdsub = value.indexOf("${ ") !== -1 || value.indexOf("${\t") !== -1 || value.indexOf("${\n") !== -1 || value.indexOf("${|") !== -1;
        var hasUntrackedCmdsub = false;
        var hasUntrackedProcsub = false;
        var idx = 0;
        var scanQuote = newQuoteState();
        while (idx < value.length) {
            if (value[idx] === "\"") {
                scanQuote.double = !scanQuote.double;
                idx += 1;
            }
            else {
                if (value[idx] === "'" && !scanQuote.double) {
                    idx += 1;
                    while (idx < value.length && value[idx] !== "'") {
                        idx += 1;
                    }
                    if (idx < value.length) {
                        idx += 1;
                    }
                }
                else {
                    if (StartsWithAt(value, idx, "$(") && !StartsWithAt(value, idx, "$((") && !IsBackslashEscaped(value, idx) && !IsDollarDollarParen(value, idx)) {
                        hasUntrackedCmdsub = true;
                        break;
                    }
                    else {
                        if ((StartsWithAt(value, idx, "<(") || StartsWithAt(value, idx, ">(")) && !scanQuote.double) {
                            if (idx === 0 || !/^[a-zA-Z0-9]$/.test(value[idx - 1]) && !"\"'".includes(value[idx - 1])) {
                                hasUntrackedProcsub = true;
                                break;
                            }
                            idx += 1;
                        }
                        else {
                            idx += 1;
                        }
                    }
                }
            }
        }
        var hasParamWithProcsubPattern = value.includes("${") && (value.includes("<(") || value.includes(">("));
        if (!(cmdsubParts.length > 0) && !(procsubParts.length > 0) && !hasBraceCmdsub && !hasUntrackedCmdsub && !hasUntrackedProcsub && !hasParamWithProcsubPattern) {
            return value;
        }
        var result = [];
        var i = 0;
        var cmdsubIdx = 0;
        var procsubIdx = 0;
        var mainQuote = newQuoteState();
        var extglobDepth = 0;
        var deprecatedArithDepth = 0;
        var arithDepth = 0;
        var arithParenDepth = 0;
        while (i < value.length) {
            if (i > 0 && IsExtglobPrefix(value[i - 1]) && value[i] === "(" && !IsBackslashEscaped(value, i - 1)) {
                extglobDepth += 1;
                result.push(value[i]);
                i += 1;
                continue;
            }
            if (value[i] === ")" && extglobDepth > 0) {
                extglobDepth -= 1;
                result.push(value[i]);
                i += 1;
                continue;
            }
            if (StartsWithAt(value, i, "$[") && !IsBackslashEscaped(value, i)) {
                deprecatedArithDepth += 1;
                result.push(value[i]);
                i += 1;
                continue;
            }
            if (value[i] === "]" && deprecatedArithDepth > 0) {
                deprecatedArithDepth -= 1;
                result.push(value[i]);
                i += 1;
                continue;
            }
            if (IsExpansionStart(value, i, "$((") && !IsBackslashEscaped(value, i) && hasArith) {
                arithDepth += 1;
                arithParenDepth += 2;
                result.push("$((");
                i += 3;
                continue;
            }
            if (arithDepth > 0 && arithParenDepth === 2 && StartsWithAt(value, i, "))")) {
                arithDepth -= 1;
                arithParenDepth -= 2;
                result.push("))");
                i += 2;
                continue;
            }
            if (arithDepth > 0) {
                if (value[i] === "(") {
                    arithParenDepth += 1;
                    result.push(value[i]);
                    i += 1;
                    continue;
                }
                else {
                    if (value[i] === ")") {
                        arithParenDepth -= 1;
                        result.push(value[i]);
                        i += 1;
                        continue;
                    }
                }
            }
            if (IsExpansionStart(value, i, "$((") && !hasArith) {
                var j = FindCmdsubEnd(value, i + 2);
                result.push(Substring(value, i, j));
                if (cmdsubIdx < cmdsubParts.length) {
                    cmdsubIdx += 1;
                }
                i = j;
                continue;
            }
            if (StartsWithAt(value, i, "$(") && !StartsWithAt(value, i, "$((") && !IsBackslashEscaped(value, i) && !IsDollarDollarParen(value, i)) {
                var j = FindCmdsubEnd(value, i + 2);
                if (extglobDepth > 0) {
                    result.push(Substring(value, i, j));
                    if (cmdsubIdx < cmdsubParts.length) {
                        cmdsubIdx += 1;
                    }
                    i = j;
                    continue;
                }
                var inner = Substring(value, i + 2, j - 1);
                if (cmdsubIdx < cmdsubParts.length) {
                    var node = cmdsubParts[cmdsubIdx];
                    var formatted = FormatCmdsubNode(node.command, 0, false, false, false);
                    cmdsubIdx += 1;
                }
                else {
                    try {
                        var parser = newParser(inner, false, false);
                        var parsed = parser.parseList(true);
                        var formatted = parsed !== null ? FormatCmdsubNode(parsed, 0, false, false, false) : "";
                    }
                    catch (_e) {
                        var formatted = inner;
                    }
                }
                if (formatted.startsWith("(")) {
                    result.push("$( " + formatted + ")");
                }
                else {
                    result.push("$(" + formatted + ")");
                }
                i = j;
            }
            else {
                if (value[i] === "`" && cmdsubIdx < cmdsubParts.length) {
                    var j = i + 1;
                    while (j < value.length) {
                        if (value[j] === "\\" && j + 1 < value.length) {
                            j += 2;
                            continue;
                        }
                        if (value[j] === "`") {
                            j += 1;
                            break;
                        }
                        j += 1;
                    }
                    result.push(Substring(value, i, j));
                    cmdsubIdx += 1;
                    i = j;
                }
                else {
                    if (IsExpansionStart(value, i, "${") && i + 2 < value.length && IsFunsubChar(value[i + 2]) && !IsBackslashEscaped(value, i)) {
                        var j = FindFunsubEnd(value, i + 2);
                        var cmdsubNode = cmdsubIdx < cmdsubParts.length ? cmdsubParts[cmdsubIdx] : null;
                        if (cmdsubNode instanceof CommandSubstitution && cmdsubNode.brace) {
                            var node = cmdsubNode;
                            var formatted = FormatCmdsubNode(node.command, 0, false, false, false);
                            var hasPipe = value[i + 2] === "|";
                            var prefix = hasPipe ? "${|" : "${ ";
                            var origInner = Substring(value, i + 2, j - 1);
                            var endsWithNewline = origInner.endsWith("\n");
                            if (!(formatted !== "") || /^\s$/.test(formatted)) {
                                var suffix = "}";
                            }
                            else {
                                if (formatted.endsWith("&") || formatted.endsWith("& ")) {
                                    var suffix = formatted.endsWith("&") ? " }" : "}";
                                }
                                else {
                                    if (endsWithNewline) {
                                        var suffix = "\n }";
                                    }
                                    else {
                                        var suffix = "; }";
                                    }
                                }
                            }
                            result.push(prefix + formatted + suffix);
                            cmdsubIdx += 1;
                        }
                        else {
                            result.push(Substring(value, i, j));
                        }
                        i = j;
                    }
                    else {
                        if ((StartsWithAt(value, i, ">(") || StartsWithAt(value, i, "<(")) && !mainQuote.double && deprecatedArithDepth === 0 && arithDepth === 0) {
                            var isProcsub = i === 0 || !/^[a-zA-Z0-9]$/.test(value[i - 1]) && !"\"'".includes(value[i - 1]);
                            if (extglobDepth > 0) {
                                var j = FindCmdsubEnd(value, i + 2);
                                result.push(Substring(value, i, j));
                                if (procsubIdx < procsubParts.length) {
                                    procsubIdx += 1;
                                }
                                i = j;
                                continue;
                            }
                            if (procsubIdx < procsubParts.length) {
                                var direction = value[i];
                                var j = FindCmdsubEnd(value, i + 2);
                                var node = procsubParts[procsubIdx];
                                var compact = StartsWithSubshell(node.command);
                                var formatted = FormatCmdsubNode(node.command, 0, true, compact, true);
                                var rawContent = Substring(value, i + 2, j - 1);
                                if (node.command.kind === "subshell") {
                                    var leadingWsEnd = 0;
                                    while (leadingWsEnd < rawContent.length && " \t\n".includes(rawContent[leadingWsEnd])) {
                                        leadingWsEnd += 1;
                                    }
                                    var leadingWs = rawContent.slice(0, leadingWsEnd);
                                    var stripped = rawContent.slice(leadingWsEnd);
                                    if (stripped.startsWith("(")) {
                                        if (leadingWs !== "") {
                                            var normalizedWs = leadingWs.replace(/\n/g, " ").replace(/\t/g, " ");
                                            var spaced = FormatCmdsubNode(node.command, 0, false, false, false);
                                            result.push(direction + "(" + normalizedWs + spaced + ")");
                                        }
                                        else {
                                            rawContent = rawContent.replace(/\\\n/g, "");
                                            result.push(direction + "(" + rawContent + ")");
                                        }
                                        procsubIdx += 1;
                                        i = j;
                                        continue;
                                    }
                                }
                                rawContent = Substring(value, i + 2, j - 1);
                                var rawStripped = rawContent.replace(/\\\n/g, "");
                                if (StartsWithSubshell(node.command) && formatted !== rawStripped) {
                                    result.push(direction + "(" + rawStripped + ")");
                                }
                                else {
                                    var finalOutput = direction + "(" + formatted + ")";
                                    result.push(finalOutput);
                                }
                                procsubIdx += 1;
                                i = j;
                            }
                            else {
                                if (isProcsub && this.parts.length !== 0) {
                                    var direction = value[i];
                                    var j = FindCmdsubEnd(value, i + 2);
                                    if (j > value.length || j > 0 && j <= value.length && value[j - 1] !== ")") {
                                        result.push(value[i]);
                                        i += 1;
                                        continue;
                                    }
                                    var inner = Substring(value, i + 2, j - 1);
                                    try {
                                        var parser = newParser(inner, false, false);
                                        var parsed = parser.parseList(true);
                                        if (parsed !== null && parser.pos === inner.length && !inner.includes("\n")) {
                                            var compact = StartsWithSubshell(parsed);
                                            var formatted = FormatCmdsubNode(parsed, 0, true, compact, true);
                                        }
                                        else {
                                            var formatted = inner;
                                        }
                                    }
                                    catch (_e) {
                                        var formatted = inner;
                                    }
                                    result.push(direction + "(" + formatted + ")");
                                    i = j;
                                }
                                else {
                                    if (isProcsub) {
                                        var direction = value[i];
                                        var j = FindCmdsubEnd(value, i + 2);
                                        if (j > value.length || j > 0 && j <= value.length && value[j - 1] !== ")") {
                                            result.push(value[i]);
                                            i += 1;
                                            continue;
                                        }
                                        var inner = Substring(value, i + 2, j - 1);
                                        if (inArith) {
                                            result.push(direction + "(" + inner + ")");
                                        }
                                        else {
                                            if (inner.trim() !== "") {
                                                var stripped = inner.replace(/^[ \t]+/, '');
                                                result.push(direction + "(" + stripped + ")");
                                            }
                                            else {
                                                result.push(direction + "(" + inner + ")");
                                            }
                                        }
                                        i = j;
                                    }
                                    else {
                                        result.push(value[i]);
                                        i += 1;
                                    }
                                }
                            }
                        }
                        else {
                            if ((IsExpansionStart(value, i, "${ ") || IsExpansionStart(value, i, "${\t") || IsExpansionStart(value, i, "${\n") || IsExpansionStart(value, i, "${|")) && !IsBackslashEscaped(value, i)) {
                                var prefix = Substring(value, i, i + 3).replace(/\t/g, " ").replace(/\n/g, " ");
                                var j = i + 3;
                                var depth = 1;
                                while (j < value.length && depth > 0) {
                                    if (value[j] === "{") {
                                        depth += 1;
                                    }
                                    else {
                                        if (value[j] === "}") {
                                            depth -= 1;
                                        }
                                    }
                                    j += 1;
                                }
                                var inner = Substring(value, i + 2, j - 1);
                                if (inner.trim() === "") {
                                    result.push("${ }");
                                }
                                else {
                                    try {
                                        var parser = newParser(inner.replace(/^[ \t\n|]+/, ''), false, false);
                                        var parsed = parser.parseList(true);
                                        if (parsed !== null) {
                                            var formatted = FormatCmdsubNode(parsed, 0, false, false, false);
                                            formatted = formatted.replace(/[;]+$/, '');
                                            if (inner.replace(/[ \t]+$/, '').endsWith("\n")) {
                                                var terminator = "\n }";
                                            }
                                            else {
                                                if (formatted.endsWith(" &")) {
                                                    var terminator = " }";
                                                }
                                                else {
                                                    var terminator = "; }";
                                                }
                                            }
                                            result.push(prefix + formatted + terminator);
                                        }
                                        else {
                                            result.push("${ }");
                                        }
                                    }
                                    catch (_e) {
                                        result.push(Substring(value, i, j));
                                    }
                                }
                                i = j;
                            }
                            else {
                                if (IsExpansionStart(value, i, "${") && !IsBackslashEscaped(value, i)) {
                                    var j = i + 2;
                                    var depth = 1;
                                    var braceQuote = newQuoteState();
                                    while (j < value.length && depth > 0) {
                                        var c = value[j];
                                        if (c === "\\" && j + 1 < value.length && !braceQuote.single) {
                                            j += 2;
                                            continue;
                                        }
                                        if (c === "'" && !braceQuote.double) {
                                            braceQuote.single = !braceQuote.single;
                                        }
                                        else {
                                            if (c === "\"" && !braceQuote.single) {
                                                braceQuote.double = !braceQuote.double;
                                            }
                                            else {
                                                if (!braceQuote.inQuotes()) {
                                                    if (IsExpansionStart(value, j, "$(") && !StartsWithAt(value, j, "$((")) {
                                                        j = FindCmdsubEnd(value, j + 2);
                                                        continue;
                                                    }
                                                    if (c === "{") {
                                                        depth += 1;
                                                    }
                                                    else {
                                                        if (c === "}") {
                                                            depth -= 1;
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                        j += 1;
                                    }
                                    if (depth > 0) {
                                        var inner = Substring(value, i + 2, j);
                                    }
                                    else {
                                        var inner = Substring(value, i + 2, j - 1);
                                    }
                                    var formattedInner = this.FormatCommandSubstitutions(inner, false);
                                    formattedInner = this.NormalizeExtglobWhitespace(formattedInner);
                                    if (depth === 0) {
                                        result.push("${" + formattedInner + "}");
                                    }
                                    else {
                                        result.push("${" + formattedInner);
                                    }
                                    i = j;
                                }
                                else {
                                    if (value[i] === "\"") {
                                        mainQuote.double = !mainQuote.double;
                                        result.push(value[i]);
                                        i += 1;
                                    }
                                    else {
                                        if (value[i] === "'" && !mainQuote.double) {
                                            var j = i + 1;
                                            while (j < value.length && value[j] !== "'") {
                                                j += 1;
                                            }
                                            if (j < value.length) {
                                                j += 1;
                                            }
                                            result.push(Substring(value, i, j));
                                            i = j;
                                        }
                                        else {
                                            result.push(value[i]);
                                            i += 1;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        return result.join("");
    };
    Word.prototype.NormalizeExtglobWhitespace = function (value) {
        var result = [];
        var i = 0;
        var extglobQuote = newQuoteState();
        var deprecatedArithDepth = 0;
        while (i < value.length) {
            if (value[i] === "\"") {
                extglobQuote.double = !extglobQuote.double;
                result.push(value[i]);
                i += 1;
                continue;
            }
            if (StartsWithAt(value, i, "$[") && !IsBackslashEscaped(value, i)) {
                deprecatedArithDepth += 1;
                result.push(value[i]);
                i += 1;
                continue;
            }
            if (value[i] === "]" && deprecatedArithDepth > 0) {
                deprecatedArithDepth -= 1;
                result.push(value[i]);
                i += 1;
                continue;
            }
            if (i + 1 < value.length && value[i + 1] === "(") {
                var prefixChar = value[i];
                if ("><".includes(prefixChar) && !extglobQuote.double && deprecatedArithDepth === 0) {
                    result.push(prefixChar);
                    result.push("(");
                    i += 2;
                    var depth = 1;
                    var patternParts = [];
                    var currentPart = [];
                    var hasPipe = false;
                    while (i < value.length && depth > 0) {
                        if (value[i] === "\\" && i + 1 < value.length) {
                            currentPart.push(value.slice(i, i + 2));
                            i += 2;
                            continue;
                        }
                        else {
                            if (value[i] === "(") {
                                depth += 1;
                                currentPart.push(value[i]);
                                i += 1;
                            }
                            else {
                                if (value[i] === ")") {
                                    depth -= 1;
                                    if (depth === 0) {
                                        var partContent = currentPart.join("");
                                        if (partContent.includes("<<")) {
                                            patternParts.push(partContent);
                                        }
                                        else {
                                            if (hasPipe) {
                                                patternParts.push(partContent.trim());
                                            }
                                            else {
                                                patternParts.push(partContent);
                                            }
                                        }
                                        break;
                                    }
                                    currentPart.push(value[i]);
                                    i += 1;
                                }
                                else {
                                    if (value[i] === "|" && depth === 1) {
                                        if (i + 1 < value.length && value[i + 1] === "|") {
                                            currentPart.push("||");
                                            i += 2;
                                        }
                                        else {
                                            hasPipe = true;
                                            var partContent = currentPart.join("");
                                            if (partContent.includes("<<")) {
                                                patternParts.push(partContent);
                                            }
                                            else {
                                                patternParts.push(partContent.trim());
                                            }
                                            currentPart = [];
                                            i += 1;
                                        }
                                    }
                                    else {
                                        currentPart.push(value[i]);
                                        i += 1;
                                    }
                                }
                            }
                        }
                    }
                    result.push(patternParts.join(" | "));
                    if (depth === 0) {
                        result.push(")");
                        i += 1;
                    }
                    continue;
                }
            }
            result.push(value[i]);
            i += 1;
        }
        return result.join("");
    };
    Word.prototype.getCondFormattedValue = function () {
        var value = this.ExpandAllAnsiCQuotes(this.value);
        value = this.StripLocaleStringDollars(value);
        value = this.FormatCommandSubstitutions(value, false);
        value = this.NormalizeExtglobWhitespace(value);
        value = value.replace(//g, "");
        return value.replace(/[\n]+$/, '');
    };
    return Word;
}());
var Command = /** @class */ (function () {
    function Command(words, redirects, kind) {
        if (words === void 0) { words = []; }
        if (redirects === void 0) { redirects = []; }
        if (kind === void 0) { kind = ""; }
        this.words = words !== null && words !== void 0 ? words : [];
        this.redirects = redirects !== null && redirects !== void 0 ? redirects : [];
        this.kind = kind;
    }
    Command.prototype.getKind = function () {
        return this.kind;
    };
    Command.prototype.toSexp = function () {
        var parts = [];
        for (var _i = 0, _a = this.words; _i < _a.length; _i++) {
            var w = _a[_i];
            parts.push(w.toSexp());
        }
        for (var _b = 0, _c = this.redirects; _b < _c.length; _b++) {
            var r = _c[_b];
            parts.push(r.toSexp());
        }
        var inner = parts.join(" ");
        if (!(inner !== "")) {
            return "(command)";
        }
        return "(command " + inner + ")";
    };
    return Command;
}());
var Pipeline = /** @class */ (function () {
    function Pipeline(commands, kind) {
        if (commands === void 0) { commands = []; }
        if (kind === void 0) { kind = ""; }
        this.commands = commands !== null && commands !== void 0 ? commands : [];
        this.kind = kind;
    }
    Pipeline.prototype.getKind = function () {
        return this.kind;
    };
    Pipeline.prototype.toSexp = function () {
        if (this.commands.length === 1) {
            return this.commands[0].toSexp();
        }
        var cmds = [];
        var i = 0;
        while (i < this.commands.length) {
            var cmd = this.commands[i];
            if (cmd instanceof PipeBoth) {
                i += 1;
                continue;
            }
            var needsRedirect = i + 1 < this.commands.length && this.commands[i + 1].kind === "pipe-both";
            cmds.push([cmd, needsRedirect]);
            i += 1;
        }
        if (cmds.length === 1) {
            var pair = cmds[0];
            cmd = pair[0];
            var needs = pair[1];
            return this.CmdSexp(cmd, needs);
        }
        var lastPair = cmds[cmds.length - 1];
        var lastCmd = lastPair[0];
        var lastNeeds = lastPair[1];
        var result = this.CmdSexp(lastCmd, lastNeeds);
        var j = cmds.length - 2;
        while (j >= 0) {
            var pair = cmds[j];
            cmd = pair[0];
            var needs = pair[1];
            if (needs && cmd.kind !== "command") {
                result = "(pipe " + cmd.toSexp() + " (redirect \">&\" 1) " + result + ")";
            }
            else {
                result = "(pipe " + this.CmdSexp(cmd, needs) + " " + result + ")";
            }
            j -= 1;
        }
        return result;
    };
    Pipeline.prototype.CmdSexp = function (cmd, needsRedirect) {
        if (!needsRedirect) {
            return cmd.toSexp();
        }
        if (cmd instanceof Command) {
            var parts = [];
            for (var _i = 0, _a = cmd.words; _i < _a.length; _i++) {
                var w = _a[_i];
                parts.push(w.toSexp());
            }
            for (var _b = 0, _c = cmd.redirects; _b < _c.length; _b++) {
                var r = _c[_b];
                parts.push(r.toSexp());
            }
            parts.push("(redirect \">&\" 1)");
            return "(command " + parts.join(" ") + ")";
        }
        return cmd.toSexp();
    };
    return Pipeline;
}());
var List = /** @class */ (function () {
    function List(parts, kind) {
        if (parts === void 0) { parts = []; }
        if (kind === void 0) { kind = ""; }
        this.parts = parts !== null && parts !== void 0 ? parts : [];
        this.kind = kind;
    }
    List.prototype.getKind = function () {
        return this.kind;
    };
    List.prototype.toSexp = function () {
        var parts = this.parts.slice();
        var opNames = new Map([["&&", "and"], ["||", "or"], [";", "semi"], ["\n", "semi"], ["&", "background"]]);
        while (parts.length > 1 && parts[parts.length - 1].kind === "operator" && (parts[parts.length - 1].op === ";" || parts[parts.length - 1].op === "\n")) {
            parts = Sublist(parts, 0, parts.length - 1);
        }
        if (parts.length === 1) {
            return parts[0].toSexp();
        }
        if (parts[parts.length - 1].kind === "operator" && parts[parts.length - 1].op === "&") {
            for (var _i = 0, _a = range(parts.length - 3, 0, -2); _i < _a.length; _i++) {
                var i = _a[_i];
                if (parts[i].kind === "operator" && (parts[i].op === ";" || parts[i].op === "\n")) {
                    var left = Sublist(parts, 0, i);
                    var right = Sublist(parts, i + 1, parts.length - 1);
                    if (left.length > 1) {
                        var leftSexp = new List(left, "list").toSexp();
                    }
                    else {
                        var leftSexp = left[0].toSexp();
                    }
                    if (right.length > 1) {
                        var rightSexp = new List(right, "list").toSexp();
                    }
                    else {
                        var rightSexp = right[0].toSexp();
                    }
                    return "(semi " + leftSexp + " (background " + rightSexp + "))";
                }
            }
            var innerParts = Sublist(parts, 0, parts.length - 1);
            if (innerParts.length === 1) {
                return "(background " + innerParts[0].toSexp() + ")";
            }
            var innerList = new List(innerParts, "list");
            return "(background " + innerList.toSexp() + ")";
        }
        return this.ToSexpWithPrecedence(parts, opNames);
    };
    List.prototype.ToSexpWithPrecedence = function (parts, opNames) {
        var semiPositions = [];
        for (var _i = 0, _a = range(parts.length); _i < _a.length; _i++) {
            var i = _a[_i];
            if (parts[i].kind === "operator" && (parts[i].op === ";" || parts[i].op === "\n")) {
                semiPositions.push(i);
            }
        }
        if (semiPositions.length > 0) {
            var segments = [];
            var start = 0;
            for (var _b = 0, semiPositions_1 = semiPositions; _b < semiPositions_1.length; _b++) {
                var pos = semiPositions_1[_b];
                var seg = Sublist(parts, start, pos);
                if (seg.length > 0 && seg[0].kind !== "operator") {
                    segments.push(seg);
                }
                start = pos + 1;
            }
            seg = Sublist(parts, start, parts.length);
            if (seg.length > 0 && seg[0].kind !== "operator") {
                segments.push(seg);
            }
            if (!(segments.length > 0)) {
                return "()";
            }
            var result = this.ToSexpAmpAndHigher(segments[0], opNames);
            for (var _c = 0, _d = range(1, segments.length); _c < _d.length; _c++) {
                var i = _d[_c];
                result = "(semi " + result + " " + this.ToSexpAmpAndHigher(segments[i], opNames) + ")";
            }
            return result;
        }
        return this.ToSexpAmpAndHigher(parts, opNames);
    };
    List.prototype.ToSexpAmpAndHigher = function (parts, opNames) {
        if (parts.length === 1) {
            return parts[0].toSexp();
        }
        var ampPositions = [];
        for (var _i = 0, _a = range(1, parts.length - 1, 2); _i < _a.length; _i++) {
            var i = _a[_i];
            if (parts[i].kind === "operator" && parts[i].op === "&") {
                ampPositions.push(i);
            }
        }
        if (ampPositions.length > 0) {
            var segments = [];
            var start = 0;
            for (var _b = 0, ampPositions_1 = ampPositions; _b < ampPositions_1.length; _b++) {
                var pos = ampPositions_1[_b];
                segments.push(Sublist(parts, start, pos));
                start = pos + 1;
            }
            segments.push(Sublist(parts, start, parts.length));
            var result = this.ToSexpAndOr(segments[0], opNames);
            for (var _c = 0, _d = range(1, segments.length); _c < _d.length; _c++) {
                var i = _d[_c];
                result = "(background " + result + " " + this.ToSexpAndOr(segments[i], opNames) + ")";
            }
            return result;
        }
        return this.ToSexpAndOr(parts, opNames);
    };
    List.prototype.ToSexpAndOr = function (parts, opNames) {
        var _a;
        if (parts.length === 1) {
            return parts[0].toSexp();
        }
        var result = parts[0].toSexp();
        for (var _i = 0, _b = range(1, parts.length - 1, 2); _i < _b.length; _i++) {
            var i = _b[_i];
            var op = parts[i];
            var cmd = parts[i + 1];
            var opName = (_a = opNames.get(op.op)) !== null && _a !== void 0 ? _a : op.op;
            result = "(" + opName + " " + result + " " + cmd.toSexp() + ")";
        }
        return result;
    };
    return List;
}());
var Operator = /** @class */ (function () {
    function Operator(op, kind) {
        if (op === void 0) { op = ""; }
        if (kind === void 0) { kind = ""; }
        this.op = op;
        this.kind = kind;
    }
    Operator.prototype.getKind = function () {
        return this.kind;
    };
    Operator.prototype.toSexp = function () {
        var _a;
        var names = new Map([["&&", "and"], ["||", "or"], [";", "semi"], ["&", "bg"], ["|", "pipe"]]);
        return ("(" + ((_a = names.get(this.op)) !== null && _a !== void 0 ? _a : this.op)) + ")";
    };
    return Operator;
}());
var PipeBoth = /** @class */ (function () {
    function PipeBoth(kind) {
        if (kind === void 0) { kind = ""; }
        this.kind = kind;
    }
    PipeBoth.prototype.getKind = function () {
        return this.kind;
    };
    PipeBoth.prototype.toSexp = function () {
        return "(pipe-both)";
    };
    return PipeBoth;
}());
var Empty = /** @class */ (function () {
    function Empty(kind) {
        if (kind === void 0) { kind = ""; }
        this.kind = kind;
    }
    Empty.prototype.getKind = function () {
        return this.kind;
    };
    Empty.prototype.toSexp = function () {
        return "";
    };
    return Empty;
}());
var Comment = /** @class */ (function () {
    function Comment(text, kind) {
        if (text === void 0) { text = ""; }
        if (kind === void 0) { kind = ""; }
        this.text = text;
        this.kind = kind;
    }
    Comment.prototype.getKind = function () {
        return this.kind;
    };
    Comment.prototype.toSexp = function () {
        return "";
    };
    return Comment;
}());
var Redirect = /** @class */ (function () {
    function Redirect(op, target, fd, kind) {
        if (op === void 0) { op = ""; }
        if (target === void 0) { target = null; }
        if (fd === void 0) { fd = null; }
        if (kind === void 0) { kind = ""; }
        this.op = op;
        this.target = target;
        this.fd = fd;
        this.kind = kind;
    }
    Redirect.prototype.getKind = function () {
        return this.kind;
    };
    Redirect.prototype.toSexp = function () {
        var op = this.op.replace(/^[0123456789]+/, '');
        if (op.startsWith("{")) {
            var j = 1;
            if (j < op.length && (/^[a-zA-Z]$/.test(op[j]) || op[j] === "_")) {
                j += 1;
                while (j < op.length && (/^[a-zA-Z0-9]$/.test(op[j]) || op[j] === "_")) {
                    j += 1;
                }
                if (j < op.length && op[j] === "[") {
                    j += 1;
                    while (j < op.length && op[j] !== "]") {
                        j += 1;
                    }
                    if (j < op.length && op[j] === "]") {
                        j += 1;
                    }
                }
                if (j < op.length && op[j] === "}") {
                    op = Substring(op, j + 1, op.length);
                }
            }
        }
        var targetVal = this.target.value;
        targetVal = this.target.ExpandAllAnsiCQuotes(targetVal);
        targetVal = this.target.StripLocaleStringDollars(targetVal);
        targetVal = this.target.FormatCommandSubstitutions(targetVal, false);
        targetVal = this.target.StripArithLineContinuations(targetVal);
        if (targetVal.endsWith("\\") && !targetVal.endsWith("\\\\")) {
            targetVal = targetVal + "\\";
        }
        if (targetVal.startsWith("&")) {
            if (op === ">") {
                op = ">&";
            }
            else {
                if (op === "<") {
                    op = "<&";
                }
            }
            var raw = Substring(targetVal, 1, targetVal.length);
            if (/^[0-9]+$/.test(raw) && parseInt(raw, 10) <= 2147483647) {
                return "(redirect \"" + op + "\" " + String(parseInt(raw, 10)) + ")";
            }
            if (raw.endsWith("-") && /^[0-9]+$/.test(raw.slice(0, raw.length - 1)) && parseInt(raw.slice(0, raw.length - 1), 10) <= 2147483647) {
                return "(redirect \"" + op + "\" " + String(parseInt(raw.slice(0, raw.length - 1), 10)) + ")";
            }
            if (targetVal === "&-") {
                return "(redirect \">&-\" 0)";
            }
            var fdTarget = raw.endsWith("-") ? raw.slice(0, raw.length - 1) : raw;
            return "(redirect \"" + op + "\" \"" + fdTarget + "\")";
        }
        if (op === ">&" || op === "<&") {
            if (/^[0-9]+$/.test(targetVal) && parseInt(targetVal, 10) <= 2147483647) {
                return "(redirect \"" + op + "\" " + String(parseInt(targetVal, 10)) + ")";
            }
            if (targetVal === "-") {
                return "(redirect \">&-\" 0)";
            }
            if (targetVal.endsWith("-") && /^[0-9]+$/.test(targetVal.slice(0, targetVal.length - 1)) && parseInt(targetVal.slice(0, targetVal.length - 1), 10) <= 2147483647) {
                return "(redirect \"" + op + "\" " + String(parseInt(targetVal.slice(0, targetVal.length - 1), 10)) + ")";
            }
            var outVal = targetVal.endsWith("-") ? targetVal.slice(0, targetVal.length - 1) : targetVal;
            return "(redirect \"" + op + "\" \"" + outVal + "\")";
        }
        return "(redirect \"" + op + "\" \"" + targetVal + "\")";
    };
    return Redirect;
}());
var HereDoc = /** @class */ (function () {
    function HereDoc(delimiter, content, stripTabs, quoted, fd, complete, StartPos, kind) {
        if (delimiter === void 0) { delimiter = ""; }
        if (content === void 0) { content = ""; }
        if (stripTabs === void 0) { stripTabs = false; }
        if (quoted === void 0) { quoted = false; }
        if (fd === void 0) { fd = null; }
        if (complete === void 0) { complete = false; }
        if (StartPos === void 0) { StartPos = 0; }
        if (kind === void 0) { kind = ""; }
        this.delimiter = delimiter;
        this.content = content;
        this.stripTabs = stripTabs;
        this.quoted = quoted;
        this.fd = fd;
        this.complete = complete;
        this.StartPos = StartPos;
        this.kind = kind;
    }
    HereDoc.prototype.getKind = function () {
        return this.kind;
    };
    HereDoc.prototype.toSexp = function () {
        var op = this.stripTabs ? "<<-" : "<<";
        var content = this.content;
        if (content.endsWith("\\") && !content.endsWith("\\\\")) {
            content = content + "\\";
        }
        return "(redirect \"".concat(op, "\" \"").concat(content, "\")");
    };
    return HereDoc;
}());
var Subshell = /** @class */ (function () {
    function Subshell(body, redirects, kind) {
        if (body === void 0) { body = null; }
        if (redirects === void 0) { redirects = []; }
        if (kind === void 0) { kind = ""; }
        this.body = body;
        this.redirects = redirects !== null && redirects !== void 0 ? redirects : [];
        this.kind = kind;
    }
    Subshell.prototype.getKind = function () {
        return this.kind;
    };
    Subshell.prototype.toSexp = function () {
        var base = "(subshell " + this.body.toSexp() + ")";
        return AppendRedirects(base, this.redirects);
    };
    return Subshell;
}());
var BraceGroup = /** @class */ (function () {
    function BraceGroup(body, redirects, kind) {
        if (body === void 0) { body = null; }
        if (redirects === void 0) { redirects = []; }
        if (kind === void 0) { kind = ""; }
        this.body = body;
        this.redirects = redirects !== null && redirects !== void 0 ? redirects : [];
        this.kind = kind;
    }
    BraceGroup.prototype.getKind = function () {
        return this.kind;
    };
    BraceGroup.prototype.toSexp = function () {
        var base = "(brace-group " + this.body.toSexp() + ")";
        return AppendRedirects(base, this.redirects);
    };
    return BraceGroup;
}());
var If = /** @class */ (function () {
    function If(condition, thenBody, elseBody, redirects, kind) {
        if (condition === void 0) { condition = null; }
        if (thenBody === void 0) { thenBody = null; }
        if (elseBody === void 0) { elseBody = null; }
        if (redirects === void 0) { redirects = []; }
        if (kind === void 0) { kind = ""; }
        this.condition = condition;
        this.thenBody = thenBody;
        this.elseBody = elseBody;
        this.redirects = redirects !== null && redirects !== void 0 ? redirects : [];
        this.kind = kind;
    }
    If.prototype.getKind = function () {
        return this.kind;
    };
    If.prototype.toSexp = function () {
        var result = "(if " + this.condition.toSexp() + " " + this.thenBody.toSexp();
        if (this.elseBody !== null) {
            result = result + " " + this.elseBody.toSexp();
        }
        result = result + ")";
        for (var _i = 0, _a = this.redirects; _i < _a.length; _i++) {
            var r = _a[_i];
            result = result + " " + r.toSexp();
        }
        return result;
    };
    return If;
}());
var While = /** @class */ (function () {
    function While(condition, body, redirects, kind) {
        if (condition === void 0) { condition = null; }
        if (body === void 0) { body = null; }
        if (redirects === void 0) { redirects = []; }
        if (kind === void 0) { kind = ""; }
        this.condition = condition;
        this.body = body;
        this.redirects = redirects !== null && redirects !== void 0 ? redirects : [];
        this.kind = kind;
    }
    While.prototype.getKind = function () {
        return this.kind;
    };
    While.prototype.toSexp = function () {
        var base = "(while " + this.condition.toSexp() + " " + this.body.toSexp() + ")";
        return AppendRedirects(base, this.redirects);
    };
    return While;
}());
var Until = /** @class */ (function () {
    function Until(condition, body, redirects, kind) {
        if (condition === void 0) { condition = null; }
        if (body === void 0) { body = null; }
        if (redirects === void 0) { redirects = []; }
        if (kind === void 0) { kind = ""; }
        this.condition = condition;
        this.body = body;
        this.redirects = redirects !== null && redirects !== void 0 ? redirects : [];
        this.kind = kind;
    }
    Until.prototype.getKind = function () {
        return this.kind;
    };
    Until.prototype.toSexp = function () {
        var base = "(until " + this.condition.toSexp() + " " + this.body.toSexp() + ")";
        return AppendRedirects(base, this.redirects);
    };
    return Until;
}());
var For = /** @class */ (function () {
    function For(varName, words, body, redirects, kind) {
        if (varName === void 0) { varName = ""; }
        if (words === void 0) { words = null; }
        if (body === void 0) { body = null; }
        if (redirects === void 0) { redirects = []; }
        if (kind === void 0) { kind = ""; }
        this.varName = varName;
        this.words = words;
        this.body = body;
        this.redirects = redirects !== null && redirects !== void 0 ? redirects : [];
        this.kind = kind;
    }
    For.prototype.getKind = function () {
        return this.kind;
    };
    For.prototype.toSexp = function () {
        var suffix = "";
        if (this.redirects.length > 0) {
            var redirectParts = [];
            for (var _i = 0, _a = this.redirects; _i < _a.length; _i++) {
                var r = _a[_i];
                redirectParts.push(r.toSexp());
            }
            suffix = " " + redirectParts.join(" ");
        }
        var tempWord = new Word(this.varName, [], "word");
        var varFormatted = tempWord.FormatCommandSubstitutions(this.varName, false);
        var varEscaped = varFormatted.replace(/\\/g, "\\\\").replace(/"/g, "\\\"");
        if (this.words === null) {
            return "(for (word \"" + varEscaped + "\") (in (word \"\\\"$@\\\"\")) " + this.body.toSexp() + ")" + suffix;
        }
        else {
            if (this.words.length === 0) {
                return "(for (word \"" + varEscaped + "\") (in) " + this.body.toSexp() + ")" + suffix;
            }
            else {
                var wordParts = [];
                for (var _b = 0, _c = this.words; _b < _c.length; _b++) {
                    var w = _c[_b];
                    wordParts.push(w.toSexp());
                }
                var wordStrs = wordParts.join(" ");
                return "(for (word \"" + varEscaped + "\") (in " + wordStrs + ") " + this.body.toSexp() + ")" + suffix;
            }
        }
    };
    return For;
}());
var ForArith = /** @class */ (function () {
    function ForArith(init, cond, incr, body, redirects, kind) {
        if (init === void 0) { init = ""; }
        if (cond === void 0) { cond = ""; }
        if (incr === void 0) { incr = ""; }
        if (body === void 0) { body = null; }
        if (redirects === void 0) { redirects = []; }
        if (kind === void 0) { kind = ""; }
        this.init = init;
        this.cond = cond;
        this.incr = incr;
        this.body = body;
        this.redirects = redirects !== null && redirects !== void 0 ? redirects : [];
        this.kind = kind;
    }
    ForArith.prototype.getKind = function () {
        return this.kind;
    };
    ForArith.prototype.toSexp = function () {
        var suffix = "";
        if (this.redirects.length > 0) {
            var redirectParts = [];
            for (var _i = 0, _a = this.redirects; _i < _a.length; _i++) {
                var r = _a[_i];
                redirectParts.push(r.toSexp());
            }
            suffix = " " + redirectParts.join(" ");
        }
        var initVal = this.init !== "" ? this.init : "1";
        var condVal = this.cond !== "" ? this.cond : "1";
        var incrVal = this.incr !== "" ? this.incr : "1";
        var initStr = FormatArithVal(initVal);
        var condStr = FormatArithVal(condVal);
        var incrStr = FormatArithVal(incrVal);
        var bodyStr = this.body.toSexp();
        return "(arith-for (init (word \"".concat(initStr, "\")) (test (word \"").concat(condStr, "\")) (step (word \"").concat(incrStr, "\")) ").concat(bodyStr, ")").concat(suffix);
    };
    return ForArith;
}());
var Select = /** @class */ (function () {
    function Select(varName, words, body, redirects, kind) {
        if (varName === void 0) { varName = ""; }
        if (words === void 0) { words = null; }
        if (body === void 0) { body = null; }
        if (redirects === void 0) { redirects = []; }
        if (kind === void 0) { kind = ""; }
        this.varName = varName;
        this.words = words;
        this.body = body;
        this.redirects = redirects !== null && redirects !== void 0 ? redirects : [];
        this.kind = kind;
    }
    Select.prototype.getKind = function () {
        return this.kind;
    };
    Select.prototype.toSexp = function () {
        var suffix = "";
        if (this.redirects.length > 0) {
            var redirectParts = [];
            for (var _i = 0, _a = this.redirects; _i < _a.length; _i++) {
                var r = _a[_i];
                redirectParts.push(r.toSexp());
            }
            suffix = " " + redirectParts.join(" ");
        }
        var varEscaped = this.varName.replace(/\\/g, "\\\\").replace(/"/g, "\\\"");
        if (this.words !== null) {
            var wordParts = [];
            for (var _b = 0, _c = this.words; _b < _c.length; _b++) {
                var w = _c[_b];
                wordParts.push(w.toSexp());
            }
            var wordStrs = wordParts.join(" ");
            if (this.words.length > 0) {
                var inClause = "(in " + wordStrs + ")";
            }
            else {
                var inClause = "(in)";
            }
        }
        else {
            var inClause = "(in (word \"\\\"$@\\\"\"))";
        }
        return "(select (word \"" + varEscaped + "\") " + inClause + " " + this.body.toSexp() + ")" + suffix;
    };
    return Select;
}());
var Case = /** @class */ (function () {
    function Case(word, patterns, redirects, kind) {
        if (word === void 0) { word = null; }
        if (patterns === void 0) { patterns = []; }
        if (redirects === void 0) { redirects = []; }
        if (kind === void 0) { kind = ""; }
        this.word = word;
        this.patterns = patterns !== null && patterns !== void 0 ? patterns : [];
        this.redirects = redirects !== null && redirects !== void 0 ? redirects : [];
        this.kind = kind;
    }
    Case.prototype.getKind = function () {
        return this.kind;
    };
    Case.prototype.toSexp = function () {
        var parts = [];
        parts.push("(case " + this.word.toSexp());
        for (var _i = 0, _a = this.patterns; _i < _a.length; _i++) {
            var p = _a[_i];
            parts.push(p.toSexp());
        }
        var base = parts.join(" ") + ")";
        return AppendRedirects(base, this.redirects);
    };
    return Case;
}());
var CasePattern = /** @class */ (function () {
    function CasePattern(pattern, body, terminator, kind) {
        if (pattern === void 0) { pattern = ""; }
        if (body === void 0) { body = null; }
        if (terminator === void 0) { terminator = ""; }
        if (kind === void 0) { kind = ""; }
        this.pattern = pattern;
        this.body = body;
        this.terminator = terminator;
        this.kind = kind;
    }
    CasePattern.prototype.getKind = function () {
        return this.kind;
    };
    CasePattern.prototype.toSexp = function () {
        var alternatives = [];
        var current = [];
        var i = 0;
        var depth = 0;
        while (i < this.pattern.length) {
            var ch = this.pattern[i];
            if (ch === "\\" && i + 1 < this.pattern.length) {
                current.push(Substring(this.pattern, i, i + 2));
                i += 2;
            }
            else {
                if ((ch === "@" || ch === "?" || ch === "*" || ch === "+" || ch === "!") && i + 1 < this.pattern.length && this.pattern[i + 1] === "(") {
                    current.push(ch);
                    current.push("(");
                    depth += 1;
                    i += 2;
                }
                else {
                    if (IsExpansionStart(this.pattern, i, "$(")) {
                        current.push(ch);
                        current.push("(");
                        depth += 1;
                        i += 2;
                    }
                    else {
                        if (ch === "(" && depth > 0) {
                            current.push(ch);
                            depth += 1;
                            i += 1;
                        }
                        else {
                            if (ch === ")" && depth > 0) {
                                current.push(ch);
                                depth -= 1;
                                i += 1;
                            }
                            else {
                                if (ch === "[") {
                                    var _a = ConsumeBracketClass(this.pattern, i, depth), result0 = _a[0], result1 = _a[1], result2 = _a[2];
                                    i = result0;
                                    current.push.apply(current, result1);
                                }
                                else {
                                    if (ch === "'" && depth === 0) {
                                        var _b = ConsumeSingleQuote(this.pattern, i), result0 = _b[0], result1 = _b[1];
                                        i = result0;
                                        current.push.apply(current, result1);
                                    }
                                    else {
                                        if (ch === "\"" && depth === 0) {
                                            var _c = ConsumeDoubleQuote(this.pattern, i), result0 = _c[0], result1 = _c[1];
                                            i = result0;
                                            current.push.apply(current, result1);
                                        }
                                        else {
                                            if (ch === "|" && depth === 0) {
                                                alternatives.push(current.join(""));
                                                current = [];
                                                i += 1;
                                            }
                                            else {
                                                current.push(ch);
                                                i += 1;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        alternatives.push(current.join(""));
        var wordList = [];
        for (var _i = 0, alternatives_1 = alternatives; _i < alternatives_1.length; _i++) {
            var alt = alternatives_1[_i];
            wordList.push(new Word(alt, [], "word").toSexp());
        }
        var patternStr = wordList.join(" ");
        var parts = ["(pattern (" + patternStr + ")"];
        if (this.body !== null) {
            parts.push(" " + this.body.toSexp());
        }
        else {
            parts.push(" ()");
        }
        parts.push(")");
        return parts.join("");
    };
    return CasePattern;
}());
var FunctionName = /** @class */ (function () {
    function FunctionName(name, body, kind) {
        if (name === void 0) { name = ""; }
        if (body === void 0) { body = null; }
        if (kind === void 0) { kind = ""; }
        this.name = name;
        this.body = body;
        this.kind = kind;
    }
    FunctionName.prototype.getKind = function () {
        return this.kind;
    };
    FunctionName.prototype.toSexp = function () {
        return "(function \"" + this.name + "\" " + this.body.toSexp() + ")";
    };
    return FunctionName;
}());
var ParamExpansion = /** @class */ (function () {
    function ParamExpansion(param, op, arg, kind) {
        if (param === void 0) { param = ""; }
        if (op === void 0) { op = ""; }
        if (arg === void 0) { arg = ""; }
        if (kind === void 0) { kind = ""; }
        this.param = param;
        this.op = op;
        this.arg = arg;
        this.kind = kind;
    }
    ParamExpansion.prototype.getKind = function () {
        return this.kind;
    };
    ParamExpansion.prototype.toSexp = function () {
        var escapedParam = this.param.replace(/\\/g, "\\\\").replace(/"/g, "\\\"");
        if (this.op !== "") {
            var escapedOp = this.op.replace(/\\/g, "\\\\").replace(/"/g, "\\\"");
            if (this.arg !== "") {
                var argVal = this.arg;
            }
            else {
                var argVal = "";
            }
            var escapedArg = argVal.replace(/\\/g, "\\\\").replace(/"/g, "\\\"");
            return "(param \"" + escapedParam + "\" \"" + escapedOp + "\" \"" + escapedArg + "\")";
        }
        return "(param \"" + escapedParam + "\")";
    };
    return ParamExpansion;
}());
var ParamLength = /** @class */ (function () {
    function ParamLength(param, kind) {
        if (param === void 0) { param = ""; }
        if (kind === void 0) { kind = ""; }
        this.param = param;
        this.kind = kind;
    }
    ParamLength.prototype.getKind = function () {
        return this.kind;
    };
    ParamLength.prototype.toSexp = function () {
        var escaped = this.param.replace(/\\/g, "\\\\").replace(/"/g, "\\\"");
        return "(param-len \"" + escaped + "\")";
    };
    return ParamLength;
}());
var ParamIndirect = /** @class */ (function () {
    function ParamIndirect(param, op, arg, kind) {
        if (param === void 0) { param = ""; }
        if (op === void 0) { op = ""; }
        if (arg === void 0) { arg = ""; }
        if (kind === void 0) { kind = ""; }
        this.param = param;
        this.op = op;
        this.arg = arg;
        this.kind = kind;
    }
    ParamIndirect.prototype.getKind = function () {
        return this.kind;
    };
    ParamIndirect.prototype.toSexp = function () {
        var escaped = this.param.replace(/\\/g, "\\\\").replace(/"/g, "\\\"");
        if (this.op !== "") {
            var escapedOp = this.op.replace(/\\/g, "\\\\").replace(/"/g, "\\\"");
            if (this.arg !== "") {
                var argVal = this.arg;
            }
            else {
                var argVal = "";
            }
            var escapedArg = argVal.replace(/\\/g, "\\\\").replace(/"/g, "\\\"");
            return "(param-indirect \"" + escaped + "\" \"" + escapedOp + "\" \"" + escapedArg + "\")";
        }
        return "(param-indirect \"" + escaped + "\")";
    };
    return ParamIndirect;
}());
var CommandSubstitution = /** @class */ (function () {
    function CommandSubstitution(command, brace, kind) {
        if (command === void 0) { command = null; }
        if (brace === void 0) { brace = false; }
        if (kind === void 0) { kind = ""; }
        this.command = command;
        this.brace = brace;
        this.kind = kind;
    }
    CommandSubstitution.prototype.getKind = function () {
        return this.kind;
    };
    CommandSubstitution.prototype.toSexp = function () {
        if (this.brace) {
            return "(funsub " + this.command.toSexp() + ")";
        }
        return "(cmdsub " + this.command.toSexp() + ")";
    };
    return CommandSubstitution;
}());
var ArithmeticExpansion = /** @class */ (function () {
    function ArithmeticExpansion(expression, kind) {
        if (expression === void 0) { expression = null; }
        if (kind === void 0) { kind = ""; }
        this.expression = expression;
        this.kind = kind;
    }
    ArithmeticExpansion.prototype.getKind = function () {
        return this.kind;
    };
    ArithmeticExpansion.prototype.toSexp = function () {
        if (this.expression === null) {
            return "(arith)";
        }
        return "(arith " + this.expression.toSexp() + ")";
    };
    return ArithmeticExpansion;
}());
var ArithmeticCommand = /** @class */ (function () {
    function ArithmeticCommand(expression, redirects, rawContent, kind) {
        if (expression === void 0) { expression = null; }
        if (redirects === void 0) { redirects = []; }
        if (rawContent === void 0) { rawContent = ""; }
        if (kind === void 0) { kind = ""; }
        this.expression = expression;
        this.redirects = redirects !== null && redirects !== void 0 ? redirects : [];
        this.rawContent = rawContent;
        this.kind = kind;
    }
    ArithmeticCommand.prototype.getKind = function () {
        return this.kind;
    };
    ArithmeticCommand.prototype.toSexp = function () {
        var formatted = new Word(this.rawContent, [], "word").FormatCommandSubstitutions(this.rawContent, true);
        var escaped = formatted.replace(/\\/g, "\\\\").replace(/"/g, "\\\"").replace(/\n/g, "\\n").replace(/\t/g, "\\t");
        var result = "(arith (word \"" + escaped + "\"))";
        if (this.redirects.length > 0) {
            var redirectParts = [];
            for (var _i = 0, _a = this.redirects; _i < _a.length; _i++) {
                var r = _a[_i];
                redirectParts.push(r.toSexp());
            }
            var redirectSexps = redirectParts.join(" ");
            return result + " " + redirectSexps;
        }
        return result;
    };
    return ArithmeticCommand;
}());
var ArithNumber = /** @class */ (function () {
    function ArithNumber(value, kind) {
        if (value === void 0) { value = ""; }
        if (kind === void 0) { kind = ""; }
        this.value = value;
        this.kind = kind;
    }
    ArithNumber.prototype.getKind = function () {
        return this.kind;
    };
    ArithNumber.prototype.toSexp = function () {
        return "(number \"" + this.value + "\")";
    };
    return ArithNumber;
}());
var ArithEmpty = /** @class */ (function () {
    function ArithEmpty(kind) {
        if (kind === void 0) { kind = ""; }
        this.kind = kind;
    }
    ArithEmpty.prototype.getKind = function () {
        return this.kind;
    };
    ArithEmpty.prototype.toSexp = function () {
        return "(empty)";
    };
    return ArithEmpty;
}());
var ArithVar = /** @class */ (function () {
    function ArithVar(name, kind) {
        if (name === void 0) { name = ""; }
        if (kind === void 0) { kind = ""; }
        this.name = name;
        this.kind = kind;
    }
    ArithVar.prototype.getKind = function () {
        return this.kind;
    };
    ArithVar.prototype.toSexp = function () {
        return "(var \"" + this.name + "\")";
    };
    return ArithVar;
}());
var ArithBinaryOp = /** @class */ (function () {
    function ArithBinaryOp(op, left, right, kind) {
        if (op === void 0) { op = ""; }
        if (left === void 0) { left = null; }
        if (right === void 0) { right = null; }
        if (kind === void 0) { kind = ""; }
        this.op = op;
        this.left = left;
        this.right = right;
        this.kind = kind;
    }
    ArithBinaryOp.prototype.getKind = function () {
        return this.kind;
    };
    ArithBinaryOp.prototype.toSexp = function () {
        return "(binary-op \"" + this.op + "\" " + this.left.toSexp() + " " + this.right.toSexp() + ")";
    };
    return ArithBinaryOp;
}());
var ArithUnaryOp = /** @class */ (function () {
    function ArithUnaryOp(op, operand, kind) {
        if (op === void 0) { op = ""; }
        if (operand === void 0) { operand = null; }
        if (kind === void 0) { kind = ""; }
        this.op = op;
        this.operand = operand;
        this.kind = kind;
    }
    ArithUnaryOp.prototype.getKind = function () {
        return this.kind;
    };
    ArithUnaryOp.prototype.toSexp = function () {
        return "(unary-op \"" + this.op + "\" " + this.operand.toSexp() + ")";
    };
    return ArithUnaryOp;
}());
var ArithPreIncr = /** @class */ (function () {
    function ArithPreIncr(operand, kind) {
        if (operand === void 0) { operand = null; }
        if (kind === void 0) { kind = ""; }
        this.operand = operand;
        this.kind = kind;
    }
    ArithPreIncr.prototype.getKind = function () {
        return this.kind;
    };
    ArithPreIncr.prototype.toSexp = function () {
        return "(pre-incr " + this.operand.toSexp() + ")";
    };
    return ArithPreIncr;
}());
var ArithPostIncr = /** @class */ (function () {
    function ArithPostIncr(operand, kind) {
        if (operand === void 0) { operand = null; }
        if (kind === void 0) { kind = ""; }
        this.operand = operand;
        this.kind = kind;
    }
    ArithPostIncr.prototype.getKind = function () {
        return this.kind;
    };
    ArithPostIncr.prototype.toSexp = function () {
        return "(post-incr " + this.operand.toSexp() + ")";
    };
    return ArithPostIncr;
}());
var ArithPreDecr = /** @class */ (function () {
    function ArithPreDecr(operand, kind) {
        if (operand === void 0) { operand = null; }
        if (kind === void 0) { kind = ""; }
        this.operand = operand;
        this.kind = kind;
    }
    ArithPreDecr.prototype.getKind = function () {
        return this.kind;
    };
    ArithPreDecr.prototype.toSexp = function () {
        return "(pre-decr " + this.operand.toSexp() + ")";
    };
    return ArithPreDecr;
}());
var ArithPostDecr = /** @class */ (function () {
    function ArithPostDecr(operand, kind) {
        if (operand === void 0) { operand = null; }
        if (kind === void 0) { kind = ""; }
        this.operand = operand;
        this.kind = kind;
    }
    ArithPostDecr.prototype.getKind = function () {
        return this.kind;
    };
    ArithPostDecr.prototype.toSexp = function () {
        return "(post-decr " + this.operand.toSexp() + ")";
    };
    return ArithPostDecr;
}());
var ArithAssign = /** @class */ (function () {
    function ArithAssign(op, target, value, kind) {
        if (op === void 0) { op = ""; }
        if (target === void 0) { target = null; }
        if (value === void 0) { value = null; }
        if (kind === void 0) { kind = ""; }
        this.op = op;
        this.target = target;
        this.value = value;
        this.kind = kind;
    }
    ArithAssign.prototype.getKind = function () {
        return this.kind;
    };
    ArithAssign.prototype.toSexp = function () {
        return "(assign \"" + this.op + "\" " + this.target.toSexp() + " " + this.value.toSexp() + ")";
    };
    return ArithAssign;
}());
var ArithTernary = /** @class */ (function () {
    function ArithTernary(condition, ifTrue, ifFalse, kind) {
        if (condition === void 0) { condition = null; }
        if (ifTrue === void 0) { ifTrue = null; }
        if (ifFalse === void 0) { ifFalse = null; }
        if (kind === void 0) { kind = ""; }
        this.condition = condition;
        this.ifTrue = ifTrue;
        this.ifFalse = ifFalse;
        this.kind = kind;
    }
    ArithTernary.prototype.getKind = function () {
        return this.kind;
    };
    ArithTernary.prototype.toSexp = function () {
        return "(ternary " + this.condition.toSexp() + " " + this.ifTrue.toSexp() + " " + this.ifFalse.toSexp() + ")";
    };
    return ArithTernary;
}());
var ArithComma = /** @class */ (function () {
    function ArithComma(left, right, kind) {
        if (left === void 0) { left = null; }
        if (right === void 0) { right = null; }
        if (kind === void 0) { kind = ""; }
        this.left = left;
        this.right = right;
        this.kind = kind;
    }
    ArithComma.prototype.getKind = function () {
        return this.kind;
    };
    ArithComma.prototype.toSexp = function () {
        return "(comma " + this.left.toSexp() + " " + this.right.toSexp() + ")";
    };
    return ArithComma;
}());
var ArithSubscript = /** @class */ (function () {
    function ArithSubscript(array, index, kind) {
        if (array === void 0) { array = ""; }
        if (index === void 0) { index = null; }
        if (kind === void 0) { kind = ""; }
        this.array = array;
        this.index = index;
        this.kind = kind;
    }
    ArithSubscript.prototype.getKind = function () {
        return this.kind;
    };
    ArithSubscript.prototype.toSexp = function () {
        return "(subscript \"" + this.array + "\" " + this.index.toSexp() + ")";
    };
    return ArithSubscript;
}());
var ArithEscape = /** @class */ (function () {
    function ArithEscape(char, kind) {
        if (char === void 0) { char = ""; }
        if (kind === void 0) { kind = ""; }
        this.char = char;
        this.kind = kind;
    }
    ArithEscape.prototype.getKind = function () {
        return this.kind;
    };
    ArithEscape.prototype.toSexp = function () {
        return "(escape \"" + this.char + "\")";
    };
    return ArithEscape;
}());
var ArithDeprecated = /** @class */ (function () {
    function ArithDeprecated(expression, kind) {
        if (expression === void 0) { expression = ""; }
        if (kind === void 0) { kind = ""; }
        this.expression = expression;
        this.kind = kind;
    }
    ArithDeprecated.prototype.getKind = function () {
        return this.kind;
    };
    ArithDeprecated.prototype.toSexp = function () {
        var escaped = this.expression.replace(/\\/g, "\\\\").replace(/"/g, "\\\"").replace(/\n/g, "\\n");
        return "(arith-deprecated \"" + escaped + "\")";
    };
    return ArithDeprecated;
}());
var ArithConcat = /** @class */ (function () {
    function ArithConcat(parts, kind) {
        if (parts === void 0) { parts = []; }
        if (kind === void 0) { kind = ""; }
        this.parts = parts !== null && parts !== void 0 ? parts : [];
        this.kind = kind;
    }
    ArithConcat.prototype.getKind = function () {
        return this.kind;
    };
    ArithConcat.prototype.toSexp = function () {
        var sexps = [];
        for (var _i = 0, _a = this.parts; _i < _a.length; _i++) {
            var p = _a[_i];
            sexps.push(p.toSexp());
        }
        return "(arith-concat " + sexps.join(" ") + ")";
    };
    return ArithConcat;
}());
var AnsiCQuote = /** @class */ (function () {
    function AnsiCQuote(content, kind) {
        if (content === void 0) { content = ""; }
        if (kind === void 0) { kind = ""; }
        this.content = content;
        this.kind = kind;
    }
    AnsiCQuote.prototype.getKind = function () {
        return this.kind;
    };
    AnsiCQuote.prototype.toSexp = function () {
        var escaped = this.content.replace(/\\/g, "\\\\").replace(/"/g, "\\\"").replace(/\n/g, "\\n");
        return "(ansi-c \"" + escaped + "\")";
    };
    return AnsiCQuote;
}());
var LocaleString = /** @class */ (function () {
    function LocaleString(content, kind) {
        if (content === void 0) { content = ""; }
        if (kind === void 0) { kind = ""; }
        this.content = content;
        this.kind = kind;
    }
    LocaleString.prototype.getKind = function () {
        return this.kind;
    };
    LocaleString.prototype.toSexp = function () {
        var escaped = this.content.replace(/\\/g, "\\\\").replace(/"/g, "\\\"").replace(/\n/g, "\\n");
        return "(locale \"" + escaped + "\")";
    };
    return LocaleString;
}());
var ProcessSubstitution = /** @class */ (function () {
    function ProcessSubstitution(direction, command, kind) {
        if (direction === void 0) { direction = ""; }
        if (command === void 0) { command = null; }
        if (kind === void 0) { kind = ""; }
        this.direction = direction;
        this.command = command;
        this.kind = kind;
    }
    ProcessSubstitution.prototype.getKind = function () {
        return this.kind;
    };
    ProcessSubstitution.prototype.toSexp = function () {
        return "(procsub \"" + this.direction + "\" " + this.command.toSexp() + ")";
    };
    return ProcessSubstitution;
}());
var Negation = /** @class */ (function () {
    function Negation(pipeline, kind) {
        if (pipeline === void 0) { pipeline = null; }
        if (kind === void 0) { kind = ""; }
        this.pipeline = pipeline;
        this.kind = kind;
    }
    Negation.prototype.getKind = function () {
        return this.kind;
    };
    Negation.prototype.toSexp = function () {
        if (this.pipeline === null) {
            return "(negation (command))";
        }
        return "(negation " + this.pipeline.toSexp() + ")";
    };
    return Negation;
}());
var Time = /** @class */ (function () {
    function Time(pipeline, posix, kind) {
        if (pipeline === void 0) { pipeline = null; }
        if (posix === void 0) { posix = false; }
        if (kind === void 0) { kind = ""; }
        this.pipeline = pipeline;
        this.posix = posix;
        this.kind = kind;
    }
    Time.prototype.getKind = function () {
        return this.kind;
    };
    Time.prototype.toSexp = function () {
        if (this.pipeline === null) {
            if (this.posix) {
                return "(time -p (command))";
            }
            else {
                return "(time (command))";
            }
        }
        if (this.posix) {
            return "(time -p " + this.pipeline.toSexp() + ")";
        }
        return "(time " + this.pipeline.toSexp() + ")";
    };
    return Time;
}());
var ConditionalExpr = /** @class */ (function () {
    function ConditionalExpr(body, redirects, kind) {
        if (body === void 0) { body = null; }
        if (redirects === void 0) { redirects = []; }
        if (kind === void 0) { kind = ""; }
        this.body = body;
        this.redirects = redirects !== null && redirects !== void 0 ? redirects : [];
        this.kind = kind;
    }
    ConditionalExpr.prototype.getKind = function () {
        return this.kind;
    };
    ConditionalExpr.prototype.toSexp = function () {
        var body = this.body;
        if (typeof body === 'string') {
            var escaped = body.replace(/\\/g, "\\\\").replace(/"/g, "\\\"").replace(/\n/g, "\\n");
            var result = "(cond \"" + escaped + "\")";
        }
        else {
            var result = "(cond " + body.toSexp() + ")";
        }
        if (this.redirects.length > 0) {
            var redirectParts = [];
            for (var _i = 0, _a = this.redirects; _i < _a.length; _i++) {
                var r = _a[_i];
                redirectParts.push(r.toSexp());
            }
            var redirectSexps = redirectParts.join(" ");
            return result + " " + redirectSexps;
        }
        return result;
    };
    return ConditionalExpr;
}());
var UnaryTest = /** @class */ (function () {
    function UnaryTest(op, operand, kind) {
        if (op === void 0) { op = ""; }
        if (operand === void 0) { operand = null; }
        if (kind === void 0) { kind = ""; }
        this.op = op;
        this.operand = operand;
        this.kind = kind;
    }
    UnaryTest.prototype.getKind = function () {
        return this.kind;
    };
    UnaryTest.prototype.toSexp = function () {
        var operandVal = this.operand.getCondFormattedValue();
        return "(cond-unary \"" + this.op + "\" (cond-term \"" + operandVal + "\"))";
    };
    return UnaryTest;
}());
var BinaryTest = /** @class */ (function () {
    function BinaryTest(op, left, right, kind) {
        if (op === void 0) { op = ""; }
        if (left === void 0) { left = null; }
        if (right === void 0) { right = null; }
        if (kind === void 0) { kind = ""; }
        this.op = op;
        this.left = left;
        this.right = right;
        this.kind = kind;
    }
    BinaryTest.prototype.getKind = function () {
        return this.kind;
    };
    BinaryTest.prototype.toSexp = function () {
        var leftVal = this.left.getCondFormattedValue();
        var rightVal = this.right.getCondFormattedValue();
        return "(cond-binary \"" + this.op + "\" (cond-term \"" + leftVal + "\") (cond-term \"" + rightVal + "\"))";
    };
    return BinaryTest;
}());
var CondAnd = /** @class */ (function () {
    function CondAnd(left, right, kind) {
        if (left === void 0) { left = null; }
        if (right === void 0) { right = null; }
        if (kind === void 0) { kind = ""; }
        this.left = left;
        this.right = right;
        this.kind = kind;
    }
    CondAnd.prototype.getKind = function () {
        return this.kind;
    };
    CondAnd.prototype.toSexp = function () {
        return "(cond-and " + this.left.toSexp() + " " + this.right.toSexp() + ")";
    };
    return CondAnd;
}());
var CondOr = /** @class */ (function () {
    function CondOr(left, right, kind) {
        if (left === void 0) { left = null; }
        if (right === void 0) { right = null; }
        if (kind === void 0) { kind = ""; }
        this.left = left;
        this.right = right;
        this.kind = kind;
    }
    CondOr.prototype.getKind = function () {
        return this.kind;
    };
    CondOr.prototype.toSexp = function () {
        return "(cond-or " + this.left.toSexp() + " " + this.right.toSexp() + ")";
    };
    return CondOr;
}());
var CondNot = /** @class */ (function () {
    function CondNot(operand, kind) {
        if (operand === void 0) { operand = null; }
        if (kind === void 0) { kind = ""; }
        this.operand = operand;
        this.kind = kind;
    }
    CondNot.prototype.getKind = function () {
        return this.kind;
    };
    CondNot.prototype.toSexp = function () {
        return this.operand.toSexp();
    };
    return CondNot;
}());
var CondParen = /** @class */ (function () {
    function CondParen(inner, kind) {
        if (inner === void 0) { inner = null; }
        if (kind === void 0) { kind = ""; }
        this.inner = inner;
        this.kind = kind;
    }
    CondParen.prototype.getKind = function () {
        return this.kind;
    };
    CondParen.prototype.toSexp = function () {
        return "(cond-expr " + this.inner.toSexp() + ")";
    };
    return CondParen;
}());
var ArrayName = /** @class */ (function () {
    function ArrayName(elements, kind) {
        if (elements === void 0) { elements = []; }
        if (kind === void 0) { kind = ""; }
        this.elements = elements !== null && elements !== void 0 ? elements : [];
        this.kind = kind;
    }
    ArrayName.prototype.getKind = function () {
        return this.kind;
    };
    ArrayName.prototype.toSexp = function () {
        if (!(this.elements.length > 0)) {
            return "(array)";
        }
        var parts = [];
        for (var _i = 0, _a = this.elements; _i < _a.length; _i++) {
            var e = _a[_i];
            parts.push(e.toSexp());
        }
        var inner = parts.join(" ");
        return "(array " + inner + ")";
    };
    return ArrayName;
}());
var Coproc = /** @class */ (function () {
    function Coproc(command, name, kind) {
        if (command === void 0) { command = null; }
        if (name === void 0) { name = ""; }
        if (kind === void 0) { kind = ""; }
        this.command = command;
        this.name = name;
        this.kind = kind;
    }
    Coproc.prototype.getKind = function () {
        return this.kind;
    };
    Coproc.prototype.toSexp = function () {
        if (this.name !== "") {
            var name = this.name;
        }
        else {
            var name = "COPROC";
        }
        return "(coproc \"" + name + "\" " + this.command.toSexp() + ")";
    };
    return Coproc;
}());
var Parser = /** @class */ (function () {
    function Parser(source, pos, length, PendingHeredocs, CmdsubHeredocEnd, SawNewlineInSingleQuote, InProcessSub, Extglob, Ctx, Lexer, TokenHistory, ParserState, DolbraceState, EofToken, WordContext, AtCommandStart, InArrayLiteral, InAssignBuiltin, ArithSrc, ArithPos, ArithLen) {
        if (source === void 0) { source = ""; }
        if (pos === void 0) { pos = 0; }
        if (length === void 0) { length = 0; }
        if (PendingHeredocs === void 0) { PendingHeredocs = []; }
        if (CmdsubHeredocEnd === void 0) { CmdsubHeredocEnd = 0; }
        if (SawNewlineInSingleQuote === void 0) { SawNewlineInSingleQuote = false; }
        if (InProcessSub === void 0) { InProcessSub = false; }
        if (Extglob === void 0) { Extglob = false; }
        if (Ctx === void 0) { Ctx = null; }
        if (Lexer === void 0) { Lexer = null; }
        if (TokenHistory === void 0) { TokenHistory = []; }
        if (ParserState === void 0) { ParserState = 0; }
        if (DolbraceState === void 0) { DolbraceState = 0; }
        if (EofToken === void 0) { EofToken = ""; }
        if (WordContext === void 0) { WordContext = 0; }
        if (AtCommandStart === void 0) { AtCommandStart = false; }
        if (InArrayLiteral === void 0) { InArrayLiteral = false; }
        if (InAssignBuiltin === void 0) { InAssignBuiltin = false; }
        if (ArithSrc === void 0) { ArithSrc = ""; }
        if (ArithPos === void 0) { ArithPos = 0; }
        if (ArithLen === void 0) { ArithLen = 0; }
        this.source = source;
        this.pos = pos;
        this.length = length;
        this.PendingHeredocs = PendingHeredocs !== null && PendingHeredocs !== void 0 ? PendingHeredocs : [];
        this.CmdsubHeredocEnd = CmdsubHeredocEnd;
        this.SawNewlineInSingleQuote = SawNewlineInSingleQuote;
        this.InProcessSub = InProcessSub;
        this.Extglob = Extglob;
        this.Ctx = Ctx;
        this.Lexer = Lexer;
        this.TokenHistory = TokenHistory !== null && TokenHistory !== void 0 ? TokenHistory : [];
        this.ParserState = ParserState;
        this.DolbraceState = DolbraceState;
        this.EofToken = EofToken;
        this.WordContext = WordContext;
        this.AtCommandStart = AtCommandStart;
        this.InArrayLiteral = InArrayLiteral;
        this.InAssignBuiltin = InAssignBuiltin;
        this.ArithSrc = ArithSrc;
        this.ArithPos = ArithPos;
        this.ArithLen = ArithLen;
    }
    Parser.prototype.SetState = function (flag) {
        this.ParserState = this.ParserState | flag;
    };
    Parser.prototype.ClearState = function (flag) {
        this.ParserState = this.ParserState & ~flag;
    };
    Parser.prototype.InState = function (flag) {
        return (this.ParserState & flag) !== 0;
    };
    Parser.prototype.SaveParserState = function () {
        return new SavedParserState(this.ParserState, this.DolbraceState, this.PendingHeredocs, this.Ctx.copyStack(), this.EofToken);
    };
    Parser.prototype.RestoreParserState = function (saved) {
        this.ParserState = saved.parserState;
        this.DolbraceState = saved.dolbraceState;
        this.EofToken = saved.eofToken;
        this.Ctx.restoreFrom(saved.ctxStack);
    };
    Parser.prototype.RecordToken = function (tok) {
        this.TokenHistory = [tok, this.TokenHistory[0], this.TokenHistory[1], this.TokenHistory[2]];
    };
    Parser.prototype.UpdateDolbraceForOp = function (op, hasParam) {
        if (this.DolbraceState === DolbraceState_NONE) {
            return;
        }
        if (op === "" || op.length === 0) {
            return;
        }
        var firstChar = op[0];
        if (this.DolbraceState === DolbraceState_PARAM && hasParam) {
            if ("%#^,".includes(firstChar)) {
                this.DolbraceState = DolbraceState_QUOTE;
                return;
            }
            if (firstChar === "/") {
                this.DolbraceState = DolbraceState_QUOTE2;
                return;
            }
        }
        if (this.DolbraceState === DolbraceState_PARAM) {
            if ("#%^,~:-=?+/".includes(firstChar)) {
                this.DolbraceState = DolbraceState_OP;
            }
        }
    };
    Parser.prototype.SyncLexer = function () {
        if (this.Lexer.TokenCache !== null) {
            if (this.Lexer.TokenCache.pos !== this.pos || this.Lexer.CachedWordContext !== this.WordContext || this.Lexer.CachedAtCommandStart !== this.AtCommandStart || this.Lexer.CachedInArrayLiteral !== this.InArrayLiteral || this.Lexer.CachedInAssignBuiltin !== this.InAssignBuiltin) {
                this.Lexer.TokenCache = null;
            }
        }
        if (this.Lexer.pos !== this.pos) {
            this.Lexer.pos = this.pos;
        }
        this.Lexer.EofToken = this.EofToken;
        this.Lexer.ParserState = this.ParserState;
        this.Lexer.LastReadToken = this.TokenHistory[0];
        this.Lexer.WordContext = this.WordContext;
        this.Lexer.AtCommandStart = this.AtCommandStart;
        this.Lexer.InArrayLiteral = this.InArrayLiteral;
        this.Lexer.InAssignBuiltin = this.InAssignBuiltin;
    };
    Parser.prototype.SyncParser = function () {
        this.pos = this.Lexer.pos;
    };
    Parser.prototype.LexPeekToken = function () {
        if (this.Lexer.TokenCache !== null && this.Lexer.TokenCache.pos === this.pos && this.Lexer.CachedWordContext === this.WordContext && this.Lexer.CachedAtCommandStart === this.AtCommandStart && this.Lexer.CachedInArrayLiteral === this.InArrayLiteral && this.Lexer.CachedInAssignBuiltin === this.InAssignBuiltin) {
            return this.Lexer.TokenCache;
        }
        var savedPos = this.pos;
        this.SyncLexer();
        var result = this.Lexer.peekToken();
        this.Lexer.CachedWordContext = this.WordContext;
        this.Lexer.CachedAtCommandStart = this.AtCommandStart;
        this.Lexer.CachedInArrayLiteral = this.InArrayLiteral;
        this.Lexer.CachedInAssignBuiltin = this.InAssignBuiltin;
        this.Lexer.PostReadPos = this.Lexer.pos;
        this.pos = savedPos;
        return result;
    };
    Parser.prototype.LexNextToken = function () {
        if (this.Lexer.TokenCache !== null && this.Lexer.TokenCache.pos === this.pos && this.Lexer.CachedWordContext === this.WordContext && this.Lexer.CachedAtCommandStart === this.AtCommandStart && this.Lexer.CachedInArrayLiteral === this.InArrayLiteral && this.Lexer.CachedInAssignBuiltin === this.InAssignBuiltin) {
            var tok = this.Lexer.nextToken();
            this.pos = this.Lexer.PostReadPos;
            this.Lexer.pos = this.Lexer.PostReadPos;
        }
        else {
            this.SyncLexer();
            var tok = this.Lexer.nextToken();
            this.Lexer.CachedWordContext = this.WordContext;
            this.Lexer.CachedAtCommandStart = this.AtCommandStart;
            this.Lexer.CachedInArrayLiteral = this.InArrayLiteral;
            this.Lexer.CachedInAssignBuiltin = this.InAssignBuiltin;
            this.SyncParser();
        }
        this.RecordToken(tok);
        return tok;
    };
    Parser.prototype.LexSkipBlanks = function () {
        this.SyncLexer();
        this.Lexer.skipBlanks();
        this.SyncParser();
    };
    Parser.prototype.LexSkipComment = function () {
        this.SyncLexer();
        var result = this.Lexer.SkipComment();
        this.SyncParser();
        return result;
    };
    Parser.prototype.LexIsCommandTerminator = function () {
        var tok = this.LexPeekToken();
        var t = tok.typeName;
        return t === TokenType_EOF || t === TokenType_NEWLINE || t === TokenType_PIPE || t === TokenType_SEMI || t === TokenType_LPAREN || t === TokenType_RPAREN || t === TokenType_AMP;
    };
    Parser.prototype.LexPeekOperator = function () {
        var tok = this.LexPeekToken();
        var t = tok.typeName;
        if (t >= TokenType_SEMI && t <= TokenType_GREATER || t >= TokenType_AND_AND && t <= TokenType_PIPE_AMP) {
            return [t, tok.value];
        }
        return [0, ""];
    };
    Parser.prototype.LexPeekReservedWord = function () {
        var tok = this.LexPeekToken();
        if (tok.typeName !== TokenType_WORD) {
            return "";
        }
        var word = tok.value;
        if (word.endsWith("\\\n")) {
            word = word.slice(0, word.length - 2);
        }
        if (RESERVED_WORDS.has(word) || (word === "{" || word === "}" || word === "[[" || word === "]]" || word === "!" || word === "time")) {
            return word;
        }
        return "";
    };
    Parser.prototype.LexIsAtReservedWord = function (word) {
        var reserved = this.LexPeekReservedWord();
        return reserved === word;
    };
    Parser.prototype.LexConsumeWord = function (expected) {
        var tok = this.LexPeekToken();
        if (tok.typeName !== TokenType_WORD) {
            return false;
        }
        var word = tok.value;
        if (word.endsWith("\\\n")) {
            word = word.slice(0, word.length - 2);
        }
        if (word === expected) {
            this.LexNextToken();
            return true;
        }
        return false;
    };
    Parser.prototype.LexPeekCaseTerminator = function () {
        var tok = this.LexPeekToken();
        var t = tok.typeName;
        if (t === TokenType_SEMI_SEMI) {
            return ";;";
        }
        if (t === TokenType_SEMI_AMP) {
            return ";&";
        }
        if (t === TokenType_SEMI_SEMI_AMP) {
            return ";;&";
        }
        return "";
    };
    Parser.prototype.atEnd = function () {
        return this.pos >= this.length;
    };
    Parser.prototype.peek = function () {
        if (this.atEnd()) {
            return "";
        }
        return this.source[this.pos];
    };
    Parser.prototype.advance = function () {
        if (this.atEnd()) {
            return "";
        }
        var ch = this.source[this.pos];
        this.pos += 1;
        return ch;
    };
    Parser.prototype.peekAt = function (offset) {
        var pos = this.pos + offset;
        if (pos < 0 || pos >= this.length) {
            return "";
        }
        return this.source[pos];
    };
    Parser.prototype.lookahead = function (n) {
        return Substring(this.source, this.pos, this.pos + n);
    };
    Parser.prototype.IsBangFollowedByProcsub = function () {
        if (this.pos + 2 >= this.length) {
            return false;
        }
        var nextChar = this.source[this.pos + 1];
        if (nextChar !== ">" && nextChar !== "<") {
            return false;
        }
        return this.source[this.pos + 2] === "(";
    };
    Parser.prototype.skipWhitespace = function () {
        while (!this.atEnd()) {
            this.LexSkipBlanks();
            if (this.atEnd()) {
                break;
            }
            var ch = this.peek();
            if (ch === "#") {
                this.LexSkipComment();
            }
            else {
                if (ch === "\\" && this.peekAt(1) === "\n") {
                    this.advance();
                    this.advance();
                }
                else {
                    break;
                }
            }
        }
    };
    Parser.prototype.skipWhitespaceAndNewlines = function () {
        while (!this.atEnd()) {
            var ch = this.peek();
            if (IsWhitespace(ch)) {
                this.advance();
                if (ch === "\n") {
                    this.GatherHeredocBodies();
                    if (this.CmdsubHeredocEnd !== -1 && this.CmdsubHeredocEnd > this.pos) {
                        this.pos = this.CmdsubHeredocEnd;
                        this.CmdsubHeredocEnd = -1;
                    }
                }
            }
            else {
                if (ch === "#") {
                    while (!this.atEnd() && this.peek() !== "\n") {
                        this.advance();
                    }
                }
                else {
                    if (ch === "\\" && this.peekAt(1) === "\n") {
                        this.advance();
                        this.advance();
                    }
                    else {
                        break;
                    }
                }
            }
        }
    };
    Parser.prototype.AtListTerminatingBracket = function () {
        if (this.atEnd()) {
            return false;
        }
        var ch = this.peek();
        if (this.EofToken !== "" && ch === this.EofToken) {
            return true;
        }
        if (ch === ")") {
            return true;
        }
        if (ch === "}") {
            var nextPos = this.pos + 1;
            if (nextPos >= this.length) {
                return true;
            }
            return IsWordEndContext(this.source[nextPos]);
        }
        return false;
    };
    Parser.prototype.AtEofToken = function () {
        if (this.EofToken === "") {
            return false;
        }
        var tok = this.LexPeekToken();
        if (this.EofToken === ")") {
            return tok.typeName === TokenType_RPAREN;
        }
        if (this.EofToken === "}") {
            return tok.typeName === TokenType_WORD && tok.value === "}";
        }
        return false;
    };
    Parser.prototype.CollectRedirects = function () {
        var redirects = [];
        while (true) {
            this.skipWhitespace();
            var redirect = this.parseRedirect();
            if (redirect === null) {
                break;
            }
            redirects.push(redirect);
        }
        return redirects.length > 0 ? redirects : null;
    };
    Parser.prototype.ParseLoopBody = function (context) {
        if (this.peek() === "{") {
            var brace = this.parseBraceGroup();
            if (brace === null) {
                throw new Error("".concat("Expected brace group body in ".concat(context), " at position ").concat(this.LexPeekToken().pos));
            }
            return brace.body;
        }
        if (this.LexConsumeWord("do")) {
            var body = this.parseListUntil(new Set(["done"]));
            if (body === null) {
                throw new Error("".concat("Expected commands after 'do'", " at position ").concat(this.LexPeekToken().pos));
            }
            this.skipWhitespaceAndNewlines();
            if (!this.LexConsumeWord("done")) {
                throw new Error("".concat("Expected 'done' to close ".concat(context), " at position ").concat(this.LexPeekToken().pos));
            }
            return body;
        }
        throw new Error("".concat("Expected 'do' or '{' in ".concat(context), " at position ").concat(this.LexPeekToken().pos));
    };
    Parser.prototype.peekWord = function () {
        var savedPos = this.pos;
        this.skipWhitespace();
        if (this.atEnd() || IsMetachar(this.peek())) {
            this.pos = savedPos;
            return "";
        }
        var chars = [];
        while (!this.atEnd() && !IsMetachar(this.peek())) {
            var ch = this.peek();
            if (IsQuote(ch)) {
                break;
            }
            if (ch === "\\" && this.pos + 1 < this.length && this.source[this.pos + 1] === "\n") {
                break;
            }
            if (ch === "\\" && this.pos + 1 < this.length) {
                chars.push(this.advance());
                chars.push(this.advance());
                continue;
            }
            chars.push(this.advance());
        }
        if (chars.length > 0) {
            var word = chars.join("");
        }
        else {
            var word = "";
        }
        this.pos = savedPos;
        return word;
    };
    Parser.prototype.consumeWord = function (expected) {
        var savedPos = this.pos;
        this.skipWhitespace();
        var word = this.peekWord();
        var keywordWord = word;
        var hasLeadingBrace = false;
        if (word !== "" && this.InProcessSub && word.length > 1 && word[0] === "}") {
            keywordWord = word.slice(1);
            hasLeadingBrace = true;
        }
        if (keywordWord !== expected) {
            this.pos = savedPos;
            return false;
        }
        this.skipWhitespace();
        if (hasLeadingBrace) {
            this.advance();
        }
        for (var _i = 0, expected_1 = expected; _i < expected_1.length; _i++) {
            var _ = expected_1[_i];
            this.advance();
        }
        while (this.peek() === "\\" && this.pos + 1 < this.length && this.source[this.pos + 1] === "\n") {
            this.advance();
            this.advance();
        }
        return true;
    };
    Parser.prototype.IsWordTerminator = function (ctx, ch, bracketDepth, parenDepth) {
        this.SyncLexer();
        return this.Lexer.IsWordTerminator(ctx, ch, bracketDepth, parenDepth);
    };
    Parser.prototype.ScanDoubleQuote = function (chars, parts, start, handleLineContinuation) {
        chars.push("\"");
        while (!this.atEnd() && this.peek() !== "\"") {
            var c = this.peek();
            if (c === "\\" && this.pos + 1 < this.length) {
                var nextC = this.source[this.pos + 1];
                if (handleLineContinuation && nextC === "\n") {
                    this.advance();
                    this.advance();
                }
                else {
                    chars.push(this.advance());
                    chars.push(this.advance());
                }
            }
            else {
                if (c === "$") {
                    if (!this.ParseDollarExpansion(chars, parts, true)) {
                        chars.push(this.advance());
                    }
                }
                else {
                    chars.push(this.advance());
                }
            }
        }
        if (this.atEnd()) {
            throw new Error("".concat("Unterminated double quote", " at position ").concat(start));
        }
        chars.push(this.advance());
    };
    Parser.prototype.ParseDollarExpansion = function (chars, parts, inDquote) {
        var _a;
        if (this.pos + 2 < this.length && this.source[this.pos + 1] === "(" && this.source[this.pos + 2] === "(") {
            var _b = this.ParseArithmeticExpansion(), result0 = _b[0], result1 = _b[1];
            if (result0 !== null) {
                parts.push(result0);
                chars.push(result1);
                return true;
            }
            _a = this.ParseCommandSubstitution(), result0 = _a[0], result1 = _a[1];
            if (result0 !== null) {
                parts.push(result0);
                chars.push(result1);
                return true;
            }
            return false;
        }
        if (this.pos + 1 < this.length && this.source[this.pos + 1] === "[") {
            var _c = this.ParseDeprecatedArithmetic(), result0 = _c[0], result1 = _c[1];
            if (result0 !== null) {
                parts.push(result0);
                chars.push(result1);
                return true;
            }
            return false;
        }
        if (this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
            var _d = this.ParseCommandSubstitution(), result0 = _d[0], result1 = _d[1];
            if (result0 !== null) {
                parts.push(result0);
                chars.push(result1);
                return true;
            }
            return false;
        }
        var _f = this.ParseParamExpansion(inDquote), result0 = _f[0], result1 = _f[1];
        if (result0 !== null) {
            parts.push(result0);
            chars.push(result1);
            return true;
        }
        return false;
    };
    Parser.prototype.ParseWordInternal = function (ctx, atCommandStart, inArrayLiteral) {
        this.WordContext = ctx;
        return this.parseWord(atCommandStart, inArrayLiteral, false);
    };
    Parser.prototype.parseWord = function (atCommandStart, inArrayLiteral, inAssignBuiltin) {
        this.skipWhitespace();
        if (this.atEnd()) {
            return null;
        }
        this.AtCommandStart = atCommandStart;
        this.InArrayLiteral = inArrayLiteral;
        this.InAssignBuiltin = inAssignBuiltin;
        var tok = this.LexPeekToken();
        if (tok.typeName !== TokenType_WORD) {
            this.AtCommandStart = false;
            this.InArrayLiteral = false;
            this.InAssignBuiltin = false;
            return null;
        }
        this.LexNextToken();
        this.AtCommandStart = false;
        this.InArrayLiteral = false;
        this.InAssignBuiltin = false;
        return tok.word;
    };
    Parser.prototype.ParseCommandSubstitution = function () {
        if (this.atEnd() || this.peek() !== "$") {
            return [null, ""];
        }
        var start = this.pos;
        this.advance();
        if (this.atEnd() || this.peek() !== "(") {
            this.pos = start;
            return [null, ""];
        }
        this.advance();
        var saved = this.SaveParserState();
        this.SetState(ParserStateFlags_PST_CMDSUBST | ParserStateFlags_PST_EOFTOKEN);
        this.EofToken = ")";
        var cmd = this.parseList(true);
        if (cmd === null) {
            cmd = new Empty("empty");
        }
        this.skipWhitespaceAndNewlines();
        if (this.atEnd() || this.peek() !== ")") {
            this.RestoreParserState(saved);
            this.pos = start;
            return [null, ""];
        }
        this.advance();
        var textEnd = this.pos;
        var text = Substring(this.source, start, textEnd);
        this.RestoreParserState(saved);
        return [new CommandSubstitution(cmd, [], "cmdsub"), text];
    };
    Parser.prototype.ParseFunsub = function (start) {
        this.SyncParser();
        if (!this.atEnd() && this.peek() === "|") {
            this.advance();
        }
        var saved = this.SaveParserState();
        this.SetState(ParserStateFlags_PST_CMDSUBST | ParserStateFlags_PST_EOFTOKEN);
        this.EofToken = "}";
        var cmd = this.parseList(true);
        if (cmd === null) {
            cmd = new Empty("empty");
        }
        this.skipWhitespaceAndNewlines();
        if (this.atEnd() || this.peek() !== "}") {
            this.RestoreParserState(saved);
            throw new Error("".concat("unexpected EOF looking for `}'", " at position ").concat(start));
        }
        this.advance();
        var text = Substring(this.source, start, this.pos);
        this.RestoreParserState(saved);
        this.SyncLexer();
        return [new CommandSubstitution(cmd, true, "cmdsub"), text];
    };
    Parser.prototype.IsAssignmentWord = function (word) {
        return Assignment(word.value, 0) !== -1;
    };
    Parser.prototype.ParseBacktickSubstitution = function () {
        if (this.atEnd() || this.peek() !== "`") {
            return [null, ""];
        }
        var start = this.pos;
        this.advance();
        var contentChars = [];
        var textChars = ["`"];
        var pendingHeredocs = [];
        var inHeredocBody = false;
        var currentHeredocDelim = "";
        var currentHeredocStrip = false;
        while (!this.atEnd() && (inHeredocBody || this.peek() !== "`")) {
            if (inHeredocBody) {
                var lineStart = this.pos;
                var lineEnd = lineStart;
                while (lineEnd < this.length && this.source[lineEnd] !== "\n") {
                    lineEnd += 1;
                }
                var line = Substring(this.source, lineStart, lineEnd);
                var checkLine = currentHeredocStrip ? line.replace(/^[\t]+/, '') : line;
                if (checkLine === currentHeredocDelim) {
                    for (var _i = 0, line_1 = line; _i < line_1.length; _i++) {
                        var ch_1 = line_1[_i];
                        contentChars.push(ch_1);
                        textChars.push(ch_1);
                    }
                    this.pos = lineEnd;
                    if (this.pos < this.length && this.source[this.pos] === "\n") {
                        contentChars.push("\n");
                        textChars.push("\n");
                        this.advance();
                    }
                    inHeredocBody = false;
                    if (pendingHeredocs.length > 0) {
                        {
                            var Entry = pendingHeredocs[pendingHeredocs.length - 1];
                            pendingHeredocs = pendingHeredocs.slice(0, pendingHeredocs.length - 1);
                            currentHeredocDelim = Entry[0];
                            currentHeredocStrip = Entry[1];
                        }
                        inHeredocBody = true;
                    }
                }
                else {
                    if (checkLine.startsWith(currentHeredocDelim) && checkLine.length > currentHeredocDelim.length) {
                        var tabsStripped = line.length - checkLine.length;
                        var endPos = tabsStripped + currentHeredocDelim.length;
                        for (var _a = 0, _b = range(endPos); _a < _b.length; _a++) {
                            var i = _b[_a];
                            contentChars.push(line[i]);
                            textChars.push(line[i]);
                        }
                        this.pos = lineStart + endPos;
                        inHeredocBody = false;
                        if (pendingHeredocs.length > 0) {
                            {
                                var Entry = pendingHeredocs[pendingHeredocs.length - 1];
                                pendingHeredocs = pendingHeredocs.slice(0, pendingHeredocs.length - 1);
                                currentHeredocDelim = Entry[0];
                                currentHeredocStrip = Entry[1];
                            }
                            inHeredocBody = true;
                        }
                    }
                    else {
                        for (var _c = 0, line_2 = line; _c < line_2.length; _c++) {
                            var ch_2 = line_2[_c];
                            contentChars.push(ch_2);
                            textChars.push(ch_2);
                        }
                        this.pos = lineEnd;
                        if (this.pos < this.length && this.source[this.pos] === "\n") {
                            contentChars.push("\n");
                            textChars.push("\n");
                            this.advance();
                        }
                    }
                }
                continue;
            }
            var c = this.peek();
            if (c === "\\" && this.pos + 1 < this.length) {
                var nextC = this.source[this.pos + 1];
                if (nextC === "\n") {
                    this.advance();
                    this.advance();
                }
                else {
                    if (IsEscapeCharInBacktick(nextC)) {
                        this.advance();
                        var escaped = this.advance();
                        contentChars.push(escaped);
                        textChars.push("\\");
                        textChars.push(escaped);
                    }
                    else {
                        var ch = this.advance();
                        contentChars.push(ch);
                        textChars.push(ch);
                    }
                }
                continue;
            }
            if (c === "<" && this.pos + 1 < this.length && this.source[this.pos + 1] === "<") {
                if (this.pos + 2 < this.length && this.source[this.pos + 2] === "<") {
                    contentChars.push(this.advance());
                    textChars.push("<");
                    contentChars.push(this.advance());
                    textChars.push("<");
                    contentChars.push(this.advance());
                    textChars.push("<");
                    while (!this.atEnd() && IsWhitespaceNoNewline(this.peek())) {
                        var ch = this.advance();
                        contentChars.push(ch);
                        textChars.push(ch);
                    }
                    while (!this.atEnd() && !IsWhitespace(this.peek()) && !"()".includes(this.peek())) {
                        if (this.peek() === "\\" && this.pos + 1 < this.length) {
                            ch = this.advance();
                            contentChars.push(ch);
                            textChars.push(ch);
                            ch = this.advance();
                            contentChars.push(ch);
                            textChars.push(ch);
                        }
                        else {
                            if ("\"'".includes(this.peek())) {
                                var quote = this.peek();
                                ch = this.advance();
                                contentChars.push(ch);
                                textChars.push(ch);
                                while (!this.atEnd() && this.peek() !== quote) {
                                    if (quote === "\"" && this.peek() === "\\") {
                                        ch = this.advance();
                                        contentChars.push(ch);
                                        textChars.push(ch);
                                    }
                                    ch = this.advance();
                                    contentChars.push(ch);
                                    textChars.push(ch);
                                }
                                if (!this.atEnd()) {
                                    ch = this.advance();
                                    contentChars.push(ch);
                                    textChars.push(ch);
                                }
                            }
                            else {
                                ch = this.advance();
                                contentChars.push(ch);
                                textChars.push(ch);
                            }
                        }
                    }
                    continue;
                }
                contentChars.push(this.advance());
                textChars.push("<");
                contentChars.push(this.advance());
                textChars.push("<");
                var stripTabs = false;
                if (!this.atEnd() && this.peek() === "-") {
                    stripTabs = true;
                    contentChars.push(this.advance());
                    textChars.push("-");
                }
                while (!this.atEnd() && IsWhitespaceNoNewline(this.peek())) {
                    var ch = this.advance();
                    contentChars.push(ch);
                    textChars.push(ch);
                }
                var delimiterChars = [];
                if (!this.atEnd()) {
                    ch = this.peek();
                    if (IsQuote(ch)) {
                        var quote = this.advance();
                        contentChars.push(quote);
                        textChars.push(quote);
                        while (!this.atEnd() && this.peek() !== quote) {
                            var dch = this.advance();
                            contentChars.push(dch);
                            textChars.push(dch);
                            delimiterChars.push(dch);
                        }
                        if (!this.atEnd()) {
                            var closing = this.advance();
                            contentChars.push(closing);
                            textChars.push(closing);
                        }
                    }
                    else {
                        if (ch === "\\") {
                            var esc = this.advance();
                            contentChars.push(esc);
                            textChars.push(esc);
                            if (!this.atEnd()) {
                                var dch = this.advance();
                                contentChars.push(dch);
                                textChars.push(dch);
                                delimiterChars.push(dch);
                            }
                            while (!this.atEnd() && !IsMetachar(this.peek())) {
                                var dch = this.advance();
                                contentChars.push(dch);
                                textChars.push(dch);
                                delimiterChars.push(dch);
                            }
                        }
                        else {
                            while (!this.atEnd() && !IsMetachar(this.peek()) && this.peek() !== "`") {
                                ch = this.peek();
                                if (IsQuote(ch)) {
                                    var quote = this.advance();
                                    contentChars.push(quote);
                                    textChars.push(quote);
                                    while (!this.atEnd() && this.peek() !== quote) {
                                        var dch = this.advance();
                                        contentChars.push(dch);
                                        textChars.push(dch);
                                        delimiterChars.push(dch);
                                    }
                                    if (!this.atEnd()) {
                                        var closing = this.advance();
                                        contentChars.push(closing);
                                        textChars.push(closing);
                                    }
                                }
                                else {
                                    if (ch === "\\") {
                                        var esc = this.advance();
                                        contentChars.push(esc);
                                        textChars.push(esc);
                                        if (!this.atEnd()) {
                                            var dch = this.advance();
                                            contentChars.push(dch);
                                            textChars.push(dch);
                                            delimiterChars.push(dch);
                                        }
                                    }
                                    else {
                                        var dch = this.advance();
                                        contentChars.push(dch);
                                        textChars.push(dch);
                                        delimiterChars.push(dch);
                                    }
                                }
                            }
                        }
                    }
                }
                var delimiter = delimiterChars.join("");
                if (delimiter !== "") {
                    pendingHeredocs.push([delimiter, stripTabs]);
                }
                continue;
            }
            if (c === "\n") {
                var ch = this.advance();
                contentChars.push(ch);
                textChars.push(ch);
                if (pendingHeredocs.length > 0) {
                    {
                        var Entry = pendingHeredocs[pendingHeredocs.length - 1];
                        pendingHeredocs = pendingHeredocs.slice(0, pendingHeredocs.length - 1);
                        currentHeredocDelim = Entry[0];
                        currentHeredocStrip = Entry[1];
                    }
                    inHeredocBody = true;
                }
                continue;
            }
            var ch = this.advance();
            contentChars.push(ch);
            textChars.push(ch);
        }
        if (this.atEnd()) {
            throw new Error("".concat("Unterminated backtick", " at position ").concat(start));
        }
        this.advance();
        textChars.push("`");
        var text = textChars.join("");
        var content = contentChars.join("");
        if (pendingHeredocs.length > 0) {
            var _d = FindHeredocContentEnd(this.source, this.pos, pendingHeredocs), heredocStart = _d[0], heredocEnd = _d[1];
            if (heredocEnd > heredocStart) {
                content = content + Substring(this.source, heredocStart, heredocEnd);
                if (this.CmdsubHeredocEnd === -1) {
                    this.CmdsubHeredocEnd = heredocEnd;
                }
                else {
                    this.CmdsubHeredocEnd = this.CmdsubHeredocEnd > heredocEnd ? this.CmdsubHeredocEnd : heredocEnd;
                }
            }
        }
        var subParser = newParser(content, false, this.Extglob);
        var cmd = subParser.parseList(true);
        if (cmd === null) {
            cmd = new Empty("empty");
        }
        return [new CommandSubstitution(cmd, [], "cmdsub"), text];
    };
    Parser.prototype.ParseProcessSubstitution = function () {
        if (this.atEnd() || !IsRedirectChar(this.peek())) {
            return [null, ""];
        }
        var start = this.pos;
        var direction = this.advance();
        if (this.atEnd() || this.peek() !== "(") {
            this.pos = start;
            return [null, ""];
        }
        this.advance();
        var saved = this.SaveParserState();
        var oldInProcessSub = this.InProcessSub;
        this.InProcessSub = true;
        this.SetState(ParserStateFlags_PST_EOFTOKEN);
        this.EofToken = ")";
        try {
            var cmd = this.parseList(true);
            if (cmd === null) {
                cmd = new Empty("empty");
            }
            this.skipWhitespaceAndNewlines();
            if (this.atEnd() || this.peek() !== ")") {
                throw new Error("".concat("Invalid process substitution", " at position ").concat(start));
            }
            this.advance();
            var textEnd = this.pos;
            var text = Substring(this.source, start, textEnd);
            text = StripLineContinuationsCommentAware(text);
            this.RestoreParserState(saved);
            this.InProcessSub = oldInProcessSub;
            return [new ProcessSubstitution(direction, cmd, "procsub"), text];
        }
        catch (e) {
            this.RestoreParserState(saved);
            this.InProcessSub = oldInProcessSub;
            var contentStartChar = start + 2 < this.length ? this.source[start + 2] : "";
            if (" \t\n".includes(contentStartChar)) {
                throw new Error("".concat("", " at position ").concat(0));
            }
            this.pos = start + 2;
            this.Lexer.pos = this.pos;
            this.Lexer.ParseMatchedPair("(", ")", 0, false);
            this.pos = this.Lexer.pos;
            var text = Substring(this.source, start, this.pos);
            text = StripLineContinuationsCommentAware(text);
            return [null, text];
        }
    };
    Parser.prototype.ParseArrayLiteral = function () {
        if (this.atEnd() || this.peek() !== "(") {
            return [null, ""];
        }
        var start = this.pos;
        this.advance();
        this.SetState(ParserStateFlags_PST_COMPASSIGN);
        var elements = [];
        while (true) {
            this.skipWhitespaceAndNewlines();
            if (this.atEnd()) {
                this.ClearState(ParserStateFlags_PST_COMPASSIGN);
                throw new Error("".concat("Unterminated array literal", " at position ").concat(start));
            }
            if (this.peek() === ")") {
                break;
            }
            var word = this.parseWord(false, true, false);
            if (word === null) {
                if (this.peek() === ")") {
                    break;
                }
                this.ClearState(ParserStateFlags_PST_COMPASSIGN);
                throw new Error("".concat("Expected word in array literal", " at position ").concat(this.pos));
            }
            elements.push(word);
        }
        if (this.atEnd() || this.peek() !== ")") {
            this.ClearState(ParserStateFlags_PST_COMPASSIGN);
            throw new Error("".concat("Expected ) to close array literal", " at position ").concat(this.pos));
        }
        this.advance();
        var text = Substring(this.source, start, this.pos);
        this.ClearState(ParserStateFlags_PST_COMPASSIGN);
        return [new ArrayName(elements, "array"), text];
    };
    Parser.prototype.ParseArithmeticExpansion = function () {
        if (this.atEnd() || this.peek() !== "$") {
            return [null, ""];
        }
        var start = this.pos;
        if (this.pos + 2 >= this.length || this.source[this.pos + 1] !== "(" || this.source[this.pos + 2] !== "(") {
            return [null, ""];
        }
        this.advance();
        this.advance();
        this.advance();
        var contentStart = this.pos;
        var depth = 2;
        var firstClosePos = -1;
        while (!this.atEnd() && depth > 0) {
            var c = this.peek();
            if (c === "'") {
                this.advance();
                while (!this.atEnd() && this.peek() !== "'") {
                    this.advance();
                }
                if (!this.atEnd()) {
                    this.advance();
                }
            }
            else {
                if (c === "\"") {
                    this.advance();
                    while (!this.atEnd()) {
                        if (this.peek() === "\\" && this.pos + 1 < this.length) {
                            this.advance();
                            this.advance();
                        }
                        else {
                            if (this.peek() === "\"") {
                                this.advance();
                                break;
                            }
                            else {
                                this.advance();
                            }
                        }
                    }
                }
                else {
                    if (c === "\\" && this.pos + 1 < this.length) {
                        this.advance();
                        this.advance();
                    }
                    else {
                        if (c === "(") {
                            depth += 1;
                            this.advance();
                        }
                        else {
                            if (c === ")") {
                                if (depth === 2) {
                                    firstClosePos = this.pos;
                                }
                                depth -= 1;
                                if (depth === 0) {
                                    break;
                                }
                                this.advance();
                            }
                            else {
                                if (depth === 1) {
                                    firstClosePos = -1;
                                }
                                this.advance();
                            }
                        }
                    }
                }
            }
        }
        if (depth !== 0) {
            if (this.atEnd()) {
                throw new Error("".concat("unexpected EOF looking for `))'", " at position ").concat(start));
            }
            this.pos = start;
            return [null, ""];
        }
        if (firstClosePos !== -1) {
            var content = Substring(this.source, contentStart, firstClosePos);
        }
        else {
            var content = Substring(this.source, contentStart, this.pos);
        }
        this.advance();
        var text = Substring(this.source, start, this.pos);
        try {
            var expr = this.ParseArithExpr(content);
        }
        catch (_e) {
            this.pos = start;
            return [null, ""];
        }
        return [new ArithmeticExpansion(expr, "arith"), text];
    };
    Parser.prototype.ParseArithExpr = function (content) {
        var savedArithSrc = this.ArithSrc;
        var savedArithPos = this.ArithPos;
        var savedArithLen = this.ArithLen;
        var savedParserState = this.ParserState;
        this.SetState(ParserStateFlags_PST_ARITH);
        this.ArithSrc = content;
        this.ArithPos = 0;
        this.ArithLen = content.length;
        this.ArithSkipWs();
        if (this.ArithAtEnd()) {
            var result = null;
        }
        else {
            var result = this.ArithParseComma();
        }
        this.ParserState = savedParserState;
        if (savedArithSrc !== "") {
            this.ArithSrc = savedArithSrc;
            this.ArithPos = savedArithPos;
            this.ArithLen = savedArithLen;
        }
        return result;
    };
    Parser.prototype.ArithAtEnd = function () {
        return this.ArithPos >= this.ArithLen;
    };
    Parser.prototype.ArithPeek = function (offset) {
        var pos = this.ArithPos + offset;
        if (pos >= this.ArithLen) {
            return "";
        }
        return this.ArithSrc[pos];
    };
    Parser.prototype.ArithAdvance = function () {
        if (this.ArithAtEnd()) {
            return "";
        }
        var c = this.ArithSrc[this.ArithPos];
        this.ArithPos += 1;
        return c;
    };
    Parser.prototype.ArithSkipWs = function () {
        while (!this.ArithAtEnd()) {
            var c = this.ArithSrc[this.ArithPos];
            if (IsWhitespace(c)) {
                this.ArithPos += 1;
            }
            else {
                if (c === "\\" && this.ArithPos + 1 < this.ArithLen && this.ArithSrc[this.ArithPos + 1] === "\n") {
                    this.ArithPos += 2;
                }
                else {
                    break;
                }
            }
        }
    };
    Parser.prototype.ArithMatch = function (s) {
        return StartsWithAt(this.ArithSrc, this.ArithPos, s);
    };
    Parser.prototype.ArithConsume = function (s) {
        if (this.ArithMatch(s)) {
            this.ArithPos += s.length;
            return true;
        }
        return false;
    };
    Parser.prototype.ArithParseComma = function () {
        var left = this.ArithParseAssign();
        while (true) {
            this.ArithSkipWs();
            if (this.ArithConsume(",")) {
                this.ArithSkipWs();
                var right = this.ArithParseAssign();
                left = new ArithComma(left, right, "comma");
            }
            else {
                break;
            }
        }
        return left;
    };
    Parser.prototype.ArithParseAssign = function () {
        var left = this.ArithParseTernary();
        this.ArithSkipWs();
        var assignOps = ["<<=", ">>=", "+=", "-=", "*=", "/=", "%=", "&=", "^=", "|=", "="];
        for (var _i = 0, assignOps_1 = assignOps; _i < assignOps_1.length; _i++) {
            var op = assignOps_1[_i];
            if (this.ArithMatch(op)) {
                if (op === "=" && this.ArithPeek(1) === "=") {
                    break;
                }
                this.ArithConsume(op);
                this.ArithSkipWs();
                var right = this.ArithParseAssign();
                return new ArithAssign(op, left, right, "assign");
            }
        }
        return left;
    };
    Parser.prototype.ArithParseTernary = function () {
        var cond = this.ArithParseLogicalOr();
        this.ArithSkipWs();
        if (this.ArithConsume("?")) {
            this.ArithSkipWs();
            if (this.ArithMatch(":")) {
                var ifTrue = null;
            }
            else {
                var ifTrue = this.ArithParseAssign();
            }
            this.ArithSkipWs();
            if (this.ArithConsume(":")) {
                this.ArithSkipWs();
                if (this.ArithAtEnd() || this.ArithPeek(0) === ")") {
                    var ifFalse = null;
                }
                else {
                    var ifFalse = this.ArithParseTernary();
                }
            }
            else {
                var ifFalse = null;
            }
            return new ArithTernary(cond, ifTrue, ifFalse, "ternary");
        }
        return cond;
    };
    Parser.prototype.ArithParseLeftAssoc = function (ops, parsefn) {
        var left = parsefn();
        while (true) {
            this.ArithSkipWs();
            var matched = false;
            for (var _i = 0, ops_1 = ops; _i < ops_1.length; _i++) {
                var op = ops_1[_i];
                if (this.ArithMatch(op)) {
                    this.ArithConsume(op);
                    this.ArithSkipWs();
                    left = new ArithBinaryOp(op, left, parsefn(), "binary-op");
                    matched = true;
                    break;
                }
            }
            if (!matched) {
                break;
            }
        }
        return left;
    };
    Parser.prototype.ArithParseLogicalOr = function () {
        return this.ArithParseLeftAssoc(["||"], this.ArithParseLogicalAnd.bind(this));
    };
    Parser.prototype.ArithParseLogicalAnd = function () {
        return this.ArithParseLeftAssoc(["&&"], this.ArithParseBitwiseOr.bind(this));
    };
    Parser.prototype.ArithParseBitwiseOr = function () {
        var left = this.ArithParseBitwiseXor();
        while (true) {
            this.ArithSkipWs();
            if (this.ArithPeek(0) === "|" && (this.ArithPeek(1) !== "|" && this.ArithPeek(1) !== "=")) {
                this.ArithAdvance();
                this.ArithSkipWs();
                var right = this.ArithParseBitwiseXor();
                left = new ArithBinaryOp("|", left, right, "binary-op");
            }
            else {
                break;
            }
        }
        return left;
    };
    Parser.prototype.ArithParseBitwiseXor = function () {
        var left = this.ArithParseBitwiseAnd();
        while (true) {
            this.ArithSkipWs();
            if (this.ArithPeek(0) === "^" && this.ArithPeek(1) !== "=") {
                this.ArithAdvance();
                this.ArithSkipWs();
                var right = this.ArithParseBitwiseAnd();
                left = new ArithBinaryOp("^", left, right, "binary-op");
            }
            else {
                break;
            }
        }
        return left;
    };
    Parser.prototype.ArithParseBitwiseAnd = function () {
        var left = this.ArithParseEquality();
        while (true) {
            this.ArithSkipWs();
            if (this.ArithPeek(0) === "&" && (this.ArithPeek(1) !== "&" && this.ArithPeek(1) !== "=")) {
                this.ArithAdvance();
                this.ArithSkipWs();
                var right = this.ArithParseEquality();
                left = new ArithBinaryOp("&", left, right, "binary-op");
            }
            else {
                break;
            }
        }
        return left;
    };
    Parser.prototype.ArithParseEquality = function () {
        return this.ArithParseLeftAssoc(["==", "!="], this.ArithParseComparison.bind(this));
    };
    Parser.prototype.ArithParseComparison = function () {
        var left = this.ArithParseShift();
        while (true) {
            this.ArithSkipWs();
            if (this.ArithMatch("<=")) {
                this.ArithConsume("<=");
                this.ArithSkipWs();
                var right = this.ArithParseShift();
                left = new ArithBinaryOp("<=", left, right, "binary-op");
            }
            else {
                if (this.ArithMatch(">=")) {
                    this.ArithConsume(">=");
                    this.ArithSkipWs();
                    var right = this.ArithParseShift();
                    left = new ArithBinaryOp(">=", left, right, "binary-op");
                }
                else {
                    if (this.ArithPeek(0) === "<" && (this.ArithPeek(1) !== "<" && this.ArithPeek(1) !== "=")) {
                        this.ArithAdvance();
                        this.ArithSkipWs();
                        var right = this.ArithParseShift();
                        left = new ArithBinaryOp("<", left, right, "binary-op");
                    }
                    else {
                        if (this.ArithPeek(0) === ">" && (this.ArithPeek(1) !== ">" && this.ArithPeek(1) !== "=")) {
                            this.ArithAdvance();
                            this.ArithSkipWs();
                            var right = this.ArithParseShift();
                            left = new ArithBinaryOp(">", left, right, "binary-op");
                        }
                        else {
                            break;
                        }
                    }
                }
            }
        }
        return left;
    };
    Parser.prototype.ArithParseShift = function () {
        var left = this.ArithParseAdditive();
        while (true) {
            this.ArithSkipWs();
            if (this.ArithMatch("<<=")) {
                break;
            }
            if (this.ArithMatch(">>=")) {
                break;
            }
            if (this.ArithMatch("<<")) {
                this.ArithConsume("<<");
                this.ArithSkipWs();
                var right = this.ArithParseAdditive();
                left = new ArithBinaryOp("<<", left, right, "binary-op");
            }
            else {
                if (this.ArithMatch(">>")) {
                    this.ArithConsume(">>");
                    this.ArithSkipWs();
                    var right = this.ArithParseAdditive();
                    left = new ArithBinaryOp(">>", left, right, "binary-op");
                }
                else {
                    break;
                }
            }
        }
        return left;
    };
    Parser.prototype.ArithParseAdditive = function () {
        var left = this.ArithParseMultiplicative();
        while (true) {
            this.ArithSkipWs();
            var c = this.ArithPeek(0);
            var c2 = this.ArithPeek(1);
            if (c === "+" && (c2 !== "+" && c2 !== "=")) {
                this.ArithAdvance();
                this.ArithSkipWs();
                var right = this.ArithParseMultiplicative();
                left = new ArithBinaryOp("+", left, right, "binary-op");
            }
            else {
                if (c === "-" && (c2 !== "-" && c2 !== "=")) {
                    this.ArithAdvance();
                    this.ArithSkipWs();
                    var right = this.ArithParseMultiplicative();
                    left = new ArithBinaryOp("-", left, right, "binary-op");
                }
                else {
                    break;
                }
            }
        }
        return left;
    };
    Parser.prototype.ArithParseMultiplicative = function () {
        var left = this.ArithParseExponentiation();
        while (true) {
            this.ArithSkipWs();
            var c = this.ArithPeek(0);
            var c2 = this.ArithPeek(1);
            if (c === "*" && (c2 !== "*" && c2 !== "=")) {
                this.ArithAdvance();
                this.ArithSkipWs();
                var right = this.ArithParseExponentiation();
                left = new ArithBinaryOp("*", left, right, "binary-op");
            }
            else {
                if (c === "/" && c2 !== "=") {
                    this.ArithAdvance();
                    this.ArithSkipWs();
                    var right = this.ArithParseExponentiation();
                    left = new ArithBinaryOp("/", left, right, "binary-op");
                }
                else {
                    if (c === "%" && c2 !== "=") {
                        this.ArithAdvance();
                        this.ArithSkipWs();
                        var right = this.ArithParseExponentiation();
                        left = new ArithBinaryOp("%", left, right, "binary-op");
                    }
                    else {
                        break;
                    }
                }
            }
        }
        return left;
    };
    Parser.prototype.ArithParseExponentiation = function () {
        var left = this.ArithParseUnary();
        this.ArithSkipWs();
        if (this.ArithMatch("**")) {
            this.ArithConsume("**");
            this.ArithSkipWs();
            var right = this.ArithParseExponentiation();
            return new ArithBinaryOp("**", left, right, "binary-op");
        }
        return left;
    };
    Parser.prototype.ArithParseUnary = function () {
        this.ArithSkipWs();
        if (this.ArithMatch("++")) {
            this.ArithConsume("++");
            this.ArithSkipWs();
            var operand = this.ArithParseUnary();
            return new ArithPreIncr(operand, "pre-incr");
        }
        if (this.ArithMatch("--")) {
            this.ArithConsume("--");
            this.ArithSkipWs();
            var operand = this.ArithParseUnary();
            return new ArithPreDecr(operand, "pre-decr");
        }
        var c = this.ArithPeek(0);
        if (c === "!") {
            this.ArithAdvance();
            this.ArithSkipWs();
            var operand = this.ArithParseUnary();
            return new ArithUnaryOp("!", operand, "unary-op");
        }
        if (c === "~") {
            this.ArithAdvance();
            this.ArithSkipWs();
            var operand = this.ArithParseUnary();
            return new ArithUnaryOp("~", operand, "unary-op");
        }
        if (c === "+" && this.ArithPeek(1) !== "+") {
            this.ArithAdvance();
            this.ArithSkipWs();
            var operand = this.ArithParseUnary();
            return new ArithUnaryOp("+", operand, "unary-op");
        }
        if (c === "-" && this.ArithPeek(1) !== "-") {
            this.ArithAdvance();
            this.ArithSkipWs();
            var operand = this.ArithParseUnary();
            return new ArithUnaryOp("-", operand, "unary-op");
        }
        return this.ArithParsePostfix();
    };
    Parser.prototype.ArithParsePostfix = function () {
        var left = this.ArithParsePrimary();
        while (true) {
            this.ArithSkipWs();
            if (this.ArithMatch("++")) {
                this.ArithConsume("++");
                left = new ArithPostIncr(left, "post-incr");
            }
            else {
                if (this.ArithMatch("--")) {
                    this.ArithConsume("--");
                    left = new ArithPostDecr(left, "post-decr");
                }
                else {
                    if (this.ArithPeek(0) === "[") {
                        if (left instanceof ArithVar) {
                            this.ArithAdvance();
                            this.ArithSkipWs();
                            var index = this.ArithParseComma();
                            this.ArithSkipWs();
                            if (!this.ArithConsume("]")) {
                                throw new Error("".concat("Expected ']' in array subscript", " at position ").concat(this.ArithPos));
                            }
                            left = new ArithSubscript(left.name, index, "subscript");
                        }
                        else {
                            break;
                        }
                    }
                    else {
                        break;
                    }
                }
            }
        }
        return left;
    };
    Parser.prototype.ArithParsePrimary = function () {
        this.ArithSkipWs();
        var c = this.ArithPeek(0);
        if (c === "(") {
            this.ArithAdvance();
            this.ArithSkipWs();
            var expr = this.ArithParseComma();
            this.ArithSkipWs();
            if (!this.ArithConsume(")")) {
                throw new Error("".concat("Expected ')' in arithmetic expression", " at position ").concat(this.ArithPos));
            }
            return expr;
        }
        if (c === "#" && this.ArithPeek(1) === "$") {
            this.ArithAdvance();
            return this.ArithParseExpansion();
        }
        if (c === "$") {
            return this.ArithParseExpansion();
        }
        if (c === "'") {
            return this.ArithParseSingleQuote();
        }
        if (c === "\"") {
            return this.ArithParseDoubleQuote();
        }
        if (c === "`") {
            return this.ArithParseBacktick();
        }
        if (c === "\\") {
            this.ArithAdvance();
            if (this.ArithAtEnd()) {
                throw new Error("".concat("Unexpected end after backslash in arithmetic", " at position ").concat(this.ArithPos));
            }
            var escapedChar = this.ArithAdvance();
            return new ArithEscape(escapedChar, "escape");
        }
        if (this.ArithAtEnd() || ")]:,;?|&<>=!+-*/%^~#{}".includes(c)) {
            return new ArithEmpty("empty");
        }
        return this.ArithParseNumberOrVar();
    };
    Parser.prototype.ArithParseExpansion = function () {
        if (!this.ArithConsume("$")) {
            throw new Error("".concat("Expected '$'", " at position ").concat(this.ArithPos));
        }
        var c = this.ArithPeek(0);
        if (c === "(") {
            return this.ArithParseCmdsub();
        }
        if (c === "{") {
            return this.ArithParseBracedParam();
        }
        var nameChars = [];
        while (!this.ArithAtEnd()) {
            var ch = this.ArithPeek(0);
            if (/^[a-zA-Z0-9]$/.test(ch) || ch === "_") {
                nameChars.push(this.ArithAdvance());
            }
            else {
                if ((IsSpecialParamOrDigit(ch) || ch === "#") && !(nameChars.length > 0)) {
                    nameChars.push(this.ArithAdvance());
                    break;
                }
                else {
                    break;
                }
            }
        }
        if (!(nameChars.length > 0)) {
            throw new Error("".concat("Expected variable name after $", " at position ").concat(this.ArithPos));
        }
        return new ParamExpansion(nameChars.join(""), [], [], "param");
    };
    Parser.prototype.ArithParseCmdsub = function () {
        this.ArithAdvance();
        if (this.ArithPeek(0) === "(") {
            this.ArithAdvance();
            var depth = 1;
            var contentStart = this.ArithPos;
            while (!this.ArithAtEnd() && depth > 0) {
                var ch = this.ArithPeek(0);
                if (ch === "(") {
                    depth += 1;
                    this.ArithAdvance();
                }
                else {
                    if (ch === ")") {
                        if (depth === 1 && this.ArithPeek(1) === ")") {
                            break;
                        }
                        depth -= 1;
                        this.ArithAdvance();
                    }
                    else {
                        this.ArithAdvance();
                    }
                }
            }
            var content = Substring(this.ArithSrc, contentStart, this.ArithPos);
            this.ArithAdvance();
            this.ArithAdvance();
            var innerExpr = this.ParseArithExpr(content);
            return new ArithmeticExpansion(innerExpr, "arith");
        }
        var depth = 1;
        var contentStart = this.ArithPos;
        while (!this.ArithAtEnd() && depth > 0) {
            var ch = this.ArithPeek(0);
            if (ch === "(") {
                depth += 1;
                this.ArithAdvance();
            }
            else {
                if (ch === ")") {
                    depth -= 1;
                    if (depth === 0) {
                        break;
                    }
                    this.ArithAdvance();
                }
                else {
                    this.ArithAdvance();
                }
            }
        }
        var content = Substring(this.ArithSrc, contentStart, this.ArithPos);
        this.ArithAdvance();
        var subParser = newParser(content, false, this.Extglob);
        var cmd = subParser.parseList(true);
        return new CommandSubstitution(cmd, [], "cmdsub");
    };
    Parser.prototype.ArithParseBracedParam = function () {
        this.ArithAdvance();
        if (this.ArithPeek(0) === "!") {
            this.ArithAdvance();
            var nameChars = [];
            while (!this.ArithAtEnd() && this.ArithPeek(0) !== "}") {
                nameChars.push(this.ArithAdvance());
            }
            this.ArithConsume("}");
            return new ParamIndirect(nameChars.join(""), [], [], "param-indirect");
        }
        if (this.ArithPeek(0) === "#") {
            this.ArithAdvance();
            var nameChars = [];
            while (!this.ArithAtEnd() && this.ArithPeek(0) !== "}") {
                nameChars.push(this.ArithAdvance());
            }
            this.ArithConsume("}");
            return new ParamLength(nameChars.join(""), "param-len");
        }
        var nameChars = [];
        while (!this.ArithAtEnd()) {
            var ch = this.ArithPeek(0);
            if (ch === "}") {
                this.ArithAdvance();
                return new ParamExpansion(nameChars.join(""), [], [], "param");
            }
            if (IsParamExpansionOp(ch)) {
                break;
            }
            nameChars.push(this.ArithAdvance());
        }
        var name = nameChars.join("");
        var opChars = [];
        var depth = 1;
        while (!this.ArithAtEnd() && depth > 0) {
            ch = this.ArithPeek(0);
            if (ch === "{") {
                depth += 1;
                opChars.push(this.ArithAdvance());
            }
            else {
                if (ch === "}") {
                    depth -= 1;
                    if (depth === 0) {
                        break;
                    }
                    opChars.push(this.ArithAdvance());
                }
                else {
                    opChars.push(this.ArithAdvance());
                }
            }
        }
        this.ArithConsume("}");
        var opStr = opChars.join("");
        if (opStr.startsWith(":-")) {
            return new ParamExpansion(name, ":-", Substring(opStr, 2, opStr.length), "param");
        }
        if (opStr.startsWith(":=")) {
            return new ParamExpansion(name, ":=", Substring(opStr, 2, opStr.length), "param");
        }
        if (opStr.startsWith(":+")) {
            return new ParamExpansion(name, ":+", Substring(opStr, 2, opStr.length), "param");
        }
        if (opStr.startsWith(":?")) {
            return new ParamExpansion(name, ":?", Substring(opStr, 2, opStr.length), "param");
        }
        if (opStr.startsWith(":")) {
            return new ParamExpansion(name, ":", Substring(opStr, 1, opStr.length), "param");
        }
        if (opStr.startsWith("##")) {
            return new ParamExpansion(name, "##", Substring(opStr, 2, opStr.length), "param");
        }
        if (opStr.startsWith("#")) {
            return new ParamExpansion(name, "#", Substring(opStr, 1, opStr.length), "param");
        }
        if (opStr.startsWith("%%")) {
            return new ParamExpansion(name, "%%", Substring(opStr, 2, opStr.length), "param");
        }
        if (opStr.startsWith("%")) {
            return new ParamExpansion(name, "%", Substring(opStr, 1, opStr.length), "param");
        }
        if (opStr.startsWith("//")) {
            return new ParamExpansion(name, "//", Substring(opStr, 2, opStr.length), "param");
        }
        if (opStr.startsWith("/")) {
            return new ParamExpansion(name, "/", Substring(opStr, 1, opStr.length), "param");
        }
        return new ParamExpansion(name, "", opStr, "param");
    };
    Parser.prototype.ArithParseSingleQuote = function () {
        this.ArithAdvance();
        var contentStart = this.ArithPos;
        while (!this.ArithAtEnd() && this.ArithPeek(0) !== "'") {
            this.ArithAdvance();
        }
        var content = Substring(this.ArithSrc, contentStart, this.ArithPos);
        if (!this.ArithConsume("'")) {
            throw new Error("".concat("Unterminated single quote in arithmetic", " at position ").concat(this.ArithPos));
        }
        return new ArithNumber(content, "number");
    };
    Parser.prototype.ArithParseDoubleQuote = function () {
        this.ArithAdvance();
        var contentStart = this.ArithPos;
        while (!this.ArithAtEnd() && this.ArithPeek(0) !== "\"") {
            var c = this.ArithPeek(0);
            if (c === "\\" && !this.ArithAtEnd()) {
                this.ArithAdvance();
                this.ArithAdvance();
            }
            else {
                this.ArithAdvance();
            }
        }
        var content = Substring(this.ArithSrc, contentStart, this.ArithPos);
        if (!this.ArithConsume("\"")) {
            throw new Error("".concat("Unterminated double quote in arithmetic", " at position ").concat(this.ArithPos));
        }
        return new ArithNumber(content, "number");
    };
    Parser.prototype.ArithParseBacktick = function () {
        this.ArithAdvance();
        var contentStart = this.ArithPos;
        while (!this.ArithAtEnd() && this.ArithPeek(0) !== "`") {
            var c = this.ArithPeek(0);
            if (c === "\\" && !this.ArithAtEnd()) {
                this.ArithAdvance();
                this.ArithAdvance();
            }
            else {
                this.ArithAdvance();
            }
        }
        var content = Substring(this.ArithSrc, contentStart, this.ArithPos);
        if (!this.ArithConsume("`")) {
            throw new Error("".concat("Unterminated backtick in arithmetic", " at position ").concat(this.ArithPos));
        }
        var subParser = newParser(content, false, this.Extglob);
        var cmd = subParser.parseList(true);
        return new CommandSubstitution(cmd, [], "cmdsub");
    };
    Parser.prototype.ArithParseNumberOrVar = function () {
        this.ArithSkipWs();
        var chars = [];
        var c = this.ArithPeek(0);
        if (/^[0-9]+$/.test(c)) {
            while (!this.ArithAtEnd()) {
                var ch = this.ArithPeek(0);
                if (/^[a-zA-Z0-9]$/.test(ch) || (ch === "#" || ch === "_")) {
                    chars.push(this.ArithAdvance());
                }
                else {
                    break;
                }
            }
            var prefix = chars.join("");
            if (!this.ArithAtEnd() && this.ArithPeek(0) === "$") {
                var expansion = this.ArithParseExpansion();
                return new ArithConcat([new ArithNumber(prefix, "number"), expansion], "arith-concat");
            }
            return new ArithNumber(prefix, "number");
        }
        if (/^[a-zA-Z]$/.test(c) || c === "_") {
            while (!this.ArithAtEnd()) {
                var ch = this.ArithPeek(0);
                if (/^[a-zA-Z0-9]$/.test(ch) || ch === "_") {
                    chars.push(this.ArithAdvance());
                }
                else {
                    break;
                }
            }
            return new ArithVar(chars.join(""), "var");
        }
        throw new Error("".concat("Unexpected character '" + c + "' in arithmetic expression", " at position ").concat(this.ArithPos));
    };
    Parser.prototype.ParseDeprecatedArithmetic = function () {
        if (this.atEnd() || this.peek() !== "$") {
            return [null, ""];
        }
        var start = this.pos;
        if (this.pos + 1 >= this.length || this.source[this.pos + 1] !== "[") {
            return [null, ""];
        }
        this.advance();
        this.advance();
        this.Lexer.pos = this.pos;
        var content = this.Lexer.ParseMatchedPair("[", "]", MatchedPairFlags_ARITH, false);
        this.pos = this.Lexer.pos;
        var text = Substring(this.source, start, this.pos);
        return [new ArithDeprecated(content, "arith-deprecated"), text];
    };
    Parser.prototype.ParseParamExpansion = function (inDquote) {
        this.SyncLexer();
        var _a = this.Lexer.ReadParamExpansion(inDquote), result0 = _a[0], result1 = _a[1];
        this.SyncParser();
        return [result0, result1];
    };
    Parser.prototype.parseRedirect = function () {
        this.skipWhitespace();
        if (this.atEnd()) {
            return null;
        }
        var start = this.pos;
        var fd = -1;
        var varfd = "";
        if (this.peek() === "{") {
            var saved = this.pos;
            this.advance();
            var varnameChars = [];
            var inBracket = false;
            while (!this.atEnd() && !IsRedirectChar(this.peek())) {
                var ch = this.peek();
                if (ch === "}" && !inBracket) {
                    break;
                }
                else {
                    if (ch === "[") {
                        inBracket = true;
                        varnameChars.push(this.advance());
                    }
                    else {
                        if (ch === "]") {
                            inBracket = false;
                            varnameChars.push(this.advance());
                        }
                        else {
                            if (/^[a-zA-Z0-9]$/.test(ch) || ch === "_") {
                                varnameChars.push(this.advance());
                            }
                            else {
                                if (inBracket && !IsMetachar(ch)) {
                                    varnameChars.push(this.advance());
                                }
                                else {
                                    break;
                                }
                            }
                        }
                    }
                }
            }
            var varname = varnameChars.join("");
            var isValidVarfd = false;
            if (varname !== "") {
                if (/^[a-zA-Z]$/.test(varname[0]) || varname[0] === "_") {
                    if (varname.includes("[") || varname.includes("]")) {
                        var left = varname.indexOf("[");
                        var right = varname.lastIndexOf("]");
                        if (left !== -1 && right === varname.length - 1 && right > left + 1) {
                            var base = varname.slice(0, left);
                            if (base !== "" && (/^[a-zA-Z]$/.test(base[0]) || base[0] === "_")) {
                                isValidVarfd = true;
                                for (var _i = 0, _a = base.slice(1); _i < _a.length; _i++) {
                                    var c = _a[_i];
                                    if (!(/^[a-zA-Z0-9]$/.test(c) || c === "_")) {
                                        isValidVarfd = false;
                                        break;
                                    }
                                }
                            }
                        }
                    }
                    else {
                        isValidVarfd = true;
                        for (var _b = 0, _c = varname.slice(1); _b < _c.length; _b++) {
                            var c = _c[_b];
                            if (!(/^[a-zA-Z0-9]$/.test(c) || c === "_")) {
                                isValidVarfd = false;
                                break;
                            }
                        }
                    }
                }
            }
            if (!this.atEnd() && this.peek() === "}" && isValidVarfd) {
                this.advance();
                varfd = varname;
            }
            else {
                this.pos = saved;
            }
        }
        if (varfd === "" && this.peek() !== "" && /^[0-9]+$/.test(this.peek())) {
            var fdChars = [];
            while (!this.atEnd() && /^[0-9]+$/.test(this.peek())) {
                fdChars.push(this.advance());
            }
            fd = parseInt(fdChars.join(""), 10);
        }
        var ch = this.peek();
        if (ch === "&" && this.pos + 1 < this.length && this.source[this.pos + 1] === ">") {
            if (fd !== -1 || varfd !== "") {
                this.pos = start;
                return null;
            }
            this.advance();
            this.advance();
            if (!this.atEnd() && this.peek() === ">") {
                this.advance();
                var op = "&>>";
            }
            else {
                var op = "&>";
            }
            this.skipWhitespace();
            var target = this.parseWord(false, false, false);
            if (target === null) {
                throw new Error("".concat("Expected target for redirect " + op, " at position ").concat(this.pos));
            }
            return new Redirect(op, target, [], "redirect");
        }
        if (ch === "" || !IsRedirectChar(ch)) {
            this.pos = start;
            return null;
        }
        if (fd === -1 && this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
            this.pos = start;
            return null;
        }
        var op = this.advance();
        var stripTabs = false;
        if (!this.atEnd()) {
            var nextCh = this.peek();
            if (op === ">" && nextCh === ">") {
                this.advance();
                op = ">>";
            }
            else {
                if (op === "<" && nextCh === "<") {
                    this.advance();
                    if (!this.atEnd() && this.peek() === "<") {
                        this.advance();
                        op = "<<<";
                    }
                    else {
                        if (!this.atEnd() && this.peek() === "-") {
                            this.advance();
                            op = "<<";
                            stripTabs = true;
                        }
                        else {
                            op = "<<";
                        }
                    }
                }
                else {
                    if (op === "<" && nextCh === ">") {
                        this.advance();
                        op = "<>";
                    }
                    else {
                        if (op === ">" && nextCh === "|") {
                            this.advance();
                            op = ">|";
                        }
                        else {
                            if (fd === -1 && varfd === "" && op === ">" && nextCh === "&") {
                                if (this.pos + 1 >= this.length || !IsDigitOrDash(this.source[this.pos + 1])) {
                                    this.advance();
                                    op = ">&";
                                }
                            }
                            else {
                                if (fd === -1 && varfd === "" && op === "<" && nextCh === "&") {
                                    if (this.pos + 1 >= this.length || !IsDigitOrDash(this.source[this.pos + 1])) {
                                        this.advance();
                                        op = "<&";
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        if (op === "<<") {
            return this.ParseHeredoc(fd, stripTabs);
        }
        if (varfd !== "") {
            op = "{" + varfd + "}" + op;
        }
        else {
            if (fd !== -1) {
                op = String(fd) + op;
            }
        }
        if (!this.atEnd() && this.peek() === "&") {
            this.advance();
            this.skipWhitespace();
            if (!this.atEnd() && this.peek() === "-") {
                if (this.pos + 1 < this.length && !IsMetachar(this.source[this.pos + 1])) {
                    this.advance();
                    var target = new Word("&-", [], "word");
                }
                else {
                    var target = null;
                }
            }
            else {
                var target = null;
            }
            if (target === null) {
                if (!this.atEnd() && (/^[0-9]+$/.test(this.peek()) || this.peek() === "-")) {
                    var wordStart = this.pos;
                    var fdChars = [];
                    while (!this.atEnd() && /^[0-9]+$/.test(this.peek())) {
                        fdChars.push(this.advance());
                    }
                    if (fdChars.length > 0) {
                        var fdTarget = fdChars.join("");
                    }
                    else {
                        var fdTarget = "";
                    }
                    if (!this.atEnd() && this.peek() === "-") {
                        fdTarget += this.advance();
                    }
                    if (fdTarget !== "-" && !this.atEnd() && !IsMetachar(this.peek())) {
                        this.pos = wordStart;
                        var innerWord = this.parseWord(false, false, false);
                        if (innerWord !== null) {
                            var target = new Word("&" + innerWord.value, [], "word");
                            target.parts = innerWord.parts;
                        }
                        else {
                            throw new Error("".concat("Expected target for redirect " + op, " at position ").concat(this.pos));
                        }
                    }
                    else {
                        var target = new Word("&" + fdTarget, [], "word");
                    }
                }
                else {
                    var innerWord = this.parseWord(false, false, false);
                    if (innerWord !== null) {
                        var target = new Word("&" + innerWord.value, [], "word");
                        target.parts = innerWord.parts;
                    }
                    else {
                        throw new Error("".concat("Expected target for redirect " + op, " at position ").concat(this.pos));
                    }
                }
            }
        }
        else {
            this.skipWhitespace();
            if ((op === ">&" || op === "<&") && !this.atEnd() && this.peek() === "-") {
                if (this.pos + 1 < this.length && !IsMetachar(this.source[this.pos + 1])) {
                    this.advance();
                    var target = new Word("&-", [], "word");
                }
                else {
                    var target = this.parseWord(false, false, false);
                }
            }
            else {
                var target = this.parseWord(false, false, false);
            }
        }
        if (target === null) {
            throw new Error("".concat("Expected target for redirect " + op, " at position ").concat(this.pos));
        }
        return new Redirect(op, target, [], "redirect");
    };
    Parser.prototype.ParseHeredocDelimiter = function () {
        this.skipWhitespace();
        var quoted = false;
        var delimiterChars = [];
        while (true) {
            while (!this.atEnd() && !IsMetachar(this.peek())) {
                var ch = this.peek();
                if (ch === "\"") {
                    quoted = true;
                    this.advance();
                    while (!this.atEnd() && this.peek() !== "\"") {
                        delimiterChars.push(this.advance());
                    }
                    if (!this.atEnd()) {
                        this.advance();
                    }
                }
                else {
                    if (ch === "'") {
                        quoted = true;
                        this.advance();
                        while (!this.atEnd() && this.peek() !== "'") {
                            var c = this.advance();
                            if (c === "\n") {
                                this.SawNewlineInSingleQuote = true;
                            }
                            delimiterChars.push(c);
                        }
                        if (!this.atEnd()) {
                            this.advance();
                        }
                    }
                    else {
                        if (ch === "\\") {
                            this.advance();
                            if (!this.atEnd()) {
                                var nextCh = this.peek();
                                if (nextCh === "\n") {
                                    this.advance();
                                }
                                else {
                                    quoted = true;
                                    delimiterChars.push(this.advance());
                                }
                            }
                        }
                        else {
                            if (ch === "$" && this.pos + 1 < this.length && this.source[this.pos + 1] === "'") {
                                quoted = true;
                                this.advance();
                                this.advance();
                                while (!this.atEnd() && this.peek() !== "'") {
                                    var c = this.peek();
                                    if (c === "\\" && this.pos + 1 < this.length) {
                                        this.advance();
                                        var esc = this.peek();
                                        var escVal = GetAnsiEscape(esc);
                                        if (escVal >= 0) {
                                            delimiterChars.push(String.fromCodePoint(escVal));
                                            this.advance();
                                        }
                                        else {
                                            if (esc === "'") {
                                                delimiterChars.push(this.advance());
                                            }
                                            else {
                                                delimiterChars.push(this.advance());
                                            }
                                        }
                                    }
                                    else {
                                        delimiterChars.push(this.advance());
                                    }
                                }
                                if (!this.atEnd()) {
                                    this.advance();
                                }
                            }
                            else {
                                if (IsExpansionStart(this.source, this.pos, "$(")) {
                                    delimiterChars.push(this.advance());
                                    delimiterChars.push(this.advance());
                                    var depth = 1;
                                    while (!this.atEnd() && depth > 0) {
                                        var c = this.peek();
                                        if (c === "(") {
                                            depth += 1;
                                        }
                                        else {
                                            if (c === ")") {
                                                depth -= 1;
                                            }
                                        }
                                        delimiterChars.push(this.advance());
                                    }
                                }
                                else {
                                    if (ch === "$" && this.pos + 1 < this.length && this.source[this.pos + 1] === "{") {
                                        var dollarCount = 0;
                                        var j = this.pos - 1;
                                        while (j >= 0 && this.source[j] === "$") {
                                            dollarCount += 1;
                                            j -= 1;
                                        }
                                        if (j >= 0 && this.source[j] === "\\") {
                                            dollarCount -= 1;
                                        }
                                        if (dollarCount % 2 === 1) {
                                            delimiterChars.push(this.advance());
                                        }
                                        else {
                                            delimiterChars.push(this.advance());
                                            delimiterChars.push(this.advance());
                                            var depth = 0;
                                            while (!this.atEnd()) {
                                                var c = this.peek();
                                                if (c === "{") {
                                                    depth += 1;
                                                }
                                                else {
                                                    if (c === "}") {
                                                        delimiterChars.push(this.advance());
                                                        if (depth === 0) {
                                                            break;
                                                        }
                                                        depth -= 1;
                                                        if (depth === 0 && !this.atEnd() && IsMetachar(this.peek())) {
                                                            break;
                                                        }
                                                        continue;
                                                    }
                                                }
                                                delimiterChars.push(this.advance());
                                            }
                                        }
                                    }
                                    else {
                                        if (ch === "$" && this.pos + 1 < this.length && this.source[this.pos + 1] === "[") {
                                            var dollarCount = 0;
                                            var j = this.pos - 1;
                                            while (j >= 0 && this.source[j] === "$") {
                                                dollarCount += 1;
                                                j -= 1;
                                            }
                                            if (j >= 0 && this.source[j] === "\\") {
                                                dollarCount -= 1;
                                            }
                                            if (dollarCount % 2 === 1) {
                                                delimiterChars.push(this.advance());
                                            }
                                            else {
                                                delimiterChars.push(this.advance());
                                                delimiterChars.push(this.advance());
                                                var depth = 1;
                                                while (!this.atEnd() && depth > 0) {
                                                    var c = this.peek();
                                                    if (c === "[") {
                                                        depth += 1;
                                                    }
                                                    else {
                                                        if (c === "]") {
                                                            depth -= 1;
                                                        }
                                                    }
                                                    delimiterChars.push(this.advance());
                                                }
                                            }
                                        }
                                        else {
                                            if (ch === "`") {
                                                delimiterChars.push(this.advance());
                                                while (!this.atEnd() && this.peek() !== "`") {
                                                    var c = this.peek();
                                                    if (c === "'") {
                                                        delimiterChars.push(this.advance());
                                                        while (!this.atEnd() && this.peek() !== "'" && this.peek() !== "`") {
                                                            delimiterChars.push(this.advance());
                                                        }
                                                        if (!this.atEnd() && this.peek() === "'") {
                                                            delimiterChars.push(this.advance());
                                                        }
                                                    }
                                                    else {
                                                        if (c === "\"") {
                                                            delimiterChars.push(this.advance());
                                                            while (!this.atEnd() && this.peek() !== "\"" && this.peek() !== "`") {
                                                                if (this.peek() === "\\" && this.pos + 1 < this.length) {
                                                                    delimiterChars.push(this.advance());
                                                                }
                                                                delimiterChars.push(this.advance());
                                                            }
                                                            if (!this.atEnd() && this.peek() === "\"") {
                                                                delimiterChars.push(this.advance());
                                                            }
                                                        }
                                                        else {
                                                            if (c === "\\" && this.pos + 1 < this.length) {
                                                                delimiterChars.push(this.advance());
                                                                delimiterChars.push(this.advance());
                                                            }
                                                            else {
                                                                delimiterChars.push(this.advance());
                                                            }
                                                        }
                                                    }
                                                }
                                                if (!this.atEnd()) {
                                                    delimiterChars.push(this.advance());
                                                }
                                            }
                                            else {
                                                delimiterChars.push(this.advance());
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            if (!this.atEnd() && "<>".includes(this.peek()) && this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
                delimiterChars.push(this.advance());
                delimiterChars.push(this.advance());
                var depth = 1;
                while (!this.atEnd() && depth > 0) {
                    var c = this.peek();
                    if (c === "(") {
                        depth += 1;
                    }
                    else {
                        if (c === ")") {
                            depth -= 1;
                        }
                    }
                    delimiterChars.push(this.advance());
                }
                continue;
            }
            break;
        }
        return [delimiterChars.join(""), quoted];
    };
    Parser.prototype.ReadHeredocLine = function (quoted) {
        var lineStart = this.pos;
        var lineEnd = this.pos;
        while (lineEnd < this.length && this.source[lineEnd] !== "\n") {
            lineEnd += 1;
        }
        var line = Substring(this.source, lineStart, lineEnd);
        if (!quoted) {
            while (lineEnd < this.length) {
                var trailingBs = CountTrailingBackslashes(line);
                if (trailingBs % 2 === 0) {
                    break;
                }
                line = Substring(line, 0, line.length - 1);
                lineEnd += 1;
                var nextLineStart = lineEnd;
                while (lineEnd < this.length && this.source[lineEnd] !== "\n") {
                    lineEnd += 1;
                }
                line = line + Substring(this.source, nextLineStart, lineEnd);
            }
        }
        return [line, lineEnd];
    };
    Parser.prototype.LineMatchesDelimiter = function (line, delimiter, stripTabs) {
        var checkLine = stripTabs ? line.replace(/^[\t]+/, '') : line;
        var normalizedCheck = NormalizeHeredocDelimiter(checkLine);
        var normalizedDelim = NormalizeHeredocDelimiter(delimiter);
        return [normalizedCheck === normalizedDelim, checkLine];
    };
    Parser.prototype.GatherHeredocBodies = function () {
        for (var _i = 0, _a = this.PendingHeredocs; _i < _a.length; _i++) {
            var heredoc = _a[_i];
            var contentLines = [];
            var lineStart = this.pos;
            while (this.pos < this.length) {
                lineStart = this.pos;
                var _b = this.ReadHeredocLine(heredoc.quoted), line = _b[0], lineEnd = _b[1];
                var _c = this.LineMatchesDelimiter(line, heredoc.delimiter, heredoc.stripTabs), matches = _c[0], checkLine = _c[1];
                if (matches) {
                    this.pos = lineEnd < this.length ? lineEnd + 1 : lineEnd;
                    break;
                }
                var normalizedCheck = NormalizeHeredocDelimiter(checkLine);
                var normalizedDelim = NormalizeHeredocDelimiter(heredoc.delimiter);
                if (this.EofToken === ")" && normalizedCheck.startsWith(normalizedDelim)) {
                    var tabsStripped = line.length - checkLine.length;
                    this.pos = lineStart + tabsStripped + heredoc.delimiter.length;
                    break;
                }
                if (lineEnd >= this.length && normalizedCheck.startsWith(normalizedDelim) && this.InProcessSub) {
                    var tabsStripped = line.length - checkLine.length;
                    this.pos = lineStart + tabsStripped + heredoc.delimiter.length;
                    break;
                }
                if (heredoc.stripTabs) {
                    line = line.replace(/^[\t]+/, '');
                }
                if (lineEnd < this.length) {
                    contentLines.push(line + "\n");
                    this.pos = lineEnd + 1;
                }
                else {
                    var addNewline = true;
                    if (!heredoc.quoted && CountTrailingBackslashes(line) % 2 === 1) {
                        addNewline = false;
                    }
                    contentLines.push(line + addNewline ? "\n" : "");
                    this.pos = this.length;
                }
            }
            heredoc.content = contentLines.join("");
        }
        this.PendingHeredocs = [];
    };
    Parser.prototype.ParseHeredoc = function (fd, stripTabs) {
        var startPos = this.pos;
        this.SetState(ParserStateFlags_PST_HEREDOC);
        var _a = this.ParseHeredocDelimiter(), delimiter = _a[0], quoted = _a[1];
        for (var _i = 0, _b = this.PendingHeredocs; _i < _b.length; _i++) {
            var existing = _b[_i];
            if (existing.StartPos === startPos && existing.delimiter === delimiter) {
                this.ClearState(ParserStateFlags_PST_HEREDOC);
                return existing;
            }
        }
        var heredoc = new HereDoc(delimiter, "", stripTabs, quoted, fd, false, [], "heredoc");
        heredoc.StartPos = startPos;
        this.PendingHeredocs.push(heredoc);
        this.ClearState(ParserStateFlags_PST_HEREDOC);
        return heredoc;
    };
    Parser.prototype.parseCommand = function () {
        var words = [];
        var redirects = [];
        while (true) {
            this.skipWhitespace();
            if (this.LexIsCommandTerminator()) {
                break;
            }
            if (words.length === 0) {
                var reserved = this.LexPeekReservedWord();
                if (reserved === "}" || reserved === "]]") {
                    break;
                }
            }
            var redirect = this.parseRedirect();
            if (redirect !== null) {
                redirects.push(redirect);
                continue;
            }
            var allAssignments = true;
            for (var _i = 0, words_1 = words; _i < words_1.length; _i++) {
                var w = words_1[_i];
                if (!this.IsAssignmentWord(w)) {
                    allAssignments = false;
                    break;
                }
            }
            var inAssignBuiltin = words.length > 0 && ASSIGNMENT_BUILTINS.has(words[0].value);
            var word = this.parseWord(!(words.length > 0) || allAssignments && redirects.length === 0, false, inAssignBuiltin);
            if (word === null) {
                break;
            }
            words.push(word);
        }
        if (!(words.length > 0) && !(redirects.length > 0)) {
            return null;
        }
        return new Command(words, redirects, "command");
    };
    Parser.prototype.parseSubshell = function () {
        this.skipWhitespace();
        if (this.atEnd() || this.peek() !== "(") {
            return null;
        }
        this.advance();
        this.SetState(ParserStateFlags_PST_SUBSHELL);
        var body = this.parseList(true);
        if (body === null) {
            this.ClearState(ParserStateFlags_PST_SUBSHELL);
            throw new Error("".concat("Expected command in subshell", " at position ").concat(this.pos));
        }
        this.skipWhitespace();
        if (this.atEnd() || this.peek() !== ")") {
            this.ClearState(ParserStateFlags_PST_SUBSHELL);
            throw new Error("".concat("Expected ) to close subshell", " at position ").concat(this.pos));
        }
        this.advance();
        this.ClearState(ParserStateFlags_PST_SUBSHELL);
        return new Subshell(body, this.CollectRedirects(), "subshell");
    };
    Parser.prototype.parseArithmeticCommand = function () {
        this.skipWhitespace();
        if (this.atEnd() || this.peek() !== "(" || this.pos + 1 >= this.length || this.source[this.pos + 1] !== "(") {
            return null;
        }
        var savedPos = this.pos;
        this.advance();
        this.advance();
        var contentStart = this.pos;
        var depth = 1;
        while (!this.atEnd() && depth > 0) {
            var c = this.peek();
            if (c === "'") {
                this.advance();
                while (!this.atEnd() && this.peek() !== "'") {
                    this.advance();
                }
                if (!this.atEnd()) {
                    this.advance();
                }
            }
            else {
                if (c === "\"") {
                    this.advance();
                    while (!this.atEnd()) {
                        if (this.peek() === "\\" && this.pos + 1 < this.length) {
                            this.advance();
                            this.advance();
                        }
                        else {
                            if (this.peek() === "\"") {
                                this.advance();
                                break;
                            }
                            else {
                                this.advance();
                            }
                        }
                    }
                }
                else {
                    if (c === "\\" && this.pos + 1 < this.length) {
                        this.advance();
                        this.advance();
                    }
                    else {
                        if (c === "(") {
                            depth += 1;
                            this.advance();
                        }
                        else {
                            if (c === ")") {
                                if (depth === 1 && this.pos + 1 < this.length && this.source[this.pos + 1] === ")") {
                                    break;
                                }
                                depth -= 1;
                                if (depth === 0) {
                                    this.pos = savedPos;
                                    return null;
                                }
                                this.advance();
                            }
                            else {
                                this.advance();
                            }
                        }
                    }
                }
            }
        }
        if (this.atEnd()) {
            throw new Error("".concat("unexpected EOF looking for `))'", " at position ").concat(savedPos));
        }
        if (depth !== 1) {
            this.pos = savedPos;
            return null;
        }
        var content = Substring(this.source, contentStart, this.pos);
        content = content.replace(/\\\n/g, "");
        this.advance();
        this.advance();
        var expr = this.ParseArithExpr(content);
        return new ArithmeticCommand(expr, this.CollectRedirects(), content, "arith-cmd");
    };
    Parser.prototype.parseConditionalExpr = function () {
        this.skipWhitespace();
        if (this.atEnd() || this.peek() !== "[" || this.pos + 1 >= this.length || this.source[this.pos + 1] !== "[") {
            return null;
        }
        var nextPos = this.pos + 2;
        if (nextPos < this.length && !(IsWhitespace(this.source[nextPos]) || this.source[nextPos] === "\\" && nextPos + 1 < this.length && this.source[nextPos + 1] === "\n")) {
            return null;
        }
        this.advance();
        this.advance();
        this.SetState(ParserStateFlags_PST_CONDEXPR);
        this.WordContext = WORD_CTX_COND;
        var body = this.ParseCondOr();
        while (!this.atEnd() && IsWhitespaceNoNewline(this.peek())) {
            this.advance();
        }
        if (this.atEnd() || this.peek() !== "]" || this.pos + 1 >= this.length || this.source[this.pos + 1] !== "]") {
            this.ClearState(ParserStateFlags_PST_CONDEXPR);
            this.WordContext = WORD_CTX_NORMAL;
            throw new Error("".concat("Expected ]] to close conditional expression", " at position ").concat(this.pos));
        }
        this.advance();
        this.advance();
        this.ClearState(ParserStateFlags_PST_CONDEXPR);
        this.WordContext = WORD_CTX_NORMAL;
        return new ConditionalExpr(body, this.CollectRedirects(), "cond-expr");
    };
    Parser.prototype.CondSkipWhitespace = function () {
        while (!this.atEnd()) {
            if (IsWhitespaceNoNewline(this.peek())) {
                this.advance();
            }
            else {
                if (this.peek() === "\\" && this.pos + 1 < this.length && this.source[this.pos + 1] === "\n") {
                    this.advance();
                    this.advance();
                }
                else {
                    if (this.peek() === "\n") {
                        this.advance();
                    }
                    else {
                        break;
                    }
                }
            }
        }
    };
    Parser.prototype.CondAtEnd = function () {
        return this.atEnd() || this.peek() === "]" && this.pos + 1 < this.length && this.source[this.pos + 1] === "]";
    };
    Parser.prototype.ParseCondOr = function () {
        this.CondSkipWhitespace();
        var left = this.ParseCondAnd();
        this.CondSkipWhitespace();
        if (!this.CondAtEnd() && this.peek() === "|" && this.pos + 1 < this.length && this.source[this.pos + 1] === "|") {
            this.advance();
            this.advance();
            var right = this.ParseCondOr();
            return new CondOr(left, right, "cond-or");
        }
        return left;
    };
    Parser.prototype.ParseCondAnd = function () {
        this.CondSkipWhitespace();
        var left = this.ParseCondTerm();
        this.CondSkipWhitespace();
        if (!this.CondAtEnd() && this.peek() === "&" && this.pos + 1 < this.length && this.source[this.pos + 1] === "&") {
            this.advance();
            this.advance();
            var right = this.ParseCondAnd();
            return new CondAnd(left, right, "cond-and");
        }
        return left;
    };
    Parser.prototype.ParseCondTerm = function () {
        this.CondSkipWhitespace();
        if (this.CondAtEnd()) {
            throw new Error("".concat("Unexpected end of conditional expression", " at position ").concat(this.pos));
        }
        if (this.peek() === "!") {
            if (this.pos + 1 < this.length && !IsWhitespaceNoNewline(this.source[this.pos + 1])) {
            }
            else {
                this.advance();
                var operand = this.ParseCondTerm();
                return new CondNot(operand, "cond-not");
            }
        }
        if (this.peek() === "(") {
            this.advance();
            var inner = this.ParseCondOr();
            this.CondSkipWhitespace();
            if (this.atEnd() || this.peek() !== ")") {
                throw new Error("".concat("Expected ) in conditional expression", " at position ").concat(this.pos));
            }
            this.advance();
            return new CondParen(inner, "cond-paren");
        }
        var word1 = this.ParseCondWord();
        if (word1 === null) {
            throw new Error("".concat("Expected word in conditional expression", " at position ").concat(this.pos));
        }
        this.CondSkipWhitespace();
        if (COND_UNARY_OPS.has(word1.value)) {
            var operand = this.ParseCondWord();
            if (operand === null) {
                throw new Error("".concat("Expected operand after " + word1.value, " at position ").concat(this.pos));
            }
            return new UnaryTest(word1.value, operand, "unary-test");
        }
        if (!this.CondAtEnd() && (this.peek() !== "&" && this.peek() !== "|" && this.peek() !== ")")) {
            if (IsRedirectChar(this.peek()) && !(this.pos + 1 < this.length && this.source[this.pos + 1] === "(")) {
                var op = this.advance();
                this.CondSkipWhitespace();
                var word2 = this.ParseCondWord();
                if (word2 === null) {
                    throw new Error("".concat("Expected operand after " + op, " at position ").concat(this.pos));
                }
                return new BinaryTest(op, word1, word2, "binary-test");
            }
            var savedPos = this.pos;
            var opWord = this.ParseCondWord();
            if (opWord !== null && COND_BINARY_OPS.has(opWord.value)) {
                this.CondSkipWhitespace();
                if (opWord.value === "=~") {
                    var word2 = this.ParseCondRegexWord();
                }
                else {
                    var word2 = this.ParseCondWord();
                }
                if (word2 === null) {
                    throw new Error("".concat("Expected operand after " + opWord.value, " at position ").concat(this.pos));
                }
                return new BinaryTest(opWord.value, word1, word2, "binary-test");
            }
            else {
                this.pos = savedPos;
            }
        }
        return new UnaryTest("-n", word1, "unary-test");
    };
    Parser.prototype.ParseCondWord = function () {
        this.CondSkipWhitespace();
        if (this.CondAtEnd()) {
            return null;
        }
        var c = this.peek();
        if (IsParen(c)) {
            return null;
        }
        if (c === "&" && this.pos + 1 < this.length && this.source[this.pos + 1] === "&") {
            return null;
        }
        if (c === "|" && this.pos + 1 < this.length && this.source[this.pos + 1] === "|") {
            return null;
        }
        return this.ParseWordInternal(WORD_CTX_COND, false, false);
    };
    Parser.prototype.ParseCondRegexWord = function () {
        this.CondSkipWhitespace();
        if (this.CondAtEnd()) {
            return null;
        }
        this.SetState(ParserStateFlags_PST_REGEXP);
        var result = this.ParseWordInternal(WORD_CTX_REGEX, false, false);
        this.ClearState(ParserStateFlags_PST_REGEXP);
        this.WordContext = WORD_CTX_COND;
        return result;
    };
    Parser.prototype.parseBraceGroup = function () {
        this.skipWhitespace();
        if (!this.LexConsumeWord("{")) {
            return null;
        }
        this.skipWhitespaceAndNewlines();
        var body = this.parseList(true);
        if (body === null) {
            throw new Error("".concat("Expected command in brace group", " at position ").concat(this.LexPeekToken().pos));
        }
        this.skipWhitespace();
        if (!this.LexConsumeWord("}")) {
            throw new Error("".concat("Expected } to close brace group", " at position ").concat(this.LexPeekToken().pos));
        }
        return new BraceGroup(body, this.CollectRedirects(), "brace-group");
    };
    Parser.prototype.parseIf = function () {
        this.skipWhitespace();
        if (!this.LexConsumeWord("if")) {
            return null;
        }
        var condition = this.parseListUntil(new Set(["then"]));
        if (condition === null) {
            throw new Error("".concat("Expected condition after 'if'", " at position ").concat(this.LexPeekToken().pos));
        }
        this.skipWhitespaceAndNewlines();
        if (!this.LexConsumeWord("then")) {
            throw new Error("".concat("Expected 'then' after if condition", " at position ").concat(this.LexPeekToken().pos));
        }
        var thenBody = this.parseListUntil(new Set(["elif", "else", "fi"]));
        if (thenBody === null) {
            throw new Error("".concat("Expected commands after 'then'", " at position ").concat(this.LexPeekToken().pos));
        }
        this.skipWhitespaceAndNewlines();
        var elseBody = null;
        if (this.LexIsAtReservedWord("elif")) {
            this.LexConsumeWord("elif");
            var elifCondition = this.parseListUntil(new Set(["then"]));
            if (elifCondition === null) {
                throw new Error("".concat("Expected condition after 'elif'", " at position ").concat(this.LexPeekToken().pos));
            }
            this.skipWhitespaceAndNewlines();
            if (!this.LexConsumeWord("then")) {
                throw new Error("".concat("Expected 'then' after elif condition", " at position ").concat(this.LexPeekToken().pos));
            }
            var elifThenBody = this.parseListUntil(new Set(["elif", "else", "fi"]));
            if (elifThenBody === null) {
                throw new Error("".concat("Expected commands after 'then'", " at position ").concat(this.LexPeekToken().pos));
            }
            this.skipWhitespaceAndNewlines();
            var innerElse = null;
            if (this.LexIsAtReservedWord("elif")) {
                innerElse = this.ParseElifChain();
            }
            else {
                if (this.LexIsAtReservedWord("else")) {
                    this.LexConsumeWord("else");
                    innerElse = this.parseListUntil(new Set(["fi"]));
                    if (innerElse === null) {
                        throw new Error("".concat("Expected commands after 'else'", " at position ").concat(this.LexPeekToken().pos));
                    }
                }
            }
            elseBody = new If(elifCondition, elifThenBody, innerElse, [], "if");
        }
        else {
            if (this.LexIsAtReservedWord("else")) {
                this.LexConsumeWord("else");
                elseBody = this.parseListUntil(new Set(["fi"]));
                if (elseBody === null) {
                    throw new Error("".concat("Expected commands after 'else'", " at position ").concat(this.LexPeekToken().pos));
                }
            }
        }
        this.skipWhitespaceAndNewlines();
        if (!this.LexConsumeWord("fi")) {
            throw new Error("".concat("Expected 'fi' to close if statement", " at position ").concat(this.LexPeekToken().pos));
        }
        return new If(condition, thenBody, elseBody, this.CollectRedirects(), "if");
    };
    Parser.prototype.ParseElifChain = function () {
        this.LexConsumeWord("elif");
        var condition = this.parseListUntil(new Set(["then"]));
        if (condition === null) {
            throw new Error("".concat("Expected condition after 'elif'", " at position ").concat(this.LexPeekToken().pos));
        }
        this.skipWhitespaceAndNewlines();
        if (!this.LexConsumeWord("then")) {
            throw new Error("".concat("Expected 'then' after elif condition", " at position ").concat(this.LexPeekToken().pos));
        }
        var thenBody = this.parseListUntil(new Set(["elif", "else", "fi"]));
        if (thenBody === null) {
            throw new Error("".concat("Expected commands after 'then'", " at position ").concat(this.LexPeekToken().pos));
        }
        this.skipWhitespaceAndNewlines();
        var elseBody = null;
        if (this.LexIsAtReservedWord("elif")) {
            elseBody = this.ParseElifChain();
        }
        else {
            if (this.LexIsAtReservedWord("else")) {
                this.LexConsumeWord("else");
                elseBody = this.parseListUntil(new Set(["fi"]));
                if (elseBody === null) {
                    throw new Error("".concat("Expected commands after 'else'", " at position ").concat(this.LexPeekToken().pos));
                }
            }
        }
        return new If(condition, thenBody, elseBody, [], "if");
    };
    Parser.prototype.parseWhile = function () {
        this.skipWhitespace();
        if (!this.LexConsumeWord("while")) {
            return null;
        }
        var condition = this.parseListUntil(new Set(["do"]));
        if (condition === null) {
            throw new Error("".concat("Expected condition after 'while'", " at position ").concat(this.LexPeekToken().pos));
        }
        this.skipWhitespaceAndNewlines();
        if (!this.LexConsumeWord("do")) {
            throw new Error("".concat("Expected 'do' after while condition", " at position ").concat(this.LexPeekToken().pos));
        }
        var body = this.parseListUntil(new Set(["done"]));
        if (body === null) {
            throw new Error("".concat("Expected commands after 'do'", " at position ").concat(this.LexPeekToken().pos));
        }
        this.skipWhitespaceAndNewlines();
        if (!this.LexConsumeWord("done")) {
            throw new Error("".concat("Expected 'done' to close while loop", " at position ").concat(this.LexPeekToken().pos));
        }
        return new While(condition, body, this.CollectRedirects(), "while");
    };
    Parser.prototype.parseUntil = function () {
        this.skipWhitespace();
        if (!this.LexConsumeWord("until")) {
            return null;
        }
        var condition = this.parseListUntil(new Set(["do"]));
        if (condition === null) {
            throw new Error("".concat("Expected condition after 'until'", " at position ").concat(this.LexPeekToken().pos));
        }
        this.skipWhitespaceAndNewlines();
        if (!this.LexConsumeWord("do")) {
            throw new Error("".concat("Expected 'do' after until condition", " at position ").concat(this.LexPeekToken().pos));
        }
        var body = this.parseListUntil(new Set(["done"]));
        if (body === null) {
            throw new Error("".concat("Expected commands after 'do'", " at position ").concat(this.LexPeekToken().pos));
        }
        this.skipWhitespaceAndNewlines();
        if (!this.LexConsumeWord("done")) {
            throw new Error("".concat("Expected 'done' to close until loop", " at position ").concat(this.LexPeekToken().pos));
        }
        return new Until(condition, body, this.CollectRedirects(), "until");
    };
    Parser.prototype.parseFor = function () {
        this.skipWhitespace();
        if (!this.LexConsumeWord("for")) {
            return null;
        }
        this.skipWhitespace();
        if (this.peek() === "(" && this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
            return this.ParseForArith();
        }
        if (this.peek() === "$") {
            var varWord = this.parseWord(false, false, false);
            if (varWord === null) {
                throw new Error("".concat("Expected variable name after 'for'", " at position ").concat(this.LexPeekToken().pos));
            }
            var varName = varWord.value;
        }
        else {
            var varName = this.peekWord();
            if (varName === "") {
                throw new Error("".concat("Expected variable name after 'for'", " at position ").concat(this.LexPeekToken().pos));
            }
            this.consumeWord(varName);
        }
        this.skipWhitespace();
        if (this.peek() === ";") {
            this.advance();
        }
        this.skipWhitespaceAndNewlines();
        var words = null;
        if (this.LexIsAtReservedWord("in")) {
            this.LexConsumeWord("in");
            this.skipWhitespace();
            var sawDelimiter = IsSemicolonOrNewline(this.peek());
            if (this.peek() === ";") {
                this.advance();
            }
            this.skipWhitespaceAndNewlines();
            words = [];
            while (true) {
                this.skipWhitespace();
                if (this.atEnd()) {
                    break;
                }
                if (IsSemicolonOrNewline(this.peek())) {
                    sawDelimiter = true;
                    if (this.peek() === ";") {
                        this.advance();
                    }
                    break;
                }
                if (this.LexIsAtReservedWord("do")) {
                    if (sawDelimiter) {
                        break;
                    }
                    throw new Error("".concat("Expected ';' or newline before 'do'", " at position ").concat(this.LexPeekToken().pos));
                }
                var word = this.parseWord(false, false, false);
                if (word === null) {
                    break;
                }
                words.push(word);
            }
        }
        this.skipWhitespaceAndNewlines();
        if (this.peek() === "{") {
            var braceGroup = this.parseBraceGroup();
            if (braceGroup === null) {
                throw new Error("".concat("Expected brace group in for loop", " at position ").concat(this.LexPeekToken().pos));
            }
            return new For(varName, words, braceGroup.body, this.CollectRedirects(), "for");
        }
        if (!this.LexConsumeWord("do")) {
            throw new Error("".concat("Expected 'do' in for loop", " at position ").concat(this.LexPeekToken().pos));
        }
        var body = this.parseListUntil(new Set(["done"]));
        if (body === null) {
            throw new Error("".concat("Expected commands after 'do'", " at position ").concat(this.LexPeekToken().pos));
        }
        this.skipWhitespaceAndNewlines();
        if (!this.LexConsumeWord("done")) {
            throw new Error("".concat("Expected 'done' to close for loop", " at position ").concat(this.LexPeekToken().pos));
        }
        return new For(varName, words, body, this.CollectRedirects(), "for");
    };
    Parser.prototype.ParseForArith = function () {
        this.advance();
        this.advance();
        var parts = [];
        var current = [];
        var parenDepth = 0;
        while (!this.atEnd()) {
            var ch = this.peek();
            if (ch === "(") {
                parenDepth += 1;
                current.push(this.advance());
            }
            else {
                if (ch === ")") {
                    if (parenDepth > 0) {
                        parenDepth -= 1;
                        current.push(this.advance());
                    }
                    else {
                        if (this.pos + 1 < this.length && this.source[this.pos + 1] === ")") {
                            parts.push(current.join("").replace(/^[ \t]+/, ''));
                            this.advance();
                            this.advance();
                            break;
                        }
                        else {
                            current.push(this.advance());
                        }
                    }
                }
                else {
                    if (ch === ";" && parenDepth === 0) {
                        parts.push(current.join("").replace(/^[ \t]+/, ''));
                        current = [];
                        this.advance();
                    }
                    else {
                        current.push(this.advance());
                    }
                }
            }
        }
        if (parts.length !== 3) {
            throw new Error("".concat("Expected three expressions in for ((;;))", " at position ").concat(this.pos));
        }
        var init = parts[0];
        var cond = parts[1];
        var incr = parts[2];
        this.skipWhitespace();
        if (!this.atEnd() && this.peek() === ";") {
            this.advance();
        }
        this.skipWhitespaceAndNewlines();
        var body = this.ParseLoopBody("for loop");
        return new ForArith(init, cond, incr, body, this.CollectRedirects(), "for-arith");
    };
    Parser.prototype.parseSelect = function () {
        this.skipWhitespace();
        if (!this.LexConsumeWord("select")) {
            return null;
        }
        this.skipWhitespace();
        var varName = this.peekWord();
        if (varName === "") {
            throw new Error("".concat("Expected variable name after 'select'", " at position ").concat(this.LexPeekToken().pos));
        }
        this.consumeWord(varName);
        this.skipWhitespace();
        if (this.peek() === ";") {
            this.advance();
        }
        this.skipWhitespaceAndNewlines();
        var words = null;
        if (this.LexIsAtReservedWord("in")) {
            this.LexConsumeWord("in");
            this.skipWhitespaceAndNewlines();
            words = [];
            while (true) {
                this.skipWhitespace();
                if (this.atEnd()) {
                    break;
                }
                if (IsSemicolonNewlineBrace(this.peek())) {
                    if (this.peek() === ";") {
                        this.advance();
                    }
                    break;
                }
                if (this.LexIsAtReservedWord("do")) {
                    break;
                }
                var word = this.parseWord(false, false, false);
                if (word === null) {
                    break;
                }
                words.push(word);
            }
        }
        this.skipWhitespaceAndNewlines();
        var body = this.ParseLoopBody("select");
        return new Select(varName, words, body, this.CollectRedirects(), "select");
    };
    Parser.prototype.ConsumeCaseTerminator = function () {
        var term = this.LexPeekCaseTerminator();
        if (term !== "") {
            this.LexNextToken();
            return term;
        }
        return ";;";
    };
    Parser.prototype.parseCase = function () {
        if (!this.consumeWord("case")) {
            return null;
        }
        this.SetState(ParserStateFlags_PST_CASESTMT);
        this.skipWhitespace();
        var word = this.parseWord(false, false, false);
        if (word === null) {
            throw new Error("".concat("Expected word after 'case'", " at position ").concat(this.LexPeekToken().pos));
        }
        this.skipWhitespaceAndNewlines();
        if (!this.LexConsumeWord("in")) {
            throw new Error("".concat("Expected 'in' after case word", " at position ").concat(this.LexPeekToken().pos));
        }
        this.skipWhitespaceAndNewlines();
        var patterns = [];
        this.SetState(ParserStateFlags_PST_CASEPAT);
        while (true) {
            this.skipWhitespaceAndNewlines();
            if (this.LexIsAtReservedWord("esac")) {
                var saved = this.pos;
                this.skipWhitespace();
                while (!this.atEnd() && !IsMetachar(this.peek()) && !IsQuote(this.peek())) {
                    this.advance();
                }
                this.skipWhitespace();
                var isPattern = false;
                if (!this.atEnd() && this.peek() === ")") {
                    if (this.EofToken === ")") {
                        isPattern = false;
                    }
                    else {
                        this.advance();
                        this.skipWhitespace();
                        if (!this.atEnd()) {
                            var nextCh = this.peek();
                            if (nextCh === ";") {
                                isPattern = true;
                            }
                            else {
                                if (!IsNewlineOrRightParen(nextCh)) {
                                    isPattern = true;
                                }
                            }
                        }
                    }
                }
                this.pos = saved;
                if (!isPattern) {
                    break;
                }
            }
            this.skipWhitespaceAndNewlines();
            if (!this.atEnd() && this.peek() === "(") {
                this.advance();
                this.skipWhitespaceAndNewlines();
            }
            var patternChars = [];
            var extglobDepth = 0;
            while (!this.atEnd()) {
                var ch = this.peek();
                if (ch === ")") {
                    if (extglobDepth > 0) {
                        patternChars.push(this.advance());
                        extglobDepth -= 1;
                    }
                    else {
                        this.advance();
                        break;
                    }
                }
                else {
                    if (ch === "\\") {
                        if (this.pos + 1 < this.length && this.source[this.pos + 1] === "\n") {
                            this.advance();
                            this.advance();
                        }
                        else {
                            patternChars.push(this.advance());
                            if (!this.atEnd()) {
                                patternChars.push(this.advance());
                            }
                        }
                    }
                    else {
                        if (IsExpansionStart(this.source, this.pos, "$(")) {
                            patternChars.push(this.advance());
                            patternChars.push(this.advance());
                            if (!this.atEnd() && this.peek() === "(") {
                                patternChars.push(this.advance());
                                var parenDepth = 2;
                                while (!this.atEnd() && parenDepth > 0) {
                                    var c = this.peek();
                                    if (c === "(") {
                                        parenDepth += 1;
                                    }
                                    else {
                                        if (c === ")") {
                                            parenDepth -= 1;
                                        }
                                    }
                                    patternChars.push(this.advance());
                                }
                            }
                            else {
                                extglobDepth += 1;
                            }
                        }
                        else {
                            if (ch === "(" && extglobDepth > 0) {
                                patternChars.push(this.advance());
                                extglobDepth += 1;
                            }
                            else {
                                if (this.Extglob && IsExtglobPrefix(ch) && this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
                                    patternChars.push(this.advance());
                                    patternChars.push(this.advance());
                                    extglobDepth += 1;
                                }
                                else {
                                    if (ch === "[") {
                                        var isCharClass = false;
                                        var scanPos = this.pos + 1;
                                        var scanDepth = 0;
                                        var hasFirstBracketLiteral = false;
                                        if (scanPos < this.length && IsCaretOrBang(this.source[scanPos])) {
                                            scanPos += 1;
                                        }
                                        if (scanPos < this.length && this.source[scanPos] === "]") {
                                            if (this.source.indexOf("]", scanPos + 1) !== -1) {
                                                scanPos += 1;
                                                hasFirstBracketLiteral = true;
                                            }
                                        }
                                        while (scanPos < this.length) {
                                            var sc = this.source[scanPos];
                                            if (sc === "]" && scanDepth === 0) {
                                                isCharClass = true;
                                                break;
                                            }
                                            else {
                                                if (sc === "[") {
                                                    scanDepth += 1;
                                                }
                                                else {
                                                    if (sc === ")" && scanDepth === 0) {
                                                        break;
                                                    }
                                                    else {
                                                        if (sc === "|" && scanDepth === 0) {
                                                            break;
                                                        }
                                                    }
                                                }
                                            }
                                            scanPos += 1;
                                        }
                                        if (isCharClass) {
                                            patternChars.push(this.advance());
                                            if (!this.atEnd() && IsCaretOrBang(this.peek())) {
                                                patternChars.push(this.advance());
                                            }
                                            if (hasFirstBracketLiteral && !this.atEnd() && this.peek() === "]") {
                                                patternChars.push(this.advance());
                                            }
                                            while (!this.atEnd() && this.peek() !== "]") {
                                                patternChars.push(this.advance());
                                            }
                                            if (!this.atEnd()) {
                                                patternChars.push(this.advance());
                                            }
                                        }
                                        else {
                                            patternChars.push(this.advance());
                                        }
                                    }
                                    else {
                                        if (ch === "'") {
                                            patternChars.push(this.advance());
                                            while (!this.atEnd() && this.peek() !== "'") {
                                                patternChars.push(this.advance());
                                            }
                                            if (!this.atEnd()) {
                                                patternChars.push(this.advance());
                                            }
                                        }
                                        else {
                                            if (ch === "\"") {
                                                patternChars.push(this.advance());
                                                while (!this.atEnd() && this.peek() !== "\"") {
                                                    if (this.peek() === "\\" && this.pos + 1 < this.length) {
                                                        patternChars.push(this.advance());
                                                    }
                                                    patternChars.push(this.advance());
                                                }
                                                if (!this.atEnd()) {
                                                    patternChars.push(this.advance());
                                                }
                                            }
                                            else {
                                                if (IsWhitespace(ch)) {
                                                    if (extglobDepth > 0) {
                                                        patternChars.push(this.advance());
                                                    }
                                                    else {
                                                        this.advance();
                                                    }
                                                }
                                                else {
                                                    patternChars.push(this.advance());
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            var pattern = patternChars.join("");
            if (!(pattern !== "")) {
                throw new Error("".concat("Expected pattern in case statement", " at position ").concat(this.LexPeekToken().pos));
            }
            this.skipWhitespace();
            var body = null;
            var isEmptyBody = this.LexPeekCaseTerminator() !== "";
            if (!isEmptyBody) {
                this.skipWhitespaceAndNewlines();
                if (!this.atEnd() && !this.LexIsAtReservedWord("esac")) {
                    var isAtTerminator = this.LexPeekCaseTerminator() !== "";
                    if (!isAtTerminator) {
                        body = this.parseListUntil(new Set(["esac"]));
                        this.skipWhitespace();
                    }
                }
            }
            var terminator = this.ConsumeCaseTerminator();
            this.skipWhitespaceAndNewlines();
            patterns.push(new CasePattern(pattern, body, terminator, "pattern"));
        }
        this.ClearState(ParserStateFlags_PST_CASEPAT);
        this.skipWhitespaceAndNewlines();
        if (!this.LexConsumeWord("esac")) {
            this.ClearState(ParserStateFlags_PST_CASESTMT);
            throw new Error("".concat("Expected 'esac' to close case statement", " at position ").concat(this.LexPeekToken().pos));
        }
        this.ClearState(ParserStateFlags_PST_CASESTMT);
        return new Case(word, patterns, this.CollectRedirects(), "case");
    };
    Parser.prototype.parseCoproc = function () {
        this.skipWhitespace();
        if (!this.LexConsumeWord("coproc")) {
            return null;
        }
        this.skipWhitespace();
        var name = "";
        var ch = "";
        if (!this.atEnd()) {
            ch = this.peek();
        }
        if (ch === "{") {
            var body = this.parseBraceGroup();
            if (body !== null) {
                return new Coproc(body, name, "coproc");
            }
        }
        if (ch === "(") {
            if (this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
                var body = this.parseArithmeticCommand();
                if (body !== null) {
                    return new Coproc(body, name, "coproc");
                }
            }
            var body = this.parseSubshell();
            if (body !== null) {
                return new Coproc(body, name, "coproc");
            }
        }
        var nextWord = this.LexPeekReservedWord();
        if (nextWord !== "" && COMPOUND_KEYWORDS.has(nextWord)) {
            var body = this.parseCompoundCommand();
            if (body !== null) {
                return new Coproc(body, name, "coproc");
            }
        }
        var wordStart = this.pos;
        var potentialName = this.peekWord();
        if (potentialName !== "") {
            while (!this.atEnd() && !IsMetachar(this.peek()) && !IsQuote(this.peek())) {
                this.advance();
            }
            this.skipWhitespace();
            ch = "";
            if (!this.atEnd()) {
                ch = this.peek();
            }
            nextWord = this.LexPeekReservedWord();
            if (IsValidIdentifier(potentialName)) {
                if (ch === "{") {
                    name = potentialName;
                    var body = this.parseBraceGroup();
                    if (body !== null) {
                        return new Coproc(body, name, "coproc");
                    }
                }
                else {
                    if (ch === "(") {
                        name = potentialName;
                        if (this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
                            var body = this.parseArithmeticCommand();
                        }
                        else {
                            var body = this.parseSubshell();
                        }
                        if (body !== null) {
                            return new Coproc(body, name, "coproc");
                        }
                    }
                    else {
                        if (nextWord !== "" && COMPOUND_KEYWORDS.has(nextWord)) {
                            name = potentialName;
                            var body = this.parseCompoundCommand();
                            if (body !== null) {
                                return new Coproc(body, name, "coproc");
                            }
                        }
                    }
                }
            }
            this.pos = wordStart;
        }
        var body = this.parseCommand();
        if (body !== null) {
            return new Coproc(body, name, "coproc");
        }
        throw new Error("".concat("Expected command after coproc", " at position ").concat(this.pos));
    };
    Parser.prototype.parseFunction = function () {
        this.skipWhitespace();
        if (this.atEnd()) {
            return null;
        }
        var savedPos = this.pos;
        if (this.LexIsAtReservedWord("function")) {
            this.LexConsumeWord("function");
            this.skipWhitespace();
            var name = this.peekWord();
            if (name === "") {
                this.pos = savedPos;
                return null;
            }
            this.consumeWord(name);
            this.skipWhitespace();
            if (!this.atEnd() && this.peek() === "(") {
                if (this.pos + 1 < this.length && this.source[this.pos + 1] === ")") {
                    this.advance();
                    this.advance();
                }
            }
            this.skipWhitespaceAndNewlines();
            var body = this.ParseCompoundCommand();
            if (body === null) {
                throw new Error("".concat("Expected function body", " at position ").concat(this.pos));
            }
            return new FunctionName(name, body, "function");
        }
        var name = this.peekWord();
        if (name === "" || RESERVED_WORDS.has(name)) {
            return null;
        }
        if (LooksLikeAssignment(name)) {
            return null;
        }
        this.skipWhitespace();
        var nameStart = this.pos;
        while (!this.atEnd() && !IsMetachar(this.peek()) && !IsQuote(this.peek()) && !IsParen(this.peek())) {
            this.advance();
        }
        name = Substring(this.source, nameStart, this.pos);
        if (!(name !== "")) {
            this.pos = savedPos;
            return null;
        }
        var braceDepth = 0;
        var i = 0;
        while (i < name.length) {
            if (IsExpansionStart(name, i, "${")) {
                braceDepth += 1;
                i += 2;
                continue;
            }
            if (name[i] === "}") {
                braceDepth -= 1;
            }
            i += 1;
        }
        if (braceDepth > 0) {
            this.pos = savedPos;
            return null;
        }
        var posAfterName = this.pos;
        this.skipWhitespace();
        var hasWhitespace = this.pos > posAfterName;
        if (!hasWhitespace && name !== "" && "*?@+!$".includes(name[name.length - 1])) {
            this.pos = savedPos;
            return null;
        }
        if (this.atEnd() || this.peek() !== "(") {
            this.pos = savedPos;
            return null;
        }
        this.advance();
        this.skipWhitespace();
        if (this.atEnd() || this.peek() !== ")") {
            this.pos = savedPos;
            return null;
        }
        this.advance();
        this.skipWhitespaceAndNewlines();
        var body = this.ParseCompoundCommand();
        if (body === null) {
            throw new Error("".concat("Expected function body", " at position ").concat(this.pos));
        }
        return new FunctionName(name, body, "function");
    };
    Parser.prototype.ParseCompoundCommand = function () {
        var result = this.parseBraceGroup();
        if (result !== null) {
            return result;
        }
        if (!this.atEnd() && this.peek() === "(" && this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
            result = this.parseArithmeticCommand();
            if (result !== null) {
                return result;
            }
        }
        result = this.parseSubshell();
        if (result !== null) {
            return result;
        }
        result = this.parseConditionalExpr();
        if (result !== null) {
            return result;
        }
        result = this.parseIf();
        if (result !== null) {
            return result;
        }
        result = this.parseWhile();
        if (result !== null) {
            return result;
        }
        result = this.parseUntil();
        if (result !== null) {
            return result;
        }
        result = this.parseFor();
        if (result !== null) {
            return result;
        }
        result = this.parseCase();
        if (result !== null) {
            return result;
        }
        result = this.parseSelect();
        if (result !== null) {
            return result;
        }
        return null;
    };
    Parser.prototype.AtListUntilTerminator = function (stopWords) {
        if (this.atEnd()) {
            return true;
        }
        if (this.peek() === ")") {
            return true;
        }
        if (this.peek() === "}") {
            var nextPos = this.pos + 1;
            if (nextPos >= this.length || IsWordEndContext(this.source[nextPos])) {
                return true;
            }
        }
        var reserved = this.LexPeekReservedWord();
        if (reserved !== "" && stopWords.has(reserved)) {
            return true;
        }
        if (this.LexPeekCaseTerminator() !== "") {
            return true;
        }
        return false;
    };
    Parser.prototype.parseListUntil = function (stopWords) {
        this.skipWhitespaceAndNewlines();
        var reserved = this.LexPeekReservedWord();
        if (reserved !== "" && stopWords.has(reserved)) {
            return null;
        }
        var pipeline = this.parsePipeline();
        if (pipeline === null) {
            return null;
        }
        var parts = [pipeline];
        while (true) {
            this.skipWhitespace();
            var op = this.parseListOperator();
            if (op === "") {
                if (!this.atEnd() && this.peek() === "\n") {
                    this.advance();
                    this.GatherHeredocBodies();
                    if (this.CmdsubHeredocEnd !== -1 && this.CmdsubHeredocEnd > this.pos) {
                        this.pos = this.CmdsubHeredocEnd;
                        this.CmdsubHeredocEnd = -1;
                    }
                    this.skipWhitespaceAndNewlines();
                    if (this.AtListUntilTerminator(stopWords)) {
                        break;
                    }
                    var nextOp = this.PeekListOperator();
                    if (nextOp === "&" || nextOp === ";") {
                        break;
                    }
                    op = "\n";
                }
                else {
                    break;
                }
            }
            if (op === "") {
                break;
            }
            if (op === ";") {
                this.skipWhitespaceAndNewlines();
                if (this.AtListUntilTerminator(stopWords)) {
                    break;
                }
                parts.push(new Operator(op, "operator"));
            }
            else {
                if (op === "&") {
                    parts.push(new Operator(op, "operator"));
                    this.skipWhitespaceAndNewlines();
                    if (this.AtListUntilTerminator(stopWords)) {
                        break;
                    }
                }
                else {
                    if (op === "&&" || op === "||") {
                        parts.push(new Operator(op, "operator"));
                        this.skipWhitespaceAndNewlines();
                    }
                    else {
                        parts.push(new Operator(op, "operator"));
                    }
                }
            }
            if (this.AtListUntilTerminator(stopWords)) {
                break;
            }
            pipeline = this.parsePipeline();
            if (pipeline === null) {
                throw new Error("".concat("Expected command after " + op, " at position ").concat(this.pos));
            }
            parts.push(pipeline);
        }
        if (parts.length === 1) {
            return parts[0];
        }
        return new List(parts, "list");
    };
    Parser.prototype.parseCompoundCommand = function () {
        this.skipWhitespace();
        if (this.atEnd()) {
            return null;
        }
        var ch = this.peek();
        if (ch === "(" && this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
            var result = this.parseArithmeticCommand();
            if (result !== null) {
                return result;
            }
        }
        if (ch === "(") {
            return this.parseSubshell();
        }
        if (ch === "{") {
            var result = this.parseBraceGroup();
            if (result !== null) {
                return result;
            }
        }
        if (ch === "[" && this.pos + 1 < this.length && this.source[this.pos + 1] === "[") {
            var result = this.parseConditionalExpr();
            if (result !== null) {
                return result;
            }
        }
        var reserved = this.LexPeekReservedWord();
        if (reserved === "" && this.InProcessSub) {
            var word = this.peekWord();
            if (word !== "" && word.length > 1 && word[0] === "}") {
                var keywordWord = word.slice(1);
                if (RESERVED_WORDS.has(keywordWord) || (keywordWord === "{" || keywordWord === "}" || keywordWord === "[[" || keywordWord === "]]" || keywordWord === "!" || keywordWord === "time")) {
                    reserved = keywordWord;
                }
            }
        }
        if (reserved === "fi" || reserved === "then" || reserved === "elif" || reserved === "else" || reserved === "done" || reserved === "esac" || reserved === "do" || reserved === "in") {
            throw new Error("".concat("Unexpected reserved word '".concat(reserved, "'"), " at position ").concat(this.LexPeekToken().pos));
        }
        if (reserved === "if") {
            return this.parseIf();
        }
        if (reserved === "while") {
            return this.parseWhile();
        }
        if (reserved === "until") {
            return this.parseUntil();
        }
        if (reserved === "for") {
            return this.parseFor();
        }
        if (reserved === "select") {
            return this.parseSelect();
        }
        if (reserved === "case") {
            return this.parseCase();
        }
        if (reserved === "function") {
            return this.parseFunction();
        }
        if (reserved === "coproc") {
            return this.parseCoproc();
        }
        var func = this.parseFunction();
        if (func !== null) {
            return func;
        }
        return this.parseCommand();
    };
    Parser.prototype.parsePipeline = function () {
        this.skipWhitespace();
        var prefixOrder = "";
        var timePosix = false;
        if (this.LexIsAtReservedWord("time")) {
            this.LexConsumeWord("time");
            prefixOrder = "time";
            this.skipWhitespace();
            if (!this.atEnd() && this.peek() === "-") {
                var saved = this.pos;
                this.advance();
                if (!this.atEnd() && this.peek() === "p") {
                    this.advance();
                    if (this.atEnd() || IsMetachar(this.peek())) {
                        timePosix = true;
                    }
                    else {
                        this.pos = saved;
                    }
                }
                else {
                    this.pos = saved;
                }
            }
            this.skipWhitespace();
            if (!this.atEnd() && StartsWithAt(this.source, this.pos, "--")) {
                if (this.pos + 2 >= this.length || IsWhitespace(this.source[this.pos + 2])) {
                    this.advance();
                    this.advance();
                    timePosix = true;
                    this.skipWhitespace();
                }
            }
            while (this.LexIsAtReservedWord("time")) {
                this.LexConsumeWord("time");
                this.skipWhitespace();
                if (!this.atEnd() && this.peek() === "-") {
                    var saved = this.pos;
                    this.advance();
                    if (!this.atEnd() && this.peek() === "p") {
                        this.advance();
                        if (this.atEnd() || IsMetachar(this.peek())) {
                            timePosix = true;
                        }
                        else {
                            this.pos = saved;
                        }
                    }
                    else {
                        this.pos = saved;
                    }
                }
            }
            this.skipWhitespace();
            if (!this.atEnd() && this.peek() === "!") {
                if ((this.pos + 1 >= this.length || IsNegationBoundary(this.source[this.pos + 1])) && !this.IsBangFollowedByProcsub()) {
                    this.advance();
                    prefixOrder = "time_negation";
                    this.skipWhitespace();
                }
            }
        }
        else {
            if (!this.atEnd() && this.peek() === "!") {
                if ((this.pos + 1 >= this.length || IsNegationBoundary(this.source[this.pos + 1])) && !this.IsBangFollowedByProcsub()) {
                    this.advance();
                    this.skipWhitespace();
                    var inner = this.parsePipeline();
                    if (inner !== null && inner.kind === "negation") {
                        if (inner.pipeline !== null) {
                            return inner.pipeline;
                        }
                        else {
                            return new Command([], [], "command");
                        }
                    }
                    return new Negation(inner, "negation");
                }
            }
        }
        var result = this.ParseSimplePipeline();
        if (prefixOrder === "time") {
            result = new Time(result, timePosix, "time");
        }
        else {
            if (prefixOrder === "negation") {
                result = new Negation(result, "negation");
            }
            else {
                if (prefixOrder === "time_negation") {
                    result = new Time(result, timePosix, "time");
                    result = new Negation(result, "negation");
                }
                else {
                    if (prefixOrder === "negation_time") {
                        result = new Time(result, timePosix, "time");
                        result = new Negation(result, "negation");
                    }
                    else {
                        if (result === null) {
                            return null;
                        }
                    }
                }
            }
        }
        return result;
    };
    Parser.prototype.ParseSimplePipeline = function () {
        var cmd = this.parseCompoundCommand();
        if (cmd === null) {
            return null;
        }
        var commands = [cmd];
        while (true) {
            this.skipWhitespace();
            var _a = this.LexPeekOperator(), tokenType = _a[0], value = _a[1];
            if (tokenType === 0) {
                break;
            }
            if (tokenType !== TokenType_PIPE && tokenType !== TokenType_PIPE_AMP) {
                break;
            }
            this.LexNextToken();
            var isPipeBoth = tokenType === TokenType_PIPE_AMP;
            this.skipWhitespaceAndNewlines();
            if (isPipeBoth) {
                commands.push(new PipeBoth("pipe-both"));
            }
            cmd = this.parseCompoundCommand();
            if (cmd === null) {
                throw new Error("".concat("Expected command after |", " at position ").concat(this.pos));
            }
            commands.push(cmd);
        }
        if (commands.length === 1) {
            return commands[0];
        }
        return new Pipeline(commands, "pipeline");
    };
    Parser.prototype.parseListOperator = function () {
        this.skipWhitespace();
        var tokenType = this.LexPeekOperator()[0];
        if (tokenType === 0) {
            return "";
        }
        if (tokenType === TokenType_AND_AND) {
            this.LexNextToken();
            return "&&";
        }
        if (tokenType === TokenType_OR_OR) {
            this.LexNextToken();
            return "||";
        }
        if (tokenType === TokenType_SEMI) {
            this.LexNextToken();
            return ";";
        }
        if (tokenType === TokenType_AMP) {
            this.LexNextToken();
            return "&";
        }
        return "";
    };
    Parser.prototype.PeekListOperator = function () {
        var savedPos = this.pos;
        var op = this.parseListOperator();
        this.pos = savedPos;
        return op;
    };
    Parser.prototype.parseList = function (newlineAsSeparator) {
        if (newlineAsSeparator) {
            this.skipWhitespaceAndNewlines();
        }
        else {
            this.skipWhitespace();
        }
        var pipeline = this.parsePipeline();
        if (pipeline === null) {
            return null;
        }
        var parts = [pipeline];
        if (this.InState(ParserStateFlags_PST_EOFTOKEN) && this.AtEofToken()) {
            return parts.length === 1 ? parts[0] : new List(parts, "list");
        }
        while (true) {
            this.skipWhitespace();
            var op = this.parseListOperator();
            if (op === "") {
                if (!this.atEnd() && this.peek() === "\n") {
                    if (!newlineAsSeparator) {
                        break;
                    }
                    this.advance();
                    this.GatherHeredocBodies();
                    if (this.CmdsubHeredocEnd !== -1 && this.CmdsubHeredocEnd > this.pos) {
                        this.pos = this.CmdsubHeredocEnd;
                        this.CmdsubHeredocEnd = -1;
                    }
                    this.skipWhitespaceAndNewlines();
                    if (this.atEnd() || this.AtListTerminatingBracket()) {
                        break;
                    }
                    var nextOp = this.PeekListOperator();
                    if (nextOp === "&" || nextOp === ";") {
                        break;
                    }
                    op = "\n";
                }
                else {
                    break;
                }
            }
            if (op === "") {
                break;
            }
            parts.push(new Operator(op, "operator"));
            if (op === "&&" || op === "||") {
                this.skipWhitespaceAndNewlines();
            }
            else {
                if (op === "&") {
                    this.skipWhitespace();
                    if (this.atEnd() || this.AtListTerminatingBracket()) {
                        break;
                    }
                    if (this.peek() === "\n") {
                        if (newlineAsSeparator) {
                            this.skipWhitespaceAndNewlines();
                            if (this.atEnd() || this.AtListTerminatingBracket()) {
                                break;
                            }
                        }
                        else {
                            break;
                        }
                    }
                }
                else {
                    if (op === ";") {
                        this.skipWhitespace();
                        if (this.atEnd() || this.AtListTerminatingBracket()) {
                            break;
                        }
                        if (this.peek() === "\n") {
                            if (newlineAsSeparator) {
                                this.skipWhitespaceAndNewlines();
                                if (this.atEnd() || this.AtListTerminatingBracket()) {
                                    break;
                                }
                            }
                            else {
                                break;
                            }
                        }
                    }
                }
            }
            pipeline = this.parsePipeline();
            if (pipeline === null) {
                throw new Error("".concat("Expected command after " + op, " at position ").concat(this.pos));
            }
            parts.push(pipeline);
            if (this.InState(ParserStateFlags_PST_EOFTOKEN) && this.AtEofToken()) {
                break;
            }
        }
        if (parts.length === 1) {
            return parts[0];
        }
        return new List(parts, "list");
    };
    Parser.prototype.parseComment = function () {
        if (this.atEnd() || this.peek() !== "#") {
            return null;
        }
        var start = this.pos;
        while (!this.atEnd() && this.peek() !== "\n") {
            this.advance();
        }
        var text = Substring(this.source, start, this.pos);
        return new Comment(text, "comment");
    };
    Parser.prototype.parse = function () {
        var source = this.source.trim();
        if (!(source !== "")) {
            return [new Empty("empty")];
        }
        var results = [];
        while (true) {
            this.skipWhitespace();
            while (!this.atEnd() && this.peek() === "\n") {
                this.advance();
            }
            if (this.atEnd()) {
                break;
            }
            var comment = this.parseComment();
            if (!comment !== null) {
                break;
            }
        }
        while (!this.atEnd()) {
            var result = this.parseList(false);
            if (result !== null) {
                results.push(result);
            }
            this.skipWhitespace();
            var foundNewline = false;
            while (!this.atEnd() && this.peek() === "\n") {
                foundNewline = true;
                this.advance();
                this.GatherHeredocBodies();
                if (this.CmdsubHeredocEnd !== -1 && this.CmdsubHeredocEnd > this.pos) {
                    this.pos = this.CmdsubHeredocEnd;
                    this.CmdsubHeredocEnd = -1;
                }
                this.skipWhitespace();
            }
            if (!foundNewline && !this.atEnd()) {
                throw new Error("".concat("Syntax error", " at position ").concat(this.pos));
            }
        }
        if (!(results.length > 0)) {
            return [new Empty("empty")];
        }
        if (this.SawNewlineInSingleQuote && this.source !== "" && this.source[this.source.length - 1] === "\\" && !(this.source.length >= 3 && this.source.slice(this.source.length - 3, this.source.length - 1) === "\\\n")) {
            if (!this.LastWordOnOwnLine(results)) {
                this.StripTrailingBackslashFromLastWord(results);
            }
        }
        return results;
    };
    Parser.prototype.LastWordOnOwnLine = function (nodes) {
        return nodes.length >= 2;
    };
    Parser.prototype.StripTrailingBackslashFromLastWord = function (nodes) {
        if (!(nodes.length > 0)) {
            return;
        }
        var lastNode = nodes[nodes.length - 1];
        var lastWord = this.FindLastWord(lastNode);
        if (lastWord !== null && lastWord.value.endsWith("\\")) {
            lastWord.value = Substring(lastWord.value, 0, lastWord.value.length - 1);
            if (!(lastWord.value !== "") && lastNode instanceof Command && lastNode.words.length > 0) {
                lastNode.words.pop();
            }
        }
    };
    Parser.prototype.FindLastWord = function (node) {
        if (node instanceof Word) {
            return node;
        }
        if (node instanceof Command) {
            if (node.words.length > 0) {
                var lastWord = node.words[node.words.length - 1];
                if (lastWord.value.endsWith("\\")) {
                    return lastWord;
                }
            }
            if (node.redirects.length > 0) {
                var lastRedirect = node.redirects[node.redirects.length - 1];
                if (lastRedirect instanceof Redirect) {
                    return lastRedirect.target;
                }
            }
            if (node.words.length > 0) {
                return node.words[node.words.length - 1];
            }
        }
        if (node instanceof Pipeline) {
            if (node.commands.length > 0) {
                return this.FindLastWord(node.commands[node.commands.length - 1]);
            }
        }
        if (node instanceof List) {
            if (node.parts.length > 0) {
                return this.FindLastWord(node.parts[node.parts.length - 1]);
            }
        }
        return null;
    };
    return Parser;
}());
function IsHexDigit(c) {
    return c >= "0" && c <= "9" || c >= "a" && c <= "f" || c >= "A" && c <= "F";
}
function IsOctalDigit(c) {
    return c >= "0" && c <= "7";
}
function GetAnsiEscape(c) {
    var _a;
    return (_a = ANSI_C_ESCAPES.get(c)) !== null && _a !== void 0 ? _a : -1;
}
function IsWhitespace(c) {
    return c === " " || c === "\t" || c === "\n";
}
function IsWhitespaceNoNewline(c) {
    return c === " " || c === "\t";
}
function Substring(s, start, end) {
    if (end > s.length) {
        end = s.length;
    }
    return s.slice(start, end);
}
function StartsWithAt(s, pos, prefix) {
    return s.startsWith(prefix, pos);
}
function CountConsecutiveDollarsBefore(s, pos) {
    var count = 0;
    var k = pos - 1;
    while (k >= 0 && s[k] === "$") {
        var bsCount = 0;
        var j = k - 1;
        while (j >= 0 && s[j] === "\\") {
            bsCount += 1;
            j -= 1;
        }
        if (bsCount % 2 === 1) {
            break;
        }
        count += 1;
        k -= 1;
    }
    return count;
}
function IsExpansionStart(s, pos, delimiter) {
    if (!StartsWithAt(s, pos, delimiter)) {
        return false;
    }
    return CountConsecutiveDollarsBefore(s, pos) % 2 === 0;
}
function Sublist(lst, start, end) {
    return lst.slice(start, end);
}
function RepeatStr(s, n) {
    var result = [];
    var i = 0;
    while (i < n) {
        result.push(s);
        i += 1;
    }
    return result.join("");
}
function StripLineContinuationsCommentAware(text) {
    var result = [];
    var i = 0;
    var inComment = false;
    var quote = newQuoteState();
    while (i < text.length) {
        var c = text[i];
        if (c === "\\" && i + 1 < text.length && text[i + 1] === "\n") {
            var numPrecedingBackslashes = 0;
            var j = i - 1;
            while (j >= 0 && text[j] === "\\") {
                numPrecedingBackslashes += 1;
                j -= 1;
            }
            if (numPrecedingBackslashes % 2 === 0) {
                if (inComment) {
                    result.push("\n");
                }
                i += 2;
                inComment = false;
                continue;
            }
        }
        if (c === "\n") {
            inComment = false;
            result.push(c);
            i += 1;
            continue;
        }
        if (c === "'" && !quote.double && !inComment) {
            quote.single = !quote.single;
        }
        else {
            if (c === "\"" && !quote.single && !inComment) {
                quote.double = !quote.double;
            }
            else {
                if (c === "#" && !quote.single && !inComment) {
                    inComment = true;
                }
            }
        }
        result.push(c);
        i += 1;
    }
    return result.join("");
}
function AppendRedirects(base, redirects) {
    if (redirects.length > 0) {
        var parts = [];
        for (var _i = 0, redirects_1 = redirects; _i < redirects_1.length; _i++) {
            var r = redirects_1[_i];
            parts.push(r.toSexp());
        }
        return base + " " + parts.join(" ");
    }
    return base;
}
function FormatArithVal(s) {
    var w = new Word(s, [], "word");
    var val = w.ExpandAllAnsiCQuotes(s);
    val = w.StripLocaleStringDollars(val);
    val = w.FormatCommandSubstitutions(val, false);
    val = val.replace(/\\/g, "\\\\").replace(/"/g, "\\\"");
    val = val.replace(/\n/g, "\\n").replace(/\t/g, "\\t");
    return val;
}
function ConsumeSingleQuote(s, start) {
    var chars = ["'"];
    var i = start + 1;
    while (i < s.length && s[i] !== "'") {
        chars.push(s[i]);
        i += 1;
    }
    if (i < s.length) {
        chars.push(s[i]);
        i += 1;
    }
    return [i, chars];
}
function ConsumeDoubleQuote(s, start) {
    var chars = ["\""];
    var i = start + 1;
    while (i < s.length && s[i] !== "\"") {
        if (s[i] === "\\" && i + 1 < s.length) {
            chars.push(s[i]);
            i += 1;
        }
        chars.push(s[i]);
        i += 1;
    }
    if (i < s.length) {
        chars.push(s[i]);
        i += 1;
    }
    return [i, chars];
}
function HasBracketClose(s, start, depth) {
    var i = start;
    while (i < s.length) {
        if (s[i] === "]") {
            return true;
        }
        if ((s[i] === "|" || s[i] === ")") && depth === 0) {
            return false;
        }
        i += 1;
    }
    return false;
}
function ConsumeBracketClass(s, start, depth) {
    var scanPos = start + 1;
    if (scanPos < s.length && (s[scanPos] === "!" || s[scanPos] === "^")) {
        scanPos += 1;
    }
    if (scanPos < s.length && s[scanPos] === "]") {
        if (HasBracketClose(s, scanPos + 1, depth)) {
            scanPos += 1;
        }
    }
    var isBracket = false;
    while (scanPos < s.length) {
        if (s[scanPos] === "]") {
            isBracket = true;
            break;
        }
        if (s[scanPos] === ")" && depth === 0) {
            break;
        }
        if (s[scanPos] === "|" && depth === 0) {
            break;
        }
        scanPos += 1;
    }
    if (!isBracket) {
        return [start + 1, ["["], false];
    }
    var chars = ["["];
    var i = start + 1;
    if (i < s.length && (s[i] === "!" || s[i] === "^")) {
        chars.push(s[i]);
        i += 1;
    }
    if (i < s.length && s[i] === "]") {
        if (HasBracketClose(s, i + 1, depth)) {
            chars.push(s[i]);
            i += 1;
        }
    }
    while (i < s.length && s[i] !== "]") {
        chars.push(s[i]);
        i += 1;
    }
    if (i < s.length) {
        chars.push(s[i]);
        i += 1;
    }
    return [i, chars, true];
}
function FormatCondBody(node) {
    var kind = node.kind;
    if (kind === "unary-test") {
        var operandVal = node.operand.getCondFormattedValue();
        return node.op + " " + operandVal;
    }
    if (kind === "binary-test") {
        var leftVal = node.left.getCondFormattedValue();
        var rightVal = node.right.getCondFormattedValue();
        return leftVal + " " + node.op + " " + rightVal;
    }
    if (kind === "cond-and") {
        return FormatCondBody(node.left) + " && " + FormatCondBody(node.right);
    }
    if (kind === "cond-or") {
        return FormatCondBody(node.left) + " || " + FormatCondBody(node.right);
    }
    if (kind === "cond-not") {
        return "! " + FormatCondBody(node.operand);
    }
    if (kind === "cond-paren") {
        return "( " + FormatCondBody(node.inner) + " )";
    }
    return "";
}
function StartsWithSubshell(node) {
    if (node instanceof Subshell) {
        return true;
    }
    if (node instanceof List) {
        for (var _i = 0, _a = node.parts; _i < _a.length; _i++) {
            var p = _a[_i];
            if (p.kind !== "operator") {
                return StartsWithSubshell(p);
            }
        }
        return false;
    }
    if (node instanceof Pipeline) {
        if (node.commands.length > 0) {
            return StartsWithSubshell(node.commands[0]);
        }
        return false;
    }
    return false;
}
function FormatCmdsubNode(node, indent, inProcsub, compactRedirects, procsubFirst) {
    if (node === null) {
        return "";
    }
    var sp = RepeatStr(" ", indent);
    var innerSp = RepeatStr(" ", indent + 4);
    if (node instanceof ArithEmpty) {
        return "";
    }
    if (node instanceof Command) {
        var parts = [];
        for (var _i = 0, _a = node.words; _i < _a.length; _i++) {
            var w = _a[_i];
            var val = w.ExpandAllAnsiCQuotes(w.value);
            val = w.StripLocaleStringDollars(val);
            val = w.NormalizeArrayWhitespace(val);
            val = w.FormatCommandSubstitutions(val, false);
            parts.push(val);
        }
        var heredocs = [];
        for (var _b = 0, _c = node.redirects; _b < _c.length; _b++) {
            var r = _c[_b];
            if (r instanceof HereDoc) {
                heredocs.push(r);
            }
        }
        for (var _d = 0, _f = node.redirects; _d < _f.length; _d++) {
            var r = _f[_d];
            parts.push(FormatRedirect(r, compactRedirects, true));
        }
        if (compactRedirects && node.words.length > 0 && node.redirects.length > 0) {
            var wordParts = parts.slice(0, node.words.length);
            var redirectParts = parts.slice(node.words.length);
            var result = wordParts.join(" ") + redirectParts.join("");
        }
        else {
            var result = parts.join(" ");
        }
        for (var _g = 0, heredocs_1 = heredocs; _g < heredocs_1.length; _g++) {
            var h = heredocs_1[_g];
            var result = result + FormatHeredocBody(h);
        }
        return result;
    }
    if (node instanceof Pipeline) {
        var cmds = [];
        var i = 0;
        while (i < node.commands.length) {
            var cmd = node.commands[i];
            if (cmd instanceof PipeBoth) {
                i += 1;
                continue;
            }
            var needsRedirect = i + 1 < node.commands.length && node.commands[i + 1].kind === "pipe-both";
            cmds.push([cmd, needsRedirect]);
            i += 1;
        }
        var resultParts = [];
        var idx = 0;
        while (idx < cmds.length) {
            {
                var Entry = cmds[idx];
                cmd = Entry[0];
                needsRedirect = Entry[1];
            }
            var formatted = FormatCmdsubNode(cmd, indent, inProcsub, false, procsubFirst && idx === 0);
            var isLast = idx === cmds.length - 1;
            var hasHeredoc = false;
            if (cmd.kind === "command" && cmd.redirects.length > 0) {
                for (var _h = 0, _j = cmd.redirects; _h < _j.length; _h++) {
                    var r = _j[_h];
                    if (r instanceof HereDoc) {
                        hasHeredoc = true;
                        break;
                    }
                }
            }
            if (needsRedirect) {
                if (hasHeredoc) {
                    var firstNl = formatted.indexOf("\n");
                    if (firstNl !== -1) {
                        formatted = formatted.slice(0, firstNl) + " 2>&1" + formatted.slice(firstNl);
                    }
                    else {
                        formatted = formatted + " 2>&1";
                    }
                }
                else {
                    formatted = formatted + " 2>&1";
                }
            }
            if (!isLast && hasHeredoc) {
                var firstNl = formatted.indexOf("\n");
                if (firstNl !== -1) {
                    formatted = formatted.slice(0, firstNl) + " |" + formatted.slice(firstNl);
                }
                resultParts.push(formatted);
            }
            else {
                resultParts.push(formatted);
            }
            idx += 1;
        }
        var compactPipe = inProcsub && cmds.length > 0 && cmds[0][0].kind === "subshell";
        var result = "";
        idx = 0;
        while (idx < resultParts.length) {
            var part = resultParts[idx];
            if (idx > 0) {
                if (result.endsWith("\n")) {
                    result = result + "  " + part;
                }
                else {
                    if (compactPipe) {
                        result = result + "|" + part;
                    }
                    else {
                        result = result + " | " + part;
                    }
                }
            }
            else {
                result = part;
            }
            idx += 1;
        }
        return result;
    }
    if (node instanceof List) {
        var hasHeredoc = false;
        for (var _k = 0, _l = node.parts; _k < _l.length; _k++) {
            var p_1 = _l[_k];
            if (p_1.kind === "command" && p_1.redirects.length > 0) {
                for (var _m = 0, _o = p_1.redirects; _m < _o.length; _m++) {
                    var r = _o[_m];
                    if (r instanceof HereDoc) {
                        hasHeredoc = true;
                        break;
                    }
                }
            }
            else {
                if (p_1 instanceof Pipeline) {
                    for (var _p = 0, _q = p_1.commands; _p < _q.length; _p++) {
                        var cmd_1 = _q[_p];
                        if (cmd_1.kind === "command" && cmd_1.redirects.length > 0) {
                            for (var _r = 0, _s = cmd_1.redirects; _r < _s.length; _r++) {
                                var r = _s[_r];
                                if (r instanceof HereDoc) {
                                    hasHeredoc = true;
                                    break;
                                }
                            }
                        }
                        if (hasHeredoc) {
                            break;
                        }
                    }
                }
            }
        }
        var result = [];
        var skippedSemi = false;
        var cmdCount = 0;
        for (var _t = 0, _u = node.parts; _t < _u.length; _t++) {
            var p_2 = _u[_t];
            if (p_2 instanceof Operator) {
                if (p_2.op === ";") {
                    if (result.length > 0 && result[result.length - 1].endsWith("\n")) {
                        skippedSemi = true;
                        continue;
                    }
                    if (result.length >= 3 && result[result.length - 2] === "\n" && result[result.length - 3].endsWith("\n")) {
                        skippedSemi = true;
                        continue;
                    }
                    result.push(";");
                    skippedSemi = false;
                }
                else {
                    if (p_2.op === "\n") {
                        if (result.length > 0 && result[result.length - 1] === ";") {
                            skippedSemi = false;
                            continue;
                        }
                        if (result.length > 0 && result[result.length - 1].endsWith("\n")) {
                            result.push(skippedSemi ? " " : "\n");
                            skippedSemi = false;
                            continue;
                        }
                        result.push("\n");
                        skippedSemi = false;
                    }
                    else {
                        if (p_2.op === "&") {
                            if (result.length > 0 && result[result.length - 1].includes("<<") && result[result.length - 1].includes("\n")) {
                                var last = result[result.length - 1];
                                if (last.includes(" |") || last.startsWith("|")) {
                                    result[result.length - 1] = last + " &";
                                }
                                else {
                                    var firstNl = last.indexOf("\n");
                                    result[result.length - 1] = last.slice(0, firstNl) + " &" + last.slice(firstNl);
                                }
                            }
                            else {
                                result.push(" &");
                            }
                        }
                        else {
                            if (result.length > 0 && result[result.length - 1].includes("<<") && result[result.length - 1].includes("\n")) {
                                var last = result[result.length - 1];
                                var firstNl = last.indexOf("\n");
                                result[result.length - 1] = last.slice(0, firstNl) + " " + p_2.op + " " + last.slice(firstNl);
                            }
                            else {
                                result.push(" " + p_2.op);
                            }
                        }
                    }
                }
            }
            else {
                if (result.length > 0 && !(result[result.length - 1].endsWith(" ") || result[result.length - 1].endsWith("\n"))) {
                    result.push(" ");
                }
                var formattedCmd = FormatCmdsubNode(p_2, indent, inProcsub, compactRedirects, procsubFirst && cmdCount === 0);
                if (result.length > 0) {
                    var last = result[result.length - 1];
                    if (last.includes(" || \n") || last.includes(" && \n")) {
                        formattedCmd = " " + formattedCmd;
                    }
                }
                if (skippedSemi) {
                    formattedCmd = " " + formattedCmd;
                    skippedSemi = false;
                }
                result.push(formattedCmd);
                cmdCount += 1;
            }
        }
        var s = result.join("");
        if (s.includes(" &\n") && s.endsWith("\n")) {
            return s + " ";
        }
        while (s.endsWith(";")) {
            s = Substring(s, 0, s.length - 1);
        }
        if (!hasHeredoc) {
            while (s.endsWith("\n")) {
                s = Substring(s, 0, s.length - 1);
            }
        }
        return s;
    }
    if (node instanceof If) {
        var cond = FormatCmdsubNode(node.condition, indent, false, false, false);
        var thenBody = FormatCmdsubNode(node.thenBody, indent + 4, false, false, false);
        var result = "if " + cond + "; then\n" + innerSp + thenBody + ";";
        if (node.elseBody !== null) {
            var elseBody = FormatCmdsubNode(node.elseBody, indent + 4, false, false, false);
            result = result + "\n" + sp + "else\n" + innerSp + elseBody + ";";
        }
        result = result + "\n" + sp + "fi";
        return result;
    }
    if (node instanceof While) {
        var cond = FormatCmdsubNode(node.condition, indent, false, false, false);
        var body = FormatCmdsubNode(node.body, indent + 4, false, false, false);
        var result = "while " + cond + "; do\n" + innerSp + body + ";\n" + sp + "done";
        if (node.redirects.length > 0) {
            for (var _v = 0, _w = node.redirects; _v < _w.length; _v++) {
                var r = _w[_v];
                result = result + " " + FormatRedirect(r, false, false);
            }
        }
        return result;
    }
    if (node instanceof Until) {
        var cond = FormatCmdsubNode(node.condition, indent, false, false, false);
        var body = FormatCmdsubNode(node.body, indent + 4, false, false, false);
        var result = "until " + cond + "; do\n" + innerSp + body + ";\n" + sp + "done";
        if (node.redirects.length > 0) {
            for (var _x = 0, _y = node.redirects; _x < _y.length; _x++) {
                var r = _y[_x];
                result = result + " " + FormatRedirect(r, false, false);
            }
        }
        return result;
    }
    if (node instanceof For) {
        var varName = node.varName;
        var body = FormatCmdsubNode(node.body, indent + 4, false, false, false);
        if (node.words !== null) {
            var wordVals = [];
            for (var _z = 0, _0 = node.words; _z < _0.length; _z++) {
                var w = _0[_z];
                wordVals.push(w.value);
            }
            var words = wordVals.join(" ");
            if (words !== "") {
                var result = "for " + varName + " in " + words + ";\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done";
            }
            else {
                var result = "for " + varName + " in ;\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done";
            }
        }
        else {
            var result = "for " + varName + " in \"$@\";\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done";
        }
        if (node.redirects.length > 0) {
            for (var _1 = 0, _2 = node.redirects; _1 < _2.length; _1++) {
                var r = _2[_1];
                var result = result + " " + FormatRedirect(r, false, false);
            }
        }
        return result;
    }
    if (node instanceof ForArith) {
        var body = FormatCmdsubNode(node.body, indent + 4, false, false, false);
        var result = "for ((" + node.init + "; " + node.cond + "; " + node.incr + "))\ndo\n" + innerSp + body + ";\n" + sp + "done";
        if (node.redirects.length > 0) {
            for (var _3 = 0, _4 = node.redirects; _3 < _4.length; _3++) {
                var r = _4[_3];
                result = result + " " + FormatRedirect(r, false, false);
            }
        }
        return result;
    }
    if (node instanceof Case) {
        var word = node.word.value;
        var patterns = [];
        var i = 0;
        while (i < node.patterns.length) {
            var p = node.patterns[i];
            var pat = p.pattern.replace(/\|/g, " | ");
            if (p.body !== null) {
                var body = FormatCmdsubNode(p.body, indent + 8, false, false, false);
            }
            else {
                var body = "";
            }
            var term = p.terminator;
            var patIndent = RepeatStr(" ", indent + 8);
            var termIndent = RepeatStr(" ", indent + 4);
            var bodyPart = body !== "" ? patIndent + body + "\n" : "\n";
            if (i === 0) {
                patterns.push(" " + pat + ")\n" + bodyPart + termIndent + term);
            }
            else {
                patterns.push(pat + ")\n" + bodyPart + termIndent + term);
            }
            i += 1;
        }
        var patternStr = patterns.join("\n" + RepeatStr(" ", indent + 4));
        var redirects = "";
        if (node.redirects.length > 0) {
            var redirectParts = [];
            for (var _5 = 0, _6 = node.redirects; _5 < _6.length; _5++) {
                var r = _6[_5];
                redirectParts.push(FormatRedirect(r, false, false));
            }
            redirects = " " + redirectParts.join(" ");
        }
        return "case " + word + " in" + patternStr + "\n" + sp + "esac" + redirects;
    }
    if (node instanceof FunctionName) {
        var name = node.name;
        var innerBody = node.body.kind === "brace-group" ? node.body.body : node.body;
        var body = FormatCmdsubNode(innerBody, indent + 4, false, false, false).replace(/[;]+$/, '');
        return "function ".concat(name, " () \n{ \n").concat(innerSp).concat(body, "\n}");
    }
    if (node instanceof Subshell) {
        var body = FormatCmdsubNode(node.body, indent, inProcsub, compactRedirects, false);
        var redirects = "";
        if (node.redirects.length > 0) {
            var redirectParts = [];
            for (var _7 = 0, _8 = node.redirects; _7 < _8.length; _7++) {
                var r = _8[_7];
                redirectParts.push(FormatRedirect(r, false, false));
            }
            redirects = redirectParts.join(" ");
        }
        if (procsubFirst) {
            if (redirects !== "") {
                return "(" + body + ") " + redirects;
            }
            return "(" + body + ")";
        }
        if (redirects !== "") {
            return "( " + body + " ) " + redirects;
        }
        return "( " + body + " )";
    }
    if (node instanceof BraceGroup) {
        var body = FormatCmdsubNode(node.body, indent, false, false, false);
        body = body.replace(/[;]+$/, '');
        var terminator = body.endsWith(" &") ? " }" : "; }";
        var redirects = "";
        if (node.redirects.length > 0) {
            var redirectParts = [];
            for (var _9 = 0, _10 = node.redirects; _9 < _10.length; _9++) {
                var r = _10[_9];
                redirectParts.push(FormatRedirect(r, false, false));
            }
            redirects = redirectParts.join(" ");
        }
        if (redirects !== "") {
            return "{ " + body + terminator + " " + redirects;
        }
        return "{ " + body + terminator;
    }
    if (node instanceof ArithmeticCommand) {
        return "((" + node.rawContent + "))";
    }
    if (node instanceof ConditionalExpr) {
        var body = FormatCondBody(node.body);
        return "[[ " + body + " ]]";
    }
    if (node instanceof Negation) {
        if (node.pipeline !== null) {
            return "! " + FormatCmdsubNode(node.pipeline, indent, false, false, false);
        }
        return "! ";
    }
    if (node instanceof Time) {
        var prefix = node.posix ? "time -p " : "time ";
        if (node.pipeline !== null) {
            return prefix + FormatCmdsubNode(node.pipeline, indent, false, false, false);
        }
        return prefix;
    }
    return "";
}
function FormatRedirect(r, compact, heredocOpOnly) {
    if (r instanceof HereDoc) {
        if (r.stripTabs) {
            var op = "<<-";
        }
        else {
            var op = "<<";
        }
        if (r.fd !== null && r.fd > 0) {
            var op = String(r.fd) + op;
        }
        if (r.quoted) {
            var delim = "'" + r.delimiter + "'";
        }
        else {
            var delim = r.delimiter;
        }
        if (heredocOpOnly) {
            return op + delim;
        }
        return op + delim + "\n" + r.content + r.delimiter + "\n";
    }
    var op = r.op;
    if (op === "1>") {
        op = ">";
    }
    else {
        if (op === "0<") {
            op = "<";
        }
    }
    var target = r.target.value;
    target = r.target.ExpandAllAnsiCQuotes(target);
    target = r.target.StripLocaleStringDollars(target);
    target = r.target.FormatCommandSubstitutions(target, false);
    if (target.startsWith("&")) {
        var wasInputClose = false;
        if (target === "&-" && op.endsWith("<")) {
            wasInputClose = true;
            op = Substring(op, 0, op.length - 1) + ">";
        }
        var afterAmp = Substring(target, 1, target.length);
        var isLiteralFd = afterAmp === "-" || afterAmp.length > 0 && /^[0-9]+$/.test(afterAmp[0]);
        if (isLiteralFd) {
            if (op === ">" || op === ">&") {
                op = wasInputClose ? "0>" : "1>";
            }
            else {
                if (op === "<" || op === "<&") {
                    op = "0<";
                }
            }
        }
        else {
            if (op === "1>") {
                op = ">";
            }
            else {
                if (op === "0<") {
                    op = "<";
                }
            }
        }
        return op + target;
    }
    if (op.endsWith("&")) {
        return op + target;
    }
    if (compact) {
        return op + target;
    }
    return op + " " + target;
}
function FormatHeredocBody(r) {
    return "\n" + r.content + r.delimiter + "\n";
}
function LookaheadForEsac(value, start, caseDepth) {
    var i = start;
    var depth = caseDepth;
    var quote = newQuoteState();
    while (i < value.length) {
        var c = value[i];
        if (c === "\\" && i + 1 < value.length && quote.double) {
            i += 2;
            continue;
        }
        if (c === "'" && !quote.double) {
            quote.single = !quote.single;
            i += 1;
            continue;
        }
        if (c === "\"" && !quote.single) {
            quote.double = !quote.double;
            i += 1;
            continue;
        }
        if (quote.single || quote.double) {
            i += 1;
            continue;
        }
        if (StartsWithAt(value, i, "case") && IsWordBoundary(value, i, 4)) {
            depth += 1;
            i += 4;
        }
        else {
            if (StartsWithAt(value, i, "esac") && IsWordBoundary(value, i, 4)) {
                depth -= 1;
                if (depth === 0) {
                    return true;
                }
                i += 4;
            }
            else {
                if (c === "(") {
                    i += 1;
                }
                else {
                    if (c === ")") {
                        if (depth > 0) {
                            i += 1;
                        }
                        else {
                            break;
                        }
                    }
                    else {
                        i += 1;
                    }
                }
            }
        }
    }
    return false;
}
function SkipBacktick(value, start) {
    var i = start + 1;
    while (i < value.length && value[i] !== "`") {
        if (value[i] === "\\" && i + 1 < value.length) {
            i += 2;
        }
        else {
            i += 1;
        }
    }
    if (i < value.length) {
        i += 1;
    }
    return i;
}
function SkipSingleQuoted(s, start) {
    var i = start;
    while (i < s.length && s[i] !== "'") {
        i += 1;
    }
    return i < s.length ? i + 1 : i;
}
function SkipDoubleQuoted(s, start) {
    {
        var i = start;
        var n = s.length;
    }
    {
        var passNext = false;
        var backq = false;
    }
    while (i < n) {
        var c = s[i];
        if (passNext) {
            passNext = false;
            i += 1;
            continue;
        }
        if (c === "\\") {
            passNext = true;
            i += 1;
            continue;
        }
        if (backq) {
            if (c === "`") {
                backq = false;
            }
            i += 1;
            continue;
        }
        if (c === "`") {
            backq = true;
            i += 1;
            continue;
        }
        if (c === "$" && i + 1 < n) {
            if (s[i + 1] === "(") {
                i = FindCmdsubEnd(s, i + 2);
                continue;
            }
            if (s[i + 1] === "{") {
                i = FindBracedParamEnd(s, i + 2);
                continue;
            }
        }
        if (c === "\"") {
            return i + 1;
        }
        i += 1;
    }
    return i;
}
function IsValidArithmeticStart(value, start) {
    var scanParen = 0;
    var scanI = start + 3;
    while (scanI < value.length) {
        var scanC = value[scanI];
        if (IsExpansionStart(value, scanI, "$(")) {
            scanI = FindCmdsubEnd(value, scanI + 2);
            continue;
        }
        if (scanC === "(") {
            scanParen += 1;
        }
        else {
            if (scanC === ")") {
                if (scanParen > 0) {
                    scanParen -= 1;
                }
                else {
                    if (scanI + 1 < value.length && value[scanI + 1] === ")") {
                        return true;
                    }
                    else {
                        return false;
                    }
                }
            }
        }
        scanI += 1;
    }
    return false;
}
function FindFunsubEnd(value, start) {
    var depth = 1;
    var i = start;
    var quote = newQuoteState();
    while (i < value.length && depth > 0) {
        var c = value[i];
        if (c === "\\" && i + 1 < value.length && !quote.single) {
            i += 2;
            continue;
        }
        if (c === "'" && !quote.double) {
            quote.single = !quote.single;
            i += 1;
            continue;
        }
        if (c === "\"" && !quote.single) {
            quote.double = !quote.double;
            i += 1;
            continue;
        }
        if (quote.single || quote.double) {
            i += 1;
            continue;
        }
        if (c === "{") {
            depth += 1;
        }
        else {
            if (c === "}") {
                depth -= 1;
                if (depth === 0) {
                    return i + 1;
                }
            }
        }
        i += 1;
    }
    return value.length;
}
function FindCmdsubEnd(value, start) {
    var depth = 1;
    var i = start;
    var caseDepth = 0;
    var inCasePatterns = false;
    var arithDepth = 0;
    var arithParenDepth = 0;
    while (i < value.length && depth > 0) {
        var c = value[i];
        if (c === "\\" && i + 1 < value.length) {
            i += 2;
            continue;
        }
        if (c === "'") {
            i = SkipSingleQuoted(value, i + 1);
            continue;
        }
        if (c === "\"") {
            i = SkipDoubleQuoted(value, i + 1);
            continue;
        }
        if (c === "#" && arithDepth === 0 && (i === start || value[i - 1] === " " || value[i - 1] === "\t" || value[i - 1] === "\n" || value[i - 1] === ";" || value[i - 1] === "|" || value[i - 1] === "&" || value[i - 1] === "(" || value[i - 1] === ")")) {
            while (i < value.length && value[i] !== "\n") {
                i += 1;
            }
            continue;
        }
        if (StartsWithAt(value, i, "<<<")) {
            i += 3;
            while (i < value.length && (value[i] === " " || value[i] === "\t")) {
                i += 1;
            }
            if (i < value.length && value[i] === "\"") {
                i += 1;
                while (i < value.length && value[i] !== "\"") {
                    if (value[i] === "\\" && i + 1 < value.length) {
                        i += 2;
                    }
                    else {
                        i += 1;
                    }
                }
                if (i < value.length) {
                    i += 1;
                }
            }
            else {
                if (i < value.length && value[i] === "'") {
                    i += 1;
                    while (i < value.length && value[i] !== "'") {
                        i += 1;
                    }
                    if (i < value.length) {
                        i += 1;
                    }
                }
                else {
                    while (i < value.length && !" \t\n;|&<>()".includes(value[i])) {
                        i += 1;
                    }
                }
            }
            continue;
        }
        if (IsExpansionStart(value, i, "$((")) {
            if (IsValidArithmeticStart(value, i)) {
                arithDepth += 1;
                i += 3;
                continue;
            }
            var j = FindCmdsubEnd(value, i + 2);
            i = j;
            continue;
        }
        if (arithDepth > 0 && arithParenDepth === 0 && StartsWithAt(value, i, "))")) {
            arithDepth -= 1;
            i += 2;
            continue;
        }
        if (c === "`") {
            i = SkipBacktick(value, i);
            continue;
        }
        if (arithDepth === 0 && StartsWithAt(value, i, "<<")) {
            i = SkipHeredoc(value, i);
            continue;
        }
        if (StartsWithAt(value, i, "case") && IsWordBoundary(value, i, 4)) {
            caseDepth += 1;
            inCasePatterns = false;
            i += 4;
            continue;
        }
        if (caseDepth > 0 && StartsWithAt(value, i, "in") && IsWordBoundary(value, i, 2)) {
            inCasePatterns = true;
            i += 2;
            continue;
        }
        if (StartsWithAt(value, i, "esac") && IsWordBoundary(value, i, 4)) {
            if (caseDepth > 0) {
                caseDepth -= 1;
                inCasePatterns = false;
            }
            i += 4;
            continue;
        }
        if (StartsWithAt(value, i, ";;")) {
            i += 2;
            continue;
        }
        if (c === "(") {
            if (!(inCasePatterns && caseDepth > 0)) {
                if (arithDepth > 0) {
                    arithParenDepth += 1;
                }
                else {
                    depth += 1;
                }
            }
        }
        else {
            if (c === ")") {
                if (inCasePatterns && caseDepth > 0) {
                    if (!LookaheadForEsac(value, i + 1, caseDepth)) {
                        depth -= 1;
                    }
                }
                else {
                    if (arithDepth > 0) {
                        if (arithParenDepth > 0) {
                            arithParenDepth -= 1;
                        }
                    }
                    else {
                        depth -= 1;
                    }
                }
            }
        }
        i += 1;
    }
    return i;
}
function FindBracedParamEnd(value, start) {
    var depth = 1;
    var i = start;
    var inDouble = false;
    var dolbraceState = DolbraceState_PARAM;
    while (i < value.length && depth > 0) {
        var c = value[i];
        if (c === "\\" && i + 1 < value.length) {
            i += 2;
            continue;
        }
        if (c === "'" && dolbraceState === DolbraceState_QUOTE && !inDouble) {
            i = SkipSingleQuoted(value, i + 1);
            continue;
        }
        if (c === "\"") {
            inDouble = !inDouble;
            i += 1;
            continue;
        }
        if (inDouble) {
            i += 1;
            continue;
        }
        if (dolbraceState === DolbraceState_PARAM && "%#^,".includes(c)) {
            dolbraceState = DolbraceState_QUOTE;
        }
        else {
            if (dolbraceState === DolbraceState_PARAM && ":-=?+/".includes(c)) {
                dolbraceState = DolbraceState_WORD;
            }
        }
        if (c === "[" && dolbraceState === DolbraceState_PARAM && !inDouble) {
            var end = SkipSubscript(value, i, 0);
            if (end !== -1) {
                i = end;
                continue;
            }
        }
        if ((c === "<" || c === ">") && i + 1 < value.length && value[i + 1] === "(") {
            i = FindCmdsubEnd(value, i + 2);
            continue;
        }
        if (c === "{") {
            depth += 1;
        }
        else {
            if (c === "}") {
                depth -= 1;
                if (depth === 0) {
                    return i + 1;
                }
            }
        }
        if (IsExpansionStart(value, i, "$(")) {
            i = FindCmdsubEnd(value, i + 2);
            continue;
        }
        if (IsExpansionStart(value, i, "${")) {
            i = FindBracedParamEnd(value, i + 2);
            continue;
        }
        i += 1;
    }
    return i;
}
function SkipHeredoc(value, start) {
    var i = start + 2;
    if (i < value.length && value[i] === "-") {
        i += 1;
    }
    while (i < value.length && IsWhitespaceNoNewline(value[i])) {
        i += 1;
    }
    var delimStart = i;
    var quoteChar = null;
    if (i < value.length && (value[i] === "\"" || value[i] === "'")) {
        quoteChar = value[i];
        i += 1;
        delimStart = i;
        while (i < value.length && value[i] !== quoteChar) {
            i += 1;
        }
        var delimiter = Substring(value, delimStart, i);
        if (i < value.length) {
            i += 1;
        }
    }
    else {
        if (i < value.length && value[i] === "\\") {
            i += 1;
            delimStart = i;
            if (i < value.length) {
                i += 1;
            }
            while (i < value.length && !IsMetachar(value[i])) {
                i += 1;
            }
            var delimiter = Substring(value, delimStart, i);
        }
        else {
            while (i < value.length && !IsMetachar(value[i])) {
                i += 1;
            }
            var delimiter = Substring(value, delimStart, i);
        }
    }
    var parenDepth = 0;
    var quote = newQuoteState();
    var inBacktick = false;
    while (i < value.length && value[i] !== "\n") {
        var c = value[i];
        if (c === "\\" && i + 1 < value.length && (quote.double || inBacktick)) {
            i += 2;
            continue;
        }
        if (c === "'" && !quote.double && !inBacktick) {
            quote.single = !quote.single;
            i += 1;
            continue;
        }
        if (c === "\"" && !quote.single && !inBacktick) {
            quote.double = !quote.double;
            i += 1;
            continue;
        }
        if (c === "`" && !quote.single) {
            inBacktick = !inBacktick;
            i += 1;
            continue;
        }
        if (quote.single || quote.double || inBacktick) {
            i += 1;
            continue;
        }
        if (c === "(") {
            parenDepth += 1;
        }
        else {
            if (c === ")") {
                if (parenDepth === 0) {
                    break;
                }
                parenDepth -= 1;
            }
        }
        i += 1;
    }
    if (i < value.length && value[i] === ")") {
        return i;
    }
    if (i < value.length && value[i] === "\n") {
        i += 1;
    }
    while (i < value.length) {
        var lineStart = i;
        var lineEnd = i;
        while (lineEnd < value.length && value[lineEnd] !== "\n") {
            lineEnd += 1;
        }
        var line = Substring(value, lineStart, lineEnd);
        while (lineEnd < value.length) {
            var trailingBs = 0;
            for (var _i = 0, _a = range(line.length - 1, -1, -1); _i < _a.length; _i++) {
                var j = _a[_i];
                if (line[j] === "\\") {
                    trailingBs += 1;
                }
                else {
                    break;
                }
            }
            if (trailingBs % 2 === 0) {
                break;
            }
            line = line.slice(0, line.length - 1);
            lineEnd += 1;
            var nextLineStart = lineEnd;
            while (lineEnd < value.length && value[lineEnd] !== "\n") {
                lineEnd += 1;
            }
            line = line + Substring(value, nextLineStart, lineEnd);
        }
        if (start + 2 < value.length && value[start + 2] === "-") {
            var stripped = line.replace(/^[\t]+/, '');
        }
        else {
            var stripped = line;
        }
        if (stripped === delimiter) {
            if (lineEnd < value.length) {
                return lineEnd + 1;
            }
            else {
                return lineEnd;
            }
        }
        if (stripped.startsWith(delimiter) && stripped.length > delimiter.length) {
            var tabsStripped = line.length - stripped.length;
            return lineStart + tabsStripped + delimiter.length;
        }
        if (lineEnd < value.length) {
            i = lineEnd + 1;
        }
        else {
            i = lineEnd;
        }
    }
    return i;
}
function FindHeredocContentEnd(source, start, delimiters) {
    if (!(delimiters.length > 0)) {
        return [start, start];
    }
    var pos = start;
    while (pos < source.length && source[pos] !== "\n") {
        pos += 1;
    }
    if (pos >= source.length) {
        return [start, start];
    }
    var contentStart = pos;
    pos += 1;
    for (var _i = 0, delimiters_1 = delimiters; _i < delimiters_1.length; _i++) {
        var Item = delimiters_1[_i];
        var delimiter = Item[0];
        var stripTabs = Item[1];
        while (pos < source.length) {
            var lineStart = pos;
            var lineEnd = pos;
            while (lineEnd < source.length && source[lineEnd] !== "\n") {
                lineEnd += 1;
            }
            var line = Substring(source, lineStart, lineEnd);
            while (lineEnd < source.length) {
                var trailingBs = 0;
                for (var _a = 0, _b = range(line.length - 1, -1, -1); _a < _b.length; _a++) {
                    var j = _b[_a];
                    if (line[j] === "\\") {
                        trailingBs += 1;
                    }
                    else {
                        break;
                    }
                }
                if (trailingBs % 2 === 0) {
                    break;
                }
                line = line.slice(0, line.length - 1);
                lineEnd += 1;
                var nextLineStart = lineEnd;
                while (lineEnd < source.length && source[lineEnd] !== "\n") {
                    lineEnd += 1;
                }
                line = line + Substring(source, nextLineStart, lineEnd);
            }
            if (stripTabs) {
                var lineStripped = line.replace(/^[\t]+/, '');
            }
            else {
                var lineStripped = line;
            }
            if (lineStripped === delimiter) {
                pos = lineEnd < source.length ? lineEnd + 1 : lineEnd;
                break;
            }
            if (lineStripped.startsWith(delimiter) && lineStripped.length > delimiter.length) {
                var tabsStripped = line.length - lineStripped.length;
                pos = lineStart + tabsStripped + delimiter.length;
                break;
            }
            pos = lineEnd < source.length ? lineEnd + 1 : lineEnd;
        }
    }
    return [contentStart, pos];
}
function IsWordBoundary(s, pos, wordLen) {
    if (pos > 0) {
        var prev = s[pos - 1];
        if (/^[a-zA-Z0-9]$/.test(prev) || prev === "_") {
            return false;
        }
        if ("{}!".includes(prev)) {
            return false;
        }
    }
    var end = pos + wordLen;
    if (end < s.length && (/^[a-zA-Z0-9]$/.test(s[end]) || s[end] === "_")) {
        return false;
    }
    return true;
}
function IsQuote(c) {
    return c === "'" || c === "\"";
}
function CollapseWhitespace(s) {
    var result = [];
    var prevWasWs = false;
    for (var _i = 0, s_2 = s; _i < s_2.length; _i++) {
        var c = s_2[_i];
        if (c === " " || c === "\t") {
            if (!prevWasWs) {
                result.push(" ");
            }
            prevWasWs = true;
        }
        else {
            result.push(c);
            prevWasWs = false;
        }
    }
    var joined = result.join("");
    return joined.replace(/^[ \t]+/, '').replace(/[ \t]+$/, '');
}
function CountTrailingBackslashes(s) {
    var count = 0;
    for (var _i = 0, _a = range(s.length - 1, -1, -1); _i < _a.length; _i++) {
        var i = _a[_i];
        if (s[i] === "\\") {
            count += 1;
        }
        else {
            break;
        }
    }
    return count;
}
function NormalizeHeredocDelimiter(delimiter) {
    var result = [];
    var i = 0;
    while (i < delimiter.length) {
        if (i + 1 < delimiter.length && delimiter.slice(i, i + 2) === "$(") {
            result.push("$(");
            i += 2;
            var depth = 1;
            var inner = [];
            while (i < delimiter.length && depth > 0) {
                if (delimiter[i] === "(") {
                    depth += 1;
                    inner.push(delimiter[i]);
                }
                else {
                    if (delimiter[i] === ")") {
                        depth -= 1;
                        if (depth === 0) {
                            var innerStr = inner.join("");
                            innerStr = CollapseWhitespace(innerStr);
                            result.push(innerStr);
                            result.push(")");
                        }
                        else {
                            inner.push(delimiter[i]);
                        }
                    }
                    else {
                        inner.push(delimiter[i]);
                    }
                }
                i += 1;
            }
        }
        else {
            if (i + 1 < delimiter.length && delimiter.slice(i, i + 2) === "${") {
                result.push("${");
                i += 2;
                var depth = 1;
                var inner = [];
                while (i < delimiter.length && depth > 0) {
                    if (delimiter[i] === "{") {
                        depth += 1;
                        inner.push(delimiter[i]);
                    }
                    else {
                        if (delimiter[i] === "}") {
                            depth -= 1;
                            if (depth === 0) {
                                var innerStr = inner.join("");
                                innerStr = CollapseWhitespace(innerStr);
                                result.push(innerStr);
                                result.push("}");
                            }
                            else {
                                inner.push(delimiter[i]);
                            }
                        }
                        else {
                            inner.push(delimiter[i]);
                        }
                    }
                    i += 1;
                }
            }
            else {
                if (i + 1 < delimiter.length && "<>".includes(delimiter[i]) && delimiter[i + 1] === "(") {
                    result.push(delimiter[i]);
                    result.push("(");
                    i += 2;
                    var depth = 1;
                    var inner = [];
                    while (i < delimiter.length && depth > 0) {
                        if (delimiter[i] === "(") {
                            depth += 1;
                            inner.push(delimiter[i]);
                        }
                        else {
                            if (delimiter[i] === ")") {
                                depth -= 1;
                                if (depth === 0) {
                                    var innerStr = inner.join("");
                                    innerStr = CollapseWhitespace(innerStr);
                                    result.push(innerStr);
                                    result.push(")");
                                }
                                else {
                                    inner.push(delimiter[i]);
                                }
                            }
                            else {
                                inner.push(delimiter[i]);
                            }
                        }
                        i += 1;
                    }
                }
                else {
                    result.push(delimiter[i]);
                    i += 1;
                }
            }
        }
    }
    return result.join("");
}
function IsMetachar(c) {
    return c === " " || c === "\t" || c === "\n" || c === "|" || c === "&" || c === ";" || c === "(" || c === ")" || c === "<" || c === ">";
}
function IsFunsubChar(c) {
    return c === " " || c === "\t" || c === "\n" || c === "|";
}
function IsExtglobPrefix(c) {
    return c === "@" || c === "?" || c === "*" || c === "+" || c === "!";
}
function IsRedirectChar(c) {
    return c === "<" || c === ">";
}
function IsSpecialParam(c) {
    return c === "?" || c === "$" || c === "!" || c === "#" || c === "@" || c === "*" || c === "-" || c === "&";
}
function IsSpecialParamUnbraced(c) {
    return c === "?" || c === "$" || c === "!" || c === "#" || c === "@" || c === "*" || c === "-";
}
function IsDigit(c) {
    return c >= "0" && c <= "9";
}
function IsSemicolonOrNewline(c) {
    return c === ";" || c === "\n";
}
function IsWordEndContext(c) {
    return c === " " || c === "\t" || c === "\n" || c === ";" || c === "|" || c === "&" || c === "<" || c === ">" || c === "(" || c === ")";
}
function SkipMatchedPair(s, start, open, close, flags) {
    var n = s.length;
    if ((flags & _SMP_PAST_OPEN) !== 0) {
        var i = start;
    }
    else {
        if (start >= n || s[start] !== open) {
            return -1;
        }
        var i = start + 1;
    }
    var depth = 1;
    var passNext = false;
    var backq = false;
    while (i < n && depth > 0) {
        var c = s[i];
        if (passNext) {
            passNext = false;
            i += 1;
            continue;
        }
        var literal = flags & _SMP_LITERAL;
        if (!(literal !== 0) && c === "\\") {
            passNext = true;
            i += 1;
            continue;
        }
        if (backq) {
            if (c === "`") {
                backq = false;
            }
            i += 1;
            continue;
        }
        if (!(literal !== 0) && c === "`") {
            backq = true;
            i += 1;
            continue;
        }
        if (!(literal !== 0) && c === "'") {
            var i = SkipSingleQuoted(s, i + 1);
            continue;
        }
        if (!(literal !== 0) && c === "\"") {
            var i = SkipDoubleQuoted(s, i + 1);
            continue;
        }
        if (!(literal !== 0) && IsExpansionStart(s, i, "$(")) {
            var i = FindCmdsubEnd(s, i + 2);
            continue;
        }
        if (!(literal !== 0) && IsExpansionStart(s, i, "${")) {
            var i = FindBracedParamEnd(s, i + 2);
            continue;
        }
        if (!(literal !== 0) && c === open) {
            depth += 1;
        }
        else {
            if (c === close) {
                depth -= 1;
            }
        }
        i += 1;
    }
    return depth === 0 ? i : -1;
}
function SkipSubscript(s, start, flags) {
    return SkipMatchedPair(s, start, "[", "]", flags);
}
function Assignment(s, flags) {
    if (!(s !== "")) {
        return -1;
    }
    if (!(/^[a-zA-Z]$/.test(s[0]) || s[0] === "_")) {
        return -1;
    }
    var i = 1;
    while (i < s.length) {
        var c = s[i];
        if (c === "=") {
            return i;
        }
        if (c === "[") {
            var subFlags = (flags & 2) !== 0 ? _SMP_LITERAL : 0;
            var end = SkipSubscript(s, i, subFlags);
            if (end === -1) {
                return -1;
            }
            i = end;
            if (i < s.length && s[i] === "+") {
                i += 1;
            }
            if (i < s.length && s[i] === "=") {
                return i;
            }
            return -1;
        }
        if (c === "+") {
            if (i + 1 < s.length && s[i + 1] === "=") {
                return i + 1;
            }
            return -1;
        }
        if (!(/^[a-zA-Z0-9]$/.test(c) || c === "_")) {
            return -1;
        }
        i += 1;
    }
    return -1;
}
function IsArrayAssignmentPrefix(chars) {
    if (!(chars.length > 0)) {
        return false;
    }
    if (!(/^[a-zA-Z]$/.test(chars[0]) || chars[0] === "_")) {
        return false;
    }
    var s = chars.join("");
    var i = 1;
    while (i < s.length && (/^[a-zA-Z0-9]$/.test(s[i]) || s[i] === "_")) {
        i += 1;
    }
    while (i < s.length) {
        if (s[i] !== "[") {
            return false;
        }
        var end = SkipSubscript(s, i, _SMP_LITERAL);
        if (end === -1) {
            return false;
        }
        i = end;
    }
    return true;
}
function IsSpecialParamOrDigit(c) {
    return IsSpecialParam(c) || IsDigit(c);
}
function IsParamExpansionOp(c) {
    return c === ":" || c === "-" || c === "=" || c === "+" || c === "?" || c === "#" || c === "%" || c === "/" || c === "^" || c === "," || c === "@" || c === "*" || c === "[";
}
function IsSimpleParamOp(c) {
    return c === "-" || c === "=" || c === "?" || c === "+";
}
function IsEscapeCharInBacktick(c) {
    return c === "$" || c === "`" || c === "\\";
}
function IsNegationBoundary(c) {
    return IsWhitespace(c) || c === ";" || c === "|" || c === ")" || c === "&" || c === ">" || c === "<";
}
function IsBackslashEscaped(value, idx) {
    var bsCount = 0;
    var j = idx - 1;
    while (j >= 0 && value[j] === "\\") {
        bsCount += 1;
        j -= 1;
    }
    return bsCount % 2 === 1;
}
function IsDollarDollarParen(value, idx) {
    var dollarCount = 0;
    var j = idx - 1;
    while (j >= 0 && value[j] === "$") {
        dollarCount += 1;
        j -= 1;
    }
    return dollarCount % 2 === 1;
}
function IsParen(c) {
    return c === "(" || c === ")";
}
function IsCaretOrBang(c) {
    return c === "!" || c === "^";
}
function IsAtOrStar(c) {
    return c === "@" || c === "*";
}
function IsDigitOrDash(c) {
    return IsDigit(c) || c === "-";
}
function IsNewlineOrRightParen(c) {
    return c === "\n" || c === ")";
}
function IsSemicolonNewlineBrace(c) {
    return c === ";" || c === "\n" || c === "{";
}
function LooksLikeAssignment(s) {
    return Assignment(s, 0) !== -1;
}
function IsValidIdentifier(name) {
    if (!(name !== "")) {
        return false;
    }
    if (!(/^[a-zA-Z]$/.test(name[0]) || name[0] === "_")) {
        return false;
    }
    for (var _i = 0, _a = name.slice(1); _i < _a.length; _i++) {
        var c = _a[_i];
        if (!(/^[a-zA-Z0-9]$/.test(c) || c === "_")) {
            return false;
        }
    }
    return true;
}
function parse(source, extglob) {
    var parser = newParser(source, false, extglob);
    return parser.parse();
}
function newParseError(message, pos, line) {
    var self = new ParseError([], [], []);
    self.message = message;
    self.pos = pos;
    self.line = line;
    return self;
}
function newMatchedPairError(message, pos, line) {
    return new MatchedPairError();
}
function newQuoteState() {
    var self = new QuoteState([], [], []);
    self.single = false;
    self.double = false;
    self.Stack = [];
    return self;
}
function newParseContext(kind) {
    var self = new ParseContext([], [], [], [], [], [], [], []);
    self.kind = kind;
    self.parenDepth = 0;
    self.braceDepth = 0;
    self.bracketDepth = 0;
    self.caseDepth = 0;
    self.arithDepth = 0;
    self.arithParenDepth = 0;
    self.quote = newQuoteState();
    return self;
}
function newContextStack() {
    var self = new ContextStack([]);
    self.Stack = [newParseContext(0)];
    return self;
}
function newLexer(source, extglob) {
    var self = new Lexer([], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []);
    self.source = source;
    self.pos = 0;
    self.length = source.length;
    self.quote = newQuoteState();
    self.TokenCache = null;
    self.ParserState = ParserStateFlags_NONE;
    self.DolbraceState = DolbraceState_NONE;
    self.PendingHeredocs = [];
    self.Extglob = extglob;
    self.Parser = null;
    self.EofToken = "";
    self.LastReadToken = null;
    self.WordContext = WORD_CTX_NORMAL;
    self.AtCommandStart = false;
    self.InArrayLiteral = false;
    self.InAssignBuiltin = false;
    self.PostReadPos = 0;
    self.CachedWordContext = WORD_CTX_NORMAL;
    self.CachedAtCommandStart = false;
    self.CachedInArrayLiteral = false;
    self.CachedInAssignBuiltin = false;
    return self;
}
function newParser(source, inProcessSub, extglob) {
    var self = new Parser([], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []);
    self.source = source;
    self.pos = 0;
    self.length = source.length;
    self.PendingHeredocs = [];
    self.CmdsubHeredocEnd = -1;
    self.SawNewlineInSingleQuote = false;
    self.InProcessSub = inProcessSub;
    self.Extglob = extglob;
    self.Ctx = newContextStack();
    self.Lexer = newLexer(source, extglob);
    self.Lexer.Parser = self;
    self.TokenHistory = [null, null, null, null];
    self.ParserState = ParserStateFlags_NONE;
    self.DolbraceState = DolbraceState_NONE;
    self.EofToken = "";
    self.WordContext = WORD_CTX_NORMAL;
    self.AtCommandStart = false;
    self.InArrayLiteral = false;
    self.InAssignBuiltin = false;
    self.ArithSrc = "";
    self.ArithPos = 0;
    self.ArithLen = 0;
    return self;
}
if (typeof module !== 'undefined') {
    module.exports = { parse: parse, ParseError: ParseError };
}
