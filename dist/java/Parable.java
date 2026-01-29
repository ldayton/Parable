import java.util.*;

@FunctionalInterface
interface NodeSupplier { Node call(); }

final class Constants {
    public static final Map<String, Integer> ANSI_C_ESCAPES = new HashMap<>(Map.ofEntries(Map.entry("a", 7), Map.entry("b", 8), Map.entry("e", 27), Map.entry("E", 27), Map.entry("f", 12), Map.entry("n", 10), Map.entry("r", 13), Map.entry("t", 9), Map.entry("v", 11), Map.entry("\\", 92), Map.entry("\"", 34), Map.entry("?", 63)));
    public static final int TOKENTYPE_EOF = 0;
    public static final int TOKENTYPE_WORD = 1;
    public static final int TOKENTYPE_NEWLINE = 2;
    public static final int TOKENTYPE_SEMI = 10;
    public static final int TOKENTYPE_PIPE = 11;
    public static final int TOKENTYPE_AMP = 12;
    public static final int TOKENTYPE_LPAREN = 13;
    public static final int TOKENTYPE_RPAREN = 14;
    public static final int TOKENTYPE_LBRACE = 15;
    public static final int TOKENTYPE_RBRACE = 16;
    public static final int TOKENTYPE_LESS = 17;
    public static final int TOKENTYPE_GREATER = 18;
    public static final int TOKENTYPE_AND_AND = 30;
    public static final int TOKENTYPE_OR_OR = 31;
    public static final int TOKENTYPE_SEMI_SEMI = 32;
    public static final int TOKENTYPE_SEMI_AMP = 33;
    public static final int TOKENTYPE_SEMI_SEMI_AMP = 34;
    public static final int TOKENTYPE_LESS_LESS = 35;
    public static final int TOKENTYPE_GREATER_GREATER = 36;
    public static final int TOKENTYPE_LESS_AMP = 37;
    public static final int TOKENTYPE_GREATER_AMP = 38;
    public static final int TOKENTYPE_LESS_GREATER = 39;
    public static final int TOKENTYPE_GREATER_PIPE = 40;
    public static final int TOKENTYPE_LESS_LESS_MINUS = 41;
    public static final int TOKENTYPE_LESS_LESS_LESS = 42;
    public static final int TOKENTYPE_AMP_GREATER = 43;
    public static final int TOKENTYPE_AMP_GREATER_GREATER = 44;
    public static final int TOKENTYPE_PIPE_AMP = 45;
    public static final int TOKENTYPE_IF = 50;
    public static final int TOKENTYPE_THEN = 51;
    public static final int TOKENTYPE_ELSE = 52;
    public static final int TOKENTYPE_ELIF = 53;
    public static final int TOKENTYPE_FI = 54;
    public static final int TOKENTYPE_CASE = 55;
    public static final int TOKENTYPE_ESAC = 56;
    public static final int TOKENTYPE_FOR = 57;
    public static final int TOKENTYPE_WHILE = 58;
    public static final int TOKENTYPE_UNTIL = 59;
    public static final int TOKENTYPE_DO = 60;
    public static final int TOKENTYPE_DONE = 61;
    public static final int TOKENTYPE_IN = 62;
    public static final int TOKENTYPE_FUNCTION = 63;
    public static final int TOKENTYPE_SELECT = 64;
    public static final int TOKENTYPE_COPROC = 65;
    public static final int TOKENTYPE_TIME = 66;
    public static final int TOKENTYPE_BANG = 67;
    public static final int TOKENTYPE_LBRACKET_LBRACKET = 68;
    public static final int TOKENTYPE_RBRACKET_RBRACKET = 69;
    public static final int TOKENTYPE_ASSIGNMENT_WORD = 80;
    public static final int TOKENTYPE_NUMBER = 81;
    public static final int PARSERSTATEFLAGS_NONE = 0;
    public static final int PARSERSTATEFLAGS_PST_CASEPAT = 1;
    public static final int PARSERSTATEFLAGS_PST_CMDSUBST = 2;
    public static final int PARSERSTATEFLAGS_PST_CASESTMT = 4;
    public static final int PARSERSTATEFLAGS_PST_CONDEXPR = 8;
    public static final int PARSERSTATEFLAGS_PST_COMPASSIGN = 16;
    public static final int PARSERSTATEFLAGS_PST_ARITH = 32;
    public static final int PARSERSTATEFLAGS_PST_HEREDOC = 64;
    public static final int PARSERSTATEFLAGS_PST_REGEXP = 128;
    public static final int PARSERSTATEFLAGS_PST_EXTPAT = 256;
    public static final int PARSERSTATEFLAGS_PST_SUBSHELL = 512;
    public static final int PARSERSTATEFLAGS_PST_REDIRLIST = 1024;
    public static final int PARSERSTATEFLAGS_PST_COMMENT = 2048;
    public static final int PARSERSTATEFLAGS_PST_EOFTOKEN = 4096;
    public static final int DOLBRACESTATE_NONE = 0;
    public static final int DOLBRACESTATE_PARAM = 1;
    public static final int DOLBRACESTATE_OP = 2;
    public static final int DOLBRACESTATE_WORD = 4;
    public static final int DOLBRACESTATE_QUOTE = 64;
    public static final int DOLBRACESTATE_QUOTE2 = 128;
    public static final int MATCHEDPAIRFLAGS_NONE = 0;
    public static final int MATCHEDPAIRFLAGS_DQUOTE = 1;
    public static final int MATCHEDPAIRFLAGS_DOLBRACE = 2;
    public static final int MATCHEDPAIRFLAGS_COMMAND = 4;
    public static final int MATCHEDPAIRFLAGS_ARITH = 8;
    public static final int MATCHEDPAIRFLAGS_ALLOWESC = 16;
    public static final int MATCHEDPAIRFLAGS_EXTGLOB = 32;
    public static final int MATCHEDPAIRFLAGS_FIRSTCLOSE = 64;
    public static final int MATCHEDPAIRFLAGS_ARRAYSUB = 128;
    public static final int MATCHEDPAIRFLAGS_BACKQUOTE = 256;
    public static final int PARSECONTEXT_NORMAL = 0;
    public static final int PARSECONTEXT_COMMAND_SUB = 1;
    public static final int PARSECONTEXT_ARITHMETIC = 2;
    public static final int PARSECONTEXT_CASE_PATTERN = 3;
    public static final int PARSECONTEXT_BRACE_EXPANSION = 4;
    public static final Set<String> RESERVED_WORDS = new HashSet<>(Set.of("if", "then", "elif", "else", "fi", "while", "until", "for", "select", "do", "done", "case", "esac", "in", "function", "coproc"));
    public static final Set<String> COND_UNARY_OPS = new HashSet<>(Set.of("-a", "-b", "-c", "-d", "-e", "-f", "-g", "-h", "-k", "-p", "-r", "-s", "-t", "-u", "-w", "-x", "-G", "-L", "-N", "-O", "-S", "-z", "-n", "-o", "-v", "-R"));
    public static final Set<String> COND_BINARY_OPS = new HashSet<>(Set.of("==", "!=", "=~", "=", "<", ">", "-eq", "-ne", "-lt", "-le", "-gt", "-ge", "-nt", "-ot", "-ef"));
    public static final Set<String> COMPOUND_KEYWORDS = new HashSet<>(Set.of("while", "until", "for", "if", "case", "select"));
    public static final Set<String> ASSIGNMENT_BUILTINS = new HashSet<>(Set.of("alias", "declare", "typeset", "local", "export", "readonly", "eval", "let"));
    public static final int SMP_LITERAL = 1;
    public static final int SMP_PAST_OPEN = 2;
    public static final int WORD_CTX_NORMAL = 0;
    public static final int WORD_CTX_COND = 1;
    public static final int WORD_CTX_REGEX = 2;
}

record Tuple1(boolean f0, boolean f1) {}

record Tuple2(String f0, boolean f1) {}

record Tuple3(Node f0, String f1) {}

record Tuple4(Node f0, String f1, List<Node> f2) {}

record Tuple5(Node f0, boolean f1) {}

record Tuple6(int f0, List<String> f1, boolean f2) {}

record Tuple7(int f0, List<String> f1) {}

record Tuple8(int f0, String f1) {}

record Tuple9(int f0, int f1) {}

record Tuple10(String f0, int f1) {}

record Tuple11(boolean f0, String f1) {}

record Tuple12(String f0, String f1) {}

interface Node {
    String getKind();
    String toSexp();
}

class ParseError {
    String message;
    int pos;
    int line;

    ParseError(String message, int pos, int line) {
        this.message = message;
        this.pos = pos;
        this.line = line;
    }

    public String _formatMessage() {
        if (this.line != 0 && this.pos != 0) {
            return String.format("Parse error at line %s, position %s: %s", this.line, this.pos, this.message);
        } else {
            if (this.pos != 0) {
                return String.format("Parse error at position %s: %s", this.pos, this.message);
            }
        }
        return String.format("Parse error: %s", this.message);
    }
}

class MatchedPairError {

}

class TokenType {

}

class Token {
    int type;
    String value;
    int pos;
    List<Node> parts;
    Word word;

    Token(int type, String value, int pos, List<Node> parts, Word word) {
        this.type = type;
        this.value = value;
        this.pos = pos;
        this.parts = parts;
        this.word = word;
    }

    public String _Repr() {
        if (this.word != null) {
            return String.format("Token(%s, %s, %s, word=%s)", this.type, this.value, this.pos, this.word);
        }
        if (!this.parts.isEmpty()) {
            return String.format("Token(%s, %s, %s, parts=%s)", this.type, this.value, this.pos, this.parts.size());
        }
        return String.format("Token(%s, %s, %s)", this.type, this.value, this.pos);
    }
}

class ParserStateFlags {

}

class DolbraceState {

}

class MatchedPairFlags {

}

class SavedParserState {
    int parserState;
    int dolbraceState;
    List<Node> pendingHeredocs;
    List<ParseContext> ctxStack;
    String eofToken;

    SavedParserState(int parserState, int dolbraceState, List<Node> pendingHeredocs, List<ParseContext> ctxStack, String eofToken) {
        this.parserState = parserState;
        this.dolbraceState = dolbraceState;
        this.pendingHeredocs = pendingHeredocs;
        this.ctxStack = ctxStack;
        this.eofToken = eofToken;
    }

}

class QuoteState {
    boolean single;
    boolean double_;
    List<Tuple1> _stack;

    QuoteState(boolean single, boolean double_, List<Tuple1> _stack) {
        this.single = single;
        this.double_ = double_;
        this._stack = _stack;
    }

    public void push() {
        this._stack.add(new Tuple1(this.single, this.double_));
        this.single = false;
        this.double_ = false;
    }

    public void pop() {
        if (!this._stack.isEmpty()) {
            {
                Tuple1 _entry = this._stack.get(this._stack.size() - 1);
                this._stack = new ArrayList<>(this._stack.subList(0, this._stack.size() - 1));
                this.single = _entry.f0();
                this.double_ = _entry.f1();
            }
        }
    }

    public boolean inQuotes() {
        return this.single || this.double_;
    }

    public QuoteState copy() {
        QuoteState qs = ParableFunctions.newQuoteState();
        qs.single = this.single;
        qs.double_ = this.double_;
        qs._stack = new ArrayList<>(this._stack);
        return qs;
    }

    public boolean outerDouble() {
        if (this._stack.isEmpty()) {
            return false;
        }
        return this._stack.get(this._stack.size() - 1).f1();
    }
}

class ParseContext {
    int kind;
    int parenDepth;
    int braceDepth;
    int bracketDepth;
    int caseDepth;
    int arithDepth;
    int arithParenDepth;
    QuoteState quote;

    ParseContext(int kind, int parenDepth, int braceDepth, int bracketDepth, int caseDepth, int arithDepth, int arithParenDepth, QuoteState quote) {
        this.kind = kind;
        this.parenDepth = parenDepth;
        this.braceDepth = braceDepth;
        this.bracketDepth = bracketDepth;
        this.caseDepth = caseDepth;
        this.arithDepth = arithDepth;
        this.arithParenDepth = arithParenDepth;
        this.quote = quote;
    }

    public ParseContext copy() {
        ParseContext ctx = ParableFunctions.newParseContext(this.kind);
        ctx.parenDepth = this.parenDepth;
        ctx.braceDepth = this.braceDepth;
        ctx.bracketDepth = this.bracketDepth;
        ctx.caseDepth = this.caseDepth;
        ctx.arithDepth = this.arithDepth;
        ctx.arithParenDepth = this.arithParenDepth;
        ctx.quote = this.quote.copy();
        return ctx;
    }
}

class ContextStack {
    List<ParseContext> _stack;

    ContextStack(List<ParseContext> _stack) {
        this._stack = _stack;
    }

    public ParseContext getCurrent() {
        return this._stack.get(this._stack.size() - 1);
    }

    public void push(int kind) {
        this._stack.add(ParableFunctions.newParseContext(kind));
    }

    public ParseContext pop() {
        if (this._stack.size() > 1) {
            return this._stack.remove(this._stack.size() - 1);
        }
        return this._stack.get(0);
    }

    public List<ParseContext> copyStack() {
        List<ParseContext> result = new ArrayList<>();
        for (ParseContext ctx : this._stack) {
            result.add(ctx.copy());
        }
        return result;
    }

    public void restoreFrom(List<ParseContext> savedStack) {
        List<ParseContext> result = new ArrayList<>();
        for (ParseContext ctx : savedStack) {
            result.add(ctx.copy());
        }
        this._stack = result;
    }
}

class Lexer {
    Map<String, Integer> reservedWords;
    String source;
    int pos;
    int length;
    QuoteState quote;
    Token _tokenCache;
    int _parserState;
    int _dolbraceState;
    List<Node> _pendingHeredocs;
    boolean _extglob;
    Parser _parser;
    String _eofToken;
    Token _lastReadToken;
    int _wordContext;
    boolean _atCommandStart;
    boolean _inArrayLiteral;
    boolean _inAssignBuiltin;
    int _postReadPos;
    int _cachedWordContext;
    boolean _cachedAtCommandStart;
    boolean _cachedInArrayLiteral;
    boolean _cachedInAssignBuiltin;

    Lexer(Map<String, Integer> reservedWords, String source, int pos, int length, QuoteState quote, Token _tokenCache, int _parserState, int _dolbraceState, List<Node> _pendingHeredocs, boolean _extglob, Parser _parser, String _eofToken, Token _lastReadToken, int _wordContext, boolean _atCommandStart, boolean _inArrayLiteral, boolean _inAssignBuiltin, int _postReadPos, int _cachedWordContext, boolean _cachedAtCommandStart, boolean _cachedInArrayLiteral, boolean _cachedInAssignBuiltin) {
        this.reservedWords = reservedWords;
        this.source = source;
        this.pos = pos;
        this.length = length;
        this.quote = quote;
        this._tokenCache = _tokenCache;
        this._parserState = _parserState;
        this._dolbraceState = _dolbraceState;
        this._pendingHeredocs = _pendingHeredocs;
        this._extglob = _extglob;
        this._parser = _parser;
        this._eofToken = _eofToken;
        this._lastReadToken = _lastReadToken;
        this._wordContext = _wordContext;
        this._atCommandStart = _atCommandStart;
        this._inArrayLiteral = _inArrayLiteral;
        this._inAssignBuiltin = _inAssignBuiltin;
        this._postReadPos = _postReadPos;
        this._cachedWordContext = _cachedWordContext;
        this._cachedAtCommandStart = _cachedAtCommandStart;
        this._cachedInArrayLiteral = _cachedInArrayLiteral;
        this._cachedInAssignBuiltin = _cachedInAssignBuiltin;
    }

    public String peek() {
        if (this.pos >= this.length) {
            return "";
        }
        return String.valueOf(this.source.charAt(this.pos));
    }

    public String advance() {
        if (this.pos >= this.length) {
            return "";
        }
        String c = String.valueOf(this.source.charAt(this.pos));
        this.pos += 1;
        return c;
    }

    public boolean atEnd() {
        return this.pos >= this.length;
    }

    public String lookahead(int n) {
        return ParableFunctions._substring(this.source, this.pos, this.pos + n);
    }

    public boolean isMetachar(String c) {
        return "|&;()<> \t\n".indexOf(c) != -1;
    }

    public Token _readOperator() {
        int start = this.pos;
        String c = this.peek();
        if (c.equals("")) {
            return null;
        }
        String two = this.lookahead(2);
        String three = this.lookahead(3);
        if (three.equals(";;&")) {
            this.pos += 3;
            return new Token(Constants.TOKENTYPE_SEMI_SEMI_AMP, three, start, new ArrayList<>(), null);
        }
        if (three.equals("<<-")) {
            this.pos += 3;
            return new Token(Constants.TOKENTYPE_LESS_LESS_MINUS, three, start, new ArrayList<>(), null);
        }
        if (three.equals("<<<")) {
            this.pos += 3;
            return new Token(Constants.TOKENTYPE_LESS_LESS_LESS, three, start, new ArrayList<>(), null);
        }
        if (three.equals("&>>")) {
            this.pos += 3;
            return new Token(Constants.TOKENTYPE_AMP_GREATER_GREATER, three, start, new ArrayList<>(), null);
        }
        if (two.equals("&&")) {
            this.pos += 2;
            return new Token(Constants.TOKENTYPE_AND_AND, two, start, new ArrayList<>(), null);
        }
        if (two.equals("||")) {
            this.pos += 2;
            return new Token(Constants.TOKENTYPE_OR_OR, two, start, new ArrayList<>(), null);
        }
        if (two.equals(";;")) {
            this.pos += 2;
            return new Token(Constants.TOKENTYPE_SEMI_SEMI, two, start, new ArrayList<>(), null);
        }
        if (two.equals(";&")) {
            this.pos += 2;
            return new Token(Constants.TOKENTYPE_SEMI_AMP, two, start, new ArrayList<>(), null);
        }
        if (two.equals("<<")) {
            this.pos += 2;
            return new Token(Constants.TOKENTYPE_LESS_LESS, two, start, new ArrayList<>(), null);
        }
        if (two.equals(">>")) {
            this.pos += 2;
            return new Token(Constants.TOKENTYPE_GREATER_GREATER, two, start, new ArrayList<>(), null);
        }
        if (two.equals("<&")) {
            this.pos += 2;
            return new Token(Constants.TOKENTYPE_LESS_AMP, two, start, new ArrayList<>(), null);
        }
        if (two.equals(">&")) {
            this.pos += 2;
            return new Token(Constants.TOKENTYPE_GREATER_AMP, two, start, new ArrayList<>(), null);
        }
        if (two.equals("<>")) {
            this.pos += 2;
            return new Token(Constants.TOKENTYPE_LESS_GREATER, two, start, new ArrayList<>(), null);
        }
        if (two.equals(">|")) {
            this.pos += 2;
            return new Token(Constants.TOKENTYPE_GREATER_PIPE, two, start, new ArrayList<>(), null);
        }
        if (two.equals("&>")) {
            this.pos += 2;
            return new Token(Constants.TOKENTYPE_AMP_GREATER, two, start, new ArrayList<>(), null);
        }
        if (two.equals("|&")) {
            this.pos += 2;
            return new Token(Constants.TOKENTYPE_PIPE_AMP, two, start, new ArrayList<>(), null);
        }
        if (c.equals(";")) {
            this.pos += 1;
            return new Token(Constants.TOKENTYPE_SEMI, c, start, new ArrayList<>(), null);
        }
        if (c.equals("|")) {
            this.pos += 1;
            return new Token(Constants.TOKENTYPE_PIPE, c, start, new ArrayList<>(), null);
        }
        if (c.equals("&")) {
            this.pos += 1;
            return new Token(Constants.TOKENTYPE_AMP, c, start, new ArrayList<>(), null);
        }
        if (c.equals("(")) {
            if (this._wordContext == Constants.WORD_CTX_REGEX) {
                return null;
            }
            this.pos += 1;
            return new Token(Constants.TOKENTYPE_LPAREN, c, start, new ArrayList<>(), null);
        }
        if (c.equals(")")) {
            if (this._wordContext == Constants.WORD_CTX_REGEX) {
                return null;
            }
            this.pos += 1;
            return new Token(Constants.TOKENTYPE_RPAREN, c, start, new ArrayList<>(), null);
        }
        if (c.equals("<")) {
            if (this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("(")) {
                return null;
            }
            this.pos += 1;
            return new Token(Constants.TOKENTYPE_LESS, c, start, new ArrayList<>(), null);
        }
        if (c.equals(">")) {
            if (this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("(")) {
                return null;
            }
            this.pos += 1;
            return new Token(Constants.TOKENTYPE_GREATER, c, start, new ArrayList<>(), null);
        }
        if (c.equals("\n")) {
            this.pos += 1;
            return new Token(Constants.TOKENTYPE_NEWLINE, c, start, new ArrayList<>(), null);
        }
        return null;
    }

    public void skipBlanks() {
        while (this.pos < this.length) {
            String c = String.valueOf(this.source.charAt(this.pos));
            if (!c.equals(" ") && !c.equals("\t")) {
                break;
            }
            this.pos += 1;
        }
    }

    public boolean _skipComment() {
        if (this.pos >= this.length) {
            return false;
        }
        if (!String.valueOf(this.source.charAt(this.pos)).equals("#")) {
            return false;
        }
        if (this.quote.inQuotes()) {
            return false;
        }
        if (this.pos > 0) {
            String prev = String.valueOf(this.source.charAt(this.pos - 1));
            if (" \t\n;|&(){}".indexOf(prev) == -1) {
                return false;
            }
        }
        while (this.pos < this.length && !String.valueOf(this.source.charAt(this.pos)).equals("\n")) {
            this.pos += 1;
        }
        return true;
    }

    public Tuple2 _readSingleQuote(int start) {
        List<String> chars = new ArrayList<>(List.of("'"));
        boolean sawNewline = false;
        while (this.pos < this.length) {
            String c = String.valueOf(this.source.charAt(this.pos));
            if (c.equals("\n")) {
                sawNewline = true;
            }
            chars.add(c);
            this.pos += 1;
            if (c.equals("'")) {
                return new Tuple2(String.join("", chars), sawNewline);
            }
        }
        throw new RuntimeException("Unterminated single quote");
    }

    public boolean _isWordTerminator(int ctx, String ch, int bracketDepth, int parenDepth) {
        if (ctx == Constants.WORD_CTX_REGEX) {
            if (ch.equals("]") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("]")) {
                return true;
            }
            if (ch.equals("&") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("&")) {
                return true;
            }
            if (ch.equals(")") && parenDepth == 0) {
                return true;
            }
            return ParableFunctions._isWhitespace(ch) && parenDepth == 0;
        }
        if (ctx == Constants.WORD_CTX_COND) {
            if (ch.equals("]") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("]")) {
                return true;
            }
            if (ch.equals(")")) {
                return true;
            }
            if (ch.equals("&")) {
                return true;
            }
            if (ch.equals("|")) {
                return true;
            }
            if (ch.equals(";")) {
                return true;
            }
            if (ParableFunctions._isRedirectChar(ch) && !(this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("("))) {
                return true;
            }
            return ParableFunctions._isWhitespace(ch);
        }
        if ((this._parserState & Constants.PARSERSTATEFLAGS_PST_EOFTOKEN) != 0 && !this._eofToken.equals("") && ch.equals(this._eofToken) && bracketDepth == 0) {
            return true;
        }
        if (ParableFunctions._isRedirectChar(ch) && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("(")) {
            return false;
        }
        return ParableFunctions._isMetachar(ch) && bracketDepth == 0;
    }

    public boolean _readBracketExpression(List<String> chars, List<Node> parts, boolean forRegex, int parenDepth) {
        if (forRegex) {
            int scan = this.pos + 1;
            if (scan < this.length && String.valueOf(this.source.charAt(scan)).equals("^")) {
                scan += 1;
            }
            if (scan < this.length && String.valueOf(this.source.charAt(scan)).equals("]")) {
                scan += 1;
            }
            boolean bracketWillClose = false;
            while (scan < this.length) {
                String sc = String.valueOf(this.source.charAt(scan));
                if (sc.equals("]") && scan + 1 < this.length && String.valueOf(this.source.charAt(scan + 1)).equals("]")) {
                    break;
                }
                if (sc.equals(")") && parenDepth > 0) {
                    break;
                }
                if (sc.equals("&") && scan + 1 < this.length && String.valueOf(this.source.charAt(scan + 1)).equals("&")) {
                    break;
                }
                if (sc.equals("]")) {
                    bracketWillClose = true;
                    break;
                }
                if (sc.equals("[") && scan + 1 < this.length && String.valueOf(this.source.charAt(scan + 1)).equals(":")) {
                    scan += 2;
                    while (scan < this.length && !(String.valueOf(this.source.charAt(scan)).equals(":") && scan + 1 < this.length && String.valueOf(this.source.charAt(scan + 1)).equals("]"))) {
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
        } else {
            if (this.pos + 1 >= this.length) {
                return false;
            }
            String nextCh = String.valueOf(this.source.charAt(this.pos + 1));
            if (ParableFunctions._isWhitespaceNoNewline(nextCh) || nextCh.equals("&") || nextCh.equals("|")) {
                return false;
            }
        }
        chars.add(this.advance());
        if (!this.atEnd() && this.peek().equals("^")) {
            chars.add(this.advance());
        }
        if (!this.atEnd() && this.peek().equals("]")) {
            chars.add(this.advance());
        }
        while (!this.atEnd()) {
            String c = this.peek();
            if (c.equals("]")) {
                chars.add(this.advance());
                break;
            }
            if (c.equals("[") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals(":")) {
                chars.add(this.advance());
                chars.add(this.advance());
                while (!this.atEnd() && !(this.peek().equals(":") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("]"))) {
                    chars.add(this.advance());
                }
                if (!this.atEnd()) {
                    chars.add(this.advance());
                    chars.add(this.advance());
                }
            } else {
                if (!forRegex && c.equals("[") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("=")) {
                    chars.add(this.advance());
                    chars.add(this.advance());
                    while (!this.atEnd() && !(this.peek().equals("=") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("]"))) {
                        chars.add(this.advance());
                    }
                    if (!this.atEnd()) {
                        chars.add(this.advance());
                        chars.add(this.advance());
                    }
                } else {
                    if (!forRegex && c.equals("[") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals(".")) {
                        chars.add(this.advance());
                        chars.add(this.advance());
                        while (!this.atEnd() && !(this.peek().equals(".") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("]"))) {
                            chars.add(this.advance());
                        }
                        if (!this.atEnd()) {
                            chars.add(this.advance());
                            chars.add(this.advance());
                        }
                    } else {
                        if (forRegex && c.equals("$")) {
                            this._syncToParser();
                            if (!this._parser._parseDollarExpansion(chars, parts, false)) {
                                this._syncFromParser();
                                chars.add(this.advance());
                            } else {
                                this._syncFromParser();
                            }
                        } else {
                            chars.add(this.advance());
                        }
                    }
                }
            }
        }
        return true;
    }

    public String _parseMatchedPair(String openChar, String closeChar, int flags, boolean initialWasDollar) {
        int start = this.pos;
        int count = 1;
        List<String> chars = new ArrayList<>();
        boolean passNext = false;
        boolean wasDollar = initialWasDollar;
        boolean wasGtlt = false;
        while (count > 0) {
            if (this.atEnd()) {
                throw new RuntimeException(String.format("unexpected EOF while looking for matching `%s'", closeChar));
            }
            String ch = this.advance();
            if ((flags & Constants.MATCHEDPAIRFLAGS_DOLBRACE) != 0 && this._dolbraceState == Constants.DOLBRACESTATE_OP) {
                if ("#%^,~:-=?+/".indexOf(ch) == -1) {
                    this._dolbraceState = Constants.DOLBRACESTATE_WORD;
                }
            }
            if (passNext) {
                passNext = false;
                chars.add(ch);
                wasDollar = ch.equals("$");
                wasGtlt = "<>".indexOf(ch) != -1;
                continue;
            }
            if (openChar.equals("'")) {
                if (ch.equals(closeChar)) {
                    count -= 1;
                    if (count == 0) {
                        break;
                    }
                }
                if (ch.equals("\\") && (flags & Constants.MATCHEDPAIRFLAGS_ALLOWESC) != 0) {
                    passNext = true;
                }
                chars.add(ch);
                wasDollar = false;
                wasGtlt = false;
                continue;
            }
            if (ch.equals("\\")) {
                if (!this.atEnd() && this.peek().equals("\n")) {
                    this.advance();
                    wasDollar = false;
                    wasGtlt = false;
                    continue;
                }
                passNext = true;
                chars.add(ch);
                wasDollar = false;
                wasGtlt = false;
                continue;
            }
            if (ch.equals(closeChar)) {
                count -= 1;
                if (count == 0) {
                    break;
                }
                chars.add(ch);
                wasDollar = false;
                wasGtlt = "<>".indexOf(ch) != -1;
                continue;
            }
            if (ch.equals(openChar) && !openChar.equals(closeChar)) {
                if (!((flags & Constants.MATCHEDPAIRFLAGS_DOLBRACE) != 0 && openChar.equals("{"))) {
                    count += 1;
                }
                chars.add(ch);
                wasDollar = false;
                wasGtlt = "<>".indexOf(ch) != -1;
                continue;
            }
            if ("'\"`".indexOf(ch) != -1 && !openChar.equals(closeChar)) {
                String nested = "";
                if (ch.equals("'")) {
                    chars.add(ch);
                    int quoteFlags = (wasDollar ? (flags | Constants.MATCHEDPAIRFLAGS_ALLOWESC) : flags);
                    nested = this._parseMatchedPair("'", "'", quoteFlags, false);
                    chars.add(nested);
                    chars.add("'");
                    wasDollar = false;
                    wasGtlt = false;
                    continue;
                } else {
                    if (ch.equals("\"")) {
                        chars.add(ch);
                        nested = this._parseMatchedPair("\"", "\"", (flags | Constants.MATCHEDPAIRFLAGS_DQUOTE), false);
                        chars.add(nested);
                        chars.add("\"");
                        wasDollar = false;
                        wasGtlt = false;
                        continue;
                    } else {
                        if (ch.equals("`")) {
                            chars.add(ch);
                            nested = this._parseMatchedPair("`", "`", flags, false);
                            chars.add(nested);
                            chars.add("`");
                            wasDollar = false;
                            wasGtlt = false;
                            continue;
                        }
                    }
                }
            }
            if (ch.equals("$") && !this.atEnd() && !((flags & Constants.MATCHEDPAIRFLAGS_EXTGLOB) != 0)) {
                String nextCh = this.peek();
                if (wasDollar) {
                    chars.add(ch);
                    wasDollar = false;
                    wasGtlt = false;
                    continue;
                }
                if (nextCh.equals("{")) {
                    if ((flags & Constants.MATCHEDPAIRFLAGS_ARITH) != 0) {
                        int afterBracePos = this.pos + 1;
                        if (afterBracePos >= this.length || !ParableFunctions._isFunsubChar(String.valueOf(this.source.charAt(afterBracePos)))) {
                            chars.add(ch);
                            wasDollar = true;
                            wasGtlt = false;
                            continue;
                        }
                    }
                    this.pos -= 1;
                    this._syncToParser();
                    boolean inDquote = (flags & Constants.MATCHEDPAIRFLAGS_DQUOTE) != 0;
                    Tuple3 _tuple1 = this._parser._parseParamExpansion(inDquote);
                    Node paramNode = _tuple1.f0();
                    String paramText = _tuple1.f1();
                    this._syncFromParser();
                    if (paramNode != null) {
                        chars.add(paramText);
                        wasDollar = false;
                        wasGtlt = false;
                    } else {
                        chars.add(this.advance());
                        wasDollar = true;
                        wasGtlt = false;
                    }
                    continue;
                } else {
                    Node arithNode = null;
                    String arithText = "";
                    if (nextCh.equals("(")) {
                        this.pos -= 1;
                        this._syncToParser();
                        Node cmdNode = null;
                        String cmdText = "";
                        if (this.pos + 2 < this.length && String.valueOf(this.source.charAt(this.pos + 2)).equals("(")) {
                            Tuple3 _tuple2 = this._parser._parseArithmeticExpansion();
                            arithNode = _tuple2.f0();
                            arithText = _tuple2.f1();
                            this._syncFromParser();
                            if (arithNode != null) {
                                chars.add(arithText);
                                wasDollar = false;
                                wasGtlt = false;
                            } else {
                                this._syncToParser();
                                Tuple3 _tuple3 = this._parser._parseCommandSubstitution();
                                cmdNode = _tuple3.f0();
                                cmdText = _tuple3.f1();
                                this._syncFromParser();
                                if (cmdNode != null) {
                                    chars.add(cmdText);
                                    wasDollar = false;
                                    wasGtlt = false;
                                } else {
                                    chars.add(this.advance());
                                    chars.add(this.advance());
                                    wasDollar = false;
                                    wasGtlt = false;
                                }
                            }
                        } else {
                            Tuple3 _tuple4 = this._parser._parseCommandSubstitution();
                            cmdNode = _tuple4.f0();
                            cmdText = _tuple4.f1();
                            this._syncFromParser();
                            if (cmdNode != null) {
                                chars.add(cmdText);
                                wasDollar = false;
                                wasGtlt = false;
                            } else {
                                chars.add(this.advance());
                                chars.add(this.advance());
                                wasDollar = false;
                                wasGtlt = false;
                            }
                        }
                        continue;
                    } else {
                        if (nextCh.equals("[")) {
                            this.pos -= 1;
                            this._syncToParser();
                            Tuple3 _tuple5 = this._parser._parseDeprecatedArithmetic();
                            arithNode = _tuple5.f0();
                            arithText = _tuple5.f1();
                            this._syncFromParser();
                            if (arithNode != null) {
                                chars.add(arithText);
                                wasDollar = false;
                                wasGtlt = false;
                            } else {
                                chars.add(this.advance());
                                wasDollar = true;
                                wasGtlt = false;
                            }
                            continue;
                        }
                    }
                }
            }
            if (ch.equals("(") && wasGtlt && (flags & (Constants.MATCHEDPAIRFLAGS_DOLBRACE | Constants.MATCHEDPAIRFLAGS_ARRAYSUB)) != 0) {
                String direction = chars.get(chars.size() - 1);
                chars = new ArrayList<>(chars.subList(0, chars.size() - 1));
                this.pos -= 1;
                this._syncToParser();
                Tuple3 _tuple6 = this._parser._parseProcessSubstitution();
                Node procsubNode = _tuple6.f0();
                String procsubText = _tuple6.f1();
                this._syncFromParser();
                if (procsubNode != null) {
                    chars.add(procsubText);
                    wasDollar = false;
                    wasGtlt = false;
                } else {
                    chars.add(direction);
                    chars.add(this.advance());
                    wasDollar = false;
                    wasGtlt = false;
                }
                continue;
            }
            chars.add(ch);
            wasDollar = ch.equals("$");
            wasGtlt = "<>".indexOf(ch) != -1;
        }
        return String.join("", chars);
    }

    public String _collectParamArgument(int flags, boolean wasDollar) {
        return this._parseMatchedPair("{", "}", (flags | Constants.MATCHEDPAIRFLAGS_DOLBRACE), wasDollar);
    }

    public Word _readWordInternal(int ctx, boolean atCommandStart, boolean inArrayLiteral, boolean inAssignBuiltin) {
        int start = this.pos;
        List<String> chars = new ArrayList<>();
        List<Node> parts = new ArrayList<>();
        int bracketDepth = 0;
        int bracketStartPos = -1;
        boolean seenEquals = false;
        int parenDepth = 0;
        while (!this.atEnd()) {
            String ch = this.peek();
            if (ctx == Constants.WORD_CTX_REGEX) {
                if (ch.equals("\\") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("\n")) {
                    this.advance();
                    this.advance();
                    continue;
                }
            }
            if (ctx != Constants.WORD_CTX_NORMAL && this._isWordTerminator(ctx, ch, bracketDepth, parenDepth)) {
                break;
            }
            if (ctx == Constants.WORD_CTX_NORMAL && ch.equals("[")) {
                if (bracketDepth > 0) {
                    bracketDepth += 1;
                    chars.add(this.advance());
                    continue;
                }
                if (!chars.isEmpty() && atCommandStart && !seenEquals && ParableFunctions._isArrayAssignmentPrefix(chars)) {
                    String prevChar = chars.get(chars.size() - 1);
                    if (prevChar.chars().allMatch(Character::isLetterOrDigit) || prevChar.equals("_")) {
                        bracketStartPos = this.pos;
                        bracketDepth += 1;
                        chars.add(this.advance());
                        continue;
                    }
                }
                if (!(!chars.isEmpty()) && !seenEquals && inArrayLiteral) {
                    bracketStartPos = this.pos;
                    bracketDepth += 1;
                    chars.add(this.advance());
                    continue;
                }
            }
            if (ctx == Constants.WORD_CTX_NORMAL && ch.equals("]") && bracketDepth > 0) {
                bracketDepth -= 1;
                chars.add(this.advance());
                continue;
            }
            if (ctx == Constants.WORD_CTX_NORMAL && ch.equals("=") && bracketDepth == 0) {
                seenEquals = true;
            }
            if (ctx == Constants.WORD_CTX_REGEX && ch.equals("(")) {
                parenDepth += 1;
                chars.add(this.advance());
                continue;
            }
            if (ctx == Constants.WORD_CTX_REGEX && ch.equals(")")) {
                if (parenDepth > 0) {
                    parenDepth -= 1;
                    chars.add(this.advance());
                    continue;
                }
                break;
            }
            if (ctx == Constants.WORD_CTX_COND || ctx == Constants.WORD_CTX_REGEX && ch.equals("[")) {
                boolean forRegex = ctx == Constants.WORD_CTX_REGEX;
                if (this._readBracketExpression(chars, parts, forRegex, parenDepth)) {
                    continue;
                }
                chars.add(this.advance());
                continue;
            }
            String content = "";
            if (ctx == Constants.WORD_CTX_COND && ch.equals("(")) {
                if (this._extglob && !chars.isEmpty() && ParableFunctions._isExtglobPrefix(chars.get(chars.size() - 1))) {
                    chars.add(this.advance());
                    content = this._parseMatchedPair("(", ")", Constants.MATCHEDPAIRFLAGS_EXTGLOB, false);
                    chars.add(content);
                    chars.add(")");
                    continue;
                } else {
                    break;
                }
            }
            if (ctx == Constants.WORD_CTX_REGEX && ParableFunctions._isWhitespace(ch) && parenDepth > 0) {
                chars.add(this.advance());
                continue;
            }
            if (ch.equals("'")) {
                this.advance();
                boolean trackNewline = ctx == Constants.WORD_CTX_NORMAL;
                Tuple2 _tuple7 = this._readSingleQuote(start);
                content = _tuple7.f0();
                boolean sawNewline = _tuple7.f1();
                chars.add(content);
                if (trackNewline && sawNewline && this._parser != null) {
                    this._parser._sawNewlineInSingleQuote = true;
                }
                continue;
            }
            Node cmdsubResult0 = null;
            String cmdsubResult1 = "";
            if (ch.equals("\"")) {
                this.advance();
                if (ctx == Constants.WORD_CTX_NORMAL) {
                    chars.add("\"");
                    boolean inSingleInDquote = false;
                    while (!this.atEnd() && inSingleInDquote || !this.peek().equals("\"")) {
                        String c = this.peek();
                        if (inSingleInDquote) {
                            chars.add(this.advance());
                            if (c.equals("'")) {
                                inSingleInDquote = false;
                            }
                            continue;
                        }
                        if (c.equals("\\") && this.pos + 1 < this.length) {
                            String nextC = String.valueOf(this.source.charAt(this.pos + 1));
                            if (nextC.equals("\n")) {
                                this.advance();
                                this.advance();
                            } else {
                                chars.add(this.advance());
                                chars.add(this.advance());
                            }
                        } else {
                            if (c.equals("$")) {
                                this._syncToParser();
                                if (!this._parser._parseDollarExpansion(chars, parts, true)) {
                                    this._syncFromParser();
                                    chars.add(this.advance());
                                } else {
                                    this._syncFromParser();
                                }
                            } else {
                                if (c.equals("`")) {
                                    this._syncToParser();
                                    Tuple3 _tuple8 = this._parser._parseBacktickSubstitution();
                                    cmdsubResult0 = _tuple8.f0();
                                    cmdsubResult1 = _tuple8.f1();
                                    this._syncFromParser();
                                    if (cmdsubResult0 != null) {
                                        parts.add(cmdsubResult0);
                                        chars.add(cmdsubResult1);
                                    } else {
                                        chars.add(this.advance());
                                    }
                                } else {
                                    chars.add(this.advance());
                                }
                            }
                        }
                    }
                    if (this.atEnd()) {
                        throw new RuntimeException("Unterminated double quote");
                    }
                    chars.add(this.advance());
                } else {
                    boolean handleLineContinuation = ctx == Constants.WORD_CTX_COND;
                    this._syncToParser();
                    this._parser._scanDoubleQuote(chars, parts, start, handleLineContinuation);
                    this._syncFromParser();
                }
                continue;
            }
            if (ch.equals("\\") && this.pos + 1 < this.length) {
                String nextCh = String.valueOf(this.source.charAt(this.pos + 1));
                if (ctx != Constants.WORD_CTX_REGEX && nextCh.equals("\n")) {
                    this.advance();
                    this.advance();
                } else {
                    chars.add(this.advance());
                    chars.add(this.advance());
                }
                continue;
            }
            if (ctx != Constants.WORD_CTX_REGEX && ch.equals("$") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("'")) {
                Tuple3 _tuple9 = this._readAnsiCQuote();
                Node ansiResult0 = _tuple9.f0();
                String ansiResult1 = _tuple9.f1();
                if (ansiResult0 != null) {
                    parts.add(ansiResult0);
                    chars.add(ansiResult1);
                } else {
                    chars.add(this.advance());
                }
                continue;
            }
            if (ctx != Constants.WORD_CTX_REGEX && ch.equals("$") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("\"")) {
                Tuple4 _tuple10 = this._readLocaleString();
                Node localeResult0 = _tuple10.f0();
                String localeResult1 = _tuple10.f1();
                List<Node> localeResult2 = _tuple10.f2();
                if (localeResult0 != null) {
                    parts.add(localeResult0);
                    parts.addAll(localeResult2);
                    chars.add(localeResult1);
                } else {
                    chars.add(this.advance());
                }
                continue;
            }
            if (ch.equals("$")) {
                this._syncToParser();
                if (!this._parser._parseDollarExpansion(chars, parts, false)) {
                    this._syncFromParser();
                    chars.add(this.advance());
                } else {
                    this._syncFromParser();
                    if (this._extglob && ctx == Constants.WORD_CTX_NORMAL && !chars.isEmpty() && chars.get(chars.size() - 1).length() == 2 && String.valueOf(chars.get(chars.size() - 1).charAt(0)).equals("$") && "?*@".indexOf(String.valueOf(chars.get(chars.size() - 1).charAt(1))) != -1 && !this.atEnd() && this.peek().equals("(")) {
                        chars.add(this.advance());
                        content = this._parseMatchedPair("(", ")", Constants.MATCHEDPAIRFLAGS_EXTGLOB, false);
                        chars.add(content);
                        chars.add(")");
                    }
                }
                continue;
            }
            if (ctx != Constants.WORD_CTX_REGEX && ch.equals("`")) {
                this._syncToParser();
                Tuple3 _tuple11 = this._parser._parseBacktickSubstitution();
                cmdsubResult0 = _tuple11.f0();
                cmdsubResult1 = _tuple11.f1();
                this._syncFromParser();
                if (cmdsubResult0 != null) {
                    parts.add(cmdsubResult0);
                    chars.add(cmdsubResult1);
                } else {
                    chars.add(this.advance());
                }
                continue;
            }
            if (ctx != Constants.WORD_CTX_REGEX && ParableFunctions._isRedirectChar(ch) && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("(")) {
                this._syncToParser();
                Tuple3 _tuple12 = this._parser._parseProcessSubstitution();
                Node procsubResult0 = _tuple12.f0();
                String procsubResult1 = _tuple12.f1();
                this._syncFromParser();
                if (procsubResult0 != null) {
                    parts.add(procsubResult0);
                    chars.add(procsubResult1);
                } else {
                    if (!procsubResult1.equals("")) {
                        chars.add(procsubResult1);
                    } else {
                        chars.add(this.advance());
                        if (ctx == Constants.WORD_CTX_NORMAL) {
                            chars.add(this.advance());
                        }
                    }
                }
                continue;
            }
            if (ctx == Constants.WORD_CTX_NORMAL && ch.equals("(") && !chars.isEmpty() && bracketDepth == 0) {
                boolean isArrayAssign = false;
                if (chars.size() >= 3 && chars.get(chars.size() - 2).equals("+") && chars.get(chars.size() - 1).equals("=")) {
                    isArrayAssign = ParableFunctions._isArrayAssignmentPrefix(new ArrayList<>(chars.subList(0, chars.size() - 2)));
                } else {
                    if (chars.get(chars.size() - 1).equals("=") && chars.size() >= 2) {
                        isArrayAssign = ParableFunctions._isArrayAssignmentPrefix(new ArrayList<>(chars.subList(0, chars.size() - 1)));
                    }
                }
                if (isArrayAssign && atCommandStart || inAssignBuiltin) {
                    this._syncToParser();
                    Tuple3 _tuple13 = this._parser._parseArrayLiteral();
                    Node arrayResult0 = _tuple13.f0();
                    String arrayResult1 = _tuple13.f1();
                    this._syncFromParser();
                    if (arrayResult0 != null) {
                        parts.add(arrayResult0);
                        chars.add(arrayResult1);
                    } else {
                        break;
                    }
                    continue;
                }
            }
            if (this._extglob && ctx == Constants.WORD_CTX_NORMAL && ParableFunctions._isExtglobPrefix(ch) && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("(")) {
                chars.add(this.advance());
                chars.add(this.advance());
                content = this._parseMatchedPair("(", ")", Constants.MATCHEDPAIRFLAGS_EXTGLOB, false);
                chars.add(content);
                chars.add(")");
                continue;
            }
            if (ctx == Constants.WORD_CTX_NORMAL && (this._parserState & Constants.PARSERSTATEFLAGS_PST_EOFTOKEN) != 0 && !this._eofToken.equals("") && ch.equals(this._eofToken) && bracketDepth == 0) {
                if (!(!chars.isEmpty())) {
                    chars.add(this.advance());
                }
                break;
            }
            if (ctx == Constants.WORD_CTX_NORMAL && ParableFunctions._isMetachar(ch) && bracketDepth == 0) {
                break;
            }
            chars.add(this.advance());
        }
        if (bracketDepth > 0 && bracketStartPos != -1 && this.atEnd()) {
            throw new RuntimeException("unexpected EOF looking for `]'");
        }
        if (!(!chars.isEmpty())) {
            return null;
        }
        if (!parts.isEmpty()) {
            return new Word(String.join("", chars), parts, "word");
        }
        return new Word(String.join("", chars), null, "word");
    }

    public Token _readWord() {
        int start = this.pos;
        if (this.pos >= this.length) {
            return null;
        }
        String c = this.peek();
        if (c.equals("")) {
            return null;
        }
        boolean isProcsub = c.equals("<") || c.equals(">") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("(");
        boolean isRegexParen = this._wordContext == Constants.WORD_CTX_REGEX && c.equals("(") || c.equals(")");
        if (this.isMetachar(c) && !isProcsub && !isRegexParen) {
            return null;
        }
        Word word = this._readWordInternal(this._wordContext, this._atCommandStart, this._inArrayLiteral, this._inAssignBuiltin);
        if (word == null) {
            return null;
        }
        return new Token(Constants.TOKENTYPE_WORD, word.value, start, null, word);
    }

    public Token nextToken() {
        Token tok = null;
        if (this._tokenCache != null) {
            tok = this._tokenCache;
            this._tokenCache = null;
            this._lastReadToken = tok;
            return tok;
        }
        this.skipBlanks();
        if (this.atEnd()) {
            tok = new Token(Constants.TOKENTYPE_EOF, "", this.pos, new ArrayList<>(), null);
            this._lastReadToken = tok;
            return tok;
        }
        if (!this._eofToken.equals("") && this.peek().equals(this._eofToken) && !((this._parserState & Constants.PARSERSTATEFLAGS_PST_CASEPAT) != 0) && !((this._parserState & Constants.PARSERSTATEFLAGS_PST_EOFTOKEN) != 0)) {
            tok = new Token(Constants.TOKENTYPE_EOF, "", this.pos, new ArrayList<>(), null);
            this._lastReadToken = tok;
            return tok;
        }
        while (this._skipComment()) {
            this.skipBlanks();
            if (this.atEnd()) {
                tok = new Token(Constants.TOKENTYPE_EOF, "", this.pos, new ArrayList<>(), null);
                this._lastReadToken = tok;
                return tok;
            }
            if (!this._eofToken.equals("") && this.peek().equals(this._eofToken) && !((this._parserState & Constants.PARSERSTATEFLAGS_PST_CASEPAT) != 0) && !((this._parserState & Constants.PARSERSTATEFLAGS_PST_EOFTOKEN) != 0)) {
                tok = new Token(Constants.TOKENTYPE_EOF, "", this.pos, new ArrayList<>(), null);
                this._lastReadToken = tok;
                return tok;
            }
        }
        tok = this._readOperator();
        if (tok != null) {
            this._lastReadToken = tok;
            return tok;
        }
        tok = this._readWord();
        if (tok != null) {
            this._lastReadToken = tok;
            return tok;
        }
        tok = new Token(Constants.TOKENTYPE_EOF, "", this.pos, new ArrayList<>(), null);
        this._lastReadToken = tok;
        return tok;
    }

    public Token peekToken() {
        if (this._tokenCache == null) {
            Token savedLast = this._lastReadToken;
            this._tokenCache = this.nextToken();
            this._lastReadToken = savedLast;
        }
        return this._tokenCache;
    }

    public Tuple3 _readAnsiCQuote() {
        if (this.atEnd() || !this.peek().equals("$")) {
            return new Tuple3(null, "");
        }
        if (this.pos + 1 >= this.length || !String.valueOf(this.source.charAt(this.pos + 1)).equals("'")) {
            return new Tuple3(null, "");
        }
        int start = this.pos;
        this.advance();
        this.advance();
        List<String> contentChars = new ArrayList<>();
        boolean foundClose = false;
        while (!this.atEnd()) {
            String ch = this.peek();
            if (ch.equals("'")) {
                this.advance();
                foundClose = true;
                break;
            } else {
                if (ch.equals("\\")) {
                    contentChars.add(this.advance());
                    if (!this.atEnd()) {
                        contentChars.add(this.advance());
                    }
                } else {
                    contentChars.add(this.advance());
                }
            }
        }
        if (!foundClose) {
            throw new RuntimeException("unexpected EOF while looking for matching `''");
        }
        String text = ParableFunctions._substring(this.source, start, this.pos);
        String content = String.join("", contentChars);
        AnsiCQuote node = new AnsiCQuote(content, "ansi-c");
        return new Tuple3(node, text);
    }

    public void _syncToParser() {
        if (this._parser != null) {
            this._parser.pos = this.pos;
        }
    }

    public void _syncFromParser() {
        if (this._parser != null) {
            this.pos = this._parser.pos;
        }
    }

    public Tuple4 _readLocaleString() {
        if (this.atEnd() || !this.peek().equals("$")) {
            return new Tuple4(null, "", new ArrayList<>());
        }
        if (this.pos + 1 >= this.length || !String.valueOf(this.source.charAt(this.pos + 1)).equals("\"")) {
            return new Tuple4(null, "", new ArrayList<>());
        }
        int start = this.pos;
        this.advance();
        this.advance();
        List<String> contentChars = new ArrayList<>();
        List<Node> innerParts = new ArrayList<>();
        boolean foundClose = false;
        while (!this.atEnd()) {
            String ch = this.peek();
            if (ch.equals("\"")) {
                this.advance();
                foundClose = true;
                break;
            } else {
                if (ch.equals("\\") && this.pos + 1 < this.length) {
                    String nextCh = String.valueOf(this.source.charAt(this.pos + 1));
                    if (nextCh.equals("\n")) {
                        this.advance();
                        this.advance();
                    } else {
                        contentChars.add(this.advance());
                        contentChars.add(this.advance());
                    }
                } else {
                    Node cmdsubNode = null;
                    String cmdsubText = "";
                    if (ch.equals("$") && this.pos + 2 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("(") && String.valueOf(this.source.charAt(this.pos + 2)).equals("(")) {
                        this._syncToParser();
                        Tuple3 _tuple14 = this._parser._parseArithmeticExpansion();
                        Node arithNode = _tuple14.f0();
                        String arithText = _tuple14.f1();
                        this._syncFromParser();
                        if (arithNode != null) {
                            innerParts.add(arithNode);
                            contentChars.add(arithText);
                        } else {
                            this._syncToParser();
                            Tuple3 _tuple15 = this._parser._parseCommandSubstitution();
                            cmdsubNode = _tuple15.f0();
                            cmdsubText = _tuple15.f1();
                            this._syncFromParser();
                            if (cmdsubNode != null) {
                                innerParts.add(cmdsubNode);
                                contentChars.add(cmdsubText);
                            } else {
                                contentChars.add(this.advance());
                            }
                        }
                    } else {
                        if (ParableFunctions._isExpansionStart(this.source, this.pos, "$(")) {
                            this._syncToParser();
                            Tuple3 _tuple16 = this._parser._parseCommandSubstitution();
                            cmdsubNode = _tuple16.f0();
                            cmdsubText = _tuple16.f1();
                            this._syncFromParser();
                            if (cmdsubNode != null) {
                                innerParts.add(cmdsubNode);
                                contentChars.add(cmdsubText);
                            } else {
                                contentChars.add(this.advance());
                            }
                        } else {
                            if (ch.equals("$")) {
                                this._syncToParser();
                                Tuple3 _tuple17 = this._parser._parseParamExpansion(false);
                                Node paramNode = _tuple17.f0();
                                String paramText = _tuple17.f1();
                                this._syncFromParser();
                                if (paramNode != null) {
                                    innerParts.add(paramNode);
                                    contentChars.add(paramText);
                                } else {
                                    contentChars.add(this.advance());
                                }
                            } else {
                                if (ch.equals("`")) {
                                    this._syncToParser();
                                    Tuple3 _tuple18 = this._parser._parseBacktickSubstitution();
                                    cmdsubNode = _tuple18.f0();
                                    cmdsubText = _tuple18.f1();
                                    this._syncFromParser();
                                    if (cmdsubNode != null) {
                                        innerParts.add(cmdsubNode);
                                        contentChars.add(cmdsubText);
                                    } else {
                                        contentChars.add(this.advance());
                                    }
                                } else {
                                    contentChars.add(this.advance());
                                }
                            }
                        }
                    }
                }
            }
        }
        if (!foundClose) {
            this.pos = start;
            return new Tuple4(null, "", new ArrayList<>());
        }
        String content = String.join("", contentChars);
        String text = "$\"" + content + "\"";
        return new Tuple4(new LocaleString(content, "locale"), text, innerParts);
    }

    public void _updateDolbraceForOp(String op, boolean hasParam) {
        if (this._dolbraceState == Constants.DOLBRACESTATE_NONE) {
            return;
        }
        if (op.equals("") || op.isEmpty()) {
            return;
        }
        String firstChar = String.valueOf(op.charAt(0));
        if (this._dolbraceState == Constants.DOLBRACESTATE_PARAM && hasParam) {
            if ("%#^,".indexOf(firstChar) != -1) {
                this._dolbraceState = Constants.DOLBRACESTATE_QUOTE;
                return;
            }
            if (firstChar.equals("/")) {
                this._dolbraceState = Constants.DOLBRACESTATE_QUOTE2;
                return;
            }
        }
        if (this._dolbraceState == Constants.DOLBRACESTATE_PARAM) {
            if ("#%^,~:-=?+/".indexOf(firstChar) != -1) {
                this._dolbraceState = Constants.DOLBRACESTATE_OP;
            }
        }
    }

    public String _consumeParamOperator() {
        if (this.atEnd()) {
            return "";
        }
        String ch = this.peek();
        String nextCh = "";
        if (ch.equals(":")) {
            this.advance();
            if (this.atEnd()) {
                return ":";
            }
            nextCh = this.peek();
            if (ParableFunctions._isSimpleParamOp(nextCh)) {
                this.advance();
                return ":" + nextCh;
            }
            return ":";
        }
        if (ParableFunctions._isSimpleParamOp(ch)) {
            this.advance();
            return ch;
        }
        if (ch.equals("#")) {
            this.advance();
            if (!this.atEnd() && this.peek().equals("#")) {
                this.advance();
                return "##";
            }
            return "#";
        }
        if (ch.equals("%")) {
            this.advance();
            if (!this.atEnd() && this.peek().equals("%")) {
                this.advance();
                return "%%";
            }
            return "%";
        }
        if (ch.equals("/")) {
            this.advance();
            if (!this.atEnd()) {
                nextCh = this.peek();
                if (nextCh.equals("/")) {
                    this.advance();
                    return "//";
                } else {
                    if (nextCh.equals("#")) {
                        this.advance();
                        return "/#";
                    } else {
                        if (nextCh.equals("%")) {
                            this.advance();
                            return "/%";
                        }
                    }
                }
            }
            return "/";
        }
        if (ch.equals("^")) {
            this.advance();
            if (!this.atEnd() && this.peek().equals("^")) {
                this.advance();
                return "^^";
            }
            return "^";
        }
        if (ch.equals(",")) {
            this.advance();
            if (!this.atEnd() && this.peek().equals(",")) {
                this.advance();
                return ",,";
            }
            return ",";
        }
        if (ch.equals("@")) {
            this.advance();
            return "@";
        }
        return "";
    }

    public boolean _paramSubscriptHasClose(int startPos) {
        int depth = 1;
        int i = startPos + 1;
        QuoteState quote = ParableFunctions.newQuoteState();
        while (i < this.length) {
            String c = String.valueOf(this.source.charAt(i));
            if (quote.single) {
                if (c.equals("'")) {
                    quote.single = false;
                }
                i += 1;
                continue;
            }
            if (quote.double_) {
                if (c.equals("\\") && i + 1 < this.length) {
                    i += 2;
                    continue;
                }
                if (c.equals("\"")) {
                    quote.double_ = false;
                }
                i += 1;
                continue;
            }
            if (c.equals("'")) {
                quote.single = true;
                i += 1;
                continue;
            }
            if (c.equals("\"")) {
                quote.double_ = true;
                i += 1;
                continue;
            }
            if (c.equals("\\")) {
                i += 2;
                continue;
            }
            if (c.equals("}")) {
                return false;
            }
            if (c.equals("[")) {
                depth += 1;
            } else {
                if (c.equals("]")) {
                    depth -= 1;
                    if (depth == 0) {
                        return true;
                    }
                }
            }
            i += 1;
        }
        return false;
    }

    public String _consumeParamName() {
        if (this.atEnd()) {
            return "";
        }
        String ch = this.peek();
        if (ParableFunctions._isSpecialParam(ch)) {
            if (ch.equals("$") && this.pos + 1 < this.length && "{'\"".indexOf(String.valueOf(this.source.charAt(this.pos + 1))) != -1) {
                return "";
            }
            this.advance();
            return ch;
        }
        if (ch.chars().allMatch(Character::isDigit)) {
            List<String> nameChars = new ArrayList<>();
            while (!this.atEnd() && this.peek().chars().allMatch(Character::isDigit)) {
                nameChars.add(this.advance());
            }
            return String.join("", nameChars);
        }
        if (ch.chars().allMatch(Character::isLetter) || ch.equals("_")) {
            List<String> nameChars = new ArrayList<>();
            while (!this.atEnd()) {
                String c = this.peek();
                if (c.chars().allMatch(Character::isLetterOrDigit) || c.equals("_")) {
                    nameChars.add(this.advance());
                } else {
                    if (c.equals("[")) {
                        if (!this._paramSubscriptHasClose(this.pos)) {
                            break;
                        }
                        nameChars.add(this.advance());
                        String content = this._parseMatchedPair("[", "]", Constants.MATCHEDPAIRFLAGS_ARRAYSUB, false);
                        nameChars.add(content);
                        nameChars.add("]");
                        break;
                    } else {
                        break;
                    }
                }
            }
            if (!nameChars.isEmpty()) {
                return String.join("", nameChars);
            } else {
                return "";
            }
        }
        return "";
    }

    public Tuple3 _readParamExpansion(boolean inDquote) {
        if (this.atEnd() || !this.peek().equals("$")) {
            return new Tuple3(null, "");
        }
        int start = this.pos;
        this.advance();
        if (this.atEnd()) {
            this.pos = start;
            return new Tuple3(null, "");
        }
        String ch = this.peek();
        if (ch.equals("{")) {
            this.advance();
            return this._readBracedParam(start, inDquote);
        }
        String text = "";
        if (ParableFunctions._isSpecialParamUnbraced(ch) || ParableFunctions._isDigit(ch) || ch.equals("#")) {
            this.advance();
            text = ParableFunctions._substring(this.source, start, this.pos);
            return new Tuple3(new ParamExpansion(ch, "", "", "param"), text);
        }
        if (ch.chars().allMatch(Character::isLetter) || ch.equals("_")) {
            int nameStart = this.pos;
            while (!this.atEnd()) {
                String c = this.peek();
                if (c.chars().allMatch(Character::isLetterOrDigit) || c.equals("_")) {
                    this.advance();
                } else {
                    break;
                }
            }
            String name = ParableFunctions._substring(this.source, nameStart, this.pos);
            text = ParableFunctions._substring(this.source, start, this.pos);
            return new Tuple3(new ParamExpansion(name, "", "", "param"), text);
        }
        this.pos = start;
        return new Tuple3(null, "");
    }

    public Tuple3 _readBracedParam(int start, boolean inDquote) {
        if (this.atEnd()) {
            throw new RuntimeException("unexpected EOF looking for `}'");
        }
        int savedDolbrace = this._dolbraceState;
        this._dolbraceState = Constants.DOLBRACESTATE_PARAM;
        String ch = this.peek();
        if (ParableFunctions._isFunsubChar(ch)) {
            this._dolbraceState = savedDolbrace;
            return this._readFunsub(start);
        }
        String param = "";
        String text = "";
        if (ch.equals("#")) {
            this.advance();
            param = this._consumeParamName();
            if (!param.equals("") && !this.atEnd() && this.peek().equals("}")) {
                this.advance();
                text = ParableFunctions._substring(this.source, start, this.pos);
                this._dolbraceState = savedDolbrace;
                return new Tuple3(new ParamLength(param, "param-len"), text);
            }
            this.pos = start + 2;
        }
        String op = "";
        String arg = "";
        if (ch.equals("!")) {
            this.advance();
            while (!this.atEnd() && ParableFunctions._isWhitespaceNoNewline(this.peek())) {
                this.advance();
            }
            param = this._consumeParamName();
            if (!param.equals("")) {
                while (!this.atEnd() && ParableFunctions._isWhitespaceNoNewline(this.peek())) {
                    this.advance();
                }
                if (!this.atEnd() && this.peek().equals("}")) {
                    this.advance();
                    text = ParableFunctions._substring(this.source, start, this.pos);
                    this._dolbraceState = savedDolbrace;
                    return new Tuple3(new ParamIndirect(param, "", "", "param-indirect"), text);
                }
                if (!this.atEnd() && ParableFunctions._isAtOrStar(this.peek())) {
                    String suffix = this.advance();
                    String trailing = this._parseMatchedPair("{", "}", Constants.MATCHEDPAIRFLAGS_DOLBRACE, false);
                    text = ParableFunctions._substring(this.source, start, this.pos);
                    this._dolbraceState = savedDolbrace;
                    return new Tuple3(new ParamIndirect(param + suffix + trailing, "", "", "param-indirect"), text);
                }
                op = this._consumeParamOperator();
                if (op.equals("") && !this.atEnd() && "}\"'`".indexOf(this.peek()) == -1) {
                    op = this.advance();
                }
                if (!op.equals("") && "\"'`".indexOf(op) == -1) {
                    arg = this._parseMatchedPair("{", "}", Constants.MATCHEDPAIRFLAGS_DOLBRACE, false);
                    text = ParableFunctions._substring(this.source, start, this.pos);
                    this._dolbraceState = savedDolbrace;
                    return new Tuple3(new ParamIndirect(param, op, arg, "param-indirect"), text);
                }
                if (this.atEnd()) {
                    this._dolbraceState = savedDolbrace;
                    throw new RuntimeException("unexpected EOF looking for `}'");
                }
                this.pos = start + 2;
            } else {
                this.pos = start + 2;
            }
        }
        param = this._consumeParamName();
        if (!(!param.equals(""))) {
            if (!this.atEnd() && "-=+?".indexOf(this.peek()) != -1 || this.peek().equals(":") && this.pos + 1 < this.length && ParableFunctions._isSimpleParamOp(String.valueOf(this.source.charAt(this.pos + 1)))) {
                param = "";
            } else {
                String content = this._parseMatchedPair("{", "}", Constants.MATCHEDPAIRFLAGS_DOLBRACE, false);
                text = "${" + content + "}";
                this._dolbraceState = savedDolbrace;
                return new Tuple3(new ParamExpansion(content, "", "", "param"), text);
            }
        }
        if (this.atEnd()) {
            this._dolbraceState = savedDolbrace;
            throw new RuntimeException("unexpected EOF looking for `}'");
        }
        if (this.peek().equals("}")) {
            this.advance();
            text = ParableFunctions._substring(this.source, start, this.pos);
            this._dolbraceState = savedDolbrace;
            return new Tuple3(new ParamExpansion(param, "", "", "param"), text);
        }
        op = this._consumeParamOperator();
        if (op.equals("")) {
            if (!this.atEnd() && this.peek().equals("$") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("\"") || String.valueOf(this.source.charAt(this.pos + 1)).equals("'")) {
                int dollarCount = 1 + ParableFunctions._countConsecutiveDollarsBefore(this.source, this.pos);
                if (dollarCount % 2 == 1) {
                    op = "";
                } else {
                    op = this.advance();
                }
            } else {
                if (!this.atEnd() && this.peek().equals("`")) {
                    int backtickPos = this.pos;
                    this.advance();
                    while (!this.atEnd() && !this.peek().equals("`")) {
                        String bc = this.peek();
                        if (bc.equals("\\") && this.pos + 1 < this.length) {
                            String nextC = String.valueOf(this.source.charAt(this.pos + 1));
                            if (ParableFunctions._isEscapeCharInBacktick(nextC)) {
                                this.advance();
                            }
                        }
                        this.advance();
                    }
                    if (this.atEnd()) {
                        this._dolbraceState = savedDolbrace;
                        throw new RuntimeException("Unterminated backtick");
                    }
                    this.advance();
                    op = "`";
                } else {
                    if (!this.atEnd() && this.peek().equals("$") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("{")) {
                        op = "";
                    } else {
                        if (!this.atEnd() && this.peek().equals("'") || this.peek().equals("\"")) {
                            op = "";
                        } else {
                            if (!this.atEnd() && this.peek().equals("\\")) {
                                op = this.advance();
                                if (!this.atEnd()) {
                                    op += this.advance();
                                }
                            } else {
                                op = this.advance();
                            }
                        }
                    }
                }
            }
        }
        this._updateDolbraceForOp(op, !param.isEmpty());
        try {
            int flags = (inDquote ? Constants.MATCHEDPAIRFLAGS_DQUOTE : Constants.MATCHEDPAIRFLAGS_NONE);
            boolean paramEndsWithDollar = !param.equals("") && param.endsWith("$");
            arg = this._collectParamArgument(flags, paramEndsWithDollar);
        } catch (Exception e) {
            this._dolbraceState = savedDolbrace;
            throw new RuntimeException("");
        }
        if (op.equals("<") || op.equals(">") && arg.startsWith("(") && arg.endsWith(")")) {
            String inner = arg.substring(1, arg.length() - 1);
            try {
                Parser subParser = ParableFunctions.newParser(inner, true, this._parser._extglob);
                Node parsed = subParser.parseList(true);
                if (parsed != null && subParser.atEnd()) {
                    String formatted = ParableFunctions._formatCmdsubNode(parsed, 0, true, false, true);
                    arg = "(" + formatted + ")";
                }
            } catch (Exception e) {
            }
        }
        text = "${" + param + op + arg + "}";
        this._dolbraceState = savedDolbrace;
        return new Tuple3(new ParamExpansion(param, op, arg, "param"), text);
    }

    public Tuple3 _readFunsub(int start) {
        return this._parser._parseFunsub(start);
    }
}

class Word implements Node {
    String value;
    List<Node> parts;
    String kind;

    Word(String value, List<Node> parts, String kind) {
        this.value = value;
        this.parts = parts;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        String value = this.value;
        value = this._expandAllAnsiCQuotes(value);
        value = this._stripLocaleStringDollars(value);
        value = this._normalizeArrayWhitespace(value);
        value = this._formatCommandSubstitutions(value, false);
        value = this._normalizeParamExpansionNewlines(value);
        value = this._stripArithLineContinuations(value);
        value = this._doubleCtlescSmart(value);
        value = value.replace("", "");
        value = value.replace("\\", "\\\\");
        if (value.endsWith("\\\\") && !value.endsWith("\\\\\\\\")) {
            value = value + "\\\\";
        }
        String escaped = value.replace("\"", "\\\"").replace("\n", "\\n").replace("\t", "\\t");
        return "(word \"" + escaped + "\")";
    }

    public void _appendWithCtlesc(List<Byte> result, int byteVal) {
        result.add((byte) (byteVal));
    }

    public String _doubleCtlescSmart(String value) {
        List<String> result = new ArrayList<>();
        QuoteState quote = ParableFunctions.newQuoteState();
        for (int _i = 0; _i < value.length(); _i++) {
            String c = String.valueOf(value.charAt(_i));
            if (c == "'" && !quote.double_) {
                quote.single = !quote.single;
            } else {
                if (c == "\"" && !quote.single) {
                    quote.double_ = !quote.double_;
                }
            }
            result.add(c);
            if (c == "") {
                if (quote.double_) {
                    int bsCount = 0;
                    for (Integer j : java.util.stream.IntStream.iterate(result.size() - 2, _x -> _x < -1, _x -> _x + -1).boxed().toList()) {
                        if (result.get(j).equals("\\")) {
                            bsCount += 1;
                        } else {
                            break;
                        }
                    }
                    if (bsCount % 2 == 0) {
                        result.add("");
                    }
                } else {
                    result.add("");
                }
            }
        }
        return String.join("", result);
    }

    public String _normalizeParamExpansionNewlines(String value) {
        List<String> result = new ArrayList<>();
        int i = 0;
        QuoteState quote = ParableFunctions.newQuoteState();
        while (i < value.length()) {
            String c = String.valueOf(value.charAt(i));
            if (c.equals("'") && !quote.double_) {
                quote.single = !quote.single;
                result.add(c);
                i += 1;
            } else {
                if (c.equals("\"") && !quote.single) {
                    quote.double_ = !quote.double_;
                    result.add(c);
                    i += 1;
                } else {
                    if (ParableFunctions._isExpansionStart(value, i, "${") && !quote.single) {
                        result.add("$");
                        result.add("{");
                        i += 2;
                        boolean hadLeadingNewline = i < value.length() && String.valueOf(value.charAt(i)).equals("\n");
                        if (hadLeadingNewline) {
                            result.add(" ");
                            i += 1;
                        }
                        int depth = 1;
                        while (i < value.length() && depth > 0) {
                            String ch = String.valueOf(value.charAt(i));
                            if (ch.equals("\\") && i + 1 < value.length() && !quote.single) {
                                if (String.valueOf(value.charAt(i + 1)).equals("\n")) {
                                    i += 2;
                                    continue;
                                }
                                result.add(ch);
                                result.add(String.valueOf(value.charAt(i + 1)));
                                i += 2;
                                continue;
                            }
                            if (ch.equals("'") && !quote.double_) {
                                quote.single = !quote.single;
                            } else {
                                if (ch.equals("\"") && !quote.single) {
                                    quote.double_ = !quote.double_;
                                } else {
                                    if (!quote.inQuotes()) {
                                        if (ch.equals("{")) {
                                            depth += 1;
                                        } else {
                                            if (ch.equals("}")) {
                                                depth -= 1;
                                                if (depth == 0) {
                                                    if (hadLeadingNewline) {
                                                        result.add(" ");
                                                    }
                                                    result.add(ch);
                                                    i += 1;
                                                    break;
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            result.add(ch);
                            i += 1;
                        }
                    } else {
                        result.add(c);
                        i += 1;
                    }
                }
            }
        }
        return String.join("", result);
    }

    public String _shSingleQuote(String s) {
        if (!(!s.equals(""))) {
            return "''";
        }
        if (s.equals("'")) {
            return "\\'";
        }
        List<String> result = new ArrayList<>(List.of("'"));
        for (int _i = 0; _i < s.length(); _i++) {
            String c = String.valueOf(s.charAt(_i));
            if (c == "'") {
                result.add("'\\''");
            } else {
                result.add(c);
            }
        }
        result.add("'");
        return String.join("", result);
    }

    public List<Byte> _ansiCToBytes(String inner) {
        List<Byte> result = new ArrayList<>();
        int i = 0;
        while (i < inner.length()) {
            if (String.valueOf(inner.charAt(i)).equals("\\") && i + 1 < inner.length()) {
                String c = String.valueOf(inner.charAt(i + 1));
                int simple = ParableFunctions._getAnsiEscape(c);
                if (simple >= 0) {
                    result.add((byte) (simple));
                    i += 2;
                } else {
                    if (c.equals("'")) {
                        result.add((byte) (39));
                        i += 2;
                    } else {
                        int j = 0;
                        int byteVal = 0;
                        if (c.equals("x")) {
                            if (i + 2 < inner.length() && String.valueOf(inner.charAt(i + 2)).equals("{")) {
                                j = i + 3;
                                while (j < inner.length() && ParableFunctions._isHexDigit(String.valueOf(inner.charAt(j)))) {
                                    j += 1;
                                }
                                String hexStr = ParableFunctions._substring(inner, i + 3, j);
                                if (j < inner.length() && String.valueOf(inner.charAt(j)).equals("}")) {
                                    j += 1;
                                }
                                if (!(!hexStr.equals(""))) {
                                    return result;
                                }
                                byteVal = (Integer.parseInt(hexStr, 16) & 255);
                                if (byteVal == 0) {
                                    return result;
                                }
                                this._appendWithCtlesc(result, byteVal);
                                i = j;
                            } else {
                                j = i + 2;
                                while (j < inner.length() && j < i + 4 && ParableFunctions._isHexDigit(String.valueOf(inner.charAt(j)))) {
                                    j += 1;
                                }
                                if (j > i + 2) {
                                    byteVal = Integer.parseInt(ParableFunctions._substring(inner, i + 2, j), 16);
                                    if (byteVal == 0) {
                                        return result;
                                    }
                                    this._appendWithCtlesc(result, byteVal);
                                    i = j;
                                } else {
                                    result.add((byte) ((int) (String.valueOf(inner.charAt(i)).charAt(0))));
                                    i += 1;
                                }
                            }
                        } else {
                            int codepoint = 0;
                            if (c.equals("u")) {
                                j = i + 2;
                                while (j < inner.length() && j < i + 6 && ParableFunctions._isHexDigit(String.valueOf(inner.charAt(j)))) {
                                    j += 1;
                                }
                                if (j > i + 2) {
                                    codepoint = Integer.parseInt(ParableFunctions._substring(inner, i + 2, j), 16);
                                    if (codepoint == 0) {
                                        return result;
                                    }
                                    result.addAll(ParableFunctions._stringToBytes(String.valueOf(((char) codepoint))));
                                    i = j;
                                } else {
                                    result.add((byte) ((int) (String.valueOf(inner.charAt(i)).charAt(0))));
                                    i += 1;
                                }
                            } else {
                                if (c.equals("U")) {
                                    j = i + 2;
                                    while (j < inner.length() && j < i + 10 && ParableFunctions._isHexDigit(String.valueOf(inner.charAt(j)))) {
                                        j += 1;
                                    }
                                    if (j > i + 2) {
                                        codepoint = Integer.parseInt(ParableFunctions._substring(inner, i + 2, j), 16);
                                        if (codepoint == 0) {
                                            return result;
                                        }
                                        result.addAll(ParableFunctions._stringToBytes(String.valueOf(((char) codepoint))));
                                        i = j;
                                    } else {
                                        result.add((byte) ((int) (String.valueOf(inner.charAt(i)).charAt(0))));
                                        i += 1;
                                    }
                                } else {
                                    if (c.equals("c")) {
                                        if (i + 3 <= inner.length()) {
                                            String ctrlChar = String.valueOf(inner.charAt(i + 2));
                                            int skipExtra = 0;
                                            if (ctrlChar.equals("\\") && i + 4 <= inner.length() && String.valueOf(inner.charAt(i + 3)).equals("\\")) {
                                                skipExtra = 1;
                                            }
                                            int ctrlVal = ((int) (ctrlChar.charAt(0)) & 31);
                                            if (ctrlVal == 0) {
                                                return result;
                                            }
                                            this._appendWithCtlesc(result, ctrlVal);
                                            i += 3 + skipExtra;
                                        } else {
                                            result.add((byte) ((int) (String.valueOf(inner.charAt(i)).charAt(0))));
                                            i += 1;
                                        }
                                    } else {
                                        if (c.equals("0")) {
                                            j = i + 2;
                                            while (j < inner.length() && j < i + 4 && ParableFunctions._isOctalDigit(String.valueOf(inner.charAt(j)))) {
                                                j += 1;
                                            }
                                            if (j > i + 2) {
                                                byteVal = (Integer.parseInt(ParableFunctions._substring(inner, i + 1, j), 8) & 255);
                                                if (byteVal == 0) {
                                                    return result;
                                                }
                                                this._appendWithCtlesc(result, byteVal);
                                                i = j;
                                            } else {
                                                return result;
                                            }
                                        } else {
                                            if ((c.compareTo("1") >= 0) && (c.compareTo("7") <= 0)) {
                                                j = i + 1;
                                                while (j < inner.length() && j < i + 4 && ParableFunctions._isOctalDigit(String.valueOf(inner.charAt(j)))) {
                                                    j += 1;
                                                }
                                                byteVal = (Integer.parseInt(ParableFunctions._substring(inner, i + 1, j), 8) & 255);
                                                if (byteVal == 0) {
                                                    return result;
                                                }
                                                this._appendWithCtlesc(result, byteVal);
                                                i = j;
                                            } else {
                                                result.add((byte) (92));
                                                result.add((byte) ((int) (c.charAt(0))));
                                                i += 2;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            } else {
                result.addAll(ParableFunctions._stringToBytes(String.valueOf(inner.charAt(i))));
                i += 1;
            }
        }
        return result;
    }

    public String _expandAnsiCEscapes(String value) {
        if (!(value.startsWith("'") && value.endsWith("'"))) {
            return value;
        }
        String inner = ParableFunctions._substring(value, 1, value.length() - 1);
        List<Byte> literalBytes = this._ansiCToBytes(inner);
        String literalStr = String.valueOf(literalBytes);
        return this._shSingleQuote(literalStr);
    }

    public String _expandAllAnsiCQuotes(String value) {
        List<String> result = new ArrayList<>();
        int i = 0;
        QuoteState quote = ParableFunctions.newQuoteState();
        boolean inBacktick = false;
        int braceDepth = 0;
        while (i < value.length()) {
            String ch = String.valueOf(value.charAt(i));
            if (ch.equals("`") && !quote.single) {
                inBacktick = !inBacktick;
                result.add(ch);
                i += 1;
                continue;
            }
            if (inBacktick) {
                if (ch.equals("\\") && i + 1 < value.length()) {
                    result.add(ch);
                    result.add(String.valueOf(value.charAt(i + 1)));
                    i += 2;
                } else {
                    result.add(ch);
                    i += 1;
                }
                continue;
            }
            if (!quote.single) {
                if (ParableFunctions._isExpansionStart(value, i, "${")) {
                    braceDepth += 1;
                    quote.push();
                    result.add("${");
                    i += 2;
                    continue;
                } else {
                    if (ch.equals("}") && braceDepth > 0 && !quote.double_) {
                        braceDepth -= 1;
                        result.add(ch);
                        quote.pop();
                        i += 1;
                        continue;
                    }
                }
            }
            boolean effectiveInDquote = quote.double_;
            if (ch.equals("'") && !effectiveInDquote) {
                boolean isAnsiC = !quote.single && i > 0 && String.valueOf(value.charAt(i - 1)).equals("$") && ParableFunctions._countConsecutiveDollarsBefore(value, i - 1) % 2 == 0;
                if (!isAnsiC) {
                    quote.single = !quote.single;
                }
                result.add(ch);
                i += 1;
            } else {
                if (ch.equals("\"") && !quote.single) {
                    quote.double_ = !quote.double_;
                    result.add(ch);
                    i += 1;
                } else {
                    if (ch.equals("\\") && i + 1 < value.length() && !quote.single) {
                        result.add(ch);
                        result.add(String.valueOf(value.charAt(i + 1)));
                        i += 2;
                    } else {
                        if (ParableFunctions._startsWithAt(value, i, "$'") && !quote.single && !effectiveInDquote && ParableFunctions._countConsecutiveDollarsBefore(value, i) % 2 == 0) {
                            int j = i + 2;
                            while (j < value.length()) {
                                if (String.valueOf(value.charAt(j)).equals("\\") && j + 1 < value.length()) {
                                    j += 2;
                                } else {
                                    if (String.valueOf(value.charAt(j)).equals("'")) {
                                        j += 1;
                                        break;
                                    } else {
                                        j += 1;
                                    }
                                }
                            }
                            String ansiStr = ParableFunctions._substring(value, i, j);
                            String expanded = this._expandAnsiCEscapes(ParableFunctions._substring(ansiStr, 1, ansiStr.length()));
                            boolean outerInDquote = quote.outerDouble();
                            if (braceDepth > 0 && outerInDquote && expanded.startsWith("'") && expanded.endsWith("'")) {
                                String inner = ParableFunctions._substring(expanded, 1, expanded.length() - 1);
                                if (inner.indexOf("") == -1) {
                                    String resultStr = String.join("", result);
                                    boolean inPattern = false;
                                    int lastBraceIdx = resultStr.lastIndexOf("${");
                                    if (lastBraceIdx >= 0) {
                                        String afterBrace = resultStr.substring(lastBraceIdx + 2);
                                        int varNameLen = 0;
                                        if (!afterBrace.equals("")) {
                                            if ("@*#?-$!0123456789_".indexOf(String.valueOf(afterBrace.charAt(0))) != -1) {
                                                varNameLen = 1;
                                            } else {
                                                if (String.valueOf(afterBrace.charAt(0)).chars().allMatch(Character::isLetter) || String.valueOf(afterBrace.charAt(0)).equals("_")) {
                                                    while (varNameLen < afterBrace.length()) {
                                                        String c = String.valueOf(afterBrace.charAt(varNameLen));
                                                        if (!(c.chars().allMatch(Character::isLetterOrDigit) || c.equals("_"))) {
                                                            break;
                                                        }
                                                        varNameLen += 1;
                                                    }
                                                }
                                            }
                                        }
                                        if (varNameLen > 0 && varNameLen < afterBrace.length() && "#?-".indexOf(String.valueOf(afterBrace.charAt(0))) == -1) {
                                            String opStart = afterBrace.substring(varNameLen);
                                            if (opStart.startsWith("@") && opStart.length() > 1) {
                                                opStart = opStart.substring(1);
                                            }
                                            for (String op : new ArrayList<>(List.of("//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"))) {
                                                if (opStart.startsWith(op)) {
                                                    inPattern = true;
                                                    break;
                                                }
                                            }
                                            if (!inPattern && !opStart.equals("") && "%#/^,~:+-=?".indexOf(String.valueOf(opStart.charAt(0))) == -1) {
                                                for (String op : new ArrayList<>(List.of("//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"))) {
                                                    if (opStart.indexOf(op) != -1) {
                                                        inPattern = true;
                                                        break;
                                                    }
                                                }
                                            }
                                        } else {
                                            if (varNameLen == 0 && afterBrace.length() > 1) {
                                                String firstChar = String.valueOf(afterBrace.charAt(0));
                                                if ("%#/^,".indexOf(firstChar) == -1) {
                                                    String rest = afterBrace.substring(1);
                                                    for (String op : new ArrayList<>(List.of("//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"))) {
                                                        if (rest.indexOf(op) != -1) {
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
                            result.add(expanded);
                            i = j;
                        } else {
                            result.add(ch);
                            i += 1;
                        }
                    }
                }
            }
        }
        return String.join("", result);
    }

    public String _stripLocaleStringDollars(String value) {
        List<String> result = new ArrayList<>();
        int i = 0;
        int braceDepth = 0;
        int bracketDepth = 0;
        QuoteState quote = ParableFunctions.newQuoteState();
        QuoteState braceQuote = ParableFunctions.newQuoteState();
        boolean bracketInDoubleQuote = false;
        while (i < value.length()) {
            String ch = String.valueOf(value.charAt(i));
            if (ch.equals("\\") && i + 1 < value.length() && !quote.single && !braceQuote.single) {
                result.add(ch);
                result.add(String.valueOf(value.charAt(i + 1)));
                i += 2;
            } else {
                if (ParableFunctions._startsWithAt(value, i, "${") && !quote.single && !braceQuote.single && i == 0 || !String.valueOf(value.charAt(i - 1)).equals("$")) {
                    braceDepth += 1;
                    braceQuote.double_ = false;
                    braceQuote.single = false;
                    result.add("$");
                    result.add("{");
                    i += 2;
                } else {
                    if (ch.equals("}") && braceDepth > 0 && !quote.single && !braceQuote.double_ && !braceQuote.single) {
                        braceDepth -= 1;
                        result.add(ch);
                        i += 1;
                    } else {
                        if (ch.equals("[") && braceDepth > 0 && !quote.single && !braceQuote.double_) {
                            bracketDepth += 1;
                            bracketInDoubleQuote = false;
                            result.add(ch);
                            i += 1;
                        } else {
                            if (ch.equals("]") && bracketDepth > 0 && !quote.single && !bracketInDoubleQuote) {
                                bracketDepth -= 1;
                                result.add(ch);
                                i += 1;
                            } else {
                                if (ch.equals("'") && !quote.double_ && braceDepth == 0) {
                                    quote.single = !quote.single;
                                    result.add(ch);
                                    i += 1;
                                } else {
                                    if (ch.equals("\"") && !quote.single && braceDepth == 0) {
                                        quote.double_ = !quote.double_;
                                        result.add(ch);
                                        i += 1;
                                    } else {
                                        if (ch.equals("\"") && !quote.single && bracketDepth > 0) {
                                            bracketInDoubleQuote = !bracketInDoubleQuote;
                                            result.add(ch);
                                            i += 1;
                                        } else {
                                            if (ch.equals("\"") && !quote.single && !braceQuote.single && braceDepth > 0) {
                                                braceQuote.double_ = !braceQuote.double_;
                                                result.add(ch);
                                                i += 1;
                                            } else {
                                                if (ch.equals("'") && !quote.double_ && !braceQuote.double_ && braceDepth > 0) {
                                                    braceQuote.single = !braceQuote.single;
                                                    result.add(ch);
                                                    i += 1;
                                                } else {
                                                    if (ParableFunctions._startsWithAt(value, i, "$\"") && !quote.single && !braceQuote.single && braceDepth > 0 || bracketDepth > 0 || !quote.double_ && !braceQuote.double_ && !bracketInDoubleQuote) {
                                                        int dollarCount = 1 + ParableFunctions._countConsecutiveDollarsBefore(value, i);
                                                        if (dollarCount % 2 == 1) {
                                                            result.add("\"");
                                                            if (bracketDepth > 0) {
                                                                bracketInDoubleQuote = true;
                                                            } else {
                                                                if (braceDepth > 0) {
                                                                    braceQuote.double_ = true;
                                                                } else {
                                                                    quote.double_ = true;
                                                                }
                                                            }
                                                            i += 2;
                                                        } else {
                                                            result.add(ch);
                                                            i += 1;
                                                        }
                                                    } else {
                                                        result.add(ch);
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
        return String.join("", result);
    }

    public String _normalizeArrayWhitespace(String value) {
        int i = 0;
        if (!(i < value.length() && String.valueOf(value.charAt(i)).chars().allMatch(Character::isLetter) || String.valueOf(value.charAt(i)).equals("_"))) {
            return value;
        }
        i += 1;
        while (i < value.length() && String.valueOf(value.charAt(i)).chars().allMatch(Character::isLetterOrDigit) || String.valueOf(value.charAt(i)).equals("_")) {
            i += 1;
        }
        while (i < value.length() && String.valueOf(value.charAt(i)).equals("[")) {
            int depth = 1;
            i += 1;
            while (i < value.length() && depth > 0) {
                if (String.valueOf(value.charAt(i)).equals("[")) {
                    depth += 1;
                } else {
                    if (String.valueOf(value.charAt(i)).equals("]")) {
                        depth -= 1;
                    }
                }
                i += 1;
            }
            if (depth != 0) {
                return value;
            }
        }
        if (i < value.length() && String.valueOf(value.charAt(i)).equals("+")) {
            i += 1;
        }
        if (!(i + 1 < value.length() && String.valueOf(value.charAt(i)).equals("=") && String.valueOf(value.charAt(i + 1)).equals("("))) {
            return value;
        }
        String prefix = ParableFunctions._substring(value, 0, i + 1);
        int openParenPos = i + 1;
        int closeParenPos = 0;
        if (value.endsWith(")")) {
            closeParenPos = value.length() - 1;
        } else {
            closeParenPos = this._findMatchingParen(value, openParenPos);
            if (closeParenPos < 0) {
                return value;
            }
        }
        String inner = ParableFunctions._substring(value, openParenPos + 1, closeParenPos);
        String suffix = ParableFunctions._substring(value, closeParenPos + 1, value.length());
        String result = this._normalizeArrayInner(inner);
        return prefix + "(" + result + ")" + suffix;
    }

    public int _findMatchingParen(String value, int openPos) {
        if (openPos >= value.length() || !String.valueOf(value.charAt(openPos)).equals("(")) {
            return -1;
        }
        int i = openPos + 1;
        int depth = 1;
        QuoteState quote = ParableFunctions.newQuoteState();
        while (i < value.length() && depth > 0) {
            String ch = String.valueOf(value.charAt(i));
            if (ch.equals("\\") && i + 1 < value.length() && !quote.single) {
                i += 2;
                continue;
            }
            if (ch.equals("'") && !quote.double_) {
                quote.single = !quote.single;
                i += 1;
                continue;
            }
            if (ch.equals("\"") && !quote.single) {
                quote.double_ = !quote.double_;
                i += 1;
                continue;
            }
            if (quote.single || quote.double_) {
                i += 1;
                continue;
            }
            if (ch.equals("#")) {
                while (i < value.length() && !String.valueOf(value.charAt(i)).equals("\n")) {
                    i += 1;
                }
                continue;
            }
            if (ch.equals("(")) {
                depth += 1;
            } else {
                if (ch.equals(")")) {
                    depth -= 1;
                    if (depth == 0) {
                        return i;
                    }
                }
            }
            i += 1;
        }
        return -1;
    }

    public String _normalizeArrayInner(String inner) {
        List<String> normalized = new ArrayList<>();
        int i = 0;
        boolean inWhitespace = true;
        int braceDepth = 0;
        int bracketDepth = 0;
        while (i < inner.length()) {
            String ch = String.valueOf(inner.charAt(i));
            if (ParableFunctions._isWhitespace(ch)) {
                if (!inWhitespace && !normalized.isEmpty() && braceDepth == 0 && bracketDepth == 0) {
                    normalized.add(" ");
                    inWhitespace = true;
                }
                if (braceDepth > 0 || bracketDepth > 0) {
                    normalized.add(ch);
                }
                i += 1;
            } else {
                int j = 0;
                if (ch.equals("'")) {
                    inWhitespace = false;
                    j = i + 1;
                    while (j < inner.length() && !String.valueOf(inner.charAt(j)).equals("'")) {
                        j += 1;
                    }
                    normalized.add(ParableFunctions._substring(inner, i, j + 1));
                    i = j + 1;
                } else {
                    if (ch.equals("\"")) {
                        inWhitespace = false;
                        j = i + 1;
                        List<String> dqContent = new ArrayList<>(List.of("\""));
                        int dqBraceDepth = 0;
                        while (j < inner.length()) {
                            if (String.valueOf(inner.charAt(j)).equals("\\") && j + 1 < inner.length()) {
                                if (String.valueOf(inner.charAt(j + 1)).equals("\n")) {
                                    j += 2;
                                } else {
                                    dqContent.add(String.valueOf(inner.charAt(j)));
                                    dqContent.add(String.valueOf(inner.charAt(j + 1)));
                                    j += 2;
                                }
                            } else {
                                if (ParableFunctions._isExpansionStart(inner, j, "${")) {
                                    dqContent.add("${");
                                    dqBraceDepth += 1;
                                    j += 2;
                                } else {
                                    if (String.valueOf(inner.charAt(j)).equals("}") && dqBraceDepth > 0) {
                                        dqContent.add("}");
                                        dqBraceDepth -= 1;
                                        j += 1;
                                    } else {
                                        if (String.valueOf(inner.charAt(j)).equals("\"") && dqBraceDepth == 0) {
                                            dqContent.add("\"");
                                            j += 1;
                                            break;
                                        } else {
                                            dqContent.add(String.valueOf(inner.charAt(j)));
                                            j += 1;
                                        }
                                    }
                                }
                            }
                        }
                        normalized.add(String.join("", dqContent));
                        i = j;
                    } else {
                        if (ch.equals("\\") && i + 1 < inner.length()) {
                            if (String.valueOf(inner.charAt(i + 1)).equals("\n")) {
                                i += 2;
                            } else {
                                inWhitespace = false;
                                normalized.add(ParableFunctions._substring(inner, i, i + 2));
                                i += 2;
                            }
                        } else {
                            int depth = 0;
                            if (ParableFunctions._isExpansionStart(inner, i, "$((")) {
                                inWhitespace = false;
                                j = i + 3;
                                depth = 1;
                                while (j < inner.length() && depth > 0) {
                                    if (j + 1 < inner.length() && String.valueOf(inner.charAt(j)).equals("(") && String.valueOf(inner.charAt(j + 1)).equals("(")) {
                                        depth += 1;
                                        j += 2;
                                    } else {
                                        if (j + 1 < inner.length() && String.valueOf(inner.charAt(j)).equals(")") && String.valueOf(inner.charAt(j + 1)).equals(")")) {
                                            depth -= 1;
                                            j += 2;
                                        } else {
                                            j += 1;
                                        }
                                    }
                                }
                                normalized.add(ParableFunctions._substring(inner, i, j));
                                i = j;
                            } else {
                                if (ParableFunctions._isExpansionStart(inner, i, "$(")) {
                                    inWhitespace = false;
                                    j = i + 2;
                                    depth = 1;
                                    while (j < inner.length() && depth > 0) {
                                        if (String.valueOf(inner.charAt(j)).equals("(") && j > 0 && String.valueOf(inner.charAt(j - 1)).equals("$")) {
                                            depth += 1;
                                        } else {
                                            if (String.valueOf(inner.charAt(j)).equals(")")) {
                                                depth -= 1;
                                            } else {
                                                if (String.valueOf(inner.charAt(j)).equals("'")) {
                                                    j += 1;
                                                    while (j < inner.length() && !String.valueOf(inner.charAt(j)).equals("'")) {
                                                        j += 1;
                                                    }
                                                } else {
                                                    if (String.valueOf(inner.charAt(j)).equals("\"")) {
                                                        j += 1;
                                                        while (j < inner.length()) {
                                                            if (String.valueOf(inner.charAt(j)).equals("\\") && j + 1 < inner.length()) {
                                                                j += 2;
                                                                continue;
                                                            }
                                                            if (String.valueOf(inner.charAt(j)).equals("\"")) {
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
                                    normalized.add(ParableFunctions._substring(inner, i, j));
                                    i = j;
                                } else {
                                    if (ch.equals("<") || ch.equals(">") && i + 1 < inner.length() && String.valueOf(inner.charAt(i + 1)).equals("(")) {
                                        inWhitespace = false;
                                        j = i + 2;
                                        depth = 1;
                                        while (j < inner.length() && depth > 0) {
                                            if (String.valueOf(inner.charAt(j)).equals("(")) {
                                                depth += 1;
                                            } else {
                                                if (String.valueOf(inner.charAt(j)).equals(")")) {
                                                    depth -= 1;
                                                } else {
                                                    if (String.valueOf(inner.charAt(j)).equals("'")) {
                                                        j += 1;
                                                        while (j < inner.length() && !String.valueOf(inner.charAt(j)).equals("'")) {
                                                            j += 1;
                                                        }
                                                    } else {
                                                        if (String.valueOf(inner.charAt(j)).equals("\"")) {
                                                            j += 1;
                                                            while (j < inner.length()) {
                                                                if (String.valueOf(inner.charAt(j)).equals("\\") && j + 1 < inner.length()) {
                                                                    j += 2;
                                                                    continue;
                                                                }
                                                                if (String.valueOf(inner.charAt(j)).equals("\"")) {
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
                                        normalized.add(ParableFunctions._substring(inner, i, j));
                                        i = j;
                                    } else {
                                        if (ParableFunctions._isExpansionStart(inner, i, "${")) {
                                            inWhitespace = false;
                                            normalized.add("${");
                                            braceDepth += 1;
                                            i += 2;
                                        } else {
                                            if (ch.equals("{") && braceDepth > 0) {
                                                normalized.add(ch);
                                                braceDepth += 1;
                                                i += 1;
                                            } else {
                                                if (ch.equals("}") && braceDepth > 0) {
                                                    normalized.add(ch);
                                                    braceDepth -= 1;
                                                    i += 1;
                                                } else {
                                                    if (ch.equals("#") && braceDepth == 0 && inWhitespace) {
                                                        while (i < inner.length() && !String.valueOf(inner.charAt(i)).equals("\n")) {
                                                            i += 1;
                                                        }
                                                    } else {
                                                        if (ch.equals("[")) {
                                                            if (inWhitespace || bracketDepth > 0) {
                                                                bracketDepth += 1;
                                                            }
                                                            inWhitespace = false;
                                                            normalized.add(ch);
                                                            i += 1;
                                                        } else {
                                                            if (ch.equals("]") && bracketDepth > 0) {
                                                                normalized.add(ch);
                                                                bracketDepth -= 1;
                                                                i += 1;
                                                            } else {
                                                                inWhitespace = false;
                                                                normalized.add(ch);
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
        return String.join("", normalized).stripTrailing();
    }

    public String _stripArithLineContinuations(String value) {
        List<String> result = new ArrayList<>();
        int i = 0;
        while (i < value.length()) {
            if (ParableFunctions._isExpansionStart(value, i, "$((")) {
                int start = i;
                i += 3;
                int depth = 2;
                List<String> arithContent = new ArrayList<>();
                int firstCloseIdx = -1;
                while (i < value.length() && depth > 0) {
                    if (String.valueOf(value.charAt(i)).equals("(")) {
                        arithContent.add("(");
                        depth += 1;
                        i += 1;
                        if (depth > 1) {
                            firstCloseIdx = -1;
                        }
                    } else {
                        if (String.valueOf(value.charAt(i)).equals(")")) {
                            if (depth == 2) {
                                firstCloseIdx = arithContent.size();
                            }
                            depth -= 1;
                            if (depth > 0) {
                                arithContent.add(")");
                            }
                            i += 1;
                        } else {
                            if (String.valueOf(value.charAt(i)).equals("\\") && i + 1 < value.length() && String.valueOf(value.charAt(i + 1)).equals("\n")) {
                                int numBackslashes = 0;
                                int j = arithContent.size() - 1;
                                while (j >= 0 && arithContent.get(j).equals("\n")) {
                                    j -= 1;
                                }
                                while (j >= 0 && arithContent.get(j).equals("\\")) {
                                    numBackslashes += 1;
                                    j -= 1;
                                }
                                if (numBackslashes % 2 == 1) {
                                    arithContent.add("\\");
                                    arithContent.add("\n");
                                    i += 2;
                                } else {
                                    i += 2;
                                }
                                if (depth == 1) {
                                    firstCloseIdx = -1;
                                }
                            } else {
                                arithContent.add(String.valueOf(value.charAt(i)));
                                i += 1;
                                if (depth == 1) {
                                    firstCloseIdx = -1;
                                }
                            }
                        }
                    }
                }
                if (depth == 0 || depth == 1 && firstCloseIdx != -1) {
                    String content = String.join("", arithContent);
                    if (firstCloseIdx != -1) {
                        content = content.substring(0, firstCloseIdx);
                        String closing = (depth == 0 ? "))" : ")");
                        result.add("$((" + content + closing);
                    } else {
                        result.add("$((" + content + ")");
                    }
                } else {
                    result.add(ParableFunctions._substring(value, start, i));
                }
            } else {
                result.add(String.valueOf(value.charAt(i)));
                i += 1;
            }
        }
        return String.join("", result);
    }

    public List<Node> _collectCmdsubs(Node node) {
        List<Node> result = new ArrayList<>();
        if (node instanceof CommandSubstitution nodeCommandSubstitution) {
            result.add(nodeCommandSubstitution);
        } else if (node instanceof Array nodeArray) {
            for (Word elem : nodeArray.elements) {
                for (Node p : elem.parts) {
                    if (p instanceof CommandSubstitution pCommandSubstitution) {
                        result.add(pCommandSubstitution);
                    } else {
                        result.addAll(this._collectCmdsubs(p));
                    }
                }
            }
        } else if (node instanceof ArithmeticExpansion nodeArithmeticExpansion) {
            if (nodeArithmeticExpansion.expression != null) {
                result.addAll(this._collectCmdsubs(nodeArithmeticExpansion.expression));
            }
        } else if (node instanceof ArithBinaryOp nodeArithBinaryOp) {
            result.addAll(this._collectCmdsubs(nodeArithBinaryOp.left));
            result.addAll(this._collectCmdsubs(nodeArithBinaryOp.right));
        } else if (node instanceof ArithComma nodeArithComma) {
            result.addAll(this._collectCmdsubs(nodeArithComma.left));
            result.addAll(this._collectCmdsubs(nodeArithComma.right));
        } else if (node instanceof ArithUnaryOp nodeArithUnaryOp) {
            result.addAll(this._collectCmdsubs(nodeArithUnaryOp.operand));
        } else if (node instanceof ArithPreIncr nodeArithPreIncr) {
            result.addAll(this._collectCmdsubs(nodeArithPreIncr.operand));
        } else if (node instanceof ArithPostIncr nodeArithPostIncr) {
            result.addAll(this._collectCmdsubs(nodeArithPostIncr.operand));
        } else if (node instanceof ArithPreDecr nodeArithPreDecr) {
            result.addAll(this._collectCmdsubs(nodeArithPreDecr.operand));
        } else if (node instanceof ArithPostDecr nodeArithPostDecr) {
            result.addAll(this._collectCmdsubs(nodeArithPostDecr.operand));
        } else if (node instanceof ArithTernary nodeArithTernary) {
            result.addAll(this._collectCmdsubs(nodeArithTernary.condition));
            result.addAll(this._collectCmdsubs(nodeArithTernary.ifTrue));
            result.addAll(this._collectCmdsubs(nodeArithTernary.ifFalse));
        } else if (node instanceof ArithAssign nodeArithAssign) {
            result.addAll(this._collectCmdsubs(nodeArithAssign.target));
            result.addAll(this._collectCmdsubs(nodeArithAssign.value));
        }
        return result;
    }

    public List<Node> _collectProcsubs(Node node) {
        List<Node> result = new ArrayList<>();
        if (node instanceof ProcessSubstitution nodeProcessSubstitution) {
            result.add(nodeProcessSubstitution);
        } else if (node instanceof Array nodeArray) {
            for (Word elem : nodeArray.elements) {
                for (Node p : elem.parts) {
                    if (p instanceof ProcessSubstitution pProcessSubstitution) {
                        result.add(pProcessSubstitution);
                    } else {
                        result.addAll(this._collectProcsubs(p));
                    }
                }
            }
        }
        return result;
    }

    public String _formatCommandSubstitutions(String value, boolean inArith) {
        List<Node> cmdsubParts = new ArrayList<>();
        List<Node> procsubParts = new ArrayList<>();
        boolean hasArith = false;
        for (Node p : this.parts) {
            if (p instanceof CommandSubstitution pCommandSubstitution) {
                cmdsubParts.add(pCommandSubstitution);
            } else if (p instanceof ProcessSubstitution pProcessSubstitution) {
                procsubParts.add(pProcessSubstitution);
            } else if (p instanceof ArithmeticExpansion pArithmeticExpansion) {
                hasArith = true;
            } else {
                cmdsubParts.addAll(this._collectCmdsubs(p));
                procsubParts.addAll(this._collectProcsubs(p));
            }
        }
        boolean hasBraceCmdsub = value.indexOf("${ ") != -1 || value.indexOf("${\t") != -1 || value.indexOf("${\n") != -1 || value.indexOf("${|") != -1;
        boolean hasUntrackedCmdsub = false;
        boolean hasUntrackedProcsub = false;
        int idx = 0;
        QuoteState scanQuote = ParableFunctions.newQuoteState();
        while (idx < value.length()) {
            if (String.valueOf(value.charAt(idx)).equals("\"")) {
                scanQuote.double_ = !scanQuote.double_;
                idx += 1;
            } else {
                if (String.valueOf(value.charAt(idx)).equals("'") && !scanQuote.double_) {
                    idx += 1;
                    while (idx < value.length() && !String.valueOf(value.charAt(idx)).equals("'")) {
                        idx += 1;
                    }
                    if (idx < value.length()) {
                        idx += 1;
                    }
                } else {
                    if (ParableFunctions._startsWithAt(value, idx, "$(") && !ParableFunctions._startsWithAt(value, idx, "$((") && !ParableFunctions._isBackslashEscaped(value, idx) && !ParableFunctions._isDollarDollarParen(value, idx)) {
                        hasUntrackedCmdsub = true;
                        break;
                    } else {
                        if (ParableFunctions._startsWithAt(value, idx, "<(") || ParableFunctions._startsWithAt(value, idx, ">(") && !scanQuote.double_) {
                            if (idx == 0 || !String.valueOf(value.charAt(idx - 1)).chars().allMatch(Character::isLetterOrDigit) && "\"'".indexOf(String.valueOf(value.charAt(idx - 1))) == -1) {
                                hasUntrackedProcsub = true;
                                break;
                            }
                            idx += 1;
                        } else {
                            idx += 1;
                        }
                    }
                }
            }
        }
        boolean hasParamWithProcsubPattern = value.indexOf("${") != -1 && value.indexOf("<(") != -1 || value.indexOf(">(") != -1;
        if (!(!cmdsubParts.isEmpty()) && !(!procsubParts.isEmpty()) && !hasBraceCmdsub && !hasUntrackedCmdsub && !hasUntrackedProcsub && !hasParamWithProcsubPattern) {
            return value;
        }
        List<String> result = new ArrayList<>();
        int i = 0;
        int cmdsubIdx = 0;
        int procsubIdx = 0;
        QuoteState mainQuote = ParableFunctions.newQuoteState();
        int extglobDepth = 0;
        int deprecatedArithDepth = 0;
        int arithDepth = 0;
        int arithParenDepth = 0;
        while (i < value.length()) {
            if (i > 0 && ParableFunctions._isExtglobPrefix(String.valueOf(value.charAt(i - 1))) && String.valueOf(value.charAt(i)).equals("(") && !ParableFunctions._isBackslashEscaped(value, i - 1)) {
                extglobDepth += 1;
                result.add(String.valueOf(value.charAt(i)));
                i += 1;
                continue;
            }
            if (String.valueOf(value.charAt(i)).equals(")") && extglobDepth > 0) {
                extglobDepth -= 1;
                result.add(String.valueOf(value.charAt(i)));
                i += 1;
                continue;
            }
            if (ParableFunctions._startsWithAt(value, i, "$[") && !ParableFunctions._isBackslashEscaped(value, i)) {
                deprecatedArithDepth += 1;
                result.add(String.valueOf(value.charAt(i)));
                i += 1;
                continue;
            }
            if (String.valueOf(value.charAt(i)).equals("]") && deprecatedArithDepth > 0) {
                deprecatedArithDepth -= 1;
                result.add(String.valueOf(value.charAt(i)));
                i += 1;
                continue;
            }
            if (ParableFunctions._isExpansionStart(value, i, "$((") && !ParableFunctions._isBackslashEscaped(value, i) && hasArith) {
                arithDepth += 1;
                arithParenDepth += 2;
                result.add("$((");
                i += 3;
                continue;
            }
            if (arithDepth > 0 && arithParenDepth == 2 && ParableFunctions._startsWithAt(value, i, "))")) {
                arithDepth -= 1;
                arithParenDepth -= 2;
                result.add("))");
                i += 2;
                continue;
            }
            if (arithDepth > 0) {
                if (String.valueOf(value.charAt(i)).equals("(")) {
                    arithParenDepth += 1;
                    result.add(String.valueOf(value.charAt(i)));
                    i += 1;
                    continue;
                } else {
                    if (String.valueOf(value.charAt(i)).equals(")")) {
                        arithParenDepth -= 1;
                        result.add(String.valueOf(value.charAt(i)));
                        i += 1;
                        continue;
                    }
                }
            }
            int j = 0;
            if (ParableFunctions._isExpansionStart(value, i, "$((") && !hasArith) {
                j = ParableFunctions._findCmdsubEnd(value, i + 2);
                result.add(ParableFunctions._substring(value, i, j));
                if (cmdsubIdx < cmdsubParts.size()) {
                    cmdsubIdx += 1;
                }
                i = j;
                continue;
            }
            String inner = "";
            Node node = null;
            String formatted = "";
            Parser parser = null;
            Node parsed = null;
            if (ParableFunctions._startsWithAt(value, i, "$(") && !ParableFunctions._startsWithAt(value, i, "$((") && !ParableFunctions._isBackslashEscaped(value, i) && !ParableFunctions._isDollarDollarParen(value, i)) {
                j = ParableFunctions._findCmdsubEnd(value, i + 2);
                if (extglobDepth > 0) {
                    result.add(ParableFunctions._substring(value, i, j));
                    if (cmdsubIdx < cmdsubParts.size()) {
                        cmdsubIdx += 1;
                    }
                    i = j;
                    continue;
                }
                inner = ParableFunctions._substring(value, i + 2, j - 1);
                if (cmdsubIdx < cmdsubParts.size()) {
                    node = cmdsubParts.get(cmdsubIdx);
                    formatted = ParableFunctions._formatCmdsubNode(((CommandSubstitution) node).command, 0, false, false, false);
                    cmdsubIdx += 1;
                } else {
                    try {
                        parser = ParableFunctions.newParser(inner, false, false);
                        parsed = parser.parseList(true);
                        formatted = (parsed != null ? ParableFunctions._formatCmdsubNode(parsed, 0, false, false, false) : "");
                    } catch (Exception e) {
                        formatted = inner;
                    }
                }
                if (formatted.startsWith("(")) {
                    result.add("$( " + formatted + ")");
                } else {
                    result.add("$(" + formatted + ")");
                }
                i = j;
            } else {
                if (String.valueOf(value.charAt(i)).equals("`") && cmdsubIdx < cmdsubParts.size()) {
                    j = i + 1;
                    while (j < value.length()) {
                        if (String.valueOf(value.charAt(j)).equals("\\") && j + 1 < value.length()) {
                            j += 2;
                            continue;
                        }
                        if (String.valueOf(value.charAt(j)).equals("`")) {
                            j += 1;
                            break;
                        }
                        j += 1;
                    }
                    result.add(ParableFunctions._substring(value, i, j));
                    cmdsubIdx += 1;
                    i = j;
                } else {
                    String prefix = "";
                    if (ParableFunctions._isExpansionStart(value, i, "${") && i + 2 < value.length() && ParableFunctions._isFunsubChar(String.valueOf(value.charAt(i + 2))) && !ParableFunctions._isBackslashEscaped(value, i)) {
                        j = ParableFunctions._findFunsubEnd(value, i + 2);
                        Node cmdsubNode = (cmdsubIdx < cmdsubParts.size() ? cmdsubParts.get(cmdsubIdx) : null);
                        if ((cmdsubNode instanceof CommandSubstitution) && ((CommandSubstitution) cmdsubNode).brace) {
                            node = cmdsubNode;
                            formatted = ParableFunctions._formatCmdsubNode(((CommandSubstitution) node).command, 0, false, false, false);
                            boolean hasPipe = String.valueOf(value.charAt(i + 2)).equals("|");
                            prefix = (hasPipe ? "${|" : "${ ");
                            String origInner = ParableFunctions._substring(value, i + 2, j - 1);
                            boolean endsWithNewline = origInner.endsWith("\n");
                            String suffix = "";
                            if (!(!formatted.equals("")) || formatted.chars().allMatch(Character::isWhitespace)) {
                                suffix = "}";
                            } else {
                                if (formatted.endsWith("&") || formatted.endsWith("& ")) {
                                    suffix = (formatted.endsWith("&") ? " }" : "}");
                                } else {
                                    if (endsWithNewline) {
                                        suffix = "\n }";
                                    } else {
                                        suffix = "; }";
                                    }
                                }
                            }
                            result.add(prefix + formatted + suffix);
                            cmdsubIdx += 1;
                        } else {
                            result.add(ParableFunctions._substring(value, i, j));
                        }
                        i = j;
                    } else {
                        if (ParableFunctions._startsWithAt(value, i, ">(") || ParableFunctions._startsWithAt(value, i, "<(") && !mainQuote.double_ && deprecatedArithDepth == 0 && arithDepth == 0) {
                            boolean isProcsub = i == 0 || !String.valueOf(value.charAt(i - 1)).chars().allMatch(Character::isLetterOrDigit) && "\"'".indexOf(String.valueOf(value.charAt(i - 1))) == -1;
                            if (extglobDepth > 0) {
                                j = ParableFunctions._findCmdsubEnd(value, i + 2);
                                result.add(ParableFunctions._substring(value, i, j));
                                if (procsubIdx < procsubParts.size()) {
                                    procsubIdx += 1;
                                }
                                i = j;
                                continue;
                            }
                            String direction = "";
                            boolean compact = false;
                            String stripped = "";
                            if (procsubIdx < procsubParts.size()) {
                                direction = String.valueOf(value.charAt(i));
                                j = ParableFunctions._findCmdsubEnd(value, i + 2);
                                node = procsubParts.get(procsubIdx);
                                compact = ParableFunctions._startsWithSubshell(((ProcessSubstitution) node).command);
                                formatted = ParableFunctions._formatCmdsubNode(((ProcessSubstitution) node).command, 0, true, compact, true);
                                String rawContent = ParableFunctions._substring(value, i + 2, j - 1);
                                if (((ProcessSubstitution) node).command.getKind() == "subshell") {
                                    int leadingWsEnd = 0;
                                    while (leadingWsEnd < rawContent.length() && " \t\n".indexOf(String.valueOf(rawContent.charAt(leadingWsEnd))) != -1) {
                                        leadingWsEnd += 1;
                                    }
                                    String leadingWs = rawContent.substring(0, leadingWsEnd);
                                    stripped = rawContent.substring(leadingWsEnd);
                                    if (stripped.startsWith("(")) {
                                        if (!leadingWs.equals("")) {
                                            String normalizedWs = leadingWs.replace("\n", " ").replace("\t", " ");
                                            String spaced = ParableFunctions._formatCmdsubNode(((ProcessSubstitution) node).command, 0, false, false, false);
                                            result.add(direction + "(" + normalizedWs + spaced + ")");
                                        } else {
                                            rawContent = rawContent.replace("\\\n", "");
                                            result.add(direction + "(" + rawContent + ")");
                                        }
                                        procsubIdx += 1;
                                        i = j;
                                        continue;
                                    }
                                }
                                rawContent = ParableFunctions._substring(value, i + 2, j - 1);
                                String rawStripped = rawContent.replace("\\\n", "");
                                if (ParableFunctions._startsWithSubshell(((ProcessSubstitution) node).command) && !formatted.equals(rawStripped)) {
                                    result.add(direction + "(" + rawStripped + ")");
                                } else {
                                    String finalOutput = direction + "(" + formatted + ")";
                                    result.add(finalOutput);
                                }
                                procsubIdx += 1;
                                i = j;
                            } else {
                                if (isProcsub && !this.parts.isEmpty()) {
                                    direction = String.valueOf(value.charAt(i));
                                    j = ParableFunctions._findCmdsubEnd(value, i + 2);
                                    if (j > value.length() || j > 0 && j <= value.length() && !String.valueOf(value.charAt(j - 1)).equals(")")) {
                                        result.add(String.valueOf(value.charAt(i)));
                                        i += 1;
                                        continue;
                                    }
                                    inner = ParableFunctions._substring(value, i + 2, j - 1);
                                    try {
                                        parser = ParableFunctions.newParser(inner, false, false);
                                        parsed = parser.parseList(true);
                                        if (parsed != null && parser.pos == inner.length() && inner.indexOf("\n") == -1) {
                                            compact = ParableFunctions._startsWithSubshell(parsed);
                                            formatted = ParableFunctions._formatCmdsubNode(parsed, 0, true, compact, true);
                                        } else {
                                            formatted = inner;
                                        }
                                    } catch (Exception e) {
                                        formatted = inner;
                                    }
                                    result.add(direction + "(" + formatted + ")");
                                    i = j;
                                } else {
                                    if (isProcsub) {
                                        direction = String.valueOf(value.charAt(i));
                                        j = ParableFunctions._findCmdsubEnd(value, i + 2);
                                        if (j > value.length() || j > 0 && j <= value.length() && !String.valueOf(value.charAt(j - 1)).equals(")")) {
                                            result.add(String.valueOf(value.charAt(i)));
                                            i += 1;
                                            continue;
                                        }
                                        inner = ParableFunctions._substring(value, i + 2, j - 1);
                                        if (inArith) {
                                            result.add(direction + "(" + inner + ")");
                                        } else {
                                            if (!inner.trim().equals("")) {
                                                stripped = inner.replaceFirst("^[" + " \t" + "]+", "");
                                                result.add(direction + "(" + stripped + ")");
                                            } else {
                                                result.add(direction + "(" + inner + ")");
                                            }
                                        }
                                        i = j;
                                    } else {
                                        result.add(String.valueOf(value.charAt(i)));
                                        i += 1;
                                    }
                                }
                            }
                        } else {
                            int depth = 0;
                            if (ParableFunctions._isExpansionStart(value, i, "${ ") || ParableFunctions._isExpansionStart(value, i, "${\t") || ParableFunctions._isExpansionStart(value, i, "${\n") || ParableFunctions._isExpansionStart(value, i, "${|") && !ParableFunctions._isBackslashEscaped(value, i)) {
                                prefix = ParableFunctions._substring(value, i, i + 3).replace("\t", " ").replace("\n", " ");
                                j = i + 3;
                                depth = 1;
                                while (j < value.length() && depth > 0) {
                                    if (String.valueOf(value.charAt(j)).equals("{")) {
                                        depth += 1;
                                    } else {
                                        if (String.valueOf(value.charAt(j)).equals("}")) {
                                            depth -= 1;
                                        }
                                    }
                                    j += 1;
                                }
                                inner = ParableFunctions._substring(value, i + 2, j - 1);
                                if (inner.trim().equals("")) {
                                    result.add("${ }");
                                } else {
                                    try {
                                        parser = ParableFunctions.newParser(inner.replaceFirst("^[" + " \t\n|" + "]+", ""), false, false);
                                        parsed = parser.parseList(true);
                                        if (parsed != null) {
                                            formatted = ParableFunctions._formatCmdsubNode(parsed, 0, false, false, false);
                                            formatted = formatted.replaceFirst("[" + ";" + "]+$", "");
                                            String terminator = "";
                                            if (inner.replaceFirst("[" + " \t" + "]+$", "").endsWith("\n")) {
                                                terminator = "\n }";
                                            } else {
                                                if (formatted.endsWith(" &")) {
                                                    terminator = " }";
                                                } else {
                                                    terminator = "; }";
                                                }
                                            }
                                            result.add(prefix + formatted + terminator);
                                        } else {
                                            result.add("${ }");
                                        }
                                    } catch (Exception e) {
                                        result.add(ParableFunctions._substring(value, i, j));
                                    }
                                }
                                i = j;
                            } else {
                                if (ParableFunctions._isExpansionStart(value, i, "${") && !ParableFunctions._isBackslashEscaped(value, i)) {
                                    j = i + 2;
                                    depth = 1;
                                    QuoteState braceQuote = ParableFunctions.newQuoteState();
                                    while (j < value.length() && depth > 0) {
                                        String c = String.valueOf(value.charAt(j));
                                        if (c.equals("\\") && j + 1 < value.length() && !braceQuote.single) {
                                            j += 2;
                                            continue;
                                        }
                                        if (c.equals("'") && !braceQuote.double_) {
                                            braceQuote.single = !braceQuote.single;
                                        } else {
                                            if (c.equals("\"") && !braceQuote.single) {
                                                braceQuote.double_ = !braceQuote.double_;
                                            } else {
                                                if (!braceQuote.inQuotes()) {
                                                    if (ParableFunctions._isExpansionStart(value, j, "$(") && !ParableFunctions._startsWithAt(value, j, "$((")) {
                                                        j = ParableFunctions._findCmdsubEnd(value, j + 2);
                                                        continue;
                                                    }
                                                    if (c.equals("{")) {
                                                        depth += 1;
                                                    } else {
                                                        if (c.equals("}")) {
                                                            depth -= 1;
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                        j += 1;
                                    }
                                    if (depth > 0) {
                                        inner = ParableFunctions._substring(value, i + 2, j);
                                    } else {
                                        inner = ParableFunctions._substring(value, i + 2, j - 1);
                                    }
                                    String formattedInner = this._formatCommandSubstitutions(inner, false);
                                    formattedInner = this._normalizeExtglobWhitespace(formattedInner);
                                    if (depth == 0) {
                                        result.add("${" + formattedInner + "}");
                                    } else {
                                        result.add("${" + formattedInner);
                                    }
                                    i = j;
                                } else {
                                    if (String.valueOf(value.charAt(i)).equals("\"")) {
                                        mainQuote.double_ = !mainQuote.double_;
                                        result.add(String.valueOf(value.charAt(i)));
                                        i += 1;
                                    } else {
                                        if (String.valueOf(value.charAt(i)).equals("'") && !mainQuote.double_) {
                                            j = i + 1;
                                            while (j < value.length() && !String.valueOf(value.charAt(j)).equals("'")) {
                                                j += 1;
                                            }
                                            if (j < value.length()) {
                                                j += 1;
                                            }
                                            result.add(ParableFunctions._substring(value, i, j));
                                            i = j;
                                        } else {
                                            result.add(String.valueOf(value.charAt(i)));
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
        return String.join("", result);
    }

    public String _normalizeExtglobWhitespace(String value) {
        List<String> result = new ArrayList<>();
        int i = 0;
        QuoteState extglobQuote = ParableFunctions.newQuoteState();
        int deprecatedArithDepth = 0;
        while (i < value.length()) {
            if (String.valueOf(value.charAt(i)).equals("\"")) {
                extglobQuote.double_ = !extglobQuote.double_;
                result.add(String.valueOf(value.charAt(i)));
                i += 1;
                continue;
            }
            if (ParableFunctions._startsWithAt(value, i, "$[") && !ParableFunctions._isBackslashEscaped(value, i)) {
                deprecatedArithDepth += 1;
                result.add(String.valueOf(value.charAt(i)));
                i += 1;
                continue;
            }
            if (String.valueOf(value.charAt(i)).equals("]") && deprecatedArithDepth > 0) {
                deprecatedArithDepth -= 1;
                result.add(String.valueOf(value.charAt(i)));
                i += 1;
                continue;
            }
            if (i + 1 < value.length() && String.valueOf(value.charAt(i + 1)).equals("(")) {
                String prefixChar = String.valueOf(value.charAt(i));
                if ("><".indexOf(prefixChar) != -1 && !extglobQuote.double_ && deprecatedArithDepth == 0) {
                    result.add(prefixChar);
                    result.add("(");
                    i += 2;
                    int depth = 1;
                    List<String> patternParts = new ArrayList<>();
                    List<String> currentPart = new ArrayList<>();
                    boolean hasPipe = false;
                    while (i < value.length() && depth > 0) {
                        if (String.valueOf(value.charAt(i)).equals("\\") && i + 1 < value.length()) {
                            currentPart.add(value.substring(i, i + 2));
                            i += 2;
                            continue;
                        } else {
                            if (String.valueOf(value.charAt(i)).equals("(")) {
                                depth += 1;
                                currentPart.add(String.valueOf(value.charAt(i)));
                                i += 1;
                            } else {
                                String partContent = "";
                                if (String.valueOf(value.charAt(i)).equals(")")) {
                                    depth -= 1;
                                    if (depth == 0) {
                                        partContent = String.join("", currentPart);
                                        if (partContent.indexOf("<<") != -1) {
                                            patternParts.add(partContent);
                                        } else {
                                            if (hasPipe) {
                                                patternParts.add(partContent.trim());
                                            } else {
                                                patternParts.add(partContent);
                                            }
                                        }
                                        break;
                                    }
                                    currentPart.add(String.valueOf(value.charAt(i)));
                                    i += 1;
                                } else {
                                    if (String.valueOf(value.charAt(i)).equals("|") && depth == 1) {
                                        if (i + 1 < value.length() && String.valueOf(value.charAt(i + 1)).equals("|")) {
                                            currentPart.add("||");
                                            i += 2;
                                        } else {
                                            hasPipe = true;
                                            partContent = String.join("", currentPart);
                                            if (partContent.indexOf("<<") != -1) {
                                                patternParts.add(partContent);
                                            } else {
                                                patternParts.add(partContent.trim());
                                            }
                                            currentPart = new ArrayList<>();
                                            i += 1;
                                        }
                                    } else {
                                        currentPart.add(String.valueOf(value.charAt(i)));
                                        i += 1;
                                    }
                                }
                            }
                        }
                    }
                    result.add(String.join(" | ", patternParts));
                    if (depth == 0) {
                        result.add(")");
                        i += 1;
                    }
                    continue;
                }
            }
            result.add(String.valueOf(value.charAt(i)));
            i += 1;
        }
        return String.join("", result);
    }

    public String getCondFormattedValue() {
        String value = this._expandAllAnsiCQuotes(this.value);
        value = this._stripLocaleStringDollars(value);
        value = this._formatCommandSubstitutions(value, false);
        value = this._normalizeExtglobWhitespace(value);
        value = value.replace("", "");
        return value.replaceFirst("[" + "\n" + "]+$", "");
    }
}

class Command implements Node {
    List<Word> words;
    List<Node> redirects;
    String kind;

    Command(List<Word> words, List<Node> redirects, String kind) {
        this.words = words;
        this.redirects = redirects;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        List<String> parts = new ArrayList<>();
        for (Word w : this.words) {
            parts.add(((Node) w).toSexp());
        }
        for (Node r : this.redirects) {
            parts.add(((Node) r).toSexp());
        }
        String inner = String.join(" ", parts);
        if (!(!inner.equals(""))) {
            return "(command)";
        }
        return "(command " + inner + ")";
    }
}

class Pipeline implements Node {
    List<Node> commands;
    String kind;

    Pipeline(List<Node> commands, String kind) {
        this.commands = commands;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        if (this.commands.size() == 1) {
            return ((Node) this.commands.get(0)).toSexp();
        }
        List<Tuple5> cmds = new ArrayList<>();
        int i = 0;
        Node cmd = null;
        while (i < this.commands.size()) {
            cmd = this.commands.get(i);
            if (cmd instanceof PipeBoth cmdPipeBoth) {
                i += 1;
                continue;
            }
            boolean needsRedirect = i + 1 < this.commands.size() && this.commands.get(i + 1).getKind() == "pipe-both";
            cmds.add(new Tuple5(cmd, needsRedirect));
            i += 1;
        }
        Tuple5 pair = null;
        boolean needs = false;
        if (cmds.size() == 1) {
            pair = cmds.get(0);
            cmd = pair.f0();
            needs = pair.f1();
            return this._cmdSexp(cmd, needs);
        }
        Tuple5 lastPair = cmds.get(cmds.size() - 1);
        Node lastCmd = lastPair.f0();
        boolean lastNeeds = lastPair.f1();
        String result = this._cmdSexp(lastCmd, lastNeeds);
        int j = cmds.size() - 2;
        while (j >= 0) {
            pair = cmds.get(j);
            cmd = pair.f0();
            needs = pair.f1();
            if (needs && cmd.getKind() != "command") {
                result = "(pipe " + ((Node) cmd).toSexp() + " (redirect \">&\" 1) " + result + ")";
            } else {
                result = "(pipe " + this._cmdSexp(cmd, needs) + " " + result + ")";
            }
            j -= 1;
        }
        return result;
    }

    public String _cmdSexp(Node cmd, boolean needsRedirect) {
        if (!needsRedirect) {
            return ((Node) cmd).toSexp();
        }
        if (cmd instanceof Command cmdCommand) {
            List<String> parts = new ArrayList<>();
            for (Word w : cmdCommand.words) {
                parts.add(((Node) w).toSexp());
            }
            for (Node r : cmdCommand.redirects) {
                parts.add(((Node) r).toSexp());
            }
            parts.add("(redirect \">&\" 1)");
            return "(command " + String.join(" ", parts) + ")";
        }
        return ((Node) cmd).toSexp();
    }
}

class ListNode implements Node {
    List<Node> parts;
    String kind;

    ListNode(List<Node> parts, String kind) {
        this.parts = parts;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        List<Node> parts = new ArrayList<>(this.parts);
        Map<String, String> opNames = new HashMap<>(Map.of("&&", "and", "||", "or", ";", "semi", "\n", "semi", "&", "background"));
        while (parts.size() > 1 && parts.get(parts.size() - 1).getKind() == "operator" && ((Operator) parts.get(parts.size() - 1)).op.equals(";") || ((Operator) parts.get(parts.size() - 1)).op.equals("\n")) {
            parts = ParableFunctions._sublist(parts, 0, parts.size() - 1);
        }
        if (parts.size() == 1) {
            return ((Node) parts.get(0)).toSexp();
        }
        if (parts.get(parts.size() - 1).getKind() == "operator" && ((Operator) parts.get(parts.size() - 1)).op.equals("&")) {
            for (Integer i : java.util.stream.IntStream.iterate(parts.size() - 3, _x -> _x < 0, _x -> _x + -2).boxed().toList()) {
                if (parts.get(i).getKind() == "operator" && ((Operator) parts.get(i)).op.equals(";") || ((Operator) parts.get(i)).op.equals("\n")) {
                    List<Node> left = ParableFunctions._sublist(parts, 0, i);
                    List<Node> right = ParableFunctions._sublist(parts, i + 1, parts.size() - 1);
                    String leftSexp = "";
                    if (left.size() > 1) {
                        leftSexp = ((Node) new ListNode(left, "list")).toSexp();
                    } else {
                        leftSexp = ((Node) left.get(0)).toSexp();
                    }
                    String rightSexp = "";
                    if (right.size() > 1) {
                        rightSexp = ((Node) new ListNode(right, "list")).toSexp();
                    } else {
                        rightSexp = ((Node) right.get(0)).toSexp();
                    }
                    return "(semi " + leftSexp + " (background " + rightSexp + "))";
                }
            }
            List<Node> innerParts = ParableFunctions._sublist(parts, 0, parts.size() - 1);
            if (innerParts.size() == 1) {
                return "(background " + ((Node) innerParts.get(0)).toSexp() + ")";
            }
            ListNode innerList = new ListNode(innerParts, "list");
            return "(background " + ((Node) innerList).toSexp() + ")";
        }
        return this._toSexpWithPrecedence(parts, opNames);
    }

    public String _toSexpWithPrecedence(List<Node> parts, Map<String, String> opNames) {
        List<Integer> semiPositions = new ArrayList<>();
        for (Integer i : java.util.stream.IntStream.range(0, parts.size()).boxed().toList()) {
            if (parts.get(i).getKind() == "operator" && ((Operator) parts.get(i)).op.equals(";") || ((Operator) parts.get(i)).op.equals("\n")) {
                semiPositions.add(i);
            }
        }
        if (!semiPositions.isEmpty()) {
            List<List<Node>> segments = new ArrayList<>();
            int start = 0;
            List<Node> seg = new ArrayList<>();
            for (int pos : semiPositions) {
                seg = ParableFunctions._sublist(parts, start, pos);
                if (!seg.isEmpty() && seg.get(0).getKind() != "operator") {
                    segments.add(seg);
                }
                start = pos + 1;
            }
            seg = ParableFunctions._sublist(parts, start, parts.size());
            if (!seg.isEmpty() && seg.get(0).getKind() != "operator") {
                segments.add(seg);
            }
            if (!(!segments.isEmpty())) {
                return "()";
            }
            String result = this._toSexpAmpAndHigher(segments.get(0), opNames);
            for (Integer i : java.util.stream.IntStream.range(1, segments.size()).boxed().toList()) {
                result = "(semi " + result + " " + this._toSexpAmpAndHigher(segments.get(i), opNames) + ")";
            }
            return result;
        }
        return this._toSexpAmpAndHigher(parts, opNames);
    }

    public String _toSexpAmpAndHigher(List<Node> parts, Map<String, String> opNames) {
        if (parts.size() == 1) {
            return ((Node) parts.get(0)).toSexp();
        }
        List<Integer> ampPositions = new ArrayList<>();
        for (Integer i : java.util.stream.IntStream.iterate(1, _x -> _x < parts.size() - 1, _x -> _x + 2).boxed().toList()) {
            if (parts.get(i).getKind() == "operator" && ((Operator) parts.get(i)).op.equals("&")) {
                ampPositions.add(i);
            }
        }
        if (!ampPositions.isEmpty()) {
            List<List<Node>> segments = new ArrayList<>();
            int start = 0;
            for (int pos : ampPositions) {
                segments.add(ParableFunctions._sublist(parts, start, pos));
                start = pos + 1;
            }
            segments.add(ParableFunctions._sublist(parts, start, parts.size()));
            String result = this._toSexpAndOr(segments.get(0), opNames);
            for (Integer i : java.util.stream.IntStream.range(1, segments.size()).boxed().toList()) {
                result = "(background " + result + " " + this._toSexpAndOr(segments.get(i), opNames) + ")";
            }
            return result;
        }
        return this._toSexpAndOr(parts, opNames);
    }

    public String _toSexpAndOr(List<Node> parts, Map<String, String> opNames) {
        if (parts.size() == 1) {
            return ((Node) parts.get(0)).toSexp();
        }
        String result = ((Node) parts.get(0)).toSexp();
        for (Integer i : java.util.stream.IntStream.iterate(1, _x -> _x < parts.size() - 1, _x -> _x + 2).boxed().toList()) {
            Node op = parts.get(i);
            Node cmd = parts.get(i + 1);
            Object opName = opNames.getOrDefault(((Operator) op).op, ((Operator) op).op);
            result = "(" + opName + " " + result + " " + ((Node) cmd).toSexp() + ")";
        }
        return result;
    }
}

class Operator implements Node {
    String op;
    String kind;

    Operator(String op, String kind) {
        this.op = op;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        Map<String, String> names = new HashMap<>(Map.of("&&", "and", "||", "or", ";", "semi", "&", "bg", "|", "pipe"));
        return "(" + names.getOrDefault(this.op, this.op) + ")";
    }
}

class PipeBoth implements Node {
    String kind;

    PipeBoth(String kind) {
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        return "(pipe-both)";
    }
}

class Empty implements Node {
    String kind;

    Empty(String kind) {
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        return "";
    }
}

class Comment implements Node {
    String text;
    String kind;

    Comment(String text, String kind) {
        this.text = text;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        return "";
    }
}

class Redirect implements Node {
    String op;
    Word target;
    Integer fd;
    String kind;

    Redirect(String op, Word target, Integer fd, String kind) {
        this.op = op;
        this.target = target;
        this.fd = fd;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        String op = this.op.replaceFirst("^[" + "0123456789" + "]+", "");
        if (op.startsWith("{")) {
            int j = 1;
            if (j < op.length() && String.valueOf(op.charAt(j)).chars().allMatch(Character::isLetter) || String.valueOf(op.charAt(j)).equals("_")) {
                j += 1;
                while (j < op.length() && String.valueOf(op.charAt(j)).chars().allMatch(Character::isLetterOrDigit) || String.valueOf(op.charAt(j)).equals("_")) {
                    j += 1;
                }
                if (j < op.length() && String.valueOf(op.charAt(j)).equals("[")) {
                    j += 1;
                    while (j < op.length() && !String.valueOf(op.charAt(j)).equals("]")) {
                        j += 1;
                    }
                    if (j < op.length() && String.valueOf(op.charAt(j)).equals("]")) {
                        j += 1;
                    }
                }
                if (j < op.length() && String.valueOf(op.charAt(j)).equals("}")) {
                    op = ParableFunctions._substring(op, j + 1, op.length());
                }
            }
        }
        String targetVal = this.target.value;
        targetVal = this.target._expandAllAnsiCQuotes(targetVal);
        targetVal = this.target._stripLocaleStringDollars(targetVal);
        targetVal = this.target._formatCommandSubstitutions(targetVal, false);
        targetVal = this.target._stripArithLineContinuations(targetVal);
        if (targetVal.endsWith("\\") && !targetVal.endsWith("\\\\")) {
            targetVal = targetVal + "\\";
        }
        if (targetVal.startsWith("&")) {
            if (op.equals(">")) {
                op = ">&";
            } else {
                if (op.equals("<")) {
                    op = "<&";
                }
            }
            String raw = ParableFunctions._substring(targetVal, 1, targetVal.length());
            if (raw.chars().allMatch(Character::isDigit) && Integer.parseInt(raw, 10) <= 2147483647) {
                return "(redirect \"" + op + "\" " + String.valueOf(Integer.parseInt(raw, 10)) + ")";
            }
            if (raw.endsWith("-") && raw.substring(0, raw.length() - 1).chars().allMatch(Character::isDigit) && Integer.parseInt(raw.substring(0, raw.length() - 1), 10) <= 2147483647) {
                return "(redirect \"" + op + "\" " + String.valueOf(Integer.parseInt(raw.substring(0, raw.length() - 1), 10)) + ")";
            }
            if (targetVal.equals("&-")) {
                return "(redirect \">&-\" 0)";
            }
            String fdTarget = (raw.endsWith("-") ? raw.substring(0, raw.length() - 1) : raw);
            return "(redirect \"" + op + "\" \"" + fdTarget + "\")";
        }
        if (op.equals(">&") || op.equals("<&")) {
            if (targetVal.chars().allMatch(Character::isDigit) && Integer.parseInt(targetVal, 10) <= 2147483647) {
                return "(redirect \"" + op + "\" " + String.valueOf(Integer.parseInt(targetVal, 10)) + ")";
            }
            if (targetVal.equals("-")) {
                return "(redirect \">&-\" 0)";
            }
            if (targetVal.endsWith("-") && targetVal.substring(0, targetVal.length() - 1).chars().allMatch(Character::isDigit) && Integer.parseInt(targetVal.substring(0, targetVal.length() - 1), 10) <= 2147483647) {
                return "(redirect \"" + op + "\" " + String.valueOf(Integer.parseInt(targetVal.substring(0, targetVal.length() - 1), 10)) + ")";
            }
            String outVal = (targetVal.endsWith("-") ? targetVal.substring(0, targetVal.length() - 1) : targetVal);
            return "(redirect \"" + op + "\" \"" + outVal + "\")";
        }
        return "(redirect \"" + op + "\" \"" + targetVal + "\")";
    }
}

class HereDoc implements Node {
    String delimiter;
    String content;
    boolean stripTabs;
    boolean quoted;
    Integer fd;
    boolean complete;
    int _startPos;
    String kind;

    HereDoc(String delimiter, String content, boolean stripTabs, boolean quoted, Integer fd, boolean complete, int _startPos, String kind) {
        this.delimiter = delimiter;
        this.content = content;
        this.stripTabs = stripTabs;
        this.quoted = quoted;
        this.fd = fd;
        this.complete = complete;
        this._startPos = _startPos;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        String op = (this.stripTabs ? "<<-" : "<<");
        String content = this.content;
        if (content.endsWith("\\") && !content.endsWith("\\\\")) {
            content = content + "\\";
        }
        return String.format("(redirect \"%s\" \"%s\")", op, content);
    }
}

class Subshell implements Node {
    Node body;
    List<Node> redirects;
    String kind;

    Subshell(Node body, List<Node> redirects, String kind) {
        this.body = body;
        this.redirects = redirects;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        String base = "(subshell " + ((Node) this.body).toSexp() + ")";
        return ParableFunctions._appendRedirects(base, this.redirects);
    }
}

class BraceGroup implements Node {
    Node body;
    List<Node> redirects;
    String kind;

    BraceGroup(Node body, List<Node> redirects, String kind) {
        this.body = body;
        this.redirects = redirects;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        String base = "(brace-group " + ((Node) this.body).toSexp() + ")";
        return ParableFunctions._appendRedirects(base, this.redirects);
    }
}

class If implements Node {
    Node condition;
    Node thenBody;
    Node elseBody;
    List<Node> redirects;
    String kind;

    If(Node condition, Node thenBody, Node elseBody, List<Node> redirects, String kind) {
        this.condition = condition;
        this.thenBody = thenBody;
        this.elseBody = elseBody;
        this.redirects = redirects;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        String result = "(if " + ((Node) this.condition).toSexp() + " " + ((Node) this.thenBody).toSexp();
        if (this.elseBody != null) {
            result = result + " " + ((Node) this.elseBody).toSexp();
        }
        result = result + ")";
        for (Node r : this.redirects) {
            result = result + " " + ((Node) r).toSexp();
        }
        return result;
    }
}

class While implements Node {
    Node condition;
    Node body;
    List<Node> redirects;
    String kind;

    While(Node condition, Node body, List<Node> redirects, String kind) {
        this.condition = condition;
        this.body = body;
        this.redirects = redirects;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        String base = "(while " + ((Node) this.condition).toSexp() + " " + ((Node) this.body).toSexp() + ")";
        return ParableFunctions._appendRedirects(base, this.redirects);
    }
}

class Until implements Node {
    Node condition;
    Node body;
    List<Node> redirects;
    String kind;

    Until(Node condition, Node body, List<Node> redirects, String kind) {
        this.condition = condition;
        this.body = body;
        this.redirects = redirects;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        String base = "(until " + ((Node) this.condition).toSexp() + " " + ((Node) this.body).toSexp() + ")";
        return ParableFunctions._appendRedirects(base, this.redirects);
    }
}

class For implements Node {
    String var;
    List<Word> words;
    Node body;
    List<Node> redirects;
    String kind;

    For(String var, List<Word> words, Node body, List<Node> redirects, String kind) {
        this.var = var;
        this.words = words;
        this.body = body;
        this.redirects = redirects;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        String suffix = "";
        if (!this.redirects.isEmpty()) {
            List<String> redirectParts = new ArrayList<>();
            for (Node r : this.redirects) {
                redirectParts.add(((Node) r).toSexp());
            }
            suffix = " " + String.join(" ", redirectParts);
        }
        Word tempWord = new Word(this.var, new ArrayList<>(), "word");
        String varFormatted = tempWord._formatCommandSubstitutions(this.var, false);
        String varEscaped = varFormatted.replace("\\", "\\\\").replace("\"", "\\\"");
        if (this.words == null) {
            return "(for (word \"" + varEscaped + "\") (in (word \"\\\"$@\\\"\")) " + ((Node) this.body).toSexp() + ")" + suffix;
        } else {
            if (this.words.isEmpty()) {
                return "(for (word \"" + varEscaped + "\") (in) " + ((Node) this.body).toSexp() + ")" + suffix;
            } else {
                List<String> wordParts = new ArrayList<>();
                for (Word w : this.words) {
                    wordParts.add(((Node) w).toSexp());
                }
                String wordStrs = String.join(" ", wordParts);
                return "(for (word \"" + varEscaped + "\") (in " + wordStrs + ") " + ((Node) this.body).toSexp() + ")" + suffix;
            }
        }
    }
}

class ForArith implements Node {
    String init;
    String cond;
    String incr;
    Node body;
    List<Node> redirects;
    String kind;

    ForArith(String init, String cond, String incr, Node body, List<Node> redirects, String kind) {
        this.init = init;
        this.cond = cond;
        this.incr = incr;
        this.body = body;
        this.redirects = redirects;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        String suffix = "";
        if (!this.redirects.isEmpty()) {
            List<String> redirectParts = new ArrayList<>();
            for (Node r : this.redirects) {
                redirectParts.add(((Node) r).toSexp());
            }
            suffix = " " + String.join(" ", redirectParts);
        }
        String initVal = (!this.init.equals("") ? this.init : "1");
        String condVal = (!this.cond.equals("") ? this.cond : "1");
        String incrVal = (!this.incr.equals("") ? this.incr : "1");
        String initStr = ParableFunctions._formatArithVal(initVal);
        String condStr = ParableFunctions._formatArithVal(condVal);
        String incrStr = ParableFunctions._formatArithVal(incrVal);
        String bodyStr = ((Node) this.body).toSexp();
        return String.format("(arith-for (init (word \"%s\")) (test (word \"%s\")) (step (word \"%s\")) %s)%s", initStr, condStr, incrStr, bodyStr, suffix);
    }
}

class Select implements Node {
    String var;
    List<Word> words;
    Node body;
    List<Node> redirects;
    String kind;

    Select(String var, List<Word> words, Node body, List<Node> redirects, String kind) {
        this.var = var;
        this.words = words;
        this.body = body;
        this.redirects = redirects;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        String suffix = "";
        if (!this.redirects.isEmpty()) {
            List<String> redirectParts = new ArrayList<>();
            for (Node r : this.redirects) {
                redirectParts.add(((Node) r).toSexp());
            }
            suffix = " " + String.join(" ", redirectParts);
        }
        String varEscaped = this.var.replace("\\", "\\\\").replace("\"", "\\\"");
        String inClause = "";
        if (this.words != null) {
            List<String> wordParts = new ArrayList<>();
            for (Word w : this.words) {
                wordParts.add(((Node) w).toSexp());
            }
            String wordStrs = String.join(" ", wordParts);
            if (!this.words.isEmpty()) {
                inClause = "(in " + wordStrs + ")";
            } else {
                inClause = "(in)";
            }
        } else {
            inClause = "(in (word \"\\\"$@\\\"\"))";
        }
        return "(select (word \"" + varEscaped + "\") " + inClause + " " + ((Node) this.body).toSexp() + ")" + suffix;
    }
}

class Case implements Node {
    Node word;
    List<Node> patterns;
    List<Node> redirects;
    String kind;

    Case(Node word, List<Node> patterns, List<Node> redirects, String kind) {
        this.word = word;
        this.patterns = patterns;
        this.redirects = redirects;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        List<String> parts = new ArrayList<>();
        parts.add("(case " + ((Node) this.word).toSexp());
        for (Node p : this.patterns) {
            parts.add(((Node) p).toSexp());
        }
        String base = String.join(" ", parts) + ")";
        return ParableFunctions._appendRedirects(base, this.redirects);
    }
}

class CasePattern implements Node {
    String pattern;
    Node body;
    String terminator;
    String kind;

    CasePattern(String pattern, Node body, String terminator, String kind) {
        this.pattern = pattern;
        this.body = body;
        this.terminator = terminator;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        List<String> alternatives = new ArrayList<>();
        List<String> current = new ArrayList<>();
        int i = 0;
        int depth = 0;
        while (i < this.pattern.length()) {
            String ch = String.valueOf(this.pattern.charAt(i));
            if (ch.equals("\\") && i + 1 < this.pattern.length()) {
                current.add(ParableFunctions._substring(this.pattern, i, i + 2));
                i += 2;
            } else {
                if (ch.equals("@") || ch.equals("?") || ch.equals("*") || ch.equals("+") || ch.equals("!") && i + 1 < this.pattern.length() && String.valueOf(this.pattern.charAt(i + 1)).equals("(")) {
                    current.add(ch);
                    current.add("(");
                    depth += 1;
                    i += 2;
                } else {
                    if (ParableFunctions._isExpansionStart(this.pattern, i, "$(")) {
                        current.add(ch);
                        current.add("(");
                        depth += 1;
                        i += 2;
                    } else {
                        if (ch.equals("(") && depth > 0) {
                            current.add(ch);
                            depth += 1;
                            i += 1;
                        } else {
                            if (ch.equals(")") && depth > 0) {
                                current.add(ch);
                                depth -= 1;
                                i += 1;
                            } else {
                                int result0 = 0;
                                List<String> result1 = new ArrayList<>();
                                if (ch.equals("[")) {
                                    Tuple6 _tuple19 = ParableFunctions._consumeBracketClass(this.pattern, i, depth);
                                    result0 = _tuple19.f0();
                                    result1 = _tuple19.f1();
                                    boolean result2 = _tuple19.f2();
                                    i = result0;
                                    current.addAll(result1);
                                } else {
                                    if (ch.equals("'") && depth == 0) {
                                        Tuple7 _tuple20 = ParableFunctions._consumeSingleQuote(this.pattern, i);
                                        result0 = _tuple20.f0();
                                        result1 = _tuple20.f1();
                                        i = result0;
                                        current.addAll(result1);
                                    } else {
                                        if (ch.equals("\"") && depth == 0) {
                                            Tuple7 _tuple21 = ParableFunctions._consumeDoubleQuote(this.pattern, i);
                                            result0 = _tuple21.f0();
                                            result1 = _tuple21.f1();
                                            i = result0;
                                            current.addAll(result1);
                                        } else {
                                            if (ch.equals("|") && depth == 0) {
                                                alternatives.add(String.join("", current));
                                                current = new ArrayList<>();
                                                i += 1;
                                            } else {
                                                current.add(ch);
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
        alternatives.add(String.join("", current));
        List<String> wordList = new ArrayList<>();
        for (String alt : alternatives) {
            wordList.add(((Node) new Word(alt, new ArrayList<>(), "word")).toSexp());
        }
        String patternStr = String.join(" ", wordList);
        List<String> parts = new ArrayList<>(List.of("(pattern (" + patternStr + ")"));
        if (this.body != null) {
            parts.add(" " + ((Node) this.body).toSexp());
        } else {
            parts.add(" ()");
        }
        parts.add(")");
        return String.join("", parts);
    }
}

class Function implements Node {
    String name;
    Node body;
    String kind;

    Function(String name, Node body, String kind) {
        this.name = name;
        this.body = body;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        return "(function \"" + this.name + "\" " + ((Node) this.body).toSexp() + ")";
    }
}

class ParamExpansion implements Node {
    String param;
    String op;
    String arg;
    String kind;

    ParamExpansion(String param, String op, String arg, String kind) {
        this.param = param;
        this.op = op;
        this.arg = arg;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        String escapedParam = this.param.replace("\\", "\\\\").replace("\"", "\\\"");
        if (!this.op.equals("")) {
            String escapedOp = this.op.replace("\\", "\\\\").replace("\"", "\\\"");
            String argVal = "";
            if (!this.arg.equals("")) {
                argVal = this.arg;
            } else {
                argVal = "";
            }
            String escapedArg = argVal.replace("\\", "\\\\").replace("\"", "\\\"");
            return "(param \"" + escapedParam + "\" \"" + escapedOp + "\" \"" + escapedArg + "\")";
        }
        return "(param \"" + escapedParam + "\")";
    }
}

class ParamLength implements Node {
    String param;
    String kind;

    ParamLength(String param, String kind) {
        this.param = param;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        String escaped = this.param.replace("\\", "\\\\").replace("\"", "\\\"");
        return "(param-len \"" + escaped + "\")";
    }
}

class ParamIndirect implements Node {
    String param;
    String op;
    String arg;
    String kind;

    ParamIndirect(String param, String op, String arg, String kind) {
        this.param = param;
        this.op = op;
        this.arg = arg;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        String escaped = this.param.replace("\\", "\\\\").replace("\"", "\\\"");
        if (!this.op.equals("")) {
            String escapedOp = this.op.replace("\\", "\\\\").replace("\"", "\\\"");
            String argVal = "";
            if (!this.arg.equals("")) {
                argVal = this.arg;
            } else {
                argVal = "";
            }
            String escapedArg = argVal.replace("\\", "\\\\").replace("\"", "\\\"");
            return "(param-indirect \"" + escaped + "\" \"" + escapedOp + "\" \"" + escapedArg + "\")";
        }
        return "(param-indirect \"" + escaped + "\")";
    }
}

class CommandSubstitution implements Node {
    Node command;
    boolean brace;
    String kind;

    CommandSubstitution(Node command, boolean brace, String kind) {
        this.command = command;
        this.brace = brace;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        if (this.brace) {
            return "(funsub " + ((Node) this.command).toSexp() + ")";
        }
        return "(cmdsub " + ((Node) this.command).toSexp() + ")";
    }
}

class ArithmeticExpansion implements Node {
    Node expression;
    String kind;

    ArithmeticExpansion(Node expression, String kind) {
        this.expression = expression;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        if (this.expression == null) {
            return "(arith)";
        }
        return "(arith " + ((Node) this.expression).toSexp() + ")";
    }
}

class ArithmeticCommand implements Node {
    Node expression;
    List<Node> redirects;
    String rawContent;
    String kind;

    ArithmeticCommand(Node expression, List<Node> redirects, String rawContent, String kind) {
        this.expression = expression;
        this.redirects = redirects;
        this.rawContent = rawContent;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        String formatted = new Word(this.rawContent, new ArrayList<>(), "word")._formatCommandSubstitutions(this.rawContent, true);
        String escaped = formatted.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n").replace("\t", "\\t");
        String result = "(arith (word \"" + escaped + "\"))";
        if (!this.redirects.isEmpty()) {
            List<String> redirectParts = new ArrayList<>();
            for (Node r : this.redirects) {
                redirectParts.add(((Node) r).toSexp());
            }
            String redirectSexps = String.join(" ", redirectParts);
            return result + " " + redirectSexps;
        }
        return result;
    }
}

class ArithNumber implements Node {
    String value;
    String kind;

    ArithNumber(String value, String kind) {
        this.value = value;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        return "(number \"" + this.value + "\")";
    }
}

class ArithEmpty implements Node {
    String kind;

    ArithEmpty(String kind) {
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        return "(empty)";
    }
}

class ArithVar implements Node {
    String name;
    String kind;

    ArithVar(String name, String kind) {
        this.name = name;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        return "(var \"" + this.name + "\")";
    }
}

class ArithBinaryOp implements Node {
    String op;
    Node left;
    Node right;
    String kind;

    ArithBinaryOp(String op, Node left, Node right, String kind) {
        this.op = op;
        this.left = left;
        this.right = right;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        return "(binary-op \"" + this.op + "\" " + ((Node) this.left).toSexp() + " " + ((Node) this.right).toSexp() + ")";
    }
}

class ArithUnaryOp implements Node {
    String op;
    Node operand;
    String kind;

    ArithUnaryOp(String op, Node operand, String kind) {
        this.op = op;
        this.operand = operand;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        return "(unary-op \"" + this.op + "\" " + ((Node) this.operand).toSexp() + ")";
    }
}

class ArithPreIncr implements Node {
    Node operand;
    String kind;

    ArithPreIncr(Node operand, String kind) {
        this.operand = operand;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        return "(pre-incr " + ((Node) this.operand).toSexp() + ")";
    }
}

class ArithPostIncr implements Node {
    Node operand;
    String kind;

    ArithPostIncr(Node operand, String kind) {
        this.operand = operand;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        return "(post-incr " + ((Node) this.operand).toSexp() + ")";
    }
}

class ArithPreDecr implements Node {
    Node operand;
    String kind;

    ArithPreDecr(Node operand, String kind) {
        this.operand = operand;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        return "(pre-decr " + ((Node) this.operand).toSexp() + ")";
    }
}

class ArithPostDecr implements Node {
    Node operand;
    String kind;

    ArithPostDecr(Node operand, String kind) {
        this.operand = operand;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        return "(post-decr " + ((Node) this.operand).toSexp() + ")";
    }
}

class ArithAssign implements Node {
    String op;
    Node target;
    Node value;
    String kind;

    ArithAssign(String op, Node target, Node value, String kind) {
        this.op = op;
        this.target = target;
        this.value = value;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        return "(assign \"" + this.op + "\" " + ((Node) this.target).toSexp() + " " + ((Node) this.value).toSexp() + ")";
    }
}

class ArithTernary implements Node {
    Node condition;
    Node ifTrue;
    Node ifFalse;
    String kind;

    ArithTernary(Node condition, Node ifTrue, Node ifFalse, String kind) {
        this.condition = condition;
        this.ifTrue = ifTrue;
        this.ifFalse = ifFalse;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        return "(ternary " + ((Node) this.condition).toSexp() + " " + ((Node) this.ifTrue).toSexp() + " " + ((Node) this.ifFalse).toSexp() + ")";
    }
}

class ArithComma implements Node {
    Node left;
    Node right;
    String kind;

    ArithComma(Node left, Node right, String kind) {
        this.left = left;
        this.right = right;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        return "(comma " + ((Node) this.left).toSexp() + " " + ((Node) this.right).toSexp() + ")";
    }
}

class ArithSubscript implements Node {
    String array;
    Node index;
    String kind;

    ArithSubscript(String array, Node index, String kind) {
        this.array = array;
        this.index = index;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        return "(subscript \"" + this.array + "\" " + ((Node) this.index).toSexp() + ")";
    }
}

class ArithEscape implements Node {
    String char_;
    String kind;

    ArithEscape(String char_, String kind) {
        this.char_ = char_;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        return "(escape \"" + this.char_ + "\")";
    }
}

class ArithDeprecated implements Node {
    String expression;
    String kind;

    ArithDeprecated(String expression, String kind) {
        this.expression = expression;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        String escaped = this.expression.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n");
        return "(arith-deprecated \"" + escaped + "\")";
    }
}

class ArithConcat implements Node {
    List<Node> parts;
    String kind;

    ArithConcat(List<Node> parts, String kind) {
        this.parts = parts;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        List<String> sexps = new ArrayList<>();
        for (Node p : this.parts) {
            sexps.add(((Node) p).toSexp());
        }
        return "(arith-concat " + String.join(" ", sexps) + ")";
    }
}

class AnsiCQuote implements Node {
    String content;
    String kind;

    AnsiCQuote(String content, String kind) {
        this.content = content;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        String escaped = this.content.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n");
        return "(ansi-c \"" + escaped + "\")";
    }
}

class LocaleString implements Node {
    String content;
    String kind;

    LocaleString(String content, String kind) {
        this.content = content;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        String escaped = this.content.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n");
        return "(locale \"" + escaped + "\")";
    }
}

class ProcessSubstitution implements Node {
    String direction;
    Node command;
    String kind;

    ProcessSubstitution(String direction, Node command, String kind) {
        this.direction = direction;
        this.command = command;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        return "(procsub \"" + this.direction + "\" " + ((Node) this.command).toSexp() + ")";
    }
}

class Negation implements Node {
    Node pipeline;
    String kind;

    Negation(Node pipeline, String kind) {
        this.pipeline = pipeline;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        if (this.pipeline == null) {
            return "(negation (command))";
        }
        return "(negation " + ((Node) this.pipeline).toSexp() + ")";
    }
}

class Time implements Node {
    Node pipeline;
    boolean posix;
    String kind;

    Time(Node pipeline, boolean posix, String kind) {
        this.pipeline = pipeline;
        this.posix = posix;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        if (this.pipeline == null) {
            if (this.posix) {
                return "(time -p (command))";
            } else {
                return "(time (command))";
            }
        }
        if (this.posix) {
            return "(time -p " + ((Node) this.pipeline).toSexp() + ")";
        }
        return "(time " + ((Node) this.pipeline).toSexp() + ")";
    }
}

class ConditionalExpr implements Node {
    Object body;
    List<Node> redirects;
    String kind;

    ConditionalExpr(Object body, List<Node> redirects, String kind) {
        this.body = body;
        this.redirects = redirects;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        Object body = this.body;
        String result = "";
        if (body instanceof String bodyString) {
            String escaped = bodyString.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n");
            result = "(cond \"" + escaped + "\")";
        } else {
            result = "(cond " + ((Node) body).toSexp() + ")";
        }
        if (!this.redirects.isEmpty()) {
            List<String> redirectParts = new ArrayList<>();
            for (Node r : this.redirects) {
                redirectParts.add(((Node) r).toSexp());
            }
            String redirectSexps = String.join(" ", redirectParts);
            return result + " " + redirectSexps;
        }
        return result;
    }
}

class UnaryTest implements Node {
    String op;
    Node operand;
    String kind;

    UnaryTest(String op, Node operand, String kind) {
        this.op = op;
        this.operand = operand;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        String operandVal = ((Word) this.operand).getCondFormattedValue();
        return "(cond-unary \"" + this.op + "\" (cond-term \"" + operandVal + "\"))";
    }
}

class BinaryTest implements Node {
    String op;
    Node left;
    Node right;
    String kind;

    BinaryTest(String op, Node left, Node right, String kind) {
        this.op = op;
        this.left = left;
        this.right = right;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        String leftVal = ((Word) this.left).getCondFormattedValue();
        String rightVal = ((Word) this.right).getCondFormattedValue();
        return "(cond-binary \"" + this.op + "\" (cond-term \"" + leftVal + "\") (cond-term \"" + rightVal + "\"))";
    }
}

class CondAnd implements Node {
    Node left;
    Node right;
    String kind;

    CondAnd(Node left, Node right, String kind) {
        this.left = left;
        this.right = right;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        return "(cond-and " + ((Node) this.left).toSexp() + " " + ((Node) this.right).toSexp() + ")";
    }
}

class CondOr implements Node {
    Node left;
    Node right;
    String kind;

    CondOr(Node left, Node right, String kind) {
        this.left = left;
        this.right = right;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        return "(cond-or " + ((Node) this.left).toSexp() + " " + ((Node) this.right).toSexp() + ")";
    }
}

class CondNot implements Node {
    Node operand;
    String kind;

    CondNot(Node operand, String kind) {
        this.operand = operand;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        return ((Node) this.operand).toSexp();
    }
}

class CondParen implements Node {
    Node inner;
    String kind;

    CondParen(Node inner, String kind) {
        this.inner = inner;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        return "(cond-expr " + ((Node) this.inner).toSexp() + ")";
    }
}

class Array implements Node {
    List<Word> elements;
    String kind;

    Array(List<Word> elements, String kind) {
        this.elements = elements;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        if (!(!this.elements.isEmpty())) {
            return "(array)";
        }
        List<String> parts = new ArrayList<>();
        for (Word e : this.elements) {
            parts.add(((Node) e).toSexp());
        }
        String inner = String.join(" ", parts);
        return "(array " + inner + ")";
    }
}

class Coproc implements Node {
    Node command;
    String name;
    String kind;

    Coproc(Node command, String name, String kind) {
        this.command = command;
        this.name = name;
        this.kind = kind;
    }

    public String getKind() { return this.kind; }

    public String toSexp() {
        String name = "";
        if (!this.name.equals("")) {
            name = this.name;
        } else {
            name = "COPROC";
        }
        return "(coproc \"" + name + "\" " + ((Node) this.command).toSexp() + ")";
    }
}

class Parser {
    String source;
    int pos;
    int length;
    List<HereDoc> _pendingHeredocs;
    int _cmdsubHeredocEnd;
    boolean _sawNewlineInSingleQuote;
    boolean _inProcessSub;
    boolean _extglob;
    ContextStack _ctx;
    Lexer _lexer;
    List<Token> _tokenHistory;
    int _parserState;
    int _dolbraceState;
    String _eofToken;
    int _wordContext;
    boolean _atCommandStart;
    boolean _inArrayLiteral;
    boolean _inAssignBuiltin;
    String _arithSrc;
    int _arithPos;
    int _arithLen;

    Parser(String source, int pos, int length, List<HereDoc> _pendingHeredocs, int _cmdsubHeredocEnd, boolean _sawNewlineInSingleQuote, boolean _inProcessSub, boolean _extglob, ContextStack _ctx, Lexer _lexer, List<Token> _tokenHistory, int _parserState, int _dolbraceState, String _eofToken, int _wordContext, boolean _atCommandStart, boolean _inArrayLiteral, boolean _inAssignBuiltin, String _arithSrc, int _arithPos, int _arithLen) {
        this.source = source;
        this.pos = pos;
        this.length = length;
        this._pendingHeredocs = _pendingHeredocs;
        this._cmdsubHeredocEnd = _cmdsubHeredocEnd;
        this._sawNewlineInSingleQuote = _sawNewlineInSingleQuote;
        this._inProcessSub = _inProcessSub;
        this._extglob = _extglob;
        this._ctx = _ctx;
        this._lexer = _lexer;
        this._tokenHistory = _tokenHistory;
        this._parserState = _parserState;
        this._dolbraceState = _dolbraceState;
        this._eofToken = _eofToken;
        this._wordContext = _wordContext;
        this._atCommandStart = _atCommandStart;
        this._inArrayLiteral = _inArrayLiteral;
        this._inAssignBuiltin = _inAssignBuiltin;
        this._arithSrc = _arithSrc;
        this._arithPos = _arithPos;
        this._arithLen = _arithLen;
    }

    public void _setState(int flag) {
        this._parserState = (this._parserState | flag);
    }

    public void _clearState(int flag) {
        this._parserState = (this._parserState & ~flag);
    }

    public boolean _inState(int flag) {
        return (this._parserState & flag) != 0;
    }

    public SavedParserState _saveParserState() {
        return new SavedParserState(this._parserState, this._dolbraceState, null /* TODO: SliceConvert */, this._ctx.copyStack(), this._eofToken);
    }

    public void _restoreParserState(SavedParserState saved) {
        this._parserState = saved.parserState;
        this._dolbraceState = saved.dolbraceState;
        this._eofToken = saved.eofToken;
        this._ctx.restoreFrom(saved.ctxStack);
    }

    public void _recordToken(Token tok) {
        this._tokenHistory = new ArrayList<>(List.of(tok, this._tokenHistory.get(0), this._tokenHistory.get(1), this._tokenHistory.get(2)));
    }

    public void _updateDolbraceForOp(String op, boolean hasParam) {
        if (this._dolbraceState == Constants.DOLBRACESTATE_NONE) {
            return;
        }
        if (op.equals("") || op.isEmpty()) {
            return;
        }
        String firstChar = String.valueOf(op.charAt(0));
        if (this._dolbraceState == Constants.DOLBRACESTATE_PARAM && hasParam) {
            if ("%#^,".indexOf(firstChar) != -1) {
                this._dolbraceState = Constants.DOLBRACESTATE_QUOTE;
                return;
            }
            if (firstChar.equals("/")) {
                this._dolbraceState = Constants.DOLBRACESTATE_QUOTE2;
                return;
            }
        }
        if (this._dolbraceState == Constants.DOLBRACESTATE_PARAM) {
            if ("#%^,~:-=?+/".indexOf(firstChar) != -1) {
                this._dolbraceState = Constants.DOLBRACESTATE_OP;
            }
        }
    }

    public void _syncLexer() {
        if (this._lexer._tokenCache != null) {
            if (this._lexer._tokenCache.pos != this.pos || this._lexer._cachedWordContext != this._wordContext || this._lexer._cachedAtCommandStart != this._atCommandStart || this._lexer._cachedInArrayLiteral != this._inArrayLiteral || this._lexer._cachedInAssignBuiltin != this._inAssignBuiltin) {
                this._lexer._tokenCache = null;
            }
        }
        if (this._lexer.pos != this.pos) {
            this._lexer.pos = this.pos;
        }
        this._lexer._eofToken = this._eofToken;
        this._lexer._parserState = this._parserState;
        this._lexer._lastReadToken = this._tokenHistory.get(0);
        this._lexer._wordContext = this._wordContext;
        this._lexer._atCommandStart = this._atCommandStart;
        this._lexer._inArrayLiteral = this._inArrayLiteral;
        this._lexer._inAssignBuiltin = this._inAssignBuiltin;
    }

    public void _syncParser() {
        this.pos = this._lexer.pos;
    }

    public Token _lexPeekToken() {
        if (this._lexer._tokenCache != null && this._lexer._tokenCache.pos == this.pos && this._lexer._cachedWordContext == this._wordContext && this._lexer._cachedAtCommandStart == this._atCommandStart && this._lexer._cachedInArrayLiteral == this._inArrayLiteral && this._lexer._cachedInAssignBuiltin == this._inAssignBuiltin) {
            return this._lexer._tokenCache;
        }
        int savedPos = this.pos;
        this._syncLexer();
        Token result = this._lexer.peekToken();
        this._lexer._cachedWordContext = this._wordContext;
        this._lexer._cachedAtCommandStart = this._atCommandStart;
        this._lexer._cachedInArrayLiteral = this._inArrayLiteral;
        this._lexer._cachedInAssignBuiltin = this._inAssignBuiltin;
        this._lexer._postReadPos = this._lexer.pos;
        this.pos = savedPos;
        return result;
    }

    public Token _lexNextToken() {
        Token tok = null;
        if (this._lexer._tokenCache != null && this._lexer._tokenCache.pos == this.pos && this._lexer._cachedWordContext == this._wordContext && this._lexer._cachedAtCommandStart == this._atCommandStart && this._lexer._cachedInArrayLiteral == this._inArrayLiteral && this._lexer._cachedInAssignBuiltin == this._inAssignBuiltin) {
            tok = this._lexer.nextToken();
            this.pos = this._lexer._postReadPos;
            this._lexer.pos = this._lexer._postReadPos;
        } else {
            this._syncLexer();
            tok = this._lexer.nextToken();
            this._lexer._cachedWordContext = this._wordContext;
            this._lexer._cachedAtCommandStart = this._atCommandStart;
            this._lexer._cachedInArrayLiteral = this._inArrayLiteral;
            this._lexer._cachedInAssignBuiltin = this._inAssignBuiltin;
            this._syncParser();
        }
        this._recordToken(tok);
        return tok;
    }

    public void _lexSkipBlanks() {
        this._syncLexer();
        this._lexer.skipBlanks();
        this._syncParser();
    }

    public boolean _lexSkipComment() {
        this._syncLexer();
        boolean result = this._lexer._skipComment();
        this._syncParser();
        return result;
    }

    public boolean _lexIsCommandTerminator() {
        Token tok = this._lexPeekToken();
        int t = tok.type;
        return t == Constants.TOKENTYPE_EOF || t == Constants.TOKENTYPE_NEWLINE || t == Constants.TOKENTYPE_PIPE || t == Constants.TOKENTYPE_SEMI || t == Constants.TOKENTYPE_LPAREN || t == Constants.TOKENTYPE_RPAREN || t == Constants.TOKENTYPE_AMP;
    }

    public Tuple8 _lexPeekOperator() {
        Token tok = this._lexPeekToken();
        int t = tok.type;
        if (t >= Constants.TOKENTYPE_SEMI && t <= Constants.TOKENTYPE_GREATER || t >= Constants.TOKENTYPE_AND_AND && t <= Constants.TOKENTYPE_PIPE_AMP) {
            return new Tuple8(t, tok.value);
        }
        return new Tuple8(0, "");
    }

    public String _lexPeekReservedWord() {
        Token tok = this._lexPeekToken();
        if (tok.type != Constants.TOKENTYPE_WORD) {
            return "";
        }
        String word = tok.value;
        if (word.endsWith("\\\n")) {
            word = word.substring(0, word.length() - 2);
        }
        if (Constants.RESERVED_WORDS.contains(word) || word.equals("{") || word.equals("}") || word.equals("[[") || word.equals("]]") || word.equals("!") || word.equals("time")) {
            return word;
        }
        return "";
    }

    public boolean _lexIsAtReservedWord(String word) {
        String reserved = this._lexPeekReservedWord();
        return reserved.equals(word);
    }

    public boolean _lexConsumeWord(String expected) {
        Token tok = this._lexPeekToken();
        if (tok.type != Constants.TOKENTYPE_WORD) {
            return false;
        }
        String word = tok.value;
        if (word.endsWith("\\\n")) {
            word = word.substring(0, word.length() - 2);
        }
        if (word.equals(expected)) {
            this._lexNextToken();
            return true;
        }
        return false;
    }

    public String _lexPeekCaseTerminator() {
        Token tok = this._lexPeekToken();
        int t = tok.type;
        if (t == Constants.TOKENTYPE_SEMI_SEMI) {
            return ";;";
        }
        if (t == Constants.TOKENTYPE_SEMI_AMP) {
            return ";&";
        }
        if (t == Constants.TOKENTYPE_SEMI_SEMI_AMP) {
            return ";;&";
        }
        return "";
    }

    public boolean atEnd() {
        return this.pos >= this.length;
    }

    public String peek() {
        if (this.atEnd()) {
            return "";
        }
        return String.valueOf(this.source.charAt(this.pos));
    }

    public String advance() {
        if (this.atEnd()) {
            return "";
        }
        String ch = String.valueOf(this.source.charAt(this.pos));
        this.pos += 1;
        return ch;
    }

    public String peekAt(int offset) {
        int pos = this.pos + offset;
        if (pos < 0 || pos >= this.length) {
            return "";
        }
        return String.valueOf(this.source.charAt(pos));
    }

    public String lookahead(int n) {
        return ParableFunctions._substring(this.source, this.pos, this.pos + n);
    }

    public boolean _isBangFollowedByProcsub() {
        if (this.pos + 2 >= this.length) {
            return false;
        }
        String nextChar = String.valueOf(this.source.charAt(this.pos + 1));
        if (!nextChar.equals(">") && !nextChar.equals("<")) {
            return false;
        }
        return String.valueOf(this.source.charAt(this.pos + 2)).equals("(");
    }

    public void skipWhitespace() {
        while (!this.atEnd()) {
            this._lexSkipBlanks();
            if (this.atEnd()) {
                break;
            }
            String ch = this.peek();
            if (ch.equals("#")) {
                this._lexSkipComment();
            } else {
                if (ch.equals("\\") && this.peekAt(1).equals("\n")) {
                    this.advance();
                    this.advance();
                } else {
                    break;
                }
            }
        }
    }

    public void skipWhitespaceAndNewlines() {
        while (!this.atEnd()) {
            String ch = this.peek();
            if (ParableFunctions._isWhitespace(ch)) {
                this.advance();
                if (ch.equals("\n")) {
                    this._gatherHeredocBodies();
                    if (this._cmdsubHeredocEnd != -1 && this._cmdsubHeredocEnd > this.pos) {
                        this.pos = this._cmdsubHeredocEnd;
                        this._cmdsubHeredocEnd = -1;
                    }
                }
            } else {
                if (ch.equals("#")) {
                    while (!this.atEnd() && !this.peek().equals("\n")) {
                        this.advance();
                    }
                } else {
                    if (ch.equals("\\") && this.peekAt(1).equals("\n")) {
                        this.advance();
                        this.advance();
                    } else {
                        break;
                    }
                }
            }
        }
    }

    public boolean _atListTerminatingBracket() {
        if (this.atEnd()) {
            return false;
        }
        String ch = this.peek();
        if (!this._eofToken.equals("") && ch.equals(this._eofToken)) {
            return true;
        }
        if (ch.equals(")")) {
            return true;
        }
        if (ch.equals("}")) {
            int nextPos = this.pos + 1;
            if (nextPos >= this.length) {
                return true;
            }
            return ParableFunctions._isWordEndContext(String.valueOf(this.source.charAt(nextPos)));
        }
        return false;
    }

    public boolean _atEofToken() {
        if (this._eofToken.equals("")) {
            return false;
        }
        Token tok = this._lexPeekToken();
        if (this._eofToken.equals(")")) {
            return tok.type == Constants.TOKENTYPE_RPAREN;
        }
        if (this._eofToken.equals("}")) {
            return tok.type == Constants.TOKENTYPE_WORD && tok.value.equals("}");
        }
        return false;
    }

    public List<Node> _collectRedirects() {
        List<Node> redirects = new ArrayList<>();
        while (true) {
            this.skipWhitespace();
            Node redirect = this.parseRedirect();
            if (redirect == null) {
                break;
            }
            redirects.add(redirect);
        }
        return (!redirects.isEmpty() ? redirects : null);
    }

    public Node _parseLoopBody(String context) {
        if (this.peek().equals("{")) {
            BraceGroup brace = this.parseBraceGroup();
            if (brace == null) {
                throw new RuntimeException(String.format("Expected brace group body in %s", context));
            }
            return brace.body;
        }
        if (this._lexConsumeWord("do")) {
            Node body = this.parseListUntil(new HashSet<>(Set.of("done")));
            if (body == null) {
                throw new RuntimeException("Expected commands after 'do'");
            }
            this.skipWhitespaceAndNewlines();
            if (!this._lexConsumeWord("done")) {
                throw new RuntimeException(String.format("Expected 'done' to close %s", context));
            }
            return body;
        }
        throw new RuntimeException(String.format("Expected 'do' or '{' in %s", context));
    }

    public String peekWord() {
        int savedPos = this.pos;
        this.skipWhitespace();
        if (this.atEnd() || ParableFunctions._isMetachar(this.peek())) {
            this.pos = savedPos;
            return "";
        }
        List<String> chars = new ArrayList<>();
        while (!this.atEnd() && !ParableFunctions._isMetachar(this.peek())) {
            String ch = this.peek();
            if (ParableFunctions._isQuote(ch)) {
                break;
            }
            if (ch.equals("\\") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("\n")) {
                break;
            }
            if (ch.equals("\\") && this.pos + 1 < this.length) {
                chars.add(this.advance());
                chars.add(this.advance());
                continue;
            }
            chars.add(this.advance());
        }
        String word = "";
        if (!chars.isEmpty()) {
            word = String.join("", chars);
        } else {
            word = "";
        }
        this.pos = savedPos;
        return word;
    }

    public boolean consumeWord(String expected) {
        int savedPos = this.pos;
        this.skipWhitespace();
        String word = this.peekWord();
        String keywordWord = word;
        boolean hasLeadingBrace = false;
        if (!word.equals("") && this._inProcessSub && word.length() > 1 && String.valueOf(word.charAt(0)).equals("}")) {
            keywordWord = word.substring(1);
            hasLeadingBrace = true;
        }
        if (!keywordWord.equals(expected)) {
            this.pos = savedPos;
            return false;
        }
        this.skipWhitespace();
        if (hasLeadingBrace) {
            this.advance();
        }
        for (int _i = 0; _i < expected.length(); _i++) {
            this.advance();
        }
        while (this.peek().equals("\\") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("\n")) {
            this.advance();
            this.advance();
        }
        return true;
    }

    public boolean _isWordTerminator(int ctx, String ch, int bracketDepth, int parenDepth) {
        this._syncLexer();
        return this._lexer._isWordTerminator(ctx, ch, bracketDepth, parenDepth);
    }

    public void _scanDoubleQuote(List<String> chars, List<Node> parts, int start, boolean handleLineContinuation) {
        chars.add("\"");
        while (!this.atEnd() && !this.peek().equals("\"")) {
            String c = this.peek();
            if (c.equals("\\") && this.pos + 1 < this.length) {
                String nextC = String.valueOf(this.source.charAt(this.pos + 1));
                if (handleLineContinuation && nextC.equals("\n")) {
                    this.advance();
                    this.advance();
                } else {
                    chars.add(this.advance());
                    chars.add(this.advance());
                }
            } else {
                if (c.equals("$")) {
                    if (!this._parseDollarExpansion(chars, parts, true)) {
                        chars.add(this.advance());
                    }
                } else {
                    chars.add(this.advance());
                }
            }
        }
        if (this.atEnd()) {
            throw new RuntimeException("Unterminated double quote");
        }
        chars.add(this.advance());
    }

    public boolean _parseDollarExpansion(List<String> chars, List<Node> parts, boolean inDquote) {
        Node result0 = null;
        String result1 = "";
        if (this.pos + 2 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("(") && String.valueOf(this.source.charAt(this.pos + 2)).equals("(")) {
            Tuple3 _tuple22 = this._parseArithmeticExpansion();
            result0 = _tuple22.f0();
            result1 = _tuple22.f1();
            if (result0 != null) {
                parts.add(result0);
                chars.add(result1);
                return true;
            }
            Tuple3 _tuple23 = this._parseCommandSubstitution();
            result0 = _tuple23.f0();
            result1 = _tuple23.f1();
            if (result0 != null) {
                parts.add(result0);
                chars.add(result1);
                return true;
            }
            return false;
        }
        if (this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("[")) {
            Tuple3 _tuple24 = this._parseDeprecatedArithmetic();
            result0 = _tuple24.f0();
            result1 = _tuple24.f1();
            if (result0 != null) {
                parts.add(result0);
                chars.add(result1);
                return true;
            }
            return false;
        }
        if (this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("(")) {
            Tuple3 _tuple25 = this._parseCommandSubstitution();
            result0 = _tuple25.f0();
            result1 = _tuple25.f1();
            if (result0 != null) {
                parts.add(result0);
                chars.add(result1);
                return true;
            }
            return false;
        }
        Tuple3 _tuple26 = this._parseParamExpansion(inDquote);
        result0 = _tuple26.f0();
        result1 = _tuple26.f1();
        if (result0 != null) {
            parts.add(result0);
            chars.add(result1);
            return true;
        }
        return false;
    }

    public Word _parseWordInternal(int ctx, boolean atCommandStart, boolean inArrayLiteral) {
        this._wordContext = ctx;
        return this.parseWord(atCommandStart, inArrayLiteral, false);
    }

    public Word parseWord(boolean atCommandStart, boolean inArrayLiteral, boolean inAssignBuiltin) {
        this.skipWhitespace();
        if (this.atEnd()) {
            return null;
        }
        this._atCommandStart = atCommandStart;
        this._inArrayLiteral = inArrayLiteral;
        this._inAssignBuiltin = inAssignBuiltin;
        Token tok = this._lexPeekToken();
        if (tok.type != Constants.TOKENTYPE_WORD) {
            this._atCommandStart = false;
            this._inArrayLiteral = false;
            this._inAssignBuiltin = false;
            return null;
        }
        this._lexNextToken();
        this._atCommandStart = false;
        this._inArrayLiteral = false;
        this._inAssignBuiltin = false;
        return tok.word;
    }

    public Tuple3 _parseCommandSubstitution() {
        if (this.atEnd() || !this.peek().equals("$")) {
            return new Tuple3(null, "");
        }
        int start = this.pos;
        this.advance();
        if (this.atEnd() || !this.peek().equals("(")) {
            this.pos = start;
            return new Tuple3(null, "");
        }
        this.advance();
        SavedParserState saved = this._saveParserState();
        this._setState((Constants.PARSERSTATEFLAGS_PST_CMDSUBST | Constants.PARSERSTATEFLAGS_PST_EOFTOKEN));
        this._eofToken = ")";
        Node cmd = this.parseList(true);
        if (cmd == null) {
            cmd = new Empty("empty");
        }
        this.skipWhitespaceAndNewlines();
        if (this.atEnd() || !this.peek().equals(")")) {
            this._restoreParserState(saved);
            this.pos = start;
            return new Tuple3(null, "");
        }
        this.advance();
        int textEnd = this.pos;
        String text = ParableFunctions._substring(this.source, start, textEnd);
        this._restoreParserState(saved);
        return new Tuple3(new CommandSubstitution(cmd, false, "cmdsub"), text);
    }

    public Tuple3 _parseFunsub(int start) {
        this._syncParser();
        if (!this.atEnd() && this.peek().equals("|")) {
            this.advance();
        }
        SavedParserState saved = this._saveParserState();
        this._setState((Constants.PARSERSTATEFLAGS_PST_CMDSUBST | Constants.PARSERSTATEFLAGS_PST_EOFTOKEN));
        this._eofToken = "}";
        Node cmd = this.parseList(true);
        if (cmd == null) {
            cmd = new Empty("empty");
        }
        this.skipWhitespaceAndNewlines();
        if (this.atEnd() || !this.peek().equals("}")) {
            this._restoreParserState(saved);
            throw new RuntimeException("unexpected EOF looking for `}'");
        }
        this.advance();
        String text = ParableFunctions._substring(this.source, start, this.pos);
        this._restoreParserState(saved);
        this._syncLexer();
        return new Tuple3(new CommandSubstitution(cmd, true, "cmdsub"), text);
    }

    public boolean _isAssignmentWord(Node word) {
        return ParableFunctions._assignment(((Word) word).value, 0) != -1;
    }

    public Tuple3 _parseBacktickSubstitution() {
        if (this.atEnd() || !this.peek().equals("`")) {
            return new Tuple3(null, "");
        }
        int start = this.pos;
        this.advance();
        List<String> contentChars = new ArrayList<>();
        List<String> textChars = new ArrayList<>(List.of("`"));
        List<Tuple2> pendingHeredocs = new ArrayList<>();
        boolean inHeredocBody = false;
        String currentHeredocDelim = "";
        boolean currentHeredocStrip = false;
        while (!this.atEnd() && inHeredocBody || !this.peek().equals("`")) {
            if (inHeredocBody) {
                int lineStart = this.pos;
                int lineEnd = lineStart;
                while (lineEnd < this.length && !String.valueOf(this.source.charAt(lineEnd)).equals("\n")) {
                    lineEnd += 1;
                }
                String line = ParableFunctions._substring(this.source, lineStart, lineEnd);
                String checkLine = (currentHeredocStrip ? line.replaceFirst("^[" + "\t" + "]+", "") : line);
                if (checkLine.equals(currentHeredocDelim)) {
                    for (int _i = 0; _i < line.length(); _i++) {
                        String ch = String.valueOf(line.charAt(_i));
                        contentChars.add(ch);
                        textChars.add(ch);
                    }
                    this.pos = lineEnd;
                    if (this.pos < this.length && String.valueOf(this.source.charAt(this.pos)).equals("\n")) {
                        contentChars.add("\n");
                        textChars.add("\n");
                        this.advance();
                    }
                    inHeredocBody = false;
                    if (!pendingHeredocs.isEmpty()) {
                        {
                            Tuple2 _entry = pendingHeredocs.get(pendingHeredocs.size() - 1);
                            pendingHeredocs = new ArrayList<>(pendingHeredocs.subList(0, pendingHeredocs.size() - 1));
                            currentHeredocDelim = _entry.f0();
                            currentHeredocStrip = _entry.f1();
                        }
                        inHeredocBody = true;
                    }
                } else {
                    if (checkLine.startsWith(currentHeredocDelim) && checkLine.length() > currentHeredocDelim.length()) {
                        int tabsStripped = line.length() - checkLine.length();
                        int endPos = tabsStripped + currentHeredocDelim.length();
                        for (Integer i : java.util.stream.IntStream.range(0, endPos).boxed().toList()) {
                            contentChars.add(String.valueOf(line.charAt(i)));
                            textChars.add(String.valueOf(line.charAt(i)));
                        }
                        this.pos = lineStart + endPos;
                        inHeredocBody = false;
                        if (!pendingHeredocs.isEmpty()) {
                            {
                                Tuple2 _entry = pendingHeredocs.get(pendingHeredocs.size() - 1);
                                pendingHeredocs = new ArrayList<>(pendingHeredocs.subList(0, pendingHeredocs.size() - 1));
                                currentHeredocDelim = _entry.f0();
                                currentHeredocStrip = _entry.f1();
                            }
                            inHeredocBody = true;
                        }
                    } else {
                        for (int _i = 0; _i < line.length(); _i++) {
                            String ch = String.valueOf(line.charAt(_i));
                            contentChars.add(ch);
                            textChars.add(ch);
                        }
                        this.pos = lineEnd;
                        if (this.pos < this.length && String.valueOf(this.source.charAt(this.pos)).equals("\n")) {
                            contentChars.add("\n");
                            textChars.add("\n");
                            this.advance();
                        }
                    }
                }
                continue;
            }
            String c = this.peek();
            String ch = "";
            if (c.equals("\\") && this.pos + 1 < this.length) {
                String nextC = String.valueOf(this.source.charAt(this.pos + 1));
                if (nextC.equals("\n")) {
                    this.advance();
                    this.advance();
                } else {
                    if (ParableFunctions._isEscapeCharInBacktick(nextC)) {
                        this.advance();
                        String escaped = this.advance();
                        contentChars.add(escaped);
                        textChars.add("\\");
                        textChars.add(escaped);
                    } else {
                        ch = this.advance();
                        contentChars.add(ch);
                        textChars.add(ch);
                    }
                }
                continue;
            }
            if (c.equals("<") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("<")) {
                String quote = "";
                if (this.pos + 2 < this.length && String.valueOf(this.source.charAt(this.pos + 2)).equals("<")) {
                    contentChars.add(this.advance());
                    textChars.add("<");
                    contentChars.add(this.advance());
                    textChars.add("<");
                    contentChars.add(this.advance());
                    textChars.add("<");
                    while (!this.atEnd() && ParableFunctions._isWhitespaceNoNewline(this.peek())) {
                        ch = this.advance();
                        contentChars.add(ch);
                        textChars.add(ch);
                    }
                    while (!this.atEnd() && !ParableFunctions._isWhitespace(this.peek()) && "()".indexOf(this.peek()) == -1) {
                        if (this.peek().equals("\\") && this.pos + 1 < this.length) {
                            ch = this.advance();
                            contentChars.add(ch);
                            textChars.add(ch);
                            ch = this.advance();
                            contentChars.add(ch);
                            textChars.add(ch);
                        } else {
                            if ("\"'".indexOf(this.peek()) != -1) {
                                quote = this.peek();
                                ch = this.advance();
                                contentChars.add(ch);
                                textChars.add(ch);
                                while (!this.atEnd() && !this.peek().equals(quote)) {
                                    if (quote.equals("\"") && this.peek().equals("\\")) {
                                        ch = this.advance();
                                        contentChars.add(ch);
                                        textChars.add(ch);
                                    }
                                    ch = this.advance();
                                    contentChars.add(ch);
                                    textChars.add(ch);
                                }
                                if (!this.atEnd()) {
                                    ch = this.advance();
                                    contentChars.add(ch);
                                    textChars.add(ch);
                                }
                            } else {
                                ch = this.advance();
                                contentChars.add(ch);
                                textChars.add(ch);
                            }
                        }
                    }
                    continue;
                }
                contentChars.add(this.advance());
                textChars.add("<");
                contentChars.add(this.advance());
                textChars.add("<");
                boolean stripTabs = false;
                if (!this.atEnd() && this.peek().equals("-")) {
                    stripTabs = true;
                    contentChars.add(this.advance());
                    textChars.add("-");
                }
                while (!this.atEnd() && ParableFunctions._isWhitespaceNoNewline(this.peek())) {
                    ch = this.advance();
                    contentChars.add(ch);
                    textChars.add(ch);
                }
                List<String> delimiterChars = new ArrayList<>();
                if (!this.atEnd()) {
                    ch = this.peek();
                    String dch = "";
                    String closing = "";
                    if (ParableFunctions._isQuote(ch)) {
                        quote = this.advance();
                        contentChars.add(quote);
                        textChars.add(quote);
                        while (!this.atEnd() && !this.peek().equals(quote)) {
                            dch = this.advance();
                            contentChars.add(dch);
                            textChars.add(dch);
                            delimiterChars.add(dch);
                        }
                        if (!this.atEnd()) {
                            closing = this.advance();
                            contentChars.add(closing);
                            textChars.add(closing);
                        }
                    } else {
                        String esc = "";
                        if (ch.equals("\\")) {
                            esc = this.advance();
                            contentChars.add(esc);
                            textChars.add(esc);
                            if (!this.atEnd()) {
                                dch = this.advance();
                                contentChars.add(dch);
                                textChars.add(dch);
                                delimiterChars.add(dch);
                            }
                            while (!this.atEnd() && !ParableFunctions._isMetachar(this.peek())) {
                                dch = this.advance();
                                contentChars.add(dch);
                                textChars.add(dch);
                                delimiterChars.add(dch);
                            }
                        } else {
                            while (!this.atEnd() && !ParableFunctions._isMetachar(this.peek()) && !this.peek().equals("`")) {
                                ch = this.peek();
                                if (ParableFunctions._isQuote(ch)) {
                                    quote = this.advance();
                                    contentChars.add(quote);
                                    textChars.add(quote);
                                    while (!this.atEnd() && !this.peek().equals(quote)) {
                                        dch = this.advance();
                                        contentChars.add(dch);
                                        textChars.add(dch);
                                        delimiterChars.add(dch);
                                    }
                                    if (!this.atEnd()) {
                                        closing = this.advance();
                                        contentChars.add(closing);
                                        textChars.add(closing);
                                    }
                                } else {
                                    if (ch.equals("\\")) {
                                        esc = this.advance();
                                        contentChars.add(esc);
                                        textChars.add(esc);
                                        if (!this.atEnd()) {
                                            dch = this.advance();
                                            contentChars.add(dch);
                                            textChars.add(dch);
                                            delimiterChars.add(dch);
                                        }
                                    } else {
                                        dch = this.advance();
                                        contentChars.add(dch);
                                        textChars.add(dch);
                                        delimiterChars.add(dch);
                                    }
                                }
                            }
                        }
                    }
                }
                String delimiter = String.join("", delimiterChars);
                if (!delimiter.equals("")) {
                    pendingHeredocs.add(new Tuple2(delimiter, stripTabs));
                }
                continue;
            }
            if (c.equals("\n")) {
                ch = this.advance();
                contentChars.add(ch);
                textChars.add(ch);
                if (!pendingHeredocs.isEmpty()) {
                    {
                        Tuple2 _entry = pendingHeredocs.get(pendingHeredocs.size() - 1);
                        pendingHeredocs = new ArrayList<>(pendingHeredocs.subList(0, pendingHeredocs.size() - 1));
                        currentHeredocDelim = _entry.f0();
                        currentHeredocStrip = _entry.f1();
                    }
                    inHeredocBody = true;
                }
                continue;
            }
            ch = this.advance();
            contentChars.add(ch);
            textChars.add(ch);
        }
        if (this.atEnd()) {
            throw new RuntimeException("Unterminated backtick");
        }
        this.advance();
        textChars.add("`");
        String text = String.join("", textChars);
        String content = String.join("", contentChars);
        if (!pendingHeredocs.isEmpty()) {
            Tuple9 _tuple27 = ParableFunctions._findHeredocContentEnd(this.source, this.pos, pendingHeredocs);
            int heredocStart = _tuple27.f0();
            int heredocEnd = _tuple27.f1();
            if (heredocEnd > heredocStart) {
                content = content + ParableFunctions._substring(this.source, heredocStart, heredocEnd);
                if (this._cmdsubHeredocEnd == -1) {
                    this._cmdsubHeredocEnd = heredocEnd;
                } else {
                    this._cmdsubHeredocEnd = (this._cmdsubHeredocEnd > heredocEnd ? this._cmdsubHeredocEnd : heredocEnd);
                }
            }
        }
        Parser subParser = ParableFunctions.newParser(content, false, this._extglob);
        Node cmd = subParser.parseList(true);
        if (cmd == null) {
            cmd = new Empty("empty");
        }
        return new Tuple3(new CommandSubstitution(cmd, false, "cmdsub"), text);
    }

    public Tuple3 _parseProcessSubstitution() {
        if (this.atEnd() || !ParableFunctions._isRedirectChar(this.peek())) {
            return new Tuple3(null, "");
        }
        int start = this.pos;
        String direction = this.advance();
        if (this.atEnd() || !this.peek().equals("(")) {
            this.pos = start;
            return new Tuple3(null, "");
        }
        this.advance();
        SavedParserState saved = this._saveParserState();
        boolean oldInProcessSub = this._inProcessSub;
        this._inProcessSub = true;
        this._setState(Constants.PARSERSTATEFLAGS_PST_EOFTOKEN);
        this._eofToken = ")";
        try {
            Node cmd = this.parseList(true);
            if (cmd == null) {
                cmd = new Empty("empty");
            }
            this.skipWhitespaceAndNewlines();
            if (this.atEnd() || !this.peek().equals(")")) {
                throw new RuntimeException("Invalid process substitution");
            }
            this.advance();
            int textEnd = this.pos;
            String text = ParableFunctions._substring(this.source, start, textEnd);
            text = ParableFunctions._stripLineContinuationsCommentAware(text);
            this._restoreParserState(saved);
            this._inProcessSub = oldInProcessSub;
            return new Tuple3(new ProcessSubstitution(direction, cmd, "procsub"), text);
        } catch (Exception e) {
            this._restoreParserState(saved);
            this._inProcessSub = oldInProcessSub;
            String contentStartChar = (start + 2 < this.length ? String.valueOf(this.source.charAt(start + 2)) : "");
            if (" \t\n".indexOf(contentStartChar) != -1) {
                throw new RuntimeException("");
            }
            this.pos = start + 2;
            this._lexer.pos = this.pos;
            this._lexer._parseMatchedPair("(", ")", 0, false);
            this.pos = this._lexer.pos;
            String text = ParableFunctions._substring(this.source, start, this.pos);
            text = ParableFunctions._stripLineContinuationsCommentAware(text);
            return new Tuple3(null, text);
        }
    }

    public Tuple3 _parseArrayLiteral() {
        if (this.atEnd() || !this.peek().equals("(")) {
            return new Tuple3(null, "");
        }
        int start = this.pos;
        this.advance();
        this._setState(Constants.PARSERSTATEFLAGS_PST_COMPASSIGN);
        List<Word> elements = new ArrayList<>();
        while (true) {
            this.skipWhitespaceAndNewlines();
            if (this.atEnd()) {
                this._clearState(Constants.PARSERSTATEFLAGS_PST_COMPASSIGN);
                throw new RuntimeException("Unterminated array literal");
            }
            if (this.peek().equals(")")) {
                break;
            }
            Word word = this.parseWord(false, true, false);
            if (word == null) {
                if (this.peek().equals(")")) {
                    break;
                }
                this._clearState(Constants.PARSERSTATEFLAGS_PST_COMPASSIGN);
                throw new RuntimeException("Expected word in array literal");
            }
            elements.add(word);
        }
        if (this.atEnd() || !this.peek().equals(")")) {
            this._clearState(Constants.PARSERSTATEFLAGS_PST_COMPASSIGN);
            throw new RuntimeException("Expected ) to close array literal");
        }
        this.advance();
        String text = ParableFunctions._substring(this.source, start, this.pos);
        this._clearState(Constants.PARSERSTATEFLAGS_PST_COMPASSIGN);
        return new Tuple3(new Array(elements, "array"), text);
    }

    public Tuple3 _parseArithmeticExpansion() {
        if (this.atEnd() || !this.peek().equals("$")) {
            return new Tuple3(null, "");
        }
        int start = this.pos;
        if (this.pos + 2 >= this.length || !String.valueOf(this.source.charAt(this.pos + 1)).equals("(") || !String.valueOf(this.source.charAt(this.pos + 2)).equals("(")) {
            return new Tuple3(null, "");
        }
        this.advance();
        this.advance();
        this.advance();
        int contentStart = this.pos;
        int depth = 2;
        int firstClosePos = -1;
        while (!this.atEnd() && depth > 0) {
            String c = this.peek();
            if (c.equals("'")) {
                this.advance();
                while (!this.atEnd() && !this.peek().equals("'")) {
                    this.advance();
                }
                if (!this.atEnd()) {
                    this.advance();
                }
            } else {
                if (c.equals("\"")) {
                    this.advance();
                    while (!this.atEnd()) {
                        if (this.peek().equals("\\") && this.pos + 1 < this.length) {
                            this.advance();
                            this.advance();
                        } else {
                            if (this.peek().equals("\"")) {
                                this.advance();
                                break;
                            } else {
                                this.advance();
                            }
                        }
                    }
                } else {
                    if (c.equals("\\") && this.pos + 1 < this.length) {
                        this.advance();
                        this.advance();
                    } else {
                        if (c.equals("(")) {
                            depth += 1;
                            this.advance();
                        } else {
                            if (c.equals(")")) {
                                if (depth == 2) {
                                    firstClosePos = this.pos;
                                }
                                depth -= 1;
                                if (depth == 0) {
                                    break;
                                }
                                this.advance();
                            } else {
                                if (depth == 1) {
                                    firstClosePos = -1;
                                }
                                this.advance();
                            }
                        }
                    }
                }
            }
        }
        if (depth != 0) {
            if (this.atEnd()) {
                throw new RuntimeException("unexpected EOF looking for `))'");
            }
            this.pos = start;
            return new Tuple3(null, "");
        }
        String content = "";
        if (firstClosePos != -1) {
            content = ParableFunctions._substring(this.source, contentStart, firstClosePos);
        } else {
            content = ParableFunctions._substring(this.source, contentStart, this.pos);
        }
        this.advance();
        String text = ParableFunctions._substring(this.source, start, this.pos);
        Node expr = null;
        try {
            expr = this._parseArithExpr(content);
        } catch (Exception e) {
            this.pos = start;
            return new Tuple3(null, "");
        }
        return new Tuple3(new ArithmeticExpansion(expr, "arith"), text);
    }

    public Node _parseArithExpr(String content) {
        String savedArithSrc = this._arithSrc;
        int savedArithPos = this._arithPos;
        int savedArithLen = this._arithLen;
        int savedParserState = this._parserState;
        this._setState(Constants.PARSERSTATEFLAGS_PST_ARITH);
        this._arithSrc = content;
        this._arithPos = 0;
        this._arithLen = content.length();
        this._arithSkipWs();
        Node result = null;
        if (this._arithAtEnd()) {
            result = null;
        } else {
            result = this._arithParseComma();
        }
        this._parserState = savedParserState;
        if (!savedArithSrc.equals("")) {
            this._arithSrc = savedArithSrc;
            this._arithPos = savedArithPos;
            this._arithLen = savedArithLen;
        }
        return result;
    }

    public boolean _arithAtEnd() {
        return this._arithPos >= this._arithLen;
    }

    public String _arithPeek(int offset) {
        int pos = this._arithPos + offset;
        if (pos >= this._arithLen) {
            return "";
        }
        return String.valueOf(this._arithSrc.charAt(pos));
    }

    public String _arithAdvance() {
        if (this._arithAtEnd()) {
            return "";
        }
        String c = String.valueOf(this._arithSrc.charAt(this._arithPos));
        this._arithPos += 1;
        return c;
    }

    public void _arithSkipWs() {
        while (!this._arithAtEnd()) {
            String c = String.valueOf(this._arithSrc.charAt(this._arithPos));
            if (ParableFunctions._isWhitespace(c)) {
                this._arithPos += 1;
            } else {
                if (c.equals("\\") && this._arithPos + 1 < this._arithLen && String.valueOf(this._arithSrc.charAt(this._arithPos + 1)).equals("\n")) {
                    this._arithPos += 2;
                } else {
                    break;
                }
            }
        }
    }

    public boolean _arithMatch(String s) {
        return ParableFunctions._startsWithAt(this._arithSrc, this._arithPos, s);
    }

    public boolean _arithConsume(String s) {
        if (this._arithMatch(s)) {
            this._arithPos += s.length();
            return true;
        }
        return false;
    }

    public Node _arithParseComma() {
        Node left = this._arithParseAssign();
        while (true) {
            this._arithSkipWs();
            if (this._arithConsume(",")) {
                this._arithSkipWs();
                Node right = this._arithParseAssign();
                left = new ArithComma(left, right, "comma");
            } else {
                break;
            }
        }
        return left;
    }

    public Node _arithParseAssign() {
        Node left = this._arithParseTernary();
        this._arithSkipWs();
        List<String> assignOps = new ArrayList<>(List.of("<<=", ">>=", "+=", "-=", "*=", "/=", "%=", "&=", "^=", "|=", "="));
        for (String op : assignOps) {
            if (this._arithMatch(op)) {
                if (op == "=" && this._arithPeek(1).equals("=")) {
                    break;
                }
                this._arithConsume(op);
                this._arithSkipWs();
                Node right = this._arithParseAssign();
                return new ArithAssign(op, left, right, "assign");
            }
        }
        return left;
    }

    public Node _arithParseTernary() {
        Node cond = this._arithParseLogicalOr();
        this._arithSkipWs();
        if (this._arithConsume("?")) {
            this._arithSkipWs();
            Node ifTrue = null;
            if (this._arithMatch(":")) {
                ifTrue = null;
            } else {
                ifTrue = this._arithParseAssign();
            }
            this._arithSkipWs();
            Node ifFalse = null;
            if (this._arithConsume(":")) {
                this._arithSkipWs();
                if (this._arithAtEnd() || this._arithPeek(0).equals(")")) {
                    ifFalse = null;
                } else {
                    ifFalse = this._arithParseTernary();
                }
            } else {
                ifFalse = null;
            }
            return new ArithTernary(cond, ifTrue, ifFalse, "ternary");
        }
        return cond;
    }

    public Node _arithParseLeftAssoc(List<String> ops, NodeSupplier parsefn) {
        Node left = parsefn.call();
        while (true) {
            this._arithSkipWs();
            boolean matched = false;
            for (String op : ops) {
                if (this._arithMatch(op)) {
                    this._arithConsume(op);
                    this._arithSkipWs();
                    left = new ArithBinaryOp(op, left, parsefn.call(), "binary-op");
                    matched = true;
                    break;
                }
            }
            if (!matched) {
                break;
            }
        }
        return left;
    }

    public Node _arithParseLogicalOr() {
        return this._arithParseLeftAssoc(new ArrayList<>(List.of("||")), () -> this._arithParseLogicalAnd());
    }

    public Node _arithParseLogicalAnd() {
        return this._arithParseLeftAssoc(new ArrayList<>(List.of("&&")), () -> this._arithParseBitwiseOr());
    }

    public Node _arithParseBitwiseOr() {
        Node left = this._arithParseBitwiseXor();
        while (true) {
            this._arithSkipWs();
            if (this._arithPeek(0).equals("|") && !this._arithPeek(1).equals("|") && !this._arithPeek(1).equals("=")) {
                this._arithAdvance();
                this._arithSkipWs();
                Node right = this._arithParseBitwiseXor();
                left = new ArithBinaryOp("|", left, right, "binary-op");
            } else {
                break;
            }
        }
        return left;
    }

    public Node _arithParseBitwiseXor() {
        Node left = this._arithParseBitwiseAnd();
        while (true) {
            this._arithSkipWs();
            if (this._arithPeek(0).equals("^") && !this._arithPeek(1).equals("=")) {
                this._arithAdvance();
                this._arithSkipWs();
                Node right = this._arithParseBitwiseAnd();
                left = new ArithBinaryOp("^", left, right, "binary-op");
            } else {
                break;
            }
        }
        return left;
    }

    public Node _arithParseBitwiseAnd() {
        Node left = this._arithParseEquality();
        while (true) {
            this._arithSkipWs();
            if (this._arithPeek(0).equals("&") && !this._arithPeek(1).equals("&") && !this._arithPeek(1).equals("=")) {
                this._arithAdvance();
                this._arithSkipWs();
                Node right = this._arithParseEquality();
                left = new ArithBinaryOp("&", left, right, "binary-op");
            } else {
                break;
            }
        }
        return left;
    }

    public Node _arithParseEquality() {
        return this._arithParseLeftAssoc(new ArrayList<>(List.of("==", "!=")), () -> this._arithParseComparison());
    }

    public Node _arithParseComparison() {
        Node left = this._arithParseShift();
        while (true) {
            this._arithSkipWs();
            Node right = null;
            if (this._arithMatch("<=")) {
                this._arithConsume("<=");
                this._arithSkipWs();
                right = this._arithParseShift();
                left = new ArithBinaryOp("<=", left, right, "binary-op");
            } else {
                if (this._arithMatch(">=")) {
                    this._arithConsume(">=");
                    this._arithSkipWs();
                    right = this._arithParseShift();
                    left = new ArithBinaryOp(">=", left, right, "binary-op");
                } else {
                    if (this._arithPeek(0).equals("<") && !this._arithPeek(1).equals("<") && !this._arithPeek(1).equals("=")) {
                        this._arithAdvance();
                        this._arithSkipWs();
                        right = this._arithParseShift();
                        left = new ArithBinaryOp("<", left, right, "binary-op");
                    } else {
                        if (this._arithPeek(0).equals(">") && !this._arithPeek(1).equals(">") && !this._arithPeek(1).equals("=")) {
                            this._arithAdvance();
                            this._arithSkipWs();
                            right = this._arithParseShift();
                            left = new ArithBinaryOp(">", left, right, "binary-op");
                        } else {
                            break;
                        }
                    }
                }
            }
        }
        return left;
    }

    public Node _arithParseShift() {
        Node left = this._arithParseAdditive();
        while (true) {
            this._arithSkipWs();
            if (this._arithMatch("<<=")) {
                break;
            }
            if (this._arithMatch(">>=")) {
                break;
            }
            Node right = null;
            if (this._arithMatch("<<")) {
                this._arithConsume("<<");
                this._arithSkipWs();
                right = this._arithParseAdditive();
                left = new ArithBinaryOp("<<", left, right, "binary-op");
            } else {
                if (this._arithMatch(">>")) {
                    this._arithConsume(">>");
                    this._arithSkipWs();
                    right = this._arithParseAdditive();
                    left = new ArithBinaryOp(">>", left, right, "binary-op");
                } else {
                    break;
                }
            }
        }
        return left;
    }

    public Node _arithParseAdditive() {
        Node left = this._arithParseMultiplicative();
        while (true) {
            this._arithSkipWs();
            String c = this._arithPeek(0);
            String c2 = this._arithPeek(1);
            Node right = null;
            if (c.equals("+") && !c2.equals("+") && !c2.equals("=")) {
                this._arithAdvance();
                this._arithSkipWs();
                right = this._arithParseMultiplicative();
                left = new ArithBinaryOp("+", left, right, "binary-op");
            } else {
                if (c.equals("-") && !c2.equals("-") && !c2.equals("=")) {
                    this._arithAdvance();
                    this._arithSkipWs();
                    right = this._arithParseMultiplicative();
                    left = new ArithBinaryOp("-", left, right, "binary-op");
                } else {
                    break;
                }
            }
        }
        return left;
    }

    public Node _arithParseMultiplicative() {
        Node left = this._arithParseExponentiation();
        while (true) {
            this._arithSkipWs();
            String c = this._arithPeek(0);
            String c2 = this._arithPeek(1);
            Node right = null;
            if (c.equals("*") && !c2.equals("*") && !c2.equals("=")) {
                this._arithAdvance();
                this._arithSkipWs();
                right = this._arithParseExponentiation();
                left = new ArithBinaryOp("*", left, right, "binary-op");
            } else {
                if (c.equals("/") && !c2.equals("=")) {
                    this._arithAdvance();
                    this._arithSkipWs();
                    right = this._arithParseExponentiation();
                    left = new ArithBinaryOp("/", left, right, "binary-op");
                } else {
                    if (c.equals("%") && !c2.equals("=")) {
                        this._arithAdvance();
                        this._arithSkipWs();
                        right = this._arithParseExponentiation();
                        left = new ArithBinaryOp("%", left, right, "binary-op");
                    } else {
                        break;
                    }
                }
            }
        }
        return left;
    }

    public Node _arithParseExponentiation() {
        Node left = this._arithParseUnary();
        this._arithSkipWs();
        if (this._arithMatch("**")) {
            this._arithConsume("**");
            this._arithSkipWs();
            Node right = this._arithParseExponentiation();
            return new ArithBinaryOp("**", left, right, "binary-op");
        }
        return left;
    }

    public Node _arithParseUnary() {
        this._arithSkipWs();
        Node operand = null;
        if (this._arithMatch("++")) {
            this._arithConsume("++");
            this._arithSkipWs();
            operand = this._arithParseUnary();
            return new ArithPreIncr(operand, "pre-incr");
        }
        if (this._arithMatch("--")) {
            this._arithConsume("--");
            this._arithSkipWs();
            operand = this._arithParseUnary();
            return new ArithPreDecr(operand, "pre-decr");
        }
        String c = this._arithPeek(0);
        if (c.equals("!")) {
            this._arithAdvance();
            this._arithSkipWs();
            operand = this._arithParseUnary();
            return new ArithUnaryOp("!", operand, "unary-op");
        }
        if (c.equals("~")) {
            this._arithAdvance();
            this._arithSkipWs();
            operand = this._arithParseUnary();
            return new ArithUnaryOp("~", operand, "unary-op");
        }
        if (c.equals("+") && !this._arithPeek(1).equals("+")) {
            this._arithAdvance();
            this._arithSkipWs();
            operand = this._arithParseUnary();
            return new ArithUnaryOp("+", operand, "unary-op");
        }
        if (c.equals("-") && !this._arithPeek(1).equals("-")) {
            this._arithAdvance();
            this._arithSkipWs();
            operand = this._arithParseUnary();
            return new ArithUnaryOp("-", operand, "unary-op");
        }
        return this._arithParsePostfix();
    }

    public Node _arithParsePostfix() {
        Node left = this._arithParsePrimary();
        while (true) {
            this._arithSkipWs();
            if (this._arithMatch("++")) {
                this._arithConsume("++");
                left = new ArithPostIncr(left, "post-incr");
            } else {
                if (this._arithMatch("--")) {
                    this._arithConsume("--");
                    left = new ArithPostDecr(left, "post-decr");
                } else {
                    if (this._arithPeek(0).equals("[")) {
                        if (left instanceof ArithVar leftArithVar) {
                            this._arithAdvance();
                            this._arithSkipWs();
                            Node index = this._arithParseComma();
                            this._arithSkipWs();
                            if (!this._arithConsume("]")) {
                                throw new RuntimeException("Expected ']' in array subscript");
                            }
                            left = new ArithSubscript(leftArithVar.name, index, "subscript");
                        } else {
                            break;
                        }
                    } else {
                        break;
                    }
                }
            }
        }
        return left;
    }

    public Node _arithParsePrimary() {
        this._arithSkipWs();
        String c = this._arithPeek(0);
        if (c.equals("(")) {
            this._arithAdvance();
            this._arithSkipWs();
            Node expr = this._arithParseComma();
            this._arithSkipWs();
            if (!this._arithConsume(")")) {
                throw new RuntimeException("Expected ')' in arithmetic expression");
            }
            return expr;
        }
        if (c.equals("#") && this._arithPeek(1).equals("$")) {
            this._arithAdvance();
            return this._arithParseExpansion();
        }
        if (c.equals("$")) {
            return this._arithParseExpansion();
        }
        if (c.equals("'")) {
            return this._arithParseSingleQuote();
        }
        if (c.equals("\"")) {
            return this._arithParseDoubleQuote();
        }
        if (c.equals("`")) {
            return this._arithParseBacktick();
        }
        if (c.equals("\\")) {
            this._arithAdvance();
            if (this._arithAtEnd()) {
                throw new RuntimeException("Unexpected end after backslash in arithmetic");
            }
            String escapedChar = this._arithAdvance();
            return new ArithEscape(escapedChar, "escape");
        }
        if (this._arithAtEnd() || ")]:,;?|&<>=!+-*/%^~#{}".indexOf(c) != -1) {
            return new ArithEmpty("empty");
        }
        return this._arithParseNumberOrVar();
    }

    public Node _arithParseExpansion() {
        if (!this._arithConsume("$")) {
            throw new RuntimeException("Expected '$'");
        }
        String c = this._arithPeek(0);
        if (c.equals("(")) {
            return this._arithParseCmdsub();
        }
        if (c.equals("{")) {
            return this._arithParseBracedParam();
        }
        List<String> nameChars = new ArrayList<>();
        while (!this._arithAtEnd()) {
            String ch = this._arithPeek(0);
            if (ch.chars().allMatch(Character::isLetterOrDigit) || ch.equals("_")) {
                nameChars.add(this._arithAdvance());
            } else {
                if (ParableFunctions._isSpecialParamOrDigit(ch) || ch.equals("#") && !(!nameChars.isEmpty())) {
                    nameChars.add(this._arithAdvance());
                    break;
                } else {
                    break;
                }
            }
        }
        if (!(!nameChars.isEmpty())) {
            throw new RuntimeException("Expected variable name after $");
        }
        return new ParamExpansion(String.join("", nameChars), "", "", "param");
    }

    public Node _arithParseCmdsub() {
        this._arithAdvance();
        int depth = 0;
        int contentStart = 0;
        String ch = "";
        String content = "";
        if (this._arithPeek(0).equals("(")) {
            this._arithAdvance();
            depth = 1;
            contentStart = this._arithPos;
            while (!this._arithAtEnd() && depth > 0) {
                ch = this._arithPeek(0);
                if (ch.equals("(")) {
                    depth += 1;
                    this._arithAdvance();
                } else {
                    if (ch.equals(")")) {
                        if (depth == 1 && this._arithPeek(1).equals(")")) {
                            break;
                        }
                        depth -= 1;
                        this._arithAdvance();
                    } else {
                        this._arithAdvance();
                    }
                }
            }
            content = ParableFunctions._substring(this._arithSrc, contentStart, this._arithPos);
            this._arithAdvance();
            this._arithAdvance();
            Node innerExpr = this._parseArithExpr(content);
            return new ArithmeticExpansion(innerExpr, "arith");
        }
        depth = 1;
        contentStart = this._arithPos;
        while (!this._arithAtEnd() && depth > 0) {
            ch = this._arithPeek(0);
            if (ch.equals("(")) {
                depth += 1;
                this._arithAdvance();
            } else {
                if (ch.equals(")")) {
                    depth -= 1;
                    if (depth == 0) {
                        break;
                    }
                    this._arithAdvance();
                } else {
                    this._arithAdvance();
                }
            }
        }
        content = ParableFunctions._substring(this._arithSrc, contentStart, this._arithPos);
        this._arithAdvance();
        Parser subParser = ParableFunctions.newParser(content, false, this._extglob);
        Node cmd = subParser.parseList(true);
        return new CommandSubstitution(cmd, false, "cmdsub");
    }

    public Node _arithParseBracedParam() {
        this._arithAdvance();
        List<String> nameChars = new ArrayList<>();
        if (this._arithPeek(0).equals("!")) {
            this._arithAdvance();
            nameChars = new ArrayList<>();
            while (!this._arithAtEnd() && !this._arithPeek(0).equals("}")) {
                nameChars.add(this._arithAdvance());
            }
            this._arithConsume("}");
            return new ParamIndirect(String.join("", nameChars), "", "", "param-indirect");
        }
        if (this._arithPeek(0).equals("#")) {
            this._arithAdvance();
            nameChars = new ArrayList<>();
            while (!this._arithAtEnd() && !this._arithPeek(0).equals("}")) {
                nameChars.add(this._arithAdvance());
            }
            this._arithConsume("}");
            return new ParamLength(String.join("", nameChars), "param-len");
        }
        nameChars = new ArrayList<>();
        String ch = "";
        while (!this._arithAtEnd()) {
            ch = this._arithPeek(0);
            if (ch.equals("}")) {
                this._arithAdvance();
                return new ParamExpansion(String.join("", nameChars), "", "", "param");
            }
            if (ParableFunctions._isParamExpansionOp(ch)) {
                break;
            }
            nameChars.add(this._arithAdvance());
        }
        String name = String.join("", nameChars);
        List<String> opChars = new ArrayList<>();
        int depth = 1;
        while (!this._arithAtEnd() && depth > 0) {
            ch = this._arithPeek(0);
            if (ch.equals("{")) {
                depth += 1;
                opChars.add(this._arithAdvance());
            } else {
                if (ch.equals("}")) {
                    depth -= 1;
                    if (depth == 0) {
                        break;
                    }
                    opChars.add(this._arithAdvance());
                } else {
                    opChars.add(this._arithAdvance());
                }
            }
        }
        this._arithConsume("}");
        String opStr = String.join("", opChars);
        if (opStr.startsWith(":-")) {
            return new ParamExpansion(name, ":-", ParableFunctions._substring(opStr, 2, opStr.length()), "param");
        }
        if (opStr.startsWith(":=")) {
            return new ParamExpansion(name, ":=", ParableFunctions._substring(opStr, 2, opStr.length()), "param");
        }
        if (opStr.startsWith(":+")) {
            return new ParamExpansion(name, ":+", ParableFunctions._substring(opStr, 2, opStr.length()), "param");
        }
        if (opStr.startsWith(":?")) {
            return new ParamExpansion(name, ":?", ParableFunctions._substring(opStr, 2, opStr.length()), "param");
        }
        if (opStr.startsWith(":")) {
            return new ParamExpansion(name, ":", ParableFunctions._substring(opStr, 1, opStr.length()), "param");
        }
        if (opStr.startsWith("##")) {
            return new ParamExpansion(name, "##", ParableFunctions._substring(opStr, 2, opStr.length()), "param");
        }
        if (opStr.startsWith("#")) {
            return new ParamExpansion(name, "#", ParableFunctions._substring(opStr, 1, opStr.length()), "param");
        }
        if (opStr.startsWith("%%")) {
            return new ParamExpansion(name, "%%", ParableFunctions._substring(opStr, 2, opStr.length()), "param");
        }
        if (opStr.startsWith("%")) {
            return new ParamExpansion(name, "%", ParableFunctions._substring(opStr, 1, opStr.length()), "param");
        }
        if (opStr.startsWith("//")) {
            return new ParamExpansion(name, "//", ParableFunctions._substring(opStr, 2, opStr.length()), "param");
        }
        if (opStr.startsWith("/")) {
            return new ParamExpansion(name, "/", ParableFunctions._substring(opStr, 1, opStr.length()), "param");
        }
        return new ParamExpansion(name, "", opStr, "param");
    }

    public Node _arithParseSingleQuote() {
        this._arithAdvance();
        int contentStart = this._arithPos;
        while (!this._arithAtEnd() && !this._arithPeek(0).equals("'")) {
            this._arithAdvance();
        }
        String content = ParableFunctions._substring(this._arithSrc, contentStart, this._arithPos);
        if (!this._arithConsume("'")) {
            throw new RuntimeException("Unterminated single quote in arithmetic");
        }
        return new ArithNumber(content, "number");
    }

    public Node _arithParseDoubleQuote() {
        this._arithAdvance();
        int contentStart = this._arithPos;
        while (!this._arithAtEnd() && !this._arithPeek(0).equals("\"")) {
            String c = this._arithPeek(0);
            if (c.equals("\\") && !this._arithAtEnd()) {
                this._arithAdvance();
                this._arithAdvance();
            } else {
                this._arithAdvance();
            }
        }
        String content = ParableFunctions._substring(this._arithSrc, contentStart, this._arithPos);
        if (!this._arithConsume("\"")) {
            throw new RuntimeException("Unterminated double quote in arithmetic");
        }
        return new ArithNumber(content, "number");
    }

    public Node _arithParseBacktick() {
        this._arithAdvance();
        int contentStart = this._arithPos;
        while (!this._arithAtEnd() && !this._arithPeek(0).equals("`")) {
            String c = this._arithPeek(0);
            if (c.equals("\\") && !this._arithAtEnd()) {
                this._arithAdvance();
                this._arithAdvance();
            } else {
                this._arithAdvance();
            }
        }
        String content = ParableFunctions._substring(this._arithSrc, contentStart, this._arithPos);
        if (!this._arithConsume("`")) {
            throw new RuntimeException("Unterminated backtick in arithmetic");
        }
        Parser subParser = ParableFunctions.newParser(content, false, this._extglob);
        Node cmd = subParser.parseList(true);
        return new CommandSubstitution(cmd, false, "cmdsub");
    }

    public Node _arithParseNumberOrVar() {
        this._arithSkipWs();
        List<String> chars = new ArrayList<>();
        String c = this._arithPeek(0);
        String ch = "";
        if (c.chars().allMatch(Character::isDigit)) {
            while (!this._arithAtEnd()) {
                ch = this._arithPeek(0);
                if (ch.chars().allMatch(Character::isLetterOrDigit) || ch.equals("#") || ch.equals("_")) {
                    chars.add(this._arithAdvance());
                } else {
                    break;
                }
            }
            String prefix = String.join("", chars);
            if (!this._arithAtEnd() && this._arithPeek(0).equals("$")) {
                Node expansion = this._arithParseExpansion();
                return new ArithConcat(new ArrayList<>(List.of(new ArithNumber(prefix, "number"), expansion)), "arith-concat");
            }
            return new ArithNumber(prefix, "number");
        }
        if (c.chars().allMatch(Character::isLetter) || c.equals("_")) {
            while (!this._arithAtEnd()) {
                ch = this._arithPeek(0);
                if (ch.chars().allMatch(Character::isLetterOrDigit) || ch.equals("_")) {
                    chars.add(this._arithAdvance());
                } else {
                    break;
                }
            }
            return new ArithVar(String.join("", chars), "var");
        }
        throw new RuntimeException("Unexpected character '" + c + "' in arithmetic expression");
    }

    public Tuple3 _parseDeprecatedArithmetic() {
        if (this.atEnd() || !this.peek().equals("$")) {
            return new Tuple3(null, "");
        }
        int start = this.pos;
        if (this.pos + 1 >= this.length || !String.valueOf(this.source.charAt(this.pos + 1)).equals("[")) {
            return new Tuple3(null, "");
        }
        this.advance();
        this.advance();
        this._lexer.pos = this.pos;
        String content = this._lexer._parseMatchedPair("[", "]", Constants.MATCHEDPAIRFLAGS_ARITH, false);
        this.pos = this._lexer.pos;
        String text = ParableFunctions._substring(this.source, start, this.pos);
        return new Tuple3(new ArithDeprecated(content, "arith-deprecated"), text);
    }

    public Tuple3 _parseParamExpansion(boolean inDquote) {
        this._syncLexer();
        Tuple3 _tuple28 = this._lexer._readParamExpansion(inDquote);
        Node result0 = _tuple28.f0();
        String result1 = _tuple28.f1();
        this._syncParser();
        return new Tuple3(result0, result1);
    }

    public Node parseRedirect() {
        this.skipWhitespace();
        if (this.atEnd()) {
            return null;
        }
        int start = this.pos;
        int fd = -1;
        String varfd = "";
        String ch = "";
        if (this.peek().equals("{")) {
            int saved = this.pos;
            this.advance();
            List<String> varnameChars = new ArrayList<>();
            boolean inBracket = false;
            while (!this.atEnd() && !ParableFunctions._isRedirectChar(this.peek())) {
                ch = this.peek();
                if (ch.equals("}") && !inBracket) {
                    break;
                } else {
                    if (ch.equals("[")) {
                        inBracket = true;
                        varnameChars.add(this.advance());
                    } else {
                        if (ch.equals("]")) {
                            inBracket = false;
                            varnameChars.add(this.advance());
                        } else {
                            if (ch.chars().allMatch(Character::isLetterOrDigit) || ch.equals("_")) {
                                varnameChars.add(this.advance());
                            } else {
                                if (inBracket && !ParableFunctions._isMetachar(ch)) {
                                    varnameChars.add(this.advance());
                                } else {
                                    break;
                                }
                            }
                        }
                    }
                }
            }
            String varname = String.join("", varnameChars);
            boolean isValidVarfd = false;
            if (!varname.equals("")) {
                if (String.valueOf(varname.charAt(0)).chars().allMatch(Character::isLetter) || String.valueOf(varname.charAt(0)).equals("_")) {
                    if (varname.indexOf("[") != -1 || varname.indexOf("]") != -1) {
                        int left = varname.indexOf("[");
                        int right = varname.lastIndexOf("]");
                        if (left != -1 && right == varname.length() - 1 && right > left + 1) {
                            String base = varname.substring(0, left);
                            if (!base.equals("") && String.valueOf(base.charAt(0)).chars().allMatch(Character::isLetter) || String.valueOf(base.charAt(0)).equals("_")) {
                                isValidVarfd = true;
                                for (int _i = 0; _i < base.substring(1).length(); _i++) {
                                    String c = String.valueOf(base.substring(1).charAt(_i));
                                    if (!(c.chars().allMatch(Character::isLetterOrDigit) || c == "_")) {
                                        isValidVarfd = false;
                                        break;
                                    }
                                }
                            }
                        }
                    } else {
                        isValidVarfd = true;
                        for (int _i = 0; _i < varname.substring(1).length(); _i++) {
                            String c = String.valueOf(varname.substring(1).charAt(_i));
                            if (!(c.chars().allMatch(Character::isLetterOrDigit) || c == "_")) {
                                isValidVarfd = false;
                                break;
                            }
                        }
                    }
                }
            }
            if (!this.atEnd() && this.peek().equals("}") && isValidVarfd) {
                this.advance();
                varfd = varname;
            } else {
                this.pos = saved;
            }
        }
        List<String> fdChars = new ArrayList<>();
        if (varfd.equals("") && !this.peek().equals("") && this.peek().chars().allMatch(Character::isDigit)) {
            fdChars = new ArrayList<>();
            while (!this.atEnd() && this.peek().chars().allMatch(Character::isDigit)) {
                fdChars.add(this.advance());
            }
            fd = Integer.parseInt(String.join("", fdChars), 10);
        }
        ch = this.peek();
        String op = "";
        Word target = null;
        if (ch.equals("&") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals(">")) {
            if (fd != -1 || !varfd.equals("")) {
                this.pos = start;
                return null;
            }
            this.advance();
            this.advance();
            if (!this.atEnd() && this.peek().equals(">")) {
                this.advance();
                op = "&>>";
            } else {
                op = "&>";
            }
            this.skipWhitespace();
            target = this.parseWord(false, false, false);
            if (target == null) {
                throw new RuntimeException("Expected target for redirect " + op);
            }
            return new Redirect(op, target, null, "redirect");
        }
        if (ch.equals("") || !ParableFunctions._isRedirectChar(ch)) {
            this.pos = start;
            return null;
        }
        if (fd == -1 && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("(")) {
            this.pos = start;
            return null;
        }
        op = this.advance();
        boolean stripTabs = false;
        if (!this.atEnd()) {
            String nextCh = this.peek();
            if (op.equals(">") && nextCh.equals(">")) {
                this.advance();
                op = ">>";
            } else {
                if (op.equals("<") && nextCh.equals("<")) {
                    this.advance();
                    if (!this.atEnd() && this.peek().equals("<")) {
                        this.advance();
                        op = "<<<";
                    } else {
                        if (!this.atEnd() && this.peek().equals("-")) {
                            this.advance();
                            op = "<<";
                            stripTabs = true;
                        } else {
                            op = "<<";
                        }
                    }
                } else {
                    if (op.equals("<") && nextCh.equals(">")) {
                        this.advance();
                        op = "<>";
                    } else {
                        if (op.equals(">") && nextCh.equals("|")) {
                            this.advance();
                            op = ">|";
                        } else {
                            if (fd == -1 && varfd.equals("") && op.equals(">") && nextCh.equals("&")) {
                                if (this.pos + 1 >= this.length || !ParableFunctions._isDigitOrDash(String.valueOf(this.source.charAt(this.pos + 1)))) {
                                    this.advance();
                                    op = ">&";
                                }
                            } else {
                                if (fd == -1 && varfd.equals("") && op.equals("<") && nextCh.equals("&")) {
                                    if (this.pos + 1 >= this.length || !ParableFunctions._isDigitOrDash(String.valueOf(this.source.charAt(this.pos + 1)))) {
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
        if (op.equals("<<")) {
            return this._parseHeredoc((fd), stripTabs);
        }
        if (!varfd.equals("")) {
            op = "{" + varfd + "}" + op;
        } else {
            if (fd != -1) {
                op = String.valueOf(fd) + op;
            }
        }
        if (!this.atEnd() && this.peek().equals("&")) {
            this.advance();
            this.skipWhitespace();
            if (!this.atEnd() && this.peek().equals("-")) {
                if (this.pos + 1 < this.length && !ParableFunctions._isMetachar(String.valueOf(this.source.charAt(this.pos + 1)))) {
                    this.advance();
                    target = new Word("&-", new ArrayList<>(), "word");
                } else {
                    target = null;
                }
            } else {
                target = null;
            }
            if (target == null) {
                Word innerWord = null;
                if (!this.atEnd() && this.peek().chars().allMatch(Character::isDigit) || this.peek().equals("-")) {
                    int wordStart = this.pos;
                    fdChars = new ArrayList<>();
                    while (!this.atEnd() && this.peek().chars().allMatch(Character::isDigit)) {
                        fdChars.add(this.advance());
                    }
                    String fdTarget = "";
                    if (!fdChars.isEmpty()) {
                        fdTarget = String.join("", fdChars);
                    } else {
                        fdTarget = "";
                    }
                    if (!this.atEnd() && this.peek().equals("-")) {
                        fdTarget += this.advance();
                    }
                    if (!fdTarget.equals("-") && !this.atEnd() && !ParableFunctions._isMetachar(this.peek())) {
                        this.pos = wordStart;
                        innerWord = this.parseWord(false, false, false);
                        if (innerWord != null) {
                            target = new Word("&" + innerWord.value, new ArrayList<>(), "word");
                            target.parts = innerWord.parts;
                        } else {
                            throw new RuntimeException("Expected target for redirect " + op);
                        }
                    } else {
                        target = new Word("&" + fdTarget, new ArrayList<>(), "word");
                    }
                } else {
                    innerWord = this.parseWord(false, false, false);
                    if (innerWord != null) {
                        target = new Word("&" + innerWord.value, new ArrayList<>(), "word");
                        target.parts = innerWord.parts;
                    } else {
                        throw new RuntimeException("Expected target for redirect " + op);
                    }
                }
            }
        } else {
            this.skipWhitespace();
            if (op.equals(">&") || op.equals("<&") && !this.atEnd() && this.peek().equals("-")) {
                if (this.pos + 1 < this.length && !ParableFunctions._isMetachar(String.valueOf(this.source.charAt(this.pos + 1)))) {
                    this.advance();
                    target = new Word("&-", new ArrayList<>(), "word");
                } else {
                    target = this.parseWord(false, false, false);
                }
            } else {
                target = this.parseWord(false, false, false);
            }
        }
        if (target == null) {
            throw new RuntimeException("Expected target for redirect " + op);
        }
        return new Redirect(op, target, null, "redirect");
    }

    public Tuple2 _parseHeredocDelimiter() {
        this.skipWhitespace();
        boolean quoted = false;
        List<String> delimiterChars = new ArrayList<>();
        while (true) {
            String c = "";
            int depth = 0;
            while (!this.atEnd() && !ParableFunctions._isMetachar(this.peek())) {
                String ch = this.peek();
                if (ch.equals("\"")) {
                    quoted = true;
                    this.advance();
                    while (!this.atEnd() && !this.peek().equals("\"")) {
                        delimiterChars.add(this.advance());
                    }
                    if (!this.atEnd()) {
                        this.advance();
                    }
                } else {
                    if (ch.equals("'")) {
                        quoted = true;
                        this.advance();
                        while (!this.atEnd() && !this.peek().equals("'")) {
                            c = this.advance();
                            if (c.equals("\n")) {
                                this._sawNewlineInSingleQuote = true;
                            }
                            delimiterChars.add(c);
                        }
                        if (!this.atEnd()) {
                            this.advance();
                        }
                    } else {
                        if (ch.equals("\\")) {
                            this.advance();
                            if (!this.atEnd()) {
                                String nextCh = this.peek();
                                if (nextCh.equals("\n")) {
                                    this.advance();
                                } else {
                                    quoted = true;
                                    delimiterChars.add(this.advance());
                                }
                            }
                        } else {
                            if (ch.equals("$") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("'")) {
                                quoted = true;
                                this.advance();
                                this.advance();
                                while (!this.atEnd() && !this.peek().equals("'")) {
                                    c = this.peek();
                                    if (c.equals("\\") && this.pos + 1 < this.length) {
                                        this.advance();
                                        String esc = this.peek();
                                        int escVal = ParableFunctions._getAnsiEscape(esc);
                                        if (escVal >= 0) {
                                            delimiterChars.add(String.valueOf(((char) escVal)));
                                            this.advance();
                                        } else {
                                            if (esc.equals("'")) {
                                                delimiterChars.add(this.advance());
                                            } else {
                                                delimiterChars.add(this.advance());
                                            }
                                        }
                                    } else {
                                        delimiterChars.add(this.advance());
                                    }
                                }
                                if (!this.atEnd()) {
                                    this.advance();
                                }
                            } else {
                                if (ParableFunctions._isExpansionStart(this.source, this.pos, "$(")) {
                                    delimiterChars.add(this.advance());
                                    delimiterChars.add(this.advance());
                                    depth = 1;
                                    while (!this.atEnd() && depth > 0) {
                                        c = this.peek();
                                        if (c.equals("(")) {
                                            depth += 1;
                                        } else {
                                            if (c.equals(")")) {
                                                depth -= 1;
                                            }
                                        }
                                        delimiterChars.add(this.advance());
                                    }
                                } else {
                                    int dollarCount = 0;
                                    int j = 0;
                                    if (ch.equals("$") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("{")) {
                                        dollarCount = 0;
                                        j = this.pos - 1;
                                        while (j >= 0 && String.valueOf(this.source.charAt(j)).equals("$")) {
                                            dollarCount += 1;
                                            j -= 1;
                                        }
                                        if (j >= 0 && String.valueOf(this.source.charAt(j)).equals("\\")) {
                                            dollarCount -= 1;
                                        }
                                        if (dollarCount % 2 == 1) {
                                            delimiterChars.add(this.advance());
                                        } else {
                                            delimiterChars.add(this.advance());
                                            delimiterChars.add(this.advance());
                                            depth = 0;
                                            while (!this.atEnd()) {
                                                c = this.peek();
                                                if (c.equals("{")) {
                                                    depth += 1;
                                                } else {
                                                    if (c.equals("}")) {
                                                        delimiterChars.add(this.advance());
                                                        if (depth == 0) {
                                                            break;
                                                        }
                                                        depth -= 1;
                                                        if (depth == 0 && !this.atEnd() && ParableFunctions._isMetachar(this.peek())) {
                                                            break;
                                                        }
                                                        continue;
                                                    }
                                                }
                                                delimiterChars.add(this.advance());
                                            }
                                        }
                                    } else {
                                        if (ch.equals("$") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("[")) {
                                            dollarCount = 0;
                                            j = this.pos - 1;
                                            while (j >= 0 && String.valueOf(this.source.charAt(j)).equals("$")) {
                                                dollarCount += 1;
                                                j -= 1;
                                            }
                                            if (j >= 0 && String.valueOf(this.source.charAt(j)).equals("\\")) {
                                                dollarCount -= 1;
                                            }
                                            if (dollarCount % 2 == 1) {
                                                delimiterChars.add(this.advance());
                                            } else {
                                                delimiterChars.add(this.advance());
                                                delimiterChars.add(this.advance());
                                                depth = 1;
                                                while (!this.atEnd() && depth > 0) {
                                                    c = this.peek();
                                                    if (c.equals("[")) {
                                                        depth += 1;
                                                    } else {
                                                        if (c.equals("]")) {
                                                            depth -= 1;
                                                        }
                                                    }
                                                    delimiterChars.add(this.advance());
                                                }
                                            }
                                        } else {
                                            if (ch.equals("`")) {
                                                delimiterChars.add(this.advance());
                                                while (!this.atEnd() && !this.peek().equals("`")) {
                                                    c = this.peek();
                                                    if (c.equals("'")) {
                                                        delimiterChars.add(this.advance());
                                                        while (!this.atEnd() && !this.peek().equals("'") && !this.peek().equals("`")) {
                                                            delimiterChars.add(this.advance());
                                                        }
                                                        if (!this.atEnd() && this.peek().equals("'")) {
                                                            delimiterChars.add(this.advance());
                                                        }
                                                    } else {
                                                        if (c.equals("\"")) {
                                                            delimiterChars.add(this.advance());
                                                            while (!this.atEnd() && !this.peek().equals("\"") && !this.peek().equals("`")) {
                                                                if (this.peek().equals("\\") && this.pos + 1 < this.length) {
                                                                    delimiterChars.add(this.advance());
                                                                }
                                                                delimiterChars.add(this.advance());
                                                            }
                                                            if (!this.atEnd() && this.peek().equals("\"")) {
                                                                delimiterChars.add(this.advance());
                                                            }
                                                        } else {
                                                            if (c.equals("\\") && this.pos + 1 < this.length) {
                                                                delimiterChars.add(this.advance());
                                                                delimiterChars.add(this.advance());
                                                            } else {
                                                                delimiterChars.add(this.advance());
                                                            }
                                                        }
                                                    }
                                                }
                                                if (!this.atEnd()) {
                                                    delimiterChars.add(this.advance());
                                                }
                                            } else {
                                                delimiterChars.add(this.advance());
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            if (!this.atEnd() && "<>".indexOf(this.peek()) != -1 && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("(")) {
                delimiterChars.add(this.advance());
                delimiterChars.add(this.advance());
                depth = 1;
                while (!this.atEnd() && depth > 0) {
                    c = this.peek();
                    if (c.equals("(")) {
                        depth += 1;
                    } else {
                        if (c.equals(")")) {
                            depth -= 1;
                        }
                    }
                    delimiterChars.add(this.advance());
                }
                continue;
            }
            break;
        }
        return new Tuple2(String.join("", delimiterChars), quoted);
    }

    public Tuple10 _readHeredocLine(boolean quoted) {
        int lineStart = this.pos;
        int lineEnd = this.pos;
        while (lineEnd < this.length && !String.valueOf(this.source.charAt(lineEnd)).equals("\n")) {
            lineEnd += 1;
        }
        String line = ParableFunctions._substring(this.source, lineStart, lineEnd);
        if (!quoted) {
            while (lineEnd < this.length) {
                int trailingBs = ParableFunctions._countTrailingBackslashes(line);
                if (trailingBs % 2 == 0) {
                    break;
                }
                line = ParableFunctions._substring(line, 0, line.length() - 1);
                lineEnd += 1;
                int nextLineStart = lineEnd;
                while (lineEnd < this.length && !String.valueOf(this.source.charAt(lineEnd)).equals("\n")) {
                    lineEnd += 1;
                }
                line = line + ParableFunctions._substring(this.source, nextLineStart, lineEnd);
            }
        }
        return new Tuple10(line, lineEnd);
    }

    public Tuple11 _lineMatchesDelimiter(String line, String delimiter, boolean stripTabs) {
        String checkLine = (stripTabs ? line.replaceFirst("^[" + "\t" + "]+", "") : line);
        String normalizedCheck = ParableFunctions._normalizeHeredocDelimiter(checkLine);
        String normalizedDelim = ParableFunctions._normalizeHeredocDelimiter(delimiter);
        return new Tuple11(normalizedCheck.equals(normalizedDelim), checkLine);
    }

    public void _gatherHeredocBodies() {
        for (HereDoc heredoc : this._pendingHeredocs) {
            List<String> contentLines = new ArrayList<>();
            int lineStart = this.pos;
            while (this.pos < this.length) {
                lineStart = this.pos;
                Tuple10 _tuple29 = this._readHeredocLine(heredoc.quoted);
                String line = _tuple29.f0();
                int lineEnd = _tuple29.f1();
                Tuple11 _tuple30 = this._lineMatchesDelimiter(line, heredoc.delimiter, heredoc.stripTabs);
                boolean matches = _tuple30.f0();
                String checkLine = _tuple30.f1();
                if (matches) {
                    this.pos = (lineEnd < this.length ? lineEnd + 1 : lineEnd);
                    break;
                }
                String normalizedCheck = ParableFunctions._normalizeHeredocDelimiter(checkLine);
                String normalizedDelim = ParableFunctions._normalizeHeredocDelimiter(heredoc.delimiter);
                int tabsStripped = 0;
                if (this._eofToken.equals(")") && normalizedCheck.startsWith(normalizedDelim)) {
                    tabsStripped = line.length() - checkLine.length();
                    this.pos = lineStart + tabsStripped + heredoc.delimiter.length();
                    break;
                }
                if (lineEnd >= this.length && normalizedCheck.startsWith(normalizedDelim) && this._inProcessSub) {
                    tabsStripped = line.length() - checkLine.length();
                    this.pos = lineStart + tabsStripped + heredoc.delimiter.length();
                    break;
                }
                if (heredoc.stripTabs) {
                    line = line.replaceFirst("^[" + "\t" + "]+", "");
                }
                if (lineEnd < this.length) {
                    contentLines.add(line + "\n");
                    this.pos = lineEnd + 1;
                } else {
                    boolean addNewline = true;
                    if (!heredoc.quoted && ParableFunctions._countTrailingBackslashes(line) % 2 == 1) {
                        addNewline = false;
                    }
                    contentLines.add(line + (addNewline ? "\n" : ""));
                    this.pos = this.length;
                }
            }
            heredoc.content = String.join("", contentLines);
        }
        this._pendingHeredocs = new ArrayList<>();
    }

    public HereDoc _parseHeredoc(Integer fd, boolean stripTabs) {
        int startPos = this.pos;
        this._setState(Constants.PARSERSTATEFLAGS_PST_HEREDOC);
        Tuple2 _tuple31 = this._parseHeredocDelimiter();
        String delimiter = _tuple31.f0();
        boolean quoted = _tuple31.f1();
        for (HereDoc existing : this._pendingHeredocs) {
            if (existing._startPos == startPos && existing.delimiter.equals(delimiter)) {
                this._clearState(Constants.PARSERSTATEFLAGS_PST_HEREDOC);
                return existing;
            }
        }
        HereDoc heredoc = new HereDoc(delimiter, "", stripTabs, quoted, fd, false, 0, "heredoc");
        heredoc._startPos = startPos;
        this._pendingHeredocs.add(heredoc);
        this._clearState(Constants.PARSERSTATEFLAGS_PST_HEREDOC);
        return heredoc;
    }

    public Command parseCommand() {
        List<Word> words = new ArrayList<>();
        List<Node> redirects = new ArrayList<>();
        while (true) {
            this.skipWhitespace();
            if (this._lexIsCommandTerminator()) {
                break;
            }
            if (words.isEmpty()) {
                String reserved = this._lexPeekReservedWord();
                if (reserved.equals("}") || reserved.equals("]]")) {
                    break;
                }
            }
            Node redirect = this.parseRedirect();
            if (redirect != null) {
                redirects.add(redirect);
                continue;
            }
            boolean allAssignments = true;
            for (Word w : words) {
                if (!this._isAssignmentWord(w)) {
                    allAssignments = false;
                    break;
                }
            }
            boolean inAssignBuiltin = !words.isEmpty() && Constants.ASSIGNMENT_BUILTINS.contains(words.get(0).value);
            Word word = this.parseWord(!(!words.isEmpty()) || allAssignments && redirects.isEmpty(), false, inAssignBuiltin);
            if (word == null) {
                break;
            }
            words.add(word);
        }
        if (!(!words.isEmpty()) && !(!redirects.isEmpty())) {
            return null;
        }
        return new Command(words, redirects, "command");
    }

    public Subshell parseSubshell() {
        this.skipWhitespace();
        if (this.atEnd() || !this.peek().equals("(")) {
            return null;
        }
        this.advance();
        this._setState(Constants.PARSERSTATEFLAGS_PST_SUBSHELL);
        Node body = this.parseList(true);
        if (body == null) {
            this._clearState(Constants.PARSERSTATEFLAGS_PST_SUBSHELL);
            throw new RuntimeException("Expected command in subshell");
        }
        this.skipWhitespace();
        if (this.atEnd() || !this.peek().equals(")")) {
            this._clearState(Constants.PARSERSTATEFLAGS_PST_SUBSHELL);
            throw new RuntimeException("Expected ) to close subshell");
        }
        this.advance();
        this._clearState(Constants.PARSERSTATEFLAGS_PST_SUBSHELL);
        return new Subshell(body, this._collectRedirects(), "subshell");
    }

    public ArithmeticCommand parseArithmeticCommand() {
        this.skipWhitespace();
        if (this.atEnd() || !this.peek().equals("(") || this.pos + 1 >= this.length || !String.valueOf(this.source.charAt(this.pos + 1)).equals("(")) {
            return null;
        }
        int savedPos = this.pos;
        this.advance();
        this.advance();
        int contentStart = this.pos;
        int depth = 1;
        while (!this.atEnd() && depth > 0) {
            String c = this.peek();
            if (c.equals("'")) {
                this.advance();
                while (!this.atEnd() && !this.peek().equals("'")) {
                    this.advance();
                }
                if (!this.atEnd()) {
                    this.advance();
                }
            } else {
                if (c.equals("\"")) {
                    this.advance();
                    while (!this.atEnd()) {
                        if (this.peek().equals("\\") && this.pos + 1 < this.length) {
                            this.advance();
                            this.advance();
                        } else {
                            if (this.peek().equals("\"")) {
                                this.advance();
                                break;
                            } else {
                                this.advance();
                            }
                        }
                    }
                } else {
                    if (c.equals("\\") && this.pos + 1 < this.length) {
                        this.advance();
                        this.advance();
                    } else {
                        if (c.equals("(")) {
                            depth += 1;
                            this.advance();
                        } else {
                            if (c.equals(")")) {
                                if (depth == 1 && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals(")")) {
                                    break;
                                }
                                depth -= 1;
                                if (depth == 0) {
                                    this.pos = savedPos;
                                    return null;
                                }
                                this.advance();
                            } else {
                                this.advance();
                            }
                        }
                    }
                }
            }
        }
        if (this.atEnd()) {
            throw new RuntimeException("unexpected EOF looking for `))'");
        }
        if (depth != 1) {
            this.pos = savedPos;
            return null;
        }
        String content = ParableFunctions._substring(this.source, contentStart, this.pos);
        content = content.replace("\\\n", "");
        this.advance();
        this.advance();
        Node expr = this._parseArithExpr(content);
        return new ArithmeticCommand(expr, this._collectRedirects(), content, "arith-cmd");
    }

    public ConditionalExpr parseConditionalExpr() {
        this.skipWhitespace();
        if (this.atEnd() || !this.peek().equals("[") || this.pos + 1 >= this.length || !String.valueOf(this.source.charAt(this.pos + 1)).equals("[")) {
            return null;
        }
        int nextPos = this.pos + 2;
        if (nextPos < this.length && !(ParableFunctions._isWhitespace(String.valueOf(this.source.charAt(nextPos))) || String.valueOf(this.source.charAt(nextPos)).equals("\\") && nextPos + 1 < this.length && String.valueOf(this.source.charAt(nextPos + 1)).equals("\n"))) {
            return null;
        }
        this.advance();
        this.advance();
        this._setState(Constants.PARSERSTATEFLAGS_PST_CONDEXPR);
        this._wordContext = Constants.WORD_CTX_COND;
        Node body = this._parseCondOr();
        while (!this.atEnd() && ParableFunctions._isWhitespaceNoNewline(this.peek())) {
            this.advance();
        }
        if (this.atEnd() || !this.peek().equals("]") || this.pos + 1 >= this.length || !String.valueOf(this.source.charAt(this.pos + 1)).equals("]")) {
            this._clearState(Constants.PARSERSTATEFLAGS_PST_CONDEXPR);
            this._wordContext = Constants.WORD_CTX_NORMAL;
            throw new RuntimeException("Expected ]] to close conditional expression");
        }
        this.advance();
        this.advance();
        this._clearState(Constants.PARSERSTATEFLAGS_PST_CONDEXPR);
        this._wordContext = Constants.WORD_CTX_NORMAL;
        return new ConditionalExpr(body, this._collectRedirects(), "cond-expr");
    }

    public void _condSkipWhitespace() {
        while (!this.atEnd()) {
            if (ParableFunctions._isWhitespaceNoNewline(this.peek())) {
                this.advance();
            } else {
                if (this.peek().equals("\\") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("\n")) {
                    this.advance();
                    this.advance();
                } else {
                    if (this.peek().equals("\n")) {
                        this.advance();
                    } else {
                        break;
                    }
                }
            }
        }
    }

    public boolean _condAtEnd() {
        return this.atEnd() || this.peek().equals("]") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("]");
    }

    public Node _parseCondOr() {
        this._condSkipWhitespace();
        Node left = this._parseCondAnd();
        this._condSkipWhitespace();
        if (!this._condAtEnd() && this.peek().equals("|") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("|")) {
            this.advance();
            this.advance();
            Node right = this._parseCondOr();
            return new CondOr(left, right, "cond-or");
        }
        return left;
    }

    public Node _parseCondAnd() {
        this._condSkipWhitespace();
        Node left = this._parseCondTerm();
        this._condSkipWhitespace();
        if (!this._condAtEnd() && this.peek().equals("&") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("&")) {
            this.advance();
            this.advance();
            Node right = this._parseCondAnd();
            return new CondAnd(left, right, "cond-and");
        }
        return left;
    }

    public Node _parseCondTerm() {
        this._condSkipWhitespace();
        if (this._condAtEnd()) {
            throw new RuntimeException("Unexpected end of conditional expression");
        }
        Node operand = null;
        if (this.peek().equals("!")) {
            if (this.pos + 1 < this.length && !ParableFunctions._isWhitespaceNoNewline(String.valueOf(this.source.charAt(this.pos + 1)))) {
            } else {
                this.advance();
                operand = this._parseCondTerm();
                return new CondNot(operand, "cond-not");
            }
        }
        if (this.peek().equals("(")) {
            this.advance();
            Node inner = this._parseCondOr();
            this._condSkipWhitespace();
            if (this.atEnd() || !this.peek().equals(")")) {
                throw new RuntimeException("Expected ) in conditional expression");
            }
            this.advance();
            return new CondParen(inner, "cond-paren");
        }
        Word word1 = this._parseCondWord();
        if (word1 == null) {
            throw new RuntimeException("Expected word in conditional expression");
        }
        this._condSkipWhitespace();
        if (Constants.COND_UNARY_OPS.contains(word1.value)) {
            operand = this._parseCondWord();
            if (operand == null) {
                throw new RuntimeException("Expected operand after " + word1.value);
            }
            return new UnaryTest(word1.value, operand, "unary-test");
        }
        if (!this._condAtEnd() && !this.peek().equals("&") && !this.peek().equals("|") && !this.peek().equals(")")) {
            Word word2 = null;
            if (ParableFunctions._isRedirectChar(this.peek()) && !(this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("("))) {
                String op = this.advance();
                this._condSkipWhitespace();
                word2 = this._parseCondWord();
                if (word2 == null) {
                    throw new RuntimeException("Expected operand after " + op);
                }
                return new BinaryTest(op, word1, word2, "binary-test");
            }
            int savedPos = this.pos;
            Word opWord = this._parseCondWord();
            if (opWord != null && Constants.COND_BINARY_OPS.contains(opWord.value)) {
                this._condSkipWhitespace();
                if (opWord.value.equals("=~")) {
                    word2 = this._parseCondRegexWord();
                } else {
                    word2 = this._parseCondWord();
                }
                if (word2 == null) {
                    throw new RuntimeException("Expected operand after " + opWord.value);
                }
                return new BinaryTest(opWord.value, word1, word2, "binary-test");
            } else {
                this.pos = savedPos;
            }
        }
        return new UnaryTest("-n", word1, "unary-test");
    }

    public Word _parseCondWord() {
        this._condSkipWhitespace();
        if (this._condAtEnd()) {
            return null;
        }
        String c = this.peek();
        if (ParableFunctions._isParen(c)) {
            return null;
        }
        if (c.equals("&") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("&")) {
            return null;
        }
        if (c.equals("|") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("|")) {
            return null;
        }
        return this._parseWordInternal(Constants.WORD_CTX_COND, false, false);
    }

    public Word _parseCondRegexWord() {
        this._condSkipWhitespace();
        if (this._condAtEnd()) {
            return null;
        }
        this._setState(Constants.PARSERSTATEFLAGS_PST_REGEXP);
        Word result = this._parseWordInternal(Constants.WORD_CTX_REGEX, false, false);
        this._clearState(Constants.PARSERSTATEFLAGS_PST_REGEXP);
        this._wordContext = Constants.WORD_CTX_COND;
        return result;
    }

    public BraceGroup parseBraceGroup() {
        this.skipWhitespace();
        if (!this._lexConsumeWord("{")) {
            return null;
        }
        this.skipWhitespaceAndNewlines();
        Node body = this.parseList(true);
        if (body == null) {
            throw new RuntimeException("Expected command in brace group");
        }
        this.skipWhitespace();
        if (!this._lexConsumeWord("}")) {
            throw new RuntimeException("Expected } to close brace group");
        }
        return new BraceGroup(body, this._collectRedirects(), "brace-group");
    }

    public If parseIf() {
        this.skipWhitespace();
        if (!this._lexConsumeWord("if")) {
            return null;
        }
        Node condition = this.parseListUntil(new HashSet<>(Set.of("then")));
        if (condition == null) {
            throw new RuntimeException("Expected condition after 'if'");
        }
        this.skipWhitespaceAndNewlines();
        if (!this._lexConsumeWord("then")) {
            throw new RuntimeException("Expected 'then' after if condition");
        }
        Node thenBody = this.parseListUntil(new HashSet<>(Set.of("elif", "else", "fi")));
        if (thenBody == null) {
            throw new RuntimeException("Expected commands after 'then'");
        }
        this.skipWhitespaceAndNewlines();
        Node elseBody = null;
        if (this._lexIsAtReservedWord("elif")) {
            this._lexConsumeWord("elif");
            Node elifCondition = this.parseListUntil(new HashSet<>(Set.of("then")));
            if (elifCondition == null) {
                throw new RuntimeException("Expected condition after 'elif'");
            }
            this.skipWhitespaceAndNewlines();
            if (!this._lexConsumeWord("then")) {
                throw new RuntimeException("Expected 'then' after elif condition");
            }
            Node elifThenBody = this.parseListUntil(new HashSet<>(Set.of("elif", "else", "fi")));
            if (elifThenBody == null) {
                throw new RuntimeException("Expected commands after 'then'");
            }
            this.skipWhitespaceAndNewlines();
            Node innerElse = null;
            if (this._lexIsAtReservedWord("elif")) {
                innerElse = this._parseElifChain();
            } else {
                if (this._lexIsAtReservedWord("else")) {
                    this._lexConsumeWord("else");
                    innerElse = this.parseListUntil(new HashSet<>(Set.of("fi")));
                    if (innerElse == null) {
                        throw new RuntimeException("Expected commands after 'else'");
                    }
                }
            }
            elseBody = new If(elifCondition, elifThenBody, innerElse, new ArrayList<>(), "if");
        } else {
            if (this._lexIsAtReservedWord("else")) {
                this._lexConsumeWord("else");
                elseBody = this.parseListUntil(new HashSet<>(Set.of("fi")));
                if (elseBody == null) {
                    throw new RuntimeException("Expected commands after 'else'");
                }
            }
        }
        this.skipWhitespaceAndNewlines();
        if (!this._lexConsumeWord("fi")) {
            throw new RuntimeException("Expected 'fi' to close if statement");
        }
        return new If(condition, thenBody, elseBody, this._collectRedirects(), "if");
    }

    public If _parseElifChain() {
        this._lexConsumeWord("elif");
        Node condition = this.parseListUntil(new HashSet<>(Set.of("then")));
        if (condition == null) {
            throw new RuntimeException("Expected condition after 'elif'");
        }
        this.skipWhitespaceAndNewlines();
        if (!this._lexConsumeWord("then")) {
            throw new RuntimeException("Expected 'then' after elif condition");
        }
        Node thenBody = this.parseListUntil(new HashSet<>(Set.of("elif", "else", "fi")));
        if (thenBody == null) {
            throw new RuntimeException("Expected commands after 'then'");
        }
        this.skipWhitespaceAndNewlines();
        Node elseBody = null;
        if (this._lexIsAtReservedWord("elif")) {
            elseBody = this._parseElifChain();
        } else {
            if (this._lexIsAtReservedWord("else")) {
                this._lexConsumeWord("else");
                elseBody = this.parseListUntil(new HashSet<>(Set.of("fi")));
                if (elseBody == null) {
                    throw new RuntimeException("Expected commands after 'else'");
                }
            }
        }
        return new If(condition, thenBody, elseBody, new ArrayList<>(), "if");
    }

    public While parseWhile() {
        this.skipWhitespace();
        if (!this._lexConsumeWord("while")) {
            return null;
        }
        Node condition = this.parseListUntil(new HashSet<>(Set.of("do")));
        if (condition == null) {
            throw new RuntimeException("Expected condition after 'while'");
        }
        this.skipWhitespaceAndNewlines();
        if (!this._lexConsumeWord("do")) {
            throw new RuntimeException("Expected 'do' after while condition");
        }
        Node body = this.parseListUntil(new HashSet<>(Set.of("done")));
        if (body == null) {
            throw new RuntimeException("Expected commands after 'do'");
        }
        this.skipWhitespaceAndNewlines();
        if (!this._lexConsumeWord("done")) {
            throw new RuntimeException("Expected 'done' to close while loop");
        }
        return new While(condition, body, this._collectRedirects(), "while");
    }

    public Until parseUntil() {
        this.skipWhitespace();
        if (!this._lexConsumeWord("until")) {
            return null;
        }
        Node condition = this.parseListUntil(new HashSet<>(Set.of("do")));
        if (condition == null) {
            throw new RuntimeException("Expected condition after 'until'");
        }
        this.skipWhitespaceAndNewlines();
        if (!this._lexConsumeWord("do")) {
            throw new RuntimeException("Expected 'do' after until condition");
        }
        Node body = this.parseListUntil(new HashSet<>(Set.of("done")));
        if (body == null) {
            throw new RuntimeException("Expected commands after 'do'");
        }
        this.skipWhitespaceAndNewlines();
        if (!this._lexConsumeWord("done")) {
            throw new RuntimeException("Expected 'done' to close until loop");
        }
        return new Until(condition, body, this._collectRedirects(), "until");
    }

    public Node parseFor() {
        this.skipWhitespace();
        if (!this._lexConsumeWord("for")) {
            return null;
        }
        this.skipWhitespace();
        if (this.peek().equals("(") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("(")) {
            return this._parseForArith();
        }
        String varName = "";
        if (this.peek().equals("$")) {
            Word varWord = this.parseWord(false, false, false);
            if (varWord == null) {
                throw new RuntimeException("Expected variable name after 'for'");
            }
            varName = varWord.value;
        } else {
            varName = this.peekWord();
            if (varName.equals("")) {
                throw new RuntimeException("Expected variable name after 'for'");
            }
            this.consumeWord(varName);
        }
        this.skipWhitespace();
        if (this.peek().equals(";")) {
            this.advance();
        }
        this.skipWhitespaceAndNewlines();
        List<Word> words = null;
        if (this._lexIsAtReservedWord("in")) {
            this._lexConsumeWord("in");
            this.skipWhitespace();
            boolean sawDelimiter = ParableFunctions._isSemicolonOrNewline(this.peek());
            if (this.peek().equals(";")) {
                this.advance();
            }
            this.skipWhitespaceAndNewlines();
            words = new ArrayList<>();
            while (true) {
                this.skipWhitespace();
                if (this.atEnd()) {
                    break;
                }
                if (ParableFunctions._isSemicolonOrNewline(this.peek())) {
                    sawDelimiter = true;
                    if (this.peek().equals(";")) {
                        this.advance();
                    }
                    break;
                }
                if (this._lexIsAtReservedWord("do")) {
                    if (sawDelimiter) {
                        break;
                    }
                    throw new RuntimeException("Expected ';' or newline before 'do'");
                }
                Word word = this.parseWord(false, false, false);
                if (word == null) {
                    break;
                }
                words.add(word);
            }
        }
        this.skipWhitespaceAndNewlines();
        if (this.peek().equals("{")) {
            BraceGroup braceGroup = this.parseBraceGroup();
            if (braceGroup == null) {
                throw new RuntimeException("Expected brace group in for loop");
            }
            return new For(varName, words, braceGroup.body, this._collectRedirects(), "for");
        }
        if (!this._lexConsumeWord("do")) {
            throw new RuntimeException("Expected 'do' in for loop");
        }
        Node body = this.parseListUntil(new HashSet<>(Set.of("done")));
        if (body == null) {
            throw new RuntimeException("Expected commands after 'do'");
        }
        this.skipWhitespaceAndNewlines();
        if (!this._lexConsumeWord("done")) {
            throw new RuntimeException("Expected 'done' to close for loop");
        }
        return new For(varName, words, body, this._collectRedirects(), "for");
    }

    public ForArith _parseForArith() {
        this.advance();
        this.advance();
        List<String> parts = new ArrayList<>();
        List<String> current = new ArrayList<>();
        int parenDepth = 0;
        while (!this.atEnd()) {
            String ch = this.peek();
            if (ch.equals("(")) {
                parenDepth += 1;
                current.add(this.advance());
            } else {
                if (ch.equals(")")) {
                    if (parenDepth > 0) {
                        parenDepth -= 1;
                        current.add(this.advance());
                    } else {
                        if (this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals(")")) {
                            parts.add(String.join("", current).replaceFirst("^[" + " \t" + "]+", ""));
                            this.advance();
                            this.advance();
                            break;
                        } else {
                            current.add(this.advance());
                        }
                    }
                } else {
                    if (ch.equals(";") && parenDepth == 0) {
                        parts.add(String.join("", current).replaceFirst("^[" + " \t" + "]+", ""));
                        current = new ArrayList<>();
                        this.advance();
                    } else {
                        current.add(this.advance());
                    }
                }
            }
        }
        if (parts.size() != 3) {
            throw new RuntimeException("Expected three expressions in for ((;;))");
        }
        String init = parts.get(0);
        String cond = parts.get(1);
        String incr = parts.get(2);
        this.skipWhitespace();
        if (!this.atEnd() && this.peek().equals(";")) {
            this.advance();
        }
        this.skipWhitespaceAndNewlines();
        Node body = this._parseLoopBody("for loop");
        return new ForArith(init, cond, incr, body, this._collectRedirects(), "for-arith");
    }

    public Select parseSelect() {
        this.skipWhitespace();
        if (!this._lexConsumeWord("select")) {
            return null;
        }
        this.skipWhitespace();
        String varName = this.peekWord();
        if (varName.equals("")) {
            throw new RuntimeException("Expected variable name after 'select'");
        }
        this.consumeWord(varName);
        this.skipWhitespace();
        if (this.peek().equals(";")) {
            this.advance();
        }
        this.skipWhitespaceAndNewlines();
        List<Word> words = null;
        if (this._lexIsAtReservedWord("in")) {
            this._lexConsumeWord("in");
            this.skipWhitespaceAndNewlines();
            words = new ArrayList<>();
            while (true) {
                this.skipWhitespace();
                if (this.atEnd()) {
                    break;
                }
                if (ParableFunctions._isSemicolonNewlineBrace(this.peek())) {
                    if (this.peek().equals(";")) {
                        this.advance();
                    }
                    break;
                }
                if (this._lexIsAtReservedWord("do")) {
                    break;
                }
                Word word = this.parseWord(false, false, false);
                if (word == null) {
                    break;
                }
                words.add(word);
            }
        }
        this.skipWhitespaceAndNewlines();
        Node body = this._parseLoopBody("select");
        return new Select(varName, words, body, this._collectRedirects(), "select");
    }

    public String _consumeCaseTerminator() {
        String term = this._lexPeekCaseTerminator();
        if (!term.equals("")) {
            this._lexNextToken();
            return term;
        }
        return ";;";
    }

    public Case parseCase() {
        if (!this.consumeWord("case")) {
            return null;
        }
        this._setState(Constants.PARSERSTATEFLAGS_PST_CASESTMT);
        this.skipWhitespace();
        Word word = this.parseWord(false, false, false);
        if (word == null) {
            throw new RuntimeException("Expected word after 'case'");
        }
        this.skipWhitespaceAndNewlines();
        if (!this._lexConsumeWord("in")) {
            throw new RuntimeException("Expected 'in' after case word");
        }
        this.skipWhitespaceAndNewlines();
        List<Node> patterns = new ArrayList<>();
        this._setState(Constants.PARSERSTATEFLAGS_PST_CASEPAT);
        while (true) {
            this.skipWhitespaceAndNewlines();
            if (this._lexIsAtReservedWord("esac")) {
                int saved = this.pos;
                this.skipWhitespace();
                while (!this.atEnd() && !ParableFunctions._isMetachar(this.peek()) && !ParableFunctions._isQuote(this.peek())) {
                    this.advance();
                }
                this.skipWhitespace();
                boolean isPattern = false;
                if (!this.atEnd() && this.peek().equals(")")) {
                    if (this._eofToken.equals(")")) {
                        isPattern = false;
                    } else {
                        this.advance();
                        this.skipWhitespace();
                        if (!this.atEnd()) {
                            String nextCh = this.peek();
                            if (nextCh.equals(";")) {
                                isPattern = true;
                            } else {
                                if (!ParableFunctions._isNewlineOrRightParen(nextCh)) {
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
            if (!this.atEnd() && this.peek().equals("(")) {
                this.advance();
                this.skipWhitespaceAndNewlines();
            }
            List<String> patternChars = new ArrayList<>();
            int extglobDepth = 0;
            while (!this.atEnd()) {
                String ch = this.peek();
                if (ch.equals(")")) {
                    if (extglobDepth > 0) {
                        patternChars.add(this.advance());
                        extglobDepth -= 1;
                    } else {
                        this.advance();
                        break;
                    }
                } else {
                    if (ch.equals("\\")) {
                        if (this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("\n")) {
                            this.advance();
                            this.advance();
                        } else {
                            patternChars.add(this.advance());
                            if (!this.atEnd()) {
                                patternChars.add(this.advance());
                            }
                        }
                    } else {
                        if (ParableFunctions._isExpansionStart(this.source, this.pos, "$(")) {
                            patternChars.add(this.advance());
                            patternChars.add(this.advance());
                            if (!this.atEnd() && this.peek().equals("(")) {
                                patternChars.add(this.advance());
                                int parenDepth = 2;
                                while (!this.atEnd() && parenDepth > 0) {
                                    String c = this.peek();
                                    if (c.equals("(")) {
                                        parenDepth += 1;
                                    } else {
                                        if (c.equals(")")) {
                                            parenDepth -= 1;
                                        }
                                    }
                                    patternChars.add(this.advance());
                                }
                            } else {
                                extglobDepth += 1;
                            }
                        } else {
                            if (ch.equals("(") && extglobDepth > 0) {
                                patternChars.add(this.advance());
                                extglobDepth += 1;
                            } else {
                                if (this._extglob && ParableFunctions._isExtglobPrefix(ch) && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("(")) {
                                    patternChars.add(this.advance());
                                    patternChars.add(this.advance());
                                    extglobDepth += 1;
                                } else {
                                    if (ch.equals("[")) {
                                        boolean isCharClass = false;
                                        int scanPos = this.pos + 1;
                                        int scanDepth = 0;
                                        boolean hasFirstBracketLiteral = false;
                                        if (scanPos < this.length && ParableFunctions._isCaretOrBang(String.valueOf(this.source.charAt(scanPos)))) {
                                            scanPos += 1;
                                        }
                                        if (scanPos < this.length && String.valueOf(this.source.charAt(scanPos)).equals("]")) {
                                            if (this.source.indexOf("]", scanPos + 1) != -1) {
                                                scanPos += 1;
                                                hasFirstBracketLiteral = true;
                                            }
                                        }
                                        while (scanPos < this.length) {
                                            String sc = String.valueOf(this.source.charAt(scanPos));
                                            if (sc.equals("]") && scanDepth == 0) {
                                                isCharClass = true;
                                                break;
                                            } else {
                                                if (sc.equals("[")) {
                                                    scanDepth += 1;
                                                } else {
                                                    if (sc.equals(")") && scanDepth == 0) {
                                                        break;
                                                    } else {
                                                        if (sc.equals("|") && scanDepth == 0) {
                                                            break;
                                                        }
                                                    }
                                                }
                                            }
                                            scanPos += 1;
                                        }
                                        if (isCharClass) {
                                            patternChars.add(this.advance());
                                            if (!this.atEnd() && ParableFunctions._isCaretOrBang(this.peek())) {
                                                patternChars.add(this.advance());
                                            }
                                            if (hasFirstBracketLiteral && !this.atEnd() && this.peek().equals("]")) {
                                                patternChars.add(this.advance());
                                            }
                                            while (!this.atEnd() && !this.peek().equals("]")) {
                                                patternChars.add(this.advance());
                                            }
                                            if (!this.atEnd()) {
                                                patternChars.add(this.advance());
                                            }
                                        } else {
                                            patternChars.add(this.advance());
                                        }
                                    } else {
                                        if (ch.equals("'")) {
                                            patternChars.add(this.advance());
                                            while (!this.atEnd() && !this.peek().equals("'")) {
                                                patternChars.add(this.advance());
                                            }
                                            if (!this.atEnd()) {
                                                patternChars.add(this.advance());
                                            }
                                        } else {
                                            if (ch.equals("\"")) {
                                                patternChars.add(this.advance());
                                                while (!this.atEnd() && !this.peek().equals("\"")) {
                                                    if (this.peek().equals("\\") && this.pos + 1 < this.length) {
                                                        patternChars.add(this.advance());
                                                    }
                                                    patternChars.add(this.advance());
                                                }
                                                if (!this.atEnd()) {
                                                    patternChars.add(this.advance());
                                                }
                                            } else {
                                                if (ParableFunctions._isWhitespace(ch)) {
                                                    if (extglobDepth > 0) {
                                                        patternChars.add(this.advance());
                                                    } else {
                                                        this.advance();
                                                    }
                                                } else {
                                                    patternChars.add(this.advance());
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
            String pattern = String.join("", patternChars);
            if (!(!pattern.equals(""))) {
                throw new RuntimeException("Expected pattern in case statement");
            }
            this.skipWhitespace();
            Node body = null;
            boolean isEmptyBody = !this._lexPeekCaseTerminator().equals("");
            if (!isEmptyBody) {
                this.skipWhitespaceAndNewlines();
                if (!this.atEnd() && !this._lexIsAtReservedWord("esac")) {
                    boolean isAtTerminator = !this._lexPeekCaseTerminator().equals("");
                    if (!isAtTerminator) {
                        body = this.parseListUntil(new HashSet<>(Set.of("esac")));
                        this.skipWhitespace();
                    }
                }
            }
            String terminator = this._consumeCaseTerminator();
            this.skipWhitespaceAndNewlines();
            patterns.add(new CasePattern(pattern, body, terminator, "pattern"));
        }
        this._clearState(Constants.PARSERSTATEFLAGS_PST_CASEPAT);
        this.skipWhitespaceAndNewlines();
        if (!this._lexConsumeWord("esac")) {
            this._clearState(Constants.PARSERSTATEFLAGS_PST_CASESTMT);
            throw new RuntimeException("Expected 'esac' to close case statement");
        }
        this._clearState(Constants.PARSERSTATEFLAGS_PST_CASESTMT);
        return new Case(word, patterns, this._collectRedirects(), "case");
    }

    public Coproc parseCoproc() {
        this.skipWhitespace();
        if (!this._lexConsumeWord("coproc")) {
            return null;
        }
        this.skipWhitespace();
        String name = "";
        String ch = "";
        if (!this.atEnd()) {
            ch = this.peek();
        }
        Node body = null;
        if (ch.equals("{")) {
            body = this.parseBraceGroup();
            if (body != null) {
                return new Coproc(body, name, "coproc");
            }
        }
        if (ch.equals("(")) {
            if (this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("(")) {
                body = this.parseArithmeticCommand();
                if (body != null) {
                    return new Coproc(body, name, "coproc");
                }
            }
            body = this.parseSubshell();
            if (body != null) {
                return new Coproc(body, name, "coproc");
            }
        }
        String nextWord = this._lexPeekReservedWord();
        if (!nextWord.equals("") && Constants.COMPOUND_KEYWORDS.contains(nextWord)) {
            body = this.parseCompoundCommand();
            if (body != null) {
                return new Coproc(body, name, "coproc");
            }
        }
        int wordStart = this.pos;
        String potentialName = this.peekWord();
        if (!potentialName.equals("")) {
            while (!this.atEnd() && !ParableFunctions._isMetachar(this.peek()) && !ParableFunctions._isQuote(this.peek())) {
                this.advance();
            }
            this.skipWhitespace();
            ch = "";
            if (!this.atEnd()) {
                ch = this.peek();
            }
            nextWord = this._lexPeekReservedWord();
            if (ParableFunctions._isValidIdentifier(potentialName)) {
                if (ch.equals("{")) {
                    name = potentialName;
                    body = this.parseBraceGroup();
                    if (body != null) {
                        return new Coproc(body, name, "coproc");
                    }
                } else {
                    if (ch.equals("(")) {
                        name = potentialName;
                        if (this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("(")) {
                            body = this.parseArithmeticCommand();
                        } else {
                            body = this.parseSubshell();
                        }
                        if (body != null) {
                            return new Coproc(body, name, "coproc");
                        }
                    } else {
                        if (!nextWord.equals("") && Constants.COMPOUND_KEYWORDS.contains(nextWord)) {
                            name = potentialName;
                            body = this.parseCompoundCommand();
                            if (body != null) {
                                return new Coproc(body, name, "coproc");
                            }
                        }
                    }
                }
            }
            this.pos = wordStart;
        }
        body = this.parseCommand();
        if (body != null) {
            return new Coproc(body, name, "coproc");
        }
        throw new RuntimeException("Expected command after coproc");
    }

    public Function parseFunction() {
        this.skipWhitespace();
        if (this.atEnd()) {
            return null;
        }
        int savedPos = this.pos;
        String name = "";
        Node body = null;
        if (this._lexIsAtReservedWord("function")) {
            this._lexConsumeWord("function");
            this.skipWhitespace();
            name = this.peekWord();
            if (name.equals("")) {
                this.pos = savedPos;
                return null;
            }
            this.consumeWord(name);
            this.skipWhitespace();
            if (!this.atEnd() && this.peek().equals("(")) {
                if (this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals(")")) {
                    this.advance();
                    this.advance();
                }
            }
            this.skipWhitespaceAndNewlines();
            body = this._parseCompoundCommand();
            if (body == null) {
                throw new RuntimeException("Expected function body");
            }
            return new Function(name, body, "function");
        }
        name = this.peekWord();
        if (name.equals("") || Constants.RESERVED_WORDS.contains(name)) {
            return null;
        }
        if (ParableFunctions._looksLikeAssignment(name)) {
            return null;
        }
        this.skipWhitespace();
        int nameStart = this.pos;
        while (!this.atEnd() && !ParableFunctions._isMetachar(this.peek()) && !ParableFunctions._isQuote(this.peek()) && !ParableFunctions._isParen(this.peek())) {
            this.advance();
        }
        name = ParableFunctions._substring(this.source, nameStart, this.pos);
        if (!(!name.equals(""))) {
            this.pos = savedPos;
            return null;
        }
        int braceDepth = 0;
        int i = 0;
        while (i < name.length()) {
            if (ParableFunctions._isExpansionStart(name, i, "${")) {
                braceDepth += 1;
                i += 2;
                continue;
            }
            if (String.valueOf(name.charAt(i)).equals("}")) {
                braceDepth -= 1;
            }
            i += 1;
        }
        if (braceDepth > 0) {
            this.pos = savedPos;
            return null;
        }
        int posAfterName = this.pos;
        this.skipWhitespace();
        boolean hasWhitespace = this.pos > posAfterName;
        if (!hasWhitespace && !name.equals("") && "*?@+!$".indexOf(String.valueOf(name.charAt(name.length() - 1))) != -1) {
            this.pos = savedPos;
            return null;
        }
        if (this.atEnd() || !this.peek().equals("(")) {
            this.pos = savedPos;
            return null;
        }
        this.advance();
        this.skipWhitespace();
        if (this.atEnd() || !this.peek().equals(")")) {
            this.pos = savedPos;
            return null;
        }
        this.advance();
        this.skipWhitespaceAndNewlines();
        body = this._parseCompoundCommand();
        if (body == null) {
            throw new RuntimeException("Expected function body");
        }
        return new Function(name, body, "function");
    }

    public Node _parseCompoundCommand() {
        Node result = this.parseBraceGroup();
        if (result != null) {
            return result;
        }
        if (!this.atEnd() && this.peek().equals("(") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("(")) {
            result = this.parseArithmeticCommand();
            if (result != null) {
                return result;
            }
        }
        result = this.parseSubshell();
        if (result != null) {
            return result;
        }
        result = this.parseConditionalExpr();
        if (result != null) {
            return result;
        }
        result = this.parseIf();
        if (result != null) {
            return result;
        }
        result = this.parseWhile();
        if (result != null) {
            return result;
        }
        result = this.parseUntil();
        if (result != null) {
            return result;
        }
        result = this.parseFor();
        if (result != null) {
            return result;
        }
        result = this.parseCase();
        if (result != null) {
            return result;
        }
        result = this.parseSelect();
        if (result != null) {
            return result;
        }
        return null;
    }

    public boolean _atListUntilTerminator(Set<String> stopWords) {
        if (this.atEnd()) {
            return true;
        }
        if (this.peek().equals(")")) {
            return true;
        }
        if (this.peek().equals("}")) {
            int nextPos = this.pos + 1;
            if (nextPos >= this.length || ParableFunctions._isWordEndContext(String.valueOf(this.source.charAt(nextPos)))) {
                return true;
            }
        }
        String reserved = this._lexPeekReservedWord();
        if (!reserved.equals("") && stopWords.contains(reserved)) {
            return true;
        }
        if (!this._lexPeekCaseTerminator().equals("")) {
            return true;
        }
        return false;
    }

    public Node parseListUntil(Set<String> stopWords) {
        this.skipWhitespaceAndNewlines();
        String reserved = this._lexPeekReservedWord();
        if (!reserved.equals("") && stopWords.contains(reserved)) {
            return null;
        }
        Node pipeline = this.parsePipeline();
        if (pipeline == null) {
            return null;
        }
        List<Node> parts = new ArrayList<>(List.of(pipeline));
        while (true) {
            this.skipWhitespace();
            String op = this.parseListOperator();
            if (op.equals("")) {
                if (!this.atEnd() && this.peek().equals("\n")) {
                    this.advance();
                    this._gatherHeredocBodies();
                    if (this._cmdsubHeredocEnd != -1 && this._cmdsubHeredocEnd > this.pos) {
                        this.pos = this._cmdsubHeredocEnd;
                        this._cmdsubHeredocEnd = -1;
                    }
                    this.skipWhitespaceAndNewlines();
                    if (this._atListUntilTerminator(stopWords)) {
                        break;
                    }
                    String nextOp = this._peekListOperator();
                    if (nextOp.equals("&") || nextOp.equals(";")) {
                        break;
                    }
                    op = "\n";
                } else {
                    break;
                }
            }
            if (op.equals("")) {
                break;
            }
            if (op.equals(";")) {
                this.skipWhitespaceAndNewlines();
                if (this._atListUntilTerminator(stopWords)) {
                    break;
                }
                parts.add(new Operator(op, "operator"));
            } else {
                if (op.equals("&")) {
                    parts.add(new Operator(op, "operator"));
                    this.skipWhitespaceAndNewlines();
                    if (this._atListUntilTerminator(stopWords)) {
                        break;
                    }
                } else {
                    if (op.equals("&&") || op.equals("||")) {
                        parts.add(new Operator(op, "operator"));
                        this.skipWhitespaceAndNewlines();
                    } else {
                        parts.add(new Operator(op, "operator"));
                    }
                }
            }
            if (this._atListUntilTerminator(stopWords)) {
                break;
            }
            pipeline = this.parsePipeline();
            if (pipeline == null) {
                throw new RuntimeException("Expected command after " + op);
            }
            parts.add(pipeline);
        }
        if (parts.size() == 1) {
            return parts.get(0);
        }
        return new ListNode(parts, "list");
    }

    public Node parseCompoundCommand() {
        this.skipWhitespace();
        if (this.atEnd()) {
            return null;
        }
        String ch = this.peek();
        Node result = null;
        if (ch.equals("(") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("(")) {
            result = this.parseArithmeticCommand();
            if (result != null) {
                return result;
            }
        }
        if (ch.equals("(")) {
            return this.parseSubshell();
        }
        if (ch.equals("{")) {
            result = this.parseBraceGroup();
            if (result != null) {
                return result;
            }
        }
        if (ch.equals("[") && this.pos + 1 < this.length && String.valueOf(this.source.charAt(this.pos + 1)).equals("[")) {
            result = this.parseConditionalExpr();
            if (result != null) {
                return result;
            }
        }
        String reserved = this._lexPeekReservedWord();
        if (reserved.equals("") && this._inProcessSub) {
            String word = this.peekWord();
            if (!word.equals("") && word.length() > 1 && String.valueOf(word.charAt(0)).equals("}")) {
                String keywordWord = word.substring(1);
                if (Constants.RESERVED_WORDS.contains(keywordWord) || keywordWord.equals("{") || keywordWord.equals("}") || keywordWord.equals("[[") || keywordWord.equals("]]") || keywordWord.equals("!") || keywordWord.equals("time")) {
                    reserved = keywordWord;
                }
            }
        }
        if (reserved.equals("fi") || reserved.equals("then") || reserved.equals("elif") || reserved.equals("else") || reserved.equals("done") || reserved.equals("esac") || reserved.equals("do") || reserved.equals("in")) {
            throw new RuntimeException(String.format("Unexpected reserved word '%s'", reserved));
        }
        if (reserved.equals("if")) {
            return this.parseIf();
        }
        if (reserved.equals("while")) {
            return this.parseWhile();
        }
        if (reserved.equals("until")) {
            return this.parseUntil();
        }
        if (reserved.equals("for")) {
            return this.parseFor();
        }
        if (reserved.equals("select")) {
            return this.parseSelect();
        }
        if (reserved.equals("case")) {
            return this.parseCase();
        }
        if (reserved.equals("function")) {
            return this.parseFunction();
        }
        if (reserved.equals("coproc")) {
            return this.parseCoproc();
        }
        Function func = this.parseFunction();
        if (func != null) {
            return func;
        }
        return this.parseCommand();
    }

    public Node parsePipeline() {
        this.skipWhitespace();
        String prefixOrder = "";
        boolean timePosix = false;
        if (this._lexIsAtReservedWord("time")) {
            this._lexConsumeWord("time");
            prefixOrder = "time";
            this.skipWhitespace();
            int saved = 0;
            if (!this.atEnd() && this.peek().equals("-")) {
                saved = this.pos;
                this.advance();
                if (!this.atEnd() && this.peek().equals("p")) {
                    this.advance();
                    if (this.atEnd() || ParableFunctions._isMetachar(this.peek())) {
                        timePosix = true;
                    } else {
                        this.pos = saved;
                    }
                } else {
                    this.pos = saved;
                }
            }
            this.skipWhitespace();
            if (!this.atEnd() && ParableFunctions._startsWithAt(this.source, this.pos, "--")) {
                if (this.pos + 2 >= this.length || ParableFunctions._isWhitespace(String.valueOf(this.source.charAt(this.pos + 2)))) {
                    this.advance();
                    this.advance();
                    timePosix = true;
                    this.skipWhitespace();
                }
            }
            while (this._lexIsAtReservedWord("time")) {
                this._lexConsumeWord("time");
                this.skipWhitespace();
                if (!this.atEnd() && this.peek().equals("-")) {
                    saved = this.pos;
                    this.advance();
                    if (!this.atEnd() && this.peek().equals("p")) {
                        this.advance();
                        if (this.atEnd() || ParableFunctions._isMetachar(this.peek())) {
                            timePosix = true;
                        } else {
                            this.pos = saved;
                        }
                    } else {
                        this.pos = saved;
                    }
                }
            }
            this.skipWhitespace();
            if (!this.atEnd() && this.peek().equals("!")) {
                if (this.pos + 1 >= this.length || ParableFunctions._isNegationBoundary(String.valueOf(this.source.charAt(this.pos + 1))) && !this._isBangFollowedByProcsub()) {
                    this.advance();
                    prefixOrder = "time_negation";
                    this.skipWhitespace();
                }
            }
        } else {
            if (!this.atEnd() && this.peek().equals("!")) {
                if (this.pos + 1 >= this.length || ParableFunctions._isNegationBoundary(String.valueOf(this.source.charAt(this.pos + 1))) && !this._isBangFollowedByProcsub()) {
                    this.advance();
                    this.skipWhitespace();
                    Node inner = this.parsePipeline();
                    if (inner != null && inner.getKind() == "negation") {
                        if (((Negation) inner).pipeline != null) {
                            return ((Negation) inner).pipeline;
                        } else {
                            return new Command(new ArrayList<>(), new ArrayList<>(), "command");
                        }
                    }
                    return new Negation(inner, "negation");
                }
            }
        }
        Node result = this._parseSimplePipeline();
        if (prefixOrder.equals("time")) {
            result = new Time(result, timePosix, "time");
        } else {
            if (prefixOrder.equals("negation")) {
                result = new Negation(result, "negation");
            } else {
                if (prefixOrder.equals("time_negation")) {
                    result = new Time(result, timePosix, "time");
                    result = new Negation(result, "negation");
                } else {
                    if (prefixOrder.equals("negation_time")) {
                        result = new Time(result, timePosix, "time");
                        result = new Negation(result, "negation");
                    } else {
                        if (result == null) {
                            return null;
                        }
                    }
                }
            }
        }
        return result;
    }

    public Node _parseSimplePipeline() {
        Node cmd = this.parseCompoundCommand();
        if (cmd == null) {
            return null;
        }
        List<Node> commands = new ArrayList<>(List.of(cmd));
        while (true) {
            this.skipWhitespace();
            Tuple8 _tuple32 = this._lexPeekOperator();
            int tokenType = _tuple32.f0();
            String value = _tuple32.f1();
            if (tokenType == 0) {
                break;
            }
            if (tokenType != Constants.TOKENTYPE_PIPE && tokenType != Constants.TOKENTYPE_PIPE_AMP) {
                break;
            }
            this._lexNextToken();
            boolean isPipeBoth = tokenType == Constants.TOKENTYPE_PIPE_AMP;
            this.skipWhitespaceAndNewlines();
            if (isPipeBoth) {
                commands.add(new PipeBoth("pipe-both"));
            }
            cmd = this.parseCompoundCommand();
            if (cmd == null) {
                throw new RuntimeException("Expected command after |");
            }
            commands.add(cmd);
        }
        if (commands.size() == 1) {
            return commands.get(0);
        }
        return new Pipeline(commands, "pipeline");
    }

    public String parseListOperator() {
        this.skipWhitespace();
        Tuple8 _tuple33 = this._lexPeekOperator();
        int tokenType = _tuple33.f0();
        String _ = _tuple33.f1();
        if (tokenType == 0) {
            return "";
        }
        if (tokenType == Constants.TOKENTYPE_AND_AND) {
            this._lexNextToken();
            return "&&";
        }
        if (tokenType == Constants.TOKENTYPE_OR_OR) {
            this._lexNextToken();
            return "||";
        }
        if (tokenType == Constants.TOKENTYPE_SEMI) {
            this._lexNextToken();
            return ";";
        }
        if (tokenType == Constants.TOKENTYPE_AMP) {
            this._lexNextToken();
            return "&";
        }
        return "";
    }

    public String _peekListOperator() {
        int savedPos = this.pos;
        String op = this.parseListOperator();
        this.pos = savedPos;
        return op;
    }

    public Node parseList(boolean newlineAsSeparator) {
        if (newlineAsSeparator) {
            this.skipWhitespaceAndNewlines();
        } else {
            this.skipWhitespace();
        }
        Node pipeline = this.parsePipeline();
        if (pipeline == null) {
            return null;
        }
        List<Node> parts = new ArrayList<>(List.of(pipeline));
        if (this._inState(Constants.PARSERSTATEFLAGS_PST_EOFTOKEN) && this._atEofToken()) {
            return (parts.size() == 1 ? parts.get(0) : new ListNode(parts, "list"));
        }
        while (true) {
            this.skipWhitespace();
            String op = this.parseListOperator();
            if (op.equals("")) {
                if (!this.atEnd() && this.peek().equals("\n")) {
                    if (!newlineAsSeparator) {
                        break;
                    }
                    this.advance();
                    this._gatherHeredocBodies();
                    if (this._cmdsubHeredocEnd != -1 && this._cmdsubHeredocEnd > this.pos) {
                        this.pos = this._cmdsubHeredocEnd;
                        this._cmdsubHeredocEnd = -1;
                    }
                    this.skipWhitespaceAndNewlines();
                    if (this.atEnd() || this._atListTerminatingBracket()) {
                        break;
                    }
                    String nextOp = this._peekListOperator();
                    if (nextOp.equals("&") || nextOp.equals(";")) {
                        break;
                    }
                    op = "\n";
                } else {
                    break;
                }
            }
            if (op.equals("")) {
                break;
            }
            parts.add(new Operator(op, "operator"));
            if (op.equals("&&") || op.equals("||")) {
                this.skipWhitespaceAndNewlines();
            } else {
                if (op.equals("&")) {
                    this.skipWhitespace();
                    if (this.atEnd() || this._atListTerminatingBracket()) {
                        break;
                    }
                    if (this.peek().equals("\n")) {
                        if (newlineAsSeparator) {
                            this.skipWhitespaceAndNewlines();
                            if (this.atEnd() || this._atListTerminatingBracket()) {
                                break;
                            }
                        } else {
                            break;
                        }
                    }
                } else {
                    if (op.equals(";")) {
                        this.skipWhitespace();
                        if (this.atEnd() || this._atListTerminatingBracket()) {
                            break;
                        }
                        if (this.peek().equals("\n")) {
                            if (newlineAsSeparator) {
                                this.skipWhitespaceAndNewlines();
                                if (this.atEnd() || this._atListTerminatingBracket()) {
                                    break;
                                }
                            } else {
                                break;
                            }
                        }
                    }
                }
            }
            pipeline = this.parsePipeline();
            if (pipeline == null) {
                throw new RuntimeException("Expected command after " + op);
            }
            parts.add(pipeline);
            if (this._inState(Constants.PARSERSTATEFLAGS_PST_EOFTOKEN) && this._atEofToken()) {
                break;
            }
        }
        if (parts.size() == 1) {
            return parts.get(0);
        }
        return new ListNode(parts, "list");
    }

    public Node parseComment() {
        if (this.atEnd() || !this.peek().equals("#")) {
            return null;
        }
        int start = this.pos;
        while (!this.atEnd() && !this.peek().equals("\n")) {
            this.advance();
        }
        String text = ParableFunctions._substring(this.source, start, this.pos);
        return new Comment(text, "comment");
    }

    public List<Node> parse() {
        String source = this.source.trim();
        if (!(!source.equals(""))) {
            return new ArrayList<>(List.of(new Empty("empty")));
        }
        List<Node> results = new ArrayList<>();
        while (true) {
            this.skipWhitespace();
            while (!this.atEnd() && this.peek().equals("\n")) {
                this.advance();
            }
            if (this.atEnd()) {
                break;
            }
            Node comment = this.parseComment();
            if ((comment == null)) {
                break;
            }
        }
        while (!this.atEnd()) {
            Node result = this.parseList(false);
            if (result != null) {
                results.add(result);
            }
            this.skipWhitespace();
            boolean foundNewline = false;
            while (!this.atEnd() && this.peek().equals("\n")) {
                foundNewline = true;
                this.advance();
                this._gatherHeredocBodies();
                if (this._cmdsubHeredocEnd != -1 && this._cmdsubHeredocEnd > this.pos) {
                    this.pos = this._cmdsubHeredocEnd;
                    this._cmdsubHeredocEnd = -1;
                }
                this.skipWhitespace();
            }
            if (!foundNewline && !this.atEnd()) {
                throw new RuntimeException("Syntax error");
            }
        }
        if (!(!results.isEmpty())) {
            return new ArrayList<>(List.of(new Empty("empty")));
        }
        if (this._sawNewlineInSingleQuote && !this.source.equals("") && String.valueOf(this.source.charAt(this.source.length() - 1)).equals("\\") && !(this.source.length() >= 3 && this.source.substring(this.source.length() - 3, this.source.length() - 1).equals("\\\n"))) {
            if (!this._lastWordOnOwnLine(results)) {
                this._stripTrailingBackslashFromLastWord(results);
            }
        }
        return results;
    }

    public boolean _lastWordOnOwnLine(List<Node> nodes) {
        return nodes.size() >= 2;
    }

    public void _stripTrailingBackslashFromLastWord(List<Node> nodes) {
        if (!(!nodes.isEmpty())) {
            return;
        }
        Node lastNode = nodes.get(nodes.size() - 1);
        Word lastWord = this._findLastWord(lastNode);
        if (lastWord != null && lastWord.value.endsWith("\\")) {
            lastWord.value = ParableFunctions._substring(lastWord.value, 0, lastWord.value.length() - 1);
            if (!(!lastWord.value.equals("")) && (lastNode instanceof Command) && !((Command) lastNode).words.isEmpty()) {
                ((Command) lastNode).words.remove(((Command) lastNode).words.size() - 1);
            }
        }
    }

    public Word _findLastWord(Node node) {
        if (node instanceof Word nodeWord) {
            return nodeWord;
        }
        if (node instanceof Command nodeCommand) {
            if (!nodeCommand.words.isEmpty()) {
                Word lastWord = nodeCommand.words.get(nodeCommand.words.size() - 1);
                if (lastWord.value.endsWith("\\")) {
                    return lastWord;
                }
            }
            if (!nodeCommand.redirects.isEmpty()) {
                Node lastRedirect = nodeCommand.redirects.get(nodeCommand.redirects.size() - 1);
                if (lastRedirect instanceof Redirect lastRedirectRedirect) {
                    return lastRedirectRedirect.target;
                }
            }
            if (!nodeCommand.words.isEmpty()) {
                return nodeCommand.words.get(nodeCommand.words.size() - 1);
            }
        }
        if (node instanceof Pipeline nodePipeline) {
            if (!nodePipeline.commands.isEmpty()) {
                return this._findLastWord(nodePipeline.commands.get(nodePipeline.commands.size() - 1));
            }
        }
        if (node instanceof ListNode nodeList) {
            if (!nodeList.parts.isEmpty()) {
                return this._findLastWord(nodeList.parts.get(nodeList.parts.size() - 1));
            }
        }
        return null;
    }
}

final class ParableFunctions {
    private ParableFunctions() {}

    static boolean _isHexDigit(String c) {
        return (c.compareTo("0") >= 0) && (c.compareTo("9") <= 0) || (c.compareTo("a") >= 0) && (c.compareTo("f") <= 0) || (c.compareTo("A") >= 0) && (c.compareTo("F") <= 0);
    }

    static boolean _isOctalDigit(String c) {
        return (c.compareTo("0") >= 0) && (c.compareTo("7") <= 0);
    }

    static int _getAnsiEscape(String c) {
        return Constants.ANSI_C_ESCAPES.getOrDefault(c, -1);
    }

    static boolean _isWhitespace(String c) {
        return c.equals(" ") || c.equals("\t") || c.equals("\n");
    }

    static List<Byte> _stringToBytes(String s) {
        return new ArrayList<>(ParableFunctions._stringToBytes(s));
    }

    static boolean _isWhitespaceNoNewline(String c) {
        return c.equals(" ") || c.equals("\t");
    }

    static String _substring(String s, int start, int end) {
        return s.substring(start, end);
    }

    static boolean _startsWithAt(String s, int pos, String prefix) {
        return s.startsWith(prefix, pos);
    }

    static int _countConsecutiveDollarsBefore(String s, int pos) {
        int count = 0;
        int k = pos - 1;
        while (k >= 0 && String.valueOf(s.charAt(k)).equals("$")) {
            int bsCount = 0;
            int j = k - 1;
            while (j >= 0 && String.valueOf(s.charAt(j)).equals("\\")) {
                bsCount += 1;
                j -= 1;
            }
            if (bsCount % 2 == 1) {
                break;
            }
            count += 1;
            k -= 1;
        }
        return count;
    }

    static boolean _isExpansionStart(String s, int pos, String delimiter) {
        if (!ParableFunctions._startsWithAt(s, pos, delimiter)) {
            return false;
        }
        return ParableFunctions._countConsecutiveDollarsBefore(s, pos) % 2 == 0;
    }

    static List<Node> _sublist(List<Node> lst, int start, int end) {
        return new ArrayList<>(lst.subList(start, end));
    }

    static String _repeatStr(String s, int n) {
        List<String> result = new ArrayList<>();
        int i = 0;
        while (i < n) {
            result.add(s);
            i += 1;
        }
        return String.join("", result);
    }

    static String _stripLineContinuationsCommentAware(String text) {
        List<String> result = new ArrayList<>();
        int i = 0;
        boolean inComment = false;
        QuoteState quote = ParableFunctions.newQuoteState();
        while (i < text.length()) {
            String c = String.valueOf(text.charAt(i));
            if (c.equals("\\") && i + 1 < text.length() && String.valueOf(text.charAt(i + 1)).equals("\n")) {
                int numPrecedingBackslashes = 0;
                int j = i - 1;
                while (j >= 0 && String.valueOf(text.charAt(j)).equals("\\")) {
                    numPrecedingBackslashes += 1;
                    j -= 1;
                }
                if (numPrecedingBackslashes % 2 == 0) {
                    if (inComment) {
                        result.add("\n");
                    }
                    i += 2;
                    inComment = false;
                    continue;
                }
            }
            if (c.equals("\n")) {
                inComment = false;
                result.add(c);
                i += 1;
                continue;
            }
            if (c.equals("'") && !quote.double_ && !inComment) {
                quote.single = !quote.single;
            } else {
                if (c.equals("\"") && !quote.single && !inComment) {
                    quote.double_ = !quote.double_;
                } else {
                    if (c.equals("#") && !quote.single && !inComment) {
                        inComment = true;
                    }
                }
            }
            result.add(c);
            i += 1;
        }
        return String.join("", result);
    }

    static String _appendRedirects(String base, List<Node> redirects) {
        if (!redirects.isEmpty()) {
            List<String> parts = new ArrayList<>();
            for (Node r : redirects) {
                parts.add(((Node) r).toSexp());
            }
            return base + " " + String.join(" ", parts);
        }
        return base;
    }

    static String _formatArithVal(String s) {
        Word w = new Word(s, new ArrayList<>(), "word");
        String val = w._expandAllAnsiCQuotes(s);
        val = w._stripLocaleStringDollars(val);
        val = w._formatCommandSubstitutions(val, false);
        val = val.replace("\\", "\\\\").replace("\"", "\\\"");
        val = val.replace("\n", "\\n").replace("\t", "\\t");
        return val;
    }

    static Tuple7 _consumeSingleQuote(String s, int start) {
        List<String> chars = new ArrayList<>(List.of("'"));
        int i = start + 1;
        while (i < s.length() && !String.valueOf(s.charAt(i)).equals("'")) {
            chars.add(String.valueOf(s.charAt(i)));
            i += 1;
        }
        if (i < s.length()) {
            chars.add(String.valueOf(s.charAt(i)));
            i += 1;
        }
        return new Tuple7(i, chars);
    }

    static Tuple7 _consumeDoubleQuote(String s, int start) {
        List<String> chars = new ArrayList<>(List.of("\""));
        int i = start + 1;
        while (i < s.length() && !String.valueOf(s.charAt(i)).equals("\"")) {
            if (String.valueOf(s.charAt(i)).equals("\\") && i + 1 < s.length()) {
                chars.add(String.valueOf(s.charAt(i)));
                i += 1;
            }
            chars.add(String.valueOf(s.charAt(i)));
            i += 1;
        }
        if (i < s.length()) {
            chars.add(String.valueOf(s.charAt(i)));
            i += 1;
        }
        return new Tuple7(i, chars);
    }

    static boolean _hasBracketClose(String s, int start, int depth) {
        int i = start;
        while (i < s.length()) {
            if (String.valueOf(s.charAt(i)).equals("]")) {
                return true;
            }
            if (String.valueOf(s.charAt(i)).equals("|") || String.valueOf(s.charAt(i)).equals(")") && depth == 0) {
                return false;
            }
            i += 1;
        }
        return false;
    }

    static Tuple6 _consumeBracketClass(String s, int start, int depth) {
        int scanPos = start + 1;
        if (scanPos < s.length() && String.valueOf(s.charAt(scanPos)).equals("!") || String.valueOf(s.charAt(scanPos)).equals("^")) {
            scanPos += 1;
        }
        if (scanPos < s.length() && String.valueOf(s.charAt(scanPos)).equals("]")) {
            if (ParableFunctions._hasBracketClose(s, scanPos + 1, depth)) {
                scanPos += 1;
            }
        }
        boolean isBracket = false;
        while (scanPos < s.length()) {
            if (String.valueOf(s.charAt(scanPos)).equals("]")) {
                isBracket = true;
                break;
            }
            if (String.valueOf(s.charAt(scanPos)).equals(")") && depth == 0) {
                break;
            }
            if (String.valueOf(s.charAt(scanPos)).equals("|") && depth == 0) {
                break;
            }
            scanPos += 1;
        }
        if (!isBracket) {
            return new Tuple6(start + 1, new ArrayList<>(List.of("[")), false);
        }
        List<String> chars = new ArrayList<>(List.of("["));
        int i = start + 1;
        if (i < s.length() && String.valueOf(s.charAt(i)).equals("!") || String.valueOf(s.charAt(i)).equals("^")) {
            chars.add(String.valueOf(s.charAt(i)));
            i += 1;
        }
        if (i < s.length() && String.valueOf(s.charAt(i)).equals("]")) {
            if (ParableFunctions._hasBracketClose(s, i + 1, depth)) {
                chars.add(String.valueOf(s.charAt(i)));
                i += 1;
            }
        }
        while (i < s.length() && !String.valueOf(s.charAt(i)).equals("]")) {
            chars.add(String.valueOf(s.charAt(i)));
            i += 1;
        }
        if (i < s.length()) {
            chars.add(String.valueOf(s.charAt(i)));
            i += 1;
        }
        return new Tuple6(i, chars, true);
    }

    static String _formatCondBody(Node node) {
        Object kind = node.getKind();
        if (kind == "unary-test") {
            String operandVal = ((Word) ((UnaryTest) node).operand).getCondFormattedValue();
            return ((UnaryTest) node).op + " " + operandVal;
        }
        if (kind == "binary-test") {
            String leftVal = ((Word) ((BinaryTest) node).left).getCondFormattedValue();
            String rightVal = ((Word) ((BinaryTest) node).right).getCondFormattedValue();
            return leftVal + " " + ((BinaryTest) node).op + " " + rightVal;
        }
        if (kind == "cond-and") {
            return ParableFunctions._formatCondBody(((CondAnd) node).left) + " && " + ParableFunctions._formatCondBody(((CondAnd) node).right);
        }
        if (kind == "cond-or") {
            return ParableFunctions._formatCondBody(((CondOr) node).left) + " || " + ParableFunctions._formatCondBody(((CondOr) node).right);
        }
        if (kind == "cond-not") {
            return "! " + ParableFunctions._formatCondBody(((CondNot) node).operand);
        }
        if (kind == "cond-paren") {
            return "( " + ParableFunctions._formatCondBody(((CondParen) node).inner) + " )";
        }
        return "";
    }

    static boolean _startsWithSubshell(Node node) {
        if (node instanceof Subshell nodeSubshell) {
            return true;
        }
        if (node instanceof ListNode nodeList) {
            for (Node p : nodeList.parts) {
                if (p.getKind() != "operator") {
                    return ParableFunctions._startsWithSubshell(p);
                }
            }
            return false;
        }
        if (node instanceof Pipeline nodePipeline) {
            if (!nodePipeline.commands.isEmpty()) {
                return ParableFunctions._startsWithSubshell(nodePipeline.commands.get(0));
            }
            return false;
        }
        return false;
    }

    static String _formatCmdsubNode(Node node, int indent, boolean inProcsub, boolean compactRedirects, boolean procsubFirst) {
        if (node == null) {
            return "";
        }
        String sp = ParableFunctions._repeatStr(" ", indent);
        String innerSp = ParableFunctions._repeatStr(" ", indent + 4);
        if (node instanceof ArithEmpty nodeArithEmpty) {
            return "";
        }
        if (node instanceof Command nodeCommand) {
            List<String> parts = new ArrayList<>();
            for (Word w : nodeCommand.words) {
                String val = w._expandAllAnsiCQuotes(w.value);
                val = w._stripLocaleStringDollars(val);
                val = w._normalizeArrayWhitespace(val);
                val = w._formatCommandSubstitutions(val, false);
                parts.add(val);
            }
            List<HereDoc> heredocs = new ArrayList<>();
            for (Node r : nodeCommand.redirects) {
                if (r instanceof HereDoc rHereDoc) {
                    heredocs.add(rHereDoc);
                }
            }
            for (Node r : nodeCommand.redirects) {
                parts.add(ParableFunctions._formatRedirect(r, compactRedirects, true));
            }
            String result = "";
            if (compactRedirects && !nodeCommand.words.isEmpty() && !nodeCommand.redirects.isEmpty()) {
                List<String> wordParts = new ArrayList<>(parts.subList(0, nodeCommand.words.size()));
                List<String> redirectParts = new ArrayList<>(parts.subList(nodeCommand.words.size(), parts.size()));
                result = String.join(" ", wordParts) + String.join("", redirectParts);
            } else {
                result = String.join(" ", parts);
            }
            for (HereDoc h : heredocs) {
                result = result + ParableFunctions._formatHeredocBody(h);
            }
            return result;
        }
        if (node instanceof Pipeline nodePipeline) {
            List<Tuple5> cmds = new ArrayList<>();
            int i = 0;
            Node cmd = null;
            boolean needsRedirect = false;
            while (i < nodePipeline.commands.size()) {
                cmd = nodePipeline.commands.get(i);
                if (cmd instanceof PipeBoth cmdPipeBoth) {
                    i += 1;
                    continue;
                }
                needsRedirect = i + 1 < nodePipeline.commands.size() && nodePipeline.commands.get(i + 1).getKind() == "pipe-both";
                cmds.add(new Tuple5(cmd, needsRedirect));
                i += 1;
            }
            List<String> resultParts = new ArrayList<>();
            int idx = 0;
            while (idx < cmds.size()) {
                {
                    Tuple5 _entry = cmds.get(idx);
                    cmd = _entry.f0();
                    needsRedirect = _entry.f1();
                }
                String formatted = ParableFunctions._formatCmdsubNode(cmd, indent, inProcsub, false, procsubFirst && idx == 0);
                boolean isLast = idx == cmds.size() - 1;
                boolean hasHeredoc = false;
                if (cmd.getKind() == "command" && !((Command) cmd).redirects.isEmpty()) {
                    for (Node r : ((Command) cmd).redirects) {
                        if (r instanceof HereDoc rHereDoc) {
                            hasHeredoc = true;
                            break;
                        }
                    }
                }
                int firstNl = 0;
                if (needsRedirect) {
                    if (hasHeredoc) {
                        firstNl = formatted.indexOf("\n");
                        if (firstNl != -1) {
                            formatted = formatted.substring(0, firstNl) + " 2>&1" + formatted.substring(firstNl);
                        } else {
                            formatted = formatted + " 2>&1";
                        }
                    } else {
                        formatted = formatted + " 2>&1";
                    }
                }
                if (!isLast && hasHeredoc) {
                    firstNl = formatted.indexOf("\n");
                    if (firstNl != -1) {
                        formatted = formatted.substring(0, firstNl) + " |" + formatted.substring(firstNl);
                    }
                    resultParts.add(formatted);
                } else {
                    resultParts.add(formatted);
                }
                idx += 1;
            }
            boolean compactPipe = inProcsub && !cmds.isEmpty() && cmds.get(0).f0().getKind() == "subshell";
            String result = "";
            idx = 0;
            while (idx < resultParts.size()) {
                String part = resultParts.get(idx);
                if (idx > 0) {
                    if (result.endsWith("\n")) {
                        result = result + "  " + part;
                    } else {
                        if (compactPipe) {
                            result = result + "|" + part;
                        } else {
                            result = result + " | " + part;
                        }
                    }
                } else {
                    result = part;
                }
                idx += 1;
            }
            return result;
        }
        if (node instanceof ListNode nodeList) {
            boolean hasHeredoc = false;
            for (Node p : nodeList.parts) {
                if (p.getKind() == "command" && !((Command) p).redirects.isEmpty()) {
                    for (Node r : ((Command) p).redirects) {
                        if (r instanceof HereDoc rHereDoc) {
                            hasHeredoc = true;
                            break;
                        }
                    }
                } else {
                    if (p instanceof Pipeline pPipeline) {
                        for (Node cmd : pPipeline.commands) {
                            if (cmd.getKind() == "command" && !((Command) cmd).redirects.isEmpty()) {
                                for (Node r : ((Command) cmd).redirects) {
                                    if (r instanceof HereDoc rHereDoc) {
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
            List<String> result = new ArrayList<>();
            boolean skippedSemi = false;
            int cmdCount = 0;
            for (Node p : nodeList.parts) {
                if (p instanceof Operator pOperator) {
                    if (pOperator.op.equals(";")) {
                        if (!result.isEmpty() && result.get(result.size() - 1).endsWith("\n")) {
                            skippedSemi = true;
                            continue;
                        }
                        if (result.size() >= 3 && result.get(result.size() - 2).equals("\n") && result.get(result.size() - 3).endsWith("\n")) {
                            skippedSemi = true;
                            continue;
                        }
                        result.add(";");
                        skippedSemi = false;
                    } else {
                        if (pOperator.op.equals("\n")) {
                            if (!result.isEmpty() && result.get(result.size() - 1).equals(";")) {
                                skippedSemi = false;
                                continue;
                            }
                            if (!result.isEmpty() && result.get(result.size() - 1).endsWith("\n")) {
                                result.add((skippedSemi ? " " : "\n"));
                                skippedSemi = false;
                                continue;
                            }
                            result.add("\n");
                            skippedSemi = false;
                        } else {
                            String last = "";
                            int firstNl = 0;
                            if (pOperator.op.equals("&")) {
                                if (!result.isEmpty() && result.get(result.size() - 1).indexOf("<<") != -1 && result.get(result.size() - 1).indexOf("\n") != -1) {
                                    last = result.get(result.size() - 1);
                                    if (last.indexOf(" |") != -1 || last.startsWith("|")) {
                                        result.set(result.size() - 1, last + " &");
                                    } else {
                                        firstNl = last.indexOf("\n");
                                        result.set(result.size() - 1, last.substring(0, firstNl) + " &" + last.substring(firstNl));
                                    }
                                } else {
                                    result.add(" &");
                                }
                            } else {
                                if (!result.isEmpty() && result.get(result.size() - 1).indexOf("<<") != -1 && result.get(result.size() - 1).indexOf("\n") != -1) {
                                    last = result.get(result.size() - 1);
                                    firstNl = last.indexOf("\n");
                                    result.set(result.size() - 1, last.substring(0, firstNl) + " " + pOperator.op + " " + last.substring(firstNl));
                                } else {
                                    result.add(" " + pOperator.op);
                                }
                            }
                        }
                    }
                } else {
                    if (!result.isEmpty() && !(result.get(result.size() - 1).endsWith(" ") || result.get(result.size() - 1).endsWith("\n"))) {
                        result.add(" ");
                    }
                    String formattedCmd = ParableFunctions._formatCmdsubNode(p, indent, inProcsub, compactRedirects, procsubFirst && cmdCount == 0);
                    if (!result.isEmpty()) {
                        String last = result.get(result.size() - 1);
                        if (last.indexOf(" || \n") != -1 || last.indexOf(" && \n") != -1) {
                            formattedCmd = " " + formattedCmd;
                        }
                    }
                    if (skippedSemi) {
                        formattedCmd = " " + formattedCmd;
                        skippedSemi = false;
                    }
                    result.add(formattedCmd);
                    cmdCount += 1;
                }
            }
            String s = String.join("", result);
            if (s.indexOf(" &\n") != -1 && s.endsWith("\n")) {
                return s + " ";
            }
            while (s.endsWith(";")) {
                s = ParableFunctions._substring(s, 0, s.length() - 1);
            }
            if (!hasHeredoc) {
                while (s.endsWith("\n")) {
                    s = ParableFunctions._substring(s, 0, s.length() - 1);
                }
            }
            return s;
        }
        if (node instanceof If nodeIf) {
            String cond = ParableFunctions._formatCmdsubNode(nodeIf.condition, indent, false, false, false);
            String thenBody = ParableFunctions._formatCmdsubNode(nodeIf.thenBody, indent + 4, false, false, false);
            String result = "if " + cond + "; then\n" + innerSp + thenBody + ";";
            if (nodeIf.elseBody != null) {
                String elseBody = ParableFunctions._formatCmdsubNode(nodeIf.elseBody, indent + 4, false, false, false);
                result = result + "\n" + sp + "else\n" + innerSp + elseBody + ";";
            }
            result = result + "\n" + sp + "fi";
            return result;
        }
        if (node instanceof While nodeWhile) {
            String cond = ParableFunctions._formatCmdsubNode(nodeWhile.condition, indent, false, false, false);
            String body = ParableFunctions._formatCmdsubNode(nodeWhile.body, indent + 4, false, false, false);
            String result = "while " + cond + "; do\n" + innerSp + body + ";\n" + sp + "done";
            if (!nodeWhile.redirects.isEmpty()) {
                for (Node r : nodeWhile.redirects) {
                    result = result + " " + ParableFunctions._formatRedirect(r, false, false);
                }
            }
            return result;
        }
        if (node instanceof Until nodeUntil) {
            String cond = ParableFunctions._formatCmdsubNode(nodeUntil.condition, indent, false, false, false);
            String body = ParableFunctions._formatCmdsubNode(nodeUntil.body, indent + 4, false, false, false);
            String result = "until " + cond + "; do\n" + innerSp + body + ";\n" + sp + "done";
            if (!nodeUntil.redirects.isEmpty()) {
                for (Node r : nodeUntil.redirects) {
                    result = result + " " + ParableFunctions._formatRedirect(r, false, false);
                }
            }
            return result;
        }
        if (node instanceof For nodeFor) {
            String var = nodeFor.var;
            String body = ParableFunctions._formatCmdsubNode(nodeFor.body, indent + 4, false, false, false);
            String result = "";
            if (nodeFor.words != null) {
                List<String> wordVals = new ArrayList<>();
                for (Word w : nodeFor.words) {
                    wordVals.add(w.value);
                }
                String words = String.join(" ", wordVals);
                if (!words.equals("")) {
                    result = "for " + var + " in " + words + ";\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done";
                } else {
                    result = "for " + var + " in ;\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done";
                }
            } else {
                result = "for " + var + " in \"$@\";\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done";
            }
            if (!nodeFor.redirects.isEmpty()) {
                for (Node r : nodeFor.redirects) {
                    result = result + " " + ParableFunctions._formatRedirect(r, false, false);
                }
            }
            return result;
        }
        if (node instanceof ForArith nodeForArith) {
            String body = ParableFunctions._formatCmdsubNode(nodeForArith.body, indent + 4, false, false, false);
            String result = "for ((" + nodeForArith.init + "; " + nodeForArith.cond + "; " + nodeForArith.incr + "))\ndo\n" + innerSp + body + ";\n" + sp + "done";
            if (!nodeForArith.redirects.isEmpty()) {
                for (Node r : nodeForArith.redirects) {
                    result = result + " " + ParableFunctions._formatRedirect(r, false, false);
                }
            }
            return result;
        }
        if (node instanceof Case nodeCase) {
            String word = ((Word) nodeCase.word).value;
            List<String> patterns = new ArrayList<>();
            int i = 0;
            while (i < nodeCase.patterns.size()) {
                Node p = nodeCase.patterns.get(i);
                Object pat = ((CasePattern) p).pattern.replace("|", " | ");
                String body = "";
                if (((CasePattern) p).body != null) {
                    body = ParableFunctions._formatCmdsubNode(((CasePattern) p).body, indent + 8, false, false, false);
                } else {
                    body = "";
                }
                String term = ((CasePattern) p).terminator;
                String patIndent = ParableFunctions._repeatStr(" ", indent + 8);
                String termIndent = ParableFunctions._repeatStr(" ", indent + 4);
                String bodyPart = (!body.equals("") ? patIndent + body + "\n" : "\n");
                if (i == 0) {
                    patterns.add(" " + pat + ")\n" + bodyPart + termIndent + term);
                } else {
                    patterns.add(pat + ")\n" + bodyPart + termIndent + term);
                }
                i += 1;
            }
            Object patternStr = String.join("\n" + ParableFunctions._repeatStr(" ", indent + 4), patterns);
            String redirects = "";
            if (!nodeCase.redirects.isEmpty()) {
                List<String> redirectParts = new ArrayList<>();
                for (Node r : nodeCase.redirects) {
                    redirectParts.add(ParableFunctions._formatRedirect(r, false, false));
                }
                redirects = " " + String.join(" ", redirectParts);
            }
            return "case " + word + " in" + patternStr + "\n" + sp + "esac" + redirects;
        }
        if (node instanceof Function nodeFunction) {
            String name = nodeFunction.name;
            Node innerBody = (nodeFunction.body.getKind() == "brace-group" ? ((BraceGroup) nodeFunction.body).body : nodeFunction.body);
            String body = ParableFunctions._formatCmdsubNode(innerBody, indent + 4, false, false, false).replaceFirst("[" + ";" + "]+$", "");
            return String.format("function %s () \n{ \n%s%s\n}", name, innerSp, body);
        }
        if (node instanceof Subshell nodeSubshell) {
            String body = ParableFunctions._formatCmdsubNode(nodeSubshell.body, indent, inProcsub, compactRedirects, false);
            String redirects = "";
            if (!nodeSubshell.redirects.isEmpty()) {
                List<String> redirectParts = new ArrayList<>();
                for (Node r : nodeSubshell.redirects) {
                    redirectParts.add(ParableFunctions._formatRedirect(r, false, false));
                }
                redirects = String.join(" ", redirectParts);
            }
            if (procsubFirst) {
                if (!redirects.equals("")) {
                    return "(" + body + ") " + redirects;
                }
                return "(" + body + ")";
            }
            if (!redirects.equals("")) {
                return "( " + body + " ) " + redirects;
            }
            return "( " + body + " )";
        }
        if (node instanceof BraceGroup nodeBraceGroup) {
            String body = ParableFunctions._formatCmdsubNode(nodeBraceGroup.body, indent, false, false, false);
            body = body.replaceFirst("[" + ";" + "]+$", "");
            String terminator = (body.endsWith(" &") ? " }" : "; }");
            String redirects = "";
            if (!nodeBraceGroup.redirects.isEmpty()) {
                List<String> redirectParts = new ArrayList<>();
                for (Node r : nodeBraceGroup.redirects) {
                    redirectParts.add(ParableFunctions._formatRedirect(r, false, false));
                }
                redirects = String.join(" ", redirectParts);
            }
            if (!redirects.equals("")) {
                return "{ " + body + terminator + " " + redirects;
            }
            return "{ " + body + terminator;
        }
        if (node instanceof ArithmeticCommand nodeArithmeticCommand) {
            return "((" + nodeArithmeticCommand.rawContent + "))";
        }
        if (node instanceof ConditionalExpr nodeConditionalExpr) {
            String body = ParableFunctions._formatCondBody(((Node) nodeConditionalExpr.body));
            return "[[ " + body + " ]]";
        }
        if (node instanceof Negation nodeNegation) {
            if (nodeNegation.pipeline != null) {
                return "! " + ParableFunctions._formatCmdsubNode(nodeNegation.pipeline, indent, false, false, false);
            }
            return "! ";
        }
        if (node instanceof Time nodeTime) {
            String prefix = (nodeTime.posix ? "time -p " : "time ");
            if (nodeTime.pipeline != null) {
                return prefix + ParableFunctions._formatCmdsubNode(nodeTime.pipeline, indent, false, false, false);
            }
            return prefix;
        }
        return "";
    }

    static String _formatRedirect(Node r, boolean compact, boolean heredocOpOnly) {
        if (r instanceof HereDoc rHereDoc) {
            String op = "";
            if (rHereDoc.stripTabs) {
                op = "<<-";
            } else {
                op = "<<";
            }
            if (rHereDoc.fd != null && rHereDoc.fd > 0) {
                op = String.valueOf(rHereDoc.fd) + op;
            }
            String delim = "";
            if (rHereDoc.quoted) {
                delim = "'" + rHereDoc.delimiter + "'";
            } else {
                delim = rHereDoc.delimiter;
            }
            if (heredocOpOnly) {
                return op + delim;
            }
            return op + delim + "\n" + rHereDoc.content + rHereDoc.delimiter + "\n";
        }
        String op = ((Redirect) r).op;
        if (op.equals("1>")) {
            op = ">";
        } else {
            if (op.equals("0<")) {
                op = "<";
            }
        }
        String target = ((Redirect) r).target.value;
        target = ((Redirect) r).target._expandAllAnsiCQuotes(target);
        target = ((Redirect) r).target._stripLocaleStringDollars(target);
        target = ((Redirect) r).target._formatCommandSubstitutions(target, false);
        if (target.startsWith("&")) {
            boolean wasInputClose = false;
            if (target.equals("&-") && op.endsWith("<")) {
                wasInputClose = true;
                op = ParableFunctions._substring(op, 0, op.length() - 1) + ">";
            }
            String afterAmp = ParableFunctions._substring(target, 1, target.length());
            boolean isLiteralFd = afterAmp.equals("-") || !afterAmp.isEmpty() && String.valueOf(afterAmp.charAt(0)).chars().allMatch(Character::isDigit);
            if (isLiteralFd) {
                if (op.equals(">") || op.equals(">&")) {
                    op = (wasInputClose ? "0>" : "1>");
                } else {
                    if (op.equals("<") || op.equals("<&")) {
                        op = "0<";
                    }
                }
            } else {
                if (op.equals("1>")) {
                    op = ">";
                } else {
                    if (op.equals("0<")) {
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

    static String _formatHeredocBody(Node r) {
        return "\n" + ((HereDoc) r).content + ((HereDoc) r).delimiter + "\n";
    }

    static boolean _lookaheadForEsac(String value, int start, int caseDepth) {
        int i = start;
        int depth = caseDepth;
        QuoteState quote = ParableFunctions.newQuoteState();
        while (i < value.length()) {
            String c = String.valueOf(value.charAt(i));
            if (c.equals("\\") && i + 1 < value.length() && quote.double_) {
                i += 2;
                continue;
            }
            if (c.equals("'") && !quote.double_) {
                quote.single = !quote.single;
                i += 1;
                continue;
            }
            if (c.equals("\"") && !quote.single) {
                quote.double_ = !quote.double_;
                i += 1;
                continue;
            }
            if (quote.single || quote.double_) {
                i += 1;
                continue;
            }
            if (ParableFunctions._startsWithAt(value, i, "case") && ParableFunctions._isWordBoundary(value, i, 4)) {
                depth += 1;
                i += 4;
            } else {
                if (ParableFunctions._startsWithAt(value, i, "esac") && ParableFunctions._isWordBoundary(value, i, 4)) {
                    depth -= 1;
                    if (depth == 0) {
                        return true;
                    }
                    i += 4;
                } else {
                    if (c.equals("(")) {
                        i += 1;
                    } else {
                        if (c.equals(")")) {
                            if (depth > 0) {
                                i += 1;
                            } else {
                                break;
                            }
                        } else {
                            i += 1;
                        }
                    }
                }
            }
        }
        return false;
    }

    static int _skipBacktick(String value, int start) {
        int i = start + 1;
        while (i < value.length() && !String.valueOf(value.charAt(i)).equals("`")) {
            if (String.valueOf(value.charAt(i)).equals("\\") && i + 1 < value.length()) {
                i += 2;
            } else {
                i += 1;
            }
        }
        if (i < value.length()) {
            i += 1;
        }
        return i;
    }

    static int _skipSingleQuoted(String s, int start) {
        int i = start;
        while (i < s.length() && !String.valueOf(s.charAt(i)).equals("'")) {
            i += 1;
        }
        return (i < s.length() ? i + 1 : i);
    }

    static int _skipDoubleQuoted(String s, int start) {
        int i = start;
        int n = s.length();
        boolean passNext = false;
        boolean backq = false;
        while (i < n) {
            String c = String.valueOf(s.charAt(i));
            if (passNext) {
                passNext = false;
                i += 1;
                continue;
            }
            if (c.equals("\\")) {
                passNext = true;
                i += 1;
                continue;
            }
            if (backq) {
                if (c.equals("`")) {
                    backq = false;
                }
                i += 1;
                continue;
            }
            if (c.equals("`")) {
                backq = true;
                i += 1;
                continue;
            }
            if (c.equals("$") && i + 1 < n) {
                if (String.valueOf(s.charAt(i + 1)).equals("(")) {
                    i = ParableFunctions._findCmdsubEnd(s, i + 2);
                    continue;
                }
                if (String.valueOf(s.charAt(i + 1)).equals("{")) {
                    i = ParableFunctions._findBracedParamEnd(s, i + 2);
                    continue;
                }
            }
            if (c.equals("\"")) {
                return i + 1;
            }
            i += 1;
        }
        return i;
    }

    static boolean _isValidArithmeticStart(String value, int start) {
        int scanParen = 0;
        int scanI = start + 3;
        while (scanI < value.length()) {
            String scanC = String.valueOf(value.charAt(scanI));
            if (ParableFunctions._isExpansionStart(value, scanI, "$(")) {
                scanI = ParableFunctions._findCmdsubEnd(value, scanI + 2);
                continue;
            }
            if (scanC.equals("(")) {
                scanParen += 1;
            } else {
                if (scanC.equals(")")) {
                    if (scanParen > 0) {
                        scanParen -= 1;
                    } else {
                        if (scanI + 1 < value.length() && String.valueOf(value.charAt(scanI + 1)).equals(")")) {
                            return true;
                        } else {
                            return false;
                        }
                    }
                }
            }
            scanI += 1;
        }
        return false;
    }

    static int _findFunsubEnd(String value, int start) {
        int depth = 1;
        int i = start;
        QuoteState quote = ParableFunctions.newQuoteState();
        while (i < value.length() && depth > 0) {
            String c = String.valueOf(value.charAt(i));
            if (c.equals("\\") && i + 1 < value.length() && !quote.single) {
                i += 2;
                continue;
            }
            if (c.equals("'") && !quote.double_) {
                quote.single = !quote.single;
                i += 1;
                continue;
            }
            if (c.equals("\"") && !quote.single) {
                quote.double_ = !quote.double_;
                i += 1;
                continue;
            }
            if (quote.single || quote.double_) {
                i += 1;
                continue;
            }
            if (c.equals("{")) {
                depth += 1;
            } else {
                if (c.equals("}")) {
                    depth -= 1;
                    if (depth == 0) {
                        return i + 1;
                    }
                }
            }
            i += 1;
        }
        return value.length();
    }

    static int _findCmdsubEnd(String value, int start) {
        int depth = 1;
        int i = start;
        int caseDepth = 0;
        boolean inCasePatterns = false;
        int arithDepth = 0;
        int arithParenDepth = 0;
        while (i < value.length() && depth > 0) {
            String c = String.valueOf(value.charAt(i));
            if (c.equals("\\") && i + 1 < value.length()) {
                i += 2;
                continue;
            }
            if (c.equals("'")) {
                i = ParableFunctions._skipSingleQuoted(value, i + 1);
                continue;
            }
            if (c.equals("\"")) {
                i = ParableFunctions._skipDoubleQuoted(value, i + 1);
                continue;
            }
            if (c.equals("#") && arithDepth == 0 && i == start || String.valueOf(value.charAt(i - 1)).equals(" ") || String.valueOf(value.charAt(i - 1)).equals("\t") || String.valueOf(value.charAt(i - 1)).equals("\n") || String.valueOf(value.charAt(i - 1)).equals(";") || String.valueOf(value.charAt(i - 1)).equals("|") || String.valueOf(value.charAt(i - 1)).equals("&") || String.valueOf(value.charAt(i - 1)).equals("(") || String.valueOf(value.charAt(i - 1)).equals(")")) {
                while (i < value.length() && !String.valueOf(value.charAt(i)).equals("\n")) {
                    i += 1;
                }
                continue;
            }
            if (ParableFunctions._startsWithAt(value, i, "<<<")) {
                i += 3;
                while (i < value.length() && String.valueOf(value.charAt(i)).equals(" ") || String.valueOf(value.charAt(i)).equals("\t")) {
                    i += 1;
                }
                if (i < value.length() && String.valueOf(value.charAt(i)).equals("\"")) {
                    i += 1;
                    while (i < value.length() && !String.valueOf(value.charAt(i)).equals("\"")) {
                        if (String.valueOf(value.charAt(i)).equals("\\") && i + 1 < value.length()) {
                            i += 2;
                        } else {
                            i += 1;
                        }
                    }
                    if (i < value.length()) {
                        i += 1;
                    }
                } else {
                    if (i < value.length() && String.valueOf(value.charAt(i)).equals("'")) {
                        i += 1;
                        while (i < value.length() && !String.valueOf(value.charAt(i)).equals("'")) {
                            i += 1;
                        }
                        if (i < value.length()) {
                            i += 1;
                        }
                    } else {
                        while (i < value.length() && " \t\n;|&<>()".indexOf(String.valueOf(value.charAt(i))) == -1) {
                            i += 1;
                        }
                    }
                }
                continue;
            }
            if (ParableFunctions._isExpansionStart(value, i, "$((")) {
                if (ParableFunctions._isValidArithmeticStart(value, i)) {
                    arithDepth += 1;
                    i += 3;
                    continue;
                }
                int j = ParableFunctions._findCmdsubEnd(value, i + 2);
                i = j;
                continue;
            }
            if (arithDepth > 0 && arithParenDepth == 0 && ParableFunctions._startsWithAt(value, i, "))")) {
                arithDepth -= 1;
                i += 2;
                continue;
            }
            if (c.equals("`")) {
                i = ParableFunctions._skipBacktick(value, i);
                continue;
            }
            if (arithDepth == 0 && ParableFunctions._startsWithAt(value, i, "<<")) {
                i = ParableFunctions._skipHeredoc(value, i);
                continue;
            }
            if (ParableFunctions._startsWithAt(value, i, "case") && ParableFunctions._isWordBoundary(value, i, 4)) {
                caseDepth += 1;
                inCasePatterns = false;
                i += 4;
                continue;
            }
            if (caseDepth > 0 && ParableFunctions._startsWithAt(value, i, "in") && ParableFunctions._isWordBoundary(value, i, 2)) {
                inCasePatterns = true;
                i += 2;
                continue;
            }
            if (ParableFunctions._startsWithAt(value, i, "esac") && ParableFunctions._isWordBoundary(value, i, 4)) {
                if (caseDepth > 0) {
                    caseDepth -= 1;
                    inCasePatterns = false;
                }
                i += 4;
                continue;
            }
            if (ParableFunctions._startsWithAt(value, i, ";;")) {
                i += 2;
                continue;
            }
            if (c.equals("(")) {
                if (!(inCasePatterns && caseDepth > 0)) {
                    if (arithDepth > 0) {
                        arithParenDepth += 1;
                    } else {
                        depth += 1;
                    }
                }
            } else {
                if (c.equals(")")) {
                    if (inCasePatterns && caseDepth > 0) {
                        if (!ParableFunctions._lookaheadForEsac(value, i + 1, caseDepth)) {
                            depth -= 1;
                        }
                    } else {
                        if (arithDepth > 0) {
                            if (arithParenDepth > 0) {
                                arithParenDepth -= 1;
                            }
                        } else {
                            depth -= 1;
                        }
                    }
                }
            }
            i += 1;
        }
        return i;
    }

    static int _findBracedParamEnd(String value, int start) {
        int depth = 1;
        int i = start;
        boolean inDouble = false;
        int dolbraceState = Constants.DOLBRACESTATE_PARAM;
        while (i < value.length() && depth > 0) {
            String c = String.valueOf(value.charAt(i));
            if (c.equals("\\") && i + 1 < value.length()) {
                i += 2;
                continue;
            }
            if (c.equals("'") && dolbraceState == Constants.DOLBRACESTATE_QUOTE && !inDouble) {
                i = ParableFunctions._skipSingleQuoted(value, i + 1);
                continue;
            }
            if (c.equals("\"")) {
                inDouble = !inDouble;
                i += 1;
                continue;
            }
            if (inDouble) {
                i += 1;
                continue;
            }
            if (dolbraceState == Constants.DOLBRACESTATE_PARAM && "%#^,".indexOf(c) != -1) {
                dolbraceState = Constants.DOLBRACESTATE_QUOTE;
            } else {
                if (dolbraceState == Constants.DOLBRACESTATE_PARAM && ":-=?+/".indexOf(c) != -1) {
                    dolbraceState = Constants.DOLBRACESTATE_WORD;
                }
            }
            if (c.equals("[") && dolbraceState == Constants.DOLBRACESTATE_PARAM && !inDouble) {
                int end = ParableFunctions._skipSubscript(value, i, 0);
                if (end != -1) {
                    i = end;
                    continue;
                }
            }
            if (c.equals("<") || c.equals(">") && i + 1 < value.length() && String.valueOf(value.charAt(i + 1)).equals("(")) {
                i = ParableFunctions._findCmdsubEnd(value, i + 2);
                continue;
            }
            if (c.equals("{")) {
                depth += 1;
            } else {
                if (c.equals("}")) {
                    depth -= 1;
                    if (depth == 0) {
                        return i + 1;
                    }
                }
            }
            if (ParableFunctions._isExpansionStart(value, i, "$(")) {
                i = ParableFunctions._findCmdsubEnd(value, i + 2);
                continue;
            }
            if (ParableFunctions._isExpansionStart(value, i, "${")) {
                i = ParableFunctions._findBracedParamEnd(value, i + 2);
                continue;
            }
            i += 1;
        }
        return i;
    }

    static int _skipHeredoc(String value, int start) {
        int i = start + 2;
        if (i < value.length() && String.valueOf(value.charAt(i)).equals("-")) {
            i += 1;
        }
        while (i < value.length() && ParableFunctions._isWhitespaceNoNewline(String.valueOf(value.charAt(i)))) {
            i += 1;
        }
        int delimStart = i;
        Object quoteChar = null;
        String delimiter = "";
        if (i < value.length() && String.valueOf(value.charAt(i)).equals("\"") || String.valueOf(value.charAt(i)).equals("'")) {
            quoteChar = String.valueOf(value.charAt(i));
            i += 1;
            delimStart = i;
            while (i < value.length() && !String.valueOf(value.charAt(i)).equals(quoteChar)) {
                i += 1;
            }
            delimiter = ParableFunctions._substring(value, delimStart, i);
            if (i < value.length()) {
                i += 1;
            }
        } else {
            if (i < value.length() && String.valueOf(value.charAt(i)).equals("\\")) {
                i += 1;
                delimStart = i;
                if (i < value.length()) {
                    i += 1;
                }
                while (i < value.length() && !ParableFunctions._isMetachar(String.valueOf(value.charAt(i)))) {
                    i += 1;
                }
                delimiter = ParableFunctions._substring(value, delimStart, i);
            } else {
                while (i < value.length() && !ParableFunctions._isMetachar(String.valueOf(value.charAt(i)))) {
                    i += 1;
                }
                delimiter = ParableFunctions._substring(value, delimStart, i);
            }
        }
        int parenDepth = 0;
        QuoteState quote = ParableFunctions.newQuoteState();
        boolean inBacktick = false;
        while (i < value.length() && !String.valueOf(value.charAt(i)).equals("\n")) {
            String c = String.valueOf(value.charAt(i));
            if (c.equals("\\") && i + 1 < value.length() && quote.double_ || inBacktick) {
                i += 2;
                continue;
            }
            if (c.equals("'") && !quote.double_ && !inBacktick) {
                quote.single = !quote.single;
                i += 1;
                continue;
            }
            if (c.equals("\"") && !quote.single && !inBacktick) {
                quote.double_ = !quote.double_;
                i += 1;
                continue;
            }
            if (c.equals("`") && !quote.single) {
                inBacktick = !inBacktick;
                i += 1;
                continue;
            }
            if (quote.single || quote.double_ || inBacktick) {
                i += 1;
                continue;
            }
            if (c.equals("(")) {
                parenDepth += 1;
            } else {
                if (c.equals(")")) {
                    if (parenDepth == 0) {
                        break;
                    }
                    parenDepth -= 1;
                }
            }
            i += 1;
        }
        if (i < value.length() && String.valueOf(value.charAt(i)).equals(")")) {
            return i;
        }
        if (i < value.length() && String.valueOf(value.charAt(i)).equals("\n")) {
            i += 1;
        }
        while (i < value.length()) {
            int lineStart = i;
            int lineEnd = i;
            while (lineEnd < value.length() && !String.valueOf(value.charAt(lineEnd)).equals("\n")) {
                lineEnd += 1;
            }
            String line = ParableFunctions._substring(value, lineStart, lineEnd);
            while (lineEnd < value.length()) {
                int trailingBs = 0;
                for (Integer j : java.util.stream.IntStream.iterate(line.length() - 1, _x -> _x < -1, _x -> _x + -1).boxed().toList()) {
                    if (String.valueOf(line.charAt(j)).equals("\\")) {
                        trailingBs += 1;
                    } else {
                        break;
                    }
                }
                if (trailingBs % 2 == 0) {
                    break;
                }
                line = line.substring(0, line.length() - 1);
                lineEnd += 1;
                int nextLineStart = lineEnd;
                while (lineEnd < value.length() && !String.valueOf(value.charAt(lineEnd)).equals("\n")) {
                    lineEnd += 1;
                }
                line = line + ParableFunctions._substring(value, nextLineStart, lineEnd);
            }
            String stripped = "";
            if (start + 2 < value.length() && String.valueOf(value.charAt(start + 2)).equals("-")) {
                stripped = line.replaceFirst("^[" + "\t" + "]+", "");
            } else {
                stripped = line;
            }
            if (stripped.equals(delimiter)) {
                if (lineEnd < value.length()) {
                    return lineEnd + 1;
                } else {
                    return lineEnd;
                }
            }
            if (stripped.startsWith(delimiter) && stripped.length() > delimiter.length()) {
                int tabsStripped = line.length() - stripped.length();
                return lineStart + tabsStripped + delimiter.length();
            }
            if (lineEnd < value.length()) {
                i = lineEnd + 1;
            } else {
                i = lineEnd;
            }
        }
        return i;
    }

    static Tuple9 _findHeredocContentEnd(String source, int start, List<Tuple2> delimiters) {
        if (!(!delimiters.isEmpty())) {
            return new Tuple9(start, start);
        }
        int pos = start;
        while (pos < source.length() && !String.valueOf(source.charAt(pos)).equals("\n")) {
            pos += 1;
        }
        if (pos >= source.length()) {
            return new Tuple9(start, start);
        }
        int contentStart = pos;
        pos += 1;
        for (Tuple2 _item : delimiters) {
            String delimiter = _item.f0();
            boolean stripTabs = _item.f1();
            while (pos < source.length()) {
                int lineStart = pos;
                int lineEnd = pos;
                while (lineEnd < source.length() && !String.valueOf(source.charAt(lineEnd)).equals("\n")) {
                    lineEnd += 1;
                }
                String line = ParableFunctions._substring(source, lineStart, lineEnd);
                while (lineEnd < source.length()) {
                    int trailingBs = 0;
                    for (Integer j : java.util.stream.IntStream.iterate(line.length() - 1, _x -> _x < -1, _x -> _x + -1).boxed().toList()) {
                        if (String.valueOf(line.charAt(j)).equals("\\")) {
                            trailingBs += 1;
                        } else {
                            break;
                        }
                    }
                    if (trailingBs % 2 == 0) {
                        break;
                    }
                    line = line.substring(0, line.length() - 1);
                    lineEnd += 1;
                    int nextLineStart = lineEnd;
                    while (lineEnd < source.length() && !String.valueOf(source.charAt(lineEnd)).equals("\n")) {
                        lineEnd += 1;
                    }
                    line = line + ParableFunctions._substring(source, nextLineStart, lineEnd);
                }
                String lineStripped = "";
                if (stripTabs) {
                    lineStripped = line.replaceFirst("^[" + "\t" + "]+", "");
                } else {
                    lineStripped = line;
                }
                if (lineStripped.equals(delimiter)) {
                    pos = (lineEnd < source.length() ? lineEnd + 1 : lineEnd);
                    break;
                }
                if (lineStripped.startsWith(delimiter) && lineStripped.length() > delimiter.length()) {
                    int tabsStripped = line.length() - lineStripped.length();
                    pos = lineStart + tabsStripped + delimiter.length();
                    break;
                }
                pos = (lineEnd < source.length() ? lineEnd + 1 : lineEnd);
            }
        }
        return new Tuple9(contentStart, pos);
    }

    static boolean _isWordBoundary(String s, int pos, int wordLen) {
        if (pos > 0) {
            String prev = String.valueOf(s.charAt(pos - 1));
            if (prev.chars().allMatch(Character::isLetterOrDigit) || prev.equals("_")) {
                return false;
            }
            if ("{}!".indexOf(prev) != -1) {
                return false;
            }
        }
        int end = pos + wordLen;
        if (end < s.length() && String.valueOf(s.charAt(end)).chars().allMatch(Character::isLetterOrDigit) || String.valueOf(s.charAt(end)).equals("_")) {
            return false;
        }
        return true;
    }

    static boolean _isQuote(String c) {
        return c.equals("'") || c.equals("\"");
    }

    static String _collapseWhitespace(String s) {
        List<String> result = new ArrayList<>();
        boolean prevWasWs = false;
        for (int _i = 0; _i < s.length(); _i++) {
            String c = String.valueOf(s.charAt(_i));
            if (c == " " || c == "\t") {
                if (!prevWasWs) {
                    result.add(" ");
                }
                prevWasWs = true;
            } else {
                result.add(c);
                prevWasWs = false;
            }
        }
        String joined = String.join("", result);
        return joined.trim();
    }

    static int _countTrailingBackslashes(String s) {
        int count = 0;
        for (Integer i : java.util.stream.IntStream.iterate(s.length() - 1, _x -> _x < -1, _x -> _x + -1).boxed().toList()) {
            if (String.valueOf(s.charAt(i)).equals("\\")) {
                count += 1;
            } else {
                break;
            }
        }
        return count;
    }

    static String _normalizeHeredocDelimiter(String delimiter) {
        List<String> result = new ArrayList<>();
        int i = 0;
        while (i < delimiter.length()) {
            int depth = 0;
            List<String> inner = new ArrayList<>();
            String innerStr = "";
            if (i + 1 < delimiter.length() && delimiter.substring(i, i + 2).equals("$(")) {
                result.add("$(");
                i += 2;
                depth = 1;
                inner = new ArrayList<>();
                while (i < delimiter.length() && depth > 0) {
                    if (String.valueOf(delimiter.charAt(i)).equals("(")) {
                        depth += 1;
                        inner.add(String.valueOf(delimiter.charAt(i)));
                    } else {
                        if (String.valueOf(delimiter.charAt(i)).equals(")")) {
                            depth -= 1;
                            if (depth == 0) {
                                innerStr = String.join("", inner);
                                innerStr = ParableFunctions._collapseWhitespace(innerStr);
                                result.add(innerStr);
                                result.add(")");
                            } else {
                                inner.add(String.valueOf(delimiter.charAt(i)));
                            }
                        } else {
                            inner.add(String.valueOf(delimiter.charAt(i)));
                        }
                    }
                    i += 1;
                }
            } else {
                if (i + 1 < delimiter.length() && delimiter.substring(i, i + 2).equals("${")) {
                    result.add("${");
                    i += 2;
                    depth = 1;
                    inner = new ArrayList<>();
                    while (i < delimiter.length() && depth > 0) {
                        if (String.valueOf(delimiter.charAt(i)).equals("{")) {
                            depth += 1;
                            inner.add(String.valueOf(delimiter.charAt(i)));
                        } else {
                            if (String.valueOf(delimiter.charAt(i)).equals("}")) {
                                depth -= 1;
                                if (depth == 0) {
                                    innerStr = String.join("", inner);
                                    innerStr = ParableFunctions._collapseWhitespace(innerStr);
                                    result.add(innerStr);
                                    result.add("}");
                                } else {
                                    inner.add(String.valueOf(delimiter.charAt(i)));
                                }
                            } else {
                                inner.add(String.valueOf(delimiter.charAt(i)));
                            }
                        }
                        i += 1;
                    }
                } else {
                    if (i + 1 < delimiter.length() && "<>".indexOf(String.valueOf(delimiter.charAt(i))) != -1 && String.valueOf(delimiter.charAt(i + 1)).equals("(")) {
                        result.add(String.valueOf(delimiter.charAt(i)));
                        result.add("(");
                        i += 2;
                        depth = 1;
                        inner = new ArrayList<>();
                        while (i < delimiter.length() && depth > 0) {
                            if (String.valueOf(delimiter.charAt(i)).equals("(")) {
                                depth += 1;
                                inner.add(String.valueOf(delimiter.charAt(i)));
                            } else {
                                if (String.valueOf(delimiter.charAt(i)).equals(")")) {
                                    depth -= 1;
                                    if (depth == 0) {
                                        innerStr = String.join("", inner);
                                        innerStr = ParableFunctions._collapseWhitespace(innerStr);
                                        result.add(innerStr);
                                        result.add(")");
                                    } else {
                                        inner.add(String.valueOf(delimiter.charAt(i)));
                                    }
                                } else {
                                    inner.add(String.valueOf(delimiter.charAt(i)));
                                }
                            }
                            i += 1;
                        }
                    } else {
                        result.add(String.valueOf(delimiter.charAt(i)));
                        i += 1;
                    }
                }
            }
        }
        return String.join("", result);
    }

    static boolean _isMetachar(String c) {
        return c.equals(" ") || c.equals("\t") || c.equals("\n") || c.equals("|") || c.equals("&") || c.equals(";") || c.equals("(") || c.equals(")") || c.equals("<") || c.equals(">");
    }

    static boolean _isFunsubChar(String c) {
        return c.equals(" ") || c.equals("\t") || c.equals("\n") || c.equals("|");
    }

    static boolean _isExtglobPrefix(String c) {
        return c.equals("@") || c.equals("?") || c.equals("*") || c.equals("+") || c.equals("!");
    }

    static boolean _isRedirectChar(String c) {
        return c.equals("<") || c.equals(">");
    }

    static boolean _isSpecialParam(String c) {
        return c.equals("?") || c.equals("$") || c.equals("!") || c.equals("#") || c.equals("@") || c.equals("*") || c.equals("-") || c.equals("&");
    }

    static boolean _isSpecialParamUnbraced(String c) {
        return c.equals("?") || c.equals("$") || c.equals("!") || c.equals("#") || c.equals("@") || c.equals("*") || c.equals("-");
    }

    static boolean _isDigit(String c) {
        return (c.compareTo("0") >= 0) && (c.compareTo("9") <= 0);
    }

    static boolean _isSemicolonOrNewline(String c) {
        return c.equals(";") || c.equals("\n");
    }

    static boolean _isWordEndContext(String c) {
        return c.equals(" ") || c.equals("\t") || c.equals("\n") || c.equals(";") || c.equals("|") || c.equals("&") || c.equals("<") || c.equals(">") || c.equals("(") || c.equals(")");
    }

    static int _skipMatchedPair(String s, int start, String open, String close, int flags) {
        int n = s.length();
        int i = 0;
        if ((flags & Constants.SMP_PAST_OPEN) != 0) {
            i = start;
        } else {
            if (start >= n || !String.valueOf(s.charAt(start)).equals(open)) {
                return -1;
            }
            i = start + 1;
        }
        int depth = 1;
        boolean passNext = false;
        boolean backq = false;
        while (i < n && depth > 0) {
            String c = String.valueOf(s.charAt(i));
            if (passNext) {
                passNext = false;
                i += 1;
                continue;
            }
            int literal = (flags & Constants.SMP_LITERAL);
            if (!(literal != 0) && c.equals("\\")) {
                passNext = true;
                i += 1;
                continue;
            }
            if (backq) {
                if (c.equals("`")) {
                    backq = false;
                }
                i += 1;
                continue;
            }
            if (!(literal != 0) && c.equals("`")) {
                backq = true;
                i += 1;
                continue;
            }
            if (!(literal != 0) && c.equals("'")) {
                i = ParableFunctions._skipSingleQuoted(s, i + 1);
                continue;
            }
            if (!(literal != 0) && c.equals("\"")) {
                i = ParableFunctions._skipDoubleQuoted(s, i + 1);
                continue;
            }
            if (!(literal != 0) && ParableFunctions._isExpansionStart(s, i, "$(")) {
                i = ParableFunctions._findCmdsubEnd(s, i + 2);
                continue;
            }
            if (!(literal != 0) && ParableFunctions._isExpansionStart(s, i, "${")) {
                i = ParableFunctions._findBracedParamEnd(s, i + 2);
                continue;
            }
            if (!(literal != 0) && c.equals(open)) {
                depth += 1;
            } else {
                if (c.equals(close)) {
                    depth -= 1;
                }
            }
            i += 1;
        }
        return (depth == 0 ? i : -1);
    }

    static int _skipSubscript(String s, int start, int flags) {
        return ParableFunctions._skipMatchedPair(s, start, "[", "]", flags);
    }

    static int _assignment(String s, int flags) {
        if (!(!s.equals(""))) {
            return -1;
        }
        if (!(String.valueOf(s.charAt(0)).chars().allMatch(Character::isLetter) || String.valueOf(s.charAt(0)).equals("_"))) {
            return -1;
        }
        int i = 1;
        while (i < s.length()) {
            String c = String.valueOf(s.charAt(i));
            if (c.equals("=")) {
                return i;
            }
            if (c.equals("[")) {
                int subFlags = ((flags & 2) != 0 ? Constants.SMP_LITERAL : 0);
                int end = ParableFunctions._skipSubscript(s, i, subFlags);
                if (end == -1) {
                    return -1;
                }
                i = end;
                if (i < s.length() && String.valueOf(s.charAt(i)).equals("+")) {
                    i += 1;
                }
                if (i < s.length() && String.valueOf(s.charAt(i)).equals("=")) {
                    return i;
                }
                return -1;
            }
            if (c.equals("+")) {
                if (i + 1 < s.length() && String.valueOf(s.charAt(i + 1)).equals("=")) {
                    return i + 1;
                }
                return -1;
            }
            if (!(c.chars().allMatch(Character::isLetterOrDigit) || c.equals("_"))) {
                return -1;
            }
            i += 1;
        }
        return -1;
    }

    static boolean _isArrayAssignmentPrefix(List<String> chars) {
        if (!(!chars.isEmpty())) {
            return false;
        }
        if (!(chars.get(0).chars().allMatch(Character::isLetter) || chars.get(0).equals("_"))) {
            return false;
        }
        String s = String.join("", chars);
        int i = 1;
        while (i < s.length() && String.valueOf(s.charAt(i)).chars().allMatch(Character::isLetterOrDigit) || String.valueOf(s.charAt(i)).equals("_")) {
            i += 1;
        }
        while (i < s.length()) {
            if (!String.valueOf(s.charAt(i)).equals("[")) {
                return false;
            }
            int end = ParableFunctions._skipSubscript(s, i, Constants.SMP_LITERAL);
            if (end == -1) {
                return false;
            }
            i = end;
        }
        return true;
    }

    static boolean _isSpecialParamOrDigit(String c) {
        return ParableFunctions._isSpecialParam(c) || ParableFunctions._isDigit(c);
    }

    static boolean _isParamExpansionOp(String c) {
        return c.equals(":") || c.equals("-") || c.equals("=") || c.equals("+") || c.equals("?") || c.equals("#") || c.equals("%") || c.equals("/") || c.equals("^") || c.equals(",") || c.equals("@") || c.equals("*") || c.equals("[");
    }

    static boolean _isSimpleParamOp(String c) {
        return c.equals("-") || c.equals("=") || c.equals("?") || c.equals("+");
    }

    static boolean _isEscapeCharInBacktick(String c) {
        return c.equals("$") || c.equals("`") || c.equals("\\");
    }

    static boolean _isNegationBoundary(String c) {
        return ParableFunctions._isWhitespace(c) || c.equals(";") || c.equals("|") || c.equals(")") || c.equals("&") || c.equals(">") || c.equals("<");
    }

    static boolean _isBackslashEscaped(String value, int idx) {
        int bsCount = 0;
        int j = idx - 1;
        while (j >= 0 && String.valueOf(value.charAt(j)).equals("\\")) {
            bsCount += 1;
            j -= 1;
        }
        return bsCount % 2 == 1;
    }

    static boolean _isDollarDollarParen(String value, int idx) {
        int dollarCount = 0;
        int j = idx - 1;
        while (j >= 0 && String.valueOf(value.charAt(j)).equals("$")) {
            dollarCount += 1;
            j -= 1;
        }
        return dollarCount % 2 == 1;
    }

    static boolean _isParen(String c) {
        return c.equals("(") || c.equals(")");
    }

    static boolean _isCaretOrBang(String c) {
        return c.equals("!") || c.equals("^");
    }

    static boolean _isAtOrStar(String c) {
        return c.equals("@") || c.equals("*");
    }

    static boolean _isDigitOrDash(String c) {
        return ParableFunctions._isDigit(c) || c.equals("-");
    }

    static boolean _isNewlineOrRightParen(String c) {
        return c.equals("\n") || c.equals(")");
    }

    static boolean _isSemicolonNewlineBrace(String c) {
        return c.equals(";") || c.equals("\n") || c.equals("{");
    }

    static boolean _looksLikeAssignment(String s) {
        return ParableFunctions._assignment(s, 0) != -1;
    }

    static boolean _isValidIdentifier(String name) {
        if (!(!name.equals(""))) {
            return false;
        }
        if (!(String.valueOf(name.charAt(0)).chars().allMatch(Character::isLetter) || String.valueOf(name.charAt(0)).equals("_"))) {
            return false;
        }
        for (int _i = 0; _i < name.substring(1).length(); _i++) {
            String c = String.valueOf(name.substring(1).charAt(_i));
            if (!(c.chars().allMatch(Character::isLetterOrDigit) || c == "_")) {
                return false;
            }
        }
        return true;
    }

    static List<Node> parse(String source, boolean extglob) {
        Parser parser = ParableFunctions.newParser(source, false, extglob);
        return parser.parse();
    }

    static ParseError newParseError(String message, int pos, int line) {
        ParseError self = new ParseError("", 0, 0);
        self.message = message;
        self.pos = pos;
        self.line = line;
        return self;
    }

    static MatchedPairError newMatchedPairError(String message, int pos, int line) {
        return new MatchedPairError();
    }

    static QuoteState newQuoteState() {
        QuoteState self = new QuoteState(false, false, new ArrayList<>());
        self.single = false;
        self.double_ = false;
        self._stack = new ArrayList<>();
        return self;
    }

    static ParseContext newParseContext(int kind) {
        ParseContext self = new ParseContext(0, 0, 0, 0, 0, 0, 0, null);
        self.kind = kind;
        self.parenDepth = 0;
        self.braceDepth = 0;
        self.bracketDepth = 0;
        self.caseDepth = 0;
        self.arithDepth = 0;
        self.arithParenDepth = 0;
        self.quote = ParableFunctions.newQuoteState();
        return self;
    }

    static ContextStack newContextStack() {
        ContextStack self = new ContextStack(new ArrayList<>());
        self._stack = new ArrayList<>(List.of(ParableFunctions.newParseContext(0)));
        return self;
    }

    static Lexer newLexer(String source, boolean extglob) {
        Lexer self = new Lexer(null, "", 0, 0, null, null, 0, 0, new ArrayList<>(), false, null, "", null, 0, false, false, false, 0, 0, false, false, false);
        self.source = source;
        self.pos = 0;
        self.length = source.length();
        self.quote = ParableFunctions.newQuoteState();
        self._tokenCache = null;
        self._parserState = Constants.PARSERSTATEFLAGS_NONE;
        self._dolbraceState = Constants.DOLBRACESTATE_NONE;
        self._pendingHeredocs = new ArrayList<>();
        self._extglob = extglob;
        self._parser = null;
        self._eofToken = "";
        self._lastReadToken = null;
        self._wordContext = Constants.WORD_CTX_NORMAL;
        self._atCommandStart = false;
        self._inArrayLiteral = false;
        self._inAssignBuiltin = false;
        self._postReadPos = 0;
        self._cachedWordContext = Constants.WORD_CTX_NORMAL;
        self._cachedAtCommandStart = false;
        self._cachedInArrayLiteral = false;
        self._cachedInAssignBuiltin = false;
        return self;
    }

    static Parser newParser(String source, boolean inProcessSub, boolean extglob) {
        Parser self = new Parser("", 0, 0, new ArrayList<>(), 0, false, false, false, null, null, new ArrayList<>(), 0, 0, "", 0, false, false, false, "", 0, 0);
        self.source = source;
        self.pos = 0;
        self.length = source.length();
        self._pendingHeredocs = new ArrayList<>();
        self._cmdsubHeredocEnd = -1;
        self._sawNewlineInSingleQuote = false;
        self._inProcessSub = inProcessSub;
        self._extglob = extglob;
        self._ctx = ParableFunctions.newContextStack();
        self._lexer = ParableFunctions.newLexer(source, extglob);
        self._lexer._parser = self;
        self._tokenHistory = new ArrayList<>(List.of(null, null, null, null));
        self._parserState = Constants.PARSERSTATEFLAGS_NONE;
        self._dolbraceState = Constants.DOLBRACESTATE_NONE;
        self._eofToken = "";
        self._wordContext = Constants.WORD_CTX_NORMAL;
        self._atCommandStart = false;
        self._inArrayLiteral = false;
        self._inAssignBuiltin = false;
        self._arithSrc = "";
        self._arithPos = 0;
        self._arithLen = 0;
        return self;
    }
}
