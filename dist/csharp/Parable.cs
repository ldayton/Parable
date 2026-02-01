using System;
using System.Collections.Generic;
using System.Linq;

public static class Constants
{
    public static readonly Dictionary<string, int> ANSI_C_ESCAPES = new Dictionary<string, int> { { "a", 7 }, { "b", 8 }, { "e", 27 }, { "E", 27 }, { "f", 12 }, { "n", 10 }, { "r", 13 }, { "t", 9 }, { "v", 11 }, { "\\", 92 }, { "\"", 34 }, { "?", 63 } };
    public const int TOKENTYPE_EOF = 0;
    public const int TOKENTYPE_WORD = 1;
    public const int TOKENTYPE_NEWLINE = 2;
    public const int TOKENTYPE_SEMI = 10;
    public const int TOKENTYPE_PIPE = 11;
    public const int TOKENTYPE_AMP = 12;
    public const int TOKENTYPE_LPAREN = 13;
    public const int TOKENTYPE_RPAREN = 14;
    public const int TOKENTYPE_LBRACE = 15;
    public const int TOKENTYPE_RBRACE = 16;
    public const int TOKENTYPE_LESS = 17;
    public const int TOKENTYPE_GREATER = 18;
    public const int TOKENTYPE_AND_AND = 30;
    public const int TOKENTYPE_OR_OR = 31;
    public const int TOKENTYPE_SEMI_SEMI = 32;
    public const int TOKENTYPE_SEMI_AMP = 33;
    public const int TOKENTYPE_SEMI_SEMI_AMP = 34;
    public const int TOKENTYPE_LESS_LESS = 35;
    public const int TOKENTYPE_GREATER_GREATER = 36;
    public const int TOKENTYPE_LESS_AMP = 37;
    public const int TOKENTYPE_GREATER_AMP = 38;
    public const int TOKENTYPE_LESS_GREATER = 39;
    public const int TOKENTYPE_GREATER_PIPE = 40;
    public const int TOKENTYPE_LESS_LESS_MINUS = 41;
    public const int TOKENTYPE_LESS_LESS_LESS = 42;
    public const int TOKENTYPE_AMP_GREATER = 43;
    public const int TOKENTYPE_AMP_GREATER_GREATER = 44;
    public const int TOKENTYPE_PIPE_AMP = 45;
    public const int TOKENTYPE_IF = 50;
    public const int TOKENTYPE_THEN = 51;
    public const int TOKENTYPE_ELSE = 52;
    public const int TOKENTYPE_ELIF = 53;
    public const int TOKENTYPE_FI = 54;
    public const int TOKENTYPE_CASE = 55;
    public const int TOKENTYPE_ESAC = 56;
    public const int TOKENTYPE_FOR = 57;
    public const int TOKENTYPE_WHILE = 58;
    public const int TOKENTYPE_UNTIL = 59;
    public const int TOKENTYPE_DO = 60;
    public const int TOKENTYPE_DONE = 61;
    public const int TOKENTYPE_IN = 62;
    public const int TOKENTYPE_FUNCTION = 63;
    public const int TOKENTYPE_SELECT = 64;
    public const int TOKENTYPE_COPROC = 65;
    public const int TOKENTYPE_TIME = 66;
    public const int TOKENTYPE_BANG = 67;
    public const int TOKENTYPE_LBRACKET_LBRACKET = 68;
    public const int TOKENTYPE_RBRACKET_RBRACKET = 69;
    public const int TOKENTYPE_ASSIGNMENT_WORD = 80;
    public const int TOKENTYPE_NUMBER = 81;
    public const int PARSERSTATEFLAGS_NONE = 0;
    public const int PARSERSTATEFLAGS_PST_CASEPAT = 1;
    public const int PARSERSTATEFLAGS_PST_CMDSUBST = 2;
    public const int PARSERSTATEFLAGS_PST_CASESTMT = 4;
    public const int PARSERSTATEFLAGS_PST_CONDEXPR = 8;
    public const int PARSERSTATEFLAGS_PST_COMPASSIGN = 16;
    public const int PARSERSTATEFLAGS_PST_ARITH = 32;
    public const int PARSERSTATEFLAGS_PST_HEREDOC = 64;
    public const int PARSERSTATEFLAGS_PST_REGEXP = 128;
    public const int PARSERSTATEFLAGS_PST_EXTPAT = 256;
    public const int PARSERSTATEFLAGS_PST_SUBSHELL = 512;
    public const int PARSERSTATEFLAGS_PST_REDIRLIST = 1024;
    public const int PARSERSTATEFLAGS_PST_COMMENT = 2048;
    public const int PARSERSTATEFLAGS_PST_EOFTOKEN = 4096;
    public const int DOLBRACESTATE_NONE = 0;
    public const int DOLBRACESTATE_PARAM = 1;
    public const int DOLBRACESTATE_OP = 2;
    public const int DOLBRACESTATE_WORD = 4;
    public const int DOLBRACESTATE_QUOTE = 64;
    public const int DOLBRACESTATE_QUOTE2 = 128;
    public const int MATCHEDPAIRFLAGS_NONE = 0;
    public const int MATCHEDPAIRFLAGS_DQUOTE = 1;
    public const int MATCHEDPAIRFLAGS_DOLBRACE = 2;
    public const int MATCHEDPAIRFLAGS_COMMAND = 4;
    public const int MATCHEDPAIRFLAGS_ARITH = 8;
    public const int MATCHEDPAIRFLAGS_ALLOWESC = 16;
    public const int MATCHEDPAIRFLAGS_EXTGLOB = 32;
    public const int MATCHEDPAIRFLAGS_FIRSTCLOSE = 64;
    public const int MATCHEDPAIRFLAGS_ARRAYSUB = 128;
    public const int MATCHEDPAIRFLAGS_BACKQUOTE = 256;
    public const int PARSECONTEXT_NORMAL = 0;
    public const int PARSECONTEXT_COMMAND_SUB = 1;
    public const int PARSECONTEXT_ARITHMETIC = 2;
    public const int PARSECONTEXT_CASE_PATTERN = 3;
    public const int PARSECONTEXT_BRACE_EXPANSION = 4;
    public static readonly HashSet<string> RESERVED_WORDS = new HashSet<string> { "if", "then", "elif", "else", "fi", "while", "until", "for", "select", "do", "done", "case", "esac", "in", "function", "coproc" };
    public static readonly HashSet<string> COND_UNARY_OPS = new HashSet<string> { "-a", "-b", "-c", "-d", "-e", "-f", "-g", "-h", "-k", "-p", "-r", "-s", "-t", "-u", "-w", "-x", "-G", "-L", "-N", "-O", "-S", "-z", "-n", "-o", "-v", "-R" };
    public static readonly HashSet<string> COND_BINARY_OPS = new HashSet<string> { "==", "!=", "=~", "=", "<", ">", "-eq", "-ne", "-lt", "-le", "-gt", "-ge", "-nt", "-ot", "-ef" };
    public static readonly HashSet<string> COMPOUND_KEYWORDS = new HashSet<string> { "while", "until", "for", "if", "case", "select" };
    public static readonly HashSet<string> ASSIGNMENT_BUILTINS = new HashSet<string> { "alias", "declare", "typeset", "local", "export", "readonly", "eval", "let" };
    public const int SMP_LITERAL = 1;
    public const int SMP_PAST_OPEN = 2;
    public const int WORD_CTX_NORMAL = 0;
    public const int WORD_CTX_COND = 1;
    public const int WORD_CTX_REGEX = 2;
}

public interface INode
{
    string Kind { get; }
    string GetKind();
    string ToSexp();
}

public class ParseError : Exception
{
    public new string Message { get; set; }
    public int Pos { get; set; }
    public int Line { get; set; }

    public ParseError(string message, int pos, int line) : base(message)
    {
        this.Message = message;
        this.Pos = pos;
        this.Line = line;
    }

    public string _FormatMessage()
    {
        if (this.Line != 0 && this.Pos != 0)
        {
            return string.Format("Parse error at line {0}, position {1}: {2}", this.Line, this.Pos, this.Message);
        }
        else
        {
            if (this.Pos != 0)
            {
                return string.Format("Parse error at position {0}: {1}", this.Pos, this.Message);
            }
        }
        return string.Format("Parse error: {0}", this.Message);
    }
}

public class MatchedPairError : ParseError
{
    public MatchedPairError(string message, int pos, int code) : base(message, pos, code) { }
}

public class TokenType
{
}

public class Token
{
    public int Type { get; set; }
    public string Value { get; set; }
    public int Pos { get; set; }
    public List<INode> Parts { get; set; }
    public Word Word { get; set; }

    public Token(int type, string value, int pos, List<INode> parts, Word word)
    {
        this.Type = type;
        this.Value = value;
        this.Pos = pos;
        this.Parts = parts;
        this.Word = word;
    }

    public string _Repr()
    {
        if (this.Word != null)
        {
            return string.Format("Token({0}, {1}, {2}, word={3})", this.Type, this.Value, this.Pos, this.Word);
        }
        if ((this.Parts.Count > 0))
        {
            return string.Format("Token({0}, {1}, {2}, parts={3})", this.Type, this.Value, this.Pos, this.Parts.Count);
        }
        return string.Format("Token({0}, {1}, {2})", this.Type, this.Value, this.Pos);
    }
}

public class ParserStateFlags
{
}

public class DolbraceState
{
}

public class MatchedPairFlags
{
}

public class SavedParserState
{
    public int ParserState { get; set; }
    public int DolbraceState { get; set; }
    public List<INode> PendingHeredocs { get; set; }
    public List<ParseContext> CtxStack { get; set; }
    public string EofToken { get; set; }

    public SavedParserState(int parserState, int dolbraceState, List<INode> pendingHeredocs, List<ParseContext> ctxStack, string eofToken)
    {
        this.ParserState = parserState;
        this.DolbraceState = dolbraceState;
        this.PendingHeredocs = pendingHeredocs;
        this.CtxStack = ctxStack;
        this.EofToken = eofToken;
    }
}

public class QuoteState
{
    public bool Single { get; set; }
    public bool Double { get; set; }
    public List<(bool, bool)> _Stack { get; set; }

    public QuoteState(bool single, bool @double, List<(bool, bool)> _stack)
    {
        this.Single = single;
        this.Double = @double;
        this._Stack = _stack;
    }

    public void Push()
    {
        this._Stack.Add((this.Single, this.Double));
        this.Single = false;
        this.Double = false;
    }

    public void Pop()
    {
        if ((this._Stack.Count > 0))
        {
            (bool, bool) _entry1 = this._Stack[this._Stack.Count - 1];
            this._Stack.RemoveAt(this._Stack.Count - 1);
            this.Single = _entry1.Item1;
            this.Double = _entry1.Item2;
        }
    }

    public bool InQuotes()
    {
        return this.Single || this.Double;
    }

    public QuoteState Copy()
    {
        QuoteState qs = ParableFunctions.NewQuoteState();
        qs.Single = this.Single;
        qs.Double = this.Double;
        qs._Stack = new List<(bool, bool)>(this._Stack);
        return qs;
    }

    public bool OuterDouble()
    {
        if (this._Stack.Count == 0)
        {
            return false;
        }
        return this._Stack[this._Stack.Count - 1].Item2;
    }
}

public class ParseContext
{
    public int Kind { get; set; }
    public int ParenDepth { get; set; }
    public int BraceDepth { get; set; }
    public int BracketDepth { get; set; }
    public int CaseDepth { get; set; }
    public int ArithDepth { get; set; }
    public int ArithParenDepth { get; set; }
    public QuoteState Quote { get; set; }

    public ParseContext(int kind, int parenDepth, int braceDepth, int bracketDepth, int caseDepth, int arithDepth, int arithParenDepth, QuoteState quote)
    {
        this.Kind = kind;
        this.ParenDepth = parenDepth;
        this.BraceDepth = braceDepth;
        this.BracketDepth = bracketDepth;
        this.CaseDepth = caseDepth;
        this.ArithDepth = arithDepth;
        this.ArithParenDepth = arithParenDepth;
        this.Quote = quote;
    }

    public ParseContext Copy()
    {
        ParseContext ctx = ParableFunctions.NewParseContext(this.Kind);
        ctx.ParenDepth = this.ParenDepth;
        ctx.BraceDepth = this.BraceDepth;
        ctx.BracketDepth = this.BracketDepth;
        ctx.CaseDepth = this.CaseDepth;
        ctx.ArithDepth = this.ArithDepth;
        ctx.ArithParenDepth = this.ArithParenDepth;
        ctx.Quote = this.Quote.Copy();
        return ctx;
    }
}

public class ContextStack
{
    public List<ParseContext> _Stack { get; set; }

    public ContextStack(List<ParseContext> _stack)
    {
        this._Stack = _stack;
    }

    public ParseContext GetCurrent()
    {
        return this._Stack[this._Stack.Count - 1];
    }

    public void Push(int kind)
    {
        this._Stack.Add(ParableFunctions.NewParseContext(kind));
    }

    public ParseContext Pop()
    {
        if (this._Stack.Count > 1)
        {
            return ((Func<ParseContext, ParseContext>)(_tmp => { this._Stack.RemoveAt(this._Stack.Count - 1); return _tmp; }))(this._Stack[this._Stack.Count - 1]);
        }
        return this._Stack[0];
    }

    public List<ParseContext> CopyStack()
    {
        List<ParseContext> result = new List<ParseContext>();
        foreach (ParseContext ctx in this._Stack)
        {
            result.Add(ctx.Copy());
        }
        return result;
    }

    public void RestoreFrom(List<ParseContext> savedStack)
    {
        List<ParseContext> result = new List<ParseContext>();
        foreach (ParseContext ctx in savedStack)
        {
            result.Add(ctx.Copy());
        }
        this._Stack = result;
    }
}

public class Lexer
{
    public Dictionary<string, int> RESERVEDWORDS { get; set; }
    public string Source { get; set; }
    public int Pos { get; set; }
    public int Length { get; set; }
    public QuoteState Quote { get; set; }
    public Token _TokenCache { get; set; }
    public int _ParserState { get; set; }
    public int _DolbraceState { get; set; }
    public List<INode> _PendingHeredocs { get; set; }
    public bool _Extglob { get; set; }
    public Parser _Parser { get; set; }
    public string _EofToken { get; set; }
    public Token _LastReadToken { get; set; }
    public int _WordContext { get; set; }
    public bool _AtCommandStart { get; set; }
    public bool _InArrayLiteral { get; set; }
    public bool _InAssignBuiltin { get; set; }
    public int _PostReadPos { get; set; }
    public int _CachedWordContext { get; set; }
    public bool _CachedAtCommandStart { get; set; }
    public bool _CachedInArrayLiteral { get; set; }
    public bool _CachedInAssignBuiltin { get; set; }

    public Lexer(Dictionary<string, int> reservedWords, string source, int pos, int length, QuoteState quote, Token _tokenCache, int _parserState, int _dolbraceState, List<INode> _pendingHeredocs, bool _extglob, Parser _parser, string _eofToken, Token _lastReadToken, int _wordContext, bool _atCommandStart, bool _inArrayLiteral, bool _inAssignBuiltin, int _postReadPos, int _cachedWordContext, bool _cachedAtCommandStart, bool _cachedInArrayLiteral, bool _cachedInAssignBuiltin)
    {
        this.RESERVEDWORDS = reservedWords;
        this.Source = source;
        this.Pos = pos;
        this.Length = length;
        this.Quote = quote;
        this._TokenCache = _tokenCache;
        this._ParserState = _parserState;
        this._DolbraceState = _dolbraceState;
        this._PendingHeredocs = _pendingHeredocs;
        this._Extglob = _extglob;
        this._Parser = _parser;
        this._EofToken = _eofToken;
        this._LastReadToken = _lastReadToken;
        this._WordContext = _wordContext;
        this._AtCommandStart = _atCommandStart;
        this._InArrayLiteral = _inArrayLiteral;
        this._InAssignBuiltin = _inAssignBuiltin;
        this._PostReadPos = _postReadPos;
        this._CachedWordContext = _cachedWordContext;
        this._CachedAtCommandStart = _cachedAtCommandStart;
        this._CachedInArrayLiteral = _cachedInArrayLiteral;
        this._CachedInAssignBuiltin = _cachedInAssignBuiltin;
    }

    public string Peek()
    {
        if (this.Pos >= this.Length)
        {
            return "";
        }
        return (this.Source[this.Pos]).ToString();
    }

    public string Advance()
    {
        if (this.Pos >= this.Length)
        {
            return "";
        }
        string c = (this.Source[this.Pos]).ToString();
        this.Pos += 1;
        return c;
    }

    public bool AtEnd()
    {
        return this.Pos >= this.Length;
    }

    public string Lookahead(int n)
    {
        return ParableFunctions._Substring(this.Source, this.Pos, this.Pos + n);
    }

    public bool IsMetachar(string c)
    {
        return "|&;()<> \t\n".Contains(c);
    }

    public Token _ReadOperator()
    {
        int start = this.Pos;
        string c = this.Peek();
        if (c == "")
        {
            return null;
        }
        string two = this.Lookahead(2);
        string three = this.Lookahead(3);
        if (three == ";;&")
        {
            this.Pos += 3;
            return new Token(Constants.TOKENTYPE_SEMI_SEMI_AMP, three, start, new List<INode>(), null);
        }
        if (three == "<<-")
        {
            this.Pos += 3;
            return new Token(Constants.TOKENTYPE_LESS_LESS_MINUS, three, start, new List<INode>(), null);
        }
        if (three == "<<<")
        {
            this.Pos += 3;
            return new Token(Constants.TOKENTYPE_LESS_LESS_LESS, three, start, new List<INode>(), null);
        }
        if (three == "&>>")
        {
            this.Pos += 3;
            return new Token(Constants.TOKENTYPE_AMP_GREATER_GREATER, three, start, new List<INode>(), null);
        }
        if (two == "&&")
        {
            this.Pos += 2;
            return new Token(Constants.TOKENTYPE_AND_AND, two, start, new List<INode>(), null);
        }
        if (two == "||")
        {
            this.Pos += 2;
            return new Token(Constants.TOKENTYPE_OR_OR, two, start, new List<INode>(), null);
        }
        if (two == ";;")
        {
            this.Pos += 2;
            return new Token(Constants.TOKENTYPE_SEMI_SEMI, two, start, new List<INode>(), null);
        }
        if (two == ";&")
        {
            this.Pos += 2;
            return new Token(Constants.TOKENTYPE_SEMI_AMP, two, start, new List<INode>(), null);
        }
        if (two == "<<")
        {
            this.Pos += 2;
            return new Token(Constants.TOKENTYPE_LESS_LESS, two, start, new List<INode>(), null);
        }
        if (two == ">>")
        {
            this.Pos += 2;
            return new Token(Constants.TOKENTYPE_GREATER_GREATER, two, start, new List<INode>(), null);
        }
        if (two == "<&")
        {
            this.Pos += 2;
            return new Token(Constants.TOKENTYPE_LESS_AMP, two, start, new List<INode>(), null);
        }
        if (two == ">&")
        {
            this.Pos += 2;
            return new Token(Constants.TOKENTYPE_GREATER_AMP, two, start, new List<INode>(), null);
        }
        if (two == "<>")
        {
            this.Pos += 2;
            return new Token(Constants.TOKENTYPE_LESS_GREATER, two, start, new List<INode>(), null);
        }
        if (two == ">|")
        {
            this.Pos += 2;
            return new Token(Constants.TOKENTYPE_GREATER_PIPE, two, start, new List<INode>(), null);
        }
        if (two == "&>")
        {
            this.Pos += 2;
            return new Token(Constants.TOKENTYPE_AMP_GREATER, two, start, new List<INode>(), null);
        }
        if (two == "|&")
        {
            this.Pos += 2;
            return new Token(Constants.TOKENTYPE_PIPE_AMP, two, start, new List<INode>(), null);
        }
        if (c == ";")
        {
            this.Pos += 1;
            return new Token(Constants.TOKENTYPE_SEMI, c, start, new List<INode>(), null);
        }
        if (c == "|")
        {
            this.Pos += 1;
            return new Token(Constants.TOKENTYPE_PIPE, c, start, new List<INode>(), null);
        }
        if (c == "&")
        {
            this.Pos += 1;
            return new Token(Constants.TOKENTYPE_AMP, c, start, new List<INode>(), null);
        }
        if (c == "(")
        {
            if (this._WordContext == Constants.WORD_CTX_REGEX)
            {
                return null;
            }
            this.Pos += 1;
            return new Token(Constants.TOKENTYPE_LPAREN, c, start, new List<INode>(), null);
        }
        if (c == ")")
        {
            if (this._WordContext == Constants.WORD_CTX_REGEX)
            {
                return null;
            }
            this.Pos += 1;
            return new Token(Constants.TOKENTYPE_RPAREN, c, start, new List<INode>(), null);
        }
        if (c == "<")
        {
            if (this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "(")
            {
                return null;
            }
            this.Pos += 1;
            return new Token(Constants.TOKENTYPE_LESS, c, start, new List<INode>(), null);
        }
        if (c == ">")
        {
            if (this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "(")
            {
                return null;
            }
            this.Pos += 1;
            return new Token(Constants.TOKENTYPE_GREATER, c, start, new List<INode>(), null);
        }
        if (c == "\n")
        {
            this.Pos += 1;
            return new Token(Constants.TOKENTYPE_NEWLINE, c, start, new List<INode>(), null);
        }
        return null;
    }

    public void SkipBlanks()
    {
        while (this.Pos < this.Length)
        {
            string c = (this.Source[this.Pos]).ToString();
            if (c != " " && c != "\t")
            {
                break;
            }
            this.Pos += 1;
        }
    }

    public bool _SkipComment()
    {
        if (this.Pos >= this.Length)
        {
            return false;
        }
        if ((this.Source[this.Pos]).ToString() != "#")
        {
            return false;
        }
        if (this.Quote.InQuotes())
        {
            return false;
        }
        if (this.Pos > 0)
        {
            string prev = (this.Source[this.Pos - 1]).ToString();
            if (!" \t\n;|&(){}".Contains(prev))
            {
                return false;
            }
        }
        while (this.Pos < this.Length && (this.Source[this.Pos]).ToString() != "\n")
        {
            this.Pos += 1;
        }
        return true;
    }

    public (string, bool) _ReadSingleQuote(int start)
    {
        List<string> chars = new List<string> { "'" };
        bool sawNewline = false;
        while (this.Pos < this.Length)
        {
            string c = (this.Source[this.Pos]).ToString();
            if (c == "\n")
            {
                sawNewline = true;
            }
            chars.Add(c);
            this.Pos += 1;
            if (c == "'")
            {
                return (string.Join("", chars), sawNewline);
            }
        }
        throw new ParseError("Unterminated single quote", start, 0);
    }

    public bool _IsWordTerminator(int ctx, string ch, int bracketDepth, int parenDepth)
    {
        if (ctx == Constants.WORD_CTX_REGEX)
        {
            if (ch == "]" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "]")
            {
                return true;
            }
            if (ch == "&" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "&")
            {
                return true;
            }
            if (ch == ")" && parenDepth == 0)
            {
                return true;
            }
            return ParableFunctions._IsWhitespace(ch) && parenDepth == 0;
        }
        if (ctx == Constants.WORD_CTX_COND)
        {
            if (ch == "]" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "]")
            {
                return true;
            }
            if (ch == ")")
            {
                return true;
            }
            if (ch == "&")
            {
                return true;
            }
            if (ch == "|")
            {
                return true;
            }
            if (ch == ";")
            {
                return true;
            }
            if (ParableFunctions._IsRedirectChar(ch) && !(this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "("))
            {
                return true;
            }
            return ParableFunctions._IsWhitespace(ch);
        }
        if (((this._ParserState & Constants.PARSERSTATEFLAGS_PST_EOFTOKEN) != 0) && this._EofToken != "" && ch == this._EofToken && bracketDepth == 0)
        {
            return true;
        }
        if (ParableFunctions._IsRedirectChar(ch) && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "(")
        {
            return false;
        }
        return ParableFunctions._IsMetachar(ch) && bracketDepth == 0;
    }

    public bool _ReadBracketExpression(List<string> chars, List<INode> parts, bool forRegex, int parenDepth)
    {
        if (forRegex)
        {
            int scan = this.Pos + 1;
            if (scan < this.Length && (this.Source[scan]).ToString() == "^")
            {
                scan += 1;
            }
            if (scan < this.Length && (this.Source[scan]).ToString() == "]")
            {
                scan += 1;
            }
            bool bracketWillClose = false;
            while (scan < this.Length)
            {
                string sc = (this.Source[scan]).ToString();
                if (sc == "]" && scan + 1 < this.Length && (this.Source[scan + 1]).ToString() == "]")
                {
                    break;
                }
                if (sc == ")" && parenDepth > 0)
                {
                    break;
                }
                if (sc == "&" && scan + 1 < this.Length && (this.Source[scan + 1]).ToString() == "&")
                {
                    break;
                }
                if (sc == "]")
                {
                    bracketWillClose = true;
                    break;
                }
                if (sc == "[" && scan + 1 < this.Length && (this.Source[scan + 1]).ToString() == ":")
                {
                    scan += 2;
                    while (scan < this.Length && !((this.Source[scan]).ToString() == ":" && scan + 1 < this.Length && (this.Source[scan + 1]).ToString() == "]"))
                    {
                        scan += 1;
                    }
                    if (scan < this.Length)
                    {
                        scan += 2;
                    }
                    continue;
                }
                scan += 1;
            }
            if (!(bracketWillClose))
            {
                return false;
            }
        }
        else
        {
            if (this.Pos + 1 >= this.Length)
            {
                return false;
            }
            string nextCh = (this.Source[this.Pos + 1]).ToString();
            if (ParableFunctions._IsWhitespaceNoNewline(nextCh) || nextCh == "&" || nextCh == "|")
            {
                return false;
            }
        }
        chars.Add(this.Advance());
        if (!(this.AtEnd()) && this.Peek() == "^")
        {
            chars.Add(this.Advance());
        }
        if (!(this.AtEnd()) && this.Peek() == "]")
        {
            chars.Add(this.Advance());
        }
        while (!(this.AtEnd()))
        {
            string c = this.Peek();
            if (c == "]")
            {
                chars.Add(this.Advance());
                break;
            }
            if (c == "[" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == ":")
            {
                chars.Add(this.Advance());
                chars.Add(this.Advance());
                while (!(this.AtEnd()) && !(this.Peek() == ":" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "]"))
                {
                    chars.Add(this.Advance());
                }
                if (!(this.AtEnd()))
                {
                    chars.Add(this.Advance());
                    chars.Add(this.Advance());
                }
            }
            else
            {
                if (!(forRegex) && c == "[" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "=")
                {
                    chars.Add(this.Advance());
                    chars.Add(this.Advance());
                    while (!(this.AtEnd()) && !(this.Peek() == "=" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "]"))
                    {
                        chars.Add(this.Advance());
                    }
                    if (!(this.AtEnd()))
                    {
                        chars.Add(this.Advance());
                        chars.Add(this.Advance());
                    }
                }
                else
                {
                    if (!(forRegex) && c == "[" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == ".")
                    {
                        chars.Add(this.Advance());
                        chars.Add(this.Advance());
                        while (!(this.AtEnd()) && !(this.Peek() == "." && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "]"))
                        {
                            chars.Add(this.Advance());
                        }
                        if (!(this.AtEnd()))
                        {
                            chars.Add(this.Advance());
                            chars.Add(this.Advance());
                        }
                    }
                    else
                    {
                        if (forRegex && c == "$")
                        {
                            this._SyncToParser();
                            if (!(this._Parser._ParseDollarExpansion(chars, parts, false)))
                            {
                                this._SyncFromParser();
                                chars.Add(this.Advance());
                            }
                            else
                            {
                                this._SyncFromParser();
                            }
                        }
                        else
                        {
                            chars.Add(this.Advance());
                        }
                    }
                }
            }
        }
        return true;
    }

    public string _ParseMatchedPair(string openChar, string closeChar, int flags, bool initialWasDollar)
    {
        int start = this.Pos;
        int count = 1;
        List<string> chars = new List<string>();
        bool passNext = false;
        bool wasDollar = initialWasDollar;
        bool wasGtlt = false;
        while (count > 0)
        {
            if (this.AtEnd())
            {
                throw new MatchedPairError(string.Format("unexpected EOF while looking for matching `{0}'", closeChar), start, 0);
            }
            string ch = this.Advance();
            if (((flags & Constants.MATCHEDPAIRFLAGS_DOLBRACE) != 0) && this._DolbraceState == Constants.DOLBRACESTATE_OP)
            {
                if (!"#%^,~:-=?+/".Contains(ch))
                {
                    this._DolbraceState = Constants.DOLBRACESTATE_WORD;
                }
            }
            if (passNext)
            {
                passNext = false;
                chars.Add(ch);
                wasDollar = ch == "$";
                wasGtlt = "<>".Contains(ch);
                continue;
            }
            if (openChar == "'")
            {
                if (ch == closeChar)
                {
                    count -= 1;
                    if (count == 0)
                    {
                        break;
                    }
                }
                if (ch == "\\" && ((flags & Constants.MATCHEDPAIRFLAGS_ALLOWESC) != 0))
                {
                    passNext = true;
                }
                chars.Add(ch);
                wasDollar = false;
                wasGtlt = false;
                continue;
            }
            if (ch == "\\")
            {
                if (!(this.AtEnd()) && this.Peek() == "\n")
                {
                    this.Advance();
                    wasDollar = false;
                    wasGtlt = false;
                    continue;
                }
                passNext = true;
                chars.Add(ch);
                wasDollar = false;
                wasGtlt = false;
                continue;
            }
            if (ch == closeChar)
            {
                count -= 1;
                if (count == 0)
                {
                    break;
                }
                chars.Add(ch);
                wasDollar = false;
                wasGtlt = "<>".Contains(ch);
                continue;
            }
            if (ch == openChar && openChar != closeChar)
            {
                if (!(((flags & Constants.MATCHEDPAIRFLAGS_DOLBRACE) != 0) && openChar == "{"))
                {
                    count += 1;
                }
                chars.Add(ch);
                wasDollar = false;
                wasGtlt = "<>".Contains(ch);
                continue;
            }
            if ("'\"`".Contains(ch) && openChar != closeChar)
            {
                string nested = "";
                if (ch == "'")
                {
                    chars.Add(ch);
                    int quoteFlags = (wasDollar ? (flags | Constants.MATCHEDPAIRFLAGS_ALLOWESC) : flags);
                    nested = this._ParseMatchedPair("'", "'", quoteFlags, false);
                    chars.Add(nested);
                    chars.Add("'");
                    wasDollar = false;
                    wasGtlt = false;
                    continue;
                }
                else
                {
                    if (ch == "\"")
                    {
                        chars.Add(ch);
                        nested = this._ParseMatchedPair("\"", "\"", (flags | Constants.MATCHEDPAIRFLAGS_DQUOTE), false);
                        chars.Add(nested);
                        chars.Add("\"");
                        wasDollar = false;
                        wasGtlt = false;
                        continue;
                    }
                    else
                    {
                        if (ch == "`")
                        {
                            chars.Add(ch);
                            nested = this._ParseMatchedPair("`", "`", flags, false);
                            chars.Add(nested);
                            chars.Add("`");
                            wasDollar = false;
                            wasGtlt = false;
                            continue;
                        }
                    }
                }
            }
            if (ch == "$" && !(this.AtEnd()) && !(((flags & Constants.MATCHEDPAIRFLAGS_EXTGLOB) != 0)))
            {
                string nextCh = this.Peek();
                if (wasDollar)
                {
                    chars.Add(ch);
                    wasDollar = false;
                    wasGtlt = false;
                    continue;
                }
                if (nextCh == "{")
                {
                    if (((flags & Constants.MATCHEDPAIRFLAGS_ARITH) != 0))
                    {
                        int afterBracePos = this.Pos + 1;
                        if (afterBracePos >= this.Length || !(ParableFunctions._IsFunsubChar((this.Source[afterBracePos]).ToString())))
                        {
                            chars.Add(ch);
                            wasDollar = true;
                            wasGtlt = false;
                            continue;
                        }
                    }
                    this.Pos -= 1;
                    this._SyncToParser();
                    bool inDquote = (flags & Constants.MATCHEDPAIRFLAGS_DQUOTE) != 0;
                    (INode paramNode, string paramText) = this._Parser._ParseParamExpansion(inDquote);
                    this._SyncFromParser();
                    if (paramNode != null)
                    {
                        chars.Add(paramText);
                        wasDollar = false;
                        wasGtlt = false;
                    }
                    else
                    {
                        chars.Add(this.Advance());
                        wasDollar = true;
                        wasGtlt = false;
                    }
                    continue;
                }
                else
                {
                    INode arithNode = null;
                    string arithText = "";
                    if (nextCh == "(")
                    {
                        this.Pos -= 1;
                        this._SyncToParser();
                        INode cmdNode = null;
                        string cmdText = "";
                        if (this.Pos + 2 < this.Length && (this.Source[this.Pos + 2]).ToString() == "(")
                        {
                            (arithNode, arithText) = this._Parser._ParseArithmeticExpansion();
                            this._SyncFromParser();
                            if (arithNode != null)
                            {
                                chars.Add(arithText);
                                wasDollar = false;
                                wasGtlt = false;
                            }
                            else
                            {
                                this._SyncToParser();
                                (cmdNode, cmdText) = this._Parser._ParseCommandSubstitution();
                                this._SyncFromParser();
                                if (cmdNode != null)
                                {
                                    chars.Add(cmdText);
                                    wasDollar = false;
                                    wasGtlt = false;
                                }
                                else
                                {
                                    chars.Add(this.Advance());
                                    chars.Add(this.Advance());
                                    wasDollar = false;
                                    wasGtlt = false;
                                }
                            }
                        }
                        else
                        {
                            (cmdNode, cmdText) = this._Parser._ParseCommandSubstitution();
                            this._SyncFromParser();
                            if (cmdNode != null)
                            {
                                chars.Add(cmdText);
                                wasDollar = false;
                                wasGtlt = false;
                            }
                            else
                            {
                                chars.Add(this.Advance());
                                chars.Add(this.Advance());
                                wasDollar = false;
                                wasGtlt = false;
                            }
                        }
                        continue;
                    }
                    else
                    {
                        if (nextCh == "[")
                        {
                            this.Pos -= 1;
                            this._SyncToParser();
                            (arithNode, arithText) = this._Parser._ParseDeprecatedArithmetic();
                            this._SyncFromParser();
                            if (arithNode != null)
                            {
                                chars.Add(arithText);
                                wasDollar = false;
                                wasGtlt = false;
                            }
                            else
                            {
                                chars.Add(this.Advance());
                                wasDollar = true;
                                wasGtlt = false;
                            }
                            continue;
                        }
                    }
                }
            }
            if (ch == "(" && wasGtlt && ((flags & (Constants.MATCHEDPAIRFLAGS_DOLBRACE | Constants.MATCHEDPAIRFLAGS_ARRAYSUB)) != 0))
            {
                string direction = chars[chars.Count - 1];
                chars = chars.GetRange(0, chars.Count - 1);
                this.Pos -= 1;
                this._SyncToParser();
                (INode procsubNode, string procsubText) = this._Parser._ParseProcessSubstitution();
                this._SyncFromParser();
                if (procsubNode != null)
                {
                    chars.Add(procsubText);
                    wasDollar = false;
                    wasGtlt = false;
                }
                else
                {
                    chars.Add(direction);
                    chars.Add(this.Advance());
                    wasDollar = false;
                    wasGtlt = false;
                }
                continue;
            }
            chars.Add(ch);
            wasDollar = ch == "$";
            wasGtlt = "<>".Contains(ch);
        }
        return string.Join("", chars);
    }

    public string _CollectParamArgument(int flags, bool wasDollar)
    {
        return this._ParseMatchedPair("{", "}", (flags | Constants.MATCHEDPAIRFLAGS_DOLBRACE), wasDollar);
    }

    public Word _ReadWordInternal(int ctx, bool atCommandStart, bool inArrayLiteral, bool inAssignBuiltin)
    {
        int start = this.Pos;
        List<string> chars = new List<string>();
        List<INode> parts = new List<INode>();
        int bracketDepth = 0;
        int bracketStartPos = -1;
        bool seenEquals = false;
        int parenDepth = 0;
        while (!(this.AtEnd()))
        {
            string ch = this.Peek();
            if (ctx == Constants.WORD_CTX_REGEX)
            {
                if (ch == "\\" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "\n")
                {
                    this.Advance();
                    this.Advance();
                    continue;
                }
            }
            if (ctx != Constants.WORD_CTX_NORMAL && this._IsWordTerminator(ctx, ch, bracketDepth, parenDepth))
            {
                break;
            }
            if (ctx == Constants.WORD_CTX_NORMAL && ch == "[")
            {
                if (bracketDepth > 0)
                {
                    bracketDepth += 1;
                    chars.Add(this.Advance());
                    continue;
                }
                if ((chars.Count > 0) && atCommandStart && !(seenEquals) && ParableFunctions._IsArrayAssignmentPrefix(chars))
                {
                    string prevChar = chars[chars.Count - 1];
                    if ((prevChar.Length > 0 && prevChar.All(char.IsLetterOrDigit)) || prevChar == "_")
                    {
                        bracketStartPos = this.Pos;
                        bracketDepth += 1;
                        chars.Add(this.Advance());
                        continue;
                    }
                }
                if (!((chars.Count > 0)) && !(seenEquals) && inArrayLiteral)
                {
                    bracketStartPos = this.Pos;
                    bracketDepth += 1;
                    chars.Add(this.Advance());
                    continue;
                }
            }
            if (ctx == Constants.WORD_CTX_NORMAL && ch == "]" && bracketDepth > 0)
            {
                bracketDepth -= 1;
                chars.Add(this.Advance());
                continue;
            }
            if (ctx == Constants.WORD_CTX_NORMAL && ch == "=" && bracketDepth == 0)
            {
                seenEquals = true;
            }
            if (ctx == Constants.WORD_CTX_REGEX && ch == "(")
            {
                parenDepth += 1;
                chars.Add(this.Advance());
                continue;
            }
            if (ctx == Constants.WORD_CTX_REGEX && ch == ")")
            {
                if (parenDepth > 0)
                {
                    parenDepth -= 1;
                    chars.Add(this.Advance());
                    continue;
                }
                break;
            }
            if ((ctx == Constants.WORD_CTX_COND || ctx == Constants.WORD_CTX_REGEX) && ch == "[")
            {
                bool forRegex = ctx == Constants.WORD_CTX_REGEX;
                if (this._ReadBracketExpression(chars, parts, forRegex, parenDepth))
                {
                    continue;
                }
                chars.Add(this.Advance());
                continue;
            }
            string content = "";
            if (ctx == Constants.WORD_CTX_COND && ch == "(")
            {
                if (this._Extglob && (chars.Count > 0) && ParableFunctions._IsExtglobPrefix(chars[chars.Count - 1]))
                {
                    chars.Add(this.Advance());
                    content = this._ParseMatchedPair("(", ")", Constants.MATCHEDPAIRFLAGS_EXTGLOB, false);
                    chars.Add(content);
                    chars.Add(")");
                    continue;
                }
                else
                {
                    break;
                }
            }
            if (ctx == Constants.WORD_CTX_REGEX && ParableFunctions._IsWhitespace(ch) && parenDepth > 0)
            {
                chars.Add(this.Advance());
                continue;
            }
            if (ch == "'")
            {
                this.Advance();
                bool trackNewline = ctx == Constants.WORD_CTX_NORMAL;
                (content, bool sawNewline) = this._ReadSingleQuote(start);
                chars.Add(content);
                if (trackNewline && sawNewline && this._Parser != null)
                {
                    this._Parser._SawNewlineInSingleQuote = true;
                }
                continue;
            }
            INode cmdsubResult0 = null;
            string cmdsubResult1 = "";
            if (ch == "\"")
            {
                this.Advance();
                if (ctx == Constants.WORD_CTX_NORMAL)
                {
                    chars.Add("\"");
                    bool inSingleInDquote = false;
                    while (!(this.AtEnd()) && (inSingleInDquote || this.Peek() != "\""))
                    {
                        string c = this.Peek();
                        if (inSingleInDquote)
                        {
                            chars.Add(this.Advance());
                            if (c == "'")
                            {
                                inSingleInDquote = false;
                            }
                            continue;
                        }
                        if (c == "\\" && this.Pos + 1 < this.Length)
                        {
                            string nextC = (this.Source[this.Pos + 1]).ToString();
                            if (nextC == "\n")
                            {
                                this.Advance();
                                this.Advance();
                            }
                            else
                            {
                                chars.Add(this.Advance());
                                chars.Add(this.Advance());
                            }
                        }
                        else
                        {
                            if (c == "$")
                            {
                                this._SyncToParser();
                                if (!(this._Parser._ParseDollarExpansion(chars, parts, true)))
                                {
                                    this._SyncFromParser();
                                    chars.Add(this.Advance());
                                }
                                else
                                {
                                    this._SyncFromParser();
                                }
                            }
                            else
                            {
                                if (c == "`")
                                {
                                    this._SyncToParser();
                                    (cmdsubResult0, cmdsubResult1) = this._Parser._ParseBacktickSubstitution();
                                    this._SyncFromParser();
                                    if (cmdsubResult0 != null)
                                    {
                                        parts.Add(cmdsubResult0);
                                        chars.Add(cmdsubResult1);
                                    }
                                    else
                                    {
                                        chars.Add(this.Advance());
                                    }
                                }
                                else
                                {
                                    chars.Add(this.Advance());
                                }
                            }
                        }
                    }
                    if (this.AtEnd())
                    {
                        throw new ParseError("Unterminated double quote", start, 0);
                    }
                    chars.Add(this.Advance());
                }
                else
                {
                    bool handleLineContinuation = ctx == Constants.WORD_CTX_COND;
                    this._SyncToParser();
                    this._Parser._ScanDoubleQuote(chars, parts, start, handleLineContinuation);
                    this._SyncFromParser();
                }
                continue;
            }
            if (ch == "\\" && this.Pos + 1 < this.Length)
            {
                string nextCh = (this.Source[this.Pos + 1]).ToString();
                if (ctx != Constants.WORD_CTX_REGEX && nextCh == "\n")
                {
                    this.Advance();
                    this.Advance();
                }
                else
                {
                    chars.Add(this.Advance());
                    chars.Add(this.Advance());
                }
                continue;
            }
            if (ctx != Constants.WORD_CTX_REGEX && ch == "$" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "'")
            {
                (INode ansiResult0, string ansiResult1) = this._ReadAnsiCQuote();
                if (ansiResult0 != null)
                {
                    parts.Add(ansiResult0);
                    chars.Add(ansiResult1);
                }
                else
                {
                    chars.Add(this.Advance());
                }
                continue;
            }
            if (ctx != Constants.WORD_CTX_REGEX && ch == "$" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "\"")
            {
                (INode localeResult0, string localeResult1, List<INode> localeResult2) = this._ReadLocaleString();
                if (localeResult0 != null)
                {
                    parts.Add(localeResult0);
                    parts.AddRange(localeResult2);
                    chars.Add(localeResult1);
                }
                else
                {
                    chars.Add(this.Advance());
                }
                continue;
            }
            if (ch == "$")
            {
                this._SyncToParser();
                if (!(this._Parser._ParseDollarExpansion(chars, parts, false)))
                {
                    this._SyncFromParser();
                    chars.Add(this.Advance());
                }
                else
                {
                    this._SyncFromParser();
                    if (this._Extglob && ctx == Constants.WORD_CTX_NORMAL && (chars.Count > 0) && chars[chars.Count - 1].Length == 2 && (chars[chars.Count - 1][0]).ToString() == "$" && "?*@".Contains((chars[chars.Count - 1][1]).ToString()) && !(this.AtEnd()) && this.Peek() == "(")
                    {
                        chars.Add(this.Advance());
                        content = this._ParseMatchedPair("(", ")", Constants.MATCHEDPAIRFLAGS_EXTGLOB, false);
                        chars.Add(content);
                        chars.Add(")");
                    }
                }
                continue;
            }
            if (ctx != Constants.WORD_CTX_REGEX && ch == "`")
            {
                this._SyncToParser();
                (cmdsubResult0, cmdsubResult1) = this._Parser._ParseBacktickSubstitution();
                this._SyncFromParser();
                if (cmdsubResult0 != null)
                {
                    parts.Add(cmdsubResult0);
                    chars.Add(cmdsubResult1);
                }
                else
                {
                    chars.Add(this.Advance());
                }
                continue;
            }
            if (ctx != Constants.WORD_CTX_REGEX && ParableFunctions._IsRedirectChar(ch) && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "(")
            {
                this._SyncToParser();
                (INode procsubResult0, string procsubResult1) = this._Parser._ParseProcessSubstitution();
                this._SyncFromParser();
                if (procsubResult0 != null)
                {
                    parts.Add(procsubResult0);
                    chars.Add(procsubResult1);
                }
                else
                {
                    if ((!string.IsNullOrEmpty(procsubResult1)))
                    {
                        chars.Add(procsubResult1);
                    }
                    else
                    {
                        chars.Add(this.Advance());
                        if (ctx == Constants.WORD_CTX_NORMAL)
                        {
                            chars.Add(this.Advance());
                        }
                    }
                }
                continue;
            }
            if (ctx == Constants.WORD_CTX_NORMAL && ch == "(" && (chars.Count > 0) && bracketDepth == 0)
            {
                bool isArrayAssign = false;
                if (chars.Count >= 3 && chars[chars.Count - 2] == "+" && chars[chars.Count - 1] == "=")
                {
                    isArrayAssign = ParableFunctions._IsArrayAssignmentPrefix(chars.GetRange(0, chars.Count - 2));
                }
                else
                {
                    if (chars[chars.Count - 1] == "=" && chars.Count >= 2)
                    {
                        isArrayAssign = ParableFunctions._IsArrayAssignmentPrefix(chars.GetRange(0, chars.Count - 1));
                    }
                }
                if (isArrayAssign && (atCommandStart || inAssignBuiltin))
                {
                    this._SyncToParser();
                    (INode arrayResult0, string arrayResult1) = this._Parser._ParseArrayLiteral();
                    this._SyncFromParser();
                    if (arrayResult0 != null)
                    {
                        parts.Add(arrayResult0);
                        chars.Add(arrayResult1);
                    }
                    else
                    {
                        break;
                    }
                    continue;
                }
            }
            if (this._Extglob && ctx == Constants.WORD_CTX_NORMAL && ParableFunctions._IsExtglobPrefix(ch) && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "(")
            {
                chars.Add(this.Advance());
                chars.Add(this.Advance());
                content = this._ParseMatchedPair("(", ")", Constants.MATCHEDPAIRFLAGS_EXTGLOB, false);
                chars.Add(content);
                chars.Add(")");
                continue;
            }
            if (ctx == Constants.WORD_CTX_NORMAL && ((this._ParserState & Constants.PARSERSTATEFLAGS_PST_EOFTOKEN) != 0) && this._EofToken != "" && ch == this._EofToken && bracketDepth == 0)
            {
                if (!((chars.Count > 0)))
                {
                    chars.Add(this.Advance());
                }
                break;
            }
            if (ctx == Constants.WORD_CTX_NORMAL && ParableFunctions._IsMetachar(ch) && bracketDepth == 0)
            {
                break;
            }
            chars.Add(this.Advance());
        }
        if (bracketDepth > 0 && bracketStartPos != -1 && this.AtEnd())
        {
            throw new MatchedPairError("unexpected EOF looking for `]'", bracketStartPos, 0);
        }
        if (!((chars.Count > 0)))
        {
            return null;
        }
        if ((parts.Count > 0))
        {
            return new Word(string.Join("", chars), parts, "word");
        }
        return new Word(string.Join("", chars), new List<INode>(), "word");
    }

    public Token _ReadWord()
    {
        int start = this.Pos;
        if (this.Pos >= this.Length)
        {
            return null;
        }
        string c = this.Peek();
        if (c == "")
        {
            return null;
        }
        bool isProcsub = (c == "<" || c == ">") && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "(";
        bool isRegexParen = this._WordContext == Constants.WORD_CTX_REGEX && (c == "(" || c == ")");
        if (this.IsMetachar(c) && !(isProcsub) && !(isRegexParen))
        {
            return null;
        }
        Word word = this._ReadWordInternal(this._WordContext, this._AtCommandStart, this._InArrayLiteral, this._InAssignBuiltin);
        if (word == null)
        {
            return null;
        }
        return new Token(Constants.TOKENTYPE_WORD, word.Value, start, new List<INode>(), word);
    }

    public Token NextToken()
    {
        Token tok = null;
        if (this._TokenCache != null)
        {
            tok = this._TokenCache;
            this._TokenCache = null;
            this._LastReadToken = tok;
            return tok;
        }
        this.SkipBlanks();
        if (this.AtEnd())
        {
            tok = new Token(Constants.TOKENTYPE_EOF, "", this.Pos, new List<INode>(), null);
            this._LastReadToken = tok;
            return tok;
        }
        if (this._EofToken != "" && this.Peek() == this._EofToken && !(((this._ParserState & Constants.PARSERSTATEFLAGS_PST_CASEPAT) != 0)) && !(((this._ParserState & Constants.PARSERSTATEFLAGS_PST_EOFTOKEN) != 0)))
        {
            tok = new Token(Constants.TOKENTYPE_EOF, "", this.Pos, new List<INode>(), null);
            this._LastReadToken = tok;
            return tok;
        }
        while (this._SkipComment())
        {
            this.SkipBlanks();
            if (this.AtEnd())
            {
                tok = new Token(Constants.TOKENTYPE_EOF, "", this.Pos, new List<INode>(), null);
                this._LastReadToken = tok;
                return tok;
            }
            if (this._EofToken != "" && this.Peek() == this._EofToken && !(((this._ParserState & Constants.PARSERSTATEFLAGS_PST_CASEPAT) != 0)) && !(((this._ParserState & Constants.PARSERSTATEFLAGS_PST_EOFTOKEN) != 0)))
            {
                tok = new Token(Constants.TOKENTYPE_EOF, "", this.Pos, new List<INode>(), null);
                this._LastReadToken = tok;
                return tok;
            }
        }
        tok = this._ReadOperator();
        if (tok != null)
        {
            this._LastReadToken = tok;
            return tok;
        }
        tok = this._ReadWord();
        if (tok != null)
        {
            this._LastReadToken = tok;
            return tok;
        }
        tok = new Token(Constants.TOKENTYPE_EOF, "", this.Pos, new List<INode>(), null);
        this._LastReadToken = tok;
        return tok;
    }

    public Token PeekToken()
    {
        if (this._TokenCache == null)
        {
            Token savedLast = this._LastReadToken;
            this._TokenCache = this.NextToken();
            this._LastReadToken = savedLast;
        }
        return this._TokenCache;
    }

    public (INode, string) _ReadAnsiCQuote()
    {
        if (this.AtEnd() || this.Peek() != "$")
        {
            return (null, "");
        }
        if (this.Pos + 1 >= this.Length || (this.Source[this.Pos + 1]).ToString() != "'")
        {
            return (null, "");
        }
        int start = this.Pos;
        this.Advance();
        this.Advance();
        List<string> contentChars = new List<string>();
        bool foundClose = false;
        while (!(this.AtEnd()))
        {
            string ch = this.Peek();
            if (ch == "'")
            {
                this.Advance();
                foundClose = true;
                break;
            }
            else
            {
                if (ch == "\\")
                {
                    contentChars.Add(this.Advance());
                    if (!(this.AtEnd()))
                    {
                        contentChars.Add(this.Advance());
                    }
                }
                else
                {
                    contentChars.Add(this.Advance());
                }
            }
        }
        if (!(foundClose))
        {
            throw new MatchedPairError("unexpected EOF while looking for matching `''", start, 0);
        }
        string text = ParableFunctions._Substring(this.Source, start, this.Pos);
        string content = string.Join("", contentChars);
        AnsiCQuote node = new AnsiCQuote(content, "ansi-c");
        return (node, text);
    }

    public void _SyncToParser()
    {
        if (this._Parser != null)
        {
            this._Parser.Pos = this.Pos;
        }
    }

    public void _SyncFromParser()
    {
        if (this._Parser != null)
        {
            this.Pos = this._Parser.Pos;
        }
    }

    public (INode, string, List<INode>) _ReadLocaleString()
    {
        if (this.AtEnd() || this.Peek() != "$")
        {
            return (null, "", new List<INode>());
        }
        if (this.Pos + 1 >= this.Length || (this.Source[this.Pos + 1]).ToString() != "\"")
        {
            return (null, "", new List<INode>());
        }
        int start = this.Pos;
        this.Advance();
        this.Advance();
        List<string> contentChars = new List<string>();
        List<INode> innerParts = new List<INode>();
        bool foundClose = false;
        while (!(this.AtEnd()))
        {
            string ch = this.Peek();
            if (ch == "\"")
            {
                this.Advance();
                foundClose = true;
                break;
            }
            else
            {
                if (ch == "\\" && this.Pos + 1 < this.Length)
                {
                    string nextCh = (this.Source[this.Pos + 1]).ToString();
                    if (nextCh == "\n")
                    {
                        this.Advance();
                        this.Advance();
                    }
                    else
                    {
                        contentChars.Add(this.Advance());
                        contentChars.Add(this.Advance());
                    }
                }
                else
                {
                    INode cmdsubNode = null;
                    string cmdsubText = "";
                    if (ch == "$" && this.Pos + 2 < this.Length && (this.Source[this.Pos + 1]).ToString() == "(" && (this.Source[this.Pos + 2]).ToString() == "(")
                    {
                        this._SyncToParser();
                        (INode arithNode, string arithText) = this._Parser._ParseArithmeticExpansion();
                        this._SyncFromParser();
                        if (arithNode != null)
                        {
                            innerParts.Add(arithNode);
                            contentChars.Add(arithText);
                        }
                        else
                        {
                            this._SyncToParser();
                            (cmdsubNode, cmdsubText) = this._Parser._ParseCommandSubstitution();
                            this._SyncFromParser();
                            if (cmdsubNode != null)
                            {
                                innerParts.Add(cmdsubNode);
                                contentChars.Add(cmdsubText);
                            }
                            else
                            {
                                contentChars.Add(this.Advance());
                            }
                        }
                    }
                    else
                    {
                        if (ParableFunctions._IsExpansionStart(this.Source, this.Pos, "$("))
                        {
                            this._SyncToParser();
                            (cmdsubNode, cmdsubText) = this._Parser._ParseCommandSubstitution();
                            this._SyncFromParser();
                            if (cmdsubNode != null)
                            {
                                innerParts.Add(cmdsubNode);
                                contentChars.Add(cmdsubText);
                            }
                            else
                            {
                                contentChars.Add(this.Advance());
                            }
                        }
                        else
                        {
                            if (ch == "$")
                            {
                                this._SyncToParser();
                                (INode paramNode, string paramText) = this._Parser._ParseParamExpansion(false);
                                this._SyncFromParser();
                                if (paramNode != null)
                                {
                                    innerParts.Add(paramNode);
                                    contentChars.Add(paramText);
                                }
                                else
                                {
                                    contentChars.Add(this.Advance());
                                }
                            }
                            else
                            {
                                if (ch == "`")
                                {
                                    this._SyncToParser();
                                    (cmdsubNode, cmdsubText) = this._Parser._ParseBacktickSubstitution();
                                    this._SyncFromParser();
                                    if (cmdsubNode != null)
                                    {
                                        innerParts.Add(cmdsubNode);
                                        contentChars.Add(cmdsubText);
                                    }
                                    else
                                    {
                                        contentChars.Add(this.Advance());
                                    }
                                }
                                else
                                {
                                    contentChars.Add(this.Advance());
                                }
                            }
                        }
                    }
                }
            }
        }
        if (!(foundClose))
        {
            this.Pos = start;
            return (null, "", new List<INode>());
        }
        string content = string.Join("", contentChars);
        string text = "$\"" + content + "\"";
        return (new LocaleString(content, "locale"), text, innerParts);
    }

    public void _UpdateDolbraceForOp(string op, bool hasParam)
    {
        if (this._DolbraceState == Constants.DOLBRACESTATE_NONE)
        {
            return;
        }
        if (op == "" || op.Length == 0)
        {
            return;
        }
        string firstChar = (op[0]).ToString();
        if (this._DolbraceState == Constants.DOLBRACESTATE_PARAM && hasParam)
        {
            if ("%#^,".Contains(firstChar))
            {
                this._DolbraceState = Constants.DOLBRACESTATE_QUOTE;
                return;
            }
            if (firstChar == "/")
            {
                this._DolbraceState = Constants.DOLBRACESTATE_QUOTE2;
                return;
            }
        }
        if (this._DolbraceState == Constants.DOLBRACESTATE_PARAM)
        {
            if ("#%^,~:-=?+/".Contains(firstChar))
            {
                this._DolbraceState = Constants.DOLBRACESTATE_OP;
            }
        }
    }

    public string _ConsumeParamOperator()
    {
        if (this.AtEnd())
        {
            return "";
        }
        string ch = this.Peek();
        string nextCh = "";
        if (ch == ":")
        {
            this.Advance();
            if (this.AtEnd())
            {
                return ":";
            }
            nextCh = this.Peek();
            if (ParableFunctions._IsSimpleParamOp(nextCh))
            {
                this.Advance();
                return ":" + nextCh;
            }
            return ":";
        }
        if (ParableFunctions._IsSimpleParamOp(ch))
        {
            this.Advance();
            return ch;
        }
        if (ch == "#")
        {
            this.Advance();
            if (!(this.AtEnd()) && this.Peek() == "#")
            {
                this.Advance();
                return "##";
            }
            return "#";
        }
        if (ch == "%")
        {
            this.Advance();
            if (!(this.AtEnd()) && this.Peek() == "%")
            {
                this.Advance();
                return "%%";
            }
            return "%";
        }
        if (ch == "/")
        {
            this.Advance();
            if (!(this.AtEnd()))
            {
                nextCh = this.Peek();
                if (nextCh == "/")
                {
                    this.Advance();
                    return "//";
                }
                else
                {
                    if (nextCh == "#")
                    {
                        this.Advance();
                        return "/#";
                    }
                    else
                    {
                        if (nextCh == "%")
                        {
                            this.Advance();
                            return "/%";
                        }
                    }
                }
            }
            return "/";
        }
        if (ch == "^")
        {
            this.Advance();
            if (!(this.AtEnd()) && this.Peek() == "^")
            {
                this.Advance();
                return "^^";
            }
            return "^";
        }
        if (ch == ",")
        {
            this.Advance();
            if (!(this.AtEnd()) && this.Peek() == ",")
            {
                this.Advance();
                return ",,";
            }
            return ",";
        }
        if (ch == "@")
        {
            this.Advance();
            return "@";
        }
        return "";
    }

    public bool _ParamSubscriptHasClose(int startPos)
    {
        int depth = 1;
        int i = startPos + 1;
        QuoteState quote = ParableFunctions.NewQuoteState();
        while (i < this.Length)
        {
            string c = (this.Source[i]).ToString();
            if (quote.Single)
            {
                if (c == "'")
                {
                    quote.Single = false;
                }
                i += 1;
                continue;
            }
            if (quote.Double)
            {
                if (c == "\\" && i + 1 < this.Length)
                {
                    i += 2;
                    continue;
                }
                if (c == "\"")
                {
                    quote.Double = false;
                }
                i += 1;
                continue;
            }
            if (c == "'")
            {
                quote.Single = true;
                i += 1;
                continue;
            }
            if (c == "\"")
            {
                quote.Double = true;
                i += 1;
                continue;
            }
            if (c == "\\")
            {
                i += 2;
                continue;
            }
            if (c == "}")
            {
                return false;
            }
            if (c == "[")
            {
                depth += 1;
            }
            else
            {
                if (c == "]")
                {
                    depth -= 1;
                    if (depth == 0)
                    {
                        return true;
                    }
                }
            }
            i += 1;
        }
        return false;
    }

    public string _ConsumeParamName()
    {
        if (this.AtEnd())
        {
            return "";
        }
        string ch = this.Peek();
        if (ParableFunctions._IsSpecialParam(ch))
        {
            if (ch == "$" && this.Pos + 1 < this.Length && "{'\"".Contains((this.Source[this.Pos + 1]).ToString()))
            {
                return "";
            }
            this.Advance();
            return ch;
        }
        if ((ch.Length > 0 && ch.All(char.IsDigit)))
        {
            List<string> nameChars = new List<string>();
            while (!(this.AtEnd()) && (this.Peek().Length > 0 && this.Peek().All(char.IsDigit)))
            {
                nameChars.Add(this.Advance());
            }
            return string.Join("", nameChars);
        }
        if ((ch.Length > 0 && ch.All(char.IsLetter)) || ch == "_")
        {
            List<string> nameChars = new List<string>();
            while (!(this.AtEnd()))
            {
                string c = this.Peek();
                if ((c.Length > 0 && c.All(char.IsLetterOrDigit)) || c == "_")
                {
                    nameChars.Add(this.Advance());
                }
                else
                {
                    if (c == "[")
                    {
                        if (!(this._ParamSubscriptHasClose(this.Pos)))
                        {
                            break;
                        }
                        nameChars.Add(this.Advance());
                        string content = this._ParseMatchedPair("[", "]", Constants.MATCHEDPAIRFLAGS_ARRAYSUB, false);
                        nameChars.Add(content);
                        nameChars.Add("]");
                        break;
                    }
                    else
                    {
                        break;
                    }
                }
            }
            if ((nameChars.Count > 0))
            {
                return string.Join("", nameChars);
            }
            else
            {
                return "";
            }
        }
        return "";
    }

    public (INode, string) _ReadParamExpansion(bool inDquote)
    {
        if (this.AtEnd() || this.Peek() != "$")
        {
            return (null, "");
        }
        int start = this.Pos;
        this.Advance();
        if (this.AtEnd())
        {
            this.Pos = start;
            return (null, "");
        }
        string ch = this.Peek();
        if (ch == "{")
        {
            this.Advance();
            return this._ReadBracedParam(start, inDquote);
        }
        string text = "";
        if (ParableFunctions._IsSpecialParamUnbraced(ch) || ParableFunctions._IsDigit(ch) || ch == "#")
        {
            this.Advance();
            text = ParableFunctions._Substring(this.Source, start, this.Pos);
            return (new ParamExpansion(ch, "", "", "param"), text);
        }
        if ((ch.Length > 0 && ch.All(char.IsLetter)) || ch == "_")
        {
            int nameStart = this.Pos;
            while (!(this.AtEnd()))
            {
                string c = this.Peek();
                if ((c.Length > 0 && c.All(char.IsLetterOrDigit)) || c == "_")
                {
                    this.Advance();
                }
                else
                {
                    break;
                }
            }
            string name = ParableFunctions._Substring(this.Source, nameStart, this.Pos);
            text = ParableFunctions._Substring(this.Source, start, this.Pos);
            return (new ParamExpansion(name, "", "", "param"), text);
        }
        this.Pos = start;
        return (null, "");
    }

    public (INode, string) _ReadBracedParam(int start, bool inDquote)
    {
        if (this.AtEnd())
        {
            throw new MatchedPairError("unexpected EOF looking for `}'", start, 0);
        }
        int savedDolbrace = this._DolbraceState;
        this._DolbraceState = Constants.DOLBRACESTATE_PARAM;
        string ch = this.Peek();
        if (ParableFunctions._IsFunsubChar(ch))
        {
            this._DolbraceState = savedDolbrace;
            return this._ReadFunsub(start);
        }
        string param = "";
        string text = "";
        if (ch == "#")
        {
            this.Advance();
            param = this._ConsumeParamName();
            if ((!string.IsNullOrEmpty(param)) && !(this.AtEnd()) && this.Peek() == "}")
            {
                this.Advance();
                text = ParableFunctions._Substring(this.Source, start, this.Pos);
                this._DolbraceState = savedDolbrace;
                return (new ParamLength(param, "param-len"), text);
            }
            this.Pos = start + 2;
        }
        string op = "";
        string arg = "";
        if (ch == "!")
        {
            this.Advance();
            while (!(this.AtEnd()) && ParableFunctions._IsWhitespaceNoNewline(this.Peek()))
            {
                this.Advance();
            }
            param = this._ConsumeParamName();
            if ((!string.IsNullOrEmpty(param)))
            {
                while (!(this.AtEnd()) && ParableFunctions._IsWhitespaceNoNewline(this.Peek()))
                {
                    this.Advance();
                }
                if (!(this.AtEnd()) && this.Peek() == "}")
                {
                    this.Advance();
                    text = ParableFunctions._Substring(this.Source, start, this.Pos);
                    this._DolbraceState = savedDolbrace;
                    return (new ParamIndirect(param, "", "", "param-indirect"), text);
                }
                if (!(this.AtEnd()) && ParableFunctions._IsAtOrStar(this.Peek()))
                {
                    string suffix = this.Advance();
                    string trailing = this._ParseMatchedPair("{", "}", Constants.MATCHEDPAIRFLAGS_DOLBRACE, false);
                    text = ParableFunctions._Substring(this.Source, start, this.Pos);
                    this._DolbraceState = savedDolbrace;
                    return (new ParamIndirect(param + suffix + trailing, "", "", "param-indirect"), text);
                }
                op = this._ConsumeParamOperator();
                if (op == "" && !(this.AtEnd()) && !"}\"'`".Contains(this.Peek()))
                {
                    op = this.Advance();
                }
                if (op != "" && !"\"'`".Contains(op))
                {
                    arg = this._ParseMatchedPair("{", "}", Constants.MATCHEDPAIRFLAGS_DOLBRACE, false);
                    text = ParableFunctions._Substring(this.Source, start, this.Pos);
                    this._DolbraceState = savedDolbrace;
                    return (new ParamIndirect(param, op, arg, "param-indirect"), text);
                }
                if (this.AtEnd())
                {
                    this._DolbraceState = savedDolbrace;
                    throw new MatchedPairError("unexpected EOF looking for `}'", start, 0);
                }
                this.Pos = start + 2;
            }
            else
            {
                this.Pos = start + 2;
            }
        }
        param = this._ConsumeParamName();
        if (!((!string.IsNullOrEmpty(param))))
        {
            if (!(this.AtEnd()) && ("-=+?".Contains(this.Peek()) || this.Peek() == ":" && this.Pos + 1 < this.Length && ParableFunctions._IsSimpleParamOp((this.Source[this.Pos + 1]).ToString())))
            {
                param = "";
            }
            else
            {
                string content = this._ParseMatchedPair("{", "}", Constants.MATCHEDPAIRFLAGS_DOLBRACE, false);
                text = "${" + content + "}";
                this._DolbraceState = savedDolbrace;
                return (new ParamExpansion(content, "", "", "param"), text);
            }
        }
        if (this.AtEnd())
        {
            this._DolbraceState = savedDolbrace;
            throw new MatchedPairError("unexpected EOF looking for `}'", start, 0);
        }
        if (this.Peek() == "}")
        {
            this.Advance();
            text = ParableFunctions._Substring(this.Source, start, this.Pos);
            this._DolbraceState = savedDolbrace;
            return (new ParamExpansion(param, "", "", "param"), text);
        }
        op = this._ConsumeParamOperator();
        if (op == "")
        {
            if (!(this.AtEnd()) && this.Peek() == "$" && this.Pos + 1 < this.Length && ((this.Source[this.Pos + 1]).ToString() == "\"" || (this.Source[this.Pos + 1]).ToString() == "'"))
            {
                int dollarCount = 1 + ParableFunctions._CountConsecutiveDollarsBefore(this.Source, this.Pos);
                if (dollarCount % 2 == 1)
                {
                    op = "";
                }
                else
                {
                    op = this.Advance();
                }
            }
            else
            {
                if (!(this.AtEnd()) && this.Peek() == "`")
                {
                    int backtickPos = this.Pos;
                    this.Advance();
                    while (!(this.AtEnd()) && this.Peek() != "`")
                    {
                        string bc = this.Peek();
                        if (bc == "\\" && this.Pos + 1 < this.Length)
                        {
                            string nextC = (this.Source[this.Pos + 1]).ToString();
                            if (ParableFunctions._IsEscapeCharInBacktick(nextC))
                            {
                                this.Advance();
                            }
                        }
                        this.Advance();
                    }
                    if (this.AtEnd())
                    {
                        this._DolbraceState = savedDolbrace;
                        throw new ParseError("Unterminated backtick", backtickPos, 0);
                    }
                    this.Advance();
                    op = "`";
                }
                else
                {
                    if (!(this.AtEnd()) && this.Peek() == "$" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "{")
                    {
                        op = "";
                    }
                    else
                    {
                        if (!(this.AtEnd()) && (this.Peek() == "'" || this.Peek() == "\""))
                        {
                            op = "";
                        }
                        else
                        {
                            if (!(this.AtEnd()) && this.Peek() == "\\")
                            {
                                op = this.Advance();
                                if (!(this.AtEnd()))
                                {
                                    op += this.Advance();
                                }
                            }
                            else
                            {
                                op = this.Advance();
                            }
                        }
                    }
                }
            }
        }
        this._UpdateDolbraceForOp(op, param.Length > 0);
        try
        {
            int flags = (inDquote ? Constants.MATCHEDPAIRFLAGS_DQUOTE : Constants.MATCHEDPAIRFLAGS_NONE);
            bool paramEndsWithDollar = param != "" && param.EndsWith("$");
            arg = this._CollectParamArgument(flags, paramEndsWithDollar);
        } catch (MatchedPairError)
        {
            this._DolbraceState = savedDolbrace;
            throw;
        }
        if ((op == "<" || op == ">") && arg.StartsWith("(") && arg.EndsWith(")"))
        {
            string inner = arg.Substring(1, (arg.Length - 1) - (1));
            try
            {
                Parser subParser = ParableFunctions.NewParser(inner, true, this._Parser._Extglob);
                INode parsed = subParser.ParseList(true);
                if (parsed != null && subParser.AtEnd())
                {
                    string formatted = ParableFunctions._FormatCmdsubNode(parsed, 0, true, false, true);
                    arg = "(" + formatted + ")";
                }
            } catch (Exception)
            {
            }
        }
        text = "${" + param + op + arg + "}";
        this._DolbraceState = savedDolbrace;
        return (new ParamExpansion(param, op, arg, "param"), text);
    }

    public (INode, string) _ReadFunsub(int start)
    {
        return this._Parser._ParseFunsub(start);
    }
}

public class Word : INode
{
    public string Value { get; set; }
    public List<INode> Parts { get; set; }
    public string Kind { get; set; }

    public Word(string value, List<INode> parts, string kind)
    {
        this.Value = value;
        this.Parts = parts;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        string value = this.Value;
        value = this._ExpandAllAnsiCQuotes(value);
        value = this._StripLocaleStringDollars(value);
        value = this._NormalizeArrayWhitespace(value);
        value = this._FormatCommandSubstitutions(value, false);
        value = this._NormalizeParamExpansionNewlines(value);
        value = this._StripArithLineContinuations(value);
        value = this._DoubleCtlescSmart(value);
        value = value.Replace("\u007f", "\u0001\u007f");
        value = value.Replace("\\", "\\\\");
        if (value.EndsWith("\\\\") && !(value.EndsWith("\\\\\\\\")))
        {
            value = value + "\\\\";
        }
        string escaped = value.Replace("\"", "\\\"").Replace("\n", "\\n").Replace("\t", "\\t");
        return "(word \"" + escaped + "\")";
    }

    public void _AppendWithCtlesc(List<byte> result, int byteVal)
    {
        result.Add((byte)(byteVal));
    }

    public string _DoubleCtlescSmart(string value)
    {
        List<string> result = new List<string>();
        QuoteState quote = ParableFunctions.NewQuoteState();
        foreach (var _c1 in value)
        {
            var c = _c1.ToString();
            if (c == "'" && !(quote.Double))
            {
                quote.Single = !(quote.Single);
            }
            else
            {
                if (c == "\"" && !(quote.Single))
                {
                    quote.Double = !(quote.Double);
                }
            }
            result.Add(c);
            if (c == "\u0001")
            {
                if (quote.Double)
                {
                    int bsCount = 0;
                    for (int j = result.Count - 2; j > -1; j += -1)
                    {
                        if (result[j] == "\\")
                        {
                            bsCount += 1;
                        }
                        else
                        {
                            break;
                        }
                    }
                    if (bsCount % 2 == 0)
                    {
                        result.Add("\u0001");
                    }
                }
                else
                {
                    result.Add("\u0001");
                }
            }
        }
        return string.Join("", result);
    }

    public string _NormalizeParamExpansionNewlines(string value)
    {
        List<string> result = new List<string>();
        int i = 0;
        QuoteState quote = ParableFunctions.NewQuoteState();
        while (i < value.Length)
        {
            string c = (value[i]).ToString();
            if (c == "'" && !(quote.Double))
            {
                quote.Single = !(quote.Single);
                result.Add(c);
                i += 1;
            }
            else
            {
                if (c == "\"" && !(quote.Single))
                {
                    quote.Double = !(quote.Double);
                    result.Add(c);
                    i += 1;
                }
                else
                {
                    if (ParableFunctions._IsExpansionStart(value, i, "${") && !(quote.Single))
                    {
                        result.Add("$");
                        result.Add("{");
                        i += 2;
                        bool hadLeadingNewline = i < value.Length && (value[i]).ToString() == "\n";
                        if (hadLeadingNewline)
                        {
                            result.Add(" ");
                            i += 1;
                        }
                        int depth = 1;
                        while (i < value.Length && depth > 0)
                        {
                            string ch = (value[i]).ToString();
                            if (ch == "\\" && i + 1 < value.Length && !(quote.Single))
                            {
                                if ((value[i + 1]).ToString() == "\n")
                                {
                                    i += 2;
                                    continue;
                                }
                                result.Add(ch);
                                result.Add((value[i + 1]).ToString());
                                i += 2;
                                continue;
                            }
                            if (ch == "'" && !(quote.Double))
                            {
                                quote.Single = !(quote.Single);
                            }
                            else
                            {
                                if (ch == "\"" && !(quote.Single))
                                {
                                    quote.Double = !(quote.Double);
                                }
                                else
                                {
                                    if (!(quote.InQuotes()))
                                    {
                                        if (ch == "{")
                                        {
                                            depth += 1;
                                        }
                                        else
                                        {
                                            if (ch == "}")
                                            {
                                                depth -= 1;
                                                if (depth == 0)
                                                {
                                                    if (hadLeadingNewline)
                                                    {
                                                        result.Add(" ");
                                                    }
                                                    result.Add(ch);
                                                    i += 1;
                                                    break;
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            result.Add(ch);
                            i += 1;
                        }
                    }
                    else
                    {
                        result.Add(c);
                        i += 1;
                    }
                }
            }
        }
        return string.Join("", result);
    }

    public string _ShSingleQuote(string s)
    {
        if (!((!string.IsNullOrEmpty(s))))
        {
            return "''";
        }
        if (s == "'")
        {
            return "\\'";
        }
        List<string> result = new List<string> { "'" };
        foreach (var _c2 in s)
        {
            var c = _c2.ToString();
            if (c == "'")
            {
                result.Add("'\\''");
            }
            else
            {
                result.Add(c);
            }
        }
        result.Add("'");
        return string.Join("", result);
    }

    public List<byte> _AnsiCToBytes(string inner)
    {
        List<byte> result = new List<byte>();
        int i = 0;
        while (i < inner.Length)
        {
            if ((inner[i]).ToString() == "\\" && i + 1 < inner.Length)
            {
                string c = (inner[i + 1]).ToString();
                int simple = ParableFunctions._GetAnsiEscape(c);
                if (simple >= 0)
                {
                    result.Add((byte)(simple));
                    i += 2;
                }
                else
                {
                    if (c == "'")
                    {
                        result.Add((byte)(39));
                        i += 2;
                    }
                    else
                    {
                        int j = 0;
                        int byteVal = 0;
                        if (c == "x")
                        {
                            if (i + 2 < inner.Length && (inner[i + 2]).ToString() == "{")
                            {
                                j = i + 3;
                                while (j < inner.Length && ParableFunctions._IsHexDigit((inner[j]).ToString()))
                                {
                                    j += 1;
                                }
                                string hexStr = ParableFunctions._Substring(inner, i + 3, j);
                                if (j < inner.Length && (inner[j]).ToString() == "}")
                                {
                                    j += 1;
                                }
                                if (!((!string.IsNullOrEmpty(hexStr))))
                                {
                                    return result;
                                }
                                byteVal = (((int)Convert.ToInt64(hexStr, 16)) & 255);
                                if (byteVal == 0)
                                {
                                    return result;
                                }
                                this._AppendWithCtlesc(result, byteVal);
                                i = j;
                            }
                            else
                            {
                                j = i + 2;
                                while (j < inner.Length && j < i + 4 && ParableFunctions._IsHexDigit((inner[j]).ToString()))
                                {
                                    j += 1;
                                }
                                if (j > i + 2)
                                {
                                    byteVal = ((int)Convert.ToInt64(ParableFunctions._Substring(inner, i + 2, j), 16));
                                    if (byteVal == 0)
                                    {
                                        return result;
                                    }
                                    this._AppendWithCtlesc(result, byteVal);
                                    i = j;
                                }
                                else
                                {
                                    result.Add((byte)((int)((inner[i]).ToString()[0])));
                                    i += 1;
                                }
                            }
                        }
                        else
                        {
                            int codepoint = 0;
                            if (c == "u")
                            {
                                j = i + 2;
                                while (j < inner.Length && j < i + 6 && ParableFunctions._IsHexDigit((inner[j]).ToString()))
                                {
                                    j += 1;
                                }
                                if (j > i + 2)
                                {
                                    codepoint = ((int)Convert.ToInt64(ParableFunctions._Substring(inner, i + 2, j), 16));
                                    if (codepoint == 0)
                                    {
                                        return result;
                                    }
                                    result.AddRange(System.Text.Encoding.UTF8.GetBytes(char.ConvertFromUtf32(codepoint)).ToList());
                                    i = j;
                                }
                                else
                                {
                                    result.Add((byte)((int)((inner[i]).ToString()[0])));
                                    i += 1;
                                }
                            }
                            else
                            {
                                if (c == "U")
                                {
                                    j = i + 2;
                                    while (j < inner.Length && j < i + 10 && ParableFunctions._IsHexDigit((inner[j]).ToString()))
                                    {
                                        j += 1;
                                    }
                                    if (j > i + 2)
                                    {
                                        codepoint = ((int)Convert.ToInt64(ParableFunctions._Substring(inner, i + 2, j), 16));
                                        if (codepoint == 0)
                                        {
                                            return result;
                                        }
                                        result.AddRange(System.Text.Encoding.UTF8.GetBytes(char.ConvertFromUtf32(codepoint)).ToList());
                                        i = j;
                                    }
                                    else
                                    {
                                        result.Add((byte)((int)((inner[i]).ToString()[0])));
                                        i += 1;
                                    }
                                }
                                else
                                {
                                    if (c == "c")
                                    {
                                        if (i + 3 <= inner.Length)
                                        {
                                            string ctrlChar = (inner[i + 2]).ToString();
                                            int skipExtra = 0;
                                            if (ctrlChar == "\\" && i + 4 <= inner.Length && (inner[i + 3]).ToString() == "\\")
                                            {
                                                skipExtra = 1;
                                            }
                                            int ctrlVal = ((int)(ctrlChar[0]) & 31);
                                            if (ctrlVal == 0)
                                            {
                                                return result;
                                            }
                                            this._AppendWithCtlesc(result, ctrlVal);
                                            i += 3 + skipExtra;
                                        }
                                        else
                                        {
                                            result.Add((byte)((int)((inner[i]).ToString()[0])));
                                            i += 1;
                                        }
                                    }
                                    else
                                    {
                                        if (c == "0")
                                        {
                                            j = i + 2;
                                            while (j < inner.Length && j < i + 4 && ParableFunctions._IsOctalDigit((inner[j]).ToString()))
                                            {
                                                j += 1;
                                            }
                                            if (j > i + 2)
                                            {
                                                byteVal = (((int)Convert.ToInt64(ParableFunctions._Substring(inner, i + 1, j), 8)) & 255);
                                                if (byteVal == 0)
                                                {
                                                    return result;
                                                }
                                                this._AppendWithCtlesc(result, byteVal);
                                                i = j;
                                            }
                                            else
                                            {
                                                return result;
                                            }
                                        }
                                        else
                                        {
                                            if (string.Compare(c, "1") >= 0 && string.Compare(c, "7") <= 0)
                                            {
                                                j = i + 1;
                                                while (j < inner.Length && j < i + 4 && ParableFunctions._IsOctalDigit((inner[j]).ToString()))
                                                {
                                                    j += 1;
                                                }
                                                byteVal = (((int)Convert.ToInt64(ParableFunctions._Substring(inner, i + 1, j), 8)) & 255);
                                                if (byteVal == 0)
                                                {
                                                    return result;
                                                }
                                                this._AppendWithCtlesc(result, byteVal);
                                                i = j;
                                            }
                                            else
                                            {
                                                result.Add((byte)(92));
                                                result.Add((byte)((int)(c[0])));
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
            else
            {
                result.AddRange(System.Text.Encoding.UTF8.GetBytes((inner[i]).ToString()).ToList());
                i += 1;
            }
        }
        return result;
    }

    public string _ExpandAnsiCEscapes(string value)
    {
        if (!(value.StartsWith("'") && value.EndsWith("'")))
        {
            return value;
        }
        string inner = ParableFunctions._Substring(value, 1, value.Length - 1);
        List<byte> literalBytes = this._AnsiCToBytes(inner);
        string literalStr = ParableFunctions._BytesToString(literalBytes);
        return this._ShSingleQuote(literalStr);
    }

    public string _ExpandAllAnsiCQuotes(string value)
    {
        List<string> result = new List<string>();
        int i = 0;
        QuoteState quote = ParableFunctions.NewQuoteState();
        bool inBacktick = false;
        int braceDepth = 0;
        while (i < value.Length)
        {
            string ch = (value[i]).ToString();
            if (ch == "`" && !(quote.Single))
            {
                inBacktick = !(inBacktick);
                result.Add(ch);
                i += 1;
                continue;
            }
            if (inBacktick)
            {
                if (ch == "\\" && i + 1 < value.Length)
                {
                    result.Add(ch);
                    result.Add((value[i + 1]).ToString());
                    i += 2;
                }
                else
                {
                    result.Add(ch);
                    i += 1;
                }
                continue;
            }
            if (!(quote.Single))
            {
                if (ParableFunctions._IsExpansionStart(value, i, "${"))
                {
                    braceDepth += 1;
                    quote.Push();
                    result.Add("${");
                    i += 2;
                    continue;
                }
                else
                {
                    if (ch == "}" && braceDepth > 0 && !(quote.Double))
                    {
                        braceDepth -= 1;
                        result.Add(ch);
                        quote.Pop();
                        i += 1;
                        continue;
                    }
                }
            }
            bool effectiveInDquote = quote.Double;
            if (ch == "'" && !(effectiveInDquote))
            {
                bool isAnsiC = !(quote.Single) && i > 0 && (value[i - 1]).ToString() == "$" && ParableFunctions._CountConsecutiveDollarsBefore(value, i - 1) % 2 == 0;
                if (!(isAnsiC))
                {
                    quote.Single = !(quote.Single);
                }
                result.Add(ch);
                i += 1;
            }
            else
            {
                if (ch == "\"" && !(quote.Single))
                {
                    quote.Double = !(quote.Double);
                    result.Add(ch);
                    i += 1;
                }
                else
                {
                    if (ch == "\\" && i + 1 < value.Length && !(quote.Single))
                    {
                        result.Add(ch);
                        result.Add((value[i + 1]).ToString());
                        i += 2;
                    }
                    else
                    {
                        if (ParableFunctions._StartsWithAt(value, i, "$'") && !(quote.Single) && !(effectiveInDquote) && ParableFunctions._CountConsecutiveDollarsBefore(value, i) % 2 == 0)
                        {
                            int j = i + 2;
                            while (j < value.Length)
                            {
                                if ((value[j]).ToString() == "\\" && j + 1 < value.Length)
                                {
                                    j += 2;
                                }
                                else
                                {
                                    if ((value[j]).ToString() == "'")
                                    {
                                        j += 1;
                                        break;
                                    }
                                    else
                                    {
                                        j += 1;
                                    }
                                }
                            }
                            string ansiStr = ParableFunctions._Substring(value, i, j);
                            string expanded = this._ExpandAnsiCEscapes(ParableFunctions._Substring(ansiStr, 1, ansiStr.Length));
                            bool outerInDquote = quote.OuterDouble();
                            if (braceDepth > 0 && outerInDquote && expanded.StartsWith("'") && expanded.EndsWith("'"))
                            {
                                string inner = ParableFunctions._Substring(expanded, 1, expanded.Length - 1);
                                if (inner.IndexOf("\u0001") == -1)
                                {
                                    string resultStr = string.Join("", result);
                                    bool inPattern = false;
                                    int lastBraceIdx = resultStr.LastIndexOf("${");
                                    if (lastBraceIdx >= 0)
                                    {
                                        string afterBrace = resultStr.Substring(lastBraceIdx + 2);
                                        int varNameLen = 0;
                                        if ((!string.IsNullOrEmpty(afterBrace)))
                                        {
                                            if ("@*#?-$!0123456789_".Contains((afterBrace[0]).ToString()))
                                            {
                                                varNameLen = 1;
                                            }
                                            else
                                            {
                                                if (((afterBrace[0]).ToString().Length > 0 && (afterBrace[0]).ToString().All(char.IsLetter)) || (afterBrace[0]).ToString() == "_")
                                                {
                                                    while (varNameLen < afterBrace.Length)
                                                    {
                                                        string c = (afterBrace[varNameLen]).ToString();
                                                        if (!((c.Length > 0 && c.All(char.IsLetterOrDigit)) || c == "_"))
                                                        {
                                                            break;
                                                        }
                                                        varNameLen += 1;
                                                    }
                                                }
                                            }
                                        }
                                        if (varNameLen > 0 && varNameLen < afterBrace.Length && !"#?-".Contains((afterBrace[0]).ToString()))
                                        {
                                            string opStart = afterBrace.Substring(varNameLen);
                                            if (opStart.StartsWith("@") && opStart.Length > 1)
                                            {
                                                opStart = opStart.Substring(1);
                                            }
                                            foreach (string op in new List<string> { "//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",," })
                                            {
                                                if (opStart.StartsWith(op))
                                                {
                                                    inPattern = true;
                                                    break;
                                                }
                                            }
                                            if (!(inPattern) && (!string.IsNullOrEmpty(opStart)) && !"%#/^,~:+-=?".Contains((opStart[0]).ToString()))
                                            {
                                                foreach (string op in new List<string> { "//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",," })
                                                {
                                                    if (opStart.Contains(op))
                                                    {
                                                        inPattern = true;
                                                        break;
                                                    }
                                                }
                                            }
                                        }
                                        else
                                        {
                                            if (varNameLen == 0 && afterBrace.Length > 1)
                                            {
                                                string firstChar = (afterBrace[0]).ToString();
                                                if (!"%#/^,".Contains(firstChar))
                                                {
                                                    string rest = afterBrace.Substring(1);
                                                    foreach (string op in new List<string> { "//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",," })
                                                    {
                                                        if (rest.Contains(op))
                                                        {
                                                            inPattern = true;
                                                            break;
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                    if (!(inPattern))
                                    {
                                        expanded = inner;
                                    }
                                }
                            }
                            result.Add(expanded);
                            i = j;
                        }
                        else
                        {
                            result.Add(ch);
                            i += 1;
                        }
                    }
                }
            }
        }
        return string.Join("", result);
    }

    public string _StripLocaleStringDollars(string value)
    {
        List<string> result = new List<string>();
        int i = 0;
        int braceDepth = 0;
        int bracketDepth = 0;
        QuoteState quote = ParableFunctions.NewQuoteState();
        QuoteState braceQuote = ParableFunctions.NewQuoteState();
        bool bracketInDoubleQuote = false;
        while (i < value.Length)
        {
            string ch = (value[i]).ToString();
            if (ch == "\\" && i + 1 < value.Length && !(quote.Single) && !(braceQuote.Single))
            {
                result.Add(ch);
                result.Add((value[i + 1]).ToString());
                i += 2;
            }
            else
            {
                if (ParableFunctions._StartsWithAt(value, i, "${") && !(quote.Single) && !(braceQuote.Single) && (i == 0 || (value[i - 1]).ToString() != "$"))
                {
                    braceDepth += 1;
                    braceQuote.Double = false;
                    braceQuote.Single = false;
                    result.Add("$");
                    result.Add("{");
                    i += 2;
                }
                else
                {
                    if (ch == "}" && braceDepth > 0 && !(quote.Single) && !(braceQuote.Double) && !(braceQuote.Single))
                    {
                        braceDepth -= 1;
                        result.Add(ch);
                        i += 1;
                    }
                    else
                    {
                        if (ch == "[" && braceDepth > 0 && !(quote.Single) && !(braceQuote.Double))
                        {
                            bracketDepth += 1;
                            bracketInDoubleQuote = false;
                            result.Add(ch);
                            i += 1;
                        }
                        else
                        {
                            if (ch == "]" && bracketDepth > 0 && !(quote.Single) && !(bracketInDoubleQuote))
                            {
                                bracketDepth -= 1;
                                result.Add(ch);
                                i += 1;
                            }
                            else
                            {
                                if (ch == "'" && !(quote.Double) && braceDepth == 0)
                                {
                                    quote.Single = !(quote.Single);
                                    result.Add(ch);
                                    i += 1;
                                }
                                else
                                {
                                    if (ch == "\"" && !(quote.Single) && braceDepth == 0)
                                    {
                                        quote.Double = !(quote.Double);
                                        result.Add(ch);
                                        i += 1;
                                    }
                                    else
                                    {
                                        if (ch == "\"" && !(quote.Single) && bracketDepth > 0)
                                        {
                                            bracketInDoubleQuote = !(bracketInDoubleQuote);
                                            result.Add(ch);
                                            i += 1;
                                        }
                                        else
                                        {
                                            if (ch == "\"" && !(quote.Single) && !(braceQuote.Single) && braceDepth > 0)
                                            {
                                                braceQuote.Double = !(braceQuote.Double);
                                                result.Add(ch);
                                                i += 1;
                                            }
                                            else
                                            {
                                                if (ch == "'" && !(quote.Double) && !(braceQuote.Double) && braceDepth > 0)
                                                {
                                                    braceQuote.Single = !(braceQuote.Single);
                                                    result.Add(ch);
                                                    i += 1;
                                                }
                                                else
                                                {
                                                    if (ParableFunctions._StartsWithAt(value, i, "$\"") && !(quote.Single) && !(braceQuote.Single) && (braceDepth > 0 || bracketDepth > 0 || !(quote.Double)) && !(braceQuote.Double) && !(bracketInDoubleQuote))
                                                    {
                                                        int dollarCount = 1 + ParableFunctions._CountConsecutiveDollarsBefore(value, i);
                                                        if (dollarCount % 2 == 1)
                                                        {
                                                            result.Add("\"");
                                                            if (bracketDepth > 0)
                                                            {
                                                                bracketInDoubleQuote = true;
                                                            }
                                                            else
                                                            {
                                                                if (braceDepth > 0)
                                                                {
                                                                    braceQuote.Double = true;
                                                                }
                                                                else
                                                                {
                                                                    quote.Double = true;
                                                                }
                                                            }
                                                            i += 2;
                                                        }
                                                        else
                                                        {
                                                            result.Add(ch);
                                                            i += 1;
                                                        }
                                                    }
                                                    else
                                                    {
                                                        result.Add(ch);
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
        return string.Join("", result);
    }

    public string _NormalizeArrayWhitespace(string value)
    {
        int i = 0;
        if (!(i < value.Length && (((value[i]).ToString().Length > 0 && (value[i]).ToString().All(char.IsLetter)) || (value[i]).ToString() == "_")))
        {
            return value;
        }
        i += 1;
        while (i < value.Length && (((value[i]).ToString().Length > 0 && (value[i]).ToString().All(char.IsLetterOrDigit)) || (value[i]).ToString() == "_"))
        {
            i += 1;
        }
        while (i < value.Length && (value[i]).ToString() == "[")
        {
            int depth = 1;
            i += 1;
            while (i < value.Length && depth > 0)
            {
                if ((value[i]).ToString() == "[")
                {
                    depth += 1;
                }
                else
                {
                    if ((value[i]).ToString() == "]")
                    {
                        depth -= 1;
                    }
                }
                i += 1;
            }
            if (depth != 0)
            {
                return value;
            }
        }
        if (i < value.Length && (value[i]).ToString() == "+")
        {
            i += 1;
        }
        if (!(i + 1 < value.Length && (value[i]).ToString() == "=" && (value[i + 1]).ToString() == "("))
        {
            return value;
        }
        string prefix = ParableFunctions._Substring(value, 0, i + 1);
        int openParenPos = i + 1;
        int closeParenPos = 0;
        if (value.EndsWith(")"))
        {
            closeParenPos = value.Length - 1;
        }
        else
        {
            closeParenPos = this._FindMatchingParen(value, openParenPos);
            if (closeParenPos < 0)
            {
                return value;
            }
        }
        string inner = ParableFunctions._Substring(value, openParenPos + 1, closeParenPos);
        string suffix = ParableFunctions._Substring(value, closeParenPos + 1, value.Length);
        string result = this._NormalizeArrayInner(inner);
        return prefix + "(" + result + ")" + suffix;
    }

    public int _FindMatchingParen(string value, int openPos)
    {
        if (openPos >= value.Length || (value[openPos]).ToString() != "(")
        {
            return -1;
        }
        int i = openPos + 1;
        int depth = 1;
        QuoteState quote = ParableFunctions.NewQuoteState();
        while (i < value.Length && depth > 0)
        {
            string ch = (value[i]).ToString();
            if (ch == "\\" && i + 1 < value.Length && !(quote.Single))
            {
                i += 2;
                continue;
            }
            if (ch == "'" && !(quote.Double))
            {
                quote.Single = !(quote.Single);
                i += 1;
                continue;
            }
            if (ch == "\"" && !(quote.Single))
            {
                quote.Double = !(quote.Double);
                i += 1;
                continue;
            }
            if (quote.Single || quote.Double)
            {
                i += 1;
                continue;
            }
            if (ch == "#")
            {
                while (i < value.Length && (value[i]).ToString() != "\n")
                {
                    i += 1;
                }
                continue;
            }
            if (ch == "(")
            {
                depth += 1;
            }
            else
            {
                if (ch == ")")
                {
                    depth -= 1;
                    if (depth == 0)
                    {
                        return i;
                    }
                }
            }
            i += 1;
        }
        return -1;
    }

    public string _NormalizeArrayInner(string inner)
    {
        List<string> normalized = new List<string>();
        int i = 0;
        bool inWhitespace = true;
        int braceDepth = 0;
        int bracketDepth = 0;
        while (i < inner.Length)
        {
            string ch = (inner[i]).ToString();
            if (ParableFunctions._IsWhitespace(ch))
            {
                if (!(inWhitespace) && (normalized.Count > 0) && braceDepth == 0 && bracketDepth == 0)
                {
                    normalized.Add(" ");
                    inWhitespace = true;
                }
                if (braceDepth > 0 || bracketDepth > 0)
                {
                    normalized.Add(ch);
                }
                i += 1;
            }
            else
            {
                int j = 0;
                if (ch == "'")
                {
                    inWhitespace = false;
                    j = i + 1;
                    while (j < inner.Length && (inner[j]).ToString() != "'")
                    {
                        j += 1;
                    }
                    normalized.Add(ParableFunctions._Substring(inner, i, j + 1));
                    i = j + 1;
                }
                else
                {
                    if (ch == "\"")
                    {
                        inWhitespace = false;
                        j = i + 1;
                        List<string> dqContent = new List<string> { "\"" };
                        int dqBraceDepth = 0;
                        while (j < inner.Length)
                        {
                            if ((inner[j]).ToString() == "\\" && j + 1 < inner.Length)
                            {
                                if ((inner[j + 1]).ToString() == "\n")
                                {
                                    j += 2;
                                }
                                else
                                {
                                    dqContent.Add((inner[j]).ToString());
                                    dqContent.Add((inner[j + 1]).ToString());
                                    j += 2;
                                }
                            }
                            else
                            {
                                if (ParableFunctions._IsExpansionStart(inner, j, "${"))
                                {
                                    dqContent.Add("${");
                                    dqBraceDepth += 1;
                                    j += 2;
                                }
                                else
                                {
                                    if ((inner[j]).ToString() == "}" && dqBraceDepth > 0)
                                    {
                                        dqContent.Add("}");
                                        dqBraceDepth -= 1;
                                        j += 1;
                                    }
                                    else
                                    {
                                        if ((inner[j]).ToString() == "\"" && dqBraceDepth == 0)
                                        {
                                            dqContent.Add("\"");
                                            j += 1;
                                            break;
                                        }
                                        else
                                        {
                                            dqContent.Add((inner[j]).ToString());
                                            j += 1;
                                        }
                                    }
                                }
                            }
                        }
                        normalized.Add(string.Join("", dqContent));
                        i = j;
                    }
                    else
                    {
                        if (ch == "\\" && i + 1 < inner.Length)
                        {
                            if ((inner[i + 1]).ToString() == "\n")
                            {
                                i += 2;
                            }
                            else
                            {
                                inWhitespace = false;
                                normalized.Add(ParableFunctions._Substring(inner, i, i + 2));
                                i += 2;
                            }
                        }
                        else
                        {
                            int depth = 0;
                            if (ParableFunctions._IsExpansionStart(inner, i, "$(("))
                            {
                                inWhitespace = false;
                                j = i + 3;
                                depth = 1;
                                while (j < inner.Length && depth > 0)
                                {
                                    if (j + 1 < inner.Length && (inner[j]).ToString() == "(" && (inner[j + 1]).ToString() == "(")
                                    {
                                        depth += 1;
                                        j += 2;
                                    }
                                    else
                                    {
                                        if (j + 1 < inner.Length && (inner[j]).ToString() == ")" && (inner[j + 1]).ToString() == ")")
                                        {
                                            depth -= 1;
                                            j += 2;
                                        }
                                        else
                                        {
                                            j += 1;
                                        }
                                    }
                                }
                                normalized.Add(ParableFunctions._Substring(inner, i, j));
                                i = j;
                            }
                            else
                            {
                                if (ParableFunctions._IsExpansionStart(inner, i, "$("))
                                {
                                    inWhitespace = false;
                                    j = i + 2;
                                    depth = 1;
                                    while (j < inner.Length && depth > 0)
                                    {
                                        if ((inner[j]).ToString() == "(" && j > 0 && (inner[j - 1]).ToString() == "$")
                                        {
                                            depth += 1;
                                        }
                                        else
                                        {
                                            if ((inner[j]).ToString() == ")")
                                            {
                                                depth -= 1;
                                            }
                                            else
                                            {
                                                if ((inner[j]).ToString() == "'")
                                                {
                                                    j += 1;
                                                    while (j < inner.Length && (inner[j]).ToString() != "'")
                                                    {
                                                        j += 1;
                                                    }
                                                }
                                                else
                                                {
                                                    if ((inner[j]).ToString() == "\"")
                                                    {
                                                        j += 1;
                                                        while (j < inner.Length)
                                                        {
                                                            if ((inner[j]).ToString() == "\\" && j + 1 < inner.Length)
                                                            {
                                                                j += 2;
                                                                continue;
                                                            }
                                                            if ((inner[j]).ToString() == "\"")
                                                            {
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
                                    normalized.Add(ParableFunctions._Substring(inner, i, j));
                                    i = j;
                                }
                                else
                                {
                                    if ((ch == "<" || ch == ">") && i + 1 < inner.Length && (inner[i + 1]).ToString() == "(")
                                    {
                                        inWhitespace = false;
                                        j = i + 2;
                                        depth = 1;
                                        while (j < inner.Length && depth > 0)
                                        {
                                            if ((inner[j]).ToString() == "(")
                                            {
                                                depth += 1;
                                            }
                                            else
                                            {
                                                if ((inner[j]).ToString() == ")")
                                                {
                                                    depth -= 1;
                                                }
                                                else
                                                {
                                                    if ((inner[j]).ToString() == "'")
                                                    {
                                                        j += 1;
                                                        while (j < inner.Length && (inner[j]).ToString() != "'")
                                                        {
                                                            j += 1;
                                                        }
                                                    }
                                                    else
                                                    {
                                                        if ((inner[j]).ToString() == "\"")
                                                        {
                                                            j += 1;
                                                            while (j < inner.Length)
                                                            {
                                                                if ((inner[j]).ToString() == "\\" && j + 1 < inner.Length)
                                                                {
                                                                    j += 2;
                                                                    continue;
                                                                }
                                                                if ((inner[j]).ToString() == "\"")
                                                                {
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
                                        normalized.Add(ParableFunctions._Substring(inner, i, j));
                                        i = j;
                                    }
                                    else
                                    {
                                        if (ParableFunctions._IsExpansionStart(inner, i, "${"))
                                        {
                                            inWhitespace = false;
                                            normalized.Add("${");
                                            braceDepth += 1;
                                            i += 2;
                                        }
                                        else
                                        {
                                            if (ch == "{" && braceDepth > 0)
                                            {
                                                normalized.Add(ch);
                                                braceDepth += 1;
                                                i += 1;
                                            }
                                            else
                                            {
                                                if (ch == "}" && braceDepth > 0)
                                                {
                                                    normalized.Add(ch);
                                                    braceDepth -= 1;
                                                    i += 1;
                                                }
                                                else
                                                {
                                                    if (ch == "#" && braceDepth == 0 && inWhitespace)
                                                    {
                                                        while (i < inner.Length && (inner[i]).ToString() != "\n")
                                                        {
                                                            i += 1;
                                                        }
                                                    }
                                                    else
                                                    {
                                                        if (ch == "[")
                                                        {
                                                            if (inWhitespace || bracketDepth > 0)
                                                            {
                                                                bracketDepth += 1;
                                                            }
                                                            inWhitespace = false;
                                                            normalized.Add(ch);
                                                            i += 1;
                                                        }
                                                        else
                                                        {
                                                            if (ch == "]" && bracketDepth > 0)
                                                            {
                                                                normalized.Add(ch);
                                                                bracketDepth -= 1;
                                                                i += 1;
                                                            }
                                                            else
                                                            {
                                                                inWhitespace = false;
                                                                normalized.Add(ch);
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
        return string.Join("", normalized).TrimEnd(" \t\n\r".ToCharArray());
    }

    public string _StripArithLineContinuations(string value)
    {
        List<string> result = new List<string>();
        int i = 0;
        while (i < value.Length)
        {
            if (ParableFunctions._IsExpansionStart(value, i, "$(("))
            {
                int start = i;
                i += 3;
                int depth = 2;
                List<string> arithContent = new List<string>();
                int firstCloseIdx = -1;
                while (i < value.Length && depth > 0)
                {
                    if ((value[i]).ToString() == "(")
                    {
                        arithContent.Add("(");
                        depth += 1;
                        i += 1;
                        if (depth > 1)
                        {
                            firstCloseIdx = -1;
                        }
                    }
                    else
                    {
                        if ((value[i]).ToString() == ")")
                        {
                            if (depth == 2)
                            {
                                firstCloseIdx = arithContent.Count;
                            }
                            depth -= 1;
                            if (depth > 0)
                            {
                                arithContent.Add(")");
                            }
                            i += 1;
                        }
                        else
                        {
                            if ((value[i]).ToString() == "\\" && i + 1 < value.Length && (value[i + 1]).ToString() == "\n")
                            {
                                int numBackslashes = 0;
                                int j = arithContent.Count - 1;
                                while (j >= 0 && arithContent[j] == "\n")
                                {
                                    j -= 1;
                                }
                                while (j >= 0 && arithContent[j] == "\\")
                                {
                                    numBackslashes += 1;
                                    j -= 1;
                                }
                                if (numBackslashes % 2 == 1)
                                {
                                    arithContent.Add("\\");
                                    arithContent.Add("\n");
                                    i += 2;
                                }
                                else
                                {
                                    i += 2;
                                }
                                if (depth == 1)
                                {
                                    firstCloseIdx = -1;
                                }
                            }
                            else
                            {
                                arithContent.Add((value[i]).ToString());
                                i += 1;
                                if (depth == 1)
                                {
                                    firstCloseIdx = -1;
                                }
                            }
                        }
                    }
                }
                if (depth == 0 || depth == 1 && firstCloseIdx != -1)
                {
                    string content = string.Join("", arithContent);
                    if (firstCloseIdx != -1)
                    {
                        content = content.Substring(0, firstCloseIdx);
                        string closing = (depth == 0 ? "))" : ")");
                        result.Add("$((" + content + closing);
                    }
                    else
                    {
                        result.Add("$((" + content + ")");
                    }
                }
                else
                {
                    result.Add(ParableFunctions._Substring(value, start, i));
                }
            }
            else
            {
                result.Add((value[i]).ToString());
                i += 1;
            }
        }
        return string.Join("", result);
    }

    public List<INode> _CollectCmdsubs(INode node)
    {
        List<INode> result = new List<INode>();
        switch (node)
        {
            case CommandSubstitution nodeCommandSubstitution:
                result.Add(nodeCommandSubstitution);
                break;
            case Array nodeArray:
                foreach (Word elem in nodeArray.Elements)
                {
                    foreach (INode p in elem.Parts)
                    {
                        switch (p)
                        {
                            case CommandSubstitution pCommandSubstitution:
                                result.Add(pCommandSubstitution);
                                break;
                            default:
                                result.AddRange(this._CollectCmdsubs(p));
                                break;
                        }
                    }
                }
                break;
            case ArithmeticExpansion nodeArithmeticExpansion:
                if (nodeArithmeticExpansion.Expression != null)
                {
                    result.AddRange(this._CollectCmdsubs(nodeArithmeticExpansion.Expression));
                }
                break;
            case ArithBinaryOp nodeArithBinaryOp:
                result.AddRange(this._CollectCmdsubs(nodeArithBinaryOp.Left));
                result.AddRange(this._CollectCmdsubs(nodeArithBinaryOp.Right));
                break;
            case ArithComma nodeArithComma:
                result.AddRange(this._CollectCmdsubs(nodeArithComma.Left));
                result.AddRange(this._CollectCmdsubs(nodeArithComma.Right));
                break;
            case ArithUnaryOp nodeArithUnaryOp:
                result.AddRange(this._CollectCmdsubs(nodeArithUnaryOp.Operand));
                break;
            case ArithPreIncr nodeArithPreIncr:
                result.AddRange(this._CollectCmdsubs(nodeArithPreIncr.Operand));
                break;
            case ArithPostIncr nodeArithPostIncr:
                result.AddRange(this._CollectCmdsubs(nodeArithPostIncr.Operand));
                break;
            case ArithPreDecr nodeArithPreDecr:
                result.AddRange(this._CollectCmdsubs(nodeArithPreDecr.Operand));
                break;
            case ArithPostDecr nodeArithPostDecr:
                result.AddRange(this._CollectCmdsubs(nodeArithPostDecr.Operand));
                break;
            case ArithTernary nodeArithTernary:
                result.AddRange(this._CollectCmdsubs(nodeArithTernary.Condition));
                result.AddRange(this._CollectCmdsubs(nodeArithTernary.IfTrue));
                result.AddRange(this._CollectCmdsubs(nodeArithTernary.IfFalse));
                break;
            case ArithAssign nodeArithAssign:
                result.AddRange(this._CollectCmdsubs(nodeArithAssign.Target));
                result.AddRange(this._CollectCmdsubs(nodeArithAssign.Value));
                break;
        }
        return result;
    }

    public List<INode> _CollectProcsubs(INode node)
    {
        List<INode> result = new List<INode>();
        switch (node)
        {
            case ProcessSubstitution nodeProcessSubstitution:
                result.Add(nodeProcessSubstitution);
                break;
            case Array nodeArray:
                foreach (Word elem in nodeArray.Elements)
                {
                    foreach (INode p in elem.Parts)
                    {
                        switch (p)
                        {
                            case ProcessSubstitution pProcessSubstitution:
                                result.Add(pProcessSubstitution);
                                break;
                            default:
                                result.AddRange(this._CollectProcsubs(p));
                                break;
                        }
                    }
                }
                break;
        }
        return result;
    }

    public string _FormatCommandSubstitutions(string value, bool inArith)
    {
        List<INode> cmdsubParts = new List<INode>();
        List<INode> procsubParts = new List<INode>();
        bool hasArith = false;
        foreach (INode p in this.Parts)
        {
            switch (p)
            {
                case CommandSubstitution pCommandSubstitution:
                    cmdsubParts.Add(pCommandSubstitution);
                    break;
                case ProcessSubstitution pProcessSubstitution:
                    procsubParts.Add(pProcessSubstitution);
                    break;
                case ArithmeticExpansion pArithmeticExpansion:
                    hasArith = true;
                    break;
                default:
                    cmdsubParts.AddRange(this._CollectCmdsubs(p));
                    procsubParts.AddRange(this._CollectProcsubs(p));
                    break;
            }
        }
        bool hasBraceCmdsub = value.IndexOf("${ ") != -1 || value.IndexOf("${\t") != -1 || value.IndexOf("${\n") != -1 || value.IndexOf("${|") != -1;
        bool hasUntrackedCmdsub = false;
        bool hasUntrackedProcsub = false;
        int idx = 0;
        QuoteState scanQuote = ParableFunctions.NewQuoteState();
        while (idx < value.Length)
        {
            if ((value[idx]).ToString() == "\"")
            {
                scanQuote.Double = !(scanQuote.Double);
                idx += 1;
            }
            else
            {
                if ((value[idx]).ToString() == "'" && !(scanQuote.Double))
                {
                    idx += 1;
                    while (idx < value.Length && (value[idx]).ToString() != "'")
                    {
                        idx += 1;
                    }
                    if (idx < value.Length)
                    {
                        idx += 1;
                    }
                }
                else
                {
                    if (ParableFunctions._StartsWithAt(value, idx, "$(") && !(ParableFunctions._StartsWithAt(value, idx, "$((")) && !(ParableFunctions._IsBackslashEscaped(value, idx)) && !(ParableFunctions._IsDollarDollarParen(value, idx)))
                    {
                        hasUntrackedCmdsub = true;
                        break;
                    }
                    else
                    {
                        if ((ParableFunctions._StartsWithAt(value, idx, "<(") || ParableFunctions._StartsWithAt(value, idx, ">(")) && !(scanQuote.Double))
                        {
                            if (idx == 0 || !(((value[idx - 1]).ToString().Length > 0 && (value[idx - 1]).ToString().All(char.IsLetterOrDigit))) && !"\"'".Contains((value[idx - 1]).ToString()))
                            {
                                hasUntrackedProcsub = true;
                                break;
                            }
                            idx += 1;
                        }
                        else
                        {
                            idx += 1;
                        }
                    }
                }
            }
        }
        bool hasParamWithProcsubPattern = value.Contains("${") && (value.Contains("<(") || value.Contains(">("));
        if (!((cmdsubParts.Count > 0)) && !((procsubParts.Count > 0)) && !(hasBraceCmdsub) && !(hasUntrackedCmdsub) && !(hasUntrackedProcsub) && !(hasParamWithProcsubPattern))
        {
            return value;
        }
        List<string> result = new List<string>();
        int i = 0;
        int cmdsubIdx = 0;
        int procsubIdx = 0;
        QuoteState mainQuote = ParableFunctions.NewQuoteState();
        int extglobDepth = 0;
        int deprecatedArithDepth = 0;
        int arithDepth = 0;
        int arithParenDepth = 0;
        while (i < value.Length)
        {
            if (i > 0 && ParableFunctions._IsExtglobPrefix((value[i - 1]).ToString()) && (value[i]).ToString() == "(" && !(ParableFunctions._IsBackslashEscaped(value, i - 1)))
            {
                extglobDepth += 1;
                result.Add((value[i]).ToString());
                i += 1;
                continue;
            }
            if ((value[i]).ToString() == ")" && extglobDepth > 0)
            {
                extglobDepth -= 1;
                result.Add((value[i]).ToString());
                i += 1;
                continue;
            }
            if (ParableFunctions._StartsWithAt(value, i, "$[") && !(ParableFunctions._IsBackslashEscaped(value, i)))
            {
                deprecatedArithDepth += 1;
                result.Add((value[i]).ToString());
                i += 1;
                continue;
            }
            if ((value[i]).ToString() == "]" && deprecatedArithDepth > 0)
            {
                deprecatedArithDepth -= 1;
                result.Add((value[i]).ToString());
                i += 1;
                continue;
            }
            if (ParableFunctions._IsExpansionStart(value, i, "$((") && !(ParableFunctions._IsBackslashEscaped(value, i)) && hasArith)
            {
                arithDepth += 1;
                arithParenDepth += 2;
                result.Add("$((");
                i += 3;
                continue;
            }
            if (arithDepth > 0 && arithParenDepth == 2 && ParableFunctions._StartsWithAt(value, i, "))"))
            {
                arithDepth -= 1;
                arithParenDepth -= 2;
                result.Add("))");
                i += 2;
                continue;
            }
            if (arithDepth > 0)
            {
                if ((value[i]).ToString() == "(")
                {
                    arithParenDepth += 1;
                    result.Add((value[i]).ToString());
                    i += 1;
                    continue;
                }
                else
                {
                    if ((value[i]).ToString() == ")")
                    {
                        arithParenDepth -= 1;
                        result.Add((value[i]).ToString());
                        i += 1;
                        continue;
                    }
                }
            }
            int j = 0;
            if (ParableFunctions._IsExpansionStart(value, i, "$((") && !(hasArith))
            {
                j = ParableFunctions._FindCmdsubEnd(value, i + 2);
                result.Add(ParableFunctions._Substring(value, i, j));
                if (cmdsubIdx < cmdsubParts.Count)
                {
                    cmdsubIdx += 1;
                }
                i = j;
                continue;
            }
            string inner = "";
            INode node = null;
            string formatted = "";
            Parser parser = null;
            INode parsed = null;
            if (ParableFunctions._StartsWithAt(value, i, "$(") && !(ParableFunctions._StartsWithAt(value, i, "$((")) && !(ParableFunctions._IsBackslashEscaped(value, i)) && !(ParableFunctions._IsDollarDollarParen(value, i)))
            {
                j = ParableFunctions._FindCmdsubEnd(value, i + 2);
                if (extglobDepth > 0)
                {
                    result.Add(ParableFunctions._Substring(value, i, j));
                    if (cmdsubIdx < cmdsubParts.Count)
                    {
                        cmdsubIdx += 1;
                    }
                    i = j;
                    continue;
                }
                inner = ParableFunctions._Substring(value, i + 2, j - 1);
                if (cmdsubIdx < cmdsubParts.Count)
                {
                    node = cmdsubParts[cmdsubIdx];
                    formatted = ParableFunctions._FormatCmdsubNode(((CommandSubstitution)node).Command, 0, false, false, false);
                    cmdsubIdx += 1;
                }
                else
                {
                    try
                    {
                        parser = ParableFunctions.NewParser(inner, false, false);
                        parsed = parser.ParseList(true);
                        formatted = (parsed != null ? ParableFunctions._FormatCmdsubNode(parsed, 0, false, false, false) : "");
                    } catch (Exception)
                    {
                        formatted = inner;
                    }
                }
                if (formatted.StartsWith("("))
                {
                    result.Add("$( " + formatted + ")");
                }
                else
                {
                    result.Add("$(" + formatted + ")");
                }
                i = j;
            }
            else
            {
                if ((value[i]).ToString() == "`" && cmdsubIdx < cmdsubParts.Count)
                {
                    j = i + 1;
                    while (j < value.Length)
                    {
                        if ((value[j]).ToString() == "\\" && j + 1 < value.Length)
                        {
                            j += 2;
                            continue;
                        }
                        if ((value[j]).ToString() == "`")
                        {
                            j += 1;
                            break;
                        }
                        j += 1;
                    }
                    result.Add(ParableFunctions._Substring(value, i, j));
                    cmdsubIdx += 1;
                    i = j;
                }
                else
                {
                    string prefix = "";
                    if (ParableFunctions._IsExpansionStart(value, i, "${") && i + 2 < value.Length && ParableFunctions._IsFunsubChar((value[i + 2]).ToString()) && !(ParableFunctions._IsBackslashEscaped(value, i)))
                    {
                        j = ParableFunctions._FindFunsubEnd(value, i + 2);
                        INode cmdsubNode = (cmdsubIdx < cmdsubParts.Count ? cmdsubParts[cmdsubIdx] : null);
                        if ((cmdsubNode is CommandSubstitution) && ((CommandSubstitution)cmdsubNode).Brace)
                        {
                            node = cmdsubNode;
                            formatted = ParableFunctions._FormatCmdsubNode(((CommandSubstitution)node).Command, 0, false, false, false);
                            bool hasPipe = (value[i + 2]).ToString() == "|";
                            prefix = (hasPipe ? "${|" : "${ ");
                            string origInner = ParableFunctions._Substring(value, i + 2, j - 1);
                            bool endsWithNewline = origInner.EndsWith("\n");
                            string suffix = "";
                            if (!((!string.IsNullOrEmpty(formatted))) || (formatted.Length > 0 && formatted.All(char.IsWhiteSpace)))
                            {
                                suffix = "}";
                            }
                            else
                            {
                                if (formatted.EndsWith("&") || formatted.EndsWith("& "))
                                {
                                    suffix = (formatted.EndsWith("&") ? " }" : "}");
                                }
                                else
                                {
                                    if (endsWithNewline)
                                    {
                                        suffix = "\n }";
                                    }
                                    else
                                    {
                                        suffix = "; }";
                                    }
                                }
                            }
                            result.Add(prefix + formatted + suffix);
                            cmdsubIdx += 1;
                        }
                        else
                        {
                            result.Add(ParableFunctions._Substring(value, i, j));
                        }
                        i = j;
                    }
                    else
                    {
                        if ((ParableFunctions._StartsWithAt(value, i, ">(") || ParableFunctions._StartsWithAt(value, i, "<(")) && !(mainQuote.Double) && deprecatedArithDepth == 0 && arithDepth == 0)
                        {
                            bool isProcsub = i == 0 || !(((value[i - 1]).ToString().Length > 0 && (value[i - 1]).ToString().All(char.IsLetterOrDigit))) && !"\"'".Contains((value[i - 1]).ToString());
                            if (extglobDepth > 0)
                            {
                                j = ParableFunctions._FindCmdsubEnd(value, i + 2);
                                result.Add(ParableFunctions._Substring(value, i, j));
                                if (procsubIdx < procsubParts.Count)
                                {
                                    procsubIdx += 1;
                                }
                                i = j;
                                continue;
                            }
                            string direction = "";
                            bool compact = false;
                            string stripped = "";
                            if (procsubIdx < procsubParts.Count)
                            {
                                direction = (value[i]).ToString();
                                j = ParableFunctions._FindCmdsubEnd(value, i + 2);
                                node = procsubParts[procsubIdx];
                                compact = ParableFunctions._StartsWithSubshell(((ProcessSubstitution)node).Command);
                                formatted = ParableFunctions._FormatCmdsubNode(((ProcessSubstitution)node).Command, 0, true, compact, true);
                                string rawContent = ParableFunctions._Substring(value, i + 2, j - 1);
                                if (((ProcessSubstitution)node).Command.Kind == "subshell")
                                {
                                    int leadingWsEnd = 0;
                                    while (leadingWsEnd < rawContent.Length && " \t\n".Contains((rawContent[leadingWsEnd]).ToString()))
                                    {
                                        leadingWsEnd += 1;
                                    }
                                    string leadingWs = rawContent.Substring(0, leadingWsEnd);
                                    stripped = rawContent.Substring(leadingWsEnd);
                                    if (stripped.StartsWith("("))
                                    {
                                        if ((!string.IsNullOrEmpty(leadingWs)))
                                        {
                                            string normalizedWs = leadingWs.Replace("\n", " ").Replace("\t", " ");
                                            string spaced = ParableFunctions._FormatCmdsubNode(((ProcessSubstitution)node).Command, 0, false, false, false);
                                            result.Add(direction + "(" + normalizedWs + spaced + ")");
                                        }
                                        else
                                        {
                                            rawContent = rawContent.Replace("\\\n", "");
                                            result.Add(direction + "(" + rawContent + ")");
                                        }
                                        procsubIdx += 1;
                                        i = j;
                                        continue;
                                    }
                                }
                                rawContent = ParableFunctions._Substring(value, i + 2, j - 1);
                                string rawStripped = rawContent.Replace("\\\n", "");
                                if (ParableFunctions._StartsWithSubshell(((ProcessSubstitution)node).Command) && formatted != rawStripped)
                                {
                                    result.Add(direction + "(" + rawStripped + ")");
                                }
                                else
                                {
                                    string finalOutput = direction + "(" + formatted + ")";
                                    result.Add(finalOutput);
                                }
                                procsubIdx += 1;
                                i = j;
                            }
                            else
                            {
                                if (isProcsub && (this.Parts.Count != 0))
                                {
                                    direction = (value[i]).ToString();
                                    j = ParableFunctions._FindCmdsubEnd(value, i + 2);
                                    if (j > value.Length || j > 0 && j <= value.Length && (value[j - 1]).ToString() != ")")
                                    {
                                        result.Add((value[i]).ToString());
                                        i += 1;
                                        continue;
                                    }
                                    inner = ParableFunctions._Substring(value, i + 2, j - 1);
                                    try
                                    {
                                        parser = ParableFunctions.NewParser(inner, false, false);
                                        parsed = parser.ParseList(true);
                                        if (parsed != null && parser.Pos == inner.Length && !inner.Contains("\n"))
                                        {
                                            compact = ParableFunctions._StartsWithSubshell(parsed);
                                            formatted = ParableFunctions._FormatCmdsubNode(parsed, 0, true, compact, true);
                                        }
                                        else
                                        {
                                            formatted = inner;
                                        }
                                    } catch (Exception)
                                    {
                                        formatted = inner;
                                    }
                                    result.Add(direction + "(" + formatted + ")");
                                    i = j;
                                }
                                else
                                {
                                    if (isProcsub)
                                    {
                                        direction = (value[i]).ToString();
                                        j = ParableFunctions._FindCmdsubEnd(value, i + 2);
                                        if (j > value.Length || j > 0 && j <= value.Length && (value[j - 1]).ToString() != ")")
                                        {
                                            result.Add((value[i]).ToString());
                                            i += 1;
                                            continue;
                                        }
                                        inner = ParableFunctions._Substring(value, i + 2, j - 1);
                                        if (inArith)
                                        {
                                            result.Add(direction + "(" + inner + ")");
                                        }
                                        else
                                        {
                                            if ((!string.IsNullOrEmpty(inner.Trim(" \t\n\r".ToCharArray()))))
                                            {
                                                stripped = inner.TrimStart(" \t".ToCharArray());
                                                result.Add(direction + "(" + stripped + ")");
                                            }
                                            else
                                            {
                                                result.Add(direction + "(" + inner + ")");
                                            }
                                        }
                                        i = j;
                                    }
                                    else
                                    {
                                        result.Add((value[i]).ToString());
                                        i += 1;
                                    }
                                }
                            }
                        }
                        else
                        {
                            int depth = 0;
                            if ((ParableFunctions._IsExpansionStart(value, i, "${ ") || ParableFunctions._IsExpansionStart(value, i, "${\t") || ParableFunctions._IsExpansionStart(value, i, "${\n") || ParableFunctions._IsExpansionStart(value, i, "${|")) && !(ParableFunctions._IsBackslashEscaped(value, i)))
                            {
                                prefix = ParableFunctions._Substring(value, i, i + 3).Replace("\t", " ").Replace("\n", " ");
                                j = i + 3;
                                depth = 1;
                                while (j < value.Length && depth > 0)
                                {
                                    if ((value[j]).ToString() == "{")
                                    {
                                        depth += 1;
                                    }
                                    else
                                    {
                                        if ((value[j]).ToString() == "}")
                                        {
                                            depth -= 1;
                                        }
                                    }
                                    j += 1;
                                }
                                inner = ParableFunctions._Substring(value, i + 2, j - 1);
                                if (inner.Trim(" \t\n\r".ToCharArray()) == "")
                                {
                                    result.Add("${ }");
                                }
                                else
                                {
                                    try
                                    {
                                        parser = ParableFunctions.NewParser(inner.TrimStart(" \t\n|".ToCharArray()), false, false);
                                        parsed = parser.ParseList(true);
                                        if (parsed != null)
                                        {
                                            formatted = ParableFunctions._FormatCmdsubNode(parsed, 0, false, false, false);
                                            formatted = formatted.TrimEnd(";".ToCharArray());
                                            string terminator = "";
                                            if (inner.TrimEnd(" \t".ToCharArray()).EndsWith("\n"))
                                            {
                                                terminator = "\n }";
                                            }
                                            else
                                            {
                                                if (formatted.EndsWith(" &"))
                                                {
                                                    terminator = " }";
                                                }
                                                else
                                                {
                                                    terminator = "; }";
                                                }
                                            }
                                            result.Add(prefix + formatted + terminator);
                                        }
                                        else
                                        {
                                            result.Add("${ }");
                                        }
                                    } catch (Exception)
                                    {
                                        result.Add(ParableFunctions._Substring(value, i, j));
                                    }
                                }
                                i = j;
                            }
                            else
                            {
                                if (ParableFunctions._IsExpansionStart(value, i, "${") && !(ParableFunctions._IsBackslashEscaped(value, i)))
                                {
                                    j = i + 2;
                                    depth = 1;
                                    QuoteState braceQuote = ParableFunctions.NewQuoteState();
                                    while (j < value.Length && depth > 0)
                                    {
                                        string c = (value[j]).ToString();
                                        if (c == "\\" && j + 1 < value.Length && !(braceQuote.Single))
                                        {
                                            j += 2;
                                            continue;
                                        }
                                        if (c == "'" && !(braceQuote.Double))
                                        {
                                            braceQuote.Single = !(braceQuote.Single);
                                        }
                                        else
                                        {
                                            if (c == "\"" && !(braceQuote.Single))
                                            {
                                                braceQuote.Double = !(braceQuote.Double);
                                            }
                                            else
                                            {
                                                if (!(braceQuote.InQuotes()))
                                                {
                                                    if (ParableFunctions._IsExpansionStart(value, j, "$(") && !(ParableFunctions._StartsWithAt(value, j, "$((")))
                                                    {
                                                        j = ParableFunctions._FindCmdsubEnd(value, j + 2);
                                                        continue;
                                                    }
                                                    if (c == "{")
                                                    {
                                                        depth += 1;
                                                    }
                                                    else
                                                    {
                                                        if (c == "}")
                                                        {
                                                            depth -= 1;
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                        j += 1;
                                    }
                                    if (depth > 0)
                                    {
                                        inner = ParableFunctions._Substring(value, i + 2, j);
                                    }
                                    else
                                    {
                                        inner = ParableFunctions._Substring(value, i + 2, j - 1);
                                    }
                                    string formattedInner = this._FormatCommandSubstitutions(inner, false);
                                    formattedInner = this._NormalizeExtglobWhitespace(formattedInner);
                                    if (depth == 0)
                                    {
                                        result.Add("${" + formattedInner + "}");
                                    }
                                    else
                                    {
                                        result.Add("${" + formattedInner);
                                    }
                                    i = j;
                                }
                                else
                                {
                                    if ((value[i]).ToString() == "\"")
                                    {
                                        mainQuote.Double = !(mainQuote.Double);
                                        result.Add((value[i]).ToString());
                                        i += 1;
                                    }
                                    else
                                    {
                                        if ((value[i]).ToString() == "'" && !(mainQuote.Double))
                                        {
                                            j = i + 1;
                                            while (j < value.Length && (value[j]).ToString() != "'")
                                            {
                                                j += 1;
                                            }
                                            if (j < value.Length)
                                            {
                                                j += 1;
                                            }
                                            result.Add(ParableFunctions._Substring(value, i, j));
                                            i = j;
                                        }
                                        else
                                        {
                                            result.Add((value[i]).ToString());
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
        return string.Join("", result);
    }

    public string _NormalizeExtglobWhitespace(string value)
    {
        List<string> result = new List<string>();
        int i = 0;
        QuoteState extglobQuote = ParableFunctions.NewQuoteState();
        int deprecatedArithDepth = 0;
        while (i < value.Length)
        {
            if ((value[i]).ToString() == "\"")
            {
                extglobQuote.Double = !(extglobQuote.Double);
                result.Add((value[i]).ToString());
                i += 1;
                continue;
            }
            if (ParableFunctions._StartsWithAt(value, i, "$[") && !(ParableFunctions._IsBackslashEscaped(value, i)))
            {
                deprecatedArithDepth += 1;
                result.Add((value[i]).ToString());
                i += 1;
                continue;
            }
            if ((value[i]).ToString() == "]" && deprecatedArithDepth > 0)
            {
                deprecatedArithDepth -= 1;
                result.Add((value[i]).ToString());
                i += 1;
                continue;
            }
            if (i + 1 < value.Length && (value[i + 1]).ToString() == "(")
            {
                string prefixChar = (value[i]).ToString();
                if ("><".Contains(prefixChar) && !(extglobQuote.Double) && deprecatedArithDepth == 0)
                {
                    result.Add(prefixChar);
                    result.Add("(");
                    i += 2;
                    int depth = 1;
                    List<string> patternParts = new List<string>();
                    List<string> currentPart = new List<string>();
                    bool hasPipe = false;
                    while (i < value.Length && depth > 0)
                    {
                        if ((value[i]).ToString() == "\\" && i + 1 < value.Length)
                        {
                            currentPart.Add(value.Substring(i, (i + 2) - (i)));
                            i += 2;
                            continue;
                        }
                        else
                        {
                            if ((value[i]).ToString() == "(")
                            {
                                depth += 1;
                                currentPart.Add((value[i]).ToString());
                                i += 1;
                            }
                            else
                            {
                                string partContent = "";
                                if ((value[i]).ToString() == ")")
                                {
                                    depth -= 1;
                                    if (depth == 0)
                                    {
                                        partContent = string.Join("", currentPart);
                                        if (partContent.Contains("<<"))
                                        {
                                            patternParts.Add(partContent);
                                        }
                                        else
                                        {
                                            if (hasPipe)
                                            {
                                                patternParts.Add(partContent.Trim(" \t\n\r".ToCharArray()));
                                            }
                                            else
                                            {
                                                patternParts.Add(partContent);
                                            }
                                        }
                                        break;
                                    }
                                    currentPart.Add((value[i]).ToString());
                                    i += 1;
                                }
                                else
                                {
                                    if ((value[i]).ToString() == "|" && depth == 1)
                                    {
                                        if (i + 1 < value.Length && (value[i + 1]).ToString() == "|")
                                        {
                                            currentPart.Add("||");
                                            i += 2;
                                        }
                                        else
                                        {
                                            hasPipe = true;
                                            partContent = string.Join("", currentPart);
                                            if (partContent.Contains("<<"))
                                            {
                                                patternParts.Add(partContent);
                                            }
                                            else
                                            {
                                                patternParts.Add(partContent.Trim(" \t\n\r".ToCharArray()));
                                            }
                                            currentPart = new List<string>();
                                            i += 1;
                                        }
                                    }
                                    else
                                    {
                                        currentPart.Add((value[i]).ToString());
                                        i += 1;
                                    }
                                }
                            }
                        }
                    }
                    result.Add(string.Join(" | ", patternParts));
                    if (depth == 0)
                    {
                        result.Add(")");
                        i += 1;
                    }
                    continue;
                }
            }
            result.Add((value[i]).ToString());
            i += 1;
        }
        return string.Join("", result);
    }

    public string GetCondFormattedValue()
    {
        string value = this._ExpandAllAnsiCQuotes(this.Value);
        value = this._StripLocaleStringDollars(value);
        value = this._FormatCommandSubstitutions(value, false);
        value = this._NormalizeExtglobWhitespace(value);
        value = value.Replace("\u0001", "\u0001\u0001");
        return value.TrimEnd("\n".ToCharArray());
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class Command : INode
{
    public List<Word> Words { get; set; }
    public List<INode> Redirects { get; set; }
    public string Kind { get; set; }

    public Command(List<Word> words, List<INode> redirects, string kind)
    {
        this.Words = words;
        this.Redirects = redirects;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        List<string> parts = new List<string>();
        foreach (Word w in this.Words)
        {
            parts.Add(((INode)w).ToSexp());
        }
        foreach (INode r in this.Redirects)
        {
            parts.Add(((INode)r).ToSexp());
        }
        string inner = string.Join(" ", parts);
        if (!((!string.IsNullOrEmpty(inner))))
        {
            return "(command)";
        }
        return "(command " + inner + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class Pipeline : INode
{
    public List<INode> Commands { get; set; }
    public string Kind { get; set; }

    public Pipeline(List<INode> commands, string kind)
    {
        this.Commands = commands;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        if (this.Commands.Count == 1)
        {
            return ((INode)this.Commands[0]).ToSexp();
        }
        List<(INode, bool)> cmds = new List<(INode, bool)>();
        int i = 0;
        INode cmd = null;
        while (i < this.Commands.Count)
        {
            cmd = this.Commands[i];
            switch (cmd)
            {
                case PipeBoth cmdPipeBoth:
                    i += 1;
                    continue;
            }
            bool needsRedirect = i + 1 < this.Commands.Count && this.Commands[i + 1].Kind == "pipe-both";
            cmds.Add((cmd, needsRedirect));
            i += 1;
        }
        (INode, bool) pair = (null, false);
        bool needs = false;
        if (cmds.Count == 1)
        {
            pair = cmds[0];
            cmd = pair.Item1;
            needs = pair.Item2;
            return this._CmdSexp(cmd, needs);
        }
        (INode, bool) lastPair = cmds[cmds.Count - 1];
        INode lastCmd = lastPair.Item1;
        bool lastNeeds = lastPair.Item2;
        string result = this._CmdSexp(lastCmd, lastNeeds);
        int j = cmds.Count - 2;
        while (j >= 0)
        {
            pair = cmds[j];
            cmd = pair.Item1;
            needs = pair.Item2;
            if (needs && cmd.Kind != "command")
            {
                result = "(pipe " + ((INode)cmd).ToSexp() + " (redirect \">&\" 1) " + result + ")";
            }
            else
            {
                result = "(pipe " + this._CmdSexp(cmd, needs) + " " + result + ")";
            }
            j -= 1;
        }
        return result;
    }

    public string _CmdSexp(INode cmd, bool needsRedirect)
    {
        if (!(needsRedirect))
        {
            return ((INode)cmd).ToSexp();
        }
        switch (cmd)
        {
            case Command cmdCommand:
                List<string> parts = new List<string>();
                foreach (Word w in cmdCommand.Words)
                {
                    parts.Add(((INode)w).ToSexp());
                }
                foreach (INode r in cmdCommand.Redirects)
                {
                    parts.Add(((INode)r).ToSexp());
                }
                parts.Add("(redirect \">&\" 1)");
                return "(command " + string.Join(" ", parts) + ")";
        }
        return ((INode)cmd).ToSexp();
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class List : INode
{
    public List<INode> Parts { get; set; }
    public string Kind { get; set; }

    public List(List<INode> parts, string kind)
    {
        this.Parts = parts;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        List<INode> parts = new List<INode>(this.Parts);
        Dictionary<string, string> opNames = new Dictionary<string, string> { { "&&", "and" }, { "||", "or" }, { ";", "semi" }, { "\n", "semi" }, { "&", "background" } };
        while (parts.Count > 1 && parts[parts.Count - 1].Kind == "operator" && (((Operator)parts[parts.Count - 1]).Op == ";" || ((Operator)parts[parts.Count - 1]).Op == "\n"))
        {
            parts = ParableFunctions._Sublist(parts, 0, parts.Count - 1);
        }
        if (parts.Count == 1)
        {
            return ((INode)parts[0]).ToSexp();
        }
        if (parts[parts.Count - 1].Kind == "operator" && ((Operator)parts[parts.Count - 1]).Op == "&")
        {
            for (int i = parts.Count - 3; i > 0; i += -2)
            {
                if (parts[i].Kind == "operator" && (((Operator)parts[i]).Op == ";" || ((Operator)parts[i]).Op == "\n"))
                {
                    List<INode> left = ParableFunctions._Sublist(parts, 0, i);
                    List<INode> right = ParableFunctions._Sublist(parts, i + 1, parts.Count - 1);
                    string leftSexp = "";
                    if (left.Count > 1)
                    {
                        leftSexp = ((INode)new List(left, "list")).ToSexp();
                    }
                    else
                    {
                        leftSexp = ((INode)left[0]).ToSexp();
                    }
                    string rightSexp = "";
                    if (right.Count > 1)
                    {
                        rightSexp = ((INode)new List(right, "list")).ToSexp();
                    }
                    else
                    {
                        rightSexp = ((INode)right[0]).ToSexp();
                    }
                    return "(semi " + leftSexp + " (background " + rightSexp + "))";
                }
            }
            List<INode> innerParts = ParableFunctions._Sublist(parts, 0, parts.Count - 1);
            if (innerParts.Count == 1)
            {
                return "(background " + ((INode)innerParts[0]).ToSexp() + ")";
            }
            List innerList = new List(innerParts, "list");
            return "(background " + ((INode)innerList).ToSexp() + ")";
        }
        return this._ToSexpWithPrecedence(parts, opNames);
    }

    public string _ToSexpWithPrecedence(List<INode> parts, Dictionary<string, string> opNames)
    {
        List<int> semiPositions = new List<int>();
        for (int i = 0; i < parts.Count; i += 1)
        {
            if (parts[i].Kind == "operator" && (((Operator)parts[i]).Op == ";" || ((Operator)parts[i]).Op == "\n"))
            {
                semiPositions.Add(i);
            }
        }
        if ((semiPositions.Count > 0))
        {
            List<List<INode>> segments = new List<List<INode>>();
            int start = 0;
            List<INode> seg = new List<INode>();
            foreach (int pos in semiPositions)
            {
                seg = ParableFunctions._Sublist(parts, start, pos);
                if ((seg.Count > 0) && seg[0].Kind != "operator")
                {
                    segments.Add(seg);
                }
                start = pos + 1;
            }
            seg = ParableFunctions._Sublist(parts, start, parts.Count);
            if ((seg.Count > 0) && seg[0].Kind != "operator")
            {
                segments.Add(seg);
            }
            if (!((segments.Count > 0)))
            {
                return "()";
            }
            string result = this._ToSexpAmpAndHigher(segments[0], opNames);
            for (int i = 1; i < segments.Count; i += 1)
            {
                result = "(semi " + result + " " + this._ToSexpAmpAndHigher(segments[i], opNames) + ")";
            }
            return result;
        }
        return this._ToSexpAmpAndHigher(parts, opNames);
    }

    public string _ToSexpAmpAndHigher(List<INode> parts, Dictionary<string, string> opNames)
    {
        if (parts.Count == 1)
        {
            return ((INode)parts[0]).ToSexp();
        }
        List<int> ampPositions = new List<int>();
        for (int i = 1; i < parts.Count - 1; i += 2)
        {
            if (parts[i].Kind == "operator" && ((Operator)parts[i]).Op == "&")
            {
                ampPositions.Add(i);
            }
        }
        if ((ampPositions.Count > 0))
        {
            List<List<INode>> segments = new List<List<INode>>();
            int start = 0;
            foreach (int pos in ampPositions)
            {
                segments.Add(ParableFunctions._Sublist(parts, start, pos));
                start = pos + 1;
            }
            segments.Add(ParableFunctions._Sublist(parts, start, parts.Count));
            string result = this._ToSexpAndOr(segments[0], opNames);
            for (int i = 1; i < segments.Count; i += 1)
            {
                result = "(background " + result + " " + this._ToSexpAndOr(segments[i], opNames) + ")";
            }
            return result;
        }
        return this._ToSexpAndOr(parts, opNames);
    }

    public string _ToSexpAndOr(List<INode> parts, Dictionary<string, string> opNames)
    {
        if (parts.Count == 1)
        {
            return ((INode)parts[0]).ToSexp();
        }
        string result = ((INode)parts[0]).ToSexp();
        for (int i = 1; i < parts.Count - 1; i += 2)
        {
            INode op = parts[i];
            INode cmd = parts[i + 1];
            string opName = (opNames.TryGetValue(((Operator)op).Op, out var _v) ? _v : ((Operator)op).Op);
            result = "(" + opName + " " + result + " " + ((INode)cmd).ToSexp() + ")";
        }
        return result;
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class Operator : INode
{
    public string Op { get; set; }
    public string Kind { get; set; }

    public Operator(string op, string kind)
    {
        this.Op = op;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        Dictionary<string, string> names = new Dictionary<string, string> { { "&&", "and" }, { "||", "or" }, { ";", "semi" }, { "&", "bg" }, { "|", "pipe" } };
        return "(" + (names.TryGetValue(this.Op, out var _v) ? _v : this.Op) + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class PipeBoth : INode
{
    public string Kind { get; set; }

    public PipeBoth(string kind)
    {
        this.Kind = kind;
    }

    public string ToSexp()
    {
        return "(pipe-both)";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class Empty : INode
{
    public string Kind { get; set; }

    public Empty(string kind)
    {
        this.Kind = kind;
    }

    public string ToSexp()
    {
        return "";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class Comment : INode
{
    public string Text { get; set; }
    public string Kind { get; set; }

    public Comment(string text, string kind)
    {
        this.Text = text;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        return "";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class Redirect : INode
{
    public string Op { get; set; }
    public Word Target { get; set; }
    public int? Fd { get; set; }
    public string Kind { get; set; }

    public Redirect(string op, Word target, int? fd, string kind)
    {
        this.Op = op;
        this.Target = target;
        this.Fd = fd;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        string op = this.Op.TrimStart("0123456789".ToCharArray());
        if (op.StartsWith("{"))
        {
            int j = 1;
            if (j < op.Length && (((op[j]).ToString().Length > 0 && (op[j]).ToString().All(char.IsLetter)) || (op[j]).ToString() == "_"))
            {
                j += 1;
                while (j < op.Length && (((op[j]).ToString().Length > 0 && (op[j]).ToString().All(char.IsLetterOrDigit)) || (op[j]).ToString() == "_"))
                {
                    j += 1;
                }
                if (j < op.Length && (op[j]).ToString() == "[")
                {
                    j += 1;
                    while (j < op.Length && (op[j]).ToString() != "]")
                    {
                        j += 1;
                    }
                    if (j < op.Length && (op[j]).ToString() == "]")
                    {
                        j += 1;
                    }
                }
                if (j < op.Length && (op[j]).ToString() == "}")
                {
                    op = ParableFunctions._Substring(op, j + 1, op.Length);
                }
            }
        }
        string targetVal = this.Target.Value;
        targetVal = this.Target._ExpandAllAnsiCQuotes(targetVal);
        targetVal = this.Target._StripLocaleStringDollars(targetVal);
        targetVal = this.Target._FormatCommandSubstitutions(targetVal, false);
        targetVal = this.Target._StripArithLineContinuations(targetVal);
        if (targetVal.EndsWith("\\") && !(targetVal.EndsWith("\\\\")))
        {
            targetVal = targetVal + "\\";
        }
        if (targetVal.StartsWith("&"))
        {
            if (op == ">")
            {
                op = ">&";
            }
            else
            {
                if (op == "<")
                {
                    op = "<&";
                }
            }
            string raw = ParableFunctions._Substring(targetVal, 1, targetVal.Length);
            if ((raw.Length > 0 && raw.All(char.IsDigit)) && Convert.ToInt64(raw, 10) <= 2147483647)
            {
                return "(redirect \"" + op + "\" " + ((int)Convert.ToInt64(raw, 10)).ToString() + ")";
            }
            if (raw.EndsWith("-") && (raw.Substring(0, raw.Length - 1).Length > 0 && raw.Substring(0, raw.Length - 1).All(char.IsDigit)) && Convert.ToInt64(raw.Substring(0, raw.Length - 1), 10) <= 2147483647)
            {
                return "(redirect \"" + op + "\" " + ((int)Convert.ToInt64(raw.Substring(0, raw.Length - 1), 10)).ToString() + ")";
            }
            if (targetVal == "&-")
            {
                return "(redirect \">&-\" 0)";
            }
            string fdTarget = (raw.EndsWith("-") ? raw.Substring(0, raw.Length - 1) : raw);
            return "(redirect \"" + op + "\" \"" + fdTarget + "\")";
        }
        if (op == ">&" || op == "<&")
        {
            if ((targetVal.Length > 0 && targetVal.All(char.IsDigit)) && Convert.ToInt64(targetVal, 10) <= 2147483647)
            {
                return "(redirect \"" + op + "\" " + ((int)Convert.ToInt64(targetVal, 10)).ToString() + ")";
            }
            if (targetVal == "-")
            {
                return "(redirect \">&-\" 0)";
            }
            if (targetVal.EndsWith("-") && (targetVal.Substring(0, targetVal.Length - 1).Length > 0 && targetVal.Substring(0, targetVal.Length - 1).All(char.IsDigit)) && Convert.ToInt64(targetVal.Substring(0, targetVal.Length - 1), 10) <= 2147483647)
            {
                return "(redirect \"" + op + "\" " + ((int)Convert.ToInt64(targetVal.Substring(0, targetVal.Length - 1), 10)).ToString() + ")";
            }
            string outVal = (targetVal.EndsWith("-") ? targetVal.Substring(0, targetVal.Length - 1) : targetVal);
            return "(redirect \"" + op + "\" \"" + outVal + "\")";
        }
        return "(redirect \"" + op + "\" \"" + targetVal + "\")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class HereDoc : INode
{
    public string Delimiter { get; set; }
    public string Content { get; set; }
    public bool StripTabs { get; set; }
    public bool Quoted { get; set; }
    public int? Fd { get; set; }
    public bool Complete { get; set; }
    public int _StartPos { get; set; }
    public string Kind { get; set; }

    public HereDoc(string delimiter, string content, bool stripTabs, bool quoted, int? fd, bool complete, int _startPos, string kind)
    {
        this.Delimiter = delimiter;
        this.Content = content;
        this.StripTabs = stripTabs;
        this.Quoted = quoted;
        this.Fd = fd;
        this.Complete = complete;
        this._StartPos = _startPos;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        string op = (this.StripTabs ? "<<-" : "<<");
        string content = this.Content;
        if (content.EndsWith("\\") && !(content.EndsWith("\\\\")))
        {
            content = content + "\\";
        }
        return string.Format("(redirect \"{0}\" \"{1}\")", op, content);
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class Subshell : INode
{
    public INode Body { get; set; }
    public List<INode> Redirects { get; set; }
    public string Kind { get; set; }

    public Subshell(INode body, List<INode> redirects, string kind)
    {
        this.Body = body;
        this.Redirects = redirects;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        string @base = "(subshell " + ((INode)this.Body).ToSexp() + ")";
        return ParableFunctions._AppendRedirects(@base, this.Redirects);
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class BraceGroup : INode
{
    public INode Body { get; set; }
    public List<INode> Redirects { get; set; }
    public string Kind { get; set; }

    public BraceGroup(INode body, List<INode> redirects, string kind)
    {
        this.Body = body;
        this.Redirects = redirects;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        string @base = "(brace-group " + ((INode)this.Body).ToSexp() + ")";
        return ParableFunctions._AppendRedirects(@base, this.Redirects);
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class If : INode
{
    public INode Condition { get; set; }
    public INode ThenBody { get; set; }
    public INode ElseBody { get; set; }
    public List<INode> Redirects { get; set; }
    public string Kind { get; set; }

    public If(INode condition, INode thenBody, INode elseBody, List<INode> redirects, string kind)
    {
        this.Condition = condition;
        this.ThenBody = thenBody;
        this.ElseBody = elseBody;
        this.Redirects = redirects;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        string result = "(if " + ((INode)this.Condition).ToSexp() + " " + ((INode)this.ThenBody).ToSexp();
        if (this.ElseBody != null)
        {
            result = result + " " + ((INode)this.ElseBody).ToSexp();
        }
        result = result + ")";
        foreach (INode r in this.Redirects)
        {
            result = result + " " + ((INode)r).ToSexp();
        }
        return result;
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class While : INode
{
    public INode Condition { get; set; }
    public INode Body { get; set; }
    public List<INode> Redirects { get; set; }
    public string Kind { get; set; }

    public While(INode condition, INode body, List<INode> redirects, string kind)
    {
        this.Condition = condition;
        this.Body = body;
        this.Redirects = redirects;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        string @base = "(while " + ((INode)this.Condition).ToSexp() + " " + ((INode)this.Body).ToSexp() + ")";
        return ParableFunctions._AppendRedirects(@base, this.Redirects);
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class Until : INode
{
    public INode Condition { get; set; }
    public INode Body { get; set; }
    public List<INode> Redirects { get; set; }
    public string Kind { get; set; }

    public Until(INode condition, INode body, List<INode> redirects, string kind)
    {
        this.Condition = condition;
        this.Body = body;
        this.Redirects = redirects;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        string @base = "(until " + ((INode)this.Condition).ToSexp() + " " + ((INode)this.Body).ToSexp() + ")";
        return ParableFunctions._AppendRedirects(@base, this.Redirects);
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class For : INode
{
    public string Var { get; set; }
    public List<Word> Words { get; set; }
    public INode Body { get; set; }
    public List<INode> Redirects { get; set; }
    public string Kind { get; set; }

    public For(string var, List<Word> words, INode body, List<INode> redirects, string kind)
    {
        this.Var = var;
        this.Words = words;
        this.Body = body;
        this.Redirects = redirects;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        string suffix = "";
        if ((this.Redirects.Count > 0))
        {
            List<string> redirectParts = new List<string>();
            foreach (INode r in this.Redirects)
            {
                redirectParts.Add(((INode)r).ToSexp());
            }
            suffix = " " + string.Join(" ", redirectParts);
        }
        Word tempWord = new Word(this.Var, new List<INode>(), "word");
        string varFormatted = tempWord._FormatCommandSubstitutions(this.Var, false);
        string varEscaped = varFormatted.Replace("\\", "\\\\").Replace("\"", "\\\"");
        if (this.Words == null)
        {
            return "(for (word \"" + varEscaped + "\") (in (word \"\\\"$@\\\"\")) " + ((INode)this.Body).ToSexp() + ")" + suffix;
        }
        else
        {
            if (this.Words.Count == 0)
            {
                return "(for (word \"" + varEscaped + "\") (in) " + ((INode)this.Body).ToSexp() + ")" + suffix;
            }
            else
            {
                List<string> wordParts = new List<string>();
                foreach (Word w in this.Words)
                {
                    wordParts.Add(((INode)w).ToSexp());
                }
                string wordStrs = string.Join(" ", wordParts);
                return "(for (word \"" + varEscaped + "\") (in " + wordStrs + ") " + ((INode)this.Body).ToSexp() + ")" + suffix;
            }
        }
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ForArith : INode
{
    public string Init { get; set; }
    public string Cond { get; set; }
    public string Incr { get; set; }
    public INode Body { get; set; }
    public List<INode> Redirects { get; set; }
    public string Kind { get; set; }

    public ForArith(string init, string cond, string incr, INode body, List<INode> redirects, string kind)
    {
        this.Init = init;
        this.Cond = cond;
        this.Incr = incr;
        this.Body = body;
        this.Redirects = redirects;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        string suffix = "";
        if ((this.Redirects.Count > 0))
        {
            List<string> redirectParts = new List<string>();
            foreach (INode r in this.Redirects)
            {
                redirectParts.Add(((INode)r).ToSexp());
            }
            suffix = " " + string.Join(" ", redirectParts);
        }
        string initVal = ((!string.IsNullOrEmpty(this.Init)) ? this.Init : "1");
        string condVal = ((!string.IsNullOrEmpty(this.Cond)) ? this.Cond : "1");
        string incrVal = ((!string.IsNullOrEmpty(this.Incr)) ? this.Incr : "1");
        string initStr = ParableFunctions._FormatArithVal(initVal);
        string condStr = ParableFunctions._FormatArithVal(condVal);
        string incrStr = ParableFunctions._FormatArithVal(incrVal);
        string bodyStr = ((INode)this.Body).ToSexp();
        return string.Format("(arith-for (init (word \"{0}\")) (test (word \"{1}\")) (step (word \"{2}\")) {3}){4}", initStr, condStr, incrStr, bodyStr, suffix);
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class Select : INode
{
    public string Var { get; set; }
    public List<Word> Words { get; set; }
    public INode Body { get; set; }
    public List<INode> Redirects { get; set; }
    public string Kind { get; set; }

    public Select(string var, List<Word> words, INode body, List<INode> redirects, string kind)
    {
        this.Var = var;
        this.Words = words;
        this.Body = body;
        this.Redirects = redirects;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        string suffix = "";
        if ((this.Redirects.Count > 0))
        {
            List<string> redirectParts = new List<string>();
            foreach (INode r in this.Redirects)
            {
                redirectParts.Add(((INode)r).ToSexp());
            }
            suffix = " " + string.Join(" ", redirectParts);
        }
        string varEscaped = this.Var.Replace("\\", "\\\\").Replace("\"", "\\\"");
        string inClause = "";
        if (this.Words != null)
        {
            List<string> wordParts = new List<string>();
            foreach (Word w in this.Words)
            {
                wordParts.Add(((INode)w).ToSexp());
            }
            string wordStrs = string.Join(" ", wordParts);
            if ((this.Words.Count > 0))
            {
                inClause = "(in " + wordStrs + ")";
            }
            else
            {
                inClause = "(in)";
            }
        }
        else
        {
            inClause = "(in (word \"\\\"$@\\\"\"))";
        }
        return "(select (word \"" + varEscaped + "\") " + inClause + " " + ((INode)this.Body).ToSexp() + ")" + suffix;
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class Case : INode
{
    public INode Word { get; set; }
    public List<INode> Patterns { get; set; }
    public List<INode> Redirects { get; set; }
    public string Kind { get; set; }

    public Case(INode word, List<INode> patterns, List<INode> redirects, string kind)
    {
        this.Word = word;
        this.Patterns = patterns;
        this.Redirects = redirects;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        List<string> parts = new List<string>();
        parts.Add("(case " + ((INode)this.Word).ToSexp());
        foreach (INode p in this.Patterns)
        {
            parts.Add(((INode)p).ToSexp());
        }
        string @base = string.Join(" ", parts) + ")";
        return ParableFunctions._AppendRedirects(@base, this.Redirects);
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class CasePattern : INode
{
    public string Pattern { get; set; }
    public INode Body { get; set; }
    public string Terminator { get; set; }
    public string Kind { get; set; }

    public CasePattern(string pattern, INode body, string terminator, string kind)
    {
        this.Pattern = pattern;
        this.Body = body;
        this.Terminator = terminator;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        List<string> alternatives = new List<string>();
        List<string> current = new List<string>();
        int i = 0;
        int depth = 0;
        while (i < this.Pattern.Length)
        {
            string ch = (this.Pattern[i]).ToString();
            if (ch == "\\" && i + 1 < this.Pattern.Length)
            {
                current.Add(ParableFunctions._Substring(this.Pattern, i, i + 2));
                i += 2;
            }
            else
            {
                if ((ch == "@" || ch == "?" || ch == "*" || ch == "+" || ch == "!") && i + 1 < this.Pattern.Length && (this.Pattern[i + 1]).ToString() == "(")
                {
                    current.Add(ch);
                    current.Add("(");
                    depth += 1;
                    i += 2;
                }
                else
                {
                    if (ParableFunctions._IsExpansionStart(this.Pattern, i, "$("))
                    {
                        current.Add(ch);
                        current.Add("(");
                        depth += 1;
                        i += 2;
                    }
                    else
                    {
                        if (ch == "(" && depth > 0)
                        {
                            current.Add(ch);
                            depth += 1;
                            i += 1;
                        }
                        else
                        {
                            if (ch == ")" && depth > 0)
                            {
                                current.Add(ch);
                                depth -= 1;
                                i += 1;
                            }
                            else
                            {
                                int result0 = 0;
                                List<string> result1 = new List<string>();
                                if (ch == "[")
                                {
                                    (result0, result1, bool result2) = ParableFunctions._ConsumeBracketClass(this.Pattern, i, depth);
                                    i = result0;
                                    current.AddRange(result1);
                                }
                                else
                                {
                                    if (ch == "'" && depth == 0)
                                    {
                                        (result0, result1) = ParableFunctions._ConsumeSingleQuote(this.Pattern, i);
                                        i = result0;
                                        current.AddRange(result1);
                                    }
                                    else
                                    {
                                        if (ch == "\"" && depth == 0)
                                        {
                                            (result0, result1) = ParableFunctions._ConsumeDoubleQuote(this.Pattern, i);
                                            i = result0;
                                            current.AddRange(result1);
                                        }
                                        else
                                        {
                                            if (ch == "|" && depth == 0)
                                            {
                                                alternatives.Add(string.Join("", current));
                                                current = new List<string>();
                                                i += 1;
                                            }
                                            else
                                            {
                                                current.Add(ch);
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
        alternatives.Add(string.Join("", current));
        List<string> wordList = new List<string>();
        foreach (string alt in alternatives)
        {
            wordList.Add(((INode)new Word(alt, new List<INode>(), "word")).ToSexp());
        }
        string patternStr = string.Join(" ", wordList);
        List<string> parts = new List<string> { "(pattern (" + patternStr + ")" };
        if (this.Body != null)
        {
            parts.Add(" " + ((INode)this.Body).ToSexp());
        }
        else
        {
            parts.Add(" ()");
        }
        parts.Add(")");
        return string.Join("", parts);
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class Function : INode
{
    public string Name { get; set; }
    public INode Body { get; set; }
    public string Kind { get; set; }

    public Function(string name, INode body, string kind)
    {
        this.Name = name;
        this.Body = body;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        return "(function \"" + this.Name + "\" " + ((INode)this.Body).ToSexp() + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ParamExpansion : INode
{
    public string Param { get; set; }
    public string Op { get; set; }
    public string Arg { get; set; }
    public string Kind { get; set; }

    public ParamExpansion(string param, string op, string arg, string kind)
    {
        this.Param = param;
        this.Op = op;
        this.Arg = arg;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        string escapedParam = this.Param.Replace("\\", "\\\\").Replace("\"", "\\\"");
        if (this.Op != "")
        {
            string escapedOp = this.Op.Replace("\\", "\\\\").Replace("\"", "\\\"");
            string argVal = "";
            if (this.Arg != "")
            {
                argVal = this.Arg;
            }
            else
            {
                argVal = "";
            }
            string escapedArg = argVal.Replace("\\", "\\\\").Replace("\"", "\\\"");
            return "(param \"" + escapedParam + "\" \"" + escapedOp + "\" \"" + escapedArg + "\")";
        }
        return "(param \"" + escapedParam + "\")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ParamLength : INode
{
    public string Param { get; set; }
    public string Kind { get; set; }

    public ParamLength(string param, string kind)
    {
        this.Param = param;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        string escaped = this.Param.Replace("\\", "\\\\").Replace("\"", "\\\"");
        return "(param-len \"" + escaped + "\")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ParamIndirect : INode
{
    public string Param { get; set; }
    public string Op { get; set; }
    public string Arg { get; set; }
    public string Kind { get; set; }

    public ParamIndirect(string param, string op, string arg, string kind)
    {
        this.Param = param;
        this.Op = op;
        this.Arg = arg;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        string escaped = this.Param.Replace("\\", "\\\\").Replace("\"", "\\\"");
        if (this.Op != "")
        {
            string escapedOp = this.Op.Replace("\\", "\\\\").Replace("\"", "\\\"");
            string argVal = "";
            if (this.Arg != "")
            {
                argVal = this.Arg;
            }
            else
            {
                argVal = "";
            }
            string escapedArg = argVal.Replace("\\", "\\\\").Replace("\"", "\\\"");
            return "(param-indirect \"" + escaped + "\" \"" + escapedOp + "\" \"" + escapedArg + "\")";
        }
        return "(param-indirect \"" + escaped + "\")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class CommandSubstitution : INode
{
    public INode Command { get; set; }
    public bool Brace { get; set; }
    public string Kind { get; set; }

    public CommandSubstitution(INode command, bool brace, string kind)
    {
        this.Command = command;
        this.Brace = brace;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        if (this.Brace)
        {
            return "(funsub " + ((INode)this.Command).ToSexp() + ")";
        }
        return "(cmdsub " + ((INode)this.Command).ToSexp() + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ArithmeticExpansion : INode
{
    public INode Expression { get; set; }
    public string Kind { get; set; }

    public ArithmeticExpansion(INode expression, string kind)
    {
        this.Expression = expression;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        if (this.Expression == null)
        {
            return "(arith)";
        }
        return "(arith " + ((INode)this.Expression).ToSexp() + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ArithmeticCommand : INode
{
    public INode Expression { get; set; }
    public List<INode> Redirects { get; set; }
    public string RawContent { get; set; }
    public string Kind { get; set; }

    public ArithmeticCommand(INode expression, List<INode> redirects, string rawContent, string kind)
    {
        this.Expression = expression;
        this.Redirects = redirects;
        this.RawContent = rawContent;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        string formatted = new Word(this.RawContent, new List<INode>(), "word")._FormatCommandSubstitutions(this.RawContent, true);
        string escaped = formatted.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", "\\n").Replace("\t", "\\t");
        string result = "(arith (word \"" + escaped + "\"))";
        if ((this.Redirects.Count > 0))
        {
            List<string> redirectParts = new List<string>();
            foreach (INode r in this.Redirects)
            {
                redirectParts.Add(((INode)r).ToSexp());
            }
            string redirectSexps = string.Join(" ", redirectParts);
            return result + " " + redirectSexps;
        }
        return result;
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ArithNumber : INode
{
    public string Value { get; set; }
    public string Kind { get; set; }

    public ArithNumber(string value, string kind)
    {
        this.Value = value;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        return "(number \"" + this.Value + "\")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ArithEmpty : INode
{
    public string Kind { get; set; }

    public ArithEmpty(string kind)
    {
        this.Kind = kind;
    }

    public string ToSexp()
    {
        return "(empty)";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ArithVar : INode
{
    public string Name { get; set; }
    public string Kind { get; set; }

    public ArithVar(string name, string kind)
    {
        this.Name = name;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        return "(var \"" + this.Name + "\")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ArithBinaryOp : INode
{
    public string Op { get; set; }
    public INode Left { get; set; }
    public INode Right { get; set; }
    public string Kind { get; set; }

    public ArithBinaryOp(string op, INode left, INode right, string kind)
    {
        this.Op = op;
        this.Left = left;
        this.Right = right;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        return "(binary-op \"" + this.Op + "\" " + ((INode)this.Left).ToSexp() + " " + ((INode)this.Right).ToSexp() + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ArithUnaryOp : INode
{
    public string Op { get; set; }
    public INode Operand { get; set; }
    public string Kind { get; set; }

    public ArithUnaryOp(string op, INode operand, string kind)
    {
        this.Op = op;
        this.Operand = operand;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        return "(unary-op \"" + this.Op + "\" " + ((INode)this.Operand).ToSexp() + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ArithPreIncr : INode
{
    public INode Operand { get; set; }
    public string Kind { get; set; }

    public ArithPreIncr(INode operand, string kind)
    {
        this.Operand = operand;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        return "(pre-incr " + ((INode)this.Operand).ToSexp() + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ArithPostIncr : INode
{
    public INode Operand { get; set; }
    public string Kind { get; set; }

    public ArithPostIncr(INode operand, string kind)
    {
        this.Operand = operand;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        return "(post-incr " + ((INode)this.Operand).ToSexp() + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ArithPreDecr : INode
{
    public INode Operand { get; set; }
    public string Kind { get; set; }

    public ArithPreDecr(INode operand, string kind)
    {
        this.Operand = operand;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        return "(pre-decr " + ((INode)this.Operand).ToSexp() + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ArithPostDecr : INode
{
    public INode Operand { get; set; }
    public string Kind { get; set; }

    public ArithPostDecr(INode operand, string kind)
    {
        this.Operand = operand;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        return "(post-decr " + ((INode)this.Operand).ToSexp() + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ArithAssign : INode
{
    public string Op { get; set; }
    public INode Target { get; set; }
    public INode Value { get; set; }
    public string Kind { get; set; }

    public ArithAssign(string op, INode target, INode value, string kind)
    {
        this.Op = op;
        this.Target = target;
        this.Value = value;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        return "(assign \"" + this.Op + "\" " + ((INode)this.Target).ToSexp() + " " + ((INode)this.Value).ToSexp() + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ArithTernary : INode
{
    public INode Condition { get; set; }
    public INode IfTrue { get; set; }
    public INode IfFalse { get; set; }
    public string Kind { get; set; }

    public ArithTernary(INode condition, INode ifTrue, INode ifFalse, string kind)
    {
        this.Condition = condition;
        this.IfTrue = ifTrue;
        this.IfFalse = ifFalse;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        return "(ternary " + ((INode)this.Condition).ToSexp() + " " + ((INode)this.IfTrue).ToSexp() + " " + ((INode)this.IfFalse).ToSexp() + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ArithComma : INode
{
    public INode Left { get; set; }
    public INode Right { get; set; }
    public string Kind { get; set; }

    public ArithComma(INode left, INode right, string kind)
    {
        this.Left = left;
        this.Right = right;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        return "(comma " + ((INode)this.Left).ToSexp() + " " + ((INode)this.Right).ToSexp() + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ArithSubscript : INode
{
    public string Array { get; set; }
    public INode Index { get; set; }
    public string Kind { get; set; }

    public ArithSubscript(string array, INode index, string kind)
    {
        this.Array = array;
        this.Index = index;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        return "(subscript \"" + this.Array + "\" " + ((INode)this.Index).ToSexp() + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ArithEscape : INode
{
    public string Char { get; set; }
    public string Kind { get; set; }

    public ArithEscape(string @char, string kind)
    {
        this.Char = @char;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        return "(escape \"" + this.Char + "\")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ArithDeprecated : INode
{
    public string Expression { get; set; }
    public string Kind { get; set; }

    public ArithDeprecated(string expression, string kind)
    {
        this.Expression = expression;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        string escaped = this.Expression.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", "\\n");
        return "(arith-deprecated \"" + escaped + "\")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ArithConcat : INode
{
    public List<INode> Parts { get; set; }
    public string Kind { get; set; }

    public ArithConcat(List<INode> parts, string kind)
    {
        this.Parts = parts;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        List<string> sexps = new List<string>();
        foreach (INode p in this.Parts)
        {
            sexps.Add(((INode)p).ToSexp());
        }
        return "(arith-concat " + string.Join(" ", sexps) + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class AnsiCQuote : INode
{
    public string Content { get; set; }
    public string Kind { get; set; }

    public AnsiCQuote(string content, string kind)
    {
        this.Content = content;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        string escaped = this.Content.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", "\\n");
        return "(ansi-c \"" + escaped + "\")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class LocaleString : INode
{
    public string Content { get; set; }
    public string Kind { get; set; }

    public LocaleString(string content, string kind)
    {
        this.Content = content;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        string escaped = this.Content.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", "\\n");
        return "(locale \"" + escaped + "\")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ProcessSubstitution : INode
{
    public string Direction { get; set; }
    public INode Command { get; set; }
    public string Kind { get; set; }

    public ProcessSubstitution(string direction, INode command, string kind)
    {
        this.Direction = direction;
        this.Command = command;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        return "(procsub \"" + this.Direction + "\" " + ((INode)this.Command).ToSexp() + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class Negation : INode
{
    public INode Pipeline { get; set; }
    public string Kind { get; set; }

    public Negation(INode pipeline, string kind)
    {
        this.Pipeline = pipeline;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        if (this.Pipeline == null)
        {
            return "(negation (command))";
        }
        return "(negation " + ((INode)this.Pipeline).ToSexp() + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class Time : INode
{
    public INode Pipeline { get; set; }
    public bool Posix { get; set; }
    public string Kind { get; set; }

    public Time(INode pipeline, bool posix, string kind)
    {
        this.Pipeline = pipeline;
        this.Posix = posix;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        if (this.Pipeline == null)
        {
            if (this.Posix)
            {
                return "(time -p (command))";
            }
            else
            {
                return "(time (command))";
            }
        }
        if (this.Posix)
        {
            return "(time -p " + ((INode)this.Pipeline).ToSexp() + ")";
        }
        return "(time " + ((INode)this.Pipeline).ToSexp() + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class ConditionalExpr : INode
{
    public object Body { get; set; }
    public List<INode> Redirects { get; set; }
    public string Kind { get; set; }

    public ConditionalExpr(object body, List<INode> redirects, string kind)
    {
        this.Body = body;
        this.Redirects = redirects;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        object body = this.Body;
        string result = "";
        switch (body)
        {
            case string bodystring:
                string escaped = bodystring.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", "\\n");
                result = "(cond \"" + escaped + "\")";
                break;
            default:
                result = "(cond " + ((INode)body).ToSexp() + ")";
                break;
        }
        if ((this.Redirects.Count > 0))
        {
            List<string> redirectParts = new List<string>();
            foreach (INode r in this.Redirects)
            {
                redirectParts.Add(((INode)r).ToSexp());
            }
            string redirectSexps = string.Join(" ", redirectParts);
            return result + " " + redirectSexps;
        }
        return result;
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class UnaryTest : INode
{
    public string Op { get; set; }
    public INode Operand { get; set; }
    public string Kind { get; set; }

    public UnaryTest(string op, INode operand, string kind)
    {
        this.Op = op;
        this.Operand = operand;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        string operandVal = ((Word)this.Operand).GetCondFormattedValue();
        return "(cond-unary \"" + this.Op + "\" (cond-term \"" + operandVal + "\"))";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class BinaryTest : INode
{
    public string Op { get; set; }
    public INode Left { get; set; }
    public INode Right { get; set; }
    public string Kind { get; set; }

    public BinaryTest(string op, INode left, INode right, string kind)
    {
        this.Op = op;
        this.Left = left;
        this.Right = right;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        string leftVal = ((Word)this.Left).GetCondFormattedValue();
        string rightVal = ((Word)this.Right).GetCondFormattedValue();
        return "(cond-binary \"" + this.Op + "\" (cond-term \"" + leftVal + "\") (cond-term \"" + rightVal + "\"))";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class CondAnd : INode
{
    public INode Left { get; set; }
    public INode Right { get; set; }
    public string Kind { get; set; }

    public CondAnd(INode left, INode right, string kind)
    {
        this.Left = left;
        this.Right = right;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        return "(cond-and " + ((INode)this.Left).ToSexp() + " " + ((INode)this.Right).ToSexp() + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class CondOr : INode
{
    public INode Left { get; set; }
    public INode Right { get; set; }
    public string Kind { get; set; }

    public CondOr(INode left, INode right, string kind)
    {
        this.Left = left;
        this.Right = right;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        return "(cond-or " + ((INode)this.Left).ToSexp() + " " + ((INode)this.Right).ToSexp() + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class CondNot : INode
{
    public INode Operand { get; set; }
    public string Kind { get; set; }

    public CondNot(INode operand, string kind)
    {
        this.Operand = operand;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        return ((INode)this.Operand).ToSexp();
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class CondParen : INode
{
    public INode Inner { get; set; }
    public string Kind { get; set; }

    public CondParen(INode inner, string kind)
    {
        this.Inner = inner;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        return "(cond-expr " + ((INode)this.Inner).ToSexp() + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class Array : INode
{
    public List<Word> Elements { get; set; }
    public string Kind { get; set; }

    public Array(List<Word> elements, string kind)
    {
        this.Elements = elements;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        if (!((this.Elements.Count > 0)))
        {
            return "(array)";
        }
        List<string> parts = new List<string>();
        foreach (Word e in this.Elements)
        {
            parts.Add(((INode)e).ToSexp());
        }
        string inner = string.Join(" ", parts);
        return "(array " + inner + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class Coproc : INode
{
    public INode Command { get; set; }
    public string Name { get; set; }
    public string Kind { get; set; }

    public Coproc(INode command, string name, string kind)
    {
        this.Command = command;
        this.Name = name;
        this.Kind = kind;
    }

    public string ToSexp()
    {
        string name = "";
        if ((!string.IsNullOrEmpty(this.Name)))
        {
            name = this.Name;
        }
        else
        {
            name = "COPROC";
        }
        return "(coproc \"" + name + "\" " + ((INode)this.Command).ToSexp() + ")";
    }

    public string GetKind()
    {
        return this.Kind;
    }
}

public class Parser
{
    public string Source { get; set; }
    public int Pos { get; set; }
    public int Length { get; set; }
    public List<HereDoc> _PendingHeredocs { get; set; }
    public int _CmdsubHeredocEnd { get; set; }
    public bool _SawNewlineInSingleQuote { get; set; }
    public bool _InProcessSub { get; set; }
    public bool _Extglob { get; set; }
    public ContextStack _Ctx { get; set; }
    public Lexer _Lexer { get; set; }
    public List<Token> _TokenHistory { get; set; }
    public int _ParserState { get; set; }
    public int _DolbraceState { get; set; }
    public string _EofToken { get; set; }
    public int _WordContext { get; set; }
    public bool _AtCommandStart { get; set; }
    public bool _InArrayLiteral { get; set; }
    public bool _InAssignBuiltin { get; set; }
    public string _ArithSrc { get; set; }
    public int _ArithPos { get; set; }
    public int _ArithLen { get; set; }

    public Parser(string source, int pos, int length, List<HereDoc> _pendingHeredocs, int _cmdsubHeredocEnd, bool _sawNewlineInSingleQuote, bool _inProcessSub, bool _extglob, ContextStack _ctx, Lexer _lexer, List<Token> _tokenHistory, int _parserState, int _dolbraceState, string _eofToken, int _wordContext, bool _atCommandStart, bool _inArrayLiteral, bool _inAssignBuiltin, string _arithSrc, int _arithPos, int _arithLen)
    {
        this.Source = source;
        this.Pos = pos;
        this.Length = length;
        this._PendingHeredocs = _pendingHeredocs;
        this._CmdsubHeredocEnd = _cmdsubHeredocEnd;
        this._SawNewlineInSingleQuote = _sawNewlineInSingleQuote;
        this._InProcessSub = _inProcessSub;
        this._Extglob = _extglob;
        this._Ctx = _ctx;
        this._Lexer = _lexer;
        this._TokenHistory = _tokenHistory;
        this._ParserState = _parserState;
        this._DolbraceState = _dolbraceState;
        this._EofToken = _eofToken;
        this._WordContext = _wordContext;
        this._AtCommandStart = _atCommandStart;
        this._InArrayLiteral = _inArrayLiteral;
        this._InAssignBuiltin = _inAssignBuiltin;
        this._ArithSrc = _arithSrc;
        this._ArithPos = _arithPos;
        this._ArithLen = _arithLen;
    }

    public void _SetState(int flag)
    {
        this._ParserState = (this._ParserState | flag);
    }

    public void _ClearState(int flag)
    {
        this._ParserState = (this._ParserState & ~flag);
    }

    public bool _InState(int flag)
    {
        return (this._ParserState & flag) != 0;
    }

    public SavedParserState _SaveParserState()
    {
        return new SavedParserState(this._ParserState, this._DolbraceState, null /* TODO: unknown expression */, this._Ctx.CopyStack(), this._EofToken);
    }

    public void _RestoreParserState(SavedParserState saved)
    {
        this._ParserState = saved.ParserState;
        this._DolbraceState = saved.DolbraceState;
        this._EofToken = saved.EofToken;
        this._Ctx.RestoreFrom(saved.CtxStack);
    }

    public void _RecordToken(Token tok)
    {
        this._TokenHistory = new List<Token> { tok, this._TokenHistory[0], this._TokenHistory[1], this._TokenHistory[2] };
    }

    public void _UpdateDolbraceForOp(string op, bool hasParam)
    {
        if (this._DolbraceState == Constants.DOLBRACESTATE_NONE)
        {
            return;
        }
        if (op == "" || op.Length == 0)
        {
            return;
        }
        string firstChar = (op[0]).ToString();
        if (this._DolbraceState == Constants.DOLBRACESTATE_PARAM && hasParam)
        {
            if ("%#^,".Contains(firstChar))
            {
                this._DolbraceState = Constants.DOLBRACESTATE_QUOTE;
                return;
            }
            if (firstChar == "/")
            {
                this._DolbraceState = Constants.DOLBRACESTATE_QUOTE2;
                return;
            }
        }
        if (this._DolbraceState == Constants.DOLBRACESTATE_PARAM)
        {
            if ("#%^,~:-=?+/".Contains(firstChar))
            {
                this._DolbraceState = Constants.DOLBRACESTATE_OP;
            }
        }
    }

    public void _SyncLexer()
    {
        if (this._Lexer._TokenCache != null)
        {
            if (this._Lexer._TokenCache.Pos != this.Pos || this._Lexer._CachedWordContext != this._WordContext || this._Lexer._CachedAtCommandStart != this._AtCommandStart || this._Lexer._CachedInArrayLiteral != this._InArrayLiteral || this._Lexer._CachedInAssignBuiltin != this._InAssignBuiltin)
            {
                this._Lexer._TokenCache = null;
            }
        }
        if (this._Lexer.Pos != this.Pos)
        {
            this._Lexer.Pos = this.Pos;
        }
        this._Lexer._EofToken = this._EofToken;
        this._Lexer._ParserState = this._ParserState;
        this._Lexer._LastReadToken = this._TokenHistory[0];
        this._Lexer._WordContext = this._WordContext;
        this._Lexer._AtCommandStart = this._AtCommandStart;
        this._Lexer._InArrayLiteral = this._InArrayLiteral;
        this._Lexer._InAssignBuiltin = this._InAssignBuiltin;
    }

    public void _SyncParser()
    {
        this.Pos = this._Lexer.Pos;
    }

    public Token _LexPeekToken()
    {
        if (this._Lexer._TokenCache != null && this._Lexer._TokenCache.Pos == this.Pos && this._Lexer._CachedWordContext == this._WordContext && this._Lexer._CachedAtCommandStart == this._AtCommandStart && this._Lexer._CachedInArrayLiteral == this._InArrayLiteral && this._Lexer._CachedInAssignBuiltin == this._InAssignBuiltin)
        {
            return this._Lexer._TokenCache;
        }
        int savedPos = this.Pos;
        this._SyncLexer();
        Token result = this._Lexer.PeekToken();
        this._Lexer._CachedWordContext = this._WordContext;
        this._Lexer._CachedAtCommandStart = this._AtCommandStart;
        this._Lexer._CachedInArrayLiteral = this._InArrayLiteral;
        this._Lexer._CachedInAssignBuiltin = this._InAssignBuiltin;
        this._Lexer._PostReadPos = this._Lexer.Pos;
        this.Pos = savedPos;
        return result;
    }

    public Token _LexNextToken()
    {
        Token tok = null;
        if (this._Lexer._TokenCache != null && this._Lexer._TokenCache.Pos == this.Pos && this._Lexer._CachedWordContext == this._WordContext && this._Lexer._CachedAtCommandStart == this._AtCommandStart && this._Lexer._CachedInArrayLiteral == this._InArrayLiteral && this._Lexer._CachedInAssignBuiltin == this._InAssignBuiltin)
        {
            tok = this._Lexer.NextToken();
            this.Pos = this._Lexer._PostReadPos;
            this._Lexer.Pos = this._Lexer._PostReadPos;
        }
        else
        {
            this._SyncLexer();
            tok = this._Lexer.NextToken();
            this._Lexer._CachedWordContext = this._WordContext;
            this._Lexer._CachedAtCommandStart = this._AtCommandStart;
            this._Lexer._CachedInArrayLiteral = this._InArrayLiteral;
            this._Lexer._CachedInAssignBuiltin = this._InAssignBuiltin;
            this._SyncParser();
        }
        this._RecordToken(tok);
        return tok;
    }

    public void _LexSkipBlanks()
    {
        this._SyncLexer();
        this._Lexer.SkipBlanks();
        this._SyncParser();
    }

    public bool _LexSkipComment()
    {
        this._SyncLexer();
        bool result = this._Lexer._SkipComment();
        this._SyncParser();
        return result;
    }

    public bool _LexIsCommandTerminator()
    {
        Token tok = this._LexPeekToken();
        int t = tok.Type;
        return t == Constants.TOKENTYPE_EOF || t == Constants.TOKENTYPE_NEWLINE || t == Constants.TOKENTYPE_PIPE || t == Constants.TOKENTYPE_SEMI || t == Constants.TOKENTYPE_LPAREN || t == Constants.TOKENTYPE_RPAREN || t == Constants.TOKENTYPE_AMP;
    }

    public (int, string) _LexPeekOperator()
    {
        Token tok = this._LexPeekToken();
        int t = tok.Type;
        if (t >= Constants.TOKENTYPE_SEMI && t <= Constants.TOKENTYPE_GREATER || t >= Constants.TOKENTYPE_AND_AND && t <= Constants.TOKENTYPE_PIPE_AMP)
        {
            return (t, tok.Value);
        }
        return (0, "");
    }

    public string _LexPeekReservedWord()
    {
        Token tok = this._LexPeekToken();
        if (tok.Type != Constants.TOKENTYPE_WORD)
        {
            return "";
        }
        string word = tok.Value;
        if (word.EndsWith("\\\n"))
        {
            word = word.Substring(0, word.Length - 2);
        }
        if (Constants.RESERVED_WORDS.Contains(word) || word == "{" || word == "}" || word == "[[" || word == "]]" || word == "!" || word == "time")
        {
            return word;
        }
        return "";
    }

    public bool _LexIsAtReservedWord(string word)
    {
        string reserved = this._LexPeekReservedWord();
        return reserved == word;
    }

    public bool _LexConsumeWord(string expected)
    {
        Token tok = this._LexPeekToken();
        if (tok.Type != Constants.TOKENTYPE_WORD)
        {
            return false;
        }
        string word = tok.Value;
        if (word.EndsWith("\\\n"))
        {
            word = word.Substring(0, word.Length - 2);
        }
        if (word == expected)
        {
            this._LexNextToken();
            return true;
        }
        return false;
    }

    public string _LexPeekCaseTerminator()
    {
        Token tok = this._LexPeekToken();
        int t = tok.Type;
        if (t == Constants.TOKENTYPE_SEMI_SEMI)
        {
            return ";;";
        }
        if (t == Constants.TOKENTYPE_SEMI_AMP)
        {
            return ";&";
        }
        if (t == Constants.TOKENTYPE_SEMI_SEMI_AMP)
        {
            return ";;&";
        }
        return "";
    }

    public bool AtEnd()
    {
        return this.Pos >= this.Length;
    }

    public string Peek()
    {
        if (this.AtEnd())
        {
            return "";
        }
        return (this.Source[this.Pos]).ToString();
    }

    public string Advance()
    {
        if (this.AtEnd())
        {
            return "";
        }
        string ch = (this.Source[this.Pos]).ToString();
        this.Pos += 1;
        return ch;
    }

    public string PeekAt(int offset)
    {
        int pos = this.Pos + offset;
        if (pos < 0 || pos >= this.Length)
        {
            return "";
        }
        return (this.Source[pos]).ToString();
    }

    public string Lookahead(int n)
    {
        return ParableFunctions._Substring(this.Source, this.Pos, this.Pos + n);
    }

    public bool _IsBangFollowedByProcsub()
    {
        if (this.Pos + 2 >= this.Length)
        {
            return false;
        }
        string nextChar = (this.Source[this.Pos + 1]).ToString();
        if (nextChar != ">" && nextChar != "<")
        {
            return false;
        }
        return (this.Source[this.Pos + 2]).ToString() == "(";
    }

    public void SkipWhitespace()
    {
        while (!(this.AtEnd()))
        {
            this._LexSkipBlanks();
            if (this.AtEnd())
            {
                break;
            }
            string ch = this.Peek();
            if (ch == "#")
            {
                this._LexSkipComment();
            }
            else
            {
                if (ch == "\\" && this.PeekAt(1) == "\n")
                {
                    this.Advance();
                    this.Advance();
                }
                else
                {
                    break;
                }
            }
        }
    }

    public void SkipWhitespaceAndNewlines()
    {
        while (!(this.AtEnd()))
        {
            string ch = this.Peek();
            if (ParableFunctions._IsWhitespace(ch))
            {
                this.Advance();
                if (ch == "\n")
                {
                    this._GatherHeredocBodies();
                    if (this._CmdsubHeredocEnd != -1 && this._CmdsubHeredocEnd > this.Pos)
                    {
                        this.Pos = this._CmdsubHeredocEnd;
                        this._CmdsubHeredocEnd = -1;
                    }
                }
            }
            else
            {
                if (ch == "#")
                {
                    while (!(this.AtEnd()) && this.Peek() != "\n")
                    {
                        this.Advance();
                    }
                }
                else
                {
                    if (ch == "\\" && this.PeekAt(1) == "\n")
                    {
                        this.Advance();
                        this.Advance();
                    }
                    else
                    {
                        break;
                    }
                }
            }
        }
    }

    public bool _AtListTerminatingBracket()
    {
        if (this.AtEnd())
        {
            return false;
        }
        string ch = this.Peek();
        if (this._EofToken != "" && ch == this._EofToken)
        {
            return true;
        }
        if (ch == ")")
        {
            return true;
        }
        if (ch == "}")
        {
            int nextPos = this.Pos + 1;
            if (nextPos >= this.Length)
            {
                return true;
            }
            return ParableFunctions._IsWordEndContext((this.Source[nextPos]).ToString());
        }
        return false;
    }

    public bool _AtEofToken()
    {
        if (this._EofToken == "")
        {
            return false;
        }
        Token tok = this._LexPeekToken();
        if (this._EofToken == ")")
        {
            return tok.Type == Constants.TOKENTYPE_RPAREN;
        }
        if (this._EofToken == "}")
        {
            return tok.Type == Constants.TOKENTYPE_WORD && tok.Value == "}";
        }
        return false;
    }

    public List<INode> _CollectRedirects()
    {
        List<INode> redirects = new List<INode>();
        while (true)
        {
            this.SkipWhitespace();
            INode redirect = this.ParseRedirect();
            if (redirect == null)
            {
                break;
            }
            redirects.Add(redirect);
        }
        return ((redirects.Count > 0) ? redirects : new List<INode>());
    }

    public INode _ParseLoopBody(string context)
    {
        if (this.Peek() == "{")
        {
            BraceGroup brace = this.ParseBraceGroup();
            if (brace == null)
            {
                throw new ParseError(string.Format("Expected brace group body in {0}", context), this._LexPeekToken().Pos, 0);
            }
            return brace.Body;
        }
        if (this._LexConsumeWord("do"))
        {
            INode body = this.ParseListUntil(new HashSet<string> { "done" });
            if (body == null)
            {
                throw new ParseError("Expected commands after 'do'", this._LexPeekToken().Pos, 0);
            }
            this.SkipWhitespaceAndNewlines();
            if (!(this._LexConsumeWord("done")))
            {
                throw new ParseError(string.Format("Expected 'done' to close {0}", context), this._LexPeekToken().Pos, 0);
            }
            return body;
        }
        throw new ParseError(string.Format("Expected 'do' or '{{' in {0}", context), this._LexPeekToken().Pos, 0);
    }

    public string PeekWord()
    {
        int savedPos = this.Pos;
        this.SkipWhitespace();
        if (this.AtEnd() || ParableFunctions._IsMetachar(this.Peek()))
        {
            this.Pos = savedPos;
            return "";
        }
        List<string> chars = new List<string>();
        while (!(this.AtEnd()) && !(ParableFunctions._IsMetachar(this.Peek())))
        {
            string ch = this.Peek();
            if (ParableFunctions._IsQuote(ch))
            {
                break;
            }
            if (ch == "\\" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "\n")
            {
                break;
            }
            if (ch == "\\" && this.Pos + 1 < this.Length)
            {
                chars.Add(this.Advance());
                chars.Add(this.Advance());
                continue;
            }
            chars.Add(this.Advance());
        }
        string word = "";
        if ((chars.Count > 0))
        {
            word = string.Join("", chars);
        }
        else
        {
            word = "";
        }
        this.Pos = savedPos;
        return word;
    }

    public bool ConsumeWord(string expected)
    {
        int savedPos = this.Pos;
        this.SkipWhitespace();
        string word = this.PeekWord();
        string keywordWord = word;
        bool hasLeadingBrace = false;
        if (word != "" && this._InProcessSub && word.Length > 1 && (word[0]).ToString() == "}")
        {
            keywordWord = word.Substring(1);
            hasLeadingBrace = true;
        }
        if (keywordWord != expected)
        {
            this.Pos = savedPos;
            return false;
        }
        this.SkipWhitespace();
        if (hasLeadingBrace)
        {
            this.Advance();
        }
        foreach (var _ in expected)
        {
            this.Advance();
        }
        while (this.Peek() == "\\" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "\n")
        {
            this.Advance();
            this.Advance();
        }
        return true;
    }

    public bool _IsWordTerminator(int ctx, string ch, int bracketDepth, int parenDepth)
    {
        this._SyncLexer();
        return this._Lexer._IsWordTerminator(ctx, ch, bracketDepth, parenDepth);
    }

    public void _ScanDoubleQuote(List<string> chars, List<INode> parts, int start, bool handleLineContinuation)
    {
        chars.Add("\"");
        while (!(this.AtEnd()) && this.Peek() != "\"")
        {
            string c = this.Peek();
            if (c == "\\" && this.Pos + 1 < this.Length)
            {
                string nextC = (this.Source[this.Pos + 1]).ToString();
                if (handleLineContinuation && nextC == "\n")
                {
                    this.Advance();
                    this.Advance();
                }
                else
                {
                    chars.Add(this.Advance());
                    chars.Add(this.Advance());
                }
            }
            else
            {
                if (c == "$")
                {
                    if (!(this._ParseDollarExpansion(chars, parts, true)))
                    {
                        chars.Add(this.Advance());
                    }
                }
                else
                {
                    chars.Add(this.Advance());
                }
            }
        }
        if (this.AtEnd())
        {
            throw new ParseError("Unterminated double quote", start, 0);
        }
        chars.Add(this.Advance());
    }

    public bool _ParseDollarExpansion(List<string> chars, List<INode> parts, bool inDquote)
    {
        INode result0 = null;
        string result1 = "";
        if (this.Pos + 2 < this.Length && (this.Source[this.Pos + 1]).ToString() == "(" && (this.Source[this.Pos + 2]).ToString() == "(")
        {
            (result0, result1) = this._ParseArithmeticExpansion();
            if (result0 != null)
            {
                parts.Add(result0);
                chars.Add(result1);
                return true;
            }
            (result0, result1) = this._ParseCommandSubstitution();
            if (result0 != null)
            {
                parts.Add(result0);
                chars.Add(result1);
                return true;
            }
            return false;
        }
        if (this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "[")
        {
            (result0, result1) = this._ParseDeprecatedArithmetic();
            if (result0 != null)
            {
                parts.Add(result0);
                chars.Add(result1);
                return true;
            }
            return false;
        }
        if (this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "(")
        {
            (result0, result1) = this._ParseCommandSubstitution();
            if (result0 != null)
            {
                parts.Add(result0);
                chars.Add(result1);
                return true;
            }
            return false;
        }
        (result0, result1) = this._ParseParamExpansion(inDquote);
        if (result0 != null)
        {
            parts.Add(result0);
            chars.Add(result1);
            return true;
        }
        return false;
    }

    public Word _ParseWordInternal(int ctx, bool atCommandStart, bool inArrayLiteral)
    {
        this._WordContext = ctx;
        return this.ParseWord(atCommandStart, inArrayLiteral, false);
    }

    public Word ParseWord(bool atCommandStart, bool inArrayLiteral, bool inAssignBuiltin)
    {
        this.SkipWhitespace();
        if (this.AtEnd())
        {
            return null;
        }
        this._AtCommandStart = atCommandStart;
        this._InArrayLiteral = inArrayLiteral;
        this._InAssignBuiltin = inAssignBuiltin;
        Token tok = this._LexPeekToken();
        if (tok.Type != Constants.TOKENTYPE_WORD)
        {
            this._AtCommandStart = false;
            this._InArrayLiteral = false;
            this._InAssignBuiltin = false;
            return null;
        }
        this._LexNextToken();
        this._AtCommandStart = false;
        this._InArrayLiteral = false;
        this._InAssignBuiltin = false;
        return tok.Word;
    }

    public (INode, string) _ParseCommandSubstitution()
    {
        if (this.AtEnd() || this.Peek() != "$")
        {
            return (null, "");
        }
        int start = this.Pos;
        this.Advance();
        if (this.AtEnd() || this.Peek() != "(")
        {
            this.Pos = start;
            return (null, "");
        }
        this.Advance();
        SavedParserState saved = this._SaveParserState();
        this._SetState((Constants.PARSERSTATEFLAGS_PST_CMDSUBST | Constants.PARSERSTATEFLAGS_PST_EOFTOKEN));
        this._EofToken = ")";
        INode cmd = this.ParseList(true);
        if (cmd == null)
        {
            cmd = new Empty("empty");
        }
        this.SkipWhitespaceAndNewlines();
        if (this.AtEnd() || this.Peek() != ")")
        {
            this._RestoreParserState(saved);
            this.Pos = start;
            return (null, "");
        }
        this.Advance();
        int textEnd = this.Pos;
        string text = ParableFunctions._Substring(this.Source, start, textEnd);
        this._RestoreParserState(saved);
        return (new CommandSubstitution(cmd, false, "cmdsub"), text);
    }

    public (INode, string) _ParseFunsub(int start)
    {
        this._SyncParser();
        if (!(this.AtEnd()) && this.Peek() == "|")
        {
            this.Advance();
        }
        SavedParserState saved = this._SaveParserState();
        this._SetState((Constants.PARSERSTATEFLAGS_PST_CMDSUBST | Constants.PARSERSTATEFLAGS_PST_EOFTOKEN));
        this._EofToken = "}";
        INode cmd = this.ParseList(true);
        if (cmd == null)
        {
            cmd = new Empty("empty");
        }
        this.SkipWhitespaceAndNewlines();
        if (this.AtEnd() || this.Peek() != "}")
        {
            this._RestoreParserState(saved);
            throw new MatchedPairError("unexpected EOF looking for `}'", start, 0);
        }
        this.Advance();
        string text = ParableFunctions._Substring(this.Source, start, this.Pos);
        this._RestoreParserState(saved);
        this._SyncLexer();
        return (new CommandSubstitution(cmd, true, "cmdsub"), text);
    }

    public bool _IsAssignmentWord(INode word)
    {
        return ParableFunctions._Assignment(((Word)word).Value, 0) != -1;
    }

    public (INode, string) _ParseBacktickSubstitution()
    {
        if (this.AtEnd() || this.Peek() != "`")
        {
            return (null, "");
        }
        int start = this.Pos;
        this.Advance();
        List<string> contentChars = new List<string>();
        List<string> textChars = new List<string> { "`" };
        List<(string, bool)> pendingHeredocs = new List<(string, bool)>();
        bool inHeredocBody = false;
        string currentHeredocDelim = "";
        bool currentHeredocStrip = false;
        string ch = "";
        while (!(this.AtEnd()) && (inHeredocBody || this.Peek() != "`"))
        {
            if (inHeredocBody)
            {
                int lineStart = this.Pos;
                int lineEnd = lineStart;
                while (lineEnd < this.Length && (this.Source[lineEnd]).ToString() != "\n")
                {
                    lineEnd += 1;
                }
                string line = ParableFunctions._Substring(this.Source, lineStart, lineEnd);
                string checkLine = (currentHeredocStrip ? line.TrimStart("\t".ToCharArray()) : line);
                if (checkLine == currentHeredocDelim)
                {
                    foreach (var _c3 in line)
                    {
                        ch = _c3.ToString();
                        contentChars.Add(ch);
                        textChars.Add(ch);
                    }
                    this.Pos = lineEnd;
                    if (this.Pos < this.Length && (this.Source[this.Pos]).ToString() == "\n")
                    {
                        contentChars.Add("\n");
                        textChars.Add("\n");
                        this.Advance();
                    }
                    inHeredocBody = false;
                    if (pendingHeredocs.Count > 0)
                    {
                        (string, bool) _entry2 = pendingHeredocs[0];
                        pendingHeredocs.RemoveAt(0);
                        currentHeredocDelim = _entry2.Item1;
                        currentHeredocStrip = _entry2.Item2;
                        inHeredocBody = true;
                    }
                }
                else
                {
                    if (checkLine.StartsWith(currentHeredocDelim) && checkLine.Length > currentHeredocDelim.Length)
                    {
                        int tabsStripped = line.Length - checkLine.Length;
                        int endPos = tabsStripped + currentHeredocDelim.Length;
                        for (int i = 0; i < endPos; i += 1)
                        {
                            contentChars.Add((line[i]).ToString());
                            textChars.Add((line[i]).ToString());
                        }
                        this.Pos = lineStart + endPos;
                        inHeredocBody = false;
                        if (pendingHeredocs.Count > 0)
                        {
                            (string, bool) _entry3 = pendingHeredocs[0];
                            pendingHeredocs.RemoveAt(0);
                            currentHeredocDelim = _entry3.Item1;
                            currentHeredocStrip = _entry3.Item2;
                            inHeredocBody = true;
                        }
                    }
                    else
                    {
                        foreach (var _c4 in line)
                        {
                            ch = _c4.ToString();
                            contentChars.Add(ch);
                            textChars.Add(ch);
                        }
                        this.Pos = lineEnd;
                        if (this.Pos < this.Length && (this.Source[this.Pos]).ToString() == "\n")
                        {
                            contentChars.Add("\n");
                            textChars.Add("\n");
                            this.Advance();
                        }
                    }
                }
                continue;
            }
            string c = this.Peek();
            if (c == "\\" && this.Pos + 1 < this.Length)
            {
                string nextC = (this.Source[this.Pos + 1]).ToString();
                if (nextC == "\n")
                {
                    this.Advance();
                    this.Advance();
                }
                else
                {
                    if (ParableFunctions._IsEscapeCharInBacktick(nextC))
                    {
                        this.Advance();
                        string escaped = this.Advance();
                        contentChars.Add(escaped);
                        textChars.Add("\\");
                        textChars.Add(escaped);
                    }
                    else
                    {
                        ch = this.Advance();
                        contentChars.Add(ch);
                        textChars.Add(ch);
                    }
                }
                continue;
            }
            if (c == "<" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "<")
            {
                string quote = "";
                if (this.Pos + 2 < this.Length && (this.Source[this.Pos + 2]).ToString() == "<")
                {
                    contentChars.Add(this.Advance());
                    textChars.Add("<");
                    contentChars.Add(this.Advance());
                    textChars.Add("<");
                    contentChars.Add(this.Advance());
                    textChars.Add("<");
                    while (!(this.AtEnd()) && ParableFunctions._IsWhitespaceNoNewline(this.Peek()))
                    {
                        ch = this.Advance();
                        contentChars.Add(ch);
                        textChars.Add(ch);
                    }
                    while (!(this.AtEnd()) && !(ParableFunctions._IsWhitespace(this.Peek())) && !"()".Contains(this.Peek()))
                    {
                        if (this.Peek() == "\\" && this.Pos + 1 < this.Length)
                        {
                            ch = this.Advance();
                            contentChars.Add(ch);
                            textChars.Add(ch);
                            ch = this.Advance();
                            contentChars.Add(ch);
                            textChars.Add(ch);
                        }
                        else
                        {
                            if ("\"'".Contains(this.Peek()))
                            {
                                quote = this.Peek();
                                ch = this.Advance();
                                contentChars.Add(ch);
                                textChars.Add(ch);
                                while (!(this.AtEnd()) && this.Peek() != quote)
                                {
                                    if (quote == "\"" && this.Peek() == "\\")
                                    {
                                        ch = this.Advance();
                                        contentChars.Add(ch);
                                        textChars.Add(ch);
                                    }
                                    ch = this.Advance();
                                    contentChars.Add(ch);
                                    textChars.Add(ch);
                                }
                                if (!(this.AtEnd()))
                                {
                                    ch = this.Advance();
                                    contentChars.Add(ch);
                                    textChars.Add(ch);
                                }
                            }
                            else
                            {
                                ch = this.Advance();
                                contentChars.Add(ch);
                                textChars.Add(ch);
                            }
                        }
                    }
                    continue;
                }
                contentChars.Add(this.Advance());
                textChars.Add("<");
                contentChars.Add(this.Advance());
                textChars.Add("<");
                bool stripTabs = false;
                if (!(this.AtEnd()) && this.Peek() == "-")
                {
                    stripTabs = true;
                    contentChars.Add(this.Advance());
                    textChars.Add("-");
                }
                while (!(this.AtEnd()) && ParableFunctions._IsWhitespaceNoNewline(this.Peek()))
                {
                    ch = this.Advance();
                    contentChars.Add(ch);
                    textChars.Add(ch);
                }
                List<string> delimiterChars = new List<string>();
                if (!(this.AtEnd()))
                {
                    ch = this.Peek();
                    string dch = "";
                    string closing = "";
                    if (ParableFunctions._IsQuote(ch))
                    {
                        quote = this.Advance();
                        contentChars.Add(quote);
                        textChars.Add(quote);
                        while (!(this.AtEnd()) && this.Peek() != quote)
                        {
                            dch = this.Advance();
                            contentChars.Add(dch);
                            textChars.Add(dch);
                            delimiterChars.Add(dch);
                        }
                        if (!(this.AtEnd()))
                        {
                            closing = this.Advance();
                            contentChars.Add(closing);
                            textChars.Add(closing);
                        }
                    }
                    else
                    {
                        string esc = "";
                        if (ch == "\\")
                        {
                            esc = this.Advance();
                            contentChars.Add(esc);
                            textChars.Add(esc);
                            if (!(this.AtEnd()))
                            {
                                dch = this.Advance();
                                contentChars.Add(dch);
                                textChars.Add(dch);
                                delimiterChars.Add(dch);
                            }
                            while (!(this.AtEnd()) && !(ParableFunctions._IsMetachar(this.Peek())))
                            {
                                dch = this.Advance();
                                contentChars.Add(dch);
                                textChars.Add(dch);
                                delimiterChars.Add(dch);
                            }
                        }
                        else
                        {
                            while (!(this.AtEnd()) && !(ParableFunctions._IsMetachar(this.Peek())) && this.Peek() != "`")
                            {
                                ch = this.Peek();
                                if (ParableFunctions._IsQuote(ch))
                                {
                                    quote = this.Advance();
                                    contentChars.Add(quote);
                                    textChars.Add(quote);
                                    while (!(this.AtEnd()) && this.Peek() != quote)
                                    {
                                        dch = this.Advance();
                                        contentChars.Add(dch);
                                        textChars.Add(dch);
                                        delimiterChars.Add(dch);
                                    }
                                    if (!(this.AtEnd()))
                                    {
                                        closing = this.Advance();
                                        contentChars.Add(closing);
                                        textChars.Add(closing);
                                    }
                                }
                                else
                                {
                                    if (ch == "\\")
                                    {
                                        esc = this.Advance();
                                        contentChars.Add(esc);
                                        textChars.Add(esc);
                                        if (!(this.AtEnd()))
                                        {
                                            dch = this.Advance();
                                            contentChars.Add(dch);
                                            textChars.Add(dch);
                                            delimiterChars.Add(dch);
                                        }
                                    }
                                    else
                                    {
                                        dch = this.Advance();
                                        contentChars.Add(dch);
                                        textChars.Add(dch);
                                        delimiterChars.Add(dch);
                                    }
                                }
                            }
                        }
                    }
                }
                string delimiter = string.Join("", delimiterChars);
                if ((!string.IsNullOrEmpty(delimiter)))
                {
                    pendingHeredocs.Add((delimiter, stripTabs));
                }
                continue;
            }
            if (c == "\n")
            {
                ch = this.Advance();
                contentChars.Add(ch);
                textChars.Add(ch);
                if (pendingHeredocs.Count > 0)
                {
                    (string, bool) _entry4 = pendingHeredocs[0];
                    pendingHeredocs.RemoveAt(0);
                    currentHeredocDelim = _entry4.Item1;
                    currentHeredocStrip = _entry4.Item2;
                    inHeredocBody = true;
                }
                continue;
            }
            ch = this.Advance();
            contentChars.Add(ch);
            textChars.Add(ch);
        }
        if (this.AtEnd())
        {
            throw new ParseError("Unterminated backtick", start, 0);
        }
        this.Advance();
        textChars.Add("`");
        string text = string.Join("", textChars);
        string content = string.Join("", contentChars);
        if (pendingHeredocs.Count > 0)
        {
            (int heredocStart, int heredocEnd) = ParableFunctions._FindHeredocContentEnd(this.Source, this.Pos, pendingHeredocs);
            if (heredocEnd > heredocStart)
            {
                content = content + ParableFunctions._Substring(this.Source, heredocStart, heredocEnd);
                if (this._CmdsubHeredocEnd == -1)
                {
                    this._CmdsubHeredocEnd = heredocEnd;
                }
                else
                {
                    this._CmdsubHeredocEnd = (this._CmdsubHeredocEnd > heredocEnd ? this._CmdsubHeredocEnd : heredocEnd);
                }
            }
        }
        Parser subParser = ParableFunctions.NewParser(content, false, this._Extglob);
        INode cmd = subParser.ParseList(true);
        if (cmd == null)
        {
            cmd = new Empty("empty");
        }
        return (new CommandSubstitution(cmd, false, "cmdsub"), text);
    }

    public (INode, string) _ParseProcessSubstitution()
    {
        if (this.AtEnd() || !(ParableFunctions._IsRedirectChar(this.Peek())))
        {
            return (null, "");
        }
        int start = this.Pos;
        string direction = this.Advance();
        if (this.AtEnd() || this.Peek() != "(")
        {
            this.Pos = start;
            return (null, "");
        }
        this.Advance();
        SavedParserState saved = this._SaveParserState();
        bool oldInProcessSub = this._InProcessSub;
        this._InProcessSub = true;
        this._SetState(Constants.PARSERSTATEFLAGS_PST_EOFTOKEN);
        this._EofToken = ")";
        try
        {
            INode cmd = this.ParseList(true);
            if (cmd == null)
            {
                cmd = new Empty("empty");
            }
            this.SkipWhitespaceAndNewlines();
            if (this.AtEnd() || this.Peek() != ")")
            {
                throw new ParseError("Invalid process substitution", start, 0);
            }
            this.Advance();
            int textEnd = this.Pos;
            string text = ParableFunctions._Substring(this.Source, start, textEnd);
            text = ParableFunctions._StripLineContinuationsCommentAware(text);
            this._RestoreParserState(saved);
            this._InProcessSub = oldInProcessSub;
            return (new ProcessSubstitution(direction, cmd, "procsub"), text);
        } catch (ParseError)
        {
            this._RestoreParserState(saved);
            this._InProcessSub = oldInProcessSub;
            string contentStartChar = (start + 2 < this.Length ? (this.Source[start + 2]).ToString() : "");
            if (" \t\n".Contains(contentStartChar))
            {
                throw;
            }
            this.Pos = start + 2;
            this._Lexer.Pos = this.Pos;
            this._Lexer._ParseMatchedPair("(", ")", 0, false);
            this.Pos = this._Lexer.Pos;
            string text = ParableFunctions._Substring(this.Source, start, this.Pos);
            text = ParableFunctions._StripLineContinuationsCommentAware(text);
            return (null, text);
        }
    }

    public (INode, string) _ParseArrayLiteral()
    {
        if (this.AtEnd() || this.Peek() != "(")
        {
            return (null, "");
        }
        int start = this.Pos;
        this.Advance();
        this._SetState(Constants.PARSERSTATEFLAGS_PST_COMPASSIGN);
        List<Word> elements = new List<Word>();
        while (true)
        {
            this.SkipWhitespaceAndNewlines();
            if (this.AtEnd())
            {
                this._ClearState(Constants.PARSERSTATEFLAGS_PST_COMPASSIGN);
                throw new ParseError("Unterminated array literal", start, 0);
            }
            if (this.Peek() == ")")
            {
                break;
            }
            Word word = this.ParseWord(false, true, false);
            if (word == null)
            {
                if (this.Peek() == ")")
                {
                    break;
                }
                this._ClearState(Constants.PARSERSTATEFLAGS_PST_COMPASSIGN);
                throw new ParseError("Expected word in array literal", this.Pos, 0);
            }
            elements.Add(word);
        }
        if (this.AtEnd() || this.Peek() != ")")
        {
            this._ClearState(Constants.PARSERSTATEFLAGS_PST_COMPASSIGN);
            throw new ParseError("Expected ) to close array literal", this.Pos, 0);
        }
        this.Advance();
        string text = ParableFunctions._Substring(this.Source, start, this.Pos);
        this._ClearState(Constants.PARSERSTATEFLAGS_PST_COMPASSIGN);
        return (new Array(elements, "array"), text);
    }

    public (INode, string) _ParseArithmeticExpansion()
    {
        if (this.AtEnd() || this.Peek() != "$")
        {
            return (null, "");
        }
        int start = this.Pos;
        if (this.Pos + 2 >= this.Length || (this.Source[this.Pos + 1]).ToString() != "(" || (this.Source[this.Pos + 2]).ToString() != "(")
        {
            return (null, "");
        }
        this.Advance();
        this.Advance();
        this.Advance();
        int contentStart = this.Pos;
        int depth = 2;
        int firstClosePos = -1;
        while (!(this.AtEnd()) && depth > 0)
        {
            string c = this.Peek();
            if (c == "'")
            {
                this.Advance();
                while (!(this.AtEnd()) && this.Peek() != "'")
                {
                    this.Advance();
                }
                if (!(this.AtEnd()))
                {
                    this.Advance();
                }
            }
            else
            {
                if (c == "\"")
                {
                    this.Advance();
                    while (!(this.AtEnd()))
                    {
                        if (this.Peek() == "\\" && this.Pos + 1 < this.Length)
                        {
                            this.Advance();
                            this.Advance();
                        }
                        else
                        {
                            if (this.Peek() == "\"")
                            {
                                this.Advance();
                                break;
                            }
                            else
                            {
                                this.Advance();
                            }
                        }
                    }
                }
                else
                {
                    if (c == "\\" && this.Pos + 1 < this.Length)
                    {
                        this.Advance();
                        this.Advance();
                    }
                    else
                    {
                        if (c == "(")
                        {
                            depth += 1;
                            this.Advance();
                        }
                        else
                        {
                            if (c == ")")
                            {
                                if (depth == 2)
                                {
                                    firstClosePos = this.Pos;
                                }
                                depth -= 1;
                                if (depth == 0)
                                {
                                    break;
                                }
                                this.Advance();
                            }
                            else
                            {
                                if (depth == 1)
                                {
                                    firstClosePos = -1;
                                }
                                this.Advance();
                            }
                        }
                    }
                }
            }
        }
        if (depth != 0)
        {
            if (this.AtEnd())
            {
                throw new MatchedPairError("unexpected EOF looking for `))'", start, 0);
            }
            this.Pos = start;
            return (null, "");
        }
        string content = "";
        if (firstClosePos != -1)
        {
            content = ParableFunctions._Substring(this.Source, contentStart, firstClosePos);
        }
        else
        {
            content = ParableFunctions._Substring(this.Source, contentStart, this.Pos);
        }
        this.Advance();
        string text = ParableFunctions._Substring(this.Source, start, this.Pos);
        INode expr = null;
        try
        {
            expr = this._ParseArithExpr(content);
        } catch (ParseError)
        {
            this.Pos = start;
            return (null, "");
        }
        return (new ArithmeticExpansion(expr, "arith"), text);
    }

    public INode _ParseArithExpr(string content)
    {
        string savedArithSrc = this._ArithSrc;
        int savedArithPos = this._ArithPos;
        int savedArithLen = this._ArithLen;
        int savedParserState = this._ParserState;
        this._SetState(Constants.PARSERSTATEFLAGS_PST_ARITH);
        this._ArithSrc = content;
        this._ArithPos = 0;
        this._ArithLen = content.Length;
        this._ArithSkipWs();
        INode result = null;
        if (this._ArithAtEnd())
        {
            result = null;
        }
        else
        {
            result = this._ArithParseComma();
        }
        this._ParserState = savedParserState;
        if (savedArithSrc != "")
        {
            this._ArithSrc = savedArithSrc;
            this._ArithPos = savedArithPos;
            this._ArithLen = savedArithLen;
        }
        return result;
    }

    public bool _ArithAtEnd()
    {
        return this._ArithPos >= this._ArithLen;
    }

    public string _ArithPeek(int offset)
    {
        int pos = this._ArithPos + offset;
        if (pos >= this._ArithLen)
        {
            return "";
        }
        return (this._ArithSrc[pos]).ToString();
    }

    public string _ArithAdvance()
    {
        if (this._ArithAtEnd())
        {
            return "";
        }
        string c = (this._ArithSrc[this._ArithPos]).ToString();
        this._ArithPos += 1;
        return c;
    }

    public void _ArithSkipWs()
    {
        while (!(this._ArithAtEnd()))
        {
            string c = (this._ArithSrc[this._ArithPos]).ToString();
            if (ParableFunctions._IsWhitespace(c))
            {
                this._ArithPos += 1;
            }
            else
            {
                if (c == "\\" && this._ArithPos + 1 < this._ArithLen && (this._ArithSrc[this._ArithPos + 1]).ToString() == "\n")
                {
                    this._ArithPos += 2;
                }
                else
                {
                    break;
                }
            }
        }
    }

    public bool _ArithMatch(string s)
    {
        return ParableFunctions._StartsWithAt(this._ArithSrc, this._ArithPos, s);
    }

    public bool _ArithConsume(string s)
    {
        if (this._ArithMatch(s))
        {
            this._ArithPos += s.Length;
            return true;
        }
        return false;
    }

    public INode _ArithParseComma()
    {
        INode left = this._ArithParseAssign();
        while (true)
        {
            this._ArithSkipWs();
            if (this._ArithConsume(","))
            {
                this._ArithSkipWs();
                INode right = this._ArithParseAssign();
                left = new ArithComma(left, right, "comma");
            }
            else
            {
                break;
            }
        }
        return left;
    }

    public INode _ArithParseAssign()
    {
        INode left = this._ArithParseTernary();
        this._ArithSkipWs();
        List<string> assignOps = new List<string> { "<<=", ">>=", "+=", "-=", "*=", "/=", "%=", "&=", "^=", "|=", "=" };
        foreach (string op in assignOps)
        {
            if (this._ArithMatch(op))
            {
                if (op == "=" && this._ArithPeek(1) == "=")
                {
                    break;
                }
                this._ArithConsume(op);
                this._ArithSkipWs();
                INode right = this._ArithParseAssign();
                return new ArithAssign(op, left, right, "assign");
            }
        }
        return left;
    }

    public INode _ArithParseTernary()
    {
        INode cond = this._ArithParseLogicalOr();
        this._ArithSkipWs();
        if (this._ArithConsume("?"))
        {
            this._ArithSkipWs();
            INode ifTrue = null;
            if (this._ArithMatch(":"))
            {
                ifTrue = null;
            }
            else
            {
                ifTrue = this._ArithParseAssign();
            }
            this._ArithSkipWs();
            INode ifFalse = null;
            if (this._ArithConsume(":"))
            {
                this._ArithSkipWs();
                if (this._ArithAtEnd() || this._ArithPeek(0) == ")")
                {
                    ifFalse = null;
                }
                else
                {
                    ifFalse = this._ArithParseTernary();
                }
            }
            else
            {
                ifFalse = null;
            }
            return new ArithTernary(cond, ifTrue, ifFalse, "ternary");
        }
        return cond;
    }

    public INode _ArithParseLeftAssoc(List<string> ops, Func<INode> parsefn)
    {
        INode left = parsefn();
        while (true)
        {
            this._ArithSkipWs();
            bool matched = false;
            foreach (string op in ops)
            {
                if (this._ArithMatch(op))
                {
                    this._ArithConsume(op);
                    this._ArithSkipWs();
                    left = new ArithBinaryOp(op, left, parsefn(), "binary-op");
                    matched = true;
                    break;
                }
            }
            if (!(matched))
            {
                break;
            }
        }
        return left;
    }

    public INode _ArithParseLogicalOr()
    {
        return this._ArithParseLeftAssoc(new List<string> { "||" }, this._ArithParseLogicalAnd);
    }

    public INode _ArithParseLogicalAnd()
    {
        return this._ArithParseLeftAssoc(new List<string> { "&&" }, this._ArithParseBitwiseOr);
    }

    public INode _ArithParseBitwiseOr()
    {
        INode left = this._ArithParseBitwiseXor();
        while (true)
        {
            this._ArithSkipWs();
            if (this._ArithPeek(0) == "|" && this._ArithPeek(1) != "|" && this._ArithPeek(1) != "=")
            {
                this._ArithAdvance();
                this._ArithSkipWs();
                INode right = this._ArithParseBitwiseXor();
                left = new ArithBinaryOp("|", left, right, "binary-op");
            }
            else
            {
                break;
            }
        }
        return left;
    }

    public INode _ArithParseBitwiseXor()
    {
        INode left = this._ArithParseBitwiseAnd();
        while (true)
        {
            this._ArithSkipWs();
            if (this._ArithPeek(0) == "^" && this._ArithPeek(1) != "=")
            {
                this._ArithAdvance();
                this._ArithSkipWs();
                INode right = this._ArithParseBitwiseAnd();
                left = new ArithBinaryOp("^", left, right, "binary-op");
            }
            else
            {
                break;
            }
        }
        return left;
    }

    public INode _ArithParseBitwiseAnd()
    {
        INode left = this._ArithParseEquality();
        while (true)
        {
            this._ArithSkipWs();
            if (this._ArithPeek(0) == "&" && this._ArithPeek(1) != "&" && this._ArithPeek(1) != "=")
            {
                this._ArithAdvance();
                this._ArithSkipWs();
                INode right = this._ArithParseEquality();
                left = new ArithBinaryOp("&", left, right, "binary-op");
            }
            else
            {
                break;
            }
        }
        return left;
    }

    public INode _ArithParseEquality()
    {
        return this._ArithParseLeftAssoc(new List<string> { "==", "!=" }, this._ArithParseComparison);
    }

    public INode _ArithParseComparison()
    {
        INode left = this._ArithParseShift();
        while (true)
        {
            this._ArithSkipWs();
            INode right = null;
            if (this._ArithMatch("<="))
            {
                this._ArithConsume("<=");
                this._ArithSkipWs();
                right = this._ArithParseShift();
                left = new ArithBinaryOp("<=", left, right, "binary-op");
            }
            else
            {
                if (this._ArithMatch(">="))
                {
                    this._ArithConsume(">=");
                    this._ArithSkipWs();
                    right = this._ArithParseShift();
                    left = new ArithBinaryOp(">=", left, right, "binary-op");
                }
                else
                {
                    if (this._ArithPeek(0) == "<" && this._ArithPeek(1) != "<" && this._ArithPeek(1) != "=")
                    {
                        this._ArithAdvance();
                        this._ArithSkipWs();
                        right = this._ArithParseShift();
                        left = new ArithBinaryOp("<", left, right, "binary-op");
                    }
                    else
                    {
                        if (this._ArithPeek(0) == ">" && this._ArithPeek(1) != ">" && this._ArithPeek(1) != "=")
                        {
                            this._ArithAdvance();
                            this._ArithSkipWs();
                            right = this._ArithParseShift();
                            left = new ArithBinaryOp(">", left, right, "binary-op");
                        }
                        else
                        {
                            break;
                        }
                    }
                }
            }
        }
        return left;
    }

    public INode _ArithParseShift()
    {
        INode left = this._ArithParseAdditive();
        while (true)
        {
            this._ArithSkipWs();
            if (this._ArithMatch("<<="))
            {
                break;
            }
            if (this._ArithMatch(">>="))
            {
                break;
            }
            INode right = null;
            if (this._ArithMatch("<<"))
            {
                this._ArithConsume("<<");
                this._ArithSkipWs();
                right = this._ArithParseAdditive();
                left = new ArithBinaryOp("<<", left, right, "binary-op");
            }
            else
            {
                if (this._ArithMatch(">>"))
                {
                    this._ArithConsume(">>");
                    this._ArithSkipWs();
                    right = this._ArithParseAdditive();
                    left = new ArithBinaryOp(">>", left, right, "binary-op");
                }
                else
                {
                    break;
                }
            }
        }
        return left;
    }

    public INode _ArithParseAdditive()
    {
        INode left = this._ArithParseMultiplicative();
        while (true)
        {
            this._ArithSkipWs();
            string c = this._ArithPeek(0);
            string c2 = this._ArithPeek(1);
            INode right = null;
            if (c == "+" && c2 != "+" && c2 != "=")
            {
                this._ArithAdvance();
                this._ArithSkipWs();
                right = this._ArithParseMultiplicative();
                left = new ArithBinaryOp("+", left, right, "binary-op");
            }
            else
            {
                if (c == "-" && c2 != "-" && c2 != "=")
                {
                    this._ArithAdvance();
                    this._ArithSkipWs();
                    right = this._ArithParseMultiplicative();
                    left = new ArithBinaryOp("-", left, right, "binary-op");
                }
                else
                {
                    break;
                }
            }
        }
        return left;
    }

    public INode _ArithParseMultiplicative()
    {
        INode left = this._ArithParseExponentiation();
        while (true)
        {
            this._ArithSkipWs();
            string c = this._ArithPeek(0);
            string c2 = this._ArithPeek(1);
            INode right = null;
            if (c == "*" && c2 != "*" && c2 != "=")
            {
                this._ArithAdvance();
                this._ArithSkipWs();
                right = this._ArithParseExponentiation();
                left = new ArithBinaryOp("*", left, right, "binary-op");
            }
            else
            {
                if (c == "/" && c2 != "=")
                {
                    this._ArithAdvance();
                    this._ArithSkipWs();
                    right = this._ArithParseExponentiation();
                    left = new ArithBinaryOp("/", left, right, "binary-op");
                }
                else
                {
                    if (c == "%" && c2 != "=")
                    {
                        this._ArithAdvance();
                        this._ArithSkipWs();
                        right = this._ArithParseExponentiation();
                        left = new ArithBinaryOp("%", left, right, "binary-op");
                    }
                    else
                    {
                        break;
                    }
                }
            }
        }
        return left;
    }

    public INode _ArithParseExponentiation()
    {
        INode left = this._ArithParseUnary();
        this._ArithSkipWs();
        if (this._ArithMatch("**"))
        {
            this._ArithConsume("**");
            this._ArithSkipWs();
            INode right = this._ArithParseExponentiation();
            return new ArithBinaryOp("**", left, right, "binary-op");
        }
        return left;
    }

    public INode _ArithParseUnary()
    {
        this._ArithSkipWs();
        INode operand = null;
        if (this._ArithMatch("++"))
        {
            this._ArithConsume("++");
            this._ArithSkipWs();
            operand = this._ArithParseUnary();
            return new ArithPreIncr(operand, "pre-incr");
        }
        if (this._ArithMatch("--"))
        {
            this._ArithConsume("--");
            this._ArithSkipWs();
            operand = this._ArithParseUnary();
            return new ArithPreDecr(operand, "pre-decr");
        }
        string c = this._ArithPeek(0);
        if (c == "!")
        {
            this._ArithAdvance();
            this._ArithSkipWs();
            operand = this._ArithParseUnary();
            return new ArithUnaryOp("!", operand, "unary-op");
        }
        if (c == "~")
        {
            this._ArithAdvance();
            this._ArithSkipWs();
            operand = this._ArithParseUnary();
            return new ArithUnaryOp("~", operand, "unary-op");
        }
        if (c == "+" && this._ArithPeek(1) != "+")
        {
            this._ArithAdvance();
            this._ArithSkipWs();
            operand = this._ArithParseUnary();
            return new ArithUnaryOp("+", operand, "unary-op");
        }
        if (c == "-" && this._ArithPeek(1) != "-")
        {
            this._ArithAdvance();
            this._ArithSkipWs();
            operand = this._ArithParseUnary();
            return new ArithUnaryOp("-", operand, "unary-op");
        }
        return this._ArithParsePostfix();
    }

    public INode _ArithParsePostfix()
    {
        INode left = this._ArithParsePrimary();
        while (true)
        {
            this._ArithSkipWs();
            if (this._ArithMatch("++"))
            {
                this._ArithConsume("++");
                left = new ArithPostIncr(left, "post-incr");
            }
            else
            {
                if (this._ArithMatch("--"))
                {
                    this._ArithConsume("--");
                    left = new ArithPostDecr(left, "post-decr");
                }
                else
                {
                    if (this._ArithPeek(0) == "[")
                    {
                        bool _breakLoop5 = false;
                        switch (left)
                        {
                            case ArithVar leftArithVar:
                                this._ArithAdvance();
                                this._ArithSkipWs();
                                INode index = this._ArithParseComma();
                                this._ArithSkipWs();
                                if (!(this._ArithConsume("]")))
                                {
                                    throw new ParseError("Expected ']' in array subscript", this._ArithPos, 0);
                                }
                                left = new ArithSubscript(leftArithVar.Name, index, "subscript");
                                break;
                            default:
                                _breakLoop5 = true;
                                break;
                        }
                        if (_breakLoop5) break;
                    }
                    else
                    {
                        break;
                    }
                }
            }
        }
        return left;
    }

    public INode _ArithParsePrimary()
    {
        this._ArithSkipWs();
        string c = this._ArithPeek(0);
        if (c == "(")
        {
            this._ArithAdvance();
            this._ArithSkipWs();
            INode expr = this._ArithParseComma();
            this._ArithSkipWs();
            if (!(this._ArithConsume(")")))
            {
                throw new ParseError("Expected ')' in arithmetic expression", this._ArithPos, 0);
            }
            return expr;
        }
        if (c == "#" && this._ArithPeek(1) == "$")
        {
            this._ArithAdvance();
            return this._ArithParseExpansion();
        }
        if (c == "$")
        {
            return this._ArithParseExpansion();
        }
        if (c == "'")
        {
            return this._ArithParseSingleQuote();
        }
        if (c == "\"")
        {
            return this._ArithParseDoubleQuote();
        }
        if (c == "`")
        {
            return this._ArithParseBacktick();
        }
        if (c == "\\")
        {
            this._ArithAdvance();
            if (this._ArithAtEnd())
            {
                throw new ParseError("Unexpected end after backslash in arithmetic", this._ArithPos, 0);
            }
            string escapedChar = this._ArithAdvance();
            return new ArithEscape(escapedChar, "escape");
        }
        if (this._ArithAtEnd() || ")]:,;?|&<>=!+-*/%^~#{}".Contains(c))
        {
            return new ArithEmpty("empty");
        }
        return this._ArithParseNumberOrVar();
    }

    public INode _ArithParseExpansion()
    {
        if (!(this._ArithConsume("$")))
        {
            throw new ParseError("Expected '$'", this._ArithPos, 0);
        }
        string c = this._ArithPeek(0);
        if (c == "(")
        {
            return this._ArithParseCmdsub();
        }
        if (c == "{")
        {
            return this._ArithParseBracedParam();
        }
        List<string> nameChars = new List<string>();
        while (!(this._ArithAtEnd()))
        {
            string ch = this._ArithPeek(0);
            if ((ch.Length > 0 && ch.All(char.IsLetterOrDigit)) || ch == "_")
            {
                nameChars.Add(this._ArithAdvance());
            }
            else
            {
                if ((ParableFunctions._IsSpecialParamOrDigit(ch) || ch == "#") && !((nameChars.Count > 0)))
                {
                    nameChars.Add(this._ArithAdvance());
                    break;
                }
                else
                {
                    break;
                }
            }
        }
        if (!((nameChars.Count > 0)))
        {
            throw new ParseError("Expected variable name after $", this._ArithPos, 0);
        }
        return new ParamExpansion(string.Join("", nameChars), "", "", "param");
    }

    public INode _ArithParseCmdsub()
    {
        this._ArithAdvance();
        int depth = 0;
        int contentStart = 0;
        string ch = "";
        string content = "";
        if (this._ArithPeek(0) == "(")
        {
            this._ArithAdvance();
            depth = 1;
            contentStart = this._ArithPos;
            while (!(this._ArithAtEnd()) && depth > 0)
            {
                ch = this._ArithPeek(0);
                if (ch == "(")
                {
                    depth += 1;
                    this._ArithAdvance();
                }
                else
                {
                    if (ch == ")")
                    {
                        if (depth == 1 && this._ArithPeek(1) == ")")
                        {
                            break;
                        }
                        depth -= 1;
                        this._ArithAdvance();
                    }
                    else
                    {
                        this._ArithAdvance();
                    }
                }
            }
            content = ParableFunctions._Substring(this._ArithSrc, contentStart, this._ArithPos);
            this._ArithAdvance();
            this._ArithAdvance();
            INode innerExpr = this._ParseArithExpr(content);
            return new ArithmeticExpansion(innerExpr, "arith");
        }
        depth = 1;
        contentStart = this._ArithPos;
        while (!(this._ArithAtEnd()) && depth > 0)
        {
            ch = this._ArithPeek(0);
            if (ch == "(")
            {
                depth += 1;
                this._ArithAdvance();
            }
            else
            {
                if (ch == ")")
                {
                    depth -= 1;
                    if (depth == 0)
                    {
                        break;
                    }
                    this._ArithAdvance();
                }
                else
                {
                    this._ArithAdvance();
                }
            }
        }
        content = ParableFunctions._Substring(this._ArithSrc, contentStart, this._ArithPos);
        this._ArithAdvance();
        Parser subParser = ParableFunctions.NewParser(content, false, this._Extglob);
        INode cmd = subParser.ParseList(true);
        return new CommandSubstitution(cmd, false, "cmdsub");
    }

    public INode _ArithParseBracedParam()
    {
        this._ArithAdvance();
        List<string> nameChars = new List<string>();
        if (this._ArithPeek(0) == "!")
        {
            this._ArithAdvance();
            nameChars = new List<string>();
            while (!(this._ArithAtEnd()) && this._ArithPeek(0) != "}")
            {
                nameChars.Add(this._ArithAdvance());
            }
            this._ArithConsume("}");
            return new ParamIndirect(string.Join("", nameChars), "", "", "param-indirect");
        }
        if (this._ArithPeek(0) == "#")
        {
            this._ArithAdvance();
            nameChars = new List<string>();
            while (!(this._ArithAtEnd()) && this._ArithPeek(0) != "}")
            {
                nameChars.Add(this._ArithAdvance());
            }
            this._ArithConsume("}");
            return new ParamLength(string.Join("", nameChars), "param-len");
        }
        nameChars = new List<string>();
        string ch = "";
        while (!(this._ArithAtEnd()))
        {
            ch = this._ArithPeek(0);
            if (ch == "}")
            {
                this._ArithAdvance();
                return new ParamExpansion(string.Join("", nameChars), "", "", "param");
            }
            if (ParableFunctions._IsParamExpansionOp(ch))
            {
                break;
            }
            nameChars.Add(this._ArithAdvance());
        }
        string name = string.Join("", nameChars);
        List<string> opChars = new List<string>();
        int depth = 1;
        while (!(this._ArithAtEnd()) && depth > 0)
        {
            ch = this._ArithPeek(0);
            if (ch == "{")
            {
                depth += 1;
                opChars.Add(this._ArithAdvance());
            }
            else
            {
                if (ch == "}")
                {
                    depth -= 1;
                    if (depth == 0)
                    {
                        break;
                    }
                    opChars.Add(this._ArithAdvance());
                }
                else
                {
                    opChars.Add(this._ArithAdvance());
                }
            }
        }
        this._ArithConsume("}");
        string opStr = string.Join("", opChars);
        if (opStr.StartsWith(":-"))
        {
            return new ParamExpansion(name, ":-", ParableFunctions._Substring(opStr, 2, opStr.Length), "param");
        }
        if (opStr.StartsWith(":="))
        {
            return new ParamExpansion(name, ":=", ParableFunctions._Substring(opStr, 2, opStr.Length), "param");
        }
        if (opStr.StartsWith(":+"))
        {
            return new ParamExpansion(name, ":+", ParableFunctions._Substring(opStr, 2, opStr.Length), "param");
        }
        if (opStr.StartsWith(":?"))
        {
            return new ParamExpansion(name, ":?", ParableFunctions._Substring(opStr, 2, opStr.Length), "param");
        }
        if (opStr.StartsWith(":"))
        {
            return new ParamExpansion(name, ":", ParableFunctions._Substring(opStr, 1, opStr.Length), "param");
        }
        if (opStr.StartsWith("##"))
        {
            return new ParamExpansion(name, "##", ParableFunctions._Substring(opStr, 2, opStr.Length), "param");
        }
        if (opStr.StartsWith("#"))
        {
            return new ParamExpansion(name, "#", ParableFunctions._Substring(opStr, 1, opStr.Length), "param");
        }
        if (opStr.StartsWith("%%"))
        {
            return new ParamExpansion(name, "%%", ParableFunctions._Substring(opStr, 2, opStr.Length), "param");
        }
        if (opStr.StartsWith("%"))
        {
            return new ParamExpansion(name, "%", ParableFunctions._Substring(opStr, 1, opStr.Length), "param");
        }
        if (opStr.StartsWith("//"))
        {
            return new ParamExpansion(name, "//", ParableFunctions._Substring(opStr, 2, opStr.Length), "param");
        }
        if (opStr.StartsWith("/"))
        {
            return new ParamExpansion(name, "/", ParableFunctions._Substring(opStr, 1, opStr.Length), "param");
        }
        return new ParamExpansion(name, "", opStr, "param");
    }

    public INode _ArithParseSingleQuote()
    {
        this._ArithAdvance();
        int contentStart = this._ArithPos;
        while (!(this._ArithAtEnd()) && this._ArithPeek(0) != "'")
        {
            this._ArithAdvance();
        }
        string content = ParableFunctions._Substring(this._ArithSrc, contentStart, this._ArithPos);
        if (!(this._ArithConsume("'")))
        {
            throw new ParseError("Unterminated single quote in arithmetic", this._ArithPos, 0);
        }
        return new ArithNumber(content, "number");
    }

    public INode _ArithParseDoubleQuote()
    {
        this._ArithAdvance();
        int contentStart = this._ArithPos;
        while (!(this._ArithAtEnd()) && this._ArithPeek(0) != "\"")
        {
            string c = this._ArithPeek(0);
            if (c == "\\" && !(this._ArithAtEnd()))
            {
                this._ArithAdvance();
                this._ArithAdvance();
            }
            else
            {
                this._ArithAdvance();
            }
        }
        string content = ParableFunctions._Substring(this._ArithSrc, contentStart, this._ArithPos);
        if (!(this._ArithConsume("\"")))
        {
            throw new ParseError("Unterminated double quote in arithmetic", this._ArithPos, 0);
        }
        return new ArithNumber(content, "number");
    }

    public INode _ArithParseBacktick()
    {
        this._ArithAdvance();
        int contentStart = this._ArithPos;
        while (!(this._ArithAtEnd()) && this._ArithPeek(0) != "`")
        {
            string c = this._ArithPeek(0);
            if (c == "\\" && !(this._ArithAtEnd()))
            {
                this._ArithAdvance();
                this._ArithAdvance();
            }
            else
            {
                this._ArithAdvance();
            }
        }
        string content = ParableFunctions._Substring(this._ArithSrc, contentStart, this._ArithPos);
        if (!(this._ArithConsume("`")))
        {
            throw new ParseError("Unterminated backtick in arithmetic", this._ArithPos, 0);
        }
        Parser subParser = ParableFunctions.NewParser(content, false, this._Extglob);
        INode cmd = subParser.ParseList(true);
        return new CommandSubstitution(cmd, false, "cmdsub");
    }

    public INode _ArithParseNumberOrVar()
    {
        this._ArithSkipWs();
        List<string> chars = new List<string>();
        string c = this._ArithPeek(0);
        string ch = "";
        if ((c.Length > 0 && c.All(char.IsDigit)))
        {
            while (!(this._ArithAtEnd()))
            {
                ch = this._ArithPeek(0);
                if ((ch.Length > 0 && ch.All(char.IsLetterOrDigit)) || ch == "#" || ch == "_")
                {
                    chars.Add(this._ArithAdvance());
                }
                else
                {
                    break;
                }
            }
            string prefix = string.Join("", chars);
            if (!(this._ArithAtEnd()) && this._ArithPeek(0) == "$")
            {
                INode expansion = this._ArithParseExpansion();
                return new ArithConcat(new List<INode> { new ArithNumber(prefix, "number"), expansion }, "arith-concat");
            }
            return new ArithNumber(prefix, "number");
        }
        if ((c.Length > 0 && c.All(char.IsLetter)) || c == "_")
        {
            while (!(this._ArithAtEnd()))
            {
                ch = this._ArithPeek(0);
                if ((ch.Length > 0 && ch.All(char.IsLetterOrDigit)) || ch == "_")
                {
                    chars.Add(this._ArithAdvance());
                }
                else
                {
                    break;
                }
            }
            return new ArithVar(string.Join("", chars), "var");
        }
        throw new ParseError("Unexpected character '" + c + "' in arithmetic expression", this._ArithPos, 0);
    }

    public (INode, string) _ParseDeprecatedArithmetic()
    {
        if (this.AtEnd() || this.Peek() != "$")
        {
            return (null, "");
        }
        int start = this.Pos;
        if (this.Pos + 1 >= this.Length || (this.Source[this.Pos + 1]).ToString() != "[")
        {
            return (null, "");
        }
        this.Advance();
        this.Advance();
        this._Lexer.Pos = this.Pos;
        string content = this._Lexer._ParseMatchedPair("[", "]", Constants.MATCHEDPAIRFLAGS_ARITH, false);
        this.Pos = this._Lexer.Pos;
        string text = ParableFunctions._Substring(this.Source, start, this.Pos);
        return (new ArithDeprecated(content, "arith-deprecated"), text);
    }

    public (INode, string) _ParseParamExpansion(bool inDquote)
    {
        this._SyncLexer();
        (INode result0, string result1) = this._Lexer._ReadParamExpansion(inDquote);
        this._SyncParser();
        return (result0, result1);
    }

    public INode ParseRedirect()
    {
        this.SkipWhitespace();
        if (this.AtEnd())
        {
            return null;
        }
        int start = this.Pos;
        int fd = -1;
        string varfd = "";
        string ch = "";
        if (this.Peek() == "{")
        {
            int saved = this.Pos;
            this.Advance();
            List<string> varnameChars = new List<string>();
            bool inBracket = false;
            while (!(this.AtEnd()) && !(ParableFunctions._IsRedirectChar(this.Peek())))
            {
                ch = this.Peek();
                if (ch == "}" && !(inBracket))
                {
                    break;
                }
                else
                {
                    if (ch == "[")
                    {
                        inBracket = true;
                        varnameChars.Add(this.Advance());
                    }
                    else
                    {
                        if (ch == "]")
                        {
                            inBracket = false;
                            varnameChars.Add(this.Advance());
                        }
                        else
                        {
                            if ((ch.Length > 0 && ch.All(char.IsLetterOrDigit)) || ch == "_")
                            {
                                varnameChars.Add(this.Advance());
                            }
                            else
                            {
                                if (inBracket && !(ParableFunctions._IsMetachar(ch)))
                                {
                                    varnameChars.Add(this.Advance());
                                }
                                else
                                {
                                    break;
                                }
                            }
                        }
                    }
                }
            }
            string varname = string.Join("", varnameChars);
            bool isValidVarfd = false;
            if ((!string.IsNullOrEmpty(varname)))
            {
                if (((varname[0]).ToString().Length > 0 && (varname[0]).ToString().All(char.IsLetter)) || (varname[0]).ToString() == "_")
                {
                    if (varname.Contains("[") || varname.Contains("]"))
                    {
                        int left = varname.IndexOf("[");
                        int right = varname.LastIndexOf("]");
                        if (left != -1 && right == varname.Length - 1 && right > left + 1)
                        {
                            string @base = varname.Substring(0, left);
                            if ((!string.IsNullOrEmpty(@base)) && (((@base[0]).ToString().Length > 0 && (@base[0]).ToString().All(char.IsLetter)) || (@base[0]).ToString() == "_"))
                            {
                                isValidVarfd = true;
                                foreach (var _c5 in @base.Substring(1))
                                {
                                    var c = _c5.ToString();
                                    if (!((c.Length > 0 && c.All(char.IsLetterOrDigit)) || c == "_"))
                                    {
                                        isValidVarfd = false;
                                        break;
                                    }
                                }
                            }
                        }
                    }
                    else
                    {
                        isValidVarfd = true;
                        foreach (var _c6 in varname.Substring(1))
                        {
                            var c = _c6.ToString();
                            if (!((c.Length > 0 && c.All(char.IsLetterOrDigit)) || c == "_"))
                            {
                                isValidVarfd = false;
                                break;
                            }
                        }
                    }
                }
            }
            if (!(this.AtEnd()) && this.Peek() == "}" && isValidVarfd)
            {
                this.Advance();
                varfd = varname;
            }
            else
            {
                this.Pos = saved;
            }
        }
        List<string> fdChars = new List<string>();
        if (varfd == "" && (!string.IsNullOrEmpty(this.Peek())) && (this.Peek().Length > 0 && this.Peek().All(char.IsDigit)))
        {
            fdChars = new List<string>();
            while (!(this.AtEnd()) && (this.Peek().Length > 0 && this.Peek().All(char.IsDigit)))
            {
                fdChars.Add(this.Advance());
            }
            fd = ((int)Convert.ToInt64(string.Join("", fdChars), 10));
        }
        ch = this.Peek();
        string op = "";
        Word target = null;
        if (ch == "&" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == ">")
        {
            if (fd != -1 || varfd != "")
            {
                this.Pos = start;
                return null;
            }
            this.Advance();
            this.Advance();
            if (!(this.AtEnd()) && this.Peek() == ">")
            {
                this.Advance();
                op = "&>>";
            }
            else
            {
                op = "&>";
            }
            this.SkipWhitespace();
            target = this.ParseWord(false, false, false);
            if (target == null)
            {
                throw new ParseError("Expected target for redirect " + op, this.Pos, 0);
            }
            return new Redirect(op, target, null, "redirect");
        }
        if (ch == "" || !(ParableFunctions._IsRedirectChar(ch)))
        {
            this.Pos = start;
            return null;
        }
        if (fd == -1 && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "(")
        {
            this.Pos = start;
            return null;
        }
        op = this.Advance();
        bool stripTabs = false;
        if (!(this.AtEnd()))
        {
            string nextCh = this.Peek();
            if (op == ">" && nextCh == ">")
            {
                this.Advance();
                op = ">>";
            }
            else
            {
                if (op == "<" && nextCh == "<")
                {
                    this.Advance();
                    if (!(this.AtEnd()) && this.Peek() == "<")
                    {
                        this.Advance();
                        op = "<<<";
                    }
                    else
                    {
                        if (!(this.AtEnd()) && this.Peek() == "-")
                        {
                            this.Advance();
                            op = "<<";
                            stripTabs = true;
                        }
                        else
                        {
                            op = "<<";
                        }
                    }
                }
                else
                {
                    if (op == "<" && nextCh == ">")
                    {
                        this.Advance();
                        op = "<>";
                    }
                    else
                    {
                        if (op == ">" && nextCh == "|")
                        {
                            this.Advance();
                            op = ">|";
                        }
                        else
                        {
                            if (fd == -1 && varfd == "" && op == ">" && nextCh == "&")
                            {
                                if (this.Pos + 1 >= this.Length || !(ParableFunctions._IsDigitOrDash((this.Source[this.Pos + 1]).ToString())))
                                {
                                    this.Advance();
                                    op = ">&";
                                }
                            }
                            else
                            {
                                if (fd == -1 && varfd == "" && op == "<" && nextCh == "&")
                                {
                                    if (this.Pos + 1 >= this.Length || !(ParableFunctions._IsDigitOrDash((this.Source[this.Pos + 1]).ToString())))
                                    {
                                        this.Advance();
                                        op = "<&";
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        if (op == "<<")
        {
            return this._ParseHeredoc(fd, stripTabs);
        }
        if (varfd != "")
        {
            op = "{" + varfd + "}" + op;
        }
        else
        {
            if (fd != -1)
            {
                op = fd.ToString() + op;
            }
        }
        if (!(this.AtEnd()) && this.Peek() == "&")
        {
            this.Advance();
            this.SkipWhitespace();
            if (!(this.AtEnd()) && this.Peek() == "-")
            {
                if (this.Pos + 1 < this.Length && !(ParableFunctions._IsMetachar((this.Source[this.Pos + 1]).ToString())))
                {
                    this.Advance();
                    target = new Word("&-", new List<INode>(), "word");
                }
                else
                {
                    target = null;
                }
            }
            else
            {
                target = null;
            }
            if (target == null)
            {
                Word innerWord = null;
                if (!(this.AtEnd()) && ((this.Peek().Length > 0 && this.Peek().All(char.IsDigit)) || this.Peek() == "-"))
                {
                    int wordStart = this.Pos;
                    fdChars = new List<string>();
                    while (!(this.AtEnd()) && (this.Peek().Length > 0 && this.Peek().All(char.IsDigit)))
                    {
                        fdChars.Add(this.Advance());
                    }
                    string fdTarget = "";
                    if ((fdChars.Count > 0))
                    {
                        fdTarget = string.Join("", fdChars);
                    }
                    else
                    {
                        fdTarget = "";
                    }
                    if (!(this.AtEnd()) && this.Peek() == "-")
                    {
                        fdTarget += this.Advance();
                    }
                    if (fdTarget != "-" && !(this.AtEnd()) && !(ParableFunctions._IsMetachar(this.Peek())))
                    {
                        this.Pos = wordStart;
                        innerWord = this.ParseWord(false, false, false);
                        if (innerWord != null)
                        {
                            target = new Word("&" + innerWord.Value, new List<INode>(), "word");
                            target.Parts = innerWord.Parts;
                        }
                        else
                        {
                            throw new ParseError("Expected target for redirect " + op, this.Pos, 0);
                        }
                    }
                    else
                    {
                        target = new Word("&" + fdTarget, new List<INode>(), "word");
                    }
                }
                else
                {
                    innerWord = this.ParseWord(false, false, false);
                    if (innerWord != null)
                    {
                        target = new Word("&" + innerWord.Value, new List<INode>(), "word");
                        target.Parts = innerWord.Parts;
                    }
                    else
                    {
                        throw new ParseError("Expected target for redirect " + op, this.Pos, 0);
                    }
                }
            }
        }
        else
        {
            this.SkipWhitespace();
            if ((op == ">&" || op == "<&") && !(this.AtEnd()) && this.Peek() == "-")
            {
                if (this.Pos + 1 < this.Length && !(ParableFunctions._IsMetachar((this.Source[this.Pos + 1]).ToString())))
                {
                    this.Advance();
                    target = new Word("&-", new List<INode>(), "word");
                }
                else
                {
                    target = this.ParseWord(false, false, false);
                }
            }
            else
            {
                target = this.ParseWord(false, false, false);
            }
        }
        if (target == null)
        {
            throw new ParseError("Expected target for redirect " + op, this.Pos, 0);
        }
        return new Redirect(op, target, null, "redirect");
    }

    public (string, bool) _ParseHeredocDelimiter()
    {
        this.SkipWhitespace();
        bool quoted = false;
        List<string> delimiterChars = new List<string>();
        while (true)
        {
            string c = "";
            int depth = 0;
            while (!(this.AtEnd()) && !(ParableFunctions._IsMetachar(this.Peek())))
            {
                string ch = this.Peek();
                if (ch == "\"")
                {
                    quoted = true;
                    this.Advance();
                    while (!(this.AtEnd()) && this.Peek() != "\"")
                    {
                        delimiterChars.Add(this.Advance());
                    }
                    if (!(this.AtEnd()))
                    {
                        this.Advance();
                    }
                }
                else
                {
                    if (ch == "'")
                    {
                        quoted = true;
                        this.Advance();
                        while (!(this.AtEnd()) && this.Peek() != "'")
                        {
                            c = this.Advance();
                            if (c == "\n")
                            {
                                this._SawNewlineInSingleQuote = true;
                            }
                            delimiterChars.Add(c);
                        }
                        if (!(this.AtEnd()))
                        {
                            this.Advance();
                        }
                    }
                    else
                    {
                        if (ch == "\\")
                        {
                            this.Advance();
                            if (!(this.AtEnd()))
                            {
                                string nextCh = this.Peek();
                                if (nextCh == "\n")
                                {
                                    this.Advance();
                                }
                                else
                                {
                                    quoted = true;
                                    delimiterChars.Add(this.Advance());
                                }
                            }
                        }
                        else
                        {
                            if (ch == "$" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "'")
                            {
                                quoted = true;
                                this.Advance();
                                this.Advance();
                                while (!(this.AtEnd()) && this.Peek() != "'")
                                {
                                    c = this.Peek();
                                    if (c == "\\" && this.Pos + 1 < this.Length)
                                    {
                                        this.Advance();
                                        string esc = this.Peek();
                                        int escVal = ParableFunctions._GetAnsiEscape(esc);
                                        if (escVal >= 0)
                                        {
                                            delimiterChars.Add(char.ConvertFromUtf32(escVal));
                                            this.Advance();
                                        }
                                        else
                                        {
                                            if (esc == "'")
                                            {
                                                delimiterChars.Add(this.Advance());
                                            }
                                            else
                                            {
                                                delimiterChars.Add(this.Advance());
                                            }
                                        }
                                    }
                                    else
                                    {
                                        delimiterChars.Add(this.Advance());
                                    }
                                }
                                if (!(this.AtEnd()))
                                {
                                    this.Advance();
                                }
                            }
                            else
                            {
                                if (ParableFunctions._IsExpansionStart(this.Source, this.Pos, "$("))
                                {
                                    delimiterChars.Add(this.Advance());
                                    delimiterChars.Add(this.Advance());
                                    depth = 1;
                                    while (!(this.AtEnd()) && depth > 0)
                                    {
                                        c = this.Peek();
                                        if (c == "(")
                                        {
                                            depth += 1;
                                        }
                                        else
                                        {
                                            if (c == ")")
                                            {
                                                depth -= 1;
                                            }
                                        }
                                        delimiterChars.Add(this.Advance());
                                    }
                                }
                                else
                                {
                                    int dollarCount = 0;
                                    int j = 0;
                                    if (ch == "$" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "{")
                                    {
                                        dollarCount = 0;
                                        j = this.Pos - 1;
                                        while (j >= 0 && (this.Source[j]).ToString() == "$")
                                        {
                                            dollarCount += 1;
                                            j -= 1;
                                        }
                                        if (j >= 0 && (this.Source[j]).ToString() == "\\")
                                        {
                                            dollarCount -= 1;
                                        }
                                        if (dollarCount % 2 == 1)
                                        {
                                            delimiterChars.Add(this.Advance());
                                        }
                                        else
                                        {
                                            delimiterChars.Add(this.Advance());
                                            delimiterChars.Add(this.Advance());
                                            depth = 0;
                                            while (!(this.AtEnd()))
                                            {
                                                c = this.Peek();
                                                if (c == "{")
                                                {
                                                    depth += 1;
                                                }
                                                else
                                                {
                                                    if (c == "}")
                                                    {
                                                        delimiterChars.Add(this.Advance());
                                                        if (depth == 0)
                                                        {
                                                            break;
                                                        }
                                                        depth -= 1;
                                                        if (depth == 0 && !(this.AtEnd()) && ParableFunctions._IsMetachar(this.Peek()))
                                                        {
                                                            break;
                                                        }
                                                        continue;
                                                    }
                                                }
                                                delimiterChars.Add(this.Advance());
                                            }
                                        }
                                    }
                                    else
                                    {
                                        if (ch == "$" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "[")
                                        {
                                            dollarCount = 0;
                                            j = this.Pos - 1;
                                            while (j >= 0 && (this.Source[j]).ToString() == "$")
                                            {
                                                dollarCount += 1;
                                                j -= 1;
                                            }
                                            if (j >= 0 && (this.Source[j]).ToString() == "\\")
                                            {
                                                dollarCount -= 1;
                                            }
                                            if (dollarCount % 2 == 1)
                                            {
                                                delimiterChars.Add(this.Advance());
                                            }
                                            else
                                            {
                                                delimiterChars.Add(this.Advance());
                                                delimiterChars.Add(this.Advance());
                                                depth = 1;
                                                while (!(this.AtEnd()) && depth > 0)
                                                {
                                                    c = this.Peek();
                                                    if (c == "[")
                                                    {
                                                        depth += 1;
                                                    }
                                                    else
                                                    {
                                                        if (c == "]")
                                                        {
                                                            depth -= 1;
                                                        }
                                                    }
                                                    delimiterChars.Add(this.Advance());
                                                }
                                            }
                                        }
                                        else
                                        {
                                            if (ch == "`")
                                            {
                                                delimiterChars.Add(this.Advance());
                                                while (!(this.AtEnd()) && this.Peek() != "`")
                                                {
                                                    c = this.Peek();
                                                    if (c == "'")
                                                    {
                                                        delimiterChars.Add(this.Advance());
                                                        while (!(this.AtEnd()) && this.Peek() != "'" && this.Peek() != "`")
                                                        {
                                                            delimiterChars.Add(this.Advance());
                                                        }
                                                        if (!(this.AtEnd()) && this.Peek() == "'")
                                                        {
                                                            delimiterChars.Add(this.Advance());
                                                        }
                                                    }
                                                    else
                                                    {
                                                        if (c == "\"")
                                                        {
                                                            delimiterChars.Add(this.Advance());
                                                            while (!(this.AtEnd()) && this.Peek() != "\"" && this.Peek() != "`")
                                                            {
                                                                if (this.Peek() == "\\" && this.Pos + 1 < this.Length)
                                                                {
                                                                    delimiterChars.Add(this.Advance());
                                                                }
                                                                delimiterChars.Add(this.Advance());
                                                            }
                                                            if (!(this.AtEnd()) && this.Peek() == "\"")
                                                            {
                                                                delimiterChars.Add(this.Advance());
                                                            }
                                                        }
                                                        else
                                                        {
                                                            if (c == "\\" && this.Pos + 1 < this.Length)
                                                            {
                                                                delimiterChars.Add(this.Advance());
                                                                delimiterChars.Add(this.Advance());
                                                            }
                                                            else
                                                            {
                                                                delimiterChars.Add(this.Advance());
                                                            }
                                                        }
                                                    }
                                                }
                                                if (!(this.AtEnd()))
                                                {
                                                    delimiterChars.Add(this.Advance());
                                                }
                                            }
                                            else
                                            {
                                                delimiterChars.Add(this.Advance());
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            if (!(this.AtEnd()) && "<>".Contains(this.Peek()) && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "(")
            {
                delimiterChars.Add(this.Advance());
                delimiterChars.Add(this.Advance());
                depth = 1;
                while (!(this.AtEnd()) && depth > 0)
                {
                    c = this.Peek();
                    if (c == "(")
                    {
                        depth += 1;
                    }
                    else
                    {
                        if (c == ")")
                        {
                            depth -= 1;
                        }
                    }
                    delimiterChars.Add(this.Advance());
                }
                continue;
            }
            break;
        }
        return (string.Join("", delimiterChars), quoted);
    }

    public (string, int) _ReadHeredocLine(bool quoted)
    {
        int lineStart = this.Pos;
        int lineEnd = this.Pos;
        while (lineEnd < this.Length && (this.Source[lineEnd]).ToString() != "\n")
        {
            lineEnd += 1;
        }
        string line = ParableFunctions._Substring(this.Source, lineStart, lineEnd);
        if (!(quoted))
        {
            while (lineEnd < this.Length)
            {
                int trailingBs = ParableFunctions._CountTrailingBackslashes(line);
                if (trailingBs % 2 == 0)
                {
                    break;
                }
                line = ParableFunctions._Substring(line, 0, line.Length - 1);
                lineEnd += 1;
                int nextLineStart = lineEnd;
                while (lineEnd < this.Length && (this.Source[lineEnd]).ToString() != "\n")
                {
                    lineEnd += 1;
                }
                line = line + ParableFunctions._Substring(this.Source, nextLineStart, lineEnd);
            }
        }
        return (line, lineEnd);
    }

    public (bool, string) _LineMatchesDelimiter(string line, string delimiter, bool stripTabs)
    {
        string checkLine = (stripTabs ? line.TrimStart("\t".ToCharArray()) : line);
        string normalizedCheck = ParableFunctions._NormalizeHeredocDelimiter(checkLine);
        string normalizedDelim = ParableFunctions._NormalizeHeredocDelimiter(delimiter);
        return (normalizedCheck == normalizedDelim, checkLine);
    }

    public void _GatherHeredocBodies()
    {
        foreach (HereDoc heredoc in this._PendingHeredocs)
        {
            List<string> contentLines = new List<string>();
            int lineStart = this.Pos;
            while (this.Pos < this.Length)
            {
                lineStart = this.Pos;
                (string line, int lineEnd) = this._ReadHeredocLine(heredoc.Quoted);
                (bool matches, string checkLine) = this._LineMatchesDelimiter(line, heredoc.Delimiter, heredoc.StripTabs);
                if (matches)
                {
                    this.Pos = (lineEnd < this.Length ? lineEnd + 1 : lineEnd);
                    break;
                }
                string normalizedCheck = ParableFunctions._NormalizeHeredocDelimiter(checkLine);
                string normalizedDelim = ParableFunctions._NormalizeHeredocDelimiter(heredoc.Delimiter);
                int tabsStripped = 0;
                if (this._EofToken == ")" && normalizedCheck.StartsWith(normalizedDelim))
                {
                    tabsStripped = line.Length - checkLine.Length;
                    this.Pos = lineStart + tabsStripped + heredoc.Delimiter.Length;
                    break;
                }
                if (lineEnd >= this.Length && normalizedCheck.StartsWith(normalizedDelim) && this._InProcessSub)
                {
                    tabsStripped = line.Length - checkLine.Length;
                    this.Pos = lineStart + tabsStripped + heredoc.Delimiter.Length;
                    break;
                }
                if (heredoc.StripTabs)
                {
                    line = line.TrimStart("\t".ToCharArray());
                }
                if (lineEnd < this.Length)
                {
                    contentLines.Add(line + "\n");
                    this.Pos = lineEnd + 1;
                }
                else
                {
                    bool addNewline = true;
                    if (!(heredoc.Quoted) && ParableFunctions._CountTrailingBackslashes(line) % 2 == 1)
                    {
                        addNewline = false;
                    }
                    contentLines.Add(line + (addNewline ? "\n" : ""));
                    this.Pos = this.Length;
                }
            }
            heredoc.Content = string.Join("", contentLines);
        }
        this._PendingHeredocs = new List<HereDoc>();
    }

    public HereDoc _ParseHeredoc(int? fd, bool stripTabs)
    {
        int startPos = this.Pos;
        this._SetState(Constants.PARSERSTATEFLAGS_PST_HEREDOC);
        (string delimiter, bool quoted) = this._ParseHeredocDelimiter();
        foreach (HereDoc existing in this._PendingHeredocs)
        {
            if (existing._StartPos == startPos && existing.Delimiter == delimiter)
            {
                this._ClearState(Constants.PARSERSTATEFLAGS_PST_HEREDOC);
                return existing;
            }
        }
        HereDoc heredoc = new HereDoc(delimiter, "", stripTabs, quoted, fd, false, 0, "heredoc");
        heredoc._StartPos = startPos;
        this._PendingHeredocs.Add(heredoc);
        this._ClearState(Constants.PARSERSTATEFLAGS_PST_HEREDOC);
        return heredoc;
    }

    public Command ParseCommand()
    {
        List<Word> words = new List<Word>();
        List<INode> redirects = new List<INode>();
        while (true)
        {
            this.SkipWhitespace();
            if (this._LexIsCommandTerminator())
            {
                break;
            }
            if (words.Count == 0)
            {
                string reserved = this._LexPeekReservedWord();
                if (reserved == "}" || reserved == "]]")
                {
                    break;
                }
            }
            INode redirect = this.ParseRedirect();
            if (redirect != null)
            {
                redirects.Add(redirect);
                continue;
            }
            bool allAssignments = true;
            foreach (Word w in words)
            {
                if (!(this._IsAssignmentWord(w)))
                {
                    allAssignments = false;
                    break;
                }
            }
            bool inAssignBuiltin = words.Count > 0 && Constants.ASSIGNMENT_BUILTINS.Contains(words[0].Value);
            Word word = this.ParseWord(!((words.Count > 0)) || allAssignments && redirects.Count == 0, false, inAssignBuiltin);
            if (word == null)
            {
                break;
            }
            words.Add(word);
        }
        if (!((words.Count > 0)) && !((redirects.Count > 0)))
        {
            return null;
        }
        return new Command(words, redirects, "command");
    }

    public Subshell ParseSubshell()
    {
        this.SkipWhitespace();
        if (this.AtEnd() || this.Peek() != "(")
        {
            return null;
        }
        this.Advance();
        this._SetState(Constants.PARSERSTATEFLAGS_PST_SUBSHELL);
        INode body = this.ParseList(true);
        if (body == null)
        {
            this._ClearState(Constants.PARSERSTATEFLAGS_PST_SUBSHELL);
            throw new ParseError("Expected command in subshell", this.Pos, 0);
        }
        this.SkipWhitespace();
        if (this.AtEnd() || this.Peek() != ")")
        {
            this._ClearState(Constants.PARSERSTATEFLAGS_PST_SUBSHELL);
            throw new ParseError("Expected ) to close subshell", this.Pos, 0);
        }
        this.Advance();
        this._ClearState(Constants.PARSERSTATEFLAGS_PST_SUBSHELL);
        return new Subshell(body, this._CollectRedirects(), "subshell");
    }

    public ArithmeticCommand ParseArithmeticCommand()
    {
        this.SkipWhitespace();
        if (this.AtEnd() || this.Peek() != "(" || this.Pos + 1 >= this.Length || (this.Source[this.Pos + 1]).ToString() != "(")
        {
            return null;
        }
        int savedPos = this.Pos;
        this.Advance();
        this.Advance();
        int contentStart = this.Pos;
        int depth = 1;
        while (!(this.AtEnd()) && depth > 0)
        {
            string c = this.Peek();
            if (c == "'")
            {
                this.Advance();
                while (!(this.AtEnd()) && this.Peek() != "'")
                {
                    this.Advance();
                }
                if (!(this.AtEnd()))
                {
                    this.Advance();
                }
            }
            else
            {
                if (c == "\"")
                {
                    this.Advance();
                    while (!(this.AtEnd()))
                    {
                        if (this.Peek() == "\\" && this.Pos + 1 < this.Length)
                        {
                            this.Advance();
                            this.Advance();
                        }
                        else
                        {
                            if (this.Peek() == "\"")
                            {
                                this.Advance();
                                break;
                            }
                            else
                            {
                                this.Advance();
                            }
                        }
                    }
                }
                else
                {
                    if (c == "\\" && this.Pos + 1 < this.Length)
                    {
                        this.Advance();
                        this.Advance();
                    }
                    else
                    {
                        if (c == "(")
                        {
                            depth += 1;
                            this.Advance();
                        }
                        else
                        {
                            if (c == ")")
                            {
                                if (depth == 1 && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == ")")
                                {
                                    break;
                                }
                                depth -= 1;
                                if (depth == 0)
                                {
                                    this.Pos = savedPos;
                                    return null;
                                }
                                this.Advance();
                            }
                            else
                            {
                                this.Advance();
                            }
                        }
                    }
                }
            }
        }
        if (this.AtEnd())
        {
            throw new MatchedPairError("unexpected EOF looking for `))'", savedPos, 0);
        }
        if (depth != 1)
        {
            this.Pos = savedPos;
            return null;
        }
        string content = ParableFunctions._Substring(this.Source, contentStart, this.Pos);
        content = content.Replace("\\\n", "");
        this.Advance();
        this.Advance();
        INode expr = this._ParseArithExpr(content);
        return new ArithmeticCommand(expr, this._CollectRedirects(), content, "arith-cmd");
    }

    public ConditionalExpr ParseConditionalExpr()
    {
        this.SkipWhitespace();
        if (this.AtEnd() || this.Peek() != "[" || this.Pos + 1 >= this.Length || (this.Source[this.Pos + 1]).ToString() != "[")
        {
            return null;
        }
        int nextPos = this.Pos + 2;
        if (nextPos < this.Length && !(ParableFunctions._IsWhitespace((this.Source[nextPos]).ToString()) || (this.Source[nextPos]).ToString() == "\\" && nextPos + 1 < this.Length && (this.Source[nextPos + 1]).ToString() == "\n"))
        {
            return null;
        }
        this.Advance();
        this.Advance();
        this._SetState(Constants.PARSERSTATEFLAGS_PST_CONDEXPR);
        this._WordContext = Constants.WORD_CTX_COND;
        INode body = this._ParseCondOr();
        while (!(this.AtEnd()) && ParableFunctions._IsWhitespaceNoNewline(this.Peek()))
        {
            this.Advance();
        }
        if (this.AtEnd() || this.Peek() != "]" || this.Pos + 1 >= this.Length || (this.Source[this.Pos + 1]).ToString() != "]")
        {
            this._ClearState(Constants.PARSERSTATEFLAGS_PST_CONDEXPR);
            this._WordContext = Constants.WORD_CTX_NORMAL;
            throw new ParseError("Expected ]] to close conditional expression", this.Pos, 0);
        }
        this.Advance();
        this.Advance();
        this._ClearState(Constants.PARSERSTATEFLAGS_PST_CONDEXPR);
        this._WordContext = Constants.WORD_CTX_NORMAL;
        return new ConditionalExpr(body, this._CollectRedirects(), "cond-expr");
    }

    public void _CondSkipWhitespace()
    {
        while (!(this.AtEnd()))
        {
            if (ParableFunctions._IsWhitespaceNoNewline(this.Peek()))
            {
                this.Advance();
            }
            else
            {
                if (this.Peek() == "\\" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "\n")
                {
                    this.Advance();
                    this.Advance();
                }
                else
                {
                    if (this.Peek() == "\n")
                    {
                        this.Advance();
                    }
                    else
                    {
                        break;
                    }
                }
            }
        }
    }

    public bool _CondAtEnd()
    {
        return this.AtEnd() || this.Peek() == "]" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "]";
    }

    public INode _ParseCondOr()
    {
        this._CondSkipWhitespace();
        INode left = this._ParseCondAnd();
        this._CondSkipWhitespace();
        if (!(this._CondAtEnd()) && this.Peek() == "|" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "|")
        {
            this.Advance();
            this.Advance();
            INode right = this._ParseCondOr();
            return new CondOr(left, right, "cond-or");
        }
        return left;
    }

    public INode _ParseCondAnd()
    {
        this._CondSkipWhitespace();
        INode left = this._ParseCondTerm();
        this._CondSkipWhitespace();
        if (!(this._CondAtEnd()) && this.Peek() == "&" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "&")
        {
            this.Advance();
            this.Advance();
            INode right = this._ParseCondAnd();
            return new CondAnd(left, right, "cond-and");
        }
        return left;
    }

    public INode _ParseCondTerm()
    {
        this._CondSkipWhitespace();
        if (this._CondAtEnd())
        {
            throw new ParseError("Unexpected end of conditional expression", this.Pos, 0);
        }
        INode operand = null;
        if (this.Peek() == "!")
        {
            if (this.Pos + 1 < this.Length && !(ParableFunctions._IsWhitespaceNoNewline((this.Source[this.Pos + 1]).ToString())))
            {
            }
            else
            {
                this.Advance();
                operand = this._ParseCondTerm();
                return new CondNot(operand, "cond-not");
            }
        }
        if (this.Peek() == "(")
        {
            this.Advance();
            INode inner = this._ParseCondOr();
            this._CondSkipWhitespace();
            if (this.AtEnd() || this.Peek() != ")")
            {
                throw new ParseError("Expected ) in conditional expression", this.Pos, 0);
            }
            this.Advance();
            return new CondParen(inner, "cond-paren");
        }
        Word word1 = this._ParseCondWord();
        if (word1 == null)
        {
            throw new ParseError("Expected word in conditional expression", this.Pos, 0);
        }
        this._CondSkipWhitespace();
        if (Constants.COND_UNARY_OPS.Contains(word1.Value))
        {
            operand = this._ParseCondWord();
            if (operand == null)
            {
                throw new ParseError("Expected operand after " + word1.Value, this.Pos, 0);
            }
            return new UnaryTest(word1.Value, operand, "unary-test");
        }
        if (!(this._CondAtEnd()) && this.Peek() != "&" && this.Peek() != "|" && this.Peek() != ")")
        {
            Word word2 = null;
            if (ParableFunctions._IsRedirectChar(this.Peek()) && !(this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "("))
            {
                string op = this.Advance();
                this._CondSkipWhitespace();
                word2 = this._ParseCondWord();
                if (word2 == null)
                {
                    throw new ParseError("Expected operand after " + op, this.Pos, 0);
                }
                return new BinaryTest(op, word1, word2, "binary-test");
            }
            int savedPos = this.Pos;
            Word opWord = this._ParseCondWord();
            if (opWord != null && Constants.COND_BINARY_OPS.Contains(opWord.Value))
            {
                this._CondSkipWhitespace();
                if (opWord.Value == "=~")
                {
                    word2 = this._ParseCondRegexWord();
                }
                else
                {
                    word2 = this._ParseCondWord();
                }
                if (word2 == null)
                {
                    throw new ParseError("Expected operand after " + opWord.Value, this.Pos, 0);
                }
                return new BinaryTest(opWord.Value, word1, word2, "binary-test");
            }
            else
            {
                this.Pos = savedPos;
            }
        }
        return new UnaryTest("-n", word1, "unary-test");
    }

    public Word _ParseCondWord()
    {
        this._CondSkipWhitespace();
        if (this._CondAtEnd())
        {
            return null;
        }
        string c = this.Peek();
        if (ParableFunctions._IsParen(c))
        {
            return null;
        }
        if (c == "&" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "&")
        {
            return null;
        }
        if (c == "|" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "|")
        {
            return null;
        }
        return this._ParseWordInternal(Constants.WORD_CTX_COND, false, false);
    }

    public Word _ParseCondRegexWord()
    {
        this._CondSkipWhitespace();
        if (this._CondAtEnd())
        {
            return null;
        }
        this._SetState(Constants.PARSERSTATEFLAGS_PST_REGEXP);
        Word result = this._ParseWordInternal(Constants.WORD_CTX_REGEX, false, false);
        this._ClearState(Constants.PARSERSTATEFLAGS_PST_REGEXP);
        this._WordContext = Constants.WORD_CTX_COND;
        return result;
    }

    public BraceGroup ParseBraceGroup()
    {
        this.SkipWhitespace();
        if (!(this._LexConsumeWord("{")))
        {
            return null;
        }
        this.SkipWhitespaceAndNewlines();
        INode body = this.ParseList(true);
        if (body == null)
        {
            throw new ParseError("Expected command in brace group", this._LexPeekToken().Pos, 0);
        }
        this.SkipWhitespace();
        if (!(this._LexConsumeWord("}")))
        {
            throw new ParseError("Expected } to close brace group", this._LexPeekToken().Pos, 0);
        }
        return new BraceGroup(body, this._CollectRedirects(), "brace-group");
    }

    public If ParseIf()
    {
        this.SkipWhitespace();
        if (!(this._LexConsumeWord("if")))
        {
            return null;
        }
        INode condition = this.ParseListUntil(new HashSet<string> { "then" });
        if (condition == null)
        {
            throw new ParseError("Expected condition after 'if'", this._LexPeekToken().Pos, 0);
        }
        this.SkipWhitespaceAndNewlines();
        if (!(this._LexConsumeWord("then")))
        {
            throw new ParseError("Expected 'then' after if condition", this._LexPeekToken().Pos, 0);
        }
        INode thenBody = this.ParseListUntil(new HashSet<string> { "elif", "else", "fi" });
        if (thenBody == null)
        {
            throw new ParseError("Expected commands after 'then'", this._LexPeekToken().Pos, 0);
        }
        this.SkipWhitespaceAndNewlines();
        INode elseBody = null;
        if (this._LexIsAtReservedWord("elif"))
        {
            this._LexConsumeWord("elif");
            INode elifCondition = this.ParseListUntil(new HashSet<string> { "then" });
            if (elifCondition == null)
            {
                throw new ParseError("Expected condition after 'elif'", this._LexPeekToken().Pos, 0);
            }
            this.SkipWhitespaceAndNewlines();
            if (!(this._LexConsumeWord("then")))
            {
                throw new ParseError("Expected 'then' after elif condition", this._LexPeekToken().Pos, 0);
            }
            INode elifThenBody = this.ParseListUntil(new HashSet<string> { "elif", "else", "fi" });
            if (elifThenBody == null)
            {
                throw new ParseError("Expected commands after 'then'", this._LexPeekToken().Pos, 0);
            }
            this.SkipWhitespaceAndNewlines();
            INode innerElse = null;
            if (this._LexIsAtReservedWord("elif"))
            {
                innerElse = this._ParseElifChain();
            }
            else
            {
                if (this._LexIsAtReservedWord("else"))
                {
                    this._LexConsumeWord("else");
                    innerElse = this.ParseListUntil(new HashSet<string> { "fi" });
                    if (innerElse == null)
                    {
                        throw new ParseError("Expected commands after 'else'", this._LexPeekToken().Pos, 0);
                    }
                }
            }
            elseBody = new If(elifCondition, elifThenBody, innerElse, new List<INode>(), "if");
        }
        else
        {
            if (this._LexIsAtReservedWord("else"))
            {
                this._LexConsumeWord("else");
                elseBody = this.ParseListUntil(new HashSet<string> { "fi" });
                if (elseBody == null)
                {
                    throw new ParseError("Expected commands after 'else'", this._LexPeekToken().Pos, 0);
                }
            }
        }
        this.SkipWhitespaceAndNewlines();
        if (!(this._LexConsumeWord("fi")))
        {
            throw new ParseError("Expected 'fi' to close if statement", this._LexPeekToken().Pos, 0);
        }
        return new If(condition, thenBody, elseBody, this._CollectRedirects(), "if");
    }

    public If _ParseElifChain()
    {
        this._LexConsumeWord("elif");
        INode condition = this.ParseListUntil(new HashSet<string> { "then" });
        if (condition == null)
        {
            throw new ParseError("Expected condition after 'elif'", this._LexPeekToken().Pos, 0);
        }
        this.SkipWhitespaceAndNewlines();
        if (!(this._LexConsumeWord("then")))
        {
            throw new ParseError("Expected 'then' after elif condition", this._LexPeekToken().Pos, 0);
        }
        INode thenBody = this.ParseListUntil(new HashSet<string> { "elif", "else", "fi" });
        if (thenBody == null)
        {
            throw new ParseError("Expected commands after 'then'", this._LexPeekToken().Pos, 0);
        }
        this.SkipWhitespaceAndNewlines();
        INode elseBody = null;
        if (this._LexIsAtReservedWord("elif"))
        {
            elseBody = this._ParseElifChain();
        }
        else
        {
            if (this._LexIsAtReservedWord("else"))
            {
                this._LexConsumeWord("else");
                elseBody = this.ParseListUntil(new HashSet<string> { "fi" });
                if (elseBody == null)
                {
                    throw new ParseError("Expected commands after 'else'", this._LexPeekToken().Pos, 0);
                }
            }
        }
        return new If(condition, thenBody, elseBody, new List<INode>(), "if");
    }

    public While ParseWhile()
    {
        this.SkipWhitespace();
        if (!(this._LexConsumeWord("while")))
        {
            return null;
        }
        INode condition = this.ParseListUntil(new HashSet<string> { "do" });
        if (condition == null)
        {
            throw new ParseError("Expected condition after 'while'", this._LexPeekToken().Pos, 0);
        }
        this.SkipWhitespaceAndNewlines();
        if (!(this._LexConsumeWord("do")))
        {
            throw new ParseError("Expected 'do' after while condition", this._LexPeekToken().Pos, 0);
        }
        INode body = this.ParseListUntil(new HashSet<string> { "done" });
        if (body == null)
        {
            throw new ParseError("Expected commands after 'do'", this._LexPeekToken().Pos, 0);
        }
        this.SkipWhitespaceAndNewlines();
        if (!(this._LexConsumeWord("done")))
        {
            throw new ParseError("Expected 'done' to close while loop", this._LexPeekToken().Pos, 0);
        }
        return new While(condition, body, this._CollectRedirects(), "while");
    }

    public Until ParseUntil()
    {
        this.SkipWhitespace();
        if (!(this._LexConsumeWord("until")))
        {
            return null;
        }
        INode condition = this.ParseListUntil(new HashSet<string> { "do" });
        if (condition == null)
        {
            throw new ParseError("Expected condition after 'until'", this._LexPeekToken().Pos, 0);
        }
        this.SkipWhitespaceAndNewlines();
        if (!(this._LexConsumeWord("do")))
        {
            throw new ParseError("Expected 'do' after until condition", this._LexPeekToken().Pos, 0);
        }
        INode body = this.ParseListUntil(new HashSet<string> { "done" });
        if (body == null)
        {
            throw new ParseError("Expected commands after 'do'", this._LexPeekToken().Pos, 0);
        }
        this.SkipWhitespaceAndNewlines();
        if (!(this._LexConsumeWord("done")))
        {
            throw new ParseError("Expected 'done' to close until loop", this._LexPeekToken().Pos, 0);
        }
        return new Until(condition, body, this._CollectRedirects(), "until");
    }

    public INode ParseFor()
    {
        this.SkipWhitespace();
        if (!(this._LexConsumeWord("for")))
        {
            return null;
        }
        this.SkipWhitespace();
        if (this.Peek() == "(" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "(")
        {
            return this._ParseForArith();
        }
        string varName = "";
        if (this.Peek() == "$")
        {
            Word varWord = this.ParseWord(false, false, false);
            if (varWord == null)
            {
                throw new ParseError("Expected variable name after 'for'", this._LexPeekToken().Pos, 0);
            }
            varName = varWord.Value;
        }
        else
        {
            varName = this.PeekWord();
            if (varName == "")
            {
                throw new ParseError("Expected variable name after 'for'", this._LexPeekToken().Pos, 0);
            }
            this.ConsumeWord(varName);
        }
        this.SkipWhitespace();
        if (this.Peek() == ";")
        {
            this.Advance();
        }
        this.SkipWhitespaceAndNewlines();
        List<Word> words = null;
        if (this._LexIsAtReservedWord("in"))
        {
            this._LexConsumeWord("in");
            this.SkipWhitespace();
            bool sawDelimiter = ParableFunctions._IsSemicolonOrNewline(this.Peek());
            if (this.Peek() == ";")
            {
                this.Advance();
            }
            this.SkipWhitespaceAndNewlines();
            words = new List<Word>();
            while (true)
            {
                this.SkipWhitespace();
                if (this.AtEnd())
                {
                    break;
                }
                if (ParableFunctions._IsSemicolonOrNewline(this.Peek()))
                {
                    sawDelimiter = true;
                    if (this.Peek() == ";")
                    {
                        this.Advance();
                    }
                    break;
                }
                if (this._LexIsAtReservedWord("do"))
                {
                    if (sawDelimiter)
                    {
                        break;
                    }
                    throw new ParseError("Expected ';' or newline before 'do'", this._LexPeekToken().Pos, 0);
                }
                Word word = this.ParseWord(false, false, false);
                if (word == null)
                {
                    break;
                }
                words.Add(word);
            }
        }
        this.SkipWhitespaceAndNewlines();
        if (this.Peek() == "{")
        {
            BraceGroup braceGroup = this.ParseBraceGroup();
            if (braceGroup == null)
            {
                throw new ParseError("Expected brace group in for loop", this._LexPeekToken().Pos, 0);
            }
            return new For(varName, words, braceGroup.Body, this._CollectRedirects(), "for");
        }
        if (!(this._LexConsumeWord("do")))
        {
            throw new ParseError("Expected 'do' in for loop", this._LexPeekToken().Pos, 0);
        }
        INode body = this.ParseListUntil(new HashSet<string> { "done" });
        if (body == null)
        {
            throw new ParseError("Expected commands after 'do'", this._LexPeekToken().Pos, 0);
        }
        this.SkipWhitespaceAndNewlines();
        if (!(this._LexConsumeWord("done")))
        {
            throw new ParseError("Expected 'done' to close for loop", this._LexPeekToken().Pos, 0);
        }
        return new For(varName, words, body, this._CollectRedirects(), "for");
    }

    public ForArith _ParseForArith()
    {
        this.Advance();
        this.Advance();
        List<string> parts = new List<string>();
        List<string> current = new List<string>();
        int parenDepth = 0;
        while (!(this.AtEnd()))
        {
            string ch = this.Peek();
            if (ch == "(")
            {
                parenDepth += 1;
                current.Add(this.Advance());
            }
            else
            {
                if (ch == ")")
                {
                    if (parenDepth > 0)
                    {
                        parenDepth -= 1;
                        current.Add(this.Advance());
                    }
                    else
                    {
                        if (this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == ")")
                        {
                            parts.Add(string.Join("", current).TrimStart(" \t".ToCharArray()));
                            this.Advance();
                            this.Advance();
                            break;
                        }
                        else
                        {
                            current.Add(this.Advance());
                        }
                    }
                }
                else
                {
                    if (ch == ";" && parenDepth == 0)
                    {
                        parts.Add(string.Join("", current).TrimStart(" \t".ToCharArray()));
                        current = new List<string>();
                        this.Advance();
                    }
                    else
                    {
                        current.Add(this.Advance());
                    }
                }
            }
        }
        if (parts.Count != 3)
        {
            throw new ParseError("Expected three expressions in for ((;;))", this.Pos, 0);
        }
        string init = parts[0];
        string cond = parts[1];
        string incr = parts[2];
        this.SkipWhitespace();
        if (!(this.AtEnd()) && this.Peek() == ";")
        {
            this.Advance();
        }
        this.SkipWhitespaceAndNewlines();
        INode body = this._ParseLoopBody("for loop");
        return new ForArith(init, cond, incr, body, this._CollectRedirects(), "for-arith");
    }

    public Select ParseSelect()
    {
        this.SkipWhitespace();
        if (!(this._LexConsumeWord("select")))
        {
            return null;
        }
        this.SkipWhitespace();
        string varName = this.PeekWord();
        if (varName == "")
        {
            throw new ParseError("Expected variable name after 'select'", this._LexPeekToken().Pos, 0);
        }
        this.ConsumeWord(varName);
        this.SkipWhitespace();
        if (this.Peek() == ";")
        {
            this.Advance();
        }
        this.SkipWhitespaceAndNewlines();
        List<Word> words = null;
        if (this._LexIsAtReservedWord("in"))
        {
            this._LexConsumeWord("in");
            this.SkipWhitespaceAndNewlines();
            words = new List<Word>();
            while (true)
            {
                this.SkipWhitespace();
                if (this.AtEnd())
                {
                    break;
                }
                if (ParableFunctions._IsSemicolonNewlineBrace(this.Peek()))
                {
                    if (this.Peek() == ";")
                    {
                        this.Advance();
                    }
                    break;
                }
                if (this._LexIsAtReservedWord("do"))
                {
                    break;
                }
                Word word = this.ParseWord(false, false, false);
                if (word == null)
                {
                    break;
                }
                words.Add(word);
            }
        }
        this.SkipWhitespaceAndNewlines();
        INode body = this._ParseLoopBody("select");
        return new Select(varName, words, body, this._CollectRedirects(), "select");
    }

    public string _ConsumeCaseTerminator()
    {
        string term = this._LexPeekCaseTerminator();
        if (term != "")
        {
            this._LexNextToken();
            return term;
        }
        return ";;";
    }

    public Case ParseCase()
    {
        if (!(this.ConsumeWord("case")))
        {
            return null;
        }
        this._SetState(Constants.PARSERSTATEFLAGS_PST_CASESTMT);
        this.SkipWhitespace();
        Word word = this.ParseWord(false, false, false);
        if (word == null)
        {
            throw new ParseError("Expected word after 'case'", this._LexPeekToken().Pos, 0);
        }
        this.SkipWhitespaceAndNewlines();
        if (!(this._LexConsumeWord("in")))
        {
            throw new ParseError("Expected 'in' after case word", this._LexPeekToken().Pos, 0);
        }
        this.SkipWhitespaceAndNewlines();
        List<INode> patterns = new List<INode>();
        this._SetState(Constants.PARSERSTATEFLAGS_PST_CASEPAT);
        while (true)
        {
            this.SkipWhitespaceAndNewlines();
            if (this._LexIsAtReservedWord("esac"))
            {
                int saved = this.Pos;
                this.SkipWhitespace();
                while (!(this.AtEnd()) && !(ParableFunctions._IsMetachar(this.Peek())) && !(ParableFunctions._IsQuote(this.Peek())))
                {
                    this.Advance();
                }
                this.SkipWhitespace();
                bool isPattern = false;
                if (!(this.AtEnd()) && this.Peek() == ")")
                {
                    if (this._EofToken == ")")
                    {
                        isPattern = false;
                    }
                    else
                    {
                        this.Advance();
                        this.SkipWhitespace();
                        if (!(this.AtEnd()))
                        {
                            string nextCh = this.Peek();
                            if (nextCh == ";")
                            {
                                isPattern = true;
                            }
                            else
                            {
                                if (!(ParableFunctions._IsNewlineOrRightParen(nextCh)))
                                {
                                    isPattern = true;
                                }
                            }
                        }
                    }
                }
                this.Pos = saved;
                if (!(isPattern))
                {
                    break;
                }
            }
            this.SkipWhitespaceAndNewlines();
            if (!(this.AtEnd()) && this.Peek() == "(")
            {
                this.Advance();
                this.SkipWhitespaceAndNewlines();
            }
            List<string> patternChars = new List<string>();
            int extglobDepth = 0;
            while (!(this.AtEnd()))
            {
                string ch = this.Peek();
                if (ch == ")")
                {
                    if (extglobDepth > 0)
                    {
                        patternChars.Add(this.Advance());
                        extglobDepth -= 1;
                    }
                    else
                    {
                        this.Advance();
                        break;
                    }
                }
                else
                {
                    if (ch == "\\")
                    {
                        if (this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "\n")
                        {
                            this.Advance();
                            this.Advance();
                        }
                        else
                        {
                            patternChars.Add(this.Advance());
                            if (!(this.AtEnd()))
                            {
                                patternChars.Add(this.Advance());
                            }
                        }
                    }
                    else
                    {
                        if (ParableFunctions._IsExpansionStart(this.Source, this.Pos, "$("))
                        {
                            patternChars.Add(this.Advance());
                            patternChars.Add(this.Advance());
                            if (!(this.AtEnd()) && this.Peek() == "(")
                            {
                                patternChars.Add(this.Advance());
                                int parenDepth = 2;
                                while (!(this.AtEnd()) && parenDepth > 0)
                                {
                                    string c = this.Peek();
                                    if (c == "(")
                                    {
                                        parenDepth += 1;
                                    }
                                    else
                                    {
                                        if (c == ")")
                                        {
                                            parenDepth -= 1;
                                        }
                                    }
                                    patternChars.Add(this.Advance());
                                }
                            }
                            else
                            {
                                extglobDepth += 1;
                            }
                        }
                        else
                        {
                            if (ch == "(" && extglobDepth > 0)
                            {
                                patternChars.Add(this.Advance());
                                extglobDepth += 1;
                            }
                            else
                            {
                                if (this._Extglob && ParableFunctions._IsExtglobPrefix(ch) && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "(")
                                {
                                    patternChars.Add(this.Advance());
                                    patternChars.Add(this.Advance());
                                    extglobDepth += 1;
                                }
                                else
                                {
                                    if (ch == "[")
                                    {
                                        bool isCharClass = false;
                                        int scanPos = this.Pos + 1;
                                        int scanDepth = 0;
                                        bool hasFirstBracketLiteral = false;
                                        if (scanPos < this.Length && ParableFunctions._IsCaretOrBang((this.Source[scanPos]).ToString()))
                                        {
                                            scanPos += 1;
                                        }
                                        if (scanPos < this.Length && (this.Source[scanPos]).ToString() == "]")
                                        {
                                            if (this.Source.IndexOf("]", scanPos + 1) != -1)
                                            {
                                                scanPos += 1;
                                                hasFirstBracketLiteral = true;
                                            }
                                        }
                                        while (scanPos < this.Length)
                                        {
                                            string sc = (this.Source[scanPos]).ToString();
                                            if (sc == "]" && scanDepth == 0)
                                            {
                                                isCharClass = true;
                                                break;
                                            }
                                            else
                                            {
                                                if (sc == "[")
                                                {
                                                    scanDepth += 1;
                                                }
                                                else
                                                {
                                                    if (sc == ")" && scanDepth == 0)
                                                    {
                                                        break;
                                                    }
                                                    else
                                                    {
                                                        if (sc == "|" && scanDepth == 0)
                                                        {
                                                            break;
                                                        }
                                                    }
                                                }
                                            }
                                            scanPos += 1;
                                        }
                                        if (isCharClass)
                                        {
                                            patternChars.Add(this.Advance());
                                            if (!(this.AtEnd()) && ParableFunctions._IsCaretOrBang(this.Peek()))
                                            {
                                                patternChars.Add(this.Advance());
                                            }
                                            if (hasFirstBracketLiteral && !(this.AtEnd()) && this.Peek() == "]")
                                            {
                                                patternChars.Add(this.Advance());
                                            }
                                            while (!(this.AtEnd()) && this.Peek() != "]")
                                            {
                                                patternChars.Add(this.Advance());
                                            }
                                            if (!(this.AtEnd()))
                                            {
                                                patternChars.Add(this.Advance());
                                            }
                                        }
                                        else
                                        {
                                            patternChars.Add(this.Advance());
                                        }
                                    }
                                    else
                                    {
                                        if (ch == "'")
                                        {
                                            patternChars.Add(this.Advance());
                                            while (!(this.AtEnd()) && this.Peek() != "'")
                                            {
                                                patternChars.Add(this.Advance());
                                            }
                                            if (!(this.AtEnd()))
                                            {
                                                patternChars.Add(this.Advance());
                                            }
                                        }
                                        else
                                        {
                                            if (ch == "\"")
                                            {
                                                patternChars.Add(this.Advance());
                                                while (!(this.AtEnd()) && this.Peek() != "\"")
                                                {
                                                    if (this.Peek() == "\\" && this.Pos + 1 < this.Length)
                                                    {
                                                        patternChars.Add(this.Advance());
                                                    }
                                                    patternChars.Add(this.Advance());
                                                }
                                                if (!(this.AtEnd()))
                                                {
                                                    patternChars.Add(this.Advance());
                                                }
                                            }
                                            else
                                            {
                                                if (ParableFunctions._IsWhitespace(ch))
                                                {
                                                    if (extglobDepth > 0)
                                                    {
                                                        patternChars.Add(this.Advance());
                                                    }
                                                    else
                                                    {
                                                        this.Advance();
                                                    }
                                                }
                                                else
                                                {
                                                    patternChars.Add(this.Advance());
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
            string pattern = string.Join("", patternChars);
            if (!((!string.IsNullOrEmpty(pattern))))
            {
                throw new ParseError("Expected pattern in case statement", this._LexPeekToken().Pos, 0);
            }
            this.SkipWhitespace();
            INode body = null;
            bool isEmptyBody = this._LexPeekCaseTerminator() != "";
            if (!(isEmptyBody))
            {
                this.SkipWhitespaceAndNewlines();
                if (!(this.AtEnd()) && !(this._LexIsAtReservedWord("esac")))
                {
                    bool isAtTerminator = this._LexPeekCaseTerminator() != "";
                    if (!(isAtTerminator))
                    {
                        body = this.ParseListUntil(new HashSet<string> { "esac" });
                        this.SkipWhitespace();
                    }
                }
            }
            string terminator = this._ConsumeCaseTerminator();
            this.SkipWhitespaceAndNewlines();
            patterns.Add(new CasePattern(pattern, body, terminator, "pattern"));
        }
        this._ClearState(Constants.PARSERSTATEFLAGS_PST_CASEPAT);
        this.SkipWhitespaceAndNewlines();
        if (!(this._LexConsumeWord("esac")))
        {
            this._ClearState(Constants.PARSERSTATEFLAGS_PST_CASESTMT);
            throw new ParseError("Expected 'esac' to close case statement", this._LexPeekToken().Pos, 0);
        }
        this._ClearState(Constants.PARSERSTATEFLAGS_PST_CASESTMT);
        return new Case(word, patterns, this._CollectRedirects(), "case");
    }

    public Coproc ParseCoproc()
    {
        this.SkipWhitespace();
        if (!(this._LexConsumeWord("coproc")))
        {
            return null;
        }
        this.SkipWhitespace();
        string name = "";
        string ch = "";
        if (!(this.AtEnd()))
        {
            ch = this.Peek();
        }
        INode body = null;
        if (ch == "{")
        {
            body = this.ParseBraceGroup();
            if (body != null)
            {
                return new Coproc(body, name, "coproc");
            }
        }
        if (ch == "(")
        {
            if (this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "(")
            {
                body = this.ParseArithmeticCommand();
                if (body != null)
                {
                    return new Coproc(body, name, "coproc");
                }
            }
            body = this.ParseSubshell();
            if (body != null)
            {
                return new Coproc(body, name, "coproc");
            }
        }
        string nextWord = this._LexPeekReservedWord();
        if (nextWord != "" && Constants.COMPOUND_KEYWORDS.Contains(nextWord))
        {
            body = this.ParseCompoundCommand();
            if (body != null)
            {
                return new Coproc(body, name, "coproc");
            }
        }
        int wordStart = this.Pos;
        string potentialName = this.PeekWord();
        if ((!string.IsNullOrEmpty(potentialName)))
        {
            while (!(this.AtEnd()) && !(ParableFunctions._IsMetachar(this.Peek())) && !(ParableFunctions._IsQuote(this.Peek())))
            {
                this.Advance();
            }
            this.SkipWhitespace();
            ch = "";
            if (!(this.AtEnd()))
            {
                ch = this.Peek();
            }
            nextWord = this._LexPeekReservedWord();
            if (ParableFunctions._IsValidIdentifier(potentialName))
            {
                if (ch == "{")
                {
                    name = potentialName;
                    body = this.ParseBraceGroup();
                    if (body != null)
                    {
                        return new Coproc(body, name, "coproc");
                    }
                }
                else
                {
                    if (ch == "(")
                    {
                        name = potentialName;
                        if (this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "(")
                        {
                            body = this.ParseArithmeticCommand();
                        }
                        else
                        {
                            body = this.ParseSubshell();
                        }
                        if (body != null)
                        {
                            return new Coproc(body, name, "coproc");
                        }
                    }
                    else
                    {
                        if (nextWord != "" && Constants.COMPOUND_KEYWORDS.Contains(nextWord))
                        {
                            name = potentialName;
                            body = this.ParseCompoundCommand();
                            if (body != null)
                            {
                                return new Coproc(body, name, "coproc");
                            }
                        }
                    }
                }
            }
            this.Pos = wordStart;
        }
        body = this.ParseCommand();
        if (body != null)
        {
            return new Coproc(body, name, "coproc");
        }
        throw new ParseError("Expected command after coproc", this.Pos, 0);
    }

    public Function ParseFunction()
    {
        this.SkipWhitespace();
        if (this.AtEnd())
        {
            return null;
        }
        int savedPos = this.Pos;
        string name = "";
        INode body = null;
        if (this._LexIsAtReservedWord("function"))
        {
            this._LexConsumeWord("function");
            this.SkipWhitespace();
            name = this.PeekWord();
            if (name == "")
            {
                this.Pos = savedPos;
                return null;
            }
            this.ConsumeWord(name);
            this.SkipWhitespace();
            if (!(this.AtEnd()) && this.Peek() == "(")
            {
                if (this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == ")")
                {
                    this.Advance();
                    this.Advance();
                }
            }
            this.SkipWhitespaceAndNewlines();
            body = this._ParseCompoundCommand();
            if (body == null)
            {
                throw new ParseError("Expected function body", this.Pos, 0);
            }
            return new Function(name, body, "function");
        }
        name = this.PeekWord();
        if (name == "" || Constants.RESERVED_WORDS.Contains(name))
        {
            return null;
        }
        if (ParableFunctions._LooksLikeAssignment(name))
        {
            return null;
        }
        this.SkipWhitespace();
        int nameStart = this.Pos;
        while (!(this.AtEnd()) && !(ParableFunctions._IsMetachar(this.Peek())) && !(ParableFunctions._IsQuote(this.Peek())) && !(ParableFunctions._IsParen(this.Peek())))
        {
            this.Advance();
        }
        name = ParableFunctions._Substring(this.Source, nameStart, this.Pos);
        if (!((!string.IsNullOrEmpty(name))))
        {
            this.Pos = savedPos;
            return null;
        }
        int braceDepth = 0;
        int i = 0;
        while (i < name.Length)
        {
            if (ParableFunctions._IsExpansionStart(name, i, "${"))
            {
                braceDepth += 1;
                i += 2;
                continue;
            }
            if ((name[i]).ToString() == "}")
            {
                braceDepth -= 1;
            }
            i += 1;
        }
        if (braceDepth > 0)
        {
            this.Pos = savedPos;
            return null;
        }
        int posAfterName = this.Pos;
        this.SkipWhitespace();
        bool hasWhitespace = this.Pos > posAfterName;
        if (!(hasWhitespace) && (!string.IsNullOrEmpty(name)) && "*?@+!$".Contains((name[name.Length - 1]).ToString()))
        {
            this.Pos = savedPos;
            return null;
        }
        if (this.AtEnd() || this.Peek() != "(")
        {
            this.Pos = savedPos;
            return null;
        }
        this.Advance();
        this.SkipWhitespace();
        if (this.AtEnd() || this.Peek() != ")")
        {
            this.Pos = savedPos;
            return null;
        }
        this.Advance();
        this.SkipWhitespaceAndNewlines();
        body = this._ParseCompoundCommand();
        if (body == null)
        {
            throw new ParseError("Expected function body", this.Pos, 0);
        }
        return new Function(name, body, "function");
    }

    public INode _ParseCompoundCommand()
    {
        INode result = this.ParseBraceGroup();
        if (result != null)
        {
            return result;
        }
        if (!(this.AtEnd()) && this.Peek() == "(" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "(")
        {
            result = this.ParseArithmeticCommand();
            if (result != null)
            {
                return result;
            }
        }
        result = this.ParseSubshell();
        if (result != null)
        {
            return result;
        }
        result = this.ParseConditionalExpr();
        if (result != null)
        {
            return result;
        }
        result = this.ParseIf();
        if (result != null)
        {
            return result;
        }
        result = this.ParseWhile();
        if (result != null)
        {
            return result;
        }
        result = this.ParseUntil();
        if (result != null)
        {
            return result;
        }
        result = this.ParseFor();
        if (result != null)
        {
            return result;
        }
        result = this.ParseCase();
        if (result != null)
        {
            return result;
        }
        result = this.ParseSelect();
        if (result != null)
        {
            return result;
        }
        return null;
    }

    public bool _AtListUntilTerminator(HashSet<string> stopWords)
    {
        if (this.AtEnd())
        {
            return true;
        }
        if (this.Peek() == ")")
        {
            return true;
        }
        if (this.Peek() == "}")
        {
            int nextPos = this.Pos + 1;
            if (nextPos >= this.Length || ParableFunctions._IsWordEndContext((this.Source[nextPos]).ToString()))
            {
                return true;
            }
        }
        string reserved = this._LexPeekReservedWord();
        if (reserved != "" && stopWords.Contains(reserved))
        {
            return true;
        }
        if (this._LexPeekCaseTerminator() != "")
        {
            return true;
        }
        return false;
    }

    public INode ParseListUntil(HashSet<string> stopWords)
    {
        this.SkipWhitespaceAndNewlines();
        string reserved = this._LexPeekReservedWord();
        if (reserved != "" && stopWords.Contains(reserved))
        {
            return null;
        }
        INode pipeline = this.ParsePipeline();
        if (pipeline == null)
        {
            return null;
        }
        List<INode> parts = new List<INode> { pipeline };
        while (true)
        {
            this.SkipWhitespace();
            string op = this.ParseListOperator();
            if (op == "")
            {
                if (!(this.AtEnd()) && this.Peek() == "\n")
                {
                    this.Advance();
                    this._GatherHeredocBodies();
                    if (this._CmdsubHeredocEnd != -1 && this._CmdsubHeredocEnd > this.Pos)
                    {
                        this.Pos = this._CmdsubHeredocEnd;
                        this._CmdsubHeredocEnd = -1;
                    }
                    this.SkipWhitespaceAndNewlines();
                    if (this._AtListUntilTerminator(stopWords))
                    {
                        break;
                    }
                    string nextOp = this._PeekListOperator();
                    if (nextOp == "&" || nextOp == ";")
                    {
                        break;
                    }
                    op = "\n";
                }
                else
                {
                    break;
                }
            }
            if (op == "")
            {
                break;
            }
            if (op == ";")
            {
                this.SkipWhitespaceAndNewlines();
                if (this._AtListUntilTerminator(stopWords))
                {
                    break;
                }
                parts.Add(new Operator(op, "operator"));
            }
            else
            {
                if (op == "&")
                {
                    parts.Add(new Operator(op, "operator"));
                    this.SkipWhitespaceAndNewlines();
                    if (this._AtListUntilTerminator(stopWords))
                    {
                        break;
                    }
                }
                else
                {
                    if (op == "&&" || op == "||")
                    {
                        parts.Add(new Operator(op, "operator"));
                        this.SkipWhitespaceAndNewlines();
                    }
                    else
                    {
                        parts.Add(new Operator(op, "operator"));
                    }
                }
            }
            if (this._AtListUntilTerminator(stopWords))
            {
                break;
            }
            pipeline = this.ParsePipeline();
            if (pipeline == null)
            {
                throw new ParseError("Expected command after " + op, this.Pos, 0);
            }
            parts.Add(pipeline);
        }
        if (parts.Count == 1)
        {
            return parts[0];
        }
        return new List(parts, "list");
    }

    public INode ParseCompoundCommand()
    {
        this.SkipWhitespace();
        if (this.AtEnd())
        {
            return null;
        }
        string ch = this.Peek();
        INode result = null;
        if (ch == "(" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "(")
        {
            result = this.ParseArithmeticCommand();
            if (result != null)
            {
                return result;
            }
        }
        if (ch == "(")
        {
            return this.ParseSubshell();
        }
        if (ch == "{")
        {
            result = this.ParseBraceGroup();
            if (result != null)
            {
                return result;
            }
        }
        if (ch == "[" && this.Pos + 1 < this.Length && (this.Source[this.Pos + 1]).ToString() == "[")
        {
            result = this.ParseConditionalExpr();
            if (result != null)
            {
                return result;
            }
        }
        string reserved = this._LexPeekReservedWord();
        if (reserved == "" && this._InProcessSub)
        {
            string word = this.PeekWord();
            if (word != "" && word.Length > 1 && (word[0]).ToString() == "}")
            {
                string keywordWord = word.Substring(1);
                if (Constants.RESERVED_WORDS.Contains(keywordWord) || keywordWord == "{" || keywordWord == "}" || keywordWord == "[[" || keywordWord == "]]" || keywordWord == "!" || keywordWord == "time")
                {
                    reserved = keywordWord;
                }
            }
        }
        if (reserved == "fi" || reserved == "then" || reserved == "elif" || reserved == "else" || reserved == "done" || reserved == "esac" || reserved == "do" || reserved == "in")
        {
            throw new ParseError(string.Format("Unexpected reserved word '{0}'", reserved), this._LexPeekToken().Pos, 0);
        }
        if (reserved == "if")
        {
            return this.ParseIf();
        }
        if (reserved == "while")
        {
            return this.ParseWhile();
        }
        if (reserved == "until")
        {
            return this.ParseUntil();
        }
        if (reserved == "for")
        {
            return this.ParseFor();
        }
        if (reserved == "select")
        {
            return this.ParseSelect();
        }
        if (reserved == "case")
        {
            return this.ParseCase();
        }
        if (reserved == "function")
        {
            return this.ParseFunction();
        }
        if (reserved == "coproc")
        {
            return this.ParseCoproc();
        }
        Function func = this.ParseFunction();
        if (func != null)
        {
            return func;
        }
        return this.ParseCommand();
    }

    public INode ParsePipeline()
    {
        this.SkipWhitespace();
        string prefixOrder = "";
        bool timePosix = false;
        if (this._LexIsAtReservedWord("time"))
        {
            this._LexConsumeWord("time");
            prefixOrder = "time";
            this.SkipWhitespace();
            int saved = 0;
            if (!(this.AtEnd()) && this.Peek() == "-")
            {
                saved = this.Pos;
                this.Advance();
                if (!(this.AtEnd()) && this.Peek() == "p")
                {
                    this.Advance();
                    if (this.AtEnd() || ParableFunctions._IsMetachar(this.Peek()))
                    {
                        timePosix = true;
                    }
                    else
                    {
                        this.Pos = saved;
                    }
                }
                else
                {
                    this.Pos = saved;
                }
            }
            this.SkipWhitespace();
            if (!(this.AtEnd()) && ParableFunctions._StartsWithAt(this.Source, this.Pos, "--"))
            {
                if (this.Pos + 2 >= this.Length || ParableFunctions._IsWhitespace((this.Source[this.Pos + 2]).ToString()))
                {
                    this.Advance();
                    this.Advance();
                    timePosix = true;
                    this.SkipWhitespace();
                }
            }
            while (this._LexIsAtReservedWord("time"))
            {
                this._LexConsumeWord("time");
                this.SkipWhitespace();
                if (!(this.AtEnd()) && this.Peek() == "-")
                {
                    saved = this.Pos;
                    this.Advance();
                    if (!(this.AtEnd()) && this.Peek() == "p")
                    {
                        this.Advance();
                        if (this.AtEnd() || ParableFunctions._IsMetachar(this.Peek()))
                        {
                            timePosix = true;
                        }
                        else
                        {
                            this.Pos = saved;
                        }
                    }
                    else
                    {
                        this.Pos = saved;
                    }
                }
            }
            this.SkipWhitespace();
            if (!(this.AtEnd()) && this.Peek() == "!")
            {
                if ((this.Pos + 1 >= this.Length || ParableFunctions._IsNegationBoundary((this.Source[this.Pos + 1]).ToString())) && !(this._IsBangFollowedByProcsub()))
                {
                    this.Advance();
                    prefixOrder = "time_negation";
                    this.SkipWhitespace();
                }
            }
        }
        else
        {
            if (!(this.AtEnd()) && this.Peek() == "!")
            {
                if ((this.Pos + 1 >= this.Length || ParableFunctions._IsNegationBoundary((this.Source[this.Pos + 1]).ToString())) && !(this._IsBangFollowedByProcsub()))
                {
                    this.Advance();
                    this.SkipWhitespace();
                    INode inner = this.ParsePipeline();
                    if (inner != null && inner.Kind == "negation")
                    {
                        if (((Negation)inner).Pipeline != null)
                        {
                            return ((Negation)inner).Pipeline;
                        }
                        else
                        {
                            return new Command(new List<Word>(), new List<INode>(), "command");
                        }
                    }
                    return new Negation(inner, "negation");
                }
            }
        }
        INode result = this._ParseSimplePipeline();
        if (prefixOrder == "time")
        {
            result = new Time(result, timePosix, "time");
        }
        else
        {
            if (prefixOrder == "negation")
            {
                result = new Negation(result, "negation");
            }
            else
            {
                if (prefixOrder == "time_negation")
                {
                    result = new Time(result, timePosix, "time");
                    result = new Negation(result, "negation");
                }
                else
                {
                    if (prefixOrder == "negation_time")
                    {
                        result = new Time(result, timePosix, "time");
                        result = new Negation(result, "negation");
                    }
                    else
                    {
                        if (result == null)
                        {
                            return null;
                        }
                    }
                }
            }
        }
        return result;
    }

    public INode _ParseSimplePipeline()
    {
        INode cmd = this.ParseCompoundCommand();
        if (cmd == null)
        {
            return null;
        }
        List<INode> commands = new List<INode> { cmd };
        while (true)
        {
            this.SkipWhitespace();
            (int tokenType, string value) = this._LexPeekOperator();
            if (tokenType == 0)
            {
                break;
            }
            if (tokenType != Constants.TOKENTYPE_PIPE && tokenType != Constants.TOKENTYPE_PIPE_AMP)
            {
                break;
            }
            this._LexNextToken();
            bool isPipeBoth = tokenType == Constants.TOKENTYPE_PIPE_AMP;
            this.SkipWhitespaceAndNewlines();
            if (isPipeBoth)
            {
                commands.Add(new PipeBoth("pipe-both"));
            }
            cmd = this.ParseCompoundCommand();
            if (cmd == null)
            {
                throw new ParseError("Expected command after |", this.Pos, 0);
            }
            commands.Add(cmd);
        }
        if (commands.Count == 1)
        {
            return commands[0];
        }
        return new Pipeline(commands, "pipeline");
    }

    public string ParseListOperator()
    {
        this.SkipWhitespace();
        (int tokenType, string _) = this._LexPeekOperator();
        if (tokenType == 0)
        {
            return "";
        }
        if (tokenType == Constants.TOKENTYPE_AND_AND)
        {
            this._LexNextToken();
            return "&&";
        }
        if (tokenType == Constants.TOKENTYPE_OR_OR)
        {
            this._LexNextToken();
            return "||";
        }
        if (tokenType == Constants.TOKENTYPE_SEMI)
        {
            this._LexNextToken();
            return ";";
        }
        if (tokenType == Constants.TOKENTYPE_AMP)
        {
            this._LexNextToken();
            return "&";
        }
        return "";
    }

    public string _PeekListOperator()
    {
        int savedPos = this.Pos;
        string op = this.ParseListOperator();
        this.Pos = savedPos;
        return op;
    }

    public INode ParseList(bool newlineAsSeparator)
    {
        if (newlineAsSeparator)
        {
            this.SkipWhitespaceAndNewlines();
        }
        else
        {
            this.SkipWhitespace();
        }
        INode pipeline = this.ParsePipeline();
        if (pipeline == null)
        {
            return null;
        }
        List<INode> parts = new List<INode> { pipeline };
        if (this._InState(Constants.PARSERSTATEFLAGS_PST_EOFTOKEN) && this._AtEofToken())
        {
            return (parts.Count == 1 ? parts[0] : new List(parts, "list"));
        }
        while (true)
        {
            this.SkipWhitespace();
            string op = this.ParseListOperator();
            if (op == "")
            {
                if (!(this.AtEnd()) && this.Peek() == "\n")
                {
                    if (!(newlineAsSeparator))
                    {
                        break;
                    }
                    this.Advance();
                    this._GatherHeredocBodies();
                    if (this._CmdsubHeredocEnd != -1 && this._CmdsubHeredocEnd > this.Pos)
                    {
                        this.Pos = this._CmdsubHeredocEnd;
                        this._CmdsubHeredocEnd = -1;
                    }
                    this.SkipWhitespaceAndNewlines();
                    if (this.AtEnd() || this._AtListTerminatingBracket())
                    {
                        break;
                    }
                    string nextOp = this._PeekListOperator();
                    if (nextOp == "&" || nextOp == ";")
                    {
                        break;
                    }
                    op = "\n";
                }
                else
                {
                    break;
                }
            }
            if (op == "")
            {
                break;
            }
            parts.Add(new Operator(op, "operator"));
            if (op == "&&" || op == "||")
            {
                this.SkipWhitespaceAndNewlines();
            }
            else
            {
                if (op == "&")
                {
                    this.SkipWhitespace();
                    if (this.AtEnd() || this._AtListTerminatingBracket())
                    {
                        break;
                    }
                    if (this.Peek() == "\n")
                    {
                        if (newlineAsSeparator)
                        {
                            this.SkipWhitespaceAndNewlines();
                            if (this.AtEnd() || this._AtListTerminatingBracket())
                            {
                                break;
                            }
                        }
                        else
                        {
                            break;
                        }
                    }
                }
                else
                {
                    if (op == ";")
                    {
                        this.SkipWhitespace();
                        if (this.AtEnd() || this._AtListTerminatingBracket())
                        {
                            break;
                        }
                        if (this.Peek() == "\n")
                        {
                            if (newlineAsSeparator)
                            {
                                this.SkipWhitespaceAndNewlines();
                                if (this.AtEnd() || this._AtListTerminatingBracket())
                                {
                                    break;
                                }
                            }
                            else
                            {
                                break;
                            }
                        }
                    }
                }
            }
            pipeline = this.ParsePipeline();
            if (pipeline == null)
            {
                throw new ParseError("Expected command after " + op, this.Pos, 0);
            }
            parts.Add(pipeline);
            if (this._InState(Constants.PARSERSTATEFLAGS_PST_EOFTOKEN) && this._AtEofToken())
            {
                break;
            }
        }
        if (parts.Count == 1)
        {
            return parts[0];
        }
        return new List(parts, "list");
    }

    public INode ParseComment()
    {
        if (this.AtEnd() || this.Peek() != "#")
        {
            return null;
        }
        int start = this.Pos;
        while (!(this.AtEnd()) && this.Peek() != "\n")
        {
            this.Advance();
        }
        string text = ParableFunctions._Substring(this.Source, start, this.Pos);
        return new Comment(text, "comment");
    }

    public List<INode> Parse()
    {
        string source = this.Source.Trim(" \t\n\r".ToCharArray());
        if (!((!string.IsNullOrEmpty(source))))
        {
            return new List<INode> { new Empty("empty") };
        }
        List<INode> results = new List<INode>();
        while (true)
        {
            this.SkipWhitespace();
            while (!(this.AtEnd()) && this.Peek() == "\n")
            {
                this.Advance();
            }
            if (this.AtEnd())
            {
                break;
            }
            INode comment = this.ParseComment();
            if (!(comment != null))
            {
                break;
            }
        }
        while (!(this.AtEnd()))
        {
            INode result = this.ParseList(false);
            if (result != null)
            {
                results.Add(result);
            }
            this.SkipWhitespace();
            bool foundNewline = false;
            while (!(this.AtEnd()) && this.Peek() == "\n")
            {
                foundNewline = true;
                this.Advance();
                this._GatherHeredocBodies();
                if (this._CmdsubHeredocEnd != -1 && this._CmdsubHeredocEnd > this.Pos)
                {
                    this.Pos = this._CmdsubHeredocEnd;
                    this._CmdsubHeredocEnd = -1;
                }
                this.SkipWhitespace();
            }
            if (!(foundNewline) && !(this.AtEnd()))
            {
                throw new ParseError("Syntax error", this.Pos, 0);
            }
        }
        if (!((results.Count > 0)))
        {
            return new List<INode> { new Empty("empty") };
        }
        if (this._SawNewlineInSingleQuote && (!string.IsNullOrEmpty(this.Source)) && (this.Source[this.Source.Length - 1]).ToString() == "\\" && !(this.Source.Length >= 3 && this.Source.Substring(this.Source.Length - 3, (this.Source.Length - 1) - (this.Source.Length - 3)) == "\\\n"))
        {
            if (!(this._LastWordOnOwnLine(results)))
            {
                this._StripTrailingBackslashFromLastWord(results);
            }
        }
        return results;
    }

    public bool _LastWordOnOwnLine(List<INode> nodes)
    {
        return nodes.Count >= 2;
    }

    public void _StripTrailingBackslashFromLastWord(List<INode> nodes)
    {
        if (!((nodes.Count > 0)))
        {
            return;
        }
        INode lastNode = nodes[nodes.Count - 1];
        Word lastWord = this._FindLastWord(lastNode);
        if (lastWord != null && lastWord.Value.EndsWith("\\"))
        {
            lastWord.Value = ParableFunctions._Substring(lastWord.Value, 0, lastWord.Value.Length - 1);
            if (!((!string.IsNullOrEmpty(lastWord.Value))) && (lastNode is Command) && (((Command)lastNode).Words.Count > 0))
            {
                ((Func<Word, Word>)(_tmp => { ((Command)lastNode).Words.RemoveAt(((Command)lastNode).Words.Count - 1); return _tmp; }))(((Command)lastNode).Words[((Command)lastNode).Words.Count - 1]);
            }
        }
    }

    public Word _FindLastWord(INode node)
    {
        switch (node)
        {
            case Word nodeWord:
                return nodeWord;
        }
        switch (node)
        {
            case Command nodeCommand:
                if ((nodeCommand.Words.Count > 0))
                {
                    Word lastWord = nodeCommand.Words[nodeCommand.Words.Count - 1];
                    if (lastWord.Value.EndsWith("\\"))
                    {
                        return lastWord;
                    }
                }
                if ((nodeCommand.Redirects.Count > 0))
                {
                    INode lastRedirect = nodeCommand.Redirects[nodeCommand.Redirects.Count - 1];
                    switch (lastRedirect)
                    {
                        case Redirect lastRedirectRedirect:
                            return lastRedirectRedirect.Target;
                    }
                }
                if ((nodeCommand.Words.Count > 0))
                {
                    return nodeCommand.Words[nodeCommand.Words.Count - 1];
                }
                break;
        }
        switch (node)
        {
            case Pipeline nodePipeline:
                if ((nodePipeline.Commands.Count > 0))
                {
                    return this._FindLastWord(nodePipeline.Commands[nodePipeline.Commands.Count - 1]);
                }
                break;
        }
        switch (node)
        {
            case List nodeList:
                if ((nodeList.Parts.Count > 0))
                {
                    return this._FindLastWord(nodeList.Parts[nodeList.Parts.Count - 1]);
                }
                break;
        }
        return null;
    }
}

public static class ParableFunctions
{
    public static bool _IsHexDigit(string c)
    {
        return string.Compare(c, "0") >= 0 && string.Compare(c, "9") <= 0 || string.Compare(c, "a") >= 0 && string.Compare(c, "f") <= 0 || string.Compare(c, "A") >= 0 && string.Compare(c, "F") <= 0;
    }

    public static bool _IsOctalDigit(string c)
    {
        return string.Compare(c, "0") >= 0 && string.Compare(c, "7") <= 0;
    }

    public static int _GetAnsiEscape(string c)
    {
        return (Constants.ANSI_C_ESCAPES.TryGetValue(c, out var _v) ? _v : -1);
    }

    public static bool _IsWhitespace(string c)
    {
        return c == " " || c == "\t" || c == "\n";
    }

    public static List<byte> _StringToBytes(string s)
    {
        return new List<byte>(System.Text.Encoding.UTF8.GetBytes(s).ToList());
    }

    public static bool _IsWhitespaceNoNewline(string c)
    {
        return c == " " || c == "\t";
    }

    public static string _Substring(string s, int start, int end)
    {
        int len = s.Length;
        int clampedStart = Math.Max(0, Math.Min(start, len));
        int clampedEnd = Math.Max(clampedStart, Math.Min(end, len));
        return s.Substring(clampedStart, clampedEnd - clampedStart);
    }

    public static bool _StartsWithAt(string s, int pos, string prefix)
    {
        return (s.IndexOf(prefix, pos) == pos);
    }

    public static int _CountConsecutiveDollarsBefore(string s, int pos)
    {
        int count = 0;
        int k = pos - 1;
        while (k >= 0 && (s[k]).ToString() == "$")
        {
            int bsCount = 0;
            int j = k - 1;
            while (j >= 0 && (s[j]).ToString() == "\\")
            {
                bsCount += 1;
                j -= 1;
            }
            if (bsCount % 2 == 1)
            {
                break;
            }
            count += 1;
            k -= 1;
        }
        return count;
    }

    public static bool _IsExpansionStart(string s, int pos, string delimiter)
    {
        if (!(ParableFunctions._StartsWithAt(s, pos, delimiter)))
        {
            return false;
        }
        return ParableFunctions._CountConsecutiveDollarsBefore(s, pos) % 2 == 0;
    }

    public static List<INode> _Sublist(List<INode> lst, int start, int end)
    {
        return lst.GetRange(start, (end) - (start));
    }

    public static string _RepeatStr(string s, int n)
    {
        List<string> result = new List<string>();
        int i = 0;
        while (i < n)
        {
            result.Add(s);
            i += 1;
        }
        return string.Join("", result);
    }

    public static string _StripLineContinuationsCommentAware(string text)
    {
        List<string> result = new List<string>();
        int i = 0;
        bool inComment = false;
        QuoteState quote = ParableFunctions.NewQuoteState();
        while (i < text.Length)
        {
            string c = (text[i]).ToString();
            if (c == "\\" && i + 1 < text.Length && (text[i + 1]).ToString() == "\n")
            {
                int numPrecedingBackslashes = 0;
                int j = i - 1;
                while (j >= 0 && (text[j]).ToString() == "\\")
                {
                    numPrecedingBackslashes += 1;
                    j -= 1;
                }
                if (numPrecedingBackslashes % 2 == 0)
                {
                    if (inComment)
                    {
                        result.Add("\n");
                    }
                    i += 2;
                    inComment = false;
                    continue;
                }
            }
            if (c == "\n")
            {
                inComment = false;
                result.Add(c);
                i += 1;
                continue;
            }
            if (c == "'" && !(quote.Double) && !(inComment))
            {
                quote.Single = !(quote.Single);
            }
            else
            {
                if (c == "\"" && !(quote.Single) && !(inComment))
                {
                    quote.Double = !(quote.Double);
                }
                else
                {
                    if (c == "#" && !(quote.Single) && !(inComment))
                    {
                        inComment = true;
                    }
                }
            }
            result.Add(c);
            i += 1;
        }
        return string.Join("", result);
    }

    public static string _AppendRedirects(string @base, List<INode> redirects)
    {
        if ((redirects.Count > 0))
        {
            List<string> parts = new List<string>();
            foreach (INode r in redirects)
            {
                parts.Add(((INode)r).ToSexp());
            }
            return @base + " " + string.Join(" ", parts);
        }
        return @base;
    }

    public static string _FormatArithVal(string s)
    {
        Word w = new Word(s, new List<INode>(), "word");
        string val = w._ExpandAllAnsiCQuotes(s);
        val = w._StripLocaleStringDollars(val);
        val = w._FormatCommandSubstitutions(val, false);
        val = val.Replace("\\", "\\\\").Replace("\"", "\\\"");
        val = val.Replace("\n", "\\n").Replace("\t", "\\t");
        return val;
    }

    public static (int, List<string>) _ConsumeSingleQuote(string s, int start)
    {
        List<string> chars = new List<string> { "'" };
        int i = start + 1;
        while (i < s.Length && (s[i]).ToString() != "'")
        {
            chars.Add((s[i]).ToString());
            i += 1;
        }
        if (i < s.Length)
        {
            chars.Add((s[i]).ToString());
            i += 1;
        }
        return (i, chars);
    }

    public static (int, List<string>) _ConsumeDoubleQuote(string s, int start)
    {
        List<string> chars = new List<string> { "\"" };
        int i = start + 1;
        while (i < s.Length && (s[i]).ToString() != "\"")
        {
            if ((s[i]).ToString() == "\\" && i + 1 < s.Length)
            {
                chars.Add((s[i]).ToString());
                i += 1;
            }
            chars.Add((s[i]).ToString());
            i += 1;
        }
        if (i < s.Length)
        {
            chars.Add((s[i]).ToString());
            i += 1;
        }
        return (i, chars);
    }

    public static bool _HasBracketClose(string s, int start, int depth)
    {
        int i = start;
        while (i < s.Length)
        {
            if ((s[i]).ToString() == "]")
            {
                return true;
            }
            if (((s[i]).ToString() == "|" || (s[i]).ToString() == ")") && depth == 0)
            {
                return false;
            }
            i += 1;
        }
        return false;
    }

    public static (int, List<string>, bool) _ConsumeBracketClass(string s, int start, int depth)
    {
        int scanPos = start + 1;
        if (scanPos < s.Length && ((s[scanPos]).ToString() == "!" || (s[scanPos]).ToString() == "^"))
        {
            scanPos += 1;
        }
        if (scanPos < s.Length && (s[scanPos]).ToString() == "]")
        {
            if (ParableFunctions._HasBracketClose(s, scanPos + 1, depth))
            {
                scanPos += 1;
            }
        }
        bool isBracket = false;
        while (scanPos < s.Length)
        {
            if ((s[scanPos]).ToString() == "]")
            {
                isBracket = true;
                break;
            }
            if ((s[scanPos]).ToString() == ")" && depth == 0)
            {
                break;
            }
            if ((s[scanPos]).ToString() == "|" && depth == 0)
            {
                break;
            }
            scanPos += 1;
        }
        if (!(isBracket))
        {
            return (start + 1, new List<string> { "[" }, false);
        }
        List<string> chars = new List<string> { "[" };
        int i = start + 1;
        if (i < s.Length && ((s[i]).ToString() == "!" || (s[i]).ToString() == "^"))
        {
            chars.Add((s[i]).ToString());
            i += 1;
        }
        if (i < s.Length && (s[i]).ToString() == "]")
        {
            if (ParableFunctions._HasBracketClose(s, i + 1, depth))
            {
                chars.Add((s[i]).ToString());
                i += 1;
            }
        }
        while (i < s.Length && (s[i]).ToString() != "]")
        {
            chars.Add((s[i]).ToString());
            i += 1;
        }
        if (i < s.Length)
        {
            chars.Add((s[i]).ToString());
            i += 1;
        }
        return (i, chars, true);
    }

    public static string _FormatCondBody(INode node)
    {
        string kind = node.Kind;
        if (kind == "unary-test")
        {
            string operandVal = ((Word)((UnaryTest)node).Operand).GetCondFormattedValue();
            return ((UnaryTest)node).Op + " " + operandVal;
        }
        if (kind == "binary-test")
        {
            string leftVal = ((Word)((BinaryTest)node).Left).GetCondFormattedValue();
            string rightVal = ((Word)((BinaryTest)node).Right).GetCondFormattedValue();
            return leftVal + " " + ((BinaryTest)node).Op + " " + rightVal;
        }
        if (kind == "cond-and")
        {
            return ParableFunctions._FormatCondBody(((CondAnd)node).Left) + " && " + ParableFunctions._FormatCondBody(((CondAnd)node).Right);
        }
        if (kind == "cond-or")
        {
            return ParableFunctions._FormatCondBody(((CondOr)node).Left) + " || " + ParableFunctions._FormatCondBody(((CondOr)node).Right);
        }
        if (kind == "cond-not")
        {
            return "! " + ParableFunctions._FormatCondBody(((CondNot)node).Operand);
        }
        if (kind == "cond-paren")
        {
            return "( " + ParableFunctions._FormatCondBody(((CondParen)node).Inner) + " )";
        }
        return "";
    }

    public static bool _StartsWithSubshell(INode node)
    {
        switch (node)
        {
            case Subshell nodeSubshell:
                return true;
        }
        switch (node)
        {
            case List nodeList:
                foreach (INode p in nodeList.Parts)
                {
                    if (p.Kind != "operator")
                    {
                        return ParableFunctions._StartsWithSubshell(p);
                    }
                }
                return false;
        }
        switch (node)
        {
            case Pipeline nodePipeline:
                if ((nodePipeline.Commands.Count > 0))
                {
                    return ParableFunctions._StartsWithSubshell(nodePipeline.Commands[0]);
                }
                return false;
        }
        return false;
    }

    public static string _FormatCmdsubNode(INode node, int indent, bool inProcsub, bool compactRedirects, bool procsubFirst)
    {
        if (node == null)
        {
            return "";
        }
        string sp = ParableFunctions._RepeatStr(" ", indent);
        string innerSp = ParableFunctions._RepeatStr(" ", indent + 4);
        switch (node)
        {
            case ArithEmpty nodeArithEmpty:
                return "";
        }
        switch (node)
        {
            case Command nodeCommand:
                List<string> parts = new List<string>();
                foreach (Word w in nodeCommand.Words)
                {
                    string val = w._ExpandAllAnsiCQuotes(w.Value);
                    val = w._StripLocaleStringDollars(val);
                    val = w._NormalizeArrayWhitespace(val);
                    val = w._FormatCommandSubstitutions(val, false);
                    parts.Add(val);
                }
                List<HereDoc> heredocs = new List<HereDoc>();
                foreach (INode r in nodeCommand.Redirects)
                {
                    switch (r)
                    {
                        case HereDoc rHereDoc:
                            heredocs.Add(rHereDoc);
                            break;
                    }
                }
                foreach (INode r in nodeCommand.Redirects)
                {
                    parts.Add(ParableFunctions._FormatRedirect(r, compactRedirects, true));
                }
                string result = "";
                if (compactRedirects && (nodeCommand.Words.Count > 0) && (nodeCommand.Redirects.Count > 0))
                {
                    List<string> wordParts = parts.GetRange(0, nodeCommand.Words.Count);
                    List<string> redirectParts = parts.GetRange(nodeCommand.Words.Count, parts.Count - nodeCommand.Words.Count);
                    result = string.Join(" ", wordParts) + string.Join("", redirectParts);
                }
                else
                {
                    result = string.Join(" ", parts);
                }
                foreach (HereDoc h in heredocs)
                {
                    result = result + ParableFunctions._FormatHeredocBody(h);
                }
                return result;
        }
        switch (node)
        {
            case Pipeline nodePipeline:
                List<(INode, bool)> cmds = new List<(INode, bool)>();
                int i = 0;
                INode cmd = null;
                bool needsRedirect = false;
                while (i < nodePipeline.Commands.Count)
                {
                    cmd = nodePipeline.Commands[i];
                    switch (cmd)
                    {
                        case PipeBoth cmdPipeBoth:
                            i += 1;
                            continue;
                    }
                    needsRedirect = i + 1 < nodePipeline.Commands.Count && nodePipeline.Commands[i + 1].Kind == "pipe-both";
                    cmds.Add((cmd, needsRedirect));
                    i += 1;
                }
                List<string> resultParts = new List<string>();
                int idx = 0;
                while (idx < cmds.Count)
                {
                    {
                        (INode, bool) _entry = cmds[idx];
                        cmd = _entry.Item1;
                        needsRedirect = _entry.Item2;
                    }
                    string formatted = ParableFunctions._FormatCmdsubNode(cmd, indent, inProcsub, false, procsubFirst && idx == 0);
                    bool isLast = idx == cmds.Count - 1;
                    bool hasHeredoc = false;
                    if (cmd.Kind == "command" && (((Command)cmd).Redirects.Count > 0))
                    {
                        foreach (INode r in ((Command)cmd).Redirects)
                        {
                            bool _breakLoop6 = false;
                            switch (r)
                            {
                                case HereDoc rHereDoc:
                                    hasHeredoc = true;
                                    _breakLoop6 = true;
                                    break;
                            }
                            if (_breakLoop6) break;
                        }
                    }
                    int firstNl = 0;
                    if (needsRedirect)
                    {
                        if (hasHeredoc)
                        {
                            firstNl = formatted.IndexOf("\n");
                            if (firstNl != -1)
                            {
                                formatted = formatted.Substring(0, firstNl) + " 2>&1" + formatted.Substring(firstNl);
                            }
                            else
                            {
                                formatted = formatted + " 2>&1";
                            }
                        }
                        else
                        {
                            formatted = formatted + " 2>&1";
                        }
                    }
                    if (!(isLast) && hasHeredoc)
                    {
                        firstNl = formatted.IndexOf("\n");
                        if (firstNl != -1)
                        {
                            formatted = formatted.Substring(0, firstNl) + " |" + formatted.Substring(firstNl);
                        }
                        resultParts.Add(formatted);
                    }
                    else
                    {
                        resultParts.Add(formatted);
                    }
                    idx += 1;
                }
                bool compactPipe = inProcsub && (cmds.Count > 0) && cmds[0].Item1.Kind == "subshell";
                string result = "";
                idx = 0;
                while (idx < resultParts.Count)
                {
                    string part = resultParts[idx];
                    if (idx > 0)
                    {
                        if (result.EndsWith("\n"))
                        {
                            result = result + "  " + part;
                        }
                        else
                        {
                            if (compactPipe)
                            {
                                result = result + "|" + part;
                            }
                            else
                            {
                                result = result + " | " + part;
                            }
                        }
                    }
                    else
                    {
                        result = part;
                    }
                    idx += 1;
                }
                return result;
        }
        switch (node)
        {
            case List nodeList:
                bool hasHeredoc = false;
                foreach (INode p in nodeList.Parts)
                {
                    if (p.Kind == "command" && (((Command)p).Redirects.Count > 0))
                    {
                        foreach (INode r in ((Command)p).Redirects)
                        {
                            bool _breakLoop7 = false;
                            switch (r)
                            {
                                case HereDoc rHereDoc:
                                    hasHeredoc = true;
                                    _breakLoop7 = true;
                                    break;
                            }
                            if (_breakLoop7) break;
                        }
                    }
                    else
                    {
                        switch (p)
                        {
                            case Pipeline pPipeline:
                                foreach (INode cmd in pPipeline.Commands)
                                {
                                    if (cmd.Kind == "command" && (((Command)cmd).Redirects.Count > 0))
                                    {
                                        foreach (INode r in ((Command)cmd).Redirects)
                                        {
                                            bool _breakLoop8 = false;
                                            switch (r)
                                            {
                                                case HereDoc rHereDoc:
                                                    hasHeredoc = true;
                                                    _breakLoop8 = true;
                                                    break;
                                            }
                                            if (_breakLoop8) break;
                                        }
                                    }
                                    if (hasHeredoc)
                                    {
                                        break;
                                    }
                                }
                                break;
                        }
                    }
                }
                List<string> result = new List<string>();
                bool skippedSemi = false;
                int cmdCount = 0;
                foreach (INode p in nodeList.Parts)
                {
                    switch (p)
                    {
                        case Operator pOperator:
                            if (pOperator.Op == ";")
                            {
                                if ((result.Count > 0) && result[result.Count - 1].EndsWith("\n"))
                                {
                                    skippedSemi = true;
                                    continue;
                                }
                                if (result.Count >= 3 && result[result.Count - 2] == "\n" && result[result.Count - 3].EndsWith("\n"))
                                {
                                    skippedSemi = true;
                                    continue;
                                }
                                result.Add(";");
                                skippedSemi = false;
                            }
                            else
                            {
                                if (pOperator.Op == "\n")
                                {
                                    if ((result.Count > 0) && result[result.Count - 1] == ";")
                                    {
                                        skippedSemi = false;
                                        continue;
                                    }
                                    if ((result.Count > 0) && result[result.Count - 1].EndsWith("\n"))
                                    {
                                        result.Add((skippedSemi ? " " : "\n"));
                                        skippedSemi = false;
                                        continue;
                                    }
                                    result.Add("\n");
                                    skippedSemi = false;
                                }
                                else
                                {
                                    string last = "";
                                    int firstNl = 0;
                                    if (pOperator.Op == "&")
                                    {
                                        if ((result.Count > 0) && result[result.Count - 1].Contains("<<") && result[result.Count - 1].Contains("\n"))
                                        {
                                            last = result[result.Count - 1];
                                            if (last.Contains(" |") || last.StartsWith("|"))
                                            {
                                                result[result.Count - 1] = last + " &";
                                            }
                                            else
                                            {
                                                firstNl = last.IndexOf("\n");
                                                result[result.Count - 1] = last.Substring(0, firstNl) + " &" + last.Substring(firstNl);
                                            }
                                        }
                                        else
                                        {
                                            result.Add(" &");
                                        }
                                    }
                                    else
                                    {
                                        if ((result.Count > 0) && result[result.Count - 1].Contains("<<") && result[result.Count - 1].Contains("\n"))
                                        {
                                            last = result[result.Count - 1];
                                            firstNl = last.IndexOf("\n");
                                            result[result.Count - 1] = last.Substring(0, firstNl) + " " + pOperator.Op + " " + last.Substring(firstNl);
                                        }
                                        else
                                        {
                                            result.Add(" " + pOperator.Op);
                                        }
                                    }
                                }
                            }
                            break;
                        default:
                            if ((result.Count > 0) && !((result[result.Count - 1].EndsWith(" ") || result[result.Count - 1].EndsWith("\n"))))
                            {
                                result.Add(" ");
                            }
                            string formattedCmd = ParableFunctions._FormatCmdsubNode(p, indent, inProcsub, compactRedirects, procsubFirst && cmdCount == 0);
                            if (result.Count > 0)
                            {
                                string last = result[result.Count - 1];
                                if (last.Contains(" || \n") || last.Contains(" && \n"))
                                {
                                    formattedCmd = " " + formattedCmd;
                                }
                            }
                            if (skippedSemi)
                            {
                                formattedCmd = " " + formattedCmd;
                                skippedSemi = false;
                            }
                            result.Add(formattedCmd);
                            cmdCount += 1;
                            break;
                    }
                }
                string s = string.Join("", result);
                if (s.Contains(" &\n") && s.EndsWith("\n"))
                {
                    return s + " ";
                }
                while (s.EndsWith(";"))
                {
                    s = ParableFunctions._Substring(s, 0, s.Length - 1);
                }
                if (!(hasHeredoc))
                {
                    while (s.EndsWith("\n"))
                    {
                        s = ParableFunctions._Substring(s, 0, s.Length - 1);
                    }
                }
                return s;
        }
        switch (node)
        {
            case If nodeIf:
                string cond = ParableFunctions._FormatCmdsubNode(nodeIf.Condition, indent, false, false, false);
                string thenBody = ParableFunctions._FormatCmdsubNode(nodeIf.ThenBody, indent + 4, false, false, false);
                string result = "if " + cond + "; then\n" + innerSp + thenBody + ";";
                if (nodeIf.ElseBody != null)
                {
                    string elseBody = ParableFunctions._FormatCmdsubNode(nodeIf.ElseBody, indent + 4, false, false, false);
                    result = result + "\n" + sp + "else\n" + innerSp + elseBody + ";";
                }
                result = result + "\n" + sp + "fi";
                return result;
        }
        switch (node)
        {
            case While nodeWhile:
                string cond = ParableFunctions._FormatCmdsubNode(nodeWhile.Condition, indent, false, false, false);
                string body = ParableFunctions._FormatCmdsubNode(nodeWhile.Body, indent + 4, false, false, false);
                string result = "while " + cond + "; do\n" + innerSp + body + ";\n" + sp + "done";
                if ((nodeWhile.Redirects.Count > 0))
                {
                    foreach (INode r in nodeWhile.Redirects)
                    {
                        result = result + " " + ParableFunctions._FormatRedirect(r, false, false);
                    }
                }
                return result;
        }
        switch (node)
        {
            case Until nodeUntil:
                string cond = ParableFunctions._FormatCmdsubNode(nodeUntil.Condition, indent, false, false, false);
                string body = ParableFunctions._FormatCmdsubNode(nodeUntil.Body, indent + 4, false, false, false);
                string result = "until " + cond + "; do\n" + innerSp + body + ";\n" + sp + "done";
                if ((nodeUntil.Redirects.Count > 0))
                {
                    foreach (INode r in nodeUntil.Redirects)
                    {
                        result = result + " " + ParableFunctions._FormatRedirect(r, false, false);
                    }
                }
                return result;
        }
        switch (node)
        {
            case For nodeFor:
                string var = nodeFor.Var;
                string body = ParableFunctions._FormatCmdsubNode(nodeFor.Body, indent + 4, false, false, false);
                string result = "";
                if (nodeFor.Words != null)
                {
                    List<string> wordVals = new List<string>();
                    foreach (Word w in nodeFor.Words)
                    {
                        wordVals.Add(w.Value);
                    }
                    string words = string.Join(" ", wordVals);
                    if ((!string.IsNullOrEmpty(words)))
                    {
                        result = "for " + var + " in " + words + ";\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done";
                    }
                    else
                    {
                        result = "for " + var + " in ;\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done";
                    }
                }
                else
                {
                    result = "for " + var + " in \"$@\";\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done";
                }
                if ((nodeFor.Redirects.Count > 0))
                {
                    foreach (INode r in nodeFor.Redirects)
                    {
                        result = result + " " + ParableFunctions._FormatRedirect(r, false, false);
                    }
                }
                return result;
        }
        switch (node)
        {
            case ForArith nodeForArith:
                string body = ParableFunctions._FormatCmdsubNode(nodeForArith.Body, indent + 4, false, false, false);
                string result = "for ((" + nodeForArith.Init + "; " + nodeForArith.Cond + "; " + nodeForArith.Incr + "))\ndo\n" + innerSp + body + ";\n" + sp + "done";
                if ((nodeForArith.Redirects.Count > 0))
                {
                    foreach (INode r in nodeForArith.Redirects)
                    {
                        result = result + " " + ParableFunctions._FormatRedirect(r, false, false);
                    }
                }
                return result;
        }
        switch (node)
        {
            case Case nodeCase:
                string word = ((Word)nodeCase.Word).Value;
                List<string> patterns = new List<string>();
                int i = 0;
                while (i < nodeCase.Patterns.Count)
                {
                    INode p = nodeCase.Patterns[i];
                    object pat = ((CasePattern)p).Pattern.Replace("|", " | ");
                    string body = "";
                    if (((CasePattern)p).Body != null)
                    {
                        body = ParableFunctions._FormatCmdsubNode(((CasePattern)p).Body, indent + 8, false, false, false);
                    }
                    else
                    {
                        body = "";
                    }
                    string term = ((CasePattern)p).Terminator;
                    string patIndent = ParableFunctions._RepeatStr(" ", indent + 8);
                    string termIndent = ParableFunctions._RepeatStr(" ", indent + 4);
                    string bodyPart = ((!string.IsNullOrEmpty(body)) ? patIndent + body + "\n" : "\n");
                    if (i == 0)
                    {
                        patterns.Add(" " + pat + ")\n" + bodyPart + termIndent + term);
                    }
                    else
                    {
                        patterns.Add(pat + ")\n" + bodyPart + termIndent + term);
                    }
                    i += 1;
                }
                object patternStr = string.Join("\n" + ParableFunctions._RepeatStr(" ", indent + 4), patterns);
                string redirects = "";
                if ((nodeCase.Redirects.Count > 0))
                {
                    List<string> redirectParts = new List<string>();
                    foreach (INode r in nodeCase.Redirects)
                    {
                        redirectParts.Add(ParableFunctions._FormatRedirect(r, false, false));
                    }
                    redirects = " " + string.Join(" ", redirectParts);
                }
                return "case " + word + " in" + patternStr + "\n" + sp + "esac" + redirects;
        }
        switch (node)
        {
            case Function nodeFunction:
                string name = nodeFunction.Name;
                INode innerBody = (nodeFunction.Body.Kind == "brace-group" ? ((BraceGroup)nodeFunction.Body).Body : nodeFunction.Body);
                string body = ParableFunctions._FormatCmdsubNode(innerBody, indent + 4, false, false, false).TrimEnd(";".ToCharArray());
                return string.Format("function {0} () \n{{ \n{1}{2}\n}}", name, innerSp, body);
        }
        switch (node)
        {
            case Subshell nodeSubshell:
                string body = ParableFunctions._FormatCmdsubNode(nodeSubshell.Body, indent, inProcsub, compactRedirects, false);
                string redirects = "";
                if ((nodeSubshell.Redirects.Count > 0))
                {
                    List<string> redirectParts = new List<string>();
                    foreach (INode r in nodeSubshell.Redirects)
                    {
                        redirectParts.Add(ParableFunctions._FormatRedirect(r, false, false));
                    }
                    redirects = string.Join(" ", redirectParts);
                }
                if (procsubFirst)
                {
                    if ((!string.IsNullOrEmpty(redirects)))
                    {
                        return "(" + body + ") " + redirects;
                    }
                    return "(" + body + ")";
                }
                if ((!string.IsNullOrEmpty(redirects)))
                {
                    return "( " + body + " ) " + redirects;
                }
                return "( " + body + " )";
        }
        switch (node)
        {
            case BraceGroup nodeBraceGroup:
                string body = ParableFunctions._FormatCmdsubNode(nodeBraceGroup.Body, indent, false, false, false);
                body = body.TrimEnd(";".ToCharArray());
                string terminator = (body.EndsWith(" &") ? " }" : "; }");
                string redirects = "";
                if ((nodeBraceGroup.Redirects.Count > 0))
                {
                    List<string> redirectParts = new List<string>();
                    foreach (INode r in nodeBraceGroup.Redirects)
                    {
                        redirectParts.Add(ParableFunctions._FormatRedirect(r, false, false));
                    }
                    redirects = string.Join(" ", redirectParts);
                }
                if ((!string.IsNullOrEmpty(redirects)))
                {
                    return "{ " + body + terminator + " " + redirects;
                }
                return "{ " + body + terminator;
        }
        switch (node)
        {
            case ArithmeticCommand nodeArithmeticCommand:
                return "((" + nodeArithmeticCommand.RawContent + "))";
        }
        switch (node)
        {
            case ConditionalExpr nodeConditionalExpr:
                string body = ParableFunctions._FormatCondBody(((INode)nodeConditionalExpr.Body));
                return "[[ " + body + " ]]";
        }
        switch (node)
        {
            case Negation nodeNegation:
                if (nodeNegation.Pipeline != null)
                {
                    return "! " + ParableFunctions._FormatCmdsubNode(nodeNegation.Pipeline, indent, false, false, false);
                }
                return "! ";
        }
        switch (node)
        {
            case Time nodeTime:
                string prefix = (nodeTime.Posix ? "time -p " : "time ");
                if (nodeTime.Pipeline != null)
                {
                    return prefix + ParableFunctions._FormatCmdsubNode(nodeTime.Pipeline, indent, false, false, false);
                }
                return prefix;
        }
        return "";
    }

    public static string _FormatRedirect(INode r, bool compact, bool heredocOpOnly)
    {
        string op = "";
        switch (r)
        {
            case HereDoc rHereDoc:
                if (rHereDoc.StripTabs)
                {
                    op = "<<-";
                }
                else
                {
                    op = "<<";
                }
                if (rHereDoc.Fd != null && rHereDoc.Fd > 0)
                {
                    op = rHereDoc.Fd.ToString() + op;
                }
                string delim = "";
                if (rHereDoc.Quoted)
                {
                    delim = "'" + rHereDoc.Delimiter + "'";
                }
                else
                {
                    delim = rHereDoc.Delimiter;
                }
                if (heredocOpOnly)
                {
                    return op + delim;
                }
                return op + delim + "\n" + rHereDoc.Content + rHereDoc.Delimiter + "\n";
        }
        op = ((Redirect)r).Op;
        if (op == "1>")
        {
            op = ">";
        }
        else
        {
            if (op == "0<")
            {
                op = "<";
            }
        }
        string target = ((Redirect)r).Target.Value;
        target = ((Redirect)r).Target._ExpandAllAnsiCQuotes(target);
        target = ((Redirect)r).Target._StripLocaleStringDollars(target);
        target = ((Redirect)r).Target._FormatCommandSubstitutions(target, false);
        if (target.StartsWith("&"))
        {
            bool wasInputClose = false;
            if (target == "&-" && op.EndsWith("<"))
            {
                wasInputClose = true;
                op = ParableFunctions._Substring(op, 0, op.Length - 1) + ">";
            }
            string afterAmp = ParableFunctions._Substring(target, 1, target.Length);
            bool isLiteralFd = afterAmp == "-" || afterAmp.Length > 0 && ((afterAmp[0]).ToString().Length > 0 && (afterAmp[0]).ToString().All(char.IsDigit));
            if (isLiteralFd)
            {
                if (op == ">" || op == ">&")
                {
                    op = (wasInputClose ? "0>" : "1>");
                }
                else
                {
                    if (op == "<" || op == "<&")
                    {
                        op = "0<";
                    }
                }
            }
            else
            {
                if (op == "1>")
                {
                    op = ">";
                }
                else
                {
                    if (op == "0<")
                    {
                        op = "<";
                    }
                }
            }
            return op + target;
        }
        if (op.EndsWith("&"))
        {
            return op + target;
        }
        if (compact)
        {
            return op + target;
        }
        return op + " " + target;
    }

    public static string _FormatHeredocBody(INode r)
    {
        return "\n" + ((HereDoc)r).Content + ((HereDoc)r).Delimiter + "\n";
    }

    public static bool _LookaheadForEsac(string value, int start, int caseDepth)
    {
        int i = start;
        int depth = caseDepth;
        QuoteState quote = ParableFunctions.NewQuoteState();
        while (i < value.Length)
        {
            string c = (value[i]).ToString();
            if (c == "\\" && i + 1 < value.Length && quote.Double)
            {
                i += 2;
                continue;
            }
            if (c == "'" && !(quote.Double))
            {
                quote.Single = !(quote.Single);
                i += 1;
                continue;
            }
            if (c == "\"" && !(quote.Single))
            {
                quote.Double = !(quote.Double);
                i += 1;
                continue;
            }
            if (quote.Single || quote.Double)
            {
                i += 1;
                continue;
            }
            if (ParableFunctions._StartsWithAt(value, i, "case") && ParableFunctions._IsWordBoundary(value, i, 4))
            {
                depth += 1;
                i += 4;
            }
            else
            {
                if (ParableFunctions._StartsWithAt(value, i, "esac") && ParableFunctions._IsWordBoundary(value, i, 4))
                {
                    depth -= 1;
                    if (depth == 0)
                    {
                        return true;
                    }
                    i += 4;
                }
                else
                {
                    if (c == "(")
                    {
                        i += 1;
                    }
                    else
                    {
                        if (c == ")")
                        {
                            if (depth > 0)
                            {
                                i += 1;
                            }
                            else
                            {
                                break;
                            }
                        }
                        else
                        {
                            i += 1;
                        }
                    }
                }
            }
        }
        return false;
    }

    public static int _SkipBacktick(string value, int start)
    {
        int i = start + 1;
        while (i < value.Length && (value[i]).ToString() != "`")
        {
            if ((value[i]).ToString() == "\\" && i + 1 < value.Length)
            {
                i += 2;
            }
            else
            {
                i += 1;
            }
        }
        if (i < value.Length)
        {
            i += 1;
        }
        return i;
    }

    public static int _SkipSingleQuoted(string s, int start)
    {
        int i = start;
        while (i < s.Length && (s[i]).ToString() != "'")
        {
            i += 1;
        }
        return (i < s.Length ? i + 1 : i);
    }

    public static int _SkipDoubleQuoted(string s, int start)
    {
        int i = start;
        int n = s.Length;
        bool passNext = false;
        bool backq = false;
        while (i < n)
        {
            string c = (s[i]).ToString();
            if (passNext)
            {
                passNext = false;
                i += 1;
                continue;
            }
            if (c == "\\")
            {
                passNext = true;
                i += 1;
                continue;
            }
            if (backq)
            {
                if (c == "`")
                {
                    backq = false;
                }
                i += 1;
                continue;
            }
            if (c == "`")
            {
                backq = true;
                i += 1;
                continue;
            }
            if (c == "$" && i + 1 < n)
            {
                if ((s[i + 1]).ToString() == "(")
                {
                    i = ParableFunctions._FindCmdsubEnd(s, i + 2);
                    continue;
                }
                if ((s[i + 1]).ToString() == "{")
                {
                    i = ParableFunctions._FindBracedParamEnd(s, i + 2);
                    continue;
                }
            }
            if (c == "\"")
            {
                return i + 1;
            }
            i += 1;
        }
        return i;
    }

    public static bool _IsValidArithmeticStart(string value, int start)
    {
        int scanParen = 0;
        int scanI = start + 3;
        while (scanI < value.Length)
        {
            string scanC = (value[scanI]).ToString();
            if (ParableFunctions._IsExpansionStart(value, scanI, "$("))
            {
                scanI = ParableFunctions._FindCmdsubEnd(value, scanI + 2);
                continue;
            }
            if (scanC == "(")
            {
                scanParen += 1;
            }
            else
            {
                if (scanC == ")")
                {
                    if (scanParen > 0)
                    {
                        scanParen -= 1;
                    }
                    else
                    {
                        if (scanI + 1 < value.Length && (value[scanI + 1]).ToString() == ")")
                        {
                            return true;
                        }
                        else
                        {
                            return false;
                        }
                    }
                }
            }
            scanI += 1;
        }
        return false;
    }

    public static int _FindFunsubEnd(string value, int start)
    {
        int depth = 1;
        int i = start;
        QuoteState quote = ParableFunctions.NewQuoteState();
        while (i < value.Length && depth > 0)
        {
            string c = (value[i]).ToString();
            if (c == "\\" && i + 1 < value.Length && !(quote.Single))
            {
                i += 2;
                continue;
            }
            if (c == "'" && !(quote.Double))
            {
                quote.Single = !(quote.Single);
                i += 1;
                continue;
            }
            if (c == "\"" && !(quote.Single))
            {
                quote.Double = !(quote.Double);
                i += 1;
                continue;
            }
            if (quote.Single || quote.Double)
            {
                i += 1;
                continue;
            }
            if (c == "{")
            {
                depth += 1;
            }
            else
            {
                if (c == "}")
                {
                    depth -= 1;
                    if (depth == 0)
                    {
                        return i + 1;
                    }
                }
            }
            i += 1;
        }
        return value.Length;
    }

    public static int _FindCmdsubEnd(string value, int start)
    {
        int depth = 1;
        int i = start;
        int caseDepth = 0;
        bool inCasePatterns = false;
        int arithDepth = 0;
        int arithParenDepth = 0;
        while (i < value.Length && depth > 0)
        {
            string c = (value[i]).ToString();
            if (c == "\\" && i + 1 < value.Length)
            {
                i += 2;
                continue;
            }
            if (c == "'")
            {
                i = ParableFunctions._SkipSingleQuoted(value, i + 1);
                continue;
            }
            if (c == "\"")
            {
                i = ParableFunctions._SkipDoubleQuoted(value, i + 1);
                continue;
            }
            if (c == "#" && arithDepth == 0 && (i == start || (value[i - 1]).ToString() == " " || (value[i - 1]).ToString() == "\t" || (value[i - 1]).ToString() == "\n" || (value[i - 1]).ToString() == ";" || (value[i - 1]).ToString() == "|" || (value[i - 1]).ToString() == "&" || (value[i - 1]).ToString() == "(" || (value[i - 1]).ToString() == ")"))
            {
                while (i < value.Length && (value[i]).ToString() != "\n")
                {
                    i += 1;
                }
                continue;
            }
            if (ParableFunctions._StartsWithAt(value, i, "<<<"))
            {
                i += 3;
                while (i < value.Length && ((value[i]).ToString() == " " || (value[i]).ToString() == "\t"))
                {
                    i += 1;
                }
                if (i < value.Length && (value[i]).ToString() == "\"")
                {
                    i += 1;
                    while (i < value.Length && (value[i]).ToString() != "\"")
                    {
                        if ((value[i]).ToString() == "\\" && i + 1 < value.Length)
                        {
                            i += 2;
                        }
                        else
                        {
                            i += 1;
                        }
                    }
                    if (i < value.Length)
                    {
                        i += 1;
                    }
                }
                else
                {
                    if (i < value.Length && (value[i]).ToString() == "'")
                    {
                        i += 1;
                        while (i < value.Length && (value[i]).ToString() != "'")
                        {
                            i += 1;
                        }
                        if (i < value.Length)
                        {
                            i += 1;
                        }
                    }
                    else
                    {
                        while (i < value.Length && !" \t\n;|&<>()".Contains((value[i]).ToString()))
                        {
                            i += 1;
                        }
                    }
                }
                continue;
            }
            if (ParableFunctions._IsExpansionStart(value, i, "$(("))
            {
                if (ParableFunctions._IsValidArithmeticStart(value, i))
                {
                    arithDepth += 1;
                    i += 3;
                    continue;
                }
                int j = ParableFunctions._FindCmdsubEnd(value, i + 2);
                i = j;
                continue;
            }
            if (arithDepth > 0 && arithParenDepth == 0 && ParableFunctions._StartsWithAt(value, i, "))"))
            {
                arithDepth -= 1;
                i += 2;
                continue;
            }
            if (c == "`")
            {
                i = ParableFunctions._SkipBacktick(value, i);
                continue;
            }
            if (arithDepth == 0 && ParableFunctions._StartsWithAt(value, i, "<<"))
            {
                i = ParableFunctions._SkipHeredoc(value, i);
                continue;
            }
            if (ParableFunctions._StartsWithAt(value, i, "case") && ParableFunctions._IsWordBoundary(value, i, 4))
            {
                caseDepth += 1;
                inCasePatterns = false;
                i += 4;
                continue;
            }
            if (caseDepth > 0 && ParableFunctions._StartsWithAt(value, i, "in") && ParableFunctions._IsWordBoundary(value, i, 2))
            {
                inCasePatterns = true;
                i += 2;
                continue;
            }
            if (ParableFunctions._StartsWithAt(value, i, "esac") && ParableFunctions._IsWordBoundary(value, i, 4))
            {
                if (caseDepth > 0)
                {
                    caseDepth -= 1;
                    inCasePatterns = false;
                }
                i += 4;
                continue;
            }
            if (ParableFunctions._StartsWithAt(value, i, ";;"))
            {
                i += 2;
                continue;
            }
            if (c == "(")
            {
                if (!(inCasePatterns && caseDepth > 0))
                {
                    if (arithDepth > 0)
                    {
                        arithParenDepth += 1;
                    }
                    else
                    {
                        depth += 1;
                    }
                }
            }
            else
            {
                if (c == ")")
                {
                    if (inCasePatterns && caseDepth > 0)
                    {
                        if (!(ParableFunctions._LookaheadForEsac(value, i + 1, caseDepth)))
                        {
                            depth -= 1;
                        }
                    }
                    else
                    {
                        if (arithDepth > 0)
                        {
                            if (arithParenDepth > 0)
                            {
                                arithParenDepth -= 1;
                            }
                        }
                        else
                        {
                            depth -= 1;
                        }
                    }
                }
            }
            i += 1;
        }
        return i;
    }

    public static int _FindBracedParamEnd(string value, int start)
    {
        int depth = 1;
        int i = start;
        bool inDouble = false;
        int dolbraceState = Constants.DOLBRACESTATE_PARAM;
        while (i < value.Length && depth > 0)
        {
            string c = (value[i]).ToString();
            if (c == "\\" && i + 1 < value.Length)
            {
                i += 2;
                continue;
            }
            if (c == "'" && dolbraceState == Constants.DOLBRACESTATE_QUOTE && !(inDouble))
            {
                i = ParableFunctions._SkipSingleQuoted(value, i + 1);
                continue;
            }
            if (c == "\"")
            {
                inDouble = !(inDouble);
                i += 1;
                continue;
            }
            if (inDouble)
            {
                i += 1;
                continue;
            }
            if (dolbraceState == Constants.DOLBRACESTATE_PARAM && "%#^,".Contains(c))
            {
                dolbraceState = Constants.DOLBRACESTATE_QUOTE;
            }
            else
            {
                if (dolbraceState == Constants.DOLBRACESTATE_PARAM && ":-=?+/".Contains(c))
                {
                    dolbraceState = Constants.DOLBRACESTATE_WORD;
                }
            }
            if (c == "[" && dolbraceState == Constants.DOLBRACESTATE_PARAM && !(inDouble))
            {
                int end = ParableFunctions._SkipSubscript(value, i, 0);
                if (end != -1)
                {
                    i = end;
                    continue;
                }
            }
            if ((c == "<" || c == ">") && i + 1 < value.Length && (value[i + 1]).ToString() == "(")
            {
                i = ParableFunctions._FindCmdsubEnd(value, i + 2);
                continue;
            }
            if (c == "{")
            {
                depth += 1;
            }
            else
            {
                if (c == "}")
                {
                    depth -= 1;
                    if (depth == 0)
                    {
                        return i + 1;
                    }
                }
            }
            if (ParableFunctions._IsExpansionStart(value, i, "$("))
            {
                i = ParableFunctions._FindCmdsubEnd(value, i + 2);
                continue;
            }
            if (ParableFunctions._IsExpansionStart(value, i, "${"))
            {
                i = ParableFunctions._FindBracedParamEnd(value, i + 2);
                continue;
            }
            i += 1;
        }
        return i;
    }

    public static int _SkipHeredoc(string value, int start)
    {
        int i = start + 2;
        if (i < value.Length && (value[i]).ToString() == "-")
        {
            i += 1;
        }
        while (i < value.Length && ParableFunctions._IsWhitespaceNoNewline((value[i]).ToString()))
        {
            i += 1;
        }
        int delimStart = i;
        object quoteChar = null;
        string delimiter = "";
        if (i < value.Length && ((value[i]).ToString() == "\"" || (value[i]).ToString() == "'"))
        {
            quoteChar = (value[i]).ToString();
            i += 1;
            delimStart = i;
            while (i < value.Length && (value[i]).ToString() != (string)quoteChar)
            {
                i += 1;
            }
            delimiter = ParableFunctions._Substring(value, delimStart, i);
            if (i < value.Length)
            {
                i += 1;
            }
        }
        else
        {
            if (i < value.Length && (value[i]).ToString() == "\\")
            {
                i += 1;
                delimStart = i;
                if (i < value.Length)
                {
                    i += 1;
                }
                while (i < value.Length && !(ParableFunctions._IsMetachar((value[i]).ToString())))
                {
                    i += 1;
                }
                delimiter = ParableFunctions._Substring(value, delimStart, i);
            }
            else
            {
                while (i < value.Length && !(ParableFunctions._IsMetachar((value[i]).ToString())))
                {
                    i += 1;
                }
                delimiter = ParableFunctions._Substring(value, delimStart, i);
            }
        }
        int parenDepth = 0;
        QuoteState quote = ParableFunctions.NewQuoteState();
        bool inBacktick = false;
        while (i < value.Length && (value[i]).ToString() != "\n")
        {
            string c = (value[i]).ToString();
            if (c == "\\" && i + 1 < value.Length && (quote.Double || inBacktick))
            {
                i += 2;
                continue;
            }
            if (c == "'" && !(quote.Double) && !(inBacktick))
            {
                quote.Single = !(quote.Single);
                i += 1;
                continue;
            }
            if (c == "\"" && !(quote.Single) && !(inBacktick))
            {
                quote.Double = !(quote.Double);
                i += 1;
                continue;
            }
            if (c == "`" && !(quote.Single))
            {
                inBacktick = !(inBacktick);
                i += 1;
                continue;
            }
            if (quote.Single || quote.Double || inBacktick)
            {
                i += 1;
                continue;
            }
            if (c == "(")
            {
                parenDepth += 1;
            }
            else
            {
                if (c == ")")
                {
                    if (parenDepth == 0)
                    {
                        break;
                    }
                    parenDepth -= 1;
                }
            }
            i += 1;
        }
        if (i < value.Length && (value[i]).ToString() == ")")
        {
            return i;
        }
        if (i < value.Length && (value[i]).ToString() == "\n")
        {
            i += 1;
        }
        while (i < value.Length)
        {
            int lineStart = i;
            int lineEnd = i;
            while (lineEnd < value.Length && (value[lineEnd]).ToString() != "\n")
            {
                lineEnd += 1;
            }
            string line = ParableFunctions._Substring(value, lineStart, lineEnd);
            while (lineEnd < value.Length)
            {
                int trailingBs = 0;
                for (int j = line.Length - 1; j > -1; j += -1)
                {
                    if ((line[j]).ToString() == "\\")
                    {
                        trailingBs += 1;
                    }
                    else
                    {
                        break;
                    }
                }
                if (trailingBs % 2 == 0)
                {
                    break;
                }
                line = line.Substring(0, line.Length - 1);
                lineEnd += 1;
                int nextLineStart = lineEnd;
                while (lineEnd < value.Length && (value[lineEnd]).ToString() != "\n")
                {
                    lineEnd += 1;
                }
                line = line + ParableFunctions._Substring(value, nextLineStart, lineEnd);
            }
            string stripped = "";
            if (start + 2 < value.Length && (value[start + 2]).ToString() == "-")
            {
                stripped = line.TrimStart("\t".ToCharArray());
            }
            else
            {
                stripped = line;
            }
            if (stripped == delimiter)
            {
                if (lineEnd < value.Length)
                {
                    return lineEnd + 1;
                }
                else
                {
                    return lineEnd;
                }
            }
            if (stripped.StartsWith(delimiter) && stripped.Length > delimiter.Length)
            {
                int tabsStripped = line.Length - stripped.Length;
                return lineStart + tabsStripped + delimiter.Length;
            }
            if (lineEnd < value.Length)
            {
                i = lineEnd + 1;
            }
            else
            {
                i = lineEnd;
            }
        }
        return i;
    }

    public static (int, int) _FindHeredocContentEnd(string source, int start, List<(string, bool)> delimiters)
    {
        if (!((delimiters.Count > 0)))
        {
            return (start, start);
        }
        int pos = start;
        while (pos < source.Length && (source[pos]).ToString() != "\n")
        {
            pos += 1;
        }
        if (pos >= source.Length)
        {
            return (start, start);
        }
        int contentStart = pos;
        pos += 1;
        foreach ((string, bool) _item in delimiters)
        {
            string delimiter = _item.Item1;
            bool stripTabs = _item.Item2;
            while (pos < source.Length)
            {
                int lineStart = pos;
                int lineEnd = pos;
                while (lineEnd < source.Length && (source[lineEnd]).ToString() != "\n")
                {
                    lineEnd += 1;
                }
                string line = ParableFunctions._Substring(source, lineStart, lineEnd);
                while (lineEnd < source.Length)
                {
                    int trailingBs = 0;
                    for (int j = line.Length - 1; j > -1; j += -1)
                    {
                        if ((line[j]).ToString() == "\\")
                        {
                            trailingBs += 1;
                        }
                        else
                        {
                            break;
                        }
                    }
                    if (trailingBs % 2 == 0)
                    {
                        break;
                    }
                    line = line.Substring(0, line.Length - 1);
                    lineEnd += 1;
                    int nextLineStart = lineEnd;
                    while (lineEnd < source.Length && (source[lineEnd]).ToString() != "\n")
                    {
                        lineEnd += 1;
                    }
                    line = line + ParableFunctions._Substring(source, nextLineStart, lineEnd);
                }
                string lineStripped = "";
                if (stripTabs)
                {
                    lineStripped = line.TrimStart("\t".ToCharArray());
                }
                else
                {
                    lineStripped = line;
                }
                if (lineStripped == delimiter)
                {
                    pos = (lineEnd < source.Length ? lineEnd + 1 : lineEnd);
                    break;
                }
                if (lineStripped.StartsWith(delimiter) && lineStripped.Length > delimiter.Length)
                {
                    int tabsStripped = line.Length - lineStripped.Length;
                    pos = lineStart + tabsStripped + delimiter.Length;
                    break;
                }
                pos = (lineEnd < source.Length ? lineEnd + 1 : lineEnd);
            }
        }
        return (contentStart, pos);
    }

    public static bool _IsWordBoundary(string s, int pos, int wordLen)
    {
        if (pos > 0)
        {
            string prev = (s[pos - 1]).ToString();
            if ((prev.Length > 0 && prev.All(char.IsLetterOrDigit)) || prev == "_")
            {
                return false;
            }
            if ("{}!".Contains(prev))
            {
                return false;
            }
        }
        int end = pos + wordLen;
        if (end < s.Length && (((s[end]).ToString().Length > 0 && (s[end]).ToString().All(char.IsLetterOrDigit)) || (s[end]).ToString() == "_"))
        {
            return false;
        }
        return true;
    }

    public static bool _IsQuote(string c)
    {
        return c == "'" || c == "\"";
    }

    public static string _CollapseWhitespace(string s)
    {
        List<string> result = new List<string>();
        bool prevWasWs = false;
        foreach (var _c7 in s)
        {
            var c = _c7.ToString();
            if (c == " " || c == "\t")
            {
                if (!(prevWasWs))
                {
                    result.Add(" ");
                }
                prevWasWs = true;
            }
            else
            {
                result.Add(c);
                prevWasWs = false;
            }
        }
        string joined = string.Join("", result);
        return joined.Trim(" \t".ToCharArray());
    }

    public static int _CountTrailingBackslashes(string s)
    {
        int count = 0;
        for (int i = s.Length - 1; i > -1; i += -1)
        {
            if ((s[i]).ToString() == "\\")
            {
                count += 1;
            }
            else
            {
                break;
            }
        }
        return count;
    }

    public static string _NormalizeHeredocDelimiter(string delimiter)
    {
        List<string> result = new List<string>();
        int i = 0;
        while (i < delimiter.Length)
        {
            int depth = 0;
            List<string> inner = new List<string>();
            string innerStr = "";
            if (i + 1 < delimiter.Length && delimiter.Substring(i, (i + 2) - (i)) == "$(")
            {
                result.Add("$(");
                i += 2;
                depth = 1;
                inner = new List<string>();
                while (i < delimiter.Length && depth > 0)
                {
                    if ((delimiter[i]).ToString() == "(")
                    {
                        depth += 1;
                        inner.Add((delimiter[i]).ToString());
                    }
                    else
                    {
                        if ((delimiter[i]).ToString() == ")")
                        {
                            depth -= 1;
                            if (depth == 0)
                            {
                                innerStr = string.Join("", inner);
                                innerStr = ParableFunctions._CollapseWhitespace(innerStr);
                                result.Add(innerStr);
                                result.Add(")");
                            }
                            else
                            {
                                inner.Add((delimiter[i]).ToString());
                            }
                        }
                        else
                        {
                            inner.Add((delimiter[i]).ToString());
                        }
                    }
                    i += 1;
                }
            }
            else
            {
                if (i + 1 < delimiter.Length && delimiter.Substring(i, (i + 2) - (i)) == "${")
                {
                    result.Add("${");
                    i += 2;
                    depth = 1;
                    inner = new List<string>();
                    while (i < delimiter.Length && depth > 0)
                    {
                        if ((delimiter[i]).ToString() == "{")
                        {
                            depth += 1;
                            inner.Add((delimiter[i]).ToString());
                        }
                        else
                        {
                            if ((delimiter[i]).ToString() == "}")
                            {
                                depth -= 1;
                                if (depth == 0)
                                {
                                    innerStr = string.Join("", inner);
                                    innerStr = ParableFunctions._CollapseWhitespace(innerStr);
                                    result.Add(innerStr);
                                    result.Add("}");
                                }
                                else
                                {
                                    inner.Add((delimiter[i]).ToString());
                                }
                            }
                            else
                            {
                                inner.Add((delimiter[i]).ToString());
                            }
                        }
                        i += 1;
                    }
                }
                else
                {
                    if (i + 1 < delimiter.Length && "<>".Contains((delimiter[i]).ToString()) && (delimiter[i + 1]).ToString() == "(")
                    {
                        result.Add((delimiter[i]).ToString());
                        result.Add("(");
                        i += 2;
                        depth = 1;
                        inner = new List<string>();
                        while (i < delimiter.Length && depth > 0)
                        {
                            if ((delimiter[i]).ToString() == "(")
                            {
                                depth += 1;
                                inner.Add((delimiter[i]).ToString());
                            }
                            else
                            {
                                if ((delimiter[i]).ToString() == ")")
                                {
                                    depth -= 1;
                                    if (depth == 0)
                                    {
                                        innerStr = string.Join("", inner);
                                        innerStr = ParableFunctions._CollapseWhitespace(innerStr);
                                        result.Add(innerStr);
                                        result.Add(")");
                                    }
                                    else
                                    {
                                        inner.Add((delimiter[i]).ToString());
                                    }
                                }
                                else
                                {
                                    inner.Add((delimiter[i]).ToString());
                                }
                            }
                            i += 1;
                        }
                    }
                    else
                    {
                        result.Add((delimiter[i]).ToString());
                        i += 1;
                    }
                }
            }
        }
        return string.Join("", result);
    }

    public static bool _IsMetachar(string c)
    {
        return c == " " || c == "\t" || c == "\n" || c == "|" || c == "&" || c == ";" || c == "(" || c == ")" || c == "<" || c == ">";
    }

    public static bool _IsFunsubChar(string c)
    {
        return c == " " || c == "\t" || c == "\n" || c == "|";
    }

    public static bool _IsExtglobPrefix(string c)
    {
        return c == "@" || c == "?" || c == "*" || c == "+" || c == "!";
    }

    public static bool _IsRedirectChar(string c)
    {
        return c == "<" || c == ">";
    }

    public static bool _IsSpecialParam(string c)
    {
        return c == "?" || c == "$" || c == "!" || c == "#" || c == "@" || c == "*" || c == "-" || c == "&";
    }

    public static bool _IsSpecialParamUnbraced(string c)
    {
        return c == "?" || c == "$" || c == "!" || c == "#" || c == "@" || c == "*" || c == "-";
    }

    public static bool _IsDigit(string c)
    {
        return string.Compare(c, "0") >= 0 && string.Compare(c, "9") <= 0;
    }

    public static bool _IsSemicolonOrNewline(string c)
    {
        return c == ";" || c == "\n";
    }

    public static bool _IsWordEndContext(string c)
    {
        return c == " " || c == "\t" || c == "\n" || c == ";" || c == "|" || c == "&" || c == "<" || c == ">" || c == "(" || c == ")";
    }

    public static int _SkipMatchedPair(string s, int start, string open, string close, int flags)
    {
        int n = s.Length;
        int i = 0;
        if (((flags & Constants.SMP_PAST_OPEN) != 0))
        {
            i = start;
        }
        else
        {
            if (start >= n || (s[start]).ToString() != open)
            {
                return -1;
            }
            i = start + 1;
        }
        int depth = 1;
        bool passNext = false;
        bool backq = false;
        while (i < n && depth > 0)
        {
            string c = (s[i]).ToString();
            if (passNext)
            {
                passNext = false;
                i += 1;
                continue;
            }
            int literal = (flags & Constants.SMP_LITERAL);
            if (!((literal != 0)) && c == "\\")
            {
                passNext = true;
                i += 1;
                continue;
            }
            if (backq)
            {
                if (c == "`")
                {
                    backq = false;
                }
                i += 1;
                continue;
            }
            if (!((literal != 0)) && c == "`")
            {
                backq = true;
                i += 1;
                continue;
            }
            if (!((literal != 0)) && c == "'")
            {
                i = ParableFunctions._SkipSingleQuoted(s, i + 1);
                continue;
            }
            if (!((literal != 0)) && c == "\"")
            {
                i = ParableFunctions._SkipDoubleQuoted(s, i + 1);
                continue;
            }
            if (!((literal != 0)) && ParableFunctions._IsExpansionStart(s, i, "$("))
            {
                i = ParableFunctions._FindCmdsubEnd(s, i + 2);
                continue;
            }
            if (!((literal != 0)) && ParableFunctions._IsExpansionStart(s, i, "${"))
            {
                i = ParableFunctions._FindBracedParamEnd(s, i + 2);
                continue;
            }
            if (!((literal != 0)) && c == open)
            {
                depth += 1;
            }
            else
            {
                if (c == close)
                {
                    depth -= 1;
                }
            }
            i += 1;
        }
        return (depth == 0 ? i : -1);
    }

    public static int _SkipSubscript(string s, int start, int flags)
    {
        return ParableFunctions._SkipMatchedPair(s, start, "[", "]", flags);
    }

    public static int _Assignment(string s, int flags)
    {
        if (!((!string.IsNullOrEmpty(s))))
        {
            return -1;
        }
        if (!(((s[0]).ToString().Length > 0 && (s[0]).ToString().All(char.IsLetter)) || (s[0]).ToString() == "_"))
        {
            return -1;
        }
        int i = 1;
        while (i < s.Length)
        {
            string c = (s[i]).ToString();
            if (c == "=")
            {
                return i;
            }
            if (c == "[")
            {
                int subFlags = (((flags & 2) != 0) ? Constants.SMP_LITERAL : 0);
                int end = ParableFunctions._SkipSubscript(s, i, subFlags);
                if (end == -1)
                {
                    return -1;
                }
                i = end;
                if (i < s.Length && (s[i]).ToString() == "+")
                {
                    i += 1;
                }
                if (i < s.Length && (s[i]).ToString() == "=")
                {
                    return i;
                }
                return -1;
            }
            if (c == "+")
            {
                if (i + 1 < s.Length && (s[i + 1]).ToString() == "=")
                {
                    return i + 1;
                }
                return -1;
            }
            if (!((c.Length > 0 && c.All(char.IsLetterOrDigit)) || c == "_"))
            {
                return -1;
            }
            i += 1;
        }
        return -1;
    }

    public static bool _IsArrayAssignmentPrefix(List<string> chars)
    {
        if (!((chars.Count > 0)))
        {
            return false;
        }
        if (!((chars[0].Length > 0 && chars[0].All(char.IsLetter)) || chars[0] == "_"))
        {
            return false;
        }
        string s = string.Join("", chars);
        int i = 1;
        while (i < s.Length && (((s[i]).ToString().Length > 0 && (s[i]).ToString().All(char.IsLetterOrDigit)) || (s[i]).ToString() == "_"))
        {
            i += 1;
        }
        while (i < s.Length)
        {
            if ((s[i]).ToString() != "[")
            {
                return false;
            }
            int end = ParableFunctions._SkipSubscript(s, i, Constants.SMP_LITERAL);
            if (end == -1)
            {
                return false;
            }
            i = end;
        }
        return true;
    }

    public static bool _IsSpecialParamOrDigit(string c)
    {
        return ParableFunctions._IsSpecialParam(c) || ParableFunctions._IsDigit(c);
    }

    public static bool _IsParamExpansionOp(string c)
    {
        return c == ":" || c == "-" || c == "=" || c == "+" || c == "?" || c == "#" || c == "%" || c == "/" || c == "^" || c == "," || c == "@" || c == "*" || c == "[";
    }

    public static bool _IsSimpleParamOp(string c)
    {
        return c == "-" || c == "=" || c == "?" || c == "+";
    }

    public static bool _IsEscapeCharInBacktick(string c)
    {
        return c == "$" || c == "`" || c == "\\";
    }

    public static bool _IsNegationBoundary(string c)
    {
        return ParableFunctions._IsWhitespace(c) || c == ";" || c == "|" || c == ")" || c == "&" || c == ">" || c == "<";
    }

    public static bool _IsBackslashEscaped(string value, int idx)
    {
        int bsCount = 0;
        int j = idx - 1;
        while (j >= 0 && (value[j]).ToString() == "\\")
        {
            bsCount += 1;
            j -= 1;
        }
        return bsCount % 2 == 1;
    }

    public static bool _IsDollarDollarParen(string value, int idx)
    {
        int dollarCount = 0;
        int j = idx - 1;
        while (j >= 0 && (value[j]).ToString() == "$")
        {
            dollarCount += 1;
            j -= 1;
        }
        return dollarCount % 2 == 1;
    }

    public static bool _IsParen(string c)
    {
        return c == "(" || c == ")";
    }

    public static bool _IsCaretOrBang(string c)
    {
        return c == "!" || c == "^";
    }

    public static bool _IsAtOrStar(string c)
    {
        return c == "@" || c == "*";
    }

    public static bool _IsDigitOrDash(string c)
    {
        return ParableFunctions._IsDigit(c) || c == "-";
    }

    public static bool _IsNewlineOrRightParen(string c)
    {
        return c == "\n" || c == ")";
    }

    public static bool _IsSemicolonNewlineBrace(string c)
    {
        return c == ";" || c == "\n" || c == "{";
    }

    public static bool _LooksLikeAssignment(string s)
    {
        return ParableFunctions._Assignment(s, 0) != -1;
    }

    public static bool _IsValidIdentifier(string name)
    {
        if (!((!string.IsNullOrEmpty(name))))
        {
            return false;
        }
        if (!(((name[0]).ToString().Length > 0 && (name[0]).ToString().All(char.IsLetter)) || (name[0]).ToString() == "_"))
        {
            return false;
        }
        foreach (var _c8 in name.Substring(1))
        {
            var c = _c8.ToString();
            if (!((c.Length > 0 && c.All(char.IsLetterOrDigit)) || c == "_"))
            {
                return false;
            }
        }
        return true;
    }

    public static List<INode> Parse(string source, bool extglob)
    {
        Parser parser = ParableFunctions.NewParser(source, false, extglob);
        return parser.Parse();
    }

    public static ParseError NewParseError(string message, int pos, int line)
    {
        ParseError self = new ParseError("", 0, 0);
        self.Message = message;
        self.Pos = pos;
        self.Line = line;
        return self;
    }

    public static MatchedPairError NewMatchedPairError(string message, int pos, int line)
    {
        return new MatchedPairError(message, pos, line);
    }

    public static QuoteState NewQuoteState()
    {
        QuoteState self = new QuoteState(false, false, new List<(bool, bool)>());
        self.Single = false;
        self.Double = false;
        self._Stack = new List<(bool, bool)>();
        return self;
    }

    public static ParseContext NewParseContext(int kind)
    {
        ParseContext self = new ParseContext(0, 0, 0, 0, 0, 0, 0, null);
        self.Kind = kind;
        self.ParenDepth = 0;
        self.BraceDepth = 0;
        self.BracketDepth = 0;
        self.CaseDepth = 0;
        self.ArithDepth = 0;
        self.ArithParenDepth = 0;
        self.Quote = ParableFunctions.NewQuoteState();
        return self;
    }

    public static ContextStack NewContextStack()
    {
        ContextStack self = new ContextStack(new List<ParseContext>());
        self._Stack = new List<ParseContext> { ParableFunctions.NewParseContext(0) };
        return self;
    }

    public static Lexer NewLexer(string source, bool extglob)
    {
        Lexer self = new Lexer(null, "", 0, 0, null, null, 0, 0, new List<INode>(), false, null, "", null, 0, false, false, false, 0, 0, false, false, false);
        self.Source = source;
        self.Pos = 0;
        self.Length = source.Length;
        self.Quote = ParableFunctions.NewQuoteState();
        self._TokenCache = null;
        self._ParserState = Constants.PARSERSTATEFLAGS_NONE;
        self._DolbraceState = Constants.DOLBRACESTATE_NONE;
        self._PendingHeredocs = new List<INode>();
        self._Extglob = extglob;
        self._Parser = null;
        self._EofToken = "";
        self._LastReadToken = null;
        self._WordContext = Constants.WORD_CTX_NORMAL;
        self._AtCommandStart = false;
        self._InArrayLiteral = false;
        self._InAssignBuiltin = false;
        self._PostReadPos = 0;
        self._CachedWordContext = Constants.WORD_CTX_NORMAL;
        self._CachedAtCommandStart = false;
        self._CachedInArrayLiteral = false;
        self._CachedInAssignBuiltin = false;
        return self;
    }

    public static Parser NewParser(string source, bool inProcessSub, bool extglob)
    {
        Parser self = new Parser("", 0, 0, new List<HereDoc>(), 0, false, false, false, null, null, new List<Token>(), 0, 0, "", 0, false, false, false, "", 0, 0);
        self.Source = source;
        self.Pos = 0;
        self.Length = source.Length;
        self._PendingHeredocs = new List<HereDoc>();
        self._CmdsubHeredocEnd = -1;
        self._SawNewlineInSingleQuote = false;
        self._InProcessSub = inProcessSub;
        self._Extglob = extglob;
        self._Ctx = ParableFunctions.NewContextStack();
        self._Lexer = ParableFunctions.NewLexer(source, extglob);
        self._Lexer._Parser = self;
        self._TokenHistory = new List<Token> { null, null, null, null };
        self._ParserState = Constants.PARSERSTATEFLAGS_NONE;
        self._DolbraceState = Constants.DOLBRACESTATE_NONE;
        self._EofToken = "";
        self._WordContext = Constants.WORD_CTX_NORMAL;
        self._AtCommandStart = false;
        self._InArrayLiteral = false;
        self._InAssignBuiltin = false;
        self._ArithSrc = "";
        self._ArithPos = 0;
        self._ArithLen = 0;
        return self;
    }

    public static string _BytesToString(List<byte> bytes)
    {
        return System.Text.Encoding.UTF8.GetString(bytes.ToArray());
    }
}
