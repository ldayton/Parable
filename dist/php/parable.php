<?php

declare(strict_types=1);

const ANSI_C_ESCAPES = ["a" => 7, "b" => 8, "e" => 27, "E" => 27, "f" => 12, "n" => 10, "r" => 13, "t" => 9, "v" => 11, "\\" => 92, "\"" => 34, "?" => 63];
const TOKENTYPE_EOF = 0;
const TOKENTYPE_WORD = 1;
const TOKENTYPE_NEWLINE = 2;
const TOKENTYPE_SEMI = 10;
const TOKENTYPE_PIPE = 11;
const TOKENTYPE_AMP = 12;
const TOKENTYPE_LPAREN = 13;
const TOKENTYPE_RPAREN = 14;
const TOKENTYPE_LBRACE = 15;
const TOKENTYPE_RBRACE = 16;
const TOKENTYPE_LESS = 17;
const TOKENTYPE_GREATER = 18;
const TOKENTYPE_AND_AND = 30;
const TOKENTYPE_OR_OR = 31;
const TOKENTYPE_SEMI_SEMI = 32;
const TOKENTYPE_SEMI_AMP = 33;
const TOKENTYPE_SEMI_SEMI_AMP = 34;
const TOKENTYPE_LESS_LESS = 35;
const TOKENTYPE_GREATER_GREATER = 36;
const TOKENTYPE_LESS_AMP = 37;
const TOKENTYPE_GREATER_AMP = 38;
const TOKENTYPE_LESS_GREATER = 39;
const TOKENTYPE_GREATER_PIPE = 40;
const TOKENTYPE_LESS_LESS_MINUS = 41;
const TOKENTYPE_LESS_LESS_LESS = 42;
const TOKENTYPE_AMP_GREATER = 43;
const TOKENTYPE_AMP_GREATER_GREATER = 44;
const TOKENTYPE_PIPE_AMP = 45;
const TOKENTYPE_IF = 50;
const TOKENTYPE_THEN = 51;
const TOKENTYPE_ELSE = 52;
const TOKENTYPE_ELIF = 53;
const TOKENTYPE_FI = 54;
const TOKENTYPE_CASE = 55;
const TOKENTYPE_ESAC = 56;
const TOKENTYPE_FOR = 57;
const TOKENTYPE_WHILE = 58;
const TOKENTYPE_UNTIL = 59;
const TOKENTYPE_DO = 60;
const TOKENTYPE_DONE = 61;
const TOKENTYPE_IN = 62;
const TOKENTYPE_FUNCTION = 63;
const TOKENTYPE_SELECT = 64;
const TOKENTYPE_COPROC = 65;
const TOKENTYPE_TIME = 66;
const TOKENTYPE_BANG = 67;
const TOKENTYPE_LBRACKET_LBRACKET = 68;
const TOKENTYPE_RBRACKET_RBRACKET = 69;
const TOKENTYPE_ASSIGNMENT_WORD = 80;
const TOKENTYPE_NUMBER = 81;
const PARSERSTATEFLAGS_NONE = 0;
const PARSERSTATEFLAGS_PST_CASEPAT = 1;
const PARSERSTATEFLAGS_PST_CMDSUBST = 2;
const PARSERSTATEFLAGS_PST_CASESTMT = 4;
const PARSERSTATEFLAGS_PST_CONDEXPR = 8;
const PARSERSTATEFLAGS_PST_COMPASSIGN = 16;
const PARSERSTATEFLAGS_PST_ARITH = 32;
const PARSERSTATEFLAGS_PST_HEREDOC = 64;
const PARSERSTATEFLAGS_PST_REGEXP = 128;
const PARSERSTATEFLAGS_PST_EXTPAT = 256;
const PARSERSTATEFLAGS_PST_SUBSHELL = 512;
const PARSERSTATEFLAGS_PST_REDIRLIST = 1024;
const PARSERSTATEFLAGS_PST_COMMENT = 2048;
const PARSERSTATEFLAGS_PST_EOFTOKEN = 4096;
const DOLBRACESTATE_NONE = 0;
const DOLBRACESTATE_PARAM = 1;
const DOLBRACESTATE_OP = 2;
const DOLBRACESTATE_WORD = 4;
const DOLBRACESTATE_QUOTE = 64;
const DOLBRACESTATE_QUOTE2 = 128;
const MATCHEDPAIRFLAGS_NONE = 0;
const MATCHEDPAIRFLAGS_DQUOTE = 1;
const MATCHEDPAIRFLAGS_DOLBRACE = 2;
const MATCHEDPAIRFLAGS_COMMAND = 4;
const MATCHEDPAIRFLAGS_ARITH = 8;
const MATCHEDPAIRFLAGS_ALLOWESC = 16;
const MATCHEDPAIRFLAGS_EXTGLOB = 32;
const MATCHEDPAIRFLAGS_FIRSTCLOSE = 64;
const MATCHEDPAIRFLAGS_ARRAYSUB = 128;
const MATCHEDPAIRFLAGS_BACKQUOTE = 256;
const PARSECONTEXT_NORMAL = 0;
const PARSECONTEXT_COMMAND_SUB = 1;
const PARSECONTEXT_ARITHMETIC = 2;
const PARSECONTEXT_CASE_PATTERN = 3;
const PARSECONTEXT_BRACE_EXPANSION = 4;
const RESERVED_WORDS = ["if" => true, "then" => true, "elif" => true, "else" => true, "fi" => true, "while" => true, "until" => true, "for" => true, "select" => true, "do" => true, "done" => true, "case" => true, "esac" => true, "in" => true, "function" => true, "coproc" => true];
const COND_UNARY_OPS = ["-a" => true, "-b" => true, "-c" => true, "-d" => true, "-e" => true, "-f" => true, "-g" => true, "-h" => true, "-k" => true, "-p" => true, "-r" => true, "-s" => true, "-t" => true, "-u" => true, "-w" => true, "-x" => true, "-G" => true, "-L" => true, "-N" => true, "-O" => true, "-S" => true, "-z" => true, "-n" => true, "-o" => true, "-v" => true, "-R" => true];
const COND_BINARY_OPS = ["==" => true, "!=" => true, "=~" => true, "=" => true, "<" => true, ">" => true, "-eq" => true, "-ne" => true, "-lt" => true, "-le" => true, "-gt" => true, "-ge" => true, "-nt" => true, "-ot" => true, "-ef" => true];
const COMPOUND_KEYWORDS = ["while" => true, "until" => true, "for" => true, "if" => true, "case" => true, "select" => true];
const ASSIGNMENT_BUILTINS = ["alias" => true, "declare" => true, "typeset" => true, "local" => true, "export" => true, "readonly" => true, "eval" => true, "let" => true];
const SMP_LITERAL = 1;
const SMP_PAST_OPEN = 2;
const WORD_CTX_NORMAL = 0;
const WORD_CTX_COND = 1;
const WORD_CTX_REGEX = 2;

interface Node
{
    public function getKind(): string;
    public function toSexp(): string;
}

class Parseerror_ extends Exception
{
    public int $pos;
    public int $line;

    public function __construct(string $message, int $pos = 0, int $line = 0)
    {
        parent::__construct($message);
        $this->pos = $pos;
        $this->line = $line;
    }

    public function _formatMessage(): string
    {
        if ($this->line !== 0 && $this->pos !== 0)
        {
            return sprintf("Parse error at line %s, position %s: %s", $this->line, $this->pos, $this->message);
        }
        else
        {
            if ($this->pos !== 0)
            {
                return sprintf("Parse error at position %s: %s", $this->pos, $this->message);
            }
        }
        return sprintf("Parse error: %s", $this->message);
    }
}

class Matchedpairerror extends Parseerror_
{

    public function __construct(string $message)
    {
        parent::__construct($message, 0, 0);
    }
}

class Tokentype
{
}

class Token
{
    public int $type;
    public string $value;
    public int $pos;
    public ?array $parts;
    public ?Word $word;

    public function __construct(int $type, string $value, int $pos, ?array $parts, ?Word $word)
    {
        $this->type = $type;
        $this->value = $value;
        $this->pos = $pos;
        $this->parts = $parts ?? [];
        $this->word = $word;
    }

    public function _Repr(): string
    {
        if ($this->word !== null)
        {
            return sprintf("Token(%s, %s, %s, word=%s)", $this->type, $this->value, $this->pos, $this->word);
        }
        if ((count($this->parts) > 0))
        {
            return sprintf("Token(%s, %s, %s, parts=%s)", $this->type, $this->value, $this->pos, count($this->parts));
        }
        return sprintf("Token(%s, %s, %s)", $this->type, $this->value, $this->pos);
    }
}

class Parserstateflags
{
}

class Dolbracestate
{
}

class Matchedpairflags
{
}

class Savedparserstate
{
    public int $parserState;
    public int $dolbraceState;
    public ?array $pendingHeredocs;
    public ?array $ctxStack;
    public string $eofToken;

    public function __construct(int $parserState, int $dolbraceState, ?array $pendingHeredocs, ?array $ctxStack, string $eofToken)
    {
        $this->parserState = $parserState;
        $this->dolbraceState = $dolbraceState;
        $this->pendingHeredocs = $pendingHeredocs ?? [];
        $this->ctxStack = $ctxStack ?? [];
        $this->eofToken = $eofToken;
    }
}

class Quotestate
{
    public bool $single;
    public bool $double;
    public ?array $_stack;

    public function __construct(bool $single, bool $double, ?array $_stack)
    {
        $this->single = $single;
        $this->double = $double;
        $this->_stack = $_stack ?? [];
    }

    public function push(): void
    {
        array_push($this->_stack, [$this->single, $this->double]);
        $this->single = false;
        $this->double = false;
    }

    public function pop(): void
    {
        if ((count($this->_stack) > 0))
        {
            [$this->single, $this->double] = array_pop($this->_stack);
        }
    }

    public function inQuotes(): bool
    {
        return $this->single || $this->double;
    }

    public function copy(): ?Quotestate
    {
        $qs = newQuoteState();
        $qs->single = $this->single;
        $qs->double = $this->double;
        $qs->_stack = $this->_stack;
        return $qs;
    }

    public function outerDouble(): bool
    {
        if (count($this->_stack) === 0)
        {
            return false;
        }
        return $this->_stack[count($this->_stack) - 1][1];
    }
}

class Parsecontext
{
    public int $kind;
    public int $parenDepth;
    public int $braceDepth;
    public int $bracketDepth;
    public int $caseDepth;
    public int $arithDepth;
    public int $arithParenDepth;
    public ?Quotestate $quote;

    public function __construct(int $kind, int $parenDepth, int $braceDepth, int $bracketDepth, int $caseDepth, int $arithDepth, int $arithParenDepth, ?Quotestate $quote)
    {
        $this->kind = $kind;
        $this->parenDepth = $parenDepth;
        $this->braceDepth = $braceDepth;
        $this->bracketDepth = $bracketDepth;
        $this->caseDepth = $caseDepth;
        $this->arithDepth = $arithDepth;
        $this->arithParenDepth = $arithParenDepth;
        $this->quote = $quote;
    }

    public function copy(): ?Parsecontext
    {
        $ctx = newParseContext($this->kind);
        $ctx->parenDepth = $this->parenDepth;
        $ctx->braceDepth = $this->braceDepth;
        $ctx->bracketDepth = $this->bracketDepth;
        $ctx->caseDepth = $this->caseDepth;
        $ctx->arithDepth = $this->arithDepth;
        $ctx->arithParenDepth = $this->arithParenDepth;
        $ctx->quote = $this->quote->copy();
        return $ctx;
    }
}

class Contextstack
{
    public ?array $_stack;

    public function __construct(?array $_stack)
    {
        $this->_stack = $_stack ?? [];
    }

    public function getCurrent(): ?Parsecontext
    {
        return $this->_stack[count($this->_stack) - 1];
    }

    public function push(int $kind): void
    {
        array_push($this->_stack, newParseContext($kind));
    }

    public function pop(): ?Parsecontext
    {
        if (count($this->_stack) > 1)
        {
            return array_pop($this->_stack);
        }
        return $this->_stack[0];
    }

    public function copyStack(): ?array
    {
        $result = [];
        foreach ($this->_stack as $ctx)
        {
            array_push($result, $ctx->copy());
        }
        return $result;
    }

    public function restoreFrom(?array $savedStack): void
    {
        $result = [];
        foreach ($savedStack as $ctx)
        {
            array_push($result, $ctx->copy());
        }
        $this->_stack = $result;
    }
}

class Lexer
{
    public array $reservedWords;
    public string $source;
    public int $pos;
    public int $length;
    public ?Quotestate $quote;
    public ?Token $_tokenCache;
    public int $_parserState;
    public int $_dolbraceState;
    public ?array $_pendingHeredocs;
    public bool $_extglob;
    public ?Parser $_parser;
    public string $_eofToken;
    public ?Token $_lastReadToken;
    public int $_wordContext;
    public bool $_atCommandStart;
    public bool $_inArrayLiteral;
    public bool $_inAssignBuiltin;
    public int $_postReadPos;
    public int $_cachedWordContext;
    public bool $_cachedAtCommandStart;
    public bool $_cachedInArrayLiteral;
    public bool $_cachedInAssignBuiltin;

    public function __construct(array $reservedWords, string $source, int $pos, int $length, ?Quotestate $quote, int $_parserState, int $_dolbraceState, ?array $_pendingHeredocs, bool $_extglob, string $_eofToken, int $_wordContext, bool $_atCommandStart, bool $_inArrayLiteral, bool $_inAssignBuiltin, int $_postReadPos, int $_cachedWordContext, bool $_cachedAtCommandStart, bool $_cachedInArrayLiteral, bool $_cachedInAssignBuiltin, ?Token $_tokenCache = null, ?Parser $_parser = null, ?Token $_lastReadToken = null)
    {
        $this->reservedWords = $reservedWords;
        $this->source = $source;
        $this->pos = $pos;
        $this->length = $length;
        $this->quote = $quote;
        $this->_parserState = $_parserState;
        $this->_dolbraceState = $_dolbraceState;
        $this->_pendingHeredocs = $_pendingHeredocs ?? [];
        $this->_extglob = $_extglob;
        $this->_eofToken = $_eofToken;
        $this->_wordContext = $_wordContext;
        $this->_atCommandStart = $_atCommandStart;
        $this->_inArrayLiteral = $_inArrayLiteral;
        $this->_inAssignBuiltin = $_inAssignBuiltin;
        $this->_postReadPos = $_postReadPos;
        $this->_cachedWordContext = $_cachedWordContext;
        $this->_cachedAtCommandStart = $_cachedAtCommandStart;
        $this->_cachedInArrayLiteral = $_cachedInArrayLiteral;
        $this->_cachedInAssignBuiltin = $_cachedInAssignBuiltin;
        $this->_tokenCache = $_tokenCache;
        $this->_parser = $_parser;
        $this->_lastReadToken = $_lastReadToken;
    }

    public function peek(): string
    {
        if ($this->pos >= $this->length)
        {
            return "";
        }
        return (string)(mb_substr($this->source, $this->pos, 1));
    }

    public function advance(): string
    {
        if ($this->pos >= $this->length)
        {
            return "";
        }
        $c = (string)(mb_substr($this->source, $this->pos, 1));
        $this->pos += 1;
        return $c;
    }

    public function atEnd(): bool
    {
        return $this->pos >= $this->length;
    }

    public function lookahead(int $n): string
    {
        return _substring($this->source, $this->pos, $this->pos + $n);
    }

    public function isMetachar(string $c): bool
    {
        return (str_contains("|&;()<> \t\n", $c));
    }

    public function _readOperator(): ?Token
    {
        $start = $this->pos;
        $c = $this->peek();
        if ($c === "")
        {
            return null;
        }
        $two = $this->lookahead(2);
        $three = $this->lookahead(3);
        if ($three === ";;&")
        {
            $this->pos += 3;
            return new Token(TOKENTYPE_SEMI_SEMI_AMP, $three, $start, [], null);
        }
        if ($three === "<<-")
        {
            $this->pos += 3;
            return new Token(TOKENTYPE_LESS_LESS_MINUS, $three, $start, [], null);
        }
        if ($three === "<<<")
        {
            $this->pos += 3;
            return new Token(TOKENTYPE_LESS_LESS_LESS, $three, $start, [], null);
        }
        if ($three === "&>>")
        {
            $this->pos += 3;
            return new Token(TOKENTYPE_AMP_GREATER_GREATER, $three, $start, [], null);
        }
        if ($two === "&&")
        {
            $this->pos += 2;
            return new Token(TOKENTYPE_AND_AND, $two, $start, [], null);
        }
        if ($two === "||")
        {
            $this->pos += 2;
            return new Token(TOKENTYPE_OR_OR, $two, $start, [], null);
        }
        if ($two === ";;")
        {
            $this->pos += 2;
            return new Token(TOKENTYPE_SEMI_SEMI, $two, $start, [], null);
        }
        if ($two === ";&")
        {
            $this->pos += 2;
            return new Token(TOKENTYPE_SEMI_AMP, $two, $start, [], null);
        }
        if ($two === "<<")
        {
            $this->pos += 2;
            return new Token(TOKENTYPE_LESS_LESS, $two, $start, [], null);
        }
        if ($two === ">>")
        {
            $this->pos += 2;
            return new Token(TOKENTYPE_GREATER_GREATER, $two, $start, [], null);
        }
        if ($two === "<&")
        {
            $this->pos += 2;
            return new Token(TOKENTYPE_LESS_AMP, $two, $start, [], null);
        }
        if ($two === ">&")
        {
            $this->pos += 2;
            return new Token(TOKENTYPE_GREATER_AMP, $two, $start, [], null);
        }
        if ($two === "<>")
        {
            $this->pos += 2;
            return new Token(TOKENTYPE_LESS_GREATER, $two, $start, [], null);
        }
        if ($two === ">|")
        {
            $this->pos += 2;
            return new Token(TOKENTYPE_GREATER_PIPE, $two, $start, [], null);
        }
        if ($two === "&>")
        {
            $this->pos += 2;
            return new Token(TOKENTYPE_AMP_GREATER, $two, $start, [], null);
        }
        if ($two === "|&")
        {
            $this->pos += 2;
            return new Token(TOKENTYPE_PIPE_AMP, $two, $start, [], null);
        }
        if ($c === ";")
        {
            $this->pos += 1;
            return new Token(TOKENTYPE_SEMI, $c, $start, [], null);
        }
        if ($c === "|")
        {
            $this->pos += 1;
            return new Token(TOKENTYPE_PIPE, $c, $start, [], null);
        }
        if ($c === "&")
        {
            $this->pos += 1;
            return new Token(TOKENTYPE_AMP, $c, $start, [], null);
        }
        if ($c === "(")
        {
            if ($this->_wordContext === WORD_CTX_REGEX)
            {
                return null;
            }
            $this->pos += 1;
            return new Token(TOKENTYPE_LPAREN, $c, $start, [], null);
        }
        if ($c === ")")
        {
            if ($this->_wordContext === WORD_CTX_REGEX)
            {
                return null;
            }
            $this->pos += 1;
            return new Token(TOKENTYPE_RPAREN, $c, $start, [], null);
        }
        if ($c === "<")
        {
            if ($this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "(")
            {
                return null;
            }
            $this->pos += 1;
            return new Token(TOKENTYPE_LESS, $c, $start, [], null);
        }
        if ($c === ">")
        {
            if ($this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "(")
            {
                return null;
            }
            $this->pos += 1;
            return new Token(TOKENTYPE_GREATER, $c, $start, [], null);
        }
        if ($c === "\n")
        {
            $this->pos += 1;
            return new Token(TOKENTYPE_NEWLINE, $c, $start, [], null);
        }
        return null;
    }

    public function skipBlanks(): void
    {
        while ($this->pos < $this->length)
        {
            $c = (string)(mb_substr($this->source, $this->pos, 1));
            if ($c !== " " && $c !== "\t")
            {
                break;
            }
            $this->pos += 1;
        }
    }

    public function _skipComment(): bool
    {
        if ($this->pos >= $this->length)
        {
            return false;
        }
        if ((string)(mb_substr($this->source, $this->pos, 1)) !== "#")
        {
            return false;
        }
        if ($this->quote->inQuotes())
        {
            return false;
        }
        if ($this->pos > 0)
        {
            $prev = (string)(mb_substr($this->source, $this->pos - 1, 1));
            if ((!str_contains(" \t\n;|&(){}", $prev)))
            {
                return false;
            }
        }
        while ($this->pos < $this->length && (string)(mb_substr($this->source, $this->pos, 1)) !== "\n")
        {
            $this->pos += 1;
        }
        return true;
    }

    public function _readSingleQuote(int $start): array
    {
        $chars = ["'"];
        $sawNewline = false;
        while ($this->pos < $this->length)
        {
            $c = (string)(mb_substr($this->source, $this->pos, 1));
            if ($c === "\n")
            {
                $sawNewline = true;
            }
            array_push($chars, $c);
            $this->pos += 1;
            if ($c === "'")
            {
                return [implode("", $chars), $sawNewline];
            }
        }
        throw new Parseerror_("Unterminated single quote");
    }

    public function _isWordTerminator(int $ctx, string $ch, int $bracketDepth, int $parenDepth): bool
    {
        if ($ctx === WORD_CTX_REGEX)
        {
            if ($ch === "]" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "]")
            {
                return true;
            }
            if ($ch === "&" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "&")
            {
                return true;
            }
            if ($ch === ")" && $parenDepth === 0)
            {
                return true;
            }
            return _isWhitespace($ch) && $parenDepth === 0;
        }
        if ($ctx === WORD_CTX_COND)
        {
            if ($ch === "]" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "]")
            {
                return true;
            }
            if ($ch === ")")
            {
                return true;
            }
            if ($ch === "&")
            {
                return true;
            }
            if ($ch === "|")
            {
                return true;
            }
            if ($ch === ";")
            {
                return true;
            }
            if (_isRedirectChar($ch) && !($this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "("))
            {
                return true;
            }
            return _isWhitespace($ch);
        }
        if ((($this->_parserState & PARSERSTATEFLAGS_PST_EOFTOKEN) !== 0) && $this->_eofToken !== "" && $ch === $this->_eofToken && $bracketDepth === 0)
        {
            return true;
        }
        if (_isRedirectChar($ch) && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "(")
        {
            return false;
        }
        return _isMetachar($ch) && $bracketDepth === 0;
    }

    public function _readBracketExpression(?array &$chars, ?array $parts, bool $forRegex, int $parenDepth): bool
    {
        if ($forRegex)
        {
            $scan = $this->pos + 1;
            if ($scan < $this->length && (string)(mb_substr($this->source, $scan, 1)) === "^")
            {
                $scan += 1;
            }
            if ($scan < $this->length && (string)(mb_substr($this->source, $scan, 1)) === "]")
            {
                $scan += 1;
            }
            $bracketWillClose = false;
            while ($scan < $this->length)
            {
                $sc = (string)(mb_substr($this->source, $scan, 1));
                if ($sc === "]" && $scan + 1 < $this->length && (string)(mb_substr($this->source, $scan + 1, 1)) === "]")
                {
                    break;
                }
                if ($sc === ")" && $parenDepth > 0)
                {
                    break;
                }
                if ($sc === "&" && $scan + 1 < $this->length && (string)(mb_substr($this->source, $scan + 1, 1)) === "&")
                {
                    break;
                }
                if ($sc === "]")
                {
                    $bracketWillClose = true;
                    break;
                }
                if ($sc === "[" && $scan + 1 < $this->length && (string)(mb_substr($this->source, $scan + 1, 1)) === ":")
                {
                    $scan += 2;
                    while ($scan < $this->length && !((string)(mb_substr($this->source, $scan, 1)) === ":" && $scan + 1 < $this->length && (string)(mb_substr($this->source, $scan + 1, 1)) === "]"))
                    {
                        $scan += 1;
                    }
                    if ($scan < $this->length)
                    {
                        $scan += 2;
                    }
                    continue;
                }
                $scan += 1;
            }
            if (!$bracketWillClose)
            {
                return false;
            }
        }
        else
        {
            if ($this->pos + 1 >= $this->length)
            {
                return false;
            }
            $nextCh = (string)(mb_substr($this->source, $this->pos + 1, 1));
            if (_isWhitespaceNoNewline($nextCh) || $nextCh === "&" || $nextCh === "|")
            {
                return false;
            }
        }
        array_push($chars, $this->advance());
        if (!$this->atEnd() && $this->peek() === "^")
        {
            array_push($chars, $this->advance());
        }
        if (!$this->atEnd() && $this->peek() === "]")
        {
            array_push($chars, $this->advance());
        }
        while (!$this->atEnd())
        {
            $c = $this->peek();
            if ($c === "]")
            {
                array_push($chars, $this->advance());
                break;
            }
            if ($c === "[" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === ":")
            {
                array_push($chars, $this->advance());
                array_push($chars, $this->advance());
                while (!$this->atEnd() && !($this->peek() === ":" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "]"))
                {
                    array_push($chars, $this->advance());
                }
                if (!$this->atEnd())
                {
                    array_push($chars, $this->advance());
                    array_push($chars, $this->advance());
                }
            }
            else
            {
                if (!$forRegex && $c === "[" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "=")
                {
                    array_push($chars, $this->advance());
                    array_push($chars, $this->advance());
                    while (!$this->atEnd() && !($this->peek() === "=" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "]"))
                    {
                        array_push($chars, $this->advance());
                    }
                    if (!$this->atEnd())
                    {
                        array_push($chars, $this->advance());
                        array_push($chars, $this->advance());
                    }
                }
                else
                {
                    if (!$forRegex && $c === "[" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === ".")
                    {
                        array_push($chars, $this->advance());
                        array_push($chars, $this->advance());
                        while (!$this->atEnd() && !($this->peek() === "." && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "]"))
                        {
                            array_push($chars, $this->advance());
                        }
                        if (!$this->atEnd())
                        {
                            array_push($chars, $this->advance());
                            array_push($chars, $this->advance());
                        }
                    }
                    else
                    {
                        if ($forRegex && $c === "\$")
                        {
                            $this->_syncToParser();
                            if (!$this->_parser->_parseDollarExpansion($chars, $parts, false))
                            {
                                $this->_syncFromParser();
                                array_push($chars, $this->advance());
                            }
                            else
                            {
                                $this->_syncFromParser();
                            }
                        }
                        else
                        {
                            array_push($chars, $this->advance());
                        }
                    }
                }
            }
        }
        return true;
    }

    public function _parseMatchedPair(string $openChar, string $closeChar, int $flags, bool $initialWasDollar): string
    {
        $start = $this->pos;
        $count = 1;
        $chars = [];
        $passNext = false;
        $wasDollar = $initialWasDollar;
        $wasGtlt = false;
        while ($count > 0)
        {
            if ($this->atEnd())
            {
                throw new Matchedpairerror(sprintf("unexpected EOF while looking for matching `%s'", $closeChar));
            }
            $ch = $this->advance();
            if ((($flags & MATCHEDPAIRFLAGS_DOLBRACE) !== 0) && $this->_dolbraceState === DOLBRACESTATE_OP)
            {
                if ((!str_contains("#%^,~:-=?+/", $ch)))
                {
                    $this->_dolbraceState = DOLBRACESTATE_WORD;
                }
            }
            if ($passNext)
            {
                $passNext = false;
                array_push($chars, $ch);
                $wasDollar = $ch === "\$";
                $wasGtlt = (str_contains("<>", $ch));
                continue;
            }
            if ($openChar === "'")
            {
                if ($ch === $closeChar)
                {
                    $count -= 1;
                    if ($count === 0)
                    {
                        break;
                    }
                }
                if ($ch === "\\" && (($flags & MATCHEDPAIRFLAGS_ALLOWESC) !== 0))
                {
                    $passNext = true;
                }
                array_push($chars, $ch);
                $wasDollar = false;
                $wasGtlt = false;
                continue;
            }
            if ($ch === "\\")
            {
                if (!$this->atEnd() && $this->peek() === "\n")
                {
                    $this->advance();
                    $wasDollar = false;
                    $wasGtlt = false;
                    continue;
                }
                $passNext = true;
                array_push($chars, $ch);
                $wasDollar = false;
                $wasGtlt = false;
                continue;
            }
            if ($ch === $closeChar)
            {
                $count -= 1;
                if ($count === 0)
                {
                    break;
                }
                array_push($chars, $ch);
                $wasDollar = false;
                $wasGtlt = (str_contains("<>", $ch));
                continue;
            }
            if ($ch === $openChar && $openChar !== $closeChar)
            {
                if (!((($flags & MATCHEDPAIRFLAGS_DOLBRACE) !== 0) && $openChar === "{"))
                {
                    $count += 1;
                }
                array_push($chars, $ch);
                $wasDollar = false;
                $wasGtlt = (str_contains("<>", $ch));
                continue;
            }
            if (((str_contains("'\"`", $ch))) && $openChar !== $closeChar)
            {
                $nested = "";
                if ($ch === "'")
                {
                    array_push($chars, $ch);
                    $quoteFlags = ($wasDollar ? ($flags | MATCHEDPAIRFLAGS_ALLOWESC) : $flags);
                    $nested = $this->_parseMatchedPair("'", "'", $quoteFlags, false);
                    array_push($chars, $nested);
                    array_push($chars, "'");
                    $wasDollar = false;
                    $wasGtlt = false;
                    continue;
                }
                else
                {
                    if ($ch === "\"")
                    {
                        array_push($chars, $ch);
                        $nested = $this->_parseMatchedPair("\"", "\"", ($flags | MATCHEDPAIRFLAGS_DQUOTE), false);
                        array_push($chars, $nested);
                        array_push($chars, "\"");
                        $wasDollar = false;
                        $wasGtlt = false;
                        continue;
                    }
                    else
                    {
                        if ($ch === "`")
                        {
                            array_push($chars, $ch);
                            $nested = $this->_parseMatchedPair("`", "`", $flags, false);
                            array_push($chars, $nested);
                            array_push($chars, "`");
                            $wasDollar = false;
                            $wasGtlt = false;
                            continue;
                        }
                    }
                }
            }
            if ($ch === "\$" && !$this->atEnd() && !(($flags & MATCHEDPAIRFLAGS_EXTGLOB) !== 0))
            {
                $nextCh = $this->peek();
                if ($wasDollar)
                {
                    array_push($chars, $ch);
                    $wasDollar = false;
                    $wasGtlt = false;
                    continue;
                }
                if ($nextCh === "{")
                {
                    if ((($flags & MATCHEDPAIRFLAGS_ARITH) !== 0))
                    {
                        $afterBracePos = $this->pos + 1;
                        if ($afterBracePos >= $this->length || !_isFunsubChar((string)(mb_substr($this->source, $afterBracePos, 1))))
                        {
                            array_push($chars, $ch);
                            $wasDollar = true;
                            $wasGtlt = false;
                            continue;
                        }
                    }
                    $this->pos -= 1;
                    $this->_syncToParser();
                    $inDquote = ((($flags & MATCHEDPAIRFLAGS_DQUOTE)) !== 0);
                    [$paramNode, $paramText] = $this->_parser->_parseParamExpansion($inDquote);
                    $this->_syncFromParser();
                    if ($paramNode !== null)
                    {
                        array_push($chars, $paramText);
                        $wasDollar = false;
                        $wasGtlt = false;
                    }
                    else
                    {
                        array_push($chars, $this->advance());
                        $wasDollar = true;
                        $wasGtlt = false;
                    }
                    continue;
                }
                else
                {
                    $arithNode = null;
                    $arithText = "";
                    if ($nextCh === "(")
                    {
                        $this->pos -= 1;
                        $this->_syncToParser();
                        $cmdNode = null;
                        $cmdText = "";
                        if ($this->pos + 2 < $this->length && (string)(mb_substr($this->source, $this->pos + 2, 1)) === "(")
                        {
                            [$arithNode, $arithText] = $this->_parser->_parseArithmeticExpansion();
                            $this->_syncFromParser();
                            if ($arithNode !== null)
                            {
                                array_push($chars, $arithText);
                                $wasDollar = false;
                                $wasGtlt = false;
                            }
                            else
                            {
                                $this->_syncToParser();
                                [$cmdNode, $cmdText] = $this->_parser->_parseCommandSubstitution();
                                $this->_syncFromParser();
                                if ($cmdNode !== null)
                                {
                                    array_push($chars, $cmdText);
                                    $wasDollar = false;
                                    $wasGtlt = false;
                                }
                                else
                                {
                                    array_push($chars, $this->advance());
                                    array_push($chars, $this->advance());
                                    $wasDollar = false;
                                    $wasGtlt = false;
                                }
                            }
                        }
                        else
                        {
                            [$cmdNode, $cmdText] = $this->_parser->_parseCommandSubstitution();
                            $this->_syncFromParser();
                            if ($cmdNode !== null)
                            {
                                array_push($chars, $cmdText);
                                $wasDollar = false;
                                $wasGtlt = false;
                            }
                            else
                            {
                                array_push($chars, $this->advance());
                                array_push($chars, $this->advance());
                                $wasDollar = false;
                                $wasGtlt = false;
                            }
                        }
                        continue;
                    }
                    else
                    {
                        if ($nextCh === "[")
                        {
                            $this->pos -= 1;
                            $this->_syncToParser();
                            [$arithNode, $arithText] = $this->_parser->_parseDeprecatedArithmetic();
                            $this->_syncFromParser();
                            if ($arithNode !== null)
                            {
                                array_push($chars, $arithText);
                                $wasDollar = false;
                                $wasGtlt = false;
                            }
                            else
                            {
                                array_push($chars, $this->advance());
                                $wasDollar = true;
                                $wasGtlt = false;
                            }
                            continue;
                        }
                    }
                }
            }
            if ($ch === "(" && $wasGtlt && (($flags & ((MATCHEDPAIRFLAGS_DOLBRACE | MATCHEDPAIRFLAGS_ARRAYSUB))) !== 0))
            {
                $direction = $chars[count($chars) - 1];
                $chars = array_slice($chars, 0, count($chars) - 1);
                $this->pos -= 1;
                $this->_syncToParser();
                [$procsubNode, $procsubText] = $this->_parser->_parseProcessSubstitution();
                $this->_syncFromParser();
                if ($procsubNode !== null)
                {
                    array_push($chars, $procsubText);
                    $wasDollar = false;
                    $wasGtlt = false;
                }
                else
                {
                    array_push($chars, $direction);
                    array_push($chars, $this->advance());
                    $wasDollar = false;
                    $wasGtlt = false;
                }
                continue;
            }
            array_push($chars, $ch);
            $wasDollar = $ch === "\$";
            $wasGtlt = (str_contains("<>", $ch));
        }
        return implode("", $chars);
    }

    public function _collectParamArgument(int $flags, bool $wasDollar): string
    {
        return $this->_parseMatchedPair("{", "}", ($flags | MATCHEDPAIRFLAGS_DOLBRACE), $wasDollar);
    }

    public function _readWordInternal(int $ctx, bool $atCommandStart, bool $inArrayLiteral, bool $inAssignBuiltin): ?Word
    {
        $start = $this->pos;
        $chars = [];
        $parts = [];
        $bracketDepth = 0;
        $bracketStartPos = -1;
        $seenEquals = false;
        $parenDepth = 0;
        while (!$this->atEnd())
        {
            $ch = $this->peek();
            if ($ctx === WORD_CTX_REGEX)
            {
                if ($ch === "\\" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "\n")
                {
                    $this->advance();
                    $this->advance();
                    continue;
                }
            }
            if ($ctx !== WORD_CTX_NORMAL && $this->_isWordTerminator($ctx, $ch, $bracketDepth, $parenDepth))
            {
                break;
            }
            if ($ctx === WORD_CTX_NORMAL && $ch === "[")
            {
                if ($bracketDepth > 0)
                {
                    $bracketDepth += 1;
                    array_push($chars, $this->advance());
                    continue;
                }
                if ((count($chars) > 0) && $atCommandStart && !$seenEquals && _isArrayAssignmentPrefix($chars))
                {
                    $prevChar = $chars[count($chars) - 1];
                    if (ctype_alnum($prevChar) || $prevChar === "_")
                    {
                        $bracketStartPos = $this->pos;
                        $bracketDepth += 1;
                        array_push($chars, $this->advance());
                        continue;
                    }
                }
                if (!(count($chars) > 0) && !$seenEquals && $inArrayLiteral)
                {
                    $bracketStartPos = $this->pos;
                    $bracketDepth += 1;
                    array_push($chars, $this->advance());
                    continue;
                }
            }
            if ($ctx === WORD_CTX_NORMAL && $ch === "]" && $bracketDepth > 0)
            {
                $bracketDepth -= 1;
                array_push($chars, $this->advance());
                continue;
            }
            if ($ctx === WORD_CTX_NORMAL && $ch === "=" && $bracketDepth === 0)
            {
                $seenEquals = true;
            }
            if ($ctx === WORD_CTX_REGEX && $ch === "(")
            {
                $parenDepth += 1;
                array_push($chars, $this->advance());
                continue;
            }
            if ($ctx === WORD_CTX_REGEX && $ch === ")")
            {
                if ($parenDepth > 0)
                {
                    $parenDepth -= 1;
                    array_push($chars, $this->advance());
                    continue;
                }
                break;
            }
            if (($ctx === WORD_CTX_COND || $ctx === WORD_CTX_REGEX) && $ch === "[")
            {
                $forRegex = $ctx === WORD_CTX_REGEX;
                if ($this->_readBracketExpression($chars, $parts, $forRegex, $parenDepth))
                {
                    continue;
                }
                array_push($chars, $this->advance());
                continue;
            }
            $content = "";
            if ($ctx === WORD_CTX_COND && $ch === "(")
            {
                if ($this->_extglob && (count($chars) > 0) && _isExtglobPrefix($chars[count($chars) - 1]))
                {
                    array_push($chars, $this->advance());
                    $content = $this->_parseMatchedPair("(", ")", MATCHEDPAIRFLAGS_EXTGLOB, false);
                    array_push($chars, $content);
                    array_push($chars, ")");
                    continue;
                }
                else
                {
                    break;
                }
            }
            if ($ctx === WORD_CTX_REGEX && _isWhitespace($ch) && $parenDepth > 0)
            {
                array_push($chars, $this->advance());
                continue;
            }
            if ($ch === "'")
            {
                $this->advance();
                $trackNewline = $ctx === WORD_CTX_NORMAL;
                [$content, $sawNewline] = $this->_readSingleQuote($start);
                array_push($chars, $content);
                if ($trackNewline && $sawNewline && $this->_parser !== null)
                {
                    $this->_parser->_sawNewlineInSingleQuote = true;
                }
                continue;
            }
            $cmdsubResult0 = null;
            $cmdsubResult1 = "";
            if ($ch === "\"")
            {
                $this->advance();
                if ($ctx === WORD_CTX_NORMAL)
                {
                    array_push($chars, "\"");
                    $inSingleInDquote = false;
                    while (!$this->atEnd() && ($inSingleInDquote || $this->peek() !== "\""))
                    {
                        $c = $this->peek();
                        if ($inSingleInDquote)
                        {
                            array_push($chars, $this->advance());
                            if ($c === "'")
                            {
                                $inSingleInDquote = false;
                            }
                            continue;
                        }
                        if ($c === "\\" && $this->pos + 1 < $this->length)
                        {
                            $nextC = (string)(mb_substr($this->source, $this->pos + 1, 1));
                            if ($nextC === "\n")
                            {
                                $this->advance();
                                $this->advance();
                            }
                            else
                            {
                                array_push($chars, $this->advance());
                                array_push($chars, $this->advance());
                            }
                        }
                        else
                        {
                            if ($c === "\$")
                            {
                                $this->_syncToParser();
                                if (!$this->_parser->_parseDollarExpansion($chars, $parts, true))
                                {
                                    $this->_syncFromParser();
                                    array_push($chars, $this->advance());
                                }
                                else
                                {
                                    $this->_syncFromParser();
                                }
                            }
                            else
                            {
                                if ($c === "`")
                                {
                                    $this->_syncToParser();
                                    [$cmdsubResult0, $cmdsubResult1] = $this->_parser->_parseBacktickSubstitution();
                                    $this->_syncFromParser();
                                    if ($cmdsubResult0 !== null)
                                    {
                                        array_push($parts, $cmdsubResult0);
                                        array_push($chars, $cmdsubResult1);
                                    }
                                    else
                                    {
                                        array_push($chars, $this->advance());
                                    }
                                }
                                else
                                {
                                    array_push($chars, $this->advance());
                                }
                            }
                        }
                    }
                    if ($this->atEnd())
                    {
                        throw new Parseerror_("Unterminated double quote");
                    }
                    array_push($chars, $this->advance());
                }
                else
                {
                    $handleLineContinuation = $ctx === WORD_CTX_COND;
                    $this->_syncToParser();
                    $this->_parser->_scanDoubleQuote($chars, $parts, $start, $handleLineContinuation);
                    $this->_syncFromParser();
                }
                continue;
            }
            if ($ch === "\\" && $this->pos + 1 < $this->length)
            {
                $nextCh = (string)(mb_substr($this->source, $this->pos + 1, 1));
                if ($ctx !== WORD_CTX_REGEX && $nextCh === "\n")
                {
                    $this->advance();
                    $this->advance();
                }
                else
                {
                    array_push($chars, $this->advance());
                    array_push($chars, $this->advance());
                }
                continue;
            }
            if ($ctx !== WORD_CTX_REGEX && $ch === "\$" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "'")
            {
                [$ansiResult0, $ansiResult1] = $this->_readAnsiCQuote();
                if ($ansiResult0 !== null)
                {
                    array_push($parts, $ansiResult0);
                    array_push($chars, $ansiResult1);
                }
                else
                {
                    array_push($chars, $this->advance());
                }
                continue;
            }
            if ($ctx !== WORD_CTX_REGEX && $ch === "\$" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "\"")
            {
                [$localeResult0, $localeResult1, $localeResult2] = $this->_readLocaleString();
                if ($localeResult0 !== null)
                {
                    array_push($parts, $localeResult0);
                    array_push($parts, ...$localeResult2);
                    array_push($chars, $localeResult1);
                }
                else
                {
                    array_push($chars, $this->advance());
                }
                continue;
            }
            if ($ch === "\$")
            {
                $this->_syncToParser();
                if (!$this->_parser->_parseDollarExpansion($chars, $parts, false))
                {
                    $this->_syncFromParser();
                    array_push($chars, $this->advance());
                }
                else
                {
                    $this->_syncFromParser();
                    if ($this->_extglob && $ctx === WORD_CTX_NORMAL && (count($chars) > 0) && mb_strlen($chars[count($chars) - 1]) === 2 && (string)(mb_substr($chars[count($chars) - 1], 0, 1)) === "\$" && ((str_contains("?*@", (string)(mb_substr($chars[count($chars) - 1], 1, 1))))) && !$this->atEnd() && $this->peek() === "(")
                    {
                        array_push($chars, $this->advance());
                        $content = $this->_parseMatchedPair("(", ")", MATCHEDPAIRFLAGS_EXTGLOB, false);
                        array_push($chars, $content);
                        array_push($chars, ")");
                    }
                }
                continue;
            }
            if ($ctx !== WORD_CTX_REGEX && $ch === "`")
            {
                $this->_syncToParser();
                [$cmdsubResult0, $cmdsubResult1] = $this->_parser->_parseBacktickSubstitution();
                $this->_syncFromParser();
                if ($cmdsubResult0 !== null)
                {
                    array_push($parts, $cmdsubResult0);
                    array_push($chars, $cmdsubResult1);
                }
                else
                {
                    array_push($chars, $this->advance());
                }
                continue;
            }
            if ($ctx !== WORD_CTX_REGEX && _isRedirectChar($ch) && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "(")
            {
                $this->_syncToParser();
                [$procsubResult0, $procsubResult1] = $this->_parser->_parseProcessSubstitution();
                $this->_syncFromParser();
                if ($procsubResult0 !== null)
                {
                    array_push($parts, $procsubResult0);
                    array_push($chars, $procsubResult1);
                }
                else
                {
                    if (($procsubResult1 !== ''))
                    {
                        array_push($chars, $procsubResult1);
                    }
                    else
                    {
                        array_push($chars, $this->advance());
                        if ($ctx === WORD_CTX_NORMAL)
                        {
                            array_push($chars, $this->advance());
                        }
                    }
                }
                continue;
            }
            if ($ctx === WORD_CTX_NORMAL && $ch === "(" && (count($chars) > 0) && $bracketDepth === 0)
            {
                $isArrayAssign = false;
                if (count($chars) >= 3 && $chars[count($chars) - 2] === "+" && $chars[count($chars) - 1] === "=")
                {
                    $isArrayAssign = _isArrayAssignmentPrefix(array_slice($chars, 0, count($chars) - 2));
                }
                else
                {
                    if ($chars[count($chars) - 1] === "=" && count($chars) >= 2)
                    {
                        $isArrayAssign = _isArrayAssignmentPrefix(array_slice($chars, 0, count($chars) - 1));
                    }
                }
                if ($isArrayAssign && ($atCommandStart || $inAssignBuiltin))
                {
                    $this->_syncToParser();
                    [$arrayResult0, $arrayResult1] = $this->_parser->_parseArrayLiteral();
                    $this->_syncFromParser();
                    if ($arrayResult0 !== null)
                    {
                        array_push($parts, $arrayResult0);
                        array_push($chars, $arrayResult1);
                    }
                    else
                    {
                        break;
                    }
                    continue;
                }
            }
            if ($this->_extglob && $ctx === WORD_CTX_NORMAL && _isExtglobPrefix($ch) && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "(")
            {
                array_push($chars, $this->advance());
                array_push($chars, $this->advance());
                $content = $this->_parseMatchedPair("(", ")", MATCHEDPAIRFLAGS_EXTGLOB, false);
                array_push($chars, $content);
                array_push($chars, ")");
                continue;
            }
            if ($ctx === WORD_CTX_NORMAL && (($this->_parserState & PARSERSTATEFLAGS_PST_EOFTOKEN) !== 0) && $this->_eofToken !== "" && $ch === $this->_eofToken && $bracketDepth === 0)
            {
                if (!(count($chars) > 0))
                {
                    array_push($chars, $this->advance());
                }
                break;
            }
            if ($ctx === WORD_CTX_NORMAL && _isMetachar($ch) && $bracketDepth === 0)
            {
                break;
            }
            array_push($chars, $this->advance());
        }
        if ($bracketDepth > 0 && $bracketStartPos !== -1 && $this->atEnd())
        {
            throw new Matchedpairerror("unexpected EOF looking for `]'");
        }
        if (!(count($chars) > 0))
        {
            return null;
        }
        if ((count($parts) > 0))
        {
            return new Word(implode("", $chars), $parts, "word");
        }
        return new Word(implode("", $chars), null, "word");
    }

    public function _readWord(): ?Token
    {
        $start = $this->pos;
        if ($this->pos >= $this->length)
        {
            return null;
        }
        $c = $this->peek();
        if ($c === "")
        {
            return null;
        }
        $isProcsub = ($c === "<" || $c === ">") && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "(";
        $isRegexParen = $this->_wordContext === WORD_CTX_REGEX && ($c === "(" || $c === ")");
        if ($this->isMetachar($c) && !$isProcsub && !$isRegexParen)
        {
            return null;
        }
        $word = $this->_readWordInternal($this->_wordContext, $this->_atCommandStart, $this->_inArrayLiteral, $this->_inAssignBuiltin);
        if ($word === null)
        {
            return null;
        }
        return new Token(TOKENTYPE_WORD, $word->value, $start, null, $word);
    }

    public function nextToken(): ?Token
    {
        $tok = null;
        if ($this->_tokenCache !== null)
        {
            $tok = $this->_tokenCache;
            $this->_tokenCache = null;
            $this->_lastReadToken = $tok;
            return $tok;
        }
        $this->skipBlanks();
        if ($this->atEnd())
        {
            $tok = new Token(TOKENTYPE_EOF, "", $this->pos, [], null);
            $this->_lastReadToken = $tok;
            return $tok;
        }
        if ($this->_eofToken !== "" && $this->peek() === $this->_eofToken && !(($this->_parserState & PARSERSTATEFLAGS_PST_CASEPAT) !== 0) && !(($this->_parserState & PARSERSTATEFLAGS_PST_EOFTOKEN) !== 0))
        {
            $tok = new Token(TOKENTYPE_EOF, "", $this->pos, [], null);
            $this->_lastReadToken = $tok;
            return $tok;
        }
        while ($this->_skipComment())
        {
            $this->skipBlanks();
            if ($this->atEnd())
            {
                $tok = new Token(TOKENTYPE_EOF, "", $this->pos, [], null);
                $this->_lastReadToken = $tok;
                return $tok;
            }
            if ($this->_eofToken !== "" && $this->peek() === $this->_eofToken && !(($this->_parserState & PARSERSTATEFLAGS_PST_CASEPAT) !== 0) && !(($this->_parserState & PARSERSTATEFLAGS_PST_EOFTOKEN) !== 0))
            {
                $tok = new Token(TOKENTYPE_EOF, "", $this->pos, [], null);
                $this->_lastReadToken = $tok;
                return $tok;
            }
        }
        $tok = $this->_readOperator();
        if ($tok !== null)
        {
            $this->_lastReadToken = $tok;
            return $tok;
        }
        $tok = $this->_readWord();
        if ($tok !== null)
        {
            $this->_lastReadToken = $tok;
            return $tok;
        }
        $tok = new Token(TOKENTYPE_EOF, "", $this->pos, [], null);
        $this->_lastReadToken = $tok;
        return $tok;
    }

    public function peekToken(): ?Token
    {
        if ($this->_tokenCache === null)
        {
            $savedLast = $this->_lastReadToken;
            $this->_tokenCache = $this->nextToken();
            $this->_lastReadToken = $savedLast;
        }
        return $this->_tokenCache;
    }

    public function _readAnsiCQuote(): array
    {
        if ($this->atEnd() || $this->peek() !== "\$")
        {
            return [null, ""];
        }
        if ($this->pos + 1 >= $this->length || (string)(mb_substr($this->source, $this->pos + 1, 1)) !== "'")
        {
            return [null, ""];
        }
        $start = $this->pos;
        $this->advance();
        $this->advance();
        $contentChars = [];
        $foundClose = false;
        while (!$this->atEnd())
        {
            $ch = $this->peek();
            if ($ch === "'")
            {
                $this->advance();
                $foundClose = true;
                break;
            }
            else
            {
                if ($ch === "\\")
                {
                    array_push($contentChars, $this->advance());
                    if (!$this->atEnd())
                    {
                        array_push($contentChars, $this->advance());
                    }
                }
                else
                {
                    array_push($contentChars, $this->advance());
                }
            }
        }
        if (!$foundClose)
        {
            throw new Matchedpairerror("unexpected EOF while looking for matching `''");
        }
        $text = _substring($this->source, $start, $this->pos);
        $content = implode("", $contentChars);
        $node = new Ansicquote($content, "ansi-c");
        return [$node, $text];
    }

    public function _syncToParser(): void
    {
        if ($this->_parser !== null)
        {
            $this->_parser->pos = $this->pos;
        }
    }

    public function _syncFromParser(): void
    {
        if ($this->_parser !== null)
        {
            $this->pos = $this->_parser->pos;
        }
    }

    public function _readLocaleString(): array
    {
        if ($this->atEnd() || $this->peek() !== "\$")
        {
            return [null, "", []];
        }
        if ($this->pos + 1 >= $this->length || (string)(mb_substr($this->source, $this->pos + 1, 1)) !== "\"")
        {
            return [null, "", []];
        }
        $start = $this->pos;
        $this->advance();
        $this->advance();
        $contentChars = [];
        $innerParts = [];
        $foundClose = false;
        while (!$this->atEnd())
        {
            $ch = $this->peek();
            if ($ch === "\"")
            {
                $this->advance();
                $foundClose = true;
                break;
            }
            else
            {
                if ($ch === "\\" && $this->pos + 1 < $this->length)
                {
                    $nextCh = (string)(mb_substr($this->source, $this->pos + 1, 1));
                    if ($nextCh === "\n")
                    {
                        $this->advance();
                        $this->advance();
                    }
                    else
                    {
                        array_push($contentChars, $this->advance());
                        array_push($contentChars, $this->advance());
                    }
                }
                else
                {
                    $cmdsubNode = null;
                    $cmdsubText = "";
                    if ($ch === "\$" && $this->pos + 2 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "(" && (string)(mb_substr($this->source, $this->pos + 2, 1)) === "(")
                    {
                        $this->_syncToParser();
                        [$arithNode, $arithText] = $this->_parser->_parseArithmeticExpansion();
                        $this->_syncFromParser();
                        if ($arithNode !== null)
                        {
                            array_push($innerParts, $arithNode);
                            array_push($contentChars, $arithText);
                        }
                        else
                        {
                            $this->_syncToParser();
                            [$cmdsubNode, $cmdsubText] = $this->_parser->_parseCommandSubstitution();
                            $this->_syncFromParser();
                            if ($cmdsubNode !== null)
                            {
                                array_push($innerParts, $cmdsubNode);
                                array_push($contentChars, $cmdsubText);
                            }
                            else
                            {
                                array_push($contentChars, $this->advance());
                            }
                        }
                    }
                    else
                    {
                        if (_isExpansionStart($this->source, $this->pos, "\$("))
                        {
                            $this->_syncToParser();
                            [$cmdsubNode, $cmdsubText] = $this->_parser->_parseCommandSubstitution();
                            $this->_syncFromParser();
                            if ($cmdsubNode !== null)
                            {
                                array_push($innerParts, $cmdsubNode);
                                array_push($contentChars, $cmdsubText);
                            }
                            else
                            {
                                array_push($contentChars, $this->advance());
                            }
                        }
                        else
                        {
                            if ($ch === "\$")
                            {
                                $this->_syncToParser();
                                [$paramNode, $paramText] = $this->_parser->_parseParamExpansion(false);
                                $this->_syncFromParser();
                                if ($paramNode !== null)
                                {
                                    array_push($innerParts, $paramNode);
                                    array_push($contentChars, $paramText);
                                }
                                else
                                {
                                    array_push($contentChars, $this->advance());
                                }
                            }
                            else
                            {
                                if ($ch === "`")
                                {
                                    $this->_syncToParser();
                                    [$cmdsubNode, $cmdsubText] = $this->_parser->_parseBacktickSubstitution();
                                    $this->_syncFromParser();
                                    if ($cmdsubNode !== null)
                                    {
                                        array_push($innerParts, $cmdsubNode);
                                        array_push($contentChars, $cmdsubText);
                                    }
                                    else
                                    {
                                        array_push($contentChars, $this->advance());
                                    }
                                }
                                else
                                {
                                    array_push($contentChars, $this->advance());
                                }
                            }
                        }
                    }
                }
            }
        }
        if (!$foundClose)
        {
            $this->pos = $start;
            return [null, "", []];
        }
        $content = implode("", $contentChars);
        $text = "\$\"" . $content . "\"";
        return [new Localestring($content, "locale"), $text, $innerParts];
    }

    public function _updateDolbraceForOp(string $op, bool $hasParam): void
    {
        if ($this->_dolbraceState === DOLBRACESTATE_NONE)
        {
            return;
        }
        if ($op === "" || mb_strlen($op) === 0)
        {
            return;
        }
        $firstChar = (string)(mb_substr($op, 0, 1));
        if ($this->_dolbraceState === DOLBRACESTATE_PARAM && $hasParam)
        {
            if ((str_contains("%#^,", $firstChar)))
            {
                $this->_dolbraceState = DOLBRACESTATE_QUOTE;
                return;
            }
            if ($firstChar === "/")
            {
                $this->_dolbraceState = DOLBRACESTATE_QUOTE2;
                return;
            }
        }
        if ($this->_dolbraceState === DOLBRACESTATE_PARAM)
        {
            if ((str_contains("#%^,~:-=?+/", $firstChar)))
            {
                $this->_dolbraceState = DOLBRACESTATE_OP;
            }
        }
    }

    public function _consumeParamOperator(): string
    {
        if ($this->atEnd())
        {
            return "";
        }
        $ch = $this->peek();
        $nextCh = "";
        if ($ch === ":")
        {
            $this->advance();
            if ($this->atEnd())
            {
                return ":";
            }
            $nextCh = $this->peek();
            if (_isSimpleParamOp($nextCh))
            {
                $this->advance();
                return ":" . $nextCh;
            }
            return ":";
        }
        if (_isSimpleParamOp($ch))
        {
            $this->advance();
            return $ch;
        }
        if ($ch === "#")
        {
            $this->advance();
            if (!$this->atEnd() && $this->peek() === "#")
            {
                $this->advance();
                return "##";
            }
            return "#";
        }
        if ($ch === "%")
        {
            $this->advance();
            if (!$this->atEnd() && $this->peek() === "%")
            {
                $this->advance();
                return "%%";
            }
            return "%";
        }
        if ($ch === "/")
        {
            $this->advance();
            if (!$this->atEnd())
            {
                $nextCh = $this->peek();
                if ($nextCh === "/")
                {
                    $this->advance();
                    return "//";
                }
                else
                {
                    if ($nextCh === "#")
                    {
                        $this->advance();
                        return "/#";
                    }
                    else
                    {
                        if ($nextCh === "%")
                        {
                            $this->advance();
                            return "/%";
                        }
                    }
                }
            }
            return "/";
        }
        if ($ch === "^")
        {
            $this->advance();
            if (!$this->atEnd() && $this->peek() === "^")
            {
                $this->advance();
                return "^^";
            }
            return "^";
        }
        if ($ch === ",")
        {
            $this->advance();
            if (!$this->atEnd() && $this->peek() === ",")
            {
                $this->advance();
                return ",,";
            }
            return ",";
        }
        if ($ch === "@")
        {
            $this->advance();
            return "@";
        }
        return "";
    }

    public function _paramSubscriptHasClose(int $startPos): bool
    {
        $depth = 1;
        $i = $startPos + 1;
        $quote = newQuoteState();
        while ($i < $this->length)
        {
            $c = (string)(mb_substr($this->source, $i, 1));
            if ($quote->single)
            {
                if ($c === "'")
                {
                    $quote->single = false;
                }
                $i += 1;
                continue;
            }
            if ($quote->double)
            {
                if ($c === "\\" && $i + 1 < $this->length)
                {
                    $i += 2;
                    continue;
                }
                if ($c === "\"")
                {
                    $quote->double = false;
                }
                $i += 1;
                continue;
            }
            if ($c === "'")
            {
                $quote->single = true;
                $i += 1;
                continue;
            }
            if ($c === "\"")
            {
                $quote->double = true;
                $i += 1;
                continue;
            }
            if ($c === "\\")
            {
                $i += 2;
                continue;
            }
            if ($c === "}")
            {
                return false;
            }
            if ($c === "[")
            {
                $depth += 1;
            }
            else
            {
                if ($c === "]")
                {
                    $depth -= 1;
                    if ($depth === 0)
                    {
                        return true;
                    }
                }
            }
            $i += 1;
        }
        return false;
    }

    public function _consumeParamName(): string
    {
        if ($this->atEnd())
        {
            return "";
        }
        $ch = $this->peek();
        if (_isSpecialParam($ch))
        {
            if ($ch === "\$" && $this->pos + 1 < $this->length && ((str_contains("{'\"", (string)(mb_substr($this->source, $this->pos + 1, 1))))))
            {
                return "";
            }
            $this->advance();
            return $ch;
        }
        if (ctype_digit($ch))
        {
            $nameChars = [];
            while (!$this->atEnd() && ctype_digit($this->peek()))
            {
                array_push($nameChars, $this->advance());
            }
            return implode("", $nameChars);
        }
        if (ctype_alpha($ch) || $ch === "_")
        {
            $nameChars = [];
            while (!$this->atEnd())
            {
                $c = $this->peek();
                if (ctype_alnum($c) || $c === "_")
                {
                    array_push($nameChars, $this->advance());
                }
                else
                {
                    if ($c === "[")
                    {
                        if (!$this->_paramSubscriptHasClose($this->pos))
                        {
                            break;
                        }
                        array_push($nameChars, $this->advance());
                        $content = $this->_parseMatchedPair("[", "]", MATCHEDPAIRFLAGS_ARRAYSUB, false);
                        array_push($nameChars, $content);
                        array_push($nameChars, "]");
                        break;
                    }
                    else
                    {
                        break;
                    }
                }
            }
            if ((count($nameChars) > 0))
            {
                return implode("", $nameChars);
            }
            else
            {
                return "";
            }
        }
        return "";
    }

    public function _readParamExpansion(bool $inDquote): array
    {
        if ($this->atEnd() || $this->peek() !== "\$")
        {
            return [null, ""];
        }
        $start = $this->pos;
        $this->advance();
        if ($this->atEnd())
        {
            $this->pos = $start;
            return [null, ""];
        }
        $ch = $this->peek();
        if ($ch === "{")
        {
            $this->advance();
            return $this->_readBracedParam($start, $inDquote);
        }
        $text = "";
        if (_isSpecialParamUnbraced($ch) || _isDigit($ch) || $ch === "#")
        {
            $this->advance();
            $text = _substring($this->source, $start, $this->pos);
            return [new Paramexpansion($ch, "", "", "param"), $text];
        }
        if (ctype_alpha($ch) || $ch === "_")
        {
            $nameStart = $this->pos;
            while (!$this->atEnd())
            {
                $c = $this->peek();
                if (ctype_alnum($c) || $c === "_")
                {
                    $this->advance();
                }
                else
                {
                    break;
                }
            }
            $name = _substring($this->source, $nameStart, $this->pos);
            $text = _substring($this->source, $start, $this->pos);
            return [new Paramexpansion($name, "", "", "param"), $text];
        }
        $this->pos = $start;
        return [null, ""];
    }

    public function _readBracedParam(int $start, bool $inDquote): array
    {
        if ($this->atEnd())
        {
            throw new Matchedpairerror("unexpected EOF looking for `}'");
        }
        $savedDolbrace = $this->_dolbraceState;
        $this->_dolbraceState = DOLBRACESTATE_PARAM;
        $ch = $this->peek();
        if (_isFunsubChar($ch))
        {
            $this->_dolbraceState = $savedDolbrace;
            return $this->_readFunsub($start);
        }
        $param = "";
        $text = "";
        if ($ch === "#")
        {
            $this->advance();
            $param = $this->_consumeParamName();
            if (($param !== '') && !$this->atEnd() && $this->peek() === "}")
            {
                $this->advance();
                $text = _substring($this->source, $start, $this->pos);
                $this->_dolbraceState = $savedDolbrace;
                return [new Paramlength($param, "param-len"), $text];
            }
            $this->pos = $start + 2;
        }
        $op = "";
        $arg = "";
        if ($ch === "!")
        {
            $this->advance();
            while (!$this->atEnd() && _isWhitespaceNoNewline($this->peek()))
            {
                $this->advance();
            }
            $param = $this->_consumeParamName();
            if (($param !== ''))
            {
                while (!$this->atEnd() && _isWhitespaceNoNewline($this->peek()))
                {
                    $this->advance();
                }
                if (!$this->atEnd() && $this->peek() === "}")
                {
                    $this->advance();
                    $text = _substring($this->source, $start, $this->pos);
                    $this->_dolbraceState = $savedDolbrace;
                    return [new Paramindirect($param, "", "", "param-indirect"), $text];
                }
                if (!$this->atEnd() && _isAtOrStar($this->peek()))
                {
                    $suffix = $this->advance();
                    $trailing = $this->_parseMatchedPair("{", "}", MATCHEDPAIRFLAGS_DOLBRACE, false);
                    $text = _substring($this->source, $start, $this->pos);
                    $this->_dolbraceState = $savedDolbrace;
                    return [new Paramindirect($param . $suffix . $trailing, "", "", "param-indirect"), $text];
                }
                $op = $this->_consumeParamOperator();
                if ($op === "" && !$this->atEnd() && ((!str_contains("}\"'`", $this->peek()))))
                {
                    $op = $this->advance();
                }
                if ($op !== "" && ((!str_contains("\"'`", $op))))
                {
                    $arg = $this->_parseMatchedPair("{", "}", MATCHEDPAIRFLAGS_DOLBRACE, false);
                    $text = _substring($this->source, $start, $this->pos);
                    $this->_dolbraceState = $savedDolbrace;
                    return [new Paramindirect($param, $op, $arg, "param-indirect"), $text];
                }
                if ($this->atEnd())
                {
                    $this->_dolbraceState = $savedDolbrace;
                    throw new Matchedpairerror("unexpected EOF looking for `}'");
                }
                $this->pos = $start + 2;
            }
            else
            {
                $this->pos = $start + 2;
            }
        }
        $param = $this->_consumeParamName();
        if (!($param !== ''))
        {
            if (!$this->atEnd() && (((str_contains("-=+?", $this->peek()))) || $this->peek() === ":" && $this->pos + 1 < $this->length && _isSimpleParamOp((string)(mb_substr($this->source, $this->pos + 1, 1)))))
            {
                $param = "";
            }
            else
            {
                $content = $this->_parseMatchedPair("{", "}", MATCHEDPAIRFLAGS_DOLBRACE, false);
                $text = "\${" . $content . "}";
                $this->_dolbraceState = $savedDolbrace;
                return [new Paramexpansion($content, "", "", "param"), $text];
            }
        }
        if ($this->atEnd())
        {
            $this->_dolbraceState = $savedDolbrace;
            throw new Matchedpairerror("unexpected EOF looking for `}'");
        }
        if ($this->peek() === "}")
        {
            $this->advance();
            $text = _substring($this->source, $start, $this->pos);
            $this->_dolbraceState = $savedDolbrace;
            return [new Paramexpansion($param, "", "", "param"), $text];
        }
        $op = $this->_consumeParamOperator();
        if ($op === "")
        {
            if (!$this->atEnd() && $this->peek() === "\$" && $this->pos + 1 < $this->length && ((string)(mb_substr($this->source, $this->pos + 1, 1)) === "\"" || (string)(mb_substr($this->source, $this->pos + 1, 1)) === "'"))
            {
                $dollarCount = 1 + _countConsecutiveDollarsBefore($this->source, $this->pos);
                if ($dollarCount % 2 === 1)
                {
                    $op = "";
                }
                else
                {
                    $op = $this->advance();
                }
            }
            else
            {
                if (!$this->atEnd() && $this->peek() === "`")
                {
                    $backtickPos = $this->pos;
                    $this->advance();
                    while (!$this->atEnd() && $this->peek() !== "`")
                    {
                        $bc = $this->peek();
                        if ($bc === "\\" && $this->pos + 1 < $this->length)
                        {
                            $nextC = (string)(mb_substr($this->source, $this->pos + 1, 1));
                            if (_isEscapeCharInBacktick($nextC))
                            {
                                $this->advance();
                            }
                        }
                        $this->advance();
                    }
                    if ($this->atEnd())
                    {
                        $this->_dolbraceState = $savedDolbrace;
                        throw new Parseerror_("Unterminated backtick");
                    }
                    $this->advance();
                    $op = "`";
                }
                else
                {
                    if (!$this->atEnd() && $this->peek() === "\$" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "{")
                    {
                        $op = "";
                    }
                    else
                    {
                        if (!$this->atEnd() && ($this->peek() === "'" || $this->peek() === "\""))
                        {
                            $op = "";
                        }
                        else
                        {
                            if (!$this->atEnd() && $this->peek() === "\\")
                            {
                                $op = $this->advance();
                                if (!$this->atEnd())
                                {
                                    $op .= $this->advance();
                                }
                            }
                            else
                            {
                                $op = $this->advance();
                            }
                        }
                    }
                }
            }
        }
        $this->_updateDolbraceForOp($op, mb_strlen($param) > 0);
        try
        {
            $flags = ($inDquote ? MATCHEDPAIRFLAGS_DQUOTE : MATCHEDPAIRFLAGS_NONE);
            $paramEndsWithDollar = $param !== "" && str_ends_with($param, "\$");
            $arg = $this->_collectParamArgument($flags, $paramEndsWithDollar);
        } catch (Matchedpairerror $e)
        {
            $this->_dolbraceState = $savedDolbrace;
            throw $e;
        }
        if (($op === "<" || $op === ">") && str_starts_with($arg, "(") && str_ends_with($arg, ")"))
        {
            $inner = mb_substr($arg, 1, (mb_strlen($arg) - 1) - (1));
            try
            {
                $subParser = newParser($inner, true, $this->_parser->_extglob);
                $parsed = $subParser->parseList(true);
                if ($parsed !== null && $subParser->atEnd())
                {
                    $formatted = _formatCmdsubNode($parsed, 0, true, false, true);
                    $arg = "(" . $formatted . ")";
                }
            } catch (Exception_ $ex)
            {
            }
        }
        $text = "\${" . $param . $op . $arg . "}";
        $this->_dolbraceState = $savedDolbrace;
        return [new Paramexpansion($param, $op, $arg, "param"), $text];
    }

    public function _readFunsub(int $start): array
    {
        return $this->_parser->_parseFunsub($start);
    }
}

class Word implements Node
{
    public string $value;
    public ?array $parts;
    public string $kind;

    public function __construct(string $value, ?array $parts, string $kind)
    {
        $this->value = $value;
        $this->parts = $parts ?? [];
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        $value = $this->value;
        $value = $this->_expandAllAnsiCQuotes($value);
        $value = $this->_stripLocaleStringDollars($value);
        $value = $this->_normalizeArrayWhitespace($value);
        $value = $this->_formatCommandSubstitutions($value, false);
        $value = $this->_normalizeParamExpansionNewlines($value);
        $value = $this->_stripArithLineContinuations($value);
        $value = $this->_doubleCtlescSmart($value);
        $value = str_replace("", "", $value);
        $value = str_replace("\\", "\\\\", $value);
        if (str_ends_with($value, "\\\\") && !str_ends_with($value, "\\\\\\\\"))
        {
            $value = $value . "\\\\";
        }
        $escaped = str_replace("\t", "\\t", str_replace("\n", "\\n", str_replace("\"", "\\\"", $value)));
        return "(word \"" . $escaped . "\")";
    }

    public function _appendWithCtlesc(?array &$result, int $byteVal): void
    {
        array_push($result, $byteVal);
    }

    public function _doubleCtlescSmart(string $value): string
    {
        $result = [];
        $quote = newQuoteState();
        foreach (mb_str_split($value) as $c)
        {
            if ($c === "'" && !$quote->double)
            {
                $quote->single = !$quote->single;
            }
            else
            {
                if ($c === "\"" && !$quote->single)
                {
                    $quote->double = !$quote->double;
                }
            }
            array_push($result, $c);
            if ($c === "")
            {
                if ($quote->double)
                {
                    $bsCount = 0;
                    for ($j = count($result) - 2; $j > -1; $j += -1)
                    {
                        if ($result[$j] === "\\")
                        {
                            $bsCount += 1;
                        }
                        else
                        {
                            break;
                        }
                    }
                    if ($bsCount % 2 === 0)
                    {
                        array_push($result, "");
                    }
                }
                else
                {
                    array_push($result, "");
                }
            }
        }
        return implode("", $result);
    }

    public function _normalizeParamExpansionNewlines(string $value): string
    {
        $result = [];
        $i = 0;
        $quote = newQuoteState();
        while ($i < mb_strlen($value))
        {
            $c = (string)(mb_substr($value, $i, 1));
            if ($c === "'" && !$quote->double)
            {
                $quote->single = !$quote->single;
                array_push($result, $c);
                $i += 1;
            }
            else
            {
                if ($c === "\"" && !$quote->single)
                {
                    $quote->double = !$quote->double;
                    array_push($result, $c);
                    $i += 1;
                }
                else
                {
                    if (_isExpansionStart($value, $i, "\${") && !$quote->single)
                    {
                        array_push($result, "\$");
                        array_push($result, "{");
                        $i += 2;
                        $hadLeadingNewline = $i < mb_strlen($value) && (string)(mb_substr($value, $i, 1)) === "\n";
                        if ($hadLeadingNewline)
                        {
                            array_push($result, " ");
                            $i += 1;
                        }
                        $depth = 1;
                        while ($i < mb_strlen($value) && $depth > 0)
                        {
                            $ch = (string)(mb_substr($value, $i, 1));
                            if ($ch === "\\" && $i + 1 < mb_strlen($value) && !$quote->single)
                            {
                                if ((string)(mb_substr($value, $i + 1, 1)) === "\n")
                                {
                                    $i += 2;
                                    continue;
                                }
                                array_push($result, $ch);
                                array_push($result, (string)(mb_substr($value, $i + 1, 1)));
                                $i += 2;
                                continue;
                            }
                            if ($ch === "'" && !$quote->double)
                            {
                                $quote->single = !$quote->single;
                            }
                            else
                            {
                                if ($ch === "\"" && !$quote->single)
                                {
                                    $quote->double = !$quote->double;
                                }
                                else
                                {
                                    if (!$quote->inQuotes())
                                    {
                                        if ($ch === "{")
                                        {
                                            $depth += 1;
                                        }
                                        else
                                        {
                                            if ($ch === "}")
                                            {
                                                $depth -= 1;
                                                if ($depth === 0)
                                                {
                                                    if ($hadLeadingNewline)
                                                    {
                                                        array_push($result, " ");
                                                    }
                                                    array_push($result, $ch);
                                                    $i += 1;
                                                    break;
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            array_push($result, $ch);
                            $i += 1;
                        }
                    }
                    else
                    {
                        array_push($result, $c);
                        $i += 1;
                    }
                }
            }
        }
        return implode("", $result);
    }

    public function _shSingleQuote(string $s): string
    {
        if (!($s !== ''))
        {
            return "''";
        }
        if ($s === "'")
        {
            return "\\'";
        }
        $result = ["'"];
        foreach (mb_str_split($s) as $c)
        {
            if ($c === "'")
            {
                array_push($result, "'\\''");
            }
            else
            {
                array_push($result, $c);
            }
        }
        array_push($result, "'");
        return implode("", $result);
    }

    public function _ansiCToBytes(string $inner): ?array
    {
        $result = [];
        $i = 0;
        while ($i < mb_strlen($inner))
        {
            if ((string)(mb_substr($inner, $i, 1)) === "\\" && $i + 1 < mb_strlen($inner))
            {
                $c = (string)(mb_substr($inner, $i + 1, 1));
                $simple = _getAnsiEscape($c);
                if ($simple >= 0)
                {
                    array_push($result, $simple);
                    $i += 2;
                }
                else
                {
                    if ($c === "'")
                    {
                        array_push($result, 39);
                        $i += 2;
                    }
                    else
                    {
                        $j = 0;
                        $byteVal = 0;
                        if ($c === "x")
                        {
                            if ($i + 2 < mb_strlen($inner) && (string)(mb_substr($inner, $i + 2, 1)) === "{")
                            {
                                $j = $i + 3;
                                while ($j < mb_strlen($inner) && _isHexDigit((string)(mb_substr($inner, $j, 1))))
                                {
                                    $j += 1;
                                }
                                $hexStr = _substring($inner, $i + 3, $j);
                                if ($j < mb_strlen($inner) && (string)(mb_substr($inner, $j, 1)) === "}")
                                {
                                    $j += 1;
                                }
                                if (!($hexStr !== ''))
                                {
                                    return $result;
                                }
                                $byteVal = (intval($hexStr, 16) & 255);
                                if ($byteVal === 0)
                                {
                                    return $result;
                                }
                                $this->_appendWithCtlesc($result, $byteVal);
                                $i = $j;
                            }
                            else
                            {
                                $j = $i + 2;
                                while ($j < mb_strlen($inner) && $j < $i + 4 && _isHexDigit((string)(mb_substr($inner, $j, 1))))
                                {
                                    $j += 1;
                                }
                                if ($j > $i + 2)
                                {
                                    $byteVal = intval(_substring($inner, $i + 2, $j), 16);
                                    if ($byteVal === 0)
                                    {
                                        return $result;
                                    }
                                    $this->_appendWithCtlesc($result, $byteVal);
                                    $i = $j;
                                }
                                else
                                {
                                    array_push($result, mb_ord(mb_substr((string)(mb_substr($inner, $i, 1)), 0, 1)));
                                    $i += 1;
                                }
                            }
                        }
                        else
                        {
                            $codepoint = 0;
                            if ($c === "u")
                            {
                                $j = $i + 2;
                                while ($j < mb_strlen($inner) && $j < $i + 6 && _isHexDigit((string)(mb_substr($inner, $j, 1))))
                                {
                                    $j += 1;
                                }
                                if ($j > $i + 2)
                                {
                                    $codepoint = intval(_substring($inner, $i + 2, $j), 16);
                                    if ($codepoint === 0)
                                    {
                                        return $result;
                                    }
                                    array_push($result, ...array_values(unpack('C*', mb_chr($codepoint))));
                                    $i = $j;
                                }
                                else
                                {
                                    array_push($result, mb_ord(mb_substr((string)(mb_substr($inner, $i, 1)), 0, 1)));
                                    $i += 1;
                                }
                            }
                            else
                            {
                                if ($c === "U")
                                {
                                    $j = $i + 2;
                                    while ($j < mb_strlen($inner) && $j < $i + 10 && _isHexDigit((string)(mb_substr($inner, $j, 1))))
                                    {
                                        $j += 1;
                                    }
                                    if ($j > $i + 2)
                                    {
                                        $codepoint = intval(_substring($inner, $i + 2, $j), 16);
                                        if ($codepoint === 0)
                                        {
                                            return $result;
                                        }
                                        array_push($result, ...array_values(unpack('C*', mb_chr($codepoint))));
                                        $i = $j;
                                    }
                                    else
                                    {
                                        array_push($result, mb_ord(mb_substr((string)(mb_substr($inner, $i, 1)), 0, 1)));
                                        $i += 1;
                                    }
                                }
                                else
                                {
                                    if ($c === "c")
                                    {
                                        if ($i + 3 <= mb_strlen($inner))
                                        {
                                            $ctrlChar = (string)(mb_substr($inner, $i + 2, 1));
                                            $skipExtra = 0;
                                            if ($ctrlChar === "\\" && $i + 4 <= mb_strlen($inner) && (string)(mb_substr($inner, $i + 3, 1)) === "\\")
                                            {
                                                $skipExtra = 1;
                                            }
                                            $ctrlVal = (mb_ord(mb_substr($ctrlChar, 0, 1)) & 31);
                                            if ($ctrlVal === 0)
                                            {
                                                return $result;
                                            }
                                            $this->_appendWithCtlesc($result, $ctrlVal);
                                            $i += 3 + $skipExtra;
                                        }
                                        else
                                        {
                                            array_push($result, mb_ord(mb_substr((string)(mb_substr($inner, $i, 1)), 0, 1)));
                                            $i += 1;
                                        }
                                    }
                                    else
                                    {
                                        if ($c === "0")
                                        {
                                            $j = $i + 2;
                                            while ($j < mb_strlen($inner) && $j < $i + 4 && _isOctalDigit((string)(mb_substr($inner, $j, 1))))
                                            {
                                                $j += 1;
                                            }
                                            if ($j > $i + 2)
                                            {
                                                $byteVal = (intval(_substring($inner, $i + 1, $j), 8) & 255);
                                                if ($byteVal === 0)
                                                {
                                                    return $result;
                                                }
                                                $this->_appendWithCtlesc($result, $byteVal);
                                                $i = $j;
                                            }
                                            else
                                            {
                                                return $result;
                                            }
                                        }
                                        else
                                        {
                                            if ($c >= "1" && $c <= "7")
                                            {
                                                $j = $i + 1;
                                                while ($j < mb_strlen($inner) && $j < $i + 4 && _isOctalDigit((string)(mb_substr($inner, $j, 1))))
                                                {
                                                    $j += 1;
                                                }
                                                $byteVal = (intval(_substring($inner, $i + 1, $j), 8) & 255);
                                                if ($byteVal === 0)
                                                {
                                                    return $result;
                                                }
                                                $this->_appendWithCtlesc($result, $byteVal);
                                                $i = $j;
                                            }
                                            else
                                            {
                                                array_push($result, 92);
                                                array_push($result, mb_ord(mb_substr($c, 0, 1)));
                                                $i += 2;
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
                array_push($result, ...array_values(unpack('C*', (string)(mb_substr($inner, $i, 1)))));
                $i += 1;
            }
        }
        return $result;
    }

    public function _expandAnsiCEscapes(string $value): string
    {
        if (!(str_starts_with($value, "'") && str_ends_with($value, "'")))
        {
            return $value;
        }
        $inner = _substring($value, 1, mb_strlen($value) - 1);
        $literalBytes = $this->_ansiCToBytes($inner);
        $literalStr = UConverter::transcode(pack('C*', ...$literalBytes), 'UTF-8', 'UTF-8');
        return $this->_shSingleQuote($literalStr);
    }

    public function _expandAllAnsiCQuotes(string $value): string
    {
        $result = [];
        $i = 0;
        $quote = newQuoteState();
        $inBacktick = false;
        $braceDepth = 0;
        while ($i < mb_strlen($value))
        {
            $ch = (string)(mb_substr($value, $i, 1));
            if ($ch === "`" && !$quote->single)
            {
                $inBacktick = !$inBacktick;
                array_push($result, $ch);
                $i += 1;
                continue;
            }
            if ($inBacktick)
            {
                if ($ch === "\\" && $i + 1 < mb_strlen($value))
                {
                    array_push($result, $ch);
                    array_push($result, (string)(mb_substr($value, $i + 1, 1)));
                    $i += 2;
                }
                else
                {
                    array_push($result, $ch);
                    $i += 1;
                }
                continue;
            }
            if (!$quote->single)
            {
                if (_isExpansionStart($value, $i, "\${"))
                {
                    $braceDepth += 1;
                    $quote->push();
                    array_push($result, "\${");
                    $i += 2;
                    continue;
                }
                else
                {
                    if ($ch === "}" && $braceDepth > 0 && !$quote->double)
                    {
                        $braceDepth -= 1;
                        array_push($result, $ch);
                        $quote->pop();
                        $i += 1;
                        continue;
                    }
                }
            }
            $effectiveInDquote = $quote->double;
            if ($ch === "'" && !$effectiveInDquote)
            {
                $isAnsiC = !$quote->single && $i > 0 && (string)(mb_substr($value, $i - 1, 1)) === "\$" && _countConsecutiveDollarsBefore($value, $i - 1) % 2 === 0;
                if (!$isAnsiC)
                {
                    $quote->single = !$quote->single;
                }
                array_push($result, $ch);
                $i += 1;
            }
            else
            {
                if ($ch === "\"" && !$quote->single)
                {
                    $quote->double = !$quote->double;
                    array_push($result, $ch);
                    $i += 1;
                }
                else
                {
                    if ($ch === "\\" && $i + 1 < mb_strlen($value) && !$quote->single)
                    {
                        array_push($result, $ch);
                        array_push($result, (string)(mb_substr($value, $i + 1, 1)));
                        $i += 2;
                    }
                    else
                    {
                        if (_startsWithAt($value, $i, "\$'") && !$quote->single && !$effectiveInDquote && _countConsecutiveDollarsBefore($value, $i) % 2 === 0)
                        {
                            $j = $i + 2;
                            while ($j < mb_strlen($value))
                            {
                                if ((string)(mb_substr($value, $j, 1)) === "\\" && $j + 1 < mb_strlen($value))
                                {
                                    $j += 2;
                                }
                                else
                                {
                                    if ((string)(mb_substr($value, $j, 1)) === "'")
                                    {
                                        $j += 1;
                                        break;
                                    }
                                    else
                                    {
                                        $j += 1;
                                    }
                                }
                            }
                            $ansiStr = _substring($value, $i, $j);
                            $expanded = $this->_expandAnsiCEscapes(_substring($ansiStr, 1, mb_strlen($ansiStr)));
                            $outerInDquote = $quote->outerDouble();
                            if ($braceDepth > 0 && $outerInDquote && str_starts_with($expanded, "'") && str_ends_with($expanded, "'"))
                            {
                                $inner = _substring($expanded, 1, mb_strlen($expanded) - 1);
                                if ((mb_strpos($inner, "") === false ? -1 : mb_strpos($inner, "")) === -1)
                                {
                                    $resultStr = implode("", $result);
                                    $inPattern = false;
                                    $lastBraceIdx = (mb_strrpos($resultStr, "\${") === false ? -1 : mb_strrpos($resultStr, "\${"));
                                    if ($lastBraceIdx >= 0)
                                    {
                                        $afterBrace = mb_substr($resultStr, $lastBraceIdx + 2);
                                        $varNameLen = 0;
                                        if (($afterBrace !== ''))
                                        {
                                            if ((str_contains("@*#?-\$!0123456789_", (string)(mb_substr($afterBrace, 0, 1)))))
                                            {
                                                $varNameLen = 1;
                                            }
                                            else
                                            {
                                                if (ctype_alpha((string)(mb_substr($afterBrace, 0, 1))) || (string)(mb_substr($afterBrace, 0, 1)) === "_")
                                                {
                                                    while ($varNameLen < mb_strlen($afterBrace))
                                                    {
                                                        $c = (string)(mb_substr($afterBrace, $varNameLen, 1));
                                                        if (!(ctype_alnum($c) || $c === "_"))
                                                        {
                                                            break;
                                                        }
                                                        $varNameLen += 1;
                                                    }
                                                }
                                            }
                                        }
                                        if ($varNameLen > 0 && $varNameLen < mb_strlen($afterBrace) && ((!str_contains("#?-", (string)(mb_substr($afterBrace, 0, 1))))))
                                        {
                                            $opStart = mb_substr($afterBrace, $varNameLen);
                                            if (str_starts_with($opStart, "@") && mb_strlen($opStart) > 1)
                                            {
                                                $opStart = mb_substr($opStart, 1);
                                            }
                                            foreach (["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"] as $op)
                                            {
                                                if (str_starts_with($opStart, $op))
                                                {
                                                    $inPattern = true;
                                                    break;
                                                }
                                            }
                                            if (!$inPattern && ($opStart !== '') && ((!str_contains("%#/^,~:+-=?", (string)(mb_substr($opStart, 0, 1))))))
                                            {
                                                foreach (["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"] as $op)
                                                {
                                                    if ((str_contains($opStart, $op)))
                                                    {
                                                        $inPattern = true;
                                                        break;
                                                    }
                                                }
                                            }
                                        }
                                        else
                                        {
                                            if ($varNameLen === 0 && mb_strlen($afterBrace) > 1)
                                            {
                                                $firstChar = (string)(mb_substr($afterBrace, 0, 1));
                                                if ((!str_contains("%#/^,", $firstChar)))
                                                {
                                                    $rest = mb_substr($afterBrace, 1);
                                                    foreach (["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"] as $op)
                                                    {
                                                        if ((str_contains($rest, $op)))
                                                        {
                                                            $inPattern = true;
                                                            break;
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                    if (!$inPattern)
                                    {
                                        $expanded = $inner;
                                    }
                                }
                            }
                            array_push($result, $expanded);
                            $i = $j;
                        }
                        else
                        {
                            array_push($result, $ch);
                            $i += 1;
                        }
                    }
                }
            }
        }
        return implode("", $result);
    }

    public function _stripLocaleStringDollars(string $value): string
    {
        $result = [];
        $i = 0;
        $braceDepth = 0;
        $bracketDepth = 0;
        $quote = newQuoteState();
        $braceQuote = newQuoteState();
        $bracketInDoubleQuote = false;
        while ($i < mb_strlen($value))
        {
            $ch = (string)(mb_substr($value, $i, 1));
            if ($ch === "\\" && $i + 1 < mb_strlen($value) && !$quote->single && !$braceQuote->single)
            {
                array_push($result, $ch);
                array_push($result, (string)(mb_substr($value, $i + 1, 1)));
                $i += 2;
            }
            else
            {
                if (_startsWithAt($value, $i, "\${") && !$quote->single && !$braceQuote->single && ($i === 0 || (string)(mb_substr($value, $i - 1, 1)) !== "\$"))
                {
                    $braceDepth += 1;
                    $braceQuote->double = false;
                    $braceQuote->single = false;
                    array_push($result, "\$");
                    array_push($result, "{");
                    $i += 2;
                }
                else
                {
                    if ($ch === "}" && $braceDepth > 0 && !$quote->single && !$braceQuote->double && !$braceQuote->single)
                    {
                        $braceDepth -= 1;
                        array_push($result, $ch);
                        $i += 1;
                    }
                    else
                    {
                        if ($ch === "[" && $braceDepth > 0 && !$quote->single && !$braceQuote->double)
                        {
                            $bracketDepth += 1;
                            $bracketInDoubleQuote = false;
                            array_push($result, $ch);
                            $i += 1;
                        }
                        else
                        {
                            if ($ch === "]" && $bracketDepth > 0 && !$quote->single && !$bracketInDoubleQuote)
                            {
                                $bracketDepth -= 1;
                                array_push($result, $ch);
                                $i += 1;
                            }
                            else
                            {
                                if ($ch === "'" && !$quote->double && $braceDepth === 0)
                                {
                                    $quote->single = !$quote->single;
                                    array_push($result, $ch);
                                    $i += 1;
                                }
                                else
                                {
                                    if ($ch === "\"" && !$quote->single && $braceDepth === 0)
                                    {
                                        $quote->double = !$quote->double;
                                        array_push($result, $ch);
                                        $i += 1;
                                    }
                                    else
                                    {
                                        if ($ch === "\"" && !$quote->single && $bracketDepth > 0)
                                        {
                                            $bracketInDoubleQuote = !$bracketInDoubleQuote;
                                            array_push($result, $ch);
                                            $i += 1;
                                        }
                                        else
                                        {
                                            if ($ch === "\"" && !$quote->single && !$braceQuote->single && $braceDepth > 0)
                                            {
                                                $braceQuote->double = !$braceQuote->double;
                                                array_push($result, $ch);
                                                $i += 1;
                                            }
                                            else
                                            {
                                                if ($ch === "'" && !$quote->double && !$braceQuote->double && $braceDepth > 0)
                                                {
                                                    $braceQuote->single = !$braceQuote->single;
                                                    array_push($result, $ch);
                                                    $i += 1;
                                                }
                                                else
                                                {
                                                    if (_startsWithAt($value, $i, "\$\"") && !$quote->single && !$braceQuote->single && ($braceDepth > 0 || $bracketDepth > 0 || !$quote->double) && !$braceQuote->double && !$bracketInDoubleQuote)
                                                    {
                                                        $dollarCount = 1 + _countConsecutiveDollarsBefore($value, $i);
                                                        if ($dollarCount % 2 === 1)
                                                        {
                                                            array_push($result, "\"");
                                                            if ($bracketDepth > 0)
                                                            {
                                                                $bracketInDoubleQuote = true;
                                                            }
                                                            else
                                                            {
                                                                if ($braceDepth > 0)
                                                                {
                                                                    $braceQuote->double = true;
                                                                }
                                                                else
                                                                {
                                                                    $quote->double = true;
                                                                }
                                                            }
                                                            $i += 2;
                                                        }
                                                        else
                                                        {
                                                            array_push($result, $ch);
                                                            $i += 1;
                                                        }
                                                    }
                                                    else
                                                    {
                                                        array_push($result, $ch);
                                                        $i += 1;
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
        return implode("", $result);
    }

    public function _normalizeArrayWhitespace(string $value): string
    {
        $i = 0;
        if (!($i < mb_strlen($value) && (ctype_alpha((string)(mb_substr($value, $i, 1))) || (string)(mb_substr($value, $i, 1)) === "_")))
        {
            return $value;
        }
        $i += 1;
        while ($i < mb_strlen($value) && (ctype_alnum((string)(mb_substr($value, $i, 1))) || (string)(mb_substr($value, $i, 1)) === "_"))
        {
            $i += 1;
        }
        while ($i < mb_strlen($value) && (string)(mb_substr($value, $i, 1)) === "[")
        {
            $depth = 1;
            $i += 1;
            while ($i < mb_strlen($value) && $depth > 0)
            {
                if ((string)(mb_substr($value, $i, 1)) === "[")
                {
                    $depth += 1;
                }
                else
                {
                    if ((string)(mb_substr($value, $i, 1)) === "]")
                    {
                        $depth -= 1;
                    }
                }
                $i += 1;
            }
            if ($depth !== 0)
            {
                return $value;
            }
        }
        if ($i < mb_strlen($value) && (string)(mb_substr($value, $i, 1)) === "+")
        {
            $i += 1;
        }
        if (!($i + 1 < mb_strlen($value) && (string)(mb_substr($value, $i, 1)) === "=" && (string)(mb_substr($value, $i + 1, 1)) === "("))
        {
            return $value;
        }
        $prefix = _substring($value, 0, $i + 1);
        $openParenPos = $i + 1;
        $closeParenPos = 0;
        if (str_ends_with($value, ")"))
        {
            $closeParenPos = mb_strlen($value) - 1;
        }
        else
        {
            $closeParenPos = $this->_findMatchingParen($value, $openParenPos);
            if ($closeParenPos < 0)
            {
                return $value;
            }
        }
        $inner = _substring($value, $openParenPos + 1, $closeParenPos);
        $suffix = _substring($value, $closeParenPos + 1, mb_strlen($value));
        $result = $this->_normalizeArrayInner($inner);
        return $prefix . "(" . $result . ")" . $suffix;
    }

    public function _findMatchingParen(string $value, int $openPos): int
    {
        if ($openPos >= mb_strlen($value) || (string)(mb_substr($value, $openPos, 1)) !== "(")
        {
            return -1;
        }
        $i = $openPos + 1;
        $depth = 1;
        $quote = newQuoteState();
        while ($i < mb_strlen($value) && $depth > 0)
        {
            $ch = (string)(mb_substr($value, $i, 1));
            if ($ch === "\\" && $i + 1 < mb_strlen($value) && !$quote->single)
            {
                $i += 2;
                continue;
            }
            if ($ch === "'" && !$quote->double)
            {
                $quote->single = !$quote->single;
                $i += 1;
                continue;
            }
            if ($ch === "\"" && !$quote->single)
            {
                $quote->double = !$quote->double;
                $i += 1;
                continue;
            }
            if ($quote->single || $quote->double)
            {
                $i += 1;
                continue;
            }
            if ($ch === "#")
            {
                while ($i < mb_strlen($value) && (string)(mb_substr($value, $i, 1)) !== "\n")
                {
                    $i += 1;
                }
                continue;
            }
            if ($ch === "(")
            {
                $depth += 1;
            }
            else
            {
                if ($ch === ")")
                {
                    $depth -= 1;
                    if ($depth === 0)
                    {
                        return $i;
                    }
                }
            }
            $i += 1;
        }
        return -1;
    }

    public function _normalizeArrayInner(string $inner): string
    {
        $normalized = [];
        $i = 0;
        $inWhitespace = true;
        $braceDepth = 0;
        $bracketDepth = 0;
        while ($i < mb_strlen($inner))
        {
            $ch = (string)(mb_substr($inner, $i, 1));
            if (_isWhitespace($ch))
            {
                if (!$inWhitespace && (count($normalized) > 0) && $braceDepth === 0 && $bracketDepth === 0)
                {
                    array_push($normalized, " ");
                    $inWhitespace = true;
                }
                if ($braceDepth > 0 || $bracketDepth > 0)
                {
                    array_push($normalized, $ch);
                }
                $i += 1;
            }
            else
            {
                $j = 0;
                if ($ch === "'")
                {
                    $inWhitespace = false;
                    $j = $i + 1;
                    while ($j < mb_strlen($inner) && (string)(mb_substr($inner, $j, 1)) !== "'")
                    {
                        $j += 1;
                    }
                    array_push($normalized, _substring($inner, $i, $j + 1));
                    $i = $j + 1;
                }
                else
                {
                    if ($ch === "\"")
                    {
                        $inWhitespace = false;
                        $j = $i + 1;
                        $dqContent = ["\""];
                        $dqBraceDepth = 0;
                        while ($j < mb_strlen($inner))
                        {
                            if ((string)(mb_substr($inner, $j, 1)) === "\\" && $j + 1 < mb_strlen($inner))
                            {
                                if ((string)(mb_substr($inner, $j + 1, 1)) === "\n")
                                {
                                    $j += 2;
                                }
                                else
                                {
                                    array_push($dqContent, (string)(mb_substr($inner, $j, 1)));
                                    array_push($dqContent, (string)(mb_substr($inner, $j + 1, 1)));
                                    $j += 2;
                                }
                            }
                            else
                            {
                                if (_isExpansionStart($inner, $j, "\${"))
                                {
                                    array_push($dqContent, "\${");
                                    $dqBraceDepth += 1;
                                    $j += 2;
                                }
                                else
                                {
                                    if ((string)(mb_substr($inner, $j, 1)) === "}" && $dqBraceDepth > 0)
                                    {
                                        array_push($dqContent, "}");
                                        $dqBraceDepth -= 1;
                                        $j += 1;
                                    }
                                    else
                                    {
                                        if ((string)(mb_substr($inner, $j, 1)) === "\"" && $dqBraceDepth === 0)
                                        {
                                            array_push($dqContent, "\"");
                                            $j += 1;
                                            break;
                                        }
                                        else
                                        {
                                            array_push($dqContent, (string)(mb_substr($inner, $j, 1)));
                                            $j += 1;
                                        }
                                    }
                                }
                            }
                        }
                        array_push($normalized, implode("", $dqContent));
                        $i = $j;
                    }
                    else
                    {
                        if ($ch === "\\" && $i + 1 < mb_strlen($inner))
                        {
                            if ((string)(mb_substr($inner, $i + 1, 1)) === "\n")
                            {
                                $i += 2;
                            }
                            else
                            {
                                $inWhitespace = false;
                                array_push($normalized, _substring($inner, $i, $i + 2));
                                $i += 2;
                            }
                        }
                        else
                        {
                            $depth = 0;
                            if (_isExpansionStart($inner, $i, "\$(("))
                            {
                                $inWhitespace = false;
                                $j = $i + 3;
                                $depth = 1;
                                while ($j < mb_strlen($inner) && $depth > 0)
                                {
                                    if ($j + 1 < mb_strlen($inner) && (string)(mb_substr($inner, $j, 1)) === "(" && (string)(mb_substr($inner, $j + 1, 1)) === "(")
                                    {
                                        $depth += 1;
                                        $j += 2;
                                    }
                                    else
                                    {
                                        if ($j + 1 < mb_strlen($inner) && (string)(mb_substr($inner, $j, 1)) === ")" && (string)(mb_substr($inner, $j + 1, 1)) === ")")
                                        {
                                            $depth -= 1;
                                            $j += 2;
                                        }
                                        else
                                        {
                                            $j += 1;
                                        }
                                    }
                                }
                                array_push($normalized, _substring($inner, $i, $j));
                                $i = $j;
                            }
                            else
                            {
                                if (_isExpansionStart($inner, $i, "\$("))
                                {
                                    $inWhitespace = false;
                                    $j = $i + 2;
                                    $depth = 1;
                                    while ($j < mb_strlen($inner) && $depth > 0)
                                    {
                                        if ((string)(mb_substr($inner, $j, 1)) === "(" && $j > 0 && (string)(mb_substr($inner, $j - 1, 1)) === "\$")
                                        {
                                            $depth += 1;
                                        }
                                        else
                                        {
                                            if ((string)(mb_substr($inner, $j, 1)) === ")")
                                            {
                                                $depth -= 1;
                                            }
                                            else
                                            {
                                                if ((string)(mb_substr($inner, $j, 1)) === "'")
                                                {
                                                    $j += 1;
                                                    while ($j < mb_strlen($inner) && (string)(mb_substr($inner, $j, 1)) !== "'")
                                                    {
                                                        $j += 1;
                                                    }
                                                }
                                                else
                                                {
                                                    if ((string)(mb_substr($inner, $j, 1)) === "\"")
                                                    {
                                                        $j += 1;
                                                        while ($j < mb_strlen($inner))
                                                        {
                                                            if ((string)(mb_substr($inner, $j, 1)) === "\\" && $j + 1 < mb_strlen($inner))
                                                            {
                                                                $j += 2;
                                                                continue;
                                                            }
                                                            if ((string)(mb_substr($inner, $j, 1)) === "\"")
                                                            {
                                                                break;
                                                            }
                                                            $j += 1;
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                        $j += 1;
                                    }
                                    array_push($normalized, _substring($inner, $i, $j));
                                    $i = $j;
                                }
                                else
                                {
                                    if (($ch === "<" || $ch === ">") && $i + 1 < mb_strlen($inner) && (string)(mb_substr($inner, $i + 1, 1)) === "(")
                                    {
                                        $inWhitespace = false;
                                        $j = $i + 2;
                                        $depth = 1;
                                        while ($j < mb_strlen($inner) && $depth > 0)
                                        {
                                            if ((string)(mb_substr($inner, $j, 1)) === "(")
                                            {
                                                $depth += 1;
                                            }
                                            else
                                            {
                                                if ((string)(mb_substr($inner, $j, 1)) === ")")
                                                {
                                                    $depth -= 1;
                                                }
                                                else
                                                {
                                                    if ((string)(mb_substr($inner, $j, 1)) === "'")
                                                    {
                                                        $j += 1;
                                                        while ($j < mb_strlen($inner) && (string)(mb_substr($inner, $j, 1)) !== "'")
                                                        {
                                                            $j += 1;
                                                        }
                                                    }
                                                    else
                                                    {
                                                        if ((string)(mb_substr($inner, $j, 1)) === "\"")
                                                        {
                                                            $j += 1;
                                                            while ($j < mb_strlen($inner))
                                                            {
                                                                if ((string)(mb_substr($inner, $j, 1)) === "\\" && $j + 1 < mb_strlen($inner))
                                                                {
                                                                    $j += 2;
                                                                    continue;
                                                                }
                                                                if ((string)(mb_substr($inner, $j, 1)) === "\"")
                                                                {
                                                                    break;
                                                                }
                                                                $j += 1;
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                            $j += 1;
                                        }
                                        array_push($normalized, _substring($inner, $i, $j));
                                        $i = $j;
                                    }
                                    else
                                    {
                                        if (_isExpansionStart($inner, $i, "\${"))
                                        {
                                            $inWhitespace = false;
                                            array_push($normalized, "\${");
                                            $braceDepth += 1;
                                            $i += 2;
                                        }
                                        else
                                        {
                                            if ($ch === "{" && $braceDepth > 0)
                                            {
                                                array_push($normalized, $ch);
                                                $braceDepth += 1;
                                                $i += 1;
                                            }
                                            else
                                            {
                                                if ($ch === "}" && $braceDepth > 0)
                                                {
                                                    array_push($normalized, $ch);
                                                    $braceDepth -= 1;
                                                    $i += 1;
                                                }
                                                else
                                                {
                                                    if ($ch === "#" && $braceDepth === 0 && $inWhitespace)
                                                    {
                                                        while ($i < mb_strlen($inner) && (string)(mb_substr($inner, $i, 1)) !== "\n")
                                                        {
                                                            $i += 1;
                                                        }
                                                    }
                                                    else
                                                    {
                                                        if ($ch === "[")
                                                        {
                                                            if ($inWhitespace || $bracketDepth > 0)
                                                            {
                                                                $bracketDepth += 1;
                                                            }
                                                            $inWhitespace = false;
                                                            array_push($normalized, $ch);
                                                            $i += 1;
                                                        }
                                                        else
                                                        {
                                                            if ($ch === "]" && $bracketDepth > 0)
                                                            {
                                                                array_push($normalized, $ch);
                                                                $bracketDepth -= 1;
                                                                $i += 1;
                                                            }
                                                            else
                                                            {
                                                                $inWhitespace = false;
                                                                array_push($normalized, $ch);
                                                                $i += 1;
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
        return rtrim(implode("", $normalized), " \t\n\r");
    }

    public function _stripArithLineContinuations(string $value): string
    {
        $result = [];
        $i = 0;
        while ($i < mb_strlen($value))
        {
            if (_isExpansionStart($value, $i, "\$(("))
            {
                $start = $i;
                $i += 3;
                $depth = 2;
                $arithContent = [];
                $firstCloseIdx = -1;
                while ($i < mb_strlen($value) && $depth > 0)
                {
                    if ((string)(mb_substr($value, $i, 1)) === "(")
                    {
                        array_push($arithContent, "(");
                        $depth += 1;
                        $i += 1;
                        if ($depth > 1)
                        {
                            $firstCloseIdx = -1;
                        }
                    }
                    else
                    {
                        if ((string)(mb_substr($value, $i, 1)) === ")")
                        {
                            if ($depth === 2)
                            {
                                $firstCloseIdx = count($arithContent);
                            }
                            $depth -= 1;
                            if ($depth > 0)
                            {
                                array_push($arithContent, ")");
                            }
                            $i += 1;
                        }
                        else
                        {
                            if ((string)(mb_substr($value, $i, 1)) === "\\" && $i + 1 < mb_strlen($value) && (string)(mb_substr($value, $i + 1, 1)) === "\n")
                            {
                                $numBackslashes = 0;
                                $j = count($arithContent) - 1;
                                while ($j >= 0 && $arithContent[$j] === "\n")
                                {
                                    $j -= 1;
                                }
                                while ($j >= 0 && $arithContent[$j] === "\\")
                                {
                                    $numBackslashes += 1;
                                    $j -= 1;
                                }
                                if ($numBackslashes % 2 === 1)
                                {
                                    array_push($arithContent, "\\");
                                    array_push($arithContent, "\n");
                                    $i += 2;
                                }
                                else
                                {
                                    $i += 2;
                                }
                                if ($depth === 1)
                                {
                                    $firstCloseIdx = -1;
                                }
                            }
                            else
                            {
                                array_push($arithContent, (string)(mb_substr($value, $i, 1)));
                                $i += 1;
                                if ($depth === 1)
                                {
                                    $firstCloseIdx = -1;
                                }
                            }
                        }
                    }
                }
                if ($depth === 0 || $depth === 1 && $firstCloseIdx !== -1)
                {
                    $content = implode("", $arithContent);
                    if ($firstCloseIdx !== -1)
                    {
                        $content = mb_substr($content, 0, $firstCloseIdx);
                        $closing = ($depth === 0 ? "))" : ")");
                        array_push($result, "\$((" . $content . $closing);
                    }
                    else
                    {
                        array_push($result, "\$((" . $content . ")");
                    }
                }
                else
                {
                    array_push($result, _substring($value, $start, $i));
                }
            }
            else
            {
                array_push($result, (string)(mb_substr($value, $i, 1)));
                $i += 1;
            }
        }
        return implode("", $result);
    }

    public function _collectCmdsubs(?Node $node): ?array
    {
        $result = [];
        if ($node instanceof Commandsubstitution)
        {
            array_push($result, $node);
        }
        elseif ($node instanceof Array_)
        {
            foreach ($node->elements as $elem)
            {
                foreach ($elem->parts as $p)
                {
                    if ($p instanceof Commandsubstitution)
                    {
                        array_push($result, $p);
                    }
                    else
                    {
                        array_push($result, ...$this->_collectCmdsubs($p));
                    }
                }
            }
        }
        elseif ($node instanceof Arithmeticexpansion)
        {
            if ($node->expression !== null)
            {
                array_push($result, ...$this->_collectCmdsubs($node->expression));
            }
        }
        elseif ($node instanceof Arithbinaryop)
        {
            array_push($result, ...$this->_collectCmdsubs($node->left));
            array_push($result, ...$this->_collectCmdsubs($node->right));
        }
        elseif ($node instanceof Arithcomma)
        {
            array_push($result, ...$this->_collectCmdsubs($node->left));
            array_push($result, ...$this->_collectCmdsubs($node->right));
        }
        elseif ($node instanceof Arithunaryop)
        {
            array_push($result, ...$this->_collectCmdsubs($node->operand));
        }
        elseif ($node instanceof Arithpreincr)
        {
            array_push($result, ...$this->_collectCmdsubs($node->operand));
        }
        elseif ($node instanceof Arithpostincr)
        {
            array_push($result, ...$this->_collectCmdsubs($node->operand));
        }
        elseif ($node instanceof Arithpredecr)
        {
            array_push($result, ...$this->_collectCmdsubs($node->operand));
        }
        elseif ($node instanceof Arithpostdecr)
        {
            array_push($result, ...$this->_collectCmdsubs($node->operand));
        }
        elseif ($node instanceof Arithternary)
        {
            array_push($result, ...$this->_collectCmdsubs($node->condition));
            array_push($result, ...$this->_collectCmdsubs($node->ifTrue));
            array_push($result, ...$this->_collectCmdsubs($node->ifFalse));
        }
        elseif ($node instanceof Arithassign)
        {
            array_push($result, ...$this->_collectCmdsubs($node->target));
            array_push($result, ...$this->_collectCmdsubs($node->value));
        }
        return $result;
    }

    public function _collectProcsubs(?Node $node): ?array
    {
        $result = [];
        if ($node instanceof Processsubstitution)
        {
            array_push($result, $node);
        }
        elseif ($node instanceof Array_)
        {
            foreach ($node->elements as $elem)
            {
                foreach ($elem->parts as $p)
                {
                    if ($p instanceof Processsubstitution)
                    {
                        array_push($result, $p);
                    }
                    else
                    {
                        array_push($result, ...$this->_collectProcsubs($p));
                    }
                }
            }
        }
        return $result;
    }

    public function _formatCommandSubstitutions(string $value, bool $inArith): string
    {
        $cmdsubParts = [];
        $procsubParts = [];
        $hasArith = false;
        foreach ($this->parts as $p)
        {
            if ($p instanceof Commandsubstitution)
            {
                array_push($cmdsubParts, $p);
            }
            elseif ($p instanceof Processsubstitution)
            {
                array_push($procsubParts, $p);
            }
            elseif ($p instanceof Arithmeticexpansion)
            {
                $hasArith = true;
            }
            else
            {
                array_push($cmdsubParts, ...$this->_collectCmdsubs($p));
                array_push($procsubParts, ...$this->_collectProcsubs($p));
            }
        }
        $hasBraceCmdsub = (mb_strpos($value, "\${ ") === false ? -1 : mb_strpos($value, "\${ ")) !== -1 || (mb_strpos($value, "\${\t") === false ? -1 : mb_strpos($value, "\${\t")) !== -1 || (mb_strpos($value, "\${\n") === false ? -1 : mb_strpos($value, "\${\n")) !== -1 || (mb_strpos($value, "\${|") === false ? -1 : mb_strpos($value, "\${|")) !== -1;
        $hasUntrackedCmdsub = false;
        $hasUntrackedProcsub = false;
        $idx = 0;
        $scanQuote = newQuoteState();
        while ($idx < mb_strlen($value))
        {
            if ((string)(mb_substr($value, $idx, 1)) === "\"")
            {
                $scanQuote->double = !$scanQuote->double;
                $idx += 1;
            }
            else
            {
                if ((string)(mb_substr($value, $idx, 1)) === "'" && !$scanQuote->double)
                {
                    $idx += 1;
                    while ($idx < mb_strlen($value) && (string)(mb_substr($value, $idx, 1)) !== "'")
                    {
                        $idx += 1;
                    }
                    if ($idx < mb_strlen($value))
                    {
                        $idx += 1;
                    }
                }
                else
                {
                    if (_startsWithAt($value, $idx, "\$(") && !_startsWithAt($value, $idx, "\$((") && !_isBackslashEscaped($value, $idx) && !_isDollarDollarParen($value, $idx))
                    {
                        $hasUntrackedCmdsub = true;
                        break;
                    }
                    else
                    {
                        if ((_startsWithAt($value, $idx, "<(") || _startsWithAt($value, $idx, ">(")) && !$scanQuote->double)
                        {
                            if ($idx === 0 || !ctype_alnum((string)(mb_substr($value, $idx - 1, 1))) && ((!str_contains("\"'", (string)(mb_substr($value, $idx - 1, 1))))))
                            {
                                $hasUntrackedProcsub = true;
                                break;
                            }
                            $idx += 1;
                        }
                        else
                        {
                            $idx += 1;
                        }
                    }
                }
            }
        }
        $hasParamWithProcsubPattern = ((str_contains($value, "\${"))) && (((str_contains($value, "<("))) || ((str_contains($value, ">("))));
        if (!(count($cmdsubParts) > 0) && !(count($procsubParts) > 0) && !$hasBraceCmdsub && !$hasUntrackedCmdsub && !$hasUntrackedProcsub && !$hasParamWithProcsubPattern)
        {
            return $value;
        }
        $result = [];
        $i = 0;
        $cmdsubIdx = 0;
        $procsubIdx = 0;
        $mainQuote = newQuoteState();
        $extglobDepth = 0;
        $deprecatedArithDepth = 0;
        $arithDepth = 0;
        $arithParenDepth = 0;
        while ($i < mb_strlen($value))
        {
            if ($i > 0 && _isExtglobPrefix((string)(mb_substr($value, $i - 1, 1))) && (string)(mb_substr($value, $i, 1)) === "(" && !_isBackslashEscaped($value, $i - 1))
            {
                $extglobDepth += 1;
                array_push($result, (string)(mb_substr($value, $i, 1)));
                $i += 1;
                continue;
            }
            if ((string)(mb_substr($value, $i, 1)) === ")" && $extglobDepth > 0)
            {
                $extglobDepth -= 1;
                array_push($result, (string)(mb_substr($value, $i, 1)));
                $i += 1;
                continue;
            }
            if (_startsWithAt($value, $i, "\$[") && !_isBackslashEscaped($value, $i))
            {
                $deprecatedArithDepth += 1;
                array_push($result, (string)(mb_substr($value, $i, 1)));
                $i += 1;
                continue;
            }
            if ((string)(mb_substr($value, $i, 1)) === "]" && $deprecatedArithDepth > 0)
            {
                $deprecatedArithDepth -= 1;
                array_push($result, (string)(mb_substr($value, $i, 1)));
                $i += 1;
                continue;
            }
            if (_isExpansionStart($value, $i, "\$((") && !_isBackslashEscaped($value, $i) && $hasArith)
            {
                $arithDepth += 1;
                $arithParenDepth += 2;
                array_push($result, "\$((");
                $i += 3;
                continue;
            }
            if ($arithDepth > 0 && $arithParenDepth === 2 && _startsWithAt($value, $i, "))"))
            {
                $arithDepth -= 1;
                $arithParenDepth -= 2;
                array_push($result, "))");
                $i += 2;
                continue;
            }
            if ($arithDepth > 0)
            {
                if ((string)(mb_substr($value, $i, 1)) === "(")
                {
                    $arithParenDepth += 1;
                    array_push($result, (string)(mb_substr($value, $i, 1)));
                    $i += 1;
                    continue;
                }
                else
                {
                    if ((string)(mb_substr($value, $i, 1)) === ")")
                    {
                        $arithParenDepth -= 1;
                        array_push($result, (string)(mb_substr($value, $i, 1)));
                        $i += 1;
                        continue;
                    }
                }
            }
            $j = 0;
            if (_isExpansionStart($value, $i, "\$((") && !$hasArith)
            {
                $j = _findCmdsubEnd($value, $i + 2);
                array_push($result, _substring($value, $i, $j));
                if ($cmdsubIdx < count($cmdsubParts))
                {
                    $cmdsubIdx += 1;
                }
                $i = $j;
                continue;
            }
            $inner = "";
            $node = null;
            $formatted = "";
            $parser = null;
            $parsed = null;
            if (_startsWithAt($value, $i, "\$(") && !_startsWithAt($value, $i, "\$((") && !_isBackslashEscaped($value, $i) && !_isDollarDollarParen($value, $i))
            {
                $j = _findCmdsubEnd($value, $i + 2);
                if ($extglobDepth > 0)
                {
                    array_push($result, _substring($value, $i, $j));
                    if ($cmdsubIdx < count($cmdsubParts))
                    {
                        $cmdsubIdx += 1;
                    }
                    $i = $j;
                    continue;
                }
                $inner = _substring($value, $i + 2, $j - 1);
                if ($cmdsubIdx < count($cmdsubParts))
                {
                    $node = $cmdsubParts[$cmdsubIdx];
                    $formatted = _formatCmdsubNode($node->command, 0, false, false, false);
                    $cmdsubIdx += 1;
                }
                else
                {
                    try
                    {
                        $parser = newParser($inner, false, false);
                        $parsed = $parser->parseList(true);
                        $formatted = ($parsed !== null ? _formatCmdsubNode($parsed, 0, false, false, false) : "");
                    } catch (Exception_ $ex)
                    {
                        $formatted = $inner;
                    }
                }
                if (str_starts_with($formatted, "("))
                {
                    array_push($result, "\$( " . $formatted . ")");
                }
                else
                {
                    array_push($result, "\$(" . $formatted . ")");
                }
                $i = $j;
            }
            else
            {
                if ((string)(mb_substr($value, $i, 1)) === "`" && $cmdsubIdx < count($cmdsubParts))
                {
                    $j = $i + 1;
                    while ($j < mb_strlen($value))
                    {
                        if ((string)(mb_substr($value, $j, 1)) === "\\" && $j + 1 < mb_strlen($value))
                        {
                            $j += 2;
                            continue;
                        }
                        if ((string)(mb_substr($value, $j, 1)) === "`")
                        {
                            $j += 1;
                            break;
                        }
                        $j += 1;
                    }
                    array_push($result, _substring($value, $i, $j));
                    $cmdsubIdx += 1;
                    $i = $j;
                }
                else
                {
                    $prefix = "";
                    if (_isExpansionStart($value, $i, "\${") && $i + 2 < mb_strlen($value) && _isFunsubChar((string)(mb_substr($value, $i + 2, 1))) && !_isBackslashEscaped($value, $i))
                    {
                        $j = _findFunsubEnd($value, $i + 2);
                        $cmdsubNode = ($cmdsubIdx < count($cmdsubParts) ? $cmdsubParts[$cmdsubIdx] : null);
                        if (($cmdsubNode instanceof Commandsubstitution) && $cmdsubNode->brace)
                        {
                            $node = $cmdsubNode;
                            $formatted = _formatCmdsubNode($node->command, 0, false, false, false);
                            $hasPipe = (string)(mb_substr($value, $i + 2, 1)) === "|";
                            $prefix = ($hasPipe ? "\${|" : "\${ ");
                            $origInner = _substring($value, $i + 2, $j - 1);
                            $endsWithNewline = str_ends_with($origInner, "\n");
                            $suffix = "";
                            if (!($formatted !== '') || ctype_space($formatted))
                            {
                                $suffix = "}";
                            }
                            else
                            {
                                if (str_ends_with($formatted, "&") || str_ends_with($formatted, "& "))
                                {
                                    $suffix = (str_ends_with($formatted, "&") ? " }" : "}");
                                }
                                else
                                {
                                    if ($endsWithNewline)
                                    {
                                        $suffix = "\n }";
                                    }
                                    else
                                    {
                                        $suffix = "; }";
                                    }
                                }
                            }
                            array_push($result, $prefix . $formatted . $suffix);
                            $cmdsubIdx += 1;
                        }
                        else
                        {
                            array_push($result, _substring($value, $i, $j));
                        }
                        $i = $j;
                    }
                    else
                    {
                        if ((_startsWithAt($value, $i, ">(") || _startsWithAt($value, $i, "<(")) && !$mainQuote->double && $deprecatedArithDepth === 0 && $arithDepth === 0)
                        {
                            $isProcsub = $i === 0 || !ctype_alnum((string)(mb_substr($value, $i - 1, 1))) && ((!str_contains("\"'", (string)(mb_substr($value, $i - 1, 1)))));
                            if ($extglobDepth > 0)
                            {
                                $j = _findCmdsubEnd($value, $i + 2);
                                array_push($result, _substring($value, $i, $j));
                                if ($procsubIdx < count($procsubParts))
                                {
                                    $procsubIdx += 1;
                                }
                                $i = $j;
                                continue;
                            }
                            $direction = "";
                            $compact = false;
                            $stripped = "";
                            if ($procsubIdx < count($procsubParts))
                            {
                                $direction = (string)(mb_substr($value, $i, 1));
                                $j = _findCmdsubEnd($value, $i + 2);
                                $node = $procsubParts[$procsubIdx];
                                $compact = _startsWithSubshell($node->command);
                                $formatted = _formatCmdsubNode($node->command, 0, true, $compact, true);
                                $rawContent = _substring($value, $i + 2, $j - 1);
                                if ($node->command->kind === "subshell")
                                {
                                    $leadingWsEnd = 0;
                                    while ($leadingWsEnd < mb_strlen($rawContent) && ((str_contains(" \t\n", (string)(mb_substr($rawContent, $leadingWsEnd, 1))))))
                                    {
                                        $leadingWsEnd += 1;
                                    }
                                    $leadingWs = mb_substr($rawContent, 0, $leadingWsEnd);
                                    $stripped = mb_substr($rawContent, $leadingWsEnd);
                                    if (str_starts_with($stripped, "("))
                                    {
                                        if (($leadingWs !== ''))
                                        {
                                            $normalizedWs = str_replace("\t", " ", str_replace("\n", " ", $leadingWs));
                                            $spaced = _formatCmdsubNode($node->command, 0, false, false, false);
                                            array_push($result, $direction . "(" . $normalizedWs . $spaced . ")");
                                        }
                                        else
                                        {
                                            $rawContent = str_replace("\\\n", "", $rawContent);
                                            array_push($result, $direction . "(" . $rawContent . ")");
                                        }
                                        $procsubIdx += 1;
                                        $i = $j;
                                        continue;
                                    }
                                }
                                $rawContent = _substring($value, $i + 2, $j - 1);
                                $rawStripped = str_replace("\\\n", "", $rawContent);
                                if (_startsWithSubshell($node->command) && $formatted !== $rawStripped)
                                {
                                    array_push($result, $direction . "(" . $rawStripped . ")");
                                }
                                else
                                {
                                    $finalOutput = $direction . "(" . $formatted . ")";
                                    array_push($result, $finalOutput);
                                }
                                $procsubIdx += 1;
                                $i = $j;
                            }
                            else
                            {
                                if ($isProcsub && (count($this->parts) !== 0))
                                {
                                    $direction = (string)(mb_substr($value, $i, 1));
                                    $j = _findCmdsubEnd($value, $i + 2);
                                    if ($j > mb_strlen($value) || $j > 0 && $j <= mb_strlen($value) && (string)(mb_substr($value, $j - 1, 1)) !== ")")
                                    {
                                        array_push($result, (string)(mb_substr($value, $i, 1)));
                                        $i += 1;
                                        continue;
                                    }
                                    $inner = _substring($value, $i + 2, $j - 1);
                                    try
                                    {
                                        $parser = newParser($inner, false, false);
                                        $parsed = $parser->parseList(true);
                                        if ($parsed !== null && $parser->pos === mb_strlen($inner) && ((!str_contains($inner, "\n"))))
                                        {
                                            $compact = _startsWithSubshell($parsed);
                                            $formatted = _formatCmdsubNode($parsed, 0, true, $compact, true);
                                        }
                                        else
                                        {
                                            $formatted = $inner;
                                        }
                                    } catch (Exception_ $ex)
                                    {
                                        $formatted = $inner;
                                    }
                                    array_push($result, $direction . "(" . $formatted . ")");
                                    $i = $j;
                                }
                                else
                                {
                                    if ($isProcsub)
                                    {
                                        $direction = (string)(mb_substr($value, $i, 1));
                                        $j = _findCmdsubEnd($value, $i + 2);
                                        if ($j > mb_strlen($value) || $j > 0 && $j <= mb_strlen($value) && (string)(mb_substr($value, $j - 1, 1)) !== ")")
                                        {
                                            array_push($result, (string)(mb_substr($value, $i, 1)));
                                            $i += 1;
                                            continue;
                                        }
                                        $inner = _substring($value, $i + 2, $j - 1);
                                        if ($inArith)
                                        {
                                            array_push($result, $direction . "(" . $inner . ")");
                                        }
                                        else
                                        {
                                            if ((trim($inner, " \t\n\r") !== ''))
                                            {
                                                $stripped = ltrim($inner, " \t");
                                                array_push($result, $direction . "(" . $stripped . ")");
                                            }
                                            else
                                            {
                                                array_push($result, $direction . "(" . $inner . ")");
                                            }
                                        }
                                        $i = $j;
                                    }
                                    else
                                    {
                                        array_push($result, (string)(mb_substr($value, $i, 1)));
                                        $i += 1;
                                    }
                                }
                            }
                        }
                        else
                        {
                            $depth = 0;
                            if ((_isExpansionStart($value, $i, "\${ ") || _isExpansionStart($value, $i, "\${\t") || _isExpansionStart($value, $i, "\${\n") || _isExpansionStart($value, $i, "\${|")) && !_isBackslashEscaped($value, $i))
                            {
                                $prefix = str_replace("\n", " ", str_replace("\t", " ", _substring($value, $i, $i + 3)));
                                $j = $i + 3;
                                $depth = 1;
                                while ($j < mb_strlen($value) && $depth > 0)
                                {
                                    if ((string)(mb_substr($value, $j, 1)) === "{")
                                    {
                                        $depth += 1;
                                    }
                                    else
                                    {
                                        if ((string)(mb_substr($value, $j, 1)) === "}")
                                        {
                                            $depth -= 1;
                                        }
                                    }
                                    $j += 1;
                                }
                                $inner = _substring($value, $i + 2, $j - 1);
                                if (trim($inner, " \t\n\r") === "")
                                {
                                    array_push($result, "\${ }");
                                }
                                else
                                {
                                    try
                                    {
                                        $parser = newParser(ltrim($inner, " \t\n|"), false, false);
                                        $parsed = $parser->parseList(true);
                                        if ($parsed !== null)
                                        {
                                            $formatted = _formatCmdsubNode($parsed, 0, false, false, false);
                                            $formatted = rtrim($formatted, ";");
                                            $terminator = "";
                                            if (str_ends_with(rtrim($inner, " \t"), "\n"))
                                            {
                                                $terminator = "\n }";
                                            }
                                            else
                                            {
                                                if (str_ends_with($formatted, " &"))
                                                {
                                                    $terminator = " }";
                                                }
                                                else
                                                {
                                                    $terminator = "; }";
                                                }
                                            }
                                            array_push($result, $prefix . $formatted . $terminator);
                                        }
                                        else
                                        {
                                            array_push($result, "\${ }");
                                        }
                                    } catch (Exception_ $ex)
                                    {
                                        array_push($result, _substring($value, $i, $j));
                                    }
                                }
                                $i = $j;
                            }
                            else
                            {
                                if (_isExpansionStart($value, $i, "\${") && !_isBackslashEscaped($value, $i))
                                {
                                    $j = $i + 2;
                                    $depth = 1;
                                    $braceQuote = newQuoteState();
                                    while ($j < mb_strlen($value) && $depth > 0)
                                    {
                                        $c = (string)(mb_substr($value, $j, 1));
                                        if ($c === "\\" && $j + 1 < mb_strlen($value) && !$braceQuote->single)
                                        {
                                            $j += 2;
                                            continue;
                                        }
                                        if ($c === "'" && !$braceQuote->double)
                                        {
                                            $braceQuote->single = !$braceQuote->single;
                                        }
                                        else
                                        {
                                            if ($c === "\"" && !$braceQuote->single)
                                            {
                                                $braceQuote->double = !$braceQuote->double;
                                            }
                                            else
                                            {
                                                if (!$braceQuote->inQuotes())
                                                {
                                                    if (_isExpansionStart($value, $j, "\$(") && !_startsWithAt($value, $j, "\$(("))
                                                    {
                                                        $j = _findCmdsubEnd($value, $j + 2);
                                                        continue;
                                                    }
                                                    if ($c === "{")
                                                    {
                                                        $depth += 1;
                                                    }
                                                    else
                                                    {
                                                        if ($c === "}")
                                                        {
                                                            $depth -= 1;
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                        $j += 1;
                                    }
                                    if ($depth > 0)
                                    {
                                        $inner = _substring($value, $i + 2, $j);
                                    }
                                    else
                                    {
                                        $inner = _substring($value, $i + 2, $j - 1);
                                    }
                                    $formattedInner = $this->_formatCommandSubstitutions($inner, false);
                                    $formattedInner = $this->_normalizeExtglobWhitespace($formattedInner);
                                    if ($depth === 0)
                                    {
                                        array_push($result, "\${" . $formattedInner . "}");
                                    }
                                    else
                                    {
                                        array_push($result, "\${" . $formattedInner);
                                    }
                                    $i = $j;
                                }
                                else
                                {
                                    if ((string)(mb_substr($value, $i, 1)) === "\"")
                                    {
                                        $mainQuote->double = !$mainQuote->double;
                                        array_push($result, (string)(mb_substr($value, $i, 1)));
                                        $i += 1;
                                    }
                                    else
                                    {
                                        if ((string)(mb_substr($value, $i, 1)) === "'" && !$mainQuote->double)
                                        {
                                            $j = $i + 1;
                                            while ($j < mb_strlen($value) && (string)(mb_substr($value, $j, 1)) !== "'")
                                            {
                                                $j += 1;
                                            }
                                            if ($j < mb_strlen($value))
                                            {
                                                $j += 1;
                                            }
                                            array_push($result, _substring($value, $i, $j));
                                            $i = $j;
                                        }
                                        else
                                        {
                                            array_push($result, (string)(mb_substr($value, $i, 1)));
                                            $i += 1;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        return implode("", $result);
    }

    public function _normalizeExtglobWhitespace(string $value): string
    {
        $result = [];
        $i = 0;
        $extglobQuote = newQuoteState();
        $deprecatedArithDepth = 0;
        while ($i < mb_strlen($value))
        {
            if ((string)(mb_substr($value, $i, 1)) === "\"")
            {
                $extglobQuote->double = !$extglobQuote->double;
                array_push($result, (string)(mb_substr($value, $i, 1)));
                $i += 1;
                continue;
            }
            if (_startsWithAt($value, $i, "\$[") && !_isBackslashEscaped($value, $i))
            {
                $deprecatedArithDepth += 1;
                array_push($result, (string)(mb_substr($value, $i, 1)));
                $i += 1;
                continue;
            }
            if ((string)(mb_substr($value, $i, 1)) === "]" && $deprecatedArithDepth > 0)
            {
                $deprecatedArithDepth -= 1;
                array_push($result, (string)(mb_substr($value, $i, 1)));
                $i += 1;
                continue;
            }
            if ($i + 1 < mb_strlen($value) && (string)(mb_substr($value, $i + 1, 1)) === "(")
            {
                $prefixChar = (string)(mb_substr($value, $i, 1));
                if (((str_contains("><", $prefixChar))) && !$extglobQuote->double && $deprecatedArithDepth === 0)
                {
                    array_push($result, $prefixChar);
                    array_push($result, "(");
                    $i += 2;
                    $depth = 1;
                    $patternParts = [];
                    $currentPart = [];
                    $hasPipe = false;
                    while ($i < mb_strlen($value) && $depth > 0)
                    {
                        if ((string)(mb_substr($value, $i, 1)) === "\\" && $i + 1 < mb_strlen($value))
                        {
                            array_push($currentPart, mb_substr($value, $i, ($i + 2) - ($i)));
                            $i += 2;
                            continue;
                        }
                        else
                        {
                            if ((string)(mb_substr($value, $i, 1)) === "(")
                            {
                                $depth += 1;
                                array_push($currentPart, (string)(mb_substr($value, $i, 1)));
                                $i += 1;
                            }
                            else
                            {
                                $partContent = "";
                                if ((string)(mb_substr($value, $i, 1)) === ")")
                                {
                                    $depth -= 1;
                                    if ($depth === 0)
                                    {
                                        $partContent = implode("", $currentPart);
                                        if ((str_contains($partContent, "<<")))
                                        {
                                            array_push($patternParts, $partContent);
                                        }
                                        else
                                        {
                                            if ($hasPipe)
                                            {
                                                array_push($patternParts, trim($partContent, " \t\n\r"));
                                            }
                                            else
                                            {
                                                array_push($patternParts, $partContent);
                                            }
                                        }
                                        break;
                                    }
                                    array_push($currentPart, (string)(mb_substr($value, $i, 1)));
                                    $i += 1;
                                }
                                else
                                {
                                    if ((string)(mb_substr($value, $i, 1)) === "|" && $depth === 1)
                                    {
                                        if ($i + 1 < mb_strlen($value) && (string)(mb_substr($value, $i + 1, 1)) === "|")
                                        {
                                            array_push($currentPart, "||");
                                            $i += 2;
                                        }
                                        else
                                        {
                                            $hasPipe = true;
                                            $partContent = implode("", $currentPart);
                                            if ((str_contains($partContent, "<<")))
                                            {
                                                array_push($patternParts, $partContent);
                                            }
                                            else
                                            {
                                                array_push($patternParts, trim($partContent, " \t\n\r"));
                                            }
                                            $currentPart = [];
                                            $i += 1;
                                        }
                                    }
                                    else
                                    {
                                        array_push($currentPart, (string)(mb_substr($value, $i, 1)));
                                        $i += 1;
                                    }
                                }
                            }
                        }
                    }
                    array_push($result, implode(" | ", $patternParts));
                    if ($depth === 0)
                    {
                        array_push($result, ")");
                        $i += 1;
                    }
                    continue;
                }
            }
            array_push($result, (string)(mb_substr($value, $i, 1)));
            $i += 1;
        }
        return implode("", $result);
    }

    public function getCondFormattedValue(): string
    {
        $value = $this->_expandAllAnsiCQuotes($this->value);
        $value = $this->_stripLocaleStringDollars($value);
        $value = $this->_formatCommandSubstitutions($value, false);
        $value = $this->_normalizeExtglobWhitespace($value);
        $value = str_replace("", "", $value);
        return rtrim($value, "\n");
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Command implements Node
{
    public ?array $words;
    public ?array $redirects;
    public string $kind;

    public function __construct(?array $words, ?array $redirects, string $kind)
    {
        $this->words = $words ?? [];
        $this->redirects = $redirects ?? [];
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        $parts = [];
        foreach ($this->words as $w)
        {
            array_push($parts, $w->toSexp());
        }
        foreach ($this->redirects as $r)
        {
            array_push($parts, $r->toSexp());
        }
        $inner = implode(" ", $parts);
        if (!($inner !== ''))
        {
            return "(command)";
        }
        return "(command " . $inner . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Pipeline implements Node
{
    public ?array $commands;
    public string $kind;

    public function __construct(?array $commands, string $kind)
    {
        $this->commands = $commands ?? [];
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        if (count($this->commands) === 1)
        {
            return $this->commands[0]->toSexp();
        }
        $cmds = [];
        $i = 0;
        $cmd = null;
        while ($i < count($this->commands))
        {
            $cmd = $this->commands[$i];
            if ($cmd instanceof Pipeboth)
            {
                $i += 1;
                continue;
            }
            $needsRedirect = $i + 1 < count($this->commands) && $this->commands[$i + 1]->kind === "pipe-both";
            array_push($cmds, [$cmd, $needsRedirect]);
            $i += 1;
        }
        $pair = null;
        $needs = false;
        if (count($cmds) === 1)
        {
            $pair = $cmds[0];
            $cmd = $pair[0];
            $needs = $pair[1];
            return $this->_cmdSexp($cmd, $needs);
        }
        $lastPair = $cmds[count($cmds) - 1];
        $lastCmd = $lastPair[0];
        $lastNeeds = $lastPair[1];
        $result = $this->_cmdSexp($lastCmd, $lastNeeds);
        $j = count($cmds) - 2;
        while ($j >= 0)
        {
            $pair = $cmds[$j];
            $cmd = $pair[0];
            $needs = $pair[1];
            if ($needs && $cmd->kind !== "command")
            {
                $result = "(pipe " . $cmd->toSexp() . " (redirect \">&\" 1) " . $result . ")";
            }
            else
            {
                $result = "(pipe " . $this->_cmdSexp($cmd, $needs) . " " . $result . ")";
            }
            $j -= 1;
        }
        return $result;
    }

    public function _cmdSexp(?Node $cmd, bool $needsRedirect): string
    {
        if (!$needsRedirect)
        {
            return $cmd->toSexp();
        }
        if ($cmd instanceof Command)
        {
            $parts = [];
            foreach ($cmd->words as $w)
            {
                array_push($parts, $w->toSexp());
            }
            foreach ($cmd->redirects as $r)
            {
                array_push($parts, $r->toSexp());
            }
            array_push($parts, "(redirect \">&\" 1)");
            return "(command " . implode(" ", $parts) . ")";
        }
        return $cmd->toSexp();
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class List_ implements Node
{
    public ?array $parts;
    public string $kind;

    public function __construct(?array $parts, string $kind)
    {
        $this->parts = $parts ?? [];
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        $parts = $this->parts;
        $opNames = ["&&" => "and", "||" => "or", ";" => "semi", "\n" => "semi", "&" => "background"];
        while (count($parts) > 1 && $parts[count($parts) - 1]->kind === "operator" && ($parts[count($parts) - 1]->op === ";" || $parts[count($parts) - 1]->op === "\n"))
        {
            $parts = _sublist($parts, 0, count($parts) - 1);
        }
        if (count($parts) === 1)
        {
            return $parts[0]->toSexp();
        }
        if ($parts[count($parts) - 1]->kind === "operator" && $parts[count($parts) - 1]->op === "&")
        {
            for ($i = count($parts) - 3; $i > 0; $i += -2)
            {
                if ($parts[$i]->kind === "operator" && ($parts[$i]->op === ";" || $parts[$i]->op === "\n"))
                {
                    $left = _sublist($parts, 0, $i);
                    $right = _sublist($parts, $i + 1, count($parts) - 1);
                    $leftSexp = "";
                    if (count($left) > 1)
                    {
                        $leftSexp = new List_($left, "list")->toSexp();
                    }
                    else
                    {
                        $leftSexp = $left[0]->toSexp();
                    }
                    $rightSexp = "";
                    if (count($right) > 1)
                    {
                        $rightSexp = new List_($right, "list")->toSexp();
                    }
                    else
                    {
                        $rightSexp = $right[0]->toSexp();
                    }
                    return "(semi " . $leftSexp . " (background " . $rightSexp . "))";
                }
            }
            $innerParts = _sublist($parts, 0, count($parts) - 1);
            if (count($innerParts) === 1)
            {
                return "(background " . $innerParts[0]->toSexp() . ")";
            }
            $innerList = new List_($innerParts, "list");
            return "(background " . $innerList->toSexp() . ")";
        }
        return $this->_toSexpWithPrecedence($parts, $opNames);
    }

    public function _toSexpWithPrecedence(?array $parts, array $opNames): string
    {
        $semiPositions = [];
        for ($i = 0; $i < count($parts); $i += 1)
        {
            if ($parts[$i]->kind === "operator" && ($parts[$i]->op === ";" || $parts[$i]->op === "\n"))
            {
                array_push($semiPositions, $i);
            }
        }
        if ((count($semiPositions) > 0))
        {
            $segments = [];
            $start = 0;
            $seg = [];
            foreach ($semiPositions as $pos)
            {
                $seg = _sublist($parts, $start, $pos);
                if ((count($seg) > 0) && $seg[0]->kind !== "operator")
                {
                    array_push($segments, $seg);
                }
                $start = $pos + 1;
            }
            $seg = _sublist($parts, $start, count($parts));
            if ((count($seg) > 0) && $seg[0]->kind !== "operator")
            {
                array_push($segments, $seg);
            }
            if (!(count($segments) > 0))
            {
                return "()";
            }
            $result = $this->_toSexpAmpAndHigher($segments[0], $opNames);
            for ($i = 1; $i < count($segments); $i += 1)
            {
                $result = "(semi " . $result . " " . $this->_toSexpAmpAndHigher($segments[$i], $opNames) . ")";
            }
            return $result;
        }
        return $this->_toSexpAmpAndHigher($parts, $opNames);
    }

    public function _toSexpAmpAndHigher(?array $parts, array $opNames): string
    {
        if (count($parts) === 1)
        {
            return $parts[0]->toSexp();
        }
        $ampPositions = [];
        for ($i = 1; $i < count($parts) - 1; $i += 2)
        {
            if ($parts[$i]->kind === "operator" && $parts[$i]->op === "&")
            {
                array_push($ampPositions, $i);
            }
        }
        if ((count($ampPositions) > 0))
        {
            $segments = [];
            $start = 0;
            foreach ($ampPositions as $pos)
            {
                array_push($segments, _sublist($parts, $start, $pos));
                $start = $pos + 1;
            }
            array_push($segments, _sublist($parts, $start, count($parts)));
            $result = $this->_toSexpAndOr($segments[0], $opNames);
            for ($i = 1; $i < count($segments); $i += 1)
            {
                $result = "(background " . $result . " " . $this->_toSexpAndOr($segments[$i], $opNames) . ")";
            }
            return $result;
        }
        return $this->_toSexpAndOr($parts, $opNames);
    }

    public function _toSexpAndOr(?array $parts, array $opNames): string
    {
        if (count($parts) === 1)
        {
            return $parts[0]->toSexp();
        }
        $result = $parts[0]->toSexp();
        for ($i = 1; $i < count($parts) - 1; $i += 2)
        {
            $op = $parts[$i];
            $cmd = $parts[$i + 1];
            $opName = ($opNames[$op->op] ?? $op->op);
            $result = "(" . $opName . " " . $result . " " . $cmd->toSexp() . ")";
        }
        return $result;
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Operator implements Node
{
    public string $op;
    public string $kind;

    public function __construct(string $op, string $kind)
    {
        $this->op = $op;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        $names = ["&&" => "and", "||" => "or", ";" => "semi", "&" => "bg", "|" => "pipe"];
        return "(" . ($names[$this->op] ?? $this->op) . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Pipeboth implements Node
{
    public string $kind;

    public function __construct(string $kind)
    {
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        return "(pipe-both)";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Empty_ implements Node
{
    public string $kind;

    public function __construct(string $kind)
    {
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        return "";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Comment implements Node
{
    public string $text;
    public string $kind;

    public function __construct(string $text, string $kind)
    {
        $this->text = $text;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        return "";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Redirect implements Node
{
    public string $op;
    public ?Word $target;
    public ?int $fd;
    public string $kind;

    public function __construct(string $op, ?Word $target, string $kind, ?int $fd = null)
    {
        $this->op = $op;
        $this->target = $target;
        $this->kind = $kind;
        $this->fd = $fd;
    }

    public function toSexp(): string
    {
        $op = ltrim($this->op, "0123456789");
        if (str_starts_with($op, "{"))
        {
            $j = 1;
            if ($j < mb_strlen($op) && (ctype_alpha((string)(mb_substr($op, $j, 1))) || (string)(mb_substr($op, $j, 1)) === "_"))
            {
                $j += 1;
                while ($j < mb_strlen($op) && (ctype_alnum((string)(mb_substr($op, $j, 1))) || (string)(mb_substr($op, $j, 1)) === "_"))
                {
                    $j += 1;
                }
                if ($j < mb_strlen($op) && (string)(mb_substr($op, $j, 1)) === "[")
                {
                    $j += 1;
                    while ($j < mb_strlen($op) && (string)(mb_substr($op, $j, 1)) !== "]")
                    {
                        $j += 1;
                    }
                    if ($j < mb_strlen($op) && (string)(mb_substr($op, $j, 1)) === "]")
                    {
                        $j += 1;
                    }
                }
                if ($j < mb_strlen($op) && (string)(mb_substr($op, $j, 1)) === "}")
                {
                    $op = _substring($op, $j + 1, mb_strlen($op));
                }
            }
        }
        $targetVal = $this->target->value;
        $targetVal = $this->target->_expandAllAnsiCQuotes($targetVal);
        $targetVal = $this->target->_stripLocaleStringDollars($targetVal);
        $targetVal = $this->target->_formatCommandSubstitutions($targetVal, false);
        $targetVal = $this->target->_stripArithLineContinuations($targetVal);
        if (str_ends_with($targetVal, "\\") && !str_ends_with($targetVal, "\\\\"))
        {
            $targetVal = $targetVal . "\\";
        }
        if (str_starts_with($targetVal, "&"))
        {
            if ($op === ">")
            {
                $op = ">&";
            }
            else
            {
                if ($op === "<")
                {
                    $op = "<&";
                }
            }
            $raw = _substring($targetVal, 1, mb_strlen($targetVal));
            if (ctype_digit($raw) && intval($raw, 10) <= 2147483647)
            {
                return "(redirect \"" . $op . "\" " . strval(intval($raw, 10)) . ")";
            }
            if (str_ends_with($raw, "-") && ctype_digit(mb_substr($raw, 0, mb_strlen($raw) - 1)) && intval(mb_substr($raw, 0, mb_strlen($raw) - 1), 10) <= 2147483647)
            {
                return "(redirect \"" . $op . "\" " . strval(intval(mb_substr($raw, 0, mb_strlen($raw) - 1), 10)) . ")";
            }
            if ($targetVal === "&-")
            {
                return "(redirect \">&-\" 0)";
            }
            $fdTarget = (str_ends_with($raw, "-") ? mb_substr($raw, 0, mb_strlen($raw) - 1) : $raw);
            return "(redirect \"" . $op . "\" \"" . $fdTarget . "\")";
        }
        if ($op === ">&" || $op === "<&")
        {
            if (ctype_digit($targetVal) && intval($targetVal, 10) <= 2147483647)
            {
                return "(redirect \"" . $op . "\" " . strval(intval($targetVal, 10)) . ")";
            }
            if ($targetVal === "-")
            {
                return "(redirect \">&-\" 0)";
            }
            if (str_ends_with($targetVal, "-") && ctype_digit(mb_substr($targetVal, 0, mb_strlen($targetVal) - 1)) && intval(mb_substr($targetVal, 0, mb_strlen($targetVal) - 1), 10) <= 2147483647)
            {
                return "(redirect \"" . $op . "\" " . strval(intval(mb_substr($targetVal, 0, mb_strlen($targetVal) - 1), 10)) . ")";
            }
            $outVal = (str_ends_with($targetVal, "-") ? mb_substr($targetVal, 0, mb_strlen($targetVal) - 1) : $targetVal);
            return "(redirect \"" . $op . "\" \"" . $outVal . "\")";
        }
        return "(redirect \"" . $op . "\" \"" . $targetVal . "\")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Heredoc implements Node
{
    public string $delimiter;
    public string $content;
    public bool $stripTabs;
    public bool $quoted;
    public ?int $fd;
    public bool $complete;
    public int $_startPos;
    public string $kind;

    public function __construct(string $delimiter, string $content, bool $stripTabs, bool $quoted, bool $complete, int $_startPos, string $kind, ?int $fd = null)
    {
        $this->delimiter = $delimiter;
        $this->content = $content;
        $this->stripTabs = $stripTabs;
        $this->quoted = $quoted;
        $this->complete = $complete;
        $this->_startPos = $_startPos;
        $this->kind = $kind;
        $this->fd = $fd;
    }

    public function toSexp(): string
    {
        $op = ($this->stripTabs ? "<<-" : "<<");
        $content = $this->content;
        if (str_ends_with($content, "\\") && !str_ends_with($content, "\\\\"))
        {
            $content = $content . "\\";
        }
        return sprintf("(redirect \"%s\" \"%s\")", $op, $content);
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Subshell implements Node
{
    public ?Node $body;
    public ?array $redirects;
    public string $kind;

    public function __construct(?Node $body, ?array $redirects, string $kind)
    {
        $this->body = $body;
        $this->redirects = $redirects ?? [];
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        $base = "(subshell " . $this->body->toSexp() . ")";
        return _appendRedirects($base, $this->redirects);
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Bracegroup implements Node
{
    public ?Node $body;
    public ?array $redirects;
    public string $kind;

    public function __construct(?Node $body, ?array $redirects, string $kind)
    {
        $this->body = $body;
        $this->redirects = $redirects ?? [];
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        $base = "(brace-group " . $this->body->toSexp() . ")";
        return _appendRedirects($base, $this->redirects);
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class If_ implements Node
{
    public ?Node $condition;
    public ?Node $thenBody;
    public ?Node $elseBody;
    public ?array $redirects;
    public string $kind;

    public function __construct(?Node $condition, ?Node $thenBody, ?Node $elseBody, ?array $redirects, string $kind)
    {
        $this->condition = $condition;
        $this->thenBody = $thenBody;
        $this->elseBody = $elseBody;
        $this->redirects = $redirects ?? [];
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        $result = "(if " . $this->condition->toSexp() . " " . $this->thenBody->toSexp();
        if ($this->elseBody !== null)
        {
            $result = $result . " " . $this->elseBody->toSexp();
        }
        $result = $result . ")";
        foreach ($this->redirects as $r)
        {
            $result = $result . " " . $r->toSexp();
        }
        return $result;
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class While_ implements Node
{
    public ?Node $condition;
    public ?Node $body;
    public ?array $redirects;
    public string $kind;

    public function __construct(?Node $condition, ?Node $body, ?array $redirects, string $kind)
    {
        $this->condition = $condition;
        $this->body = $body;
        $this->redirects = $redirects ?? [];
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        $base = "(while " . $this->condition->toSexp() . " " . $this->body->toSexp() . ")";
        return _appendRedirects($base, $this->redirects);
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Until implements Node
{
    public ?Node $condition;
    public ?Node $body;
    public ?array $redirects;
    public string $kind;

    public function __construct(?Node $condition, ?Node $body, ?array $redirects, string $kind)
    {
        $this->condition = $condition;
        $this->body = $body;
        $this->redirects = $redirects ?? [];
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        $base = "(until " . $this->condition->toSexp() . " " . $this->body->toSexp() . ")";
        return _appendRedirects($base, $this->redirects);
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class For_ implements Node
{
    public string $var_;
    public ?array $words;
    public ?Node $body;
    public ?array $redirects;
    public string $kind;

    public function __construct(string $var_, ?Node $body, ?array $redirects, string $kind, ?array $words = null)
    {
        $this->var_ = $var_;
        $this->body = $body;
        $this->redirects = $redirects ?? [];
        $this->kind = $kind;
        $this->words = $words;
    }

    public function toSexp(): string
    {
        $suffix = "";
        if ((count($this->redirects) > 0))
        {
            $redirectParts = [];
            foreach ($this->redirects as $r)
            {
                array_push($redirectParts, $r->toSexp());
            }
            $suffix = " " . implode(" ", $redirectParts);
        }
        $tempWord = new Word($this->var_, [], "word");
        $varFormatted = $tempWord->_formatCommandSubstitutions($this->var_, false);
        $varEscaped = str_replace("\"", "\\\"", str_replace("\\", "\\\\", $varFormatted));
        if ($this->words === null)
        {
            return "(for (word \"" . $varEscaped . "\") (in (word \"\\\"\$@\\\"\")) " . $this->body->toSexp() . ")" . $suffix;
        }
        else
        {
            if (count($this->words) === 0)
            {
                return "(for (word \"" . $varEscaped . "\") (in) " . $this->body->toSexp() . ")" . $suffix;
            }
            else
            {
                $wordParts = [];
                foreach ($this->words as $w)
                {
                    array_push($wordParts, $w->toSexp());
                }
                $wordStrs = implode(" ", $wordParts);
                return "(for (word \"" . $varEscaped . "\") (in " . $wordStrs . ") " . $this->body->toSexp() . ")" . $suffix;
            }
        }
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Forarith implements Node
{
    public string $init;
    public string $cond;
    public string $incr;
    public ?Node $body;
    public ?array $redirects;
    public string $kind;

    public function __construct(string $init, string $cond, string $incr, ?Node $body, ?array $redirects, string $kind)
    {
        $this->init = $init;
        $this->cond = $cond;
        $this->incr = $incr;
        $this->body = $body;
        $this->redirects = $redirects ?? [];
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        $suffix = "";
        if ((count($this->redirects) > 0))
        {
            $redirectParts = [];
            foreach ($this->redirects as $r)
            {
                array_push($redirectParts, $r->toSexp());
            }
            $suffix = " " . implode(" ", $redirectParts);
        }
        $initVal = (($this->init !== '') ? $this->init : "1");
        $condVal = (($this->cond !== '') ? $this->cond : "1");
        $incrVal = (($this->incr !== '') ? $this->incr : "1");
        $initStr = _formatArithVal($initVal);
        $condStr = _formatArithVal($condVal);
        $incrStr = _formatArithVal($incrVal);
        $bodyStr = $this->body->toSexp();
        return sprintf("(arith-for (init (word \"%s\")) (test (word \"%s\")) (step (word \"%s\")) %s)%s", $initStr, $condStr, $incrStr, $bodyStr, $suffix);
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Select implements Node
{
    public string $var_;
    public ?array $words;
    public ?Node $body;
    public ?array $redirects;
    public string $kind;

    public function __construct(string $var_, ?Node $body, ?array $redirects, string $kind, ?array $words = null)
    {
        $this->var_ = $var_;
        $this->body = $body;
        $this->redirects = $redirects ?? [];
        $this->kind = $kind;
        $this->words = $words;
    }

    public function toSexp(): string
    {
        $suffix = "";
        if ((count($this->redirects) > 0))
        {
            $redirectParts = [];
            foreach ($this->redirects as $r)
            {
                array_push($redirectParts, $r->toSexp());
            }
            $suffix = " " . implode(" ", $redirectParts);
        }
        $varEscaped = str_replace("\"", "\\\"", str_replace("\\", "\\\\", $this->var_));
        $inClause = "";
        if ($this->words !== null)
        {
            $wordParts = [];
            foreach ($this->words as $w)
            {
                array_push($wordParts, $w->toSexp());
            }
            $wordStrs = implode(" ", $wordParts);
            if ((count($this->words) > 0))
            {
                $inClause = "(in " . $wordStrs . ")";
            }
            else
            {
                $inClause = "(in)";
            }
        }
        else
        {
            $inClause = "(in (word \"\\\"\$@\\\"\"))";
        }
        return "(select (word \"" . $varEscaped . "\") " . $inClause . " " . $this->body->toSexp() . ")" . $suffix;
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Case_ implements Node
{
    public ?Node $word;
    public ?array $patterns;
    public ?array $redirects;
    public string $kind;

    public function __construct(?Node $word, ?array $patterns, ?array $redirects, string $kind)
    {
        $this->word = $word;
        $this->patterns = $patterns ?? [];
        $this->redirects = $redirects ?? [];
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        $parts = [];
        array_push($parts, "(case " . $this->word->toSexp());
        foreach ($this->patterns as $p)
        {
            array_push($parts, $p->toSexp());
        }
        $base = implode(" ", $parts) . ")";
        return _appendRedirects($base, $this->redirects);
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Casepattern implements Node
{
    public string $pattern;
    public ?Node $body;
    public string $terminator;
    public string $kind;

    public function __construct(string $pattern, ?Node $body, string $terminator, string $kind)
    {
        $this->pattern = $pattern;
        $this->body = $body;
        $this->terminator = $terminator;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        $alternatives = [];
        $current = [];
        $i = 0;
        $depth = 0;
        while ($i < mb_strlen($this->pattern))
        {
            $ch = (string)(mb_substr($this->pattern, $i, 1));
            if ($ch === "\\" && $i + 1 < mb_strlen($this->pattern))
            {
                array_push($current, _substring($this->pattern, $i, $i + 2));
                $i += 2;
            }
            else
            {
                if (($ch === "@" || $ch === "?" || $ch === "*" || $ch === "+" || $ch === "!") && $i + 1 < mb_strlen($this->pattern) && (string)(mb_substr($this->pattern, $i + 1, 1)) === "(")
                {
                    array_push($current, $ch);
                    array_push($current, "(");
                    $depth += 1;
                    $i += 2;
                }
                else
                {
                    if (_isExpansionStart($this->pattern, $i, "\$("))
                    {
                        array_push($current, $ch);
                        array_push($current, "(");
                        $depth += 1;
                        $i += 2;
                    }
                    else
                    {
                        if ($ch === "(" && $depth > 0)
                        {
                            array_push($current, $ch);
                            $depth += 1;
                            $i += 1;
                        }
                        else
                        {
                            if ($ch === ")" && $depth > 0)
                            {
                                array_push($current, $ch);
                                $depth -= 1;
                                $i += 1;
                            }
                            else
                            {
                                $result0 = 0;
                                $result1 = [];
                                if ($ch === "[")
                                {
                                    [$result0, $result1, $result2] = _consumeBracketClass($this->pattern, $i, $depth);
                                    $i = $result0;
                                    array_push($current, ...$result1);
                                }
                                else
                                {
                                    if ($ch === "'" && $depth === 0)
                                    {
                                        [$result0, $result1] = _consumeSingleQuote($this->pattern, $i);
                                        $i = $result0;
                                        array_push($current, ...$result1);
                                    }
                                    else
                                    {
                                        if ($ch === "\"" && $depth === 0)
                                        {
                                            [$result0, $result1] = _consumeDoubleQuote($this->pattern, $i);
                                            $i = $result0;
                                            array_push($current, ...$result1);
                                        }
                                        else
                                        {
                                            if ($ch === "|" && $depth === 0)
                                            {
                                                array_push($alternatives, implode("", $current));
                                                $current = [];
                                                $i += 1;
                                            }
                                            else
                                            {
                                                array_push($current, $ch);
                                                $i += 1;
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
        array_push($alternatives, implode("", $current));
        $wordList = [];
        foreach ($alternatives as $alt)
        {
            array_push($wordList, new Word($alt, [], "word")->toSexp());
        }
        $patternStr = implode(" ", $wordList);
        $parts = ["(pattern (" . $patternStr . ")"];
        if ($this->body !== null)
        {
            array_push($parts, " " . $this->body->toSexp());
        }
        else
        {
            array_push($parts, " ()");
        }
        array_push($parts, ")");
        return implode("", $parts);
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Function_ implements Node
{
    public string $name;
    public ?Node $body;
    public string $kind;

    public function __construct(string $name, ?Node $body, string $kind)
    {
        $this->name = $name;
        $this->body = $body;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        return "(function \"" . $this->name . "\" " . $this->body->toSexp() . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Paramexpansion implements Node
{
    public string $param;
    public string $op;
    public string $arg;
    public string $kind;

    public function __construct(string $param, string $op, string $arg, string $kind)
    {
        $this->param = $param;
        $this->op = $op;
        $this->arg = $arg;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        $escapedParam = str_replace("\"", "\\\"", str_replace("\\", "\\\\", $this->param));
        if ($this->op !== "")
        {
            $escapedOp = str_replace("\"", "\\\"", str_replace("\\", "\\\\", $this->op));
            $argVal = "";
            if ($this->arg !== "")
            {
                $argVal = $this->arg;
            }
            else
            {
                $argVal = "";
            }
            $escapedArg = str_replace("\"", "\\\"", str_replace("\\", "\\\\", $argVal));
            return "(param \"" . $escapedParam . "\" \"" . $escapedOp . "\" \"" . $escapedArg . "\")";
        }
        return "(param \"" . $escapedParam . "\")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Paramlength implements Node
{
    public string $param;
    public string $kind;

    public function __construct(string $param, string $kind)
    {
        $this->param = $param;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        $escaped = str_replace("\"", "\\\"", str_replace("\\", "\\\\", $this->param));
        return "(param-len \"" . $escaped . "\")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Paramindirect implements Node
{
    public string $param;
    public string $op;
    public string $arg;
    public string $kind;

    public function __construct(string $param, string $op, string $arg, string $kind)
    {
        $this->param = $param;
        $this->op = $op;
        $this->arg = $arg;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        $escaped = str_replace("\"", "\\\"", str_replace("\\", "\\\\", $this->param));
        if ($this->op !== "")
        {
            $escapedOp = str_replace("\"", "\\\"", str_replace("\\", "\\\\", $this->op));
            $argVal = "";
            if ($this->arg !== "")
            {
                $argVal = $this->arg;
            }
            else
            {
                $argVal = "";
            }
            $escapedArg = str_replace("\"", "\\\"", str_replace("\\", "\\\\", $argVal));
            return "(param-indirect \"" . $escaped . "\" \"" . $escapedOp . "\" \"" . $escapedArg . "\")";
        }
        return "(param-indirect \"" . $escaped . "\")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Commandsubstitution implements Node
{
    public ?Node $command;
    public bool $brace;
    public string $kind;

    public function __construct(?Node $command, bool $brace, string $kind)
    {
        $this->command = $command;
        $this->brace = $brace;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        if ($this->brace)
        {
            return "(funsub " . $this->command->toSexp() . ")";
        }
        return "(cmdsub " . $this->command->toSexp() . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Arithmeticexpansion implements Node
{
    public ?Node $expression;
    public string $kind;

    public function __construct(string $kind, ?Node $expression = null)
    {
        $this->kind = $kind;
        $this->expression = $expression;
    }

    public function toSexp(): string
    {
        if ($this->expression === null)
        {
            return "(arith)";
        }
        return "(arith " . $this->expression->toSexp() . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Arithmeticcommand implements Node
{
    public ?Node $expression;
    public ?array $redirects;
    public string $rawContent;
    public string $kind;

    public function __construct(?array $redirects, string $rawContent, string $kind, ?Node $expression = null)
    {
        $this->redirects = $redirects ?? [];
        $this->rawContent = $rawContent;
        $this->kind = $kind;
        $this->expression = $expression;
    }

    public function toSexp(): string
    {
        $formatted = new Word($this->rawContent, [], "word")->_formatCommandSubstitutions($this->rawContent, true);
        $escaped = str_replace("\t", "\\t", str_replace("\n", "\\n", str_replace("\"", "\\\"", str_replace("\\", "\\\\", $formatted))));
        $result = "(arith (word \"" . $escaped . "\"))";
        if ((count($this->redirects) > 0))
        {
            $redirectParts = [];
            foreach ($this->redirects as $r)
            {
                array_push($redirectParts, $r->toSexp());
            }
            $redirectSexps = implode(" ", $redirectParts);
            return $result . " " . $redirectSexps;
        }
        return $result;
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Arithnumber implements Node
{
    public string $value;
    public string $kind;

    public function __construct(string $value, string $kind)
    {
        $this->value = $value;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        return "(number \"" . $this->value . "\")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Arithempty implements Node
{
    public string $kind;

    public function __construct(string $kind)
    {
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        return "(empty)";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Arithvar implements Node
{
    public string $name;
    public string $kind;

    public function __construct(string $name, string $kind)
    {
        $this->name = $name;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        return "(var \"" . $this->name . "\")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Arithbinaryop implements Node
{
    public string $op;
    public ?Node $left;
    public ?Node $right;
    public string $kind;

    public function __construct(string $op, ?Node $left, ?Node $right, string $kind)
    {
        $this->op = $op;
        $this->left = $left;
        $this->right = $right;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        return "(binary-op \"" . $this->op . "\" " . $this->left->toSexp() . " " . $this->right->toSexp() . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Arithunaryop implements Node
{
    public string $op;
    public ?Node $operand;
    public string $kind;

    public function __construct(string $op, ?Node $operand, string $kind)
    {
        $this->op = $op;
        $this->operand = $operand;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        return "(unary-op \"" . $this->op . "\" " . $this->operand->toSexp() . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Arithpreincr implements Node
{
    public ?Node $operand;
    public string $kind;

    public function __construct(?Node $operand, string $kind)
    {
        $this->operand = $operand;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        return "(pre-incr " . $this->operand->toSexp() . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Arithpostincr implements Node
{
    public ?Node $operand;
    public string $kind;

    public function __construct(?Node $operand, string $kind)
    {
        $this->operand = $operand;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        return "(post-incr " . $this->operand->toSexp() . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Arithpredecr implements Node
{
    public ?Node $operand;
    public string $kind;

    public function __construct(?Node $operand, string $kind)
    {
        $this->operand = $operand;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        return "(pre-decr " . $this->operand->toSexp() . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Arithpostdecr implements Node
{
    public ?Node $operand;
    public string $kind;

    public function __construct(?Node $operand, string $kind)
    {
        $this->operand = $operand;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        return "(post-decr " . $this->operand->toSexp() . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Arithassign implements Node
{
    public string $op;
    public ?Node $target;
    public ?Node $value;
    public string $kind;

    public function __construct(string $op, ?Node $target, ?Node $value, string $kind)
    {
        $this->op = $op;
        $this->target = $target;
        $this->value = $value;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        return "(assign \"" . $this->op . "\" " . $this->target->toSexp() . " " . $this->value->toSexp() . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Arithternary implements Node
{
    public ?Node $condition;
    public ?Node $ifTrue;
    public ?Node $ifFalse;
    public string $kind;

    public function __construct(?Node $condition, ?Node $ifTrue, ?Node $ifFalse, string $kind)
    {
        $this->condition = $condition;
        $this->ifTrue = $ifTrue;
        $this->ifFalse = $ifFalse;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        return "(ternary " . $this->condition->toSexp() . " " . $this->ifTrue->toSexp() . " " . $this->ifFalse->toSexp() . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Arithcomma implements Node
{
    public ?Node $left;
    public ?Node $right;
    public string $kind;

    public function __construct(?Node $left, ?Node $right, string $kind)
    {
        $this->left = $left;
        $this->right = $right;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        return "(comma " . $this->left->toSexp() . " " . $this->right->toSexp() . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Arithsubscript implements Node
{
    public string $array_;
    public ?Node $index;
    public string $kind;

    public function __construct(string $array_, ?Node $index, string $kind)
    {
        $this->array_ = $array_;
        $this->index = $index;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        return "(subscript \"" . $this->array_ . "\" " . $this->index->toSexp() . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Arithescape implements Node
{
    public string $char;
    public string $kind;

    public function __construct(string $char, string $kind)
    {
        $this->char = $char;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        return "(escape \"" . $this->char . "\")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Arithdeprecated implements Node
{
    public string $expression;
    public string $kind;

    public function __construct(string $expression, string $kind)
    {
        $this->expression = $expression;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        $escaped = str_replace("\n", "\\n", str_replace("\"", "\\\"", str_replace("\\", "\\\\", $this->expression)));
        return "(arith-deprecated \"" . $escaped . "\")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Arithconcat implements Node
{
    public ?array $parts;
    public string $kind;

    public function __construct(?array $parts, string $kind)
    {
        $this->parts = $parts ?? [];
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        $sexps = [];
        foreach ($this->parts as $p)
        {
            array_push($sexps, $p->toSexp());
        }
        return "(arith-concat " . implode(" ", $sexps) . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Ansicquote implements Node
{
    public string $content;
    public string $kind;

    public function __construct(string $content, string $kind)
    {
        $this->content = $content;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        $escaped = str_replace("\n", "\\n", str_replace("\"", "\\\"", str_replace("\\", "\\\\", $this->content)));
        return "(ansi-c \"" . $escaped . "\")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Localestring implements Node
{
    public string $content;
    public string $kind;

    public function __construct(string $content, string $kind)
    {
        $this->content = $content;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        $escaped = str_replace("\n", "\\n", str_replace("\"", "\\\"", str_replace("\\", "\\\\", $this->content)));
        return "(locale \"" . $escaped . "\")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Processsubstitution implements Node
{
    public string $direction;
    public ?Node $command;
    public string $kind;

    public function __construct(string $direction, ?Node $command, string $kind)
    {
        $this->direction = $direction;
        $this->command = $command;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        return "(procsub \"" . $this->direction . "\" " . $this->command->toSexp() . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Negation implements Node
{
    public ?Node $pipeline;
    public string $kind;

    public function __construct(?Node $pipeline, string $kind)
    {
        $this->pipeline = $pipeline;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        if ($this->pipeline === null)
        {
            return "(negation (command))";
        }
        return "(negation " . $this->pipeline->toSexp() . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Time implements Node
{
    public ?Node $pipeline;
    public bool $posix;
    public string $kind;

    public function __construct(?Node $pipeline, bool $posix, string $kind)
    {
        $this->pipeline = $pipeline;
        $this->posix = $posix;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        if ($this->pipeline === null)
        {
            if ($this->posix)
            {
                return "(time -p (command))";
            }
            else
            {
                return "(time (command))";
            }
        }
        if ($this->posix)
        {
            return "(time -p " . $this->pipeline->toSexp() . ")";
        }
        return "(time " . $this->pipeline->toSexp() . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Conditionalexpr implements Node
{
    public mixed $body;
    public ?array $redirects;
    public string $kind;

    public function __construct(mixed $body, ?array $redirects, string $kind)
    {
        $this->body = $body;
        $this->redirects = $redirects ?? [];
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        $body = $this->body;
        $result = "";
        if ($body instanceof string)
        {
            $escaped = str_replace("\n", "\\n", str_replace("\"", "\\\"", str_replace("\\", "\\\\", $body)));
            $result = "(cond \"" . $escaped . "\")";
        }
        else
        {
            $result = "(cond " . $body->toSexp() . ")";
        }
        if ((count($this->redirects) > 0))
        {
            $redirectParts = [];
            foreach ($this->redirects as $r)
            {
                array_push($redirectParts, $r->toSexp());
            }
            $redirectSexps = implode(" ", $redirectParts);
            return $result . " " . $redirectSexps;
        }
        return $result;
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Unarytest implements Node
{
    public string $op;
    public ?Node $operand;
    public string $kind;

    public function __construct(string $op, ?Node $operand, string $kind)
    {
        $this->op = $op;
        $this->operand = $operand;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        $operandVal = $this->operand->getCondFormattedValue();
        return "(cond-unary \"" . $this->op . "\" (cond-term \"" . $operandVal . "\"))";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Binarytest implements Node
{
    public string $op;
    public ?Node $left;
    public ?Node $right;
    public string $kind;

    public function __construct(string $op, ?Node $left, ?Node $right, string $kind)
    {
        $this->op = $op;
        $this->left = $left;
        $this->right = $right;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        $leftVal = $this->left->getCondFormattedValue();
        $rightVal = $this->right->getCondFormattedValue();
        return "(cond-binary \"" . $this->op . "\" (cond-term \"" . $leftVal . "\") (cond-term \"" . $rightVal . "\"))";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Condand implements Node
{
    public ?Node $left;
    public ?Node $right;
    public string $kind;

    public function __construct(?Node $left, ?Node $right, string $kind)
    {
        $this->left = $left;
        $this->right = $right;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        return "(cond-and " . $this->left->toSexp() . " " . $this->right->toSexp() . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Condor implements Node
{
    public ?Node $left;
    public ?Node $right;
    public string $kind;

    public function __construct(?Node $left, ?Node $right, string $kind)
    {
        $this->left = $left;
        $this->right = $right;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        return "(cond-or " . $this->left->toSexp() . " " . $this->right->toSexp() . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Condnot implements Node
{
    public ?Node $operand;
    public string $kind;

    public function __construct(?Node $operand, string $kind)
    {
        $this->operand = $operand;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        return $this->operand->toSexp();
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Condparen implements Node
{
    public ?Node $inner;
    public string $kind;

    public function __construct(?Node $inner, string $kind)
    {
        $this->inner = $inner;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        return "(cond-expr " . $this->inner->toSexp() . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Array_ implements Node
{
    public ?array $elements;
    public string $kind;

    public function __construct(?array $elements, string $kind)
    {
        $this->elements = $elements ?? [];
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        if (!(count($this->elements) > 0))
        {
            return "(array)";
        }
        $parts = [];
        foreach ($this->elements as $e)
        {
            array_push($parts, $e->toSexp());
        }
        $inner = implode(" ", $parts);
        return "(array " . $inner . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Coproc implements Node
{
    public ?Node $command;
    public string $name;
    public string $kind;

    public function __construct(?Node $command, string $name, string $kind)
    {
        $this->command = $command;
        $this->name = $name;
        $this->kind = $kind;
    }

    public function toSexp(): string
    {
        $name = "";
        if (($this->name !== ''))
        {
            $name = $this->name;
        }
        else
        {
            $name = "COPROC";
        }
        return "(coproc \"" . $name . "\" " . $this->command->toSexp() . ")";
    }

    public function getKind(): string
    {
        return $this->kind;
    }
}

class Parser
{
    public string $source;
    public int $pos;
    public int $length;
    public ?array $_pendingHeredocs;
    public int $_cmdsubHeredocEnd;
    public bool $_sawNewlineInSingleQuote;
    public bool $_inProcessSub;
    public bool $_extglob;
    public ?Contextstack $_ctx;
    public ?Lexer $_lexer;
    public ?array $_tokenHistory;
    public int $_parserState;
    public int $_dolbraceState;
    public string $_eofToken;
    public int $_wordContext;
    public bool $_atCommandStart;
    public bool $_inArrayLiteral;
    public bool $_inAssignBuiltin;
    public string $_arithSrc;
    public int $_arithPos;
    public int $_arithLen;

    public function __construct(string $source, int $pos, int $length, ?array $_pendingHeredocs, int $_cmdsubHeredocEnd, bool $_sawNewlineInSingleQuote, bool $_inProcessSub, bool $_extglob, ?Contextstack $_ctx, ?Lexer $_lexer, ?array $_tokenHistory, int $_parserState, int $_dolbraceState, string $_eofToken, int $_wordContext, bool $_atCommandStart, bool $_inArrayLiteral, bool $_inAssignBuiltin, string $_arithSrc, int $_arithPos, int $_arithLen)
    {
        $this->source = $source;
        $this->pos = $pos;
        $this->length = $length;
        $this->_pendingHeredocs = $_pendingHeredocs ?? [];
        $this->_cmdsubHeredocEnd = $_cmdsubHeredocEnd;
        $this->_sawNewlineInSingleQuote = $_sawNewlineInSingleQuote;
        $this->_inProcessSub = $_inProcessSub;
        $this->_extglob = $_extglob;
        $this->_ctx = $_ctx;
        $this->_lexer = $_lexer;
        $this->_tokenHistory = $_tokenHistory ?? [];
        $this->_parserState = $_parserState;
        $this->_dolbraceState = $_dolbraceState;
        $this->_eofToken = $_eofToken;
        $this->_wordContext = $_wordContext;
        $this->_atCommandStart = $_atCommandStart;
        $this->_inArrayLiteral = $_inArrayLiteral;
        $this->_inAssignBuiltin = $_inAssignBuiltin;
        $this->_arithSrc = $_arithSrc;
        $this->_arithPos = $_arithPos;
        $this->_arithLen = $_arithLen;
    }

    public function _setState(int $flag): void
    {
        $this->_parserState = ($this->_parserState | $flag);
    }

    public function _clearState(int $flag): void
    {
        $this->_parserState = ($this->_parserState & ~$flag);
    }

    public function _inState(int $flag): bool
    {
        return ((($this->_parserState & $flag)) !== 0);
    }

    public function _saveParserState(): ?Savedparserstate
    {
        return new Savedparserstate($this->_parserState, $this->_dolbraceState, null /* TODO: unknown expression */, $this->_ctx->copyStack(), $this->_eofToken);
    }

    public function _restoreParserState(?Savedparserstate $saved): void
    {
        $this->_parserState = $saved->parserState;
        $this->_dolbraceState = $saved->dolbraceState;
        $this->_eofToken = $saved->eofToken;
        $this->_ctx->restoreFrom($saved->ctxStack);
    }

    public function _recordToken(?Token $tok): void
    {
        $this->_tokenHistory = [$tok, $this->_tokenHistory[0], $this->_tokenHistory[1], $this->_tokenHistory[2]];
    }

    public function _updateDolbraceForOp(string $op, bool $hasParam): void
    {
        if ($this->_dolbraceState === DOLBRACESTATE_NONE)
        {
            return;
        }
        if ($op === "" || mb_strlen($op) === 0)
        {
            return;
        }
        $firstChar = (string)(mb_substr($op, 0, 1));
        if ($this->_dolbraceState === DOLBRACESTATE_PARAM && $hasParam)
        {
            if ((str_contains("%#^,", $firstChar)))
            {
                $this->_dolbraceState = DOLBRACESTATE_QUOTE;
                return;
            }
            if ($firstChar === "/")
            {
                $this->_dolbraceState = DOLBRACESTATE_QUOTE2;
                return;
            }
        }
        if ($this->_dolbraceState === DOLBRACESTATE_PARAM)
        {
            if ((str_contains("#%^,~:-=?+/", $firstChar)))
            {
                $this->_dolbraceState = DOLBRACESTATE_OP;
            }
        }
    }

    public function _syncLexer(): void
    {
        if ($this->_lexer->_tokenCache !== null)
        {
            if ($this->_lexer->_tokenCache->pos !== $this->pos || $this->_lexer->_cachedWordContext !== $this->_wordContext || $this->_lexer->_cachedAtCommandStart !== $this->_atCommandStart || $this->_lexer->_cachedInArrayLiteral !== $this->_inArrayLiteral || $this->_lexer->_cachedInAssignBuiltin !== $this->_inAssignBuiltin)
            {
                $this->_lexer->_tokenCache = null;
            }
        }
        if ($this->_lexer->pos !== $this->pos)
        {
            $this->_lexer->pos = $this->pos;
        }
        $this->_lexer->_eofToken = $this->_eofToken;
        $this->_lexer->_parserState = $this->_parserState;
        $this->_lexer->_lastReadToken = $this->_tokenHistory[0];
        $this->_lexer->_wordContext = $this->_wordContext;
        $this->_lexer->_atCommandStart = $this->_atCommandStart;
        $this->_lexer->_inArrayLiteral = $this->_inArrayLiteral;
        $this->_lexer->_inAssignBuiltin = $this->_inAssignBuiltin;
    }

    public function _syncParser(): void
    {
        $this->pos = $this->_lexer->pos;
    }

    public function _lexPeekToken(): ?Token
    {
        if ($this->_lexer->_tokenCache !== null && $this->_lexer->_tokenCache->pos === $this->pos && $this->_lexer->_cachedWordContext === $this->_wordContext && $this->_lexer->_cachedAtCommandStart === $this->_atCommandStart && $this->_lexer->_cachedInArrayLiteral === $this->_inArrayLiteral && $this->_lexer->_cachedInAssignBuiltin === $this->_inAssignBuiltin)
        {
            return $this->_lexer->_tokenCache;
        }
        $savedPos = $this->pos;
        $this->_syncLexer();
        $result = $this->_lexer->peekToken();
        $this->_lexer->_cachedWordContext = $this->_wordContext;
        $this->_lexer->_cachedAtCommandStart = $this->_atCommandStart;
        $this->_lexer->_cachedInArrayLiteral = $this->_inArrayLiteral;
        $this->_lexer->_cachedInAssignBuiltin = $this->_inAssignBuiltin;
        $this->_lexer->_postReadPos = $this->_lexer->pos;
        $this->pos = $savedPos;
        return $result;
    }

    public function _lexNextToken(): ?Token
    {
        $tok = null;
        if ($this->_lexer->_tokenCache !== null && $this->_lexer->_tokenCache->pos === $this->pos && $this->_lexer->_cachedWordContext === $this->_wordContext && $this->_lexer->_cachedAtCommandStart === $this->_atCommandStart && $this->_lexer->_cachedInArrayLiteral === $this->_inArrayLiteral && $this->_lexer->_cachedInAssignBuiltin === $this->_inAssignBuiltin)
        {
            $tok = $this->_lexer->nextToken();
            $this->pos = $this->_lexer->_postReadPos;
            $this->_lexer->pos = $this->_lexer->_postReadPos;
        }
        else
        {
            $this->_syncLexer();
            $tok = $this->_lexer->nextToken();
            $this->_lexer->_cachedWordContext = $this->_wordContext;
            $this->_lexer->_cachedAtCommandStart = $this->_atCommandStart;
            $this->_lexer->_cachedInArrayLiteral = $this->_inArrayLiteral;
            $this->_lexer->_cachedInAssignBuiltin = $this->_inAssignBuiltin;
            $this->_syncParser();
        }
        $this->_recordToken($tok);
        return $tok;
    }

    public function _lexSkipBlanks(): void
    {
        $this->_syncLexer();
        $this->_lexer->skipBlanks();
        $this->_syncParser();
    }

    public function _lexSkipComment(): bool
    {
        $this->_syncLexer();
        $result = $this->_lexer->_skipComment();
        $this->_syncParser();
        return $result;
    }

    public function _lexIsCommandTerminator(): bool
    {
        $tok = $this->_lexPeekToken();
        $t = $tok->type;
        return $t === TOKENTYPE_EOF || $t === TOKENTYPE_NEWLINE || $t === TOKENTYPE_PIPE || $t === TOKENTYPE_SEMI || $t === TOKENTYPE_LPAREN || $t === TOKENTYPE_RPAREN || $t === TOKENTYPE_AMP;
    }

    public function _lexPeekOperator(): array
    {
        $tok = $this->_lexPeekToken();
        $t = $tok->type;
        if ($t >= TOKENTYPE_SEMI && $t <= TOKENTYPE_GREATER || $t >= TOKENTYPE_AND_AND && $t <= TOKENTYPE_PIPE_AMP)
        {
            return [$t, $tok->value];
        }
        return [0, ""];
    }

    public function _lexPeekReservedWord(): string
    {
        $tok = $this->_lexPeekToken();
        if ($tok->type !== TOKENTYPE_WORD)
        {
            return "";
        }
        $word = $tok->value;
        if (str_ends_with($word, "\\\n"))
        {
            $word = mb_substr($word, 0, mb_strlen($word) - 2);
        }
        if ((isset(RESERVED_WORDS[$word])) || $word === "{" || $word === "}" || $word === "[[" || $word === "]]" || $word === "!" || $word === "time")
        {
            return $word;
        }
        return "";
    }

    public function _lexIsAtReservedWord(string $word): bool
    {
        $reserved = $this->_lexPeekReservedWord();
        return $reserved === $word;
    }

    public function _lexConsumeWord(string $expected): bool
    {
        $tok = $this->_lexPeekToken();
        if ($tok->type !== TOKENTYPE_WORD)
        {
            return false;
        }
        $word = $tok->value;
        if (str_ends_with($word, "\\\n"))
        {
            $word = mb_substr($word, 0, mb_strlen($word) - 2);
        }
        if ($word === $expected)
        {
            $this->_lexNextToken();
            return true;
        }
        return false;
    }

    public function _lexPeekCaseTerminator(): string
    {
        $tok = $this->_lexPeekToken();
        $t = $tok->type;
        if ($t === TOKENTYPE_SEMI_SEMI)
        {
            return ";;";
        }
        if ($t === TOKENTYPE_SEMI_AMP)
        {
            return ";&";
        }
        if ($t === TOKENTYPE_SEMI_SEMI_AMP)
        {
            return ";;&";
        }
        return "";
    }

    public function atEnd(): bool
    {
        return $this->pos >= $this->length;
    }

    public function peek(): string
    {
        if ($this->atEnd())
        {
            return "";
        }
        return (string)(mb_substr($this->source, $this->pos, 1));
    }

    public function advance(): string
    {
        if ($this->atEnd())
        {
            return "";
        }
        $ch = (string)(mb_substr($this->source, $this->pos, 1));
        $this->pos += 1;
        return $ch;
    }

    public function peekAt(int $offset): string
    {
        $pos = $this->pos + $offset;
        if ($pos < 0 || $pos >= $this->length)
        {
            return "";
        }
        return (string)(mb_substr($this->source, $pos, 1));
    }

    public function lookahead(int $n): string
    {
        return _substring($this->source, $this->pos, $this->pos + $n);
    }

    public function _isBangFollowedByProcsub(): bool
    {
        if ($this->pos + 2 >= $this->length)
        {
            return false;
        }
        $nextChar = (string)(mb_substr($this->source, $this->pos + 1, 1));
        if ($nextChar !== ">" && $nextChar !== "<")
        {
            return false;
        }
        return (string)(mb_substr($this->source, $this->pos + 2, 1)) === "(";
    }

    public function skipWhitespace(): void
    {
        while (!$this->atEnd())
        {
            $this->_lexSkipBlanks();
            if ($this->atEnd())
            {
                break;
            }
            $ch = $this->peek();
            if ($ch === "#")
            {
                $this->_lexSkipComment();
            }
            else
            {
                if ($ch === "\\" && $this->peekAt(1) === "\n")
                {
                    $this->advance();
                    $this->advance();
                }
                else
                {
                    break;
                }
            }
        }
    }

    public function skipWhitespaceAndNewlines(): void
    {
        while (!$this->atEnd())
        {
            $ch = $this->peek();
            if (_isWhitespace($ch))
            {
                $this->advance();
                if ($ch === "\n")
                {
                    $this->_gatherHeredocBodies();
                    if ($this->_cmdsubHeredocEnd !== -1 && $this->_cmdsubHeredocEnd > $this->pos)
                    {
                        $this->pos = $this->_cmdsubHeredocEnd;
                        $this->_cmdsubHeredocEnd = -1;
                    }
                }
            }
            else
            {
                if ($ch === "#")
                {
                    while (!$this->atEnd() && $this->peek() !== "\n")
                    {
                        $this->advance();
                    }
                }
                else
                {
                    if ($ch === "\\" && $this->peekAt(1) === "\n")
                    {
                        $this->advance();
                        $this->advance();
                    }
                    else
                    {
                        break;
                    }
                }
            }
        }
    }

    public function _atListTerminatingBracket(): bool
    {
        if ($this->atEnd())
        {
            return false;
        }
        $ch = $this->peek();
        if ($this->_eofToken !== "" && $ch === $this->_eofToken)
        {
            return true;
        }
        if ($ch === ")")
        {
            return true;
        }
        if ($ch === "}")
        {
            $nextPos = $this->pos + 1;
            if ($nextPos >= $this->length)
            {
                return true;
            }
            return _isWordEndContext((string)(mb_substr($this->source, $nextPos, 1)));
        }
        return false;
    }

    public function _atEofToken(): bool
    {
        if ($this->_eofToken === "")
        {
            return false;
        }
        $tok = $this->_lexPeekToken();
        if ($this->_eofToken === ")")
        {
            return $tok->type === TOKENTYPE_RPAREN;
        }
        if ($this->_eofToken === "}")
        {
            return $tok->type === TOKENTYPE_WORD && $tok->value === "}";
        }
        return false;
    }

    public function _collectRedirects(): ?array
    {
        $redirects = [];
        while (true)
        {
            $this->skipWhitespace();
            $redirect = $this->parseRedirect();
            if ($redirect === null)
            {
                break;
            }
            array_push($redirects, $redirect);
        }
        return ((count($redirects) > 0) ? $redirects : null);
    }

    public function _parseLoopBody(string $context): ?Node
    {
        if ($this->peek() === "{")
        {
            $brace = $this->parseBraceGroup();
            if ($brace === null)
            {
                throw new Parseerror_(sprintf("Expected brace group body in %s", $context));
            }
            return $brace->body;
        }
        if ($this->_lexConsumeWord("do"))
        {
            $body = $this->parseListUntil(["done" => true]);
            if ($body === null)
            {
                throw new Parseerror_("Expected commands after 'do'");
            }
            $this->skipWhitespaceAndNewlines();
            if (!$this->_lexConsumeWord("done"))
            {
                throw new Parseerror_(sprintf("Expected 'done' to close %s", $context));
            }
            return $body;
        }
        throw new Parseerror_(sprintf("Expected 'do' or '{' in %s", $context));
    }

    public function peekWord(): string
    {
        $savedPos = $this->pos;
        $this->skipWhitespace();
        if ($this->atEnd() || _isMetachar($this->peek()))
        {
            $this->pos = $savedPos;
            return "";
        }
        $chars = [];
        while (!$this->atEnd() && !_isMetachar($this->peek()))
        {
            $ch = $this->peek();
            if (_isQuote($ch))
            {
                break;
            }
            if ($ch === "\\" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "\n")
            {
                break;
            }
            if ($ch === "\\" && $this->pos + 1 < $this->length)
            {
                array_push($chars, $this->advance());
                array_push($chars, $this->advance());
                continue;
            }
            array_push($chars, $this->advance());
        }
        $word = "";
        if ((count($chars) > 0))
        {
            $word = implode("", $chars);
        }
        else
        {
            $word = "";
        }
        $this->pos = $savedPos;
        return $word;
    }

    public function consumeWord(string $expected): bool
    {
        $savedPos = $this->pos;
        $this->skipWhitespace();
        $word = $this->peekWord();
        $keywordWord = $word;
        $hasLeadingBrace = false;
        if ($word !== "" && $this->_inProcessSub && mb_strlen($word) > 1 && (string)(mb_substr($word, 0, 1)) === "}")
        {
            $keywordWord = mb_substr($word, 1);
            $hasLeadingBrace = true;
        }
        if ($keywordWord !== $expected)
        {
            $this->pos = $savedPos;
            return false;
        }
        $this->skipWhitespace();
        if ($hasLeadingBrace)
        {
            $this->advance();
        }
        foreach (mb_str_split($expected) as $_)
        {
            $this->advance();
        }
        while ($this->peek() === "\\" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "\n")
        {
            $this->advance();
            $this->advance();
        }
        return true;
    }

    public function _isWordTerminator(int $ctx, string $ch, int $bracketDepth, int $parenDepth): bool
    {
        $this->_syncLexer();
        return $this->_lexer->_isWordTerminator($ctx, $ch, $bracketDepth, $parenDepth);
    }

    public function _scanDoubleQuote(?array &$chars, ?array $parts, int $start, bool $handleLineContinuation): void
    {
        array_push($chars, "\"");
        while (!$this->atEnd() && $this->peek() !== "\"")
        {
            $c = $this->peek();
            if ($c === "\\" && $this->pos + 1 < $this->length)
            {
                $nextC = (string)(mb_substr($this->source, $this->pos + 1, 1));
                if ($handleLineContinuation && $nextC === "\n")
                {
                    $this->advance();
                    $this->advance();
                }
                else
                {
                    array_push($chars, $this->advance());
                    array_push($chars, $this->advance());
                }
            }
            else
            {
                if ($c === "\$")
                {
                    if (!$this->_parseDollarExpansion($chars, $parts, true))
                    {
                        array_push($chars, $this->advance());
                    }
                }
                else
                {
                    array_push($chars, $this->advance());
                }
            }
        }
        if ($this->atEnd())
        {
            throw new Parseerror_("Unterminated double quote");
        }
        array_push($chars, $this->advance());
    }

    public function _parseDollarExpansion(?array &$chars, ?array &$parts, bool $inDquote): bool
    {
        $result0 = null;
        $result1 = "";
        if ($this->pos + 2 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "(" && (string)(mb_substr($this->source, $this->pos + 2, 1)) === "(")
        {
            [$result0, $result1] = $this->_parseArithmeticExpansion();
            if ($result0 !== null)
            {
                array_push($parts, $result0);
                array_push($chars, $result1);
                return true;
            }
            [$result0, $result1] = $this->_parseCommandSubstitution();
            if ($result0 !== null)
            {
                array_push($parts, $result0);
                array_push($chars, $result1);
                return true;
            }
            return false;
        }
        if ($this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "[")
        {
            [$result0, $result1] = $this->_parseDeprecatedArithmetic();
            if ($result0 !== null)
            {
                array_push($parts, $result0);
                array_push($chars, $result1);
                return true;
            }
            return false;
        }
        if ($this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "(")
        {
            [$result0, $result1] = $this->_parseCommandSubstitution();
            if ($result0 !== null)
            {
                array_push($parts, $result0);
                array_push($chars, $result1);
                return true;
            }
            return false;
        }
        [$result0, $result1] = $this->_parseParamExpansion($inDquote);
        if ($result0 !== null)
        {
            array_push($parts, $result0);
            array_push($chars, $result1);
            return true;
        }
        return false;
    }

    public function _parseWordInternal(int $ctx, bool $atCommandStart, bool $inArrayLiteral): ?Word
    {
        $this->_wordContext = $ctx;
        return $this->parseWord($atCommandStart, $inArrayLiteral, false);
    }

    public function parseWord(bool $atCommandStart, bool $inArrayLiteral, bool $inAssignBuiltin): ?Word
    {
        $this->skipWhitespace();
        if ($this->atEnd())
        {
            return null;
        }
        $this->_atCommandStart = $atCommandStart;
        $this->_inArrayLiteral = $inArrayLiteral;
        $this->_inAssignBuiltin = $inAssignBuiltin;
        $tok = $this->_lexPeekToken();
        if ($tok->type !== TOKENTYPE_WORD)
        {
            $this->_atCommandStart = false;
            $this->_inArrayLiteral = false;
            $this->_inAssignBuiltin = false;
            return null;
        }
        $this->_lexNextToken();
        $this->_atCommandStart = false;
        $this->_inArrayLiteral = false;
        $this->_inAssignBuiltin = false;
        return $tok->word;
    }

    public function _parseCommandSubstitution(): array
    {
        if ($this->atEnd() || $this->peek() !== "\$")
        {
            return [null, ""];
        }
        $start = $this->pos;
        $this->advance();
        if ($this->atEnd() || $this->peek() !== "(")
        {
            $this->pos = $start;
            return [null, ""];
        }
        $this->advance();
        $saved = $this->_saveParserState();
        $this->_setState((PARSERSTATEFLAGS_PST_CMDSUBST | PARSERSTATEFLAGS_PST_EOFTOKEN));
        $this->_eofToken = ")";
        $cmd = $this->parseList(true);
        if ($cmd === null)
        {
            $cmd = new Empty_("empty");
        }
        $this->skipWhitespaceAndNewlines();
        if ($this->atEnd() || $this->peek() !== ")")
        {
            $this->_restoreParserState($saved);
            $this->pos = $start;
            return [null, ""];
        }
        $this->advance();
        $textEnd = $this->pos;
        $text = _substring($this->source, $start, $textEnd);
        $this->_restoreParserState($saved);
        return [new Commandsubstitution($cmd, false, "cmdsub"), $text];
    }

    public function _parseFunsub(int $start): array
    {
        $this->_syncParser();
        if (!$this->atEnd() && $this->peek() === "|")
        {
            $this->advance();
        }
        $saved = $this->_saveParserState();
        $this->_setState((PARSERSTATEFLAGS_PST_CMDSUBST | PARSERSTATEFLAGS_PST_EOFTOKEN));
        $this->_eofToken = "}";
        $cmd = $this->parseList(true);
        if ($cmd === null)
        {
            $cmd = new Empty_("empty");
        }
        $this->skipWhitespaceAndNewlines();
        if ($this->atEnd() || $this->peek() !== "}")
        {
            $this->_restoreParserState($saved);
            throw new Matchedpairerror("unexpected EOF looking for `}'");
        }
        $this->advance();
        $text = _substring($this->source, $start, $this->pos);
        $this->_restoreParserState($saved);
        $this->_syncLexer();
        return [new Commandsubstitution($cmd, true, "cmdsub"), $text];
    }

    public function _isAssignmentWord(?Node $word): bool
    {
        return _assignment($word->value, 0) !== -1;
    }

    public function _parseBacktickSubstitution(): array
    {
        if ($this->atEnd() || $this->peek() !== "`")
        {
            return [null, ""];
        }
        $start = $this->pos;
        $this->advance();
        $contentChars = [];
        $textChars = ["`"];
        $pendingHeredocs = [];
        $inHeredocBody = false;
        $currentHeredocDelim = "";
        $currentHeredocStrip = false;
        $ch = "";
        while (!$this->atEnd() && ($inHeredocBody || $this->peek() !== "`"))
        {
            if ($inHeredocBody)
            {
                $lineStart = $this->pos;
                $lineEnd = $lineStart;
                while ($lineEnd < $this->length && (string)(mb_substr($this->source, $lineEnd, 1)) !== "\n")
                {
                    $lineEnd += 1;
                }
                $line = _substring($this->source, $lineStart, $lineEnd);
                $checkLine = ($currentHeredocStrip ? ltrim($line, "\t") : $line);
                if ($checkLine === $currentHeredocDelim)
                {
                    foreach (mb_str_split($line) as $ch)
                    {
                        array_push($contentChars, $ch);
                        array_push($textChars, $ch);
                    }
                    $this->pos = $lineEnd;
                    if ($this->pos < $this->length && (string)(mb_substr($this->source, $this->pos, 1)) === "\n")
                    {
                        array_push($contentChars, "\n");
                        array_push($textChars, "\n");
                        $this->advance();
                    }
                    $inHeredocBody = false;
                    if (count($pendingHeredocs) > 0)
                    {
                        [$currentHeredocDelim, $currentHeredocStrip] = array_shift($pendingHeredocs);
                        $inHeredocBody = true;
                    }
                }
                else
                {
                    if (str_starts_with($checkLine, $currentHeredocDelim) && mb_strlen($checkLine) > mb_strlen($currentHeredocDelim))
                    {
                        $tabsStripped = mb_strlen($line) - mb_strlen($checkLine);
                        $endPos = $tabsStripped + mb_strlen($currentHeredocDelim);
                        for ($i = 0; $i < $endPos; $i += 1)
                        {
                            array_push($contentChars, (string)(mb_substr($line, $i, 1)));
                            array_push($textChars, (string)(mb_substr($line, $i, 1)));
                        }
                        $this->pos = $lineStart + $endPos;
                        $inHeredocBody = false;
                        if (count($pendingHeredocs) > 0)
                        {
                            [$currentHeredocDelim, $currentHeredocStrip] = array_shift($pendingHeredocs);
                            $inHeredocBody = true;
                        }
                    }
                    else
                    {
                        foreach (mb_str_split($line) as $ch)
                        {
                            array_push($contentChars, $ch);
                            array_push($textChars, $ch);
                        }
                        $this->pos = $lineEnd;
                        if ($this->pos < $this->length && (string)(mb_substr($this->source, $this->pos, 1)) === "\n")
                        {
                            array_push($contentChars, "\n");
                            array_push($textChars, "\n");
                            $this->advance();
                        }
                    }
                }
                continue;
            }
            $c = $this->peek();
            if ($c === "\\" && $this->pos + 1 < $this->length)
            {
                $nextC = (string)(mb_substr($this->source, $this->pos + 1, 1));
                if ($nextC === "\n")
                {
                    $this->advance();
                    $this->advance();
                }
                else
                {
                    if (_isEscapeCharInBacktick($nextC))
                    {
                        $this->advance();
                        $escaped = $this->advance();
                        array_push($contentChars, $escaped);
                        array_push($textChars, "\\");
                        array_push($textChars, $escaped);
                    }
                    else
                    {
                        $ch = $this->advance();
                        array_push($contentChars, $ch);
                        array_push($textChars, $ch);
                    }
                }
                continue;
            }
            if ($c === "<" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "<")
            {
                $quote = "";
                if ($this->pos + 2 < $this->length && (string)(mb_substr($this->source, $this->pos + 2, 1)) === "<")
                {
                    array_push($contentChars, $this->advance());
                    array_push($textChars, "<");
                    array_push($contentChars, $this->advance());
                    array_push($textChars, "<");
                    array_push($contentChars, $this->advance());
                    array_push($textChars, "<");
                    while (!$this->atEnd() && _isWhitespaceNoNewline($this->peek()))
                    {
                        $ch = $this->advance();
                        array_push($contentChars, $ch);
                        array_push($textChars, $ch);
                    }
                    while (!$this->atEnd() && !_isWhitespace($this->peek()) && ((!str_contains("()", $this->peek()))))
                    {
                        if ($this->peek() === "\\" && $this->pos + 1 < $this->length)
                        {
                            $ch = $this->advance();
                            array_push($contentChars, $ch);
                            array_push($textChars, $ch);
                            $ch = $this->advance();
                            array_push($contentChars, $ch);
                            array_push($textChars, $ch);
                        }
                        else
                        {
                            if ((str_contains("\"'", $this->peek())))
                            {
                                $quote = $this->peek();
                                $ch = $this->advance();
                                array_push($contentChars, $ch);
                                array_push($textChars, $ch);
                                while (!$this->atEnd() && $this->peek() !== $quote)
                                {
                                    if ($quote === "\"" && $this->peek() === "\\")
                                    {
                                        $ch = $this->advance();
                                        array_push($contentChars, $ch);
                                        array_push($textChars, $ch);
                                    }
                                    $ch = $this->advance();
                                    array_push($contentChars, $ch);
                                    array_push($textChars, $ch);
                                }
                                if (!$this->atEnd())
                                {
                                    $ch = $this->advance();
                                    array_push($contentChars, $ch);
                                    array_push($textChars, $ch);
                                }
                            }
                            else
                            {
                                $ch = $this->advance();
                                array_push($contentChars, $ch);
                                array_push($textChars, $ch);
                            }
                        }
                    }
                    continue;
                }
                array_push($contentChars, $this->advance());
                array_push($textChars, "<");
                array_push($contentChars, $this->advance());
                array_push($textChars, "<");
                $stripTabs = false;
                if (!$this->atEnd() && $this->peek() === "-")
                {
                    $stripTabs = true;
                    array_push($contentChars, $this->advance());
                    array_push($textChars, "-");
                }
                while (!$this->atEnd() && _isWhitespaceNoNewline($this->peek()))
                {
                    $ch = $this->advance();
                    array_push($contentChars, $ch);
                    array_push($textChars, $ch);
                }
                $delimiterChars = [];
                if (!$this->atEnd())
                {
                    $ch = $this->peek();
                    $dch = "";
                    $closing = "";
                    if (_isQuote($ch))
                    {
                        $quote = $this->advance();
                        array_push($contentChars, $quote);
                        array_push($textChars, $quote);
                        while (!$this->atEnd() && $this->peek() !== $quote)
                        {
                            $dch = $this->advance();
                            array_push($contentChars, $dch);
                            array_push($textChars, $dch);
                            array_push($delimiterChars, $dch);
                        }
                        if (!$this->atEnd())
                        {
                            $closing = $this->advance();
                            array_push($contentChars, $closing);
                            array_push($textChars, $closing);
                        }
                    }
                    else
                    {
                        $esc = "";
                        if ($ch === "\\")
                        {
                            $esc = $this->advance();
                            array_push($contentChars, $esc);
                            array_push($textChars, $esc);
                            if (!$this->atEnd())
                            {
                                $dch = $this->advance();
                                array_push($contentChars, $dch);
                                array_push($textChars, $dch);
                                array_push($delimiterChars, $dch);
                            }
                            while (!$this->atEnd() && !_isMetachar($this->peek()))
                            {
                                $dch = $this->advance();
                                array_push($contentChars, $dch);
                                array_push($textChars, $dch);
                                array_push($delimiterChars, $dch);
                            }
                        }
                        else
                        {
                            while (!$this->atEnd() && !_isMetachar($this->peek()) && $this->peek() !== "`")
                            {
                                $ch = $this->peek();
                                if (_isQuote($ch))
                                {
                                    $quote = $this->advance();
                                    array_push($contentChars, $quote);
                                    array_push($textChars, $quote);
                                    while (!$this->atEnd() && $this->peek() !== $quote)
                                    {
                                        $dch = $this->advance();
                                        array_push($contentChars, $dch);
                                        array_push($textChars, $dch);
                                        array_push($delimiterChars, $dch);
                                    }
                                    if (!$this->atEnd())
                                    {
                                        $closing = $this->advance();
                                        array_push($contentChars, $closing);
                                        array_push($textChars, $closing);
                                    }
                                }
                                else
                                {
                                    if ($ch === "\\")
                                    {
                                        $esc = $this->advance();
                                        array_push($contentChars, $esc);
                                        array_push($textChars, $esc);
                                        if (!$this->atEnd())
                                        {
                                            $dch = $this->advance();
                                            array_push($contentChars, $dch);
                                            array_push($textChars, $dch);
                                            array_push($delimiterChars, $dch);
                                        }
                                    }
                                    else
                                    {
                                        $dch = $this->advance();
                                        array_push($contentChars, $dch);
                                        array_push($textChars, $dch);
                                        array_push($delimiterChars, $dch);
                                    }
                                }
                            }
                        }
                    }
                }
                $delimiter = implode("", $delimiterChars);
                if (($delimiter !== ''))
                {
                    array_push($pendingHeredocs, [$delimiter, $stripTabs]);
                }
                continue;
            }
            if ($c === "\n")
            {
                $ch = $this->advance();
                array_push($contentChars, $ch);
                array_push($textChars, $ch);
                if (count($pendingHeredocs) > 0)
                {
                    [$currentHeredocDelim, $currentHeredocStrip] = array_shift($pendingHeredocs);
                    $inHeredocBody = true;
                }
                continue;
            }
            $ch = $this->advance();
            array_push($contentChars, $ch);
            array_push($textChars, $ch);
        }
        if ($this->atEnd())
        {
            throw new Parseerror_("Unterminated backtick");
        }
        $this->advance();
        array_push($textChars, "`");
        $text = implode("", $textChars);
        $content = implode("", $contentChars);
        if (count($pendingHeredocs) > 0)
        {
            [$heredocStart, $heredocEnd] = _findHeredocContentEnd($this->source, $this->pos, $pendingHeredocs);
            if ($heredocEnd > $heredocStart)
            {
                $content = $content . _substring($this->source, $heredocStart, $heredocEnd);
                if ($this->_cmdsubHeredocEnd === -1)
                {
                    $this->_cmdsubHeredocEnd = $heredocEnd;
                }
                else
                {
                    $this->_cmdsubHeredocEnd = ($this->_cmdsubHeredocEnd > $heredocEnd ? $this->_cmdsubHeredocEnd : $heredocEnd);
                }
            }
        }
        $subParser = newParser($content, false, $this->_extglob);
        $cmd = $subParser->parseList(true);
        if ($cmd === null)
        {
            $cmd = new Empty_("empty");
        }
        return [new Commandsubstitution($cmd, false, "cmdsub"), $text];
    }

    public function _parseProcessSubstitution(): array
    {
        if ($this->atEnd() || !_isRedirectChar($this->peek()))
        {
            return [null, ""];
        }
        $start = $this->pos;
        $direction = $this->advance();
        if ($this->atEnd() || $this->peek() !== "(")
        {
            $this->pos = $start;
            return [null, ""];
        }
        $this->advance();
        $saved = $this->_saveParserState();
        $oldInProcessSub = $this->_inProcessSub;
        $this->_inProcessSub = true;
        $this->_setState(PARSERSTATEFLAGS_PST_EOFTOKEN);
        $this->_eofToken = ")";
        try
        {
            $cmd = $this->parseList(true);
            if ($cmd === null)
            {
                $cmd = new Empty_("empty");
            }
            $this->skipWhitespaceAndNewlines();
            if ($this->atEnd() || $this->peek() !== ")")
            {
                throw new Parseerror_("Invalid process substitution");
            }
            $this->advance();
            $textEnd = $this->pos;
            $text = _substring($this->source, $start, $textEnd);
            $text = _stripLineContinuationsCommentAware($text);
            $this->_restoreParserState($saved);
            $this->_inProcessSub = $oldInProcessSub;
            return [new Processsubstitution($direction, $cmd, "procsub"), $text];
        } catch (Parseerror_ $e)
        {
            $this->_restoreParserState($saved);
            $this->_inProcessSub = $oldInProcessSub;
            $contentStartChar = ($start + 2 < $this->length ? (string)(mb_substr($this->source, $start + 2, 1)) : "");
            if ((str_contains(" \t\n", $contentStartChar)))
            {
                throw $e;
            }
            $this->pos = $start + 2;
            $this->_lexer->pos = $this->pos;
            $this->_lexer->_parseMatchedPair("(", ")", 0, false);
            $this->pos = $this->_lexer->pos;
            $text = _substring($this->source, $start, $this->pos);
            $text = _stripLineContinuationsCommentAware($text);
            return [null, $text];
        }
    }

    public function _parseArrayLiteral(): array
    {
        if ($this->atEnd() || $this->peek() !== "(")
        {
            return [null, ""];
        }
        $start = $this->pos;
        $this->advance();
        $this->_setState(PARSERSTATEFLAGS_PST_COMPASSIGN);
        $elements = [];
        while (true)
        {
            $this->skipWhitespaceAndNewlines();
            if ($this->atEnd())
            {
                $this->_clearState(PARSERSTATEFLAGS_PST_COMPASSIGN);
                throw new Parseerror_("Unterminated array literal");
            }
            if ($this->peek() === ")")
            {
                break;
            }
            $word = $this->parseWord(false, true, false);
            if ($word === null)
            {
                if ($this->peek() === ")")
                {
                    break;
                }
                $this->_clearState(PARSERSTATEFLAGS_PST_COMPASSIGN);
                throw new Parseerror_("Expected word in array literal");
            }
            array_push($elements, $word);
        }
        if ($this->atEnd() || $this->peek() !== ")")
        {
            $this->_clearState(PARSERSTATEFLAGS_PST_COMPASSIGN);
            throw new Parseerror_("Expected ) to close array literal");
        }
        $this->advance();
        $text = _substring($this->source, $start, $this->pos);
        $this->_clearState(PARSERSTATEFLAGS_PST_COMPASSIGN);
        return [new Array_($elements, "array"), $text];
    }

    public function _parseArithmeticExpansion(): array
    {
        if ($this->atEnd() || $this->peek() !== "\$")
        {
            return [null, ""];
        }
        $start = $this->pos;
        if ($this->pos + 2 >= $this->length || (string)(mb_substr($this->source, $this->pos + 1, 1)) !== "(" || (string)(mb_substr($this->source, $this->pos + 2, 1)) !== "(")
        {
            return [null, ""];
        }
        $this->advance();
        $this->advance();
        $this->advance();
        $contentStart = $this->pos;
        $depth = 2;
        $firstClosePos = -1;
        while (!$this->atEnd() && $depth > 0)
        {
            $c = $this->peek();
            if ($c === "'")
            {
                $this->advance();
                while (!$this->atEnd() && $this->peek() !== "'")
                {
                    $this->advance();
                }
                if (!$this->atEnd())
                {
                    $this->advance();
                }
            }
            else
            {
                if ($c === "\"")
                {
                    $this->advance();
                    while (!$this->atEnd())
                    {
                        if ($this->peek() === "\\" && $this->pos + 1 < $this->length)
                        {
                            $this->advance();
                            $this->advance();
                        }
                        else
                        {
                            if ($this->peek() === "\"")
                            {
                                $this->advance();
                                break;
                            }
                            else
                            {
                                $this->advance();
                            }
                        }
                    }
                }
                else
                {
                    if ($c === "\\" && $this->pos + 1 < $this->length)
                    {
                        $this->advance();
                        $this->advance();
                    }
                    else
                    {
                        if ($c === "(")
                        {
                            $depth += 1;
                            $this->advance();
                        }
                        else
                        {
                            if ($c === ")")
                            {
                                if ($depth === 2)
                                {
                                    $firstClosePos = $this->pos;
                                }
                                $depth -= 1;
                                if ($depth === 0)
                                {
                                    break;
                                }
                                $this->advance();
                            }
                            else
                            {
                                if ($depth === 1)
                                {
                                    $firstClosePos = -1;
                                }
                                $this->advance();
                            }
                        }
                    }
                }
            }
        }
        if ($depth !== 0)
        {
            if ($this->atEnd())
            {
                throw new Matchedpairerror("unexpected EOF looking for `))'");
            }
            $this->pos = $start;
            return [null, ""];
        }
        $content = "";
        if ($firstClosePos !== -1)
        {
            $content = _substring($this->source, $contentStart, $firstClosePos);
        }
        else
        {
            $content = _substring($this->source, $contentStart, $this->pos);
        }
        $this->advance();
        $text = _substring($this->source, $start, $this->pos);
        $expr = null;
        try
        {
            $expr = $this->_parseArithExpr($content);
        } catch (Parseerror_ $ex)
        {
            $this->pos = $start;
            return [null, ""];
        }
        return [new Arithmeticexpansion("arith", $expr), $text];
    }

    public function _parseArithExpr(string $content): ?Node
    {
        $savedArithSrc = $this->_arithSrc;
        $savedArithPos = $this->_arithPos;
        $savedArithLen = $this->_arithLen;
        $savedParserState = $this->_parserState;
        $this->_setState(PARSERSTATEFLAGS_PST_ARITH);
        $this->_arithSrc = $content;
        $this->_arithPos = 0;
        $this->_arithLen = mb_strlen($content);
        $this->_arithSkipWs();
        $result = null;
        if ($this->_arithAtEnd())
        {
            $result = null;
        }
        else
        {
            $result = $this->_arithParseComma();
        }
        $this->_parserState = $savedParserState;
        if ($savedArithSrc !== "")
        {
            $this->_arithSrc = $savedArithSrc;
            $this->_arithPos = $savedArithPos;
            $this->_arithLen = $savedArithLen;
        }
        return $result;
    }

    public function _arithAtEnd(): bool
    {
        return $this->_arithPos >= $this->_arithLen;
    }

    public function _arithPeek(int $offset): string
    {
        $pos = $this->_arithPos + $offset;
        if ($pos >= $this->_arithLen)
        {
            return "";
        }
        return (string)(mb_substr($this->_arithSrc, $pos, 1));
    }

    public function _arithAdvance(): string
    {
        if ($this->_arithAtEnd())
        {
            return "";
        }
        $c = (string)(mb_substr($this->_arithSrc, $this->_arithPos, 1));
        $this->_arithPos += 1;
        return $c;
    }

    public function _arithSkipWs(): void
    {
        while (!$this->_arithAtEnd())
        {
            $c = (string)(mb_substr($this->_arithSrc, $this->_arithPos, 1));
            if (_isWhitespace($c))
            {
                $this->_arithPos += 1;
            }
            else
            {
                if ($c === "\\" && $this->_arithPos + 1 < $this->_arithLen && (string)(mb_substr($this->_arithSrc, $this->_arithPos + 1, 1)) === "\n")
                {
                    $this->_arithPos += 2;
                }
                else
                {
                    break;
                }
            }
        }
    }

    public function _arithMatch(string $s): bool
    {
        return _startsWithAt($this->_arithSrc, $this->_arithPos, $s);
    }

    public function _arithConsume(string $s): bool
    {
        if ($this->_arithMatch($s))
        {
            $this->_arithPos += mb_strlen($s);
            return true;
        }
        return false;
    }

    public function _arithParseComma(): ?Node
    {
        $left = $this->_arithParseAssign();
        while (true)
        {
            $this->_arithSkipWs();
            if ($this->_arithConsume(","))
            {
                $this->_arithSkipWs();
                $right = $this->_arithParseAssign();
                $left = new Arithcomma($left, $right, "comma");
            }
            else
            {
                break;
            }
        }
        return $left;
    }

    public function _arithParseAssign(): ?Node
    {
        $left = $this->_arithParseTernary();
        $this->_arithSkipWs();
        $assignOps = ["<<=", ">>=", "+=", "-=", "*=", "/=", "%=", "&=", "^=", "|=", "="];
        foreach ($assignOps as $op)
        {
            if ($this->_arithMatch($op))
            {
                if ($op === "=" && $this->_arithPeek(1) === "=")
                {
                    break;
                }
                $this->_arithConsume($op);
                $this->_arithSkipWs();
                $right = $this->_arithParseAssign();
                return new Arithassign($op, $left, $right, "assign");
            }
        }
        return $left;
    }

    public function _arithParseTernary(): ?Node
    {
        $cond = $this->_arithParseLogicalOr();
        $this->_arithSkipWs();
        if ($this->_arithConsume("?"))
        {
            $this->_arithSkipWs();
            $ifTrue = null;
            if ($this->_arithMatch(":"))
            {
                $ifTrue = null;
            }
            else
            {
                $ifTrue = $this->_arithParseAssign();
            }
            $this->_arithSkipWs();
            $ifFalse = null;
            if ($this->_arithConsume(":"))
            {
                $this->_arithSkipWs();
                if ($this->_arithAtEnd() || $this->_arithPeek(0) === ")")
                {
                    $ifFalse = null;
                }
                else
                {
                    $ifFalse = $this->_arithParseTernary();
                }
            }
            else
            {
                $ifFalse = null;
            }
            return new Arithternary($cond, $ifTrue, $ifFalse, "ternary");
        }
        return $cond;
    }

    public function _arithParseLeftAssoc(?array $ops, callable $parsefn): ?Node
    {
        $left = $parsefn();
        while (true)
        {
            $this->_arithSkipWs();
            $matched = false;
            foreach ($ops as $op)
            {
                if ($this->_arithMatch($op))
                {
                    $this->_arithConsume($op);
                    $this->_arithSkipWs();
                    $left = new Arithbinaryop($op, $left, $parsefn(), "binary-op");
                    $matched = true;
                    break;
                }
            }
            if (!$matched)
            {
                break;
            }
        }
        return $left;
    }

    public function _arithParseLogicalOr(): ?Node
    {
        return $this->_arithParseLeftAssoc(["||"], [$this, '_arithParseLogicalAnd']);
    }

    public function _arithParseLogicalAnd(): ?Node
    {
        return $this->_arithParseLeftAssoc(["&&"], [$this, '_arithParseBitwiseOr']);
    }

    public function _arithParseBitwiseOr(): ?Node
    {
        $left = $this->_arithParseBitwiseXor();
        while (true)
        {
            $this->_arithSkipWs();
            if ($this->_arithPeek(0) === "|" && $this->_arithPeek(1) !== "|" && $this->_arithPeek(1) !== "=")
            {
                $this->_arithAdvance();
                $this->_arithSkipWs();
                $right = $this->_arithParseBitwiseXor();
                $left = new Arithbinaryop("|", $left, $right, "binary-op");
            }
            else
            {
                break;
            }
        }
        return $left;
    }

    public function _arithParseBitwiseXor(): ?Node
    {
        $left = $this->_arithParseBitwiseAnd();
        while (true)
        {
            $this->_arithSkipWs();
            if ($this->_arithPeek(0) === "^" && $this->_arithPeek(1) !== "=")
            {
                $this->_arithAdvance();
                $this->_arithSkipWs();
                $right = $this->_arithParseBitwiseAnd();
                $left = new Arithbinaryop("^", $left, $right, "binary-op");
            }
            else
            {
                break;
            }
        }
        return $left;
    }

    public function _arithParseBitwiseAnd(): ?Node
    {
        $left = $this->_arithParseEquality();
        while (true)
        {
            $this->_arithSkipWs();
            if ($this->_arithPeek(0) === "&" && $this->_arithPeek(1) !== "&" && $this->_arithPeek(1) !== "=")
            {
                $this->_arithAdvance();
                $this->_arithSkipWs();
                $right = $this->_arithParseEquality();
                $left = new Arithbinaryop("&", $left, $right, "binary-op");
            }
            else
            {
                break;
            }
        }
        return $left;
    }

    public function _arithParseEquality(): ?Node
    {
        return $this->_arithParseLeftAssoc(["==", "!="], [$this, '_arithParseComparison']);
    }

    public function _arithParseComparison(): ?Node
    {
        $left = $this->_arithParseShift();
        while (true)
        {
            $this->_arithSkipWs();
            $right = null;
            if ($this->_arithMatch("<="))
            {
                $this->_arithConsume("<=");
                $this->_arithSkipWs();
                $right = $this->_arithParseShift();
                $left = new Arithbinaryop("<=", $left, $right, "binary-op");
            }
            else
            {
                if ($this->_arithMatch(">="))
                {
                    $this->_arithConsume(">=");
                    $this->_arithSkipWs();
                    $right = $this->_arithParseShift();
                    $left = new Arithbinaryop(">=", $left, $right, "binary-op");
                }
                else
                {
                    if ($this->_arithPeek(0) === "<" && $this->_arithPeek(1) !== "<" && $this->_arithPeek(1) !== "=")
                    {
                        $this->_arithAdvance();
                        $this->_arithSkipWs();
                        $right = $this->_arithParseShift();
                        $left = new Arithbinaryop("<", $left, $right, "binary-op");
                    }
                    else
                    {
                        if ($this->_arithPeek(0) === ">" && $this->_arithPeek(1) !== ">" && $this->_arithPeek(1) !== "=")
                        {
                            $this->_arithAdvance();
                            $this->_arithSkipWs();
                            $right = $this->_arithParseShift();
                            $left = new Arithbinaryop(">", $left, $right, "binary-op");
                        }
                        else
                        {
                            break;
                        }
                    }
                }
            }
        }
        return $left;
    }

    public function _arithParseShift(): ?Node
    {
        $left = $this->_arithParseAdditive();
        while (true)
        {
            $this->_arithSkipWs();
            if ($this->_arithMatch("<<="))
            {
                break;
            }
            if ($this->_arithMatch(">>="))
            {
                break;
            }
            $right = null;
            if ($this->_arithMatch("<<"))
            {
                $this->_arithConsume("<<");
                $this->_arithSkipWs();
                $right = $this->_arithParseAdditive();
                $left = new Arithbinaryop("<<", $left, $right, "binary-op");
            }
            else
            {
                if ($this->_arithMatch(">>"))
                {
                    $this->_arithConsume(">>");
                    $this->_arithSkipWs();
                    $right = $this->_arithParseAdditive();
                    $left = new Arithbinaryop(">>", $left, $right, "binary-op");
                }
                else
                {
                    break;
                }
            }
        }
        return $left;
    }

    public function _arithParseAdditive(): ?Node
    {
        $left = $this->_arithParseMultiplicative();
        while (true)
        {
            $this->_arithSkipWs();
            $c = $this->_arithPeek(0);
            $c2 = $this->_arithPeek(1);
            $right = null;
            if ($c === "+" && $c2 !== "+" && $c2 !== "=")
            {
                $this->_arithAdvance();
                $this->_arithSkipWs();
                $right = $this->_arithParseMultiplicative();
                $left = new Arithbinaryop("+", $left, $right, "binary-op");
            }
            else
            {
                if ($c === "-" && $c2 !== "-" && $c2 !== "=")
                {
                    $this->_arithAdvance();
                    $this->_arithSkipWs();
                    $right = $this->_arithParseMultiplicative();
                    $left = new Arithbinaryop("-", $left, $right, "binary-op");
                }
                else
                {
                    break;
                }
            }
        }
        return $left;
    }

    public function _arithParseMultiplicative(): ?Node
    {
        $left = $this->_arithParseExponentiation();
        while (true)
        {
            $this->_arithSkipWs();
            $c = $this->_arithPeek(0);
            $c2 = $this->_arithPeek(1);
            $right = null;
            if ($c === "*" && $c2 !== "*" && $c2 !== "=")
            {
                $this->_arithAdvance();
                $this->_arithSkipWs();
                $right = $this->_arithParseExponentiation();
                $left = new Arithbinaryop("*", $left, $right, "binary-op");
            }
            else
            {
                if ($c === "/" && $c2 !== "=")
                {
                    $this->_arithAdvance();
                    $this->_arithSkipWs();
                    $right = $this->_arithParseExponentiation();
                    $left = new Arithbinaryop("/", $left, $right, "binary-op");
                }
                else
                {
                    if ($c === "%" && $c2 !== "=")
                    {
                        $this->_arithAdvance();
                        $this->_arithSkipWs();
                        $right = $this->_arithParseExponentiation();
                        $left = new Arithbinaryop("%", $left, $right, "binary-op");
                    }
                    else
                    {
                        break;
                    }
                }
            }
        }
        return $left;
    }

    public function _arithParseExponentiation(): ?Node
    {
        $left = $this->_arithParseUnary();
        $this->_arithSkipWs();
        if ($this->_arithMatch("**"))
        {
            $this->_arithConsume("**");
            $this->_arithSkipWs();
            $right = $this->_arithParseExponentiation();
            return new Arithbinaryop("**", $left, $right, "binary-op");
        }
        return $left;
    }

    public function _arithParseUnary(): ?Node
    {
        $this->_arithSkipWs();
        $operand = null;
        if ($this->_arithMatch("++"))
        {
            $this->_arithConsume("++");
            $this->_arithSkipWs();
            $operand = $this->_arithParseUnary();
            return new Arithpreincr($operand, "pre-incr");
        }
        if ($this->_arithMatch("--"))
        {
            $this->_arithConsume("--");
            $this->_arithSkipWs();
            $operand = $this->_arithParseUnary();
            return new Arithpredecr($operand, "pre-decr");
        }
        $c = $this->_arithPeek(0);
        if ($c === "!")
        {
            $this->_arithAdvance();
            $this->_arithSkipWs();
            $operand = $this->_arithParseUnary();
            return new Arithunaryop("!", $operand, "unary-op");
        }
        if ($c === "~")
        {
            $this->_arithAdvance();
            $this->_arithSkipWs();
            $operand = $this->_arithParseUnary();
            return new Arithunaryop("~", $operand, "unary-op");
        }
        if ($c === "+" && $this->_arithPeek(1) !== "+")
        {
            $this->_arithAdvance();
            $this->_arithSkipWs();
            $operand = $this->_arithParseUnary();
            return new Arithunaryop("+", $operand, "unary-op");
        }
        if ($c === "-" && $this->_arithPeek(1) !== "-")
        {
            $this->_arithAdvance();
            $this->_arithSkipWs();
            $operand = $this->_arithParseUnary();
            return new Arithunaryop("-", $operand, "unary-op");
        }
        return $this->_arithParsePostfix();
    }

    public function _arithParsePostfix(): ?Node
    {
        $left = $this->_arithParsePrimary();
        while (true)
        {
            $this->_arithSkipWs();
            if ($this->_arithMatch("++"))
            {
                $this->_arithConsume("++");
                $left = new Arithpostincr($left, "post-incr");
            }
            else
            {
                if ($this->_arithMatch("--"))
                {
                    $this->_arithConsume("--");
                    $left = new Arithpostdecr($left, "post-decr");
                }
                else
                {
                    if ($this->_arithPeek(0) === "[")
                    {
                        if ($left instanceof Arithvar)
                        {
                            $this->_arithAdvance();
                            $this->_arithSkipWs();
                            $index = $this->_arithParseComma();
                            $this->_arithSkipWs();
                            if (!$this->_arithConsume("]"))
                            {
                                throw new Parseerror_("Expected ']' in array subscript");
                            }
                            $left = new Arithsubscript($left->name, $index, "subscript");
                        }
                        else
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
        return $left;
    }

    public function _arithParsePrimary(): ?Node
    {
        $this->_arithSkipWs();
        $c = $this->_arithPeek(0);
        if ($c === "(")
        {
            $this->_arithAdvance();
            $this->_arithSkipWs();
            $expr = $this->_arithParseComma();
            $this->_arithSkipWs();
            if (!$this->_arithConsume(")"))
            {
                throw new Parseerror_("Expected ')' in arithmetic expression");
            }
            return $expr;
        }
        if ($c === "#" && $this->_arithPeek(1) === "\$")
        {
            $this->_arithAdvance();
            return $this->_arithParseExpansion();
        }
        if ($c === "\$")
        {
            return $this->_arithParseExpansion();
        }
        if ($c === "'")
        {
            return $this->_arithParseSingleQuote();
        }
        if ($c === "\"")
        {
            return $this->_arithParseDoubleQuote();
        }
        if ($c === "`")
        {
            return $this->_arithParseBacktick();
        }
        if ($c === "\\")
        {
            $this->_arithAdvance();
            if ($this->_arithAtEnd())
            {
                throw new Parseerror_("Unexpected end after backslash in arithmetic");
            }
            $escapedChar = $this->_arithAdvance();
            return new Arithescape($escapedChar, "escape");
        }
        if ($this->_arithAtEnd() || ((str_contains(")]:,;?|&<>=!+-*/%^~#{}", $c))))
        {
            return new Arithempty("empty");
        }
        return $this->_arithParseNumberOrVar();
    }

    public function _arithParseExpansion(): ?Node
    {
        if (!$this->_arithConsume("\$"))
        {
            throw new Parseerror_("Expected '\$'");
        }
        $c = $this->_arithPeek(0);
        if ($c === "(")
        {
            return $this->_arithParseCmdsub();
        }
        if ($c === "{")
        {
            return $this->_arithParseBracedParam();
        }
        $nameChars = [];
        while (!$this->_arithAtEnd())
        {
            $ch = $this->_arithPeek(0);
            if (ctype_alnum($ch) || $ch === "_")
            {
                array_push($nameChars, $this->_arithAdvance());
            }
            else
            {
                if ((_isSpecialParamOrDigit($ch) || $ch === "#") && !(count($nameChars) > 0))
                {
                    array_push($nameChars, $this->_arithAdvance());
                    break;
                }
                else
                {
                    break;
                }
            }
        }
        if (!(count($nameChars) > 0))
        {
            throw new Parseerror_("Expected variable name after \$");
        }
        return new Paramexpansion(implode("", $nameChars), "", "", "param");
    }

    public function _arithParseCmdsub(): ?Node
    {
        $this->_arithAdvance();
        $depth = 0;
        $contentStart = 0;
        $ch = "";
        $content = "";
        if ($this->_arithPeek(0) === "(")
        {
            $this->_arithAdvance();
            $depth = 1;
            $contentStart = $this->_arithPos;
            while (!$this->_arithAtEnd() && $depth > 0)
            {
                $ch = $this->_arithPeek(0);
                if ($ch === "(")
                {
                    $depth += 1;
                    $this->_arithAdvance();
                }
                else
                {
                    if ($ch === ")")
                    {
                        if ($depth === 1 && $this->_arithPeek(1) === ")")
                        {
                            break;
                        }
                        $depth -= 1;
                        $this->_arithAdvance();
                    }
                    else
                    {
                        $this->_arithAdvance();
                    }
                }
            }
            $content = _substring($this->_arithSrc, $contentStart, $this->_arithPos);
            $this->_arithAdvance();
            $this->_arithAdvance();
            $innerExpr = $this->_parseArithExpr($content);
            return new Arithmeticexpansion("arith", $innerExpr);
        }
        $depth = 1;
        $contentStart = $this->_arithPos;
        while (!$this->_arithAtEnd() && $depth > 0)
        {
            $ch = $this->_arithPeek(0);
            if ($ch === "(")
            {
                $depth += 1;
                $this->_arithAdvance();
            }
            else
            {
                if ($ch === ")")
                {
                    $depth -= 1;
                    if ($depth === 0)
                    {
                        break;
                    }
                    $this->_arithAdvance();
                }
                else
                {
                    $this->_arithAdvance();
                }
            }
        }
        $content = _substring($this->_arithSrc, $contentStart, $this->_arithPos);
        $this->_arithAdvance();
        $subParser = newParser($content, false, $this->_extglob);
        $cmd = $subParser->parseList(true);
        return new Commandsubstitution($cmd, false, "cmdsub");
    }

    public function _arithParseBracedParam(): ?Node
    {
        $this->_arithAdvance();
        $nameChars = [];
        if ($this->_arithPeek(0) === "!")
        {
            $this->_arithAdvance();
            $nameChars = [];
            while (!$this->_arithAtEnd() && $this->_arithPeek(0) !== "}")
            {
                array_push($nameChars, $this->_arithAdvance());
            }
            $this->_arithConsume("}");
            return new Paramindirect(implode("", $nameChars), "", "", "param-indirect");
        }
        if ($this->_arithPeek(0) === "#")
        {
            $this->_arithAdvance();
            $nameChars = [];
            while (!$this->_arithAtEnd() && $this->_arithPeek(0) !== "}")
            {
                array_push($nameChars, $this->_arithAdvance());
            }
            $this->_arithConsume("}");
            return new Paramlength(implode("", $nameChars), "param-len");
        }
        $nameChars = [];
        $ch = "";
        while (!$this->_arithAtEnd())
        {
            $ch = $this->_arithPeek(0);
            if ($ch === "}")
            {
                $this->_arithAdvance();
                return new Paramexpansion(implode("", $nameChars), "", "", "param");
            }
            if (_isParamExpansionOp($ch))
            {
                break;
            }
            array_push($nameChars, $this->_arithAdvance());
        }
        $name = implode("", $nameChars);
        $opChars = [];
        $depth = 1;
        while (!$this->_arithAtEnd() && $depth > 0)
        {
            $ch = $this->_arithPeek(0);
            if ($ch === "{")
            {
                $depth += 1;
                array_push($opChars, $this->_arithAdvance());
            }
            else
            {
                if ($ch === "}")
                {
                    $depth -= 1;
                    if ($depth === 0)
                    {
                        break;
                    }
                    array_push($opChars, $this->_arithAdvance());
                }
                else
                {
                    array_push($opChars, $this->_arithAdvance());
                }
            }
        }
        $this->_arithConsume("}");
        $opStr = implode("", $opChars);
        if (str_starts_with($opStr, ":-"))
        {
            return new Paramexpansion($name, ":-", _substring($opStr, 2, mb_strlen($opStr)), "param");
        }
        if (str_starts_with($opStr, ":="))
        {
            return new Paramexpansion($name, ":=", _substring($opStr, 2, mb_strlen($opStr)), "param");
        }
        if (str_starts_with($opStr, ":+"))
        {
            return new Paramexpansion($name, ":+", _substring($opStr, 2, mb_strlen($opStr)), "param");
        }
        if (str_starts_with($opStr, ":?"))
        {
            return new Paramexpansion($name, ":?", _substring($opStr, 2, mb_strlen($opStr)), "param");
        }
        if (str_starts_with($opStr, ":"))
        {
            return new Paramexpansion($name, ":", _substring($opStr, 1, mb_strlen($opStr)), "param");
        }
        if (str_starts_with($opStr, "##"))
        {
            return new Paramexpansion($name, "##", _substring($opStr, 2, mb_strlen($opStr)), "param");
        }
        if (str_starts_with($opStr, "#"))
        {
            return new Paramexpansion($name, "#", _substring($opStr, 1, mb_strlen($opStr)), "param");
        }
        if (str_starts_with($opStr, "%%"))
        {
            return new Paramexpansion($name, "%%", _substring($opStr, 2, mb_strlen($opStr)), "param");
        }
        if (str_starts_with($opStr, "%"))
        {
            return new Paramexpansion($name, "%", _substring($opStr, 1, mb_strlen($opStr)), "param");
        }
        if (str_starts_with($opStr, "//"))
        {
            return new Paramexpansion($name, "//", _substring($opStr, 2, mb_strlen($opStr)), "param");
        }
        if (str_starts_with($opStr, "/"))
        {
            return new Paramexpansion($name, "/", _substring($opStr, 1, mb_strlen($opStr)), "param");
        }
        return new Paramexpansion($name, "", $opStr, "param");
    }

    public function _arithParseSingleQuote(): ?Node
    {
        $this->_arithAdvance();
        $contentStart = $this->_arithPos;
        while (!$this->_arithAtEnd() && $this->_arithPeek(0) !== "'")
        {
            $this->_arithAdvance();
        }
        $content = _substring($this->_arithSrc, $contentStart, $this->_arithPos);
        if (!$this->_arithConsume("'"))
        {
            throw new Parseerror_("Unterminated single quote in arithmetic");
        }
        return new Arithnumber($content, "number");
    }

    public function _arithParseDoubleQuote(): ?Node
    {
        $this->_arithAdvance();
        $contentStart = $this->_arithPos;
        while (!$this->_arithAtEnd() && $this->_arithPeek(0) !== "\"")
        {
            $c = $this->_arithPeek(0);
            if ($c === "\\" && !$this->_arithAtEnd())
            {
                $this->_arithAdvance();
                $this->_arithAdvance();
            }
            else
            {
                $this->_arithAdvance();
            }
        }
        $content = _substring($this->_arithSrc, $contentStart, $this->_arithPos);
        if (!$this->_arithConsume("\""))
        {
            throw new Parseerror_("Unterminated double quote in arithmetic");
        }
        return new Arithnumber($content, "number");
    }

    public function _arithParseBacktick(): ?Node
    {
        $this->_arithAdvance();
        $contentStart = $this->_arithPos;
        while (!$this->_arithAtEnd() && $this->_arithPeek(0) !== "`")
        {
            $c = $this->_arithPeek(0);
            if ($c === "\\" && !$this->_arithAtEnd())
            {
                $this->_arithAdvance();
                $this->_arithAdvance();
            }
            else
            {
                $this->_arithAdvance();
            }
        }
        $content = _substring($this->_arithSrc, $contentStart, $this->_arithPos);
        if (!$this->_arithConsume("`"))
        {
            throw new Parseerror_("Unterminated backtick in arithmetic");
        }
        $subParser = newParser($content, false, $this->_extglob);
        $cmd = $subParser->parseList(true);
        return new Commandsubstitution($cmd, false, "cmdsub");
    }

    public function _arithParseNumberOrVar(): ?Node
    {
        $this->_arithSkipWs();
        $chars = [];
        $c = $this->_arithPeek(0);
        $ch = "";
        if (ctype_digit($c))
        {
            while (!$this->_arithAtEnd())
            {
                $ch = $this->_arithPeek(0);
                if (ctype_alnum($ch) || $ch === "#" || $ch === "_")
                {
                    array_push($chars, $this->_arithAdvance());
                }
                else
                {
                    break;
                }
            }
            $prefix = implode("", $chars);
            if (!$this->_arithAtEnd() && $this->_arithPeek(0) === "\$")
            {
                $expansion = $this->_arithParseExpansion();
                return new Arithconcat([new Arithnumber($prefix, "number"), $expansion], "arith-concat");
            }
            return new Arithnumber($prefix, "number");
        }
        if (ctype_alpha($c) || $c === "_")
        {
            while (!$this->_arithAtEnd())
            {
                $ch = $this->_arithPeek(0);
                if (ctype_alnum($ch) || $ch === "_")
                {
                    array_push($chars, $this->_arithAdvance());
                }
                else
                {
                    break;
                }
            }
            return new Arithvar(implode("", $chars), "var");
        }
        throw new Parseerror_("Unexpected character '" . $c . "' in arithmetic expression");
    }

    public function _parseDeprecatedArithmetic(): array
    {
        if ($this->atEnd() || $this->peek() !== "\$")
        {
            return [null, ""];
        }
        $start = $this->pos;
        if ($this->pos + 1 >= $this->length || (string)(mb_substr($this->source, $this->pos + 1, 1)) !== "[")
        {
            return [null, ""];
        }
        $this->advance();
        $this->advance();
        $this->_lexer->pos = $this->pos;
        $content = $this->_lexer->_parseMatchedPair("[", "]", MATCHEDPAIRFLAGS_ARITH, false);
        $this->pos = $this->_lexer->pos;
        $text = _substring($this->source, $start, $this->pos);
        return [new Arithdeprecated($content, "arith-deprecated"), $text];
    }

    public function _parseParamExpansion(bool $inDquote): array
    {
        $this->_syncLexer();
        [$result0, $result1] = $this->_lexer->_readParamExpansion($inDquote);
        $this->_syncParser();
        return [$result0, $result1];
    }

    public function parseRedirect(): ?Node
    {
        $this->skipWhitespace();
        if ($this->atEnd())
        {
            return null;
        }
        $start = $this->pos;
        $fd = -1;
        $varfd = "";
        $ch = "";
        if ($this->peek() === "{")
        {
            $saved = $this->pos;
            $this->advance();
            $varnameChars = [];
            $inBracket = false;
            while (!$this->atEnd() && !_isRedirectChar($this->peek()))
            {
                $ch = $this->peek();
                if ($ch === "}" && !$inBracket)
                {
                    break;
                }
                else
                {
                    if ($ch === "[")
                    {
                        $inBracket = true;
                        array_push($varnameChars, $this->advance());
                    }
                    else
                    {
                        if ($ch === "]")
                        {
                            $inBracket = false;
                            array_push($varnameChars, $this->advance());
                        }
                        else
                        {
                            if (ctype_alnum($ch) || $ch === "_")
                            {
                                array_push($varnameChars, $this->advance());
                            }
                            else
                            {
                                if ($inBracket && !_isMetachar($ch))
                                {
                                    array_push($varnameChars, $this->advance());
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
            $varname = implode("", $varnameChars);
            $isValidVarfd = false;
            if (($varname !== ''))
            {
                if (ctype_alpha((string)(mb_substr($varname, 0, 1))) || (string)(mb_substr($varname, 0, 1)) === "_")
                {
                    if (((str_contains($varname, "["))) || ((str_contains($varname, "]"))))
                    {
                        $left = (mb_strpos($varname, "[") === false ? -1 : mb_strpos($varname, "["));
                        $right = (mb_strrpos($varname, "]") === false ? -1 : mb_strrpos($varname, "]"));
                        if ($left !== -1 && $right === mb_strlen($varname) - 1 && $right > $left + 1)
                        {
                            $base = mb_substr($varname, 0, $left);
                            if (($base !== '') && (ctype_alpha((string)(mb_substr($base, 0, 1))) || (string)(mb_substr($base, 0, 1)) === "_"))
                            {
                                $isValidVarfd = true;
                                foreach (mb_str_split(mb_substr($base, 1)) as $c)
                                {
                                    if (!(ctype_alnum($c) || $c === "_"))
                                    {
                                        $isValidVarfd = false;
                                        break;
                                    }
                                }
                            }
                        }
                    }
                    else
                    {
                        $isValidVarfd = true;
                        foreach (mb_str_split(mb_substr($varname, 1)) as $c)
                        {
                            if (!(ctype_alnum($c) || $c === "_"))
                            {
                                $isValidVarfd = false;
                                break;
                            }
                        }
                    }
                }
            }
            if (!$this->atEnd() && $this->peek() === "}" && $isValidVarfd)
            {
                $this->advance();
                $varfd = $varname;
            }
            else
            {
                $this->pos = $saved;
            }
        }
        $fdChars = [];
        if ($varfd === "" && ($this->peek() !== '') && ctype_digit($this->peek()))
        {
            $fdChars = [];
            while (!$this->atEnd() && ctype_digit($this->peek()))
            {
                array_push($fdChars, $this->advance());
            }
            $fd = intval(implode("", $fdChars), 10);
        }
        $ch = $this->peek();
        $op = "";
        $target = null;
        if ($ch === "&" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === ">")
        {
            if ($fd !== -1 || $varfd !== "")
            {
                $this->pos = $start;
                return null;
            }
            $this->advance();
            $this->advance();
            if (!$this->atEnd() && $this->peek() === ">")
            {
                $this->advance();
                $op = "&>>";
            }
            else
            {
                $op = "&>";
            }
            $this->skipWhitespace();
            $target = $this->parseWord(false, false, false);
            if ($target === null)
            {
                throw new Parseerror_("Expected target for redirect " . $op);
            }
            return new Redirect($op, $target, "redirect", null);
        }
        if ($ch === "" || !_isRedirectChar($ch))
        {
            $this->pos = $start;
            return null;
        }
        if ($fd === -1 && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "(")
        {
            $this->pos = $start;
            return null;
        }
        $op = $this->advance();
        $stripTabs = false;
        if (!$this->atEnd())
        {
            $nextCh = $this->peek();
            if ($op === ">" && $nextCh === ">")
            {
                $this->advance();
                $op = ">>";
            }
            else
            {
                if ($op === "<" && $nextCh === "<")
                {
                    $this->advance();
                    if (!$this->atEnd() && $this->peek() === "<")
                    {
                        $this->advance();
                        $op = "<<<";
                    }
                    else
                    {
                        if (!$this->atEnd() && $this->peek() === "-")
                        {
                            $this->advance();
                            $op = "<<";
                            $stripTabs = true;
                        }
                        else
                        {
                            $op = "<<";
                        }
                    }
                }
                else
                {
                    if ($op === "<" && $nextCh === ">")
                    {
                        $this->advance();
                        $op = "<>";
                    }
                    else
                    {
                        if ($op === ">" && $nextCh === "|")
                        {
                            $this->advance();
                            $op = ">|";
                        }
                        else
                        {
                            if ($fd === -1 && $varfd === "" && $op === ">" && $nextCh === "&")
                            {
                                if ($this->pos + 1 >= $this->length || !_isDigitOrDash((string)(mb_substr($this->source, $this->pos + 1, 1))))
                                {
                                    $this->advance();
                                    $op = ">&";
                                }
                            }
                            else
                            {
                                if ($fd === -1 && $varfd === "" && $op === "<" && $nextCh === "&")
                                {
                                    if ($this->pos + 1 >= $this->length || !_isDigitOrDash((string)(mb_substr($this->source, $this->pos + 1, 1))))
                                    {
                                        $this->advance();
                                        $op = "<&";
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        if ($op === "<<")
        {
            return $this->_parseHeredoc($fd, $stripTabs);
        }
        if ($varfd !== "")
        {
            $op = "{" . $varfd . "}" . $op;
        }
        else
        {
            if ($fd !== -1)
            {
                $op = strval($fd) . $op;
            }
        }
        if (!$this->atEnd() && $this->peek() === "&")
        {
            $this->advance();
            $this->skipWhitespace();
            if (!$this->atEnd() && $this->peek() === "-")
            {
                if ($this->pos + 1 < $this->length && !_isMetachar((string)(mb_substr($this->source, $this->pos + 1, 1))))
                {
                    $this->advance();
                    $target = new Word("&-", [], "word");
                }
                else
                {
                    $target = null;
                }
            }
            else
            {
                $target = null;
            }
            if ($target === null)
            {
                $innerWord = null;
                if (!$this->atEnd() && (ctype_digit($this->peek()) || $this->peek() === "-"))
                {
                    $wordStart = $this->pos;
                    $fdChars = [];
                    while (!$this->atEnd() && ctype_digit($this->peek()))
                    {
                        array_push($fdChars, $this->advance());
                    }
                    $fdTarget = "";
                    if ((count($fdChars) > 0))
                    {
                        $fdTarget = implode("", $fdChars);
                    }
                    else
                    {
                        $fdTarget = "";
                    }
                    if (!$this->atEnd() && $this->peek() === "-")
                    {
                        $fdTarget .= $this->advance();
                    }
                    if ($fdTarget !== "-" && !$this->atEnd() && !_isMetachar($this->peek()))
                    {
                        $this->pos = $wordStart;
                        $innerWord = $this->parseWord(false, false, false);
                        if ($innerWord !== null)
                        {
                            $target = new Word("&" . $innerWord->value, [], "word");
                            $target->parts = $innerWord->parts;
                        }
                        else
                        {
                            throw new Parseerror_("Expected target for redirect " . $op);
                        }
                    }
                    else
                    {
                        $target = new Word("&" . $fdTarget, [], "word");
                    }
                }
                else
                {
                    $innerWord = $this->parseWord(false, false, false);
                    if ($innerWord !== null)
                    {
                        $target = new Word("&" . $innerWord->value, [], "word");
                        $target->parts = $innerWord->parts;
                    }
                    else
                    {
                        throw new Parseerror_("Expected target for redirect " . $op);
                    }
                }
            }
        }
        else
        {
            $this->skipWhitespace();
            if (($op === ">&" || $op === "<&") && !$this->atEnd() && $this->peek() === "-")
            {
                if ($this->pos + 1 < $this->length && !_isMetachar((string)(mb_substr($this->source, $this->pos + 1, 1))))
                {
                    $this->advance();
                    $target = new Word("&-", [], "word");
                }
                else
                {
                    $target = $this->parseWord(false, false, false);
                }
            }
            else
            {
                $target = $this->parseWord(false, false, false);
            }
        }
        if ($target === null)
        {
            throw new Parseerror_("Expected target for redirect " . $op);
        }
        return new Redirect($op, $target, "redirect", null);
    }

    public function _parseHeredocDelimiter(): array
    {
        $this->skipWhitespace();
        $quoted = false;
        $delimiterChars = [];
        while (true)
        {
            $c = "";
            $depth = 0;
            while (!$this->atEnd() && !_isMetachar($this->peek()))
            {
                $ch = $this->peek();
                if ($ch === "\"")
                {
                    $quoted = true;
                    $this->advance();
                    while (!$this->atEnd() && $this->peek() !== "\"")
                    {
                        array_push($delimiterChars, $this->advance());
                    }
                    if (!$this->atEnd())
                    {
                        $this->advance();
                    }
                }
                else
                {
                    if ($ch === "'")
                    {
                        $quoted = true;
                        $this->advance();
                        while (!$this->atEnd() && $this->peek() !== "'")
                        {
                            $c = $this->advance();
                            if ($c === "\n")
                            {
                                $this->_sawNewlineInSingleQuote = true;
                            }
                            array_push($delimiterChars, $c);
                        }
                        if (!$this->atEnd())
                        {
                            $this->advance();
                        }
                    }
                    else
                    {
                        if ($ch === "\\")
                        {
                            $this->advance();
                            if (!$this->atEnd())
                            {
                                $nextCh = $this->peek();
                                if ($nextCh === "\n")
                                {
                                    $this->advance();
                                }
                                else
                                {
                                    $quoted = true;
                                    array_push($delimiterChars, $this->advance());
                                }
                            }
                        }
                        else
                        {
                            if ($ch === "\$" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "'")
                            {
                                $quoted = true;
                                $this->advance();
                                $this->advance();
                                while (!$this->atEnd() && $this->peek() !== "'")
                                {
                                    $c = $this->peek();
                                    if ($c === "\\" && $this->pos + 1 < $this->length)
                                    {
                                        $this->advance();
                                        $esc = $this->peek();
                                        $escVal = _getAnsiEscape($esc);
                                        if ($escVal >= 0)
                                        {
                                            array_push($delimiterChars, mb_chr($escVal));
                                            $this->advance();
                                        }
                                        else
                                        {
                                            if ($esc === "'")
                                            {
                                                array_push($delimiterChars, $this->advance());
                                            }
                                            else
                                            {
                                                array_push($delimiterChars, $this->advance());
                                            }
                                        }
                                    }
                                    else
                                    {
                                        array_push($delimiterChars, $this->advance());
                                    }
                                }
                                if (!$this->atEnd())
                                {
                                    $this->advance();
                                }
                            }
                            else
                            {
                                if (_isExpansionStart($this->source, $this->pos, "\$("))
                                {
                                    array_push($delimiterChars, $this->advance());
                                    array_push($delimiterChars, $this->advance());
                                    $depth = 1;
                                    while (!$this->atEnd() && $depth > 0)
                                    {
                                        $c = $this->peek();
                                        if ($c === "(")
                                        {
                                            $depth += 1;
                                        }
                                        else
                                        {
                                            if ($c === ")")
                                            {
                                                $depth -= 1;
                                            }
                                        }
                                        array_push($delimiterChars, $this->advance());
                                    }
                                }
                                else
                                {
                                    $dollarCount = 0;
                                    $j = 0;
                                    if ($ch === "\$" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "{")
                                    {
                                        $dollarCount = 0;
                                        $j = $this->pos - 1;
                                        while ($j >= 0 && (string)(mb_substr($this->source, $j, 1)) === "\$")
                                        {
                                            $dollarCount += 1;
                                            $j -= 1;
                                        }
                                        if ($j >= 0 && (string)(mb_substr($this->source, $j, 1)) === "\\")
                                        {
                                            $dollarCount -= 1;
                                        }
                                        if ($dollarCount % 2 === 1)
                                        {
                                            array_push($delimiterChars, $this->advance());
                                        }
                                        else
                                        {
                                            array_push($delimiterChars, $this->advance());
                                            array_push($delimiterChars, $this->advance());
                                            $depth = 0;
                                            while (!$this->atEnd())
                                            {
                                                $c = $this->peek();
                                                if ($c === "{")
                                                {
                                                    $depth += 1;
                                                }
                                                else
                                                {
                                                    if ($c === "}")
                                                    {
                                                        array_push($delimiterChars, $this->advance());
                                                        if ($depth === 0)
                                                        {
                                                            break;
                                                        }
                                                        $depth -= 1;
                                                        if ($depth === 0 && !$this->atEnd() && _isMetachar($this->peek()))
                                                        {
                                                            break;
                                                        }
                                                        continue;
                                                    }
                                                }
                                                array_push($delimiterChars, $this->advance());
                                            }
                                        }
                                    }
                                    else
                                    {
                                        if ($ch === "\$" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "[")
                                        {
                                            $dollarCount = 0;
                                            $j = $this->pos - 1;
                                            while ($j >= 0 && (string)(mb_substr($this->source, $j, 1)) === "\$")
                                            {
                                                $dollarCount += 1;
                                                $j -= 1;
                                            }
                                            if ($j >= 0 && (string)(mb_substr($this->source, $j, 1)) === "\\")
                                            {
                                                $dollarCount -= 1;
                                            }
                                            if ($dollarCount % 2 === 1)
                                            {
                                                array_push($delimiterChars, $this->advance());
                                            }
                                            else
                                            {
                                                array_push($delimiterChars, $this->advance());
                                                array_push($delimiterChars, $this->advance());
                                                $depth = 1;
                                                while (!$this->atEnd() && $depth > 0)
                                                {
                                                    $c = $this->peek();
                                                    if ($c === "[")
                                                    {
                                                        $depth += 1;
                                                    }
                                                    else
                                                    {
                                                        if ($c === "]")
                                                        {
                                                            $depth -= 1;
                                                        }
                                                    }
                                                    array_push($delimiterChars, $this->advance());
                                                }
                                            }
                                        }
                                        else
                                        {
                                            if ($ch === "`")
                                            {
                                                array_push($delimiterChars, $this->advance());
                                                while (!$this->atEnd() && $this->peek() !== "`")
                                                {
                                                    $c = $this->peek();
                                                    if ($c === "'")
                                                    {
                                                        array_push($delimiterChars, $this->advance());
                                                        while (!$this->atEnd() && $this->peek() !== "'" && $this->peek() !== "`")
                                                        {
                                                            array_push($delimiterChars, $this->advance());
                                                        }
                                                        if (!$this->atEnd() && $this->peek() === "'")
                                                        {
                                                            array_push($delimiterChars, $this->advance());
                                                        }
                                                    }
                                                    else
                                                    {
                                                        if ($c === "\"")
                                                        {
                                                            array_push($delimiterChars, $this->advance());
                                                            while (!$this->atEnd() && $this->peek() !== "\"" && $this->peek() !== "`")
                                                            {
                                                                if ($this->peek() === "\\" && $this->pos + 1 < $this->length)
                                                                {
                                                                    array_push($delimiterChars, $this->advance());
                                                                }
                                                                array_push($delimiterChars, $this->advance());
                                                            }
                                                            if (!$this->atEnd() && $this->peek() === "\"")
                                                            {
                                                                array_push($delimiterChars, $this->advance());
                                                            }
                                                        }
                                                        else
                                                        {
                                                            if ($c === "\\" && $this->pos + 1 < $this->length)
                                                            {
                                                                array_push($delimiterChars, $this->advance());
                                                                array_push($delimiterChars, $this->advance());
                                                            }
                                                            else
                                                            {
                                                                array_push($delimiterChars, $this->advance());
                                                            }
                                                        }
                                                    }
                                                }
                                                if (!$this->atEnd())
                                                {
                                                    array_push($delimiterChars, $this->advance());
                                                }
                                            }
                                            else
                                            {
                                                array_push($delimiterChars, $this->advance());
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            if (!$this->atEnd() && ((str_contains("<>", $this->peek()))) && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "(")
            {
                array_push($delimiterChars, $this->advance());
                array_push($delimiterChars, $this->advance());
                $depth = 1;
                while (!$this->atEnd() && $depth > 0)
                {
                    $c = $this->peek();
                    if ($c === "(")
                    {
                        $depth += 1;
                    }
                    else
                    {
                        if ($c === ")")
                        {
                            $depth -= 1;
                        }
                    }
                    array_push($delimiterChars, $this->advance());
                }
                continue;
            }
            break;
        }
        return [implode("", $delimiterChars), $quoted];
    }

    public function _readHeredocLine(bool $quoted): array
    {
        $lineStart = $this->pos;
        $lineEnd = $this->pos;
        while ($lineEnd < $this->length && (string)(mb_substr($this->source, $lineEnd, 1)) !== "\n")
        {
            $lineEnd += 1;
        }
        $line = _substring($this->source, $lineStart, $lineEnd);
        if (!$quoted)
        {
            while ($lineEnd < $this->length)
            {
                $trailingBs = _countTrailingBackslashes($line);
                if ($trailingBs % 2 === 0)
                {
                    break;
                }
                $line = _substring($line, 0, mb_strlen($line) - 1);
                $lineEnd += 1;
                $nextLineStart = $lineEnd;
                while ($lineEnd < $this->length && (string)(mb_substr($this->source, $lineEnd, 1)) !== "\n")
                {
                    $lineEnd += 1;
                }
                $line = $line . _substring($this->source, $nextLineStart, $lineEnd);
            }
        }
        return [$line, $lineEnd];
    }

    public function _lineMatchesDelimiter(string $line, string $delimiter, bool $stripTabs): array
    {
        $checkLine = ($stripTabs ? ltrim($line, "\t") : $line);
        $normalizedCheck = _normalizeHeredocDelimiter($checkLine);
        $normalizedDelim = _normalizeHeredocDelimiter($delimiter);
        return [$normalizedCheck === $normalizedDelim, $checkLine];
    }

    public function _gatherHeredocBodies(): void
    {
        foreach ($this->_pendingHeredocs as $heredoc)
        {
            $contentLines = [];
            $lineStart = $this->pos;
            while ($this->pos < $this->length)
            {
                $lineStart = $this->pos;
                [$line, $lineEnd] = $this->_readHeredocLine($heredoc->quoted);
                [$matches, $checkLine] = $this->_lineMatchesDelimiter($line, $heredoc->delimiter, $heredoc->stripTabs);
                if ($matches)
                {
                    $this->pos = ($lineEnd < $this->length ? $lineEnd + 1 : $lineEnd);
                    break;
                }
                $normalizedCheck = _normalizeHeredocDelimiter($checkLine);
                $normalizedDelim = _normalizeHeredocDelimiter($heredoc->delimiter);
                $tabsStripped = 0;
                if ($this->_eofToken === ")" && str_starts_with($normalizedCheck, $normalizedDelim))
                {
                    $tabsStripped = mb_strlen($line) - mb_strlen($checkLine);
                    $this->pos = $lineStart + $tabsStripped + mb_strlen($heredoc->delimiter);
                    break;
                }
                if ($lineEnd >= $this->length && str_starts_with($normalizedCheck, $normalizedDelim) && $this->_inProcessSub)
                {
                    $tabsStripped = mb_strlen($line) - mb_strlen($checkLine);
                    $this->pos = $lineStart + $tabsStripped + mb_strlen($heredoc->delimiter);
                    break;
                }
                if ($heredoc->stripTabs)
                {
                    $line = ltrim($line, "\t");
                }
                if ($lineEnd < $this->length)
                {
                    array_push($contentLines, $line . "\n");
                    $this->pos = $lineEnd + 1;
                }
                else
                {
                    $addNewline = true;
                    if (!$heredoc->quoted && _countTrailingBackslashes($line) % 2 === 1)
                    {
                        $addNewline = false;
                    }
                    array_push($contentLines, $line . (($addNewline ? "\n" : "")));
                    $this->pos = $this->length;
                }
            }
            $heredoc->content = implode("", $contentLines);
        }
        $this->_pendingHeredocs = [];
    }

    public function _parseHeredoc(?int $fd, bool $stripTabs): ?Heredoc
    {
        $startPos = $this->pos;
        $this->_setState(PARSERSTATEFLAGS_PST_HEREDOC);
        [$delimiter, $quoted] = $this->_parseHeredocDelimiter();
        foreach ($this->_pendingHeredocs as $existing)
        {
            if ($existing->_startPos === $startPos && $existing->delimiter === $delimiter)
            {
                $this->_clearState(PARSERSTATEFLAGS_PST_HEREDOC);
                return $existing;
            }
        }
        $heredoc = new Heredoc($delimiter, "", $stripTabs, $quoted, false, 0, "heredoc", $fd);
        $heredoc->_startPos = $startPos;
        array_push($this->_pendingHeredocs, $heredoc);
        $this->_clearState(PARSERSTATEFLAGS_PST_HEREDOC);
        return $heredoc;
    }

    public function parseCommand(): ?Command
    {
        $words = [];
        $redirects = [];
        while (true)
        {
            $this->skipWhitespace();
            if ($this->_lexIsCommandTerminator())
            {
                break;
            }
            if (count($words) === 0)
            {
                $reserved = $this->_lexPeekReservedWord();
                if ($reserved === "}" || $reserved === "]]")
                {
                    break;
                }
            }
            $redirect = $this->parseRedirect();
            if ($redirect !== null)
            {
                array_push($redirects, $redirect);
                continue;
            }
            $allAssignments = true;
            foreach ($words as $w)
            {
                if (!$this->_isAssignmentWord($w))
                {
                    $allAssignments = false;
                    break;
                }
            }
            $inAssignBuiltin = count($words) > 0 && (isset(ASSIGNMENT_BUILTINS[$words[0]->value]));
            $word = $this->parseWord(!(count($words) > 0) || $allAssignments && count($redirects) === 0, false, $inAssignBuiltin);
            if ($word === null)
            {
                break;
            }
            array_push($words, $word);
        }
        if (!(count($words) > 0) && !(count($redirects) > 0))
        {
            return null;
        }
        return new Command($words, $redirects, "command");
    }

    public function parseSubshell(): ?Subshell
    {
        $this->skipWhitespace();
        if ($this->atEnd() || $this->peek() !== "(")
        {
            return null;
        }
        $this->advance();
        $this->_setState(PARSERSTATEFLAGS_PST_SUBSHELL);
        $body = $this->parseList(true);
        if ($body === null)
        {
            $this->_clearState(PARSERSTATEFLAGS_PST_SUBSHELL);
            throw new Parseerror_("Expected command in subshell");
        }
        $this->skipWhitespace();
        if ($this->atEnd() || $this->peek() !== ")")
        {
            $this->_clearState(PARSERSTATEFLAGS_PST_SUBSHELL);
            throw new Parseerror_("Expected ) to close subshell");
        }
        $this->advance();
        $this->_clearState(PARSERSTATEFLAGS_PST_SUBSHELL);
        return new Subshell($body, $this->_collectRedirects(), "subshell");
    }

    public function parseArithmeticCommand(): ?Arithmeticcommand
    {
        $this->skipWhitespace();
        if ($this->atEnd() || $this->peek() !== "(" || $this->pos + 1 >= $this->length || (string)(mb_substr($this->source, $this->pos + 1, 1)) !== "(")
        {
            return null;
        }
        $savedPos = $this->pos;
        $this->advance();
        $this->advance();
        $contentStart = $this->pos;
        $depth = 1;
        while (!$this->atEnd() && $depth > 0)
        {
            $c = $this->peek();
            if ($c === "'")
            {
                $this->advance();
                while (!$this->atEnd() && $this->peek() !== "'")
                {
                    $this->advance();
                }
                if (!$this->atEnd())
                {
                    $this->advance();
                }
            }
            else
            {
                if ($c === "\"")
                {
                    $this->advance();
                    while (!$this->atEnd())
                    {
                        if ($this->peek() === "\\" && $this->pos + 1 < $this->length)
                        {
                            $this->advance();
                            $this->advance();
                        }
                        else
                        {
                            if ($this->peek() === "\"")
                            {
                                $this->advance();
                                break;
                            }
                            else
                            {
                                $this->advance();
                            }
                        }
                    }
                }
                else
                {
                    if ($c === "\\" && $this->pos + 1 < $this->length)
                    {
                        $this->advance();
                        $this->advance();
                    }
                    else
                    {
                        if ($c === "(")
                        {
                            $depth += 1;
                            $this->advance();
                        }
                        else
                        {
                            if ($c === ")")
                            {
                                if ($depth === 1 && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === ")")
                                {
                                    break;
                                }
                                $depth -= 1;
                                if ($depth === 0)
                                {
                                    $this->pos = $savedPos;
                                    return null;
                                }
                                $this->advance();
                            }
                            else
                            {
                                $this->advance();
                            }
                        }
                    }
                }
            }
        }
        if ($this->atEnd())
        {
            throw new Matchedpairerror("unexpected EOF looking for `))'");
        }
        if ($depth !== 1)
        {
            $this->pos = $savedPos;
            return null;
        }
        $content = _substring($this->source, $contentStart, $this->pos);
        $content = str_replace("\\\n", "", $content);
        $this->advance();
        $this->advance();
        $expr = $this->_parseArithExpr($content);
        return new Arithmeticcommand($this->_collectRedirects(), $content, "arith-cmd", $expr);
    }

    public function parseConditionalExpr(): ?Conditionalexpr
    {
        $this->skipWhitespace();
        if ($this->atEnd() || $this->peek() !== "[" || $this->pos + 1 >= $this->length || (string)(mb_substr($this->source, $this->pos + 1, 1)) !== "[")
        {
            return null;
        }
        $nextPos = $this->pos + 2;
        if ($nextPos < $this->length && !(_isWhitespace((string)(mb_substr($this->source, $nextPos, 1))) || (string)(mb_substr($this->source, $nextPos, 1)) === "\\" && $nextPos + 1 < $this->length && (string)(mb_substr($this->source, $nextPos + 1, 1)) === "\n"))
        {
            return null;
        }
        $this->advance();
        $this->advance();
        $this->_setState(PARSERSTATEFLAGS_PST_CONDEXPR);
        $this->_wordContext = WORD_CTX_COND;
        $body = $this->_parseCondOr();
        while (!$this->atEnd() && _isWhitespaceNoNewline($this->peek()))
        {
            $this->advance();
        }
        if ($this->atEnd() || $this->peek() !== "]" || $this->pos + 1 >= $this->length || (string)(mb_substr($this->source, $this->pos + 1, 1)) !== "]")
        {
            $this->_clearState(PARSERSTATEFLAGS_PST_CONDEXPR);
            $this->_wordContext = WORD_CTX_NORMAL;
            throw new Parseerror_("Expected ]] to close conditional expression");
        }
        $this->advance();
        $this->advance();
        $this->_clearState(PARSERSTATEFLAGS_PST_CONDEXPR);
        $this->_wordContext = WORD_CTX_NORMAL;
        return new Conditionalexpr($body, $this->_collectRedirects(), "cond-expr");
    }

    public function _condSkipWhitespace(): void
    {
        while (!$this->atEnd())
        {
            if (_isWhitespaceNoNewline($this->peek()))
            {
                $this->advance();
            }
            else
            {
                if ($this->peek() === "\\" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "\n")
                {
                    $this->advance();
                    $this->advance();
                }
                else
                {
                    if ($this->peek() === "\n")
                    {
                        $this->advance();
                    }
                    else
                    {
                        break;
                    }
                }
            }
        }
    }

    public function _condAtEnd(): bool
    {
        return $this->atEnd() || $this->peek() === "]" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "]";
    }

    public function _parseCondOr(): ?Node
    {
        $this->_condSkipWhitespace();
        $left = $this->_parseCondAnd();
        $this->_condSkipWhitespace();
        if (!$this->_condAtEnd() && $this->peek() === "|" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "|")
        {
            $this->advance();
            $this->advance();
            $right = $this->_parseCondOr();
            return new Condor($left, $right, "cond-or");
        }
        return $left;
    }

    public function _parseCondAnd(): ?Node
    {
        $this->_condSkipWhitespace();
        $left = $this->_parseCondTerm();
        $this->_condSkipWhitespace();
        if (!$this->_condAtEnd() && $this->peek() === "&" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "&")
        {
            $this->advance();
            $this->advance();
            $right = $this->_parseCondAnd();
            return new Condand($left, $right, "cond-and");
        }
        return $left;
    }

    public function _parseCondTerm(): ?Node
    {
        $this->_condSkipWhitespace();
        if ($this->_condAtEnd())
        {
            throw new Parseerror_("Unexpected end of conditional expression");
        }
        $operand = null;
        if ($this->peek() === "!")
        {
            if ($this->pos + 1 < $this->length && !_isWhitespaceNoNewline((string)(mb_substr($this->source, $this->pos + 1, 1))))
            {
            }
            else
            {
                $this->advance();
                $operand = $this->_parseCondTerm();
                return new Condnot($operand, "cond-not");
            }
        }
        if ($this->peek() === "(")
        {
            $this->advance();
            $inner = $this->_parseCondOr();
            $this->_condSkipWhitespace();
            if ($this->atEnd() || $this->peek() !== ")")
            {
                throw new Parseerror_("Expected ) in conditional expression");
            }
            $this->advance();
            return new Condparen($inner, "cond-paren");
        }
        $word1 = $this->_parseCondWord();
        if ($word1 === null)
        {
            throw new Parseerror_("Expected word in conditional expression");
        }
        $this->_condSkipWhitespace();
        if (isset(COND_UNARY_OPS[$word1->value]))
        {
            $operand = $this->_parseCondWord();
            if ($operand === null)
            {
                throw new Parseerror_("Expected operand after " . $word1->value);
            }
            return new Unarytest($word1->value, $operand, "unary-test");
        }
        if (!$this->_condAtEnd() && $this->peek() !== "&" && $this->peek() !== "|" && $this->peek() !== ")")
        {
            $word2 = null;
            if (_isRedirectChar($this->peek()) && !($this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "("))
            {
                $op = $this->advance();
                $this->_condSkipWhitespace();
                $word2 = $this->_parseCondWord();
                if ($word2 === null)
                {
                    throw new Parseerror_("Expected operand after " . $op);
                }
                return new Binarytest($op, $word1, $word2, "binary-test");
            }
            $savedPos = $this->pos;
            $opWord = $this->_parseCondWord();
            if ($opWord !== null && (isset(COND_BINARY_OPS[$opWord->value])))
            {
                $this->_condSkipWhitespace();
                if ($opWord->value === "=~")
                {
                    $word2 = $this->_parseCondRegexWord();
                }
                else
                {
                    $word2 = $this->_parseCondWord();
                }
                if ($word2 === null)
                {
                    throw new Parseerror_("Expected operand after " . $opWord->value);
                }
                return new Binarytest($opWord->value, $word1, $word2, "binary-test");
            }
            else
            {
                $this->pos = $savedPos;
            }
        }
        return new Unarytest("-n", $word1, "unary-test");
    }

    public function _parseCondWord(): ?Word
    {
        $this->_condSkipWhitespace();
        if ($this->_condAtEnd())
        {
            return null;
        }
        $c = $this->peek();
        if (_isParen($c))
        {
            return null;
        }
        if ($c === "&" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "&")
        {
            return null;
        }
        if ($c === "|" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "|")
        {
            return null;
        }
        return $this->_parseWordInternal(WORD_CTX_COND, false, false);
    }

    public function _parseCondRegexWord(): ?Word
    {
        $this->_condSkipWhitespace();
        if ($this->_condAtEnd())
        {
            return null;
        }
        $this->_setState(PARSERSTATEFLAGS_PST_REGEXP);
        $result = $this->_parseWordInternal(WORD_CTX_REGEX, false, false);
        $this->_clearState(PARSERSTATEFLAGS_PST_REGEXP);
        $this->_wordContext = WORD_CTX_COND;
        return $result;
    }

    public function parseBraceGroup(): ?Bracegroup
    {
        $this->skipWhitespace();
        if (!$this->_lexConsumeWord("{"))
        {
            return null;
        }
        $this->skipWhitespaceAndNewlines();
        $body = $this->parseList(true);
        if ($body === null)
        {
            throw new Parseerror_("Expected command in brace group");
        }
        $this->skipWhitespace();
        if (!$this->_lexConsumeWord("}"))
        {
            throw new Parseerror_("Expected } to close brace group");
        }
        return new Bracegroup($body, $this->_collectRedirects(), "brace-group");
    }

    public function parseIf(): ?If_
    {
        $this->skipWhitespace();
        if (!$this->_lexConsumeWord("if"))
        {
            return null;
        }
        $condition = $this->parseListUntil(["then" => true]);
        if ($condition === null)
        {
            throw new Parseerror_("Expected condition after 'if'");
        }
        $this->skipWhitespaceAndNewlines();
        if (!$this->_lexConsumeWord("then"))
        {
            throw new Parseerror_("Expected 'then' after if condition");
        }
        $thenBody = $this->parseListUntil(["elif" => true, "else" => true, "fi" => true]);
        if ($thenBody === null)
        {
            throw new Parseerror_("Expected commands after 'then'");
        }
        $this->skipWhitespaceAndNewlines();
        $elseBody = null;
        if ($this->_lexIsAtReservedWord("elif"))
        {
            $this->_lexConsumeWord("elif");
            $elifCondition = $this->parseListUntil(["then" => true]);
            if ($elifCondition === null)
            {
                throw new Parseerror_("Expected condition after 'elif'");
            }
            $this->skipWhitespaceAndNewlines();
            if (!$this->_lexConsumeWord("then"))
            {
                throw new Parseerror_("Expected 'then' after elif condition");
            }
            $elifThenBody = $this->parseListUntil(["elif" => true, "else" => true, "fi" => true]);
            if ($elifThenBody === null)
            {
                throw new Parseerror_("Expected commands after 'then'");
            }
            $this->skipWhitespaceAndNewlines();
            $innerElse = null;
            if ($this->_lexIsAtReservedWord("elif"))
            {
                $innerElse = $this->_parseElifChain();
            }
            else
            {
                if ($this->_lexIsAtReservedWord("else"))
                {
                    $this->_lexConsumeWord("else");
                    $innerElse = $this->parseListUntil(["fi" => true]);
                    if ($innerElse === null)
                    {
                        throw new Parseerror_("Expected commands after 'else'");
                    }
                }
            }
            $elseBody = new If_($elifCondition, $elifThenBody, $innerElse, [], "if");
        }
        else
        {
            if ($this->_lexIsAtReservedWord("else"))
            {
                $this->_lexConsumeWord("else");
                $elseBody = $this->parseListUntil(["fi" => true]);
                if ($elseBody === null)
                {
                    throw new Parseerror_("Expected commands after 'else'");
                }
            }
        }
        $this->skipWhitespaceAndNewlines();
        if (!$this->_lexConsumeWord("fi"))
        {
            throw new Parseerror_("Expected 'fi' to close if statement");
        }
        return new If_($condition, $thenBody, $elseBody, $this->_collectRedirects(), "if");
    }

    public function _parseElifChain(): ?If_
    {
        $this->_lexConsumeWord("elif");
        $condition = $this->parseListUntil(["then" => true]);
        if ($condition === null)
        {
            throw new Parseerror_("Expected condition after 'elif'");
        }
        $this->skipWhitespaceAndNewlines();
        if (!$this->_lexConsumeWord("then"))
        {
            throw new Parseerror_("Expected 'then' after elif condition");
        }
        $thenBody = $this->parseListUntil(["elif" => true, "else" => true, "fi" => true]);
        if ($thenBody === null)
        {
            throw new Parseerror_("Expected commands after 'then'");
        }
        $this->skipWhitespaceAndNewlines();
        $elseBody = null;
        if ($this->_lexIsAtReservedWord("elif"))
        {
            $elseBody = $this->_parseElifChain();
        }
        else
        {
            if ($this->_lexIsAtReservedWord("else"))
            {
                $this->_lexConsumeWord("else");
                $elseBody = $this->parseListUntil(["fi" => true]);
                if ($elseBody === null)
                {
                    throw new Parseerror_("Expected commands after 'else'");
                }
            }
        }
        return new If_($condition, $thenBody, $elseBody, [], "if");
    }

    public function parseWhile(): ?While_
    {
        $this->skipWhitespace();
        if (!$this->_lexConsumeWord("while"))
        {
            return null;
        }
        $condition = $this->parseListUntil(["do" => true]);
        if ($condition === null)
        {
            throw new Parseerror_("Expected condition after 'while'");
        }
        $this->skipWhitespaceAndNewlines();
        if (!$this->_lexConsumeWord("do"))
        {
            throw new Parseerror_("Expected 'do' after while condition");
        }
        $body = $this->parseListUntil(["done" => true]);
        if ($body === null)
        {
            throw new Parseerror_("Expected commands after 'do'");
        }
        $this->skipWhitespaceAndNewlines();
        if (!$this->_lexConsumeWord("done"))
        {
            throw new Parseerror_("Expected 'done' to close while loop");
        }
        return new While_($condition, $body, $this->_collectRedirects(), "while");
    }

    public function parseUntil(): ?Until
    {
        $this->skipWhitespace();
        if (!$this->_lexConsumeWord("until"))
        {
            return null;
        }
        $condition = $this->parseListUntil(["do" => true]);
        if ($condition === null)
        {
            throw new Parseerror_("Expected condition after 'until'");
        }
        $this->skipWhitespaceAndNewlines();
        if (!$this->_lexConsumeWord("do"))
        {
            throw new Parseerror_("Expected 'do' after until condition");
        }
        $body = $this->parseListUntil(["done" => true]);
        if ($body === null)
        {
            throw new Parseerror_("Expected commands after 'do'");
        }
        $this->skipWhitespaceAndNewlines();
        if (!$this->_lexConsumeWord("done"))
        {
            throw new Parseerror_("Expected 'done' to close until loop");
        }
        return new Until($condition, $body, $this->_collectRedirects(), "until");
    }

    public function parseFor(): ?Node
    {
        $this->skipWhitespace();
        if (!$this->_lexConsumeWord("for"))
        {
            return null;
        }
        $this->skipWhitespace();
        if ($this->peek() === "(" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "(")
        {
            return $this->_parseForArith();
        }
        $varName = "";
        if ($this->peek() === "\$")
        {
            $varWord = $this->parseWord(false, false, false);
            if ($varWord === null)
            {
                throw new Parseerror_("Expected variable name after 'for'");
            }
            $varName = $varWord->value;
        }
        else
        {
            $varName = $this->peekWord();
            if ($varName === "")
            {
                throw new Parseerror_("Expected variable name after 'for'");
            }
            $this->consumeWord($varName);
        }
        $this->skipWhitespace();
        if ($this->peek() === ";")
        {
            $this->advance();
        }
        $this->skipWhitespaceAndNewlines();
        $words = null;
        if ($this->_lexIsAtReservedWord("in"))
        {
            $this->_lexConsumeWord("in");
            $this->skipWhitespace();
            $sawDelimiter = _isSemicolonOrNewline($this->peek());
            if ($this->peek() === ";")
            {
                $this->advance();
            }
            $this->skipWhitespaceAndNewlines();
            $words = [];
            while (true)
            {
                $this->skipWhitespace();
                if ($this->atEnd())
                {
                    break;
                }
                if (_isSemicolonOrNewline($this->peek()))
                {
                    $sawDelimiter = true;
                    if ($this->peek() === ";")
                    {
                        $this->advance();
                    }
                    break;
                }
                if ($this->_lexIsAtReservedWord("do"))
                {
                    if ($sawDelimiter)
                    {
                        break;
                    }
                    throw new Parseerror_("Expected ';' or newline before 'do'");
                }
                $word = $this->parseWord(false, false, false);
                if ($word === null)
                {
                    break;
                }
                array_push($words, $word);
            }
        }
        $this->skipWhitespaceAndNewlines();
        if ($this->peek() === "{")
        {
            $braceGroup = $this->parseBraceGroup();
            if ($braceGroup === null)
            {
                throw new Parseerror_("Expected brace group in for loop");
            }
            return new For_($varName, $braceGroup->body, $this->_collectRedirects(), "for", $words);
        }
        if (!$this->_lexConsumeWord("do"))
        {
            throw new Parseerror_("Expected 'do' in for loop");
        }
        $body = $this->parseListUntil(["done" => true]);
        if ($body === null)
        {
            throw new Parseerror_("Expected commands after 'do'");
        }
        $this->skipWhitespaceAndNewlines();
        if (!$this->_lexConsumeWord("done"))
        {
            throw new Parseerror_("Expected 'done' to close for loop");
        }
        return new For_($varName, $body, $this->_collectRedirects(), "for", $words);
    }

    public function _parseForArith(): ?Forarith
    {
        $this->advance();
        $this->advance();
        $parts = [];
        $current = [];
        $parenDepth = 0;
        while (!$this->atEnd())
        {
            $ch = $this->peek();
            if ($ch === "(")
            {
                $parenDepth += 1;
                array_push($current, $this->advance());
            }
            else
            {
                if ($ch === ")")
                {
                    if ($parenDepth > 0)
                    {
                        $parenDepth -= 1;
                        array_push($current, $this->advance());
                    }
                    else
                    {
                        if ($this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === ")")
                        {
                            array_push($parts, ltrim(implode("", $current), " \t"));
                            $this->advance();
                            $this->advance();
                            break;
                        }
                        else
                        {
                            array_push($current, $this->advance());
                        }
                    }
                }
                else
                {
                    if ($ch === ";" && $parenDepth === 0)
                    {
                        array_push($parts, ltrim(implode("", $current), " \t"));
                        $current = [];
                        $this->advance();
                    }
                    else
                    {
                        array_push($current, $this->advance());
                    }
                }
            }
        }
        if (count($parts) !== 3)
        {
            throw new Parseerror_("Expected three expressions in for ((;;))");
        }
        $init = $parts[0];
        $cond = $parts[1];
        $incr = $parts[2];
        $this->skipWhitespace();
        if (!$this->atEnd() && $this->peek() === ";")
        {
            $this->advance();
        }
        $this->skipWhitespaceAndNewlines();
        $body = $this->_parseLoopBody("for loop");
        return new Forarith($init, $cond, $incr, $body, $this->_collectRedirects(), "for-arith");
    }

    public function parseSelect(): ?Select
    {
        $this->skipWhitespace();
        if (!$this->_lexConsumeWord("select"))
        {
            return null;
        }
        $this->skipWhitespace();
        $varName = $this->peekWord();
        if ($varName === "")
        {
            throw new Parseerror_("Expected variable name after 'select'");
        }
        $this->consumeWord($varName);
        $this->skipWhitespace();
        if ($this->peek() === ";")
        {
            $this->advance();
        }
        $this->skipWhitespaceAndNewlines();
        $words = null;
        if ($this->_lexIsAtReservedWord("in"))
        {
            $this->_lexConsumeWord("in");
            $this->skipWhitespaceAndNewlines();
            $words = [];
            while (true)
            {
                $this->skipWhitespace();
                if ($this->atEnd())
                {
                    break;
                }
                if (_isSemicolonNewlineBrace($this->peek()))
                {
                    if ($this->peek() === ";")
                    {
                        $this->advance();
                    }
                    break;
                }
                if ($this->_lexIsAtReservedWord("do"))
                {
                    break;
                }
                $word = $this->parseWord(false, false, false);
                if ($word === null)
                {
                    break;
                }
                array_push($words, $word);
            }
        }
        $this->skipWhitespaceAndNewlines();
        $body = $this->_parseLoopBody("select");
        return new Select($varName, $body, $this->_collectRedirects(), "select", $words);
    }

    public function _consumeCaseTerminator(): string
    {
        $term = $this->_lexPeekCaseTerminator();
        if ($term !== "")
        {
            $this->_lexNextToken();
            return $term;
        }
        return ";;";
    }

    public function parseCase(): ?Case_
    {
        if (!$this->consumeWord("case"))
        {
            return null;
        }
        $this->_setState(PARSERSTATEFLAGS_PST_CASESTMT);
        $this->skipWhitespace();
        $word = $this->parseWord(false, false, false);
        if ($word === null)
        {
            throw new Parseerror_("Expected word after 'case'");
        }
        $this->skipWhitespaceAndNewlines();
        if (!$this->_lexConsumeWord("in"))
        {
            throw new Parseerror_("Expected 'in' after case word");
        }
        $this->skipWhitespaceAndNewlines();
        $patterns = [];
        $this->_setState(PARSERSTATEFLAGS_PST_CASEPAT);
        while (true)
        {
            $this->skipWhitespaceAndNewlines();
            if ($this->_lexIsAtReservedWord("esac"))
            {
                $saved = $this->pos;
                $this->skipWhitespace();
                while (!$this->atEnd() && !_isMetachar($this->peek()) && !_isQuote($this->peek()))
                {
                    $this->advance();
                }
                $this->skipWhitespace();
                $isPattern = false;
                if (!$this->atEnd() && $this->peek() === ")")
                {
                    if ($this->_eofToken === ")")
                    {
                        $isPattern = false;
                    }
                    else
                    {
                        $this->advance();
                        $this->skipWhitespace();
                        if (!$this->atEnd())
                        {
                            $nextCh = $this->peek();
                            if ($nextCh === ";")
                            {
                                $isPattern = true;
                            }
                            else
                            {
                                if (!_isNewlineOrRightParen($nextCh))
                                {
                                    $isPattern = true;
                                }
                            }
                        }
                    }
                }
                $this->pos = $saved;
                if (!$isPattern)
                {
                    break;
                }
            }
            $this->skipWhitespaceAndNewlines();
            if (!$this->atEnd() && $this->peek() === "(")
            {
                $this->advance();
                $this->skipWhitespaceAndNewlines();
            }
            $patternChars = [];
            $extglobDepth = 0;
            while (!$this->atEnd())
            {
                $ch = $this->peek();
                if ($ch === ")")
                {
                    if ($extglobDepth > 0)
                    {
                        array_push($patternChars, $this->advance());
                        $extglobDepth -= 1;
                    }
                    else
                    {
                        $this->advance();
                        break;
                    }
                }
                else
                {
                    if ($ch === "\\")
                    {
                        if ($this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "\n")
                        {
                            $this->advance();
                            $this->advance();
                        }
                        else
                        {
                            array_push($patternChars, $this->advance());
                            if (!$this->atEnd())
                            {
                                array_push($patternChars, $this->advance());
                            }
                        }
                    }
                    else
                    {
                        if (_isExpansionStart($this->source, $this->pos, "\$("))
                        {
                            array_push($patternChars, $this->advance());
                            array_push($patternChars, $this->advance());
                            if (!$this->atEnd() && $this->peek() === "(")
                            {
                                array_push($patternChars, $this->advance());
                                $parenDepth = 2;
                                while (!$this->atEnd() && $parenDepth > 0)
                                {
                                    $c = $this->peek();
                                    if ($c === "(")
                                    {
                                        $parenDepth += 1;
                                    }
                                    else
                                    {
                                        if ($c === ")")
                                        {
                                            $parenDepth -= 1;
                                        }
                                    }
                                    array_push($patternChars, $this->advance());
                                }
                            }
                            else
                            {
                                $extglobDepth += 1;
                            }
                        }
                        else
                        {
                            if ($ch === "(" && $extglobDepth > 0)
                            {
                                array_push($patternChars, $this->advance());
                                $extglobDepth += 1;
                            }
                            else
                            {
                                if ($this->_extglob && _isExtglobPrefix($ch) && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "(")
                                {
                                    array_push($patternChars, $this->advance());
                                    array_push($patternChars, $this->advance());
                                    $extglobDepth += 1;
                                }
                                else
                                {
                                    if ($ch === "[")
                                    {
                                        $isCharClass = false;
                                        $scanPos = $this->pos + 1;
                                        $scanDepth = 0;
                                        $hasFirstBracketLiteral = false;
                                        if ($scanPos < $this->length && _isCaretOrBang((string)(mb_substr($this->source, $scanPos, 1))))
                                        {
                                            $scanPos += 1;
                                        }
                                        if ($scanPos < $this->length && (string)(mb_substr($this->source, $scanPos, 1)) === "]")
                                        {
                                            if ((mb_strpos($this->source, "]", $scanPos + 1) === false ? -1 : mb_strpos($this->source, "]", $scanPos + 1)) !== -1)
                                            {
                                                $scanPos += 1;
                                                $hasFirstBracketLiteral = true;
                                            }
                                        }
                                        while ($scanPos < $this->length)
                                        {
                                            $sc = (string)(mb_substr($this->source, $scanPos, 1));
                                            if ($sc === "]" && $scanDepth === 0)
                                            {
                                                $isCharClass = true;
                                                break;
                                            }
                                            else
                                            {
                                                if ($sc === "[")
                                                {
                                                    $scanDepth += 1;
                                                }
                                                else
                                                {
                                                    if ($sc === ")" && $scanDepth === 0)
                                                    {
                                                        break;
                                                    }
                                                    else
                                                    {
                                                        if ($sc === "|" && $scanDepth === 0)
                                                        {
                                                            break;
                                                        }
                                                    }
                                                }
                                            }
                                            $scanPos += 1;
                                        }
                                        if ($isCharClass)
                                        {
                                            array_push($patternChars, $this->advance());
                                            if (!$this->atEnd() && _isCaretOrBang($this->peek()))
                                            {
                                                array_push($patternChars, $this->advance());
                                            }
                                            if ($hasFirstBracketLiteral && !$this->atEnd() && $this->peek() === "]")
                                            {
                                                array_push($patternChars, $this->advance());
                                            }
                                            while (!$this->atEnd() && $this->peek() !== "]")
                                            {
                                                array_push($patternChars, $this->advance());
                                            }
                                            if (!$this->atEnd())
                                            {
                                                array_push($patternChars, $this->advance());
                                            }
                                        }
                                        else
                                        {
                                            array_push($patternChars, $this->advance());
                                        }
                                    }
                                    else
                                    {
                                        if ($ch === "'")
                                        {
                                            array_push($patternChars, $this->advance());
                                            while (!$this->atEnd() && $this->peek() !== "'")
                                            {
                                                array_push($patternChars, $this->advance());
                                            }
                                            if (!$this->atEnd())
                                            {
                                                array_push($patternChars, $this->advance());
                                            }
                                        }
                                        else
                                        {
                                            if ($ch === "\"")
                                            {
                                                array_push($patternChars, $this->advance());
                                                while (!$this->atEnd() && $this->peek() !== "\"")
                                                {
                                                    if ($this->peek() === "\\" && $this->pos + 1 < $this->length)
                                                    {
                                                        array_push($patternChars, $this->advance());
                                                    }
                                                    array_push($patternChars, $this->advance());
                                                }
                                                if (!$this->atEnd())
                                                {
                                                    array_push($patternChars, $this->advance());
                                                }
                                            }
                                            else
                                            {
                                                if (_isWhitespace($ch))
                                                {
                                                    if ($extglobDepth > 0)
                                                    {
                                                        array_push($patternChars, $this->advance());
                                                    }
                                                    else
                                                    {
                                                        $this->advance();
                                                    }
                                                }
                                                else
                                                {
                                                    array_push($patternChars, $this->advance());
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
            $pattern = implode("", $patternChars);
            if (!($pattern !== ''))
            {
                throw new Parseerror_("Expected pattern in case statement");
            }
            $this->skipWhitespace();
            $body = null;
            $isEmptyBody = $this->_lexPeekCaseTerminator() !== "";
            if (!$isEmptyBody)
            {
                $this->skipWhitespaceAndNewlines();
                if (!$this->atEnd() && !$this->_lexIsAtReservedWord("esac"))
                {
                    $isAtTerminator = $this->_lexPeekCaseTerminator() !== "";
                    if (!$isAtTerminator)
                    {
                        $body = $this->parseListUntil(["esac" => true]);
                        $this->skipWhitespace();
                    }
                }
            }
            $terminator = $this->_consumeCaseTerminator();
            $this->skipWhitespaceAndNewlines();
            array_push($patterns, new Casepattern($pattern, $body, $terminator, "pattern"));
        }
        $this->_clearState(PARSERSTATEFLAGS_PST_CASEPAT);
        $this->skipWhitespaceAndNewlines();
        if (!$this->_lexConsumeWord("esac"))
        {
            $this->_clearState(PARSERSTATEFLAGS_PST_CASESTMT);
            throw new Parseerror_("Expected 'esac' to close case statement");
        }
        $this->_clearState(PARSERSTATEFLAGS_PST_CASESTMT);
        return new Case_($word, $patterns, $this->_collectRedirects(), "case");
    }

    public function parseCoproc(): ?Coproc
    {
        $this->skipWhitespace();
        if (!$this->_lexConsumeWord("coproc"))
        {
            return null;
        }
        $this->skipWhitespace();
        $name = "";
        $ch = "";
        if (!$this->atEnd())
        {
            $ch = $this->peek();
        }
        $body = null;
        if ($ch === "{")
        {
            $body = $this->parseBraceGroup();
            if ($body !== null)
            {
                return new Coproc($body, $name, "coproc");
            }
        }
        if ($ch === "(")
        {
            if ($this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "(")
            {
                $body = $this->parseArithmeticCommand();
                if ($body !== null)
                {
                    return new Coproc($body, $name, "coproc");
                }
            }
            $body = $this->parseSubshell();
            if ($body !== null)
            {
                return new Coproc($body, $name, "coproc");
            }
        }
        $nextWord = $this->_lexPeekReservedWord();
        if ($nextWord !== "" && (isset(COMPOUND_KEYWORDS[$nextWord])))
        {
            $body = $this->parseCompoundCommand();
            if ($body !== null)
            {
                return new Coproc($body, $name, "coproc");
            }
        }
        $wordStart = $this->pos;
        $potentialName = $this->peekWord();
        if (($potentialName !== ''))
        {
            while (!$this->atEnd() && !_isMetachar($this->peek()) && !_isQuote($this->peek()))
            {
                $this->advance();
            }
            $this->skipWhitespace();
            $ch = "";
            if (!$this->atEnd())
            {
                $ch = $this->peek();
            }
            $nextWord = $this->_lexPeekReservedWord();
            if (_isValidIdentifier($potentialName))
            {
                if ($ch === "{")
                {
                    $name = $potentialName;
                    $body = $this->parseBraceGroup();
                    if ($body !== null)
                    {
                        return new Coproc($body, $name, "coproc");
                    }
                }
                else
                {
                    if ($ch === "(")
                    {
                        $name = $potentialName;
                        if ($this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "(")
                        {
                            $body = $this->parseArithmeticCommand();
                        }
                        else
                        {
                            $body = $this->parseSubshell();
                        }
                        if ($body !== null)
                        {
                            return new Coproc($body, $name, "coproc");
                        }
                    }
                    else
                    {
                        if ($nextWord !== "" && (isset(COMPOUND_KEYWORDS[$nextWord])))
                        {
                            $name = $potentialName;
                            $body = $this->parseCompoundCommand();
                            if ($body !== null)
                            {
                                return new Coproc($body, $name, "coproc");
                            }
                        }
                    }
                }
            }
            $this->pos = $wordStart;
        }
        $body = $this->parseCommand();
        if ($body !== null)
        {
            return new Coproc($body, $name, "coproc");
        }
        throw new Parseerror_("Expected command after coproc");
    }

    public function parseFunction(): ?Function_
    {
        $this->skipWhitespace();
        if ($this->atEnd())
        {
            return null;
        }
        $savedPos = $this->pos;
        $name = "";
        $body = null;
        if ($this->_lexIsAtReservedWord("function"))
        {
            $this->_lexConsumeWord("function");
            $this->skipWhitespace();
            $name = $this->peekWord();
            if ($name === "")
            {
                $this->pos = $savedPos;
                return null;
            }
            $this->consumeWord($name);
            $this->skipWhitespace();
            if (!$this->atEnd() && $this->peek() === "(")
            {
                if ($this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === ")")
                {
                    $this->advance();
                    $this->advance();
                }
            }
            $this->skipWhitespaceAndNewlines();
            $body = $this->_parseCompoundCommand();
            if ($body === null)
            {
                throw new Parseerror_("Expected function body");
            }
            return new Function_($name, $body, "function");
        }
        $name = $this->peekWord();
        if ($name === "" || (isset(RESERVED_WORDS[$name])))
        {
            return null;
        }
        if (_looksLikeAssignment($name))
        {
            return null;
        }
        $this->skipWhitespace();
        $nameStart = $this->pos;
        while (!$this->atEnd() && !_isMetachar($this->peek()) && !_isQuote($this->peek()) && !_isParen($this->peek()))
        {
            $this->advance();
        }
        $name = _substring($this->source, $nameStart, $this->pos);
        if (!($name !== ''))
        {
            $this->pos = $savedPos;
            return null;
        }
        $braceDepth = 0;
        $i = 0;
        while ($i < mb_strlen($name))
        {
            if (_isExpansionStart($name, $i, "\${"))
            {
                $braceDepth += 1;
                $i += 2;
                continue;
            }
            if ((string)(mb_substr($name, $i, 1)) === "}")
            {
                $braceDepth -= 1;
            }
            $i += 1;
        }
        if ($braceDepth > 0)
        {
            $this->pos = $savedPos;
            return null;
        }
        $posAfterName = $this->pos;
        $this->skipWhitespace();
        $hasWhitespace = $this->pos > $posAfterName;
        if (!$hasWhitespace && ($name !== '') && ((str_contains("*?@+!\$", (string)(mb_substr($name, mb_strlen($name) - 1, 1))))))
        {
            $this->pos = $savedPos;
            return null;
        }
        if ($this->atEnd() || $this->peek() !== "(")
        {
            $this->pos = $savedPos;
            return null;
        }
        $this->advance();
        $this->skipWhitespace();
        if ($this->atEnd() || $this->peek() !== ")")
        {
            $this->pos = $savedPos;
            return null;
        }
        $this->advance();
        $this->skipWhitespaceAndNewlines();
        $body = $this->_parseCompoundCommand();
        if ($body === null)
        {
            throw new Parseerror_("Expected function body");
        }
        return new Function_($name, $body, "function");
    }

    public function _parseCompoundCommand(): ?Node
    {
        $result = $this->parseBraceGroup();
        if ($result !== null)
        {
            return $result;
        }
        if (!$this->atEnd() && $this->peek() === "(" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "(")
        {
            $result = $this->parseArithmeticCommand();
            if ($result !== null)
            {
                return $result;
            }
        }
        $result = $this->parseSubshell();
        if ($result !== null)
        {
            return $result;
        }
        $result = $this->parseConditionalExpr();
        if ($result !== null)
        {
            return $result;
        }
        $result = $this->parseIf();
        if ($result !== null)
        {
            return $result;
        }
        $result = $this->parseWhile();
        if ($result !== null)
        {
            return $result;
        }
        $result = $this->parseUntil();
        if ($result !== null)
        {
            return $result;
        }
        $result = $this->parseFor();
        if ($result !== null)
        {
            return $result;
        }
        $result = $this->parseCase();
        if ($result !== null)
        {
            return $result;
        }
        $result = $this->parseSelect();
        if ($result !== null)
        {
            return $result;
        }
        return null;
    }

    public function _atListUntilTerminator(array $stopWords): bool
    {
        if ($this->atEnd())
        {
            return true;
        }
        if ($this->peek() === ")")
        {
            return true;
        }
        if ($this->peek() === "}")
        {
            $nextPos = $this->pos + 1;
            if ($nextPos >= $this->length || _isWordEndContext((string)(mb_substr($this->source, $nextPos, 1))))
            {
                return true;
            }
        }
        $reserved = $this->_lexPeekReservedWord();
        if ($reserved !== "" && (isset($stopWords[$reserved])))
        {
            return true;
        }
        if ($this->_lexPeekCaseTerminator() !== "")
        {
            return true;
        }
        return false;
    }

    public function parseListUntil(array $stopWords): ?Node
    {
        $this->skipWhitespaceAndNewlines();
        $reserved = $this->_lexPeekReservedWord();
        if ($reserved !== "" && (isset($stopWords[$reserved])))
        {
            return null;
        }
        $pipeline = $this->parsePipeline();
        if ($pipeline === null)
        {
            return null;
        }
        $parts = [$pipeline];
        while (true)
        {
            $this->skipWhitespace();
            $op = $this->parseListOperator();
            if ($op === "")
            {
                if (!$this->atEnd() && $this->peek() === "\n")
                {
                    $this->advance();
                    $this->_gatherHeredocBodies();
                    if ($this->_cmdsubHeredocEnd !== -1 && $this->_cmdsubHeredocEnd > $this->pos)
                    {
                        $this->pos = $this->_cmdsubHeredocEnd;
                        $this->_cmdsubHeredocEnd = -1;
                    }
                    $this->skipWhitespaceAndNewlines();
                    if ($this->_atListUntilTerminator($stopWords))
                    {
                        break;
                    }
                    $nextOp = $this->_peekListOperator();
                    if ($nextOp === "&" || $nextOp === ";")
                    {
                        break;
                    }
                    $op = "\n";
                }
                else
                {
                    break;
                }
            }
            if ($op === "")
            {
                break;
            }
            if ($op === ";")
            {
                $this->skipWhitespaceAndNewlines();
                if ($this->_atListUntilTerminator($stopWords))
                {
                    break;
                }
                array_push($parts, new Operator($op, "operator"));
            }
            else
            {
                if ($op === "&")
                {
                    array_push($parts, new Operator($op, "operator"));
                    $this->skipWhitespaceAndNewlines();
                    if ($this->_atListUntilTerminator($stopWords))
                    {
                        break;
                    }
                }
                else
                {
                    if ($op === "&&" || $op === "||")
                    {
                        array_push($parts, new Operator($op, "operator"));
                        $this->skipWhitespaceAndNewlines();
                    }
                    else
                    {
                        array_push($parts, new Operator($op, "operator"));
                    }
                }
            }
            if ($this->_atListUntilTerminator($stopWords))
            {
                break;
            }
            $pipeline = $this->parsePipeline();
            if ($pipeline === null)
            {
                throw new Parseerror_("Expected command after " . $op);
            }
            array_push($parts, $pipeline);
        }
        if (count($parts) === 1)
        {
            return $parts[0];
        }
        return new List_($parts, "list");
    }

    public function parseCompoundCommand(): ?Node
    {
        $this->skipWhitespace();
        if ($this->atEnd())
        {
            return null;
        }
        $ch = $this->peek();
        $result = null;
        if ($ch === "(" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "(")
        {
            $result = $this->parseArithmeticCommand();
            if ($result !== null)
            {
                return $result;
            }
        }
        if ($ch === "(")
        {
            return $this->parseSubshell();
        }
        if ($ch === "{")
        {
            $result = $this->parseBraceGroup();
            if ($result !== null)
            {
                return $result;
            }
        }
        if ($ch === "[" && $this->pos + 1 < $this->length && (string)(mb_substr($this->source, $this->pos + 1, 1)) === "[")
        {
            $result = $this->parseConditionalExpr();
            if ($result !== null)
            {
                return $result;
            }
        }
        $reserved = $this->_lexPeekReservedWord();
        if ($reserved === "" && $this->_inProcessSub)
        {
            $word = $this->peekWord();
            if ($word !== "" && mb_strlen($word) > 1 && (string)(mb_substr($word, 0, 1)) === "}")
            {
                $keywordWord = mb_substr($word, 1);
                if ((isset(RESERVED_WORDS[$keywordWord])) || $keywordWord === "{" || $keywordWord === "}" || $keywordWord === "[[" || $keywordWord === "]]" || $keywordWord === "!" || $keywordWord === "time")
                {
                    $reserved = $keywordWord;
                }
            }
        }
        if ($reserved === "fi" || $reserved === "then" || $reserved === "elif" || $reserved === "else" || $reserved === "done" || $reserved === "esac" || $reserved === "do" || $reserved === "in")
        {
            throw new Parseerror_(sprintf("Unexpected reserved word '%s'", $reserved));
        }
        if ($reserved === "if")
        {
            return $this->parseIf();
        }
        if ($reserved === "while")
        {
            return $this->parseWhile();
        }
        if ($reserved === "until")
        {
            return $this->parseUntil();
        }
        if ($reserved === "for")
        {
            return $this->parseFor();
        }
        if ($reserved === "select")
        {
            return $this->parseSelect();
        }
        if ($reserved === "case")
        {
            return $this->parseCase();
        }
        if ($reserved === "function")
        {
            return $this->parseFunction();
        }
        if ($reserved === "coproc")
        {
            return $this->parseCoproc();
        }
        $func = $this->parseFunction();
        if ($func !== null)
        {
            return $func;
        }
        return $this->parseCommand();
    }

    public function parsePipeline(): ?Node
    {
        $this->skipWhitespace();
        $prefixOrder = "";
        $timePosix = false;
        if ($this->_lexIsAtReservedWord("time"))
        {
            $this->_lexConsumeWord("time");
            $prefixOrder = "time";
            $this->skipWhitespace();
            $saved = 0;
            if (!$this->atEnd() && $this->peek() === "-")
            {
                $saved = $this->pos;
                $this->advance();
                if (!$this->atEnd() && $this->peek() === "p")
                {
                    $this->advance();
                    if ($this->atEnd() || _isMetachar($this->peek()))
                    {
                        $timePosix = true;
                    }
                    else
                    {
                        $this->pos = $saved;
                    }
                }
                else
                {
                    $this->pos = $saved;
                }
            }
            $this->skipWhitespace();
            if (!$this->atEnd() && _startsWithAt($this->source, $this->pos, "--"))
            {
                if ($this->pos + 2 >= $this->length || _isWhitespace((string)(mb_substr($this->source, $this->pos + 2, 1))))
                {
                    $this->advance();
                    $this->advance();
                    $timePosix = true;
                    $this->skipWhitespace();
                }
            }
            while ($this->_lexIsAtReservedWord("time"))
            {
                $this->_lexConsumeWord("time");
                $this->skipWhitespace();
                if (!$this->atEnd() && $this->peek() === "-")
                {
                    $saved = $this->pos;
                    $this->advance();
                    if (!$this->atEnd() && $this->peek() === "p")
                    {
                        $this->advance();
                        if ($this->atEnd() || _isMetachar($this->peek()))
                        {
                            $timePosix = true;
                        }
                        else
                        {
                            $this->pos = $saved;
                        }
                    }
                    else
                    {
                        $this->pos = $saved;
                    }
                }
            }
            $this->skipWhitespace();
            if (!$this->atEnd() && $this->peek() === "!")
            {
                if (($this->pos + 1 >= $this->length || _isNegationBoundary((string)(mb_substr($this->source, $this->pos + 1, 1)))) && !$this->_isBangFollowedByProcsub())
                {
                    $this->advance();
                    $prefixOrder = "time_negation";
                    $this->skipWhitespace();
                }
            }
        }
        else
        {
            if (!$this->atEnd() && $this->peek() === "!")
            {
                if (($this->pos + 1 >= $this->length || _isNegationBoundary((string)(mb_substr($this->source, $this->pos + 1, 1)))) && !$this->_isBangFollowedByProcsub())
                {
                    $this->advance();
                    $this->skipWhitespace();
                    $inner = $this->parsePipeline();
                    if ($inner !== null && $inner->kind === "negation")
                    {
                        if ($inner->pipeline !== null)
                        {
                            return $inner->pipeline;
                        }
                        else
                        {
                            return new Command([], [], "command");
                        }
                    }
                    return new Negation($inner, "negation");
                }
            }
        }
        $result = $this->_parseSimplePipeline();
        if ($prefixOrder === "time")
        {
            $result = new Time($result, $timePosix, "time");
        }
        else
        {
            if ($prefixOrder === "negation")
            {
                $result = new Negation($result, "negation");
            }
            else
            {
                if ($prefixOrder === "time_negation")
                {
                    $result = new Time($result, $timePosix, "time");
                    $result = new Negation($result, "negation");
                }
                else
                {
                    if ($prefixOrder === "negation_time")
                    {
                        $result = new Time($result, $timePosix, "time");
                        $result = new Negation($result, "negation");
                    }
                    else
                    {
                        if ($result === null)
                        {
                            return null;
                        }
                    }
                }
            }
        }
        return $result;
    }

    public function _parseSimplePipeline(): ?Node
    {
        $cmd = $this->parseCompoundCommand();
        if ($cmd === null)
        {
            return null;
        }
        $commands = [$cmd];
        while (true)
        {
            $this->skipWhitespace();
            [$tokenType, $value] = $this->_lexPeekOperator();
            if ($tokenType === 0)
            {
                break;
            }
            if ($tokenType !== TOKENTYPE_PIPE && $tokenType !== TOKENTYPE_PIPE_AMP)
            {
                break;
            }
            $this->_lexNextToken();
            $isPipeBoth = $tokenType === TOKENTYPE_PIPE_AMP;
            $this->skipWhitespaceAndNewlines();
            if ($isPipeBoth)
            {
                array_push($commands, new Pipeboth("pipe-both"));
            }
            $cmd = $this->parseCompoundCommand();
            if ($cmd === null)
            {
                throw new Parseerror_("Expected command after |");
            }
            array_push($commands, $cmd);
        }
        if (count($commands) === 1)
        {
            return $commands[0];
        }
        return new Pipeline($commands, "pipeline");
    }

    public function parseListOperator(): string
    {
        $this->skipWhitespace();
        [$tokenType, $_] = $this->_lexPeekOperator();
        if ($tokenType === 0)
        {
            return "";
        }
        if ($tokenType === TOKENTYPE_AND_AND)
        {
            $this->_lexNextToken();
            return "&&";
        }
        if ($tokenType === TOKENTYPE_OR_OR)
        {
            $this->_lexNextToken();
            return "||";
        }
        if ($tokenType === TOKENTYPE_SEMI)
        {
            $this->_lexNextToken();
            return ";";
        }
        if ($tokenType === TOKENTYPE_AMP)
        {
            $this->_lexNextToken();
            return "&";
        }
        return "";
    }

    public function _peekListOperator(): string
    {
        $savedPos = $this->pos;
        $op = $this->parseListOperator();
        $this->pos = $savedPos;
        return $op;
    }

    public function parseList(bool $newlineAsSeparator): ?Node
    {
        if ($newlineAsSeparator)
        {
            $this->skipWhitespaceAndNewlines();
        }
        else
        {
            $this->skipWhitespace();
        }
        $pipeline = $this->parsePipeline();
        if ($pipeline === null)
        {
            return null;
        }
        $parts = [$pipeline];
        if ($this->_inState(PARSERSTATEFLAGS_PST_EOFTOKEN) && $this->_atEofToken())
        {
            return (count($parts) === 1 ? $parts[0] : new List_($parts, "list"));
        }
        while (true)
        {
            $this->skipWhitespace();
            $op = $this->parseListOperator();
            if ($op === "")
            {
                if (!$this->atEnd() && $this->peek() === "\n")
                {
                    if (!$newlineAsSeparator)
                    {
                        break;
                    }
                    $this->advance();
                    $this->_gatherHeredocBodies();
                    if ($this->_cmdsubHeredocEnd !== -1 && $this->_cmdsubHeredocEnd > $this->pos)
                    {
                        $this->pos = $this->_cmdsubHeredocEnd;
                        $this->_cmdsubHeredocEnd = -1;
                    }
                    $this->skipWhitespaceAndNewlines();
                    if ($this->atEnd() || $this->_atListTerminatingBracket())
                    {
                        break;
                    }
                    $nextOp = $this->_peekListOperator();
                    if ($nextOp === "&" || $nextOp === ";")
                    {
                        break;
                    }
                    $op = "\n";
                }
                else
                {
                    break;
                }
            }
            if ($op === "")
            {
                break;
            }
            array_push($parts, new Operator($op, "operator"));
            if ($op === "&&" || $op === "||")
            {
                $this->skipWhitespaceAndNewlines();
            }
            else
            {
                if ($op === "&")
                {
                    $this->skipWhitespace();
                    if ($this->atEnd() || $this->_atListTerminatingBracket())
                    {
                        break;
                    }
                    if ($this->peek() === "\n")
                    {
                        if ($newlineAsSeparator)
                        {
                            $this->skipWhitespaceAndNewlines();
                            if ($this->atEnd() || $this->_atListTerminatingBracket())
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
                    if ($op === ";")
                    {
                        $this->skipWhitespace();
                        if ($this->atEnd() || $this->_atListTerminatingBracket())
                        {
                            break;
                        }
                        if ($this->peek() === "\n")
                        {
                            if ($newlineAsSeparator)
                            {
                                $this->skipWhitespaceAndNewlines();
                                if ($this->atEnd() || $this->_atListTerminatingBracket())
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
            $pipeline = $this->parsePipeline();
            if ($pipeline === null)
            {
                throw new Parseerror_("Expected command after " . $op);
            }
            array_push($parts, $pipeline);
            if ($this->_inState(PARSERSTATEFLAGS_PST_EOFTOKEN) && $this->_atEofToken())
            {
                break;
            }
        }
        if (count($parts) === 1)
        {
            return $parts[0];
        }
        return new List_($parts, "list");
    }

    public function parseComment(): ?Node
    {
        if ($this->atEnd() || $this->peek() !== "#")
        {
            return null;
        }
        $start = $this->pos;
        while (!$this->atEnd() && $this->peek() !== "\n")
        {
            $this->advance();
        }
        $text = _substring($this->source, $start, $this->pos);
        return new Comment($text, "comment");
    }

    public function parse(): ?array
    {
        $source = trim($this->source, " \t\n\r");
        if (!($source !== ''))
        {
            return [new Empty_("empty")];
        }
        $results = [];
        while (true)
        {
            $this->skipWhitespace();
            while (!$this->atEnd() && $this->peek() === "\n")
            {
                $this->advance();
            }
            if ($this->atEnd())
            {
                break;
            }
            $comment = $this->parseComment();
            if (!$comment !== null)
            {
                break;
            }
        }
        while (!$this->atEnd())
        {
            $result = $this->parseList(false);
            if ($result !== null)
            {
                array_push($results, $result);
            }
            $this->skipWhitespace();
            $foundNewline = false;
            while (!$this->atEnd() && $this->peek() === "\n")
            {
                $foundNewline = true;
                $this->advance();
                $this->_gatherHeredocBodies();
                if ($this->_cmdsubHeredocEnd !== -1 && $this->_cmdsubHeredocEnd > $this->pos)
                {
                    $this->pos = $this->_cmdsubHeredocEnd;
                    $this->_cmdsubHeredocEnd = -1;
                }
                $this->skipWhitespace();
            }
            if (!$foundNewline && !$this->atEnd())
            {
                throw new Parseerror_("Syntax error");
            }
        }
        if (!(count($results) > 0))
        {
            return [new Empty_("empty")];
        }
        if ($this->_sawNewlineInSingleQuote && ($this->source !== '') && (string)(mb_substr($this->source, mb_strlen($this->source) - 1, 1)) === "\\" && !(mb_strlen($this->source) >= 3 && mb_substr($this->source, mb_strlen($this->source) - 3, (mb_strlen($this->source) - 1) - (mb_strlen($this->source) - 3)) === "\\\n"))
        {
            if (!$this->_lastWordOnOwnLine($results))
            {
                $this->_stripTrailingBackslashFromLastWord($results);
            }
        }
        return $results;
    }

    public function _lastWordOnOwnLine(?array $nodes): bool
    {
        return count($nodes) >= 2;
    }

    public function _stripTrailingBackslashFromLastWord(?array $nodes): void
    {
        if (!(count($nodes) > 0))
        {
            return;
        }
        $lastNode = $nodes[count($nodes) - 1];
        $lastWord = $this->_findLastWord($lastNode);
        if ($lastWord !== null && str_ends_with($lastWord->value, "\\"))
        {
            $lastWord->value = _substring($lastWord->value, 0, mb_strlen($lastWord->value) - 1);
            if (!($lastWord->value !== '') && ($lastNode instanceof Command) && $lastNode->words !== null)
            {
                array_pop($lastNode->words);
            }
        }
    }

    public function _findLastWord(?Node $node): ?Word
    {
        if ($node instanceof Word)
        {
            return $node;
        }
        if ($node instanceof Command)
        {
            if ((count($node->words) > 0))
            {
                $lastWord = $node->words[count($node->words) - 1];
                if (str_ends_with($lastWord->value, "\\"))
                {
                    return $lastWord;
                }
            }
            if ((count($node->redirects) > 0))
            {
                $lastRedirect = $node->redirects[count($node->redirects) - 1];
                if ($lastRedirect instanceof Redirect)
                {
                    return $lastRedirect->target;
                }
            }
            if ((count($node->words) > 0))
            {
                return $node->words[count($node->words) - 1];
            }
        }
        if ($node instanceof Pipeline)
        {
            if ((count($node->commands) > 0))
            {
                return $this->_findLastWord($node->commands[count($node->commands) - 1]);
            }
        }
        if ($node instanceof List_)
        {
            if ((count($node->parts) > 0))
            {
                return $this->_findLastWord($node->parts[count($node->parts) - 1]);
            }
        }
        return null;
    }
}

function _isHexDigit(string $c): bool
{
    return $c >= "0" && $c <= "9" || $c >= "a" && $c <= "f" || $c >= "A" && $c <= "F";
}

function _isOctalDigit(string $c): bool
{
    return $c >= "0" && $c <= "7";
}

function _getAnsiEscape(string $c): int
{
    return (ANSI_C_ESCAPES[$c] ?? -1);
}

function _isWhitespace(string $c): bool
{
    return $c === " " || $c === "\t" || $c === "\n";
}

function _stringToBytes(string $s): ?array
{
    return array_values(unpack('C*', $s));
}

function _isWhitespaceNoNewline(string $c): bool
{
    return $c === " " || $c === "\t";
}

function _substring(string $s, int $start, int $end): string
{
    return mb_substr($s, $start, ($end) - ($start));
}

function _startsWithAt(string $s, int $pos, string $prefix): bool
{
    return str_starts_with(mb_substr($s, $pos), $prefix);
}

function _countConsecutiveDollarsBefore(string $s, int $pos): int
{
    $count = 0;
    $k = $pos - 1;
    while ($k >= 0 && (string)(mb_substr($s, $k, 1)) === "\$")
    {
        $bsCount = 0;
        $j = $k - 1;
        while ($j >= 0 && (string)(mb_substr($s, $j, 1)) === "\\")
        {
            $bsCount += 1;
            $j -= 1;
        }
        if ($bsCount % 2 === 1)
        {
            break;
        }
        $count += 1;
        $k -= 1;
    }
    return $count;
}

function _isExpansionStart(string $s, int $pos, string $delimiter): bool
{
    if (!_startsWithAt($s, $pos, $delimiter))
    {
        return false;
    }
    return _countConsecutiveDollarsBefore($s, $pos) % 2 === 0;
}

function _sublist(?array $lst, int $start, int $end): ?array
{
    return array_slice($lst, $start, ($end) - ($start));
}

function _repeatStr(string $s, int $n): string
{
    $result = [];
    $i = 0;
    while ($i < $n)
    {
        array_push($result, $s);
        $i += 1;
    }
    return implode("", $result);
}

function _stripLineContinuationsCommentAware(string $text): string
{
    $result = [];
    $i = 0;
    $inComment = false;
    $quote = newQuoteState();
    while ($i < mb_strlen($text))
    {
        $c = (string)(mb_substr($text, $i, 1));
        if ($c === "\\" && $i + 1 < mb_strlen($text) && (string)(mb_substr($text, $i + 1, 1)) === "\n")
        {
            $numPrecedingBackslashes = 0;
            $j = $i - 1;
            while ($j >= 0 && (string)(mb_substr($text, $j, 1)) === "\\")
            {
                $numPrecedingBackslashes += 1;
                $j -= 1;
            }
            if ($numPrecedingBackslashes % 2 === 0)
            {
                if ($inComment)
                {
                    array_push($result, "\n");
                }
                $i += 2;
                $inComment = false;
                continue;
            }
        }
        if ($c === "\n")
        {
            $inComment = false;
            array_push($result, $c);
            $i += 1;
            continue;
        }
        if ($c === "'" && !$quote->double && !$inComment)
        {
            $quote->single = !$quote->single;
        }
        else
        {
            if ($c === "\"" && !$quote->single && !$inComment)
            {
                $quote->double = !$quote->double;
            }
            else
            {
                if ($c === "#" && !$quote->single && !$inComment)
                {
                    $inComment = true;
                }
            }
        }
        array_push($result, $c);
        $i += 1;
    }
    return implode("", $result);
}

function _appendRedirects(string $base, ?array $redirects): string
{
    if ((count($redirects) > 0))
    {
        $parts = [];
        foreach ($redirects as $r)
        {
            array_push($parts, $r->toSexp());
        }
        return $base . " " . implode(" ", $parts);
    }
    return $base;
}

function _formatArithVal(string $s): string
{
    $w = new Word($s, [], "word");
    $val = $w->_expandAllAnsiCQuotes($s);
    $val = $w->_stripLocaleStringDollars($val);
    $val = $w->_formatCommandSubstitutions($val, false);
    $val = str_replace("\"", "\\\"", str_replace("\\", "\\\\", $val));
    $val = str_replace("\t", "\\t", str_replace("\n", "\\n", $val));
    return $val;
}

function _consumeSingleQuote(string $s, int $start): array
{
    $chars = ["'"];
    $i = $start + 1;
    while ($i < mb_strlen($s) && (string)(mb_substr($s, $i, 1)) !== "'")
    {
        array_push($chars, (string)(mb_substr($s, $i, 1)));
        $i += 1;
    }
    if ($i < mb_strlen($s))
    {
        array_push($chars, (string)(mb_substr($s, $i, 1)));
        $i += 1;
    }
    return [$i, $chars];
}

function _consumeDoubleQuote(string $s, int $start): array
{
    $chars = ["\""];
    $i = $start + 1;
    while ($i < mb_strlen($s) && (string)(mb_substr($s, $i, 1)) !== "\"")
    {
        if ((string)(mb_substr($s, $i, 1)) === "\\" && $i + 1 < mb_strlen($s))
        {
            array_push($chars, (string)(mb_substr($s, $i, 1)));
            $i += 1;
        }
        array_push($chars, (string)(mb_substr($s, $i, 1)));
        $i += 1;
    }
    if ($i < mb_strlen($s))
    {
        array_push($chars, (string)(mb_substr($s, $i, 1)));
        $i += 1;
    }
    return [$i, $chars];
}

function _hasBracketClose(string $s, int $start, int $depth): bool
{
    $i = $start;
    while ($i < mb_strlen($s))
    {
        if ((string)(mb_substr($s, $i, 1)) === "]")
        {
            return true;
        }
        if (((string)(mb_substr($s, $i, 1)) === "|" || (string)(mb_substr($s, $i, 1)) === ")") && $depth === 0)
        {
            return false;
        }
        $i += 1;
    }
    return false;
}

function _consumeBracketClass(string $s, int $start, int $depth): array
{
    $scanPos = $start + 1;
    if ($scanPos < mb_strlen($s) && ((string)(mb_substr($s, $scanPos, 1)) === "!" || (string)(mb_substr($s, $scanPos, 1)) === "^"))
    {
        $scanPos += 1;
    }
    if ($scanPos < mb_strlen($s) && (string)(mb_substr($s, $scanPos, 1)) === "]")
    {
        if (_hasBracketClose($s, $scanPos + 1, $depth))
        {
            $scanPos += 1;
        }
    }
    $isBracket = false;
    while ($scanPos < mb_strlen($s))
    {
        if ((string)(mb_substr($s, $scanPos, 1)) === "]")
        {
            $isBracket = true;
            break;
        }
        if ((string)(mb_substr($s, $scanPos, 1)) === ")" && $depth === 0)
        {
            break;
        }
        if ((string)(mb_substr($s, $scanPos, 1)) === "|" && $depth === 0)
        {
            break;
        }
        $scanPos += 1;
    }
    if (!$isBracket)
    {
        return [$start + 1, ["["], false];
    }
    $chars = ["["];
    $i = $start + 1;
    if ($i < mb_strlen($s) && ((string)(mb_substr($s, $i, 1)) === "!" || (string)(mb_substr($s, $i, 1)) === "^"))
    {
        array_push($chars, (string)(mb_substr($s, $i, 1)));
        $i += 1;
    }
    if ($i < mb_strlen($s) && (string)(mb_substr($s, $i, 1)) === "]")
    {
        if (_hasBracketClose($s, $i + 1, $depth))
        {
            array_push($chars, (string)(mb_substr($s, $i, 1)));
            $i += 1;
        }
    }
    while ($i < mb_strlen($s) && (string)(mb_substr($s, $i, 1)) !== "]")
    {
        array_push($chars, (string)(mb_substr($s, $i, 1)));
        $i += 1;
    }
    if ($i < mb_strlen($s))
    {
        array_push($chars, (string)(mb_substr($s, $i, 1)));
        $i += 1;
    }
    return [$i, $chars, true];
}

function _formatCondBody(?Node $node): string
{
    $kind = $node->kind;
    if ($kind === "unary-test")
    {
        $operandVal = $node->operand->getCondFormattedValue();
        return $node->op . " " . $operandVal;
    }
    if ($kind === "binary-test")
    {
        $leftVal = $node->left->getCondFormattedValue();
        $rightVal = $node->right->getCondFormattedValue();
        return $leftVal . " " . $node->op . " " . $rightVal;
    }
    if ($kind === "cond-and")
    {
        return _formatCondBody($node->left) . " && " . _formatCondBody($node->right);
    }
    if ($kind === "cond-or")
    {
        return _formatCondBody($node->left) . " || " . _formatCondBody($node->right);
    }
    if ($kind === "cond-not")
    {
        return "! " . _formatCondBody($node->operand);
    }
    if ($kind === "cond-paren")
    {
        return "( " . _formatCondBody($node->inner) . " )";
    }
    return "";
}

function _startsWithSubshell(?Node $node): bool
{
    if ($node instanceof Subshell)
    {
        return true;
    }
    if ($node instanceof List_)
    {
        foreach ($node->parts as $p)
        {
            if ($p->kind !== "operator")
            {
                return _startsWithSubshell($p);
            }
        }
        return false;
    }
    if ($node instanceof Pipeline)
    {
        if ((count($node->commands) > 0))
        {
            return _startsWithSubshell($node->commands[0]);
        }
        return false;
    }
    return false;
}

function _formatCmdsubNode(?Node $node, int $indent, bool $inProcsub, bool $compactRedirects, bool $procsubFirst): string
{
    if ($node === null)
    {
        return "";
    }
    $sp = _repeatStr(" ", $indent);
    $innerSp = _repeatStr(" ", $indent + 4);
    if ($node instanceof Arithempty)
    {
        return "";
    }
    if ($node instanceof Command)
    {
        $parts = [];
        foreach ($node->words as $w)
        {
            $val = $w->_expandAllAnsiCQuotes($w->value);
            $val = $w->_stripLocaleStringDollars($val);
            $val = $w->_normalizeArrayWhitespace($val);
            $val = $w->_formatCommandSubstitutions($val, false);
            array_push($parts, $val);
        }
        $heredocs = [];
        foreach ($node->redirects as $r)
        {
            if ($r instanceof Heredoc)
            {
                array_push($heredocs, $r);
            }
        }
        foreach ($node->redirects as $r)
        {
            array_push($parts, _formatRedirect($r, $compactRedirects, true));
        }
        $result = "";
        if ($compactRedirects && (count($node->words) > 0) && (count($node->redirects) > 0))
        {
            $wordParts = array_slice($parts, 0, count($node->words));
            $redirectParts = array_slice($parts, count($node->words));
            $result = implode(" ", $wordParts) . implode("", $redirectParts);
        }
        else
        {
            $result = implode(" ", $parts);
        }
        foreach ($heredocs as $h)
        {
            $result = $result . _formatHeredocBody($h);
        }
        return $result;
    }
    if ($node instanceof Pipeline)
    {
        $cmds = [];
        $i = 0;
        $cmd = null;
        $needsRedirect = false;
        while ($i < count($node->commands))
        {
            $cmd = $node->commands[$i];
            if ($cmd instanceof Pipeboth)
            {
                $i += 1;
                continue;
            }
            $needsRedirect = $i + 1 < count($node->commands) && $node->commands[$i + 1]->kind === "pipe-both";
            array_push($cmds, [$cmd, $needsRedirect]);
            $i += 1;
        }
        $resultParts = [];
        $idx = 0;
        while ($idx < count($cmds))
        {
            {
                $_entry = $cmds[$idx];
                $cmd = $_entry[0];
                $needsRedirect = $_entry[1];
            }
            $formatted = _formatCmdsubNode($cmd, $indent, $inProcsub, false, $procsubFirst && $idx === 0);
            $isLast = $idx === count($cmds) - 1;
            $hasHeredoc = false;
            if ($cmd->kind === "command" && $cmd->redirects !== null)
            {
                foreach ($cmd->redirects as $r)
                {
                    if ($r instanceof Heredoc)
                    {
                        $hasHeredoc = true;
                        break;
                    }
                }
            }
            $firstNl = 0;
            if ($needsRedirect)
            {
                if ($hasHeredoc)
                {
                    $firstNl = (mb_strpos($formatted, "\n") === false ? -1 : mb_strpos($formatted, "\n"));
                    if ($firstNl !== -1)
                    {
                        $formatted = mb_substr($formatted, 0, $firstNl) . " 2>&1" . mb_substr($formatted, $firstNl);
                    }
                    else
                    {
                        $formatted = $formatted . " 2>&1";
                    }
                }
                else
                {
                    $formatted = $formatted . " 2>&1";
                }
            }
            if (!$isLast && $hasHeredoc)
            {
                $firstNl = (mb_strpos($formatted, "\n") === false ? -1 : mb_strpos($formatted, "\n"));
                if ($firstNl !== -1)
                {
                    $formatted = mb_substr($formatted, 0, $firstNl) . " |" . mb_substr($formatted, $firstNl);
                }
                array_push($resultParts, $formatted);
            }
            else
            {
                array_push($resultParts, $formatted);
            }
            $idx += 1;
        }
        $compactPipe = $inProcsub && (count($cmds) > 0) && $cmds[0][0]->kind === "subshell";
        $result = "";
        $idx = 0;
        while ($idx < count($resultParts))
        {
            $part = $resultParts[$idx];
            if ($idx > 0)
            {
                if (str_ends_with($result, "\n"))
                {
                    $result = $result . "  " . $part;
                }
                else
                {
                    if ($compactPipe)
                    {
                        $result = $result . "|" . $part;
                    }
                    else
                    {
                        $result = $result . " | " . $part;
                    }
                }
            }
            else
            {
                $result = $part;
            }
            $idx += 1;
        }
        return $result;
    }
    if ($node instanceof List_)
    {
        $hasHeredoc = false;
        foreach ($node->parts as $p)
        {
            if ($p->kind === "command" && $p->redirects !== null)
            {
                foreach ($p->redirects as $r)
                {
                    if ($r instanceof Heredoc)
                    {
                        $hasHeredoc = true;
                        break;
                    }
                }
            }
            else
            {
                if ($p instanceof Pipeline)
                {
                    foreach ($p->commands as $cmd)
                    {
                        if ($cmd->kind === "command" && $cmd->redirects !== null)
                        {
                            foreach ($cmd->redirects as $r)
                            {
                                if ($r instanceof Heredoc)
                                {
                                    $hasHeredoc = true;
                                    break;
                                }
                            }
                        }
                        if ($hasHeredoc)
                        {
                            break;
                        }
                    }
                }
            }
        }
        $result = [];
        $skippedSemi = false;
        $cmdCount = 0;
        foreach ($node->parts as $p)
        {
            if ($p instanceof Operator)
            {
                if ($p->op === ";")
                {
                    if ((count($result) > 0) && str_ends_with($result[count($result) - 1], "\n"))
                    {
                        $skippedSemi = true;
                        continue;
                    }
                    if (count($result) >= 3 && $result[count($result) - 2] === "\n" && str_ends_with($result[count($result) - 3], "\n"))
                    {
                        $skippedSemi = true;
                        continue;
                    }
                    array_push($result, ";");
                    $skippedSemi = false;
                }
                else
                {
                    if ($p->op === "\n")
                    {
                        if ((count($result) > 0) && $result[count($result) - 1] === ";")
                        {
                            $skippedSemi = false;
                            continue;
                        }
                        if ((count($result) > 0) && str_ends_with($result[count($result) - 1], "\n"))
                        {
                            array_push($result, ($skippedSemi ? " " : "\n"));
                            $skippedSemi = false;
                            continue;
                        }
                        array_push($result, "\n");
                        $skippedSemi = false;
                    }
                    else
                    {
                        $last = "";
                        $firstNl = 0;
                        if ($p->op === "&")
                        {
                            if ((count($result) > 0) && ((str_contains($result[count($result) - 1], "<<"))) && ((str_contains($result[count($result) - 1], "\n"))))
                            {
                                $last = $result[count($result) - 1];
                                if (((str_contains($last, " |"))) || str_starts_with($last, "|"))
                                {
                                    $result[count($result) - 1] = $last . " &";
                                }
                                else
                                {
                                    $firstNl = (mb_strpos($last, "\n") === false ? -1 : mb_strpos($last, "\n"));
                                    $result[count($result) - 1] = mb_substr($last, 0, $firstNl) . " &" . mb_substr($last, $firstNl);
                                }
                            }
                            else
                            {
                                array_push($result, " &");
                            }
                        }
                        else
                        {
                            if ((count($result) > 0) && ((str_contains($result[count($result) - 1], "<<"))) && ((str_contains($result[count($result) - 1], "\n"))))
                            {
                                $last = $result[count($result) - 1];
                                $firstNl = (mb_strpos($last, "\n") === false ? -1 : mb_strpos($last, "\n"));
                                $result[count($result) - 1] = mb_substr($last, 0, $firstNl) . " " . $p->op . " " . mb_substr($last, $firstNl);
                            }
                            else
                            {
                                array_push($result, " " . $p->op);
                            }
                        }
                    }
                }
            }
            else
            {
                if ((count($result) > 0) && !(str_ends_with($result[count($result) - 1], " ") || str_ends_with($result[count($result) - 1], "\n")))
                {
                    array_push($result, " ");
                }
                $formattedCmd = _formatCmdsubNode($p, $indent, $inProcsub, $compactRedirects, $procsubFirst && $cmdCount === 0);
                if (count($result) > 0)
                {
                    $last = $result[count($result) - 1];
                    if (((str_contains($last, " || \n"))) || ((str_contains($last, " && \n"))))
                    {
                        $formattedCmd = " " . $formattedCmd;
                    }
                }
                if ($skippedSemi)
                {
                    $formattedCmd = " " . $formattedCmd;
                    $skippedSemi = false;
                }
                array_push($result, $formattedCmd);
                $cmdCount += 1;
            }
        }
        $s = implode("", $result);
        if (((str_contains($s, " &\n"))) && str_ends_with($s, "\n"))
        {
            return $s . " ";
        }
        while (str_ends_with($s, ";"))
        {
            $s = _substring($s, 0, mb_strlen($s) - 1);
        }
        if (!$hasHeredoc)
        {
            while (str_ends_with($s, "\n"))
            {
                $s = _substring($s, 0, mb_strlen($s) - 1);
            }
        }
        return $s;
    }
    if ($node instanceof If_)
    {
        $cond = _formatCmdsubNode($node->condition, $indent, false, false, false);
        $thenBody = _formatCmdsubNode($node->thenBody, $indent + 4, false, false, false);
        $result = "if " . $cond . "; then\n" . $innerSp . $thenBody . ";";
        if ($node->elseBody !== null)
        {
            $elseBody = _formatCmdsubNode($node->elseBody, $indent + 4, false, false, false);
            $result = $result . "\n" . $sp . "else\n" . $innerSp . $elseBody . ";";
        }
        $result = $result . "\n" . $sp . "fi";
        return $result;
    }
    if ($node instanceof While_)
    {
        $cond = _formatCmdsubNode($node->condition, $indent, false, false, false);
        $body = _formatCmdsubNode($node->body, $indent + 4, false, false, false);
        $result = "while " . $cond . "; do\n" . $innerSp . $body . ";\n" . $sp . "done";
        if ((count($node->redirects) > 0))
        {
            foreach ($node->redirects as $r)
            {
                $result = $result . " " . _formatRedirect($r, false, false);
            }
        }
        return $result;
    }
    if ($node instanceof Until)
    {
        $cond = _formatCmdsubNode($node->condition, $indent, false, false, false);
        $body = _formatCmdsubNode($node->body, $indent + 4, false, false, false);
        $result = "until " . $cond . "; do\n" . $innerSp . $body . ";\n" . $sp . "done";
        if ((count($node->redirects) > 0))
        {
            foreach ($node->redirects as $r)
            {
                $result = $result . " " . _formatRedirect($r, false, false);
            }
        }
        return $result;
    }
    if ($node instanceof For_)
    {
        $var_ = $node->var_;
        $body = _formatCmdsubNode($node->body, $indent + 4, false, false, false);
        $result = "";
        if ($node->words !== null)
        {
            $wordVals = [];
            foreach ($node->words as $w)
            {
                array_push($wordVals, $w->value);
            }
            $words = implode(" ", $wordVals);
            if (($words !== ''))
            {
                $result = "for " . $var_ . " in " . $words . ";\n" . $sp . "do\n" . $innerSp . $body . ";\n" . $sp . "done";
            }
            else
            {
                $result = "for " . $var_ . " in ;\n" . $sp . "do\n" . $innerSp . $body . ";\n" . $sp . "done";
            }
        }
        else
        {
            $result = "for " . $var_ . " in \"\$@\";\n" . $sp . "do\n" . $innerSp . $body . ";\n" . $sp . "done";
        }
        if ((count($node->redirects) > 0))
        {
            foreach ($node->redirects as $r)
            {
                $result = $result . " " . _formatRedirect($r, false, false);
            }
        }
        return $result;
    }
    if ($node instanceof Forarith)
    {
        $body = _formatCmdsubNode($node->body, $indent + 4, false, false, false);
        $result = "for ((" . $node->init . "; " . $node->cond . "; " . $node->incr . "))\ndo\n" . $innerSp . $body . ";\n" . $sp . "done";
        if ((count($node->redirects) > 0))
        {
            foreach ($node->redirects as $r)
            {
                $result = $result . " " . _formatRedirect($r, false, false);
            }
        }
        return $result;
    }
    if ($node instanceof Case_)
    {
        $word = $node->word->value;
        $patterns = [];
        $i = 0;
        while ($i < count($node->patterns))
        {
            $p = $node->patterns[$i];
            $pat = str_replace("|", " | ", $p->pattern);
            $body = "";
            if ($p->body !== null)
            {
                $body = _formatCmdsubNode($p->body, $indent + 8, false, false, false);
            }
            else
            {
                $body = "";
            }
            $term = $p->terminator;
            $patIndent = _repeatStr(" ", $indent + 8);
            $termIndent = _repeatStr(" ", $indent + 4);
            $bodyPart = (($body !== '') ? $patIndent . $body . "\n" : "\n");
            if ($i === 0)
            {
                array_push($patterns, " " . $pat . ")\n" . $bodyPart . $termIndent . $term);
            }
            else
            {
                array_push($patterns, $pat . ")\n" . $bodyPart . $termIndent . $term);
            }
            $i += 1;
        }
        $patternStr = implode("\n" . _repeatStr(" ", $indent + 4), $patterns);
        $redirects = "";
        if ((count($node->redirects) > 0))
        {
            $redirectParts = [];
            foreach ($node->redirects as $r)
            {
                array_push($redirectParts, _formatRedirect($r, false, false));
            }
            $redirects = " " . implode(" ", $redirectParts);
        }
        return "case " . $word . " in" . $patternStr . "\n" . $sp . "esac" . $redirects;
    }
    if ($node instanceof Function_)
    {
        $name = $node->name;
        $innerBody = ($node->body->kind === "brace-group" ? $node->body->body : $node->body);
        $body = rtrim(_formatCmdsubNode($innerBody, $indent + 4, false, false, false), ";");
        return sprintf("function %s () \n{ \n%s%s\n}", $name, $innerSp, $body);
    }
    if ($node instanceof Subshell)
    {
        $body = _formatCmdsubNode($node->body, $indent, $inProcsub, $compactRedirects, false);
        $redirects = "";
        if ((count($node->redirects) > 0))
        {
            $redirectParts = [];
            foreach ($node->redirects as $r)
            {
                array_push($redirectParts, _formatRedirect($r, false, false));
            }
            $redirects = implode(" ", $redirectParts);
        }
        if ($procsubFirst)
        {
            if (($redirects !== ''))
            {
                return "(" . $body . ") " . $redirects;
            }
            return "(" . $body . ")";
        }
        if (($redirects !== ''))
        {
            return "( " . $body . " ) " . $redirects;
        }
        return "( " . $body . " )";
    }
    if ($node instanceof Bracegroup)
    {
        $body = _formatCmdsubNode($node->body, $indent, false, false, false);
        $body = rtrim($body, ";");
        $terminator = (str_ends_with($body, " &") ? " }" : "; }");
        $redirects = "";
        if ((count($node->redirects) > 0))
        {
            $redirectParts = [];
            foreach ($node->redirects as $r)
            {
                array_push($redirectParts, _formatRedirect($r, false, false));
            }
            $redirects = implode(" ", $redirectParts);
        }
        if (($redirects !== ''))
        {
            return "{ " . $body . $terminator . " " . $redirects;
        }
        return "{ " . $body . $terminator;
    }
    if ($node instanceof Arithmeticcommand)
    {
        return "((" . $node->rawContent . "))";
    }
    if ($node instanceof Conditionalexpr)
    {
        $body = _formatCondBody($node->body);
        return "[[ " . $body . " ]]";
    }
    if ($node instanceof Negation)
    {
        if ($node->pipeline !== null)
        {
            return "! " . _formatCmdsubNode($node->pipeline, $indent, false, false, false);
        }
        return "! ";
    }
    if ($node instanceof Time)
    {
        $prefix = ($node->posix ? "time -p " : "time ");
        if ($node->pipeline !== null)
        {
            return $prefix . _formatCmdsubNode($node->pipeline, $indent, false, false, false);
        }
        return $prefix;
    }
    return "";
}

function _formatRedirect(?Node $r, bool $compact, bool $heredocOpOnly): string
{
    $op = "";
    if ($r instanceof Heredoc)
    {
        if ($r->stripTabs)
        {
            $op = "<<-";
        }
        else
        {
            $op = "<<";
        }
        if ($r->fd !== null && $r->fd > 0)
        {
            $op = strval($r->fd) . $op;
        }
        $delim = "";
        if ($r->quoted)
        {
            $delim = "'" . $r->delimiter . "'";
        }
        else
        {
            $delim = $r->delimiter;
        }
        if ($heredocOpOnly)
        {
            return $op . $delim;
        }
        return $op . $delim . "\n" . $r->content . $r->delimiter . "\n";
    }
    $op = $r->op;
    if ($op === "1>")
    {
        $op = ">";
    }
    else
    {
        if ($op === "0<")
        {
            $op = "<";
        }
    }
    $target = $r->target->value;
    $target = $r->target->_expandAllAnsiCQuotes($target);
    $target = $r->target->_stripLocaleStringDollars($target);
    $target = $r->target->_formatCommandSubstitutions($target, false);
    if (str_starts_with($target, "&"))
    {
        $wasInputClose = false;
        if ($target === "&-" && str_ends_with($op, "<"))
        {
            $wasInputClose = true;
            $op = _substring($op, 0, mb_strlen($op) - 1) . ">";
        }
        $afterAmp = _substring($target, 1, count($target));
        $isLiteralFd = $afterAmp === "-" || mb_strlen($afterAmp) > 0 && ctype_digit((string)(mb_substr($afterAmp, 0, 1)));
        if ($isLiteralFd)
        {
            if ($op === ">" || $op === ">&")
            {
                $op = ($wasInputClose ? "0>" : "1>");
            }
            else
            {
                if ($op === "<" || $op === "<&")
                {
                    $op = "0<";
                }
            }
        }
        else
        {
            if ($op === "1>")
            {
                $op = ">";
            }
            else
            {
                if ($op === "0<")
                {
                    $op = "<";
                }
            }
        }
        return $op . $target;
    }
    if (str_ends_with($op, "&"))
    {
        return $op . $target;
    }
    if ($compact)
    {
        return $op . $target;
    }
    return $op . " " . $target;
}

function _formatHeredocBody(?Node $r): string
{
    return "\n" . $r->content . $r->delimiter . "\n";
}

function _lookaheadForEsac(string $value, int $start, int $caseDepth): bool
{
    $i = $start;
    $depth = $caseDepth;
    $quote = newQuoteState();
    while ($i < mb_strlen($value))
    {
        $c = (string)(mb_substr($value, $i, 1));
        if ($c === "\\" && $i + 1 < mb_strlen($value) && $quote->double)
        {
            $i += 2;
            continue;
        }
        if ($c === "'" && !$quote->double)
        {
            $quote->single = !$quote->single;
            $i += 1;
            continue;
        }
        if ($c === "\"" && !$quote->single)
        {
            $quote->double = !$quote->double;
            $i += 1;
            continue;
        }
        if ($quote->single || $quote->double)
        {
            $i += 1;
            continue;
        }
        if (_startsWithAt($value, $i, "case") && _isWordBoundary($value, $i, 4))
        {
            $depth += 1;
            $i += 4;
        }
        else
        {
            if (_startsWithAt($value, $i, "esac") && _isWordBoundary($value, $i, 4))
            {
                $depth -= 1;
                if ($depth === 0)
                {
                    return true;
                }
                $i += 4;
            }
            else
            {
                if ($c === "(")
                {
                    $i += 1;
                }
                else
                {
                    if ($c === ")")
                    {
                        if ($depth > 0)
                        {
                            $i += 1;
                        }
                        else
                        {
                            break;
                        }
                    }
                    else
                    {
                        $i += 1;
                    }
                }
            }
        }
    }
    return false;
}

function _skipBacktick(string $value, int $start): int
{
    $i = $start + 1;
    while ($i < mb_strlen($value) && (string)(mb_substr($value, $i, 1)) !== "`")
    {
        if ((string)(mb_substr($value, $i, 1)) === "\\" && $i + 1 < mb_strlen($value))
        {
            $i += 2;
        }
        else
        {
            $i += 1;
        }
    }
    if ($i < mb_strlen($value))
    {
        $i += 1;
    }
    return $i;
}

function _skipSingleQuoted(string $s, int $start): int
{
    $i = $start;
    while ($i < mb_strlen($s) && (string)(mb_substr($s, $i, 1)) !== "'")
    {
        $i += 1;
    }
    return ($i < mb_strlen($s) ? $i + 1 : $i);
}

function _skipDoubleQuoted(string $s, int $start): int
{
    $i = $start;
    $n = mb_strlen($s);
    $passNext = false;
    $backq = false;
    while ($i < $n)
    {
        $c = (string)(mb_substr($s, $i, 1));
        if ($passNext)
        {
            $passNext = false;
            $i += 1;
            continue;
        }
        if ($c === "\\")
        {
            $passNext = true;
            $i += 1;
            continue;
        }
        if ($backq)
        {
            if ($c === "`")
            {
                $backq = false;
            }
            $i += 1;
            continue;
        }
        if ($c === "`")
        {
            $backq = true;
            $i += 1;
            continue;
        }
        if ($c === "\$" && $i + 1 < $n)
        {
            if ((string)(mb_substr($s, $i + 1, 1)) === "(")
            {
                $i = _findCmdsubEnd($s, $i + 2);
                continue;
            }
            if ((string)(mb_substr($s, $i + 1, 1)) === "{")
            {
                $i = _findBracedParamEnd($s, $i + 2);
                continue;
            }
        }
        if ($c === "\"")
        {
            return $i + 1;
        }
        $i += 1;
    }
    return $i;
}

function _isValidArithmeticStart(string $value, int $start): bool
{
    $scanParen = 0;
    $scanI = $start + 3;
    while ($scanI < mb_strlen($value))
    {
        $scanC = (string)(mb_substr($value, $scanI, 1));
        if (_isExpansionStart($value, $scanI, "\$("))
        {
            $scanI = _findCmdsubEnd($value, $scanI + 2);
            continue;
        }
        if ($scanC === "(")
        {
            $scanParen += 1;
        }
        else
        {
            if ($scanC === ")")
            {
                if ($scanParen > 0)
                {
                    $scanParen -= 1;
                }
                else
                {
                    if ($scanI + 1 < mb_strlen($value) && (string)(mb_substr($value, $scanI + 1, 1)) === ")")
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
        $scanI += 1;
    }
    return false;
}

function _findFunsubEnd(string $value, int $start): int
{
    $depth = 1;
    $i = $start;
    $quote = newQuoteState();
    while ($i < mb_strlen($value) && $depth > 0)
    {
        $c = (string)(mb_substr($value, $i, 1));
        if ($c === "\\" && $i + 1 < mb_strlen($value) && !$quote->single)
        {
            $i += 2;
            continue;
        }
        if ($c === "'" && !$quote->double)
        {
            $quote->single = !$quote->single;
            $i += 1;
            continue;
        }
        if ($c === "\"" && !$quote->single)
        {
            $quote->double = !$quote->double;
            $i += 1;
            continue;
        }
        if ($quote->single || $quote->double)
        {
            $i += 1;
            continue;
        }
        if ($c === "{")
        {
            $depth += 1;
        }
        else
        {
            if ($c === "}")
            {
                $depth -= 1;
                if ($depth === 0)
                {
                    return $i + 1;
                }
            }
        }
        $i += 1;
    }
    return mb_strlen($value);
}

function _findCmdsubEnd(string $value, int $start): int
{
    $depth = 1;
    $i = $start;
    $caseDepth = 0;
    $inCasePatterns = false;
    $arithDepth = 0;
    $arithParenDepth = 0;
    while ($i < mb_strlen($value) && $depth > 0)
    {
        $c = (string)(mb_substr($value, $i, 1));
        if ($c === "\\" && $i + 1 < mb_strlen($value))
        {
            $i += 2;
            continue;
        }
        if ($c === "'")
        {
            $i = _skipSingleQuoted($value, $i + 1);
            continue;
        }
        if ($c === "\"")
        {
            $i = _skipDoubleQuoted($value, $i + 1);
            continue;
        }
        if ($c === "#" && $arithDepth === 0 && ($i === $start || (string)(mb_substr($value, $i - 1, 1)) === " " || (string)(mb_substr($value, $i - 1, 1)) === "\t" || (string)(mb_substr($value, $i - 1, 1)) === "\n" || (string)(mb_substr($value, $i - 1, 1)) === ";" || (string)(mb_substr($value, $i - 1, 1)) === "|" || (string)(mb_substr($value, $i - 1, 1)) === "&" || (string)(mb_substr($value, $i - 1, 1)) === "(" || (string)(mb_substr($value, $i - 1, 1)) === ")"))
        {
            while ($i < mb_strlen($value) && (string)(mb_substr($value, $i, 1)) !== "\n")
            {
                $i += 1;
            }
            continue;
        }
        if (_startsWithAt($value, $i, "<<<"))
        {
            $i += 3;
            while ($i < mb_strlen($value) && ((string)(mb_substr($value, $i, 1)) === " " || (string)(mb_substr($value, $i, 1)) === "\t"))
            {
                $i += 1;
            }
            if ($i < mb_strlen($value) && (string)(mb_substr($value, $i, 1)) === "\"")
            {
                $i += 1;
                while ($i < mb_strlen($value) && (string)(mb_substr($value, $i, 1)) !== "\"")
                {
                    if ((string)(mb_substr($value, $i, 1)) === "\\" && $i + 1 < mb_strlen($value))
                    {
                        $i += 2;
                    }
                    else
                    {
                        $i += 1;
                    }
                }
                if ($i < mb_strlen($value))
                {
                    $i += 1;
                }
            }
            else
            {
                if ($i < mb_strlen($value) && (string)(mb_substr($value, $i, 1)) === "'")
                {
                    $i += 1;
                    while ($i < mb_strlen($value) && (string)(mb_substr($value, $i, 1)) !== "'")
                    {
                        $i += 1;
                    }
                    if ($i < mb_strlen($value))
                    {
                        $i += 1;
                    }
                }
                else
                {
                    while ($i < mb_strlen($value) && ((!str_contains(" \t\n;|&<>()", (string)(mb_substr($value, $i, 1))))))
                    {
                        $i += 1;
                    }
                }
            }
            continue;
        }
        if (_isExpansionStart($value, $i, "\$(("))
        {
            if (_isValidArithmeticStart($value, $i))
            {
                $arithDepth += 1;
                $i += 3;
                continue;
            }
            $j = _findCmdsubEnd($value, $i + 2);
            $i = $j;
            continue;
        }
        if ($arithDepth > 0 && $arithParenDepth === 0 && _startsWithAt($value, $i, "))"))
        {
            $arithDepth -= 1;
            $i += 2;
            continue;
        }
        if ($c === "`")
        {
            $i = _skipBacktick($value, $i);
            continue;
        }
        if ($arithDepth === 0 && _startsWithAt($value, $i, "<<"))
        {
            $i = _skipHeredoc($value, $i);
            continue;
        }
        if (_startsWithAt($value, $i, "case") && _isWordBoundary($value, $i, 4))
        {
            $caseDepth += 1;
            $inCasePatterns = false;
            $i += 4;
            continue;
        }
        if ($caseDepth > 0 && _startsWithAt($value, $i, "in") && _isWordBoundary($value, $i, 2))
        {
            $inCasePatterns = true;
            $i += 2;
            continue;
        }
        if (_startsWithAt($value, $i, "esac") && _isWordBoundary($value, $i, 4))
        {
            if ($caseDepth > 0)
            {
                $caseDepth -= 1;
                $inCasePatterns = false;
            }
            $i += 4;
            continue;
        }
        if (_startsWithAt($value, $i, ";;"))
        {
            $i += 2;
            continue;
        }
        if ($c === "(")
        {
            if (!($inCasePatterns && $caseDepth > 0))
            {
                if ($arithDepth > 0)
                {
                    $arithParenDepth += 1;
                }
                else
                {
                    $depth += 1;
                }
            }
        }
        else
        {
            if ($c === ")")
            {
                if ($inCasePatterns && $caseDepth > 0)
                {
                    if (!_lookaheadForEsac($value, $i + 1, $caseDepth))
                    {
                        $depth -= 1;
                    }
                }
                else
                {
                    if ($arithDepth > 0)
                    {
                        if ($arithParenDepth > 0)
                        {
                            $arithParenDepth -= 1;
                        }
                    }
                    else
                    {
                        $depth -= 1;
                    }
                }
            }
        }
        $i += 1;
    }
    return $i;
}

function _findBracedParamEnd(string $value, int $start): int
{
    $depth = 1;
    $i = $start;
    $inDouble = false;
    $dolbraceState = DOLBRACESTATE_PARAM;
    while ($i < mb_strlen($value) && $depth > 0)
    {
        $c = (string)(mb_substr($value, $i, 1));
        if ($c === "\\" && $i + 1 < mb_strlen($value))
        {
            $i += 2;
            continue;
        }
        if ($c === "'" && $dolbraceState === DOLBRACESTATE_QUOTE && !$inDouble)
        {
            $i = _skipSingleQuoted($value, $i + 1);
            continue;
        }
        if ($c === "\"")
        {
            $inDouble = !$inDouble;
            $i += 1;
            continue;
        }
        if ($inDouble)
        {
            $i += 1;
            continue;
        }
        if ($dolbraceState === DOLBRACESTATE_PARAM && ((str_contains("%#^,", $c))))
        {
            $dolbraceState = DOLBRACESTATE_QUOTE;
        }
        else
        {
            if ($dolbraceState === DOLBRACESTATE_PARAM && ((str_contains(":-=?+/", $c))))
            {
                $dolbraceState = DOLBRACESTATE_WORD;
            }
        }
        if ($c === "[" && $dolbraceState === DOLBRACESTATE_PARAM && !$inDouble)
        {
            $end = _skipSubscript($value, $i, 0);
            if ($end !== -1)
            {
                $i = $end;
                continue;
            }
        }
        if (($c === "<" || $c === ">") && $i + 1 < mb_strlen($value) && (string)(mb_substr($value, $i + 1, 1)) === "(")
        {
            $i = _findCmdsubEnd($value, $i + 2);
            continue;
        }
        if ($c === "{")
        {
            $depth += 1;
        }
        else
        {
            if ($c === "}")
            {
                $depth -= 1;
                if ($depth === 0)
                {
                    return $i + 1;
                }
            }
        }
        if (_isExpansionStart($value, $i, "\$("))
        {
            $i = _findCmdsubEnd($value, $i + 2);
            continue;
        }
        if (_isExpansionStart($value, $i, "\${"))
        {
            $i = _findBracedParamEnd($value, $i + 2);
            continue;
        }
        $i += 1;
    }
    return $i;
}

function _skipHeredoc(string $value, int $start): int
{
    $i = $start + 2;
    if ($i < mb_strlen($value) && (string)(mb_substr($value, $i, 1)) === "-")
    {
        $i += 1;
    }
    while ($i < mb_strlen($value) && _isWhitespaceNoNewline((string)(mb_substr($value, $i, 1))))
    {
        $i += 1;
    }
    $delimStart = $i;
    $quoteChar = null;
    $delimiter = "";
    if ($i < mb_strlen($value) && ((string)(mb_substr($value, $i, 1)) === "\"" || (string)(mb_substr($value, $i, 1)) === "'"))
    {
        $quoteChar = (string)(mb_substr($value, $i, 1));
        $i += 1;
        $delimStart = $i;
        while ($i < mb_strlen($value) && (string)(mb_substr($value, $i, 1)) !== $quoteChar)
        {
            $i += 1;
        }
        $delimiter = _substring($value, $delimStart, $i);
        if ($i < mb_strlen($value))
        {
            $i += 1;
        }
    }
    else
    {
        if ($i < mb_strlen($value) && (string)(mb_substr($value, $i, 1)) === "\\")
        {
            $i += 1;
            $delimStart = $i;
            if ($i < mb_strlen($value))
            {
                $i += 1;
            }
            while ($i < mb_strlen($value) && !_isMetachar((string)(mb_substr($value, $i, 1))))
            {
                $i += 1;
            }
            $delimiter = _substring($value, $delimStart, $i);
        }
        else
        {
            while ($i < mb_strlen($value) && !_isMetachar((string)(mb_substr($value, $i, 1))))
            {
                $i += 1;
            }
            $delimiter = _substring($value, $delimStart, $i);
        }
    }
    $parenDepth = 0;
    $quote = newQuoteState();
    $inBacktick = false;
    while ($i < mb_strlen($value) && (string)(mb_substr($value, $i, 1)) !== "\n")
    {
        $c = (string)(mb_substr($value, $i, 1));
        if ($c === "\\" && $i + 1 < mb_strlen($value) && ($quote->double || $inBacktick))
        {
            $i += 2;
            continue;
        }
        if ($c === "'" && !$quote->double && !$inBacktick)
        {
            $quote->single = !$quote->single;
            $i += 1;
            continue;
        }
        if ($c === "\"" && !$quote->single && !$inBacktick)
        {
            $quote->double = !$quote->double;
            $i += 1;
            continue;
        }
        if ($c === "`" && !$quote->single)
        {
            $inBacktick = !$inBacktick;
            $i += 1;
            continue;
        }
        if ($quote->single || $quote->double || $inBacktick)
        {
            $i += 1;
            continue;
        }
        if ($c === "(")
        {
            $parenDepth += 1;
        }
        else
        {
            if ($c === ")")
            {
                if ($parenDepth === 0)
                {
                    break;
                }
                $parenDepth -= 1;
            }
        }
        $i += 1;
    }
    if ($i < mb_strlen($value) && (string)(mb_substr($value, $i, 1)) === ")")
    {
        return $i;
    }
    if ($i < mb_strlen($value) && (string)(mb_substr($value, $i, 1)) === "\n")
    {
        $i += 1;
    }
    while ($i < mb_strlen($value))
    {
        $lineStart = $i;
        $lineEnd = $i;
        while ($lineEnd < mb_strlen($value) && (string)(mb_substr($value, $lineEnd, 1)) !== "\n")
        {
            $lineEnd += 1;
        }
        $line = _substring($value, $lineStart, $lineEnd);
        while ($lineEnd < mb_strlen($value))
        {
            $trailingBs = 0;
            for ($j = mb_strlen($line) - 1; $j > -1; $j += -1)
            {
                if ((string)(mb_substr($line, $j, 1)) === "\\")
                {
                    $trailingBs += 1;
                }
                else
                {
                    break;
                }
            }
            if ($trailingBs % 2 === 0)
            {
                break;
            }
            $line = mb_substr($line, 0, mb_strlen($line) - 1);
            $lineEnd += 1;
            $nextLineStart = $lineEnd;
            while ($lineEnd < mb_strlen($value) && (string)(mb_substr($value, $lineEnd, 1)) !== "\n")
            {
                $lineEnd += 1;
            }
            $line = $line . _substring($value, $nextLineStart, $lineEnd);
        }
        $stripped = "";
        if ($start + 2 < mb_strlen($value) && (string)(mb_substr($value, $start + 2, 1)) === "-")
        {
            $stripped = ltrim($line, "\t");
        }
        else
        {
            $stripped = $line;
        }
        if ($stripped === $delimiter)
        {
            if ($lineEnd < mb_strlen($value))
            {
                return $lineEnd + 1;
            }
            else
            {
                return $lineEnd;
            }
        }
        if (str_starts_with($stripped, $delimiter) && mb_strlen($stripped) > mb_strlen($delimiter))
        {
            $tabsStripped = mb_strlen($line) - mb_strlen($stripped);
            return $lineStart + $tabsStripped + mb_strlen($delimiter);
        }
        if ($lineEnd < mb_strlen($value))
        {
            $i = $lineEnd + 1;
        }
        else
        {
            $i = $lineEnd;
        }
    }
    return $i;
}

function _findHeredocContentEnd(string $source, int $start, ?array $delimiters): array
{
    if (!(count($delimiters) > 0))
    {
        return [$start, $start];
    }
    $pos = $start;
    while ($pos < mb_strlen($source) && (string)(mb_substr($source, $pos, 1)) !== "\n")
    {
        $pos += 1;
    }
    if ($pos >= mb_strlen($source))
    {
        return [$start, $start];
    }
    $contentStart = $pos;
    $pos += 1;
    foreach ($delimiters as $_item)
    {
        $delimiter = $_item[0];
        $stripTabs = $_item[1];
        while ($pos < mb_strlen($source))
        {
            $lineStart = $pos;
            $lineEnd = $pos;
            while ($lineEnd < mb_strlen($source) && (string)(mb_substr($source, $lineEnd, 1)) !== "\n")
            {
                $lineEnd += 1;
            }
            $line = _substring($source, $lineStart, $lineEnd);
            while ($lineEnd < mb_strlen($source))
            {
                $trailingBs = 0;
                for ($j = mb_strlen($line) - 1; $j > -1; $j += -1)
                {
                    if ((string)(mb_substr($line, $j, 1)) === "\\")
                    {
                        $trailingBs += 1;
                    }
                    else
                    {
                        break;
                    }
                }
                if ($trailingBs % 2 === 0)
                {
                    break;
                }
                $line = mb_substr($line, 0, mb_strlen($line) - 1);
                $lineEnd += 1;
                $nextLineStart = $lineEnd;
                while ($lineEnd < mb_strlen($source) && (string)(mb_substr($source, $lineEnd, 1)) !== "\n")
                {
                    $lineEnd += 1;
                }
                $line = $line . _substring($source, $nextLineStart, $lineEnd);
            }
            $lineStripped = "";
            if ($stripTabs)
            {
                $lineStripped = ltrim($line, "\t");
            }
            else
            {
                $lineStripped = $line;
            }
            if ($lineStripped === $delimiter)
            {
                $pos = ($lineEnd < mb_strlen($source) ? $lineEnd + 1 : $lineEnd);
                break;
            }
            if (str_starts_with($lineStripped, $delimiter) && mb_strlen($lineStripped) > mb_strlen($delimiter))
            {
                $tabsStripped = mb_strlen($line) - mb_strlen($lineStripped);
                $pos = $lineStart + $tabsStripped + mb_strlen($delimiter);
                break;
            }
            $pos = ($lineEnd < mb_strlen($source) ? $lineEnd + 1 : $lineEnd);
        }
    }
    return [$contentStart, $pos];
}

function _isWordBoundary(string $s, int $pos, int $wordLen): bool
{
    if ($pos > 0)
    {
        $prev = (string)(mb_substr($s, $pos - 1, 1));
        if (ctype_alnum($prev) || $prev === "_")
        {
            return false;
        }
        if ((str_contains("{}!", $prev)))
        {
            return false;
        }
    }
    $end = $pos + $wordLen;
    if ($end < mb_strlen($s) && (ctype_alnum((string)(mb_substr($s, $end, 1))) || (string)(mb_substr($s, $end, 1)) === "_"))
    {
        return false;
    }
    return true;
}

function _isQuote(string $c): bool
{
    return $c === "'" || $c === "\"";
}

function _collapseWhitespace(string $s): string
{
    $result = [];
    $prevWasWs = false;
    foreach (mb_str_split($s) as $c)
    {
        if ($c === " " || $c === "\t")
        {
            if (!$prevWasWs)
            {
                array_push($result, " ");
            }
            $prevWasWs = true;
        }
        else
        {
            array_push($result, $c);
            $prevWasWs = false;
        }
    }
    $joined = implode("", $result);
    return trim($joined, " \t");
}

function _countTrailingBackslashes(string $s): int
{
    $count = 0;
    for ($i = mb_strlen($s) - 1; $i > -1; $i += -1)
    {
        if ((string)(mb_substr($s, $i, 1)) === "\\")
        {
            $count += 1;
        }
        else
        {
            break;
        }
    }
    return $count;
}

function _normalizeHeredocDelimiter(string $delimiter): string
{
    $result = [];
    $i = 0;
    while ($i < mb_strlen($delimiter))
    {
        $depth = 0;
        $inner = [];
        $innerStr = "";
        if ($i + 1 < mb_strlen($delimiter) && mb_substr($delimiter, $i, ($i + 2) - ($i)) === "\$(")
        {
            array_push($result, "\$(");
            $i += 2;
            $depth = 1;
            $inner = [];
            while ($i < mb_strlen($delimiter) && $depth > 0)
            {
                if ((string)(mb_substr($delimiter, $i, 1)) === "(")
                {
                    $depth += 1;
                    array_push($inner, (string)(mb_substr($delimiter, $i, 1)));
                }
                else
                {
                    if ((string)(mb_substr($delimiter, $i, 1)) === ")")
                    {
                        $depth -= 1;
                        if ($depth === 0)
                        {
                            $innerStr = implode("", $inner);
                            $innerStr = _collapseWhitespace($innerStr);
                            array_push($result, $innerStr);
                            array_push($result, ")");
                        }
                        else
                        {
                            array_push($inner, (string)(mb_substr($delimiter, $i, 1)));
                        }
                    }
                    else
                    {
                        array_push($inner, (string)(mb_substr($delimiter, $i, 1)));
                    }
                }
                $i += 1;
            }
        }
        else
        {
            if ($i + 1 < mb_strlen($delimiter) && mb_substr($delimiter, $i, ($i + 2) - ($i)) === "\${")
            {
                array_push($result, "\${");
                $i += 2;
                $depth = 1;
                $inner = [];
                while ($i < mb_strlen($delimiter) && $depth > 0)
                {
                    if ((string)(mb_substr($delimiter, $i, 1)) === "{")
                    {
                        $depth += 1;
                        array_push($inner, (string)(mb_substr($delimiter, $i, 1)));
                    }
                    else
                    {
                        if ((string)(mb_substr($delimiter, $i, 1)) === "}")
                        {
                            $depth -= 1;
                            if ($depth === 0)
                            {
                                $innerStr = implode("", $inner);
                                $innerStr = _collapseWhitespace($innerStr);
                                array_push($result, $innerStr);
                                array_push($result, "}");
                            }
                            else
                            {
                                array_push($inner, (string)(mb_substr($delimiter, $i, 1)));
                            }
                        }
                        else
                        {
                            array_push($inner, (string)(mb_substr($delimiter, $i, 1)));
                        }
                    }
                    $i += 1;
                }
            }
            else
            {
                if ($i + 1 < mb_strlen($delimiter) && ((str_contains("<>", (string)(mb_substr($delimiter, $i, 1))))) && (string)(mb_substr($delimiter, $i + 1, 1)) === "(")
                {
                    array_push($result, (string)(mb_substr($delimiter, $i, 1)));
                    array_push($result, "(");
                    $i += 2;
                    $depth = 1;
                    $inner = [];
                    while ($i < mb_strlen($delimiter) && $depth > 0)
                    {
                        if ((string)(mb_substr($delimiter, $i, 1)) === "(")
                        {
                            $depth += 1;
                            array_push($inner, (string)(mb_substr($delimiter, $i, 1)));
                        }
                        else
                        {
                            if ((string)(mb_substr($delimiter, $i, 1)) === ")")
                            {
                                $depth -= 1;
                                if ($depth === 0)
                                {
                                    $innerStr = implode("", $inner);
                                    $innerStr = _collapseWhitespace($innerStr);
                                    array_push($result, $innerStr);
                                    array_push($result, ")");
                                }
                                else
                                {
                                    array_push($inner, (string)(mb_substr($delimiter, $i, 1)));
                                }
                            }
                            else
                            {
                                array_push($inner, (string)(mb_substr($delimiter, $i, 1)));
                            }
                        }
                        $i += 1;
                    }
                }
                else
                {
                    array_push($result, (string)(mb_substr($delimiter, $i, 1)));
                    $i += 1;
                }
            }
        }
    }
    return implode("", $result);
}

function _isMetachar(string $c): bool
{
    return $c === " " || $c === "\t" || $c === "\n" || $c === "|" || $c === "&" || $c === ";" || $c === "(" || $c === ")" || $c === "<" || $c === ">";
}

function _isFunsubChar(string $c): bool
{
    return $c === " " || $c === "\t" || $c === "\n" || $c === "|";
}

function _isExtglobPrefix(string $c): bool
{
    return $c === "@" || $c === "?" || $c === "*" || $c === "+" || $c === "!";
}

function _isRedirectChar(string $c): bool
{
    return $c === "<" || $c === ">";
}

function _isSpecialParam(string $c): bool
{
    return $c === "?" || $c === "\$" || $c === "!" || $c === "#" || $c === "@" || $c === "*" || $c === "-" || $c === "&";
}

function _isSpecialParamUnbraced(string $c): bool
{
    return $c === "?" || $c === "\$" || $c === "!" || $c === "#" || $c === "@" || $c === "*" || $c === "-";
}

function _isDigit(string $c): bool
{
    return $c >= "0" && $c <= "9";
}

function _isSemicolonOrNewline(string $c): bool
{
    return $c === ";" || $c === "\n";
}

function _isWordEndContext(string $c): bool
{
    return $c === " " || $c === "\t" || $c === "\n" || $c === ";" || $c === "|" || $c === "&" || $c === "<" || $c === ">" || $c === "(" || $c === ")";
}

function _skipMatchedPair(string $s, int $start, string $open, string $close, int $flags): int
{
    $n = mb_strlen($s);
    $i = 0;
    if ((($flags & SMP_PAST_OPEN) !== 0))
    {
        $i = $start;
    }
    else
    {
        if ($start >= $n || (string)(mb_substr($s, $start, 1)) !== $open)
        {
            return -1;
        }
        $i = $start + 1;
    }
    $depth = 1;
    $passNext = false;
    $backq = false;
    while ($i < $n && $depth > 0)
    {
        $c = (string)(mb_substr($s, $i, 1));
        if ($passNext)
        {
            $passNext = false;
            $i += 1;
            continue;
        }
        $literal = ($flags & SMP_LITERAL);
        if (!($literal !== 0) && $c === "\\")
        {
            $passNext = true;
            $i += 1;
            continue;
        }
        if ($backq)
        {
            if ($c === "`")
            {
                $backq = false;
            }
            $i += 1;
            continue;
        }
        if (!($literal !== 0) && $c === "`")
        {
            $backq = true;
            $i += 1;
            continue;
        }
        if (!($literal !== 0) && $c === "'")
        {
            $i = _skipSingleQuoted($s, $i + 1);
            continue;
        }
        if (!($literal !== 0) && $c === "\"")
        {
            $i = _skipDoubleQuoted($s, $i + 1);
            continue;
        }
        if (!($literal !== 0) && _isExpansionStart($s, $i, "\$("))
        {
            $i = _findCmdsubEnd($s, $i + 2);
            continue;
        }
        if (!($literal !== 0) && _isExpansionStart($s, $i, "\${"))
        {
            $i = _findBracedParamEnd($s, $i + 2);
            continue;
        }
        if (!($literal !== 0) && $c === $open)
        {
            $depth += 1;
        }
        else
        {
            if ($c === $close)
            {
                $depth -= 1;
            }
        }
        $i += 1;
    }
    return ($depth === 0 ? $i : -1);
}

function _skipSubscript(string $s, int $start, int $flags): int
{
    return _skipMatchedPair($s, $start, "[", "]", $flags);
}

function _assignment(string $s, int $flags): int
{
    if (!($s !== ''))
    {
        return -1;
    }
    if (!(ctype_alpha((string)(mb_substr($s, 0, 1))) || (string)(mb_substr($s, 0, 1)) === "_"))
    {
        return -1;
    }
    $i = 1;
    while ($i < mb_strlen($s))
    {
        $c = (string)(mb_substr($s, $i, 1));
        if ($c === "=")
        {
            return $i;
        }
        if ($c === "[")
        {
            $subFlags = ((($flags & 2) !== 0) ? SMP_LITERAL : 0);
            $end = _skipSubscript($s, $i, $subFlags);
            if ($end === -1)
            {
                return -1;
            }
            $i = $end;
            if ($i < mb_strlen($s) && (string)(mb_substr($s, $i, 1)) === "+")
            {
                $i += 1;
            }
            if ($i < mb_strlen($s) && (string)(mb_substr($s, $i, 1)) === "=")
            {
                return $i;
            }
            return -1;
        }
        if ($c === "+")
        {
            if ($i + 1 < mb_strlen($s) && (string)(mb_substr($s, $i + 1, 1)) === "=")
            {
                return $i + 1;
            }
            return -1;
        }
        if (!(ctype_alnum($c) || $c === "_"))
        {
            return -1;
        }
        $i += 1;
    }
    return -1;
}

function _isArrayAssignmentPrefix(?array $chars): bool
{
    if (!(count($chars) > 0))
    {
        return false;
    }
    if (!(ctype_alpha($chars[0]) || $chars[0] === "_"))
    {
        return false;
    }
    $s = implode("", $chars);
    $i = 1;
    while ($i < mb_strlen($s) && (ctype_alnum((string)(mb_substr($s, $i, 1))) || (string)(mb_substr($s, $i, 1)) === "_"))
    {
        $i += 1;
    }
    while ($i < mb_strlen($s))
    {
        if ((string)(mb_substr($s, $i, 1)) !== "[")
        {
            return false;
        }
        $end = _skipSubscript($s, $i, SMP_LITERAL);
        if ($end === -1)
        {
            return false;
        }
        $i = $end;
    }
    return true;
}

function _isSpecialParamOrDigit(string $c): bool
{
    return _isSpecialParam($c) || _isDigit($c);
}

function _isParamExpansionOp(string $c): bool
{
    return $c === ":" || $c === "-" || $c === "=" || $c === "+" || $c === "?" || $c === "#" || $c === "%" || $c === "/" || $c === "^" || $c === "," || $c === "@" || $c === "*" || $c === "[";
}

function _isSimpleParamOp(string $c): bool
{
    return $c === "-" || $c === "=" || $c === "?" || $c === "+";
}

function _isEscapeCharInBacktick(string $c): bool
{
    return $c === "\$" || $c === "`" || $c === "\\";
}

function _isNegationBoundary(string $c): bool
{
    return _isWhitespace($c) || $c === ";" || $c === "|" || $c === ")" || $c === "&" || $c === ">" || $c === "<";
}

function _isBackslashEscaped(string $value, int $idx): bool
{
    $bsCount = 0;
    $j = $idx - 1;
    while ($j >= 0 && (string)(mb_substr($value, $j, 1)) === "\\")
    {
        $bsCount += 1;
        $j -= 1;
    }
    return $bsCount % 2 === 1;
}

function _isDollarDollarParen(string $value, int $idx): bool
{
    $dollarCount = 0;
    $j = $idx - 1;
    while ($j >= 0 && (string)(mb_substr($value, $j, 1)) === "\$")
    {
        $dollarCount += 1;
        $j -= 1;
    }
    return $dollarCount % 2 === 1;
}

function _isParen(string $c): bool
{
    return $c === "(" || $c === ")";
}

function _isCaretOrBang(string $c): bool
{
    return $c === "!" || $c === "^";
}

function _isAtOrStar(string $c): bool
{
    return $c === "@" || $c === "*";
}

function _isDigitOrDash(string $c): bool
{
    return _isDigit($c) || $c === "-";
}

function _isNewlineOrRightParen(string $c): bool
{
    return $c === "\n" || $c === ")";
}

function _isSemicolonNewlineBrace(string $c): bool
{
    return $c === ";" || $c === "\n" || $c === "{";
}

function _looksLikeAssignment(string $s): bool
{
    return _assignment($s, 0) !== -1;
}

function _isValidIdentifier(string $name): bool
{
    if (!($name !== ''))
    {
        return false;
    }
    if (!(ctype_alpha((string)(mb_substr($name, 0, 1))) || (string)(mb_substr($name, 0, 1)) === "_"))
    {
        return false;
    }
    foreach (mb_str_split(mb_substr($name, 1)) as $c)
    {
        if (!(ctype_alnum($c) || $c === "_"))
        {
            return false;
        }
    }
    return true;
}

function parse(string $source, bool $extglob): ?array
{
    $parser = newParser($source, false, $extglob);
    return $parser->parse();
}

function newParseError(string $message, int $pos, int $line): ?Parseerror_
{
    $self = new Parseerror_("", 0, 0);
    $self->message = $message;
    $self->pos = $pos;
    $self->line = $line;
    return $self;
}

function newMatchedPairError(string $message, int $pos, int $line): ?Matchedpairerror
{
    return new Matchedpairerror();
}

function newQuoteState(): ?Quotestate
{
    $self = new Quotestate(false, false, []);
    $self->single = false;
    $self->double = false;
    $self->_stack = [];
    return $self;
}

function newParseContext(int $kind): ?Parsecontext
{
    $self = new Parsecontext(0, 0, 0, 0, 0, 0, 0, null);
    $self->kind = $kind;
    $self->parenDepth = 0;
    $self->braceDepth = 0;
    $self->bracketDepth = 0;
    $self->caseDepth = 0;
    $self->arithDepth = 0;
    $self->arithParenDepth = 0;
    $self->quote = newQuoteState();
    return $self;
}

function newContextStack(): ?Contextstack
{
    $self = new Contextstack([]);
    $self->_stack = [newParseContext(0)];
    return $self;
}

function newLexer(string $source, bool $extglob): ?Lexer
{
    $self = new Lexer([], "", 0, 0, null, 0, 0, [], false, "", 0, false, false, false, 0, 0, false, false, false, null, null, null);
    $self->source = $source;
    $self->pos = 0;
    $self->length = mb_strlen($source);
    $self->quote = newQuoteState();
    $self->_tokenCache = null;
    $self->_parserState = PARSERSTATEFLAGS_NONE;
    $self->_dolbraceState = DOLBRACESTATE_NONE;
    $self->_pendingHeredocs = [];
    $self->_extglob = $extglob;
    $self->_parser = null;
    $self->_eofToken = "";
    $self->_lastReadToken = null;
    $self->_wordContext = WORD_CTX_NORMAL;
    $self->_atCommandStart = false;
    $self->_inArrayLiteral = false;
    $self->_inAssignBuiltin = false;
    $self->_postReadPos = 0;
    $self->_cachedWordContext = WORD_CTX_NORMAL;
    $self->_cachedAtCommandStart = false;
    $self->_cachedInArrayLiteral = false;
    $self->_cachedInAssignBuiltin = false;
    return $self;
}

function newParser(string $source, bool $inProcessSub, bool $extglob): ?Parser
{
    $self = new Parser("", 0, 0, [], 0, false, false, false, null, null, [], 0, 0, "", 0, false, false, false, "", 0, 0);
    $self->source = $source;
    $self->pos = 0;
    $self->length = mb_strlen($source);
    $self->_pendingHeredocs = [];
    $self->_cmdsubHeredocEnd = -1;
    $self->_sawNewlineInSingleQuote = false;
    $self->_inProcessSub = $inProcessSub;
    $self->_extglob = $extglob;
    $self->_ctx = newContextStack();
    $self->_lexer = newLexer($source, $extglob);
    $self->_lexer->_parser = $self;
    $self->_tokenHistory = [null, null, null, null];
    $self->_parserState = PARSERSTATEFLAGS_NONE;
    $self->_dolbraceState = DOLBRACESTATE_NONE;
    $self->_eofToken = "";
    $self->_wordContext = WORD_CTX_NORMAL;
    $self->_atCommandStart = false;
    $self->_inArrayLiteral = false;
    $self->_inAssignBuiltin = false;
    $self->_arithSrc = "";
    $self->_arithPos = 0;
    $self->_arithLen = 0;
    return $self;
}

