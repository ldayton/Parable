function range(start, end, step) {
  if (end === undefined) { end = start; start = 0; }
  if (step === undefined) { step = 1; }
  const result = [];
  if (step > 0) {
    for (var i = start; i < end; i += step) result.push(i);
  } else {
    for (var i = start; i > end; i += step) result.push(i);
  }
  return result;
}
const ANSI_C_ESCAPES = new Map([["a", 7], ["b", 8], ["e", 27], ["E", 27], ["f", 12], ["n", 10], ["r", 13], ["t", 9], ["v", 11], ["\\", 92], ["\"", 34], ["?", 63]]);
const TokenType_EOF = 0;
const TokenType_WORD = 1;
const TokenType_NEWLINE = 2;
const TokenType_SEMI = 10;
const TokenType_PIPE = 11;
const TokenType_AMP = 12;
const TokenType_LPAREN = 13;
const TokenType_RPAREN = 14;
const TokenType_LBRACE = 15;
const TokenType_RBRACE = 16;
const TokenType_LESS = 17;
const TokenType_GREATER = 18;
const TokenType_AND_AND = 30;
const TokenType_OR_OR = 31;
const TokenType_SEMI_SEMI = 32;
const TokenType_SEMI_AMP = 33;
const TokenType_SEMI_SEMI_AMP = 34;
const TokenType_LESS_LESS = 35;
const TokenType_GREATER_GREATER = 36;
const TokenType_LESS_AMP = 37;
const TokenType_GREATER_AMP = 38;
const TokenType_LESS_GREATER = 39;
const TokenType_GREATER_PIPE = 40;
const TokenType_LESS_LESS_MINUS = 41;
const TokenType_LESS_LESS_LESS = 42;
const TokenType_AMP_GREATER = 43;
const TokenType_AMP_GREATER_GREATER = 44;
const TokenType_PIPE_AMP = 45;
const TokenType_IF = 50;
const TokenType_THEN = 51;
const TokenType_ELSE = 52;
const TokenType_ELIF = 53;
const TokenType_FI = 54;
const TokenType_CASE = 55;
const TokenType_ESAC = 56;
const TokenType_FOR = 57;
const TokenType_WHILE = 58;
const TokenType_UNTIL = 59;
const TokenType_DO = 60;
const TokenType_DONE = 61;
const TokenType_IN = 62;
const TokenType_FUNCTION = 63;
const TokenType_SELECT = 64;
const TokenType_COPROC = 65;
const TokenType_TIME = 66;
const TokenType_BANG = 67;
const TokenType_LBRACKET_LBRACKET = 68;
const TokenType_RBRACKET_RBRACKET = 69;
const TokenType_ASSIGNMENT_WORD = 80;
const TokenType_NUMBER = 81;
const ParserStateFlags_NONE = 0;
const ParserStateFlags_PST_CASEPAT = 1;
const ParserStateFlags_PST_CMDSUBST = 2;
const ParserStateFlags_PST_CASESTMT = 4;
const ParserStateFlags_PST_CONDEXPR = 8;
const ParserStateFlags_PST_COMPASSIGN = 16;
const ParserStateFlags_PST_ARITH = 32;
const ParserStateFlags_PST_HEREDOC = 64;
const ParserStateFlags_PST_REGEXP = 128;
const ParserStateFlags_PST_EXTPAT = 256;
const ParserStateFlags_PST_SUBSHELL = 512;
const ParserStateFlags_PST_REDIRLIST = 1024;
const ParserStateFlags_PST_COMMENT = 2048;
const ParserStateFlags_PST_EOFTOKEN = 4096;
const DolbraceState_NONE = 0;
const DolbraceState_PARAM = 1;
const DolbraceState_OP = 2;
const DolbraceState_WORD = 4;
const DolbraceState_QUOTE = 64;
const DolbraceState_QUOTE2 = 128;
const MatchedPairFlags_NONE = 0;
const MatchedPairFlags_DQUOTE = 1;
const MatchedPairFlags_DOLBRACE = 2;
const MatchedPairFlags_COMMAND = 4;
const MatchedPairFlags_ARITH = 8;
const MatchedPairFlags_ALLOWESC = 16;
const MatchedPairFlags_EXTGLOB = 32;
const MatchedPairFlags_FIRSTCLOSE = 64;
const MatchedPairFlags_ARRAYSUB = 128;
const MatchedPairFlags_BACKQUOTE = 256;
const ParseContext_NORMAL = 0;
const ParseContext_COMMAND_SUB = 1;
const ParseContext_ARITHMETIC = 2;
const ParseContext_CASE_PATTERN = 3;
const ParseContext_BRACE_EXPANSION = 4;
const RESERVED_WORDS = new Set(["if", "then", "elif", "else", "fi", "while", "until", "for", "select", "do", "done", "case", "esac", "in", "function", "coproc"]);
const COND_UNARY_OPS = new Set(["-a", "-b", "-c", "-d", "-e", "-f", "-g", "-h", "-k", "-p", "-r", "-s", "-t", "-u", "-w", "-x", "-G", "-L", "-N", "-O", "-S", "-z", "-n", "-o", "-v", "-R"]);
const COND_BINARY_OPS = new Set(["==", "!=", "=~", "=", "<", ">", "-eq", "-ne", "-lt", "-le", "-gt", "-ge", "-nt", "-ot", "-ef"]);
const COMPOUND_KEYWORDS = new Set(["while", "until", "for", "if", "case", "select"]);
const ASSIGNMENT_BUILTINS = new Set(["alias", "declare", "typeset", "local", "export", "readonly", "eval", "let"]);
const _SMP_LITERAL = 1;
const _SMP_PAST_OPEN = 2;
const WORD_CTX_NORMAL = 0;
const WORD_CTX_COND = 1;
const WORD_CTX_REGEX = 2;

class ParseError {
  constructor(message = "", pos = 0, line = 0) {
    this.message = message;
    this.pos = pos;
    this.line = line;
  }

  FormatMessage() {
    if (this.line !== 0 && this.pos !== 0) {
      return `Parse error at line ${this.line}, position ${this.pos}: ${this.message}`;
    } else {
      if (this.pos !== 0) {
        return `Parse error at position ${this.pos}: ${this.message}`;
      }
    }
    return `Parse error: ${this.message}`;
  }
}

class MatchedPairError extends ParseError {
}

class TokenType {
}

class Token {
  constructor(type = 0, value = "", pos = 0, parts = [], word = null) {
    this.type = type;
    this.value = value;
    this.pos = pos;
    this.parts = parts ?? [];
    this.word = word;
  }

  Repr() {
    if (this.word !== null) {
      return `Token(${this.type}, ${this.value}, ${this.pos}, word=${this.word})`;
    }
    if ((this.parts.length > 0)) {
      return `Token(${this.type}, ${this.value}, ${this.pos}, parts=${this.parts.length})`;
    }
    return `Token(${this.type}, ${this.value}, ${this.pos})`;
  }
}

class ParserStateFlags {
}

class DolbraceState {
}

class MatchedPairFlags {
}

class SavedParserState {
  constructor(parserState = 0, dolbraceState = 0, pendingHeredocs = [], ctxStack = [], eofToken = "") {
    this.parserState = parserState;
    this.dolbraceState = dolbraceState;
    this.pendingHeredocs = pendingHeredocs ?? [];
    this.ctxStack = ctxStack ?? [];
    this.eofToken = eofToken;
  }
}

class QuoteState {
  constructor(single = false, double = false, Stack = []) {
    this.single = single;
    this.double = double;
    this.Stack = Stack ?? [];
  }

  push() {
    this.Stack.push([this.single, this.double]);
    this.single = false;
    this.double = false;
  }

  pop() {
    if ((this.Stack.length > 0)) {
      [this.single, this.double] = this.Stack.pop();
    }
  }

  inQuotes() {
    return this.single || this.double;
  }

  copy() {
    var qs = newQuoteState();
    qs.single = this.single;
    qs.double = this.double;
    qs.Stack = this.Stack.slice();
    return qs;
  }

  outerDouble() {
    if (this.Stack.length === 0) {
      return false;
    }
    return this.Stack[this.Stack.length - 1][1];
  }
}

class ParseContext {
  constructor(kind = 0, parenDepth = 0, braceDepth = 0, bracketDepth = 0, caseDepth = 0, arithDepth = 0, arithParenDepth = 0, quote = null) {
    this.kind = kind;
    this.parenDepth = parenDepth;
    this.braceDepth = braceDepth;
    this.bracketDepth = bracketDepth;
    this.caseDepth = caseDepth;
    this.arithDepth = arithDepth;
    this.arithParenDepth = arithParenDepth;
    this.quote = quote;
  }

  copy() {
    var ctx = newParseContext(this.kind);
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
  constructor(Stack = []) {
    this.Stack = Stack ?? [];
  }

  getCurrent() {
    return this.Stack[this.Stack.length - 1];
  }

  push(kind) {
    this.Stack.push(newParseContext(kind));
  }

  pop() {
    if (this.Stack.length > 1) {
      return this.Stack.pop();
    }
    return this.Stack[0];
  }

  copyStack() {
    var result = [];
    result.push(...this.Stack.map(ctx => ctx.copy()));
    return result;
  }

  restoreFrom(savedStack) {
    var result = [];
    result.push(...savedStack.map(ctx => ctx.copy()));
    this.Stack = result;
  }
}

class Lexer {
  constructor(RESERVED_WORDS = new Map(), source = "", pos = 0, length = 0, quote = null, TokenCache = null, ParserState = 0, DolbraceState = 0, PendingHeredocs = [], Extglob = false, Parser = null, EofToken = "", LastReadToken = null, WordContext = 0, AtCommandStart = false, InArrayLiteral = false, InAssignBuiltin = false, PostReadPos = 0, CachedWordContext = 0, CachedAtCommandStart = false, CachedInArrayLiteral = false, CachedInAssignBuiltin = false) {
    this.RESERVED_WORDS = RESERVED_WORDS;
    this.source = source;
    this.pos = pos;
    this.length = length;
    this.quote = quote;
    this.TokenCache = TokenCache;
    this.ParserState = ParserState;
    this.DolbraceState = DolbraceState;
    this.PendingHeredocs = PendingHeredocs ?? [];
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

  peek() {
    if (this.pos >= this.length) {
      return "";
    }
    return this.source[this.pos];
  }

  advance() {
    if (this.pos >= this.length) {
      return "";
    }
    var c = this.source[this.pos];
    this.pos += 1;
    return c;
  }

  atEnd() {
    return this.pos >= this.length;
  }

  lookahead(n) {
    return Substring(this.source, this.pos, this.pos + n);
  }

  isMetachar(c) {
    return "|&;()<> \t\n".includes(c);
  }

  ReadOperator() {
    var start = this.pos;
    var c = this.peek();
    if (c === "") {
      return null;
    }
    var two = this.lookahead(2);
    var three = this.lookahead(3);
    if (three === ";;&") {
      this.pos += 3;
      return new Token(TokenType_SEMI_SEMI_AMP, three, start, null, null);
    }
    if (three === "<<-") {
      this.pos += 3;
      return new Token(TokenType_LESS_LESS_MINUS, three, start, null, null);
    }
    if (three === "<<<") {
      this.pos += 3;
      return new Token(TokenType_LESS_LESS_LESS, three, start, null, null);
    }
    if (three === "&>>") {
      this.pos += 3;
      return new Token(TokenType_AMP_GREATER_GREATER, three, start, null, null);
    }
    if (two === "&&") {
      this.pos += 2;
      return new Token(TokenType_AND_AND, two, start, null, null);
    }
    if (two === "||") {
      this.pos += 2;
      return new Token(TokenType_OR_OR, two, start, null, null);
    }
    if (two === ";;") {
      this.pos += 2;
      return new Token(TokenType_SEMI_SEMI, two, start, null, null);
    }
    if (two === ";&") {
      this.pos += 2;
      return new Token(TokenType_SEMI_AMP, two, start, null, null);
    }
    if (two === "<<") {
      this.pos += 2;
      return new Token(TokenType_LESS_LESS, two, start, null, null);
    }
    if (two === ">>") {
      this.pos += 2;
      return new Token(TokenType_GREATER_GREATER, two, start, null, null);
    }
    if (two === "<&") {
      this.pos += 2;
      return new Token(TokenType_LESS_AMP, two, start, null, null);
    }
    if (two === ">&") {
      this.pos += 2;
      return new Token(TokenType_GREATER_AMP, two, start, null, null);
    }
    if (two === "<>") {
      this.pos += 2;
      return new Token(TokenType_LESS_GREATER, two, start, null, null);
    }
    if (two === ">|") {
      this.pos += 2;
      return new Token(TokenType_GREATER_PIPE, two, start, null, null);
    }
    if (two === "&>") {
      this.pos += 2;
      return new Token(TokenType_AMP_GREATER, two, start, null, null);
    }
    if (two === "|&") {
      this.pos += 2;
      return new Token(TokenType_PIPE_AMP, two, start, null, null);
    }
    if (c === ";") {
      this.pos += 1;
      return new Token(TokenType_SEMI, c, start, null, null);
    }
    if (c === "|") {
      this.pos += 1;
      return new Token(TokenType_PIPE, c, start, null, null);
    }
    if (c === "&") {
      this.pos += 1;
      return new Token(TokenType_AMP, c, start, null, null);
    }
    if (c === "(") {
      if (this.WordContext === WORD_CTX_REGEX) {
        return null;
      }
      this.pos += 1;
      return new Token(TokenType_LPAREN, c, start, null, null);
    }
    if (c === ")") {
      if (this.WordContext === WORD_CTX_REGEX) {
        return null;
      }
      this.pos += 1;
      return new Token(TokenType_RPAREN, c, start, null, null);
    }
    if (c === "<") {
      if (this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
        return null;
      }
      this.pos += 1;
      return new Token(TokenType_LESS, c, start, null, null);
    }
    if (c === ">") {
      if (this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
        return null;
      }
      this.pos += 1;
      return new Token(TokenType_GREATER, c, start, null, null);
    }
    if (c === "\n") {
      this.pos += 1;
      return new Token(TokenType_NEWLINE, c, start, null, null);
    }
    return null;
  }

  skipBlanks() {
    while (this.pos < this.length) {
      var c = this.source[this.pos];
      if (c !== " " && c !== "\t") {
        break;
      }
      this.pos += 1;
    }
  }

  SkipComment() {
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
  }

  ReadSingleQuote(start) {
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
    throw new ParseError(`Unterminated single quote at position ${start}`, start)
  }

  IsWordTerminator(ctx, ch, bracketDepth, parenDepth) {
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
    if (((this.ParserState & ParserStateFlags_PST_EOFTOKEN) !== 0) && this.EofToken !== "" && ch === this.EofToken && bracketDepth === 0) {
      return true;
    }
    if (IsRedirectChar(ch) && this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
      return false;
    }
    return IsMetachar(ch) && bracketDepth === 0;
  }

  ReadBracketExpression(chars, parts, forRegex, parenDepth) {
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
    } else {
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
      } else {
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
        } else {
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
          } else {
            if (forRegex && c === "$") {
              this.SyncToParser();
              if (!this.Parser.ParseDollarExpansion(chars, parts, false)) {
                this.SyncFromParser();
                chars.push(this.advance());
              } else {
                this.SyncFromParser();
              }
            } else {
              chars.push(this.advance());
            }
          }
        }
      }
    }
    return true;
  }

  ParseMatchedPair(openChar, closeChar, flags, initialWasDollar) {
    var start = this.pos;
    var count = 1;
    var chars = [];
    var passNext = false;
    var wasDollar = initialWasDollar;
    var wasGtlt = false;
    while (count > 0) {
      if (this.atEnd()) {
        throw new MatchedPairError()
      }
      var ch = this.advance();
      if (((flags & MatchedPairFlags_DOLBRACE) !== 0) && this.DolbraceState === DolbraceState_OP) {
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
        if (ch === "\\" && ((flags & MatchedPairFlags_ALLOWESC) !== 0)) {
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
        if (!(((flags & MatchedPairFlags_DOLBRACE) !== 0) && openChar === "{")) {
          count += 1;
        }
        chars.push(ch);
        wasDollar = false;
        wasGtlt = "<>".includes(ch);
        continue;
      }
      if ("'\"`".includes(ch) && openChar !== closeChar) {
        var nested;
        if (ch === "'") {
          chars.push(ch);
          var quoteFlags = (wasDollar ? flags | MatchedPairFlags_ALLOWESC : flags);
          nested = this.ParseMatchedPair("'", "'", quoteFlags, false);
          chars.push(nested);
          chars.push("'");
          wasDollar = false;
          wasGtlt = false;
          continue;
        } else {
          if (ch === "\"") {
            chars.push(ch);
            nested = this.ParseMatchedPair("\"", "\"", flags | MatchedPairFlags_DQUOTE, false);
            chars.push(nested);
            chars.push("\"");
            wasDollar = false;
            wasGtlt = false;
            continue;
          } else {
            if (ch === "`") {
              chars.push(ch);
              nested = this.ParseMatchedPair("`", "`", flags, false);
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
          if (((flags & MatchedPairFlags_ARITH) !== 0)) {
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
          var [paramNode, paramText] = this.Parser.ParseParamExpansion(inDquote);
          this.SyncFromParser();
          if (paramNode !== null) {
            chars.push(paramText);
            wasDollar = false;
            wasGtlt = false;
          } else {
            chars.push(this.advance());
            wasDollar = true;
            wasGtlt = false;
          }
          continue;
        } else {
          var arithNode;
          var arithText;
          if (nextCh === "(") {
            this.pos -= 1;
            this.SyncToParser();
            var cmdNode;
            var cmdText;
            if (this.pos + 2 < this.length && this.source[this.pos + 2] === "(") {
              [arithNode, arithText] = this.Parser.ParseArithmeticExpansion();
              this.SyncFromParser();
              if (arithNode !== null) {
                chars.push(arithText);
                wasDollar = false;
                wasGtlt = false;
              } else {
                this.SyncToParser();
                [cmdNode, cmdText] = this.Parser.ParseCommandSubstitution();
                this.SyncFromParser();
                if (cmdNode !== null) {
                  chars.push(cmdText);
                  wasDollar = false;
                  wasGtlt = false;
                } else {
                  chars.push(this.advance());
                  chars.push(this.advance());
                  wasDollar = false;
                  wasGtlt = false;
                }
              }
            } else {
              [cmdNode, cmdText] = this.Parser.ParseCommandSubstitution();
              this.SyncFromParser();
              if (cmdNode !== null) {
                chars.push(cmdText);
                wasDollar = false;
                wasGtlt = false;
              } else {
                chars.push(this.advance());
                chars.push(this.advance());
                wasDollar = false;
                wasGtlt = false;
              }
            }
            continue;
          } else {
            if (nextCh === "[") {
              this.pos -= 1;
              this.SyncToParser();
              [arithNode, arithText] = this.Parser.ParseDeprecatedArithmetic();
              this.SyncFromParser();
              if (arithNode !== null) {
                chars.push(arithText);
                wasDollar = false;
                wasGtlt = false;
              } else {
                chars.push(this.advance());
                wasDollar = true;
                wasGtlt = false;
              }
              continue;
            }
          }
        }
      }
      if (ch === "(" && wasGtlt && ((flags & (MatchedPairFlags_DOLBRACE | MatchedPairFlags_ARRAYSUB)) !== 0)) {
        {
          var direction = chars[chars.length - 1];
          chars = chars.slice(0, chars.length - 1);
        }
        this.pos -= 1;
        this.SyncToParser();
        var [procsubNode, procsubText] = this.Parser.ParseProcessSubstitution();
        this.SyncFromParser();
        if (procsubNode !== null) {
          chars.push(procsubText);
          wasDollar = false;
          wasGtlt = false;
        } else {
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
  }

  CollectParamArgument(flags, wasDollar) {
    return this.ParseMatchedPair("{", "}", flags | MatchedPairFlags_DOLBRACE, wasDollar);
  }

  ReadWordInternal(ctx, atCommandStart, inArrayLiteral, inAssignBuiltin) {
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
        if ((chars.length > 0) && atCommandStart && !seenEquals && IsArrayAssignmentPrefix(chars)) {
          var prevChar = chars[chars.length - 1];
          if (/^[a-zA-Z0-9]+$/.test(prevChar) || prevChar === "_") {
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
      var content;
      if (ctx === WORD_CTX_COND && ch === "(") {
        if (this.Extglob && (chars.length > 0) && IsExtglobPrefix(chars[chars.length - 1])) {
          chars.push(this.advance());
          content = this.ParseMatchedPair("(", ")", MatchedPairFlags_EXTGLOB, false);
          chars.push(content);
          chars.push(")");
          continue;
        } else {
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
        [content, sawNewline] = this.ReadSingleQuote(start);
        chars.push(content);
        if (trackNewline && sawNewline && this.Parser !== null) {
          this.Parser.SawNewlineInSingleQuote = true;
        }
        continue;
      }
      var cmdsubResult0;
      var cmdsubResult1;
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
              } else {
                chars.push(this.advance());
                chars.push(this.advance());
              }
            } else {
              if (c === "$") {
                this.SyncToParser();
                if (!this.Parser.ParseDollarExpansion(chars, parts, true)) {
                  this.SyncFromParser();
                  chars.push(this.advance());
                } else {
                  this.SyncFromParser();
                }
              } else {
                if (c === "`") {
                  this.SyncToParser();
                  [cmdsubResult0, cmdsubResult1] = this.Parser.ParseBacktickSubstitution();
                  this.SyncFromParser();
                  if (cmdsubResult0 !== null) {
                    parts.push(cmdsubResult0);
                    chars.push(cmdsubResult1);
                  } else {
                    chars.push(this.advance());
                  }
                } else {
                  chars.push(this.advance());
                }
              }
            }
          }
          if (this.atEnd()) {
            throw new ParseError(`Unterminated double quote at position ${start}`, start)
          }
          chars.push(this.advance());
        } else {
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
        } else {
          chars.push(this.advance());
          chars.push(this.advance());
        }
        continue;
      }
      if (ctx !== WORD_CTX_REGEX && ch === "$" && this.pos + 1 < this.length && this.source[this.pos + 1] === "'") {
        var [ansiResult0, ansiResult1] = this.ReadAnsiCQuote();
        if (ansiResult0 !== null) {
          parts.push(ansiResult0);
          chars.push(ansiResult1);
        } else {
          chars.push(this.advance());
        }
        continue;
      }
      if (ctx !== WORD_CTX_REGEX && ch === "$" && this.pos + 1 < this.length && this.source[this.pos + 1] === "\"") {
        var [localeResult0, localeResult1, localeResult2] = this.ReadLocaleString();
        if (localeResult0 !== null) {
          parts.push(localeResult0);
          parts.push(...localeResult2);
          chars.push(localeResult1);
        } else {
          chars.push(this.advance());
        }
        continue;
      }
      if (ch === "$") {
        this.SyncToParser();
        if (!this.Parser.ParseDollarExpansion(chars, parts, false)) {
          this.SyncFromParser();
          chars.push(this.advance());
        } else {
          this.SyncFromParser();
          if (this.Extglob && ctx === WORD_CTX_NORMAL && (chars.length > 0) && chars[chars.length - 1].length === 2 && chars[chars.length - 1][0] === "$" && "?*@".includes(chars[chars.length - 1][1]) && !this.atEnd() && this.peek() === "(") {
            chars.push(this.advance());
            content = this.ParseMatchedPair("(", ")", MatchedPairFlags_EXTGLOB, false);
            chars.push(content);
            chars.push(")");
          }
        }
        continue;
      }
      if (ctx !== WORD_CTX_REGEX && ch === "`") {
        this.SyncToParser();
        [cmdsubResult0, cmdsubResult1] = this.Parser.ParseBacktickSubstitution();
        this.SyncFromParser();
        if (cmdsubResult0 !== null) {
          parts.push(cmdsubResult0);
          chars.push(cmdsubResult1);
        } else {
          chars.push(this.advance());
        }
        continue;
      }
      if (ctx !== WORD_CTX_REGEX && IsRedirectChar(ch) && this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
        this.SyncToParser();
        var [procsubResult0, procsubResult1] = this.Parser.ParseProcessSubstitution();
        this.SyncFromParser();
        if (procsubResult0 !== null) {
          parts.push(procsubResult0);
          chars.push(procsubResult1);
        } else {
          if ((procsubResult1.length > 0)) {
            chars.push(procsubResult1);
          } else {
            chars.push(this.advance());
            if (ctx === WORD_CTX_NORMAL) {
              chars.push(this.advance());
            }
          }
        }
        continue;
      }
      if (ctx === WORD_CTX_NORMAL && ch === "(" && (chars.length > 0) && bracketDepth === 0) {
        var isArrayAssign = false;
        if (chars.length >= 3 && chars[chars.length - 2] === "+" && chars[chars.length - 1] === "=") {
          isArrayAssign = IsArrayAssignmentPrefix(chars.slice(0, chars.length - 2));
        } else {
          if (chars[chars.length - 1] === "=" && chars.length >= 2) {
            isArrayAssign = IsArrayAssignmentPrefix(chars.slice(0, chars.length - 1));
          }
        }
        if (isArrayAssign && (atCommandStart || inAssignBuiltin)) {
          this.SyncToParser();
          var [arrayResult0, arrayResult1] = this.Parser.ParseArrayLiteral();
          this.SyncFromParser();
          if (arrayResult0 !== null) {
            parts.push(arrayResult0);
            chars.push(arrayResult1);
          } else {
            break;
          }
          continue;
        }
      }
      if (this.Extglob && ctx === WORD_CTX_NORMAL && IsExtglobPrefix(ch) && this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
        chars.push(this.advance());
        chars.push(this.advance());
        content = this.ParseMatchedPair("(", ")", MatchedPairFlags_EXTGLOB, false);
        chars.push(content);
        chars.push(")");
        continue;
      }
      if (ctx === WORD_CTX_NORMAL && ((this.ParserState & ParserStateFlags_PST_EOFTOKEN) !== 0) && this.EofToken !== "" && ch === this.EofToken && bracketDepth === 0) {
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
      throw new MatchedPairError()
    }
    if (!(chars.length > 0)) {
      return null;
    }
    if ((parts.length > 0)) {
      return new Word(chars.join(""), parts, "word");
    }
    return new Word(chars.join(""), null, "word");
  }

  ReadWord() {
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
  }

  nextToken() {
    var tok;
    if (this.TokenCache !== null) {
      tok = this.TokenCache;
      this.TokenCache = null;
      this.LastReadToken = tok;
      return tok;
    }
    this.skipBlanks();
    if (this.atEnd()) {
      tok = new Token(TokenType_EOF, "", this.pos, null, null);
      this.LastReadToken = tok;
      return tok;
    }
    if (this.EofToken !== "" && this.peek() === this.EofToken && !((this.ParserState & ParserStateFlags_PST_CASEPAT) !== 0) && !((this.ParserState & ParserStateFlags_PST_EOFTOKEN) !== 0)) {
      tok = new Token(TokenType_EOF, "", this.pos, null, null);
      this.LastReadToken = tok;
      return tok;
    }
    while (this.SkipComment()) {
      this.skipBlanks();
      if (this.atEnd()) {
        tok = new Token(TokenType_EOF, "", this.pos, null, null);
        this.LastReadToken = tok;
        return tok;
      }
      if (this.EofToken !== "" && this.peek() === this.EofToken && !((this.ParserState & ParserStateFlags_PST_CASEPAT) !== 0) && !((this.ParserState & ParserStateFlags_PST_EOFTOKEN) !== 0)) {
        tok = new Token(TokenType_EOF, "", this.pos, null, null);
        this.LastReadToken = tok;
        return tok;
      }
    }
    tok = this.ReadOperator();
    if (tok !== null) {
      this.LastReadToken = tok;
      return tok;
    }
    tok = this.ReadWord();
    if (tok !== null) {
      this.LastReadToken = tok;
      return tok;
    }
    tok = new Token(TokenType_EOF, "", this.pos, null, null);
    this.LastReadToken = tok;
    return tok;
  }

  peekToken() {
    if (this.TokenCache === null) {
      var savedLast = this.LastReadToken;
      this.TokenCache = this.nextToken();
      this.LastReadToken = savedLast;
    }
    return this.TokenCache;
  }

  ReadAnsiCQuote() {
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
      } else {
        if (ch === "\\") {
          contentChars.push(this.advance());
          if (!this.atEnd()) {
            contentChars.push(this.advance());
          }
        } else {
          contentChars.push(this.advance());
        }
      }
    }
    if (!foundClose) {
      throw new MatchedPairError()
    }
    var text = Substring(this.source, start, this.pos);
    var content = contentChars.join("");
    var node = new AnsiCQuote(content, "ansi-c");
    return [node, text];
  }

  SyncToParser() {
    if (this.Parser !== null) {
      this.Parser.pos = this.pos;
    }
  }

  SyncFromParser() {
    if (this.Parser !== null) {
      this.pos = this.Parser.pos;
    }
  }

  ReadLocaleString() {
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
      } else {
        if (ch === "\\" && this.pos + 1 < this.length) {
          var nextCh = this.source[this.pos + 1];
          if (nextCh === "\n") {
            this.advance();
            this.advance();
          } else {
            contentChars.push(this.advance());
            contentChars.push(this.advance());
          }
        } else {
          var cmdsubNode;
          var cmdsubText;
          if (ch === "$" && this.pos + 2 < this.length && this.source[this.pos + 1] === "(" && this.source[this.pos + 2] === "(") {
            this.SyncToParser();
            var [arithNode, arithText] = this.Parser.ParseArithmeticExpansion();
            this.SyncFromParser();
            if (arithNode !== null) {
              innerParts.push(arithNode);
              contentChars.push(arithText);
            } else {
              this.SyncToParser();
              [cmdsubNode, cmdsubText] = this.Parser.ParseCommandSubstitution();
              this.SyncFromParser();
              if (cmdsubNode !== null) {
                innerParts.push(cmdsubNode);
                contentChars.push(cmdsubText);
              } else {
                contentChars.push(this.advance());
              }
            }
          } else {
            if (IsExpansionStart(this.source, this.pos, "$(")) {
              this.SyncToParser();
              [cmdsubNode, cmdsubText] = this.Parser.ParseCommandSubstitution();
              this.SyncFromParser();
              if (cmdsubNode !== null) {
                innerParts.push(cmdsubNode);
                contentChars.push(cmdsubText);
              } else {
                contentChars.push(this.advance());
              }
            } else {
              if (ch === "$") {
                this.SyncToParser();
                var [paramNode, paramText] = this.Parser.ParseParamExpansion(false);
                this.SyncFromParser();
                if (paramNode !== null) {
                  innerParts.push(paramNode);
                  contentChars.push(paramText);
                } else {
                  contentChars.push(this.advance());
                }
              } else {
                if (ch === "`") {
                  this.SyncToParser();
                  [cmdsubNode, cmdsubText] = this.Parser.ParseBacktickSubstitution();
                  this.SyncFromParser();
                  if (cmdsubNode !== null) {
                    innerParts.push(cmdsubNode);
                    contentChars.push(cmdsubText);
                  } else {
                    contentChars.push(this.advance());
                  }
                } else {
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
  }

  UpdateDolbraceForOp(op, hasParam) {
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
  }

  ConsumeParamOperator() {
    if (this.atEnd()) {
      return "";
    }
    var ch = this.peek();
    var nextCh;
    if (ch === ":") {
      this.advance();
      if (this.atEnd()) {
        return ":";
      }
      nextCh = this.peek();
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
        nextCh = this.peek();
        if (nextCh === "/") {
          this.advance();
          return "//";
        } else {
          if (nextCh === "#") {
            this.advance();
            return "/#";
          } else {
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
  }

  ParamSubscriptHasClose(startPos) {
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
      } else {
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
  }

  ConsumeParamName() {
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
    if (/^\d+$/.test(ch)) {
      var nameChars = [];
      while (!this.atEnd() && /^\d+$/.test(this.peek())) {
        nameChars.push(this.advance());
      }
      return nameChars.join("");
    }
    if (/^[a-zA-Z]+$/.test(ch) || ch === "_") {
      var nameChars = [];
      while (!this.atEnd()) {
        var c = this.peek();
        if (/^[a-zA-Z0-9]+$/.test(c) || c === "_") {
          nameChars.push(this.advance());
        } else {
          if (c === "[") {
            if (!this.ParamSubscriptHasClose(this.pos)) {
              break;
            }
            nameChars.push(this.advance());
            var content = this.ParseMatchedPair("[", "]", MatchedPairFlags_ARRAYSUB, false);
            nameChars.push(content);
            nameChars.push("]");
            break;
          } else {
            break;
          }
        }
      }
      if ((nameChars.length > 0)) {
        return nameChars.join("");
      } else {
        return "";
      }
    }
    return "";
  }

  ReadParamExpansion(inDquote) {
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
    var text;
    if (IsSpecialParamUnbraced(ch) || IsDigit(ch) || ch === "#") {
      this.advance();
      text = Substring(this.source, start, this.pos);
      return [new ParamExpansion(ch, null, null, "param"), text];
    }
    if (/^[a-zA-Z]+$/.test(ch) || ch === "_") {
      var nameStart = this.pos;
      while (!this.atEnd()) {
        var c = this.peek();
        if (/^[a-zA-Z0-9]+$/.test(c) || c === "_") {
          this.advance();
        } else {
          break;
        }
      }
      var name = Substring(this.source, nameStart, this.pos);
      text = Substring(this.source, start, this.pos);
      return [new ParamExpansion(name, null, null, "param"), text];
    }
    this.pos = start;
    return [null, ""];
  }

  ReadBracedParam(start, inDquote) {
    if (this.atEnd()) {
      throw new MatchedPairError()
    }
    var savedDolbrace = this.DolbraceState;
    this.DolbraceState = DolbraceState_PARAM;
    var ch = this.peek();
    if (IsFunsubChar(ch)) {
      this.DolbraceState = savedDolbrace;
      return this.ReadFunsub(start);
    }
    var param;
    var text;
    if (ch === "#") {
      this.advance();
      param = this.ConsumeParamName();
      if ((param.length > 0) && !this.atEnd() && this.peek() === "}") {
        this.advance();
        text = Substring(this.source, start, this.pos);
        this.DolbraceState = savedDolbrace;
        return [new ParamLength(param, "param-len"), text];
      }
      this.pos = start + 2;
    }
    var op;
    var arg;
    if (ch === "!") {
      this.advance();
      while (!this.atEnd() && IsWhitespaceNoNewline(this.peek())) {
        this.advance();
      }
      param = this.ConsumeParamName();
      if ((param.length > 0)) {
        while (!this.atEnd() && IsWhitespaceNoNewline(this.peek())) {
          this.advance();
        }
        if (!this.atEnd() && this.peek() === "}") {
          this.advance();
          text = Substring(this.source, start, this.pos);
          this.DolbraceState = savedDolbrace;
          return [new ParamIndirect(param, null, null, "param-indirect"), text];
        }
        if (!this.atEnd() && IsAtOrStar(this.peek())) {
          var suffix = this.advance();
          var trailing = this.ParseMatchedPair("{", "}", MatchedPairFlags_DOLBRACE, false);
          text = Substring(this.source, start, this.pos);
          this.DolbraceState = savedDolbrace;
          return [new ParamIndirect(param + suffix + trailing, null, null, "param-indirect"), text];
        }
        op = this.ConsumeParamOperator();
        if (op === "" && !this.atEnd() && !"}\"'`".includes(this.peek())) {
          op = this.advance();
        }
        if (op !== "" && !"\"'`".includes(op)) {
          arg = this.ParseMatchedPair("{", "}", MatchedPairFlags_DOLBRACE, false);
          text = Substring(this.source, start, this.pos);
          this.DolbraceState = savedDolbrace;
          return [new ParamIndirect(param, op, arg, "param-indirect"), text];
        }
        if (this.atEnd()) {
          this.DolbraceState = savedDolbrace;
          throw new MatchedPairError()
        }
        this.pos = start + 2;
      } else {
        this.pos = start + 2;
      }
    }
    param = this.ConsumeParamName();
    if (!(param.length > 0)) {
      if (!this.atEnd() && ("-=+?".includes(this.peek()) || this.peek() === ":" && this.pos + 1 < this.length && IsSimpleParamOp(this.source[this.pos + 1]))) {
        param = "";
      } else {
        var content = this.ParseMatchedPair("{", "}", MatchedPairFlags_DOLBRACE, false);
        text = "${" + content + "}";
        this.DolbraceState = savedDolbrace;
        return [new ParamExpansion(content, null, null, "param"), text];
      }
    }
    if (this.atEnd()) {
      this.DolbraceState = savedDolbrace;
      throw new MatchedPairError()
    }
    if (this.peek() === "}") {
      this.advance();
      text = Substring(this.source, start, this.pos);
      this.DolbraceState = savedDolbrace;
      return [new ParamExpansion(param, null, null, "param"), text];
    }
    op = this.ConsumeParamOperator();
    if (op === "") {
      if (!this.atEnd() && this.peek() === "$" && this.pos + 1 < this.length && (this.source[this.pos + 1] === "\"" || this.source[this.pos + 1] === "'")) {
        var dollarCount = 1 + CountConsecutiveDollarsBefore(this.source, this.pos);
        if (dollarCount % 2 === 1) {
          op = "";
        } else {
          op = this.advance();
        }
      } else {
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
            throw new ParseError(`Unterminated backtick at position ${backtickPos}`, backtickPos)
          }
          this.advance();
          op = "`";
        } else {
          if (!this.atEnd() && this.peek() === "$" && this.pos + 1 < this.length && this.source[this.pos + 1] === "{") {
            op = "";
          } else {
            if (!this.atEnd() && (this.peek() === "'" || this.peek() === "\"")) {
              op = "";
            } else {
              if (!this.atEnd() && this.peek() === "\\") {
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
    this.UpdateDolbraceForOp(op, param.length > 0);
    try {
      var flags = (inDquote ? MatchedPairFlags_DQUOTE : MatchedPairFlags_NONE);
      var paramEndsWithDollar = param !== "" && param.endsWith("$");
      arg = this.CollectParamArgument(flags, paramEndsWithDollar);
    } catch (e) {
      this.DolbraceState = savedDolbrace;
      throw e
    }
    if ((op === "<" || op === ">") && arg.startsWith("(") && arg.endsWith(")")) {
      var inner = arg.slice(1, arg.length - 1);
      try {
        var subParser = newParser(inner, true, this.Parser.Extglob);
        var parsed = subParser.parseList(true);
        if (parsed !== null && subParser.atEnd()) {
          var formatted = FormatCmdsubNode(parsed, 0, true, false, true);
          arg = "(" + formatted + ")";
        }
      } catch (_e) {
      }
    }
    text = "${" + param + op + arg + "}";
    this.DolbraceState = savedDolbrace;
    return [new ParamExpansion(param, op, arg, "param"), text];
  }

  ReadFunsub(start) {
    return this.Parser.ParseFunsub(start);
  }
}

class Word {
  constructor(value = "", parts = [], kind = "") {
    this.value = value;
    this.parts = parts ?? [];
    this.kind = kind;
  }

  toSexp() {
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
  }

  AppendWithCtlesc(result, byteVal) {
    result.push(byteVal);
  }

  DoubleCtlescSmart(value) {
    var result = [];
    var quote = newQuoteState();
    for (const c of value) {
      if (c === "'" && !quote.double) {
        quote.single = !quote.single;
      } else {
        if (c === "\"" && !quote.single) {
          quote.double = !quote.double;
        }
      }
      result.push(c);
      if (c === "") {
        if (quote.double) {
          var bsCount = 0;
          for (var j = result.length - 2; j > -1; j += -1) {
            if (result[j] === "\\") {
              bsCount += 1;
            } else {
              break;
            }
          }
          if (bsCount % 2 === 0) {
            result.push("");
          }
        } else {
          result.push("");
        }
      }
    }
    return result.join("");
  }

  NormalizeParamExpansionNewlines(value) {
    var result = [];
    var i = 0;
    var quote = newQuoteState();
    while (i < value.length) {
      var c = value[i];
      if (c === "'" && !quote.double) {
        quote.single = !quote.single;
        result.push(c);
        i += 1;
      } else {
        if (c === "\"" && !quote.single) {
          quote.double = !quote.double;
          result.push(c);
          i += 1;
        } else {
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
              } else {
                if (ch === "\"" && !quote.single) {
                  quote.double = !quote.double;
                } else {
                  if (!quote.inQuotes()) {
                    if (ch === "{") {
                      depth += 1;
                    } else {
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
          } else {
            result.push(c);
            i += 1;
          }
        }
      }
    }
    return result.join("");
  }

  ShSingleQuote(s) {
    if (!(s.length > 0)) {
      return "''";
    }
    if (s === "'") {
      return "\\'";
    }
    var result = ["'"];
    for (const c of s) {
      if (c === "'") {
        result.push("'\\''");
      } else {
        result.push(c);
      }
    }
    result.push("'");
    return result.join("");
  }

  AnsiCToBytes(inner) {
    var result = [];
    var i = 0;
    while (i < inner.length) {
      if (inner[i] === "\\" && i + 1 < inner.length) {
        var c = inner[i + 1];
        var simple = GetAnsiEscape(c);
        if (simple >= 0) {
          result.push(simple);
          i += 2;
        } else {
          if (c === "'") {
            result.push(39);
            i += 2;
          } else {
            var j;
            var byteVal;
            if (c === "x") {
              if (i + 2 < inner.length && inner[i + 2] === "{") {
                j = i + 3;
                while (j < inner.length && IsHexDigit(inner[j])) {
                  j += 1;
                }
                var hexStr = Substring(inner, i + 3, j);
                if (j < inner.length && inner[j] === "}") {
                  j += 1;
                }
                if (!(hexStr.length > 0)) {
                  return result;
                }
                byteVal = parseInt(hexStr, 16) & 255;
                if (byteVal === 0) {
                  return result;
                }
                this.AppendWithCtlesc(result, byteVal);
                i = j;
              } else {
                j = i + 2;
                while (j < inner.length && j < i + 4 && IsHexDigit(inner[j])) {
                  j += 1;
                }
                if (j > i + 2) {
                  byteVal = parseInt(Substring(inner, i + 2, j), 16);
                  if (byteVal === 0) {
                    return result;
                  }
                  this.AppendWithCtlesc(result, byteVal);
                  i = j;
                } else {
                  result.push(inner[i].charCodeAt(0));
                  i += 1;
                }
              }
            } else {
              var codepoint;
              if (c === "u") {
                j = i + 2;
                while (j < inner.length && j < i + 6 && IsHexDigit(inner[j])) {
                  j += 1;
                }
                if (j > i + 2) {
                  codepoint = parseInt(Substring(inner, i + 2, j), 16);
                  if (codepoint === 0) {
                    return result;
                  }
                  result.push(...Array.from(new TextEncoder().encode(String.fromCodePoint(codepoint))));
                  i = j;
                } else {
                  result.push(inner[i].charCodeAt(0));
                  i += 1;
                }
              } else {
                if (c === "U") {
                  j = i + 2;
                  while (j < inner.length && j < i + 10 && IsHexDigit(inner[j])) {
                    j += 1;
                  }
                  if (j > i + 2) {
                    codepoint = parseInt(Substring(inner, i + 2, j), 16);
                    if (codepoint === 0) {
                      return result;
                    }
                    result.push(...Array.from(new TextEncoder().encode(String.fromCodePoint(codepoint))));
                    i = j;
                  } else {
                    result.push(inner[i].charCodeAt(0));
                    i += 1;
                  }
                } else {
                  if (c === "c") {
                    if (i + 3 <= inner.length) {
                      var ctrlChar = inner[i + 2];
                      var skipExtra = 0;
                      if (ctrlChar === "\\" && i + 4 <= inner.length && inner[i + 3] === "\\") {
                        skipExtra = 1;
                      }
                      var ctrlVal = ctrlChar.charCodeAt(0) & 31;
                      if (ctrlVal === 0) {
                        return result;
                      }
                      this.AppendWithCtlesc(result, ctrlVal);
                      i += 3 + skipExtra;
                    } else {
                      result.push(inner[i].charCodeAt(0));
                      i += 1;
                    }
                  } else {
                    if (c === "0") {
                      j = i + 2;
                      while (j < inner.length && j < i + 4 && IsOctalDigit(inner[j])) {
                        j += 1;
                      }
                      if (j > i + 2) {
                        byteVal = parseInt(Substring(inner, i + 1, j), 8) & 255;
                        if (byteVal === 0) {
                          return result;
                        }
                        this.AppendWithCtlesc(result, byteVal);
                        i = j;
                      } else {
                        return result;
                      }
                    } else {
                      if (c >= "1" && c <= "7") {
                        j = i + 1;
                        while (j < inner.length && j < i + 4 && IsOctalDigit(inner[j])) {
                          j += 1;
                        }
                        byteVal = parseInt(Substring(inner, i + 1, j), 8) & 255;
                        if (byteVal === 0) {
                          return result;
                        }
                        this.AppendWithCtlesc(result, byteVal);
                        i = j;
                      } else {
                        result.push(92);
                        result.push(c.charCodeAt(0));
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
        result.push(...Array.from(new TextEncoder().encode(inner[i])));
        i += 1;
      }
    }
    return result;
  }

  ExpandAnsiCEscapes(value) {
    if (!(value.startsWith("'") && value.endsWith("'"))) {
      return value;
    }
    var inner = Substring(value, 1, value.length - 1);
    var literalBytes = this.AnsiCToBytes(inner);
    var literalStr = new TextDecoder().decode(new Uint8Array(literalBytes));
    return this.ShSingleQuote(literalStr);
  }

  ExpandAllAnsiCQuotes(value) {
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
        } else {
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
        } else {
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
      } else {
        if (ch === "\"" && !quote.single) {
          quote.double = !quote.double;
          result.push(ch);
          i += 1;
        } else {
          if (ch === "\\" && i + 1 < value.length && !quote.single) {
            result.push(ch);
            result.push(value[i + 1]);
            i += 2;
          } else {
            if (StartsWithAt(value, i, "$'") && !quote.single && !effectiveInDquote && CountConsecutiveDollarsBefore(value, i) % 2 === 0) {
              var j = i + 2;
              while (j < value.length) {
                if (value[j] === "\\" && j + 1 < value.length) {
                  j += 2;
                } else {
                  if (value[j] === "'") {
                    j += 1;
                    break;
                  } else {
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
                    if ((afterBrace.length > 0)) {
                      if ("@*#?-$!0123456789_".includes(afterBrace[0])) {
                        varNameLen = 1;
                      } else {
                        if (/^[a-zA-Z]+$/.test(afterBrace[0]) || afterBrace[0] === "_") {
                          while (varNameLen < afterBrace.length) {
                            var c = afterBrace[varNameLen];
                            if (!(/^[a-zA-Z0-9]+$/.test(c) || c === "_")) {
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
                      for (const op of ["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"]) {
                        if (opStart.startsWith(op)) {
                          inPattern = true;
                          break;
                        }
                      }
                      if (!inPattern && (opStart.length > 0) && !"%#/^,~:+-=?".includes(opStart[0])) {
                        for (const op of ["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"]) {
                          if (opStart.includes(op)) {
                            inPattern = true;
                            break;
                          }
                        }
                      }
                    } else {
                      if (varNameLen === 0 && afterBrace.length > 1) {
                        var firstChar = afterBrace[0];
                        if (!"%#/^,".includes(firstChar)) {
                          var rest = afterBrace.slice(1);
                          for (const op of ["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"]) {
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
            } else {
              result.push(ch);
              i += 1;
            }
          }
        }
      }
    }
    return result.join("");
  }

  StripLocaleStringDollars(value) {
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
      } else {
        if (StartsWithAt(value, i, "${") && !quote.single && !braceQuote.single && (i === 0 || value[i - 1] !== "$")) {
          braceDepth += 1;
          braceQuote.double = false;
          braceQuote.single = false;
          result.push("$");
          result.push("{");
          i += 2;
        } else {
          if (ch === "}" && braceDepth > 0 && !quote.single && !braceQuote.double && !braceQuote.single) {
            braceDepth -= 1;
            result.push(ch);
            i += 1;
          } else {
            if (ch === "[" && braceDepth > 0 && !quote.single && !braceQuote.double) {
              bracketDepth += 1;
              bracketInDoubleQuote = false;
              result.push(ch);
              i += 1;
            } else {
              if (ch === "]" && bracketDepth > 0 && !quote.single && !bracketInDoubleQuote) {
                bracketDepth -= 1;
                result.push(ch);
                i += 1;
              } else {
                if (ch === "'" && !quote.double && braceDepth === 0) {
                  quote.single = !quote.single;
                  result.push(ch);
                  i += 1;
                } else {
                  if (ch === "\"" && !quote.single && braceDepth === 0) {
                    quote.double = !quote.double;
                    result.push(ch);
                    i += 1;
                  } else {
                    if (ch === "\"" && !quote.single && bracketDepth > 0) {
                      bracketInDoubleQuote = !bracketInDoubleQuote;
                      result.push(ch);
                      i += 1;
                    } else {
                      if (ch === "\"" && !quote.single && !braceQuote.single && braceDepth > 0) {
                        braceQuote.double = !braceQuote.double;
                        result.push(ch);
                        i += 1;
                      } else {
                        if (ch === "'" && !quote.double && !braceQuote.double && braceDepth > 0) {
                          braceQuote.single = !braceQuote.single;
                          result.push(ch);
                          i += 1;
                        } else {
                          if (StartsWithAt(value, i, "$\"") && !quote.single && !braceQuote.single && (braceDepth > 0 || bracketDepth > 0 || !quote.double) && !braceQuote.double && !bracketInDoubleQuote) {
                            var dollarCount = 1 + CountConsecutiveDollarsBefore(value, i);
                            if (dollarCount % 2 === 1) {
                              result.push("\"");
                              if (bracketDepth > 0) {
                                bracketInDoubleQuote = true;
                              } else {
                                if (braceDepth > 0) {
                                  braceQuote.double = true;
                                } else {
                                  quote.double = true;
                                }
                              }
                              i += 2;
                            } else {
                              result.push(ch);
                              i += 1;
                            }
                          } else {
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
  }

  NormalizeArrayWhitespace(value) {
    var i = 0;
    if (!(i < value.length && (/^[a-zA-Z]+$/.test(value[i]) || value[i] === "_"))) {
      return value;
    }
    i += 1;
    while (i < value.length && (/^[a-zA-Z0-9]+$/.test(value[i]) || value[i] === "_")) {
      i += 1;
    }
    while (i < value.length && value[i] === "[") {
      var depth = 1;
      i += 1;
      while (i < value.length && depth > 0) {
        if (value[i] === "[") {
          depth += 1;
        } else {
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
    var closeParenPos;
    if (value.endsWith(")")) {
      closeParenPos = value.length - 1;
    } else {
      closeParenPos = this.FindMatchingParen(value, openParenPos);
      if (closeParenPos < 0) {
        return value;
      }
    }
    var inner = Substring(value, openParenPos + 1, closeParenPos);
    var suffix = Substring(value, closeParenPos + 1, value.length);
    var result = this.NormalizeArrayInner(inner);
    return prefix + "(" + result + ")" + suffix;
  }

  FindMatchingParen(value, openPos) {
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
      } else {
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
  }

  NormalizeArrayInner(inner) {
    var normalized = [];
    var i = 0;
    var inWhitespace = true;
    var braceDepth = 0;
    var bracketDepth = 0;
    while (i < inner.length) {
      var ch = inner[i];
      if (IsWhitespace(ch)) {
        if (!inWhitespace && (normalized.length > 0) && braceDepth === 0 && bracketDepth === 0) {
          normalized.push(" ");
          inWhitespace = true;
        }
        if (braceDepth > 0 || bracketDepth > 0) {
          normalized.push(ch);
        }
        i += 1;
      } else {
        var j;
        if (ch === "'") {
          inWhitespace = false;
          j = i + 1;
          while (j < inner.length && inner[j] !== "'") {
            j += 1;
          }
          normalized.push(Substring(inner, i, j + 1));
          i = j + 1;
        } else {
          if (ch === "\"") {
            inWhitespace = false;
            j = i + 1;
            var dqContent = ["\""];
            var dqBraceDepth = 0;
            while (j < inner.length) {
              if (inner[j] === "\\" && j + 1 < inner.length) {
                if (inner[j + 1] === "\n") {
                  j += 2;
                } else {
                  dqContent.push(inner[j]);
                  dqContent.push(inner[j + 1]);
                  j += 2;
                }
              } else {
                if (IsExpansionStart(inner, j, "${")) {
                  dqContent.push("${");
                  dqBraceDepth += 1;
                  j += 2;
                } else {
                  if (inner[j] === "}" && dqBraceDepth > 0) {
                    dqContent.push("}");
                    dqBraceDepth -= 1;
                    j += 1;
                  } else {
                    if (inner[j] === "\"" && dqBraceDepth === 0) {
                      dqContent.push("\"");
                      j += 1;
                      break;
                    } else {
                      dqContent.push(inner[j]);
                      j += 1;
                    }
                  }
                }
              }
            }
            normalized.push(dqContent.join(""));
            i = j;
          } else {
            if (ch === "\\" && i + 1 < inner.length) {
              if (inner[i + 1] === "\n") {
                i += 2;
              } else {
                inWhitespace = false;
                normalized.push(Substring(inner, i, i + 2));
                i += 2;
              }
            } else {
              var depth;
              if (IsExpansionStart(inner, i, "$((")) {
                inWhitespace = false;
                j = i + 3;
                depth = 1;
                while (j < inner.length && depth > 0) {
                  if (j + 1 < inner.length && inner[j] === "(" && inner[j + 1] === "(") {
                    depth += 1;
                    j += 2;
                  } else {
                    if (j + 1 < inner.length && inner[j] === ")" && inner[j + 1] === ")") {
                      depth -= 1;
                      j += 2;
                    } else {
                      j += 1;
                    }
                  }
                }
                normalized.push(Substring(inner, i, j));
                i = j;
              } else {
                if (IsExpansionStart(inner, i, "$(")) {
                  inWhitespace = false;
                  j = i + 2;
                  depth = 1;
                  while (j < inner.length && depth > 0) {
                    if (inner[j] === "(" && j > 0 && inner[j - 1] === "$") {
                      depth += 1;
                    } else {
                      if (inner[j] === ")") {
                        depth -= 1;
                      } else {
                        if (inner[j] === "'") {
                          j += 1;
                          while (j < inner.length && inner[j] !== "'") {
                            j += 1;
                          }
                        } else {
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
                } else {
                  if ((ch === "<" || ch === ">") && i + 1 < inner.length && inner[i + 1] === "(") {
                    inWhitespace = false;
                    j = i + 2;
                    depth = 1;
                    while (j < inner.length && depth > 0) {
                      if (inner[j] === "(") {
                        depth += 1;
                      } else {
                        if (inner[j] === ")") {
                          depth -= 1;
                        } else {
                          if (inner[j] === "'") {
                            j += 1;
                            while (j < inner.length && inner[j] !== "'") {
                              j += 1;
                            }
                          } else {
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
                  } else {
                    if (IsExpansionStart(inner, i, "${")) {
                      inWhitespace = false;
                      normalized.push("${");
                      braceDepth += 1;
                      i += 2;
                    } else {
                      if (ch === "{" && braceDepth > 0) {
                        normalized.push(ch);
                        braceDepth += 1;
                        i += 1;
                      } else {
                        if (ch === "}" && braceDepth > 0) {
                          normalized.push(ch);
                          braceDepth -= 1;
                          i += 1;
                        } else {
                          if (ch === "#" && braceDepth === 0 && inWhitespace) {
                            while (i < inner.length && inner[i] !== "\n") {
                              i += 1;
                            }
                          } else {
                            if (ch === "[") {
                              if (inWhitespace || bracketDepth > 0) {
                                bracketDepth += 1;
                              }
                              inWhitespace = false;
                              normalized.push(ch);
                              i += 1;
                            } else {
                              if (ch === "]" && bracketDepth > 0) {
                                normalized.push(ch);
                                bracketDepth -= 1;
                                i += 1;
                              } else {
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
  }

  StripArithLineContinuations(value) {
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
          } else {
            if (value[i] === ")") {
              if (depth === 2) {
                firstCloseIdx = arithContent.length;
              }
              depth -= 1;
              if (depth > 0) {
                arithContent.push(")");
              }
              i += 1;
            } else {
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
                } else {
                  i += 2;
                }
                if (depth === 1) {
                  firstCloseIdx = -1;
                }
              } else {
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
            var closing = (depth === 0 ? "))" : ")");
            result.push("$((" + content + closing);
          } else {
            result.push("$((" + content + ")");
          }
        } else {
          result.push(Substring(value, start, i));
        }
      } else {
        result.push(value[i]);
        i += 1;
      }
    }
    return result.join("");
  }

  CollectCmdsubs(node) {
    var result = [];
    if (node instanceof CommandSubstitution) {
      result.push(node);
    } else if (node instanceof ArrayName) {
      for (const elem of node.elements) {
        for (const p of elem.parts) {
          if (p instanceof CommandSubstitution) {
            result.push(p);
          } else {
            result.push(...this.CollectCmdsubs(p));
          }
        }
      }
    } else if (node instanceof ArithmeticExpansion) {
      if (node.expression !== null) {
        result.push(...this.CollectCmdsubs(node.expression));
      }
    } else if (node instanceof ArithBinaryOp) {
      result.push(...this.CollectCmdsubs(node.left));
      result.push(...this.CollectCmdsubs(node.right));
    } else if (node instanceof ArithComma) {
      result.push(...this.CollectCmdsubs(node.left));
      result.push(...this.CollectCmdsubs(node.right));
    } else if (node instanceof ArithUnaryOp) {
      result.push(...this.CollectCmdsubs(node.operand));
    } else if (node instanceof ArithPreIncr) {
      result.push(...this.CollectCmdsubs(node.operand));
    } else if (node instanceof ArithPostIncr) {
      result.push(...this.CollectCmdsubs(node.operand));
    } else if (node instanceof ArithPreDecr) {
      result.push(...this.CollectCmdsubs(node.operand));
    } else if (node instanceof ArithPostDecr) {
      result.push(...this.CollectCmdsubs(node.operand));
    } else if (node instanceof ArithTernary) {
      result.push(...this.CollectCmdsubs(node.condition));
      result.push(...this.CollectCmdsubs(node.ifTrue));
      result.push(...this.CollectCmdsubs(node.ifFalse));
    } else if (node instanceof ArithAssign) {
      result.push(...this.CollectCmdsubs(node.target));
      result.push(...this.CollectCmdsubs(node.value));
    }
    return result;
  }

  CollectProcsubs(node) {
    var result = [];
    if (node instanceof ProcessSubstitution) {
      result.push(node);
    } else if (node instanceof ArrayName) {
      for (const elem of node.elements) {
        for (const p of elem.parts) {
          if (p instanceof ProcessSubstitution) {
            result.push(p);
          } else {
            result.push(...this.CollectProcsubs(p));
          }
        }
      }
    }
    return result;
  }

  FormatCommandSubstitutions(value, inArith) {
    var cmdsubParts = [];
    var procsubParts = [];
    var hasArith = false;
    for (const p of this.parts) {
      if (p instanceof CommandSubstitution) {
        cmdsubParts.push(p);
      } else if (p instanceof ProcessSubstitution) {
        procsubParts.push(p);
      } else if (p instanceof ArithmeticExpansion) {
        hasArith = true;
      } else {
        cmdsubParts.push(...this.CollectCmdsubs(p));
        procsubParts.push(...this.CollectProcsubs(p));
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
      } else {
        if (value[idx] === "'" && !scanQuote.double) {
          idx += 1;
          while (idx < value.length && value[idx] !== "'") {
            idx += 1;
          }
          if (idx < value.length) {
            idx += 1;
          }
        } else {
          if (StartsWithAt(value, idx, "$(") && !StartsWithAt(value, idx, "$((") && !IsBackslashEscaped(value, idx) && !IsDollarDollarParen(value, idx)) {
            hasUntrackedCmdsub = true;
            break;
          } else {
            if ((StartsWithAt(value, idx, "<(") || StartsWithAt(value, idx, ">(")) && !scanQuote.double) {
              if (idx === 0 || !/^[a-zA-Z0-9]+$/.test(value[idx - 1]) && !"\"'".includes(value[idx - 1])) {
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
        } else {
          if (value[i] === ")") {
            arithParenDepth -= 1;
            result.push(value[i]);
            i += 1;
            continue;
          }
        }
      }
      var j;
      if (IsExpansionStart(value, i, "$((") && !hasArith) {
        j = FindCmdsubEnd(value, i + 2);
        result.push(Substring(value, i, j));
        if (cmdsubIdx < cmdsubParts.length) {
          cmdsubIdx += 1;
        }
        i = j;
        continue;
      }
      var inner;
      var node;
      var formatted;
      var parser;
      var parsed;
      if (StartsWithAt(value, i, "$(") && !StartsWithAt(value, i, "$((") && !IsBackslashEscaped(value, i) && !IsDollarDollarParen(value, i)) {
        j = FindCmdsubEnd(value, i + 2);
        if (extglobDepth > 0) {
          result.push(Substring(value, i, j));
          if (cmdsubIdx < cmdsubParts.length) {
            cmdsubIdx += 1;
          }
          i = j;
          continue;
        }
        inner = Substring(value, i + 2, j - 1);
        if (cmdsubIdx < cmdsubParts.length) {
          node = cmdsubParts[cmdsubIdx];
          formatted = FormatCmdsubNode(node.command, 0, false, false, false);
          cmdsubIdx += 1;
        } else {
          try {
            parser = newParser(inner, false, false);
            parsed = parser.parseList(true);
            formatted = (parsed !== null ? FormatCmdsubNode(parsed, 0, false, false, false) : "");
          } catch (_e) {
            formatted = inner;
          }
        }
        if (formatted.startsWith("(")) {
          result.push("$( " + formatted + ")");
        } else {
          result.push("$(" + formatted + ")");
        }
        i = j;
      } else {
        if (value[i] === "`" && cmdsubIdx < cmdsubParts.length) {
          j = i + 1;
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
        } else {
          var prefix;
          if (IsExpansionStart(value, i, "${") && i + 2 < value.length && IsFunsubChar(value[i + 2]) && !IsBackslashEscaped(value, i)) {
            j = FindFunsubEnd(value, i + 2);
            var cmdsubNode = (cmdsubIdx < cmdsubParts.length ? cmdsubParts[cmdsubIdx] : null);
            if (cmdsubNode instanceof CommandSubstitution && cmdsubNode.brace) {
              node = cmdsubNode;
              formatted = FormatCmdsubNode(node.command, 0, false, false, false);
              var hasPipe = value[i + 2] === "|";
              prefix = (hasPipe ? "${|" : "${ ");
              var origInner = Substring(value, i + 2, j - 1);
              var endsWithNewline = origInner.endsWith("\n");
              var suffix;
              if (!(formatted.length > 0) || /^\s+$/.test(formatted)) {
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
              result.push(prefix + formatted + suffix);
              cmdsubIdx += 1;
            } else {
              result.push(Substring(value, i, j));
            }
            i = j;
          } else {
            if ((StartsWithAt(value, i, ">(") || StartsWithAt(value, i, "<(")) && !mainQuote.double && deprecatedArithDepth === 0 && arithDepth === 0) {
              var isProcsub = i === 0 || !/^[a-zA-Z0-9]+$/.test(value[i - 1]) && !"\"'".includes(value[i - 1]);
              if (extglobDepth > 0) {
                j = FindCmdsubEnd(value, i + 2);
                result.push(Substring(value, i, j));
                if (procsubIdx < procsubParts.length) {
                  procsubIdx += 1;
                }
                i = j;
                continue;
              }
              var direction;
              var compact;
              var stripped;
              if (procsubIdx < procsubParts.length) {
                direction = value[i];
                j = FindCmdsubEnd(value, i + 2);
                node = procsubParts[procsubIdx];
                compact = StartsWithSubshell(node.command);
                formatted = FormatCmdsubNode(node.command, 0, true, compact, true);
                var rawContent = Substring(value, i + 2, j - 1);
                if (node.command.kind === "subshell") {
                  var leadingWsEnd = 0;
                  while (leadingWsEnd < rawContent.length && " \t\n".includes(rawContent[leadingWsEnd])) {
                    leadingWsEnd += 1;
                  }
                  var leadingWs = rawContent.slice(0, leadingWsEnd);
                  stripped = rawContent.slice(leadingWsEnd);
                  if (stripped.startsWith("(")) {
                    if ((leadingWs.length > 0)) {
                      var normalizedWs = leadingWs.replace(/\n/g, " ").replace(/\t/g, " ");
                      var spaced = FormatCmdsubNode(node.command, 0, false, false, false);
                      result.push(direction + "(" + normalizedWs + spaced + ")");
                    } else {
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
                } else {
                  var finalOutput = direction + "(" + formatted + ")";
                  result.push(finalOutput);
                }
                procsubIdx += 1;
                i = j;
              } else {
                if (isProcsub && (this.parts.length !== 0)) {
                  direction = value[i];
                  j = FindCmdsubEnd(value, i + 2);
                  if (j > value.length || j > 0 && j <= value.length && value[j - 1] !== ")") {
                    result.push(value[i]);
                    i += 1;
                    continue;
                  }
                  inner = Substring(value, i + 2, j - 1);
                  try {
                    parser = newParser(inner, false, false);
                    parsed = parser.parseList(true);
                    if (parsed !== null && parser.pos === inner.length && !inner.includes("\n")) {
                      compact = StartsWithSubshell(parsed);
                      formatted = FormatCmdsubNode(parsed, 0, true, compact, true);
                    } else {
                      formatted = inner;
                    }
                  } catch (_e) {
                    formatted = inner;
                  }
                  result.push(direction + "(" + formatted + ")");
                  i = j;
                } else {
                  if (isProcsub) {
                    direction = value[i];
                    j = FindCmdsubEnd(value, i + 2);
                    if (j > value.length || j > 0 && j <= value.length && value[j - 1] !== ")") {
                      result.push(value[i]);
                      i += 1;
                      continue;
                    }
                    inner = Substring(value, i + 2, j - 1);
                    if (inArith) {
                      result.push(direction + "(" + inner + ")");
                    } else {
                      if ((inner.trim().length > 0)) {
                        stripped = inner.replace(/^[ \t]+/, '');
                        result.push(direction + "(" + stripped + ")");
                      } else {
                        result.push(direction + "(" + inner + ")");
                      }
                    }
                    i = j;
                  } else {
                    result.push(value[i]);
                    i += 1;
                  }
                }
              }
            } else {
              var depth;
              if ((IsExpansionStart(value, i, "${ ") || IsExpansionStart(value, i, "${\t") || IsExpansionStart(value, i, "${\n") || IsExpansionStart(value, i, "${|")) && !IsBackslashEscaped(value, i)) {
                prefix = Substring(value, i, i + 3).replace(/\t/g, " ").replace(/\n/g, " ");
                j = i + 3;
                depth = 1;
                while (j < value.length && depth > 0) {
                  if (value[j] === "{") {
                    depth += 1;
                  } else {
                    if (value[j] === "}") {
                      depth -= 1;
                    }
                  }
                  j += 1;
                }
                inner = Substring(value, i + 2, j - 1);
                if (inner.trim() === "") {
                  result.push("${ }");
                } else {
                  try {
                    parser = newParser(inner.replace(/^[ \t\n|]+/, ''), false, false);
                    parsed = parser.parseList(true);
                    if (parsed !== null) {
                      formatted = FormatCmdsubNode(parsed, 0, false, false, false);
                      formatted = formatted.replace(/[;]+$/, '');
                      var terminator;
                      if (inner.replace(/[ \t]+$/, '').endsWith("\n")) {
                        terminator = "\n }";
                      } else {
                        if (formatted.endsWith(" &")) {
                          terminator = " }";
                        } else {
                          terminator = "; }";
                        }
                      }
                      result.push(prefix + formatted + terminator);
                    } else {
                      result.push("${ }");
                    }
                  } catch (_e) {
                    result.push(Substring(value, i, j));
                  }
                }
                i = j;
              } else {
                if (IsExpansionStart(value, i, "${") && !IsBackslashEscaped(value, i)) {
                  j = i + 2;
                  depth = 1;
                  var braceQuote = newQuoteState();
                  while (j < value.length && depth > 0) {
                    var c = value[j];
                    if (c === "\\" && j + 1 < value.length && !braceQuote.single) {
                      j += 2;
                      continue;
                    }
                    if (c === "'" && !braceQuote.double) {
                      braceQuote.single = !braceQuote.single;
                    } else {
                      if (c === "\"" && !braceQuote.single) {
                        braceQuote.double = !braceQuote.double;
                      } else {
                        if (!braceQuote.inQuotes()) {
                          if (IsExpansionStart(value, j, "$(") && !StartsWithAt(value, j, "$((")) {
                            j = FindCmdsubEnd(value, j + 2);
                            continue;
                          }
                          if (c === "{") {
                            depth += 1;
                          } else {
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
                    inner = Substring(value, i + 2, j);
                  } else {
                    inner = Substring(value, i + 2, j - 1);
                  }
                  var formattedInner = this.FormatCommandSubstitutions(inner, false);
                  formattedInner = this.NormalizeExtglobWhitespace(formattedInner);
                  if (depth === 0) {
                    result.push("${" + formattedInner + "}");
                  } else {
                    result.push("${" + formattedInner);
                  }
                  i = j;
                } else {
                  if (value[i] === "\"") {
                    mainQuote.double = !mainQuote.double;
                    result.push(value[i]);
                    i += 1;
                  } else {
                    if (value[i] === "'" && !mainQuote.double) {
                      j = i + 1;
                      while (j < value.length && value[j] !== "'") {
                        j += 1;
                      }
                      if (j < value.length) {
                        j += 1;
                      }
                      result.push(Substring(value, i, j));
                      i = j;
                    } else {
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
  }

  NormalizeExtglobWhitespace(value) {
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
            } else {
              if (value[i] === "(") {
                depth += 1;
                currentPart.push(value[i]);
                i += 1;
              } else {
                var partContent;
                if (value[i] === ")") {
                  depth -= 1;
                  if (depth === 0) {
                    partContent = currentPart.join("");
                    if (partContent.includes("<<")) {
                      patternParts.push(partContent);
                    } else {
                      if (hasPipe) {
                        patternParts.push(partContent.trim());
                      } else {
                        patternParts.push(partContent);
                      }
                    }
                    break;
                  }
                  currentPart.push(value[i]);
                  i += 1;
                } else {
                  if (value[i] === "|" && depth === 1) {
                    if (i + 1 < value.length && value[i + 1] === "|") {
                      currentPart.push("||");
                      i += 2;
                    } else {
                      hasPipe = true;
                      partContent = currentPart.join("");
                      if (partContent.includes("<<")) {
                        patternParts.push(partContent);
                      } else {
                        patternParts.push(partContent.trim());
                      }
                      currentPart = [];
                      i += 1;
                    }
                  } else {
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
  }

  getCondFormattedValue() {
    var value = this.ExpandAllAnsiCQuotes(this.value);
    value = this.StripLocaleStringDollars(value);
    value = this.FormatCommandSubstitutions(value, false);
    value = this.NormalizeExtglobWhitespace(value);
    value = value.replace(//g, "");
    return value.replace(/[\n]+$/, '');
  }

  getKind() {
    return this.kind;
  }
}

class Command {
  constructor(words = [], redirects = [], kind = "") {
    this.words = words ?? [];
    this.redirects = redirects ?? [];
    this.kind = kind;
  }

  toSexp() {
    var parts = [];
    parts.push(...this.words.map(w => w.toSexp()));
    parts.push(...this.redirects.map(r => r.toSexp()));
    var inner = parts.join(" ");
    if (!(inner.length > 0)) {
      return "(command)";
    }
    return "(command " + inner + ")";
  }

  getKind() {
    return this.kind;
  }
}

class Pipeline {
  constructor(commands = [], kind = "") {
    this.commands = commands ?? [];
    this.kind = kind;
  }

  toSexp() {
    if (this.commands.length === 1) {
      return this.commands[0].toSexp();
    }
    var cmds = [];
    var i = 0;
    var cmd;
    while (i < this.commands.length) {
      cmd = this.commands[i];
      if (cmd instanceof PipeBoth) {
        i += 1;
        continue;
      }
      var needsRedirect = i + 1 < this.commands.length && this.commands[i + 1].kind === "pipe-both";
      cmds.push([cmd, needsRedirect]);
      i += 1;
    }
    var pair;
    var needs;
    if (cmds.length === 1) {
      pair = cmds[0];
      cmd = pair[0];
      needs = pair[1];
      return this.CmdSexp(cmd, needs);
    }
    var lastPair = cmds[cmds.length - 1];
    var lastCmd = lastPair[0];
    var lastNeeds = lastPair[1];
    var result = this.CmdSexp(lastCmd, lastNeeds);
    var j = cmds.length - 2;
    while (j >= 0) {
      pair = cmds[j];
      cmd = pair[0];
      needs = pair[1];
      if (needs && cmd.kind !== "command") {
        result = "(pipe " + cmd.toSexp() + " (redirect \">&\" 1) " + result + ")";
      } else {
        result = "(pipe " + this.CmdSexp(cmd, needs) + " " + result + ")";
      }
      j -= 1;
    }
    return result;
  }

  CmdSexp(cmd, needsRedirect) {
    if (!needsRedirect) {
      return cmd.toSexp();
    }
    if (cmd instanceof Command) {
      var parts = [];
      parts.push(...cmd.words.map(w => w.toSexp()));
      parts.push(...cmd.redirects.map(r => r.toSexp()));
      parts.push("(redirect \">&\" 1)");
      return "(command " + parts.join(" ") + ")";
    }
    return cmd.toSexp();
  }

  getKind() {
    return this.kind;
  }
}

class List {
  constructor(parts = [], kind = "") {
    this.parts = parts ?? [];
    this.kind = kind;
  }

  toSexp() {
    var parts = this.parts.slice();
    var opNames = new Map([["&&", "and"], ["||", "or"], [";", "semi"], ["\n", "semi"], ["&", "background"]]);
    while (parts.length > 1 && parts[parts.length - 1].kind === "operator" && (parts[parts.length - 1].op === ";" || parts[parts.length - 1].op === "\n")) {
      parts = Sublist(parts, 0, parts.length - 1);
    }
    if (parts.length === 1) {
      return parts[0].toSexp();
    }
    if (parts[parts.length - 1].kind === "operator" && parts[parts.length - 1].op === "&") {
      for (var i = parts.length - 3; i > 0; i += -2) {
        if (parts[i].kind === "operator" && (parts[i].op === ";" || parts[i].op === "\n")) {
          var left = Sublist(parts, 0, i);
          var right = Sublist(parts, i + 1, parts.length - 1);
          var leftSexp;
          if (left.length > 1) {
            leftSexp = new List(left, "list").toSexp();
          } else {
            leftSexp = left[0].toSexp();
          }
          var rightSexp;
          if (right.length > 1) {
            rightSexp = new List(right, "list").toSexp();
          } else {
            rightSexp = right[0].toSexp();
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
  }

  ToSexpWithPrecedence(parts, opNames) {
    var semiPositions = [];
    for (var i = 0; i < parts.length; i += 1) {
      if (parts[i].kind === "operator" && (parts[i].op === ";" || parts[i].op === "\n")) {
        semiPositions.push(i);
      }
    }
    if ((semiPositions.length > 0)) {
      var segments = [];
      var start = 0;
      var seg;
      for (const pos of semiPositions) {
        seg = Sublist(parts, start, pos);
        if ((seg.length > 0) && seg[0].kind !== "operator") {
          segments.push(seg);
        }
        start = pos + 1;
      }
      seg = Sublist(parts, start, parts.length);
      if ((seg.length > 0) && seg[0].kind !== "operator") {
        segments.push(seg);
      }
      if (!(segments.length > 0)) {
        return "()";
      }
      var result = this.ToSexpAmpAndHigher(segments[0], opNames);
      for (var i = 1; i < segments.length; i += 1) {
        result = "(semi " + result + " " + this.ToSexpAmpAndHigher(segments[i], opNames) + ")";
      }
      return result;
    }
    return this.ToSexpAmpAndHigher(parts, opNames);
  }

  ToSexpAmpAndHigher(parts, opNames) {
    if (parts.length === 1) {
      return parts[0].toSexp();
    }
    var ampPositions = [];
    for (var i = 1; i < parts.length - 1; i += 2) {
      if (parts[i].kind === "operator" && parts[i].op === "&") {
        ampPositions.push(i);
      }
    }
    if ((ampPositions.length > 0)) {
      var segments = [];
      var start = 0;
      for (const pos of ampPositions) {
        segments.push(Sublist(parts, start, pos));
        start = pos + 1;
      }
      segments.push(Sublist(parts, start, parts.length));
      var result = this.ToSexpAndOr(segments[0], opNames);
      for (var i = 1; i < segments.length; i += 1) {
        result = "(background " + result + " " + this.ToSexpAndOr(segments[i], opNames) + ")";
      }
      return result;
    }
    return this.ToSexpAndOr(parts, opNames);
  }

  ToSexpAndOr(parts, opNames) {
    if (parts.length === 1) {
      return parts[0].toSexp();
    }
    var result = parts[0].toSexp();
    for (var i = 1; i < parts.length - 1; i += 2) {
      var op = parts[i];
      var cmd = parts[i + 1];
      var opName = opNames.get(op.op) ?? op.op;
      result = "(" + opName + " " + result + " " + cmd.toSexp() + ")";
    }
    return result;
  }

  getKind() {
    return this.kind;
  }
}

class Operator {
  constructor(op = "", kind = "") {
    this.op = op;
    this.kind = kind;
  }

  toSexp() {
    var names = new Map([["&&", "and"], ["||", "or"], [";", "semi"], ["&", "bg"], ["|", "pipe"]]);
    return ("(" + (names.get(this.op) ?? this.op)) + ")";
  }

  getKind() {
    return this.kind;
  }
}

class PipeBoth {
  constructor(kind = "") {
    this.kind = kind;
  }

  toSexp() {
    return "(pipe-both)";
  }

  getKind() {
    return this.kind;
  }
}

class Empty {
  constructor(kind = "") {
    this.kind = kind;
  }

  toSexp() {
    return "";
  }

  getKind() {
    return this.kind;
  }
}

class Comment {
  constructor(text = "", kind = "") {
    this.text = text;
    this.kind = kind;
  }

  toSexp() {
    return "";
  }

  getKind() {
    return this.kind;
  }
}

class Redirect {
  constructor(op = "", target = null, fd = null, kind = "") {
    this.op = op;
    this.target = target;
    this.fd = fd;
    this.kind = kind;
  }

  toSexp() {
    var op = this.op.replace(/^[0123456789]+/, '');
    if (op.startsWith("{")) {
      var j = 1;
      if (j < op.length && (/^[a-zA-Z]+$/.test(op[j]) || op[j] === "_")) {
        j += 1;
        while (j < op.length && (/^[a-zA-Z0-9]+$/.test(op[j]) || op[j] === "_")) {
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
      } else {
        if (op === "<") {
          op = "<&";
        }
      }
      var raw = Substring(targetVal, 1, targetVal.length);
      if (/^\d+$/.test(raw) && parseInt(raw, 10) <= 2147483647) {
        return "(redirect \"" + op + "\" " + String(parseInt(raw, 10)) + ")";
      }
      if (raw.endsWith("-") && /^\d+$/.test(raw.slice(0, raw.length - 1)) && parseInt(raw.slice(0, raw.length - 1), 10) <= 2147483647) {
        return "(redirect \"" + op + "\" " + String(parseInt(raw.slice(0, raw.length - 1), 10)) + ")";
      }
      if (targetVal === "&-") {
        return "(redirect \">&-\" 0)";
      }
      var fdTarget = (raw.endsWith("-") ? raw.slice(0, raw.length - 1) : raw);
      return "(redirect \"" + op + "\" \"" + fdTarget + "\")";
    }
    if (op === ">&" || op === "<&") {
      if (/^\d+$/.test(targetVal) && parseInt(targetVal, 10) <= 2147483647) {
        return "(redirect \"" + op + "\" " + String(parseInt(targetVal, 10)) + ")";
      }
      if (targetVal === "-") {
        return "(redirect \">&-\" 0)";
      }
      if (targetVal.endsWith("-") && /^\d+$/.test(targetVal.slice(0, targetVal.length - 1)) && parseInt(targetVal.slice(0, targetVal.length - 1), 10) <= 2147483647) {
        return "(redirect \"" + op + "\" " + String(parseInt(targetVal.slice(0, targetVal.length - 1), 10)) + ")";
      }
      var outVal = (targetVal.endsWith("-") ? targetVal.slice(0, targetVal.length - 1) : targetVal);
      return "(redirect \"" + op + "\" \"" + outVal + "\")";
    }
    return "(redirect \"" + op + "\" \"" + targetVal + "\")";
  }

  getKind() {
    return this.kind;
  }
}

class HereDoc {
  constructor(delimiter = "", content = "", stripTabs = false, quoted = false, fd = null, complete = false, StartPos = 0, kind = "") {
    this.delimiter = delimiter;
    this.content = content;
    this.stripTabs = stripTabs;
    this.quoted = quoted;
    this.fd = fd;
    this.complete = complete;
    this.StartPos = StartPos;
    this.kind = kind;
  }

  toSexp() {
    var op = (this.stripTabs ? "<<-" : "<<");
    var content = this.content;
    if (content.endsWith("\\") && !content.endsWith("\\\\")) {
      content = content + "\\";
    }
    return `(redirect "${op}" "${content}")`;
  }

  getKind() {
    return this.kind;
  }
}

class Subshell {
  constructor(body = null, redirects = [], kind = "") {
    this.body = body;
    this.redirects = redirects ?? [];
    this.kind = kind;
  }

  toSexp() {
    var base = "(subshell " + this.body.toSexp() + ")";
    return AppendRedirects(base, this.redirects);
  }

  getKind() {
    return this.kind;
  }
}

class BraceGroup {
  constructor(body = null, redirects = [], kind = "") {
    this.body = body;
    this.redirects = redirects ?? [];
    this.kind = kind;
  }

  toSexp() {
    var base = "(brace-group " + this.body.toSexp() + ")";
    return AppendRedirects(base, this.redirects);
  }

  getKind() {
    return this.kind;
  }
}

class If {
  constructor(condition = null, thenBody = null, elseBody = null, redirects = [], kind = "") {
    this.condition = condition;
    this.thenBody = thenBody;
    this.elseBody = elseBody;
    this.redirects = redirects ?? [];
    this.kind = kind;
  }

  toSexp() {
    var result = "(if " + this.condition.toSexp() + " " + this.thenBody.toSexp();
    if (this.elseBody !== null) {
      result = result + " " + this.elseBody.toSexp();
    }
    result = result + ")";
    for (const r of this.redirects) {
      result = result + " " + r.toSexp();
    }
    return result;
  }

  getKind() {
    return this.kind;
  }
}

class While {
  constructor(condition = null, body = null, redirects = [], kind = "") {
    this.condition = condition;
    this.body = body;
    this.redirects = redirects ?? [];
    this.kind = kind;
  }

  toSexp() {
    var base = "(while " + this.condition.toSexp() + " " + this.body.toSexp() + ")";
    return AppendRedirects(base, this.redirects);
  }

  getKind() {
    return this.kind;
  }
}

class Until {
  constructor(condition = null, body = null, redirects = [], kind = "") {
    this.condition = condition;
    this.body = body;
    this.redirects = redirects ?? [];
    this.kind = kind;
  }

  toSexp() {
    var base = "(until " + this.condition.toSexp() + " " + this.body.toSexp() + ")";
    return AppendRedirects(base, this.redirects);
  }

  getKind() {
    return this.kind;
  }
}

class For {
  constructor(varName = "", words = null, body = null, redirects = [], kind = "") {
    this.varName = varName;
    this.words = words;
    this.body = body;
    this.redirects = redirects ?? [];
    this.kind = kind;
  }

  toSexp() {
    var suffix = "";
    if ((this.redirects.length > 0)) {
      var redirectParts = [];
      redirectParts.push(...this.redirects.map(r => r.toSexp()));
      suffix = " " + redirectParts.join(" ");
    }
    var tempWord = new Word(this.varName, [], "word");
    var varFormatted = tempWord.FormatCommandSubstitutions(this.varName, false);
    var varEscaped = varFormatted.replace(/\\/g, "\\\\").replace(/"/g, "\\\"");
    if (this.words === null) {
      return "(for (word \"" + varEscaped + "\") (in (word \"\\\"$@\\\"\")) " + this.body.toSexp() + ")" + suffix;
    } else {
      if (this.words.length === 0) {
        return "(for (word \"" + varEscaped + "\") (in) " + this.body.toSexp() + ")" + suffix;
      } else {
        var wordParts = [];
        wordParts.push(...this.words.map(w => w.toSexp()));
        var wordStrs = wordParts.join(" ");
        return "(for (word \"" + varEscaped + "\") (in " + wordStrs + ") " + this.body.toSexp() + ")" + suffix;
      }
    }
  }

  getKind() {
    return this.kind;
  }
}

class ForArith {
  constructor(init = "", cond = "", incr = "", body = null, redirects = [], kind = "") {
    this.init = init;
    this.cond = cond;
    this.incr = incr;
    this.body = body;
    this.redirects = redirects ?? [];
    this.kind = kind;
  }

  toSexp() {
    var suffix = "";
    if ((this.redirects.length > 0)) {
      var redirectParts = [];
      redirectParts.push(...this.redirects.map(r => r.toSexp()));
      suffix = " " + redirectParts.join(" ");
    }
    var initVal = ((this.init.length > 0) ? this.init : "1");
    var condVal = ((this.cond.length > 0) ? this.cond : "1");
    var incrVal = ((this.incr.length > 0) ? this.incr : "1");
    var initStr = FormatArithVal(initVal);
    var condStr = FormatArithVal(condVal);
    var incrStr = FormatArithVal(incrVal);
    var bodyStr = this.body.toSexp();
    return `(arith-for (init (word "${initStr}")) (test (word "${condStr}")) (step (word "${incrStr}")) ${bodyStr})${suffix}`;
  }

  getKind() {
    return this.kind;
  }
}

class Select {
  constructor(varName = "", words = null, body = null, redirects = [], kind = "") {
    this.varName = varName;
    this.words = words;
    this.body = body;
    this.redirects = redirects ?? [];
    this.kind = kind;
  }

  toSexp() {
    var suffix = "";
    if ((this.redirects.length > 0)) {
      var redirectParts = [];
      redirectParts.push(...this.redirects.map(r => r.toSexp()));
      suffix = " " + redirectParts.join(" ");
    }
    var varEscaped = this.varName.replace(/\\/g, "\\\\").replace(/"/g, "\\\"");
    var inClause;
    if (this.words !== null) {
      var wordParts = [];
      wordParts.push(...this.words.map(w => w.toSexp()));
      var wordStrs = wordParts.join(" ");
      if ((this.words.length > 0)) {
        inClause = "(in " + wordStrs + ")";
      } else {
        inClause = "(in)";
      }
    } else {
      inClause = "(in (word \"\\\"$@\\\"\"))";
    }
    return "(select (word \"" + varEscaped + "\") " + inClause + " " + this.body.toSexp() + ")" + suffix;
  }

  getKind() {
    return this.kind;
  }
}

class Case {
  constructor(word = null, patterns = [], redirects = [], kind = "") {
    this.word = word;
    this.patterns = patterns ?? [];
    this.redirects = redirects ?? [];
    this.kind = kind;
  }

  toSexp() {
    var parts = [];
    parts.push("(case " + this.word.toSexp());
    parts.push(...this.patterns.map(p => p.toSexp()));
    var base = parts.join(" ") + ")";
    return AppendRedirects(base, this.redirects);
  }

  getKind() {
    return this.kind;
  }
}

class CasePattern {
  constructor(pattern = "", body = null, terminator = "", kind = "") {
    this.pattern = pattern;
    this.body = body;
    this.terminator = terminator;
    this.kind = kind;
  }

  toSexp() {
    var alternatives = [];
    var current = [];
    var i = 0;
    var depth = 0;
    while (i < this.pattern.length) {
      var ch = this.pattern[i];
      if (ch === "\\" && i + 1 < this.pattern.length) {
        current.push(Substring(this.pattern, i, i + 2));
        i += 2;
      } else {
        if ((ch === "@" || ch === "?" || ch === "*" || ch === "+" || ch === "!") && i + 1 < this.pattern.length && this.pattern[i + 1] === "(") {
          current.push(ch);
          current.push("(");
          depth += 1;
          i += 2;
        } else {
          if (IsExpansionStart(this.pattern, i, "$(")) {
            current.push(ch);
            current.push("(");
            depth += 1;
            i += 2;
          } else {
            if (ch === "(" && depth > 0) {
              current.push(ch);
              depth += 1;
              i += 1;
            } else {
              if (ch === ")" && depth > 0) {
                current.push(ch);
                depth -= 1;
                i += 1;
              } else {
                var result0;
                var result1;
                if (ch === "[") {
                  var [result0, result1, result2] = ConsumeBracketClass(this.pattern, i, depth);
                  i = result0;
                  current.push(...result1);
                } else {
                  if (ch === "'" && depth === 0) {
                    [result0, result1] = ConsumeSingleQuote(this.pattern, i);
                    i = result0;
                    current.push(...result1);
                  } else {
                    if (ch === "\"" && depth === 0) {
                      [result0, result1] = ConsumeDoubleQuote(this.pattern, i);
                      i = result0;
                      current.push(...result1);
                    } else {
                      if (ch === "|" && depth === 0) {
                        alternatives.push(current.join(""));
                        current = [];
                        i += 1;
                      } else {
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
    wordList.push(...alternatives.map(alt => new Word(alt, null, "word").toSexp()));
    var patternStr = wordList.join(" ");
    var parts = ["(pattern (" + patternStr + ")"];
    if (this.body !== null) {
      parts.push(" " + this.body.toSexp());
    } else {
      parts.push(" ()");
    }
    parts.push(")");
    return parts.join("");
  }

  getKind() {
    return this.kind;
  }
}

class FunctionName {
  constructor(name = "", body = null, kind = "") {
    this.name = name;
    this.body = body;
    this.kind = kind;
  }

  toSexp() {
    return "(function \"" + this.name + "\" " + this.body.toSexp() + ")";
  }

  getKind() {
    return this.kind;
  }
}

class ParamExpansion {
  constructor(param = "", op = "", arg = "", kind = "") {
    this.param = param;
    this.op = op;
    this.arg = arg;
    this.kind = kind;
  }

  toSexp() {
    var escapedParam = this.param.replace(/\\/g, "\\\\").replace(/"/g, "\\\"");
    if (this.op !== "") {
      var escapedOp = this.op.replace(/\\/g, "\\\\").replace(/"/g, "\\\"");
      var argVal;
      if (this.arg !== "") {
        argVal = this.arg;
      } else {
        argVal = "";
      }
      var escapedArg = argVal.replace(/\\/g, "\\\\").replace(/"/g, "\\\"");
      return "(param \"" + escapedParam + "\" \"" + escapedOp + "\" \"" + escapedArg + "\")";
    }
    return "(param \"" + escapedParam + "\")";
  }

  getKind() {
    return this.kind;
  }
}

class ParamLength {
  constructor(param = "", kind = "") {
    this.param = param;
    this.kind = kind;
  }

  toSexp() {
    var escaped = this.param.replace(/\\/g, "\\\\").replace(/"/g, "\\\"");
    return "(param-len \"" + escaped + "\")";
  }

  getKind() {
    return this.kind;
  }
}

class ParamIndirect {
  constructor(param = "", op = "", arg = "", kind = "") {
    this.param = param;
    this.op = op;
    this.arg = arg;
    this.kind = kind;
  }

  toSexp() {
    var escaped = this.param.replace(/\\/g, "\\\\").replace(/"/g, "\\\"");
    if (this.op !== "") {
      var escapedOp = this.op.replace(/\\/g, "\\\\").replace(/"/g, "\\\"");
      var argVal;
      if (this.arg !== "") {
        argVal = this.arg;
      } else {
        argVal = "";
      }
      var escapedArg = argVal.replace(/\\/g, "\\\\").replace(/"/g, "\\\"");
      return "(param-indirect \"" + escaped + "\" \"" + escapedOp + "\" \"" + escapedArg + "\")";
    }
    return "(param-indirect \"" + escaped + "\")";
  }

  getKind() {
    return this.kind;
  }
}

class CommandSubstitution {
  constructor(command = null, brace = false, kind = "") {
    this.command = command;
    this.brace = brace;
    this.kind = kind;
  }

  toSexp() {
    if (this.brace) {
      return "(funsub " + this.command.toSexp() + ")";
    }
    return "(cmdsub " + this.command.toSexp() + ")";
  }

  getKind() {
    return this.kind;
  }
}

class ArithmeticExpansion {
  constructor(expression = null, kind = "") {
    this.expression = expression;
    this.kind = kind;
  }

  toSexp() {
    if (this.expression === null) {
      return "(arith)";
    }
    return "(arith " + this.expression.toSexp() + ")";
  }

  getKind() {
    return this.kind;
  }
}

class ArithmeticCommand {
  constructor(expression = null, redirects = [], rawContent = "", kind = "") {
    this.expression = expression;
    this.redirects = redirects ?? [];
    this.rawContent = rawContent;
    this.kind = kind;
  }

  toSexp() {
    var formatted = new Word(this.rawContent, null, "word").FormatCommandSubstitutions(this.rawContent, true);
    var escaped = formatted.replace(/\\/g, "\\\\").replace(/"/g, "\\\"").replace(/\n/g, "\\n").replace(/\t/g, "\\t");
    var result = "(arith (word \"" + escaped + "\"))";
    if ((this.redirects.length > 0)) {
      var redirectParts = [];
      redirectParts.push(...this.redirects.map(r => r.toSexp()));
      var redirectSexps = redirectParts.join(" ");
      return result + " " + redirectSexps;
    }
    return result;
  }

  getKind() {
    return this.kind;
  }
}

class ArithNumber {
  constructor(value = "", kind = "") {
    this.value = value;
    this.kind = kind;
  }

  toSexp() {
    return "(number \"" + this.value + "\")";
  }

  getKind() {
    return this.kind;
  }
}

class ArithEmpty {
  constructor(kind = "") {
    this.kind = kind;
  }

  toSexp() {
    return "(empty)";
  }

  getKind() {
    return this.kind;
  }
}

class ArithVar {
  constructor(name = "", kind = "") {
    this.name = name;
    this.kind = kind;
  }

  toSexp() {
    return "(var \"" + this.name + "\")";
  }

  getKind() {
    return this.kind;
  }
}

class ArithBinaryOp {
  constructor(op = "", left = null, right = null, kind = "") {
    this.op = op;
    this.left = left;
    this.right = right;
    this.kind = kind;
  }

  toSexp() {
    return "(binary-op \"" + this.op + "\" " + this.left.toSexp() + " " + this.right.toSexp() + ")";
  }

  getKind() {
    return this.kind;
  }
}

class ArithUnaryOp {
  constructor(op = "", operand = null, kind = "") {
    this.op = op;
    this.operand = operand;
    this.kind = kind;
  }

  toSexp() {
    return "(unary-op \"" + this.op + "\" " + this.operand.toSexp() + ")";
  }

  getKind() {
    return this.kind;
  }
}

class ArithPreIncr {
  constructor(operand = null, kind = "") {
    this.operand = operand;
    this.kind = kind;
  }

  toSexp() {
    return "(pre-incr " + this.operand.toSexp() + ")";
  }

  getKind() {
    return this.kind;
  }
}

class ArithPostIncr {
  constructor(operand = null, kind = "") {
    this.operand = operand;
    this.kind = kind;
  }

  toSexp() {
    return "(post-incr " + this.operand.toSexp() + ")";
  }

  getKind() {
    return this.kind;
  }
}

class ArithPreDecr {
  constructor(operand = null, kind = "") {
    this.operand = operand;
    this.kind = kind;
  }

  toSexp() {
    return "(pre-decr " + this.operand.toSexp() + ")";
  }

  getKind() {
    return this.kind;
  }
}

class ArithPostDecr {
  constructor(operand = null, kind = "") {
    this.operand = operand;
    this.kind = kind;
  }

  toSexp() {
    return "(post-decr " + this.operand.toSexp() + ")";
  }

  getKind() {
    return this.kind;
  }
}

class ArithAssign {
  constructor(op = "", target = null, value = null, kind = "") {
    this.op = op;
    this.target = target;
    this.value = value;
    this.kind = kind;
  }

  toSexp() {
    return "(assign \"" + this.op + "\" " + this.target.toSexp() + " " + this.value.toSexp() + ")";
  }

  getKind() {
    return this.kind;
  }
}

class ArithTernary {
  constructor(condition = null, ifTrue = null, ifFalse = null, kind = "") {
    this.condition = condition;
    this.ifTrue = ifTrue;
    this.ifFalse = ifFalse;
    this.kind = kind;
  }

  toSexp() {
    return "(ternary " + this.condition.toSexp() + " " + this.ifTrue.toSexp() + " " + this.ifFalse.toSexp() + ")";
  }

  getKind() {
    return this.kind;
  }
}

class ArithComma {
  constructor(left = null, right = null, kind = "") {
    this.left = left;
    this.right = right;
    this.kind = kind;
  }

  toSexp() {
    return "(comma " + this.left.toSexp() + " " + this.right.toSexp() + ")";
  }

  getKind() {
    return this.kind;
  }
}

class ArithSubscript {
  constructor(array = "", index = null, kind = "") {
    this.array = array;
    this.index = index;
    this.kind = kind;
  }

  toSexp() {
    return "(subscript \"" + this.array + "\" " + this.index.toSexp() + ")";
  }

  getKind() {
    return this.kind;
  }
}

class ArithEscape {
  constructor(char = "", kind = "") {
    this.char = char;
    this.kind = kind;
  }

  toSexp() {
    return "(escape \"" + this.char + "\")";
  }

  getKind() {
    return this.kind;
  }
}

class ArithDeprecated {
  constructor(expression = "", kind = "") {
    this.expression = expression;
    this.kind = kind;
  }

  toSexp() {
    var escaped = this.expression.replace(/\\/g, "\\\\").replace(/"/g, "\\\"").replace(/\n/g, "\\n");
    return "(arith-deprecated \"" + escaped + "\")";
  }

  getKind() {
    return this.kind;
  }
}

class ArithConcat {
  constructor(parts = [], kind = "") {
    this.parts = parts ?? [];
    this.kind = kind;
  }

  toSexp() {
    var sexps = [];
    sexps.push(...this.parts.map(p => p.toSexp()));
    return "(arith-concat " + sexps.join(" ") + ")";
  }

  getKind() {
    return this.kind;
  }
}

class AnsiCQuote {
  constructor(content = "", kind = "") {
    this.content = content;
    this.kind = kind;
  }

  toSexp() {
    var escaped = this.content.replace(/\\/g, "\\\\").replace(/"/g, "\\\"").replace(/\n/g, "\\n");
    return "(ansi-c \"" + escaped + "\")";
  }

  getKind() {
    return this.kind;
  }
}

class LocaleString {
  constructor(content = "", kind = "") {
    this.content = content;
    this.kind = kind;
  }

  toSexp() {
    var escaped = this.content.replace(/\\/g, "\\\\").replace(/"/g, "\\\"").replace(/\n/g, "\\n");
    return "(locale \"" + escaped + "\")";
  }

  getKind() {
    return this.kind;
  }
}

class ProcessSubstitution {
  constructor(direction = "", command = null, kind = "") {
    this.direction = direction;
    this.command = command;
    this.kind = kind;
  }

  toSexp() {
    return "(procsub \"" + this.direction + "\" " + this.command.toSexp() + ")";
  }

  getKind() {
    return this.kind;
  }
}

class Negation {
  constructor(pipeline = null, kind = "") {
    this.pipeline = pipeline;
    this.kind = kind;
  }

  toSexp() {
    if (this.pipeline === null) {
      return "(negation (command))";
    }
    return "(negation " + this.pipeline.toSexp() + ")";
  }

  getKind() {
    return this.kind;
  }
}

class Time {
  constructor(pipeline = null, posix = false, kind = "") {
    this.pipeline = pipeline;
    this.posix = posix;
    this.kind = kind;
  }

  toSexp() {
    if (this.pipeline === null) {
      if (this.posix) {
        return "(time -p (command))";
      } else {
        return "(time (command))";
      }
    }
    if (this.posix) {
      return "(time -p " + this.pipeline.toSexp() + ")";
    }
    return "(time " + this.pipeline.toSexp() + ")";
  }

  getKind() {
    return this.kind;
  }
}

class ConditionalExpr {
  constructor(body = null, redirects = [], kind = "") {
    this.body = body;
    this.redirects = redirects ?? [];
    this.kind = kind;
  }

  toSexp() {
    var body = this.body;
    var result;
    if (typeof body === 'string') {
      var escaped = body.replace(/\\/g, "\\\\").replace(/"/g, "\\\"").replace(/\n/g, "\\n");
      result = "(cond \"" + escaped + "\")";
    } else {
      result = "(cond " + body.toSexp() + ")";
    }
    if ((this.redirects.length > 0)) {
      var redirectParts = [];
      redirectParts.push(...this.redirects.map(r => r.toSexp()));
      var redirectSexps = redirectParts.join(" ");
      return result + " " + redirectSexps;
    }
    return result;
  }

  getKind() {
    return this.kind;
  }
}

class UnaryTest {
  constructor(op = "", operand = null, kind = "") {
    this.op = op;
    this.operand = operand;
    this.kind = kind;
  }

  toSexp() {
    var operandVal = this.operand.getCondFormattedValue();
    return "(cond-unary \"" + this.op + "\" (cond-term \"" + operandVal + "\"))";
  }

  getKind() {
    return this.kind;
  }
}

class BinaryTest {
  constructor(op = "", left = null, right = null, kind = "") {
    this.op = op;
    this.left = left;
    this.right = right;
    this.kind = kind;
  }

  toSexp() {
    var leftVal = this.left.getCondFormattedValue();
    var rightVal = this.right.getCondFormattedValue();
    return "(cond-binary \"" + this.op + "\" (cond-term \"" + leftVal + "\") (cond-term \"" + rightVal + "\"))";
  }

  getKind() {
    return this.kind;
  }
}

class CondAnd {
  constructor(left = null, right = null, kind = "") {
    this.left = left;
    this.right = right;
    this.kind = kind;
  }

  toSexp() {
    return "(cond-and " + this.left.toSexp() + " " + this.right.toSexp() + ")";
  }

  getKind() {
    return this.kind;
  }
}

class CondOr {
  constructor(left = null, right = null, kind = "") {
    this.left = left;
    this.right = right;
    this.kind = kind;
  }

  toSexp() {
    return "(cond-or " + this.left.toSexp() + " " + this.right.toSexp() + ")";
  }

  getKind() {
    return this.kind;
  }
}

class CondNot {
  constructor(operand = null, kind = "") {
    this.operand = operand;
    this.kind = kind;
  }

  toSexp() {
    return this.operand.toSexp();
  }

  getKind() {
    return this.kind;
  }
}

class CondParen {
  constructor(inner = null, kind = "") {
    this.inner = inner;
    this.kind = kind;
  }

  toSexp() {
    return "(cond-expr " + this.inner.toSexp() + ")";
  }

  getKind() {
    return this.kind;
  }
}

class ArrayName {
  constructor(elements = [], kind = "") {
    this.elements = elements ?? [];
    this.kind = kind;
  }

  toSexp() {
    if (!(this.elements.length > 0)) {
      return "(array)";
    }
    var parts = [];
    parts.push(...this.elements.map(e => e.toSexp()));
    var inner = parts.join(" ");
    return "(array " + inner + ")";
  }

  getKind() {
    return this.kind;
  }
}

class Coproc {
  constructor(command = null, name = "", kind = "") {
    this.command = command;
    this.name = name;
    this.kind = kind;
  }

  toSexp() {
    var name;
    if ((this.name.length > 0)) {
      name = this.name;
    } else {
      name = "COPROC";
    }
    return "(coproc \"" + name + "\" " + this.command.toSexp() + ")";
  }

  getKind() {
    return this.kind;
  }
}

class Parser {
  constructor(source = "", pos = 0, length = 0, PendingHeredocs = [], CmdsubHeredocEnd = 0, SawNewlineInSingleQuote = false, InProcessSub = false, Extglob = false, Ctx = null, Lexer = null, TokenHistory = [], ParserState = 0, DolbraceState = 0, EofToken = "", WordContext = 0, AtCommandStart = false, InArrayLiteral = false, InAssignBuiltin = false, ArithSrc = "", ArithPos = 0, ArithLen = 0) {
    this.source = source;
    this.pos = pos;
    this.length = length;
    this.PendingHeredocs = PendingHeredocs ?? [];
    this.CmdsubHeredocEnd = CmdsubHeredocEnd;
    this.SawNewlineInSingleQuote = SawNewlineInSingleQuote;
    this.InProcessSub = InProcessSub;
    this.Extglob = Extglob;
    this.Ctx = Ctx;
    this.Lexer = Lexer;
    this.TokenHistory = TokenHistory ?? [];
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

  SetState(flag) {
    this.ParserState = this.ParserState | flag;
  }

  ClearState(flag) {
    this.ParserState = this.ParserState & ~flag;
  }

  InState(flag) {
    return (this.ParserState & flag) !== 0;
  }

  SaveParserState() {
    return new SavedParserState(this.ParserState, this.DolbraceState, this.PendingHeredocs, this.Ctx.copyStack(), this.EofToken);
  }

  RestoreParserState(saved) {
    this.ParserState = saved.parserState;
    this.DolbraceState = saved.dolbraceState;
    this.EofToken = saved.eofToken;
    this.Ctx.restoreFrom(saved.ctxStack);
  }

  RecordToken(tok) {
    this.TokenHistory = [tok, this.TokenHistory[0], this.TokenHistory[1], this.TokenHistory[2]];
  }

  UpdateDolbraceForOp(op, hasParam) {
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
  }

  SyncLexer() {
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
  }

  SyncParser() {
    this.pos = this.Lexer.pos;
  }

  LexPeekToken() {
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
  }

  LexNextToken() {
    var tok;
    if (this.Lexer.TokenCache !== null && this.Lexer.TokenCache.pos === this.pos && this.Lexer.CachedWordContext === this.WordContext && this.Lexer.CachedAtCommandStart === this.AtCommandStart && this.Lexer.CachedInArrayLiteral === this.InArrayLiteral && this.Lexer.CachedInAssignBuiltin === this.InAssignBuiltin) {
      tok = this.Lexer.nextToken();
      this.pos = this.Lexer.PostReadPos;
      this.Lexer.pos = this.Lexer.PostReadPos;
    } else {
      this.SyncLexer();
      tok = this.Lexer.nextToken();
      this.Lexer.CachedWordContext = this.WordContext;
      this.Lexer.CachedAtCommandStart = this.AtCommandStart;
      this.Lexer.CachedInArrayLiteral = this.InArrayLiteral;
      this.Lexer.CachedInAssignBuiltin = this.InAssignBuiltin;
      this.SyncParser();
    }
    this.RecordToken(tok);
    return tok;
  }

  LexSkipBlanks() {
    this.SyncLexer();
    this.Lexer.skipBlanks();
    this.SyncParser();
  }

  LexSkipComment() {
    this.SyncLexer();
    var result = this.Lexer.SkipComment();
    this.SyncParser();
    return result;
  }

  LexIsCommandTerminator() {
    var tok = this.LexPeekToken();
    var t = tok.type;
    return t === TokenType_EOF || t === TokenType_NEWLINE || t === TokenType_PIPE || t === TokenType_SEMI || t === TokenType_LPAREN || t === TokenType_RPAREN || t === TokenType_AMP;
  }

  LexPeekOperator() {
    var tok = this.LexPeekToken();
    var t = tok.type;
    if (t >= TokenType_SEMI && t <= TokenType_GREATER || t >= TokenType_AND_AND && t <= TokenType_PIPE_AMP) {
      return [t, tok.value];
    }
    return [0, ""];
  }

  LexPeekReservedWord() {
    var tok = this.LexPeekToken();
    if (tok.type !== TokenType_WORD) {
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
  }

  LexIsAtReservedWord(word) {
    var reserved = this.LexPeekReservedWord();
    return reserved === word;
  }

  LexConsumeWord(expected) {
    var tok = this.LexPeekToken();
    if (tok.type !== TokenType_WORD) {
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
  }

  LexPeekCaseTerminator() {
    var tok = this.LexPeekToken();
    var t = tok.type;
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
  }

  atEnd() {
    return this.pos >= this.length;
  }

  peek() {
    if (this.atEnd()) {
      return "";
    }
    return this.source[this.pos];
  }

  advance() {
    if (this.atEnd()) {
      return "";
    }
    var ch = this.source[this.pos];
    this.pos += 1;
    return ch;
  }

  peekAt(offset) {
    var pos = this.pos + offset;
    if (pos < 0 || pos >= this.length) {
      return "";
    }
    return this.source[pos];
  }

  lookahead(n) {
    return Substring(this.source, this.pos, this.pos + n);
  }

  IsBangFollowedByProcsub() {
    if (this.pos + 2 >= this.length) {
      return false;
    }
    var nextChar = this.source[this.pos + 1];
    if (nextChar !== ">" && nextChar !== "<") {
      return false;
    }
    return this.source[this.pos + 2] === "(";
  }

  skipWhitespace() {
    while (!this.atEnd()) {
      this.LexSkipBlanks();
      if (this.atEnd()) {
        break;
      }
      var ch = this.peek();
      if (ch === "#") {
        this.LexSkipComment();
      } else {
        if (ch === "\\" && this.peekAt(1) === "\n") {
          this.advance();
          this.advance();
        } else {
          break;
        }
      }
    }
  }

  skipWhitespaceAndNewlines() {
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
      } else {
        if (ch === "#") {
          while (!this.atEnd() && this.peek() !== "\n") {
            this.advance();
          }
        } else {
          if (ch === "\\" && this.peekAt(1) === "\n") {
            this.advance();
            this.advance();
          } else {
            break;
          }
        }
      }
    }
  }

  AtListTerminatingBracket() {
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
  }

  AtEofToken() {
    if (this.EofToken === "") {
      return false;
    }
    var tok = this.LexPeekToken();
    if (this.EofToken === ")") {
      return tok.type === TokenType_RPAREN;
    }
    if (this.EofToken === "}") {
      return tok.type === TokenType_WORD && tok.value === "}";
    }
    return false;
  }

  CollectRedirects() {
    var redirects = [];
    while (true) {
      this.skipWhitespace();
      var redirect = this.parseRedirect();
      if (redirect === null) {
        break;
      }
      redirects.push(redirect);
    }
    return ((redirects.length > 0) ? redirects : null);
  }

  ParseLoopBody(context) {
    if (this.peek() === "{") {
      var brace = this.parseBraceGroup();
      if (brace === null) {
        throw new ParseError(`${`Expected brace group body in ${context}`} at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
      }
      return brace.body;
    }
    if (this.LexConsumeWord("do")) {
      var body = this.parseListUntil(new Set(["done"]));
      if (body === null) {
        throw new ParseError(`Expected commands after 'do' at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
      }
      this.skipWhitespaceAndNewlines();
      if (!this.LexConsumeWord("done")) {
        throw new ParseError(`${`Expected 'done' to close ${context}`} at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
      }
      return body;
    }
    throw new ParseError(`${`Expected 'do' or '{' in ${context}`} at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
  }

  peekWord() {
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
    var word;
    if ((chars.length > 0)) {
      word = chars.join("");
    } else {
      word = "";
    }
    this.pos = savedPos;
    return word;
  }

  consumeWord(expected) {
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
    for (const _ of expected) {
      this.advance();
    }
    while (this.peek() === "\\" && this.pos + 1 < this.length && this.source[this.pos + 1] === "\n") {
      this.advance();
      this.advance();
    }
    return true;
  }

  IsWordTerminator(ctx, ch, bracketDepth, parenDepth) {
    this.SyncLexer();
    return this.Lexer.IsWordTerminator(ctx, ch, bracketDepth, parenDepth);
  }

  ScanDoubleQuote(chars, parts, start, handleLineContinuation) {
    chars.push("\"");
    while (!this.atEnd() && this.peek() !== "\"") {
      var c = this.peek();
      if (c === "\\" && this.pos + 1 < this.length) {
        var nextC = this.source[this.pos + 1];
        if (handleLineContinuation && nextC === "\n") {
          this.advance();
          this.advance();
        } else {
          chars.push(this.advance());
          chars.push(this.advance());
        }
      } else {
        if (c === "$") {
          if (!this.ParseDollarExpansion(chars, parts, true)) {
            chars.push(this.advance());
          }
        } else {
          chars.push(this.advance());
        }
      }
    }
    if (this.atEnd()) {
      throw new ParseError(`Unterminated double quote at position ${start}`, start)
    }
    chars.push(this.advance());
  }

  ParseDollarExpansion(chars, parts, inDquote) {
    var result0;
    var result1;
    if (this.pos + 2 < this.length && this.source[this.pos + 1] === "(" && this.source[this.pos + 2] === "(") {
      [result0, result1] = this.ParseArithmeticExpansion();
      if (result0 !== null) {
        parts.push(result0);
        chars.push(result1);
        return true;
      }
      [result0, result1] = this.ParseCommandSubstitution();
      if (result0 !== null) {
        parts.push(result0);
        chars.push(result1);
        return true;
      }
      return false;
    }
    if (this.pos + 1 < this.length && this.source[this.pos + 1] === "[") {
      [result0, result1] = this.ParseDeprecatedArithmetic();
      if (result0 !== null) {
        parts.push(result0);
        chars.push(result1);
        return true;
      }
      return false;
    }
    if (this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
      [result0, result1] = this.ParseCommandSubstitution();
      if (result0 !== null) {
        parts.push(result0);
        chars.push(result1);
        return true;
      }
      return false;
    }
    [result0, result1] = this.ParseParamExpansion(inDquote);
    if (result0 !== null) {
      parts.push(result0);
      chars.push(result1);
      return true;
    }
    return false;
  }

  ParseWordInternal(ctx, atCommandStart, inArrayLiteral) {
    this.WordContext = ctx;
    return this.parseWord(atCommandStart, inArrayLiteral, false);
  }

  parseWord(atCommandStart, inArrayLiteral, inAssignBuiltin) {
    this.skipWhitespace();
    if (this.atEnd()) {
      return null;
    }
    this.AtCommandStart = atCommandStart;
    this.InArrayLiteral = inArrayLiteral;
    this.InAssignBuiltin = inAssignBuiltin;
    var tok = this.LexPeekToken();
    if (tok.type !== TokenType_WORD) {
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
  }

  ParseCommandSubstitution() {
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
    return [new CommandSubstitution(cmd, null, "cmdsub"), text];
  }

  ParseFunsub(start) {
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
      throw new MatchedPairError()
    }
    this.advance();
    var text = Substring(this.source, start, this.pos);
    this.RestoreParserState(saved);
    this.SyncLexer();
    return [new CommandSubstitution(cmd, true, "cmdsub"), text];
  }

  IsAssignmentWord(word) {
    return Assignment(word.value, 0) !== -1;
  }

  ParseBacktickSubstitution() {
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
    var ch;
    while (!this.atEnd() && (inHeredocBody || this.peek() !== "`")) {
      if (inHeredocBody) {
        var lineStart = this.pos;
        var lineEnd = lineStart;
        while (lineEnd < this.length && this.source[lineEnd] !== "\n") {
          lineEnd += 1;
        }
        var line = Substring(this.source, lineStart, lineEnd);
        var checkLine = (currentHeredocStrip ? line.replace(/^[\t]+/, '') : line);
        if (checkLine === currentHeredocDelim) {
          for (const ch of line) {
            contentChars.push(ch);
            textChars.push(ch);
          }
          this.pos = lineEnd;
          if (this.pos < this.length && this.source[this.pos] === "\n") {
            contentChars.push("\n");
            textChars.push("\n");
            this.advance();
          }
          inHeredocBody = false;
          if (pendingHeredocs.length > 0) {
            [currentHeredocDelim, currentHeredocStrip] = pendingHeredocs.shift();
            inHeredocBody = true;
          }
        } else {
          if (checkLine.startsWith(currentHeredocDelim) && checkLine.length > currentHeredocDelim.length) {
            var tabsStripped = line.length - checkLine.length;
            var endPos = tabsStripped + currentHeredocDelim.length;
            for (var i = 0; i < endPos; i += 1) {
              contentChars.push(line[i]);
              textChars.push(line[i]);
            }
            this.pos = lineStart + endPos;
            inHeredocBody = false;
            if (pendingHeredocs.length > 0) {
              [currentHeredocDelim, currentHeredocStrip] = pendingHeredocs.shift();
              inHeredocBody = true;
            }
          } else {
            for (const ch of line) {
              contentChars.push(ch);
              textChars.push(ch);
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
        } else {
          if (IsEscapeCharInBacktick(nextC)) {
            this.advance();
            var escaped = this.advance();
            contentChars.push(escaped);
            textChars.push("\\");
            textChars.push(escaped);
          } else {
            ch = this.advance();
            contentChars.push(ch);
            textChars.push(ch);
          }
        }
        continue;
      }
      if (c === "<" && this.pos + 1 < this.length && this.source[this.pos + 1] === "<") {
        var quote;
        if (this.pos + 2 < this.length && this.source[this.pos + 2] === "<") {
          contentChars.push(this.advance());
          textChars.push("<");
          contentChars.push(this.advance());
          textChars.push("<");
          contentChars.push(this.advance());
          textChars.push("<");
          while (!this.atEnd() && IsWhitespaceNoNewline(this.peek())) {
            ch = this.advance();
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
            } else {
              if ("\"'".includes(this.peek())) {
                quote = this.peek();
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
              } else {
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
          ch = this.advance();
          contentChars.push(ch);
          textChars.push(ch);
        }
        var delimiterChars = [];
        if (!this.atEnd()) {
          ch = this.peek();
          var dch;
          var closing;
          if (IsQuote(ch)) {
            quote = this.advance();
            contentChars.push(quote);
            textChars.push(quote);
            while (!this.atEnd() && this.peek() !== quote) {
              dch = this.advance();
              contentChars.push(dch);
              textChars.push(dch);
              delimiterChars.push(dch);
            }
            if (!this.atEnd()) {
              closing = this.advance();
              contentChars.push(closing);
              textChars.push(closing);
            }
          } else {
            var esc;
            if (ch === "\\") {
              esc = this.advance();
              contentChars.push(esc);
              textChars.push(esc);
              if (!this.atEnd()) {
                dch = this.advance();
                contentChars.push(dch);
                textChars.push(dch);
                delimiterChars.push(dch);
              }
              while (!this.atEnd() && !IsMetachar(this.peek())) {
                dch = this.advance();
                contentChars.push(dch);
                textChars.push(dch);
                delimiterChars.push(dch);
              }
            } else {
              while (!this.atEnd() && !IsMetachar(this.peek()) && this.peek() !== "`") {
                ch = this.peek();
                if (IsQuote(ch)) {
                  quote = this.advance();
                  contentChars.push(quote);
                  textChars.push(quote);
                  while (!this.atEnd() && this.peek() !== quote) {
                    dch = this.advance();
                    contentChars.push(dch);
                    textChars.push(dch);
                    delimiterChars.push(dch);
                  }
                  if (!this.atEnd()) {
                    closing = this.advance();
                    contentChars.push(closing);
                    textChars.push(closing);
                  }
                } else {
                  if (ch === "\\") {
                    esc = this.advance();
                    contentChars.push(esc);
                    textChars.push(esc);
                    if (!this.atEnd()) {
                      dch = this.advance();
                      contentChars.push(dch);
                      textChars.push(dch);
                      delimiterChars.push(dch);
                    }
                  } else {
                    dch = this.advance();
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
        if ((delimiter.length > 0)) {
          pendingHeredocs.push([delimiter, stripTabs]);
        }
        continue;
      }
      if (c === "\n") {
        ch = this.advance();
        contentChars.push(ch);
        textChars.push(ch);
        if (pendingHeredocs.length > 0) {
          [currentHeredocDelim, currentHeredocStrip] = pendingHeredocs.shift();
          inHeredocBody = true;
        }
        continue;
      }
      ch = this.advance();
      contentChars.push(ch);
      textChars.push(ch);
    }
    if (this.atEnd()) {
      throw new ParseError(`Unterminated backtick at position ${start}`, start)
    }
    this.advance();
    textChars.push("`");
    var text = textChars.join("");
    var content = contentChars.join("");
    if (pendingHeredocs.length > 0) {
      var [heredocStart, heredocEnd] = FindHeredocContentEnd(this.source, this.pos, pendingHeredocs);
      if (heredocEnd > heredocStart) {
        content = content + Substring(this.source, heredocStart, heredocEnd);
        if (this.CmdsubHeredocEnd === -1) {
          this.CmdsubHeredocEnd = heredocEnd;
        } else {
          this.CmdsubHeredocEnd = (this.CmdsubHeredocEnd > heredocEnd ? this.CmdsubHeredocEnd : heredocEnd);
        }
      }
    }
    var subParser = newParser(content, false, this.Extglob);
    var cmd = subParser.parseList(true);
    if (cmd === null) {
      cmd = new Empty("empty");
    }
    return [new CommandSubstitution(cmd, null, "cmdsub"), text];
  }

  ParseProcessSubstitution() {
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
        throw new ParseError(`Invalid process substitution at position ${start}`, start)
      }
      this.advance();
      var textEnd = this.pos;
      var text = Substring(this.source, start, textEnd);
      text = StripLineContinuationsCommentAware(text);
      this.RestoreParserState(saved);
      this.InProcessSub = oldInProcessSub;
      return [new ProcessSubstitution(direction, cmd, "procsub"), text];
    } catch (e) {
      this.RestoreParserState(saved);
      this.InProcessSub = oldInProcessSub;
      var contentStartChar = (start + 2 < this.length ? this.source[start + 2] : "");
      if (" \t\n".includes(contentStartChar)) {
        throw e
      }
      this.pos = start + 2;
      this.Lexer.pos = this.pos;
      this.Lexer.ParseMatchedPair("(", ")", 0, false);
      this.pos = this.Lexer.pos;
      var text = Substring(this.source, start, this.pos);
      text = StripLineContinuationsCommentAware(text);
      return [null, text];
    }
  }

  ParseArrayLiteral() {
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
        throw new ParseError(`Unterminated array literal at position ${start}`, start)
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
        throw new ParseError(`Expected word in array literal at position ${this.pos}`, this.pos)
      }
      elements.push(word);
    }
    if (this.atEnd() || this.peek() !== ")") {
      this.ClearState(ParserStateFlags_PST_COMPASSIGN);
      throw new ParseError(`Expected ) to close array literal at position ${this.pos}`, this.pos)
    }
    this.advance();
    var text = Substring(this.source, start, this.pos);
    this.ClearState(ParserStateFlags_PST_COMPASSIGN);
    return [new ArrayName(elements, "array"), text];
  }

  ParseArithmeticExpansion() {
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
      } else {
        if (c === "\"") {
          this.advance();
          while (!this.atEnd()) {
            if (this.peek() === "\\" && this.pos + 1 < this.length) {
              this.advance();
              this.advance();
            } else {
              if (this.peek() === "\"") {
                this.advance();
                break;
              } else {
                this.advance();
              }
            }
          }
        } else {
          if (c === "\\" && this.pos + 1 < this.length) {
            this.advance();
            this.advance();
          } else {
            if (c === "(") {
              depth += 1;
              this.advance();
            } else {
              if (c === ")") {
                if (depth === 2) {
                  firstClosePos = this.pos;
                }
                depth -= 1;
                if (depth === 0) {
                  break;
                }
                this.advance();
              } else {
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
        throw new MatchedPairError()
      }
      this.pos = start;
      return [null, ""];
    }
    var content;
    if (firstClosePos !== -1) {
      content = Substring(this.source, contentStart, firstClosePos);
    } else {
      content = Substring(this.source, contentStart, this.pos);
    }
    this.advance();
    var text = Substring(this.source, start, this.pos);
    var expr;
    try {
      expr = this.ParseArithExpr(content);
    } catch (_e) {
      this.pos = start;
      return [null, ""];
    }
    return [new ArithmeticExpansion(expr, "arith"), text];
  }

  ParseArithExpr(content) {
    var savedArithSrc = this.ArithSrc;
    var savedArithPos = this.ArithPos;
    var savedArithLen = this.ArithLen;
    var savedParserState = this.ParserState;
    this.SetState(ParserStateFlags_PST_ARITH);
    this.ArithSrc = content;
    this.ArithPos = 0;
    this.ArithLen = content.length;
    this.ArithSkipWs();
    var result;
    if (this.ArithAtEnd()) {
      result = null;
    } else {
      result = this.ArithParseComma();
    }
    this.ParserState = savedParserState;
    if (savedArithSrc !== "") {
      this.ArithSrc = savedArithSrc;
      this.ArithPos = savedArithPos;
      this.ArithLen = savedArithLen;
    }
    return result;
  }

  ArithAtEnd() {
    return this.ArithPos >= this.ArithLen;
  }

  ArithPeek(offset) {
    var pos = this.ArithPos + offset;
    if (pos >= this.ArithLen) {
      return "";
    }
    return this.ArithSrc[pos];
  }

  ArithAdvance() {
    if (this.ArithAtEnd()) {
      return "";
    }
    var c = this.ArithSrc[this.ArithPos];
    this.ArithPos += 1;
    return c;
  }

  ArithSkipWs() {
    while (!this.ArithAtEnd()) {
      var c = this.ArithSrc[this.ArithPos];
      if (IsWhitespace(c)) {
        this.ArithPos += 1;
      } else {
        if (c === "\\" && this.ArithPos + 1 < this.ArithLen && this.ArithSrc[this.ArithPos + 1] === "\n") {
          this.ArithPos += 2;
        } else {
          break;
        }
      }
    }
  }

  ArithMatch(s) {
    return StartsWithAt(this.ArithSrc, this.ArithPos, s);
  }

  ArithConsume(s) {
    if (this.ArithMatch(s)) {
      this.ArithPos += s.length;
      return true;
    }
    return false;
  }

  ArithParseComma() {
    var left = this.ArithParseAssign();
    while (true) {
      this.ArithSkipWs();
      if (this.ArithConsume(",")) {
        this.ArithSkipWs();
        var right = this.ArithParseAssign();
        left = new ArithComma(left, right, "comma");
      } else {
        break;
      }
    }
    return left;
  }

  ArithParseAssign() {
    var left = this.ArithParseTernary();
    this.ArithSkipWs();
    var assignOps = ["<<=", ">>=", "+=", "-=", "*=", "/=", "%=", "&=", "^=", "|=", "="];
    for (const op of assignOps) {
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
  }

  ArithParseTernary() {
    var cond = this.ArithParseLogicalOr();
    this.ArithSkipWs();
    if (this.ArithConsume("?")) {
      this.ArithSkipWs();
      var ifTrue;
      if (this.ArithMatch(":")) {
        ifTrue = null;
      } else {
        ifTrue = this.ArithParseAssign();
      }
      this.ArithSkipWs();
      var ifFalse;
      if (this.ArithConsume(":")) {
        this.ArithSkipWs();
        if (this.ArithAtEnd() || this.ArithPeek(0) === ")") {
          ifFalse = null;
        } else {
          ifFalse = this.ArithParseTernary();
        }
      } else {
        ifFalse = null;
      }
      return new ArithTernary(cond, ifTrue, ifFalse, "ternary");
    }
    return cond;
  }

  ArithParseLeftAssoc(ops, parsefn) {
    var left = parsefn();
    while (true) {
      this.ArithSkipWs();
      var matched = false;
      for (const op of ops) {
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
  }

  ArithParseLogicalOr() {
    return this.ArithParseLeftAssoc(["||"], this.ArithParseLogicalAnd.bind(this));
  }

  ArithParseLogicalAnd() {
    return this.ArithParseLeftAssoc(["&&"], this.ArithParseBitwiseOr.bind(this));
  }

  ArithParseBitwiseOr() {
    var left = this.ArithParseBitwiseXor();
    while (true) {
      this.ArithSkipWs();
      if (this.ArithPeek(0) === "|" && (this.ArithPeek(1) !== "|" && this.ArithPeek(1) !== "=")) {
        this.ArithAdvance();
        this.ArithSkipWs();
        var right = this.ArithParseBitwiseXor();
        left = new ArithBinaryOp("|", left, right, "binary-op");
      } else {
        break;
      }
    }
    return left;
  }

  ArithParseBitwiseXor() {
    var left = this.ArithParseBitwiseAnd();
    while (true) {
      this.ArithSkipWs();
      if (this.ArithPeek(0) === "^" && this.ArithPeek(1) !== "=") {
        this.ArithAdvance();
        this.ArithSkipWs();
        var right = this.ArithParseBitwiseAnd();
        left = new ArithBinaryOp("^", left, right, "binary-op");
      } else {
        break;
      }
    }
    return left;
  }

  ArithParseBitwiseAnd() {
    var left = this.ArithParseEquality();
    while (true) {
      this.ArithSkipWs();
      if (this.ArithPeek(0) === "&" && (this.ArithPeek(1) !== "&" && this.ArithPeek(1) !== "=")) {
        this.ArithAdvance();
        this.ArithSkipWs();
        var right = this.ArithParseEquality();
        left = new ArithBinaryOp("&", left, right, "binary-op");
      } else {
        break;
      }
    }
    return left;
  }

  ArithParseEquality() {
    return this.ArithParseLeftAssoc(["==", "!="], this.ArithParseComparison.bind(this));
  }

  ArithParseComparison() {
    var left = this.ArithParseShift();
    while (true) {
      this.ArithSkipWs();
      var right;
      if (this.ArithMatch("<=")) {
        this.ArithConsume("<=");
        this.ArithSkipWs();
        right = this.ArithParseShift();
        left = new ArithBinaryOp("<=", left, right, "binary-op");
      } else {
        if (this.ArithMatch(">=")) {
          this.ArithConsume(">=");
          this.ArithSkipWs();
          right = this.ArithParseShift();
          left = new ArithBinaryOp(">=", left, right, "binary-op");
        } else {
          if (this.ArithPeek(0) === "<" && (this.ArithPeek(1) !== "<" && this.ArithPeek(1) !== "=")) {
            this.ArithAdvance();
            this.ArithSkipWs();
            right = this.ArithParseShift();
            left = new ArithBinaryOp("<", left, right, "binary-op");
          } else {
            if (this.ArithPeek(0) === ">" && (this.ArithPeek(1) !== ">" && this.ArithPeek(1) !== "=")) {
              this.ArithAdvance();
              this.ArithSkipWs();
              right = this.ArithParseShift();
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

  ArithParseShift() {
    var left = this.ArithParseAdditive();
    while (true) {
      this.ArithSkipWs();
      if (this.ArithMatch("<<=")) {
        break;
      }
      if (this.ArithMatch(">>=")) {
        break;
      }
      var right;
      if (this.ArithMatch("<<")) {
        this.ArithConsume("<<");
        this.ArithSkipWs();
        right = this.ArithParseAdditive();
        left = new ArithBinaryOp("<<", left, right, "binary-op");
      } else {
        if (this.ArithMatch(">>")) {
          this.ArithConsume(">>");
          this.ArithSkipWs();
          right = this.ArithParseAdditive();
          left = new ArithBinaryOp(">>", left, right, "binary-op");
        } else {
          break;
        }
      }
    }
    return left;
  }

  ArithParseAdditive() {
    var left = this.ArithParseMultiplicative();
    while (true) {
      this.ArithSkipWs();
      var c = this.ArithPeek(0);
      var c2 = this.ArithPeek(1);
      var right;
      if (c === "+" && (c2 !== "+" && c2 !== "=")) {
        this.ArithAdvance();
        this.ArithSkipWs();
        right = this.ArithParseMultiplicative();
        left = new ArithBinaryOp("+", left, right, "binary-op");
      } else {
        if (c === "-" && (c2 !== "-" && c2 !== "=")) {
          this.ArithAdvance();
          this.ArithSkipWs();
          right = this.ArithParseMultiplicative();
          left = new ArithBinaryOp("-", left, right, "binary-op");
        } else {
          break;
        }
      }
    }
    return left;
  }

  ArithParseMultiplicative() {
    var left = this.ArithParseExponentiation();
    while (true) {
      this.ArithSkipWs();
      var c = this.ArithPeek(0);
      var c2 = this.ArithPeek(1);
      var right;
      if (c === "*" && (c2 !== "*" && c2 !== "=")) {
        this.ArithAdvance();
        this.ArithSkipWs();
        right = this.ArithParseExponentiation();
        left = new ArithBinaryOp("*", left, right, "binary-op");
      } else {
        if (c === "/" && c2 !== "=") {
          this.ArithAdvance();
          this.ArithSkipWs();
          right = this.ArithParseExponentiation();
          left = new ArithBinaryOp("/", left, right, "binary-op");
        } else {
          if (c === "%" && c2 !== "=") {
            this.ArithAdvance();
            this.ArithSkipWs();
            right = this.ArithParseExponentiation();
            left = new ArithBinaryOp("%", left, right, "binary-op");
          } else {
            break;
          }
        }
      }
    }
    return left;
  }

  ArithParseExponentiation() {
    var left = this.ArithParseUnary();
    this.ArithSkipWs();
    if (this.ArithMatch("**")) {
      this.ArithConsume("**");
      this.ArithSkipWs();
      var right = this.ArithParseExponentiation();
      return new ArithBinaryOp("**", left, right, "binary-op");
    }
    return left;
  }

  ArithParseUnary() {
    this.ArithSkipWs();
    var operand;
    if (this.ArithMatch("++")) {
      this.ArithConsume("++");
      this.ArithSkipWs();
      operand = this.ArithParseUnary();
      return new ArithPreIncr(operand, "pre-incr");
    }
    if (this.ArithMatch("--")) {
      this.ArithConsume("--");
      this.ArithSkipWs();
      operand = this.ArithParseUnary();
      return new ArithPreDecr(operand, "pre-decr");
    }
    var c = this.ArithPeek(0);
    if (c === "!") {
      this.ArithAdvance();
      this.ArithSkipWs();
      operand = this.ArithParseUnary();
      return new ArithUnaryOp("!", operand, "unary-op");
    }
    if (c === "~") {
      this.ArithAdvance();
      this.ArithSkipWs();
      operand = this.ArithParseUnary();
      return new ArithUnaryOp("~", operand, "unary-op");
    }
    if (c === "+" && this.ArithPeek(1) !== "+") {
      this.ArithAdvance();
      this.ArithSkipWs();
      operand = this.ArithParseUnary();
      return new ArithUnaryOp("+", operand, "unary-op");
    }
    if (c === "-" && this.ArithPeek(1) !== "-") {
      this.ArithAdvance();
      this.ArithSkipWs();
      operand = this.ArithParseUnary();
      return new ArithUnaryOp("-", operand, "unary-op");
    }
    return this.ArithParsePostfix();
  }

  ArithParsePostfix() {
    var left = this.ArithParsePrimary();
    while (true) {
      this.ArithSkipWs();
      if (this.ArithMatch("++")) {
        this.ArithConsume("++");
        left = new ArithPostIncr(left, "post-incr");
      } else {
        if (this.ArithMatch("--")) {
          this.ArithConsume("--");
          left = new ArithPostDecr(left, "post-decr");
        } else {
          if (this.ArithPeek(0) === "[") {
            if (left instanceof ArithVar) {
              this.ArithAdvance();
              this.ArithSkipWs();
              var index = this.ArithParseComma();
              this.ArithSkipWs();
              if (!this.ArithConsume("]")) {
                throw new ParseError(`Expected ']' in array subscript at position ${this.ArithPos}`, this.ArithPos)
              }
              left = new ArithSubscript(left.name, index, "subscript");
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

  ArithParsePrimary() {
    this.ArithSkipWs();
    var c = this.ArithPeek(0);
    if (c === "(") {
      this.ArithAdvance();
      this.ArithSkipWs();
      var expr = this.ArithParseComma();
      this.ArithSkipWs();
      if (!this.ArithConsume(")")) {
        throw new ParseError(`Expected ')' in arithmetic expression at position ${this.ArithPos}`, this.ArithPos)
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
        throw new ParseError(`Unexpected end after backslash in arithmetic at position ${this.ArithPos}`, this.ArithPos)
      }
      var escapedChar = this.ArithAdvance();
      return new ArithEscape(escapedChar, "escape");
    }
    if (this.ArithAtEnd() || ")]:,;?|&<>=!+-*/%^~#{}".includes(c)) {
      return new ArithEmpty("empty");
    }
    return this.ArithParseNumberOrVar();
  }

  ArithParseExpansion() {
    if (!this.ArithConsume("$")) {
      throw new ParseError(`Expected '\$' at position ${this.ArithPos}`, this.ArithPos)
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
      if (/^[a-zA-Z0-9]+$/.test(ch) || ch === "_") {
        nameChars.push(this.ArithAdvance());
      } else {
        if ((IsSpecialParamOrDigit(ch) || ch === "#") && !(nameChars.length > 0)) {
          nameChars.push(this.ArithAdvance());
          break;
        } else {
          break;
        }
      }
    }
    if (!(nameChars.length > 0)) {
      throw new ParseError(`Expected variable name after \$ at position ${this.ArithPos}`, this.ArithPos)
    }
    return new ParamExpansion(nameChars.join(""), null, null, "param");
  }

  ArithParseCmdsub() {
    this.ArithAdvance();
    var depth;
    var contentStart;
    var ch;
    var content;
    if (this.ArithPeek(0) === "(") {
      this.ArithAdvance();
      depth = 1;
      contentStart = this.ArithPos;
      while (!this.ArithAtEnd() && depth > 0) {
        ch = this.ArithPeek(0);
        if (ch === "(") {
          depth += 1;
          this.ArithAdvance();
        } else {
          if (ch === ")") {
            if (depth === 1 && this.ArithPeek(1) === ")") {
              break;
            }
            depth -= 1;
            this.ArithAdvance();
          } else {
            this.ArithAdvance();
          }
        }
      }
      content = Substring(this.ArithSrc, contentStart, this.ArithPos);
      this.ArithAdvance();
      this.ArithAdvance();
      var innerExpr = this.ParseArithExpr(content);
      return new ArithmeticExpansion(innerExpr, "arith");
    }
    depth = 1;
    contentStart = this.ArithPos;
    while (!this.ArithAtEnd() && depth > 0) {
      ch = this.ArithPeek(0);
      if (ch === "(") {
        depth += 1;
        this.ArithAdvance();
      } else {
        if (ch === ")") {
          depth -= 1;
          if (depth === 0) {
            break;
          }
          this.ArithAdvance();
        } else {
          this.ArithAdvance();
        }
      }
    }
    content = Substring(this.ArithSrc, contentStart, this.ArithPos);
    this.ArithAdvance();
    var subParser = newParser(content, false, this.Extglob);
    var cmd = subParser.parseList(true);
    return new CommandSubstitution(cmd, null, "cmdsub");
  }

  ArithParseBracedParam() {
    this.ArithAdvance();
    var nameChars;
    if (this.ArithPeek(0) === "!") {
      this.ArithAdvance();
      nameChars = [];
      while (!this.ArithAtEnd() && this.ArithPeek(0) !== "}") {
        nameChars.push(this.ArithAdvance());
      }
      this.ArithConsume("}");
      return new ParamIndirect(nameChars.join(""), null, null, "param-indirect");
    }
    if (this.ArithPeek(0) === "#") {
      this.ArithAdvance();
      nameChars = [];
      while (!this.ArithAtEnd() && this.ArithPeek(0) !== "}") {
        nameChars.push(this.ArithAdvance());
      }
      this.ArithConsume("}");
      return new ParamLength(nameChars.join(""), "param-len");
    }
    nameChars = [];
    var ch;
    while (!this.ArithAtEnd()) {
      ch = this.ArithPeek(0);
      if (ch === "}") {
        this.ArithAdvance();
        return new ParamExpansion(nameChars.join(""), null, null, "param");
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
      } else {
        if (ch === "}") {
          depth -= 1;
          if (depth === 0) {
            break;
          }
          opChars.push(this.ArithAdvance());
        } else {
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
  }

  ArithParseSingleQuote() {
    this.ArithAdvance();
    var contentStart = this.ArithPos;
    while (!this.ArithAtEnd() && this.ArithPeek(0) !== "'") {
      this.ArithAdvance();
    }
    var content = Substring(this.ArithSrc, contentStart, this.ArithPos);
    if (!this.ArithConsume("'")) {
      throw new ParseError(`Unterminated single quote in arithmetic at position ${this.ArithPos}`, this.ArithPos)
    }
    return new ArithNumber(content, "number");
  }

  ArithParseDoubleQuote() {
    this.ArithAdvance();
    var contentStart = this.ArithPos;
    while (!this.ArithAtEnd() && this.ArithPeek(0) !== "\"") {
      var c = this.ArithPeek(0);
      if (c === "\\" && !this.ArithAtEnd()) {
        this.ArithAdvance();
        this.ArithAdvance();
      } else {
        this.ArithAdvance();
      }
    }
    var content = Substring(this.ArithSrc, contentStart, this.ArithPos);
    if (!this.ArithConsume("\"")) {
      throw new ParseError(`Unterminated double quote in arithmetic at position ${this.ArithPos}`, this.ArithPos)
    }
    return new ArithNumber(content, "number");
  }

  ArithParseBacktick() {
    this.ArithAdvance();
    var contentStart = this.ArithPos;
    while (!this.ArithAtEnd() && this.ArithPeek(0) !== "`") {
      var c = this.ArithPeek(0);
      if (c === "\\" && !this.ArithAtEnd()) {
        this.ArithAdvance();
        this.ArithAdvance();
      } else {
        this.ArithAdvance();
      }
    }
    var content = Substring(this.ArithSrc, contentStart, this.ArithPos);
    if (!this.ArithConsume("`")) {
      throw new ParseError(`Unterminated backtick in arithmetic at position ${this.ArithPos}`, this.ArithPos)
    }
    var subParser = newParser(content, false, this.Extglob);
    var cmd = subParser.parseList(true);
    return new CommandSubstitution(cmd, null, "cmdsub");
  }

  ArithParseNumberOrVar() {
    this.ArithSkipWs();
    var chars = [];
    var c = this.ArithPeek(0);
    var ch;
    if (/^\d+$/.test(c)) {
      while (!this.ArithAtEnd()) {
        ch = this.ArithPeek(0);
        if (/^[a-zA-Z0-9]+$/.test(ch) || (ch === "#" || ch === "_")) {
          chars.push(this.ArithAdvance());
        } else {
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
    if (/^[a-zA-Z]+$/.test(c) || c === "_") {
      while (!this.ArithAtEnd()) {
        ch = this.ArithPeek(0);
        if (/^[a-zA-Z0-9]+$/.test(ch) || ch === "_") {
          chars.push(this.ArithAdvance());
        } else {
          break;
        }
      }
      return new ArithVar(chars.join(""), "var");
    }
    throw new ParseError(`${"Unexpected character '" + c + "' in arithmetic expression"} at position ${this.ArithPos}`, this.ArithPos)
  }

  ParseDeprecatedArithmetic() {
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
  }

  ParseParamExpansion(inDquote) {
    this.SyncLexer();
    var [result0, result1] = this.Lexer.ReadParamExpansion(inDquote);
    this.SyncParser();
    return [result0, result1];
  }

  parseRedirect() {
    this.skipWhitespace();
    if (this.atEnd()) {
      return null;
    }
    var start = this.pos;
    var fd = -1;
    var varfd = "";
    var ch;
    if (this.peek() === "{") {
      var saved = this.pos;
      this.advance();
      var varnameChars = [];
      var inBracket = false;
      while (!this.atEnd() && !IsRedirectChar(this.peek())) {
        ch = this.peek();
        if (ch === "}" && !inBracket) {
          break;
        } else {
          if (ch === "[") {
            inBracket = true;
            varnameChars.push(this.advance());
          } else {
            if (ch === "]") {
              inBracket = false;
              varnameChars.push(this.advance());
            } else {
              if (/^[a-zA-Z0-9]+$/.test(ch) || ch === "_") {
                varnameChars.push(this.advance());
              } else {
                if (inBracket && !IsMetachar(ch)) {
                  varnameChars.push(this.advance());
                } else {
                  break;
                }
              }
            }
          }
        }
      }
      var varname = varnameChars.join("");
      var isValidVarfd = false;
      if ((varname.length > 0)) {
        if (/^[a-zA-Z]+$/.test(varname[0]) || varname[0] === "_") {
          if (varname.includes("[") || varname.includes("]")) {
            var left = varname.indexOf("[");
            var right = varname.lastIndexOf("]");
            if (left !== -1 && right === varname.length - 1 && right > left + 1) {
              var base = varname.slice(0, left);
              if ((base.length > 0) && (/^[a-zA-Z]+$/.test(base[0]) || base[0] === "_")) {
                isValidVarfd = true;
                for (const c of base.slice(1)) {
                  if (!(/^[a-zA-Z0-9]+$/.test(c) || c === "_")) {
                    isValidVarfd = false;
                    break;
                  }
                }
              }
            }
          } else {
            isValidVarfd = true;
            for (const c of varname.slice(1)) {
              if (!(/^[a-zA-Z0-9]+$/.test(c) || c === "_")) {
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
      } else {
        this.pos = saved;
      }
    }
    var fdChars;
    if (varfd === "" && (this.peek().length > 0) && /^\d+$/.test(this.peek())) {
      fdChars = [];
      while (!this.atEnd() && /^\d+$/.test(this.peek())) {
        fdChars.push(this.advance());
      }
      fd = parseInt(fdChars.join(""), 10);
    }
    ch = this.peek();
    var op;
    var target;
    if (ch === "&" && this.pos + 1 < this.length && this.source[this.pos + 1] === ">") {
      if (fd !== -1 || varfd !== "") {
        this.pos = start;
        return null;
      }
      this.advance();
      this.advance();
      if (!this.atEnd() && this.peek() === ">") {
        this.advance();
        op = "&>>";
      } else {
        op = "&>";
      }
      this.skipWhitespace();
      target = this.parseWord(false, false, false);
      if (target === null) {
        throw new ParseError(`${"Expected target for redirect " + op} at position ${this.pos}`, this.pos)
      }
      return new Redirect(op, target, null, "redirect");
    }
    if (ch === "" || !IsRedirectChar(ch)) {
      this.pos = start;
      return null;
    }
    if (fd === -1 && this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
      this.pos = start;
      return null;
    }
    op = this.advance();
    var stripTabs = false;
    if (!this.atEnd()) {
      var nextCh = this.peek();
      if (op === ">" && nextCh === ">") {
        this.advance();
        op = ">>";
      } else {
        if (op === "<" && nextCh === "<") {
          this.advance();
          if (!this.atEnd() && this.peek() === "<") {
            this.advance();
            op = "<<<";
          } else {
            if (!this.atEnd() && this.peek() === "-") {
              this.advance();
              op = "<<";
              stripTabs = true;
            } else {
              op = "<<";
            }
          }
        } else {
          if (op === "<" && nextCh === ">") {
            this.advance();
            op = "<>";
          } else {
            if (op === ">" && nextCh === "|") {
              this.advance();
              op = ">|";
            } else {
              if (fd === -1 && varfd === "" && op === ">" && nextCh === "&") {
                if (this.pos + 1 >= this.length || !IsDigitOrDash(this.source[this.pos + 1])) {
                  this.advance();
                  op = ">&";
                }
              } else {
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
    } else {
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
          target = new Word("&-", null, "word");
        } else {
          target = null;
        }
      } else {
        target = null;
      }
      if (target === null) {
        var innerWord;
        if (!this.atEnd() && (/^\d+$/.test(this.peek()) || this.peek() === "-")) {
          var wordStart = this.pos;
          fdChars = [];
          while (!this.atEnd() && /^\d+$/.test(this.peek())) {
            fdChars.push(this.advance());
          }
          var fdTarget;
          if ((fdChars.length > 0)) {
            fdTarget = fdChars.join("");
          } else {
            fdTarget = "";
          }
          if (!this.atEnd() && this.peek() === "-") {
            fdTarget += this.advance();
          }
          if (fdTarget !== "-" && !this.atEnd() && !IsMetachar(this.peek())) {
            this.pos = wordStart;
            innerWord = this.parseWord(false, false, false);
            if (innerWord !== null) {
              target = new Word("&" + innerWord.value, null, "word");
              target.parts = innerWord.parts;
            } else {
              throw new ParseError(`${"Expected target for redirect " + op} at position ${this.pos}`, this.pos)
            }
          } else {
            target = new Word("&" + fdTarget, null, "word");
          }
        } else {
          innerWord = this.parseWord(false, false, false);
          if (innerWord !== null) {
            target = new Word("&" + innerWord.value, null, "word");
            target.parts = innerWord.parts;
          } else {
            throw new ParseError(`${"Expected target for redirect " + op} at position ${this.pos}`, this.pos)
          }
        }
      }
    } else {
      this.skipWhitespace();
      if ((op === ">&" || op === "<&") && !this.atEnd() && this.peek() === "-") {
        if (this.pos + 1 < this.length && !IsMetachar(this.source[this.pos + 1])) {
          this.advance();
          target = new Word("&-", null, "word");
        } else {
          target = this.parseWord(false, false, false);
        }
      } else {
        target = this.parseWord(false, false, false);
      }
    }
    if (target === null) {
      throw new ParseError(`${"Expected target for redirect " + op} at position ${this.pos}`, this.pos)
    }
    return new Redirect(op, target, null, "redirect");
  }

  ParseHeredocDelimiter() {
    this.skipWhitespace();
    var quoted = false;
    var delimiterChars = [];
    while (true) {
      var c;
      var depth;
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
        } else {
          if (ch === "'") {
            quoted = true;
            this.advance();
            while (!this.atEnd() && this.peek() !== "'") {
              c = this.advance();
              if (c === "\n") {
                this.SawNewlineInSingleQuote = true;
              }
              delimiterChars.push(c);
            }
            if (!this.atEnd()) {
              this.advance();
            }
          } else {
            if (ch === "\\") {
              this.advance();
              if (!this.atEnd()) {
                var nextCh = this.peek();
                if (nextCh === "\n") {
                  this.advance();
                } else {
                  quoted = true;
                  delimiterChars.push(this.advance());
                }
              }
            } else {
              if (ch === "$" && this.pos + 1 < this.length && this.source[this.pos + 1] === "'") {
                quoted = true;
                this.advance();
                this.advance();
                while (!this.atEnd() && this.peek() !== "'") {
                  c = this.peek();
                  if (c === "\\" && this.pos + 1 < this.length) {
                    this.advance();
                    var esc = this.peek();
                    var escVal = GetAnsiEscape(esc);
                    if (escVal >= 0) {
                      delimiterChars.push(String.fromCodePoint(escVal));
                      this.advance();
                    } else {
                      if (esc === "'") {
                        delimiterChars.push(this.advance());
                      } else {
                        delimiterChars.push(this.advance());
                      }
                    }
                  } else {
                    delimiterChars.push(this.advance());
                  }
                }
                if (!this.atEnd()) {
                  this.advance();
                }
              } else {
                if (IsExpansionStart(this.source, this.pos, "$(")) {
                  delimiterChars.push(this.advance());
                  delimiterChars.push(this.advance());
                  depth = 1;
                  while (!this.atEnd() && depth > 0) {
                    c = this.peek();
                    if (c === "(") {
                      depth += 1;
                    } else {
                      if (c === ")") {
                        depth -= 1;
                      }
                    }
                    delimiterChars.push(this.advance());
                  }
                } else {
                  var dollarCount;
                  var j;
                  if (ch === "$" && this.pos + 1 < this.length && this.source[this.pos + 1] === "{") {
                    dollarCount = 0;
                    j = this.pos - 1;
                    while (j >= 0 && this.source[j] === "$") {
                      dollarCount += 1;
                      j -= 1;
                    }
                    if (j >= 0 && this.source[j] === "\\") {
                      dollarCount -= 1;
                    }
                    if (dollarCount % 2 === 1) {
                      delimiterChars.push(this.advance());
                    } else {
                      delimiterChars.push(this.advance());
                      delimiterChars.push(this.advance());
                      depth = 0;
                      while (!this.atEnd()) {
                        c = this.peek();
                        if (c === "{") {
                          depth += 1;
                        } else {
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
                  } else {
                    if (ch === "$" && this.pos + 1 < this.length && this.source[this.pos + 1] === "[") {
                      dollarCount = 0;
                      j = this.pos - 1;
                      while (j >= 0 && this.source[j] === "$") {
                        dollarCount += 1;
                        j -= 1;
                      }
                      if (j >= 0 && this.source[j] === "\\") {
                        dollarCount -= 1;
                      }
                      if (dollarCount % 2 === 1) {
                        delimiterChars.push(this.advance());
                      } else {
                        delimiterChars.push(this.advance());
                        delimiterChars.push(this.advance());
                        depth = 1;
                        while (!this.atEnd() && depth > 0) {
                          c = this.peek();
                          if (c === "[") {
                            depth += 1;
                          } else {
                            if (c === "]") {
                              depth -= 1;
                            }
                          }
                          delimiterChars.push(this.advance());
                        }
                      }
                    } else {
                      if (ch === "`") {
                        delimiterChars.push(this.advance());
                        while (!this.atEnd() && this.peek() !== "`") {
                          c = this.peek();
                          if (c === "'") {
                            delimiterChars.push(this.advance());
                            while (!this.atEnd() && this.peek() !== "'" && this.peek() !== "`") {
                              delimiterChars.push(this.advance());
                            }
                            if (!this.atEnd() && this.peek() === "'") {
                              delimiterChars.push(this.advance());
                            }
                          } else {
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
                            } else {
                              if (c === "\\" && this.pos + 1 < this.length) {
                                delimiterChars.push(this.advance());
                                delimiterChars.push(this.advance());
                              } else {
                                delimiterChars.push(this.advance());
                              }
                            }
                          }
                        }
                        if (!this.atEnd()) {
                          delimiterChars.push(this.advance());
                        }
                      } else {
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
        depth = 1;
        while (!this.atEnd() && depth > 0) {
          c = this.peek();
          if (c === "(") {
            depth += 1;
          } else {
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
  }

  ReadHeredocLine(quoted) {
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
  }

  LineMatchesDelimiter(line, delimiter, stripTabs) {
    var checkLine = (stripTabs ? line.replace(/^[\t]+/, '') : line);
    var normalizedCheck = NormalizeHeredocDelimiter(checkLine);
    var normalizedDelim = NormalizeHeredocDelimiter(delimiter);
    return [normalizedCheck === normalizedDelim, checkLine];
  }

  GatherHeredocBodies() {
    for (const heredoc of this.PendingHeredocs) {
      var contentLines = [];
      var lineStart = this.pos;
      while (this.pos < this.length) {
        lineStart = this.pos;
        var [line, lineEnd] = this.ReadHeredocLine(heredoc.quoted);
        var [matches, checkLine] = this.LineMatchesDelimiter(line, heredoc.delimiter, heredoc.stripTabs);
        if (matches) {
          this.pos = (lineEnd < this.length ? lineEnd + 1 : lineEnd);
          break;
        }
        var normalizedCheck = NormalizeHeredocDelimiter(checkLine);
        var normalizedDelim = NormalizeHeredocDelimiter(heredoc.delimiter);
        var tabsStripped;
        if (this.EofToken === ")" && normalizedCheck.startsWith(normalizedDelim)) {
          tabsStripped = line.length - checkLine.length;
          this.pos = lineStart + tabsStripped + heredoc.delimiter.length;
          break;
        }
        if (lineEnd >= this.length && normalizedCheck.startsWith(normalizedDelim) && this.InProcessSub) {
          tabsStripped = line.length - checkLine.length;
          this.pos = lineStart + tabsStripped + heredoc.delimiter.length;
          break;
        }
        if (heredoc.stripTabs) {
          line = line.replace(/^[\t]+/, '');
        }
        if (lineEnd < this.length) {
          contentLines.push(line + "\n");
          this.pos = lineEnd + 1;
        } else {
          var addNewline = true;
          if (!heredoc.quoted && CountTrailingBackslashes(line) % 2 === 1) {
            addNewline = false;
          }
          contentLines.push(line + (addNewline ? "\n" : ""));
          this.pos = this.length;
        }
      }
      heredoc.content = contentLines.join("");
    }
    this.PendingHeredocs = [];
  }

  ParseHeredoc(fd, stripTabs) {
    var startPos = this.pos;
    this.SetState(ParserStateFlags_PST_HEREDOC);
    var [delimiter, quoted] = this.ParseHeredocDelimiter();
    for (const existing of this.PendingHeredocs) {
      if (existing.StartPos === startPos && existing.delimiter === delimiter) {
        this.ClearState(ParserStateFlags_PST_HEREDOC);
        return existing;
      }
    }
    var heredoc = new HereDoc(delimiter, "", stripTabs, quoted, fd, false, null, "heredoc");
    heredoc.StartPos = startPos;
    this.PendingHeredocs.push(heredoc);
    this.ClearState(ParserStateFlags_PST_HEREDOC);
    return heredoc;
  }

  parseCommand() {
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
      for (const w of words) {
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
  }

  parseSubshell() {
    this.skipWhitespace();
    if (this.atEnd() || this.peek() !== "(") {
      return null;
    }
    this.advance();
    this.SetState(ParserStateFlags_PST_SUBSHELL);
    var body = this.parseList(true);
    if (body === null) {
      this.ClearState(ParserStateFlags_PST_SUBSHELL);
      throw new ParseError(`Expected command in subshell at position ${this.pos}`, this.pos)
    }
    this.skipWhitespace();
    if (this.atEnd() || this.peek() !== ")") {
      this.ClearState(ParserStateFlags_PST_SUBSHELL);
      throw new ParseError(`Expected ) to close subshell at position ${this.pos}`, this.pos)
    }
    this.advance();
    this.ClearState(ParserStateFlags_PST_SUBSHELL);
    return new Subshell(body, this.CollectRedirects(), "subshell");
  }

  parseArithmeticCommand() {
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
      } else {
        if (c === "\"") {
          this.advance();
          while (!this.atEnd()) {
            if (this.peek() === "\\" && this.pos + 1 < this.length) {
              this.advance();
              this.advance();
            } else {
              if (this.peek() === "\"") {
                this.advance();
                break;
              } else {
                this.advance();
              }
            }
          }
        } else {
          if (c === "\\" && this.pos + 1 < this.length) {
            this.advance();
            this.advance();
          } else {
            if (c === "(") {
              depth += 1;
              this.advance();
            } else {
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
              } else {
                this.advance();
              }
            }
          }
        }
      }
    }
    if (this.atEnd()) {
      throw new MatchedPairError()
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
  }

  parseConditionalExpr() {
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
      throw new ParseError(`Expected ]] to close conditional expression at position ${this.pos}`, this.pos)
    }
    this.advance();
    this.advance();
    this.ClearState(ParserStateFlags_PST_CONDEXPR);
    this.WordContext = WORD_CTX_NORMAL;
    return new ConditionalExpr(body, this.CollectRedirects(), "cond-expr");
  }

  CondSkipWhitespace() {
    while (!this.atEnd()) {
      if (IsWhitespaceNoNewline(this.peek())) {
        this.advance();
      } else {
        if (this.peek() === "\\" && this.pos + 1 < this.length && this.source[this.pos + 1] === "\n") {
          this.advance();
          this.advance();
        } else {
          if (this.peek() === "\n") {
            this.advance();
          } else {
            break;
          }
        }
      }
    }
  }

  CondAtEnd() {
    return this.atEnd() || this.peek() === "]" && this.pos + 1 < this.length && this.source[this.pos + 1] === "]";
  }

  ParseCondOr() {
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
  }

  ParseCondAnd() {
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
  }

  ParseCondTerm() {
    this.CondSkipWhitespace();
    if (this.CondAtEnd()) {
      throw new ParseError(`Unexpected end of conditional expression at position ${this.pos}`, this.pos)
    }
    var operand;
    if (this.peek() === "!") {
      if (this.pos + 1 < this.length && !IsWhitespaceNoNewline(this.source[this.pos + 1])) {
      } else {
        this.advance();
        operand = this.ParseCondTerm();
        return new CondNot(operand, "cond-not");
      }
    }
    if (this.peek() === "(") {
      this.advance();
      var inner = this.ParseCondOr();
      this.CondSkipWhitespace();
      if (this.atEnd() || this.peek() !== ")") {
        throw new ParseError(`Expected ) in conditional expression at position ${this.pos}`, this.pos)
      }
      this.advance();
      return new CondParen(inner, "cond-paren");
    }
    var word1 = this.ParseCondWord();
    if (word1 === null) {
      throw new ParseError(`Expected word in conditional expression at position ${this.pos}`, this.pos)
    }
    this.CondSkipWhitespace();
    if (COND_UNARY_OPS.has(word1.value)) {
      operand = this.ParseCondWord();
      if (operand === null) {
        throw new ParseError(`${"Expected operand after " + word1.value} at position ${this.pos}`, this.pos)
      }
      return new UnaryTest(word1.value, operand, "unary-test");
    }
    if (!this.CondAtEnd() && (this.peek() !== "&" && this.peek() !== "|" && this.peek() !== ")")) {
      var word2;
      if (IsRedirectChar(this.peek()) && !(this.pos + 1 < this.length && this.source[this.pos + 1] === "(")) {
        var op = this.advance();
        this.CondSkipWhitespace();
        word2 = this.ParseCondWord();
        if (word2 === null) {
          throw new ParseError(`${"Expected operand after " + op} at position ${this.pos}`, this.pos)
        }
        return new BinaryTest(op, word1, word2, "binary-test");
      }
      var savedPos = this.pos;
      var opWord = this.ParseCondWord();
      if (opWord !== null && COND_BINARY_OPS.has(opWord.value)) {
        this.CondSkipWhitespace();
        if (opWord.value === "=~") {
          word2 = this.ParseCondRegexWord();
        } else {
          word2 = this.ParseCondWord();
        }
        if (word2 === null) {
          throw new ParseError(`${"Expected operand after " + opWord.value} at position ${this.pos}`, this.pos)
        }
        return new BinaryTest(opWord.value, word1, word2, "binary-test");
      } else {
        this.pos = savedPos;
      }
    }
    return new UnaryTest("-n", word1, "unary-test");
  }

  ParseCondWord() {
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
  }

  ParseCondRegexWord() {
    this.CondSkipWhitespace();
    if (this.CondAtEnd()) {
      return null;
    }
    this.SetState(ParserStateFlags_PST_REGEXP);
    var result = this.ParseWordInternal(WORD_CTX_REGEX, false, false);
    this.ClearState(ParserStateFlags_PST_REGEXP);
    this.WordContext = WORD_CTX_COND;
    return result;
  }

  parseBraceGroup() {
    this.skipWhitespace();
    if (!this.LexConsumeWord("{")) {
      return null;
    }
    this.skipWhitespaceAndNewlines();
    var body = this.parseList(true);
    if (body === null) {
      throw new ParseError(`Expected command in brace group at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
    }
    this.skipWhitespace();
    if (!this.LexConsumeWord("}")) {
      throw new ParseError(`Expected } to close brace group at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
    }
    return new BraceGroup(body, this.CollectRedirects(), "brace-group");
  }

  parseIf() {
    this.skipWhitespace();
    if (!this.LexConsumeWord("if")) {
      return null;
    }
    var condition = this.parseListUntil(new Set(["then"]));
    if (condition === null) {
      throw new ParseError(`Expected condition after 'if' at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
    }
    this.skipWhitespaceAndNewlines();
    if (!this.LexConsumeWord("then")) {
      throw new ParseError(`Expected 'then' after if condition at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
    }
    var thenBody = this.parseListUntil(new Set(["elif", "else", "fi"]));
    if (thenBody === null) {
      throw new ParseError(`Expected commands after 'then' at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
    }
    this.skipWhitespaceAndNewlines();
    var elseBody = null;
    if (this.LexIsAtReservedWord("elif")) {
      this.LexConsumeWord("elif");
      var elifCondition = this.parseListUntil(new Set(["then"]));
      if (elifCondition === null) {
        throw new ParseError(`Expected condition after 'elif' at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
      }
      this.skipWhitespaceAndNewlines();
      if (!this.LexConsumeWord("then")) {
        throw new ParseError(`Expected 'then' after elif condition at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
      }
      var elifThenBody = this.parseListUntil(new Set(["elif", "else", "fi"]));
      if (elifThenBody === null) {
        throw new ParseError(`Expected commands after 'then' at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
      }
      this.skipWhitespaceAndNewlines();
      var innerElse = null;
      if (this.LexIsAtReservedWord("elif")) {
        innerElse = this.ParseElifChain();
      } else {
        if (this.LexIsAtReservedWord("else")) {
          this.LexConsumeWord("else");
          innerElse = this.parseListUntil(new Set(["fi"]));
          if (innerElse === null) {
            throw new ParseError(`Expected commands after 'else' at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
          }
        }
      }
      elseBody = new If(elifCondition, elifThenBody, innerElse, null, "if");
    } else {
      if (this.LexIsAtReservedWord("else")) {
        this.LexConsumeWord("else");
        elseBody = this.parseListUntil(new Set(["fi"]));
        if (elseBody === null) {
          throw new ParseError(`Expected commands after 'else' at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
        }
      }
    }
    this.skipWhitespaceAndNewlines();
    if (!this.LexConsumeWord("fi")) {
      throw new ParseError(`Expected 'fi' to close if statement at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
    }
    return new If(condition, thenBody, elseBody, this.CollectRedirects(), "if");
  }

  ParseElifChain() {
    this.LexConsumeWord("elif");
    var condition = this.parseListUntil(new Set(["then"]));
    if (condition === null) {
      throw new ParseError(`Expected condition after 'elif' at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
    }
    this.skipWhitespaceAndNewlines();
    if (!this.LexConsumeWord("then")) {
      throw new ParseError(`Expected 'then' after elif condition at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
    }
    var thenBody = this.parseListUntil(new Set(["elif", "else", "fi"]));
    if (thenBody === null) {
      throw new ParseError(`Expected commands after 'then' at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
    }
    this.skipWhitespaceAndNewlines();
    var elseBody = null;
    if (this.LexIsAtReservedWord("elif")) {
      elseBody = this.ParseElifChain();
    } else {
      if (this.LexIsAtReservedWord("else")) {
        this.LexConsumeWord("else");
        elseBody = this.parseListUntil(new Set(["fi"]));
        if (elseBody === null) {
          throw new ParseError(`Expected commands after 'else' at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
        }
      }
    }
    return new If(condition, thenBody, elseBody, null, "if");
  }

  parseWhile() {
    this.skipWhitespace();
    if (!this.LexConsumeWord("while")) {
      return null;
    }
    var condition = this.parseListUntil(new Set(["do"]));
    if (condition === null) {
      throw new ParseError(`Expected condition after 'while' at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
    }
    this.skipWhitespaceAndNewlines();
    if (!this.LexConsumeWord("do")) {
      throw new ParseError(`Expected 'do' after while condition at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
    }
    var body = this.parseListUntil(new Set(["done"]));
    if (body === null) {
      throw new ParseError(`Expected commands after 'do' at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
    }
    this.skipWhitespaceAndNewlines();
    if (!this.LexConsumeWord("done")) {
      throw new ParseError(`Expected 'done' to close while loop at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
    }
    return new While(condition, body, this.CollectRedirects(), "while");
  }

  parseUntil() {
    this.skipWhitespace();
    if (!this.LexConsumeWord("until")) {
      return null;
    }
    var condition = this.parseListUntil(new Set(["do"]));
    if (condition === null) {
      throw new ParseError(`Expected condition after 'until' at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
    }
    this.skipWhitespaceAndNewlines();
    if (!this.LexConsumeWord("do")) {
      throw new ParseError(`Expected 'do' after until condition at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
    }
    var body = this.parseListUntil(new Set(["done"]));
    if (body === null) {
      throw new ParseError(`Expected commands after 'do' at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
    }
    this.skipWhitespaceAndNewlines();
    if (!this.LexConsumeWord("done")) {
      throw new ParseError(`Expected 'done' to close until loop at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
    }
    return new Until(condition, body, this.CollectRedirects(), "until");
  }

  parseFor() {
    this.skipWhitespace();
    if (!this.LexConsumeWord("for")) {
      return null;
    }
    this.skipWhitespace();
    if (this.peek() === "(" && this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
      return this.ParseForArith();
    }
    var varName;
    if (this.peek() === "$") {
      var varWord = this.parseWord(false, false, false);
      if (varWord === null) {
        throw new ParseError(`Expected variable name after 'for' at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
      }
      varName = varWord.value;
    } else {
      varName = this.peekWord();
      if (varName === "") {
        throw new ParseError(`Expected variable name after 'for' at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
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
          throw new ParseError(`Expected ';' or newline before 'do' at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
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
        throw new ParseError(`Expected brace group in for loop at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
      }
      return new For(varName, words, braceGroup.body, this.CollectRedirects(), "for");
    }
    if (!this.LexConsumeWord("do")) {
      throw new ParseError(`Expected 'do' in for loop at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
    }
    var body = this.parseListUntil(new Set(["done"]));
    if (body === null) {
      throw new ParseError(`Expected commands after 'do' at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
    }
    this.skipWhitespaceAndNewlines();
    if (!this.LexConsumeWord("done")) {
      throw new ParseError(`Expected 'done' to close for loop at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
    }
    return new For(varName, words, body, this.CollectRedirects(), "for");
  }

  ParseForArith() {
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
      } else {
        if (ch === ")") {
          if (parenDepth > 0) {
            parenDepth -= 1;
            current.push(this.advance());
          } else {
            if (this.pos + 1 < this.length && this.source[this.pos + 1] === ")") {
              parts.push(current.join("").replace(/^[ \t]+/, ''));
              this.advance();
              this.advance();
              break;
            } else {
              current.push(this.advance());
            }
          }
        } else {
          if (ch === ";" && parenDepth === 0) {
            parts.push(current.join("").replace(/^[ \t]+/, ''));
            current = [];
            this.advance();
          } else {
            current.push(this.advance());
          }
        }
      }
    }
    if (parts.length !== 3) {
      throw new ParseError(`Expected three expressions in for ((;;)) at position ${this.pos}`, this.pos)
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
  }

  parseSelect() {
    this.skipWhitespace();
    if (!this.LexConsumeWord("select")) {
      return null;
    }
    this.skipWhitespace();
    var varName = this.peekWord();
    if (varName === "") {
      throw new ParseError(`Expected variable name after 'select' at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
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
  }

  ConsumeCaseTerminator() {
    var term = this.LexPeekCaseTerminator();
    if (term !== "") {
      this.LexNextToken();
      return term;
    }
    return ";;";
  }

  parseCase() {
    if (!this.consumeWord("case")) {
      return null;
    }
    this.SetState(ParserStateFlags_PST_CASESTMT);
    this.skipWhitespace();
    var word = this.parseWord(false, false, false);
    if (word === null) {
      throw new ParseError(`Expected word after 'case' at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
    }
    this.skipWhitespaceAndNewlines();
    if (!this.LexConsumeWord("in")) {
      throw new ParseError(`Expected 'in' after case word at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
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
          } else {
            this.advance();
            this.skipWhitespace();
            if (!this.atEnd()) {
              var nextCh = this.peek();
              if (nextCh === ";") {
                isPattern = true;
              } else {
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
          } else {
            this.advance();
            break;
          }
        } else {
          if (ch === "\\") {
            if (this.pos + 1 < this.length && this.source[this.pos + 1] === "\n") {
              this.advance();
              this.advance();
            } else {
              patternChars.push(this.advance());
              if (!this.atEnd()) {
                patternChars.push(this.advance());
              }
            }
          } else {
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
                  } else {
                    if (c === ")") {
                      parenDepth -= 1;
                    }
                  }
                  patternChars.push(this.advance());
                }
              } else {
                extglobDepth += 1;
              }
            } else {
              if (ch === "(" && extglobDepth > 0) {
                patternChars.push(this.advance());
                extglobDepth += 1;
              } else {
                if (this.Extglob && IsExtglobPrefix(ch) && this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
                  patternChars.push(this.advance());
                  patternChars.push(this.advance());
                  extglobDepth += 1;
                } else {
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
                      } else {
                        if (sc === "[") {
                          scanDepth += 1;
                        } else {
                          if (sc === ")" && scanDepth === 0) {
                            break;
                          } else {
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
                    } else {
                      patternChars.push(this.advance());
                    }
                  } else {
                    if (ch === "'") {
                      patternChars.push(this.advance());
                      while (!this.atEnd() && this.peek() !== "'") {
                        patternChars.push(this.advance());
                      }
                      if (!this.atEnd()) {
                        patternChars.push(this.advance());
                      }
                    } else {
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
                      } else {
                        if (IsWhitespace(ch)) {
                          if (extglobDepth > 0) {
                            patternChars.push(this.advance());
                          } else {
                            this.advance();
                          }
                        } else {
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
      if (!(pattern.length > 0)) {
        throw new ParseError(`Expected pattern in case statement at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
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
      throw new ParseError(`Expected 'esac' to close case statement at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
    }
    this.ClearState(ParserStateFlags_PST_CASESTMT);
    return new Case(word, patterns, this.CollectRedirects(), "case");
  }

  parseCoproc() {
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
    var body;
    if (ch === "{") {
      body = this.parseBraceGroup();
      if (body !== null) {
        return new Coproc(body, name, "coproc");
      }
    }
    if (ch === "(") {
      if (this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
        body = this.parseArithmeticCommand();
        if (body !== null) {
          return new Coproc(body, name, "coproc");
        }
      }
      body = this.parseSubshell();
      if (body !== null) {
        return new Coproc(body, name, "coproc");
      }
    }
    var nextWord = this.LexPeekReservedWord();
    if (nextWord !== "" && COMPOUND_KEYWORDS.has(nextWord)) {
      body = this.parseCompoundCommand();
      if (body !== null) {
        return new Coproc(body, name, "coproc");
      }
    }
    var wordStart = this.pos;
    var potentialName = this.peekWord();
    if ((potentialName.length > 0)) {
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
          body = this.parseBraceGroup();
          if (body !== null) {
            return new Coproc(body, name, "coproc");
          }
        } else {
          if (ch === "(") {
            name = potentialName;
            if (this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
              body = this.parseArithmeticCommand();
            } else {
              body = this.parseSubshell();
            }
            if (body !== null) {
              return new Coproc(body, name, "coproc");
            }
          } else {
            if (nextWord !== "" && COMPOUND_KEYWORDS.has(nextWord)) {
              name = potentialName;
              body = this.parseCompoundCommand();
              if (body !== null) {
                return new Coproc(body, name, "coproc");
              }
            }
          }
        }
      }
      this.pos = wordStart;
    }
    body = this.parseCommand();
    if (body !== null) {
      return new Coproc(body, name, "coproc");
    }
    throw new ParseError(`Expected command after coproc at position ${this.pos}`, this.pos)
  }

  parseFunction() {
    this.skipWhitespace();
    if (this.atEnd()) {
      return null;
    }
    var savedPos = this.pos;
    var name;
    var body;
    if (this.LexIsAtReservedWord("function")) {
      this.LexConsumeWord("function");
      this.skipWhitespace();
      name = this.peekWord();
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
      body = this.ParseCompoundCommand();
      if (body === null) {
        throw new ParseError(`Expected function body at position ${this.pos}`, this.pos)
      }
      return new FunctionName(name, body, "function");
    }
    name = this.peekWord();
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
    if (!(name.length > 0)) {
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
    if (!hasWhitespace && (name.length > 0) && "*?@+!$".includes(name[name.length - 1])) {
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
    body = this.ParseCompoundCommand();
    if (body === null) {
      throw new ParseError(`Expected function body at position ${this.pos}`, this.pos)
    }
    return new FunctionName(name, body, "function");
  }

  ParseCompoundCommand() {
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
  }

  AtListUntilTerminator(stopWords) {
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
  }

  parseListUntil(stopWords) {
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
        } else {
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
      } else {
        if (op === "&") {
          parts.push(new Operator(op, "operator"));
          this.skipWhitespaceAndNewlines();
          if (this.AtListUntilTerminator(stopWords)) {
            break;
          }
        } else {
          if (op === "&&" || op === "||") {
            parts.push(new Operator(op, "operator"));
            this.skipWhitespaceAndNewlines();
          } else {
            parts.push(new Operator(op, "operator"));
          }
        }
      }
      if (this.AtListUntilTerminator(stopWords)) {
        break;
      }
      pipeline = this.parsePipeline();
      if (pipeline === null) {
        throw new ParseError(`${"Expected command after " + op} at position ${this.pos}`, this.pos)
      }
      parts.push(pipeline);
    }
    if (parts.length === 1) {
      return parts[0];
    }
    return new List(parts, "list");
  }

  parseCompoundCommand() {
    this.skipWhitespace();
    if (this.atEnd()) {
      return null;
    }
    var ch = this.peek();
    var result;
    if (ch === "(" && this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
      result = this.parseArithmeticCommand();
      if (result !== null) {
        return result;
      }
    }
    if (ch === "(") {
      return this.parseSubshell();
    }
    if (ch === "{") {
      result = this.parseBraceGroup();
      if (result !== null) {
        return result;
      }
    }
    if (ch === "[" && this.pos + 1 < this.length && this.source[this.pos + 1] === "[") {
      result = this.parseConditionalExpr();
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
      throw new ParseError(`${`Unexpected reserved word '${reserved}'`} at position ${this.LexPeekToken().pos}`, this.LexPeekToken().pos)
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
  }

  parsePipeline() {
    this.skipWhitespace();
    var prefixOrder = "";
    var timePosix = false;
    if (this.LexIsAtReservedWord("time")) {
      this.LexConsumeWord("time");
      prefixOrder = "time";
      this.skipWhitespace();
      var saved;
      if (!this.atEnd() && this.peek() === "-") {
        saved = this.pos;
        this.advance();
        if (!this.atEnd() && this.peek() === "p") {
          this.advance();
          if (this.atEnd() || IsMetachar(this.peek())) {
            timePosix = true;
          } else {
            this.pos = saved;
          }
        } else {
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
          saved = this.pos;
          this.advance();
          if (!this.atEnd() && this.peek() === "p") {
            this.advance();
            if (this.atEnd() || IsMetachar(this.peek())) {
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
      if (!this.atEnd() && this.peek() === "!") {
        if ((this.pos + 1 >= this.length || IsNegationBoundary(this.source[this.pos + 1])) && !this.IsBangFollowedByProcsub()) {
          this.advance();
          prefixOrder = "time_negation";
          this.skipWhitespace();
        }
      }
    } else {
      if (!this.atEnd() && this.peek() === "!") {
        if ((this.pos + 1 >= this.length || IsNegationBoundary(this.source[this.pos + 1])) && !this.IsBangFollowedByProcsub()) {
          this.advance();
          this.skipWhitespace();
          var inner = this.parsePipeline();
          if (inner !== null && inner.kind === "negation") {
            if (inner.pipeline !== null) {
              return inner.pipeline;
            } else {
              return new Command([], null, "command");
            }
          }
          return new Negation(inner, "negation");
        }
      }
    }
    var result = this.ParseSimplePipeline();
    if (prefixOrder === "time") {
      result = new Time(result, timePosix, "time");
    } else {
      if (prefixOrder === "negation") {
        result = new Negation(result, "negation");
      } else {
        if (prefixOrder === "time_negation") {
          result = new Time(result, timePosix, "time");
          result = new Negation(result, "negation");
        } else {
          if (prefixOrder === "negation_time") {
            result = new Time(result, timePosix, "time");
            result = new Negation(result, "negation");
          } else {
            if (result === null) {
              return null;
            }
          }
        }
      }
    }
    return result;
  }

  ParseSimplePipeline() {
    var cmd = this.parseCompoundCommand();
    if (cmd === null) {
      return null;
    }
    var commands = [cmd];
    while (true) {
      this.skipWhitespace();
      var [tokenType, value] = this.LexPeekOperator();
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
        throw new ParseError(`Expected command after | at position ${this.pos}`, this.pos)
      }
      commands.push(cmd);
    }
    if (commands.length === 1) {
      return commands[0];
    }
    return new Pipeline(commands, "pipeline");
  }

  parseListOperator() {
    this.skipWhitespace();
    var [tokenType, ] = this.LexPeekOperator();
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
  }

  PeekListOperator() {
    var savedPos = this.pos;
    var op = this.parseListOperator();
    this.pos = savedPos;
    return op;
  }

  parseList(newlineAsSeparator) {
    if (newlineAsSeparator) {
      this.skipWhitespaceAndNewlines();
    } else {
      this.skipWhitespace();
    }
    var pipeline = this.parsePipeline();
    if (pipeline === null) {
      return null;
    }
    var parts = [pipeline];
    if (this.InState(ParserStateFlags_PST_EOFTOKEN) && this.AtEofToken()) {
      return (parts.length === 1 ? parts[0] : new List(parts, "list"));
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
        } else {
          break;
        }
      }
      if (op === "") {
        break;
      }
      parts.push(new Operator(op, "operator"));
      if (op === "&&" || op === "||") {
        this.skipWhitespaceAndNewlines();
      } else {
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
            } else {
              break;
            }
          }
        } else {
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
              } else {
                break;
              }
            }
          }
        }
      }
      pipeline = this.parsePipeline();
      if (pipeline === null) {
        throw new ParseError(`${"Expected command after " + op} at position ${this.pos}`, this.pos)
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
  }

  parseComment() {
    if (this.atEnd() || this.peek() !== "#") {
      return null;
    }
    var start = this.pos;
    while (!this.atEnd() && this.peek() !== "\n") {
      this.advance();
    }
    var text = Substring(this.source, start, this.pos);
    return new Comment(text, "comment");
  }

  parse() {
    var source = this.source.trim();
    if (!(source.length > 0)) {
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
        throw new ParseError(`Syntax error at position ${this.pos}`, this.pos)
      }
    }
    if (!(results.length > 0)) {
      return [new Empty("empty")];
    }
    if (this.SawNewlineInSingleQuote && (this.source.length > 0) && this.source[this.source.length - 1] === "\\" && !(this.source.length >= 3 && this.source.slice(this.source.length - 3, this.source.length - 1) === "\\\n")) {
      if (!this.LastWordOnOwnLine(results)) {
        this.StripTrailingBackslashFromLastWord(results);
      }
    }
    return results;
  }

  LastWordOnOwnLine(nodes) {
    return nodes.length >= 2;
  }

  StripTrailingBackslashFromLastWord(nodes) {
    if (!(nodes.length > 0)) {
      return;
    }
    var lastNode = nodes[nodes.length - 1];
    var lastWord = this.FindLastWord(lastNode);
    if (lastWord !== null && lastWord.value.endsWith("\\")) {
      lastWord.value = Substring(lastWord.value, 0, lastWord.value.length - 1);
      if (!(lastWord.value.length > 0) && lastNode instanceof Command && (lastNode.words.length > 0)) {
        lastNode.words.pop();
      }
    }
  }

  FindLastWord(node) {
    if (node instanceof Word) {
      return node;
    }
    if (node instanceof Command) {
      if ((node.words.length > 0)) {
        var lastWord = node.words[node.words.length - 1];
        if (lastWord.value.endsWith("\\")) {
          return lastWord;
        }
      }
      if ((node.redirects.length > 0)) {
        var lastRedirect = node.redirects[node.redirects.length - 1];
        if (lastRedirect instanceof Redirect) {
          return lastRedirect.target;
        }
      }
      if ((node.words.length > 0)) {
        return node.words[node.words.length - 1];
      }
    }
    if (node instanceof Pipeline) {
      if ((node.commands.length > 0)) {
        return this.FindLastWord(node.commands[node.commands.length - 1]);
      }
    }
    if (node instanceof List) {
      if ((node.parts.length > 0)) {
        return this.FindLastWord(node.parts[node.parts.length - 1]);
      }
    }
    return null;
  }
}

function IsHexDigit(c) {
  return c >= "0" && c <= "9" || c >= "a" && c <= "f" || c >= "A" && c <= "F";
}

function IsOctalDigit(c) {
  return c >= "0" && c <= "7";
}

function GetAnsiEscape(c) {
  return ANSI_C_ESCAPES.get(c) ?? -1;
}

function IsWhitespace(c) {
  return c === " " || c === "\t" || c === "\n";
}

function StringToBytes(s) {
  return Array.from(new TextEncoder().encode(s)).slice();
}

function IsWhitespaceNoNewline(c) {
  return c === " " || c === "\t";
}

function Substring(s, start, end) {
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
    } else {
      if (c === "\"" && !quote.single && !inComment) {
        quote.double = !quote.double;
      } else {
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
  if ((redirects.length > 0)) {
    var parts = [];
    parts.push(...redirects.map(r => r.toSexp()));
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
    for (const p of node.parts) {
      if (p.kind !== "operator") {
        return StartsWithSubshell(p);
      }
    }
    return false;
  }
  if (node instanceof Pipeline) {
    if ((node.commands.length > 0)) {
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
    for (const w of node.words) {
      var val = w.ExpandAllAnsiCQuotes(w.value);
      val = w.StripLocaleStringDollars(val);
      val = w.NormalizeArrayWhitespace(val);
      val = w.FormatCommandSubstitutions(val, false);
      parts.push(val);
    }
    var heredocs = [];
    for (const r of node.redirects) {
      if (r instanceof HereDoc) {
        heredocs.push(r);
      }
    }
    parts.push(...node.redirects.map(r => FormatRedirect(r, compactRedirects, true)));
    var result;
    if (compactRedirects && (node.words.length > 0) && (node.redirects.length > 0)) {
      var wordParts = parts.slice(0, node.words.length);
      var redirectParts = parts.slice(node.words.length);
      result = wordParts.join(" ") + redirectParts.join("");
    } else {
      result = parts.join(" ");
    }
    for (const h of heredocs) {
      result = result + FormatHeredocBody(h);
    }
    return result;
  }
  if (node instanceof Pipeline) {
    var cmds = [];
    var i = 0;
    var cmd;
    var needsRedirect;
    while (i < node.commands.length) {
      cmd = node.commands[i];
      if (cmd instanceof PipeBoth) {
        i += 1;
        continue;
      }
      needsRedirect = i + 1 < node.commands.length && node.commands[i + 1].kind === "pipe-both";
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
      if (cmd.kind === "command" && (cmd.redirects.length > 0)) {
        for (const r of cmd.redirects) {
          if (r instanceof HereDoc) {
            hasHeredoc = true;
            break;
          }
        }
      }
      var firstNl;
      if (needsRedirect) {
        if (hasHeredoc) {
          firstNl = formatted.indexOf("\n");
          if (firstNl !== -1) {
            formatted = formatted.slice(0, firstNl) + " 2>&1" + formatted.slice(firstNl);
          } else {
            formatted = formatted + " 2>&1";
          }
        } else {
          formatted = formatted + " 2>&1";
        }
      }
      if (!isLast && hasHeredoc) {
        firstNl = formatted.indexOf("\n");
        if (firstNl !== -1) {
          formatted = formatted.slice(0, firstNl) + " |" + formatted.slice(firstNl);
        }
        resultParts.push(formatted);
      } else {
        resultParts.push(formatted);
      }
      idx += 1;
    }
    var compactPipe = inProcsub && (cmds.length > 0) && cmds[0][0].kind === "subshell";
    result = "";
    idx = 0;
    while (idx < resultParts.length) {
      var part = resultParts[idx];
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
  if (node instanceof List) {
    var hasHeredoc = false;
    for (const p of node.parts) {
      if (p.kind === "command" && (p.redirects.length > 0)) {
        for (const r of p.redirects) {
          if (r instanceof HereDoc) {
            hasHeredoc = true;
            break;
          }
        }
      } else {
        if (p instanceof Pipeline) {
          for (const cmd of p.commands) {
            if (cmd.kind === "command" && (cmd.redirects.length > 0)) {
              for (const r of cmd.redirects) {
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
    result = [];
    var skippedSemi = false;
    var cmdCount = 0;
    for (const p of node.parts) {
      if (p instanceof Operator) {
        if (p.op === ";") {
          if ((result.length > 0) && result[result.length - 1].endsWith("\n")) {
            skippedSemi = true;
            continue;
          }
          if (result.length >= 3 && result[result.length - 2] === "\n" && result[result.length - 3].endsWith("\n")) {
            skippedSemi = true;
            continue;
          }
          result.push(";");
          skippedSemi = false;
        } else {
          if (p.op === "\n") {
            if ((result.length > 0) && result[result.length - 1] === ";") {
              skippedSemi = false;
              continue;
            }
            if ((result.length > 0) && result[result.length - 1].endsWith("\n")) {
              result.push((skippedSemi ? " " : "\n"));
              skippedSemi = false;
              continue;
            }
            result.push("\n");
            skippedSemi = false;
          } else {
            var last;
            if (p.op === "&") {
              if ((result.length > 0) && result[result.length - 1].includes("<<") && result[result.length - 1].includes("\n")) {
                last = result[result.length - 1];
                if (last.includes(" |") || last.startsWith("|")) {
                  result[result.length - 1] = last + " &";
                } else {
                  firstNl = last.indexOf("\n");
                  result[result.length - 1] = last.slice(0, firstNl) + " &" + last.slice(firstNl);
                }
              } else {
                result.push(" &");
              }
            } else {
              if ((result.length > 0) && result[result.length - 1].includes("<<") && result[result.length - 1].includes("\n")) {
                last = result[result.length - 1];
                firstNl = last.indexOf("\n");
                result[result.length - 1] = last.slice(0, firstNl) + " " + p.op + " " + last.slice(firstNl);
              } else {
                result.push(" " + p.op);
              }
            }
          }
        }
      } else {
        if ((result.length > 0) && !(result[result.length - 1].endsWith(" ") || result[result.length - 1].endsWith("\n"))) {
          result.push(" ");
        }
        var formattedCmd = FormatCmdsubNode(p, indent, inProcsub, compactRedirects, procsubFirst && cmdCount === 0);
        if (result.length > 0) {
          last = result[result.length - 1];
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
    result = "if " + cond + "; then\n" + innerSp + thenBody + ";";
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
    result = "while " + cond + "; do\n" + innerSp + body + ";\n" + sp + "done";
    if ((node.redirects.length > 0)) {
      for (const r of node.redirects) {
        result = result + " " + FormatRedirect(r, false, false);
      }
    }
    return result;
  }
  if (node instanceof Until) {
    var cond = FormatCmdsubNode(node.condition, indent, false, false, false);
    var body = FormatCmdsubNode(node.body, indent + 4, false, false, false);
    result = "until " + cond + "; do\n" + innerSp + body + ";\n" + sp + "done";
    if ((node.redirects.length > 0)) {
      for (const r of node.redirects) {
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
      wordVals.push(...node.words.map(w => w.value));
      var words = wordVals.join(" ");
      if ((words.length > 0)) {
        result = "for " + varName + " in " + words + ";\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done";
      } else {
        result = "for " + varName + " in ;\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done";
      }
    } else {
      result = "for " + varName + " in \"$@\";\n" + sp + "do\n" + innerSp + body + ";\n" + sp + "done";
    }
    if ((node.redirects.length > 0)) {
      for (const r of node.redirects) {
        result = result + " " + FormatRedirect(r, false, false);
      }
    }
    return result;
  }
  if (node instanceof ForArith) {
    var body = FormatCmdsubNode(node.body, indent + 4, false, false, false);
    result = "for ((" + node.init + "; " + node.cond + "; " + node.incr + "))\ndo\n" + innerSp + body + ";\n" + sp + "done";
    if ((node.redirects.length > 0)) {
      for (const r of node.redirects) {
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
      var body;
      if (p.body !== null) {
        body = FormatCmdsubNode(p.body, indent + 8, false, false, false);
      } else {
        body = "";
      }
      var term = p.terminator;
      var patIndent = RepeatStr(" ", indent + 8);
      var termIndent = RepeatStr(" ", indent + 4);
      var bodyPart = ((body.length > 0) ? patIndent + body + "\n" : "\n");
      if (i === 0) {
        patterns.push(" " + pat + ")\n" + bodyPart + termIndent + term);
      } else {
        patterns.push(pat + ")\n" + bodyPart + termIndent + term);
      }
      i += 1;
    }
    var patternStr = patterns.join("\n" + RepeatStr(" ", indent + 4));
    var redirects = "";
    if ((node.redirects.length > 0)) {
      var redirectParts = [];
      redirectParts.push(...node.redirects.map(r => FormatRedirect(r, false, false)));
      redirects = " " + redirectParts.join(" ");
    }
    return "case " + word + " in" + patternStr + "\n" + sp + "esac" + redirects;
  }
  if (node instanceof FunctionName) {
    var name = node.name;
    var innerBody = (node.body.kind === "brace-group" ? node.body.body : node.body);
    body = FormatCmdsubNode(innerBody, indent + 4, false, false, false).replace(/[;]+$/, '');
    return `function ${name} () 
{ 
${innerSp}${body}
}`;
  }
  if (node instanceof Subshell) {
    body = FormatCmdsubNode(node.body, indent, inProcsub, compactRedirects, false);
    var redirects = "";
    if ((node.redirects.length > 0)) {
      var redirectParts = [];
      redirectParts.push(...node.redirects.map(r => FormatRedirect(r, false, false)));
      redirects = redirectParts.join(" ");
    }
    if (procsubFirst) {
      if ((redirects.length > 0)) {
        return "(" + body + ") " + redirects;
      }
      return "(" + body + ")";
    }
    if ((redirects.length > 0)) {
      return "( " + body + " ) " + redirects;
    }
    return "( " + body + " )";
  }
  if (node instanceof BraceGroup) {
    body = FormatCmdsubNode(node.body, indent, false, false, false);
    body = body.replace(/[;]+$/, '');
    var terminator = (body.endsWith(" &") ? " }" : "; }");
    var redirects = "";
    if ((node.redirects.length > 0)) {
      var redirectParts = [];
      redirectParts.push(...node.redirects.map(r => FormatRedirect(r, false, false)));
      redirects = redirectParts.join(" ");
    }
    if ((redirects.length > 0)) {
      return "{ " + body + terminator + " " + redirects;
    }
    return "{ " + body + terminator;
  }
  if (node instanceof ArithmeticCommand) {
    return "((" + node.rawContent + "))";
  }
  if (node instanceof ConditionalExpr) {
    body = FormatCondBody(node.body);
    return "[[ " + body + " ]]";
  }
  if (node instanceof Negation) {
    if (node.pipeline !== null) {
      return "! " + FormatCmdsubNode(node.pipeline, indent, false, false, false);
    }
    return "! ";
  }
  if (node instanceof Time) {
    var prefix = (node.posix ? "time -p " : "time ");
    if (node.pipeline !== null) {
      return prefix + FormatCmdsubNode(node.pipeline, indent, false, false, false);
    }
    return prefix;
  }
  return "";
}

function FormatRedirect(r, compact, heredocOpOnly) {
  var op;
  if (r instanceof HereDoc) {
    if (r.stripTabs) {
      op = "<<-";
    } else {
      op = "<<";
    }
    if (r.fd !== null && r.fd > 0) {
      op = String(r.fd) + op;
    }
    var delim;
    if (r.quoted) {
      delim = "'" + r.delimiter + "'";
    } else {
      delim = r.delimiter;
    }
    if (heredocOpOnly) {
      return op + delim;
    }
    return op + delim + "\n" + r.content + r.delimiter + "\n";
  }
  op = r.op;
  if (op === "1>") {
    op = ">";
  } else {
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
    var isLiteralFd = afterAmp === "-" || afterAmp.length > 0 && /^\d+$/.test(afterAmp[0]);
    if (isLiteralFd) {
      if (op === ">" || op === ">&") {
        op = (wasInputClose ? "0>" : "1>");
      } else {
        if (op === "<" || op === "<&") {
          op = "0<";
        }
      }
    } else {
      if (op === "1>") {
        op = ">";
      } else {
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
    } else {
      if (StartsWithAt(value, i, "esac") && IsWordBoundary(value, i, 4)) {
        depth -= 1;
        if (depth === 0) {
          return true;
        }
        i += 4;
      } else {
        if (c === "(") {
          i += 1;
        } else {
          if (c === ")") {
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

function SkipBacktick(value, start) {
  var i = start + 1;
  while (i < value.length && value[i] !== "`") {
    if (value[i] === "\\" && i + 1 < value.length) {
      i += 2;
    } else {
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
  return (i < s.length ? i + 1 : i);
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
    } else {
      if (scanC === ")") {
        if (scanParen > 0) {
          scanParen -= 1;
        } else {
          if (scanI + 1 < value.length && value[scanI + 1] === ")") {
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
    } else {
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
          } else {
            i += 1;
          }
        }
        if (i < value.length) {
          i += 1;
        }
      } else {
        if (i < value.length && value[i] === "'") {
          i += 1;
          while (i < value.length && value[i] !== "'") {
            i += 1;
          }
          if (i < value.length) {
            i += 1;
          }
        } else {
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
        } else {
          depth += 1;
        }
      }
    } else {
      if (c === ")") {
        if (inCasePatterns && caseDepth > 0) {
          if (!LookaheadForEsac(value, i + 1, caseDepth)) {
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
    } else {
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
    } else {
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
  var delimiter;
  if (i < value.length && (value[i] === "\"" || value[i] === "'")) {
    quoteChar = value[i];
    i += 1;
    delimStart = i;
    while (i < value.length && value[i] !== quoteChar) {
      i += 1;
    }
    delimiter = Substring(value, delimStart, i);
    if (i < value.length) {
      i += 1;
    }
  } else {
    if (i < value.length && value[i] === "\\") {
      i += 1;
      delimStart = i;
      if (i < value.length) {
        i += 1;
      }
      while (i < value.length && !IsMetachar(value[i])) {
        i += 1;
      }
      delimiter = Substring(value, delimStart, i);
    } else {
      while (i < value.length && !IsMetachar(value[i])) {
        i += 1;
      }
      delimiter = Substring(value, delimStart, i);
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
    } else {
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
      for (var j = line.length - 1; j > -1; j += -1) {
        if (line[j] === "\\") {
          trailingBs += 1;
        } else {
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
    var stripped;
    if (start + 2 < value.length && value[start + 2] === "-") {
      stripped = line.replace(/^[\t]+/, '');
    } else {
      stripped = line;
    }
    if (stripped === delimiter) {
      if (lineEnd < value.length) {
        return lineEnd + 1;
      } else {
        return lineEnd;
      }
    }
    if (stripped.startsWith(delimiter) && stripped.length > delimiter.length) {
      var tabsStripped = line.length - stripped.length;
      return lineStart + tabsStripped + delimiter.length;
    }
    if (lineEnd < value.length) {
      i = lineEnd + 1;
    } else {
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
  for (const Item of delimiters) {
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
        for (var j = line.length - 1; j > -1; j += -1) {
          if (line[j] === "\\") {
            trailingBs += 1;
          } else {
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
      var lineStripped;
      if (stripTabs) {
        lineStripped = line.replace(/^[\t]+/, '');
      } else {
        lineStripped = line;
      }
      if (lineStripped === delimiter) {
        pos = (lineEnd < source.length ? lineEnd + 1 : lineEnd);
        break;
      }
      if (lineStripped.startsWith(delimiter) && lineStripped.length > delimiter.length) {
        var tabsStripped = line.length - lineStripped.length;
        pos = lineStart + tabsStripped + delimiter.length;
        break;
      }
      pos = (lineEnd < source.length ? lineEnd + 1 : lineEnd);
    }
  }
  return [contentStart, pos];
}

function IsWordBoundary(s, pos, wordLen) {
  if (pos > 0) {
    var prev = s[pos - 1];
    if (/^[a-zA-Z0-9]+$/.test(prev) || prev === "_") {
      return false;
    }
    if ("{}!".includes(prev)) {
      return false;
    }
  }
  var end = pos + wordLen;
  if (end < s.length && (/^[a-zA-Z0-9]+$/.test(s[end]) || s[end] === "_")) {
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
  for (const c of s) {
    if (c === " " || c === "\t") {
      if (!prevWasWs) {
        result.push(" ");
      }
      prevWasWs = true;
    } else {
      result.push(c);
      prevWasWs = false;
    }
  }
  var joined = result.join("");
  return joined.replace(/^[ \t]+/, '').replace(/[ \t]+$/, '');
}

function CountTrailingBackslashes(s) {
  var count = 0;
  for (var i = s.length - 1; i > -1; i += -1) {
    if (s[i] === "\\") {
      count += 1;
    } else {
      break;
    }
  }
  return count;
}

function NormalizeHeredocDelimiter(delimiter) {
  var result = [];
  var i = 0;
  while (i < delimiter.length) {
    var depth;
    var inner;
    var innerStr;
    if (i + 1 < delimiter.length && delimiter.slice(i, i + 2) === "$(") {
      result.push("$(");
      i += 2;
      depth = 1;
      inner = [];
      while (i < delimiter.length && depth > 0) {
        if (delimiter[i] === "(") {
          depth += 1;
          inner.push(delimiter[i]);
        } else {
          if (delimiter[i] === ")") {
            depth -= 1;
            if (depth === 0) {
              innerStr = inner.join("");
              innerStr = CollapseWhitespace(innerStr);
              result.push(innerStr);
              result.push(")");
            } else {
              inner.push(delimiter[i]);
            }
          } else {
            inner.push(delimiter[i]);
          }
        }
        i += 1;
      }
    } else {
      if (i + 1 < delimiter.length && delimiter.slice(i, i + 2) === "${") {
        result.push("${");
        i += 2;
        depth = 1;
        inner = [];
        while (i < delimiter.length && depth > 0) {
          if (delimiter[i] === "{") {
            depth += 1;
            inner.push(delimiter[i]);
          } else {
            if (delimiter[i] === "}") {
              depth -= 1;
              if (depth === 0) {
                innerStr = inner.join("");
                innerStr = CollapseWhitespace(innerStr);
                result.push(innerStr);
                result.push("}");
              } else {
                inner.push(delimiter[i]);
              }
            } else {
              inner.push(delimiter[i]);
            }
          }
          i += 1;
        }
      } else {
        if (i + 1 < delimiter.length && "<>".includes(delimiter[i]) && delimiter[i + 1] === "(") {
          result.push(delimiter[i]);
          result.push("(");
          i += 2;
          depth = 1;
          inner = [];
          while (i < delimiter.length && depth > 0) {
            if (delimiter[i] === "(") {
              depth += 1;
              inner.push(delimiter[i]);
            } else {
              if (delimiter[i] === ")") {
                depth -= 1;
                if (depth === 0) {
                  innerStr = inner.join("");
                  innerStr = CollapseWhitespace(innerStr);
                  result.push(innerStr);
                  result.push(")");
                } else {
                  inner.push(delimiter[i]);
                }
              } else {
                inner.push(delimiter[i]);
              }
            }
            i += 1;
          }
        } else {
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
  var i;
  if (((flags & _SMP_PAST_OPEN) !== 0)) {
    i = start;
  } else {
    if (start >= n || s[start] !== open) {
      return -1;
    }
    i = start + 1;
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
      i = SkipSingleQuoted(s, i + 1);
      continue;
    }
    if (!(literal !== 0) && c === "\"") {
      i = SkipDoubleQuoted(s, i + 1);
      continue;
    }
    if (!(literal !== 0) && IsExpansionStart(s, i, "$(")) {
      i = FindCmdsubEnd(s, i + 2);
      continue;
    }
    if (!(literal !== 0) && IsExpansionStart(s, i, "${")) {
      i = FindBracedParamEnd(s, i + 2);
      continue;
    }
    if (!(literal !== 0) && c === open) {
      depth += 1;
    } else {
      if (c === close) {
        depth -= 1;
      }
    }
    i += 1;
  }
  return (depth === 0 ? i : -1);
}

function SkipSubscript(s, start, flags) {
  return SkipMatchedPair(s, start, "[", "]", flags);
}

function Assignment(s, flags) {
  if (!(s.length > 0)) {
    return -1;
  }
  if (!(/^[a-zA-Z]+$/.test(s[0]) || s[0] === "_")) {
    return -1;
  }
  var i = 1;
  while (i < s.length) {
    var c = s[i];
    if (c === "=") {
      return i;
    }
    if (c === "[") {
      var subFlags = (((flags & 2) !== 0) ? _SMP_LITERAL : 0);
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
    if (!(/^[a-zA-Z0-9]+$/.test(c) || c === "_")) {
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
  if (!(/^[a-zA-Z]+$/.test(chars[0]) || chars[0] === "_")) {
    return false;
  }
  var s = chars.join("");
  var i = 1;
  while (i < s.length && (/^[a-zA-Z0-9]+$/.test(s[i]) || s[i] === "_")) {
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
  if (!(name.length > 0)) {
    return false;
  }
  if (!(/^[a-zA-Z]+$/.test(name[0]) || name[0] === "_")) {
    return false;
  }
  for (const c of name.slice(1)) {
    if (!(/^[a-zA-Z0-9]+$/.test(c) || c === "_")) {
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
  var self = new ParseError(null, null, null);
  self.message = message;
  self.pos = pos;
  self.line = line;
  return self;
}

function newMatchedPairError(message, pos, line) {
  return new MatchedPairError();
}

function newQuoteState() {
  var self = new QuoteState(null, null, null);
  self.single = false;
  self.double = false;
  self.Stack = [];
  return self;
}

function newParseContext(kind) {
  var self = new ParseContext(null, null, null, null, null, null, null, null);
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
  var self = new ContextStack(null);
  self.Stack = [newParseContext(0)];
  return self;
}

function newLexer(source, extglob) {
  var self = new Lexer(null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null);
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
  var self = new Parser(null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null);
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

// CommonJS exports
if (typeof module !== 'undefined') {
  module.exports = { parse, ParseError };
}
